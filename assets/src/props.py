"""Trackside furniture: obstacles the runner dodges plus dressing that sells
the corridor. Exported as individual GLBs.

* barrier   -- waist-high hurdle to jump (stripes = hazard zone)
* gantry    -- overhead sign bridge, high enough to run under: pure dressing
* hoarding  -- low advertising bridge; its underside is genuinely below head
               height, so it is the obstacle that has to be rolled under
* ramp      -- sloped launcher onto a train roof (stripes = hazard zone)
* fence     -- tileable lineside fence panel
* pillar    -- elevated-line support column
* coin      -- squat gold disc, additive glow added at runtime

Heights here are load-bearing: ``assets/measure.py`` records them and the
runner plans jumps and rolls against the recorded numbers, so moving a beam
moves the gameplay with it. See ``tests/test_assets.py``.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, wedge, zone,
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


def hoarding():
    """A low advertising bridge across the whole track.

    The one number that matters: the underside of the board sits at 1.55, so
    drawn at railhead height its soffit lands at 1.85 -- under the running
    character's 2.39 head, over the 1.48 of a slide. That gap *is* the reason
    the roll exists, and the asset test asserts it stays true.
    """
    STEEL = zone("dark", (0.16, 0.17, 0.19), rough=0.7)
    BOARD = zone("sign", (0.88, 0.24, 0.30), rough=0.45)
    CREAM = zone("cream", (0.92, 0.90, 0.84), rough=0.5)
    SOFFIT = 1.55
    parts = [
        box("board", (7.4, 0.16, 0.68), (0, 0, SOFFIT + 0.34), BOARD, 0.03),
        box("underbeam", (8.0, 0.34, 0.13), (0, 0, SOFFIT + 0.065), STEEL, 0.03),
        box("topcap", (7.8, 0.3, 0.12), (0, 0, SOFFIT + 0.74), STEEL, 0.03),
    ]
    # a cream band across the board so it reads as signage, not a red slab
    parts.append(box("band", (6.4, 0.06, 0.2), (0, -0.1, SOFFIT + 0.34), CREAM, 0.01))
    for side in (-1, 1):
        parts.append(box(f"post{side}", (0.34, 0.34, SOFFIT + 0.8),
                         (side * 3.9, 0, (SOFFIT + 0.8) / 2), STEEL, 0.04))
        parts.append(box(f"foot{side}", (0.6, 0.6, 0.16), (side * 3.9, 0, 0.08), STEEL, 0.03))
    return join(parts, "hoarding")


def ramp():
    """A launcher onto a train roof: a hazard-striped wedge one lane wide.

    Rises to 1.15 over 3.4 m. The runner does not physically ride the slope --
    touching it commits a scripted launch whose arc is solved against the roof
    height -- but the slope has to look like it could produce that arc.
    """
    STRIPE = zone("stripe", (0.95, 0.55, 0.08), rough=0.5)
    DARK = zone("dark", (0.13, 0.13, 0.15), rough=0.8)
    STEEL = zone("steel", (0.46, 0.48, 0.52), rough=0.4)
    parts = [wedge("slope", 2.0, 3.4, 1.15, (0, 0, 0.0), STRIPE)]
    # side cheeks and a lip so the wedge does not read as a paper triangle
    for side in (-1, 1):
        parts.append(box(f"cheek{side}", (0.12, 3.4, 0.1),
                         (side * 1.0, 0, 0.05), DARK, 0.02))
    parts.append(box("lip", (2.1, 0.18, 0.12), (0, 1.7, 1.12), STEEL, 0.03))
    parts.append(box("kick", (2.1, 0.2, 0.1), (0, -1.7, 0.05), DARK, 0.02))
    return join(parts, "ramp")


def lamp():
    """Lineside lamp post: a mast with a cowled head leaning over the track.

    Trackside furniture is what stops a corridor reading as a corridor. One
    repeated post on a cadence does more for the sense of speed than anything
    in the middle of the track, because it is close to the camera and it is
    what the eye uses to measure how fast the world is moving.
    """
    POST = zone("dark", (0.17, 0.18, 0.21), rough=0.7)
    LAMP = zone("lamp", (1.0, 0.94, 0.68), rough=0.15)
    parts = [
        box("base", (0.34, 0.34, 0.22), (0, 0, 0.11), POST, 0.03),
        box("mast", (0.16, 0.16, 4.2), (0, 0, 2.2), POST, 0.03),
        box("arm", (0.9, 0.13, 0.13), (0.42, 0, 4.22), POST, 0.03),
        box("cowl", (0.62, 0.34, 0.12), (0.78, 0, 4.14), POST, 0.03),
        box("bulb", (0.5, 0.24, 0.09), (0.78, 0, 4.03), LAMP, 0.02),
    ]
    return join(parts, "lamp")


def signal():
    """A three-aspect lineside signal, the other half of the trackside kit."""
    POST = zone("dark", (0.15, 0.16, 0.18), rough=0.75)
    HOOD = zone("steel", (0.36, 0.38, 0.42), rough=0.5)
    RED = zone("stripe", (0.92, 0.18, 0.16), rough=0.3)
    parts = [
        box("base", (0.4, 0.4, 0.18), (0, 0, 0.09), POST, 0.03),
        box("mast", (0.14, 0.14, 2.5), (0, 0, 1.3), POST, 0.03),
        box("head", (0.34, 0.3, 0.95), (0, 0, 2.85), HOOD, 0.05),
        box("ladder", (0.05, 0.22, 1.6), (-0.14, 0, 1.1), HOOD, 0.01),
    ]
    for i, z in enumerate((2.55, 2.85, 3.15)):
        parts.append(box(f"aspect{i}", (0.1, 0.2, 0.2), (0.19, 0, z),
                         RED if i == 0 else HOOD, 0.02))
    return join(parts, "signal")


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
    ("hoarding", hoarding, 256),
    ("ramp", ramp, 256),
    ("lamp", lamp, 256),
    ("signal", signal, 256),
    ("fence", fence, 256),
    ("pillar", pillar, 256),
    ("coin", coin, 128),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
