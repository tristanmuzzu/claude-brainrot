"""The two climbable block faces: a ladder and a curtain of vines.

The spiral tower drew both of these as whole cells, and both are wrong as
cells for the same reason the plants in ``props_mc.py`` and
``props_flora.py`` are: they are not blocks. A ladder in the game is a thin
lattice stuck on the *face* of the block behind it -- you can see the stone
through the gaps and you can see the rails in silhouette against the drop. A
vine is a ragged sheet a pixel thick on a block face, hanging in tatters. A
solid cube says neither thing; it says "somebody coloured a block brown",
which is exactly the note the owner sent back.

Both are **one block's worth and tileable vertically**, because that is how
they are used: a climb is a column of these, and the seam between two copies
has to be invisible. The ladder's rungs are spaced so the gap across a join is
the same as the gap inside one copy; the vine's full-height strands keep a
constant width and depth for the same reason.

Local axes are the project's: X across, Y along, **Z up**, origin on the
ground so a prop can be dropped at a cell's floor without an offset nobody can
see the reason for. The exporter converts to glTF's Y-up.

**Which way they face.** Both models lie in a thin slab in front of the plane
``y = 0``: the wall is the half-space *behind* them, at negative Y, and the
climbable side looks along **+Y** -- the same axis every other prop file calls
"along", and the axis a yaw of zero points down. So a caller hanging one on a
wall whose outward normal is the horizontal heading ``(nx, nz)`` passes the
yaw that heading already implies, ``atan2(nx, -nz)`` -- the same expression
``scenes/spiralplan.py`` uses to turn a step into a bearing. Placed at the
floor of the cell *in front of* the wall block, the model then covers that
wall's face and nothing else.

Nothing is flush with ``y = 0``. Both start two centimetres out from it,
because a face laid exactly on the wall's own face is two coincident surfaces
with no answer to give a ray -- the bake comes back with a hard black
rectangle where they meet (``props_flora.py``'s cactus elbow is the same
lesson), and at runtime the two z-fight.

* ladder -- two rails and three rungs, hard against a wall, tileable
* vine   -- a ragged sheet of strands and leaf clusters, tileable

Zones are named for what the runtime recolours: ``wood`` and ``leaf``. A prop
that does not carry a zone simply ignores the colour, which is what
``ModelAsset.recolor`` is for.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, join, reset, run_script_banner, zone,
)

#: The thickness of every flat quad here, and the same two centimetres
#: ``props_mc.py`` and ``props_flora.py`` use, for the same reason: vanilla
#: draws these as single textured planes with no thickness at all, a plane with
#: no thickness disappears edge-on, and the camera in this scene runs *past*
#: these things at seven metres a second. Two centimetres is invisible as a
#: solid and never vanishes. Deliberately duplicated rather than shared -- an
#: asset script is run by Blender as a program, and importing a sibling would
#: run its build.
LEAF = 0.02

#: How far the nearest geometry stands off the wall plane. See the module
#: docstring: zero would be two coincident surfaces.
STANDOFF = 0.02

#: The front of the slab. A ladder in the game is a couple of pixels proud of
#: the block it is on; fourteen centimetres is that, and it is also the whole
#: budget -- nothing here may stick out further, because the cell in front of a
#: climbable wall is the one the body is standing in.
DEPTH = 0.14

#: Rungs per block. The spacing falls out of it (``(i + 0.5) / RUNGS``), which
#: is the only arrangement that is uniform *across a join* as well as within
#: one copy: the last rung of a copy sits half a gap below its top, the first
#: rung of the copy above sits half a gap above its bottom, and the pair are
#: one gap apart like every other pair. Rungs typed in as three numbers is how
#: a stack ends up with a doubled rung at every block boundary.
RUNGS = 3


def ladder():
    """One block of ladder: two rails the full height of the cell and three
    rungs between them.

    The rails run z = 0 to z = 1 exactly, so a stack of these is one unbroken
    pair of rails with no step at the seams. They also sit *proud* of the
    rungs -- the rungs are inset two centimetres at the front and two at the
    back -- which is the whole read at a distance: side-on, a ladder is two
    lines with the wall showing between them, and rails flush with their rungs
    are a solid panel.
    """
    WOOD = zone("wood", (0.55, 0.40, 0.22), rough=0.85)
    parts = []
    for i, x in enumerate((-0.38, 0.38)):
        parts.append(box(f"rail{i}", (0.12, DEPTH - STANDOFF, 1.0),
                         (x, (STANDOFF + DEPTH) / 2, 0.5), WOOD, bevel=0.0))
    for i in range(RUNGS):
        z = (i + 0.5) / RUNGS
        # The rung runs a little *into* both rails rather than up to them: a
        # rung that stops on the rail's inner face is another pair of
        # coincident surfaces, and at this size the overlap costs nothing.
        parts.append(box(f"rung{i}", (0.80, 0.08, 0.07),
                         (0.0, STANDOFF + 0.02 + 0.04, z), WOOD, bevel=0.0))
    return join(parts, "ladder")


def _strand(name, x, y, top, bottom, width, material):
    """One vertical ribbon of vine, thin in Y, standing between two heights.

    Every strand gets its own ``y``, spread across the slab rather than shared,
    so the sheet is not one plane: a curtain whose parts are all coplanar is a
    curtain that flattens to a line when the camera comes at the wall from the
    side, which is the same failure ``LEAF`` exists to prevent one step up.
    """
    height = top - bottom
    return box(name, (width, LEAF, height), (x, y, bottom + height / 2),
               material, bevel=0.0)


def _cluster(name, x, y, z, w, d, h, material, tilt=0.0):
    """A leaf clump: two small quads at right angles, so it reads from any
    horizontal angle. ``d`` is kept small deliberately -- the crosswise quad is
    the only part of this model with any depth to it, and it has to stay inside
    the slab.

    ``tilt`` leans the broad quad in the plane of the wall, and it is the only
    reason the clumps are visible at all. Built upright they were green
    rectangles against green rectangles, in a model where every other edge is
    also vertical: they read as more sheet, and two renders in a row went by
    without anyone being able to point at one. A diagonal in a picture made
    entirely of vertical lines is seen instantly, at any distance, and costs
    nothing. Only the broad quad turns -- the crosswise one stays upright,
    because its whole job is to be there when the broad one is edge-on.
    """
    return [
        box(f"{name}a", (w, LEAF, h), (x, y, z + h / 2), material, bevel=0.0,
            rot=(0, tilt, 0)),
        box(f"{name}b", (LEAF, d, h * 0.8), (x, y, z + h * 0.4), material,
            bevel=0.0),
    ]


def vine():
    """One block of hanging vine: five overlapping panels with a ragged lower
    edge, three thin tendrils below it, and four leaf clumps on the front.

    The point of this model is that it is **not** a lattice, and both ways of
    getting that wrong were built before this one. Five evenly spaced strands
    of similar width, with air between every pair, is a green **picket
    fence**. Five panels overlapping in x so they tile the whole face, which
    was the correction, is a green **slab** -- and a slab is the cube this
    model exists to stop being drawn. A vine in the game is a mass, with the
    wall showing through it in places.

    So the panels overlap at the top, where nearly the whole face is covered,
    and there are exactly two vertical slits of daylight left open all the way
    down. The ragged read is in the *bottom* edge: each panel stops at a
    different height and hangs a narrower lip below that, and the lower half
    of the block is mostly air.

    Two panels run the full height, and those two are the only parts that
    cross a block boundary -- so they are the two that keep a **constant
    width, x and y** down their whole length. A panel that tapers looks better
    on its own and puts a visible step at every seam in a stack, which is the
    trade this format cannot make. They are also deliberately **not
    adjacent**: side by side they were a solid unbroken column half the face
    wide, which is what made the second attempt a slab.

    The clumps stand further out than the sheet, on purpose. Lying in its
    plane they were the same green against the same green and might as well
    not have been built; straddling a slit at a height where the sheet has
    ended they are the only thing giving the silhouette a bump.
    """
    LEAFZ = zone("leaf", (0.27, 0.47, 0.20), rough=0.9)
    parts = []
    # (x, y, width, bottom, lip width, lip drop). Left to right the x spans are
    # -0.44..-0.35, -0.41..-0.19, -0.16..+0.04, +0.075..+0.265, +0.25..+0.44:
    # neighbours overlap except at two 3 cm gaps, and those two gaps are the
    # slits. The first two rows of the table are the pair that reach z = 0 and
    # carry the stack.
    panels = ((-0.300, 0.030, 0.22, 0.00, 0.00, 0.00),
              (0.170, 0.060, 0.19, 0.00, 0.00, 0.00),
              (-0.060, 0.040, 0.20, 0.30, 0.11, 0.13),
              (0.345, 0.070, 0.19, 0.16, 0.09, 0.10),
              (-0.395, 0.055, 0.09, 0.52, 0.08, 0.16))
    for i, (x, y, w, bottom, lw, drop) in enumerate(panels):
        parts.append(_strand(f"panel{i}", x, y, 1.0, bottom, w, LEAFZ))
        if drop:
            # a narrower lip below the cut, offset sideways: a panel that ends
            # on a straight horizontal edge reads as a strip of tape.
            parts.append(_strand(f"lip{i}", x + w * 0.22, y, bottom,
                                 bottom - drop, lw, LEAFZ))
    # (x, y, top, bottom, width) -- single runners hanging clear of the sheet,
    # two of them down the slits, which is what stops a slit reading as a
    # straight sawn edge.
    for i, (x, y, top, bottom, w) in enumerate((
            (-0.175, 0.125, 0.62, 0.28, 0.045),
            (0.055, 0.125, 0.45, 0.10, 0.040),
            (0.410, 0.125, 0.30, 0.05, 0.040))):
        parts.append(_strand(f"tendril{i}", x, y, top, bottom, w, LEAFZ))
    # (x, y, z, width, depth, height, tilt degrees) -- three of the four hang
    # in the open lower half, past the sheet's ragged edge, because a clump
    # laid over a panel is the same green on the same green and contributes
    # nothing; against the drop it is the whole silhouette. ``y`` plus half of
    # ``depth`` is what pins the model's front face at DEPTH, so these are the
    # parts that set it -- and every y here is off the half-centimetre so that
    # no face of a clump lands *coplanar* with a face of a panel, which is the
    # bake's one hard rule (see the module docstring).
    for i, (x, y, z, w, d, h, tilt) in enumerate((
            (-0.175, 0.0975, 0.14, 0.24, 0.085, 0.20, 35),
            (0.050, 0.0975, 0.05, 0.22, 0.085, 0.19, -30),
            (0.310, 0.0975, 0.04, 0.20, 0.085, 0.17, 26),
            (-0.200, 0.0975, 0.62, 0.18, 0.085, 0.16, -38))):
        parts += _cluster(f"clump{i}", x, y, z, w, d, h, LEAFZ,
                          math.radians(tilt))
    return join(parts, "vine")


for name, builder, res in (
    ("ladder", ladder, 128),
    ("vine", vine, 128),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
