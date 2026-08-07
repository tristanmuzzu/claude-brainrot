# claude-brainrot — project context

A generated 3D "brainrot" overlay (Subway-Surfers-style runner + first-person
Minecraft parkour) that appears while Claude Code is thinking. raylib renderer,
glTF assets built by the Blender scripts in `assets/src/`, worlds generated
per-seed. Read `docs/ARCHITECTURE.md` for how the pieces fit; it is current.

## State of the project (updated 2026-08-07)

Branch `claude/project-visuals-animations-qzbkiq` holds a complete rebuild:
pygame → raylib + baked-light glTF assets, both scenes rebuilt to match the
real reel formats, animation overhaul (rig with knees/elbows, world-axis pose
system, ballistic parkour hops with ground beats).

**Now verified on real Windows hardware with a GPU**, which turned up several
things the software-rasteriser cloud sessions could not have seen — see
"Landmines" below. 288 tests green, including a Win32 suite that exercises the
real window API.

The runner has a real collision model. Obstacles carry hitboxes derived from
the assets' own measured geometry (`assets/measure.py` → `metrics.json`), and
`scenes/runnerplan.py` plans lanes and take-offs *in time* and then verifies
the plan by simulating it before committing. Evidence: zero interpenetration
across 60 seeds × 180 s of simulated running, at every speed. If you change
anything in the runner, re-run that sweep — `tests/test_collision.py` covers
the same ground in a form that fits in the suite.

The overlay is **installed and verified end to end** on the owner's machine:
hooks registered, daemon running, `brainrot doctor` 10/10. Measured live —
appears 2.0 s after `UserPromptSubmit`, click-through, never focused, off
alt-tab, hides 3.0 s after `Stop`.

Either scene can also be **driven by hand** (`engine/input.py`): arrows or
WASD, up/space to jump, down to duck, eight idle seconds to hand back. The
overlay never reads a key until `Ctrl+Alt+B` deliberately gives it focus —
there is no global key hook, on purpose. `brainrot demo` needs no chord.
`Scene.playable` gates this; the runner opts in, parkour does not yet.

## Still outstanding

1. **Parkour needs the depth the runner got** — see
   `docs/HANDOFF-parkour.md`, which has the job and a prompt to start it.
2. **Window attachment in anger.** The mechanism is proven and tested against
   the live API; the *feel* is not. Watch whether the strip sits one z-level
   above the terminal and is covered by anything else you focus.
3. **DPI**: on a scaled display check the strip's size and placement; raylib
   windows are not DPI-aware by default.
4. Per-frame cost at sustained top speed, vsync off: runner 6.1 ms, parkour
   1.3 ms, against a 16.7 ms budget.

## Tried and reverted: running along train roofs

Ramps that mount the runner onto a train roof (the signature Subway Surfers
move) are implemented in full in the history around this commit and were
**reverted** — not because the riding did not work, it did, but because the
lane search and the mount decision are made in separate stages. The lane
search is pulled toward a rideable train; if verification then rejects the
mount, the runner is already committed to a lane with a train across it, and
contacts went from zero to thousands. Making it work needs the lane choice and
the mount to be solved *jointly*, not in sequence. Worth doing; not worth
shipping half-done, because it regresses the one property the collision work
exists to guarantee.

## Dev loop (works headless and locally)

- `brainrot shoot --scene runner --seed N --frames 240 --every 40 --out shots/`
  renders exact frames of exact runs to PNG. This is how all art direction
  was done: render, look, adjust, repeat.
- `python assets/build.py [name]` rebuilds committed .glb files from their
  scripts (needs `pip install bpy`, one subprocess per asset). Blender 5.0.1
  reproduces every committed asset's geometry and materials exactly.
  **Always follow a rebuild with `python assets/measure.py`.**
- `python assets/preview.py <asset>` and
  `python assets/animstrip.py character run` render assets/clips for review.
- On a machine without a display or GPU:
  `pip install raylib-software --force-reinstall --no-deps` swaps in the
  software rasteriser (CI uses this; colours/output match the GPU build).

## Landmines that cost hours — do not relearn these

- **Pose-bone axes**: down-pointing bones swing SIDEWAYS on local x. All pose
  code must go through `swing()`/`lift()`/`world_axis_q()` in
  `assets/src/common.py`, which key world-space intentions.
- **Vertex colours are banned in assets**: the software rasteriser ignores
  material colour and tint when a colour attribute exists; export strips them.
- **`ClearBackground` every frame**: it also clears depth; skipping it because
  "the sky covers everything" makes every frame after the first invisible.
- **Texture lifecycle**: scene textures are evicted when the next scene is
  built (`scene_api.build`), and `assets.unload_all` must unload embedded glTF
  textures itself. Both exist because texture slots leak otherwise.
- **raylib maps glTF material i to slot i+1** (slot 0 is its default). Zone
  names come from the GLB JSON chunk; see `src/brainrot/assets/__init__.py`.
- **bpy imports once per process**: asset builds run one subprocess each.
- **Capture correction is measured, not assumed.** Which rasteriser is
  underneath decides whether captures come back flipped and BGR-swapped, and
  `os.name` cannot answer that question — assuming it wrote every `shoot`
  frame upside down on Windows for the entire life of the branch.
  `engine/rl.py:_capture_fix` draws a marker frame and reads back where it
  landed. Never read the screen directly.
- **GLFW window calls block off-thread.** On the GPU build under Windows,
  `SetWindowSize` and friends post to the thread that owns the window and wait
  for it to pump messages. Calling one from a worker thread deadlocks — which
  is why `HeadlessWindow.create` skips a resize to the size it already is.
- **An owned window dies with its owner.** The overlay is owned by the Claude
  Code host window for z-order, and `DestroyWindow` on an owner destroys what
  it owns. The daemon therefore detaches whenever it goes idle. In tests,
  destroy the fake host *after* detaching or it takes the shared raylib window
  with it.
- **Numbers the gameplay depends on live in `metrics.json`.** Rebuild an asset
  and you must re-run `python assets/measure.py`; `tests/test_assets.py` fails
  if they drift apart. Moving a hoarding's beam moves whether a slide fits
  under it.

## Conventions

- Every generated thing draws from `seed.stream("label")` substreams; same
  seed must replay pixel-identically (tests assert this).
- Scenes never touch windowing/hooks/config. Solvability is by construction,
  never by rejection sampling; invariants live in `tests/test_generation.py`.
- `GENERATION_EPOCH` in `rng.py` re-rolls all seeds after big generation
  changes; bump it rather than fighting stale-looking runs.
- Run `python -m pytest tests/` before committing; it is fast (~15s).
