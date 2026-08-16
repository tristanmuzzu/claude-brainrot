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
renderer against a *hand-built* course of thirty-three designed levels. `tower`
is what the default rotation plays. Both have their own sections below. (The
old ring tower and platform-stack spiral were earlier, deleted attempts at the
same format with the reference wrong; nothing of them survives, and the current
`tower_probe.py` / `test_tower.py` are new files about the new scene, not
resurrections.)

**Now verified on real Windows hardware with a GPU**, which turned up several
things the software-rasteriser cloud sessions could not have seen — see
"Landmines" below. 641 passed, 34 skipped, including a Win32 suite that
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

## The hand-built tower: `tower` (rebuilt 2026-08-12, second pass)

**The scene the rotation plays**, rebuilt the same day it was first built,
because the owner looked at the 24-level version and said what the probes
could not: the parkour read as unnecessary (blocks on a walkable plaza),
nothing was ever interior, no level had a landmark, and the camera did not
look where it jumped. All four were true. The rebuild started from frame-level
research of the real maps -- Parkour Spiral 1 and 3 walkthroughs plus the
speedrun, 130-odd frames sampled and read -- and `docs/TOWER.md` is now the
design doc that carries what the reference actually does, the acceptance
criteria (frame criteria F1-F6 judged from contact sheets, probe criteria
P1-P6), the 33-level roster, and the measured table. Read it before touching
any of this.

The design as data moved to **`scenes/handlevels.py`** (33 levels, ~345
authored landings); `handplan.py` is the machinery that reads it. What the
engine grew, each verified by render + probe the day it was written:

- **Terrace profiles**: `ledge` (default -- shelf against the core, drop
  outboard, apron swell for the landmark), `plaza`, `channel`. Paint and
  collision decide by the same per-cell test, or the course grows invisible
  walls.
- **Shells**: `shell=tunnel|hall|cave|shaft` on any beat builds an interior
  around the move at commit, through `write()`, whose refusal of reserved
  cells cuts the doorways for free. The shaft tube stops a course below the
  climb's top -- sealed to the top it walls off an exit that has no reserved
  path yet, and the stuck rate doubles (measured 0.41% -> 0.22%).
- **A weathered face**: `Cone.core_r` -- monotone-in-height overhang, so no
  cell of the cliff ever has air above it and nothing can stand on the face.
  The first draft used rock noise and the walkability probe caught it making
  one-block stairs at the level seams. Plus soffit teeth, dark cliff
  materials, and cloud shelves that keep out of the tower's radius (one
  drifting through a terrace reads as a rendering fault).
- **Landmarks**: 14 cell blueprints (windmill, watchtower, tree, bell, crane,
  totem, comb, great cap, hoard, wool stripes, cabin, hoodoo, arch, amethyst
  cluster) **reserved** the moment a section enters the horizon -- laid out
  at the apron from a per-level stream, held against placement, arcs,
  shells, pours and dressing, and merely redeemed at paint time. Accent
  cells may be dropped alone, base cells move the whole structure.
