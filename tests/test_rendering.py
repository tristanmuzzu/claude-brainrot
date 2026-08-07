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
    """reset_colors restores the colours baked into the asset.

    The expected value is read from the .glb's own material factor rather than
    from whatever the shared asset happens to be tinted right now: models are
    cached and every scene recolours them, so sampling the "before" colour
    here just measures which test ran first.
    """
    import json
    import struct

    train = assets.load("train_cab")
    assert "body" in train.zones

    blob = assets.data_path("train_cab").read_bytes()
    length, = struct.unpack_from("<I", blob, 12)
    header = json.loads(blob[20:20 + length].decode("utf-8"))
    factor = next(m["pbrMetallicRoughness"]["baseColorFactor"]
                  for m in header["materials"] if m["name"] == "body")
    baked = tuple(round(c * 255) for c in factor[:3])

    train.recolor({"body": (10, 200, 30)})
    assert train._color_of(train.zones["body"]) == (10, 200, 30)
    train.reset_colors()
    restored = train._color_of(train.zones["body"])
    assert all(abs(a - b) <= 1 for a, b in zip(restored, baked)), (
        f"reset gave {restored}, asset declares {baked}"
    )


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


def test_a_batched_plane_is_drawn_before_the_models_above_it() -> None:
    """raylib has two draw paths and they do not run in call order.

    ``DrawPlane`` queues vertices in rlgl's render batch, which is not
    submitted until ``EndMode3D``; ``DrawModelEx`` issues its draw call
    immediately. So a ground plane drawn first is really drawn *last*, and
    loses the depth test to everything standing above it. Opaque models hide
    the damage; a transparent one does not, which is how this surfaced -- as
    cloud-shelf-shaped holes in the parkour sea with the sky showing through.

    Here the model above the plane is fully transparent, so the plane must
    still be visible through it.
    """
    window = ensure_window()
    ground = (0, 200, 0)
    cam = rl.make_camera(60.0)
    cam.position = (0.0, 5.0, 5.0)
    cam.target = (0.0, 0.0, 0.0)
    cam.up = (0.0, 1.0, 0.0)
    invisible = voxel.block_model("flush-probe", (255, 0, 0), seed=5)
    for _ in range(2):
        window.begin()
        rl.BeginMode3D(cam[0])
        rl.DrawPlane((0.0, 0.0, 0.0), (60.0, 60.0), rl.rgba(ground))
        rl.flush()
        voxel.draw_block(invisible, 0.0, 1.5, 0.0, (255, 255, 255, 0), 3.0)
        rl.EndMode3D()
        window.end()
    raw = rl.capture_frame()
    width = rl.GetScreenWidth()
    i = ((rl.GetScreenHeight() // 2) * width + width // 2) * 4
    assert tuple(raw[i:i + 3]) == ground, "the ground lost the depth test"


def test_capture_frame_returns_the_colours_it_drew() -> None:
    """Every art decision on this project was made by looking at a capture, so
    a capture that swaps red and blue silently invalidates all of them.

    The mark is deliberately asymmetric in both axes: a channel swap changes
    its colour, a vertical flip moves it to the wrong end of the frame, and
    either one fails here rather than in someone's eye a week later.
    """
    from conftest import H, W

    window = ensure_window()
    mark = (203, 96, 24)
    # Twice: a read-back can be one buffer swap behind the draw.
    for _ in range(2):
        window.begin()
        rl.DrawRectangle(0, 0, W, H // 4, rl.rgba(mark))
        window.end()
    raw = rl.capture_frame()
    width = rl.GetScreenWidth()

    def pixel(x: int, y: int) -> tuple[int, int, int]:
        i = (y * width + x) * 4
        return tuple(raw[i:i + 3])

    assert pixel(4, 4) == mark, "capture mangled the colours it was given"
    assert pixel(4, rl.GetScreenHeight() - 5) == (0, 0, 0), "capture is upside down"


def test_capture_frame_shape() -> None:
    window = ensure_window()
    window.begin()
    rl.DrawRectangle(0, 0, 10, 10, (255, 0, 0, 255))
    window.end()
    raw = rl.capture_frame()
    assert raw is not None
    assert len(raw) == rl.GetScreenWidth() * rl.GetScreenHeight() * 4
