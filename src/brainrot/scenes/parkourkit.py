"""The parkour kernel: physics, moves, the lattice, and what a body fits in.

Everything in this module is true of *any* course this project builds and
knows the shape of no building. It is Minecraft's own motion -- gravity, the
one jump impulse, sprint speed, ladders, bubble columns, slime, ice, soul sand,
cobweb -- expressed as a single type (:class:`Move`, a list of legs) so that
the generator, the simulation, the orb solver and the probes all read the same
answer from the same arithmetic. There is no raylib import here and there never
should be: a sixty-run geometry sweep costs a few seconds and no window.

It was extracted unchanged from the ring-tower plan module that used to live
beside it, because it is the part of that file that measured clean -- zero
interpenetration, zero orbs laid but not collected -- and the part that had
nothing to do with the building whose shape turned out to be wrong. That
building is gone; this is what was worth keeping.

The one convention everything below depends on: **a cell's ``y`` is its floor,
its ``x`` and ``z`` are its centre.** A block at ``y`` is stood on at ``y + 1``.
"""

from __future__ import annotations

import math


#: 0.08 b/t^2 with vanilla's 0.98 per-tick drag, which is what makes a jump
#: apex at 1.25 blocks rather than the 1.1 the undamped figure gives.
GRAVITY = 28.0
#: 0.42 b/t. The only jump impulse the game has, and the reason nothing can
#: step up two blocks unaided.
JUMP_V = 8.4
#: Sprint, 0.2806 b/t.
RUN_SPEED = 5.612
#: Sprint-jump: the forward impulse on the tick you jump is why a four-block
#: gap is clearable at all. Horizontal speed is constant for a whole flight.
AIR_SPEED = 7.10
#: Vanilla walk, 0.21585 b/t.
WALK_SPEED = 4.317

#: Ladders and vines: 0.1176 b/t up (0.12 with vanilla's drag on it), and a
#: floor of 0.15 b/t coming down. Slow, and it *should* feel slow -- a ladder
#: is the game's way of trading time for height, and one that climbs at running
#: pace is a lift.
CLIMB_SPEED = 2.35
CLIMB_DOWN = 3.00
#: Scaffolding. Neither wiki documents a figure for this, so it climbs like a
#: ladder here and is labelled one in the probe, rather than being given an
#: invented constant that would get quoted back as vanilla later.
SCAFFOLD_SPEED = CLIMB_SPEED
#: Riding a soul-sand bubble column, which in Java is about eleven blocks a
#: second -- twice sprinting, and by a distance the fastest way up anything in
#: the game. Not a number worth softening: arriving eight blocks higher in
#: three quarters of a second is the whole reason a map builds one.
BUBBLE_SPEED = 11.0
#: Soul sand: 0.4x horizontal, cumulative per block touched, walking at about
#: two and a half blocks a second. This is the tower's slow beat, and
#: everything either side of it reads faster for it.
SOUL_SPEED = 2.51
#: Cobweb, and the one place this file knowingly leaves the game behind.
#: Vanilla divides horizontal movement by four: a sprint through a web is
#: 0.64 m/s, so two metres of web is three seconds. The overlay is on screen
#: for as long as Claude is thinking -- often fifteen seconds -- and it cannot
#: spend a fifth of that in one web. Webs here are short and crossed at a
#: little under walking pace: still unmistakably a web, still the slowest thing
#: in the scene by a factor of three, and stated here rather than passed off.
WEB_SPEED = 1.20
#: Packed ice, slipperiness 0.98 against an ordinary block's 0.6. What that
#: buys is *carried momentum*, not a longer arc: the flight time of a jump is
#: fixed by its height tier, so a jump off ice goes further only because the
#: body is moving faster when it leaves. A long blue-ice run reaches over
#: 17 m/s in the game; a few blocks of it reaches these.
ICE_RUN = 8.50
ICE_AIR = 10.00

#: A slime bounce inverts vertical velocity exactly -- vanilla's restitution is
#: 1.0 -- and the per-tick drag then takes a little off on the way back up, so
#: a bounce returns you to a bit under the height you fell from.
#:
#: Which is worth being blunt about, because the obvious design is wrong: slime
#: is **not** a way to gain height. Holding jump through a bounce *cancels* it
#: and gives an ordinary jump instead, so there is no way to add the impulse on
#: top and no way to chain upward. What slime is for is spending a drop
#: somewhere else -- you fall down a shaft and come back up the far side of it
#: -- and that is what ``_seg_slimeshaft`` builds.
BOUNCE_KEEP = 0.96
BOUNCE_MAX = 24.0

