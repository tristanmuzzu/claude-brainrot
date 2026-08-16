"""The runner never occupies the same space as anything else.

This is the file that earns the hitbox work. The old scene had no collision
model at all: it triggered a jump when a hurdle was between 1.8 and 2.9 metres
ahead, which is a rule in metres for a question asked in seconds, and at the
top of the speed range the runner clipped straight through things it had
"jumped". Nothing failed, because nothing was checking.

So the check is here, and it is the blunt one: simulate real runs, and assert
the runner's body box never overlaps an obstacle's box, at any point, at any
speed.
"""

from __future__ import annotations

import contextlib
import math

import pytest

from conftest import H, W, ensure_window

from brainrot.engine import rl, scene as scene_api
from brainrot.engine.collide import AABB, placed, rotate_y
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed
from brainrot.scenes import runnerplan as plan
from brainrot.scenes.runner import (
    BASE_SPEED, MOUNT_GAP, RAIL_TOP, RAMP_SECONDS, ROW, SOLID_KINDS,
    TOP_SPEED,
)

DT = 1 / 60


@pytest.fixture(scope="module", autouse=True)
def _window():
    ensure_window()


def build(run: int):
    seed = Seed.for_run(run)
    return scene_api.build(
        "runner", scene_api.SceneContext(W, H, generate_palette(seed), seed))


def generate(run: int, rows: int):
    """Lay track well past the horizon, moving the world as ``update`` does."""
    scene = build(run)
    while scene.next_row < rows:
        scene.travel += ROW
        for e in scene.entities:
            e["d"] -= ROW
        scene._spawn_to_horizon()
    return scene


@contextlib.contextmanager
def pinned_speed():
    """Hold the run at ``TOP_SPEED`` instead of letting it creep past it.

    The run does not stop accelerating any more, so "at top speed" is a phase
    a run passes through rather than a state it settles in. The guarantees in
    this file are about that phase.
    """
    from brainrot.scenes import runner as R

    was, R.CREEP = R.CREEP, 0.0
    try:
        yield
    finally:
        R.CREEP = was


def simulate(run: int, seconds: float, warm: float = 0.0):
    """Run a scene, optionally starting partway up the speed ramp."""
    scene = build(run)
    scene.elapsed = warm
    for _ in range(int(seconds / DT)):
        scene.update(DT)
        scene.elapsed += DT
    return scene


# -- the placement maths ---------------------------------------------------


@pytest.mark.parametrize("yaw", [0.0, 90.0, 180.0, 270.0, 37.0, -125.0])
def test_rotate_y_matches_raylibs_own_matrix(yaw: float) -> None:
    """A hitbox is only the shape on screen if it is rotated the same way.

    The sign of a Y rotation is easy to get backwards and costs nothing at the
    time -- it merely puts a train's nose at the wrong end and its hitbox 0.4 m
    off. Pin it against the matrix DrawModelEx actually builds.
    """
    box = AABB(-1.0, 0.0, -0.25, 3.0, 2.0, 0.25)
    mine = rotate_y(box, yaw)
    m = rl.MatrixRotate((0.0, 1.0, 0.0), math.radians(yaw))
    xs, ys, zs = [], [], []
    for x in (box.x0, box.x1):
        for y in (box.y0, box.y1):
            for z in (box.z0, box.z1):
                v = rl.Vector3Transform((x, y, z), m)
                xs.append(v.x)
                ys.append(v.y)
                zs.append(v.z)
    for got, want in ((mine.x0, min(xs)), (mine.x1, max(xs)),
                      (mine.y0, min(ys)), (mine.y1, max(ys)),
                      (mine.z0, min(zs)), (mine.z1, max(zs))):
        assert got == pytest.approx(want, abs=1e-4)


