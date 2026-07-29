"""Value noise and fractal Brownian motion.

Used at scene-construction time to generate textures, cloud layers and terrain
detail. Nothing in here runs per frame -- the outputs are baked into Surfaces
once and then blitted, so this module can afford to be straightforward rather
than clever.

All generators take an explicit :class:`random.Random` so noise is part of the
run's seeded, replayable output rather than an independent source of entropy.
"""

from __future__ import annotations

import random

import numpy as np


def _smoothstep(t: np.ndarray) -> np.ndarray:
    """Hermite fade. Without it, value noise shows its grid as visible creases."""
    return t * t * (3.0 - 2.0 * t)


def _upscale(grid: np.ndarray, height: int, width: int, wrap: bool = False) -> np.ndarray:
    """Bilinear resample with a smoothstep fade.

    ``wrap`` makes the result tile horizontally, which is what lets a cloud
    band scroll forever without a seam.
    """
    gh, gw = grid.shape
    ys = np.linspace(0, gh - 1, height)
    xs = np.linspace(0, gw if wrap else gw - 1, width, endpoint=False if wrap else True)

    y0 = np.floor(ys).astype(np.int32)
    x0 = np.floor(xs).astype(np.int32)
    fy = _smoothstep(ys - y0)[:, None]
    fx = _smoothstep(xs - x0)[None, :]

    y1 = np.minimum(y0 + 1, gh - 1)
    if wrap:
        x0 = x0 % gw
        x1 = (x0 + 1) % gw
    else:
        x1 = np.minimum(x0 + 1, gw - 1)

    top = grid[np.ix_(y0, x0)] * (1 - fx) + grid[np.ix_(y0, x1)] * fx
    bottom = grid[np.ix_(y1, x0)] * (1 - fx) + grid[np.ix_(y1, x1)] * fx
    return top * (1 - fy) + bottom * fy


def fbm(
    height: int,
    width: int,
    rng: random.Random,
    octaves: int = 5,
    base: int = 4,
    persistence: float = 0.5,
    wrap: bool = False,
) -> np.ndarray:
    """Fractal Brownian motion in ``[0, 1]``.

    Summed octaves of value noise at doubling frequency and halving amplitude --
    the standard recipe, and the reason generated clouds and stone read as
    natural rather than as a blur.
    """
    seed = rng.getrandbits(32)
    generator = np.random.default_rng(seed)

    total = np.zeros((height, width), dtype=np.float32)
    amplitude = 1.0
    norm = 0.0
    frequency = base

    for _ in range(octaves):
        grid = generator.random((max(2, frequency), max(2, frequency))).astype(np.float32)
        total += _upscale(grid, height, width, wrap=wrap) * amplitude
        norm += amplitude
        amplitude *= persistence
        frequency *= 2

    total /= max(norm, 1e-6)
    # Renormalise: summing octaves compresses the range toward the middle, and
    # an unstretched result looks washed out once it reaches a colour ramp.
    low, high = float(total.min()), float(total.max())
    if high - low > 1e-6:
        total = (total - low) / (high - low)
    return total


def turbulence(
    height: int, width: int, rng: random.Random, octaves: int = 5, base: int = 4
) -> np.ndarray:
    """Absolute-valued fbm. The creases it produces are what make marble veins."""
    field = fbm(height, width, rng, octaves=octaves, base=base)
    return np.abs(field * 2.0 - 1.0)


def ridged(height: int, width: int, rng: random.Random, octaves: int = 5, base: int = 4) -> np.ndarray:
    """Inverted turbulence -- sharp ridges, useful for rock and cloud edges."""
    return 1.0 - turbulence(height, width, rng, octaves=octaves, base=base)
