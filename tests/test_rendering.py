"""Texture generation, quad warping and the box model."""

from __future__ import annotations

import math
import random

import numpy as np
import pygame
import pytest

from brainrot.engine import model, pixelart, warp

W, H = 360, 640


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((W, H))
    yield
    pygame.quit()


# -- pixel art ------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(pixelart.BLOCKS))
def test_block_textures_are_16x16_rgb(name: str) -> None:
    arr = pixelart.BLOCKS[name](random.Random(1))
    assert arr.shape == (16, 16, 3)
    assert arr.dtype == np.uint8


@pytest.mark.parametrize("name", sorted(pixelart.BLOCKS))
def test_block_textures_are_deterministic(name: str) -> None:
    a = pixelart.BLOCKS[name](random.Random(9))
    b = pixelart.BLOCKS[name](random.Random(9))
    assert np.array_equal(a, b)


@pytest.mark.parametrize("name", sorted(pixelart.BLOCKS))
def test_block_textures_have_internal_structure(name: str) -> None:
    """A texture that is one flat colour would defeat the whole point."""
    arr = pixelart.BLOCKS[name](random.Random(3))
    assert len(np.unique(arr.reshape(-1, 3), axis=0)) > 3


def test_grass_side_is_green_on_top_and_brown_below() -> None:
    """The fringe is the single most recognisable detail in the idiom."""
    arr = pixelart.grass_side(random.Random(5))
    top = arr[0].astype(int)
    bottom = arr[15].astype(int)
    # Green channel dominates at the top; red dominates in the soil below.
    assert (top[:, 1] > top[:, 0]).mean() > 0.9
    assert (bottom[:, 0] > bottom[:, 1]).mean() > 0.9


def test_grass_fringe_is_ragged() -> None:
    """A straight boundary reads as a painted stripe, not as grass."""
    arr = pixelart.grass_side(random.Random(11))
    depths = []
    for x in range(16):
        depth = 0
        for y in range(16):
            r, g, b = (int(c) for c in arr[y, x])
            if g <= r:
                break
            depth += 1
        depths.append(depth)
    assert len(set(depths)) > 1


def test_humanoid_skin_has_every_part() -> None:
    skin = pixelart.humanoid_skin(
        random.Random(2), (232, 178, 136), (58, 42, 32), (60, 120, 200), (70, 72, 140), (110, 80, 60)
    )
    for part in ("head_face", "head_side", "head_back", "head_top", "torso", "arm", "leg"):
        assert part in skin
    # Parts are authored at their real pixel dimensions.
    assert skin["head_face"].shape == (8, 8, 3)
    assert skin["torso"].shape == (12, 8, 3)
    assert skin["arm"].shape == (12, 4, 3)


def test_face_has_eyes() -> None:
    """Two bright pixel pairs on an otherwise skin-toned field."""
    skin = pixelart.humanoid_skin(
        random.Random(4), (232, 178, 136), (58, 42, 32), (60, 120, 200), (70, 72, 140), (110, 80, 60)
    )
    face = skin["head_face"].astype(int)
    # The eye whites are far brighter than the skin around them.
    assert face.sum(axis=2).max() > (232 + 178 + 136)


# -- warping --------------------------------------------------------------


def _checker() -> np.ndarray:
    arr = np.zeros((16, 16, 3), dtype=np.uint8)
    for y in range(16):
        for x in range(16):
            arr[y, x] = (255, 255, 255) if (x + y) % 2 else (0, 0, 0)
    return arr


def test_warp_draws_within_its_quad() -> None:
    warp.reset_cache()
    surface = pygame.Surface((W, H))
    surface.fill((255, 0, 255))
    corners = [(100.0, 100.0), (160.0, 100.0), (160.0, 160.0), (100.0, 160.0)]
    assert warp.draw_quad(surface, _checker(), "checker", corners)

    # Inside the quad the magenta background is gone.
    assert surface.get_at((130, 130))[:3] != (255, 0, 255)
    # Well outside it is untouched.
    assert surface.get_at((10, 10))[:3] == (255, 0, 255)


def test_warp_is_cached_across_identical_shapes() -> None:
    """The cache is the only reason this is affordable at all."""
    warp.reset_cache()
    surface = pygame.Surface((W, H))
    for i in range(20):
        x = 10.0 + i
        warp.draw_quad(
            surface, _checker(), "checker", [(x, 10.0), (x + 40, 10.0), (x + 40, 50.0), (x, 50.0)]
        )
    hits, misses = warp.stats()
    assert misses == 1, f"same shape rebuilt {misses} times"
    assert hits == 19


def test_warp_rejects_degenerate_quads() -> None:
    warp.reset_cache()
    surface = pygame.Surface((W, H))
    # Edge-on: zero height.
    assert not warp.draw_quad(
        surface, _checker(), "checker", [(0.0, 0.0), (40.0, 0.0), (40.0, 0.0), (0.0, 0.0)]
    )
    # Sub-pixel.
    assert not warp.draw_quad(
        surface, _checker(), "checker", [(0.0, 0.0), (0.4, 0.0), (0.4, 0.4), (0.0, 0.4)]
    )