- **The camera locks onto the landing** through take-off and flight
  (`_look`'s `lock` ramp); the corridor-tangent blend only steers early in a
  run. This was the owner's "not looking where it jumps", and it was real.
- **The quarry descends the outside of the tower** -- signed `step_y` hops
  onto floating benches below the rim, the longest jumps in the tower
  (7.55 m max) with the sea under them. A dug pit is not expressible:
  terrain would have to be carved ahead of placement, and the chasm guard
  rightly refuses landings below the far floor.
- **Webs draw as crossed gauze sheets** (salted yaw per cell), never cubes:
  the body wades *through* a web, and a translucent cube from inside is a
  whole lens of speckle. Same fix in `_draw_course` for web-form landings
  and the soft-cell path.
- Eight new themes (honey, coral, gold, library, prismarine, snow, crimson,
  quartz) and nine materials; `Level.exit_beats` lets a level author its way
  out with the generated climb as fallback (mechanism live and tested, no
  level uses it yet).

Two features are **machinery inserted between script beats**, both tied to a
world feature, both leaving the cursor untouched, and the pattern is the same
one twice (`handplan.MACHINERY` names them, and they are kept out of the
fidelity numbers because they are aimed rather than authored):

- **Locks** (2026-08-12). Every level's first floor break is 5.5-6.7 wide --
  unjumpable -- and `Course._lock_nodes` crosses it: approach at height, an
  island floated over the hole, a landing on the far ground. Measured with
  `tools/bypass_probe.py`, which walks the *built world* rather than the cone
  alone: **47% of a level covered without a jump, 0 of 42 levels walkable end
  to end**, against the real map's exactly-comparable 46% and 0 of 43.
- **Gated landmarks** (2026-08-12, this pass). Twelve of the fourteen
  structures have a bigger variant carrying a held-open passage
  (`spiralplan.GATED`), and `Course._landmark_nodes` steers the course
  through it. See below.

Measured (full table in `docs/TOWER.md`): design 100% legal on paper,
**93.5% placed as authored** over the design alone, unchecked **0.31%**,
twice-claimed 0, walkability 0 m, body inside the world 0.00%, 634 tests +
34 skips green, **frames mostly filled by a wall 1.8%** (down from 2.8%).
The one criterion missed is the frame budget: **3.74 ms** against parkour's
2.44 in the same process (ratio 1.53, against 1.30 with the gates switched
off in the same process), where the criteria ask for 3.5. The gated
structures are three to four times the cells of the ones they replace, and
the cheap way back is fewer cells per blueprint -- hollow interiors, ring
eaves -- rather than fewer gates.

## The course runs *through* the landmarks (2026-08-12)

The owner watched five minutes of live strip and remembered **one**
structure, against a 97% placement rate. `tools/landmark_probe.py` is the
number that says why -- a real run, frame by frame, through the real camera
-- and it agreed with him: only **18%** of the levels that stood a landmark
up ever held it at 25 degrees, unoccluded and in frame, for a second and a
half, and **none** ever reached 40. Placement rate was never the question,
and this is the standing lesson: *a metric that measures the thing you can
build rather than the thing the viewer sees will read green forever.*

So twelve of the fourteen blueprints have a bigger **gated** variant
(`spiralplan.GATED`) carrying a passage that is held open from the moment
the level enters the horizon, and `handplan.Course._landmark_nodes` steers
the course through it exactly as `_lock_nodes` steers it across a break.
Same worlds, gates off vs on: **20% -> 52%** of levels at 25 degrees, **0%
-> 29%** at 40, **1.00 -> 2.75** structures a minute, for +0.05 points of
unchecked placement and one point of fidelity.

What had to be true, and none of it was guessable:

- **A doorway is walked through, not jumped through.** One jump impulse
  always rises 1.25 m, so the head sweeps three cells above the take-off:
  an arc under a lintel low enough to read as a doorway is refused, every
  time. Interiors are `walk` gates (three cells of clearance, crossed at a
  run); arches, bell frames, canopies and the hole in the loom wall are
  `hop` gates, five cells high.
- **A passage is three cells wide or it is a graze.** A body is 0.6 m across
  and straddles the next cell whenever it is not dead centre, and on a
  circle the diagonal step is the normal case.
- **The landings are cells, computed with the structure and stored.** The
  same arithmetic re-run later against a bearing that has moved on misses
  its own doorway by the cell it drifted.
- **But the crossing's real work is handing the passage over, not aiming
  it.** Six runs: 41 crossings offered, **18 landed inside the structure, 4
  of them on the exact stored cell**. The leg onto the first stored cell is
  an ordinary jump from wherever the approach finished and is refused about
  half the time; what works every time is that the offer takes the doorway
  out of the hold while the frontier is beside it, leaving it the only
  clear ground on the lane. **Retrying a refused offer makes it worse** --
  `_last_resort`'s recovery hop is three to five blocks in whatever
  direction will take one, so the second attempt aims behind itself
  (measured: retirements 18 -> 65, unchecked 0.34% -> 0.60%).
- **Two inserted features cannot share ground.** The lock lays seventeen
  blocks in one decision and was walking the frontier straight past
  doorways. Breaks on a gate-capable level are now kept nine blocks clear
  *and on the far side of the apron*, the lock defers to a nearer doorway,
  and script beats are clipped short of one. This is the owner's rule --
  when they collide, move the lock -- and `floor_breaks` is where a lock
  moves.
- **A gate the course never reaches must come down.** Holding the big
  structures without crossing them measured **1.96%** unchecked against
  0.30%; crossing them, 0.77%; retiring the missed ones and standing the
  small landmark ahead of the body instead, **0.31%**. A gate is a good
  trade only while the crossing is still to come.
- **Do not gate only the wide levels.** Refusing narrow ones (band under
  8.5, shelf under four) measured *worse on both counts* -- 0.56% against
  0.47%, and two fewer structures seen -- because the fallback there is a
  hold on the apron with the course squeezing past. The one exception is
  `cluster`, whose two levels are the deep-dark pair, and it is out.
- **Fidelity is counted over the design alone now** (`handplan.MACHINERY`).
  The climb, the recoveries, the lock and the crossing are aimed at world
  features, not written down landing by landing; with them inside the
  numerator the same runs read 88% and nothing was wrong.

Two hard-won harness facts. `tools/level_shot.py --level N --sheet` renders
one level without waiting for the tower to reach it -- and it must patch
`sp.Cone.__init__` (the base class), never `hp.Cone.__init__`, because
handplan's own `__init__` draws the phase from the rng before delegating,
and skipping that draw silently renders a *different world* from the one a
normal run of the same seed builds. And the fidelity probe's per-beat table
is the design feedback loop: every table row under 98% traced to a real
authoring mistake, and half of them were at beat boundaries -- including the
one class nobody looks for, the filler loop's last-landing-to-first seam.

## Levels 1-20, rebuilt against measured research (2026-08-13)

The design as data is now **one module per level** in
`src/brainrot/scenes/levels/`; `handlevels.py` re-exports it. Two documents
sit under `docs/TOWER.md` and are read first when the job is a level rather
than the tower: **`docs/RULES.md`**, the constitution a level must satisfy,
and **`docs/RESEARCH.md`**, what the real map and its footage measure as.
`docs/reference/` holds the material -- 182 frames, the contact sheets, the
checkpoint and palette data -- and `tools/mapdig/` the parsers that read the
world save.

**Three things `docs/TOWER.md` believed did not survive being measured**, and
each had been load-bearing for a rebuild. The reference does *not* alternate
interior and exposed (fully enclosed 6.1% of the way; what it always is, is a
**groove** -- a wall within 4 m on one side 71% of the time and a rock lid a
median 8 blocks overhead on 98% of samples). It does *not* put a landmark on
each level (median biggest mass on a real terrace: 12 cells, 4 blocks tall);
**identity comes from the floor**, a median 14 materials with the dominant one
at 26%, against our two or three. And its levels are *not* monotonic climbs --
36 of 43 descend somewhere and 22 dip below their own start, travelling 11
blocks vertically to gain 4, by falling off edges rather than jumping down.
Also: two of the three reference videos are **Parkour Volcano, not Parkour
Spiral**, so TOWER.md's frame-level section has the wrong provenance.

**And the exotic-physics premise was wrong in the other direction.** Across
~2,900 s of footage there is no slime, honey, soul sand, bubble column or
waded cobweb; cobweb appears **zero** times in the entire Spiral save. Lava
and water are the mechanic (26 and 20 of 43 levels), slime is one 2x2 pad per
level, and the one special block the reference leans on hard is the
**ladder**. A hop-heavy tower is *matching* the reference, not falling short.

`tools/level_review.py --level N --all` is the per-level tool: the game camera
over the level and into the next, a **blueprint** (elevation and plan of the
built world, the only view that shows ground running unbroken past your
jumps), a Blender orthographic three-view, and that level's numbers.
`tools/roster_sheet.py` tiles one frame per level, which is how "do the levels
look like different places" gets answered. **One level per process** -- the
phase pin is a class patch and the tool refuses a second.

**The pin skewed three metrics before this was noticed**, and the pattern is
worth knowing: a pinned run *opens* on the level a fifth of the way along it,
so walkability read 0% where the walker simply had nowhere to seed, a
structure was measured from beside it rather than from the run-up (0.6 s
against a true 1.5), and fidelity read 88% where the tests read 100%. All
three now run unpinned in their own process; the pin belongs to the camera.

Measured after the rebuild: placed as authored **94.7%**, designed content
42%, exit climb 37%, unchecked 0.35%, twice-claimed 0, cone-alone walkability
0 m, **0 of 52 levels walkable end to end** (real map 0 of 43), non-hop share
**6% -> 14.3%**, dead air 0.0%, seconds on one theme 10.7-13.0 (reference
10-15), **frame empty 43-77% -> 44-56%**, and **2.65 ms/frame against the 3.5
the criteria ask for** -- the one criterion the previous pass missed, met
without optimising anything. 634 tests pass.

**The generated exit ladder used to essentially never fire**, because
`_ascent_climb` wrote its column at `pedestal=False` and a climb anchors on
solid rock within one cell of the column at its middle index and at its top,
which the core's lean never reaches. That is fixed (`pedestal=True`, and the
note beside it records the measurement: 1 anchored column in 1,559 without a
pedestal). Two things about it were still recorded here long after they stopped
being true, and both mattered:

