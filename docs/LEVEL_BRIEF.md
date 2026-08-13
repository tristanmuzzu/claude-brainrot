# Redesigning one level

You own **one** module in `src/brainrot/scenes/levels/`. Nothing else in the
repository is yours. Read this whole file, then `docs/RULES.md` §1 and §7, then
`src/brainrot/scenes/levels/_base.py`, then your own module — before you change
a line.

## Why you are here

The owner watched the tower live and said, close to verbatim:

- Ninety per cent of the levels are bad. The jumps are not thought out.
- Half the jumps are at ground level or lower — you can walk much of a level
  and only start jumping later.
- There are not many non-standard jumps: a couple of ground-level hops, then a
  couple higher, then stairs, then you drop back down.
- The levels are too long and too thin. They keep going without much
  happening. **They should be shorter and feel longer** — more complex in what
  happens, not more metres of it.
- Every level must have exactly one way to the end. No walking half of it.
- Every jump should be *planned*: why from this block to that one, what the
  physics of it are, what it asks of the player.

The building underneath you was rebuilt on 2026-08-13 and is not the one the
older docs describe. It now has an outer wall on the drop side about a third
of the way round (so a stretch of your level is a corridor with rock on both
shoulders and a stretch is a shelf with the drop), a floor made of ten-odd
materials instead of one, a banded cliff instead of a grey slab, and an exit
ladder that actually anchors. Those were the engine's failures. What is left
is design, and that is your job.

## What is fixed and what is yours

**Fixed. Do not change these, they are assigned across the whole tower:**

- `rise` — the tower's vertical rhythm, assigned so any three consecutive
  levels sum to a legal head-room.
- `landmark` — assigned so no blueprint repeats within four levels.
- `theme` and the level's name.

**Yours, all of it:** `beats`, `filler`, `exit_beats`, `exit`, `gap`,
`profile`, `shelf`, `band`, `breaks`, and every material override in the skin.

## What to aim at

1. **Get off the floor.** 55% of authored landings across the roster sit at
   `lift` 0 or 1. That is the "half the jumps are at ground level" complaint,
   measured. A level that spends its first four beats at lift 0–1 reads as a
   walk with decorations on it.
2. **Author your own way out.** `Level.exit_beats` is live and tested and *no
   level uses it*. Without it your level ends in a generated staircase that is
   about a third of everything the viewer sees. Write the exit: a ladder up a
   chimney, a bubble column, a spiral of ledges — whatever your place has.
   The generated climb stays underneath as the fallback if yours cannot be
   built, so this is safe to attempt.
3. **Density, not length.** Fewer metres, more happening per metre. A beat
   that is three hops in a row at the same height is one idea; a beat that is
   a duck under a lintel, a drop onto a slab and a jump over a pour is three.
4. **One route.** No stretch of your level should be walkable past the
   parkour. `--all` prints the no-jump walk coverage for your level; the real
   map averages 46% and no level of it is passable end to end.
5. **Be a place.** The theme's floor palette is built for you now; use
   `deco`, `moat`, `shell`, `ceiling`, props and the liquid to make the level
   about something. Say what it is in the module docstring, in prose, the way
   the existing ones do.

## The physics, in one paragraph

One jump impulse, one horizontal speed. Flat, a hop reaches 2.00–4.26 m
stand-point to stand-point; rising one block, 2.00–3.10; descending one,
2.35–4.98. **Nothing rises two blocks in one ballistic move** — the
discriminant has no solution, exactly as in vanilla. A rising hop's `arc`
stays at or under 3.6; a flat one under 4.9; only a descending jump may ask
more. A head-hitter lid sits at **three** above the take-off, not the genre's
two, because a jump's apex sweeps the two cells above every take-off. All of
this is in `docs/RULES.md` §1 with the derivations.

## How to verify

```bash
python tools/level_review.py --level N --all
```

Four artefacts in `shots/review/lNN_slug/`: the game camera over your level and
into the next (**this is the judge**), a blueprint of the built world in
elevation and plan (the only view that shows ground running unbroken past your
jumps), a Blender three-view, and your level's numbers. `--seam` prints what
the level below hands you and what the level above opens with.

**Judge the contact sheet with your own eyes before you look at any number.**
Three separate metrics were green on this tower while the owner called it bad,
and two of them were mine. A number's job here is to catch a regression, not
to tell you the level is good.

## Hard rules

- **One level per process.** `level_review` pins the phase with a class-level
  patch and refuses a second level in the same run.
- **Never run `tests/test_tower.py` or the full suite.** They measure the whole
  tower and will report other agents' work in progress. The coordinator runs
  them at merge.
- **Never edit `spiralplan.py`, `handplan.py`, `_base.py`, any other level, any
  tool or any doc.** If your level needs an engine change, *do not make it* —
  say so in your report and design around it.
