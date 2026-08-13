"""Level 29: THE CORNICE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# An avalanche gallery under a snow cornice.
#
# The old version was white cubes on a pale blue sky: 60% of the frame
# empty, 73% of the design placed, and its cabin never stood up once.
# Three things were wrong with it and all three are geometry rather than
# taste.
#
# * **It ran out at the rim.** Every landing hugged 5.6-8.8 on a band of
#   8.5 with a shelf of 4.0, so the body spent the level out over the
#   drop with nothing but sky in front of it -- and the two beats that
#   asked for it, ``ridge`` (hug 5.8, pedestal on) and ``cornice`` (hug
#   8.8, past the band entirely), were the tower's two worst-placed
#   beats through every pass. A pedestal cannot stand past the shelf and
#   a landing cannot stand past the rim. Everything here hugs 2.8-4.0:
#   the cliff is a few metres off the shoulder, the drop is outboard,
#   and something is overhead. That is the groove the real map measures
#   as (a wall within 4 m on 71% of samples, a lid on 98%).
# * **The cabin is a walk gate**, and a walk gate reserves 0-2 times in 8
#   on a ledge where a hop gate reserves 8 of 8 (``docs/RULES.md`` §7).
#   So the level's one structure was never built and the frame never
#   held one. The crane is a hop gate, it is made of spruce, and its
#   **jib passes over the run six blocks up** -- a timber cable-crane
#   above an alpine shelf is both the thing you would name the place
#   after and a lid in the top of the frame.
# * **It was one value.** White snow, pale ice and a pale sky read as a
#   single wash, which is the mistake GLACIER SHELF fixed by keeping the
#   terrace light and building everything on it dark. Here the floor is
#   snow -- the lightest thing low in the frame -- and everything built
#   is dark spruce and dark oak decking, with the cliff dark above and
#   one warm lantern doing the only job light does on this level.
#
# The place: a snowfield pinned under an overhanging lip and broken into
# islands, decked in timber, with meltwater cut through the deck, a lit
# gallery roofed against the cornice, and the crane standing at the turn.
# It falls into the notch a third of the way along and climbs from there
# to the gallery's own ledges, which are the highest thing in it.
#
# **It is a broken plaza now, and that is the answer to the empty frame.**
# The rebuild above fixed the palette, the structure and the fidelity and
# left one thing wrong: the owner picked this level out of a contact sheet
# as white cubes against a pale wash, and the rule tightened to *under 48%
# of the view empty*. As a ``ledge`` of 4.5 on a band of 8.5 it measured
# **55.4% over eight seeds**, and the reason is where the ray fan goes: the
# probe fires 25 rays inside an 8 m horizon, and on a 4.5-block shelf the
# whole outboard half of them clears the rim and reaches the sea. Roofs
# barely touch that -- three shells added to the exit stair moved it under
# a point. Ground does: **``plaza`` on ``band`` 10.5, with ``breaks=3``,
# and a checked lid over every arc in the level, reads 47.5%.**
#
# A wide *ledge* was tried instead of the plaza and is worse on the same
# worlds (shelf 6.5 on band 10.5: 49.2% against 47.8% on the diagnostic
# that compared them), so the profile is doing real work and not standing
# in for the band. **Quote the two endpoints and nothing between them**:
# the intermediate steps were measured with a per-segment diagnostic that
# calls the ray fan on a slightly different frame from ``level_review``'s
# own camera pass and reads two to three points high, which is fine for
# ranking two candidates and useless as a number to record.
#
# **A plaza is only legitimate broken and dressed** -- an undressed one is
# what killed the first tower -- so ``breaks=3`` and both meltwater moats
# stay, and they hold it: a no-jump walker covers 38% of it against a
# limit of 55 and the reference's own 46%, and none of thirty-seven walks
# crossed a level end to end. The break count is also a *frame* lever in
# its own right: the lock builds an approach stack and an island out over
# its hole, and those blocks stand in the corridor ahead of the body where
# an open shelf has nothing (lock frames read 47.6% empty against the
# level's 47.5% and the exit climb's 55.1%).
#
# **Everything overhead is a ``ceiling`` beam, not a shell, and the reason
# is worth knowing.** ``_ceiling_cells`` spreads its ``n`` cells along the
# *direction of travel*, so ``ceiling=5`` roofs nearly the whole arc in
# the one column of the fan that looks where you are going. A ``shell``
# roof is five cells wide but sits three above the walking surface --
# exactly the cell the body's head sweeps at the apex of a hop -- so
# ``write`` refuses it there and a tunnel over a jump is a roof with a
# hole in the middle of it. It survives whole over a ``walk``. The exit
# climb is a third of every run and was the emptiest part of the level at
# 64%; beams on all seven treads took it to 55%.
#
# Against THE SEA GATE below (prismarine, a six-block ledge on band 12,
# arch, cool blue-green) and WART FIELDS above (crimson nylium, lava,
# a fungus canopy) this is white timber-decked ground in the snow: a
# different enclosure, a different verb, and a hue that shares nothing
# with either.
LEVEL = Level("THE CORNICE", "snow", rise=6, gap=3.0, exit="stair",
              band=10.5, profile="plaza", shelf=4.5, breaks=3,
              landmark="bell",
              ground="snow", sub="packedice", rock="spruce",
              accent="frost", glow="lantern", liquid="water",
              props=("chain", "mcfence", "lanternpost", "pebbles"),
              step=("spruce", "hop"), beats=[
    # The threshold: one lantern set flush in the snow on a rise with the
    # meltwater dug out round it, then a stride onto the deck under the
    # first beam. The material changes completely at that block --
    # prismarine and sea light below, snow and timber here.
    #
    # ``ceiling`` goes on **every** node, and the earlier note here that a
    # lid three cells up is refused over any arc that climbs is wrong: the
    # check is on the *feet*, and one jump impulse lifts them 1.25 against
    # a lid at 3, so a +1 tread takes a beam as happily as a walk does.
    # What a walk buys is the *shell*, whose five-wide roof sits in the
    # cell the head sweeps at a hop's apex and is refused there.
    #
    # Three nodes and not two because the first two beats are the only
    # ones a level of this length reliably lays -- measured, ``sill`` and
    # ``notch`` were attempted on 8 runs of 8 and the fourth beat on one
    # -- so a landing written here is a landing the viewer sees and one
    # written at the tail of the script is not.
    ("sill", [n("glow", arc=3.4, lift=1, hug=3.0, spread=1,
                deco="lamp", moat=True, ceiling=5, shell="tunnel",
                orbs=1),
              n("spruce", arc=2.9, lift=1, hug=3.0, kind="walk",
                spread=0, ceiling=5, shell="tunnel", orbs=1),
              n("darkoak", arc=3.2, lift=2, hug=2.8, spread=0,
                ceiling=5, shell="tunnel")]),
    # The gallery: the timber snow-shed, and the second beat because a
    # second beat is still laid whole.
    #
    # It sits at **lift 1** and that is the whole of it. A shell grows
    # walls only where there is ground under them, so a shelled landing
    # a block up gets a roof on stilts and one on the deck gets a room;
    # and a beat's first node is placed from wherever the machinery
    # between beats left the body, which is lift 1 -- written at lift 2
    # this beat measured 86% placed as authored over sixteen runs and at
    # lift 1 it measures 100%.
    #
    # The shell goes on the landing whose *arrival* is roofed and the way
    # out of it is walked rather than jumped: a shell wraps the arc that
    # arrived and its roof then refuses the next one, and a doorway is
    # walked through in any case.
    ("gallery", [n("spruce", arc=3.2, lift=1, hug=3.0, spread=0,
                   ceiling=5),
                 n("darkoak", arc=2.9, lift=1, hug=3.0, kind="walk",
                   spread=0, shell="tunnel", ceiling=5, orbs=1)]),
    # The notch, and the level's descent -- in its first half, which is
    # where the reference puts one, and by falling off an edge rather
    # than jumping down, which is how the real map spends eleven blocks
    # of travel to gain four. Off the end of the deck onto the terrace
    # itself under a beam, and back up out of the meltwater on the wind-
    # polished ice.
    #
    # 4.4 m of arc is a reach of 3.72: a -1 fall against a window of
    # 2.35-4.98 and a -2 against 3.12-5.56, so it is legal whichever
    # height the beat before it left the body at. The two hops after it
    # are written at 3.2 and 4.2 rather than 3.6 and 3.6 because a +1
    # hop reaches 2.00-3.10 and a +1 *slide* 2.67-4.36 -- the first was
    # sitting at 2.92, hard against the top of its own window, and the
    # arc that has to fall back is the arc that is not exact.
    ("notch", [n("ground", arc=4.4, lift=0, form="floor", hug=3.0,
                 spread=0, ceiling=5, orbs=1),
               n("frost", arc=3.2, lift=1, hug=3.0, spread=1,
                 moat=True, ceiling=5, orbs=1),
               n("packedice", arc=4.2, lift=2, kind="slide", form="ice",
                 hug=3.2, spread=0, shell="cave", ceiling=5, orbs=1)]),
    # The showpiece, a little past halfway: the cornice itself. One frost
    # ledge under the lip and then the wind-polished ice on its very
    # edge, hung over the drop with nothing under it and a beam over the
    # jump. A slide reaches 6.00 m level where a hop reaches 4.26, so
    # this is the jump in the level that reads as long.
    ("cornice", [n("frost", arc=3.2, lift=2, hug=3.8, spread=0,
                   ceiling=5),
                 n("packedice", arc=4.0, lift=2, kind="slide",
                   form="ice", hug=4.0, spread=0, pedestal=False,
                   ceiling=5, shell="tunnel", orbs=1)]),
], filler=[
    # The level's voice, repeated for as long as the terrace lasts: the
    # covered deck, taken on foot under the beams and left on the ice.
    #
    # Every landing in it is level with the one before, and that is
    # deliberate rather than dull: a flat run is the one a ``shell`` can
    # roof the whole way, because a hop's apex puts the head in the cell
    # the roof wants and ``write`` refuses it there. The beams go on
    # everything regardless -- they are checked against the *feet* and a
    # climbing tread clears them. Half of every frame in this tower is sky
    # and this is the cheapest thing a level author can do about it.
    #
    # No moat in here -- a filler loops, and the second lap digs away the
    # ground the first lap's pedestals are standing on.
    ("deck", [n("spruce", arc=3.2, lift=1, hug=2.8, spread=1,
                ceiling=5, orbs=1),
              n("darkoak", arc=2.9, lift=1, hug=2.8, kind="walk",
                spread=0, ceiling=5, shell="tunnel"),
              n("frost", arc=3.6, lift=1, hug=3.2, spread=1, ceiling=5),
              n("packedice", arc=4.2, lift=1, kind="slide", form="ice",
                hug=3.2, spread=0, ceiling=5, orbs=1)]),
], exit_beats=[
    # The gallery's own ledges, cut into the cliff and lit at the foot
    # and the head. Authored rather than generated because the climb out
    # is the single biggest consumer of a level -- twenty-seven of this
    # one's eighty-eight landings before this pass -- and a generated
    # staircase of the cone's own stone says nothing about the place.
    #
    # A stair and deliberately not a ladder: the tower already leaves
    # seventeen of twenty rebuilt levels by a climb against the real
    # map's seven of forty-three, and this level's idea is the shelf,
    # not the shaft.
    #
    # **Seven treads, every one roofed and beamed.** The climb is a third
    # of every run and was the emptiest part of this level by a wide
    # margin -- 64% of the view against the level's own 54% -- because a
    # body walking up a staircase against the cliff is looking at the
    # chasm, the next terrace and the sky over it, and the slab that roofs
    # this corridor is seven to thirteen blocks up, past anything the ray
    # fan can reach. Beams took it to 55%. The seventh tread is there
    # because six left the body a block short about half the time and the
    # fallback staircase that answered that was three unroofed landings.
    n("spruce", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      shell="tunnel", ceiling=5, deco="lamp"),
    n("darkoak", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
      shell="tunnel", ceiling=5),
    # Two of the six treads are wind-polished ice, taken as slides, and
    # they are the reason this level is not 91% plain hop: the climb out
    # is a third of every run and can otherwise only ever be hops. A
    # slide gaining a block reaches 2.67-4.36 m against a hop's
    # 2.00-3.10, so an icy tread is written a little longer than a
    # timber one.
    n("packedice", arc=3.6, step_y=1, kind="slide", form="ice",
      hug=2.4, spread=0, radial=-0.9, shell="tunnel", ceiling=5,
      orbs=1),
    n("darkoak", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
      shell="tunnel", ceiling=5),
    n("packedice", arc=3.6, step_y=1, kind="slide", form="ice",
      hug=2.4, spread=0, radial=-0.9, shell="tunnel", ceiling=5,
      orbs=1),
    n("darkoak", arc=3.0, step_y=1, hug=2.6, spread=0, deco="lamp",
      shell="tunnel", ceiling=5),
    n("spruce", arc=3.0, step_y=1, hug=2.6, spread=0, shell="tunnel",
      ceiling=5),
])