- **All thirty-three levels write `exit_beats`.** The exit is designed, not
  generated. `_ascent_climb` is now dead code in the tower and lives on only in
  the generated `spiral`.
- **Nobody could tell, because the label cannot say.** Every landing of the
  climb is labelled `ascent` whether a level wrote it or the engine improvised
  it, and that label is load-bearing in eight other places -- so a third of the
  course sat outside every fidelity number the project had. Nodes carry
  `origin` now, blocks keep it, and `tower_probe` prints **THE WAY OUT**.

## What the exit climb is made of (first measured 2026-08-14)

It is 29% of the course, and:

| | |
|---|---|
| the level wrote it | **60%**, of which **98.5%** placed as authored |
| the crossing | 23% |
| a generated staircase finishing a climb the design did not top out | 17% |
| the reliability chain (`_climb_on`, `_grab_the_wall`) | **0** -- it never fires |

Two engine faults were hiding under the label and both put a staircase where a
level had written an exit. **One refused landing threw the whole authored exit
away** -- the recovery went straight to `_ascent_stair` from the first refusal,
which alone was ECHO SHAFT and WINDMILL REACH losing twenty-four landings a
sweep each; the rest of the design is tried first now. And **an authored exit
climbs a fixed height while `need` is not fixed** -- it is the next level's
floor minus wherever the level's own beats left the body, so six treads against
a need of three climb three blocks past the thing being climbed to, and the
crossing, offered from too high, is refused and re-plans as a staircase.
`_drop_climbed_treads` stops an authored climb one block above the next floor,
which is where the crossing wants to launch from because it descends by design.

