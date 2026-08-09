"""X11 window treatment, on ctypes so there is no dependency to install.

The Linux counterpart of :mod:`brainrot.overlay.win32`, and it answers the
same questions: how does a window become click-through, stay off alt-tab,
never take focus, and sit above the window running Claude Code.

**Why X11 at all on a Wayland desktop.** GNOME 49 dropped the X11 session, so
Ubuntu 25.10 and later are Wayland-only -- but that is the *session*, not the
only window protocol on it. A Wayland client is forbidden from knowing where
it is, moving itself, raising itself or shaping its input region; every single
thing an overlay is made of. XWayland clients are not: mutter runs a real
X11 window manager for them and honours the EWMH hints below. So the daemon
asks GLFW for the X11 backend (:func:`prepare`, before ``InitWindow``) and
does its window surgery in X11, on a desktop that is otherwise Wayland.

Measured on Ubuntu 26.04 / GNOME Shell 50.1, all of it against the live
compositor: position honoured to the pixel, ``_NET_WM_STATE_ABOVE`` puts the
strip above native Wayland windows as well as X11 ones, an empty input shape
makes clicks fall through, and mapping a window whose ``WM_HINTS`` say it
takes no input does not move the keyboard.

Two things X11 *cannot* answer here, and they are why
:mod:`brainrot.overlay.shell` exists:

* **Who is in front.** ``_NET_ACTIVE_WINDOW`` names only X11 windows. Claude
  Code's host -- a terminal, or the desktop app -- is usually a Wayland
  client, and to XWayland it does not exist.
* **Where the pointer is.** ``XQueryPointer`` returns a stale position
  whenever the pointer is over a Wayland surface (measured: y = 1564 on a
  1728-tall screen with the pointer nowhere near it).

Both come from a gnome-shell extension instead, which is inside the
compositor and therefore simply knows.
"""

from __future__ import annotations

import ctypes
import os
from ctypes.util import find_library

from ..config import Config

#: X11 request/response constants worth naming.
CLIENT_MESSAGE = 33
PROP_MODE_REPLACE = 0
INPUT_HINT = 1 << 0

SUBSTRUCTURE_NOTIFY_MASK = 1 << 19
SUBSTRUCTURE_REDIRECT_MASK = 1 << 20

#: XShape: which of a window's two regions, and what to do to it.
SHAPE_BOUNDING, SHAPE_CLIP, SHAPE_INPUT = 0, 1, 2
SHAPE_SET = 0

#: _NET_WM_STATE actions.
NET_WM_STATE_REMOVE, NET_WM_STATE_ADD = 0, 1

#: Property types we write, by their well-known atom numbers. These four are
#: fixed by the X protocol itself rather than interned at runtime.
XA_ATOM, XA_CARDINAL, XA_WINDOW = 4, 6, 33

Window = ctypes.c_ulong
Atom = ctypes.c_ulong


class XWMHints(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_long),
        ("input", ctypes.c_int),
        ("initial_state", ctypes.c_int),
        ("icon_pixmap", ctypes.c_ulong),
        ("icon_window", Window),
        ("icon_x", ctypes.c_int),
        ("icon_y", ctypes.c_int),
        ("icon_mask", ctypes.c_ulong),
        ("window_group", ctypes.c_ulong),
    ]


class XClientMessageEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", Window),
        ("message_type", Atom),
        ("format", ctypes.c_int),
        ("data", ctypes.c_long * 5),
    ]


class XEvent(ctypes.Union):
    #: An XEvent is a union whose largest member is 24 longs. Sending a
    #: ClientMessage through a short buffer is how you get memory corruption
    #: that only shows up under someone else's window manager.
    _fields_ = [("type", ctypes.c_int), ("xclient", XClientMessageEvent),
                ("pad", ctypes.c_long * 24)]


