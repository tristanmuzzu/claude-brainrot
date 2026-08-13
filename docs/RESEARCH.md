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

**Used, 2026-08-13.** `spiralplan.FLOOR_MIX` gives every theme a weighted tail
of eight to eleven materials underneath its four roles, and `Theme.floor_style`
picks one per cell — patchy at three cells with a fifth of cells re-rolling on
their own, salted by the level's name, a pure function of the cell so
re-emitting a layer draws the same floor. Measured over 29 level-visits on the
terrace itself, palette off against palette on in one process:

| a level's walking surface | before | after | real map |
|---|---|---|---|
| materials holding ≥1% | **3** | **10** | 14 |
| share held by the commonest | **69%** | **45%** | 26% |

Two notes for whoever reads this next. The commonest is still 45% because a
good deal of the terrace is not painted by `_slab` at all — course pedestals,
landings and dressing go through `write()` and each use a single role — so
closing the rest of that gap is a change to those, not to the palette. And the
first version of this measurement was wrong in a way worth remembering: it
counted `Course.struct`, which is terrain the *course* wrote, and the cone's
terrace is emitted through `_draw_only` and deliberately never enters it. The
floor was not in the number that was supposed to be about the floor.

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

### The one-sided question was the wrong question (2026-08-13)

*"A wall within 4 m on **at least one** side"* cannot tell a shelf cut into
the outside of a tower from a groove with rock on both sides, and those are
completely different places to stand. Our tower satisfied it at 73% against
the real map's 71% and looked nothing like it. `tools/mapdig/enclosure.py`
asks the two-sided question against the save — it reproduces the 71% row as
72.4%, which is what says the two measurements are the same measurement:

| along the route | real map | ours, before | ours, after |
|---|---|---|---|
| rock within 4 m on **both** sides | **22.6%** | **3.9%** | **20.5%** |
| inward (the core) only | 39.0% | **71.3%** | 55.5% |
| **outward only** | **11.0%** | 1.8% | 9.3% |
| **rock outboard at all** | **33.6%** | **5.6%** | **29.8%** |
| a canyon: both sides *and* a lid within 12 | **22.2%** | **3.3%** | 16.7% |

The "after" column is `Cone.buttress_*`, added 2026-08-13: an outer wall on the
drop side, present on stretches and absent on stretches, closed form like
everything else about the building. Cost: unchecked placements 0.16% → 0.27%,
designed content 46% → 44%, and frame cost went *down* (2.65 → 2.40 ms, ratio
to parkour 1.17) because a wall occludes the world behind it. Walkability held
at 0 m, twice-claimed cells at 0, 628 tests green.

**A third of the real route has rock on its outboard shoulder. Ours has the
drop there essentially always.** That is the measured form of "it feels like a
thin layer wrapped around one big undifferentiated tower": our body always has
the core on one side and nothing whatever on the other, so every frame is
composed identically — cliff down one edge, sky down the other — and no amount
of level design changes it, because it is the building.

Note what it does *not* say. The real map is not a canyon most of the time
either; 39% of it is the one-sided shelf we build everywhere. The difference
is that it has a second wall a fifth of the time and an outboard-only wall a
tenth, so the composition keeps changing. Variety of enclosure, not more of
it.

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

## 8. What the frames say — and first, whose frames they are

**Two of the three reference videos are not Parkour Spiral.** `ps1_shaders` and
`ps3_shaders` are the same map, **Parkour Volcano** — both open on the same
garden and the same painted "Parkour Volcano" title board. Only the speedrun is
a different map. Same author, same cone-spiral genre, so the design
observations transfer, but **`docs/TOWER.md` § "What the reference actually
does" is sourced from Volcano and says Parkour Spiral**, and that is the
provenance of everything in it.

This also explains the two places where §§1–7 above and this section disagree:
**§§1–7 are the Parkour Spiral world save, this section is Parkour Volcano
footage.** They are different maps and the differences are real, not error.
Where they conflict, the save is authoritative for Spiral and a block census
beats frame-reading. Full report: `docs/reference/FRAME_FINDINGS.md`.

| | Spiral (save) | Volcano (footage) |
|---|---|---|
| fully enclosed | 6.1% of the way, runs of 2 m | 20.8% of seconds, 17 runs ≥ 3 s, mean 5.6 s |
| slime | 189 cells, 46 pads, **26 / 43 levels** | **none seen in ~2,900 s** |
| level length | — | **10–15 s**, mean 12 |

A 2×2 pad is easy to miss at three-second sampling, so the slime rows are
consistent with each other; the enclosure rows are a genuine difference between
two maps.

### The frame is a slot, and the overhang makes it one

Measured over 325 frames of Volcano at 1 s:

