# claude-brainrot — project context

A generated 3D "brainrot" overlay (Subway-Surfers-style runner + first-person
Minecraft parkour) that appears while Claude Code is thinking. raylib renderer,
glTF assets built by the Blender scripts in `assets/src/`, worlds generated
per-seed. Read `docs/ARCHITECTURE.md` for how the pieces fit; it is current.

## State of the project (updated 2026-08-07)

Branch `claude/project-visuals-animations-qzbkiq` holds a complete rebuild:
pygame → raylib + baked-light glTF assets, both scenes rebuilt to match the
real reel formats, animation overhaul (rig with knees/elbows, world-axis pose
system, ballistic parkour hops with ground beats), 224 tests green. All work
so far was done and verified in a headless cloud container via the software
rasteriser — **nothing has been verified on real Windows hardware yet.**

## If you are a local Claude session on the owner's Windows machine

You have what the cloud sessions did not: a GPU, a real display, and the
actual overlay window path. The highest-value work, in order:

1. `pip install -e .` then `brainrot doctor` — every check should pass or
   warn sensibly on Windows. Report anything red.
2. `brainrot demo --scene runner` and `--scene parkour`: verify frame rate
   (should be an easy 60), that colours/animation match `docs/media/*.gif`,
   and that nothing GPU-specific diverges from the software-rendered media
   (that pipeline was designed to match — confirm it actually does).
3. The overlay itself: `brainrot install && brainrot run`, then use Claude
   Code normally. Verify: appears ~1.5s after a prompt, fades, never steals
   focus, clicks pass through, hides on permission prompts.
4. Window attachment (`attach = "host"`, the default): the overlay should sit
   one z-level above the window hosting the Claude Code session and be
   covered by anything else you focus. `overlay/win32.py` is ctypes and was
   written blind — this is the most likely place to need fixes.
5. DPI: on a scaled display check the strip's size/placement; raylib windows
   are not DPI-aware by default.

## Dev loop (works headless and locally)

- `brainrot shoot --scene runner --seed N --frames 240 --every 40 --out shots/`
  renders exact frames of exact runs to PNG. This is how all art direction
  was done: render, look, adjust, repeat.
- `python assets/build.py [name]` rebuilds committed .glb files from their
  scripts (needs `pip install bpy`, one subprocess per asset).
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
- Headless captures come back vertically flipped with R/B swapped;
  `engine/rl.py:capture_frame` corrects this — never read the screen directly.

## Conventions

- Every generated thing draws from `seed.stream("label")` substreams; same
  seed must replay pixel-identically (tests assert this).
- Scenes never touch windowing/hooks/config. Solvability is by construction,
  never by rejection sampling; invariants live in `tests/test_generation.py`.
- `GENERATION_EPOCH` in `rng.py` re-rolls all seeds after big generation
  changes; bump it rather than fighting stale-looking runs.
- Run `python -m pytest tests/` before committing; it is fast (~15s).
