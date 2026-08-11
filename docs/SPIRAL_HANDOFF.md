# Handoff: the spiral-platform rebuild

One piece of work, handed to a fresh session. Everything else in the repo is
finished and shipped; read `CLAUDE.md` first for the project as a whole, and
`docs/ARCHITECTURE.md` for how the pieces fit.

Retire this file when the work below is done and its decisions have been folded
into `CLAUDE.md` and `docs/ARCHITECTURE.md`.

## Objective

The owner's reference screenshot of a Parkour Spiral map settles what this
format actually is, and the scene that ships today gets it wrong.

- **What ships now** (`scenes/tower.py` + `scenes/towerplan.py`): a cylindrical
  stone tower. Jump blocks hang in the air *outside* the wall and spiral round
  it; interiors are rooms *inside* that cylinder. Floating blocks going round
  something, plus caves.
- **What the reference is**: a stack of **built places**. Each themed section
  is a slab of real world a dozen blocks across — a farm with crops and fences,
  a nether cave with lava and lanterns, a rainbow floor, a honey ledge —
  standing on a forest of columns, spiralling up. The parkour is two different
  things: *running over actual ground* across a platform, and floating-block
  parkour out over the drop *between* platforms.

The objective is the second one, without losing anything the first one proved.

### Acceptance criteria

Measured by `python tools/tower_probe.py` (a spiral equivalent must be written;
see "Next action"). The shipped ring version's current numbers are the bar:

| | ring version, shipping | spiral version, required |
|---|---|---|
| cells claimed twice | 0 of 263,786 | **0** |
| blocks off the integer lattice | 0 of 6,320 | **0** |
| emergency placements | 15 of 6,320 (0.24%) | **under 0.5%** |
| orbs laid but not collected | 0 | **0** |
| body inside the building | 0.33% of frames | **under 0.5%** |
| per-frame cost | 1.52 ms | **under 2.5 ms** |
| tests | 563 green | **563 + spiral tests green** |

Plus, and this is the point of the work: a run must spend most of its time on
**built platforms**, not on isolated floating cubes, and the platforms must be
visibly different places from one another.

## Verified state

`git log` head is `fd995be`. Working tree clean. On branch
`claude/project-visuals-animations-qzbkiq`, pushed.

- **`python -m pytest tests/` — 563 passed, 34 skipped** (~2 min). The Win32
  suite skips off Windows and the X11 suite skips without a display, so a green
  run here means less on the other platform's machine; check the count.
- **`python tools/tower_probe.py --runs 20 --blocks 300 --no-motion`** gives the
  left-hand column above.
- **The daemon is running the committed code** and `brainrot doctor` is 14/14.
  It is autostarted from `~/.config/autostart/claude-brainrot.desktop`; a
  restart is `pkill -f "brainrot run"` then
  `setsid /home/tristan/projects/claude-brainrot/.venv/bin/brainrot run &`.
  **The interpreter is `.venv/bin/python`** — there is no bare `python` on this
  machine, and `timeout(1)` is not available in the agent's shell.

Nothing outside Git changed except the running daemon process.

## What is already built, and where

`src/brainrot/scenes/spiralplan.py` — **unfinished, deliberately not imported
by anything.** `scenes/__init__.py` still registers only `parkour`, `runner`,
`tower`, so this file cannot affect the running scene.

It contains, and these work:

- `Spiral` — platforms on a helix, each with its own theme, columns descending
  under the rim, an `enclosed` variant with walls, a roof and lamps (the cave),
  and a per-platform `enter` / `leave` / `lane` route. Scenery is kept a cell
  clear of the lane, so the way across a platform is clear by construction.
- `Course` — subclasses `towerplan.Course`, so **all the physics, the lattice,
  the move vocabulary, the four reservations and the orb solver are inherited
  unchanged**. What it replaces is the planning layer: nodes are aimed at a
  *cell* rather than at a bearing and a radius, and the plan is the scheduled
  sequence "cross, bridge, cross, bridge" instead of a weighted roll.
- Nine bridge styles (`BRIDGES`) sharing one geometry and differing only in
  dressing, which is the right split: where a bridge goes is fixed by where the
  two platforms are.

Three defects were found and fixed in it; the fixes are commented where they
live and are worth not rediscovering:

1. **The columns of the platform one revolution above hang through the bridge
   below.** Five platforms a turn is thirty-odd blocks up and legs run
   twenty-four deep. Both are laid out by the spiral from the same geometry, so
   it can be asked — `Spiral._clear_of_bridges`.
2. **A bridge aimed at its landing spends its last stones inside the platform
   it is aiming at**, whose cells are that platform's own ground. It now aims
   at a point three cells outside the rim and steps up (`_out`, `aim`).
