# Architecture

## Shape

```
Claude Code
    │  hook fires (UserPromptSubmit, Stop, Notification, SessionEnd)
    ▼
brainrot_hook.py            ~30ms, one UDP datagram, cannot block or raise
    │                       (on Windows: carries the foreground window handle)
    ▼  127.0.0.1:47821
Overlay daemon (long-lived)
    ├── ipc.EventListener      UDP receive on a background thread
    ├── state.ThinkingState    events + time  ->  visibility
    ├── engine.loop.Overlay    frame loop, fade, scene lifecycle
    ├── engine.window          raylib window: overlay / desktop / headless
    ├── scenes.*               generated worlds
    └── overlay.win32          click-through + owned-window layering (ctypes)
```

## The decisions that shaped everything

### 1. Hooks, not polling

Claude Code fires shell commands on lifecycle events, which gives an exact
signal for "started thinking" and "stopped thinking". The alternative — tailing
session transcripts and inferring state — is both laggier and coupled to a file
format that is not a public interface.

Only `UserPromptSubmit` and `Stop` are needed, and both fire **once per turn**.
`PreToolUse`/`PostToolUse` fire on every tool call and are therefore left
opt-in (`--with-tool-events`); they buy nothing but a live tool-name caption.

### 2. UDP, because hooks block Claude Code

The shim runs inside your session's critical path. A hook that hangs hangs
*your editor*. UDP was chosen for what it cannot do:

- no connect handshake, so a dead daemon cannot stall the shim;
- no delivery guarantee, so a wedged daemon cannot apply backpressure;
- a lost packet costs at most one missed show or hide, corrected by the next
  event.

