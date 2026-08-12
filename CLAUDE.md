# claude-brainrot — project context

A generated 3D "brainrot" overlay (Subway-Surfers-style runner + first-person
Minecraft parkour, flat and up a spiral tower) that appears while Claude Code
is thinking. raylib renderer, glTF assets built by the Blender scripts in
`assets/src/`, worlds generated per-seed. Read `docs/ARCHITECTURE.md` for how
the pieces fit; it is current.

## State of the project (updated 2026-08-12)

Branch `claude/project-visuals-animations-qzbkiq` holds a complete rebuild:
pygame → raylib + baked-light glTF assets, both original scenes rebuilt to
match the real reel formats, animation overhaul (rig with knees/elbows,
world-axis pose system, ballistic parkour hops with ground beats) — and a
**third scene, `spiral`**, which is the other Minecraft reel format, Parkour
Spiral — and, since 2026-08-12, a **fourth, `tower`**, which is that scene's
renderer against a *hand-built* course of twenty-four designed levels. `tower`
is what the default rotation plays. Both have their own sections below. (The
old ring tower and platform-stack spiral were earlier, deleted attempts at the
same format with the reference wrong; nothing of them survives, and the current
`tower_probe.py` / `test_tower.py` are new files about the new scene, not
resurrections.)

**Now verified on real Windows hardware with a GPU**, which turned up several
things the software-rasteriser cloud sessions could not have seen — see
"Landmines" below. 621 passed, 34 skipped, including a Win32 suite that
exercises the real window API.

The runner has a real collision model. Obstacles carry hitboxes derived from
the assets' own measured geometry (`assets/measure.py` → `metrics.json`), and
`scenes/runnerplan.py` plans lanes and take-offs *in time* and then verifies
the plan by simulating it before committing. Evidence: zero interpenetration
across 60 seeds × 180 s of simulated running, at every speed. If you change
anything in the runner, re-run that sweep — `tests/test_collision.py` covers
the same ground in a form that fits in the suite.

The runner had the same pass the parkour scene did (2026-08-11), for the same
complaint — "a bit slow, doesn't feel natural, something missing for it to be
actually entertaining" — and the same method: turn each complaint into a
number, write `tools/runner_probe.py` to measure it, then rewrite against the
probe. Four structural facts came out of it:

- **Content is laid down a set-piece at a time**, not a row at a time.
  `SEGMENT_TABLE` is the vocabulary — cruise, hurdles, slalom, tunnel, yard,
  express, roofrun — and each entry decides a stretch of track *and the
  corridor through it* together, which is the only way to express a weave, a
  train yard or a ramp onto a roof at all. A set-piece never follows itself,
  and one that finds the track it wanted occupied declines and is rewound
  whole (`_mark`/`_rewind`): a segment that wrote a corridor and then gave up
  used to leave those rows for the next one to overwrite from a different
  lane, and a corridor that steps two lanes in one row is a promise the body
  cannot keep.
- **There is an occupancy ledger, and a separate ledger for *moves*.**
  `_spans` is per-lane track occupancy in absolute distance and nothing is
  placed without asking it; `_acts` is the same idea for the stretch a jump or
  a slide commits the body to. Row counting stood in for both and could see
  neither: a 25 m train against a 6 m row is a great many rows of nothing
  being said, and two hurdles either side of a set-piece boundary put the
  runner's feet through the second while it was still coming down off the
  first.
- **The runner rides train roofs** — see below. That is the move the owner
  asked for by name, and the reason the motion model now has surfaces at all.
- **It starts quick.** The speed ramp was 8.5–15.5 m/s over 75 s, which is
  sensible for a game somebody sits down to play and wrong for a strip that is
  on screen for as long as Claude is thinking: it spent its whole visible life
  in the bottom third of its own range. 10.5–18.0 over 40 s.

The probe's numbers, before and after, both measured with the *same* probe —
`tools/runner_probe.py` runs against the old scene too, because a before/after
tool that only works on "after" measures nothing. Safety over 60 seeds × 180 s
after and 20 × 180 s before; pacing over 20 × 180 s both sides. Re-run it after
touching anything in this scene; the first two rows are non-negotiable.

| | before | after |
|---|---|---|
| obstacles drawn inside each other | 305,134 frame-pairs, worst 2.18 m | **0** |
| body inside an obstacle | 6 frames, worst 0.19 m | **0** |
| required actions per minute | 42.8 | **49.2** |
| median idle between actions | 1.15 s | **1.00 s** |
| 95th-percentile idle | 3.48 s | **2.78 s** |
| worst idle | 9.17 s | **7.48 s** |
| dead air (idle over 3 s, riding excluded) | 5.8% | **1.8%** |
| speed at 15 s / 30 s | 9.9 / 11.3 m/s | **13.3 / 16.1 m/s** |
| slides per minute | 4.6 | **4.5** |
| mounts onto a train roof per minute | n/a | **1.84** |
| median time to the first mount | n/a | **3.0 s** |
| seconds spent on a roof per minute | n/a | **2.35** |
| distinct obstacle kinds per 30 s | n/a | **9.1** |

Two of those deserve a note. The 6 body contacts before are the interesting
one: this file claimed zero interpenetration across 60 seeds × 180 s, and that
was true of the sweep it was measured on and is not true of `HEAD` — the
guarantee had quietly lapsed. And **slides per minute did not move**, which is
the honest reading of a mix that looks much more varied: the slide was always
about as frequent as it is now, and what changed is that it arrives in a
*tunnel* of two or three rather than singly. Nothing in the probe measures
that, and it is the kind of thing only looking at a contact sheet catches.

The overlay is **installed and verified end to end** on the owner's machine:
hooks registered, daemon running, `brainrot doctor` 12/12. Measured live —
appears 2.0 s after `UserPromptSubmit`, click-through, never focused, off
alt-tab, hides 3.0 s after `Stop`, and (2026-08-07) stays hidden while the
window in front is not the one the prompt came from.

The parkour scene has had the same depth pass, and then a second one
(2026-08-11) after the note that "the blocks are sometimes inside each other"
and "the parkour feels fake and scripted". Both were true and both were
measurable; `tools/parkour_probe.py` is the thing that measures them and the
numbers it prints are the acceptance criteria. Before: 3,756 interpenetrating
solid pairs in 8,000 blocks (worst 0.87 m), 0.2% of blocks on an integer grid,
the body inside a solid block on 9.3% of frames, and the player standing
perfectly still for 30% of every frame drawn. After: **0, 100%, 0.04 m worst
case, and 0%.** Re-run it after touching anything in this scene.

Then a third pass (2026-08-11, later) for "invisible blocks or walls blocking
other stuff", "tiny jumps that would be very weird to do quickly", and "make it
more difficult". All three were real:

- **The invisible walls were the glows.** See the depth-write landmine below.
- **The hops were too short**, and one number fixed nearly all of it: `MIN_HOP`
  went 1.1 -> 2.0, and because every set-piece's gap goes through `fit_gap`,
  every hard-coded one-block gap in the file widened to two at a stroke.
  Take-off to landing went from min 1.32 / median 2.43 to **min 2.32 / median
  2.79 / mean 3.03 m**; landing to landing, which is what the probe has always
  printed, went from min 2.00 / median 3.13 / max 6.45 to **2.99 / 4.00 /
  8.18**.
- **The course now ramps.** `difficulty` goes 0 to 1 over the first 80 blocks
  laid. Mean flight by block index: **2.93 -> 3.08 -> 3.15 -> 3.14 m** across
  blocks 0-40, 40-80, 80-200, 200+ -- it climbs and then *holds*, which is the
  half of a ramp that is easy to get wrong. Two new set-pieces, `slabs`
  (half-height landings) and `squeeze` (beams to skim under, columns to
  clear). Report the ramp on the **mean**: a hop length is one of a handful of
  discrete values, so the median snaps between modes and can move the wrong
  way between two samples that differ by a few per cent.

Four structural facts, all of which the tests state:

