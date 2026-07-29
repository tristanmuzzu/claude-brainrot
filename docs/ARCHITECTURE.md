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

## Rendering

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
├── engine/
│   ├── projection.py perspective maths
│   ├── scene.py      Scene contract and registry
│   ├── draw.py       gradients, text, particles, vignette
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
