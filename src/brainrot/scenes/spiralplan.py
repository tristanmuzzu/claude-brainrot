"""The spiral proper: themed *platforms* winding up, and the parkour between.

**Unfinished, and deliberately not wired into any scene.** The geometry works
-- platforms, columns, caves, entry and exit lanes, nine bridge styles -- but
placement still falls through to the unchecked answer on about one node in
eight, against one in three hundred for the ring version in ``towerplan``. It
is committed rather than kept in a scratch directory because the three causes
already found and fixed are the expensive part, and they are recorded in the
comments where they were fixed:

* the columns of the platform one revolution *above* hang straight through the
  bridge below (:meth:`Spiral._clear_of_bridges`);
* a bridge aimed at its landing spends its last stones inside the platform it
  is aiming at, whose cells are that platform's own ground (``_out``/``aim``);
* a 2.8 m step rounded onto the lattice can land 1.4 m out, under ``MIN_HOP``,
  and the next stone is then measured from a body that never moved.

What is left is the fourth: a bridge that arrives under a platform without
having climbed enough cannot make the last blocks, because there is no room
left to climb in and the stones pile up on each other. The half-written answer
is a flight of steps *beside* the rim rather than under it.


This replaces the first tower's architecture, and the difference is the whole
point of the format rather than a detail of it.

The first version was a cylinder with jump blocks hung outside it: a course of
floating cubes that happened to go round something. What the reference maps
actually are -- and what a screenshot of one taken from underneath makes
obvious -- is a **stack of built places**. A farm with crops and fences. A
nether cave with lava and lanterns. A rainbow floor. A honey ledge. Each is a
small piece of *world*, a dozen blocks across, standing on a forest of stone
columns that runs down out of the shot; they spiral round an axis, each a
little higher and a little further round than the last, and the parkour is two
different things stitched together:

* **crossing a platform** -- running over real ground, past its own scenery,
  ducking under a beam, over a fence, across an ice patch;
* **the bridge between two platforms** -- the classic floating-block parkour,
  out over the drop, which is where the set-piece vocabulary lives.

Making the platforms first-class changes the generator's shape as well as its
look. The old one *rolled* for a set-piece and then argued with placement about
where it would fit. This one is **scheduled**: the spiral decides where the
platforms are, each platform decides where you come in and where you go out,
and the course is the sequence "cross, bridge, cross, bridge". Nothing has to
search for a doorway, because every platform states its own; nothing can circle
a room for two hundred blocks, because there is nowhere to circle.

The physics, the lattice, the move vocabulary and every occupancy rule are
:mod:`brainrot.scenes.towerplan`'s, unchanged -- that half was never about the
shape of the building.
"""

from __future__ import annotations

import math

from .towerplan import (  # noqa: F401  (re-exported for the scene and probes)
    AIR_MIN, AIR_MAX, AIR_SPEED, BODY_H, BODY_HALF_W, BUBBLE_SPEED, CANDY,
    CHEST, CLIMB_SPEED, EYE, FORMS, GRAVITY, HEADROOM, ICE_AIR, ICE_RUN,
    JUMP_V, MATERIALS, MIN_HOP, Move, RUN_SPEED, SEE_THROUGH, SOUL_SPEED,
    SPREAD, SURFACE_SPEED, VY_MAX, VY_MIN, WALK_SPEED, WEB_SPEED, Theme,
    arc_leg, body_cells, bounce_launch, fall_speed, fit_gap, hop_move,
    hop_span, land_point, line_leg, quantise, takeoff_point, _deco, _floor,
    _footprint, _line_cells, _round, _standing_cells, _wrap,
)

# ---------------------------------------------------------------------------
# The shape of the spiral
# ---------------------------------------------------------------------------

#: Platforms in one revolution, and how far out from the axis they stand.
#:
#: Five and twenty-two put consecutive platforms about twenty-six metres apart
#: -- eight or nine hops of bridge, which is long enough to be a real stretch
#: of parkour and short enough that the next place to stand is always visible
#: from the one you are on. Fewer and larger reads as a staircase of islands;
#: more and smaller reads as the cylinder this replaced.
PADS_PER_TURN = 5
SPIRAL_R = 22.0
#: Half-width of a platform, in cells, and the range it may vary over. Eleven
#: to fifteen across: big enough to hold a farm, a cave or a rainbow floor and
#: still be crossed in a few seconds.
PAD_HALF = (5, 7)
#: What each platform climbs over the last. Five per revolution at seven a
#: platform is thirty-five blocks a turn, which at this pace is about a minute
#: -- so a viewer sees a revolution's worth of *themes* without ever needing to
#: see a revolution.
PAD_RISE = (5, 9)
#: How far the columns under a platform run down before they are simply not
#: built. They are the whole silhouette of the thing from outside, and they are
#: also the cheapest geometry in the scene: one style, no faces where they
#: touch.
COLUMN_DEPTH = 30
#: How far the columns lean in as they descend, per block. This is where the
#: cone comes from -- the reference screenshot's whole shape is columns that
#: converge, not platforms that shrink.
COLUMN_LEAN = 0.006
#: Height of the walls and the ceiling on an enclosed platform -- a cave.
ROOF_H = 5
#: How far the course is generated and kept, in platforms.
PADS_AHEAD = 3
#: How wide a corridor the bridges are given, and columns are kept out of.
BRIDGE_CLEAR = 4.0
#: Blocks laid before a run is at full difficulty.
RAMP_BLOCKS = 80
AHEAD = 16
TRAIL = 3


