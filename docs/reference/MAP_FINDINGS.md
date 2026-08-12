# Parkour Spiral, dug block by block

What the real map does, measured from the save at
`…/ae099ecc-…/scratchpad/psmap/Parkour Spiral/`.  Nothing under that path was
modified and nothing in the repo was touched; every number below comes from a
script in
`/tmp/claude-1000/-home-tristan-projects-claude-brainrot/7d49286c-3332-4cc0-9d89-cadc822a1df6/scratchpad/r1/`.

## The five that would change how you build a level

1. **A level's palette is fourteen materials, not three.**  Median 14 distinct
   floor blocks per leg, no material over 51% anywhere, median 7 kinds needed
   to cover 80% of what you see.  The theme is one strong material at about a
   quarter, with a long tail underneath.
2. **There is no landmark per level.**  The median biggest thing standing on a
   terrace is **12 cells, 4 blocks tall**, and 0 masses of 20+ cells.  The big
   ones are trees and rock outcrops.  Identity comes from the floor, not from
   a hero structure.
3. **Three metres is the map's jump.**  122 jumps on solved routes: modal
   3.0 m, median 3.16, max 5.10.  The single mismatch with our envelope is
   **up-one**, where the real map reaches 5.10 m and we stop at 3.10.  We are
   *more* generous than the reference on down-one and never need to be.
4. **The reference does not alternate interior and exposed.**  Fully enclosed
   6.1% of the way, 0 of 43 legs enclosed more than half, enclosed runs median
   2 m.  What it does instead is uniform: a **groove** — rock a median 3 m to
   one side on 71% of samples, open drop the other, a rock lid a median 8
   blocks overhead on 98% of samples.
5. **Levels descend.**  36 of 43 legs go down somewhere, 22 dip below their own
   starting checkpoint, and a leg travels 11 blocks vertically to gain 4.  But
   it almost never *jumps* down — 2 of 122 jumps drop more than one block.
   Descent is falling off an edge, which is free.

Two more that are cheap to act on: **cobweb, honey, scaffolding and powder snow
are effectively absent from the whole map** (0, 2, 3 and 25 cells) while lava
and water are the mechanic in 26 and 20 of 43 legs; and **slime is rationed to
one 2×2 bounce pad per level** (46 clusters, 34 of them exactly four cells).

## Scripts, and what each one is for