- **The course is on an integer lattice, with an occupancy map** (`_solid`).
  Headings stay continuous — a course restricted to eight compass points looks
  like a maze — but placement snaps to whole cells, and whole cells cannot
  interpenetrate. Placement asks four questions: are the block's cells free,
  are the two cells above the landing free, is the hop one a body can make,
  and does the *arc* pass through anything.
- **Motion is vanilla's.** `GRAVITY`, `JUMP_V`, `RUN_SPEED`, `AIR_SPEED` are
  Minecraft's own numbers converted from ticks. Horizontal speed is
  **constant**, so `flight()` is one line and every hop is the same motion at
  a different height. What used to be there solved each hop for a duration and
  then clamped it, so speed swung between 3.5 and 6 m/s from hop to hop.
- **The body never stops.** It lands on a block's near edge, runs across it,
  and leaves from the far edge; the beat on each block is a run-up, and its
  length is that distance at sprint pace rather than a number anybody chose.
  This is the single change that answers "feels scripted".
- **The course knows its own path.** Where the feet land and leave is decided
  when the block is generated, so the arc of every future hop is computable at
  generation time. Orbs hang *on* that arc at chest height, which is why
  "every orb laid down is collected" is a test rather than a hope. An early
  jump moves the take-off, so `_begin_air` re-solves the arc and re-hangs that
  hop's orbs; on autopilot the two are identical numbers.

A fifth: **the difficulty ramp is counted in blocks laid, not metres
travelled** (`ParkourScene.difficulty`). Generation runs fourteen blocks ahead
of the body, and the probes and half the generation tests grow a course by
calling `_spawn_block` without ever moving one -- keyed to `self.distance` the
ramp would read zero forever and every test that believes it is checking the
hard end of the course would be checking the easy one.

`scene.stuck` counts the times placement fell back on its unchecked emergency
hop. It must stay zero — when it was not, the visible symptom was a flight of
stairs stacked nearly vertically, and the cause was a set-piece asking for a
gap its rise could not support. `fit_gap` now reconciles the two centrally.

The strip can also be **dragged where you want it**: hold `drag_chord`
(`ctrl+alt`) and drag with the mouse; double-click while holding it to go back
to automatic placement. Click-through is lifted only while the chord is held
*and* the pointer is over the strip, so an ordinary click still belongs to the
app behind, and focus is never taken. Where it was dropped is stored as an
offset from the host window (`placement.py`), so a remembered spot still
follows that window and still means something at another resolution.

`runner` and `parkour` can also be **driven by hand** (`engine/input.py`):
arrows or WASD, up/space to jump, down to duck, eight idle seconds to hand
back. The overlay never reads a key until the takeover chord deliberately gives
it focus — there is no global key hook, on purpose. `brainrot demo` needs no
chord. Both opt in via `Scene.playable`; `spiral` does not, because a course of
solved helical arcs has no free movement to hand over. Steering parkour bends the
*course* rather than moving a body: there is no free movement to give a runner
made of solved arcs between blocks that do not exist yet.

The overlay is on screen **only while a Claude Code window that is actually
working is the window in front** (`follow_focus`, default on). Ownership alone
was never enough for that — it decides what covers what, not what is visible,
so a strip that did not overlap whatever you switched to just sat there over
it. Each frame the daemon compares the real foreground window against the
hosts of the sessions currently thinking; `ThinkingState` tracks those per
session id, from prompt events only. Not one of them, and not the overlay
itself (the takeover chord makes the overlay the foreground window — a naive
"hide unless the host is in front" hides the strip the instant you press it)
→ fade out. Unknown host means hidden, never topmost.

It is also **placed against the host window rather than the screen**
(`engine/window.py:place`, pure geometry, `tests/test_placement.py`). Docking
to a monitor edge put it straight on top of the Claude Code sidebar, which is
what a screen edge holds in every app worth overlaying. It now stands *beside*
the host window when the desktop has room and in that window's own gutter when
it does not, on the `dock` side, re-checked every frame so it keeps up with a
window being dragged. Real geometry lives in `overlay/win32.py`
(`window_rect`, `work_area`, `move_window` — `SetWindowPos`, never raylib's
`SetWindowPosition`, which would block off-thread).

## The spiral tower: a cone of stacked levels (rebuilt 2026-08-12)

A third scene, `spiral`, and the other Minecraft reel format -- the Parkour
Spiral genre, where the course winds up the outside of a tower that keeps going
out of the top of the frame.

**The trough is not a ramp: it is a stack of levels, and that is the headline.**
The owner looked at a render and said *without the parkour you could still just
walk up this*. He was right, and it was geometry rather than course design: the
trough climbed a block every eight blocks of arc -- a spiral staircase, which a
body walks up without noticing -- so every landing was decoration on a ramp that
already reached the top. A `Section` is now a **level**: a flat themed terrace,
then a chasm with no floor in it at all (`GAP_ARC = (2.8, 3.9)` blocks of arc),
then the next terrace `LEVEL_RISE = (4, 6)` blocks higher. Neither half is
passable, so the only way out of a level is the climb out of it. **The
acceptance test is a walker**: `spiral_probe`'s `walkability` floods the *cone
alone* -- no course blocks, no pedestals, no dressing -- one block up and any
survivable drop, and gets **0 m at worst, 0.0 m mean**.

- **One turn must be a whole number of levels** (`LEVELS_PER_TURN = 3`). The
  ceiling over level `i` is the floor slab of level `i + LEVELS_PER_TURN`;
  anything else has soffit and floor stepping at different bearings and sawing
  against each other.
- **The rises vary**, so a revolution gains 12-18 rather than a fixed 22 -- the
  other half of the same complaint, that it climbed at the same rate forever.
- **`unwrap` is no longer a division.** It was one while every turn rose by the
  same fixed amount and cannot be now, so it walks the levels at a bearing (they
  are `j`, `j+3`, `j+6`...) to the last floor at or below the height. That walk
  is why `Course._rock` memoises.
- **The exit climb (`ascent`) is ~47% of all landings** and is the load-bearing
  feature: a staircase of ledges against the core, or a ladder, vine or
  soul-sand column where the theme has one (`Theme.exits`). Stairs are weighted
  well above the vertical climbs for a *measured* reason -- stair-only exits
  fall through to the unchecked hop on 2.35% of landings, mixed exits on 3.05%,
  because a ladder needs a free column, an anchor and a launch block hard
  against the core, and any of the three can be missing.
- **The staircase has a theme's own footing** (`Theme.step`, a
  `(material, move)`). Being half of every run, one stone and one hop in all
  fifteen places was the largest source of sameness left: the farm climbs hay,
  the nether soul sand, the mine oak, the end purpur, and the ice level climbs
  packed ice on *slides*, which reach further than a hop for the same rise.
- **The crossing descends one block.** `hop_span(-1)` allows 2.35-4.98 m where a
  flat jump reaches 4.26, so the staircase climbs one *above* the next level and
  the last jump comes down onto it.
- **The crossing must actually cross** (`node["cross"]`), and until 2026-08-12
  nothing said so -- it was a landing on the trough's own ground, and the
  nearest such ground is the terrace being climbed off. It is also **re-aimed
  from where the climb got to** (`_aim_crossing`) rather than from where it was
  planned a dozen blocks earlier; asked too early it is refused, and the climb
  lays another step and asks again. This one bug was three quarters of every
  unchecked placement the format had.
- **And when nothing crosses, the far wall does** (`_grab_the_wall`): a ladder
  or vine up the other side of the chasm, checked by `_climb_move` like any
  other climb, tried immediately before the unchecked hop.
- **The staircase stays on the level's own ground** (`node["confine"]`), and
  nothing may be placed in a chasm below the far level's floor
  (`Course._far_floor`): a body stranded low over a chasm cannot get out, the
  climb re-plans from inside the hole, and lays its staircase through the one
  already there.
