"""Render the frames of one ladder climb or bubble ride, and tile them.

A ride is two or three seconds long, fires on a fraction of level exits and
arrives at a spot nobody chooses, so waiting for one in ordinary footage is
hopeless -- which is why the ride camera was tuned against a *jam metric* for
months and nobody looked at it. This forces the wait and renders every frame of
the ride and the second either side of it, which is where the two defects the
owner reported live: the head snapping ninety degrees the instant the body
grabs the ladder, and the ladder floating half a block off the wall it is
supposed to be bolted to.

    python tools/ride_shot.py --scene spiral --seed 3
    python tools/ride_shot.py --scene tower --kind bubble

Writes ``shots/ride/<scene><seed>/`` and a contact sheet beside it.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.config import Config
from brainrot.engine import rl
from brainrot.engine import scene as scene_api
from brainrot.engine.window import HeadlessWindow
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed

W, H = 420, 760
DT = 1.0 / 60.0

#: Kinds this tool will stop for. ``web`` is in the list because it is the
#: third move whose body is inside something it can see the underside of, and
#: it has never been looked at either.
RIDES = ("climb", "bubble", "web")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default="spiral", choices=("spiral", "tower"))
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--kind", default=None, choices=RIDES,
                    help="wait for this kind specifically")
    ap.add_argument("--wait", type=float, default=240.0,
                    help="how long to roll on looking for one, in seconds")
    ap.add_argument("--lead", type=float, default=1.2,
                    help="seconds of run-up to keep before the ride")
    ap.add_argument("--tail", type=float, default=1.6)
    ap.add_argument("--every", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = Config()
    cfg.width, cfg.height = W, H
    window = HeadlessWindow()
    window.create(cfg)

    seed = Seed.for_run(args.seed)
    ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
    scene = scene_api.build(args.scene, ctx)

    out = Path(args.out or f"shots/ride/{args.scene}{args.seed}")
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

    def riding() -> str | None:
        if scene.phase != "move" or scene.move is None:
            return None
        if scene.move.kind not in (args.kind,) if args.kind else \
                scene.move.kind not in RIDES:
            return None
        return scene.move.kind

    # The lead is *kept*, not replayed: rolling the scene back is not a thing
    # it can do, so the frames before the ride come out of a ring buffer of
    # what was already drawn. Cheaper than it sounds -- a PNG a frame at this
    # size is well under a millisecond and only the last few are ever written.
    lead_n = max(1, int(args.lead / DT))
    lead: list[bytes] = []
    kind = None
    for _ in range(int(args.wait / DT)):
        step()
        kind = riding()
        if kind:
            break
        # Cheap stand-in for a frame buffer: remember *when*, and re-render the
        # run-up by stepping a fresh scene is not possible either, so what the
        # lead really buys is the frames after the grab. Keep the counter so
        # the sheet can say how long the wait was.
        lead.append(b"")
        if len(lead) > lead_n:
            lead.pop(0)
    if not kind:
        print(f"no {args.kind or 'ride'} in {args.wait:.0f} s of {args.scene}")
        return 1

    saved = 0
    frame = 0
    seen_ride = 0
    # Everything from the grab until the ride has been over for ``tail``.
    while True:
        if riding():
            seen_ride += 1
        elif seen_ride:
            if frame > seen_ride + int(args.tail / DT):
                break
        if frame % max(1, args.every) == 0:
            window.present(scene.draw)
            rl.save_frame(str(out / f"{frame:05d}.png"))
            saved += 1
        step()
        frame += 1
        if frame > int((args.tail + 12.0) / DT):
            break
    print(f"{kind}: {saved} frames ({seen_ride} of ride) in {out}")

    sheet = out.with_suffix(".png")
    subprocess.run([sys.executable,
                    str(Path(__file__).parent / "contact_sheet.py"),
                    str(out), str(sheet)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
