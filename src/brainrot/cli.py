"""Command line interface."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .config import Config
from .rng import RunCounter, Seed, state_dir


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--port", type=int, help="UDP port for hook events")
    parser.add_argument("--width", type=int, help="overlay width in pixels")
    parser.add_argument("--height", type=int, help="overlay height in pixels")
    parser.add_argument("--scene", help="force a single scene")
    parser.add_argument("--seed", type=int, help="replay a specific run number")
    parser.add_argument(
        "--quality", choices=("high", "balanced", "low"), help="detail level (CPU trade-off)"
    )


def _config_from(args: argparse.Namespace) -> Config:
    cfg = Config.load()
    for name in ("port", "width", "height"):
        value = getattr(args, name, None)
        if value:
            setattr(cfg, name, value)
    if getattr(args, "scene", None):
        cfg.force_scene = args.scene
    if getattr(args, "seed", None):
        cfg.force_seed = args.seed
    if getattr(args, "quality", None):
        cfg.quality = args.quality
    cfg._validate()
    return cfg


def cmd_run(args: argparse.Namespace) -> int:
    from .engine.loop import Overlay
    from .engine.window import select_backend
    from .ipc import AlreadyRunning

    cfg = _config_from(args)
    backend = select_backend(args.backend or "")
    overlay = Overlay(cfg, backend, verbose=args.verbose)
    print(
        f"claude-brainrot {__version__} listening on {cfg.host}:{cfg.port} "
        f"({type(backend).__name__}, scenes: {', '.join(cfg.scenes)})",
        flush=True,
    )
    # Turns that were already running when the daemon started fired their
    # UserPromptSubmit before anything was listening, so the first thing you
    # see is the *next* prompt. Saying so beats it looking broken for a turn.
    print("waiting for the next prompt (a turn already in flight is not "
          "something a hook can be told about after the fact)", flush=True)
    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    except AlreadyRunning as exc:
        print(f"\n{exc}", file=sys.stderr)
        print("Stop the other one first, or start this with --port.",
              file=sys.stderr)
        return 1
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Watch a scene without any hooks -- the development loop."""
    from .engine.loop import Overlay
    from .engine.window import select_backend

    cfg = _config_from(args)
    # Force it on screen immediately and keep it there -- including through
    # the focus rule, which has no host to match against here and would
    # otherwise keep the demo permanently hidden.
    cfg.grace_seconds = 0.0
    cfg.min_visible_seconds = 1e9
    cfg.follow_focus = False
    backend = select_backend(args.backend or "desktop")
    overlay = Overlay(cfg, backend, verbose=args.verbose)
    overlay.state.handle("UserPromptSubmit", "demo")
    print("demo mode -- Esc or Ctrl-C to quit")
    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    return 0