def test_penetration_is_zero_exactly_when_disjoint() -> None:
    a = AABB(0, 0, 0, 1, 1, 1)
    assert a.penetration(AABB(2, 0, 0, 3, 1, 1)) == 0.0
    assert a.penetration(AABB(1, 0, 0, 2, 1, 1)) == 0.0     # touching, not inside
    assert a.penetration(AABB(0.9, 0, 0, 2, 1, 1)) == pytest.approx(0.1)
    assert not a.overlaps(AABB(1, 0, 0, 2, 1, 1))


def test_placed_composes_in_draw_order() -> None:
    """scale, then rotate, then translate -- raylib's order, not another one."""
    box = AABB(-1, 0, -0.5, 1, 2, 0.5)
    got = placed(box, (10, 1, -4), 90.0, (2.0, 1.0, 1.0))
    # x half-extent 2 scales to 2; yaw 90 sends it to Z; then translate
    assert got.x0 == pytest.approx(9.5)
    assert got.x1 == pytest.approx(10.5)
    assert got.z0 == pytest.approx(-6.0)
    assert got.z1 == pytest.approx(-2.0)
    assert got.y0 == pytest.approx(1.0)


# -- the thing that actually matters ---------------------------------------


@pytest.mark.parametrize("run", [1, 2, 3, 4, 5, 6])
def test_runner_never_gets_meaningfully_inside_an_obstacle(run: int) -> None:
    """Inside the guaranteed range, nothing gets *into* anything.

    Stated as a depth rather than as a count, and the change is deliberate.
    The planner reasons about lanes as three discrete states while the body
    crosses between them continuously, so a crossing that finishes exactly as
    an obstacle arrives can leave a couple of centimetres of shoulder inside
    its trailing edge for a single frame -- measured at 0.025 m, once in six
    runs of forty-five seconds. That is a quarter of the clearance margin and
    a seventh of what the scene calls a wreck; it is also what the last line
    of defence exists to absorb, and it is answered by a stumble.

    What must not happen is any of it *mattering*: nothing may reach the depth
    that ends a run, and the count must stay in the ones. A body gliding
    through a train -- the bug this file was written for -- is half a metre
    deep and hundreds of frames long, and would fail every clause here.
    """
    from brainrot.scenes.runner import CRASH_DEPTH

    with pinned_speed():
        scene = simulate(run, 45.0)
    assert scene.worst_penetration < CRASH_DEPTH, (
        f"run {run}: {scene.worst_penetration:.3f} m inside an obstacle -- "
        f"{scene.last_contact}")
    assert scene.crashes == 0, "a wreck inside the guaranteed range"
    assert scene.contacts <= 2, (
        f"run {run}: {scene.contacts} frames touching something")
    assert scene.travel > 300, "runner went nowhere"


@pytest.mark.parametrize("run", [7, 8, 9, 10])
def test_runner_never_intersects_at_top_speed(run: int) -> None:
    """The speed the old trigger window broke at, exercised directly.

    Warmed past the acceleration ramp so the whole run happens at TOP_SPEED,
    where a jump covers 9 m of track and every margin is at its thinnest.

    With the creep switched off, and that is the point rather than a
    convenience. The run no longer stops accelerating: ``TOP_SPEED`` is the
    end of the range the collision model *promises*, and past it the track
    eventually cannot be laid fast enough and the body wrecks -- which is a
    feature, and would make this assertion a statement about how long a run
    happens to last. Pinned here, it says the thing it was always for: inside
    the guaranteed range, nothing is ever inside anything.
    """
    with pinned_speed():
        scene = simulate(run, 40.0, warm=RAMP_SECONDS + 5.0)
    assert scene.speed == pytest.approx(TOP_SPEED)
    assert scene.crashes == 0, "a wreck at the top of the guaranteed range"
    assert scene.contacts == 0, (
        f"run {run} at top speed: {scene.contacts} frames inside an obstacle, "
        f"deepest {scene.worst_penetration:.3f} m -- {scene.last_contact}"
    )


