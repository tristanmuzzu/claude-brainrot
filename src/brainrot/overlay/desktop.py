"""Plain-window backend for development and for non-Windows desktops.

No click-through and no focus suppression -- SDL cannot do either portably --
so this is a normal, movable window. It exists so the engine and every scene
can be developed and watched on Linux or macOS without touching the win32 path.
"""

from __future__ import annotations

import os

import pygame

from ..config import Config
from .base import Placement, compute_placement


class DesktopBackend:
    def __init__(self) -> None:
        self._surface: pygame.Surface | None = None
        self._placement: Placement | None = None
        self._visible = False

    def create(self, cfg: Config) -> pygame.Surface:
        placement = compute_placement(cfg)
        self._placement = placement
        os.environ.setdefault("SDL_VIDEO_WINDOW_POS", f"{placement.x},{placement.y}")

        pygame.display.init()
        self._surface = pygame.display.set_mode((placement.width, placement.height))
        pygame.display.set_caption("claude-brainrot")
        return self._surface

    def set_visible(self, visible: bool) -> None:
        # Iconifying on every hide would be obnoxious to develop against and
        # some window managers refuse to restore without user input, so the
        # window stays put and simply renders nothing while hidden.
        self._visible = visible

    def set_opacity(self, alpha: float) -> None:
        try:
            pygame.display.get_window().opacity = alpha
        except (AttributeError, pygame.error):
            pass

    def present(self) -> None:
        pygame.display.flip()

    def destroy(self) -> None:
        self._surface = None
        pygame.display.quit()
