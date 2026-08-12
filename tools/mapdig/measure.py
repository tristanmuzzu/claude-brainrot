"""The seven questions, measured against the real Parkour Spiral map.

Usage:  python measure.py [all|palette|physics|gaps|enclosure|width|
                          structures|vertical]

Everything is measured inside a *corridor*: the columns within CORR metres
(in plan) of a leg's helical spine, whose standable surface sits within
YWIN of the spine's local height.  That is the ground a player is on.
"""
import json
import math
import pickle
import sys
from collections import Counter, defaultdict

import common as C

CORR = float(__import__("os").environ.get("MCORR", 9.0))        # corridor half-width, metres, in plan
YWIN = 10         # a surface this far off the local spine height still counts
REACH = 8.0       # furthest horizontal distance a jump candidate may span
STRUCT_UP = 16    # how far above the terrace a landmark may reach

world = None
legvol = None
owner = None
L = None


def setup():
    global world, legvol, owner, L
    legvol = pickle.load(open(C.R1 + "/legvol.pkl", "rb"))
    owner = pickle.load(open(C.R1 + "/owner.pkl", "rb"))
    L = C.legs()


def col_dist(pts):
    """(x, z) -> (distance to spine in plan, index of nearest spine point)."""
    cache = {}

    def f(x, z):
        k = (x, z)
        v = cache.get(k)
        if v is None:
            best, bi = 1e18, 0
            cx, cz = x + 0.5, z + 0.5
            for i, p in enumerate(pts):
                d = (p[0] - cx) ** 2 + (p[2] - cz) ** 2
                if d < best:
                    best, bi = d, i
            v = (math.sqrt(best), bi)
            cache[k] = v
        return v
    return f


def corridor(idx, a, b, pts):
    """Standable positions in the leg's corridor.

    Returns (stand, cells, dist) where stand maps (x, z) -> [(feet_y,
    ground_block_name, spine_index)], cells is the leg volume, dist the
    column-distance function.
    """
    cells = legvol[idx]
    dist = col_dist(pts)
    stand = defaultdict(list)
    for (x, y, z), name in cells.items():
        if owner.get((x, y, z)) != idx:
            continue
        if not C.solid_name(name):
            continue
        d, i = dist(x, z)
        if d > CORR:
            continue
        if C.solid_name(cells.get((x, y + 1, z))):
            continue
        if C.solid_name(cells.get((x, y + 2, z))):
            continue
        if abs((y + 1) - pts[i][1]) > YWIN:
            continue
        stand[(x, z)].append((y + 1, name, i))
    for k in stand:
        stand[k].sort()
    return stand, cells, dist


# ---------------------------------------------------------------- 1 palette

def q_palette():
    rows = []
    for idx, a, b, pts in L:
        stand, cells, dist = corridor(idx, a, b, pts)
        floor = Counter()      # what you stand on
        skin = Counter()       # floor + the three cells above it
        for (x, z), lst in stand.items():
            for fy, name, i in lst:
                floor[name] += 1
                skin[name] += 1
                for dy in range(0, 3):
                    n2 = cells.get((x, fy + dy, z))
                    if n2:
                        skin[n2] += 1
        tot = sum(skin.values())
        top = skin.most_common(15)
        dom = top[0][1] / tot if tot else 0
        rows.append({
            "leg": idx, "y": [a[1], b[1]],
            "floor_cells": sum(floor.values()),
            "palette_floor": len(floor), "palette_skin": len(skin),
            "dominant": top[0][0] if top else None, "dominant_frac": dom,
            "top15": top,
            "cover80": next((k for k in range(1, len(top) + 1)
                             if sum(v for _, v in top[:k]) / tot >= 0.8),
                            len(top)),
        })
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} palette floor "
              f"{len(floor):3d} skin {len(skin):3d}  dom {top[0][0]:<22s} "
              f"{dom:5.1%}  80% in {rows[-1]['cover80']} kinds")
    ps = [r["palette_floor"] for r in rows]
    print(f"\npalette size (floor blocks) per leg: min {min(ps)} median "
          f"{C.pct(ps,0.5)} mean {sum(ps)/len(ps):.1f} max {max(ps)}")
    ps = [r["palette_skin"] for r in rows]
    print(f"palette size (floor + 3 above)     : min {min(ps)} median "
          f"{C.pct(ps,0.5)} mean {sum(ps)/len(ps):.1f} max {max(ps)}")
    ds = [r["dominant_frac"] for r in rows]
    print(f"dominant material share: min {min(ds):.0%} median "
          f"{C.pct(ds,0.5):.0%} max {max(ds):.0%}")
    cs = [r["cover80"] for r in rows]
    print(f"kinds needed to cover 80% of a leg: min {min(cs)} median "
          f"{C.pct(cs,0.5)} mean {sum(cs)/len(cs):.1f} max {max(cs)}")
    return rows


