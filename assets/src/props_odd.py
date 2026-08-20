"""Oddities: the things on a terrace that are worth *looking at*.

``props_mc.py`` and ``props_flora.py`` are dressing -- a torch, a tuft, a
fence -- and they are meant to disappear into a place. ``props_land.py`` is
the parts a *landmark* needs. ``props_world.py`` is the other end of the
range: scenery at forty to three hundred metres, where a model is its
silhouette and nothing else. This file is the gap in the middle, and it is a
different problem from all three.

These are read at **five to thirty metres**, by a camera moving past them at
seven metres a second, and there is one of them every level or two. So:

* **A hole, a top, or a joke.** Every asset here is one of three things and
  says which: something the course can be steered *through*, something a
  landing can sit *on*, or something that is simply odd to run past. A piece
  that is none of those is furniture, and furniture already has two files.
* **Detail, but only where the silhouette already worked.** At ten metres a
  bucket on a scarecrow's head reads and a bevel does not, so everything here
  is still square-edged boxes (:func:`blk`) and six- to eight-sided prisms.
  What is spent instead is *parts*: a broken minecart is only funny if you
  can see that a wheel has come off.
* **One draw call each.** Everything is joined into a single mesh, like every
  other asset in the project.

And the rule this directory has now learned three times -- ``props_flora.
cactus`` at its elbow, ``props_world.terrace`` on an island lawn, and once
more here on a cake: **no two overlapping slabs may share a top face.** Two
coplanar faces have no answer for a ray, and the bake comes back with hard
black rectangles across them that read as holes punched through the model.
:func:`plates` steps each slab a few centimetres below the last, which is
also what a cut cake looks like. The same care applies to anything *resting*
on a surface -- a slab laid exactly on a floor leaves a hairline the bake
draws as a black outline round it -- so stacked parts here always overlap by
a few centimetres and never merely abut.

Local axes are the project's: X across, Y along, **Z up**. The exporter
converts to glTF's Y-up, so a Z here is a Y in ``metrics.json``.

Origin convention
-----------------
**Every asset in this file is ground origin**: z=0 is the terrace it stands
on, and it rises into +z. Nothing here hangs (contrast ``props_flora.
vinehang``, ``props_deco.dripstone``, ``props_land.bell``). Three of them
have geometry *below* z=0 on purpose, because a thing half sunk into the
ground reads as having been there a long time -- ``hollowlog``, ``pipemouth``
and ``boneribs``. That geometry is never seen on an opaque terrace; it is
there so the ground line can cut through solid material at any bearing rather
than leaving a model balanced on a floor.

The through-pieces
------------------
A body is 0.6 m across and straddles the next cell whenever it is not dead
centre, and on a circle the diagonal step is the normal case -- so a passage
the course can be steered through is **three cells wide and three high**, and
every hole here clears 3.0 m both ways. That is what makes these big: a gate
with a three-metre hole in it is a five-metre gate. The clear rectangle for
each is written on its builder, measured between the *inner faces* of the
parts that bound it, and every one of them straddles the local Y axis -- you
walk through along **Y**, at local x=0.

* torii      -- a vermilion gate, two beams and a plaque. 3.10 x 3.30.
* hollowlog  -- a giant fallen log, bored through and half sunk. 3.10 x 3.10.
* brokenarch -- a ruined arch, one pier bitten into. 3.20 x 3.30.
* pipemouth  -- an iron outfall pipe out of an earth bank. 3.20 x 3.10.
* doorframe  -- a door and its frame and nothing else. 3.32 x 3.41
               (over its own 0.14 m threshold, not off the terrace).
* boneribs   -- a rib cage out of the ground, with the skull. 3.20 x 3.20.

The standable ones
------------------
Flat, honest tops, one to three cells across, so a landing can sit on one.
The height is written on the builder and is the **top face**, not the
bounding box: several of them carry something small and proud of it (a
candle, a spot, a bookmark) that a foot would simply ignore.

* bigshroom   -- a giant mushroom with a plate for a cap.   top z=2.60
* cratestack  -- crates, a barrel and what fell out.        top z=2.36
* anvilplinth -- an anvil on a stepped plinth.              top z=2.52
* boathull    -- a punt upturned on two cradles.            top z=2.28
* tomestack   -- three enormous books on a step.            top z=2.26
* layercake   -- a two-tier cake on a stand, one slice out. top z=2.82

The odd ones
------------
* bucketcrow    -- a scarecrow with a bucket on, and a crow it cannot see.
* oddshrine     -- a shrine, a lopsided idol, and what has been left for it.
* blockjenga    -- a stack of blocks that should not be standing.
* signpost      -- six arms, one up, one down, none of them anywhere.
* hatrock       -- a wizard's hat slumped on a boulder, staff still leaning.
* meltman       -- a snowman most of the way to being a puddle.
* chickenstatue -- a monument to a chicken, with a bird sitting on it.

Zones
-----
``wood``, ``stem``, ``leaf``, ``metal`` and ``glow`` are the runtime's
recolouring vocabulary (``ModelAsset.recolor``; the spiral scene writes all
five per palette). They are used here **only where a per-theme tint is
wanted** -- a gate that takes the level's timber colour is right, a cake that
takes the level's leaf colour is not. Everything whose colour is part of the
joke carries its own zone name instead (``bone``, ``snow``, ``icing``,
``sponge``, ``straw``, ``paper``, ``stone``, ``rock``, ``moss``, ``cloth``,
``rust``, ``gold``, ``ink``, ``flesh``), which ``recolor`` ignores.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)

#: Thickness of every thin sheet here -- paper, cloth, a page, a ribbon, a
#: wing. Same argument as ``props_flora.LEAF`` and ``props_world.SHEET``: a
#: plane with no thickness vanishes edge-on, and the camera goes *past* these
#: rather than looking at them from one side. Four centimetres is invisible
#: as a solid at five metres and never blinks out.
SHEET = 0.04


def blk(name, size, loc, mat, rot=None, bevel=0.0):
    """A box, square-edged by default. The unit of this whole file.

    Wrapping :func:`common.box` rather than typing ``bevel=0.0`` three hundred
    times is not tidiness -- the default is 0.05, and one forgotten argument
    is a hundred triangles of rounding on a thing that is meant to look like
    Minecraft. The few places a bevel earns its keep (a snowball, a cherry, a
    straw head) pass one explicitly.
    """
    return box(name, size, loc, mat, bevel=bevel, rot=rot)


def merge(parts, name):
    """Join, then bake the survivor's own transform into the mesh.

    ``join`` keeps the *active* object's transform and rewrites everybody else
    relative to it, so a model whose first part happened to be a yawed crate
    ends up with a node rotation in the glTF -- a second description of where
    the model is, which the runtime then has to agree with. Applying it leaves
    exactly one description: the vertices. Straight out of
    ``props_world.merge``, for the same reason.
    """
    ob = join(parts, name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


def spin(ob, axis: str, deg: float):
    """Rotate an object's mesh data in place, about its own origin."""
    ob.data.transform(Matrix.Rotation(math.radians(deg), 4, axis))
    return ob


def shift(ob, dx=0.0, dy=0.0, dz=0.0):
    """Translate an object's mesh data. Same argument as :func:`spin`."""
    ob.data.transform(Matrix.Translation((dx, dy, dz)))
    return ob


def plates(parts, tag, mat, slabs, *, top, thick, step=0.05):
    """Overlapping slabs making one irregular surface, no two coplanar.

    ``slabs`` is ``(width, depth, x, y, yaw)`` each. The first slab's top face
    is exactly ``top``; every later one is ``step`` lower. That step is the
    whole point -- built at one height their top faces coincide, and
    coincident faces bake black. Five centimetres is nothing to look at and is
    the difference between a cake with a slice out of it and a cake with a
    hole in it. Lifted from ``props_world.terrace``.
    """
    for i, (w, d, x, y, yaw) in enumerate(slabs):
        z = top - step * i
        parts.append(blk(f"{tag}{i}", (w, d, thick), (x, y, z - thick / 2),
                         mat, rot=(0, 0, yaw)))
    return parts


def span(name, p0, p1, w, d, mat, y=0.0):
    """A beam running from ``p0`` to ``p1``, both ``(x, z)`` in the XZ plane.

    Every arch, rib, roof board and leaning stick in this file is one of
    these. Solving for the angle rather than typing one is what keeps a
    voussoir's ends actually touching its neighbours' after somebody moves a
    springing point by ten centimetres -- which happened four times while this
    file was being written.

    Local Z runs along the beam, local X is ``w`` across it in the XZ plane,
    and local Y is ``d``, the thickness along the world Y axis.
    """
    (x0, z0), (x1, z1) = p0, p1
    dx, dz = x1 - x0, z1 - z0
    return blk(name, (w, d, math.hypot(dx, dz)),
               ((x0 + x1) / 2, y, (z0 + z1) / 2), mat,
               rot=(0, math.atan2(dx, dz), 0))


def tube(parts, tag, mat, *, r_in, thick, length, zc, wide=None, y=0.0,
         n=8, jitter=()):
    """A prism tube lying along **Y**: ``n`` planks in a ring about the Y axis.

    This is how both things you can run *through* the middle of are built, and
    the arithmetic is worth stating once because it is what sets their size. A
    ring of ``n`` planks whose inner faces are ``r_in`` from the axis admits an
    axis-aligned square of half-side ``r_in / sqrt(2)`` (the binding face is
    the one at 45 degrees). A three-metre passage therefore needs
    ``r_in >= 2.12`` -- which is why a hollow log you can run through is five
    metres of log.

    ``jitter`` is a per-plank *outward* radius offset, and outward only: it
    makes a log look grown rather than turned, and it can only ever make the
    bore bigger. A literal table rather than a random draw, because an asset
    is built once and committed and a build that produces different geometry
    on Tuesday is one nobody can check against ``metrics.json``.
    """
    wide = wide or (2.0 * math.pi * (r_in + thick / 2) / n) * 1.10
    for i in range(n):
        a = 2.0 * math.pi * i / n
        out = jitter[i] if i < len(jitter) else 0.0
        r = r_in + thick / 2 + out
        parts.append(blk(f"{tag}{i}", (thick, length, wide),
                         (r * math.cos(a), y, zc + r * math.sin(a)), mat,
                         rot=(0, -a, 0)))
    return parts


def rubble(parts, tag, mat, table, *, z=0.0):
    """A scatter of tilted, yawed stones. ``table`` is ``(x, y, sx, sy, sz,
    yaw_deg, tilt_deg)``.

    The tilt is the whole trick and ``props_deco.pebbles`` records why: boxes
    sitting square on a floor read as boxes however different their sizes are,
    because every one of them shows the same three faces to the same light.
    """
    for i, (x, y, sx, sy, sz, yaw, tilt) in enumerate(table):
        parts.append(blk(f"{tag}{i}", (sx, sy, sz),
                         (x, y, z + sz / 2 - sz * 0.18), mat,
                         rot=(math.radians(tilt), math.radians(-tilt * 0.6),
                              math.radians(yaw))))
    return parts


def cross(parts, tag, w, h, loc, mat, tilt=0.0):
    """Two quads at right angles: straw, a wisp, a tuft. ``loc`` is the foot."""
    x, y, z = loc
    for i, rot in enumerate((0.0, math.pi / 2)):
        parts.append(blk(f"{tag}{i}", (w, SHEET, h), (x, y, z + h / 2), mat,
                         rot=(tilt, 0, rot)))
    return parts


def patches(parts, tag, mat, table, *, top=0.04, thick=0.07, step=0.03):
    """Moss, straw, meltwater: thin yawed slabs sunk into the ground.

    ``table`` is ``(x, y, w, d, yaw)``, and the pieces have to **overlap each
    other**. Every one of these started life as a single slab and rendered as
    a flat coloured rectangle on the floor, which is what a lawn looks like in
    a game from 1996; three *separate* smaller slabs is three tiles, which is
    worse. Two or three overlapping ones at slightly different heights and
    yaws read as one ragged patch, and the height difference is compulsory
    anyway -- laid at one z they are coplanar and the bake blacks them out.

    They also want to be **small and dark**. A moss patch is a stain, and at a
    metre across in a saturated green it is a snooker table.
    """
    for i, (x, y, w, d, yaw) in enumerate(table):
        z = top - step * i
        parts.append(blk(f"{tag}{i}", (w, d, thick), (x, y, z - thick / 2),
                         mat, rot=(0, 0, yaw)))
    return parts


# ---------------------------------------------------------------------------
# Things with a hole in them
# ---------------------------------------------------------------------------

