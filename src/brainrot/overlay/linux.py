"""The Linux overlay backend: X11 for our own window, gnome-shell for the rest.

:mod:`brainrot.overlay.win32` gets to answer every question from one API,
because on Windows one API knows everything. Here the two halves come from
different places and this module is the seam:

* **our own window** -- click-through, never focused, off the switcher, moved
  to the pixel -- is X11 surgery on an XWayland window
  (:mod:`brainrot.overlay.x11`);
* **everybody else's windows** -- who is in front, where the Claude Code
  window is, where the pointer is -- comes from a gnome-shell extension
  (:mod:`brainrot.overlay.shell`), because Wayland refuses all three to a
  client and refuses them by design rather than by omission.

The two speak different coordinate systems and that is the one thing worth
being careful about: the compositor counts in logical pixels, X11 counts in
device pixels, and on a HiDPI display those differ by a factor of two. Every
number that crosses this module is converted, once, here.

**Without the extension it still works**, which is deliberate: an overlay you
have to install a shell extension to see at all would be a bad trade for
someone who just wants to try it. What you lose is precisely the three things
above -- the strip docks to the work area instead of standing beside the
Claude Code window, and it stays up for the whole turn instead of only while
you are looking at Claude Code. :func:`degraded` is what ``brainrot doctor``
reports on.

There is one thing Windows can do that this cannot: an *owned* window, which
rides exactly one z-level above the window it belongs to. mutter has no notion
of an X11 window owned by a Wayland one, so the strip lives in the always-above
band and ``follow_focus`` -- not the z-order -- is what keeps it off your other
applications.
"""

from __future__ import annotations

import os

from ..config import Config
from . import shell, x11


#: The styles that stop this window taking the keyboard have to be applied
#: before it is ever mapped, so it is created hidden and shown deliberately.
CREATE_HIDDEN = True


def available() -> bool:
    return x11.available()


def offer_datagram(payload: bytes) -> bool:
    """Take a datagram if it came from the shell extension rather than a hook."""
    return shell.bridge().offer(payload)


def prepare() -> bool:
    """Runs before ``InitWindow``: put GLFW on X11 rather than Wayland."""
    return x11.prepare()


def degraded() -> bool:
    """True when the shell extension is not talking to us."""
    return not shell.bridge().live()


# ---------------------------------------------------------------------------
# Our own window
# ---------------------------------------------------------------------------


def own_window(raylib_handle: int = 0) -> int:
    """Our X11 window id.

    ``raylib_handle`` is the ``GLFWwindow *`` and is deliberately unused: the
    X11 window behind it is not reachable through the cffi module's symbol
    table. See :func:`brainrot.overlay.x11.own_window`.
    """
    return x11.own_window()


def apply_overlay_styles(win: int, cfg: Config) -> None:
    x11.apply_overlay_styles(win, cfg)


def set_window_shown(win: int, shown: bool) -> None:
    x11.set_window_shown(win, shown)


def set_click_through(win: int, through: bool) -> None:
    x11.set_click_through(win, through)


def is_click_through(win: int) -> bool:
    return x11.is_click_through(win)


def move_window(win: int, x: int, y: int, width: int, height: int) -> None:
    x11.move_window(win, x, y, width, height)


def own_rect(win: int) -> "tuple[int, int, int, int] | None":
    return x11.window_rect(win)


def focus_window(win: int, focused: bool) -> None:
    x11.focus_window(win, focused)


# ---------------------------------------------------------------------------
# The Claude Code host window
# ---------------------------------------------------------------------------


def attach_to_host(win: int, host: int) -> bool:
    """Remember the host. There is no ownership relation to establish.

    Returns whether the host is a window the compositor still reports, which
    is what the caller uses to decide whether the handle is worth keeping.
    """
    return host_alive(host)


def detach(win: int, topmost: bool = False) -> None:
    """Nothing to give back.

    The strip stays in the always-above band for its whole life, because it is
    *unmapped* when idle rather than merely deprioritised -- and because
    removing and re-adding the state every idle spell is a restack per turn
    for no gain. The Windows version has to detach for a reason that does not
    exist here: an owned window is destroyed along with its owner.
    """


def owner_of(win: int) -> int:
    return 0


def is_topmost(win: int) -> bool:
    return True


def host_alive(host: int) -> bool:
    """Is this still a window? Unknown when the extension is not running."""
    snap = shell.bridge().snapshot
    if not shell.bridge().live():
        # Without the extension we cannot tell a closed window from a window
        # we simply cannot see. Saying "gone" would make the daemon forget the
        # host on every frame; saying "alive" costs nothing, because nothing
        # downstream can act on it either.
        return bool(host)
    return snap.window(host) is not None