class XWindowAttributes(ctypes.Structure):
    #: Only ``map_state`` is read, but the whole layout has to be declared:
    #: ctypes reads the field at its offset, and a short struct reads the
    #: wrong one -- and X will happily write past it.
    _fields_ = [
        ("x", ctypes.c_int), ("y", ctypes.c_int),
        ("width", ctypes.c_int), ("height", ctypes.c_int),
        ("border_width", ctypes.c_int), ("depth", ctypes.c_int),
        ("visual", ctypes.c_void_p), ("root", Window),
        ("window_class", ctypes.c_int), ("bit_gravity", ctypes.c_int),
        ("win_gravity", ctypes.c_int), ("backing_store", ctypes.c_int),
        ("backing_planes", ctypes.c_ulong), ("backing_pixel", ctypes.c_ulong),
        ("save_under", ctypes.c_int), ("colormap", ctypes.c_ulong),
        ("map_installed", ctypes.c_int), ("map_state", ctypes.c_int),
        ("all_event_masks", ctypes.c_long), ("your_event_mask", ctypes.c_long),
        ("do_not_propagate_mask", ctypes.c_long),
        ("override_redirect", ctypes.c_int), ("screen", ctypes.c_void_p),
    ]


#: XWindowAttributes.map_state
IS_UNMAPPED, IS_UNVIEWABLE, IS_VIEWABLE = 0, 1, 2


class XRectangle(ctypes.Structure):
    _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short),
                ("width", ctypes.c_ushort), ("height", ctypes.c_ushort)]


class _Lib:
    """The X connection, opened once and kept.

    Deliberately a lazily-built singleton rather than module-level ctypes
    calls: importing this module must be free and must not fail on a machine
    with no display, because :mod:`brainrot.doctor` imports it precisely to
    report that there is no display.
    """

    def __init__(self) -> None:
        self.x11 = ctypes.CDLL(find_library("X11") or "libX11.so.6")
        self.xext = ctypes.CDLL(find_library("Xext") or "libXext.so.6")
        self._declare()
        self.display = ctypes.c_void_p(self.x11.XOpenDisplay(None))
        if not self.display.value:
            raise OSError("cannot open X display")
        self.root = self.x11.XDefaultRootWindow(self.display)
        self._atoms: dict[str, int] = {}

    def _declare(self) -> None:
        """Every call gets argument and return types.

        Left to itself ctypes passes Python integers as C ``int`` and reads
        returns as ``int``, which truncates a 64-bit ``Display *`` to 32 bits
        and hands X a pointer into nowhere.
        """
        x11, xext = self.x11, self.xext
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        x11.XDefaultRootWindow.restype = Window
        x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x11.XInternAtom.restype = Atom
        x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        x11.XFlush.argtypes = [ctypes.c_void_p]
        x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x11.XFree.argtypes = [ctypes.c_void_p]
        x11.XGetWindowProperty.restype = ctypes.c_int
        x11.XGetWindowProperty.argtypes = [
            ctypes.c_void_p, Window, Atom, ctypes.c_long, ctypes.c_long, ctypes.c_int,
            Atom, ctypes.POINTER(Atom), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))]
        x11.XChangeProperty.argtypes = [
            ctypes.c_void_p, Window, Atom, Atom, ctypes.c_int, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_int]
        x11.XDeleteProperty.argtypes = [ctypes.c_void_p, Window, Atom]
        x11.XSendEvent.argtypes = [ctypes.c_void_p, Window, ctypes.c_int,
                                   ctypes.c_long, ctypes.POINTER(XEvent)]
        x11.XMoveResizeWindow.argtypes = [ctypes.c_void_p, Window, ctypes.c_int,
                                          ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
        x11.XMapWindow.argtypes = [ctypes.c_void_p, Window]
        x11.XUnmapWindow.argtypes = [ctypes.c_void_p, Window]
        x11.XRaiseWindow.argtypes = [ctypes.c_void_p, Window]
        x11.XSetWMHints.argtypes = [ctypes.c_void_p, Window, ctypes.POINTER(XWMHints)]
        x11.XGetWMHints.restype = ctypes.POINTER(XWMHints)
        x11.XGetWMHints.argtypes = [ctypes.c_void_p, Window]
        x11.XQueryTree.restype = ctypes.c_int
        x11.XQueryTree.argtypes = [
            ctypes.c_void_p, Window, ctypes.POINTER(Window), ctypes.POINTER(Window),
            ctypes.POINTER(ctypes.POINTER(Window)), ctypes.POINTER(ctypes.c_uint)]
        x11.XGetGeometry.restype = ctypes.c_int
        x11.XGetGeometry.argtypes = [
            ctypes.c_void_p, Window, ctypes.POINTER(Window), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint)]
        x11.XTranslateCoordinates.restype = ctypes.c_int
        x11.XTranslateCoordinates.argtypes = [
            ctypes.c_void_p, Window, Window, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(Window)]
        x11.XDisplayWidth.restype = ctypes.c_int
        x11.XDisplayWidth.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x11.XDisplayHeight.restype = ctypes.c_int
        x11.XDisplayHeight.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x11.XGetWindowAttributes.restype = ctypes.c_int
        x11.XGetWindowAttributes.argtypes = [ctypes.c_void_p, Window,
                                             ctypes.POINTER(XWindowAttributes)]
        x11.XSetErrorHandler.restype = ctypes.c_void_p
        x11.XSetErrorHandler.argtypes = [ctypes.c_void_p]
        xext.XShapeCombineRectangles.argtypes = [
            ctypes.c_void_p, Window, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(XRectangle), ctypes.c_int, ctypes.c_int, ctypes.c_int]
        xext.XShapeGetRectangles.restype = ctypes.POINTER(XRectangle)
        xext.XShapeGetRectangles.argtypes = [
            ctypes.c_void_p, Window, ctypes.c_int, ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int)]

    def atom(self, name: str) -> int:
        cached = self._atoms.get(name)
        if cached is None:
            cached = int(self.x11.XInternAtom(self.display, name.encode(), 0))
            self._atoms[name] = cached
        return cached