The shim additionally runs under `python -S` (skipping `site`, most of a cold
interpreter's startup), imports only builtins, wraps its whole body in a bare
`except`, and on Windows runs under `pythonw.exe` so no console window flashes.

A dropped frame of brainrot is free. A stalled editor is not.

### 3. Busy != visible

`ThinkingState` is not a passthrough. It applies a grace period, a minimum
visible duration, refcounting across concurrent sessions, and suppression while
Claude waits on you. Without these the overlay strobes on short turns and
flashes on fast ones, which is worse than not existing.

The clock is injected, so all of it is tested without sleeping. The timing
logic is also derived from timestamps rather than from tick history, so a burst
that begins and ends between two frames is still judged correctly.

### 4. Crafted assets, generated worlds

The first version generated every pixel in software, which capped how good it
could ever look. The current split:

- **Assets are crafted, reproducibly.** Every model is a glTF file built by a
  Blender script committed to `assets/src/`, run headless. Nothing is
  downloaded and nothing is hand-exported from an opaque tool; delete
  `src/brainrot/assets/data` and `python assets/build.py` recreates it
  byte-for-byte-*equivalent* — measured, that means every recorded bound and
  every recorded animation frame comes back identical while about half the
  .glb files differ in bytes, which is the bake's own dithering and nothing
  more. `bpy` is reached either as a wheel in the venv or as a standalone
  Blender the build script goes looking for, because the wheel trails Python
  releases by a year or so and a project should not be pinned to an old
  interpreter by its art pipeline.
- **Worlds are generated, uniquely.** Which track, which palette, which sky,
  which trains where — all drawn from a seed that never repeats.

### 5. On screen only while you are looking at Claude Code

An overlay that floats above *everything* is a universal window; this one
should belong to Claude Code. The shim reads the foreground window at event
time — the window you submitted a prompt from *is* the Claude Code host — and
sends its handle with the datagram. Only a *prompt* is trusted for this: a
Stop or a tool event fires whenever Claude gets there, which may well be while
you are reading something else.

Two mechanisms, answering two different questions:

- **Where in the stack.** The daemon makes the overlay an **owned window** of
  the host (`GWLP_HWNDPARENT`). Windows keeps an owned window exactly one
  z-level above its owner, so the strip rides above the terminal. Ownership
  binds lifetimes as well as z-order, which is why the daemon detaches
  whenever it goes idle.
- **On screen at all.** Ownership only decides what covers what — a window
  that does not happen to overlap the strip leaves it in plain sight over
  whatever you switched to. So each frame the daemon compares the real
  foreground window against the hosts of the sessions that are currently
  working (`follow_focus`, on by default) and fades out when it is neither
  those nor the overlay itself. Nothing known about a session's window means
  hidden; "show over everything until we learn better" is the wrong default in
  both halves.

- **Where on the desktop.** Also from the host window, not the monitor: a
  screen edge is exactly where an editor keeps its sidebar. `place()` in
  `engine/window.py` puts the strip *beside* the host window when the desktop
  has room for it there — covering nothing at all — and otherwise into that
  window's own margin on the `dock` side, which on a maximised app is the
  gutter outside its content column. Recomputed every frame, so it keeps
  station on a window being dragged or maximised underneath it. Pure geometry
  with the window rectangles passed in, so it is tested without a desktop.

`attach = "topmost"` and `follow_focus = false` restore the older, blunter
behaviour for demos and recordings. All of it is ctypes; there is no pywin32
dependency.

### 6. Two platforms, one vocabulary

Every question above — is this window click-through, where is it, who is in
front, how big is a pixel — is asked of a *backend*, resolved once by
`overlay.native()`. The engine above it contains no platform tests at all.
The two backends are shaped very differently underneath:

- **Windows** (`overlay/win32.py`): one API knows about every window, so most
  of the contract is one call under a name that does not presume it.
- **Linux** (`overlay/linux.py`): two halves that fail independently, and the
  seam is the interesting part.

#### Why the Linux strip is an X11 window on a Wayland desktop

GNOME 49 dropped the X11 session, so Ubuntu 25.10 and later are Wayland-only.
That removes the *session*, not the protocol: XWayland is still there, and
mutter runs a real X11 window manager for it. This matters because a Wayland
client is forbidden — by design, not by omission — from doing every single
thing an overlay is made of: it cannot know where it is, move itself, raise
itself, or shape its input region.

An X11 client can do all four, and mutter honours them for XWayland windows.
So the daemon asks GLFW for the X11 backend before raylib initialises it
(`x11.prepare()`, a `glfwInitHint` before `InitWindow`) and does its window
surgery in X11. Measured against the live compositor on GNOME Shell 50.1:
position honoured to the pixel, `_NET_WM_STATE_ABOVE` stacking the strip above
native Wayland windows as well as X11 ones, an empty XShape input region
making clicks fall through, and a window whose `WM_HINTS` say it takes no
input mapping without moving the keyboard.

#### Why there is a gnome-shell extension

Two questions X11 cannot answer on that desktop, and one it answers wrongly:

- **Who is in front.** `_NET_ACTIVE_WINDOW` names only X11 windows, and Claude
  Code's host is usually a Wayland client. `org.gnome.Shell.Introspect` exists
  for exactly this and refuses: *"GetWindows is not allowed"*.
- **Where the Claude Code window is**, which is what `place()` needs.
- **Where the pointer is.** `XQueryPointer` answers — with the last position X
  saw, which over a Wayland surface is stale and plausible. Measured: y = 1564
  on a screen 1728 tall, pointer nowhere near it.

So a small extension (`src/brainrot/extension/`) runs inside gnome-shell,
where all three are ordinary calls, and pushes snapshots to the daemon's
existing UDP port — no D-Bus client in the daemon, no new dependency, and a
daemon that is not running simply drops the packets. It idles at 4 Hz and
speeds up to 60 Hz only while a modifier is held, which is the only time the
pointer position is worth paying for.

It is **optional on purpose**. Without it the strip docks to the work area and
stays up for the whole turn; `linux.focus_known()` is what keeps those two
states distinguishable, because a backend that cannot tell "nobody is in front"
from "I cannot see who is in front" either hides the overlay forever or shows
it over everything.

#### The host window, without a window handle

The Windows shim reads the foreground `HWND` at event time. On Wayland there
is no such thing to read — a client cannot be told about windows, its own
included. So the shim sends its own **process ancestry**, nearest first: the
terminal or app running Claude Code is one of its ancestors. The daemon
matches that against the window list the compositor reports (`Snapshot.
host_for`), which is also why nearest-first matters — a shell inside a
multiplexer resolves to the window you are actually looking at.

#### Two coordinate spaces

The compositor counts in logical pixels; X11 counts in device pixels; on a
200% display those differ by a factor of two. Rather than trusting a scale
factor from either side, the ratio is **measured**: the X screen width divided
by the logical desktop width, two numbers each side can read directly
(`Snapshot.scale_against`). Everything crossing `overlay/linux.py` is
converted there, so `place()` above it is pure geometry in device pixels, and
`cfg.width` keeps meaning "the size it should look".

The strip is then a device-pixel window with the scene drawn into a
render texture at the config's size and scaled on the way out — the scenes
keep their own pixel geometry, so a HUD chip is 14 points high because that is
what looks right rather than because of the display.

Two things Windows can do that this cannot, both recorded here so they are not
rediscovered: an *owned* window (mutter has no notion of an X11 window owned by
a Wayland one, so `follow_focus` rather than z-order is what keeps the strip
off other applications), and hot-installing the extension (gnome-shell only
scans for new extensions at startup; `ReloadExtension` over D-Bus answers
*"deprecated and does not work"*, so installing marks it enabled in gsettings
and the next login switches it on).

## Never repeating, and replayable anyway

Those two goals conflict unless you separate *which run is this* from *how is
it generated*.

**Uniqueness** comes from a monotonic counter persisted to disk. Two runs
cannot share a seed because two runs cannot share a counter value — no
randomness is involved, so there is no collision to reason about.

**Independence** comes from substreams. Each generator draws from
`seed.stream("palette")`, `seed.stream("row13")` and so on, derived by hashing
the root seed with a label. Changing how obstacles generate does not shift the
palette, which is what makes generated content tunable at all.

**Replay** is then free: `--seed N` reconstructs run N exactly, and the test
suite asserts this at the pixel level — the same seed renders byte-identical
frames.

Hashing is BLAKE2b rather than Python's `hash()`, which is salted per process
and would silently break replay across daemon restarts.

Hues come from the golden-ratio sequence indexed by run number, not from the
RNG: uniform random hues cluster, so consecutive runs would occasionally look
near-identical. `GENERATION_EPOCH` in `rng.py` re-rolls every generator without
disturbing the counter — epoch 2 is the raylib rebuild.

## The rendering contract

raylib's default shader computes `texture x material colour x tint` per pixel,
identically on the GPU build (what users run) and the software rasteriser
(what CI and `brainrot shoot` run). The whole art pipeline is built to need
nothing else:

- **Lighting is baked at asset build time.** Each Blender script unwraps its
  model, bakes sun + sky + AO into a grayscale map (`DIFFUSE` with the colour
  pass disabled, so the bake is independent of albedo), and wires it as the
  base-colour texture. One shared sun direction across all bakes keeps mixed
  assets consistent.
- **Colour lives in named material zones** (`hoodie`, `body`, `wall`,
  `window`...). The glTF material order is stable and raylib maps glTF
  material *i* to slot *i + 1*, so the runtime reads zone names from the GLB's
  JSON chunk and recolours by writing one material colour. Trains get per-run
  liveries, buildings get night-lit windows, the runner gets an outfit — no
  lighting maths anywhere.
- **Fog is the draw tint.** Every entity is drawn with a tint interpolated
  toward the palette's fog colour by distance. The parkour scene needs haze
  *between* the world below and the course, so it draws the ocean and islands,
  exits 3D, lays a smooth alpha gradient, and re-enters the same camera for
  the course — the haze writes no depth, so the course still depth-tests
  correctly. A tint *multiplies*, so fogging a dark object toward a dark fog
  colour only makes it darker; anything meant to recede into a night sky or a
  night sea fades on alpha as well.
- **A blend mode does not stop a draw writing depth.** This is the single
  most expensive lesson in the renderer, because its symptom is *missing
  geometry* and nothing about a missing block points at the sprite that
  removed it. `BeginBlendMode(BLEND_ADDITIVE)` changes how a fragment is
  combined; the fragment is still recorded in the depth buffer, alpha and all.
  A glow billboard is a soft radial disc that is nearly transparent at its
  edges and fully transparent outside them, and it was stamping that whole
  quad into depth — so every block drawn afterwards and further away was
  rejected. From the outside that is an invisible wall in the level.
  `engine/fx.py` owns the fix as two context managers, `no_depth_write` and
  `emissive`, and nothing draws a translucent overlay without one. Both flush
  the render batch on the way in *and* on the way out, because rlgl issues
  batched draws late while the depth mask changes immediately — get either
  flush wrong and the state that reaches the driver is not the state the code
  reads as having set.

  Turning the writing off is only half of it. A glow drawn *between* two
  blocks is still composited between them, so the nearer block paints over the
  glow that was meant to be in front of it and a lamp flickers as the course
  goes past. Parkour therefore queues its glows during the geometry pass and
  issues them all at the end of the frame through `fx.glow_pass`, which is
  also one blend-mode switch per frame instead of one per lantern.

  `tools/depth_probe.py` is how this is checked rather than argued about. It
  renders a frame twice — the second time with one draw's depth writing turned
  off, nothing else changed — and counts the pixels that differ. Zero is proof
  the draw hides nothing. It also intersects those pixels with a silhouette of
  the course, because scenery sixty metres below mis-tinting other scenery is
  not what anybody is looking at.
- **rlgl has two draw paths and they do not run in call order.**
  `DrawPlane`, `DrawLine3D` and friends queue vertices in the render batch,
  which is not submitted until something forces it (usually `EndMode3D`).
  `DrawModelEx` issues its draw call immediately. A ground plane drawn "first"
  is therefore drawn *last* and loses the depth test to everything standing on
  it — invisible under opaque models, and very visible under transparent ones.
  `rl.flush()` submits the batch; both scenes call it after their ground plane.
- **Vertex colours are banned.** The software rasteriser ignores material
  colour and tint whenever a colour attribute is present, which would make CI
  frames diverge from GPU frames. The exporter strips them.

Two things the first version taught us are kept: the sky is a 2D backdrop
(gradient, sun/moon disc with an additive glow, seeded stars, parallax cloud
sprites) drawn before the 3D pass, and weather is screen-space streaks over
it, exactly like the reference material.

### Voxel blocks

The parkour course does not use Blender assets at all. The entire Minecraft
look is three cheap tricks, baked into 16x16 pixel-art atlas textures at scene
construction: vanilla's face-shading constants (top 1.0, north/south 0.8,
east/west 0.6, bottom 0.5), a baked corner gradient standing in for vanilla's
smooth lighting, and a **texel pattern** — planks, brick courses, stone
brick, a Voronoi cobble, wool weave, concrete, quartz striation, ore fleck, a
glowstone lattice, leaves, sand, dirt. The pattern is what makes a material
legible at a glance without the eye having to resolve its edges, and it is the
difference between a course of coloured cubes and a course of *things*.

