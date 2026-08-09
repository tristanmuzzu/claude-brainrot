"""Self-diagnosis.

Nothing about a click-through, never-focused, correctly-stacked overlay can be
exercised from CI: it needs a real desktop with a real window manager, and the
answers differ per platform. So the checks live here instead -- run
``brainrot doctor`` on the machine that actually matters and it reports what is
wrong, rather than leaving you to infer it from an overlay that silently does
nothing.

On Linux, "silently does nothing" has two quite different causes worth telling
apart, and both are reported here: no X display for the strip's own window
(fatal -- there is nothing to draw into), and no gnome-shell extension (not
fatal -- the strip docks to the work area and stays up for the whole turn
instead of following the Claude Code window).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .hookinstall import SHIM_NAME, settings_path
from .rng import RunCounter, state_dir

OK = "ok"
WARN = "warn"
FAIL = "fail"


@dataclass
class Check:
    name: str
    status: str
    detail: str
    fix: str = ""


def _check_python() -> Check:
    version = sys.version_info
    if version < (3, 11):
        return Check(
            "python",
            FAIL,
            f"{version.major}.{version.minor} is too old",
            "claude-brainrot needs Python 3.11 or newer (it uses tomllib).",
        )
    return Check("python", OK, f"{version.major}.{version.minor}.{version.micro}")


def _check_deps() -> list[Check]:
    checks: list[Check] = []
    try:
        import raylib  # noqa: F401

        checks.append(Check("raylib", OK, "importable"))
    except ImportError:
        checks.append(Check("raylib", FAIL, "not installed", "pip install raylib"))
    try:
        import PIL

        checks.append(Check("pillow", OK, PIL.__version__))
    except ImportError:
        checks.append(
            Check("pillow", FAIL, "not installed",
                  "pip install pillow (procedural textures and PNG output)")
        )
    return checks


def _check_assets() -> Check:
    """The committed .glb kit must actually be present in this install."""
    from . import assets as asset_api

    try:
        names = asset_api.available()
    except Exception as exc:  # noqa: BLE001 - diagnostic
        return Check("assets", FAIL, f"{type(exc).__name__}: {exc}",
                     "Reinstall the package; the data files did not ship.")
    if len(names) < 10:
        return Check("assets", FAIL, f"only {len(names)} models found",
                     "Reinstall the package; the asset kit is incomplete.")
    return Check("assets", OK, f"{len(names)} models")


def _check_backend(cfg: Config) -> list[Check]:
    """The important one: can we actually make a click-through overlay?"""
    from . import overlay as overlay_pkg

    checks: list[Check] = []
    native = overlay_pkg.native()
    if native is None:
        checks.append(_no_backend_check())
        return checks

    if os.name == "nt":
        checks.append(
            Check("overlay", OK,
                  "click-through, never focused, layered above the Claude Code "
                  f"window (attach = {cfg.attach})")
        )
    else:
        checks += _check_linux_backend(cfg)

    if cfg.follow_focus and not native.focus_known():
        checks.append(
            Check("focus", WARN,
                  "follow_focus is on, but nothing here can say who is in front",
                  "The strip will stay up for the whole turn rather than only "
                  "while you are looking at Claude Code. See the `shell` line "
                  "above for how to fix that."),
        )
    elif cfg.follow_focus:
        checks.append(
            Check("focus", OK,
                  "hidden unless a working Claude Code window is in front")
        )
    else:
        checks.append(
            Check("focus", WARN,
                  "follow_focus is off -- visible whenever Claude is busy",
                  "The overlay will stay on screen over other applications. "
                  "Set follow_focus = true in config.toml to have it appear "
                  "only while you are looking at Claude Code."),
        )
    return checks


def _no_backend_check() -> Check:
    """No window surgery available: say which of the reasons it is."""
    if not sys.platform.startswith("linux"):
        return Check(
            "overlay", WARN, f"{sys.platform}: plain window, no click-through",
            "The overlay window treatment exists for Windows and for Linux/X11. "
            "Everything else -- scenes, hooks, `brainrot shoot` -- works here.",
        )
    if not os.environ.get("DISPLAY"):
        return Check(
            "overlay", FAIL, "no DISPLAY: nothing to open a window on",
            "The strip is an X11 window, which on a Wayland session means "
            "XWayland. It is normally already running; if DISPLAY is genuinely "
            "unset you are on a headless machine, where `brainrot shoot` is "
            "the useful command.",
        )
    return Check(
        "overlay", FAIL, "cannot open the X display named by DISPLAY",
        "Check that XWayland is running: `xdpyinfo | head -3` should answer.",
    )


def _check_linux_backend(cfg: Config) -> list[Check]:
    """The Linux backend is two halves, and they fail independently."""
    from . import extinstall
    from .overlay import shell, x11

    checks: list[Check] = []
    session = os.environ.get("XDG_SESSION_TYPE") or "unknown"
    width = x11.screen_rect()[2]
    checks.append(Check(
        "overlay", OK,
        f"X11 window on a {session} session, {width}px wide screen: "
        "click-through, never focused, above"))

    if not extinstall.is_gnome():
        checks.append(Check(
            "shell", WARN,
            f"{os.environ.get('XDG_CURRENT_DESKTOP') or 'unknown desktop'}: "
            "no window information available",
            "The strip will dock to the work area and stay up for the whole "
            "turn. Standing beside the Claude Code window, and appearing only "
            "while you are looking at it, both need to ask the compositor "
            "where things are -- which only the GNOME extension does today.",
        ))
        return checks

    if not extinstall.installed():
        checks.append(Check(
            "shell", WARN, "gnome-shell extension not installed",
            "Without it the strip docks to the work area and stays up for the "
            "whole turn. Install it with: brainrot extension install",
        ))
        return checks
    if not extinstall.enabled():
        if extinstall.enabled_next_session():
            checks.append(Check(
                "shell", WARN,
                "extension installed and switched on, but this gnome-shell has "
                "not loaded it",
                "gnome-shell only picks up a new extension when it starts, and "
                "on Wayland that means the session. Log out and back in.",
            ))
        else:
            checks.append(Check(
                "shell", WARN, "gnome-shell extension installed but disabled",
                f"Enable it with: gnome-extensions enable {extinstall.UUID}",
            ))
        return checks
    if not extinstall.up_to_date():
        checks.append(Check(
            "shell", WARN, "an older copy of the extension is installed",
            "Update it with: brainrot extension install",
        ))

    port = extinstall.configured_port()
    if port is not None and port != cfg.port:
        checks.append(Check(
            "shell", FAIL,
            f"extension sends to port {port}, daemon listens on {cfg.port}",
            "Re-run `brainrot install` (it sets both), or set the port by hand: "
            f"gsettings --schemadir {extinstall.target_dir()}/schemas set "
            f"{extinstall.SCHEMA_ID} port {cfg.port}",
        ))
        return checks

    # Whether it is actually *talking* is a different question from whether it
    # is enabled, and the only honest way to answer it is to listen.
    heard = _listen_for_shell(cfg)
    if heard is None:
        checks.append(Check(
            "shell", OK,
            "extension enabled (the daemon is running, so it is holding the "
            "port -- ask it, not me)"))
    elif heard:
        snap = shell.bridge().snapshot
        checks.append(Check(
            "shell", OK,
            f"{len(snap.windows)} windows, {len(snap.monitors)} monitor(s), "
            f"{snap.scale_against(x11.screen_rect()[2]):g}x scale"))
    else:
        checks.append(Check(
            "shell", FAIL, "extension enabled but sending nothing",
            "gnome-shell may have failed to load it. Look for the reason: "
            "journalctl --user -b -u org.gnome.Shell@wayland.service | tail -40",
        ))
    return checks


def _listen_for_shell(cfg: Config, timeout: float = 2.0) -> "bool | None":
    """Bind the daemon's port briefly and see whether a snapshot arrives.

    None means the port is already taken -- which almost always means the
    daemon itself has it, and is therefore the answer "cannot tell from here"
    rather than a failure.
    """
    import socket

    from .overlay import shell

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        try:
            sock.bind((cfg.host, cfg.port))
        except OSError:
            return None
        sock.settimeout(timeout)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                payload, _ = sock.recvfrom(65535)
            except socket.timeout:
                break
            if shell.bridge().offer(payload):
                return True
        return False
    finally:
        sock.close()


def _check_pythonw() -> Check:
    """A console flash on every hook is the most annoying failure mode there is."""
    if os.name != "nt":
        return Check("pythonw", OK, "not applicable off Windows")

    candidate = Path(sys.executable).with_name("pythonw.exe")
    if candidate.exists() or shutil.which("pythonw"):
        return Check("pythonw", OK, "found -- hooks will run without a console window")
    return Check(
        "pythonw",
        WARN,
        "not found next to your interpreter",
        "Hooks will run under python.exe and flash a console window twice per "
        "turn. Installing Python from python.org rather than the Microsoft "
        "Store provides pythonw.exe.",
    )


def _check_hooks(cfg: Config) -> list[Check]:
    checks: list[Check] = []
    shim = state_dir() / SHIM_NAME
    if shim.exists():
        checks.append(Check("shim", OK, str(shim)))
    else:
        checks.append(Check("shim", FAIL, "not written", "Run: brainrot install"))

    path = settings_path("user")
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
        hooks = settings.get("hooks", {})
    except (OSError, json.JSONDecodeError):
        checks.append(Check("hooks", FAIL, f"cannot read {path}", "Run: brainrot install"))
        return checks

    registered = [
        event
        for event, entries in hooks.items()
        if isinstance(entries, list)
        and any(SHIM_NAME in str(h.get("command", "")) for e in entries for h in e.get("hooks", []))
    ]
    if registered:
        checks.append(Check("hooks", OK, ", ".join(sorted(registered))))
    else:
        checks.append(
            Check("hooks", FAIL, f"none registered in {path}", "Run: brainrot install")
        )
    return checks


def _check_daemon(cfg: Config) -> Check:
    """Is anything already listening? A bound port means the daemon is up."""
    import socket

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.bind((cfg.host, cfg.port))
    except OSError:
        return Check("daemon", OK, f"something is listening on {cfg.host}:{cfg.port}")
    else:
        return Check(
            "daemon",
            WARN,
            f"nothing listening on {cfg.host}:{cfg.port}",
            "Start it with: brainrot run",
        )
    finally:
        probe.close()


def _packaged_copies() -> list[Path]:
    """Every redirected copy of the state directory this machine can show us.

    A Store-packaged interpreter does not merely redirect its *writes* under
    ``%APPDATA%`` -- it cannot see the real folder at all. So a config.toml
    sitting in plain sight at ``AppData\\Roaming\\claude-brainrot`` may be a
    file the daemon has never once read, and there can be several copies, one
    per packaged app that has run this code. Editing the wrong one changes
    nothing and explains nothing.
    """
    local = os.environ.get("LOCALAPPDATA")
    if os.name != "nt" or not local:
        return []
    try:
        return sorted(Path(local, "Packages").glob("*/LocalCache/Roaming/claude-brainrot"))
    except OSError:
        return []


def _check_config() -> Check:
    """Which config.toml the daemon is actually reading."""
    path = state_dir() / "config.toml"
    detail = str(path) if path.exists() else f"{path} (absent -- built-in defaults)"

    packaged = "WindowsApps" in sys.prefix or "WindowsApps" in sys.executable
    if not packaged:
        return Check("config", OK, detail)

    copies = _packaged_copies()
    mine = [p for p in copies if p.parent.parent.parent.name in sys.executable]
    real = str(mine[0] / "config.toml") if mine else "(could not locate it)"
    where = f"{detail}\n            on disk: {real}"

    # Other copies only matter when they *disagree*. Identical ones are just
    # the same settings sitting in more than one place, which is what happens
    # the moment a second packaged app runs this code.
    live = path.read_bytes() if path.exists() else b""
    stale = []
    for other in (p / "config.toml" for p in copies if p not in mine):
        try:
            if other.read_bytes() != live:
                stale.append(other)
        except OSError:
            continue
    if not stale:
        return Check("config", OK, where)
    return Check(
        "config", WARN, where,
        "This interpreter is a Store build: %APPDATA% is redirected and the "
        "plain AppData\\Roaming copy is invisible to it. These copies say "
        "something different and are being ignored -- edit the 'on disk' path "
        "above instead: " + ", ".join(str(p) for p in stale),
    )


def _count_overlay_windows() -> int:
    """How many overlay windows exist right now, across every process."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    seen = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _lparam):
        text = ctypes.create_unicode_buffer(64)
        user32.GetWindowTextW(hwnd, text, 64)
        if text.value == "claude-brainrot":
            seen.append(int(hwnd))
        return True

    user32.EnumWindows(visit, 0)
    return len(seen)