class Pad:
    """One themed platform: where it is, what it is made of, and the way
    through it.

    ``enter`` and ``leave`` are cells on opposite rims, chosen from the
    directions of the neighbouring platforms, and ``lane`` is the straight run
    of cells between them. Nothing is decorated within a cell of that lane, so
    the way across is clear by construction rather than by the generator
    negotiating with its own scenery.
    """

    __slots__ = ("index", "theme", "angle", "cx", "cz", "y", "half",
                 "enclosed", "enter", "leave", "lane", "features")

    def __init__(self, index: int, theme: Theme, angle: float, cx: int,
                 cz: int, y: int, half: int, enclosed: bool) -> None:
        self.index = index
        self.theme = theme
        self.angle = angle
        self.cx, self.cz = cx, cz
        #: The height the feet stand at. The top cell of the platform is
        #: ``y - 1``, exactly as everywhere else in this project.
        self.y = y
        self.half = half
        self.enclosed = enclosed
        self.enter: tuple[int, int, int] = (cx, y - 1, cz)
        self.leave: tuple[int, int, int] = (cx, y - 1, cz)
        self.lane: tuple[tuple[int, int, int], ...] = ()
        self.features: list[dict] = []

    def centre_cell(self) -> tuple[int, int, int]:
        return (self.cx, self.y - 1, self.cz)

    def holds(self, x: int, z: int) -> bool:
        return abs(x - self.cx) <= self.half and abs(z - self.cz) <= self.half


