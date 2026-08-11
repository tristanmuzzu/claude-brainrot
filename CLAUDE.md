# claude-brainrot — project context

A generated 3D "brainrot" overlay (Subway-Surfers-style runner + first-person
Minecraft parkour) that appears while Claude Code is thinking. raylib renderer,
glTF assets built by the Blender scripts in `assets/src/`, worlds generated
per-seed. Read `docs/ARCHITECTURE.md` for how the pieces fit; it is current.

## State of the project (updated 2026-08-09)

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

The runner had the same pass the parkour scene did (2026-08-11), for the same
complaint — "a bit slow, doesn't feel natural, something missing for it to be
actually entertaining" — and the same method: turn each complaint into a
number, write `tools/runner_probe.py` to measure it, then rewrite against the
probe. Four structural facts came out of it:

- **Content is laid down a set-piece at a time**, not a row at a time.
  `SEGMENT_TABLE` is the vocabulary — cruise, hurdles, slalom, tunnel, yard,
  express, roofrun — and each entry decides a stretch of track *and the
  corridor through it* together, which is the only way to express a weave, a
  train yard or a ramp onto a roof at all. A set-piece never follows itself,
  and one that finds the track it wanted occupied declines and is rewound
  whole (`_mark`/`_rewind`): a segment that wrote a corridor and then gave up
  used to leave those rows for the next one to overwrite from a different
  lane, and a corridor that steps two lanes in one row is a promise the body
  cannot keep.
- **There is an occupancy ledger, and a separate ledger for *moves*.**
  `_spans` is per-lane track occupancy in absolute distance and nothing is
  placed without asking it; `_acts` is the same idea for the stretch a jump or
  a slide commits the body to. Row counting stood in for both and could see
  neither: a 25 m train against a 6 m row is a great many rows of nothing
  being said, and two hurdles either side of a set-piece boundary put the
  runner's feet through the second while it was still coming down off the
  first.
- **The runner rides train roofs** — see below. That is the move the owner
  asked for by name, and the reason the motion model now has surfaces at all.
- **It starts quick.** The speed ramp was 8.5–15.5 m/s over 75 s, which is
  sensible for a game somebody sits down to play and wrong for a strip that is
  on screen for as long as Claude is thinking: it spent its whole visible life
  in the bottom third of its own range. 10.5–18.0 over 40 s.

The probe's numbers, before and after, both measured with the *same* probe —
`tools/runner_probe.py` runs against the old scene too, because a before/after
tool that only works on "after" measures nothing. Safety over 60 seeds × 180 s
after and 20 × 180 s before; pacing over 20 × 180 s both sides. Re-run it after
touching anything in this scene; the first two rows are non-negotiable.

| | before | after |
|---|---|---|
| obstacles drawn inside each other | 305,134 frame-pairs, worst 2.18 m | **0** |
| body inside an obstacle | 6 frames, worst 0.19 m | **0** |
| required actions per minute | 42.8 | **49.2** |
| median idle between actions | 1.15 s | **1.00 s** |
| 95th-percentile idle | 3.48 s | **2.78 s** |
| worst idle | 9.17 s | **7.48 s** |
| dead air (idle over 3 s, riding excluded) | 5.8% | **1.8%** |
| speed at 15 s / 30 s | 9.9 / 11.3 m/s | **13.3 / 16.1 m/s** |
| slides per minute | 4.6 | **4.5** |
| mounts onto a train roof per minute | n/a | **1.63** |
| seconds spent on a roof per minute | n/a | **2.35** |
| distinct obstacle kinds per 30 s | n/a | **9.1** |

Two of those deserve a note. The 6 body contacts before are the interesting
one: this file claimed zero interpenetration across 60 seeds × 180 s, and that
was true of the sweep it was measured on and is not true of `HEAD` — the
guarantee had quietly lapsed. And **slides per minute did not move**, which is
the honest reading of a mix that looks much more varied: the slide was always
about as frequent as it is now, and what changed is that it arrives in a
*tunnel* of two or three rather than singly. Nothing in the probe measures
that, and it is the kind of thing only looking at a contact sheet catches.

The overlay is **installed and verified end to end** on the owner's machine:
hooks registered, daemon running, `brainrot doctor` 12/12. Measured live —
appears 2.0 s after `UserPromptSubmit`, click-through, never focused, off
alt-tab, hides 3.0 s after `Stop`, and (2026-08-07) stays hidden while the
window in front is not the one the prompt came from.

The parkour scene has had the same depth pass, and then a second one
(2026-08-11) after the note that "the blocks are sometimes inside each other"
and "the parkour feels fake and scripted". Both were true and both were
measurable; `tools/parkour_probe.py` is the thing that measures them and the
numbers it prints are the acceptance criteria. Before: 3,756 interpenetrating
solid pairs in 8,000 blocks (worst 0.87 m), 0.2% of blocks on an integer grid,
the body inside a solid block on 9.3% of frames, and the player standing
perfectly still for 30% of every frame drawn. After: **0, 100%, 0.04 m worst
case, and 0%.** Re-run it after touching anything in this scene.

Then a third pass (2026-08-11, later) for "invisible blocks or walls blocking
other stuff", "tiny jumps that would be very weird to do quickly", and "make it
more difficult". All three were real:

- **The invisible walls were the glows.** See the depth-write landmine below.
- **The hops were too short**, and one number fixed nearly all of it: `MIN_HOP`
  went 1.1 -> 2.0, and because every set-piece's gap goes through `fit_gap`,
  every hard-coded one-block gap in the file widened to two at a stroke.
  Take-off to landing went from min 1.32 / median 2.43 to **min 2.32 / median
  2.79 / mean 3.03 m**; landing to landing, which is what the probe has always
  printed, went from min 2.00 / median 3.13 / max 6.45 to **2.99 / 4.00 /
  8.18**.
- **The course now ramps.** `difficulty` goes 0 to 1 over the first 80 blocks
  laid. Mean flight by block index: **2.93 -> 3.08 -> 3.15 -> 3.14 m** across
  blocks 0-40, 40-80, 80-200, 200+ -- it climbs and then *holds*, which is the
  half of a ramp that is easy to get wrong. Two new set-pieces, `slabs`
  (half-height landings) and `squeeze` (beams to skim under, columns to
  clear). Report the ramp on the **mean**: a hop length is one of a handful of
  discrete values, so the median snaps between modes and can move the wrong
  way between two samples that differ by a few per cent.

Four structural facts, all of which the tests state:

- **The course is on an integer lattice, with an occupancy map** (`_solid`).
  Headings stay continuous — a course restricted to eight compass points looks
  like a maze — but placement snaps to whole cells, and whole cells cannot
  interpenetrate. Placement asks four questions: are the block's cells free,
  are the two cells above the landing free, is the hop one a body can make,
  and does the *arc* pass through anything.
- **Motion is vanilla's.** `GRAVITY`, `JUMP_V`, `RUN_SPEED`, `AIR_SPEED` are
  Minecraft's own numbers converted from ticks. Horizontal speed is
  **constant**, so `flight()` is one line and every hop is the same motion at
  a different height. What used to be there solved each hop for a duration and
  then clamped it, so speed swung between 3.5 and 6 m/s from hop to hop.
- **The body never stops.** It lands on a block's near edge, runs across it,
  and leaves from the far edge; the beat on each block is a run-up, and its
  length is that distance at sprint pace rather than a number anybody chose.
  This is the single change that answers "feels scripted".
- **The course knows its own path.** Where the feet land and leave is decided
  when the block is generated, so the arc of every future hop is computable at
  generation time. Orbs hang *on* that arc at chest height, which is why
  "every orb laid down is collected" is a test rather than a hope. An early
  jump moves the take-off, so `_begin_air` re-solves the arc and re-hangs that
  hop's orbs; on autopilot the two are identical numbers.

A fifth: **the difficulty ramp is counted in blocks laid, not metres
travelled** (`ParkourScene.difficulty`). Generation runs fourteen blocks ahead
of the body, and the probes and half the generation tests grow a course by
calling `_spawn_block` without ever moving one -- keyed to `self.distance` the
ramp would read zero forever and every test that believes it is checking the
hard end of the course would be checking the easy one.

