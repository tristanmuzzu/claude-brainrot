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

BASE_SPEED = 8.5
TOP_SPEED = 15.5
RAMP_SECONDS = 75.0

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
PLAN_EVERY = 0.10
#: Rounds of "solve, check, mark what failed as unavoidable, solve again".
PLAN_ATTEMPTS = 5
#: How far into a plan counts as committed. Trouble past this is left to the
#: next re-solve, which will see it from closer up and with more options.
COMMIT_WINDOW = 1.2
#: How far ahead the last-resort reflex looks. Only needs to cover the moment
#: a move has to start, not the moment it is best planned.
REFLEX_WINDOW = 1.0

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
#: costs four metres of track.
TRAIN_PAD = 8.0


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
        self.fence = assets.load("fence")
        self.pillar = assets.load("pillar")
        self.coin = assets.load("coin")
        self.buildings = [assets.load(f"building_{c}") for c in "abc"]

        # -- measured geometry -------------------------------------------
        self.body = _body_profile()
        self.kin = plan.Kinematics.for_speed(BASE_SPEED)
        self._boxes = _obstacle_boxes()

        style = seed.stream("wardrobe")
        self.outfit = {
            "hoodie": pal.accent,
            "cap": pal.accent2,
            "pants": (40, 48, 82) if not pal.is_dark else (58, 62, 96),
            "pack": pal.hazard if style.random() < 0.5 else pal.accent2,
        }
        self.train_liveries = [pal.accent, pal.accent2, pal.train, pal.hazard]

        # -- world state -------------------------------------------------
        self.rng = ctx.stream("runner-layout")
        self.travel = 0.0
        self.speed = BASE_SPEED
        self.next_row = 2          # rows 0-1 stay clear, like the original
        self.corridor: dict[int, int] = {0: 1, 1: 1}
        self._corridor_held: dict[int, int] = {0: CORRIDOR_HOLD, 1: CORRIDOR_HOLD}
        self.entities: list[dict] = []
        self.score = 0.0
        self.coins = 0
        self._last_action_row = -99
        self._last_hoarding_row = -99
        self._last_any_barrier_row = -99
        #: most recent barrier row per lane, so two hurdles never land closer
        #: together than one jump takes to complete
        self._last_barrier_row: dict[int, int] = {}
        #: (lane, start, end) in absolute track distance, for every train laid
        #: down. Keeps the "only one lane blocked by a train" invariant
        #: checkable at spawn time rather than discoverable at collision time.
        self._train_spans: list[tuple[int, float, float]] = []

        # -- runner state ------------------------------------------------
        #: Position, velocity and what the body is currently committed to.
        #: The planner advances a copy of this to check its own work, so the
        #: rules of motion live in exactly one place.
        self.motion = plan.Motion(LANE_X)
        self.run_phase = 0.0
        self.cam_shake = 0.0
        self.impact_t = -1.0
        #: diagnostics the tests read: every frame in which the body box
        #: overlapped an obstacle box, and how deep it got.
        self.contacts = 0
        self.worst_penetration = 0.0
        self.last_contact: dict | None = None
        self.unsolvable = 0
        self.reflexes = 0

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
    def lane(self) -> int:
        """The lane the *body* is in, which is what collision cares about."""
        return self.motion.lane()

    @property
    def target_lane(self) -> int:
        return self.motion.target_lane

    # -- generation -------------------------------------------------------

    def _lane_clear(self, row: int) -> int:
        """The lane guaranteed clear at ``row``.

        The corridor holds each lane for a minimum number of rows before it is
        allowed to move again. Without that, a corridor that steps sideways on
        consecutive rows demands a lane change every 0.39 s at top speed --
        faster than a body can cross one lane and be ready to cross the next,
        which makes the *guaranteed-safe* path the one thing the runner cannot
        follow.
        """
        lane = self.corridor.get(row)
        if lane is None:
            if row <= 0:
                lane = 1
                self._corridor_held[row] = CORRIDOR_HOLD
            else:
                prev = self._lane_clear(row - 1)
                held = self._corridor_held.get(row - 1, CORRIDOR_HOLD)
                step = self.rng.choice((-1, 0, 0, 1)) if held >= CORRIDOR_HOLD else 0
                lane = max(0, min(2, prev + step))
                self._corridor_held[row] = 1 if lane != prev else held + 1
            self.corridor[row] = lane
        return lane

    def _may_spawn_train(self) -> bool:
        """No new train while one is sweeping the track the other way.

        An oncoming train crosses every row ahead of it, so it is potentially
        in *any* lane by the time it arrives. Adding a second train anywhere
        while that is true is how a runner ends up with no free lane.
        """
        return not any(e["kind"] == "train" and e["vel"] for e in self.entities)

    def _span_is_alone(self, lane: int, start: float, end: float) -> bool:
        """True when no train in a different lane shares this stretch."""
        return not any(other != lane and start < b and end > a
                       for other, a, b in self._train_spans)

    def _forget_passed_spans(self) -> None:
        self._train_spans = [s for s in self._train_spans
                             if s[2] > self.travel - VIEW_BEHIND]

    def _spawn_to_horizon(self) -> None:
        while self.next_row * ROW < self.travel + VIEW_AHEAD:
            self._spawn_row(self.next_row)
            self.next_row += 1

    def _spawn_row(self, row: int) -> None:
        d0 = row * ROW - self.travel
        rng = self.ctx.seed.stream(f"row{row}")
        clear = self._lane_clear(row)
        blocked = [ln for ln in (0, 1, 2) if ln != clear]
        # An obstacle in the corridor costs a move, and a move has a duration.
        # Two of them inside one move's length is an unsolvable corridor no
        # matter how good the planner is, so spacing is enforced here.
        may_act = row - self._last_action_row >= ACTION_GAP_ROWS

        roll = rng.random()
        if roll < 0.27 and row > 3 and self._may_spawn_train():
            # A train: 2-4 cars in a blocked lane, parked or oncoming.
            #
            # The hard invariant is that no more than one lane is ever blocked
            # by a train. Trains are the only obstacle that cannot be answered
            # by jumping or sliding, so two of them abreast is a situation with
            # no answer at all -- and since a train is up to 20 m long against
            # a 6 m row, two spawned three rows apart are very much abreast.
            lane = rng.choice(blocked)
            cars = rng.randint(2, 4)
            oncoming = rng.random() < 0.35
            length = cars * TRAIN_CAR_LEN
            start = row * ROW + ROW * 0.5
            parked_span = (start - TRAIN_PAD, start + length + TRAIN_PAD)
            # A moving train sweeps every row ahead of it, so it reserves the
            # whole visible stretch rather than a fixed span -- and has to be
            # checked against trains already laid down, not just against ones
            # that come after it. Otherwise it sweeps straight past a parked
            # train in another lane and blocks two at once.
            span = (start - VIEW_AHEAD, start + length) if oncoming else parked_span
            if not self._span_is_alone(lane, *span):
                if not oncoming or not self._span_is_alone(lane, *parked_span):
                    return
                oncoming, span = False, parked_span
            self._train_spans.append((lane, *span))
            livery = rng.choice(self.train_liveries)
            self.entities.append({
                "kind": "train", "lane": lane, "d": d0 + ROW * 0.5,
                "cars": cars, "vel": (self.speed * 0.55 + 4.5) if oncoming else 0.0,
                "color": livery,
            })
        elif roll < 0.55 and row > 2 and row - self._last_hoarding_row >= HOARDING_GAP_ROWS:
            # barriers: all blocked lanes, sometimes the corridor too (jumpable)
            for lane in blocked:
                if (rng.random() < 0.75
                        and row - self._last_barrier_row.get(lane, -99) >= ACTION_GAP_ROWS):
                    self.entities.append({"kind": "barrier", "lane": lane, "d": d0})
                    self._last_barrier_row[lane] = row
                    self._last_any_barrier_row = row
            if may_act and rng.random() < 0.5:
                self.entities.append({"kind": "barrier", "lane": clear, "d": d0})
                self._last_barrier_row[clear] = row
                self._last_any_barrier_row = row
                self._last_action_row = row
        elif (roll < 0.68 and row > 2 and may_act
                and row - self._last_any_barrier_row >= HOARDING_GAP_ROWS
                and row - self._last_hoarding_row >= HOARDING_GAP_ROWS):
            # a low hoarding across the whole track: everyone rolls
            self.entities.append({"kind": "hoarding", "d": d0})
            self._last_action_row = row
            self._last_hoarding_row = row
        elif roll < 0.78:
            self.entities.append({"kind": "gantry", "d": d0})

        # coins ride the corridor, arcing over any jumpable on it
        if rng.random() < 0.6 and row > 1:
            over = any(e["kind"] == "barrier" and e["lane"] == clear
                       and abs(e["d"] - d0) < 1.0 for e in self.entities)
            n = rng.randint(4, 7)
            for i in range(n):
                dd = d0 + (i - n / 2) * 0.9
                y = 0.55 + (1.35 * math.sin(math.pi * i / (n - 1)) if over else 0.0)
                self.entities.append({"kind": "coin", "lane": clear, "d": dd,
                                      "y": y, "taken": False})

        # city canyon: a building per side on an independent cadence
        for side in (-1, 1):
            srng = self.ctx.seed.stream(f"city{side}{row}")
            if srng.random() < 0.8:
                idx = srng.randrange(3)
                dist = srng.uniform(10.5, 16.0)
                tone = 0.55 + srng.random() * 0.5
                self.entities.append({
                    "kind": "building", "x": side * dist, "d": d0 + srng.uniform(0, ROW),
                    "idx": idx, "yaw": 90.0 if side < 0 else -90.0,
                    "tone": tone,
                })
            if srng.random() < 0.22:
                self.entities.append({"kind": "pillar",
                                      "x": side * srng.uniform(6.8, 8.4),
                                      "d": d0 + srng.uniform(0, ROW)})

    # -- collision geometry -----------------------------------------------

    def _lane_x(self, lane: int) -> float:
        return (lane - 1) * LANE_X

    def body_box(self) -> AABB:
        """The runner's own volume right now, in world space."""
        rolling = self.motion.rolling
        return AABB.around(self.motion.x, RAIL_TOP + self.motion.y, 0.0,
                           self.body.half_w, self.body.height(rolling),
                           self.body.depth(rolling))

    def solid_box(self, e: dict) -> AABB | None:
        """World hitbox of an entity, or None when it is pure decoration.

        Built by the same ``placed`` call the draw uses, from the same measured
        model box -- so a hitbox cannot drift away from its picture without the
        scene passing two different transforms, which the tests check for.
        """
        kind = e["kind"]
        d = e["d"]
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

    def _threats(self) -> list[plan.Threat]:
        """Every obstacle inside the horizon, as lane/height/time facts."""
        out: list[plan.Threat] = []
        for e in self.entities:
            box = self.solid_box(e)
            if box is None:
                continue
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
            th = plan.Threat(e["kind"], lanes, box.y0, box.y1,
                             max(0.0, t0), t1, x0=box.x0, x1=box.x1, ref=e)
            action = plan.classify(th, self.body, self.kin, RAIL_TOP)
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

    def _already_cleared(self, th: plan.Threat) -> bool:
        """Will the jump currently in progress carry the body over this?

        Without asking, the planner keeps seeing a hurdle it is already sailing
        over as a reason to swerve -- and swerving in mid-air is how the runner
        used to land on the barrier in the next lane.
        """
        if not self.motion.airborne:
            return False
        need = th.y1 - RAIL_TOP + self.kin.clearance_margin
        flight = self.motion.flight(self.kin)
        for t in (th.t_enter, 0.5 * (th.t_enter + th.t_exit), th.t_exit):
            if t < 0.0:
                continue
            if flight.height_at(self.motion.air_t + t) < need:
                return False
        return True

    # -- planning ---------------------------------------------------------

    def _corridor_lanes(self) -> list[int]:
        """The generator's clear lane at each step of the planning horizon."""
        steps = max(1, int(math.ceil(PLAN_HORIZON / PLAN_STEP)))
        out = []
        for i in range(steps):
            ahead = self.travel + self.speed * (i * PLAN_STEP)
            out.append(self._lane_clear(int(ahead / ROW)))
        return out

    def _replan(self) -> None:
        threats = self._threats()
        transit = max(1, int(round(self.kin.lane_time / PLAN_STEP)))
        # When the body next becomes available: mid-jump or mid-slide, it is
        # committed, and anything scheduled inside that window would simply be
        # dropped at execution time and never noticed.
        busy_until = self.motion.time_to_free(self.kin)
        corridor = self._corridor_lanes()
        # Keep the attempt that survives longest, not the last one tried: a
        # later attempt is only better if marking something unavoidable
        # actually helped, and often it does not.
        best = (-1.0, self._lane_plan, [])
        for _ in range(PLAN_ATTEMPTS):
            grid = plan.occupancy(threats, PLAN_HORIZON, PLAN_STEP, corridor)
            # Plan onward from where the body is committed to arriving, not
            # from where it happens to be mid-slide.
            lane_plan = plan.choose_lanes(grid, self.motion.target_lane,
                                          PLAN_STEP, transit)
            booked, unsolved = plan.schedule_vertical(
                threats, lane_plan, self.body, self.kin, RAIL_TOP, busy_until)
            if not unsolved:
                # The two halves of the plan are each self-consistent; that is
                # not the same as the body surviving them together. Run it.
                failure = plan.verify(self.motion, lane_plan, booked, threats,
                                      self.body, self.kin, PLAN_HORIZON,
                                      PLAN_STEP, RAIL_TOP)
                if failure is None:
                    best = (float("inf"), lane_plan, booked)
                    break
                unsolved = [failure[0]]
                if failure[1] > best[0]:
                    best = (failure[1], lane_plan, booked)
            elif best[0] < 0.0:
                best = (0.0, lane_plan, booked)
            # Whatever the plan could not answer becomes something to route
            # around rather than something to walk into.
            for th in unsolved:
                th.hard = True
        survives, lane_plan, booked = best
        self._lane_plan = lane_plan
        self._booked = [(self.elapsed + t, a) for t, a in booked]
        #: How often no plan survived even the part of the horizon that will
        #: actually be flown before the next re-solve. Non-zero here is the
        #: honest early warning that the generator is producing situations
        #: with no answer -- long before it shows up as a body inside a train.
        if survives < COMMIT_WINDOW:
            self.unsolvable += 1

    # -- simulation -------------------------------------------------------

    def update(self, dt: float) -> None:
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

        for e in self.entities:
            e["d"] -= step
            if e["kind"] == "train" and e["vel"]:
                e["d"] -= e["vel"] * dt
        self.entities = [e for e in self.entities if e["d"] > -VIEW_BEHIND]
        self._forget_passed_spans()
        self._spawn_to_horizon()

        if self.elapsed - self._plan_at >= PLAN_EVERY:
            self._plan_at = self.elapsed
            self._replan()

        while self._booked and self._booked[0][0] <= self.elapsed:
            _, action = self._booked.pop(0)
            self.motion.begin(action, self.kin)
        self._reflex()

        was_airborne = self.motion.airborne
        self.motion.advance(dt, self.kin, self._lane_plan.lane_at(
            max(0.0, self.elapsed - self._plan_at)))
        if was_airborne and not self.motion.airborne:
            self.cam_shake = 0.5

        if self.impact_t >= 0:
            self.impact_t += dt
            if self.impact_t >= IMPACT_TIME:
                self.impact_t = -1.0

        self._collect_coins()
        self._resolve_contacts()
        self.burst.update(dt)

    def _reflex(self) -> None:
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
        body = self.body_box()
        for e in self.entities:
            box = self.solid_box(e)
            if box is None or box.x1 <= body.x0 or box.x0 >= body.x1:
                continue
            closing = self._closing_speed(e)
            half_len = (box.z1 - box.z0) * 0.5
            centre_d = -0.5 * (box.z0 + box.z1)
            t0, t1 = plan.contact_window(centre_d, half_len,
                                         self.body.half_d, closing)
            if t1 <= 0.0 or t0 > REFLEX_WINDOW:
                continue
            th = plan.Threat(e["kind"], (self.lane,), box.y0, box.y1,
                             max(0.0, t0), t1, x0=box.x0, x1=box.x1, ref=e)
            action = plan.classify(th, self.body, self.kin, RAIL_TOP)
            if action == "roll":
                t0, t1 = plan.contact_window(centre_d, half_len,
                                             self.body.roll_half_d, closing)
                th.t_enter, th.t_exit = max(0.0, t0), t1
                window = plan.solve_roll(th, self.kin)
            elif action == "jump":
                window = plan.solve_jump(th, self.body, self.kin, RAIL_TOP)
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
                self.burst.spawn(self.x, RAIL_TOP + e["y"], -e["d"],
                                 (255, 215, 80), count=8, rng=self.rng)

    def _resolve_contacts(self) -> None:
        """Last line of defence: if a body box is inside an obstacle box, take
        the hit and push back out, rather than letting the mesh pass through.

        The planner is supposed to make this unreachable, and the tests assert
        it stays unreached over long runs -- but "assert it never happens" and
        "behave sanely when it does" are different jobs, and a background toy
        that occasionally shows a runner gliding through a train is worse than
        one that occasionally shows a runner clipping a train and stumbling.
        """
        body = self.body_box()
        for e in self.entities:
            box = self.solid_box(e)
            if box is None or not body.overlaps(box):
                continue
            depth = body.penetration(box)
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

    def draw(self) -> None:
        pal = self.palette
        self.sky.draw(self.elapsed)

        cam = self.camera
        # two footfalls per stride cycle drive the bob
        bob = math.sin(self.run_phase * math.tau * 2) * 0.045 * (self.speed / TOP_SPEED)
        shake = (math.sin(self.elapsed * 43.0) * 0.05
                 + math.sin(self.elapsed * 61.0) * 0.03) * self.cam_shake
        # Ride directly behind the runner: with the camera between lanes, a
        # passing train in the next lane would wipe across the whole frame.
        cam.position = (self.x * 0.92 + shake, 3.5 + bob + self.y * 0.28, 6.8)
        cam.target = (self.x, 1.6 + bob * 0.5 + shake * 0.6 + self.y * 0.3, -4.6)
        cam.fovy = 56.0 + 6.0 * (self.speed - BASE_SPEED) / (TOP_SPEED - BASE_SPEED)

        rl.BeginMode3D(cam[0])

        # ground plane under everything; fog handled by the horizon haze
        rl.DrawPlane((0, -0.05, -30), (240, 160), rl.rgba(pal.ground, 255))

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
            elif kind == "train":
                self._draw_train(e, fog)
            elif kind == "barrier":
                self.barrier.recolor({"stripe": pal.hazard})
                rl.DrawModelEx(self.barrier.model,
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
            elif e["kind"] == "train" and e["vel"] and pal.is_dark and e["d"] < 70:
                # oncoming headlights punching through the dark, on the nose --
                # which faces us, so they sit at the near end of the hull
                x_t = self._lane_x(e["lane"])
                for side in (-1, 1):
                    glow_billboard(self.camera, x_t + side * 0.6, 1.05,
                                   -e["d"] + 2.6, 1.6, (255, 235, 170), 120)
        self.burst.draw(self.camera)
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        self._draw_hud()

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
            flight = self.motion.flight(self.kin)
            ch.pose("jump", min(0.999, self.motion.air_t / flight.jump_air_time))
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
        blob_shadow(self.x, RAIL_TOP + 0.04, 0.0, 0.62,
                    alpha=int(110 * max(0.0, 1.0 - self.y / 3.0)))
        rl.DrawModelEx(ch.model, (self.x, RAIL_TOP + self.y, 0), (0, 1, 0), 0.0,
                       (CHAR_SCALE, CHAR_SCALE, CHAR_SCALE), rl.WHITE4)

    def _draw_hud(self) -> None:
        pal = self.palette
        text(f"{int(self.score):06d}", self.width - 14, 12, 26, pal.ink, anchor="topright")
        # coin counter with a little gold disc
        rl.DrawCircle(self.width - 66, 58, 7, (255, 205, 60, 255))
        rl.DrawCircle(self.width - 66, 58, 4, (255, 235, 140, 255))
        text(f"{self.coins}", self.width - 14, 48, 20, (255, 215, 90), anchor="topright")


# ---------------------------------------------------------------------------
# Geometry helpers -- all of it measured, none of it typed in
# ---------------------------------------------------------------------------

#: Gantries are pure dressing, so they are hung clear of the tallest thing the
#: runner can become. The number is checked against the measured soffit in
#: tests/test_assets.py rather than eyeballed against a screenshot.
GANTRY_Y = 1.9


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
    for name in ("barrier", "train_cab", "train_car"):
        boxes[name] = assets.bounds(name)
    for name in ("hoarding", "gantry"):
        full = assets.bounds(name)
        y0, y1 = assets.metrics(name)["corridor"]
        boxes[name] = AABB(-LANE_X - 1.2, y0, full.z0, LANE_X + 1.2, y1, full.z1)
    return boxes