_lib: "_Lib | None" = None
_lib_failed = False


#: X's default error handler calls ``exit()``. A window that vanished between
#: our asking about it and X reading the request is an ordinary race here --
#: the host was closed mid-frame -- and must cost a return value, not the
#: daemon. Every read below is written to tolerate a zero.
@ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
def _swallow_error(_display, _event):  # pragma: no cover - only fires on a race
    return 0


def lib() -> "_Lib | None":
    """The X connection, or None when there is no reachable display."""
    global _lib, _lib_failed
    if _lib is None and not _lib_failed:
        try:
            _lib = _Lib()
            _lib.x11.XSetErrorHandler(ctypes.cast(_swallow_error, ctypes.c_void_p))
        except Exception:
            _lib_failed = True
    return _lib


def available() -> bool:
    """Is there an X display (real or XWayland) we can drive?"""
    return bool(os.environ.get("DISPLAY")) and lib() is not None


# ---------------------------------------------------------------------------
# Getting a window at all
# ---------------------------------------------------------------------------

#: GLFW's platform-selection init hint, and the value that means X11.
GLFW_PLATFORM = 0x00050003
GLFW_PLATFORM_X11 = 0x00060004


def prepare() -> bool:
    """Ask GLFW for X11 before raylib initialises it. Call before InitWindow.

    GLFW 3.4 picks its platform by trying Wayland first, and libwayland
    defaults to the socket ``wayland-0`` when ``WAYLAND_DISPLAY`` is unset --
    so clearing the environment variable does *not* get you X11, it just makes
    the choice harder to see. The documented lever is this init hint, which
    has to be set before ``glfwInit``; raylib calls that inside ``InitWindow``,
    so this runs first and nothing else has to change.

    Returns False when the hint could not be set, which the caller treats as
    "the window will be whatever GLFW picked" rather than as an error: a
    Wayland-backed strip still draws, it just cannot place itself.
    """
    try:
        import glob

        import raylib as rl

        so = glob.glob(os.path.join(os.path.dirname(rl.__file__), "_raylib_cffi*.so"))
        if not so:
            return False
        glfw = ctypes.CDLL(so[0])
        glfw.glfwInitHint.argtypes = [ctypes.c_int, ctypes.c_int]
        glfw.glfwInitHint(GLFW_PLATFORM, GLFW_PLATFORM_X11)
        return True
    except Exception:
        return False


