# claude-brainrot

*Subway Surfers while CC is thinking.*

[![PyPI](https://img.shields.io/pypi/v/claude-brainrot)](https://pypi.org/project/claude-brainrot/)
[![tests](https://github.com/tristanmuzzu/claude-brainrot/actions/workflows/ci.yml/badge.svg)](https://github.com/tristanmuzzu/claude-brainrot/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20Windows-informational)](#platform-support)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A narrow strip of generated gameplay that appears beside your Claude Code
window while it is thinking, and gets out of the way when it stops.

<p align="center">
  <img src="docs/media/tower.gif" width="240" alt="the hand-built tower" />
  <img src="docs/media/runner.gif" width="240" alt="the runner scene" />
  <img src="docs/media/parkour.gif" width="240" alt="the parkour scene" />
</p>

No footage, no downloads. Every world is generated at runtime from a seed that
has never been used before and never will be again — rendered in real 3D with
models built by the Blender scripts in this repository. Those three clips are
`brainrot shoot` output at 15 fps, not a screen recording of something else.

```
  you hit enter
        │
        ▼
  UserPromptSubmit hook ──UDP──► daemon ──► new seed ──► new world ──► fade in
        ...
  Stop hook ────────────────────► daemon ──────────────────────────► fade out
```

## The tower

The default scene, and where most of the work has gone. It is the **Parkour
Spiral** format — a course winding up the outside of a tower that keeps going
out of the top of the frame — against a course of **thirty-three hand-designed
levels**, 385 authored landings, rather than a generated one.

<p align="center">
  <img src="docs/media/levels.png" width="640" alt="eight of the thirty-three levels" />
</p>

Eight of the thirty-three. A level is a themed terrace with a landmark on it —
a windmill, a watchtower, a bell frame, a crane, a great mushroom cap — and
three things about it are load-bearing:

- **The course goes *through* the landmark, not past it.** Placing a structure
  and measuring how often it was placed says nothing: the first version stood
  one up on 97% of levels and a viewer watching five minutes of live strip
  remembered exactly one. Framing is the number that matters — how long a
  structure holds 25° of your view, unoccluded, and twelve of the fourteen
  blueprints now carry a passage the course is steered through.
- **The course flies.** After the first step up off the terrace, every landing
  stands at least two blocks over the ground. Miss a jump and you land on the
  terrace, which is a dead end — the course left it at landing one — so you
  walk back to the start of the level rather than rejoining halfway. It used to
  be that 88% of missed jumps walked straight back into the middle of the
  course; it is now **1 in 8,484**.
- **Every jump is checked against the physics before it is placed.** Gravity,
  jump impulse and sprint speed are Minecraft's own numbers converted from
  ticks, so the furthest a hop can reach is computed rather than chosen. A
  designed landing that no jump can reach is refused at build time, not
  discovered mid-run.

Each level is also its own *place*, and the lever for that turned out to be the
floor rather than the skyline: a median of **six** materials underfoot where a
generated level uses two or three. (The real Parkour Spiral map measures
fourteen, so there is room left.) Ten to thirteen seconds of strip each, its
own signature move, its own way out.

## What else plays

Four scenes, chosen per run from the run's seed — `runner`, `parkour` and
`tower` by default, with `spiral` one line of config away.

| Scene | What it is |
|---|---|
| `runner` | The classic: three locked lanes, a chase camera, subway cars with per-run liveries, hazard barriers, gantries, coin arcs, and a city canyon whose windows light up at night. The runner **rides train roofs** — the ramp, the train, the corridor onto it and the clear lane to bail into are laid down as one decision, and the leap is solved at generation time at both ends of the speed range, so a ramp whose train is out of reach is never built. An autopilot follows a corridor guaranteed reachable *by construction* and live-dodges oncoming trains. |
| `parkour` | First-person infinite parkour, the way the actual background reels do it: one flawless sprint-jump per beat, high over an ocean of wooded islands, reef shallows and drifting cloud shelves. The course arrives in set-pieces — a staircase, a plank causeway, a gate you run *through*, a long fall onto a lantern-lit platform — each built from one family of materials. Orbs hang on the exact arc of the jump that reaches them, so every one laid down is collected. Something is always in your hand: a block, a sword, a pickaxe, a torch. |
| `tower` | The thirty-three designed levels above. |
| `spiral` | The same tower format with the course *generated* instead of authored: one solid inverted cone, fluted with vertical ribs, fifteen themes out of a shuffled bag several to a revolution with hard seams between them, and the parkour built into each theme's own ground — lily pads across the desert's pond, a mine's ladders, an ice slide, a nether lava channel, a soul-sand bubble column. Still registered and still tested; `tower` simply reads better. |

Every run also generates its own palette, time of day, weather and sky — a sun
or crescent moon with a real glow, parallax clouds, a starfield that thins
toward the horizon, rain or snow. The same scene twice in a row does not look
the same.

<p align="center">
  <img src="docs/media/variety.png" width="640" alt="sixteen consecutive runs" />
</p>

Sixteen consecutive runs, one frame each, nothing hand-picked — whatever the
seed chose.

## Install

Python 3.11 or newer. There is nothing to compile and no GPU requirement —
`pip` pulls two wheels (raylib ~2 MB, Pillow) and that is the whole dependency
list. It is a long-running background tool rather than a library, so
[pipx](https://pipx.pypa.io/) or [uv](https://docs.astral.sh/uv/) is the
tidiest way in:

```bash
pipx install claude-brainrot     # or: uv tool install claude-brainrot
```

<details open>
<summary><b>Linux (GNOME/Wayland — Ubuntu, Fedora, …)</b></summary>

```bash
pipx install claude-brainrot     # or: pip install claude-brainrot

brainrot install        # hooks, plus the gnome-shell extension
brainrot extension load # load it into the running shell (or just log out and in)
brainrot run            # long-lived; leave it running
```

Verified on Ubuntu 26.04 / GNOME Shell 50.1 (Wayland, 200% scaling) —
`brainrot doctor` reports 14 checks passing.
</details>

<details open>
<summary><b>Windows 10/11</b></summary>

```powershell
pipx install claude-brainrot     # or: pip install claude-brainrot

brainrot install        # writes hooks into ~/.claude/settings.json
brainrot run            # long-lived; leave it running
```

That is the whole setup. No pywin32 — the window work is ctypes on `user32`.

**Do not use a Microsoft Store Python.** The Store redirects `%APPDATA%` into
the package's own `LocalCache` for reads as well as writes, so the config file
you can see in Explorer is one the daemon cannot open at all, and every setting
silently reverts to its default. Install from
[python.org](https://www.python.org/downloads/) instead; `brainrot doctor`
prints the config path it is genuinely reading.
</details>

<details>
<summary><b>From source</b>, to change something</summary>

```bash
git clone https://github.com/tristanmuzzu/claude-brainrot
cd claude-brainrot
python3 -m venv .venv && source .venv/bin/activate   # Windows: py -m venv .venv
pip install -e ".[dev]"
```
</details>

The hooks are written with the **absolute path** of the interpreter you
installed into, so the daemon and the hooks work whether or not any venv is
activated. Move or remove that interpreter and you must re-run `brainrot
install`.

<details>
<summary>Why Linux needs that extra <code>extension</code> step</summary>

`brainrot install` copies a small gnome-shell extension into
`~/.local/share/gnome-shell/extensions` and switches it on. gnome-shell only
looks for new extensions when it *starts*, though, and on Wayland that means
the session — so it needs one of:

```bash
brainrot extension load    # loads it into the running shell, no logout
```

which walks you through a one-time fifteen-second toggle in Looking Glass
(`Alt+F2` → `lg`) and puts the setting back afterwards; **or** simply log out
and back in, which does the same job with no steps to follow.

The extension exists because a Wayland client is not allowed to know which
window is in front, where any window is, or where the pointer is — and the
strip needs all three, to appear only while you are looking at Claude Code, to
stand beside that window, and to be draggable. It sends window geometry, window
classes, process ids and the pointer to the daemon on loopback. No titles, no
contents, no keystrokes.

**It works without the extension too** (`brainrot install --no-extension`, or
before you have loaded it): the strip docks to the work area, stays up for the
whole turn, and cannot be dragged. It also deliberately stays *out* of the
always-above band in that state — a window that floats over everything and
cannot hide itself is a window that sits on top of your browser, so instead it
comes up over the Claude Code window you were just typing into and gets buried
the moment you click anything else.

`brainrot run` says which of the two modes it is in, and says so again if that
changes underneath it. `brainrot doctor` and `brainrot extension status` both
report on it too.

Wayland-only distributions are the reason this is not simpler: GNOME 49 dropped
the X11 session, so Ubuntu 25.10 and later have no X11 session to fall back to.
The strip is therefore an *XWayland* window — X11 is still a first-class
protocol on that desktop, and it is the one that lets a window place itself,
stay above, shape its input region and be shown without taking focus.
</details>

Open Claude Code and give it something slow to do. Check any machine with
`brainrot doctor`. Remove with `brainrot uninstall`.

## It belongs to Claude Code, not to your screen

The overlay is not on screen just because Claude is busy. The hook tells the
daemon which window your prompt came from — that window *is* your Claude Code
— and from then on:

- **It only appears while you are looking at that window.** Switch to your
  browser and it fades out; switch back and it returns. Nothing known about
  where Claude Code is means it stays hidden, rather than floating over
  everything. (`follow_focus = false` for the always-on behaviour, which is
  what demos and screen recordings want.)
- **It stands beside that window, not on your screen edge.** A screen edge is
  wherever the app keeps its sidebar; the strip goes into the empty gutter on
  the `dock` side of the Claude Code window instead, and *outside* that window
  entirely when the desktop has room. It follows the window if you move it.
- **It rides one z-level above it.** On Windows the strip is an *owned* window
  of the Claude Code window, so raising your terminal raises the strip with it
  and anything else you focus covers both. mutter has no notion of an X11
  window owned by a Wayland one, so on Linux the strip is in the always-above
  band and the focus rule above — not the z-order — is what keeps it off your
  other applications. `attach = "topmost"` restores float-over-all on Windows.
- **You can move it.** Hold `ctrl+alt` and drag it wherever you like; where
  you drop it is remembered and still follows the window. Double-click while
  holding the chord to go back to automatic placement. Clicks are caught only
  while that chord is held over the strip — otherwise the mouse falls
  straight through, and focus is never taken either way. (Linux: needs the
  extension, which is where the pointer position comes from.)
- **It is the size you asked for.** On a HiDPI display the strip is drawn at
  the configured size and scaled to the display, so `width = 360` means 360
  points rather than 360 device pixels — and the scenes keep their own pixel
  geometry rather than rendering a HUD at half size.

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

## Try it without Claude Code

```bash
brainrot demo --scene tower                # a normal window, always on
brainrot demo --scene runner --seed 4712   # replay one specific run
brainrot shoot --scene tower --frames 300 --out shots/   # frames to PNG
brainrot scenes                            # what is registered, and your run count
```

`runner` and `parkour` are also **playable** — arrows or WASD, up or space to
jump, down to duck, eight idle seconds to hand control back. `brainrot demo`
needs no chord for it. The overlay never reads a key until you deliberately
hand it focus; there is no global key hook, on purpose.

`brainrot ping UserPromptSubmit` and `brainrot ping Stop` drive the real daemon
by hand, which is the fastest way to check show/hide behaviour without waiting
on a real turn.

## Configuration

Optional `config.toml`, next to the run-counter state:

- Linux/macOS: `~/.local/state/claude-brainrot/config.toml`
- Windows: `%APPDATA%\claude-brainrot\config.toml`

Run `brainrot doctor` for the path it is actually reading. On a **Microsoft
Store** Python that is not the path above: the Store redirects `%APPDATA%`
into the package's `LocalCache`, and the copy you can see in Explorer is one
the daemon cannot open at all. The `config` check prints the real one.

```toml
[window]
width = 360
height = 640
dock = "right"     # which side of the Claude Code window to stand on
margin_x = 12      # gap from that side
margin_y = 20      # gap from the top and bottom of that window
anchor_y = 0.0     # 0 = top of it, 1 = bottom of it
monitor = 0        # only used when no host window is known
opacity = 0.88
fps = 60
attach = "host"    # "host" = one level above Claude Code, "topmost" = above all

[behaviour]
grace_seconds = 1.5
min_visible_seconds = 3.0
hide_on_notification = true
max_thinking_seconds = 900   # give up on a session that stops saying anything
follow_focus = true      # on screen only while you are looking at Claude Code
drag_chord = "ctrl+alt"  # hold to drag the strip; "" to disable

[content]
scenes = ["runner", "parkour", "tower"]   # "spiral" is the fourth
quality = "high"
```

Any field can also be set with an environment variable:
`BRAINROT_WIDTH`, `BRAINROT_GRACE_SECONDS`, `BRAINROT_SCENES`, and so on.

## Platform support

| | Overlay | Click-through | Never focused | Follows Claude Code | Notes |
|---|---|---|---|---|---|
| Windows 10/11 | yes | yes | yes | yes, as an owned window | ctypes on `user32`, no extra deps |
| Linux, GNOME/Wayland | yes | yes | yes | yes, via the shell extension | XWayland window; extension needs one log-out to load |
| Linux, GNOME/Wayland, no extension | yes | yes | yes | docks to the work area, stays up for the turn | still useful; `brainrot doctor` says so |
| Linux, other desktops | yes | yes | yes | work-area docking only | the X11 half is generic EWMH; only the compositor half is GNOME-specific |
| macOS | plain window | no | no | no | scenes, hooks and `shoot` all work; no overlay backend |
| Headless / CI | offscreen | n/a | n/a | n/a | software rasteriser, no display needed |

Verified on Windows 11 and on Ubuntu 26.04 / GNOME Shell 50.1 (Wayland, 200%
scaling) — both by measurement on the machine rather than by inspection.

## How it looks like that

The renderer is [raylib](https://www.raylib.com/) (a ~2 MB wheel); the models
are glTF files **built by scripts committed to this repo** (`assets/src/*.py`),
executed under headless Blender. Each asset bakes its lighting — sun, sky
bounce, ambient occlusion — into a grayscale texture, and keeps its colours in
flat named material zones. At runtime every pixel is just

    baked light map  ×  zone colour  ×  distance fog

which is why the daemon can recolour a hoodie or a train livery per seed
without any lighting maths, and why CI screenshots (rendered on a software
rasteriser) match what your GPU shows.

The character is skin-rigged with run, jump and roll clips authored in the same
scripts. The parkour blocks use vanilla Minecraft's actual face-shading
constants (top 1.0, sides 0.8/0.6, bottom 0.5) baked into 16×16 pixel-art
atlases — over a light level, not on their own, which is a distinction that
cost this project a whole set of frames half again too dark.

Rebuilding the kit after editing a script (needs `pip install bpy`, dev-only):

```bash
python assets/build.py            # everything
python assets/build.py character  # one asset
python assets/preview.py character  # render it for your eyeballs
python assets/measure.py          # always, after any rebuild
```

## Development

```bash
pip install -e ".[dev]"
pip install raylib-software --force-reinstall --no-deps  # headless machines/CI
pytest
```

641 tests covering the show/hide state machine, the seeding guarantees, hook
install/uninstall, the real shim end to end, a full daemon driven over UDP,
pixel-identical determinism per seed, the real overlay window driven against a
real X server, the compositor bridge's parsing and host resolution, and the
generation invariants — the corridor that can never strand the runner, the
single-oncoming-train rule and the live dodge, zero interpenetration over hours
of simulated running, no parkour hop the flight solver cannot fly, self-overlap
refusal, the altitude band, and every orb the parkour generator hangs being
collected.

The 34 skips are platform suites: `tests/test_overlay_win32.py` only runs where
`os.name` is `nt`, `tests/test_overlay_x11.py` only where there is a display. A
green run on one platform therefore means less than the count suggests, which
is why CI runs the whole suite on **both** — 632 passing on each — and then
renders a frame of every scene on each and keeps them as artifacts: same seed,
same software rasteriser, and the frames come back **pixel-identical** between
the two platforms.

What CI does *not* cover is the overlay window surgery itself. Both platform
suites need a real desktop — the Win32 one skips on a runner as soon as raylib
reports no native window handle, and the X11 one needs a display. Those are
verified by hand on real machines.

Beyond the suite, each scene has a **probe** that turns "it feels wrong" into
numbers, and those numbers are the acceptance criteria:

```bash
python tools/tower_probe.py --runs 16 --blocks 340    # the design, and what survived placement
python tools/reentry_probe.py --runs 6 --blocks 260   # can a missed jump rejoin the course
python tools/landmark_probe.py --runs 6 --seconds 40  # is the landmark ever actually seen
python tools/bypass_probe.py --runs 6 --blocks 240    # can a level be walked without jumping
python tools/runner_probe.py --runs 12 --seconds 120  # safety, pacing, riding
python tools/parkour_probe.py --runs 24               # interpenetration, hops, dead air
python tools/frame_cost.py                            # every scene, one process, vsync off
```

Docs: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the pieces fit and
why, [`docs/TOWER.md`](docs/TOWER.md) for the tower's design and acceptance
criteria, [`docs/RULES.md`](docs/RULES.md) for what a level must satisfy,
[`docs/HOOKS.md`](docs/HOOKS.md) for the hook layer.

## License

MIT. Every model ships as output of a script in `assets/src/` — no third-party
assets are included or fetched.