| script | what it does | runtime |
|---|---|---|
| `load.py` | reads the region files into `world.pkl`, 1,575,137 non-air cells, `\|x\|,\|z\| <= 100`, y 36–252. Keeps **fluids** — the existing `realworld.json` drops water into its air set, which makes the physics question unanswerable from it | 33 s |
| `legvol.py` | cuts the tower into 43 per-leg volumes (16 m in plan around each leg's spine) | 35 s |
| `assign.py` | gives every cell exactly **one** owning leg. Without this the volumes overlap: 551,682 of 743,031 cells were in more than one, and every per-leg count was inflated | 23 s |
| `common.py` | block classification (passable / solid / full cube / physics family), plate loading, leg spines | — |
| `explore.py` | sanity checks, including the TOWER.md band-composition cross-check | 9 min |
| `measure.py` | questions 1, 2, 4, 5, 6, 7 | 47 s |
| `route.py` | question 3: solves each leg with Dijkstra over walk / fall / climb / jump and reads the gap table off the route. Also runs the no-jump walker cross-check | 29 s |
| `gaps2.py` | question 3, second and route-free read, over all 43 legs | 5 s |
| `diag.py` | why the unsolved legs are unsolved | 12 s |
| `report.py` | renders the per-leg tables at the bottom of this file | — |

## Method in one paragraph

A **leg** is the stretch between two consecutive checkpoint plates, ordered by
height: 44 plates, 43 legs.  Each leg gets a **spine** — a helical polyline
interpolating radius, bearing (the short way round; every leg turns less than
96°, so this is unambiguous) and height between its two plates, sampled every
metre.  A leg's **corridor** is the columns within 9 m of that spine whose
standable surface is within 10 blocks of the spine's local height.  A
**standable** cell is a solid block with two passable cells above it.  Nothing
is sampled: every measurement enumerates the whole corridor.

## Cross-checks

1. **No-jump walkability.** `route.py` re-implements the walker independently
   (8-neighbour, step up one, fall any survivable distance) and gets **mean
   45% coverage of a leg, 0 of 43 legs walkable end to end.**  TOWER.md
   records 46% and 0 of 43 from the earlier pass.
2. **Course-band composition.** `explore.py` reproduces TOWER.md's definition
   (within five blocks of the straight checkpoint-to-checkpoint lines) and
   gets **98.3% ordinary cubes, slabs 0.8%, snow 1.1%, fences/walls 0.2%,
   stairs 0.2%** against the recorded 96.1 / 0.7 / 0.8 / 0.2 / 0.1.  The small
   gap is block classification, not geometry.
3. **Geometry.** Plate radius min/mean/max **26.2 / 44.6 / 49.1** against the
   recorded 28.5 / 44.5 / 51.7 (the earlier pass fitted a centre from the
   plate cloud; this one uses the origin, which the map is actually built on).
   44 plates, y 52 → 230.

## The shape of the thing, first

- 43 legs, **4.82 revolutions**, so **8.9 legs to a revolution** and **36.9 m
  of height per revolution**.
- A leg is **38.9 m of arc on average** (median 34.2, min 13.1, max 76.8) and
  **rises 4.1 blocks** (median 4, min 0, max 10).
- So a level is a *shallow* thing: forty metres of running for four blocks of
  climb.  Vertically, the next turn of the spiral is **37 blocks** overhead,
  not 8 — but see question 4, because the corridor still has a lid.

---

## 1. Per-leg palette — what a real level is built from

Measured over the leg's **floor** (every standable block in the corridor) and
its **skin** (the floor plus the three cells above it).  Script: `measure.py
palette`, per-leg table A.

| | min | median | mean | max |
|---|---|---|---|---|
| distinct floor materials in one leg | 7 | **14** | 15.2 | 26 |
| distinct materials in floor + 3 above | 9 | **21** | 23.8 | 43 |
| share held by the commonest material | 13% | **26%** | — | 51% |
| materials needed to cover 80% of the leg | 3 | **7** | 6.9 | 12 |

**A real level uses about fourteen floor materials, and no material owns more
than half of any level.**  The median level needs seven kinds to account for
four fifths of what you see.  Two or three materials plus an accent — the
usual generated-theme shape — is not what this map does; the closest real leg
is leg 8 (8 kinds, red sand 49%) and it is the exception.

The dominant material is a genuine theme marker, though: `sand`, `end_stone`,
`podzol`, `lava`, `white_concrete_powder`, `lime_terracotta`,
`nether_wart_block`, `snow`, `prismarine`, `black_wool`, `honeycomb_block`,
`spruce_wood`, `soul_soil`, `magma_block`, `jungle_leaves`.  The theme is one
strong material at a quarter of the level and a long tail underneath it.

---

## 2. Physics blocks — where the mechanics actually are

A block counts as **on the walking line** if it is within one cell of the
column a body occupies standing on any corridor surface (surface, feet, head).
Everything else in the leg volume is **scenery**.  Script: `measure.py
physics`, per-leg table B.

| family | cells on the line | cells anywhere | legs using it on the line |
|---|---|---|---|
| lava | 1,562 | 2,898 | **26 / 43** |
| water | 1,069 | 4,376 | **20 / 43** |
| ice (incl. packed, blue) | 557 | 1,009 | 3 / 43 |
| magma block | 442 | 546 | 10 / 43 |
| soul sand / soul soil | 355 | 1,603 | 7 / 43 |
| hay bale | 190 | 226 | 3 / 43 |
| slime block | 155 | 168 | **26 / 43** |
| vine | 84 | 425 | 7 / 43 |
| ladder | 52 | 73 | 7 / 43 |
| trapdoor | 44 | 46 | 10 / 43 |
| bed | 28 | 38 | 10 / 43 |
| sweet berry bush | 31 | 31 | 2 / 43 |
| scaffolding | 0 | 3 | 0 / 43 |
| fence gate | 1 | 1 | 1 / 43 |

Whole-map counts, for the ones that are conspicuously *absent*: **cobweb 0,
big dripleaf 0, honey block 2, scaffolding 3, blue ice 15, powder snow 25**.
Against 49,840 water, 7,512 lava, 951 packed ice, 987 vine, 553 magma, 229
hay, 189 slime, 110 soul sand, 73 ladder.

Three things worth saying plainly:

- **Only two legs (25 and 30) have no physics block on the line at all.**  The
  median leg spends **15.2% of its walking band** on or beside one; the
  distribution runs from 0% to **73.5%** (leg 39, the soul-sand and magma
  level), 63.6% (leg 38) and 60.3% (leg 9, a lava level).
- **Lava and water are the map's main mechanic, by a long way**, and they are
  mostly *hazard and floor*, not obstacle: 4,376 water cells against 1,069 on
  the line means three quarters of the water is a lake you fall into.
- **Slime is the one deliberate movement gadget, and it is rationed.**  189
  cells in the entire map, in **46 clusters, 34 of which are exactly 2×2** —
  one bounce pad, roughly one per level, in 26 of 43 legs.  Cobweb, honey,
  scaffolding and powder snow — the obvious "physics block" vocabulary — are
  effectively **not used**.

---

## 3. The real gap table

Two independent reads, because the first honest attempt was wrong and it is
worth saying how.  A naive "nearest island to nearest island" measurement
produced 522 gaps of which 60% were 2.00 m at drops of −2 to −7: those are not
jumps, they are the edge of a terrace with ground somewhere below.  **A gap is
only a gap if walking and falling cannot get you there.**

### 3a. Jumps on a solved route (primary)

`route.py` builds the move graph over standable surfaces — walk and fall free,
climb/swim free (a continuous column of ladder, vine, scaffolding or water
joins every surface beside it), jump costing `1 + (d/4)^4` — and runs Dijkstra
from the plate that opens a leg to the plate that closes it.  The cost curve
means a jump is used only where the ground runs out, and the shortest one that
works is preferred.  Jump envelope allowed to the search: `d <= 5.5 m` (6.0
descending), `dy <= +1`, arc clearance checked against a parabola with a
1.25 m apex; `dy <= +3` off a slime block; `d <= 7.5` off ice.

**26 of 43 legs solve. 122 jumps, 4.7 per leg.**

| height change | n | share | min | median | mean | p90 | max |
|---|---|---|---|---|---|---|---|
| **+3** (slime bounce) | 20 | 16.4% | 2.00 | 2.24 | 2.56 | 3.16 | 5.00 |
| +2 | 4 | 3.3% | 2.00 | 2.83 | 2.61 | 3.61 | 3.61 |
| **+1** | 35 | 28.7% | 2.00 | 3.16 | 3.14 | 4.12 | **5.10** |
| **0** | 46 | 37.7% | 2.24 | 3.16 | 3.52 | 4.24 | **4.47** |
| **−1** | 15 | 12.3% | 2.00 | 3.00 | 3.32 | 4.12 | **4.24** |
| −3 | 1 | 0.8% | 3.00 | 3.00 | 3.00 | 3.00 | 3.00 |
| −4 | 1 | 0.8% | 3.61 | 3.61 | 3.61 | 3.61 | 3.61 |
| **all** | 122 | | 2.00 | **3.16** | **3.20** | 4.12 | 5.10 |

Distances cluster hard: 2.0 m ×24, 3.0 m ×56, 3.5 m ×13, 4.0 m ×24, 4.5 m ×2,
5.0 m ×3.  **Three metres — a two-block gap — is the map's default jump**, and
half of everything is 3.0 or 3.16.

Against the project's own envelope (2.00–4.26 flat, 2.00–3.10 up one,
2.35–4.98 down one):