Two rules about those patterns, both learned by looking at them at the size a
block actually occupies on the strip (`tools/atlas_sheet.py` renders every one
at texel scale and at block scale, side by side, which is the only way to
judge this):

- **Detail lives at the top of the range.** Small amplitude, high frequency.
  The first version drew four enormous bricks and an eight-texel
  chequerboard; at block scale that reads as a *stamp on a plastic cube*
  rather than as a material. The only strong darks left are structural —
  mortar, plank seams, the gaps between stones.
- **Corners darken, edges darken less.** There is no neighbour information at
  texture-build time, so the gradient is baked as if every block had
  neighbours. The error on a lone floating block is a slightly rounded look,
  which is the harmless direction; without it a wall of identical cubes reads
  as one surface rather than as cubes.

One shared unit-cube mesh carries per-face atlas UVs; each style is a material
wrapping it, and `draw_box` scales it per axis, so slabs, panes, posts, beams
and tree trunks all cost one mesh and no new geometry.

### Meshed chunks, for the static half of a world

One cube per draw call is the right answer for a course of a dozen platforms
that pop in, fade and move. It is the wrong answer for *architecture*. The
spiral scene's tower — a solid cone, its flank, its fluted skin, and the floor
slab of every level of the helix — is thousands of cells a layer, and at roughly
seven microseconds of Python per `DrawModelEx` that is the whole frame budget
spent on scenery nobody lands on.

`engine/chunk.py` builds the static half the way the game does:

- **One texture for every material.** Each style's six face tiles
  (`voxel.face_strip`) are stacked into a single image, so a mesh may mix
  brick, glass and gold and still be one draw call. Without it a chunk costs
  one call per material in it, and the interesting chunks are the ones with
  six.
- **Only the faces you can see.** A face is emitted where its neighbour cell is
  empty or see-through, culled against the *whole world* rather than the chunk
  — so seams are clean, hollowing a building out costs nothing, and filling it
  in costs nothing either. That second half is what makes the spiral's tower a
  *solid* mass rather than a shell: a solid disc of radius nine is 250 cells a
  layer and about 40 faces.
- **Drawn only if it could be on screen.** A distance cull keeps a *sphere*
  around the camera, and this project's window is a tall narrow strip with
  about fifty degrees of horizontal field -- so most of that sphere is behind
  the viewer, and every chunk of it was a draw call and a pass over its
  vertices for nothing. `draw` takes the camera's own direction and drops
  anything outside a generous cone around it: worth a third of the spiral
  scene's frame, where the body in its trough has a whole tower behind it.
- **Cells can be taken away again.** `ChunkedVolume.clear` exists because the
  spiral's terrain is *dug* as well as built — a pond is a hole in the terrace
  with water in it, and a blue square painted on top of the floor is not one.
  It costs one dirty chunk: a chunk's cell list is only walked when it is
  re-meshed anyway.
- **Cut into cubic chunks, and that is about fog rather than culling.**
  Distance fog is a per-draw tint, so everything in one mesh recedes by the
  same amount; a whole tower in one mesh would fog its near wall and its far
  wall identically. At eight cells a chunk the error inside one is under a
  tenth of the fog range.

Building is the expensive half — about 7 µs a face, so a 250-face chunk is
under two milliseconds — and it happens off the frame that needs it:
`build_pending` takes a budget and the scene gives it two chunks a frame,
generating far enough ahead that a mesh is never wanted the frame it is made.
Drawing is nearly free: measured at 0.78 ms for twenty chunks of 3,600 faces,
which is forty times more geometry than a tower ever has on screen.

Two raylib details this module owns, because they corrupt memory rather than
look wrong. **A mesh raylib will free must be allocated by raylib** —
`UnloadMesh` calls `RL_FREE` on `mesh.vertices`, and handing it a cffi buffer
kills the process inside libc, so every array is `MemAlloc`'d and filled with a
memmove. And **the material is process-global with its texture swapped per
draw**, because `LoadMaterialDefault` allocates and a scene that built one per
run would leak a map array per run for the life of the daemon.

Because the kit in the player's hand is assembled from those same shared
models, anything that writes to a model — notably `model.transform` — must put
it back. It did not, once, and every plank walkway in the world drew tilted.

### Texture lifecycle

Exactly one scene is ever alive, and every scene's textures (sky gradient,
clouds, block atlases — all keyed by run number) are unloaded when the next
scene is built. Without this a long-lived daemon leaks a scene's textures per
run, and the software rasteriser — which has a finite texture pool — stops
rendering entirely within a handful of runs. Glow sprites and discs are
process-global; GLB assets stay resident and are shared across scenes.

### Skinned characters

The runner is one mesh, rigid-skinned per part to a 7-bone armature (rigid on
purpose: joints bend, boxes stay boxes). Run, jump and roll clips are sampled
into glTF animations by the asset script and CPU-skinned at runtime
(`UpdateModelAnimation`), which the software rasteriser supports — so CI sees
the same poses the GPU does.

## Scene formats, from the reference material

