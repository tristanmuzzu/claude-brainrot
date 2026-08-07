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

import math

import pytest

from conftest import H, W, ensure_window

from brainrot.engine import rl, scene as scene_api
from brainrot.engine.collide import AABB, placed, rotate_y
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed
from brainrot.scenes import runnerplan as plan
from brainrot.scenes.runner import BASE_SPEED, RAIL_TOP, RAMP_SECONDS, TOP_SPEED

DT = 1 / 60


@pytest.fixture(scope="module", autouse=True)
def _window():
    ensure_window()


def build(run: int):
    seed = Seed.for_run(run)
    return scene_api.build(
        "runner", scene_api.SceneContext(W, H, generate_palette(seed), seed))


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
def test_runner_never_intersects_an_obstacle(run: int) -> None:
    scene = simulate(run, 45.0)
    assert scene.contacts == 0, (
        f"run {run}: {scene.contacts} frames inside an obstacle, deepest "
        f"{scene.worst_penetration:.3f} m -- {scene.last_contact}"
    )
    assert scene.travel > 300, "runner went nowhere"


@pytest.mark.parametrize("run", [7, 8, 9, 10])
def test_runner_never_intersects_at_top_speed(run: int) -> None:
    """The speed the old trigger window broke at, exercised directly.

    Warmed past the acceleration ramp so the whole run happens at TOP_SPEED,
    where a jump covers 9 m of track and every margin is at its thinnest.
    """
    scene = simulate(run, 40.0, warm=RAMP_SECONDS + 5.0)
    assert scene.speed == pytest.approx(TOP_SPEED)
    assert scene.contacts == 0, (
        f"run {run} at top speed: {scene.contacts} frames inside an obstacle, "
        f"deepest {scene.worst_penetration:.3f} m -- {scene.last_contact}"
    )


def test_runner_still_collects_while_staying_clean() -> None:
    """Avoiding everything by standing still would also score zero contacts."""
    scene = simulate(11, 45.0)
    assert scene.contacts == 0
    assert scene.coins > 40, f"only {scene.coins} coins -- is it dodging the corridor?"


def test_generator_leaves_at_most_one_lane_blocked_by_trains() -> None:
    """Trains cannot be jumped or slid under, so two abreast has no answer."""
    for run in (3, 12, 25, 31):
        scene = build(run)
        for _ in range(int(60 / DT)):
            scene.update(DT)
            scene.elapsed += DT
            blocked = {e["lane"] for e in scene.entities
                       if e["kind"] == "train"
                       and -e["cars"] * 5.2 < e["d"] < 8.0}
            assert len(blocked) <= 1, f"run {run}: trains blocking lanes {blocked}"


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
    """Moves scale with speed; that is what keeps them usable at the top."""
    spans = [plan.Kinematics.for_speed(v).jump_air_time * v
             for v in (BASE_SPEED, 11.0, 13.0, TOP_SPEED)]
    assert max(spans) - min(spans) < 1.0, spans


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
