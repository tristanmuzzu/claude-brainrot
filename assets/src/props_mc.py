"""Minecraft-ish platform furniture for the spiral scene: the thin things.

Everything else in this project is built out of whole cells, because
everything else in this project is a *building* -- a wall, a floor, a column,
a jump block. The platforms in ``scenes/spiral.py`` are places rather than
architecture, and what makes a farm read as a farm is precisely the parts of
Minecraft that are **not** cubes: wheat and flowers are two intersecting
quads, a fence is a post and two rails, a lantern hangs on a chain, sugar cane
is a stalk a few pixels wide. Drawn as cells those all come out as a scattering
of coloured boxes -- which is what the platforms had, and which reads as
rubble.

Local axes are the project's: X across, Y along, **Z up**, origin on the
ground so a prop can be dropped at a cell's floor without an offset nobody can
see the reason for. The exporter converts to glTF's Y-up.

* crop        -- four crossed blades, the wheat/carrot/nether-wart shape
* flower      -- a crossed pair of petals on a short stem
* mcfence     -- one post and two rails, a metre long, tileable end to end
                 (``mc`` because ``props.py`` already exports a trackside
                 ``fence``, and an asset name is a filename: building this
                 one as ``fence`` silently replaced the runner's)
* lanternpost -- a post with a bracket and a hanging lantern
* sugarcane   -- three stacked crossed segments, tall and thin
* chain       -- a hanging chain, for a lantern under a platform's rim

Zones are named for what the runtime recolours: ``leaf``, ``stem``, ``wood``,
``metal``, ``glow``. A prop that does not carry a zone simply ignores the
colour, which is what ``ModelAsset.recolor`` is for.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)

#: The blade thickness of every crossed quad here. Vanilla draws these as
#: single textured planes with no thickness at all; a plane with no thickness
#: disappears edge-on, and the camera in this scene runs *past* these things
#: at seven metres a second. Two centimetres is invisible as a solid and never
#: vanishes.
LEAF = 0.02


def _cross(name, w, h, z, material, tilt=0.0):
    """Two quads at right angles: the shape every plant in the game is."""
    out = []
    for i, rot in enumerate((0.0, math.pi / 2)):
        out.append(box(f"{name}{i}", (w, LEAF, h), (0, 0, z + h / 2), material,
                       bevel=0.0, rot=(tilt, 0, rot)))
    return out


def crop():
    """Wheat: four blades, the outer pair shorter, on a stubby stem. Grown to
    about three quarters of a block, which is what a ripe crop looks like."""
    LEAFZ = zone("leaf", (0.62, 0.66, 0.20), rough=0.85)
    STEM = zone("stem", (0.45, 0.52, 0.16), rough=0.9)
    parts = _cross("blade", 0.62, 0.72, 0.02, LEAFZ)
    parts += _cross("inner", 0.34, 0.50, 0.0, STEM, tilt=math.radians(6))
    return join(parts, "crop")


def flower():
    """A crossed pair of petals on a stem. Small on purpose -- a flower that
    reads at a distance is a bush."""
    PETAL = zone("leaf", (0.90, 0.33, 0.30), rough=0.6)
    STEM = zone("stem", (0.30, 0.52, 0.22), rough=0.9)
    parts = [box("stem", (0.05, 0.05, 0.34), (0, 0, 0.17), STEM, bevel=0.0)]
    parts += _cross("petal", 0.30, 0.26, 0.30, PETAL)
    return join(parts, "flower")


def mcfence():
    """One metre of fence: a post and two rails, and the rails run the whole
    cell so a line of them meets end to end with no gap."""
    WOOD = zone("wood", (0.48, 0.34, 0.19), rough=0.85)
    parts = [box("post", (0.16, 0.16, 1.0), (0, 0, 0.5), WOOD, 0.01)]
    for z in (0.42, 0.78):
        parts.append(box(f"rail{z:.2f}", (0.08, 1.0, 0.10), (0, 0, z), WOOD,
                         0.01))
    return join(parts, "mcfence")


def lanternpost():
    """A post, a bracket, and a lantern hanging off it. The lantern's own zone
    is ``glow`` so the scene can hang an additive sprite on the same point and
    have the two agree about where the light is."""
    WOOD = zone("wood", (0.36, 0.27, 0.16), rough=0.85)
    METAL = zone("metal", (0.30, 0.30, 0.33), rough=0.6)
    GLOW = zone("glow", (1.0, 0.82, 0.42), rough=0.25)
    parts = [
        box("post", (0.16, 0.16, 1.9), (0, 0, 0.95), WOOD, 0.02),
        box("bracket", (0.08, 0.44, 0.08), (0, 0.22, 1.82), METAL, 0.01),
        box("hook", (0.05, 0.05, 0.16), (0, 0.42, 1.72), METAL, 0.01),
        box("lantern", (0.28, 0.28, 0.32), (0, 0.42, 1.48), GLOW, 0.03),
        box("cap", (0.34, 0.34, 0.06), (0, 0.42, 1.66), METAL, 0.01),
    ]
    return join(parts, "lanternpost")


def sugarcane():
    """Three crossed segments stacked: tall, thin, and the one plant in the
    game that reads from a long way off."""
    CANE = zone("leaf", (0.55, 0.74, 0.42), rough=0.85)
    parts = []
    for i in range(3):
        parts += _cross(f"seg{i}", 0.52, 1.0, i * 1.0, CANE)
    return join(parts, "sugarcane")


def chain():
    """A two-metre chain, for hanging a lantern under a rim. Links are alternate
    crossed plates rather than real torus geometry -- which is exactly how the
    game does it, and at this distance the difference is nothing."""
    METAL = zone("metal", (0.34, 0.34, 0.38), rough=0.55)
    parts = []
    for i in range(8):
        z = 2.0 - (i + 0.5) * 0.25
        rot = 0.0 if i % 2 == 0 else math.pi / 2
        parts.append(box(f"link{i}", (0.13, LEAF, 0.24), (0, 0, z), METAL,
                         bevel=0.0, rot=(0, 0, rot)))
    parts.append(cylinder("ring", 0.06, 0.06, (0, 0, 1.98), METAL,
                          rot=(0, 0, 0), vertices=8))
    return join(parts, "chain")


for name, builder, res in (
    ("crop", crop, 128),
    ("flower", flower, 128),
    ("mcfence", mcfence, 128),
    ("lanternpost", lanternpost, 128),
    ("sugarcane", sugarcane, 128),
    ("chain", chain, 128),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