def torii():
    """A torii gate. Ground origin. **Hole: 3.10 wide x 3.30 high at x=0.**

    The one piece here that is straightforwardly beautiful, and it earns its
    place by being the clearest possible statement of "go through this": two
    uprights, two beams, nothing else in the frame, and the upper beam's ends
    turned up so the silhouette is not a capital H.

    The lanterns hang on the **outside** faces of the posts. Hung under the
    lower beam where they belong they came down to 2.6 m in the corners of
    the opening, which quietly costs half a metre of the clear height the
    whole asset exists to provide -- and a passage's clear rectangle is the
    smallest one anywhere in it, not the one at the middle.
    """
    WOOD = zone("wood", (0.63, 0.21, 0.16), rough=0.85)
    TRIM = zone("stem", (0.22, 0.14, 0.12), rough=0.9)
    STONE = zone("stone", (0.52, 0.51, 0.48), rough=0.95)
    PAPER = zone("paper", (0.93, 0.88, 0.74), rough=0.9)
    STRAW = zone("straw", (0.80, 0.72, 0.46), rough=0.95)
    GLOW = zone("glow", (1.0, 0.84, 0.48), rough=0.25)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)

    # **The footing sets the clear width, not the post.** A torii's base stone
    # is wider than the pillar it carries, so at 1.05 across on a 1.88 axis it
    # reached to x=1.36 and the bottom half-metre of a 3.32 m passage was
    # really 2.71 -- which is the sort of thing that is invisible in a render
    # and fatal to a body. The post stands further out and the stone is
    # smaller; the binding number is now 2.00 - 0.90/2 = 1.55.
    px, pw = 2.00, 0.44
    parts = []
    for s in (-1, 1):
        t = "l" if s < 0 else "r"
        parts.append(blk(f"{t}foot", (0.90, 0.98, 0.52), (s * px, 0, 0.20),
                         STONE))
        parts.append(blk(f"{t}post", (pw, pw, 4.10), (s * px, 0, 2.42), WOOD))
        # A lantern on a bracket, outboard, clear of the opening entirely.
        parts.append(blk(f"{t}brack", (0.52, 0.12, 0.12),
                         (s * (px + 0.34), 0, 3.05), TRIM))
        lx = s * (px + 0.56)
        parts.append(blk(f"{t}chain", (0.06, 0.06, 0.24), (lx, 0, 2.88), TRIM))
        parts.append(blk(f"{t}lanttop", (0.40, 0.40, 0.08), (lx, 0, 2.72),
                         TRIM))
        parts.append(blk(f"{t}lant", (0.34, 0.34, 0.46), (lx, 0, 2.46), PAPER))
        parts.append(blk(f"{t}lantlit", (0.24, 0.24, 0.10), (lx, 0, 2.20),
                         GLOW))

    # The lower beam (nuki). Its underside at 3.30 is the clear height, and
    # everything above it is allowed to be as busy as it likes.
    parts.append(blk("nuki", (5.14, 0.36, 0.32), (0, 0, 3.46), WOOD))
    parts.append(blk("plaque", (0.72, 0.26, 0.60), (0, 0, 3.94), WOOD))
    parts.append(blk("plaqface", (0.50, 0.10, 0.40), (0, -0.16, 3.96), TRIM))
    # The rope, sitting on the beam rather than hanging off it: hung, its
    # tails are in the opening. Fat and knotted and straw-coloured -- at 0.24
    # thick and the same cream as the plaque it read as a second lintel.
    for i, (x, w, t) in enumerate(((-1.30, 1.5, 0.34), (0.0, 1.7, 0.44),
                                   (1.30, 1.5, 0.34))):
        parts.append(blk(f"rope{i}", (w, t, t), (x, 0.0, 3.76 + 0.02 * i),
                         STRAW, rot=(0, (i - 1) * 0.06, 0)))
    for i, x in enumerate((-0.78, 0.78)):
        parts.append(blk(f"knot{i}", (0.30, 0.40, 0.40), (x, 0.0, 3.80), STRAW,
                         rot=(0, 0, 0.3)))
    # Second beam (shimaki) and top beam (kasagi), overlapping by 3 cm rather
    # than abutting: two faces exactly on one plane bake as a black seam.
    parts.append(blk("shimaki", (5.64, 0.46, 0.28), (0, 0, 4.44), WOOD))
    parts.append(blk("kasagi", (5.44, 0.58, 0.40), (0, 0, 4.74), TRIM))
    for s in (-1, 1):
        t = "l" if s < 0 else "r"
        parts.append(blk(f"{t}end", (1.30, 0.58, 0.38), (s * 2.98, 0, 4.83),
                         TRIM, rot=(0, -s * 0.17, 0)))
    parts.append(blk("moss0", (0.90, 0.56, 0.08), (-1.62, 0.02, 4.96), MOSS,
                     rot=(0, 0, 0.05)))
    parts.append(blk("moss1", (0.55, 0.50, 0.08), (0.70, -0.06, 4.94), MOSS,
                     rot=(0, 0, -0.2)))
    parts.append(blk("moss2", (0.70, 0.26, 0.14), (2.30, -0.30, 0.42), MOSS))
    return merge(parts, "torii")


def hollowlog():
    """A giant fallen log, bored through. Ground origin, buried to z=-1.19.

    **Hole: 3.10 wide x 3.10 high, centred on x=0, from z=0 up.** The bore's
    own floor is under the terrace, so what a body runs on through here is the
    ground, which is the point -- a tube resting on a floor has a lip at each
    end to trip over and reads as a pipe somebody dropped.

    Eight planks in a ring (:func:`tube`), because that is the cheapest shape
    that is round from every heading, with the radii jittered *outward* so it
    reads as grown rather than turned. Bark strips outside it, splinters at
    the broken end, moss and mushrooms where it meets the ground.
    """
    WOOD = zone("wood", (0.72, 0.58, 0.38), rough=0.92)
    BARK = zone("stem", (0.33, 0.24, 0.16), rough=0.95)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)
    CAP = zone("leaf", (0.74, 0.34, 0.26), rough=0.85)

    parts = []
    R, T, ZC, LEN = 2.19, 0.55, 1.55, 8.60
    tube(parts, "core", WOOD, r_in=R, thick=T, length=LEN, zc=ZC,
         jitter=(0.06, 0.0, 0.09, 0.03, 0.07, 0.0, 0.05, 0.10))
    # **It has to be much longer than it is thick.** At six metres against a
    # five-and-a-half metre bore this was a cube with a hole in it and read as
    # a barrel; the bore a body runs through is what sets the width, so the
    # only lever left is length. Plus a flare at the butt end, because a
    # constant-section tube is a pipe.
    tube(parts, "butt", BARK, r_in=R + 0.16, thick=0.62, length=1.20, zc=ZC,
         y=-LEN / 2 + 0.30)
    # Bark: **narrow ridges**, twelve round the girth at broken lengths.
    # Eight wide slabs was the first pass and it panelled the log like a
    # shipping container.
    for i in range(12):
        a = 2.0 * math.pi * (i + 0.5) / 12
        r = R + T + 0.09
        runs = ((-2.3, 3.4), (1.9, 4.0)) if i % 2 else ((-0.4, 7.4),)
        for j, (dy, ln) in enumerate(runs):
            parts.append(blk(f"bark{i}{j}", (0.18, ln, 0.62),
                             (r * math.cos(a), dy, ZC + r * math.sin(a)),
                             BARK, rot=(0, -a, 0)))
    # Two knots and a snapped branch stub, which is what stops a long tube
    # being a long tube.
    for i, (a, dy, s) in enumerate(((0.9, 2.6, 0.62), (3.9, -1.1, 0.48))):
        r = R + T + 0.05
        parts.append(blk(f"knot{i}", (0.34, s, s),
                         (r * math.cos(a), dy, ZC + r * math.sin(a)), BARK,
                         rot=(0, -a, 0)))
    # The branch stub leans **out** of the log, not into the bore: at
    # x = -2.35 with a 0.9 rad lean its lower end swung back inside the
    # passage, which is a branch across the one thing this asset is for.
    parts.append(blk("branch", (0.44, 0.44, 1.90),
                     (-2.95, 3.30, ZC + 2.05), BARK, rot=(0.3, -1.1, 0.2)))
    # The broken end: shards leaning off the +Y rim, all at different angles.
    for i, (a, ln, tl) in enumerate(((0.5, 1.1, -0.30), (1.9, 0.8, 0.22),
                                     (3.4, 1.3, -0.18), (5.2, 0.9, 0.30))):
        r = R + T / 2
        parts.append(blk(f"shard{i}", (0.42, ln, 0.70),
                         (r * math.cos(a), LEN / 2 + ln * 0.3,
                          ZC + r * math.sin(a)), WOOD,
                         rot=(tl, -a, 0.2)))
    # Moss along the top, in three pieces at different heights (one slab
    # across the crown is a lid, and coplanar with the plank's own top face).
    patches(parts, "moss", MOSS, (
        (-0.30, 1.20, 2.10, 3.00, 0.10),
        (0.55, -1.90, 1.50, 2.20, -0.22),
        (-0.15, 3.40, 1.20, 1.60, 0.35),
    ), top=ZC + R + T + 0.10, thick=0.22, step=0.06)
    # Mushrooms at the foot, on the side you pass.
    for i, (x, y, s) in enumerate(((-2.6, 2.6, 0.46), (-2.9, 1.7, 0.30),
                                   (2.7, -3.2, 0.38))):
        parts.append(blk(f"stalk{i}", (s * 0.30, s * 0.30, s * 0.9),
                         (x, y, s * 0.45), WOOD))
        parts.append(cylinder(f"cap{i}", s * 0.80, s * 0.34,
                              (x, y, s * 1.02), CAP, vertices=8))
    rubble(parts, "root", BARK, (
        (-2.9, -3.6, 0.7, 0.5, 0.4, 24, 10),
        (3.0, 3.4, 0.9, 0.6, 0.5, -38, 8),
        (2.8, -4.9, 0.6, 0.7, 0.35, 61, -12),
    ))
    return merge(parts, "hollowlog")


def brokenarch():
    """A ruined arch, standing on its own. Ground origin.

    **Hole: 3.20 wide x 3.30 high**, measured between the piers and up to the
    springing; the arch itself rises to 4.5 in the middle.

    The half that has fallen is what makes it a ruin rather than a gate
    somebody maintains -- the same note ``props_world.startisle`` records
    about its own arch -- so the right-hand pier has a bite out of it, the top
    two voussoirs on that side are gone, and one of them is lying on the
    ground where it landed.
    """
    STONE = zone("stone", (0.72, 0.68, 0.58), rough=0.92)
    DARK = zone("rock", (0.44, 0.42, 0.38), rough=0.95)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)
    IVY = zone("leaf", (0.30, 0.52, 0.24), rough=0.9)

    parts = []
    # **The plinth and the capital set the clear width, not the pier.** Both
    # are wider than the shaft between them -- that is what a plinth and a
    # capital *are* -- so on a 2.10 axis they reached to 1.35 and 1.45 and
    # pinched the bottom and the top of the opening without changing the look
    # of the render at all. On 2.35 the binding number is the plinth's 1.60.
    px, spring = 2.35, 3.30
    # Left pier: whole, on a plinth, with a capital at the springing.
    parts.append(blk("lplinth", (1.50, 1.50, 0.40), (-px, 0, 0.16), DARK))
    parts.append(blk("lpier", (1.00, 1.05, 2.90), (-px, 0, 1.85), STONE))
    parts.append(blk("lcap", (1.26, 1.25, 0.36), (-px, 0, 3.14), DARK))
    # Right pier: bitten into. Three courses, each losing width or depth off a
    # *corner* rather than off a whole face -- a course made shallower all the
    # way across is a recess right round the pier, and the bake fills a recess
    # with shadow, so it read as a letterbox slot cut in the stone.
    parts.append(blk("rplinth", (1.50, 1.50, 0.40), (px, 0, 0.16), DARK))
    for i, (w, d, h, dx, dy) in enumerate(((1.00, 1.05, 1.10, 0.0, 0.0),
                                           (0.86, 0.88, 0.95, -0.07, -0.08),
                                           (0.74, 1.02, 0.95, 0.13, 0.02))):
        parts.append(blk(f"rpier{i}", (w, d, h),
                         (px + dx, dy, 0.38 + h / 2 + i * 0.92), STONE))
    parts.append(blk("rcap", (1.22, 1.20, 0.34), (px, 0, 3.15), DARK))

    # **Two rings of voussoirs, the outer one offset by half a stone.** That
    # is a real arch's construction and it is here for a rendering reason:
    # eight boxes over a half-circle turn 22.5 degrees at each joint, so
    # whatever you do with one ring is wrong. Butted on their centre lines
    # they leave a wedge open on the *extrados* -- 15 cm at 0.74 thick --
    # which bakes to pure occlusion and reads as a row of black gashes up the
    # arch. Overlapping them to close it is worse: heavily interpenetrating
    # boxes give the bake interior faces to shade and the gashes get bigger.
    # A thin ring has a small wedge (8 cm at 0.42), and a second ring whose
    # joints sit over the first ring's stones covers even those.
    #
    # And the centre line of a voussoir is the **intrados plus half its
    # width**, not the intrados: built on the opening's own radius the
    # springing stones stood inboard of the piers and quietly took the
    # passage from 3.24 down to 2.50, which is not a passage.
    VW, OVER = 0.42, 0.008

    def ring(tag, inner, offset, keep, depth):
        rx, rz = 1.62 + inner + VW / 2, 1.42 + inner + VW / 2

        def pt(t):
            a = math.pi * (t + offset)
            return (-math.cos(a) * rx, spring + math.sin(a) * rz)

        for i in keep:
            parts.append(span(f"{tag}{i}", pt(i / 8 - OVER),
                              pt((i + 1) / 8 + OVER), VW, depth, STONE))

    ring("vouss", 0.0, 0.0, (0, 1, 2, 3, 6, 7), 1.00)
    # The outer ring has spalled off the top three stones, which is what makes
    # the arch look eaten rather than demolished.
    ring("outer", VW, 1 / 16, (0, 1, 2, 6, 7), 0.88)
    # The crown, still up there but tipped out of line.
    ring("crown", 0.0, 0.0, (4,), 0.92)
    parts.append(blk("tipped", (0.70, 0.90, 0.62), (0.90, -0.10, 4.44), STONE,
                     rot=(0.12, 0.55, 0.10)))
    # What came down.
    rubble(parts, "fall", STONE, (
        (2.9, 1.5, 0.90, 0.80, 0.66, 34, 14),
        (2.2, -1.7, 0.70, 0.62, 0.52, -22, -9),
        (3.4, -0.4, 0.55, 0.50, 0.40, 58, 7),
        (-2.8, 1.8, 0.48, 0.44, 0.36, 12, -11),
    ))
    patches(parts, "moss", MOSS, (
        (-2.35, 0.10, 0.76, 0.66, 0.30),
        (-2.10, 0.40, 0.48, 0.40, -0.4),
    ), top=3.34, thick=0.09, step=0.04)
    # Ivy down the whole left pier, two ragged sheets on different faces --
    # outboard and on the flank, never on the face that bounds the passage.
    parts.append(blk("ivy0", (0.10, 0.80, 2.20), (-2.87, 0.15, 2.20), IVY))
    parts.append(blk("ivy1", (0.55, 0.10, 1.40), (-2.55, 0.56, 1.70), IVY))
    return merge(parts, "brokenarch")


