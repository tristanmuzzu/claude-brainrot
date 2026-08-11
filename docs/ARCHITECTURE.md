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
  Blender script committed to `assets/src/`, run under headless `bpy`. Nothing
  is downloaded and nothing is hand-exported from an opaque tool; delete
  `src/brainrot/assets/data` and `python assets/build.py` recreates it
  byte-for-byte-equivalent.
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
  pattern (segments spawned ahead, destroyed behind, content generated per
  6 m row from a per-row substream).
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

## Solvability by construction

Both scenes could generate layouts that fail. Neither is allowed to, and
neither checks afterwards — rejection sampling would stall inside a render
loop.

- **runner**: each row is assigned a guaranteed-clear lane *before* obstacles
  are placed, and that lane may move by at most one between consecutive rows.
  Parked trains only occupy lanes the corridor does not. Oncoming trains sweep
  across rows, which a static corridor cannot answer — so at most **one**
  oncoming train exists at a time, and the autopilot dodges it live (lane
  changes work mid-air, exactly like the game it imitates; with two oncoming
  trains a dodge can be pinned with no legal answer, which is why the limit is
  structural rather than probabilistic).
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

All of these are asserted directly in `tests/test_generation.py` across many
runs, rather than being left as comments.

## Cost while idle

The daemon spends almost all of its life hidden. In that state it holds no
scene, renders nothing, and sleeps 80ms per iteration (draining the window's
event queue so the OS does not flag it unresponsive). Scenes are constructed
on the transition to visible and destroyed on the transition to hidden — which
is also what makes every appearance freshly generated.

## Layout

```
tools/                offline, never imported by the daemon
├── parkour_probe.py  measures the parkour course and its motion: block
│                     interpenetration, grid alignment, emergency hops, the
│                     hop distribution and its difficulty ramp, and whether
│                     the body is ever inside a solid block
├── depth_probe.py    what each translucent draw is hiding, by re-rendering
│                     the frame with that one draw's depth writing off
├── frame_cost.py     per-frame cost of each scene, alternated in one process
│                     so the ratio between them survives a busy machine
├── atlas_sheet.py    every block pattern at texel scale and at block scale
└── contact_sheet.py  tile a run's `shoot` frames into one image to look at

assets/
├── build.py          rebuild committed .glb files (one bpy subprocess each)
├── preview.py        render any asset to PNG with the CI rasteriser
└── src/              the Blender scripts that ARE the asset sources
    ├── common.py     zones, boxes, bake pipeline, rigging, GLB export
    ├── character.py  rigged runner: run / jump / roll
    ├── train.py      cab + middle cars
    ├── track.py      tileable 3-lane track segment
    ├── city.py       three building archetypes with window zones
    └── props.py      barrier, gantry, fence, pillar, coin

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
    └── parkour.py    first-person infinite parkour
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
