"""Level 22: THE PILLARS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A drowned colonnade. Out of the basalt slot into a wide pale court:
# obsidian pillars standing in black water, purpur architraves slung
# between them a half block at a time, sea lanterns set flush in the
# endstone, and the obsidian gate the course runs straight through. The
# way out is up the water column inside the last pillar.
#
# The seam is the point of the palette. Level 21 is a red vent field
# nine blocks wide with a rock lid over most of it and a staircase out;
# this is cream endstone and lilac purpur at twelve, open overhead
# except where an architrave crosses, left by a water column -- and the
# light goes from orange shroomlight to pale sea lantern at the first
# block of it. Band, profile, enclosure, colour, light and exit: six of
# the seven things consecutive levels are meant to differ on.
#
# Four decisions, each of them a number this level was failing.
#
# **Nothing floats any more.** The level this replaces hung every
# landing at ``hug`` 5.6 to 9.6 with ``pedestal=False`` -- seventy-five
# per cent of its landings were cubes in an empty sky, and fifty-seven
# per cent of the view was sky, sea or drop. The landings are the tops
# of pillars and the beams between them now, standing on the court, and
# the court is under the lens.
#
# **The water is what stops the walker.** This level measured 58%
# covered without a jump against a 55% limit, on a flat unbroken plate.
# The End has no liquid of its own, so this one is skinned water, and it
# is not decoration: water is see-through, so a moat is a *pit* the
# walker falls into and cannot climb out of, which is the one lever in
# the vocabulary that reliably moves that number. Two of them, ten
# metres apart -- a moat digs a radius-three disc the moment its landing
# commits, and a second one inside that radius stands in the hole the
# first dug. Two took the walker from 58% to 7%; a third bought nothing
# and a level with no walkable metre in it is as wrong as one you can
# stroll.
#
# **The bubble stays, because the climb is what this level is about.**
# The rule is a climb exit on about one level in five and this tower
# overshot it badly, so the question for every one of them is whether
# the level's idea is the climb -- and going up *inside* one of the
# pillars on a level called THE PILLARS is exactly that. It is also what
# lets the level stay low: a level whose course sits at lift 1 has six
# blocks to find at the end, which is a six-step staircase and half the
# terrace, and a water column does it in one landing. It is authored
# with its pedestal and a five-block ``step_y`` because a column that
# cannot find solid rock beside it at its middle cell and its top is
# refused silently and becomes that staircase with nothing reporting it
# -- **check the move mix in ``--report`` for the word ``bubble``**.
#
# **The architrave is a head-hitter you walk under.** ``ceiling=3`` over
# a ``kind="walk"`` leg is the genre's 2bc, and the only form of it this
# motion model can express: a jump always rises 1.25 m and sweeps the
# two cells over its own take-off, so a lid low enough to read as a beam
# refuses every arc under it. A walk has no arc.
#
# **The frame pass (2026-08-13).** The rule went to *under 48%* empty, and
# this level read 44% mean over eight seeds with three of those seeds at
# 48. Measured with a 25-ray fan bucketed by direction, the emptiness was
# almost all *overhead* -- the two up rows were 47-66% empty against the
# two down rows' 13-48% -- and outboard, the drop side of the fan being
# the worst column at every pitch. Three things moved it to **41% mean,
# 48 worst**, and one thing that should have did not:
#
# * **``shelf`` 5.0 -> 5.5.** Ground outboard of the body is what the
#   down rows hit; a metre of it was worth more than every lid here.
#   5.5 and not 6.5: at 6.5 the frame is a point better again and one
#   walk of twenty-three covers 58% of the level, over the 55% ceiling.
#   At 5.5 the walker reads *better* than before the pass (mean 10% ->
#   8%, worst 46% -> 33%).
# * **A ``cave`` on the exit launch.** The ascent is a third of the run
#   and the emptiest third of most levels; here it was already the
#   fullest beat (30%) because the bubble rides inside a ``shaft``, and
#   roofing the landing it launches from took the whole level another
#   point and the jammed lens *down* (10.7% -> 8.9%).
# * **The architrave dropped a block** (lift 2/3/3 -> 1/2/2). It gains
#   nothing structurally -- the exit beat opens at lift 1 regardless --
#   and a beat that opens at lift 1 is the documented fidelity lever.
# * **Lids are not a frame lever.** ``ceiling=3`` on both filler landings
#   moved the number by one tenth of a point. It is one cell wide and
#   answers the centre column of the fan only; the shells are what carry
#   this. Keep them for the head-hitter they are, not for the sky.
LEVEL = Level("THE PILLARS", "end", rise=7, gap=3.4, exit="bubble",
              band=12.0, shelf=5.5, breaks=3, landmark="hoodoo",
              ground="endstone", sub="purpur", rock="obsidian",
              accent="chorus", glow="sealantern", liquid="water",
              props=("chorus", "endrod", "pebbles", "lanternpost"),
              step=("purpur", "hop"), beats=[
    # The threshold: a sea lantern flush in the endstone with the water
    # cut round it, then the walked step in between the first two
    # pillars, under their architrave. Everything about the frame
    # changes here -- colour, width, light, lid -- in one block. The
    # ``tunnel`` makes the architrave a thing you walk *through* rather
    # than a beam near your head; its walls find no footing over the
    # moat's pit, so what it really contributes is the roof.
    ("threshold", [n("glow", arc=3.4, lift=1, hug=3.6, spread=0,
                     deco="lamp", moat=True, orbs=1),
                   n("rock", arc=2.8, lift=1, hug=3.6, kind="walk",
                     spread=0, ceiling=3, deco="post",
                     shell="tunnel")]),
    # The colonnade: up the beams a half block at a time. A slab landing
    # is the reference's commonest non-cube form by a wide margin, it
    # reads as deliberate architecture rather than as a fudge, and it
    # buys reach -- two slab steps gain a block across seven metres of
    # ground where one hop could only manage 3.10.
    #
    # Then off the end of the run of beams, two blocks down into the
    # tarn. The fall is in the same beat as the climb: written across a
    # beat boundary it falls off nothing about half the time, because
    # machinery arrives at its own height between beats.
    ("colonnade", [n("sub", arc=3.6, lift=1, form="slab", hug=3.6,
                     spread=0),
                   n("rock", arc=2.8, lift=1, form="slab", hug=3.6,
                     kind="walk", spread=0, ceiling=3),
                   n("accent", arc=3.4, lift=2, form="slab", hug=3.6,
                     spread=0, orbs=1),
                   n("ground", arc=4.6, lift=0, form="floor", spread=0,
                     orbs=2)]),
    # The tarn: the court has flooded between the pillars and the way
    # across is the stone that fell off them. One landing floats -- a
    # single block standing in the water with nothing under it -- and
    # only the last one digs a pool of its own, ten metres from the one
    # in the threshold. A moat is a radius-three disc dug the moment its
    # landing commits, and a second one inside that radius stands in the
    # hole the first dug.
    ("tarn", [n("sub", arc=3.5, lift=1, hug=4.4, spread=0),
              n("accent", arc=4.0, lift=1, hug=4.4, spread=0,
                pedestal=False, orbs=1),
              n("sub", arc=2.8, lift=1, hug=4.4, kind="walk", spread=0),
              n("sub", arc=3.9, lift=1, hug=4.4, spread=0, moat=True,
                orbs=1)]),
    # Back up on to the architraves, in against the pillars. A block
    # lower than it was written: the exit beat opens at lift 1 whatever
    # this beat reaches, so the height bought nothing and a beat opening
    # at lift 2 is asking machinery for a rise it may not have. The shell
    # goes on the beat's *last* node -- a shell is painted the moment its
    # landing commits and its roof then refuses the next arc out of it.
    ("architrave", [n("rock", arc=3.4, lift=1, hug=3.4, spread=0,
                      ceiling=3),
                    n("sub", arc=3.4, lift=2, form="slab", hug=3.4,
                      spread=0, orbs=1),
                    n("accent", arc=3.4, lift=2, hug=3.4, spread=0,
                      shell="tunnel")]),
], filler=[
    # The court, for as long as it lasts: a fall back down to the
    # flooded floor, a wade across a submerged sill, and a chorus stone
    # standing in the water. Flat, low and near the ground on purpose --
    # this is the beat that repeats, so it is the one that decides how
    # much of the frame is sky.
    #
    # No moat in it. The filler loops and the second lap digs away the
    # ground the first lap is standing on. Every node carries some
    # ``spread`` because the first lap is entered from wherever the lock
    # or the gate crossing left the body.
    #
    # The two lids are honest head-hitters and nothing more: measured on
    # eight seeds they moved empty frame by a tenth of a point, because
    # ``ceiling=n`` is one cell wide and answers the centre column of the
    # ray fan alone. What roofs a frame is a shell.
    ("court", [n("ground", arc=4.4, lift=1, hug=4.2, spread=1, orbs=1),
               n("sub", arc=2.8, lift=1, hug=4.2, kind="walk", spread=1,
                 ceiling=3),
               n("accent", arc=3.6, lift=1, hug=4.2, spread=1, orbs=1,
                 ceiling=3)]),
], exit_beats=[
    # Out up the water column inside the last pillar. Declared as the
    # level's exit as well, so the reserve is a climb's three landings
    # rather than a staircase's seven.
    #
    # It keeps its **pedestal** and asks for no ``hug``, and that is the
    # whole difference between a bubble column and a silent staircase:
    # the column has to find solid rock within a cell of itself at its
    # middle index and at its top, and hugged to a core that leans away
    # there is nothing there. Standing the landing on its own stack
    # gives the column something to hang on for its whole height.
    #
    # The launch carries a ``cave`` for the frame rather than for the
    # climb: the ride already sits inside the ``shaft``, which is why
    # this level's ascent measures 30% empty where its neighbour's bare
    # vine measured 46, and roofing the landing it leaves from closes the
    # seconds either side of it.
    n("rock", arc=3.2, lift=1, hug=2.6, spread=2, deco="lamp",
      shell="cave"),
    n("sub", arc=3.0, step_y=5, kind="bubble", spread=0, shell="shaft",
      orbs=2),
])
