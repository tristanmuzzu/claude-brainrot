# What a good spiral-tower parkour level is, measured

Why the rules in `docs/RULES.md` are the rules. Two sources, and where they
disagree the map file wins over anything written about the genre:

- **The real map, block by block.** Hielke's *Parkour Spiral*, 1.2M downloads,
  parsed from the world save: 1,575,137 non-air cells, 44 checkpoint plates,
  43 levels. Scripts in `tools/mapdig/`, full per-level tables in
  `docs/reference/MAP_FINDINGS.md`.
- **The footage, frame by frame.** Three runs of the real maps, sampled and
  read. Frames in `docs/reference/frames/`, sheets in `docs/reference/sheets/`.

A **leg** — one level — is the stretch between two consecutive checkpoints.
Every number below enumerates a whole corridor; nothing is sampled.

> **Three claims in `docs/TOWER.md` did not survive being measured**, and they
> had each been load-bearing for a rebuild. They are corrected in place below
> and the old text is left standing in TOWER.md as the record of what was
> believed: the reference does *not* alternate interior and exposed, it does
> *not* put one big landmark on each level, and its levels are *not*
> monotonic climbs.

---

## The shape of the thing

- 43 levels over **4.82 revolutions** — 8.9 levels to a turn, 36.9 blocks of
  height per turn.
- A level is **38.9 m of arc** (median 34.2, min 13.1, max 76.8) and **rises
  4.1 blocks** (median 4, max 10).
- Course radius **26.2 / 44.6 / 49.1** min/mean/max, tower centred on the
  origin, y 52 → 230.

Forty metres of running to gain four blocks. A level is a *shallow* thing.

Cross-checks against the numbers already in `docs/TOWER.md`, all independent
re-implementations: no-jump walkability **45%** mean and **0 of 43** legs
passable end to end (recorded 46%, 0 of 43); course band **98.3% ordinary
cubes, 0.8% slabs, 0.2% fences** (recorded 96.1 / 0.7 / 0.2).

---

## 1. A level is fourteen materials

| | min | median | max |
|---|---|---|---|
| distinct **floor** materials in one level | 7 | **14** | 26 |
| distinct materials in floor + 3 cells above | 9 | **21** | 43 |
| share held by the commonest material | 13% | **26%** | 51% |
| materials needed to cover 80% of the level | 3 | **7** | 12 |

No material owns more than half of any level. The theme is **one strong
material at about a quarter with a long tail underneath**: sand 44%, podzol
24%, honeycomb 25%, black wool 46%, nether wart block 45%. The dominant
material is a real theme marker — but seven kinds are needed to account for
four fifths of what you look at.

This tower gives a level six material roles and most levels set two or three.
That is the gap, and it is probably the largest single reason the reference's
levels read as places and this tower's read as boxes.

## 2. Lava and water are the mechanic; slime is rationed; cobweb does not exist

A block is *on the walking line* if it is within one cell of the column a body
occupies standing on any corridor surface.

| family | cells on the line | levels using it |
|---|---|---|
| **lava** | 1,562 | **26 / 43** |
| **water** | 1,069 | **20 / 43** |
| ice, packed and blue | 557 | 3 / 43 |
| magma | 442 | 10 / 43 |
| soul sand and soul soil | 355 | 7 / 43 |
| hay | 190 | 3 / 43 |
| **slime** | 155 | **26 / 43** |
| vine / ladder | 84 / 52 | 7 / 43 each |
| trapdoor | 44 | 10 / 43 |
| **cobweb** | **0 in the whole map** | 0 |
| honey / scaffolding / powder snow | 2 / 3 / 25 cells, whole map | ~0 |

The median level spends **15.2% of its walking band** on or beside a physics
block, from 0% to 73.5%; only **two levels of forty-three have none**. Three
quarters of the water is a lake you fall into rather than something you cross:
hazard and floor, not obstacle.

**Slime is the one deliberate movement gadget and it is rationed to a pad.**
189 cells in the entire map, in 46 clusters, **34 of them exactly 2×2** — about
one bounce pad per level. The obvious "physics block" vocabulary a designer
reaches for — cobweb, honey, scaffolding, powder snow — is simply not used.

## 3. Three metres is the jump

122 jumps read off Dijkstra solutions of the 26 levels a walk/fall/climb/jump
model can finish. **4.7 jumps per level.**

| height change | n | share | median | max |
|---|---|---|---|---|
| **+3** (off a slime pad) | 20 | **16.4%** | 2.24 | 5.00 |
| +2 | 4 | 3.3% | 2.83 | 3.61 |
| **+1** | 35 | 28.7% | 3.16 | **5.10** |
| **level** | 46 | 37.7% | 3.16 | 4.47 |
| −1 | 15 | 12.3% | 3.00 | 4.24 |
| −3, −4 | 2 | 1.6% | — | 3.61 |
| **all** | 122 | | **3.16** (mean 3.20, p90 4.12) | 5.10 |

Distances cluster hard: 2.0 m ×24, **3.0 m ×56**, 3.5 m ×13, 4.0 m ×24, 5.0 m
×3. A route-free second read over all 43 levels — every terrace edge with no
walkable continuation, paired with the nearest arc-clear landing — agrees:
2,245 edges, median 2.00, p90 4.12, nothing legal past about 5 m.

Against this project's envelope (flat 2.00–4.26, up one 2.00–3.10, down one
2.35–4.98):

