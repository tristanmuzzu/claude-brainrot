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
| 2 | 7–12 | **merged** — 630 tests, design 100% legal |
| 3 | 13–18 | running |
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
10. ~~**The no-jump walker is not deterministic across processes.**~~
    **Checked and false.** Run three times in three processes on a stable
    roster it reads identically to the digit. The ±6 spread the agent saw was
    the *roster* changing under it — five other agents were rewriting levels
    while it measured. Sets of int tuples do not get hash randomisation, so
    there was never a mechanism. Worth keeping as a reminder that "noisy
    metric" and "the thing being measured is moving" look identical from
    inside one level.

11. **The generated exit climb launches at `hug=2.2` and that is most of the
    wall-in-lens number.** Measured on one level: 69 jammed frames of 1,293 at
    2.2, **0 of 1,280** at 2.8. `_ascent_climb`'s first node is written
    `hug=2.2`, so this is one constant across the whole tower and is the most
    promising single fix left for "a surface owns half the frame". Needs its
    own A/B — it moves every world.
12. ~~**A beat's first node is effectively pinned at lift 1.**~~ **Narrowed by
    a second agent, and the narrowing is the useful part.** One level measured
    an opener at lift 2 placing 67% against 100% at lift 1; another measured a
    `lift=2, spread=1` opener at **72/72, 100% exact over 24 runs**, genuinely
    at lift 2 in the blueprint. The difference is what the beat *follows*: an
    opener after a script beat is free, an opener after **machinery** — the
    climb, the lock, a recovery — is not, because machinery leaves the body
    wherever it happened to finish. So the real item is that machinery hands
    over at an unstated height, which is also backlog 5. A level can and
    should open its script beats above the floor.
13. **`exit` becomes a reserve declaration once `exit_beats` exists.**
    `_level_budget` reserves `(need+1)*3.2` for `"stair"` and a flat three
    landings for anything else, so a level with a four-landing authored exit
    has to *misdescribe its own exit kind* to get an honest reserve — one
    level declared `"vine"` for an exit that is a walkway, because declaring
    `"stair"` reserved ten blocks nothing would spend and truncated its
    showpiece out of the run. Cost it from `len(exit_beats)` instead.
14. **A shell has no per-node material** — `_shell` paints walls `theme.rock`
    and roof `theme.sub`, so the only wide overhead mass available to any
    level is brown. Letting `pedestal_style` paint a shell the way it already
    paints a lid would give the jungle a real canopy for nothing.
15. **`hug` on a climb node is inert** — 2.0 through 3.0 give identical
    worlds. Only the launch landing's hug does anything. Either make it work
    or reject it loudly.

16. **Re-test `shelf` above 5.0 centrally.** Two levels independently measured
    a wider shelf as strictly better -- one at 5.6 read designed content 54.8
    -> 56.1% with 100% exact and no unchecked -- and both left it at 5.0
    because `docs/RULES.md` records 5.2 and 5.5 failing
    `test_the_course_goes_through_the_landmarks_it_gates` on a *different*
    level. That is a tower-wide test agents are forbidden to run, so nobody
    can check whether the ceiling is real or was one level's accident. Free
    content across the roster if it lifts. (5.9+ starts producing unchecked
    placements on at least one level; do not go far.)
17. **The climb's own pedestal is the wall in the lens.** An in-body ladder
    anchors on the column it builds, and the body then rides with its face
    against that column -- one level measured 9.7% jammed on a seed with every
    jamming ray hitting its *own* brick, none of it the cliff. A `_climb_move`
    that could anchor on the cliff at `hug` 1.6-2.0 without building a column
    would remove it. Same defect family as backlog 11.

## Watch list

- ~~No-jump walk coverage at 59% mean, 1 of 16 fully walkable.~~ **Closed
  after batch 2: 37% mean, median 40%, and 0 of 40 levels walkable end to
  end**, against the real map's 46% and 0 of 43. Better than the reference on
  both halves. The batch-1 reading was taken while agents were editing.
- Unlit is 29% of the frame against vanilla Minecraft's 18%. Closing the rest
  means an ambient term in the shading, which touches all four scenes.
- A single surface still owns about half the frame against the reference's
  third — the camera passing close to a wall on corridor bends.
