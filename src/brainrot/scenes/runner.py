"""The endless runner, rebuilt on real 3D assets.

Layout follows the reference format exactly: three locked lanes, a chase
camera behind and above, trains and barriers streaming toward the player,
coin arcs along a guaranteed-clear corridor, city canyon either side.

World model: the runner stays at the origin; the world flows past. Every
entity carries ``d`` -- its distance ahead of the runner along the track --
which shrinks by the run speed each frame and maps to ``z = -d`` at draw
time. Content is generated per 6 m *row* from a per-row substream, so a run
number always replays the same world.

Two invariants hold the whole thing up.

**Solvability by construction.** Each row is assigned a clear lane before
obstacles are placed, and that lane moves at most one lane between rows.
Blocking obstacles only go in lanes the corridor does not occupy; the
corridor itself only carries things that can be jumped or rolled through, and
never two of those close enough together that one move cannot finish before
the next begins.

**Nothing is ever drawn intersecting anything.** Every obstacle has a hitbox
built from the asset's own measured geometry pushed through the same
transform as its draw call (:mod:`brainrot.engine.collide`), the runner has a
body box measured from the character's posed meshes, and
:mod:`brainrot.scenes.runnerplan` schedules lane changes and take-offs in
*time* so the clearance is solved rather than hoped for. What remains is a
per-frame overlap test with a stumble behind it, so that even a case the
planner could not solve reads as a hit taken rather than as geometry passing
through a body.
"""

from __future__ import annotations

import math

from .. import assets
from ..engine import rl
from ..engine.collide import AABB, placed
from ..engine.fx import Burst, Weather, blob_shadow, glow_billboard
from ..engine.hud import text
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import SkyDome
from . import runnerplan as plan

LANE_X = 2.4                  # must match assets/src/track.py LANE_SPACING
ROW = 6.0                     # generation stride; also the track tile length
VIEW_AHEAD = 96.0             # spawn horizon
VIEW_BEHIND = 16.0
FOG_FAR = 88.0

#: The speed range, and how long the run takes to cross it.
#:
#: These were 8.5 to 15.5 over 75 seconds, which is a sensible ramp for a game
#: somebody sits down to play and the wrong one entirely for this. The strip
#: is on screen for as long as Claude is thinking -- ten seconds to a minute,
#: usually -- so the old ramp spent the whole of its visible life in the
#: bottom third of its own speed range: 8.5 m/s at the start, 11.3 by thirty
#: seconds, and the interesting part of the curve reserved for a run nobody
#: ever saw. It starts quick now and gets quick fast.
#:
#: Then 10.5 to 18 over forty seconds turned out to be the same mistake one
#: notch along. Read off the reference -- a five-million-point run of the real
#: game, score rate against the clock -- the distance rate at the top is about
#: 1.65 times what it is a minute in, and the top is where a watched run
#: should live. What a strip cannot afford is the *approach* to it: this one
#: opens where the old one finished and reaches a speed the old one had no
#: name for, in under half a minute.
#:
#: Everything downstream is sized in metres rather than seconds precisely so
#: this could be raised without re-deriving it -- see
#: :meth:`plan.Kinematics.for_speed`. What does not survive untouched are the
#: two clamps in there: past about 19 m/s a jump stops shrinking and starts
#: covering more *track*, so the spans below are read off the top of the range
#: rather than off the nominal figures.
BASE_SPEED = 15.0
TOP_SPEED = 24.0
RAMP_SECONDS = 28.0
#: The runner's capabilities at the fastest it will ever go. Everything that
#: reserves track for a move is sized from this, because a move's *span* is
#: longest there -- 12.4 m of slide against the nominal 8.4.
TOP_KIN = plan.Kinematics.for_speed(TOP_SPEED)

RAIL_TOP = 0.30               # y of the surface the runner runs on
CHAR_SCALE = 0.95

#: How far ahead the planner reasons, and how often it re-solves. The horizon
#: has to outlast the longest commitment (a jump) with room to see the far
#: side of it; re-solving faster than the world changes just burns CPU.
PLAN_HORIZON = 2.8
#: Resolution of the plan. At top speed a step is how far the world moves
#: between decisions, so it has to stay well under the depth of the thinnest
#: obstacle -- a 0.4 m hurdle crossed at 15.5 m/s is gone in 0.026 s.
PLAN_STEP = 0.03
#: Resolution of the *lane* search, which is coarser on purpose. Lanes change
#: on the scale of a quarter-second; solving them at the collision grid's
#: resolution costs four times the work for a decision that cannot use it,
#: and the lane DP was comfortably the most expensive thing in the scene.
LANE_STEP = 0.06
PLAN_EVERY = 0.10
#: Rounds of "solve, check, mark what failed as unavoidable, solve again".
PLAN_ATTEMPTS = 5
#: How far into a plan counts as committed. Trouble past this is left to the
#: next re-solve, which will see it from closer up and with more options.
COMMIT_WINDOW = 1.2
#: How far ahead the last-resort reflex looks. Only needs to cover the moment
#: a move has to start, not the moment it is best planned.
REFLEX_WINDOW = 1.0
#: Seconds a pickup run stays on the HUD after the last coin.
COMBO_HOLD = 1.6
#: How long a player's input keeps the planner switched off. Long enough that
#: it does not fight between key presses, short enough that letting go of the
#: keyboard hands the run back promptly.
DRIVEN_HOLD = 0.6

#: Entity kinds a body can actually hit. Everything else is scenery, and
#: checking that first is what keeps the per-frame collision pass cheap. A
#: ramp is deliberately absent: it is a floor, not a wall, and it appears in
#: :meth:`RunnerScene.surface_at` instead.
SOLID_KINDS = frozenset(("barrier", "hoarding", "gantry", "train"))

#: "no particular lane" in the occupancy ledger -- a hoarding spans them all.
ANY_LANE = -1
#: Slack left around a reserved span, so that two obstacles are never merely
#: adjacent: a body is most of a metre deep and has to fit between them.
BODY_PAD = 0.5
#: Spacing of a coin trail along the track.
COIN_PITCH = 0.9
#: Half the track a move commits the body to, so two obstacles that each
#: demand one are never closer together than one move takes to finish. A slide
#: is the long one -- ``plan.ROLL_SPAN`` of track, at any speed, which is the
#: point of sizing moves in metres rather than in seconds. Row counting used
#: to stand in for this and could not see across a set-piece boundary: two
#: hurdles a row apart either side of one put the runner's feet through the
#: second while it was still coming down off the first.
#:
#: Read off the top of the speed range rather than from ``plan.ROLL_SPAN``,
#: which is the span a slide covers only while ``for_speed`` is still able to
#: shorten it. Past 18 m/s the roll clamps at 0.46 s and starts covering more
#: track with every metre a second added, so the nominal figure understates
#: the reservation by half at the top of this range -- and an understated
#: reservation is two obstacles the body meets inside one move.
ACTION_SPAN = max(plan.ROLL_SPAN, TOP_KIN.roll_time * TOP_SPEED)
#: Track between two hurdles in a rhythm. Twice the commitment, and a little
#: over, so the run-up is never a scramble.
HURDLE_PITCH = 2.0 * ACTION_SPAN + 1.2
#: A shallower overlap than this is two faces meeting, not a body inside
#: something. A runner standing on a train roof has its feet at exactly the
#: roof's height, and floating point does not do "exactly".
CONTACT_EPS = 0.002

# -- riding a train ---------------------------------------------------------
#: The ramp asset, in the numbers the scene needs, all as distances from the
#: ramp's own position. The model is built nose-forward, so the slope starts
#: at ``RAMP_FOOT`` (nearest), climbs ``RAMP_LIP_H`` over ``RAMP_RUN`` of
#: track, and then holds that height across a flat top which begins at
#: ``-RAMP_LIP``. Checked against the measured asset in tests/test_assets.py
#: rather than trusted here.
#:
#: The flat top is what makes the take-off survivable. It is booked at a time
#: and fired on a frame boundary, so with the slope running to the back edge
#: the moment the leap is due is the same moment the ramp stops holding the
#: body up -- and one frame of rounding decides between a leap onto the train
#: and a trip off the end into the side of it. Measured over 60 seeds x 180 s,
#: that came down wrong 31 times.
RAMP_FOOT = 1.8
RAMP_RUN = 3.0
RAMP_LIP = 1.2
RAMP_LIP_H = 1.15
#: Clear track between the lip and the train's front face. It has to be longer
#: than the leap takes to rise past roof height and shorter than the leap
#: takes to come back down -- both of which are fixed lengths whatever the
#: speed, because that is what :meth:`plan.Kinematics.for_speed` is for.
MOUNT_GAP = 4.4
#: Track before the ramp, for the corridor to settle into its lane, and after
#: the train, for the fall off the back to land in.
APPROACH_RUN = 13.0
DISMOUNT_RUN = 7.0
#: A convoy: how many trains are chained one behind the next, how many cars
#: each is, and the gap left between two of them.
#:
#: This is the shape the whole set-piece was missing. It laid one train, rode
#: it for the twenty-odd metres it was long -- a second and a bit at speed --
#: and put the runner back on the rails, which measured as 2.7 seconds on a
#: roof per minute. Read off the reference at full speed, roughly a third of
#: the frames have the player up on the trains, and the way they stay up there
#: is by jumping from one roof to the next. So the trains come in a line now,
#: and the gaps between them are the point rather than a flaw: a chain of four
#: is sixty metres of elevated running and three leaps to keep it.
CONVOY_TRAINS = (3, 5)
CONVOY_CARS = (3, 5)
#: How much longer than the rows it was offered a convoy may run before it
#: starts dropping trains off its own tail.
CONVOY_SLACK = 8
ROOF_GAP = (2.8, 4.0)
#: Slack a roof-to-roof leap must have over the gap it crosses, on top of the
#: body's own depth. Not a margin for error -- the arc is solved -- but the
#: track the take-off is taken *before* the roof ends, which is what stops the
#: leap being a step off the last centimetre of it.
HOP_MARGIN = 2.6
#: How far before the roof runs out the leap is taken, as a fraction of its
#: own air time. Later looks better and lands further onto the next roof; too
#: late and one frame of rounding is a fall into the gap.
HOP_LEAD = 0.38
#: How often a convoy stands a second line of trains alongside it -- the
#: canyon the reference runs down at speed rather than a single train in an
#: empty yard.
FLANK_CHANCE = 0.7
#: How near the middle of a ramp's lane the body has to be for the slope to
#: pick it up. Much tighter than the ramp is wide, and deliberately: a body
#: still crossing when it clips the edge of a ramp is frozen there by the rule
#: below, mounts from an offset, and lands on the roof a metre and a half off
#: centre -- where it rides along inside the train in the *next* lane. You get
#: onto a ramp by running at it.
RAMP_GRIP = 0.30
#: A body is held up while its *centre* is over the surface, which is only
#: safe because a body that is up on something may not start a crossing at all
#: (see ``Motion.advance``). Widening it to "any part of me is over it" so
#: that leaving could never graze the edge was worse in both directions: a
#: lane change that merely brushed a train was enough to teleport the runner
#: 2.59 m straight up onto its roof, and 157 frames of body-inside-train
#: followed.
#: How far ahead a surface is worth carrying in the ridable list. Has to cover
#: the planning horizon at top speed, or the plan lands on a roof the check
#: cannot see and reports a fall into thin air.
RIDE_REACH = 70.0

#: The set-piece vocabulary: ``(name, min rows, max rows, weight)``.
#:
#: The parkour scene learned that a uniform stream of content is watchable for
#: about ten seconds; this is the runner's answer to its ``SEGMENT_TABLE`` and
#: it exists for exactly the same reason. Every entry is a stretch of track
#: *and* the corridor through it, decided together -- which is the only way to
#: express a weave, a yard, or a ramp onto a roof.
#: How often a run *opens* on a roof set-piece rather than drawing from the
#: table. See ``_begin_segment``: what gets watched is the first few seconds.
OPENING_ROOFRUN = 0.62

