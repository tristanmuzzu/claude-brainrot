# Handoff — the tower after the walk-verb session

Rewritten 2026-08-14, at the end of the session that took the previous handoff
apart. Everything below is committed, pushed and live on branch
`claude/project-visuals-animations-qzbkiq`. 634 tests pass, 34 skip.

The previous edition of this file is in the history and is worth reading for
its method, not its facts: **five of its six open items turned out to rest on
something that was no longer true, or on a diagnosis that was one layer short.**
That is not a criticism of it — every one of those items named the right
symptom, and three of them named the right measurement. It is the standing
lesson of this project restated: a claim in a document has no date on it that
the reader can trust, and the first thing to do with an inherited item is
re-measure it.

---

## What the owner reported, and what it turned out to be

Two symptoms, from watching the live strip:

1. **A landing a block or two away with a gap in between is crossed by walking
   over the air.** Real, and it was the `walk` verb: `_move_for` validated a
   walk by its two endpoints and nothing between them. 98% of walk legs crossed
   air, mean 0.76 m, worst 1.68 m. Fixed — a walk now lays the shelf it crosses
   (`Course._walk_bridge`), 0% of legs cross air, and the fix costs nothing
   (design fidelity 97.6% against 97.7% before).
2. **Sometimes the body passes straight through a block.** Real, much bigger
   than anyone thought, and **not the walk verb**. `emit_layer` drew the core's
   flutes a cell proud of `core_r`; `rock` had never heard of them. Twenty-eight
   of the fifty-six ribs — the tower's signature forest of columns — were drawn,
   lit, fogged and walked through. **3.3% of body samples along a course were
   inside a cell the tower draws**, up to 0.80 m deep.

The reason symptom 2 hid for so long is worth keeping: the "body inside the
world" figure asks `blocked`, which is `rock`, which is exactly the half of the
disagreement that is wrong. A metric built on one of two disagreeing sources
cannot see them disagree.

Both are held by tests. `tools/walk_probe.py` is the instrument for the first
and `tests/test_spiral.py::test_what_the_tower_draws_is_what_the_tower_is` for
the second.

### The owner's deeper question, answered with a number

> *Does the player model have an actual hitbox, and do the individual blocks?*

There is geometry for a body at generation time (`parkourkit.body_cells`), and
no runtime collision: the course is a list of solved moves and the body plays
them. The question is whether that construction-time proof should be replaced
by simulation-time truth, and it now has a measurement behind it.

`tools/walk_probe.py` walks every committed move against the world as it stands
when the body would reach it. On the tower, after this session's fixes, over
2,880 moves: **0% over nothing on a ground leg, 0.14% of moves with solid
inside the body and never deeper than 0.55 m** — and that residue is the
dressing-built-after-an-arc class, unchanged from before.

So the construction guarantee is not fiction. It had two holes — one verb and
one surface described twice — and both are closed. A real collision model is
still the thing that would let a level be *proved* completable and would unblock
the kernel changes `docs/TOWER.md` lists (jump-cancel, momentum, steered
jumps), but the case for it is what it buys, not the state of the contract.

---

## Open, in the order I would take them

### 1. The generated staircase is 17% of the exit climb

The exit climb is 29% of the course and, measured for the first time this
session, **60% of it is the level's own design** at 98.5% placed as authored.
The rest is the crossing (23%, and it is the hero jump — it is meant to be
there) and a generated staircase finishing a climb the design did not top out
(17%).

That last 17% is per-level authoring and the reject table names a different
cause for each: WINDMILL REACH `no move: hop`, WART FIELDS `landing occupied`,
THE WHITE STAIR `pedestal will not stand`, THE QUARRY `no move: bubble`,
MARKET STREET `no move: climb`. `tower_probe` prints THE WAY OUT and a
per-level staircase count; that is the loop.

### 2. Two beats own most of the remaining wall-in-the-lens

