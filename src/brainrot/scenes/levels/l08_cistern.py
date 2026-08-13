"""Level 8: THE CISTERN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The tower's water tank, cut into the dripstone -- and its wall has
# cracked open into an amethyst geode.
#
# One sentence: *you go down into the tank before you can get out of it.*
# You arrive over the coping on a lantern set flush in the stone, sprint
# under a stalactite with the water already dug out beside you, climb the
# tank's inner wall two blocks -- and then go off the top of it, two down
# and four and a half metres out, onto the one algae-covered stone lying
# in the bottom. It throws you two blocks straight back up onto the
# crystal, which is the only place in this motion model where a landing
# gains two. Then the wall opens: a white calcite chamber roofed in
# amethyst, crossed on foot. You leave up the overflow well in the
# corner, on a bubble column.
#
# **The landmark changed from ``arch`` to ``cluster``, and that is why
# this level was rebuilt rather than patched.** ``cluster`` is the
# amethyst geode -- four cells and three blocks tall, the *only* one of
# the fifteen blueprints with no gated variant, on purpose
# (``spiralplan.GATED``'s footnote: its two deep-dark levels measured
# worse with a five-cell gate across them). So there is no crossing to
# steer the course through it and nothing to make it big. A four-cell
# structure cannot be a level's identity, and the reference agrees --
# the median biggest mass on a real terrace is twelve cells and four
# blocks tall (RESEARCH 4). So the crystal is the level's *palette*
# rather than its monument, and it is everywhere:
#
# * ``sub="amethyst"`` puts it in the lowest two cells of the cliff at
#   every bearing (``Cone.cliff_style``, ``h < 2``) -- a purple seam
#   running along the tank's waterline for the whole level -- in the cut
#   face under the terrace lip (``_slab``, depth 1), and in the roof of
#   the one shell (``_shell``'s ``roof = theme.sub``). A white-walled
#   chamber with a purple crystal ceiling *is* a geode; nothing had to
#   be built for it.
# * the geode blueprint itself then reads as one more outcrop of the
#   same seam rather than as a lilac ornament dropped on a grey plate.
#
# ``profile`` was ``channel`` and this is the second-largest change.
# A channel cuts its liquid two cells wide at 3.6 out from the core --
# where ``Course.lane_radius`` puts the running line -- and an *ungated*
# landmark cannot reserve on a ``ledge`` at all (RULES 7). Between them
# that left the only two profiles this level could have as ``channel``,
# where the structure measured **0.4 s** on screen against the 1.5 s
# rule, and ``plaza``. A plaza is also what a cistern actually is: the
# reference's answer to a wide floor is not to narrow it but to make its
# whole width hazard (RESEARCH 8), and this floor is water in holes,
# floating stones and one lock across a break.
#
# The identity is the floor, thirteen materials with no one of them over
# a fifth: brown dripstone and grey tuff, blue-grey clay silt, deepslate
# where it stays wet, gravel and moss and mossy cobble at the waterline,
# one copper fitting, and amethyst speckled through all of it. Against
# CANOPY WALK's jungle green below and GLACIER SHELF's snow-and-blue-ice
# above, this level is brown, white and purple and is not confusable
# with either from a single frame.
LEVEL = Level("THE CISTERN", "dripstone", rise=6, gap=2.8, exit="bubble",
              band=10.0, profile="plaza", breaks=1, landmark="cluster",
              ground="dripstone", sub="deepslate", rock="dripstone",
              accent="amethyst", liquid="water", glow="lantern",
              dark=0.32, sky=(102, 92, 116),
              candy=("amethyst", "calcite", "copper"),
              step=("calcite", "hop"),
              props=("dripstone", "chain", "lilypad", "pebbles",
                     "vinehang", "lanternpost"),
              # A cistern floor: rock under silt under water. ``tuff``
              # carries it with the dripstone, and the tail is what
              # stands in the bottom of a tank -- clay, gravel, moss and
              # mossy cobble along the waterline, deepslate in the wet,
              # one copper fitting. Thirteen kinds, dominant 21%,
              # against the reference's median fourteen and 26%.
              floor=(("tuff", 3), ("dripstone", 2), ("calcite", 2),
                     ("gravel", 2), ("clay", 2), ("amethyst", 1),
                     ("mossy", 1), ("cobble", 1), ("andesite", 1),
                     ("stone", 1), ("moss", 1), ("copper", 1)),
              beats=[
    # The coping. Three ideas in three landings, which is the density the
    # complaint asked for rather than three hops at one height:
    #
    #   0. a lantern set flush in the coping, on a rise, with a
    #      stalactite three cells over it. The threshold -- a light to
    #      aim at, mass over the head in the level's *first* frame, and
    #      the complete change of palette from the jungle below.
    #   1. the coping itself, **walked** under a second stalactite with
    #      the tank's water dug out beneath. A lid at three is the
    #      genre's 2bc and the only honest form of it here: one impulse
    #      always rises 1.25 m, so the head sweeps the two cells above
    #      every take-off and a beam low enough to read as a beam
    #      refuses every arc under it. Over a leg that never leaves the
    #      ground it is exact. The walk is at position two and never
    #      first: first in a beat it follows machinery at an arbitrary
    #      height, and a walk needs its predecessor within half a metre.
    #   2. up the tank's inner wall, on ``step_y`` rather than ``lift``
    #      so the rise is measured from where the body actually is, and
    #      floating -- the moat one landing back digs a bowl of radius
    #      three that a plinth 3.2 m along would have to stand in.
    ("coping", [n("glow", arc=3.0, lift=1, spread=2, deco="lamp", orbs=1,
                  ceiling=3, pedestal_style="dripstone"),
                n("calcite", arc=2.9, lift=1, kind="walk", spread=0,
                  ceiling=3, moat=True),
                n("calcite", arc=3.2, step_y=1, spread=0, pedestal=False,
                  orbs=1)]),
    # The tank, and this is the level. It is the one beat that is worth
    # writing out jump by jump, because all three of its numbers are
    # forced:
    #
    #   0. the top of the tank wall, +1 at ``arc`` 3.2-3.4 -- a reach of
    #      2.72 against a +1 window that shuts at 3.10. The highest dry
    #      stone in the level and the thing you aim at from the door.
    #   1. **off the front of it: two blocks down, 3.92 m of reach.**
    #      The longest jump here and the only way to buy one -- nothing
    #      rises two in one impulse, but falling takes time and the body
    #      does not slow down while it does, so -2 reaches 5.56 where
    #      level reaches 4.26. Written on ``step_y`` because a descent
    #      has to be a descent from wherever the beat above left the
    #      body, and at 4.6 its two fallback arcs (5.24, 5.89 -- a
    #      ``step_y`` node falls back *longer*, never shorter) both stay
    #      inside the -2 window of 3.80-6.24.
    #   2. and the fall is what pays for the next jump. A bounce is
    #      thrown by the speed it arrived with: this arc lands at 11.35
    #      m/s, and ``bounce_launch`` keeps 96% of it, which is 10.90
    #      against the 10.58 a **two-block** gain needs. One block less
    #      of drop, or an arc a metre shorter, and this is an ordinary
    #      hop with the beat still reading as placed. ``spread=1`` is
    #      not optional either -- at ``spread=0`` the bounce is refused
    #      and the landing is quietly placed a block lower.
    #
    # The rise and the drop are inside *one* beat and that is not
    # tidiness: machinery is inserted between beats and leaves the body
    # back at lift 1, so a beat that opens by dropping off the height
    # the beat before it climbed to drops nothing about half the time.
    ("tank", [n("calcite", arc=3.2, lift=2, spread=1, ceiling=3, orbs=1,
                pedestal_style="dripstone"),
              n("calcite", arc=3.2, step_y=1, spread=0, orbs=1,
                pedestal_style="dripstone"),
              n("slime", arc=4.6, lift=1, spread=0, pedestal=False,
                moat=True, orbs=2),
              n("amethyst", arc=3.4, lift=3, kind="bounce", spread=1,
                pedestal=False, orbs=3)]),
    # The geode: the tank wall opened out into two metres of crystal
    # chamber. Two metres and not fifteen seconds -- the real map is
    # fully enclosed 6.1% of the way and its enclosed runs have a median
    # length of two metres (RESEARCH 4). What it *is* almost always is a
    # groove, and that is what the rest of this level is.
    #
    # The shell is a ``cave`` and it sits on the **walk**, for a reason
    # that is geometry rather than taste: a shell's roof lands in the
    # cell the head sweeps at a hop's apex, so ``write`` refuses it
    # there and a tunnel over a jump is a roof with a hole in it. It
    # only survives whole over a leg that never leaves the ground. Its
    # walls come out ``theme.rock`` -- white calcite -- and its roof
    # ``theme.sub``, which is the amethyst. That is the whole structure
    # the level is named for, and it cost one keyword.
    ("geode", [n("amethyst", arc=3.2, lift=2, spread=1, ceiling=3, orbs=1,
                 pedestal_style="dripstone"),
               n("amethyst", arc=3.0, lift=2, kind="walk", spread=0,
                 shell="cave", deco="lamp"),
               n("calcite", arc=3.2, lift=3, spread=0, deco="lamp", orbs=2)]),
], filler=[
    # The drip run, and this is where the level's character actually
    # lives: the filler repeats and a script's tail does not. Four
    # landings at lifts 2, 2, 3 and 1 -- it climbs and then *falls*,
    # which is the thing every level in this tower lacked. The real map
    # descends somewhere on 36 of its 43 legs and travels eleven blocks
    # vertically to gain four; it does it by coming off edges, not by
    # jumping down, and the two-block drop at the end of this loop is
    # that.
    #
    # The four seams are all legal, including the one nobody looks for
    # -- the loop's own last-to-first: 2 -> 2 walked, 2 -> 3 at reach
    # 2.52, 3 -> 1 at reach 3.72, and 1 -> 2 back round at 2.52.
    #
    # The walk is at position two and is the level's third: it is the
    # only non-hop verb reliable enough to put in a loop, and a loop is
    # the only place a verb gets used more than once. No ``moat``
    # anywhere in here, and that is a rule rather than a preference --
    # the filler loops, and the second lap digs the ground out from
    # under the pedestals the first lap stood up.
    ("drip", [n("calcite", arc=3.2, lift=2, spread=1, ceiling=3, orbs=1,
                pedestal_style="dripstone"),
              n("ground", arc=2.9, lift=2, kind="walk", spread=0,
                ceiling=3, deco="lamp"),
              n("amethyst", arc=3.2, lift=3, spread=0, pedestal=False,
                orbs=1),
              n("ground", arc=4.4, lift=1, spread=0, pedestal=False,
                orbs=2, deco="lamp")]),
], exit_beats=[
    # The overflow well in the corner of the tank. Written out rather
    # than left to the generated climb for the usual reason -- a climb
    # wants solid rock within one cell of its column at the column's
    # middle index and at its top, and a column hung mid-lane at
    # ``hug`` 2.0 with no pedestal has nothing to grab (11,097 of 13,000
    # candidates refused on a generated bubble). The recipe that fires
    # is the landing's **own pedestal** under the column plus a rise of
    # at least four, so the middle cell lands inside the stack rather
    # than in the air below it: hence no ``hug`` at all on the column.
    #
    # ``step_y=6`` is the level's ``rise`` exactly. Short is not free
    # here -- the crossing appended after the climb comes down one on to
    # the next terrace, so a column that overshoots makes GLACIER SHELF
    # open by jumping back down to its own floor, which is the owner's
    # "it puts a ladder there and then jumps back down" in one number.
    # Six blocks of *bubble* is half a second at 11.0 m/s; the same six
    # on a ladder would be two and a half seconds of plate against the
    # lens, which is why this theme exits by water.
    #
    # Nothing overhead on the well head. Both lids RULES 7 recommends
    # for an exit launch were measured on the level below this one and
    # both cost designed content, because a lid that will not fit
    # refuses the launch landing outright and the fallback for a refused
    # ascent node is the generated staircase.
    n("calcite", arc=3.0, lift=1, hug=2.4, spread=2, deco="lamp", orbs=1),
    n("calcite", arc=3.0, step_y=6, kind="bubble", climb_style="water",
      spread=0, deco="lamp", orbs=2),
])