- `python tools/tower_probe.py --design-only` is instant, needs nothing built,
  and checks every authored jump in the roster against the physics. Run it
  after every edit; it is the fastest way to catch an illegal `arc`.

## Landmines that will cost you an hour each

These are the ones that bite level authors specifically; `docs/RULES.md` §7 has
the rest and is worth reading in full.

- A `shell=` or `moat=` is painted the moment its landing commits and blocks
  the **next** landing of the same beat. Put `shell=` on a beat's *last* node.
- Two `moat=True` landings must be more than three cells apart, and **never
  repeat a `moat` in `filler`** — the filler loops and the second lap digs away
  the ground the first lap's pedestals stand on.
- Changing `breaks` moves *every* break, not just how many.
- **Your exit climb's *launch* block is most of your jammed-lens number.**
  One level measured 69 wall-jammed frames of 1,293 with the launch landing at
  `hug=2.2`, and **0 of 1,280** at `hug=2.8`. Only the launch landing matters:
  `hug` on the climb node itself is inert (2.0, 2.2, 2.6 and 3.0 all produce
  worlds identical to the frame). If your sheet has a flat wall filling it
  during the climb, move the launch block out before you try anything else.
- **A `step_y` descent must not land at surface 1.0.** That is the terrace's
  own top cell: solid, so the landing is refused, the rest of the beat is
  abandoned, and the recovery drops a plain cube a block lower *under the
  beat's own name* — so the beat still reads as placed and the per-beat table
  cannot tell you why it is stuck at 85%. One agent lost two passes to it. The
  same rule with teeth: a bounce pad that is not at the bottom of a **two**
  block fall will not throw two, because the pad needs an arrival over 11 m/s.
- **`moat` and `pedestal_style` on the same node dig a pond full of that
  material.** `Course._moat` fills the bowl with `pedestal_style or
  theme.liquid`, so a landing written `moat=True, pedestal_style="log"` cuts a
  hole and fills it with solid, walkable logs — no error, no rejection, and
  your unwalkability quietly gone. Writing both on one node is a natural thing
  to do; do not.
- **A level whose `landmark` is gate-capable cannot really use
  `profile="channel"`.** The channel cuts its liquid exactly where the running
  line goes, so there is no footing for the gate, the reservation fails and the
  level pays for it and gets nothing — one level measured its structure on
  screen at 0.4 s until it moved to `plaza`, then 2.4 s. Since `landmark` is
  frozen, treat `channel` as available only if you are prepared for the
  structure never to be seen.
- `_targets` can return nothing and record no rejection. The cause is always
  `wants_ground` over a floor break, or `hug` past the shelf edge.
  `pedestal=False` is the fix.
- A beat's tail is almost never laid — put a shell, a lid or your non-hop verb
  on a beat's **first two** nodes, not its last.
- Anything past about the fifth authored beat is never built: a level lays
  9–12 landings and the exit climb takes some of those.
- **A stale `__pycache__` will hand you a fabricated A/B.** Editing a level
  module twice inside one second, where the two versions are the *same number
  of bytes* (`shelf=4.5` → `shelf=3.6`), leaves Python's cache valid by
  mtime-and-size and your second arm measures the first. One agent measured a
  nine-point walk-coverage "win" that way before catching it. Run
  `find src -name __pycache__ -delete` between arms of any A/B.
- **A failed node abandons the whole rest of its beat**, silently, and the
  recovery hop is committed under the beat's own name. So a beat reading 64%
  is not "some landings missed" — it is usually *one* opener that wanted
  ground it did not have, costing every node behind it. Suspect the first node
  of a beat, not the last.
- `frame empty` and `lens jammed` are seed-noisy. Average several seeds, and
  remember that changing your level re-rolls the levels above it, so a ±10
  point move on one seed is not evidence.
- **Your absolutes are not stable while your neighbours are being rewritten.**
  Thirty-two other levels are changing under you: one agent measured the same
  unchanged design at 63%, 57% and 44% designed content across three worlds
  that differed only in the levels *below* it. So take every decision on an
  **in-process A/B** — same roster, same seeds, both variants swapped on the
  live `Level` object inside one run — and quote absolutes only as
  approximate. Only the A/B is evidence.

## What to report back

Short, and in this order:

1. **What the level is now**, in two or three sentences. The place, the route
   through it, and the one thing a viewer would remember.
2. **The jumps, in a list.** For each: from what to what, the rise, the
   distance, and *why* — what it asks of the player. This is the thing the
   owner said was missing.
3. **Your judgement of the contact sheet.** What looks right, what does not,
   in your own words. Be honest; a level you are not happy with is more useful
   reported than hidden.
4. **The numbers** from `--all`: per-beat fidelity, lift distribution, no-jump
   walk coverage, and whether your `exit_beats` was built or fell back.
5. **Anything you wanted from the engine and could not have.**