- **runner** is third-person chase cam over three locked lanes, because that
  is what Subway Surfers footage is. World streaming follows the industry
  pattern (spawned ahead, destroyed behind, drawn from a per-row substream so
  a run replays).

  Content is laid down a **set-piece** at a time, not a row at a time, for the
  same reason the parkour course is: a uniform stream is watchable for about
  ten seconds. `SEGMENT_TABLE` is the vocabulary — a cruise, a rhythm of
  hurdles, a slalom the corridor weaves through, a tunnel of hoardings to
  slide under, a train yard, an express the other way, and a ramp onto a train
  roof. A set-piece never follows itself, and each one decides a stretch of
  track *and the corridor through it together*, which is the only way to
  express a weave, a yard or a roof run at all: the row-at-a-time generator
  this replaced could only say "put an obstacle here" and then defend itself
  with spacing rules. What it produced was safe and repeated itself inside ten
  seconds — measured over twelve minutes, 7.6 hurdles a minute, 0.2 hoardings,
  and the slide appearing about once every five minutes.

  A set-piece that finds the track it wanted occupied **declines**, and is
  rewound whole. Every ledger it writes to is append-only so that rolling one
  back is a truncation; without that, a segment that wrote a corridor and then
  gave up left those rows for the next one to overwrite from a different
  starting lane, and a corridor that steps two lanes in one row is a promise
  the body cannot keep.

  The runner also **rides train roofs**, which is the one thing in either
  scene that needed the motion model to grow: `Motion` carries the height of
  the surface under the feet, lands on whatever the arc comes down to, and
  starts falling when that surface drops away. A ramp is therefore a floor
  rather than an obstacle, and appears in `RunnerScene.surface_at` instead of
  in the threat list.
- **parkour** is **first-person**, because the real Minecraft-parkour reels
  are recorded first-person on infinite-parkour servers. The generator starts
  from the plugin that produces most of that footage — weighted gap (2-5
  blocks) and rise (-2..+1) tables, Gaussian lateral drift steered back toward
  a spine, blocks despawning two behind — and then works in **set-pieces** on
  top of it, because a uniform stream of cubes is only watchable for about ten
  seconds. `SEGMENT_TABLE` is the vocabulary: staircase, plank causeway,
  spiral round a brick tower, gate you run *through*, long fall, lantern walk,
  chasm, a field of capped columns, a ruined wall, a run of half-height slab
  landings, and a squeeze of beams to skim under and columns to clear. A
  segment never follows itself, and which ones are eligible depends on which
  way the course has drifted within its altitude band — so verticality comes
  from steering generation rather than from vetoing it.

  **The course also gets harder as it goes.** `difficulty` runs 0 to 1 over
  the first eighty blocks laid, and every set-piece draws its gap from a pair
  of tables through `_gap` rather than from a constant — the ramp has to reach
  the whole vocabulary, because the cruise is only about a fifth of the blocks
  and ramping it alone moved the median hop by two centimetres. `SEGMENT_RAMP`
  applies the same idea to which set-pieces get chosen, which is the half a
  viewer actually reads: a squeeze arriving instead of a plank causeway is a
  change of subject, where a wider gap is only a number. It is counted in
  blocks laid and not metres travelled, because generation runs fourteen
  blocks ahead of the body and because the probes grow a course without ever
  moving one.

  **A beam over a gap is built against the arc that will be flown under it.**
  Where the feet leave and land is known when a block is generated, so the
  exact flight is a list of points, and a lintel hung a body's height above
  the highest of them — or a column topped out just below the lowest — is
  guaranteed to be missed while looking as though it will not be. `HEADROOM`
  still keeps two cells clear over every *landing*; what the squeeze relaxes
  is the space over the **gap**, which nothing ever needed. Note the shape of
  the limit that fell out of this: the arc apexes under a metre above the
  surface it left, because `flight` solves the take-off for the two endpoints
  rather than using vanilla's full jump — so a column in a gap tops out level
  with the course and there is no room for a taller one.

  Four things carry the weight, and all four were rebuilt after the scene came
  back with "the blocks are inside each other and the running feels scripted":

  - **The course is on an integer lattice.** Headings stay continuous, because
    a course that may only run along eight compass points looks like a maze;
    but the *placement* those headings produce is snapped to whole cells, and
    two cubes at whole cells cannot be inside one another. The previous
    generator asked only whether the next block's centre was 1.45 m from a
    recent one, which is not a question about volumes at all: measured over
    eight thousand blocks, one pair in two interpenetrated, worst case nearly
    a whole block deep. It is now zero by construction.
  - **`_solid` is the occupancy map, and it is asked four questions.** Are the
    block's own cells free; are the two cells above the landing free (a body
    is 1.8 m tall and has to fit); is the hop one a body can make; does the
    *arc* pass through anything. Candidates are tried in order of how close
    they are to what the set-piece asked for, so the first that satisfies all
    four is also the nearest thing to what was wanted.
  - **Motion is vanilla's, in vanilla's numbers.** One gravity, one jump
    impulse, one sprint speed, one sprint-jump speed. `flight()` is now a
    single line — horizontal speed is *constant*, so a hop's duration is its
    length over that speed and the take-off is whatever lands you on the far
    end. Whether that take-off is one a body has is a separate question, asked
    once, in `_fits`, which is why there is no table of legal gaps: `hop_span`
    derives them. The body also never stops. It lands on the near edge of a
    block, runs across it, and leaves from the far edge — so the gap it
    actually clears is wider than the gap between block centres, and the beat
    on each block is a run-up rather than a pause.
  - **The course knows its own path.** Where the feet touch down and leave is
    decided when the block is generated, so the exact ballistic arc of every
    future hop is computable at generation time. Orbs are hung *on* that arc
    at chest height, which makes "every orb laid down is collected" a property
    of generation rather than a hope about the simulation. A player who jumps
    early moves the take-off, so the arc is re-solved at that moment and the
    orbs on it move with it — on autopilot the two are the same numbers.

