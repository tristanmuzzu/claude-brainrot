"""Local Codex/ChatGPT integration, without requiring an account or app."""

import json
import socket
import subprocess
import sys

import pytest

from brainrot.cli import build_parser, main
from brainrot.config import Config
from brainrot.doctor import FAIL, _check_hooks
from brainrot.hookinstall import (
    CODEX_EVENTS, CODEX_SHIM_NAME, SHIM_NAME, install, settings_path, uninstall, write_shim,
)
from brainrot.ipc import Event
from brainrot.overlay.shell import ShellWindow, Snapshot
from brainrot.state import ThinkingState, Visibility


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setenv("BRAINROT_STATE_DIR", str(tmp_path / "state"))
    return tmp_path


def test_codex_and_chatgpt_use_the_same_user_home(isolated):
    expected = isolated / "codex-home" / "hooks.json"
    assert settings_path(agent="codex") == expected
    assert settings_path(agent="chatgpt") == expected
    assert settings_path(agent="claude").name == "settings.json"


def test_project_scope_does_not_use_codex_home(isolated, monkeypatch):
    monkeypatch.chdir(isolated)
    assert settings_path("project", "chatgpt") == isolated / ".codex" / "hooks.json"


def test_codex_home_defaults_to_dot_codex(isolated, monkeypatch):
    from pathlib import Path

    monkeypatch.delenv("CODEX_HOME")
    monkeypatch.setattr(Path, "home", lambda: isolated)
    assert settings_path(agent="codex") == isolated / ".codex" / "hooks.json"


def test_install_alias_is_idempotent_and_preserves_other_hooks(isolated):
    path = settings_path(agent="codex")
    path.parent.mkdir()
    other = {"matcher": "*", "hooks": [{"type": "command", "command": "other-hook"}]}
    path.write_text(json.dumps({"description": "keep me", "hooks": {"Stop": [other]}}))
    for agent in ("codex", "chatgpt", "codex"):
        installed, events = install(Config(), agent=agent)
        assert installed == path
        assert set(events) == set(CODEX_EVENTS)
    data = json.loads(path.read_text())
    assert data["description"] == "keep me"
    assert data["hooks"]["Stop"][0] == other
    for event in CODEX_EVENTS:
        ours = [e for e in data["hooks"][event]
                if CODEX_SHIM_NAME in e["hooks"][0]["command"]]
        assert len(ours) == 1
        assert ours[0]["hooks"][0]["timeout"] == 1
    assert "Notification" not in data["hooks"]
    assert "PreToolUse" not in data["hooks"]
    uninstall(agent="chatgpt")
    assert json.loads(path.read_text()) == {"description": "keep me", "hooks": {"Stop": [other]}}


def test_tool_events_can_be_removed_without_losing_activity_heartbeats(isolated):
    path, _ = install(Config(), agent="codex", with_tool_events=True)
    assert "PreToolUse" in json.loads(path.read_text())["hooks"]
    install(Config(), agent="codex")
    hooks = json.loads(path.read_text())["hooks"]
    assert "PreToolUse" not in hooks
    assert "PostToolUse" in hooks
    assert len(hooks["PostToolUse"]) == 1


@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_mixed_handler_groups_preserve_foreign_handlers(isolated, agent):
    path = isolated / "mixed.json"
    foreign = {"type": "command", "command": "another-tool"}
    other_provider = {"type": "command", "command": (
        SHIM_NAME if agent == "codex" else CODEX_SHIM_NAME)}
    ours = {"type": "command", "command": (
        CODEX_SHIM_NAME if agent == "codex" else SHIM_NAME)}
    group = {"matcher": "special", "hooks": [foreign, ours, other_provider]}
    path.write_text(json.dumps({"hooks": {"Stop": [group]}}))
    install(Config(), agent=agent, settings_file=path)
    uninstall(agent=agent, settings_file=path)
    assert json.loads(path.read_text())["hooks"]["Stop"] == [
        {"matcher": "special", "hooks": [foreign, other_provider]}]


@pytest.mark.parametrize("content", ["broken JSON", "[]", '{"hooks": 3}',
                                     '{"hooks": {"Stop": {}}}'])
def test_install_leaves_invalid_config_untouched(isolated, content):
    path = isolated / "bad.json"
    path.write_text(content)
    with pytest.raises(ValueError, match="left unchanged"):
        install(Config(), agent="codex", settings_file=path)
    assert path.read_text() == content
    assert not (isolated / "state" / CODEX_SHIM_NAME).exists()


