"""Level 14: THE BELFRY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A pale limestone campanile over a churchyard that has flooded to the
# sill.
#
# One sentence: *you come in through the lych-gate at path level, and
# from there the ground is water -- you cross the drowned nave on the
# tops of the tombs, run under the bell itself, and then you are on the
# tower, going round it on its own cornice until the ladder.*
#
# **What it is answering, and it is not a number.** This level was a red
# village: ``terracotta`` ground, ``brick`` sub, ``roof`` accent, a
# rooftop of tiles and chimneys with lanterns on them -- which is
# MARKET STREET, eleven levels below, wearing the same theme and the
# same three materials. Two levels of thirty-three share the ``village``
# theme and they cannot both be a red street. So this one is the other
# thing a village has: the stone thing at the end of it, pale and
# vertical, with water round its foot. Bone and honey stone with moss in
# the joints where level 3 is terracotta and tile; a shelf with the drop
# genuinely outboard where level 3 is a full plaza; the route on a
# *tower* where level 3's route is on roofs. Between a black sculk
# gallery below and a wool level above, this is the pale one.
#
# **``rise=4`` is the smallest in the tower, and that is the budget this
# level spends.** The exit reserve is ``(need + 1) * 3.2`` measured from
# wherever the body stands, so a four-block level keeps eight to ten
# blocks of terrace that an eight-block one hands straight to its
# staircase. All of it goes into the body: the exit here is two
# landings, a lit footing and one four-block ladder, and everything else
# on screen is the design.
#
# **The bell is machinery and it is the best thing in the level.**
# ``_lm_g_bell`` is a *hop* gate -- two five-tall posts of the theme's
# own rock at three cells apart, an oak headstock beam across the top of
# them, and the bell hanging at ``dy 5`` -- and ``_landmark_nodes``
# steers the course between the posts. So the body runs *under* the bell
# at head height, once a visit, for free. A ledge level's real choice is
# a hop gate or nothing (walk gates reserve 0-2 of 8 on a ledge), and
# this is a hop gate, so ``profile="ledge"`` is safe and ``breaks=0``
# keeps the lock out of the crossing's way.
#
# **Two moats and no lock.** Any ``breaks >= 1`` forces the lock across
# a 5.5-6.7 m hole and costs one to three landings of a level that only
# lays about eleven; the walk number is held down instead by water and
# by the fact that six of the eleven authored landings float with
# nothing under them. Measured on the level this replaces, which was
# built the same way: 8% covered without a jump, 0 of 7 walks got down
# it, against a 55% ceiling.
#
# **The lids are the level's own timber.** ``Course.write`` paints a
# ``ceiling=`` lid with ``pedestal_style or theme.rock``, and on a
# landing that floats there is no plinth for it to paint -- so
# ``pedestal_style="spruce"`` on a floating landing is three cells of
# dark beam at head height and nothing else. That is the rood beam over
# the nave and the joists under the ringing floor, and it is also the
# composition rule: dark mass across the top of the frame, the level's
# own pale ground across the bottom, sky as a slot between them.
LEVEL = Level("THE BELFRY", "village", rise=4, gap=3.0, exit="ladder",
              band=9.5, shelf=4.0, profile="ledge", breaks=3,
              landmark="bell",
              # Warm limestone, green moss and dark timber. ``rock`` is
              # the bell frame's own posts as well as the terrace's
              # outcrops, so it is the tower's stone and not the
              # accent's timber -- a campanile is masonry with the
              # headstock in it, and ``_lm_g_bell`` supplies that beam
              # in oak whatever the theme says.
              ground="plaster", sub="chiselled", rock="sandstone",
              accent="spruce", glow="lantern", liquid="water",
              step=("chiselled", "hop"), dark=0.22,
              # Twelve materials with plaster at 21% and nothing else
              # over a seventh: one committed hue with a long tail under
              # it, which is the shape a real terrace measures as (a
              # median 14 kinds, dominant share 26%).
              #
              # **And the hue is warm, which took a rebuild to learn.**
              # The first pass of this palette was a whitewashed church
              # -- plaster over cobble, stone, andesite, diorite,
              # gravel -- and every one of those is a neutral grey, so
              # the contact sheet came back the colour of the *cone*
              # (118, 113, 109) with pale cubes in it. A level's
              # identity is its floor and a floor has to be a colour.
              # Plaster (226, 218, 200), chiselled (214, 198, 140) and
              # sandstone (222, 208, 150) are bone and honey; mossy
              # (104, 122, 96) is the wet green in the joints, and
              # spruce (114, 84, 50) is the only dark thing at ground
              # level. Grey is what the cliff behind it is for.
              floor=(("plaster", 5), ("chiselled", 3), ("sandstone", 3),
                     ("mossy", 3), ("spruce", 2), ("clay", 2),
                     ("grass", 1), ("gravel", 1), ("oak", 1),
                     ("cobble", 1), ("diorite", 1), ("coarse", 1)),
              # The churchyard's furniture, and one of them is doing a
              # job rather than dressing: ``chain`` is in ``HANGING``,
              # so it is hung from the trough's ceiling rather than
              # stood on the floor -- bell ropes down out of the dark
              # over the running line. ``lilypad`` needs the water the
              # two moats dig.
              props=("chain", "mcfence", "lanternpost", "lilypad",
                     "grasstuft", "pebbles"),
              beats=[
    # The threshold, and it is two nodes because the second one is a
    # walk: a shell is painted the moment its landing commits and then
    # refuses the next landing of the same beat, so ``shell=`` goes on a
    # beat's last node, and a shell roof only survives whole over a
    # ``walk`` anyway -- over a hop it sits in the cell the head sweeps
    # at the apex and ``write`` punches a hole in it.
    #
    # * **the lit flagstone** -- a lantern set flush in the path. The
    #   reference signposts where a level *begins* with exactly this: an
    #   emissive block, and the palette changing completely at it. Below
    #   is sculk and deepslate; here it is bone and water, in one block.
    #
    #   It is a **full block at lift 1** and it took an A/B to get
    #   there. Written as the half step this level wanted -- ``lift=2,
    #   form="slab"``, a +0.5 rise, legal on paper at a reach of 2.52
    #   against a window of 2.00-3.78 -- it placed every time and was
    #   *exact* 7 times in 11: over the same twelve worlds, ``ceiling``,
    #   ``pedestal``, ``hug`` 3.4, ``arc`` 2.8 and ``arc`` 3.6 all read
    #   7/11 to the landing, and the full block at lift 1 read **11/11**
    #   with the beat's design share unchanged. A beat's opener is
    #   placed from wherever machinery left the body, which is the
    #   crossing's ``form="floor"`` landing on this level's own ground,
    #   and asking it for anything but that height is what costs the
    #   exactness. The half step moves to the *gate*, one node later,
    #   where its predecessor is known.
    # * **the lych-gate** -- walked, not jumped, because one impulse
    #   always rises 1.25 m and the head then sweeps the two cells above
    #   every take-off: a lintel low enough to read as a gate is a
    #   lintel no arc gets under. A +0.5 step up onto the gate's own
    #   sill (a slab at ``lift=2`` stands half a block proud of the
    #   block before it), 1.92 m on foot against a walk's 2.4 m limit,
    #   dark timber, with the ``tunnel`` two-metre pinch round it and a
    #   lid at three -- the genre's ``2bc``, the one this motion model
    #   can honestly express.
    ("lychgate", [n("glow", arc=3.2, lift=1, hug=2.8,
                    spread=1, ceiling=3, deco="lamp", orbs=1),
                  n("accent", arc=2.6, lift=3, form="slab", hug=2.8,
                    kind="walk", spread=1, ceiling=3, deco="lintel",
                    shell="tunnel")]),
    # The drowned nave, and this is the level's showpiece beat. Three
    # landings, and the point of them is that the ground has stopped
    # being a route: the first digs its own pond, the second has nothing
    # under it at all, and the third stands in a second pond at the lip
    # of the shelf.
    #
    # * **the first tomb** -- +1 off the gate onto a table tomb, arc
    #   3.2, a reach of 2.52 against a +1 window that stops at 3.10.
    #   Centred and not at the top of it: 3.6 is a reach of 2.92 and is
    #   the arc that has to fall back, and a fallback is not exact.
    #   ``moat`` digs the flood round its foot -- the radius-three bowl
    #   is what actually stops the no-jump walker, because water is in
    #   ``SEE_THROUGH`` and a walker that steps into the hole cannot
    #   step back out.
    # * **across the nave** -- the long one. Level, arc 4.6, a reach of
    #   3.92 against a flat maximum of 4.26, which is a showpiece
    #   distance and is written as one: the roster's ordinary jump is
    #   3.0-3.5 and the real map's modal gap is 3.0. It floats
    #   (``pedestal=False``), so there is nothing under it to walk to,
    #   and it carries the rood beam -- ``ceiling=3`` painted in
    #   ``spruce`` over a landing with no plinth, which is three cells
    #   of dark timber at head height and the darkest thing in the top
    #   of the frame.
    # * **the fallen headstone** -- the level's descent, and it is here
    #   rather than at the end because a level's drop belongs in its
    #   first two thirds and nothing after the high point may go down.
    #   Lift 2 to lift 1 across 3.4 m of arc is a reach of 2.72 against
    #   a one-block-drop window of 2.35-4.98. ``hug=4.2`` on a
    #   four-cell shelf is past the edge on about half the bearings, so
    #   it hangs over the drop with its own second pond under it -- and
    #   it is 8.0 m from the first moat, which it has to be: the bowls
    #   are radius three and a second one inside that radius stands in
    #   the hole the first dug.
    ("nave", [n("rock", arc=3.2, lift=3, hug=3.0, spread=1, moat=True,
                orbs=1),
              n("ground", arc=4.6, lift=3, hug=3.6, spread=1,
                pedestal=False, pedestal_style="spruce", ceiling=3,
                orbs=2),
              n("mossy", arc=3.4, lift=2, hug=4.2, spread=0,
                pedestal=False, moat=True, ceiling=3, orbs=1)]),
], filler=[
    # The tower, and on a level that lays about eleven designed landings
    # this loop is more than half of them -- it repeats and the tail of
    # a script does not, so the level's character lives here and its
    # surprise lives in the nave. Four landings that close into a ring
    # round the campanile, and none of them is at path level: the
    # lowest is a block up and the loop never comes down to the
    # churchyard again.
    #
    # * **the cornice** -- +1 onto the string course, standing on a
    #   timber putlog (``pedestal_style="spruce"``) with a beam over the
    #   head. This is the reference's groove and the loop is built to
    #   hold it: masonry a few metres away on the core side, the drop
    #   outboard, a lid above.
    #
    #   **The whole loop's ``hug`` is measured, and it is not
    #   monotonic.** Written hard against the tower at 2.6 -- which is
    #   what a string course *is* -- the lens is jammed by a flat grey
    #   wall on 8.5% of frames, because this loop is sixty per cent of
    #   the level and the probe counts a jam when over half the lens
    #   sits inside three metres. Over the same four seeds and 2,430
    #   frames: 2.6/2.6/3.2/3.8 read **8.5%**, 3.2/3.2/3.6/4.2 read
    #   **3.7%**, and 3.6/3.6/4.0/4.4 -- further out again -- read
    #   **10.6%**, because past the string course the body is out where
    #   the cliff swings across the aim at a corridor bend. The middle
    #   one costs 3.6 points of empty frame (42.9% to 46.5%, against a
    #   48% rule) and is worth it: a wall filling the lens is a frame
    #   with nothing in it either, and it is the one this tower's own
    #   criteria call out.
    # * **through the louvre** -- a walk, at position *two* and not at
    #   the tail, because a beat lays about half its nodes and a verb
    #   written last is written and never seen. Level, 1.92 m on foot,
    #   under a lid at three: the opening in the belfry's own boarding,
    #   ducked through at a run.
    # * **the corner corbel** -- +1 out onto a stone bracket with
    #   nothing under it and the drop below, three cells of dark joist
    #   overhead. The exposed landing of the loop, and the one that puts
    #   sky behind the bell frame when the crossing has laid it ahead.
    # * **off the corbel** -- the loop's long jump and its way back
    #   down: lift 3 to lift 2 across 4.4 m, a reach of 3.72 against
    #   2.35-4.98. A descent is the only long jump this motion model
    #   has, because falling takes time and the body does not slow down
    #   while it does.
    #
    # The seam back to the first node is the thing half a filler's
    # fidelity is usually lost to, so it is written rather than hoped
    # for: lift 2 to lift 2 across 3.2 m is a level hop of 2.52. And
    # there is no ``moat`` anywhere in here -- the filler loops, and the
    # second lap digs away the ground the first lap's pedestals stand
    # on. This level's water is the two ponds in the nave.
    ("cornice", [n("rock", arc=3.2, lift=2, hug=3.2, spread=1,
                   pedestal_style="spruce", ceiling=3, orbs=1),
                 n("accent", arc=2.6, lift=2, hug=3.2, kind="walk",
                   spread=1, ceiling=3, deco="lintel"),
                 n("ground", arc=3.2, lift=2, hug=3.6, spread=0,
                   pedestal=False, pedestal_style="spruce", ceiling=3,
                   orbs=2),
                 n("sub", arc=4.4, lift=2, hug=4.2, spread=0,
                   pedestal=False, orbs=1)]),
], exit_beats=[
    # The way out is the ringing chamber: a lit footing at the tower's
    # foot and one ladder up the inside of it. Two landings, because
    # ``rise=4`` is the smallest in the tower and a four-block climb is
    # one ride -- and because a climb exit belongs on about one level in
    # five, for a level whose *idea* is the climb. A bell tower is the
    # example that rule is written about.
    #
    # **The launch block's ``hug`` is most of the level's jammed-lens
    # number.** With the design settled, jam by segment over four seeds
    # and 2,430 frames reads **nave 0%, cornice 0%, lychgate 0%** --
    # every wall-filled frame this level has is machinery. At the 2.8
    # the rest of the tower settled on, the level reads **3.7%**; at
    # 3.2, **1.2%**, for 2.3 points of empty frame. Further out again
    # (3.6) buys no more jam and costs another point of sky, so 3.2 is
    # the knee. ``hug`` on the climb node itself is inert -- 2.0 through
    # 3.0 produce identical worlds -- so only this one matters.
    #
    # What is left at 1.2% is **the bell's own posts**, and it is not
    # fixable from here. Sampling the material every ray lands on when
    # most of the lens is close: 709 hits of sandstone under the
    # ``landmark`` crossing against 141 anywhere else. ``_lm_g_bell``
    # stands two five-tall columns of ``theme.rock`` one cell either
    # side of a three-cell passage and the course is steered between
    # them -- so being under the bell is a wall to the left and a wall
    # to the right, by construction. Whatever ``rock`` is made of, it is
    # a wall; the landmark is frozen and this is the price of it, and
    # the frames either side of it are the best in the level.
    #
    # **And the ladder carries no beam, which was tried and is the
    # trap this document warns about.** ``ceiling=3`` on the climb node
    # -- the joists under the ringing floor, and the exit climb is 36%
    # of the frames spent on this level and the emptiest part of any
    # level in this tower -- measured **48.1% empty down to 45.3%** with
    # the jam unmoved, and it is a mirage: the lid stands in the ladder
    # column, ``_climb_move`` finds nothing to hang on, and the climb
    # silently becomes hops. The giveaway is that the level got 16%
    # *shorter* in frames, because a ladder is ridden at 2.35 m/s and a
    # hop is not, and the proof is that ``climb`` left the move mix by
    # name and the hop share went 82% to 87%, through the 85% rule.
    # Nothing reports it. Check the mix for ``climb`` after touching
    # anything here.
    #
    # **No ``shell="shaft"`` round it**, which the version this replaces
    # had. The tube is what puts the body inside the wall, and the
    # pedestal-plus-``step_y >= 4`` recipe anchors the ladder on its
    # own: ``_climb_move`` wants solid rock or pedestal within one cell
    # of the column at its middle index and at its top, and a plinth
    # under a four-block rise puts the middle cell on the landing rather
    # than on the stack below.
    #
    # **The arithmetic of ``step_y=4`` against ``gap=3.0``.** The
    # crossing is a fixed ``gap + 1.4`` of arc, so a reach of 3.72 --
    # legal level (2.00-4.26), down one (2.35-4.98) and down two
    # (3.12-5.56), and the intersection of those three is 3.12-4.26,
    # which 3.72 sits in the middle of. The footing is pinned at
    # ``lift=2`` with one of fallback, so the ladder tops out at surface
    # 5, 6 or 7 against a next floor at 4: one, two or three blocks
    # above it, and the crossing comes down onto it. What it must not do
    # is finish *below* four, which is why the footing is an absolute
    # ``lift`` rather than a ``step_y`` and why it is 2 rather than 1.
    # ``lift=1`` and not 2, applied by the coordinator after a tower-wide
    # check. The launch height plus the ride's ``step_y`` is where the climb
    # tops out, and at lift 2 + 4 this ended **6** over the terrace against a
    # ``rise`` of 4. A crossing cannot find the far ground from more than one
    # block over the next floor: it is refused, the body comes back down onto
    # this terrace, and the reliability chain climbs out all over again --
    # five ascent landings a visit, reading 100% on every per-beat check
    # because every landing was placed. Another level instrumented exactly
    # that; ``tower_probe --design-only`` now asks the question for the whole
    # roster and this was the only level that failed it.
    n("glow", arc=3.4, step_y=0, hug=3.2, spread=1, confine=True,
      pedestal_style="cobble", ceiling=3, deco="lamp", orbs=1),
    n("rock", arc=2.4, step_y=3, kind="climb", climb_style="ladder",
      hug=2.4, pedestal_style="cobble", spread=0, confine=True, orbs=2),
])