- **spiral** is the *other* Minecraft reel format, and a different thing rather
  than a reskin of the first: the **Parkour Spiral** genre, where the course
  winds up the outside of a tower that keeps going out of the top of the frame.

  **The reference was misread twice, and that is the headline.** The owner's
  screenshot is a view of the tower's *underside*, which looks like a forest of
  grey columns. The first attempt built a cylinder with jump blocks hung round
  the outside. The second read the columns as *stilts* and built a stack of
  hexagonal platforms standing on legs. Hielke's own screenshots of Parkour
  Spiral 1-3 say it is neither:

  - The tower is **one solid mass**, and it is an **inverted cone** — narrow at
    the waterline, flaring as it rises. Every wide shot shows it. `BASE_R` is
    24 and `FLARE` 0.05, which is measured off the reference: about 1.7 times
    as wide at the crown as at the waterline over roughly fourteen revolutions.
  - The "column forest" is the **skin, not the structure**: vertical one-cell
    ribs alternating in and out for the tower's whole height, a corduroy
    surface. Full-resolution crops of the underside show them running unbroken
    from the themed lip down into the sea with nothing behind them. `RIBS` is
    56, which at the base is a rib every 1.9 cells, and `rib_out` takes them
    from the *bearing* rather than from arc length — arc-length ribs drift up a
    cone whose circumference is growing and read as a barber's pole.
  - The parkour is a **helical trough** cut round the outside. You are always
    in a corridor: the drop and the sky on your outboard side, the fluted core
    on your inboard side, and the floor slab of the turn above as a ceiling.
    `BAND` is 9.5 blocks wide and `FLOOR_T` 5 of a turn's 12 to 18 is slab, so
    the mass is around a third solid and the open gap seven to thirteen blocks.
    At three in sixteen the ledges came out as thin plates with daylight
    between them from every angle, which is not what any reference shot looks
    like.
  - **Several themed sections fit in one revolution**, not one — a single band
    in the reference runs end, farm, village, plains, mesa in one arc — and the
    seam between two is **hard**, with no blending. Three to a revolution
    (`LEVELS_PER_TURN`), six to ten seconds of strip each. Fifteen themes come
    out of a shuffled bag.
  - **The parkour is built into the theme's own ground.** You run over the
    desert's dunes and across its pond on lily pads. Floating blocks over the
    void are the minority and they are a *theme* — the wool section — rather
    than the default. Measured: 92.2% of landings are the level's own terrain
    or something built down to it.

  **And the trough is not a ramp: it is a stack of levels.** This is the second
  correction and it came from the owner looking at a render of the finished
  tower and saying *without the parkour you could still just walk up this*. He
  was right, and it was a property of the geometry rather than of the course —
  the trough climbed one block every eight blocks of arc, which is a spiral
  staircase, and a body walks up one-block steps without noticing. Every
  landing the generator laid was optional scenery on a ramp that already went
  all the way to the top.

  A `Section` is therefore a **level**: a flat themed terrace, then a chasm
  with no floor in it at all (`GAP_ARC`, 2.8 to 3.9 blocks of arc), then the
  next terrace `LEVEL_RISE` — four to six blocks — higher. You cannot walk over
  a hole and you cannot walk up four blocks, so neither half is passable and
  the only way out of a level is the parkour out of it. That is proved rather
  than asserted: `tools/spiral_probe.py`'s `walkability` flood-fills the **cone
  alone** — no course blocks, no pedestals, no dressing — from the start point,
  stepping at most one block up and dropping any survivable distance, and
  reports the highest it gets. **0 m at worst over six runs**, and
  `tests/test_spiral.py` holds the same line.

  Everything about that arrangement is forced by something:

  - **One turn is a whole number of levels** (`LEVELS_PER_TURN` = 3). The
    ceiling over level `i` is the floor slab of level `i + LEVELS_PER_TURN`;
    were that not an integer count, soffit and floor would step at different
    bearings and saw up and down against each other.
  - **The rises vary**, so a revolution gains 12 to 18 blocks rather than
    always 22. That was the other half of the same complaint — a tower that
    gains exactly the same height every revolution reads as a machine part.
  - **`Cone.unwrap` is no longer a division.** It was one while every turn rose
    by a fixed amount, and it cannot be now: the levels at a bearing are `j`,
    `j + 3`, `j + 6` … and their floors strictly increase, so it estimates from
    a constant-rate tower and then walks to the last floor at or below the
    height. That walk is why `Course._rock` memoises `Cone.rock`.
  - **The exit climb is the load-bearing feature**, about 44% of all landings.
    It is themed: a staircase of ledges against the core, or a ladder, a vine
    or a soul-sand bubble column where the place has one (`Theme.exits`).
    Stairs are weighted well above the vertical climbs and the reason is
    measured, not aesthetic — stair-only exits fall through to the unchecked
    hop on 2.35% of landings and mixed exits on 3.05%, because a ladder needs a
    free column, an anchor and a launch block hard against the wall and any of
    the three can be missing. What the treads are made of, and what riding them
    is, is the theme's to say (`Theme.step`, a `(material, move)`): the climb is
    over forty per cent of every run, so one stone and one hop in all fifteen
    places was the largest single source of sameness in the format. The farm
    climbs hay, the nether soul sand, the mine oak, the end purpur — and the ice
    level climbs packed ice, where the steps off it are *slides*, which reach
    further than a hop for the same rise.
  - **The crossing descends one block**, which is what makes the widest chasm
    crossable at all: `hop_span(-1)` allows 2.35 to 4.98 m stand point to stand
    point where a flat sprint jump reaches 4.26. So the staircase climbs one
    *above* the level it is heading for and the last jump comes down onto it,
    which also means you see where you are going before you commit.
  - **A stranded body is the failure mode everything else defends against.** A
    landing low in a chasm cannot be left — the far wall is four to six blocks
    up and nothing jumps a chasm and climbs it in one move — so the exit climb
    re-plans from inside the hole and lays its staircase through the one
    already there. Two rules stop it: the staircase is confined to the level's
    own ground (`node["confine"]`), and nothing may be placed in a chasm below
    the far level's floor (`Course._far_floor`). Negotiating that away one case
    at a time never got below two per cent.
  - **`hug` is a distance, not a flag.** An exit climb laid mid-lane finds no
    anchor — the only thing always there over a chasm is the tower — and that
    was 96% of every run that got stuck; but hard against the wall at 1.0 it
    filled the lens with masonry on every frame the body stood at the top of a
    ladder. The column stands one cell back from the landing it caps, so at 1.6
    it still finds its anchor while the *body*, which stands on the landing,
    does not. 2.2 for the block it launches from, 2.4 for a staircase, which
    only wants to read as ledges cut into the wall. Standing back was also
    worth 0.90 points off the unchecked rate, because a landing further out
    leaves more of the band reachable from the top of a climb.
  - **A head-hitter is a checked constraint**, not a beam drawn near a jump:
    the lid goes into the arc's own clearance test and a landing whose jump
    would rise through it is refused. It sits three above the take-off rather
    than the genre's two, and the reason is in `_ceiling_cells` — a body is
    1.8 m tall and a jump reaches 1.25, so its head sweeps the two cells above
    every take-off, and a lid at two is a lid inside the player that the
    clearance test then rightly refuses every jump under. A faithful `2bc`
    needs the game's jump-cancel response in `parkourkit`, which does not
    exist.
  - **A landing is the level's own stone, and what marks it is that it is
    *lit*.** The candy palette is gone from this scene entirely. That is both
    what was asked for and where the map-making community landed: a
    contrasting jump block wrecks the theme and buys nothing mechanically,
    because a cake and a cobblestone have the same hitbox, and the fix is to
    light the landing face (`LAND_LIT_FAR` in the renderer — small radius, low
    alpha, enough to pick the next block out of a wall at a glance).
  - **Ladders and vines are thin models on a block face**, not 0.84-wide cubes:
    `assets/src/props_climb.py` builds a lattice and a ragged sheet, tileable
    vertically. Which face they are on is recorded when the column is placed,
    because working it out again at draw time is how you end up drawing a cube.
  - **A slab may not be a step in the exit stair.** A slab stands half a block
    up, so the step after it is asked for one and a half and there is no such
    jump. The climb's arithmetic is exactly one block a landing.

  Three modules, and the split is the interesting part:

  - `scenes/parkourkit.py` is the **kernel**: vanilla's motion numbers,
    `Move` (a list of legs with a speed each), `hop_span`, `fit_gap`, the
    lattice helpers, `body_cells`, and `MATERIALS`. It knows the shape of no
    building, and it was extracted **unchanged** from the ring-tower plan
    module that used to live here — because it is the part of that file that
    measured clean, and the part that had nothing to do with the building whose
    shape turned out to be wrong.
  - `scenes/spiralplan.py` is the cone, the levels, the course and its 35
    features besides the exit climb. **No raylib import**, deliberately: a
    24-run geometry sweep costs a few seconds and no window, and neither does
    the walkability check.
  - `scenes/spiral.py` is the renderer, and nothing else. It meshes what the
    plan describes, moves a body along it and points a camera; the only two
    questions it asks about the building are "is this section lit by the sky"
    and "which way is along the trough".

  **The building is analytic, and that deletes a whole class of bug.**
  `Cone.rock(cell)` answers "is this cell inside the tower" in closed form, for
  any cell, at any time, with no memory — two rules, a flare and a wobble.
  Nothing has to be generated ahead of the course and nothing can appear behind
  it. The previous version streamed its building into an occupancy map as the
  course advanced, which meant a wall could be built through a jump that had
  already been solved; four reservations existed largely to defend against
  that. Three of them are still here (head-room, path cells, soft cells) plus a
  fourth for terrain (`ground`, the cells load-bearing *under* a landing),
  because terrain and course blocks are still written — but the case where the
  *building* grows into a solved arc is gone by construction.

  **The course is laid first and the terrain is painted around it afterwards**,
  which is the opposite of the previous attempt's order and the single most
  important thing in the file. A feature expands into nodes; each node is
  resolved against the world one at a time and never in advance; the landing is
  placed, its pedestal is built down to the ground under it, and the arc that
  reaches it, the run across it and the two cells over it are all *reserved*;
  and only then is the terrain painted, around what is reserved rather than
  through it. Terrain laid second cannot block a course. Building the world
  first and then negotiating a course through it started at **13% of nodes**
  falling through to an unchecked emergency hop; it was **0.46%** before the
  levels, 2.98% with them and **2.00%** now, which is still an honest
  regression — see "Solvability by construction" below. A human map-maker
  builds this way too.

  Three more things, each of which cost real time to see:

  - **A level's floor is one flat integer for its whole arc**, which retires an
    older defect rather than solving it again. Everything in this project that
    reasons about standing on a block depends on a cell's `y` being its floor
    and a surface being an integer; the helix used to climb continuously, which
    put the walking surface three quarters of the way up a cell and solved
    every hop off it against a height no block has. Quantising it to a
    staircase fixed that; making it flat and putting the climb in the parkour
    fixed the larger problem the staircase had.
  - **Nothing rises two blocks in one ballistic move**: a landing one block
    above the ground, reached from a landing *on* the ground across a step,
    asks for two. Measured before the clamp in `Course._targets`, at two thirds
    of the stuck cases *every* candidate had a rise of exactly +2.0. The clamp
    is for the ballistic kinds only — a ladder, a bubble column and a slime
    bounce all rise several blocks by design, and clamping those too took
    climbs and lifts from 3% of moves to none at all.
  - **The world is emitted outward from the body**, not upward from the bottom.
    The chunk mesher builds in the order cells were dirtied, so bottom-up means
    the first thing meshed is the world forty-six blocks *below* the camera,
    which is fog: 422 chunks were still unmeshed after the priming pass, three
    and a half seconds of a strip that lives for one thinking turn watching its
    own world assemble around it. `Course.build_world` takes a `y_from` and
    alternates out from it. The prime itself is bounded (`PRIME_CHUNKS`) for
    the opposite reason — scene construction happens at the moment the strip
    becomes visible, and meshing everything took it from 1.1 s to 1.6 s. For
    the same reason a run opens on `START_LEVEL` rather than at the base, and a
    fifth of the way into that level rather than wherever the arithmetic lands:
    the bottom of the tower has nothing under it to draw, and a run that opens
    beside a chasm opens looking at sea and sky in the three seconds every
    viewer sees.
  - **Dressing needs a margin around the running line.** `pathcells` is exactly
    body-width, so a cell merely *adjacent* to a jump is free by that test —
    and a block face half a metre from an eighty-degree lens is most of the
    frame. Without the margin in `_dressable`, a fifth of a contact sheet came
    back solid green, which reads as the camera being inside the world and is
    really the camera standing beside a boulder nobody meant to put there.

  **The camera is pure geometry and it decided a generation constant.** The
  body runs *outside* a convex core, so a camera looking along the trough is
  looking down a tangent — and a tangent to a circle you are outside of never
  meets it. Measured at a thirteen-block band: the core wall sat 50 to 90
  degrees off the direction of travel at every bearing, against a horizontal
  field of 52. The wall was drawn, correctly, on every frame and appeared on
  none of them; every frame was ground, sky and soffit, which reads as floating
  islands rather than as a tower. The fix is not aiming at it — aiming at it
  means running sideways — it is **standing nearer to it**, so `BAND` is 9.5
  and `COURSE_OUT` puts the course mid-lane within it. The renderer then blends
  the head's bearing toward the trough's own tangent (`TANGENT_MIX`), because
  aiming only at the next few landings swings the view out over the rim on
  every frame where the next hop goes outboard.

  Two smaller numbers worth knowing. `LIFT_MAX` is 6: the trough is seven to
  thirteen blocks of open air, a body needs two over its head, and a landing
  higher than that has the next turn's floor slab for a ceiling before it has
  anywhere to jump to. And `GAP_RAMP` is 0.26 — how much wider every gap gets
  between the start of a run and full difficulty, applied centrally in `_node`
  rather than left to each feature's own tables, because most features want a
  *fixed* shape and would otherwise sit out the ramp entirely. Measured before
  it existed: mean hop 2.62 m at the start of a run and 2.67 m two hundred
  landings in, which is a flat line with noise on it, in a scene whose whole
  pacing story is that it gets harder. The exit climb is exempt by name: its
  arc is reserved for exactly so many landings at exactly that spacing, and
  stretching it hangs the last steps of the staircase over the chasm.

  A word on the **furniture**, because it is the reason the terraces read as
  places. Crops, flowers, fences, lantern posts, sugar cane, torches, rails,
  end rods, chorus plants, bamboo, mushroom caps, cacti, dead bushes, pebbles,
  hanging vines and dripstone are the parts of Minecraft that are *not* cubes —
  two crossed quads, a post and two rails, a stalk a few pixels wide — and as
  cells they all come out as the same coloured box. They are models
  (`assets/src/props_mc.py`, `props_flora.py`, `props_deco.py`), fourteen of
  them per section, one draw call each, distance- and direction-culled like the
  chunks.

