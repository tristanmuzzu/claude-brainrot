# The hand-built tower

A designed tower of twenty-four levels, climbed in order and looping, replacing
the procedurally chosen course in the `spiral` scene. The building, the physics,
the placement checks, the terrain painting and the renderer are all the ones
that were already there; what changes is **who decides what the parkour is**.

This document is the design. `src/brainrot/scenes/handplan.py` is that design as
data, and the level table's comments are the per-level detail — read them
together, but read this first.

## Why hand-build it at all

The generator works and is safe: 0.30% of landings fall through to the one
unchecked hop, no two solids share a cell, nothing is unreachable. What it
cannot do is be *memorable*. Its levels are drawn from one vocabulary with
per-level weights, so a level is a different **mix** of the same thirty-five
features rather than a different **place**, and the shape of a run is the same
shape every time. Two numbers say it plainly: the exit climb is 47% of all
landings and is one of four shapes, and the move mix is 94% plain hop.

A designed level can commit to something. It can be four maximum-reach jumps
onto one-cell pillars with no rest, or a room you cross entirely under a
ceiling, or a shaft you climb rather than a terrace you run along. It can also
be *wrong*, which is what the rest of this document is about.

## The bargain: authored intent, mechanical placement, verified physics

Three layers, and the split is the whole design.

**Authored.** Every landing in every level is written down: what it is made of,
how far along the terrace, how far in or out of the corridor, how high off the
floor, what shape it is, whether there is a lid over the jump that reaches it,
whether there is water underneath. Nothing is rolled.

**Mechanical.** The tower is round and the world is a lattice, so "3.6 blocks
further along the corridor and 1.2 further out" is not a cell. Placement resolves
that to whole cells the way it always has (`Course._targets` ranks the cells
nearest the authored point; `_try_node` walks its fallbacks). This is not
generation: the *shape* is authored and the machine only decides which cell is
nearest to what was asked for.

**Verified.** Every resolved landing goes through the same `Course._attempt`
that the generator's did: the cell must be free, have head-room, stand on
something, be reachable by a move vanilla's numbers actually have, and have a
clear path. An authored jump that no body can make is refused exactly as a
generated one would be, and `tools/tower_probe.py` reports how many landings
came out as authored, how many needed a fallback, and how many were refused
outright. **Fidelity is the acceptance criterion for the design; safety is the
acceptance criterion for the code.** They are different numbers and both are
printed.

The consequence worth stating: a level that measures badly is a level I
designed badly, and the fix is to change the design, not to widen a tolerance.

## The tower

Unchanged from the generated version, because its shape was not the problem: a
solid inverted cone, `BASE_R = 24`, flaring 0.05 per block, with a helical
trough cut round it and one-cell ribs for a skin. You are always in a corridor
— drop and sky outboard, fluted core inboard, the floor slab of the level three
above as a ceiling.

What changes is that **the levels are no longer random**. Their themes, heights
and chasm widths come from the table instead of from dice:

- **Twenty-four levels**, three to a revolution, so the cycle is eight
  revolutions. At six to ten seconds a level that is a little under three
  minutes of distinct content before anything repeats — comfortably longer than
  the strip is ever on screen for one thinking turn.
- **A run starts anywhere in the cycle.** The tower is fixed; the seed picks
  which level you enter on. Two runs a minute apart show different places.
- **It loops by climbing.** Level 24's exit lands on level 25, which is level 1
  again, six or so blocks higher. There is no seam to hide because there is no
  seam: the tower genuinely keeps going up, and the designed sequence is what
  repeats. The last level is designed as a gate for that reason — it is the one
  place the loop is legible, and making it legible is better than pretending.

Level heights vary from 3 to 11 by design rather than 4 to 6 at random, which
is most of what makes one level feel like a different building from the next:
a three-block rise is a step up between two rooms, an eleven-block rise is a
shaft.

## What "difficult" can mean here, honestly

There is one jump impulse and one horizontal speed, so the envelope is fixed
and small, and pretending otherwise would produce jumps the checker refuses:

| | shortest | longest |
|---|---|---|
| level | 2.00 m | **4.26 m** |
| up one block | 2.00 m | **3.10 m** |
| up two blocks | — | *no solution, here or in the game* |
| down one | 2.35 m | **4.98 m** |
| down four | 3.98 m | **7.05 m** |

Distances are stand-point to stand-point, which is about 0.7 m shorter than
centre to centre for ordinary blocks — the feet plant back from each edge.

So difficulty is not "longer". It is:

1. **At the top of the envelope, repeatedly.** A 4.0 m level jump is a
   four-block jump in the game and is the standard hard jump; a 3.0 m up-jump
   is the three-block up-jump. A designed level can ask for those back to back,
   which a weighted table almost never does.
2. **Small landings.** One-cell pillars, slabs, fence posts. The body's own
   footprint is 0.6 m against a 1 m cell, so a one-cell landing is genuinely
   tight and reads as tight.
3. **A lid.** A ceiling over the jump forces a flat arc and refuses the ones
   that climb. Checked, not decorative.
4. **No rest.** Chaining demanding landings with no easy beat between them is
   the cheapest difficulty there is and costs no geometry.
5. **Consequence in view.** A jump over lava, over a hole with nothing in it, or
   out over the rim with two hundred blocks of air under it is not harder to
   land and is much harder to *watch*, which is what this strip is for.

Nine tenths of the roster leans on 1, 2 and 4 together. Where a level wants a
verb the kernel does not have, the kernel gets it — but that is a physics
change with its own proof, and it is listed under "Kernel work" rather than
smuggled into a level.

