"""The tower: its architecture, its course, and how a body gets up it.

This module is the whole of the *tower parkour* format and none of its
rendering. It has no raylib import on purpose -- the geometry, the physics and
every guarantee the scene makes are testable in a plain interpreter with no
window, which is what makes a sweep of sixty runs a thing you can afford to run
after every change.

Why a second parkour scene at all
---------------------------------

``scenes/parkour.py`` is *infinite parkour*: a course of floating blocks that
runs away from you in a roughly straight line, high over an ocean. That is one
real reel format and it is the one those reels mostly are. The other one -- the
one the whole "parkour tower" / "Parkour Spiral" genre of Minecraft maps is
made of -- is not a variation on it. It is a different thing in four ways, and
each of them breaks something the flat scene relies on:

* **Progress is altitude.** The course winds round a fixed axis, so it comes
  back over itself every revolution. A generator that only ever asks "is the
  next block clear" against a course that never returns is not enough; this one
  is climbing through the space it was in twenty seconds ago.
* **There is a building.** Most of what you see is not the course. It is a
  wall, with windows and cornices and buttresses, and the course is furniture
  hung on it. That is thousands of static cells, which is why
  :mod:`brainrot.engine.chunk` exists.
* **Two blocks up is normal.** The flat scene cannot express a rise of two,
  because vanilla's one jump impulse cannot reach it -- and it does not need
  to, because it can always go along instead. A tower has nowhere else to go,
  so it has to have the moves the game has for going up: ladders, slime, a
  bubble column, a stairwell. That is a motion model with more than one verb in
  it.
* **Sections, not set-pieces.** A spiral map is read as a stack of *themed
  floors* -- the stone keep, the mine, the nether ring, the ice ring -- with a
  landing between them. The set-piece is still the unit of content, but which
  set-pieces exist at all changes with altitude.

The four things that carry the weight
-------------------------------------

**Everything is on an integer lattice, structure included.** The tower's cells
and the course's cells are the same cells, in one occupancy map, so a landing
can no more be inside a buttress than two landings can be inside each other.
The helix is computed in continuous polar coordinates and then *snapped*: a
course restricted to whole angles would look like a cog, and a course that was
never snapped would interpenetrate its own building.

**Every move is solved before it is laid.** A hop is checked against vanilla's
one jump impulse exactly as the flat scene checks it. A ladder is checked
against a column of cells that has to exist, be reachable, and be clear all the
way up. A bounce is checked against how fast the body will actually be moving
when it hits the slime. Nothing is placed that cannot then be done, and nothing
is checked after the fact -- rejection sampling inside a frame loop is how a
generator comes to stall on the one seed nobody tested.

**A move is a path, not a jump.** :class:`Move` is a list of legs with a speed
each, so a ladder, a swim up a bubble column, a run round a curved balcony and
a sprint-jump are the same kind of object to everything downstream. The flat
scene has two phases and hard-codes a parabola into both of them; adding a
ladder to it would mean a third phase, a fourth, and a state machine nobody can
hold in their head.

**The course knows its own path,** which is inherited wholesale from the flat
scene and is just as load-bearing here: where the feet land and leave is
decided when a block is generated, so the exact trajectory of every future move
is computable at generation time. That is what lets a beam be hung over a jump
it is guaranteed to miss, and orbs be strung on a path they are guaranteed to
be carried through.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Vanilla's numbers
# ---------------------------------------------------------------------------
#
# Minecraft is a 20 Hz simulation and every figure below is quoted in the
# game's own blocks-per-tick before being converted, because the point of
# copying them is that a viewer who has played the game recognises the motion
# without being able to say why. Where the flat scene already has a number,
# this module uses the same one: the two scenes are the same body.

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
FORMS = {"full": 1.0, "slab": 0.5, "wide": 1.0, "stair": 1.0, "ice": 1.0,
         "slime": 1.0, "web": 1.0, "floor": 1.0}
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
        "slime": 0.34, "web": 0.34, "wide": 1.05, "floor": 0.40}
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
# Lattice helpers
# ---------------------------------------------------------------------------

def _round(v: float) -> int:
    return int(math.floor(v + 0.5))


def _floor(v: float) -> int:
    return int(math.floor(v))


def _unit(dx: float, dz: float) -> tuple[float, float]:
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
    ox, oz = _edge_offset(form, *_unit(*in_dir))
    return (x - ox, surface, z - oz)


def takeoff_point(x: float, surface: float, z: float, form: str,
                  out_dir: tuple[float, float]) -> tuple[float, float, float]:
    """Where the feet leave: the far edge, on the way out."""
    ox, oz = _edge_offset(form, *_unit(*out_dir))
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
    for cy in range(_floor(y + 0.05), _floor(y + BODY_H - 0.05) + 1):
        for cx in (_round(x - BODY_HALF_W), _round(x + BODY_HALF_W)):
            for cz in (_round(z - BODY_HALF_W), _round(z + BODY_HALF_W)):
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
MATERIALS: dict[str, tuple[tuple[int, int, int], str, float]] = {
    # -- the keep
    "stonebrick": ((136, 136, 142), "stonebrick", 0.02),
    "cobble": ((128, 128, 134), "cobble", 0.03),
    "stone": ((146, 146, 150), "concrete", 0.02),
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
    "terracotta": ((172, 106, 74), "concrete", 0.03),
    # -- nether
    "netherrack": ((116, 54, 54), "dirt", 0.04),
    "netherbrick": ((84, 44, 52), "bricks", 0.02),
    "magma": ((214, 118, 52), "speck", 0.05),
    "soulsand": ((98, 76, 62), "dirt", 0.04),
    "blackstone": ((70, 64, 74), "cobble", 0.03),
    # -- ice
    "packedice": ((156, 192, 232), "grain", 0.02),
    "blueice": ((116, 164, 228), "grain", 0.02),
    "snow": ((238, 244, 250), "concrete", 0.02),
    "frost": ((186, 210, 232), "stonebrick", 0.02),
    # -- the laboratory
    "slime": ((128, 200, 108), "leaves", 0.03),
    "honey": ((232, 172, 60), "grain", 0.03),
    "copper": ((188, 120, 88), "concrete", 0.02),
    # -- the deep
    "prismarine": ((92, 152, 146), "stonebrick", 0.03),
    "darkprismarine": ((62, 108, 102), "concrete", 0.02),
    "sealantern": ((198, 226, 216), "lantern", 0.02),
    # -- the end
    "purpur": ((166, 128, 172), "stonebrick", 0.02),
    "endstone": ((216, 214, 156), "speck", 0.03),
    "obsidian": ((56, 46, 78), "concrete", 0.02),
    # -- the summit
    "quartz": ((228, 226, 218), "grain", 0.02),
    "gold": ((234, 198, 84), "concrete", 0.02),
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


class Theme:
    """One ring of the tower: what it is made of and what happens on it.

    Themes change **abruptly at a floor boundary** rather than blending, which
    is what makes a climb read as chaptered rather than as a gradient -- it is
    the one structural note every spiral map in the reference material agrees
    on, from Parkour Spiral's nether-to-jungle jumps to Biome Spiral's plains-
    to-End run.
    """

    __slots__ = ("name", "wall", "trim", "floor", "accent", "glow", "course",
                 "weights", "sky", "dark")

    def __init__(self, name: str, wall: str, trim: str, floor: str,
                 accent: str, glow: str, course: tuple[str, ...],
                 weights: dict[str, float], sky: tuple[int, int, int],
                 dark: float = 0.0) -> None:
        self.name = name
        self.wall = wall
        self.trim = trim
        self.floor = floor
        self.accent = accent
        self.glow = glow
        #: Materials the jump blocks of this ring are made of. Always a mix of
        #: the ring's own stone and the run's candy colours -- an all-candy ring
        #: has no architecture in it and an all-stone one has no course.
        self.course = course
        #: Multipliers on the shared set-piece table. A ring's signature move
        #: is the one it multiplies up; everything else stays available, so a
        #: ring is a change of emphasis rather than a different game.
        self.weights = weights
        #: How this ring tints the light around it, which is most of what makes
        #: an interior read as a different place from the ring below it.
        self.sky = sky
        #: 0 for a ring lit by the sky, 1 for one lit only by its own lamps.
        self.dark = dark


THEMES = (
    Theme("keep", "stonebrick", "cobble", "stone", "andesite", "torch",
          ("candy0", "candy1", "stonebrick"),
          {"stairs": 2.0, "corbel": 1.6, "rim": 1.4}, (176, 196, 220)),
    Theme("timber", "oak", "darkoak", "spruce", "log", "lantern",
          ("candy1", "oak", "candy2"),
          {"beams": 2.6, "ladderrun": 2.2, "balcony": 1.5}, (196, 186, 156)),
    Theme("mine", "deepslate", "tuff", "deepslate", "goldore", "torch",
          ("candy0", "coalore", "tuff"),
          {"interior": 3.0, "webwalk": 2.2, "pillars": 1.6}, (96, 92, 104), 0.72),
    Theme("overgrown", "mossy", "cobble", "moss", "leaves", "lantern",
          ("candy2", "moss", "candy0"),
          {"vinerun": 2.6, "pillars": 1.8, "corbel": 1.4}, (150, 190, 140)),
    Theme("desert", "sandstone", "chiselled", "sandstone", "terracotta",
          "lantern", ("candy1", "sandstone", "terracotta"),
          {"soulwalk": 2.4, "balcony": 1.8, "gap": 1.5}, (232, 206, 156)),
    Theme("nether", "netherbrick", "blackstone", "netherrack", "magma",
          "magma", ("candy0", "netherbrick", "magma"),
          {"gap": 2.2, "soulwalk": 2.0, "headhitter": 1.8}, (156, 62, 48), 0.55),
    Theme("ice", "packedice", "frost", "snow", "blueice", "lantern",
          ("candy2", "packedice", "snow"),
          {"iceline": 3.2, "gap": 1.8, "balcony": 1.4}, (188, 216, 244)),
    Theme("lab", "copper", "iron", "stone", "honey", "lantern",
          ("slime", "honey", "candy1"),
          {"slimeshaft": 3.4, "bubblelift": 1.8, "beams": 1.4}, (168, 176, 168)),
    Theme("deep", "prismarine", "darkprismarine", "prismarine", "sealantern",
          "sealantern", ("candy2", "prismarine", "sealantern"),
          {"bubblelift": 3.0, "plunge": 2.4, "interior": 1.4},
          (72, 132, 148), 0.35),
    Theme("end", "purpur", "endstone", "endstone", "obsidian", "lantern",
          ("candy0", "purpur", "endstone"),
          {"pillars": 2.4, "gap": 2.0, "headhitter": 1.6}, (44, 36, 62), 0.6),
    Theme("summit", "quartz", "gold", "quartz", "gold", "glowstone",
          ("candy1", "quartz", "gold"),
          {"balcony": 2.0, "stairs": 1.8, "corbel": 1.4}, (250, 226, 176)),
)
THEME_BY_NAME = {t.name: t for t in THEMES}


# ---------------------------------------------------------------------------
# The building
# ---------------------------------------------------------------------------

#: Blocks of height in one themed ring, and the number the whole scene is
#: paced by. It is arithmetic rather than taste, from both ends:
#:
#: A helix cannot climb faster than about a block a hop, because there is one
#: jump impulse and it reaches 1.25 blocks. At this radius a revolution is
#: around sixty-five metres of circumference and a hop covers a bit over three,
#: so a turn is about twenty hops -- and two published spiral maps independently
#: land on 0.64 blocks of rise per hop, which is twelve blocks a turn. A ring
#: of twelve is therefore *one revolution*, which is what makes the theme change
#: arrive at the same moment the view comes back round to where it started.
#:
#: It is also about sixteen seconds at this pace, which is the length of a
#: thinking turn. A ring the viewer never finishes is a ring they never see the
#: point of.
TIER_H = 12
#: Radius of the hole in the middle of every floor. The course falls through it
#: (``_seg_plunge``), you see daylight down it from the balconies, and it is
#: the reason the tower reads as a shaft rather than as a stack of discs.
OCULUS = 3
#: How far a balcony reaches out past the wall.
#:
#: Two, not three, and the reason is that a balcony is an *overhang*: nothing
#: can stand under it, because a landing needs two clear cells over it for a
#: body to be in. At three the gallery reached across the whole band the course
#: runs in, so the approach to every checkpoint had nowhere to put its feet and
#: fell through to the emergency hop -- which is exactly the failure this
#: project's flat scene documents as "a flight of stairs stacked vertically".
BALCONY_OUT = 2
#: Buttresses per ring, and how far they stand proud of the wall.
BUTTRESSES = 6
#: The wall radii a ring may have. Kept narrow -- the reference towers are
#: around ten to one, tall and thin, and a wide one stops reading as a tower at
#: all in a portrait strip.
RADII = (5, 6, 7, 8)


class Tower:
    """The architecture: wall, floors, balconies, buttresses, windows.

    Generated a *layer at a time* rather than a ring at a time, and that is a
    frame-budget decision rather than a tidiness one. One ring is about
    thirteen hundred cells, which is ten milliseconds of Python; one layer is
    eighty, which is under one. The scene asks for a few layers a frame and
    stays ahead of the course without ever dropping a frame to a floor being
    born.
    """

    def __init__(self, rng, base_y: int = 0) -> None:
        self.rng = rng
        self.base = base_y
        self.built_to = base_y
        self._radius: dict[int, int] = {}
        self._theme: dict[int, Theme] = {}
        self._windows: dict[int, list[tuple[int, int]]] = {}
        self._bag: list[Theme] = []

    # -- what a ring is ----------------------------------------------------

    def tier_of(self, y: float) -> int:
        return int(math.floor((y - self.base) / TIER_H))

    def tier_base(self, tier: int) -> int:
        return self.base + tier * TIER_H

    def radius(self, tier: int) -> int:
        got = self._radius.get(tier)
        if got is None:
            if tier - 1 in self._radius:
                prev = self._radius[tier - 1]
                # At most one block in or out per ring: a tower that jumps two
                # has a step in its silhouette that no cornice can cover, and
                # the course crossing that boundary has to make a lateral move
                # it was never asked for.
                choices = [r for r in RADII if abs(r - prev) <= 1]
                got = self.rng.choice(choices)
            else:
                got = self.rng.choice(RADII)
            self._radius[tier] = got
        return got

    def theme(self, tier: int) -> Theme:
        got = self._theme.get(tier)
        if got is None:
            if not self._bag:
                # A shuffled bag rather than a weighted roll: a roll repeats,
                # and two nether rings in a row is the one thing a stack of
                # themed floors must never do. Refilled when it empties, minus
                # whatever was last used, so the seam between bags is clean.
                self._bag = list(THEMES)
                self.rng.shuffle(self._bag)
                last = self._theme.get(tier - 1)
                if last is not None and self._bag[0] is last and len(self._bag) > 1:
                    self._bag[0], self._bag[1] = self._bag[1], self._bag[0]
            got = self._bag.pop(0)
            self._theme[tier] = got
        return got

    def theme_at(self, y: float) -> Theme:
        return self.theme(self.tier_of(y))

    def radius_at(self, y: float) -> int:
        return self.radius(self.tier_of(y))

    def windows(self, tier: int) -> list[tuple[int, int]]:
        """``(angle_step, height_offset)`` of each opening in a ring.

        Angles are in whole sixteenths of a turn so two windows cannot end up
        one cell apart, which at this radius is a wall with a slot in it rather
        than a wall with windows in it.
        """
        got = self._windows.get(tier)
        if got is None:
            rng = self.rng
            slots = rng.sample(range(16), rng.randint(3, 5))
            got = [(s, rng.choice((2, 3, 4, 8, 9, 10))) for s in slots]
            self._windows[tier] = got
        return got

    # -- generation --------------------------------------------------------

    def build_to(self, y_top: int, place) -> int:
        """Lay every layer up to ``y_top``. Returns how many layers it built.

        ``place(cell, style)`` is the caller's -- the tower does not own an
        occupancy map or a renderer, which is what lets the same generator feed
        a probe that only counts cells and a scene that meshes them.
        """
        built = 0
        while self.built_to < y_top:
            self._layer(self.built_to, place)
            self.built_to += 1
            built += 1
        return built

    def _layer(self, y: int, place) -> None:
        tier = self.tier_of(y)
        theme = self.theme(tier)
        radius = self.radius(tier)
        base = self.tier_base(tier)
        local = y - base
        openings = self._openings(tier, radius)

        # -- the wall. One cell thick: from outside that is a wall, from
        # inside that is a wall, and anything thicker is cells nobody sees.
        for x, z in _ring_cells(radius):
            if (x, z, local) in openings:
                continue
            place((x, y, z), theme.wall)
        # A course of trim at the top and bottom of each ring, which is what
        # stops a sixteen-block wall reading as one extruded shape.
        if local in (0, TIER_H - 1):
            for x, z in _ring_cells(radius):
                if (x, z, local) not in openings:
                    place((x, y, z), theme.trim)

        if local == 0:
            self._floor(y, tier, theme, radius, place)
        # Buttresses stand proud of the wall and flare where they meet the ring
        # above, which is the cheapest thing that makes a cylinder read as a
        # building. They start two blocks up, *above* the gallery: a rib
        # running down through a balcony is one that takes the head-room out of
        # the cells the course has to stand in to get onto it, and 6 ribs x 2
        # cells of flare is a quarter of a gallery closed off.
        if local >= 2:
            flare = 1 if local >= TIER_H - 2 else 0
            for k in range(BUTTRESSES):
                a = (k + 0.5 * tier) * (2 * math.pi / BUTTRESSES)
                for out in range(1, 2 + flare):
                    place((_round(math.cos(a) * (radius + out)), y,
                           _round(math.sin(a) * (radius + out))), theme.trim)

    def _floor(self, y: int, tier: int, theme: Theme, radius: int, place) -> None:
        """The slab a ring stands on: interior floor, oculus, balcony, cornice.

        Drawn one block *below* the ring's first wall layer so that its top
        surface is the floor level -- which is also the height the course's
        checkpoint set-piece lands on, so the two agree without either knowing
        about the other.
        """
        below = self.radius(tier - 1) if tier - 1 in self._radius else radius
        reach = max(radius, below) + BALCONY_OUT
        for x, z in _disc_cells(reach):
            d2 = x * x + z * z
            if d2 <= OCULUS * OCULUS:
                continue                      # the hole down the middle
            if d2 < radius * radius:
                place((x, y - 1, z), theme.floor)
            else:
                # The balcony, and the cornice under it. A ledge that just
                # stops has no shadow line; one with a lip under it reads as
                # masonry from thirty metres away, which is the only distance
                # anybody sees it from.
                place((x, y - 1, z), theme.trim)
                if d2 <= (radius + 1) ** 2:
                    place((x, y - 2, z), theme.trim)

    def _openings(self, tier: int, radius: int) -> set[tuple[int, int, int]]:
        """The cells a ring's windows take out of its wall."""
        out: set[tuple[int, int, int]] = set()
        for slot, height in self.windows(tier):
            a = slot * (2 * math.pi / 16)
            for da in (-0.5, 0.0, 0.5):
                x = _round(math.cos(a + da / radius) * radius)
                z = _round(math.sin(a + da / radius) * radius)
                for dy in range(3):
                    out.add((x, z, height + dy))
        return out


