"""Landmark furniture: the pieces a built structure needs to stop being boxes.

``props_deco.py`` dresses platforms; this file dresses the *landmarks*. A
windmill without sails is a plaster silo, a belfry without a bell is a brick
box with a hole, a pumpkin farm without a scarecrow is rows of orange cubes --
each of these is one model that turns a cell blueprint into the thing the
level is named after.

Local axes are the project's: X across, Y along, **Z up**, origin on the
ground -- except ``bell``, which hangs from its origin like ``dripstone``
does, because a bell's cell is the beam it swings under.

* millblades -- four sails on a hub, mounted on a windmill's cap. Origin at
  the hub so the placement says where the axle is, not where the ground was.
* bell       -- a bronze dome with a lip and a yoke, hanging downward.
* scarecrow  -- post, crossbar, straw head on a leaning frame.
* coralfan   -- two crossed fans, recolourable, for the reef garden.
"""

import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)

LEAF = 0.02


def millblades():
    WOOD = zone("wood", (0.42, 0.30, 0.20), rough=0.85)
    SAIL = zone("leaf", (0.86, 0.82, 0.72), rough=0.9)
    parts = [cylinder("hub", 0.16, 0.3, (0, -0.1, 0), WOOD, vertices=8,
                      rot=(math.pi / 2, 0, 0))]
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        dx, dz = math.cos(a), math.sin(a)
        # The arm, then the sail hung off its leading side.
        parts.append(box(f"arm{i}", (0.10, 0.06, 1.9),
                         (dx * 0.85, 0.0, dz * 0.85), WOOD, bevel=0.0,
                         rot=(0, -a, 0)))
        parts.append(box(f"sail{i}", (0.55, LEAF, 1.5),
                         (dx * 1.05, 0.03, dz * 1.05), SAIL, bevel=0.0,
                         rot=(0, -a, 0)))
    return join(parts, "millblades")


def bell():
    BRONZE = zone("metal", (0.78, 0.62, 0.28), rough=0.35)
    DARK = zone("wood", (0.30, 0.22, 0.16), rough=0.9)
    parts = [box("yoke", (0.5, 0.14, 0.12), (0, 0, -0.06), DARK, bevel=0.0)]
    profile = ((0.16, 0.12), (0.22, 0.28), (0.26, 0.24), (0.34, 0.10))
    zoff = -0.12
    for i, (r, h) in enumerate(profile):
        zoff -= h
        parts.append(cylinder(f"b{i}", r, h, (0, 0, zoff), BRONZE,
                              vertices=10))
    parts.append(cylinder("clapper", 0.06, 0.16, (0, 0, zoff - 0.10), DARK,
                          vertices=6))
    return join(parts, "bell")


def scarecrow():
    POST = zone("wood", (0.40, 0.28, 0.18), rough=0.9)
    STRAW = zone("leaf", (0.82, 0.68, 0.28), rough=0.95)
    HEAD = zone("glow", (0.85, 0.48, 0.14), rough=0.7)
    lean = 0.08
    parts = [
        box("post", (0.12, 0.12, 1.7), (0, 0, 0.85), POST, bevel=0.0,
            rot=(lean, 0, 0)),
        box("arms", (1.3, 0.10, 0.10), (0, -0.12, 1.28), POST, bevel=0.0,
            rot=(lean, 0, 0)),
        box("coat", (0.5, 0.16, 0.55), (0, -0.06, 1.05), STRAW, bevel=0.02,
            rot=(lean, 0, 0)),
        box("head", (0.34, 0.30, 0.34), (0, -0.16, 1.62), HEAD, bevel=0.03,
            rot=(lean, 0, 0)),
    ]
    for i, (dx, dz) in enumerate(((-0.55, 1.24), (0.55, 1.22))):
        parts.append(box(f"straw{i}", (0.18, LEAF, 0.22), (dx, -0.14, dz),
                         STRAW, bevel=0.0, rot=(0, 0.4 * (1 - 2 * (i % 2)),
                                                0)))
    return join(parts, "scarecrow")


def coralfan():
    FAN = zone("leaf", (0.86, 0.32, 0.38), rough=0.8)
    parts = []
    for i, rot in enumerate((0.35, math.pi / 2 + 0.35)):
        parts.append(box(f"fan{i}", (0.72, LEAF, 0.62),
                         (0, 0, 0.34), FAN, bevel=0.0, rot=(0.35, 0, rot)))
    parts.append(cylinder("foot", 0.07, 0.12, (0, 0, 0.02), FAN, vertices=6))
    return join(parts, "coralfan")


for name, builder, res in (
    ("millblades", millblades, 128),
    ("bell", bell, 128),
    ("scarecrow", scarecrow, 128),
    ("coralfan", coralfan, 128),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