def _count_x11_overlay_windows() -> int:
    """The same count on X11: our window carries its own title."""
    from .overlay import x11

    handle = x11.lib()
    if handle is None:
        return 0
    return sum(1 for win in x11._prop(handle, handle.root, "_NET_CLIENT_LIST")
               if _title_of(handle, win) == "claude-brainrot")


def _title_of(handle, win: int) -> str:
    import ctypes

    from .overlay import x11

    actual, fmt = x11.Atom(), ctypes.c_int()
    items, after = ctypes.c_ulong(), ctypes.c_ulong()
    data = ctypes.POINTER(ctypes.c_ubyte)()
    if handle.x11.XGetWindowProperty(
            handle.display, win, handle.atom("_NET_WM_NAME"), 0, 64, 0, 0,
            ctypes.byref(actual), ctypes.byref(fmt), ctypes.byref(items),
            ctypes.byref(after), ctypes.byref(data)) != 0 or not data:
        return ""
    text = bytes(ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte))[:items.value])
    handle.x11.XFree(data)
    return text.decode("utf-8", "replace")


def _check_one_daemon() -> Check | None:
    """More than one daemon is not an idle curiosity.

    UDP with ``SO_REUSEADDR`` lets a second daemon bind the same port quite
    happily, and then the hook events are split between them: each gets a
    fraction of the turn, both fight over the screen, and every symptom looks
    like a bug in the overlay rather than a spare process. Cost an hour here.
    """
    try:
        if os.name == "nt":
            count = _count_overlay_windows()
        elif os.environ.get("DISPLAY"):
            count = _count_x11_overlay_windows()
        else:
            return None
    except Exception:  # noqa: BLE001 - diagnostic only
        return None
    if count <= 1:
        return Check("instances", OK, f"{count} overlay window")
    return Check(
        "instances", WARN, f"{count} overlay windows -- more than one daemon",
        "Hook events are split between them and they fight over the screen. "
        "Close the extras and start one with: brainrot run. On Windows a "
        "Store Python's command line is not readable through WMI, so a kill "
        "filtered on it matches nothing -- count the windows, as this does.",
    )