- **Flat**: real map 2.24–4.47, median 3.16.  Ours reaches 4.26.  Close; the
  real map's flat maximum is about 0.2 m past ours and almost nothing sits
  there.
- **Up one**: real map 2.00–**5.10**, median 3.16.  **Ours stops at 3.10.**
  This is the one clear mismatch — the reference routinely asks for a
  four-block-gap jump that gains a block, and our model cannot express it.
- **Down one**: real map 2.00–4.24, median 3.00.  Ours reaches 4.98, so we are
  *more* generous than the reference here and never need to be.
- **Down two and below**: the real map almost never jumps down more than one
  (2 of 122).  It **falls** instead — see question 7.

### 3b. Terrace-edge gaps, route-free (secondary, all 43 legs)

`gaps2.py`: stand on every corridor cell that has no walkable continuation
directly forward, and measure the shortest arc-clear landing forward within
6 m.  **2,245 edges**, median 2.00, mean 2.54, p90 4.12, max 6.00.  Level
edges (dy 0) are median 2.24 / p90 4.12; up-one edges median 2.24 / p90 4.47.
This read is noisier — it will happily pair an edge with a landing the route
never uses, which is where its 6.00 m outliers come from — but it agrees with
3a on the important part: **the modal gap is one block (2.00 m), the working
range is 2–4.5 m, and nothing legal exceeds about 5 m.**

### What is *not* measurable, and why

**17 legs cannot be solved by any walk / fall / climb / jump model I could
build, and widening the search does not help** — raising the corridor from 16
to 26 m and the height window from 18 to 26 changed the solve count by zero.
`diag.py` says the blocker is the *move set*, not the search space.  One
blocker was found and fixed and is worth recording: **the map wires iron doors
to pressure plates**, and treating a door as a wall made whole legs
unreachable; that alone was leg 42.  The rest sit at escapes of 2–4 m rising
+1 or +2 that the arc-clearance test refuses, which points at mechanics this
model does not have — head-hitting a lid to cancel a jump, half-block stair
and slab surfaces (the loader keeps names, not the `type` property, so every
slab is treated as a full block), momentum off ice, and neo/steered jumps.
**Any gap statistic here is therefore drawn from the 26 legs a simple body can
finish, and is likely to under-represent the hardest jumps in the map.**

---

## 4. Enclosure rhythm — the claim is false

The claim under test was "the reference alternates exposed and interior every
10–20 seconds".  Script: `measure.py enclosure`, per-leg table D.  Sample
points every metre along the spine, snapped to the nearest standable surface.

| | |
|---|---|
| enclosed (roof within 6 **and** walls within 4 on both sides) | **6.1%** of 1,662 metre-samples |
| legs essentially never enclosed (<2%) | **20 / 43** |
| legs enclosed more than half the way | **0 / 43** |
| enclosed runs | n=42, median **2 m**, mean 2.4, max 9 |
| open runs | n=83, median **13 m**, mean 18.8, max 63 |

**There is no alternation.**  The map is open essentially all the time, with
occasional two-metre pinches — a doorway, an overhang — and nothing that reads
as an interior stretch.

But the corridor is not open *sky*, and this is the part worth taking:

| | |
|---|---|
| ceiling above the walking surface | nothing within 40 blocks on only **2%** of samples; where there is one: min 2, p10 4, **median 8**, p90 11, max 23 |
| roof within 6 | 25% of samples |
| at least one wall within 4 | **71%** of samples |
| sideways wall distance | no wall within 24 on **33%** of sides; where there is one, median **3**, p90 7 |

So the real shape is a **groove**: a shelf with rock 3 m away on one side, open
drop on the other, and a rock lid a median 8 blocks overhead.  Almost always
half-enclosed, almost never fully enclosed, almost never truly open above.
That is a different thing from "tunnel / hall / open terrace alternating", and
it is uniform enough that a generator could just *always* build it.

---

## 5. Corridor width and radial wander

Width is the run of columns, perpendicular to travel, whose standable surface
is within one block of the sample point's.  Script: `measure.py width`,
per-leg table D.

| | min | median | mean | p90 | max |
|---|---|---|---|---|---|
| walkable width across the corridor (blocks) | 1 | **4** | 5.0 | 9 | 18 |
| radial wander **within one leg** (m) | 1.1 | **4.4** | 5.5 | — | 21.8 |

**The walkable shelf is four blocks wide at the median and is often one.**
And a level barely moves in and out: the median leg swings 4.4 m of radius
across its whole length, against a whole-map radius band of 26–49.  Two legs
are the exception — leg 38 (21.8 m) and leg 39 (17.0 m), the pair that
descends the outside of the tower.  **Radial wander is a per-level feature
used twice in 43 levels, not a continuous meander.**

