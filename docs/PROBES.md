# Dev loop and probes

Moved verbatim from `CLAUDE.md` on 2026-09-02. `CLAUDE.md` keeps the short
table of which probe to re-run after touching what; this is the full
description of each tool, what it measures and the traps in reading it.

- `brainrot shoot --scene runner --seed N --frames 240 --every 40 --out shots/`
  renders exact frames of exact runs to PNG. This is how all art direction
  was done: render, look, adjust, repeat.
- `python assets/build.py [name]` rebuilds committed .glb files from their
  scripts, one subprocess per asset. It needs a working `bpy` and finds one of
  two ways: the **wheel**, imported by the venv's own Python, or a
  **standalone Blender** driven as `blender -b -P script`. The wheel trails
  Python releases and there is none for 3.14, which is what the venv is — so
  on this machine it is the standalone, unpacked at
  `~/.local/share/blender/5.0.1/`. `python assets/build.py --where` says which
  it would use and prints the install recipe when there is neither;
  `BRAINROT_BLENDER` forces a particular binary.

  Verified 2026-08-11: a full rebuild of all sixteen assets through that path
  reproduces every recorded bound and every recorded pose frame exactly — the
  24 checks in `tests/test_assets.py` pass against the *committed*
  `metrics.json` without re-measuring, and the whole suite stays green on the
  rebuilt files. Nine of the sixteen .glb files differ in bytes afterwards;
  that is bake noise and nothing else, which is what "byte-for-byte-
  equivalent" in `docs/ARCHITECTURE.md` has always meant.

  **Always follow a rebuild with `python assets/measure.py`.**
- `python assets/preview.py <asset>` and
  `python assets/animstrip.py character run` render assets/clips for review.
  `preview.py` works on this machine as of 2026-08-12 -- it used to come back
  black and colour-inverted, see the landmine below.
- `python tools/runner_probe.py --runs 12 --seconds 120` is the runner
  scene's acceptance test in numbers, and the only way "it feels boring" was
  ever going to be actionable. Three sections: **safety** (obstacles inside
  each other, the body inside an obstacle, plans with no answer), **pacing**
  (how often the runner is forced to act, the distribution of the idle
  stretches between those moments, the obstacle mix, the set-piece mix, and
  the speed at 0/15/30/60/90 s), and **riding** (mounts, roof-to-roof
  crossings and seconds on a roof per minute, what share of the trains laid
  are actually moving, and "surface pops" — a body teleported upward by a
  surface, which is what a badly built ramp looks like), plus **wrecks** and
  seconds spent flying. `--safety-runs 60 --safety-seconds 180` is the full
  sweep the collision model is held to; it **pins the creep off**, as
  `tests/test_collision.py` does, so it speaks for the guaranteed range and
  not for the deliberately-unsolvable end of a run. The criterion is a *depth*
  rather than a count -- nothing may reach `CRASH_DEPTH` inside that range,
  and a wreck past it is the scene working as intended. Read that one before
  anything else, and re-run the full sweep after touching the runner, because
  4 runs x 40 s reads clean on faults that 60 x 180 finds.
- `python tools/speed_probe.py --runs 12 --seconds 240` is the other half, and
  it is what made "it taps out at a low speed while it's still easy"
  actionable: nothing is pinned, and **every frame is bucketed by the speed it
  was drawn at**, so how long a run lasts, how fast it was going when it ended,
  and whether anything actually breaks at a given speed are readings rather
  than beliefs. Three beliefs recorded in this file did not survive it -- see
  "The speed has no top". Run it after anything that touches the speed curve,
  `pressure`, or the planner's horizon.
- `python tools/flow_probe.py --scene all --runs 4 --seconds 25` is the
  parkour family's *motion* acceptance test, and the only thing that could
  make "it looks bot-like and rickety" actionable. It measures the derivative
  of the camera and nothing else: how long the feet are on the ground, the
  one-frame change in ground speed, the one-frame **acceleration** of the eye
  (a step in position and a smooth fall are the same first difference and
  nothing else tells them apart), the field of view, the yaw, and the apex of
  each hop against the 1.25 m every vanilla jump reaches. The take-off's own
  step is counted separately and forgiven by name -- it is instant in the real
  game too. Re-run it after touching anything in `parkour.py`, `spiral.py`,
  `parkourkit.GroundRun` or `parkourkit.spend_impulse`. **The apex row is the
  one to read for "does it feel like a Minecraft jump"**, and it is trustworthy
  only since 2026-08-18: it segments hops by the scene's own `landings` counter
  and takes each launch height from `land_y`, because a landing is now often
  shorter than a frame and a frame that reaches across a take-off has the body
  already part of a jump up.