Together: exit landings 894 -> 867 a sweep, generated staircase 177 -> 141,
authored exits placed as authored 98.1% -> 98.6%. What is left is per-level
authoring, and the reject table names a different cause for each: WINDMILL
REACH `no move: hop`, WART FIELDS `landing occupied`, THE WHITE STAIR
`pedestal will not stand`, THE QUARRY `no move: bubble`, MARKET STREET
`no move: climb`.

## The course flies over its terrace (rebuilt 2026-08-16)

**The owner's third and sharpest complaint about the tower's parkour**, and
the one that changed the format: the jumps went from a block resting on the
floor to another block resting on the floor -- "they're attached to the floor,
but the player keeps jumping from one to the next" -- so missing one cost
nothing. His own criterion, and it is better than "put it over the void":

> if you fall, you should theoretically have to go back to the beginning of
> that level to attempt the parkour again, and there should not be any point
> in the level where you go down to a ground block and from there go up again.

That is a **reachability** question, not a void question, and `docs/REHASH.md`
is the whole record: the plan, what was built, what it measured, and the four
things the probe itself had to get right before its number meant anything.
`tools/reentry_probe.py` is the number. **87.9% of missed jumps walked back
into the middle of the course; it is **1 in 8,484** now, on one level visit
in eighty-five.**

The shape, in one paragraph. A level is entered on its terrace, steps up off
it once, and everything after that stands **at least two blocks over the
ground** -- a body steps up one, so anything at one is a landing a fall walks
back onto. The terrace is untouched, fully themed and fully dressed: it is the
place the course flies over and the place a fall lands, and it is a dead end
because the course left it at landing one. Falls therefore do not need void
under them, which is what keeps the levels looking like places.

Five numbers moved with it, and two of them are the *other* complaints this
tower has had:

| | before | after |
|---|---|---|
| missed jumps that re-enter the course | 87.9% | **1 in 8,484** |
| landings resting on the terrace | 15.9 a level | **2.4 a level** |
| a level walked end to end without jumping | 2 of 24 | **0 of 55** (34% mean) |
| landmarks framed at 25 / 40 degrees | 55% / 30% | **68% / 63%** |
| unchecked emergency placements | 0.31% | **0.41%** |

**`Level.deck` is the new number every part of the machinery aims at**: how
high over its own terrace a level's course cruises, computed in
`levels/_base.py` from where the script and the filler leave the body. The
exit climbs `rise + 1 - deck` and nothing more; a gated landmark stands on a
plinth that tall; the design checker knows what the filler has to come back
to. `tools/level_climb.py` prints it for one level or the whole roster and is
the reading tool for all of this.

Seven engine changes, each found by measuring and not one by reading the code
(`docs/REHASH.md` section 5 has the full list and the numbers):

- **pedestals are off by default on this tower** -- a stack down to the ground
  is a staircase back up to the landing it holds;
- **a fallback height may go up and never under the deck** -- `spread` was
  quietly placing an authored landing three blocks up at one block up, and
  that was the largest single source of re-entry after the designs;
- **machinery keeps the body's height** (`_here_lift`, floored at two): the
  lock's approach, the doorway's approach, every recovery hop and the one
  unchecked emergency landing all asked for `lift=1`, which on a climbing
  level is a staircase down to the terrace and back;
- **the lock is skipped while the course is flying** -- it exists to cross a
  hole in ground the body is running on, and three blocks up that hole is
  scenery;
- **a gated landmark stands on a plinth as tall as the deck**, and the plinth
  stops short of its own passage so a fall through the doorway carries on down
  rather than landing in it (4.5 points of re-entry and 1.6 of unchecked
  placement on its own);
- **`noclimb`**: nothing may be built in the ring beside a landing between the
  terrace and that landing's height. Dressing was three quarters of what was
  left once the designs were raised -- the landings were out of reach and the
  scenery beside them was a staircase;
- **the exit starts from the deck.** Eighteen levels opened theirs with an
  absolute `lift`, which on a flying course is the whole level dropping back
  down;
- **a relative chain that lost a block gets it back.** ``step_y`` is measured
  from the landing before, so one refused node in the middle of a beat leaves
  everything after it a block low -- and a block low is one block over the
  terrace, which is the whole defect. ``_targets`` nudges such a landing up to
  the deck when that is still a jump the body has. Re-entry 3.4% -> **0.6%**,
  and the levels showing any nine -> three.

