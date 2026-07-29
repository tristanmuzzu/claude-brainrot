# Architecture

## Shape

```
Claude Code
    │  hook fires (UserPromptSubmit, Stop, Notification, SessionEnd)
    ▼
brainrot_hook.py            ~30ms, one UDP datagram, cannot block or raise
    │
    ▼  127.0.0.1:47821
Overlay daemon (long-lived)
    ├── ipc.EventListener      UDP receive on a background thread
    ├── state.ThinkingState    events + time  ->  visibility
    ├── engine.loop.Overlay    frame loop, fade, scene lifecycle
    ├── scenes.*               generated worlds
    └── overlay.*              win32 / desktop / headless window backends
```

## The four decisions that shaped everything

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

### 4. Generated, never sourced

There is no bundled media and no download step, so there is nothing to license,
nothing to keep in git, and nothing to curate. It also means content genuinely
cannot repeat.

## Never repeating, and replayable anyway

Those two goals conflict unless you separate *which run is this* from *how is it
generated*.

**Uniqueness** comes from a monotonic counter persisted to disk. Two runs cannot
share a seed because two runs cannot share a counter value — no randomness is
involved, so there is no collision to reason about.

**Independence** comes from substreams. Each generator draws from
`seed.stream("palette")`, `seed.stream("runner-layout")` and so on, derived by
hashing the root seed with a label. Changing how obstacles generate does not
shift the palette, which is what makes generated content tunable at all.

**Replay** is then free: `--seed N` reconstructs run N exactly.

Hashing is BLAKE2b rather than Python's `hash()`, which is salted per process
and would silently break replay across daemon restarts.

One more detail: hues come from the golden-ratio sequence indexed by run number,
not from the RNG. Uniform random hues cluster, so consecutive runs would
occasionally come out near-identical and read as a repeat. The low-discrepancy
sequence guarantees they never do.

`GENERATION_EPOCH` in `rng.py` re-rolls every generator without disturbing the
counter — bump it when generation logic changes enough that old seeds would look
stale.

## The rendering pipeline

Everything visible is synthesised. There are no image files in this repository
and nothing is fetched at runtime, so surface detail has to come from somewhere
else — and the geometry pygame can draw is limited to flat-filled polygons.

**Baked at scene construction** (`noise.py`, `texture.py`, `sky.py`), where a
few milliseconds once is free:

- value noise and fbm, used for cloud layers, facade grime and stone veining;
- the sky: a three-anchor gradient with a warm horizon band, a sun or moon disc
  with an exponential glow, a starfield whose density thins toward the horizon,
  and two wrapping cloud bands that scroll at different speeds for parallax;
- lit sphere sprites with diffuse, Blinn-Phong specular and rim terms — this is
  what makes a marble a ball rather than a circle;
- building facades with real window grids, pre-tinted at seven fog depths so
  distance fogging is a plain blit rather than a per-frame alpha composite.

**Per frame**, using only pygame's C-side blend operations:

- *bloom*, blurred with a downscale/upscale ladder — `smoothscale` is bilinear
  in C, so shrinking and regrowing a surface approximates a wide blur for
  almost nothing;
- *grade*, a split-tone: multiply toward warm (which affects highlights
  proportionally more than shadows) then a small additive cool lift;
- *chromatic aberration*, reconstructing the frame from three channel-shifted
  copies, masked to the edges by a radial ramp;
- *vignette*, a cached radial multiply.

The deliberate boundary: numpy is used at construction and **never** per frame.
An `array3d` round trip costs about 3 ms on this surface size; the blend-op
equivalents cost about 0.05 ms combined.

### Bloom without HDR

Real engines bloom in HDR, where the sky sits near 1.0 and a lamp sits at 10.0,
so a fixed threshold separates them. In 8-bit sRGB there is no such headroom: a
bright daytime sky is numerically as bright as a light source. A fixed
threshold therefore bloomed the *entire sky* and smeared its colour across
every frame — which is exactly what happened, and it looked like the whole
scene had been dipped in the sky's hue.

`postfx.auto_threshold` derives the cut from the luminance of the sky the run
actually generated, so the backdrop stays out of the bloom while windows,
coins, sparks and the sun still catch it. The palette also caps peak sky
brightness below 1.0, deliberately leaving headroom for things that emit.

### Texture mapping, which pygame does not have

pygame fills polygons with a flat colour and nothing else. An earlier version
approximated texture by scattering small "texel" polygons over each face; that
gave surfaces *detail* but never actual texture, and you could not put a legible
16x16 cobblestone pattern on a cube and have it read as cobblestone.

`warp.py` does the real thing: each face is treated as a parallelogram, the
pixels inside it are inverse-mapped back into texture space with numpy, and the
texture is sampled nearest-neighbour so pixel art stays hard-edged.

Doing that per face per frame would be far too slow -- numpy's per-call overhead
dominates on arrays this small. What makes it affordable is that a face's
*shape* depends only on the camera angle and the distance, not on where the
block is, so at any moment nearly every visible face of a given orientation is
the same parallelogram at one of a handful of sizes. Quantising the two edge
vectors into buckets turns that into a cache key, and the warp then runs a few
dozen times a frame instead of a few hundred; everything else is a plain blit.
Three details that turned out to matter:

* **Evict a fraction, not everything.** Clearing the cache when it filled
  dropped the hit rate to about 30% -- each eviction threw away the entire
  working set mid-frame. Dropping the oldest quarter took it to ~72%.
* **Coarser buckets for longer edges.** Whole-pixel buckets on a large face
  mint an entry for almost every depth the orbiting camera passes through.
