# The path, and what is in the way of it

Two questions this project could not answer until 2026-08-20, both asked by
the owner after watching the tower live:

1. **What is the course, actually?** Not "how many landings a level places" --
   the whole run, landing by landing: which block to which block, how far, how
   much rise, which move, and how long it takes.
2. **What is standing in the middle of it?** *"Many jumps look impossible
   because there are blocks in the way, but the player just passes through
   them, and they look off -- they don't belong there at all."*

`tools/arc_probe.py` answers both. It grows a real course headless, walks
every committed move the way the body plays it, samples the body's swept
volume **by distance** rather than by a fixed count, and asks the *drawn*
world what is inside it -- with the cell's provenance, so every finding names
the code that wrote it. `--path` prints the first question's answer as a
table.

    python tools/arc_probe.py --runs 8 --blocks 300        # the audit
    python tools/arc_probe.py --path --run 0 --blocks 760  # the whole course
    python tools/arc_probe.py --runs 8 --blocks 300 --dump 2,148   # one move

Both need no window and no renderer; a full sweep is about two minutes.

---

## 1. The path

`docs/reference/tower_path_run0.txt` is the committed artefact: run 0, 786
landings, every level of the cycle. One row per landing --

    idx  level  lv  author  beat  origin  terrace-y  surface-y  lift  cell
         material/form  move  distance  rise  cumulative-seconds

`level` is where the landing physically *is*; `author` is the level whose plan
emitted it, and the two differ wherever a level's exit spills over a boundary
(`CLAUDE.md` explains why both are kept). `lift` is height over that level's
own terrace, which is the number the whole design is written in.

**The tower does not end -- it loops**, and the numbers for one full cycle are:

| | |
|---|---|
| levels in a cycle | **33** |
| landings in a cycle | **786** (run 0; varies a little by seed) |
| simulated length of one cycle | **356 s** -- five minutes fifty-six |
| blocks climbed | **325** gross, **+198** net of the descents |
| where a five-minute turn ends | landing 664 of 786, THE WEIR |
| mean landing rate | 2.2 a second |

A thinking turn almost never sees a whole cycle. The tower starts at a random
level (`Cone.phase`), so two runs a minute apart open in different places on a
building the viewer comes to recognise -- which is the entire reason to
hand-build one.

### Reading a row

    17  THE PILLARS   5  BASALT FLUES  ascent  crossi  32  32.0  0.0
        (15,31,28)  purpur/floor  hop  3.49  -1.0  7.53

Landing 17 is the **crossing**: the jump over the chasm at the end of BASALT
FLUES onto THE PILLARS' own terrace. It is authored by the level being left,
it lands on built ground (`form=floor` places no block of its own), it
descends a block -- which is what makes the widest chasm crossable at all,
because falling takes longer and the body does not slow down while it does --
and it happens 7.53 s into the run.

---

## 2. What was in the way

Measured on the hand-built tower, 8 runs × 300 landings = 2,408 moves.

| | before | after |
|---|---|---|
| moves passing through something drawn | 1.83% | **0.96%** |
| worst penetration | 0.600 m | 0.575 m |
| **the body through a piece of furniture** | **31.9%** | **0.21%** |
| **the camera inside a piece of furniture** | **2.57%** | **0.00%** |
| the camera inside a drawn cell | 0.29% | 0.17% |
| drawn but not solid ("ghosts") | 0.50% | 0.33% |

Five separate causes, none of which was visible in the aggregate and none of
which was found by reading the code.

### The sampler said 0.2 m and delivered 1.13

`Move.points` sampled evenly **in time** at a fixed seventeen points, with a
note claiming that put them 0.2 m apart. It did not. A seven-and-a-half-metre
descending hop is 0.44 m a sample, and any move whose legs run at different
speeds -- a ladder's step-in, ride and step-off -- gives the slow leg nearly
all seventeen and the fast ones none. Measured over 1,950 committed moves the
largest gap had a median of 0.27 m and a **worst of 1.13 m: wider than a
cell**, so a whole block could sit between two tests.

The consequence is not a check that is wrong where it looks. It is that the
same points are what `Course._commit` reserves as `pathcells`, so a cell the
arc passes through but no sample lands in is never reserved and terrain laid
afterwards is free to fill it.

`ARC_STEP = 0.3` and a per-leg closed-form step count. Worst gap 1.134 m ->
**0.300 m**, moves sampled coarser than the body is wide 1.9% -> **0**, and it
is free: 4 runs × 300 landings takes 30.2 s against 31.0 before.

### A lamp is a lit cube in the middle of the block you land on