_RING_CACHE: dict[int, tuple[tuple[int, int], ...]] = {}


def _ring_cells(radius: int) -> tuple[tuple[int, int], ...]:
    """Every cell of a one-thick circle of this radius, once each.

    Walked by angle rather than by scanning the square, because a scan has to
    decide what ``round(hypot) == r`` means at the diagonals and gets a ring
    with gaps in it; stepping the angle finely enough that consecutive samples
    land in adjacent cells cannot leave one out.
    """
    got = _RING_CACHE.get(radius)
    if got is None:
        cells: dict[tuple[int, int], None] = {}
        steps = max(48, int(radius * 12))
        for i in range(steps):
            a = i * (2 * math.pi / steps)
            cells[(_round(math.cos(a) * radius), _round(math.sin(a) * radius))] = None
        got = tuple(cells)
        _RING_CACHE[radius] = got
    return got


_DISC_CACHE: dict[int, tuple[tuple[int, int], ...]] = {}


def _disc_cells(radius: int) -> tuple[tuple[int, int], ...]:
    got = _DISC_CACHE.get(radius)
    if got is None:
        got = tuple((x, z)
                    for x in range(-radius, radius + 1)
                    for z in range(-radius, radius + 1)
                    if x * x + z * z <= radius * radius)
        _DISC_CACHE[radius] = got
    return got


