"""Level 23: SPORE HOLLOW.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE HOLLOW. The mycelium crust has fallen in, and what is left is a
# bowl with black water standing in the bottom of it, one enormous red
# cap roofing the whole thing, and shelf fungus bracketed out of the
# cliff to get across on.
#
# The old version was a full lilac *plaza* with a forest of identical
# pale stems standing on it: 58% of it walkable, 100% plain hop, half
# the frame sky, and nothing anywhere near the lens. Four things answer
# that and they are all geometry rather than decoration -- the terrace
# is a four-block ledge with the drop outboard, the crust gives way in
# the second beat and drops the body two blocks into the pool, the cap
# and two checked lids put rock over the body's head, and **every
# landing in the level is hugged in to 2.4-3.2** so the core wall is a
# couple of metres off the shoulder for the whole run. That last is the
# reference's own shape -- a wall within 4 m on one side 71% of the
# time, a lid overhead on 98% of samples -- and it is what a "hollow"
# has to be to read as one.
#
# The hugs are also load-bearing rather than decorative, and this cost
# a pass to learn: on a ``ledge`` an unhugged landing is pulled to the
# *middle of the band*, which on a four-block shelf inside a ten-block
# band is out over the drop with no ground under it. The first draft
# left the cap shelves and the whole filler unhugged and they came out
# at 67% and 0% placed, with one unchecked emergency landing behind
# them. Everything here carries a ``hug``.
#
# The showpiece is the second beat, because on a terrace this length a
# beat written fourth is a beat nobody sees. Two steps up the stem, a
# two-block fall onto the bracket of slime standing in the water, and
# the throw two blocks back out onto the gills -- the only move in this
# engine that gains two, and the reference's one rationed gadget (one
# 2x2 pad a level, 26 levels of 43). The rise and the fall have to be
# *inside* one beat: written across a boundary the machinery in between
# puts the body back on the terrace, the fall becomes a one-block drop,
# and a one-block drop is refused as a +2 bounce on every candidate.
#
# The way out is the vine up the great stem, and here the climb really
# is the level's idea: a bowl has no stair out of it. It is authored
# rather than left to the generated climb, which measured 1 anchored
# column in 1,559 candidates and silently becomes an eight-step
# staircase -- **check the move mix in ``--report`` for the word
# ``climb``**; if it is missing, this is a staircase.
#
# Jumps are written at 3.0-3.6 m, the real map's own modal jump. The
# long ones are the fall into the pool and the leap onto the brackets,
# and a descent cannot also be short: the arc covers three or four
# metres of ground before it arrives.
LEVEL = Level("SPORE HOLLOW", "mushroom", rise=5, gap=3.0, exit="vine",
              band=10.0, shelf=4.5, profile="ledge", breaks=2,
              landmark="greatcap",
              # Violet ground, bone-white stem, one red roof and the
              # shroomlight doing the only job light does here. The
              # ground is skinned as well as the built blocks: it is a
              # third of every frame and it was the cone's own grey.
              ground="mycelium", sub="podzol", rock="mushroomstem",
              accent="mushroomred", glow="shroomlight", liquid="water",
              candy=("mushroomred", "mushroomstem"),
              props=("mushroomcap", "vinehang", "grasstuft", "flower"),
              sky=(158, 136, 176), dark=0.25,
              step=("mushroomstem", "hop"), beats=[
    # The threshold: one shroomlight flush in the crust on a rise, then
    # a stride along the spore path under a checked lid. The palette
    # changes completely at that block -- obsidian and purpur out at the
    # rim below, violet and red here. A lintel is walked under and never
    # jumped under: one impulse always rises 1.25 m, so the head sweeps
    # the three cells over every take-off and an arc under a low lid is
    # refused. Over a ``walk`` there is no arc at all, which is what
    # makes ``ceiling=3`` an honest head-hitter rather than a wall.
    ("crust", [n("glow", arc=3.0, lift=1, hug=2.6, spread=0, deco="lamp",
                 orbs=1),
               n("coarse", arc=2.9, lift=1, hug=2.6, kind="walk", spread=0,
                 ceiling=3)]),
    # The crust gives way. Two steps up the stem, the two-block fall
    # into the pool onto the slime bracket, and the throw back up onto
    # the gills. The pad carries no pedestal: with one it is only
    # offered cells with ground under them, and at the bottom of a hole
    # there are none. It also sits half a metre further out than the
    # rest, which is what makes the fall read as a fall into something.
    ("sinkhole", [n("rock", arc=3.3, lift=2, hug=2.8, spread=0),
                  n("accent", arc=3.2, lift=3, hug=2.8, spread=0),
                  n("slime", arc=5.0, lift=1, hug=3.2, form="slime",
                    spread=0, pedestal=False, moat=True, orbs=1),
                  n("accent", arc=3.6, lift=3, hug=2.8, kind="bounce",
                    spread=1, orbs=3)]),
    # The brackets: shelf fungus half a block proud of the cliff, the
    # first of them standing over its own pool, and a grotto cut into
    # the wall at the end of it. The shell goes on the beat's *last*
    # node -- a shell is painted the moment its landing commits and its
    # roof then refuses the next arc out of it.
    #
    # This is the *third* beat and the gills are the fourth, which is
    # the other way round from the first draft and is worth the note.
    # A terrace this length lays two beats whole and truncates the
    # third, so whichever beat is third gets its first node and nothing
    # else -- and this beat's first node is the pool, which is a thing,
    # where the gills' first node is a ledge like any other.
    ("brackets", [n("rock", arc=4.4, lift=3, hug=2.8, form="slab",
                    spread=0, moat=True),
                  n("podzol", arc=2.9, lift=3, hug=2.8, form="slab",
                    kind="walk", spread=0, ceiling=3),
                  n("accent", arc=3.2, lift=3, hug=2.6, spread=0,
                    shell="grotto", orbs=1)]),
    # The gills: three tiers of the cap's underside, stepping up against
    # the stem. A half-height landing is the reference's commonest
    # non-cube form by a wide margin and it buys reach as well as looks.
    ("gills", [n("accent", arc=4.0, lift=3, hug=2.6, form="slab",
                 spread=0, orbs=1),
               n("rock", arc=3.2, lift=3, hug=2.4, spread=0),
               n("accent", arc=3.3, lift=4, hug=2.6, spread=0, orbs=1)]),
], filler=[
    # The level's voice, and on a terrace this long it is most of the
    # level: a cap, a stem, a stride down the spore path under a lid,
    # and a step up onto the next tier of gills. It climbs a block each
    # lap and drops one at the seam where it loops, which is why its
    # first landing is written long enough to be a legal descent as well
    # as a legal flat hop.
    #
    # **No moat in here.** The filler loops, and the second lap digs
    # away the ground the first lap's pedestals are standing on.
    ("spores", [n("accent", arc=3.4, lift=3, hug=2.6, spread=0, orbs=1),
                n("coarse", arc=2.9, lift=3, hug=2.6, kind="walk",
                  spread=0, ceiling=3),
                n("rock", arc=3.5, lift=3, hug=2.4, spread=0),
                n("mushroomred", arc=3.3, lift=4, hug=2.6, spread=0,
                  orbs=1)]),
], exit_beats=[
    # Down off the gills to the foot of the great stem, then out up the
    # vine. Written rather than generated, and the lines that decide
    # whether it is a vine or a silent staircase are the *pedestal*, the
    # shaft and the height: a climb wants solid rock within one cell of
    # its column at the column's middle index and at its top, and a
    # column hugged to a cliff that leans away has nothing to hang on.
    # Standing the landing on its own stack, inside a shaft that
    # supplies the wall, and asking for four blocks so the middle index
    # lands on the landing rather than on the stack below, gives it
    # something for the whole ride.
    #
    # The launch is written at ``lift=2`` and ``spread=1``, which is the
    # arithmetic of the ride and not a taste: the launch surface is
    # three above the terrace, four blocks of vine tops out at seven,
    # the next level's floor is at six, and the crossing comes down one
    # block onto it. Two of spread would let the launch settle at lift
    # four, and then the crossing is a three-block drop over the chasm,
    # which is 3.66 m against a minimum of 3.72 and is refused.
    n("rock", arc=4.2, lift=2, hug=2.2, spread=1, deco="lamp"),
    n("mushroomstem", arc=2.6, step_y=4, kind="climb", climb_style="vine",
      spread=0, orbs=2),
])
