"""Shared drawing helpers.

Anything more than one scene needs, plus the weather particles that sell a
generated palette as a *place* rather than a colour scheme.
"""

from __future__ import annotations

import math
import random

import pygame

from ..palette import RGB, Palette, lerp_rgb, luminance

_font_cache: dict[tuple[str, int, bool], pygame.font.Font] = {}
_gradient_cache: dict[tuple[int, int, RGB, RGB], pygame.Surface] = {}


def reset_caches() -> None:
    """Drop cached Fonts and Surfaces.

    Both are tied to an initialised SDL: a ``Font`` created before
    ``pygame.quit()`` raises "font module quit since font created" when reused
    afterwards, and converted Surfaces are bound to the display that made them.
    The run loop calls this on startup and shutdown so a restarted daemon in the
    same process starts from clean state.
    """
    _font_cache.clear()
    _gradient_cache.clear()


def font(size: int, bold: bool = False, name: str = "") -> pygame.font.Font:
    key = (name, size, bold)
    cached = _font_cache.get(key)
    if cached is None:
        if not pygame.font.get_init():
            pygame.font.init()
        cached = pygame.font.SysFont(name or "arialrounded,arial,dejavusans", size, bold=bold)
        _font_cache[key] = cached
    return cached


def vertical_gradient(width: int, height: int, top: RGB, bottom: RGB) -> pygame.Surface:
    """Cached vertical gradient.

    Built once per (size, colour pair) and blitted thereafter. Regenerating a
    640-row gradient every frame is pure waste in a process whose entire reason
    to exist is *not* competing with Claude for CPU.
    """
    key = (width, height, top, bottom)
    cached = _gradient_cache.get(key)
    if cached is not None:
        return cached

    # Render one pixel per row, then let SDL do the stretch in C.
    strip = pygame.Surface((1, height)).convert()
    for y in range(height):
        strip.set_at((0, y), lerp_rgb(top, bottom, y / max(1, height - 1)))
    surface = pygame.transform.smoothscale(strip, (width, height)).convert()

    # Unbounded growth is not a real risk (palettes are per-run) but a stuck
    # daemon running for weeks would otherwise accumulate one entry per run.
    if len(_gradient_cache) > 12:
        _gradient_cache.clear()
    _gradient_cache[key] = surface
    return surface


def text(
    surface: pygame.Surface,
    value: str,
    x: int,
    y: int,
    size: int = 18,
    color: RGB = (255, 255, 255),
    bold: bool = True,
    anchor: str = "topleft",
    outline: bool = True,
) -> pygame.Rect:
    """Draw text with a contrast outline so it survives any background."""
    glyphs = font(size, bold)
    body = glyphs.render(value, True, color)
    rect = body.get_rect(**{anchor: (x, y)})

    if outline:
        # Outline colour is picked against the text, not the background, which
        # we do not know -- dark text gets a light halo and vice versa.
        halo = (12, 12, 16) if luminance(color) > 0.5 else (240, 240, 245)
        shadow = glyphs.render(value, True, halo)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
            surface.blit(shadow, rect.move(dx, dy))

    surface.blit(body, rect)
    return rect


def rounded_rect(
    surface: pygame.Surface, rect: pygame.Rect, color: RGB, radius: int = 6
) -> None:
    if rect.width <= 0 or rect.height <= 0:
        return
    pygame.draw.rect(surface, color, rect, border_radius=max(0, min(radius, rect.height // 2)))


def vignette(surface: pygame.Surface, strength: float = 0.35) -> None:
    """Darken the edges.

    Pulls the eye to the centre of a tall narrow strip, and softens the hard
    boundary where the overlay meets the desktop behind it.
    """
    if strength <= 0:
        return
    width, height = surface.get_size()
    band = max(8, height // 10)
    shade = pygame.Surface((width, band), pygame.SRCALPHA)
    for i in range(band):
        alpha = int(255 * strength * (1.0 - i / band))
        pygame.draw.line(shade, (0, 0, 0, alpha), (0, i), (width, i))
    surface.blit(shade, (0, 0))
    surface.blit(pygame.transform.flip(shade, False, True), (0, height - band))


class Particles:
    """Weather overlay driven by the run's palette.

    Rain, snow and stars share one system because they differ only in velocity,
    size and whether they wrap or twinkle.
    """

    def __init__(self, palette: Palette, width: int, height: int, rng: random.Random) -> None:
        self.palette = palette
        self.width = width
        self.height = height
        self.rng = rng
        self.kinds = list(palette.particles)
        self.items: list[list[float]] = []
        self._spawn()

    def _spawn(self) -> None:
        counts = {"rain": 90, "snow": 70, "stars": 60}
        for kind in self.kinds:
            for _ in range(counts.get(kind, 40)):
                self.items.append(
                    [
                        float(self.kinds.index(kind)),
                        self.rng.uniform(0, self.width),
                        self.rng.uniform(0, self.height),
                        self.rng.uniform(0.5, 1.5),  # depth factor
                        self.rng.uniform(0, math.tau),  # phase, for twinkle
                    ]
                )

    def update(self, dt: float) -> None:
        for item in self.items:
            kind = self.kinds[int(item[0])]
            if kind == "stars":
                item[4] += dt * 2.0
                continue
            speed = (620.0 if kind == "rain" else 70.0) * item[3]
            item[2] += speed * dt
            if kind == "snow":
                item[1] += math.sin(item[4] + item[2] * 0.02) * 22.0 * dt
            if item[2] > self.height:
                item[2] = -10.0
                item[1] = self.rng.uniform(0, self.width)

    def draw(self, surface: pygame.Surface) -> None:
        for item in self.items:
            kind = self.kinds[int(item[0])]
            x, y, depth = item[1], item[2], item[3]
            if kind == "rain":
                length = 9.0 * depth
                pygame.draw.line(
                    surface,
                    lerp_rgb(self.palette.fog, (255, 255, 255), 0.4),
                    (x, y),
                    (x - 1.5, y + length),
                    1,
                )
            elif kind == "snow":
                pygame.draw.circle(surface, (238, 242, 250), (int(x), int(y)), max(1, int(depth * 1.6)))
            else:  # stars -- fixed position, only brightness moves
                twinkle = 0.55 + 0.45 * math.sin(item[4])
                # depth runs to 1.5, so the product must be clamped rather than
                # trusted: an unclamped 200*1.5 overflows the channel.
                value = min(255, int(200 * twinkle * depth))
                surface.set_at(
                    (int(x) % self.width, int(y) % max(1, self.height // 2)),
                    (value, value, min(255, value + 30)),
                )

    def __len__(self) -> int:
        return len(self.items)
