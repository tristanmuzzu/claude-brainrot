"""Where does a runner run die, and how fast was it going?

The runner's speed has no top: it compounds until the body cannot answer what
is in front of it, and then the run ends and starts again. That makes two
questions the ordinary probe cannot answer, because it averages over the whole
run rather than over the speed:

* **how long does a run last, and at what speed does it end** -- the thing the
  owner asked for by name, and the thing that decides whether a strip left up
  for a long thinking turn is watchable or a smear;
* **does anything break at a particular speed**. Every frame is bucketed by
  the speed it was drawn at, so "the collision model starts producing wrecks
  around 26 m/s" is a reading rather than a belief. It was a belief, it was in
  ``CLAUDE.md`` for days, and it was wrong by a factor of five: measured, the
  32-36 m/s band had **zero** contacts over 276 seconds.

Run: ``python tools/speed_probe.py --runs 12 --seconds 240``

Nothing here is pinned. This is the probe for the part of the run the
guarantees deliberately do not cover -- ``tools/runner_probe.py``'s safety
section is the one that pins the creep and speaks for the guaranteed range.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.config import Config
from brainrot.engine import scene as scene_api
from brainrot.engine.window import HeadlessWindow
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed

W, H = 420, 760
DT = 1.0 / 60.0
#: Width of a speed bucket, in metres a second.
BAND = 4
_window = None


def ensure_window():
    """One offscreen window per process, as tests/conftest.py does it."""
    global _window
    if _window is None:
        cfg = Config()
        cfg.width, cfg.height = W, H
        _window = HeadlessWindow()
        _window.create(cfg)
    return _window


def band(v: float) -> str:
    lo = int(v // BAND) * BAND
    return f"{lo:3d}-{lo + BAND:3d}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=12)
    ap.add_argument("--seconds", type=float, default=240.0)
    args = ap.parse_args()

    ensure_window()
    wrecks: list[tuple[float, float, str]] = []
    unsolved = defaultdict(int)
    frames = defaultdict(int)
    contacts = defaultdict(Counter)
    entities = defaultdict(list)
    blind = 0
    top = 0.0

    for run in range(args.runs):
        seed = Seed.for_run(run)
        ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
        scene = scene_api.build("runner", ctx)
        seen_wrecks = seen_unsolved = seen_contacts = 0
        for _ in range(int(args.seconds / DT)):
            scene.update(DT)
            scene.elapsed += DT
            # Before the wreck is skipped over: ``run_t`` is what it was at
            # the moment of the crash only until ``_restart`` zeroes it, and
            # the hold in between is the part this loop skips.
            if scene.crashes > seen_wrecks:
                seen_wrecks = scene.crashes
                hit = scene.last_contact or {}
                wrecks.append((scene.run_t, hit.get("speed", 0.0),
                               f"{hit.get('kind')}/{hit.get('depth', 0):.2f}"))
            if scene.crash_t >= 0.0:
                continue
            key = band(scene.speed)
            frames[key] += 1
            entities[key].append(len(scene.entities))
            top = max(top, scene.speed)
            if getattr(scene, "blind", False):
                blind += 1
            if scene.unsolvable > seen_unsolved:
                unsolved[key] += scene.unsolvable - seen_unsolved
                seen_unsolved = scene.unsolvable
            if scene.contacts > seen_contacts:
                seen_contacts = scene.contacts
                hit = scene.last_contact or {}
                # Bucketed by the speed *the contact recorded*, not by the
                # speed this frame is being drawn at. They are the same frame
                # almost always and are not on the one that matters: a wreck
                # is held for a couple of seconds and the run that starts
                # afterwards is back at ``BASE_SPEED``, so reading the live
                # speed files a handful of the deepest contacts in the scene
                # under the slowest band there is.
                contacts[band(hit.get("speed", scene.speed))][hit.get("kind")] += 1

    total = sum(frames.values()) * DT
    print(f"\n{args.runs} runs x {args.seconds:.0f}s")
    print(f"top speed reached : {top:.1f} m/s")
    print(f"wrecks            : {len(wrecks)}")
    if wrecks:
        lives = sorted(w[0] for w in wrecks)
        print(f"run life          : min {lives[0]:.0f}  median "
              f"{lives[len(lives) // 2]:.0f}  max {lives[-1]:.0f} s")
        print(f"speed at the wreck: {min(w[1] for w in wrecks):.1f} .. "
              f"{max(w[1] for w in wrecks):.1f} m/s")
    print(f"blind (fog nearer than the commitment): "
          f"{blind * DT / max(total, 1e-9) * 100:.1f}% of the run")
    print(f"\n{'speed':>9} {'sec':>7} {'no-plan/min':>12} {'contacts':>9} "
          f"{'entities':>9}  what was hit")
    for key in sorted(frames, key=lambda k: int(k.split("-")[0])):
        secs = frames[key] * DT
        hit = dict(contacts[key])
        print(f"{key:>9} {secs:>7.0f} "
              f"{unsolved[key] / max(secs, 1e-9) * 60:>12.0f} "
              f"{sum(contacts[key].values()):>9} "
              f"{sum(entities[key]) / len(entities[key]):>9.0f}  "
              f"{hit if hit else ''}")


if __name__ == "__main__":
    main()
