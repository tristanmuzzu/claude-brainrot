# Handoff: bring the parkour scene up to the runner's standard

Paste the prompt at the bottom into a fresh Claude Code session in
`C:\Users\acer\claude-brainrot`. Everything above it is context for whoever
picks this up.

## Where things stand

Branch `claude/project-visuals-animations-qzbkiq`, 298 tests green, overlay
installed and running on Tristan's machine (`brainrot doctor` is 10/10).

The **runner** has had a deep pass: measured hitboxes, a planner that solves
lane changes and take-offs in time and verifies its own plan before committing,
generation invariants that keep the track solvable, and evidence of zero
interpenetration across 60 seeds x 180 s of simulated running. It is also
playable by hand (arrows/WASD, Ctrl+Alt+B to take the keyboard from the
overlay).

The **parkour** scene has had a much lighter pass: a first-person held block
and crosshair, landing dust, and the capture/perf fixes it shares with
everything else. Tristan's words: *"I'm hoping you put as much work into the
Minecraft version as you did the Subway Surfers one, because that one also
needed quite a bit of work."* That is the job.

## What parkour is now

`src/brainrot/scenes/parkour.py`, ~470 lines. First-person infinite parkour
over an ocean:

- Course generated one block at a time: gap from `GAP_TABLE`, height change
  from `RISE_TABLE`, Gaussian sideways drift steered back toward a spine, with
  a fan of candidate headings rejecting placements that land on recent course.
- Motion is a ground/air state machine with a real ballistic arc solved to land
  exactly on the next block (`_begin_air` computes `vy0` from the gap and the
  height difference). Tests assert it lands where it aimed, every hop.
- Camera: yaw eases toward where it is going, pitch follows vertical velocity,
  a little roll into turns, landing dip.
- World below: ocean plane, drifting cloud shelves, grass-capped voxel islands,
  a 2D haze band for aerial perspective.
- Held stone block + arm in the corner, crosshair centre screen.

Per-frame cost is 1.3 ms against a 16.7 ms budget, so there is a lot of room.

## What it is missing

Judgement calls, not a spec — look at reference footage and decide. Starting
observations from the last session:

- **The course is visually monotonous.** One cube shape, one size, six colours.
  Real footage has slabs, stairs, fences, panes, ladders, glowing blocks,
  chequerboards, and structures you run *through* rather than only *on*.
- **Nothing marks progress.** The runner has coins, a score, a combo. Parkour
  has a distance counter and nothing to collect or aim at.
- **No verticality events.** Every hop is much like the last. Reference reels
  have long drops, staircases, tight zigzags, and occasional big set-pieces.
- **The world below is thin.** Islands are grey-brown blobs. Trees, structures,
  boats, waterfalls, varied biome colour would all help, and it is all free
  (fog hides most of it).
- **No block-break / placement flourishes**, which is most of what makes
  Minecraft footage read as Minecraft beyond the hand.
- **Weather and time of day are inherited from the palette but barely used.**
- **The hand never does anything.** It bobs and punches on landing. It could
  swing, place a block, hold different items per run.

## What must not regress

- `python -m pytest tests/` — 298 green. Parkour is covered by
  `tests/test_generation.py` (gap/rise tables, no self-overlap, altitude band,
  lands on the block it aimed for, bounded memory).
- Determinism: same run number replays pixel-identically. Everything generated
  must draw from `seed.stream("label")`.
- Per-frame budget. Measure with the perf harness pattern in the git history
  (`HeadlessWindow` + `SetTargetFPS(0)`, since `DesktopWindow` has vsync on and
  will report a flat 16.6 ms that tells you nothing).
- If you add anything the player can hit, it needs a hitbox derived from
  measured geometry the way `engine/collide.py` + `assets/measure.py` do it for
  the runner — not typed-in numbers.

## Landmines

`CLAUDE.md` has the full list and it is current. The ones most likely to bite
here:

- Vertex colours are banned in assets; the software rasteriser ignores material
  colour when a colour attribute exists.
- `ClearBackground` every frame — it clears depth too.
- Rebuild an asset, re-run `python assets/measure.py`, or `tests/test_assets.py`
  fails.
- Captures are corrected by measurement (`engine/rl.py:_capture_fix`); never
  read the screen directly.
- Blender 5.0.1 reproduces every committed asset exactly, so rebuilding is safe.

## The dev loop

```
python -m brainrot shoot --scene parkour --seed 5 --frames 400 --every 130 --out shots/
python assets/media.py parkour      # refresh docs/media
python -m pytest tests/ -q
```

`shoot` renders exact frames of exact runs. All the art direction on this
project was done by render, look, adjust, repeat.

## Also open

**Parkour is not playable yet.** `Scene.playable` is False for it, and the loop
will not hand it a keyboard. If you want it controllable like the runner,
design the scheme first — the character auto-hops along a generated course, so
"control" probably means steering the *choice of next block* (left/right
biasing the heading) and possibly timing the jump, not free movement. See
`engine/input.py` and `RunnerScene.control` for the contract.

**Train-roof running in the runner** was built in full and reverted; see the
section in `CLAUDE.md` for why and what it would take.

---

## Prompt to paste

> I'm continuing work on claude-brainrot on the branch
> `claude/project-visuals-animations-qzbkiq`. Read `CLAUDE.md` and
> `docs/HANDOFF-parkour.md` first — the handoff explains the job.
>
> Short version: the runner (Subway Surfers) scene got a deep pass last
> session — measured hitboxes, a real planner, generation invariants, proven
> zero interpenetration over hours of simulated running. The parkour
> (first-person Minecraft) scene only got a light one. I want it brought up to
> the same standard: much richer block and course variety, something to collect
> or aim at, real set-pieces and verticality, a world below worth looking at,
> and the held item doing more than bobbing.
>
> Work the way the last session did: render frames with `brainrot shoot`, look
> at them, adjust, repeat. Keep all 298 tests green, keep runs deterministic per
> seed, keep the frame budget (parkour is currently 1.3 ms of 16.7 ms). If you
> add anything the player can collide with, derive its hitbox from measured
> geometry the way `engine/collide.py` and `assets/measure.py` do for the
> runner — don't type numbers in.
>
> Take as long as it needs and iterate. Commit in meaningful chunks.
