"""Level 2: WINDMILL REACH.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# **A working mill, the leat that drives it and the rick it fills.**
# Straw-gold the whole way -- hay underfoot at about a fifth of the
# cells over ploughed earth, gravel, oak boards and grass -- against THE
# GATEHOUSE's green below and MARKET STREET's terracotta above.
#
# The route is the mill's own working order, and the level says what it
# is inside four landings. In over a lit sill; **through the field gate,
# walked, on the plank bridge over the head of the leat**; straight up
# the mill's sack ladder, four blocks in one move, and in under the cap
# on to the loading stage; then **off the stage and three blocks down
# into the wheel pit**, on to a board hung over the dug water and the
# millstone standing in it; and up the rick -- bale, yard rail, top
# course -- which is where the way out begins.
#
# The order is not decoration, and it cost three rewrites to arrive at.
# Everything past about the fourth authored landing is at the mercy of
# how much terrace the exit climb has left itself, so the ladder is beat
# *two*: the mill is on screen and climbed before the budget can take it
# away. Written as beat four -- which is the reading order a mill
# suggests, yard then leat then mill -- the ladder fired on one visit in
# twenty-four and the level was a walk with a staircase on the end.
#
# The other half of that arithmetic is that the exit's reserve is
# ``(need + 1) * 3.2`` metres measured from **where the body is
# standing**, so a level that has already climbed asks the machinery for
# a shorter way out. That is the whole reason the descent into the pit
# stops at lift 2 rather than going to the floor: every block the pit
# gives away is a block the climb out has to buy back, at a landing a
# block, out of the same terrace the design is written on.
LEVEL = Level("WINDMILL REACH", "farm", rise=6, gap=3.0, exit="stair",
              band=10.5, shelf=5.0, breaks=3, landmark="windmill",
              ground="hay", sub="coarse", rock="oak", accent="darkoak",
              liquid="water", glow="lantern",
              # Thirteen materials with hay at about a fifth of the
              # weight: one committed hue and a long tail of dirt under
              # it, which is the shape a real terrace measures as. The
              # farm theme's own mix carries most of this; what is added
              # is the yard -- gravel, farmland, log.
              floor=(("coarse", 2), ("farmland", 2), ("gravel", 2),
                     ("dirt", 2), ("hay", 2), ("oak", 1), ("log", 1),
                     ("grass", 1), ("podzol", 1), ("moss", 1),
                     ("stone", 1), ("cobble", 1)),
              candy=("hay", "oak"), step=("hay", "hop"),
              props=("crop", "mcfence", "scarecrow", "sugarcane",
                     "lanternpost", "grasstuft"),
              beats=[
    # The threshold: a lantern set flush in the headland on a half step,
    # and two metres on the field gate itself -- *walked* under a checked
    # lid, because one impulse always rises 1.25 m and no arc gets beneath
    # a lintel low enough to read as a gate. The gate stands on the plank
    # bridge at the head of the leat, so the level's water is under the
    # feet in its first two seconds and the walker who never jumps drops
    # into the cut there.
    #
    # **The lantern stone is the one landing on this level standing on the
    # ground**, and the sack ladder now comes straight off it. A body steps
    # up one block, so anything at lift 1 is something a fall walks back
    # onto: the apron is where a level begins and everything after it is at
    # least two up (``docs/REHASH.md``). The walk that used to be here has
    # moved up the ladder to the loading stage, where it reads better
    # anyway -- you walk *inside* the mill rather than past its door.
    ("sill", [n("glow", arc=3.2, lift=1, spread=0, hug=3.0,
                deco="lamp", orbs=1, moat=True)]),
    # The mill, second beat and third landing: the sack ladder up the
    # roundhouse, four blocks in one move, and a stride in under the cap
    # on to the loading stage with the miller's lantern on it.
    #
    # Four is not a free number. A climb anchors on solid rock beside its
    # column at the column's middle cell and at its top, and out in the
    # lane the only candidate is the landing's own pedestal stack -- so
    # this carries a pedestal (the default) and a rise of at least four,
    # which is what puts that middle cell inside the landing rather than
    # in the plinth below it. At ``step_y=3`` the same node stops firing
    # and quietly becomes a hop.
    #
    # The stage is *walked* on to, and the walk is what lets it be
    # shelled: a shell roof sits in the cell the head sweeps at a hop's
    # apex and ``write`` refuses it there, so a cap over a jump is a roof
    # with a hole in it and a cap over a walk is a room. It is worth a
    # whole row of the contact sheet -- the eight frames at the top of
    # the ladder were sea and sky, and are now the inside of the mill.
    ("race", [n("rock", arc=2.4, step_y=4, kind="climb",
                climb_style="ladder", hug=2.4, spread=0,
                pedestal=True, pedestal_style="darkoak", orbs=2),
              n("ground", arc=2.7, lift=5, kind="walk", spread=0, hug=2.6,
                ceiling=3, shell="cave", deco="lamp", orbs=1)]),
    # The wheel pit, and the level's descent: off the stage and three
    # blocks straight down. It is the only long jump here and it is long
    # *because* it drops -- falling takes time and the body does not slow
    # down while it does, so a -3 may ask for 3.72 to 6.05 m where a flat
    # hop stops at 4.26. It lands on the launder board hung over the
    # water (``pedestal=False``: there is nothing under it to walk to),
    # and the millstone standing in the dug pit is the step off it.
    #
    # ``hug`` is 2.6 and not 3.2, which is a *camera* number rather than
    # a placement one: the lens locks on to the landing through take-off
    # and flight, so a landing thrown outboard aims the whole fall at the
    # sea. Pulled in against the core the same jump looks down the
    # corridor.
    #
    # The climb and the drop are adjacent in the script on purpose:
    # machinery is inserted *between* beats and leaves the body back at
    # lift 1, so a fall written far from the climb that fed it is a fall
    # that does not happen.
    ("pit", [n("accent", arc=5.2, lift=3, spread=1, hug=2.6, ceiling=5,
               pedestal=False, orbs=3),
             n("stone", arc=3.2, lift=3, spread=1, hug=2.8, moat=True,
               pedestal_style="gravel", orbs=1)]),
    # The rick, climbing back out of the pit, and three different
    # questions in three landings:
    #
    # * **bale** -- the only plain +1 in the level's body, arc 3.2, a
    #   reach of 2.52 against a window that stops at 3.10.
    # * **rail** -- a fence at lift 2 is a walking surface at 2.5, so this
    #   is a half step onto a *sliver*: ``EDGE`` 0.05 against a block's
    #   0.34, so the feet plant dead centre. Placement, not distance.
    # * **top course** -- off the rail onto the stack, another half step,
    #   with the gantry the sacks swing from checked in overhead.
    ("rick", [n("ground", arc=3.2, lift=4, spread=1, hug=2.8, ceiling=5,
                orbs=1),
              n("rock", arc=3.0, lift=4, form="fence", spread=0, hug=2.6,
                radial=0.9),
              n("ground", arc=3.0, lift=5, spread=0, hug=2.6, radial=-0.9,
                ceiling=3, orbs=1)]),
], filler=[
    # The yard, which is what the terrace plays if it outlasts the
    # script: down off the stack onto the cart bed, a stride along the
    # boards, out onto the rail and back up. No ``moat`` anywhere in here
    # -- the loop's second lap would dig away the ground the first lap's
    # pedestals stand on.
    ("yard", [n("ground", arc=4.2, lift=5, spread=2, hug=2.8, ceiling=5,
                orbs=1),
              n("rock", arc=2.7, lift=5, kind="walk", spread=0, hug=2.6,
                radial=0.9),
              n("accent", arc=3.0, lift=5, form="fence", spread=0,
                hug=2.4, radial=-0.9),
              n("ground", arc=3.0, lift=5, spread=0, hug=2.6, orbs=1)]),
], exit_beats=[
    # Out over the top course of the rick that is being built against the
    # cliff: bale, board, bale, board, and the last lantern in the level
    # on the top one. Authored rather than left to the generated stair
    # because the climb out is the single biggest consumer of a level --
    # a third to two thirds of every visit -- and a flight of the level's
    # own stone says nothing about the place. A tread that cannot be
    # placed hands the whole thing back to the generated staircase, so
    # that reliability chain is still underneath this.
    #
    # Two things here are measured rather than chosen. The **first tread
    # carries no ``hug``**, exactly as the generated stair's does not: it
    # is placed from wherever the body happens to be standing, and
    # pinning it to a lane it cannot reach throws the whole list away.
    # There were **six**, chosen when a refused crossing re-planned the
    # whole climb as a generated staircase (20 and 16 crossing attempts
    # over 24 runs at four and five treads, against 14 at six). That is no
    # longer how a refused crossing behaves -- see the note further down --
    # and at six the fifth tread was failing four visits in six.
    #
    # ``hug=2.2`` against the generated stair's 2.4: harder against the
    # cliff the treads read as ledges cut into the tower rather than as
    # free-standing columns, and each carries a beam along its own arc --
    # the one column of the lens an exit climb otherwise spends looking
    # at sky.
    #
    # The note that used to sit here said about a third of the exit climb
    # is these treads and the rest is the engine's own recovery, and that
    # it was out of reach of a level module. It was right, it was found
    # and fixed on 2026-08-14, and the two engine faults are written up in
    # ``CLAUDE.md`` -- a refused tread threw the whole authored exit away,
    # and an authored climb of fixed height overshoots a ``need`` that is
    # not fixed.
    #
    # **Five treads, not six.** Measured per tread over ten runs, the
    # first four place on every visit and the fifth places on two of six:
    # 24 refusals of ``no move: hop`` and 12 of ``body does not fit on
    # landing``. That is the terrace running out under a staircase that
    # walks along it, and it is not something a shorter arc can fix -- an
    # arc of 2.6 is a *jump* of 1.92, under ``MIN_HOP``. Dropping the
    # sixth took this level's mean exit climb from 11.0 landings to 5.5
    # and the tower's generated staircase from 134 landings a sweep to
    # 126. The lamp and the last orb moved onto the new top tread.
    #
    # **And it is two treads now, not five.** The yard cruises five blocks
    # over the terrace since the rehash, so what the climb has left to gain
    # is the level's rise of six minus that, plus the one block the crossing
    # brings back down: two. The level does its own climbing on the sack
    # ladder in its second beat, which is a better thing to watch than a
    # staircase and was always the level's own idea.
    n("ground", arc=3.0, step_y=1, spread=0, confine=True, ceiling=6,
      pedestal_style="coarse", orbs=1),
    n("log", arc=2.9, step_y=1, hug=2.2, spread=0, confine=True,
      ceiling=6, pedestal_style="hay", radial=0.9, deco="lamp", orbs=1),
])