**`breaks=0` is gone from the roster and that is a consequence, not a taste.**
Nineteen levels had chosen no floor breaks because any break forced the lock
and the lock cost them landings. The lock is skipped now, so breaks are free
obstacles again: everything is at three or four, and that alone took a no-jump
walker from 70% of a level to 48% and from two levels walkable end to end to
none.

**All thirty-three level modules were re-authored by a source-level `ast`
pass, not by hand and not by an agent each.** Each landing moves up by the
least that clears the deck, *preserving the deltas* -- the shape of a level is
its rises, so its arcs stay legal wherever they were legal -- and the filler is
flattened to the deck because it repeats and anything it gains it gives back at
the seam. `tower_probe --design-only` then named what broke, by level, beat and
node: 170 complaints, then 57, then none, and every one of the 57 was a real
authoring decision. Third time on this project that a mechanical AST pass plus
an instant design checker has beaten hand-editing.

**Two things on the plan turned out not to be needed**, and both are worth
knowing before anybody re-derives them. `_walk_bridge` lays its ground at the
walk's *own height*, so it is a platform rather than a ramp and creates no
re-entry. And `LIFT_MAX = 6` is exactly right rather than conservative: open
air over a level is the next three rises minus `FLOOR_T`, which the
three-window rule holds at eight or more, and a landing at lift 6 needs exactly
eight. What climbs past it is the exit, written on `step_y`, which is not
clamped.

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

00. ~~Frame cost is the one criterion the rehash lost~~ **It was the
   machine.** Five rounds while the test suite ran in the background read
   tower 3.63 ms and tower/parkour 1.78, against the recorded 1.46; nine
   rounds on a quiet machine read **tower 3.00 ms and 1.389**, which is better
   than the record and inside the 3.5 ms the criteria ask for. The world got
   *smaller*, which is the other half of the answer -- a tower run writes 5,187
   cells against 5,780 before the rehash, because the pedestals went. The
   lesson is the one already written under item 5 and it cost an hour anyway:
   **do not read `frame_cost` off a busy machine, and do not read a ratio off
   five rounds when the spread is 1.0 ms.**
0a. **One missed jump in 8,484 still walks back onto the course**, and it is
   a fall onto the lower step of the same generated staircase -- tread 21 to
   22 missed, landing on tread 20, which is under the arc because the stair
   weaves. What kills it is not a wider weave but the level topping out on its
   own, which is item 0. Everything else that used to do this was a ledge
   beside a landing: more landings at terrace
   height than the geometry needs. `python tools/reentry_probe.py --levels
   --only NAME` names them; `docs/REHASH.md` is the criterion. Trace one with
   a throwaway path-printer -- a forward walk from the fall cells with parent
   pointers, printing what each step stands on -- because all six causes found
   in this pass were invisible in the aggregate and obvious in one path.
0. **The generated staircase is 16% of the exit climb**, and what is left of
   it is per-level authoring rather than an engine change -- see "What the
   exit climb is made of" above for the decomposition and the per-level
   reject table. The loop that works is `scratchpad`-style per-tread
   instrumentation: tag each authored exit node with its index, count
   `_attempt` calls and successes per index, and read which tread stops
   landing. On WINDMILL REACH it said the first four place on every visit
   and the fifth on two of six, which is a terrace running out and is fixed
   by writing one fewer tread (mean exit climb 11.0 -> 5.5 landings).

   **But the staircase is not a tread problem at all: it is the crossing.**
   That was worth two wrong turns to find, and both are worth knowing.
   Attribution was suspected first -- the table buckets by `blk["theme"]`,
   which is the theme of wherever a landing physically *is*, and THE QUARRY's
   exit descends the outside of the tower past a revolution above THE VAULT.
   Blocks now also carry `author`, the level whose plan emitted them, and the
   two attributions **agree**: 143 staircase landings a sweep either way, and
   THE QUARRY is charged 24 by both. `author` is kept because it is the right
   thing to bucket by, not because it changed an answer.

   What the measurement actually says is that on THE QUARRY, WINDMILL REACH,
   WART FIELDS and THE WEIR the authored treads place on nearly every visit
   and the staircase still fires four to nine times in eight runs -- about
   once a visit -- and always *after* `_crossing` has been refused. So the
   generated staircase is the crossing's failure, once per level visit, and
   the lever is `_aim_crossing`.

   **And the crossing fails on distance, not on height.** Instrumented over
   eight runs: 338 crossings asked, 114 placed, the staircase fired 134 times.
   The body is at exactly the intended height on 290 of the 338 asks (+1 above
   the next floor, which is where `_drop_climbed_treads` leaves it) and on 102
   of the 134 give-ups. What it is asked to jump is the problem --
   `_aim_crossing` sets `arc = (lv.u1 - u) * radius + 1.2`, which is *the
   distance to the end of the level*, not a distance a body can cover: at
   give-up the median arc asked for is **9.9 m** and the worst is 76.6, against
   a level hop of 4.26 and 4.98 dropping one. So the crossing is arithmetically
   impossible until the body has walked most of the way to the lip, and the
   generated staircase is what walks it there. The cheap answer to try first is
   to not ask at all while the arc is beyond the physics, and to travel along
   the trough instead -- but see the dead end immediately below before writing
   the loop.

   Do **not** answer it by shortening the recovery. A body already level with
   the terrace it is jumping to gains nothing from climbing, so one
   repositioning step instead of eight looks obviously right; measured, it
   loops -- step, crossing refused, step -- and takes the exit climb from 16%
   of the course to 40% (staircase 126 -> 357 a sweep, crossings 180 -> 71).
   The full staircase at least terminates.
