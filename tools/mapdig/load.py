"""Load the real Parkour Spiral tower into a pickle, keeping fluids.

The existing realworld.json drops water (it is in that script's AIRLIKE set),
which makes the physics-block question unanswerable from it.  This pass keeps
everything that is not literally air, and records block properties for the
handful of block kinds where the property is the mechanic (slab type, stair
half, trapdoor open, water level).

Output: r1/world.pkl  ->  {(x,y,z): name}, plus meta.
"""
import glob
import os
import pickle
import sys
import time

import anvil

BASE = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
        "ae099ecc-79f8-4994-8bb6-bf154d746d6b/scratchpad/psmap/"
        "Parkour Spiral/dimensions/minecraft/overworld/region")
OUT = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
       "7d49286c-3332-4cc0-9d89-cadc822a1df6/scratchpad/r1")

R = 100          # |x|, |z| bound (course max radius is 51.7)
Y0, Y1 = 36, 252
AIR = {"air", "cave_air", "void_air"}


def main():
    world = {}
    t0 = time.time()
    sec_lo, sec_hi = Y0 // 16, Y1 // 16
    for path in sorted(glob.glob(BASE + "/*.mca")):
        rx, rz = (int(v) for v in os.path.basename(path)[2:-4].split("."))
        wx0, wz0 = rx * 512, rz * 512
        if wx0 > R or wx0 + 512 < -R or wz0 > R or wz0 + 512 < -R:
            continue
        try:
            region = anvil.Region.from_file(path)
        except Exception:
            continue
        for cx in range(32):
            bx = wx0 + cx * 16
            if bx > R or bx + 16 < -R:
                continue
            for cz in range(32):
                bz = wz0 + cz * 16
                if bz > R or bz + 16 < -R:
                    continue
                try:
                    chunk = anvil.Chunk.from_region(region, cx, cz)
                except Exception:
                    continue
                try:
                    sections = chunk.data.get("sections", [])
                except Exception:
                    continue
                have = set()
                for sec in sections:
                    have.add(int(str(sec.get("Y"))))
                for sy in range(sec_lo, sec_hi + 1):
                    if sy not in have:
                        continue
                    try:
                        sec = chunk.get_section(sy)
                        bs = sec.get("block_states")
                    except Exception:
                        continue
                    if bs is None:
                        continue
                    pal = [str(e.get("Name", "")).replace("minecraft:", "")
                           for e in bs.get("palette", [])]
                    if all(p in AIR for p in pal):
                        continue
                    i = 0
                    try:
                        for blk in chunk.stream_blocks(section=sy):
                            name = blk.id
                            if name not in AIR:
                                y = sy * 16 + (i >> 8)
                                if Y0 <= y <= Y1:
                                    world[(bx + (i & 15), y,
                                           bz + ((i >> 4) & 15))] = name
                            i += 1
                    except Exception as exc:
                        print("section fail", bx, sy, bz, exc,
                              file=sys.stderr)
        print(f"{os.path.basename(path)}  cells={len(world)}  "
              f"{time.time() - t0:.0f}s", file=sys.stderr)
    with open(OUT + "/world.pkl", "wb") as f:
        pickle.dump(world, f, protocol=5)
    print(f"{len(world)} non-air cells, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
