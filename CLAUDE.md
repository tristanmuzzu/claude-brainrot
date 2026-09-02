# claude-brainrot: project context

A generated 3D "brainrot" strip that stands beside the Claude Code window
while Claude is thinking and fades when it stops. raylib renderer, glTF assets
baked by the Blender scripts in `assets/src/`, worlds generated per seed. Four
scenes: `runner` (a Subway-Surfers convoy runner that rides train roofs),
`parkour` (first-person Minecraft parkour on the flat), `spiral` (the same
parkour up a generated cone of levels) and `tower` (the spiral renderer
against thirty-three hand-built levels in `scenes/levels/`). The default
rotation plays `runner`, `parkour`, `tower`.

`docs/ARCHITECTURE.md` says how the pieces fit and is current. This file is
the short guide. The build diary that used to live here is `docs/HISTORY.md`;
open it when you need to know why something is the shape it is.

## Run, test, iterate

```
pip install -e ".[dev]"
pip install raylib-software --force-reinstall --no-deps   # only without a display or GPU
brainrot install              # Claude Code hooks, plus the gnome-shell extension on Linux
brainrot doctor               # the per-machine check, both platforms
brainrot extension status     # the gnome-shell half alone
brainrot demo --scene tower   # watch a scene in a normal window, no chord needed
brainrot shoot --scene runner --seed 3 --frames 240 --every 40 --out shots/
python -m pytest tests/       # about 270 s
```

Art direction is done by looking at `brainrot shoot` frames and
`tools/contact_sheet.py` sheets, never by reading a number alone. The probes
below are the acceptance criteria in numbers; each one's full description, what
it measures and the traps in reading it are in `docs/PROBES.md`. Re-run:

- `python tools/runner_probe.py --safety-runs 60 --safety-seconds 180` after
  anything in `scenes/runner.py` or `runnerplan.py`. 4 runs x 40 s reads clean
  on faults that 60 x 180 finds; `tests/test_collision.py` covers the same
  ground in suite-sized form.
- `python tools/speed_probe.py --runs 12 --seconds 240` after the speed curve,
  `pressure` or the planner's horizon.
- `python tools/flow_probe.py --scene all --runs 4 --seconds 25` after
  `parkour.py`, `spiral.py`, `parkourkit.GroundRun` or `spend_impulse`. The
  apex row is the one that says whether it still feels like a Minecraft jump.
- `python tools/parkour_probe.py --runs 24 --motion-runs 12` after parkour
  generation. Expected: 0 overlapping pairs, 0 emergency hops, 100% on grid.
- `python tools/level_review.py --level N --all` while designing one level
  (one level per process), then `python tools/tower_probe.py --runs 16
  --blocks 340` (a beat under 98% is a design to look at) and
  `python tools/reentry_probe.py --runs 6 --levels` (shortcut re-entries must
  read zero; the criterion is `docs/REHASH.md`).
- `python tools/walk_probe.py --plan tower --runs 12 --blocks 240` after any
  verb in `_move_for`.
- `python tools/endurance_probe.py --hours 1 --runs 4 --levels` after anything
  touching placement or the exit climb. Ten minutes, no window.
- `python tools/arc_probe.py --runs 8 --blocks 300` and
  `python tools/depth_probe.py --scene tower` after anything drawn in the
  spiral family; `--dump run,index` shows one move sample by sample.
- `python assets/build.py [name]` after an asset script, then **always**
  `python assets/measure.py`. `build.py --where` says which Blender it found.

## Current state (2026-09-02)

- Live branch is `main`; the rebuild branch `claude/project-visuals-animations-qzbkiq`
  named in older docs is behind it.
- Last recorded suite: 682 passed, 34 skipped (Win32 skips off Windows, X11
  skips without a display, so check the count on the other platform).
  `test_overlay_x11.py::test_the_states_survive_being_hidden_and_shown_again`
  has flaked once; re-run before believing a failure.
- `GENERATION_EPOCH` is 4. A bump was tried on 2026-08-22 and reverted: it
  re-rolls the runner's test worlds too, and two runner tests pin
  world-dependent facts. Bump only with a full run to prove it.
- The Linux port is verified live on Ubuntu 26.04 / GNOME 50.1 (Wayland). The
  strip is an XWayland window; everything about other windows comes from the
  gnome-shell extension in `src/brainrot/extension/` over the daemon's UDP
  port; the top-bar switch (gsettings `overlay-enabled`) toggles it. The Win32
  suite was repaired on 2026-08-22 and still needs one run on a Windows box.
- Backlog: `docs/OUTSTANDING.md`. Defect ledger: `FINDINGS.md`.

## Landmines most likely to bite today

The whole list, Windows ones included, is `docs/LANDMINES.md`; read the entry
matching your symptom before theorising.

- The software rasteriser (CI, `raylib-software`) honours neither the depth
  mask nor alpha blending, so the tests that hold `no_depth_write` and the
  batch-order fix skip there (`conftest.software_rasteriser`).