#: A hop is legal exactly when the take-off it needs is one a body has.
VY_MIN = 1.6
VY_MAX = JUMP_V
#: Hang-time bounds for an ordinary hop, derived from the above rather than
#: chosen.
AIR_MIN, AIR_MAX = 0.12, 1.45
#: Shortest hop the generator will lay, take-off point to landing point.
#: Anything under this is a shuffle rather than a jump, and a run of shuffles
#: is the single most common way generated parkour reads as fake.
MIN_HOP = 2.0

#: Vanilla's own collision volume, and the head-room a landing needs in whole
#: cells for a 1.8 m body to stand in.
BODY_HALF_W = 0.30
BODY_H = 1.80
HEADROOM = 2
EYE = 1.62
#: Where on the body an orb is aimed, so passing through one cannot miss it.
CHEST = 0.90

#: form -> height of the walking surface above the block's own base.
#: ``floor`` is the odd one: a landing that places no block at all and stands
#: on architecture that is already there. It is how the course gets onto the
#: tower's own galleries, and without it a checkpoint would have to build a
#: platform on top of the balcony it is meant to be arriving on.
#: ``fence`` and ``wall`` stand **one and a half** high, which is the real
#: map's signature obstacle: a body cannot jump onto one from the ground
#: beside it (the rise is past the 1.25 a jump has), so it must be arrived
#: at from height -- the checker enforces that for free, exactly as it
#: refuses any other impossible rise. ``trapdoor`` is a plate lying almost
#: flat on its cell.
FORMS = {"full": 1.0, "slab": 0.5, "wide": 1.0, "stair": 1.0, "ice": 1.0,
         "slime": 1.0, "web": 1.0, "floor": 1.0,
         "fence": 1.5, "wall": 1.5, "trapdoor": 0.2}
#: form -> how far from a block's centre the feet plant, along the direction of
#: travel. You land on the near edge and leave from the far one, which is what
#: a run-up is and why the gap a body clears is wider than the gap between two
#: block centres.
#:
#: ``wide`` is 1.05 and not 1.5, and the missing 0.45 is the body. A three-wide
#: platform reaches 1.5 m along an axis, so feet planted at 1.3 put a 0.6 m
#: body's leading edge at 1.6 -- in the cell *beyond* the platform, every time,
#: on every take-off. Out over a void that is invisible; on a tower it is a
#: shoulder inside whatever the platform is bolted to, and it was the deepest
#: single class of contact the probe found.
EDGE = {"full": 0.34, "slab": 0.34, "stair": 0.34, "ice": 0.34,
        "slime": 0.34, "web": 0.34, "wide": 1.05, "floor": 0.40,
        # A fence post's top is a sliver: the feet plant dead centre, and a
        # wall's cap is barely wider. The trapdoor is a full plate.
        "fence": 0.05, "wall": 0.08, "trapdoor": 0.34}
#: Half-footprint of a form, in cells.
SPREAD = {"wide": 1}
#: Forms a move may launch from with more than the jump impulse.
SPRINGY = frozenset(("slime",))

#: How many points a path is sampled at when it is checked against the world.
#: The body is 0.6 m wide and the longest move is a little over seven, so
#: seventeen samples put consecutive tests about 0.2 m apart -- inside the body
#: rather than beside it, which is what stops a shoulder slipping through a
#: buttress between two samples.
ARC_SAMPLES = 17


# ---------------------------------------------------------------------------
# Moves
# ---------------------------------------------------------------------------

