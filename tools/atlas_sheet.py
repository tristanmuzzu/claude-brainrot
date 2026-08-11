"""Render every block pattern as a contact sheet, at texel scale and at
block scale, so a texture can be judged by looking at it.

    python tools/atlas_sheet.py out.png

The left column is the raw 16x16 top tile blown up 8x (what a texel actually
is); the right is a 4x4 tiling of the same tile at 32 px a block, which is
roughly how large a block reads on the strip at arm's length. A pattern that
looks fine at 8x and turns into a grid of stamps at 32 px is the failure mode
this sheet exists to catch.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image, ImageDraw  # noqa: E402

from brainrot.engine import voxel  # noqa: E402

SAMPLES = [
    ("noise", (150, 106, 60)),
    ("planks", (150, 106, 60)),
    ("bricks", (170, 88, 70)),
    ("stonebrick", (140, 140, 146)),
    ("cobble", (132, 132, 140)),
    ("wool", (208, 90, 178)),
    ("concrete", (60, 150, 214)),
    ("grain", (228, 226, 218)),
    ("speck", (132, 132, 140)),
    ("lantern", (255, 212, 128)),
    ("leaves", (72, 148, 62)),
    ("sand", (222, 208, 150)),
    ("dirt", (124, 92, 62)),
    ("checker", (208, 90, 178)),
]


def tile(kind: str, colour, face: str = "top", seed: int = 5) -> Image.Image:
    im = Image.new("RGB", (16, 16))
    px = im.load()
    for y in range(16):
        for x in range(16):
            f = voxel._pattern_factor(kind, face, x, y, seed)
            px[x, y] = tuple(max(0, min(255, int(c * f))) for c in colour)
    return im


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "atlas.png")
    row_h = 132
    im = Image.new("RGB", (860, row_h * len(SAMPLES)), (28, 30, 34))
    d = ImageDraw.Draw(im)
    for i, (kind, colour) in enumerate(SAMPLES):
        y0 = i * row_h + 2
        t = tile(kind, colour)
        im.paste(t.resize((128, 128), Image.NEAREST), (170, y0))
        # four by four at block scale, plus one at half that again
        for scale, x0 in ((32, 320), (16, 470), (48, 560)):
            sheet = Image.new("RGB", (16 * 4, 16 * 4))
            for a in range(4):
                for b in range(4):
                    sheet.paste(t, (a * 16, b * 16))
            n = scale * 4
            im.paste(sheet.resize((n, n), Image.NEAREST), (x0, y0))
        d.text((12, y0 + 56), kind, fill=(230, 230, 235))
    im.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
