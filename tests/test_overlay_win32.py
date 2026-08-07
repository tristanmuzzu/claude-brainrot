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


def _make_host(name: str = "brainrot-test-host") -> int:
    hwnd = user32.CreateWindowExW(
        WS_EX_TOOLWINDOW, "STATIC", name, WS_POPUP,
        10, 10, 200, 120, None, None, None, None)
    if not hwnd:
        pytest.skip("could not create a test host window")
    return int(hwnd)


@pytest.fixture
def host(overlay_hwnd: int):
    """A real top-level window to play the part of the Claude Code host.

    Depends on ``overlay_hwnd`` purely for teardown order. Windows destroys a
    window's *owned* windows along with it, so destroying this host while the
    overlay is still attached destroys the one raylib window the whole test
    session shares -- which is how this fixture originally took out every test
    that ran after it.
    """
    hwnd = _make_host()
    yield hwnd
    win32.detach(overlay_hwnd)          # break ownership before the owner dies
    user32.DestroyWindow(hwnd)


@pytest.fixture
def hosts(overlay_hwnd: int):
    """Make as many stand-in host windows as a test needs."""
    made: list[int] = []

    def make(name: str = "brainrot-test-host") -> int:
        made.append(_make_host(name))
        return made[-1]

    yield make
    win32.detach(overlay_hwnd)          # never destroy an owner while it owns us
    for hwnd in made:
        if win32.is_window(hwnd):
            user32.DestroyWindow(hwnd)


@pytest.fixture
def window(overlay_hwnd: int):
    """An ``OverlayWindow`` driving the shared raylib window."""
    from brainrot.engine.window import OverlayWindow

    overlay = OverlayWindow()
    overlay._cfg = Config()
    yield overlay
    overlay.detach_host()


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
    win32.attach_to_host(overlay_hwnd, host)
    assert not win32.is_topmost(overlay_hwnd)


def test_an_unknown_host_does_not_mean_over_everything(overlay_hwnd: int) -> None:
    """The old fallback was backwards: between daemon start and the first
    prompt nothing has said where Claude Code is, and that is the moment the
    overlay used to spend floating above every window on the desktop.

    raylib creates the window with FLAG_WINDOW_TOPMOST, so this is measuring a
    bit that really is set beforehand.
    """
    win32._order_topmost(overlay_hwnd)
    assert win32.is_topmost(overlay_hwnd), "precondition: the flag starts set"
    win32.apply_overlay_styles(overlay_hwnd, Config())
    assert not win32.is_topmost(overlay_hwnd)


def test_topmost_mode_is_still_reachable(overlay_hwnd: int) -> None:
    """Always-on-top stays available for demos and recordings."""
    win32.apply_overlay_styles(overlay_hwnd, Config(attach="topmost"))
    assert win32.is_topmost(overlay_hwnd)
    win32.detach(overlay_hwnd, topmost=True)
    assert win32.is_topmost(overlay_hwnd)


def test_attaching_does_not_restack_the_host(overlay_hwnd: int, host: int) -> None:
    """Raising the user's terminal above whatever they put in front of it is
    not this program's business -- and the previous version did exactly that,
    immediately after asking for the opposite ordering.

    Measured with the overlay itself excluded from the ordering: attaching is
    *supposed* to move the overlay above the host, and counting that as the
    host moving would make this test assert the opposite of what it means.
    """
    win32.apply_overlay_styles(overlay_hwnd, Config())
    before = _z_index(host, ignore=overlay_hwnd)
    win32.attach_to_host(overlay_hwnd, host)
    after = _z_index(host, ignore=overlay_hwnd)
    assert before >= 0, "the host window is not in the top-level z-order"
    assert before == after, "attaching moved the host window in the z-order"


def test_attaching_does_not_need_the_topmost_flag(overlay_hwnd: int, host: int) -> None:
    """Ownership, not the topmost bit, is what puts the strip above the host.

    (Where the two end up relative to each other is deliberately *not*
    asserted: Windows applies the one-level-above-owner rule when the owner is
    activated, and a test cannot activate anything without stealing the
    foreground from whoever is running it.)
    """
    win32.apply_overlay_styles(overlay_hwnd, Config())
    win32.attach_to_host(overlay_hwnd, host)
    assert win32.owner_of(overlay_hwnd) == host
    assert not win32.is_topmost(overlay_hwnd)


def test_detach_gives_up_ownership_without_going_topmost(
        overlay_hwnd: int, host: int) -> None:
    """Detaching happens every time the overlay goes idle, which is the most
    ordinary thing it does. Coming back from idle floating above everything is
    how it ended up over a YouTube video."""
    win32.apply_overlay_styles(overlay_hwnd, Config())
    win32.attach_to_host(overlay_hwnd, host)
    win32.detach(overlay_hwnd)
    assert win32.owner_of(overlay_hwnd) == 0
    assert not win32.is_topmost(overlay_hwnd)


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


# ---------------------------------------------------------------------------
# Following the focus
#
# These cannot move the foreground window around: SetForegroundWindow is
# refused to a process that is not already the one being used, and a test suite
# that yanked focus off the person running it would be its own bug. So they
# feed a *real* window handle in as the foreground and let every other step --
# GA_ROOT resolution, IsWindow liveness, the handle round-trip -- run against
# the live API. One test below uses no override at all and pins that seam to
# what GetForegroundWindow actually reports.
# ---------------------------------------------------------------------------


