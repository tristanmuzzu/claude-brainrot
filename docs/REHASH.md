# The parkour rehash: a level is a climb you cannot re-enter

Plan only. Nothing here is built yet. Written 2026-08-16 from the owner's
review of the live tower, and it supersedes parts of `docs/RULES.md` and
`docs/RESEARCH.md` — see § "What this retires".

Read `docs/TOWER.md` for the tower's design and `docs/RULES.md` for the
constitution a level satisfies today. This document changes the constitution.

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
> at any landing of that level except its **first**.

Three outcomes for a missed jump and only one of them is a defect. **Dead**:
it lands in the void, or on ground that connects to nothing. **Back to the
start**: it can walk to the level's first landing and begin again — this is
what the owner describes and it is the *wanted* outcome. **Shortcut**: it can
walk back to landing 1 or later, so the fall cost nothing and every jump
before the one it re-enters at was decoration. Target: **zero shortcuts.**

Written: `tools/reentry_probe.py`, held by `tests/test_reentry.py`.

**The baseline, 6 runs × 260 landings of the tower as it stands:**

| | now | target |
|---|---|---|
| missed jumps that are a **shortcut** | **87.9%** | **0** |
| — back to the start | 5.1% | (fine) |
| — dead | 7.0% | (fine) |
| levels with at least one shortcut | **71 of 71** | 0 |
| landings standing on the terrace | 80.2%, **15.9 a level** | 1–2 a level |
| levels that never drop | **1 of 71** | all |
| air under a landing | median **0** blocks | — |

Two things follow immediately, and they are the whole rebuild:

- **A level climbs, monotonically, from its floor to its exit.** Start on the
  terrace, and every landing after that is at or above the one before. The
  level ends at the height the next level's floor wants. "Always going higher
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

## 3. What this does to the shape of a level

**The exit climb dissolves, and that is the largest single win here.** Today
the climb out is a separate appendage: 29–37% of every level, a staircase of
treads hugging the core, authored by all 33 levels via `exit_beats` with
`_ascent_stair` underneath as a fallback. It is also, by construction, both
the most floor-attached thing in the tower and a literal re-entry path.

If the level itself climbs from its floor to the next level's floor, the exit
is just the last two or three beats of the level. `ascent` stops being a third
of the course; the crossing over the chasm remains, and it is the one place a
level is allowed to lose a block (`hop_span(-1)` reaches 4.98 m against a
level 4.26, which is why the crossing descends by design).

**A level's climb budget is its `rise`.** Roster today: rise 4 (8 levels), 5
(7), 6 (8), 7 (5), 8 (5). Over nine to twelve landings, a rise of 5 is five
`+1` hops and the rest flat — comfortably inside the physics, since nothing
rises two blocks in one ballistic move and consecutive hops may rise at most
one.