def cmd_shoot(args: argparse.Namespace) -> int:
    """Render frames to PNG offscreen.

    Generated content is far easier to tune when you can inspect an exact frame
    of an exact run without waiting for it to occur naturally. Uses the same
    software rasteriser as CI, colour-corrected to match the GPU output.
    """
    os.environ["BRAINROT_HEADLESS"] = "1"

    from .engine import rl, scene as scene_api
    from .engine.window import HeadlessWindow
    from .palette import generate as generate_palette

    cfg = _config_from(args)
    window = HeadlessWindow()
    window.create(cfg)

    run = args.seed or RunCounter().value + 1
    seed = Seed.for_run(run)
    palette = generate_palette(seed)
    name = cfg.force_scene or scene_api.choose(cfg.scenes, seed)
    ctx = scene_api.SceneContext(cfg.width, cfg.height, palette, seed, cfg.quality)
    scene = scene_api.build(name, ctx)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    dt = 1.0 / cfg.fps
    saved = []
    # One warmup frame: the first swap after window creation presents an
    # empty back buffer, which would make frame 0 capture black.
    window.begin()
    scene.draw()
    window.end()
    for frame in range(args.frames):
        scene.update(dt)
        scene.elapsed += dt
        window.begin()
        scene.draw()
        window.end()
        if frame % max(1, args.every) == 0:
            # A read-back is one or more buffer swaps behind the draw, so put
            # this frame up again -- as many times as this renderer needs --
            # before reading it. Otherwise the PNG holds the frame before the
            # one it is named after.
            window.present(scene.draw)
            path = out / f"{name}-run{run}-{frame:04d}.png"
            rl.save_frame(str(path))
            saved.append(path)

    print(f"run {run}: {name} ({palette.time_of_day}/{palette.weather}) -> {len(saved)} frames in {out}")
    window.destroy()
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    from .hookinstall import hook_command, install, write_shim

    cfg = _config_from(args)
    path, events = install(cfg, scope=args.scope, with_tool_events=args.with_tool_events)
    shim = write_shim(cfg)
    print(f"hooks installed in {path}")
    print(f"  events: {', '.join(events)}")
    print(f"  shim:   {shim}")
    print(f"  command: {hook_command(shim)}")

    if sys.platform.startswith("linux") and not args.no_extension:
        from . import extinstall

        if extinstall.is_gnome():
            ok, detail = extinstall.install(cfg)
            print(f"\ngnome-shell extension: {detail}")
            if ok and not extinstall.enabled():
                print("  to skip the logout:  brainrot extension load")
            if not ok:
                print("  the overlay still works without it -- see `brainrot doctor`")
        else:
            print("\ngnome-shell extension: skipped (not a GNOME session)")

    print("\nStart the daemon with:  brainrot run")
    return 0


def cmd_extension(args: argparse.Namespace) -> int:
    """Install, load, remove or report on the gnome-shell half."""
    import time

    from . import extinstall

    cfg = _config_from(args)
    if args.action == "load":
        return _load_extension_now(extinstall, time)
    if args.action == "remove":
        ok, detail = extinstall.uninstall()
        print(detail)
        return 0 if ok else 1
    if args.action == "install":
        ok, detail = extinstall.install(cfg)
        print(detail)
        return 0 if ok else 1

    print(f"uuid:      {extinstall.UUID}")
    print(f"ships in:  {extinstall.source_dir()}")
    print(f"installed: {extinstall.target_dir() if extinstall.installed() else 'no'}")
    if extinstall.installed():
        print(f"current:   {'yes' if extinstall.up_to_date() else 'no -- run: brainrot extension install'}")
        print(f"enabled:   {'yes' if extinstall.enabled() else 'no'}")
        print(f"port:      {extinstall.configured_port()}")
    print(f"shell:     {extinstall.shell_version() or 'not found'}")
    print(f"supports:  {', '.join(extinstall.supported_versions())}")
    return 0


def _load_extension_now(extinstall, time) -> int:
    """Get the extension running without ending the session.

    gnome-shell scans for extensions once, at startup, and on Wayland it
    cannot be restarted without logging out -- so a freshly installed one
    normally waits for the next login. It can be loaded by hand from inside
    the shell, which needs unsafe mode, which only a person can turn on. This
    walks through that and then puts unsafe mode back.
    """
    ok, detail = extinstall.load_now()
    if ok:
        print(detail)
        return 0
    if detail != "gnome-shell is not in unsafe mode":
        print(detail)
        return 1

    print("gnome-shell only looks for new extensions when it starts, and on")
    print("Wayland that means the session. It can be told to load one now,")
    print("but only from inside the shell -- which needs unsafe mode, and only")
    print("you can turn that on:\n")
    print("  1. press Alt+F2")
    print("  2. type  lg  and press Enter (this is Looking Glass)")
    print("  3. in the prompt at the bottom, type:")
    print("       global.context.unsafe_mode = true")
    print("     and press Enter")
    print("  4. press Esc to close it\n")
    print("Waiting for that... (Ctrl-C to give up and just log out instead)")

    deadline = time.monotonic() + 180
    try:
        while time.monotonic() < deadline:
            if extinstall.unsafe_mode():
                break
            time.sleep(0.5)
        else:
            print("\nTimed out. Logging out and back in does the same job.")
            return 1
    except KeyboardInterrupt:
        print("\nstopped")
        return 1

    ok, detail = extinstall.load_now()
    print(f"\n{detail}")
    # Leave the machine as it was found: unsafe mode is not something to walk
    # away from, and nothing here needs it once the extension is running.
    if extinstall.set_unsafe_mode(False):
        print("unsafe mode turned back off")
    else:
        print("could not turn unsafe mode back off -- do it in Looking Glass, "
              "or just log out; it does not survive a session")
    return 0 if ok else 1