---

## 6. Structures — there is no landmark per level

A structure is a 6-connected mass of solid cells sitting above the walking
surface, stopped at the **rock lid** (the first run of six solid cells above
the terrace).  The lid is load-bearing: without it the biggest "structure" on
leg 36 came out as 6,768 cells of plain stone running from y 195 to y 225 —
the tower's own body.  Script: `measure.py structures`, per-leg table D.

| | min | median | mean | max |
|---|---|---|---|---|
| biggest above-ground mass in a leg (cells) | 0 | **12** | 37 | 595 |
| its height (blocks) | 1 | **4** | — | 7 |
| masses of 20+ cells per leg | 0 | **0** | 0.7 | 7 |

**The median level has nothing standing on it bigger than twelve blocks.**
Widening the corridor to 16 m barely moves it (median 13).  The handful of
real masses are terrain features, not buildings: leg 40's 663 cells are stone,
grass and jungle leaves (a wooded knoll), leg 20's 127 are a dark-oak tree,
leg 0's 99 are a stone-and-dripstone outcrop, leg 38's 80-cell mass, 9x4x7,
is about the biggest genuinely *built* thing the measurement finds.

This is the finding most likely to change how somebody builds a level: **the
reference does not put one big readable landmark on each level.**  A level's
identity comes from its floor palette and the shape of its ground, and the
things standing on it are small — a tree, an outcrop, a couple of blocks of
furniture.

---

## 7. Vertical travel inside a leg

Two reads.  `measure.py vertical` walks the spine-snapped ground profile;
`route.py` sums the solved route.  Script: per-leg table C.

| along the ground profile | min | median | mean | max |
|---|---|---|---|---|
| net rise | 0 | **4** | 4.1 | 10 |
| total travel (up + down) | — | **11** | 11.9 | 31 |
| descent | — | **4** | 3.9 | 14 |

- ratio of travel to net rise: **3.36**
- **legs whose walking surface goes down at all: 36 / 43**
- **legs that dip below their own starting checkpoint: 22 / 43**

On the solved routes: climbed median 6 / mean 7.8, descended median 3 /
mean 3.9, net median 3.  **23 of 26 solved legs descend somewhere.**

**A real level does not only go up.**  It climbs about eleven blocks to gain
four, and half of all levels drop below the height they started at before
they finish.  Combined with question 3 — the map almost never *jumps* down
more than one block — the picture is that descent happens by **falling**: you
walk or drop off an edge onto something lower, and that is free.

### A. Per-leg palette (question 1)