- **`hug` is a distance, not a flag.** An exit climb laid mid-lane finds no
  anchor and fails, and that was 96% of every run that got stuck -- but at 1.0
  the wall filled the lens. The column stands one cell back from the landing it
  caps, so 1.6 still finds its anchor while the *body* stands clear (2.2 for
  its launch block, 2.4 for a staircase). And **no slab step in the exit
  stair**: a slab stands half a block up, so the step after asks for +1.5.
  `step_y` is nevertheless measured between *walking surfaces* rather than
  between block floors, because a stair may still *begin* on a slab some other
  feature left behind -- and asked as `prev["y"] + 1` that beginning was a rise
  of one and a half, which no hop has, refused identically at every distance.
- **Head-hitters are a checked constraint**, not a beam drawn near a jump -- the
  lid goes into the arc's clearance test, so a landing whose jump would rise
  through it is refused. Why it sits at three, not the genre's two: landmine
  below.
- **Landings are the level's own stone, marked by being *lit*** -- the candy
  palette is gone from this scene. Owner's objection and map-making consensus
  both: a contrasting jump block wrecks the theme and buys nothing (a cake and a
  cobblestone have the same hitbox), so light the landing face (`LAND_LIT_FAR`).
- **Ladders and vines are thin models on a block face**, not 0.84-wide cubes
  (`assets/src/props_climb.py`, tileable vertically). Which face is recorded
  when the column is placed: working it out at draw time is how you draw a cube.

**The building** is one solid **inverted cone** (`BASE_R = 24.0`,
`FLARE = 0.05`, 1.7x as wide at the crown over fourteen revolutions), and the
"forest of columns" in the reference is its **skin** -- one-cell ribs
alternating in and out for the whole height (`RIBS = 56`, `SKIN = 2`, taken from
the *bearing*, since arc-length ribs drift up a growing circumference and read
as a barber's pole). You are always in a **corridor**: drop and sky outboard,
fluted core inboard, the slab above as a ceiling (`BAND = 9.5`, `FLOOR_T = 5`
out of a turn of 12-18, so about a third solid and seven to thirteen blocks of
open air), three themed sections to a revolution with *hard* seams, 6-10 s of
strip each, fifteen themes from a shuffled bag, and the parkour **built into the
theme's own ground** -- floating blocks over the void are a *theme* (the wool
section), not the default. That shape was misread twice getting here; the
history is in `docs/ARCHITECTURE.md` § "Scene formats".

**Three modules, and the split is the point.** `scenes/parkourkit.py` is the
kernel -- vanilla's motion numbers, `Move` as a list of legs, `hop_span`,
`fit_gap`, the lattice helpers, `body_cells`, `MATERIALS` -- extracted
**unchanged** from the deleted ring-tower plan, being the part that measured
clean and had nothing to do with a building whose shape was wrong.
`scenes/spiralplan.py` is the cone, the levels, the course and 35 features
besides the ascent; `scenes/spiral.py` is the renderer and nothing else. Neither
plan module imports raylib: a 24-run sweep costs seconds and no window.

**The building is analytic, and that deletes a class of bug.** `Cone.rock(cell)`
answers "is this inside the tower" in closed form, no memory, same answer
whenever asked, so nothing can appear behind the course. The old design streamed
its building into an occupancy map as the course advanced -- a wall could be
built through a jump already solved -- and needed four reservations to defend
against that. Three remain (`headroom`, `pathcells`, `softcells`) plus `ground`,
the cells load-bearing *under* a landing: a `floor` landing places no block, so
without it a pond dug during dressing takes the floor out from under one.

**Course first, terrain second.** The course is laid, its arc, its run and its
head-room reserved, and only *then* is terrain painted around what is reserved,
so terrain laid second cannot block a course. Building the world first and
negotiating through it started at **13% of nodes** falling through to the one
unchecked emergency hop; it was 0.46% before the levels, 2.98% with them, and
**0.30%** now -- better than before the levels, and the regression that stood
at the top of "Still outstanding" for two days is closed.

**What closed it was one bug, and it never once looked like one.** The exit
climb's last node was a landing on the trough's own ground at whatever bearing
its arc reached -- and *the nearest such ground is the terrace the body has
just spent five landings climbing off*. So a staircase would gain its blocks,
come down where it started, and be asked to climb out again with less room each
time; the run reached the chasm lip having climbed nothing, and there is no
jump in this motion model that both crosses a hole and gains four blocks.
Nothing caught it because **the crossing always succeeded**. A crossing now
carries `cross`, `_targets` refuses any candidate on the level being left, and
`_aim_crossing` re-measures the jump from where the climb actually got to
rather than from where it was planned -- so a crossing asked for too early is
refused and the climb lays another step instead.

Four more, each found by reading `Course.rejects` and none by reading the code:

- **`step_y` is a rise between *walking surfaces*.** It was `prev["y"] + 1`,
  so a stair starting from a slab asked for +1.5, which no hop has, and every
  candidate failed identically at every distance.
- **A failed climb recovers with another climb** (`_climb_on`), not with a hop
  at a height measured from the level's own floor -- which, three blocks up a
  staircase, is a *descent*.
- **...but only while there is climbing left to do.** Past the height it needs
  it walks. Gaining a block on every filler stride runs the body up into the
  slab overhead, and then every cell around it is solid.
- **When nothing can leave a level, climb the far wall** (`_grab_the_wall`). On
  the ground at the lip, three below the far terrace, there is a wall three
  metres away with four blocks of climbable rock in it. Halved the rate on its
  own, and it is the only recovery in the module that improves the move mix.

Three things that were tried and made it **worse**, all measured, none obvious:
a switchback staircase across the corridor instead of along it (0.64% ->
1.34%); converting arc-to-angle at the body's radius instead of the tower's rim
in `_plan_feature`, which is *arithmetically correct* and still costs a point,
because the same number is the ordinary features' truncation budget and
shrinking it cuts them to single nodes; and triggering the climb earlier, for
the same reason.

Two defects that cost real time here, both of the kind that recurs:

- **`Cone.rock` had two unreachable branches.** `unwrap` returns the level *at
  or below* a cell, so the branches for lower heights never fired -- a smooth
  cylinder with the themes as stripes and nothing to run along. Found by
  rendering the world in Blender from outside, not by reading the code.
- **Nothing rises two blocks in one ballistic move**, and a landing one block
  above the ground reached from one *on* the ground across a step asks for two:
  at two thirds of the stuck cases *every* candidate rose exactly +2.0. The
  clamp is in `Course._targets`, `BALLISTIC` kinds only -- clamping ladders and
  bubble columns too took climbs and lifts from 3% of moves to none.

**The world is emitted outward from the body, not upward from the bottom.**
`Course.build_world` alternates out from a `y_from`, because the chunk mesher
builds in the order cells were dirtied -- bottom-up means the first thing meshed
is the world forty-six blocks *below* the camera, which is fog: 422 chunks still
unmeshed after priming, three and a half seconds of a strip watching its own
world assemble. The prime is bounded (`PRIME_CHUNKS`) for the opposite reason --
`_begin_scene` runs when the strip becomes visible, and meshing the lot took
construction from 1.1 s to 1.6 s. Likewise a run opens on `START_LEVEL = 4`, a
fifth of the way in: the bottom of the tower has nothing under it to draw, and a
run opening beside a chasm opens looking at sea and sky.

**Dressing needs a margin around the running line.** `pathcells` is exactly
body-width, so a cell merely *adjacent* to a jump passes that test -- and a
block face half a metre from an eighty-degree lens is most of the frame. A fifth
of a contact sheet was solid green before `_dressable`'s margin existed.

**The camera is pure geometry, and it set a generation constant.** The body runs
*outside* a convex core, so a camera looking along the trough looks down a
tangent -- and a tangent to a circle you are outside of never meets it. At a
13-block band the core wall sat 50-90 degrees off the direction of travel at
every bearing against a 52-degree horizontal field: drawn correctly on every
frame, visible on none. The fix is not aiming at it (that means running
sideways) but *standing nearer to it* -- `BAND = 9.5`, `COURSE_OUT = 0.5` --
plus blending the head's bearing toward the trough's tangent (`TANGENT_MIX`),
because aiming only at the next few landings swings the view out over the rim.

