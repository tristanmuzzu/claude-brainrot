"""Backdrop buildings: three archetypes the scene instances and recolours.

Windows are their own zone so night runs can turn them into lit grids by
writing one bright colour. Walls are the recolourable "wall" zone.

Origin at ground centre; buildings rise along +Z (glTF +Y).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import bake_and_export, box, join, reset, run_script_banner, zone  # noqa: E402


def window_grid(parts, mat, w, d, h, cols, rows, z0=1.2):
    """Inset window boxes on both long faces."""
    margin_x = w * 0.12
    span = w - 2 * margin_x
    for side in (-1, 1):
        for c in range(cols):
            for r in range(rows):
                x = -w / 2 + margin_x + (c + 0.5) * span / cols
                z = z0 + (r + 0.5) * (h - z0 - 0.8) / rows
                parts.append(box(f"win{side}{c}{r}", (span / cols * 0.62, 0.1, (h - z0) / rows * 0.55),
                                 (x, side * (d / 2 + 0.01), z), mat, 0.0))


def tower(idx: int):
    WALL = zone("wall", (0.42, 0.44, 0.50), rough=0.85)
    TRIM = zone("trim", (0.30, 0.31, 0.35), rough=0.8)
    WINDOW = zone("window", (0.35, 0.55, 0.70), rough=0.2)

    parts = []
    if idx == 0:                       # straight slab tower
        w, d, h = 8.0, 7.0, 26.0
        parts.append(box("body", (w, d, h), (0, 0, h / 2), WALL, 0.1))
        parts.append(box("crown", (w * 0.9, d * 0.9, 0.9), (0, 0, h + 0.4), TRIM, 0.05))
        parts.append(box("tank", (2.0, 2.0, 1.8), (w * 0.2, 0, h + 1.7), TRIM, 0.06))
        window_grid(parts, WINDOW, w, d, h, cols=4, rows=7)
    elif idx == 1:                     # stepped set-back tower
        w, d = 9.0, 8.0
        h1, h2, h3 = 12.0, 9.0, 7.0
        parts.append(box("b1", (w, d, h1), (0, 0, h1 / 2), WALL, 0.1))
        parts.append(box("b2", (w * 0.72, d * 0.72, h2), (0, 0, h1 + h2 / 2), WALL, 0.1))
        parts.append(box("b3", (w * 0.48, d * 0.48, h3), (0, 0, h1 + h2 + h3 / 2), WALL, 0.1))
        for lvl, (bw, bd, bz) in enumerate([(w, d, h1), (w * 0.72, d * 0.72, h1 + h2), (w * 0.48, d * 0.48, h1 + h2 + h3)]):
            parts.append(box(f"trim{lvl}", (bw * 0.94, bd * 0.94, 0.5), (0, 0, bz + 0.2), TRIM, 0.04))
        window_grid(parts, WINDOW, w, d, h1, cols=5, rows=3)
        window_grid(parts, WINDOW, w * 0.72, d * 0.72, h1 + h2, cols=4, rows=2, z0=h1 + 0.8)
    else:                              # low wide block with billboard frame
        w, d, h = 12.0, 8.0, 9.0
        parts.append(box("body", (w, d, h), (0, 0, h / 2), WALL, 0.1))
        parts.append(box("crown", (w * 0.96, d * 0.96, 0.6), (0, 0, h + 0.25), TRIM, 0.04))
        parts.append(box("board", (6.0, 0.4, 3.2), (0, 0, h + 2.2), TRIM, 0.05))
        parts.append(box("boardface", (5.6, 0.12, 2.8), (0, -0.22, h + 2.2), WINDOW, 0.02))
        window_grid(parts, WINDOW, w, d, h, cols=6, rows=3)
    return parts


for idx in range(3):
    reset()
    run_script_banner(f"building_{'abc'[idx]}")
    b = join(tower(idx), f"building_{'abc'[idx]}")
    bake_and_export([b], f"building_{'abc'[idx]}", resolution=512)
