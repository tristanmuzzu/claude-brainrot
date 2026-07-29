"""Perspective projection."""

from __future__ import annotations

import pytest

from brainrot.engine.projection import (
    NEAR_PLANE,
    Camera,
    fog_amount,
    jump_height,
    project,
)

W, H = 360, 640


@pytest.fixture
def cam() -> Camera:
    return Camera(x=0.0, y=2.0, z=0.0, focal=340.0, horizon=0.5, far=90.0)


def test_points_behind_the_near_plane_are_dropped(cam: Camera) -> None:
    assert project(cam, 0, 0, cam.z, W, H) is None
    assert project(cam, 0, 0, cam.z + NEAR_PLANE * 0.5, W, H) is None
    assert project(cam, 0, 0, cam.z + 10, W, H) is not None


def test_distant_things_are_smaller(cam: Camera) -> None:
    near = project(cam, 0, 0, 10, W, H)
    far = project(cam, 0, 0, 40, W, H)
    assert near is not None and far is not None
    assert near.scale > far.scale
    assert far.scale == pytest.approx(near.scale / 4, rel=1e-6)


def test_equal_spacing_compresses_with_distance(cam: Camera) -> None:
    """The motion illusion: constant Z steps must bunch up toward the horizon."""
    ys = []
    for z in range(5, 60, 5):
        p = project(cam, 0, 0, z, W, H)
        assert p is not None
        ys.append(p.y)
    gaps = [ys[i - 1] - ys[i] for i in range(1, len(ys))]
    assert all(gaps[i] < gaps[i - 1] for i in range(1, len(gaps)))


def test_everything_converges_on_the_horizon(cam: Camera) -> None:
    horizon = H * cam.horizon
    for x in (-20.0, 0.0, 20.0):
        p = project(cam, x, 0.0, 5000.0, W, H)
        assert p is not None
        assert abs(p.y - horizon) < 1.0
        assert abs(p.x - W * 0.5) < 2.0


def test_centre_of_view_maps_to_centre_of_screen(cam: Camera) -> None:
    p = project(cam, cam.x, cam.y, cam.z + 20, W, H)
    assert p is not None
    assert p.x == pytest.approx(W * 0.5)
    assert p.y == pytest.approx(H * cam.horizon)


def test_fog_is_absent_up_close_and_total_at_the_far_plane(cam: Camera) -> None:
    assert fog_amount(cam, 1.0) == 0.0
    assert fog_amount(cam, cam.far) == pytest.approx(1.0)
    assert 0.0 < fog_amount(cam, cam.far * 0.7) < 1.0


def test_jump_arc_starts_and_ends_on_the_ground() -> None:
    assert jump_height(0.0, 2.5, 0.72) == 0.0
    assert jump_height(0.72, 2.5, 0.72) == pytest.approx(0.0)
    assert jump_height(0.36, 2.5, 0.72) == pytest.approx(2.5)
    # Outside the jump window there is no arc at all.
    assert jump_height(-1.0, 2.5, 0.72) == 0.0
    assert jump_height(2.0, 2.5, 0.72) == 0.0
