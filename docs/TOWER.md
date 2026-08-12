# The hand-built tower

A designed tower of thirty-three levels, climbed in order and looping,
replacing the procedurally chosen course in the `spiral` scene. The building,
the physics, the placement checks and the renderer are the ones that were
already there; what changes is **who decides what the parkour is, and what the
world around it is made of**.

This document is the design. `src/brainrot/scenes/handplan.py` is that design
as data, and the level table's comments are the per-level detail — read them
together, but read this first.

## Why the last tower failed, in frames

The 24-level tower of 2026-08-12 measured clean — 97% fidelity, 0.13%
unchecked, 0 m walkable — and looked wrong, and the owner said so. A contact
sheet of any run says why, and none of it is a number the probes watched:

1. **The ground was a plaza.** Nearly every frame was a wide flat terrace
   with knee-high boxes scattered on it. The body hopped between blocks it
   could visibly have walked around: the walker probe only proves you cannot
   climb *between* levels, and within a level the floor was right there under
   every jump. Parkour over ground you could walk on is parkour that reads as
   unnecessary — the owner's word, and the correct one.
2. **Nothing was ever interior.** The reference alternates exposed cliff
   ledge with enclosed rooms, tunnels and shafts every ten to twenty seconds.
   The old tower was one hundred per cent open corridor: no walls, no roofs,
   no lamps, no rhythm.
3. **No level had a landmark.** "Village" was plaster-coloured boxes;
   "jungle" was green ones. A place you recognise needs one thing to
   recognise — a windmill, a temple hall, a giant tree — and no level had
   anything larger than a pillar.
4. **The wall and ceiling were undressed.** The core was a smooth fluted
   cylinder and the ceiling a flat grey slab, both obviously procedural at
   one glance.
5. **The camera aimed at dirt.** The look-at is a blend of the next three
   landings pulled toward the corridor tangent, so at take-off the actual
   landing was routinely off-centre or off-frame — the owner read it as the
   character not looking where it is jumping, which is exactly what it is.

## What the reference actually does

Read off Hielke's own maps at frame level (Parkour Spiral 1 walkthrough and
speedrun, Parkour Spiral 3 walkthrough; 130-odd sampled frames, 2026-08-12):

- **The course is a shelf, not a floor.** The walking surface is two to four
  blocks wide, hugging a cliff face, with the drop directly outboard. Wide
  ground exists only where a *place* needs it — a village street, a temple
  floor — and then it is dressed as that place.
- **In/out rhythm.** Exposed ledge, then an interior (temple hall, mine
  gallery, treasure cave, library, barrel silo, ice tunnel), then exposed
  again. Interiors have two-to-three-block ceilings, walls on both sides,
  and their own light: lanterns, candles, glowstone, lava.
- **One landmark per level.** Windmill, lighthouse, beehive frame, giant
  tree, scaffolding crane, bell tower, wool loom, obsidian totem. It fills
  the frame at least once and is what you remember.
- **The cliff overhangs.** The rock face above the course leans out, ragged,
  with vines, icicles, moss and the occasional lava or water pour falling
  past the course. The tower reads as one huge weathered thing, not a stack
  of clean plates.
- **Hazards run through the floor.** Lava channels, water channels, void
  slots — cut into the course's own ground, jumped along and across, not
  parked beside it as decoration.
- **Verticality is readable.** You look down and see the level you left as a
  little diorama — the farm below the cliff you just climbed. You climb
  hollow shafts inside the tower. You descend into pits and come back out.
  Net motion is always up; *travel* is up and down.
- **Difficulty is mostly modest.** The place is the star; the hard jumps are
  punctuation. What keeps it entertaining watched rather than played is
  exposure and variety, not gap length.

## Acceptance criteria

Two kinds, and the split is the point: **frame criteria are judged by looking
at contact sheets** — they are the reason this rebuild exists and no probe
replaces them — and **probe criteria hold the old guarantees** while the world
gets more complicated.

Frame criteria, over a contact sheet of any 40-second run:

- F1. No frame in which flat terrace ground dominates the lower half with
  the course as scattered knee-high blocks on it. The footing is always a
  shelf, a structure, a pit, a channel bank or a room floor.
- F2. The run alternates: at least a quarter of frames enclosed (walls both
  sides, ceiling within three blocks), at least a third exposed (drop, sea
  or the level below visible past the course), and no stretch of more than
  ~15 s in one state.
- F3. Every level's signature structure is on screen within its first four
  seconds.
- F4. In airborne frames the next landing sits in the middle third of the
  frame at least seven times in ten.
- F5. Any single frame shows at least three materials of distinct value in
  the course zone; no level reads as one colour.
