"""Level 33: THE GATE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE GATE. The top of the tower, and the door out of it. A pale
# endstone causeway laid along the last shelf of rock, with a black
# gatehouse standing on it: two obsidian piers with fire burning in
# their heads, a lintel across the top, and the course going **through**
# it rather than past it. You come in at a magma sill, stride under two
# black lintels, climb the near pier, walk the gate head three blocks up
# with the void off your shoulder, and then **fall off the far side of
# it** -- two blocks down and four and a half metres out onto a lit
# stone hanging over nothing. Then the court behind the gate, and a
# black-and-white stair up the back of the gatehouse to the crown, where
# the tower ends and the loop starts again in a green meadow.
#
# The thing a viewer remembers is the fall off the gate head: the last
# built thing in the tower is behind you, the lamp is on a stone with no
# ground under it, and the sea is a very long way down.
#
# ---------------------------------------------------------------------
# **The landmark is the level.** ``landmark="totem"`` is frozen, and its
# gated variant (``_lm_g_totem``) is two obsidian piers six blocks tall,
# a lintel across their heads and ``theme.glow`` set in both of them --
# which is a gatehouse with a fire in each pier, and the crossing steers
# the course straight through the middle of it. So the level does not
# need to build its own gate; it needs to be *made of* gates, so that the
# big one reads as the last and largest of a series. Hence the verb:
# every beat here has a ``kind="walk"`` stride under a ``ceiling=3``
# lintel, which is the genre's `2bc` and the only honest head-hitter this
# kernel has -- one jump impulse rises 1.25 m, so the head sweeps the two
# cells above every take-off and an *arc* under a beam low enough to read
# as a doorway is refused every time. A walk has no arc, so the check
# never fires. Measured over 8 runs and 265 landings: **hop 81%, walk
# 19%**, against a roster at 94% hop and a rule of no more than 85%.
#
# **``glow`` is ``magma`` and that is a correctness fix, not a taste
# one.** ``spiral._GLOWING`` is ``lantern``, ``torch``, ``glowstone``,
# ``sealantern``, ``magma`` and nothing else; this level used to name
# ``amethyst``, which is a bright *texture* that emits not one photon, so
# both of the totem's fires and every ``glow`` landing in the level were
# dark violet blocks. Magma is also the only warm source in that list,
# and THE PILLARS eleven levels below took the cold one (``sealantern``)
# expressly so that the two End levels do not light the same way.
#
# **Pale floor, black gate -- the inverse of THE PILLARS, on purpose.**
# Level 22 is the approach: an orchid-violet purpur court with black
# pillars broken across it. It says so in its own header and left the
# end-of-the-world imagery here. So this level inverts it -- ``endstone``
# is the dominant floor at 26% of the palette, ``calcite`` and ``quartz``
# under it, and purpur is demoted to a stripe in the tail. That number
# is the reference's own (median 14 floor materials, dominant share 26%);
# the theme's stock mix is purpur 3 / obsidian 2 / chorus 2, which is why
# the old contact sheet of this level came back lilac-and-grey with the
# "pale endstone causeway" nowhere in it. ``rock`` is ``blackstone``
# rather than purpur for the same reason: what stands up out of the
# causeway should be black, so the gate is a silhouette and not one more
# violet cube among violet cubes.
#
# **The seam is the biggest contrast in the roster and it is free.**
# Behind is THE WHITE STAIR -- quartz and gold, a thirteen-block channel
# court. Ahead, and this is the only place in the tower where the cycle
# closes, is THE GATEHOUSE: grass, moss, oak, water, a ten-and-a-half
# block plaza. So this level is the tightest corridor of the three
# (``band=9.5``), the darkest, and the only warm-lit one, and the last
# thing before the seam is deliberately a lit stone with **sky** behind
# it rather than cliff -- the stair steps outward as it climbs (``hug``
# 2.9 -> 3.5) so the crown stands clear, and the next frame is green.
#
# **The exit is a stair, and it is four treads.** ``rise=4`` is the
# smallest in the tower: the body reaches the chasm at lift 1, the next
# terrace's walking surface is four above this one's, and the crossing
# comes down a block -- so the top tread wants lift 5 and the launch plus
# four treads is exactly that. No ladder: measured over four seeds and
# bucketed by move, an ``ascent/climb`` ride is 20.9% wall-jammed where
# every other move in the same level is 0.0%, because the wall a ladder
# hangs on *is* the wall in the lens and ``hug`` on a climb node is
# inert. No bubble either -- THE PILLARS is the End level whose idea is
# the climb, and two water columns in one theme is one too many. Written
# on ``step_y`` throughout, never on absolute ``lift``, because ``lift``
# is silently clamped at ``LIFT_MAX = 6``.
#
# What the cheap exit buys is the body of the level: the reserve is
# ``(need + 1) * 3.2`` metres of terrace, so a four-block rise hands back
# about ten blocks against the roster's tall levels. It is spent on an
# eight-node opening beat -- the one beat that is never truncated --
# which is the whole level: threshold, three doorways, the climb up the
# pier, the walk through the gate head, the fall, and the landing back in
# under a rough roof. Measured: every script beat 100% placed, 100%
# exact, 0 unchecked emergency placements, designed content 60%.
#
# **One thing to know before reading this level's jammed-lens number.**
# ``level_review`` stops counting camera frames when ``scene.tier``
# changes, and the tier does *not* tick over at the 33 -> 1 wrap, so its
# 6.3% for THE GATE is measured over THE GATEHOUSE as well. Bucketed by
# segment and move over four seeds -- the method the docs ask for -- the
# 117 of 133 jammed frames sit on ``ascent/climb``, which is level 1's
# authored ladder; **every one of this level's own buckets reads 0.0%**,
# including ``ascent/hop``, the black stair, at 0 of 305 frames. The
# residue is 16 frames on ``start``, which is the pin's artificial
# opening and does not exist in an unpinned run. This is the only level
# in the roster where that tool limitation can bite, because it is the
# only one whose next level is index 0.
LEVEL = Level("THE GATE", "end", rise=4, gap=3.0, exit="stair",
              band=9.5, shelf=4.0, breaks=3, landmark="totem",
              # Pale causeway, black gate, one warm light. ``sub`` is
              # calcite rather than blackstone so the *cut face at the
              # rim* stays pale too and the terrace reads as a bright
              # plate with the dark cliff over it -- the reference's own
              # composition, light in the bottom of the frame and dark
              # across the top.
              ground="endstone", sub="calcite", rock="blackstone",
              accent="obsidian", glow="magma", liquid="lava",
              # The ring light is ``mix(white, sky, 0.35 + 0.45 * dark)``
              # multiplied over everything. ``end``'s own (46,38,66) at
              # 0.62 is a 48% grey wash, which is what made the old sheet
              # of this level four near-black frames in twenty-eight;
              # (122,98,138) at 0.42 is 54% and lilac. Obsidian still
              # comes out near-black -- it should, it is the silhouette
              # -- but it now has pale endstone behind it instead of more
              # obsidian.
              dark=0.42, sky=(122, 98, 138),
              props=("endrod", "chorus", "pebbles", "lanternpost"),
              candy=("purpur", "amethyst"),
              # Fourteen materials with endstone at 26%, which is the
              # shape a real terrace measures as. The roles are weighted
              # 4/2/2/2 on top of this, so the totals are endstone 8,
              # calcite 4, blackstone 4, obsidian 3, quartz 2, purpur 2
              # and a tail of ones -- pale stone underfoot, grit and
              # sculk in it, and the one violet in the level is a stripe
              # rather than the plate it used to be.
              floor=(("endstone", 4), ("calcite", 2), ("quartz", 2),
                     ("blackstone", 2), ("purpur", 2), ("obsidian", 1),
                     ("amethyst", 1), ("sculk", 1), ("deepslate", 1),
                     ("diorite", 1), ("chorus", 1), ("stone", 1),
                     ("tuff", 1), ("gravel", 1)),
              step=("obsidian", "hop"), beats=[
    # THE GATEHOUSE -- the whole level in one beat, because this is the
    # only stretch that is laid whole on every visit and because the
    # climb and the fall have to be in the *same* beat: machinery is
    # inserted between beats and hands the body back at lift 1, so a
    # three-block drop written across a beat boundary is a drop that is
    # not there about half the time.
    #
    # Everything behind the opener is on ``step_y`` rather than ``lift``.
    # The opener carries ``spread``, so it lands a block high or low
    # about a fifth of the time, and ``lift + 1`` on the node after it is
    # then a rise of two, which nothing in this motion model makes.
    # ``step_y`` is measured between walking surfaces and is true
    # wherever the body actually is.
    #
    # 1. The sill: a magma block on a rise in the pale paving, lit, with
    #    a black lintel three cells over it. The reference signposts
    #    where a level *begins* with an emissive block set in the floor
    #    and the palette changing completely at it, in one frame, with no
    #    blend -- and behind this one is a quartz-and-gold court, so the
    #    change is white to black in a single step. ``lift=1`` and not 2:
    #    the identical threshold beat measures 67% at lift 2 and 100% at
    #    lift 1, because an opener is placed from wherever the machinery
    #    between levels left the body.
    # 2. **The first doorway, on foot.** A calcite tread with an obsidian
    #    plinth and an obsidian lid over it (``pedestal_style`` paints
    #    both). Position two and not one, because a walk needs its
    #    predecessor within half a metre and a beat's first landing has
    #    no such guarantee -- and not the tail either, because a beat
    #    lays about half its nodes and a verb written last is written and
    #    never seen.
    # 3. **Up onto the pier, and that is the third landing of the
    #    level.** 55% of authored landings in this tower sit at lift 0-1;
    #    from here nothing in this level touches the causeway again until
    #    the fall. +1 at ``arc=3.2`` is a reach of 2.52 against a +1
    #    window of 2.00-3.10 -- centred, not pressed against the top of
    #    it, because a +1 written at 3.6 is the arc that has to fall back
    #    and a fallback is not ``exact``. It keeps its pedestal and its
    #    plinth is obsidian: on a level about a gatehouse, the stack under
    #    this landing *is* the near pier.
    # 4. A stride along the top of the pier, under the second beam.
    #    **Three walks in this beat is what holds the level under the 85%
    #    plain hop the rules allow**: with two it measured 86%, because
    #    the exit stair is a quarter of everything laid and can only ever
    #    be hops. The opening beat is the only cheap place to put a verb
    #    -- it is never truncated, so a node written into it is a node
    #    that is actually seen, where one added to a later beat or to the
    #    filler is written and about half of it never laid.
    # 5. Up onto the gate head, +1 again and a little further out. This
    #    one floats -- it is the lintel course, and a lintel with a
    #    column of masonry under it is a wall.
    # 6. **Through the gate**, three blocks up in the air, walked under a
    #    black beam with the drop a metre and a half off the shoulder.
    #    This is the level's picture and the reason the verb is a walk:
    #    a doorway is *walked* through and never jumped through.
    # 7. **Off the far side of it.** ``step_y=-2`` at ``arc=4.9`` with
    #    1.2 m of ``hug`` outboard: a reach of about 4.39 against a -2
    #    window of 3.12-5.56, and the level's long jump, because a
    #    descent is the only long jump this motion model has -- falling
    #    takes time and the body does not slow down while it does. It
    #    lands lit, on pale calcite at ``hug=4.4``, which is past the
    #    shelf: the stone is floating over the drop with the sea under
    #    it, and it has to float, because ``_targets`` silently returns
    #    nothing when a pedestal is asked for past the shelf edge.
    #    The level's descent is here, at about 60% of the way through it,
    #    and nothing after it goes down: the exit stair is the highest
    #    thing in the level.
    # 8. Back in against the cliff, +1 onto a black shelf under a rough
    #    roof. ``arc=3.2`` with 1.4 m of ``hug`` coming back in is a
    #    reach of 2.88, just inside the +1 limit of 3.10 -- the inward
    #    swing is part of the jump and has to be paid for out of the arc.
    #    The ``shell`` rides the beat's **last** node, which is the only
    #    place one may go: a shell is painted the moment its landing
    #    commits and its roof then refuses the next arc of the same beat.
    #    At lift 2 it grows a roof and open sides, which is what is
    #    wanted -- what these sheets are short of is not walls but the
    #    dark brow across the top of the frame.
    ("gatehouse", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1,
                     deco="lamp", ceiling=3, orbs=1),
                   n("sub", arc=3.2, step_y=1, hug=3.0,
                     spread=0, ceiling=3, pedestal_style="obsidian",
                     orbs=1),
                   n("rock", arc=2.9, step_y=0, hug=3.0, kind="walk", spread=0,
                     pedestal_style="obsidian", orbs=1),
                   n("accent", arc=2.9, step_y=0, hug=3.0, kind="walk",
                     spread=0, ceiling=3, pedestal_style="obsidian"),
                   n("accent", arc=3.2, step_y=1, hug=3.2, spread=0,
                     pedestal=False, orbs=1),
                   n("accent", arc=2.9, step_y=0, hug=3.2, kind="walk",
                     spread=0, pedestal=False, ceiling=3,
                     pedestal_style="obsidian", orbs=1),
                   n("sub", arc=4.9, lift=2, step_y=-1, hug=4.4, spread=0,
                     pedestal=False, deco="lamp", orbs=2),
                   n("rock", arc=3.2, step_y=1, hug=3.0, spread=0,
                     pedestal=False, shell="cave", orbs=1)]),
    # THE COURT behind the gate: a bowl of lava cut in the causeway with
    # a pale stone standing in it, a third doorway straight over the top
    # of the fire, and two black steps out of it to the highest ground in
    # the body of the level.
    #
    # The ``moat`` is on the beat's **first** node and the two landings
    # after it float, which is the only safe arrangement: the bowl is a
    # radius-three disc dug the moment the landing commits, and a pedestal
    # cannot stand in a hole. It is well over ten metres from anything
    # else that digs. And it is written **without** ``pedestal_style``,
    # which is the trap: ``Course._moat`` fills its bowl with
    # ``pedestal_style or theme.liquid``, so a landing carrying both cuts
    # a hole and packs it with walkable stone -- no error, no rejection,
    # nothing in the fidelity table. The previous version of this level
    # had that pair on two separate nodes.
    #
    # Honest about what the lava buys: **atmosphere and not
    # unwalkability.** Lava is solid in this engine and a no-jump walker
    # strolls across the top of it; only water is see-through, and water
    # in the End is somebody else's level. What holds the walk number
    # here is the floor breaks, the floating landings and a four-block
    # shelf with the void immediately outboard.
    #
    # It ends **high**, at lift 3, and that is worth more than another
    # landing would be: ``_feat_ascent``'s budget is the next level's
    # floor minus wherever the body actually got to, so a beat that hands
    # the chasm a body three blocks up has already paid for most of the
    # way out.
    #
    # Every landing here stands at ``hug`` 2.9 or more and the beat walks
    # steadily outboard, 2.9 -> 3.2 -> 3.4 -> 3.8. **``hug`` is the
    # jammed-lens number on ordinary landings and not only on climbs**:
    # one level bucketed its jammed frames by move and found a single
    # beat's ``walk`` at 41% with every other move at 0.0%, and moving it
    # out by six tenths of a block took the whole level from 5.7% to 1.5%.
    # The core face is a wall like any other, and a body at 2.6 has it
    # inside the probe's three-metre threshold across half the ray fan.
    ("court", [n("ground", arc=3.4, lift=2, hug=2.9, spread=1, moat=True,
                 ceiling=3, orbs=1),
               n("accent", arc=2.9, step_y=0, hug=3.2, kind="walk",
                 spread=0, pedestal=False, ceiling=3,
                 pedestal_style="obsidian"),
               n("rock", arc=3.2, step_y=1, hug=3.4, spread=0,
                 pedestal=False, orbs=1),
               n("glow", arc=3.2, step_y=1, hug=3.8, spread=0,
                 pedestal=False, shell="cave", orbs=2)]),
], filler=[
    # THE CAUSEWAY. The filler repeats and a script's tail does not, so
    # this is what the level mostly *is*: the pale endstone road under a
    # black eave, a fire set in it, and a black stone standing out over
    # the drop. Four nodes and not three so the loop is a **cycle** --
    # it climbs two and falls two every lap, and the body spends the
    # level between lift 1 and lift 3 rather than running flat with sky
    # under two thirds of the view.
    #
    # The opener is 4.4 m because it has three different heights to be
    # legal from. It follows the court's last landing, or the loop's own
    # last landing, or a piece of machinery back down on the causeway:
    # at -2 that is a reach of 3.81 (window 3.12-5.56), at -1 3.72
    # (2.35-4.98) and level 3.72 (2.00-4.26). The loop's seam is checked
    # like any other jump and half of what a filler ever loses is there.
    #
    # **No ``moat`` anywhere in here.** The filler loops, and the second
    # lap digs away the ground the first lap's pedestals stand on --
    # 27,859 "pedestal will not stand" refusals from that one keyword
    # when it was instrumented. This level's fire is in the court, which
    # plays once.
    # It steps outboard as it climbs for the same reason the court does:
    # the two landings that keep a pedestal stay at 2.9 and 3.0, where a
    # four-block shelf that wobbles about +/-1.3 still has ground under
    # them, and the two that float go out to 3.4 and 3.8 where the core
    # face is out of the lens.
    ("causeway", [n("ground", arc=4.4, lift=4, hug=2.9, spread=1,
                    ceiling=3, orbs=1),
                  n("accent", arc=2.9, step_y=0, hug=3.0, kind="walk",
                    spread=0, ceiling=3, pedestal_style="obsidian"),
                  n("glow", arc=3.2, step_y=1, hug=3.4, spread=0,
                    pedestal=False, orbs=1),
                  n("rock", arc=3.4, step_y=-1, hug=3.8, spread=0,
                    pedestal=False, orbs=1)]),
], exit_beats=[
    # THE CROWN. A black-and-white stair up the back of the gatehouse,
    # alternating obsidian and calcite treads, lit at the bottom and at
    # the top and nowhere in between -- every lamp in the reference is at
    # an end of something and doing a job.
    #
    # **Four treads, and the arithmetic is the whole design.** The body
    # arrives at the chasm at lift 1 (walking surface 2.0 over a terrace
    # floor at 1.0). The next level's terrace stands ``rise=4`` above
    # this one, so its walking surface is 5.0, and the crossing is
    # written as ``hop_span(-1)`` -- it comes down a block. So the top
    # tread wants a walking surface of 6.0, which is lift 5, which is the
    # launch plus four ``step_y=1`` treads. Not one of these is written
    # on absolute ``lift``: ``lift`` is clamped to ``LIFT_MAX = 6``
    # *silently*, and a level that wrote 2..9 there ground against the
    # chasm for twelve landings a visit with nothing in the fidelity
    # table saying so.
    #
    # **The launch stands at ``hug=2.9``, and that one number is most of
    # an exit's jammed lens.** Measured elsewhere: 69 wall-jammed frames
    # of 1,293 with the launch at 2.2 and **0 of 1,280** at 2.8. The
    # camera locks on to the landing through take-off and flight, so a
    # launch tucked against the core aims the whole climb at the cliff.
    # It carries a ``cave``, which takes its chimney out of the reserved
    # climb cells for nothing and is the single biggest frame win an exit
    # has -- the climb is the emptiest third of any level in this tower.
    #
    # **And the stair walks *out* as it rises**, 2.9 -> 2.9 -> 3.1 ->
    # 3.3 -> 3.5. A four-tread stair chained at one ``hug`` against a
    # cliff two and a half metres away is four consecutive frames of flat
    # rock; stepping it outboard puts sky behind the last two treads. The
    # beams stop after the third for the same reason: the crown is the
    # last frame of the tower before the loop restarts in a meadow, and
    # it should be a lit stone against sky, not a lid.
    #
    # No ladder and no bubble here. A ladder is ridden at 2.35 m/s with
    # the column a hand's width from an eighty-degree lens, and bucketed
    # by move it measures 20.9% wall-jammed against 0.0% for everything
    # else in the same level; a five-tread stair read 1.0% against a
    # ladder's 5.4% for identical designed content. A bubble is the other
    # good answer and belongs to THE PILLARS, whose idea is the climb.
    # This level's idea is the gate, and a stair on the gate's own
    # obsidian is a quieter ending rather than a worse one.
    n("glow", arc=3.2, step_y=0, hug=2.9, spread=2, confine=True,
      deco="lamp", ceiling=3, shell="cave", orbs=1),
    n("glow", arc=3.2, step_y=1, hug=3.5, spread=0, deco="lamp", orbs=2),
])
