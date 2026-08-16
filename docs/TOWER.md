# The hand-built tower

A designed tower of thirty-three levels, climbed in order and looping,
replacing the procedurally chosen course in the `spiral` scene. The building,
the physics, the placement checks and the renderer are the ones that were
already there; what changes is **who decides what the parkour is, and what the
world around it is made of**.

This document is the design. `src/brainrot/scenes/levels/` is that design as
data — **one module per level** since 2026-08-13, so that a level can be
rewritten without touching any other; `_base.py` holds the vocabulary and
`handlevels.py` is a re-export for anything that imported the old table.
`handplan.py` is the machinery that places it.

Two documents sit under this one and are read before it when the job is
building a level rather than the tower:

- **`docs/RULES.md`** — the constitution a single level must satisfy. The jump
  envelope per rise, the verb table (and which verbs actually fire, which is
  not the same thing), the ground rules that decide whether a level can be
  walked past, structures, rhythm, and the checklist with the command that
  prints each number.
- **`docs/RESEARCH.md`** — what the real map and its footage do, measured;
  `docs/reference/` is the material itself.

`tools/level_review.py` is the one command that renders and measures a single
level.

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

> **Read this section against `docs/RESEARCH.md`, which measured it and found
> three of these claims false.** The reference does *not* alternate interior
> and exposed (fully enclosed 6.1% of the way, in pinches a couple of metres
> long — what it always is, is a groove); it does *not* put one landmark on
> each level (the median biggest thing standing on a real terrace is 12 cells
> and 4 blocks tall, and identity comes from a 14-material floor); and its
> levels are *not* monotonic climbs (36 of 43 descend somewhere). Two of the
> three videos this was read off are also **Parkour Volcano, not Parkour
> Spiral** — same author, same genre, wrong label. The text below is kept as
> the record of what was believed when the tower was built.

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
  shelf, a structure, a pit, a channel bank or a room floor. **Since the
  rehash the course is not on that ground at all**: it runs two to six blocks
  over it, so what the lower half of a frame shows is the terrace *below* the
  running line — which is the same criterion read from the other side, and the
  reason the terrace's fourteen-material floor still matters.
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

- P0. **A level's structure is seen.** `tools/landmark_probe.py`: over half
  the levels that stand one up hold it at 25 degrees, unoccluded and in
  frame, for 1.5 s; at least a quarter reach 40 degrees; at least two per
  minute. This is the criterion the gated landmarks exist for, and the one
  that placement rate was standing in for and getting wrong.
- P1. Designed landings placed as authored ≥ 90% overall, no level under 80%.
  Counted over the design alone: the exit climb, the recoveries, the lock and
  the landmark crossing are `handplan.MACHINERY`, aimed at world features
  rather than written down landing by landing, and a fidelity number that
  includes them answers a different question (the lock alone took it from 97%
  to 91.5% when it landed).
- P2. Unchecked emergency placements ≤ 0.4% (raised from 0.3 when
  landmark reservation landed: +0.16 points on a same-world A/B buys the
  placement rate going 50% → 97%); cells twice-claimed 0;
  off-lattice 0; orbs missed 0.
- P3. Cone-alone walkability 0 m (the levels stay levels).
- P4. Body inside the world ≤ 0.05% of frames.
- P5. Per frame ≤ 3.5 ms in `frame_cost.py` terms (the shells and dressing
  are not free; this is the budget they must fit in).
- P6. Every authored jump legal on paper (`--design-only` clean).
- **P7. A fall costs you the level** (added 2026-08-16, and it is now the
  first criterion a level is judged on). A body that misses a jump and then
  walks — up one block, down any, never jumping — must not arrive back on the
  course above the level's entry apron. `tools/reentry_probe.py`, target
  **0**, currently one missed jump in 8,484 on one level visit in 85.
  Its design-time half is one landing per level within a block of the terrace
  and everything else at least two up (`tower_probe --design-only`), and the
  whole argument is `docs/REHASH.md`.

