"""Render one designed tower level, by name or number, without waiting for it.

The visual pass over the hand-built tower is per level -- render, look, adjust,
repeat -- and a run only opens where its seed says. This pins the cone's phase
so the run opens on the level asked for, and changes nothing else: same scene,
same camera, same physics.

    python tools/level_shot.py --level "MARKET STREET" --frames 450 --every 15
    python tools/level_shot.py --level 3 --seed 5 --sheet
    python tools/level_shot.py --list

``--sheet`` tiles the frames into one contact sheet next to the frames.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

os.environ.setdefault("BRAINROT_HEADLESS", "1")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level", default="1",
                    help="level number (1-based) or name substring")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--frames", type=int, default=450)
    ap.add_argument("--every", type=int, default=15)
    ap.add_argument("--out", default=None)
    ap.add_argument("--sheet", action="store_true",
                    help="also tile the frames into one contact sheet")
    ap.add_argument("--list", action="store_true", help="print the roster")
    args = ap.parse_args()

    from brainrot.scenes import handplan as hp

    if args.list:
        for i, lv in enumerate(hp.LEVELS, 1):
            print(f"{i:2d}  {lv.name:16s} {lv.theme:10s} rise={lv.rise} "
                  f"exit={lv.exit}")
        return 0

    names = [lv.name for lv in hp.LEVELS]
    try:
        index = int(args.level) - 1
        if not 0 <= index < len(names):
            raise ValueError
    except ValueError:
        want = str(args.level).upper()
        hits = [i for i, n in enumerate(names) if want in n.upper()]
        if len(hits) != 1:
            print(f"level {args.level!r} matches {len(hits)} of: {names}")
            return 2
        index = hits[0]
    name = names[index]

    # The run opens on section START_LEVEL, whose design is
    # LEVELS[(START_LEVEL + phase) % n] -- so pin the phase that puts the
    # wanted level there. Set before super().__init__ lays the first section.
    from brainrot.scenes import spiralplan as sp
    pin = (index - sp.START_LEVEL) % len(names)
    base_init = sp.Cone.__init__

    def pinned(self, rng, base_y=0):
        base_init(self, rng, base_y)
        self.phase = pin
    # Patch the *base* class, not handplan's. handplan's own __init__ draws
    # the phase from the rng before delegating; replacing it would skip that
    # draw and shift every roll after it -- a different world from the one a
    # normal run of the same seed builds, which is exactly what a probe
    # harness must never do. This way the draw still happens and the pin
    # simply overwrites the result.
    sp.Cone.__init__ = pinned  # type: ignore[method-assign]
    # ``phase`` is read in _extend_section during construction, so it must be
    # in place before the first section exists: hand Cone a pre-set attribute
    # via the class, then let instances override it harmlessly.
    hp.Cone.phase = pin  # type: ignore[attr-defined]

    from brainrot.config import Config
    from brainrot.engine import rl
    from brainrot.engine import scene as scene_api
    from brainrot.engine.window import HeadlessWindow
    from brainrot.palette import generate as generate_palette
    from brainrot.rng import Seed

    cfg = Config()
    window = HeadlessWindow()
    window.create(cfg)
    seed = Seed.for_run(args.seed)
    palette = generate_palette(seed)
    ctx = scene_api.SceneContext(cfg.width, cfg.height, palette, seed,
                                 cfg.quality)
    scene = scene_api.build("tower", ctx)

    slug = name.lower().replace(" ", "_")
    out = Path(args.out or f"shots/level_{index + 1:02d}_{slug}")
    out.mkdir(parents=True, exist_ok=True)

    dt = 1.0 / cfg.fps
    window.begin(); scene.draw(); window.end()
    saved = []
    for frame in range(args.frames):
        scene.update(dt)
        scene.elapsed += dt
        window.begin(); scene.draw(); window.end()
        if frame % max(1, args.every) == 0:
            window.present(scene.draw)
            path = out / f"{slug}-{frame:04d}.png"
            rl.save_frame(str(path))
            saved.append(path)
    window.destroy()
    print(f"level {index + 1} {name}: {len(saved)} frames in {out}")

    if args.sheet and saved:
        import subprocess
        sheet = out.with_suffix(".png")
        subprocess.run([sys.executable,
                        str(Path(__file__).parent / "contact_sheet.py"),
                        str(out), str(sheet)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