`scene.stuck` counts the times placement fell back on its unchecked emergency
hop. It must stay zero — when it was not, the visible symptom was a flight of
stairs stacked nearly vertically, and the cause was a set-piece asking for a
gap its rise could not support. `fit_gap` now reconciles the two centrally.

The strip can also be **dragged where you want it**: hold `drag_chord`
(`ctrl+alt`) and drag with the mouse; double-click while holding it to go back
to automatic placement. Click-through is lifted only while the chord is held
*and* the pointer is over the strip, so an ordinary click still belongs to the
app behind, and focus is never taken. Where it was dropped is stored as an
offset from the host window (`placement.py`), so a remembered spot still
follows that window and still means something at another resolution.

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

It is also **placed against the host window rather than the screen**
(`engine/window.py:place`, pure geometry, `tests/test_placement.py`). Docking
to a monitor edge put it straight on top of the Claude Code sidebar, which is
what a screen edge holds in every app worth overlaying. It now stands *beside*
the host window when the desktop has room and in that window's own gutter when
it does not, on the `dock` side, re-checked every frame so it keeps up with a
window being dragged. Real geometry lives in `overlay/win32.py`
(`window_rect`, `work_area`, `move_window` — `SetWindowPos`, never raylib's
`SetWindowPosition`, which would block off-thread).

## Linux (added 2026-08-09, verified on the owner's Ubuntu box)

Runs on Ubuntu 26.04 / GNOME Shell 50.1 (Wayland, 200% scaling) with the same
behaviour as Windows: appears while a Claude Code window that is working is in
front, hides when you look elsewhere, hides on `Stop`, click-through, never
focused, stands against the host window. Measured live, not inferred.

The platform split is `overlay.native()`; the engine has no `os.name` tests
left. Read `docs/ARCHITECTURE.md` § "Two platforms, one vocabulary" before
touching any of it — the reasoning is there, this is the short list:

- **The strip is an X11 (XWayland) window on a Wayland session.** A Wayland
  client cannot place itself, raise itself, or shape its input region; an X11
  one can, and mutter honours it. `x11.prepare()` sets `glfwInitHint(
  GLFW_PLATFORM, X11)` before `InitWindow`. Clearing `WAYLAND_DISPLAY` does
  **not** do this: libwayland defaults to the socket `wayland-0`.
- **Everything about other windows comes from a gnome-shell extension**
  (`src/brainrot/extension/`), pushed over the daemon's own UDP port.
  `org.gnome.Shell.Introspect.GetWindows` is refused. It is optional; without
  it the strip docks to the work area and stays up for the whole turn.
- **The host is resolved from process ancestry, not a window handle.** There
  is no handle to read on Wayland. The shim sends its `/proc` ancestry
  nearest-first and `Snapshot.host_for` matches it against window pids.

## Still outstanding

1. **DPI**: measured 2026-08-07 on the owner's 1920x1080 at 125%. The daemon
   *is* per-monitor DPI aware — GLFW sets that at `InitWindow` — so every
   `GetWindowRect`/`SetWindowPos`/work-area number inside it is in **physical
   pixels**, and placement is self-consistent. What is still open is that
   `width`/`height` are therefore physical too, so the strip is 1/1.25 of the
   apparent size you would expect from the number. Beware when comparing
   against an outside probe: a plain script is DPI-*un*aware and reads the
   same window back scaled (1920 → 1536), which looks exactly like a bug and
   is not. Call `SetProcessDpiAwareness(2)` in probes.
