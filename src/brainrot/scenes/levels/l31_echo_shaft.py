"""Level 31: ECHO SHAFT.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A geode well sunk through the terrace, with black water in the bottom
# of it and a ladder up the inside.
#
# This is the tower's *vertical* level and it has to earn that against
# THE SILENCE, which is the other deep-dark place: that one is a drowned
# gallery bored sideways into the cliff, all tunnel and bounce. This one
# goes down and then up, and its whole palette is the geode -- deepslate
# skin, a white calcite band, amethyst in the middle of it. Calcite is
# the point: the level this replaces was black blocks on a black cliff
# against a bright sky and 55% of the view was empty, because there was
# no light value anywhere in the lower half of the frame to hold the eye.
#
# The shape. A lit amethyst sill on the rim with the water dug out round
# it; a stride under the lintel into the wellhead; two calcite kerbs up
# to the lip and then the fall, two blocks down onto a stone standing in
# the sump -- **the descent, and it is a third of the way in**, because a
# level that drops after its own high point reads as climb-then-fall. Out
# of the sump on the ladder, which is the level's one idea and the reason
# its exit is a climb at all; then a lit gallery a block under the head
# of it, and the cave bay in the wall.
#
# Three things this file is careful about, all of them measured
# elsewhere and all of them silent when got wrong:
#
# * **The climb must appear in the move mix by name.** ``_climb_move``
#   wants solid rock within one cell of the column at its middle index
#   and at its top; out in the lane there is nothing to grab and the
#   ladder becomes a staircase with nothing reporting it. The in-body
#   one therefore keeps its pedestal and hugs 2.4, and the exit one
#   carries its own ``shell="shaft"`` tube, which is the wall the
#   generated climbs borrow.
# * **The old shaft was oak.** ``n("oak", ...)`` on a deep-dark level
#   put a brown wooden tube round the one climb in it, and at 10 m the
#   lens was full of plank -- three of the sixty-three frames on the old
#   contact sheet are nothing but brown. The column is deepslate now and
#   the ladder is the model on its face.
# * **The rise and the drop live in the same beat.** Machinery is
#   inserted between beats and leaves the body back at lift 1, so a fall
#   written as a beat's first node is not a fall.
LEVEL = Level("ECHO SHAFT", "deepdark", rise=8, gap=2.6, exit="ladder",
              band=8.5, shelf=3.5, profile="ledge", breaks=3,
              landmark="arch",
              ground="sculk", sub="tuff", rock="deepslate",
              accent="calcite", glow="amethyst", liquid="water",
              props=("pebbles", "dripstone", "chain", "torch"),
              step=("calcite", "hop"), beats=[
    # The threshold: one amethyst block flush in the sculk with the
    # water cut out round it, and then the mouth of the well, walked
    # under a lid. A lintel is never jumped -- one impulse rises 1.25 m,
    # so the head sweeps the two cells over every take-off and an arc
    # under a low beam is refused every time.
    ("brink", [n("glow", arc=3.2, lift=1, spread=1, deco="lamp",
                 moat=True, orbs=1),
               n("ground", arc=2.4, lift=1, kind="walk", spread=0,
                 ceiling=3)]),
    # The wellhead, and the level's descent. Two calcite kerbs up to the
    # lip -- the white band of the geode, and the only light value in
    # the lower half of the frame -- then two blocks down onto a stone
    # standing in the sump, with nothing under it.
    # The two kerbs float. They are ledges cut into the rim of the well
    # rather than blocks stood on it, which is what they should look
    # like anyway -- and a pedestal on a ``ledge`` has to find ground
    # under a shelf that wobbles about a block and a third either side
    # of its nominal width and has three holes in it. ``_targets``
    # returns nothing and records no rejection when it cannot, so the
    # landing is simply missing and the beat still reads as placed.
    ("wellhead", [n("accent", arc=3.3, lift=2, spread=0,
                    pedestal=False),
                  n("accent", arc=3.3, lift=3, spread=0, ceiling=2,
                    deco="lamp", pedestal=False, orbs=1),
                  n("rock", arc=4.9, lift=1, spread=0, moat=True,
                    orbs=2),
                  n("rock", arc=3.4, lift=1, spread=0,
                    pedestal=False)]),
    # The bay at the bottom of the well: rough rock closing over two
    # metres of it, which is what the real map's enclosure actually
    # measures -- a pinch, not a room. One amethyst in the roof is the
    # only light and the way out of it is walked. It sits at lift 1
    # because a shell only grows *walls* where the terrain gives them a
    # footing; higher up you get a roof and open sides, and a bay with
    # open sides is not a bay.
    ("geode", [n("glow", arc=3.3, lift=1, spread=0, deco="lamp"),
               n("accent", arc=3.2, lift=1, spread=0, shell="cave"),
               n("ground", arc=2.4, lift=1, kind="walk", spread=0,
                 shell="cave", orbs=1)]),
    # The shaft, and it is the *last* script beat on purpose: everything
    # this level does below is a descent, and the way out has to be the
    # highest thing in it or the eye reads the whole level as
    # climb-then-fall.
    #
    # It is a *body* climb as well as the exit one, because the exit
    # climb is half of every run and the move mix cannot tell the two
    # apart from outside. Pedestal on, hug 2.4, four blocks: at three
    # the beat fell to 43% and the verb vanished from the mix entirely,
    # and out in the lane with no pedestal there is no wall for the
    # column to hang on at its middle cell.
    ("shaft", [n("rock", arc=3.2, lift=2, spread=0, pedestal=False),
               n("deepslate", arc=2.4, step_y=4, kind="climb",
                 climb_style="ladder", hug=2.4, spread=0, orbs=2),
               n("accent", arc=3.4, lift=5, spread=0, ceiling=2,
                 deco="lamp", orbs=1)]),
], filler=[
    # The voice, repeated, and it stays *up* -- calcite ledges hung off
    # the inside of the well a block under its head, looking down the
    # shaft, with the rock lid a couple of blocks over them. Nothing in
    # here falls more than one block, because the filler is what the
    # tail of a long terrace is made of and this level must not spend
    # its last seconds giving back the climb.
    #
    # No moat anywhere in it either: the filler loops, and the second
    # lap digs away the ground the first lap's pedestals stand on.
    ("echo", [n("accent", arc=3.4, lift=4, spread=0, pedestal=False,
                ceiling=2, orbs=1),
              n("ground", arc=2.4, lift=4, kind="walk", spread=0,
                ceiling=3),
              n("glow", arc=3.3, lift=5, spread=0, pedestal=False,
                deco="lamp"),
              n("rock", arc=3.4, lift=5, spread=0, pedestal=False,
                orbs=1)]),
], exit_beats=[
    # Out of the well the way you came into it: a lit calcite footing
    # hard against the wall and eight blocks of ladder in its own tube.
    # Eight is the whole of this level's rise and the tallest climb in
    # the tower, which is the one thing ECHO SHAFT is for.
    #
    # **Splitting it into three stone steps and a five-block ladder was
    # tried and reverted.** It was aimed at the lens: a climb runs at
    # 2.35 m/s, so eight blocks is three and a half seconds with a
    # wooden stile a hand's width from an eighty-degree lens. It moved
    # the jammed-frame count by *nothing at all* -- 116 of 640 frames
    # both ways, to the frame -- because the frames it was aimed at are
    # the **in-body** climb rather than this one, and it cost six points
    # of fidelity and four of designed content in the shuffle. The lens
    # bill for this level is the price of the verb, and the verb is what
    # the level is.
    #
    # **Check the move mix in ``--report`` for the word ``climb``**: if
    # it is missing this is an eight-step staircase and the level has no
    # idea left in it.
    n("accent", arc=3.2, lift=1, hug=2.2, spread=2, confine=True,
      deco="lamp"),
    n("deepslate", arc=2.4, step_y=8, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=False, spread=0, shell="shaft", orbs=2),
])
