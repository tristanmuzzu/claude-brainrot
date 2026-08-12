"""Solve each leg the way a player does, and read the real gap table off it.

A first attempt measured "nearest island to nearest island" and produced
nonsense: 60% of its gaps were 2.00 m drops of three to seven blocks, which
are not jumps at all -- they are the edge of a terrace with ground somewhere
below.  A gap is only a gap if walking and falling cannot get you there.

So: build the move graph over standable surfaces --

  walk  8-neighbour column, |dy| <= 1          cost EPS
  fall  8-neighbour column, any drop, clear    cost EPS
  jump  2.0 <= d <= CAP, dy <= +1, arc clear   cost 1 + (d / 4) ** 4

-- and Dijkstra from the checkpoint plate that opens the leg to the one that
closes it.  Cheap moves are free, so the route uses a jump only where the
ground genuinely runs out, and the cost curve makes it prefer the short jump
when several would do.  The jumps on that route are the real gap table.

Also reports, as a cross-check on the whole method, how far a walk-and-fall
flood gets without any jump at all.
"""
import heapq
import json
import math
import pickle
import sys
from collections import defaultdict

import common as C

CORR = float(__import__("os").environ.get("CORR", 16.0))
YWIN = float(__import__("os").environ.get("YWIN", 18))
# Vanilla sprint-jump clears a four-block gap: five metres block-centre to
# block-centre, level.  A one-block drop buys about half a metre more; a
# take-off from ice buys a lot more; a slime block buys height.
CAP = float(__import__("os").environ.get("CAP", 5.5))
CAP_ICE = 7.5
MAXFALL = 30
EPS = 1e-4

CLIMB = {"ladder", "vine", "cave_vines", "cave_vines_plant", "scaffolding",
         "twisting_vines", "twisting_vines_plant", "weeping_vines",
         "weeping_vines_plant", "water", "bubble_column", "kelp",
         "kelp_plant"}
ICE = {"ice", "packed_ice", "blue_ice", "frosted_ice"}


def build(idx, a, b, pts, legvol):
    cells = legvol[idx]
    cache = {}

    def dist(x, z):
        k = (x, z)
        v = cache.get(k)
        if v is None:
            best, bi = 1e18, 0
            cx, cz = x + .5, z + .5
            for i, p in enumerate(pts):
                d = (p[0] - cx) ** 2 + (p[2] - cz) ** 2
                if d < best:
                    best, bi = d, i
            v = (math.sqrt(best), bi)
            cache[k] = v
        return v

    stand = {}
    for (x, y, z), name in cells.items():
        if not C.solid_name(name):
            continue
        if C.solid_name(cells.get((x, y + 1, z))):
            continue
        if C.solid_name(cells.get((x, y + 2, z))):
            continue
        d, i = dist(x, z)
        if d > CORR or abs((y + 1) - pts[i][1]) > YWIN:
            continue
        stand.setdefault((x, z), []).append(y + 1)
    for k in stand:
        stand[k].sort()
    return cells, stand, dist


def clear_at(cells, x, y, z):
    return not (C.solid_name(cells.get((x, y, z))) or
                C.solid_name(cells.get((x, y + 1, z))))


def arc_clear(cells, x, s, z, x2, s2, z2):
    """Sample a jump arc: rise 1.25 at the apex, then fall to the landing."""
    d = math.hypot(x2 - x, z2 - z)
    n = max(4, int(d * 3))
    for k in range(1, n):
        u = k / n
        px = x + (x2 - x) * u
        pz = z + (z2 - z) * u
        # parabola through (0, s), apex s+1.25, ending at (1, s2)
        py = s + (s2 - s) * u + 1.25 * 4 * u * (1 - u)
        cy = int(math.floor(py))
        for cx in (int(math.floor(px)), int(math.floor(px + .5))):
            for cz in (int(math.floor(pz)), int(math.floor(pz + .5))):
                if not clear_at(cells, cx, cy, cz):
                    return False
    return True


