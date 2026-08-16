"""Power-ups: the pickups you run into, and the jetpack you then wear.

Four small models, and they exist because the first version of the power-ups
drew a coloured cube with a white wireframe round it and called the difference
between them the colour. Three seconds of the most eventful thing in the scene
should not be announced by a box.

* ``pickup_jet``    -- a little jetpack: twin tanks, harness yoke, two nozzles
* ``pickup_boots``  -- a winged boot, because that is what the move is
* ``pickup_magnet`` -- a horseshoe magnet with red and steel poles
* ``jetpack``       -- the pack the body actually wears while flying, built at
                       body scale and hung off the back

The pickups are built to a common radius so the scene can spin them all about
their own centres and glow them all at one size: whatever they are, they read
as "the bright thing standing in the lane" from the far end of the fog, and
only resolve into an object as they arrive. That is the order the real game
does it in too.

The jetpack is separate from ``pickup_jet`` rather than the same model scaled,
because a pickup is seen from the front at two metres and a worn pack is seen
from behind at one: the pickup can afford a yoke and shoulder straps that
would be inside the runner's back, and the worn one needs nozzles that point
somewhere the flame can come out of.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)

#: Every pickup is modelled inside this radius, so one glow size and one spin
#: suit all three and the scene needs no per-power table of magic numbers.
PICKUP_R = 0.46


def _tank(name, x, material, length=0.62, radius=0.15):
    return cylinder(name, radius, length, (x, 0, 0), material,
                    rot=(0, 0, 0), vertices=14)


def pickup_jet():
    """Twin tanks in a yoke, nozzles down, a hazard band round each tank."""
    SHELL = zone("shell", (0.93, 0.42, 0.10), rough=0.35)
    BAND = zone("white", (0.95, 0.95, 0.97), rough=0.4)
    METAL = zone("metal", (0.42, 0.44, 0.50), rough=0.35)
    DARK = zone("dark", (0.13, 0.13, 0.15), rough=0.7)
    parts = []
    for side in (-1, 1):
        x = side * 0.17
        parts.append(_tank(f"tank{side}", x, SHELL))
        parts.append(cylinder(f"band{side}", 0.158, 0.12, (x, 0, 0.06), BAND,
                              vertices=14))
        parts.append(cylinder(f"cap{side}", 0.13, 0.06, (x, 0, 0.34), METAL,
                              vertices=14))
        # nozzle: a short cone-ish stack, wider at the mouth
        parts.append(cylinder(f"noz{side}", 0.09, 0.12, (x, 0, -0.36), DARK,
                              vertices=12))
        parts.append(cylinder(f"mouth{side}", 0.13, 0.06, (x, 0, -0.44), DARK,
                              vertices=12))
    parts.append(box("yoke", (0.42, 0.16, 0.12), (0, 0, 0.20), METAL, 0.04))
    parts.append(box("strap", (0.10, 0.20, 0.34), (0, -0.12, 0.02), DARK, 0.03))
    return join(parts, "pickup_jet")


def pickup_boots():
    """A winged boot: sole, upper, cuff, and a pair of swept wings.

    Wings out of boxes rather than a swept surface -- three tapering slabs a
    side reads as a wing at the size this is ever seen, and costs a dozen
    triangles instead of a few hundred.
    """
    UPPER = zone("shell", (0.16, 0.62, 0.86), rough=0.4)
    SOLE = zone("dark", (0.12, 0.13, 0.16), rough=0.8)
    CUFF = zone("white", (0.94, 0.96, 0.98), rough=0.45)
    WING = zone("wing", (0.86, 0.94, 1.0), rough=0.25)
    parts = [
        box("foot", (0.46, 0.24, 0.16), (0.02, 0, -0.20), UPPER, 0.05),
        box("toe", (0.18, 0.22, 0.13), (0.20, 0, -0.22), UPPER, 0.05),
        box("sole", (0.50, 0.26, 0.07), (0.02, 0, -0.30), SOLE, 0.03),
        box("heel", (0.14, 0.24, 0.10), (-0.18, 0, -0.30), SOLE, 0.03),
        box("shaft", (0.24, 0.24, 0.30), (-0.06, 0, -0.02), UPPER, 0.05),
        box("cuff", (0.28, 0.28, 0.09), (-0.06, 0, 0.14), CUFF, 0.03),
    ]
    for side in (-1, 1):
        y = side * 0.14
        for i, (w, h, dx, dz) in enumerate(((0.26, 0.09, -0.16, 0.10),
                                            (0.20, 0.08, -0.24, 0.19),
                                            (0.13, 0.07, -0.30, 0.27))):
            parts.append(box(f"wing{side}{i}", (w, 0.05, h),
                             (dx, y + side * 0.03 * i, dz), WING, 0.02))
    return join(parts, "pickup_boots")


def pickup_magnet():
    """A horseshoe magnet: two poles, a yoke, red and steel tips.

    The shape everyone reads instantly, which is the whole job. The arch is
    four boxes rather than a bent tube for the same reason the wings are
    slabs: at the size this is seen the silhouette is all there is.
    """
    BODY = zone("shell", (0.86, 0.16, 0.30), rough=0.4)
    TIP = zone("metal", (0.78, 0.80, 0.86), rough=0.25)
    parts = [
        box("legL", (0.15, 0.20, 0.44), (-0.17, 0, -0.06), BODY, 0.04),
        box("legR", (0.15, 0.20, 0.44), (+0.17, 0, -0.06), BODY, 0.04),
        box("yoke", (0.49, 0.20, 0.15), (0, 0, 0.20), BODY, 0.05),
        box("tipL", (0.15, 0.21, 0.13), (-0.17, 0, -0.33), TIP, 0.03),
        box("tipR", (0.15, 0.21, 0.13), (+0.17, 0, -0.33), TIP, 0.03),
    ]
    return join(parts, "pickup_magnet")


def jetpack():
    """The pack the runner wears: worn scale, nozzles pointing down.

    Modelled about its own origin with ``-Z`` at the nozzle mouths, so the
    scene can hang it off the spine and put a flame at a fixed offset without
    measuring anything at draw time.
    """
    SHELL = zone("shell", (0.93, 0.42, 0.10), rough=0.35)
    BAND = zone("white", (0.95, 0.95, 0.97), rough=0.4)
    METAL = zone("metal", (0.42, 0.44, 0.50), rough=0.35)
    DARK = zone("dark", (0.13, 0.13, 0.15), rough=0.7)
    parts = [box("back", (0.34, 0.14, 0.40), (0, 0.02, 0.04), METAL, 0.04)]
    for side in (-1, 1):
        x = side * 0.16
        parts.append(cylinder(f"tank{side}", 0.115, 0.50, (x, -0.06, 0.04),
                              SHELL, vertices=14))
        parts.append(cylinder(f"band{side}", 0.122, 0.09, (x, -0.06, 0.10),
                              BAND, vertices=14))
        parts.append(cylinder(f"noz{side}", 0.075, 0.12, (x, -0.06, -0.26),
                              DARK, vertices=12))
        parts.append(cylinder(f"mouth{side}", 0.105, 0.05, (x, -0.06, -0.33),
                              DARK, vertices=12))
    return join(parts, "jetpack")


def flame():
    """The exhaust plume, as a stack of tapering discs pointing ``-Z``.

    A model rather than a billboard, because two of them have to sit at fixed
    points on a pack that tips with the body -- a camera-facing sprite pinned
    to a moving nozzle slides off it the moment the body leans. The colour
    runs white-hot at the throat to orange at the tip; the scene scales the
    whole thing per frame to make it flicker.
    """
    CORE = zone("glow", (1.0, 0.96, 0.80), rough=0.1)
    MID = zone("flame", (1.0, 0.66, 0.16), rough=0.1)
    TIP = zone("tip", (0.95, 0.30, 0.06), rough=0.1)
    parts = []
    for i, (r, z, mat) in enumerate(((0.085, -0.02, CORE),
                                     (0.070, -0.11, CORE),
                                     (0.056, -0.19, MID),
                                     (0.040, -0.26, MID),
                                     (0.024, -0.32, TIP))):
        parts.append(cylinder(f"seg{i}", r, 0.10, (0, 0, z), mat, vertices=10))
    return join(parts, "flame")


for name, builder, res in (
    ("pickup_jet", pickup_jet, 128),
    ("pickup_boots", pickup_boots, 128),
    ("pickup_magnet", pickup_magnet, 128),
    ("jetpack", jetpack, 128),
    ("flame", flame, 64),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