class Move:
    """How a body gets from one landing to the next, as a list of legs.

    A leg is either a straight line covered at a constant speed or a ballistic
    arc, and every move in the vocabulary is one or more of those: a hop is one
    arc, a ladder is a step in, a rise and a step off, a bubble column is the
    same with a different speed, a web is a slow line. Making them one type is
    what keeps the simulation to a single loop and the probe to a single
    measurement -- and it is what makes adding the *next* move a table entry
    rather than another branch in a state machine.

    ``kind`` is only ever used for choosing an animation, a sound the scene
    does not have, or a probe bucket. Nothing about the motion reads it.
    """

    __slots__ = ("kind", "legs", "dur", "frm", "to")

    def __init__(self, kind: str, legs: list[dict]) -> None:
        self.kind = kind
        self.legs = legs
        self.dur = sum(leg["dur"] for leg in legs)
        self.frm = legs[0]["frm"]
        self.to = legs[-1]["to"]

    def at(self, t: float) -> tuple[float, float, float]:
        """Where the body is ``t`` seconds into the move."""
        for leg in self.legs:
            if t <= leg["dur"] or leg is self.legs[-1]:
                return _leg_at(leg, min(t, leg["dur"]))
            t -= leg["dur"]
        return self.to

    def points(self, samples: int = ARC_SAMPLES) -> list[tuple[float, float, float]]:
        """The path, sampled evenly in time. What everything checks against."""
        if self.dur <= 0.0:
            return [self.frm, self.to]
        return [self.at(self.dur * i / samples) for i in range(samples + 1)]

    def rise(self) -> float:
        return self.to[1] - self.frm[1]

    def speed_in(self) -> float:
        """Ground speed the body enters this move at."""
        return _leg_speed(self.legs[0])

    def speed_out(self) -> float:
        """Ground speed the body leaves this move at.

        Which is the number the block *after* the move needs: the run across a
        landing has to start at whatever speed arrived on it, or the body
        changes pace in the one frame it touches down.
        """
        return _leg_speed(self.legs[-1])


def _leg_speed(leg: dict) -> float:
    frm, to = leg["frm"], leg["to"]
    return math.dist((frm[0], frm[2]), (to[0], to[2])) / max(1e-6, leg["dur"])


def _leg_at(leg: dict, t: float) -> tuple[float, float, float]:
    frm, to = leg["frm"], leg["to"]
    dur = leg["dur"] or 1e-6
    f = t / dur
    x = frm[0] + (to[0] - frm[0]) * f
    z = frm[2] + (to[2] - frm[2]) * f
    if leg["kind"] == "arc":
        y = frm[1] + leg["vy0"] * t - 0.5 * GRAVITY * t * t
    else:
        y = frm[1] + (to[1] - frm[1]) * f
    return (x, y, z)


def line_leg(frm, to, speed: float) -> dict:
    """A straight leg at a constant speed, through all three axes.

    Length is the full 3-D distance and not the ground distance, which matters
    for exactly one thing and matters a lot for it: a ladder is *only* vertical,
    so a ground-distance leg would take no time at all and the body would
    teleport up it.
    """
    dist = math.dist(frm, to)
    return {"kind": "line", "frm": tuple(frm), "to": tuple(to),
            "dur": max(1e-4, dist / speed), "vy0": 0.0}


def arc_leg(frm, to, speed: float = AIR_SPEED) -> dict:
    """A ballistic leg: constant horizontal speed, gravity doing the rest.

    This is the flat scene's ``flight()`` and the reasoning is unchanged.
    Horizontal speed is constant, so the time a hop takes is how far it goes
    divided by how fast a body sprints, and the take-off velocity is then
    whatever lands you on the far end. Solving for a duration instead and
    clamping it -- which is what this project did once -- makes the horizontal
    speed different on every hop, and the short ones visibly float.
    """
    dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
    dur = max(1e-4, dist / speed)
    vy0 = (to[1] - frm[1]) / dur + 0.5 * GRAVITY * dur
    return {"kind": "arc", "frm": tuple(frm), "to": tuple(to), "dur": dur,
            "vy0": vy0}


def hop_move(frm, to, speed: float = AIR_SPEED, kind: str = "hop") -> Move:
    return Move(kind, [arc_leg(frm, to, speed)])


def hop_span(rise: float, speed: float = AIR_SPEED,
             vy_max: float = VY_MAX) -> tuple[float, float]:
    """Shortest and longest hop a body can make for a change in height.

    Both ends fall out of one jump impulse and one constant horizontal speed,
    and neither is a number anybody chose:

    * **Longest** is the full jump: the descending root of
      ``rise = vy*t - g t^2/2``, at sprint speed. Level that is 4.3 m; dropping
      buys more, because falling takes longer and the body does not slow down
      while it does. Rising two blocks has no solution, here or in the game.
    * **Shortest** stops for different reasons in the two directions. A climb
      has to be past its apex when it arrives, or the body has come up through
      the *side* of the block rather than onto it. A drop has to leave the
      ground properly rather than be tipped off it, which is what ``VY_MIN``
      is.
    """
    if rise >= 0:
        lo = speed * math.sqrt(2.0 * rise / GRAVITY)
    else:
        lo = speed * (VY_MIN + math.sqrt(VY_MIN * VY_MIN
                                         - 2.0 * GRAVITY * rise)) / GRAVITY
    disc = vy_max * vy_max - 2.0 * GRAVITY * rise
    hi = 0.0 if disc < 0.0 else speed * (vy_max + math.sqrt(disc)) / GRAVITY
    return max(MIN_HOP, lo), hi


