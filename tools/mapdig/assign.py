"""Give every cell exactly one owning leg.

The per-leg volumes overlap badly (74% of their cells sit in more than one),
because consecutive checkpoints are only ~4 blocks apart in height and ~38 m
apart along the arc.  Per-leg *counts* are meaningless until each cell has a
single owner, so: a cell belongs to the leg whose spine passes nearest to it
in 3-D, considered only among the legs whose volume already contains it.

Output: r1/owner.pkl -> {(x, y, z): leg_index}
"""
import pickle
import time

import common as C

lv = pickle.load(open(C.R1 + "/legvol.pkl", "rb"))
L = C.legs()
spines = {i: pts for i, a, b, pts in L}

cand = {}
for i, cells in lv.items():
    for c in cells:
        cand.setdefault(c, []).append(i)

t0 = time.time()
owner = {}
for c, legs_ in cand.items():
    if len(legs_) == 1:
        owner[c] = legs_[0]
        continue
    x, y, z = c[0] + 0.5, c[1] + 0.5, c[2] + 0.5
    best, bi = 1e18, legs_[0]
    for i in legs_:
        for p in spines[i]:
            d = (p[0] - x) ** 2 + (p[1] - y) ** 2 + (p[2] - z) ** 2
            if d < best:
                best, bi = d, i
    owner[c] = bi

with open(C.R1 + "/owner.pkl", "wb") as f:
    pickle.dump(owner, f, protocol=5)
n = {}
for v in owner.values():
    n[v] = n.get(v, 0) + 1
print(f"{len(owner)} cells assigned in {time.time()-t0:.0f}s")
print("cells per leg: min", min(n.values()), "median",
      C.pct(list(n.values()), 0.5), "max", max(n.values()))
