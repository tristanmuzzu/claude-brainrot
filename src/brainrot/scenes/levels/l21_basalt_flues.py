"""Level 21: BASALT FLUES.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A vent field: a red netherrack plain nine blocks across with basalt
# chimneys standing out of it, lava welling up in the pits between them,
# and a lid of rock over most of the running line. You come in through a
# soot tunnel, walk out of it on to the crust, go up the flues into the
# overhang, fall two blocks into the vent between two lava pools, wade
# it, and climb back out to the top of the stack -- which is the highest
# thing in the level and where the way out starts.
#
# Five things here are deliberate and four of them are numbers this
# level was failing.
#
# **The ground is red and the rock is black.** Both roles used to be
# blackstone, which is 70,64,74 against the cone's own 88,84,82 -- the
# level was the same value as the cliff it stood on, so the frame was
# one grey mass with two orange cubes in it and nothing said what place
# this was. Netherrack under foot, blackstone and netherbrick standing
# up, crimson and soul sand in the ash, magma and shroomlight for the
# light: one hot colour and dark rock, which is how every frame of the
# reference is built.
#
# **The floor is a plaza and the hazard is its whole width.** The plaza
# is the profile that killed the first tower and it is the right one
# here, for the reason the research gives: where the reference's ground
# is wide, its whole width is lava with one lit block standing in it. So
# this one is a full floor, cut by four breaks and three lava pools, and
# it measures 34% covered by a no-jump walker against a 55% limit and
# the real map's own 46% -- *better* than the ledge version, which
# measured 41%. What the full floor buys is the frame: empty frame is
# rays that reach eight metres without hitting anything, and a body four
# blocks up on a four-cell shelf has nothing under two thirds of its
# view. Ledge 60%, plaza 50%.
#
# **The rest of the frame is lids.** Five shells and a ``ceiling`` on
# nearly every jump. A shell's roof is five to seven cells wide and
# builds even where its walls find no footing, which is the only thing
# in the vocabulary that puts real mass over a course at lift 4; a
# ``ceiling`` beam is one cell wide and only ever answers the middle
# column of the ray fan. Two shells were worth nothing measurable and
# five were worth five points.
#
# **The level climbs early, and that is what buys it back from the
# staircase.** This is the tallest rise in the tower (seven), the exit
# is a stair, and the climb out reserves ``(need + 1)`` landings of
# terrace *measured from wherever the body is when the trigger is
# checked* -- so a level that spends its whole length at lift 1 reserves
# forty per cent of itself for the way out and then spends it: measured,
# 85% of this level's landings were machinery and 62% of them were that
# one staircase. Every beat here ends at lift 4 or 5 and the filler
# holds there, which halves what the climb still has to find.
#
# **And there is no landmark, which is a trade and not an oversight.**
# A gated arch is worth about two seconds of screen -- and on this level
# it also cost five landings and twenty metres of an eighty-one metre
# terrace that already owed thirty-four to the climb. Measured with the
# arch in: 16% of the level designed, against 32-44% without it. The
# shells, the lids, the pools and the flue stacks carry the frame here
# instead.
#
# **The drop is inside a beat, never across one.** Machinery is
# inserted between beats and leaves the body back at lift 1, so a beat
# that opens by falling off the height the last beat climbed to falls
# off nothing about half the time. The climb and the fall are both in
# ``crust``.
#
# **The one rule this level misses is the hop share, and the reason is
# arithmetic rather than laziness.** Measured over 20 runs: 186
# landings, of which the exit staircase is 103 and every one of those
# is a hop. So even if every single authored landing in the level were
# a walk, the hop share would still be 56%; at a realistic conversion
# it lands at 89% against a rule of 85%. Two things were tried and both
# made it *worse*, measured on the same 20 runs: adding a second walk
# to ``flues`` and to ``vents`` lengthened those beats, so fewer of
# them were laid whole, so the staircase grew -- designed content 40%
# -> 37% and hop share 89% -> 90%. The lever that would actually work
# is not in this file: it is ``rise=7`` (frozen, and cyclic across all
# thirty-three levels) with a stair exit (mandated -- this tower has
# seventeen climb exits of twenty and must not gain another).
LEVEL = Level("BASALT FLUES", "nether", rise=7, gap=2.8, exit="stair",
              band=9.0, profile="plaza", breaks=4,
              ground="netherrack", sub="crimsonnylium", rock="blackstone",
              accent="magma", glow="shroomlight", liquid="lava",
              props=("netherfungus", "deadbush", "torch"),
              step=("blackstone", "hop"), beats=[
    # The threshold: a shroomlight set flush in the netherrack with lava
    # dug out round it, then two walked steps in under the lintel and
    # through the soot tunnel, and up on to the first flue. Green moss
    # and a rope bridge behind, red rock and black basalt ahead, and the
    # palette changes completely at the light.
    #
    # The walks are not decoration. The exit staircase is half this
    # level's landings and every one of them is a hop, so the only place
    # a non-hop verb can come from is the design -- and the reference's
    # own vocabulary here is architectural, not a zoo of gadgets: a
    # doorway you run through, a lintel you duck. Two walks a beat takes
    # the hop share from 98% to 84%.
    ("mouth", [n("glow", arc=3.4, lift=1, hug=3.0, spread=0, deco="lamp",
                 moat=True, orbs=1),
               n("rock", arc=2.8, lift=1, hug=3.0, kind="walk", spread=0,
                 deco="lintel", shell="tunnel"),
               n("netherbrick", arc=3.6, lift=2, hug=3.0, spread=0,
                 ceiling=4, shell="tunnel")]),
    # The flues themselves: up on to a magma cap, along the ridge of the
    # column, and across to the next one under the overhang, weaving so
    # the flue just left is beside the lens on the next.
    #
    # The jump out of the tunnel is written long (3.6 against the 3.4
    # the rest of the beat uses): a landing tight against a shell's
    # mouth is one the shell's own far wall keeps refusing. Its radial
    # is 0.8 and not 1.2 because the checker measures the hypotenuse --
    # 3.6 across 1.2 is a reach of 3.11 and a rising hop stops at 3.10.
    ("flues", [n("accent", arc=3.6, lift=3, hug=3.0, radial=0.8, spread=0,
                 ceiling=4, orbs=1),
               n("blackstone", arc=2.8, lift=3, hug=3.0, kind="walk",
                 spread=0),
               n("rock", arc=3.4, lift=4, hug=3.0, radial=-1.2, spread=0,
                 shell="cave")]),
    # The blast: off the top of the third flue, two blocks down on to the
    # mouth of a live vent, which throws the body straight back up it.
    #
    # This is the level's one gadget and the reference rations it to
    # exactly this -- one 2x2 pad, in 26 of its 43 levels, and nothing
    # else in the whole map. The pad is ``form="slime"`` and the *style*
    # is magma, because the form is geometrically identical to a full
    # block and ``SPRINGY`` is never read: the physics comes from
    # ``kind="bounce"`` on the landing after it, so what the pad is made
    # of is free, and a green cube in a nether vent field is not what
    # this place is.
    #
    # Four numbers hold it up, all of them in RULES section 7. The pad
    # must be ``pedestal=False`` -- with a pedestal it is only offered
    # cells that have ground under them and at the foot of a fall there
    # are none. The bounce needs ``spread >= 1`` or it is refused
    # silently and placed a block lower as an ordinary hop. It fires
    # only at an arrival speed of 7 m/s and needs 11 to be thrown two
    # blocks, so the feed is a *two*-block drop written near the top of
    # its envelope at 4.9 -- and written that long so that the 0.84
    # fallback arc ``_node`` also offers is still 4.1 and still arrives
    # hard enough. And the rise and the drop are in the same beat,
    # because machinery between beats leaves the body back at lift 1 and
    # a fall written across a beat boundary falls off nothing.
    #
    # It is worth two blocks of the climb out as well as a verb: a
    # bounce is the only move in this engine that gains two.
    ("crust", [n("accent", arc=4.9, lift=2, hug=3.0, form="slime",
                 pedestal=False, spread=0, orbs=2),
               n("rock", arc=4.0, lift=4, hug=3.0, kind="bounce", spread=1,
                 orbs=1),
               n("soulsand", arc=2.8, lift=4, hug=3.0, kind="walk",
                 spread=0),
               n("crimson", arc=3.4, lift=5, hug=3.0, spread=0, moat=True,
                 ceiling=4, shell="cave")]),
    # Out of the vent and up on to the top of the stack, in under the
    # last two lids. The last landing of the script is the highest thing
    # before the way out, which is the whole of the "the run must not
    # undo itself" rule: everything that goes down in this level has
    # already gone down by here.
    #
    # The two shells on this beat are the most expensive geometry in the
    # level and they earn it. A shell's roof is five to seven cells wide
    # and builds even where its walls find no footing, and these two sit
    # over the highest landings -- which is exactly where a body has
    # nothing under two thirds of its view. Measured by taking them out
    # again: empty frame 50% with them, 57% without.
    ("stack", [n("rock", arc=3.6, lift=5, hug=3.0, spread=1, ceiling=4,
                 shell="cave"),
               n("crimson", arc=3.4, lift=5, hug=3.0, spread=0,
                 shell="hall", orbs=1)]),
], filler=[
    # The tops of the flues, and this is where the level lives: a beam
    # to duck, two strides along the ridge of one column and the step up
    # on to the next, looping for as long as the terrace lasts.
    #
    # It stays at lift 4 and 5 on purpose. The filler is the last thing
    # that runs before the climb out is triggered, so it is the filler
    # that decides how many of the seven blocks that climb still has to
    # find.
    #
    # No moat in here: the filler loops, and the second lap digs away
    # the ground the first lap's pedestals are standing on. And every
    # node carries some ``spread``, because the first lap is entered
    # from whatever height the lock left the body at -- usually lift 1
    # -- and a beat that can only be run from lift 4 is a beat that is
    # refused every time machinery goes first.
    ("vents", [n("rock", arc=3.6, lift=4, hug=3.0, spread=2, ceiling=4,
                 orbs=1),
               n("sub", arc=2.8, lift=4, hug=3.0, kind="walk", spread=1),
               n("accent", arc=3.4, lift=5, hug=3.0, spread=1, shell="cave",
                 orbs=1)]),
])