- **flat** — the reference runs 2.24–4.47 with a median of 3.16. Ours is right,
  and nothing in the reference sits at the top of it.
- **up one** — the reference reaches **5.10 m**, ours stops at 3.10. **The one
  real mismatch.** The reference routinely asks for a four-metre gap that gains
  a block, and this motion model cannot express it; the mechanics that buy it
  there (slab and stair half-surfaces, head-hitting to cancel a jump, ice
  momentum, steered jumps) are exactly the ones this kernel lacks.
- **down** — the reference almost never jumps down more than one block, 2 of
  122. We are more generous below the horizontal than it ever needs.

**Honest limit.** 17 of 43 levels cannot be solved by any walk/fall/climb/jump
model built here, and widening the search space changed the solve count by
zero — so the blocker is the move set, not the search. The gap table is drawn
from the 26 that solve and therefore under-represents the hardest jumps in the
map. (One blocker was a genuine bug and is worth recording for any future dig:
the map wires **iron doors to pressure plates**, and treating a door as a wall
made whole levels unreachable.)

## 4. It is a groove, not an alternation of rooms and ledges

The claim under test, from `docs/TOWER.md`: *"the reference alternates exposed
ledge with enclosed rooms, tunnels and shafts every ten to twenty seconds."*
Over 1,662 metre-samples:

| | |
|---|---|
| fully enclosed (roof within 6, walls within 4 both sides) | **6.1%** |
| levels enclosed more than half the way | **0 / 43** |
| levels essentially never enclosed | **20 / 43** |
| enclosed runs | median **2 m**, max 9 |
| open runs | median **13 m** |

**There is no alternation.** But the corridor is not open sky either:

| | |
|---|---|
| a wall within 4 m on at least one side | **71%** of samples, median distance **3 m** |
| a rock lid somewhere overhead | **98%** of samples, median **8 blocks** up |
| roof within 6 | 25% |
| nothing overhead within 40 blocks | **2%** |

A shelf with rock a few metres off one shoulder, the open drop off the other,
and a lid eight blocks overhead. Almost always half-enclosed, almost never
fully enclosed, **almost never actually open above** — which is precisely what
a contact sheet of this tower is, and why half its frames are sky.

## 5. The shelf is four blocks wide, and levels do not wander

| | min | median | p90 | max |
|---|---|---|---|---|
| walkable width across the corridor | 1 | **4** | 9 | 18 |
| radial wander **within one level** | 1.1 | **4.4 m** | — | 21.8 |

The walkable shelf is four blocks at the median and often one. And a level
barely moves in and out: 4.4 m of radius across its whole length, against a
whole-map band of 26–49. **Radial wander is a per-level feature used twice in
forty-three levels** — the pair that descends the outside of the tower — not a
continuous meander. (This corrects the reading in `docs/TOWER.md` §8, which
took the whole-map radius range as evidence that every level should wander.)

## 6. There is no landmark per level

A structure here is a connected mass of solid cells standing above the walking
surface, cut off at the rock lid.

| | min | median | mean | max |
|---|---|---|---|---|
| biggest above-ground mass in a level (cells) | 0 | **12** | 37 | 595 |
| its height (blocks) | 1 | **4** | — | 7 |
| masses of 20+ cells per level | 0 | **0** | 0.7 | 7 |

The median level has nothing standing on it bigger than twelve blocks, and the
few real masses are terrain — a wooded knoll, a dark-oak tree, a dripstone
outcrop. The biggest genuinely *built* thing in forty-three levels is 9×4×7.

**A level's identity comes from its floor, not from a hero structure.** This
tower's gated landmarks were added for a real reason and measurably worked
(levels holding a structure at readable size went 20% → 52%), so they stay —
but they are compensating for a floor palette that has never been built, and
they are not what makes the reference legible.

## 7. Levels descend

| along the ground profile | median | mean | max |
|---|---|---|---|
| net rise | **4** | 4.1 | 10 |
| total vertical travel (up + down) | **11** | 11.9 | 31 |
| descent within the level | **4** | 3.9 | 14 |

Travel to net rise: **3.36 to 1**. **36 of 43 levels descend somewhere, and 22
dip below their own starting checkpoint.** Combined with §3 — the map almost
never jumps down — descent happens by **falling off an edge**, which is free.

Every level in this tower is a monotonic climb.

---

## 8. What the frames say

<!-- filled from the footage pass -->

---

## What this changes

| the tower believed | measured | so |
|---|---|---|
| three to five materials per level | **14 floor materials, dominant 26%** | palette is the identity lever, and it has never been used |
| alternate interior and exposed every 10–20 s | **6% enclosed, runs of 2 m** | build the groove: wall one side, drop the other, lid overhead. Interiors are pinches |
| one big landmark per level | **median biggest mass 12 cells** | keep ours, but the floor does the work and small furniture is everywhere |
| the course should wander radially | **4.4 m within a level** | wandering is a feature for one or two levels, not a default |
| levels climb | **36/43 descend, 22 dip below their start** | a level goes down as well as up, by falling |
| exotic physics blocks are the variety | **cobweb 0, honey 2, scaffolding 3** | lava and water are the mechanic; slime is one pad |
| difficulty is the top of the envelope | **modal jump 3.0 m, 4.7 jumps a level** | write 3.0–3.5 m and save the envelope's top for a showpiece |
