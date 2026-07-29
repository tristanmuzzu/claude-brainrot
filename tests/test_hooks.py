"""Hook installation and the IPC transport."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from brainrot.config import Config
from brainrot.hookinstall import DEFAULT_EVENTS, TOOL_EVENTS, install, uninstall, write_shim
from brainrot.ipc import Event, EventListener, send


@pytest.fixture
def settings(tmp_path: Path) -> Path:
    return tmp_path / "settings.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_install_registers_the_expected_events(settings: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BRAINROT_STATE_DIR", str(tmp_path))
    _path, events = install(Config(), settings_file=settings)
    assert set(events) == set(DEFAULT_EVENTS)

    hooks = read(settings)["hooks"]
    for event in DEFAULT_EVENTS:
        assert event in hooks
    # Tool events cost a shim launch per tool call, so they stay opt-in.
    for event in TOOL_EVENTS:
        assert event not in hooks


def test_tool_events_are_opt_in(settings: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BRAINROT_STATE_DIR", str(tmp_path))
    install(Config(), settings_file=settings, with_tool_events=True)
    hooks = read(settings)["hooks"]
    for event in TOOL_EVENTS:
        assert event in hooks
        assert hooks[event][0]["matcher"] == "*"


def test_install_is_idempotent(settings: Path, tmp_path: Path, monkeypatch) -> None:
    """Re-running install must not stack duplicate shims."""
    monkeypatch.setenv("BRAINROT_STATE_DIR", str(tmp_path))
    for _ in range(4):
        install(Config(), settings_file=settings)
    hooks = read(settings)["hooks"]
    for event in DEFAULT_EVENTS:
        assert len(hooks[event]) == 1


def test_install_preserves_other_tools_hooks(settings: Path, tmp_path: Path, monkeypatch) -> None:
    """Someone else's hooks are not ours to touch."""
    monkeypatch.setenv("BRAINROT_STATE_DIR", str(tmp_path))
    settings.write_text(
        json.dumps(
            {
                "model": "opus",
                "hooks": {
                    "Stop": [{"hooks": [{"type": "command", "command": "notify-send done"}]}],
                    "PreCompact": [{"hooks": [{"type": "command", "command": "echo hi"}]}],
                },
            }
        ),
        encoding="utf-8",
    )

    install(Config(), settings_file=settings)
    data = read(settings)

    assert data["model"] == "opus"
    assert data["hooks"]["PreCompact"][0]["hooks"][0]["command"] == "echo hi"
    stop_commands = [h["command"] for entry in data["hooks"]["Stop"] for h in entry["hooks"]]
    assert "notify-send done" in stop_commands
    assert any("brainrot" in c for c in stop_commands)


def test_uninstall_removes_only_our_hooks(settings: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BRAINROT_STATE_DIR", str(tmp_path))
    settings.write_text(
        json.dumps(
            {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "notify-send done"}]}]}}
        ),
        encoding="utf-8",
    )
    install(Config(), settings_file=settings)
    uninstall(settings_file=settings)

    data = read(settings)
    commands = [h["command"] for entry in data["hooks"]["Stop"] for h in entry["hooks"]]
    assert commands == ["notify-send done"]


def test_uninstall_on_missing_file_is_harmless(tmp_path: Path) -> None:
    uninstall(settings_file=tmp_path / "nope.json")


def test_shim_sends_a_datagram(tmp_path: Path) -> None:
    """End-to-end: run the real generated shim and catch what it emits."""
    cfg = Config(port=47899)
    shim = write_shim(cfg, tmp_path)

    received: list[Event] = []
    listener = EventListener(cfg.host, cfg.port, received.append)
    listener.start()
    try:
        payload = json.dumps(
            {"hook_event_name": "UserPromptSubmit", "session_id": "abc123", "tool_name": ""}
        )
        result = subprocess.run(
            [sys.executable, "-S", str(shim)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr

        deadline = time.monotonic() + 3.0
        while not received and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        listener.stop()

    assert len(received) == 1
    assert received[0].kind == "UserPromptSubmit"
    assert received[0].session == "abc123"


def test_shim_never_fails_on_garbage_input(tmp_path: Path) -> None:
    """The shim runs inside Claude Code. It must not raise, ever."""
    shim = write_shim(Config(port=47898), tmp_path)
    for payload in ("", "not json", "[]", "null"):
        result = subprocess.run(
            [sys.executable, "-S", str(shim)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert result.stderr == ""


def test_send_to_a_dead_daemon_is_silent() -> None:
    """Nothing is listening on this port; this must simply return."""
    send("127.0.0.1", 47897, "Stop")


def test_event_parsing_rejects_junk() -> None:
    assert Event.parse(b"not json") is None
    assert Event.parse(b"[]") is None
    assert Event.parse(b'{"no_kind": 1}') is None
    assert Event.parse(b'{"kind": "Stop"}') == Event(kind="Stop")


def test_listener_survives_a_handler_exception() -> None:
    """One bad event must not take the listener down for the session."""
    seen: list[Event] = []

    def handler(event: Event) -> None:
        if event.kind == "boom":
            raise RuntimeError("scene bug")
        seen.append(event)

    listener = EventListener("127.0.0.1", 47896, handler)
    listener.start()
    try:
        send("127.0.0.1", 47896, "boom")
        time.sleep(0.15)
        send("127.0.0.1", 47896, "Stop")

        deadline = time.monotonic() + 3.0
        while not seen and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        listener.stop()

    assert [e.kind for e in seen] == ["Stop"]
