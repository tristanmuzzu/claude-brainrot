"""More Minecraft-ish platform furniture: the things that grow.

``props_mc.py`` is the same argument as this file and it is worth restating,
because it is the only reason either exists. Everything else in the project is
built out of whole cells, because everything else in the project is a
*building*. A platform is a **place**, and what makes a place read as a swamp
or a desert or a cave is precisely the parts of Minecraft that are **not**
cubes: a tuft of grass is a handful of blades, a dead bush is twigs and no
leaves, a lily pad is a disc one pixel thick, a vine is a ragged sheet hanging
off a ceiling. Built out of cells every one of those is the same coloured box,
which is what reads as rubble.

Local axes are the project's: X across, Y along, **Z up**, origin on the
ground so a prop can be dropped at a cell's floor without an offset nobody can
see the reason for. The exporter converts to glTF's Y-up. The one exception is
``vinehang``, whose origin is at its **top**, and which says so again where it
is built.

* grasstuft   -- a clump of seven blades, half a block, for every green section
* deadbush    -- a short trunk and its twiggy forks, no leaves
* cactus      -- a two-block ridged column with spines, and one arm
* lilypad     -- a notched disc that lies ON water, 2 cm above z=0
* vinehang    -- three blocks of ragged strands hung DOWNWARD from the origin
* bamboo      -- a jointed stalk two and a half blocks tall, leaves at the top
* mushroomcap -- a white stem under a stepped red cap with white spots

Zones are named for what the runtime recolours: ``leaf``, ``stem``, ``wood``,
``glow``. A prop that does not carry a zone simply ignores the colour, which is
what ``ModelAsset.recolor`` is for.
"""

import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)

#: The blade thickness of every flat quad here, and the same two centimetres
#: ``props_mc.py`` uses, for the same reason: vanilla draws these as single
#: textured planes with no thickness at all, a plane with no thickness
#: disappears edge-on, and the camera in this scene runs *past* these things at
#: seven metres a second. Two centimetres is invisible as a solid and never
#: vanishes. Deliberately duplicated rather than shared -- an asset script is
#: run by Blender as a program, and importing a sibling would run its build.
LEAF = 0.02


def _dir(tilt, azim):
    """The unit vector a part's local +Z points along under ``rot=(tilt, 0,
    azim)``: tipped ``tilt`` off vertical, swung round to ``azim``."""
    return (math.sin(tilt) * math.sin(azim),
            -math.sin(tilt) * math.cos(azim),
            math.cos(tilt))


def _along(name, size, base, tilt, azim, material, bevel=0.0):
    """A box of length ``size[2]`` *standing on* ``base`` and leaning.

    :func:`box` centres its mesh on the location it is given, which is the
    wrong end to reason from for anything that grows out of something else: a
    blade, a twig and a cactus spine are all a length rooted at a point.
    """
    d = _dir(tilt, azim)
    half = size[2] / 2
    loc = (base[0] + d[0] * half, base[1] + d[1] * half, base[2] + d[2] * half)
    return box(name, size, loc, material, bevel=bevel, rot=(tilt, 0, azim))


def _end(base, length, tilt, azim):
    """Where :func:`_along` put the far end, so the next part can start there."""
    d = _dir(tilt, azim)
    return (base[0] + d[0] * length, base[1] + d[1] * length,
            base[2] + d[2] * length)


def _cross(name, w, h, centre, material, tilt=0.0):
    """Two quads at right angles: the shape every plant in the game is.

    ``centre`` is (x, y, bottom) -- the pair stands on that z.
    """
    x, y, z = centre
    return [box(f"{name}{i}", (w, LEAF, h), (x, y, z + h / 2), material,
                bevel=0.0, rot=(tilt, 0, rot))
            for i, rot in enumerate((0.0, math.pi / 2))]