- `python tools/level_review.py --level N --all` is **the** per-level tool and
  the one to reach for when a level is being designed rather than the tower.
  Four artefacts in `shots/review/lNN_slug/`: the game camera over the level
  and into the next (`frames.png`, the judge); a **blueprint** — elevation and
  plan of the built world, which is the only view that shows ground running
  unbroken past three of your jumps; the level as solid geometry rendered
  orthographically in Blender (`--outside`); and the numbers for that level
  alone — per-beat fidelity, move mix, no-jump walk coverage, body inside the
  world, how much of the frame is empty sky, and how long its structure is on
  screen. `--seam` prints what the level below hands it and what the level
  above opens with. **One level per process**: the phase pin is a class-level
  patch and the tool refuses a second.
- `python tools/level_climb.py` prints what every level does *vertically* --
  the height of each authored landing over its own terrace, the deck the
  filler holds, and what the exit still has to climb (`rise + 1 - deck`).
  Instant, builds nothing, and it is the reading tool for the rehash: `low`
  under 2 on any level is a landing a fall can walk back onto. One level's
  name as an argument prints that level landing by landing.
- `python tools/tower_probe.py --runs 16 --blocks 340` is the hand-built
  tower's acceptance test *for the design*: every authored jump checked against
  the physics on paper (`--design-only` needs nothing built and is instant),
  then how much of the design survived being placed, per level and per beat.
  Run it after touching a level. A beat under 98% is a design to look at.
- `python tools/endurance_probe.py --hours 1 --runs 4 --levels` is the only
  probe here that asks whether the thing ever *stops*: one simulated hour a
  run, every landing checked for a stall, a give-back or a level it cannot
  leave, plus the distribution of how far a landing carries the body along the
  corridor. Ten minutes, no window. Run it after anything that touches
  placement or the exit climb. **Its per-level table is only trustworthy
  because visits are segmented by the crossing and labelled by `to_level`** --
  see "Left alone for an hour" for the three false alarms that cost.
- `python tools/ride_shot.py --scene spiral --seed 3 --kind climb` renders every
  frame of one ladder climb, bubble ride or web wade, plus the second either
  side, and tiles it. A ride is two seconds long and arrives somewhere nobody
  chooses, which is how the ride camera spent months aimed at the wrong thing
  with every number green. `--kind bubble` for the underwater one. **Look at
  the individual frames as well as the sheet**: a twenty-frame sheet at strip
  size is too small to see that the ladder is missing.
- `python tools/arc_probe.py --runs 8 --blocks 300` is the acceptance test for
  *"there are blocks in the way and the player just passes through them"*, and
  it is the only probe here that asks about what is **drawn** rather than about
  what is solid -- which is where three whole classes of defect were hiding.
  It walks every committed move the way the body plays it, samples the body's
  swept volume **by distance**, and reports what is inside it with the
  **provenance of the offending cell** (course block, pedestal, lid, shell,
  bridge, landmark, prop, terrain paint, cone) and with whether that cell was
  written *before or after* the arc it blocks -- which is the number that
  decides whether the fix is "reserve more" or "fix the writer". It counts
  three things nothing else ever has: the body through non-solid **furniture**,
  the **camera** inside anything, and **ghosts** (drawn, released by `advance`,
  never un-drawn). `--dump run,index` prints one move sample by sample; every
  cause found in this pass was invisible in the aggregate and obvious in one
  dump. `--path --run N --blocks 760` prints the whole course as a table --
  block to block, distance, rise, move, cumulative simulated seconds -- and is
  what `docs/reference/tower_path_run0.txt` was produced with. No window, about
  two minutes. `docs/PATH.md` is the write-up.
- `python tools/walk_probe.py --plan tower --runs 12 --blocks 240` asks whether
  a *solved* move is still legal when it is played: it walks every committed
  move against the world as it stands `AHEAD` landings later, which is where
  the body is, and asks whether anything solid is inside the body and -- on a
  leg the body is on its feet for -- whether there is ground under them.
  Nothing had ever asked the second question, and the answer was that **98% of
  walk legs crossed air** (see `Course._walk_bridge`). Check it after touching
  any verb in `_move_for`. Needs no window.
- `python tools/spiral_probe.py --plan tower ...` is the same probe's *safety*
  half pointed at the hand-built tower. The two towers are the same building
  and the same physics, so every number means the same thing for both and the
  hand-built one is held to what the generated one reached.
