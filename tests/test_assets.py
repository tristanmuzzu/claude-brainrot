"""The recorded geometry, and the gameplay contracts that rest on it.

``assets/measure.py`` writes ``metrics.json`` from the committed .glb files,
and the runner plans every jump and slide against those numbers. That makes
the file a load-bearing part of the scene rather than a cache: a rebuilt asset
whose measurements are not refreshed leaves the runner solving for a body and
a set of obstacles that no longer exist.

So: re-measure here and compare, then assert the handful of height
relationships the moves depend on. A hoarding that drifts 20 cm lower stops
being something a slide can pass under, and nothing else in the suite would
notice.
"""

from __future__ import annotations

import pytest

from conftest import ensure_window

from brainrot import assets
from brainrot.engine.collide import model_aabb, placed, posed_aabb
from brainrot.scenes import runnerplan as plan
from brainrot.scenes.runner import (
    CHAR_SCALE, GANTRY_Y, RAIL_TOP, TOP_SPEED, _body_profile, _obstacle_boxes,
)

TOL = 1e-3


@pytest.fixture(scope="module", autouse=True)
def _window():
    ensure_window()


def test_every_asset_has_recorded_metrics() -> None:
    recorded = set(assets.metrics()["assets"])
    assert recorded == set(assets.available())


@pytest.mark.parametrize("name", sorted(assets.available()))
def test_recorded_bounds_match_the_committed_model(name: str) -> None:
    """Catches a rebuilt asset whose measurements were never refreshed."""
    live = model_aabb(assets.load(name).model)
    recorded = assets.bounds(name)
    for axis in ("x0", "y0", "z0", "x1", "y1", "z1"):
        assert getattr(live, axis) == pytest.approx(getattr(recorded, axis), abs=TOL), (
            f"{name}.{axis} drifted -- re-run `python assets/measure.py`")


def test_recorded_pose_extents_match_the_skinned_mesh() -> None:
    ch = assets.load("character")
    data = assets.metrics("character")["clips"]
    samples = assets.metrics()["samples"]
    for clip, entry in data.items():
        for i, frame in enumerate(entry["frames"]):
            ch.pose(clip, i / samples)
            live = posed_aabb(ch.model)
            for k, axis in enumerate(("x0", "y0", "z0", "x1", "y1", "z1")):
                assert getattr(live, axis) == pytest.approx(frame[k], abs=TOL), (
                    f"character/{clip} frame {i} {axis} drifted")


# -- the height relationships the moves depend on --------------------------


def test_a_slide_fits_under_the_hoarding_and_a_run_does_not() -> None:
    """The whole reason the roll exists.

    Before this was measured, the "low" gantry's soffit sat at 2.28 m against
    a 2.39 m runner: rolling under it achieved nothing, and the head clipped
    the sign every time.
    """
    body = _body_profile()
    soffit = RAIL_TOP + _obstacle_boxes()["hoarding"].y0
    standing = RAIL_TOP + body.stand_h
    sliding = RAIL_TOP + body.roll_h
    assert soffit < standing, "a running body would pass under it untouched"
    assert sliding + plan.Kinematics().clearance_margin < soffit, (
        f"a slide reaches {sliding:.2f} m, soffit is at {soffit:.2f} m")


def test_gantries_clear_the_runner_entirely() -> None:
    """They are scenery. Hung at head height they are scenery that hits you."""
    body = _body_profile()
    soffit = GANTRY_Y + _obstacle_boxes()["gantry"].y0
    assert soffit > RAIL_TOP + body.stand_h + 0.5


def test_a_jump_clears_the_barrier_with_room() -> None:
    body = _body_profile()
    top = _obstacle_boxes()["barrier"].y1
    for speed in (8.5, 11.0, TOP_SPEED):
        kin = plan.Kinematics.for_speed(speed)
        assert kin.jump_apex > top + kin.clearance_margin, (
            f"apex {kin.jump_apex:.2f} m does not clear a {top:.2f} m hurdle")
    assert body.stand_h > top, "the hurdle would pass overhead"


def test_the_slide_never_sinks_through_the_track() -> None:
    """A roll that drops the hips without folding the legs takes the feet
    with it -- 33 cm under the ballast, in the version that shipped."""
    lowest = min(f[1] for f in
                 assets.metrics("character")["clips"]["roll"]["frames"])
    assert lowest * CHAR_SCALE > -RAIL_TOP, (
        f"the slide reaches {lowest:.3f} m, below the railhead at {-RAIL_TOP}")


def test_the_slide_holds_its_lowest_height_for_the_planned_window() -> None:
    """solve_roll assumes the body is low across roll_low_from..roll_low_to.

    The clip is authored as a trapezoid for exactly this reason; a sine dips
    through its lowest point in an instant and the runner does not fit under
    anything at the slow end of the speed range.
    """
    kin = plan.Kinematics()
    low = assets.clip_bounds("character", "roll", kin.roll_low_from, kin.roll_low_to)
    deepest = assets.clip_bounds("character", "roll", 0.45, 0.55)
    assert low.y1 - deepest.y1 < 0.25, (
        "the roll is not flat across the window solve_roll relies on")


def test_the_body_box_is_the_drawn_character() -> None:
    """Width and depth come from the mesh, through the draw's own transform."""
    body = _body_profile()
    scale = (CHAR_SCALE, CHAR_SCALE, CHAR_SCALE)
    run = placed(assets.clip_bounds("character", "run"), (0, 0, 0), 90.0, scale)
    assert body.half_w == pytest.approx(max(abs(run.x0), run.x1), abs=0.05)
    assert body.stand_h == pytest.approx(run.y1, abs=0.1)
    # A slide reaches further along the track than a run: legs go out in front.
    assert body.roll_half_d > body.half_d