**P2 is met on the nose**: unchecked placement is **0.41%** against the 0.4%
this list asks for, and what closed it was raising eight levels' decks rather
than anything in the recovery chain -- a level cruising two blocks up with a
rise of eight spends seven landings on a staircase against the wall, and that
staircase is where the stuck landings were. It is an open item in CLAUDE.md
rather than an accepted number. P5 is *met* — 3.00 ms and a tower/parkour
ratio of 1.389 over nine rounds on a quiet machine, better than the 1.46 on
record, and a run writes 10% fewer cells than before the rehash because the
pedestals went. The 3.63 ms measured mid-pass was five rounds taken while the
test suite was running.

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
4b. **Gated landmarks: the course goes *through* them.** Reserving a
   structure got it built; it did not get it *seen*. The owner watched five
   minutes of live strip and remembered one structure against a 97%
   placement rate, and `tools/landmark_probe.py` says why: driven frame by
   frame through the real camera, only **18%** of the levels that were
   offered a landmark ever held it at 25 degrees, unoccluded and in frame,
   for a second and a half — and **none** ever reached 40 degrees. Placement
   rate was never the question.

   So the big structures are bigger, and each carries a **gate**: a box of
   cells through it, held open from the moment the level enters the horizon
   (`spiralplan.GATED`, the void written down rather than modelled, so a
   builder describes a solid mass and the doorway is cut from it in one
   place). `handplan.Course._landmark_nodes` steers the course through it,
   exactly as `_lock_nodes` steers it across a floor break: ordinary approach
   hops, then three stored landings — short of the doorway, inside it, out
   the far side — with the cursor untouched. Four things this taught:

   - **A doorway is walked through, not jumped through.** One jump impulse
     always rises 1.25 m, so the head sweeps three cells above every
     take-off: a lintel low enough to read as a doorway is a lintel the arc
     is refused under. Interiors (`walk` gates, three cells of clearance) are
     crossed at a run; openings five cells high (`hop` gates — an arch, a
     bell frame, a hole punched in the loom wall, a canopy overhead) are
     jumped through.
   - **A passage must be three cells wide.** A body is 0.6 m across and
     straddles the cell next door whenever it is not dead centre, and on a
     circle the diagonal step is the normal case — a one-cell doorway is
     refused by the body-fit check nearly every time and then placed by the
     non-strict retry, which is a body grazing a wall.
   - **The landings are cells, stored, not distances recomputed.** They are
     laid out in the structure's own frame when it is reserved. The same
     arithmetic run later against a bearing that has moved on misses its own
     doorway by the cell it drifted.
   - **...and the crossing's real work is the hand-over, not the aim.**
     Measured over six runs: 41 crossings offered, **18 put a landing inside
     the structure and only 4 of those were the exact stored landing**. The
     leg onto the first stored cell is an ordinary jump from wherever the
     approach hops finished and is refused about as often as not; what
     reliably works is that the offer releases the passage from the hold at
     the moment the frontier is near it, and the passage is then the only
     clear ground on the lane, so ordinary course walks into it. Retrying a
     refused offer does *not* help — a refused leg ends in `_last_resort`,
     whose recovery hop is three to five blocks in whatever direction will
     take one, so the second attempt is aiming behind itself (measured: 18
     retirements became 65, and 0.34% unchecked became 0.60%).
   - **Two inserted features cannot share ground.** The lock lays seventeen
     blocks in one decision and walked the frontier straight past doorways;
     the fix is the owner's rule — move the lock. Breaks on a gate-capable
     level are now kept nine blocks clear and on the far side of the apron,
     the lock defers to a nearer doorway, and script beats are clipped short
     of one. A gate the frontier gets past anyway is **retired**: the
     structure comes down and the small landmark is stood ahead of the body
     instead, because what is left otherwise is a wall.

4. **Landmarks** (`Level.landmark`). Data-driven blueprint stamps: windmill
   (with bladed sails), watchtower, temple front, giant tree, a hanging
   bell, crane, arch, scarecrow and more. **Reserved, not begged for**: the
   moment a section enters the horizon its landmark's exact cells are laid
   out at the apron from a per-level stream and held -- placement, arcs,
   pedestals, shells, pours and dressing all respect the hold, and painting
   later just redeems it. Measured: 97% of landmarked sections place their
   structure (it was ~50% when the painter ran last and searched for
   leftovers), at about +0.16 points of unchecked-placement cost on a
   same-world A/B. Three rules bought that trade: the hold is the
   blueprint's own cells with no margin ring, the apron bulge itself is
   clamped to the first 0.55 of the arc so it can never bar the exit
   staircase's wall lane, and on a ledge a structural cell that would sit
   in the course's lane fails the whole anchor rather than pinching it.