def solve(idx, a, b, pts, legvol):
    cells, stand, dist = build(idx, a, b, pts, legvol)
    nodes = []
    nid = {}
    for (x, z), lst in stand.items():
        for s in lst:
            nid[(x, s, z)] = len(nodes)
            nodes.append((x, s, z))
    if not nodes:
        return None

    def nearest(p):
        best, bn = 1e18, None
        for n, (x, s, z) in enumerate(nodes):
            d = (x + .5 - p[0]) ** 2 + (s - p[1]) ** 2 + (z + .5 - p[2]) ** 2
            if d < best:
                best, bn = d, n
        return bn, math.sqrt(best)

    src, dsrc = nearest((a[0] + .5, a[1], a[2] + .5))
    dst, ddst = nearest((b[0] + .5, b[1], b[2] + .5))

    # ---- cheap moves (walk + fall): also the no-jump reachability set -----
    def cheap(n):
        x, s, z = nodes[n]
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                lst = stand.get((x + dx, z + dz))
                if not lst:
                    continue
                best = None
                for s2 in lst:
                    if s2 > s + 1:
                        continue
                    if s - s2 > MAXFALL:
                        continue
                    if best is None or s2 > best:
                        best = s2
                if best is None:
                    continue
                # the body must fit through the doorway it steps into
                if not clear_at(cells, x + dx, max(s, best), z + dz):
                    continue
                if dx and dz and not (clear_at(cells, x + dx, s, z) or
                                      clear_at(cells, x, s, z + dz)):
                    continue
                m = nid.get((x + dx, best, z + dz))
                if m is not None:
                    yield m

    # ---- climb / swim links ----------------------------------------------
    # A column of ladder, vine, scaffolding or water joins every standable
    # surface beside it, at any height inside the column.  That is one move
    # in the game and it is the mechanic 19 legs turned out to need.
    spans = {}
    for (x, y, z), name in cells.items():
        if name in CLIMB:
            spans.setdefault((x, z), []).append(y)
    groups = defaultdict(list)
    for (x, z), ys in spans.items():
        ys.sort()
        runs, cur = [], [ys[0]]
        for y in ys[1:]:
            if y == cur[-1] + 1:
                cur.append(y)
            else:
                runs.append(cur)
                cur = [y]
        runs.append(cur)
        for k, run in enumerate(runs):
            if len(run) < 2:
                continue
            groups[(x, z, k)] = (run[0], run[-1] + 1)
    climb_of = defaultdict(list)
    for (x, z, k), (lo, hi) in groups.items():
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for s in range(lo, hi + 1):
                    m = nid.get((x + dx, s, z + dz))
                    if m is not None:
                        climb_of[(x, z, k)].append(m)
    climb_link = defaultdict(list)
    for key, members in climb_of.items():
        if len(members) < 2:
            continue
        for m in members:
            climb_link[m].append(members)

    def climbs(n):
        for members in climb_link.get(n, ()):
            for m in members:
                if m != n:
                    yield m

    def cheap_all(n):
        yield from cheap(n)
        yield from climbs(n)

    # no-jump flood, for the cross-check
    seen = {src}
    stack = [src]
    while stack:
        for m in cheap(stack.pop()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    bx, by, bz = b
    walk_best = min(math.hypot(nodes[n][0] - bx, nodes[n][2] - bz) +
                    abs(nodes[n][1] - by) for n in seen)
    d0 = math.hypot(a[0] - bx, a[2] - bz) + abs(a[1] - by)
    walk_cover = 1.0 - walk_best / max(1e-9, d0)
    walk_through = walk_best <= 2.0

    # ---- jump moves -------------------------------------------------------
    grid = defaultdict(list)
    for n, (x, s, z) in enumerate(nodes):
        grid[(x // 8, z // 8)].append(n)

    jcache = {}

    def jumps(n):
        v = jcache.get(n)
        if v is not None:
            return v
        x, s, z = nodes[n]
        foot = cells.get((x, s - 1, z))
        cap = CAP_ICE if foot in ICE else CAP
        rise = 3 if foot == "slime_block" else 1
        out = []
        for kx in range(x // 8 - 2, x // 8 + 3):
            for kz in range(z // 8 - 2, z // 8 + 3):
                for m in grid.get((kx, kz), ()):
                    x2, s2, z2 = nodes[m]
                    d = math.hypot(x2 - x, z2 - z)
                    if d < 2.0 or d > cap + (0.5 if s2 < s else 0.0):
                        continue
                    if s2 - s > rise:
                        continue
                    if s - s2 > MAXFALL:
                        continue
                    if not arc_clear(cells, x, s, z, x2, s2, z2):
                        continue
                    out.append((m, d, s2 - s))
        jcache[n] = out
        return out

    # ---- Dijkstra ---------------------------------------------------------
    INF = float("inf")
    best = defaultdict(lambda: INF)
    best[src] = 0.0
    prev = {}
    pq = [(0.0, src)]
    while pq:
        c, n = heapq.heappop(pq)
        if c > best[n] + 1e-9:
            continue
        if n == dst:
            break
        for m in cheap_all(n):
            nc = c + EPS
            if nc < best[m]:
                best[m] = nc
                prev[m] = (n, None)
                heapq.heappush(pq, (nc, m))
        for m, d, dy in jumps(n):
            nc = c + 1.0 + (d / 4.0) ** 4
            if nc < best[m]:
                best[m] = nc
                prev[m] = (n, (d, dy))
                heapq.heappush(pq, (nc, m))

    if best[dst] == INF:
        return {"leg": idx, "solved": False, "walk_cover": walk_cover,
                "walk_through": walk_through, "nodes": len(nodes),
                "src_off": dsrc, "dst_off": ddst, "jumps": []}

    route = []
    n = dst
    while n != src:
        p, mv = prev[n]
        route.append((p, n, mv))
        n = p
    route.reverse()
    jl = [(round(mv[0], 3), mv[1]) for _, _, mv in route if mv]
    prof = [nodes[route[0][0]][1]] + [nodes[m][1] for _, m, _ in route]
    up = sum(max(0, q - p) for p, q in zip(prof, prof[1:]))
    dn = sum(max(0, p - q) for p, q in zip(prof, prof[1:]))
    return {"leg": idx, "solved": True, "walk_cover": walk_cover,
            "walk_through": walk_through, "nodes": len(nodes),
            "src_off": dsrc, "dst_off": ddst, "jumps": jl,
            "steps": len(route), "up": up, "down": dn,
            "lo": min(prof), "hi": max(prof),
            "net": nodes[dst][1] - nodes[src][1]}


def main():
    legvol = pickle.load(open(C.R1 + "/legvol.pkl", "rb"))
    rows = []
    for idx, a, b, pts in C.legs():
        r = solve(idx, a, b, pts, legvol)
        rows.append(r)
        js = [d for d, _ in r["jumps"]]
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} {'ok ' if r['solved'] else 'FAIL'} "
              f"nodes {r['nodes']:5d} jumps {len(js):3d} "
              f"median {C.pct(js,0.5) if js else 0:5.2f} max "
              f"{max(js) if js else 0:5.2f}  walk-cover {r['walk_cover']:5.1%}"
              f"  snap {r['src_off']:.1f}/{r['dst_off']:.1f}")
        sys.stdout.flush()
    with open(C.R1 + "/route.json", "w") as f:
        json.dump(rows, f)

    ok = [r for r in rows if r["solved"]]
    print(f"\n{len(ok)}/43 legs solved")
    wc = [r["walk_cover"] for r in rows]
    print(f"CROSS-CHECK no-jump walker: mean coverage "
          f"{sum(wc)/len(wc):.0%}, legs walkable end to end "
          f"{sum(r['walk_through'] for r in rows)}/43")
    alld = [d for r in ok for d, _ in r["jumps"]]
    allh = [h for r in ok for _, h in r["jumps"]]
    print(f"\njumps on the solved routes: n={len(alld)}, "
          f"{len(alld)/len(ok):.1f} per leg")
    print(f"  distance min {min(alld):.2f} median {C.pct(alld,0.5):.2f} "
          f"mean {sum(alld)/len(alld):.2f} p90 {C.pct(alld,0.9):.2f} "
          f"max {max(alld):.2f}")
    by = defaultdict(list)
    for d, h in zip(alld, allh):
        by[h if h >= -4 else -5].append(d)
    print("  by height change:")
    for h in sorted(by, reverse=True):
        v = by[h]
        lab = f"{h:+d}" if h > -5 else "<=-5"
        print(f"    {lab:>5s} n={len(v):4d} ({len(v)/len(alld):5.1%})  "
              f"min {min(v):.2f} median {C.pct(v,0.5):.2f} mean "
              f"{sum(v)/len(v):.2f} p90 {C.pct(v,0.9):.2f} max {max(v):.2f}")
    print("\n  distance histogram (0.5 m buckets):")
    hist = defaultdict(int)
    for d in alld:
        hist[round(d * 2) / 2] += 1
    for k in sorted(hist):
        print(f"    {k:4.1f} m  {hist[k]:4d}  {'#' * (hist[k] // 3)}")
    ups = [r["up"] for r in ok]
    dns = [r["down"] for r in ok]
    nets = [r["net"] for r in ok]
    print(f"\nvertical along the solved route: net median {C.pct(nets,0.5)} "
          f"mean {sum(nets)/len(nets):.1f}; climbed median {C.pct(ups,0.5)} "
          f"mean {sum(ups)/len(ups):.1f}; descended median {C.pct(dns,0.5)} "
          f"mean {sum(dns)/len(dns):.1f}")
    print(f"  legs that descend at all: {sum(1 for d in dns if d)}/{len(ok)}")


if __name__ == "__main__":
    main()
