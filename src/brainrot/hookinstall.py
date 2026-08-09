"""Claude Code hook installation.

The shim written by this module runs inside Claude Code's critical path, so it
is built around three constraints:

1. **It must never block.** One UDP datagram, no connect, no response read. If
   the daemon is dead, stopped, or wedged, the packet is dropped by the kernel
   and Claude Code carries on. A hook that can hang is a hook that can hang
   *your editor*.
2. **It must never fail.** The whole body is wrapped in a bare except. A
   traceback on stderr from a toy overlay has no business appearing in a real
   session.
3. **It must start fast.** ``python -S`` skips ``site``, which is most of a
   cold interpreter's startup, and the script imports only builtins. On Windows
   it runs under ``pythonw.exe`` so no console window flashes on every event;
   on Linux there is no console to flash, and the few ``/proc`` reads that
   discover the shim's ancestry cost microseconds.

One shim covers every event: the hook payload already carries
``hook_event_name``, so there is nothing to parameterise per hook.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from .config import Config
from .rng import state_dir

#: Shim filename. Doubles as the marker that lets install/uninstall recognise
#: our own entries without disturbing anyone else's hooks.
SHIM_NAME = "brainrot_hook.py"

#: Hooks we register. PreToolUse/PostToolUse are deliberately absent by
#: default -- they fire on every single tool call, and the overlay needs
#: nothing from them that Stop and UserPromptSubmit do not already provide.
DEFAULT_EVENTS = ("UserPromptSubmit", "Stop", "Notification", "SessionEnd")

#: Opt-in via --with-tool-events. Buys live tool captions at the cost of
#: running the shim on the hot path.
TOOL_EVENTS = ("PreToolUse", "PostToolUse")

_SHIM_TEMPLATE = '''\
"""claude-brainrot hook shim -- generated, safe to delete.

Sends one UDP datagram and exits. Never blocks, never raises.
"""
try:
    import json
    import os
    import socket
    import sys

    payload = json.load(sys.stdin)

    # The window you are typing into when a hook fires IS the Claude Code
    # host window; its handle lets the daemon layer the overlay just above
    # that window instead of above everything.
    hwnd = 0
    if os.name == "nt":
        try:
            import ctypes

            hwnd = int(ctypes.windll.user32.GetForegroundWindow())
        except Exception:
            hwnd = 0

    # On Wayland there is no such handle to read: a client cannot be told
    # about windows, its own included. So send this process's ancestry
    # instead -- the terminal or app running Claude Code is one of these
    # processes -- and let the daemon match it against the window list the
    # compositor gives it. Nearest ancestor first, so a shell inside a
    # multiplexer resolves to the window you are actually looking at.
    pids = []
    if os.name != "nt":
        try:
            pid = os.getpid()
            for _ in range(12):
                pids.append(pid)
                with open("/proc/%d/stat" % pid, "rb") as handle:
                    fields = handle.read().rsplit(b")", 1)[1].split()
                parent = int(fields[1])
                if parent <= 1 or parent == pid:
                    break
                pid = parent
        except Exception:
            pass

    message = json.dumps(
        {{
            "kind": payload.get("hook_event_name", ""),
            "session": payload.get("session_id", ""),
            "tool": payload.get("tool_name", ""),
            "hwnd": hwnd,
            "pids": pids,
        }}
    ).encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message, ({host!r}, {port}))
    sock.close()
except Exception:
    pass
'''


def settings_path(scope: str = "user") -> Path:
    if scope == "project":
        return Path.cwd() / ".claude" / "settings.json"
    return Path.home() / ".claude" / "settings.json"


def _python_for_hooks() -> str:
    """The interpreter the shim runs under.

    On Windows this is ``pythonw.exe`` -- the console-less build. Using plain
    ``python.exe`` would pop a console window on every prompt and every
    response, which is unusable.
    """
    exe = Path(sys.executable)
    if os.name == "nt":
        candidate = exe.with_name("pythonw.exe")
        if candidate.exists():
            return str(candidate)
        found = shutil.which("pythonw")
        if found:
            return found
    return str(exe)


def write_shim(cfg: Config, directory: Path | None = None) -> Path:
    directory = directory or state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    # The filename carries the marker that identifies our hooks in
    # settings.json. Relying on the *directory* containing "brainrot" would
    # break the moment BRAINROT_STATE_DIR points somewhere else, and a failed
    # match means uninstall silently leaves hooks behind while re-installing
    # stacks duplicates.
    path = directory / SHIM_NAME
    path.write_text(_SHIM_TEMPLATE.format(host=cfg.host, port=cfg.port), encoding="utf-8")
    return path


def hook_command(shim: Path) -> str:
    return f'"{_python_for_hooks()}" -S "{shim}"'


def _is_ours(entry: dict) -> bool:
    for hook in entry.get("hooks", []):
        if SHIM_NAME in str(hook.get("command", "")):
            return True
    return False


def install(
    cfg: Config,
    scope: str = "user",
    with_tool_events: bool = False,
    settings_file: Path | None = None,
) -> tuple[Path, list[str]]:
    """Register hooks, preserving anything already configured.

    Returns the settings path and the events registered.
    """
    shim = write_shim(cfg)
    command = hook_command(shim)
    events = list(DEFAULT_EVENTS) + (list(TOOL_EVENTS) if with_tool_events else [])

    path = settings_file or settings_path(scope)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict):
            settings = {}
    except (OSError, json.JSONDecodeError):
        settings = {}

    hooks = settings.setdefault("hooks", {})
    for event in events:
        entries = hooks.setdefault(event, [])
        # Drop any previous install of ours so re-running is idempotent rather
        # than stacking duplicate shims, while leaving other tools' hooks alone.
        entries[:] = [e for e in entries if not _is_ours(e)]
        entry: dict = {"hooks": [{"type": "command", "command": command}]}
        if event in TOOL_EVENTS:
            entry["matcher"] = "*"
        entries.append(entry)

    _write_json(path, settings)
    return path, events


def uninstall(scope: str = "user", settings_file: Path | None = None) -> Path:
    """Remove our hooks, leaving every other hook untouched."""
    path = settings_file or settings_path(scope)
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return path
    if not isinstance(settings, dict):
        return path

    hooks = settings.get("hooks", {})
    for event, entries in list(hooks.items()):
        if not isinstance(entries, list):
            continue
        entries[:] = [e for e in entries if not _is_ours(e)]
        if not entries:
            hooks.pop(event, None)
    if not hooks:
        settings.pop("hooks", None)

    _write_json(path, settings)
    return path


def _write_json(path: Path, data: dict) -> None:
    # Write-then-replace so an interrupted install cannot leave the user with a
    # truncated settings.json and a broken Claude Code.
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