**Floor contact is a budget, not an accident.** One landing per level touches
the terrace — the opener. A second is allowed where the level's idea needs it
(a landmark's threshold, a doorway). Everything else is airborne or stands on
authored structure that itself does not reach the ground.

## 4. What this retires

State it plainly so nobody re-derives it as a regression:

- **`bypass_probe`'s 46% target goes.** `docs/RESEARCH.md` measured the real
  Parkour Spiral save at 46% no-jump walk coverage and we deliberately match
  it at 47%. The reference map is paced for a twenty-minute run; this strip is
  on screen for fifteen seconds. The owner has asked for the harder thing
  knowingly. Coverage becomes a *reported* number, not a criterion.
- **"Levels are not monotonic climbs" goes.** RESEARCH.md §: 36 of 43
  reference levels descend somewhere and 22 dip below their own start. We are
  deliberately doing the opposite. The one sanctioned descent is the chasm
  crossing.
- **"Levels descend by falling off edges" goes** as a source of free variety.
  A fall is now a failure state, not a route.
- **`docs/RULES.md` §0 and §3 need rewriting** against P-RE once Phase 1
  lands.

Nothing about the *look* is retired: material counts, the 14-material floors,
enclosure, landmarks, the groove, the frame-emptiness budget all stand.

## 5. Engine work (Phase 1)

Ordered by how much of the complaint each closes.

1. **`pedestal` defaults to `False`** in `Course._node`. Today a landing that
   cannot build a column to the ground is *refused* (`_pedestal`: "never found
   ground: it is a stilt"), so floating is opt-in per node. Invert it. The 1–2
   floor-contact landings a level is allowed say `pedestal=True` explicitly.
2. **Monotonic lift, enforced.** A design-time check in
   `tools/tower_probe.py --design-only` (instant, no world) refusing any
   authored node whose surface is below the one before it, bar the crossing.
   Cheap, and it catches the whole class before anything is rendered.
3. **The exit becomes the level's own last beats.** `exit_beats` stays as a
   mechanism; `_ascent_stair` becomes a genuine emergency rather than 17% of
   the climb. Watch the stuck rate here — this is the change most likely to
   move it, and `TRACE` round `Course._attempt` is how it gets diagnosed.
   Every reduction this format has ever had came from reading that table and
   not one from reading the code.
4. **`Course._walk_bridge` stops laying free ground.** It currently lays
   terrain under any `walk` leg that crosses air — 98% of walk legs did — which
   is a re-entry path being built automatically under the one verb that is not
   a jump. A walk becomes an authored platform or the leg is refused.
5. **`LIFT_MAX = 6` versus a rise of 7 or 8.** Ten levels want more climb than
   the cap allows. Open air over a level is the next three rises minus
   `FLOOR_T = 5`, so 8–15 blocks; 7 and 8 are probably fine and the cap is
   probably conservative. **Measure it before raising it** — a landing too
   high has the next turn's floor slab for a ceiling. Cheapest alternative:
   cap the roster's rises at 6, which touches ten level headers and nothing
   else.
6. **Gated landmarks must move or move earlier.** `_landmark_nodes` steers the
   course through a structure's passage at apron level, which is terrace
   height — that fights a course that has already climbed away from the
   terrace. Two answers, both cheap: enter the gate in the level's first two
   beats while the body is still low, or raise the gate to an upper storey of
   the structure. Locks (`_lock_nodes`) are unaffected and stay useful: an
   island floated over a floor break is already airborne.
7. **The head-hitter stays at three above the take-off.** Unchanged, and the
   reason is in `_ceiling_cells`: a body is 1.8 m and a jump rises 1.25, so a
   lid at two is a lid inside the player. Faithful `2bc` needs jump-cancel in
   `parkourkit`, which is a physics change and not this one.

## 6. The probe (Phase 0) — **done**

`tools/reentry_probe.py --runs 6 --blocks 260`, ten seconds, no window.
`--levels` prints one line per level, worst first, which is the authoring
feedback loop for Phase 3. Sections: re-entry (the criterion), floor contact,
the climb, and two numbers reported but not gated.

Four things it does that a naive version gets wrong, each of them a wrong
answer that was measured before it was fixed:

- **A jump that was made is not a fall.** Early in an arc the body is still
  over the block it left; a sample coming to rest there is not a miss, and
  counting it makes every jump in the tower read as a shortcut.
- **The fall is sampled along the whole arc**, not from the landing. A miss
  happens anywhere between the two blocks, and where it comes down decides
  everything.
- **A level is judged while its own cells are still live.** `Course.advance`
  releases cells behind the body, so a level walked after the fact is walked
  against a world that has had its floor taken away — which reads as a
  spectacular pass and is the probe's own doing. `KEEP` holds ninety-six
  landings and `LAG` judges two levels back, because a level's exit climb and
  crossing are laid *after* its last terrace landing.
- **One flood per level, not one per landing.** Reachability is a component
  id; union-find over the walkable surface answers ten landings for the price
  of one.

`tests/test_reentry.py` holds it against worlds small enough to check by hand:
a course on a continuous floor must read all shortcut, the same course over
the void must read all dead, and a floor under the opening landing alone must
read "back to the start". The third test is one cell wide on purpose — extend
its slab by three cells and the answer flips to shortcut, which is the whole
design in miniature.

Every later phase is judged against this file. The runner and the spiral were
both fixed exactly this way — turn the complaint into a number, write the
probe, then rewrite against it — and neither was fixable before the number
existed.

## 7. Phases, and where subagents go

| phase | what | subagents |
|---|---|---|
| 0 | `reentry_probe`, targets agreed | no |
| 1 | engine, § 5 above, one context, `TRACE` loop | no |
| 2 | pilot three levels by hand — one ledge, one interior, one vertical (BALCONIES, CISTERN, ECHO SHAFT) — reviewed with `tools/level_review.py --level N --all` until the frames are right. Produces the authoring recipe. | no |
| 3 | the other 30 levels against the recipe | **yes** |
| 4 | whole-roster verification | no |

Phase 3 is the clean fan-out: one agent per level module, each touching
exactly one file, each verified by `tower_probe --design-only` (instant, on
paper) plus its own `level_review`. Batches of five or six; the main thread
reads the frames and merges. Each agent must be told: **one level per
process** — the phase pin in the review tools is a class-level patch and the
tool refuses a second — and no agent runs the full test suite.

Phases 0, 1, 2 and 4 are single-context work with a measurement loop. Fanning
out on the engine is how four agents each fix the stuck rate a different
incompatible way.

## 8. Verification at the end (Phase 4)

`reentry_probe` (the criterion), `tower_probe` (fidelity — the design is
100% legal on paper and ≥94% placed as authored), `spiral_probe --plan tower`
(safety: nothing twice-claimed, body never inside the world, unchecked
placements ≤ 0.5%), `landmark_probe` (structures still seen), `frame_cost`
(a floating course draws *fewer* cells than a pedestalled one, so this should
improve), `roster_sheet` (do the levels still read as places), and
`python -m pytest tests/`.

## 9. Risks, honestly

- **The stuck rate.** Removing the pedestal requirement makes placement
  *easier*, but removing the generated staircase removes the recovery of last
  resort. Net effect unknown; `TRACE` is the instrument.
- **Frames of nothing.** A course three to six blocks above its terrace looks
  down at the terrace, which is good, but it also looks out at sky. Frame
  emptiness is currently 44–56% and the budget is 48%. Watch `level_review`'s
  emptiness number per level, not just the roster mean.
- **The camera.** It locks onto the landing through take-off and flight, and a
  rising course means more of the frame is the sky above the core. May need
  the tangent blend re-tuned; it is `_look`'s `lock` ramp and `RIDE_OUT`.
- **The move mix.** 82% plain hop today, and a monotonic climb is hop-shaped.
  The non-hop share (walk 8, slide 4, climb 3, bounce 2, bubble 1) partly
  lives in the exit staircase that is being dissolved. Expect it to fall
  before it rises, and buy it back with authored ladders, vines and slides
  *between airborne platforms* rather than against the core.
