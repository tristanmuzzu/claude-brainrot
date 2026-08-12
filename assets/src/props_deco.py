"""More Minecraft-ish furniture for the spiral scene: light, track and rock.

``props_mc.py`` covers the things that grow on a farm. This file covers the
rest of what dresses a platform, and it exists for the same reason: a torch is
a stick with a flame on it, a rail is two strips of iron on sleepers, a
stalactite is a spike -- built out of whole cells every one of them comes out
as the same coloured box, and a platform scattered with those reads as rubble
rather than as a place somebody built.

Local axes are the project's: X across, Y along, **Z up**, origin on the
ground so a prop can be dropped at a cell's floor without an offset nobody can
see the reason for. The exporter converts to glTF's Y-up. One prop breaks that
rule on purpose -- see ``dripstone``.

* torch        -- a stick with a bright head, the wall/floor torch
* rail         -- one metre of minecart track, tileable end to end
* endrod       -- a white rod a block tall with a lit tip
* chorus       -- a forking purple stalk two blocks tall, bulbs and buds
* netherfungus -- a domed fungus a block tall, with sprouts round its foot
* pebbles      -- a scatter of small rocks, to break up bare stone ground
* dripstone    -- a stalactite, hanging **downward** from the origin

Zones are named for what the runtime recolours: ``leaf``, ``stem``, ``wood``,
``metal``, ``glow``. A prop that does not carry a zone simply ignores the
colour, which is what ``ModelAsset.recolor`` is for.
"""

import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)

#: The blade thickness of every crossed quad here. Vanilla draws these as
#: single textured planes with no thickness at all; a plane with no thickness
#: disappears edge-on, and the camera in this scene runs *past* these things
#: at seven metres a second. Two centimetres is invisible as a solid and never
#: vanishes. Same constant, same reason, as ``props_mc.py``.
LEAF = 0.02


def _cross(name, w, h, loc, material, tilt=0.0):
    """Two quads at right angles: the shape every small plant in the game is.

    ``loc`` is the foot of the cross, so a sprout can be dropped beside its
    parent without anybody working out a centre.
    """
    x, y, z = loc
    out = []
    for i, rot in enumerate((0.0, math.pi / 2)):
        out.append(box(f"{name}{i}", (w, LEAF, h), (x, y, z + h / 2), material,
                       bevel=0.0, rot=(tilt, 0, rot)))
    return out


def _dome(name, radius, height, loc, material, segments=12, rings=6):
    """A squashed sphere: the one shape in here that ``common`` has no
    primitive for, and the only honest way to build a mushroom cap.

    Everything else here is boxes and prisms, and a cap was tried twice that
    way -- stacked discs, then stacked bevelled boxes. Both fail for the same
    reason: whatever shrinks from one layer to the next leaves the lower
    layer's top face over as a flat ring, the bake puts a crease along it, and
    the eye counts rings. Seventy-odd quads of real curvature is cheaper than
    the tiers it takes to fake one, and it is right from every heading.

    The scale is left on the object rather than applied to the mesh: ``join``
    bakes object transforms, which is the same thing :func:`common.box` relies
    on for its rotations.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (radius, radius, height)
    ob.data.materials.append(material)
    return ob


def _limb(name, start, length, tilt, az, w, material, bevel=0.0):
    """A square stalk of ``length`` leaning ``tilt`` from vertical, pointing
    along compass angle ``az``. Returns the part and the point it ends at, so
    the next joint hangs off the last one rather than off arithmetic repeated
    by hand.

    Blender's XYZ euler applies Z last, so ``(0, tilt, az)`` swings the stalk's
    own up-axis out to ``tilt`` and then spins that lean round to ``az`` --
    which is the order the two angles are meant in.
    """
    d = (math.sin(tilt) * math.cos(az),
         math.sin(tilt) * math.sin(az),
         math.cos(tilt))
    mid = tuple(s + d[i] * length / 2 for i, s in enumerate(start))
    end = tuple(s + d[i] * length for i, s in enumerate(start))
    return box(name, (w, w, length), mid, material, bevel=bevel,
               rot=(0, tilt, az)), end


def torch():
    """A torch: a stick a bit over half a block, and a head that is its own
    ``glow`` zone so the scene can hang an additive sprite on the same point
    and have the two agree about where the light is.

    The head is the **same width as the stick**, plus a nub above it. Anything
    wider is a marshmallow on a stick or a lollipop -- both were rendered and
    both were exactly that -- and vanilla's torch is no wider at the top
    either: what makes it a flame there is the brightness, not the size, and
    brightness is what the ``glow`` zone is for.
    """
    WOOD = zone("wood", (0.42, 0.30, 0.17), rough=0.85)
    GLOW = zone("glow", (1.0, 0.78, 0.34), rough=0.25)
    parts = [
        box("stick", (0.12, 0.12, 0.52), (0, 0, 0.26), WOOD, bevel=0.0),
        box("head", (0.13, 0.13, 0.13), (0, 0, 0.575), GLOW, bevel=0.015),
        box("flame", (0.07, 0.07, 0.08), (0, 0, 0.66), GLOW, bevel=0.025),
    ]
    return join(parts, "torch")


def rail():
    """One metre of minecart track, running along **Y**. The strips span the
    whole cell and the sleepers are on a quarter-metre pitch that carries
    across the join, so a line of these meets end to end with neither a gap
    nor a doubled sleeper."""
    METAL = zone("metal", (0.56, 0.56, 0.59), rough=0.4)
    WOOD = zone("wood", (0.24, 0.18, 0.12), rough=0.9)
    parts = []
    for y in (-0.375, -0.125, 0.125, 0.375):
        parts.append(box(f"sleeper{y:+.3f}", (0.66, 0.13, 0.055),
                         (0, y, 0.028), WOOD, bevel=0.01))
    for x in (-0.25, 0.25):
        parts.append(box(f"strip{x:+.2f}", (0.09, 1.0, 0.065),
                         (x, 0, 0.058), METAL, bevel=0.012))
    return join(parts, "rail")


def endrod():
    """An End Rod: a thin white rod a block tall, standing on a slightly wider
    foot, with a lit tip. The foot is what stops it reading as a dropped
    pencil -- vanilla's has one too."""
    STEM = zone("stem", (0.93, 0.93, 0.89), rough=0.5)
    GLOW = zone("glow", (1.0, 0.94, 0.66), rough=0.2)
    parts = [
        box("foot", (0.22, 0.22, 0.12), (0, 0, 0.06), STEM, bevel=0.02),
        box("rod", (0.10, 0.10, 0.80), (0, 0, 0.50), STEM, bevel=0.0),
        box("tip", (0.14, 0.14, 0.12), (0, 0, 0.94), GLOW, bevel=0.03),
    ]
    return join(parts, "endrod")