def test_no_known_host_means_hidden(window) -> None:
    assert window.focus_allows(frozenset()) is False


def test_a_host_that_is_not_in_front_stays_hidden(window, hosts) -> None:
    """The complaint, reduced to one assertion."""
    claude, chrome = hosts("claude"), hosts("chrome")
    assert window.focus_allows({claude}, foreground=chrome) is False


def test_the_host_in_front_shows(window, hosts) -> None:
    claude = hosts("claude")
    assert window.focus_allows({claude}, foreground=claude) is True


def test_only_the_sessions_that_are_working_count(window, hosts) -> None:
    """Two Claude Code windows, one of them busy: the overlay belongs on the
    busy one's screen, and the daemon only ever passes the busy ones in."""
    busy, idle = hosts("busy"), hosts("idle")
    assert window.focus_allows({busy}, foreground=idle) is False
    assert window.focus_allows({busy, idle}, foreground=idle) is True


def test_the_live_foreground_window_is_what_is_actually_consulted(window) -> None:
    """No override: whatever is genuinely in front of this desktop right now."""
    front = win32.foreground_root()
    if not front:
        pytest.skip("no foreground window on this desktop")
    allowed = window.focus_allows({front})
    if win32.foreground_root() != front:
        pytest.skip("the foreground window changed mid-test")
    assert allowed is True
    assert window.focus_allows(frozenset()) is False


def test_the_overlay_being_in_front_is_not_the_user_leaving(window, hosts) -> None:
    """The trap. ``engine/input.py:_grab`` calls SetForegroundWindow on the
    overlay itself, so "hide unless the host is in front" hides the strip at
    the exact moment the user presses the chord to play with it.

    Written as the broader rule -- our own window in front is never evidence
    that the user left -- because that needs no coordination with whatever
    state the takeover happens to be in.
    """
    claude = hosts("claude")
    assert window.focus_allows({claude}, foreground=window._hwnd()) is True


def test_an_owned_overlay_is_still_its_own_root(overlay_hwnd: int, host: int) -> None:
    """The takeover check compares the foreground against the overlay's root,
    and that only distinguishes anything because GA_ROOT walks the parent
    chain and ownership is not parenthood. Worth measuring rather than
    believing: if ownership did move the root, the two cases above would be
    the same test."""
    win32.attach_to_host(overlay_hwnd, host)
    assert win32.owner_of(overlay_hwnd) == host
    assert win32.root_of(overlay_hwnd) == overlay_hwnd


def test_a_second_session_replaces_the_attachment(window, hosts) -> None:
    """Two sessions on one daemon is normal here. The old guard latched the
    overlay to the first host it ever saw."""
    first, second = hosts("first"), hosts("second")
    window.attach_host(first)
    assert win32.owner_of(window._hwnd()) == first
    window.attach_host(second)
    assert win32.owner_of(window._hwnd()) == second
    assert window._host_hwnd == second


def test_a_dead_host_is_forgotten_rather_than_latched(window, hosts) -> None:
    """The measured failure: an unowned, non-topmost window stranded on screen
    with ``_attached`` still True and a host handle that names nothing.
    """
    claude = hosts("claude")
    window.attach_host(claude)
    assert window._attached is True

    # Break the ownership before killing the owner -- Windows destroys owned
    # windows along with their owner and this overlay is the one raylib window
    # the whole test session shares. `_attached` is deliberately left True:
    # that drift between what the daemon believes and what Windows has
    # recorded is the thing being tested.
    win32.detach(window._hwnd())
    assert user32.DestroyWindow(claude)
    assert not win32.is_window(claude)

    assert window.focus_allows({claude}, foreground=claude) is False
    assert window._host_hwnd == 0, "kept a handle that names nothing"
    assert window._attached is False, "still believes it is attached"
    assert win32.owner_of(window._hwnd()) == 0
    assert not win32.is_topmost(window._hwnd()), "stranded above everything"


def test_reattaching_to_a_dead_host_forgets_it(window, hosts) -> None:
    """The idle path is where this bites: the daemon detaches when it goes
    idle, the terminal closes, and the next show tries to re-take a window
    that is gone. Failing to attach must not leave the overlay believing it
    still has a host."""
    claude = hosts("claude")
    window.attach_host(claude)
    window.detach_host()
    assert user32.DestroyWindow(claude)

    window.set_visible(True)            # what the daemon does on the way back up
    assert window._attached is False
    assert window._host_hwnd == 0
    assert window.focus_allows(frozenset()) is False


def _z_index(hwnd: int, ignore: int = 0) -> int:
    """Position of a window in the top-level z-order, or -1 if not found.

    ``ignore`` leaves one window out of the count, for comparing a window's
    place against everything *except* the overlay being moved around it.
    """
    GW_HWNDFIRST, GW_HWNDNEXT = 0, 2
    user32.GetWindow.restype = wintypes.HWND
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    cur = user32.GetWindow(user32.GetDesktopWindow(), 5)  # GW_CHILD
    cur = user32.GetWindow(cur, GW_HWNDFIRST) if cur else None
    index = 0
    while cur:
        if int(cur) == hwnd:
            return index
        if int(cur) != ignore:
            index += 1
        cur = user32.GetWindow(cur, GW_HWNDNEXT)
    return -1