class Spiral:
    """Every platform, its scenery, and the columns underneath.

    Generated a platform at a time and *written* a slice at a time: a platform
    with its columns is a few thousand cells, which is tens of milliseconds of
    Python, and the scene pays for it out of a per-frame budget rather than in
    one frame.
    """

    def __init__(self, rng, base_y: int = 0) -> None:
        self.rng = rng
        self.base = base_y
        self.pads: list[Pad] = []
        self.lamps: list[tuple[int, int, int]] = []
        self._bag: list[Theme] = []
        self._built = 0            # platforms whose cells have been emitted
        #: The straight run between one platform's exit and the next one's
        #: entrance, with the height band the bridge over it occupies. Columns
        #: are not built through these. See :meth:`_clear_of_bridges`.
        self.corridors: list[tuple[float, float, float, float, int, int]] = []

    # -- laying out the spiral ---------------------------------------------

    def _next_theme(self) -> Theme:
        if not self._bag:
            self._bag = list(THEMES)
            self.rng.shuffle(self._bag)
            if self.pads and self._bag[0] is self.pads[-1].theme \
                    and len(self._bag) > 1:
                self._bag[0], self._bag[1] = self._bag[1], self._bag[0]
        return self._bag.pop(0)

    def pad(self, index: int) -> Pad:
        """The platform at ``index``, generated on demand."""
        while len(self.pads) <= index:
            self._extend()
        return self.pads[index]

    def _extend(self) -> None:
        rng = self.rng
        i = len(self.pads)
        step = 2 * math.pi / PADS_PER_TURN
        angle = i * step
        radius = SPIRAL_R + rng.uniform(-1.5, 1.5)
        half = rng.randint(*PAD_HALF)
        if self.pads:
            y = self.pads[-1].y + rng.randint(*PAD_RISE)
        else:
            y = self.base
        theme = self._next_theme()
        # A cave every so often, and never two running. The reference maps put
        # a roofed section between open ones for exactly the reason this scene
        # wants one: coming out of a dark room into the sky is the strongest
        # beat either has.
        enclosed = (theme.dark > 0.3 and rng.random() < 0.75
                    and not (self.pads and self.pads[-1].enclosed))
        pad = Pad(i, theme, angle,
                  _round(math.cos(angle) * radius), _round(math.sin(angle) * radius),
                  y, half, enclosed)
        self.pads.append(pad)
        self._route(pad)
        if len(self.pads) > 1:
            before = self.pads[-2]
            self.corridors.append((before.leave[0], before.leave[2],
                                   pad.enter[0], pad.enter[2],
                                   before.y - 3, pad.y + 4))

    def _route(self, pad: Pad) -> None:
        """Where the course comes in, where it goes out, and the lane between.

        Both are rim cells aimed at the neighbouring platforms -- in toward the
        one before, out toward the one after -- so the bridge at either end is
        a straight run and the crossing is a straight line through the middle.
        A platform whose entrance and exit were chosen independently of its
        neighbours is one the course has to double back across.
        """
        step = 2 * math.pi / PADS_PER_TURN
        back = pad.angle - step
        fwd = pad.angle + step
        pad.enter = self._rim(pad, math.cos(back) * SPIRAL_R - pad.cx,
                              math.sin(back) * SPIRAL_R - pad.cz)
        pad.leave = self._rim(pad, math.cos(fwd) * SPIRAL_R - pad.cx,
                              math.sin(fwd) * SPIRAL_R - pad.cz)
        pad.lane = tuple(_line_cells(pad.enter, pad.leave))

    def _rim(self, pad: Pad, dx: float, dz: float) -> tuple[int, int, int]:
        """The furthest cell toward ``(dx, dz)`` that is still *on* the pad.

        Walked outward and stopped at the last footprint cell rather than
        computed: a platform has its corners cut off, so the point half a width
        along a diagonal is outside it, and a way in that is not on the ground
        is a landing the course is told to make onto thin air.
        """
        n = math.hypot(dx, dz) or 1.0
        ux, uz = dx / n, dz / n
        shape = set(_pad_cells(pad.half))
        best = (0, 0)
        for step in range(1, pad.half + 1):
            cell = (_round(ux * step), _round(uz * step))
            if cell in shape:
                best = cell
        return (pad.cx + best[0], pad.y - 1, pad.cz + best[1])

    def theme_at(self, y: float) -> Theme:
        return self.pad_at(y).theme

    def theme(self, index: int) -> Theme:
        return self.pad(index).theme

    def tier_of(self, y: float) -> int:
        """Which platform's height band ``y`` is in. Named for the ring
        version's method so the scene's caption and lighting need no change."""
        return self.pad_at(y).index

    def radius_at(self, y: float) -> float:
        """There is no wall. Zero, because the inherited placement code asks
        this to work out which side of one a cell is on, and on a spiral of
        platforms the answer is always "outside"."""
        return 0.0

    def pad_at(self, y: float) -> Pad:
        """The platform whose height band contains ``y``. Used for lighting and
        for the ring caption, both of which want "where am I" rather than
        "which one am I standing on"."""
        best = self.pads[0] if self.pads else self.pad(0)
        for pad in self.pads:
            if pad.y <= y + 2:
                best = pad
        return best

    # -- emitting cells -----------------------------------------------------

    def build_to(self, index: int, place) -> int:
        """Emit every platform up to and including ``index``. Returns how many.

        ``place(cell, style)`` is the caller's, so the same generator feeds a
        probe that only counts cells and a scene that meshes them.
        """
        built = 0
        while self._built <= index:
            self._emit(self.pad(self._built), place)
            self._built += 1
            built += 1
        return built

    def _emit(self, pad: Pad, place) -> None:
        theme = pad.theme
        top = pad.y - 1
        cells = _pad_cells(pad.half)
        keep = {(pad.cx + c[0], pad.cz + c[1]) for c in cells}
        # -- the ground, two deep. One layer reads as a sheet of paper from
        # underneath, which is the angle this whole format is looked at from.
        for dx, dz in cells:
            x, z = pad.cx + dx, pad.cz + dz
            rim = max(abs(dx), abs(dz)) >= pad.half - 0
            place((x, top, z), theme.trim if rim else theme.floor)
            place((x, top - 1, z), theme.wall)
        # -- the columns. Every rim cell, leaning in as they go down, which is
        # where the cone in the reference screenshot comes from: the platforms
        # do not shrink, the legs converge.
        #
        # Except under the way in and the way out. A bridge arrives at the rim
        # from below and outside, so a leg hanging under the cell it lands on
        # is a leg in the two cells the body's head needs -- and the landing is
        # refused for want of head-room on a platform it is standing next to.
        doors = ((pad.enter[0], pad.enter[2]), (pad.leave[0], pad.leave[2]))
        for dx, dz in cells:
            if max(abs(dx), abs(dz)) < pad.half:
                continue
            x0, z0 = pad.cx + dx, pad.cz + dz
            if any(abs(x0 - dx0) <= 2 and abs(z0 - dz0) <= 2
                   for dx0, dz0 in doors):
                continue
            for depth in range(2, COLUMN_DEPTH):
                lean = 1.0 - COLUMN_LEAN * depth
                cx = pad.cx + _round(dx * lean)
                cy = top - depth
                cz = pad.cz + _round(dz * lean)
                if self._clear_of_bridges(cx, cy, cz):
                    place((cx, cy, cz), "stone")
        if pad.enclosed:
            self._roof(pad, place, keep)
        self._dress(pad, place, keep)

    def _clear_of_bridges(self, x: int, y: int, z: int) -> bool:
        """Is this column cell out of the way of a bridge further down?

        A spiral comes back over itself: five platforms a revolution means the
        one directly above is thirty-odd blocks up, and legs that hang
        twenty-four deep from it reach into the exact stretch of air the bridge
        below climbs through. Measured before this existed, that one collision
        was most of a placement failure rate of twenty-three per cent -- the
        bridge could not be built because the building above it was in the way.

        Both are laid out by the spiral from the same geometry, so it can
        simply be asked. Nothing here depends on the course.
        """
        for ax, az, bx, bz, lo, hi in self.corridors:
            if not (lo <= y <= hi):
                continue
            if _seg_dist(x, z, ax, az, bx, bz) < BRIDGE_CLEAR:
                return False
        return True

    def _roof(self, pad: Pad, place, keep) -> None:
        """Walls and a ceiling: the cave.

        Openings are punched at the two rim cells the course actually uses, and
        only there, so a cave is a room with a way in and a way out rather than
        a box the generator has to find a hole in.
        """
        theme = pad.theme
        top = pad.y - 1
        doors = {(pad.enter[0], pad.enter[2]), (pad.leave[0], pad.leave[2])}
        for dx, dz in _pad_cells(pad.half):
            x, z = pad.cx + dx, pad.cz + dz
            if max(abs(dx), abs(dz)) == pad.half:
                if (x, z) in doors:
                    continue
                for h in range(1, ROOF_H):
                    place((x, top + h, z), theme.wall)
            place((x, top + ROOF_H, z), theme.trim)
        # ...and it needs light, or it is a black hole in the middle of a
        # bright sky. The cells are handed back so the scene can hang a glow on
        # each: the building is meshed, and you cannot pick one emissive block
        # out of a mesh.
        for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x = pad.cx + sx * (pad.half - 1)
            z = pad.cz + sz * (pad.half - 1)
            place((x, top + ROOF_H - 1, z), theme.glow)
            self.lamps.append((x, top + ROOF_H - 1, z))

    def _dress(self, pad: Pad, place, keep) -> None:
        """The scenery that makes a platform a *place* rather than a floor.

        Everything here keeps a cell clear of the lane, which is the run
        between the way in and the way out -- so the course never has to
        negotiate with the platform's own decoration, and the decoration never
        has to know the course exists.
        """
        rng = self.rng
        theme = pad.theme
        top = pad.y - 1
        lane = {(c[0], c[2]) for c in pad.lane}
        for c in list(lane):
            for ox in (-1, 0, 1):
                for oz in (-1, 0, 1):
                    lane.add((c[0] + ox, c[1] + oz))
        free = [(pad.cx + dx, pad.cz + dz) for dx, dz in _pad_cells(pad.half - 1)
                if (pad.cx + dx, pad.cz + dz) not in lane]
        rng.shuffle(free)
        budget = len(free) // (2 if pad.enclosed else 3)
        kit = DRESSING.get(theme.name, DRESSING["_default"])
        for x, z in free[:budget]:
            what = kit[rng.randrange(len(kit))]
            if what == "lamp":
                place((x, top + 1, z), theme.glow)
                self.lamps.append((x, top + 1, z))
            elif what == "post":
                for h in (1, 2):
                    place((x, top + h, z), theme.trim)
                place((x, top + 3, z), theme.glow)
                self.lamps.append((x, top + 3, z))
            elif what == "block":
                place((x, top + 1, z), theme.accent)
            elif what == "pool":
                place((x, top, z), "water")
            elif what == "hollow":
                place((x, top, z), theme.wall)
            else:
                place((x, top + 1, z), what)


