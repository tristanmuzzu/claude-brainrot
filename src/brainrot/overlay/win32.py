"""Win32 window treatment, on ctypes so there is no dependency to install.

Two jobs:

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
   falls back to topmost until one does.
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

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

_set_long = user32.SetWindowLongPtrW
_get_long = user32.GetWindowLongPtrW
_set_long.restype = ctypes.c_longlong
_set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]
_get_long.restype = ctypes.c_longlong
_get_long.argtypes = [wintypes.HWND, ctypes.c_int]


def apply_overlay_styles(hwnd: int, cfg: Config) -> None:
    """Make the raylib window a proper overlay. raylib's flags already gave us
    undecorated + unfocused + passthrough; this adds what it has no API for."""
    ex = _get_long(hwnd, GWL_EXSTYLE)
    ex |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
    ex &= ~WS_EX_APPWINDOW  # keep it off the taskbar
    _set_long(hwnd, GWL_EXSTYLE, ex)

    if cfg.attach == "topmost":
        _order_topmost(hwnd)
    # attach == "host": stay topmost until a host window announces itself,
    # then attach_to_host() reparents us.
    else:
        _order_topmost(hwnd)


def _order_topmost(hwnd: int) -> None:
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)


def attach_to_host(hwnd: int, host_hwnd: int) -> bool:
    """Own the overlay to the Claude Code host window.

    Returns False when the handle is stale (host window already gone), in
    which case the caller should keep its current mode.
    """
    if not host_hwnd or not user32.IsWindow(host_hwnd):
        return False
    root = user32.GetAncestor(host_hwnd, 2)  # GA_ROOT
    if root:
        host_hwnd = root
    # Drop out of the topmost band first: owned windows follow their owner's
    # band, and a stale TOPMOST bit would defeat the whole point.
    user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    _set_long(hwnd, GWLP_HWNDPARENT, host_hwnd)
    # Nudge the z-order so ownership takes effect immediately.
    user32.SetWindowPos(hwnd, host_hwnd, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    user32.SetWindowPos(host_hwnd, hwnd, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    return True


def detach(hwnd: int) -> None:
    """Back to free-floating topmost (config attach = "topmost", or host gone)."""
    _set_long(hwnd, GWLP_HWNDPARENT, 0)
    _order_topmost(hwnd)


def foreground_window() -> int:
    """The window the user is working in right now. The hook shim calls this
    at event time: whatever is foreground when you submit a prompt to Claude
    Code *is* the Claude Code host window."""
    return int(user32.GetForegroundWindow())