#: Reweighted against the reference rather than against taste. At full speed
#: the real game is trains: a third of the frames have the player up on one,
#: nearly every frame has one in it, and the plain jump-or-duck barrier is the
#: *least* of what is going on. This scene was the other way round -- 48
#: barriers a minute against 7.8 trains, and 2.7 seconds a minute spent on a
#: roof -- which is the "a bunch of mediocre speed barriers" the owner named.
#: So the roof run is the commonest set-piece there is now, the yard is second,
#: and the two barrier set-pieces between them are worth less than either.
SEGMENT_TABLE = (
    ("cruise", 2, 3, 0.5),
    ("hurdles", 5, 8, 1.2),
    ("slalom", 6, 9, 1.3),
    ("tunnel", 5, 8, 1.0),
    ("yard", 9, 14, 2.4),
    ("express", 8, 11, 0.9),
    ("roofrun", 14, 22, 5.0),
)

#: Minimum rows between two obstacles that demand a move. One move must be
#: able to finish before the next begins even at top speed, or the corridor
#: stops being solvable however well the planner reasons. At 15.5 m/s a row
#: is 0.39 s, a jump is 0.61 s and a slide is 0.80 s -- so two hurdles need
#: two rows between them, and anything either side of a hoarding needs four.
ACTION_GAP_ROWS = 3
#: A hoarding spans every lane, so its spacing is not a per-lane matter: a
#: hurdle anywhere near one is a hurdle the runner meets mid-slide, whichever
#: lane it picked. A slide and a jump back to back is 1.41 s; five rows at top
#: speed is 1.94 s.
HOARDING_GAP_ROWS = 5
#: Rows the guaranteed-clear lane must hold before it may move again. Two rows
#: is 0.77 s at top speed, against 0.52 s to cross a lane and be ready to
#: cross again.
CORRIDOR_HOLD = 2

TRAIN_CAR_LEN = 5.1
IMPACT_TIME = 0.75
#: Clear track reserved either side of a train, so that two trains in
#: different lanes are never merely *adjacent*. Back to back with a small gap
#: still squeezes the runner: it has to be out of the first lane and into a
#: third before the second arrives, and one lane change at top speed already
#: costs four and a half metres of track. Derived from that rather than typed
#: in, for the same reason ``ACTION_SPAN`` is.
TRAIN_PAD = max(8.0, 2.0 * TOP_KIN.lane_time * TOP_SPEED + 1.0)


