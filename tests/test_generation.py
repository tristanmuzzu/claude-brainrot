"""Generated-content invariants.

The point of these is that generation is *structurally* correct rather than
usually correct. A layout that misbehaves one run in fifty would be a bug you
could stare at for an hour without reproducing.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys

import pytest

from conftest import H, W, ensure_window

from brainrot.engine import rl, scene as scene_api
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed


def context(run: int) -> scene_api.SceneContext:
    seed = Seed.for_run(run)
    return scene_api.SceneContext(W, H, generate_palette(seed), seed)


@pytest.fixture(scope="module", autouse=True)
def _window():
    ensure_window()


def build_runner(run: int):
    # Through the registry, so per-scene texture eviction applies -- the
    # software rasteriser's texture pool cannot survive 25 unevicted scenes.
    return scene_api.build("runner", context(run))


def build_parkour(run: int):
    return scene_api.build("parkour", context(run))


# -- runner ---------------------------------------------------------------


@pytest.mark.parametrize("run", range(1, 25))
def test_runner_corridor_is_always_reachable(run: int) -> None:
    """The safe lane may never jump more than one lane between rows.

    This is the invariant the whole generator is built around: satisfy it and
    an unwinnable track is impossible to express.
    """
    scene = build_runner(run)
    lanes = [scene._lane_clear(row) for row in range(300)]
    for i in range(1, len(lanes)):
        assert abs(lanes[i] - lanes[i - 1]) <= 1
        assert 0 <= lanes[i] <= 2


@pytest.mark.parametrize("run", range(1, 20))
def test_runner_static_trains_avoid_the_corridor(run: int) -> None:
    """Parked trains only ever occupy lanes the corridor does not."""
    scene = build_runner(run)
    while scene.next_row < 200:
        scene._spawn_row(scene.next_row)
        scene.next_row += 1
    from brainrot.scenes.runner import ROW

    for e in scene.entities:
        if e["kind"] == "train" and not e["vel"]:
            row = round((e["d"] + scene.travel - ROW * 0.5) / ROW)
            assert e["lane"] != scene._lane_clear(row), (
                f"run {run}: parked train in the corridor at row {row}"
            )


def test_runner_never_more_than_one_oncoming_train() -> None:
    """The live dodge can always answer one sweeping train; two can pin every
    lane at once, so the generator must never allow it."""
    for run in (3, 11, 42):
        scene = build_runner(run)
        for _ in range(3600):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            oncoming = [e for e in scene.entities if e["kind"] == "train" and e["vel"]]
            assert len(oncoming) <= 1


def test_runner_autopilot_makes_progress_and_collects() -> None:
    scene = build_runner(42)
    for _ in range(3600):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    assert scene.travel > 400, "runner went nowhere"
    assert scene.coins > 0, "corridor coins were never collected"
    # The runner must always sit in a legal lane.
    assert 0 <= scene.lane <= 2


def test_runner_dodges_oncoming_trains() -> None:
    """Whenever an oncoming train reaches the player, the player is not in
    its lane -- the dodge fired in time."""
    for run in (7, 23, 42):
        scene = build_runner(run)
        for _ in range(5400):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            for e in scene.entities:
                if e["kind"] == "train" and e["vel"]:
                    length = e["cars"] * 5.1
                    if -length + 1.0 < e["d"] < 1.0:
                        assert e["lane"] != scene.lane, (
                            f"run {run}: hit by oncoming train"
                        )


# -- parkour --------------------------------------------------------------


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_jumps_stay_physical(run: int) -> None:
    """Every hop must be one a jump can actually make.

    The set-pieces widened what a hop may be -- a chasm is far longer than any
    entry in the gap table and a descent falls further than any entry in the
    rise table -- so the invariant is stated against the flight solver instead
    of against the tables. A hop is legal when the ballistic solve lands on it
    inside the allowed hang time and without crossing the ground faster than a
    body can run.
    """
    from brainrot.scenes.parkour import (
        AIR_MAX, AIR_MIN, BAND, COURSE_ALT, HOP_SPEED_MAX, flight)

    scene = build_parkour(run)
    while len(scene.blocks) < 400:
        scene._spawn_block()
    blocks = scene.blocks
    for a, b in zip(blocks, blocks[1:]):
        frm, to = scene._stand_point(a), scene._stand_point(b)
        gap = math.dist((frm[0], frm[2]), (to[0], to[2]))
        dur, vy0 = flight(frm, to)
        assert AIR_MIN <= dur <= AIR_MAX, f"run {run}: {dur:.2f}s hang"
        assert gap / dur <= HOP_SPEED_MAX, f"run {run}: {gap / dur:.1f} m/s hop"
        assert 1.0 <= gap <= 8.0, f"run {run}: gap of {gap:.2f}"
        # the arc must clear the block it leaves and land on the one it aims at
        landed = frm[1] + vy0 * dur - 0.5 * 26.0 * dur * dur
        assert landed == pytest.approx(to[1], abs=1e-6)
        assert COURSE_ALT - BAND - 2 <= b["y"] <= COURSE_ALT + BAND + 2


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_uses_its_whole_vocabulary(run: int) -> None:
    """A run of any length must not be one set-piece over and over -- which is
    the single thing that made the old course tiring to look at."""
    from brainrot.scenes.parkour import SEGMENT_TABLE

    scene = build_parkour(run)
    while len(scene.blocks) < 400:
        scene._spawn_block()
    seen = {b["segment"] for b in scene.blocks}
    assert len(seen) >= 5, f"run {run}: only {seen}"
    assert seen <= {n for n, _ in SEGMENT_TABLE} | {"start"}
    # every block carries a material the catalogue knows how to draw
    for blk in scene.blocks:
        assert blk["style"] in scene.styles
        for deco in blk["deco"]:
            assert deco["style"] in scene.styles


def test_parkour_orbs_are_placed_where_the_body_will_be() -> None:
    """Every orb the generator hangs is collected, because it is hung on the
    flight path rather than near it. A missed orb means the arc that was solved
    at generation is not the arc that gets flown."""
    scene = build_parkour(12)
    for _ in range(7200):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    assert scene.orbs > 40, f"only {scene.orbs} orbs in two minutes"
    assert scene.orbs_missed == 0, f"{scene.orbs_missed} orbs went past uncollected"


def test_parkour_leaves_no_transform_on_a_shared_block_model() -> None:
    """The held kit is assembled from the same block models the course is
    drawn with. A rotation left on one of them tilts every block of that
    material in the world from the next frame onward -- which is where the
    slabs of brick lying at an angle over the sea came from."""
    window = ensure_window()
    scene = build_parkour(10)          # a run whose kit is a tool, not a block
    for _ in range(2):
        window.begin()
        scene.draw()
        window.end()
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    for name, style in scene.styles.items():
        m = style["model"].transform
        got = [getattr(m, f"m{i}") for i in range(16)]
        assert got == pytest.approx(identity), f"{name} kept a transform"


def test_parkour_draw_is_the_same_frame_twice() -> None:
    """Drawing without updating must draw the same picture.

    Every screenshot this scene has ever been judged from is captured by
    presenting a frame a second time, so a draw that quietly advances the
    camera means the frame reviewed is not the frame the simulation is in.
    """
    window = ensure_window()
    scene = build_parkour(6)
    for _ in range(120):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60

    def render() -> bytes:
        for _ in range(3):
            window.begin()
            scene.draw()
            window.end()
        return rl.capture_frame()

    assert render() == render()


def test_parkour_orb_hitbox_is_the_model_it_draws() -> None:
    """The box comes from the orb model pushed through the orb's own draw
    transform, so it cannot disagree with the picture."""
    from brainrot.engine.collide import model_aabb, placed
    from brainrot.scenes.parkour import ORB_SCALE

    scene = build_parkour(3)
    orb = next(o for blk in scene.blocks for o in blk["orbs"])
    want = placed(model_aabb(scene._model("orb")),
                  (orb["x"], orb["y"], orb["z"]),
                  scale=(ORB_SCALE, ORB_SCALE, ORB_SCALE))
    assert scene.orb_box(orb) == want


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_course_does_not_self_overlap(run: int) -> None:
    """Blocks near each other in time must not land on each other in space."""
    scene = build_parkour(run)
    while len(scene.blocks) < 400:
        scene._spawn_block()
    blocks = scene.blocks
    for i in range(len(blocks)):
        for j in range(i + 2, min(i + 7, len(blocks))):
            d = math.dist((blocks[i]["x"], blocks[i]["z"]),
                          (blocks[j]["x"], blocks[j]["z"]))
            assert d > 0.9, f"run {run}: blocks {i} and {j} overlap ({d:.2f})"


@pytest.mark.parametrize("run", range(1, 15))
def test_parkour_altitude_stays_in_band(run: int) -> None:
    """The course wanders further than it used to -- that is the point of the
    descent and staircase set-pieces -- but it still has to come back."""
    from brainrot.scenes.parkour import BAND, COURSE_ALT

    scene = build_parkour(run)
    while len(scene.blocks) < 400:
        scene._spawn_block()
    for blk in scene.blocks:
        assert COURSE_ALT - BAND - 2 <= blk["y"] <= COURSE_ALT + BAND + 2
    # and it must actually use the room: a course pinned to one altitude has
    # no verticality however wide the band is
    heights = [blk["y"] for blk in scene.blocks]
    assert max(heights) - min(heights) > 8, f"run {run}: course is flat"


def test_parkour_advances_forever() -> None:
    from brainrot.scenes.parkour import AIR_MAX, AIR_MIN

    scene = build_parkour(9)
    for _ in range(3600):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    assert scene.distance > 60
    assert AIR_MIN <= scene.air_dur <= AIR_MAX
    # the trail is bounded: memory cannot grow with distance
    assert len(scene.blocks) < 40
    assert sum(len(b["orbs"]) for b in scene.blocks) < 60
    assert sum(len(b["deco"]) for b in scene.blocks) < 400


def test_parkour_lands_on_the_block_it_aimed_for() -> None:
    """The ballistic solve must actually deliver the player onto the target
    block, offsets included, for every hop."""
    scene = build_parkour(4)
    for _ in range(7200):
        prev_phase = scene.phase
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
        if prev_phase == "air" and scene.phase == "ground":
            blk = scene.blocks[scene.jump_index]
            assert abs(scene.stand[0] - blk["x"]) <= 1.31
            assert abs(scene.stand[2] - blk["z"]) <= 1.31
            assert scene.stand[1] == pytest.approx(scene.surface(blk))


# -- every scene ----------------------------------------------------------


@pytest.mark.parametrize("name", ["runner", "parkour"])
def test_scene_renders_and_covers_the_frame(name: str) -> None:
    window = ensure_window()
    scene = scene_api.build(name, context(21))
    for _ in range(90):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    for _ in range(2):
        window.begin()
        scene.draw()
        window.end()
    raw = rl.capture_frame()
    assert raw is not None and len(raw) == W * H * 4
    # Fully covered (opaque) and actually drawn (not one flat colour).
    assert all(raw[i + 3] == 255 for i in range(0, len(raw), 4001 * 4 - (4001 * 4) % 4))
    samples = {raw[i:i + 3] for i in range(0, len(raw) - 3, 997 * 4)}
    assert len(samples) > 12, f"{name} rendered almost nothing"


@pytest.mark.parametrize("name", ["runner", "parkour"])
def test_scene_is_deterministic_for_a_seed(name: str) -> None:
    window = ensure_window()

    def render() -> bytes:
        scene = scene_api.build(name, context(77))
        for _ in range(60):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
        for _ in range(2):
            window.begin()
            scene.draw()
            window.end()
        return rl.capture_frame()

    assert render() == render()


def test_scene_choice_is_stable_per_run() -> None:
    names = ["runner", "parkour"]
    for run in range(1, 50):
        seed = Seed.for_run(run)
        assert scene_api.choose(names, seed) == scene_api.choose(names, seed)


def test_scene_choice_uses_the_whole_roster() -> None:
    names = ["runner", "parkour"]
    picked = {scene_api.choose(names, Seed.for_run(run)) for run in range(1, 60)}
    assert picked == set(names)


def test_available_populates_the_registry_on_its_own() -> None:
    """It must not depend on someone else having imported the scenes first."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from brainrot.engine.scene import available; print('SCENES=' + ','.join(available()))",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "BRAINROT_HEADLESS": "1", "SDL_VIDEODRIVER": "dummy"},
    )
    assert result.returncode == 0, result.stderr
    line = next(l for l in result.stdout.splitlines() if l.startswith("SCENES="))
    assert set(line.removeprefix("SCENES=").split(",")) == {"runner", "parkour"}