def pipemouth():
    """An iron outfall pipe out of a rubble berm. Ground origin, buried to
    z=-1.10.

    **Hole: 3.20 wide x 3.10 high measured from the terrace up**, which is the
    honest number for a round bore: the pipe's inner faces are 2.35 from its
    axis and the axis is 1.50 up, so a body walking on the ground at z=0 has
    3.20 of clear width and keeps it to z=3.10. Right through the middle it is
    4.70 across.

    The flange and its bolts are the whole read. A plain tube out of a mound
    is a hole; a flange says somebody bolted this here and then left.
    """
    IRON = zone("metal", (0.42, 0.44, 0.47), rough=0.55)
    DARK = zone("ink", (0.12, 0.12, 0.13), rough=0.95)
    RUST = zone("rust", (0.48, 0.28, 0.15), rough=0.95)
    #: The spoil is **brown**, and that is the whole reason this asset reads
    #: at all. At (0.40, 0.39, 0.38) it was the same *value* as the iron and
    #: the render came back as one undifferentiated grey lump -- a pipe out of
    #: a bank of rock is two materials or it is neither.
    ROCK = zone("rock", (0.34, 0.28, 0.21), rough=0.95)
    WATER = zone("water", (0.36, 0.56, 0.62), rough=0.25)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)

    parts = []
    # **2.35, not the 2.20 the arithmetic asks for.** ``r_in / sqrt(2) - zc``
    # gives exactly a 3.22 x 3.00 rectangle at 2.20, which means the corners
    # of the passage lie *on* the plank faces -- and then a lining ring a
    # hand's breadth inside the mouth, added to make the hole read as a hole,
    # silently took it to 2.94. A bore with no margin in it is a bore that
    # the next detail closes.
    R, T, ZC, LEN = 2.35, 0.40, 1.50, 6.00
    tube(parts, "pipe", IRON, r_in=R, thick=T, length=LEN, zc=ZC)
    # **A pipe has to be longer than it is wide**, and this one was half as
    # long: at 3.2 against a 5.2 bore it read as a ring somebody had dropped,
    # and the bore -- the entire point -- was invisible from any heading but
    # straight down the axis.
    #
    # A dark lining just inside the mouth, so the hole reads as a hole from
    # outside rather than as the flat end of a cylinder. It sits **in** the
    # wall, from ``r_in`` outward, never inboard of it.
    tube(parts, "lining", DARK, r_in=R, thick=0.14, length=1.20,
         zc=ZC, y=LEN / 2 - 0.60)
    # The flange at the +Y mouth, and eight bolts round it.
    tube(parts, "flange", IRON, r_in=R + T - 0.08, thick=0.58, length=0.46,
         zc=ZC, y=LEN / 2 + 0.05)
    for i in range(8):
        a = 2.0 * math.pi * (i + 0.5) / 8
        r = R + T + 0.20
        parts.append(cylinder(f"bolt{i}", 0.15, 0.22,
                              (r * math.cos(a), LEN / 2 + 0.24,
                               ZC + r * math.sin(a)), RUST, vertices=6,
                              rot=(math.pi / 2, 0, 0)))
    # A pair of hoops part way back, and rust in narrow streaks. A single wide
    # patch is a painted panel; an even coat is a brown pipe.
    for i, dy in enumerate((-0.9, -2.6)):
        tube(parts, f"hoop{i}", IRON, r_in=R + T - 0.06, thick=0.34,
             length=0.30, zc=ZC, y=dy)
    for i, (a, h, dy, ln) in enumerate(((0.55, 1.5, 1.4, 1.9),
                                        (0.95, 0.9, 2.1, 1.1),
                                        (2.35, 1.2, -1.4, 1.6),
                                        (4.90, 1.4, 0.6, 2.2),
                                        (5.45, 0.7, -2.2, 1.0))):
        r = R + T + 0.07
        parts.append(blk(f"rust{i}", (0.10, ln, h),
                         (r * math.cos(a), dy, ZC + r * math.sin(a)), RUST,
                         rot=(0, -a, 0)))
    # **The bank has to be bigger than the pipe.** Two passes of this asset
    # scattered rock *around* the mouth and both read as one grey lump with
    # some paving fallen off it -- because a pipe five metres across banked by
    # two-metre stones is a pipe with pebbles at it, and nothing in the
    # silhouette says the pipe comes *out* of anything. It is now a bank the
    # pipe is buried in to its shoulders, in three masses that overrun it in
    # every direction, with the rubble as a toe rather than as the bank.
    rubble(parts, "bankl", ROCK, (
        (-3.95, -2.80, 2.40, 3.00, 4.60, 6, 2),
        (-3.75, -0.60, 2.00, 2.20, 3.20, 27, -8),
        (-3.45, 1.20, 1.45, 1.50, 1.20, 41, 9),
    ))
    rubble(parts, "bankr", ROCK, (
        (3.95, -2.90, 2.40, 2.80, 4.20, -11, 3),
        (3.80, -0.50, 1.90, 2.00, 2.80, -33, 7),
        (3.55, 1.50, 1.30, 1.40, 1.00, -22, -6),
    ))
    # ...and **over** it. A bank laid as one wide mass behind the mouth fills
    # the far half of the bore with earth, which looks perfectly right and
    # turns the tunnel into an alcove. It goes either side of the pipe and
    # across the top of it, with the pipe in the slot between.
    rubble(parts, "bankt", ROCK, (
        (-0.50, -2.90, 6.00, 2.60, 1.80, 3, 2),
        (0.70, -1.50, 4.40, 1.70, 1.20, -5, 3),
    ), z=4.10)
    # A trickle out of the mouth and a puddle it runs into.
    patches(parts, "pool", WATER, (
        (0.20, 4.00, 0.90, 1.40, 0.0),
        (0.10, 4.80, 1.90, 1.30, 0.2),
        (0.80, 5.30, 1.10, 0.90, -0.4),
    ))
    patches(parts, "moss", MOSS, (
        (-0.70, 4.05, 1.00, 0.55, 0.15),
        (0.75, 3.80, 0.60, 0.50, -0.35),
    ))
    # A valve wheel propped against the bank: the one curved thing in shot.
    parts.append(cylinder("wheel", 0.62, 0.14, (-2.9, 2.3, 0.70), RUST,
                          vertices=8, rot=(1.25, 0, 0.4)))
    parts.append(cylinder("hub", 0.20, 0.24, (-2.9, 2.3, 0.70), RUST,
                          vertices=6, rot=(1.25, 0, 0.4)))
    return merge(parts, "pipemouth")


def doorframe():
    """A door, its frame, and no house. Ground origin.

    **Hole: 3.32 wide x 3.41 high at x=0**, measured off its own 0.14 m
    threshold rather than off the terrace.

    The joke only works if the door is unmistakably *open* rather than
    missing, so it hangs past ninety degrees on one surviving hinge, tipped
    ten degrees so its lower corner is on the ground. Swung to seventy-five it
    read as a door and took twenty-five centimetres out of the opening -- past
    a right angle it is outside the frame entirely and the clear width is the
    frame's own.

    There is a mat, and there is a key under it.
    """
    WOOD = zone("wood", (0.50, 0.34, 0.20), rough=0.9)
    DOOR = zone("stem", (0.28, 0.24, 0.14), rough=0.9)
    #: The door is **painted**, and that is the difference between reading it
    #: and not. Built out of the frame's own timber it swung open perfectly
    #: and vanished: same colour, same light, edge-on to half the headings it
    #: is seen from.
    PAINT = zone("leaf", (0.24, 0.42, 0.34), rough=0.8)
    STONE = zone("stone", (0.60, 0.58, 0.54), rough=0.95)
    BRASS = zone("metal", (0.72, 0.58, 0.26), rough=0.4)
    CLOTH = zone("cloth", (0.55, 0.34, 0.24), rough=0.95)
    GOLD = zone("gold", (0.84, 0.70, 0.30), rough=0.35)

    jx, jw = 1.90, 0.48         # jamb axis, jamb width -> inner faces +-1.66
    parts = []
    # A pad under each jamb and a **shallow** threshold between them. A single
    # step slab across the opening is what a doorstep is and it put 30 cm of
    # stone across the floor of the passage; 12 cm is a threshold a body walks
    # over rather than a ledge it has to be placed on.
    for s in (-1, 1):
        parts.append(blk(f"pad{s}", (0.84, 1.40, 0.30), (s * 2.08, 0.10, 0.10),
                         STONE))
    parts.append(blk("sill", (3.10, 1.20, 0.14), (0, 0.10, 0.05), STONE))
    for s in (-1, 1):
        t = "l" if s < 0 else "r"
        parts.append(blk(f"{t}jamb", (jw, 0.62, 3.40), (s * jx, 0, 1.95),
                         WOOD))
        # The stop bead sits **in** the jamb's inner face, not proud of it: at
        # 5 cm proud it was a door stop doing its job and quietly taking the
        # clear width from 3.32 to 3.08.
        parts.append(blk(f"{t}jambin", (0.14, 0.34, 3.30),
                         (s * (jx - jw / 2 + 0.19), 0.0, 1.95), DOOR))
    parts.append(blk("lintel", (4.60, 0.62, 0.42), (0, 0, 3.76), WOOD))
    parts.append(blk("linteltrim", (4.90, 0.74, 0.16), (0, 0, 4.02), DOOR))
    # A pediment, so the top of the frame is not a plain lintel.
    for s in (-1, 1):
        parts.append(span(f"ped{s}", (s * 2.10, 4.10), (0.0, 4.86), 0.30, 0.52,
                          WOOD))
    parts.append(blk("finial", (0.26, 0.26, 0.34), (0, 0, 5.02), DOOR))

    # The door, on one hinge, swung 122 degrees and tipped over. Past a right
    # angle on purpose: at seventy-five it looked more like a door and stood
    # 25 cm inside the opening, and the clear rectangle is the whole reason
    # this asset is in the through list.
    ang = math.radians(122)
    hinge = (-jx - 0.12, 0.26)
    dw, dh = 1.62, 3.20
    cx = hinge[0] + math.cos(ang) * dw / 2
    cy = hinge[1] + math.sin(ang) * dw / 2
    parts.append(blk("door", (dw, 0.18, dh), (cx, cy, 1.66), PAINT,
                     rot=(0.0, 0.17, ang)))
    parts.append(blk("doorlip", (dw + 0.06, 0.10, 0.16), (cx, cy, 3.20), DOOR,
                     rot=(0.0, 0.17, ang)))
    # Two sunk panels a shade darker, and the rails between them.
    for i, dz in enumerate((-0.86, 0.86)):
        parts.append(blk(f"panel{i}", (dw * 0.60, 0.22, 1.00),
                         (cx, cy, 1.66 + dz), DOOR,
                         rot=(0.0, 0.17, ang)))
        parts.append(blk(f"pfill{i}", (dw * 0.48, 0.24, 0.84),
                         (cx, cy, 1.66 + dz), PAINT,
                         rot=(0.0, 0.17, ang)))
    # The knob, out on the swinging edge where a knob is.
    parts.append(blk("knob", (0.22, 0.22, 0.22),
                     (cx + math.cos(ang) * 0.58 - math.sin(ang) * 0.16,
                      cy + math.sin(ang) * 0.58 + math.cos(ang) * 0.16, 1.80),
                     BRASS, bevel=0.07))
    parts.append(blk("plate", (0.14, 0.26, 0.34),
                     (cx + math.cos(ang) * 0.62, cy + math.sin(ang) * 0.62,
                      1.80), BRASS, rot=(0.0, 0.0, ang)))
    parts.append(blk("hinge0", (0.16, 0.30, 0.26), (hinge[0], hinge[1], 2.70),
                     BRASS))
    # The hinge that let go, still screwed to the jamb.
    parts.append(blk("hinge1", (0.16, 0.30, 0.24), (-jx - 0.06, 0.30, 0.72),
                     BRASS, rot=(0, 0, -0.5)))

    parts.append(blk("mat", (1.60, 0.86, 0.09), (0.15, 1.15, 0.05), CLOTH,
                     rot=(0, 0, 0.09)))
    parts.append(blk("matrim", (1.34, 0.62, 0.10), (0.15, 1.15, 0.09), DOOR,
                     rot=(0, 0, 0.09)))
    parts.append(blk("key", (0.30, 0.10, 0.05), (0.95, 1.42, 0.045), GOLD,
                     rot=(0, 0, 0.7)))
    parts.append(blk("keybit", (0.10, 0.12, 0.05), (1.08, 1.50, 0.045), GOLD,
                     rot=(0, 0, 0.7)))
    return merge(parts, "doorframe")


