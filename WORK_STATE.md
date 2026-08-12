# Handoff: landmarks IN the parkour (task #12) — for a fresh session

The owner ended the 2026-08-12 marathon session with this steer, verbatim in
spirit: *landmarks should be blocky and integrated into the parkour in some
way* — the course jumping through a windmill's doorway, over a bell frame,
up a watchtower — not scenery standing beside the path. That is also how the
real map does it (its checkpoint legs run through temple halls, barrel
silos, libraries; see docs/TOWER.md § "What the reference actually does").
Everything below is what a fresh session needs. Read docs/TOWER.md first;
the project CLAUDE.md's tower section predates phases 2–3, so trust
TOWER.md, this file and `git log` over it.

## Where things stand (all shipped, live, pushed — HEAD 4fe8726+)

- 33 hand-built levels (`scenes/handlevels.py` data, `handplan.py`
  machinery, `spiralplan.py` engine). Probes and targets in docs/TOWER.md.
- **Locks** (this is the pattern to copy): every level's first floor break
  is 5.5–6.7 wide — unjumpable — and `handplan.Course._lock_nodes`
  machinery-inserts course beats that cross it (approach at height, island
  float, far landing) when the frontier approaches the break. Course
  geometry tied to a world feature, inserted between script beats, cursor
  untouched. Measured: 0% of levels fully bypassable, 46% mean walkable
  coverage vs the real map's exactly-comparable 50%/0
  (`scratchpad/bypass_probe.py` — copy it into tools/, it is THE
  walkability criterion now; the in-repo `runnable` metric is cone-alone
  and misleading).
- **Landmark reservation** (the other half of the pattern): the moment a
  section enters the horizon, `Course._reserve_landmark` lays the
  blueprint out at the apron (deterministic per-level rng
  `random.Random(section.index * 977 + cone.wind * 31)`) and holds its
  exact cells; placement/arcs/shells/pours/dressing respect
  `self._hold_cells`; `Course._landmark` redeems at paint time. 97% place.
  `Cone.marks[section index] = centroid` feeds the camera glance
  (spiral.py `_look`: leans toward the mark while running).

## The task

Make the course PASS THROUGH landmarks on at least the big-structure
levels: windmill (door at dy 1–2, dr -2 side faces the course), watchtower
(over or through), bell frame (under the beam, over the posts), arch
(already course-adjacent via ceiling beats — verify), great cap (onto the
cap?), cabin (through: it already shells the CORNICE beat — different
level though). Approach:

1. In `_reserve_landmark`, also compute and store 2–3 **crossing nodes**
   in the level frame (entry point before the structure, a landing in the
   doorway/on the roof, an exit landing past it) — the blueprints already
   carry a doorway-ish gap on the course side (windmill glow at dr=-2).
   Reserve must NOT hold the crossing cells (the course needs them —
   exempt them like the lock's island).
2. Insert the crossing like `_lock_nodes` does: when the frontier is
   within ~8 blocks of the landmark's bearing, emit the stored nodes
   (label them, e.g. "landmark"), cursor untouched. The doorway cells must
   be *carved/kept open* through the reservation so the checker accepts
   the pass-through (headroom over the doorway landing must not collide
   with held cells — drop held cells that sit in the crossing's headroom
   at reserve time).
3. Structures may need doorways widened in the blueprints (body needs
   2-cell clearance; windmill tower is 3x3 with dy 0-2 walls — cut a
   2-high, 1-wide gap on the course side in the blueprint itself, facing
   dr negative).
4. **Visibility metric before claiming done**: extend the motion probe (or
   `scratchpad/snap_probe.py` pattern) — per run, does each crossed
   landmark subtend a meaningful angle (>10°) for >1.5 s? The owner
   watched five minutes live and saw one structure; that number is the
   acceptance criterion, not placement rate.
5. Re-run the standing battery after (below), especially bypass_probe —
   crossings must not create new walkable routes (a doorway at ground
   level through a structure the walker can enter is fine ONLY if it dead
   ends; prefer crossings entered from height, like the locks).

## Standing verification set

- `scratchpad/bypass_probe.py` (copy to tools/): expect ~0% full bypass,
  40–55% coverage.
- `tools/tower_probe.py --design-only` (instant) and `--runs 6 --blocks
  240` (fidelity ≥90; currently 91.5 after locks).
- `tools/spiral_probe.py --plan tower --runs 6 --blocks 200 --no-motion
  --walk-runs 4`: twice-claimed 0, unchecked ≤0.4%, cone-walk 0 m.
- `pytest tests/test_tower.py tests/test_spiral.py` (59 green).
- `tools/level_shot.py --level "WINDMILL" --seed N --sheet` — the eye.
  Harness must patch `sp.Cone.__init__` (base), never handplan's (skips an
  rng draw, renders a different world — comment in the file).
- Ship = commit AND push AND restart the daemon:
  `pkill -f "brainrot run"` (NEVER in a compound command with other
  steps — pkill -f matches the wrapping shell snapshot and kills the
  command itself, exit 144), then
  `setsid nohup .venv/bin/brainrot run >/tmp/d.log 2>&1 & disown`.
  Hooks do NOT auto-spawn the daemon.

## Landmines specific to this task

- Reserving a section lazily creates the section three above
  (trough_height) — never iterate `cone.sections` while reserving;
  spawn() bounds to the frontier neighbourhood.
- Reserve-and-paint must agree: both derive from the same per-level rng
  and the same anchor math (`_try_reserve_at`); if the crossing nodes are
  computed at reserve time, store them — do not recompute at insert time.
- The apron/anchor is clamped to the first 0.55 of the arc (exit stair
  owns the wall lane past that) and the lock's wide break avoids the apron
  by 5.5 — crossings live inside that same guarded window, so a landmark
  crossing plus a lock plus the script must all fit: on short terraces the
  lock already moves (`floor_breaks` shift loop); if the crossing and lock
  collide, move the LOCK, not the landmark.
- A/B honestly: any generation change re-rolls worlds. The reserve path
  has its own rng stream, so monkeypatching `_reserve_landmark` to a
  no-op is a clean same-world toggle.
- Landmark placement is whole-or-nothing (bounded accent skips) — keep it
  that way; a hollowed windmill with floating sails was the bug that rule
  killed.

## Also queued (smaller, from the same owner feedback)

- Camera wall-clip frames measured at 0.12% (`scratchpad/snap_probe.py`
  buckets them); if the owner still reports through-wall reads, add a
  camera-vs-solid nudge in the renderer.
- Fidelity recovery toward 95%: script beats that land over wide breaks
  fall back nearby; teaching `_choose_feature` to pre-shift an authored
  beat's arc when it would straddle the level's wide break would recover
  most of the 4 points.