def _check_render(cfg: Config) -> Check:
    """Actually build and draw a frame of every scene, offscreen.

    Runs in a subprocess: the doctor may be invoked on a machine where a GPU
    window would be attempted, and a render crash must not take the doctor
    down with it.
    """
    import subprocess

    code = (
        "import os; os.environ['BRAINROT_HEADLESS']='1';"
        "from brainrot.config import Config;"
        "from brainrot.engine import scene as scene_api;"
        "from brainrot.engine.window import HeadlessWindow;"
        "from brainrot.palette import generate;"
        "from brainrot.rng import Seed;"
        "cfg=Config(); w=HeadlessWindow(); w.create(cfg);"
        "seed=Seed.for_run(1); names=scene_api.available();\n"
        "for n in names:\n"
        "    s=scene_api.build(n, scene_api.SceneContext(cfg.width, cfg.height,"
        " generate(seed), seed, cfg.quality));"
        " s.update(1/60); w.begin(); s.draw(); w.end()\n"
        "print('RENDERED='+','.join(names))"
    )
    try:
        result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                                text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return Check("render", FAIL, "render probe timed out", "This is a bug; please report it.")
    for line in result.stdout.splitlines():
        if line.startswith("RENDERED="):
            names = line.removeprefix("RENDERED=").split(",")
            return Check("render", OK, f"{len(names)} scenes drew a frame: {', '.join(names)}")
    tail = (result.stderr or result.stdout).strip().splitlines()
    detail = tail[-1] if tail else "no output"
    return Check("render", FAIL, detail, "This is a bug; please report it.")


