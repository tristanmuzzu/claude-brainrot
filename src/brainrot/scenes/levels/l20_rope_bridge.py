"""Level 20: ROPE BRIDGE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A rope bridge slung along a mossy bank over the river. You come out of
# the doorway in the pier, walk on at the bridge head between its two
# posts, cross the planks -- they climb, they do not sag -- drop off the
# far end on to the mat of creeper at the foot of the tree, and it throws
# you back up. Then in against the pier on the two ledges it is anchored
# to, down to the bank where the river is cut into the ground, and up
# into the canopy for the way out.
#
# Three things had to change from the level this replaces, which was four
# oak cubes in an empty sky at 65% empty frame.
#
# **The hand ropes are real geometry.** Every plank carries a post and
# the deck carries a lid three cells up. A bridge is mostly the things
# holding it up, and if none of them are built the deck is not a bridge,
# it is four cubes.
#
# **The deck is slung just past the bank rather than out at the rim.**
# Measured: floating planks out over the drop cost about two and a half
# points of empty frame each, and everything this level does to earn them
# back -- the doorway, the lids, the moss -- is worth about the same. So
# there are two planks rather than four, they sit a metre outboard of the
# shelf edge where the bank is still under the lens, and what you are
# crossing is the river and the floor breaks.
#
# **The order is the design.** A level only ever gets four or five
# authored landings laid before the lock, the landmark crossing and the
# climb out have spent the terrace, and a beat is truncated to what is
# left -- so the two beats that carry a verb other than the plain hop
# (the walked threshold, and the drop on to the creeper) are written
# first and second, not saved for later. Everything after them is a
# bonus, and the filler is more bridge.
#
# Green after the quarry's orange, wide where the quarry was a slot, and
# it descends twice -- once off the deck on to the creeper, once off the
# top of the pier.
LEVEL = Level("ROPE BRIDGE", "jungle", rise=5, gap=3.4, exit="vine",
              band=10.0, shelf=5.0, breaks=3, landmark="tree",
              ground="moss", sub="podzol", rock="junglelog",
              accent="oak", glow="lantern", liquid="water",
              step=("junglelog", "hop"), beats=[
    # The threshold: a lantern flush in the moss at the change of
    # colour, then the doorway through the pier and the walked step on
    # to the bridge head. A deck is walked on to, never jumped on to.
    ("head", [n("glow", arc=3.5, lift=1, spread=0, hug=3.2,
                deco="lamp", orbs=1),
              n("rock", arc=2.7, lift=1, spread=0, hug=3.0,
                kind="walk", shell="tunnel", deco="post")]),
    # The deck: two planks climbing out over the water, a post on each
    # and the hand rope overhead.
    ("deck", [n("oak", arc=3.5, lift=2, form="trapdoor", spread=0,
                hug=4.2, pedestal=False, deco="post", ceiling=2),
              n("oak", arc=3.4, lift=3, form="trapdoor", spread=0,
                hug=4.6, pedestal=False, deco="post", ceiling=2,
                orbs=1)]),
    # Off the end of the deck on to the creeper mat at the foot of the
    # tree, which throws you straight back up. The one slime pad here.
    ("fall", [n("slime", arc=4.4, lift=1, form="slime", spread=0,
                hug=3.6),
              n("rock", arc=4.0, lift=2, kind="bounce", spread=1,
                hug=3.2, orbs=2)]),
    # In against the pier: the two ledges the bridge is anchored to, cut
    # into the face, with a beam over the second.
    #
    # There was a vine climb here and it is gone, which is worth writing
    # down. A ``climb`` needs a free column with solid rock behind it and
    # a grab within 4.2 m; offered from a plank out over the drop it was
    # refused 0 of 6 times, and offered from a wall ledge it never got
    # laid at all, because this beat is the fourth in the level and a
    # level only ever gets four or five authored landings before the
    # machinery has spent the terrace. Worse, the *next* beat was written
    # against the height the climb would have reached -- so a verb that
    # silently does not fire does not merely go missing, it makes the
    # landing after it illegal, and that was this level's one unchecked
    # emergency placement.
    ("lash", [n("rock", arc=3.5, lift=1, spread=0, hug=2.6),
              n("accent", arc=3.4, lift=2, spread=0, hug=2.4,
                ceiling=1)]),
    # Down to the bank: the moss, and a log standing in the river.
    ("bank", [n("ground", arc=4.6, lift=0, form="floor", hug=3.4,
                orbs=1),
              n("rock", arc=3.5, lift=1, spread=0, hug=3.0,
                moat=True)]),
    # And up into the canopy and down again to the water.
    ("canopy", [n("accent", arc=3.4, lift=2, spread=0, hug=2.8,
                  ceiling=2),
                n("rock", arc=3.5, lift=1, spread=0, hug=3.2,
                  moat=True, orbs=1)]),
], filler=[
    # More bridge: this is what the level is, so this is the filler.
    ("cable", [n("oak", arc=3.5, lift=2, form="trapdoor", spread=0,
                 hug=4.2, pedestal=False, deco="post"),
               n("oak", arc=3.5, lift=1, form="trapdoor", spread=0,
                 hug=4.8, pedestal=False, deco="post", ceiling=2,
                 orbs=1),
               n("rock", arc=3.4, lift=1, spread=0, hug=3.4, moat=True,
                 orbs=1)]),
])
