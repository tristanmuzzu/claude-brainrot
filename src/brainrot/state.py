"""Thinking-state machine.

Translating "Claude is working" into "the overlay is on screen" is not a
straight passthrough, and the difference is the whole user experience:

  * **Grace period.** Most turns are short. Showing instantly means the strip
    strobes on every quick answer, which is worse than not having it at all.
    Nothing appears until Claude has been busy for ``grace_seconds``.

  * **Minimum visible time.** Having cleared the grace period, the overlay
    stays for ``min_visible_seconds`` even if Claude finishes immediately
    after. A flash-and-vanish reads as a glitch.

  * **Refcounting.** Several Claude Code windows can be busy at once. The
    overlay is up while *any* session is thinking, and only comes down when the
    last one finishes.

  * **Suppression.** When Claude needs a permission decision, your attention
    belongs on the terminal, so the overlay gets out of the way.

The clock is injected so all of this is testable without sleeping.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

# Hook events that mean "this session is actively working".
_START_EVENTS = frozenset({"UserPromptSubmit"})
_END_EVENTS = frozenset({"Stop"})
_ACTIVITY_EVENTS = frozenset({"PreToolUse", "PostToolUse"})
_SUPPRESS_EVENTS = frozenset({"Notification"})
_TEARDOWN_EVENTS = frozenset({"SessionEnd"})


class Visibility(Enum):
    HIDDEN = "hidden"
    #: Thinking, but still inside the grace period -- nothing drawn yet.
    PENDING = "pending"
    VISIBLE = "visible"
    #: Thinking finished, holding the minimum visible duration.
    LINGERING = "lingering"


@dataclass
class ThinkingState:
    grace_seconds: float = 1.5
    min_visible_seconds: float = 3.0
    hide_on_notification: bool = True
    clock: Callable[[], float] = time.monotonic

    _thinking: set[str] = field(default_factory=set)
    _visibility: Visibility = Visibility.HIDDEN
    _busy_since: float | None = None
    _shown_at: float | None = None
    _released_at: float | None = None
    _suppressed: bool = False
    caption: str = ""

    # -- queries ----------------------------------------------------------

    @property
    def visibility(self) -> Visibility:
        return self._visibility

    @property
    def on_screen(self) -> bool:
        return self._visibility in (Visibility.VISIBLE, Visibility.LINGERING)

    @property
    def busy(self) -> bool:
        return bool(self._thinking)

    # -- input ------------------------------------------------------------

    def handle(self, kind: str, session: str = "", tool: str = "") -> None:
        """Fold one hook event into the state."""
        session = session or "default"

        if kind in _START_EVENTS:
            # A new prompt means the user is done deciding things, so any
            # pending-permission suppression is stale.
            self._suppressed = False
            self.caption = ""
            self._begin(session)
        elif kind in _END_EVENTS:
            self._suppressed = False
            self._end(session)
        elif kind in _ACTIVITY_EVENTS:
            self._suppressed = False
            if tool:
                self.caption = tool
            # Tool traffic without a preceding prompt happens when the daemon
            # starts mid-turn; treat it as evidence the session is working.
            self._begin(session)
        elif kind in _SUPPRESS_EVENTS:
            if self.hide_on_notification:
                self._suppressed = True
        elif kind in _TEARDOWN_EVENTS:
            self._end(session)

        self.tick()

    def _begin(self, session: str) -> None:
        if session in self._thinking:
            return
        was_idle = not self._thinking
        self._thinking.add(session)
        if was_idle:
            self._busy_since = self.clock()
            self._released_at = None

    def _end(self, session: str) -> None:
        self._thinking.discard(session)
        if not self._thinking:
            self._released_at = self.clock()

    # -- time -------------------------------------------------------------

    def tick(self) -> Visibility:
        """Advance timers. Call every frame; returns the current visibility."""
        now = self.clock()

        if self._suppressed:
            self._visibility = Visibility.HIDDEN
            self._shown_at = None
            return self._visibility

        if self._thinking:
            if self._visibility in (Visibility.VISIBLE, Visibility.LINGERING):
                # Work resumed while we were holding the tail -- back to normal.
                self._visibility = Visibility.VISIBLE
            else:
                started = self._busy_since if self._busy_since is not None else now
                if now - started >= self.grace_seconds:
                    if self._shown_at is None:
                        self._shown_at = now
                    self._visibility = Visibility.VISIBLE
                else:
                    self._visibility = Visibility.PENDING
            return self._visibility

        # Nothing is thinking. Whether the overlay earned its minimum visible
        # time is derived from the timestamps rather than from whether we
        # happened to tick during the grace window -- an event burst that
        # starts and ends between two frames must still be judged correctly.
        cleared_grace = (
            self._busy_since is not None
            and self._released_at is not None
            and self._released_at - self._busy_since >= self.grace_seconds
        )
        if self._visibility in (Visibility.VISIBLE, Visibility.LINGERING) or cleared_grace:
            if self._shown_at is None:
                assert self._busy_since is not None
                self._shown_at = self._busy_since + self.grace_seconds
            shown_at = self._shown_at
            if now - shown_at >= self.min_visible_seconds:
                self._visibility = Visibility.HIDDEN
                self._retire()
            else:
                self._visibility = Visibility.LINGERING
        else:
            self._visibility = Visibility.HIDDEN
            self._retire()

        return self._visibility

    def _retire(self) -> None:
        """Forget the finished turn so its timestamps cannot re-trigger a show."""
        self._shown_at = None
        self._busy_since = None
        self._released_at = None
        self.caption = ""

    def reset(self) -> None:
        self._thinking.clear()
        self._visibility = Visibility.HIDDEN
        self._busy_since = None
        self._shown_at = None
        self._released_at = None
        self._suppressed = False
        self.caption = ""