# ---------------------------------------------------------------- 2 physics

def q_physics():
    rows = []
    tot_fam = Counter()
    line_fam = Counter()
    legs_with = Counter()
    none_legs = []
    for idx, a, b, pts in L:
        stand, cells, dist = corridor(idx, a, b, pts)
        # cells a body occupies or brushes: the two cells above every
        # standable surface, the surface itself, and anything within one
        # cell of those.
        online = set()
        for (x, z), lst in stand.items():
            for fy, name, i in lst:
                for dy in range(-1, 3):
                    online.add((x, fy + dy, z))
        near = set()
        for (x, y, z) in online:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    near.add((x + dx, y, z + dz))
        band = sum(1 for c in online if c in cells and owner.get(c) == idx)
        mech = Counter()
        scen = Counter()
        for (x, y, z), name in cells.items():
            if owner.get((x, y, z)) != idx:
                continue
            fam = C.kind(name)
            if fam is None:
                continue
            if (x, y, z) in near:
                mech[fam] += 1
            else:
                scen[fam] += 1
        tot_fam.update(mech)
        tot_fam.update(scen)
        line_fam.update(mech)
        for f in mech:
            legs_with[f] += 1
        if not mech:
            none_legs.append(idx)
        rows.append({"leg": idx, "y": [a[1], b[1]], "band_cells": band,
                     "mechanic": dict(mech), "scenery": dict(scen),
                     "mech_frac": sum(mech.values()) / max(1, band)})
        m = ", ".join(f"{k} {v}" for k, v in mech.most_common())
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} band {band:5d}  "
              f"mech {sum(mech.values()):4d} ({rows[-1]['mech_frac']:5.2%})  "
              f"{m if m else '-- none --'}")
    print("\nfamily totals (on/next to the walking line | anywhere in leg):")
    for f, n in tot_fam.most_common():
        print(f"  {f:12s} {line_fam[f]:6d} | {n:6d}   on the line in "
              f"{legs_with[f]:2d}/43 legs")
    print(f"\nlegs with no physics block on the line: {len(none_legs)} "
          f"-> {none_legs}")
    return rows


# ------------------------------------------------------------------- 3 gaps

