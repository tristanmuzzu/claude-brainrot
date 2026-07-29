"""Offscreen backend.

Renders to an ordinary surface with no display at all. This is what makes the
scenes testable in CI and what lets ``brainrot shoot`` dump frames to PNG on a
machine with no graphics stack -- generated content is much easier to iterate on
when you can look at frame 300 of run 4712 without waiting for it to appear.
"""

from __future__ import annotations

import os

import pygame

from ..config import Config


class HeadlessBackend:
    def __init__(self) -> None:
        self._surface: pygame.Surface | None = None

    def create(self, cfg: Config) -> pygame.Surface:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.display.init()
        # A real display surface (rather than a bare Surface) keeps pixel
        # formats identical to the on-screen backends, so what CI renders is
        # what Windows renders.
        self._surface = pygame.display.set_mode((cfg.width, cfg.height))
        return self._surface

    @property
    def surface(self) -> pygame.Surface | None:
        return self._surface

    def set_visible(self, visible: bool) -> None:
        pass

    def set_opacity(self, alpha: float) -> None:
        pass

    def present(self) -> None:
        pass

    def destroy(self) -> None:
        self._surface = None
        pygame.display.quit()