0b. **Half the gate-capable levels still do not get entered**, and the fix
   this file used to recommend has been tried and is **worse**. Over 8 runs:
   173 levels wanted a gate, 135 got the reservation, the offer was made on
   107, and 62 put a landing in the passage. Aiming the last approach landing
   at a cell one level hop back from the doorway halves the hop refusals
   (157 -> 77) and *reduces* passages entered, 56 -> 48, because an `at` node
   is strict, the crossing is offered once, and a launch cell that will not
   take a landing spends the offer. Pre-checking the cell for occupancy
   changes nothing -- the cells are free; what fails is the hop into them.
   Doing it properly means the reservation holding the approach cells too,
   which is a real change to `_reserve_landmark`. What *did* work is letting
   a refused stored landing fall through to the next one (56 -> 62), which is
   the same shape as the authored-exit recovery.
0c. ~~The gated structures cost 0.74 ms a frame~~ **Was met, and the rehash
   lost it again -- see item 00.** Measured 2026-08-14 with all four scenes in
   one process: parkour 1.91, tower 2.79, spiral 2.07, runner 1.83 ms/frame,
   tower/parkour 1.46. The 3.74 ms on record predates the level rebuild.
1. **A wall fills the lens on 1.8-2.9% of frames**, and the biggest cause is
   now known and fixed: bucketing every jammed frame by what the body was
   *doing* said **climb 42.0% and bubble 30.3% against hop 1.0%** -- three
   quarters of every jammed frame was a ladder or a bubble ride, because a
   climbable column has to anchor on the core and the ride is therefore the
   one move whose body is pinned against the surface it cannot see past. The
   camera now looks outward for the length of a ride (`RIDE_OUT`): jammed
   frames 3.23% -> 1.83%, climb -> 16.3%, bubble -> 15.2%. It is *not*
   enclosure -- frames with rock overhead jam at 0.9% against 4.1% for open
   ones, so a tunnel is the level working as designed. Next by rate, both
   level-specific: `basin` 16.7% of 54 frames, `sill` 8.2% of 748.
1c. **Level openings are not the problem they were recorded as.** Measured
   over 4 runs x 35 s, a level's first ninety frames are 46.2% sky against
   41.9% everywhere else -- four points, not "one or two frames of sky with a
   cube in them". What is actually empty is the exit climb (48.6% of 3,716
   frames) and three beats: `stacks` 60.2%, `gate` 55.7%, `stalls` 55.3%.
   Whole-frame emptiness is 14.9% against vanilla's 24.4%, so this axis has
   headroom rather than a deficit.
1b. **The roster still wants assets**: per-theme pours (falling lava/water
   columns past the course), the windmill's blades, a bell, coral fans, a
   scarecrow -- all `assets/src/` work, none load-bearing.
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
3. ~~`tools/depth_probe.py` does not know about the spiral or the tower.~~
   **Done.** `--scene spiral|tower` and a suspect table for that family.
   Answer: the depth guards are load-bearing and now have a number -- without
   them, up to 3,370 px (1.06%) of the course is deleted on the tower and
   7,428 px on the generated spiral. Glows, bursts, cloud shelves and the haze
   band all measure zero; props reach at most 99 px of the course. Two
   instrumentation traps are written into the tool and both read as a clean
   pass: wrapping `_draw_furniture` measures the *opaque* ladders it also
   draws, and patching `fx.no_depth_write` reaches nothing because `spiral.py`
   imports it by name.
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

   Measured 2026-08-14 with **all four** scenes in one process, which is what
   it defaults to now, and every scene is reported against the first one asked
   for rather than against `runner` by name: parkour **1.91**, tower **2.79**,
   spiral **2.07**, runner **1.83** ms/frame; tower/parkour **1.46**. The
   rebuilt spiral and the hand-built tower had never been through this harness
   at all, because the ratio table listed scenes by name and neither was in it.
   The ring tower's 1.28 ms went with that scene -- do not quote it.

   Scene *construction* is a separate cost and worth watching: the tower takes
   **1.80 s**, up from 1.53 s since `emit_layer` began gating every cell of
   skin on `rock`. That is paid once when the strip appears, and it buys the
   guarantee that nothing drawn is walk-through.

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
- `python tools/level_review.py --level N --all` is **the** per-level tool and
  the one to reach for when a level is being designed rather than the tower.
  Four artefacts in `shots/review/lNN_slug/`: the game camera over the level
  and into the next (`frames.png`, the judge); a **blueprint** — elevation and
  plan of the built world, which is the only view that shows ground running
  unbroken past three of your jumps; the level as solid geometry rendered
  orthographically in Blender (`--outside`); and the numbers for that level
  alone — per-beat fidelity, move mix, no-jump walk coverage, body inside the
  world, how much of the frame is empty sky, and how long its structure is on
  screen. `--seam` prints what the level below hands it and what the level
  above opens with. **One level per process**: the phase pin is a class-level
  patch and the tool refuses a second.
