"""One tileable segment of three-lane subway track.

SEG_LEN long, spanning all three lanes; the scene chains copies end to end.
Everything that must tile across the joint -- ballast, rails -- runs the full
length with no end bevel, and sleepers are spaced so the rhythm continues
seamlessly from one segment to the next.

Lane centres sit at x = -LANE_SPACING, 0, +LANE_SPACING (glTF X), so the
runtime's lane constants must match LANE_SPACING here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import bake_and_export, box, join, reset, run_script_banner, zone  # noqa: E402

SEG_LEN = 6.0
LANE_SPACING = 2.4
GAUGE = 1.5          # rail-to-rail per lane

reset()
run_script_banner("track")

BALLAST = zone("ballast", (0.35, 0.33, 0.34), rough=0.95)
EDGE = zone("edge", (0.45, 0.44, 0.46), rough=0.9)
RAIL = zone("rail", (0.60, 0.62, 0.66), rough=0.3)
SLEEPER = zone("sleeper", (0.16, 0.13, 0.11), rough=0.9)

full_w = LANE_SPACING * 2 + GAUGE + 1.6

parts = [
    # ballast bed: a low, full-width slab; no bevel along the tiling axis
    box("bed", (full_w, SEG_LEN, 0.22), (0, 0, 0.11), BALLAST, 0.0),
    # raised concrete edges walling the corridor
    box("edge_l", (0.55, SEG_LEN, 0.5), (-full_w / 2 + 0.27, 0, 0.25), EDGE, 0.0),
    box("edge_r", (0.55, SEG_LEN, 0.5), (+full_w / 2 - 0.27, 0, 0.25), EDGE, 0.0),
]

for lane in (-1, 0, 1):
    cx = lane * LANE_SPACING
    for side in (-1, 1):
        parts.append(box(f"rail{lane}{side}", (0.09, SEG_LEN, 0.12),
                         (cx + side * GAUGE / 2, 0, 0.28), RAIL, 0.0))
    n_sleepers = 8
    for i in range(n_sleepers):
        y = -SEG_LEN / 2 + (i + 0.5) * SEG_LEN / n_sleepers
        parts.append(box(f"sleeper{lane}{i}", (GAUGE + 0.5, 0.24, 0.07),
                         (cx, y, 0.235), SLEEPER, 0.0))

seg = join(parts, "track")
bake_and_export([seg], "track", resolution=512)
