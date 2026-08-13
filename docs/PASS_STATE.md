# The level pass: live state

Working file for the 33-level rebuild started 2026-08-13. Delete it when the
pass is finished and its findings have moved into `docs/TOWER.md`.

## The rule for this pass

One agent per level, six at a time. Between batches: merge, run the full
suite, re-measure on a stable roster, and apply engine fixes. **Never change
the engine while agents are running** — every engine change re-rolls every
world and invalidates whatever they are measuring.

## Batches

| batch | levels | state |
|---|---|---|
| 1 | 1–6 | **merged** — 630 tests, design 100% legal |
| 2 | 7–12 | running |
| 3 | 13–18 | not started |
| 4 | 19–24 | not started |
| 5 | 25–30 | not started |
| 6 | 31–33 | not started |

After batch 6: full suite, `tower_probe`, `spiral_probe --plan tower`,
`bypass_probe`, `landmark_probe`, `frame_cost`, a roster sheet judged by eye,
then restart the daemon and confirm `brainrot doctor` is 14/14 with 1 daemon.

## Fixed centrally before the pass, do not let an agent move these

- `rise` — 4–8, nine values, every three consecutive summing 13–20 checked
  cyclically. Cycle climbs 187 blocks over 11 revolutions.
- `landmark` — spread so no blueprint repeats inside four levels; `arch` down
  from 8 of 33 to 4.

## Engine work done during the pass

- **Exit ladder anchors** (`_ascent_climb` stands its column on a pedestal):
  exit climb 38% → 33% of the course, level-visit overruns of 210 landings
  gone, worst now 30.
- **The outer wall** (`Cone.buttress_*`): rock outboard 5.6% → 29.8% against
  the real map's 33.6%.
- **The floor palette** (`FLOOR_MIX`, `Theme.floor_style`): a level's walking
  surface 3 materials at 69% dominance → 10 at 45%.
- **The cliff palette** (`CLIFF_MIX`, `Cone.cliff_style`) and lighter cone
  stone: unlit 39% → 29% of the frame.
- **A climb with nothing left to climb is just the crossing**
  (`handplan.Course._feat_ascent`, `need <= 0`): visits firing two ascents
  18.5% → 11.8%, designed content 45% → 49%, exit climb 36% → 31%.
- `level_review --sheet` now empties its frame directory — it was tiling stale
  PNGs into the sheet that judges the whole rebuild.

## Engine backlog, none of it blocking

Found by agents from inside their own levels. Apply between batches, each with
its own A/B, never while agents run.

1. **`_break_lips` always makes break 0 the wide one** and only that one gets a
   lock. Narrow breaks — holes a course jumps and a walker cannot — cannot be
   asked for without it, which forces `breaks=0` on levels that want them.
2. **`breaks` count is inert**: 3, 4, 5 and 6 produce a byte-identical course;
   only presence matters. Contradicts `docs/RULES.md`. Verify, then fix one or
   the other.
3. **`deco="lintel"` takes its height from the move's apex**, and a `walk` has
   no apex, so a lintel over a doorway lands at shin height — the one move
   that most wants one cannot have it.
4. **`wide` landings are priced out.** `_truncate` spends a beat's budget on
   `arc` and `wide`'s 1.05 `EDGE` forces every arc 0.6 m longer, so a 3×3 roof
   plate — the cheapest way to make a village read as buildings — costs a
   fifth of a level's designed content.
5. **`step_y` is absolute while the launch height is not**, so an authored
   ladder is only right for one entry height. Relative to the next level's
   floor would let a level author its exit once.
6. **`_last_resort` abandons the rest of a beat silently**, committing the
   recovery under the beat's own name. Worth surfacing in the probe.
7. **The gate crossing is the bottleneck, not the blueprint**: instrumented on
   one level, `_gate_crossing` returned `None` 103 times against 2 successes.
   This is the tower's own open item 0b.
8. **A gate-capable landmark cannot stand on a `channel` level** — no footing,
   the reservation fails, the level pays and gets nothing. With `landmark`
   frozen this pass, `channel` now carries that cost.

9. **`moat=True` on a `kind="walk"` node looks like a no-op.** Measured in one
   position over eight runs: identical worlds on every figure. If general, a
   plank across water cannot be authored, which is a hole in the vocabulary.
   Check `Course._moat` against walk landings.
10. **The no-jump walker is not deterministic across processes.** The same
    unchanged design read 41.8 / 45.0 / 47.9 / 53.2% coverage in four runs —
    set iteration order in the flood. That is ±6 points of noise on the one
    number the owner's "exactly one way to the end" rule is judged by, and it
    probably explains the 59%-mean / 1-of-16-fully reading at the batch-1
    merge. Sort the frontier; re-measure the watch item afterwards.

## Watch list

- **No-jump walk coverage rose to 59% mean with 1 of 16 levels fully
  walkable** at the batch-1 merge (real map 46%, none fully). The owner's rule
  is exactly one route to the end. If it is still there after batch 2, tighten
  the brief rather than the levels.
- Unlit is 29% of the frame against vanilla Minecraft's 18%. Closing the rest
  means an ambient term in the shading, which touches all four scenes.
- A single surface still owns about half the frame against the reference's
  third — the camera passing close to a wall on corridor bends.
