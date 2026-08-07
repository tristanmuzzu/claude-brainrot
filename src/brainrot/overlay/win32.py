"""Win32 window treatment, on ctypes so there is no dependency to install.

Three jobs:

1. :func:`apply_overlay_styles` -- the classic overlay quartet on the raylib
   window: click-through, never-activate, no alt-tab entry, and z-order.

2. **Owned-window attachment.** By default the overlay is NOT globally
   always-on-top. The hook shim discovers the window of the terminal or editor
   hosting Claude Code and sends its handle with each event; the daemon then
   makes the overlay an *owned window* of that host. Windows keeps an owned
   window exactly one z-level above its owner: raise the terminal and the
   overlay rides above it, focus anything else and that window covers both.
   Which is precisely "attached to Claude Code, not glued to your screen".

   ``attach = "topmost"`` in the config restores the old always-on-top mode;
   ``attach = "host"`` (default) uses ownership when a host handle arrives and
   stays out of the topmost band entirely until one does. It used to fall back
   to topmost, which is precisely backwards: before any host has announced
   itself the overlay knows nothing about where Claude Code is, and "show over
   everything" is the worst possible reading of "we do not know yet".

   **Ownership binds lifetimes, not just z-order.** ``DestroyWindow`` destroys
   a window's owned windows along with it, so while the overlay is owned by
   the terminal, closing that terminal destroys the overlay's window out from
   under the daemon. This is not hypothetical -- it took out the shared window
   mid-test-run the first time these paths ran on real Windows. The daemon
   therefore only stays owned while it is actually on screen and detaches when
   it goes idle (see :meth:`OverlayWindow.detach_host`), which reduces the
   exposure to the few seconds an answer is being drawn.

3. **Who is in front.** Ownership decides what covers what, not what is on
   screen -- a window that does not happen to overlap the strip leaves it in
   plain sight over whatever you switched to. :func:`foreground_root` answers
   the other question, and the daemon hides the overlay outright whenever the
   window in front is neither a Claude Code window that is currently working
   nor the overlay itself.

Every call here declares its argument and return types. Left to itself ctypes
passes Python integers as C ``int`` and reads returns as ``int`` -- which
truncates a 64-bit ``HWND`` to 32 bits. Window handles happen to stay inside
32 bits on current Windows, so the bug is silent rather than absent, and it
stops being silent on the day the OS stops being generous.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from ..config import Config

user32 = ctypes.windll.user32  # type: ignore[attr-defined]

GWL_EXSTYLE = -20
GWLP_HWNDPARENT = -8

WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
WS_EX_APPWINDOW = 0x00040000

HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_NOOWNERZORDER = 0x0200

GA_ROOT = 2

_set_long = user32.SetWindowLongPtrW
_get_long = user32.GetWindowLongPtrW
_set_long.restype = ctypes.c_longlong
_set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]
_get_long.restype = ctypes.c_longlong
_get_long.argtypes = [wintypes.HWND, ctypes.c_int]

user32.SetWindowPos.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.UINT,
]
user32.IsWindow.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.GetAncestor.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetForegroundWindow.argtypes = []


def apply_overlay_styles(hwnd: int, cfg: Config) -> None:
    """Make the raylib window a proper overlay. raylib's flags already gave us
    undecorated + unfocused + passthrough; this adds what it has no API for."""
    ex = _get_long(hwnd, GWL_EXSTYLE)
    ex |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
    ex &= ~WS_EX_APPWINDOW  # keep it off the taskbar
    _set_long(hwnd, GWL_EXSTYLE, ex)
    # raylib created the window with FLAG_WINDOW_TOPMOST, so this is a real
    # change and not a formality: in host mode we come straight back out of
    # the band and only ownership decides where the strip sits.
    if getattr(cfg, "attach", "host") == "topmost":
        _order_topmost(hwnd)
    else:
        _order_normal(hwnd)


def _order_topmost(hwnd: int) -> None:
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)


def _order_normal(hwnd: int) -> None:
    """Out of the topmost band, into ordinary z-order."""
    user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)


def attach_to_host(hwnd: int, host_hwnd: int) -> bool:
    """Own the overlay to the Claude Code host window.

    Returns False when the handle is stale (host window already gone), in
    which case the caller should keep its current mode.
    """
    if not host_hwnd or not user32.IsWindow(host_hwnd):
        return False
    root = user32.GetAncestor(host_hwnd, GA_ROOT)
    if root:
        host_hwnd = root
    if host_hwnd == hwnd:
        return False        # never own yourself: that is an unbreakable loop
    # Drop out of the topmost band first: owned windows follow their owner's
    # band, and a stale TOPMOST bit would defeat the whole point.
    user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    _set_long(hwnd, GWLP_HWNDPARENT, host_hwnd)
    # Ownership alone does not restack anything already on screen, so nudge
    # the overlay to the top of its band once.
    #
    # Only the overlay moves. The previous version also yanked the *host*
    # window in front of the overlay immediately afterwards, which both undid
    # the ordering it had just asked for and hoisted the user's terminal above
    # whatever they had deliberately put in front of it. Raising someone
    # else's window is not this program's business.
    user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                        | SWP_NOOWNERZORDER)
    return True


def detach(hwnd: int, topmost: bool = False) -> None:
    """Give up ownership.

    ``topmost`` is the old free-floating mode, and is only right when the
    config asked for it. Defaulting it on is how a daemon that had merely gone
    idle came back as a window floating above everything on the screen.
    """
    _set_long(hwnd, GWLP_HWNDPARENT, 0)
    if topmost:
        _order_topmost(hwnd)
    else:
        _order_normal(hwnd)


def owner_of(hwnd: int) -> int:
    """Current owner handle, or 0. Exists so the attachment is testable."""
    return int(_get_long(hwnd, GWLP_HWNDPARENT) or 0)


def is_topmost(hwnd: int) -> bool:
    return bool(_get_long(hwnd, GWL_EXSTYLE) & 0x00000008)  # WS_EX_TOPMOST


def foreground_window() -> int:
    """The window the user is working in right now. The hook shim calls this
    at event time: whatever is foreground when you submit a prompt to Claude
    Code *is* the Claude Code host window."""
    return int(user32.GetForegroundWindow() or 0)


def is_window(hwnd: int) -> bool:
    """Does this handle still name a live window?

    Handles are reused, so this is not proof the window is the *same* one --
    but a host that has been closed fails it, which is the case that used to
    strand the overlay attached to nothing.
    """
    return bool(hwnd) and bool(user32.IsWindow(hwnd))


def root_of(hwnd: int) -> int:
    """The top-level window a handle belongs to.

    ``GA_ROOT`` walks the *parent* chain, not the owner chain, so an overlay
    that is owned by the host still reports itself -- which is what makes the
    takeover case below distinguishable from the host case.
    """
    if not hwnd:
        return 0
    return int(user32.GetAncestor(hwnd, GA_ROOT) or hwnd)


def foreground_root() -> int:
    """Top-level window in front, or 0 if the desktop has no foreground."""
    return root_of(foreground_window())
