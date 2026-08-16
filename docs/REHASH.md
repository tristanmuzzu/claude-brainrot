# The parkour rehash: the course flies over its terrace

**Built 2026-08-16.** Written first as a plan, from the owner's review of the
live tower, and then carried out in one pass across the engine, all thirty-three
level modules and the probes. It supersedes parts of `docs/RULES.md` and
`docs/RESEARCH.md` — see § "What this retires".

Read `docs/TOWER.md` for the tower's design and `docs/RULES.md` for the
constitution a level satisfies. This document changed that constitution.

**Where it ended up**, 6 runs × 260 landings unless said otherwise:

| | before | after |
|---|---|---|
| missed jumps that walk back into the course | **87.9%** | **0.6%** |
| levels with one | all of them | **3 of 84 visits** |
| landings resting on the terrace | 15.9 a level (80%) | **2.5 a level (13%)** |
| a level walked end to end, no jumps | 2 of 24 | **0 of 55**, 34% mean |
| landmarks framed at 25° / 40° | 55% / 30% | **68% / 63%** |
| unchecked emergency placements | 0.31% | **0.64%** |
| the design placed as authored | 97.9% | **94.9%** |
| designed content, share of the course | 52% | **56%** |
| frame cost against `parkour` in one process | 1.46 | **1.78** |

---

## 1. The complaint, and the number under it

The owner's words: the levels *look* right — the themes, the decoration, the
sense of place are all liked — but the parkour is "too easy, too strange". The
jumps go from a block resting on the floor to another block resting on the
floor; "they're attached to the floor, but the player keeps jumping from one
to the next", and it is rare that any jump is one a real player would find
difficult.

Measured, 4 runs × 240 landings of the tower as it stands:

| | |
|---|---|
| landings attached to the floor | **83.2%** |
| — of which a pedestal column down to the terrace | 42.8% of all landings |
| — of which resting directly on the terrace terrain | 40.4% of all landings |
| landings with any air under them | 16.8% |
| landings with 8+ blocks of clear void under them | 4.1% |
| landings at `lift = 1` | **76.7%** |

Authored across the roster: 121 nodes at `lift=1`, 94 at 2, 43 at 3, 11 above
that, and 203 nodes that name no lift at all. The design says what the world
measures.

## 2. The criterion: **no re-entry**

The owner's own framing, and it is sharper than "put it over the void":

> I want it to feel like if you fall, you would theoretically have to go back
> to the beginning of that level to attempt the parkour again. There shouldn't
> be any point in the level where you go down to a ground block and then from
> there can go up again.

So the acceptance test is not "is there void beneath this jump" — void is a
flavour, and some jumps out over the rim are wanted for their own sake. The
test is **reachability**:

> **P-RE.** A body that misses a jump, falls, and then walks — stepping up at
> most one block, dropping any distance, never jumping — must not arrive back
> at any landing of that level except its **entry apron**.

Three outcomes for a missed jump and only one of them is a defect. **Dead**:
it lands in the void, or on ground that connects to nothing. **Back to the
start**: it reaches the entry apron and no further — this is what the owner
describes and it is the *wanted* outcome. **Shortcut**: it can walk back onto
anything above that apron, so the fall cost nothing and every jump before the
one it re-enters at was decoration. Target: **zero shortcuts.**

**The apron is geometry, not generosity**, and getting that definition right
was most of the probe's development. A level below tops its climb out one
block over this terrace so that its crossing can *descend* onto it; the
crossing lands on the terrace itself; and the first landing off the terrace
can only be one block up, because nothing rises two in one ballistic move. All
of those are walkable from the ground whatever anybody designs, they arrive
interleaved rather than in a neat prefix, and walking back to any of them is
walking back to the beginning. So the apron is *every* landing at or under one
block over the terrace, capped at six — and what stops a level living down
there is the design check, which allows exactly one.

Written: `tools/reentry_probe.py`, held by `tests/test_reentry.py`.

**The baseline it started from, and where it is now** (the same probe, 4–6
runs × 240–260 landings):

| | before | after |
|---|---|---|
| missed jumps that are a **shortcut** | **87.9%** | **0.6%** |
| — back to the apron | 5.1% | 33.7% |
| — dead | 7.0% | **65.7%** |
| levels with at least one shortcut | **71 of 71** | **3 of 84 visits** |
| landings standing on the terrace | 80.2%, 15.9 a level | **13%, 2.5 a level** |
| air under a landing | median **0** blocks | median **2** |