# ---------------------------------------------------------------------------
# The course
# ---------------------------------------------------------------------------

#: How far outside the wall the jump blocks hang, and the band they may wander
#: in. Close enough that the wall is a handrail you can see against, far enough
#: that a buttress does not eat every second landing.
COURSE_OUT = 3.6
COURSE_MIN, COURSE_MAX = 2.6, 5.4
#: Blocks laid before a run is at full difficulty. About eighty hops, which at
#: this pace is a little under a minute -- inside the length of a turn the
#: overlay is actually on screen for.
RAMP_BLOCKS = 80
#: How far ahead of the body the course is generated, and how much is kept
#: behind it. Larger than the flat scene's, because a tower is *seen* from
#: further away: the ring above you is in shot for its whole length.
AHEAD = 16
TRAIL = 3
#: Which ring a run starts on, and how much tower is built underneath it.
#:
#: Not the ground floor. A tower whose base is six blocks below the camera is a
#: chimney; what makes the first frame read as "high up a very tall building" is
#: that the wall already runs down out of the shot into the haze. Fifty-two is
#: what the scene draws before fog takes over, so building more would be cells
#: nobody ever sees.
START_TIER = 3
BUILD_BELOW = 52

#: Running pace across a block, by what the block is made of. Vanilla walking
#: speeds: soul sand slows you to 2.5, slime to 1.36, ice carries you at 8.5.
#: This is the cheapest characterisation in the scene -- one number and a ring
#: made of soul sand *feels* like a ring made of soul sand.
SURFACE_SPEED = {
    "soulsand": SOUL_SPEED,
    "slime": 1.36,
    "honey": 2.10,
    "packedice": ICE_RUN,
    "blueice": ICE_RUN,
    "web": WEB_SPEED,
}

#: The shared set-piece vocabulary and its base weights. A theme multiplies
#: these (see :attr:`Theme.weights`), so every ring can still produce every
#: set-piece and a ring is a change of emphasis rather than a different game.
#: That distinction is from the reference material: what makes spiral maps
#: repetitive is not too few block types, it is too few *shapes*.
SEGMENTS = {
    "rim": 22.0,
    "corbel": 12.0,
    "stairs": 9.0,
    "balcony": 7.0,
    "pillars": 9.0,
    "beams": 7.0,
    "ladderrun": 7.0,
    "bubblelift": 5.0,
    "slimeshaft": 4.0,
    "iceline": 5.0,
    "webwalk": 4.0,
    "soulwalk": 4.0,
    "gap": 6.0,
    "headhitter": 6.0,
}
#: How the difficulty ramp reweights it. The reference is explicit that a
#: course should escalate by *mechanic class* rather than by gap width -- and
#: equally explicit that five hard sections in a row is what makes people quit,
#: which is why nothing here is multiplied to zero.
SEGMENT_RAMP = {
    "gap": 2.0, "headhitter": 1.8, "pillars": 1.2, "slimeshaft": 1.2,
    "rim": -0.5, "balcony": -0.6, "corbel": -0.35, "stairs": -0.3,
}
#: Set-pieces that must not follow themselves.
NO_REPEAT = frozenset(SEGMENTS) - {"rim"}
#: Which set-pieces gain height and which spend it. A tower is the one format
#: where "went down a bit" is not a variation but a failure -- the whole
#: premise is the climb -- so whenever the course has slipped below the highest
#: point it reached, these two sets are what pull it back.
CLIMBERS = frozenset(("stairs", "ladderrun", "bubblelift", "corbel"))
FALLERS = frozenset(("gap", "slimeshaft"))
#: Blocks of altitude the course is expected to gain per block laid, and how
#: far it may fall behind that before the choice of set-piece -- and then the
#: rises themselves -- are fully committed to climbing again.
#:
#: Measured against a *target* rather than against the highest point reached,
#: and that distinction is the whole mechanism. Against a high-water mark the
#: course climbs until it beats its own record, relaxes, spends the gain on the
#: next descending set-piece, and climbs back to the same mark: it oscillates
#: around a ceiling instead of rising through it. One run in eight gained seven
#: centimetres a second over forty-five seconds that way -- a spiral tower that
#: does not go up.
CLIMB_TARGET = 0.45
SLIP = 3.5


