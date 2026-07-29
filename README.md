# claude-brainrot

*Subway Surfers while CC is thinking.*

A narrow strip of procedurally generated gameplay that appears on the left edge
of your screen while Claude Code is thinking, and gets out of the way when it
stops.

Nothing is ever downloaded, uploaded or bundled. Every frame is generated at
runtime from a seed that has never been used before and never will be again.

```
  you hit enter
        │
        ▼
  UserPromptSubmit hook ──UDP──► daemon ──► new seed ──► new world ──► fade in
        ...
  Stop hook ────────────────────► daemon ──────────────────────────► fade out
```

## What plays

Three scenes, chosen per run from the run's seed.

| Scene | What it is |
|---|---|
| `runner` | Three-lane endless runner. Textured train carriages with window bands and headlamps, hazard-striped barriers, a generated skyline, coins and sparks. Played by an autopilot that mostly does not crash. |
| `tower` | Voxel parkour spire on a strict integer grid: grass, dirt, cobblestone, planks, logs and leaves, all drawn with real 16x16 textures. A figure hops down a route generated before the tower is built around it. |
| `marbles` | Seven lit spheres with specular highlights and motion trails, a generated zigzag course, real collision physics and no predetermined winner. |

Every run also generates its own palette, time of day, weather and sky — with a
sun or moon that sits somewhere specific, layered parallax clouds, and a
starfield that thins out toward the horizon. The same scene twice in a row does
not look the same.

Blocks and characters are real textured 3D boxes — 16x16 pixel-art faces,
sampled nearest-neighbour so they stay crisp, mapped onto projected quads with a
cached affine warp (pygame has no texture mapping of its own). The figures use
the standard voxel proportions: 8x8x8 head, 8x12x4 torso, 4x12x4 limbs, exactly
two blocks tall, with limbs swinging from real shoulder and hip pivots.

Everything is drawn through a post-processing chain: bloom, a split-tone colour
grade, chromatic aberration at the frame edges, and a radial vignette.

## Install

```bash
git clone https://github.com/tristanmuzzu/claude-brainrot
cd claude-brainrot
pip install -e .

# Windows, for the click-through overlay:
pip install pywin32
```

Check the install at any point with:

```bash
brainrot doctor
```

Register the hooks, then start the daemon:

```bash
brainrot install     # writes hooks into ~/.claude/settings.json
brainrot run         # long-lived; leave it running
```

That is the whole setup. Open Claude Code and give it something slow to do.

To remove it: `brainrot uninstall`.

## Try it without Claude Code

```bash
brainrot demo --scene runner        # a normal window, always on
brainrot demo --scene tower --seed 4712   # replay one specific run
brainrot shoot --scene marbles --frames 300 --out shots/   # frames to PNG
brainrot scenes                     # what is registered, and your run count
brainrot doctor                     # diagnose install, backend and hooks
```

`brainrot ping UserPromptSubmit` and `brainrot ping Stop` drive the real daemon
by hand, which is the fastest way to check your show/hide behaviour without
waiting on a real turn.

## Why it does not annoy you

The gap between "Claude is busy" and "put something on screen" is where all the
work is:

- **Short turns never show anything.** Nothing appears until Claude has been
  busy for 1.5s, so quick answers do not make the strip strobe.
- **Nothing flashes.** Once it has appeared it stays for at least 3s, even if
  Claude finishes immediately afterwards.
- **It never takes focus or eats clicks.** The window is click-through and
  cannot be activated, so it does not interrupt typing and you can click
  straight through it.
- **It hides when Claude needs you.** A permission prompt means your attention
  belongs on the terminal.
- **It costs nothing while hidden.** No scene is held, nothing renders, and the
  loop parks on a long sleep — **0.25% of one core**.

## Performance and the quality knob

Rendering is not free, and this thing runs while you are building. Measured at
360×640, 30fps, on a (slow) cloud container — a desktop CPU will be well under
these:

| scene | high | balanced | low |
|---|---|---|---|
| `runner` | 8.2 ms | 4.9 ms | 4.8 ms |
| `tower` | 19.5 ms | 14.9 ms | 8.4 ms |
| `marbles` | 4.4 ms | 2.1 ms | 1.9 ms |

At 30fps a 10 ms frame is roughly 30% of one core. If that is more than you
want to spend, drop the quality or the frame rate:

```toml
[content]
quality = "balanced"   # high (default) | balanced | low

[window]
fps = 24
```

`balanced` halves the voxel texture budget and drops chromatic aberration;
`low` draws blocks as flat-shaded faces instead of textured ones. All three keep
the generated geometry, models and lighting identical — only surface detail
changes.

`brainrot doctor` reports what your machine will actually do, including whether
the click-through overlay is available.

## Configuration

Optional `config.toml`, next to the run-counter state:

- Linux/macOS: `~/.local/state/claude-brainrot/config.toml`
- Windows: `%APPDATA%\claude-brainrot\config.toml`

```toml
[window]
width = 360
height = 640
margin_x = 12      # gap from the left screen edge
anchor_y = 0.5     # 0 = top, 1 = bottom
monitor = 0
opacity = 0.88
fps = 30

[behaviour]
grace_seconds = 1.5
min_visible_seconds = 3.0
hide_on_notification = true

[content]
scenes = ["runner", "tower", "marbles"]
quality = "high"
```

Any field can also be set with an environment variable:
`BRAINROT_WIDTH`, `BRAINROT_GRACE_SECONDS`, `BRAINROT_SCENES`, and so on.

## Platform support

| | Overlay | Click-through | Notes |
|---|---|---|---|
| Windows | yes | yes | needs `pywin32`; the intended target |
| Linux / macOS | yes | no | ordinary window, fine for development |
| Headless / CI | offscreen | n/a | what the test suite runs against |

The click-through behaviour is Windows-only because SDL cannot express it
portably. Everything else — the engine, all three scenes, the state machine —
is platform-independent and fully tested offscreen.

## Development

```bash
pip install -e ".[dev]"
pytest
```

206 tests covering the show/hide state machine, the seeding guarantees, the
projection maths, hook install/uninstall, the real shim end to end, a full
daemon driven over UDP, and the generation invariants — including a test that
drives the runner's autopilot for two simulated minutes and asserts it
survives, and one that sweeps every point of 300 generated rows to prove no
track can ever wall off all three lanes.

Docs: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the pieces fit and
why, [`docs/HOOKS.md`](docs/HOOKS.md) for the hook layer specifically.

## License

MIT. All visual content is generated at runtime; no third-party assets are
included or fetched.
