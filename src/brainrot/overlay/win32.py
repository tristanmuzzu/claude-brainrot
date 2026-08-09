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
SWP_NOZORDER = 0x0004

GA_ROOT = 2

SW_HIDE = 0
#: Show, but do not activate -- the only kind of showing an overlay may do.
SW_SHOWNA = 8

MONITOR_DEFAULTTOPRIMARY = 1
MONITOR_DEFAULTTONEAREST = 2


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]

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
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.MonitorFromWindow.restype = wintypes.HANDLE
user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.MonitorFromPoint.restype = wintypes.HANDLE
user32.MonitorFromPoint.argtypes = [POINT, wintypes.DWORD]
user32.GetMonitorInfoW.restype = wintypes.BOOL
user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]


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


def set_window_shown(hwnd: int, shown: bool) -> None:
    """Put the overlay on or off screen without ever activating it.

    raylib unhides through ``glfwShowWindow``, and GLFW's ``GLFW_FOCUS_ON_SHOW``
    defaults on -- so raylib's way of showing a window also asks Windows to
    make it the foreground window, and ``WS_EX_NOACTIVATE`` does not stop it.
    Measured on this machine: the strip appeared, and 70ms later
    ``GetGUIThreadInfo`` reported the *keyboard focus* on the overlay. Anyone
    mid-sentence in Claude Code lost the rest of it.

    It only reproduces when the host window belongs to another process, which
    is why a first attempt at this was talked out of existence by a test whose
    fake host was in-process. ``SW_SHOWNA`` is the same show with the
    activation left out.
    """
    user32.ShowWindow(hwnd, SW_SHOWNA if shown else SW_HIDE)


def set_click_through(hwnd: int, through: bool) -> None:
    """Whether the mouse falls through the overlay or lands on it.

    ``WS_EX_TRANSPARENT`` is the reason the strip is not in the way, so it
    goes back on the moment the drag gesture ends. ``WS_EX_NOACTIVATE`` is
    never touched: catching a click and *taking focus* are different things,
    and the overlay may do the first without ever doing the second.
    """
    ex = _get_long(hwnd, GWL_EXSTYLE)
    ex = (ex | WS_EX_TRANSPARENT) if through else (ex & ~WS_EX_TRANSPARENT)
    _set_long(hwnd, GWL_EXSTYLE, ex)


def is_click_through(hwnd: int) -> bool:
    return bool(_get_long(hwnd, GWL_EXSTYLE) & WS_EX_TRANSPARENT)


def cursor_pos() -> tuple[int, int]:
    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        return (0, 0)
    return int(point.x), int(point.y)


def keys_held(codes) -> bool:
    """Are all of these virtual keys down right now?

    Polled, like the takeover chord, and for the same reason: the overlay has
    no focus, so there is nothing to deliver a key press to. Reading one
    specific combination is not the same as reading what somebody typed.
    """
    if not codes:
        return False
    return all(user32.GetAsyncKeyState(code) & 0x8000 for code in codes)


#: VK_LBUTTON. Swapped by the OS when the buttons are swapped for a left-hander,
#: so this stays "the primary button" rather than "the left one".
VK_LBUTTON = 0x01


def primary_button_down() -> bool:
    return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)


def window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    """Screen rectangle of a window, or None if the handle is dead."""
    if not is_window(hwnd):
        return None
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)


def work_area(hwnd: int = 0) -> tuple[int, int, int, int] | None:
    """Usable desktop of the monitor a window is on -- taskbar excluded.

    The work area rather than the monitor because the taskbar is not a place
    the overlay may hide behind, and on a multi-monitor desk the monitor that
    matters is the one Claude Code is on, not the one raylib calls first.
    """
    monitor = (user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST) if hwnd
               else user32.MonitorFromPoint(POINT(0, 0), MONITOR_DEFAULTTOPRIMARY))
    if not monitor:
        return None
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return None
    work = info.rcWork
    return int(work.left), int(work.top), int(work.right), int(work.bottom)


def move_window(hwnd: int, x: int, y: int, width: int, height: int) -> None:
    """Reposition without activating, restacking, or disturbing the owner.

    Deliberately ``SetWindowPos`` and not raylib's ``SetWindowPosition``: this
    is called from whichever thread notices the host has moved, and GLFW's
    window calls post to the thread that owns the window and block until it
    pumps its queue.
    """
    user32.SetWindowPos(hwnd, HWND_TOP, x, y, width, height,
                        SWP_NOACTIVATE | SWP_NOZORDER | SWP_NOOWNERZORDER)


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


# ---------------------------------------------------------------------------
# The names :mod:`brainrot.overlay` asks every backend for.
#
# On Windows one API knows about every window, so most of these are the same
# call under a name that does not presume it. The Linux backend answers them
# from two different places and needs the distinction to be real; keeping the
# vocabulary identical is what lets the engine above stop caring.
# ---------------------------------------------------------------------------


def prepare() -> bool:
    """Nothing to choose: raylib's Windows backend is the only one."""
    return True


def own_window(raylib_handle: int = 0) -> int:
    """raylib hands out the real ``HWND`` on Windows, so this is a formality."""
    return int(raylib_handle)


def degraded() -> bool:
    """Whether anything is missing. Nothing ever is, here."""
    return False


#: Windows reports every coordinate in physical pixels already, and the
#: process is per-monitor DPI aware, so there is no conversion to do.
def scale() -> float:
    return 1.0


def focus_known() -> bool:
    """Always: ``GetForegroundWindow`` is never a guess."""
    return True


own_rect = window_rect
host_rect = window_rect
host_alive = is_window
foreground_host = foreground_root


def same_host(a: int, b: int) -> bool:
    return bool(a) and bool(b) and root_of(a) == root_of(b)


def is_own_window(front: int, own: int) -> bool:
    return bool(front) and bool(own) and root_of(front) == root_of(own)


def resolve_host(pids) -> int:
    """Windows sends a window handle, not an ancestry: nothing to resolve."""
    return 0


def focus_window(win: int, focused: bool) -> None:
    """Take or give back the keyboard, for the takeover chord only."""
    ex = _get_long(win, GWL_EXSTYLE)
    if focused:
        ex &= ~(WS_EX_TRANSPARENT | WS_EX_NOACTIVATE)
        _set_long(win, GWL_EXSTYLE, ex)
        user32.SetForegroundWindow(win)
    else:
        ex |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        _set_long(win, GWL_EXSTYLE, ex)


#: The chord is polled here -- ``GetAsyncKeyState`` can read one specific
#: combination without focus, which is the whole reason the takeover works on
#: Windows without a system-wide keyboard hook.
poll_chord = keys_held


def takeover_state() -> "bool | None":
    """No queued request: the chord is polled, so there is no news to collect."""
    return None


def set_foreground(win: int) -> None:
    user32.SetForegroundWindow(win)