5. **Authored exits.** A level may write its exit beats the way it writes
   any beat — a staircase through a broken roof, a ladder inside a shaft
   shell — with the generated climb kept as the fallback it already is.
   The reliability chain (`_climb_on`, `_grab_the_wall`) is untouched.
6. **The camera looks where it jumps.** From the moment a take-off is
   booked until landing, the aim blends hard toward the actual landing
   block; the corridor-tangent blend applies only while running. This is
   F4, and it is a renderer change, not a course change.
7. **Per-level corridor geometry** (`Level.band`, 7.5–13 across the roster,
   capped by `BAND_MAX`). The corridor's width itself is a design decision:
   the timberworks is a 7.5-block gallery whose walls press in, the white
   stair a 13-block court, and the two are different buildings before a
   single block is laid. Every geometry site asks the level
   (`Cone.band_at`), and the old constant is only the generated tower's
   default.
8. **Radial wandering** (added after mining the real map, whose course
   swings radius 28–52). Outward: a landing whose ``hug`` exceeds the band
   width stands *past the rim* on floating spurs and piers — ``band()``
   gives way upward, and the aim's outer clamp follows. Inward:
   ``shell="grotto"`` carves a lamplit bay into the core face beside the
   move, lined as it is cut because the cone's interior is analytic and
   was never painted — a bare carve is a window onto invisible rock.
   Measured across the roster: landings sit 0.7 to 10.8 blocks off the
   core wall (band is 9.5), with 2% out past the old rim margin.

## Levels 1–20, rebuilt against the research (2026-08-13)

Twenty levels redesigned a pair at a time, each against `docs/RULES.md` and
judged from rendered frames rather than from probes. `name`, `theme` and `rise`
were frozen; everything else — every beat, filler, profile, shelf, band,
landmark, breaks, exit and skin — was rewritten, most of them from scratch.

| | 24-level tower | before this pass | **after** |
|---|---|---|---|
| designed landings placed as authored | 94.5% | 94.1% | **94.7%** |
| designed content, share of the course | 49% | 48% | 42% |
| the exit climb | 39% | 35% | 37% |
| unchecked emergency placements | 0.28% | — | **0.35%** |
| cells twice-claimed / off-lattice / orbs missed | 0 | 0 | **0** |
| climbable without the parkour | 0 m | 0 m | **0 m** |
| walkable along a level, built world | 47% mean, 0 of 42 | — | **43% mean, 0 of 52** |
| body inside the world | 0.00% | — | 0.02% (1 frame of 6,000) |
| **non-hop share of the move mix** | ~6% | ~6% | **14.3%** |
| move mix | hop 94% | hop 94% | **hop 86, walk 5, climb 4, slide 3, bounce 2, bubble 1** |
| levels holding their structure at 25° | 52% | — | 50% |
| ...at 40° | 29% | — | 30% |
| structures seen per minute | 2.75 | — | 2.50 |
| seconds on one theme | — | — | **10.7–13.0 s** (the reference is 10–15) |
| moves per minute / median idle | 100.6 / 0.53 s | — | 101.4 / 0.53 s |
| dead air / frozen frames | 0.6% / 0.00% | — | **0.0% / 0.00%** |
| frames mostly filled by a wall | 1.8% | 1.8% | 3.6% |
| **per frame** (vs parkour, same process) | 3.74 ms (×1.53) | — | **2.65 ms (×1.32)**  (2.79 ms ×1.46 on 2026-08-14) |
| tests | — | 628 pass | **628 pass, 34 skip** |

Four honest notes.

**The frame budget is met for the first time.** 3.74 ms was the one criterion
the gated-landmark pass missed; it is 2.65 now, comfortably inside the 3.5 the
criteria ask for. Nothing was optimised — the levels simply stopped hanging
floating cubes over the drop and started building on the ground they have.

**Designed content fell, 48% to 42%, and that is not what it looks like.** Six
points of it is a measurement fix: `level_review` was computing fidelity in the
*pinned* process, where a run opens on the level and lays its script from the
first landing. Measured the way `tower_probe` and the tests do, the same levels
read lower and always did.