def cmd_uninstall(args: argparse.Namespace) -> int:
    from .hookinstall import uninstall

    path = uninstall(scope=args.scope)
    print(f"hooks removed from {path}")
    return 0


def cmd_ping(args: argparse.Namespace) -> int:
    from .ipc import send

    cfg = _config_from(args)
    # Stand in for the hook shim completely, window handle included: the
    # daemon shows nothing for a session whose window it does not know, so a
    # ping without one would look like a broken daemon. This makes the
    # terminal you ping from the host, which is also what you want when
    # checking the focus behaviour by hand.
    hwnd = 0
    if os.name == "nt":
        try:
            from .overlay.win32 import foreground_window

            hwnd = foreground_window()
        except Exception:
            hwnd = 0
    # Elsewhere the shim sends its ancestry instead of a handle, and so does
    # this: the ancestry of `brainrot ping` reaches the terminal it was typed
    # in, which makes that terminal the host -- exactly as if Claude Code were
    # running there.
    pids = _ancestry() if os.name != "nt" else ()
    send(cfg.host, cfg.port, args.event, session=args.session, tool=args.tool,
         hwnd=hwnd, pids=pids)
    print(f"sent {args.event} to {cfg.host}:{cfg.port}")
    return 0


def _ancestry(limit: int = 12) -> tuple[int, ...]:
    """This process and its parents, nearest first. See the hook shim."""
    pids: list[int] = []
    pid = os.getpid()
    try:
        for _ in range(limit):
            pids.append(pid)
            with open(f"/proc/{pid}/stat", "rb") as handle:
                fields = handle.read().rsplit(b")", 1)[1].split()
            parent = int(fields[1])
            if parent <= 1 or parent == pid:
                break
            pid = parent
    except OSError:
        pass
    return tuple(pids)


def cmd_doctor(args: argparse.Namespace) -> int:
    from . import doctor

    return doctor.run(_config_from(args))