| leg | y | floor kinds | kinds for 80% | dominant floor+3 material | its share | top five |
|---|---|---|---|---|---|---|
| 0 | 52-59 | 9 | 3 | sand | 44% | sand 287, water 171, grass_block 95, lily_pad 13, flowering_azalea_leaves 13 |
| 1 | 59-69 | 24 | 10 | grass_block | 19% | grass_block 217, smooth_stone 135, lava 123, water 83, sand 82 |
| 2 | 69-73 | 19 | 7 | black_concrete | 23% | black_concrete 143, end_stone 142, wheat 80, stone 70, grass_block 40 |
| 3 | 73-77 | 17 | 7 | podzol | 24% | podzol 94, spruce_slab 52, gravel 41, red_sand 40, dirt 35 |
| 4 | 77-79 | 12 | 5 | red_sand | 41% | red_sand 132, water 42, acacia_planks 36, light_gray_terracotta 36, terracotta 24 |
| 5 | 79-80 | 12 | 6 | stone | 30% | stone 81, gravel 74, grass_block 26, rail 17, warped_nylium 17 |
| 6 | 80-85 | 21 | 9 | lava | 16% | lava 136, netherrack 128, grass_block 104, hay_block 100, warped_nylium 76 |
| 7 | 85-90 | 12 | 6 | stone | 41% | stone 207, sand 82, lava 48, rail 33, acacia_slab 22 |
| 8 | 90-95 | 8 | 3 | red_sand | 49% | red_sand 218, lava 97, yellow_concrete_powder 50, bamboo 33, crimson_nylium 11 |
| 9 | 95-95 | 11 | 5 | lava | 28% | lava 97, magma_block 82, grass_block 44, crimson_nylium 41, netherrack 26 |
| 10 | 95-99 | 12 | 8 | lava | 19% | lava 63, crimson_nylium 46, magma_block 38, red_sand 34, stone 29 |
| 11 | 99-101 | 15 | 8 | red_sand | 25% | red_sand 78, oak_planks 44, oak_wood 36, red_sandstone 26, lava 26 |
| 12 | 101-106 | 21 | 9 | white_concrete_powder | 36% | white_concrete_powder 192, yellow_terracotta 33, sand 32, birch_fence 30, birch_wood 30 |
| 13 | 106-109 | 12 | 6 | grass_block | 18% | grass_block 75, lime_terracotta 68, dirt 59, lava 58, dirt_path 49 |
| 14 | 109-117 | 22 | 8 | light_blue_terracotta | 17% | light_blue_terracotta 153, lime_terracotta 150, grass_block 109, dirt 86, water 86 |
| 15 | 117-120 | 11 | 4 | dark_oak_planks | 37% | dark_oak_planks 105, spruce_slab 76, nether_wart_block 43, weeping_vines 8, lava 8 |
| 16 | 120-122 | 13 | 5 | nether_wart_block | 45% | nether_wart_block 132, nether_wart 36, red_nether_bricks 30, red_terracotta 28, sand 16 |
| 17 | 122-127 | 19 | 9 | snow | 22% | snow 175, snow_block 159, fire_coral_block 53, water 49, sand 49 |
| 18 | 127-132 | 11 | 6 | gold_block | 20% | gold_block 146, lava 131, stone 124, dirt 122, gold_ore 50 |
| 19 | 132-135 | 10 | 4 | red_sandstone | 35% | red_sandstone 136, lava 127, red_sandstone_slab 32, grass_block 27, stone 21 |
| 20 | 135-138 | 18 | 8 | grass_block | 31% | grass_block 157, dark_oak_leaves 115, dirt_path 36, dirt 24, water 24 |
| 21 | 138-144 | 7 | 3 | snow | 35% | snow 304, snow_block 301, packed_ice 148, ice 70, spruce_leaves 21 |
| 22 | 144-146 | 15 | 7 | snow | 21% | snow 127, snow_block 92, grass_block 85, carrots 65, packed_ice 45 |
| 23 | 146-150 | 22 | 10 | netherrack | 23% | netherrack 146, lava 120, grass_block 76, prismarine 32, dirt_path 27 |
| 24 | 150-151 | 12 | 6 | prismarine | 26% | prismarine 95, wet_sponge 81, water 39, quartz_block 38, grass_block 27 |
| 25 | 151-154 | 11 | 6 | grass_block | 27% | grass_block 61, beetroots 34, stone 29, red_mushroom_block 27, sand 24 |
| 26 | 154-159 | 11 | 6 | sand | 47% | sand 112, cut_sandstone_slab 23, red_sand 18, grass_block 17, lava 16 |
| 27 | 159-162 | 20 | 9 | red_sand | 23% | red_sand 163, pink_terracotta 70, black_concrete 70, mycelium 64, lava 60 |
| 28 | 162-163 | 11 | 7 | yellow_terracotta | 19% | yellow_terracotta 40, grass_block 38, end_stone 30, smooth_stone_slab 28, gravel 15 |
| 29 | 163-171 | 24 | 11 | grass_block | 22% | grass_block 165, podzol 91, red_sand 63, oak_leaves 58, sand 52 |
| 30 | 171-178 | 10 | 5 | end_stone | 39% | end_stone 70, bubble_coral_block 32, magenta_terracotta 25, purpur_slab 14, stone 11 |
| 31 | 178-183 | 26 | 12 | grass_block | 22% | grass_block 225, stone 188, stone_slab 73, dirt_path 63, end_stone 62 |
| 32 | 183-188 | 15 | 3 | black_wool | 46% | black_wool 209, lime_terracotta 157, brown_terracotta 16, magenta_concrete_powder 15, white_terracotta 12 |
| 33 | 188-190 | 13 | 7 | red_concrete_powder | 17% | red_concrete_powder 46, lime_concrete_powder 45, yellow_concrete_powder 44, honeycomb_block 27, pink_concrete_powder 21 |
| 34 | 190-192 | 19 | 11 | honeycomb_block | 25% | honeycomb_block 116, lava 60, grass_block 45, bamboo_mosaic 39, gravel 31 |
| 35 | 192-195 | 14 | 6 | netherrack | 35% | netherrack 103, red_nether_bricks 48, lava 28, dark_prismarine 27, wither_rose 18 |
| 36 | 195-201 | 21 | 10 | spruce_wood | 22% | spruce_wood 173, sea_lantern 100, water 100, dark_prismarine 62, prismarine_bricks 51 |
| 37 | 201-206 | 15 | 5 | red_sand | 51% | red_sand 312, water 68, terracotta 56, lava 34, gravel 18 |
| 38 | 206-207 | 17 | 9 | soul_soil | 29% | soul_soil 148, grass_block 116, acacia_leaves 45, cobblestone_slab 38, dirt_path 28 |
| 39 | 207-213 | 9 | 6 | nether_wart | 20% | nether_wart 25, magma_block 21, lava 21, nether_brick_stairs 19, netherrack 13 |
| 40 | 213-218 | 21 | 12 | yellow_terracotta | 13% | yellow_terracotta 91, magma_block 82, terracotta 55, lava 55, red_terracotta 55 |
| 41 | 218-224 | 22 | 7 | sand | 34% | sand 268, grass_block 197, jungle_slab 52, water 43, dirt 34 |
| 42 | 224-230 | 8 | 4 | jungle_leaves | 31% | jungle_leaves 151, sand 115, water 83, grass_block 55, gravel 31 |

### B. Per-leg physics blocks (question 2)