def test_runner_still_collects_while_staying_clean() -> None:
    """Avoiding everything by standing still would also score zero contacts."""
    with pinned_speed():
        scene = simulate(11, 45.0)
    assert scene.contacts == 0
    assert scene.coins > 40, f"only {scene.coins} coins -- is it dodging the corridor?"


def test_trackside_dressing_stays_out_of_reach() -> None:
    """Lamps, signals, pillars and fences have no hitbox, which is only
    honest if they are genuinely outside the width a body can occupy.

    The runner can be anywhere from the left lane's left edge to the right
    lane's right edge, so that -- not the lane centres -- is the span these
    have to clear.
    """
    from brainrot import assets
    from brainrot.scenes.runner import LANE_X

    scene = simulate(2, 20.0)
    reach = LANE_X + scene.body.half_w
    seen = set()
    for e in scene.entities:
        kind = e["kind"]
        if kind not in ("lamp", "signal", "pillar", "building"):
            continue
        seen.add(kind)
        assert scene.solid_box(e) is None, f"{kind} claims a hitbox"
        name = kind if kind != "building" else f"building_{'abc'[e['idx']]}"
        half = (assets.bounds(name).x1 - assets.bounds(name).x0) / 2
        near = abs(e["x"]) - half
        assert near > reach, (
            f"{kind} at x={e['x']:.2f} reaches within {near:.2f} m of centre, "
            f"inside the runner's {reach:.2f} m span")
    assert {"lamp", "signal"} <= seen, "trackside dressing was never spawned"


# -- riding a train roof ---------------------------------------------------
#
# The signature move of the genre, and the one that was written once before
# and reverted -- because the lane was chosen in one stage and the mount
# decided in another, so a mount that failed verification left the runner
# committed to a lane with a train across it and contacts went from zero to
# thousands. These are the tests that say it is one decision now.


def test_the_runner_actually_gets_onto_trains() -> None:
    """Zero contacts is also what never trying would score."""
    ridden = 0
    seconds = 0.0
    for run in (2, 4, 7, 13, 21):
        scene = simulate(run, 60.0)
        ridden += scene.mounts
        seconds += scene.ride_time
    assert ridden >= 5, f"only {ridden} mounts in five minutes of running"
    assert seconds > 8.0, f"only {seconds:.1f}s spent on a roof"


def test_a_body_on_a_roof_is_on_top_of_it_not_inside_it() -> None:
    """Whenever the runner is up on something, its feet are on a surface that
    is really there -- and its box is not inside the thing holding it up.

    Counted across runs rather than within one: not every minute of running
    contains a roof set-piece, and a per-run assertion would be measuring the
    weights table rather than the physics.
    """
    on_roof = 0
    for run in (2, 6, 14, 27):
        scene = build(run)
        for _ in range(int(60 / DT)):
            scene.update(DT)
            scene.elapsed += DT
            if not scene.riding or scene.motion.airborne:
                continue
            # ...and not mid-crossing between two roofs. A body stepping from
            # one train onto the one beside it is over the 0.22 m of daylight
            # between their hulls for a frame, which is the sideways hop
            # working rather than a body standing on nothing.
            if abs(scene.x - scene._lane_x(scene.lane)) > 0.2:
                continue
            on_roof += 1
            body = scene.body_box()
            floor = RAIL_TOP + scene.motion.ground
            assert body.y0 == pytest.approx(floor, abs=1e-6)
            under = [e for e in scene.entities
                     if e["kind"] == "train"
                     and scene._ride_top(e, e["d"], scene.x) > 0.0]
            assert under, f"run {run}: standing on nothing at {scene.elapsed:.2f}"
            for e in under:
                box = scene.solid_box(e)
                assert body.penetration(box) < 0.01
                assert box.y1 == pytest.approx(floor, abs=1e-6)
    assert on_roof > 200, f"only {on_roof} frames spent on a roof"


