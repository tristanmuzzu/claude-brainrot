"""Regenerate the images in ``docs/media`` from the current build.

    python assets/media.py            # everything
    python assets/media.py runner     # one scene's stills and gif

Renders through the same path ``brainrot shoot`` uses, so what lands in the
README is what the engine actually draws -- on whichever rasteriser is
installed, since capture correction is measured rather than assumed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("BRAINROT_HEADLESS", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from PIL import Image                                    # noqa: E402

from brainrot.engine import rl, scene as scene_api       # noqa: E402
from brainrot.engine.window import HeadlessWindow        # noqa: E402
from brainrot.config import Config                       # noqa: E402
from brainrot.palette import generate as generate_palette  # noqa: E402
from brainrot.rng import Seed                            # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "media"
W, H = 360, 640

#: (file stem, scene, run) for the stills. Runs chosen for their palettes.
STILLS = [
    ("runner-day", "runner", 3),
    ("runner-night", "runner", 8),
    ("parkour-day", "parkour", 5),
    ("parkour-dusk", "parkour", 9),
]
#: (file stem, scene, run, seconds, fps) for the animations
CLIPS = [
    ("runner", "runner", 3, 6.0, 20),
    ("parkour", "parkour", 5, 6.0, 20),
]
#: the contact sheet: sixteen runs, sixteen looks
VARIETY_RUNS = range(1, 17)
VARIETY_COLS = 8


def _window():
    cfg = Config()
    cfg.width, cfg.height = W, H
    window = HeadlessWindow()
    window.create(cfg)
    return window


def _render(window, name: str, run: int, seconds: float, keep_every: int = 0):
    """Run a scene and return frames as PIL images (the last one, or many)."""
    seed = Seed.for_run(run)
    scene = scene_api.build(
        name, scene_api.SceneContext(W, H, generate_palette(seed), seed))
    frames = []
    dt = 1 / 60
    total = int(seconds / dt)
    for i in range(total):
        scene.update(dt)
        scene.elapsed += dt
        want = keep_every and i % keep_every == 0
        if not want and i != total - 1:
            continue
        # Twice: the window is double-buffered, so a single draw leaves the
        # frame we want in the back buffer and captures whatever was in front.
        for _ in range(2):
            window.begin()
            scene.draw()
            window.end()
        raw = rl.capture_frame()
        if raw is None:
            continue
        img = Image.frombytes("RGBA", (W, H), raw).convert("RGB")
        if want or (not keep_every and i == total - 1):
            frames.append(img)
    return frames


def main(argv: list[str]) -> int:
    wanted = set(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    window = _window()

    for stem, name, run in STILLS:
        if wanted and name not in wanted and stem not in wanted:
            continue
        frames = _render(window, name, run, 5.0)
        frames[-1].save(OUT / f"{stem}.png")
        print(f"[media] {stem}.png")

    for stem, name, run, seconds, fps in CLIPS:
        if wanted and name not in wanted and stem not in wanted:
            continue
        every = max(1, round(60 / fps))
        frames = _render(window, name, run, seconds, keep_every=every)
        if not frames:
            continue
        # Quantise together so the palette is stable across the loop rather
        # than shimmering frame to frame.
        pal = frames[0].quantize(colors=192, method=Image.MEDIANCUT)
        frames = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
        frames[0].save(OUT / f"{stem}.gif", save_all=True,
                       append_images=frames[1:], loop=0,
                       duration=int(1000 / fps), optimize=True)
        print(f"[media] {stem}.gif ({len(frames)} frames)")

    if not wanted or "variety" in wanted:
        tiles = []
        for run in VARIETY_RUNS:
            name = scene_api.choose(["runner", "parkour"], Seed.for_run(run))
            tiles.append(_render(window, name, run, 4.0)[-1])
        cols = VARIETY_COLS
        rows = (len(tiles) + cols - 1) // cols
        tw, th = W // 2, H // 2
        sheet = Image.new("RGB", (cols * tw, rows * th), (16, 16, 20))
        for i, tile in enumerate(tiles):
            sheet.paste(tile.resize((tw, th), Image.LANCZOS),
                        ((i % cols) * tw, (i // cols) * th))
        sheet.save(OUT / "variety.png")
        print(f"[media] variety.png ({len(tiles)} runs)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