def own_window(pid: int = 0) -> int:
    """Our own toplevel X11 window, found by ``_NET_WM_PID``.

    raylib's ``GetWindowHandle`` returns the ``GLFWwindow *`` on Linux, and
    ``glfwGetX11Window`` is not reachable through the cffi module's symbol
    table (it returns 0 with no error), so the handle has to be discovered
    rather than asked for. Walking the window tree for our own pid is exact,
    costs a few dozen property reads once at startup, and -- unlike reading
    ``_NET_CLIENT_LIST`` -- also finds the window while it is still unmapped,
    which is the only moment the overlay's styles can be applied without a
    visible flash.
    """
    handle = lib()
    if handle is None:
        return 0
    pid = pid or os.getpid()
    stack = [(handle.root, 0)]
    while stack:
        win, depth = stack.pop()
        if win != handle.root and _prop(handle, win, "_NET_WM_PID")[:1] == [pid]:
            return int(win)
        if depth < 3:
            stack.extend((child, depth + 1) for child in _children(handle, win))
    return 0


def _children(handle: _Lib, win: int) -> list[int]:
    root, parent = Window(), Window()
    kids = ctypes.POINTER(Window)()
    count = ctypes.c_uint()
    if not handle.x11.XQueryTree(handle.display, win, ctypes.byref(root),
                                 ctypes.byref(parent), ctypes.byref(kids),
                                 ctypes.byref(count)):
        return []
    out = list(kids[:count.value])
    handle.x11.XFree(kids)
    return out


def _prop(handle: _Lib, win: int, name: str, count: int = 1024) -> list[int]:
    """A 32-bit window property as a list of ints; [] when it is not set."""
    actual, fmt = Atom(), ctypes.c_int()
    items, after = ctypes.c_ulong(), ctypes.c_ulong()
    data = ctypes.POINTER(ctypes.c_ubyte)()
    status = handle.x11.XGetWindowProperty(
        handle.display, win, handle.atom(name), 0, count, 0, 0,
        ctypes.byref(actual), ctypes.byref(fmt), ctypes.byref(items),
        ctypes.byref(after), ctypes.byref(data))
    if status != 0 or not data:
        return []
    out: list[int] = []
    if fmt.value == 32:
        # Format 32 is a C *long* on the client side, not a uint32: X's own
        # 64-bit convention, and reading it as uint32 halves every value.
        out = list(ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))[:items.value])
    handle.x11.XFree(data)
    return out


# ---------------------------------------------------------------------------
# The overlay quartet
# ---------------------------------------------------------------------------


def apply_overlay_styles(win: int, cfg: Config) -> None:
    """Make the raylib window a proper overlay, before it is ever mapped.

    Four separate mechanisms, because X11 has no single "overlay" bit:

    * ``WM_HINTS.input = False`` plus ``_NET_WM_USER_TIME = 0`` -- this window
      takes no keyboard input and has never been interacted with, so mutter
      has no reason to focus it when it appears. Without this the strip
      appearing mid-sentence takes the keyboard, exactly as it did on Windows.
    * ``_NET_WM_WINDOW_TYPE_UTILITY`` -- an accessory of another window, which
      is what keeps it out of the window switcher.
    * ``_NET_WM_STATE_SKIP_TASKBAR`` / ``SKIP_PAGER`` -- and off the dock and
      the workspace overview with it.
    * an empty input shape -- the pointer falls through to whatever is behind.
    """
    handle = lib()
    if handle is None or not win:
        return
    hints = XWMHints()
    hints.flags = INPUT_HINT
    hints.input = 0
    handle.x11.XSetWMHints(handle.display, win, ctypes.byref(hints))
    _set_cardinal(handle, win, "_NET_WM_USER_TIME", 0)
    _set_atom_prop(handle, win, "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_UTILITY")
    # While the window is unmapped, _NET_WM_STATE is the client's to write and
    # is read by the window manager as the state to come up in. Once mapped it
    # belongs to the window manager and only a ClientMessage changes it --
    # which is why assert_states below exists as well as this.
    _set_states_property(handle, win, above=True)
    set_click_through(win, True)
    handle.x11.XFlush(handle.display)


