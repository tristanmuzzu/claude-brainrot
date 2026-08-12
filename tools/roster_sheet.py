"""One frame per level, tiled — the variety check, in one picture.

A per-level contact sheet answers "is this level any good". It cannot answer
the question that has sunk three passes of this tower: **do the levels look
like different places?** Twenty per-level sheets read one after another do not
answer it either, because nothing is side by side.

This tiles one frame from each level into a single image. The first time it was
run it said the whole thing in one glance: a grey cliff down the left edge, one
or two coloured cubes, two thirds sky, twenty times over, with half the levels
unidentifiable from a still.

    python tools/roster_sheet.py --levels 1-20 --out sheet.png

Frames come from whatever ``tools/level_review.py`` last rendered, so render
first; ``--render`` does it for you, one process per level.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from brainrot.scenes.handlevels import LEVELS  # noqa: E402


def want(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [i for i in out if 1 <= i <= len(LEVELS)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--levels", default=f"1-{len(LEVELS)}")
    ap.add_argument("--out", default="shots/review/roster.png")
    ap.add_argument("--at", type=int, default=12,
                    help="which saved frame of each level to take")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--render", action="store_true",
                    help="render the levels first, five at a time")
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    levels = want(args.levels)

    if args.render:
        procs: list[subprocess.Popen] = []
        for n in levels:
            procs.append(subprocess.Popen(
                [sys.executable, str(ROOT / "tools/level_review.py"),
                 "--level", str(n), "--sheet", "--seed", str(args.seed)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=ROOT))
            while sum(p.poll() is None for p in procs) >= 5:
                procs[0].wait()
                procs.pop(0)
        for p in procs:
            p.wait()

    from PIL import Image, ImageDraw

    tiles = []
    for n in levels:
        d = next(iter((ROOT / "shots/review").glob(f"l{n:02d}_*")), None)
        shots = sorted((d / "frames").glob("*.png")) if d else []
        if not shots:
            print(f"level {n}: no frames -- render it first")
            continue
        im = Image.open(shots[min(args.at, len(shots) - 1)]).convert("RGB")
        im = im.resize((300, int(300 * im.height / im.width)))
        lab = Image.new("RGB", (im.width, im.height + 18), (12, 12, 14))
        lab.paste(im, (0, 18))
        ImageDraw.Draw(lab).text((4, 4), f"{n} {LEVELS[n - 1].name}",
                                 fill=(240, 220, 120))
        tiles.append(lab)
    if not tiles:
        return 1
    w, h = tiles[0].size
    rows = (len(tiles) + args.cols - 1) // args.cols
    sheet = Image.new("RGB", (args.cols * (w + 4), rows * (h + 4)), (12, 12, 14))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % args.cols) * (w + 4), (i // args.cols) * (h + 4)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"{len(tiles)} levels -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