Two things follow, and they are the whole rebuild:

- **A level climbs.** Start on the terrace, gain a block, and cruise three to
  six blocks over it for the rest of the level; a drop of up to three is a
  showpiece and anything more is the deck coming back down. The level ends
  higher than it began and the way out finishes the job. "Always going higher
  and higher above the level from start to finish, and then the next level
  starts and it goes again."
- **The terrace stops being the ground the course stands on and becomes the
  place the course flies over.** It stays fully themed and fully dressed —
  that is the half the owner likes and none of it is being deleted. It is the
  fall zone, and the fall zone is a dead end because the course left it at
  landing one and never came back down to it.

Falls therefore do not need void beneath them. They need the terrace under
them to be **unable to climb back**, which is true for free once the course is
three or more blocks above it with no pedestal, no staircase and no ramp.

## 3. What it did to the shape of a level

**The exit climb shrank, and that was the largest single win.** It was a
separate appendage: 29–37% of every level, a staircase of treads hugging the
core, authored by all thirty-three levels via `exit_beats` with
`_ascent_stair` underneath as a fallback — simultaneously the most
floor-attached thing in the tower and a literal re-entry path.

A level's course now cruises two to six blocks over its own terrace, so the
way out has only `rise + 1 - deck` left to gain: one to three treads where it
used to be five or seven. The authored *share* of the exit therefore fell —
46% against 55% — while the design got better, because what fills the gap is
the crossing and the walk along the last of the terrace to it, both aimed at
the chasm rather than written down. `tests/test_tower.py` was rewritten to
hold what now matters: the improvised staircase stays under 30% of the exit,
and the design, the crossing and the walk to it are over 70% of it together.

The crossing itself is untouched, and it is still the one place a level is
allowed to lose a block (`hop_span(-1)` reaches 4.98 m against a level 4.26,
which is why it descends by design).

**`Level.deck` is the number the rest of the machinery aims at**: where the
script and the filler leave the body, computed once in `levels/_base.py`. A
gated landmark stands on a plinth that tall; the exit knows what is left to
climb; the design check knows what the filler has to come back to.

**Floor contact is now a budget of one.** The apron is the level's beginning;
everything after it is at least two blocks up. Measured, the tower runs at 3.3
floor-contact landings a level, and every one of them is geometry rather than
design: the crossing's own landing on the terrace, the apron, and the tread
the level below topped out on.

## 4. What this retires

State it plainly so nobody re-derives it as a regression:

- **`bypass_probe`'s 46% target goes.** `docs/RESEARCH.md` measured the real
  Parkour Spiral save at 46% no-jump walk coverage and the tower deliberately
  matched it at 47%. The reference map is paced for a twenty-minute run; this
  strip is on screen for fifteen seconds. Coverage is a *reported* number now
  — and it came out at **34% mean, 0 of 55 levels walkable end to end**, which
  is harder than the reference rather than softer.
- **"Levels are not monotonic climbs" goes.** RESEARCH.md: 36 of 43 reference
  levels descend somewhere and 22 dip below their own start. This tower climbs
  on balance and its drops are showpieces of at most three blocks.
- **"Levels descend by falling off edges" goes** as a source of free variety.
  A fall is a failure state now, not a route.
- **`breaks=0` goes with the lock.** Nineteen levels had chosen no floor
  breaks because any break at all forced the lock, and the lock cost them one
  to three landings. A course three blocks up flies over a break, so the lock
  is skipped and breaks are free obstacles again: the whole roster is at three
  or four, and that alone took a no-jump walker from 70% of a level to 48%
  and from 2 levels walkable end to end to none.

Nothing about the *look* is retired: material counts, the fourteen-material
floors, enclosure, landmarks, the groove and the frame-emptiness budget all
stand, and the terrace is untouched.

## 5. The engine, as built

1. **`pedestal_default = False` on `handplan.Course`.** A landing that cannot
   build a column to the ground used to be *refused*; floating is the default
   here and the generated tower keeps the opposite, which is the one thing the
   two formats genuinely disagree about.