- `python tools/spiral_probe.py --runs 24 --blocks 280 --motion-runs 6
  --seconds 35 --walk-runs 6` is the spiral scene's acceptance test in numbers,
  and it is self-contained -- it imports nothing from another probe. Four
  sections: **walkability** (the one this rebuild exists for -- a walker let
  loose on the *cone alone*, no course blocks, no pedestals, no dressing, that
  may step one block up and drop any survivable distance; anything but 0 m
  means the levels are not levels), **safety** (cells claimed twice, landings
  off the lattice, ladders and water inside rock, emergency placements, and
  whether the body is ever inside the world), **the course** (how many landings
  are the level's own ground or something built down to it rather than a cube
  hung over the drop, plus the move mix, the feature mix, the themes seen, and
  the hop distribution and its ramp), and **the climb and pacing** (metres a
  second gained, revolutions a minute, seconds on one theme, the idle between
  moves, dead air, frozen frames, and how much of the lens is clear ahead).
  `--no-motion` needs no window at all, because `scenes/spiralplan.py` imports
  no renderer -- and neither does the walk, so both are seconds.
- `python tools/landmark_probe.py --runs 6 --seconds 40` asks whether a
  level's signature structure is ever *seen*: a real run, frame by frame,
  through the real camera, counting a structure when it holds 10/25/40
  degrees, unoccluded and in frame, for a second and a half. Placement rate
  was the number that stood in for this and it was wrong -- 97% placed, 18%
  ever framed. Currently **55% of levels at 25 degrees, 30% at 40, 2.75 a
  minute**.
- `python tools/bypass_probe.py --runs 6 --blocks 240` walks the **built
  world** -- cone, course, pedestals, terrain, shells, landmarks -- one cell
  at a time, up one, down any drop, never jumping, and reports how much of a
  level it covers. This is the walkability criterion for the hand-built
  tower; `spiral_probe`'s cone-alone walker answers a different question and
  reads as if levels were much harder to walk than they are. Currently **47%
  mean, 0 of 42 levels walkable end to end**, against the real map's 46% and
  0 of 43.
- `python tools/reentry_probe.py --runs 6 --blocks 260` is the acceptance test
  for the parkour rehash (`docs/REHASH.md`), and it is the owner's own
  criterion as a number: a body that misses a jump and then *walks* -- up one,
  down any, never jumping -- must not arrive back at any landing of that level
  but its **entry apron**. A miss is **dead** (the void, or ground connecting
  to nothing), **back to the start** (fine, and the wanted outcome), or a
  **shortcut** (the defect: the fall cost nothing and every jump before the
  re-entry point was decoration). Also floor contact -- landings resting on the
  terrace, by pedestal or directly -- the apron's own size, and what the level
  climbs. **Shortcut 87.9% before the rehash and 2.0% after, on one level of
  thirty-three.** Ten seconds, no window. `--levels [--only NAME]` is the
  per-level table to author against; `tests/test_reentry.py` holds the walker
  itself against worlds checkable by hand, and the four things it has to get
  right before its number means anything are in `docs/REHASH.md` section 6 --
  the shortest of them being that walking is not symmetric, so it searches
  backwards.
- `python tools/parkour_probe.py --runs 24 --motion-runs 12` is the parkour
  scene's acceptance test in numbers: interpenetration, grid alignment,
  emergency hops, the hop distribution and its ramp, and whether the body ever
  ends up inside a block. Currently: **0 overlapping pairs, 0 emergency hops,
  100% on the grid, 0% frozen frames, body worst case 0.042 m.**
- `python tools/depth_probe.py --scene tower` says what each translucent draw
  is hiding in the spiral family. The one that is not zero is `guards`, which
  switches `no_depth_write` off scene-wide and is this scene's answer to
  `--legacy`. Read the two instrumentation notes in the suspect table before
  adding a suspect: both of the traps they describe read as a clean pass.
- `python tools/depth_probe.py` says what each translucent draw is hiding, by
  re-rendering the frame with that one draw's depth writing turned off and
  counting the pixels that change -- and again against a silhouette of the
  course alone, which is the number that matters. Everything reads 0 now.
  `--legacy` reconstructs the pre-fix draw order in the same process, which is
  where the before numbers come from.
- `python tools/frame_cost.py` times **all four** scenes in one process with
  vsync off and reports every one against the first asked for. Absolute
  milliseconds off a busy machine are worthless; those ratios are not.
- `python tools/atlas_sheet.py out.png` shows every block pattern at texel
  scale *and* at block scale. Judging a texture at 8x is how the first set
  ended up as four enormous bricks and a chequerboard.
- `python tools/contact_sheet.py <shots dir> sheet.png` tiles a whole run into
  one image. A single frame can be flattering by accident; what needs judging
  is whether the course stays in shot from hop to hop.
- On a machine without a display or GPU:
  `pip install raylib-software --force-reinstall --no-deps` swaps in the
  software rasteriser (CI uses this; colours/output match the GPU build).

