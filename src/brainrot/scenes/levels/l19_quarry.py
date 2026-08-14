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
# with its jib out over your head, and a bottom that has gone under water.
#
# The route, in one breath. A lantern set flush in the orange floor at the
# head of the haul way -- ice-blue behind you, terracotta ahead, no blend
# -- then a walked step in under the timber tipple. Up two benches to the
# copper-plated head of the face, and **straight off the front of it, two
# blocks down and 4.9 m out, into the sump**, landing on a sawn block
# standing in the water. Out of the water, and then **out past the edge of
# the tower**: the cut has eaten through the rim, so the last two stones
# of the quarry stand on nothing at all with two hundred metres of sea
# under them, and the crane's jib is the only thing overhead. Back in off
# the spur, up the worked benches half a block at a time on their own
# slabs, and out up the flooded joint in the face.
#
# The one thing a viewer would remember is the rim: the orange floor
# simply stops, and the next two landings are out in the sky.
#
# ---------------------------------------------------------------------
# What was here before was the same place with its order inside out, and
# the three things that changed are all rules rather than taste.
#
# **The rim cut was the last beat.** It is the level's showpiece and the
# longest jumps in the tower, and ``_truncate`` spends a beat's budget on
# ``arc`` and eats the longest arc of the last beat first -- so the level's
# best moment was the one most likely never to be laid. It is beat two
# now. The same move fixes the other half of it: RULES 3 wants a level's
# descent in its **first two thirds** with the exit as the highest thing
# in the level, and a rim descent written last is a level that climbs and
# then dumps you three blocks down immediately before the way out.
#
# **The level was a ledge with a five-cell shelf and it framed as sky** --
# 77% of the view sea and air, the emptiest in the roster. A quarry floor
# is *wide*: it is the one place in the tower where a ``plaza`` is not the
# undressed plate that killed the first tower but the thing the place
# actually is, and a plaza paints its whole ``band`` from the level's own
# floor palette, which is the only lever that puts a colour in the bottom
# of every frame. The walk number that a ledge used to buy is bought here
# by three water moats instead -- water is see-through, so what stops a
# walker is not the liquid but the radius-three bowl the moat digs, which
# it can get into and cannot step out of (measured elsewhere at 65.8% ->
# 25.8% on identical worlds).
#
# **``rise=8`` decides the way out, and there was no choice to make.**
# This is the joint-tallest level in the tower. A staircase spends a
# landing a block, so leaving this one costs **eight** of the nine to
# twelve landings a level ever lays -- the whole design, spent on
# machinery. A bubble column costs three, and ``_level_budget`` hands
# back ``(need - 2) * 3.2`` -- nineteen metres of terrace -- for saying so.
# THE SILENCE is the tower's other ``rise=8`` level and reached the same
# conclusion from the same arithmetic. The ladder was never on the table:
# a ride at 2.35 m/s with the column a hand's width from an eighty-degree
# lens measured 20.9% of its frames jammed against 0.0% for every other
# move in the level it was instrumented on, and a bubble goes up at 11.0.
LEVEL = Level("THE QUARRY", "desert", rise=8, gap=3.0, exit="bubble",
              band=10.0, profile="plaza", breaks=0, landmark="crane",
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
    # THE HAUL WAY. The threshold, the face, and the fall into the sump --
    # six landings, and they are the level.
    #
    # **Why the whole idea is in one beat.** A beat is laid whole or not
    # at all and is truncated from the end, and machinery -- here the
    # crossing through the derrick, and any recovery -- is inserted
    # *between* beats and hands the body back at lift 1. So a rise written
    # in one beat and spent in the next is a rise that mostly does not
    # happen, and a fall that depends on it fails silently while still
    # reading as placed. The opener is also the one beat that is never
    # truncated, because it never competes with anything for terrace.
    #
    # 1. A lantern set flush in the orange floor on the rise at the head
    #    of the haul way, with a two-cell beam over it. The reference's
    #    own way of saying where a level begins: an emissive block on
    #    screen a couple of seconds before it is reached, and the palette
    #    changing completely at that block with no blend. Below is BLUE
    #    RUN -- blue ice, calcite and sea lanterns; from here it is
    #    terracotta, sawn sandstone and copper.
    # 2. In under the tipple on foot, with its beam three cells over the
    #    take-off. **A doorway is walked through and never jumped**: one
    #    impulse always rises 1.25 m and the head then sweeps the two
    #    cells above every take-off, so a lintel low enough to read as a
    #    lintel refuses every arc under it. This is the genre's 2bc, the
    #    lid you sprint under, and the only honest form of it this kernel
    #    has. It is second and not first because a walk needs its
    #    predecessor within half a metre of it and a beat boundary does
    #    not promise that.
    # 3. Up on to the first bench. +1 at arc 3.2, which is a reach of 2.53
    #    against a +1 window of 2.00-3.10 -- centred rather than pressed
    #    against the top of it, because 3.6 reaches 2.92 and is the arc
    #    that then has to fall back, and a fallback is not exact. The
    #    first water is cut under this jump: the toe of a quarry face is
    #    where it seeps.
    # 4. Up on to the copper-plated head of the face, lit. The highest dry
    #    stone in the body of the level and the thing you aim at from the
    #    threshold. It floats, because node 3's moat has just dug a bowl
    #    of radius three and a plinth cannot stand in a hole.
    # 5. **Off the front of it into the sump.** ``step_y=-2`` at arc 4.9
    #    across a hug that steps out 0.8: a reach of 4.29 against a -2
    #    window of 3.12-5.56, and the 0.84 fallback is still 3.51 and
    #    still inside it. This is the level's long jump and the only kind
    #    of long jump this motion model has -- level, a hop stops at 4.26
    #    stand point to stand point, and what buys the extra metre is the
    #    time spent falling, because the body does not slow down while it
    #    falls. It lands floating on a sawn block standing in the water
    #    the moat cuts under it. Written on ``step_y`` so that it is two
    #    below *the bench the body actually reached*, and it stops at
    #    surface 2.0 rather than 1.0: 1.0 is the terrace's own top cell,
    #    solid, and a descent on to it is refused with the rest of the
    #    beat abandoned silently behind it.
    # 6. Out of the water on to the next stone, roofed. The ``shell`` goes
    #    on the beat's **last** node, which is the only place one may go:
    #    it is painted the moment its landing commits and its walls are
    #    then in the way of the next landing of the same beat. At lift 2
    #    ``_shell`` skips every wall column with nothing under it, so what
    #    it grows is a roof and open sides -- which is exactly what is
    #    wanted, because what this level's sheet has always been short of
    #    is not walls but the dark brow across the top of the frame that
    #    the reference has in 73% of its shots.
    ("haulway", [n("glow", arc=3.2, lift=1, hug=3.2, spread=1,
                   deco="lamp", ceiling=2, orbs=1),
                 n("spruce", arc=2.9, step_y=0, hug=3.0, kind="walk",
                   ceiling=3, deco="lintel"),
                 n("sandstone", arc=3.2, step_y=1, hug=2.8, moat=True,
                   orbs=1),
                 n("copper", arc=3.2, step_y=1, hug=2.6, pedestal=False,
                   deco="lamp", orbs=1),
                 n("chiselled", arc=4.9, step_y=-2, hug=3.4,
                   pedestal=False, moat=True, orbs=2),
                 n("sandstone", arc=3.4, step_y=1, hug=3.0,
                   pedestal=False, shell="cave", orbs=1)]),
    # THE RIM CUT. The showpiece, at about sixty per cent of the way
    # through, which is where the reference puts one -- and emphatically
    # not in the last beat, where the truncator eats the longest arc
    # first.
    #
    # The quarry has worked *through* the outside of the tower. So the
    # orange floor stops, and the last two stones of the cut stand on
    # nothing: ``hug`` 6.6 and 9.6 against a ``band`` of 10.0, which is
    # past the outer margin the course normally keeps and therefore
    # genuinely out over the drop, with ``pedestal=False`` because there
    # is no ground out there for a plinth to reach down to. Both jumps
    # are long for the same reason every long jump here is -- a change of
    # ``hug`` is distance across the corridor and goes into the same
    # hypotenuse the ``arc`` does, so the second is 4.69 m of ground with
    # the sea under all of it.
    #
    # The third moat is on the opener: standing water in the middle of the
    # pit, and the node after it floats, so the bowl cannot take the
    # ground out from under it. Three moats is what holds the no-jump
    # walker down on a level with no floor breaks at all -- and ``breaks``
    # is zero on purpose, because any break at all forces the lock, which
    # lays seventeen blocks in one decision and is two or three of the
    # nine to twelve landings this level gets to spend.
    #
    # The opener is at lift 2 and is legal from either side of the beat
    # boundary: off the shell at surface 3.0 it is a level hop of 3.76,
    # and off machinery at lift 1 the 0.84 fallback is 3.06 against a +1
    # ceiling of 3.10. Everything behind it is on ``step_y``, which is
    # measured from the landing before and is therefore true wherever the
    # opener actually came down.
    ("rimcut", [n("chiselled", arc=4.4, lift=2, hug=3.6, spread=2,
                  moat=True, ceiling=2, orbs=1),
                n("sandstone", arc=3.6, step_y=0, hug=6.6,
                  pedestal=False, ceiling=2, orbs=1),
                n("copper", arc=3.6, step_y=-1, hug=9.6, pedestal=False,
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
    # deliberately not on ``step_y``: with ``step_y`` the placement floors
    # ``prev_surface + step_y - 0.5``, so a slab asked to rise one rises a
    # half and the paper checker and the engine disagree about where the
    # beat is.
    #
    # Every landing steps *inboard* as it climbs -- hug 6.2, 4.4, 3.6,
    # 3.2, 3.0 -- because that is what a bench does: each course is set
    # back from the one below it, and the face reads as a face rather than
    # as a wall of cubes. The lateral is not free, though: it goes into
    # the same hypotenuse the arc does, which is why these arcs are short.
    #
    # The opener is at lift 1 with ``spread=1``, and that is the safe
    # shape for a beat written on absolute lifts. ``_node`` clamps a
    # non-floor lift to at least 1, so the only fallback available to it
    # is *upward* -- and node two at lift 2 is then either +1 or level,
    # both of which a body makes. An opener at lift 2 could fall to 1 and
    # leave node two asking for a rise of two, which nothing in this
    # motion model has.
    ("benches", [n("sandstone", arc=3.4, lift=1, hug=6.2, spread=1,
                   orbs=1),
                 n("chiselled", arc=3.0, lift=2, hug=4.4, spread=0,
                   pedestal=False, ceiling=2, orbs=1),
                 n("sandstone", arc=3.2, lift=3, form="slab", hug=3.6,
                   spread=0, pedestal=False),
                 n("chiselled", arc=3.2, lift=4, form="slab", hug=3.2,
                   spread=0, pedestal=False, orbs=1),
                 n("copper", arc=3.2, lift=4, hug=3.0, spread=0,
                   pedestal=False, ceiling=3, deco="lamp", orbs=2)]),
], filler=[
    # THE SPOIL. The filler repeats and the tail of a script does not, so
    # this is what the level mostly *is*: the spoil heaps at the back of
    # the cut, a plank laid over the standing water between two of them,
    # and the tipping stage at the top with the tramway running on to it.
    #
    # It is written as a **cycle** and not as a line: it climbs two and
    # falls two every lap, so the body spends the loop at lift 2 to 4 with
    # the orange floor under it rather than running along the terrace at
    # lift 1. That is the answer to "half the jumps are at ground level",
    # and it is also worth frame -- the ray fan the empty-frame number is
    # taken with is +/-36 degrees inside eight metres, so at lift 1 its
    # shallow down-rows fly out over the rim and on a band this wide, from
    # a landing this high, they land on floor.
    #
    # The seam where the loop closes is a jump like any other and half of
    # what a filler ever loses is there: the stage at surface 5.0 back
    # down to the spoil head at 3.0 is -2 across 4.42 m of ground, a reach
    # of 3.74 against a -2 window of 3.12-5.56 -- the identical jump the
    # beat above hands it, which is why the loop can be entered from
    # either place.
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
    # level's water is all in the two beats that play once.
    ("spoil", [n("ground", arc=4.4, lift=2, hug=3.6, spread=1, ceiling=2,
                 orbs=1),
               n("spruce", arc=2.8, step_y=0, hug=3.4, kind="walk",
                 ceiling=3, deco="lamp"),
               n("chiselled", arc=3.4, step_y=1, hug=3.0, pedestal=False,
                 orbs=1),
               n("copper", arc=3.2, step_y=1, hug=3.2, pedestal=False,
                 orbs=1)]),
], exit_beats=[
    # THE FLOODED JOINT. Eight blocks, the joint-tallest rise in the
    # tower, and three landings rather than the eight a staircase would
    # spend.
    #
    # The cut has struck a spring, and the joint it opened in the back of
    # the face is running full. That is what a quarry that has stopped
    # working looks like, and it is the level's own idea rather than a way
    # out bolted on to it: the toe of the face is wet at node 3 of the
    # first beat, the bottom of the cut is a sump, and the water is what
    # finally puts you out of the hole. A body rides a bubble column at
    # **11.0 m/s** against a ladder's 2.35, so eight blocks is under a
    # second of screen -- and a climbing body has its face against
    # whatever it is climbing, which is why the ladder this level used to
    # leave by measured a fifth of its ride as a flat wall at arm's
    # length.
    #
    # **``pedestal=True`` is the load-bearing keyword and the reason this
    # fires at all.** ``_climb_move`` wants solid rock within one cell of
    # the column at its middle index *and* at its top; out in the lane the
    # only candidate is the landing's own stack, so the column needs a
    # plinth under it and a rise of at least four. Instrumented elsewhere,
    # a generated exit column with neither was refused on 11,097 of 13,000
    # candidates and became a staircase with nothing anywhere reporting
    # it. The stack here is sawn ``chiselled`` stone -- a standing pillar
    # of rock the quarry left un-taken, which is a real thing a quarry
    # has, and eight blocks of mass in the frame where the exit climb is
    # otherwise the emptiest third of any level in this tower. There is
    # deliberately no ``shell="shaft"`` round it: the tube is what puts
    # the body inside the wall, and taking one off elsewhere took body-
    # inside-the-world from 3 frames of 556 to 0 and the jam from 18.2%
    # to 10.4%.
    #
    # **The launch block stands at ``hug=2.9``**, and only the launch
    # block matters -- ``hug`` on the climb node itself is inert and
    # produces worlds identical to the frame. One level measured 69
    # wall-jammed frames of 1,293 with its launch at 2.2 and **0 of 1,280**
    # at 2.8. The camera locks on to the landing through take-off and
    # flight, so a launch tucked against the core aims the whole ride at
    # the cliff.
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
    n("glow", arc=3.2, lift=2, hug=2.9, spread=2, confine=True,
      deco="lamp", ceiling=3, orbs=1),
    n("sandstone", arc=2.4, step_y=6, kind="bubble", hug=2.4,
      pedestal=True, pedestal_style="chiselled", spread=0, orbs=2),
    n("copper", arc=3.2, step_y=1, hug=3.6, spread=0, pedestal=False,
      deco="lamp", ceiling=3, orbs=2),
])