| leg | y | band cells | on the line | share of band | families on the line | families as scenery |
|---|---|---|---|---|---|---|
| 0 | 52-59 | 646 | 226 | 35.0% | water 224, vine 2 | water 263, lava 32, vine 10 |
| 1 | 59-69 | 1120 | 231 | 20.6% | lava 143, water 84, slime 4 | water 972, lava 136 |
| 2 | 69-73 | 626 | 55 | 8.8% | hay 28, water 17, trapdoor 8, berry_bush 2 | water 25, hay 8, lava 3 |
| 3 | 73-77 | 385 | 71 | 18.4% | water 35, berry_bush 29, slime 7 | - |
| 4 | 77-79 | 318 | 47 | 14.8% | water 42, slime 4, ladder 1 | ladder 1 |
| 5 | 79-80 | 267 | 4 | 1.5% | trapdoor 4 | - |
| 6 | 80-85 | 840 | 336 | 40.0% | lava 136, hay 135, magma 36, vine 21, slime 8 | lava 155, magma 13, hay 8, vine 3 |
| 7 | 85-90 | 500 | 46 | 9.2% | lava 46 | water 43, vine 19 |
| 8 | 90-95 | 431 | 110 | 25.5% | lava 106, slime 4 | lava 2 |
| 9 | 95-95 | 325 | 196 | 60.3% | magma 100, lava 94, bed 2 | lava 13, magma 1 |
| 10 | 95-99 | 320 | 118 | 36.9% | lava 68, magma 50 | lava 39 |
| 11 | 99-101 | 307 | 33 | 10.7% | lava 29, slime 4 | lava 51, bed 2 |
| 12 | 101-106 | 521 | 26 | 5.0% | lava 11, ladder 8, trapdoor 7 | hay 20, ladder 5, lava 2 |
| 13 | 106-109 | 414 | 62 | 15.0% | lava 58, slime 4 | ice 1 |
| 14 | 109-117 | 905 | 123 | 13.6% | water 89, lava 29, slime 4, soul_sand 1 | lava 46, water 19 |
| 15 | 117-120 | 273 | 56 | 20.5% | lava 26, magma 13, vine 8, soul_sand 5, slime 4 | lava 189, vine 2 |
| 16 | 120-122 | 291 | 44 | 15.1% | soul_sand 30, vine 7, slime 5, magma 2 | vine 33, soul_sand 14 |
| 17 | 122-127 | 793 | 126 | 15.9% | ice 66, water 51, slime 9 | ice 26, slime 5 |
| 18 | 127-132 | 725 | 161 | 22.2% | lava 132, ladder 28, slime 1 | ladder 4 |
| 19 | 132-135 | 393 | 185 | 47.1% | lava 129, magma 54, slime 2 | magma 17, lava 4 |
| 20 | 135-138 | 500 | 51 | 10.2% | water 24, lava 19, slime 4, bed 2, ladder 2 | lava 44, ladder 8 |
| 21 | 138-144 | 868 | 443 | 51.0% | ice 443 | ice 425 |
| 22 | 144-146 | 582 | 64 | 11.0% | ice 48, slime 10, bed 4, soul_sand 1, trapdoor 1 | trapdoor 2, water 2, soul_sand 1 |
| 23 | 146-150 | 620 | 195 | 31.5% | lava 130, hay 27, soul_sand 26, slime 8, water 4 | water 33, soul_sand 10, bed 4, scaffolding 3 |
| 24 | 150-151 | 364 | 47 | 12.9% | water 39, slime 8 | - |
| 25 | 151-154 | 228 | 0 | 0.0% | - | slime 1 |
| 26 | 154-159 | 234 | 16 | 6.8% | lava 16 | slime 7 |
| 27 | 159-162 | 675 | 122 | 18.1% | lava 60, water 47, ladder 7, bed 4, slime 4 | lava 71, bed 2, ladder 2 |
| 28 | 162-163 | 198 | 6 | 3.0% | bed 3, ladder 2, trapdoor 1 | water 2, ladder 1, bed 1 |
| 29 | 163-171 | 736 | 65 | 8.8% | lava 38, water 10, vine 7, ladder 4, slime 4, trapdoor 1, bed 1 | lava 69, water 4, bed 1 |
| 30 | 171-178 | 174 | 0 | 0.0% | - | - |
| 31 | 178-183 | 1009 | 103 | 10.2% | lava 55, water 30, slime 9, bed 4, trapdoor 4, fence_gate 1 | soul_sand 310, lava 35, water 7 |
| 32 | 183-188 | 457 | 8 | 1.8% | slime 8 | soul_sand 214, lava 22, water 13 |
| 33 | 188-190 | 262 | 8 | 3.1% | slime 4, water 4 | water 18 |
| 34 | 190-192 | 462 | 88 | 19.0% | lava 66, water 10, trapdoor 8, bed 4 | lava 27 |
| 35 | 192-195 | 291 | 49 | 16.8% | lava 28, magma 21 | lava 1 |
| 36 | 195-201 | 787 | 120 | 15.2% | water 105, slime 12, trapdoor 3 | lava 5 |
| 37 | 201-206 | 602 | 128 | 21.3% | water 71, lava 42, slime 8, trapdoor 7 | water 351, lava 16, vine 5 |
| 38 | 206-207 | 492 | 313 | 63.6% | soul_sand 274, magma 21, water 12, lava 4, bed 2 | soul_sand 682, water 333, lava 21, magma 14, vine 14 |
| 39 | 207-213 | 117 | 86 | 73.5% | magma 46, lava 22, soul_sand 18 | water 516, magma 55, soul_sand 16, lava 3 |
| 40 | 213-218 | 680 | 165 | 24.3% | magma 99, lava 59, slime 7 | water 404, magma 4, soul_sand 1 |
| 41 | 218-224 | 786 | 84 | 10.7% | water 56, lava 16, slime 9, bed 2, vine 1 | vine 155, water 111, lava 78 |
| 42 | 224-230 | 492 | 153 | 31.1% | water 115, vine 38 | lava 272, water 191, vine 100 |

### C. Per-leg route, gaps and vertical travel (questions 3, 7)