Two more numbers: `LIFT_MAX = 6` (seven to thirteen blocks of open air, two
needed over the head, and a landing higher has the next turn's slab for a
ceiling before it has anywhere to jump to), and `GAP_RAMP = 0.26`, applied
centrally in `_node` because most features want a *fixed* shape and would sit
out the ramp -- before it, mean hop was 2.62 m at the start of a run and 2.67 m
two hundred landings in. The exit climb is exempt by name: stretch its arc and
the last steps of the staircase hang over the chasm.

**Platform furniture is models, not cells** (`assets/src/props_mc.py`,
`props_flora.py`, `props_deco.py`, `props_climb.py`): crops, fences, torches,
rails, bamboo, cacti, lily pads, mushroom caps, chorus plants, dripstone,
ladders and vines are the parts of Minecraft that are *not* cubes, and as cells
they all come out as the same coloured box. Fourteen per section
(`PROP_BUDGET`), one draw call each, distance- and direction-culled.

## The spiral's difficulty is per level, not per run (2026-08-12)

One ramp over the first seventy landings makes every level past the seventieth
the same level. A **level** is the natural unit instead -- a themed terrace
with a beginning and an end, six to ten seconds of strip, one place to the eye
-- so each draws its own pitch (`Section.hard`) and `Course.difficulty` is that
times the opening ramp. The distribution's *top* opens out with altitude while
its floor stays put (`HARD_FLOOR`, `HARD_TOP`, `HARD_SPAN`), which is the
difference between a course that gets harder and one that gets more varied: a
mild level can still turn up late. Measured over 630 levels, mean hop by pitch
band: **2.80 / 2.93 / 3.07 m**.

Two things ride on it, and one is the only lever there is on the move mix:

- **A level is about something.** It picks a signature verb from its own theme
  (`Section.signature`), weighted `SIGNATURE_WEIGHT` above the rest of the
  pool, preferring one that is *not* a jump where the theme owns one
  (`NON_HOP`). On identical worlds that is worth **+1.4 points of non-hop
  share** (4.8% -> 6.2%). Nothing else moves that number: the exit climb is
  half the course and can only ever be hops.
- **"Harder" lives in what the pool is made of** (`HARDER`), not in gap length.
  One jump impulse means the whole usable range is 2.0 to 4.3 m and a course
  spends it by the second landing; a lid to stay under, a one-cell landing and
  a hole with nothing in it are different *questions* and the pool can ask them
  as often as it likes. A hard level also stops being offered the easy beat
  (`flat`).

**Do not read a stuck-rate change across this commit as a regression without
the A/B.** Adding two draws to `Cone._extend_section` re-rolled every world, and
the same generator reads 0.45% on the old stream and 0.59% on the new one.
Flattening the difficulty back to a constant *on the new worlds* also reads
0.59%, which is how it is known the variety costs nothing.

`tools/spiral_probe.py` is the acceptance test in numbers and is self-contained.
Current, over 24 runs x 296 landings, 6 runs x 40 s and 8 walk runs:

| | |
|---|---|
| **climbable without the parkour** | **0 m at worst, 0.0 m mean** |
| cells twice-claimed / off-lattice / soft in rock / orbs missed | **0** each |
| unchecked emergency placements | **0.30%** (was 2.00%) |
| body inside the world | 0.03% of frames, worst 0.50 m |
| **landings on built terrain** | **94.1%** (terrace 6.3%, floating 5.9%) |
| hop length min/mean/max | 1.48 / **2.90** / 5.95 m |
| mean hop by landing index | 2.77 -> 2.87 -> 2.93 -> **2.94** (climbs, then holds) |
| altitude gained | **0.74 m/s** mean |
| revolutions per minute | **2.73** (4.9-10.5 s on one theme) |
| moves per minute | **99.8**, median idle **0.52 s** |
| dead air (idle over 3 s) / frozen | **0.3%** / **0.01%** |
| clear lens ahead | median **8.00 m**; **1.24%** of frames inside 0.8 m |
| move mix | hop 94%, slide 3%, climb 2%, bubble 1%, then web, walk, bounce |
| feature mix | 38 kinds; all 15 themes seen; commonest after `ascent` are `headhitter` 4%, `spire` 4% |

Three notes. **The lens figure halved** (2.41% -> 1.24%, measured against the
same twelve runs) and it is still the worst row in the table: a contact sheet
of twenty frames has three or four looking straight into a wall. That is the
camera problem in "The camera is pure geometry" and not a course problem, and
it is now the top outstanding item. The **body figure is not zero** -- the
residue is a pedestal or a piece of dressing built after an arc was solved, and
the probe's exemptions are the three the generator makes (the landing being
left, the landing arrived on, and a slab, whose surface is halfway up its own
cell). And the **38 feature kinds are the 35-feature vocabulary plus `ascent`,
`start` and `stuck`** -- if `stuck` goes, emergency placements are at zero.

**When it goes wrong, turn on `TRACE`.** It is a counter round `Course._attempt`
recording *which* check refused each candidate, off by default because placement
asks those questions a few thousand times a landing. Every reduction this format
has had, 13% of nodes down to a third of one per cent, came from reading that
table, and **not one was found by reading the code.** Rebuild it before changing
anything here. Worth knowing about the last pass: the raw table names the check
that refused most candidates, and for the exit climb it said `no move: hop`
loudly and *was pointing at the wrong landing*. What paid was counting the
**first** failure in a climb rather than the one that finally ran out of
answers, and bucketing it by how much terrace was left and how far below the
next level the body was -- two lines of context that turned one undifferentiated
pile into four separate bugs.

## The hand-built tower: `tower` (added 2026-08-12)

**The scene the rotation plays.** Same building, same physics, same renderer,
same placement checks as `spiral` — and the course is *written down* instead of
chosen. `docs/TOWER.md` is the design; `scenes/handplan.py` is that design as
data. Read the doc before touching a level.

Why: the generator is safe and is not memorable. Its levels are a different
*mix* of one thirty-five-entry vocabulary rather than different *places*, so
every run has the same shape. Two numbers said it — the exit climb was 47% of
all landings and one of four shapes, and the move mix was 94% plain hop.

**`SpiralScene.plan` was already a class attribute**, and that is the whole
mechanism: `TowerScene` is `class TowerScene(SpiralScene): plan = handplan`.
`handplan.Cone` overrides one method (`_extend_section`, reading the level table
instead of rolling) and `handplan.Course` overrides three (`_choose_feature`,
`_feat_ascent`, `_level_budget`). Nothing else is forked. To make that possible
`spiralplan._plan_feature` was split into `_level_budget` / `_choose_feature` /
`_truncate`, and `Cone.base_r`, `Cone.flare` and `Course.ahead` became class
attributes.

**Authored intent, mechanical placement, verified physics.** Every landing is
written down. The lattice is resolved by `_targets` as it always was — the
*shape* is authored and the machine only picks the nearest cell. `_attempt` is
untouched, so an authored jump no body can make is refused exactly as a
generated one would be. **Fidelity is the acceptance criterion for the design;
safety is the acceptance criterion for the code**, they are different numbers,
and both are printed.

`tools/tower_probe.py` asks the question only a hand-built tower can fail: did
it come out as designed. It checks every authored jump against `hop_span` **on
paper** before building anything (`--design-only` is instant), then reports
fidelity per level and per beat. It found **nineteen real errors** on the first
pass, and the most valuable thing about it is what it found *second*: the
mistakes hand-authoring makes are not the ones you look for.

- Half of them were **at a beat boundary**, not inside a beat. Beats play in
  order and the jump from the last landing of one to the first of the next is a
  jump like any other.
- The largest single class was **the filler loop seam**. A level's filler
  repeats when the terrace outlasts the script, and `filler` defaults to the
  last two beats — which for a level that *ends* on a five-block fall is
  exactly the wrong choice. Eight of the twenty-four needed their own.
- The checker was itself wrong twice before it was right: it read `lift` off a
  climb node (climbs use `step_y`, measured from the landing before, so every
  jump after a climb was checked against the wrong height), and it used a flat
  0.68 m edge inset when `wide` is 1.05 at each end — a five-block gap between
  two mushroom caps is a three-block jump, and reading it as five condemns a
  good design.

Four things the design needed that are not the design:

