"""Level 22: THE PILLARS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE PILLARS. The broken colonnade on the approach to the gate. An
# orchid-violet purpur court laid along the rim, a row of obsidian
# pillars standing out of it, and most of them snapped -- the architraves
# they carried are down across the paving, the ground between them has
# gone into the void, and two eroded rust-red hoodoos are all that is
# left standing at full height until the last pillar at the end.
#
# The route, in one breath. A sea lantern flush in the paving with black
# water cut round it -- the palette stops being level 21's red netherrack
# and orange shroomlight at that one block. **On foot** under a fallen
# lintel, up two broken stumps, and then **out along the colonnade**: a
# half-height architrave slab thrown 4.2 m outboard, two pillar caps
# climbed at the rim with the drop a metre off the shoulder, and off the
# top of the last one -- **two blocks down and 5.2 m of arc back in**,
# which is the level's long jump and the only kind of long jump this
# motion model has. It lands lit, under a rough roof. Then the shattered
# stand: a second pool, two plinths up, and a leap out to a rim pillar.
# The court repeats for as long as the terrace lasts, and the way out is
# the last pillar, which is hollow and full of water.
#
# The one thing a viewer would remember is the run out along the
# colonnade and the fall off the end of it.
#
# ---------------------------------------------------------------------
# **This is an End level and it has to look like one, which means it may
# not look like the sky.** The version this replaces skinned the ground
# ``endstone`` -- (216,214,156), pale cream -- under a bright blue sky
# dome, with grey cone stone showing through and pale lilac purpur
# standing on it. Every value in the frame was within about thirty of
# every other and the contact sheet came back as a wash. The palette is
# inverted here: **purpur is the floor** (166,128,172, a mid-value
# orchid nothing else in the tower is), endstone is demoted to the pale
# *plinths and route stripe* laid through it, and **obsidian is the one
# thing that stands up or hangs overhead**. That is the reference's own
# composition -- one committed hue in the bottom of the frame, dark rock
# across the top, sky as a slot between them -- and it is also the
# inverse of THE GATE eleven levels up, which is a pale endstone
# causeway with a black gate on it. Same theme, opposite picture.
#
# **Every lid in this level is free black mass.** ``Course._node`` writes
# a ``ceiling`` lid as ``pedestal_style or theme.rock`` and a
# ``deco="lintel"`` beam as ``theme.rock``, so with ``rock="obsidian"``
# the head-hitters, the beams and the shell roofs are all near-black
# without a single ``pedestal_style`` being named. Lids are on about half
# the landings and not all of them, because a lid within eight blocks of
# the head makes ``_indoor_want`` return 0.85 and takes 27% off every
# tint in the frame. The ones that carry them are the enclosed
# stretches; the colonnade caps deliberately have nothing over them,
# because a black pillar top is only legible with sky behind it.
#
# **The light is cold and there are four of them.** ``sealantern``
# (198,226,216) rather than the theme's ``lantern``: it is the only pale
# cold source in ``spiral._GLOWING`` -- ``lantern``, ``torch``,
# ``glowstone``, ``sealantern`` and ``magma`` are the whole list, and
# every other one is warm. THE GATE keeps the warm one for its fire, so
# the two End levels do not light the same way either. The four are at
# the threshold, at the foot of the long fall, at the foot of the exit
# and at the top of it: every lamp in the reference is at an end of
# something and doing a job.
#
# **``dark`` and ``sky`` are lifted off the base theme.** The ring light
# is ``mix(white, sky, 0.35 + 0.45 * dark)`` multiplied over everything,
# and ``end``'s own (46,38,66) at 0.62 is a 48% violet-grey: obsidian
# under it is (27,22,37), a hole with no faces, and purpur is a muddy
# grey-mauve. (88,72,132) at 0.45 is 64% -- purpur reads as (106,80,110),
# obsidian as (36,29,50), a dark shape you can still see the courses in,
# and the cone's own stone at (56,54,52) is *darker* than the level's
# floor rather than the same value, which is what stops the terrace
# reading as cliff.
#
# **The hoodoo is terracotta and cannot be re-skinned**, and rather than
# fight that the floor is salted with it. ``_lm_g_hoodoo`` names
# ``terra_red``, ``terra_orange`` and ``terra_white`` literally whatever
# the theme is (RULES 7), so a level carrying it gets two rust spires
# from another biome standing in it -- which is exactly how the last
# contact sheet read. Rust and white terracotta are in the floor
# palette now, as grit weathered off the spires, and against a violet
# court and black pillars the warm orange is a *complement* rather than
# a clash: it is the only warm thing in the level, which makes it the
# thing the eye goes to, which is what a landmark is for.
#
# **Fourteen floor materials.** A real leg of the reference uses a median
# fourteen with the commonest at about a quarter; this level had the
# theme's stock ten, nine of which are pale. Purpur is the dominant at
# about a quarter with endstone, obsidian, blackstone and chorus under
# it and calcite, quartz, diorite, amethyst, sculk and the terracotta
# grit in the tail.
#
# ---------------------------------------------------------------------
# **The shape: two beats and a filler, and the first beat is the level.**
# Everything past about the fifth authored beat is never laid and a level
# only gets nine to twelve landings, so the previous four-beat script was
# writing seventeen landings and showing eight of them -- its ``tarn``
# and ``architrave`` beats measured 83% and 89% and were the two nobody
# ever finished. THE VAULT's evidence is that an *opening* beat is never
# truncated at all (149 landings asked, 149 laid, over 24 runs), because
# it never competes with anything for terrace. So the threshold, the
# climb, the showpiece and the fall are one seven-node beat, and the
# level's character is in a four-node filler that loops.
#
# **It gets off the floor inside its first beat, and that is not only a
# composition argument.** ``_feat_ascent`` returns nothing but the
# crossing when ``need <= 0``, and ``need`` is the next level's floor
# minus wherever the body actually got to -- so on the tallest rise in
# the roster (seven) a design that spends its whole length at lift 1
# reserves and then spends forty per cent of itself on a staircase.
# Beat 1 reaches lift 4 and the filler cycles 1 -> 3 rather than running
# flat, which is what leaves the bubble three or four blocks to find
# instead of six.
#
# **The level descends twice, and never after its high point.** Off the
# top of the colonnade (-2), and again every lap of the filler where the
# loop's seam falls two blocks back on to the paving; both inside the
# first two thirds, and the exit is the highest thing here with nothing
# after it going down. The real map travels eleven blocks vertically to
# gain four and does it by falling off edges, and 36 of its 43 legs
# descend somewhere.
#
# **``breaks=0``, which is the largest single measurement in this file.**
# Any ``breaks >= 1`` forces the lock, because a level's first floor
# break is always 5.5-6.7 m wide -- and the lock is an approach at
# height, an island floated over the hole and a landing on the far
# ground, four or five landings out of the nine or ten a level gets. On
# a level that is *also* paying for a gated-landmark crossing that is two
# thirds of everything laid, and the blueprint's elevation said so before
# any number did: a flat line at lift 1 the whole width of the level with
# the design squeezed into two bumps. Measured, same seeds, only
# ``breaks`` swapped:
#
#   | breaks | designed | machinery | hop | empty frame | walker |
#   |--------|----------|-----------|-----|-------------|--------|
#   | 3      | 54%      | 46%       | 84% | 43%         | 12%    |
#   | **0**  | **66%**  | **34%**   | **82%** | **41%**  | 15%    |
#
# It is better on every count including the frame, which is the one it
# was expected to cost -- the note that a lock's approach stack fills the
# corridor ahead of the body is a *plaza* observation and does not
# survive a course that already stands its own pillars there. What holds
# the no-jump walker instead is water in **holes**: two ``moat``
# landings, each swapping the terrace's top cell for water over a
# radius-three disc. Liquid on its own is atmosphere -- water is
# see-through and lava is solid, so neither blocks a walker -- and it is
# the bowl the moat digs that stops one, because a walker can get into it
# and cannot step back out. 15% mean against a 55% ceiling and the real
# map's own 46%, and 0 of 7 walks reach the end.
LEVEL = Level("THE PILLARS", "end", rise=7, gap=3.2, exit="bubble",
              band=12.0, shelf=5.5, breaks=0, landmark="hoodoo",
              # Violet court, pale plinths, black colonnade, chorus for
              # the growth on it, cold light, and water in the two holes
              # the paving has fallen through.
              ground="purpur", sub="endstone", rock="obsidian",
              accent="chorus", glow="sealantern", liquid="water",
              dark=0.40, sky=(104, 88, 154),
              floor=(("purpur", 3), ("endstone", 3), ("obsidian", 2),
                     ("blackstone", 2), ("chorus", 2), ("calcite", 1),
                     ("quartz", 1), ("diorite", 1), ("amethyst", 1),
                     ("sculk", 1), ("stone", 1), ("deepslate", 1),
                     ("terra_white", 1), ("terra_orange", 1)),
              props=("chorus", "endrod", "pebbles", "lanternpost"),
              # If the water column will not anchor, the fallback stair
              # climbs the colonnade's own stone rather than the cliff.
              step=("obsidian", "hop"), beats=[
    # THE COLONNADE -- the threshold, the climb, the showpiece and the
    # fall, all in one beat, because this is the only stretch of the
    # level that is laid whole on every visit.
    #
    # Everything behind the opener is written on ``step_y`` rather than
    # on ``lift``. ``lift`` is measured from the terrace, so a beat whose
    # opener came down a block high or low -- it carries ``spread``, so
    # it does, about a fifth of the time -- then asks for a rise of two,
    # which nothing in this motion model makes. ``step_y`` is measured
    # between *walking surfaces* and is true wherever the body actually
    # is.
    #
    # 1. The sill. A sea lantern set flush in the purpur on a rise, with
    #    black water cut round it and an obsidian beam three cells over
    #    it: light, lid and a complete change of palette at one block,
    #    with no blend, which is how the reference signposts a level.
    #    Below is BASALT FLUES -- red netherrack, orange shroomlight, a
    #    nine-block plaza; here it is violet, cold white and black at
    #    twelve.
    # 2. Under the fallen lintel, on foot. **A doorway is walked and
    #    never jumped**: one impulse always rises 1.25 m and the head
    #    then sweeps the two cells above every take-off, so an arc under
    #    a lid low enough to read as a beam is refused every time. Over a
    #    ``walk`` there is no arc at all, which is what makes
    #    ``ceiling=3`` an honest head-hitter -- the genre's 2bc, and the
    #    only form of it this kernel can express. It is at position two
    #    and not one because a walk needs its predecessor within half a
    #    metre and a beat's first landing is placed from wherever the
    #    machinery between beats left the body. It floats: the moat has
    #    just dug a radius-three bowl and a pedestal cannot stand in a
    #    hole.
    # 3. Up on to the first broken stump. +1 at ``arc=3.2``, a reach of
    #    2.55 centred in the 2.00-3.10 a one-block rise allows rather
    #    than pressed against the top of it -- 3.6 reaches 2.92, so it is
    #    the arc that has to fall back, and a fallback is not exact.
    # 4. **Out on to the architrave**, 4.2 m of arc and 1.2 m of ``hug``
    #    outboard in one jump: a reach of 3.69 against a level window of
    #    2.00-4.26, and the longest flat jump in the level. It is a
    #    ``slab``, which is what an architrave is -- a half-height beam
    #    slung between two pillars -- and stairs and slabs are the
    #    commonest non-cube form in the reference by a wide margin. On
    #    ``step_y=0`` it is a level jump on to a thinner stone, not the
    #    -0.5 step a slab written on ``lift`` would be.
    # 5-6. Up the colonnade, two caps at +1 out near the shelf edge --
    #    the drop is a metre off the shoulder and the core wall is four
    #    behind, which is the reference's groove. **These two are the
    #    only landings in the level that keep a pedestal**, and the
    #    keyword is the picture rather than a nicety: a pedestal builds
    #    the stack under a landing all the way down to the terrace, which
    #    on a level called THE PILLARS is the pillar. Written floating
    #    like everything else they were two cubes hanging in blue sky --
    #    86% of this level's landings floated and the contact sheet's
    #    middle third was cubes against nothing. ``pedestal_style`` makes
    #    the shaft obsidian under a chorus cap.
    #
    #    They cost fidelity and the cost was measured. A pedestal on a
    #    ``ledge`` has to find ground under a shelf that wobbles about
    #    +/-1.3 and has holes in it, so it is refused where a floating
    #    landing is not: five pedestals across the three beats took
    #    exactness from 100% to 90% with ``stand`` at 77%, and the exit
    #    climb grew by ten landings behind the beats that gave up. These
    #    two, at ``hug`` 4.0 and 3.8 where the shelf is reliable, cost
    #    nothing at all -- every beat is back at 100% with them in. The
    #    other three are gone.
    #
    #    Neither carries a lid: a black pillar cap is only legible with
    #    sky behind it, and this is the one stretch of the level that
    #    should frame as a slot of sky between the cliff and the void.
    # 7. **Off the end of the colonnade.** ``step_y=-2`` at ``arc=5.2``
    #    with 1.4 m of ``hug`` coming back in: a reach of 4.71 against a
    #    -2 window of 3.12-5.56, and it is written as a descent because a
    #    descent is the only long jump this model has -- level, a hop
    #    stops at 4.26 stand-point to stand-point. It lands lit, on a
    #    pale endstone block with nothing under it, under a ``cave``.
    #    The shell is on the beat's **last** node because a shell is
    #    painted the moment its landing commits and its roof then refuses
    #    the next arc of the same beat; at lift 2 it grows a roof and
    #    open sides, which is what is wanted -- what this sheet is short
    #    of is not walls but the dark brow across the top of the frame.
    #    It does **not** come down to surface 1.0: that is the terrace's
    #    own top cell, solid, and a ``step_y`` descent on to it is
    #    refused with the rest of the beat abandoned behind it.
    ("colonnade", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1,
                     deco="lamp", ceiling=3, moat=True, orbs=1),
                   n("rock", arc=2.9, step_y=0, hug=3.0, kind="walk",
                     spread=0, ceiling=3, deco="lintel",
                     pedestal=False),
                   n("sub", arc=3.2, step_y=1, hug=3.4, spread=0,
                     pedestal=False, orbs=1),
                   n("rock", arc=4.2, step_y=0, hug=4.4, form="slab",
                     spread=0, pedestal=False, orbs=2),
                   n("rock", arc=3.2, step_y=1, hug=4.0, spread=0,
                     pedestal_style="obsidian", orbs=1),
                   n("accent", arc=3.2, step_y=1, hug=3.8, spread=0,
                     pedestal_style="obsidian", orbs=1),
                   n("sub", arc=5.2, step_y=-2, hug=3.0, spread=0,
                     pedestal=False, deco="lamp", shell="cave",
                     orbs=2)]),
    # THE STAND. The second pool, a stride under a second fallen lintel,
    # and two broken plinths climbed out of the water to the highest
    # ground in the body of the level. Four nodes, because a beat written
    # after the opener gets about half of what it asks for and a fifth
    # node here is a node nobody sees -- written as five, with an outward
    # leap on the end, it measured 20 landings of 26 where four measure
    # 29 of 29.
    #
    # It ends **high**, and that is worth more than the leap was.
    # ``_feat_ascent`` returns nothing but the crossing when ``need <=
    # 0``, and ``need`` is the next level's floor minus wherever the body
    # actually got to -- so a beat that hands the chasm a body at lift 3
    # is a beat that has already paid for part of the way out.
    #
    # The moat is on the beat's **first** node, which is the opposite of
    # what the radius-three bowl usually wants -- but a beat's tail is
    # almost never laid, so a pool written second is a pool authored and
    # never seen, and the two landings after it float, so the bowl cannot
    # take the ground out from under them. It is well over ten metres
    # from the sill's pool: a moat digs a radius-three disc the moment
    # its landing commits and a second one inside that radius stands in
    # the hole the first dug.
    #
    # **The water is not decoration and it is not for the atmosphere.**
    # ``end`` has no liquid of its own, and the one this level borrows is
    # chosen for its physics: water is in ``SEE_THROUGH``, so the bowl a
    # moat digs is a *pit* a no-jump walker falls into and cannot climb
    # back out of. Lava is solid and a walker strolls across the top of
    # it. With no floor breaks in the level at all these two pools are
    # the whole of what stops one, and they hold it to 15%.
    #
    # The walk is at position **two** for the same reason it is in beat
    # one: a beat lays about half its nodes, so a non-hop verb written at
    # a beat's tail is written and never seen, and one written first
    # follows machinery at an arbitrary height where a walk needs its
    # predecessor within half a metre. This third stride is what took the
    # hop share off the 85% limit -- 87% with two walks in the level, 82%
    # with three.
    #
    # The shell rides the beat's **last** node, because a shell is
    # painted the moment its landing commits and its roof then refuses
    # the next arc of the same beat. At lift 3 it grows a roof and open
    # sides -- ``_shell`` skips a wall column with nothing under it --
    # which is what is wanted: what this sheet is short of is not walls
    # but the dark brow across the top of the frame.
    ("stand", [n("ground", arc=3.4, lift=1, hug=3.0, spread=1,
                 moat=True, ceiling=3, orbs=1),
               n("rock", arc=2.9, step_y=0, hug=3.0, kind="walk",
                 spread=0, ceiling=3, deco="lintel", pedestal=False),
               n("accent", arc=3.2, step_y=1, hug=3.4, spread=0,
                 pedestal=False, orbs=1),
               n("sub", arc=3.2, step_y=1, hug=3.8, spread=0,
                 pedestal=False, shell="cave", orbs=2)]),
], filler=[
    # THE COURT. The filler repeats and a script's tail does not, so this
    # is what the level mostly *is*, and it is therefore the only place
    # where "half the jumps are at ground level" can actually be
    # answered. Four nodes and not three, so that the loop is a **cycle**
    # rather than a line: it climbs two and falls two every lap, and the
    # body spends the level between lift 1 and lift 3 with the violet
    # paving under it rather than running flat at lift 1 with sky under
    # two thirds of the view.
    #
    # The opener is 4.4 m because it has three different heights to be
    # legal from -- a reach of 3.72, inside the window at level
    # (2.00-4.26), at -1 (2.35-4.98) and at -2 (3.12-5.56). It follows
    # the stand's rim pillar, or the loop's own last landing, or a piece
    # of machinery back down on the terrace, and it is the same jump from
    # all three. The loop's seam is checked like any other jump and half
    # of what a filler ever loses is there: -2 from the chorus stone
    # across 4.4 of arc.
    #
    # The walk is at position **two**. A beat lays about half its nodes,
    # so a non-hop verb written at a beat's tail is written and never
    # seen, and one written first follows machinery at an arbitrary
    # height where a walk needs its predecessor within half a metre.
    # This one, the doorway in beat 1 and the stand's stride are the
    # whole of the level's non-hop share outside the exit, and they are
    # the right three: cobweb appears zero times in the entire reference
    # save, honey has no physics here at all, ice is another level's
    # speciality, and the slime pad placed on 6 runs of 24 and fired on 1
    # when it was measured.
    #
    # The last node has no lid on purpose. It is the top of the loop, it
    # is the landing the eye is on when the body is highest, and a
    # ``ceiling`` there is the one place in the level where overhead mass
    # costs more than it buys: a lid within eight blocks of the head
    # makes ``_indoor_want`` return 0.85 and takes 27% off every tint in
    # the frame, and this beat repeats.
    #
    # **No ``moat`` anywhere in here.** The filler loops, and the second
    # lap digs away the ground the first lap's pedestals are standing on
    # -- 27,859 "pedestal will not stand" refusals from one keyword when
    # it was instrumented. This level's water is in the two beats that
    # play once.
    ("court", [n("ground", arc=4.4, lift=1, hug=3.0, spread=1,
                 ceiling=3, orbs=1),
               n("rock", arc=2.9, step_y=0, hug=3.0, kind="walk",
                 spread=0, ceiling=3, deco="lintel"),
               n("sub", arc=3.2, step_y=1, hug=3.2, spread=0,
                 pedestal=False, orbs=1),
               n("accent", arc=3.4, step_y=1, hug=3.4, spread=0,
                 pedestal=False, orbs=1)]),
], exit_beats=[
    # THE LAST PILLAR. The colonnade's one unbroken shaft, and it is
    # hollow: the water that has flooded the court stands in it and
    # pushes you seven blocks out of the top. Three landings written out
    # rather than left to the generated climb, which hangs its column
    # mid-lane at ``hug=2.0`` with no pedestal, finds nothing within a
    # cell of its middle index to anchor on, and is refused silently --
    # 11,097 of 13,000 candidates when it was instrumented -- after which
    # the level gets a seven-step staircase and is never told.
    #
    # **It is water and not a ladder, and that is not a preference.**
    # Bucketed by segment *and* move over four seeds, an ``ascent/climb``
    # ride measured **20.9% of its frames with a wall in the lens** where
    # every other move in the same level measured 0.0%: a ladder is
    # ridden at 2.35 m/s with the column a hand's width from an
    # eighty-degree lens, and the wall it hangs on *is* the wall in the
    # frame. ``hug`` on a climb node is inert, so it is not tunable. A
    # bubble goes up at **11.0 m/s** -- seven blocks is under a second --
    # and one level measured the swap at 14.9% jammed to 6.6% at no
    # other cost.
    #
    # It is also the level's idea rather than a way out of it. RULES 3
    # asks for a climb exit on about one level in five and this tower
    # overshot it badly; a level called THE PILLARS whose last pillar is
    # the one you go up the inside of is what that rule is for. It is
    # what lets the level stay in its groove as well: on the tallest rise
    # in the roster a staircase is seven landings of the nine or ten the
    # level gets, and declaring a non-stair exit hands ``_level_budget``
    # back ``(need - 2) * 3.2`` metres of terrace for the design.
    #
    # **``pedestal=True`` is the load-bearing keyword and the reason this
    # fires at all.** ``_climb_move`` wants solid rock within one cell of
    # the column at its middle index *and* at its top; out in the lane
    # the only candidate is the landing's own stack, so the column needs
    # a pedestal under it and a rise of at least four. The stack is the
    # pillar's own obsidian casing. There is deliberately **no**
    # ``shell="shaft"`` round it: the tube is what puts the body inside
    # the wall, and taking one off elsewhere took body-inside-the-world
    # from 3 frames of 556 to 0 and the jam from 18.2% to 10.4%. And
    # there is no ``ceiling`` on the climb node, because a lid stands in
    # the column, ``_climb_move`` finds nothing to hang on, and the climb
    # silently becomes ordinary hops with the per-beat table still
    # reading 100%.
    #
    # **The launch stands at ``hug=2.9``.** One level measured 69
    # wall-jammed frames of 1,293 with its launch landing at 2.2 and
    # **0 of 1,280** at 2.8, and only the launch landing matters. The
    # camera locks on to the landing through take-off and flight, so a
    # launch tucked against the core aims the whole ride at the cliff.
    # It carries a ``cave`` for the frame rather than for the climb: the
    # exit is the emptiest third of any level in this tower and roofing
    # the landing it leaves from is the single biggest win available
    # there.
    #
    # The last landing is out at ``hug=3.6`` with sky behind it rather
    # than tucked against the core, for the same reason: the last thing
    # before the leap into SPORE HOLLOW should be a lit stone against the
    # sky and not a cliff.
    #
    # The arithmetic of the height: the lip is lift 1, the column gains
    # six, the head of it steps up one -- a walking surface of 9.0 against
    # the next terrace's 8.0, which is exactly this level's ``rise`` of
    # seven, and the crossing comes down that block on to it. A flat
    # sprint jump reaches 4.26 m and dropping one buys nearly another
    # metre, so the crossing wants that block to spend. A climb that
    # overshoots is a level above that opens by dropping back to its own
    # terrace, which is the owner's "it puts a ladder there and then
    # jumps back down to a lower part".
    #
    # **Check ``--report``'s move mix for the word ``bubble``.** If it is
    # missing, this is a seven-step staircase and the level has no way
    # out of its own idea. It reads 5% here.
    #
    # One recorded non-finding, because it looks like a lead and is not.
    # This level measures **one frame of 475 with the body 0.50 m inside
    # the cone**, and the obvious suspect is the column at ``hug=2.4``
    # clipping the core's lean. Moving it to 2.8 changed *nothing* -- not
    # the frame, not the jam, not that one frame, not a single number in
    # the report. ``hug`` on a climb node is inert, exactly as RULES 7
    # says, and the residue is the documented 0.1% of cells at hug
    # 1.8-4.2 that come out as rock. It is left at 2.8 because that is
    # where it happens to be written and there is no reason to move it
    # back.
    n("glow", arc=3.2, lift=1, hug=2.9, spread=2, confine=True,
      deco="lamp", ceiling=3, shell="cave", orbs=1),
    n("rock", arc=2.4, step_y=6, kind="bubble", hug=2.8, pedestal=True,
      pedestal_style="obsidian", spread=0, orbs=2),
    n("sub", arc=3.2, step_y=1, hug=3.6, spread=0, pedestal=False,
      deco="lamp", ceiling=3, orbs=2),
])
