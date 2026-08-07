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

### 5. Attached to Claude Code, not to the screen

An overlay that floats above *everything* is a universal window; this one
should belong to Claude Code. The shim reads the foreground window at event
time — the window you submitted a prompt from *is* the Claude Code host — and
sends its handle with the datagram. The daemon then makes the overlay an
**owned window** of that host (`GWLP_HWNDPARENT`): Windows keeps an owned
window exactly one z-level above its owner, so the strip rides above the
terminal, and any other window you focus covers both. `attach = "topmost"`
restores the old behaviour. All of it is ctypes; there is no pywin32
dependency.

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
east/west 0.6, bottom 0.5), per-texel noise with a darkened 1-px rim that
separates adjacent blocks the way baked AO would, and a **texel pattern** —
planks, brick courses, cobble, checker, ore fleck, a glowstone lattice,
leaves. The pattern is what makes a material legible at a glance without the
eye having to resolve its edges, and it is the difference between a course of
coloured cubes and a course of *things*.

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
  from the plugin that produces most of that footage — weighted gap (1-4
  blocks) and rise (-2..+1) tables, Gaussian lateral drift steered back toward
  a spine, refusal to overlap recent course, blocks despawning two behind —
  and then works in **set-pieces** on top of it, because a uniform stream of
  cubes is only watchable for about ten seconds. `SEGMENT_TABLE` is the
  vocabulary: staircase, plank causeway, spiral round a brick tower, gate you
  run *through*, long fall, lantern walk, chasm. A segment never follows
  itself, and which ones are eligible depends on which way the course has
  drifted within its altitude band — so verticality comes from steering
  generation rather than from vetoing it.

  Two consequences worth knowing before changing any of it:

  - **The course knows its own path.** Where the player will stand on each
    block is drawn when the block is generated, so the exact ballistic arc of
    every future hop is computable at generation time. Orbs are hung *on* that
    arc at chest height, which makes "every orb laid down is collected" a
    property of generation rather than a hope about the simulation.
  - **Flight time comes from the drop, not only the distance.** A hop covers
    its gap at running pace; a fall takes as long as a fall takes.

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
- **parkour**: no hop is laid down that the flight solver cannot fly — the
  test states the invariant against the solver rather than against the tables,
  because the set-pieces widened what a hop may be. Altitude is clamped to a
  band that segment choice keeps it away from; candidate headings fan out
  until one clears the recent course; a hop shorter than `MIN_HOP` is pushed
  out until there is a real jump to make. Every orb the generator hangs is
  collected, which is asserted over two minutes of running and again over a
  minute of being steered by hand.

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
├── overlay/
│   └── win32.py      ctypes: click-through, no-activate, owned-window attach
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