def boneribs():
    """A rib cage out of the ground. Ground origin, buried to z=-0.60.

    **Hole: 3.20 wide x 3.20 high**, running the length of the cage along Y --
    a body goes in at one end and out at the other under four arches, which is
    the most theatrical passage in the file and the cheapest to build.

    The ribs are quarter-ellipses solved by :func:`span`, four segments each,
    because a rib that is one straight strut is a gatepost. They are also
    **not all the same**: the pairs shrink toward the head and lean a few
    degrees apart, so the cage is a cage rather than four copies of an arch.
    """
    BONE = zone("bone", (0.86, 0.83, 0.72), rough=0.85)
    OLD = zone("stone", (0.66, 0.63, 0.53), rough=0.9)
    DIRT = zone("rock", (0.38, 0.32, 0.24), rough=0.95)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)

    parts = []
    SEGS = 4
    # **A cage's clear rectangle is an ellipse's, and an ellipse is meaner
    # than it looks.** The first pass sprang from x=2.30 and topped out at
    # 4.05, which sounds like plenty for a 3.2 m passage and is not: at half
    # the arch's width the intrados is already only 2.1 m up, so the honest
    # clear rectangle was 3.4 x 2.1. Solving ``(s/x)^2 + (h/z)^2 <= 1`` for
    # the *narrowest* pair in the set is what sets these numbers.
    for k, (y, x0, top, lean) in enumerate(((-3.0, 3.05, 4.85, -0.10),
                                            (-1.1, 3.15, 5.15, 0.04),
                                            (0.8, 3.10, 5.05, -0.05),
                                            (2.5, 2.90, 4.65, 0.09))):
        for s in (-1, 1):
            def pt(t, s=s, x0=x0, top=top):
                a = math.pi / 2 * t
                return (s * x0 * math.cos(a), -0.55 + (top + 0.55) * math.sin(a))
            for i in range(SEGS):
                w = 0.34 - 0.05 * i
                parts.append(span(f"rib{k}{s}{i}", pt(i / SEGS),
                                  pt((i + 1) / SEGS), w, 0.40, BONE, y=y))
        # A vertebra where the pair meets, with its spur standing up.
        parts.append(blk(f"vert{k}", (0.62, 0.66, 0.52), (0, y, top + 0.06),
                         OLD, rot=(0, lean, 0)))
        parts.append(blk(f"spur{k}", (0.20, 0.24, 0.52), (0, y, top + 0.52),
                         OLD, rot=(0.12 * (k % 2 * 2 - 1), lean, 0)))
    # The spine linking them, in three pieces so the run is not one long bar.
    for i, (y, ln, z) in enumerate(((-2.1, 2.3, 5.02), (-0.2, 2.3, 5.12),
                                    (1.7, 2.1, 4.88))):
        parts.append(blk(f"spine{i}", (0.34, ln, 0.30), (0, y, z), OLD,
                         rot=(0, 0.03 * (i - 1), 0)))

    # The skull, past the far end and half in the ground. Three boxes on a
    # taper with a brow over the sockets, not one cube with a smaller cube on
    # it -- the first pass was exactly that and read as a packing crate at the
    # end of a rib cage.
    tilt = (0.10, 0.24, -0.34)
    parts.append(blk("cranium", (1.72, 1.55, 1.42), (0.30, 4.30, 0.66), BONE,
                     rot=tilt))
    parts.append(blk("brow", (1.80, 0.42, 0.44), (0.36, 5.05, 1.02), OLD,
                     rot=tilt))
    parts.append(blk("muzzle", (1.28, 1.05, 1.00), (0.14, 5.55, 0.50), BONE,
                     rot=tilt))
    parts.append(blk("nose", (0.80, 0.66, 0.62), (0.02, 6.20, 0.36), BONE,
                     rot=tilt))
    # Sockets sunk into the face under the brow, and the nasal hole between.
    for s in (-1, 1):
        parts.append(blk(f"socket{s}", (0.46, 0.34, 0.44),
                         (0.34 + s * 0.46, 5.00, 0.74 + s * 0.10), DIRT,
                         rot=tilt))
    parts.append(blk("nasal", (0.24, 0.30, 0.30), (0.16, 5.72, 0.52), DIRT,
                     rot=tilt))
    # Teeth along the lower edge of the muzzle.
    for i in range(4):
        parts.append(blk(f"tooth{i}", (0.20, 0.24, 0.30),
                         (0.44 - i * 0.27, 5.62 - i * 0.06, -0.04), OLD,
                         rot=(0.1, 0.24, -0.34 + 0.1 * i)))
    parts.append(blk("jaw", (0.85, 1.60, 0.30), (-0.85, 5.20, 0.15), OLD,
                     rot=(0.05, 0, 0.55)))
    # Loose bones and the dirt they came out of, all **outboard of the
    # ribs**. Scattered where they looked best they lay across the floor of
    # the cage, which is a passage with rubble in it -- and rubble at ankle
    # height is exactly what a probe measuring a clear rectangle finds and a
    # render never shows.
    rubble(parts, "loose", BONE, (
        (-3.5, 3.4, 1.30, 0.30, 0.28, 28, 12),
        (3.4, 1.9, 0.90, 0.26, 0.24, -55, -8),
        (-3.8, -1.6, 0.34, 1.10, 0.30, 14, 9),
    ))
    rubble(parts, "dirt", DIRT, (
        (-3.4, -3.4, 1.4, 1.1, 0.55, 21, 7),
        (3.5, -2.8, 1.3, 1.4, 0.48, -33, 6),
        (3.7, 3.1, 1.1, 1.2, 0.42, 47, -9),
    ))
    patches(parts, "moss", MOSS, (
        (-2.60, 2.70, 0.90, 0.80, 0.40),
        (-2.20, 3.30, 0.62, 0.60, -0.3),
        (2.55, -2.10, 0.80, 0.72, 0.15),
    ))
    return merge(parts, "boneribs")


# ---------------------------------------------------------------------------
# Things with a flat top
# ---------------------------------------------------------------------------

def bigshroom():
    """A giant mushroom. Ground origin. **Standable top: z = 2.60**, an
    octagon 2.90 across.

    The cap is a *plate* rather than a dome, which is the whole reason this
    is in the standable list: a landing wants a flat face and a real mushroom
    cap has none. What sells it as a cap instead of a table is underneath --
    a skirt ring below the rim and eight radial gills -- and that is worth
    more than curvature on top, because the body approaches these from below.

    The spots stand three centimetres proud of the top. That is deliberate
    and it is the limit: anything a foot would notice belongs on the rim.
    """
    STEM = zone("stem", (0.90, 0.86, 0.76), rough=0.9)
    CAP = zone("leaf", (0.72, 0.24, 0.20), rough=0.85)
    GILL = zone("paper", (0.82, 0.76, 0.66), rough=0.9)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)

    parts = []
    parts.append(cylinder("bulb", 0.62, 0.44, (0, 0, 0.20), STEM, vertices=8))
    parts.append(blk("stalk0", (0.86, 0.86, 1.30), (0, 0, 0.98), STEM))
    parts.append(blk("stalk1", (0.72, 0.72, 0.92), (0, 0, 1.98), STEM,
                     rot=(0, 0, 0.16)))
    parts.append(cylinder("annulus", 0.66, 0.16, (0, 0, 1.62), GILL,
                          vertices=8))
    # Gills: eight fins hung under the cap, pointing outward. Placed with
    # rot z = a - 90 degrees, because a box's local Y under a plain yaw of
    # ``a`` runs *tangentially* -- which is how you draw a turbine.
    for i in range(8):
        a = 2.0 * math.pi * i / 8 + 0.2
        parts.append(blk(f"gill{i}", (0.10, 1.10, 0.20),
                         (0.78 * math.cos(a), 0.78 * math.sin(a), 2.10), GILL,
                         rot=(0, 0, a - math.pi / 2)))
    parts.append(cylinder("skirt", 1.58, 0.24, (0, 0, 2.12), CAP, vertices=8))
    parts.append(cylinder("cap", 1.45, 0.44, (0, 0, 2.38), CAP, vertices=8))
    for i, (x, y, s) in enumerate(((0.0, 0.0, 0.42), (0.82, -0.34, 0.30),
                                   (-0.62, 0.66, 0.34), (-0.30, -0.86, 0.26),
                                   (0.55, 0.80, 0.22))):
        parts.append(blk(f"spot{i}", (s, s, 0.14), (x, y, 2.56), GILL,
                         rot=(0, 0, i * 0.4)))
    # Two small ones at the foot: one mushroom is a prop, three are a patch.
    for i, (x, y, s) in enumerate(((-1.35, 0.95, 0.42), (1.20, 1.30, 0.30))):
        parts.append(blk(f"minis{i}", (s * 0.42, s * 0.42, s * 1.5),
                         (x, y, s * 0.75), STEM))
        parts.append(cylinder(f"minic{i}", s * 1.05, s * 0.45,
                              (x, y, s * 1.62), CAP, vertices=8))
    patches(parts, "moss", MOSS, (
        (0.90, -1.00, 0.68, 0.54, 0.35),
        (0.55, -1.24, 0.46, 0.40, -0.4),
        (1.24, -0.78, 0.40, 0.46, 0.9),
    ))
    return merge(parts, "bigshroom")


def cratestack():
    """Crates, a barrel and what fell out. Ground origin.
    **Standable top: z = 2.36**, a crate lid 1.34 x 1.34.

    Three base crates and one on top. The three are at *different heights*
    (1.10, 0.96, 1.04) and that is not styling -- built level they overlap in
    plan and their top faces are coplanar, which is the black-rectangle bake
    this file's docstring is about. Uneven crates also happen to be what a
    stack of crates looks like.
    """
    WOOD = zone("wood", (0.60, 0.44, 0.26), rough=0.92)
    BATTEN = zone("stem", (0.42, 0.30, 0.17), rough=0.92)
    IRON = zone("metal", (0.44, 0.45, 0.48), rough=0.5)
    STRAW = zone("straw", (0.82, 0.72, 0.40), rough=0.95)
    GOLD = zone("gold", (0.86, 0.72, 0.30), rough=0.35)

    parts = []

    def crate(tag, w, h, x, y, z, yaw):
        parts.append(blk(f"{tag}box", (w, w * 0.94, h), (x, y, z + h / 2),
                         WOOD, rot=(0, 0, yaw)))
        # Corner battens and a band: four boxes, which is the least that reads
        # as a crate rather than a cube of wood.
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            ox = sx * (w / 2 - 0.06) * math.cos(yaw) - sy * (w * 0.47 - 0.06) * math.sin(yaw)
            oy = sx * (w / 2 - 0.06) * math.sin(yaw) + sy * (w * 0.47 - 0.06) * math.cos(yaw)
            parts.append(blk(f"{tag}bat{i}", (0.16, 0.16, h * 0.98),
                             (x + ox, y + oy, z + h / 2), BATTEN,
                             rot=(0, 0, yaw)))
        parts.append(blk(f"{tag}band", (w * 1.03, w * 0.97, 0.12),
                         (x, y, z + h * 0.62), BATTEN, rot=(0, 0, yaw)))

    crate("a", 1.16, 1.10, -0.52, -0.42, 0.0, 0.10)
    crate("b", 1.02, 0.96, 0.62, -0.30, 0.0, -0.24)
    crate("c", 1.08, 1.04, 0.05, 0.78, 0.0, 0.42)
    crate("d", 1.34, 1.30, 0.05, 0.02, 1.06, -0.13)

    # A barrel alongside, on its side, with the hoops proud of the staves.
    parts.append(cylinder("barrel", 0.52, 1.30, (-1.55, 0.85, 0.54), WOOD,
                          vertices=8, rot=(math.pi / 2, 0, 0.35)))
    for i, dy in enumerate((-0.40, 0.40)):
        parts.append(cylinder(f"hoop{i}", 0.56, 0.12,
                              (-1.55 - dy * 0.34, 0.85 + dy * 0.94, 0.54),
                              IRON, vertices=8, rot=(math.pi / 2, 0, 0.35)))
    parts.append(blk("chock", (0.34, 0.30, 0.22), (-1.55, 0.10, 0.10), BATTEN,
                     rot=(0, 0, 0.3)))
    # Straw and a spilled coin or two, so something has clearly been opened.
    patches(parts, "straw", STRAW, (
        (-1.85, -0.55, 0.75, 0.50, 0.40),
        (-1.45, -0.85, 0.50, 0.42, -0.3),
        (1.50, 0.95, 0.60, 0.45, -0.6),
        (0.95, -1.40, 0.65, 0.48, 0.15),
    ), top=0.06, thick=0.10, step=0.03)
    for i, (x, y, r) in enumerate(((1.62, 1.02, 0.16), (1.34, 1.28, 0.14),
                                   (-2.05, -0.35, 0.15))):
        parts.append(cylinder(f"coin{i}", r, 0.05, (x, y, 0.09), GOLD,
                              vertices=8, rot=(0.2 * (i - 1), 0.1, 0)))
    # A crowbar leaning on the stack -- the reason the lid is off.
    parts.append(blk("bar", (0.09, 0.09, 1.60), (1.05, -1.00, 0.72), IRON,
                     rot=(-0.42, 0.24, 0.4)))
    parts.append(blk("barclaw", (0.09, 0.26, 0.16), (1.32, -1.36, 0.08), IRON,
                     rot=(0.6, 0.24, 0.4)))
    return merge(parts, "cratestack")


