"""Render an animation clip as a filmstrip for frame-by-frame judgement.

    python assets/animstrip.py character run
    python assets/animstrip.py character run --frames 12 --yaw 90
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ["BRAINROT_HEADLESS"] = "1"

DATA = Path(__file__).parent.parent / "src" / "brainrot" / "assets" / "data"
OUT = Path(__file__).parent / "previews"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("clip")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--yaw", type=float, default=90.0, help="35=three-quarter, 90=profile")
    ap.add_argument("--cell", type=int, default=240)
    args = ap.parse_args()

    import math

    from PIL import Image

    from raylib import (
        ffi, BeginDrawing, BeginMode3D, ClearBackground, CloseWindow,
        DrawModel, EndDrawing, EndMode3D, ExportImage, GetModelBoundingBox,
        ImageFlipVertical, InitWindow, LoadImageFromScreen, LoadModel,
        LoadModelAnimations, SetTraceLogLevel, UpdateModelAnimation, WHITE,
        CAMERA_PERSPECTIVE, DrawLine3D,
    )

    path = DATA / f"{args.name}.glb"
    SetTraceLogLevel(4)
    InitWindow(args.cell, args.cell, b"strip")
    model = LoadModel(str(path).encode())
    count = ffi.new("int *")
    anims = LoadModelAnimations(str(path).encode(), count)
    clip = None
    for i in range(count[0]):
        if ffi.string(anims[i].name).decode() == args.clip:
            clip = anims[i]
    if clip is None:
        print(f"no clip {args.clip!r}")
        return 1

    bb = GetModelBoundingBox(model)
    height = max(bb.max.y - bb.min.y, 1.0)
    # Frame the whole figure from the waist's height, looking level: a camera
    # above the subject foreshortens exactly the vertical extent these strips
    # exist to judge. Keep the eye on the mid-line and the ground stays where
    # the eye expects it.
    cy = height * 0.5
    dist = height * 2.3
    yaw = math.radians(args.yaw)
    cam = ffi.new("Camera3D *")
    cam.position = (dist * math.cos(yaw), cy, dist * math.sin(yaw))
    cam.target = (0.0, cy, 0.0)
    cam.up = (0.0, 1.0, 0.0)
    cam.fovy = 40.0
    cam.projection = CAMERA_PERSPECTIVE

    cells = []
    for i in range(args.frames):
        frame = int(i / args.frames * (clip.keyframeCount - 1))
        UpdateModelAnimation(model, clip, frame)
        for _ in range(2):
            BeginDrawing()
            ClearBackground((238, 241, 246, 255))
            BeginMode3D(cam[0])
            DrawModel(model, (0, 0, 0), 1.0, WHITE)
            # Ground plus half-metre rules: the strip is for judging how high
            # a jump gets and how low a duck reaches, so give it a ruler.
            for k in range(0, 7):
                h = k * 0.5
                shade = (60, 60, 70, 255) if k == 0 else (
                    (170, 176, 190, 255) if k % 2 else (205, 210, 220, 255))
                DrawLine3D((-2, h, -1.2), (2, h, -1.2), shade)
            DrawLine3D((0, 0, -1.2), (0, 0, 1.2), (150, 150, 160, 255))
            EndMode3D()
            EndDrawing()
        img = LoadImageFromScreen()
        ImageFlipVertical(ffi.addressof(img))
        tmp = OUT / f"_cell{i}.png"
        OUT.mkdir(exist_ok=True)
        ExportImage(img, str(tmp).encode())
        im = Image.open(tmp).convert("RGBA")
        r, g, b, a = im.split()
        cells.append(Image.merge("RGBA", (b, g, r, a)))
        tmp.unlink()
    CloseWindow()

    strip = Image.new("RGBA", (args.cell * len(cells), args.cell))
    for i, cell in enumerate(cells):
        strip.paste(cell, (i * args.cell, 0))
    out = OUT / f"{args.name}-{args.clip}-strip.png"
    strip.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
