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
# The place: a shelf pinned under an overhanging snow lip, decked in
# timber, with meltwater cut through the deck, a lit gallery roofed
# against the cornice, and the crane standing where the ledge turns.
# It falls into the notch a third of the way along and climbs from there
# to the gallery's own ledges, which are the highest thing in it.
#
# **``breaks=1``, and the number is a trade rather than a default.** Any
# break at all forces the lock -- a level's first floor break is always
# too wide to jump and the machinery that crosses it costs one to three
# of the nine or ten landings a level gets -- and on a level that also
# holds a gate the two inserted features share ground and the script is
# clipped between them. Measured over sixteen runs, everything else
# identical:
#
# | breaks | placed as authored | designed content | frame empty |
# |---|---|---|---|
# | 0 | **100%, every beat** | **50%** | 58% |
# | 1 | 98% (``notch`` 88%) | 34% | **53%** |
# | 2 | 97% (``notch`` 93%) | 39% | 54% |
#
# The breaks are *not* here for the walker -- the meltwater pits and a
# shelf with the drop straight outboard hold a no-jump walk to 13% of
# the level with none at all, against a limit of 55. They are here for
# the **frame**, and that was not the expected result: the lock builds an
# approach stack and an island out over its hole, and those blocks stand
# in the corridor ahead of the body where the open shelf has nothing.
# Half of every frame in this tower being sky is the complaint this pass
# exists to answer, so one break is worth two points of fidelity on one
# beat -- and that beat's loss is its ``form="floor"`` landing, which by
# construction cannot be placed where the floor has a hole in it.
#
# Against THE SEA GATE below (a broad pale prismarine plaza, band 12,
# arch, cool blue-green) and WART FIELDS above (crimson nylium, lava,
# a fungus canopy) this is a narrow timber gallery in the snow: band
# 8.5, a different enclosure, a different verb, and a hue that shares
# nothing with either.
LEVEL = Level("THE CORNICE", "snow", rise=5, gap=3.0, exit="stair",
              band=8.5, shelf=4.5, breaks=1, landmark="crane",
              ground="snow", sub="packedice", rock="spruce",
              accent="frost", glow="lantern", liquid="water",
              props=("chain", "mcfence", "lanternpost", "pebbles"),
              step=("spruce", "hop"), beats=[
    # The threshold: one lantern set flush in the snow on a rise with the
    # meltwater dug out round it, then a stride onto the deck under the
    # first beam. The material changes completely at that block --
    # prismarine and sea light below, snow and timber here.
    #
    # ``ceiling`` goes on the *walk*: a lid three cells up is refused
    # over any arc that climbs, and a walk has no arc at all, which is
    # the one place in this engine the genre's head-hitter is honest.
    #
    # Three nodes and not two because the first two beats are the only
    # ones a level of this length reliably lays -- measured, ``sill`` and
    # ``notch`` were attempted on 8 runs of 8 and the fourth beat on one
    # -- so a landing written here is a landing the viewer sees and one
    # written at the tail of the script is not.
    ("sill", [n("glow", arc=3.4, lift=1, hug=3.0, spread=1,
                deco="lamp", moat=True, ceiling=3, orbs=1),
              n("spruce", arc=2.9, lift=1, hug=3.0, kind="walk",
                spread=0, ceiling=5, orbs=1),
              n("darkoak", arc=3.2, lift=2, hug=2.8, spread=0)]),
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
                   ceiling=3),
                 n("darkoak", arc=2.9, lift=1, hug=3.0, kind="walk",
                   spread=0, shell="tunnel", orbs=1)]),
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
                 moat=True, orbs=1),
               n("packedice", arc=4.2, lift=2, kind="slide", form="ice",
                 hug=3.2, spread=0, shell="cave", orbs=1)]),
    # The showpiece, a little past halfway: the cornice itself. One frost
    # ledge under the lip and then the wind-polished ice on its very
    # edge, hung over the drop with nothing under it and a beam over the
    # jump. A slide reaches 6.00 m level where a hop reaches 4.26, so
    # this is the jump in the level that reads as long.
    ("cornice", [n("frost", arc=3.2, lift=2, hug=3.8, spread=0),
                 n("packedice", arc=4.0, lift=2, kind="slide",
                   form="ice", hug=4.0, spread=0, pedestal=False,
                   ceiling=3, orbs=1)]),
], filler=[
    # The level's voice, repeated for as long as the terrace lasts: the
    # covered deck, taken on foot under the beams and left on the ice.
    #
    # Every landing in it is level with the one before, and that is
    # deliberate rather than dull: a lid three cells up is refused over
    # any arc that *climbs*, because one impulse always lifts the head
    # through them, so a flat run is the only run that can be roofed the
    # whole way. Half of every frame in this tower is sky and this is the
    # cheapest thing a level author can do about it.
    #
    # No moat in here -- a filler loops, and the second lap digs away the
    # ground the first lap's pedestals are standing on.
    ("deck", [n("spruce", arc=3.2, lift=1, hug=2.8, spread=1,
                ceiling=3, orbs=1),
              n("darkoak", arc=2.9, lift=1, hug=2.8, kind="walk",
                spread=0, ceiling=5),
              n("frost", arc=3.6, lift=1, hug=3.2, spread=1, ceiling=3),
              n("packedice", arc=4.2, lift=1, kind="slide", form="ice",
                hug=3.2, spread=0, ceiling=3, orbs=1)]),
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
    n("spruce", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      shell="tunnel", deco="lamp"),
    n("darkoak", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
      shell="tunnel"),
    # Two of the six treads are wind-polished ice, taken as slides, and
    # they are the reason this level is not 91% plain hop: the climb out
    # is a third of every run and can otherwise only ever be hops. A
    # slide gaining a block reaches 2.67-4.36 m against a hop's
    # 2.00-3.10, so an icy tread is written a little longer than a
    # timber one.
    n("packedice", arc=3.6, step_y=1, kind="slide", form="ice",
      hug=2.4, spread=0, radial=-0.9, orbs=1),
    n("darkoak", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
      shell="tunnel"),
    n("packedice", arc=3.6, step_y=1, kind="slide", form="ice",
      hug=2.4, spread=0, radial=-0.9, orbs=1),
    n("darkoak", arc=3.0, step_y=1, hug=2.6, spread=0, deco="lamp"),
])