- Never resize the shared test window or open a second one; every drawing test
  goes through `conftest.ensure_window()`. RLSW does not reallocate its
  framebuffer, and the crash is reported wherever the heap is next touched.
- A cell's `y` is its floor, its `x` and `z` its centre; `engine/chunk.py`
  adds the +0.5. Every "standing on a block" rule (`surface = y + 1`) relies on it.
- Every cell of tower skin goes through `Course._paint` and is placed only if
  `rock` agrees; a drawn cell `rock` has not heard of is walked straight through.
- Checking is not reserving: head-room checked at placement is not held
  against a later block or support post. Reserve it.
- A probe that exempts what it measures reads zero forever, and a probe that
  checks a move one step late (`<` for `<=`) measures a world whose floor
  `advance` already released. Ask the world what the body would.
- A blend mode does not stop a draw writing depth. Everything emissive goes
  through `fx.no_depth_write` / `fx.emissive`; parkour queues its glows and
  draws them after all opaque geometry.
- rlgl batches `DrawPlane` and issues `DrawModelEx` at once, so a plane drawn
  first is drawn last; call `rl.flush()` after any batched draw whose order
  matters. Shared `voxel` models must be left exactly as found (`model.transform`).
- A mesh raylib will free must be raylib-allocated (`MemAlloc`); a cffi buffer
  handed to `UnloadMesh` dies inside libc.
- Any capture path calls `brainrot.overlay.x11.prepare()` before `InitWindow`
  and saves through `engine/rl.save_frame`, which measures flip and channel
  order rather than assuming them; read-back is one swap behind the draw.
- Rebuilding an asset changes `metrics.json` inputs: run `assets/measure.py` or
  `tests/test_assets.py` fails. Asset names are filenames and a clash is silent
  (check `src/brainrot/assets/data/` first). `vinehang`, `dripstone`, `chain`
  hang from the top. Blender exits 0 when a script raises; `build.py` passes
  `--python-exit-code 1`. `bpy` imports once per process.
- Pose code goes through `swing()`/`lift()`/`world_axis_q()` in
  `assets/src/common.py`; down-pointing bones swing sideways on local x.
  Vertex colours are banned in assets.
- Strip flapping, a scene left on screen, or a 10 Hz flicker is almost always
  a second daemon or a second compositor (headless gnome-shell) feeding the
  port. Check `brainrot doctor`'s `instances` line first.
- A changed `extension.js` cannot be reloaded into a running shell (gjs
  imports a module once); new code means logging out. `brainrot extension
  load` is only for a shell that has never seen it.
- One jump impulse and one run speed fix the longest hop: `hop_span(rise)`,
  about 4.3 m level, further only by dropping, never two blocks up in one hop.
  Longer jumps need a different motion model, not a bigger number.

## Conventions

- Every generated thing draws from `seed.stream("label")` substreams; the same
  seed must replay pixel-identically (tests assert this).
- Scenes never touch windowing, hooks or config. Solvability is by
  construction, never by rejection sampling; invariants live in
  `tests/test_generation.py` and, for the spiral, `tests/test_spiral.py`
  (including that nothing can walk up the tower without touching the parkour).
- Run `python -m pytest tests/` before committing and check the count, not just
  the colour.
- Art direction is done by looking at `brainrot shoot` output, so the capture
  itself is tested: colours survive, the frame is the right way up, and
  drawing the same state twice draws the same picture. `draw()` must never
  advance anything.
- Levels are one module each in `src/brainrot/scenes/levels/`, built to
  `docs/RULES.md`; `docs/LEVEL_BRIEF.md` is the brief for redesigning one.

## Where things live

- `docs/ARCHITECTURE.md`: how the pieces fit, both platforms. Open before any
  change to the engine, overlay or IPC.
- `docs/PROBES.md`: every probe, what it measures, how to read it.
- `docs/LANDMINES.md`: the full trap list. Open on any odd symptom.
- `docs/OUTSTANDING.md`: the design backlog, numbered by age, with the probe
  that measures each item.
- `docs/HISTORY.md`: the dated build diary. Open for "why is it like this";
  read pre-2026-08-22 fidelity and crossing numbers with its review-pass
  correction in mind, and re-run the probe rather than quoting a table.
- `docs/TOWER.md`, `docs/RULES.md`, `docs/RESEARCH.md`, `docs/REHASH.md`,
  `docs/PATH.md`: the hand-built tower (roster, the level constitution, the
  measured reference map, the fly-over-the-terrace rehash, the course path).
- `docs/LEVEL_BRIEF.md`, `docs/PASS_STATE.md`: the per-level redesign brief
  and the finished level pass (kept as record).
- `docs/HOOKS.md`: what `brainrot install` writes. `docs/BLENDER_TOWER.md`:
  a speculative bookmark. `docs/HANDOFF*.md`: older session handoffs.
- `docs/reference/`: measured frame and map findings plus the tower path dump.
- `FINDINGS.md`: the defect ledger, one row per finding.
