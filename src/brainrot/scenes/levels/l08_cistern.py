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
# You come in over the coping on a lantern set flush in the stone and
# sprint under a stalactite with the water already dug out beside you.
# Two treads take you to the top of the tank's inner wall, and then you
# go off the front of it -- two blocks down and four and a half metres
# out, the long jump of the level -- onto the one algae-covered stone
# lying in the bottom, which throws you **two blocks straight back up**
# on to the crystal. That bounce is the only place in this motion model
# where a landing gains two, and it exists only because of the fall that
# feeds it. Then the tank wall opens into two metres of crystal chamber
# crossed on foot, and you leave up the overflow well in the corner on a
# bubble column.
#
# **The landmark changed from ``arch`` to ``cluster``, and that is why
# this level was rebuilt rather than patched.** ``cluster`` is an
# amethyst geode -- four cells, three blocks tall, and the *only* one of
# the fifteen blueprints with no gated variant, deliberately
# (``spiralplan.GATED``'s footnote: its two deep-dark levels measured
# worse with a five-cell gate across them). So there is no crossing to
# steer the course through it and no way to make it bigger, and a
# four-cell blob standing beside a runner is never going to hold 25
# degrees for a second and a half. Measured here: it **reserves 12 of 12
# runs** on this profile and is on screen for **0.0 s** all the same.
# The reference agrees that this is the wrong thing to lean on -- the
# median biggest mass on a real terrace is twelve cells and four blocks
# tall, and identity comes from the floor (RESEARCH 4).
#
# So the crystal is the level's *palette* rather than its monument, and
# the thing you would remember is a purple column with a lantern on it
# standing in a white-and-brown tank. ``accent="amethyst"`` speckles it
# through the ground; four landings are cut from it -- the block the
# bounce throws you on to, both halves of the chamber, and the floating
# spur in the filler -- and the geode blueprint then reads as one more
# outcrop of the same seam rather than as a lilac ornament dropped on a
# grey plate.
#
# ``profile`` was ``channel``, and this is the second-largest change.
# A channel cuts its liquid two cells wide at 3.6 out from the core --
# which is where ``Course.lane_radius`` puts the running line -- and an
# *ungated* landmark cannot reserve on a ``ledge`` at all (RULES 7), so
# the level's real choice was channel or plaza. A plaza is also what a
# cistern actually is: the reference's answer to a wide floor is not to
# narrow it but to make its whole width hazard (RESEARCH 8), and this
# floor is water in holes, floating landings and one lock across a
# break. It measures 19% covered by a no-jump walker against a 55% rule.
#
# The identity is the floor: thirteen materials, none over a fifth --
# brown dripstone and grey tuff, blue-grey clay silt, deepslate where it
# stays wet, gravel and moss and mossy cobble along the waterline, one
# copper fitting, amethyst speckled through all of it. Against CANOPY
# WALK's jungle green below and GLACIER SHELF's snow and blue ice above,
# this level is brown, white and purple and is not confusable with
# either from a single frame.
#
# Two skin decisions are load-bearing and were both taken off the
# contact sheet rather than off a number:
#
# * **``sub`` is deepslate, not amethyst.** The first rebuild put the
#   crystal on ``sub``, which is the lowest two cells of the cliff at
#   every bearing (``Cone.cliff_style``, ``h < 2``), the cut face under
#   the terrace lip (``_slab``, depth 1) and every shell roof -- on
#   paper a seam running the length of the tank, on the sheet whole
#   flat lilac walls filling the lens for a quarter of the level. A dark
#   sub is also the reference's own composition: the brow at the top of
#   the frame is the darkest thing in it.
# * **``rock`` is dripstone, not calcite.** ``rock`` is the shell's wall
#   material and the default material of a ``ceiling=`` lid, and calcite
#   is a near-white 222 with almost no texture -- the two frames the
#   body spends inside the chamber came back as a blank pale plate. Brown
#   grainy dripstone walls and brown lids read as a cave and warm the top
#   of the frame; the white is then spent where it is worth something,
#   on the landings, which are named literally.
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
    #   2. off the coping on to a stone standing in the tank, on
    #      ``step_y`` rather than ``lift`` so the rise is measured from
    #      where the body actually is, and floating -- the moat one
    #      landing back digs a bowl of radius three that a plinth 3.2 m
    #      along would have to stand in. ``pedestal_style`` is *not* on
    #      the moat node: ``Course._moat`` fills the bowl with
    #      ``pedestal_style or theme.liquid``, so the two keywords
    #      together cut a hole and fill it with solid walkable stone,
    #      with nothing reporting it.
    ("coping", [n("glow", arc=3.0, lift=1, spread=2, deco="lamp", orbs=1,
                  ceiling=3, pedestal_style="dripstone"),
                n("calcite", arc=2.9, lift=1, kind="walk", spread=0,
                  ceiling=3, moat=True),
                n("calcite", arc=3.2, step_y=1, spread=0, pedestal=False,
                  orbs=1)]),
    # The tank, and this is the level. Four landings, and every number
    # in them is forced by something:
    #
    #   0. the tank's inner wall at lift 2, reachable from lift 1, 2 or
    #      3 -- because machinery is inserted between beats and leaves
    #      the body back at lift 1, so an opener written at the height
    #      the beat wants is an opener that falls back.
    #   1. the coping above it on ``step_y=1``, which is +1 from
    #      *wherever node 0 actually landed* rather than +1 from the
    #      terrace. The highest dry stone in the level and the thing you
    #      aim at from the door. ``arc`` 3.2 is a reach of 2.52 against a
    #      +1 window that shuts at 3.10; 3.6 would be a reach of 2.92 and
    #      would spend its life falling back.
    #   2. **off the front of it: two blocks down, 3.92 m of reach.** The
    #      longest jump here and the only way to buy one -- nothing rises
    #      two in one impulse, but falling takes time and the body does
    #      not slow down while it does, so -2 reaches 5.56 where level
    #      reaches 4.26. Written as an absolute ``lift=1`` and not as
    #      ``step_y=-2``, and that one keyword was worth ten points of
    #      this beat: a ``step_y`` landing is placed at
    #      ``prev_surface + step_y``, so on the runs where node 1 came up
    #      a block short the drop was aimed one cell *inside the terrace
    #      floor* and every candidate was refused as "landing occupied"
    #      (instrumented: 7 of 20 visits, 1,680 refusals, all cone rock).
    #      Aimed at the floor instead it is a -2 when the climb worked
    #      and a -1 when it did not, and 4.6 with its 0.84/1.18 fallbacks
    #      is legal in both windows.
    #   3. and the fall is what pays for the next jump. A bounce is
    #      thrown by the speed it arrived with: that arc lands at 11.35
    #      m/s, ``bounce_launch`` keeps 96% of it, and 10.90 is over the
    #      10.58 a **two-block** gain needs. One block less of drop, or
    #      an arc a metre shorter, and this is an ordinary hop with the
    #      beat still reading as placed. ``spread=1`` is not optional
    #      either -- at ``spread=0`` the bounce is refused outright and
    #      the landing is quietly placed a block lower.
    #
    # The rise and the drop are inside *one* beat and that is not
    # tidiness: a beat that opens by dropping off the height the beat
    # before it climbed to drops nothing about half the time.
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
    # there and a tunnel over a jump is a roof with a hole in the middle
    # of it. It only survives whole over a leg that never leaves the
    # ground. Its walls come out ``theme.rock`` and its roof
    # ``theme.sub`` -- brown dripstone and dark deepslate -- and the two
    # amethyst landings are what is inside it. One shell and no more:
    # three in a row jam the lens on 10-21% of frames, and the reference
    # is fully enclosed 6.1% of the way with a median enclosed run of
    # two metres (RESEARCH 4).
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
      spread=0, deco="lamp", orbs=2, pedestal_style="dripstone"),
])
