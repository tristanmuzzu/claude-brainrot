"""Procedural visual themes.

Every run generates its own palette, time of day and weather, so two runs never
look alike even when the same scene plays twice in a row. Hue selection uses the
golden-ratio sequence rather than uniform random choice -- see
:func:`brainrot.rng.golden_sequence` for why.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass, field
from functools import lru_cache

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


@lru_cache(maxsize=16384)
def shade(color: RGB, factor: float) -> RGB:
    """Scale brightness, clamped. ``factor`` above 1 lightens.

    Cached because the voxel renderer calls this for every texel on every face
    of every block, every frame -- profiling showed it as the single hottest
    line in the scene, almost entirely on repeat arguments.
    """
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
    accent2: RGB
    train: RGB
    window_lit: RGB
    hazard: RGB
    ink: RGB
    ambient: float
    #: Block-face colour families for the parkour course, brightest first.
    blocks: list[RGB] = field(default_factory=list)
    particles: list[str] = field(default_factory=list)

    @property
    def is_dark(self) -> bool:
        return luminance(self.sky_bottom) < 0.45


def _band(hue01: float, lo: float, hi: float) -> float:
    """Map a 0..1 hue onto the band [lo, hi] -- variety inside taste.

    The golden-sequence hue guarantees consecutive runs differ; the band
    guarantees a *sky* never lands on olive or lime. Accents keep the whole
    wheel; skies do not want it.
    """
    return lo + (hue01 % 1.0) * (hi - lo)


def generate(seed: Seed) -> Palette:
    """Build the palette for a run."""
    rng = seed.stream("palette")

    # Hue comes from the run number, not the RNG, so consecutive runs are
    # guaranteed to be far apart on the colour wheel.
    base_hue = golden_sequence(seed.run)
    time_of_day = _weighted(rng, _TIMES)
    weather = _weighted(rng, _WEATHER)

    # Skies are two-hue gradients confined to bands that photograph well;
    # the reference material is saturated and punchy, never muddy.
    if time_of_day == "day":
        top_h = _band(base_hue, 0.55, 0.64)          # azure..cerulean
        sky_top = hsv(top_h, 0.72, 0.92)
        sky_bottom = hsv(top_h - 0.045, 0.30, 1.0)   # bright milky horizon
        ambient = 0.95
    elif time_of_day == "dawn":
        sky_top = hsv(_band(base_hue, 0.58, 0.72), 0.45, 0.82)   # cool upper sky
        sky_bottom = hsv(_band(base_hue, 0.04, 0.10), 0.70, 1.0)  # gold horizon
        ambient = 0.78
    elif time_of_day == "dusk":
        sky_top = hsv(_band(base_hue, 0.72, 0.85), 0.62, 0.62)   # violet..magenta
        sky_bottom = hsv(_band(base_hue, 0.985, 1.06), 0.78, 0.98)  # hot pink..orange
        ambient = 0.66
    else:  # night
        top_h = _band(base_hue, 0.60, 0.70)
        sky_top = hsv(top_h, 0.70, 0.16)
        sky_bottom = hsv(top_h - 0.03, 0.52, 0.34)
        ambient = 0.34

    fog = lerp_rgb(sky_bottom, (255, 255, 255), 0.10 if time_of_day != "night" else 0.0)

    # Accents keep the full wheel and full punch. accent2 sits a third away so
    # outfit combinations read as designed rather than random.
    accent = hsv(base_hue + 0.5 + rng.uniform(-0.06, 0.06), 0.88, 0.98)
    accent2 = hsv(base_hue + 0.5 + 0.33 + rng.uniform(-0.05, 0.05), 0.80, 0.92)
    train = hsv(base_hue + rng.uniform(0.42, 0.58), 0.72, 0.80)
    # Hazards must never be mistaken for scenery: pinned to red-orange.
    hazard = hsv(rng.uniform(-0.02, 0.05), 0.90, 0.98)
    window_lit = hsv(0.115 + rng.uniform(-0.02, 0.02), 0.55, 1.0)

    # Ground and structures deliberately do NOT share the sky's hue. Deriving
    # everything from one hue makes the whole frame collapse into a single
    # colour wash -- real scenes have a tinted sky over near-neutral ground, and
    # the contrast between them is most of what reads as depth.
    ground_hue = base_hue + 0.5 + rng.uniform(-0.06, 0.06)
    ground_v = {"day": 0.42, "dawn": 0.36, "dusk": 0.30, "night": 0.16}[time_of_day]
    ground = hsv(ground_hue, 0.16, ground_v)
    ground_alt = shade(ground, 1.35)
    structure = hsv(base_hue + rng.uniform(0.1, 0.2), 0.18,
                    {"day": 0.62, "dawn": 0.52, "dusk": 0.44, "night": 0.24}[time_of_day])

    # Parkour block families: candy-bright, distinct, ordered.
    block_hues = [accent, accent2, hsv(base_hue + rng.uniform(0.16, 0.24), 0.75, 0.95)]
    rng.shuffle(block_hues)

    # Ink sits in the top corners, against the UPPER sky and the skyline --
    # judge readability against sky_top, not the bright horizon.
    ink = (248, 248, 252) if luminance(sky_top) < 0.6 else (24, 24, 30)

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
        accent2=accent2,
        train=train,
        window_lit=window_lit,
        hazard=hazard,
        ink=ink,
        ambient=ambient,
        blocks=block_hues,
        particles=particles,
    )
