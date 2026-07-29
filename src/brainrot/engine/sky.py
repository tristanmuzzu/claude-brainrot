"""Atmospheric sky.

A two-stop linear gradient is the tell of a programmer-art background. Real
skies are darker at the zenith, brighter and warmer toward the horizon, have a
light source that actually sits somewhere, and have cloud structure at more than
one scale.

All of it is built once when the scene is constructed and then blitted, so a
much better sky costs the same per frame as the flat one did.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pygame

from ..palette import RGB, Palette, lerp_rgb
from .noise import fbm

#: Sun tint and glow radius (as a fraction of height) per time of day.
_SUN = {
    "day": ((255, 248, 214), 0.30, 0.16),
    "dawn": ((255, 186, 128), 0.62, 0.62),
    "dusk": ((255, 146, 96), 0.66, 0.70),
    "night": ((206, 220, 255), 0.26, 0.30),
}


def _ramp(palette: Palette, height: int) -> np.ndarray:
    """Vertical colour ramp with a warm horizon band.

    Three anchors instead of two: zenith, mid-sky and horizon. The horizon
    anchor is pushed toward the sun's tint, which is what produces the glow band
    real skies have and flat gradients do not.
    """
    tint, strength, _radius = _SUN[palette.time_of_day]

    zenith = np.array(palette.sky_top, dtype=np.float32) * 0.82
    middle = np.array(palette.sky_top, dtype=np.float32)
    horizon = np.array(palette.sky_bottom, dtype=np.float32)
    horizon = horizon * (1.0 - strength * 0.5) + np.array(tint, dtype=np.float32) * (
        strength * 0.5
    )

    t = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    # Gamma on the upper half keeps the zenith rich rather than fading to grey
    # halfway down.
    upper = zenith[None, :] + (middle - zenith)[None, :] * np.power(t / 0.55, 1.4).clip(0, 1)
    lower_t = ((t - 0.55) / 0.45).clip(0, 1)
    return upper + (horizon - middle)[None, :] * np.power(lower_t, 0.75)


class Sky:
    """A generated sky: gradient, celestial body, stars and scrolling clouds."""

    def __init__(
        self,
        palette: Palette,
        width: int,
        height: int,
        rng: random.Random,
        horizon: float = 0.42,
    ) -> None:
        self.palette = palette
        self.width = width
        self.height = height
        self.horizon_y = int(height * horizon)

        self.sun_x = rng.uniform(0.15, 0.85)
        self.sun_y = {
            "day": rng.uniform(0.06, 0.20),
            "dawn": rng.uniform(0.28, 0.38),
            "dusk": rng.uniform(0.30, 0.40),
            "night": rng.uniform(0.08, 0.24),
        }[palette.time_of_day]

        self.backdrop = self._build_backdrop(rng)
        self.clouds = self._build_clouds(rng)
        self._offsets = [0.0 for _ in self.clouds]

    # -- construction -----------------------------------------------------

    def _build_backdrop(self, rng: random.Random) -> pygame.Surface:
        width, height = self.width, self.height
        tint, strength, radius = _SUN[self.palette.time_of_day]

        ramp = _ramp(self.palette, height)  # (H, 3)
        # surfarray indexes (x, y), so the canvas is built width-major.
        canvas = np.repeat(ramp[None, :, :], width, axis=0).astype(np.float32)

        # Sun/moon glow: an inverse-square-ish falloff around the disc, added
        # rather than blended so it brightens the sky instead of tinting it flat.
        sx, sy = self.sun_x * width, self.sun_y * height
        xs = np.arange(width, dtype=np.float32)[:, None]
        ys = np.arange(height, dtype=np.float32)[None, :]
        dist = np.sqrt((xs - sx) ** 2 + (ys - sy) ** 2) / (height * radius)
        glow = np.exp(-dist * 2.2) * strength * 220.0
        canvas += glow[:, :, None] * (np.array(tint, dtype=np.float32) / 255.0)[None, None, :]

        # The disc itself, with a soft edge so it does not alias into a polygon.
        disc_r = height * (0.030 if self.palette.time_of_day != "night" else 0.026)
        disc = np.clip(1.0 - (dist * height * radius) / disc_r, 0.0, 1.0)
        disc = np.power(disc, 0.35)
        canvas = canvas * (1 - disc[:, :, None]) + np.array(tint, dtype=np.float32)[
            None, None, :
        ] * disc[:, :, None]

        if "stars" in self.palette.particles:
            self._scatter_stars(canvas, rng)

        np.clip(canvas, 0, 255, out=canvas)
        return pygame.surfarray.make_surface(canvas.astype(np.uint8)).convert()

    def _scatter_stars(self, canvas: np.ndarray, rng: random.Random) -> None:
        """Bake stars into the gradient.

        Density falls off toward the horizon, matching how atmosphere actually
        washes them out, and brightness follows a power law so a few are much
        brighter than the rest -- an evenly bright starfield looks like noise.
        """
        width, height = self.width, self.height
        count = int(width * height / 900)
        generator = np.random.default_rng(rng.getrandbits(32))

        xs = generator.integers(0, width, count)
        ys = (generator.power(0.6, count) * self.horizon_y).astype(np.int32)
        brightness = np.power(generator.random(count), 3.0) * 210 + 30
        fade = 1.0 - (ys / max(1, self.horizon_y)) * 0.75

        values = (brightness * fade).clip(0, 255)
        for x, y, v in zip(xs, ys, values):
            canvas[x, y] = np.maximum(canvas[x, y], (v, v, min(255.0, v + 24)))

    def _build_clouds(self, rng: random.Random) -> list[tuple[pygame.Surface, int, float]]:
        """Two cloud bands at different scales, speeds and opacities.

        Each band is twice the strip width and generated with wrapping noise, so
        scrolling it never shows a seam. Parallax between the two sells depth
        far more cheaply than any additional geometry would.
        """
        if self.palette.time_of_day == "night":
            coverage, opacity = 0.62, 0.30
        elif self.palette.weather in ("rain", "snow"):
            coverage, opacity = 0.38, 0.72
        else:
            coverage, opacity = 0.58, 0.52

        bands: list[tuple[pygame.Surface, int, float]] = []
        specs = (
            # (height fraction, y fraction, octaves, base, speed, alpha scale)
            (0.30, 0.02, 5, 3, 3.5, 1.0),
            (0.18, 0.24, 4, 5, 8.0, 0.72),
        )
        base_tint = lerp_rgb(self.palette.fog, (255, 255, 255), 0.45)
        lit = lerp_rgb(base_tint, _SUN[self.palette.time_of_day][0], 0.35)

        for h_frac, y_frac, octaves, base, speed, alpha_scale in specs:
            band_h = max(8, int(self.height * h_frac))
            band_w = self.width * 2
            field = fbm(band_h, band_w, rng, octaves=octaves, base=base, wrap=True)

            # Threshold into puffs, then feather the edge. A hard cut looks like
            # a paper cutout; a soft ramp reads as cloud.
            alpha = np.clip((field - coverage) / max(1e-6, 1.0 - coverage), 0.0, 1.0)
            alpha = np.power(alpha, 1.6)

            # Fade both the top and bottom of the band so it has no straight edge.
            rows = np.linspace(0.0, 1.0, band_h, dtype=np.float32)[:, None]
            # sin(pi) lands a hair below zero in float32, and a negative base to
            # a fractional power is NaN -- which propagates all the way to a
            # corrupt uint8 cast. Clamp before the power.
            alpha *= np.clip(np.sin(rows * math.pi), 0.0, 1.0) ** 0.6

            # Shade by vertical position within the puff: lit on top, grey below.
            shade = np.clip(field * 1.4 - 0.2, 0.0, 1.0)[:, :, None]
            rgb = (
                np.array(base_tint, dtype=np.float32)[None, None, :] * (1 - shade)
                + np.array(lit, dtype=np.float32)[None, None, :] * shade
            )

            rgba = np.dstack([rgb, (alpha * 255 * opacity * alpha_scale)[:, :, None]])
            # (H, W, 4) -> (W, H, 4) for surfarray's column-major indexing.
            surface = pygame.image.frombytes(
                np.ascontiguousarray(rgba.clip(0, 255).astype(np.uint8)).tobytes(),
                (band_w, band_h),
                "RGBA",
            ).convert_alpha()

            bands.append((surface, int(self.height * y_frac), speed))
        return bands

    # -- rendering --------------------------------------------------------

    def update(self, dt: float, wind: float = 1.0) -> None:
        for i, (_surface, _y, speed) in enumerate(self.clouds):
            self._offsets[i] = (self._offsets[i] + speed * wind * dt) % self.width

    def draw(self, surface: pygame.Surface, parallax: float = 0.0) -> None:
        surface.blit(self.backdrop, (0, 0))
        for (band, y, speed), offset in zip(self.clouds, self._offsets):
            # Bands are 2x wide, so one extra blit covers the wrap.
            x = -((offset + parallax * speed * 0.06) % self.width)
            surface.blit(band, (x, y))
            surface.blit(band, (x + self.width, y))

    def sun_screen_pos(self) -> tuple[int, int]:
        return int(self.sun_x * self.width), int(self.sun_y * self.height)