2. **`lift_floor = DECK_MIN`.** `spread` lets placement fall back through
   neighbouring heights, and an authored landing three blocks up was quietly
   being placed one block up. A fallback may go up and never under the deck;
   the floor never rises above what the node asked for, so the apron keeps its
   own height.
3. **Machinery keeps the body's height.** `_here_lift()` — floored at two,
   because the one place the body legitimately is lower is the apron and a hop
   from there to two is an ordinary +1. It is used by the lock's approach and
   island, the doorway's approach, `_recover_lifts` and the unchecked
   emergency landing. Every one of those asked for `lift=1` before, which on a
   climbing level is a staircase down to the terrace and back.
4. **The lock is skipped while the course is flying.** It exists to get a body
   across a hole in ground it is running on; three blocks up the hole is
   scenery. The break stays uncrossed and unmarked, so a level whose course
   does come back down is still offered it.
5. **A gated landmark stands on a plinth as tall as the level's deck**, so the
   course goes through its doorway rather than past its foot — and the plinth
   stops short of the passage, so a fall through the doorway carries on down
   instead of landing in it. Worth 4.5 points of re-entry and 1.6 points of
   unchecked placement on its own, and it took landmarks framed at 40° from
   30% of levels to 63%.
6. **`noclimb`: nothing may be built in the ring beside a landing, between the
   terrace and the landing's own height.** Terrain dressing was three quarters
   of what was left once the designs were raised — the landings were out of
   reach and the scenery beside them was a staircase. Reserved rather than
   checked, because dressing runs after the course is laid.
7. **The exit starts from the deck.** Eighteen levels opened their exit with
   an absolute `lift` — the foot of a staircase standing on the ground — which
   on a flying course is the whole level dropping back down. They are written
   `step_y=0` now, and `_feat_ascent` prepends one +1 hop when a level is
   entered so late that its own beats never climbed.
8. **A relative chain that lost a block gets it back.** `step_y` is measured
   from the landing before, so one refused node in the middle of a beat leaves
   every node after it a block low — and a block low is one block over the
   terrace, which is the whole defect. `_targets` nudges such a landing up to
   the deck *when that is still a jump the body has*, which is exactly when
   the chain is one block down; the step after is back on the design's own
   numbers. This one change took re-entry from 3.4% to **0.6%** and the levels
   showing any from nine to three.

**Two things on the plan's list turned out not to be needed.**
`Course._walk_bridge` lays ground under a walk leg *at the walk's own height*,
so it is a platform rather than a ramp and it creates no re-entry; it stays.
And `LIFT_MAX = 6` is exactly right rather than conservative: the open air
over a level is the next three rises minus `FLOOR_T`, which the three-window
rule holds at eight or more, and a landing at lift 6 needs exactly eight. What
climbs past it is the exit, which is written on `step_y` and is not clamped.

## 6. The probe

`tools/reentry_probe.py --runs 6 --blocks 260`, ten seconds, no window.
`--levels` prints one line per level, worst first, and `--only NAME` filters
it. Sections: re-entry (the criterion), floor contact, the climb, and two
numbers reported but not gated.

Five things it does that a naive version gets wrong, each of them a wrong
answer that was measured before it was fixed:

- **A jump that was made is not a fall.** Early in an arc the body is still
  over the block it left; a sample coming to rest there is not a miss, and
  counting it makes every jump in the tower read as a shortcut.
- **Only a ballistic move can be missed.** A walk is on the ground for its
  whole length, a climb is on a ladder and a bubble ride is inside a column of
  water. Sampling a fall from one measures the walkway it is standing on, and
  leaving them in read as re-entry on every walk leg in the tower.
- **The fall is sampled along the whole arc**, not from the landing. A miss
  happens anywhere between the two blocks, and where it comes down decides
  everything.
- **A level is judged while its own cells are still live.** `Course.advance`
  releases cells behind the body, so a level walked after the fact is walked
  against a world that has had its floor taken away — which reads as a
  spectacular pass and is the probe's own doing. `KEEP` holds ninety-six
  landings and `LAG` judges two levels back, because a level's exit climb and
  crossing are laid *after* its last terrace landing.
- **Walking is not symmetric, so the search runs backwards.** A body steps up
  one block and drops four; "are these two spots connected" is the wrong
  question, and a union-find answers it wrongly in a way that looks right — a
  landing four blocks over the terrace can always walk *down* to it, and a
  symmetric flood then reports the terrace as able to walk back up. It is one
  reverse breadth-first search per level per target set.