def _fire(shim, kind, **fields):
    result = subprocess.run(
        [sys.executable, "-S", str(shim)],
        input=json.dumps({"hook_event_name": kind, "session_id": "same-id", **fields}),
        text=True, capture_output=True, timeout=5,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_desktop_lifecycle_through_the_real_shim(isolated):
    """Payload -> subprocess -> UDP -> state -> desktop host matching."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.settimeout(3)
        shim = write_shim(Config(port=listener.getsockname()[1]), agent="codex")
        state = ThinkingState(grace_seconds=0, min_visible_seconds=0)
        # The main desktop process is an ancestor even when the hook is run
        # by its app-server child. One process can own several app windows.
        for kind in ("UserPromptSubmit", "PermissionRequest", "PostToolUse", "Interrupt"):
            _fire(shim, kind, tool_name="Bash", prompt="not forwarded",
                  tool_input={"secret": "not forwarded"})
            packet = listener.recv(65536)
            assert b"not forwarded" not in packet
            event = Event.parse(packet)
            assert event.session == "codex:same-id"
            if sys.platform.startswith("linux"):
                assert event.pids
                app_pid = event.pids[-1]
                snapshot = Snapshot(focus=42, windows=(
                    ShellWindow(41, app_pid, "ChatGPT", (0, 0, 100, 100)),
                    ShellWindow(42, app_pid, "ChatGPT", (0, 0, 100, 100)),
                ))
                host = snapshot.host_for(event.pids)
                assert host == 42
            else:
                host = 42
            state.handle(event.kind, event.session, event.tool, host)
            if kind == "Interrupt":
                assert state.visibility is Visibility.HIDDEN
                assert not state.busy
            else:
                assert state.visibility is Visibility.VISIBLE
                assert state.hosts == frozenset({42})
                assert state.caption == ""
        # Late child results use the parent's session id but cannot restart it.
        _fire(shim, "PostToolUse", tool_name="Bash")
        event = Event.parse(listener.recv(65536))
        state.handle(event.kind, event.session, event.tool)
        assert not state.busy


def test_automatic_approval_keeps_the_existing_run_visible():
    """PermissionRequest precedes automatic review too, not just user prompts.

    PostToolUse may arrive much later. The strip must keep the same visible
    run throughout the command instead of fading away and rebuilding it.
    """
    now = [0.0]
    state = ThinkingState(grace_seconds=1.5, min_visible_seconds=3,
                          clock=lambda: now[0])
    session = "codex:busy"
    state.handle("UserPromptSubmit", session, hwnd=42)
    now[0] = 2
    assert state.tick() is Visibility.VISIBLE
    shown_at = state._shown_at
    state.handle("PermissionRequest", session, tool="Bash", hwnd=99)
    for elapsed in (3, 6, 20):
        now[0] = elapsed
        assert state.tick() is Visibility.VISIBLE
        assert state._shown_at == shown_at
        assert state.hosts == frozenset({42})
    state.handle("CodexActivity", session)
    assert state.visibility is Visibility.VISIBLE
    state.handle("Stop", session)
    assert state.visibility is Visibility.HIDDEN


def test_permission_request_cannot_restart_a_finished_codex_turn():
    state = ThinkingState(grace_seconds=0, min_visible_seconds=0)
    state.handle("UserPromptSubmit", "codex:busy", hwnd=42)
    state.handle("Stop", "codex:busy")
    state.handle("PermissionRequest", "codex:busy")
    assert not state.busy
    assert state.visibility is Visibility.HIDDEN


def test_codex_tool_captions_are_opt_in(isolated):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.settimeout(3)
        cfg = Config(port=listener.getsockname()[1])
        shim = write_shim(cfg, agent="codex", with_tool_events=True)
        _fire(shim, "PostToolUse", tool_name="Bash")
        event = Event.parse(listener.recv(65536))
        assert event.kind == "CodexActivity"
        assert event.tool == "Bash"


def test_same_session_ids_from_different_agents_remain_independent():
    state = ThinkingState(grace_seconds=0, min_visible_seconds=0)
    state.handle("UserPromptSubmit", "same-id", hwnd=1)
    state.handle("UserPromptSubmit", "codex:same-id", hwnd=2)
    state.handle("Stop", "codex:same-id")
    assert state.sessions == frozenset({"same-id"})
    assert state.hosts == frozenset({1})


def test_doctor_checks_selected_agent_and_required_events(isolated):
    path, _ = install(Config(), agent="chatgpt")
    checks = _check_hooks(Config(), "chatgpt")
    assert not any(c.status == FAIL for c in checks)
    data = json.loads(path.read_text())
    del data["hooks"]["Interrupt"]
    path.write_text(json.dumps(data))
    assert any(c.status == FAIL and "Interrupt" in c.detail
               for c in _check_hooks(Config(), "codex"))
    path.with_name("config.toml").write_text("[features]\nhooks = false\n")
    assert any(c.status == FAIL and c.name == "hooks-on"
               for c in _check_hooks(Config(), "codex"))


def test_cli_default_stays_claude_and_codex_install_uses_selected_home(isolated, capsys):
    parser = build_parser()
    for command in ("install", "uninstall", "doctor"):
        assert parser.parse_args([command]).agent == "claude"
        assert parser.parse_args([command, "--agent", "chatgpt"]).agent == "chatgpt"
    assert main(["install", "--agent", "codex", "--no-extension"]) == 0
    assert settings_path(agent="codex").exists()
    assert "trust" in capsys.readouterr().out
    assert main(["uninstall", "--agent", "chatgpt"]) == 0
    assert "hooks" not in json.loads(settings_path(agent="codex").read_text())


def test_cli_reports_invalid_settings_without_overwriting_them(isolated, capsys):
    path = settings_path(agent="codex")
    path.parent.mkdir()
    path.write_text("bad")
    assert main(["install", "--agent", "codex", "--no-extension"]) == 1
    assert "left unchanged" in capsys.readouterr().err
    assert path.read_text() == "bad"