- F6. Standing frames on undressed flat wall/soffit stay as rare as they are
  now (lens metric ≤ 0.5% of frames mostly wall).

Probe criteria (`tools/tower_probe.py`, `tools/spiral_probe.py --plan tower`),
all held at or better than the 24-level tower:

- P1. Designed landings placed as authored ≥ 90% overall, no level under 80%.
- P2. Unchecked emergency placements ≤ 0.3%; cells twice-claimed 0;
  off-lattice 0; orbs missed 0.
- P3. Cone-alone walkability 0 m (the levels stay levels).
- P4. Body inside the world ≤ 0.05% of frames.
- P5. Per frame ≤ 3.5 ms in `frame_cost.py` terms (the shells and dressing
  are not free; this is the budget they must fit in).
- P6. Every authored jump legal on paper (`--design-only` clean).

## What the engine grows to say it

Six capabilities, each earned by a specific reference observation. The level
table may only name things on this list or things that already existed.

1. **Terrace profiles** (`Level.profile`). The plaza dies. A level's ground
   is one of: `ledge` (a shelf against the core, the drop genuinely
   outboard — the default; it swells into an *apron* at one bearing to hold
   the landmark), `plaza` (the old full floor, reserved for levels that
   dress it as a real place), `channel` (full floor with the theme's liquid
   cut along the course). Profiles carve what `Cone`'s section painting
   emits, with paint and collision deciding by the same per-cell test; the
   walkability guarantee is unchanged because removing floor never adds a
   walkable route. Going *down* is not a profile: the quarry descends the
   **outside** of the tower on floating benches below the rim (signed
   `step_y` hops), because a dug pit would need terrain carved ahead of
   placement and the chasm guard rightly refuses landings below the far
   floor.
2. **Shells** (beat-level `shell=`). A stretch of course can be built
   *inside* something: `tunnel` (tight walls, flat roof two to three over
   the course), `hall` (tall interior, lamp niches), `cave` (rough walls,
   uneven roof), `shaft` (a vertical tube around a climb). Painted after
   the course is laid, through the same reservation checks as pedestals, so
   a shell can never close over a jump's clearance. Shell interiors carry
   their own light so the level's `dark` flag finally has somewhere to be
   dark.
3. **A weathered face.** The core wall grows a brow — the profile is
   monotone in height by construction, only ever leaning further out as it
   rises, so no cell of the cliff ever has free air above it and nothing
   can stand on the face (the first draft used rock noise here and the
   walkability probe caught it making one-block stairs at the level seams)
   — plus bearing-keyed ridges, hanging teeth under the soffit's rim, and
   dark cliff materials in place of the old light stone brick. Per-theme
   pours (falling lava and water columns) are designed but not yet built.
4. **Landmarks** (`Level.landmark`). Data-driven blueprint stamps painted on
   the terrace through `_dressable`: windmill (with a bladed prop), watch
   tower, temple front, giant tree, bell frame, crane, arch. One per level,
   placed where the course faces it.
5. **Authored exits.** A level may write its exit beats the way it writes
   any beat — a staircase through a broken roof, a ladder inside a shaft
   shell — with the generated climb kept as the fallback it already is.
   The reliability chain (`_climb_on`, `_grab_the_wall`) is untouched.
6. **The camera looks where it jumps.** From the moment a take-off is
   booked until landing, the aim blends hard toward the actual landing
   block; the corridor-tangent blend applies only while running. This is
   F4, and it is a renderer change, not a course change.

## The tower

Same building: solid inverted cone, `base_r = 36`, flare 0.05, one-cell ribs,
three levels to a revolution. Thirty-three levels is eleven revolutions;
at six to ten seconds a level that is four to five minutes of distinct
content before anything repeats. A run still starts anywhere in the cycle,
and the tower still loops by climbing — level 33's exit lands on level 1
six blocks higher.

Rises vary 3–10 and any three consecutive rises sum to 13–20 (the ceiling
over a level is the floor slab of the level three above; the sum *is* the
head-room). Tall rises belong to the two shaft levels and the canopy; short
rises to thresholds and streets. Down happens inside levels — pits, drops
through canopy, descents into cisterns — never between them, exactly as the
reference does it.

## The roster

Thirty-three levels. Consecutive levels differ on at least three of: band,
enclosure, form, verb, constraint, rhythm, light. No theme twice in a row;
interiors never twice in a row; each third of the tower gets at least three
interiors and at least one vertical level.

