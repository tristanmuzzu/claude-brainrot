"""Level 26: THE GROVE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE GROVE. **A warped fungus grove that has grown up through a spilled
# hoard.** The bastion's treasury floor cracked and went into the tower;
# what is left on this terrace is teal nylium with raw gold half buried
# in it, lava standing in the crack, blackstone rubble overhead, and the
# piglins' gold piled where it fell. The way out is up the pile.
#
# The route, in one breath. A glowstone block set flush in the nylium
# with lava cut round it -- the palette stops being PUMPKIN ROWS' brown
# farmland at that one block -- then **on foot** under a fallen
# blackstone lintel, up a gold ingot heap, up a warped stem, and **off
# the top of it: two blocks down and 4.9 m out** onto a gold block
# hanging over the drop, which is the level's long jump and the only
# kind of long jump this motion model has. Then the heaps themselves: a
# slow stride through the soul sand spilled among them, up over a lava
# pool on a floating ingot, and up under a rough roof. The grove loops
# for as long as the terrace lasts, and the way out is **the treasure
# stair** -- a lit block of paving at the foot and seven treads climbing
# the pile against the cliff on black plinths, gold and warped stem
# alternating, with a glowstone curb at the head.
#
# The one thing a viewer would remember is the fall off the stem out
# over the sea with the gold under it.
#
# ---------------------------------------------------------------------
# **The landmark decided the level, and it is the reason this is a
# rewrite rather than a patch.** ``hoard`` is now assigned here, and
# ``_lm_g_hoard`` names ``rawgold`` and ``gold`` *literally* whatever the
# theme is (RULES 7): two four-block piles of raw gold either side of the
# way through, with a gold lintel over it at dy 5. A level that is
# committed to teal and orange gets a warm yellow gate standing in it
# from another biome -- which is exactly how the last contact sheet of
# the previous design would have read. So the gold is the level instead
# of an intruder in it: it is in the floor palette as ingots and nuggets,
# it is the accent role, it is what the exit stair is made of, and the
# gate is the one place the pile is deep enough to walk between.
#
# Everything else is set against it. ``rock="blackstone"`` (70,64,74) is
# the darkest thing here and it is what ``Course._node`` writes for every
# ``ceiling`` lid, every ``deco="lintel"`` beam and every shell roof --
# so the dark brow across the top of the frame costs nothing but the
# keyword, which is the reference's own composition (73% of its frames
# are more than half dark rock in the top fifth). The nylium is the
# committed hue in the bottom of the frame. The sky is the slot between.
#
# Against PUMPKIN ROWS below: teal and black against brown farmland and
# hay, a lit crack in the ground against a field gate, a two-block fall
# and a gold stair against a flat weave. Against DUST DEVILS above: teal
# against red sand. This is the cold level between two warm ones and it
# should be read as the break.
#
# ---------------------------------------------------------------------
# **What was wrong, measured before anything was changed.** The version
# this replaces read 27% designed content, 87% plain hop, its structure
# on screen for 0.6 s and **96 of its 195 landings over eight runs were
# the exit climb** -- half the level. The cause was one number and it was
# not a taste question: the level's ``rise`` is **8**, so the top of the
# way out has to stand at lift 9 (a walking surface of 10.0 against the
# next terrace's 9.0, with the crossing coming down that block), and the
# authored bubble column topped out at **lift 7**. The crossing was then
# asked for a jump that rises two, which nothing in this motion model
# makes; it was refused, ``_climb_on`` laid another step, and the level
# spent twelve landings a visit grinding at a chasm it could not cross.
# Every beat behind it lost its terrace to that. Check the arithmetic of
# the exit height before anything else in this file.
#
# **And the way out is a stair, not a bubble.** A bubble column is drawn
# as ``water`` whatever ``climb_style`` says, so on a nether-family theme
# it is a bright blue tube standing in an alien forest -- two frames of
# the old sheet are a full-screen blue-green wash, which is the ride
# itself. Measured elsewhere on identical designed content, a five-tread
# stair reads **1.0% of frames with a wall in the lens against a ladder's
# 5.4%**, and a stair on a themed footing is not a worse ending than a
# climb, it is a quieter one. RULES 3 asks for a climb exit on about one
# level in five and this level's idea is the hoard, not a shaft.
#
# The bill for that is honest and it is in the numbers: seven treads plus
# the launch is eight landings of the twenty-five this terrace lays, and
# ``exit_beats`` are counted as machinery by ``handplan.MACHINERY``
# however carefully they are written -- so the way out of a level whose
# ``rise`` is 8 is half of it whatever anybody does, and the level's
# designed share reads 36-45% depending on the sweep. What it buys back
# is that they are *lidded and pedestalled* -- the exit is the emptiest
# third of any level in this tower, and a roofed tread standing on its
# own black plinth is the difference between a staircase and a row of
# cubes in the sky.
#
# **``band`` is 10.0 and not 12.0, and that was worth more than any
# keyword in the file.** Same seeds, only the band changed: designed
# content 42% -> 45%, exact 93% -> 95%, jammed lens 2.6% and 0.2% on two
# seeds -> **0.0% on both**, frame empty 49/51 -> 48/50, walker 49% ->
# 48%. A wider corridor on a level whose course spends most of its
# length at lift 2-9 simply pushes the cliff out of the lens and puts
# sea in it. ``shelf`` was swept with it: 6.5 is worse on every count
# (jam 3.9%, empty 50/52) and 5.0 costs four points of designed content,
# because the notes' "widening the shelf fills the bottom of the frame"
# is a *low* level's lever and the down-rays here fly over the shelf
# whatever it is.
#
# ---------------------------------------------------------------------
# The things that are not free choices:
#
# * **``glow`` is ``glowstone``, not the theme's ``shroomlight``.**
#   ``spiral._GLOWING`` is five names -- ``lantern``, ``torch``,
#   ``glowstone``, ``sealantern``, ``magma`` -- and ``shroomlight`` is a
#   bright orange *texture* that emits nothing at all. Glowstone
#   (250,214,130) is the warm pale one and it is the same family as the
#   gold, so the five lamps in this level read as the hoard's own light
#   rather than as furniture: at the threshold, inside each of the two
#   ``cave`` bays, at the foot of the stair and at the head of it. Every
#   light in the reference is at an end of something and doing a job,
#   and an interior carries its own or it is a black frame -- three of
#   this level's frames came back near-black before the two bays had
#   theirs.
# * **The liquid is lava, and it is here for the picture rather than for
#   the walker.** Water is in ``SEE_THROUGH``, so a water moat digs a pit
#   a no-jump walker falls into and cannot climb out of; lava is *solid*
#   and a walker strolls across the top of it. So the two pools buy
#   atmosphere and nothing at all for walkability, and what holds that
#   number down here is ``breaks=3`` plus the floating landings. Water in
#   the Nether would have bought the metric and lost the place.
# * **Soul sand is the slow beat.** It runs at 2.51 m/s against a normal
#   5.61, so the stride through the spill is a genuinely different tempo
#   rather than a differently-coloured cube -- and a ``walk`` is the only
#   verb this kernel has that can pass under a lid at all, because one
#   impulse always rises 1.25 m and the head then sweeps the two cells
#   above every take-off. It is at position **two** of every beat that
#   has one: a beat lays about half its nodes, so a non-hop verb written
#   last is written and never seen, and one written first follows
#   machinery at an arbitrary height where a walk needs its predecessor
#   within half a block.
# * **Fourteen floor materials with the dominant one at 26%.** A real leg
#   of the reference measures a median fourteen kinds with the commonest
#   at about a quarter, and that -- not the one big structure -- is why
#   its levels read as places. The tail here is the hoard weathering into
#   the grove: raw gold, gold ore, gold, nuggets of magma, and the
#   crimson that has crept in at the edges of the warped.
# * **Lids on about half the landings and not all of them.** A lid within
#   eight blocks of the head sends ``_indoor_want`` to 0.85 and takes 27%
#   off every tint in the frame, so a level that lids everything is a
#   dark level whatever ``dark`` says. The ones that carry none are the
#   heap tops out near the rim, which are the landings that want sky
#   behind them: a silhouette against the cliff is not legible and one
#   against sky is.
# * **Every landing has a ``hug``.** On a ``ledge`` an unhugged landing
#   is pulled to the middle of the *band*, which on a five-and-a-half
#   cell shelf inside an eleven-block band is out over the drop.
LEVEL = Level("THE GROVE", "warped", rise=8, gap=3.0, exit="stair",
              band=10.0, shelf=5.5, breaks=3, landmark="hoard",
              # Teal floor, black everything that stands up or hangs
              # overhead, gold for the hoard, warm pale light, lava in
              # the crack the treasury fell through.
              ground="warpednylium", sub="warped", rock="blackstone",
              accent="gold", glow="glowstone", liquid="lava",
              candy=("gold", "warped"),
              props=("netherfungus", "vinehang", "grasstuft", "pebbles",
                     "chain"),
              sky=(96, 204, 190), dark=0.30,
              # The grove growing back over the spill: nylium and stem at
              # the top, the bastion's blackstone and netherrack under
              # it, and the gold in three grades -- ingot blocks, ore and
              # the nuggets trodden into the ground.
              floor=(("warpednylium", 7), ("warped", 4), ("blackstone", 2),
                     ("rawgold", 2), ("goldore", 2), ("soulsand", 2),
                     ("netherrack", 1), ("magma", 1), ("shroomlight", 1),
                     ("crimsonnylium", 1), ("wartblock", 1), ("gold", 1),
                     ("deepslate", 1), ("tuff", 1)),
              # If the authored stair ever falls through to the generated
              # one, it climbs the hoard's own gold rather than the cliff.
              step=("gold", "hop"), beats=[
    # THE CRACK -- the threshold, the climb and the fall, all in one
    # beat, because this is the only stretch of the level that is laid
    # whole on every visit. An opening beat is never truncated: it never
    # competes with anything for terrace. Everything behind the opener is
    # written on ``step_y`` rather than on ``lift``, because ``lift`` is
    # measured from the terrace and a beat whose opener came down a block
    # high -- it carries ``spread``, so it does, about a fifth of the
    # time -- then asks for a rise of two, which nothing here makes.
    #
    # 1. **The sill.** A glowstone block set flush in the nylium on a
    #    rise, with lava cut round it in a radius-three bowl and a
    #    blackstone beam three cells over it: light, lid and a complete
    #    change of palette at one block with no blend, which is how the
    #    reference signposts a level. Written at ``lift=1`` and not 2 --
    #    the identical beat measures about 67% at lift 2 and 100% at
    #    lift 1, because a beat's opener is placed from wherever the
    #    machinery between beats left the body, and that is lift 1.
    # 2. **Under the fallen lintel, on foot.** A doorway is walked and
    #    never jumped: an arc under a beam low enough to read as one is
    #    refused every time, and over a ``walk`` there is no arc at all,
    #    which is what makes ``ceiling=3`` an honest head-hitter -- the
    #    genre's 2bc, and the only form of it this kernel can express.
    #    2.9 of arc is 2.22 m of ground against a walk's 2.4 m limit. It
    #    floats, because the moat one node back has just dug a bowl and a
    #    pedestal cannot stand in a hole.
    # 3. **A second stride, through the spill.** Soul sand runs at 2.51
    #    m/s against a normal 5.61, so this one is slow where the one
    #    before it was only low, and the two of them are the level's
    #    threshold: you *enter* the grove on foot and at half pace before
    #    you jump anything. Two walks in a row is legal and cheap -- each
    #    needs only its predecessor within 2.4 m of ground and half a
    #    block of height -- and this is where they belong, because a beat
    #    lays about half its nodes and the opening beat is the one that
    #    lays all of them. The level's whole non-hop share outside the
    #    filler is these two and the one in THE SPILL; without them it
    #    measures 93% plain hop against a rule of 85.
    # 4. **Up on to the first heap.** +1 at ``arc=3.0`` is a reach of
    #    2.32 centred in the 2.00-3.10 a one-block rise allows rather
    #    than pressed against the top of it: 3.6 reaches 2.92, so it is
    #    the arc that has to fall back, and a fallback is not ``exact``.
    #    From here to the bottom of the fall nothing touches the terrace.
    # 5. **Up the warped stem**, +1 again at 2.32, and out from the wall:
    #    ``hug`` goes 3.2, 3.2, 3.2, 3.4, 3.6, so the level steps out
    #    over the drop as it climbs and the stem stands clear with sky
    #    behind it. It keeps its pedestal and the pedestal is the picture
    #    -- a stem is a stem because there is a stalk under the cap, and
    #    a landing written floating here is a teal cube hanging in blue.
    # 6. **Off the top of the stem.** ``step_y=-2`` at ``arc=4.9``: a
    #    reach of 4.22 against a -2 window of 3.12-5.56, and the level's
    #    long jump, because a descent is the only long jump this motion
    #    model has -- falling takes time and the body does not slow down
    #    while it does. Level, a hop stops at 4.26 stand-point to
    #    stand-point and that is the whole envelope. It lands on a gold
    #    block hanging over the drop at ``hug=4.4`` with the sea under
    #    it, and it comes down to lift 1 rather than to the terrace: a
    #    ``step_y`` descent on to surface 1.0 is the terrace's own top
    #    cell, solid, refused, and the rest of the beat is abandoned
    #    behind it under the beat's own name.
    # 7. **Back in and up**, +1 at 2.32 on to a blackstone shelf against
    #    the cliff, under a ``cave``. The shell rides the beat's **last**
    #    node because a shell is painted the moment its landing commits
    #    and its roof then refuses the next arc of the same beat.
    ("crack", [n("glow", arc=3.2, lift=1, hug=3.2, spread=1, deco="lamp",
                 ceiling=3, moat=True, orbs=1),
               n("blackstone", arc=2.9, step_y=0, hug=3.2, kind="walk",
                 spread=0, ceiling=3, deco="lintel", pedestal=False),
               n("soulsand", arc=2.9, step_y=0, hug=3.2, kind="walk",
                 spread=0, ceiling=3, pedestal=False, orbs=1),
               n("rawgold", arc=3.0, step_y=1, hug=3.4, spread=0,
                 pedestal=False, orbs=1),
               n("warped", arc=3.0, step_y=1, hug=3.6, spread=0,
                 pedestal_style="warped", ceiling=3, orbs=1),
               n("gold", arc=4.9, step_y=-2, hug=4.4, spread=0,
                 pedestal=False, orbs=2),
               n("warped", arc=3.0, step_y=1, hug=3.4, spread=0,
                 pedestal_style="warped", shell="cave", deco="lamp",
                 orbs=1)]),
    # THE SPILL. The second beat and the quiet one: the heaps themselves,
    # crossed at the pace the spill sets. It opens at ``lift=2`` with
    # ``spread=1`` -- following the beat above that is free, following
    # machinery it costs a fallback, which the spread covers -- and
    # everything after the opener is on ``step_y``, so a beat that
    # started a block low still has the shape it was written with.
    #
    # 1. Up on to a raw-gold heap, lidded.
    # 2-3. **Two strides across the spill**, at positions two and three.
    #    Soul sand runs at 2.51 m/s against a normal 5.61, so the whole
    #    middle of this beat is slow, under a black lid three cells up --
    #    the genre's 2bc, and the only form of it this kernel can
    #    express, because an arc under a beam that low is refused every
    #    time and a walk has no arc. They are at two and three and not at
    #    the tail: a beat lays about half its nodes, so a non-hop verb
    #    written last is written and never seen. This beat and THE CRACK
    #    are where the level's non-hop share actually comes from -- with
    #    one walk apiece it measured 88% plain hop against a rule of 85.
    # 4. **Up on to the ingot over the pool**, +1 at a reach of 2.32,
    #    with lava cut under the jump and a ``cave`` over the landing.
    #    The ``moat`` and the ``shell`` share the beat's last node, which
    #    is legal and deliberate: ``_moat`` runs first and takes the
    #    footing out from under the shell's wall columns, so what is left
    #    is exactly the roof -- and a roof is what this level's frames
    #    are short of, not walls. The landing floats because a pedestal
    #    cannot stand in the bowl the moat has just dug. It is well over
    #    ten metres from the sill's pool: a moat digs a radius-three disc
    #    and a second one inside that radius stands in the first's hole.
    #    It ends at lift 3 and not 4 so that the filler after it opens on
    #    a legal descent -- 4 -> 2 is a drop of two and wants 3.12 m of
    #    reach, more than an opener that also has to be legal *up* one
    #    can ask for.
    ("spill", [n("rawgold", arc=3.4, lift=2, hug=3.2, spread=1, ceiling=3,
                 orbs=1),
               n("soulsand", arc=2.9, step_y=0, hug=3.2, kind="walk",
                 spread=0, ceiling=3),
               n("soulsand", arc=2.9, step_y=0, hug=3.4, kind="walk",
                 spread=0, orbs=1),
               n("gold", arc=3.0, step_y=1, hug=3.6, spread=0,
                 pedestal=False, moat=True, shell="cave", deco="lamp",
                 orbs=2)]),
], filler=[
    # THE THICKET. The filler repeats and a script's tail does not, so
    # this is what the level mostly *is*, and it is therefore the only
    # place where "half the jumps are at ground level" can actually be
    # answered. It is a **cycle and not a line**: 2 -> 2 -> 3 -> 1, up on
    # to a stem, along it at soul-sand pace, up on to a heap, and then
    # **off the side of the heap, two blocks down** on to a low ingot in
    # the nylium. Three of its four landings are off the floor and the
    # fourth is a *fall* rather than a stroll -- the reference travels
    # eleven blocks vertically to gain four and does almost all of it by
    # coming off edges, and 36 of its 43 legs descend somewhere.
    #
    # The fall is also load-bearing for the way out, and that is the
    # least obvious line in this file. The exit's reserve is
    # ``(need + 1) * 3.2`` metres of terrace measured from **wherever the
    # body is standing when the trigger fires**, and ``exit_beats`` is a
    # fixed list that cannot shrink to match: a loop that handed the
    # chasm a body at lift 3 would reserve six landings' worth of terrace
    # and then lay nine, and the stair would run out of ground short of
    # the lip. Ending the lap low is what keeps the two numbers in step.
    #
    # The opener is 3.4 m because it has three heights to be legal from:
    # a reach of 2.72, inside the window at +1 (2.00-3.10), level
    # (2.00-4.26) and -1 (2.35-4.98). It follows the spill's shelf at
    # lift 3, or a piece of machinery back down on the terrace at lift 1,
    # or the loop's own last landing at lift 1, and it is the same jump
    # from all three. That seam is checked like any other jump and half
    # of what a filler ever loses is there.
    #
    # The walk is at position **two** for the reason above, and the last
    # node carries no lid on purpose: it is the landing at the bottom of
    # a two-block fall, and what should be over it is the drop it came
    # off rather than a beam.
    #
    # **No ``moat`` anywhere in here.** The filler loops, and the second
    # lap digs away the ground the first lap's pedestals are standing on
    # -- 27,859 "pedestal will not stand" refusals from one keyword when
    # it was instrumented elsewhere. This level's two pools are in beats
    # that play once.
    ("thicket", [n("warped", arc=3.4, lift=2, hug=3.0, spread=1,
                   pedestal_style="warped", ceiling=3, orbs=1),
                 n("soulsand", arc=2.9, step_y=0, hug=3.0, kind="walk",
                   spread=0, ceiling=3),
                 n("rawgold", arc=3.2, step_y=1, hug=3.4, spread=0,
                   pedestal=False, orbs=1),
                 n("gold", arc=4.4, step_y=-2, hug=3.8, spread=0,
                   pedestal_style="rawgold", orbs=2)]),
], exit_beats=[
    # THE TREASURE STAIR. The hoard is piled against the cliff at the end
    # of the terrace and warped stems have grown up through it; the way
    # out is up the pile, and the stair is gold and stem alternating on
    # black plinths -- a lit block of paving at the foot, seven treads,
    # and a glowstone curb at the head to stand on before the leap across
    # the chasm.
    #
    # **The arithmetic, which is the thing that was wrong here before.**
    # The terrace above stands ``rise`` = 8 blocks over this one, so its
    # walking surface is 9.0 against this level's 1.0; the crossing is a
    # ``hop_span(-1)`` jump and wants a block to spend coming down, so
    # the head of the stair has to stand at **lift 9**, a walking surface
    # of 10.0. From the launch at lift 2 that is seven treads of +1 and
    # there is no way to buy any of them back -- nothing in this motion
    # model rises two in one ballistic move, and a slab landing at +0.5
    # buys reach rather than height. A stair that stops short is not a
    # short stair: the crossing is refused, ``_climb_on`` lays another
    # step, and the level grinds at the chasm for a dozen landings.
    #
    # **Only the launch is written on ``lift``; every tread is on
    # ``step_y``, and that is not a style preference.** ``_node`` clamps
    # ``lift`` to ``LIFT_MAX``, which is **6** -- so a stair written as
    # lift 2, 3, 4 ... 9 is a stair whose last three treads are all lift
    # 6, three level hops in a row, and a crossing then asked to rise
    # three. Measured, that version of this file laid **755 landings over
    # eight runs against the old design's 195**, 342 of them the exit
    # grinding at a chasm it could not reach, with thirteen unchecked
    # emergency placements behind it. ``step_y`` is an absolute rise
    # between walking surfaces and is not clamped, which is why every
    # climb in the generator is written with it.
    #
    # The launch *is* on ``lift``, at 2 with ``spread=1``, because it is
    # the anchor the seven relative treads are counted from: the filler
    # hands the chasm a body at lift 1 by design (see THE THICKET), the
    # launch is one step up off it, and seven treads then land the head
    # at lift 9 -- a walking surface of 10.0 against the terrace above's
    # 9.0, with the crossing coming down that block. A flat sprint jump
    # reaches 4.26 m and dropping one buys nearly another metre, so the
    # crossing wants that block to spend. Launching at lift 2 rather than
    # at 1 is worth a whole landing of the level, and lift 2 is the
    # highest it may be: the trigger can also fire on a body at lift 1,
    # and nothing rises two in one ballistic move.
    #
    # **Every tread keeps its pedestal**, and the keyword is the picture
    # rather than a nicety: a pedestal writes the stack under a landing
    # all the way down to the terrace, which on a staircase up a treasure
    # heap *is* the heap. Floating the top half instead measured 59% of
    # this level's landings hanging in air against 33% with the stacks
    # in, and the contact sheet's last third was cubes over the sea. The
    # plinths are named ``blackstone`` so the stack and the lid over it
    # are the dark mass and only the tread itself is gold or stem.
    #
    # The lids are on the **top four** treads and not on alternate ones.
    # The bottom of the stair stands against the cliff and has the brow
    # of the level above over it already; it is the head, eight and nine
    # blocks up, that frames as sky. A lid within eight blocks of the
    # head also makes ``_indoor_want`` return 0.85 and takes 27% off
    # every tint in the frame, so lidding all eight would make a dark
    # level whatever ``dark`` says. (Honest note: swapping the lids from
    # alternate to top-weighted moved ``frame empty`` by under a point on
    # two seeds. It is kept because the *sheet* is better, and because
    # the probe's ray fan reaches only 4.6 m above the eye and cannot see
    # most of what a lid is for.)
    #
    # **The launch stands at ``hug=2.9``.** One level measured 69
    # wall-jammed frames of 1,293 with its launch at 2.2 and **0 of
    # 1,280** at 2.8: the camera locks on to the landing through take-off
    # and flight, so a launch tucked against the core aims the whole
    # climb at the cliff. The stair then *zigzags* -- 2.6, 3.1, 2.6, 2.9,
    # 2.4, 2.9, 3.2 -- because a hugging node's ``radial`` is never read,
    # so the only weave available to it is in ``hug``, and a straight
    # column of identical hops is the single most monotonous thing this
    # format produces. The head stands furthest out, with sky behind it,
    # because the last thing before the leap into DUST DEVILS should be a
    # lit stone against the slot and not against rock.
    #
    # **Do not flatten that zigzag.** Softening the top three from
    # 2.9/2.4/2.9 to 3.0/2.6/3.0 -- a change of two tenths of a block --
    # took seed 7 from 486 frames on the level with **0.2%** of them
    # jammed by a wall to **703 frames and 14.8%**, with seed 3 unmoved.
    # Same seeds, one edit, nothing else touched. The stair is threading
    # a corridor between the cliff and the drop and there is less slack
    # in it than the numbers suggest; re-measure both seeds after any
    # change here.
    n("glow", arc=3.6, lift=2, hug=2.9, spread=1, confine=True,
      deco="lamp", ceiling=3, shell="cave", orbs=1),
    n("gold", arc=2.9, step_y=1, hug=2.6, spread=0,
      pedestal_style="blackstone", orbs=1),
    n("warped", arc=2.9, step_y=1, hug=3.1, spread=0,
      pedestal_style="blackstone"),
    n("gold", arc=2.9, step_y=1, hug=2.6, spread=0,
      pedestal_style="blackstone", orbs=1),
    n("warped", arc=2.9, step_y=1, hug=2.9, spread=0,
      pedestal_style="blackstone", ceiling=3),
    n("gold", arc=2.9, step_y=1, hug=2.4, spread=0,
      pedestal_style="blackstone", ceiling=3, orbs=1),
    n("warped", arc=2.9, step_y=1, hug=2.9, spread=0,
      pedestal_style="blackstone", ceiling=3),
    n("glow", arc=2.9, step_y=1, hug=3.2, spread=0,
      pedestal_style="blackstone", deco="lamp", ceiling=3, orbs=2),
])