def host_rect(host: int) -> "tuple[int, int, int, int] | None":
    """The Claude Code window, in X11 device pixels."""
    snap = shell.bridge().snapshot
    if not shell.bridge().live():
        return None
    win = snap.window(host)
    if win is None:
        return None
    ratio = scale()
    x, y, w, h = win.rect
    return (round(x * ratio), round(y * ratio),
            round((x + w) * ratio), round((y + h) * ratio))


def work_area(host: int = 0) -> "tuple[int, int, int, int] | None":
    """Usable desktop of the monitor the host window is on, in device pixels.

    From the compositor when it is talking, because that is the only source
    that knows which monitor the Claude Code window is on. ``_NET_WORKAREA``
    is the fallback, and it describes the primary monitor only.
    """
    snap = shell.bridge().snapshot
    if shell.bridge().live():
        monitor = snap.monitor_for(host)
        if monitor is not None:
            ratio = scale()
            x, y, w, h = monitor.work
            return (round(x * ratio), round(y * ratio),
                    round((x + w) * ratio), round((y + h) * ratio))
    area = x11.work_area()
    if area is not None:
        return area
    left, top, right, bottom = x11.screen_rect()
    return (left, top, right, bottom) if right and bottom else None


def focus_known() -> bool:
    """Can we answer "who is in front" at all?

    No, when the shell extension is not installed or not running -- and that
    is a supported way to run this, so the answer has to be *distinguishable*
    from "nobody is in front". A caller that cannot tell the two apart either
    hides the overlay forever (if it reads silence as "not Claude Code") or
    shows it over everything (if it reads silence as "close enough"); the
    first is what happened, and it looks exactly like a dead daemon.
    """
    return shell.bridge().live()


def foreground_host() -> int:
    """The window in front, as the compositor sees it.

    Zero means "nothing known". Check :func:`focus_known` first: within a
    live snapshot, zero genuinely means no window is focused, and the overlay
    should be hidden.
    """
    if not shell.bridge().live():
        return 0
    return shell.bridge().snapshot.focus


def same_host(a: int, b: int) -> bool:
    return bool(a) and a == b


def is_own_window(front: int, own: int = 0) -> bool:
    """Is the window in front our own strip?

    Our window being in front is never evidence that the user has left: the
    takeover chord puts it there deliberately. ``own`` -- our X11 window --
    cannot be compared against a compositor window id at all, they are
    different namespaces, so this is a process-id comparison instead.
    """
    if not front or not shell.bridge().live():
        return False
    win = shell.bridge().snapshot.window(front)
    return win is not None and win.pid == os.getpid()


def resolve_host(pids) -> int:
    """The window id for a hook's process ancestry. 0 when unknown."""
    if not shell.bridge().live():
        return 0
    return shell.bridge().snapshot.host_for(pids)


def scale() -> float:
    """Device pixels per logical pixel, measured against the X screen."""
    return shell.bridge().snapshot.scale_against(x11.screen_rect()[2])


# ---------------------------------------------------------------------------
# Pointer and keys
# ---------------------------------------------------------------------------


def cursor_pos() -> tuple[int, int]:
    """Pointer position in device pixels.

    ``XQueryPointer`` is not usable here: whenever the pointer is over a
    Wayland surface -- which is most of the desktop -- it returns the last
    position X saw, which is both wrong and plausible. Measured on this
    machine: y = 1564 on a screen 1728 tall with the pointer at the top.
    """
    if not shell.bridge().live():
        return (0, 0)
    x, y, _mods = shell.bridge().snapshot.pointer
    ratio = scale()
    return (round(x * ratio), round(y * ratio))


def keys_held(codes) -> bool:
    """Are all of these modifiers held right now?

    Only modifiers, and only the ones a chord can name. The compositor sends a
    mask of exactly those bits and nothing else about the keyboard, so this
    cannot become a way of reading what somebody typed even by accident.
    """
    if not codes or not shell.bridge().live():
        return False
    wanted = shell.mods_from_vk(codes)
    if not wanted:
        return False
    return (shell.bridge().snapshot.pointer[2] & wanted) == wanted


def primary_button_down() -> bool:
    if not shell.bridge().live():
        return False
    return bool(shell.bridge().snapshot.pointer[2] & shell.CLUTTER_BUTTON1)


def poll_chord(codes) -> bool:
    """No: the takeover chord contains an ordinary key, and this backend can
    only see modifiers. :func:`takeover_state` is how it arrives instead."""
    return False


def takeover_state() -> "bool | None":
    """Whether the extension's chord has asked for the keyboard. None = no news.

    Registered inside gnome-shell rather than polled, which is the opposite
    trade from Windows and a better one: nothing typed anywhere else is ever
    read, and the chord genuinely belongs to us instead of firing alongside
    whatever else wanted it. The extension owns the on/off state because it
    also owns putting focus *back* where it was -- a Wayland client cannot
    activate another window, and the compositor can.
    """
    return shell.bridge().claim_takeover()
