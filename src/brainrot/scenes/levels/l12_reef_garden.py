"""Level 12: REEF GARDEN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A reef flat at the lip of the drop-off, standing under one enormous
# red coral head.
#
# One sentence: *the ground is a tide shelf and the pools in it are
# holes.* You come in over a sea lantern set flush in the sand, sprint
# under the reef overhang with the first pool cut out beneath you, climb
# the coral out of it, and then fall two blocks into the lagoon onto a
# sponge that throws you two blocks back out -- the only move in this
# engine that gains two, and the thing a viewer would remember if the
# great cap were not standing over the whole level. The way out is the
# blue hole: an upwelling in a prismarine well, ridden up rather than
# walked up.
#
# **The great cap is why this level is a ledge and not a channel.** It
# was a channel with ``band=12.5`` before this pass, and the bill was
# exact: a channel cuts two cells of liquid at 3.6 out from the core,
# which is where ``Course.lane_radius`` puts the running line, so
# ``Cone.rock`` is False under the lane and a gated structure's base
# cells never find footing. Measured on the old design over eight runs:
# the level held its own landmark on screen for **0.4 s** against the
# 1.5 s rule and **0.0 s counted from the approach in** -- it paid for
# the gate and got nothing at all. ``greatcap`` is a *hop* gate, and hop
# gates reserve 8 of 8 on a ledge, so the ledge is the profile that
# actually shows it. The water comes back as moats, which is the
# reference's own way of doing it anyway: liquid in a **hole**, under
# the jump, rather than a ribbon painted beside it. It is the hole and
# not the liquid that stops a walker.
#
# And a ledge is the right shape for a reef besides. A reef flat *is* a
# shelf that ends in a wall and plunges: banded prismarine cliff at your
# back, four or five cells of pale sand under you, the blue outboard.
# That is also the reference's own groove -- rock within four metres on
# one side on 71% of its samples, the drop on the other -- and it is the
# single most reliable thing a level can do about being walkable, since
# there is nothing to walk *around*.
#
# ``breaks=0``, and that follows from the same choice. Any ``breaks >=
# 1`` forces the lock, which lays eighteen blocks of arc in one decision
# and cost this level three of its landings a visit; a reef flat does
# not want holes chopped through it, it wants pools. The walk number is
# held down by the shelf's own edge and by the three moats instead --
# the trade RULES 7 measures at 65.8% -> 25.8% on identical worlds.
#
# The seam is half the point. Level 11 is black rock, a red sky and lava
# pressed against the wall; level 13 is sculk and the dark. This is the
# one bright level between them: pale sand, blue water, a cyan sky, and
# the palette changes completely at the sea lantern in the first beat.
#
# The accent is ``coral_red`` on purpose. ``_lm_g_greatcap`` names its
# own materials -- ``mushroomstem`` and ``mushroomred`` (196, 66, 58) --
# whatever the level's theme is, and ``coral_red`` is (202, 62, 72). So
# the structure reads as a giant red coral head standing in a reef of
# the same colour rather than as a mushroom that wandered in from
# another biome, and the course runs *under* its cap.
LEVEL = Level("REEF GARDEN", "coral", rise=6, gap=2.8, exit="bubble",
              band=11.0, profile="ledge", shelf=4.5, breaks=3,
              landmark="greatcap",
              ground="sand", sub="sandstone", rock="prismarine",
              accent="coral_red", glow="sealantern", liquid="water",
              step=("prismarine", "hop"),
              props=("coralfan", "lilypad", "vinehang", "pebbles",
                     "grasstuft", "flower"),
              # Twelve materials and no one of them over a fifth. The
              # identity of a level is its floor, and a reef flat is not
              # a sand plate: it is sand with coral rubble ground into
              # it, gravel where the surge sorts it, clay and moss in
              # the wet cells, calcite shell grit, and enough prismarine
              # that the terrace still reads as cut out of the same rock
              # as the cliff behind it.
              floor=(("sand", 3), ("sandstone", 2), ("gravel", 2),
                     ("coral_pink", 2), ("coral_red", 2), ("prismarine", 2),
                     ("darkprismarine", 1), ("clay", 1), ("moss", 1),
                     ("calcite", 1), ("coral_blue", 1), ("stone", 1)),
              beats=[
    # The threshold, and three ideas in three landings rather than three
    # hops at one height.
    #
    #   0. a sea lantern laid flush in the sand as a half step. The
    #      light to aim at and the complete change of palette off the
    #      foundry below.
    #   1. the reef overhang: a lid three cells over the take-off,
    #      *walked* under at a run, with the first tide pool dug out
    #      beneath it. One jump impulse always rises 1.25 m and the head
    #      then sweeps the two cells above every take-off, so a lid low
    #      enough to read as an overhang refuses every arc under it --
    #      the genre's 2bc is only expressible over a leg that never
    #      leaves the ground. The walk is second and never first: first
    #      in a beat it follows machinery at an arbitrary height, and a
    #      walk needs its predecessor within half a metre.
    #   2. off the floor and onto the first coral head, standing out of
    #      the pool the landing before it just dug. ``pedestal=False``
    #      because a plinth 3.2 m along would have to stand in that hole,
    #      and because it is a coral head: it has water under it.
    #
    # The surfaces are 1.5 / 2.0 / 3.0 and every step between them is
    # legal by construction. A slab stands half a block down in its own
    # cell, so the lantern into the overhang is +0.5, inside the 0.55 a
    # walk allows; the jump off it is +1.0 at ``arc`` 3.2, a reach of
    # 2.52 against a +1 window that shuts at 3.10.
    ("tideline", [n("glow", arc=3.2, lift=1, hug=3.0, form="slab", spread=1,
                    deco="lamp", orbs=1),
                  n("sub", arc=2.8, lift=2, hug=3.0, kind="walk", spread=0,
                    ceiling=3, moat=True),
                  n("accent", arc=3.2, step_y=1, hug=2.8, spread=0,
                    pedestal=False, orbs=1)]),
    # The lagoon, and it is the *second* beat because this is the last
    # place a beat still gets laid whole: machinery is inserted between
    # beats and the clip eats the tail of whatever is due, so a showpiece
    # in beat four is a showpiece nobody sees.
    #
    # Up the coral, off the top of it into the water two blocks down, and
    # thrown two blocks back out. Four things about it, none of them
    # free:
    #
    # * **The rise and the drop are inside one beat.** Written across a
    #   beat boundary the fall is one block about half the time, and a
    #   one-block fall is refused as a bounce on every candidate: the
    #   bounce fires at ``impact >= 7.0`` and gains *two* only at 11.0,
    #   which wants a two-block drop across 4.4 m or more. 4.9 has it.
    # * **The climb is on ``step_y``, not on ``lift``.** A beat's opener
    #   carries ``spread`` and sits a block high or low about a fifth of
    #   the time, so an absolute ``lift + 1`` behind it is a rise of two,
    #   which nothing in this motion model makes. ``step_y`` is measured
    #   from the landing before and is therefore true wherever the body
    #   actually turned out to be.
    # * **The sponge is ``pedestal=False`` and digs its own lagoon.** With
    #   a pedestal it is only offered cells with ground under them, and at
    #   the bottom of a fall into a lagoon there are none. Its material is
    #   free -- ``SPRINGY`` is imported by ``spiralplan`` and never read,
    #   and the physics is entirely ``kind="bounce"`` on the next node
    #   against the previous landing's impact -- so it is moss rather than
    #   slime, because a green slime cube in a coral garden is not a
    #   place.
    # * **``spread >= 1`` on the bounce**, or it is silently refused and
    #   placed a block lower as an ordinary hop, which looks exactly like
    #   it worked.
    #
    # Surfaces 2.0 / 3.0 / 4.0 / 2.0 / 4.0: two steps up the coral, the
    # fall into the water, and thrown out of it onto the crest. That is
    # the level's descent, and it is in the middle rather than at the end.
    #
    # **The three climbing landings are why this beat is five nodes, and
    # that is measured rather than chosen.** Written as 2.0 / 3.0 / 1.0 it
    # asked the sponge to stand at surface 1.0, which on a level with real
    # ground under it is the terrace's *own top cell*: the cell is solid,
    # the node is refused, the rest of the beat goes with it, and the
    # recovery drops a plain moss cube one block down under the beat's own
    # name so the table still reads it as placed. Instrumented over twelve
    # runs, the sponge came out ``form="full"``, ``exact=False`` and
    # arrived at impact 8.0-8.8 on eight of twelve -- under the 11.0 a +2
    # bounce needs, so the pad silently was not one. Taking off from 4.0
    # puts it at 2.0, which is an ordinary free landing height, and the
    # arrival is 12.2-13.5.
    ("lagoon", [n("rock", arc=3.2, lift=2, hug=3.0, spread=1, ceiling=3,
                  orbs=1),
                n("accent", arc=3.2, step_y=1, hug=2.8, spread=0,
                  ceiling=3),
                n("coral_pink", arc=3.2, step_y=1, hug=2.6, spread=0,
                  orbs=1),
                n("moss", arc=4.9, lift=2, step_y=-2, hug=3.2, form="slime",
                  spread=0, pedestal=False, moat=True),
                n("accent", arc=3.6, step_y=2, hug=3.0, kind="bounce",
                  spread=1, pedestal=False, orbs=3)]),
    # The bars: half-height sand standing out of the second pool. Stairs
    # and slabs are the reference's commonest non-cube form by a wide
    # margin and this tower had almost none, and a slab is worth reach as
    # well as looks -- it lands at +0.5 and reaches 3.78 m, so two slab
    # steps gain a block across seven metres of ground where one hop
    # could only manage 3.10.
    #
    # It opens with the level's longest jump, and that is arithmetic
    # rather than taste: the beat before it ends on the crest at 4.0 and
    # this one opens at 1, a drop of two, and a descent *cannot also be
    # short* -- the -2 window starts at 3.12 m of reach, because the arc
    # covers that much ground before it arrives. ``arc=4.4`` is a reach
    # of 3.72 and is the one length that is also legal level, which is
    # what it is asked from when machinery lands between the two beats.
    #
    # Surfaces 2.0 / 2.5 / 3.5 / 4.0, and the first step between them is
    # a **stride, not a jump**: a slab stands half a block down in its own
    # cell, so the bar is +0.5 away, inside the 0.55 a walk allows and
    # inside its 2.4 m of ground at ``arc=2.8``. It is at position two and
    # not at the tail because a beat lays about half its nodes and a
    # non-hop verb written last is written and never seen -- and it is the
    # lamp, which is the route painted: on a shelf of open sand the lit
    # bar is the only thing saying which way the reef runs. Measured, the
    # one keyword took the level from 86% plain hop, over the rule, to
    # 80%.
    #
    # The third moat is on this beat's opener, eight metres downstream of
    # the lagoon's: a moat digs a radius-three bowl at commit and two any
    # closer means the second stands in the hole the first dug, which is
    # also why everything after one here is ``pedestal=False``. The grotto
    # is on the beat's **last** node, because a shell is painted the
    # moment its landing commits and the walls it puts up are then in the
    # way of the next landing of the same beat.
    ("bars", [n("ground", arc=4.4, lift=2, hug=2.8, spread=1, moat=True,
                orbs=1),
              n("sub", arc=2.8, lift=3, hug=2.6, form="slab", kind="walk",
                spread=0, pedestal=False, deco="lamp"),
              n("ground", arc=3.4, lift=4, hug=3.0, form="slab", spread=0,
                pedestal=False, orbs=1),
              n("coral_pink", arc=3.2, lift=4, hug=2.6, spread=0,
                shell="grotto", orbs=2)]),
], filler=[
    # The character, repeated, and on a terrace this long the filler is
    # where the identity has to live -- a script's tail is never laid and
    # this is not. Off the reef into the shallows a block down, along the
    # lit gangway of dead coral under the overhang on foot, and back up
    # onto a coral head out of the water.
    #
    # Nothing enclosed and above all **no moat** in a filler: the filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on -- 27,859 refusals from one keyword, on
    # the level that found it.
    #
    # The walk is at position two and not at the tail. A beat lays about
    # half its nodes, so a non-hop verb written last is written and never
    # seen; moving one walk to position two took another level from 100%
    # plain hop to 83%. It is also the route painted: the reference
    # lights the place you are going to and nothing else, and on a shelf
    # of open sand the lit slab is the only thing saying which way the
    # reef runs.
    #
    # The loop seam is checked as a jump like any other, and it is what
    # sets the opening arc: the last landing stands at 3.0 and the first
    # at 2.0, so coming back round is a drop of one and wants a reach in
    # the 2.35-4.98 window. 4.4 has it, and stays legal level as well,
    # which is what the ``spread`` on that node is there to use.
    ("fans", [n("ground", arc=4.4, lift=4, hug=2.6, spread=2,
                pedestal=False, orbs=2),
              n("rock", arc=2.8, lift=4, hug=2.6, kind="walk", spread=0,
                ceiling=3, deco="lamp"),
              n("accent", arc=3.2, lift=4, hug=2.8, spread=0,
                pedestal=False, orbs=1)]),
], exit_beats=[
    # The blue hole: a well cut through the reef with the water coming up
    # it. Written out rather than left to the generated climb, because
    # that one hangs its column mid-lane at ``hug`` 2.0 with no pedestal
    # and the only thing it can anchor on is a cliff that leans away --
    # instrumented, 11,097 of 13,000 candidates refused for "no anchor"
    # on a generated bubble exit, which became a six-step staircase, a
    # third of that level, with nothing at all reporting it.
    #
    # So the column keeps its **pedestal** and asks for no ``hug``:
    # standing the landing on its own stack is what gives the column
    # something to hang on for its whole height, and ``step_y`` of four
    # or more is what puts its middle cell inside that stack rather than
    # below it. Five, here, because ``rise`` is six and the crossing
    # appended after the climb comes down one block onto the next
    # terrace -- a column that overshoots is the owner's "it puts a
    # ladder there and then jumps back down to a lower part".
    #
    # **No ``shell="shaft"``.** It was here and it is measured off: a
    # tube around an authored climb put the body inside the wall and took
    # the jammed lens from 10.4% to 18.2% on the level that removed it,
    # and the pedestal plus ``step_y >= 4`` recipe anchors without it.
    # Nothing overhead on the launch either -- both lids RULES 7
    # recommends for the exit were measured on SUNKEN TEMPLE at three
    # points of empty frame and 2.6 points of designed content, and this
    # level is comfortably inside the frame rule and not inside the
    # content one.
    #
    # **Check the move mix in ``--report`` for the word ``bubble``.** If
    # it is missing, this beat is six steps of staircase and the level
    # has lost a third of itself with no error anywhere.
    n("rock", arc=3.0, step_y=0, hug=2.4, spread=2, deco="lamp", orbs=1),
    n("prismarine", arc=3.0, step_y=3, kind="bubble", climb_style="water",
      spread=0, deco="lamp", orbs=2),
])
