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
        import pygame

        checks.append(Check("pygame", OK, pygame.version.ver))
    except ImportError:
        checks.append(Check("pygame", FAIL, "not installed", "pip install pygame-ce"))
    try:
        import numpy

        checks.append(Check("numpy", OK, numpy.__version__))
    except ImportError:
        checks.append(
            Check("numpy", FAIL, "not installed", "pip install numpy (used to bake textures)")
        )
    return checks


def _check_backend() -> list[Check]:
    """The important one: can we actually make a click-through overlay?"""
    checks: list[Check] = []
    if os.name != "nt":
        checks.append(
            Check(
                "overlay",
                WARN,
                f"{sys.platform}: plain window, no click-through",
                "Click-through and always-on-top are Windows-only; SDL cannot "
                "express them portably. Everything else works.",
            )
        )
        return checks

    try:
        import win32con  # noqa: F401
        import win32gui  # noqa: F401

        checks.append(Check("pywin32", OK, "available"))
        checks.append(
            Check("overlay", OK, "layered, click-through, always-on-top, never focused")
        )
    except ImportError:
        checks.append(
            Check(
                "pywin32",
                FAIL,
                "not installed",
                "pip install pywin32 -- without it the overlay falls back to an "
                "ordinary window that steals focus and eats clicks.",
            )
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
    """Actually build and draw a frame of every scene."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    try:
        import pygame

        from .engine import scene as scene_api
        from .palette import generate
        from .rng import Seed

        pygame.init()
        pygame.display.set_mode((cfg.width, cfg.height))
        surface = pygame.Surface((cfg.width, cfg.height))
        seed = Seed.for_run(1)
        names = scene_api.available()
        for name in names:
            built = scene_api.build(
                name,
                scene_api.SceneContext(cfg.width, cfg.height, generate(seed), seed, cfg.quality),
            )
            built.update(1 / 30)
            built.draw(surface)
        return Check("render", OK, f"{len(names)} scenes drew a frame: {', '.join(names)}")
    except Exception as exc:  # noqa: BLE001 - this is the diagnostic
        return Check("render", FAIL, f"{type(exc).__name__}: {exc}", "This is a bug; please report it.")


def run(cfg: Config | None = None) -> int:
    cfg = cfg or Config.load()
    checks: list[Check] = [_check_python()]
    checks += _check_deps()
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