def q_gaps():
    allg = []
    rows = []
    for idx, a, b, pts in L:
        stand, cells, dist = corridor(idx, a, b, pts)
        nodes = []
        index = {}
        for (x, z), lst in stand.items():
            for fy, name, i in lst:
                index[(x, fy, z)] = len(nodes)
                nodes.append((x, fy, z, i))
        # union-find over walk-connected surfaces (8-neighbour, |dy| <= 1)
        par = list(range(len(nodes)))

        def find(v):
            while par[v] != v:
                par[v] = par[par[v]]
                v = par[v]
            return v

        def union(u, v):
            u, v = find(u), find(v)
            if u != v:
                par[u] = v
        for (x, fy, z, i) in nodes:
            n = index[(x, fy, z)]
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dx == 0 and dz == 0:
                        continue
                    for dy in (-1, 0, 1):
                        m = index.get((x + dx, fy + dy, z + dz))
                        if m is not None:
                            union(n, m)
        groups = defaultdict(list)
        for n, (x, fy, z, i) in enumerate(nodes):
            groups[find(n)].append(n)
        # spatial hash for candidate lookup
        grid = defaultdict(list)
        for n, (x, fy, z, i) in enumerate(nodes):
            grid[(x // 8, z // 8)].append(n)
        gaps = []
        for g, members in groups.items():
            best = None
            for n in members:
                x, fy, z, i = nodes[n]
                tan = None
                p, q = pts[min(i, len(pts) - 2)], pts[min(i + 1, len(pts) - 1)]
                tx, tz = q[0] - p[0], q[2] - p[2]
                tl = math.hypot(tx, tz) or 1.0
                tx, tz = tx / tl, tz / tl
                for kx in range(x // 8 - 2, x // 8 + 3):
                    for kz in range(z // 8 - 2, z // 8 + 3):
                        for m in grid.get((kx, kz), ()):
                            if find(m) == g:
                                continue
                            x2, fy2, z2, i2 = nodes[m]
                            d = math.hypot(x2 - x, z2 - z)
                            if d < 2.0 or d > REACH:
                                continue
                            dy = fy2 - fy
                            if dy > 1 or dy < -8:
                                continue
                            if (x2 - x) * tx + (z2 - z) * tz <= 0.3 * d:
                                continue        # not forward along the leg
                            if best is None or d < best[0]:
                                best = (d, dy, len(members))
            if best:
                gaps.append(best)
        allg.extend((idx,) + g for g in gaps)
        ds = [g[0] for g in gaps]
        rows.append({"leg": idx, "y": [a[1], b[1]], "islands": len(groups),
                     "gaps": len(gaps),
                     "median": C.pct(ds, 0.5) if ds else None,
                     "max": max(ds) if ds else None})
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} islands {len(groups):4d} "
              f"forward gaps {len(gaps):4d}  median "
              f"{C.pct(ds,0.5) if ds else 0:.2f}  max {max(ds) if ds else 0:.2f}")
    ds = [g[1] for g in allg]
    print(f"\nall forward island-to-island gaps: n={len(ds)}")
    print(f"  min {min(ds):.2f} median {C.pct(ds,0.5):.2f} mean "
          f"{sum(ds)/len(ds):.2f} p90 {C.pct(ds,0.9):.2f} max {max(ds):.2f}")
    byh = defaultdict(list)
    for idx, d, dy, sz in allg:
        byh[max(-6, dy) if dy >= -6 else -7].append(d)
    print("  by height change (feet-to-feet):")
    for dy in sorted(byh, reverse=True):
        v = byh[dy]
        lab = f"{dy:+d}" if dy > -7 else "<=-7"
        print(f"    {lab:>5s}  n={len(v):5d}  min {min(v):.2f} median "
              f"{C.pct(v,0.5):.2f} mean {sum(v)/len(v):.2f} p90 "
              f"{C.pct(v,0.9):.2f} max {max(v):.2f}")
    return rows, allg


# -------------------------------------------------------------- 4 enclosure

def snap(stand, pts, i, cellsize=6):
    """Nearest standable position to spine point i."""
    p = pts[i]
    best, bp = 1e18, None
    px, pz = int(round(p[0])), int(round(p[2]))
    for dx in range(-cellsize, cellsize + 1):
        for dz in range(-cellsize, cellsize + 1):
            for fy, name, j in stand.get((px + dx, pz + dz), ()):
                d = (dx + px + .5 - p[0]) ** 2 + (dz + pz + .5 - p[2]) ** 2 \
                    + (fy - p[1]) ** 2
                if d < best:
                    best, bp = d, (px + dx, fy, pz + dz)
    return bp


def q_enclosure(roof=6, wall=4):
    rows = []
    runs_in, runs_out = [], []
    tot, enc = 0, 0
    ceil_h, wall_l, wall_r, roofed, oneside = [], [], [], 0, 0
    for idx, a, b, pts in L:
        stand, cells, dist = corridor(idx, a, b, pts)
        seq = []
        for i in range(len(pts)):
            sp = snap(stand, pts, i)
            if sp is None:
                seq.append(None)
                continue
            x, fy, z = sp
            ch = next((k for k in range(2, 41)
                       if C.solid_name(cells.get((x, fy + k, z)))), 99)
            ceil_h.append(ch)
            has_roof = ch <= roof
            roofed += has_roof
            p, q = pts[min(i, len(pts) - 2)], pts[min(i + 1, len(pts) - 1)]
            tx, tz = q[0] - p[0], q[2] - p[2]
            tl = math.hypot(tx, tz) or 1.0
            nx, nz = -tz / tl, tx / tl
            sides = 0
            for s, acc in ((1, wall_l), (-1, wall_r)):
                hit = 99
                for k in range(1, 25):
                    cx = int(round(x + nx * s * k))
                    cz = int(round(z + nz * s * k))
                    if any(C.solid_name(cells.get((cx, fy + h, cz)))
                           for h in (0, 1)):
                        hit = k
                        break
                acc.append(hit)
                sides += hit <= wall
            oneside += sides >= 1
            seq.append(bool(has_roof and sides == 2))
        good = [v for v in seq if v is not None]
        f = sum(good) / len(good) if good else 0.0
        tot += len(good)
        enc += sum(good)
        # run lengths (1 sample ~ 1 metre of arc)
        cur, val = 0, None
        for v in good:
            if v == val:
                cur += 1
            else:
                if val is True:
                    runs_in.append(cur)
                elif val is False:
                    runs_out.append(cur)
                val, cur = v, 1
        if val is True:
            runs_in.append(cur)
        elif val is False:
            runs_out.append(cur)
        rows.append({"leg": idx, "y": [a[1], b[1]], "samples": len(good),
                     "enclosed_frac": f})
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} samples {len(good):3d}  "
              f"enclosed {f:5.1%}")
    print(f"\noverall enclosed (roof<={roof}, walls<={wall} both sides): "
          f"{enc/tot:.1%} of {tot} metre-samples")
    if runs_in:
        print(f"  enclosed runs: n={len(runs_in)} median "
              f"{C.pct(runs_in,0.5):.0f} m mean {sum(runs_in)/len(runs_in):.1f} "
              f"max {max(runs_in)} m")
    if runs_out:
        print(f"  open runs:     n={len(runs_out)} median "
              f"{C.pct(runs_out,0.5):.0f} m mean "
              f"{sum(runs_out)/len(runs_out):.1f} max {max(runs_out)} m")
    nl = sum(1 for r in rows if r["enclosed_frac"] < 0.02)
    print(f"  legs essentially never enclosed (<2%): {nl}/43")
    nh = sum(1 for r in rows if r["enclosed_frac"] > 0.5)
    print(f"  legs enclosed more than half the way: {nh}/43")
    fin = [c for c in ceil_h if c < 99]
    print(f"\n  ceiling above the walking surface: nothing within 40 on "
          f"{sum(1 for c in ceil_h if c == 99)/len(ceil_h):.0%} of samples;"
          f" where there is one, min {min(fin)} p10 {C.pct(fin,0.1)} median "
          f"{C.pct(fin,0.5)} p90 {C.pct(fin,0.9)} max {max(fin)}")
    print(f"  roof within {roof}: {roofed/tot:.0%} of samples")
    both = wall_l + wall_r
    fw = [w for w in both if w < 99]
    print(f"  wall distance sideways: no wall within 24 on "
          f"{sum(1 for w in both if w == 99)/len(both):.0%} of sides; where "
          f"there is one, median {C.pct(fw,0.5)} p90 {C.pct(fw,0.9)}")
    print(f"  at least one wall within {wall}: {oneside/tot:.0%} of samples")
    return rows, runs_in, runs_out


