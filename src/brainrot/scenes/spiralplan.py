"""The spiral proper: themed *platforms* winding up, and the parkour between.

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

**One rule holds the whole file up**, and it was learned twice, once on each
half of the course: *every node is decided from where the body actually is*,
never from where an earlier plan assumed it would be. A plan laid several
nodes deep is a chain in which the first landing that comes down a cell to one
side, or a block low because its own hop was refused, makes every node after
it ask for a step the physics does not have. Both halves are reactive now --
:meth:`Course._cross_node` and :meth:`Course._plan` return one node each -- and
each node carries the runners-up it would have accepted, because placement has
to answer questions the plan cannot see.

Placement fell through to its one unchecked answer on **13% of nodes** when
this file was handed over. It is 0.23% now, against 0.28% for the ring version
that shipped, and every step of the way down is recorded at the line that
fixed it. Nothing on that list was found by reading the code: each one came
from a counter wrapped round ``Course._attempt`` that records which check said
no. Rebuild that counter before changing anything here -- guessing cost the
previous session several rounds and it found each cause in one.
"""

from __future__ import annotations

import math

from .towerplan import (  # noqa: F401  (re-exported for the scene and probes)
    AIR_MIN, AIR_MAX, AIR_SPEED, BODY_H, BODY_HALF_W, BUBBLE_SPEED, CANDY,
    CHEST, CLIMB_SPEED, EDGE, EYE, FORMS, GRAVITY, HEADROOM, ICE_AIR, ICE_RUN,
    JUMP_V, MATERIALS, MIN_HOP, Move, RUN_SPEED, SEE_THROUGH, SOUL_SPEED,
    SPREAD, SURFACE_SPEED, VY_MAX, VY_MIN, WALK_SPEED, WEB_SPEED, Theme,
    arc_leg, body_cells, bounce_launch, fall_speed, fit_gap, hop_move,
    hop_span, land_point, line_leg, quantise, takeoff_point, _deco, _floor,
    _footprint, _line_cells, _round, _standing_cells, _wrap,
)

# ---------------------------------------------------------------------------
# The shape of the spiral
# ---------------------------------------------------------------------------