- **The question is per jump, not per level.** What a fall may not do is
  resume the course *at or past where it fell from*; walking back to something
  earlier is the long way round and is the point. Seeded from the landings in
  descending order, one pass labels every cell with the latest landing it can
  reach, which answers all of them at once. Without it the level below reads
  as this level's course — its climb tops out one block over this terrace so
  its crossing can descend onto it, and half a dozen of its landings lie about
  on this floor.

`tests/test_reentry.py` holds it against worlds small enough to check by hand:
a course on a continuous floor must read all shortcut, the same course over
the void must read all dead, a floor under the opening landing alone must read
"back to the start", and the apron must be excused. The third test is one cell
wide on purpose — extend its slab by three cells and the answer flips to
shortcut, which is the whole design in miniature.

## 7. How the thirty-three levels were re-authored

Not by hand, landing by landing, and not by an agent per level either. The
transform is mechanical and the judgement is in the exceptions:

1. **A source-level rewrite through `ast`**, editing the exact offsets of each
   `lift=` keyword so every comment and every hand-chosen number outside it
   survives. Each level's landings move up by the least that clears the deck,
   *preserving the deltas* — the shape of a level is its rises, so the arcs
   stay legal wherever they were legal before.
2. **The filler is flattened to the deck**, because it repeats and anything it
   gains it gives back at the seam.
3. **`tower_probe --design-only` names what broke**, instantly and by level,
   beat and node index. It went 170 complaints → 57 → 0, and every one of the
   57 was a real authoring decision: a walk that had to swap places with the
   hop after it so the level could get off its apron, a fall that had to stop
   two blocks higher, a filler whose ladder had to move into the script
   because a climb inside a loop comes back down at the seam.
4. **The exits were trimmed by the same method** — whole `n(...)` calls
   deleted from the middle of `exit_beats`, and a single ladder or bubble
   shortened when there was nothing to delete.

The scripts are throwaway and live in the session scratchpad; the *method* is
the durable part, and it is the third time on this project that a mechanical
AST pass plus an instant design checker has beaten hand-editing.

## 8. Verified

| | |
|---|---|
| `reentry_probe` | shortcut **0.6%**, 3 level visits of 84, apron 2.5 a level |
| `tower_probe` | design 100% legal on paper, **94.9%** placed as authored, designed content **56%** of the course |
| `spiral_probe --plan tower` | twice-claimed 0, off-lattice 0, unchecked **0.64%**, cone-alone walkability **0 m** |
| `bypass_probe` | **34%** mean, **0 of 55** levels walkable end to end |
| `landmark_probe` | **68%** of levels at 25°, **63%** at 40°, 3.25 a minute |
| `spiral_probe` (generated) | unchecked **0.24%**, built terrain 94.4% — unchanged |
| `frame_cost` | parkour 2.04, runner 2.16, spiral 2.62, **tower 3.63** ms |
| `pytest` | 640 passed, 34 skipped |

## 9. Still open

- **Frame cost.** tower/parkour went 1.46 → 1.78 and the tower is 3.63 ms
  against the 3.5 the criteria ask for. The likely causes are all cell counts:
  the terrace is dressed *and* the course is a separate set of blocks above
  it, where before the two were the same cells. Measure `emit_layer` and the
  dressing pass before optimising anything.
- **Three level visits in eighty-four still have a shortcut**, at 0.6% of
  missed jumps. `reentry_probe --levels --only NAME` names them; each is worth
  tracing with the same throwaway path-printer the rest of this pass used,
  because every one of the six causes found this way was invisible in the
  aggregate.
- **The move mix.** A flying course is hop-shaped and the exit staircase that
  carried the slides and climbs is mostly gone. Non-hop share is 16% on the
  tower against 6% on the generated spiral, so this is not urgent, but the
  answer when it becomes urgent is authored ladders, vines and slides
  *between airborne platforms* rather than against the core.
- **The camera.** A course three to six blocks up sits closer to the slab
  overhead, and the contact sheet shows more frames with a ceiling across the
  top than before. It reads as enclosure rather than as a fault, but it is
  worth a pass with `level_review`'s emptiness number per level.
