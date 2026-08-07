"""The Windows overlay treatment, exercised against the real Win32 API.

This module was written blind against documentation, on a machine with no
Windows to try it on, and it showed: the attach path asked for two
contradictory z-orders in a row and passed 64-bit handles through ctypes'
default 32-bit marshalling. None of that fails loudly -- it produces an
overlay that sits in the wrong place -- so the checks here are about the
observable state Windows reports back, not about whether the calls returned.

Skipped anywhere that is not Windows.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Win32 only")

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    from conftest import ensure_window

    from brainrot.config import Config
    from brainrot.engine import rl
    from brainrot.overlay import win32

    user32 = ctypes.windll.user32
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
    ]
    user32.DestroyWindow.restype = wintypes.BOOL
    user32.DestroyWindow.argtypes = [wintypes.HWND]

WS_POPUP = 0x80000000
WS_EX_TOOLWINDOW = 0x00000080


@pytest.fixture
def overlay_hwnd():
    ensure_window()
    handle = int(rl.ffi.cast("intptr_t", rl.GetWindowHandle()))
    if not handle:
        pytest.skip("no native window handle from raylib")
    yield handle
    # Leave the shared window as we found it: unowned and out of the band.
    win32.detach(handle)
    win32._set_long(handle, win32.GWLP_HWNDPARENT, 0)


@pytest.fixture
def host(overlay_hwnd: int):
    """A real top-level window to play the part of the Claude Code host.

    Depends on ``overlay_hwnd`` purely for teardown order. Windows destroys a
    window's *owned* windows along with it, so destroying this host while the
    overlay is still attached destroys the one raylib window the whole test
    session shares -- which is how this fixture originally took out every test
    that ran after it.
    """
    hwnd = user32.CreateWindowExW(
        WS_EX_TOOLWINDOW, "STATIC", "brainrot-test-host", WS_POPUP,
        10, 10, 200, 120, None, None, None, None)
    if not hwnd:
        pytest.skip("could not create a test host window")
    yield int(hwnd)
    win32.detach(overlay_hwnd)          # break ownership before the owner dies
    user32.DestroyWindow(hwnd)


def test_overlay_styles_are_actually_set(overlay_hwnd: int) -> None:
    win32.apply_overlay_styles(overlay_hwnd, Config())
    ex = win32._get_long(overlay_hwnd, win32.GWL_EXSTYLE)
    assert ex & win32.WS_EX_TRANSPARENT, "clicks would not pass through"
    assert ex & win32.WS_EX_NOACTIVATE, "the overlay could steal focus"
    assert ex & win32.WS_EX_TOOLWINDOW, "it would appear in alt-tab"
    assert not ex & win32.WS_EX_APPWINDOW, "it would appear on the taskbar"


def test_attaching_makes_the_overlay_owned_by_the_host(
        overlay_hwnd: int, host: int) -> None:
    """Ownership is the whole mechanism: Windows keeps an owned window exactly
    one level above its owner, which is what "attached to Claude Code" means.
    """
    win32.apply_overlay_styles(overlay_hwnd, Config())
    assert win32.attach_to_host(overlay_hwnd, host) is True
    assert win32.owner_of(overlay_hwnd) == host


def test_attaching_leaves_the_topmost_band(overlay_hwnd: int, host: int) -> None:
    """An overlay still flagged topmost floats over everything regardless of
    its owner, which defeats the point of attaching it to anything."""
    win32.apply_overlay_styles(overlay_hwnd, Config())
    assert win32.is_topmost(overlay_hwnd), "should start topmost as a fallback"
    win32.attach_to_host(overlay_hwnd, host)
    assert not win32.is_topmost(overlay_hwnd)


def test_attaching_does_not_restack_the_host(overlay_hwnd: int, host: int) -> None:
    """Raising the user's terminal above whatever they put in front of it is
    not this program's business -- and the previous version did exactly that,
    immediately after asking for the opposite ordering."""
    win32.apply_overlay_styles(overlay_hwnd, Config())
    before = _z_index(host)
    win32.attach_to_host(overlay_hwnd, host)
    after = _z_index(host)
    assert before == after, "attaching moved the host window in the z-order"


def test_detach_restores_free_floating_topmost(
        overlay_hwnd: int, host: int) -> None:
    win32.apply_overlay_styles(overlay_hwnd, Config())
    win32.attach_to_host(overlay_hwnd, host)
    win32.detach(overlay_hwnd)
    assert win32.owner_of(overlay_hwnd) == 0
    assert win32.is_topmost(overlay_hwnd)


def test_a_dead_host_handle_is_refused(overlay_hwnd: int) -> None:
    """A stale handle must leave the current mode alone, not own the overlay
    to a window that no longer exists."""
    assert win32.attach_to_host(overlay_hwnd, 0) is False
    assert win32.attach_to_host(overlay_hwnd, 0xDEADBEEF) is False


def test_the_overlay_refuses_to_own_itself(overlay_hwnd: int) -> None:
    assert win32.attach_to_host(overlay_hwnd, overlay_hwnd) is False


def test_handles_survive_the_ctypes_round_trip(overlay_hwnd: int, host: int) -> None:
    """Declared argtypes are what stop a 64-bit HWND being cut to 32 bits."""
    assert win32.attach_to_host(overlay_hwnd, host) is True
    assert win32.owner_of(overlay_hwnd) == host


def test_owned_only_while_visible(host: int) -> None:
    """The daemon lets go of the host whenever it has nothing to show.

    Ownership couples lifetimes: while attached, closing the terminal destroys
    the overlay's window too. Holding the attachment only for the seconds a
    scene is on screen keeps that window of exposure small.
    """
    from brainrot.engine.window import OverlayWindow

    window = OverlayWindow()
    window._cfg = Config()
    window.attach_host(host)
    assert window._attached is True
    assert win32.owner_of(window._hwnd()) == host

    window.detach_host()
    assert window._attached is False
    assert win32.owner_of(window._hwnd()) == 0

    window.set_visible(True)            # coming back on screen re-takes it
    assert window._attached is True
    assert win32.owner_of(window._hwnd()) == host
    window.detach_host()


def _z_index(hwnd: int) -> int:
    """Position of a window in the top-level z-order, or -1 if not found."""
    GW_HWNDFIRST, GW_HWNDNEXT = 0, 2
    user32.GetWindow.restype = wintypes.HWND
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    cur = user32.GetWindow(user32.GetDesktopWindow(), 5)  # GW_CHILD
    cur = user32.GetWindow(cur, GW_HWNDFIRST) if cur else None
    index = 0
    while cur:
        if int(cur) == hwnd:
            return index
        cur = user32.GetWindow(cur, GW_HWNDNEXT)
        index += 1
    return -1