def anvilplinth():
    """An anvil on a stepped plinth. Ground origin.
    **Standable top: z = 2.52**, the anvil's face, 1.60 x 1.15. (The hardy
    hole is a 2 cm boss on it and nothing else stands proud at all.)

    A landing wants somewhere to *stand*, so the face is wider and deeper
    than a real anvil's -- which is fine, because what says anvil is the
    waist and the horn, not the proportion of the face.

    The hammer leans against the plinth rather than lying on the face. It was
    on the face first, which is where a smith would leave it and where it was
    invisible: a grey hammer head on a grey anvil, against the sky. Against
    the plinth it is silhouetted, and it leaves the landing surface with
    nothing on it at all.
    """
    #: Three values, not two, and in this order: a **dark** anvil against a
    #: **pale** shaft with a **mid** base and cap between them. The first pass
    #: had the cap darker than the anvil standing on it and the whole model
    #: came back as one black mass with a stripe in it -- what tells you a
    #: thing is standing on another thing is a value change at the join.
    IRON = zone("metal", (0.26, 0.27, 0.30), rough=0.5)
    STONE = zone("stone", (0.66, 0.64, 0.58), rough=0.93)
    DARK = zone("rock", (0.44, 0.43, 0.40), rough=0.95)
    COAL = zone("ink", (0.13, 0.13, 0.14), rough=0.95)
    WOOD = zone("wood", (0.54, 0.37, 0.20), rough=0.9)
    PALE = zone("gold", (0.74, 0.72, 0.66), rough=0.4)

    parts = []
    parts.append(blk("base", (2.00, 1.90, 0.36), (0, 0, 0.16), DARK))
    parts.append(blk("shaft", (1.52, 1.44, 0.96), (0, 0, 0.82), STONE))
    parts.append(blk("cap", (1.78, 1.68, 0.28), (0, 0, 1.42), DARK))
    # A corner knocked off the cap, and one course of the shaft sitting proud.
    # The chisel "scar" that used to be here was a dark rectangle on a pale
    # face and read as a letterbox.
    parts.append(blk("chip", (0.42, 0.38, 0.30), (-0.82, 0.74, 1.34), STONE,
                     rot=(0.3, 0.4, 0.6)))
    parts.append(blk("course", (1.58, 1.50, 0.20), (0.02, 0.0, 0.60), STONE,
                     rot=(0, 0, 0.04)))

    # The anvil: foot, waist, face, horn, heel.
    parts.append(blk("foot", (1.40, 1.00, 0.24), (0, 0, 1.62), IRON))
    parts.append(blk("waist", (0.76, 0.62, 0.30), (0, 0, 1.88), IRON))
    parts.append(blk("face", (1.60, 1.15, 0.42), (0, 0, 2.31), IRON))
    for i, (w, d, h, x) in enumerate(((0.44, 0.80, 0.34, 1.02),
                                      (0.30, 0.52, 0.24, 1.34))):
        parts.append(blk(f"horn{i}", (w, d, h), (x, 0, 2.24 - 0.03 * i), IRON,
                         rot=(0, 0.10 + 0.12 * i, 0)))
    parts.append(blk("heel", (0.36, 0.90, 0.30), (-1.02, 0, 2.22), IRON))
    parts.append(blk("hardy", (0.18, 0.18, 0.08), (-0.52, 0.0, 2.50), COAL))

    # The hammer, stood against the plinth: head on the ground, haft leaning.
    parts.append(blk("hammerhead", (0.36, 0.58, 0.36), (1.18, -0.86, 0.18),
                     IRON, rot=(0, 0, -0.4)))
    parts.append(blk("haft", (0.12, 0.12, 1.40), (1.02, -1.02, 0.88), WOOD,
                     rot=(-0.30, 0.16, -0.4)))
    # Ingots and a bent sword at the foot.
    for i, (x, y, yaw, tl) in enumerate(((1.45, 0.90, 0.4, 0.0),
                                         (1.60, 0.55, -0.2, 0.0),
                                         (1.30, 0.62, 0.9, 0.25))):
        parts.append(blk(f"ingot{i}", (0.46, 0.22, 0.14),
                         (x, y, 0.07 + i * 0.10), PALE,
                         rot=(tl, 0, yaw)))
    parts.append(blk("coal", (0.62, 0.56, 0.22), (-1.25, -0.85, 0.10), COAL,
                     rot=(0, 0, 0.5)))
    parts.append(blk("coal1", (0.34, 0.30, 0.18), (-1.55, -0.45, 0.08), COAL,
                     rot=(0.2, 0, -0.4)))
    parts.append(blk("blade", (0.10, 1.50, 0.05), (-1.35, -0.30, 0.85), IRON,
                     rot=(0.9, 0.2, -0.3)))
    parts.append(blk("hilt", (0.34, 0.10, 0.08), (-1.52, -0.86, 0.20), WOOD,
                     rot=(0.9, 0.2, -0.3)))
    return merge(parts, "anvilplinth")


def boathull():
    """A clinker boat upturned on two trestles. Ground origin.
    **Standable top: z = 2.28**, the flat bottom, 1.52 x 4.60.

    Four cells of landing in a line, which is the most useful shape in the
    standable set -- a course can run *along* this rather than touch it once.

    **Clinker, not carvel**, and that is what rescued this asset. The first
    version was a bottom plate with two splayed side panels, and it read
    as a wooden crate from every heading: a boat's hull is a curve, a splayed
    panel is a facet, and one facet is a wall. Four *stepped* strakes, each a
    little wider and a little longer than the one above, give the same curve
    as a stack of overlapping planks -- which is exactly what a clinker boat
    is, is trivially free of coplanar faces because every strake's top is a
    different height, and is far more Minecraft than a smooth hull would be.

    Flat-bottomed on purpose. A keel is the honest shape and it would put a
    ridge down the middle of the only flat top here.
    """
    HULL = zone("wood", (0.56, 0.40, 0.23), rough=0.92)
    PLANK = zone("stem", (0.44, 0.30, 0.17), rough=0.92)
    TRIM = zone("rust", (0.36, 0.22, 0.13), rough=0.92)
    ROPE = zone("straw", (0.78, 0.70, 0.48), rough=0.95)
    TIMBER = zone("rock", (0.40, 0.32, 0.22), rough=0.95)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)
    DARK = zone("ink", (0.13, 0.11, 0.10), rough=0.95)

    parts = []
    # Two trestles, an A-frame each. Rocks were tried and read as a boat that
    # had been dropped rather than one that had been hauled out.
    for k, (y, h) in enumerate(((-1.45, 1.16), (1.35, 1.12))):
        for s in (-1, 1):
            parts.append(span(f"leg{k}{s}", (s * 1.15, 0.0), (s * 0.42, h),
                              0.20, 0.24, TIMBER, y=y))
        parts.append(blk(f"tie{k}", (1.90, 0.18, 0.16), (0, y, h * 0.45),
                         TIMBER))
        parts.append(blk(f"pad{k}", (1.30, 0.34, 0.18), (0, y, h + 0.05),
                         TIMBER))

    # The hull, upside down: four strakes, widest and longest at the bottom
    # of the stack (which is the sheer). Each overlaps the one above by 4 cm.
    for i, (w, ln, z0, h) in enumerate(((1.52, 4.60, 1.98, 0.30),
                                        (1.76, 4.94, 1.70, 0.32),
                                        (1.94, 5.20, 1.42, 0.32),
                                        (2.06, 5.40, 1.12, 0.34))):
        parts.append(blk(f"strake{i}", (w, ln, h), (0, 0, z0 + h / 2),
                         HULL if i % 2 == 0 else PLANK))
    # The sheer rail along the bottom edge, and two rubbing strakes.
    parts.append(blk("sheer", (2.14, 5.44, 0.14), (0, 0, 1.18), TRIM))
    for s in (-1, 1):
        parts.append(blk(f"rub{s}", (0.12, 5.10, 0.14), (s * 1.00, 0, 1.86),
                         TRIM))

    # The bow: three boxes stepping forward and narrowing, plus a stem post.
    for i, (w, ln, y, z0, h) in enumerate(((1.44, 0.60, 2.86, 1.28, 0.96),
                                           (1.00, 0.55, 3.28, 1.42, 0.78),
                                           (0.58, 0.50, 3.62, 1.56, 0.60))):
        parts.append(blk(f"bow{i}", (w, ln, h), (0, y, z0 + h / 2), HULL))
    parts.append(blk("stempost", (0.30, 0.42, 1.10), (0, 3.80, 1.72), TRIM,
                     rot=(-0.18, 0, 0)))
    # The transom at -Y, raked.
    parts.append(blk("transom", (1.86, 0.20, 1.20), (0, -2.78, 1.72), PLANK,
                     rot=(-0.16, 0, 0)))
    parts.append(blk("transtrim", (1.94, 0.14, 0.16), (0, -2.72, 2.24), TRIM))

    # Ribs across the bottom: three, thin, the only things proud of the
    # landing surface, and 8 cm is what a foot ignores.
    for i, y in enumerate((-1.55, 0.0, 1.55)):
        parts.append(blk(f"rib{i}", (1.56, 0.16, 0.08), (0, y, 2.30), PLANK))
    # The hole somebody stove in her, and the splinters round it.
    parts.append(blk("hole", (0.14, 0.70, 0.46), (-0.98, -0.90, 1.62), DARK))
    for i, (dy, dz, tl) in enumerate(((-1.28, 1.80, 0.5), (-0.58, 1.42, -0.7))):
        parts.append(blk(f"splint{i}", (0.18, 0.36, 0.22), (-1.00, dy, dz),
                         HULL, rot=(tl, 0.2, 0.2)))
    # An oar against the transom, a coil of rope, moss where she sits.
    parts.append(blk("oar", (0.11, 0.11, 2.70), (1.35, -2.30, 1.20), HULL,
                     rot=(-0.55, 0.28, 0.2)))
    parts.append(blk("oarblade", (0.32, 0.10, 0.72), (1.92, -3.20, 0.30),
                     HULL, rot=(-0.55, 0.28, 0.2)))
    for i, r in enumerate((0.42, 0.32, 0.22)):
        parts.append(cylinder(f"coil{i}", r, 0.10,
                              (-1.85, 2.00, 0.06 + i * 0.09), ROPE,
                              vertices=8))
    patches(parts, "moss", MOSS, (
        (1.55, 1.35, 0.62, 0.50, 0.40),
        (1.28, 1.62, 0.44, 0.42, -0.2),
        (-1.65, -0.95, 0.50, 0.60, 0.7),
    ))
    return merge(parts, "boathull")


def tomestack():
    """Three enormous books on a step. Ground origin.
    **Standable top: z = 2.26**, the top cover, 2.06 x 1.58.

    Each book is a cover-pages-cover sandwich with a spine, and the covers
    *overhang* the pages by six centimetres on three sides. That overhang is
    the entire read: without it a book is a slab, and three slabs are a
    staircase.

    The bookmark hangs out of the middle volume and the loose page is on the
    ground beside it, because a stack of shut books is furniture and a stack
    somebody was working through is a scene.
    """
    STONE = zone("stone", (0.58, 0.56, 0.52), rough=0.93)
    LEATHER = zone("leaf", (0.42, 0.20, 0.22), rough=0.85)
    COVER2 = zone("stem", (0.24, 0.32, 0.44), rough=0.85)
    COVER3 = zone("wood", (0.36, 0.30, 0.18), rough=0.88)
    PAGES = zone("paper", (0.90, 0.86, 0.74), rough=0.95)
    GOLD = zone("gold", (0.84, 0.70, 0.30), rough=0.35)
    RIBBON = zone("cloth", (0.72, 0.24, 0.26), rough=0.9)
    GLOW = zone("glow", (1.0, 0.86, 0.52), rough=0.25)

    parts = []
    parts.append(blk("step0", (2.60, 2.40, 0.34), (0, 0, 0.15), STONE))
    parts.append(blk("step1", (2.30, 2.10, 0.28), (0.05, -0.05, 0.44), STONE,
                     rot=(0, 0, 0.06)))

    def book(tag, w, d, z0, yaw, cover):
        """Bottom cover, pages, top cover, spine. Heights chosen so nothing is
        coplanar with anything: the pages start 1 cm inside the lower cover
        and finish 1 cm inside the upper one."""
        parts.append(blk(f"{tag}c0", (w, d, 0.10), (0, 0, z0 + 0.05), cover,
                         rot=(0, 0, yaw)))
        parts.append(blk(f"{tag}p", (w - 0.13, d - 0.13, 0.36),
                         (0.03, 0, z0 + 0.27), PAGES, rot=(0, 0, yaw)))
        parts.append(blk(f"{tag}c1", (w, d, 0.12), (0, 0, z0 + 0.49), cover,
                         rot=(0, 0, yaw)))
        parts.append(blk(f"{tag}spine", (0.18, d + 0.04, 0.62),
                         (-w / 2 + 0.02, 0, z0 + 0.30), cover,
                         rot=(0, 0, yaw)))
        for i in range(2):
            parts.append(blk(f"{tag}gild{i}", (0.10, d * 0.22, 0.07),
                             (-w / 2 - 0.02, (i - 0.5) * d * 0.45,
                              z0 + 0.20 + i * 0.24), GOLD, rot=(0, 0, yaw)))
        return z0 + 0.55

    z = book("b0", 2.20, 1.72, 0.56, 0.00, LEATHER)
    z = book("b1", 2.10, 1.64, z - 0.03, 0.26, COVER2)
    z = book("b2", 2.06, 1.58, z - 0.03, -0.17, COVER3)
    # A gold device on the top board, four centimetres proud.
    parts.append(blk("device", (0.44, 0.44, 0.06), (0.10, 0.06, 2.27), GOLD,
                     rot=(0, 0, 0.6)))
    # The bookmark, out of the middle volume and down its side.
    parts.append(blk("mark0", (0.34, SHEET * 3, 0.22), (0.92, 0.30, 1.42),
                     RIBBON, rot=(0, 0, 0.26)))
    parts.append(blk("mark1", (0.26, SHEET * 3, 0.60), (1.08, 0.34, 1.06),
                     RIBBON, rot=(0.12, 0.10, 0.26)))
    # A page that got away, and a candle stub burning on the step.
    parts.append(blk("loose", (0.80, 0.62, SHEET * 2), (1.72, -1.10, 0.62),
                     PAGES, rot=(0.14, -0.20, 0.5)))
    parts.append(blk("holder", (0.36, 0.36, 0.08), (-1.05, 0.92, 0.62), GOLD))
    parts.append(blk("candle", (0.18, 0.18, 0.40), (-1.05, 0.92, 0.86), PAGES))
    parts.append(blk("flame", (0.10, 0.10, 0.16), (-1.05, 0.92, 1.13), GLOW,
                     bevel=0.03))
    return merge(parts, "tomestack")


