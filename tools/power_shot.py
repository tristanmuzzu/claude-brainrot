"""Render the frames of one power-up, or of one convoy, and tile them.

The point is to *look*. Every number this project has about the runner is a
number about geometry and pacing, and the two most recent complaints -- "the
jetpack is a body teleported into the air still running" and "the other
power-ups don't seem to do anything" -- are things no probe was ever going to
say. A power-up lasts five to seven seconds and arrives every four minutes at
a spot nobody chooses, so waiting for one in ordinary footage is hopeless: this
forces it, at a known moment, and renders every frame of it.

    python tools/power_shot.py --power jet --seed 6
    python tools/power_shot.py --convoy --seed 6 --seconds 9

Writes ``shots/power/<what>/`` and a contact sheet beside it.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.config import Config                         # noqa: E402
from brainrot.engine import rl, scene as scene_api         # noqa: E402
from brainrot.engine.window import HeadlessWindow          # noqa: E402
from brainrot.palette import generate as generate_palette  # noqa: E402
from brainrot.rng import Seed                              # noqa: E402

W, H = 420, 760
DT = 1.0 / 60.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--power", default=None,
                    help="jet, boots or magnet -- forced at --warm")
    ap.add_argument("--convoy", action="store_true",
                    help="instead, wait for the runner to get onto a roof")
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument("--warm", type=float, default=12.0)
    ap.add_argument("--seconds", type=float, default=7.0)
    ap.add_argument("--every", type=int, default=4)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = Config()
    cfg.width, cfg.height = W, H
    window = HeadlessWindow()
    window.create(cfg)

    seed = Seed.for_run(args.seed)
    ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
    scene = scene_api.build("runner", ctx)

    what = args.power or ("convoy" if args.convoy else "run")
    out = Path(args.out or f"shots/power/{what}{args.seed}")
    if out.exists():
        for old in out.glob("*.png"):
            old.unlink()
    out.mkdir(parents=True, exist_ok=True)

    window.begin()
    scene.draw()
    window.end()

    def step() -> None:
        scene.update(DT)
        scene.elapsed += DT
        window.begin()
        scene.draw()
        window.end()

    for _ in range(int(args.warm / DT)):
        step()
    if args.convoy:
        # Roll on until the body is actually up on something, so the sheet is
        # of the move rather than of the approach to it.
        for _ in range(int(40.0 / DT)):
            if scene.riding:
                break
            step()
    if args.power:
        scene._take_power(args.power)

    saved = 0
    for frame in range(int(args.seconds / DT)):
        step()
        if frame % max(1, args.every) == 0:
            window.present(scene.draw)
            rl.save_frame(str(out / f"{frame:05d}.png"))
            saved += 1
    print(f"{saved} frames in {out}")

    sheet = out.with_suffix(".png")
    subprocess.run([sys.executable, str(Path(__file__).parent / "contact_sheet.py"),
                    str(out), str(sheet)], check=False)


if __name__ == "__main__":
    main()
