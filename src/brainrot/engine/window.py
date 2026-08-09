"""Window management.

Three ways to put frames somewhere, one interface:

* ``OverlayWindow``  -- the product: undecorated, never focused, click-through,
  standing beside the Claude Code window, faded via whole-window opacity.
  The parts raylib has no API for -- no switcher entry, click-through, showing
  without activating, knowing where the Claude Code window is -- come from the
  platform backend in :mod:`brainrot.overlay`.
* ``DesktopWindow``  -- an ordinary window for development.
* ``HeadlessWindow`` -- the software rasteriser under SDL's dummy driver, for
  tests and ``brainrot shoot``. No display server required.

raylib owns the actual window; these classes own *when* flags are applied,
because half of them only work if set before ``InitWindow`` and the other half
only after.
"""

from __future__ import annotations

import os
import time
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
          manual: "Manual | None" = None, scale: float = 1.0) -> Placement:
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

    ``scale`` is device pixels per logical pixel. Every rectangle passed in is
    already in device pixels; the *config* is not, because someone writing
    ``width = 360`` means a strip that looks like 360 pixels rather than one
    that measures 360 of them on a 200% display. So the numbers that come from
    the config -- the size and the two margins -- are the only ones scaled
    here, and they are scaled at the one point where both spaces meet.

    Pure geometry, no window API: everything here is exercised by tests that
    do not need a desktop.
    """
    scale = scale if scale > 0 else 1.0
    width = min(round(cfg.width * scale), max(1, work.width))
    height = min(round(cfg.height * scale), max(1, work.height))
    margin_x = round(cfg.margin_x * scale)
    margin_y = round(cfg.margin_y * scale)
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
        x = work.right - width - margin_x if right_side else work.left + margin_x
        top, bottom = work.top, work.bottom
    else:
        gap = margin_x * 2 + width
        if right_side and work.right - host.right >= gap:
            x = host.right + margin_x                     # beside it, covering nothing
        elif not right_side and host.left - work.left >= gap:
            x = host.left - margin_x - width
        elif right_side:
            x = host.right - width - margin_x             # tucked into its own margin
        else:
            x = host.left + margin_x
        top = max(work.top, host.top)
        bottom = min(work.bottom, host.bottom)

    travel = max(0, (bottom - top) - height - margin_y * 2)
    y = top + margin_y + int(travel * cfg.anchor_y)
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


def compute_placement(cfg: Config, scale: float = 1.0) -> Placement:
    """Placement with nothing known about a host window."""
    return place(cfg, monitor_work_area(cfg), scale=scale)


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

    def flags(self, cfg: Config) -> int:
        return self.creation_flags

    def create(self, cfg: Config) -> None:
        rl.SetTraceLogLevel(rl.LOG_WARNING)
        rl.SetConfigFlags(self.flags(cfg))
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

    def present(self, draw, limit: int = 6) -> None:
        """Draw a frame and leave it where a capture can read it back.

        Not one ``begin/draw/end``: a read-back shows the buffer the swap chain
        has finished with, which is one frame behind on a GPU under Windows and
        two behind on Mesa under a Wayland compositor. So the same frame goes
        up repeatedly until the read-back settles.

        The measured depth is used as the *floor* and convergence decides the
        rest, because the depth is not actually a constant: a compositor
        throttles frame callbacks for a surface nobody is looking at, so
        counting presents is right on average and occasionally one short --
        which shows up as a screenshot test that fails once an afternoon and
        is blamed on everything except the buffer it came from.

        Requires that ``draw`` really is the same picture every time, which is
        a property the scenes are separately tested for.
        """
        for _ in range(max(1, rl.present_lag())):
            self.begin()
            draw()
            self.end()
        previous = None
        for _ in range(limit):
            self.begin()
            draw()
            self.end()
            current = rl.capture_frame()
            if current is not None and current == previous:
                return
            previous = current

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
    """The product: a strip that is there while Claude is working and in the
    way of nothing.

    Four properties, and every one of them needs the platform backend rather
    than raylib (:mod:`brainrot.overlay`):

    * clicks fall through to whatever is behind;
    * it never takes focus, not even at the moment it appears;
    * it is not in the window switcher;
    * it stands beside the Claude Code window, and follows it.

    The backend differs -- Win32 on Windows, X11-on-XWayland plus a
    gnome-shell extension on Linux -- but the sequence does not: create the
    window, apply the styles *before* anything is on screen, then show and
    hide it without ever activating it.
    """

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

    #: How long to wait at startup for the compositor to say how big a pixel
    #: is. The gnome-shell extension speaks within 250ms of the daemon
    #: starting; this only has to outlast that, and only costs anything on a
    #: machine where the extension is not installed at all.
    SCALE_WAIT = 0.6

    def __init__(self) -> None:
        super().__init__()
        self._native = None
        self._cfg: Config | None = None
        self._win = 0
        self._host = 0
        self._attached = False
        self._placed: Placement | None = None
        self._manual: Manual | None = None
        self._click_through = True
        self._ratio = 1.0
        self._target = None

    # -- creation ---------------------------------------------------------

    def flags(self, cfg: Config) -> int:
        flags = self.creation_flags
        if getattr(self._native, "CREATE_HIDDEN", False):
            # The styles that stop this window taking the keyboard have to be
            # on it before it is ever mapped, and there is no way to apply
            # them to a window that does not exist yet. So it is born hidden
            # and shown deliberately, which is also how it is shown from then
            # on.
            flags |= rl.FLAG_WINDOW_HIDDEN
        return flags

    def create(self, cfg: Config) -> None:
        from .. import overlay

        self._native = overlay.native()
        if self._native is not None:
            # Chooses X11 over Wayland on Linux, and must happen before raylib
            # calls glfwInit inside InitWindow. A no-op on Windows.
            self._native.prepare()
        self._cfg = cfg
        self._ratio = self._measure_scale()

        rl.SetTraceLogLevel(rl.LOG_WARNING)
        rl.SetConfigFlags(self.flags(cfg))
        # The window is sized in device pixels; the scenes are drawn in the
        # config's pixels. On a 100% display those are the same number and
        # nothing below does anything.
        self.width = max(1, round(cfg.width * self._ratio))
        self.height = max(1, round(cfg.height * self._ratio))
        rl.InitWindow(self.width, self.height, b"claude-brainrot")
        rl.calibrate_capture()
        self._after_create(cfg)

    def _measure_scale(self) -> float:
        """Device pixels per logical pixel, waited for rather than assumed.

        A strip configured 360 wide should *look* 360 wide, which on a 200%
        display means a window 720 pixels across drawn from a 360-pixel scene.
        The number comes from the compositor, so there is a moment at startup
        where it is not known yet -- and guessing 1.0 and correcting later
        would mean resizing the window under a running scene.
        """
        native = self._native
        if native is None or not hasattr(native, "scale"):
            return 1.0
        deadline = time.monotonic() + self.SCALE_WAIT
        while getattr(native, "degraded", lambda: False)() and time.monotonic() < deadline:
            time.sleep(0.02)
        try:
            ratio = float(native.scale())
        except Exception:
            return 1.0
        return ratio if 0.25 <= ratio <= 8.0 else 1.0

    def _after_create(self, cfg: Config) -> None:
        self._manual = placement_store.load()
        if self._native is None:
            rl.SetWindowPosition(*compute_placement(cfg, self._ratio)[:2])
            self.set_visible(False)
            return
        self._win = self._native.own_window(
            int(rl.ffi.cast("intptr_t", rl.GetWindowHandle())))
        try:
            self._native.apply_overlay_styles(self._win, cfg)
        except Exception:
            # A window API hiccup should degrade to a plain topmost
            # click-through window, not take the daemon down.
            pass
        placement = compute_placement(cfg, self._ratio)
        self._move(placement)
        self.set_visible(False)
        if self._ratio != 1.0:
            # Scenes keep their own pixel geometry -- a HUD chip is 14 points
            # high because that is what looks right, not because of the
            # display -- so the frame is drawn at the scene's size and scaled
            # on the way out, rather than the scenes being told to draw bigger.
            self._target = rl.LoadRenderTexture(cfg.width, cfg.height)

    # -- frame ------------------------------------------------------------

    def begin(self) -> None:
        if self._target is None:
            super().begin()
            return
        rl.BeginTextureMode(self._target)
        rl.ClearBackground((0, 0, 0, 255))

    def end(self) -> None:
        if self._target is None:
            super().end()
            return
        rl.EndTextureMode()
        texture = self._target.texture
        rl.BeginDrawing()
        rl.ClearBackground((0, 0, 0, 255))
        # Negative source height: a render texture is stored bottom-up, and
        # blitting it the right way round is what that sign means to raylib.
        rl.DrawTexturePro(
            texture,
            (0.0, 0.0, float(texture.width), -float(texture.height)),
            (0.0, 0.0, float(rl.GetScreenWidth()), float(rl.GetScreenHeight())),
            (0.0, 0.0), 0.0, rl.WHITE4)
        rl.EndDrawing()

    # -- showing ----------------------------------------------------------

    def set_visible(self, visible: bool) -> None:
        if visible:
            self._apply_stacking()
        if self._native is None:
            super().set_visible(visible)
        elif visible != self._visible:
            self._visible = visible
            try:
                # Not raylib's hide flag: that route asks the window manager to
                # activate the window on the way up, and it succeeds --
                # keyboard focus and all. Both backends have a show that
                # leaves the activation out.
                self._native.set_window_shown(self._win, visible)
            except Exception:
                self._visible = not visible
                super().set_visible(visible)
        # Re-take ownership on the way back up; detach_host dropped it when the
        # overlay last went idle.
        if visible:
            self._reattach()

    def attach_host(self, host: int) -> None:
        """Remember the Claude Code host window, and ride above it."""
        if self._native is None or not host:
            return
        if self._cfg is not None and self._cfg.attach != "host":
            return
        if host != self._host:
            # A different window announced itself -- a second Claude Code
            # session, or the same one restarted. Without this the "already
            # attached" guard below pins the overlay to the first host it ever
            # saw, for the life of the daemon.
            self._host = host
            self._attached = False
        self._reattach()

    def _reattach(self) -> None:
        if self._native is None or not self._host or self._attached:
            return
        try:
            self._attached = self._native.attach_to_host(self._win, self._host)
            if not self._attached:
                # The handle no longer names a window. Forgetting it is the
                # point: a remembered dead host is a host that can never be
                # matched against the foreground and never be replaced.
                self._host = 0
        except Exception:
            pass

    def detach_host(self) -> None:
        """Give up ownership, keeping the host for next time.

        Called whenever the overlay goes idle. On Windows an owned window is
        destroyed along with its owner, so staying owned around the clock
        means the daemon's window dies the moment the user closes the terminal
        it was attached to; being owned only while visible keeps that risk to
        the seconds a scene is actually on screen. On Linux there is no
        ownership to give up and this is a no-op.

        Deliberately not guarded on ``self._attached``: the flag records what
        we believe, and the whole class of bug here is the belief drifting
        away from what the window manager actually has recorded.
        """
        if self._native is None:
            return
        try:
            self._native.detach(self._win, topmost=self._topmost_mode())
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
          there on purpose, so a plain "hide unless the host is in front" rule
          hides the strip at the exact moment someone asks to play with it.
          Stated this way rather than as "unless the takeover is active"
          because it needs no coordination with the takeover's state.

        ``foreground`` overrides the live query, for tests that cannot move
        the foreground window of somebody's actual desktop around.
        """
        native = self._native
        if native is None:
            return True
        if not native.focus_known():
            # Nothing can be said about who is in front -- no shell extension,
            # on a desktop that will not tell a client. Fail *open*: an
            # overlay that turns up when it should not is a nuisance, one that
            # can never appear again is indistinguishable from a dead daemon.
            return True

        # Every frame, because the host can be closed at any point in one.
        if self._host and not native.host_alive(self._host):
            self._forget_host()

        front = native.foreground_host() if foreground is None else foreground
        if not front:
            return False
        if native.is_own_window(front, self._win):
            return True
        return any(native.same_host(front, host) for host in hosts
                   if native.host_alive(host))

    def _forget_host(self) -> None:
        """The host window is gone: drop it, and the ownership recorded
        against it, rather than staying latched to a handle that can no longer
        match anything."""
        self._host = 0
        if self._attached and self._native is not None:
            try:
                self._native.detach(self._win, topmost=self._topmost_mode())
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
        native = self._native
        if native is None or self._cfg is None:
            return
        self._recheck_scale()
        self._apply_stacking()
        try:
            host = native.host_rect(self._host) if self._host else None
            area = native.work_area(self._host or 0)
            if area is None:
                return
            wanted = place(self._cfg, Rect(*area), Rect(*host) if host else None,
                           self._manual, self._ratio)
        except Exception:
            return
        if wanted == self._placed:
            return
        self._move(wanted)

    def _apply_stacking(self) -> bool:
        """Which stacking band the strip belongs in, asked again each time.

        Only a backend that has more than one answer defines this; Windows
        decides where the strip sits by *ownership* and has nothing to
        reconsider. On Linux the answer depends on whether anything can say
        who is in front, which can start being true at any moment.
        """
        native = self._native
        apply = getattr(native, "apply_stacking", None)
        if apply is None or self._cfg is None or not self._win:
            return False
        try:
            return bool(apply(self._win, self._cfg))
        except Exception:
            return False

    def _recheck_scale(self) -> None:
        """Notice a change in what a pixel is, and rebuild for it.

        :meth:`_measure_scale` waits at startup for the compositor to answer,
        but "waits" is not "gets an answer": start the daemon before the shell
        extension and it comes up believing in 100%, then stays half the size
        it should be for the rest of the day. It is also the honest answer to
        the display scale being changed while the daemon runs.

        Cheap enough to ask every frame -- it is a division on a number that
        is already in memory -- and the rebuild only happens on a real change.
        """
        native = self._native
        if native is None or self._cfg is None:
            return
        try:
            ratio = float(native.scale())
        except Exception:
            return
        if not 0.25 <= ratio <= 8.0 or abs(ratio - self._ratio) < 0.01:
            return
        self._ratio = ratio
        self._placed = None            # the size changed, so the position must
        if self._target is not None:
            try:
                rl.UnloadRenderTexture(self._target)
            except Exception:
                pass
            self._target = None
        if ratio != 1.0:
            self._target = rl.LoadRenderTexture(self._cfg.width, self._cfg.height)

    def _move(self, wanted: Placement) -> None:
        self._placed = wanted
        try:
            self._native.move_window(self._win, wanted.x, wanted.y,
                                     wanted.width, wanted.height)
        except Exception:
            self._placed = None
            return
        self.width, self.height = wanted.width, wanted.height

    # -- being dragged ----------------------------------------------------

    def rect(self) -> Rect | None:
        if self._native is None:
            return None
        try:
            found = self._native.own_rect(self._win)
        except Exception:
            return None
        return Rect(*found) if found else None

    def set_click_through(self, through: bool) -> None:
        """Let the mouse fall through, or catch it.

        Caught only while the drag chord is held over the strip: the rest of
        the time a click belongs to whatever is behind, and taking one would
        make the overlay exactly the thing it is built not to be.
        """
        if self._native is None or through == self._click_through:
            return
        try:
            self._native.set_click_through(self._win, through)
        except Exception:
            return
        self._click_through = through

    def move_to(self, x: int, y: int) -> None:
        """Put the strip here, now -- mid-drag, following the pointer."""
        if self._native is None:
            return
        here = self.rect()
        if here is None:
            return
        try:
            self._native.move_window(self._win, int(x), int(y),
                                     here.width, here.height)
        except Exception:
            return
        self._placed = Placement(int(x), int(y), here.width, here.height)

    def remember_placement(self) -> None:
        """Keep where it was just dropped, as an offset from the host window."""
        native = self._native
        if native is None or self._cfg is None:
            return
        here = self.rect()
        if here is None:
            return
        try:
            host = native.host_rect(self._host) if self._host else None
            anchor = Rect(*(host or native.work_area(self._host or 0) or (0, 0, 0, 0)))
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

    def destroy(self) -> None:
        if self._target is not None:
            try:
                rl.UnloadRenderTexture(self._target)
            except Exception:
                pass
            self._target = None
        super().destroy()


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
    if choice in ("win32", "x11", "overlay"):
        return OverlayWindow()
    if rl.HEADLESS:
        return HeadlessWindow()

    from .. import overlay

    # An overlay is only worth asking for where the window system will let us
    # build one. Everywhere else -- a Mac, a Linux box with no display -- a
    # plain window is both what you get and what you want.
    return OverlayWindow() if overlay.native() is not None else DesktopWindow()