# ------------------------------------------------- 5 width and radial wander

def q_width():
    rows = []
    allw = []
    for idx, a, b, pts in L:
        stand, cells, dist = corridor(idx, a, b, pts)
        widths, radii = [], []
        for i in range(len(pts)):
            sp = snap(stand, pts, i)
            if sp is None:
                continue
            x, fy, z = sp
            radii.append(math.hypot(x + .5, z + .5))
            p, q = pts[min(i, len(pts) - 2)], pts[min(i + 1, len(pts) - 1)]
            tx, tz = q[0] - p[0], q[2] - p[2]
            tl = math.hypot(tx, tz) or 1.0
            nx, nz = -tz / tl, tx / tl
            w = 1
            for s in (1, -1):
                for k in range(1, 21):
                    cx, cz = int(round(x + nx * s * k)), int(round(z + nz * s * k))
                    hits = [t for t in stand.get((cx, cz), ())
                            if abs(t[0] - fy) <= 1]
                    if not hits:
                        break
                    w += 1
            widths.append(w)
        allw.extend(widths)
        rows.append({"leg": idx, "y": [a[1], b[1]],
                     "w_min": min(widths) if widths else None,
                     "w_med": C.pct(widths, 0.5) if widths else None,
                     "w_max": max(widths) if widths else None,
                     "r_min": min(radii) if radii else None,
                     "r_max": max(radii) if radii else None,
                     "r_span": (max(radii) - min(radii)) if radii else None})
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} width min/med/max "
              f"{min(widths):2d}/{C.pct(widths,0.5):2d}/{max(widths):2d}  "
              f"radius {min(radii):5.1f}-{max(radii):5.1f} "
              f"(span {max(radii)-min(radii):4.1f})")
    print(f"\ncorridor width over all samples: min {min(allw)} median "
          f"{C.pct(allw,0.5)} mean {sum(allw)/len(allw):.1f} p90 "
          f"{C.pct(allw,0.9)} max {max(allw)}")
    sp = [r["r_span"] for r in rows]
    print(f"radial wander within one leg: min {min(sp):.1f} median "
          f"{C.pct(sp,0.5):.1f} mean {sum(sp)/len(sp):.1f} max {max(sp):.1f}")
    return rows