#: Platforms in one revolution, how far out from the axis they stand, and how
#: big they are. These four numbers are one decision, and the thing they decide
#: is the only one the format is actually about: **how much of a run happens on
#: built ground rather than out on floating stones.**
#:
#: The first version of this file had five platforms of eleven to fifteen cells
#: on a radius of twenty-two, which puts them twenty-six metres apart and
#: leaves a gap of fourteen -- eight or nine stones of bridge against four
#: landings of crossing. Measured with ``tools/spiral_probe.py``: **a quarter**
#: of the run was spent on a platform, in stretches of a second and a half,
#: against four and a half seconds at a time out over the drop. That is the
#: cylinder this file replaced, wearing a hat.
#:
#: Six platforms of seventeen to twenty-three cells on a radius of twenty-eight
#: are twenty-eight metres apart with a gap of six to twelve -- two to four
#: stones of bridge against six or seven landings of crossing, and the ratio
#: comes out the other way up. A gap under about five metres would be a
#: staircase of touching islands; over about fifteen and the bridge is the
#: scene again.
PADS_PER_TURN = 6
SPIRAL_R = 34.0
PAD_HALF = (11, 14)
#: What each platform climbs over the last, and it falls out of the gap rather
#: than being chosen: a bridge gains at most one block a stone, and there are
#: two to four stones. Ask for more and the difference is made up by the flight
#: of steps beside the rim, which is a fine answer once and a spiral staircase
#: with a platform on top of it three times a minute. Six a platform at six
#: platforms a turn is still thirty-six blocks a revolution.
PAD_RISE = (3, 6)
#: How far the columns under a platform run down before they are simply not
#: built. They are the whole silhouette of the thing from outside, and they are
#: also the cheapest geometry in the scene: one style, no faces where they
#: touch -- but there are a great many of them, and at these platform sizes
#: they are most of the cells in the world. Eighteen still leaves every one of
#: them running out of the bottom of a portrait frame, and it is a fifth off
#: the per-frame cost.
COLUMN_DEPTH = 18
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
                 "enclosed", "enter", "leave", "lane", "features", "lift")

    def __init__(self, index: int, theme: Theme, angle: float, cx: int,
                 cz: int, y: int, half: int, enclosed: bool,
                 lift: int = 0) -> None:
        self.index = index
        self.theme = theme
        self.angle = angle
        self.cx, self.cz = cx, cz
        #: The height the feet stand at. The top cell of the platform is
        #: ``y - 1``, exactly as everywhere else in this project.
        self.y = y
        self.half = half
        self.enclosed = enclosed
        #: How much higher the way out is than the way in. The platform is
        #: terraced, so the crossing climbs part of what the spiral has to
        #: climb and the bridge is only asked for the rest -- which is what
        #: keeps a bridge two to four stones long while a platform still gains
        #: six blocks a turn. It is also what the reference maps look like:
        #: their platforms have terrain on them, not a flat plate.
        self.lift = lift
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
        #: ``(cell, kind, yaw)`` for every piece of sub-block furniture. Handed
        #: to the scene to draw as models -- see :meth:`_plant`.
        self.props: list[tuple[tuple[int, int, int], str, float]] = []
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
        theme = self._next_theme()
        # A cave every so often, and never two running. The reference maps put
        # a roofed section between open ones for exactly the reason this scene
        # wants one: coming out of a dark room into the sky is the strongest
        # beat either has.
        enclosed = (theme.dark > 0.3 and rng.random() < 0.75
                    and not (self.pads and self.pads[-1].enclosed))
        # A cave's terrace is capped at one, because the roof is five above the
        # floor and a body needs two over its feet: a three-step terrace under
        # it leaves a metre of head-room and every landing on the top step is
        # refused for want of it.
        lift = rng.randint(0, 1) if enclosed else rng.randint(1, 3)
        # The bridge climbs what the platform did not, so what is rolled here
        # is the *bridge's* share and the terrace is added to it. Rolling the
        # total instead makes a tall platform and a long climb the same event,
        # and the seed that draws both hands the bridge a rise it has no room
        # for -- which is the shape of the defect this file was written to fix.
        if self.pads:
            y = (self.pads[-1].y + self.pads[-1].lift
                 + rng.randint(*PAD_RISE))
        else:
            y = self.base
        pad = Pad(i, theme, angle,
                  _round(math.cos(angle) * radius), _round(math.sin(angle) * radius),
                  y, half, enclosed, lift)
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
        leave = self._rim(pad, math.cos(fwd) * SPIRAL_R - pad.cx,
                          math.sin(fwd) * SPIRAL_R - pad.cz)
        pad.leave = (leave[0], leave[1] + pad.lift, leave[2])
        # The lane is flat ground until near the far rim and then a flight of
        # steps, rather than one long ramp from one side to the other.
        #
        # Interpolating the whole way is the obvious thing and it is wrong
        # twice over. It makes two thirds of a platform's landings *built
        # blocks* rather than its own ground, which is the one thing this
        # format exists to avoid -- measured, landings on real ground went from
        # 44% to 20%. And it puts a step every cell or two, while landings are
        # a hop apart, so consecutive landings differ by two blocks: a rise
        # nothing in the game can make.
        #
        # Three cells of run-up per step is therefore not a look, it is the
        # spacing at which each landing climbs exactly one.
        dx, dz = leave[0] - pad.enter[0], leave[2] - pad.enter[2]
        n = math.hypot(dx, dz) or 1.0
        back = min(n - 1.0, 3.0 * pad.lift + 1.0)
        knee = (_round(leave[0] - dx / n * back), pad.y - 1,
                _round(leave[2] - dz / n * back))
        run = list(_line_cells(pad.enter, knee))
        if pad.lift:
            run += list(_line_cells(knee, pad.leave))
        # One cell per column, highest wins. A run interpolated onto the
        # lattice can put the same column in twice at two heights, and the
        # lower of those is a landing with the next step sitting on its head.
        seen: dict[tuple[int, int], tuple[int, int, int]] = {}
        for cell in run:
            at = (cell[0], cell[2])
            if at not in seen or cell[1] > seen[at][1]:
                seen[at] = cell
        pad.lane = tuple(seen.values())

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

    def roofed(self, x: float, y: float, z: float) -> bool:
        """Is this point under a platform's roof?

        The spiral's answer to the ring tower's "which side of the wall am I
        on". There is no wall, so the question is which platform's footprint
        the body is standing in and whether that one has a lid -- and it has to
        be answered against the *height band* as well, or a body on the bridge
        thirty blocks under a cave is told it is indoors.
        """
        for pad in self.pads:
            if not pad.enclosed:
                continue
            if pad.y - 1 <= y <= pad.y + ROOF_H and pad.holds(_round(x),
                                                              _round(z)):
                return True
        return False

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
        doors = ((pad.enter[0], pad.enter[2]), (pad.leave[0], pad.leave[2]))
        for dx, dz in _pad_cells(pad.half):
            x, z = pad.cx + dx, pad.cz + dz
            if max(abs(dx), abs(dz)) == pad.half:
                # Three cells wide, not one. A body is 0.6 m across and plants
                # its feet 0.4 m from a block's centre along the way it is
                # going, so on a diagonal approach it occupies 0.58 m either
                # side of the middle of the cell it is standing in -- past the
                # cell wall, into whatever is next to the doorway. A one-cell
                # opening therefore refuses every diagonal entry, and every
                # platform's way in and way out is diagonal more often than
                # not: measured, that and the lifts beside it were 34 of the
                # 88 remaining placement failures.
                #
                # Widened again to five, once the platforms grew: a bridge
                # arrives at a rim cell from three cells out and a couple
                # below, so the arc crosses the wall line a metre or two to one
                # side of the doorway it is aiming at, and the last stretch of
                # a crossing leaves the same way. Caves on their own were half
                # of everything the course could not place.
                if any(abs(x - dx0) <= 2 and abs(z - dz0) <= 2
                       for dx0, dz0 in doors):
                    continue
                for h in range(1, ROOF_H):
                    place((x, top + h, z), theme.wall)
            place((x, top + ROOF_H, z), theme.trim)
        # ...and it needs light, or it is a black hole in the middle of a
        # bright sky. The cells are handed back so the scene can hang a glow on
        # each: the building is meshed, and you cannot pick one emissive block
        # out of a mesh.
        #
        # On a grid, not one in each corner. Four lamps lit a room eleven cells
        # across; these are twenty-nine, so the corners are fourteen metres from
        # the middle and the middle is where the course runs. Read off a contact
        # sheet rather than reasoned about: three consecutive frames of a
        # fourteen-frame run came back essentially black, which on a strip that
        # is on screen for fifteen seconds is a fifth of it showing nothing.
        step = max(4, pad.half // 2)
        for dx in range(-pad.half + 1, pad.half, step):
            for dz in range(-pad.half + 1, pad.half, step):
                x, z = pad.cx + dx, pad.cz + dz
                if (x, z) not in keep:
                    continue
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
        # Two cells clear of the lane, not one. One is enough for the cell the
        # body *stands* in and not for the one it flies over: placement is
        # allowed to land a cell to either side of the lane when the middle of
        # it is occupied, and from there a lamp post two cells out is one cell
        # out, and the arc clips it. It is also the cheapest of the fixes,
        # because a platform is twenty-five cells across and the lane is one.
        lane = {(c[0], c[2]) for c in pad.lane}
        for c in list(lane):
            for ox in range(-2, 3):
                for oz in range(-2, 3):
                    lane.add((c[0] + ox, c[1] + oz))
        free = [(pad.cx + dx, pad.cz + dz) for dx, dz in _pad_cells(pad.half - 1)
                if (pad.cx + dx, pad.cz + dz) not in lane]
        rng.shuffle(free)
        # A sixth of the free ground, not a half. The fraction was chosen when a
        # platform was eleven cells across and a hundred and twenty free cells;
        # at twenty-nine it is six hundred, and half of that is three hundred
        # separate one-cell decorations on one platform -- which is both more
        # scenery than a farm has and, because each of them is an isolated cube
        # with six visible faces, several times the meshing cost of the ground
        # it is standing on.
        budget = len(free) // (5 if pad.enclosed else 6)
        kit = DRESSING.get(theme.name, DRESSING["_default"])
        self._plant(pad, free[budget:], rng)
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

    def _plant(self, pad: Pad, spare, rng) -> None:
        """The thin furniture: crops, flowers, fences, lantern posts, cane.

        Not cells, and that is the point of it. Everything else in this scene
        is whole cells because everything else is a *building*; a platform is
        a place, and what makes a farm read as a farm is exactly the parts of
        the game that are not cubes -- wheat and flowers are two crossed quads,
        a fence is a post and two rails, cane is a stalk a few pixels wide. As
        cells they all come out as the same coloured box, which is what these
        platforms used to be scattered with and what read as rubble.

        Handed to the scene rather than placed, for the same reason the lamps
        are: the building is meshed, and a mesh has no room in it for a model.

        A fixed count rather than a fraction of the platform, and a small one.
        These are drawn one model at a time -- against a whole platform of
        ground that is a handful of draw calls -- so the budget is set by what
        the frame can afford rather than by how much room there is.
        """
        kit = PLANTS.get(pad.theme.name)
        if not kit or not spare:
            return
        top = pad.y - 1
        for x, z in spare[:PLANT_BUDGET]:
            what = kit[rng.randrange(len(kit))]
            if what == "mcfence":
                # A fence is a run or it is a post standing on its own in a
                # field. Three or four cells along one axis, which is also why
                # it carries a heading: the rails have to line up.
                step = (1, 0) if rng.random() < 0.5 else (0, 1)
                for i in range(rng.randint(3, 5)):
                    at = (x + step[0] * i, top + 1, z + step[1] * i)
                    if not pad.holds(at[0], at[2]):
                        break
                    self.props.append((at, what, 0.0 if step[0] else HALF_PI))
                continue
            self.props.append(((x, top + 1, z), what,
                               rng.uniform(0.0, 2.0 * math.pi)))


#: What grows, stands or pools on each theme's platform. Sub-block furniture --
#: crops, flowers, fences -- is drawn by the scene from these same names; the
#: entries here are the *materials*, and how they are shaped is a drawing
#: question rather than a generation one.
#: The sub-block furniture each theme grows, drawn as models by the scene from
#: ``assets/src/props_mc.py``. A theme with no entry simply has none -- the end
#: and the nether are not places anything grows, and a rainbow floor with a
#: hedge on it is worse than a rainbow floor.
PLANTS = {
    "overgrown": ("crop", "crop", "flower", "sugarcane", "mcfence"),
    "timber": ("mcfence", "mcfence", "crop", "lanternpost"),
    "keep": ("lanternpost", "mcfence", "flower"),
    "desert": ("sugarcane", "mcfence", "lanternpost"),
    "mine": ("lanternpost", "chain", "chain"),
    "ice": ("lanternpost", "chain"),
    "deep": ("chain", "chain", "lanternpost"),
    "summit": ("lanternpost", "flower", "chain"),
}
#: How many of them one platform gets. Each is its own draw call against a
#: whole platform of ground that costs a handful, so this is set by the frame
#: budget rather than by how much room there is: at twelve the scene measures
#: within noise of no props at all, and it is already the difference between a
#: field and a floor.
PLANT_BUDGET = 12
HALF_PI = math.pi / 2

DRESSING = {
    "_default": ("block", "post", "hollow"),
    "keep": ("post", "block", "hollow", "hollow"),
    "timber": ("post", "block", "block", "hollow"),
    "mine": ("lamp", "block", "hollow", "hollow", "block"),
    "overgrown": ("leaves", "leaves", "moss", "post", "pool"),
    "desert": ("block", "post", "sandstone", "hollow"),
    "nether": ("lamp", "magma", "magma", "block", "hollow"),
    "ice": ("snow", "packedice", "block", "post"),
    "lab": ("slime", "honey", "block", "post"),
    "deep": ("pool", "pool", "sealantern", "block"),
    "end": ("block", "post", "obsidian", "hollow"),
    "summit": ("post", "lamp", "block", "gold"),
}

#: The scene builds its world as ``plan.Tower(rng, 0)``. Naming the spiral's
#: building class after the one it replaces is what lets one renderer draw
#: both -- ``scenes/tower.py`` is a renderer, and it has no business knowing
#: whether the thing it is drawing is a cylinder or a stack of platforms.
Tower = Spiral


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
#: How far a bridge may be from the platform it is aiming at before the flight
#: of steps beside the rim is worth looking for. Six metres is two hops.
BESIDE_R = 6.0
#: Rings of cells the flight of steps is drawn from, out from the landing cell.
#: Three is clear of the platform's own ground and its columns; six is as far
#: out as a staircase can wander and still read as belonging to the platform.
BESIDE_RINGS = (3, 4, 5, 6)


def _band(from_form: str, to_form: str, rise: float,
          dx: float = 1.0, dz: float = 0.0) -> tuple[float, float]:
    """The **cell-centre** distances a hop of this rise and heading may cover.

    :func:`hop_span` answers in take-off and landing *points*, and a plan
    chooses *cells*; the difference is one edge offset at each end. Two thirds
    of a metre does not sound like a difference worth a function until you
    notice that the whole legal band for a hop that climbs a block is only a
    metre wide -- so a plan that measures cells against a span measured in feet
    asks for steps the physics does not have, roughly one time in three.

    And the offset depends on which way the body is going, because a block is
    square and a radius is round: the feet plant against the block's *face*, so
    running into a corner they plant 1.41 times as far out as running into a
    side. Ignoring that is worth nearly half a metre on a diagonal, which is
    half the width of the band.
    """
    lo, hi = hop_span(rise)
    m = max(abs(dx), abs(dz)) or 1.0
    n = math.hypot(dx, dz) or 1.0
    pad = (EDGE.get(from_form, 0.34) + EDGE.get(to_form, 0.34)) / (m / n)
    return lo + pad, hi + pad


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
        #: How far along the current platform's lane the crossing has got, and
        #: how many landings it has laid. Both are state rather than a list of
        #: planned nodes on purpose -- see :meth:`_cross_node`.
        self._lane_i = 0
        self._cross_n = 0

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
        """The next node, and the next node only.

        Everything here is decided from ``self.blocks[-1]`` -- where the body
        actually is -- rather than from where an earlier plan assumed it would
        be. That is the single structural rule of this file and it was learned
        twice, once on each half of the course: a plan laid several nodes
        deep is a chain in which the first landing that comes down a cell to
        one side or a block low makes every node after it ask for a step the
        physics does not have.
        """
        if self.stage == "cross":
            pad = self.tower.pad(self.pad_i)
            node = self._cross_node(pad)
            if node is not None:
                self.segment = "cave" if pad.enclosed else "cross"
                self._pending = [node]
                return
            self.stage = "bridge"
            self.bridge = self._roll_bridge()
            self.stone = 0
        prev = self.blocks[-1]
        there = self.tower.pad(self.pad_i + 1)
        target = there.enter
        self.segment = self.bridge
        # The landing is a hop like any other, so what decides that the bridge
        # is *finished* is the same question placement will ask: is the rim
        # cell a step this body can make from here? Against a fixed radius it
        # is not -- the old "within 4.4 m" fired on stones two metres from the
        # rim, which is under ``MIN_HOP``, and the landing was then refused for
        # being too close rather than too far.
        rise = target[1] + 1.0 - (prev["y"] + FORMS[prev["form"]])
        lo, hi = _band(prev["form"], "floor", rise,
                       target[0] - prev["x"], target[2] - prev["z"])
        flat = math.dist((prev["x"], prev["z"]), (target[0], target[2]))
        need = target[1] - prev["y"]
        # ...and it steps *across* onto the platform, never up into it. A
        # landing hop that still has to climb comes in under the rim, and a
        # platform's ground is two cells deep -- so the body's head crosses the
        # lower of those two on the way in and the arc is refused for hitting
        # the thing it is landing on. The bridge climbs to the platform's own
        # height first, beside it, and then walks in: that one condition took
        # the unchecked answer from 0.68% of nodes to 0.25%, and it is also
        # exactly what a player does.
        if (lo <= flat <= hi and need <= 0) or self.stone > 30:
            land = self._node(style=there.theme.floor, form="floor",
                              spread=1, cell=target, orbs=1, label=self.bridge)
            # A doorway is a cell wide and a platform is twenty-five. The way
            # in is where the *route* wants to arrive, not the only ground
            # there is, and a landing with no alternative was the last group of
            # failures left: a third of them, every one a perfectly ordinary
            # arrival refused because something the bridge could not see was
            # standing beside that one cell.
            land["alts"] = tuple(self._rim_alts(there, target, prev))
            self._pending = [land]
            self.pad_i += 1
            self.stage = "cross"
            self._lane_i = 0
            self._cross_n = 0
            return
        self.stone += 1
        # Every legal cell, best first, rather than one cell and an argument.
        # Placement has to answer questions the plan cannot see -- what a
        # column driven down from a landing twenty blocks further on is
        # standing in, whether the body can run across the block it is leaving
        # -- and a plan that offers one answer turns each of those into a
        # failure. Offering the runners-up costs a list and takes the same
        # checks; it is the difference between 2.2% of nodes unchecked and
        # 0.3%.
        stairs = self._beside(prev, there, target, need)
        runs = self._run_cells(prev, there, target)
        cands = (stairs + runs) if (need > 0 or flat < lo) else (runs + stairs)
        if not cands:
            # Nothing legal anywhere: hand placement the honest thing it was
            # asked for and let it count the miss, rather than inventing a cell
            # that only looks like an answer.
            ux, uz = _out(there, target)
            cands = [(target[0] + _round(ux * 4), prev["y"] + 1,
                      target[2] + _round(uz * 4))]
        node = self._bridge_node(self.bridge, there.theme, self.stone,
                                 cands[0], self.rng)
        node["alts"] = tuple(cands[1:12])
        self._pending = [node]

    def _rim_alts(self, there: Pad, target, prev: dict) -> list:
        """Other ground on the far platform a bridge could arrive on.

        Only the platform's own top cells, only ones a body can stand on, and
        only ones the hop from here is one the physics has -- so an alternative
        landing is a landing, not a relaxation.
        """
        out = []
        surface = prev["y"] + FORMS[prev["form"]]
        for cell in _near(target, 2)[1:]:
            if cell not in self.solid or not self._standable(cell):
                continue
            dx, dz = cell[0] - prev["x"], cell[2] - prev["z"]
            lo, hi = _band(prev["form"], "floor",
                           cell[1] + 1.0 - surface, dx, dz)
            if lo <= math.hypot(dx, dz) <= hi:
                out.append(cell)
        return out

    def _run_cells(self, prev: dict, there: Pad, target) -> list:
        """A stone further along the bridge: nearer, and a block higher.

        Aimed at a point a few cells *outside* the rim, not at the rim cell
        itself. A bridge that heads straight for its landing spends its last
        two or three stones inside the platform it is aiming at -- the cells
        are that platform's own ground, so they are occupied, and the stone is
        refused. Approaching from outside and stepping up onto the rim is both
        placeable and what it should look like.

        Walked out along the line until the *cell* is a real hop away, not
        placed at a distance and rounded. Rounding a 2.8 m step onto the
        lattice can land it 1.4 m out, which is under ``MIN_HOP`` -- and the
        next stone is then measured from a body that never moved.
        """
        ux, uz = _out(there, target)
        aim = (target[0] + _round(ux * 3), target[1], target[2] + _round(uz * 3))
        span = math.dist((prev["x"], prev["z"]), (aim[0], aim[2]))
        if span < 1e-3:
            return []              # already there; this is the stairs' job
        ux, uz = (aim[0] - prev["x"]) / span, (aim[2] - prev["z"]) / span
        y = prev["y"]
        if y < target[1]:
            y += 1
        elif y > target[1] + 1:
            y -= 1
        rise = y + 1.0 - (prev["y"] + FORMS[prev["form"]])
        # A fan of whole cells, not the points along one line rounded.
        #
        # The band a hop that climbs a block may cover is about 1.1 m wide, and
        # cells along a *diagonal* are 1.41 m apart: walk out along a
        # north-easterly line and the distances go 2.83, 4.24, and the whole
        # legal band falls down the gap between them. Nothing is wrong with
        # either number and there is no answer on that line at all -- while one
        # cell to either side of it there are two. Measured: that gap alone was
        # 13 of the last 23 nodes the scene could not place, every one of them
        # on the first or second stone of a bridge leaving on a diagonal.
        out = []
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                if dx == 0 and dz == 0:
                    continue
                d = math.hypot(dx, dz)
                lo, hi = _band(prev["form"], "full", rise, dx, dz)
                if not (lo <= d <= hi):
                    continue
                # Straightest first, then longest: a bridge that wanders is a
                # bridge that arrives under its platform without the height.
                cos = (dx * ux + dz * uz) / d
                if cos < 0.55:
                    continue
                out.append((-cos, -d, (prev["x"] + dx, y, prev["z"] + dz)))
        out.sort()
        return [c for _, _, c in out]

    def _beside(self, prev: dict, there: Pad, target, need: int) -> list:
        """Steps up the flight of stairs beside the rim, nearest the rim first.

        This is the case the whole scene used to fall over on. A bridge has to
        gain the entire rise of a platform -- five to nine blocks -- across
        about nine stones, and one jump impulse reaches 1.25; on the seeds
        where the rise is at the top of its range and the platforms happen to
        sit close together, the bridge arrives *under* the platform with three
        or four blocks still to climb. From there the direction "toward the
        landing" is made of rounding error, the step comes out as no step at
        all, and every stone after it is laid on top of the last. Measured with
        a counter round ``_attempt``: that one geometry was 3% of every node in
        the scene and the single largest cause of placement failing.

        So when the course is under its landing and low, it stops stepping
        *toward* it and circles it instead: a ring of cells a few out from the
        rim, each a real hop from the last and each a block higher. The cells
        it may not use are the ones already spoken for -- and that is what
        makes the flight turn rather than bounce between two stones, because
        coming back to a column two blocks up lands in the head-room reserved
        over it, so the third step is forced somewhere new.

        What it reads as is a corkscrew of steps up the outside of a platform,
        which is what a spiral map builds at exactly this moment and for
        exactly this reason.
        """
        if math.dist((prev["x"], prev["z"]),
                     (target[0], target[2])) > BESIDE_R + 4.0:
            return []
        y = prev["y"] + (1 if need > 0 else 0)
        ux, uz = _out(there, target)
        tx, tz = -uz, ux
        rise = y + 1.0 - (prev["y"] + FORMS[prev["form"]])
        found = {}
        for along in range(-5, 6):
            for out in BESIDE_RINGS:
                cx = target[0] + _round(ux * out + tx * along)
                cz = target[2] + _round(uz * out + tz * along)
                if there.holds(cx, cz):
                    continue
                dx, dz = cx - prev["x"], cz - prev["z"]
                lo, hi = _band(prev["form"], "full", rise, dx, dz)
                if not (lo <= math.hypot(dx, dz) <= hi):
                    continue
                if (cx, y, cz) in self.solid or (cx, y, cz) in self.headroom:
                    continue
                # Nearest the landing first, so the flight stays beside the rim
                # instead of wandering off round the drop.
                found[(cx, y, cz)] = math.hypot(cx - target[0],
                                                cz - target[2])
        return [c for c, _ in sorted(found.items(), key=lambda kv: kv[1])]

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

    def _cross_node(self, pad: Pad) -> "dict | None":
        """The next landing on this platform, or ``None`` when it is crossed.

        Landings are on the ground itself -- ``floor`` nodes, which place no
        block and stand on what the spiral already built -- so a crossing is
        the body running over real terrain rather than over a line of cubes
        somebody floated there. Not every cell: a course that lands on every
        cell is a walk, so each landing is a genuine hop from the last.

        One at a time, measured from the block the body is actually on. The
        whole crossing used to be chosen in advance from ``pad.enter``, which
        is where the *arrival* was supposed to land -- and an arrival that came
        down a cell to one side, or a block low because its own last hop was
        refused, turns the first hop of the crossing into one the physics does
        not have. Measured with a counter round ``_attempt``, that alone was
        58% of every placement failure in this scene: the largest single cause,
        and invisible from the crossing's own code, because nothing there was
        wrong.

        The style carried on each landing is the platform's own floor material,
        which is what makes an ice platform slide and a soul-sand one drag:
        ``ground_speed`` reads it, and that one number is most of what makes a
        theme feel like what it is made of.
        """
        rng = self.rng
        prev = self.blocks[-1]
        lane = pad.lane
        end = len(lane) - 1
        if self._lane_i >= end:
            return None
        px, pz = prev["x"], prev["z"]
        surface = prev["y"] + FORMS[prev["form"]]
        # Where the body *is* on the lane, not where the last node aimed it.
        # Placement is free to take one of the alternatives below, and a
        # crossing that kept counting from its own first choice would then
        # offer the body a cell it has already run past.
        here = min(range(len(lane)),
                   key=lambda i: math.hypot(lane[i][0] - px, lane[i][2] - pz))
        self._lane_i = max(self._lane_i, here)
        if self._lane_i >= end:
            return None

        floor_y = pad.y - 1

        def form_at(cell) -> str:
            # Above the platform's own ground, a landing has to *build* -- the
            # lane climbs to a way out that is one to three blocks up, and a
            # ``floor`` landing needs the cell it names to be solid already.
            return "floor" if cell[1] <= floor_y else "full"

        def reach(cell, form):
            dx, dz = cell[0] - px, cell[2] - pz
            lo, hi = _band(prev["form"], form,
                           cell[1] + FORMS[form] - surface, dx, dz)
            return lo, hi, math.hypot(dx, dz)

        # The best next landing is not the first legal one but the one nearest
        # a comfortable hop. A crossing made of the shortest legal steps is a
        # shuffle, and one made of the longest leaves no margin at all for an
        # arrival that came in short.
        # Room to stand is a *preference*, not a requirement, and the
        # difference is a whole class of failure. On a terrace the cells beside
        # a step are the ones the body overhangs, and there are stretches of
        # lane where every cell within a hop is one of them -- so a filter
        # leaves the crossing with no candidate at all and it falls back on the
        # far rim, twenty metres away. Ranked instead, the awkward cell is
        # tried after the comfortable ones and before the answer nobody
        # checked.
        ranked = []
        for i in range(self._lane_i + 1, end + 1):
            lo, hi, d = reach(lane[i], form_at(lane[i]))
            if lo <= d <= hi:
                ranked.append((0 if self._standable(lane[i]) else 1,
                               abs(d - 3.2), i))
        ranked.sort()
        best = ranked[0] if ranked else None
        if best is None:
            self._lane_i = end
            lo, _, d = reach(lane[end], form_at(lane[end]))
            if d < lo:
                return None    # already at the far rim; the bridge starts here
            i = end
        else:
            i = best[-1]
        self._lane_i = i
        self._cross_n += 1
        cell = lane[i]
        # The steps up to the way out. The lane climbs ``pad.lift`` blocks
        # before it reaches the rim, and above the ground those landings are
        # *built* -- a short flight of blocks on a plinth, which is what a
        # parkour map puts on a platform anyway.
        #
        # Built rather than terraced, and that is the whole of the reasoning.
        # Raising the platform's own ground under the lane was tried first and
        # it is the more obvious idea: it gives the same climb and it looks
        # like terrain. What it also gives is a step at shoulder height beside
        # every landing next to it, and an arc that clips the step it is
        # climbing -- emergency placements went from 0.2% of blocks to 5%, and
        # they are unfixable from the crossing's side because the offending
        # geometry is the *building*. Placed as blocks, every one of them goes
        # through the same four checks as a bridge stone and cannot be laid at
        # all unless the body can make it.
        above = cell[1] - floor_y
        if above > 0:
            node = self._node(style=pad.theme.accent, form="full", spread=0,
                              cell=cell, support=above,
                              support_style=pad.theme.wall,
                              orbs=1 if rng.random() < 0.55 else 0,
                              label="cave" if pad.enclosed else "cross")
            node["alts"] = tuple(lane[r[-1]] for r in ranked[1:6])
            return node
        # A feature every so often: a block on the ground to hop up onto, which
        # on a farm is a hay bale and in a cave is a fallen rock. It is the same
        # node either way -- what changes is the material. Only where the hop
        # onto it is one a body has, which is a narrower band than the flat hop
        # it replaces.
        # ...and never within two cells of the rim. Standing a block higher
        # puts the body's shoulders level with a cave's wall rather than under
        # it, and one cell of clearance is not one cell of clearance to a body
        # 0.6 m wide standing 0.4 m off centre.
        lift = 0
        inner = max(abs(cell[0] - pad.cx), abs(cell[2] - pad.cz)) <= pad.half - 2
        if i < end and inner and rng.random() < 0.30:
            lo, hi, d = reach((cell[0], cell[1] + 1, cell[2]), "full")
            lift = 1 if lo <= d <= hi else 0
        node = self._node(
            style=pad.theme.accent if lift else pad.theme.floor,
            form="full" if lift else "floor", spread=0 if lift else 1,
            cell=(cell[0], cell[1] + lift, cell[2]),
            deco="lantern" if pad.enclosed and self._cross_n % 3 == 1 else None,
            orbs=1 if rng.random() < 0.55 else 0,
            label="cave" if pad.enclosed else "cross")
        # The other lane cells that are also a hop away, in case this one is
        # standing under something the crossing cannot see -- a column driven
        # down from the platform above, most often.
        if not lift:
            node["alts"] = tuple(self._lane_alts(pad, lane, ranked))
        return node

    def _standable(self, cell) -> bool:
        """Is this piece of ground clear of anything a *shoulder* would hit?

        The landing's own head-room says nothing about the cell next door, and
        a body is 0.6 m wide standing 0.4 m off the middle of the block along
        the way it is going -- so on a terrace it overhangs the step in front
        of it every time. That is not a hop being refused, it is a run across a
        block being refused, which reads as the course inexplicably declining
        perfectly ordinary flat ground. It was 87 of the 148 failures the
        terraces introduced.
        """
        cx, cy, cz = cell
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                if ox == oz == 0:
                    continue
                for h in (1, 2):
                    if (cx + ox, cy + h, cz + oz) in self.solid:
                        return False
        return True

    def _lane_alts(self, pad: Pad, lane, ranked) -> list:
        """Other ground a crossing could land on: further along the lane, and
        a cell either side of it.

        The lane is one cell wide and a platform is eleven to fifteen, so
        insisting on the middle of it turns any single obstruction -- a column
        driven down from the platform above, most often -- into a node nothing
        can place. A step to one side is the same ground, and it stops a
        crossing reading as a painted line.
        """
        out = []
        for r in ranked[1:6]:
            out.append(lane[r[-1]])
        fx, fz = _toward(lane[0], lane[-1])
        rx, rz = -fz, fx
        for r in ranked[:4]:
            cell = lane[r[-1]]
            for side in (1, -1):
                aside = (cell[0] + rx * side, cell[1], cell[2] + rz * side)
                if aside in self.solid and aside not in out:
                    out.append(aside)
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
            # A viaduct: piers under every other stone, and a rail along the
            # whole of it. Deliberately *not* the head-hitting lintel the ring
            # version hangs over a jump, and this is the one place where the
            # shape of the format forbids a set-piece outright. A bridge here
            # climbs a block a stone in a straight line, and a lintel is hung
            # at a fixed height above the arc it spans -- so a beam that the
            # hop it belongs to passes cleanly under is sitting exactly where
            # the body's head will be three stones later. Measured: arches were
            # 12.6% of their own nodes stuck against 2.3% without the lintel,
            # five times every other style in the table.
            return self._node(style=candy, deco="rail",
                              support=rng.randint(4, 10) if i % 2 else 0,
                              support_style=theme.wall, **common)
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
        # No half-height landings out here, and this is arithmetic rather than
        # taste. A slab's walking surface is half a block above its own cell,
        # so a body standing on one is off the lattice every later step is
        # planned against: the ordinary climb of one cell becomes a rise of
        # 1.5, and ``hop_span``'s discriminant has no solution at 1.5 -- here
        # or in the game. Measured, that alone was a quarter of what was left
        # unchecked. Slabs belong where the course is not obliged to climb.
        return self._node(style=candy,
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
        alts = node.get("alts") or ()
        for cell in _near(node["cell"], node["spread"]):
            got = self._attempt(prev, node, cell)
            if got is not None:
                return got
        # The plan's runners-up, before anything is relaxed. A second cell the
        # plan itself vouched for beats the first cell with a rule switched
        # off, every time.
        for cell in alts:
            got = self._attempt(prev, node, cell)
            if got is not None:
                return got
        # Then the same stone with its costume off. A web, a ladder or a bounce
        # is chosen by the *style* after the plan has already picked a cell for
        # an ordinary hop, and each of those has its own physics -- a web is
        # only crossable between 1.4 and 3.6 m, a ladder wants a post it can
        # hang on. When the costume is what fails, an ordinary stone in the
        # same place is a better answer than an unchecked one somewhere else.
        if node["kind"] != "hop" or node["form"] != "full":
            plain = dict(node, form="full", kind="hop", deco=None, support=0,
                         support_style=None)
            for cell in (node["cell"],) + tuple(alts):
                got = self._attempt(prev, plain, cell)
                if got is not None:
                    return got
        for cell in _near(node["cell"], node["spread"]):
            got = self._attempt(prev, node, cell, strict=False)
            if got is not None:
                return got
        for cell in alts:
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

    def _attempt(self, prev: dict, node: dict, cell, strict: bool = True,
                 loose: bool = False):
        """Everything the ring version checks, plus: not in a flight already
        promised.

        ``pathcells`` is the corridor a solved move flies through, and the ring
        version consults it only when the *building* wants to grow -- a course
        that keeps moving forward is never going to lay a block where it has
        already agreed to fly. This one does, every time it climbs: the flight
        of steps beside a rim comes back over the same three cells a block
        higher each time, so the stone three ahead is built in the arc that
        reaches the stone one ahead. The arc was checked when it was solved and
        the stone did not exist yet; nothing later asks.

        Measured before this check: the body was inside a course block on 3.2%
        of frames, and every single one of them was a block two, three or four
        ahead of the one it was standing on.
        """
        if node["form"] != "floor" and any(
                c in self.pathcells for c in _footprint(*cell, node["form"])):
            return None
        return super()._attempt(prev, node, cell, strict=strict, loose=loose)

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
