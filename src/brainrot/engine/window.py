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

from ..config import Config
from . import rl


@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    width: int
    height: int


def compute_placement(cfg: Config) -> Placement:
    """Dock the strip to the left edge of the configured monitor. Uses real
    monitor origins, so multi-monitor setups place correctly."""
    width, height = cfg.width, cfg.height
    count = rl.GetMonitorCount()
    if count <= 0:
        return Placement(cfg.margin_x, 0, width, height)
    index = max(0, min(cfg.monitor, count - 1))
    origin = rl.GetMonitorPosition(index)
    screen_w = rl.GetMonitorWidth(index)
    screen_h = rl.GetMonitorHeight(index)
    height = min(height, screen_h) if screen_h > 0 else height
    width = min(width, screen_w) if screen_w > 0 else width
    y = int((screen_h - height) * cfg.anchor_y) if screen_h > 0 else 0
    return Placement(int(origin.x) + cfg.margin_x, max(0, int(origin.y) + y), width, height)


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

    def detach_host(self) -> None:
        """Release any host attachment. Only meaningful on Windows."""

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

    def _after_create(self, cfg: Config) -> None:
        self._cfg = cfg
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
        self._host_hwnd = hwnd
        self._reattach()

    def _reattach(self) -> None:
        if not self._host_hwnd or self._attached:
            return
        try:
            from ..overlay.win32 import attach_to_host

            self._attached = attach_to_host(self._hwnd(), self._host_hwnd)
        except Exception:
            pass

    def detach_host(self) -> None:
        """Give up ownership, keeping the host for next time.

        Called whenever the overlay goes idle. An owned window is destroyed
        along with its owner, so staying owned around the clock means the
        daemon's window dies the moment the user closes the terminal it was
        attached to. Being owned only while visible keeps that risk to the
        seconds a scene is actually on screen.
        """
        if os.name != "nt" or not self._attached:
            return
        try:
            from ..overlay.win32 import detach

            detach(self._hwnd())
        except Exception:
            pass
        self._attached = False


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