def run(cfg: Config | None = None) -> int:
    cfg = cfg or Config.load()
    checks: list[Check] = [_check_python()]
    checks += _check_deps()
    checks.append(_check_assets())
    checks += _check_backend(cfg)
    checks.append(_check_pythonw())
    checks.append(_check_config())
    checks += _check_hooks(cfg)
    checks.append(_check_daemon(cfg))
    instances = _check_one_daemon()
    if instances is not None:
        checks.append(instances)
    checks.append(_check_render(cfg))

    symbols = {OK: "PASS", WARN: "WARN", FAIL: "FAIL"}
    print(f"claude-brainrot doctor  ({sys.platform}, quality={cfg.quality})\n")
    for check in checks:
        print(f"  [{symbols[check.status]}] {check.name:9s} {check.detail}")
        if check.fix and check.status != OK:
            for line in _wrap(check.fix, 66):
                print(f"            {line}")

    counter = RunCounter()
    print(f"\n  state dir: {state_dir()}")
    print(f"  runs so far: {counter.value}")

    failures = sum(1 for c in checks if c.status == FAIL)
    warnings = sum(1 for c in checks if c.status == WARN)
    print(f"\n  {failures} failed, {warnings} warnings, {len(checks) - failures - warnings} passed")
    return 1 if failures else 0


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines
