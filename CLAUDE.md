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
"Landmines" below. 371 tests green, including a Win32 suite that exercises the
real window API.

The runner has a real collision model. Obstacles carry hitboxes derived from
the assets' own measured geometry (`assets/measure.py` → `metrics.json`), and
`scenes/runnerplan.py` plans lanes and take-offs *in time* and then verifies
the plan by simulating it before committing. Evidence: zero interpenetration
across 60 seeds × 180 s of simulated running, at every speed. If you change
anything in the runner, re-run that sweep — `tests/test_collision.py` covers
the same ground in a form that fits in the suite.

The overlay is **installed and verified end to end** on the owner's machine:
hooks registered, daemon running, `brainrot doctor` 12/12. Measured live —
appears 2.0 s after `UserPromptSubmit`, click-through, never focused, off
alt-tab, hides 3.0 s after `Stop`, and (2026-08-07) stays hidden while the
window in front is not the one the prompt came from.

The parkour scene has had the same depth pass. Its course is generated in
**set-pieces** (`SEGMENT_TABLE`) rather than as a uniform stream of cubes, its
materials carry texel patterns, and the crucial structural change is that
**the course knows its own path**: where the player will stand on each block is
decided when the block is generated, so the exact ballistic arc of every future
hop is computable at generation time. Orbs are hung on that arc at chest
height, which is why "every orb laid down is collected" is a test rather than a
hope. If you change the flight solver or the landing offsets, that test is the
one that will tell you.

Either scene can also be **driven by hand** (`engine/input.py`): arrows or
WASD, up/space to jump, down to duck, eight idle seconds to hand back. The
overlay never reads a key until the takeover chord deliberately gives it focus
— there is no global key hook, on purpose. `brainrot demo` needs no chord.
Both scenes now opt in via `Scene.playable`. Steering parkour bends the
*course* rather than moving a body: there is no free movement to give a runner
made of solved arcs between blocks that do not exist yet.

The overlay is on screen **only while a Claude Code window that is actually
working is the window in front** (`follow_focus`, default on). Ownership alone
was never enough for that — it decides what covers what, not what is visible,
so a strip that did not overlap whatever you switched to just sat there over
it. Each frame the daemon compares the real foreground window against the
hosts of the sessions currently thinking; `ThinkingState` tracks those per
session id, from prompt events only. Not one of them, and not the overlay
itself (the takeover chord makes the overlay the foreground window — a naive
"hide unless the host is in front" hides the strip the instant you press it)
→ fade out. Unknown host means hidden, never topmost.

## Still outstanding

1. **DPI**: on a scaled display check the strip's size and placement; raylib
   windows are not DPI-aware by default.
2. Per-frame cost at sustained top speed, vsync off, on an idle machine:
   runner 2.6-3.0 ms, parkour 1.5-2.3 ms, against a 16.7 ms budget. Measure
   with `HeadlessWindow` + `SetTargetFPS(0)`; `DesktopWindow` has vsync on and
   will report a flat 16.6 ms that tells you nothing. Take the reading on a
   *quiet* machine — with a browser and Docker busy, both scenes measure two
   to four times higher and the absolute numbers are worthless. **Measure
   parkour against the runner in the same process**: that ratio is stable at
   about 0.75 whatever else the machine is doing, and it is the number that
   actually tells you whether a change cost anything.

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

## Known limit: how long a parkour jump can be

The chasm set-piece is only a little wider than the gap table's own maximum,
and deliberately. The hop is a ballistic arc that lands exactly where it aimed,
so a longer jump can only be paid for by crossing the ground faster than a body
runs or by arcing higher than a body jumps, and both look wrong immediately. A
chasm reads as a chasm because of the void under it and the two lit platforms
either side, not because of another metre of distance. If you want genuinely
long jumps you need a different motion model, not a bigger number.

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
  `engine/rl.py:_capture_fix` draws marker frames and reads back where they
  landed. Never read the screen directly.
- **Read-back is one buffer swap behind the draw** on the GPU build here, so
  the probe above draws its marker *until the read is decisive* and runs at
  window creation. A single marker frame read back the previous frame — a blue
  sky, in which blue beats red — concluded the channels were swapped, and every
  `shoot` PNG came out with an orange sky and a brown ocean. Anything that
  wants to capture a frame must present it twice.
- **rlgl batches some draws and issues others immediately.** `DrawPlane` goes
  into the render batch and is not submitted until `EndMode3D`; `DrawModelEx`
  draws at once. So a ground plane drawn first is drawn *last* and loses the
  depth test to everything above it. Opaque models hide this; transparent ones
  do not — it punched cloud-shaped holes in the parkour sea. Call `rl.flush()`
  after any batched draw whose order matters.
- **Shared block models must be left as they were found.** The parkour kit is
  built from the same `voxel` models the course is, so a `model.transform` left
  behind by the held item tilts every block of that material in the world on
  the next frame.
- **GLFW window calls block off-thread.** On the GPU build under Windows,
  `SetWindowSize` and friends post to the thread that owns the window and wait
  for it to pump messages. Calling one from a worker thread deadlocks — which
  is why `HeadlessWindow.create` skips a resize to the size it already is.
- **An owned window dies with its owner.** The overlay is owned by the Claude
  Code host window for z-order, and `DestroyWindow` on an owner destroys what
  it owns. The daemon therefore detaches whenever it goes idle. In tests,
  destroy the fake host *after* detaching or it takes the shared raylib window
  with it.
- **Two daemons bind the same port quite happily.** UDP with `SO_REUSEADDR`
  does not refuse the second bind; the hook events are then split between the
  processes, each gets a fraction of the turn, and their windows fight over
  the screen. Every symptom looks like a bug in the overlay. Worse, a Store
  Python's `CommandLine` is not readable through WMI, so
  `Where-Object CommandLine -like '*brainrot*'` matches **nothing** and a kill
  that reports no error can have killed no one. Count the windows instead:
  `brainrot doctor` has an `instances` check that does exactly that.
- **A leaked daemon can steal the foreground.** Chasing why the overlay hid
  itself the instant it appeared cost an hour and produced a plausible,
  entirely wrong theory about `glfwShowWindow` activating the window. It does
  not: measured on a real `OverlayWindow`, raylib's own hide flag leaves the
  foreground alone. It was three daemons. Check `instances` first.
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
- Run `python -m pytest tests/` before committing; it is fast (~50s).
- Art direction is done by looking at `brainrot shoot` output. That only works
  if the capture is honest, so there are tests on the capture itself: colours
  survive, the frame is the right way up, and drawing the same state twice
  draws the same picture (`draw()` must not advance anything).
