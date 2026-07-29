"""Thinking-state machine.

These cover the behaviours that make the overlay tolerable rather than
maddening, so they are worth more than their line count suggests.
"""

from __future__ import annotations

import pytest

from brainrot.state import ThinkingState, Visibility


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def state(clock: Clock) -> ThinkingState:
    return ThinkingState(grace_seconds=1.5, min_visible_seconds=3.0, clock=clock)


def test_short_burst_never_shows(state: ThinkingState, clock: Clock) -> None:
    """The single most important behaviour: quick turns must not flash."""
    state.handle("UserPromptSubmit", "s1")
    clock.advance(0.4)
    assert state.tick() is Visibility.PENDING

    state.handle("Stop", "s1")
    clock.advance(5.0)
    assert state.tick() is Visibility.HIDDEN
    assert not state.on_screen


def test_shows_after_grace_period(state: ThinkingState, clock: Clock) -> None:
    state.handle("UserPromptSubmit", "s1")
    clock.advance(1.4)
    assert state.tick() is Visibility.PENDING
    clock.advance(0.2)
    assert state.tick() is Visibility.VISIBLE


def test_lingers_for_minimum_duration(state: ThinkingState, clock: Clock) -> None:
    state.handle("UserPromptSubmit", "s1")
    clock.advance(2.0)
    assert state.tick() is Visibility.VISIBLE

    # Claude finishes almost immediately after the overlay appeared.
    state.handle("Stop", "s1")
    assert state.tick() is Visibility.LINGERING
    assert state.on_screen

    clock.advance(3.1)
    assert state.tick() is Visibility.HIDDEN


def test_resumed_work_cancels_linger(state: ThinkingState, clock: Clock) -> None:
    state.handle("UserPromptSubmit", "s1")
    clock.advance(2.0)
    state.handle("Stop", "s1")
    assert state.tick() is Visibility.LINGERING

    state.handle("UserPromptSubmit", "s1")
    assert state.tick() is Visibility.VISIBLE


def test_refcounts_across_sessions(state: ThinkingState, clock: Clock) -> None:
    """Two Claude Code windows: visible until the last one finishes."""
    state.handle("UserPromptSubmit", "s1")
    clock.advance(0.5)
    state.handle("UserPromptSubmit", "s2")
    clock.advance(1.5)
    assert state.tick() is Visibility.VISIBLE

    state.handle("Stop", "s1")
    clock.advance(4.0)
    # s2 is still working, so we stay up well past min_visible_seconds.
    assert state.tick() is Visibility.VISIBLE

    state.handle("Stop", "s2")
    clock.advance(4.0)
    assert state.tick() is Visibility.HIDDEN


def test_notification_hides_immediately(state: ThinkingState, clock: Clock) -> None:
    """A permission prompt means the user needs the terminal, now."""
    state.handle("UserPromptSubmit", "s1")
    clock.advance(2.0)
    assert state.tick() is Visibility.VISIBLE

    state.handle("Notification", "s1")
    assert state.tick() is Visibility.HIDDEN
    assert not state.on_screen


def test_suppression_clears_when_work_resumes(state: ThinkingState, clock: Clock) -> None:
    state.handle("UserPromptSubmit", "s1")
    clock.advance(2.0)
    state.handle("Notification", "s1")
    assert state.tick() is Visibility.HIDDEN

    # Permission granted, tools start running again.
    state.handle("PostToolUse", "s1", tool="Bash")
    clock.advance(2.0)
    assert state.tick() is Visibility.VISIBLE


def test_notification_can_be_disabled(clock: Clock) -> None:
    state = ThinkingState(
        grace_seconds=0.1, min_visible_seconds=0.0, hide_on_notification=False, clock=clock
    )
    state.handle("UserPromptSubmit", "s1")
    clock.advance(0.5)
    state.handle("Notification", "s1")
    assert state.tick() is Visibility.VISIBLE


def test_tool_events_set_caption(state: ThinkingState, clock: Clock) -> None:
    state.handle("UserPromptSubmit", "s1")
    state.handle("PreToolUse", "s1", tool="Grep")
    assert state.caption == "Grep"


def test_session_end_releases_the_session(state: ThinkingState, clock: Clock) -> None:
    state.handle("UserPromptSubmit", "s1")
    clock.advance(2.0)
    assert state.tick() is Visibility.VISIBLE

    state.handle("SessionEnd", "s1")
    clock.advance(4.0)
    assert state.tick() is Visibility.HIDDEN


def test_daemon_started_mid_turn_still_shows(state: ThinkingState, clock: Clock) -> None:
    """Tool traffic with no preceding prompt is still evidence of work."""
    state.handle("PostToolUse", "s1", tool="Read")
    clock.advance(2.0)
    assert state.tick() is Visibility.VISIBLE
