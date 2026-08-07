"""End-to-end: real daemon, real UDP events, real frames.

Everything below the window is exercised for real here -- the listener thread,
the state machine, scene construction, and the render loop -- with only the
window swapped for the shared offscreen one.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from conftest import ensure_window

from brainrot.config import Config
from brainrot.engine.loop import Overlay
from brainrot.engine.window import HeadlessWindow
from brainrot.ipc import send

PORT = 47870


def wait_for(predicate, timeout: float = 8.0, interval: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


@pytest.fixture
def daemon(tmp_path: Path, monkeypatch):
    # The shared window must exist before the daemon thread starts, so every
    # raylib call after this point happens in one thread at a time.
    ensure_window()
    monkeypatch.setenv("BRAINROT_STATE_DIR", str(tmp_path))
    cfg = Config(
        port=PORT,
        grace_seconds=0.3,
        min_visible_seconds=0.4,
        fade_seconds=0.05,
        fps=60,
    )
    overlay = Overlay(cfg, HeadlessWindow())
    thread = threading.Thread(target=overlay.run, daemon=True)
    thread.start()
    assert wait_for(lambda: overlay.running)
    yield overlay
    overlay.running = False
    thread.join(timeout=5.0)


def test_prompt_shows_and_stop_hides(daemon: Overlay) -> None:
    send("127.0.0.1", PORT, "UserPromptSubmit", session="s1")

    assert wait_for(lambda: daemon.state.on_screen), "overlay never appeared"
    assert wait_for(lambda: daemon.scene is not None), "no scene was built"
    assert wait_for(lambda: daemon.alpha > 0.9), "never faded in"

    send("127.0.0.1", PORT, "Stop", session="s1")

    assert wait_for(lambda: not daemon.state.on_screen), "overlay never went away"
    # The scene must actually be released, not just hidden -- that is what makes
    # the idle path free and the next appearance freshly generated.
    assert wait_for(lambda: daemon.scene is None), "scene was not released"
    assert daemon.alpha == pytest.approx(0.0, abs=0.01)


def test_short_burst_never_appears(daemon: Overlay) -> None:
    send("127.0.0.1", PORT, "UserPromptSubmit", session="s1")
    time.sleep(0.1)
    send("127.0.0.1", PORT, "Stop", session="s1")

    time.sleep(1.0)
    assert not daemon.state.on_screen
    assert daemon.scene is None
    assert daemon.alpha == pytest.approx(0.0, abs=0.01)


def test_each_appearance_generates_a_new_world(daemon: Overlay) -> None:
    """The core promise: it is never the same twice."""
    seeds = []
    for i in range(3):
        send("127.0.0.1", PORT, "UserPromptSubmit", session=f"s{i}")
        assert wait_for(lambda: daemon.scene is not None)
        seeds.append(daemon.scene.ctx.seed.run)
        send("127.0.0.1", PORT, "Stop", session=f"s{i}")
        assert wait_for(lambda: daemon.scene is None)

    assert len(set(seeds)) == 3, f"repeated run seeds: {seeds}"
    assert seeds == sorted(seeds), "run counter went backwards"


def test_concurrent_sessions_are_refcounted(daemon: Overlay) -> None:
    send("127.0.0.1", PORT, "UserPromptSubmit", session="a")
    send("127.0.0.1", PORT, "UserPromptSubmit", session="b")
    assert wait_for(lambda: daemon.state.on_screen)

    send("127.0.0.1", PORT, "Stop", session="a")
    time.sleep(0.8)
    assert daemon.state.on_screen, "hid while another session was still working"

    send("127.0.0.1", PORT, "Stop", session="b")
    assert wait_for(lambda: not daemon.state.on_screen)


def test_notification_hides_mid_turn(daemon: Overlay) -> None:
    send("127.0.0.1", PORT, "UserPromptSubmit", session="s1")
    assert wait_for(lambda: daemon.state.on_screen)

    send("127.0.0.1", PORT, "Notification", session="s1")
    assert wait_for(lambda: not daemon.state.on_screen), "did not yield for a prompt"


def test_unknown_events_are_ignored(daemon: Overlay) -> None:
    send("127.0.0.1", PORT, "SomeFutureHook", session="s1")
    time.sleep(0.6)
    assert not daemon.state.on_screen
    assert daemon.running, "daemon died on an unrecognised event"


def test_event_carries_hwnd_without_breaking(daemon: Overlay) -> None:
    """The host-window handle rides along on prompt events; a headless
    backend must simply ignore it."""
    send("127.0.0.1", PORT, "UserPromptSubmit", session="s1", hwnd=123456)
    assert wait_for(lambda: daemon.state.on_screen)
    send("127.0.0.1", PORT, "Stop", session="s1")
    assert wait_for(lambda: not daemon.state.on_screen)