| | |
|---|---|
| the top fifth of the screen, share of its pixels that are dark rock | **63%** on average |
| frames whose top fifth is more than half dark rock | **73%** |
| seconds with more than 10% open sky or sea | 66.6% |
| seconds with more than 20% | 53.1% |
| seconds showing **no sky at all** | 20.8% |
| luminance standard deviation across the frame | mean **65.8** |

**The overhang deletes every wrong answer above you.** You are in a slot: the
roof is the underside of the level above, the floor is the lightest thing in
the lower half, the cliff is the darkest thing in the upper, and the only
bright exit is forward. Sky is present in two thirds of seconds — but as a
band, not as the subject.

### How a level opens

- **An emissive block flush in the floor, on a rise, on screen 2.3 s before you
  reach it.** One block, level with the ground, emitting light — it reads at
  distance and at speed and never looks like scenery.
- **The material changes completely at that block**, in one or two frames.
  Nine seams in 120 s, every one abrupt. No two adjacent levels share a
  dominant hue.
- **The exit is not signposted.** The corridor narrows to a tongue that ends in
  air, or to a lit doorway. The design tells you where a level *starts* and
  lets the geometry tell you where it ends.

### How you are told where to go — four devices, all cheap

1. **The route is paved.** A stripe of a different floor material down the
   middle of every terrace wide enough to be ambiguous: a dirt path across
   grass, gravel through a garden, a red carpet runner down a stone hall.
2. **Every lamp is at the far end.** Lanterns hang at a corridor's exit, not
   spread through it; a lamp post stands at the tip of a promontory where the
   course turns. **There is no ambient decorative lighting anywhere — every
   light in these frames is doing a job.**
3. **A landmark stands where the course turns**, on the last block of the
   ledge, not in the middle of the terrace.
4. **Silhouettes against sky are legible; anything against the cliff is not.**

### Why you cannot walk it — width and hazard, not gaps

The reference does **not** break a continuous ledge with chasms.

1. The walking surface is **2–4 blocks wide with the drop directly outboard**,
   so there is nothing to walk around.
2. **Where the ground is wide, its whole width is hazard.** A lava lake
   spanning the terrace with one lit block in it; a room whose entire floor is
   lava, crossed on a staircase of oak stairs; a stretch where the floor is the
   *sea* and the landings are lily pads. The landings are isolated single
   blocks with two or three blocks of hazard between them — not a five-block
   chasm.
3. Interiors are corridors of two to three blocks, where bypass is not a
   question.

And the nuance that matters: **the rule is "no level walkable end to end", not
"no metre walkable".** At its widest the ground stops being a course and
becomes a *place* — a village terrace with fences and a trough, a garden — and
the map lets you walk that for a few seconds, because the level's entrance and
exit are still separated by a real break somewhere else.

### Structures

Six read closely. Two habits worth copying:

- **A structure is either a corridor you are inside or a silhouette you run at
  the foot of.** Nothing in the footage is a solid mass parked beside the
  course.
- **The big interiors are always the level's height gain.** A lava hall
  climbing on oak stairs, a six-second ladder shaft, a cantilevered white
  structure whose steps *are* the landings. The structure and the climb are one
  decision.

### The obstacle vocabulary, seen

Staples: plain gaps level or ±1; **stairs and slabs as the walking surface —
the commonest non-cube form by a wide margin**; fences as edging and scenery
(never unambiguously a landing); hazard floors of lava then water; doorways and
lintels you run under.

Once or twice a level: one-block landings in a hazard field; **ladders**, both
as short wall climbs and as a whole level's climb; ice as one level's terrain.

**The negative result, and it is load-bearing for this project.** Across ~2,900
seconds: **no slime, no honey, no soul sand, no magma bounce, no bubble column,
and no cobweb used as a movement surface.** The only physics-altering block
present is ice, as one level's ground. An engine that can express those and
uses almost none of them is **matching** the reference, not falling short. The
one special block to lean on is the **ladder**.

### Pacing

A level is **10–15 s**, mean 12 over ten consecutive sections. Read end to end
at 4 fps, one level ran 16.3 s: 2.5 s of approach and arrival, ~11 s of the
level's own terrain, 2–3 s of descent into the next interior. **The hardest
moment sat at about 60% of the way through**, not at the end.

Altitude changes the backdrop: below halfway the drop reads as sea and beach,
above it as a flat white cloud deck. That one change makes the top of the map
feel higher with no geometry change at all.

### The move vocabulary, named correctly

From a bounded check of community sources: **2bc and head-hitter are the same
move** — a jump under a ceiling low enough to strike your head, cutting the
rise. A **neo** is jumping off a block's edge and landing back against the face
of the pillar you left; a **neup** targets one block higher. A **ladder jump**
uses height gained off a ladder to clear a gap. **Momentum/FMM** is sprinting
in mid-air out of a confined space to widen a one-tick window. Notation: `3b
+1` is a three-block jump one block up.