- **The tower is half as wide again** (`Cone.base_r = 36`). A level is a third
  of a revolution, its exit climb needs a fixed run-up in *blocks*, and what is
  left is the design; at the generated radius that was four authored landings a
  level against seven for the climb. A bigger circle lengthens every terrace and
  changes nothing else — and straightens the corridor, which the camera likes.
- **The exit reserve knows which of the four shapes the level uses.** A ladder
  costs three landings whatever the height; reserving seven for one threw away
  sixteen blocks of a forty-block terrace.
- **Generation runs twenty-six landings ahead, not sixteen** (`Course.ahead`).
  A section is dressed when the *generator* leaves it, and with longer terraces
  the body was standing in an undressed section a third of the time.
- **A mid-level climb gets a launch block hard against the core**, the way the
  exit climb always has. Without it the ladder has nothing to hang on and is
  refused every single time — two beats measured 0% fidelity and the fix took
  them to 60-67%.

Measured, 16 runs x 340 landings and 6 runs x 40 s, against the generated tower
on the same probes:

| | generated | hand-built |
|---|---|---|
| designed landings placed **as authored** | n/a | **97.1%** |
| designed content / the exit climb | n/a / 47% | **68% / 33%** |
| distinct named beats in a run | 38 | **137** |
| named places | 15 shuffled themes | **24 designed levels** |
| mean jump / share over 4 m | 2.90 m / — | **3.12 m / 17%** |
| unchecked emergency placements | 0.30% | **0.13%** |
| cells twice-claimed / off-lattice | 0 | **0** |
| climbable without the parkour | 0 m | **0 m** |
| frames mostly filled by a wall | 1.7% | **0.4%** |
| seconds on one place | 7.3 s | **10.7 s** |
| per frame | 2.34 ms | **2.80 ms** |

Fidelity is not 100% and should not be: the tower is round and the world is
whole cells, so some authored point always falls between two of them. What the
number guards is *sag*.

**The one bug hand-authoring produced that no geometry check could see** was a
level naming a material the renderer has no recipe for (`candy0`, which this
scene deliberately does not define). Growing the course was fine; the run died
with a `KeyError` a hundred and forty frames in, the first time that block came
into view. Two guards now: the design checker refuses an unknown material
outright, and `tests/test_tower.py` builds, updates and **draws** the scene
every forty-five frames for nine hundred, across two seeds.

## Linux (added 2026-08-09, verified on the owner's Ubuntu box)

Runs on Ubuntu 26.04 / GNOME Shell 50.1 (Wayland, 200% scaling) with the same
behaviour as Windows: appears while a Claude Code window that is working is in
front, hides when you look elsewhere, hides on `Stop`, click-through, never
focused, stands against the host window. Measured live, not inferred.

The platform split is `overlay.native()`; the engine has no `os.name` tests
left. Read `docs/ARCHITECTURE.md` § "Two platforms, one vocabulary" before
touching any of it — the reasoning is there, this is the short list:

- **The strip is an X11 (XWayland) window on a Wayland session.** A Wayland
  client cannot place itself, raise itself, or shape its input region; an X11
  one can, and mutter honours it. `x11.prepare()` sets `glfwInitHint(
  GLFW_PLATFORM, X11)` before `InitWindow`. Clearing `WAYLAND_DISPLAY` does
  **not** do this: libwayland defaults to the socket `wayland-0`.
- **Everything about other windows comes from a gnome-shell extension**
  (`src/brainrot/extension/`), pushed over the daemon's own UDP port.
  `org.gnome.Shell.Introspect.GetWindows` is refused. It is optional; without
  it the strip docks to the work area and stays up for the whole turn.
- **The host is resolved from process ancestry, not a window handle.** There
  is no handle to read on Wayland. The shim sends its `/proc` ancestry
  nearest-first and `Snapshot.host_for` matches it against window pids.

## Still outstanding

0. **The exit climb is still a third of the hand-built tower.** The levels own
   *which* of the four shapes they leave by, and that is worth a lot -- 98
   distinct beats against 38 -- but not the shape itself, so a third of every
   run is machinery rather than design. The way in is to let a level author its
   exit the way it authors a beat, with the generated climb kept as the
   fallback it already is; the reliability guarantee lives in `_climb_on` and
   `_grab_the_wall`, not in `_ascent_stair`, so an authored exit that fails is
   already caught.
1. **A wall fills the lens on 0.7% of frames** in `tower` and 1.7% in
   `spiral`, down from 1.6% and 2.3%. What closed most of it was measuring
   *which segment the body was in* when it happened: 10% of exit-climb frames
   and **0% of every designed beat**. So it was never a camera constant that
   was wrong everywhere -- it was one arrangement the aim had no answer for,
   the course hugging the core for the whole climb, and the fix is an inner
   clamp on the aim point (`AIM_INSET`) matching the outer one that had always
   been there. The residue is the same shape and the same method will find it:
   `scratchpad`-style harness that walks a run, calls `spiral_probe._lens_jammed`
   every few frames and buckets by `blk["segment"]`.
2. **The spiral's move mix is 94% plain hop.** The exit climb is 47% of all
   landings and can only ever be hops, so this is bounded by what the *kernel*
   can express, not by the feature table -- reweighting `FEATURES` was tried
   and is not it. Two things did move it, both in this session: a level's
   signature verb prefers a non-hop where the theme owns one (+1.4 points on
   identical worlds), and `_grab_the_wall` doubled the climb share by turning
   the last stuck case into a ladder up the far side of the chasm. Getting
   materially past this needs a kernel change, and the honest list of what is
   available is short:
   - **Jump-cancel** (hitting your head zeroes the rise and keeps the run) is a
     closed form and would make `_ceiling_cells` honest at two blocks instead
     of three. Worth doing for the head-hitter, but note what it does *not*
     buy: worked through, a 2bc level jump reaches at most 1.7 m, under
     `MIN_HOP`. A 2bc is a thing you sprint under, not a gap you clear -- so
     the genre's `2bc` is already expressible today as a lid over a `walk` or
     `web` leg, which never rises at all.
   - **Momentum between landings** reads well on paper and fights this model.
     A `full` block's run-up is 0.68 m *by construction* (`EDGE` at both ends),
     so scaling jump speed by run-up length shortens every hop in the scene by
     about an eighth and takes the +1 reach from 3.10 to 2.73. The reason this
     project's body is always at sprint speed is that **it never stops** --
     which is a deliberate, load-bearing feature of the flat scene too.
   - **Two-leg steered jumps** (the neo family) and **ice accumulation** are
     both real and both still untried.
3. **`tools/depth_probe.py` does not know about the spiral or the tower.** It patches
   `parkour`'s own draw methods by name. The spiral's translucent draws --
   water, cobweb, lava glow, every emissive -- do all go through
   `fx.no_depth_write` / `fx.glow_pass`, and `tests/test_rendering.py` proves
   that guard is load-bearing at the `fx` level. What is *not* measured is how
   many pixels each individual draw in *this* scene would hide, which is what
   the probe would tell you. The tower's version of that coverage went with
   `tests/test_tower.py` and has not been replaced.
4. **DPI**: measured 2026-08-07 on the owner's 1920x1080 at 125%. The daemon
   *is* per-monitor DPI aware — GLFW sets that at `InitWindow` — so every
   `GetWindowRect`/`SetWindowPos`/work-area number inside it is in **physical
   pixels**, and placement is self-consistent. What is still open is that
   `width`/`height` are therefore physical too, so the strip is 1/1.25 of the
   apparent size you would expect from the number. Beware when comparing
   against an outside probe: a plain script is DPI-*un*aware and reads the
   same window back scaled (1920 → 1536), which looks exactly like a bug and
   is not. Call `SetProcessDpiAwareness(2)` in probes.
