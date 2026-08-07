"""Taking the wheel: hand control of a scene to whoever is at the keyboard.

The scenes drive themselves. This module lets a person interrupt that, and
hands it back when they stop.

The awkward part is that the overlay is built not to receive input. It carries
``WS_EX_TRANSPARENT | WS_EX_NOACTIVATE`` so clicks fall through to whatever is
behind it and it never takes focus -- which is the entire reason it is not
annoying, and also the reason it cannot see a key press. There are three ways
round that and only one of them is acceptable:

* Poll every key with ``GetAsyncKeyState``. Works without focus, and means
  arrow keys drive the runner *while you are typing into Claude Code*, where
  arrows move your cursor. No.
* Install a ``WH_KEYBOARD_LL`` hook. Works, and a background toy has no
  business installing a system-wide keyboard hook. No.
* Watch for one deliberate chord, and only on seeing it drop the overlay bits
  and take focus, at which point raylib reads the keyboard the ordinary way.
  Nothing is intercepted until it is asked for, and the polling is a single
  test of one specific combination rather than a read of everything typed.

The third one is what this does. Releasing control puts the styles back and
returns focus to the window it was taken from, so the overlay goes back to
being ignorable.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from . import rl

#: Seconds of no input before a scene resumes driving itself.
IDLE_HANDBACK = 8.0

#: Virtual-key codes for the takeover chord: Ctrl+Alt+B.
_VK_CONTROL, _VK_MENU, _VK_B = 0x11, 0x12, 0x42


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
        elif self.engaged and now - self.last_input > IDLE_HANDBACK:
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
# Windows: the deliberate takeover
# ---------------------------------------------------------------------------


class Takeover:
    """Watches for the chord, and flips the overlay in and out of input mode.

    Off Windows, or on a window that already has focus (``brainrot demo``),
    this does nothing and :meth:`focused` simply reports the truth.
    """

    CHORD = "Ctrl+Alt+B"

    def __init__(self, window) -> None:
        self.window = window
        self.active = False
        self._was_down = False
        self._previous_foreground = 0

    # -- chord detection --------------------------------------------------

    def _chord_down(self) -> bool:
        if os.name != "nt":
            return False
        try:
            import ctypes

            user32 = ctypes.windll.user32
            def down(vk: int) -> bool:
                return bool(user32.GetAsyncKeyState(vk) & 0x8000)

            return down(_VK_CONTROL) and down(_VK_MENU) and down(_VK_B)
        except Exception:
            return False

    def update(self) -> None:
        """Toggle on the press edge, so holding the chord does not flap."""
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

    def _grab(self) -> None:
        if os.name != "nt":
            return
        try:
            import ctypes
            from ..overlay import win32

            user32 = ctypes.windll.user32
            self._previous_foreground = win32.foreground_window()
            hwnd = self.window._hwnd()
            ex = win32._get_long(hwnd, win32.GWL_EXSTYLE)
            ex &= ~(win32.WS_EX_TRANSPARENT | win32.WS_EX_NOACTIVATE)
            win32._set_long(hwnd, win32.GWL_EXSTYLE, ex)
            user32.SetForegroundWindow(hwnd)
        except Exception:
            self.active = False

    def _release(self) -> None:
        if os.name != "nt":
            return
        try:
            import ctypes
            from ..overlay import win32

            user32 = ctypes.windll.user32
            hwnd = self.window._hwnd()
            ex = win32._get_long(hwnd, win32.GWL_EXSTYLE)
            ex |= win32.WS_EX_TRANSPARENT | win32.WS_EX_NOACTIVATE
            win32._set_long(hwnd, win32.GWL_EXSTYLE, ex)
            if self._previous_foreground:
                user32.SetForegroundWindow(self._previous_foreground)
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