**Wall-filled frames doubled, 1.8% to 3.6%**, and the cause is known and was
chosen: a ladder ride is a solid column one cell from the camera for two or
three seconds, and levels that never had a working climb now have one. It is
the price of the exit climb finally firing.

**And the empty-frame number, which is the one the rebuild existed for, is not
in this table because no probe carried it before.** It is now
`level_review --report`'s `frame empty`, and across the twenty it went from
43–77% of the view to 44–56%, with the two worst (THE QUARRY 77%, ROPE BRIDGE
65%) coming in at 54% and 53%.

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
- **Its course band is still 96.1% ordinary cubes.** Within five blocks of
  the checkpoint-to-checkpoint lines: slabs 0.7%, snow 0.8%, fences 0.2%,
  stairs 0.1%, trapdoors/walls/panes/carpets under 0.1% each. The famous
  sub-block obstacles are *seasoning* — a couple of appearances per level —
  and the craft that actually separates the real map is what its cubes are
  arranged as: buildings, terrain, rooms. Which is to say: profiles, shells
  and landmarks are the right counterpart, and the fence/wall/trapdoor
  forms should stay at the seasoning rate they now have, not become a
  staple.

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

`python tools/landmark_probe.py` asks **is the place's own structure ever
seen** — a real run, frame by frame, through the real camera, reported in
three bands of apparent size. `python tools/bypass_probe.py` asks **can a
walker get down a level without jumping**, over the built world rather than
the cone alone, which is the metric the levels' floor breaks and locks exist
to hold; the real map measures 46% mean coverage with no leg passable end to
end, and so does this tower.

`tests/test_tower.py` holds the invariants: design legal on paper, rises
sum to head-room, no theme twice in a row, every level reached, the loop
closes, fidelity over 90%, unknown materials refused, and the scene drawn
end to end across seeds.

Measured 2026-08-12, after the gated landmarks (12 runs × 292 landings for
safety; 6 × 240 for fidelity; 6 × 35 s for motion; 4 walk runs; 6 × 40 s for
visibility). The A/B column is the *same worlds with `GATED` emptied*, which
is the only honest before for this pass:

| | scenery beside the course | run through it |
|---|---|---|
| **levels holding their structure at 25° for 1.5 s** | 20% | **52%** |
| ...at 40° | 0% | **29%** |
| structures seen per minute | 1.00 | **2.75** |
| frames with one on screen | 13.0% | **18.5%** |
| designed landings placed as authored | 94.5% | **93.5%** |
| designed content / machinery / the exit climb | 49 / 12 / 39% | **39 / 23 / 38%** |
| unchecked emergency placements | 0.28% | **0.31–0.34%** |
| cells twice-claimed / off-lattice / orbs missed | 0 | **0** |
| climbable without the parkour | 0 m | **0 m** |
| walkable along a level, built world | — | **47% mean, 0 of 42 end to end** |
| body inside the world | 0.03% | **0.00%** |
| moves per minute / median idle | — | **100.6 / 0.53 s** |
| dead air / frozen frames | — | **0.6% / 0.00%** |
| frames mostly filled by a wall | — | **1.8%** (was 2.8%) |
| per frame (vs parkour same run) | 3.41 ms (×1.30) | **3.74 ms (×1.53)** |

Four honest notes. **A tenth of the course changed hands**: designed content
went 49% to 39% and machinery 12% to 23%, because a crossing is five to seven
landings the script did not write and the beat that would have played is
clipped short of the doorway. That is the trade this pass makes, and it is
the right one only because what the machinery now does is take the body
through the level's own building.

**Fidelity is counted over the design alone** from this pass on
(`handplan.MACHINERY`); measured the old way, with the lock and the crossing
inside the numerator, the same runs read 88%, and the drop is entirely
machinery aimed at world features rather than authored landings falling back.

**The frame cost went up** — 3.41 ms to 3.74, and against parkour in the same
process 1.30 to 1.53. The gated structures are three to four times the cells
of the ones they replace. It is comfortably inside a 16.7 ms budget and it is
over the 3.5 ms the criteria ask for, so it is the one criterion this pass
misses, and the cheap way back is fewer cells per blueprint rather than fewer
gates.