5. Per-frame cost at sustained top speed, vsync off, against a 16.7 ms
   budget. `python tools/frame_cost.py` is the harness and it does the things
   that have to be right: `HeadlessWindow` + `SetTargetFPS(0)` (`DesktopWindow`
   has vsync on and reports a flat 16.6 ms that tells you nothing), and the two
   scenes built alternately round by round, because only one scene may be alive
   at a time and alternating averages out whatever else the machine started
   doing. Absolute milliseconds off a busy machine are worthless; **the ratio
   between the two scenes in one process is not**.

   Measured 2026-08-11: parkour **2.02 ms**, runner 1.78 ms, ratio 1.15. Do not
   read that ratio against the old 0.75 without checking the denominator: the
   runner was rewritten in a parallel session and now measures 1.78 ms against
   the 2.6-3.0 ms this file used to record, and 2.02/2.8 = 0.72, which is the
   old number. What did change on this side is the new set-pieces -- parkour
   past the ramp costs 2.02 ms against 1.49 ms with `squeeze` and `slabs`
   weighted out, so their geometry is about half a millisecond. The ramp
   itself is free.

   The rebuilt `spiral` has **not** been through `frame_cost.py` yet, and the
   ring tower's 1.28 ms went with the scene -- do not quote it. It defaults to
   the three live scenes (`--scenes runner parkour spiral`), so the measurement
   is one command. What is known from the shape of the thing: a whole cone of
   face-culled geometry is one draw call per chunk against one call per cube,
   and the view-cone cull in `engine/chunk.py` was worth a third of a frame on
   the platform version of this scene.

   The runner's own set-piece rewrite was measured the same way, back to back
   on a busier machine: **1.025 before, 1.005 after**, against a round-to-round
   spread of 0.77 ms. Cost-neutral. Do not compare either of those to the 1.15
   above -- that was a quiet machine, and only the ratio survives the
   difference.

## Running along train roofs, and why it works now

The signature Subway Surfers move. It was written once before, in the history
around this branch, and **reverted** — not because the riding did not work, it
did, but because the lane search and the mount decision were made in separate
stages: the search was pulled toward a rideable train, and when verification
then rejected the mount the runner was already committed to a lane with a
train across it. Contacts went from zero to thousands.

They are one decision now, and the shape of it is worth keeping in mind before
touching any of it:

- **The set-piece commits or declines as a whole.** `_seg_roofrun` lays the
  ramp, the train, the corridor onto it, the clear lane to bail into and the
  clear sky over all of it together, and it solves the leap *at generation
  time* — at both ends of the speed range, because gravity and launch speed
  are rebuilt as the run accelerates. A ramp whose train is out of reach is
  not a hard puzzle, it is a promise the track cannot keep, so it is never
  laid.
- **The train is one threat with one answer.** It carries `mount_at`: the one
  moment a take-off can happen, which is when the ramp's lip is under the
  feet. `classify` reads that and returns `"mount"`; `schedule_vertical` books
  it; `plan.verify` rolls the lane path and the take-off forward *together*
  over a world that includes the train. If that fails, the existing machinery
  marks the threat hard, the search routes around it, and the bail lane is
  empty by construction. Both outcomes are safe; that is the whole trick.
- **The offer has a deadline.** `_mount_at` withdraws it as soon as the body
  can no longer be squarely in the ramp's lane before the foot of the ramp —
  while there is still track in which to leave that lane. Offering it right up
  to the ramp is what the reverted version did.
- **A run opens on one, 62% of the time.** Not a weight -- `_begin_segment`
  *tries* roofrun first on the opening set-piece, because a heavier weight is
  still a dice roll. The strip is on screen for one thinking turn, often
  fifteen or twenty seconds, and on the ordinary weights the median time to a
  first mount was 19.7 s: the owner watched several turns, saw no train to run
  on, and reasonably reported the feature as missing. It is 3.0 s now, and 72%
  of runner runs show one inside fifteen seconds against 30% before.
- **Riding is free to the lane search.** `MOUNT_COST` is 0.0 and has to be:
  the search already pays `preference` for every step spent outside the
  guaranteed corridor, so *any* positive cost on the roof makes standing
  beside the train cheaper than standing on it. At 0.4 against a preference of
  0.22 the runner stepped one lane clear of every ramp in the scene — 33 ramps
  laid down, 2 ever taken.

Two motion rules hold it up, and both are in `Motion.advance` so the check and
the execution cannot disagree: a body **holds its lateral position while it is
off the rails** (stepping sideways off a roof puts the fall alongside the
train with the box still overlapping the corner it left), and it is **held up
while its centre is over a surface but until its back has left it** (a body is
over a metre deep, and dropping it the moment its centre crosses the far edge
leaves the rear half hanging over a roof it is no longer standing on). The
ramp additionally only picks a body up within `RAMP_GRIP` of its lane centre:
you get onto a ramp by running at it, not by sideswiping it.

## Known limit: how long a parkour jump can be

There is one jump impulse and one horizontal speed, so the furthest a hop can
reach is fixed, and `hop_span(rise)` computes it rather than anybody choosing
it. Level, that is about 4.3 m stand point to stand point; reaching further is
available only by *dropping*, because falling takes longer and the body does
not slow down while it does. That is why `_seg_chasm` steps down — the extra
hang time of a one- or two-block drop is what buys the last metre, exactly as a
player clears a gap they cannot make level.

The same arithmetic runs the other way and is why `fit_gap` exists: a hop that
descends four blocks *cannot* also be short, because the arc covers close to
four metres of ground before it arrives. Descents therefore leap out into the
drop. And nothing can rise two blocks in one hop, because the discriminant has
no solution — the same reason vanilla cannot.

A chasm reads as a chasm because of the void under it and the two lit platforms
either side, not because of another metre of distance. If you want genuinely
long jumps you need a different motion model, not a bigger number.

## Dev loop (works headless and locally)

- `brainrot shoot --scene runner --seed N --frames 240 --every 40 --out shots/`
  renders exact frames of exact runs to PNG. This is how all art direction
  was done: render, look, adjust, repeat.
- `python assets/build.py [name]` rebuilds committed .glb files from their
  scripts, one subprocess per asset. It needs a working `bpy` and finds one of
  two ways: the **wheel**, imported by the venv's own Python, or a
  **standalone Blender** driven as `blender -b -P script`. The wheel trails
  Python releases and there is none for 3.14, which is what the venv is — so
  on this machine it is the standalone, unpacked at
  `~/.local/share/blender/5.0.1/`. `python assets/build.py --where` says which
  it would use and prints the install recipe when there is neither;
  `BRAINROT_BLENDER` forces a particular binary.

  Verified 2026-08-11: a full rebuild of all sixteen assets through that path
  reproduces every recorded bound and every recorded pose frame exactly — the
  24 checks in `tests/test_assets.py` pass against the *committed*
  `metrics.json` without re-measuring, and the whole suite stays green on the
  rebuilt files. Nine of the sixteen .glb files differ in bytes afterwards;
  that is bake noise and nothing else, which is what "byte-for-byte-
  equivalent" in `docs/ARCHITECTURE.md` has always meant.

  **Always follow a rebuild with `python assets/measure.py`.**
- `python assets/preview.py <asset>` and
  `python assets/animstrip.py character run` render assets/clips for review.
  `preview.py` works on this machine as of 2026-08-12 -- it used to come back
  black and colour-inverted, see the landmine below.
- `python tools/runner_probe.py --runs 12 --seconds 120` is the runner
  scene's acceptance test in numbers, and the only way "it feels boring" was
  ever going to be actionable. Three sections: **safety** (obstacles inside
  each other, the body inside an obstacle, plans with no answer), **pacing**
  (how often the runner is forced to act, the distribution of the idle
  stretches between those moments, the obstacle mix, the set-piece mix, and
  the speed at 0/15/30/60 s), and **riding** (mounts and seconds on a roof per
  minute, and "surface pops" — a body teleported upward by a surface, which is
  what a badly built ramp looks like). `--safety-runs 60 --safety-seconds 180`
  is the full sweep the collision model is held to.
- `python tools/tower_probe.py --runs 16 --blocks 340` is the hand-built
  tower's acceptance test *for the design*: every authored jump checked against
  the physics on paper (`--design-only` needs nothing built and is instant),
  then how much of the design survived being placed, per level and per beat.
  Run it after touching a level. A beat under 98% is a design to look at.
