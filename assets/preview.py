"""Render a committed asset to PNG for eyeballing, using the same software
rasteriser CI uses.

    python assets/preview.py character            # rest + each anim mid-pose
    python assets/preview.py train --yaw 30
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

DATA = Path(__file__).parent.parent / "src" / "brainrot" / "assets" / "data"
OUT = Path(__file__).parent / "previews"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--yaw", type=float, default=35.0)
    ap.add_argument("--pitch", type=float, default=18.0)
    ap.add_argument("--size", type=int, default=520)
    args = ap.parse_args()

    import math

    from raylib import (
        ffi, BeginDrawing, BeginMode3D, ClearBackground, CloseWindow,
        DrawGrid, DrawModel, EndDrawing, EndMode3D, GetModelBoundingBox,
        InitWindow, LoadModel, LoadModelAnimations, SetTraceLogLevel,
        UpdateModelAnimation, WHITE, CAMERA_PERSPECTIVE,
    )
    from PIL import Image

    from raylib import LoadImageFromScreen, ImageFlipVertical, ExportImage

    path = DATA / f"{args.name}.glb"
    if not path.exists():
        print(f"no such asset: {path}")
        return 1
    OUT.mkdir(exist_ok=True)

    SetTraceLogLevel(4)
    InitWindow(args.size, args.size, b"preview")
    model = LoadModel(str(path).encode())
    count = ffi.new("int *")
    anims = LoadModelAnimations(str(path).encode(), count)

    bb = GetModelBoundingBox(model)
    cx = (bb.min.x + bb.max.x) / 2
    cy = (bb.min.y + bb.max.y) / 2
    cz = (bb.min.z + bb.max.z) / 2
    radius = max(bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)
    dist = max(radius * 1.7, 1.0)

    yaw = math.radians(args.yaw)
    pitch = math.radians(args.pitch)
    cam = ffi.new("Camera3D *")
    cam.position = (cx + dist * math.cos(pitch) * math.cos(yaw),
                    cy + dist * math.sin(pitch),
                    cz + dist * math.cos(pitch) * math.sin(yaw))
    cam.target = (cx, cy, cz)
    cam.up = (0.0, 1.0, 0.0)
    cam.fovy = 42.0
    cam.projection = CAMERA_PERSPECTIVE

    def shot(fname: Path) -> None:
        for _ in range(2):
            BeginDrawing()
            ClearBackground((236, 240, 245, 255))
            BeginMode3D(cam[0])
            DrawModel(model, (0, 0, 0), 1.0, WHITE)
            DrawGrid(8, max(0.25, radius / 6))
            EndMode3D()
            EndDrawing()
        img = LoadImageFromScreen()
        ImageFlipVertical(ffi.addressof(img))
        tmp = str(fname.with_suffix(".raw.png")).encode()
        ExportImage(img, tmp)
        im = Image.open(fname.with_suffix(".raw.png")).convert("RGBA")
        r, g, b, a = im.split()
        Image.merge("RGBA", (b, g, r, a)).save(fname)
        fname.with_suffix(".raw.png").unlink()

    shot(OUT / f"{args.name}-rest.png")
    saved = [OUT / f"{args.name}-rest.png"]
    for i in range(count[0]):
        a = anims[i]
        name = ffi.string(a.name).decode()
        UpdateModelAnimation(model, a, max(1, a.keyframeCount // 3))
        target = OUT / f"{args.name}-{name}.png"
        shot(target)
        saved.append(target)
    CloseWindow()
    for p in saved:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