## Solvability by construction

Every scene could generate layouts that fail. None of them is allowed to, and
none of them checks afterwards — rejection sampling would stall inside a render
loop.

- **runner**: the guaranteed-clear lane is written by whichever set-piece owns
  the row, never derived afterwards, and may move by at most one lane between
  consecutive rows and no faster than a body can cross one. Two things are
  then asked before anything is placed:

  - **`_spans`, the occupancy ledger** — per-lane track occupancy in absolute
    distance, plus a separate list for what is hung *over* the track. Row
    counting stood in for this and could not see volumes at all: a 25 m train
    against a 6 m row is a great many rows of nothing being said, and the
    result was 9,731 frames per four runs in which two obstacles were drawn
    inside each other, the worst 2.18 m deep.
  - **`_acts`, the same idea for *moves*** — the stretch of track a jump or a
    slide commits the body to, so two obstacles that each demand one are never
    closer together than one move takes to finish. Volumes and moves are
    different questions, and the second one goes wrong at set-piece
    boundaries, where per-segment spacing rules cannot see each other.

  Parked trains only occupy lanes the corridor does not, asked over the
  train's whole *length* rather than the row it was spawned on. A yard may
  close two lanes at once — the old generator forbade that and had to, because
  while the corridor was a random walk it could not see, a second train could
  land across the only lane left; a set-piece writes the weave itself, so it
  can close everything the weave does not need and still promise a way
  through. At most **one** oncoming train exists at a time, and it is placed
  by solving for where it will *meet* the runner and working backwards: it
  closes at half as much again as the runner runs, and generation happens a
  full view-length ahead of the body, so a train laid at the far end of a
  set-piece passes the runner several rows *before* that set-piece begins, over
  track somebody else wrote the corridor for.

  A train with a ramp in front of it is the one case where the corridor points
  *at* an obstacle, because the way through is over the top. The lane choice
  and the mount are one decision: the train carries the single moment a
  take-off can happen, `classify` turns that into a `"mount"` action,
  `schedule_vertical` books it, and `plan.verify` rolls the lane path and the
  take-off forward together over a world that includes the train. If that
  fails the threat is marked hard and the search routes around it — into a
  lane the set-piece left empty for exactly this. Both outcomes are safe by
  construction, which is what the first attempt at this lacked: it chose the
  lane in one stage and decided the mount in another, so a rejected mount left
  the runner committed to a lane with a train across it.