| # | name | theme | the idea | encl. | landmark | rise | exit |
|---|------|-------|----------|-------|----------|------|------|
| 1 | THE GATEHOUSE | plains | hedge-walled garden path, pond, benches; the gentle open | open | gate arch | 5 | stair |
| 2 | WINDMILL REACH | farm | crop furrows as channels, hay ranks at full reach | open | windmill | 4 | hay stair |
| 3 | MARKET STREET | village | a real street: facades, stalls, awning slabs, one house crossed inside | mixed | belfry facade | 6 | ladder up a gable |
| 4 | THE TIMBERWORKS | mine | timbered gallery, rails, webs, candle light | interior | TNT crate stack | 5 | ladder in a timber cage |
| 5 | SUNKEN TEMPLE | desert | sandstone hall, lava channel down the middle, doorway lids | interior | temple front | 6 | stair through broken roof |
| 6 | THE BALCONIES | mesa | narrow terra ledges, big drops, bridge over a lava pour | open | terra bridge | 7 | rim stair |
| 7 | CANOPY WALK | jungle | giant trunk, leaf decks, vine to the upper storey, drop back through | mixed | giant tree | 7 | vine wall |
| 8 | THE CISTERN | dripstone | flooded cave, stepping stones, spikes, bubble out of the pool | interior | the well shaft | 6 | bubble in the well |
| 9 | GLACIER SHELF | ice | open slides at reach, icicle brow, crevasse pit mid-level | open | crevasse | 4 | ice stair |
| 10 | THE APIARY | honey | honeycomb frames, one slow honey beat, a slime bounce room | mixed | comb frame | 5 | scaffold |
| 11 | THE CRUCIBLE | nether | dark cavern, zigzag lava channel, glowstone points | interior | lava fall | 7 | blackstone stair |
| 12 | REEF GARDEN | coral | colour after the dark: coral fans, sea lanterns, water channel | open | brain-coral dome | 5 | prismarine stair |
| 13 | THE SILENCE | deepdark | one-cell sculk landings over void, amethyst light | open | amethyst cluster | 6 | ladder |
| 14 | THE BELFRY | village | vertical: beams and ledges up inside the bell tower | interior | the bell | 8 | ladder in the shaft |
| 15 | WOOLWORKS | rainbow | the loom: wool stripe wall, checks, slime pad; short and loud | open | stripe wall | 4 | quartz stair |
| 16 | THE VAULT | gold | treasure cave: gold, glowstone veins, a ledge over lava | interior | gold hoard | 5 | stair through the collapse |
| 17 | THE WEIR | plains | water channel the whole way, stones barely above it, one long leap | open | the mill tower | 5 | oak ledges |
| 18 | BLUE RUN | ice | relentless rim slides, then an ice tunnel finish | mixed | ice tunnel | 6 | ice stair |
| 19 | THE QUARRY | desert | the undercut: down the *outside* of the tower on jutting benches, sea below, climb back over the crane | open | crane | 4 | stair |
| 20 | ROPE BRIDGE | jungle | one-wide planks at the rim, guy posts, lantern poles | open | the bridge | 5 | vine |
| 21 | BASALT FLUES | nether | blackstone columns under a low soffit, magma vents | interior | flue stacks | 7 | stair |
| 22 | THE PILLARS | end | obsidian pillars over the void, purpur slabs, chorus | open | obsidian totem | 6 | bubble |
| 23 | SPORE HOLLOW | mushroom | cave of giant mushrooms, shroomlight, mycelium | interior | great red cap | 5 | vine |
| 24 | THE ARCHIVE | library | bookshelf halls, gallery stairs, lantern light | interior | the stair rotunda | 6 | ladder behind the shelves |
| 25 | PUMPKIN ROWS | farm | dusk farm: glowing jack-o-lanterns, scarecrow, hay | open | scarecrow | 4 | hay stair |
| 26 | THE GROVE | warped | teal shroomlight wood, bubble mid-level, caps above | mixed | warped giant | 6 | bubble |
| 27 | DUST DEVILS | mesa | hoodoo spires with capstones, uneven rhythm, biggest drops | open | hoodoo forest | 7 | rim stair |
| 28 | THE SEA GATE | prismarine | monument hall: sea-lantern light, water floor slots | interior | the gate arch | 5 | stair |
| 29 | THE CORNICE | snow | snow ridge at the rim, icicles under it, a lit cabin crossed inside | mixed | the cabin | 5 | stair |
| 30 | WART FIELDS | crimson | vivid nylium ledge, wart-canopy trees, lava pour behind | open | crimson giant | 6 | ladder on a trunk |
| 31 | ECHO SHAFT | deepdark | the dark vertical: a louvred sculk well climbed from inside, amethyst light | interior | the shaft | 8 | ladder |
| 32 | THE WHITE STAIR | quartz | pale gallery, long views, elegant; the breath before the gate | mixed | colonnade | 5 | stair |
| 33 | THE GATE | end | the obsidian arch, one last leap, and the garden again | open | the arch | 4 | stair |

