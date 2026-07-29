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
    from .overlay import select_backend

    cfg = _config_from(args)
    backend = select_backend(args.backend or "")
    overlay = Overlay(cfg, backend, verbose=args.verbose)
    print(
        f"claude-brainrot {__version__} listening on {cfg.host}:{cfg.port} "
        f"({type(backend).__name__}, scenes: {', '.join(cfg.scenes)})"
    )
    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Watch a scene without any hooks -- the development loop."""
    from .engine.loop import Overlay
    from .overlay import select_backend

    cfg = _config_from(args)
    # Force it on screen immediately and keep it there.
    cfg.grace_seconds = 0.0
    cfg.min_visible_seconds = 1e9
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
    of an exact run without waiting for it to occur naturally.
    """
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    from .engine import scene as scene_api
    from .palette import generate as generate_palette

    cfg = _config_from(args)
    pygame.init()
    pygame.display.set_mode((cfg.width, cfg.height))

    run = args.seed or RunCounter().value + 1
    seed = Seed.for_run(run)
    palette = generate_palette(seed)
    name = cfg.force_scene or scene_api.choose(cfg.scenes, seed)
    ctx = scene_api.SceneContext(cfg.width, cfg.height, palette, seed, cfg.quality)
    scene = scene_api.build(name, ctx)

    surface = pygame.Surface((cfg.width, cfg.height))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    dt = 1.0 / cfg.fps
    saved = []
    for frame in range(args.frames):
        scene.update(dt)
        scene.elapsed += dt
        scene.draw(surface)
        if frame % max(1, args.every) == 0:
            path = out / f"{name}-run{run}-{frame:04d}.png"
            pygame.image.save(surface, str(path))
            saved.append(path)

    print(f"run {run}: {name} ({palette.time_of_day}/{palette.weather}) -> {len(saved)} frames in {out}")
    pygame.quit()
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
    print("\nStart the daemon with:  brainrot run")
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    from .hookinstall import uninstall

    path = uninstall(scope=args.scope)
    print(f"hooks removed from {path}")
    return 0


def cmd_ping(args: argparse.Namespace) -> int:
    from .ipc import send

    cfg = _config_from(args)
    send(cfg.host, cfg.port, args.event, session=args.session, tool=args.tool)
    print(f"sent {args.event} to {cfg.host}:{cfg.port}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    from . import doctor

    return doctor.run(_config_from(args))


def cmd_scenes(args: argparse.Namespace) -> int:
    from .engine import scene as scene_api
    from . import scenes  # noqa: F401

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
    run.add_argument("--backend", help="win32, desktop or headless")
    run.set_defaults(func=cmd_run)

    demo = sub.add_parser("demo", help="watch a scene in a normal window")
    _add_common(demo)
    demo.add_argument("--backend", help="win32, desktop or headless")
    demo.set_defaults(func=cmd_demo)

    shoot = sub.add_parser("shoot", help="render frames to PNG offscreen")
    _add_common(shoot)
    shoot.add_argument("--frames", type=int, default=180)
    shoot.add_argument("--every", type=int, default=30, help="save every Nth frame")
    shoot.add_argument("--out", default="shots")
    shoot.set_defaults(func=cmd_shoot)

    install = sub.add_parser("install", help="register Claude Code hooks")
    _add_common(install)
    install.add_argument("--scope", choices=("user", "project"), default="user")
    install.add_argument(
        "--with-tool-events",
        action="store_true",
        help="also hook PreToolUse/PostToolUse for live tool captions (hot path)",
    )
    install.set_defaults(func=cmd_install)

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
