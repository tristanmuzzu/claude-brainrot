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
| `runner` | Three-lane endless runner. Generated track, generated obstacles, played by an autopilot that mostly does not crash. |
| `tower` | Voxel parkour spire. A figure hops its way down a route that is generated before the tower is built around it. |
| `marbles` | Seven marbles, a generated zigzag course, real collision physics and no predetermined winner. |

Every run also generates its own palette, time of day and weather, so the same
scene twice in a row still does not look the same.

## Install

```bash
git clone https://github.com/tristanmuzzu/claude-brainrot
cd claude-brainrot
pip install -e .

# Windows, for the click-through overlay:
pip install pywin32
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
  loop parks on a long sleep.

Measured on the daemon itself, 360×640 at 30fps:

| | CPU |
|---|---|
| hidden | 0.08% of one core |
| rendering | 3.9% of one core |

Your hardware will differ, but the shape is the point: while it is not on
screen it is doing nothing, so it is not competing with your build.

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

The suite covers the show/hide state machine, the seeding guarantees, the
projection maths, and the generation invariants — including a test that drives
the runner's autopilot for two simulated minutes and asserts it survives, and
one that checks no generated track can ever wall off all three lanes.

Docs: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the pieces fit and
why, [`docs/HOOKS.md`](docs/HOOKS.md) for the hook layer specifically.

## License

MIT. All visual content is generated at runtime; no third-party assets are
included or fetched.
