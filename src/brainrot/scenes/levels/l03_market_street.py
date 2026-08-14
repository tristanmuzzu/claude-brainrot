"""Level 3: MARKET STREET.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A covered market street -- and the route is not the street. It is the
# stalls and the roofs *over* the street.
#
# The idea in one sentence: *you come in under the gate at paving level,
# climb the market furniture -- rail, counter, awning, tile -- and spend
# the rest of the level on the roofs, looking down into your own street.*
# The level below is a yellow farm on a five-cell shelf; the one above is
# a black timber deck over water. This is red, close, and stacked: four
# blocks of house between the running line and the ground for most of its
# length, which is the one thing neither neighbour has.
#
# **The plaza has to earn itself.** ``profile="plaza"`` is a full floor,
# and a full floor with parkour standing on it is the thing the owner
# rejected -- you walk round it. What makes this one a street rather than
# a plate is that the *route leaves it*: from the fourth landing on,
# every designed landing is two to four blocks up, half of them floating
# with nothing under them at all, and the paving below is cut by three
# floor breaks and the gutter the market jump digs. Walking the street
# gets you along the street; it does not get you to the ladder, which
# starts on a roof.
#
# Its identity is the **floor**, and it is written out rather than left
# to the theme. The village theme's own mix is grey -- coarse, cobble,
# stone, andesite -- and this level was painted in it, which is why the
# last contact sheet of it was a car park with red cubes standing on a
# pale plate. Twelve materials now, measured over an 80x80 patch:
# terracotta 43%, brick 14, roof tile 11, coarse 6, plaster 6, and a
# long tail of andesite, clay, moss, oak, gravel, dirt and cobble under
# them. Mean floor colour (162, 112, 89) against the cone's own
# (118, 113, 109). That dominant share is above the real map's median
# 26% and inside its range -- its sand terrace runs 44% -- and it is
# deliberate: this level's whole job in the seam is to be *red* between
# a yellow farm and a black sawmill.
#
# No decorative light anywhere: the three lamps are the threshold stone,
# the ridge you jump off, and the foot of the ladder out.
#
# **Written for two beats and a filler, not for ten.** Measured, a visit
# to this level lays about eighteen landings and nine of them are the
# script's: the gate is two, the climb onto the roofs is five, and
# everything after that is the filler, which repeats. So the climb is the
# whole of the second beat -- a beat is truncated from the end and
# inserted machinery puts the body back on the paving, so a rise split
# across two beats is a rise that happens once in three visits -- and the
# level's character (roof, roof, off the eave, back up the house front)
# is the loop.
LEVEL = Level("MARKET STREET", "village", rise=7, gap=3.0, exit="ladder",
              band=8.5, profile="plaza", breaks=3, landmark="watchtower",
              ground="terracotta", sub="brick", rock="plaster", accent="roof",
              glow="lantern", liquid="water", step=("brick", "hop"),
              # Twelve materials with terracotta at 26% of the weight, the
              # same shape the real map's terraces measure as: one committed
              # hue and a long tail of grit under it. The village theme's own
              # mix is grey -- coarse, cobble, stone, andesite -- and painted
              # a street that read as a car park with red cubes on it.
              floor=(("terracotta", 4), ("brick", 3), ("roof", 2),
                     ("coarse", 2), ("cobble", 1), ("gravel", 1),
                     ("oak", 1), ("clay", 1), ("mossy", 1), ("dirt", 1),
                     ("andesite", 1)),
              props=("mcfence", "lanternpost", "torch", "crop", "flower",
                     "pebbles"),
              beats=[
    # The threshold. A lantern flush in the paving on a half step, then
    # the gate itself -- walked through, because one jump impulse always
    # rises 1.25 m and no arc gets under a lintel low enough to read as
    # a door. The tunnel shell is a two-metre pinch, not a room, and it
    # only survives whole because it is wrapped round a *walk*: a shell
    # roof sits in the cell the head sweeps at a hop's apex, so a tunnel
    # over a jump is a roof with a hole in the middle of it.
    #
    # The walk is *second* on purpose: first in a beat it follows
    # machinery at an arbitrary height and a walk needs its predecessor
    # within half a metre.
    ("gate", [n("glow", arc=3.2, lift=1, form="slab", spread=0,
                deco="lamp", orbs=1),
              n("rock", arc=2.8, lift=1, form="slab", kind="walk",
                spread=0, shell="tunnel")]),
    # The market, and this is the level: four landings that climb the
    # furniture of a stall from the paving to the ridge tiles, and then
    # the jump across the street between two roofs.
    #
    # It is one beat and not two because machinery -- the lock across the
    # first floor break, the crossing through the watchtower -- is
    # inserted *between* script beats and leaves the body back at lift 1.
    # A climb that starts again from the paving is a climb that never
    # gets anywhere, and this measured 50% split against 94% joined last
    # time it was tried.
    #
    # The steps, and what each asks:
    #
    # * **rail** -- a fence at lift 1 is a walking surface at 1.5, so
    #   this is a +1 onto a one-cell perch: the reach is 2.61 against a
    #   +1 window of 2.00-3.10, and the landing is a sliver (``EDGE``
    #   0.05) rather than a plate. Placement, not distance.
    # * **counter** -- off the rail onto the stall top is only +0.5,
    #   because the fence already stands half a block proud. The short
    #   step is deliberate: it is the one beat in the climb that is easy,
    #   and it is where the eye finds the awning. It is a *hop* and was
    #   written as a walk, which is the one thing a fence top cannot do:
    #   the feet stand half a block above the block holding them up, so
    #   there is no cell under them and a walk across the gap is a walk
    #   across air. ``_move_for`` refuses it now; at arc 2.7 off a post's
    #   dead-centre plant it is a reach of 2.31, comfortably a hop.
    # * **awning** and **tiles** -- two ordinary +1 hops at arc 3.2,
    #   which is a reach of 2.52 against 3.10. Centred, not at the top of
    #   the envelope: a +1 written at 3.6 is a reach of 2.92 and is the
    #   arc that has to fall back.
    # * **across the street** -- level, arc 4.4, reach 3.72 against a
    #   flat maximum of 4.26. The long one, and the only one in the level
    #   with nothing under it: ``pedestal=False`` leaves the far roof
    #   floating, and ``moat`` digs the gutter into the paving four
    #   blocks below it, so the jump is over water whether or not you
    #   ever touch it. It is the beat's last node, which is where a moat
    #   has to go -- a moat is painted the moment its landing commits and
    #   the pond then swallows the next landing of the same beat.
    ("stalls", [n("oak", arc=3.0, lift=1, form="fence", spread=0,
                  deco="post", orbs=1),
                n("rock", arc=2.7, lift=2, spread=0),
                n("accent", arc=3.2, lift=3, spread=0, deco="lintel",
                  orbs=1),
                n("accent", arc=3.2, lift=4, spread=0,
                  pedestal_style="plaster"),
                n("accent", arc=4.4, lift=4, spread=1, ceiling=3,
                  pedestal=False, moat=True, orbs=2)]),
], exit_beats=[
    # The way out is the watchtower at the end of the street, and you
    # reach it **from the roofs** -- the launch landing is at lift 4, not
    # on the paving. Two reasons, one of each kind. The design one is the
    # rule that a level's descent belongs in its first two thirds and
    # nothing after the high point goes down: this level's drop is the
    # eave in the filler, and dropping back into the street to leave
    # would undo the whole climb one landing before the seam. The
    # measured one is that the filler leaves the body at lift 2, 4 or 6,
    # and a launch written at lift 1 is then a five-block fall across
    # 2.8 m, which nothing makes -- it is refused, recovered from, and
    # the ladder is asked for from wherever the recovery hop landed.
    #
    # ``spread=3`` is what covers all three of those entry heights, and
    # ``step_y=4`` is measured rather than chosen: from a roof at
    # surface 4 it tops out at 8, one block above the next level's own
    # floor, which is exactly what the crossing wants -- it comes down
    # one block onto it. Measured over 16 runs against the same world,
    # the four candidates were street/6 (10 climb moves, 2 unchecked),
    # roof/5 (18, 5), roof/4 (14, 2) and the generated climb (9, 2). The
    # last column is why this is roof/4 and not roof/5.
    #
    # The ladder is lit at its foot, which is the last of the level's
    # three lamps and the only thing in the closing seconds that says
    # which way out is. The generated staircase is still underneath as
    # the fallback, in ``spawn``.
    n("rock", arc=3.6, lift=4, hug=2.8, spread=3, confine=True),
    n("ladder", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
      hug=2.6, pedestal_style="plaster", spread=0, confine=True,
      deco="lamp", orbs=2),
], filler=[
    # The roofs, and on a level that lays eighteen landings this is half
    # of what is seen. Four landings that close into a loop, and the loop
    # is the level's shape in miniature: along the ridge, off the eave
    # into the street, back up the house front, onto the next roof.
    #
    # * **ridge** -- the entry landing, at lift 4 with ``spread`` 2. It
    #   is the one node here whose predecessor is not known: the loop can
    #   be entered off the market jump, off a lock's far landing or off
    #   the watchtower's doorway, and those are three different heights.
    #   Two of fallback is what covers all of them.
    # * **the lit ridge** -- level, arc 3.6, and a ``ceiling`` beam at
    #   three: the awning spar over the street, which is a real
    #   head-hitter over a flat hop (the apex is 1.25) and the cheapest
    #   overhead mass a level author has. The lantern on it is the mark
    #   for the drop, and it is the only light between the gate and the
    #   ladder.
    # * **off the eave** -- lift 4 to lift 2 is a two-block fall across
    #   4.9 m of arc, a reach of 4.22 against a window of 3.12-5.56. The
    #   long jump of the level and the only way down off the roofs: a
    #   descent is the only jump that can be long, because falling takes
    #   time and the body does not slow down while it does. It lands on
    #   an oak stall board floating over the paving -- ``pedestal=False``,
    #   so there is nothing under it to walk to.
    # * **the ladder up the house front** -- the one special block the
    #   reference leans on hard, and the only non-hop this level has
    #   that is not a threshold. ``step_y=4`` from the board at surface
    #   2 puts the column's middle cell inside the landing's own
    #   pedestal, which is what a climb has to anchor on: written
    #   shorter, or without a pedestal, it finds no wall and silently
    #   becomes a hop. It tops out at surface 6, and the loop's seam --
    #   a two-block fall of 4.4 m onto the next ridge at 4 -- is legal
    #   from there, which is half of what a filler beat ever loses
    #   fidelity to. Measured against the same loop ending in a plain
    #   +1 hop instead: 89% plain hop against 86%, for four points of
    #   this beat's exactness. Worth it.
    #
    # No ``moat`` anywhere in here, and that is not taste: the filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals stand on. The level's water is the gutter under the
    # market jump, in a beat that plays once.
    ("ridge", [n("accent", arc=4.4, lift=4, spread=2, deco="lintel",
                 orbs=1),
               n("glow", arc=3.6, lift=4, spread=0, deco="lamp",
                 ceiling=3),
               n("oak", arc=4.9, lift=2, spread=1, ceiling=3,
                 pedestal=False, orbs=2),
               n("rock", arc=2.4, step_y=4, kind="climb",
                 climb_style="ladder", hug=2.4, spread=0,
                 pedestal_style="plaster", orbs=2)]),
])