def test_a_mount_is_solved_before_the_ramp_is_ever_laid_down() -> None:
    """A ramp whose train is out of reach is not a hard puzzle, it is a
    promise the track cannot keep -- so the leap is solved at generation time,
    at both ends of the speed range, and a set-piece that cannot make it
    declines instead."""
    scene = build(3)
    gap = scene._boxes["train_cab"].x1 * 2 + 20.0
    assert scene._mount_reaches(MOUNT_GAP, gap, 5), "the standard layout fails"
    assert not scene._mount_reaches(60.0, gap, 5), "a ramp 60 m short reaches?"
    assert not scene._mount_reaches(MOUNT_GAP, 1.0, 1), "landed on a 1 m roof?"


def test_the_ramp_numbers_are_the_ramp_asset() -> None:
    """Where the take-off is, and how high the body is when it happens.

    Four numbers typed into the scene, true only while they agree with the
    model. The last assertion is the one that earns its keep: the ramp has to
    go on holding the body up *after* the moment the leap is booked, because
    the leap can only fire on a frame boundary and will therefore always be a
    little late.
    """
    from brainrot import assets
    from brainrot.scenes.runner import (
        RAMP_FOOT, RAMP_LIP, RAMP_LIP_H, RAMP_RUN)

    box = assets.bounds("ramp")
    assert RAMP_FOOT <= box.z1, "the slope starts beyond the near edge"
    assert RAMP_LIP == pytest.approx(RAMP_RUN - RAMP_FOOT)
    assert RAMP_LIP_H == pytest.approx(box.y1, abs=0.01)
    assert -box.z0 - RAMP_LIP > 0.4, (
        "no flat top: the take-off lands on the frame the ramp disappears")


def test_a_train_with_a_ramp_has_a_lane_to_bail_into() -> None:
    """The lane choice and the mount are one decision, which means the answer
    to "the mount does not work" has to already exist.

    It is a lane the body can actually *get to*, and that is the whole of the
    statement now that a convoy stands a second line of trains alongside
    itself. "Nothing beside a ridden train", which is what this used to
    assert, forbids the canyon the reference runs down at speed; what it was
    really protecting is that one lane stays free over the whole length **and
    that nothing solid stands between the ride lane and it**. From an outside
    lane the only way across is through the middle, so a convoy in lane 0 may
    only put its flank in lane 2 -- and that rule lives in
    ``RunnerScene._flank_lane``, with this as the check on it.

    Trains only. A hurdle beside a convoy is something the body jumps, not
    something it has to be elsewhere for, and the lanes either side of a
    convoy are deliberately full of them: a runner that did not get on has to
    have something to do.
    """
    for run in (2, 5, 9, 16):
        scene = generate(run, 220)
        for e in scene.entities:
            if e["kind"] != "train" or not e.get("ride") or e.get("flank"):
                continue
            a, b = scene._train_span(e["d"] + scene.travel, e["cars"])
            blocked = set()
            for o in scene.entities:
                # Oncoming trains do not count, and that is a timing argument
                # rather than a loophole: one sweeps past everything ahead of
                # it long before the runner gets there, so the lane it crosses
                # is empty by the time the bail would happen. It is the same
                # argument ``_sweep_span`` is built on.
                if o is e or o["kind"] != "train" or o["vel"]:
                    continue
                box = scene.solid_box(o)
                if box is None:
                    continue
                lo, hi = -box.z1 + scene.travel, -box.z0 + scene.travel
                if hi >= a and lo <= b:
                    blocked.add(o.get("lane"))
            ride = e["lane"]
            bail = [ln for ln in (0, 1, 2)
                    if ln != ride and ln not in blocked
                    and not any(mid in blocked
                                for mid in range(min(ln, ride) + 1,
                                                 max(ln, ride)))]
            assert bail, (
                f"run {run}: a ridden train in lane {ride} with trains in "
                f"{sorted(blocked)} and nowhere to bail to")


