"""Generated-content invariants.

The point of these is that generation is *structurally* correct rather than
usually correct. A layout that is unwinnable one run in fifty would be a bug you
could stare at for an hour without reproducing.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from brainrot.engine import scene as scene_api  # noqa: E402
from brainrot.palette import generate as generate_palette  # noqa: E402
from brainrot.rng import Seed  # noqa: E402
from brainrot.scenes.marbles import MarbleScene  # noqa: E402
from brainrot.scenes.runner import LANE_X, RunnerScene  # noqa: E402
from brainrot.scenes.tower import DROP_MAX, REACH_MAX, TowerScene  # noqa: E402

W, H = 360, 640


def context(run: int) -> scene_api.SceneContext:
    seed = Seed.for_run(run)
    return scene_api.SceneContext(W, H, generate_palette(seed), seed)


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((W, H))
    yield
    pygame.quit()


# -- runner ---------------------------------------------------------------


@pytest.mark.parametrize("run", range(1, 25))
def test_runner_corridor_is_always_reachable(run: int) -> None:
    """The safe lane may never jump more than one lane between rows.

    This is the invariant the whole generator is built around: satisfy it and
    an unwinnable track is impossible to express.
    """
    scene = RunnerScene(context(run))
    lanes = []
    for _ in range(300):
        lanes.append(scene._safe_lane)
        scene._generate_row()

    for i in range(1, len(lanes)):
        assert abs(lanes[i] - lanes[i - 1]) <= 1
        assert 0 <= lanes[i] <= 2


@pytest.mark.parametrize("run", range(1, 15))
def test_runner_never_blocks_every_lane_with_trains(run: int) -> None:
    """At least one lane is always passable without a lane change of >1."""
    scene = RunnerScene(context(run))
    for _ in range(200):
        scene._generate_row()

    # Group trains by the rows they occupy and check no z-slice is fully walled.
    trains = [o for o in scene.obstacles if o.kind == "train"]
    for probe in range(0, 3000, 2):
        z = float(probe)
        blocked = {t.lane for t in trains if t.z <= z <= t.z_end}
        assert len(blocked) < 3, f"all lanes blocked at z={z}"


def test_runner_autopilot_survives_a_long_session() -> None:
    """Drive the runner for ~2 minutes and assert it mostly stays alive."""
    scene = RunnerScene(context(42))
    crashes = 0
    was_crashed = False
    for _ in range(3600):  # 120s at 30fps
        scene.update(1 / 30)
        if scene.player.crashed and not was_crashed:
            crashes += 1
        was_crashed = scene.player.crashed

    # It should make real progress rather than dying in place.
    assert scene.player.z > 1500
    # Crashes are a feature, but a competent autopilot should not be constantly
    # eating obstacles.
    assert crashes < 40, f"autopilot crashed {crashes} times"


def test_runner_collects_coins() -> None:
    """Coins trace the safe corridor, so following it should pick some up."""
    scene = RunnerScene(context(11))
    for _ in range(1800):
        scene.update(1 / 30)
    assert scene.player.coins > 0


def test_runner_lanes_are_distinct() -> None:
    assert len(set(LANE_X)) == 3


# -- tower ----------------------------------------------------------------


@pytest.mark.parametrize("run", range(1, 20))
def test_tower_path_steps_stay_within_jump_range(run: int) -> None:
    """Every hop must be physically plausible, by construction."""
    scene = TowerScene(context(run))
    path = scene.path
    assert len(path) > 20

    for a, b in zip(path, path[1:]):
        drop = a.y - b.y
        assert 0 < drop <= DROP_MAX + 1e-6
        reach = ((a.x - b.x) ** 2 + (a.z - b.z) ** 2) ** 0.5
        # Arc distance is clamped by construction; allow a little slack for the
        # chord-versus-arc difference and radius drift.
        assert reach <= REACH_MAX + 1.5, f"hop of {reach:.2f} at run {run}"


def test_tower_descends_monotonically() -> None:
    scene = TowerScene(context(5))
    ys = [n.y for n in scene.path]
    assert all(ys[i] < ys[i - 1] for i in range(1, len(ys)))


def test_tower_regenerates_at_the_bottom() -> None:
    """Reaching the last node must yield a new tower, not a stall."""
    scene = TowerScene(context(8))
    first = [(n.x, n.y, n.z) for n in scene.path]
    for _ in range(4000):
        scene.update(1 / 30)
    second = [(n.x, n.y, n.z) for n in scene.path]
    assert first != second


# -- marbles --------------------------------------------------------------


def test_marbles_stay_inside_the_course() -> None:
    """Walls must actually contain the field, including at top speed."""
    from brainrot.scenes.marbles import WORLD_W

    scene = MarbleScene(context(3))
    for _ in range(2400):
        scene.update(1 / 30)
        for m in scene.marbles:
            assert -1.0 < m.x < WORLD_W + 1.0, f"marble escaped at x={m.x}"


def test_marbles_make_downward_progress() -> None:
    scene = MarbleScene(context(4))
    start = max(m.y for m in scene.marbles)
    for _ in range(900):
        scene.update(1 / 30)
    assert max(m.y for m in scene.marbles) > start + 20


def test_marble_positions_change() -> None:
    """A race with a fixed running order is not a race."""
    scene = MarbleScene(context(12))
    orders = set()
    for step in range(1800):
        scene.update(1 / 30)
        if step % 120 == 0:
            ranked = tuple(
                sorted(range(len(scene.marbles)), key=lambda i: -scene.marbles[i].y)
            )
            orders.add(ranked)
    assert len(orders) > 1


# -- every scene ----------------------------------------------------------


@pytest.mark.parametrize("name", ["runner", "tower", "marbles"])
def test_scene_renders_without_error(name: str) -> None:
    surface = pygame.Surface((W, H))
    scene = scene_api.build(name, context(21))
    for _ in range(120):
        scene.update(1 / 30)
        scene.elapsed += 1 / 30
        scene.draw(surface)

    # A scene must fully cover the strip; a transparent gap would show the
    # desktop through the middle of the overlay.
    assert surface.get_at((W // 2, H // 2))[3] == 255
    assert surface.get_at((2, 2))[3] == 255


@pytest.mark.parametrize("name", ["runner", "tower", "marbles"])
def test_scene_is_deterministic_for_a_seed(name: str) -> None:
    def render() -> bytes:
        surface = pygame.Surface((W, H))
        scene = scene_api.build(name, context(77))
        for _ in range(60):
            scene.update(1 / 30)
            scene.elapsed += 1 / 30
        scene.draw(surface)
        return pygame.image.tobytes(surface, "RGB")

    assert render() == render()


def test_scene_choice_is_stable_per_run() -> None:
    names = ["runner", "tower", "marbles"]
    for run in range(1, 50):
        seed = Seed.for_run(run)
        assert scene_api.choose(names, seed) == scene_api.choose(names, seed)


def test_scene_choice_uses_the_whole_roster() -> None:
    names = ["runner", "tower", "marbles"]
    picked = {scene_api.choose(names, Seed.for_run(run)) for run in range(1, 60)}
    assert picked == set(names)