- `python tools/level_climb.py` prints what every level does *vertically* --
  the height of each authored landing over its own terrace, the deck the
  filler holds, and what the exit still has to climb (`rise + 1 - deck`).
  Instant, builds nothing, and it is the reading tool for the rehash: `low`
  under 2 on any level is a landing a fall can walk back onto. One level's
  name as an argument prints that level landing by landing.
- `python tools/tower_probe.py --runs 16 --blocks 340` is the hand-built
  tower's acceptance test *for the design*: every authored jump checked against
  the physics on paper (`--design-only` needs nothing built and is instant),
  then how much of the design survived being placed, per level and per beat.
  Run it after touching a level. A beat under 98% is a design to look at.
- `python tools/walk_probe.py --plan tower --runs 12 --blocks 240` asks whether
  a *solved* move is still legal when it is played: it walks every committed
  move against the world as it stands `AHEAD` landings later, which is where
  the body is, and asks whether anything solid is inside the body and -- on a
  leg the body is on its feet for -- whether there is ground under them.
  Nothing had ever asked the second question, and the answer was that **98% of
  walk legs crossed air** (see `Course._walk_bridge`). Check it after touching
  any verb in `_move_for`. Needs no window.
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
- `python tools/landmark_probe.py --runs 6 --seconds 40` asks whether a
  level's signature structure is ever *seen*: a real run, frame by frame,
  through the real camera, counting a structure when it holds 10/25/40
  degrees, unoccluded and in frame, for a second and a half. Placement rate
  was the number that stood in for this and it was wrong -- 97% placed, 18%
  ever framed. Currently **55% of levels at 25 degrees, 30% at 40, 2.75 a
  minute**.
- `python tools/bypass_probe.py --runs 6 --blocks 240` walks the **built
  world** -- cone, course, pedestals, terrain, shells, landmarks -- one cell
  at a time, up one, down any drop, never jumping, and reports how much of a
  level it covers. This is the walkability criterion for the hand-built
  tower; `spiral_probe`'s cone-alone walker answers a different question and
  reads as if levels were much harder to walk than they are. Currently **47%
  mean, 0 of 42 levels walkable end to end**, against the real map's 46% and
  0 of 43.
- `python tools/reentry_probe.py --runs 6 --blocks 260` is the acceptance test
  for the parkour rehash (`docs/REHASH.md`), and it is the owner's own
  criterion as a number: a body that misses a jump and then *walks* -- up one,
  down any, never jumping -- must not arrive back at any landing of that level
  but its **entry apron**. A miss is **dead** (the void, or ground connecting
  to nothing), **back to the start** (fine, and the wanted outcome), or a
  **shortcut** (the defect: the fall cost nothing and every jump before the
  re-entry point was decoration). Also floor contact -- landings resting on the
  terrace, by pedestal or directly -- the apron's own size, and what the level
  climbs. **Shortcut 87.9% before the rehash and 2.0% after, on one level of
  thirty-three.** Ten seconds, no window. `--levels [--only NAME]` is the
  per-level table to author against; `tests/test_reentry.py` holds the walker
  itself against worlds checkable by hand, and the four things it has to get
  right before its number means anything are in `docs/REHASH.md` section 6 --
  the shortest of them being that walking is not symmetric, so it searches
  backwards.
- `python tools/parkour_probe.py --runs 24 --motion-runs 12` is the parkour
  scene's acceptance test in numbers: interpenetration, grid alignment,
  emergency hops, the hop distribution and its ramp, and whether the body ever
  ends up inside a block. Currently: **0 overlapping pairs, 0 emergency hops,
  100% on the grid, 0% frozen frames, body worst case 0.042 m.**
- `python tools/depth_probe.py --scene tower` says what each translucent draw
  is hiding in the spiral family. The one that is not zero is `guards`, which
  switches `no_depth_write` off scene-wide and is this scene's answer to
  `--legacy`. Read the two instrumentation notes in the suspect table before
  adding a suspect: both of the traps they describe read as a clean pass.