def chorus():
    """A chorus plant: a knobbly stalk that forks once, about two blocks tall.

    The bulbs are heavily bevelled boxes rather than spheres -- at a metre or
    more the difference is nothing and the triangle count is a tenth. Each tip
    carries a flower, and the flower's petals are crossed quads, which is what
    the game draws there.

    The two arms are 125 degrees apart rather than opposite. Opposite arms are
    coplanar, so from one heading in every four the plant is a stick; a plant
    that is only ever a Y from two headings is the one that reads.
    """
    STEM = zone("stem", (0.52, 0.34, 0.56), rough=0.8)
    BUD = zone("leaf", (0.72, 0.52, 0.76), rough=0.6)
    parts = []

    trunk, top = _limb("trunk", (0, 0, 0), 0.78, 0.0, 0.0, 0.22, STEM)
    parts.append(trunk)
    parts.append(box("knee", (0.30, 0.30, 0.24), (0, 0, 0.46), STEM,
                     bevel=0.08))
    parts.append(box("fork", (0.34, 0.34, 0.30), (0, 0, top[2] + 0.10), STEM,
                     bevel=0.10))
    joint = (0, 0, top[2] + 0.22)

    for i, az in enumerate((math.radians(25), math.radians(150))):
        tilt = math.radians(34 if i == 0 else 28)
        arm, arm_end = _limb(f"arm{i}", joint, 0.62, tilt, az, 0.19, STEM)
        parts.append(arm)
        parts.append(box(f"elbow{i}", (0.28, 0.28, 0.26), arm_end, STEM,
                         bevel=0.08))
        tip, tip_end = _limb(f"tip{i}", arm_end, 0.38, tilt / 3, az, 0.15,
                             STEM)
        parts.append(tip)
        parts.append(box(f"bud{i}", (0.24, 0.24, 0.22),
                         (tip_end[0], tip_end[1], tip_end[2] + 0.06), BUD,
                         bevel=0.07))
        parts += _cross(f"petal{i}", 0.34, 0.22,
                        (tip_end[0], tip_end[1], tip_end[2] - 0.02), BUD)
    return join(parts, "chorus")