class Course:
    """The parkour: nodes, moves, occupancy, and the ramp.

    Owns one occupancy map covering *both* the building and the course, which
    is the whole reason a landing cannot end up inside a buttress. The tower
    writes into it through :meth:`_place_struct`; every course block and every
    solid decoration writes into it too.
    """

    def __init__(self, rng, tower: Tower, hop_rng=None) -> None:
        self.rng = rng
        self.hop_rng = hop_rng or rng
        self.tower = tower
        #: cell -> style for everything the *building* is made of. Handed to
        #: the renderer as a stream of writes so the scene can mesh it.
        self.struct: dict[tuple[int, int, int], str] = {}
        self.writes: list[tuple[tuple[int, int, int], str]] = []
        #: Every cell a body cannot pass through. Structure plus course.
        self.solid: set[tuple[int, int, int]] = set()
        #: The two cells over every live landing. Head-room is *checked* when a
        #: block is placed and that is not enough on its own: a spiral comes
        #: back over itself, so a later block can be laid in the space an
        #: earlier one was given to stand in, and the body then spends its whole
        #: run across that block with its head inside a cube. Reserving it is
        #: the fix; measured, that one case was three quarters of a metre deep
        #: and the deepest contact in the scene.
        self.headroom: set[tuple[int, int, int]] = set()
        #: Every cell the body will pass through on a move that has already
        #: been solved. Reserved for the same reason head-room is: the arc is
        #: checked against the world *at the moment it is laid*, and the
        #: building keeps being built afterwards -- a post driven down from a
        #: landing twenty blocks further on will happily go through a jump
        #: nobody is going to re-check.
        self.pathcells: set[tuple[int, int, int]] = set()
        #: Cells a ladder, a bubble column or a clump of cobweb is using.
        #: Never solid -- a ladder you cannot climb through is not a ladder --
        #: but reserved all the same, because a wall built through one later is
        #: a ladder buried in masonry.
        self.softcells: set[tuple[int, int, int]] = set()
        self.blocks: list[dict] = []
        self._pending: list[dict] = []
        self.segment = ""
        self.laid = 0
        self.stuck = 0
        #: Orbs that fell off the back of the course without being taken. The
        #: generation tests hold this at zero: every orb is hung *on* a path the
        #: body is about to be carried through, so a miss is a bug in the path
        #: rather than a near-miss by a player.
        self.orbs_missed = 0
        #: Tier boundaries already answered with a checkpoint, so one cannot be
        #: scheduled twice by a segment that happens to straddle it.
        self._checked: set[int] = set()
        self.wind = 1 if rng.random() < 0.5 else -1
        #: The highest the course has reached. A tower run that has slipped
        #: below it is a run going the wrong way, and :attr:`climb_pressure` is
        #: what notices.
        self.high = 0
        #: Where the course *should* be by now. See :data:`CLIMB_TARGET`.
        self.expected = 0.0

        # Start six blocks under a floor, so the first checkpoint -- the loudest
        # thing this scene does -- arrives inside the first ten seconds. The
        # runner scene learned the same lesson about its train roofs: on a strip
        # that is on screen for one thinking turn, a feature that appears at the
        # median is a feature most viewers never see.
        start_y = tower.base + START_TIER * TIER_H - 6
        tower.built_to = max(tower.base, start_y - BUILD_BELOW)
        self.tower.build_to(start_y + 12, self._place_struct)
        angle = rng.uniform(0, 2 * math.pi)
        self.high = start_y
        self.expected = float(start_y)
        # The opening platform is the one landing nothing chose, so it is the
        # one landing nothing checked: pushed outward until its own cells and
        # the two over each of them are clear. Skipping this put the very first
        # block of a run under a cornice, and the body then spent its first
        # three seconds with its head in the masonry.
        base = tower.radius_at(start_y)
        for out in (COURSE_OUT, COURSE_OUT + 1, COURSE_OUT + 2, COURSE_OUT + 3):
            radius = base + out
            cx = _round(math.cos(angle) * radius)
            cz = _round(math.sin(angle) * radius)
            cells = _footprint(cx, start_y, cz, "wide")
            if self._free(cells) and self._free(
                    (x, y + h, z) for x, y, z in cells
                    for h in range(1, HEADROOM + 1)):
                break
        first = self._block(cx, start_y, cz,
                            style="stone", form="wide",
                            step=(self.wind * -_round(math.sin(angle)) or 1,
                                  self.wind * _round(math.cos(angle))),
                            segment="start")
        self.blocks.append(first)
        self.solid.update(_cells_of(first))
        self.headroom.update((x, y + h, z)
                             for x, y, z in _footprint(cx, start_y, cz, "wide")
                             for h in range(1, HEADROOM + 1))
        while len(self.blocks) < AHEAD:
            self.spawn()

    # -- bookkeeping -------------------------------------------------------

    def _place_struct(self, cell, style: str) -> None:
        # The building is generated a long way ahead of the course and keeps
        # going after a ladder has been hung on it, so a later floor can be
        # laid straight through a column the course is already using. The
        # ladder wins: it is load-bearing and the wall is scenery.
        if cell in self.softcells or cell in self.pathcells:
            return
        self.struct[cell] = style
        self.writes.append((cell, style))
        if style not in SEE_THROUGH:
            self.solid.add(cell)

    @property
    def climb_pressure(self) -> float:
        """0 while the course is at its own high point, 1 once it has slipped.

        Every other format in this project can wander. This one cannot: a
        spiral that spends twenty seconds coming back down is not a harder
        tower, it is a broken one, and the descending set-pieces are exactly
        the ones that can produce it by accident -- a chasm that drops two and
        a slime shaft that spends four is a net loss of six that the rim has to
        win back a block at a time.
        """
        return min(1.0, max(0.0,
                            (self.expected - self.blocks[-1]["y"]) / SLIP))

    @property
    def difficulty(self) -> float:
        """0 at the start of a run, 1 once it has been climbing a while.

        Counted in blocks laid rather than metres climbed, for the same two
        reasons the flat scene counts them that way: generation runs sixteen
        blocks ahead of the body, and the probes grow a course without ever
        moving one.
        """
        return min(1.0, self.laid / RAMP_BLOCKS)

    def _block(self, x: int, y: int, z: int, style: str, form: str,
               step: tuple[int, int], segment: str, theme: str = "",
               born: float = -1e9) -> dict:
        return {"x": x, "y": y, "z": z, "style": style, "form": form,
                "step": step, "out": None, "segment": segment,
                "theme": theme or self.tower.theme_at(y).name,
                "yaw": math.atan2(step[0], -step[1]), "born": born,
                "laid": self.laid,
                "deco": [], "soft": [], "orbs": [], "move": None,
                "path": (), "unchecked": False, "impact": 0.0}

    def surface(self, blk: dict) -> float:
        return blk["y"] + FORMS[blk["form"]]

    def land_point(self, blk: dict):
        return land_point(blk["x"], self.surface(blk), blk["z"], blk["form"],
                          blk["step"])

    def takeoff_point(self, blk: dict):
        return takeoff_point(blk["x"], self.surface(blk), blk["z"],
                             blk["form"], blk["out"] or blk["step"])

    def ground_speed(self, blk: dict) -> float:
        return SURFACE_SPEED.get(blk["style"], RUN_SPEED)

    def angle_of(self, blk: dict) -> float:
        return math.atan2(blk["z"], blk["x"])

    def radius_of(self, blk: dict) -> float:
        return math.hypot(blk["x"], blk["z"])

    # -- laying a block ----------------------------------------------------

    def spawn(self) -> dict:
        """Lay the next block down. Never fails, and counts it when it nearly
        does -- ``stuck`` is held at zero by the generation tests, because the
        emergency answer is the only unchecked hop in the whole module."""
        if not self._pending:
            self._plan_segment()
        prev = self.blocks[-1]
        node = self._next_node(prev)
        self.laid += 1
        # Keep the building ahead of the course, and by enough that a landing
        # is never chosen against a wall that has not been built yet -- which
        # would put the course inside the next ring the moment it appeared.
        self.tower.build_to(prev["y"] + 24, self._place_struct)

        got = self._try_node(prev, node) or self._last_resort(prev)
        if got is None:
            self.stuck += 1
            got = self._emergency(prev, node)
            # Labelled, so that a probe or a test can tell an unchecked hop
            # from a checked one instead of quietly averaging the two together.
            node = dict(node, label="stuck")
        return self._commit(prev, node, got)

    def _next_node(self, prev: dict) -> dict:
        """Take the next node, resolving anything that depends on where the
        body actually got to.

        A set-piece expands into nodes *before* any of them is placed, so it
        can only ask for changes in height -- and placement is allowed to fall
        back through neighbouring rises, so a run of "climb one" nodes does not
        reliably arrive one-per-block. Anything that has to land at a specific
        altitude -- the gallery a checkpoint stands on, which is a solid ring at
        a known height -- says so with ``to_y`` and is answered here, a block at
        a time, against where the body is now. Planning the approach in advance
        instead is how the arrival ended up one block out and every candidate
        got rejected for asking the physics to rise two.
        """
        node = self._pending[0]
        if self.climb_pressure > 0.35 and node.get("to_y") is None \
                and node["kind"] in ("hop", "slide", "walk"):
            # Behind schedule, so nothing goes down. Reweighting the set-piece
            # table is not enough on its own: a rim is still two thirds flat,
            # and a course that only ever declines to descend takes a very long
            # time to make up five blocks.
            # Highest first, and never above one: rising two blocks in a hop
            # has no solution, so offering it only wastes the first candidate
            # sweep. Ordering matters as much as flooring -- placement takes
            # the first rise that fits, so a list that starts at zero climbs
            # nothing while technically declining to descend.
            floored = sorted({min(1, max(0, r)) for r in node["rises"]},
                             reverse=True)
            node = dict(node, rises=floored, rise=floored[0])
            self._pending[0] = node
        target = node.get("to_y")
        if target is None:
            return self._pending.pop(0)
        if node["form"] == "floor" and node["kind"] == "walk" \
                and prev["form"] != "floor":
            # The gallery was never reached, so there is nothing to walk along.
            self._pending.pop(0)
            return self._next_node(prev) if self._pending else \
                self._node(style=self.tower.theme_at(prev["y"]).course[0])
        need = target - prev["y"]
        # Level with the gallery, not one under it. A hop that *climbs* onto a
        # balcony has its feet in the balcony's own row of cells for the first
        # half of the arc, so it is refused for flying through the thing it is
        # aiming at -- correctly, and the answer is to arrive from beside it
        # rather than from below it.
        if need > 0 and node["form"] == "floor":
            theme = self.tower.theme_at(prev["y"])
            # Three cells out from the wall, which is one clear of the gallery
            # overhang and no further. Both halves of that matter: inside the
            # overhang there is no head-room to stand in, and out at the far
            # edge of the band the step back in to land on the balcony is
            # longer than a hop that also climbs a block can reach.
            # Clear of the gallery's skirt by a block and a bit, worked out
            # from the gallery rather than guessed at: the ring above may be
            # wider than the one the approach is climbing past, and a fixed
            # "three cells out from the wall" measured against the wrong one of
            # the two is a landing the overhang rule then refuses.
            wall = self.tower.radius_at(prev["y"] + 2)
            out = max(3.0, self.gallery_outer(target + 1) + 1.3 - wall)
            return self._node(style=theme.course[self.laid % len(theme.course)],
                              gap=self._gap(self.rng, (2, 2, 3), (2, 3, 3)),
                              rise=1, radius=out, spread=1, orbs=1,
                              label="approach")
        self._pending.pop(0)
        return dict(node, rise=need, rises=[need])

    def _try_node(self, prev: dict, node: dict):
        got = self._place(prev, node)
        if got is not None:
            return got
        # Nothing fitted where the set-piece wanted it. Rather than give up on
        # the whole node, give up on its *shape*: a step further out over the
        # void has strictly more empty cells in it than one tucked against a
        # wall full of buttresses, and one block wider always has more places
        # to land. Both are visible as a slightly odd hop; the alternative is
        # the unchecked emergency answer, which is visible as a broken course.
        relaxed = dict(node, radial=node["radial"] + 1.4, gap=node["gap"] + 1)
        if node["radius"] is not None:
            relaxed["radius"] = node["radius"] + 1.0
        got = self._place(prev, relaxed)
        if got is not None:
            return got
        # Last resort before the unchecked one: forget the set-piece entirely
        # and lay a plain block out over the void, which is where the empty
        # cells are. It is a hop like any other and every guarantee still
        # holds; all that is lost is the shape of one node. That is a trade
        # worth making every time, because the alternative below it is the
        # only move in the module nobody has checked.
        theme = self.tower.theme_at(prev["y"])
        style = theme.course[self.laid % len(theme.course)]
        # Swept in *absolute* distance from the wall rather than as a nudge,
        # and deliberately past the band the course normally keeps to. By the
        # time it gets here the body is usually already outside that band --
        # which is how it got boxed in -- and a nudge that is then clamped back
        # into the band only ever offers cells further into the trouble.
        for rise in (0, -4, -8):
            # And if going along will not do it, go *down*. A drop always has
            # more room in it than a step: falling takes time, the body keeps
            # its speed the whole way, so a descent reaches further and lands
            # in a part of the tower nothing has been built in yet. It costs
            # the run some altitude and it is never the shape anybody asked
            # for, which is why it is the last thing tried and not the first.
            for radius in (3.0, 4.0, 2.2, 5.0, 6.0, 7.0, 1.8):
                for gap in (2, 3, 4):
                    got = self._place(prev, self._node(
                        style=style, gap=gap, rise=rise, radius=radius,
                        spread=3))
                    if got is not None:
                        return got
        # Nothing along and nothing down: go straight up a ladder. It needs one
        # clear column and a post to hang on, which the node builds itself, so
        # it is the move most likely to fit somewhere a hop cannot -- and a
        # ladder out of a corner is a thing a player would actually do.
        for out in (2.4, 3.4, 1.8, 4.4):
            for rise in (3, 4, 2, 5):
                got = self._place(prev, self._node(
                    style=style, gap=1, rise=rise, kind="climb", spread=0,
                    radius=out, support=rise + 1, support_style=theme.wall,
                    label="scramble"))
                if got is not None:
                    return got
        return None

    def _place(self, prev: dict, node: dict, strict: bool = True):
        for rise in node["rises"]:
            for cell in self._targets(prev, node, rise):
                got = self._attempt(prev, node, cell, strict)
                if got is not None:
                    return got
        return None

    def _targets(self, prev: dict, node: dict, rise: int):
        """Candidate landing cells, nearest first to where the helix wants to be.

        This is where the spiral meets the lattice. The ideal point is computed
        in polar coordinates -- advance the angle by the arc the set-piece asked
        for, move the radius toward what it asked for, add the rise -- and then
        the *cells* near that point are ranked by how close they are to it. So
        the course curves continuously and lands on whole cells, and two whole
        cells cannot be inside one another.
        """
        y = prev["y"] + rise
        wall = self.tower.radius_at(y + 1)
        if node["radius"] is not None:
            radius = wall + node["radius"]
        else:
            radius = min(max(self.radius_of(prev) + node["radial"],
                             wall + COURSE_MIN), wall + COURSE_MAX)
        step = node["gap"] + 1
        angle = self.angle_of(prev) + self.wind * step / max(3.0, radius)
        ix, iz = math.cos(angle) * radius, math.sin(angle) * radius
        bx, bz = _round(ix), _round(iz)
        # A landing on the building searches wider, because what it is looking
        # for is a *specific* solid ring rather than empty air: the gallery is
        # only a couple of cells deep and the ideal point can easily fall
        # outside it when the ring below was a different radius.
        span = 3 if node["form"] == "floor" else 2
        scored = []
        for dz in range(-span, span + 1):
            for dx in range(-span, span + 1):
                x, z = bx + dx, bz + dz
                if x == prev["x"] and z == prev["z"] and rise <= 0:
                    continue
                scored.append((math.hypot(x - ix, z - iz), x, z))
        scored.sort()
        return [(x, y, z) for _, x, z in scored[:26]]

    def _attempt(self, prev: dict, node: dict, cell, strict: bool = True):
        """Everything that has to be true, in the order that rejects soonest.

        ``strict`` separates the two kinds of requirement. Without it, a
        landing must be empty, have head-room, be reachable by a move the
        physics has, and have a clear path -- those are *correctness*, and they
        never relax. With it, the body must also fit comfortably where it
        lands, all the way across the block, and stay clear of a gallery's
        overhang -- those are *comfort*, and a course that cannot satisfy them
        anywhere is better off grazing a buttress than falling through to an
        answer nobody checked at all. Measured, that is four blocks in
        twenty-five thousand.
        """
        cx, cy, cz = cell
        step = (cx - prev["x"], cz - prev["z"])
        if step == (0, 0) and node["kind"] not in ("climb", "bubble"):
            return None
        form = node["form"]
        if strict and form != "floor" and not self._clear_of_gallery(cx, cy, cz):
            return None
        cells = _footprint(cx, cy, cz, form)
        if form == "floor":
            # A landing on the building itself: the cell has to be *solid*,
            # which is the exact opposite of every other form's test.
            if (cx, cy, cz) not in self.solid:
                return None
            cells = ((cx, cy, cz),)
        elif not self._free(cells):
            return None
        # Head-room over every cell of the landing: a body is 1.8 m tall and
        # has to be able to stand where it arrives.
        if not self._free((x, y + h, z)
                          for x, y, z in cells for h in range(1, HEADROOM + 1)):
            return None
        if self._reserved(cells) or any(c in self.headroom for c in cells):
            return None
        support = self._support_cells(prev, node, cx, cy, cz)
        if support is None or self._reserved(support):
            return None
        # And the body has to *fit* where it lands, which is not the same
        # question as whether the landing's own cells are free. A body is 0.6
        # wide, so standing one cell clear of a wall it still straddles the
        # cell the wall is in -- head-room says yes and the camera is inside
        # masonry. Measured before this check existed: the body was inside
        # something on 2% of frames, worst case three quarters of a metre.
        surface = cy + FORMS[form]
        if strict and not self._body_fits(
                land_point(cx, surface, cz, form, step), cells):
            return None
        # The same question about the block being *left*. Which edge the feet
        # leave from is not known until the next landing is chosen -- it is
        # chosen here -- and the run across a block toward that edge is a
        # stretch of walking nothing else checks. A take-off corner buried in a
        # buttress is a body that walks through masonry for a fifth of a
        # second, every time, on the way to a jump that was itself perfectly
        # legal.
        if strict:
            here = self.land_point(prev)
            own = set(_footprint(prev["x"], prev["y"], prev["z"], prev["form"]))
            # Whatever the body is already touching where it landed is not this
            # move's fault, and refusing every candidate over it is how a block
            # that was legal to arrive at becomes one nothing can leave.
            own |= set(body_cells(*here))
            gone = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                                 prev["form"], step)
            for f in (0.34, 0.67, 1.0):
                at = tuple(here[i] + (gone[i] - here[i]) * f for i in range(3))
                if not self._body_fits(at, own):
                    return None
        built = self._move_for(prev, node, cx, cy, cz, form, step, support)
        if built is None:
            return None
        move, soft = built
        exempt = _standing_cells(prev) | _standing_cells(
            {"x": cx, "y": cy, "z": cz, "form": form})
        exempt |= set(soft)
        if not self._path_clear(move, exempt,
                                _footprint(prev["x"], prev["y"], prev["z"],
                                           prev["form"]), support):
            return None
        return {"cell": (cx, cy, cz), "step": step, "form": form,
                "move": move, "soft": soft, "support": support}

    def _body_fits(self, at, own) -> bool:
        """Can a body stand at ``at`` without being inside anything?

        The cells of the landing itself are exempt -- for a slab the feet are
        genuinely inside its cell -- and so is anything strictly below the
        feet, because standing *on* a block is not being inside it.
        """
        floor = _floor(at[1] + 0.05)
        own = set(own)
        for cell in body_cells(*at):
            if cell[1] < floor or cell in own:
                continue
            if cell in self.solid:
                return False
        return True

    def _clear_of_gallery(self, cx: int, cy: int, cz: int) -> bool:
        """Keep ordinary landings out from under a balcony's overhang.

        Head-room already refuses a block *directly* under the gallery, and
        that is not enough. A body is 0.6 wide, so standing one cell outside
        the overhang it still straddles the cell at the edge of it -- so the
        block gets placed (its own head-room is clear) and then every move out
        of it is refused for clipping the balcony, which is a landing nothing
        can leave. The course spent its emergency hops climbing out of exactly
        that corner, and this is cheaper than teaching placement to look one
        move further ahead.
        """
        boundary = self.tower.tier_base(self.tower.tier_of(cy + 2))
        if not (boundary - 2 <= cy <= boundary - 1):
            return True
        return math.hypot(cx, cz) > self.gallery_outer(boundary) + 0.75

    def gallery_outer(self, boundary: int) -> float:
        """How far the gallery at this floor level reaches out from the axis.

        A ring's balcony is drawn against *both* radii it meets, so a ring
        standing on a wider one below keeps the wider skirt -- which is what a
        cornice is for, and which means this cannot be read off either radius
        alone.
        """
        tier = self.tower.tier_of(boundary + 2)
        below = self.tower.radius(tier - 1) if tier >= 1 else 0
        return max(self.tower.radius(tier), below) + BALCONY_OUT

    def _support_cells(self, prev: dict, node: dict, cx: int, cy: int, cz: int):
        """The column a set-piece wants under its landing, or ``()``.

        Returns ``None`` when the column will not fit, which is a rejection
        rather than a silent drop: a corbel with no bracket under it is a cube
        floating a foot off a wall, and a ladder with no post to hang on is a
        ladder in mid-air.
        """
        depth = node["support"]
        if not depth:
            return ()
        out = []
        for y in range(cy - 1, cy - 1 - depth, -1):
            cell = (cx, y, cz)
            if cell in self.solid or cell in self.softcells \
                    or cell in self.pathcells:
                break               # it has reached the wall, or a floor
            if cell in self.headroom:
                # It has reached the air over a landing somewhere below, which
                # is not free space even though nothing is drawn in it. A post
                # driven through it is a body running along with its head
                # inside a beam -- and because a post is *structure*, it
                # outlives the block that placed it, so this was the deepest
                # contact in the scene and the last one left.
                break
            out.append(cell)
        return tuple(out)

    def _move_for(self, prev: dict, node: dict, cx: int, cy: int, cz: int,
                  form: str, step, support):
        """Build the move that gets from ``prev`` to this cell, or ``None``.

        Every kind answers the same question -- is this a thing a body can
        actually do -- and answers it against vanilla's numbers rather than
        against a table of gaps somebody chose.
        """
        kind = node["kind"]
        frm = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                            prev["form"], step)
        to = land_point(cx, cy + FORMS[form], cz, form, step)
        if kind in ("hop", "slide"):
            speed = ICE_AIR if kind == "slide" else AIR_SPEED
            leg = arc_leg(frm, to, speed)
            dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
            if dist < MIN_HOP:
                return None
            if not (VY_MIN <= leg["vy0"] <= VY_MAX):
                return None
            if not (AIR_MIN <= leg["dur"] <= AIR_MAX):
                return None
            # You have to be on the way *down* when you arrive, or the body has
            # come up through the side of the block rather than onto it.
            if leg["dur"] < leg["vy0"] / GRAVITY:
                return None
            return Move(kind, [leg]), ()
        if kind == "bounce":
            vy0 = bounce_launch(prev["impact"])
            if vy0 < JUMP_V * 0.8:
                return None            # the drop that fed it was not enough
            rise = to[1] - frm[1]
            disc = vy0 * vy0 - 2.0 * GRAVITY * rise
            if disc < 0.0:
                return None            # the bounce cannot reach that high
            dur = (vy0 + math.sqrt(disc)) / GRAVITY
            dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
            speed = dist / dur
            # A bounce gives no sprint momentum, so what a body can steer to in
            # the air is a band rather than one speed.
            if not (2.6 <= speed <= AIR_SPEED * 1.1):
                return None
            leg = {"kind": "arc", "frm": tuple(frm), "to": tuple(to),
                   "dur": dur, "vy0": vy0}
            return Move("bounce", [leg]), ()
        if kind in ("climb", "bubble"):
            return self._climb_move(prev, node, cx, cy, cz, form, step, frm, to,
                                    support)
        if kind == "web":
            dist = math.dist(frm, to)
            if not (1.4 <= dist <= 3.6) or abs(to[1] - frm[1]) > 1.01:
                return None
            webs = _line_cells(frm, to)
            if not self._free(webs):
                return None
            return Move("web", [line_leg(frm, to, WEB_SPEED)]), tuple(
                (c, "web") for c in webs)
        if kind == "walk":
            dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
            if dist > 2.4 or abs(to[1] - frm[1]) > 0.55:
                return None
            return Move("walk", [line_leg(frm, to, RUN_SPEED)]), ()
        return None

    def _climb_move(self, prev, node, cx, cy, cz, form, step, frm, to, support):
        """A ladder or a bubble column: grab it, ride it, step off.

        The column stands beside the post the landing caps, on the side the
        body arrives from, which is the only arrangement where all three legs
        are things a body can do: a short hop onto it, a vertical ride, and a
        step off onto the block at the top. Put the column *under* the landing
        instead and the last leg has to pass through the block it is aiming at.
        """
        fx, fz = quantise(*step)
        lx, lz = cx - fx, cz - fz
        foot = self.surface(prev)
        top = cy + FORMS[form]
        if top - foot < 1.5:
            return None                 # not worth a ladder
        if top - foot > 9.5:
            return None                 # a ride nobody would sit through
        column = [(lx, y, lz) for y in range(_floor(foot), int(top) + 1)]
        if not self._free(column):
            return None
        if not self._free((lx, y, lz) for y in range(int(top) + 1,
                                                     int(top) + 2)):
            return None
        # A ladder has to hang on something. The post under the landing is the
        # usual answer and the set-piece builds it; a wall behind will do too.
        anchored = any((lx + ax, y, lz + az) in self.solid or
                       (lx + ax, y, lz + az) in set(support)
                       for ax, az in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       for y in (column[len(column) // 2][1], column[-1][1]))
        if not anchored and not support:
            return None
        grab = (lx, foot, lz)
        reach = math.dist((frm[0], frm[2]), (grab[0], grab[2]))
        if not (0.9 <= reach <= 4.2):
            return None
        speed = BUBBLE_SPEED if node["kind"] == "bubble" else CLIMB_SPEED
        legs = [arc_leg(frm, grab, AIR_SPEED),
                line_leg(grab, (lx, top, lz), speed),
                line_leg((lx, top, lz), to, WALK_SPEED)]
        if not (VY_MIN <= legs[0]["vy0"] <= VY_MAX):
            return None
        style = "water" if node["kind"] == "bubble" else "ladder"
        soft = tuple((c, style) for c in column)
        if node["kind"] == "bubble":
            # Soul sand under the column is what makes it push upward. Skipped
            # rather than forced when the floor is already something else --
            # it is one invisible cell at the bottom of a shaft.
            base = (lx, _floor(foot) - 1, lz)
            if base not in self.solid and base not in self.struct:
                soft += ((base, "soulsand"),)
        return Move(node["kind"], legs), soft

    # -- the occupancy map -------------------------------------------------

    def _free(self, cells) -> bool:
        solid = self.solid
        return all(c not in solid for c in cells)

    def _path_clear(self, move: Move, exempt, leaving=(), extra=()) -> bool:
        """Nothing solid along the path, except what the body is already in.

        That last clause is not a loophole, it is the difference between a
        check that works and one that deadlocks. A body is 0.6 m wide and takes
        off from a block's *far edge*, so on the lattice it routinely straddles
        the cell next door -- and which edge it leaves from is not known when
        the block it is standing on is placed. So a landing can be perfectly
        legal to arrive at and have its take-off corner clipping a buttress,
        and then *every* move out of it is refused for a cell the body was
        already occupying before the move began. Measured: that one case was
        the whole of the remaining emergency hops.

        The exemption is bounded to the first third of the path, so a move that
        arcs back into the thing it started next to is still refused.
        """
        solid = self.solid
        # ``extra`` is what this landing is *about* to build -- the post under
        # it. It does not exist in the occupancy map yet, and it must still be
        # checked, because a column driven down from the block you are jumping
        # to is a column built straight through the arc that gets you there.
        # It is placed after the move is solved, so nothing else would notice.
        extra = set(extra)
        points = move.points(ARC_SAMPLES)
        early = len(points) // 3
        leaving = set(leaving)
        for i, (x, y, z) in enumerate(points):
            for cell in body_cells(x, y, z):
                if (cell not in solid and cell not in extra) or cell in exempt:
                    continue
                if i <= early and cell in leaving:
                    continue
                return False
        return True

    def _last_resort(self, prev: dict):
        """Every shape, everywhere, with the comfort rules switched off.

        The move still has to be one the physics has and the path still has to
        be clear of anything solid; what is given up is the body having room to
        stand comfortably and the gallery overhang being kept clear. A hop that
        clips the corner of a buttress is a small ugliness. The alternative,
        below, is not checked at all.
        """
        theme = self.tower.theme_at(prev["y"])
        style = theme.course[self.laid % len(theme.course)]
        for rise in (0, 1, -2, -5):
            for radius in (3.0, 4.0, 2.2, 5.0, 6.0, 1.8):
                for gap in (2, 3, 4, 5):
                    got = self._place(prev, self._node(
                        style=style, gap=gap, rise=rise, radius=radius,
                        spread=3, label="scramble"), strict=False)
                    if got is not None:
                        return got
        return None

    def _emergency(self, prev: dict, node: dict):
        """The one unchecked answer, for when the course has boxed itself in.

        Straight up and out onto the nearest free cell a body could stand on.
        Counted, and the tests hold the count at zero: a course that reaches
        this often is a course laying moves nobody can make, and the only
        visible symptom is a set-piece that looks wrong.
        """
        for rise in (1, 0, 2, -1):
            for cell in self._targets(prev, dict(node, gap=2, radial=0.0), rise):
                cells = _footprint(*cell, "full")
                if self._free(cells) and self._free(
                        (x, y + h, z) for x, y, z in cells
                        for h in range(1, HEADROOM + 1)):
                    step = (cell[0] - prev["x"], cell[2] - prev["z"])
                    frm = takeoff_point(prev["x"], self.surface(prev),
                                        prev["z"], prev["form"], step)
                    to = land_point(cell[0], cell[1] + 1.0, cell[2], "full",
                                    step)
                    return {"cell": cell, "step": step, "form": "full",
                            "move": hop_move(frm, to), "soft": (),
                            "support": ()}
        cell = (prev["x"], prev["y"] + 1, prev["z"] + 1)
        step = (0, 1)
        frm = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                            prev["form"], step)
        to = land_point(cell[0], cell[1] + 1.0, cell[2], "full", step)
        return {"cell": cell, "step": step, "form": "full",
                "move": hop_move(frm, to), "soft": (), "support": ()}

    def _commit(self, prev: dict, node: dict, got: dict) -> dict:
        cx, cy, cz = got["cell"]
        theme = self.tower.theme_at(cy)
        blk = self._block(cx, cy, cz, style=node["style"], form=got["form"],
                          step=got["step"],
                          segment=node.get("label") or self.segment,
                          theme=theme.name)
        prev["out"] = got["step"]
        prev["move"] = got["move"]
        # A move belongs to the block it *leaves*, so the emergency answer's
        # label has to be written back one block. Getting that wrong is how a
        # test that meant to skip the one unchecked hop in a run skipped a
        # perfectly ordinary one instead.
        prev["unchecked"] = node.get("label") == "stuck"
        # The run *across* prev as well as the jump off it. Both are only
        # known now -- which edge the feet leave from is decided by where the
        # course goes next -- and both are corridors the building must not be
        # allowed to grow into afterwards.
        run = self.land_point(prev), self.takeoff_point(prev)
        walk = [tuple(run[0][i] + (run[1][i] - run[0][i]) * f
                      for i in range(3)) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
        prev["path"] = tuple({
            c for x, y, z in list(got["move"].points(ARC_SAMPLES)) + walk
            for c in body_cells(x, y, z)})
        self.pathcells.update(prev["path"])
        # What the body will be doing vertically when it lands here, which is
        # the only thing a slime pad needs to know about the hop that fed it.
        last = got["move"].legs[-1]
        blk["impact"] = (abs(last["vy0"] - GRAVITY * last["dur"])
                         if last["kind"] == "arc" else 0.0)
        for cell, style in got["soft"]:
            self._place_soft(blk, cell, style)
        for cell in got["support"]:
            self._place_struct(cell, node["support_style"] or theme.trim)
        self.blocks.append(blk)
        self.headroom.update(
            (x, y + h, z)
            for x, y, z in _footprint(cx, cy, cz, got["form"]) or ((cx, cy, cz),)
            for h in range(1, HEADROOM + 1))
        self.high = max(self.high, cy)
        self.expected = min(self.expected + CLIMB_TARGET, cy + SLIP)
        self.solid.update(_cells_of(blk))
        if node["deco"]:
            self._decorate(blk, node, theme, got["move"])
        if node["orbs"]:
            self._hang_orbs(prev, blk, node["orbs"])
        return blk

    def _reserved(self, cells) -> bool:
        soft = self.softcells
        return any(c in soft for c in cells)

    def _place_soft(self, blk: dict, cell, style: str) -> None:
        """Ladders, water and webs: drawn, never solid, owned by their block.

        Kept off the structure stream on purpose. They belong to one move, they
        vanish when that move falls off the back of the course, and a ladder
        meshed into the building would outlive the post it was nailed to.
        """
        self.softcells.add(cell)
        blk["soft"].append({"dx": cell[0] - blk["x"], "dy": cell[1] - blk["y"],
                            "dz": cell[2] - blk["z"], "style": style})

    def advance(self, index: int) -> int:
        """Drop what is behind the body. Returns how many blocks went.

        Cells are released here and nowhere else. An occupancy map that only
        ever grows would refuse the whole tower after a few hundred blocks --
        and this course *comes back over itself* every revolution, so it would
        refuse it far sooner than the flat scene would.
        """
        if index <= TRAIL:
            return 0
        drop = index - TRAIL
        for blk in self.blocks[:drop]:
            self.orbs_missed += sum(1 for o in blk["orbs"] if not o["taken"])
            for cell in _cells_of(blk):
                self.solid.discard(cell)
            for s in blk["soft"]:
                self.softcells.discard((blk["x"] + s["dx"], blk["y"] + s["dy"],
                                        blk["z"] + s["dz"]))
            for x, y, z in _footprint(blk["x"], blk["y"], blk["z"],
                                      blk["form"]) or ((blk["x"], blk["y"],
                                                        blk["z"]),):
                for h in range(1, HEADROOM + 1):
                    self.headroom.discard((x, y + h, z))
            self.pathcells.difference_update(blk["path"])
        self.blocks = self.blocks[drop:]
        return drop

    # -- set-pieces --------------------------------------------------------

    def _node(self, style: str, gap: int = 2, rise: int = 0,
              kind: str = "hop", form: str = "full", radial: float = 0.0,
              deco: str | None = None, orbs: int = 0, support: int = 0,
              support_style: str | None = None, spread: int = 2,
              to_y: int | None = None, radius: float | None = None,
              label: str | None = None) -> dict:
        """One entry in a set-piece's expansion.

        ``spread`` is how many neighbouring rises placement may fall back
        through. Two is generous and right for a free-floating hop; a stair or
        a ladder wants zero, because a staircase whose steps are sometimes two
        blocks apart is not a staircase.
        """
        rises = [rise]
        for d in range(1, spread + 1):
            rises += [rise - d, rise + d]
        return {"style": style, "gap": fit_gap(gap, rise), "rise": rise,
                "rises": rises, "kind": kind, "form": form, "radial": radial,
                "deco": deco, "orbs": orbs, "support": support,
                "support_style": support_style, "to_y": to_y,
                #: An *absolute* distance out from the wall, when a set-piece
                #: needs one. ``radial`` nudges the course in or out from
                #: wherever it happens to be, which is the right control for
                #: nearly everything and the wrong one for landing on a
                #: gallery two cells deep -- a nudge from an unknown starting
                #: radius arrives at an unknown finishing one.
                "radius": radius,
                #: What the probe should call this block. Only set where a
                #: node is manufactured mid-set-piece -- the approach to a
                #: gallery is not a checkpoint, and counting it as one made
                #: checkpoints look like two fifths of the course.
                "label": label}

    def _plan_segment(self) -> None:
        prev = self.blocks[-1]
        y = prev["y"]
        boundary = self.tower.tier_base(self.tower.tier_of(y) + 1)
        tier = self.tower.tier_of(boundary)
        # Anything already below the body is written off rather than chased. A
        # bubble column gains eight blocks in one move and can clear a whole
        # ring; a scheduler that insisted on the gallery it flew past would
        # send the course back down for it.
        self._checked.update(t for t in range(tier) if t not in self._checked)
        if tier not in self._checked and 2 <= boundary - y <= 6:
            self._checked.add(tier)
            self.segment = "checkpoint"
            self._pending = self._seg_checkpoint(self.rng, boundary)
            return
        theme = self.tower.theme_at(y + 2)
        hard = self.difficulty
        push = self.climb_pressure
        rng = self.rng
        weights = []
        for name, base in SEGMENTS.items():
            if name == self.segment and name in NO_REPEAT:
                continue
            w = base * theme.weights.get(name, 1.0)
            w *= max(0.05, 1.0 + SEGMENT_RAMP.get(name, 0.0) * hard)
            if name in CLIMBERS:
                w *= 1.0 + 4.0 * push
            elif name in FALLERS:
                w *= max(0.02, 1.0 - push)
            weights.append((name, w))
        roll = rng.random() * sum(w for _, w in weights)
        upto = 0.0
        name = weights[-1][0]
        for candidate, w in weights:
            upto += w
            if roll <= upto:
                name = candidate
                break
        self.segment = name
        self._pending = getattr(self, f"_seg_{name}")(rng, theme)

    def _gap(self, rng, easy, hard) -> int:
        """A set-piece's gap, ramped between two of its own tables.

        Two tables per set-piece rather than one shared pair, because what
        "harder" means is not the same for all of them: a balcony with a
        four-block gap is not a balcony and a staircase physically cannot have
        one. The tables lean short on purpose -- a shipped infinite-parkour
        generator's own distribution is 55% two-block gaps, 34% three and 1%
        four, and a course of nothing but its longest jump reads as a stunt
        reel rather than as running.
        """
        d = self.difficulty
        pick = hard if rng.random() < d else easy
        return pick[rng.randrange(len(pick))]

    def _seg_rim(self, rng, theme) -> list[dict]:
        """The default: hops round the outside of the wall.

        Two thirds flat and a third climbing, which is the ratio the reference
        maps land on from both directions -- 0.64 blocks of rise per hop
        measured off a published map's own stats, and 65% flat / 20% up in a
        shipped generator's tuning file.
        """
        out = []
        for i in range(rng.randint(4, 8)):
            rise = rng.choice((1, 1, 1, 0) if self.climb_pressure > 0.4
                              else (0, 0, 1, 1, 1, 1, 1, -1))
            out.append(self._node(
                style=theme.course[i % len(theme.course)],
                gap=self._gap(rng, (2, 2, 2, 3), (2, 3, 3, 4)),
                rise=rise,
                form="slab" if rng.random() < 0.10 + 0.20 * self.difficulty
                else "full",
                deco="rail" if rng.random() < 0.18 else None,
                orbs=1 if rng.random() < 0.45 else 0))
        return out

    def _seg_corbel(self, rng, theme) -> list[dict]:
        """Landings that hug the wall, each on its own bracket.

        The single cheapest thing that makes the course look *attached* to the
        building rather than floating beside it, and it is what a real spiral
        map's ledges are: a block, and a corbel under it.
        """
        out = []
        for i in range(rng.randint(4, 7)):
            out.append(self._node(
                style=theme.course[i % len(theme.course)] if i % 2
                else theme.trim,
                gap=self._gap(rng, (2, 2, 3), (2, 3, 3)),
                rise=rng.choice((1, 1, 1, 0)),
                radial=-0.7,
                support=2, support_style=theme.trim,
                deco="bracket",
                orbs=1 if rng.random() < 0.4 else 0))
        return out

    def _seg_stairs(self, rng, theme) -> list[dict]:
        """A flight winding up the wall, one block a step.

        The one set-piece the ramp cannot widen, and the reason is arithmetic:
        climbing a block means arriving past the apex, so the longest hop that
        rises one is 4.0 m and only a two-block gap fits under it. What the
        ramp does with staircases instead is call for fewer of them.
        """
        style = theme.trim
        return [self._node(style=style if i % 2 else theme.wall,
                           gap=2, rise=1, form="stair", spread=1,
                           support=1, support_style=theme.wall,
                           radial=-0.3,
                           orbs=1 if i % 2 else 0)
                for i in range(rng.randint(5, 8))]

    def _seg_balcony(self, rng, theme) -> list[dict]:
        """A walkway you *run* along rather than jump across.

        Every parkour course needs somewhere the feet are on the ground for
        more than a fifth of a second, and a spiral map's answer is a gallery.
        The blocks touch, so the move between them is a walk -- which is a real
        move here rather than a degenerate jump, and reads as one.
        """
        out = [self._node(style=theme.trim, gap=self._gap(rng, (2, 3), (3, 3)),
                          rise=0, support=2, support_style=theme.wall,
                          deco="rail")]
        for i in range(rng.randint(3, 6)):
            out.append(self._node(style=theme.trim if i % 2 else theme.floor,
                                  gap=0, rise=0, kind="walk", spread=0,
                                  support=2, support_style=theme.wall,
                                  deco="rail" if i % 2 == 0 else "lantern",
                                  orbs=1 if i % 2 else 0))
        return out

    def _seg_pillars(self, rng, theme) -> list[dict]:
        """Columns standing out of the void, tops at staggered heights.

        Mostly *below* the path: each landing caps a shaft running down out of
        sight, which is what stops a stretch of course reading as cubes hanging
        in air. Vanilla parkour maps are full of these and it costs one column.
        """
        style = theme.accent
        return [self._node(
            style=theme.course[i % len(theme.course)] if i % 2 else style,
            gap=self._gap(rng, (2, 3, 3), (3, 3, 4)),
            rise=rng.choice((0, 1, 1, -1)),
            radial=rng.uniform(0.2, 0.9),
            support=rng.randint(4, 9), support_style=theme.wall,
            orbs=1 if rng.random() < 0.5 else 0)
            for i in range(rng.randint(4, 7))]

    def _seg_beams(self, rng, theme) -> list[dict]:
        """Timbers cantilevered out of the wall, landed on end-on."""
        return [self._node(style=theme.accent if i % 2 else theme.course[0],
                           gap=self._gap(rng, (2, 2, 3), (2, 3, 3)),
                           rise=rng.choice((1, 1, 0, 1, -1)),
                           radial=-0.4, deco="beam",
                           orbs=1 if rng.random() < 0.45 else 0)
                for i in range(rng.randint(4, 7))]

    def _seg_ladderrun(self, rng, theme) -> list[dict]:
        """Up a post on a ladder, then off the top of it.

        A ladder is the game's own answer to the thing a tower needs and a hop
        cannot give: more than one block of height at once. It is deliberately
        slow -- two and a third metres a second against a sprint's five and a
        half -- and the pause is the point, because it is the only moment in a
        run where the camera has time to look at the drop.
        """
        rise = rng.randint(3, 6) + int(2 * self.difficulty)
        return [
            self._node(style=theme.accent, gap=1, rise=rise, kind="climb",
                       spread=0, support=rise + 1, support_style=theme.wall,
                       deco="lantern", orbs=1),
            self._node(style=theme.course[0],
                       gap=self._gap(rng, (2, 3), (3, 3)),
                       rise=rng.choice((0, 0, -1)), orbs=1),
        ]

    def _seg_bubblelift(self, rng, theme) -> list[dict]:
        """A soul-sand bubble column: eleven metres a second, straight up.

        By a distance the fastest thing in the game, and this scene does not
        soften it. It is what a ring builds when it needs to gain eight blocks
        in the space a ladder would take three seconds over.
        """
        rise = rng.randint(5, 8) + int(2 * self.difficulty)
        return [
            self._node(style=theme.accent, gap=1, rise=rise, kind="bubble",
                       spread=0, support=rise + 1, support_style=theme.wall,
                       deco="lantern", orbs=2),
            self._node(style=theme.course[0], gap=self._gap(rng, (2, 3), (3, 3)),
                       rise=0, orbs=1),
        ]

    def _seg_slimeshaft(self, rng, theme) -> list[dict]:
        """Drop onto slime, come back up the far side.

        And the important thing about it is what it is *not*: slime does not
        gain height. Vanilla's restitution is exactly 1.0 and holding jump
        cancels the bounce, so a pad can only ever spend a fall that already
        happened. What it buys is the shape -- a plunge and a rebound, in a
        place a hop could not have crossed -- and the arithmetic in
        ``_move_for`` is what makes the rebound land where the set-piece says.
        """
        drop = rng.randint(3, 5)
        return [
            self._node(style="slime", gap=self._gap(rng, (2, 3), (3, 4)),
                       rise=-drop, form="slime", spread=1,
                       support=2, support_style=theme.wall, orbs=1),
            self._node(style=theme.course[0], gap=3, rise=drop - 1,
                       kind="bounce", spread=2, orbs=2),
        ]

    def _seg_iceline(self, rng, theme) -> list[dict]:
        """A few blocks of packed ice, and then the jump it buys.

        Ice does not lengthen the arc -- flight time is fixed by the height
        tier -- it lengthens the *run-up*, so the body leaves faster and
        therefore further. Hence the shape: you have to cross the ice before
        the jump means anything.
        """
        out = [self._node(style="packedice", form="ice",
                          gap=self._gap(rng, (2, 2), (2, 3)), rise=0,
                          orbs=1 if i == 0 else 0)
               for i in range(rng.randint(2, 4))]
        out.append(self._node(style=theme.course[0], kind="slide",
                              gap=self._gap(rng, (4, 5), (5, 6)),
                              rise=rng.choice((-1, -1, 0)), spread=1, orbs=3))
        return out

    def _seg_webwalk(self, rng, theme) -> list[dict]:
        """A clump of cobweb to push through. The slow beat."""
        return [
            self._node(style=theme.course[0],
                       gap=self._gap(rng, (2, 3), (3, 3)), rise=0),
            self._node(style=theme.trim, gap=1, rise=0, kind="web", spread=1,
                       orbs=1),
            self._node(style=theme.course[1 % len(theme.course)],
                       gap=self._gap(rng, (2, 3), (3, 3)),
                       rise=rng.choice((0, 1)), orbs=1),
        ]

    def _seg_soulwalk(self, rng, theme) -> list[dict]:
        """Soul sand: two and a half metres a second, and it shows."""
        return [self._node(style="soulsand",
                           gap=self._gap(rng, (2, 2, 3), (2, 3, 3)),
                           rise=rng.choice((0, 1, 1)),
                           support=1, support_style=theme.wall,
                           deco="torch" if i % 2 else None,
                           orbs=1 if i % 2 else 0)
                for i in range(rng.randint(3, 5))]

    def _seg_gap(self, rng, theme) -> list[dict]:
        """The longest jump the physics has, between two places to stand.

        A computed number rather than a dramatic one: one impulse and one
        speed fix the reach, and going further is only available by dropping,
        which is exactly how a player clears a gap they cannot make level.
        """
        drop = rng.choice((-1, -1, -2))
        return [
            self._node(style=theme.trim, gap=self._gap(rng, (2, 3), (3, 3)),
                       rise=0, form="wide", radial=0.8, deco="lantern"),
            self._node(style=theme.accent, gap=fit_gap(6, drop), rise=drop,
                       spread=1, orbs=3),
            self._node(style=theme.trim, gap=self._gap(rng, (2, 3), (3, 3)),
                       rise=0, form="wide", radial=-0.4, deco="lantern",
                       orbs=1),
        ]

    def _seg_headhitter(self, rng, theme) -> list[dict]:
        """Hops under a lintel low enough to be worth ducking.

        The beam is hung against the arc that is about to be flown under it,
        which is the only reason it is safe to build: where the feet leave and
        land is known when the block is generated, so the flight is a list of
        points and a lintel a body's height above the highest of them is
        guaranteed to be missed while looking as though it will not be.
        """
        return [self._node(style=theme.course[i % len(theme.course)],
                           gap=self._gap(rng, (2, 3), (3, 3)),
                           rise=rng.choice((0, 0, -1)),
                           deco="lintel" if i % 2 else "rail",
                           orbs=1 if rng.random() < 0.5 else 0)
                for i in range(rng.randint(3, 6))]

    def _seg_checkpoint(self, rng, boundary: int) -> list[dict]:
        """Arrive on the gallery that separates one ring from the next.

        Scheduled rather than rolled, because the balcony is a solid ring at a
        known height and a course that wandered past it would have to be
        refused a landing everywhere along it. It is also the loudest beat the
        scene has: the theme changes on the step off it.

        The landings are ``floor`` nodes -- they stand on architecture that
        already exists rather than placing a block of their own, which is the
        only way to land *on the building*.
        """
        y = boundary - 1
        # One block out from the wall, which is the middle of a gallery two
        # deep -- and stated absolutely, because a nudge inward from wherever
        # the approach happened to end up lands on the balcony only by luck.
        # Just past the middle of a gallery two cells deep. Nearer the wall
        # and the body's shoulder is inside the masonry it is standing beside;
        # further and the landing is off the outer edge.
        out = [self._node(style="", gap=2, rise=0, form="floor", spread=0,
                          radius=1.7, deco="lantern", orbs=1, to_y=y)]
        for i in range(rng.randint(1, 2)):
            out.append(self._node(style="", gap=0, rise=0, kind="walk",
                                  form="floor", spread=0, to_y=y, radius=1.7,
                                  deco="banner" if i == 0 else None,
                                  orbs=1 if i % 2 else 0))
        return out

    # -- decoration and pickups -------------------------------------------

    def _decorate(self, blk: dict, node: dict, theme: Theme, move: Move) -> None:
        """Expand a decoration into boxes in the block's own frame.

        Two rules keep the scene on the grid, both inherited from the flat
        scene because both were learned the hard way there. Offsets are rotated
        into the *quantised* heading -- one of eight lattice directions -- so a
        rail cannot land three fifths of the way into a cell. And sub-block
        furniture (posts, rails, lanterns, brackets) is centred inside its cell
        exactly as vanilla's is, so it occupies a block without filling it and
        the generator is not forced to route the course around a lamp.

        Only the lintel is solid, and it is the only one checked against the
        flight it hangs over.
        """
        kind = node["deco"]
        fx, fz = quantise(*blk["step"])
        rx, rz = -fz, fx
        # Which way the wall is: decoration leans toward the building, because
        # a bracket on the void side is holding nothing up.
        wall = self.tower.radius_at(blk["y"])
        inward = -1.0 if math.hypot(blk["x"], blk["z"]) > wall else 1.0
        ix = inward * (blk["x"] / (math.hypot(blk["x"], blk["z"]) or 1.0))
        iz = inward * (blk["z"] / (math.hypot(blk["x"], blk["z"]) or 1.0))
        add = blk["deco"].append
        top = FORMS[blk["form"]]

        if kind == "rail":
            for side in (-1, 1):
                add(_deco(rx * side * 0.42, top, rz * side * 0.42,
                          0.16, 0.86, 0.16, theme.trim))
                add(_deco(rx * side * 0.42, top + 0.62, rz * side * 0.42,
                          0.9 if abs(fx) else 0.16, 0.12,
                          0.9 if abs(fz) else 0.16, theme.trim))
        elif kind == "lantern":
            add(_deco(rx * 0.40, top + 0.18, rz * 0.40, 0.30, 0.36, 0.30,
                      theme.glow, glow=True))
            add(_deco(rx * 0.40, top + 0.02, rz * 0.40, 0.08, 0.18, 0.08,
                      theme.trim))
        elif kind == "torch":
            add(_deco(rx * 0.42, top + 0.34, rz * 0.42, 0.09, 0.52, 0.09,
                      theme.trim))
            add(_deco(rx * 0.42, top + 0.64, rz * 0.42, 0.16, 0.16, 0.16,
                      theme.glow, glow=True))
        elif kind == "bracket":
            add(_deco(ix * 0.30, -0.34, iz * 0.30, 0.42, 0.62, 0.42,
                      theme.trim))
        elif kind == "beam":
            add(_deco(ix * 1.20, 0.10, iz * 1.20,
                      2.6 if abs(ix) > abs(iz) else 0.30, 0.28,
                      2.6 if abs(iz) >= abs(ix) else 0.30, theme.accent))
        elif kind == "banner":
            add(_deco(rx * 0.46, top + 0.9, rz * 0.46, 0.34, 1.8, 0.08,
                      self.rng.choice(CANDY)))
        elif kind == "lintel" and move is not None:
            self._lintel(blk, theme, move, fx, fz, rx, rz)

    def _lintel(self, blk: dict, theme: Theme, move: Move, fx, fz, rx, rz) -> None:
        """A beam over the jump that has just been made, hung to be missed.

        ``HEADROOM`` still keeps two cells clear over every *landing*, because
        a body has to be able to stand where it arrives. What a head-hitter
        relaxes is the space over the **gap**, which nothing ever needed and
        which is where the real game keeps its low ceilings.
        """
        points = move.points(9)
        apex = max(p[1] for p in points)
        mid = points[len(points) // 2]
        y = _round(apex + BODY_H + 0.15)
        cells = [(_round(mid[0]) + rx * s, y, _round(mid[2]) + rz * s)
                 for s in (-1, 0, 1)]
        if not self._free(cells) or any(c in self.headroom for c in cells):
            return
        for x, cy, z in cells:
            for px, py, pz in points:
                if (x, cy, z) in set(body_cells(px, py, pz)):
                    return
        for cell in cells:
            self.solid.add(cell)
            blk["deco"].append({"dx": cell[0] - blk["x"],
                                "dy": cell[1] - blk["y"],
                                "dz": cell[2] - blk["z"],
                                "sx": 1.0, "sy": 1.0, "sz": 1.0,
                                "style": theme.trim, "glow": False,
                                "solid": True})

    def _hang_orbs(self, prev: dict, blk: dict, count: int) -> None:
        """Strung *on* the path that is about to be flown, at chest height.

        Which makes "every orb laid down is collected" a property of generation
        rather than a hope about the simulation.
        """
        move = prev["move"]
        if move is None:
            return
        spread = ORB_FRACTIONS.get(count)
        if spread is None:
            return
        for f in spread:
            x, y, z = move.at(move.dur * f)
            blk["orbs"].append({"x": x, "y": y + CHEST, "z": z, "taken": False})


#: Where along a move a run of orbs sits. Never at the very ends, where an orb
#: is inside the block it was strung from.
ORB_FRACTIONS = {1: (0.5,), 2: (0.34, 0.66), 3: (0.26, 0.5, 0.74)}


def _deco(dx: float, dy: float, dz: float, sx: float, sy: float, sz: float,
          style: str, glow: bool = False) -> dict:
    return {"dx": dx, "dy": dy, "dz": dz, "sx": sx, "sy": sy, "sz": sz,
            "style": style, "glow": glow, "solid": False}


def _footprint(cx: int, cy: int, cz: int, form: str):
    """Every cell a landing of this form fills. A ``floor`` fills none: it
    stands on architecture that is already there."""
    if form == "floor":
        return ()
    sp = SPREAD.get(form, 0)
    if not sp:
        return ((cx, cy, cz),)
    return tuple((cx + ox, cy, cz + oz)
                 for ox in range(-sp, sp + 1) for oz in range(-sp, sp + 1))


def _cells_of(blk: dict):
    """Every cell a block and its *solid* decoration occupy."""
    out = list(_footprint(blk["x"], blk["y"], blk["z"], blk["form"]))
    for d in blk["deco"]:
        if d.get("solid"):
            out.append((blk["x"] + _round(d["dx"]), blk["y"] + _round(d["dy"]),
                        blk["z"] + _round(d["dz"])))
    return out


def _standing_cells(blk: dict) -> set:
    """Cells the body is inside while standing on this block.

    Only a slab qualifies: its walking surface is halfway up its own cell, so
    the feet are inside it. Exempting a whole block wholesale -- which the flat
    scene did once -- makes the one check that would catch a hop leaving a wide
    platform too flat blind to it by construction.
    """
    if blk["form"] != "slab":
        return set()
    return set(_footprint(blk["x"], blk["y"], blk["z"], blk["form"]))


def _line_cells(frm, to) -> tuple:
    """Whole cells along a straight run, for filling a gap with cobweb."""
    steps = max(2, int(math.dist(frm, to) * 2) + 1)
    out: dict = {}
    for i in range(steps + 1):
        f = i / steps
        out[(_round(frm[0] + (to[0] - frm[0]) * f),
             _floor(frm[1] + (to[1] - frm[1]) * f + 0.5),
             _round(frm[2] + (to[2] - frm[2]) * f))] = None
    return tuple(out)
