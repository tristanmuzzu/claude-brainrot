"""World scenery: what you see out over the water and up in the air.

Everything else in ``assets/src`` is furniture the body runs past at a few
metres. This file is the opposite problem: these are drawn at **40 to 300
metres** through an eighty-degree lens, against sea and sky, and at that range
a model is its **silhouette** and nothing else. Three consequences, and every
shape here follows from them:

* **No bevels, no round numbers of segments.** A bevel is sub-pixel at forty
  metres and multiplies a cube's triangles by eight. Every box in this file is
  ``bevel=0.0`` (see :func:`blk`), and the cylinders are six- to ten-sided.
  The whole file is boxes on purpose -- it is also what makes it read as the
  same game as the tower.
* **Big, and irregular in plan.** A shape has to subtend a few degrees to be
  a shape at all, so an island is fifty metres across, not five. Rock is a
  stack of *yawed, jittered* boxes (:func:`rocky`) because a stack of aligned
  ones is a ziggurat, and a ziggurat is the one silhouette a rock cannot have.
* **Contrast at the top edge.** Whatever caps a mass -- grass, sand, a lit
  lamp room, a sail -- is the part that separates from the sky, so it is a
  different zone from the mass under it in every asset here.

And one rule that is not about distance at all, learned twice in this file
after it had already been learned once by ``props_flora.cactus``: **no two
overlapping slabs may share a top face.** An island's lawn and a ruin's floor
are each several boxes at different yaws, and built at one height their top
faces are coplanar -- which a ray has no answer for, so the bake comes back
with hard black rectangles across them that read as holes punched in the
model. :func:`terrace` steps each slab a few centimetres below the last, which
also happens to be what a broken floor looks like.

The jitter comes from ``random.Random`` on fixed seeds, so a rebuild
reproduces the committed geometry exactly and ``metrics.json`` stays put.

Local axes are the project's: X across, Y along, **Z up**. The exporter
converts to glTF's Y-up, so a Z here is a Y in ``metrics.json``.

Origin conventions -- read this before placing anything
-------------------------------------------------------
``spiralplan.HANGING`` exists because this was got wrong before, so each asset
says which of three conventions it uses:

* **ground/waterline origin** (the project default): z=0 is where the thing
  meets what holds it up, and it rises into +z. Anything below z=0 is meant to
  be under water or under the ground.

  The figures are the measured ones out of ``metrics.json`` -- remember that a
  z here is a **y** there.

  - ``startisle``   -- z=0 is the **waterline**; -9.4 to +17.9.
  - ``seastack``    -- z=0 is the **waterline**; -8.7 to +27.0.
  - ``seaarch``     -- z=0 is the **waterline**; -8.7 to +19.2.
  - ``shipwreck``   -- z=0 is the **waterline**; -5.9 to +22.1, and the hull
                       is genuinely half under it rather than sitting on it.
  - ``lighthouse``  -- z=0 is the **waterline**; -8.5 to +32.8.
  - ``airship``     -- z=0 is the gondola's **keel**; -0.2 to +13.2.

  Everything below z=0 in the first five is there so the waterline cuts
  through solid rock at any angle. The scene's sea is an opaque plane, so none
  of it is ever drawn -- it is two or three layers, not a foundation.

* **deck origin** (the two things that float in mid air): z=0 is the **top
  surface**, and the mass hangs *below* it into -z. Place one at the altitude
  you want its top to be. Trees and pillars still rise into +z.

  - ``skyisland``   -- z=0 is the grass; rock hangs to -22.5, trees to +9.4.
  - ``skyruin``     -- z=0 is the broken floor; rubble hangs to -9.1, columns
                       and architrave to +11.9.

* **hanging origin** (the ``vinehang`` convention): z=0 is the **top** and the
  whole model is below it.

  - ``waterfall``   -- z=0 is the lip. It falls to -29.5 exactly, so the
                       splash lands at ``origin - 29.5``.

``skyisland`` carries a **spout**: a notched lip in its rim at local
``(x=+8.4, y=0.0, z=-0.6)``. Put a ``waterfall`` at that offset from the
island's origin and the water leaves the island where the island says it does.

The assets
----------
* startisle  -- the place you set off from: rock, a sand beach, six trees, a
                ruined arch on the knoll and a jetty out over the water.
* seastack   -- a tapering pillar of rock with a mossy cap and a stub beside
                it. The cheap one; scatter several.
* seaarch    -- two legs and a span, with a hole in it big enough to see sky
                through at two hundred metres.
* shipwreck  -- a hull rolled twenty degrees and half sunk, bow down, mast
                leaning, one torn sail on the yard.
* skyisland  -- a floating island: grass, dirt, a crooked rock spike, three
                trees and the spout the waterfall hangs off.
* waterfall  -- the water itself: crossed sheets that widen as they fall, foam
                at the lip and a splash where they end.
* skyruin    -- a fragment of floor and five columns, two of them snapped,
                hanging in the air with rubble under it.
* lighthouse -- a banded tower on a reef, with a gallery, a lit lamp room and
                a keeper's cottage.
* airship    -- a blocky envelope, fins, a slung gondola and a propeller.
"""

import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)

#: The thickness every flat sheet in this file gets. Same argument as
#: ``props_flora.LEAF``: a plane with no thickness vanishes edge-on, and a sail
#: or a waterfall seen edge-on from two hundred metres would simply blink out.
#: Bigger than the flora's 2 cm because these are bigger objects.
SHEET = 0.10


def blk(name, size, loc, mat, rot=None):
    """A box with no bevel. The unit of this entire file.

    Wrapping :func:`common.box` rather than passing ``bevel=0.0`` sixty times
    is not tidiness: the default is 0.05, and one forgotten argument is a
    hundred triangles of rounding nobody can see on scenery that is drawn as a
    silhouette.
    """
    return box(name, size, loc, mat, bevel=0.0, rot=rot)


