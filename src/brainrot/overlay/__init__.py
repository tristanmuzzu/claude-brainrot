"""Platform-specific window treatment for the overlay strip.

The engine's :mod:`brainrot.engine.window` owns the window itself; this
package holds the surgery raylib has no API for -- click-through, keeping the
strip off the window switcher, never letting it take focus, and putting it
above the Claude Code window rather than above everything you own.

One backend per platform, and they answer the same set of questions:

===========================  ==========================================
``prepare()``                before ``InitWindow``: choose the platform
``own_window(handle)``       our window, in whatever a handle means here
``apply_overlay_styles``     the overlay quartet, before it is ever shown
``set_window_shown``         show and hide without activating
``set_click_through``        let the mouse fall through, or catch it
``own_rect`` ``move_window`` where our window is, and where to put it
``set_opacity``              whole-window fade
``focus_window``             the takeover, and only the takeover
``attach_to_host``           ride above the Claude Code window
``host_rect`` ``work_area``  where to place ourselves, and within what
``foreground_host``          who is in front right now
``same_host`` ``is_own_window`` ``host_alive``  and is that one of ours
``cursor_pos`` ``keys_held`` ``primary_button_down``  the drag gesture
``scale()``                  device pixels per logical pixel
===========================  ==========================================

Everything is in *device* pixels at this boundary, on both platforms, so the
placement geometry above it never has to know which one it is on.

:func:`native` returns None when there is no backend -- a Mac, a Linux box
with no display, CI -- and every caller treats that as "an ordinary window",
which is what ``brainrot demo`` wants anyway.
"""

from __future__ import annotations

import os
import sys

_resolved = False
_backend = None


def native():
    """The backend for this platform, or None.

    Resolved once. Importing a backend is cheap but *opening a display* is
    not, and on Linux the answer can be "no display" -- which is a normal
    state (a headless test run) rather than a failure.
    """
    global _resolved, _backend
    if _resolved:
        return _backend
    _resolved = True
    _backend = _resolve()
    return _backend


def _resolve():
    if os.environ.get("BRAINROT_NO_NATIVE"):
        return None
    if os.name == "nt":
        try:
            from . import win32

            return win32
        except Exception:
            return None
    if sys.platform.startswith("linux"):
        try:
            from . import linux

            return linux if linux.available() else None
        except Exception:
            return None
    return None


def reset() -> None:
    """Forget the resolved backend. For tests, which change the environment."""
    global _resolved, _backend
    _resolved = False
    _backend = None
