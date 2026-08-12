"""Load the real tower into memory and measure what the real levels are like.

Two questions, both aimed at our own generator:

1. Can you *walk* from checkpoint to checkpoint on the real map -- the exact
   straight-line-running complaint the owner has about ours?
2. What is under the course: how much of each leg is over solid ground vs
   over a drop, and what blocks make up the course band?

Loads y 40..245 within |x|,|z| <= 80 via section streaming (fast), then runs
a no-jump walker (step +1, drop <= 3, needs 2 air above) between consecutive
plates.
"""
import glob
import json
import math
import os
from collections import Counter

import anvil

S = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
     "ae099ecc-79f8-4994-8bb6-bf154d746d6b/scratchpad")
base = S + "/psmap/Parkour Spiral/dimensions/minecraft/overworld/region"

AIRLIKE = {"air", "cave_air", "void_air", "light", "structure_void", "water"}
# Things a body passes through or barely notices for walking purposes.
SOFT = AIRLIKE | {"short_grass", "tall_grass", "fern", "large_fern", "vine",
                  "poppy", "dandelion", "azure_bluet", "cornflower", "allium",
                  "oxeye_daisy", "lily_of_the_valley", "torch", "wall_torch",
                  "rail", "snow", "dead_bush", "sugar_cane", "cave_vines",
                  "cave_vines_plant", "glow_lichen", "moss_carpet"}

world = {}
R = 80
for path in sorted(glob.glob(base + "/*.mca")):
    name = os.path.basename(path)[2:-4]
    rx, rz = (int(v) for v in name.split("."))
    if not (-4 <= rx <= 3 and -4 <= rz <= 3):
        continue
    wx0, wz0 = rx * 512, rz * 512
    if wx0 > R or wx0 + 512 < -R or wz0 > R or wz0 + 512 < -R:
        continue
    try:
        region = anvil.Region.from_file(path)
    except Exception:
        continue
    for cx in range(32):
        for cz in range(32):
            bx, bz = rx * 512 + cx * 16, rz * 512 + cz * 16
            if bx > R or bx + 16 < -R or bz > R or bz + 16 < -R:
                continue
            try:
                chunk = anvil.Chunk.from_region(region, cx, cz)
            except Exception:
                continue
            try:
                sections = chunk.data.get("sections", [])
            except Exception:
                continue
            for sec in sections:
                sy = int(str(sec.get("Y")))
                if not (2 <= sy <= 15):
                    continue
                bs = sec.get("block_states")
                if bs is None:
                    continue
                palette = [str(e.get("Name", "")).replace("minecraft:", "")
                           for e in bs.get("palette", [])]
                if all(p in AIRLIKE for p in palette):
                    continue
                sec_obj = chunk.get_section(sy)
                for y in range(16):
                    wy = sy * 16 + y
                    for z in range(16):
                        for x in range(16):
                            try:
                                b = chunk.get_block(x, wy, z)
                            except Exception:
                                continue
                            if b.id not in AIRLIKE:
                                world[(bx + x, wy, bz + z)] = b.id

print(f"{len(world)} solid-ish cells loaded")

def solid(c):
    return world.get(c) is not None and world.get(c) not in SOFT

def open_cell(c):
    return world.get(c) is None or world.get(c) in SOFT

plates = [tuple(p) for p in json.load(open(S + "/plates.json"))]
plates.sort(key=lambda p: p[1])

def walkable(a, b, limit=60000):
    """No-jump walker from plate a toward plate b."""
    start = (a[0], a[1], a[2])
    seen = {start}
    edge = [start]
    best = math.hypot(a[0] - b[0], a[2] - b[2]) + abs(a[1] - b[1])
    while edge and len(seen) < limit:
        x, y, z = edge.pop()
        d = math.hypot(x - b[0], z - b[2]) + abs(y - b[1])
        if d < best:
            best = d
        if d <= 2.0:
            return True, 0.0
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            for ny in range(y + 1, y - 4, -1):
                if not solid((nx, ny - 1, nz)):
                    continue
                if open_cell((nx, ny, nz)) and open_cell((nx, ny + 1, nz)):
                    cell = (nx, ny, nz)
                    if cell not in seen:
                        seen.add(cell)
                        edge.append(cell)
                break
    return False, best

start_d = [math.hypot(a[0] - b[0], a[2] - b[2]) + abs(a[1] - b[1])
           for a, b in zip(plates, plates[1:])]
reached = 0
closes = []
for (a, b), d0 in zip(zip(plates, plates[1:]), start_d):
    ok, best = walkable(a, b)
    reached += ok
    closes.append(1.0 - (best / max(1e-9, d0)) if not ok else 1.0)
    print(f"y {a[1]:3d} -> {b[1]:3d}  d0 {d0:5.1f}  "
          f"{'WALKED THROUGH' if ok else f'stopped, covered {closes[-1]:.0%}'}")
print(f"\n{reached}/{len(plates)-1} real legs walkable end to end")
print(f"mean fraction coverable without a jump: "
      f"{sum(closes)/len(closes):.0%}")
json.dump({str(k): v for k, v in world.items()},
          open(S + "/realworld.json", "w"))