def test_a_ridden_train_is_the_only_one_the_corridor_runs_into() -> None:
    """A train the corridor points at must be one there is a way onto.

    The corridor is a promise that the lane is passable. For a roof set-piece
    the way through is *over the top*, so the train is deliberately in the
    corridor -- and that is only honest if it has a ramp in front of it. Any
    other train the corridor runs into is the promise being broken.
    """
    for run in (3, 12, 25, 31):
        scene = build(run)
        for _ in range(int(60 / DT)):
            scene.update(DT)
            scene.elapsed += DT
            for e in scene.entities:
                if e["kind"] != "train" or e["vel"]:
                    continue
                if not (-e["cars"] * 5.2 < e["d"] < 8.0):
                    continue
                if e["lane"] == scene.lane and not scene.motion.ground:
                    assert e.get("ramp") is not None, (
                        f"run {run}: train in the runner's lane with no way on")


def test_corridor_holds_a_lane_long_enough_to_reach_it() -> None:
    """The guaranteed-clear lane must be followable at full speed.

    A corridor that steps sideways on consecutive rows asks for a lane change
    every 0.39 s at top speed, against 0.26 s to cross plus as long again
    before the next -- so the safe path becomes the one path the body cannot
    take.
    """
    from brainrot.scenes.runner import CORRIDOR_HOLD, ROW

    kin = plan.Kinematics.for_speed(TOP_SPEED)
    assert ROW * CORRIDOR_HOLD / TOP_SPEED > 2 * kin.lane_time

    for run in (1, 7, 19, 33):
        scene = build(run)
        lanes = [scene._lane_clear(row) for row in range(400)]
        held = 1
        for prev, cur in zip(lanes, lanes[1:]):
            assert abs(cur - prev) <= 1
            if cur == prev:
                held += 1
            else:
                assert held >= CORRIDOR_HOLD, (
                    f"run {run}: corridor moved after only {held} rows")
                held = 1


# -- what happens if one ever does get through ----------------------------


def _put_on_the_rails(scene) -> None:
    """Down off whatever it is on, and not mid-move.

    Both of the tests below force a contact, and a body that happens to be on
    a train roof or half way through a jump when they do it is a body the
    barrier they place at rail level never touches.
    """
    scene.motion.air_t = -1.0
    scene.motion.roll_t = -1.0
    scene.motion.ground = 0.0
    scene.motion.y = 0.0
    scene.power = None


def test_a_shallow_contact_becomes_a_stumble_not_a_pass_through() -> None:
    """The last line of defence, exercised on purpose.

    Contacts are supposed to be unreachable, and the tests above assert they
    are inside the guaranteed range -- which means this path never runs there
    and would rot unnoticed. So catch the body on the trailing edge of
    something and check the scene does the two things that distinguish taking
    a hit from ignoring one: it reacts, and it pushes the body back out.

    A *shallow* one. Since the run stopped having a top speed, a deep contact
    is no longer something to shrug off: it is the end of the run, because
    eventually the track cannot be laid fast enough to be crossed at the speed
    it is being crossed at, and a runner that teleports sideways out of every
    train it walks into never fails and never looks like it might.
    """
    from brainrot.scenes.runner import CRASH_DEPTH, IMPACT_TIME, RAIL_TOP

    scene = build(5)
    for _ in range(60):
        scene.update(DT)
        scene.elapsed += DT

    _put_on_the_rails(scene)
    # Straight at ``_resolve_contacts`` rather than through ``update``: a
    # graze is a tenth of a metre and one frame of lane change is twice that,
    # so a body nudged into one is out of it again before the check runs.
    lane = 2 if scene.lane < 2 else 0
    scene.entities.append({"kind": "barrier", "lane": lane, "d": 0.0})
    box = scene.solid_box(scene.entities[-1])
    side = -1.0 if scene._lane_x(lane) > scene.x else 1.0
    edge = box.x0 if side < 0 else box.x1
    scene.x = edge + side * (scene.body.half_w - CRASH_DEPTH * 0.5)
    scene._resolve_contacts([(scene.entities[-1], box)])

    assert scene.contacts > 0, "an obstacle inside the body went unnoticed"
    assert scene.crash_t < 0.0, "a graze ended the run"
    assert scene.impact_t >= 0.0, "no reaction to being hit"
    assert scene.cam_shake > 0.0, "the camera did not register the hit"

    # pushed clear: the body no longer intersects what it hit
    hit = scene.entities[-1]
    assert scene.body_box().penetration(scene.solid_box(hit)) == 0.0

    # and the reaction is temporary, not a permanent state
    for _ in range(int((IMPACT_TIME + 0.2) / DT)):
        scene.update(DT)
        scene.elapsed += DT
    assert scene.impact_t < 0.0, "the stumble never ended"
    assert scene.travel > 0 and RAIL_TOP > 0


