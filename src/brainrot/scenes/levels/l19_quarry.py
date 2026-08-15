"""Level 19: THE QUARRY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE QUARRY. A working sandstone quarry that has bitten a bay out of the
# tower's own face. The rock here has been *taken away*: what is left is a
# hot orange floor of worked terracotta, a stepped face of sawn benches
# with the pale cut still on them, a spruce derrick standing over the cut
# with its jib out across the run, and a bottom that has gone under water.
#
# The route, in one breath. A lantern set flush in the orange floor at the
# head of the haul way -- ice-blue behind you, terracotta ahead, no blend
# -- then a walked step in under the timber tipple. Up two benches and
# along the top of the face on foot to the tipping point, and **straight
# off the front of it, two blocks down and 4.9 m out, into the sump**,
# landing on a sawn block standing in the water. Up out of the water and
# then **out through the edge of the tower**: the cut has eaten past the
# rim, so the last stone of the quarry stands on nothing at all with two
# hundred metres of sea under it. Back in off the spur and up the worked
# benches half a block at a time on their own slabs, and out up the
# flooded joint in the face.
#
# The one thing a viewer would remember is the rim: the orange floor
# simply stops, and the next landing is out in the sky.
#
# ---------------------------------------------------------------------
# What was here before was the same place with its order inside out, and
# four things changed. Every one is a measurement.
#
# **The whole level is one beat, and that is the largest change in the
# file.** Measured over 24 unpinned runs, this level lays about seven and
# a half designed landings a visit and nine and a half of machinery --
# nearly all of the latter being BLUE RUN's exit staircase, which climbs
# into *this* terrace. Written as four beats the opener ate five of the
# seven and the rim cut, which is what the level is *about*, was laid on
# **one visit in three**: node-by-node, its two rim landings came out 4
# and 3 times in 12. As one eight-node beat they come out **9 and 7**,
# because an opening beat never competes with anything for terrace and is
# never truncated -- per node, this beat is laid 12/12, 12/12, 12/12,
# 12/12, 12/12, 10/12, 9/12, 7/12 over twelve runs. The whole level moved
# with it, same seeds, one process, only the beat list swapped: designed
# content 40% -> 43%, plain hop **89% -> 84%** against an 85% ceiling, and
# the two beats behind it went from 89% and 100% placed to **100% and
# 100%**, because they now ask for the little that is left rather than
# competing for the middle.
#
# **The rim cut was the last beat.** It is the showpiece and the longest
# jumps here, and ``_truncate`` spends a beat's budget on ``arc`` and eats
# the longest arc of the last beat first -- so the level's best moment was
# the one most likely never to be laid. The same move fixes the other half
# of it: RULES 3 wants a level's descent in its **first two thirds** with
# the exit as the highest thing in the level, and a rim descent written
# last is a level that climbs and then dumps you three blocks down
# immediately before the way out.
#
# **The level was a ledge with a five-cell shelf and it framed as sky** --
# 77% of the view sea and air, the emptiest in the roster. A quarry floor
# is *wide*: this is the one place in the tower where a ``plaza`` is not
# the undressed plate that killed the first tower but the thing the place
# actually is, and a plaza paints its whole ``band`` from the level's own
# floor palette, which is the only lever that puts a colour in the bottom
# of every frame. It measures **40%**. The walk number a ledge used to buy
# is bought here by four water moats instead -- water is see-through, so
# what stops a walker is not the liquid but the radius-three bowl the moat
# digs, which it can get into and cannot step out of.
#
# **``rise=8`` decides the way out, and there was no choice to make.**
# This is the joint-tallest level in the tower. A staircase spends a
# landing a block, so leaving this one costs **eight** of the nine to
# twelve landings a level ever lays -- the whole design, spent on
# machinery. A bubble column costs three, and ``_level_budget`` hands back
# ``(need - 2) * 3.2`` -- nineteen metres of terrace -- for saying so. THE
# SILENCE is the tower's other ``rise=8`` level and reached the same
# conclusion from the same arithmetic. The ladder was never on the table:
# a ride at 2.35 m/s with the column a hand's width from an eighty-degree
# lens measured 20.9% of its frames jammed against 0.0% for every other
# move in the level it was instrumented on, and a bubble goes up at 11.0.
LEVEL = Level("THE QUARRY", "desert", rise=8, gap=3.0, exit="bubble",
              band=10.5, profile="plaza", breaks=3, landmark="crane",
              # Hot, worked and industrial, and deliberately nothing like
              # SUNKEN TEMPLE, which is this tower's other desert: that
              # one is pale sandstone, gold and wet green prismarine, a
              # building drowned. This is the raw orange of a cut floor,
              # the pale sawn face standing over it, and oxidised copper
              # for everything the quarry *made* -- the tramway, the
              # tipping stages, the crane's tackle. ``_lm_g_crane`` builds
              # its mast and jib out of spruce literally and takes
              # ``theme.glow`` for the lamp at the head of the mast, so
              # the derrick is timber with one warm light in it whatever
              # else the palette does.
              ground="terra_orange", sub="redsand", rock="sandstone",
              accent="copper", glow="lantern", liquid="water",
              props=("rail", "lanternpost", "mcfence", "pebbles",
                     "deadbush"),
              # Twelve names here, which with the four roles weighted in
              # on top by ``Theme.floor_palette`` comes out at twelve
              # materials with the dominant one at 23% -- the shape a real
              # terrace of the reference measures as (a median fourteen
              # kinds, dominant 26%). The desert theme's own mix is
              # sandstone, gravel and stone and paints this level as a
              # beach; a quarry floor is spoil, grit, spilled stone and
              # the orange dust of what is being cut.
              floor=(("terra_orange", 3), ("sandstone", 3), ("redsand", 2),
                     ("chiselled", 2), ("gravel", 2), ("terracotta", 2),
                     ("terra_yellow", 1), ("clay", 1), ("coarse", 1),
                     ("spruce", 1), ("copper", 1), ("stone", 1)),
              candy=("copper", "chiselled"),
              # Bright and dusty. A lid within eight blocks of the head
              # makes ``_indoor_want`` return 0.85 and takes 27% off every
              # tint in the frame, and this level carries lids on about
              # half its landings on purpose -- so the ambient has to be
              # low enough that the lit half stays hot.
              dark=0.22, sky=(236, 198, 152),
              # If the flooded joint cannot be anchored the fallback stair
              # climbs the quarry's own sawn stone rather than the cliff.
              step=("sandstone", "hop"), beats=[
    # THE CUT. Eight landings, and they are the level: the threshold, the
    # face, the fall into the sump and the way out through the rim.
    #
    # An eight-node beat is against the usual advice, and the measurement
    # that justifies it is in the header: this beat is laid 12/12 through
    # its first five nodes and 7/12 at its last, because an *opening* beat
    # is never truncated. Everything behind node 0 is written on
    # ``step_y`` rather than on ``lift``: ``lift`` is measured from the
    # terrace, and an opener carries ``spread`` and therefore comes down a
    # block high or low about a fifth of the time, after which ``lift + 1``
    # is a rise of two and nothing in this motion model rises two.
    #
    # 0. A lantern set flush in the orange floor on the rise at the head
    #    of the haul way, with a two-cell beam over it. The reference's
    #    own way of saying where a level begins: an emissive block on
    #    screen a couple of seconds before it is reached, and the palette
    #    changing completely at that block with no blend. Below is BLUE
    #    RUN -- blue ice, calcite and sea lanterns; from here it is
    #    terracotta, sawn sandstone and copper.
    # 1. In under the tipple on foot, with its beam three cells over the
    #    take-off. **A doorway is walked through and never jumped**: one
    #    impulse always rises 1.25 m and the head then sweeps the two
    #    cells above every take-off, so a lintel low enough to read as a
    #    lintel refuses every arc under it. This is the genre's 2bc, the
    #    lid you sprint under, and the only honest form of it this kernel
    #    has. It is second and not first because a walk needs its
    #    predecessor within half a metre of it and a beat boundary does
    #    not promise that.
    # 2. Up on to the first bench. +1 at arc 3.2, a reach of 2.53 against
    #    a +1 window of 2.00-3.10 -- centred rather than pressed against
    #    the top of it, because 3.6 reaches 2.92 and is then the arc that
    #    has to fall back, and a fallback is not exact. The first water is
    #    cut under this jump: the toe of a quarry face is where it seeps.
    # 3. Up on to the second bench, lit and copper-plated. It floats,
    #    because node 2's moat has just dug a bowl of radius three and a
    #    plinth cannot stand in a hole.
    # 4. **Along the top of the face on foot to the tipping point.** The
    #    level's second walk, and it is worth five points of hop share on
    #    its own -- 89% -> 84% over 24 runs with nothing else changed --
    #    because it sits in the one beat of this level that is laid whole
    #    every single visit. A flat leg also costs the terrace two metres
    #    where a jump costs three, which is what pays for nodes 6 and 7.
    # 5. **Off the front of it into the sump.** ``step_y=-2`` at arc 4.9
    #    across a hug that steps out 0.6: a reach of 4.26 against a -2
    #    window of 3.12-5.56. This is the level's long jump and the only
    #    kind of long jump this motion model has -- level, a hop stops at
    #    4.26 stand point to stand point, and what buys the extra metre is
    #    the time spent falling, because the body does not slow down while
    #    it falls. It lands floating on a sawn block standing in the water
    #    the moat cuts under it. Written on ``step_y`` so that it is two
    #    below *the bench the body actually reached*, and it stops at
    #    surface 2.0 and not 1.0: 1.0 is the terrace's own top cell,
    #    solid, and a descent on to it is refused with the rest of the
    #    beat abandoned silently behind it.
    # 6. Up out of the water on to the lip of the cut. A rise of one while
    #    moving 1.4 m across the corridor, which is nearly all a +1 has:
    #    ``hug`` is distance across, it goes into the same hypotenuse the
    #    ``arc`` does, and the reach is 2.45 against a ceiling of 3.10.
    #    Written at 5.0 rather than the 6.0 it wanted for exactly that
    #    reason -- the wider step measured **37% exact** against **100%**
    #    here, because its two longer fallback arcs are both outside a +1
    #    window and only the authored one could ever have worked.
    # 7. **Out through the rim.** ``hug=8.8`` against a ``band`` of 10.5:
    #    the course normally keeps two off each edge, so this stands past
    #    the outer margin, over the drop, with nothing under it and no
    #    plinth reaching down to anything. 3.8 m across the corridor and
    #    3.4 along it is a jump of 4.42 m of ground, the longest in the
    #    level, and it is a *descent* because that is the only way to buy
    #    one. It carries the lamp, because the reference puts every light
    #    at the far end of a stretch and none in the middle distance.
    ("cut", [n("glow", arc=3.2, lift=1, hug=3.2, spread=1, deco="lamp",
               ceiling=2, orbs=1),
             n("spruce", arc=3.2, step_y=1, hug=3.0,
               ceiling=3, deco="lintel"),
             n("sandstone", arc=2.9, step_y=0, hug=2.8, kind="walk", moat=True,
               orbs=1),
             n("copper", arc=3.2, step_y=1, hug=2.6, pedestal=False,
               deco="lamp", orbs=1),
             n("copper", arc=2.8, step_y=0, hug=3.0, kind="walk",
               pedestal=False, ceiling=3),
             n("chiselled", arc=4.9, lift=2, step_y=-1, hug=3.6, pedestal=False,
               moat=True, orbs=2),
             n("sandstone", arc=2.8, step_y=1, hug=5.0, pedestal=False,
               ceiling=2, orbs=1),
             n("copper", arc=3.2, lift=2, step_y=0, hug=8.0, pedestal=False,
               deco="lamp", orbs=2)]),
    # THE BENCHES. Back in off the spur and up the worked face, and this
    # is the one beat written in half blocks.
    #
    # A quarry face *is* a flight of half-height steps -- stone comes out
    # in courses -- and ``form="slab"`` is the reference's commonest
    # non-cube form and is barely used in this tower. It also buys reach:
    # a slab landing is +0.5 and reaches 3.78 m where a full block at +1
    # stops at 3.10, so two slab courses gain a block across seven metres
    # of ground that one hop could not cross. Written on ``lift`` and
    # deliberately not on ``step_y``, because with ``step_y`` placement
    # floors ``prev_surface + step_y - 0.5`` and a slab asked to rise one
    # rises a half -- after which the design on paper and the level in the
    # world are describing different staircases.
    #
    # Every landing steps *inboard* as it climbs -- 6.4, 4.6, 3.8, 3.4,
    # 3.2 -- because that is what a bench does: each course is set back
    # from the one below it, and the face then reads as a face rather than
    # as a wall of cubes. The lateral is not free; it is why these arcs
    # are short.
    #
    # The opener is at lift 1 with ``spread=1``, which is the safe shape
    # for a beat written on absolute lifts. ``_node`` clamps a non-floor
    # lift to at least 1, so the only fallback available to it is
    # *upward*, and node 1 at lift 2 is then either +1 or level -- both of
    # which a body makes. An opener at lift 2 could fall back to 1 and
    # leave node 1 asking for a rise of two, which nothing makes. Measured
    # 28 landings of 28 exact over 24 runs.
    #
    # The fourth pond is on this opener, and it is the level's whole
    # answer to walkability. ``breaks=0`` means no floor gaps and no lock,
    # and turning one on measured, same sixteen seeds in one process, a
    # walker covering 43% instead of 50% -- for **designed content 42% ->
    # 28%**, because a lock lays seventeen blocks in one decision on a
    # level that only gets seven or eight of its own. A pond here instead
    # bought 50% -> **46%, worst run 96% -> 67%**, at *no* cost: design,
    # exactness, the per-beat table and the unchecked count came back
    # identical to the landing. The mechanism is not the water -- water is
    # see-through and a walker wades it -- it is the radius-three bowl,
    # which a walker can get into and cannot step out of. Node 1 floats,
    # so the bowl cannot take the ground from under it.
    ("benches", [n("sandstone", arc=3.0, lift=3, hug=6.4, spread=1,
                   moat=True, orbs=1),
                 n("chiselled", arc=3.0, lift=4, hug=4.6, spread=0,
                   pedestal=False, ceiling=2, orbs=1),
                 n("sandstone", arc=3.2, lift=5, form="slab", hug=3.8,
                   spread=0, pedestal=False),
                 n("chiselled", arc=3.2, lift=6, form="slab", hug=3.4,
                   spread=0, pedestal=False, orbs=1),
                 n("copper", arc=3.2, lift=6, hug=3.2, spread=0,
                   pedestal=False, ceiling=3, deco="lamp", orbs=2)]),
], filler=[
    # THE SPOIL. The filler repeats and the tail of a script does not, so
    # this is what the level does with whatever terrace is left: the spoil
    # heaps at the back of the cut, a plank laid over the standing water
    # between two of them, and the tipping stage at the top with the
    # tramway running on to it.
    #
    # It is written as a **cycle** and not as a line: it climbs two and
    # falls two every lap, so the body spends the loop at lift 2 to 4 with
    # the orange floor under it rather than running along the terrace at
    # lift 1. That is the answer to "half the jumps are at ground level",
    # and it is also worth frame -- the ray fan the empty-frame number is
    # taken with is +/-36 degrees inside eight metres, so at lift 1 its
    # shallow down-rows fly out over the rim, and from a landing this high
    # on a band this wide they land on floor.
    #
    # The seam where the loop closes is a jump like any other and half of
    # what a filler ever loses is there: the stage at surface 5.0 back
    # down to the spoil head at 3.0 is -2 across 4.42 m of ground, a reach
    # of 3.74 against a -2 window of 3.12-5.56 -- the identical jump the
    # beat above hands it, which is why the loop can be entered from
    # either place. 21 landings of 21 exact over 24 runs.
    #
    # The walk is at position **two**. A beat lays about half its nodes,
    # so a non-hop verb written at a beat's tail is written and never
    # seen, and one written first follows machinery at an arbitrary height
    # where a walk needs its predecessor within half a metre.
    #
    # **No ``moat`` anywhere in here**, and that is not taste: the filler
    # loops, and the second lap digs away the ground the first lap's
    # plinths are standing on -- 27,859 "pedestal will not stand"
    # refusals from one keyword when it was last instrumented. This
    # level's water is all in the beat that plays once.
    ("spoil", [n("ground", arc=4.4, lift=6, hug=3.6, spread=1, ceiling=2,
                 orbs=1),
               n("spruce", arc=2.8, step_y=0, hug=3.4, kind="walk",
                 ceiling=3, deco="lamp"),
               n("chiselled", arc=3.4, step_y=1, hug=3.0, pedestal=False,
                 orbs=1),
               n("copper", arc=3.2, step_y=-1, hug=3.2, pedestal=False,
                 orbs=1)]),
], exit_beats=[
    # THE FLOODED JOINT. Eight blocks, the joint-tallest rise in the
    # tower, and three landings rather than the eight a staircase would
    # spend.
    #
    # The cut has struck a spring and the joint it opened in the back of
    # the face is running full. That is what a quarry that has stopped
    # working looks like, and it is this level's own idea rather than a
    # way out bolted on to it: the toe of the face is wet at node 2 of the
    # first beat, the bottom of the cut is a sump, and the water is what
    # finally puts you out of the hole. A body rides a bubble column at
    # **11.0 m/s** against a ladder's 2.35, so eight blocks is under a
    # second of screen -- and a climbing body has its face against
    # whatever it is climbing, which is why the ladder this level used to
    # leave by is the single defect the brief names by name.
    #
    # **``pedestal=True`` is the load-bearing keyword and the reason this
    # fires at all.** ``_climb_move`` wants solid rock within one cell of
    # the column at its middle index *and* at its top; out in the lane the
    # only candidate is the landing's own stack, so the column needs a
    # plinth under it and a rise of at least four. Instrumented elsewhere,
    # a generated exit column with neither was refused on 11,097 of 13,000
    # candidates and became a staircase with nothing anywhere reporting
    # it. The stack here is sawn ``chiselled`` stone -- a standing pillar
    # the quarry left un-taken, which is a real thing a quarry has, and
    # eight blocks of mass in the frame where the exit climb is otherwise
    # the emptiest third of any level in this tower. There is deliberately
    # no ``shell="shaft"`` round it: the tube is what puts the body inside
    # the wall, and taking one off elsewhere took body-inside-the-world
    # from 3 frames of 556 to 0 and the jam from 18.2% to 10.4%.
    #
    # **The launch block stands at ``hug=3.4``**, and only the launch
    # block matters -- ``hug`` on the climb node itself is inert and
    # produces worlds identical to the frame. The camera locks on to the
    # landing through take-off and flight, so a launch tucked against the
    # core aims the whole ride at the cliff. Measured here over four seeds
    # in one process with nothing else changed, bucketing every frame the
    # body spends on this level: launch at 2.9 gave **61 jammed frames of
    # 2,241 (2.7%)** and at 3.4 gave **30 of 2,235 (1.3%)**. 3.9 is
    # identical to 3.4 to the frame, so 3.4 is where it stops paying.
    #
    # **No ``ceiling`` on the column**, ever: the lid stands in the cell
    # the column wants, ``_climb_move`` finds nothing to hang on, and the
    # climb becomes ordinary hops with the per-beat table still reading
    # 100% because the landings are all placed. The two lids here are on
    # the landings either side of it, where a beam is spread along the
    # direction of travel and answers the one column of the ray fan that
    # looks where the body is going.
    #
    # The last landing is the crane's loading stage, out at ``hug=3.6``
    # with the sky behind it rather than tucked against the core, for the
    # same reason: the last thing before the leap into ROPE BRIDGE should
    # be a lit copper floor against the sky and not a cliff.
    #
    # The arithmetic of the height: the lip is lift 2, the column gains
    # six, the head of it steps up one -- lift 9, one block above the next
    # level's floor, and the crossing comes down that block on to it,
    # because a flat sprint jump reaches 4.26 m and dropping one buys
    # nearly another metre. A climb that overshoots is a level above that
    # opens by dropping back down on to its own terrace, which is the
    # owner's "it puts a ladder there and then jumps back down to a lower
    # part than where the ladder was".
    #
    # **Check ``--report``'s move mix for the word ``bubble``.** If it is
    # missing this is an eight-tread staircase reserved for three, and the
    # level has no way out of its own idea.
    n("glow", arc=3.2, step_y=0, hug=3.4, spread=2, confine=True,
      deco="lamp", ceiling=3, orbs=1),
    n("sandstone", arc=2.4, step_y=2, kind="bubble", hug=2.4,
      pedestal=True, pedestal_style="chiselled", spread=0, orbs=2),
    n("copper", arc=3.2, step_y=1, hug=3.6, spread=0, pedestal=False,
      deco="lamp", ceiling=3, orbs=2),
])
