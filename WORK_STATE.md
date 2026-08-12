# Checkpoint: the honest-metrics reckoning (2026-08-12, phase 3)

The owner watched the live strip (daemon confirmed running commit 875cd0c —
what he sees IS the shipped state) and reported: ~70% of a level walkable,
structures almost never visible, through-wall moments, an occasional
teleport a stage down. He is right, and the root cause is that three
acceptance metrics measured the wrong thing. His standing rule fired again:
when it measures clean and looks wrong, the metric is wrong.

## The three metric failures, measured this session

1. **Walkability counted the cone without the course.** The course's own
   pedestals and lift-1 landings are stepping stones. New honest probe
   (`scratchpad/bypass_probe.py`): walker over the world AS BUILT with lazy
   jumps (clears 3-cell gaps flat, 2-cell rising) — **ours: 76% of a
   level's arc coverable, 5% of levels fully bypassed**. Same walker on the
   real map (`realworld.json` + `plates.json`): **50% coverage, 0/43
   bypassed**. Target = close the 26-point gap. Task #11 carries the fix
   design (wide 5.5-7 breaks + machinery-inserted elevated lock crossings +
   floating stretches). NOTE: the in-repo `runnable` metric in
   spiral_probe.py is the cone-alone one — replace or relabel it, and put
   bypass_probe (course-inclusive) into tools/ as the real criterion.
2. **Landmarks measured placement, not visibility.** 97% place, on outboard
   apron bulges; the aim (landing-lock + tangent) never frames them. Owner
   saw one structure in ~5 minutes. Task #12: camera glance behavior +
   course-adjacent/through-structure placement + a visibility metric
   (subtended angle over time in the motion probe).
3. **Phasing probe checked the cone only.** Owner still sees through-wall
   moments and an occasional full-stage-down teleport. Task #13: extend
   `scratchpad/phase_probe.py` with frame-displacement snap detection
   (>2.5 m/frame) and eye-near-solid wall-clip counting; suspects for the
   teleport: crossing re-aim, recovery placements, advance() index
   arithmetic, the loop seam.

## What IS confirmed live and working

Daemon runs latest; floats above the drop, breaks, fences, authored exits,
pours, per-level bands all live. The chasm + exit climb DO stop full bypass
(5%). The spiral loops seamlessly by construction (level 33 exit lands on
level 1, tests assert the cycle: `test_the_tower_loops`).

## Standing verification set (updated)

- `scratchpad/bypass_probe.py` — THE walkability criterion now (76% → aim
  ~50%; real-map comparison script inline in session history).
- tower_probe --design-only / --runs 8 --blocks 260 (fidelity ≥90; last:
  95.9%).
- spiral_probe --plan tower (unchecked ≤0.4 — P2 raised with the landmark
  reservation trade, docs/TOWER.md).
- pytest tests/test_tower.py tests/test_spiral.py (59 green).
- After any ship: restart daemon —
  `setsid nohup .venv/bin/brainrot run > /tmp/daemon.log 2>&1 & disown`
  (pkill first; hooks do NOT auto-spawn it).

## Landmine log for this code area (fresh ones)

- Iterating `cone.sections` while reserving landmarks builds the tower
  forever (trough_height lazily creates section i+3). Bounded to frontier
  neighbourhood in spawn().
- pkill/pgrep -f in a compound Bash command matches the command's own
  shell-snapshot eval and kills it (exit 144).
- A/B across ANY generation change re-rolls worlds; only same-world
  toggles (the landmark reserve uses its own rng stream, so monkeypatching
  it to a no-op is a clean toggle) are honest.