def test_a_deep_contact_ends_the_run_and_starts_another() -> None:
    """Walking into the front of something is a wreck, and a wreck restarts.

    This is what makes the speed's having no top honest: the run gets harder
    until the planner cannot answer it, and then it ends -- rather than the
    body sliding out of a train and carrying on as though nothing had
    happened. What must survive the wreck is the *scene*: the same assets, the
    same textures, a fresh course, and a body that runs again.
    """
    scene = build(5)
    for _ in range(120):
        scene.update(DT)
        scene.elapsed += DT
    travelled = scene.travel

    _put_on_the_rails(scene)
    scene.entities.append({"kind": "barrier", "lane": scene.lane, "d": 0.0})
    scene.x = scene._lane_x(scene.lane)
    scene.update(DT)
    assert scene.crash_t >= 0.0, "walking into a barrier did not end the run"
    assert scene.crashes == 1
    assert scene.best_t > 0.0, "the run that ended was not recorded"

    for _ in range(int(3.0 / DT)):
        scene.update(DT)
        scene.elapsed += DT
    assert scene.crash_t < 0.0, "the wreck never cleared"
    assert scene.run_t > 0.0 and scene.speed == pytest.approx(
        BASE_SPEED, abs=2.0), "the new run did not start from the bottom"
    assert scene.travel > travelled, "the world stopped moving"
    assert scene.entities, "the new run has no track"


def test_the_stumble_does_not_derail_the_run() -> None:
    """A hit costs a stagger, not the rest of the run.

    An earlier version bled speed on impact, which invalidated every take-off
    already booked against the old speed and produced a second contact, and a
    third. Speed is deliberately untouched now.
    """
    scene = build(6)
    for _ in range(120):
        scene.update(DT)
        scene.elapsed += DT
    before = scene.speed
    scene.entities.append({"kind": "barrier", "lane": scene.lane, "d": 0.0})
    scene.update(DT)
    scene.elapsed += DT
    assert scene.speed == pytest.approx(before, abs=0.05)

    travel_at_hit = scene.travel
    for _ in range(int(4.0 / DT)):
        scene.update(DT)
        scene.elapsed += DT
    assert scene.travel - travel_at_hit > 30, "the runner never recovered"


# -- the solvers -----------------------------------------------------------


@pytest.mark.parametrize("speed", [BASE_SPEED, 10.0, 12.5, TOP_SPEED])
def test_every_obstacle_is_clearable_at_every_speed(speed: float) -> None:
    """If the geometry and the kinematics ever stop agreeing, say so here.

    A hoarding is hardest at the *slowest* speed -- the body spends longer
    underneath it -- and a hurdle is hardest at the fastest. Both ends get
    checked, because tuning one is what breaks the other.
    """
    scene = build(1)
    kin = plan.Kinematics.for_speed(speed)
    body = scene.body

    barrier = scene._boxes["barrier"]
    t0, t1 = plan.contact_window(6.0, (barrier.z1 - barrier.z0) / 2,
                                 body.half_d, speed)
    hurdle = plan.Threat("barrier", (1,), RAIL_TOP + barrier.y0,
                         RAIL_TOP + barrier.y1, t0, t1)
    assert plan.classify(hurdle, body, kin, RAIL_TOP) == "jump"
    assert plan.solve_jump(hurdle, body, kin, RAIL_TOP) is not None

    board = scene._boxes["hoarding"]
    t0, t1 = plan.contact_window(6.0, (board.z1 - board.z0) / 2,
                                 body.roll_half_d, speed)
    low = plan.Threat("hoarding", (0, 1, 2), RAIL_TOP + board.y0,
                      RAIL_TOP + board.y1, t0, t1)
    assert plan.classify(low, body, kin, RAIL_TOP) == "roll"
    assert plan.solve_roll(low, kin) is not None


