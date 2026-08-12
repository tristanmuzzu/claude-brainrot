"""Cut the loaded tower into 43 per-leg volumes and cache them.

A leg's volume is every non-air cell within HORIZ metres (in plan) of that
leg's spine and inside the leg's height band, widened upward so a landmark
standing on the terrace is inside its own leg.

Output: r1/legvol.pkl -> {leg_index: {(x, y, z): name}} plus the spines.
"""
import math
import pickle
import time

import common as C

HORIZ = 16.0
Y_BELOW, Y_ABOVE = 8, 24
BUCKET = 8


def main():
    world = C.load_world()
    print(f"{len(world)} cells")
    grid = {}
    for (x, y, z), n in world.items():
        grid.setdefault((x // BUCKET, y // BUCKET, z // BUCKET),
                        []).append((x, y, z, n))
    print(f"{len(grid)} buckets")

    out = {}
    t0 = time.time()
    for idx, a, b, pts in C.legs():
        ylo = min(a[1], b[1]) - Y_BELOW
        yhi = max(a[1], b[1]) + Y_ABOVE
        keys = set()
        rb = int(HORIZ // BUCKET) + 1
        for p in pts:
            bx, bz = int(p[0]) // BUCKET, int(p[2]) // BUCKET
            for kx in range(bx - rb, bx + rb + 1):
                for kz in range(bz - rb, bz + rb + 1):
                    for ky in range(ylo // BUCKET, yhi // BUCKET + 1):
                        keys.add((kx, ky, kz))
        cells = {}
        h2 = HORIZ * HORIZ
        for k in keys:
            for x, y, z, n in grid.get(k, ()):
                if not (ylo <= y <= yhi):
                    continue
                for p in pts:
                    if (p[0] - x) ** 2 + (p[2] - z) ** 2 <= h2:
                        cells[(x, y, z)] = n
                        break
        out[idx] = cells
        print(f"leg {idx:2d}  y {a[1]}->{b[1]}  {len(cells)} cells  "
              f"{time.time() - t0:.0f}s")
    with open(C.R1 + "/legvol.pkl", "wb") as f:
        pickle.dump(out, f, protocol=5)
    print("total", sum(len(v) for v in out.values()), f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
