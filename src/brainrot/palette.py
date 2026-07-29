"""Procedural visual themes.

Every run generates its own palette, time of day and weather, so two runs never
look alike even when the same scene plays twice in a row. Hue selection uses the
golden-ratio sequence rather than uniform random choice -- see
:func:`brainrot.rng.golden_sequence` for why.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass, field

from .rng import Seed, golden_sequence

RGB = tuple[int, int, int]


def hsv(h: float, s: float, v: float) -> RGB:
    """HSV (all components 0..1, hue wrapping) to 8-bit RGB."""
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


def lerp_rgb(a: RGB, b: RGB, t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def shade(color: RGB, factor: float) -> RGB:
    """Scale brightness, clamped. ``factor`` above 1 lightens."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)  # type: ignore[return-value]


def luminance(color: RGB) -> float:
    """Perceptual luminance, 0..1. Used to keep text readable on any sky."""
    r, g, b = (c / 255 for c in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# Time of day drives sky, fog and how strongly faces are lit. Weights are
# deliberately uneven: night looks great but is tiring as a default.
_TIMES = (
    ("day", 0.40),
    ("dusk", 0.25),
    ("dawn", 0.20),
    ("night", 0.15),
)

_WEATHER = (
    ("clear", 0.55),
    ("rain", 0.25),
    ("snow", 0.20),
)


def _weighted(rng, options: tuple[tuple[str, float], ...]) -> str:
    roll = rng.random() * sum(w for _, w in options)
    upto = 0.0
    for name, weight in options:
        upto += weight
        if roll <= upto:
            return name
    return options[-1][0]


@dataclass
class Palette:
    """A generated theme. Scenes read from this rather than hardcoding colour."""

    time_of_day: str
    weather: str
    sky_top: RGB
    sky_bottom: RGB
    fog: RGB
    ground: RGB
    ground_alt: RGB
    structure: RGB
    accent: RGB
    hazard: RGB
    ink: RGB
    ambient: float
    particles: list[str] = field(default_factory=list)

    @property
    def is_dark(self) -> bool:
        return luminance(self.sky_bottom) < 0.45

    def face(self, base: RGB, orientation: str) -> RGB:
        """Shade a cube face by orientation.

        Three fixed brightness levels for top/side/front is the oldest trick in
        voxel rendering and still the most legible at small sizes -- it reads as
        solid geometry without any real lighting maths.
        """
        factors = {"top": 1.0, "side": 0.72, "front": 0.86, "bottom": 0.45}
        lit = factors.get(orientation, 1.0)
        # Ambient lifts the darkest faces at night so silhouettes stay readable.
        lit = lit + (1.0 - lit) * (1.0 - self.ambient) * 0.5
        return shade(base, lit)


def generate(seed: Seed) -> Palette:
    """Build the palette for a run."""
    rng = seed.stream("palette")

    # Hue comes from the run number, not the RNG, so consecutive runs are
    # guaranteed to be far apart on the colour wheel.
    base_hue = golden_sequence(seed.run)
    time_of_day = _weighted(rng, _TIMES)
    weather = _weighted(rng, _WEATHER)

    # Value/saturation envelopes per time of day: (sky_v, sky_s, ambient).
    envelope = {
        "day": (0.95, 0.35, 0.95),
        "dawn": (0.80, 0.55, 0.70),
        "dusk": (0.70, 0.65, 0.60),
        "night": (0.28, 0.55, 0.30),
    }[time_of_day]
    sky_v, sky_s, ambient = envelope

    sky_top = hsv(base_hue, sky_s * 0.9, sky_v * 0.75)
    sky_bottom = hsv(base_hue + 0.06, sky_s * 0.5, sky_v)
    fog = lerp_rgb(sky_bottom, (255, 255, 255), 0.15 if time_of_day != "night" else 0.0)

    # Complementary-ish accent, offset far enough to read as a different colour
    # but jittered so it is not mechanically 180 degrees every time.
    accent = hsv(base_hue + 0.5 + rng.uniform(-0.08, 0.08), 0.85, 0.95)
    # Hazards must never be mistaken for scenery, so they are pinned to the
    # red-orange band regardless of the run's hue.
    hazard = hsv(rng.uniform(-0.02, 0.06), 0.85, 0.95)

    ground = hsv(base_hue + rng.uniform(-0.05, 0.05), 0.25, sky_v * 0.45)
    ground_alt = shade(ground, 1.25)
    structure = hsv(base_hue + rng.uniform(0.1, 0.2), 0.30, sky_v * 0.6)

    # Ink is chosen against the sky it will sit on, not fixed white/black.
    ink = (245, 245, 250) if luminance(sky_bottom) < 0.55 else (18, 18, 24)

    particles = []
    if weather == "rain":
        particles = ["rain"]
    elif weather == "snow":
        particles = ["snow"]
    if time_of_day == "night" and rng.random() < 0.7:
        particles.append("stars")

    return Palette(
        time_of_day=time_of_day,
        weather=weather,
        sky_top=sky_top,
        sky_bottom=sky_bottom,
        fog=fog,
        ground=ground,
        ground_alt=ground_alt,
        structure=structure,
        accent=accent,
        hazard=hazard,
        ink=ink,
        ambient=ambient,
        particles=particles,
    )