def test_adjacent_quads_leave_no_gap() -> None:
    """Neighbouring faces must not show background between them.

    Rounding the origin and the edges independently used to leave a one-pixel
    seam between every pair of blocks, which is far more visible than the
    overlap that fixing it introduces.
    """
    warp.reset_cache()
    surface = pygame.Surface((W, H))
    surface.fill((255, 0, 255))
    solid = np.full((16, 16, 3), (40, 200, 90), dtype=np.uint8)

    for i in range(6):
        x = 40.0 + i * 30.7  # deliberately fractional
        warp.draw_quad(
            surface, solid, "solid", [(x, 200.0), (x + 30.7, 200.0), (x + 30.7, 260.0), (x, 260.0)]
        )

    strip = [surface.get_at((x, 230))[:3] for x in range(50, 210)]
    assert (255, 0, 255) not in strip, "background visible through a seam"


def test_winding_detects_facing() -> None:
    clockwise = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert warp.facing_camera(clockwise)
    assert not warp.facing_camera(clockwise[::-1])


# -- box model ------------------------------------------------------------


def _projector(cam_z: float = -6.0, focal: float = 420.0):
    def project(x: float, y: float, z: float):
        depth = z - cam_z
        if depth <= 0.4:
            return None
        scale = focal / depth
        return (W * 0.5 + x * scale, H * 0.45 + (2.0 - y) * scale, depth)

    return project


def test_box_corners_count_and_extent() -> None:
    box = model.Box(x=0, y=0, z=0, w=2, h=4, d=6)
    corners = box.corners()
    assert len(corners) == 8
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    zs = [c[2] for c in corners]
    assert max(xs) - min(xs) == pytest.approx(2)
    assert max(ys) - min(ys) == pytest.approx(4)
    assert max(zs) - min(zs) == pytest.approx(6)


def test_pitch_rotates_about_the_pivot_not_the_centre() -> None:
    """A limb must swing from its joint, or it slides instead of rotating."""
    pivot = (0.0, 1.0, 0.0)
    box = model.Box(x=0, y=0.5, z=0, w=0.25, h=1.0, d=0.25, pitch=0.0, pivot=pivot)
    rotated = model.Box(
        x=0, y=0.5, z=0, w=0.25, h=1.0, d=0.25, pitch=1.2, pivot=pivot
    )
    # The pivot end barely moves; the far end sweeps.
    top_before = max(c[1] for c in box.corners())
    top_after = max(c[1] for c in rotated.corners())
    bottom_before = min(c[1] for c in box.corners())
    bottom_after = min(c[1] for c in rotated.corners())
    assert abs(top_after - top_before) < 0.35
    assert abs(bottom_after - bottom_before) > 0.35


def test_draw_box_renders_something() -> None:
    surface = pygame.Surface((W, H))
    surface.fill((255, 0, 255))
    atlas = pixelart.build_atlas(random.Random(6))
    model.draw_box(
        surface, _projector(), model.Box(x=0, y=0, z=2, w=1, h=1, d=1, default="cobblestone"), atlas
    )
    changed = sum(
        1
        for x in range(0, W, 4)
        for y in range(0, H, 4)
        if surface.get_at((x, y))[:3] != (255, 0, 255)
    )
    assert changed > 20


def test_humanoid_proportions_match_the_spec() -> None:
    """Two blocks tall, built from 8x12x4 and 4x12x4 parts."""
    figure = model.Humanoid()
    boxes = figure.parts(0.0, 0.0, 0.0, swing=0.0)
    assert len(boxes) == 6  # two legs, torso, two arms, head

    tops = [max(c[1] for c in b.corners()) for b in boxes]
    bottoms = [min(c[1] for c in b.corners()) for b in boxes]
    assert max(tops) == pytest.approx(2.0, abs=1e-6)
    assert min(bottoms) == pytest.approx(0.0, abs=1e-6)


def test_head_scale_grows_upward_from_the_neck() -> None:
    """An oversized head must not sink into the shoulders."""
    figure = model.Humanoid()
    normal = figure.parts(0.0, 0.0, 0.0, swing=0.0)[-1]
    big = figure.parts(0.0, 0.0, 0.0, swing=0.0, head_scale=1.5)[-1]
    assert min(c[1] for c in big.corners()) == pytest.approx(
        min(c[1] for c in normal.corners()), abs=1e-6
    )
    assert max(c[1] for c in big.corners()) > max(c[1] for c in normal.corners())


def test_walk_cycle_swings_limbs_in_opposition() -> None:
    figure = model.Humanoid()
    boxes = figure.parts(0.0, 0.0, 0.0, swing=math.pi / 2, amplitude=0.8)
    left_leg, right_leg = boxes[0], boxes[1]
    assert left_leg.pitch == pytest.approx(-right_leg.pitch)
    assert abs(left_leg.pitch) > 0.1