- `python tools/spiral_probe.py --plan tower ...` is the same probe's *safety*
  half pointed at the hand-built tower. The two towers are the same building
  and the same physics, so every number means the same thing for both and the
  hand-built one is held to what the generated one reached.
- `python tools/spiral_probe.py --runs 24 --blocks 280 --motion-runs 6
  --seconds 35 --walk-runs 6` is the spiral scene's acceptance test in numbers,
  and it is self-contained -- it imports nothing from another probe. Four
  sections: **walkability** (the one this rebuild exists for -- a walker let
  loose on the *cone alone*, no course blocks, no pedestals, no dressing, that
  may step one block up and drop any survivable distance; anything but 0 m
  means the levels are not levels), **safety** (cells claimed twice, landings
  off the lattice, ladders and water inside rock, emergency placements, and
  whether the body is ever inside the world), **the course** (how many landings
  are the level's own ground or something built down to it rather than a cube
  hung over the drop, plus the move mix, the feature mix, the themes seen, and
  the hop distribution and its ramp), and **the climb and pacing** (metres a
  second gained, revolutions a minute, seconds on one theme, the idle between
  moves, dead air, frozen frames, and how much of the lens is clear ahead).
  `--no-motion` needs no window at all, because `scenes/spiralplan.py` imports
  no renderer -- and neither does the walk, so both are seconds.
- `python tools/parkour_probe.py --runs 24 --motion-runs 12` is the parkour
  scene's acceptance test in numbers: interpenetration, grid alignment,
  emergency hops, the hop distribution and its ramp, and whether the body ever
  ends up inside a block. Currently: **0 overlapping pairs, 0 emergency hops,
  100% on the grid, 0% frozen frames, body worst case 0.042 m.**
- `python tools/depth_probe.py` says what each translucent draw is hiding, by
  re-rendering the frame with that one draw's depth writing turned off and
  counting the pixels that change -- and again against a silhouette of the
  course alone, which is the number that matters. Everything reads 0 now.
  `--legacy` reconstructs the pre-fix draw order in the same process, which is
  where the before numbers come from.
- `python tools/frame_cost.py` times each scene in one process with vsync off
  and reports the ratio between them. Absolute milliseconds off a busy machine
  are worthless; that ratio is not.
- `python tools/atlas_sheet.py out.png` shows every block pattern at texel
  scale *and* at block scale. Judging a texture at 8x is how the first set
  ended up as four enormous bricks and a chequerboard.
- `python tools/contact_sheet.py <shots dir> sheet.png` tiles a whole run into
  one image. A single frame can be flattering by accident; what needs judging
  is whether the course stays in shot from hop to hop.
- On a machine without a display or GPU:
  `pip install raylib-software --force-reinstall --no-deps` swaps in the
  software rasteriser (CI uses this; colours/output match the GPU build).

## Landmines that cost hours — do not relearn these

- **A cell's `y` is its floor, its `x` and `z` are its centre.** Everything
  that reasons about standing on a block (`surface = y + 1`) depends on it, and
  a cube mesh centred on `y` instead draws a whole building half a block below
  the world it collides with. `engine/chunk.py` adds the +0.5 explicitly.
- **A mesh raylib will free must be allocated by raylib.** `UnloadMesh` calls
  `RL_FREE` on `mesh.vertices`; hand it a cffi buffer and the process dies
  inside libc. `chunk.py` `MemAlloc`s and memmoves; `voxel.py` takes the other
  way out and never unloads its one shared cube.
- **Checking is not reserving.** Head-room is checked when a block is placed;
  nothing stopped a *later* block, or a support post from a landing twenty
  blocks on, being built in it. On a course that comes back over itself that is
  routine, and the symptom is the body running with masonry through its head.
  See the spiral's four reservations above.
- **A texture pattern that ignores `face` was still being computed six times.**
  `_cobble_face` and `_ao_table` are cached per salt and per process; before
  them one cobble strip cost 34 ms, and the spiral bakes fifty-odd materials at
  scene construction. Also: `Image.load()[x, y] = tuple` is about two
  microseconds a texel -- that one call was 280 ms of a 315 ms build.
- **Pose-bone axes**: down-pointing bones swing SIDEWAYS on local x. All pose
  code must go through `swing()`/`lift()`/`world_axis_q()` in
  `assets/src/common.py`, which key world-space intentions.
- **Vertex colours are banned in assets**: the software rasteriser ignores
  material colour and tint when a colour attribute exists; export strips them.
- **`ClearBackground` every frame**: it also clears depth; skipping it because
  "the sky covers everything" makes every frame after the first invisible.
- **Texture lifecycle**: scene textures are evicted when the next scene is
  built (`scene_api.build`), and `assets.unload_all` must unload embedded glTF
  textures itself. Both exist because texture slots leak otherwise.
- **raylib maps glTF material i to slot i+1** (slot 0 is its default). Zone
  names come from the GLB JSON chunk; see `src/brainrot/assets/__init__.py`.
- **bpy imports once per process**: asset builds run one subprocess each.
- **Capture correction is measured, not assumed.** Which rasteriser is
  underneath decides whether captures come back flipped and BGR-swapped, and
  `os.name` cannot answer that question — assuming it wrote every `shoot`
  frame upside down on Windows for the entire life of the branch.
  `engine/rl.py:_capture_fix` draws marker frames and reads back where they
  landed. Never read the screen directly.
- **Read-back is one buffer swap behind the draw** on the GPU build here, so
  the probe above draws its marker *until the read is decisive* and runs at
  window creation. A single marker frame read back the previous frame — a blue
  sky, in which blue beats red — concluded the channels were swapped, and every
  `shoot` PNG came out with an orange sky and a brown ocean. Anything that
  wants to capture a frame must present it twice.
- **That landmine was live in a *second* copy of the capture path** until
  2026-08-12. `assets/preview.py` had its own, and it flipped vertically and
  swapped red for blue unconditionally -- right for the software rasteriser,
  wrong for a GPU build, so brown assets came back dark blue and the grid was
  above the model. It also came back solid black, because on a Wayland session
  GLFW opens a Wayland surface and `LoadImageFromScreen` reads nothing off one.
  Both fixed the same way any capture path must be: call
  `brainrot.overlay.x11.prepare()` before `InitWindow`, and go through
  `engine/rl.save_frame`, which *measures* the correction rather than assuming
  it. If another script grows a capture path, it gets these two lines or it
  lies to you.
- **rlgl batches some draws and issues others immediately.** `DrawPlane` goes
  into the render batch and is not submitted until `EndMode3D`; `DrawModelEx`
  draws at once. So a ground plane drawn first is drawn *last* and loses the
  depth test to everything above it. Opaque models hide this; transparent ones
  do not — it punched cloud-shaped holes in the parkour sea. Call `rl.flush()`
  after any batched draw whose order matters.
- **Shared block models must be left as they were found.** The parkour kit is
  built from the same `voxel` models the course is, so a `model.transform` left
  behind by the held item tilts every block of that material in the world on
  the next frame.
- **GLFW window calls block off-thread.** On the GPU build under Windows,
  `SetWindowSize` and friends post to the thread that owns the window and wait
  for it to pump messages. Calling one from a worker thread deadlocks — which
  is why `HeadlessWindow.create` skips a resize to the size it already is.
- **An owned window dies with its owner.** The overlay is owned by the Claude
  Code host window for z-order, and `DestroyWindow` on an owner destroys what
  it owns. The daemon therefore detaches whenever it goes idle. In tests,
  destroy the fake host *after* detaching or it takes the shared raylib window
  with it.
- **Two daemons used to bind the same port quite happily.** UDP with
  `SO_REUSEADDR` did not refuse the second bind; the datagrams then went to
  one of them only -- the first showed the strip on a prompt, the second took
  the `Stop`, and the first left a scene on screen for the rest of the day.
  Every symptom of that reads as a bug in the overlay, and it cost an
  afternoon twice. Fixed 2026-08-09 by dropping `SO_REUSEADDR`: the second
  daemon now refuses to start. UDP has no `TIME_WAIT`, so nothing was bought
  by allowing it. `brainrot doctor`'s `instances` line counts *processes* on
  Linux rather than windows -- an idle duplicate has no window and is
  invisible to a window count right up until it steals an event. Worse, a Store
  Python's `CommandLine` is not readable through WMI, so
  `Where-Object CommandLine -like '*brainrot*'` matches **nothing** and a kill
  that reports no error can have killed no one. Count the windows instead:
  `brainrot doctor` has an `instances` check that does exactly that.