Bucketing jammed frames by what the body is doing found the big one (the ride
camera, fixed — climb 42% → 16%). What is left is level-specific: `basin` jams
16.7% of its 54 frames and `sill` 8.2% of 748. Same method, same predicate
(`spiral_probe._lens_jammed`), one level at a time.

### 3. Three beats are mostly sky

`stacks` 60.2%, `gate` 55.7%, `stalls` 55.3%, against 41.9% for the run as a
whole. Note the direction before acting: the frame is emptier than the real
game's only in the *other* direction — whole-frame emptiness is 14.9% against
vanilla's 24.4% — so this is about those three beats reading as thin, not about
the tower being empty.

### 4. Gate entry, and the fix that is not the obvious one

Over 8 runs: 173 levels wanted a gate, 135 got the reservation, 107 were
offered, 62 put a landing in the passage. **The fix the last handoff
recommended has been tried and is worse** — see the note under CLAUDE.md's
outstanding item 0b. Doing it properly means `_reserve_landmark` holding the
approach cells as well as the passage.

### 5. The roster still wants assets

Per-theme pours, the windmill's blades, a bell, coral fans, a scarecrow. All
`assets/src/` work, none load-bearing.

---

## Closed this session, with the numbers

| | before | after |
|---|---|---|
| walk legs crossing air | 98% (mean 0.76 m) | **0%** |
| body inside a cell the tower draws | 3.3% of samples, 0.80 m | **0%** |
| drawn cells that are air | ~24,000 | **0** |
| body inside the world | 0.02% of frames | **0.00%** |
| unlit pixels (vanilla 17.4%) | 24.1% | **17.9%** |
| jammed frames (climb / bubble) | 3.23% (42% / 30%) | **1.83%** (16% / 15%) |
| exit climb: generated staircase | 177 a sweep | **141** |
| exit climb: authored, placed as authored | 98.1% | **98.6%** |
| gated passages entered (8 runs) | 56 | **62** |
| design fidelity | 97.7% | **98.0%** |
| tower ms/frame (criteria: 3.5) | 3.74 on record | **2.79** |
| a bubble column in a lava theme | always water | its theme's liquid |

---

## Two measured dead ends, so nobody pays for them twice

- **Aiming the gate approach.** Placing the last approach landing a level hop
  back from the doorway halves the hop refusals and *reduces* passages entered
  (56 → 48), because an `at` node is strict, the crossing is offered once, and
  a launch cell that will not take a landing spends the offer. Pre-checking the
  cell changes nothing: the cells are free, and what fails is the hop into
  them.
- **Skipping the `rock` gate inside `emit_layer`.** A margin that skips the
  gate "comfortably inside" the wall leaks five cells a sweep, because `unwrap`
  puts a cell near a level seam in the *other* level, whose band is a different
  width. The 0.27 s of scene construction the gate costs is the price of the
  guarantee.

---

## How to work on this tower

The previous edition's four rules all held up, and this session added a fifth.

- **Judge the contact sheet with your own eyes before you look at a number.**
- **Check what a reference actually is.** Two of the three "Parkour Spiral"
  videos this project was calibrated against are shader-rendered and one is a
  different map. `docs/reference/frames/vanilla_2hz` is the only vanilla-lit
  set; the ambient-light fix is measured against it and nothing else.
- **Send a second agent whose brief is to refute the first.**
- **A moving roster is not a noisy metric.** Decide on in-process A/Bs.
- **Re-measure an inherited claim before building on it.** Five of the six
  items in the last handoff had moved: all thirty-three levels write
  `exit_beats` (it said none did), the exit ladder fires (it said never), the
  frame budget is met (it said 3.74 ms against 3.5), the level openings are
  four points emptier than average rather than a hole at every boundary, and
  the gate fix it recommended is a regression. The one that was exactly right —
  the walk verb — was right because whoever wrote it read the code and said
  plainly that they had not then instrumented it.