def cmd_hotkey(args: argparse.Namespace) -> int:
    """Print the config line for whatever chord you press.

    The takeover chord is *polled*, not registered, so it can never take a
    combination away from another program -- and equally can never discover
    that another program already owns one. Pick a combination nothing else
    reacts to, press it here, and paste the line it prints.
    """
    import time

    if os.name != "nt":
        # Nothing to capture: on GNOME the chord is *grabbed* by the shell
        # extension rather than polled, so it is a gsettings key rather than
        # something this process could watch for -- and being grabbed, it
        # cannot collide with another program the way a polled one can.
        from . import extinstall

        cfg = _config_from(args)
        print(f"current hotkey: {cfg.hotkey}")
        print("\nOn GNOME the chord is registered inside gnome-shell, so it is")
        print("set there rather than here:\n")
        print(f"  gsettings --schemadir {extinstall.target_dir()}/schemas \\")
        print(f"      set {extinstall.SCHEMA_ID} takeover \"['<Control><Alt><Shift>Home']\"")
        print("\nAnything gnome-shell already uses will simply refuse to bind,")
        print("which is the collision check Windows has to do by hand.")
        return 0

    import ctypes

    from .engine.keys import MODIFIERS, describe, parse_chord

    user32 = ctypes.windll.user32
    cfg = _config_from(args)
    print(f"current hotkey: {cfg.hotkey}")
    print("\nHold a combination you want to use. Watch whether anything else")
    print("on your machine reacts to it -- if something does, try another.")
    print("Ctrl-C to stop.\n")

    mods = set(MODIFIERS.values())
    best: frozenset[int] = frozenset()
    shown = ""
    try:
        while True:
            held = {vk for vk in range(0x08, 0xFF)
                    if user32.GetAsyncKeyState(vk) & 0x8000}
            # Ignore mouse buttons, which GetAsyncKeyState also reports.
            held -= {0x01, 0x02, 0x04, 0x05, 0x06}
            if held:
                # Grow to the largest combination held in one go, so releasing
                # in any order still reports what was actually pressed.
                if len(held) >= len(best):
                    best = frozenset(held)
            elif best:
                spec = describe(best)
                if parse_chord(spec) and not set(best) <= mods:
                    if spec != shown:
                        print(f"  {spec}")
                        print(f"      config.toml:  hotkey = \"{spec}\"")
                        print(f"      or:           set BRAINROT_HOTKEY={spec}\n")
                        shown = spec
                elif set(best) <= mods:
                    print("  (modifiers only -- add a real key)\n")
                best = frozenset()
            time.sleep(0.03)
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def cmd_scenes(args: argparse.Namespace) -> int:
    from .engine import scene as scene_api

    cfg = Config.load()
    counter = RunCounter()
    print("registered scenes:")
    for name in scene_api.available():
        mark = "*" if name in cfg.scenes else " "
        print(f"  {mark} {name}")
    print(f"\nstate dir: {state_dir()}")
    print(f"runs so far: {counter.value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="brainrot", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="start the overlay daemon")
    _add_common(run)
    run.add_argument("--backend", help="overlay, desktop or headless")
    run.set_defaults(func=cmd_run)

    demo = sub.add_parser("demo", help="watch a scene in a normal window")
    _add_common(demo)
    demo.add_argument("--backend", help="overlay, desktop or headless")
    demo.set_defaults(func=cmd_demo)

    shoot = sub.add_parser("shoot", help="render frames to PNG offscreen")
    _add_common(shoot)
    shoot.add_argument("--frames", type=int, default=180)
    shoot.add_argument("--every", type=int, default=30, help="save every Nth frame")
    shoot.add_argument("--out", default="shots")
    shoot.set_defaults(func=cmd_shoot)

    hotkey = sub.add_parser(
        "hotkey",
        help="find a free chord for handing the overlay the keyboard")
    _add_common(hotkey)
    hotkey.set_defaults(func=cmd_hotkey)

    install = sub.add_parser("install", help="register Claude Code hooks")
    _add_common(install)
    install.add_argument("--scope", choices=("user", "project"), default="user")
    install.add_argument(
        "--with-tool-events",
        action="store_true",
        help="also hook PreToolUse/PostToolUse for live tool captions (hot path)",
    )
    install.add_argument(
        "--no-extension",
        action="store_true",
        help="skip the gnome-shell extension (Linux); the overlay then docks "
             "to the work area and stays up for the whole turn",
    )
    install.set_defaults(func=cmd_install)

    ext = sub.add_parser(
        "extension",
        help="the gnome-shell half: what Wayland will not tell a client")
    _add_common(ext)
    ext.add_argument("action", nargs="?", default="status",
                     choices=("status", "install", "load", "remove"))
    ext.set_defaults(func=cmd_extension)

    remove = sub.add_parser("uninstall", help="remove Claude Code hooks")
    remove.add_argument("--scope", choices=("user", "project"), default="user")
    remove.set_defaults(func=cmd_uninstall)

    ping = sub.add_parser("ping", help="send a hook event by hand")
    _add_common(ping)
    ping.add_argument("event", nargs="?", default="UserPromptSubmit")
    ping.add_argument("--session", default="manual")
    ping.add_argument("--tool", default="")
    ping.set_defaults(func=cmd_ping)

    check = sub.add_parser("doctor", help="diagnose the install and the overlay backend")
    _add_common(check)
    check.set_defaults(func=cmd_doctor)

    listing = sub.add_parser("scenes", help="list registered scenes")
    listing.set_defaults(func=cmd_scenes)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)