#: Out of the switcher, the dock and the workspace overview, for its whole life.
QUIET_STATES = ("_NET_WM_STATE_SKIP_TASKBAR", "_NET_WM_STATE_SKIP_PAGER")

#: Above everything -- which is only right while something else can decide
#: *when* the strip is on screen. See :func:`brainrot.overlay.linux.wants_above`.
ABOVE_STATE = "_NET_WM_STATE_ABOVE"

OVERLAY_STATES = (ABOVE_STATE,) + QUIET_STATES


def _set_states_property(handle: _Lib, win: int, above: bool) -> None:
    names = ((ABOVE_STATE,) if above else ()) + QUIET_STATES
    atoms = (ctypes.c_ulong * len(names))(*(handle.atom(n) for n in names))
    handle.x11.XChangeProperty(handle.display, win, handle.atom("_NET_WM_STATE"),
                               XA_ATOM, 32, PROP_MODE_REPLACE,
                               ctypes.byref(atoms), len(names))


def assert_states(win: int, above: bool) -> None:
    """Ask for the window states again, now that the window is mapped.

    mutter does not carry ``_NET_WM_STATE`` across an unmap and remap: the
    strip goes idle at the end of a turn, comes back for the next one, and
    comes back in the ordinary stacking band -- where the Claude Code window
    it is standing on covers it. Measured on GNOME Shell 50.1, and invisible
    until the second turn of a session, which is the worst kind of invisible.
    Two atoms per message is the protocol's limit, hence two messages.
    """
    handle = lib()
    if handle is None or not win:
        return
    _wm_state(handle, win, NET_WM_STATE_ADD, *QUIET_STATES)
    _wm_state(handle, win, NET_WM_STATE_ADD if above else NET_WM_STATE_REMOVE,
              ABOVE_STATE)


def _set_cardinal(handle: _Lib, win: int, name: str, value: int) -> None:
    payload = ctypes.c_ulong(value)
    handle.x11.XChangeProperty(handle.display, win, handle.atom(name), XA_CARDINAL,
                               32, PROP_MODE_REPLACE, ctypes.byref(payload), 1)


def _set_atom_prop(handle: _Lib, win: int, name: str, value: str) -> None:
    payload = ctypes.c_ulong(handle.atom(value))
    handle.x11.XChangeProperty(handle.display, win, handle.atom(name), XA_ATOM,
                               32, PROP_MODE_REPLACE, ctypes.byref(payload), 1)


def _wm_state(handle: _Lib, win: int, action: int, *props: str) -> None:
    """Ask the window manager to add or remove window states.

    A ClientMessage to the *root*, not a property write: after a window is
    mapped ``_NET_WM_STATE`` belongs to the window manager, and writing it
    directly is ignored. Two states per message is the protocol's limit.
    """
    event = XEvent()
    event.xclient.type = CLIENT_MESSAGE
    event.xclient.send_event = 1
    event.xclient.display = handle.display
    event.xclient.window = win
    event.xclient.message_type = handle.atom("_NET_WM_STATE")
    event.xclient.format = 32
    event.xclient.data[0] = action
    for index, name in enumerate(props[:2]):
        event.xclient.data[1 + index] = handle.atom(name)
    event.xclient.data[3] = 1          # source indication: a normal application
    handle.x11.XSendEvent(handle.display, handle.root, 0,
                          SUBSTRUCTURE_REDIRECT_MASK | SUBSTRUCTURE_NOTIFY_MASK,
                          ctypes.byref(event))
    handle.x11.XFlush(handle.display)