#: What grows, stands or pools on each theme's platform. Sub-block furniture --
#: crops, flowers, fences -- is drawn by the scene from these same names; the
#: entries here are the *materials*, and how they are shaped is a drawing
#: question rather than a generation one.
DRESSING = {
    "_default": ("block", "post", "hollow"),
    "keep": ("post", "block", "hollow", "hollow"),
    "timber": ("post", "block", "block", "hollow"),
    "mine": ("lamp", "block", "hollow", "hollow", "block"),
    "overgrown": ("leaves", "leaves", "moss", "post", "pool"),
    "desert": ("block", "post", "sand", "hollow"),
    "nether": ("lamp", "magma", "magma", "block", "hollow"),
    "ice": ("snow", "packedice", "block", "post"),
    "lab": ("slime", "honey", "block", "post"),
    "deep": ("pool", "pool", "sealantern", "block"),
    "end": ("block", "post", "obsidian", "hollow"),
    "summit": ("post", "lamp", "block", "gold"),
}

def _out(pad: Pad, cell) -> tuple[float, float]:
    """The outward direction at a rim cell: away from the platform's middle."""
    dx, dz = cell[0] - pad.cx, cell[2] - pad.cz
    n = math.hypot(dx, dz) or 1.0
    return dx / n, dz / n