def fit_gap(gap: int, rise: float, speed: float = AIR_SPEED) -> int:
    """Widen a gap until the hop across it is one a body can make.

    A drop is the case that matters: falling takes time, the body keeps its
    speed all the way down, so a hop that descends four blocks covers close to
    four metres of ground whether the set-piece wanted it to or not. Ask for a
    two-block gap under a four-block drop and the only way to deliver it is to
    throw the player at the floor.
    """
    lo, hi = hop_span(rise, speed)
    if hi <= 0.0:
        return max(1, gap)
    for g in range(max(1, gap), 10):
        span = g + 1 - 2 * EDGE["full"]
        if lo - 1e-6 <= span <= hi + 1e-6:
            return g
    return max(1, gap)


def bounce_launch(impact: float) -> float:
    """How fast a slime pad throws you back, given how fast you hit it.

    Restitution is 1.0 and drag takes the rest, so this is a little under what
    arrived and a bounce can never reach higher than the fall that fed it. The
    cap is there because a generator with an unbounded launch velocity will
    happily throw the camera a hundred blocks up the shaft on the one seed
    where a set-piece drops further than it meant to.
    """
    return min(BOUNCE_MAX, abs(impact) * BOUNCE_KEEP)


def fall_speed(drop: float) -> float:
    """Impact speed after falling ``drop`` metres from rest."""
    return math.sqrt(max(0.0, 2.0 * GRAVITY * drop))


# ---------------------------------------------------------------------------
# The run across a landing
# ---------------------------------------------------------------------------
#
# What used to happen between two flights was a constant: the body arrived at
# the arc's speed, was set to the material's walking speed for the length of
# the block, and then set back. Both of those are one-frame steps of about a
# metre and a half a second, twice per landing, at four landings a second --
# and a step in speed is a thing the eye reads as a *stop* however short it is.
# The owner's report was that the body "clicks into something and sticks to
# whatever block he's on" before jumping again, which is exactly what a square
# wave in the speed looks like from inside the head.
#
# So the crossing is a velocity profile now, and it is the ordinary one: brake
# as hard as the ground allows, cruise at the material's own speed if there is
# any room left to, and accelerate back up in time to leave at the speed the
# next move needs. On a one-cell landing -- 0.68 m, which is most of them --
# there is no room, so the body barely slows: it *runs over* the block, which
# is what a player chaining jumps does and what nothing in this project's
# motion could previously express.
#
# The two ends are exact by construction. ``speed_at(0)`` is the speed the
# body arrived with and ``speed_at(length)`` is the speed the next move
# begins at, so there is no step at either boundary for any material, any
# block length or any move -- including a ladder, which the body now decelerates
# into rather than snapping to a stop at.

#: How hard a body may brake on the ground, and how hard it may accelerate.
#: Vanilla's ground friction is fierce and its sprint acceleration is not, and
#: the asymmetry is what makes a wide platform read as a breather: the body
#: sheds speed onto it quickly and has to work to get it back.
GROUND_DECEL = 42.0
GROUND_ACCEL = 26.0
#: Below this a "run" is a stall, whatever the material says.
CRAWL = 0.45