- **A Microsoft Store Python cannot see `%APPDATA%`.** The whole subtree is
  redirected into `…\Local\Packages\<pkg>\LocalCache\Roaming\`, for *reads as
  well as writes*: `(state_dir()/"config.toml").exists()` is False for the
  file you are looking at in Explorer. The owner's `hotkey` setting had never
  once been read. There are several such copies here — the Claude desktop app
  is a packaged app too, so anything it launches gets its own. `Config.load`
  swallows the miss (`except OSError: raw = {}`) and every value silently
  reverts to a default that looks plausible. `brainrot doctor`'s `config`
  check prints the path that is genuinely being read; trust that, not the
  path printed next to "state dir".
- **Showing the window through raylib steals the keyboard.** `set_visible`
  must go through `win32.set_window_shown` (`SW_SHOWNA`), never
  `FLAG_WINDOW_HIDDEN`: raylib unhides via `glfwShowWindow`, GLFW's
  `GLFW_FOCUS_ON_SHOW` defaults on, and `WS_EX_NOACTIVATE` does **not** stop
  it. Measured with `GetGUIThreadInfo`: strip visible at 1.62s, foreground at
  1.64s, *keyboard focus* at 1.69s. Anyone mid-sentence lost the rest of it.
- **That one only reproduces when the owner is in another process**, and it
  cost the fix a whole round trip. A harness whose fake host was a window in
  its own process showed no theft at all, twice, and was believed over the
  live daemon; the correct fix was reverted on the strength of it. If a
  reproduction disagrees with the running system, the reproduction is wrong
  until proven otherwise. `/tmp`-style scratch harness that *does* reproduce
  it: run the real `Overlay` in-process with an `OverlayWindow` subclass that
  checks `foreground_root()` after each window call, and pass it the handle
  of a real window belonging to some other application.
- **A session whose `Stop` never arrives used to think forever**, and the
  strip stayed up with it. The transport cannot promise delivery, and "the
  next event corrects it" is no correction when there is no next event for
  that session. `max_thinking_seconds` (default 900) gives up on one that has
  said nothing for that long; any event from it refreshes the clock.
- **A leaked daemon looks exactly like a window bug.** The same investigation
  first blamed the show path for a 10Hz flap that was really three daemons
  fighting. Check `brainrot doctor`'s `instances` line before theorising.
- **A blend mode does not stop a draw writing depth**, and the symptom is
  *missing geometry* with nothing pointing at what removed it. Additive glows
  stamped their whole quad -- soft, mostly transparent, and at alpha 0 for an
  orb right at the lens -- into the depth buffer, deleting every block drawn
  after them and further away. Measured at up to 1,678 px of the frame for the
  lanterns and **25,589 px (8%) for the landing dust burst**, which nobody had
  suspected. Everything emissive now goes through `fx.no_depth_write` /
  `fx.emissive`, and parkour queues its glows and issues them in one pass after
  all the opaque geometry -- depth writing off is not enough on its own,
  because a glow drawn between two blocks is still *composited* between them.
  Both flushes inside those context managers are load-bearing in opposite
  directions: rlgl issues batched draws late, the depth mask changes at once.
  Audited the whole class with `tools/depth_probe.py`: glows, bursts, cloud
  shelves and reef discs were all guilty and are all fixed; the haze band is 2D
  and writes no depth; islands are solid land and *must* write depth, and
  cannot reach the course anyway because everything in the world below tops out
  at least 7 m under the lowest altitude the course may use (now a test).
- **A head-hitter sits at *three* above the take-off, not the genre's two.**
  The `2bc` -- a lid two blocks over the floor that the head strikes, killing
  the rise and keeping the run -- is the most-used obstacle in serious
  Minecraft parkour, and this motion model cannot have one. A body is 1.8 m
  tall and a jump reaches 1.25, so its head sweeps the two cells above *every*
  take-off: a lid at two is a lid inside the player, and the arc's clearance
  test then correctly refuses every jump under it. At three it is honest and
  mild -- it refuses the arcs that climb hardest and passes the flat and
  descending ones. Making it faithful means adding the game's jump-cancel
  response to `parkourkit`, which does not exist and is a change to the
  physics, not to `spiralplan._ceiling_cells`.
- **A booked action can only fire on a frame boundary.** The planner solves a
  take-off window in continuous time and the loop fires it on the next frame,
  so the body always leaves the ground a little late — and near the ends of an
  arc the feet move most of a third of a metre in one frame at top speed,
  against a nine-centimetre clearance margin. `solve_jump`/`solve_roll` take a
  `late` argument for exactly this and the scene passes it the real `dt`. The
  margin cannot be asked to absorb it: inflating the required height instead
  makes the window vanish entirely.
- **The reflex is a last resort, not a competitor.** It fires at the *edge* of
  a take-off window; the planner books the middle of one. Letting it fire when
  a take-off was already booked replaced a good jump with a marginal one, and
  the feet came down three millimetres inside the hurdle it had cleared.
- **Gantries are only scenery if a *jumping* body clears them.** The height
  was typed in, and the test that guarded it asked for half a metre over a
  standing runner — against an apex of over a metre and a half. `GANTRY_Y` is
  derived from the apex now, and typing it in is no longer possible.
- **`id()` is reused.** A probe that counts live entities by identity
  undercounts by an order of magnitude, because a retired entity's id is
  handed straight back to the next one. The scene counts spawns itself
  (`RunnerScene.spawned`).
- **Blender exits 0 when the script raises.** `blender -b -P thing.py` reports
  success for a build that built nothing, which for a build script is the one
  unforgivable failure mode. `--python-exit-code 1` fixes it and
  `assets/build.py` always passes it — along with `--factory-startup`, so a
  stray add-on or preference cannot change what comes out of a bake.
- **Numbers the gameplay depends on live in `metrics.json`.** Rebuild an asset
  and you must re-run `python assets/measure.py`; `tests/test_assets.py` fails
  if they drift apart. Moving a hoarding's beam moves whether a slide fits
  under it.
- **An asset name is a filename, and a clash is silent.** The spiral's
  Minecraft fence is called `mcfence` because `props.py` already exports the
  runner's trackside `fence`; building it as `fence` replaces that one with no
  error anywhere. Check the names in `src/brainrot/assets/data/` before adding
  a builder.
- **`vinehang`, `dripstone` and `chain` have their origin at the *top*** and
  hang downward (`spiralplan.HANGING`). Dropped on a floor cell like every other
  prop they are underneath it, which looks exactly like a prop that failed to
  load.

## Conventions

- Every generated thing draws from `seed.stream("label")` substreams; same
  seed must replay pixel-identically (tests assert this).
- Scenes never touch windowing/hooks/config. Solvability is by construction,
  never by rejection sampling; invariants live in `tests/test_generation.py`
  and, for the spiral, `tests/test_spiral.py` (42 of them, including that
  nothing can walk up the tower without touching the parkour).
- `GENERATION_EPOCH` in `rng.py` re-rolls all seeds after big generation
  changes; bump it rather than fighting stale-looking runs.
- Run `python -m pytest tests/` before committing; it is fast (~150s). **621
  passed, 34 skipped.** The Win32 suite skips off Windows and the X11 suite
  skips without a display, so a green run means less on the other platform's
  machine -- check the count.
- `brainrot doctor` is the per-machine check and knows about both platforms;
  `brainrot extension status` reports on the gnome-shell half alone.
- Art direction is done by looking at `brainrot shoot` output. That only works
  if the capture is honest, so there are tests on the capture itself: colours
  survive, the frame is the right way up, and drawing the same state twice
  draws the same picture (`draw()` must not advance anything).
