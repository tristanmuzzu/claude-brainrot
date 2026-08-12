"""Render a committed asset to PNG for eyeballing.

    python assets/preview.py character            # rest + each anim mid-pose
    python assets/preview.py train --yaw 30

Two things here are not obvious and both of them produced silently wrong
pictures for the whole life of this script:

* **The window has to be an X11 one.** On a Wayland session GLFW opens a
  Wayland surface, and ``LoadImageFromScreen`` reads nothing back off one --
  every preview came out solid black, roughly one run in four at first and
  then always. ``brainrot.overlay.x11.prepare()`` is the project's own lever
  for this and it has to be pulled before ``InitWindow``.
* **The capture correction is measured, not assumed.** This script used to
  flip vertically and swap red for blue unconditionally, which is right for the
  software rasteriser and wrong for a GPU build: brown assets came back dark
  blue and the grid was above the model. ``engine/rl.save_frame`` already draws
  marker frames at window creation and reads back where they landed, so it
  knows which corrections this backend actually needs. Use it rather than
  guessing -- this is the same landmine ``docs/ARCHITECTURE.md`` records for
  ``brainrot shoot``, still live here because this file had its own copy of the
  capture path.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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
        CAMERA_PERSPECTIVE,
        WHITE,
        BeginDrawing,
        BeginMode3D,
        ClearBackground,
        CloseWindow,
        DrawGrid,
        DrawModel,
        EndDrawing,
        EndMode3D,
        GetModelBoundingBox,
        InitWindow,
        LoadModel,
        LoadModelAnimations,
        SetTraceLogLevel,
        UpdateModelAnimation,
        ffi,
    )

    from brainrot.engine import rl as engine_rl
    from brainrot.overlay import x11

    path = DATA / f"{args.name}.glb"
    if not path.exists():
        print(f"no such asset: {path}")
        return 1
    OUT.mkdir(exist_ok=True)

    SetTraceLogLevel(4)
    x11.prepare()
    InitWindow(args.size, args.size, b"preview")
    engine_rl.calibrate_capture()
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
        # Presented twice on purpose: read-back is one buffer swap behind the
        # draw on this GPU build, so a single frame reads back the *previous*
        # one. Anything that wants to capture a frame has to present it twice.
        engine_rl.save_frame(str(fname))

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
