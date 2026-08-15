"""Level 30: WART FIELDS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# WART FIELDS. A worked nether-wart farm cut in steps into the red
# terrace: beds of soul sand held in by netherbrick baulks, wart standing
# in rows on them, a lava sluice run along the headland to keep the crop
# hot -- and one enormous wild crimson fungus left standing in the middle
# of the cleared ground, which is the thing the whole farm is planted
# around and the thing you run under.
#
# The route, in one breath. In over a shroomlight set flush in the
# nylium, a wade across the headland bed under the farm gate; up the
# baulk and onto a stack of bales; **off the top of the bales, two blocks
# down and 4.9 m out into a drained bed** -- the longest jump here and
# the only kind of long jump this motion model has -- and then **out of
# it at a wade**, because a bed is soul sand and soul sand is 2.51 m/s
# against a sprint's 5.612. After that it is the rows: bale, wade, bale,
# off the end of the row and out over the rim. The way out is the harvest
# stair up the headwall, lit at the top and thrown out over the drop.
#
# The one thing a viewer would remember is the fall into the bed and the
# slow drag out of it: everything else in this tower is at sprint pace.
#
# ---------------------------------------------------------------------
# **The place had to be a farm, and that is a differentiation decision
# rather than a flourish.** Three levels nearby are already fungus or
# nether: THE CRUCIBLE at 11 is a *built* smelting gallery, BASALT FLUES
# at 21 is a *geological* vent crust, and THE GROVE at 26 -- one turn
# below -- is a teal warped forest. And SPORE HOLLOW at 23 is the other
# ``greatcap`` level: a collapsed bowl carpeted in red cap flesh with
# black water in the bottom of it. A red fungus *forest* here would have
# been the fourth of those and the second of that. Cultivation is what
# none of them is: straight beds, a retaining wall, a sluice, a crop in
# rows, and a stair up the headwall at the end of the day's work. The
# soul sand is the whole reason it reads -- it is the block nether wart
# actually grows on, it is brown against a red field so the beds are a
# painted route without a single decorative block, and it is *slow*,
# which no other level in the tower has as its idea.
#
# **The exit is a stair and it is not negotiable.** The version this
# replaces climbed out on a ladder inside a ``shell="shaft"``, and the
# contact sheet is unambiguous about what that is worth: **eight
# consecutive frames of flat dark red**, a fifth of every frame the level
# gets, the body's face against the inside of a tube. Measured elsewhere
# on the roster by bucketing every jammed frame by segment *and* move, a
# ladder ride is 20.9% jammed against 0.0% for every other move in the
# same level, and it is not tunable, because the wall a ladder hangs on
# *is* the wall in the lens and ``hug`` on a climb node is inert. A
# five-tread stair read 1.0% against the same ladder's 5.4% for identical
# designed content.
#
# **A bubble was the other good answer and this level cannot have one.**
# ``_climb_move`` draws a bubble column as ``water`` whatever its
# ``climb_style`` says -- an agent found that on level 21 -- so a blue
# column standing in a red fungus field is a rendering fault with a story
# attached. Stair it is, and a stair on the farm's own headwall is a
# better ending than a hole in it anyway.
#
# **The great cap is skinned to be native.** ``_lm_g_greatcap`` names
# ``mushroomstem`` and ``mushroomred`` literally whatever the theme is,
# so both are written into the floor palette -- cap flesh trodden into
# the beds, stem chips in the path -- and the structure then reads as the
# wild fungus this farm was cleared around rather than as a mushroom that
# wandered in from another biome. It is REEF GARDEN's trick at level 12,
# taken down a notch: there the *accent* was moved to the structure's own
# red and the whole level went with it, and here the accent stays on the
# crop, because the level is called WART FIELDS and wart is
# ``wartblock``. Weight 1 each out of twenty-one is enough for the
# materials to be present in the ground without SPORE HOLLOW's red-flesh
# floor happening again seven levels later.
#
# ``greatcap`` is a **hop** gate, which reserves 8 of 8 on a ledge where
# the walk gates reserve 0-2, and an *ungated* landmark cannot reserve on
# a ledge at all -- so ledge is the profile that actually shows this
# structure, and it is also the one neither neighbour has (THE CORNICE
# below and ECHO SHAFT above are both plazas).
#
# **Three moats and three breaks, and they do different jobs.** This
# theme's liquid is lava and lava is *solid* to the no-jump walker, so a
# lava moat buys atmosphere and nothing at all for walkability -- what
# stops a walker is the hole, and on a lava level the holes have to be
# floor breaks. Hence ``breaks=3``, which costs the lock, and the two
# moats are spent on the picture: the bed the fall lands in, and the
# clinker in the sluice at the end of the first beat.
#
# **``band`` came down from 11.0 and the reason is measured on this
# level.** At 11.0 with a five-block shelf the contact sheet came back
# grey -- the corridor is wider than the level's own ground, so what
# fills the frame is cone soffit and cliff rather than red field -- and
# the great cap was held at readable size for **0.8 s** against the
# 1.5 s rule, because the course runs its lane and the structure stands
# a metre and a half further off it at every bearing. 10.0 is SPORE
# HOLLOW's own number for the same blueprint on the same profile, and
# the shelf is REEF GARDEN's 4.5, which is the widest that has been
# measured not to break a gated crossing. It is also the reference's
# groove: something solid within about four metres on the core side, the
# drop outboard.
#
# Measured over 8 unpinned runs, the two arms of that one change plus the
# beat restructure it paid for (the third beat's light and moat moved
# into the first beat, which is the only one that reliably lays):
#
#   | | band 11.0 / shelf 5.0 | band 10.0 / shelf 4.5 |
#   |---|---|---|
#   | designed content | 40% | **49%** (the rule is 45) |
#   | plain hop | 85% -- on the rule's own line | **82%** |
#   | structure held from the approach | 0.8 s | **2.5 s at 25 deg, 1.4 at 40** |
#   | walker coverage | 49% | **47%** (the real map: 46%) |
#   | lens jammed by a wall | 0.0% | **0.0%** |
#   | body inside the world | 0 of 502 | **0 of 529** |
#   | unchecked emergency placements | 1 | 2 (0.69%) |
#   | frame empty | 48% | 48% |
#   | the filler | never played | **28 of 28, 100%** |
#
# The version before either of those -- ladder, ``shell="shaft"``,
# ``band=10.0``, ``shelf=4.0`` -- read 94% exact with four beats at
# 90-97%, 3 unchecked, and eight consecutive dead frames on the sheet.
LEVEL = Level("WART FIELDS", "crimson", rise=6, gap=3.0, exit="stair",
              band=10.0, profile="ledge", shelf=4.5, breaks=3,
              landmark="greatcap",
              # Red field, brown beds, dark baulks, and the crop for the
              # only saturated thing standing on it. ``sub`` is what the
              # rim's cut face is made of, so a terrace of soul sand
              # shows its beds in section all the way along the drop.
              ground="crimsonnylium", sub="soulsand", rock="netherbrick",
              accent="wartblock", glow="shroomlight", liquid="lava",
              # ``shroomlight`` is a bright *texture* and emits nothing --
              # only ``lantern``, ``torch``, ``glowstone``, ``sealantern``
              # and ``magma`` are in ``spiral._GLOWING``. What does emit
              # is ``deco="lamp"``, which draws a cube of ``theme.glow``
              # with ``glow=True`` regardless, and the one ``magma``
              # landing in the first beat. So the farm's lights are real and
              # the amber is the theme's own rather than borrowed
              # glowstone, which is what THE CRUCIBLE and BASALT FLUES
              # both light their nether with.
              props=("crop", "mcfence", "netherfungus", "torch",
                     "vinehang", "pebbles"),
              # Brighter and warmer than the stock crimson theme, which
              # sits at ``dark=0.55`` behind a sky of (150, 58, 56) and
              # came out muddy on the sheet this replaces. ``sky`` is not
              # the sky -- the dome is the run's own palette -- it is the
              # ring's light: ``mix(white, sky, 0.35 + 0.45 * dark)``. At
              # 0.35 and a warmer red the world is lit rosy rather than
              # dimmed maroon, which matters because half the landings
              # here carry a lid and a lid takes 27% off every tint.
              sky=(198, 88, 74), dark=0.35,
              step=("crimson", "hop"),
              # Thirteen materials with the dominant at 14% before the
              # four roles are added on top. A real leg of the reference
              # uses a median fourteen and no one of them owns half. The
              # farm's own ground is the two big ones -- red nylium and
              # brown bed -- and under them: raw netherrack where the
              # field is unturned, the crop, the brick of the baulks, cut
              # stem timber, clinker where the sluice has burnt through,
              # grit, and the cap's own flesh and stem trodden into the
              # path.
              floor=(("crimsonnylium", 3), ("soulsand", 3),
                     ("netherrack", 2), ("wartblock", 2),
                     ("netherbrick", 2), ("crimson", 2), ("magma", 1),
                     ("gravel", 1), ("blackstone", 1), ("obsidian", 1),
                     ("mushroomstem", 1), ("mushroomred", 1),
                     ("shroomlight", 1)),
              beats=[
    # THE GATE. Seven nodes, and the whole opening movement is one beat
    # on purpose. A beat is laid whole or not at all and is truncated
    # from the end, and machinery -- the lock across the first floor
    # break, the crossing through the fungus -- is inserted *between*
    # beats and hands the body back at lift 1. So a rise written in one
    # beat and spent in the next is a rise that mostly does not happen,
    # and the fall that this level is about would then be a fall off
    # nothing. This beat opens the level, never competes with anything
    # for terrace, and is never truncated.
    #
    # 1. **A shroomlight flush in the nylium**, on a rise, with a lamp on
    #    it. The reference signposts where a level *begins* with an
    #    emissive block set into the floor and the palette changing
    #    completely at that block with no blend: below is THE CORNICE --
    #    snow, packed ice and pale spruce, white on dark -- and from this
    #    block it is red ground, brown beds and amber.
    # 2. **The headland bed, waded, under the gate lintel.** A lid three
    #    cells over the take-off is a lid inside a *jumping* player --
    #    one impulse always rises 1.25 m and the head then sweeps the two
    #    cells above every take-off -- so an arc under one is refused
    #    every time and the genre's 2bc is only expressible over a leg
    #    that never leaves the ground. It is at position two and never
    #    first: a walk needs its predecessor within half a metre and a
    #    beat boundary does not promise that. And the block is soul sand,
    #    so it is crossed at 2.51 m/s: the wade is the level's verb and
    #    this is where it is introduced.
    # 3. **Up onto the first baulk**, +1 at ``arc`` 3.2 -- a reach of
    #    2.53 against a window of 2.00-3.10, centred rather than pressed
    #    against the top of it, where the arc is what has to fall back.
    #    It keeps its pedestal, and that is the cheapest mass this format
    #    has: ``_pedestal`` writes the stack under a landing in the
    #    landing's own style, so a netherbrick block three up **is** a
    #    three-block brick pier standing out of the field.
    # 4. **Onto the stack of bales**, +1 again, pedestalled for the same
    #    reason -- a column of ``wartblock`` is a stook of cut crop, and
    #    it is the only saturated thing above head height in the level.
    # 5. **Off the bales into the drained bed.** ``step_y=-2`` at
    #    ``arc`` 4.9: a reach of 4.24 against a -2 window of 3.12-5.56.
    #    A descent is the only long jump this model has, because falling
    #    takes time and the body does not slow down while it does. It is
    #    on ``step_y`` and not on ``lift`` so that it is two blocks below
    #    *the bale the body actually reached*. It lands at surface 2.0
    #    and not 1.0 -- 1.0 is the terrace's own top cell, solid, and a
    #    descent onto it is refused with the whole rest of the beat
    #    behind it while the recovery drops a plain cube under the beat's
    #    own name. ``moat`` cuts the lava round it, so the fall is into a
    #    hole with the sluice standing in it.
    # 6. **The wade out**, on foot, under the cap's brim, with the lava
    #    either side of the bed. This is the level, and it is why the
    #    fall is worth having: every other landing in this tower is left
    #    at a sprint. ``pedestal=False`` from here, because node 5 has
    #    just dug a radius-three bowl and a stack of terrain cannot stand
    #    in a hole.
    # 7. **Up onto the far headland**, +1, and out of the bed.
    # 8. **The stride down the bale row**, level, under the rock. The
    #    third walk, and it is here rather than at the tail because the
    #    verb share is decided by what is *laid*: measured over 8 runs
    #    the level came out at exactly 85% plain hop, on the rule's own
    #    boundary, with two walks in the first seven nodes of this beat.
    # 9. **The clinker in the sluice**, +1 with the lava cut round it.
    #    This landing is ``magma``, which is the only warm material in
    #    the engine that actually emits -- ``spiral._GLOWING`` is
    #    ``lantern``, ``torch``, ``glowstone``, ``sealantern``, ``magma``
    #    and nothing else -- so it is one real light source at the far
    #    end of the run rather than a bright texture. It **was** the last
    #    node of the third beat, where the placement table said it laid
    #    0.6 times a visit: a beat past the second is a beat that mostly
    #    does not happen, and a light nobody sees is not a light. Its
    #    moat stands 9.3 m downstream of node 5's bed, which is the
    #    minimum -- a moat digs a radius-three bowl at commit and two any
    #    closer means the second stands in the hole the first dug.
    ("gate", [n("glow", arc=3.2, lift=1, hug=3.2, spread=1, deco="lamp",
                orbs=1),
              n("sub", arc=2.9, lift=2, hug=3.2, kind="walk", spread=0,
                ceiling=3, deco="lintel"),
              n("rock", arc=3.2, step_y=1, hug=3.0, spread=0, orbs=1),
              n("accent", arc=3.2, step_y=1, hug=3.2, spread=0, ceiling=3),
              n("sub", arc=4.9, lift=2, step_y=-2, hug=3.6, spread=0,
                pedestal=False, moat=True, orbs=2),
              n("sub", arc=2.9, step_y=0, hug=3.4, kind="walk", spread=0,
                pedestal=False, ceiling=3, deco="lamp"),
              n("accent", arc=3.2, step_y=1, hug=3.0, spread=0,
                pedestal=False, orbs=1),
              n("accent", arc=2.9, step_y=0, hug=3.2, kind="walk", spread=0,
                pedestal=False, ceiling=3),
              n("magma", arc=3.2, step_y=1, hug=3.4, spread=0,
                pedestal=False, moat=True, orbs=2)]),
    # THE ROWS. The crop itself, and the drying shed cut into the
    # headwall at the end of it.
    #
    # It opens at **lift 2** with ``spread=2``, which is the one real
    # lever a level has against "half the jumps are at ground level" and
    # is not free: an opener following machinery is placed from wherever
    # the machinery finished, so the spread is what buys it back. The
    # ``arc`` is 3.4 for the same reason -- a reach of 2.72 is inside the
    # window at +1 (2.00-3.10), level (2.00-4.26) *and* -1 (2.35-4.98),
    # so the opener exists whichever of the three heights the body is
    # handed over at, which a 4.4 would not: 3.72 is past what a
    # one-block rise can make.
    #
    # The wade is at position **two**. A beat lays about half its nodes,
    # so a non-hop verb written at the tail is written and never seen,
    # and the lamp on it is the route painted -- the reference lights the
    # place you are *going* and nothing else, and on a field of red
    # nylium the lit end of a brown bed is the only thing saying which
    # way the rows run.
    #
    # The shed is on the beat's **last** node, which is the only place a
    # shell may go: it is painted the moment its landing commits and its
    # walls are then in the way of the next landing of the same beat. It
    # is a ``cave`` and not a ``tunnel`` because the roof of either sits
    # in the cell a hop's apex sweeps and ``write`` refuses it there, so
    # what survives whole over a jump is the rough one; and it is the
    # only enclosure in the level, because one shell is a pinch and three
    # in a row jam the lens on 10-21% of frames.
    ("rows", [n("accent", arc=3.4, lift=3, hug=3.0, spread=2, ceiling=3,
                orbs=1),
              n("sub", arc=2.9, lift=3, hug=3.2, kind="walk", spread=0,
                ceiling=3, deco="lamp"),
              n("accent", arc=3.2, step_y=1, hug=2.9, spread=0, orbs=1),
              n("rock", arc=4.4, lift=2, step_y=-1, hug=3.8, spread=0,
                pedestal=False, shell="cave", orbs=2)]),
    # THE BANK. Three nodes, and it is written knowing exactly what it
    # is: the placement table says a third beat lays **0.6 landings a
    # visit** on a terrace this length, so this is a beat whose whole job
    # is to be a good first node. The bale at the head of the last bank,
    # the wade down it under the rock, and off the end of the row down
    # one and out over the rim.
    #
    # It carries no moat and no light, both of which used to be here and
    # are now in the first beat, where they are seen.
    ("bank", [n("accent", arc=3.4, lift=3, hug=3.0, spread=2, ceiling=3,
                orbs=1),
              n("sub", arc=2.9, lift=3, hug=3.2, kind="walk", spread=0,
                ceiling=3, deco="lintel"),
              n("rock", arc=4.4, lift=2, step_y=-1, hug=3.8, spread=0,
                pedestal=False, orbs=2)]),
], filler=[
    # THE BEDS, repeated for as long as the terrace lasts, and this is
    # what the level mostly *is*: a filler loops and a script's tail does
    # not. A bale at the head of the row, the wade down the bed, up onto
    # the stook, and off the end of the row down one and out over the rim.
    #
    # It is a **cycle and not a line** -- it gains a block and gives it
    # back every lap -- which is the only way a repeating beat does not
    # read as a corridor, and it is where this level's "descends
    # somewhere" mostly lives. Nothing in it sits at lift 1: the lifts
    # are 2, 2, 3, 2, so the body spends the repeated half of the level a
    # clear block or two above its own beds rather than on them.
    #
    # **No moat in here.** The filler loops, and the second lap digs away
    # the ground the first lap's pedestals are standing on -- 27,859
    # "pedestal will not stand" refusals from one keyword, on the level
    # that found it.
    #
    # The seam where the loop closes is a jump like any other and half of
    # what a filler ever loses is there: the last landing stands at 3.0
    # at ``hug`` 3.6 and the first at 3.0 at 3.0, so coming back round is
    # a level jump across a reach of 2.77 -- and the same number is legal
    # at +1 and at -1, which is what it is asked from when machinery
    # lands between two laps.
    ("beds", [n("accent", arc=3.4, lift=2, hug=3.0, spread=2, ceiling=3,
                orbs=1),
              n("sub", arc=2.9, lift=2, hug=3.2, kind="walk", spread=0,
                ceiling=3, deco="lamp"),
              n("accent", arc=3.2, step_y=1, hug=2.9, spread=0, orbs=1),
              n("rock", arc=4.4, lift=2, step_y=-1, hug=3.6, spread=0,
                pedestal=False, orbs=1)]),
], exit_beats=[
    # THE HEADWALL. Seven landings up the retaining wall at the end of
    # the last bed, written out rather than left to the generated
    # staircase -- which is the same six landings unlit, unlidded and
    # hung in the corridor, and the exit is the emptiest third of any
    # level in this tower.
    #
    # **The arithmetic of the height.** The foot stands at lift 2, so its
    # walking surface is 3.0; the wade holds it there; five treads gain
    # five; the top is 8.0 against the next terrace's 7.0, and the
    # crossing appended after the climb comes down exactly one block --
    # which is this level's ``rise`` of 6. A stair that overshoots is a
    # level above that opens by dropping back onto its own terrace, which
    # is the owner's "it puts a ladder there and then jumps back down to
    # a lower part than where the ladder was". Seven nodes and not five,
    # because an authored ``exit_beats`` shorter than the reserve the
    # machinery asked for is discarded *whole* and replaced by the
    # unlidded generated stair, and the reserve does not shrink because a
    # design ends high: machinery puts the body back at lift 1, so it is
    # six or seven whatever the level does.
    #
    # Every tread is a block up and about three along, written at ``arc``
    # 2.9 -- a reach of 2.25, and its 1.28 ``step_y`` fallback is 3.03,
    # both inside the 2.00-3.10 a one-block rise allows, so even the
    # fallback is exact-legal. The ``hug`` weaves 3.2 - 2.8 - 3.3 - 2.8 -
    # 3.4 - 4.2, so the flight winds up the face of the wall instead of
    # being a straight column of identical hops, which is the single most
    # monotonous thing this format can produce and is a third of what a
    # viewer sees. ``confine=True`` keeps the treads on the level's own
    # ground; only the last lip hangs.
    #
    # Every tread carries a lid and the last one carries none. A
    # ``ceiling`` beam is the cheapest overhead mass a level author has,
    # it is legal over a +1 hop (an apex of 1.25 against a lid at three,
    # and the check is on the feet), and it fills the one column of the
    # ray fan that looks where you are going. The lip is bare and lit and
    # thrown **out** at ``hug`` 4.2, because the camera locks onto the
    # landing through take-off and flight: a lip tucked against the core
    # aims the last second of the level at the cliff, and a lip over the
    # drop aims it at sky with the next level standing in it.
    n("glow", arc=3.2, step_y=0, hug=3.0, spread=2, deco="lamp", ceiling=3,
      orbs=1),
    n("sub", arc=2.9, step_y=0, hug=3.2, kind="walk", spread=0,
      confine=True, ceiling=3, deco="lintel"),
    n("rock", arc=2.9, step_y=1, hug=2.8, spread=0, confine=True,
      ceiling=3),
    n("accent", arc=2.9, step_y=1, hug=3.3, spread=0, confine=True,
      ceiling=3, orbs=1),
    n("rock", arc=2.9, step_y=1, hug=2.8, spread=0, confine=True,
      ceiling=3),
    n("accent", arc=2.9, step_y=1, hug=3.4, spread=0, confine=True,
      ceiling=3, orbs=1),
    n("glow", arc=3.0, step_y=1, hug=4.2, spread=0, pedestal=False,
      deco="lamp", orbs=2),
])
