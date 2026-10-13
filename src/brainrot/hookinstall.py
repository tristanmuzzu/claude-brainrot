"""Claude Code and local Codex/ChatGPT hook installation.

The shim written by this module runs inside the agent's critical path, so it
is built around three constraints:

1. **It must never block.** One UDP datagram, no connect, no response read. If
   the daemon is dead, stopped, or wedged, the packet is dropped by the kernel
   and the agent carries on. A hook that can hang is a hook that can hang
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
CODEX_SHIM_NAME = "brainrot_codex_hook.py"
AGENTS = ("claude", "codex", "chatgpt")

#: Claude hooks we register. PreToolUse/PostToolUse are deliberately absent by
#: default -- they fire on every single tool call, and the overlay needs
#: nothing from them that Stop and UserPromptSubmit do not already provide.
DEFAULT_EVENTS = ("UserPromptSubmit", "Stop", "Notification", "SessionEnd")

#: Opt-in via --with-tool-events. Buys live tool captions at the cost of
#: running the shim on the hot path.
TOOL_EVENTS = ("PreToolUse", "PostToolUse")

# Codex has no Notification event. PermissionRequest is a progress signal,
# not proof that a person must approve: automatic review fires it too.
# PostToolUse keeps long-running turns alive, even without live captions.
CODEX_EVENTS = ("UserPromptSubmit", "Stop", "Interrupt", "PermissionRequest",
                "PostToolUse", "SessionEnd")


def canonical_agent(agent: str) -> str:
    if agent not in AGENTS:
        raise ValueError(f"unknown agent: {agent}")
    return "codex" if agent == "chatgpt" else agent


def shim_name(agent: str = "claude") -> str:
    return CODEX_SHIM_NAME if canonical_agent(agent) == "codex" else SHIM_NAME


def events_for(agent: str = "claude", with_tool_events: bool = False) -> list[str]:
    events = list(CODEX_EVENTS if canonical_agent(agent) == "codex" else DEFAULT_EVENTS)
    if with_tool_events:
        events.extend(event for event in TOOL_EVENTS if event not in events)
    return events


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
    kind = payload.get("hook_event_name", "")
    session = payload.get("session_id", "")
    tool = payload.get("tool_name", "")
    if {agent!r} == "codex":
        # Keep providers independent even if they supply the same session id.
        session = "codex:" + session
        if kind in ("PreToolUse", "PostToolUse"):
            kind = "CodexActivity"
            if not {with_tool_events!r}:
                tool = ""

    # The window you are typing into when a prompt hook fires IS the agent's
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
    # instead -- the terminal or desktop app running the agent is one of these
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
            "kind": kind,
            "session": session,
            "tool": tool,
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


def settings_path(scope: str = "user", agent: str = "claude") -> Path:
    agent = canonical_agent(agent)
    if scope not in ("user", "project"):
        raise ValueError(f"unknown scope: {scope}")
    if agent == "codex":
        root = (Path.cwd() / ".codex" if scope == "project" else
                Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"))
        return root / "hooks.json"
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


def write_shim(cfg: Config, directory: Path | None = None,
               agent: str = "claude", with_tool_events: bool = False) -> Path:
    directory = directory or state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    # The filename carries the marker that identifies our hooks in
    # settings.json. Relying on the *directory* containing "brainrot" would
    # break the moment BRAINROT_STATE_DIR points somewhere else, and a failed
    # match means uninstall silently leaves hooks behind while re-installing
    # stacks duplicates.
    path = directory / shim_name(agent)
    path.write_text(_SHIM_TEMPLATE.format(host=cfg.host, port=cfg.port,
                    agent=canonical_agent(agent), with_tool_events=with_tool_events),
                    encoding="utf-8")
    return path


def hook_command(shim: Path) -> str:
    return f'"{_python_for_hooks()}" -S "{shim}"'


def _is_ours(entry, agent: str = "claude") -> bool:
    # Hand-edited settings can hold anything; a malformed entry is simply not
    # ours rather than a crash in install/uninstall/doctor.
    if not isinstance(entry, dict):
        return False
    hooks = entry.get("hooks")
    if not isinstance(hooks, list):
        return False
    for hook in hooks:
        if isinstance(hook, dict) and shim_name(agent) in str(hook.get("command", "")):
            return True
    return False


def install(
    cfg: Config,
    scope: str = "user",
    with_tool_events: bool = False,
    settings_file: Path | None = None,
    agent: str = "claude",
) -> tuple[Path, list[str]]:
    """Register hooks, preserving anything already configured.

    Returns the settings path and the events registered.
    """
    agent = canonical_agent(agent)
    path = settings_file or settings_path(scope, agent)
    settings = _read_settings(path)
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path}: hooks must be an object; file left unchanged")
    events = events_for(agent, with_tool_events)
    if any(event in hooks and not isinstance(hooks[event], list) for event in events):
        raise ValueError(f"{path}: hook events must be arrays; file left unchanged")
    shim = write_shim(cfg, agent=agent, with_tool_events=with_tool_events)
    command = hook_command(shim)
    # Sweep *every* event for a previous install of ours, not just the ones
    # being registered: installing with --with-tool-events and later without
    # used to leave the PreToolUse/PostToolUse shims in place forever -- a
    # shim spawn on every tool call the user asked to stop paying for.
    _remove_ours(hooks, agent)
    for event in events:
        entries = hooks.setdefault(event, [])
        handler: dict = {"type": "command", "command": command}
        if agent == "codex":
            handler["timeout"] = 1
        entry: dict = {"hooks": [handler]}
        if event in TOOL_EVENTS or event == "PermissionRequest":
            entry["matcher"] = "*"
        entries.append(entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, settings)
    return path, events


def uninstall(scope: str = "user", settings_file: Path | None = None,
              agent: str = "claude") -> Path:
    """Remove our hooks, leaving every other hook untouched."""
    agent = canonical_agent(agent)
    path = settings_file or settings_path(scope, agent)
    if not path.exists():
        return path
    settings = _read_settings(path)
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path}: hooks must be an object; file left unchanged")
    _remove_ours(hooks, agent)
    if not hooks:
        settings.pop("hooks", None)

    _write_json(path, settings)
    return path


def _remove_ours(hooks: dict, agent: str) -> None:
    """Remove individual handlers, preserving mixed matcher groups."""
    for event, entries in list(hooks.items()):
        if not isinstance(entries, list):
            continue
        kept = []
        for entry in entries:
            if _is_ours(entry, agent):
                remaining = [h for h in entry["hooks"]
                             if not (isinstance(h, dict) and
                                     shim_name(agent) in str(h.get("command", "")))]
                if remaining:
                    kept.append({**entry, "hooks": remaining})
            else:
                kept.append(entry)
        entries[:] = kept
        if not entries:
            hooks.pop(event, None)


def _read_settings(path: Path) -> dict:
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON; file left unchanged") from exc
    if not isinstance(settings, dict):
        raise ValueError(f"{path}: settings must be an object; file left unchanged")
    return settings


def _write_json(path: Path, data: dict) -> None:
    # Write-then-replace so an interrupted install cannot leave the user with a
    # truncated settings.json/hooks.json and a broken agent setup.
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