And the **wall-filled frame rate went down**, 2.8% to 1.8%, which was not the
point and is worth understanding before it is trusted: the crossings put the
course inside structures whose walls are close but whose doorways frame the
sky, where the residue this metric was chasing is the cliff swinging across
the aim at corridor bends. The method for the rest of it is unchanged —
bucket `_lens_jammed` frames by segment, and now by whether a shell or a gate
encloses the body. Per-theme pours, the windmill's blades, a bell, coral fans
and a scarecrow are still the assets the roster wants, and authored
`exit_beats` are still written for no level yet.


## All thirty-three rebuilt (2026-08-13)

Levels 21–33 followed the first twenty, seven agents against the rules as they
stood after the first pass — including the owner's two notes from watching a
preview run (fewer ladders; a level's descent belongs in its first two thirds,
with the exit as its highest point).

| | before the pass | after 1–20 | **all 33** |
|---|---|---|---|
| designed landings placed as authored | 94.1% | 94.7% | **95.2%** |
| unchecked emergency placements | — | 0.35% | **0.15%** |
| cells twice-claimed / off-lattice | 0 | 0 | **0** |
| climbable without the parkour | 0 m | 0 m | **0 m** |
| walkable along a level, built world | — | 43%, 0 of 52 | **41%, 0 of 75** |
| **non-hop share of the move mix** | ~6% | 14.3% | **18.5%** |
| move mix | hop 94% | hop 86% | **hop 82, walk 8, slide 4, climb 3, bounce 2, bubble 1** |
| seconds on one theme | — | 10.7–13.0 | **10.2–14.4** (reference 10–15) |
| dead air | 0.6% | 0.0% | **0.6%** |
| body inside the world | 0.00% | 0.02% | **0.17%** ✗ |
| frames mostly filled by a wall | 1.8% | 3.6% | **6.3%** ✗ |
| per frame (vs parkour, same process) | 3.74 ms (×1.53) | 2.65 ms (×1.32) | **3.40 ms (×1.60)** |
| tests | 628 pass | 628 pass | **628 pass, 34 skip** |

**Two criteria are missed and both have the same cause: the climbs now fire.**
Wall-filled frames went 1.8% → 6.3% because a ladder ride is a solid column a
cell from the camera for two or three seconds, and levels that never had a
working climb now have one — measured per level at 10–19% on the ladder levels
and 0% on the rest. Body-inside-the-world went 0.02% → 0.17% (10 frames of
6,000, worst 0.75 m), almost all of it ECHO SHAFT, whose profile was forced
from `ledge` to `plaza` to stop its exit staircase lapping the tower. Both are
real regressions, both were taken knowingly, and the alternative in each case
was worse: a silent staircase where a ladder was written, and a level that eats
an entire run.

Frame cost is 3.40 ms against the 3.5 the criteria ask for — inside the budget,
but the ratio to parkour is 1.60, the highest it has been, and that is the
interiors and the lids.

## What this pass leaves open

1. **An authored exit that cannot complete loops instead of falling back.**
   THE CISTERN with `profile="channel"` and an authored bubble `exit_beats`
   never left its own level: the course circled the tower at constant height
   and came back over its own cells one, two and three laps later, which the
   twice-claimed test caught as 157 doubled cells. Either change alone is
   fine. The authored exit was dropped to close it, but the real defect is
   that `exit_beats` has no working fallback when its climb cannot be built.
2. **The generated exit ladder essentially never fires**, and it is the
   biggest single thing left. `_ascent_climb` writes its column at `hug=2.0`
   with `pedestal=False`, and a climb anchors on solid rock within one cell of
   the column at its middle index and at its top — which at these bands the
   core's lean never reaches. Measured on a vine: 1 success in 1,559 "no
   anchor" refusals without a pedestal, 5 in 9 with one and `step_y >= 4`. On
   a generated bubble exit, 11,097 of 13,000 candidates refused. So a level
   whose `exit` says ladder gets an eight-landing staircase and is not told.
   **The one-line change is measured and not applied**: standing the column on
   its own pedestal takes designed content 47.7% → 50.1%, the exit climb 35.9%
   → 32.8%, climb-moves 107 → 125 and mean ascent 8.3 → 7.6 landings a level,
   at a cost of 4 → 6 unchecked placements. It touches the generated `spiral`
   scene as well as this one, so it wants its own pass and its own A/B.
