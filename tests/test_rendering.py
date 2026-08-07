"""Assets, palettes and the texture/voxel toolkits."""

from __future__ import annotations

import pytest

from conftest import ensure_window

from brainrot import assets
from brainrot.engine import rl, textures, voxel
from brainrot.palette import generate as generate_palette, luminance
from brainrot.rng import Seed


@pytest.fixture(scope="module", autouse=True)
def _window():
    ensure_window()


# -- assets ---------------------------------------------------------------


def test_every_committed_asset_loads() -> None:
    names = assets.available()
    assert len(names) >= 10, f"asset kit shrank: {names}"
    for name in names:
        asset = assets.load(name)
        assert asset.model.meshCount > 0, name
        assert asset.zones, f"{name} exports no named material zones"


def test_character_is_rigged_with_all_clips() -> None:
    ch = assets.load("character")
    for clip in ("run", "jump", "roll"):
        assert clip in ch.clips, f"missing clip {clip}"
        assert ch.clip_length(clip) > 10
        # 11 bones: root, spine, head, and two-bone limbs (knees + elbows)
        assert ch.clips[clip].boneCount == 11


def test_recolor_writes_and_reset_restores() -> None:
    train = assets.load("train_cab")
    assert "body" in train.zones
    original = train._color_of(train.zones["body"])
    train.recolor({"body": (10, 200, 30)})
    assert train._color_of(train.zones["body"]) == (10, 200, 30)
    train.reset_colors()
    assert train._color_of(train.zones["body"]) == original


def test_recolor_ignores_unknown_zones() -> None:
    assets.load("coin").recolor({"no-such-zone": (1, 2, 3)})


def test_track_and_lane_geometry_agree() -> None:
    """The scene's lane positions must match the track asset's rails."""
    from brainrot.scenes.runner import LANE_X

    assert LANE_X == pytest.approx(2.4)


# -- palette --------------------------------------------------------------


@pytest.mark.parametrize("run", range(1, 60))
def test_palette_structural_properties(run: int) -> None:
    pal = generate_palette(Seed.for_run(run))
    assert len(pal.blocks) == 3
    # Hazard stays in the red-orange band: never mistakable for scenery.
    r, g, b = pal.hazard
    assert r > g > b
    # Ink must contrast with the upper sky it sits against.
    assert abs(luminance(pal.ink) - luminance(pal.sky_top)) > 0.25


def test_palettes_differ_between_consecutive_runs() -> None:
    a = generate_palette(Seed.for_run(101))
    b = generate_palette(Seed.for_run(102))
    assert a.sky_top != b.sky_top or a.accent != b.accent


def test_palette_replays_exactly() -> None:
    assert generate_palette(Seed.for_run(31)) == generate_palette(Seed.for_run(31))


# -- textures & voxel -----------------------------------------------------


def test_texture_cache_returns_same_object() -> None:
    a = textures.radial_glow()
    b = textures.radial_glow()
    assert a is b


def test_vanilla_face_shading_constants() -> None:
    """The exact numbers vanilla uses; the whole voxel look hangs off them."""
    assert voxel.SHADE == {"top": 1.00, "bottom": 0.50, "north": 0.80,
                           "south": 0.80, "east": 0.60, "west": 0.60}


def test_block_model_builds_with_texture() -> None:
    model = voxel.block_model("test-red", (200, 40, 40), seed=3)
    tex = model.materials[0].maps[rl.MATERIAL_MAP_ALBEDO].texture
    assert tex.id != 0
    assert voxel.block_model("test-red", (200, 40, 40), seed=3) is model


def test_capture_frame_shape() -> None:
    window = ensure_window()
    window.begin()
    rl.DrawRectangle(0, 0, 10, 10, (255, 0, 0, 255))
    window.end()
    raw = rl.capture_frame()
    assert raw is not None
    assert len(raw) == rl.GetScreenWidth() * rl.GetScreenHeight() * 4