**Where the sources and the frames disagree, the frames win, and they do.** The
community lists are written for *technical* parkour servers — neos, momentum,
one-tick windows. There is no frame in 2,900 s where the player does anything
needing a named technique. **This genre is adventure parkour, not technical
parkour**, and the vocabulary that matters for building it is architectural:
corridor, shaft, hazard floor, ledge, threshold.

---

## What this changes

| the tower believed | measured | so |
|---|---|---|
| three to five materials per level | **14 floor materials, dominant 26%** | palette is the identity lever, and it has never been used |
| alternate interior and exposed every 10–20 s | **6% enclosed, runs of 2 m** | build the groove: wall one side, drop the other, lid overhead. Interiors are pinches |
| one big landmark per level | **median biggest mass 12 cells** | keep ours, but the floor does the work and small furniture is everywhere |
| the course should wander radially | **4.4 m within a level** | wandering is a feature for one or two levels, not a default |
| levels climb | **36/43 descend, 22 dip below their start** | a level goes down as well as up, by falling |
| exotic physics blocks are the variety | **cobweb 0, honey 2, scaffolding 3**, and none seen in 2,900 s of footage | lava and water are the mechanic; slime is one pad; the special block to lean on is the **ladder** |
| difficulty is the top of the envelope | **modal jump 3.0 m, 4.7 jumps a level** | write 3.0–3.5 m and save the envelope's top for a showpiece |
| the frames are Parkour Spiral | **two of the three videos are Parkour Volcano** | relabel the provenance; the save is the authority for Spiral |
| unwalkability comes from breaking the floor | **width plus hazard**; where it widens, the whole width is lava or water with one block in it | breaks are one tool, not the tool |
| nothing says where a level begins | **an emissive block flush in the floor, on a rise, 2.3 s early, and the palette changes completely at it** | levels need a threshold |
| the route is obvious | **it is painted** — a stripe of another floor material down the middle of any wide ground | free legibility we have never used |
| light is decoration | **every lamp is at the far end of a room; there is no ambient decorative lighting anywhere** | light is a wayfinding device |

## 10. What the footage measures as, once the control is right (2026-08-13)

The frame comparisons this project has made were all against `ps1` and `ps3`,
and both of those run a shader pack (see `reference/README.md`, where the
provenance is now written down from the video titles rather than assumed).
Comparing flat baked light against a shader pack tells you about the shader
pack. `frames/vanilla_2hz/` is the fix: 125 frames of the vanilla speedrun at
2.22 fps, which is the **same 0.45 s spacing** a `brainrot shoot --every 27`
produces, so a frame-to-frame figure is finally comparable.

`tools/frame_probe.py`, 100 frames of the hand-built tower against 125 vanilla
and 125 shader:

| | ours | vanilla | shaders |
|---|---|---|---|
| **frame-to-frame change** | **9.8%** | **20.3%** | 29.4% |
| ...stillest tenth of frames | **5.3%** | 10.6% | 17.0% |
| left/right lopsidedness | **41.3%** | **32.6%** | 41.2% |
| unlit (under 18% luma) | **28.3%** | **17.3%** | 40.1% |
| detail in the top third | **4.5%** | **6.9%** | 2.8% |
| materials on screen | 8.4 | 10.1 | 10.2 |
| biggest single surface | 33% | 33% | 33% |
| empty ninths | 24% | 25% | 35% |

Four rows separate and the rest do not:

- **The picture changes at half the rate.** Ours 9.8% against vanilla's 20.3%,
  and the shader walkthrough — a *slower* run than the speedrun — is higher
  still at 29.4%, so this is not the speedrunner's pace. A real player whips
  the camera constantly; ours is on rails with a smoothed tangent blend and
  moves like a tram. This is the largest single difference the frames show and
  it is a **camera** finding, not a level-design one.
- **Ours is more lopsided** (41% against 33%), which is the enclosure table in
  §4 arriving in the pixels.
- **Ours is darker than vanilla** (28% against 17%). The old reading that ours
  was *less* unlit came from comparing against a graded shader render.
- **Less overhead** (4.5% against 6.9%), same story as the lid.

And the rows that do not separate are worth as much: surface dominance,
material count, empty ninths and edge detail are all within noise of the real
map. **Palette count off a frame is not the floor-palette finding** in
`docs/TOWER.md` — that one is measured off the *blocks* of a terrace, where we
run 6 materials at 55% dominance against 14 at 26%, and it does not show up in
a frame statistic because a frame is mostly sky, rock and lighting.