def layercake():
    """A two-tier cake on a stand, one slice out. Ground origin.
    **Standable top: z = 2.82**, the top icing, 1.90 x 1.90.

    The slice is out of the **bottom** tier and not the top, and that is a
    constraint rather than a preference: an L-shaped tier is two overlapping
    slabs, and two overlapping slabs at one height bake as a black rectangle.
    :func:`plates` steps them five centimetres apart, which is invisible in a
    cake and would be a hole in a landing -- so the top tier stays one box
    with one slab of icing on it and is dead flat.

    The candles are on the rim. A candle in the middle of the only flat top
    in the asset would be a joke played on whoever has to land there.
    """
    SPONGE = zone("sponge", (0.78, 0.58, 0.34), rough=0.95)
    ICING = zone("icing", (0.95, 0.93, 0.88), rough=0.8)
    JAM = zone("leaf", (0.68, 0.16, 0.22), rough=0.85)
    PLATE = zone("stone", (0.66, 0.64, 0.60), rough=0.85)
    WAX = zone("cloth", (0.86, 0.78, 0.62), rough=0.9)
    GLOW = zone("glow", (1.0, 0.84, 0.46), rough=0.25)
    CHERRY = zone("flesh", (0.72, 0.14, 0.18), rough=0.5)

    parts = []
    # The stand: a foot, a stem, and a plate wider than the cake.
    parts.append(cylinder("foot", 1.05, 0.24, (0, 0, 0.11), PLATE, vertices=8))
    parts.append(blk("stem", (0.72, 0.72, 0.72), (0, 0, 0.56), PLATE))
    parts.append(cylinder("plate", 1.70, 0.22, (0, 0, 1.00), PLATE,
                          vertices=8))

    # Bottom tier, L-shaped: a bite out of the +X +Y quarter. Two slabs,
    # stepped, and the jam layer between them stepped the same way.
    #
    # The two slabs **overlap in plan and their side faces are offset**, and
    # that is a second lesson on top of the coplanar-tops one. Built to meet
    # exactly at y=0.22 with their -X faces both at -1.22 they shared two
    # whole planes down the side of the cake, and the render came back with a
    # zigzag of z-fighting all the way down the left-hand edge. ``plates``
    # only guarantees the *tops* are apart; the caller has to keep the sides
    # apart too.
    L = ((2.44, 1.52, 0.00, -0.44, 0.0),
         (1.26, 1.16, -0.58, 0.58, 0.0))
    plates(parts, "tier0", SPONGE, L, top=1.62, thick=0.52, step=0.05)
    plates(parts, "jam", JAM, tuple((w + 0.02, d + 0.02, x, y, r)
                                    for w, d, x, y, r in L),
           top=1.76, thick=0.16, step=0.05)
    plates(parts, "tier0b", SPONGE, L, top=1.98, thick=0.26, step=0.05)
    plates(parts, "ice0", ICING, tuple((w + 0.10, d + 0.10, x, y, r)
                                       for w, d, x, y, r in L),
           top=2.10, thick=0.16, step=0.05)
    # The cut faces, showing the crumb where the slice came out.
    parts.append(blk("cut0", (0.12, 1.10, 0.64), (0.66, 0.60, 1.70), JAM))
    parts.append(blk("cut1", (1.32, 0.12, 0.64), (-0.56, 0.34, 1.70), JAM))
    # The slice itself, on its side on the plate. Flatter and smaller than the
    # first pass, which stood up as tall as the tier it came out of and read
    # as a second cake nobody had explained.
    parts.append(blk("slice", (0.78, 0.62, 0.34), (1.14, 0.92, 1.30), SPONGE,
                     rot=(0.10, 0.55, 0.5)))
    parts.append(blk("slicetop", (0.72, 0.58, 0.10), (1.28, 1.00, 1.40),
                     ICING, rot=(0.10, 0.55, 0.5)))

    # Top tier: one box, one slab of icing, dead flat.
    parts.append(blk("tier1", (1.80, 1.80, 0.62), (0, 0, 2.41), SPONGE))
    parts.append(blk("ice1", (1.90, 1.90, 0.16), (0, 0, 2.74), ICING))
    # Drips down the sides, hanging off the icing rather than resting on it.
    for i, (x, y, w, h) in enumerate(((-0.70, 0.95, 0.24, 0.34),
                                      (0.30, 0.95, 0.18, 0.22),
                                      (0.95, -0.20, 0.20, 0.40),
                                      (-0.95, -0.55, 0.22, 0.26))):
        parts.append(blk(f"drip{i}", (w, w, h), (x, y, 2.70 - h / 2), ICING))
    # Candles and cherries, all on the rim, centre left clear.
    for i, (x, y) in enumerate(((-0.72, -0.72), (0.72, -0.72), (0.72, 0.72),
                                (-0.72, 0.72))):
        parts.append(blk(f"candle{i}", (0.13, 0.13, 0.46), (x, y, 3.03), WAX,
                         rot=(0, 0.05 * (i - 1.5), 0)))
        parts.append(blk(f"wick{i}", (0.09, 0.09, 0.15), (x, y, 3.32), GLOW,
                         bevel=0.03))
    for i, (x, y) in enumerate(((0.0, -0.76), (-0.76, 0.10), (0.76, 0.28))):
        parts.append(blk(f"cherry{i}", (0.24, 0.24, 0.24), (x, y, 2.92),
                         CHERRY, bevel=0.08))
    return merge(parts, "layercake")


# ---------------------------------------------------------------------------
# Things that are simply odd
# ---------------------------------------------------------------------------

def bucketcrow():
    """A scarecrow with a bucket on its head. Ground origin.

    ``props_land.scarecrow`` is the straight version and stands in a pumpkin
    field. This is the joke: the bucket is over its eyes, and there is a crow
    sitting on the crossbar four feet away.

    The bucket is tipped twelve degrees and the whole figure leans on its
    post, because a scarecrow that is plumb is a signpost with a shirt on.
    """
    WOOD = zone("wood", (0.44, 0.32, 0.19), rough=0.92)
    STRAW = zone("straw", (0.84, 0.72, 0.36), rough=0.95)
    CLOTH = zone("cloth", (0.40, 0.46, 0.56), rough=0.92)
    IRON = zone("metal", (0.52, 0.54, 0.58), rough=0.45)
    CROW = zone("ink", (0.11, 0.11, 0.13), rough=0.85)
    BEAK = zone("gold", (0.80, 0.62, 0.22), rough=0.5)
    DIRT = zone("rock", (0.38, 0.33, 0.26), rough=0.95)

    lean = 0.09
    parts = []
    rubble(parts, "mound", DIRT, (
        (0.0, 0.0, 0.95, 0.90, 0.42, 14, 5),
        (0.48, -0.42, 0.62, 0.55, 0.26, -40, 7),
        (-0.40, 0.36, 0.50, 0.48, 0.20, 33, -9),
    ))
    parts.append(blk("post", (0.20, 0.20, 3.10), (0, 0, 1.60), WOOD,
                     rot=(0, lean, 0)))
    parts.append(blk("crossbar", (2.50, 0.16, 0.16), (-0.14, 0, 2.12), WOOD,
                     rot=(0, lean, 0.06)))
    # Body: a sack shirt, hanging off the bar and not quite square to it.
    parts.append(blk("shirt", (0.92, 0.60, 1.15), (-0.10, 0.02, 1.62), CLOTH,
                     rot=(0.03, lean, 0.14)))
    parts.append(blk("belt", (0.96, 0.64, 0.14), (-0.10, 0.02, 1.12), WOOD,
                     rot=(0.03, lean, 0.14)))
    parts.append(blk("patch", (0.30, 0.10, 0.28), (0.20, -0.30, 1.70), STRAW,
                     rot=(0.03, lean, 0.14)))
    # Straw out of the cuffs and the hem. Small: at 0.62 across these read as
    # gold epaulettes rather than as straw coming out of a sleeve.
    for i, (x, y, z, tl) in enumerate(((-1.12, 0.0, 1.96, 0.5),
                                       (-1.26, 0.10, 1.88, 0.9),
                                       (0.92, 0.0, 2.04, -0.5),
                                       (-0.10, 0.0, 1.00, 0.0),
                                       (0.16, -0.12, 0.98, 0.3))):
        cross(parts, f"wisp{i}", 0.30, 0.34, (x, y, z), STRAW, tilt=tl)
    # A mitten on one hand, because one is funnier than two.
    parts.append(blk("mitten", (0.26, 0.22, 0.30), (-1.34, 0.0, 2.02), CLOTH,
                     rot=(0.3, 0, 0.2)))
    # Head: a straw ball, and the bucket over it.
    parts.append(blk("head", (0.52, 0.50, 0.50), (-0.20, 0.0, 2.48), STRAW,
                     bevel=0.14))
    parts.append(cylinder("bucket", 0.42, 0.72, (-0.24, 0.02, 2.78), IRON,
                          vertices=8, rot=(0.21, 0, 0.3)))
    parts.append(cylinder("bucketrim", 0.46, 0.10, (-0.32, 0.04, 2.46), IRON,
                          vertices=8, rot=(0.21, 0, 0.3)))
    # The bail, hanging down over the face. A bucket the right way up carries
    # its handle over the top; upside down on somebody's head it hangs where
    # their eyes are, which is the joke twice.
    bail = ((-0.68, 2.54), (-0.76, 2.16), (-0.24, 2.00), (0.28, 2.16),
            (0.20, 2.54))
    for i in range(4):
        parts.append(span(f"bail{i}", bail[i], bail[i + 1], 0.07, 0.07, IRON,
                          y=-0.34))
    # The crow, on the far end of the bar. Facing the scarecrow.
    parts.append(blk("crowbody", (0.26, 0.44, 0.28), (1.02, 0.0, 2.34), CROW,
                     rot=(0, 0, 0.15)))
    parts.append(blk("crowhead", (0.20, 0.20, 0.20), (0.98, -0.28, 2.52), CROW))
    parts.append(blk("crowbeak", (0.09, 0.20, 0.08), (0.98, -0.44, 2.50), BEAK))
    parts.append(blk("crowtail", (0.14, 0.30, 0.07), (1.06, 0.32, 2.30), CROW,
                     rot=(-0.3, 0, 0.15)))
    parts.append(blk("crowwing", (0.07, 0.34, 0.20), (1.16, 0.0, 2.34), CROW,
                     rot=(0, 0.2, 0.15)))
    # A boot somebody left at the foot of the post.
    parts.append(blk("boot", (0.28, 0.44, 0.24), (0.80, 0.72, 0.20), WOOD,
                     rot=(0.1, 0.2, -0.6)))
    return merge(parts, "bucketcrow")


def oddshrine():
    """A shrine, a lopsided idol, and what has been left for it. Ground
    origin.

    A niche on a plinth, open along **+Y** so it faces whoever is running
    past, with a roof of two boards and a finial. The idol inside is
    deliberately badly made -- head far too big, one eye lower than the other,
    no neck -- because a well-carved one reads as a statue and the point is
    that somebody's uncle made this.

    Among the offerings there is a rubber duck. That is not a slip.
    """
    STONE = zone("stone", (0.62, 0.60, 0.55), rough=0.93)
    DARK = zone("rock", (0.40, 0.39, 0.36), rough=0.95)
    WOOD = zone("wood", (0.48, 0.33, 0.19), rough=0.9)
    IDOL = zone("stem", (0.52, 0.50, 0.42), rough=0.92)
    GLOW = zone("glow", (1.0, 0.84, 0.48), rough=0.25)
    GOLD = zone("gold", (0.84, 0.70, 0.30), rough=0.35)
    DUCK = zone("flesh", (0.94, 0.80, 0.20), rough=0.5)
    BEAK = zone("rust", (0.90, 0.46, 0.14), rough=0.6)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)
    APPLE = zone("leaf", (0.68, 0.18, 0.18), rough=0.7)

    parts = []
    parts.append(blk("plinth0", (2.00, 1.60, 0.34), (0, 0, 0.15), DARK))
    parts.append(blk("plinth1", (1.66, 1.30, 0.42), (0, -0.06, 0.52), STONE))
    # The niche: back, two cheeks, a floor slab set down into the plinth.
    parts.append(blk("back", (1.34, 0.20, 1.30), (0, -0.48, 1.38), STONE))
    for s in (-1, 1):
        parts.append(blk(f"cheek{s}", (0.20, 0.86, 1.24),
                         (s * 0.57, -0.10, 1.35), STONE))
    parts.append(blk("niche", (1.20, 0.80, 0.10), (0, -0.12, 0.76), DARK))
    # Roof: two boards leaning together, plus a ridge and a finial.
    #
    # **Raised, and pulled back off the front.** Springing at 1.92 with a
    # 1.30 m spread, the eave came down right across the opening and the idol
    # -- the whole reason there is a niche -- was invisible from in front,
    # which is the one heading this thing is ever seen from. It now springs at
    # 2.22 and its bulk sits behind the opening rather than over it.
    for s in (-1, 1):
        parts.append(span(f"roof{s}", (s * 1.05, 2.22), (0.0, 2.70), 0.20,
                          1.10, WOOD, y=-0.24))
    parts.append(blk("ridge", (0.34, 1.22, 0.16), (0, -0.24, 2.72), WOOD))
    parts.append(blk("finial", (0.16, 0.16, 0.30), (0, -0.24, 2.90), GOLD))
    # A lintel across the front, so the opening has a top edge without the
    # roof having to come down and provide one.
    parts.append(blk("lintel", (1.56, 0.22, 0.22), (0, 0.24, 2.02), WOOD))

    # The idol: too much head, not enough everything else. Stood **forward**
    # in the niche and up on a low block, for the same reason as the roof.
    parts.append(blk("idolstand", (0.60, 0.50, 0.14), (0, -0.06, 0.86), DARK))
    parts.append(blk("idolbody", (0.42, 0.34, 0.44), (0, -0.06, 1.14), IDOL,
                     rot=(0, 0, 0.12)))
    parts.append(blk("idolhead", (0.62, 0.52, 0.56), (0.02, -0.08, 1.62), IDOL,
                     rot=(0.05, 0.08, -0.1)))
    for i, (x, z, s) in enumerate(((-0.16, 1.68, 0.11), (0.16, 1.62, 0.09))):
        parts.append(blk(f"eye{i}", (s, 0.10, s), (x, 0.16, z), DARK))
    parts.append(blk("idolmouth", (0.24, 0.09, 0.06), (0.0, 0.16, 1.46),
                     DARK, rot=(0, 0.2, 0)))
    parts.append(blk("idolarm", (0.44, 0.14, 0.12), (0.0, -0.08, 1.28), IDOL,
                     rot=(0, 0.3, 0)))

    # Offerings on the step, in a row nobody straightened.
    for i, (x, r, h) in enumerate(((-0.62, 0.20, 0.12), (-0.20, 0.17, 0.10),
                                   (0.24, 0.19, 0.11))):
        parts.append(cylinder(f"bowl{i}", r, h, (x, 0.42, 0.78 + h / 2), DARK,
                              vertices=8))
    parts.append(blk("apple", (0.20, 0.20, 0.20), (-0.20, 0.42, 0.96), APPLE,
                     bevel=0.06))
    parts.append(blk("coins", (0.30, 0.26, 0.09), (0.24, 0.42, 0.90), GOLD,
                     rot=(0, 0, 0.4)))
    # The duck.
    parts.append(blk("duckbody", (0.26, 0.34, 0.20), (0.66, 0.40, 0.83), DUCK,
                     bevel=0.07, rot=(0, 0, -0.3)))
    parts.append(blk("duckhead", (0.18, 0.18, 0.19), (0.62, 0.24, 1.00), DUCK,
                     bevel=0.05))
    parts.append(blk("duckbeak", (0.10, 0.14, 0.07), (0.61, 0.13, 0.98), BEAK))
    # Two candles either side, and incense burning in the left-hand bowl.
    for s in (-1, 1):
        parts.append(blk(f"post{s}", (0.14, 0.14, 1.05), (s * 1.00, 0.55, 0.52),
                         WOOD))
        parts.append(blk(f"lant{s}", (0.28, 0.28, 0.30), (s * 1.00, 0.55, 1.18),
                         GLOW, bevel=0.05))
        parts.append(blk(f"lantcap{s}", (0.36, 0.36, 0.08),
                         (s * 1.00, 0.55, 1.37), WOOD))
    parts.append(blk("incense", (0.03, 0.03, 0.40), (-0.62, 0.42, 1.02), WOOD,
                     rot=(0, 0.14, 0)))
    parts.append(blk("ember", (0.06, 0.06, 0.06), (-0.59, 0.42, 1.23), GLOW,
                     bevel=0.02))
    patches(parts, "moss", MOSS, (
        (-1.20, -0.55, 0.56, 0.44, 0.30),
        (-1.00, -0.82, 0.40, 0.38, -0.4),
    ))
    return merge(parts, "oddshrine")