class GroundRun:
    """A braking-cruising-accelerating crossing of one landing.

    ``speed_at`` is the standard trapezoid: the pointwise minimum of what the
    body can still be doing having braked from ``v_in``, and what it can be
    doing and still reach ``v_out`` by the far edge -- floored by the second
    constraint, so a short block whose next move is fast never dips to the
    material speed at all, because it physically cannot.
    """

    __slots__ = ("length", "v_in", "v_out", "cruise", "decel", "accel", "dur")

    def __init__(self, length: float, v_in: float, v_out: float,
                 cruise: float, decel: float = GROUND_DECEL,
                 accel: float = GROUND_ACCEL) -> None:
        self.length = max(0.0, length)
        self.v_in = max(CRAWL, v_in)
        self.v_out = max(CRAWL, v_out)
        self.cruise = max(CRAWL, cruise)
        self.decel = decel
        self.accel = accel
        self.dur = self._integrate()

    def speed_at(self, s: float) -> float:
        s = min(max(0.0, s), self.length)
        v_in, v_out, cruise = self.v_in, self.v_out, self.cruise
        # What the body is doing having tried to reach the cruise speed from
        # the near edge.
        if v_in >= cruise:
            want = math.sqrt(max(cruise * cruise, v_in * v_in
                                 - 2.0 * self.decel * s))
        else:
            want = min(cruise, math.sqrt(v_in * v_in + 2.0 * self.accel * s))
        back = self.length - s
        # ...capped by what it could brake from and still be this fast, and
        # floored by what it has to be doing to reach ``v_out`` in time.
        ceil = math.sqrt(v_out * v_out + 2.0 * self.decel * back)
        floor = math.sqrt(max(0.0, v_out * v_out - 2.0 * self.accel * back))
        return max(floor, min(want, ceil), CRAWL)

    def _integrate(self) -> float:
        """How long the crossing takes: ``ds / v(s)``, by trapezoid.

        Numerically, because the closed form has three cases and two of them
        have sub-cases, and this is called once per landing.
        """
        if self.length <= 1e-9:
            return 0.0
        n = 16
        h = self.length / n
        total = 0.0
        prev = 1.0 / self.speed_at(0.0)
        for i in range(1, n + 1):
            cur = 1.0 / self.speed_at(h * i)
            total += (prev + cur) * 0.5 * h
            prev = cur
        return total


# ---------------------------------------------------------------------------
# Lattice helpers
# ---------------------------------------------------------------------------