2. Per-frame cost at sustained top speed, vsync off, against a 16.7 ms
   budget. `python tools/frame_cost.py` is the harness and it does the things
   that have to be right: `HeadlessWindow` + `SetTargetFPS(0)` (`DesktopWindow`
   has vsync on and reports a flat 16.6 ms that tells you nothing), and the two
   scenes built alternately round by round, because only one scene may be alive
   at a time and alternating averages out whatever else the machine started
   doing. Absolute milliseconds off a busy machine are worthless; **the ratio
   between the two scenes in one process is not**.

   Measured 2026-08-11: parkour **2.02 ms**, runner 1.78 ms, ratio 1.15. Do not
   read that ratio against the old 0.75 without checking the denominator: the
   runner was rewritten in a parallel session and now measures 1.78 ms against
   the 2.6-3.0 ms this file used to record, and 2.02/2.8 = 0.72, which is the
   old number. What did change on this side is the new set-pieces -- parkour
   past the ramp costs 2.02 ms against 1.49 ms with `squeeze` and `slabs`
   weighted out, so their geometry is about half a millisecond. The ramp
   itself is free.

   The runner's own set-piece rewrite was measured the same way, back to back
   on a busier machine: **1.025 before, 1.005 after**, against a round-to-round
   spread of 0.77 ms. Cost-neutral. Do not compare either of those to the 1.15
   above -- that was a quiet machine, and only the ratio survives the
   difference.

## Running along train roofs, and why it works now

The signature Subway Surfers move. It was written once before, in the history
around this branch, and **reverted** — not because the riding did not work, it
did, but because the lane search and the mount decision were made in separate
stages: the search was pulled toward a rideable train, and when verification
then rejected the mount the runner was already committed to a lane with a
train across it. Contacts went from zero to thousands.

They are one decision now, and the shape of it is worth keeping in mind before
touching any of it:

- **The set-piece commits or declines as a whole.** `_seg_roofrun` lays the
  ramp, the train, the corridor onto it, the clear lane to bail into and the
  clear sky over all of it together, and it solves the leap *at generation
  time* — at both ends of the speed range, because gravity and launch speed
  are rebuilt as the run accelerates. A ramp whose train is out of reach is
  not a hard puzzle, it is a promise the track cannot keep, so it is never
  laid.
- **The train is one threat with one answer.** It carries `mount_at`: the one
  moment a take-off can happen, which is when the ramp's lip is under the
  feet. `classify` reads that and returns `"mount"`; `schedule_vertical` books
  it; `plan.verify` rolls the lane path and the take-off forward *together*
  over a world that includes the train. If that fails, the existing machinery
  marks the threat hard, the search routes around it, and the bail lane is
  empty by construction. Both outcomes are safe; that is the whole trick.
- **The offer has a deadline.** `_mount_at` withdraws it as soon as the body
  can no longer be squarely in the ramp's lane before the foot of the ramp —
  while there is still track in which to leave that lane. Offering it right up
  to the ramp is what the reverted version did.
- **Riding is free to the lane search.** `MOUNT_COST` is 0.0 and has to be:
  the search already pays `preference` for every step spent outside the
  guaranteed corridor, so *any* positive cost on the roof makes standing
  beside the train cheaper than standing on it. At 0.4 against a preference of
  0.22 the runner stepped one lane clear of every ramp in the scene — 33 ramps
  laid down, 2 ever taken.

Two motion rules hold it up, and both are in `Motion.advance` so the check and
the execution cannot disagree: a body **holds its lateral position while it is
off the rails** (stepping sideways off a roof puts the fall alongside the
train with the box still overlapping the corner it left), and it is **held up
while its centre is over a surface but until its back has left it** (a body is
over a metre deep, and dropping it the moment its centre crosses the far edge
leaves the rear half hanging over a roof it is no longer standing on). The
ramp additionally only picks a body up within `RAMP_GRIP` of its lane centre:
you get onto a ramp by running at it, not by sideswiping it.

## Known limit: how long a parkour jump can be

There is one jump impulse and one horizontal speed, so the furthest a hop can
reach is fixed, and `hop_span(rise)` computes it rather than anybody choosing
it. Level, that is about 4.3 m stand point to stand point; reaching further is
available only by *dropping*, because falling takes longer and the body does
not slow down while it does. That is why `_seg_chasm` steps down — the extra
hang time of a one- or two-block drop is what buys the last metre, exactly as a
player clears a gap they cannot make level.

The same arithmetic runs the other way and is why `fit_gap` exists: a hop that
descends four blocks *cannot* also be short, because the arc covers close to
four metres of ground before it arrives. Descents therefore leap out into the
drop. And nothing can rise two blocks in one hop, because the discriminant has
no solution — the same reason vanilla cannot.

