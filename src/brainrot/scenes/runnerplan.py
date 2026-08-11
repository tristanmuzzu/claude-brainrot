"""The runner's brain: decide where to be, and when to leave the ground.

This module is deliberately free of raylib and of the scene -- it is plain
arithmetic over boxes and times, so the tests can run millions of simulated
seconds of decision-making without opening a window.

Why a planner at all, when the old scene got by on "if something is between
1.8 and 2.9 metres ahead, jump"? Because that rule is wrong at speed. The jump
took a fixed 0.62 s to complete, so the distance at which it had to *start*
changed as the run accelerated; at top speed the trigger window straddled the
point where the arc was still too low, and the runner clipped straight through
the hurdle it had just jumped at. A trigger measured in metres cannot answer a
question asked in seconds.

So the logic here works in time throughout:

* :func:`threats` converts obstacles into "lane L is blocked from t0 to t1,
  between heights y0 and y1" -- closing speed included, so an oncoming train
  and a parked one are the same kind of fact.
* :func:`choose_lanes` picks a lane for each moment of the next couple of
  seconds by dynamic programming, charging a lane change for occupying *both*
  lanes while it crosses (which is what the body actually does, and what the
  old code forgot: it snapped its lane index across instantly and left the
  mesh sliding through whatever was in the lane it was leaving).
* :func:`solve_jump` and :func:`solve_roll` answer "when must this start so
  the clearance window covers the whole contact?" in closed form, and report
  failure rather than producing a jump that almost works.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

LANES = (0, 1, 2)

#: Contact shallower than this is two faces meeting rather than one body
#: inside another. A runner standing on a train roof has its feet at exactly
#: the roof's height, and "exactly" is not something floating point offers --
#: without this the check that decides whether a plan survives rejects every
#: plan that involves standing on anything.
TOUCH = 0.005


# ---------------------------------------------------------------------------
# Vertical motion
# ---------------------------------------------------------------------------


#: Peak height of an ordinary jump, in metres above the running surface. This
#: is the one part of the move that must not change with speed -- it is what
#: decides whether a hurdle is cleared at all.
JUMP_APEX = 1.56
#: How much track a jump should span, in metres. Holding this constant is what
#: makes the move scale: a jump that takes a fixed 0.6 s covers 5 m at the
#: start of a run and 9.4 m at the end, and by the end it is a commitment long
#: enough to fly straight into the next row of obstacles. Real runner games
#: snap the jump up as the speed rises for exactly this reason.
JUMP_SPAN = 6.4
#: Track spanned by a slide, and by a lane change. Same argument.
ROLL_SPAN = 8.4
LANE_SPAN = 3.1
#: Apex of a *mount* -- the leap off a ramp's lip onto a train roof -- above
#: the lip it left from. Big enough that the roof is cleared with obvious room
#: rather than grazed, because a mount that only just works looks like a bug
#: even on the frames where it does work.
MOUNT_APEX = 2.35


@dataclass(frozen=True)
class Kinematics:
    """The runner's physical capabilities at one running speed.

    Rebuilt as the run accelerates -- see :meth:`for_speed`. Everything the
    planner solves is expressed in seconds, so the numbers here are what tie
    those solutions to how fast the world is actually moving.
    """

    gravity: float = 34.0
    #: launch speed of an ordinary hurdle jump, m/s
    jump_v0: float = 10.3
    #: A slide has to stay low for longer than the body is long, at top speed:
    #: the legs go out in front, so the body passing under a hoarding is over
    #: two metres of it, and a snappier roll simply cannot fit underneath.
    roll_time: float = 0.80
    #: seconds to slide fully across one lane
    lane_time: float = 0.26
    #: The flat-bottomed stretch of the roll clip, as a fraction of it. The
    #: clip is authored as a trapezoid precisely so this window is wide and
    #: the height across it is constant: it has to outlast the time the body
    #: takes to pass under a hoarding, which is *longest* at the slowest speed.
    #: Must sit strictly inside the clip's authored ramp (character.py's
    #: ROLL_RAMP = 0.18 at each end). The window is sampled by flooring onto
    #: recorded frames, so edges placed exactly on the ramp boundary pick up
    #: the frame just outside it -- and the body's height is taken as the
    #: worst frame in the window, so one ramp frame reports the runner 25 cm
    #: taller than it slides.
    roll_low_from: float = 0.22
    roll_low_to: float = 0.78
    #: Height the body must have to spare when passing an obstacle. Solving
    #: for exact contact produces arcs that graze what they clear -- correct
    #: to the millimetre, and visibly wrong at the trailing edge of the body,
    #: where a couple of centimetres of foot end up inside the hurdle.
    clearance_margin: float = 0.09

    @classmethod
    def for_speed(cls, speed: float) -> "Kinematics":
        """Moves sized so each spans a fixed stretch of track.

        Given an air time T and a required apex A, gravity and launch speed
        follow: ``g = 8A/T^2`` and ``v0 = 4A/T``. So fixing how far a jump
        carries the runner fixes the whole arc, at any speed, with the apex
        preserved -- which is the only part of it a hurdle cares about.
        """
        speed = max(1.0, speed)
        air = min(0.78, max(0.34, JUMP_SPAN / speed))
        return cls(
            gravity=8.0 * JUMP_APEX / (air * air),
            jump_v0=4.0 * JUMP_APEX / air,
            roll_time=min(1.05, max(0.46, ROLL_SPAN / speed)),
            lane_time=min(0.36, max(0.17, LANE_SPAN / speed)),
        )

    @property
    def jump_air_time(self) -> float:
        return 2.0 * self.jump_v0 / self.gravity

    @property
    def jump_apex(self) -> float:
        return self.jump_v0 ** 2 / (2.0 * self.gravity)

    @property
    def mount_v0(self) -> float:
        """Launch speed off a ramp's lip, solved for a fixed apex.

        Derived rather than stored, because gravity changes with the run speed
        (see :meth:`for_speed`) and a stored launch speed would quietly stop
        reaching the roof as the run got quicker -- which is exactly the class
        of bug this module exists to remove.
        """
        return math.sqrt(2.0 * self.gravity * MOUNT_APEX)

    def height_at(self, tau: float, v0: float | None = None) -> float:
        """Feet height above the take-off surface ``tau`` seconds into a jump.

        Clamped at zero, which is right for a jump that lands where it left.
        A body walking off an edge is falling *below* its take-off surface;
        that is :meth:`offset_at`.
        """
        return max(0.0, self.offset_at(tau, v0))

    def offset_at(self, tau: float, v0: float | None = None) -> float:
        """Signed height relative to the take-off surface, unclamped."""
        v0 = self.jump_v0 if v0 is None else v0
        if tau <= 0.0:
            return 0.0
        return v0 * tau - 0.5 * self.gravity * tau * tau

    def clearance_window(self, need: float, v0: float | None = None
                         ) -> tuple[float, float] | None:
        """When, within one jump, are the feet at least ``need`` above the
        take-off surface? Returns ``(tau_a, tau_b)``, or None if never.

        Solving this rather than trusting an eyeballed trigger distance is the
        whole fix: the answer is in seconds, so it stays true at every speed.
        """
        v0 = self.jump_v0 if v0 is None else v0
        disc = v0 * v0 - 2.0 * self.gravity * need
        if disc <= 0.0:
            return None
        root = math.sqrt(disc)
        return ((v0 - root) / self.gravity, (v0 + root) / self.gravity)


# ---------------------------------------------------------------------------
# The body
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Body:
    """The runner's collision volume, measured from the character asset.

    A slide is not just a shorter runner: the legs go out in front, so the
    body is markedly *longer* along the track at the same time as it gets
    lower. Carrying one half-depth for both states gets one of them wrong --
    and taking the union of the whole roll clip gets the height wrong too,
    because a roll begins and ends standing up.
    """

    half_w: float
    half_d: float
    roll_half_d: float
    stand_h: float
    roll_h: float

    def height(self, rolling: bool) -> float:
        return self.roll_h if rolling else self.stand_h

    def depth(self, rolling: bool) -> float:
        return self.roll_half_d if rolling else self.half_d


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------


def lane_x(lane: int, spacing: float) -> float:
    return (lane - 1) * spacing


@dataclass
class Motion:
    """Everything about the runner that moves, and the rules that move it.

    The scene owns one of these and advances it; the planner advances a *copy*
    to check that the plan it is about to commit to actually survives contact
    with the obstacles. Sharing the code is the point -- when the check and
    the execution are two descriptions of the same rules, they disagree, and
    every disagreement is a runner walking through something the planner was
    certain it had avoided.
    """

    spacing: float
    x: float = 0.0
    y: float = 0.0
    #: seconds into the current jump, or -1 when on the ground. The arc is
    #: evaluated from this in closed form rather than integrated step by step,
    #: so it is identical whether it is being flown at 60 fps or checked at
    #: the planner's coarser resolution. An Euler-integrated jump is a
    #: different height at every step size, which makes a verified plan a
    #: statement about a trajectory the body never actually flies.
    air_t: float = -1.0
    roll_t: float = -1.0
    target_lane: int = 1
    #: The arc this jump was launched with. Kinematics change as the run
    #: accelerates, and a jump whose gravity is edited underneath it is a jump
    #: whose clearance was solved for a trajectory it is no longer flying.
    air_kin: "Kinematics | None" = None
    roll_dur: float = 0.0
    #: Height of the surface under the feet, above the base running surface.
    #: Zero on the rails, the roof height while riding a train, part-way up
    #: while running up a ramp. While airborne it holds the height the jump
    #: *left from*, which is what the closed-form arc is measured against.
    ground: float = 0.0
    #: Launch speed of the current jump. A mount leaves the ground harder than
    #: a hurdle jump, and a body walking off an edge leaves it at zero.
    air_v0: float = 0.0

    @property
    def rolling(self) -> bool:
        return self.roll_t >= 0.0

    @property
    def airborne(self) -> bool:
        return self.air_t >= 0.0

    def flight(self, kin: Kinematics) -> Kinematics:
        """The arc currently being flown: the frozen one, or a fresh one."""
        return self.air_kin or kin

    def lane(self) -> int:
        return min(LANES, key=lambda ln: abs(lane_x(ln, self.spacing) - self.x))

    def settled(self) -> bool:
        return abs(self.x - lane_x(self.target_lane, self.spacing)) < 0.02

    def begin(self, action: str, kin: Kinematics) -> bool:
        """Start a jump, a mount or a slide, if the body is free to."""
        if self.airborne or self.rolling:
            return False
        if action in ("jump", "mount"):
            self.air_t = 0.0
            self.air_kin = kin
            self.air_v0 = kin.mount_v0 if action == "mount" else kin.jump_v0
        elif action == "roll":
            self.roll_t = 0.0
            self.roll_dur = kin.roll_time
        else:
            return False
        return True

    def advance(self, dt: float, kin: Kinematics, desired_lane: int,
                ground_here: float = 0.0) -> None:
        """One step of motion under two commitments and one surface.

        Finish a crossing before reconsidering -- a body caught halfway by a
        change of mind is in two lanes and safe in neither -- and never start
        one in mid-air, where the jump was solved for the lane it left from.

        ``ground_here`` is the height of whatever the body is over *now*: the
        rails, a ramp's slope, a train roof. Three rules, and between them
        they are the whole of riding a train:

        * airborne and the arc has come back down to the surface -> land on it,
          whatever height that surface is;
        * on the ground and the surface under the feet has risen -> the feet
          rise with it, which is what running up a ramp is;
        * on the ground and the surface has fallen away -> start falling, from
          a standing height with no upward impulse, which is what running off
          the back of a train is.
        """
        if self.settled() and not self.airborne:
            self.target_lane = desired_lane
        # Anything off the rails holds its lateral position, in the air as
        # well as on the ground. A body that steps sideways off a train roof
        # spends the fall beside the train with its box still overlapping the
        # corner it left, which is a contact; a body still crossing when it
        # lands on one slides straight off the far side of it. Freezing while
        # raised makes leaving a roof something that can only happen at the
        # *end* of the train, which is also what riding one looks like. The
        # crossing is not cancelled -- it resumes on landing.
        if self.ground <= 0.0:
            goal = lane_x(self.target_lane, self.spacing)
            rate = self.spacing / kin.lane_time
            if self.x < goal:
                self.x = min(goal, self.x + rate * dt)
            else:
                self.x = max(goal, self.x - rate * dt)

        if self.airborne:
            flight = self.flight(kin)
            self.air_t += dt
            offset = flight.offset_at(self.air_t, self.air_v0)
            rising = self.air_t < self.air_v0 / flight.gravity
            y = self.ground + offset
            if not rising and y <= ground_here:
                self.air_t = -1.0
                self.air_kin = None
                self.ground = ground_here
                self.y = ground_here
            else:
                self.y = y
        else:
            if ground_here > self.ground:
                self.ground = ground_here          # walked up a slope
            elif ground_here < self.ground:
                self.air_t = 0.0                   # walked off an edge
                self.air_kin = kin
                self.air_v0 = 0.0
            self.y = self.ground
        if self.rolling:
            self.roll_t += dt
            if self.roll_t >= (self.roll_dur or kin.roll_time):
                self.roll_t = -1.0

    def extent(self, body: Body) -> tuple[float, float, float, float]:
        """``(x0, x1, y0, y1)`` of the body, relative to the running surface."""
        half_w = body.half_w
        return (self.x - half_w, self.x + half_w,
                self.y, self.y + body.height(self.rolling))

    def time_to_free(self, kin: Kinematics, landing: float = 0.0) -> float:
        """When the body finishes what it is doing and can act again.

        ``landing`` is the height of the surface it will come down on, which
        for a leap off a train roof is well below the one it left: the fall
        takes longer than the rise, and a scheduler that assumed otherwise
        would book the next move while the body was still in the air.
        """
        busy = 0.0
        if self.airborne:
            flight = self.flight(kin)
            drop = self.ground - landing
            # v0*t - g t^2/2 = -drop, taking the descending root
            disc = self.air_v0 ** 2 + 2.0 * flight.gravity * max(0.0, drop)
            total = (self.air_v0 + math.sqrt(max(0.0, disc))) / flight.gravity
            busy = max(busy, total - self.air_t)
        if self.rolling:
            busy = max(busy, (self.roll_dur or kin.roll_time) - self.roll_t)
        return busy


def verify(motion: Motion, lane_plan: "LanePlan", booked: list[tuple[float, str]],
           threats: list[Threat], body: Body, kin: Kinematics,
           horizon: float, step: float, surface: float = 0.0,
           ground: "callable | None" = None,
           ) -> "tuple[Threat, float] | None":
    """Roll the plan forward; return the first threat it fails to avoid, and
    when. ``None`` means the whole horizon came through clean.

    The lane search and the take-off solver each reason correctly about their
    own half of the problem and still combine into a plan the body cannot
    execute -- a crossing that starts a moment before a hurdle, a slide the
    lane change walks sideways out of. Rather than add another rule for each
    way that happens, run the plan and look.

    *When* it fails matters as much as whether. A plan is only ever followed
    for a fraction of its horizon before being re-solved from a fresh state,
    so trouble two seconds out is a hint, not a verdict; rejecting a plan for
    it throws away one that was perfectly safe for the part that gets used.

    ``ground`` is ``f(t, x) -> height`` for the surface under the body -- the
    rails, a ramp, a train roof. It is the same function the scene advances
    the real body against, which is what makes a mount *verified* rather than
    merely scheduled: the lane path and the take-off are rolled forward
    together, over a world that includes the train the plan intends to land
    on, and either the pair survives or neither is committed.
    """
    sim = Motion(motion.spacing, motion.x, motion.y, motion.air_t,
                 motion.roll_t, motion.target_lane, motion.air_kin,
                 motion.roll_dur, motion.ground, motion.air_v0)
    queue = sorted(booked)
    steps = max(1, int(horizon / step))
    t = 0.0
    for _ in range(steps):
        while queue and queue[0][0] <= t:
            sim.begin(queue.pop(0)[1], kin)
        sim.advance(step, kin, lane_plan.lane_at(t),
                    0.0 if ground is None else ground(t, sim.x))
        t += step
        x0, x1, y0, y1 = sim.extent(body)
        y0 += surface
        y1 += surface
        for th in threats:
            if not (th.t_enter <= t <= th.t_exit):
                continue
            if x1 <= th.x0 + TOUCH or x0 >= th.x1 - TOUCH:
                continue
            if y1 <= th.y0 + TOUCH or y0 >= th.y1 - TOUCH:
                continue
            return (th, t)
    return None


# ---------------------------------------------------------------------------
# Threats
# ---------------------------------------------------------------------------


@dataclass
class Threat:
    """One obstacle, expressed as "this space, this height band, this window".

    ``t_enter``/``t_exit`` are seconds from now, already including the runner's
    own body depth, so overlap is exactly ``t_enter < t < t_exit``. ``lanes``
    is what the lane search reasons about; ``x0``/``x1`` is the real extent,
    which is what matters to a body that is between two lanes.
    """

    kind: str
    lanes: tuple[int, ...]
    y0: float
    y1: float
    t_enter: float
    t_exit: float
    x0: float = -1e9
    x1: float = 1e9
    #: True when nothing the runner can do clears it -- must be dodged sideways
    hard: bool = False
    #: identity of the source entity, for the scene to cross-reference
    ref: object = None
    #: For a train with a ramp in front of it: when to leave the ramp's lip.
    #: A train is otherwise the one obstacle with no answer but a lane change,
    #: so this is what turns "get out of that lane" into "get on top of it",
    #: and it is the *whole* of what the planner needs to know about riding.
    #: The scene solves it; ``verify`` is what decides whether it survives.
    mount_at: float | None = None

    @property
    def duration(self) -> float:
        return self.t_exit - self.t_enter


def contact_window(d: float, half_len: float, half_depth: float,
                   closing: float) -> tuple[float, float]:
    """When an obstacle ``d`` ahead overlaps the runner along the track.

    ``closing`` is the rate the gap shrinks: run speed alone for something
    parked, run speed plus its own for something coming the other way.
    """
    if closing <= 1e-6:
        return (float("inf"), float("inf"))
    reach = half_len + half_depth
    return ((d - reach) / closing, (d + reach) / closing)


def classify(threat: Threat, body: Body, kin: Kinematics,
             surface: float = 0.0) -> str:
    """Can this be jumped, rolled under, or only avoided?

    Heights are relative to the surface the runner is standing on. The test is
    against the *measured* body: a roll clears something only if the recorded
    crouch silhouette fits under it, not because rolling feels like it ought
    to help.
    """
    if threat.mount_at is not None and not threat.hard:
        return "mount"
    top = threat.y1 - surface
    bottom = threat.y0 - surface
    margin = kin.clearance_margin
    if bottom >= body.stand_h:
        return "clear"                      # passes overhead untouched
    if bottom >= body.roll_h + margin:
        # low enough to hit a running body, high enough to slide under
        return "roll"
    if top <= 0.0:
        return "clear"
    window = kin.clearance_window(top + margin)
    if window is not None:
        span = window[1] - window[0]
        if span > threat.duration:
            return "jump"
    return "hard"


# ---------------------------------------------------------------------------
# Lane planning
# ---------------------------------------------------------------------------


@dataclass
class LanePlan:
    """A lane for each step of the planning horizon."""

    step: float
    lanes: list[int] = field(default_factory=list)
    cost: float = 0.0

    def lane_at(self, t: float) -> int:
        if not self.lanes:
            return 1
        i = int(t / self.step)
        if i < 0:
            i = 0
        if i >= len(self.lanes):
            i = len(self.lanes) - 1
        return self.lanes[i]

    def first_change(self) -> tuple[float, int] | None:
        """Time and destination of the next lane change, if any."""
        if not self.lanes:
            return None
        start = self.lanes[0]
        for i, lane in enumerate(self.lanes):
            if lane != start:
                return (i * self.step, lane)
        return None


#: How long before a hard obstacle arrives its lane starts feeling expensive.
APPROACH = 1.1
#: What a rideable train costs per step of the lane search.
#:
#: Zero, and it has to be: the search already pays ``preference`` for every
#: step spent outside the guaranteed corridor, so *any* positive cost on the
#: roof makes standing beside the train cheaper than standing on it. Set to
#: 0.4 against a preference of 0.22, the runner stepped one lane clear of
#: every ramp in the scene and stayed there -- thirty-three ramps laid down,
#: two of them ever taken. A train with a way onto it is not an obstacle.
MOUNT_COST = 0.0


def occupancy(threats: list[Threat], horizon: float, step: float,
              preferred: "list[int] | None" = None,
              preference: float = 0.22) -> list[list[float]]:
    """Cost grid ``[lane][step]``: how blocked each lane is at each moment.

    Hard threats cost a lot; soft ones cost a little, so that given a free
    choice the planner would rather take the lane that does not also demand a
    jump -- without ever preferring a train to a hurdle.

    Hard threats also cast a shadow *backwards* in time, ramping up as they
    approach. Without it the search is indifferent about when to leave a lane
    that is going to be blocked later -- moving now and moving in a second
    score the same -- so each re-solve happily defers the move again, and the
    runner strolls along in front of a train until the only remaining option
    is to cross while the train is alongside. Paying a little to leave early
    makes leaving early the plan.

    ``preferred`` names the generator's guaranteed-clear lane at each step.
    Being anywhere else is legal and often cheaper for a moment, but only the
    corridor comes with a promise that the next few rows have an answer, so
    wandering out of it is charged a little. Cheap enough to dodge a train;
    expensive enough not to drift out and get cornered.
    """
    steps = max(1, int(math.ceil(horizon / step)))
    grid = [[0.0] * steps for _ in LANES]
    if preferred:
        for i in range(steps):
            want = preferred[min(i, len(preferred) - 1)]
            for lane in LANES:
                if lane != want:
                    grid[lane][i] += preference
    approach_steps = max(1, int(APPROACH / step))
    for th in threats:
        if th.mount_at is not None and not th.hard:
            # A train with a way onto it is not a wall, it is a road. Charging
            # it the ordinary obstacle cost would make the search treat the
            # signature move of the genre as damage to be routed around; a
            # small cost keeps it honest about the risk without refusing it.
            weight = MOUNT_COST
        else:
            weight = 100.0 if th.hard else 1.0
        i0 = max(0, int(math.floor(th.t_enter / step)))
        i1 = min(steps - 1, int(math.ceil(th.t_exit / step)))
        if i1 < 0 or i0 >= steps:
            continue
        for lane in th.lanes:
            for i in range(i0, i1 + 1):
                grid[lane][i] += weight
            if not th.hard:
                continue
            for k in range(1, approach_steps + 1):
                i = i0 - k
                if i < 0:
                    break
                grid[lane][i] += weight * 0.05 * (1.0 - k / (approach_steps + 1))
    return grid


def choose_lanes(grid: list[list[float]], start_lane: int, step: float,
                 transit_steps: int, hysteresis: float = 0.6) -> LanePlan:
    """Cheapest lane-versus-time path, by dynamic programming.

    Two rules make the path one a body could actually follow:

    * A lane change is charged the cost of *both* lanes for the whole time the
      body takes to cross, because for that time the body is genuinely in both.
    * After a change, the next one has to wait out the crossing. This is a
      *cooldown*, carried in the search state -- not an alignment of changes to
      a fixed grid. Snapping them to a grid rooted at the start of the horizon
      forbids changing lanes for the first crossing-length of every plan, and
      since the plan is re-solved several times a crossing, that moment keeps
      being pushed back and the runner never moves at all.
    """
    steps = len(grid[0])
    transit_steps = max(1, transit_steps)
    lanes_n = len(LANES)
    inf = math.inf
    # best[i][lane][cool]: cool = steps that must pass before changing again
    best = [[[inf] * transit_steps for _ in range(lanes_n)] for _ in range(steps)]
    back = [[[(0, 0)] * transit_steps for _ in range(lanes_n)] for _ in range(steps)]
    best[0][start_lane][0] = grid[start_lane][0]

    # Cost of occupying the lane being left, for the length of one crossing.
    # Prefix sums make this O(1) instead of O(transit) inside the innermost
    # loop, which is what makes a fine enough time grid affordable -- and the
    # grid has to be fine, because at top speed a coarse step is most of a
    # metre and a hurdle is only 0.4 m deep.
    prefix = [[0.0] * (steps + 1) for _ in LANES]
    for lane in LANES:
        row = grid[lane]
        acc = prefix[lane]
        for i in range(steps):
            acc[i + 1] = acc[i] + row[i]

    def leaving(prev: int, i: int) -> float:
        end = min(steps, i + transit_steps)
        return prefix[prev][end] - prefix[prev][i]

    for i in range(1, steps):
        for lane in LANES:
            here = grid[lane][i]
            for prev in LANES:
                for cool in range(transit_steps):
                    prior = best[i - 1][prev][cool]
                    if prior == inf:
                        continue
                    if lane == prev:
                        nxt = max(0, cool - 1)
                        cost = prior + here
                    else:
                        if cool != 0 or abs(prev - lane) != 1:
                            continue
                        nxt = transit_steps - 1
                        cost = prior + here + hysteresis + leaving(prev, i)
                    if cost < best[i][lane][nxt]:
                        best[i][lane][nxt] = cost
                        back[i][lane][nxt] = (prev, cool)

    end_lane, end_cool, end_cost = start_lane, 0, inf
    for lane in LANES:
        for cool in range(transit_steps):
            if best[steps - 1][lane][cool] < end_cost:
                end_lane, end_cool, end_cost = lane, cool, best[steps - 1][lane][cool]
    if end_cost == inf:
        return LanePlan(step, [start_lane] * steps, inf)
    lanes = [0] * steps
    lane, cool = end_lane, end_cool
    for i in range(steps - 1, -1, -1):
        lanes[i] = lane
        if i:
            lane, cool = back[i][lane][cool]
    return LanePlan(step, lanes, end_cost)


# ---------------------------------------------------------------------------
# Vertical scheduling
# ---------------------------------------------------------------------------


def solve_jump(threat: Threat, body: Body, kin: Kinematics,
               surface: float = 0.0, late: float = 0.0
               ) -> tuple[float, float] | None:
    """Every take-off time that clears this threat, as ``(earliest, latest)``.

    Returning the whole window rather than one ideal instant matters: the
    ideal instant is often unavailable -- it can land inside a jump already in
    progress, or simply have passed while the body was busy -- and a scheduler
    handed a single number can only drop the action, which is how a runner
    ends up strolling into a hurdle having "decided" to jump it. With the
    window, a late take-off that still works is available.
    """
    need = threat.y1 - surface + kin.clearance_margin
    window = kin.clearance_window(need)
    if window is None:
        return None
    tau_a, tau_b = window
    # take-off must satisfy  start + tau_a <= t_enter  and  start + tau_b >= t_exit
    earliest = threat.t_exit - tau_b
    latest = threat.t_enter - tau_a - late
    if earliest > latest:
        return None
    return (earliest, latest)


def solve_mount(t_face: float, t_back: float, rise: float, from_height: float,
                kin: Kinematics, margin: float = 0.09
                ) -> tuple[float, float] | None:
    """Every take-off time that puts the body on a train roof.

    ``t_face`` is when the train's front face arrives and ``t_back`` when its
    rear does; ``rise`` is the roof height above the base surface and
    ``from_height`` the height of the lip being left. Two conditions, and they
    pull against each other, which is why this is solved rather than tuned:

    * be *above* the roof by the time the front face arrives, or the body
      arrives inside the front of the train;
    * come back down to roof height *after* that face and before the rear one,
      or it lands short of the train, or past the end of it.

    Returns ``(earliest, latest)`` take-off, or None when the leap cannot
    reach -- which is a real answer, and the reason a ramp too far from its
    train is never laid down.
    """
    need = rise - from_height + margin
    window = kin.clearance_window(need, kin.mount_v0)
    if window is None:
        return None                      # the leap does not reach the roof
    tau_a, tau_b = window
    earliest = t_face - tau_b            # land no earlier than the face
    latest = min(t_face - tau_a,         # be up by the face
                 t_back - tau_b)         # land no later than the rear
    if earliest > latest:
        return None
    return (earliest, latest)


def solve_roll(threat: Threat, kin: Kinematics,
               late: float = 0.0) -> tuple[float, float] | None:
    """Every start time whose low window spans the contact."""
    low_a = kin.roll_low_from * kin.roll_time
    low_b = kin.roll_low_to * kin.roll_time
    earliest = threat.t_exit - low_b
    latest = threat.t_enter - low_a - late
    if earliest > latest:
        return None
    return (earliest, latest)


def schedule_vertical(threats: list[Threat], plan: LanePlan, body: Body,
                      kin: Kinematics, surface: float = 0.0,
                      not_before: float = 0.0, late: float = 0.0,
                      ) -> tuple[list[tuple[float, str]], list[Threat]]:
    """Walk the chosen lane path and book a jump or roll for what it meets.

    ``not_before`` is when the body next becomes free -- the end of a jump or
    slide already under way. Actions are booked as late as their window allows
    rather than at their ideal instant when that is what it takes to fit, and
    only reported unsolved when even the last usable moment has gone. The
    caller then feeds those back into the lane planner as hard, so it routes
    around them instead of walking into them.
    """
    booked: list[tuple[float, str]] = []
    unsolved: list[Threat] = []
    # busy windows, so two actions cannot be scheduled on top of each other
    busy: list[tuple[float, float]] = [(-math.inf, not_before)] if not_before > 0 else []

    def earliest_free(after: float, length: float) -> float | None:
        """First moment at or after ``after`` with ``length`` clear."""
        t = after
        for _ in range(len(busy) + 1):
            clash = next(((a, b) for a, b in busy if t < b and t + length > a), None)
            if clash is None:
                return t
            t = clash[1]
        return None

    relevant = []
    for th in threats:
        if th.hard or th.t_exit <= 0.0:
            continue
        mid = 0.5 * (th.t_enter + th.t_exit)
        if plan.lane_at(max(0.0, mid)) in th.lanes:
            relevant.append(th)
    for th in sorted(relevant, key=lambda t: t.t_enter):
        action = classify(th, body, kin, surface)
        if action == "clear":
            continue
        if action == "mount":
            # The one moment this can happen is the moment the body leaves the
            # ramp's lip: earlier it is still climbing and lower than the arc
            # was solved for, later there is no ramp under it. So there is no
            # window to search -- either the body is free then, or the mount is
            # off and the lane search is told to route around the train.
            start = th.mount_at
            length = kin.jump_air_time
            if start < not_before or any(a < start + length and b > start
                                         for a, b in busy):
                unsolved.append(th)
                continue
            busy.append((start, start + length))
            booked.append((start, "mount"))
            continue
        if action == "jump":
            window = solve_jump(th, body, kin, surface, late)
            length = kin.jump_air_time
        elif action == "roll":
            window = solve_roll(th, kin, late)
            length = kin.roll_time
        else:
            unsolved.append(th)
            continue
        if window is None:
            unsolved.append(th)
            continue
        earliest, latest = window
        # Aim for the middle of the window, which is where the clearance has
        # the most room on both sides; slide earlier only if the middle is
        # taken. Booking at the earliest valid instant instead means the arc
        # is already descending as the *back* of the body passes the obstacle.
        lower = max(earliest, not_before, 0.0)
        ideal = max(lower, 0.5 * (earliest + latest))
        start = earliest_free(ideal, length)
        if start is None or start > latest:
            start = earliest_free(lower, length)
        if start is None or start > latest:
            unsolved.append(th)
            continue
        busy.append((start, start + length))
        booked.append((start, action))
    booked.sort()
    return booked, unsolved
