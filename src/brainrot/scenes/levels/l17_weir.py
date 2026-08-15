"""Level 17: THE WEIR.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A dam across the tower's river, and the level is the dam: you arrive on
# the bank above it, go through the head-gate arch on foot, climb the
# coping onto the crest, walk out along the sill with the held water on
# both sides of you -- and then **go over the weir**: two blocks down and
# nearly five metres out into the scoured pool at its foot, which is the
# longest jump in the level and the only thing in it that reads as long.
# Down there you come back up onto the boulders in the tail-race, cross
# the mill's plank walk over the outfall, and leave the way the water
# does: up the **boil**, the standing upwelling at the foot of every real
# weir, here a soul-sand column six blocks tall with a lit lip on top of
# it. A willow leans over the pool and the course goes under it.
#
# The place is a green river bank with dressed masonry standing in it:
# moss and grass underfoot, pale stone for everything built, dark oak for
# the sluice timbers, and water in cut bowls. Against THE VAULT below
# (warm dark
# gold, a plaza, an interior, a hoard) and BLUE RUN above (pale blue ice,
# slides, an arch) it is a different hue, a different enclosure and a
# different verb; and against THE GATEHOUSE, its theme-mate at the bottom
# of the tower, it is a *dam* rather than a court -- masonry standing in
# water rather than grass with a ditch cut through it, a fall rather than
# a bounce, a ledge rather than a plaza, water on both sides of the
# walking line rather than beside it.
#
# ---------------------------------------------------------------------
# What changed in this pass, and why each of them is a measurement
# ---------------------------------------------------------------------
#
# **It is no longer a ``channel`` level, and that was the whole first
# decision.** ``profile="channel"`` cuts a 2.2-cell trough of liquid down
# the middle of the band -- ``Cone.channel_range``, at ``band - 3.6``
# plus a wander of 1.1 -- which is *exactly* where a hugged course runs,
# and ``Cone.rock`` is False under it. So a gated landmark has no footing
# for its base cells and never reserves (``docs/RULES.md`` §7: 1
# reservation in 8 on a channel against 8 in 8 on a ledge), and two other
# levels measured their structure on screen at 0.0-0.4 s until they moved
# off it and then at 1.6-2.4 s. ``landmark="tree"`` is frozen, so the
# choice was between paying for a structure that is never seen and giving
# up the free water. The water came back as holes instead, which is what
# the reference actually does: liquid on the walking line in 20 of its 43
# legs, and always **in a dug bowl**, never as a blue patch of floor.
# Three ``moat`` landings put the pond above the dam, the plunge pool
# under the sill and the outfall under the plank walk, and a pit is what
# stops the no-jump walker -- water is in ``SEE_THROUGH`` and blocks
# nothing on its own; the bowl it sits in does.
#
# **The exit is the boil, and it is three landings instead of seven.**
# This level rises seven, and a staircase spends a landing a block: on a
# level that lays nine to twelve landings in total that is the level. The
# ladder recipe in ``docs/RULES.md`` §7 -- a pedestal under the column
# and ``step_y >= 4`` so the anchor test's middle index lands on the
# landing rather than on the stack below it -- is the only thing that
# makes a climb fire at all, and ``exit="bubble"`` additionally hands the
# terrace back ``(need - 2) * 3.2`` metres of arc that the stair was
# holding in reserve (``handplan._level_budget``), which is about four
# more landings of design. A bubble and not a ladder for the same reason
# GLACIER SHELF's moulin is one: a column is *ridden*, and a ladder is
# ridden at 2.35 m/s against a bubble's 11.0, so the ladder spends a
# third of the level's screen time looking at a wall from arm's length.
# And it is honest here rather than convenient -- the roster is already
# two thirds climb exits, and the rule is one level in five, for a level
# whose *idea* is the climb. This level's idea is the fall into the pool
# and the water that puts you back on top of the dam.
#
# **The rise and the fall are one beat.** Machinery -- the landmark
# crossing, a recovery -- is inserted *between* script beats and hands
# the body back at lift 1, so a beat that climbs and a beat that drops
# off what it climbed are a beat that climbs and a beat that does
# nothing. ``crest`` is four nodes for that reason and no other.
#
# **Every beat after the first opens at lift 2.** A beat's first node is
# placed from wherever the last thing left the body, and machinery leaves
# it at lift 1 -- so a *threshold* beat is written at lift 1 (measured
# elsewhere at 100% against 67% at lift 2) and a beat following another
# script beat is written at lift 2 with ``spread=1``, which is the one
# real lever a level has against the owner's "half the jumps are at
# ground level". Five of this level's eight script landings stand at lift
# 2 or 3.
#
# **No ``breaks``, so no lock.** A level's first floor break is always
# 5.5-6.7 m wide and the machinery that crosses it costs one to three
# landings of the ten this level gets. The moats and the four floating
# landings hold the walker without spending any.
#
# **The bounce is gone.** The version this replaces made a slime pad the
# level's signature move. Measured tower-wide it places on 6 runs in 24
# and fires on 1, and a green slime cube is the brightest thing in a
# frame of wet grey stone. Two reliable ``walk`` strides -- the head-gate
# arch and the plank over the outfall -- buy more non-hop share than the
# pad ever did, and both are things a weir actually has.
#
# **The bank is green and the dam is the only grey thing on it.** Written
# the other way round first -- the terrace itself as wet masonry, mossy
# cobble over tuff and deepslate -- and the contact sheet came back a grey
# plate with grey landings standing on it and the water as two thin blue
# lines. The reference's frames are one strong hue plus dark rock, and
# that version had no hue at all. See the ``floor`` table below.
#
# **Nothing stands above lift 3.** ``_lm_g_tree`` hangs its canopy at dy
# 5-6, so a landing at lift 4 or higher on a ``tree`` level puts the
# camera inside the leaves.
#
# Three A/Bs, all on the same three seeds with ``__pycache__`` cleared
# between arms, because a level module edited twice inside a second at the
# same byte count leaves Python's cache valid and the second arm measures
# the first:
#
# * **``band`` 11.0 against 10.0.** The narrower corridor is better on
#   two rows -- walker coverage 31% to 26%, empty frame 48.3% to 46.7%
#   mean -- and it takes ``tailrace`` from 16/16 to 14/15, which is the
#   one beat whose landings both float. 11.0 is the widest band at which
#   every beat is placed exactly, a weir is a broad thing, and both
#   neighbours are narrower (THE VAULT 10.0, BLUE RUN 7.5).
# * **One more ``ceiling`` beam, on ``crest``'s opener.** A lid is a
#   one-cell beam along the direction of travel and answers only the
#   centre column of the lens fan -- but chained beat to beat that is the
#   column that looks where you are going. Empty frame 48.3% to
#   **46.3%** mean over the three seeds, for one keyword, at no cost to
#   anything else. That took this level under the 48% rule.
# * **The head-gate's ``shell``, on against off.** Kept because it is
#   free: the jammed-lens figure is 30 of 494 frames on seed 3 either
#   way, to the frame. The jam is not the tunnel -- seeds 5 and 7 read
#   0.0% with the same shell in place -- it is the cliff swinging across
#   the aim at one corridor bend, which is the tower's own open item 1
#   and not something a level can fix from here.
LEVEL = Level("THE WEIR", "plains", rise=7, gap=3.0, exit="bubble",
              band=11.0, shelf=5.0, breaks=3, landmark="tree",
              ground="moss", sub="gravel", rock="stonebrick",
              accent="darkoak", glow="lantern", liquid="water",
              # Fifteen distinct kinds once the four roles are added on
              # top at role weight, with the dominant (moss) at 24% of
              # the terrace against the real map's median dominant share
              # of 26%. Green of one kind or another is about two fifths
              # and the grey-brown tail is the shingle and silt of a
              # river bed. Green is also the hue neither neighbour has --
              # THE VAULT's warm gold below, BLUE RUN's pale ice above --
              # and it is what makes the dressed-stone landings read as
              # the route without a single extra cell being laid.
              floor=(("moss", 4), ("grass", 3), ("mossy", 3),
                     ("gravel", 2), ("cobble", 2), ("podzol", 1),
                     ("coarse", 1), ("dirt", 1), ("clay", 1),
                     ("andesite", 1), ("stone", 1), ("spruce", 1),
                     ("tuff", 1), ("darkoak", 1)),
              props=("sugarcane", "lilypad", "mcfence", "grasstuft",
                     "pebbles"),
              # Overcast river light rather than the plains' holiday
              # blue: the sky is a third of every frame on a ledge and
              # this level's whole palette is grey-green.
              sky=(168, 190, 196),
              candy=("mossy", "stonebrick"),
              step=("stonebrick", "hop"), beats=[
    # The threshold: a lantern set flush in the wet kerb on the bank, and
    # then the head-gate itself -- an arch of dressed stone, **walked**
    # through with the passage closing over your head.
    #
    # A doorway is walked and never jumped. One impulse always rises
    # 1.25 m, so the head sweeps the two cells above every take-off and
    # an arc under a lintel low enough to read as a door is refused every
    # time. The walk is the *second* node and not the first: a walk needs
    # its predecessor within half a metre and a beat's opener is placed
    # from wherever machinery left the body. Reach 2.12 against the
    # 2.4 m a walk leg spans, dead level, legal by construction.
    #
    # The shell is on the beat's last node, because a shell is painted
    # the moment its landing commits and its walls are then in the way of
    # the next landing of the same beat -- and it is at lift 1, which is
    # the only height at which ``_shell`` finds footing for a wall rather
    # than hanging a roof over open sides. This is the level's one real
    # interior and it is a two-metre pinch, which is what the reference's
    # interiors measure as (fully enclosed 6.1% of the way, median
    # enclosed run two metres).
    #
    # It carries its own lamp, because an interior in the reference is
    # always lit from inside. It was put here to answer the one flat
    # frame on this level's contact sheet -- a single grey wall, nothing
    # else in it -- and it did not: switching the whole shell off leaves
    # the jammed-lens count at 30 of 494 frames on that seed, to the
    # frame, so the wall is the cliff at a corridor bend and not this
    # arch. The lamp stayed anyway; the reasoning for it was sound even
    # though the diagnosis was wrong.
    ("headgate", [n("glow", arc=3.2, lift=1, spread=1, hug=2.8,
                    deco="lamp", orbs=1),
                  n("stonebrick", arc=2.8, lift=2, kind="walk", spread=0,
                    hug=2.8, shell="tunnel", ceiling=3, deco="lamp")]),
    # The dam, and the whole of the level's one idea in one beat: up onto
    # the coping, out along the crest with the held water either side,
    # and over the sill.
    #
    # Four jumps, and each is a different question.
    #
    # 1. **The coping**, +1 across arc 3.2 -- reach 2.52 against a
    #    2.00-3.10 window, centred rather than pressed against the top of
    #    it, because at 3.6 it is the *arc* that has to fall back and a
    #    fallback is not exact. ``spread=1`` because this is a beat's
    #    opener; ``deco="post"`` stands a dark oak sluice post on it.
    # 2. **The crest stone**, level across 3.2, standing *in* the water:
    #    ``moat`` swaps the terrace's top cell for the theme's liquid
    #    over a radius-3 disc and the landing keeps its own stack, so
    #    this is a pier in the head-race rather than a block on a blue
    #    patch of floor. ``ceiling=3`` is the winch beam over it -- legal
    #    over a level hop, whose apex is 1.25 m against a lid at three.
    # 3. **The sill**, +1 again, and it floats. ``pedestal=False`` is not
    #    decoration: the moat one landing back digs a bowl of radius 3
    #    and this stone is 3.2 m from it, so a landing wanting ground
    #    here is a landing wanting ground that has just been dug away.
    #    It carries the level's far-end lamp, which is the turn signal --
    #    every light in the reference is at the end of the stretch it
    #    lights, and there is no decorative lighting anywhere in it.
    # 4. **The spill**, and it is the showpiece: from lift 3 to lift 1,
    #    two blocks down across 4.9 m of arc. Reach 4.22 against a
    #    3.12-5.56 window at -2 and a 2.35-4.98 one at -1, so
    #    ``spread=1`` is legal both ways. A descent is the only long jump
    #    this motion model has -- falling takes time and the body does
    #    not slow down while it falls -- and this is the only jump in the
    #    level past 4.4. It lands floating over the plunge pool the
    #    second moat digs, 8.1 m clear of the first, which is well past
    #    the radius at which two ponds fight.
    ("crest", [n("stonebrick", arc=3.2, lift=3, spread=1, hug=3.0,
                 ceiling=3, deco="post"),
               n("mossy", arc=3.2, lift=3, spread=0, hug=3.4, moat=True,
                 ceiling=3, orbs=1),
               n("stonebrick", arc=3.2, lift=4, spread=0, hug=3.0,
                 pedestal=False, deco="lamp"),
               n("mossy", arc=4.9, lift=2, spread=1, hug=3.6,
                 pedestal=False, moat=True, orbs=2)]),
    # The tail-race: out of the pool onto a scoured boulder, and across
    # the mill's plank walk over the outfall.
    #
    # It opens at lift 2 and not lift 1 -- +1 off the pool, reach 2.52 --
    # because it follows a script beat rather than machinery and so knows
    # where the body is. Both landings float, which is what keeps the
    # bottom of this level from being a shelf you could stroll: below a
    # dam there is no ground, there is scour.
    #
    # The plank is the level's second ``walk`` and it is at position two,
    # which is where a non-hop verb fires -- a beat lays about half its
    # nodes, so a verb written at a beat's tail is written and never seen.
    # Its own moat is the outfall, 6.0 m from the plunge pool.
    ("tailrace", [n("gravel", arc=3.2, lift=3, spread=1, hug=2.8,
                    pedestal=False, ceiling=3),
                  n("darkoak", arc=2.8, lift=3, kind="walk", spread=0,
                    hug=2.8, pedestal=False, moat=True, ceiling=3,
                    orbs=1)]),
], filler=[
    # The ford below the mill, and this is where the level's character
    # actually lives: a filler repeats when the terrace outlasts the
    # script and the tail of a script does not.
    #
    # The opener is the longest jump outside the spill and it has three
    # different heights to be legal from -- reach 3.72 is inside the -1
    # window (2.35-4.98), the level one (2.00-4.26) and the -2 one
    # (3.12-5.56) -- so it works off the plank, off the filler's own last
    # stone when the loop comes round, and off the terrace when machinery
    # has put the body back down. A filler's seam is checked like any
    # other jump and half a filler's fidelity is usually lost there.
    #
    # Then the shallows, waded rather than jumped, under a lid; then up
    # onto a floating stone at lift 2.
    #
    # **No ``moat`` anywhere in here**, and that is not taste: the filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on.
    ("ford", [n("mossy", arc=4.4, lift=3, spread=1, hug=3.0, orbs=1),
              n("cobble", arc=2.8, lift=3, kind="walk", spread=0,
                hug=3.2, ceiling=3),
              n("stonebrick", arc=3.2, lift=3, spread=0, hug=2.8,
                pedestal=False, orbs=1)]),
], exit_beats=[
    # The **boil**: the standing upwelling at the foot of a real weir,
    # where the water that has gone over the sill comes back up. A last
    # dry stone to launch from, six blocks of column, and a lit lip on
    # top of the dam's shoulder to stand on before the leap across.
    #
    # The arithmetic of the height. The level rises seven and the body
    # arrives at the chasm at lift 1 or 2, so the climb has to gain six
    # or seven. The launch resets to lift 1, the column gains six and the
    # lip one: the last landing is a block *above* the next level's
    # floor, which is deliberate -- the crossing comes down one block
    # onto it, and a jump that descends a block reaches 4.98 m where a
    # flat one stops at 4.26.
    #
    # ``pedestal=True`` is why this branch fires at all rather than
    # silently becoming a staircase. ``_climb_move`` wants solid rock
    # within one cell of the column at its **middle index and at its
    # top**, and out in the lane the only candidate is the landing's own
    # stack; floated, it is refused with nothing reporting it -- 11,097
    # of 13,000 candidates on the generated bubble exit, which became a
    # six-step staircase and a third of that level. ``step_y=6`` is the
    # other half of the recipe: under four and the middle index lands on
    # the stack below the landing instead of on the landing, and at eight
    # the ride is nine consecutive flat-grey frames. The only proof it
    # worked is ``bubble`` appearing by name in the move mix.
    #
    # The launch stands at ``hug=2.8`` and not 2.2, which is the whole of
    # a level's jammed-lens number: one level measured 69 wall-jammed
    # frames of 1,293 at 2.2 and **0 of 1,280** at 2.8. ``hug`` on the
    # column itself is inert. No ``shell="shaft"`` around it -- it is the
    # obvious way to stop a climb framing as sky and it puts the body
    # inside the tube wall; the lids on the launch and the lip do the
    # same job honestly, and a beam chained beat to beat is what fills
    # the one column of the lens fan that looks where you are going.
    n("stonebrick", arc=3.2, step_y=0, hug=2.8, spread=1, confine=True,
      ceiling=3, deco="lamp"),
    n("mossy", arc=2.4, step_y=4, kind="bubble", hug=2.0, pedestal=True,
      pedestal_style="stonebrick", spread=0, deco="lamp", orbs=2),
    n("stonebrick", arc=3.0, step_y=1, hug=2.8, spread=0, pedestal=False,
      ceiling=3, orbs=1),
])