def merge(parts, name):
    """Join the parts and **bake the survivor's own transform into the mesh**.

    ``join`` keeps the *active* object's transform and rewrites everybody
    else's geometry relative to it, so a model whose first part happened to be
    a yawed rock ends up with a node rotation in the glTF: a second
    description of where the model is, which the runtime then has to agree
    with. Applying it leaves exactly one description -- the vertices -- and it
    also means :func:`spin` and :func:`shift` below act about the origin a
    reader would expect rather than about whatever ``parts[0]`` was.
    """
    ob = join(parts, name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


def spin(ob, axis: str, deg: float):
    """Rotate an object's **mesh data** in place, about its own origin."""
    ob.data.transform(Matrix.Rotation(math.radians(deg), 4, axis))
    return ob


def shift(ob, dx=0.0, dy=0.0, dz=0.0):
    """Translate an object's mesh data. Same argument as :func:`spin`."""
    ob.data.transform(Matrix.Translation((dx, dy, dz)))
    return ob


def rocky(parts, tag, rng, mat, *, z0, z1, r0, r1, layers, wobble=0.30,
          at=(0.0, 0.0)):
    """A tapering stack of yawed, jittered boxes: this project's rock.

    ``r0``/``r1`` are half-widths at the bottom and the top, so ``r1 < r0`` is
    a stack and ``r1 > r0`` is an overhang -- which is what makes a sea stack
    look like a sea stack and a floating island look like it is floating.

    The layers deliberately **overlap** in z (each is 1.3 of its share) so the
    joint between two of them is never a visible horizontal seam right across
    the silhouette.

    ``at`` moves the whole stack in plan, and is a parameter rather than a
    caller editing ``ob.location`` afterwards because these boxes are *yawed*:
    a translation applied after the fact lands in the box's own rotated frame
    and the stack scatters.
    """
    span = (z1 - z0) / layers
    for i in range(layers):
        t = i / max(1, layers - 1)
        r = r0 + (r1 - r0) * t
        rx = r * rng.uniform(1.0 - wobble * 0.5, 1.0 + wobble * 0.5)
        ry = r * rng.uniform(1.0 - wobble * 0.5, 1.0 + wobble * 0.5)
        parts.append(blk(
            f"{tag}{i}", (rx * 2, ry * 2, span * 1.3),
            (at[0] + rng.uniform(-wobble, wobble) * r,
             at[1] + rng.uniform(-wobble, wobble) * r,
             z0 + span * (i + 0.5)),
            mat, rot=(0, 0, rng.uniform(-0.6, 0.6))))
    return parts


def terrace(parts, tag, mat, slabs, *, top=0.0, thick=1.2, step=0.06):
    """Overlapping yawed slabs making one irregular surface, no two coplanar.

    ``slabs`` is ``(width, depth, x, y, yaw)`` each. The first slab's top face
    is exactly ``top`` and every later one is ``step`` lower, which is the
    whole point: built at one height their top faces coincide, and coincident
    faces bake **black** (the same defect ``props_flora.cactus`` records at its
    elbow). Six centimetres is invisible at forty metres and is the difference
    between a lawn and a lawn with holes in it.
    """
    for i, (w, d, x, y, yaw) in enumerate(slabs):
        z = top - step * i
        parts.append(blk(f"{tag}{i}", (w, d, thick), (x, y, z - thick / 2),
                         mat, rot=(0, 0, yaw)))
    return parts


def tree(parts, tag, at, wood, leaf, *, height=6.0, spread=4.4, rng=None):
    """An oak: a trunk and three shrinking canopy boxes, yawed apart.

    Three boxes rather than one because a single cube of leaves on a stick is
    a lollipop, and the whole job of a tree at this range is to put a ragged
    edge on the top of an island.
    """
    rng = rng or random.Random(0)
    x, y, z = at
    t = 0.55
    parts.append(blk(f"{tag}t", (t, t, height), (x, y, z + height * 0.5), wood))
    for i, (w, h, dz) in enumerate(((1.00, 2.0, -0.4), (0.74, 1.7, 1.2),
                                    (0.42, 1.3, 2.5))):
        parts.append(blk(
            f"{tag}c{i}", (spread * w, spread * w * rng.uniform(0.82, 1.0), h),
            (x + rng.uniform(-0.4, 0.4), y + rng.uniform(-0.4, 0.4),
             z + height + dz),
            leaf, rot=(0, 0, rng.uniform(-0.7, 0.7))))
    return parts


# ---------------------------------------------------------------------------
# Sea level
# ---------------------------------------------------------------------------

def startisle():
    """The starting island. Origin at the **waterline**.

    Fifty metres across, because it has to read as somewhere you could set off
    from rather than a rock, and because at two hundred metres below the
    course anything smaller is a smudge. Four things give it that reading and
    none of them is the rock: the **sand rim**, which is the only bright edge
    in a scene of grey rock and blue water; the **trees**, which give the
    outline teeth; the **arch**, which is the one man-made vertical; and the
    **jetty**, which points somewhere and so implies that somebody left.
    """
    rng = random.Random(4211)
    ROCK = zone("rock", (0.44, 0.43, 0.42), rough=0.95)
    DARK = zone("stone", (0.31, 0.31, 0.33), rough=0.95)
    SAND = zone("sand", (0.86, 0.79, 0.58), rough=0.9)
    GRASS = zone("grass", (0.34, 0.60, 0.25), rough=0.9)
    WOOD = zone("wood", (0.44, 0.31, 0.19), rough=0.95)
    LEAF = zone("leaf", (0.29, 0.55, 0.22), rough=0.9)

    parts = []
    # Below the water: dark, and narrower than the beach rather than wider.
    # The first pass had a broad flat shelf under everything and the island
    # read as a *tray* with a lump on it -- so the underwater mass is now
    # something the beach sits on top of, not something it sits inside.
    rocky(parts, "foot", rng, DARK, z0=-9.0, z1=-0.5, r0=12.0, r1=17.0,
          layers=3, wobble=0.28)
    # The beach: the sand is a rim, three or four metres of it, and no more.
    parts.append(blk("shelf", (36.0, 31.0, 1.6), (0, 0, 0.05), SAND))
    parts.append(blk("spit0", (16.0, 12.0, 1.4), (15.0, -9.0, -0.35), SAND,
                     rot=(0, 0, 0.5)))
    parts.append(blk("spit1", (12.0, 14.0, 1.3), (-14.0, 9.0, -0.55), SAND,
                     rot=(0, 0, -0.4)))
    # The land: one big irregular rock mass rising *out of* the sand, which is
    # what makes it an island rather than a cake stand. Strong wobble, because
    # this is the silhouette.
    #
    # **The grass overhangs the rock it caps** (28 across a top of 24), and
    # that is the whole difference between an island and a wedding cake. Cap a
    # mass with something narrower than it and its top face shows all round as
    # a grey shelf; do it three times -- sand, rock, grass -- and you have
    # drawn three concentric plates, which is exactly what the first two
    # passes of this asset were.
    # **A capped stack's top layer has to fit under its cap in all three
    # axes**, and the jitter is part of its width: ``rocky`` offsets a layer
    # by up to ``wobble * r``, so at wobble 0.34 a 24-metre top layer reaches
    # 18 metres from the axis against a 14-metre lawn -- and the top-down
    # render showed exactly that, a grey slab lying across the grass with its
    # own top face proud of it. The top layer is therefore narrow (21 across
    # under a 31-metre lawn) and the stack tops out at 3.8 against a lawn
    # underside of 3.0. The rock that is *supposed* to show gets to be an
    # outcrop, placed on purpose.
    rocky(parts, "land", rng, ROCK, z0=-1.0, z1=3.6, r0=15.0, r1=10.5,
          layers=3, wobble=0.22)
    terrace(parts, "lawn", GRASS, (
        (31.0, 27.0, 0.0, 0.0, 0.0),
        (18.0, 15.0, 7.5, 6.0, 0.6),
        (15.0, 17.0, -8.0, -4.5, -0.5),
    ), top=4.6, thick=1.6)
    for i, (w, d, x, y, z, rot) in enumerate((
            (4.6, 3.8, 9.0, -2.0, 5.0, 0.5),
            (3.2, 3.6, -7.5, 6.5, 4.9, -0.3))):
        parts.append(blk(f"outcrop{i}", (w, d, 2.2), (x, y, z), ROCK,
                         rot=(0, 0, rot)))
    # The knoll: the arch stands on it, so the arch is skylined instead of
    # being lost against the trees behind it.
    rocky(parts, "knoll", rng, ROCK, z0=3.8, z1=7.2, r0=6.5, r1=4.6, layers=2,
          wobble=0.16)
    # Wider than the knoll it caps, for the third time in this asset and the
    # same reason: a cap narrower than its mass leaves a grey ring.
    terrace(parts, "knolltop", GRASS, (
        (16.0, 14.0, -1.0, 1.0, 0.3),
        (9.5, 10.0, 2.0, -2.0, -0.4),
    ), top=7.8, thick=1.3)

    for i, (x, y, z, h, s) in enumerate((
            (10.5, -6.0, 4.4, 8.0, 6.0), (12.5, 5.0, 4.4, 6.2, 5.0),
            (-10.5, -8.0, 4.4, 7.2, 5.6), (-11.5, 4.0, 4.4, 5.6, 4.4),
            (2.0, -9.5, 4.4, 6.8, 5.2), (-3.5, 3.5, 7.6, 6.0, 4.8))):
        tree(parts, f"tree{i}", (x, y, z), WOOD, LEAF, height=h, spread=s,
             rng=rng)

    # The ruin: one whole leg, one snapped, and a lintel that only reaches
    # halfway across. A complete arch reads as a gate somebody maintains.
    # Eight metres of leg rather than six, because on the first pass it was
    # shorter than the trees around it and simply disappeared into them.
    parts.append(blk("leg0", (2.2, 2.2, 8.0), (-4.8, 2.4, 11.6), DARK))
    parts.append(blk("legcap", (3.0, 3.0, 0.9), (-4.8, 2.4, 16.0), DARK))
    parts.append(blk("leg1", (2.0, 2.0, 4.6), (2.6, 2.4, 9.9), DARK,
                     rot=(0, 0.09, 0)))
    parts.append(blk("legbreak", (1.9, 1.7, 1.2), (3.1, 2.1, 12.6), DARK,
                     rot=(0.3, 0.25, 0.4)))
    parts.append(blk("lintel", (6.2, 2.0, 1.5), (-3.0, 2.4, 17.0), DARK,
                     rot=(0, -0.05, 0)))
    parts.append(blk("fallen", (4.6, 1.8, 1.4), (5.0, 0.2, 8.6), DARK,
                     rot=(0, 0.12, 0.7)))

    # The jetty. It has to *touch the beach* -- the first pass started it
    # beyond the sand and it read as a bench floating on the water next to an
    # island, which is the only way a jetty can fail.
    parts.append(blk("deck", (4.2, 18.0, 0.5), (3.0, -22.0, 1.35), WOOD))
    for i in range(4):
        y = -16.0 - i * 4.4
        for s in (-1, 1):
            parts.append(blk(f"post{i}{s}", (0.6, 0.6, 3.4),
                             (3.0 + s * 1.6, y, -0.3), WOOD))
    parts.append(blk("bollard", (0.8, 0.8, 1.6), (3.0, -30.2, 2.3), WOOD))
    return merge(parts, "startisle")


def seastack():
    """A lone pillar of rock. Origin at the **waterline**.

    Wider at the top than at the waist (``r1 > r0`` through the middle
    course), because a sea stack is what the sea has *not* eaten yet and the
    sea eats at the waterline. The stub beside it turns one object into a
    group, which is worth more at distance than any amount of detail on the
    pillar.
    """
    rng = random.Random(902)
    ROCK = zone("rock", (0.47, 0.45, 0.42), rough=0.95)
    DARK = zone("stone", (0.30, 0.30, 0.32), rough=0.95)
    MOSS = zone("grass", (0.33, 0.56, 0.24), rough=0.9)

    parts = []
    # The underwater foot is narrow on purpose. An opaque sea plane hides
    # everything below it anyway, so a wide one buys nothing and, on the first
    # pass, gave the stack a visible plinth wherever the waterline cut it.
    rocky(parts, "base", rng, DARK, z0=-8.0, z1=1.2, r0=6.0, r1=5.4, layers=2,
          wobble=0.26)
    rocky(parts, "shaft", rng, ROCK, z0=1.0, z1=17.0, r0=4.6, r1=5.2, layers=5,
          wobble=0.30)
    rocky(parts, "head", rng, ROCK, z0=16.5, z1=26.4, r0=5.0, r1=3.6, layers=3,
          wobble=0.34)
    # The cap has to be *bigger* than the rock it caps and sit down into it,
    # or it is a green postage stamp balanced on a corner -- which is what the
    # first pass was, at 6.4 across a 7-metre head.
    terrace(parts, "cap", MOSS, (
        (7.8, 7.0, 0.3, -0.4, 0.4),
        (5.6, 6.2, -1.6, 1.2, -0.5),
    ), top=27.0, thick=2.0)
    # Two ledges: they catch the sun on one face and put a horizontal into a
    # shape that is otherwise all vertical.
    parts.append(blk("ledge0", (8.6, 3.4, 0.9), (1.4, 1.2, 11.0), ROCK,
                     rot=(0, 0, 0.9)))
    parts.append(blk("ledge1", (3.4, 7.8, 0.8), (-1.8, 0.6, 19.5), ROCK,
                     rot=(0, 0, -0.6)))
    # The stub.
    rocky(parts, "stub", rng, DARK, z0=-6.0, z1=6.5, r0=4.4, r1=2.4, layers=3,
          wobble=0.28, at=(11.5, -6.5))
    return merge(parts, "seastack")


def seaarch():
    """A rock arch. Origin at the **waterline**.

    The one asset here whose whole point is a **hole**: at two hundred metres
    the sky through the opening is what tells you this is not another stack,
    so the opening is twelve metres wide and eleven tall, which is most of the
    thing. The span is four boxes stepping up and over rather than a curve,
    because four boxes at that range *is* a curve and costs eight triangles.
    """
    rng = random.Random(7717)
    ROCK = zone("rock", (0.46, 0.44, 0.41), rough=0.95)
    DARK = zone("stone", (0.29, 0.29, 0.31), rough=0.95)
    MOSS = zone("grass", (0.32, 0.55, 0.23), rough=0.9)

    parts = []
    span = 11.0          # centre-to-centre of the legs
    for s, tag in ((-1, "l"), (1, "r")):
        rocky(parts, f"{tag}foot", rng, DARK, z0=-8.0, z1=0.8,
              r0=4.8, r1=4.4, layers=2, wobble=0.22, at=(s * span, 0.0))
        rocky(parts, f"{tag}leg", rng, ROCK, z0=0.6, z1=13.5,
              r0=4.2, r1=3.4, layers=4, wobble=0.24, at=(s * span, 0.0))
    # The span: the two shoulders lean inward, the two crown blocks are level.
    parts.append(blk("sh0", (6.0, 6.2, 3.4), (-9.0, 0.0, 14.6), ROCK,
                     rot=(0, -0.34, 0.1)))
    parts.append(blk("sh1", (6.0, 6.2, 3.4), (9.0, 0.0, 14.6), ROCK,
                     rot=(0, 0.34, -0.1)))
    parts.append(blk("crown0", (7.4, 6.6, 3.0), (-3.4, 0.3, 17.2), ROCK,
                     rot=(0, -0.06, -0.15)))
    parts.append(blk("crown1", (7.4, 6.6, 3.0), (3.4, -0.3, 17.4), ROCK,
                     rot=(0, 0.05, 0.18)))
    # Moss on the crown, in two pieces at different heights: one slab right
    # across the span is a lid, and a lid is the one thing that would say
    # somebody built this.
    terrace(parts, "moss", MOSS, (
        (7.6, 5.6, -2.6, 0.4, 0.12),
        (5.4, 4.8, 3.4, -0.6, -0.3),
    ), top=19.2, thick=0.9)
    # A small stack outboard, so the arch is a coastline and not an exhibit.
    rocky(parts, "out", rng, DARK, z0=-6.0, z1=8.5, r0=3.6, r1=2.0, layers=3,
          wobble=0.30, at=(-21.0, 5.0))
    return merge(parts, "seaarch")


def shipwreck():
    """A half-sunk ship. Origin at the **waterline**.

    Built level and bow-forward, then rolled 21 degrees onto its starboard
    side, pitched 7 down by the bow, and dropped 2.4 m so the sea cuts through
    the hull. Doing it that way round -- one :func:`spin` on the finished mesh
    rather than a tilt argument on forty boxes -- is why the deck, the ribs
    and the mast still agree with each other after the tilt.

    The mast is the read. A hull at this size is a dark lump on the water; a
    leaning mast with a torn sail on it is a shipwreck at any distance the
    hull is still a few pixels wide.
    """
    HULL = zone("hull", (0.30, 0.22, 0.16), rough=0.95)
    DECK = zone("wood", (0.62, 0.47, 0.30), rough=0.95)
    TRIM = zone("trim", (0.20, 0.15, 0.13), rough=0.95)
    SAIL = zone("canvas", (0.80, 0.76, 0.66), rough=0.98)

    parts = []
    # Hull sections along +Y (the bow). Half-widths taper to a point forward.
    for i, (y, hw, h, z) in enumerate((
            (-10.0, 3.1, 5.2, 0.6), (-5.6, 3.6, 5.9, 0.3),
            (-0.6, 3.6, 6.1, 0.2), (4.4, 3.0, 5.7, 0.3),
            (8.6, 2.1, 5.1, 0.7), (11.6, 1.1, 4.3, 1.2))):
        parts.append(blk(f"hull{i}", (hw * 2, 5.2 if i else 4.0, h),
                         (0, y, z), HULL))
    parts.append(blk("keel", (1.2, 21.0, 0.9), (0, -0.5, -2.4), TRIM))
    # A pale strake down each flank. The hull is one brown mass otherwise, and
    # a brown mass on brown water at two hundred metres is nothing at all.
    for i, s in enumerate((-1, 1)):
        parts.append(blk(f"strake{i}", (0.35, 20.0, 0.8),
                         (s * 3.5, -1.0, 1.3), DECK))
    parts.append(blk("rail0", (0.5, 20.0, 0.6), (-3.4, -1.0, 2.5), TRIM))
    parts.append(blk("rail1", (0.5, 20.0, 0.6), (3.4, -1.0, 2.5), TRIM))
    parts.append(blk("deck", (5.8, 11.0, 0.5), (0, 3.0, 2.2), DECK))
    # Stern castle, and the hole amidships where the deck has gone.
    parts.append(blk("castle", (5.4, 4.6, 2.8), (0, -8.4, 3.6), DECK))
    parts.append(blk("castletop", (5.8, 5.0, 0.4), (0, -8.4, 5.2), TRIM))
    for i, y in enumerate((-5.4, -3.6, -1.8, 0.0)):
        for s in (-1, 1):
            parts.append(blk(f"rib{i}{s}", (0.4, 0.5, 3.0 + 0.4 * i),
                             (s * 2.9, y, 3.4 + 0.2 * i), TRIM,
                             rot=(0, s * 0.10, 0)))
    parts.append(blk("bowsprit", (0.5, 6.0, 0.5), (0, 14.4, 3.4), TRIM,
                     rot=(-0.38, 0, 0)))

    # The mast, leaning aft. Every part of the rig is placed on the same lean
    # so the yard stays square to the mast rather than to the world.
    #
    # Twenty-two metres against a twenty-four metre hull, which is out of
    # scale for a real ship of this size and is the point: at two hundred
    # metres the hull is a dark smudge on the water and the *mast* is the
    # whole read. The first pass built it at fifteen and the wreck was a raft.
    lean = 0.46
    base = (0.0, -1.0, 2.4)
    ln = 22.0

    def on_mast(t):
        """A point ``t`` of the way up the leaning mast."""
        return (base[0], base[1] - math.sin(lean) * ln * t,
                base[2] + math.cos(lean) * ln * t)

    mid = on_mast(0.5)
    parts.append(blk("mast", (1.0, 1.0, ln), mid, TRIM, rot=(lean, 0, 0)))
    yard = on_mast(0.58)
    parts.append(blk("yard", (12.0, 0.5, 0.5), yard, TRIM, rot=(lean, 0, 0)))
    parts.append(blk("nest", (2.0, 2.0, 1.0), on_mast(0.84), TRIM,
                     rot=(lean, 0, 0)))
    # No second yard above the crow's nest. There was one, and a short spar
    # crossing the mast just above a box reads as a crucifix rather than as
    # rigging -- which is what the render said and no measurement could.
    parts.append(blk("topmast", (0.5, 0.5, 3.0), on_mast(1.02), TRIM,
                     rot=(lean, 0, 0)))
    # Three rags of sail, all different and all hanging off centre: a sail
    # that is symmetrical is a sail, and this ship has not had one for years.
    # They are big -- the biggest is five metres by seven -- because canvas is
    # the only pale thing on a brown wreck and pale is what carries.
    parts.append(blk("sail0", (5.0, SHEET, 7.0),
                     (-2.4, yard[1] + 0.4, yard[2] - 3.6), SAIL,
                     rot=(0.06, 0, 0)))
    parts.append(blk("sail1", (3.0, SHEET, 4.2),
                     (3.2, yard[1] + 0.15, yard[2] - 2.2), SAIL,
                     rot=(-0.09, 0, 0)))
    parts.append(blk("sail2", (2.2, SHEET, 2.6),
                     (-1.0, yard[1] - 0.35, yard[2] - 8.0), SAIL,
                     rot=(0.14, 0, 0.2)))
    # A spar in the water, so there is wreckage and not just a wreck.
    parts.append(blk("spar", (0.5, 7.0, 0.5), (7.5, -13.0, 0.1), TRIM,
                     rot=(0.05, 0, 0.5)))

    ob = merge(parts, "shipwreck")
    spin(ob, "Y", 21.0)
    spin(ob, "X", -7.0)
    # 1.6 m, not 2.4. At 2.4 the hull's own top edge sat *at* the waterline,
    # so everything below the deck was under the sea plane and the wreck read
    # as a raft with a mast on it. Half sunk means half.
    return shift(ob, dz=-1.6)


def lighthouse():
    """A lighthouse on a reef. Origin at the **waterline**.

    Thirty-four metres, banded red and white, which is the only strongly
    chromatic thing in this file and is meant to be: it is the object the eye
    finds first over an expanse of grey rock and blue water, and the bands are
    what survive when the tower is four pixels wide.

    The taper is four stacked sections rather than a cone -- the same trade as
    the arch's span, and the horizontal joints double as the courses a real
    tower is built in.
    """
    rng = random.Random(1381)
    ROCK = zone("rock", (0.42, 0.41, 0.40), rough=0.95)
    DARK = zone("stone", (0.28, 0.28, 0.30), rough=0.95)
    WHITE = zone("wall", (0.90, 0.89, 0.86), rough=0.8)
    BAND = zone("trim", (0.72, 0.22, 0.18), rough=0.8)
    GLASS = zone("glow", (0.98, 0.92, 0.62), rough=0.25)

    parts = []
    rocky(parts, "reef", rng, DARK, z0=-8.0, z1=1.0, r0=10.5, r1=7.5, layers=3,
          wobble=0.24)
    rocky(parts, "rock", rng, ROCK, z0=0.8, z1=5.4, r0=7.0, r1=5.0, layers=2,
          wobble=0.18)

    # The tower: alternating white and red courses on a taper.
    z = 5.0
    for i, (w, h) in enumerate(((6.2, 4.4), (5.6, 4.2), (5.0, 4.0),
                                (4.4, 3.8), (3.9, 3.6))):
        parts.append(blk(f"course{i}", (w, w, h), (0, 0, z + h / 2),
                         WHITE if i % 2 == 0 else BAND))
        z += h
    # Gallery, lamp room, roof. The gallery's overhang is what stops the top
    # being the same silhouette as the shaft with a lid on.
    parts.append(blk("gallery", (6.4, 6.4, 0.6), (0, 0, z + 0.3), DARK))
    for i, s in enumerate(((-1, 0), (1, 0), (0, -1), (0, 1))):
        parts.append(blk(f"rail{i}",
                         (6.2 if s[1] else 0.35, 6.2 if s[0] else 0.35, 1.0),
                         (s[0] * 3.0, s[1] * 3.0, z + 1.1), DARK))
    parts.append(blk("lamp", (3.4, 3.4, 3.0), (0, 0, z + 2.1), GLASS))
    parts.append(blk("lampcap", (3.8, 3.8, 0.5), (0, 0, z + 3.8), DARK))
    for i, (w, h) in enumerate(((3.0, 0.9), (2.0, 0.8), (1.0, 0.7))):
        parts.append(blk(f"roof{i}", (w, w, h), (0, 0, z + 4.3 + i * 0.8),
                         BAND))
    parts.append(blk("finial", (0.35, 0.35, 1.2), (0, 0, z + 7.2), DARK))

    # The keeper's cottage, downhill and off-axis. Pushed a good way clear of
    # the tower: built tight against it, it read as a lump on the base rather
    # than as a second building, which is the only thing it is for.
    parts.append(blk("cotrock", (9.0, 8.0, 3.0), (9.6, -5.0, 3.4), ROCK,
                     rot=(0, 0, 0.35)))
    parts.append(blk("cot", (5.6, 4.4, 3.2), (9.6, -5.0, 6.4), WHITE,
                     rot=(0, 0, 0.35)))
    for i, (w, h) in enumerate(((5.9, 0.7), (4.2, 0.7), (2.5, 0.7))):
        parts.append(blk(f"cotroof{i}", (w, 4.7, h),
                         (9.6, -5.0, 8.1 + i * 0.65), BAND, rot=(0, 0, 0.35)))
    parts.append(blk("cotdoor", (1.1, 0.3, 1.9), (7.8, -6.8, 5.8), DARK,
                     rot=(0, 0, 0.35)))
    parts.append(blk("jetty", (2.6, 8.0, 0.4), (-4.0, 9.0, 1.4), DARK,
                     rot=(0, 0, -0.2)))
    return merge(parts, "lighthouse")


# ---------------------------------------------------------------------------
# Mid air
# ---------------------------------------------------------------------------

def skyisland():
    """A floating island. Origin at the **top surface** (the grass).

    Everything hangs *below* z=0 -- twenty-one metres of it -- which is the
    inverse of every other convention in the project and is deliberate: what a
    placer knows about a floating island is the altitude it wants the island's
    deck to be at, and the spike underneath is however long it happens to be.

    The underside is the asset. Seen from a tower you are mostly *above* or
    *level with* these, so the spike, its overhang at the rim and the spout
    are what is on screen; the grass is a green line on top of them. Hence the
    first rock course being **wider** than the dirt above it.

    The spout is a notch in the rim at ``(x=+8.4, y=0.0, z=-0.6)``. Hang a
    ``waterfall`` there.
    """
    rng = random.Random(6608)
    GRASS = zone("grass", (0.35, 0.61, 0.26), rough=0.9)
    DIRT = zone("dirt", (0.46, 0.33, 0.21), rough=0.95)
    ROCK = zone("rock", (0.45, 0.43, 0.41), rough=0.95)
    WOOD = zone("wood", (0.44, 0.31, 0.19), rough=0.95)
    LEAF = zone("leaf", (0.28, 0.54, 0.22), rough=0.9)

    parts = []
    terrace(parts, "lawn", GRASS, (
        (23.0, 20.0, 0.0, 0.0, 0.0),
        (13.0, 12.0, 6.0, 5.0, 0.55),
        (11.0, 13.0, -6.5, -4.0, -0.45),
    ), top=0.0, thick=1.4)
    # The dirt stops *under* the lawn rather than level with it. On the first
    # pass its top sat above the lawn's underside and poked through the gaps
    # between the three lobes -- as fully-occluded faces, so they baked black
    # and read as holes in the island.
    rocky(parts, "dirt", rng, DIRT, z0=-3.6, z1=-1.5, r0=10.6, r1=11.4,
          layers=2, wobble=0.16)
    # The overhang: wider than the dirt, so the island is undercut and reads
    # as torn out of the ground rather than sawn off it.
    rocky(parts, "brow", rng, ROCK, z0=-6.2, z1=-3.2, r0=10.0, r1=11.8,
          layers=2, wobble=0.22)
    # The spike is the asset -- seen from a tower you are level with these and
    # it is most of what is on screen. **Two stages, not one**: a linear taper
    # from ten metres to one over eight layers spends its width evenly and
    # comes out as an upside-down wedding cake, because every layer's top face
    # shows all round as a shelf. A short fat shoulder that loses most of the
    # width at once, then a long thin tail that barely loses any, is a spike.
    rocky(parts, "shoulder", rng, ROCK, z0=-10.5, z1=-5.5, r0=6.0, r1=9.2,
          layers=2, wobble=0.40)
    rocky(parts, "spike", rng, ROCK, z0=-22.0, z1=-9.5, r0=0.8, r1=5.4,
          layers=4, wobble=0.50)

    # The spout: a lip proud of the rim with a notch of grass behind it, so
    # the water has somewhere to come from.
    parts.append(blk("lip", (2.6, 4.2, 0.9), (8.4, 0.0, -0.7), ROCK))
    parts.append(blk("chan", (3.4, 2.2, 0.5), (6.4, 0.0, -0.35), ROCK))
    parts.append(blk("pool", (4.4, 3.6, 0.4), (3.6, 0.0, -0.5), DIRT))

    for i, (x, y, h, s) in enumerate(((-5.5, 3.5, 6.2, 4.6),
                                      (4.0, -6.0, 5.0, 3.8),
                                      (-3.0, -3.5, 4.2, 3.2))):
        tree(parts, f"tree{i}", (x, y, 0.0), WOOD, LEAF, height=h, spread=s,
             rng=rng)
    parts.append(blk("boulder", (3.4, 2.8, 2.2), (6.5, 6.0, 0.6), ROCK,
                     rot=(0, 0.12, 0.6)))
    return merge(parts, "skyisland")


def waterfall():
    """The water pouring off something. Origin at the **top** (the lip).

    The ``vinehang`` convention: everything is below z=0, thirty metres of it,
    so it is hung from the thing it falls off rather than stood under it.

    Crossed sheets, like every plant in the project, and for the same reason
    -- a single plane is invisible from ninety degrees away and these are seen
    from wherever the course happens to be. The narrow sheet is deliberately
    *not* the same width as the broad one, because two equal crossed quads
    read as an X from above.

    It **widens and wanders** as it falls (each segment is a little broader
    and a little offset), which is the whole difference between water and a
    white ribbon, and it ends in a splash rather than in mid air.
    """
    WATER = zone("water", (0.42, 0.66, 0.88), rough=0.2)
    FOAM = zone("foam", (0.93, 0.96, 0.98), rough=0.35)

    parts = []
    parts.append(blk("lip", (4.4, 2.4, 0.35), (0, 0, -0.18), FOAM))

    # The fall is **long boxes, not a stack of segments**. Chopping it into
    # seven and offsetting each one was the first pass, and what it produced
    # was a pile of misaligned blue plates: every segment boundary is a step
    # in the silhouette, and a waterfall has no steps in it. Two overlapping
    # sheets per axis -- one the whole drop, one covering the lower two thirds
    # and wider -- give the widening profile in four boxes and no seams.
    #
    # The two broad sheets are **offset a third of a metre in y**, and that is
    # not styling: built at y=0 with the same thickness they are two coplanar
    # pairs of faces over the whole of the lower fall, and coplanar faces bake
    # black. The first render of this version had a black stripe straight down
    # the middle of the water.
    drop = 29.0
    for tag, w, d, h, z, oy in (("core", 4.0, SHEET, drop, -drop / 2, 0.0),
                                ("skirt", 6.4, SHEET, drop * 0.62,
                                 -drop + drop * 0.31, 0.34)):
        parts.append(blk(f"{tag}b", (w, d, h), (0.0, oy, z), WATER))
        # The crossed sheet is deliberately narrower than the broad one: two
        # equal quads at right angles read as an X from above, and these are
        # looked down on as often as not.
        parts.append(blk(f"{tag}t", (d, w * 0.66, h), (oy * 0.9, 0.0, z),
                         WATER, rot=(0, 0, 0.18)))
    # Foam: at the lip, in two streaks proud of the face where the fall breaks
    # up, and in the splash. A fall that is one flat colour top to bottom is a
    # sheet of plastic. The streaks stand 6 cm off the sheet so they are not
    # coplanar with it -- coincident faces bake black.
    parts.append(blk("streak0", (1.5, SHEET, 9.0), (0.7, -0.14, -11.0), FOAM))
    parts.append(blk("streak1", (1.0, SHEET, 6.5), (-1.4, 0.50, -21.5), FOAM))
    parts.append(blk("streak2", (SHEET, 1.1, 7.0), (0.42, 0.8, -17.0), FOAM))
    # The splash: flat and wide, and the fall runs *into* it rather than
    # standing on it -- a 1.4 m slab under the water read as a plinth.
    terrace(parts, "splash", FOAM, (
        (10.4, 9.0, 0.2, 0.0, 0.3),
        (7.4, 6.4, -0.4, 0.3, -0.5),
    ), top=-28.2, thick=0.8, step=0.5)
    for i, (x, y, s, z) in enumerate(((3.8, 1.4, 2.6, -27.2),
                                      (-3.0, -2.4, 2.2, -26.6),
                                      (1.0, 3.6, 1.8, -25.9),
                                      (-2.2, 2.8, 1.5, -27.6))):
        parts.append(blk(f"mist{i}", (s, s * 0.85, s * 0.55), (x, y, z), FOAM,
                         rot=(0, 0, i * 0.7)))
    return merge(parts, "waterfall")


def skyruin():
    """A fragment of a building, hanging in the air. Origin at the **floor**.

    Same convention as ``skyisland``: z=0 is the top of the broken floor and
    the rubble hangs to -7, so a placer says where the floor should be.

    Pale sandstone against a blue sky on purpose -- it is the one thing in the
    air that is meant to be *bright*, so it separates from cloud rather than
    reading as more of it. Five columns and only three of them standing: the
    two snapped ones are what make it a ruin instead of a temple, and they are
    the reason the roofline has a gap in it.
    """
    rng = random.Random(3050)
    STONE = zone("stone", (0.80, 0.75, 0.62), rough=0.9)
    TRIM = zone("trim", (0.63, 0.58, 0.47), rough=0.9)
    MOSS = zone("grass", (0.34, 0.52, 0.27), rough=0.9)

    parts = []
    # The floor, in four overlapping slabs at different yaws: the edge has to
    # be broken, and a broken edge is the only thing that says this is a piece
    # of something rather than a platform somebody built. Stepped, because
    # four coplanar tops baked as black bands right across it.
    terrace(parts, "floor", STONE, (
        (15.0, 11.0, 0.0, 0.0, 0.0),
        (8.0, 7.0, 5.5, 3.0, 0.5),
        (7.0, 8.0, -5.0, -3.5, -0.6),
        (6.0, 5.0, 2.0, -5.0, 0.25),
    ), top=0.0, thick=1.5)
    parts.append(blk("step", (9.0, 2.2, 0.5), (0.0, 5.6, 0.25), TRIM))
    # The underside: this thing is seen from below and from level with it far
    # more often than from above, so the hanging mass is worth as much as the
    # columns are.
    # Same two-stage taper as the sky island's spike, and for the same reason:
    # an even taper over four layers is four visible shelves.
    rocky(parts, "rub", rng, TRIM, z0=-3.4, z1=-1.2, r0=4.4, r1=6.4, layers=2,
          wobble=0.36)
    rocky(parts, "tail", rng, TRIM, z0=-7.2, z1=-3.0, r0=1.2, r1=3.8, layers=2,
          wobble=0.46)
    for i, (x, y, z, s) in enumerate(((5.0, -2.0, -5.4, 2.4),
                                      (-3.5, 2.5, -6.8, 1.8),
                                      (0.5, -4.0, -4.2, 2.8),
                                      (-1.5, 1.5, -8.2, 1.4))):
        parts.append(blk(f"chunk{i}", (s, s * 0.85, s * 0.9), (x, y, z), TRIM,
                         rot=(0.3, 0.2, rng.uniform(0, 1.2))))

    # (x, y, height, snapped?)
    for i, (x, y, h, snapped) in enumerate((
            (-5.2, -3.2, 9.6, False), (-5.2, 3.2, 9.0, False),
            (5.2, 3.2, 8.8, False), (5.2, -3.2, 4.2, True),
            (0.0, -4.6, 1.8, True))):
        parts.append(blk(f"base{i}", (2.2, 2.2, 0.6), (x, y, 0.3), TRIM))
        parts.append(blk(f"col{i}", (1.5, 1.5, h), (x, y, 0.6 + h / 2), STONE))
        if snapped:
            # A jagged top: two small blocks leaning off the break.
            parts.append(blk(f"break{i}", (1.4, 1.0, 0.8),
                             (x + 0.3, y - 0.2, 0.9 + h), STONE,
                             rot=(0.35, 0.2, 0.4)))
        else:
            parts.append(blk(f"cap{i}", (2.3, 2.3, 0.7), (x, y, 0.95 + h),
                             TRIM))
    # The architrave spans the two whole columns on the -X side only, which is
    # why the ruin has a top-left corner and nothing else.
    parts.append(blk("beam", (2.0, 8.4, 1.3), (-5.2, 0.0, 11.2), TRIM))
    parts.append(blk("beam2", (5.0, 1.9, 1.2), (-3.4, 3.2, 11.1), TRIM))
    parts.append(blk("fallen", (1.4, 5.2, 1.2), (3.0, 0.5, 0.6), TRIM,
                     rot=(0, 0.08, 0.6)))
    # Moss sunk *into* the floor rather than laid on it: a slab resting on a
    # surface leaves a hairline gap that bakes as a black outline, which at
    # distance is a rectangle drawn round the moss.
    parts.append(blk("moss0", (6.0, 4.5, 0.5), (1.5, 1.0, -0.16), MOSS,
                     rot=(0, 0, 0.4)))
    parts.append(blk("moss1", (3.4, 3.0, 0.5), (-4.0, -2.0, -0.22), MOSS,
                     rot=(0, 0, -0.3)))
    return merge(parts, "skyruin")


def airship():
    """An airship. Origin at the **gondola's keel**, all of it above.

    Kept to the ground-origin convention rather than the deck one even though
    it flies, because the thing a placer wants to say about an airship is the
    altitude of the *ship*, and its keel is the lowest point of it.

    The envelope is six boxes tapering both ways, which at this range is an
    ellipsoid for a tenth of the triangles, and the fins are what make it an
    airship rather than a whale -- they are the only sharp edges on it, so
    they are oversized.
    """
    ENV = zone("wall", (0.86, 0.83, 0.76), rough=0.85)
    STRIPE = zone("trim", (0.70, 0.34, 0.22), rough=0.8)
    WOOD = zone("wood", (0.42, 0.30, 0.19), rough=0.95)
    METAL = zone("metal", (0.35, 0.36, 0.40), rough=0.5)
    GLASS = zone("glow", (0.72, 0.86, 0.94), rough=0.25)

    parts = []
    cz = 8.4
    # The envelope, six boxes tapering both ways. Colour is carried by whole
    # *sections* -- nose and tail -- plus one band round the waist, and that
    # is a correction: the first pass ran a single stripe down each flank at a
    # fixed x, and since the envelope is only that wide amidships the stripe
    # hung a metre outside the hull at both ends like a plank nailed through
    # the ship.
    # Nine sections on an **ellipse** rather than six widths typed in. Typed
    # widths jump -- 1.6, 3.6, 5.4 -- and every jump is a step in the
    # silhouette, so the envelope read as a stack of crates. Solving for the
    # width instead makes the steps even and small, which at this range is a
    # spindle.
    half, wmax, n = 11.5, 5.4, 9
    for i in range(n):
        t = -1.0 + 2.0 * (i + 0.5) / n
        w = wmax * math.sqrt(max(0.055, 1.0 - t * t))
        parts.append(blk(f"env{i}", (w, 2.0 * half / n * 1.16, w * 1.02),
                         (0, t * half, cz),
                         STRIPE if i in (0, n - 1) else ENV))
    # A quarter of a metre proud of the section it rings, not four
    # centimetres: two same-facing surfaces that close together bake as one
    # dark smear rather than as a band with a lit edge.
    parts.append(blk("band", (6.0, 1.6, 6.05), (0, 1.3, cz), STRIPE))
    parts.append(blk("nose", (0.9, 1.6, 0.9), (0, 12.0, cz), STRIPE))

    # Fins: one upper, one lower, two lateral, all at the tail.
    parts.append(blk("finv0", (0.35, 4.2, 3.4), (0, -8.6, cz + 2.6), STRIPE,
                     rot=(0.25, 0, 0)))
    parts.append(blk("finv1", (0.35, 4.0, 3.0), (0, -8.6, cz - 2.4), STRIPE,
                     rot=(-0.25, 0, 0)))
    for s in (-1, 1):
        parts.append(blk(f"finh{s}", (3.2, 4.0, 0.35), (s * 2.4, -8.6, cz),
                         STRIPE, rot=(0, s * 0.25, 0)))

    # The gondola, slung under it on four cables.
    parts.append(blk("hull", (2.8, 7.4, 1.9), (0, 1.0, 1.1), WOOD))
    parts.append(blk("hullkeel", (1.8, 6.0, 0.7), (0, 1.0, 0.2), WOOD))
    parts.append(blk("cabin", (2.4, 4.2, 1.5), (0, 0.4, 2.7), WOOD))
    parts.append(blk("cabinroof", (2.8, 4.6, 0.35), (0, 0.4, 3.6), METAL))
    for s in (-1, 1):
        parts.append(blk(f"win{s}", (0.2, 3.4, 0.7), (s * 1.25, 0.4, 2.8),
                         GLASS))
    parts.append(blk("prow", (1.4, 1.6, 1.0), (0, 4.6, 2.4), GLASS,
                     rot=(-0.2, 0, 0)))
    for i, (x, y) in enumerate(((-1.2, 4.0), (1.2, 4.0), (-1.2, -2.0),
                                (1.2, -2.0))):
        parts.append(blk(f"cable{i}", (0.16, 0.16, 3.4), (x, y, 4.4), METAL,
                         rot=(0, x * 0.05, 0)))

    # Propeller on a boom off the stern: a hub and two blades, so it is a disc
    # edge-on and a cross face-on and never nothing.
    parts.append(blk("boom", (0.4, 3.0, 0.4), (0, -3.6, 2.2), METAL))
    parts.append(cylinder("hub", 0.42, 0.7, (0, -5.2, 2.2), METAL,
                          vertices=6, rot=(math.pi / 2, 0, 0)))
    for i, a in enumerate((0.0, math.pi / 2)):
        parts.append(blk(f"blade{i}", (0.5 + 3.0 * math.cos(a), 0.18,
                                       0.5 + 3.0 * math.sin(a)),
                         (0, -5.5, 2.2), METAL))
    parts.append(blk("rudder", (0.3, 1.8, 2.0), (0, -6.6, 3.0), WOOD,
                     rot=(0, 0, 0)))
    return merge(parts, "airship")


# The light map sizes are set by how much *surface* an asset has, not by how
# important it is: a fifty-metre island at 256 is four centimetres a texel and
# the AO under its trees turns into a grey smudge. The small ones stay at 256
# because doubling a bake nobody can see the result of is forty seconds a
# rebuild for nothing.
for name, builder, res in (
    ("startisle", startisle, 512),
    ("seastack", seastack, 256),
    ("seaarch", seaarch, 256),
    ("shipwreck", shipwreck, 256),
    ("lighthouse", lighthouse, 512),
    ("skyisland", skyisland, 512),
    ("waterfall", waterfall, 256),
    ("skyruin", skyruin, 256),
    ("airship", airship, 256),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