def blockjenga():
    """A stack of blocks that should not be standing. Ground origin.

    Eight cubes, each smaller than the last, each yawed further round and
    tipped a little more, on a base narrower than the stack is tall. The lean
    accumulates -- the top block's centre is a metre out over the edge of the
    bottom one -- which is the only way a stack reads as *precarious* rather
    than merely untidy.

    Eight rather than the ten it started with, and that is a placement
    constraint rather than a look: ten came out **seven metres tall**, which
    on a terrace with the course flying two or three blocks up is a tower
    standing in the middle of the parkour rather than beside it.

    Materials alternate so it looks like a magpie assembled it. One block near
    the bottom is obviously slipping out, and one small one is wedged under
    the lean holding the whole thing up, which is funnier than a straight
    tower and is also, just about, structurally an argument.
    """
    STONE = zone("stone", (0.60, 0.58, 0.54), rough=0.93)
    WOOD = zone("wood", (0.55, 0.38, 0.21), rough=0.9)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)
    GOLD = zone("gold", (0.84, 0.70, 0.28), rough=0.35)
    IRON = zone("metal", (0.45, 0.47, 0.50), rough=0.5)
    GLOW = zone("glow", (1.0, 0.86, 0.52), rough=0.25)

    mats = (STONE, WOOD, MOSS, STONE, GOLD, WOOD, IRON, MOSS)
    parts = []
    z, x, y = 0.0, 0.0, 0.0
    for i, mat in enumerate(mats):
        s = 1.15 - 0.09 * i
        h = s * (0.80 if i % 3 else 0.62)
        # Each block sits 4 cm down into the one below: exact abutment leaves
        # a hairline the bake outlines in black.
        parts.append(blk(f"blk{i}", (s, s * 0.94, h), (x, y, z + h / 2 - 0.04),
                         mat, rot=(math.radians(3.5 * math.sin(i * 1.7)),
                                   math.radians(4.0 + 1.1 * i),
                                   0.34 * i)))
        z += h - 0.04
        x += 0.095 + 0.016 * i
        y += 0.034 * math.sin(i * 2.1)
    # The one that is on its way out: hanging clear of the stack on the -Y
    # face, so it breaks the silhouette from every heading rather than only
    # from the one it was placed against.
    parts.append(blk("slip", (0.98, 1.10, 0.34), (0.08, -0.70, 1.34), IRON,
                     rot=(-0.30, 0.08, 0.5)))
    parts.append(blk("slipped", (0.58, 0.54, 0.26), (0.30, -1.20, 0.16), IRON,
                     rot=(0.3, 0.4, 1.3)))
    # The wedge holding it all up, and what it is standing on.
    parts.append(blk("wedge", (0.44, 0.40, 0.34), (0.62, -0.10, 0.17), WOOD,
                     rot=(0, -0.30, 0.4)))
    parts.append(blk("slab", (1.70, 1.60, 0.22), (0.10, 0.0, 0.06), STONE,
                     rot=(0, 0, 0.12)))
    # A lantern on the top block, because of course there is.
    parts.append(blk("lamp", (0.26, 0.26, 0.28), (x + 0.02, y, z + 0.18), GLOW,
                     bevel=0.05))
    parts.append(blk("lampcap", (0.34, 0.34, 0.07), (x + 0.02, y, z + 0.35),
                     IRON))
    return merge(parts, "blockjenga")


def signpost():
    """Six arms, one up, one down, none of them anywhere. Ground origin.

    The arms are at six heights and six bearings, and two of them are the
    joke: one points **straight up** and one points **straight down**. A third
    has snapped in the middle and hangs off its nail.

    A pointed end is a small box yawed forty-five degrees at the tip of a
    board -- a diamond in plan, which at ten metres is an arrowhead for eight
    triangles.
    """
    WOOD = zone("wood", (0.56, 0.40, 0.22), rough=0.92)
    DARK = zone("stem", (0.34, 0.24, 0.14), rough=0.92)
    PAINT = zone("paper", (0.88, 0.84, 0.72), rough=0.9)
    IRON = zone("metal", (0.46, 0.47, 0.50), rough=0.5)
    GLOW = zone("glow", (1.0, 0.85, 0.50), rough=0.25)
    DIRT = zone("rock", (0.40, 0.35, 0.27), rough=0.95)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)

    parts = []
    rubble(parts, "mound", DIRT, (
        (0.0, 0.0, 1.00, 0.92, 0.46, 16, 6),
        (-0.48, 0.40, 0.62, 0.58, 0.30, -34, 8),
        (0.42, -0.36, 0.55, 0.50, 0.24, 47, -7),
    ))
    parts.append(blk("post", (0.24, 0.24, 3.30), (0, 0, 1.70), WOOD,
                     rot=(0, 0.05, 0)))

    def arm(tag, z, yaw, length, tilt=0.0, mat=PAINT):
        """A board sticking out from the post at ``yaw``, point outward."""
        dx, dy = math.cos(yaw), math.sin(yaw)
        mid = length / 2 + 0.16
        parts.append(blk(f"{tag}board", (length, 0.10, 0.34),
                         (dx * mid, dy * mid, z), mat,
                         rot=(0, tilt, yaw)))
        parts.append(blk(f"{tag}tip", (0.30, 0.11, 0.30),
                         (dx * (mid + length / 2 - 0.02),
                          dy * (mid + length / 2 - 0.02),
                          z - math.sin(tilt) * length / 2), mat,
                         rot=(0, tilt, yaw + math.pi / 4)))
        # Two bars of "writing", which is all a sign needs at ten metres.
        for i in range(2):
            parts.append(blk(f"{tag}txt{i}", (length * 0.45, 0.06, 0.055),
                             (dx * (mid - 0.06), dy * (mid - 0.06) - 0.055,
                              z + 0.07 - i * 0.13), DARK,
                             rot=(0, tilt, yaw)))

    arm("a0", 3.02, 0.35, 1.15)
    arm("a1", 2.62, 2.60, 0.95, tilt=0.10)
    arm("a2", 2.20, 4.30, 1.25, tilt=-0.08)
    arm("a3", 1.72, 1.55, 0.85, tilt=0.16)
    # Straight up, and straight down.
    parts.append(blk("upboard", (0.34, 0.11, 1.05), (0.28, 0.10, 3.62), PAINT,
                     rot=(0, 0.06, 0.5)))
    parts.append(blk("uptip", (0.30, 0.11, 0.30), (0.30, 0.11, 4.14), PAINT,
                     rot=(0, math.pi / 4 + 0.06, 0.5)))
    parts.append(blk("dnboard", (0.32, 0.11, 0.95), (-0.30, -0.18, 1.02),
                     PAINT, rot=(0, -0.06, -0.7)))
    parts.append(blk("dntip", (0.28, 0.11, 0.28), (-0.31, -0.19, 0.52), PAINT,
                     rot=(0, math.pi / 4 - 0.06, -0.7)))
    # The one that snapped, hanging from a nail.
    parts.append(blk("brokestub", (0.42, 0.10, 0.32), (-0.42, 0.30, 2.86),
                     PAINT, rot=(0, 0, 2.52)))
    parts.append(blk("brokehang", (0.28, 0.10, 0.86), (-0.72, 0.52, 2.42),
                     PAINT, rot=(0.2, 0.35, 2.52)))
    parts.append(blk("nail", (0.06, 0.06, 0.06), (-0.55, 0.40, 2.86), IRON))
    # A lantern hung **under an arm that actually exists**. The first pass put
    # the hook at a point near no board at all and the lantern hung in mid air
    # a metre from the post, which reads as a bug rather than as a lantern.
    hx, hy = math.cos(4.30) * 1.05, math.sin(4.30) * 1.05
    parts.append(blk("hook", (0.05, 0.05, 0.24), (hx, hy, 1.92), IRON))
    parts.append(blk("lantcap", (0.32, 0.32, 0.07), (hx, hy, 1.78), IRON))
    parts.append(blk("lant", (0.26, 0.26, 0.30), (hx, hy, 1.60), GLOW,
                     bevel=0.05))
    parts.append(blk("moss0", (0.09, 0.26, 1.30), (-0.15, 0.02, 1.20), MOSS))
    return merge(parts, "signpost")


def hatrock():
    """A wizard's hat slumped on a boulder, staff still leaning. Ground
    origin.

    The cone is six shrinking boxes whose tilt *accumulates*, so the point
    ends up nearly a metre off the axis and folds over -- a straight cone is
    a traffic cone, and the difference between the two is entirely in whether
    the lean compounds.

    The staff and the book are the rest of the sentence: somebody stopped
    here, put everything down, and did not pick it up again.
    """
    ROCK = zone("rock", (0.44, 0.43, 0.41), rough=0.95)
    FELT = zone("stem", (0.24, 0.20, 0.40), rough=0.95)
    BAND = zone("cloth", (0.16, 0.13, 0.28), rough=0.9)
    GOLD = zone("gold", (0.84, 0.70, 0.28), rough=0.35)
    WOOD = zone("wood", (0.46, 0.33, 0.20), rough=0.92)
    GLOW = zone("glow", (0.72, 0.86, 1.0), rough=0.2)
    PAPER = zone("paper", (0.90, 0.86, 0.74), rough=0.95)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)

    parts = []
    rubble(parts, "rock", ROCK, (
        (0.0, 0.0, 1.70, 1.45, 1.05, 14, 6),
        (-0.55, 0.50, 1.10, 1.00, 0.75, -32, 9),
        (0.62, -0.45, 0.95, 0.85, 0.60, 47, -7),
        (1.25, 0.55, 0.60, 0.55, 0.35, 8, 11),
    ))
    # Moss on the rock's own shoulder, sunk into it rather than laid on it: a
    # slab resting on a surface leaves a hairline the bake outlines in black,
    # and one at the rim reads as a green flag stuck out sideways.
    patches(parts, "moss", MOSS, (
        (0.30, 0.62, 0.60, 0.48, 0.40),
        (0.02, 0.78, 0.42, 0.36, -0.3),
    ), top=0.96, thick=0.14, step=0.05)

    # The brim, sitting down onto the rock rather than on it.
    parts.append(cylinder("brim", 0.92, 0.14, (0, 0, 1.06), FELT, vertices=8,
                          rot=(0.06, 0.10, 0)))
    parts.append(cylinder("band", 0.66, 0.16, (0.02, 0, 1.18), BAND,
                          vertices=8, rot=(0.06, 0.10, 0)))
    parts.append(blk("buckle", (0.22, 0.10, 0.20), (0.02, -0.62, 1.20), GOLD))
    # The cone: six boxes, each tilted a little further than the last.
    x, y, z, tilt = 0.02, 0.0, 1.26, 0.10
    for i in range(6):
        s = 0.62 - 0.085 * i
        h = 0.34
        tilt += 0.16 + 0.04 * i
        x += math.sin(tilt) * h * 0.85
        parts.append(blk(f"cone{i}", (s, s, h), (x, y, z + h / 2), FELT,
                         rot=(0, tilt, 0.3 * i)))
        z += h * math.cos(tilt) * 0.94
    parts.append(blk("tip", (0.14, 0.14, 0.18), (x + 0.10, y, z), FELT,
                     rot=(0, tilt, 0)))
    parts.append(blk("star", (0.22, 0.05, 0.22), (0.28, -0.42, 1.62), GOLD,
                     rot=(0, 0.3, 0.2)))

    # The staff, leaning on the boulder, crystal at the top.
    parts.append(blk("staff", (0.10, 0.10, 2.60), (-1.25, 0.62, 1.10), WOOD,
                     rot=(-0.24, -0.30, 0.4)))
    parts.append(blk("crystal", (0.22, 0.22, 0.30), (-1.66, 0.90, 2.30), GLOW,
                     bevel=0.07, rot=(0.2, 0.3, 0.4)))
    for i, (dz, s) in enumerate(((-0.30, 0.14), (-0.55, 0.11))):
        parts.append(blk(f"knot{i}", (s, s, s * 0.8), (-1.58 + i * 0.06, 0.84,
                                                       2.30 + dz), WOOD,
                         rot=(0.2, 0.3, 0.4 + i)))
    # The book, open face up on the ground where it was dropped: a cover, two
    # low page blocks and a shallow valley between them. Built as a steep tent
    # it read as a paper hat.
    parts.append(blk("bookcov", (1.10, 0.80, 0.07), (1.30, -1.05, 0.035),
                     BAND, rot=(0, 0, 0.5)))
    for s in (-1, 1):
        parts.append(blk(f"page{s}", (0.50, 0.72, 0.11),
                         (1.30 - s * 0.24 * math.sin(0.5),
                          -1.05 + s * 0.24 * math.cos(0.5), 0.12), PAPER,
                         rot=(0, -s * 0.22, 0.5)))
    parts.append(blk("spine", (0.10, 0.74, 0.14), (1.30, -1.05, 0.10), BAND,
                     rot=(0, 0, 0.5)))
    return merge(parts, "hatrock")


