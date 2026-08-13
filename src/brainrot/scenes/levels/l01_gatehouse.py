"""Level 1: THE GATEHOUSE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The tower's front door, and the first thing anybody ever sees of this
# tower: a green outer court behind a gate, with a flooded ditch cut across
# it and a timber gate lodge standing in the middle of it. In over a lit
# sill, through the gate arch **on foot**, out over the drawbridge deck and
# onto a pier standing in the water, up the far bank and down into the mire
# at the bottom of the ditch, bounced out of it onto the curtain wall, and
# away up the vine on the wall's own face.
#
# **The level is built around the lodge, and that decided the profile.**
# ``cabin`` is a *walk* gate -- an interior three cells high, crossed at a
# run, because one jump impulse always rises 1.25 m and no arc gets under a
# lintel low enough to read as a door. A walk gate reserves 0-2 times in 8
# on a ``ledge`` and a hop gate 8 of 8 (``docs/RULES.md`` §7), which is why
# THE CORNICE gave its cabin up and took the crane instead. This level
# cannot -- the cabin is assigned, and a gatehouse whose gate you run *past*
# is not a gatehouse -- so the ground is a ``plaza``, the one profile with
# five supported cells across the corridor to give it. MARKET STREET is the
# precedent: a plaza carrying the watchtower's walk gate two levels up.
#
# Instrumented, pinned to this level: the gated lodge reserves on 2 runs in
# 8, the small cabin stands beside the course on 4 more, and the two left
# get nothing. The course has still never been caught landing *inside* it,
# which is the tower's own open item 0b and not a thing a level can fix.
# What it is worth is measurable anyway -- structure on screen went from
# 0.0 s at 25 degrees on the old ledge to 0.8-2.6 s depending on the seed.
#
# **``breaks=0``, and it is the biggest single decision in the file.** Any
# break at all forces the lock: a level's first floor break is always
# 5.5-6.7 m wide, so the machinery that crosses it lays an approach at
# height, an island floated over the hole and a landing on the far ground.
# Measured over 24 runs, the same design either way --
#
#   |                                | ``breaks=2`` | ``breaks=0`` |
#   |--------------------------------|--------------|--------------|
#   | landings that are the design's | 39%          | **56%**      |
#   | plain hop                      | 87%          | **73%**      |
#   | covered by a no-jump walker    | 43%          | 48%          |
#   | walked end to end              | 0 of 14      | 0 of 14      |
#
# -- five points of walkability for seventeen of design. What holds the
# walker without a lock is the water: **four** ``moat`` landings, each
# swapping the terrace's top cell for water over a radius-3 disc, and water
# is not standable. Moats alone are measured tower-wide as taking a walker
# from 65.8% of a level to 25.8%, and the chasm at the level's end is what
# makes it impassable end to end. An *undressed* plaza is what killed the
# first tower; this one is 57% floating landings with ponds cut through it.
#
# The plaza is also what puts colour in the bottom of the frame. Its whole
# band is painted from the level's floor palette, which here is thirteen
# materials with none of them over about a sixth of it: grass, moss, mossy
# cobble and oak at role weight over coarse, podzol, gravel, dirt, stone,
# cobble, andesite and farmland. The real map measures a median fourteen
# materials a level with the commonest at 26%; this tower used to measure
# six with the commonest at 55%. It shows -- 42-53% of the view empty here
# against 48% on the five-cell shelf this level used to be, which read on
# its own contact sheet as grey stone and blue sky with two green cubes in
# it.
#
# **One shell and no more.** A shell's walls only stand where the terrain
# gives them a footing, so on a ledge a shell is a roof with open sides and
# on a plaza it is a real room. The gate arch gets the tunnel, because a
# two-metre pinch is exactly what a doorway is; everything else overhead is
# a ``ceiling`` beam, which is one cell spread along the direction of
# travel and does not wall the lane in.
#
# **Beat order is the budget.** The terrace is about 82 m of arc, the exit
# reserves a landing for every block still to gain, and the lodge crossing
# takes its approach and its three stored cells out of the middle. Four
# short beats and a filler is what fits, and the identity has to be in the
# first two and in the filler, which repeats -- a beat is laid whole or not
# at all, and this level lays about seven of its own landings a run.
LEVEL = Level("THE GATEHOUSE", "plains", rise=4, gap=2.8, exit="stair",
              band=10.5, profile="plaza", shelf=4.0, breaks=0,
              landmark="cabin",
              ground="grass", sub="moss", rock="mossy", accent="oak",
              liquid="water", glow="lantern",
              props=("grasstuft", "flower", "mcfence", "lilypad",
                     "sugarcane"),
              candy=("oak", "mossy"), step=("cobble", "hop"), beats=[
    # The threshold, and on the tower's opening level it is also the first
    # frame of the whole strip: one lantern set flush in the road on a half
    # step, and then the gate arch itself, **walked** through with the
    # passage closing over your head.
    #
    # A doorway is walked and never jumped. One jump impulse always rises
    # 1.25 m and the head then sweeps the two cells above every take-off, so
    # an arc under a lintel low enough to read as a door is refused every
    # time -- which is why ``kind="walk"`` exists and why it is the second
    # node rather than the first. A walk needs its predecessor within half a
    # metre and a beat's first landing is placed from wherever the machinery
    # between beats left the body; written first it fires two times in
    # eight. Both nodes are slabs, so the two are dead level and the walk is
    # legal by construction: reach 2.12 against its 2.4 m window.
    #
    # Two nodes, because a beat is laid whole or not at all and the two that
    # matter most on this level are the ones that always play. It comes out
    # 28 of 28 as authored over 24 runs.
    #
    # No ``deco="lintel"`` on it, and that is arithmetic rather than taste:
    # the beam's height is taken from the *apex of the move it spans* plus a
    # third of a metre, and a walk has no apex, so over a slab -- whose
    # walking surface is halfway up its own cell -- the beam comes out at
    # shin height. The ``ceiling`` lid does the same job honestly, three
    # cells over the feet and checked against the arc rather than drawn near
    # it, and the tunnel supplies the walls.
    ("gate", [n("glow", arc=3.2, lift=1, form="slab", spread=1,
                deco="lamp", orbs=1),
              n("cobble", arc=2.8, lift=1, form="slab", kind="walk",
                spread=0, shell="tunnel", ceiling=3)]),
    # Out across the ditch: onto the kerb, over the drawbridge deck on foot
    # under its beam, and up onto the far pier standing in dug water.
    #
    # ``moat`` swaps the terrace's top cell for the theme's liquid over a
    # radius-3 disc, so the jump onto that pier is a jump over water rather
    # than over a coloured patch of floor -- and this is the single most-used
    # mechanic in the reference (water on the walking line in 20 of its 43
    # legs, lava in 26) and the one this tower has least of. It is on the
    # beat's **last** node: a moat is painted the moment its landing commits
    # and eats into the next landing of the same beat.
    #
    # The second walk, and again at position two. A beat lays about half its
    # nodes, so a non-hop verb written at a beat's tail is written and never
    # seen; measured on this level, moving the walks to position two is the
    # difference between a move mix that is 96% plain hop and one that is
    # not. The deck is level with the kerb because a walk allows half a
    # metre of height change and no more.
    #
    # The pier is +1 at reach 2.52, centred in the 2.00–3.10 a one-block rise
    # allows rather than pressed against the top of it -- an arc of 3.6
    # reaches 2.92, so it is the arc that has to fall back, and a fallback is
    # not exact.
    ("causeway", [n("mossy", arc=3.4, lift=1, spread=1),
                  n("oak", arc=2.8, lift=1, kind="walk", spread=0,
                    ceiling=3),
                  n("oak", arc=3.2, lift=2, spread=0, moat=True,
                    orbs=2)]),
    # The ditch, and the level's one showpiece: up onto the far bank, a long
    # fall into the green mire standing in the flooded bottom, and the bounce
    # out of it onto the foot of the wall.
    #
    # **The rise and the drop are in the same beat and they have to be.**
    # Machinery is inserted *between* script beats and leaves the body back
    # at lift 1, so a beat that opens by dropping off the height the beat
    # before it climbed to drops nothing about half the time -- the pad is
    # fed a flat approach, the bounce is silently refused, it becomes an
    # ordinary hop, and the beat still reads as placed. WINDMILL REACH above
    # measured exactly that at 0%.
    #
    # **The bounce is arithmetic, not luck.** It fires only at an arrival
    # speed of 7.0 m/s: a level hop arrives at 5.4 and cannot bounce at all,
    # a one-block drop across 4.9 m arrives well past it and is thrown back
    # one block. And the feed has to survive its own *short* fallback --
    # placement offers ``arc * 0.84`` when the distance asked for has no
    # landing, and at 4.4 m that fallback lands at 6.75 against a 6.72
    # threshold, which is the bounce quietly not happening. At 4.9 the
    # fallback is still 4.1 m. ``spread`` on the bounce is 1 and never 0: at
    # zero the bounce is refused outright and the landing is placed a block
    # lower as a hop, which looks like it worked.
    #
    # This is the only move in the level that gains height without a jump,
    # and the one thing on it a viewer would call a trick.
    ("ditch", [n("mossy", arc=3.4, lift=2, spread=1),
               n("slime", arc=4.9, lift=1, spread=0, moat=True, orbs=1),
               n("mossy", arc=3.6, lift=2, kind="bounce", spread=1,
                 orbs=3)]),
    # The wall-head, and this is the beat that gets off the floor: out of
    # the ditch, up the two courses of the curtain wall and onto a merlon
    # hung over the water with nothing under it. Four blocks of walking
    # surface above the ditch bed, and the last landing is unwalkable by
    # construction -- ``pedestal=False`` leaves it no stack, which on a
    # plaza is the only way a landing is not simply a block you could have
    # stepped up onto.
    #
    # Two +1 hops at reach 2.52 each. Nothing rises two blocks in one
    # ballistic move -- the discriminant has no solution, exactly as in
    # vanilla -- so a wall is climbed one course at a time or not at all,
    # and the bounce in the beat before is the only thing on this level that
    # does it in one.
    #
    # The merlon carries the level's fourth moat even though nothing stands
    # under it: ``_moat`` digs the terrace at the *floor*, so a landing hung
    # over the court with the ditch cut away beneath it is a merlon over
    # water, and it is the one place on the level where the walker is stopped
    # by a hole rather than by a jump it cannot make.
    ("wallhead", [n("mossy", arc=3.4, lift=1, spread=1),
                  n("cobble", arc=3.2, lift=2, spread=0, ceiling=3),
                  n("mossy", arc=3.2, lift=3, spread=0, pedestal=False,
                    moat=True, orbs=1)]),
], filler=[
    # The court itself, and on a level this tight the filler is most of
    # what a viewer actually sees, so the character is here rather than in
    # a fourth beat that is written and never laid.
    #
    # Three things in the order a walled court has them: the long drop back
    # down off the wall onto the worn path, the wicket gate walked through
    # under its beam, and the well-head standing in the court pond.
    #
    # The **walk is at position two**, which is the one lever this level's
    # own body has on a move mix that is otherwise all hops: a beat lays
    # about half its nodes, so a non-hop verb written at a beat's tail is
    # written and never seen, and one written first follows machinery at an
    # arbitrary height where a walk needs its predecessor within half a
    # metre. Position two is where it fires. The lodge crossing supplies a
    # second walk when it lands, but that is machinery aimed at a world
    # feature and this level should not depend on it.
    #
    # The opener is 4.4 m because it has three different heights to be
    # legal from: −2 off the merlon at the end of ``wallhead`` (reach 3.72
    # against 3.12–5.56), −1 off the well-head when the filler loops back on
    # itself (2.35–4.98), and level when machinery has put the body back
    # down on the terrace (2.00–4.26). It is also the longest jump in the
    # level and the one that reads as long, because a descent is the only
    # long jump this motion model has.
    #
    # One moat, on the beat's **last** node. A moat is painted the moment
    # its landing commits and eats into the next landing of the same beat,
    # and a filler loops -- so it goes last, and the loop back over it is
    # the 4.4 m jump rather than a stride.
    ("court", [n("podzol", arc=4.4, lift=1, spread=1, orbs=1),
               n("oak", arc=2.8, lift=1, kind="walk", spread=0,
                 ceiling=3, deco="lamp"),
               n("cobble", arc=3.2, lift=2, spread=0, moat=True,
                 orbs=1)]),
], exit_beats=[
    # The way out is the vine on the wall's own face, and it is deliberately
    # not a staircase. The owner's complaint about this tower names one:
    # "a couple of ground-level hops, then a couple higher, *then stairs*,
    # then you drop back down". Measured over the same 24 runs, a four-tread
    # stair of dressed cobble -- lit, roofed, hugged to the wall, everything
    # a stair can be given -- was worse on both counts than the climb: **96
    # landings of exit against 92, and 87% plain hop against 73%.** It does
    # not even buy the level room; the climb out is a third of it either
    # way. Three treads was tried as well and is worse again (98), because a
    # stair that arrives short hands the crossing a jump no physics has and
    # the recovery chain pays for it.
    #
    # A vine rather than a ladder for two reasons: WINDMILL REACH above
    # leaves by a ladder and two in a row at the bottom of the tower is one
    # too many, and this wall is mossy. Same two nodes, same numbers to the
    # landing, a different thing to look at.
    #
    # ``exit="stair"`` in the header is not a contradiction: ``exit_beats``
    # is what gets built and ``exit`` names what happens when it *cannot*
    # be, and the honest fallback is a stair on this level's own cobble
    # (``step``). A generated climb is the wrong fallback -- it hangs its
    # column at ``hug`` 2.0 with no pedestal, finds nothing to anchor on,
    # and falls through to a longer staircase than the one it replaced.
    #
    # The recipe is the part of a climb that is not negotiable. A column
    # anchors only where there is solid rock within one cell of it at its
    # **middle index and at its top**, which out in the lane there never is
    # -- so it needs a pedestal under it and a rise of at least four, and
    # ``step_y=4`` on a level that rises four is exactly that and no more.
    # A climb that cannot anchor silently becomes a staircase and the beat
    # still reads as placed, so the only proof is the move mix showing
    # ``climb`` by name: it is 10% of every move in this level.
    #
    # No ``shell="shaft"`` round it. It is the obvious way to stop a climb
    # framing as sky and it is the wrong one -- measured elsewhere in this
    # roster it puts the body inside the tube wall, and taking one off took
    # a jammed lens from 18.2% to 10.4%. The lid goes on the launch landing
    # instead: the exit climb is the emptiest part of every level in this
    # tower, because a body climbing against the cliff is looking at the
    # chasm, the next terrace and the sky over it.
    n("cobble", arc=2.8, lift=1, hug=2.8, spread=1, confine=True,
      ceiling=5, deco="lamp"),
    n("vine", arc=2.4, step_y=4, kind="climb", climb_style="vine",
      hug=2.6, pedestal_style="cobble", spread=0, confine=True,
      deco="lamp", orbs=2),
])
