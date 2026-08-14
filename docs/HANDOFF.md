# Handoff — the tower after the level pass

Written 2026-08-14, at the end of the session that rebuilt all thirty-three
levels. Everything below is committed, pushed and live on branch
`claude/project-visuals-animations-qzbkiq` at the head of that work. `brainrot
doctor` is 14/14 with one daemon; 631 tests pass, 34 skip.

Read `docs/PASS_STATE.md` first for how the pass ran and the sixteen
level-authoring landmines it paid for. This file is what is *left*.

---

## 0. The bug the owner reported, and the question under it

**This is the most important item in the file and it is first for that reason.**
Two symptoms, reported from watching the live strip:

1. **A landing one or two blocks away with a gap in between is crossed by
   walking over the air, not by jumping.** The body slides across the hole at
   run speed and never leaves the ground.
2. **Sometimes the body passes straight through a block**, entirely.

### The hypothesis to test first

`Course._walk_move` in `src/brainrot/scenes/spiralplan.py` reads, in essence:

```python
if kind == "walk":
    dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
    if dist > 2.4 or abs(to[1] - frm[1]) > 0.55:
        return None
    return Move("walk", [line_leg(frm, to, RUN_SPEED)]), ()
```

It validates **only the two endpoints** — how far apart they are and how much
they differ in height. It never asks whether there is floor along the line
between them, and it never asks whether anything solid is *in* that line. A
`walk` is then a straight `line_leg` from A to B.

If that is the whole story, both symptoms are the same bug: a walk leg whose
path crosses a hole walks on air, and a walk leg whose path crosses a block
walks through it. Every *ballistic* move goes through the arc clearance test
(`_path_clear`, `body_cells`) and is checked properly; the walk is the one verb
that skips it.

**Do not take this on trust.** It is read off the code by someone who did not
then instrument it. Verify by finding a real occurrence first: drive the scene,
sample the body along every `walk` leg, and count legs where a sample has no
solid cell beneath the feet, or has a solid cell inside the body. Then decide
whether the fix is to give `walk` the same clearance test the hops get, or to
refuse a walk whose path is not continuous ground and let the feature fall back
to a hop.

Watch for a second-order effect: `walk` is 12% of the move mix and several
levels lean on it deliberately (it is the only non-hop verb a hot theme can
spend, and it is how a doorway is crossed). A fix that silently converts walks
to hops will move the hop share, the non-hop share and several levels' beat
fidelity. A/B it.

### The question the owner wants thought about deeply

> *Does the player model have an actual hitbox, and do the individual blocks?
> This would make for a far more interesting experience and simulation of
> whether a level can be completed or not.*

Here is the honest state of it, so the next agent starts from fact rather than
from scratch:

- **There is geometry for a body.** `parkourkit.body_cells` enumerates the cells
  a body occupies, and placement uses it: `Course._attempt` refuses a landing
  whose cells are occupied, and the arc of every ballistic move is checked for
  clearance against the world before the move is committed.
- **There is no runtime collision.** Nothing pushes the body out of anything
  while a run plays. The course is a list of *solved* moves and the body follows
  them. If a move was legal when it was solved, it is played; if the world
  changed underneath it, nothing notices.
- **That is deliberate and it is written down.** `CLAUDE.md`: *"Solvability is
  by construction, never by rejection sampling."* The generator's contract is
  that an illegal move is never laid, so nothing has to be caught at runtime.
- **The contract has holes, and this session found several.** The walk verb
  above. Dressing and pedestals built *after* an arc was solved (the reason
  `pathcells`, `headroom`, `softcells` and `ground` reservations exist at all).
  `spiral_probe` still measures the body inside the world on 0.02% of frames,
  which is small but is not zero, and it is exactly this class.

So the real question is not "is there a hitbox" — there is one, at generation
time — but **whether construction-time proof should be replaced or backed by
simulation-time truth.** Both are defensible and they cost different things:

- **Keep construction, close the holes.** Cheap, incremental, keeps the
  generator's guarantee. The walk fix is this. So is auditing every verb in
  `_move_for` for what it does and does not check.
- **Add a real collision model.** A body with a hitbox that is swept against
  the world each frame, and a level that is *proved* completable by simulating
  it rather than by asserting it. This is a much bigger change and it buys
  something the current design cannot: a level that is genuinely unfinishable
  becomes *detectable* instead of merely improbable, and the owner's question
  about "whether a level can be completed" gets a real answer. It also opens
  the door to the kernel changes `docs/TOWER.md` lists as blocked — jump-cancel,
  momentum, steered jumps — because those need a body that interacts with the
  world rather than a body that replays a solution.