def netherfungus():
    """A nether fungus: a pale stalk under a domed cap, a block tall, with a
    few sprouts round its foot.

    The cap is one squashed sphere -- see :func:`_dome` for why it is not the
    stack of prisms everything else here is made of -- with a pale disc tucked
    under it for the gills, which is what stops the underside reading as the
    bottom of a ball.

    The sprouts are crossed quads, because that is literally what vanilla's
    small fungus is: two intersecting planes.
    """
    STEM = zone("stem", (0.80, 0.74, 0.64), rough=0.85)
    CAP = zone("leaf", (0.70, 0.16, 0.16), rough=0.75)
    parts = [
        box("stalk", (0.18, 0.18, 0.66), (0, 0, 0.33), STEM, bevel=0.02),
        cylinder("gills", 0.28, 0.05, (0, 0, 0.61), STEM, vertices=12),
        _dome("cap", 0.36, 0.24, (0, 0, 0.74), CAP),
    ]
    for i, (x, y, s) in enumerate(((-0.42, 0.24, 0.22),
                                   (0.36, -0.32, 0.17),
                                   (0.14, 0.44, 0.13))):
        parts.append(box(f"sprout{i}", (s * 0.2, s * 0.2, s * 0.5),
                         (x, y, s * 0.25), STEM, bevel=0.0))
        parts += _cross(f"sprout{i}cap", s, s * 0.75, (x, y, s * 0.38), CAP)
    return join(parts, "netherfungus")


def pebbles():
    """A scatter of small rocks over about a block, none higher than a quarter.

    Bare stone ground draws as one flat plate at any distance, and a plate is
    the one thing that never reads as terrain. Its zone is ``wood`` -- reused
    here as the generic mineral zone, because the runtime's zone names are a
    recolouring vocabulary rather than a material list, and adding a name to
    that vocabulary for one prop costs every caller.

    The scatter is a literal table rather than a random draw: an asset is
    built once and committed, and a build that produces different geometry on
    Tuesday is a build nobody can check against ``metrics.json``.

    Each rock is also tilted a few degrees and sunk a centimetre and a half.
    Nine boxes all sitting square on the floor read as nine boxes however
    different their sizes are, because every one of them shows the same three
    faces to the same light; a tilt is what makes them stone.
    """
    ROCK = zone("wood", (0.46, 0.45, 0.44), rough=0.9)
    # x, y, size x, size y, size z, yaw degrees, tilt degrees
    table = (
        (-0.36, -0.30, 0.22, 0.17, 0.13, 18, 6),
        (-0.05, -0.42, 0.15, 0.13, 0.09, -40, -8),
        (0.30, -0.20, 0.25, 0.20, 0.19, 63, 4),
        (-0.18, -0.02, 0.13, 0.12, 0.08, 5, 10),
        (0.16, 0.14, 0.18, 0.23, 0.14, -22, -5),
        (-0.40, 0.24, 0.20, 0.15, 0.11, 47, 7),
        (0.00, 0.36, 0.15, 0.18, 0.09, -8, -11),
        (0.36, 0.40, 0.12, 0.11, 0.07, 30, 9),
        (0.44, 0.06, 0.17, 0.14, 0.12, -55, -6),
    )
    parts = [
        box(f"rock{i}", (sx, sy, sz), (x, y, sz / 2 - 0.015), ROCK,
            bevel=min(0.045, sz * 0.28),
            rot=(math.radians(tilt), math.radians(-tilt),
                 math.radians(yaw)))
        for i, (x, y, sx, sy, sz, yaw, tilt) in enumerate(table)
    ]
    return join(parts, "pebbles")


def dripstone():
    """A stalactite, and the one prop here whose **origin is at its top**: it
    hangs a block and a half *downward*, from z=0 to z=-1.5.

    Say that out loud because it is the kind of thing that costs an hour --
    every other prop in this directory stands on its origin, and a caller that
    drops this one on a floor cell gets a spike buried in the floor with
    nothing visible above it. It goes at the **ceiling** cell's floor plane.

    Four-sided prisms of shrinking width, because vanilla's dripstone is a
    stepped taper too, and a smooth cone at this size costs triangles to look
    less like the game. Its zone is ``wood``, the generic mineral zone --
    see :func:`pebbles`.

    Ten prisms rather than five, on a curve rather than a straight line. Five
    read as a flight of stairs -- a step of nine centimetres at the top is a
    thing the eye counts -- and a straight taper reads as a traffic cone. The
    exponent leans the profile inward so it narrows slowly and then points,
    which is what a stalactite that grew does.
    """
    ROCK = zone("wood", (0.55, 0.42, 0.36), rough=0.9)
    SEGS, TOP_R, DROP = 10, 0.36, 1.5
    parts = []
    for i in range(SEGS):
        t = (i + 0.5) / SEGS
        r = TOP_R * (1.0 - t) ** 1.3 + 0.02
        parts.append(cylinder(f"seg{i}", r, DROP / SEGS,
                              (0, 0, -(i + 0.5) * DROP / SEGS), ROCK,
                              vertices=4))
    return join(parts, "dripstone")


for name, builder, res in (
    ("torch", torch, 128),
    ("rail", rail, 128),
    ("endrod", endrod, 128),
    ("chorus", chorus, 128),
    ("netherfungus", netherfungus, 128),
    ("pebbles", pebbles, 128),
    ("dripstone", dripstone, 128),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