def _seg_dist(px: float, pz: float, ax: float, az: float,
              bx: float, bz: float) -> float:
    """Distance from a point to a line *segment*, in the ground plane."""
    dx, dz = bx - ax, bz - az
    n = dx * dx + dz * dz
    t = 0.0 if n <= 1e-9 else max(0.0, min(1.0, ((px - ax) * dx
                                                 + (pz - az) * dz) / n))
    return math.hypot(px - (ax + dx * t), pz - (az + dz * t))


_PAD_CACHE: dict[int, tuple[tuple[int, int], ...]] = {}


def _pad_cells(half: int) -> tuple[tuple[int, int], ...]:
    """A platform's footprint: a square with the corners taken off, which from
    a distance reads as a rounded plate rather than as a tile."""
    got = _PAD_CACHE.get(half)
    if got is None:
        cut = max(1, half // 2)
        got = tuple((dx, dz)
                    for dx in range(-half, half + 1)
                    for dz in range(-half, half + 1)
                    if abs(dx) + abs(dz) <= half + cut)
        _PAD_CACHE[half] = got
    return got


# Imported late: THEMES is a list of Theme instances built in towerplan, and
# importing it at the top would be a cycle only if towerplan grew a dependency
# the other way. It has not, and this keeps the two lists in one place.
from .towerplan import THEMES  # noqa: E402


# ---------------------------------------------------------------------------
# The course
# ---------------------------------------------------------------------------

from .towerplan import Course as _RingCourse  # noqa: E402

#: What a bridge between two platforms is made of. Every entry lays the same
#: line of stepping stones and dresses it differently, because the geometry of
#: a bridge is fixed by where the two platforms are and only its *character* is
#: a choice. Weighted, and reweighted by the difficulty ramp.
BRIDGES = {
    "stones": 22.0,
    "pillars": 14.0,
    "lanterns": 10.0,
    "beams": 9.0,
    "arches": 9.0,
    "ice": 7.0,
    "slime": 6.0,
    "ladder": 6.0,
    "webs": 5.0,
}
BRIDGE_RAMP = {"arches": 1.6, "slime": 1.4, "ice": 1.2,
               "stones": -0.5, "lanterns": -0.4}
#: Metres between consecutive stepping stones. Under the 3.10 m a hop that
#: climbs a block can reach, because most of a bridge climbs: five platforms a
#: revolution at seven blocks each has to gain that height somewhere, and it
#: gains it out over the drop rather than on the flat.
STONE_STEP = 2.8


class Course(_RingCourse):
    """Cross a platform, bridge to the next, cross that one.

    Everything about *how a body moves* -- the moves, the lattice, the
    occupancy rules, the reservations, the orb solver -- is inherited
    unchanged. What is replaced is the layer above it: where the course is
    trying to go and why. The ring version rolled for a set-piece and then
    negotiated with placement; this one is told by the spiral, so a node is
    aimed at a *cell* rather than at a bearing and a radius.
    """

    def __init__(self, rng, spiral: Spiral, hop_rng=None) -> None:
        self.rng = rng
        self.hop_rng = hop_rng or rng
        self.tower = spiral
        self.struct: dict[tuple[int, int, int], str] = {}
        self.writes: list[tuple[tuple[int, int, int], str]] = []
        self.solid: set[tuple[int, int, int]] = set()
        self.headroom: set[tuple[int, int, int]] = set()
        self.softcells: set[tuple[int, int, int]] = set()
        self.pathcells: set[tuple[int, int, int]] = set()
        self.blocks: list[dict] = []
        self._pending: list[dict] = []
        self.segment = "start"
        self.laid = 0
        self.stuck = 0
        self.bailed = 0
        self.orbs_missed = 0
        self.wind = 1
        self.high = 0
        self.expected = 0.0
        self._approach = 0
        self._indoor = 0
        self._left_at = -99
        self._checked: set[int] = set()

        #: Which platform the course is on, and whether it is crossing it or
        #: bridging off it. The whole plan is these two.
        self.pad_i = 0
        self.stage = "cross"
        self.bridge = "stones"
        self.stone = 0

        spiral.build_to(PADS_AHEAD, self._place_struct)
        first = spiral.pad(0)
        self.high = first.y
        self.expected = float(first.y)
        blk = self._block(first.enter[0], first.enter[1], first.enter[2],
                          style=first.theme.floor, form="floor",
                          step=_toward(first.enter, first.leave),
                          segment="start", theme=first.theme.name)
        self.blocks.append(blk)
        self.headroom.update((blk["x"], blk["y"] + h, blk["z"])
                             for h in range(1, HEADROOM + 1))
        while len(self.blocks) < AHEAD:
            self.spawn()

    # -- the plan -----------------------------------------------------------

    @property
    def difficulty(self) -> float:
        return min(1.0, self.laid / RAMP_BLOCKS)

    @property
    def climb_pressure(self) -> float:
        """Always zero. The spiral *is* the climb: every platform is higher
        than the last by construction, so there is nothing to correct and no
        way for a run to wander downhill."""
        return 0.0

    def spawn(self) -> dict:
        if not self._pending:
            self._plan()
        prev = self.blocks[-1]
        node = self._pending.pop(0)
        self.laid += 1
        self.tower.build_to(self.pad_i + PADS_AHEAD, self._place_struct)
        got = self._try(prev, node)
        if got is None:
            self.stuck += 1
            got = self._emergency(prev, node)
            node = dict(node, label="stuck")
        return self._commit(prev, node, got)

    def _plan(self) -> None:
        if self.stage == "cross":
            pad = self.tower.pad(self.pad_i)
            self.segment = "cave" if pad.enclosed else "cross"
            self._pending = self._seg_cross(pad)
            self.stage = "bridge"
            self.bridge = self._roll_bridge()
            self.stone = 0
            return
        # A bridge is generated **one stone at a time**, from where the body
        # actually is rather than from where a plan assumed it would be.
        #
        # That is not a refinement, it is the difference between working and
        # not. A bridge has to gain the whole of a platform's rise -- five to
        # nine blocks -- and one jump reaches one, so a pre-computed line of
        # stones is a chain in which any single failure leaves the body a block
        # short and every stone after it asking for a rise the physics does not
        # have. Measured that way: one placement in five fell through to the
        # unchecked answer. Reactively, each stone is 2.8 m nearer and at most a
        # block higher than the one the body is *on*, so the bridge converges
        # on the next platform from wherever it has got to.
        prev = self.blocks[-1]
        there = self.tower.pad(self.pad_i + 1)
        target = there.enter
        # Aimed at a point a few cells *outside* the rim, not at the rim cell
        # itself. A bridge that heads straight for its landing spends its last
        # two or three stones inside the platform it is aiming at -- the cells
        # are the platform's own ground, so they are occupied, and the stone is
        # refused. Approaching from outside and stepping up onto the rim is
        # both placeable and what it should look like.
        ux, uz = _out(there, target)
        aim = (target[0] + _round(ux * 3), target[1], target[2] + _round(uz * 3))
        flat = math.dist((prev["x"], prev["z"]), (target[0], target[2]))
        if (flat <= 4.4 and abs(target[1] - prev["y"]) <= 1) or self.stone > 18:
            self.segment = self.bridge
            self._pending = [self._node(style=there.theme.floor, form="floor",
                                        spread=0, cell=target, orbs=1,
                                        label=self.bridge)]
            self.pad_i += 1
            self.stage = "cross"
            return
        self.stone += 1
        self.segment = self.bridge
        span = max(1e-3, math.dist((prev["x"], prev["z"]), (aim[0], aim[2])))
        y = prev["y"]
        if y < target[1]:
            y += 1
        elif y > target[1] + 1:
            y -= 1

        # Walked out along the line until the *cell* is a real hop away, not
        # placed at a distance and rounded. Rounding a 2.8 m step onto the
        # lattice can land it 1.4 m out, which is under ``MIN_HOP`` and gets
        # refused -- and then the next stone is measured from a body that never
        # moved.
        ux = (aim[0] - prev["x"]) / span
        uz = (aim[2] - prev["z"]) / span
        cell = (_round(prev["x"] + ux * STONE_STEP), y,
                _round(prev["z"] + uz * STONE_STEP))
        for reach in range(1, 7):
            cell = (_round(prev["x"] + ux * (STONE_STEP + reach * 0.4)), y,
                    _round(prev["z"] + uz * (STONE_STEP + reach * 0.4)))
            if math.dist((prev["x"], prev["z"]), (cell[0], cell[2])) >= 2.75:
                break
        self._pending = [self._bridge_node(self.bridge, there.theme,
                                           self.stone, cell, self.rng)]

    def _roll_bridge(self) -> str:
        hard = self.difficulty
        rng = self.rng
        weights = [(name, base * max(0.05, 1.0 + BRIDGE_RAMP.get(name, 0.0) * hard))
                   for name, base in BRIDGES.items() if name != self.segment]
        roll = rng.random() * sum(w for _, w in weights)
        upto = 0.0
        for name, w in weights:
            upto += w
            if roll <= upto:
                return name
        return weights[-1][0]

    # -- crossing a platform ------------------------------------------------

    def _seg_cross(self, pad: Pad) -> list[dict]:
        """Run over the platform, from the way in to the way out.

        Landings are on the ground itself -- ``floor`` nodes, which place no
        block and stand on what the spiral already built -- so a crossing is
        the body running over real terrain rather than over a line of cubes
        somebody floated there. Every second or third cell, so there is still a
        hop between them: a course that lands on every cell is a walk.

        The style carried on each landing is the platform's own floor material,
        which is what makes an ice platform slide and a soul-sand one drag:
        ``ground_speed`` reads it, and that one number is most of what makes a
        theme feel like what it is made of.
        """
        rng = self.rng
        lane = pad.lane
        if len(lane) < 3:
            return [self._node(style=pad.theme.floor, form="floor", spread=0,
                               cell=pad.leave, label="cross")]
        # Picked by *distance*, not by counting cells. A lane is a run of
        # adjacent cells, so a fixed stride of two is 2 m along an axis and
        # 2.8 m along a diagonal -- and the first of those is under ``MIN_HOP``
        # and gets refused. Every landing is at least a real hop from the last.
        out: list[dict] = []
        picks: list[int] = []
        last = 0
        for i in range(1, len(lane)):
            if math.dist(lane[last], lane[i]) >= 2.9:
                picks.append(i)
                last = i
        if not picks or math.dist(lane[picks[-1]], lane[-1]) >= 2.9:
            picks.append(len(lane) - 1)
        else:
            picks[-1] = len(lane) - 1
        for n, i in enumerate(picks):
            cell = lane[i]
            # A feature every so often: a block on the ground to hop up onto,
            # which on a farm is a hay bale and in a cave is a fallen rock. It
            # is the same node either way -- what changes is the material.
            lift = 1 if (n and n < len(picks) - 1 and rng.random() < 0.30) else 0
            out.append(self._node(
                style=pad.theme.accent if lift else pad.theme.floor,
                form="full" if lift else "floor", spread=0,
                cell=(cell[0], cell[1] + lift, cell[2]),
                deco="lantern" if pad.enclosed and n % 3 == 1 else None,
                orbs=1 if rng.random() < 0.55 else 0,
                label="cave" if pad.enclosed else "cross"))
        return out

    # -- the bridge between two platforms -----------------------------------

    def _bridge_node(self, style: str, theme: Theme, i: int, cell,
                     rng) -> dict:
        """One stepping stone, dressed according to the bridge's style.

        The geometry is already decided by the time this is called -- where the
        two platforms are is the only sensible place for a bridge -- so what a
        style chooses is character: what holds the stone up, what hangs over it,
        what it is made of. That separation is why there are nine of them and
        an argument with placement in none of them.
        """
        common = dict(cell=cell, label=style,
                      orbs=1 if rng.random() < 0.5 else 0)
        candy = CANDY[i % len(CANDY)]
        if style == "pillars":
            return self._node(style=candy, support=rng.randint(6, 14),
                              support_style=theme.wall, **common)
        if style == "lanterns":
            return self._node(style=theme.glow if i % 2 else candy,
                              deco="lantern" if i % 2 else None, **common)
        if style == "beams":
            return self._node(style=theme.accent, deco="beam", **common)
        if style == "arches":
            return self._node(style=candy,
                              deco="lintel" if i % 2 else "rail", **common)
        if style == "ice":
            return self._node(style="packedice", form="ice", **common)
        if style == "slime":
            if i % 3 == 2:
                return self._node(style="slime", form="slime", **common)
            return self._node(style=candy, **common)
        if style == "ladder" and i == 2:
            return self._node(style=theme.accent, kind="climb",
                              support=rng.randint(6, 10),
                              support_style=theme.wall, deco="lantern",
                              orbs=2, cell=(cell[0], cell[1] + rng.randint(3, 5),
                                            cell[2]), label=style)
        if style == "webs" and i % 4 == 3:
            return self._node(style=theme.trim, kind="web", **common)
        return self._node(style=candy,
                          form="slab" if rng.random() < 0.18 else "full",
                          deco="rail" if rng.random() < 0.15 else None,
                          **common)

    # -- placement ----------------------------------------------------------

    def _node(self, style: str, cell, gap: int = 2, rise: int = 0,
              kind: str = "hop", form: str = "full", deco: str | None = None,
              orbs: int = 0, support: int = 0, support_style: str | None = None,
              spread: int = 1, label: str | None = None) -> dict:
        """One entry in a plan. Aimed at a *cell*, which is the whole
        difference from the ring version: the spiral knows where everything is,
        so nothing has to be searched for."""
        return {"style": style, "cell": cell, "gap": gap, "rise": rise,
                "rises": [rise], "kind": kind, "form": form, "radial": 0.0,
                "deco": deco, "orbs": orbs, "support": support,
                "support_style": support_style, "to_y": None, "radius": None,
                "angle": None, "label": label, "spread": spread}

    def _try(self, prev: dict, node: dict):
        """The wanted cell, then its neighbours, then a shorter reach.

        Far less machinery than the ring version needed, and that is the point
        of scheduling rather than rolling: the answer is nearly always the
        first cell tried, because the spiral chose it knowing where everything
        else is.
        """
        for cell in _near(node["cell"], node["spread"]):
            got = self._attempt(prev, node, cell)
            if got is not None:
                return got
        for cell in _near(node["cell"], node["spread"]):
            got = self._attempt(prev, node, cell, strict=False)
            if got is not None:
                return got
        # Still nothing: take the same step at whatever height fits, which for
        # a bridge stone is a stone one lower and for a landing is the next cell
        # of the platform along.
        loose = dict(node, form="full", kind="hop", deco=None, support=0)
        for dy in (-1, 1, -2, 2):
            for cell in _near((node["cell"][0], node["cell"][1] + dy,
                               node["cell"][2]), 2):
                got = self._attempt(prev, loose, cell, strict=False)
                if got is not None:
                    return got
        return None

    def _targets(self, prev: dict, node: dict, rise: int):
        return [node["cell"]]

    def _clear_of_gallery(self, cx: int, cy: int, cz: int) -> bool:
        return True

    def _emergency(self, prev: dict, node: dict):
        """The one unchecked answer. Aimed at the cell that was wanted, at
        whatever height there is room at.

        Reached far less often than the ring version's, because there is no
        searching to fail: the spiral says where the next landing is and the
        platform under it already exists.
        """
        for dy in (0, 1, -1, 2, -2, -4):
            for cell in _near((node["cell"][0], node["cell"][1] + dy,
                               node["cell"][2]), 2):
                cells = _footprint(*cell, "full")
                if not self._free(cells):
                    continue
                if not self._free((x, y + h, z) for x, y, z in cells
                                  for h in range(1, HEADROOM + 1)):
                    continue
                step = (cell[0] - prev["x"], cell[2] - prev["z"])
                if step == (0, 0):
                    continue
                frm = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                                    prev["form"], step)
                to = land_point(cell[0], cell[1] + 1.0, cell[2], "full", step)
                return {"cell": cell, "step": step, "form": "full",
                        "move": hop_move(frm, to), "soft": (), "support": ()}
        cell = (prev["x"], prev["y"] + 1, prev["z"] + 1)
        step = (0, 1)
        frm = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                            prev["form"], step)
        to = land_point(cell[0], cell[1] + 1.0, cell[2], "full", step)
        return {"cell": cell, "step": step, "form": "full",
                "move": hop_move(frm, to), "soft": (), "support": ()}


def _toward(a, b) -> tuple[int, int]:
    dx, dz = b[0] - a[0], b[2] - a[2]
    n = max(abs(dx), abs(dz)) or 1
    return (_round(dx / n), _round(dz / n))


def _near(cell, spread: int = 1):
    """The cell itself, then the ones around it, nearest first."""
    cx, cy, cz = cell
    out = [(cx, cy, cz)]
    for r in range(1, spread + 1):
        ring = []
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if max(abs(dx), abs(dz)) != r:
                    continue
                ring.append((math.hypot(dx, dz), cx + dx, cy, cz + dz))
        ring.sort()
        out += [(x, y, z) for _, x, y, z in ring]
    return out