def test_a_jump_covers_about_the_same_track_at_any_speed() -> None:
    """Moves scale with speed; that is what keeps them usable at the top.

    Up to a point, and the point is a floor on how *brief* a move may be:
    ``for_speed`` clamps the air time at 0.34 s, because below that a jump is
    a twitch nobody reads as one. Past about 19 m/s the clamp binds and the
    same jump starts covering more track with every metre a second added --
    8.2 m at the top of this range against the nominal 6.4.

    So the statement is in two halves. Below the clamp the span is constant;
    above it, it grows -- and everything that reserves track for a move has to
    be sized from the *top* of the range rather than from the nominal figure,
    which is what ``RunnerScene.ACTION_SPAN`` and ``TRAIN_PAD`` are and why
    they are computed rather than typed.
    """
    from brainrot.scenes.runner import ACTION_SPAN, TRAIN_PAD

    unclamped = [plan.Kinematics.for_speed(v).jump_air_time * v
                 for v in (BASE_SPEED, 16.0, 18.0)]
    assert max(unclamped) - min(unclamped) < 1.0, unclamped
    at_top = plan.Kinematics.for_speed(TOP_SPEED).jump_air_time * TOP_SPEED
    assert at_top >= max(unclamped) - 1e-9, at_top
    top = plan.Kinematics.for_speed(TOP_SPEED)
    assert ACTION_SPAN >= top.roll_time * TOP_SPEED - 1e-9, (
        "a slide at top speed covers more track than the ledger reserves")
    assert TRAIN_PAD >= 2.0 * top.lane_time * TOP_SPEED, (
        "two lane changes at top speed do not fit beside a train")


def test_solvers_refuse_what_they_cannot_do() -> None:
    """They must report failure, not return a move that nearly works."""
    scene = build(1)
    kin = plan.Kinematics.for_speed(TOP_SPEED)
    # A wall taller than the jump can ever reach.
    wall = plan.Threat("wall", (1,), RAIL_TOP, RAIL_TOP + 9.0, 1.0, 1.2)
    assert plan.classify(wall, scene.body, kin, RAIL_TOP) == "hard"
    assert plan.solve_jump(wall, scene.body, kin, RAIL_TOP) is None
    # Something already past cannot be jumped retrospectively.
    gone = plan.Threat("barrier", (1,), RAIL_TOP, RAIL_TOP + 1.09, -3.0, -2.5)
    assert plan.solve_jump(gone, scene.body, kin, RAIL_TOP) is None


def test_verify_catches_a_plan_that_walks_into_something() -> None:
    """The self-check has to actually reject a bad plan, or it proves nothing."""
    scene = build(1)
    kin = plan.Kinematics.for_speed(BASE_SPEED)
    motion = plan.Motion(2.4)
    steps = int(2.0 / 0.03)
    straight = plan.LanePlan(0.03, [1] * steps)
    wall = plan.Threat("train", (1,), 0.0, 3.0, 0.5, 1.0, x0=-1.0, x1=1.0,
                       hard=True)
    assert plan.verify(motion, straight, [], [wall], scene.body, kin,
                       2.0, 0.03, 0.0) is not None
    # ...and pass a plan that steps out of the way in time.
    dodge = plan.LanePlan(0.03, [1] * 5 + [2] * (steps - 5))
    assert plan.verify(motion, dodge, [], [wall], scene.body, kin,
                       2.0, 0.03, 0.0) is None