A chasm reads as a chasm because of the void under it and the two lit platforms
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
- `python tools/runner_probe.py --runs 12 --seconds 120` is the runner
  scene's acceptance test in numbers, and the only way "it feels boring" was
  ever going to be actionable. Three sections: **safety** (obstacles inside
  each other, the body inside an obstacle, plans with no answer), **pacing**
  (how often the runner is forced to act, the distribution of the idle
  stretches between those moments, the obstacle mix, the set-piece mix, and
  the speed at 0/15/30/60 s), and **riding** (mounts and seconds on a roof per
  minute, and "surface pops" — a body teleported upward by a surface, which is
  what a badly built ramp looks like). `--safety-runs 60 --safety-seconds 180`
  is the full sweep the collision model is held to.
- `python tools/parkour_probe.py --runs 24 --motion-runs 12` is the parkour
  scene's acceptance test in numbers: interpenetration, grid alignment,
  emergency hops, the hop distribution and its ramp, and whether the body ever
  ends up inside a block. Currently: **0 overlapping pairs, 0 emergency hops,
  100% on the grid, 0% frozen frames, body worst case 0.042 m.**
- `python tools/depth_probe.py` says what each translucent draw is hiding, by
  re-rendering the frame with that one draw's depth writing turned off and
  counting the pixels that change -- and again against a silhouette of the
  course alone, which is the number that matters. Everything reads 0 now.
  `--legacy` reconstructs the pre-fix draw order in the same process, which is
  where the before numbers come from.
- `python tools/frame_cost.py` times each scene in one process with vsync off
  and reports the ratio between them. Absolute milliseconds off a busy machine
  are worthless; that ratio is not.
- `python tools/atlas_sheet.py out.png` shows every block pattern at texel
  scale *and* at block scale. Judging a texture at 8x is how the first set
  ended up as four enormous bricks and a chequerboard.
- `python tools/contact_sheet.py <shots dir> sheet.png` tiles a whole run into
  one image. A single frame can be flattering by accident; what needs judging
  is whether the course stays in shot from hop to hop.
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
- **Two daemons used to bind the same port quite happily.** UDP with
  `SO_REUSEADDR` did not refuse the second bind; the datagrams then went to
  one of them only -- the first showed the strip on a prompt, the second took
  the `Stop`, and the first left a scene on screen for the rest of the day.
  Every symptom of that reads as a bug in the overlay, and it cost an
  afternoon twice. Fixed 2026-08-09 by dropping `SO_REUSEADDR`: the second
  daemon now refuses to start. UDP has no `TIME_WAIT`, so nothing was bought
  by allowing it. `brainrot doctor`'s `instances` line counts *processes* on
  Linux rather than windows -- an idle duplicate has no window and is
  invisible to a window count right up until it steals an event. Worse, a Store
  Python's `CommandLine` is not readable through WMI, so
  `Where-Object CommandLine -like '*brainrot*'` matches **nothing** and a kill
  that reports no error can have killed no one. Count the windows instead:
  `brainrot doctor` has an `instances` check that does exactly that.