* **Grow each edge before quantising.** Rounding the origin and the edges
  independently leaves sub-pixel gaps, and a one-pixel seam showing sky between
  every pair of blocks is far more visible than a one-pixel overlap -- which,
  drawn in painter's order, is invisible. The size guard has to run *before*
  that inflation, or genuinely sub-pixel faces get floored at three pixels and
  distant geometry renders several times too large.

The mapping is affine, not perspective-correct: a cube face in perspective is
really a trapezoid. Across a block a few dozen pixels wide the difference is
under a pixel. Long faces -- a train carriage running away from the camera --
are subdivided by the caller into ~2-unit segments so each stays small enough
for the approximation to hold.

### Models

`model.py` is the only thing that knows how to turn a box into pixels:
transform eight corners, drop the faces whose screen-space winding points away
from the camera, draw the rest as textured quads. Back-face removal by winding
rather than by reasoning about camera position means it works unchanged for the
runner's fixed forward camera and the tower's orbiting one.

Figures follow the standard voxel-game proportions, in texture pixels where one
block is 16: 8x8x8 head, 8x12x4 torso, 4x12x4 limbs, exactly two blocks tall.
Those numbers matter more than they look -- a slightly-too-small head stops the
figure reading as the thing it is imitating however good the textures are.
Limbs rotate about a pivot at the shoulder or hip, not their own centre, which
is the difference between a joint and a box sliding back and forth.

### Terrain palettes are fixed

Block colours do **not** follow the run palette. Grass is grass-coloured and
stone is stone-coloured in every run; only the sky, the lighting, and the
character's shirt pick up the generated hue. Terrain that changes colour every
run reads as a bug rather than as variety -- and the same applies to the
characters, whose hair was briefly derived from `palette.ink` and consequently
turned white on every dark palette.

Surface detail is still capped to a **budget of the nearest blocks**, and the
`quality` setting scales it.

## Projection

One projection module serves the two 3D scenes: a pinhole camera looking down
+Z, `scale = focal / depth`. The entire illusion of motion is that world
features at *constant* Z spacing project to *shrinking* screen spacing.

The projection deliberately has no yaw. `tower` needs an orbiting camera, so it
rotates the world about the tower axis in `_to_view` before handing a plain
forward-looking camera the result — keeping the rotation local to the one scene
that wants it leaves `projection.py` small enough to reason about.

`marbles` is honestly 2D and skips the projection entirely; a perspective camera
would buy nothing but a smaller playfield in a strip a few hundred pixels wide.

Depth ordering everywhere is painter's algorithm. At a few hundred blocks it is
cheaper than maintaining any spatial structure.

## Solvability by construction

Both game scenes could generate layouts that cannot be completed. Neither is
allowed to, and neither checks afterwards — rejection sampling would stall for
an unbounded time inside a render loop.

- **runner**: each row is assigned a guaranteed-clear lane *before* obstacles
  are placed, and that lane may only move by one between consecutive rows.
  Obstacles are painted into the lanes the corridor does not occupy. A
  reachable path therefore exists by construction. Coins are spawned along the
  corridor, which makes the route read as deliberate.
- **tower**: the descent route is generated first, with per-step drop and reach
  clamped to what a hop covers. The tower is then built around it.

Both invariants are asserted directly in `tests/test_generation.py` across many
runs, rather than being left as comments.

## Quality tiers

Rendering has a real cost and the overlay runs while you are building, so the
trade is exposed rather than chosen silently. `quality` reaches scenes through
`SceneContext` and scales the voxel detail budget, bloom blur passes, and
whether chromatic aberration runs at all. Generated geometry, lighting and
palette are identical across all three tiers — only surface detail changes.

## Cost while idle

The daemon spends almost all of its life hidden. In that state it holds no
scene, renders nothing, and sleeps 80ms per iteration. Scenes are constructed on
the transition to visible and destroyed on the transition to hidden — which is
also what makes every appearance freshly generated.

While visible it renders at 30fps and sleeps the remainder of each frame rather
than spinning.

## Layout

```
src/brainrot/
├── cli.py            run / demo / shoot / install / uninstall / ping / scenes
├── config.py         TOML + BRAINROT_* env overrides
├── rng.py            run counter, seeds, substreams, golden sequence
├── palette.py        generated theme: colour, time of day, weather
├── ipc.py            UDP listener and sender
├── state.py          thinking -> visibility state machine
├── hookinstall.py    shim generation and settings.json merging
├── doctor.py         self-diagnosis, incl. the untestable win32 path
├── engine/
│   ├── projection.py perspective maths
│   ├── scene.py      Scene contract and registry
│   ├── noise.py      value noise / fbm, for generated textures
│   ├── pixelart.py   16x16 block textures and character skins
│   ├── warp.py       cached affine textured-quad rasteriser
│   ├── model.py      textured boxes and the box-humanoid rig
│   ├── texture.py    spheres, glows, facades
│   ├── sky.py        gradient, sun/moon, stars, parallax clouds
│   ├── postfx.py     bloom, grade, aberration, vignette
│   ├── draw.py       text, particles, cached gradients
│   └── loop.py       frame loop, fades, scene lifecycle
├── overlay/
│   ├── base.py       backend interface, monitor placement
│   ├── win32.py      layered, click-through, always-on-top, no focus
│   ├── desktop.py    plain window for development
│   └── headless.py   offscreen, for tests and `shoot`
└── scenes/
    ├── runner.py     endless runner + autopilot
    ├── tower.py      voxel parkour descent
    └── marbles.py    marble race with collision physics
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
    def draw(self, surface) -> None: ...          # must fully cover the surface
```

Import it in `scenes/__init__.py` and add its name to `scenes` in config.
Scenes touch no windowing, hooks or config, which is what makes them testable
offscreen and cheap to write.