def meltman():
    """A snowman most of the way to being a puddle. Ground origin.

    Three balls, each further out of line than the last, the head sliding off
    the shoulder at forty degrees; the bottom one has spread and there is meltwater
    round it. Bevels are big here -- this is the one asset in the file that
    is *supposed* to be soft, and a square snowman is a fridge.

    One eye has fallen out and is sitting on the belly. The carrot is pointing
    at the ground. The hat is off entirely.
    """
    SNOW = zone("snow", (0.94, 0.95, 0.97), rough=0.7)
    WATER = zone("water", (0.50, 0.62, 0.68), rough=0.2)
    COAL = zone("ink", (0.12, 0.12, 0.14), rough=0.85)
    CARROT = zone("rust", (0.88, 0.46, 0.14), rough=0.6)
    STICK = zone("wood", (0.40, 0.29, 0.18), rough=0.95)
    SCARF = zone("cloth", (0.70, 0.20, 0.22), rough=0.92)
    IRON = zone("metal", (0.50, 0.52, 0.56), rough=0.45)

    parts = []
    # The meltwater: four overlapping slabs at four heights, sunk. One slab
    # is a blue rectangle lying on the floor, which is what it was.
    patches(parts, "pool", WATER, (
        (0.05, 0.02, 1.95, 1.70, 0.20),
        (-0.80, -0.42, 1.25, 1.35, -0.5),
        (0.85, 0.48, 1.15, 1.05, 0.7),
        (-0.15, 0.82, 0.95, 0.80, -0.2),
    ), top=0.04, thick=0.06, step=0.022)
    # Bottom ball: spread wide and low.
    parts.append(blk("ball0", (1.70, 1.56, 0.82), (0, 0, 0.40), SNOW,
                     bevel=0.30))
    parts.append(blk("sag", (1.86, 1.68, 0.24), (0.04, 0.02, 0.14), SNOW,
                     bevel=0.10, rot=(0, 0, 0.2)))
    # Middle ball: slumped, tipped, offset.
    parts.append(blk("ball1", (1.10, 1.02, 0.95), (0.22, -0.06, 1.20), SNOW,
                     bevel=0.26, rot=(0.10, 0.22, 0.3)))
    # Head: half off, at forty degrees.
    parts.append(blk("head", (0.74, 0.70, 0.68), (0.62, -0.12, 1.92), SNOW,
                     bevel=0.20, rot=(0.14, 0.70, 0.2)))
    # Face. One eye where it should be, one on the belly.
    parts.append(blk("eye0", (0.11, 0.11, 0.11), (0.60, -0.44, 2.06), COAL))
    parts.append(blk("eye1", (0.11, 0.11, 0.11), (0.16, -0.50, 1.34), COAL,
                     rot=(0.3, 0, 0.4)))
    parts.append(blk("nose", (0.16, 0.42, 0.16), (0.72, -0.42, 1.86), CARROT,
                     rot=(0.85, 0, -0.1)))
    for i, (x, z) in enumerate(((0.44, 1.76), (0.60, 1.72), (0.76, 1.74))):
        parts.append(blk(f"mouth{i}", (0.07, 0.07, 0.07), (x, -0.44, z), COAL))
    # Buttons down what is left of the front.
    for i, (x, z) in enumerate(((0.28, 1.42), (0.22, 1.10))):
        parts.append(blk(f"button{i}", (0.12, 0.12, 0.12), (x, -0.48, z),
                         COAL))
    # Arms: one still in, one on the ground with its twigs.
    parts.append(blk("arm0", (1.15, 0.09, 0.09), (-0.55, 0.10, 1.34), STICK,
                     rot=(0, -0.35, 0.15)))
    for i, (dx, dz) in enumerate(((-0.14, 0.22), (-0.20, -0.14))):
        parts.append(blk(f"twig{i}", (0.34, 0.06, 0.06),
                         (-1.20 + dx, 0.12, 1.62 + dz), STICK,
                         rot=(0, -0.9 + i * 1.5, 0.15)))
    parts.append(blk("arm1", (1.05, 0.08, 0.08), (1.35, 0.85, 0.08), STICK,
                     rot=(0, 0.05, -0.7)))
    # The scarf, hanging off the middle ball and trailing in the water.
    parts.append(blk("scarf0", (1.14, 1.06, 0.20), (0.20, -0.04, 1.62), SCARF,
                     bevel=0.06, rot=(0.08, 0.16, 0.3)))
    parts.append(blk("scarf1", (0.30, SHEET * 4, 0.85), (-0.20, -0.52, 1.20),
                     SCARF, rot=(0.14, -0.24, 0.2)))
    parts.append(blk("scarf2", (0.32, 0.58, 0.08), (-0.44, -0.72, 0.10),
                     SCARF, rot=(0, 0, 0.6)))
    # The bucket hat, off and lying beside it. It needs the rim *and* the bail
    # or it is a grey boulder: a plain octagonal prism on its side has nothing
    # in the silhouette that says bucket.
    parts.append(cylinder("hat", 0.34, 0.56, (-1.20, -1.00, 0.32), IRON,
                          vertices=8, rot=(1.32, 0, 0.5)))
    parts.append(cylinder("hatrim", 0.40, 0.09, (-1.08, -1.26, 0.34), IRON,
                          vertices=8, rot=(1.32, 0, 0.5)))
    bail = ((-1.44, 0.62), (-1.02, 0.74), (-0.62, 0.56))
    for i in range(2):
        parts.append(span(f"hatbail{i}", bail[i], bail[i + 1], 0.06, 0.06,
                          IRON, y=-1.24))
    return merge(parts, "meltman")


def chickenstatue():
    """A monument to a chicken, with a bird sitting on it. Ground origin.

    Carved stone rather than a live chicken, which is what makes it funny:
    somebody put up a plinth, cut an inscription and commissioned this. It is
    also weathered -- a chip out of one wing, a crack down the plinth -- so it
    has been here long enough for the joke to have stopped being a joke.

    The bird on its head is a different, smaller, *painted* bird, and it is
    the only saturated thing in the model, so it is what the eye finds.
    """
    STONE = zone("stone", (0.68, 0.66, 0.60), rough=0.92)
    DARK = zone("rock", (0.42, 0.41, 0.38), rough=0.95)
    COMB = zone("leaf", (0.66, 0.18, 0.18), rough=0.8)
    BEAK = zone("gold", (0.82, 0.64, 0.22), rough=0.5)
    BIRD = zone("cloth", (0.24, 0.44, 0.68), rough=0.8)
    MOSS = zone("moss", (0.27, 0.37, 0.22), rough=0.9)

    parts = []
    parts.append(blk("base", (1.90, 1.80, 0.30), (0, 0, 0.13), DARK))
    parts.append(blk("plinth", (1.42, 1.34, 1.00), (0, 0, 0.78), STONE))
    parts.append(blk("cornice", (1.66, 1.58, 0.22), (0, 0, 1.38), DARK))
    parts.append(blk("plaque", (0.90, 0.10, 0.42), (0, -0.70, 0.92), DARK))
    # Two lines of "writing" and no more: three even bars on a dark plaque
    # read as an air vent.
    for i, (w, dz) in enumerate(((0.58, 0.06), (0.34, -0.10))):
        parts.append(blk(f"letters{i}", (w, 0.06, 0.035),
                         (-0.04 + i * 0.06, -0.76, 0.94 + dz), STONE))
    # A crack down one face, and moss at the foot.
    parts.append(blk("crack", (0.07, 0.08, 0.80), (0.44, -0.68, 0.86), DARK,
                     rot=(0, 0.14, 0)))
    patches(parts, "moss", MOSS, (
        (1.02, 0.72, 0.52, 0.42, 0.40),
        (0.76, 0.92, 0.38, 0.36, -0.3),
    ))

    # The bird. Body along Y, facing +Y, standing on two stubby legs.
    for s in (-1, 1):
        parts.append(blk(f"leg{s}", (0.13, 0.13, 0.26), (s * 0.22, 0.06, 1.60),
                         BEAK))
    parts.append(blk("body", (0.94, 1.24, 0.86), (0, 0, 2.14), STONE))
    parts.append(blk("rump", (0.72, 0.44, 0.62), (0, -0.72, 2.24), STONE,
                     rot=(0.22, 0, 0)))
    for i, (dy, dz, tl) in enumerate(((-1.00, 2.62, 0.55), (-1.22, 2.90, 0.9))):
        parts.append(blk(f"tail{i}", (0.52 - i * 0.10, 0.60, 0.14),
                         (0, dy, dz), STONE, rot=(tl, 0, 0)))
    for s in (-1, 1):
        parts.append(blk(f"wing{s}", (0.13, 0.96, 0.56), (s * 0.50, 0.02, 2.12),
                         STONE, rot=(0, 0, s * 0.05)))
    # A chunk out of the right wing.
    parts.append(blk("chipped", (0.20, 0.34, 0.26), (0.52, 0.42, 1.86), DARK,
                     rot=(0.3, 0.2, 0.4)))
    parts.append(blk("neck", (0.44, 0.44, 0.34), (0, 0.44, 2.62), STONE,
                     rot=(-0.18, 0, 0)))
    parts.append(blk("head", (0.52, 0.50, 0.48), (0, 0.54, 2.94), STONE))
    parts.append(blk("beak", (0.18, 0.30, 0.16), (0, 0.86, 2.90), BEAK))
    parts.append(blk("comb", (0.12, 0.42, 0.20), (0, 0.50, 3.24), COMB))
    parts.append(blk("wattle", (0.12, 0.16, 0.24), (0, 0.76, 2.72), COMB))
    for s in (-1, 1):
        parts.append(blk(f"eye{s}", (0.10, 0.10, 0.10), (s * 0.22, 0.72, 3.02),
                         DARK))

    # The other bird: small, blue, and looking the other way.
    parts.append(blk("bbody", (0.22, 0.34, 0.24), (0.10, 0.42, 3.42), BIRD,
                     rot=(0, 0, -0.4)))
    parts.append(blk("bhead", (0.17, 0.17, 0.17), (0.02, 0.60, 3.58), BIRD))
    parts.append(blk("bbeak", (0.07, 0.14, 0.06), (0.00, 0.72, 3.56), BEAK))
    parts.append(blk("btail", (0.11, 0.24, 0.06), (0.17, 0.24, 3.40), BIRD,
                     rot=(-0.3, 0, -0.4)))
    return merge(parts, "chickenstatue")


# The bake resolution is set by how much *surface* an asset has and how close
# it is looked at, not by how important it is. These are all seen at five to
# thirty metres, which is nearer than anything in ``props_world.py`` and much
# further than ``props_deco.py``'s hand props, so 256 across the board: at 128
# a five-metre gate is four centimetres a texel and the AO under its beams
# turns into a grey smear. The small odd ones stay at 256 too, because they
# have the most parts per cubic metre and the shadow between two of those
# parts is the whole reason the bake exists.
for name, builder, res in (
    ("torii", torii, 256),
    ("hollowlog", hollowlog, 256),
    ("brokenarch", brokenarch, 256),
    ("pipemouth", pipemouth, 256),
    ("doorframe", doorframe, 256),
    ("boneribs", boneribs, 256),
    ("bigshroom", bigshroom, 256),
    ("cratestack", cratestack, 256),
    ("anvilplinth", anvilplinth, 256),
    ("boathull", boathull, 256),
    ("tomestack", tomestack, 256),
    ("layercake", layercake, 256),
    ("bucketcrow", bucketcrow, 256),
    ("oddshrine", oddshrine, 256),
    ("blockjenga", blockjenga, 256),
    ("signpost", signpost, 256),
    ("hatrock", hatrock, 256),
    ("meltman", meltman, 256),
    ("chickenstatue", chickenstatue, 256),
):
    reset()
    run_script_banner(name)
    ob = builder()
    bake_and_export([ob], name, resolution=res)