| leg | y | solved | jumps on route | median | max | climbed | descended | net | walk-only coverage | surface profile up+down |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 52-59 | no | 0 | - | - |  |  |  | 40% | 7+0 |
| 1 | 59-69 | yes | 13 | 3.00 | 4.12 | 19 | 9 | 10 | 25% | 17+7 |
| 2 | 69-73 | no | 0 | - | - |  |  |  | 54% | 12+8 |
| 3 | 73-77 | yes | 10 | 3.16 | 4.24 | 7 | 3 | 4 | 76% | 8+4 |
| 4 | 77-79 | no | 0 | - | - |  |  |  | 73% | 6+4 |
| 5 | 79-80 | yes | 4 | 4.12 | 4.24 | 3 | 2 | 1 | 44% | 1+0 |
| 6 | 80-85 | yes | 4 | 3.16 | 4.00 | 13 | 8 | 5 | 32% | 10+5 |
| 7 | 85-90 | yes | 8 | 3.16 | 4.12 | 5 | 0 | 5 | 64% | 7+2 |
| 8 | 90-95 | no | 0 | - | - |  |  |  | 77% | 7+2 |
| 9 | 95-95 | yes | 4 | 4.12 | 5.00 | 3 | 3 | 0 | 60% | 3+3 |
| 10 | 95-99 | yes | 3 | 3.00 | 3.61 | 13 | 9 | 4 | 86% | 12+8 |
| 11 | 99-101 | no | 0 | - | - |  |  |  | 3% | 8+6 |
| 12 | 101-106 | yes | 9 | 3.00 | 4.12 | 13 | 8 | 5 | 31% | 11+6 |
| 13 | 106-109 | yes | 1 | 2.83 | 2.83 | 4 | 1 | 3 | 79% | 4+1 |
| 14 | 109-117 | no | 0 | - | - |  |  |  | 30% | 11+3 |
| 15 | 117-120 | yes | 1 | 5.00 | 5.00 | 3 | 0 | 3 | 74% | 3+0 |
| 16 | 120-122 | yes | 3 | 4.24 | 4.24 | 5 | 3 | 2 | 11% | 5+3 |
| 17 | 122-127 | no | 0 | - | - |  |  |  | 27% | 11+6 |
| 18 | 127-132 | yes | 5 | 3.00 | 4.24 | 8 | 3 | 5 | 22% | 9+4 |
| 19 | 132-135 | yes | 3 | 3.61 | 3.61 | 3 | 0 | 3 | 65% | 4+1 |
| 20 | 135-138 | yes | 1 | 2.83 | 2.83 | 4 | 1 | 3 | 85% | 7+4 |
| 21 | 138-144 | no | 0 | - | - |  |  |  | 51% | 13+7 |
| 22 | 144-146 | yes | 1 | 2.00 | 2.00 | 6 | 4 | 2 | 85% | 8+6 |
| 23 | 146-150 | yes | 5 | 2.00 | 3.16 | 9 | 5 | 4 | 48% | 9+5 |
| 24 | 150-151 | yes | 1 | 2.83 | 2.83 | 5 | 4 | 1 | 71% | 3+2 |
| 25 | 151-154 | yes | 2 | 3.16 | 4.00 | 7 | 4 | 3 | 68% | 3+0 |
| 26 | 154-159 | no | 0 | - | - |  |  |  | 36% | 6+1 |
| 27 | 159-162 | no | 0 | - | - |  |  |  | 22% | 17+14 |
| 28 | 162-163 | no | 0 | - | - |  |  |  | 11% | 2+1 |
| 29 | 163-171 | yes | 8 | 3.16 | 4.12 | 19 | 11 | 8 | 36% | 9+1 |
| 30 | 171-178 | no | 0 | - | - |  |  |  | 59% | 7+0 |
| 31 | 178-183 | no | 0 | - | - |  |  |  | 53% | 15+10 |
| 32 | 183-188 | yes | 4 | 3.16 | 4.12 | 7 | 2 | 5 | 29% | 9+4 |
| 33 | 188-190 | yes | 3 | 4.12 | 4.24 | 3 | 1 | 2 | 6% | 5+3 |
| 34 | 190-192 | yes | 3 | 4.00 | 5.10 | 3 | 1 | 2 | 20% | 4+2 |
| 35 | 192-195 | yes | 6 | 2.83 | 4.47 | 5 | 2 | 3 | 73% | 3+0 |
| 36 | 195-201 | yes | 7 | 2.83 | 4.47 | 12 | 6 | 6 | 32% | 12+6 |
| 37 | 201-206 | yes | 9 | 3.00 | 4.12 | 14 | 9 | 5 | 11% | 9+4 |
| 38 | 206-207 | no | 0 | - | - |  |  |  | 28% | 6+5 |
| 39 | 207-213 | no | 0 | - | - |  |  |  | 39% | 13+7 |
| 40 | 213-218 | no | 0 | - | - |  |  |  | 23% | 6+1 |
| 41 | 218-224 | yes | 4 | 4.00 | 4.00 | 9 | 3 | 6 | 25% | 17+11 |
| 42 | 224-230 | no | 0 | - | - |  |  |  | 55% | 6+0 |

### D. Per-leg enclosure, corridor width, radial wander, structures (questions 4, 5, 6)

