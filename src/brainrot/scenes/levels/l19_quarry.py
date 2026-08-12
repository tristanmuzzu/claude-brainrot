"""Level 19: THE QUARRY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A worked sandstone quarry cut back into the cliff. In under the lintel
# of the adit, up the benches half a block at a time, off the top of the
# heap on to the spoil tip -- which throws you back at the face -- down to
# the flooded sump and across it on the stone that came out of it, and
# out along the rim cut, where the quarry has eaten past the edge of the
# tower and the last benches hang over two hundred metres of sea.
#
# Orange terracotta floor, pale chiselled faces, water standing in the
# bottom: the one hot level between the ice below and the jungle above,
# and its threshold is a lantern set flush in the floor at the change.
#
# Three things here are deliberate and two of them cost something.
#
# **The rim cut is the tower's only descent down the outside** -- signed
# ``step_y`` on to benches with nothing under them -- and it is why this
# level's frames have always been the emptiest in the roster (77% of the
# view sky and sea before this pass). So it is the *last* beat rather
# than the first, it is four landings and no more, and every jump in it
# carries a lid: the crane's staging is overhead the whole way out,
# which is the difference between a cube in the sky and a place.
#
# **Everything before it is built on ground.** A tunnel at the mouth,
# pedestals under every bench, the sump dug into the terrace and filled,
# a head-hitter over the working face. A level with nothing above head
# height frames as sky whatever else is right about it, and the two
# levers that actually moved the number were terrain under the body and
# lids over it.
#
# **The hop is short here on purpose** -- 2.7 to 2.9 m stand point to
# stand point for the ordinary beats, against the reference's 3.16 m
# median -- because the terrace only holds about sixteen landings and
# eleven of them are already spoken for by the lock, the landmark
# crossing and the climb out. Long jumps here buy nothing but a level
# made of machinery.
LEVEL = Level("THE QUARRY", "desert", rise=4, gap=3.2, exit="ladder",
              band=9.0, shelf=5.0, breaks=3, landmark="crane",
              ground="terracotta", sub="sandstone", rock="chiselled",
              accent="sandstone", glow="lantern", liquid="water",
              step=("chiselled", "hop"), beats=[
    # The threshold: a lantern flush in the quarry floor, and a walked
    # step in under the lintel. The palette changes completely here --
    # ice white behind, terracotta ahead -- and the adit is a two-metre
    # pinch, not a room.
    ("mouth", [n("glow", arc=3.5, lift=1, spread=0, deco="lamp",
                 orbs=1),
               n("chiselled", arc=2.7, lift=1, spread=0, kind="walk",
                 shell="tunnel", deco="lintel")]),
    # The benches, worked half a block at a time, with the overburden
    # left standing in a beam overhead.
    # (the first of these is written long -- 3.02 m stand point to stand
    # point rather than 2.7 -- because it is the jump *out of the adit*,
    # and a landing tight against a tunnel mouth is one the shell's own
    # far wall keeps refusing.)
    ("benches", [n("rock", arc=3.7, lift=2, spread=0, ceiling=1),
                 n("accent", arc=3.5, lift=3, form="slab", spread=0,
                   orbs=1)]),
    # The tip: off the top of the heap on to the spoil, which throws you
    # straight back at the working face. The one slime pad in the level.
    ("tip", [n("slime", arc=4.6, lift=1, form="slime", spread=0),
             n("accent", arc=4.0, lift=2, kind="bounce", spread=1,
               orbs=2)]),
    # The sump. The cut has taken the floor down to the water table and
    # the way across is the stone that came out of it.
    ("sump", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
              n("sub", arc=3.5, lift=1, spread=0, moat=True),
              n("chiselled", arc=3.5, lift=1, spread=0, moat=True,
                orbs=1)]),
    # The rim cut: the only place in the tower where the course stands
    # outboard of the tower itself. Down two, down one more, and back in
    # under the staging.
    ("rimcut", [n("rock", arc=4.6, step_y=-2, hug=6.6, pedestal=False,
                  spread=0, ceiling=2, orbs=1),
                n("accent", arc=4.0, step_y=-1, hug=7.0, pedestal=False,
                  spread=0, ceiling=2),
                n("rock", arc=3.2, step_y=1, hug=5.8, pedestal=False,
                  spread=0, ceiling=1, orbs=1),
                n("rock", arc=3.2, step_y=1, hug=4.6, spread=0)]),
], filler=[
    # The character of the place, for as long as the terrace lasts: a
    # stone standing in the water, a half-height bench cut out of the
    # face, and a jump under the overburden.
    ("spoil", [n("sub", arc=3.5, lift=1, spread=0, moat=True, orbs=1),
               n("accent", arc=3.5, lift=2, form="slab", spread=0),
               n("rock", arc=3.4, lift=2, spread=0, ceiling=1,
                 orbs=1)]),
])
