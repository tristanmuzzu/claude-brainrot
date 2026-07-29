"""Windows overlay: always-on-top, click-through, never steals focus.

The window has to be present without ever being *in the way*, which takes four
independent pieces of window state. Missing any one of them produces a
subtly broken overlay, so they are documented individually below.
"""

from __future__ import annotations

import pygame

try:
    import win32api
    import win32con
    import win32gui
except ImportError as exc:  # pragma: no cover - platform specific
    raise ImportError("pywin32 is required for the win32 overlay backend") from exc

from ..config import Config
from .base import Placement, compute_placement


class Win32Backend:
    def __init__(self) -> None:
        self._hwnd: int | None = None
        self._surface: pygame.Surface | None = None
        self._placement: Placement | None = None
        self._visible = False
        self._alpha = -1.0

    def create(self, cfg: Config) -> pygame.Surface:
        placement = compute_placement(cfg)
        self._placement = placement

        # SDL honours this only at window creation time, so it must be set
        # before set_mode rather than corrected afterwards (which would show a
        # visible jump from the default position).
        import os

        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{placement.x},{placement.y}"

        pygame.display.init()
        self._surface = pygame.display.set_mode(
            (placement.width, placement.height),
            pygame.NOFRAME,
        )
        pygame.display.set_caption("claude-brainrot")

        self._hwnd = pygame.display.get_wm_info()["window"]
        self._apply_styles()
        self.set_visible(False)
        return self._surface

    def _apply_styles(self) -> None:
        hwnd = self._hwnd
        if hwnd is None:
            return

        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= (
            # LAYERED: enables per-window alpha, which is how fades work.
            win32con.WS_EX_LAYERED
            # TRANSPARENT: mouse input passes straight through to whatever is
            # underneath. Without this the strip eats clicks on your editor.
            | win32con.WS_EX_TRANSPARENT
            # NOACTIVATE: the window never takes focus, so your keystrokes keep
            # going to the terminal when it appears mid-typing.
            | win32con.WS_EX_NOACTIVATE
            # TOOLWINDOW: keeps it out of alt-tab and the taskbar.
            | win32con.WS_EX_TOOLWINDOW
        )
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        placement = self._placement
        assert placement is not None
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            placement.x,
            placement.y,
            placement.width,
            placement.height,
            # SWP_NOACTIVATE matters as much as the style bit: without it the
            # topmost call itself would steal focus each time we show.
            win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW,
        )

    def set_visible(self, visible: bool) -> None:
        if self._hwnd is None or visible == self._visible:
            return
        self._visible = visible
        # SW_SHOWNOACTIVATE rather than SW_SHOW, again to avoid focus theft.
        flag = win32con.SW_SHOWNOACTIVATE if visible else win32con.SW_HIDE
        win32gui.ShowWindow(self._hwnd, flag)
        if visible:
            placement = self._placement
            assert placement is not None
            # Re-assert topmost: other always-on-top windows opened since our
            # last show would otherwise sit above us.
            win32gui.SetWindowPos(
                self._hwnd,
                win32con.HWND_TOPMOST,
                placement.x,
                placement.y,
                placement.width,
                placement.height,
                win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW,
            )

    def set_opacity(self, alpha: float) -> None:
        if self._hwnd is None:
            return
        alpha = max(0.0, min(1.0, alpha))
        # Skip redundant calls; this crosses into the window manager and is by
        # far the most expensive thing we would otherwise do every frame.
        if abs(alpha - self._alpha) < 0.004:
            return
        self._alpha = alpha
        win32gui.SetLayeredWindowAttributes(
            self._hwnd, 0, int(alpha * 255), win32con.LWA_ALPHA
        )

    def present(self) -> None:
        pygame.display.flip()

    def destroy(self) -> None:
        self._hwnd = None
        self._surface = None
        pygame.display.quit()