def set_window_shown(win: int, shown: bool, above: bool = True) -> None:
    """Put the overlay on or off screen without ever activating it.

    ``XMapWindow`` rather than raylib's unhide for the same reason Windows
    needs ``SW_SHOWNA``: GLFW shows a window through ``glfwShowWindow``, whose
    ``GLFW_FOCUS_ON_SHOW`` defaults on, so raylib's way of showing a window
    also asks for the keyboard. Mapping it ourselves is the same show with the
    focus call left out -- and with ``WM_HINTS.input = False`` already set,
    mutter has nothing to focus even if it wanted to.
    """
    handle = lib()
    if handle is None or not win:
        return
    if shown:
        handle.x11.XMapWindow(handle.display, win)
        # Not once at startup: the states do not survive being unmapped, and
        # the overlay is unmapped at the end of every turn.
        assert_states(win, above)
    else:
        handle.x11.XUnmapWindow(handle.display, win)
    handle.x11.XFlush(handle.display)


def is_mapped(win: int) -> bool:
    """Whether the window is on screen right now.

    From the server's own attributes rather than from ``_NET_CLIENT_LIST``:
    the client list is maintained by the window manager and lags a map by as
    long as the window manager takes to notice, so asking it straight after a
    map reliably answers "no".
    """
    handle = lib()
    if handle is None or not win:
        return False
    attrs = XWindowAttributes()
    if not handle.x11.XGetWindowAttributes(handle.display, win, ctypes.byref(attrs)):
        return False
    return attrs.map_state == IS_VIEWABLE


def set_click_through(win: int, through: bool) -> None:
    """Whether the mouse falls through the overlay or lands on it.

    The *input* shape, never the bounding shape: the bounding shape is what
    the window looks like, and emptying that would make the strip invisible
    rather than intangible.
    """
    handle = lib()
    if handle is None or not win:
        return
    if through:
        handle.xext.XShapeCombineRectangles(handle.display, win, SHAPE_INPUT, 0, 0,
                                            None, 0, SHAPE_SET, 0)
    else:
        whole = XRectangle(0, 0, 0x7FFF, 0x7FFF)
        handle.xext.XShapeCombineRectangles(handle.display, win, SHAPE_INPUT, 0, 0,
                                            ctypes.byref(whole), 1, SHAPE_SET, 0)
    handle.x11.XFlush(handle.display)


def is_click_through(win: int) -> bool:
    handle = lib()
    if handle is None or not win:
        return False
    count, order = ctypes.c_int(), ctypes.c_int()
    rects = handle.xext.XShapeGetRectangles(handle.display, win, SHAPE_INPUT,
                                            ctypes.byref(count), ctypes.byref(order))
    if rects:
        handle.x11.XFree(rects)
    return count.value == 0


def set_opacity(win: int, alpha: float) -> None:
    """Whole-window opacity, the compositor's business rather than ours.

    raylib's ``SetWindowOpacity`` writes the same property, but only from the
    thread that owns the window; this one can be called from anywhere, which
    matters because the fade and the placement run in different places.
    """
    handle = lib()
    if handle is None or not win:
        return
    alpha = max(0.0, min(1.0, alpha))
    _set_cardinal(handle, win, "_NET_WM_WINDOW_OPACITY", int(alpha * 0xFFFFFFFF))
    handle.x11.XFlush(handle.display)


def move_window(win: int, x: int, y: int, width: int, height: int) -> None:
    """Reposition without activating or restacking."""
    handle = lib()
    if handle is None or not win:
        return
    handle.x11.XMoveResizeWindow(handle.display, win, int(x), int(y),
                                 max(1, int(width)), max(1, int(height)))
    handle.x11.XFlush(handle.display)


def window_rect(win: int) -> "tuple[int, int, int, int] | None":
    """Screen rectangle of a window, or None if it is gone.

    Via ``XTranslateCoordinates`` rather than ``XGetGeometry`` alone: the
    window manager reparents managed windows into a frame, so a window's own
    geometry is relative to that frame and not to the screen.
    """
    handle = lib()
    if handle is None or not win:
        return None
    root = Window()
    x, y = ctypes.c_int(), ctypes.c_int()
    w, h, border, depth = (ctypes.c_uint() for _ in range(4))
    if not handle.x11.XGetGeometry(handle.display, win, ctypes.byref(root),
                                   ctypes.byref(x), ctypes.byref(y), ctypes.byref(w),
                                   ctypes.byref(h), ctypes.byref(border),
                                   ctypes.byref(depth)):
        return None
    ax, ay, child = ctypes.c_int(), ctypes.c_int(), Window()
    if not handle.x11.XTranslateCoordinates(handle.display, win, handle.root, 0, 0,
                                            ctypes.byref(ax), ctypes.byref(ay),
                                            ctypes.byref(child)):
        return None
    return int(ax.value), int(ay.value), int(ax.value + w.value), int(ay.value + h.value)


