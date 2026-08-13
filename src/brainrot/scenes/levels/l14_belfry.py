"""Level 14: THE BELFRY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The bell tower. A red-tiled street with a lantern standing in the
# village water and the bell frame across it, oak slab treads up the
# tower's flank, a well under the eaves with a pad at the bottom of it
# -- and then the way out is the shaft itself: a ladder up the inside
# of the tower, walled by its own ``shell="shaft"``, with the doorway
# out at the top.
#
# What it is answering. This is the tower's *vertical* level -- eight
# blocks, the biggest rise of the thirty-three -- and it measured 25%
# designed and 94% plain hop, which means its verticality was all
# generated exit staircase and none of it was written down. Two
# measured facts about this engine decided how to fix that:
#
# * **A level is seven to twelve landings and only two to five of them
#   are the design's.** Everything past the fifth authored landing is
#   written and never seen. So the identity lives in the first two
#   beats and in the filler, which repeats; the well and its slime pad
#   are in the filler for the same reason.
# * **The exit climb is the one feature that happens in every run.** So
#   the ladder is written as ``exit_beats`` rather than as a beat --
#   the climb *is* the level, which is what the reference does with
#   every one of its big interiors -- and it comes with its own shaft
#   round it and a lamp at its foot.
#
# ``breaks=0`` on purpose: any break at all forces the lock across it,
# which costs a landing and a half of a seven-landing level, and this
# level does not need it -- the shelf is four cells with the drop
# outboard, the trough and the well cut liquid through it, and a walker
# gets a fifth of the way along.
LEVEL = Level("THE BELFRY", "village", rise=8, gap=3.0, exit="ladder",
              band=9.5, shelf=4.0, profile="ledge", breaks=0,
              landmark="bell",
              ground="terracotta", sub="brick", rock="plaster",
              accent="brick", glow="lantern", liquid="water",
              step=("oak", "hop"),
              props=("chain", "lanternpost", "mcfence", "torch"),
              beats=[
    # The threshold: a lantern standing in the village water, then the
    # door -- a lintel is walked under, never jumped through, and a
    # walk is never the first node of a beat.
    ("doorstep", [n("lantern", arc=3.2, lift=1, spread=1, deco="lamp",
                    moat=True, orbs=1),
                  n("plaster", arc=2.3, lift=1, kind="walk", spread=0,
                    shell="tunnel")]),
    # Up the flank on half-height treads, hard against the wall: three
    # steps, three blocks, none of them a stretch. Slabs are the
    # commonest non-cube form in the reference by a wide margin.
    ("eaves", [n("oak", arc=2.8, lift=1, form="slab", hug=3.0,
                 spread=0),
               n("oak", arc=2.8, lift=2, form="slab", hug=3.0, spread=0,
                 orbs=1),
               n("oak", arc=2.8, lift=3, form="slab", hug=3.0,
                 spread=0)]),
    # Under the gable: brick, a lamp, and a tie beam low overhead.
    ("gable", [n("brick", arc=3.0, lift=3, hug=3.0, spread=0,
                 ceiling=2, deco="lamp"),
               n("roof", arc=3.4, lift=3, hug=4.0, spread=0, orbs=1)]),
], filler=[
    # The character *and* the level's one trick, because this is the
    # part that repeats: the tiled roofline with a beam over it, a
    # doorway, the drop down the well onto the pad in the water, and
    # the bounce back out.
    # The rise and the drop are in the same beat on purpose: machinery
    # is inserted between beats and leaves the body back at lift 1, so
    # a drop written as a beat's first node is not a drop, the pad is
    # landed on too slowly to throw anything, and the bounce silently
    # becomes a hop.
    ("rafters", [n("slime", arc=4.9, lift=1, form="slime", hug=4.2,
                   spread=0, pedestal_style="brick", moat=True),
                 n("brick", arc=3.3, lift=2, kind="bounce", spread=1,
                   orbs=2),
                 n("roof", arc=3.4, lift=2, hug=3.8, spread=0,
                   ceiling=2, deco="lamp"),
                 n("plaster", arc=2.3, lift=2, kind="walk", spread=0,
                   hug=3.8, ceiling=2)]),
], exit_beats=[
    # The way out is the tower: a lit footing against the wall and a
    # ladder up the shaft, walled by its own tube. The crossing onto
    # the next level is appended by the machinery.
    n("plaster", arc=3.2, lift=1, hug=2.2, spread=2, confine=True,
      deco="lamp"),
    n("oak", arc=2.4, step_y=8, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=False, spread=0, shell="shaft", orbs=2),
])