- **parkour**: no hop is laid down that a body cannot fly. The invariant is
  stated against the take-off the hop *needs* — it must be between standing
  off an edge and vanilla's one jump impulse, and the arc must be on its way
  down when it arrives, or the body has come up through the side of the block
  rather than onto it. A set-piece asking for a gap its rise cannot support
  has that gap widened (`fit_gap`) before placement ever sees it; a drop
  cannot also be a short hop, because the body keeps its speed all the way
  down. Placement falls back through nearby rises and then through wider gaps
  and deeper drops, and the one emergency answer left at the bottom is counted
  in `scene.stuck`, which the tests hold at zero. Every orb the generator
  hangs is collected, which is asserted over two minutes of running and again
  over a minute of being steered by hand.

- **spiral**: the same discipline as parkour — it inherits the arithmetic
  wholesale from `parkourkit` — plus *reservations*, because the terrain here
  is written **after** the course it has to leave alone. The building itself
  needs no reservation at all: `Cone.rock` is analytic, so the cone cannot
  grow into anything. What is reserved is everything the course has committed
  to and nothing else can see:

  - `headroom`, the two cells over every live landing. Checking is not the same
    as reserving: head-room is *checked* when a block is placed, and a spiral
    comes back over itself, so a later block — or a pedestal driven down from a
    landing twenty blocks further on — lands in the space an earlier one was
    given to stand in. Measured as the body running for a second with three
    quarters of a metre of masonry through its head, which is not visible in
    any other way.
  - `pathcells`, every cell the body will pass through on a move already
    solved. This is the one the flat scene does not need, because a course that
    keeps going forward never lays a block where it has agreed to fly; a helix
    comes back over the same cells every revolution.
  - `softcells`, what a ladder, a bubble column or a cobweb is using — drawn,
    never solid, and a wall built through a ladder is a ladder in a wall.
  - `ground`, the cells load-bearing *under* a landing. Head-room covers what
    is over one and the path covers what the body passes through; neither
    covers the floor a `floor` landing stands on, because that landing places
    no block of its own. Without it a pond dug during dressing takes the floor
    out from under a landing already committed.

  Placement then separates *correctness* from *comfort*, and the split is
  load-bearing. A landing must be empty, have head-room, sit on something, be
  reachable by a move the physics has, and have a clear path — those never
  relax. That the body also fits comfortably where it lands and all the way
  across it is **comfort**, relaxed by the last resort, because a course that
  cannot satisfy those anywhere is better off grazing a bank than falling
  through to the one answer nothing checked. That last answer is counted in
  `Course.stuck`: **2.00%** of landings over 16 runs of 240 blocks, against
  zero cells claimed twice, zero landings off the lattice, zero ladders or
  water inside rock and zero orbs laid but not collected.

  **That 2.00% is an honest regression** — it was 0.46% before the trough
  became a stack of levels and 2.98% immediately after, and it is recorded
  rather than smoothed over. The reason is structural: a *mandatory* move is a
  far harder guarantee than a free one. The old course could wander when a
  landing would not fit; this one must leave every level, over a chasm, onto
  ground four to six blocks up, and that climb is 44% of all landings.
  `tests/test_spiral.py` holds the ceiling at 4% and says in its docstring that
  the number is worse than the 0.5% this scene used to make. The failure is
  concentrated in the ascent, and both reductions since have come from making
  the ascent itself easier to satisfy — standing the ladder back off the wall,
  and giving the ice level's stair a move that reaches further.

  When it does go wrong, the way to find out why is `TRACE` — a counter around
  `Course._attempt` recording *which* check refused each candidate. It is off
  by default because placement asks those questions a few thousand times a
  landing. Every reduction this format has had, from 13% of nodes down to a few
  per cent, came out of reading that table, and **not one of them was found by
  reading the code**. Rebuild it before changing anything here — the 2.00% is
  the next one to go after.

