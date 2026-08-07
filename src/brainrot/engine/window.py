"""Window management.

Three ways to put frames somewhere, one interface:

* ``OverlayWindow``  -- the product: undecorated, never focused, click-through,
  docked to a screen edge, faded via whole-window opacity. On Windows it also
  gets the Win32 treatment (no alt-tab entry, optional attachment above the
  Claude Code host window) from :mod:`brainrot.overlay.win32`.
* ``DesktopWindow``  -- an ordinary window for development.
* ``HeadlessWindow`` -- the software rasteriser under SDL's dummy driver, for
  tests and ``brainrot shoot``. No display server required.

raylib owns the actual window; these classes own *when* flags are applied,
because half of them only work if set before ``InitWindow`` and the other half
only after.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .. import placement as placement_store
from ..config import Config
from ..placement import Manual
from . import rl


@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def place(cfg: Config, work: Rect, host: Rect | None = None,
          manual: "Manual | None" = None) -> Placement:
    """Where the strip goes, given the desktop and the window it belongs to.

    Docking to a screen edge is what put the overlay straight on top of the
    Claude Code sidebar: the edge of the *monitor* has nothing to do with
    where the app keeps anything. The host window's rectangle does, so:

    1. **Beside the window** if the desktop has room for it there. The strip
       then covers nothing at all, which is the best outcome available.
    2. Otherwise **in the window's own margin** on the docked side -- the
       gutter a maximised app leaves outside its content column. Not free,
       but far cheaper than the navigation the other edge is made of.

    ``work`` is the work area rather than the whole monitor, so the taskbar
    is not somewhere the strip can hide.

    Pure geometry, no window API: everything here is exercised by tests that
    do not need a desktop.
    """
    width = min(cfg.width, max(1, work.width))
    height = min(cfg.height, max(1, work.height))
    right_side = cfg.dock != "left"

    if manual is not None:
        # Somebody dragged it here. Geometry does not get a vote any more --
        # only the clamp below, so a remembered spot cannot strand the strip
        # off the side of a smaller screen.
        anchor = host or work
        x = (anchor.right - width - manual.dx) if right_side else (anchor.left + manual.dx)
        y = anchor.top + manual.dy
        x = max(work.left, min(int(x), work.right - width))
        y = max(work.top, min(int(y), work.bottom - height))
        return Placement(int(x), int(y), int(width), int(height))

    if host is None:
        x = work.right - width - cfg.margin_x if right_side else work.left + cfg.margin_x
        top, bottom = work.top, work.bottom
    else:
        gap = cfg.margin_x * 2 + width
        if right_side and work.right - host.right >= gap:
            x = host.right + cfg.margin_x                 # beside it, covering nothing
        elif not right_side and host.left - work.left >= gap:
            x = host.left - cfg.margin_x - width
        elif right_side:
            x = host.right - width - cfg.margin_x         # tucked into its own margin
        else:
            x = host.left + cfg.margin_x
        top = max(work.top, host.top)
        bottom = min(work.bottom, host.bottom)

    travel = max(0, (bottom - top) - height - cfg.margin_y * 2)
    y = top + cfg.margin_y + int(travel * cfg.anchor_y)
    # Never leave the work area, however small the window it is following is.
    x = max(work.left, min(x, work.right - width))
    y = max(work.top, min(y, work.bottom - height))
    return Placement(int(x), int(y), int(width), int(height))


def monitor_work_area(cfg: Config) -> Rect:
    """The configured monitor, as raylib sees it. No taskbar information --
    the Win32 path below has that, and this is the fallback."""
    count = rl.GetMonitorCount()
    if count <= 0:
        return Rect(0, 0, max(1, cfg.width), max(1, cfg.height))
    index = max(0, min(cfg.monitor, count - 1))
    origin = rl.GetMonitorPosition(index)
    return Rect(int(origin.x), int(origin.y),
                int(origin.x) + rl.GetMonitorWidth(index),
                int(origin.y) + rl.GetMonitorHeight(index))


def compute_placement(cfg: Config) -> Placement:
    """Placement with nothing known about a host window."""
    return place(cfg, monitor_work_area(cfg))


class _BaseWindow:
    creation_flags = 0

    #: Whether this window can receive keyboard input by simply being focused.
    #: True for ordinary windows; the overlay is built never to take focus, so
    #: it has to be handed the keyboard deliberately (engine/input.py).
    accepts_input = True

    def __init__(self) -> None:
        self.width = 0
        self.height = 0
        self._visible = True
        self._opacity = -1.0

    def create(self, cfg: Config) -> None:
        rl.SetTraceLogLevel(rl.LOG_WARNING)
        rl.SetConfigFlags(self.creation_flags)
        rl.InitWindow(cfg.width, cfg.height, b"claude-brainrot")
        self.width, self.height = cfg.width, cfg.height
        # Settle the capture correction against this renderer while there is
        # nothing on screen worth keeping -- it draws marker frames.
        rl.calibrate_capture()
        self._after_create(cfg)

    def _after_create(self, cfg: Config) -> None:
        pass

    # -- frame ------------------------------------------------------------

    def begin(self) -> None:
        rl.BeginDrawing()
        # Scenes fully cover the frame, but this is not (only) about colour:
        # ClearBackground also resets the depth buffer, and without it every
        # frame after the first fails the depth test against stale depth.
        rl.ClearBackground((0, 0, 0, 255))

    def end(self) -> None:
        rl.EndDrawing()

    def pump(self) -> None:
        """Keep the event queue drained while idle (no scene, no draw)."""
        rl.BeginDrawing()
        rl.ClearBackground((0, 0, 0, 255))
        rl.EndDrawing()

    def should_close(self) -> bool:
        return bool(rl.WindowShouldClose())

    # -- state ------------------------------------------------------------

    def set_visible(self, visible: bool) -> None:
        if visible == self._visible:
            return
        self._visible = visible
        if visible:
            rl.ClearWindowState(rl.FLAG_WINDOW_HIDDEN)
        else:
            rl.SetWindowState(rl.FLAG_WINDOW_HIDDEN)

    def set_opacity(self, alpha: float) -> None:
        alpha = max(0.0, min(1.0, alpha))
        if abs(alpha - self._opacity) < 0.004:
            return
        self._opacity = alpha
        rl.SetWindowOpacity(alpha)

    def attach_host(self, hwnd: int) -> None:
        """Layer this window relative to the Claude Code host window. Only the
        Windows overlay backend has anything to do here."""

    def follow_host(self) -> None:
        """Keep station on the host window. Windows overlay only."""

    # -- being dragged by hand. Only the overlay can be; the rest of these
    # are windows the window manager already lets you drag by their title bar.

    def rect(self) -> "Rect | None":
        return None

    def set_click_through(self, through: bool) -> None:
        pass

    def move_to(self, x: int, y: int) -> None:
        pass

    def remember_placement(self) -> None:
        pass

    def clear_placement(self) -> None:
        pass

    def detach_host(self) -> None:
        """Release any host attachment. Only meaningful on Windows."""

    def focus_allows(self, hosts, foreground: int | None = None) -> bool:
        """May the overlay be on screen, given who is in front right now?

        An ordinary window is being looked at by definition -- it is a window
        the user opened. Only the overlay has to earn its place.
        """
        return True

    def destroy(self) -> None:
        rl.CloseWindow()


class OverlayWindow(_BaseWindow):
    creation_flags = (
        rl.FLAG_WINDOW_UNDECORATED
        | rl.FLAG_WINDOW_TOPMOST
        | rl.FLAG_WINDOW_UNFOCUSED
        | rl.FLAG_WINDOW_MOUSE_PASSTHROUGH
        | rl.FLAG_VSYNC_HINT
    )

    #: Built never to take focus, so it cannot be typed into until the
    #: takeover chord deliberately makes it focusable.
    accepts_input = False

    def __init__(self) -> None:
        super().__init__()
        self._cfg: Config | None = None
        self._host_hwnd = 0
        self._attached = False
        self._placed: Placement | None = None
        self._manual: Manual | None = None
        self._click_through = True

    def _after_create(self, cfg: Config) -> None:
        self._cfg = cfg
        self._manual = placement_store.load()
        placement = compute_placement(cfg)
        rl.SetWindowPosition(placement.x, placement.y)
        self.set_visible(False)
        if os.name == "nt":
            try:
                from ..overlay.win32 import apply_overlay_styles

                apply_overlay_styles(self._hwnd(), cfg)
            except Exception:
                # A Win32 API hiccup should degrade to a plain topmost
                # click-through window, not take the daemon down.
                pass

    def _hwnd(self) -> int:
        return int(rl.ffi.cast("intptr_t", rl.GetWindowHandle()))

    def set_visible(self, visible: bool) -> None:
        if os.name != "nt":
            super().set_visible(visible)
        elif visible != self._visible:
            self._visible = visible
            try:
                # Not raylib's hide flag: that route asks Windows to activate
                # the window on the way up, and it succeeds -- keyboard focus
                # and all. See win32.set_window_shown.
                from ..overlay.win32 import set_window_shown

                set_window_shown(self._hwnd(), visible)
            except Exception:
                self._visible = not visible
                super().set_visible(visible)
        # Re-take ownership on the way back up; detach_host dropped it when the
        # overlay last went idle.
        if visible:
            self._reattach()

    def attach_host(self, hwnd: int) -> None:
        """Remember the Claude Code host window, and ride above it."""
        if os.name != "nt" or not hwnd:
            return
        if self._cfg is not None and self._cfg.attach != "host":
            return
        if hwnd != self._host_hwnd:
            # A different window announced itself -- a second Claude Code
            # session, or the same one restarted. Without this the "already
            # attached" guard below pins the overlay to the first host it ever
            # saw, for the life of the daemon.
            self._host_hwnd = hwnd
            self._attached = False
        self._reattach()

    def _reattach(self) -> None:
        if not self._host_hwnd or self._attached:
            return
        try:
            from ..overlay.win32 import attach_to_host

            self._attached = attach_to_host(self._hwnd(), self._host_hwnd)
            if not self._attached:
                # The handle no longer names a window. Forgetting it is the
                # point: a remembered dead host is a host that can never be
                # matched against the foreground and never be replaced.
                self._host_hwnd = 0
        except Exception:
            pass

    def detach_host(self) -> None:
        """Give up ownership, keeping the host for next time.

        Called whenever the overlay goes idle. An owned window is destroyed
        along with its owner, so staying owned around the clock means the
        daemon's window dies the moment the user closes the terminal it was
        attached to. Being owned only while visible keeps that risk to the
        seconds a scene is actually on screen.

        Deliberately not guarded on ``self._attached``: the flag records what
        we believe, and the whole class of bug here is the belief drifting
        away from what Windows actually has recorded against the window.
        """
        if os.name != "nt":
            return
        try:
            from ..overlay.win32 import detach

            detach(self._hwnd(), topmost=self._topmost_mode())
        except Exception:
            pass
        self._attached = False

    # -- focus ------------------------------------------------------------

    def focus_allows(self, hosts, foreground: int | None = None) -> bool:
        """Is the user looking at something this overlay belongs in front of?

        Two ways to qualify:

        * the window in front is the host of a session that is working, or
        * the window in front is *this overlay*. Our own window being in front
          is never evidence that the user has left. The takeover chord puts it
          there on purpose (``engine/input.py:_grab`` calls
          ``SetForegroundWindow``), so a plain "hide unless the host is in
          front" rule hides the strip at the exact moment someone asks to play
          with it. Stated this way rather than as "unless the takeover is
          active" because it needs no coordination with the takeover's state.

        ``foreground`` overrides the live query, for tests that cannot move
        the foreground window of somebody's actual desktop around.
        """
        if os.name != "nt":
            return True
        from ..overlay.win32 import foreground_root, is_window, root_of

        # Every frame, because the host can be closed at any point in one.
        if self._host_hwnd and not is_window(self._host_hwnd):
            self._forget_host()

        front = foreground_root() if foreground is None else root_of(foreground)
        if not front:
            return False
        if front == root_of(self._hwnd()):
            return True
        return any(is_window(host) and root_of(host) == front for host in hosts)

    def _forget_host(self) -> None:
        """The host window is gone: drop it, and the ownership recorded
        against it, rather than staying latched to a handle that can no longer
        match anything."""
        self._host_hwnd = 0
        if self._attached:
            try:
                from ..overlay.win32 import detach

                detach(self._hwnd(), topmost=self._topmost_mode())
            except Exception:
                pass
        self._attached = False

    def _topmost_mode(self) -> bool:
        return self._cfg is not None and self._cfg.attach == "topmost"

    # -- placement --------------------------------------------------------

    def follow_host(self) -> None:
        """Sit beside the Claude Code window, or in its margin, or wherever
        it was last dragged to.

        Called while the strip is on screen, so it keeps up with a window
        that gets moved, resized or maximised underneath it rather than
        holding a position that was right when the turn started.
        """
        if os.name != "nt" or self._cfg is None:
            return
        try:
            from ..overlay.win32 import move_window, window_rect, work_area

            host = window_rect(self._host_hwnd) if self._host_hwnd else None
            area = work_area(self._host_hwnd or 0)
            if area is None:
                return
            wanted = place(self._cfg, Rect(*area),
                           Rect(*host) if host else None, self._manual)
        except Exception:
            return
        if wanted == self._placed:
            return
        self._placed = wanted
        try:
            move_window(self._hwnd(), wanted.x, wanted.y, wanted.width, wanted.height)
        except Exception:
            self._placed = None

    # -- being dragged ----------------------------------------------------

    def rect(self) -> Rect | None:
        if os.name != "nt":
            return None
        try:
            from ..overlay.win32 import window_rect

            found = window_rect(self._hwnd())
        except Exception:
            return None
        return Rect(*found) if found else None

    def set_click_through(self, through: bool) -> None:
        """Let the mouse fall through, or catch it.

        Caught only while the drag chord is held over the strip: the rest of
        the time a click belongs to whatever is behind, and taking one would
        make the overlay exactly the thing it is built not to be.
        """
        if os.name != "nt" or through == self._click_through:
            return
        try:
            from ..overlay.win32 import set_click_through

            set_click_through(self._hwnd(), through)
        except Exception:
            return
        self._click_through = through

    def move_to(self, x: int, y: int) -> None:
        """Put the strip here, now -- mid-drag, following the pointer."""
        if os.name != "nt":
            return
        here = self.rect()
        if here is None:
            return
        try:
            from ..overlay.win32 import move_window

            move_window(self._hwnd(), int(x), int(y), here.width, here.height)
        except Exception:
            return
        self._placed = Placement(int(x), int(y), here.width, here.height)

    def remember_placement(self) -> None:
        """Keep where it was just dropped, as an offset from the host window."""
        if os.name != "nt" or self._cfg is None:
            return
        here = self.rect()
        if here is None:
            return
        try:
            from ..overlay.win32 import window_rect, work_area

            host = window_rect(self._host_hwnd) if self._host_hwnd else None
            anchor = Rect(*(host or work_area(self._host_hwnd or 0) or (0, 0, 0, 0)))
        except Exception:
            return
        if self._cfg.dock != "left":
            dx = anchor.right - here.right
        else:
            dx = here.left - anchor.left
        self._manual = Manual(int(dx), int(here.top - anchor.top))
        placement_store.save(self._manual)

    def clear_placement(self) -> None:
        """Back to placing itself. The way out of a corner you dragged it into."""
        self._manual = None
        self._placed = None
        placement_store.clear()


class DesktopWindow(_BaseWindow):
    creation_flags = rl.FLAG_VSYNC_HINT


class HeadlessWindow(_BaseWindow):
    """Software rendering; frames only exist to be captured.

    There is one raylib window per process, so create() is idempotent -- a
    second headless consumer (tests, an in-process daemon) resizes the
    existing window rather than fighting over it -- and destroy() is a no-op:
    the process exit reclaims an offscreen framebuffer just fine.
    """

    def create(self, cfg: Config) -> None:
        os.environ["BRAINROT_HEADLESS"] = "1"
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        if rl.IsWindowReady():
            # Only resize when the size actually differs. Resizing is not a
            # free no-op: on the GPU (GLFW) build under Windows it posts to the
            # thread that owns the window and blocks until that thread pumps
            # its message queue. A caller on a *different* thread -- which is
            # exactly how the integration tests drive the daemon -- therefore
            # deadlocks on a resize to the size the window already is.
            if (rl.GetScreenWidth(), rl.GetScreenHeight()) != (cfg.width, cfg.height):
                rl.SetWindowSize(cfg.width, cfg.height)
            self.width, self.height = cfg.width, cfg.height
            return
        super().create(cfg)

    def set_visible(self, visible: bool) -> None:
        self._visible = visible

    def set_opacity(self, alpha: float) -> None:
        self._opacity = alpha

    def should_close(self) -> bool:
        return False

    def destroy(self) -> None:
        pass


def select_backend(force: str = "") -> _BaseWindow:
    choice = (force or os.environ.get("BRAINROT_BACKEND") or "").strip().lower()
    if choice in ("headless", "shoot"):
        return HeadlessWindow()
    if choice == "desktop":
        return DesktopWindow()
    if choice in ("win32", "overlay"):
        return OverlayWindow()
    if rl.HEADLESS:
        return HeadlessWindow()
    if os.name == "nt":
        return OverlayWindow()
    return DesktopWindow()