@register("runner")
class RunnerScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        seed = ctx.seed
        pal = ctx.palette

        self.sky = SkyDome(pal, seed, ctx.width, ctx.height)
        self.weather = Weather(pal, ctx.width, ctx.height, seed.root & 0xFFFF)
        self.burst = Burst()
        self.camera = rl.make_camera(58.0)

        # -- assets ------------------------------------------------------
        self.track = assets.load("track")
        self.character = assets.load("character")
        self.train_cab = assets.load("train_cab")
        self.train_car = assets.load("train_car")
        self.barrier = assets.load("barrier")
        self.hoarding = assets.load("hoarding")
        self.gantry = assets.load("gantry")
        self.ramp = assets.load("ramp")
        self.fence = assets.load("fence")
        self.pillar = assets.load("pillar")
        self.lamp = assets.load("lamp")
        self.signal = assets.load("signal")
        self.coin = assets.load("coin")
        self.buildings = [assets.load(f"building_{c}") for c in "abc"]

        # -- measured geometry -------------------------------------------
        self.body = _body_profile()
        self.kin = plan.Kinematics.for_speed(BASE_SPEED)
        self._boxes = _obstacle_boxes()
        #: half-depth along the track of everything that reserves some, from
        #: the measured boxes rather than from a table anybody could forget to
        #: update after moving a beam
        self._half = {name: 0.5 * (self._boxes[name].z1 - self._boxes[name].z0)
                      for name in ("barrier", "hoarding", "gantry")}

        style = seed.stream("wardrobe")
        self.outfit = {
            "hoodie": pal.accent,
            "cap": pal.accent2,
            "pants": (40, 48, 82) if not pal.is_dark else (58, 62, 96),
            "pack": pal.hazard if style.random() < 0.5 else pal.accent2,
        }
        self.train_liveries = [pal.accent, pal.accent2, pal.train, pal.hazard]
        # Sign bridges are the most-repeated object in the scene after the
        # track itself, and the asset's own zone colour is a fixed green -- so
        # every run had the same green rectangle over it every fifty metres.
        self.sign_color = rl.mix_rgb(style.choice((pal.accent2, pal.train)),
                                     pal.structure, 0.35)

        # -- world state -------------------------------------------------
        self.rng = ctx.stream("runner-layout")
        self.travel = 0.0
        self.speed = BASE_SPEED
        self.next_row = 2          # rows 0-1 stay clear, like the original
        self.corridor: dict[int, int] = {0: 1, 1: 1}
        self._first_row = 0
        self._last_row = 1
        self._held = CORRIDOR_HOLD
        self._last_segment = ""
        #: how many of each set-piece this run has laid down, and of each
        #: kind of thing in them -- the numbers ``tools/runner_probe.py``
        #: turns into "does it repeat itself". Counted at spawn rather than by
        #: scanning the live entity list, which cannot be done by identity:
        #: a retired entity's ``id`` is handed straight back out to the next
        #: one, and a probe that walks the list undercounts by a factor of ten.
        self.segments: dict[str, int] = {}
        self.spawned: dict[str, int] = {}
        self.entities: list[dict] = []
        self.score = 0.0
        self.coins = 0
        #: consecutive pickups, and how long the tally stays on screen
        self.combo = 0
        self.combo_t = 0.0
        #: The occupancy ledger: ``(lane, start, end)`` in absolute track
        #: distance for everything solid, and separately for everything hung
        #: over the track. Consulted before anything is placed, which is the
        #: whole of "nothing is ever drawn inside anything else".
        self._spans: list[tuple[int, float, float]] = []
        self._over: list[tuple[float, float]] = []
        #: The same idea for *moves* rather than for volumes: the stretch of
        #: track a jump or a slide commits the body to. Two obstacles can be
        #: metres apart and still be one unanswerable problem, because the
        #: answer to the first is not finished when the second arrives.
        self._acts: list[tuple[int, float, float]] = []
        #: Surfaces the body can stand on that are not the rails: ramps, and
        #: the trains they lead onto. Rebuilt per frame, and short.
        self._ridables: list[dict] = []
        #: how many seconds of this run have been spent on a train roof
        self.ride_time = 0.0
        self.mounts = 0

        # -- runner state ------------------------------------------------
        #: Position, velocity and what the body is currently committed to.
        #: The planner advances a copy of this to check its own work, so the
        #: rules of motion live in exactly one place.
        self.motion = plan.Motion(LANE_X)
        self.run_phase = 0.0
        self.cam_shake = 0.0
        #: The level the camera is riding at, lagging the body's own -- see
        #: :meth:`camera_pose`.
        self.cam_ground = 0.0
        self.impact_t = -1.0
        #: diagnostics the tests read: every frame in which the body box
        #: overlapped an obstacle box, and how deep it got.
        self.contacts = 0
        self.worst_penetration = 0.0
        self.last_contact: dict | None = None
        self.unsolvable = 0
        self.reflexes = 0
        #: counts down while a person is at the controls; the planner stands
        #: down for as long as it is above zero
        self.driven_t = 0.0

        #: The frame length last seen. Actions are booked at a time and fired
        #: on the next frame, so every solved window has to leave room for
        #: one frame of lateness -- at 18 m/s that is a quarter of a metre of
        #: arc, against a nine-centimetre clearance margin.
        self._dt = 1.0 / 60.0
        self._plan_at = -99.0
        self._lane_plan = plan.LanePlan(PLAN_STEP, [1] * 2)
        self._booked: list[tuple[float, str]] = []

        self._spawn_to_horizon()

    # -- motion, surfaced for the scene and the tests ---------------------

    @property
    def x(self) -> float:
        return self.motion.x

    @x.setter
    def x(self, value: float) -> None:
        self.motion.x = value

    @property
    def y(self) -> float:
        """Feet height above the running surface."""
        return self.motion.y

    @property
    def airborne(self) -> bool:
        return self.motion.airborne

    @property
    def roll_t(self) -> float:
        return self.motion.roll_t

    @property
    def riding(self) -> bool:
        """On a train roof -- above anything a ramp alone could account for."""
        return self.motion.ground > RAMP_LIP_H

    @property
    def lane(self) -> int:
        """The lane the *body* is in, which is what collision cares about."""
        return self.motion.lane()

    @property
    def target_lane(self) -> int:
        return self.motion.target_lane

    # -- generation -------------------------------------------------------
    #
    # Content is laid down one *set-piece* at a time, not one row at a time.
    # The row-at-a-time generator this replaced could only say "put an
    # obstacle here", and then had to defend itself with spacing rules; what
    # it produced was safe and repeated itself inside ten seconds -- measured
    # over twelve minutes of running, 7.6 hurdles a minute, 0.2 hoardings, and
    # the slide appearing about once every five minutes. It also could not
    # express a slalom, a train yard or a ramp onto a train roof *at all*,
    # because each of those is a decision about a stretch of track and the
    # corridor through it at the same time.

    def _lane_clear(self, row: int) -> int:
        """The lane guaranteed passable at ``row``.

        Read, never derived: whichever set-piece owns the row wrote it down.
        A yard that weaves the corridor between parked trains has to choose
        the weave and the trains together, or the guarantee is a guess. Rows
        outside what has been generated hold the nearest lane that has.
        """
        lane = self.corridor.get(row)
        if lane is not None:
            return lane
        if not self.corridor:
            return 1
        # Clamped to what has been *written*, which runs well ahead of
        # ``next_row``: a set-piece lays down a dozen rows at once, and
        # clamping to the spawn cursor instead reported the lane from twelve
        # rows back -- a corridor that appeared to jump two lanes in one row
        # the moment the cursor caught up.
        return self.corridor[max(self._first_row, min(self._last_row, row))]

    # -- the occupancy ledger ---------------------------------------------
    #
    # Everything solid records the stretch of track it occupies, per lane, in
    # absolute distance. Nothing is placed without asking first. Before this
    # existed, obstacles were spaced by counting rows -- which says nothing
    # about volumes, and a 25 m train against a 6 m row is a great many rows
    # of nothing being said. Measured over four runs, 9,731 frames in which
    # two obstacles were drawn inside each other, the worst 2.18 m deep:
    # trains through trains, and hoardings hung through the middle of them.

    def _clash(self, lane: int, a: float, b: float, pad: float = 0.0) -> bool:
        """Is anything solid already in this lane over this stretch?"""
        for ln, s, e in self._spans:
            if ln != ANY_LANE and lane != ANY_LANE and ln != lane:
                continue
            if a - pad < e and b + pad > s:
                return True
        return False

    def _reserve(self, lane: int, a: float, b: float) -> None:
        self._spans.append((lane, a, b))

    def _over_clash(self, a: float, b: float) -> bool:
        """Anything hung over the track here? Only a ride has to care: a
        gantry's soffit is 1 m above a standing runner and 0.7 m *below* one
        on a train roof."""
        return any(a < e and b > s for s, e in self._over)

    def _forget_spans(self) -> None:
        behind = self.travel - VIEW_BEHIND - 4.0
        self._spans = [s for s in self._spans if s[2] > behind]
        self._over = [s for s in self._over if s[1] > behind]
        self._acts = [s for s in self._acts if s[2] > behind]
        for row in [r for r in self.corridor if r * ROW < behind - ROW]:
            del self.corridor[row]
        self._first_row = min(self.corridor) if self.corridor else 0
        self._last_row = max(self.corridor) if self.corridor else 0

    def _may_spawn_train(self) -> bool:
        """No new train while one is sweeping the track the other way.

        An oncoming train crosses every row ahead of it, so it is potentially
        in *any* lane by the time it arrives. Adding a second train anywhere
        while that is true is how a runner ends up with no free lane.
        """
        return not any(e["kind"] == "train" and e["vel"] for e in self.entities)

    # -- placing one thing -------------------------------------------------

    def _add(self, e: dict, p: float) -> dict:
        e["d"] = p - self.travel
        self.entities.append(e)
        kind = e["kind"]
        if kind == "train":
            kind = "train-oncoming" if e["vel"] else "train-parked"
        self.spawned[kind] = self.spawned.get(kind, 0) + 1
        return e

    def _act_clash(self, lane: int, p: float) -> bool:
        """Would a move here run into one the body is still finishing?

        Each action reserves ``ACTION_SPAN`` of track either side of itself,
        and the reservations are tested against each other -- so two of them
        end up a whole slide apart *each*, which is what two consecutive moves
        actually cost. Testing a span against a *point* instead, as this did
        at first, buys only half of that: at top speed it leaves two slides
        0.47 s apart against a slide that takes 0.47 s, and the second one
        starts the instant the first ends with nothing in hand.
        """
        return any((ln == ANY_LANE or lane == ANY_LANE or ln == lane)
                   and p - ACTION_SPAN < b and p + ACTION_SPAN > a
                   for ln, a, b in self._acts)

    def _add_barrier(self, p: float, lane: int) -> bool:
        half = self._half["barrier"]
        if self._clash(lane, p - half, p + half, BODY_PAD):
            return False
        if self._act_clash(lane, p):
            return False
        self._reserve(lane, p - half, p + half)
        self._acts.append((lane, p - ACTION_SPAN, p + ACTION_SPAN))
        self._add({"kind": "barrier", "lane": lane}, p)
        return True

    def _add_hoarding(self, p: float) -> bool:
        half = self._half["hoarding"]
        if self._clash(ANY_LANE, p - half, p + half, BODY_PAD):
            return False
        if self._act_clash(ANY_LANE, p):
            return False
        self._reserve(ANY_LANE, p - half, p + half)
        self._acts.append((ANY_LANE, p - ACTION_SPAN, p + ACTION_SPAN))
        self._over.append((p - half, p + half))
        self._add({"kind": "hoarding"}, p)
        return True

    def _add_gantry(self, p: float) -> None:
        half = self._half["gantry"]
        self._over.append((p - half, p + half))
        self._add({"kind": "gantry"}, p)

    def _train_span(self, p: float, cars: int) -> tuple[float, float]:
        """Absolute track the train laid at ``p`` occupies, cab and all.

        Taken from the same measured boxes ``solid_box`` builds from -- a
        train is modelled along its own X and yawed a quarter turn, so its
        length and its width swap over, and typing the number in by hand is
        how it ends up half a car out.
        """
        cab, car = self._boxes["train_cab"], self._boxes["train_car"]
        return (p - cab.x1, p + (cars - 1) * TRAIN_CAR_LEN + car.x1)

    def _add_train(self, p: float, lane: int, cars: int, rng,
                   oncoming: bool = False, ride: bool = False,
                   sweep: float = 0.0, pad: float | None = None) -> dict | None:
        a, b = self._train_span(p, cars)
        if pad is None:
            pad = TRAIN_PAD
        # A moving train sweeps the track between here and the runner, so it
        # reserves that stretch rather than its own length. ``sweep`` is how
        # much: the set-piece that lays it knows how far it will get before
        # the two meet, and reserving the whole ninety-metre view instead --
        # which is what this did first -- means the lane is never empty enough
        # and the set-piece declines nine times out of ten.
        span = ((a - sweep, b) if oncoming else (a - pad, b + pad))
        if self._clash(lane, *span, BODY_PAD):
            return None
        # Even a moving train stays in its own lane; what makes it different is
        # that it sweeps *every row* of that lane between here and there, so
        # the stretch it reserves is the whole approach rather than its length.
        # Reserving all three lanes instead -- which the first version of this
        # did -- silently emptied the next ninety metres of track.
        self._reserve(lane, *span)
        return self._add({"kind": "train", "lane": lane, "cars": cars,
                          "vel": (self.speed * 0.55 + 4.5) if oncoming else 0.0,
                          "color": rng.choice(self.train_liveries),
                          "ride": ride, "ramp": None, "behind": None}, p)

    def _add_coins(self, p: float, n: float, lane: int, rng,
                   base: float = 0.55, arc: float = 0.0) -> None:
        count = max(2, int(n))
        for i in range(count):
            y = base + (arc * math.sin(math.pi * i / (count - 1)) if arc else 0.0)
            self._add({"kind": "coin", "lane": lane, "y": y, "taken": False},
                      p + (i - count / 2) * COIN_PITCH)

    # -- set-pieces --------------------------------------------------------

    def _spawn_to_horizon(self) -> None:
        while self.next_row * ROW < self.travel + VIEW_AHEAD:
            self._dress_row(self.next_row)
            if self.next_row not in self.corridor:
                self._begin_segment(self.next_row)
            self.next_row += 1

    def _begin_segment(self, row0: int) -> None:
        """Choose the next set-piece and lay it down whole.

        Never the same one twice running -- the single cheapest thing that
        stops a vocabulary of seven reading like a vocabulary of two -- and a
        set-piece that finds the track it wanted already occupied declines
        rather than forcing itself in, which is what keeps the ledger's
        promise cheap to keep.
        """
        rng = self.ctx.seed.stream(f"seg{row0}")
        table = [s for s in SEGMENT_TABLE if s[0] != self._last_segment]
        # Front-load the signature move. The strip is on screen for one
        # thinking turn -- often fifteen or twenty seconds -- and on the
        # ordinary weights the median time to a first mount is 19.7 s, so a
        # viewer saw the runner get onto a train on about a quarter of turns
        # and reasonably concluded the feature was not there. Opening on one
        # puts it about two and a half seconds in. Tried first rather than
        # merely weighted up: a heavier weight is still a dice roll, and this
        # is the one set-piece whose absence reads as a missing feature.
        forced = ("roofrun" if not self._last_segment
                  and rng.random() < OPENING_ROOFRUN else None)
        for _ in range(len(table) + 1):
            if forced is not None:
                name, lo, hi = next((e[0], e[1], e[2]) for e in SEGMENT_TABLE
                                    if e[0] == forced)
                forced = None
            else:
                total = sum(e[3] for e in table)
                if not table:
                    break
                pick = rng.random() * total
                for name, lo, hi, weight in table:
                    pick -= weight
                    if pick <= 0:
                        break
            mark = self._mark()
            used = getattr(self, f"_seg_{name}")(row0, rng.randint(lo, hi), rng)
            if used:
                self._last_segment = name
                self.segments[name] = self.segments.get(name, 0) + 1
                self._fill_corridor(row0, used)
                return
            self._rewind(mark, row0)
            table = [e for e in table if e[0] != name]
        self._seg_cruise(row0, 2, rng)
        self._last_segment = "cruise"
        self.segments["cruise"] = self.segments.get("cruise", 0) + 1
        self._fill_corridor(row0, 2)

    def _mark(self) -> tuple:
        """Everything a set-piece could have changed, before it starts."""
        return (len(self.entities), len(self._spans), len(self._over),
                len(self._acts), self._held)

    def _rewind(self, mark: tuple, row0: int) -> None:
        """Undo a set-piece that decided it could not fit.

        Declining has to leave no trace. When it did not, a segment that wrote
        a corridor and then gave up left those rows behind for the *next*
        segment to overwrite from a different starting lane -- and a corridor
        that steps two lanes in one row is a promise the body cannot keep.
        Every ledger here is append-only for exactly this reason: rolling one
        back is a truncation.
        """
        n_ent, n_spans, n_over, n_acts, held = mark
        del self.entities[n_ent:]
        del self._spans[n_spans:]
        del self._over[n_over:]
        del self._acts[n_acts:]
        self._held = held
        for row in [r for r in self.corridor if r >= row0]:
            del self.corridor[row]
        self._last_row = max(self.corridor) if self.corridor else 0

    def _set_lane(self, row: int, lane: int) -> None:
        self.corridor[row] = lane
        self._last_row = max(self._last_row, row)

    def _fill_corridor(self, row0: int, rows: int) -> None:
        prev = self._lane_clear(row0 - 1) if row0 else 1
        for row in range(row0, row0 + rows):
            if row in self.corridor:
                prev = self.corridor[row]
            else:
                self._set_lane(row, prev)

    def _walk_corridor(self, row0: int, rows: int, target: int) -> int:
        """Write a corridor from wherever it is toward ``target``.

        One lane at a time and never faster than :data:`CORRIDOR_HOLD` rows,
        because the guarantee is worthless if the guaranteed path is one the
        body cannot physically follow: at top speed a row is a third of a
        second and crossing a lane takes the best part of one.
        """
        lane = self._lane_clear(row0 - 1) if row0 else 1
        held = self._held
        for row in range(row0, row0 + rows):
            if lane != target and held >= CORRIDOR_HOLD:
                lane += 1 if target > lane else -1
                held = 1
            else:
                held += 1
            self._set_lane(row, lane)
        self._held = held
        return lane

    def _seg_cruise(self, row0: int, rows: int, rng) -> int:
        """The breath between set-pieces: a coin trail and a fenced-off side.

        Short, and never entirely empty. It is also the fallback when every
        other set-piece declines, so it has to work on any stretch of track --
        which is why the barrier here is offered rather than required.
        """
        lane = self._walk_corridor(row0, rows, self._lane_clear(row0 - 1) if row0 else 1)
        self._add_coins(row0 * ROW + ROW, rows * 3, lane, rng)
        for ln in (0, 1, 2):
            if ln != lane:
                self._add_barrier(row0 * ROW + ROW * (rows - 0.5), ln)
        return rows

    def _seg_hurdles(self, row0: int, rows: int, rng) -> int:
        """A rhythm of hurdles down one lane, with the sides fenced off.

        The corridor holds still, so every hurdle is a jump rather than a
        choice -- which is what makes it read as a rhythm.
        """
        lane = self._walk_corridor(row0, rows, self._lane_clear(row0 - 1) if row0 else 1)
        placed = 0
        p = row0 * ROW + ROW
        end = (row0 + rows) * ROW
        while p < end:
            if self._add_barrier(p, lane):
                placed += 1
                self._add_coins(p, 5, lane, rng, arc=1.35)
            for ln in (0, 1, 2):
                if ln != lane and rng.random() < 0.7:
                    self._add_barrier(p, ln)
            p += HURDLE_PITCH
        return rows if placed else 0

    def _seg_slalom(self, row0: int, rows: int, rng) -> int:
        """The corridor weaves, and the lane it leaves is closed behind it.

        Lane changes are the cheapest action the runner has and the one the
        old generator produced almost by accident -- 262 of them against 176
        jumps, most of them the planner drifting back toward a corridor that
        had wandered. Here they are the point of the set-piece.
        """
        lane = self._lane_clear(row0 - 1) if row0 else 1
        row = row0
        moves = 0
        while row < row0 + rows:
            target = 0 if lane == 2 else 2 if lane == 0 else rng.choice((0, 2))
            step = CORRIDOR_HOLD + 1
            lane_before = lane
            lane = self._walk_corridor(row, step, target)
            if lane != lane_before:
                moves += 1
                # close the lane behind the weave, so the move is forced
                self._add_barrier((row + step) * ROW, lane_before)
            row += step
        return (row - row0) if moves else 0

    def _seg_tunnel(self, row0: int, rows: int, rng) -> int:
        """Hoardings across the whole track: slide, run, slide.

        The slide was the rarest thing in the scene by a factor of thirty.
        Giving it a set-piece of its own is the only way to make a move that
        needs five clear rows either side of it appear more than once a run.
        """
        lane = self._walk_corridor(row0, rows, self._lane_clear(row0 - 1) if row0 else 1)
        placed = 0
        p = row0 * ROW + ROW
        end = (row0 + rows) * ROW
        while p < end:
            if self._add_hoarding(p):
                placed += 1
                self._add_coins(p, 6, lane, rng, base=0.42)
            p += HURDLE_PITCH
        return rows if placed else 0

    def _seg_yard(self, row0: int, rows: int, rng) -> int:
        """Parked trains, and a corridor threaded between them.

        Two lanes may be blocked at once here, which the old generator forbade
        -- rightly, while the corridor was a random walk it could not see. A
        set-piece knows where the corridor goes because it is the thing
        writing it down, so it can close everything else and still promise a
        way through.
        """
        if not self._may_spawn_train():
            return 0
        # The weave is decided in full *first*, and only then are the trains
        # laid against it. The other order looks equivalent and is not: a
        # train is three to five rows long, so one placed beside the corridor
        # where it stands today is squarely across it two rows later, and the
        # guaranteed lane turns out to have a train parked in it.
        lane = self._lane_clear(row0 - 1) if row0 else 1
        row = row0
        while row < row0 + rows - 2:
            # Always somewhere else. A weave that is allowed to pick the lane
            # it is already in is a yard the runner walks straight through
            # with its hands in its pockets, and it was the longest stretch of
            # nothing in the scene.
            target = rng.choice([ln for ln in (0, 1, 2)
                                 if ln != lane and abs(ln - lane) <= 1])
            hold = CORRIDOR_HOLD + rng.randint(1, 2)
            lane = self._walk_corridor(row, hold, target)
            self._add_coins(row * ROW + ROW, hold * 3, lane, rng)
            row += hold
        used = row - row0
        laid = 0
        for r in range(row0, row0 + used - 1):
            for ln in (0, 1, 2):
                if rng.random() > 0.38:
                    continue
                cars = rng.randint(2, 4)
                p = r * ROW + ROW * 0.5
                if not self._corridor_avoids(ln, *self._train_span(p, cars),
                                             row0, row0 + used):
                    continue
                if self._add_train(p, ln, cars, rng):
                    laid += 1
        return used if laid else 0

    def _corridor_avoids(self, lane: int, a: float, b: float,
                         row0: int, row1: int) -> bool:
        """Does the corridor stay out of ``lane`` for this whole stretch?

        Asked over the train's real length rather than the row it was spawned
        on, and with a row of slack each side so the body has somewhere to be
        while it crosses. A train whose tail would hang past ``row1`` is
        refused outright rather than checked: those rows belong to a set-piece
        that has not been chosen yet, so there is no corridor there to check
        against -- and asking anyway gets the answer for the last row that
        *was* written, which is how a train ends up laid across a weave that
        had not been decided when it was laid.
        """
        lo = int((a - ROW) // ROW)
        hi = int((b + ROW) // ROW)
        if lo < row0 or hi >= row1:
            return False
        return all(self._lane_clear(row) != lane for row in range(lo, hi + 1))

    def _seg_express(self, row0: int, rows: int, rng) -> int:
        """One train the other way down an otherwise open stretch.

        The train is placed by solving for where it will *meet* the runner and
        working backwards, rather than by dropping it at the end of the
        set-piece: it closes at half as much again as the runner runs, and
        generation happens a full view-length ahead of the body, so a train
        laid at the far end of these rows passes the runner several rows
        *before* they begin -- over track some earlier set-piece wrote the
        corridor for. Choosing its lane by "not the corridor here" therefore
        put an express straight down the lane the runner was following.

        Solved instead, the meeting lands in the middle of these rows, where
        this set-piece owns the corridor and can promise the lane is free.
        """
        if not self._may_spawn_train():
            return 0
        lane = self._lane_clear(row0 - 1) if row0 else 1
        far = rng.choice([ln for ln in (0, 1, 2) if ln != lane])
        cars = rng.randint(3, 5)
        meet = (row0 + rows * 0.6) * ROW
        closing = self.speed * 1.55 + 4.5
        # where it has to start so that it arrives there when the runner does
        p = self.travel + (meet - self.travel) * closing / self.speed
        a, b = self._train_span(p, cars)
        train = self._add_train(p, far, cars, rng, oncoming=True,
                                sweep=a - meet + 3 * ROW)
        if train is None:
            return 0
        self._walk_corridor(row0, rows, lane)
        self._add_coins(row0 * ROW + ROW, rows * 3, lane, rng)
        # Hurdles ahead of the meeting, in every lane the train is not in --
        # the corridor included, where they are a jump rather than a dodge.
        # Left out of the corridor they cost a runner that stays in it
        # nothing, and this set-piece was then eight seconds of empty track
        # waiting for a train, which is the longest idle stretch in the scene.
        for ln in (0, 1, 2):
            if ln == far:
                continue
            q = row0 * ROW + ROW * 1.5
            while q < meet - ROW:
                self._add_barrier(q, ln)
                q += HURDLE_PITCH
        return rows

    def _corridor_free(self, lane: int, a: float, b: float) -> bool:
        """Does the corridor stay out of ``lane`` over this stretch of track?

        Only rows that have been written are consulted -- an unwritten row
        belongs to a set-piece that has not been chosen yet, and the answer
        for it would really be the answer for the last row that *was*.
        """
        for row in range(int(a // ROW), int(b // ROW) + 1):
            if self.corridor.get(row, lane) == lane:
                return False
        return True

    def _seg_roofrun(self, row0: int, rows: int, rng) -> int:
        """A ramp onto a train roof, and a stretch of running along the top.

        The move the genre is named for. It was written once before and
        reverted, because the lane was chosen in one stage and the mount
        decided in another: when verification rejected the mount the runner
        was already committed to a lane with a train across it, and contacts
        went from zero to thousands.

        Here they are one decision. The ramp, the train, the corridor onto it,
        the clear lane to bail into and the clear sky over all of it are laid
        down together or not at all, and the leap is solved *at generation
        time* -- at both ends of the speed range, because the arc is rebuilt
        as the run accelerates -- before any of it is committed. What the
        planner then does with it is still checked by ``plan.verify``, which
        rolls the lane path and the take-off forward together over a world
        that includes the train; if that fails the train goes back to being an
        ordinary obstacle in a lane the corridor does not need, and the bail
        lane is empty by construction.
        """
        if not self._may_spawn_train():
            return 0
        lane = self._lane_clear(row0 - 1) if row0 else 1
        p_ramp = row0 * ROW + APPROACH_RUN
        p_lip = p_ramp + RAMP_LIP
        nose = self._boxes["train_cab"].x1
        # Laid out on paper first, and the whole convoy accepted or refused as
        # one. A chain that gets three trains in and finds the fourth blocked
        # is a roof that ends over a wall.
        chain: list[tuple[float, int, float, float]] = []
        p = p_lip + MOUNT_GAP + nose
        for i in range(rng.randint(*CONVOY_TRAINS)):
            cars = rng.randint(*CONVOY_CARS)
            a, b = self._train_span(p, cars)
            chain.append((p, cars, a, b))
            p = b + rng.uniform(*ROOF_GAP) + nose

        def measure() -> tuple[tuple[float, float], int]:
            span = (row0 * ROW, chain[-1][3] + DISMOUNT_RUN + ROW)
            return span, int(math.ceil((span[1] - row0 * ROW) / ROW))

        stretch, used = measure()
        # Too long for the stretch it was given: drop trains off the end
        # rather than declining. A convoy of two is still a convoy, and
        # refusing outright is how the signature move ends up rare -- the
        # length is drawn before the track it has to fit in is known.
        while used > rows + CONVOY_SLACK and len(chain) > 1:
            chain.pop()
            stretch, used = measure()
        if used > rows + CONVOY_SLACK:
            return 0
        end = chain[-1][3]
        if self._clash(ANY_LANE, *stretch, BODY_PAD) or self._over_clash(*stretch):
            return 0
        if not self._mount_reaches(MOUNT_GAP, chain[0][3] - chain[0][2],
                                   chain[0][1]):
            return 0
        # Every gap in the chain has to be one the leap crosses at *both* ends
        # of the speed range, for the same reason the mount does: a roof that
        # ends short of a jump the body has is not a hard puzzle, it is a fall.
        if any(not self._hop_reaches(chain[i][2] - chain[i - 1][3])
               for i in range(1, len(chain))):
            return 0
        prev = None
        for i, (p, cars, a, b) in enumerate(chain):
            train = self._add_train(p, lane, cars, rng, ride=True, pad=0.0)
            if train is None:                       # pre-checked; belt and braces
                return 0
            if prev is None:
                ramp = self._add({"kind": "ramp", "lane": lane}, p_ramp)
                train["ramp"] = ramp
            else:
                train["behind"] = prev
            prev = train
        # ...and the ride lane held for the whole convoy, gaps included, only
        # now that the trains are down. Reserved *first* it refuses its own
        # trains -- each one asks the ledger before it is placed -- and the
        # set-piece then rewinds every time, which is a roof run that never
        # once appeared in a hundred and twenty seconds of running.
        self._reserve(lane, stretch[0], stretch[1])
        self._over.append(stretch)
        self._walk_corridor(row0, used, lane)
        # A second line of trains alongside, which is what the reference looks
        # like at speed -- a canyon rather than a train. Never on the side
        # *between* the ride lane and the lane the runner bails into when the
        # mount is refused: that lane has to stay empty by construction, and it
        # is no use if the way to it is through a train.
        flank = self._flank_lane(lane, rng)
        if flank is not None:
            q = chain[0][2] + rng.uniform(2.0, 7.0)
            while q + nose < end - 10.0:
                cars = rng.randint(2, 3)
                a2, b2 = self._train_span(q + nose, cars)
                if b2 > end - 3.0:
                    break
                self._add_train(q + nose, flank, cars, rng, pad=0.0)
                q = b2 + rng.uniform(5.0, 11.0)
        # Hurdles down the lanes the convoy is not in. From the roof they cost
        # nothing and read as depth; on the ground they are the whole of what
        # a runner that did not get on has to do, and without them a convoy
        # nobody mounted is a hundred metres of empty track. Measured, that is
        # where this scene's dead air lives: the roof run owned 48 of the 81
        # idle seconds in twelve minutes of running.
        #
        # Barriers rather than anything solid, and that distinction is what
        # makes it safe: the bail lane has to stay *reachable*, not empty, and
        # a hurdle is something the body jumps rather than something it has to
        # be elsewhere for. ``_add_barrier`` refuses the flank lane by itself,
        # because the ledger already has trains in it.
        q = chain[0][2] + HURDLE_PITCH
        while q < end - ROW:
            for ln in (0, 1, 2):
                if ln != lane:
                    self._add_barrier(q, ln)
            q += HURDLE_PITCH
        # coins along the roof, which is also what tells a viewer it is a road
        roof = self._boxes["train_cab"].y1 - RAIL_TOP
        self._add_coins(row0 * ROW + ROW, 6, lane, rng)
        for i, (p, cars, a, b) in enumerate(chain):
            self._add_coins((a + b) * 0.5, (b - a) / COIN_PITCH * 0.8, lane,
                            rng, base=roof + 0.55)
            if i + 1 < len(chain):
                # ...and an arc over the gap, which is the reference's own way
                # of saying "this is a jump and this is where it goes".
                self._add_coins(0.5 * (b + chain[i + 1][2]), 5, lane, rng,
                                base=roof + 0.55, arc=1.5)
        return used

    def _flank_lane(self, lane: int, rng) -> int | None:
        """Which lane a convoy may stand a second line of trains in.

        The bail lane -- the one the lane search escapes into when the mount is
        refused -- has to be reachable, and from an outside lane the only way
        to the far side is through the middle. So a convoy in lane 1 may flank
        either side, and one in lane 0 or 2 may only flank the far side.
        """
        if rng.random() >= FLANK_CHANCE:
            return None
        if lane == 1:
            return rng.choice((0, 2))
        return 2 if lane == 0 else 0

    def _hop_reaches(self, gap: float) -> bool:
        """Does the leap off one roof land on the next one, at every speed?

        The leap is the mount arc, so its air time is fixed and its *span* is
        that time at whatever the body is running -- shortest at the bottom of
        the speed range, which is the end that decides. The body has to clear
        the gap and have its whole depth on the far roof, with the lead the
        take-off is taken with still to pay for.
        """
        if gap <= 0.0:
            return False
        for speed in (BASE_SPEED, TOP_SPEED):
            kin = plan.Kinematics.for_speed(speed)
            span = 2.0 * kin.mount_v0 / kin.gravity * speed
            if span < gap + 2.0 * self.body.half_d + HOP_MARGIN:
                return False
        return True

    def _mount_reaches(self, gap: float, roof_len: float, cars: int) -> bool:
        """Does the leap off the lip land on the roof, at every running speed?

        Asked here, at generation time, rather than discovered by the planner
        later: a ramp whose train is out of reach is not a hard puzzle, it is
        a promise the track cannot keep. Both ends of the speed range are
        checked because gravity and launch speed are rebuilt as the run
        accelerates -- the spans are meant to come out the same, and this is
        what would notice if they stopped.
        """
        rise = self._boxes["train_cab"].y1 - RAIL_TOP
        for speed in (BASE_SPEED, TOP_SPEED):
            kin = plan.Kinematics.for_speed(speed)
            window = plan.solve_mount(gap / speed, (gap + roof_len) / speed,
                                      rise, RAMP_LIP_H, kin)
            if window is None or not (window[0] <= 0.0 <= window[1]):
                return False
        return True

    # -- trackside dressing, independent of the set-pieces -----------------

    def _dress_row(self, row: int) -> None:
        """Furniture, and the city either side.

        It never touches the runner -- it sits outside the running width,
        which the collision test asserts -- but it is close to the camera and
        regular, and that is what the eye actually uses to read speed.
        """
        d0 = row * ROW - self.travel
        if row % 2 == 0:
            side = 1 if (row // 2) % 2 == 0 else -1
            self._add({"kind": "lamp", "x": side * 5.25,
                       "yaw": 0.0 if side < 0 else 180.0}, row * ROW + ROW * 0.5)
        if row % 7 == 3:
            side = 1 if (row // 7) % 2 == 0 else -1
            self._add({"kind": "signal", "x": side * 4.55,
                       "yaw": 0.0 if side < 0 else 180.0}, row * ROW + ROW * 0.25)
        srng = self.ctx.seed.stream(f"dress{row}")
        # A gantry is pure dressing: it is hung clear of the tallest thing the
        # runner can become on the rails. It is *not* clear of one on a train
        # roof, which is why it goes into the overhead ledger.
        if srng.random() < 0.08 and not self._over_clash(row * ROW - 3.0,
                                                        row * ROW + 3.0):
            self._add_gantry(row * ROW)
        for side in (-1, 1):
            crng = self.ctx.seed.stream(f"city{side}{row}")
            if crng.random() < 0.8:
                self._add({"kind": "building", "x": side * crng.uniform(10.5, 16.0),
                           "idx": crng.randrange(3),
                           "yaw": 90.0 if side < 0 else -90.0,
                           "tone": 0.55 + crng.random() * 0.5},
                          row * ROW + crng.uniform(0, ROW))
            if crng.random() < 0.22:
                self._add({"kind": "pillar", "x": side * crng.uniform(6.8, 8.4)},
                          row * ROW + crng.uniform(0, ROW))

    # -- collision geometry -----------------------------------------------

    def _lane_x(self, lane: int) -> float:
        return (lane - 1) * LANE_X

    def body_box(self) -> AABB:
        """The runner's own volume right now, in world space."""
        rolling = self.motion.rolling
        return AABB.around(self.motion.x, RAIL_TOP + self.motion.y, 0.0,
                           self.body.half_w, self.body.height(rolling),
                           self.body.depth(rolling))

    def _solids_near(self, reach: float) -> list[tuple[dict, AABB]]:
        """The entities close enough to matter, with their world boxes.

        Built once per frame and shared by everything that needs it. Most of
        what is on screen is scenery -- buildings, lamps, coins -- and boxing
        all of it three times a frame was the single largest cost in the
        scene, well ahead of anything that draws.
        """
        out = []
        for e in self.entities:
            kind = e["kind"]
            if kind not in SOLID_KINDS:
                continue
            d = e["d"]
            # A train's ``d`` is its near end; the rest of it trails away, so
            # it stays relevant long after that end has gone past.
            behind = -(e["cars"] * TRAIN_CAR_LEN + 4.0) if kind == "train" else -4.0
            if d > reach or d < behind:
                continue
            box = self.solid_box(e)
            if box is not None:
                out.append((e, box))
        return out

    def solid_box(self, e: dict, d: float | None = None) -> AABB | None:
        """World hitbox of an entity, or None when it is pure decoration.

        Built by the same ``placed`` call the draw uses, from the same measured
        model box -- so a hitbox cannot drift away from its picture without the
        scene passing two different transforms, which the tests check for.

        ``d`` overrides where the entity is, which is how the planner asks
        where a train's roof *will* be a second and a half from now without
        anybody having to copy the arithmetic somewhere else.
        """
        kind = e["kind"]
        d = e["d"] if d is None else d
        if kind == "barrier":
            return placed(self._boxes["barrier"],
                          (self._lane_x(e["lane"]), RAIL_TOP, -d))
        if kind == "hoarding":
            return placed(self._boxes["hoarding"], (0.0, RAIL_TOP, -d))
        if kind == "gantry":
            return placed(self._boxes["gantry"], (0.0, GANTRY_Y, -d))
        if kind == "train":
            x = self._lane_x(e["lane"])
            yaw = _train_yaw(e)
            box = placed(self._boxes["train_cab"], (x, 0.0, -d), yaw)
            tail = placed(self._boxes["train_car"],
                          (x, 0.0, -(d + (e["cars"] - 1) * TRAIN_CAR_LEN)), yaw)
            return AABB(min(box.x0, tail.x0), min(box.y0, tail.y0),
                        min(box.z0, tail.z0), max(box.x1, tail.x1),
                        max(box.y1, tail.y1), max(box.z1, tail.z1))
        return None

    def _closing_speed(self, e: dict) -> float:
        return self.speed + (e.get("vel") or 0.0)

    # -- what the body is standing on --------------------------------------

    def surface_at(self, t: float, x: float) -> float:
        """Height of the standing surface under the body, above ``RAIL_TOP``.

        The rails are zero; a ramp is part-way up its own slope; a train being
        ridden is its roof. ``t`` is seconds from now, so the same function
        answers "what am I standing on" for the live body and "what will the
        plan be standing on" for :func:`plan.verify` -- which is what makes a
        mount verified rather than merely intended. One description of the
        rules, checked and executed.
        """
        best = 0.0
        for e in self._ridables:
            top = self._ride_top(e, e["d"] - self.speed * t, x)
            if top > best:
                best = top
        return best

    def _ride_top(self, e: dict, d: float, x: float) -> float:
        """Height this one surface offers a body at ``x`` when it is ``d``
        ahead, or 0.0 when the body is not over it."""
        if e["kind"] == "ramp":
            lane_x = self._lane_x(e["lane"])
            box = self._boxes["ramp"]
            if not (box.z0 <= d <= box.z1):
                return 0.0
            if abs(x - lane_x) > RAMP_GRIP:
                return 0.0
            # The model is built lip-forward, so the slope climbs as the
            # ramp's own position passes the body: d = +RAMP_FOOT is the foot
            # of it and the climb is done by d = -RAMP_LIP, after which the
            # flat top holds the body at full height until the ramp is behind.
            return RAMP_LIP_H * max(0.0, min(1.0, (RAMP_FOOT - d) / RAMP_RUN))
        world = self.solid_box(e, d)
        # Asymmetric on purpose. The body gets onto a roof when its *centre*
        # is over the train, so that a mount cannot land it on thin air just
        # short of the nose; it stays on until its *back* has left, because
        # the body is over a metre deep and dropping it the moment its centre
        # crosses the far edge leaves the rear half hanging over the roof it
        # is no longer standing on -- five millimetres inside it, and counted.
        if world is None or not (world.z0 <= self.body.half_d
                                 and world.z1 >= 0.0):
            return 0.0
        if not (world.x0 < x < world.x1):
            return 0.0
        return world.y1 - RAIL_TOP

    def _refresh_ridables(self) -> None:
        """The short list of surfaces close enough to stand on."""
        self._ridables = [
            e for e in self.entities
            if (e["kind"] == "ramp" or (e["kind"] == "train" and e.get("ride")))
            and -TRAIN_CAR_LEN * (e.get("cars", 1) + 1) < e["d"] < RIDE_REACH]

    def _stand_y(self) -> float:
        """World height of the surface the body is standing on."""
        return RAIL_TOP + self.motion.ground

    def _threats(self) -> list[plan.Threat]:
        """Every obstacle inside the horizon, as lane/height/time facts."""
        out: list[plan.Threat] = []
        reach = PLAN_HORIZON * (self.speed * 2.0) + 8.0
        for e, box in self._solids_near(reach):
            if self.riding and self._ride_top(e, e["d"], self.motion.x) > 0.0:
                continue        # you cannot collide with what you stand on
            closing = self._closing_speed(e)
            half_len = (box.z1 - box.z0) * 0.5
            centre_d = -0.5 * (box.z0 + box.z1)

            def window(depth: float) -> tuple[float, float]:
                return plan.contact_window(centre_d, half_len, depth, closing)

            t0, t1 = window(self.body.half_d)
            if t1 <= 0.0 or t0 > PLAN_HORIZON:
                continue
            lanes = tuple(ln for ln in plan.LANES
                          if box.x0 < self._lane_x(ln) + self.body.half_w
                          and box.x1 > self._lane_x(ln) - self.body.half_w)
            if not lanes:
                continue
            mw = self._mount_window(e, box)
            link = e.get("behind") is not None
            th = plan.Threat(e["kind"], lanes, box.y0, box.y1,
                             max(0.0, t0), t1, x0=box.x0, x1=box.x1, ref=e,
                             mount_at=mw[0] if mw else None,
                             mount_to=mw[1] if mw else None, ride_link=link,
                             ride_ahead=mw is None and self._convoy_open(e))
            action = plan.classify(th, self.body, self.kin, self._stand_y())
            if action == "mount" or th.ride_ahead:
                out.append(th)
                continue
            if action == "roll":
                # A slide puts the legs out in front: the body is longer along
                # the track exactly while it is under the thing it is sliding
                # under, so the window it has to stay low for is longer too.
                t0, t1 = window(self.body.roll_half_d)
                th.t_enter, th.t_exit = max(0.0, t0), t1
            if self._already_cleared(th):
                continue
            th.hard = action == "hard"
            out.append(th)
        return out

    def _convoy_open(self, e: dict) -> bool:
        """Is this train part of a convoy the body is on, or about to get on?

        A convoy is one decision. Every gap in it was checked against the leap
        at both ends of the speed range before a single car was laid, so if the
        body gets onto the first train the whole chain is a road -- and if it
        does not, the whole chain is a wall and the lane search bails into the
        lane the set-piece left empty for exactly that. What there is no way to
        say without this is the middle case, which is the common one: standing
        on the rails, looking at a hundred metres of train in the lane with the
        ramp in front of it. Charged as a wall, the search leaves that lane
        before it ever reaches the ramp, and the mount it was avoiding is
        never offered at all.
        """
        node = e.get("behind")
        for _ in range(len(self.entities)):
            if node is None:
                return False
            if self._ride_top(node, node["d"], self.motion.x) > 0.0:
                return True                 # standing on it now
            if node.get("ramp") is not None:
                box = self.solid_box(node)
                return box is not None and self._ramp_mount_at(node, box) is not None
            node = node.get("behind")
        return False

    def _roof_hop(self, e: dict, box: AABB, lead: dict
                  ) -> tuple[float, float] | None:
        """When to leap from ``lead``'s roof onto this train's, as a window.

        Unlike a ramp, which is one instant, this is a stretch of time: the
        body is already at roof height and already going the right way, so any
        take-off far enough back to clear the gap and early enough to still
        have roof under the feet will do. Returning the window rather than an
        instant is what makes a busy scheduler a late leap instead of a fall.

        The stretch the roof being left is actually underfoot for is asked of
        :meth:`_ride_top` rather than derived from the train's length, because
        that is the function the body itself obeys -- a roof that holds the
        body until its *back* has left is not the same as one that holds it
        until its centre has, and a leap solved against the wrong one of those
        is short by most of a body.

        Asked of the *track* and not of the live body: the whole convoy has to
        be plannable before the body is on any of it, or the planner books the
        ramp mount, rolls forward, watches itself fall into the first gap, and
        throws the mount away in favour of never getting on at all. Which is
        exactly what it did -- 105 verifications failed on a train, and not one
        mount happened in four runs.
        """
        if not self._convoy_open(e):
            return None
        speed = max(1e-6, self.speed)
        lead_box = self.solid_box(lead)
        if lead_box is None:
            return None
        window = plan.solve_mount(-box.z1 / speed, -box.z0 / speed,
                                  box.y1 - RAIL_TOP, lead_box.y1 - RAIL_TOP,
                                  self.kin, self.kin.clearance_margin)
        if window is None:
            return None
        x = self._lane_x(e["lane"])
        first = last = None
        t = 0.0
        while t <= PLAN_HORIZON:
            if self._ride_top(lead, lead["d"] - speed * t, x) > 0.0:
                if first is None:
                    first = t
                last = t
            elif first is not None:
                break
            t += PLAN_STEP
        if last is None:
            return None
        latest = min(window[1], last)
        earliest = max(window[0], first, latest - HOP_LEAD * self.kin.mount_air_time)
        if earliest > latest:
            return None
        return (earliest, latest)

    def _mount_window(self, e: dict, box: AABB) -> tuple[float, float] | None:
        """Every take-off that gets the body onto this train, or None.

        Two ways up: off a ramp standing in front of it, which is one instant,
        or off the roof of the train it is chained behind, which is a stretch
        of time. Both come back in the same shape so that nothing downstream
        has to know which happened.
        """
        if e["kind"] != "train":
            return None
        lead = e.get("behind")
        if lead is not None:
            return self._roof_hop(e, box, lead)
        t = self._ramp_mount_at(e, box)
        return None if t is None else (t, t)

    def _ramp_mount_at(self, e: dict, box: AABB) -> float | None:
        """When to leave this train's ramp, if the leap works from here.

        There is exactly one moment: when the ramp's lip passes under the
        feet. Before it the body is still climbing and lower than the arc was
        solved for; after it there is no ramp left to leave. So this returns a
        time rather than a window, and nothing at all once the moment has gone
        -- at which point the train is an ordinary obstacle again, and the
        lane search is told so by the same field being None.
        """
        ramp = e.get("ramp")
        if ramp is None or self.riding:
            return None
        speed = max(1e-6, self.speed)
        t_lip = (ramp["d"] + RAMP_LIP) / speed
        if t_lip <= 0.0:
            # Past the lip, but the flat top is still underfoot and at the
            # same height -- so "now" is as good a take-off as the booked one
            # was. This is the other half of what the flat top is for: without
            # it the offer expires on the frame it is due.
            if self.motion.ground < RAMP_LIP_H - 1e-3:
                return None
            t_lip = 0.0
        # The offer stands only while the body can still be squarely in the
        # ramp's lane before it reaches the foot of it, with a crossing to
        # spare. This is the joint half of the decision: the moment the lane
        # can no longer be reached in time, the train goes back to being a
        # wall -- and it does so while there is still track left in which to
        # leave its lane. Offering the mount right up to the ramp instead is
        # what the reverted version of this did, and it is how a runner ends
        # up committed to a lane with a train across it.
        off = abs(self.motion.x - self._lane_x(ramp["lane"]))
        if off > RAMP_GRIP:
            t_foot = (ramp["d"] - RAMP_FOOT) / speed
            if (off / LANE_X + 1.0) * self.kin.lane_time > t_foot:
                return None
        closing = self._closing_speed(e)
        window = plan.solve_mount(-box.z1 / closing - t_lip,
                                  -box.z0 / closing - t_lip,
                                  box.y1 - RAIL_TOP, RAMP_LIP_H, self.kin,
                                  self.kin.clearance_margin)
        if window is None or not (window[0] <= 0.0 <= window[1]):
            return None
        return t_lip

    def _already_cleared(self, th: plan.Threat) -> bool:
        """Will the jump currently in progress carry the body over this?

        Without asking, the planner keeps seeing a hurdle it is already sailing
        over as a reason to swerve -- and swerving in mid-air is how the runner
        used to land on the barrier in the next lane.
        """
        if not self.motion.airborne:
            return False
        need = th.y1 - RAIL_TOP + self.kin.clearance_margin
        m = self.motion
        flight = m.flight(self.kin)
        for t in (th.t_enter, 0.5 * (th.t_enter + th.t_exit), th.t_exit):
            if t < 0.0:
                continue
            if m.ground + flight.offset_at(m.air_t + t, m.air_v0) < need:
                return False
        return True

    # -- being driven -----------------------------------------------------

    playable = True

    def control(self, intent) -> None:
        """Steer by hand for one frame.

        Lane changes go through the same commitment the planner uses -- a
        crossing finishes before another can start, and none begin in mid-air
        -- so a player gets the same body, not a teleporting one. The planner
        is suppressed while this is happening, including the reflex: a runner
        that keeps saving itself is not one you are really driving.
        """
        self.driven_t = DRIVEN_HOLD
        m = self.motion
        if m.settled() and not m.airborne and not m.rolling:
            if intent.left and m.target_lane > 0:
                m.target_lane -= 1
            elif intent.right and m.target_lane < 2:
                m.target_lane += 1
        if intent.jump:
            m.begin("jump", self.kin)
        elif intent.duck:
            m.begin("roll", self.kin)

    @property
    def driven(self) -> bool:
        return self.driven_t > 0.0

    # -- planning ---------------------------------------------------------

    def _corridor_lanes(self) -> list[int]:
        """The generator's clear lane at each step of the planning horizon."""
        steps = max(1, int(math.ceil(PLAN_HORIZON / LANE_STEP)))
        out = []
        for i in range(steps):
            ahead = self.travel + self.speed * (i * LANE_STEP)
            out.append(self._lane_clear(int(ahead / ROW)))
        return out

    def _pin_while_raised(self, lane_plan) -> None:
        """Hold the lane for as long as the body is up on something.

        ``Motion.advance`` freezes lateral movement while the body is raised
        -- that is the rule that stops it stepping sideways off a train roof
        -- so a lane change planned for the middle of a ride is one the body
        cannot make, and every threat scheduled against the lane it was
        supposed to be in by then goes unanswered. Measured over sixty runs of
        three minutes: 3,288 reports of no surviving plan against the 192 this
        scene had before convoys existed, and three fifths of them arrived
        while the body was on a roof.

        Only for as long as the ride lasts. Pinning the whole horizon was
        worse than not pinning at all (4,310): the tail of it is the runner
        back on the rails with the next set-piece in front of it, and that is
        a lane decision like any other.
        """
        if not self.riding or not lane_plan.lanes:
            return
        here = self.lane
        speed = max(1e-6, self.speed)
        x = self._lane_x(here)
        t = 0.0
        i = 0
        while i < len(lane_plan.lanes) and t <= PLAN_HORIZON:
            if self.surface_at(t, x) <= RAMP_LIP_H:
                break
            lane_plan.lanes[i] = here
            i += 1
            t += LANE_STEP

    def _replan(self) -> None:
        threats = self._threats()
        transit = max(1, int(round(self.kin.lane_time / LANE_STEP)))
        # When the body next becomes available: mid-jump or mid-slide, it is
        # committed, and anything scheduled inside that window would simply be
        # dropped at execution time and never noticed.
        busy_until = self.motion.time_to_free(self.kin,
                                              self.surface_at(0.0, self.motion.x))
        corridor = self._corridor_lanes()
        # Keep the attempt that survives longest, not the last one tried: a
        # later attempt is only better if marking something unavoidable
        # actually helped, and often it does not.
        best = (-1.0, self._lane_plan, [])
        #: Set when the only thing the plan could not answer is a leap further
        #: down the convoy the body is standing on. See below.
        deferred = False
        for _ in range(PLAN_ATTEMPTS):
            grid = plan.occupancy(threats, PLAN_HORIZON, LANE_STEP, corridor)
            # Plan onward from where the body is committed to arriving, not
            # from where it happens to be mid-slide.
            lane_plan = plan.choose_lanes(grid, self.motion.target_lane,
                                          LANE_STEP, transit)
            self._pin_while_raised(lane_plan)
            booked, unsolved = plan.schedule_vertical(
                threats, lane_plan, self.body, self.kin, self._stand_y(),
                busy_until, self._dt, self.riding)
            # A leap onto a roof three trains further down the convoy that
            # will not fit in this horizon is not a plan that failed: it is a
            # decision that is not due yet, and the re-solve a tenth of a
            # second from now will make it from closer up. Counting those as
            # unsolved stopped the plan being verified at all for the whole
            # length of every convoy.
            if self.riding:
                unsolved = [th for th in unsolved if not th.ride_link]
            if not unsolved:
                # The two halves of the plan are each self-consistent; that is
                # not the same as the body surviving them together. Run it --
                # over a world that includes the train the plan may intend to
                # land on, which is what makes the lane choice and the mount
                # one decision rather than two that have to agree.
                failure = plan.verify(self.motion, lane_plan, booked, threats,
                                      self.body, self.kin, PLAN_HORIZON,
                                      PLAN_STEP, RAIL_TOP, self.surface_at)
                if failure is None:
                    best = (float("inf"), lane_plan, booked)
                    break
                if self.riding and failure[0].ride_link:
                    # The body ran off the end of the *second* roof in the
                    # rolled-forward world, because only one leap fits in a
                    # schedule at a time and the horizon holds two or three
                    # gaps. That is not a plan with no answer, it is a
                    # decision the re-solve a tenth of a second from now will
                    # make from closer up -- and the leap it will book is one
                    # the generator checked against the physics before it laid
                    # the convoy down. Take the plan and stop counting it as a
                    # failure; every one of the 3,288 "no answer" reports this
                    # scene picked up when convoys arrived was this.
                    best = (float("inf"), lane_plan, booked)
                    deferred = True
                    break
                unsolved = [failure[0]]
                if failure[1] > best[0]:
                    best = (failure[1], lane_plan, booked)
            elif best[0] < 0.0:
                best = (0.0, lane_plan, booked)
            # Whatever the plan could not answer becomes something to route
            # around rather than something to walk into -- except the rest of
            # the convoy the body is currently standing on, which there is no
            # routing around: it is the floor.
            for th in unsolved:
                if self.riding and th.ride_link:
                    continue
                th.hard = True
        survives, lane_plan, booked = best
        self._lane_plan = lane_plan
        self._booked = [(self.elapsed + t, a) for t, a in booked]
        #: How often no plan survived even the part of the horizon that will
        #: actually be flown before the next re-solve. Non-zero here is the
        #: honest early warning that the generator is producing situations
        #: with no answer -- long before it shows up as a body inside a train.
        if survives < COMMIT_WINDOW and not deferred:
            self.unsolvable += 1

    # -- simulation -------------------------------------------------------

    def update(self, dt: float) -> None:
        self._dt = dt
        # Speed is the variable every contact window is solved against, so a
        # hit deliberately does *not* change it. Dropping the speed on impact
        # invalidates the plan in flight -- everything arrives later than the
        # jumps were booked for -- and the second contact that causes drops it
        # again. The stumble is expressed in the pose and the camera instead.
        self.speed = min(TOP_SPEED, BASE_SPEED
                         + (TOP_SPEED - BASE_SPEED) * (self.elapsed / RAMP_SECONDS))
        # Moves are sized against the current speed, so they always span about
        # the same stretch of track. A jump in flight keeps the arc it left
        # the ground with.
        self.kin = plan.Kinematics.for_speed(self.speed)
        self.motion.spacing = LANE_X
        step = self.speed * dt
        self.travel += step
        self.score += self.speed * dt * 3.2
        # Stride cadence in CYCLES per second. A sprint is ~1.7 strides/s;
        # anything much faster aliases at 30-60fps into limb flicker.
        self.run_phase += dt * (1.35 + self.speed * 0.038)
        self.cam_shake = max(0.0, self.cam_shake - dt * 3.0)
        self.cam_ground += ((self.motion.ground - self.cam_ground)
                            * min(1.0, dt * CAM_CLIMB))

        for e in self.entities:
            e["d"] -= step
            if e["kind"] == "train" and e["vel"]:
                e["d"] -= e["vel"] * dt
        # A train is only *at* its near end; the rest of it trails away behind
        # and has to stay drawn until the last car has gone past.
        self.entities = [e for e in self.entities
                         if e["d"] > -VIEW_BEHIND - (e["cars"] * TRAIN_CAR_LEN
                                                     if e["kind"] == "train" else 0.0)]
        self._forget_spans()
        self._spawn_to_horizon()
        self._refresh_ridables()

        self.driven_t = max(0.0, self.driven_t - dt)
        # Fire what is already due *before* re-solving. A re-solve replaces the
        # booking list wholesale, and a mount is a one-instant action -- there
        # is exactly one moment the ramp's lip is underfoot -- so a re-solve
        # landing on that instant threw the take-off away and the runner ran
        # off the end of its own launcher into the side of the train.
        if not self.driven:
            while self._booked and self._booked[0][0] <= self.elapsed:
                _, action = self._booked.pop(0)
                self.motion.begin(action, self.kin)
        else:
            self._booked.clear()
        if not self.driven and self.elapsed - self._plan_at >= PLAN_EVERY:
            self._plan_at = self.elapsed
            self._replan()
        # One pass over what is close enough to matter, shared by the reflex
        # and the contact check.
        near = self._solids_near(REFLEX_WINDOW * self.speed + 6.0)
        if not self.driven:
            self._reflex(near)

        # While a person is driving, the lane they chose stands: feeding the
        # planner's lane in here would quietly steer back out of it.
        desired = (self.motion.target_lane if self.driven
                   else self._lane_plan.lane_at(
                       max(0.0, self.elapsed - self._plan_at)))
        was_airborne = self.motion.airborne
        was_ground = self.motion.ground
        self.motion.advance(dt, self.kin, desired,
                            self.surface_at(0.0, self.motion.x))
        if was_airborne and not self.motion.airborne:
            self.cam_shake = 0.5 if self.motion.ground <= was_ground else 0.35
        # "Riding" means a train roof, not the ramp on the way up to one --
        # and the leap from one roof to the next counts, because the body's
        # standing height through it is the roof it left. Excluding the air
        # was the old reading and it undercounted a convoy by a third: the
        # gaps are the part of a roof run the viewer is watching.
        if self.riding:
            self.ride_time += dt
        if self.motion.ground > RAMP_LIP_H >= was_ground:
            self.mounts += 1

        if self.impact_t >= 0:
            self.impact_t += dt
            if self.impact_t >= IMPACT_TIME:
                self.impact_t = -1.0

        self._collect_coins()
        self._resolve_contacts(near)
        self.burst.update(dt)
        if self.combo_t > 0.0:
            self.combo_t -= dt
            if self.combo_t <= 0.0:
                self.combo = 0

    def _reflex(self, near: list[tuple[dict, AABB]]) -> None:
        """Jump or slide when this instant is the moment to, plan or no plan.

        The planner decides a lane and a set of take-offs in two stages, and
        for a tenth of a second at a time they can disagree about which lane
        the body will be in when a hurdle arrives -- so no take-off is booked
        for it, and by the time they agree the window has closed. This is the
        reflex a player has and a schedule does not: look at what is actually
        in front of the body, and if right now is a valid moment to leave the
        ground, leave the ground.

        It cannot fire a move that would not work: the take-off window comes
        from the same solver the planner uses, and firing requires *now* to be
        inside it.
        """
        m = self.motion
        if m.airborne or m.rolling:
            return
        if self._booked and self._booked[0][0] - self.elapsed <= REFLEX_WINDOW:
            # A take-off is already booked for what is in front of the body.
            # The reflex exists for the case where none is, and firing anyway
            # replaces a take-off solved for the middle of its window with one
            # at the very edge of it -- measured, that is a jump whose feet
            # came down three millimetres inside the hurdle it had cleared.
            return
        body = self.body_box()
        for e, box in near:
            if box.x1 <= body.x0 or box.x0 >= body.x1:
                continue
            closing = self._closing_speed(e)
            half_len = (box.z1 - box.z0) * 0.5
            centre_d = -0.5 * (box.z0 + box.z1)
            t0, t1 = plan.contact_window(centre_d, half_len,
                                         self.body.half_d, closing)
            if t1 <= 0.0 or t0 > REFLEX_WINDOW:
                continue
            mw = self._mount_window(e, box)
            th = plan.Threat(e["kind"], (self.lane,), box.y0, box.y1,
                             max(0.0, t0), t1, x0=box.x0, x1=box.x1, ref=e,
                             mount_at=mw[0] if mw else None,
                             mount_to=mw[1] if mw else None,
                             ride_link=e.get("behind") is not None)
            action = plan.classify(th, self.body, self.kin, self._stand_y())
            if action == "mount":
                # The last chance to get onto a train the plan meant to ride.
                # One frame wide, and checked every frame: the arc was solved
                # from the *lip's* height, so leaving even a tenth of a second
                # early leaves from 40 cm lower down the slope and arrives
                # through the side of the roof rather than on top of it.
                # ...and never off flat ground. A roof-to-roof leap offered
                # to a body that is not on the first roof is a jump with a
                # mount's launch speed taken from the rails, and it lands ten
                # metres later on whatever is there.
                if th.mount_at <= self._dt and not (th.ride_link
                                                    and not self.riding):
                    self.motion.begin("mount", self.kin)
                    self.reflexes += 1
                    return
                continue
            if action == "roll":
                t0, t1 = plan.contact_window(centre_d, half_len,
                                             self.body.roll_half_d, closing)
                th.t_enter, th.t_exit = max(0.0, t0), t1
                window = plan.solve_roll(th, self.kin, self._dt)
            elif action == "jump":
                window = plan.solve_jump(th, self.body, self.kin,
                                         self._stand_y(), self._dt)
            else:
                continue
            if window and window[0] <= 0.0 <= window[1]:
                self.motion.begin(action, self.kin)
                self.reflexes += 1
                return

    def _collect_coins(self) -> None:
        for e in self.entities:
            if e["kind"] != "coin" or e["taken"] or abs(e["d"]) >= 0.6:
                continue
            if (abs(self._lane_x(e["lane"]) - self.motion.x) < 0.9
                    and abs(e["y"] - 0.4 - self.motion.y) < 1.1):
                e["taken"] = True
                self.coins += 1
                self.score += 25
                self.combo += 1
                self.combo_t = COMBO_HOLD
                self.burst.spawn(self.x, RAIL_TOP + e["y"], -e["d"],
                                 (255, 215, 80), count=8, rng=self.rng)

    def _resolve_contacts(self, near: list[tuple[dict, AABB]]) -> None:
        """Last line of defence: if a body box is inside an obstacle box, take
        the hit and push back out, rather than letting the mesh pass through.

        The planner is supposed to make this unreachable, and the tests assert
        it stays unreached over long runs -- but "assert it never happens" and
        "behave sanely when it does" are different jobs, and a background toy
        that occasionally shows a runner gliding through a train is worse than
        one that occasionally shows a runner clipping a train and stumbling.
        """
        body = self.body_box()
        for e, box in near:
            if not body.overlaps(box):
                continue
            depth = body.penetration(box)
            # Standing on a train roof puts the feet at exactly the roof's
            # height, and floating point does not do "exactly". An overlap
            # this shallow is two faces meeting, which is what standing *is*.
            if depth <= CONTACT_EPS:
                continue
            self.contacts += 1
            self.worst_penetration = max(self.worst_penetration, depth)
            #: what was hit, captured before the push-out moves anything
            self.last_contact = {
                "t": self.elapsed, "kind": e["kind"], "lane": e.get("lane"),
                "d": e["d"], "depth": depth, "x": self.x, "y": self.y,
                "body_lane": self.lane, "target": self.target_lane,
                "airborne": self.airborne, "roll_t": self.roll_t,
                "speed": self.speed, "box": box, "body": body,
            }
            if self.impact_t < 0:
                self.impact_t = 0.0
                self.cam_shake = 1.0
                self.burst.spawn(self.x, RAIL_TOP + self.y + 0.7, 0.0,
                                 self.palette.hazard, count=12, rng=self.rng)
            # separate along the shallowest axis so nothing is left inside
            if box.x1 > body.x0 and box.x0 < body.x1:
                if self.x < box.center_x:
                    self.x = min(self.x, box.x0 - self.body.half_w - 0.01)
                else:
                    self.x = max(self.x, box.x1 + self.body.half_w + 0.01)
            break

    # -- drawing ----------------------------------------------------------

    def _fog(self, d: float, alpha: int = 255):
        f = max(0.0, min(1.0, d / FOG_FAR))
        f = f * f * (3 - 2 * f)
        return rl.rgba(rl.mix_rgb((255, 255, 255), self.palette.fog, f), alpha)

    def camera_pose(self) -> tuple[tuple[float, float, float],
                                   tuple[float, float, float], float]:
        """Where the chase camera is, what it looks at, and how wide.

        Split out of :meth:`draw` so ``tools/runner_probe.py`` can project the
        lanes onto the frame without rendering one -- "can you see all three
        lanes" is a question about this function, and it is the question a
        9:16 strip most often answers badly.
        """
        # two footfalls per stride cycle drive the bob
        bob = math.sin(self.run_phase * math.tau * 2) * 0.045 * (self.speed / TOP_SPEED)
        shake = (math.sin(self.elapsed * 43.0) * 0.05
                 + math.sin(self.elapsed * 61.0) * 0.03) * self.cam_shake
        # Ride directly behind the runner: with the camera between lanes, a
        # passing train in the next lane would wipe across the whole frame.
        # Height is measured from the surface the *camera* is over, not from
        # the rails. On a train roof the two differ by two and a half metres,
        # and a camera that stays down on the ballast frames the roof rather
        # than the run: the runner ends up a small figure at the top of the
        # frame with 60% of the picture given over to orange sheet metal.
        # The lag is not a smoothing trick either -- the camera is seven
        # metres behind the body, so it genuinely arrives at each change of
        # level a little later.
        floor = self.cam_ground
        air = self.y - floor
        return ((self.x * 0.92 + shake, CAM_HEIGHT + floor + bob + air * 0.28,
                 CAM_BACK),
                (self.x, CAM_LOOK_Y + floor + bob * 0.5 + shake * 0.6
                 + air * 0.3, CAM_LOOK_Z),
                fov_for_speed(self.speed))

    def draw(self) -> None:
        pal = self.palette
        self.sky.draw(self.elapsed)

        cam = self.camera
        position, target, fovy = self.camera_pose()
        cam.position = position
        cam.target = target
        cam.fovy = fovy

        rl.BeginMode3D(cam[0])

        # ground plane under everything; fog handled by the horizon haze
        rl.DrawPlane((0, -0.05, -30), (240, 160), rl.rgba(pal.ground, 255))
        # Submitted here rather than left in rlgl's batch, which would not be
        # drawn until EndMode3D -- i.e. after every model in the scene, losing
        # the depth test to all of them. See rl.flush.
        rl.flush()

        # track tiles, snapped to the row grid
        first = int((self.travel - 8) / ROW)
        for k in range(first, first + int((VIEW_AHEAD + 16) / ROW)):
            d = k * ROW - self.travel + ROW / 2
            if d < -VIEW_BEHIND:
                continue
            rl.DrawModelEx(self.track.model, (0, 0, -d), (0, 1, 0), 0.0,
                           (1, 1, 1), self._fog(d))
            # lineside fences ride the same grid
            for side in (-1, 1):
                rl.DrawModelEx(self.fence.model, (side * 6.3, 0, -d), (0, 1, 0), 90.0,
                               (1, 1, 1), self._fog(d))
                rl.DrawModelEx(self.fence.model, (side * 6.3, 0, -d + 3.0), (0, 1, 0), 90.0,
                               (1, 1, 1), self._fog(d))

        # far-to-near keeps alpha'd glows honest without a sort pass
        for e in sorted(self.entities, key=lambda e: -e["d"]):
            d = e["d"]
            if d > VIEW_AHEAD:
                continue
            fog = self._fog(d)
            kind = e["kind"]
            if kind == "building":
                b = self.buildings[e["idx"]]
                t = e["tone"]
                b.recolor({"wall": rl.scale_rgb(pal.structure, t),
                           "trim": rl.scale_rgb(pal.structure, t * 0.7),
                           "window": pal.window_lit if pal.is_dark
                           else rl.mix_rgb(pal.sky_bottom, (255, 255, 255), 0.35)})
                rl.DrawModelEx(b.model, (e["x"], 0, -d), (0, 1, 0), e["yaw"], (1, 1, 1), fog)
            elif kind == "pillar":
                rl.DrawModelEx(self.pillar.model, (e["x"], 0, -d), (0, 1, 0), 0, (1, 1, 1), fog)
            elif kind == "lamp":
                rl.DrawModelEx(self.lamp.model, (e["x"], 0, -d), (0, 1, 0),
                               e["yaw"], (1, 1, 1), fog)
            elif kind == "signal":
                self.signal.recolor({"stripe": pal.hazard})
                rl.DrawModelEx(self.signal.model, (e["x"], 0, -d), (0, 1, 0),
                               e["yaw"], (1, 1, 1), fog)
            elif kind == "train":
                self._draw_train(e, fog)
            elif kind == "barrier":
                self.barrier.recolor({"stripe": pal.hazard})
                rl.DrawModelEx(self.barrier.model,
                               (self._lane_x(e["lane"]), RAIL_TOP, -d),
                               (0, 1, 0), 0, (1, 1, 1), fog)
            elif kind == "ramp":
                self.ramp.recolor({"stripe": pal.hazard})
                rl.DrawModelEx(self.ramp.model,
                               (self._lane_x(e["lane"]), RAIL_TOP, -d),
                               (0, 1, 0), 0, (1, 1, 1), fog)
            elif kind == "hoarding":
                if d < -2.0:
                    continue
                self.hoarding.recolor({"sign": pal.accent2})
                rl.DrawModelEx(self.hoarding.model, (0, RAIL_TOP, -d), (0, 1, 0), 0,
                               (1, 1, 1), fog)
            elif kind == "gantry":
                if d < -1.5:
                    continue  # passing the camera plane: never wipe the frame
                self.gantry.recolor({"sign": self.sign_color})
                rl.DrawModelEx(self.gantry.model, (0, GANTRY_Y, -d), (0, 1, 0), 0,
                               (1, 1, 1), fog)
            elif kind == "coin" and not e["taken"]:
                x = self._lane_x(e["lane"])
                y = RAIL_TOP + e["y"] + math.sin(self.elapsed * 3 + d) * 0.06
                rl.DrawModelEx(self.coin.model, (x, y, -d), (0, 1, 0),
                               (self.elapsed * 220 + d * 40) % 360,
                               (0.55, 0.55, 0.55), fog)

        self._draw_runner()
        for e in self.entities:
            if e["kind"] == "coin" and not e["taken"] and e["d"] < 30:
                glow_billboard(self.camera, self._lane_x(e["lane"]),
                               RAIL_TOP + e["y"], -e["d"], 0.6, (255, 200, 60), 55)
            elif e["kind"] == "lamp" and pal.is_dark and e["d"] < 60:
                # the lamp head hangs over the track; light it from there
                glow_billboard(self.camera, e["x"] + (0.78 if e["yaw"] else -0.78),
                               4.05, -e["d"], 2.4, (255, 232, 170), 90)
            elif e["kind"] == "train" and e["vel"] and pal.is_dark and e["d"] < 70:
                # oncoming headlights punching through the dark, on the nose --
                # which faces us, so they sit at the near end of the hull
                x_t = self._lane_x(e["lane"])
                for side in (-1, 1):
                    glow_billboard(self.camera, x_t + side * 0.6, 1.05,
                                   -e["d"] + 2.6, 1.6, (255, 235, 170), 120)
        self.burst.draw(self.camera)
        rl.EndMode3D()

        self._draw_speed_lines()
        self.weather.draw(self.elapsed)
        self._draw_hud()

    def _draw_speed_lines(self) -> None:
        """Streaks raked past the edges of the frame once the run is quick.

        Screen space, and only near the sides, so they read as motion past the
        lens rather than as objects in the world. Fades in over the top third
        of the speed range -- at walking pace they would just be noise.
        """
        t = (self.speed - BASE_SPEED) / (TOP_SPEED - BASE_SPEED)
        t = max(0.0, (t - 0.45) / 0.55)
        if t <= 0.0:
            return
        rl.BeginBlendMode(rl.BLEND_ADDITIVE)
        for i in range(14):
            phase = (self.elapsed * (2.4 + (i % 5) * 0.5) + i * 0.137) % 1.0
            y = phase * (self.height + 260) - 130
            side = -1 if i % 2 else 1
            x = self.width * (0.5 + side * (0.30 + (i % 7) * 0.028))
            length = 60 + (i % 4) * 44
            alpha = int(46 * t * math.sin(math.pi * min(1.0, phase * 1.6)))
            if alpha <= 0:
                continue
            rl.DrawLineEx((x, y), (x + side * 12, y + length), 2.0,
                          (255, 255, 255, alpha))
        rl.EndBlendMode()

    def _draw_train(self, e: dict, fog) -> None:
        x = self._lane_x(e["lane"])
        self.train_cab.recolor({"body": e["color"]})
        self.train_car.recolor({"body": e["color"]})
        yaw = _train_yaw(e)
        d = e["d"]
        rl.DrawModelEx(self.train_cab.model, (x, 0, -d), (0, 1, 0), yaw,
                       (1, 1, 1), fog)
        for i in range(1, e["cars"]):
            rl.DrawModelEx(self.train_car.model, (x, 0, -(d + i * TRAIN_CAR_LEN)),
                           (0, 1, 0), yaw, (1, 1, 1), self._fog(d + i * TRAIN_CAR_LEN))

    def _draw_runner(self) -> None:
        ch = self.character
        ch.recolor(self.outfit)

        if self.impact_t >= 0:
            # a stagger: the roll clip held near its folded frames reads as a
            # body absorbing a hit, which is what just happened
            ch.pose("roll", 0.30 + 0.12 * math.sin(self.impact_t * 26.0))
        elif self.motion.airborne:
            # Through the clip in proportion to *this* arc, not to an ordinary
            # jump's: a mount off a ramp hangs half as long again, and a fall
            # off the back of a train has no rise at all, so a fixed divisor
            # runs the take-off and the landing at the wrong moments.
            m = self.motion
            air = max(0.2, 2.0 * m.air_v0 / m.flight(self.kin).gravity)
            ch.pose("jump", min(0.999, m.air_t / air))
        elif self.motion.rolling:
            ch.pose("roll", self.motion.roll_t
                    / (self.motion.roll_dur or self.kin.roll_time))
        else:
            ch.pose("run", self.run_phase % 1.0)

        lean = (self._lane_x(self.lane) - self.x) * -14.0
        if self.impact_t >= 0:
            lean += 16.0 * math.sin(self.impact_t * 18.0) * (1.0 - self.impact_t / IMPACT_TIME)
        transform = rl.MatrixMultiply(
            rl.MatrixRotateY(math.radians(90)),
            rl.MatrixRotateZ(math.radians(lean)),
        )
        ch.model.transform = transform
        # The shadow belongs on whatever is under the feet, not on the rails:
        # a runner two and a half metres up on a train roof with its shadow
        # still down on the ballast reads as a body floating in space.
        floor = RAIL_TOP + self.surface_at(0.0, self.x)
        blob_shadow(self.x, floor + 0.04, 0.0, 0.62,
                    alpha=int(110 * max(0.0, 1.0 - (RAIL_TOP + self.y - floor) / 3.0)))
        rl.DrawModelEx(ch.model, (self.x, RAIL_TOP + self.y, 0), (0, 1, 0), 0.0,
                       (CHAR_SCALE, CHAR_SCALE, CHAR_SCALE), rl.WHITE4)

    def _draw_hud(self) -> None:
        pal = self.palette
        text(f"{int(self.score):06d}", self.width - 14, 12, 26, pal.ink, anchor="topright")
        # coin counter with a little gold disc
        rl.DrawCircle(self.width - 66, 58, 7, (255, 205, 60, 255))
        rl.DrawCircle(self.width - 66, 58, 4, (255, 235, 140, 255))
        text(f"{self.coins}", self.width - 14, 48, 20, (255, 215, 90), anchor="topright")
        # a run of pickups is worth saying out loud
        if self.combo >= 4 and self.combo_t > 0.0:
            fade = min(1.0, self.combo_t / (COMBO_HOLD * 0.5))
            size = 18 + min(8, self.combo // 4)
            text(f"x{self.combo}", self.width - 16, 76, size,
                 rl.mix_rgb(pal.ink, (255, 214, 92), fade), anchor="topright")


# ---------------------------------------------------------------------------
# Geometry helpers -- all of it measured, none of it typed in
# ---------------------------------------------------------------------------

#: Vertical field of view at the bottom and the top of the speed range. Opening
#: it up as the run accelerates is the oldest speed cue there is.
FOV_SLOW = 56.0
FOV_FAST = 62.0
#: Where the chase camera sits relative to the runner, and what it aims at.
CAM_BACK = 6.8
CAM_HEIGHT = 3.5
CAM_LOOK_Y = 1.6
CAM_LOOK_Z = -4.6
#: How fast the camera climbs to a new level, per second. Slow enough that a
#: mount reads as the world dropping away, quick enough to have arrived by the
#: time the runner is a car and a half along the roof.
CAM_CLIMB = 3.2


def fov_for_speed(speed: float) -> float:
    """Vertical FOV at a running speed.

    Exposed rather than inlined in ``draw`` so ``tools/runner_probe.py`` can
    report what the camera actually shows without rendering a frame -- and so
    the horizontal FOV, which is what a 9:16 strip is short of, is computable.
    """
    t = (speed - BASE_SPEED) / (TOP_SPEED - BASE_SPEED)
    return FOV_SLOW + (FOV_FAST - FOV_SLOW) * max(0.0, min(1.0, t))


def _train_yaw(e: dict) -> float:
    """Which way the cab's nose points.

    The cab is modelled with its nose at +X. A yaw of 270 sends +X to +Z, i.e.
    toward the camera; 90 sends it away down the track. So a train coming the
    other way shows its nose and headlights, and one we are running up behind
    shows its tail -- which is the opposite of what this used to do, because
    the sign of a Y rotation is easy to get backwards and nothing checked it.
    ``tests/test_collision.py`` now pins the convention against raylib's own
    matrix.
    """
    return 270.0 if e.get("vel") else 90.0


def _body_profile() -> plan.Body:
    """The runner's collision volume, from the character's own posed meshes.

    The character model is drawn yawed 90 degrees and scaled, so its recorded
    model-space extents are pushed through exactly that transform here.

    The roll is measured over only the stretch of the clip where the body is
    actually down (:attr:`Kinematics.roll_low_from` to ``roll_low_to``), which
    is the same window :func:`runnerplan.solve_roll` schedules the slide to
    cover. Measuring the whole clip instead reports the standing height, since
    a roll starts and finishes upright -- and a runner that believes ducking
    changes nothing will never duck.
    """
    kin = plan.Kinematics()
    scale = (CHAR_SCALE, CHAR_SCALE, CHAR_SCALE)

    def world(clip: str, t0: float = 0.0, t1: float = 1.0):
        return placed(assets.clip_bounds("character", clip, t0, t1),
                      (0, 0, 0), 90.0, scale)

    run, jump = world("run"), world("jump")
    roll_low = world("roll", kin.roll_low_from, kin.roll_low_to)
    roll_all = world("roll")

    def half(box, axis):
        lo, hi = (box.x0, box.x1) if axis == "x" else (box.z0, box.z1)
        return max(abs(lo), abs(hi))

    return plan.Body(
        half_w=max(half(b, "x") for b in (run, jump, roll_all)),
        half_d=max(half(run, "z"), half(jump, "z")),
        roll_half_d=half(roll_all, "z"),
        stand_h=max(run.y1, jump.y1),
        roll_h=roll_low.y1,
    )


def _obstacle_boxes() -> dict[str, AABB]:
    """Model-space hitboxes, keyed by asset.

    Track-spanning props use their *corridor* profile -- the vertical extent of
    the geometry actually over the lanes. Their legs stand on the ballast
    outside the running width, and a whole-model box would report a hoarding
    as a wall from the ground up.
    """
    boxes: dict[str, AABB] = {}
    for name in ("barrier", "train_cab", "train_car", "ramp"):
        boxes[name] = assets.bounds(name)
    for name in ("hoarding", "gantry"):
        full = assets.bounds(name)
        y0, y1 = assets.metrics(name)["corridor"]
        boxes[name] = AABB(-LANE_X - 1.2, y0, full.z0, LANE_X + 1.2, y1, full.z1)
    return boxes


def _gantry_height() -> float:
    """How high to hang a sign bridge so that it stays scenery.

    It was 1.9, typed in, and the test that guarded it asked only for half a
    metre over a *standing* runner -- which is the wrong body. A runner jumps,
    and a jumping runner's head reaches its own height plus the apex; measured
    over 45 s of run 2, it went through the sign bridge twenty-two times. So
    the number is derived from the apex and the body that has to fit under it,
    and typing it in is no longer possible.
    """
    body = _body_profile()
    reach = RAIL_TOP + plan.JUMP_APEX + body.stand_h + 0.15
    return reach - _obstacle_boxes()["gantry"].y0


#: Gantries are pure dressing, so they hang clear of the tallest thing the
#: runner can become *on the rails*. A body on a train roof is a metre and a
#: half higher again, which no reasonable bridge clears -- so a roof set-piece
#: reserves the sky over itself instead (:meth:`RunnerScene._over_clash`).
GANTRY_Y = _gantry_height()