| leg | y | enclosed | width min/med/max | radius min-max | wander | masses >=20 cells | biggest mass | its bbox (x,y,z) |
|---|---|---|---|---|---|---|---|---|
| 0 | 52-59 | 0% | 1/10/18 | 42.8-49.5 | 6.7 | 1 | 99 | [7, 5, 7] |
| 1 | 59-69 | 8% | 1/6/12 | 41.3-48.6 | 7.3 | 2 | 67 | [11, 7, 7] |
| 2 | 69-73 | 2% | 1/7/9 | 44.5-48.7 | 4.2 | 0 | 19 | [3, 4, 4] |
| 3 | 73-77 | 9% | 1/3/11 | 42.1-47.3 | 5.2 | 0 | 18 | [4, 5, 3] |
| 4 | 77-79 | 0% | 1/2/10 | 42.1-48.7 | 6.6 | 0 | 3 | [2, 2, 1] |
| 5 | 79-80 | 0% | 1/2/11 | 48.1-49.6 | 1.5 | 0 | 1 | [1, 1, 1] |
| 6 | 80-85 | 11% | 1/8/10 | 45.3-49.7 | 4.4 | 1 | 51 | [5, 5, 5] |
| 7 | 85-90 | 0% | 1/3/9 | 40.5-46.3 | 5.8 | 0 | 6 | [2, 3, 2] |
| 8 | 90-95 | 8% | 1/5/14 | 39.8-49.0 | 9.2 | 1 | 55 | [7, 6, 6] |
| 9 | 95-95 | 9% | 1/3/5 | 46.5-48.9 | 2.4 | 0 | 0 | None |
| 10 | 95-99 | 15% | 1/2/5 | 41.7-46.4 | 4.6 | 0 | 4 | [1, 4, 1] |
| 11 | 99-101 | 6% | 1/4/11 | 38.6-48.2 | 9.6 | 0 | 0 | None |
| 12 | 101-106 | 8% | 1/5/12 | 45.5-49.6 | 4.1 | 0 | 11 | [2, 4, 5] |
| 13 | 106-109 | 0% | 2/6/11 | 44.3-47.5 | 3.2 | 0 | 11 | [4, 4, 2] |
| 14 | 109-117 | 0% | 1/3/11 | 42.8-46.8 | 4.0 | 1 | 50 | [6, 4, 5] |
| 15 | 117-120 | 0% | 4/8/12 | 43.2-45.3 | 2.1 | 0 | 2 | [1, 2, 1] |
| 16 | 120-122 | 19% | 1/6/10 | 43.7-46.1 | 2.4 | 0 | 13 | [2, 5, 2] |
| 17 | 122-127 | 5% | 1/4/9 | 44.1-47.5 | 3.5 | 0 | 12 | [3, 5, 2] |
| 18 | 127-132 | 0% | 1/3/11 | 42.4-45.1 | 2.7 | 1 | 30 | [3, 4, 5] |
| 19 | 132-135 | 0% | 1/3/9 | 42.2-44.6 | 2.4 | 0 | 11 | [3, 4, 2] |
| 20 | 135-138 | 9% | 1/8/10 | 44.1-49.4 | 5.3 | 2 | 127 | [9, 5, 10] |
| 21 | 138-144 | 2% | 1/5/14 | 44.0-49.1 | 5.2 | 0 | 4 | [1, 4, 1] |
| 22 | 144-146 | 0% | 1/8/10 | 41.5-44.6 | 3.0 | 0 | 1 | [1, 1, 1] |
| 23 | 146-150 | 6% | 2/3/11 | 40.7-43.1 | 2.4 | 0 | 5 | [2, 3, 1] |
| 24 | 150-151 | 0% | 2/6/10 | 40.8-41.9 | 1.1 | 0 | 18 | [3, 3, 3] |
| 25 | 151-154 | 0% | 1/7/17 | 41.6-48.5 | 6.9 | 0 | 6 | [3, 1, 4] |
| 26 | 154-159 | 0% | 3/4/13 | 45.3-49.5 | 4.2 | 0 | 9 | [1, 3, 3] |
| 27 | 159-162 | 18% | 1/5/11 | 32.4-45.2 | 12.9 | 0 | 17 | [6, 2, 4] |
| 28 | 162-163 | 23% | 1/3/6 | 33.8-47.2 | 13.4 | 0 | 14 | [5, 2, 4] |
| 29 | 163-171 | 10% | 1/5/10 | 47.1-49.9 | 2.8 | 4 | 61 | [5, 5, 5] |
| 30 | 171-178 | 0% | 2/3/10 | 41.9-48.1 | 6.3 | 0 | 3 | [1, 3, 1] |
| 31 | 178-183 | 11% | 1/3/10 | 40.2-45.8 | 5.6 | 0 | 11 | [2, 5, 2] |
| 32 | 183-188 | 0% | 1/3/10 | 43.8-48.3 | 4.4 | 0 | 0 | None |
| 33 | 188-190 | 0% | 2/4/9 | 45.6-48.6 | 3.0 | 0 | 1 | [1, 1, 1] |
| 34 | 190-192 | 15% | 1/5/14 | 42.7-46.8 | 4.1 | 0 | 6 | [2, 4, 1] |
| 35 | 192-195 | 0% | 3/9/12 | 43.3-47.3 | 3.9 | 1 | 25 | [4, 4, 4] |
| 36 | 195-201 | 5% | 1/4/10 | 45.3-49.6 | 4.4 | 1 | 33 | [4, 4, 8] |
| 37 | 201-206 | 4% | 1/3/11 | 47.4-49.5 | 2.1 | 1 | 50 | [4, 7, 6] |
| 38 | 206-207 | 11% | 1/3/11 | 25.5-47.3 | 21.8 | 1 | 80 | [9, 4, 7] |
| 39 | 207-213 | 19% | 1/2/4 | 27.0-44.0 | 17.0 | 0 | 1 | [1, 1, 1] |
| 40 | 213-218 | 0% | 1/5/10 | 43.5-48.6 | 5.1 | 5 | 595 | [17, 7, 21] |
| 41 | 218-224 | 0% | 1/6/9 | 44.8-49.1 | 4.2 | 0 | 16 | [4, 4, 5] |
| 42 | 224-230 | 7% | 1/2/11 | 39.6-44.6 | 5.0 | 7 | 54 | [8, 3, 5] |
