"""What a frame of each scene costs, measured against the other one.

Absolute milliseconds off this machine are close to worthless. With a browser
and a container runtime busy, both scenes measure two to four times higher than
they do on a quiet box, and there is no way to tell from the number which of
those you are looking at. What *is* stable is the ratio between the two scenes
measured in the same process minutes apart, so that is what this reports and
that is the number a change should be judged on.

Two things the harness has to get right or the reading is fiction. The window
must be a ``HeadlessWindow`` with ``SetTargetFPS(0)``: ``DesktopWindow`` has
vsync on and will report a flat 16.6 ms whatever the scene does. And only one
scene may be alive at a time -- ``scene_api.build`` evicts the previous scene's
textures and block models -- so the two are built alternately, round by round,
which also averages out whatever else the machine started doing halfway
through.

    python tools/frame_cost.py --rounds 5 --frames 400
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.config import Config                       # noqa: E402
from brainrot.engine import rl                           # noqa: E402
from brainrot.engine import scene as scene_api           # noqa: E402
from brainrot.engine.window import HeadlessWindow        # noqa: E402
from brainrot.palette import generate as generate_palette  # noqa: E402
from brainrot.rng import Seed                            # noqa: E402

W, H = 420, 760
DT = 1.0 / 60.0
#: Frames run before the clock starts: the first few build textures, warm the
#: batch and pay for whatever the scene lazily allocates.
WARM = 60


def measure(window, name: str, run: int, frames: int, settle: int) -> float:
    """Median milliseconds for one frame of ``name``, update and draw."""
    seed = Seed.for_run(run)
    scene = scene_api.build(name, scene_api.SceneContext(
        W, H, generate_palette(seed), seed))
    # Run it in to the state it spends most of its life in -- for parkour that
    # is past the difficulty ramp, where there is the most on screen.
    for _ in range(settle):
        scene.update(DT)
        scene.elapsed += DT
    for _ in range(WARM):
        window.begin()
        scene.draw()
        window.end()

    samples = []
    for _ in range(frames):
        t0 = time.perf_counter()
        scene.update(DT)
        scene.elapsed += DT
        window.begin()
        scene.draw()
        window.end()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(samples)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--frames", type=int, default=400)
    ap.add_argument("--run", type=int, default=21)
    ap.add_argument("--settle", type=int, default=2400,
                    help="frames simulated before timing starts")
    ap.add_argument("--scenes", nargs="*", default=["runner", "parkour"])
    args = ap.parse_args()

    cfg = Config()
    cfg.width, cfg.height = W, H
    window = HeadlessWindow()
    window.create(cfg)
    rl.SetTargetFPS(0)          # or every reading is the refresh rate

    got: dict[str, list[float]] = {n: [] for n in args.scenes}
    for r in range(args.rounds):
        for name in args.scenes:
            ms = measure(window, name, args.run, args.frames, args.settle)
            got[name].append(ms)
            print(f"round {r + 1} {name:<8} {ms:6.2f} ms")

    print()
    med = {n: statistics.median(v) for n, v in got.items()}
    for name, ms in med.items():
        spread = max(got[name]) - min(got[name])
        print(f"{name:<8} {ms:6.2f} ms/frame   (spread {spread:.2f} ms "
              f"over {args.rounds} rounds)")
    if "runner" in med and "parkour" in med and med["runner"]:
        print(f"\nparkour / runner = {med['parkour'] / med['runner']:.3f}"
              "   <- the number that means something")


if __name__ == "__main__":
    main()