3. **8.5% of level visits overrun** — 12 of 141 over six runs, worst cases 171,
   209 and 210 landings against a design of nine to twelve, with zero unchecked
   placements to show for it. It is the exit climb failing to leave, laying 50
   to 68 ascent landings in one place. Same root cause as (2); the strip can
   sit in one level for two minutes instead of eight seconds.
4. **A block records the theme of wherever it physically is**, so a level that
   leaves its own band donates its landings to whoever owns the air it lands
   in: THE QUARRY's rim descent passes one revolution above THE VAULT and is
   attributed to it, worth eight points of that level's designed-content
   figure. Any per-level number should be read with this in mind.
5. **Wall-filled frames are 3.6%, up from 1.8%**, and it is the ladder rides.
   Worth a look at whether a climb can be framed better rather than lit better.
6. **Levels 21–33 have not been through this pass.** They are the roster as it
   was: two or three materials, monotonic climbs, and `arc` values written
   against the old reading of the jump envelope.

## Measured against the reference, four ways (2026-08-13)

The owner watched the rebuilt tower live and said ninety per cent of the levels
were bad. Every acceptance number this tower had was green at the time, so the
first job was to find a number that was not. Four were tried. **Three of them
say we already match the real Parkour Spiral, and the fourth says we lose
badly** -- and the fourth is the one `docs/RESEARCH.md` had already written
down as never used.

> **Rows 1 and 2 were measured against the wrong reference and are corrected
> below.** Both were compared to `frames/ps1` and `frames/ps3`, and both of
> those videos run a **shader pack** — see `docs/reference/README.md`, where
> the provenance is now read off the titles instead of assumed. Against a
> vanilla control at matched sampling (`frames/vanilla_2hz/`), three rows do
> separate: we are **darker** (39% unlit against 18%), a single surface owns
> **more of the frame** (49% against 34%) and we are **more lopsided** (44%
> against 34%). A fourth — "our picture changes at half the rate" — was
> **retracted**: that vanilla column had been subsampled to 3.15 s against our
> 0.45 s, and at matched spacing the two are 13.9% and 14.2%. And the corridor question
> was underdetermined: asked two-sided, the real route has rock outboard
> **33.6%** of the way against our **5.6%**. `docs/RESEARCH.md` §4 and §10
> carry both. The paragraphs below are left standing as the record of what
> was believed, and as the reason to check what a reference actually is
> before drawing a conclusion from it.

**1. The pixels of a frame: no gap.** `tools/frame_probe.py` reads rendered
images and runs unchanged over a `brainrot shoot` directory and over the 122
real frames in `docs/reference/frames`. Over 100 frames of the tower against
the real map, every single-frame statistic says ours matches or beats it: unlit
28% against 38 and 49, biggest single surface 35% against 31 and 39, materials
on screen 8.4 against 10.2 and 8.3, edge detail 6.3% against 6.0 and 5.1, empty
ninths 24% against 34 and 40, lopsidedness 41% against 39 and 45. **There is no
aggregate of one frame's pixels on which this tower is worse than the one it
copies.** Use those numbers as a regression guard -- they will catch a level
going dark, blank or monochrome -- and never as a definition of good.

Two things had to be fixed on the way in and both would have read as plausible
results: an adaptive quantiser finds its N colours in any picture whatsoever,
so the palette count read 20-23 materials for a black cliff and for a market
square alike, and both sources wear a heads-up display inside the crop.

**2. The groove: no gap either.** `docs/RESEARCH.md` §4 measured the real
corridor as a shelf with rock off one shoulder, the drop off the other and a
lid overhead almost always. Sampled at 1,596 landings over six runs, ours is
the same building:

| | ours | real map |
|---|---|---|
| a rock lid somewhere overhead | 98% | 98% |
| median lid height | 9 blocks | 8 blocks |
| roof within 6 | 26% | 25% |
| nothing overhead within 40 | 2% | 2% |
| a wall within 4 m on a side | 73% | 71% |
| median distance to it | 4 m | 3 m |