# ------------------------------------------------------------- 6 structures

def q_structures():
    rows = []
    for idx, a, b, pts in L:
        stand, cells, dist = corridor(idx, a, b, pts)
        # ground height per column, taken as the standable surface nearest
        # the local spine height
        ground = {}
        for (x, z), lst in stand.items():
            d, i = dist(x, z)
            fy = min(lst, key=lambda t: abs(t[0] - pts[i][1]))[0]
            ground[(x, z)] = fy
        # Stop each column at the rock lid.  The tower is a cone with the
        # course cut into it, so the massif closes over the corridor only a
        # few blocks up; without this the biggest "structure" on leg 36 came
        # out as 6,768 cells of plain stone running from y 195 to 225.
        cand = set()
        for (x, z), g in ground.items():
            lid = g + STRUCT_UP
            for y in range(g, g + STRUCT_UP):
                if all(C.solid_name(cells.get((x, y + k, z)))
                       for k in range(6)):
                    lid = y
                    break
            for y in range(g, lid):
                if C.solid_name(cells.get((x, y, z))):
                    cand.add((x, y, z))
        seen, comps = set(), []
        for c in cand:
            if c in seen:
                continue
            stack, comp = [c], []
            seen.add(c)
            while stack:
                x, y, z = stack.pop()
                comp.append((x, y, z))
                for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                                   (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    n = (x + dx, y + dy, z + dz)
                    if n in cand and n not in seen:
                        seen.add(n)
                        stack.append(n)
            comps.append(comp)
        # A mass that is still going at the top of the window is the tower's
        # own rock (the cliff carrying the next turn), not a landmark: the
        # biggest "structure" on leg 36 was 6,768 cells of plain stone
        # running from y 195 to 225.  Drop anything open-topped, and anything
        # whose plan footprint is longer than a building can be.
        keep = []
        for c in comps:
            xs = [q[0] for q in c]
            zs = [q[2] for q in c]
            if max(max(xs) - min(xs), max(zs) - min(zs)) + 1 > 28:
                continue
            if Counter(owner.get(q) for q in c).most_common(1)[0][0] != idx:
                continue
            keep.append(c)
        comps = keep
        comps.sort(key=len, reverse=True)
        big = [c for c in comps if len(c) >= 20]
        top = comps[0] if comps else []
        bb = None
        if top:
            xs = [c[0] for c in top]
            ys = [c[1] for c in top]
            zs = [c[2] for c in top]
            bb = [max(xs) - min(xs) + 1, max(ys) - min(ys) + 1,
                  max(zs) - min(zs) + 1]
        rows.append({"leg": idx, "y": [a[1], b[1]], "masses>=20": len(big),
                     "biggest": len(top), "bbox": bb,
                     "second": len(comps[1]) if len(comps) > 1 else 0})
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} masses>=20 {len(big):3d}  "
              f"biggest {len(top):5d} cells bbox {bb}  second "
              f"{rows[-1]['second']}")
    bs = [r["biggest"] for r in rows]
    print(f"\nbiggest above-ground mass per leg: min {min(bs)} median "
          f"{C.pct(bs,0.5)} mean {sum(bs)/len(bs):.0f} max {max(bs)}")
    hs = [r["bbox"][1] for r in rows if r["bbox"]]
    print(f"  its height: min {min(hs)} median {C.pct(hs,0.5)} max {max(hs)}")
    ms = [r["masses>=20"] for r in rows]
    print(f"masses of 20+ cells per leg: min {min(ms)} median "
          f"{C.pct(ms,0.5)} mean {sum(ms)/len(ms):.1f} max {max(ms)}")
    return rows


