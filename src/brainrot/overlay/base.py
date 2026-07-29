"""Window backend interface and geometry helpers.

The engine draws to a plain :class:`pygame.Surface` and knows nothing about
windowing. Everything platform-specific -- click-through, always-on-top,
focus suppression, per-window alpha -- lives behind this interface so a new
platform is one file rather than a rewrite.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import pygame

from ..config import Config


@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    width: int
    height: int


def compute_placement(cfg: Config) -> Placement:
    """Dock the strip to the left edge of the configured monitor.

    Falls back to the requested size if the desktop cannot be queried, which is
    what happens under the dummy video driver in tests.
    """
    width, height = cfg.width, cfg.height
    try:
        desktops = pygame.display.get_desktop_sizes()
    except (pygame.error, AttributeError):
        desktops = []

    if not desktops:
        return Placement(cfg.margin_x, 0, width, height)

    index = max(0, min(cfg.monitor, len(desktops) - 1))
    screen_w, screen_h = desktops[index]

    # Never let a misconfigured size exceed the screen.
    height = min(height, screen_h)
    width = min(width, screen_w)

    x = cfg.margin_x
    y = int((screen_h - height) * cfg.anchor_y)

    # Multi-monitor origins are not exposed by pygame, so horizontal offset for
    # non-primary displays is approximated by stacking widths left to right.
    for i in range(index):
        x += desktops[i][0]

    return Placement(x, max(0, y), width, height)


class WindowBackend(Protocol):
    """Lifecycle for the overlay window."""

    def create(self, cfg: Config) -> pygame.Surface:
        """Open the window and return the surface scenes draw onto."""
        ...

    def set_visible(self, visible: bool) -> None:
        ...

    def set_opacity(self, alpha: float) -> None:
        """``alpha`` is 0..1. Backends without alpha support may no-op."""
        ...

    def present(self) -> None:
        """Push the drawn frame to the screen."""
        ...

    def destroy(self) -> None:
        ...


def select_backend(force: str = "") -> "WindowBackend":
    """Pick the best backend for this machine.

    ``force`` accepts ``win32``, ``desktop`` or ``headless`` to override, which
    is how the dev loop runs a normal window on a machine that would otherwise
    get the click-through treatment.
    """
    choice = (force or os.environ.get("BRAINROT_BACKEND") or "").strip().lower()

    if choice == "headless":
        from .headless import HeadlessBackend

        return HeadlessBackend()
    if choice == "desktop":
        from .desktop import DesktopBackend

        return DesktopBackend()
    if choice == "win32":
        from .win32 import Win32Backend

        return Win32Backend()

    if os.name == "nt":
        try:
            from .win32 import Win32Backend

            return Win32Backend()
        except ImportError:
            # pywin32 missing -- a plain window is still better than nothing,
            # it just will not be click-through.
            pass

    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY") and os.name != "nt":
        from .headless import HeadlessBackend

        return HeadlessBackend()

    from .desktop import DesktopBackend

    return DesktopBackend()