3. **A 2.8 m step rounded onto the lattice can land 1.4 m out**, under
   `MIN_HOP`, and the next stone is then measured from a body that never moved.
   Stones are walked outward until the *cell* is a real hop away.

## The open defect

**A bridge that arrives under a platform without having climbed enough cannot
make the last blocks.** One jump reaches 1.25 blocks; when the body is beside
the target and three or four below it, the direction toward the aim point is
made of rounding error, the stones pile up on each other, and placement fails.

Measured: **about one node in eight falls through to the unchecked answer**
(`stuck`), against one in three hundred for the shipped ring version. That is
the only reason this is not switched on.

There is a half-written answer in `Course._plan` — a flight of steps *beside*
the rim rather than under it, using `_perp` — which was **not applied to the
file** (the edit that added `_perp` failed its own assertion and was abandoned).
Treat it as a sketch, not as code that ran.

Repro:

```bash
PYTHONPATH=src .venv/bin/python - <<'EOF'
import random, collections
from brainrot.scenes import spiralplan as sp
tot = n = 0
for seed in range(1, 9):
    s = sp.Spiral(random.Random(seed * 977), 0)
    c = sp.Course(random.Random(seed * 6151), s)
    for i in range(300):
        c.spawn(); n += 1
        if len(c.blocks) > sp.AHEAD:
            c.advance(len(c.blocks) - sp.AHEAD + sp.TRAIL)
    tot += c.stuck
print("stuck %d/%d (%.2f%%)" % (tot, n, 100 * tot / n))
EOF
```

Prints `stuck 313/2400 (13.04%)`. Target: under 0.5%.

The diagnostic that found each of the three fixed causes is worth rebuilding
before guessing: wrap `Course._attempt`, and when it returns `None` for the
node's *own* cell, re-run each test in order and count which one refused it.
Guessing cost several rounds in the last session; the counter found each cause
in one.

## Next action, in order

1. **Fix the open defect.** Steps beside the rim is the sketched answer; check
   it against the counter above rather than by eye. Stop when `stuck` is under
   0.5% over 8 runs × 300 blocks, then confirm over 40 × 400.
2. **Write `tools/spiral_probe.py`**, modelled on `tools/tower_probe.py` —
   which is the acceptance test in numbers and the only reason the ring version
   is trustworthy. It needs the safety block unchanged, plus: fraction of
   *blocks* that are platform ground rather than floating stones, seconds spent
   on a platform versus on a bridge, and platforms visited per minute.
3. **Wire it in**: a `spiral` scene beside `tower`, or replace `tower` outright
   once the probe says it is at least as safe. Register in
   `scenes/__init__.py` and `config.py`'s default `scenes` list, and update the
   scene-registry test in `tests/test_generation.py`, which asserts the exact
   set of names.
4. **Look at it.** `brainrot shoot --scene spiral --seed N --frames 1200
   --every 100 --out shots/` then `python tools/contact_sheet.py shots/
   sheet.png`, and read the sheet. Every art decision in this project was made
   that way and none of them survived being reasoned about instead. The
   scratch `orbit.py` pattern — drive the scene, then park a camera 40-60 m out
   and render the building alone — is what showed the ring tower was good.
5. **Blender props kit.** This is a real gap the reference makes obvious: the
   platforms want crops, flowers, fences, lantern posts, sugar cane and chains,
   and those are cross-shaped and thin. Cubes fake them badly. Add a
   `assets/src/props_mc.py` in the same shape as the existing asset scripts,
   build with `python assets/build.py`, and **always follow a rebuild with
   `python assets/measure.py`**.
6. Fold the decisions into `CLAUDE.md` and `docs/ARCHITECTURE.md`, delete this
   file, and retire `towerplan.py`'s ring machinery only if the spiral has
   replaced it — not before.

## Constraints that must be preserved

- **The physics layer is not up for renegotiation.** `towerplan.py`'s constants
  are vanilla's, sourced; `hop_span`, `fit_gap` and `Move` are what make every
  guarantee checkable. The spiral `Course` inherits them on purpose.
- **Correctness rules never relax; comfort rules may.** `_attempt(strict=False)`
  is the seam. Empty cells, head-room, a move the physics has and a clear path
  are correctness. Room to stand and clearance from an overhang are comfort.
- **Four reservations, not one occupancy map**: `solid`, `softcells`,
  `headroom`, `pathcells`. Checking is not reserving — see `CLAUDE.md`.
- **Nothing is downloaded.** The owner has said open-source assets are allowed;
  the standing pipeline is that every asset is rebuilt from a committed Blender
  script, which is what makes `assets/build.py` reproducible and keeps licence
  questions out of the repo. Raise the trade before importing anything.
- The runner and flat parkour scenes are finished. Do not touch them except for
  shared-engine changes, and re-run `tools/depth_probe.py` and
  `tools/frame_cost.py` if you do.