So "it feels like a thin layer wrapped around one big undifferentiated tower"
is **not** the corridor's proportions. Do not go looking for it there again.

**3. The exit climb: a real gap, and now closed by one keyword.** See the
commit that stands the exit ladder on a pillar. Designed content 42% -> 46% of
the course, the exit climb 38% -> 33%, climb moves 2% -> 4% of the mix, at no
cost to placement, walkability, twice-claimed cells or the test suite. The
overruns in item 3 of the previous section are gone with it: over 12 runs, a
level visit is now min 11, median 20, max **30** landings, against the 171, 209
and 210 recorded before.

**4. The floor palette: the gap.** `docs/RESEARCH.md` line 365 --
*"palette is the identity lever, and it has never been used"* -- and it still
has not been. Measured over 54 level-visits, counting the top solid cell of
every column of written terrain and keeping materials that hold at least 1% of
that level's floor:

| | ours | real map |
|---|---|---|
| materials on a level's floor | **median 6** | **median 14** |
| share held by the commonest one | **55%** | **26%** |

That is the only axis on which this tower loses to the reference, it is the
one the research predicted, and it is what the owner is describing when he says
the ground has to be reshaped rather than the jump blocks. Two more unused
levers sit beside it in the same table and cost nothing once a floor has a
palette: the real map **paints its route** as a stripe of another floor
material down the middle of wide ground, and it marks a level's beginning with
an emissive block flush in the floor with the palette changing completely at
it.

**The standing lesson.** Three of four probes said we were fine. The last pass
was not wrong to measure; it was wrong to conclude from green numbers that the
thing was good. A probe can only ever say *this particular difference is not
the one* -- which is worth knowing, and is why all four are written down here
including the three that found nothing.

## Where the open list actually stands (2026-08-14)

The list above is kept as written because how it read at the time is part of
the record. Re-measured at the end of the walk-verb session, most of it has
moved, and one item was never the thing it looked like.

| item above | now |
|---|---|
| 1. an authored exit that cannot complete loops | still true in principle; a refused authored landing now falls through to the *next* authored landing before the generated staircase takes over, which is what fixed the cases that were losing twenty-four landings a sweep |
| 2. the generated exit ladder never fires | **fixed and superseded.** `pedestal=True` is applied. More to the point, **all thirty-three levels write `exit_beats`**, so `_ascent_climb` is dead code here and lives on only in the generated `spiral` |
| 3. 8.5% of level visits overrun | largely closed by (2) and by `_drop_climbed_treads`, which stops an authored climb one block above the next floor instead of letting it climb a fixed height past it |
| 4. a block records the theme of where it is | unchanged, and still the right warning to read every per-level number with |
| 5. wall-filled frames are the ladder rides | **confirmed exactly, and fixed at the camera.** Bucketed by move: climb 42.0%, bubble 30.3%, hop 1.0%. A ride is the one move whose body is pinned against the core, so the camera now looks outward for its length: 3.23% → 1.83% of frames, climb → 16.3% |
| 6. levels 21–33 have not been through the pass | unchanged |

**And the frame budget is met.** All four scenes in one process: parkour 1.91,
tower **2.79**, spiral 2.07, runner 1.83 ms/frame; tower/parkour 1.46 against
the 3.5 ms the criteria ask for. Every figure in the tables above that says
3.74 or 3.40 predates the level rebuild.

**What the exit climb is made of**, measured for the first time — the number
this document has been arguing about without ever having: 29% of the course, of
which **60% is the level's own design at 98.5% placed as authored**, 23% the
crossing, 17% a generated staircase, and 0% the reliability chain. It could not
be measured before because every landing of the climb is labelled `ascent`
whichever wrote it; nodes carry `origin` now and `tower_probe` prints it.

**Two acceptance criteria that were being met by two different descriptions of
the same surface.** `emit_layer` drew the core's flutes a cell proud of
`core_r` and `rock` had never heard of them, so half the ribs were geometry the
body walked through — 3.3% of body samples inside a drawn cell, up to 0.80 m.
"Body inside the world" could not see it, because it asks `blocked`, which is
`rock`. Paint is a subset of the solid by construction now and the figure is
0.00%.