# ---------------------------------------------------------------- 7 vertical

def q_vertical():
    rows = []
    for idx, a, b, pts in L:
        stand, cells, dist = corridor(idx, a, b, pts)
        prof = []
        for i in range(len(pts)):
            sp = snap(stand, pts, i)
            if sp:
                prof.append(sp[1])
        up = sum(max(0, q - p) for p, q in zip(prof, prof[1:]))
        dn = sum(max(0, p - q) for p, q in zip(prof, prof[1:]))
        net = b[1] - a[1]
        rows.append({"leg": idx, "y": [a[1], b[1]], "net": net,
                     "up": up, "down": dn, "travel": up + dn,
                     "lo": min(prof) if prof else None,
                     "hi": max(prof) if prof else None})
        print(f"leg {idx:2d} y{a[1]:4d}-{b[1]:<4d} net {net:+3d}  up {up:3d} "
              f"down {dn:3d}  travel {up+dn:3d}  surface {min(prof)}..{max(prof)}"
              f"  dips below start by {max(0, a[1]-min(prof))}")
    ns = [r["net"] for r in rows]
    ts = [r["travel"] for r in rows]
    dd = [r["down"] for r in rows]
    print(f"\nnet rise per leg: min {min(ns)} median {C.pct(ns,0.5)} mean "
          f"{sum(ns)/len(ns):.1f} max {max(ns)}")
    print(f"total travel per leg (up+down): median {C.pct(ts,0.5)} mean "
          f"{sum(ts)/len(ts):.1f} max {max(ts)}")
    print(f"descent per leg: median {C.pct(dd,0.5)} mean "
          f"{sum(dd)/len(dd):.1f} max {max(dd)}")
    print(f"ratio travel/|net|: mean "
          f"{sum(t/max(1,abs(n)) for t,n in zip(ts,ns))/len(ts):.2f}")
    nz = sum(1 for r in rows if r["down"] > 0)
    print(f"legs whose walking surface ever goes down: {nz}/43")
    nb = sum(1 for r in rows if r["lo"] is not None and r["lo"] < r["y"][0])
    print(f"legs that dip below their own starting checkpoint: {nb}/43")
    return rows


def main():
    setup()
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    out = {}
    order = ["palette", "physics", "gaps", "enclosure", "width",
             "structures", "vertical"]
    for name in order:
        if what not in ("all", name):
            continue
        print("\n" + "=" * 72)
        print(name.upper())
        print("=" * 72)
        r = globals()["q_" + name]()
        out[name] = r[0] if isinstance(r, tuple) else r
    with open(C.R1 + f"/results_{what}.json", "w") as f:
        json.dump(out, f, default=str)


if __name__ == "__main__":
    main()
