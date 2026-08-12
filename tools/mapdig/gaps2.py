"""A second, route-free read of the gap table, over all 43 legs.

The Dijkstra solve only covers the 26 legs a walk/fall/climb/jump model can
finish.  This one asks a narrower question that needs no route: stand on a
terrace edge -- a standable cell with nothing walkable in front of it in the
direction of travel -- and measure the shortest legal landing forward.  That
is the gap the map puts in front of you at that spot, whether or not the
route happens to use it.
"""
import math
import pickle
from collections import defaultdict

import common as C
import route as R

CAP = 6.0


def main():
    legvol = pickle.load(open(C.R1 + "/legvol.pkl", "rb"))
    alld, allh = [], []
    per = {}
    for idx, a, b, pts in C.legs():
        cells, stand, dist = R.build(idx, a, b, pts, legvol)
        nodes, nid = [], {}
        for (x, z), lst in stand.items():
            for s in lst:
                nid[(x, s, z)] = len(nodes)
                nodes.append((x, s, z))
        grid = defaultdict(list)
        for n, (x, s, z) in enumerate(nodes):
            grid[(x // 8, z // 8)].append(n)
        found = []
        for n, (x, s, z) in enumerate(nodes):
            d0, i = dist(x, z)
            if d0 > 9.0:
                continue
            p = pts[min(i, len(pts) - 2)]
            q = pts[min(i + 1, len(pts) - 1)]
            tx, tz = q[0] - p[0], q[2] - p[2]
            tl = math.hypot(tx, tz) or 1.0
            tx, tz = tx / tl, tz / tl
            # an edge: the cell one step forward has no surface within one
            fx, fz = x + round(tx), z + round(tz)
            if any(abs(s2 - s) <= 1 for s2 in stand.get((fx, fz), ())):
                continue
            if not R.clear_at(cells, fx, s, fz):
                continue          # a wall, not an edge
            best = None
            for kx in range(x // 8 - 1, x // 8 + 2):
                for kz in range(z // 8 - 1, z // 8 + 2):
                    for m in grid.get((kx, kz), ()):
                        x2, s2, z2 = nodes[m]
                        d = math.hypot(x2 - x, z2 - z)
                        if d < 2.0 or d > CAP or s2 - s > 1:
                            continue
                        if (x2 - x) * tx + (z2 - z) * tz <= 0.5 * d:
                            continue
                        if not R.arc_clear(cells, x, s, z, x2, s2, z2):
                            continue
                        if best is None or d < best[0]:
                            best = (d, s2 - s)
            if best:
                found.append(best)
        per[idx] = found
        alld.extend(d for d, _ in found)
        allh.extend(h for _, h in found)
        ds = [d for d, _ in found]
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} edges with a landing "
              f"{len(found):4d}  median {C.pct(ds,0.5) if ds else 0:.2f}  "
              f"max {max(ds) if ds else 0:.2f}")
    print(f"\nall 43 legs, {len(alld)} terrace-edge gaps")
    print(f"  min {min(alld):.2f} median {C.pct(alld,0.5):.2f} mean "
          f"{sum(alld)/len(alld):.2f} p90 {C.pct(alld,0.9):.2f} max "
          f"{max(alld):.2f}")
    by = defaultdict(list)
    for d, h in zip(alld, allh):
        by[h].append(d)
    for h in sorted(by, reverse=True):
        v = by[h]
        print(f"    {h:+d}  n={len(v):5d} ({len(v)/len(alld):5.1%})  min "
              f"{min(v):.2f} median {C.pct(v,0.5):.2f} mean "
              f"{sum(v)/len(v):.2f} p90 {C.pct(v,0.9):.2f} max {max(v):.2f}")
    hist = defaultdict(int)
    for d in alld:
        hist[round(d * 2) / 2] += 1
    print("  histogram:")
    for k in sorted(hist):
        print(f"    {k:4.1f} m  {hist[k]:5d}  "
              f"{'#' * (hist[k] * 60 // max(hist.values()))}")


if __name__ == "__main__":
    main()
