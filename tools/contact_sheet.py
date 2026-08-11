"""Tile a directory of shoot frames into one contact sheet.

    python tools/contact_sheet.py shots/ sheet.png [columns]

Art direction on this scene is done by looking at whole runs rather than at
single frames -- one frame can be flattering by accident, and what actually
needs judging is whether the course stays in shot from hop to hop.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

def main() -> None:
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    files = sorted(p for p in src.rglob("*.png"))
    if not files:
        raise SystemExit(f"no frames under {src}")
    thumbs = [Image.open(p).convert("RGB") for p in files]
    tw = 168
    th = int(thumbs[0].height * tw / thumbs[0].width)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (18, 18, 20))
    for i, im in enumerate(thumbs):
        sheet.paste(im.resize((tw, th), Image.LANCZOS),
                    ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    print(f"{len(thumbs)} frames -> {out}")

if __name__ == "__main__":
    main()
