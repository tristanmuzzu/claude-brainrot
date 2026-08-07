"""Trackside furniture: obstacles the runner dodges plus dressing that sells
the corridor. Exported as individual GLBs.

* barrier   -- waist-high hurdle to jump (stripes = hazard zone)
* gantry    -- overhead sign bridge to roll under (sign = accent zone)
* fence     -- tileable lineside fence panel
* pillar    -- elevated-line support column
* coin      -- squat gold disc, additive glow added at runtime
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)


def barrier():
    """A hurdle that cannot be mistaken for a bench: alternating hazard
    stripes on the beam, a thin mid-bar, splayed legs."""
    STRIPE = zone("stripe", (0.95, 0.55, 0.08), rough=0.5)
    WHITE = zone("white", (0.93, 0.93, 0.95), rough=0.5)
    DARK = zone("dark", (0.12, 0.12, 0.13), rough=0.8)
    parts = []
    segs = 6
    seg_w = 1.9 / segs
    for i in range(segs):
        x = -1.9 / 2 + (i + 0.5) * seg_w
        parts.append(box(f"seg{i}", (seg_w, 0.26, 0.34), (x, 0, 0.92),
                         STRIPE if i % 2 == 0 else WHITE, 0.02))
    parts.append(box("midbar", (1.9, 0.2, 0.12), (0, 0, 0.5), DARK, 0.02))
    for side in (-1, 1):
        parts.append(box(f"leg{side}", (0.16, 0.3, 1.06), (side * 0.86, 0, 0.53), DARK, 0.03))
        parts.append(box(f"foot{side}", (0.34, 0.4, 0.08), (side * 0.86, 0, 0.04), DARK, 0.02))
    return join(parts, "barrier")


def gantry():
    STEEL = zone("dark", (0.16, 0.17, 0.19), rough=0.7)
    SIGN = zone("sign", (0.10, 0.55, 0.35), rough=0.4)
    parts = [box("beam", (8.4, 0.5, 0.55), (0, 0, 2.6), STEEL, 0.05),
             box("signface", (2.6, 0.12, 1.1), (0, -0.28, 2.55), SIGN, 0.03)]
    for side in (-1, 1):
        parts.append(box(f"post{side}", (0.3, 0.3, 2.9), (side * 4.0, 0, 1.45), STEEL, 0.04))
    return join(parts, "gantry")


def fence():
    """3 m tileable panel, origin at centre, runs along X."""
    POST = zone("dark", (0.14, 0.14, 0.16), rough=0.8)
    MESH = zone("mesh", (0.35, 0.37, 0.40), rough=0.7)
    parts = [box("panel", (3.0, 0.06, 1.5), (0, 0, 1.05), MESH, 0.0),
             box("rail_top", (3.0, 0.1, 0.09), (0, 0, 1.85), POST, 0.02)]
    for x in (-1.5, 0.0, 1.5):
        parts.append(box(f"post{x:.0f}", (0.12, 0.12, 1.9), (x, 0, 0.95), POST, 0.02))
    return join(parts, "fence")


def pillar():
    CONC = zone("wall", (0.40, 0.40, 0.43), rough=0.9)
    parts = [box("shaft", (0.9, 0.9, 5.2), (0, 0, 2.6), CONC, 0.08),
             box("cap", (1.6, 1.6, 0.5), (0, 0, 5.45), CONC, 0.06),
             box("foot", (1.4, 1.4, 0.4), (0, 0, 0.2), CONC, 0.06)]
    return join(parts, "pillar")


def coin():
    GOLD = zone("gold", (1.0, 0.78, 0.15), rough=0.25)
    GOLD_RIM = zone("gold_rim", (0.85, 0.60, 0.05), rough=0.3)
    parts = [
        cylinder("disc", 0.42, 0.1, (0, 0, 0), GOLD, rot=(math.radians(90), 0, 0), vertices=20),
        cylinder("rim", 0.42, 0.16, (0, 0, 0), GOLD_RIM, rot=(math.radians(90), 0, 0), vertices=20),
        cylinder("core", 0.30, 0.12, (0, 0, 0), GOLD, rot=(math.radians(90), 0, 0), vertices=16),
    ]
    # rim is a thin torus stand-in: slightly larger disc behind a smaller one
    parts[1].scale = (1.0, 1.0, 0.9)
    return join(parts, "coin")


for name, builder, res in (
    ("barrier", barrier, 256),
    ("gantry", gantry, 256),
    ("fence", fence, 256),
    ("pillar", pillar, 256),
    ("coin", coin, 128),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
