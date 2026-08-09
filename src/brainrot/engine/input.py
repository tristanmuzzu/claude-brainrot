"""Taking the wheel: hand control of a scene to whoever is at the keyboard.

The scenes drive themselves. This module lets a person interrupt that, and
hands it back when they stop.

The awkward part is that the overlay is built not to receive input. Clicks
fall through it and it never takes focus -- which is the entire reason it is
not annoying, and also the reason it cannot see a key press. There are three
ways round that and only one of them is acceptable:

* Read every key. Works without focus, and means arrow keys drive the runner
  *while you are typing into Claude Code*, where arrows move your cursor. No.
* Install a system-wide keyboard hook. Works, and a background toy has no
  business installing one. No.
* Watch for one deliberate chord, and only on seeing it drop the overlay bits
  and take focus, at which point raylib reads the keyboard the ordinary way.
  Nothing is intercepted until it is asked for, and what is watched is a
  single specific combination rather than everything typed.

The third one is what this does. Releasing control puts the styles back and
returns focus to the window it was taken from, so the overlay goes back to
being ignorable.

The two platforms get there differently, and the difference is instructive.
Windows *polls* the chord, because ``GetAsyncKeyState`` can test one specific
combination without focus -- which also means the chord can never be taken
away from another program, and can never discover that another program
already owns it. GNOME *grabs* it, inside the shell extension, because a
Wayland client cannot register a global hotkey at all -- which makes the chord
genuinely ours, and means nothing typed anywhere else is readable even in
principle. :mod:`brainrot.overlay` hides the difference behind
``poll_chord`` and ``takeover_state``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .. import overlay
from . import rl

#: Seconds of no input before a scene resumes driving itself. Overridable per
#: install via ``Config.handback_seconds``.
IDLE_HANDBACK = 8.0


@dataclass
class Intent:
    """What the player is asking for this frame, in scene-neutral terms."""

    left: bool = False
    right: bool = False
    jump: bool = False
    duck: bool = False

    def any(self) -> bool:
        return self.left or self.right or self.jump or self.duck


@dataclass
class Controller:
    """Reads the keyboard, and tracks whether anyone is actually driving."""

    #: True while a person is in charge; scenes check this to stand down.
    engaged: bool = False
    last_input: float = field(default=-1e9)
    #: set when the player takes over or hands back, for the caption
    changed_at: float = field(default=-1e9)
    handback: float = IDLE_HANDBACK

    def poll(self, now: float, focused: bool) -> Intent:
        """Sample the keys and decide who is driving.

        ``focused`` says whether this window can legitimately see key presses.
        When it cannot, nothing is read at all -- that is the whole contract.
        """
        intent = Intent()
        if not focused:
            if self.engaged:
                self._set(False, now)
            return intent

        intent.left = bool(rl.IsKeyDown(rl.KEY_LEFT) or rl.IsKeyDown(rl.KEY_A))
        intent.right = bool(rl.IsKeyDown(rl.KEY_RIGHT) or rl.IsKeyDown(rl.KEY_D))
        intent.jump = bool(rl.IsKeyDown(rl.KEY_UP) or rl.IsKeyDown(rl.KEY_W)
                           or rl.IsKeyDown(rl.KEY_SPACE))
        intent.duck = bool(rl.IsKeyDown(rl.KEY_DOWN) or rl.IsKeyDown(rl.KEY_S)
                           or rl.IsKeyDown(rl.KEY_LEFT_CONTROL))

        if intent.any():
            self.last_input = now
            if not self.engaged:
                self._set(True, now)
        elif self.engaged and now - self.last_input > self.handback:
            # Hands off the keys for long enough: give it back rather than
            # leaving a motionless runner waiting for someone who has gone.
            self._set(False, now)
        return intent

    def _set(self, engaged: bool, now: float) -> None:
        self.engaged = engaged
        self.changed_at = now

    def caption(self, now: float) -> str:
        """Momentary banner when control changes hands."""
        if now - self.changed_at > 1.6:
            return ""
        return "you have control" if self.engaged else "autopilot"


# ---------------------------------------------------------------------------
# The deliberate takeover, and the deliberate drag
# ---------------------------------------------------------------------------


class Mover:
    """Hold the chord, drag the strip somewhere better.

    Automatic placement knows where the Claude Code window is and nothing at
    all about where that window keeps its toolbar, so it will sometimes put
    the strip over something that matters. This is the correction, and the
    same three constraints as the takeover apply:

    * **No global mouse hook.** The pointer and the button are polled, and
      only one specific modifier combination is watched. Nothing about what
      you click anywhere else is read, or readable.
    * **No focus, ever.** The strip catches the click without ever becoming
      the window you are typing into.
    * **Clicks belong to the app behind.** Click-through is lifted only while
      the chord is held *and* the pointer is over the strip, and goes back the
      instant either stops being true.

    Double-click with the chord held to forget a dragged position and go back
    to placing itself -- the way out of a corner you dragged it into.

    Every input is injected so the whole gesture can be driven by a test
    rather than by a hand.
    """

    #: Two presses closer together than this are a double-click.
    DOUBLE_CLICK = 0.4

    def __init__(self, window, chord: str = "", clock=time.monotonic,
                 held=None, cursor=None, button=None) -> None:
        from .keys import parse_modifiers

        self.window = window
        self.chord = chord
        self.codes = parse_modifiers(chord)
        self.clock = clock
        self.dragging = False
        #: Chord held with the pointer over the strip: it will catch a click.
        self.armed = False
        self._held = held or self._keys_held
        self._cursor = cursor or self._cursor_pos
        self._button = button or self._button_down
        self._grab = (0, 0)
        self._was_down = False
        self._last_press = -1e9

    # -- the real input sources, replaced wholesale in tests --------------

    def _keys_held(self) -> bool:
        try:
            native = overlay.native()
            return bool(native is not None and native.keys_held(self.codes))
        except Exception:
            return False

    def _cursor_pos(self) -> tuple[int, int]:
        try:
            native = overlay.native()
            return native.cursor_pos() if native is not None else (0, 0)
        except Exception:
            return (0, 0)

    def _button_down(self) -> bool:
        try:
            native = overlay.native()
            return bool(native is not None and native.primary_button_down())
        except Exception:
            return False

    # -- the gesture ------------------------------------------------------

    def update(self) -> None:
        """One frame of it. Call while the strip is on screen."""
        if not self.codes:
            self.release()
            return

        rect = self.window.rect()
        if rect is None:
            self.release()
            return

        x, y = self._cursor()
        over = rect.left <= x < rect.right and rect.top <= y < rect.bottom
        # Staying armed mid-drag matters: the pointer routinely runs ahead of
        # a window that is being dragged, and leaving the rectangle must not
        # drop what you are holding.
        armed = self._held() and (over or self.dragging)
        if armed != self.armed:
            self.armed = armed
            self.window.set_click_through(not armed)

        down = self._button()
        pressed = down and not self._was_down
        self._was_down = down

        if pressed and armed:
            now = self.clock()
            if now - self._last_press <= self.DOUBLE_CLICK:
                self.dragging = False
                self.window.clear_placement()
            else:
                self.dragging = True
                self._grab = (x - rect.left, y - rect.top)
            self._last_press = now
        elif self.dragging and not down:
            self.dragging = False
            self.window.remember_placement()

        if self.dragging:
            self.window.move_to(x - self._grab[0], y - self._grab[1])

    def release(self) -> None:
        """Drop everything: click-through back on, a drag in progress kept.

        Called when the strip goes off screen as well as when the chord is
        let go, because a hidden window that still eats clicks is a window
        that eats clicks for no reason at all.
        """
        if self.dragging:
            self.dragging = False
            self.window.remember_placement()
        if self.armed:
            self.armed = False
            self.window.set_click_through(True)

    def caption(self) -> str:
        if self.dragging:
            return "moving -- double-click to reset"
        return "drag to move" if self.armed else ""


class Takeover:
    """Watches for the chord, and flips the overlay in and out of input mode.

    With no platform backend, or on a window that already has focus
    (``brainrot demo``), this does nothing and :meth:`focused` simply reports
    the truth.
    """

    def __init__(self, window, chord: str = "") -> None:
        from .keys import parse_chord

        self.window = window
        self.chord = chord
        self.codes = parse_chord(chord)
        self.active = False
        self._was_down = False
        self._previous_foreground = 0

    # -- chord detection --------------------------------------------------

    def _chord_down(self) -> bool:
        """Are all of the chord's keys held right now?

        Only ever true on a backend that polls (Windows). Where the chord is
        grabbed by the compositor instead, the request arrives through
        :meth:`update` as a state rather than as a key state.
        """
        if not self.codes:
            return False
        try:
            native = overlay.native()
            return bool(native is not None and native.poll_chord(self.codes))
        except Exception:
            return False

    def update(self) -> None:
        """Toggle on the press edge, so holding the chord does not flap."""
        try:
            native = overlay.native()
            wanted = native.takeover_state() if native is not None else None
        except Exception:
            wanted = None
        if wanted is not None and wanted != self.active:
            # Asked for by name rather than toggled: the compositor owns the
            # state on that path, and a toggle would drift out of step with it
            # the first time a request was missed.
            self.toggle()

        down = self._chord_down()
        if down and not self._was_down:
            self.toggle()
        self._was_down = down

    def toggle(self) -> None:
        self.active = not self.active
        if self.active:
            self._grab()
        else:
            self._release()

    # -- style switching --------------------------------------------------

    def _window_handle(self) -> int:
        return int(getattr(self.window, "_win", 0) or 0)

    def _grab(self) -> None:
        native = overlay.native()
        if native is None or not self._window_handle():
            self.active = False
            return
        try:
            self._previous_foreground = native.foreground_host()
            native.focus_window(self._window_handle(), True)
        except Exception:
            self.active = False

    def _release(self) -> None:
        """Give the keyboard back.

        Two halves, and only one of them is ours everywhere: dropping our own
        claim on the keyboard is, and putting focus somewhere sensible
        afterwards is not. On Windows we can hand it straight back to the
        window it came from. On GNOME the extension does that, because it
        raised the chord in the first place and a Wayland client may not
        activate somebody else's window.
        """
        native = overlay.native()
        if native is None or not self._window_handle():
            return
        try:
            native.focus_window(self._window_handle(), False)
            restore = getattr(native, "set_foreground", None)
            if restore is not None and self._previous_foreground:
                restore(self._previous_foreground)
        except Exception:
            pass

    # -- state ------------------------------------------------------------

    def focused(self) -> bool:
        """Whether key presses may legitimately be read this frame.

        An ordinary window -- ``brainrot demo`` -- just needs focus, and the
        chord is irrelevant. The overlay needs the chord *and* focus, because
        without the chord it does not have focus to begin with.
        """
        ordinary = getattr(self.window, "accepts_input", True)
        if not ordinary and not self.active:
            return False
        try:
            return bool(rl.IsWindowFocused())
        except Exception:
            return ordinary

    def needs_chord(self) -> bool:
        return not getattr(self.window, "accepts_input", True)