def wrap_angle(a: float) -> float:
    """An angle folded into -pi..pi."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def iround(v: float) -> int:
    return int(math.floor(v + 0.5))


def ifloor(v: float) -> int:
    return int(math.floor(v))


def unit(dx: float, dz: float) -> tuple[float, float]:
    length = math.hypot(dx, dz) or 1.0
    return dx / length, dz / length


def _edge_offset(form: str, ux: float, uz: float) -> tuple[float, float]:
    """Where the feet plant, measured against a block's *face*.

    A block is square and a radius is round: a three-wide platform reaches
    1.5 m along an axis and 2.1 m into its corner, so a flat radius takes off
    with a metre of platform still ahead of it when the course runs diagonally
    -- and the arc starts falling immediately, so the camera dips through the
    platform's own outer cube.
    """
    m = max(abs(ux), abs(uz)) or 1.0
    e = EDGE[form] / m
    return ux * e, uz * e


def land_point(x: float, surface: float, z: float, form: str,
               in_dir: tuple[float, float]) -> tuple[float, float, float]:
    """Where the feet touch down: the near edge, on the way in."""
    ox, oz = _edge_offset(form, *unit(*in_dir))
    return (x - ox, surface, z - oz)


def takeoff_point(x: float, surface: float, z: float, form: str,
                  out_dir: tuple[float, float]) -> tuple[float, float, float]:
    """Where the feet leave: the far edge, on the way out."""
    ox, oz = _edge_offset(form, *unit(*out_dir))
    return (x + ox, surface, z + oz)


def quantise(dx: float, dz: float) -> tuple[int, int]:
    """A direction as one of the eight lattice steps.

    Decoration offsets are rotated into this rather than into the exact float
    heading the course happens to be running at, which is what keeps a window
    jamb in a whole cell instead of three-fifths of the way into one.
    """
    if abs(dx) < 1e-9 and abs(dz) < 1e-9:
        return (0, -1)
    a = math.atan2(dx, -dz)
    k = int(round(a / (math.pi / 4))) % 8
    return ((0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1))[k]


def body_cells(x: float, y: float, z: float):
    """Cells a body with its feet at ``(x, y, z)`` touches.

    Deliberately generous at the edges: a body is 0.6 wide, so on the lattice
    it straddles two cells whenever it is not dead centre, and a corridor test
    blind to the cell a shoulder is in clears arcs that visibly graze walls.
    """
    floor = math.floor
    x0 = int(floor(x - BODY_HALF_W + 0.5))
    x1 = int(floor(x + BODY_HALF_W + 0.5))
    z0 = int(floor(z - BODY_HALF_W + 0.5))
    z1 = int(floor(z + BODY_HALF_W + 0.5))
    # Hoisted and de-duplicated on purpose. This is the hottest function in the
    # module by a wide margin -- placement asks it for every sample of every
    # candidate path -- and the naive form recomputed both roundings inside the
    # height loop and yielded the same cell four times whenever the body sat
    # near the middle of one.
    xs = (x0,) if x0 == x1 else (x0, x1)
    zs = (z0,) if z0 == z1 else (z0, z1)
    for cy in range(int(floor(y + 0.05)), int(floor(y + BODY_H - 0.05)) + 1):
        for cx in xs:
            for cz in zs:
                yield (cx, cy, cz)

# ---------------------------------------------------------------------------
# Materials and themes
# ---------------------------------------------------------------------------
#
# The material list is here rather than in the scene because the *generator* is
# what decides that a nether ring is netherrack and a mine is deepslate, and a
# theme whose materials live somewhere else is a theme in two files. The scene
# turns each entry into a texture; nothing here imports a renderer.
#
# ``see_through`` materials are drawn but never block: glass, water, a ladder,
# a cobweb, a vine. They are the reason the occupancy map and the *drawn* world
# are two different collections -- a ladder you cannot climb through is not a
# ladder, and a course that refuses to be laid past a window pane is a course
# that will not fit inside its own building.

#: name -> (base colour, texel pattern, colour noise)
#:
#: Note how few entries use the near-flat ``concrete`` pattern. A material
#: with no grain in it is fine for a jump block with sky around it and wrong
#: for a *wall*: forty cubes meeting edge to edge with nothing to separate
#: them read as one extruded surface. Anything a ring is built out of has
#: courses, seams or stones in it.
MATERIALS: dict[str, tuple[tuple[int, int, int], str, float]] = {
    # -- the keep
    "stonebrick": ((136, 136, 142), "stonebrick", 0.02),
    "cobble": ((128, 128, 134), "cobble", 0.03),
    "stone": ((146, 146, 150), "stonebrick", 0.02),
    "mossy": ((104, 122, 96), "cobble", 0.04),
    "andesite": ((150, 150, 148), "speck", 0.02),
    # -- timber
    "oak": ((166, 132, 78), "planks", 0.02),
    "darkoak": ((104, 74, 44), "planks", 0.02),
    "spruce": ((114, 84, 50), "planks", 0.02),
    "log": ((124, 98, 58), "grain", 0.03),
    # -- the mine
    "deepslate": ((92, 92, 100), "stonebrick", 0.02),
    "tuff": ((108, 108, 102), "cobble", 0.03),
    "coalore": ((120, 120, 124), "speck", 0.03),
    "goldore": ((168, 154, 108), "speck", 0.03),
    "rail": ((150, 132, 96), "grain", 0.02),
    # -- overgrown
    "leaves": ((72, 148, 62), "leaves", 0.04),
    "vine": ((80, 140, 66), "leaves", 0.05),
    "moss": ((92, 138, 74), "dirt", 0.04),
    "dirt": ((122, 92, 62), "dirt", 0.03),
    # -- desert
    "sandstone": ((222, 208, 150), "sand", 0.02),
    "chiselled": ((214, 198, 140), "stonebrick", 0.02),
    "terracotta": ((172, 106, 74), "bricks", 0.03),
    # -- nether
    "netherrack": ((116, 54, 54), "dirt", 0.04),
    "netherbrick": ((84, 44, 52), "bricks", 0.02),
    "magma": ((214, 118, 52), "speck", 0.05),
    "soulsand": ((98, 76, 62), "dirt", 0.04),
    "blackstone": ((70, 64, 74), "cobble", 0.03),
    # -- ice
    "packedice": ((156, 192, 232), "grain", 0.02),
    "blueice": ((116, 164, 228), "grain", 0.02),
    "snow": ((238, 244, 250), "sand", 0.02),
    "frost": ((186, 210, 232), "stonebrick", 0.02),
    # -- the laboratory
    "slime": ((128, 200, 108), "leaves", 0.03),
    "honey": ((232, 172, 60), "grain", 0.03),
    "copper": ((188, 120, 88), "bricks", 0.02),
    # -- the deep
    "prismarine": ((92, 152, 146), "stonebrick", 0.03),
    "darkprismarine": ((62, 108, 102), "stonebrick", 0.02),
    "sealantern": ((198, 226, 216), "lantern", 0.02),
    # -- the end
    "purpur": ((166, 128, 172), "stonebrick", 0.02),
    "endstone": ((216, 214, 156), "speck", 0.03),
    "obsidian": ((56, 46, 78), "stonebrick", 0.02),
    # -- the summit
    "quartz": ((228, 226, 218), "grain", 0.02),
    "gold": ((234, 198, 84), "stonebrick", 0.02),
    "glowstone": ((250, 214, 130), "lantern", 0.02),
    # -- furniture and fittings, shared by every theme
    "lantern": ((255, 212, 128), "lantern", 0.02),
    "torch": ((255, 198, 110), "lantern", 0.02),
    "ladder": ((158, 122, 70), "planks", 0.02),
    "scaffold": ((198, 168, 108), "planks", 0.02),
    "water": ((88, 132, 220), "grain", 0.03),
    "web": ((228, 232, 238), "leaves", 0.02),
    "glass": ((186, 220, 236), "grain", 0.02),
    "iron": ((188, 190, 196), "concrete", 0.02),
}

#: Materials a face is still drawn against, and which nothing collides with.
SEE_THROUGH = frozenset(("glass", "water", "web", "vine", "ladder", "leaves",
                         "scaffold", "rail"))

#: The three per-run course colours, filled in by the scene from the palette.
#: A tower dressed only in its own materials is a grey tower; the reference
#: maps all put brightly coloured jump blocks against a muted building, which
#: is also the only way the eye finds the next landing at a glance.
CANDY = ("candy0", "candy1", "candy2")


# ---------------------------------------------------------------------------
# Blocks, footprints and orbs
# ---------------------------------------------------------------------------

#: Where along a move a run of orbs sits. Never at the very ends, where an orb
#: is inside the block it was strung from.
ORB_FRACTIONS = {1: (0.5,), 2: (0.34, 0.66), 3: (0.26, 0.5, 0.74)}


def deco(dx: float, dy: float, dz: float, sx: float, sy: float, sz: float,
          style: str, glow: bool = False) -> dict:
    return {"dx": dx, "dy": dy, "dz": dz, "sx": sx, "sy": sy, "sz": sz,
            "style": style, "glow": glow, "solid": False}


def footprint(cx: int, cy: int, cz: int, form: str):
    """Every cell a landing of this form fills. A ``floor`` fills none: it
    stands on architecture that is already there."""
    if form == "floor":
        return ()
    sp = SPREAD.get(form, 0)
    if not sp:
        return ((cx, cy, cz),)
    return tuple((cx + ox, cy, cz + oz)
                 for ox in range(-sp, sp + 1) for oz in range(-sp, sp + 1))


def cells_of(blk: dict):
    """Every cell a block and its *solid* decoration occupy."""
    out = list(footprint(blk["x"], blk["y"], blk["z"], blk["form"]))
    for d in blk["deco"]:
        if d.get("solid"):
            out.append((blk["x"] + iround(d["dx"]), blk["y"] + iround(d["dy"]),
                        blk["z"] + iround(d["dz"])))
    return out


def standing_cells(blk: dict) -> set:
    """Cells the body is inside while standing on this block.

    Only a slab qualifies: its walking surface is halfway up its own cell, so
    the feet are inside it. Exempting a whole block wholesale -- which the flat
    scene did once -- makes the one check that would catch a hop leaving a wide
    platform too flat blind to it by construction.
    """
    if blk["form"] != "slab":
        return set()
    return set(footprint(blk["x"], blk["y"], blk["z"], blk["form"]))


def line_cells(frm, to) -> tuple:
    """Whole cells along a straight run, for filling a gap with cobweb."""
    steps = max(2, int(math.dist(frm, to) * 2) + 1)
    out: dict = {}
    for i in range(steps + 1):
        f = i / steps
        out[(iround(frm[0] + (to[0] - frm[0]) * f),
             ifloor(frm[1] + (to[1] - frm[1]) * f + 0.5),
             iround(frm[2] + (to[2] - frm[2]) * f))] = None
    return tuple(out)
