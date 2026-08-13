"""Level 17: THE WEIR.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A mill race. The terrace is a flooded weir: the floor is wet green
# stone with the water cut down the middle of it, the first thing you
# do is wade, and the level's one big move is the fall over the sill.
# Up the sluice gates on their timbers, three blocks down onto the
# weed-slick apron, thrown two blocks straight back up by it onto the
# mill's beam, in over the wheel pit under the mill's roof, out through
# its far door on foot -- and then the ford repeats for as long as the
# terrace lasts. You leave up the mill's own oak ledges.
#
# Everything here that is not obvious was measured, and most of it only
# the per-beat fidelity table or the rejection counter would show:
#
# * **A level lays nine or ten landings and only a handful are yours**,
#   so the script is two beats and the character lives in the filler.
#   The tail of a longer script is never seen.
# * **``breaks=0``, so there is no lock.** A level's first floor break
#   is always too wide to jump and the machinery that crosses it costs
#   two of those landings. This is the water level: the channel and the
#   moats stop the walker without spending any.
# * **Authored nodes are *not* ramped** (``handplan._resolve`` sets
#   ``ramp=False``), so ``arc`` is the real distance and ``arc`` minus
#   both edges is the real jump. Written for the reference's modal
#   3.0-3.5 m: 3.6 up one, 3.9 level, 5.7 for the fall.
# * **The bounce needs a three-block fall.** Off a two-block drop the
#   pad gives back vy0 = 10.4 against the 10.58 that clearing +2 needs,
#   and every candidate is refused with "cannot reach" -- silently, as
#   an ordinary hop, because ``--design-only`` checks hops and slides
#   only. Off three blocks it gives 13.6.
# * **A slime pad must float.** With a pedestal it is offered only cells
#   with ground under them, and at the foot of a fall there are none;
#   ``pedestal=False`` took that node from 3/6 to 7/7.
# * **The willow is a hop gate.** The roster's watchtower is a *walk*
#   gate, whose three stored landings sit 3 blocks apart against a
#   1.4-3.05 m window (``GATE_NODES``): 20 reservations of 20 refused on
#   this level's bearings, so the structure was never framed. A hop gate
#   is offered at 4 blocks against 2.7-4.9 and reserves on every one.
# * **A chain of dependent landings belongs inside one beat**, because
#   the lock and the landmark crossing are inserted *between* beats. The
#   climb, the fall, the bounce and the mill are one beat for that
#   reason.
# * **A ``walk`` is never first in a beat** -- it needs its predecessor
#   within half a block and a beat boundary does not promise that.
#
# Against THE VAULT below (warm dark gold, plaza, interior, hoard) and
# BLUE RUN above (pale blue ice, ledge, slides, arch) this is green-grey
# wet masonry, dark timber and open water: different enclosure,
# different verb, different hue, different structure.
LEVEL = Level("THE WEIR", "plains", rise=7, gap=3.0, exit="stair",
              band=12.0, profile="channel", breaks=0, landmark="tree",
              ground="mossy", sub="cobble", rock="stonebrick",
              accent="darkoak", glow="lantern", liquid="water",
              props=("sugarcane", "lilypad", "mcfence", "grasstuft"),
              step=("stonebrick", "hop"), beats=[
    # The threshold: one lit block set on a rise in the level's own wet
    # stone, and then, two metres on, the first wade -- so the level
    # says what it is with its second landing.
    ("sill", [n("glowstone", arc=3.6, lift=1, spread=1, hug=3.6,
                deco="lamp", orbs=1),
              n("cobble", arc=2.9, lift=1, kind="walk", spread=0,
                hug=3.6, moat=True, orbs=1)]),
    # The whole of the level's one big idea, in one beat.
    ("weir", [n("darkoak", arc=3.6, lift=2, spread=1, hug=3.6),
              n("darkoak", arc=3.6, lift=3, spread=0, hug=3.6, orbs=1),
              n("slime", arc=5.4, lift=1, form="slime", spread=0,
                hug=3.6, pedestal=False),
              n("darkoak", arc=4.0, lift=3, kind="bounce", spread=1,
                hug=3.6, orbs=2)]),
    # The mill house, and its own beat rather than the tail of the one
    # above: a beat is laid whole or not at all and the climb's arc
    # budget clips whatever is left, so a seven-node beat spends its
    # last two nodes on the bounce that is the point of it.
    ("mill", [n("oak", arc=3.9, lift=3, spread=0, hug=3.6, shell="hall",
                ceiling=2),
              n("oak", arc=2.9, lift=3, kind="walk", spread=0, hug=3.6,
                orbs=1)]),
], filler=[
    # The ford, and this is where the level's character actually lives,
    # because a filler repeats and a script's tail does not: a stone in
    # its own dug pool with a lid over the jump onto it, then three legs
    # waded rather than jumped, then out. The wades are what hold this
    # level's plain-hop share down -- the exit climb is a third of it and
    # can only be hops.
    ("ford", [n("mossy", arc=3.9, lift=1, spread=1, hug=3.6, moat=True,
                ceiling=2),
              n("cobble", arc=2.9, lift=1, kind="walk", spread=0,
                hug=3.6, orbs=1),
              n("mossy", arc=2.9, lift=1, kind="walk", spread=0,
                hug=3.6),
              n("cobble", arc=2.9, lift=1, kind="walk", spread=0,
                hug=3.6),
              n("mossy", arc=3.4, lift=1, spread=1, hug=3.6, orbs=1)]),
], exit_beats=[
    # The mill's own oak ledges, lit top and bottom. Authored rather
    # than generated because the climb is the single biggest consumer of
    # a level's landings -- four of THE WEIR's ten -- and a generated
    # staircase of the level's stone says nothing about the place.
    n("darkoak", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      deco="lamp"),
    n("oak", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("darkoak", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("oak", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("darkoak", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("oak", arc=3.0, step_y=1, hug=2.6, spread=0, deco="lamp"),
])