def _bite(target, cutter):
    """Boolean the ``cutter`` out of ``target`` and drop it.

    Used once, for the lily pad's notch, because the notch is the only thing
    that tells a lily pad from a coin and there is no way to *not* build
    geometry with a primitive.
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    mod = target.modifiers.new("notch", "BOOLEAN")
    mod.object = cutter
    mod.operation = "DIFFERENCE"
    bpy.ops.object.modifier_apply(modifier="notch")
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def grasstuft():
    """A clump of seven blades, about half a block.

    The one prop that is scattered over every green section, so it is the one
    that has to survive being looked at, and the first attempt did not: seven
    wide quads leaning hard off a point is a spiky star, not a plant. Three
    things fix it, and all three are about the blade rather than the clump.
    A blade is **three** segments, near-upright at the root and only bending
    over near the tip, so it is a curve and the clump has an outline instead of
    radii. It **narrows** as it goes, because a blade of even width is a plank.
    And it is **thin against its length** -- eight centimetres against fifty --
    which is what a blade of grass is and what the first pass, at twice the
    width and half the height, was not.

    The azimuths are spread right round the circle on purpose: a quad shows its
    broad face along its own normal, so a tuft whose blades all face one way is
    a tuft that vanishes when the camera comes at it from the side.
    """
    LEAFZ = zone("leaf", (0.40, 0.68, 0.26), rough=0.9)
    STEM = zone("stem", (0.28, 0.50, 0.20), rough=0.9)
    parts = [box("root", (0.13, 0.13, 0.05), (0, 0, 0.025), STEM, bevel=0.0)]
    # (azimuth degrees, total height, width at the root)
    blades = ((8, 0.54, 0.085), (63, 0.46, 0.080), (117, 0.58, 0.090),
              (172, 0.38, 0.070), (228, 0.50, 0.085), (285, 0.33, 0.070),
              (331, 0.43, 0.078))
    # (share of the height, lean off vertical, share of the width)
    segments = ((0.42, 5, 1.00), (0.33, 19, 0.74), (0.25, 39, 0.38))
    for i, (deg, h, w) in enumerate(blades):
        azim = math.radians(deg)
        at = (math.sin(azim) * 0.045, -math.cos(azim) * 0.045, 0.02)
        # each blade also swings a little round the clump as it rises, in
        # alternate directions. A blade that bends in the plane it started in
        # bends straight out from the middle, and seven of those is a fountain
        # however gentle each one is.
        curl = math.radians(11 if i % 2 else -11)
        for k, (share, lean, taper) in enumerate(segments):
            tilt, length = math.radians(lean), h * share
            parts.append(_along(f"blade{i}_{k}", (w * taper, LEAF, length), at,
                                tilt, azim, STEM if k == 0 else LEAFZ))
            at = _end(at, length, tilt, azim)
            azim += curl
    return join(parts, "grasstuft")


def deadbush():
    """The dead bush: a stub of trunk and five forks of twig, no leaves.

    The twigs are square rods rather than quads, which is the one place this
    file departs from how the game draws a plant. A dead bush is *nothing but*
    its silhouette, and a silhouette made of planes is a silhouette that halves
    itself every quarter turn.
    """
    WOOD = zone("wood", (0.45, 0.33, 0.19), rough=0.95)
    parts = [box("trunk", (0.09, 0.09, 0.30), (0, 0, 0.15), WOOD, bevel=0.0)]
    # (azimuth, height it leaves the trunk at, lean, length)
    forks = ((14, 0.13, 44, 0.30), (88, 0.26, 30, 0.32), (163, 0.18, 52, 0.28),
             (242, 0.29, 24, 0.30), (308, 0.10, 58, 0.26))
    for i, (deg, z, lean, ln) in enumerate(forks):
        azim, tilt = math.radians(deg), math.radians(lean)
        base = (0, 0, z)
        parts.append(_along(f"twig{i}", (0.055, 0.055, ln), base, tilt, azim,
                            WOOD))
        elbow = _end(base, ln, tilt, azim)
        for j, (dt, da, dl) in enumerate(((-16, -22, 0.21), (19, 26, 0.17))):
            parts.append(_along(
                f"fork{i}{j}", (0.045, 0.045, dl), elbow,
                max(math.radians(6), tilt + math.radians(dt)),
                azim + math.radians(da), WOOD))
    return join(parts, "deadbush")


def cactus():
    """Two blocks of cactus: a column a little narrower than a cell, with a
    proud panel on each face, spines, and one arm.

    The panels are the game's own trick -- the cactus's sides sit one pixel in
    from its top, which is what stops a green column reading as a green block.
    The arm is not vanilla and is here anyway: at twenty metres in a portrait
    strip the ridges are gone and the silhouette is all that is left, and a
    plain column has the silhouette of a fence post.
    """
    BODY = zone("leaf", (0.24, 0.52, 0.24), rough=0.9)
    SPINE = zone("stem", (0.80, 0.80, 0.60), rough=0.55)
    H = 2.0
    parts = [box("core", (0.80, 0.80, H), (0, 0, H / 2), BODY, 0.02)]

    def spines(name, radius, azim, levels, spread=0.19):
        """Two spines a level, standing off the face whose panel sits at
        ``azim``. That face's outward normal is ``azim + pi`` in the frame
        :func:`_dir` works in, and getting the half-turn wrong puts every
        spine on the far side of the model -- which is what the arm's did.
        """
        out = []
        out_dir = azim + math.pi
        for k, z in enumerate(levels):
            for s, side in enumerate((-spread, spread)):
                base = (math.sin(out_dir) * radius + math.cos(azim) * side,
                        -math.cos(out_dir) * radius + math.sin(azim) * side, z)
                out.append(_along(f"{name}{k}{s}", (0.03, 0.03, 0.095), base,
                                  math.pi / 2, out_dir, SPINE))
        return out

    for i in range(4):
        azim = i * math.pi / 2
        parts.append(box(f"panel{i}", (0.62, 0.07, H - 0.12),
                         (-math.sin(azim) * 0.42, math.cos(azim) * 0.42, H / 2),
                         BODY, bevel=0.01, rot=(0, 0, azim)))
        parts += spines(f"spine{i}", 0.45, azim, (0.34, 0.86, 1.38, 1.78))

    # The arm: out along +X at chest height, then up. It reaches half a block
    # clear of the body and rises most of the way to the crown, because an arm
    # that only just clears the panels reads as a lump growing on one.
    #
    # The reach and the upright deliberately do **not** share a face. Built
    # flush -- both ending at x=0.86, both starting at z=0.86 -- the bake came
    # back with a hard black rectangle at the elbow, which reads as a hole
    # punched in the model and survived being given four times the light map.
    # Two coincident surfaces have no answer to give a ray, so they are given
    # different planes instead: the reach ends *inside* the upright.
    parts.append(_along("arm0", (0.24, 0.24, 0.44), (0.34, 0.0, 0.98),
                        math.pi / 2, math.pi / 2, BODY, bevel=0.02))
    parts.append(_along("arm1", (0.24, 0.24, 1.00), (0.74, 0.0, 0.80), 0, 0,
                        BODY, bevel=0.02))
    parts += spines("armspine", 0.86, -math.pi / 2, (1.18, 1.52), spread=0.075)
    return join(parts, "cactus")


def lilypad():
    """A lily pad: an octagonal disc lying two centimetres above z=0, with the
    notch bitten out of one side.

    It is meant to be dropped ON a water surface rather than in a cell, so it
    is deliberately thin enough to have no side worth seeing and low enough
    that a water block's own top face is what you look at it against. An
    octagon reads as round at every distance this thing is ever drawn from.
    """
    PAD = zone("leaf", (0.29, 0.55, 0.25), rough=0.85)
    pad = cylinder("pad", 0.45, 0.035, (0, 0, 0.02), PAD, vertices=8)
    # A square turned 45 degrees drives its corner in, so the bite is a V
    # rather than a rectangle -- which is the whole shape of the notch.
    cutter = box("notch", (0.36, 0.36, 0.3), (0, 0.46, 0.02), PAD, bevel=0.0,
                 rot=(0, 0, math.pi / 4))
    return _bite(pad, cutter)


def vinehang():
    """Hanging vines: four ragged strands, three blocks of drop.

    **This model's origin is at its TOP**, and it is the only one in either
    prop file that is: a vine is hung from the *ceiling* cell it grows on, and
    everything below the origin is the drop. Place it at the floor of the cell
    above and the strands fall through the three cells under it. Give it a
    cell's floor like every other prop here and it hangs through the platform.

    Each strand is crossed quads in segments of unequal width, wandering a few
    centimetres as it descends, so the sheet has an edge instead of being a
    rectangle with a texture on it. The widest is most of a block across, which
    is what a vine is in the game -- a whole block face -- and the first pass,
    at a third of that, read as four sticks hanging on a string.
    """
    VINE = zone("leaf", (0.28, 0.48, 0.21), rough=0.9)
    parts = []
    # (x, y, drop, width at the top)
    strands = ((0.00, 0.00, 3.0, 0.72), (-0.30, 0.18, 2.4, 0.58),
               (0.26, -0.24, 1.7, 0.62), (0.08, 0.32, 2.7, 0.50))
    for s, (x, y, drop, w) in enumerate(strands):
        n = max(2, round(drop / 0.85))
        seg = drop / n
        for i in range(n):
            top = -i * seg
            width = w * (0.92 + 0.16 * math.cos(i * 2.4 + s)) * (1 - 0.09 * i)
            parts += _cross(
                f"v{s}_{i}", width, seg,
                (x + 0.07 * math.sin(i * 2.1 + s),
                 y + 0.07 * math.cos(i * 1.7 + s), top - seg), VINE)
    return join(parts, "vinehang")


def bamboo():
    """A bamboo stalk: two and a half blocks, four joints, leaves at the top.

    The joints are the read. A plain rod of that thinness is a fence post seen
    end-on, and the collars are what say it is a plant -- so they are wider
    than the cane by half again, which is more than the game's and is what
    survives being a few pixels tall on screen.
    """
    CANE = zone("stem", (0.53, 0.70, 0.30), rough=0.85)
    LEAFZ = zone("leaf", (0.40, 0.66, 0.27), rough=0.9)
    H = 2.5
    parts = [box("stalk", (0.14, 0.14, H), (0, 0, H / 2), CANE, bevel=0.0)]
    for i, z in enumerate((0.62, 1.20, 1.74, 2.22)):
        parts.append(box(f"node{i}", (0.21, 0.21, 0.07), (0, 0, z), CANE, 0.01))
    # (height, azimuth, lean off vertical, length) -- the thin axis is across
    # the lean, so a leaf shows its face to a camera passing it sideways
    for i, (z, deg, lean, ln) in enumerate((
            (1.84, 24, 64, 0.42), (2.00, 152, 72, 0.34),
            (2.16, 268, 58, 0.44), (2.32, 84, 76, 0.30),
            (2.44, 206, 66, 0.36))):
        parts.append(_along(f"leaf{i}", (LEAF, 0.11, ln), (0, 0, z),
                            math.radians(lean), math.radians(deg), LEAFZ))
    parts += _cross("crown", 0.26, 0.24, (0, 0, 2.46), LEAFZ)
    return join(parts, "bamboo")


def mushroomcap():
    """A red mushroom: white stem, stepped cap, white spots.

    The cap is three discs rather than a dome because a dome at this size is a
    hundred triangles to say what three steps say, and because the game's own
    mushroom is a stack of flat texels anyway. The spots are their own ``glow``
    zone so a cave section can light them without lighting the cap.
    """
    STEM = zone("stem", (0.92, 0.90, 0.84), rough=0.8)
    CAP = zone("leaf", (0.76, 0.15, 0.13), rough=0.7)
    SPOT = zone("glow", (0.96, 0.94, 0.88), rough=0.5)
    parts = [box("stalk", (0.22, 0.22, 0.46), (0, 0, 0.23), STEM, 0.02)]
    for i, (r, d, z) in enumerate(((0.40, 0.13, 0.45), (0.33, 0.10, 0.55),
                                   (0.21, 0.09, 0.63))):
        parts.append(cylinder(f"cap{i}", r, d, (0, 0, z), CAP, vertices=10))
    # Spots are sunk into the step they sit on and stand a couple of
    # centimetres proud of it. Set out on the surface instead they are knobs.
    # Unbeveled, because a bevel on a five-centimetre box is invisible at every
    # distance this is ever drawn from and eight of them were two thirds of the
    # model's triangles.
    for i, deg in enumerate((18, 90, 162, 234, 306)):
        azim = math.radians(deg)
        parts.append(box(f"spot{i}", (0.11, 0.055, 0.07),
                         (-math.sin(azim) * 0.36, math.cos(azim) * 0.36, 0.46),
                         SPOT, bevel=0.0, rot=(0, 0, azim)))
    for i, deg in enumerate((54, 198)):
        azim = math.radians(deg)
        parts.append(box(f"spotb{i}", (0.09, 0.05, 0.06),
                         (-math.sin(azim) * 0.30, math.cos(azim) * 0.30, 0.56),
                         SPOT, bevel=0.0, rot=(0, 0, azim)))
    parts.append(box("spottop", (0.12, 0.12, 0.04), (0, 0, 0.665), SPOT, 0.0))
    return join(parts, "mushroomcap")


for name, builder, res in (
    ("grasstuft", grasstuft, 128),
    ("deadbush", deadbush, 128),
    # the cactus alone gets a bigger light map: thirty-odd spines are
    # thirty-odd UV islands, and at 128 the atlas has no room left for the
    # panels, which come back with a black smear under the arm
    ("cactus", cactus, 256),
    ("lilypad", lilypad, 128),
    ("vinehang", vinehang, 128),
    ("bamboo", bamboo, 128),
    ("mushroomcap", mushroomcap, 128),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