All of these are asserted directly in `tests/test_generation.py` and
`tests/test_spiral.py` across many runs, rather than being left as comments.

## Cost while idle

The daemon spends almost all of its life hidden. In that state it holds no
scene, renders nothing, and sleeps 80ms per iteration (draining the window's
event queue so the OS does not flag it unresponsive). Scenes are constructed
on the transition to visible and destroyed on the transition to hidden — which
is also what makes every appearance freshly generated.

## Layout

```
tools/                offline, never imported by the daemon
├── runner_probe.py   measures the runner's safety and its pacing: obstacles
│                     inside each other, the body inside an obstacle, how
│                     often the runner is forced to act and how long the idle
│                     stretches are, the obstacle and set-piece mix, the speed
│                     ramp, and how much of a run is spent on a train roof
├── parkour_probe.py  measures the parkour course and its motion: block
│                     interpenetration, grid alignment, emergency hops, the
│                     hop distribution and its difficulty ramp, and whether
│                     the body is ever inside a solid block
├── spiral_probe.py   measures the spiral tower, starting with the number the
│                     rebuild exists for: how far a walker gets up the cone
│                     alone, with the parkour taken away (`--walk-runs`). Then
│                     cells claimed twice, landings off the lattice, ladders
│                     buried in rock, the body inside the world, emergency
│                     placements, the move and feature mix, the hop
│                     distribution and its ramp, how fast the run gains
│                     altitude, how long a themed section lasts, the idle
│                     between moves, how much of the lens is clear ahead, and
│                     how many landings are the level's own ground rather than
│                     a cube hung in air. `--no-motion` needs no window at all
├── depth_probe.py    what each translucent draw is hiding, by re-rendering
│                     the frame with that one draw's depth writing off
├── frame_cost.py     per-frame cost of each scene, alternated in one process
│                     so the ratio between them survives a busy machine
├── atlas_sheet.py    every block pattern at texel scale and at block scale
└── contact_sheet.py  tile a run's `shoot` frames into one image to look at

assets/
├── build.py          rebuild committed .glb files (one subprocess each), via
│                     the bpy wheel or a standalone Blender, whichever exists
├── preview.py        render any asset to PNG with the CI rasteriser
└── src/              the Blender scripts that ARE the asset sources
    ├── common.py     zones, boxes, bake pipeline, rigging, GLB export
    ├── character.py  rigged runner: run / jump / roll
    ├── train.py      cab + middle cars
    ├── track.py      tileable 3-lane track segment
    ├── city.py       three building archetypes with window zones
    ├── props.py      barrier, gantry, fence, pillar, coin
    ├── props_mc.py   the spiral's Minecraft furniture: crops, flowers, sugar
    │                 cane, lantern posts, chains, and `mcfence` -- named that
    │                 because `props.py` already exports the runner's trackside
    │                 `fence`, and an asset name is a filename
    ├── props_flora.py grass tufts, dead bushes, cacti, lily pads, hanging
    │                 vines, bamboo, mushroom caps
    ├── props_deco.py torches, rails, end rods, chorus plants, nether fungus,
    │                 pebbles, dripstone
    └── props_climb.py the two climbable block *faces*: a ladder lattice and a
                      ragged vine sheet, both tileable vertically. Not cubes --
                      drawn as one they read as a pillar of wood

src/brainrot/
├── cli.py            run / demo / shoot / install / uninstall / ping / scenes
├── config.py         TOML + BRAINROT_* env overrides
├── rng.py            run counter, seeds, substreams, golden sequence
├── palette.py        generated theme: banded skies, accents, block families
├── ipc.py            UDP listener and sender (+ host window handle)
├── state.py          thinking -> visibility state machine
├── hookinstall.py    shim generation and settings.json merging
├── doctor.py         self-diagnosis, incl. an out-of-process render probe
├── assets/           runtime loading: zones by name, clips by name, recolor
│   └── data/         the committed .glb kit (built, never hand-made)
├── engine/
│   ├── rl.py         raylib access layer; colour-correct headless capture
│   ├── window.py     overlay / desktop / headless windows, placement
│   ├── scene.py      Scene contract, registry, per-scene texture eviction
│   ├── textures.py   PIL -> texture cache with scene/global scopes
│   ├── sky.py        gradient, sun/moon, stars, parallax clouds
│   ├── voxel.py      16x16 atlas cube models with vanilla face shading
│   ├── chunk.py      one atlas for every material, face-culled chunk meshes,
│   │                 and a volume that builds them a budget at a time
│   ├── fx.py         weather, blob shadows, glow billboards, bursts
│   ├── hud.py        shadowed text and caption chips
│   └── loop.py       frame loop, fades, scene lifecycle
├── extinstall.py     copy/compile/enable the gnome-shell extension
├── extension/        the gnome-shell half, shipped inside the wheel
│   └── brainrot@claude-brainrot.dev/
├── overlay/
│   ├── __init__.py   native(): one backend per platform, one vocabulary
│   ├── win32.py      ctypes: click-through, no-activate, owned-window attach,
│   │                 and which window is in front
│   ├── x11.py        ctypes on libX11/libXext: the same, for an XWayland
│   │                 window -- input shape, EWMH states, map without focus
│   ├── shell.py      what gnome-shell tells us: windows, monitors, pointer,
│   │                 and the logical-to-device ratio derived from it
│   └── linux.py      the seam between those two, and the only place the two
│                     coordinate spaces meet
└── scenes/
    ├── runner.py     three-lane chase-cam runner
    ├── runnerplan.py the runner's lane search and take-off planner
    ├── parkour.py    first-person infinite parkour
    ├── parkourkit.py the parkour kernel: vanilla's physics, `Move` as a list
    │                 of legs, the lattice, what a body fits in. Knows the
    │                 shape of no building; no renderer in it either
    ├── spiralplan.py the cone, its stacked themed levels, the course and its
    │                 35 features besides the exit climb -- no renderer, so a
    │                 24-run sweep needs no window
    └── spiral.py     first-person Parkour Spiral: meshing, weather, a body
                      and a lens, and nothing that knows the building's shape
```

## Adding a scene

```python
from brainrot.engine.scene import Scene, SceneContext, register

@register("mything")
class MyScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        self.rng = ctx.stream("mything-layout")   # own substream

    def update(self, dt: float) -> None: ...
    def draw(self) -> None: ...   # raylib calls; must fully cover the frame
```

Import it in `scenes/__init__.py` and add its name to `scenes` in config.
Scenes touch no windowing, hooks or config, which is what makes them testable
offscreen and cheap to write.