**A specific thing worth measuring before choosing:** how often is a solved
move actually wrong at play time? Sample the body every frame across many runs
and count frames where it is inside solid, over nothing while on a ground leg,
or passing through a cell it should not. If that number is tiny, close the
holes. If it is not, the construction guarantee is already fiction and a real
model is the honest answer. `spiral_probe`'s body check is the seed of this and
currently only reports the first of the three.

---

## 1. Unlit frames: 26% against vanilla Minecraft's 17%

`tools/frame_probe.py --shoot tower --dir docs/reference/frames/vanilla_2hz:0.45`
is the measurement, and `docs/reference/frames/vanilla_2hz/` is the only
reference set that is vanilla-lit and matched in sampling rate. Everything else
in `docs/reference/frames/` is shader-rendered; comparing our flat baked light
against it measures the shader pack, which cost this project a whole false
conclusion earlier in the session.

The cause is understood. `voxel.SHADE` keeps vanilla's own face constants —
top 1.00, bottom 0.50, sides 0.60 and 0.80 — but Minecraft has skylight
carrying into shade and this renderer has none, so a grey-104 stone on an
east face lands at 62 and reads as black. The soffit and the outer wall are
already compensated per material (`conesoffit` at 206, `conebutt` at 152), which
works but is a per-material patch applied three times now.

The general fix is an ambient term: `shade' = AMBIENT + (1 - AMBIENT) * shade`.
It touches `engine/voxel.py` and therefore **all four scenes**, so it needs
frames from runner and parkour as well as the tower, and it trades against
face-to-face contrast, which is what makes cubes legible. That trade is the
whole decision and it wants judging by eye, not by the luma number.

## 2. One surface owns 38% of the frame, against the reference's 33%

The camera passing close to the cliff on corridor bends. Longest-standing
visual item in the project and the only one that survived the whole level pass.

What is already known and should not be re-derived: the exit **ladder** was 20.9%
of it and is gone (a ladder ride is the body's face against the column it must
anchor to; a stair measures 1.0% for identical designed content, a bubble
rides 4.7x faster). What is left is the core face itself. `hug` is the lever on
ordinary landings — one level took 5.7% to 1.5% by moving one beat out six
tenths of a block — but that is per level and it has now been spent on most of
them.

The method that works here, and the only one that has: bucket every jammed
frame by `blk["segment"]` **and** by move, over several seeds. Three separate
agents found their real cause that way and each had a wrong theory before they
did. `spiral_probe._lens_jammed` is the predicate.

## 3. Level openings are machinery, not design

A level's first frames are the arrival crossing from the level below, before
its first authored landing. Several agents flagged it independently; none could
reach it from inside a level module, and they are right that they cannot.

It is `handplan.Course`'s crossing and the reliability chain around it. The
symptom on a contact sheet is one or two frames of sky with a cube in them at
every level boundary — thirty-three times a cycle. Fixing it means the crossing
knowing what the level it is arriving at wants to open on, which is a real
piece of design work in the machinery rather than a tuning pass.

## 4. About 10,500 cells of cliff painted inside chasms where `rock` says air

Found during the terrace paint fix and deliberately left, because it wants its
own frames and the fix in flight was already large. In a chasm at slab heights
`Cone.rock` returns False for the whole disc, but the core ring paints there
regardless. The cells are deep inboard of the band so the course never reaches
them — but this is the invisible-geometry class, which in this project has a
history of being harmless right up until it is not. There is no `FINDINGS.md`
in this repo; this paragraph is the record.

## 5. A bubble column always draws as water

`_climb_move` styles the column `"water"` whatever `climb_style` says, so the
fastest and cleanest exit in the engine is a blue column standing in a lava
field — unavailable to all eight nether, crimson and warped levels. Three
separate agents hit this and designed around it. A `climb_style`-respecting
tint is a small change with a large return, because the alternative those
levels are left with is a stair, and the ladder is now forbidden.

---

## How to work on this tower

Four things this session learned the hard way. They are worth more than any
of the items above.

- **Judge the contact sheet with your own eyes before you look at a number.**
  Three separate metrics read green on this tower while the owner watched it
  live and said it was bad, and two of those metrics were the coordinator's own.
- **Check what a reference actually is.** Two of the three "Parkour Spiral"
  videos this project was calibrated against are shader-rendered, and one is a
  different map in the series. A whole class of conclusion had to be retracted.
- **Send a second agent whose brief is to refute the first.** The terrace paint
  bug — a third of every level's ground undrawn but still walkable — was
  introduced by the coordinator, survived every probe, and was only found
  because a read-only agent was told that refuting the diagnosis would be the
  most useful thing it could produce. The metric that should have caught it
  scored the *broken* build higher.
- **A moving roster is not a noisy metric.** While thirty-three levels are being
  rewritten in parallel, the same unchanged file measures 187, 45 and 223
  landings inside twenty minutes. Decide on in-process A/Bs — same seeds, both
  variants swapped on the live object in one run — and treat every absolute as
  approximate until the tree is still.