`_decorate`'s `lamp` was a 0.62 m cube at `dy = 1.0` -- dead centre of the
landing's walking surface, and `deco` is `solid=False` by design. The landing
is one cell, the body is 0.6 m wide and lands on the middle of it, so the
runner went **through** a glowing block on 31.9% of all moves, and the camera
was inside one on 2.6%. Thirty-nine lanterns, twenty glowstone and ten magma
against three stray lintels.

A lamp hangs *under* the landing's leading edge now, which is where a lantern
hangs in the reference anyway and which is the face you can see on the way in
to a landing above you. A `post` goes to a back corner.

### A lintel was a beam through the runner's chest

`deco="lintel"` sat at `apex + 0.35` -- **the apex of the feet**. A body is
1.8 m tall. On a `walk`, which is what most lintels are written on because a
doorway is walked through, the apex *is* the walking surface and the beam was
at knee height. Over the head at the arc's highest point now.

### A head-hitter's clearance was the feet's, not the head's

`_ceiling_cells` refused an arc whose *path* went above the lid. Same mistake
one layer down, and lids were the largest single writer of cells inside the
body: 17 moves at up to 0.543 m, and four of the seven moves that put the
camera inside a drawn cell.

Simply refusing those was not available. Since every jump spends the whole
impulse (2026-08-18) every hop apexes about 1.25 m over its take-off, so "apex
plus a body under a lid at three" excludes *all* of them and 244 of the
roster's 276 lids stop being buildable. So the lid **rises to clear the head**
and only refuses when that would take it past `LID_MAX`, where it stops
reading as a beam and starts being the roof of a room -- which a level would
have asked for with a `shell`. A flat walk keeps its lid at three, which is
the case the doorways are written for. Fidelity is unchanged: 94.7%.

### A walk onto a slab laid full cubes around the shins

`_walk_bridge` picked its support cell with `ifloor(y - 0.05)` at each sample,
which is right only when the foot height is a cell top -- and a walk joining
two surfaces half a cell apart (a full block to a slab) is never at one in the
middle. It laid full cubes spanning the body's own shins: **5.4% of all walks,
and every 0.600 m reading in the table.**

Moving the shelf under the *lower* end is the obvious fix and it is wrong the
other way -- it leaves the feet in mid-air, which
`test_a_walk_never_crosses_air` catches. There is no third cell: `line_leg`
interpolates height linearly, so a half-block walk is a **ramp**, and a ramp
cannot be built out of whole cubes at all.

Refusing half-block walks outright works and costs two points of design
fidelity (94.7% -> 92.7%), because a third of the roster writes walks by name
and some of them land on slabs. What costs nothing is to stop the walk being a
ramp: it is **flat, and then a step** -- one leg at the take-off's height for
all but the last `STEP_UP` metres, and one short leg rising onto the landing,
which happens over the landing's own footprint. The flat leg gets an honest
shelf, the step gets the block it is stepping onto, and `_walk_bridge` lays
nothing under a rising leg. That is also what the game does: half a block is
walked up, not jumped. `bridge` disappears from the offender table entirely
and fidelity stays at 94.7%.

### A lid outlives the jump it was built for

`advance` releases a landing's cells from the occupancy map when it falls off
the back of the course, and the renderer never un-draws them. For a pedestal
that is right -- it is built ground standing on the terrace, and it is what
the levels below you are made of when you look down. For a **head-hitter** it
is not: a lid is a beam hanging in mid-air whose only justification is the
jump underneath it, and released it becomes a block floating over the course
that the next revolution's arcs fly straight through, because `blocked()` has
correctly forgotten it. Fifteen of seventeen ghost cells were lids, and one
was flown through twice running. `advance` writes air for them now.

---

## 3. What is left, and where it is

- **0.96% of moves still pass through something drawn**, worst 0.575 m, and
  **91% of the offending cells were laid before the arc that hits them was
  solved.** That number is the reason the fix is never "delete afterwards":
  the three reservation ledgers are doing their job and nothing meaningful is
  being painted into a solved arc.
- The biggest remaining writer is **`landmark`** -- 5 moves, 21 cells -- which
  is the gated structure the course is deliberately steered *through*. Worth
  looking at whether the held passage is wide enough at the shoulders.
- **`lid` still ghosts on 9 cells.** The un-draw covers lids released with
  their landing; these are not, and the mechanism is not yet known.
- **Grazes: 23% of moves come within 0.25 m of something solid**, overwhelm-
  ingly `cone:core` -- the body running close to the wall, which is what
  `hug` asks for. Reported, not gated.
- **One unchecked emergency placement produced a 26.76 m "hop"** through 118
  cone cells. That is `CLAUDE.md`'s outstanding item 0a; the probe now
  attributes it rather than guessing. It has not been seen since the exit
  climb stopped aiming at the wrong chasm, but it is not proven gone.