- `python tools/depth_probe.py` says what each translucent draw is hiding, by
  re-rendering the frame with that one draw's depth writing turned off and
  counting the pixels that change -- and again against a silhouette of the
  course alone, which is the number that matters. Everything reads 0 now.
  `--legacy` reconstructs the pre-fix draw order in the same process, which is
  where the before numbers come from.
- `python tools/frame_cost.py` times **all four** scenes in one process with
  vsync off and reports every one against the first asked for. Absolute
  milliseconds off a busy machine are worthless; those ratios are not.
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

- **The software rasteriser is not the GPU build, and where it differs is
  exactly where this project has guards.** RLSW (raylib 6.0's software
  renderer, which is what `raylib-software` installs and what CI runs on)
  honours **neither the depth mask nor alpha blending** — so the two tests that
  hold `no_depth_write` and the rlgl batch-order fix cannot be observed on it
  and are skipped there (`conftest.software_rasteriser`, which reads the marker
  out of the loaded `.so` rather than trusting the installed distribution list:
  `raylib-software` is force-installed *over* `raylib`, so both names are
  present afterwards and only the binary says which won). "colours/output match
  the GPU build" was true of frames and is not true of depth.
- **Do not resize the shared test window, and never open a second one.** RLSW
  allocates its framebuffer at `InitWindow` and `SetWindowSize` does not
  reallocate it, so a draw at the new size runs off the end of the old buffer.
  `test_tower` did both — its own 180x320 window, then `destroy()` on it — and
  the whole suite was green here and *dead on CI on both platforms*: a
  segfault or a glibc abort about a thousand frames later, reported against
  `GetWorldToScreen` in the spiral's haze band, which has nothing to do with
  it. Every drawing test goes through `conftest.ensure_window()` at the size it
  already is. This is the general shape: **a heap-corrupting bug is reported
  wherever the heap is next touched**, so the named frame is evidence about
  timing and not about cause.

- **Two descriptions of one surface will disagree, and the disagreement is
  invisible in both directions.** `emit_layer` drew the core's flutes a cell
  proud of `core_r` and `rock` had never heard of them, so twenty-eight of the
  fifty-six ribs -- the tower's signature forest of columns -- were drawn, lit,
  fogged and walked straight through. Measured: **3.3% of body samples along a
  course were inside a cell the tower draws**, up to 0.80 m deep. The "body
  inside the world" figure cannot see this, because it asks `blocked`, which is
  `rock`, which is exactly the half that is wrong. Every cell of skin now goes
  through `Course._paint` and is placed only if `rock` agrees, and
  `tests/test_spiral.py` holds it at zero. A margin that skipped the gate well
  inside the wall leaks: `unwrap` puts a cell near a level seam in the *other*
  level, whose band is a different width, so "comfortably inside" is not a
  local question.
- **A probe that exempts what it is measuring reads zero forever.** The walk
  probe accepted a cell belonging to either landing as ground, which exempted
  precisely the cells a walk's own bridge meant to lay -- including the ones
  `write` refused. It read 0% while `tests/test_tower.py` failed. Ask the world
  the same question the body would.
- **Check a move at the moment the body reaches it, not one step later.**
  `advance` releases the ground behind the body, so a probe that walks the
  course with `<` where `<=` was meant measures every move against a world that
  has already had its floor taken away. It reads as a catastrophic air-walk and
  it is the probe's own doing. This was made twice in one session.
- **A refusal in the middle of a written sequence is not the sequence
  failing.** Both the authored exit and the gated crossing threw away
  everything after the first landing that would not go, and in both cases the
  next landing is aimed further along the same lane and usually goes. Worth
  twenty-four landings a sweep on two levels and six passages entered.
- **Vanilla's constants are not vanilla's *result*.** The face-shade table
  (top 1.0, bottom 0.5, sides 0.6/0.8) multiplies a light level skylight has
  already filled in. Copied on its own it is 60% of nothing, and this
  renderer's frames were half again as dark as the real game's -- with three
  materials hand-brightened to compensate locally before anybody checked the
  general case.

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
- Run `python -m pytest tests/` before committing; it is fast (~255s). **641
  passed, 34 skipped.** The Win32 suite skips off Windows and the X11 suite
  skips without a display, so a green run means less on the other platform's
  machine -- check the count.
  `tests/test_overlay_x11.py::test_the_states_survive_being_hidden_and_shown_again`
  has been seen to fail once in a full run and pass alone and on the next full
  run; if it fails, re-run before believing it.
- `brainrot doctor` is the per-machine check and knows about both platforms;
  `brainrot extension status` reports on the gnome-shell half alone.
- Art direction is done by looking at `brainrot shoot` output. That only works
  if the capture is honest, so there are tests on the capture itself: colours
  survive, the frame is the right way up, and drawing the same state twice
  draws the same picture (`draw()` must not advance anything).
