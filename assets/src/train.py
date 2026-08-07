"""Subway rolling stock: a cab car and a middle car, exported separately so the
scene can compose trains of any length. The body zone is recoloured per seed;
glass, frame and steel stay fixed.

Scale: metres. Car is 4.9 long, 2.1 wide, sits on rails at y=0 (glTF Y-up).
Built along Blender +X; the scene treats +X as "toward the camera" after the
Y-up export, and yaws it as needed.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, cylinder, join, reset, run_script_banner, zone,
)


def build_car(with_cab: bool):
    BODY = zone("body", (0.06, 0.52, 0.56), rough=0.35)
    CREAM = zone("cream", (0.93, 0.90, 0.82), rough=0.5)
    GLASS = zone("glass", (0.07, 0.09, 0.12), rough=0.1)
    DARK = zone("dark", (0.10, 0.10, 0.12), rough=0.85)
    STRIPE = zone("stripe", (0.96, 0.62, 0.10), rough=0.4)
    STEEL = zone("steel", (0.52, 0.54, 0.58), rough=0.35)
    LAMP = zone("lamp", (1.0, 0.92, 0.55), rough=0.2)

    L, W = 4.9, 2.1
    z0 = 0.62               # hull floor above railhead
    HULL = 2.0

    parts = [
        box("hull_low", (L, W, 0.95), (0, 0, z0 + 0.475), BODY, 0.09),
        box("hull_up", (L, W, 1.05), (0, 0, z0 + 1.475), CREAM, 0.09),
        box("stripe", (L + 0.04, W + 0.04, 0.14), (0, 0, z0 + 0.99), STRIPE, 0.03),
        box("roof", (L * 0.92, W * 0.82, 0.18), (0, 0, z0 + HULL + 0.07), BODY, 0.07),
        box("vent", (L * 0.4, W * 0.4, 0.14), (0, 0, z0 + HULL + 0.2), DARK, 0.04),
        box("frame", (L * 0.98, W * 0.84, 0.30), (0, 0, z0 - 0.15), DARK, 0.04),
    ]
    # side glass bands with mullions
    for side in (-1, 1):
        parts.append(box(f"glass{side}", (L * 0.8, 0.05, 0.6),
                         (0, side * (W / 2 + 0.005), z0 + 1.48), GLASS, 0.02))
        for i in range(3):
            x = -L * 0.8 / 2 + (i + 1) * (L * 0.8 / 4)
            parts.append(box(f"mull{side}{i}", (0.10, 0.07, 0.6),
                             (x, side * (W / 2 + 0.006), z0 + 1.48), CREAM, 0.0))
        # sliding doors
        for dx in (-L * 0.27, L * 0.27):
            parts.append(box(f"door{side}{dx:.0f}", (0.66, 0.05, 1.55),
                             (dx, side * (W / 2 + 0.004), z0 + 0.93), BODY, 0.02))
            parts.append(box(f"doorwin{side}{dx:.0f}", (0.4, 0.06, 0.5),
                             (dx, side * (W / 2 + 0.005), z0 + 1.45), GLASS, 0.01))

    if with_cab:
        parts.append(box("cab", (0.55, W * 0.94, HULL * 0.97),
                         (L / 2 + 0.12, 0, z0 + HULL / 2 - 0.02), BODY, 0.13))
        parts.append(box("windscreen", (0.06, W * 0.6, 0.62),
                         (L / 2 + 0.4, 0, z0 + 1.42), GLASS, 0.02))
        for side in (-1, 1):
            parts.append(box(f"lamp{side}", (0.07, 0.26, 0.2),
                             (L / 2 + 0.4, side * 0.6, z0 + 0.42), LAMP, 0.02))

    # bogies + wheels
    for bx in (-1.55, 1.55):
        parts.append(box(f"bogie{bx:.0f}", (1.15, W * 0.7, 0.3), (bx, 0, 0.32), DARK, 0.04))
        for wx in (-0.4, 0.4):
            for side in (-1, 1):
                parts.append(cylinder(f"wheel{bx:.0f}{wx:.0f}{side}", 0.27, 0.14,
                                      (bx + wx, side * (W * 0.7 / 2), 0.27),
                                      STEEL, rot=(math.radians(90), 0, 0), vertices=12))
    return parts


reset()
run_script_banner("train (cab)")
car = join(build_car(with_cab=True), "train_cab")
bake_and_export([car], "train_cab", resolution=512)

reset()
run_script_banner("train (car)")
car = join(build_car(with_cab=False), "train_car")
bake_and_export([car], "train_car", resolution=512)