def screen_rect() -> "tuple[int, int, int, int]":
    """The whole X screen, in X11 pixels."""
    handle = lib()
    if handle is None:
        return (0, 0, 0, 0)
    return (0, 0, int(handle.x11.XDisplayWidth(handle.display, 0)),
            int(handle.x11.XDisplayHeight(handle.display, 0)))


def work_area() -> "tuple[int, int, int, int] | None":
    """Usable desktop, panels excluded, in X11 pixels.

    ``_NET_WORKAREA`` is maintained by the window manager and is the only
    client-visible answer; when it is missing (some compositors never set it)
    the caller falls back to the whole screen, which costs the strip nothing
    worse than sitting under a panel.
    """
    handle = lib()
    if handle is None:
        return None
    area = _prop(handle, handle.root, "_NET_WORKAREA")
    if len(area) < 4:
        return None
    x, y, w, h = (int(v) for v in area[:4])
    return (x, y, x + w, y + h)


def is_window(win: int) -> bool:
    """Does this id still name a live window?"""
    handle = lib()
    if handle is None or not win:
        return False
    return window_rect(win) is not None


def root_of(win: int) -> int:
    """The toplevel a window id belongs to.

    Under a reparenting window manager a client's window sits inside a frame
    owned by the WM; walking up to the child of the root is what turns any of
    them into the toplevel everything else talks about.
    """
    handle = lib()
    if handle is None or not win:
        return 0
    current = int(win)
    for _ in range(8):
        root, parent = Window(), Window()
        kids = ctypes.POINTER(Window)()
        count = ctypes.c_uint()
        if not handle.x11.XQueryTree(handle.display, current, ctypes.byref(root),
                                     ctypes.byref(parent), ctypes.byref(kids),
                                     ctypes.byref(count)):
            return current
        if kids:
            handle.x11.XFree(kids)
        if not parent.value or parent.value == handle.root:
            return current
        current = int(parent.value)
    return current


def foreground_window() -> int:
    """The active window, as far as X11 knows.

    Which is not very far on a Wayland session: when a native Wayland window
    is focused this reports the last X11 window that was, or nothing.
    :mod:`brainrot.overlay.shell` is the answer that is actually true, and
    this is the fallback for a real X11 session.
    """
    handle = lib()
    if handle is None:
        return 0
    active = _prop(handle, handle.root, "_NET_ACTIVE_WINDOW")
    return int(active[0]) if active else 0


def foreground_root() -> int:
    return root_of(foreground_window())


def focus_window(win: int, focused: bool) -> None:
    """Hand the keyboard over, or give it back.

    The takeover chord is the only thing that may call this. Focusing needs
    both halves changed: ``WM_HINTS.input`` is what mutter consults before it
    will focus a window at all, and ``_NET_ACTIVE_WINDOW`` is the request.
    """
    handle = lib()
    if handle is None or not win:
        return
    hints = XWMHints()
    hints.flags = INPUT_HINT
    hints.input = 1 if focused else 0
    handle.x11.XSetWMHints(handle.display, win, ctypes.byref(hints))
    if focused:
        event = XEvent()
        event.xclient.type = CLIENT_MESSAGE
        event.xclient.send_event = 1
        event.xclient.display = handle.display
        event.xclient.window = win
        event.xclient.message_type = handle.atom("_NET_ACTIVE_WINDOW")
        event.xclient.format = 32
        event.xclient.data[0] = 2      # source indication: a pager or a user action
        handle.x11.XSendEvent(handle.display, handle.root, 0,
                              SUBSTRUCTURE_REDIRECT_MASK | SUBSTRUCTURE_NOTIFY_MASK,
                              ctypes.byref(event))
    handle.x11.XFlush(handle.display)
