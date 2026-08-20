"""Does the body fly *through* blocks on its way between two landings?

The owner's report: *"there are many jumps that look impossible because there
are blocks in the way, but the player just passes through whatever blocks are
in its way and lands on the next block. This happens quite often, and visually
those blocks look off -- they don't belong there at all."*

Nothing in the project measures that. ``tools/walk_probe.py`` comes closest and
asks a narrower question in a way that cannot see it:

* it asks ``Course.blocked``, which is the **collision** answer, and the strip
  has no collision -- the body is drawn along the move whatever is there. What
  the viewer sees is the **drawn** world, which is a different collection:
  liquids, leaves, glass, webs and ladders are drawn and never solid, the
  furniture on a landing (a lamp, a post, a lintel) is drawn and is in no cell
  set at all, and a pedestal that has fallen off the back of the course is
  removed from ``solid`` while staying in the renderer's volume forever.
* it exempts, for both landings, the whole footprint **plus the pedestal, the
  footing and the soft cells**. The generator's own contract is far tighter
  (``spiralplan.Course._attempt``: only ``standing_cells`` -- a slab -- plus
  the move's own soft cells, plus the block being left for the first third of
  the path), so a hop straight down the pedestal column of the block it is
  jumping to reads clean. A probe that exempts what it is measuring reads zero
  forever, so both numbers are printed here and neither is the default.
* it samples every leg at ``0.05 m``, which is fine, but it reports one worst
  depth for the whole sweep and buckets nothing. Six causes found in an earlier
  pass on this project were invisible in the aggregate and obvious in one path.

* and it walks the *move* only. The scene plays a stretch of course as a
  **run across the landing** and then the move (``spiral.Scene._begin_ground``),
  and the run is checked nowhere at more than five points.

So this probe walks the whole played path, sampled by **distance**, asks *what
the viewer sees* -- including the eye alone, since these scenes are first
person -- buckets every hit by material, level, beat, author, move kind and
**who laid the offending cell**, and says whether that cell was laid before or
after the arc it blocks was solved, which is the number that decides where the
fix belongs.

    python tools/arc_probe.py --runs 8 --blocks 300
    python tools/arc_probe.py --plan spiral --runs 8 --blocks 300
    python tools/arc_probe.py --dump 3,142          # one offender in full
    python tools/arc_probe.py --path --run 1        # the whole course as a table

No window and no renderer: both plan modules import raylib not at all.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.scenes import handplan as hp
from brainrot.scenes import parkourkit as pk
from brainrot.scenes import spiralplan as sp

#: How finely a path is walked, in **metres of path**, not in seconds. The
#: distinction is the whole reason this probe exists: ``Move.points`` samples
#: evenly in *time* over the whole move, so a three-leg climb -- a step onto
#: the ladder, a five-second ride, a step off -- spends sixteen of its
#: seventeen samples on the ride and one or two on the two horizontal legs
#: that are the ones with scenery in them. Every check in the generator that
#: reasons about a path (``_path_clear``, and the ``pathcells`` reservation in
#: ``_commit``) goes through that same call.
STEP = 0.10

#: How near a drawn block has to come to the body before it is reported as a
#: *graze*. The camera rides inside that box at eighty degrees, so a block the
#: arc misses by a hand's width is a block that fills the frame -- and "there
#: are blocks in the way" is a report about the frame, not about a collision
#: the scene does not have. Set to 0.0 to switch the second pass off.
GRAZE = 0.25

#: Styles that are drawn and are not solid. A body passes through them by the
#: renderer's own design -- but a leaf block, a pane of glass and a cobweb are
#: *blocks* to the eye, so they are counted and reported apart rather than
#: ignored.
SEE_THROUGH = pk.SEE_THROUGH

HALF_W = pk.BODY_HALF_W
BODY_H = pk.BODY_H

#: Provenance tags, in the order they are reported. Every one of them is a
#: distinct writer in ``spiralplan``; see :func:`instrument`.
TAGS = ("block", "pedestal", "bridge", "lid", "moat", "shell", "landmark",
        "pour", "pool", "terrain", "cone:slab", "cone:tooth", "cone:buttress",
        "cone:core", "furniture", "prop", "?")


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def _box_overlap(x: float, y: float, z: float, lo, hi,
                 height: float = BODY_H) -> float:
    """Minimum translation distance between the body at ``(x, y, z)`` and a box.

    The body's own box: ``x, z`` half a width either side, ``y`` to ``y +
    1.8``. Returns 0.0 when they do not overlap. The *minimum* of the three
    axis overlaps rather than the diagonal, which is how deep in the thing
    really is -- ``walk_probe`` takes the minimum of the two horizontal axes
    only, so a lid a body's head goes through reads as a metre deep there and
    a few centimetres here, which is the honest number.
    """
    ox = min(x + HALF_W, hi[0]) - max(x - HALF_W, lo[0])
    if ox <= 0.0:
        return 0.0
    oy = min(y + height, hi[1]) - max(y, lo[1])
    if oy <= 0.0:
        return 0.0
    oz = min(z + HALF_W, hi[2]) - max(z - HALF_W, lo[2])
    if oz <= 0.0:
        return 0.0
    return min(ox, oy, oz)


def _cell_overlap(x: float, y: float, z: float, cell,
                  margin: float = 0.0) -> float:
    cx, cy, cz = cell
    return _box_overlap(x, y, z,
                        (cx - 0.5 - margin, cy - margin, cz - 0.5 - margin),
                        (cx + 0.5 + margin, cy + 1.0 + margin,
                         cz + 0.5 + margin))


def _near_cells(x: float, y: float, z: float, margin: float = 0.0):
    """``parkourkit.body_cells``, optionally inflated by ``margin``.

    At ``margin=0`` it is that function exactly, and it has to stay that way:
    the whole value of this probe is that it asks the world the same question
    the generator's own checks ask it.
    """
    if margin <= 0.0:
        yield from pk.body_cells(x, y, z)
        return
    w = HALF_W + margin
    x0, x1 = math.floor(x - w + 0.5), math.floor(x + w + 0.5)
    z0, z1 = math.floor(z - w + 0.5), math.floor(z + w + 0.5)
    for cy in range(math.floor(y - margin + 0.05),
                    math.floor(y + BODY_H + margin - 0.05) + 1):
        for cx in range(int(x0), int(x1) + 1):
            for cz in range(int(z0), int(z1) + 1):
                yield (cx, cy, cz)


def _leg_at(leg: dict, f: float):
    frm, to = leg["frm"], leg["to"]
    x = frm[0] + (to[0] - frm[0]) * f
    z = frm[2] + (to[2] - frm[2]) * f
    if leg["kind"] == "arc":
        t = leg["dur"] * f
        y = frm[1] + leg["vy0"] * t - 0.5 * pk.GRAVITY * t * t
    else:
        y = frm[1] + (to[1] - frm[1]) * f
    return (x, y, z)


def _leg_length(leg: dict) -> float:
    """Real path length, not the chord. An arc is longer than the straight
    line between its ends by most of a metre on a full-impulse hop, and a
    sampler that divides the chord by ``STEP`` is that much coarser than it
    thinks it is."""
    prev = _leg_at(leg, 0.0)
    total = 0.0
    for i in range(1, 33):
        cur = _leg_at(leg, i / 32.0)
        total += math.dist(prev, cur)
        prev = cur
    return total


def walk_path(course, blk: dict, move) -> tuple[list, int]:
    """The **played** path across one landing and off it, sampled by distance.

    Two halves, and the first one is not in any move: the scene lands the body
    at ``land_point``, *runs it across the block* to ``takeoff_point``
    (``spiral.Scene._begin_ground`` / ``_step_ground``, a straight line at
    ``GroundRun``'s speeds) and only then plays the move. Nothing in the
    generator checks that run at more than five points -- ``_commit`` puts
    ``(0, .25, .5, .75, 1)`` of it into ``pathcells``, and ``_attempt``'s
    ``body does not fit leaving`` asks at three -- which on a five-cell ``wide``
    platform is a metre between samples against a body 0.6 across.

    Returns ``([(leg, f, x, y, z), ...], how many of them are the run)``.
    """
    out = []
    a = course.land_point(blk)
    b = course.takeoff_point(blk)
    span = math.dist(a, b)
    n = max(1, int(span / STEP) + 1)
    for i in range(n + 1):
        f = i / n
        out.append((-1, f, a[0] + (b[0] - a[0]) * f,
                    a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f))
    run = len(out)
    for li, leg in enumerate(move.legs):
        n = max(2, int(_leg_length(leg) / STEP) + 1)
        for i in range(n + 1):
            f = i / n
            x, y, z = _leg_at(leg, f)
            out.append((li, f, x, y, z))
    return out, run


# ---------------------------------------------------------------------------
# Which part of the analytic cone said yes
# ---------------------------------------------------------------------------

def cone_part(cone, cell) -> str:
    """``Cone.rock``'s branches, named. Mirrors ``spiralplan.Cone.rock``.

    The cone is analytic, so there is nothing to instrument: the only way to
    say *which* piece of the building a body is inside is to ask its own
    questions again in its own order.
    """
    x, y, z = cell
    r = math.hypot(x, z)
    if r > cone.base_r + cone.flare * (y - cone.base) + 6.0:
        return ""
    u = cone.unwrap(x, z, y)
    i = cone.level_index(u)
    above = cone.level(i + sp.LEVELS_PER_TURN)
    if y >= above.y - sp.FLOOR_T:
        up = u + 2 * math.pi
        if cone.has_floor(up) and r <= cone.floor_range(up)[1]:
            ch = cone.channel_range(up)
            if not (ch and ch[0] <= r <= ch[1] and y >= above.y - 2):
                return "cone:slab"
    if y == above.y - sp.FLOOR_T - 1 and cone.tooth(u):
        up = u + 2 * math.pi
        if cone.has_floor(up):
            r1f = cone.floor_range(up)[1]
            if r1f - 1.6 <= r <= r1f:
                return "cone:tooth"
    if r > cone.rim_at(y) - sp.BUTTRESS_MAX - 2.0 and r >= cone.buttress_r(u, y):
        return "cone:buttress"
    if r <= cone.face_r(x, z, u, y):
        return "cone:core"
    return ""


# ---------------------------------------------------------------------------
# Provenance: who laid the cell
# ---------------------------------------------------------------------------

def instrument(base):
    """A ``Course`` subclass that records who wrote every cell, and when.

    ``spiralplan.Course.write`` is the single choke point for everything solid
    that is not the analytic cone, so a tag stack round its callers is enough
    to name every writer. The callers are wrapped rather than the writes
    themselves because the same two lines in ``write`` serve a moat, a shell,
    an outcrop and a pedestal.

    Two writers are **not** reachable this way and are handled by hand:

    * a landing's own cells never go through ``write`` at all (``_commit``
      does ``solid.update(cells_of(blk))`` directly), so they are tagged from
      ``_commit``'s own ``got`` dict;
    * the analytic cone writes nothing ever -- see :func:`cone_part`.

    Nothing under ``src/`` is touched: this is a subclass, and the probe
    instantiates it instead of ``Course``.
    """

    class Probe(base):
        def __init__(self, rng, cone, hop_rng=None) -> None:
            #: cell -> ``[tag, seq, style]`` for everything the renderer is
            #: ever handed. Kept for the whole run: ``advance`` takes cells out
            #: of the *collision* map but the chunk volume they were written
            #: into is never rewound, so what the viewer sees only grows.
            self.drawn: dict = {}
            #: cell -> ``(seq, block index)`` for the landing blocks, which are
            #: drawn from the live list and genuinely do disappear.
            self.blockcell: dict = {}
            self.seq = 0
            self._tag = ["?"]
            super().__init__(rng, cone, hop_rng)

        # -- the tag stack -------------------------------------------------

        def _push(self, tag: str):
            probe = self

            class _Ctx:
                def __enter__(self):
                    probe._tag.append(tag)

                def __exit__(self, *a):
                    probe._tag.pop()
                    return False
            return _Ctx()

        # -- the choke point -----------------------------------------------

        def write(self, cell, style: str) -> None:
            n = len(self.writes)
            super().write(cell, style)
            if len(self.writes) > n:
                self.seq += 1
                self.drawn[cell] = [self._tag[-1], self.seq, style]

        def carve(self, cell) -> None:
            n = len(self.writes)
            super().carve(cell)
            if len(self.writes) > n:
                self.seq += 1
                self.drawn[cell] = [self._tag[-1], self.seq, "air"]

        # -- the writers ---------------------------------------------------

        def _commit(self, prev: dict, node: dict, got: dict) -> dict:
            with self._push("pedestal"):
                blk = super()._commit(prev, node, got)
            self.seq += 1
            blk["seq"] = self.seq
            blk["index"] = len(self.blockcell)      # only for the dump
            for cell in got.get("ceiling") or ():
                if cell in self.drawn and self.drawn[cell][0] == "pedestal":
                    self.drawn[cell][0] = "lid"
            for cell in got.get("bridge") or ():
                if cell in self.drawn and self.drawn[cell][0] == "pedestal":
                    self.drawn[cell][0] = "bridge"
            for cell in pk.cells_of(blk):
                self.blockcell[cell] = (self.seq, blk)
            return blk

        def _paint(self, section) -> None:
            with self._push("terrain"):
                return super()._paint(section)

        def _landmark(self, section) -> None:
            with self._push("landmark"):
                return super()._landmark(section)

        def _pour(self, section) -> None:
            with self._push("pour"):
                return super()._pour(section)

        def _pool(self, theme, cx, cy, cz) -> None:
            with self._push("pool"):
                return super()._pool(theme, cx, cy, cz)

        def _moat(self, blk, theme, node) -> None:
            with self._push("moat"):
                return super()._moat(blk, theme, node)

        def _shell(self, prev, blk, theme, kind) -> None:
            with self._push("shell"):
                return super()._shell(prev, blk, theme, kind)

    return Probe


# ---------------------------------------------------------------------------
# The world, as the viewer sees it
# ---------------------------------------------------------------------------

class World:
    """What is on screen, and when it got there.

    Three sources, and the union is the picture:

    * the analytic cone (``Cone.rock``), which is always there;
    * everything ``write`` has handed the renderer, which never goes away --
      ``Scene._pump`` copies each write into the chunk volume and only an
      explicit ``carve`` ever clears one;
    * the live landing blocks, which are drawn from ``Course.blocks`` and do
      go away when ``advance`` releases them.
    """

    def __init__(self, course) -> None:
        self.course = course
        self.cone = course.cone

    def hits(self, x: float, y: float, z: float, upto: int | None,
             live_blocks: set | None, margin: float = 0.0):
        """Every drawn cell the body at ``(x, y, z)`` is inside.

        ``upto`` is a write sequence: ``None`` means the end of the run, an
        integer means the world as it stood when that many cells had been
        written. ``live_blocks`` is the set of landing-block cells that are
        still on the course at that moment. ``margin`` inflates the body box,
        which is how a *graze* is asked for: a block the arc misses by five
        centimetres is a block that fills the lens on a scene whose camera
        rides inside that box.
        """
        for cell in _near_cells(x, y, z, margin):
            got = self.at(cell, upto, live_blocks)
            if got is None:
                continue
            d = _cell_overlap(x, y, z, cell, margin)
            if d <= 1e-9:
                continue
            yield (cell,) + got + (d,)

    def at(self, cell, upto: int | None, live_blocks: set | None):
        """``(tag, seq, style)`` for one cell, or ``None`` if it is air."""
        rec = self.course.drawn.get(cell)
        if rec is not None and (upto is None or rec[1] <= upto):
            if rec[2] == "air":
                return None
            return rec[0], rec[1], rec[2]
        blk = self.course.blockcell.get(cell)
        if blk is not None and (upto is None or blk[0] <= upto) \
                and (live_blocks is None or cell in live_blocks):
            return "block", blk[0], blk[1]["style"]
        if cell in self.course.softcells:
            # A ladder, a vine, a water column or a cobweb belonging to some
            # *other* landing. ``_place_soft`` never goes through ``write``,
            # so these are in no stream the probe could see and in no
            # occupancy map either -- drawn, and passed through.
            return "soft", 0, "soft"
        part = cone_part(self.cone, cell)
        if part:
            return part, 0, part
        return None


# ---------------------------------------------------------------------------
# One move
# ---------------------------------------------------------------------------

def _wide_own(blk: dict) -> set:
    """``walk_probe``'s exemption: the whole landing, its stack and its soft
    cells. Printed so the two numbers can be compared, never used alone."""
    out = set(pk.footprint(blk["x"], blk["y"], blk["z"], blk["form"])
              or ((blk["x"], blk["y"], blk["z"]),))
    out |= set(blk.get("pedestal", ()))
    out |= set(blk.get("footing", ()))
    out |= set(blk.get("ceiling", ()))
    for s in blk.get("soft", ()):
        out.add((blk["x"] + s["dx"], blk["y"] + s["dy"], blk["z"] + s["dz"]))
    return out


def _strict_own(prev: dict, nxt: dict) -> tuple[set, set]:
    """The generator's *own* three exemptions, and nothing else.

    ``spiralplan.Course._attempt`` clears an arc against
    ``standing_cells(prev) | standing_cells(landing) | soft``, plus the block
    being left for the first third of the path. Those are the only cells the
    course has ever promised itself it may pass through: the landing being
    left, the landing arrived on, and a slab -- whose walking surface is
    halfway up its own cell, so the feet are inside it by construction.
    """
    own = pk.standing_cells(prev) | pk.standing_cells(nxt)
    for s in nxt.get("soft", ()):
        own.add((nxt["x"] + s["dx"], nxt["y"] + s["dy"], nxt["z"] + s["dz"]))
    for s in prev.get("soft", ()):
        own.add((prev["x"] + s["dx"], prev["y"] + s["dy"], prev["z"] + s["dz"]))
    leaving = set(pk.footprint(prev["x"], prev["y"], prev["z"], prev["form"])
                  or ((prev["x"], prev["y"], prev["z"]),))
    return own, leaving


def furniture_hits(blk: dict, x: float, y: float, z: float,
                   height: float = BODY_H):
    """Decoration boxes the body is inside.

    ``deco`` entries are drawn as boxes (``spiral.Scene._draw_furniture``) and
    carry ``solid: False``, so they are in **no** cell set anywhere: not
    ``solid``, not ``struct``, not ``pathcells``. Nothing in the project has
    ever asked whether the body runs through one, and a ``lamp`` sits at the
    centre of the landing it decorates, 0.62 across, from one block over the
    block's floor -- which is the height of the feet running across it.
    """
    for d in blk["deco"]:
        cx = blk["x"] + d["dx"]
        cy = blk["y"] + d["dy"] + d["sy"] * 0.5
        cz = blk["z"] + d["dz"]
        lo = (cx - d["sx"] / 2, cy - d["sy"] / 2, cz - d["sz"] / 2)
        hi = (cx + d["sx"] / 2, cy + d["sy"] / 2, cz + d["sz"] / 2)
        depth = _box_overlap(x, y, z, lo, hi, height)
        if depth > 1e-9:
            yield d["style"], depth


def check_move(world: World, prev: dict, nxt: dict, upto, live_blocks,
               props: dict, want_path: bool = False) -> dict:
    """Walk one played stretch -- the run across ``prev``, then its move."""
    move = prev.get("move")
    own, leaving = _strict_own(prev, nxt)
    wide = _wide_own(prev) | _wide_own(nxt)
    samples, run = walk_path(world.course, prev, move)
    # The block being left is exempt for the first third of the *arc*, which
    # is the generator's own rule (``_path_clear``'s ``leaving``) -- and for
    # the whole of the run across it, which is the body standing on it.
    early = run + (len(samples) - run) // 3
    solved = nxt.get("seq", 0)

    hits: dict = {}                 # cell -> [tag, seq, style, depth, at, i]
    soft: dict = {}
    furn: dict = {}
    props_hit: dict = {}
    graze: dict = {}
    eye: dict = {}
    eye_furn: dict = {}
    path = [] if want_path else None
    for i, (li, f, x, y, z) in enumerate(samples):
        if path is not None:
            path.append((li, x, y, z))
        if GRAZE > 0.0:
            # Only what is *level with or above the feet*. A cell below them
            # is the floor -- the terrace being flown over, the block being
            # landed on -- and counting it makes every move in the tower a
            # graze, which is a probe measuring the ground.
            under = math.floor(y + 0.05)
            for cell, tag, seq, style, depth in world.hits(
                    x, y, z, upto, live_blocks, GRAZE):
                if cell[1] < under or cell in own or cell in wide:
                    continue
                if i <= early and cell in leaving:
                    continue
                if style in SEE_THROUGH:
                    continue
                rec = graze.get(cell)
                if rec is None or depth > rec[3]:
                    graze[cell] = [tag, seq, style, depth, (x, y, z),
                                   i, False, False, True]
        for cell, tag, seq, style, depth in world.hits(x, y, z, upto,
                                                       live_blocks):
            if cell in own:
                continue
            if i <= early and cell in leaving:
                continue
            bag = soft if (style in SEE_THROUGH) else hits
            # **Underfoot is not "in the way".** A walk that steps down onto a
            # slab has its feet half a block inside the cell holding them up
            # -- the surface is halfway up its own cell -- and the walk's own
            # bridge is exactly that cell. Flagged rather than dropped: this
            # is the one exemption class ``walk_probe``'s wide ``own`` set is
            # right about, and a probe that silently swallowed it would be the
            # thing this file exists to complain about.
            floorish = (cell[1] <= math.floor(y + 0.05)
                        and cell[1] + 1.0 - y <= 0.51)
            rec = bag.get(cell)
            if rec is None or depth > rec[3]:
                # **Is it in the occupancy map right now?** ``advance``
                # discards a landing's block, pedestal, footing and lid cells
                # from ``solid`` when it falls off the back of the course --
                # and the renderer never takes anything back out of its chunk
                # volume, because ``Scene._pump`` only ever *adds*. So a cell
                # can be on screen and not in the world the generator checks
                # against, which is a jump flying through masonry that is
                # visibly there and provably absent.
                bag[cell] = [tag, seq, style, depth, (x, y, z), i,
                             cell in wide, floorish,
                             world.course.blocked(cell)]
        # **The eye, which is what the viewer actually is.** These scenes are
        # first person (``parkourkit.EYE = 1.62`` over the feet), so "there
        # are blocks in the way" is a report about one *point*, not about the
        # body box -- and a cell the camera is inside fills the whole frame.
        ey = y + pk.EYE
        ecell = (math.floor(x + 0.5), math.floor(ey), math.floor(z + 0.5))
        got = world.at(ecell, upto, live_blocks)
        if got is not None and got[2] not in SEE_THROUGH \
                and ecell not in own and not (i <= early
                                              and ecell in leaving):
            eye.setdefault(ecell, [got[0], got[1], got[2], 0.0, (x, ey, z), i,
                                   ecell in wide, False, True])
        for blk in (prev, nxt):
            for style, d2 in furniture_hits(blk, x, ey - 0.0001, z,
                                            height=0.0002):
                eye_furn[(id(blk), style)] = style
            for style, depth in furniture_hits(blk, x, y, z):
                key = (id(blk), style)
                if depth > furn.get(key, (0.0,))[0]:
                    furn[key] = (depth, style)
        for cell in pk.body_cells(x, y, z):
            kind = props.get(cell)
            if kind is not None:
                props_hit[cell] = kind
    return {
        "move": move, "prev": prev, "nxt": nxt, "hits": hits, "soft": soft,
        "furniture": furn, "props": props_hit, "solved": solved,
        "samples": samples, "path": path, "run": run, "graze": graze,
        "eye": eye, "eye_furn": eye_furn,
    }


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------

def grow(plan, run: int, blocks: int):
    """Exactly ``tools/tower_probe.py:grow``, with the instrumented Course.

    The move for landing ``i`` is checked at the moment landing ``i`` becomes
    the oldest one still live, which is where the body is: generation has run
    its full ``ahead`` past it, so everything that was going to be built
    around that path has been, and ``advance`` has not yet released the block
    itself. ``<=``, not ``<`` -- the strictly-less form checks every move one
    step after its own ground has been taken away, which reads as a
    catastrophic air-walk and is the probe's own doing.
    """
    cone = plan.Cone(random.Random(run * 977 + 13), 0)
    course = instrument(plan.Course)(random.Random(run * 6151 + 29), cone)
    world = World(course)
    seen = list(course.blocks)
    checked: list[dict] = []
    nxt = 0
    for _ in range(blocks):
        seen.append(course.spawn())
        if len(course.blocks) > course.ahead:
            course.advance(len(course.blocks) - course.ahead + sp.TRAIL)
        first_live = len(seen) - len(course.blocks)
        while nxt <= first_live and nxt + 1 < len(seen):
            a, b = seen[nxt], seen[nxt + 1]
            nxt += 1
            if a.get("move") is None:
                continue
            got = check_move(world, a, b, course.seq, course.solid,
                             _props(cone))
            got["index"] = nxt - 1
            checked.append(got)
    return cone, course, seen, checked


def _props(cone) -> dict:
    return {at: kind for at, kind, _ in cone.props}


def _worst(rec: dict) -> float:
    best = 0.0
    for v in rec["hits"].values():
        best = max(best, v[3])
    return best


def sweep(plan, runs: int, blocks: int) -> dict:
    out = {
        "runs": runs, "blocks": blocks, "moves": 0,
        "strict": 0, "wide": 0, "solid": 0, "seethrough": 0,
        "furniture": 0, "props": 0, "late": 0, "late_only": 0,
        "worst": 0.0, "worst_what": "", "worst_at": None,
        "by_tag": defaultdict(lambda: [0, 0, 0.0]),     # moves, cells, worst
        "by_style": Counter(), "by_kind": Counter(), "by_level": Counter(),
        "by_beat": Counter(), "by_author": Counter(), "by_leg": Counter(),
        "kinds": Counter(), "before": 0, "after": 0, "cone_hits": 0,
        "furn_style": Counter(), "prop_kind": Counter(),
        "soft_style": Counter(), "soft_worst": 0.0, "furn_worst": 0.0,
        "underfoot": 0, "ghost": 0, "ghost_tag": Counter(),
        "eye": 0, "eye_tag": Counter(), "eye_furn": 0,
        "eye_furn_style": Counter(),
        "grazed": 0, "graze_tag": Counter(), "graze_kind": Counter(),
        "graze_beat": Counter(), "graze_level": Counter(),
        "depths": [], "offenders": [],
    }
    for run in range(runs):
        cone, course, _seen, checked = grow(plan, run, blocks)
        world = World(course)
        props = _props(cone)
        live_all: set = set()                # see the note at the late check
        for rec in checked:
            out["moves"] += 1
            move = rec["move"]
            out["kinds"][move.kind] += 1
            strict = {c: v for c, v in rec["hits"].items() if not v[7]}
            under = {c: v for c, v in rec["hits"].items() if v[7]}
            if under:
                out["underfoot"] += 1
            if strict:
                out["strict"] += 1
                wide = {c: v for c, v in strict.items() if not v[6]}
                if wide:
                    out["wide"] += 1
                if any(v[8] for v in strict.values()):
                    out["solid"] += 1
                if any(not v[8] for v in strict.values()):
                    out["ghost"] += 1
                    for v in strict.values():
                        if not v[8]:
                            out["ghost_tag"][v[0]] += 1
                worst = max(v[3] for v in strict.values())
                out["depths"].append(worst)
                name = _name(cone, rec["prev"])
                if worst > out["worst"]:
                    out["worst"] = worst
                    deep = max(strict.items(), key=lambda kv: kv[1][3])
                    out["worst_what"] = (f"{deep[1][2]} laid by {deep[1][0]} "
                                         f"on a {move.kind} in {name}")
                    out["worst_at"] = (run, rec["index"])
                seg = rec["prev"]["segment"]
                author = _author(cone, rec["prev"])
                for cell, v in strict.items():
                    tag, seq, style, depth, _at, si0 = v[:6]
                    slot = out["by_tag"][tag]
                    slot[1] += 1
                    slot[2] = max(slot[2], depth)
                    out["by_style"][style] += 1
                    if tag.startswith("cone:"):
                        out["cone_hits"] += 1
                    if seq and seq < rec["solved"]:
                        out["before"] += 1
                    elif seq:
                        out["after"] += 1
                    si = v[5]
                    leg = rec["samples"][si][0] if si < len(rec["samples"]) \
                        else 0
                    where = "run across" if leg < 0 else f"leg {leg}"
                    out["by_leg"][f"{move.kind}: {where}"] += 1
                for tag in {v[0] for v in strict.values()}:
                    out["by_tag"][tag][0] += 1
                out["by_kind"][move.kind] += 1
                out["by_level"][name] += 1
                out["by_beat"][seg] += 1
                out["by_author"][author] += 1
                out["offenders"].append((worst, run, rec["index"], name, seg,
                                         move.kind,
                                         max(strict.items(),
                                             key=lambda kv: kv[1][3])))
            if rec["eye"]:
                out["eye"] += 1
                for v in rec["eye"].values():
                    out["eye_tag"][v[0]] += 1
            if rec["eye_furn"]:
                out["eye_furn"] += 1
                for style in rec["eye_furn"].values():
                    out["eye_furn_style"][style] += 1
            near = {c: v for c, v in rec["graze"].items()
                    if c not in rec["hits"]}
            if near:
                out["grazed"] += 1
                for v in near.values():
                    out["graze_tag"][v[0]] += 1
                out["graze_kind"][move.kind] += 1
                out["graze_beat"][rec["prev"]["segment"]] += 1
                out["graze_level"][_name(cone, rec["prev"])] += 1
            if rec["soft"]:
                out["seethrough"] += 1
                for v in rec["soft"].values():
                    out["soft_style"][v[2]] += 1
                    out["soft_worst"] = max(out["soft_worst"], v[3])
            if rec["furniture"]:
                out["furniture"] += 1
                for depth, style in rec["furniture"].values():
                    out["furn_style"][style] += 1
                    out["furn_worst"] = max(out["furn_worst"], depth)
            if rec["props"]:
                out["props"] += 1
                for kind in rec["props"].values():
                    out["prop_kind"][kind] += 1
            # ...and the same move against the world as it stands at the very
            # end of the run. Dressing that lands late is exactly the class of
            # bug suspected here, and the live check cannot see it: a section
            # is painted when the *generator* leaves it, which on a level
            # longer than ``ahead`` is after the body is already inside it.
            # ``live_blocks=set()`` on purpose: the landing blocks themselves
            # are drawn from the live list and genuinely do disappear, so
            # counting a dead one would be the probe inventing an obstacle.
            # What is left is exactly the persistent terrain -- everything
            # ``write`` handed the renderer, which is never taken back.
            late = check_move(world, rec["prev"], rec["nxt"], None, live_all,
                              props)
            late_hits = {c: v for c, v in late["hits"].items() if not v[7]}
            if late_hits:
                out["late"] += 1
                if not strict:
                    out["late_only"] += 1
    return out


def _name(cone, blk: dict) -> str:
    return blk.get("theme") or "?"


def _author(cone, blk: dict) -> str:
    idx = blk.get("author", -1)
    if idx is None or idx < 0:
        return "(none)"
    design = getattr(cone, "design", None)
    if design is None:
        return f"section {idx}"
    return design(idx).name


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _pc(n: int, d: int) -> str:
    return f"{100.0 * n / max(1, d):5.2f}%"


def report(o: dict, plan_name: str) -> str:
    m = o["moves"]
    depths = sorted(o["depths"])
    med = depths[len(depths) // 2] if depths else 0.0
    lines = [
        f"ARC PROBE -- plan {plan_name}, {o['runs']} runs x {o['blocks']} "
        f"landings, sampled every {STEP:.2f} m of path",
        f"  moves walked                                {m}",
        "  move mix                                    "
        + ", ".join(f"{k} {v}" for k, v in o["kinds"].most_common(8)),
        "",
        "  THE BODY PASSES THROUGH SOMETHING DRAWN",
        f"    moves, generator's own exemptions         {o['strict']:6d}"
        f"  ({_pc(o['strict'], m)})",
        f"    moves, walk_probe's wider exemptions      {o['wide']:6d}"
        f"  ({_pc(o['wide'], m)})   <- the number walk_probe reports",
        f"    ...through a cell blocked() calls solid   {o['solid']:6d}"
        f"  ({_pc(o['solid'], m)})",
        f"    ...through a cell it does NOT              {o['ghost']:6d}"
        f"  ({_pc(o['ghost'], m)})   drawn, released by advance, never"
        f" un-drawn",
        "        those, by writer                      "
        + (", ".join(f"{k} {v}" for k, v in o["ghost_tag"].most_common(8))
           or "none"),
        f"    worst penetration                         {o['worst']:.3f} m"
        f"  ({o['worst_what'] or 'none'})",
        f"    median offending move's worst             {med:.3f} m",
        f"    (excluded: feet inside the ground under them"
        f" {o['underfoot']:5d}  ({_pc(o['underfoot'], m)}) -- a slab's surface"
        f" is halfway up its own cell)",
        "",
        "  THE CAMERA ITSELF  (first person: the eye is 1.62 m over the feet)",
        f"    moves with the eye inside a drawn cell     {o['eye']:6d}"
        f"  ({_pc(o['eye'], m)})",
        "        by writer                             "
        + (", ".join(f"{k} {v}" for k, v in o["eye_tag"].most_common(8))
           or "none"),
        f"    moves with the eye inside furniture       {o['eye_furn']:6d}"
        f"  ({_pc(o['eye_furn'], m)})",
        "        by material                           "
        + (", ".join(f"{k} {v}"
                     for k, v in o["eye_furn_style"].most_common(8)) or "none"),
        "",
        "  ...AND THROUGH THINGS NOTHING HAS EVER COUNTED",
        f"    see-through blocks (leaves, glass, web)   {o['seethrough']:6d}"
        f"  ({_pc(o['seethrough'], m)})   worst {o['soft_worst']:.3f} m",
        f"    furniture on a landing (deco boxes)       {o['furniture']:6d}"
        f"  ({_pc(o['furniture'], m)})   worst {o['furn_worst']:.3f} m",
        f"    props                                     {o['props']:6d}"
        f"  ({_pc(o['props'], m)})",
        f"    grazes: solid within {GRAZE:.2f} m of the body {o['grazed']:6d}"
        f"  ({_pc(o['grazed'], m)})",
        "",
        "  THE SAME MOVES AGAINST THE FINISHED WORLD",
        f"    moves through solid at the end of the run {o['late']:6d}"
        f"  ({_pc(o['late'], m)})",
        f"    ...that were clear when the body was there{o['late_only']:6d}"
        f"  ({_pc(o['late_only'], m)})",
        "",
        "  WHO LAID THE OFFENDING CELL",
        f"    {'tag':<16}{'moves':>7}{'cells':>8}{'worst':>9}",
    ]
    for tag in TAGS:
        slot = o["by_tag"].get(tag)
        if not slot or not slot[1]:
            continue
        lines.append(f"    {tag:<16}{slot[0]:>7}{slot[1]:>8}"
                     f"{slot[2]:>8.3f}m")
    for tag, slot in sorted(o["by_tag"].items()):
        if tag not in TAGS and slot[1]:
            lines.append(f"    {tag:<16}{slot[0]:>7}{slot[1]:>8}"
                         f"{slot[2]:>8.3f}m")
    tot = o["before"] + o["after"]
    lines += [
        "",
        "  WAS IT THERE BEFORE THE ARC WAS SOLVED?",
        f"    laid before the arc was solved            {o['before']:6d}"
        f"  ({_pc(o['before'], tot)})",
        f"    laid after                                {o['after']:6d}"
        f"  ({_pc(o['after'], tot)})",
        f"    the analytic cone (no sequence)           {o['cone_hits']:6d}",
        "",
        "  BY MATERIAL      "
        + ", ".join(f"{k} {v}" for k, v in o["by_style"].most_common(10)),
        "  BY MOVE KIND     "
        + ", ".join(f"{k} {v}" for k, v in o["by_kind"].most_common(10)),
        "  BY LEG           "
        + ", ".join(f"{k} {v}" for k, v in o["by_leg"].most_common(8)),
        "  BY BEAT          "
        + ", ".join(f"{k} {v}" for k, v in o["by_beat"].most_common(10)),
        "  BY LEVEL (where) "
        + ", ".join(f"{k} {v}" for k, v in o["by_level"].most_common(8)),
        "  BY AUTHOR (whose)"
        + ", ".join(f"{k} {v}" for k, v in o["by_author"].most_common(8)),
    ]
    if o["soft_style"]:
        lines.append("  SEE-THROUGH      "
                     + ", ".join(f"{k} {v}"
                                 for k, v in o["soft_style"].most_common(8)))
    if o["furn_style"]:
        lines.append("  FURNITURE        "
                     + ", ".join(f"{k} {v}"
                                 for k, v in o["furn_style"].most_common(8)))
    if o["prop_kind"]:
        lines.append("  PROPS            "
                     + ", ".join(f"{k} {v}"
                                 for k, v in o["prop_kind"].most_common(8)))
    if o["graze_tag"]:
        lines += [
            "",
            f"  WHAT THE BODY ALMOST TOUCHES (within {GRAZE:.2f} m, "
            "never inside)",
            "    by writer      "
            + ", ".join(f"{k} {v}" for k, v in o["graze_tag"].most_common(10)),
            "    by move kind   "
            + ", ".join(f"{k} {v}" for k, v in o["graze_kind"].most_common(8)),
            "    by beat        "
            + ", ".join(f"{k} {v}" for k, v in o["graze_beat"].most_common(8)),
            "    by level       "
            + ", ".join(f"{k} {v}"
                        for k, v in o["graze_level"].most_common(8)),
        ]
    worst = sorted(o["offenders"], reverse=True, key=lambda t: t[0])[:12]
    if worst:
        lines += ["", "  THE WORST TWELVE  (--dump run,index for one in full)"]
        for depth, run, idx, name, seg, kind, deep in worst:
            cell, v = deep
            lines.append(f"    {depth:5.2f} m  --dump {run},{idx:<4d} "
                         f"{kind:<7} {name:<16} {seg:<10} "
                         f"{v[2]} laid by {v[0]} at {cell}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# One offender in full
# ---------------------------------------------------------------------------

def dump(plan, run: int, index: int, blocks: int) -> None:
    cone, course, _seen, checked = grow(plan, run, blocks)
    world = World(course)
    rec = next((r for r in checked if r["index"] == index), None)
    if rec is None:
        print(f"no move at index {index} in run {run} "
              f"({len(checked)} moves checked)")
        return
    prev, nxt, move = rec["prev"], rec["nxt"], rec["move"]
    print(f"RUN {run}  MOVE {index}   {move.kind}  "
          f"{move.dur:.2f} s  {math.dist((move.frm[0], move.frm[2]), (move.to[0], move.to[2])):.2f} m "
          f"horizontally, {move.to[1] - move.frm[1]:+.2f} m vertically")
    for who, blk in (("take-off", prev), ("landing ", nxt)):
        print(f"  {who}  cell ({blk['x']},{blk['y']},{blk['z']})  "
              f"{blk['style']}/{blk['form']}  level {blk['theme']}  "
              f"beat {blk['segment']}  origin {blk.get('origin')}  "
              f"author {_author(cone, blk)}  lift {blk.get('lift')}")
        if blk.get("pedestal"):
            print(f"            pedestal {blk['pedestal']}")
        if blk.get("ceiling"):
            print(f"            lid      {blk['ceiling']}")
        if blk.get("deco"):
            print("            deco     "
                  + ", ".join(d["style"] for d in blk["deco"]))
    own, leaving = _strict_own(prev, nxt)
    print(f"  exempt (generator's own): {sorted(own) or 'none'}")
    print(f"  exempt for the first third (block being left): {sorted(leaving)}")
    print(f"  the arc was solved at write sequence {rec['solved']}")
    print("\n  SAMPLES  (every "
          f"{STEP:.2f} m of path; the generator checks {pk.ARC_SAMPLES + 1} "
          "points spread evenly in TIME over the whole move)")
    bad_at = {v[5] for v in rec["hits"].values()}
    for i, (li, f, x, y, z) in enumerate(rec["samples"]):
        flag = "  <<<" if i in bad_at else ""
        name = "run" if li < 0 else f"leg{li}"
        print(f"    {i:3d} {name:<5} f={f:4.2f}  "
              f"({x:8.3f},{y:8.3f},{z:8.3f}){flag}")
    print("\n  SOLID CELLS THE BODY IS INSIDE")
    if not rec["hits"]:
        print("    none")
    for cell, v in sorted(rec["hits"].items(), key=lambda kv: -kv[1][3]):
        tag, seq, style, _at, i, wide, floorish, hard = (
            v[0], v[1], v[2], v[4], v[5], v[6], v[7], v[8])
        depth = v[3]
        when = ("before" if seq and seq < rec["solved"] else
                "AFTER" if seq else "analytic")
        print(f"    {cell}  {style:<14} laid by {tag:<10} "
              f"seq {seq:<6} ({when} the arc)  depth {depth:.3f} m  "
              f"at sample {i}"
              + ("   [walk_probe exempts this]" if wide else "")
              + ("   [underfoot: the ground, not an obstacle]"
                 if floorish else "")
              + ("" if hard else
                 "   [DRAWN ONLY: blocked() says air here]"))
    if rec["soft"]:
        print("\n  SEE-THROUGH CELLS THE BODY IS INSIDE (drawn, never solid)")
        for cell, v in sorted(rec["soft"].items(), key=lambda kv: -kv[1][3]):
            print(f"    {cell}  {v[2]:<14} laid by {v[0]:<10} "
                  f"depth {v[3]:.3f} m")
    if rec["furniture"]:
        print("\n  FURNITURE THE BODY RUNS THROUGH")
        for depth, style in rec["furniture"].values():
            print(f"    {style:<14} depth {depth:.3f} m")
    if rec["props"]:
        print("\n  PROPS THE BODY RUNS THROUGH")
        for cell, kind in rec["props"].items():
            print(f"    {cell}  {kind}")
    # ``set()``, as the sweep's late pass does: a landing block is drawn from
    # the live list and genuinely disappears, so counting a dead one here
    # would be the probe inventing an obstacle. Persistent terrain only.
    late = check_move(world, prev, nxt, None, set(), _props(cone))
    extra = {c: v for c, v in late["hits"].items() if c not in rec["hits"]}
    if extra:
        print("\n  ...AND THESE ARRIVED AFTER THE BODY HAD GONE PAST")
        for cell, v in sorted(extra.items(), key=lambda kv: -kv[1][3]):
            print(f"    {cell}  {v[2]:<14} laid by {v[0]:<10} "
                  f"seq {v[1]}  depth {v[3]:.3f} m")


# ---------------------------------------------------------------------------
# The whole course as a table
# ---------------------------------------------------------------------------

def path_table(plan, run: int, blocks: int) -> None:
    cone, course, seen, _checked = grow(plan, run, blocks)
    print(f"THE PATH -- plan {plan.__name__.rsplit('.', 1)[-1]}, run {run}, "
          f"{len(seen)} landings")
    print("  idx  level              lv  author            beat       orig  "
          "  terr   surf  lift   cell                    material/form  "
          "move     dist   rise    t")
    t = 0.0
    levels: list[int] = []
    climbed = 0.0
    prev_surface = None
    five = None
    for i, blk in enumerate(seen):
        u = course.u_of(blk)
        li = cone.level_index(u)
        lv = cone.level(li)
        surface = course.surface(blk)
        lift = surface - lv.y
        move = seen[i - 1].get("move") if i else None
        if move is not None:
            dist = math.dist((move.frm[0], move.frm[2]),
                             (move.to[0], move.to[2]))
            rise = move.to[1] - move.frm[1]
            t += move.dur
            kind = move.kind
        else:
            dist = rise = 0.0
            kind = "-"
        if prev_surface is not None and surface > prev_surface:
            climbed += surface - prev_surface
        prev_surface = surface
        if not levels or levels[-1] != li:
            levels.append(li)
        if five is None and t >= 300.0:
            five = (i, blk, t)
        print(f"  {i:4d}  {blk['theme'][:17]:<17} {li:3d}  "
              f"{_author(cone, blk)[:16]:<16}  {blk['segment'][:10]:<10} "
              f"{str(blk.get('origin') or '-')[:6]:<6} "
              f"{lv.y:5d} {surface:6.1f} {lift:5.1f}   "
              f"({blk['x']:4d},{blk['y']:4d},{blk['z']:4d})   "
              f"{blk['style'][:12]:<12}/{blk['form']:<5}  "
              f"{kind:<7} {dist:5.2f} {rise:+5.1f} {t:7.2f}")
    print()
    print(f"  landings                 {len(seen)}")
    print(f"  levels traversed         {len(levels)}  "
          f"({', '.join(cone.level(i).theme.name for i in levels[:12])}"
          f"{' ...' if len(levels) > 12 else ''})")
    print(f"  blocks climbed           {climbed:.0f}  "
          f"({course.surface(seen[-1]) - course.surface(seen[0]):+.0f} net)")
    print(f"  simulated seconds        {t:.1f}")
    if five is not None:
        i, blk, tt = five
        print(f"  after 5 minutes          landing {i} of {len(seen)}, "
              f"{blk['theme']}, {tt:.1f} s")
    else:
        print(f"  after 5 minutes          the run is only {t:.1f} s long "
              f"-- {300.0 / max(1e-9, t) * len(seen):.0f} landings would be "
              f"needed")


# ---------------------------------------------------------------------------

def main() -> int:
    global STEP
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--blocks", type=int, default=300)
    ap.add_argument("--plan", choices=("tower", "spiral"), default="tower")
    ap.add_argument("--step", type=float, default=STEP,
                    help="metres of path between samples (0.15 or finer)")
    ap.add_argument("--dump", default="",
                    help="run,index -- print one move in full")
    ap.add_argument("--path", action="store_true",
                    help="print the whole course as a walkable table")
    ap.add_argument("--run", type=int, default=0,
                    help="which run --path walks (the seed is run*6151+29)")
    args = ap.parse_args()
    STEP = args.step
    plan = hp if args.plan == "tower" else sp

    if args.dump:
        run, index = (int(v) for v in args.dump.split(","))
        dump(plan, run, index, args.blocks)
        return 0
    if args.path:
        path_table(plan, args.run, args.blocks)
        return 0
    print(report(sweep(plan, args.runs, args.blocks), args.plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