- **A Microsoft Store Python cannot see `%APPDATA%`.** The whole subtree is
  redirected into `…\Local\Packages\<pkg>\LocalCache\Roaming\`, for *reads as
  well as writes*: `(state_dir()/"config.toml").exists()` is False for the
  file you are looking at in Explorer. The owner's `hotkey` setting had never
  once been read. There are several such copies here — the Claude desktop app
  is a packaged app too, so anything it launches gets its own. `Config.load`
  swallows the miss (`except OSError: raw = {}`) and every value silently
  reverts to a default that looks plausible. `brainrot doctor`'s `config`
  check prints the path that is genuinely being read; trust that, not the
  path printed next to "state dir".
- **Showing the window through raylib steals the keyboard.** `set_visible`
  must go through `win32.set_window_shown` (`SW_SHOWNA`), never
  `FLAG_WINDOW_HIDDEN`: raylib unhides via `glfwShowWindow`, GLFW's
  `GLFW_FOCUS_ON_SHOW` defaults on, and `WS_EX_NOACTIVATE` does **not** stop
  it. Measured with `GetGUIThreadInfo`: strip visible at 1.62s, foreground at
  1.64s, *keyboard focus* at 1.69s. Anyone mid-sentence lost the rest of it.
- **That one only reproduces when the owner is in another process**, and it
  cost the fix a whole round trip. A harness whose fake host was a window in
  its own process showed no theft at all, twice, and was believed over the
  live daemon; the correct fix was reverted on the strength of it. If a
  reproduction disagrees with the running system, the reproduction is wrong
  until proven otherwise. `/tmp`-style scratch harness that *does* reproduce
  it: run the real `Overlay` in-process with an `OverlayWindow` subclass that
  checks `foreground_root()` after each window call, and pass it the handle
  of a real window belonging to some other application.
- **A session whose `Stop` never arrives used to think forever**, and the
  strip stayed up with it. The transport cannot promise delivery, and "the
  next event corrects it" is no correction when there is no next event for
  that session. `max_thinking_seconds` (default 900) gives up on one that has
  said nothing for that long; any event from it refreshes the clock.
- **A leaked daemon looks exactly like a window bug.** The same investigation
  first blamed the show path for a 10Hz flap that was really three daemons
  fighting. Check `brainrot doctor`'s `instances` line before theorising.
- **A blend mode does not stop a draw writing depth**, and the symptom is
  *missing geometry* with nothing pointing at what removed it. Additive glows
  stamped their whole quad -- soft, mostly transparent, and at alpha 0 for an
  orb right at the lens -- into the depth buffer, deleting every block drawn
  after them and further away. Measured at up to 1,678 px of the frame for the
  lanterns and **25,589 px (8%) for the landing dust burst**, which nobody had
  suspected. Everything emissive now goes through `fx.no_depth_write` /
  `fx.emissive`, and parkour queues its glows and issues them in one pass after
  all the opaque geometry -- depth writing off is not enough on its own,
  because a glow drawn between two blocks is still *composited* between them.
  Both flushes inside those context managers are load-bearing in opposite
  directions: rlgl issues batched draws late, the depth mask changes at once.
  Audited the whole class with `tools/depth_probe.py`: glows, bursts, cloud
  shelves and reef discs were all guilty and are all fixed; the haze band is 2D
  and writes no depth; islands are solid land and *must* write depth, and
  cannot reach the course anyway because everything in the world below tops out
  at least 7 m under the lowest altitude the course may use (now a test).
- **A booked action can only fire on a frame boundary.** The planner solves a
  take-off window in continuous time and the loop fires it on the next frame,
  so the body always leaves the ground a little late — and near the ends of an
  arc the feet move most of a third of a metre in one frame at top speed,
  against a nine-centimetre clearance margin. `solve_jump`/`solve_roll` take a
  `late` argument for exactly this and the scene passes it the real `dt`. The
  margin cannot be asked to absorb it: inflating the required height instead
  makes the window vanish entirely.
- **The reflex is a last resort, not a competitor.** It fires at the *edge* of
  a take-off window; the planner books the middle of one. Letting it fire when
  a take-off was already booked replaced a good jump with a marginal one, and
  the feet came down three millimetres inside the hurdle it had cleared.
- **Gantries are only scenery if a *jumping* body clears them.** The height
  was typed in, and the test that guarded it asked for half a metre over a
  standing runner — against an apex of over a metre and a half. `GANTRY_Y` is
  derived from the apex now, and typing it in is no longer possible.
- **`id()` is reused.** A probe that counts live entities by identity
  undercounts by an order of magnitude, because a retired entity's id is
  handed straight back to the next one. The scene counts spawns itself
  (`RunnerScene.spawned`).
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
- Run `python -m pytest tests/` before committing; it is fast (~60s). 545
  tests. The Win32 suite skips off Windows and the X11 suite skips without a
  display, so a green run means less on the other platform's machine -- check
  the count.
- `brainrot doctor` is the per-machine check and knows about both platforms;
  `brainrot extension status` reports on the gnome-shell half alone.
- Art direction is done by looking at `brainrot shoot` output. That only works
  if the capture is honest, so there are tests on the capture itself: colours
  survive, the frame is the right way up, and drawing the same state twice
  draws the same picture (`draw()` must not advance anything).
