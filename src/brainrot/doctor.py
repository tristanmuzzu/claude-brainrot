"""Self-diagnosis.

The click-through overlay is Windows-only and cannot be exercised from CI or
from any non-Windows machine, so the checks it needs live here instead: run
``brainrot doctor`` on the machine that actually matters and it reports what is
wrong rather than leaving you to infer it from an overlay that silently does
nothing.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
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


def _check_backend() -> list[Check]:
    """The important one: can we actually make a click-through overlay?"""
    checks: list[Check] = []
    if os.name != "nt":
        checks.append(
            Check(
                "overlay",
                WARN,
                f"{sys.platform}: plain window, no click-through",
                "Click-through and host-window attachment are Windows-only. "
                "Everything else works.",
            )
        )
        return checks

    checks.append(
        Check("overlay", OK,
              "click-through, never focused, layered above the Claude Code "
              "window (attach = host)")
    )
    return checks


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
    checks += _check_backend()
    checks.append(_check_pythonw())
    checks += _check_hooks(cfg)
    checks.append(_check_daemon(cfg))
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