## Making twenty-four levels feel like twenty-four places

Seven axes, and the roster is laid out so that consecutive levels differ on at
least three:

- **Band** — where in the corridor the course runs: hard against the core,
  down the middle, or out at the rim over the drop.
- **Altitude** — on the floor, at head height, or up near the soffit.
- **Form** — the terrace itself, full blocks, slabs, one-cell pillars, wide
  platforms.
- **Verb** — hop, ice slide, cobweb wade, ladder, bubble column, slime bounce,
  walk.
- **Constraint** — lids, moats, void beneath, narrow corridors.
- **Rhythm** — even, accelerating, burst-and-rest, relentless.
- **Light** — daylit, dusk, or dark enough that the level's own lamps are all
  you have.

## The roster

Levels are listed in climb order. "Rise" is how far above this level the next
one sits; "exit" is the designed way out of it.

| # | theme | name | the idea | rise | exit |
|---|---|---|---|---|---|
| 1 | plains | Meadow Gate | wide grass humps at full reach over a carved pond, then fence posts | 5 | oak ledges |
| 2 | farm | The Long Furrow | hay bales in a straight rank at 4.0 m, crop rows between, a haystack to top out | 4 | hay stair |
| 3 | village | Rooftops | plaster roofs at three heights, doorway lids, a drop onto a slab awning | 6 | ladder up a gable |
| 4 | desert | Sunstruck | dune tops, then sandstone one-cell pillars under a beam | 5 | sandstone stair |
| 5 | mesa | Red Spires | tall thin spires, big drops, the longest jumps in the tower | 8 | stair on the rim |
| 6 | jungle | Canopy | logs and leaf platforms, a vine to gain the upper storey, a drop through it | 7 | vine wall |
| 7 | mushroom | Spore Deck | wide caps with wide gaps, a slime pad in the middle | 4 | vine |
| 8 | dripstone | The Drip | spikes down from the soffit, water below, a bubble lift out of the pool | 9 | bubble column |
| 9 | mine | Cut and Cover | rails on the floor and a low ceiling the whole way, webs in the dark | 5 | ladder shaft |
| 10 | deepdark | Sculk | void gaps, tiny landings, lit only by amethyst | 6 | ladder |
| 11 | ice | Glacier Run | packed ice, the fastest level, slides at maximum reach | 5 | ice stair on slides |
| 12 | nether | Lava Leap | lava moats and magma pillars, a soul-sand beat to break the pace | 7 | stair |
| 13 | warped | Warped Grove | shroomlight, a bubble lift mid-level, caps and vines | 6 | bubble |
| 14 | end | Endpillars | obsidian pillars over the void, purpur slabs, chorus | 8 | bubble |
| 15 | rainbow | Woolwork | the candy level: pure floating blocks, slime, checks | 4 | stair |
| 16 | plains | The Weir | a water channel crossed on stepping stones, then one long leap | 5 | oak ledges |
| 17 | mine | The Shaft | vertical: scaffolds and ladders, barely a jump in it | 11 | ladder |
| 18 | ice | Blue Ice | relentless: long slides, no rest, out at the rim | 6 | ice stair |
| 19 | desert | The Quarry | a stepped pit of cut sandstone, deep drop-jumps | 4 | stair |
| 20 | jungle | Rope Bridge | one-wide plank runs out at the rim over two hundred blocks of air | 5 | vine |
| 21 | nether | Basalt Deltas | blackstone columns, tight lids, magma underfoot | 7 | stair |
| 22 | deepdark | Silence | the hardest: maximum reach onto one-cell landings, in the dark | 6 | ladder |
| 23 | village | Belfry | vertical: beams and ledges up the inside of a tower | 10 | ladder |
| 24 | end | The Gate | an obsidian arch, one last leap, and the cycle begins again | 3 | stair |

## Kernel work this design asks for

Listed separately because each is a change to the physics and needs its own
proof, not a level that happens to use it. Nothing in the roster above depends
on any of them; they are what the roster would like *next*.

- **Jump-cancel** — hitting your head zeroes the rise and keeps the run. Closed
  form, and it makes a lid at two blocks honest instead of the three the
  clearance test currently needs. Worth knowing before building it: a level
  jump under a two-block lid reaches at most 1.7 m, under `MIN_HOP`, so a `2bc`
  is a thing you sprint under rather than a gap you clear.
- **Ice accumulation** — speed as a state that ice raises and friction decays,
  so an ice corridor is a run-up you build. Levels 11 and 18 are designed
  around ice reaching further than stone; with accumulation they could reach
  further still the longer they ran.
- **Two-leg steered jumps** — an approximation of air control, which would make
  the neo family expressible. Levels 20 and 23 both want it.

## Verifying it

`python tools/tower_probe.py` prints two blocks of numbers.

**Fidelity** — did the tower come out as designed? Per level: landings
authored, landings placed as authored, landings placed on a fallback, landings
refused, and the arc actually spent against the arc designed. Anything refused
is a design bug and is named.

**Safety and feel** — the same measurements `tools/spiral_probe.py` makes, so
the hand-built tower is held to the standards the generated one reached: no
cell claimed twice, nothing off the lattice, the body never inside the world,
the cone alone still unclimbable without the parkour, and the pacing, hop
distribution and move mix.

`tests/test_tower.py` holds the invariants that must never lapse, including one
that every level in the table is reachable, exits, and is distinct from its
neighbours on at least three of the seven axes.