Every level: 10–15 authored landings before its exit, a filler in its own
voice, and its skin naming three to five materials with real value contrast.

New themes this roster needs: honey, coral, gold, library, prismarine, snow,
crimson, quartz — most built from materials that already exist; new
materials are bookshelf, honeycomb, coral (three colours), shroomlight,
crimson nylium and wart block, pumpkin, raw gold, calcite already exists.
New props: lantern pole, windmill blades, bell, candle cluster, coral fans,
scarecrow. All built by `assets/src/` scripts like everything else.

## What the real map measures as (2026-08-12, from the map file itself)

The owner supplied the actual Parkour Spiral world save (1.2M downloads).
Parsed block-by-block; the numbers below are this project's targets and the
scripts live beside the session that produced them.

- **485 distinct block types** against this tower's ~60. The gap is mostly
  sub-block detail: fences, walls, slabs, trapdoors, snow layers, six kinds
  of flower, cave vines, froglights, dirt paths.
- **44 checkpoints** (gold pressure plates), y 52 → 230, tower centred on
  the origin. Course radius min/mean/max **28.5 / 44.5 / 51.7** — the real
  course wanders more than twenty blocks radially, where ours holds a
  five-block lane. Radial freedom is a large part of why its levels read as
  places rather than a corridor.
- **No checkpoint leg is walkable end to end.** A no-jump walker (step up
  one, drop three) covers a **mean 46%** of a leg before the ground ends.
  This is the islands-not-a-ribbon rule, measured; the in-level floor
  breaks exist to hold this tower to the same standard, and the probe's
  `runnable` metric prints both numbers side by side.

## What "difficult" can mean here, honestly

Unchanged from the 24-level tower and still binding — one jump impulse, one
speed:

| | shortest | longest |
|---|---|---|
| level | 2.00 m | **4.26 m** |
| up one block | 2.00 m | **3.10 m** |
| up two blocks | — | *no solution, here or in the game* |
| down one | 2.35 m | **4.98 m** |
| down four | 3.98 m | **7.05 m** |

Difficulty is: the top of the envelope repeatedly, small landings, lids,
no rest, and consequence in view. The roster leans on all five, but the
lesson of the reference is that difficulty is the punctuation, not the
sentence — the place is the sentence.

## Verifying it

`python tools/tower_probe.py` asks **did it come out as designed** — every
authored jump against `hop_span` on paper first (`--design-only`, instant),
then fidelity per level and per beat. `python tools/spiral_probe.py --plan
tower` asks **is it safe**, with nothing special-cased. The frame criteria
are judged from `brainrot shoot` contact sheets per level — `tools/`
carries a per-level harness so one level can be rendered without waiting
for the tower to reach it.

`tests/test_tower.py` holds the invariants: design legal on paper, rises
sum to head-room, no theme twice in a row, every level reached, the loop
closes, fidelity over 90%, unknown materials refused, and the scene drawn
end to end across seeds.

Measured on this design, 2026-08-12 (16 runs × 340 landings; 12 × 306 for
safety; 6 × 35 s for motion; 8 walk runs):

| | 24-level tower | this tower |
|---|---|---|
| designed landings placed as authored | 97.1% | **98.5%** |
| designed content / the exit climb | 68% / 33% | **67% / 33%** |
| named places | 24 | **33** |
| designed jump min/mean/max | — / 3.12 / — | **2.26 / 3.02 / 7.55 m** |
| unchecked emergency placements | 0.13% | **0.19–0.22%** |
| cells twice-claimed / off-lattice | 0 | **0** |
| climbable without the parkour | 0 m | **0 m** |
| moves per minute / median idle | — | **98.6 / 0.53 s** |
| dead air / frozen frames | — | **0.6% / 0.00%** |
| orbs taken / missed | — | **252 / 0** |
| per frame (vs parkour same run) | 2.80 ms (×1.39) | **3.41 ms (×1.30)** |
| frames mostly filled by a wall | 0.4% | **2.8%** |

Two of those need the honest note. The 7.55 m maximum jump is the quarry's
undercut drops — the longest jumps the motion model can express, finally
somewhere a viewer can see why. And **the wall-filled frame rate went up**,
which is partly the price of having interiors at all (a tunnel *is* walls
near the lens) and partly a real residue: it clusters in one- to two-second
stretches at corridor bends where the cliff swings across the aim, exactly
the shape the last such residue had. The method that closed that one —
bucket `_lens_jammed` frames by segment — is the way into this one, and it
is the top outstanding item, with per-theme pours, the windmill's blades
(and a bell, coral fans, a scarecrow) as the assets the roster still wants,
and authored `exit_beats` written for no level yet — the mechanism exists
and is tested, so the remaining third of the course that is machinery can
now be replaced one level at a time.
