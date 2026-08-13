"""Level 1: THE GATEHOUSE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The tower's front door, and it is a green one: grass, moss, podzol and
# a gravel path, against the pale purple THE GATE hands over. You come in
# over a lit sill into a bay cut back in the cliff, bounce out of the
# green mire at the head of the moat, climb the gate tower's ladder, come
# down off the wall-head onto cobbles standing in the moat under a lintel,
# and leave through the postern.
#
# It was written as a ``channel`` first -- a water cut down the middle of
# a full-width floor, which is the reference's "where the ground is wide,
# its whole width is hazard". Measured, that profile is what empties the
# frame: a wide flat plate has nothing standing on it, and the same beats
# read **63% empty sky on a channel and 46% on a ledge**, because a shelf
# stands its landings on plinths and a plinth is masonry in the near
# ground. A five-cell shelf with the drop directly outboard is the
# reference's commoner answer and it is the right one here.
#
# **Beat order is the budget, and the numbers are worth writing down.**
# The terrace is about 59 m of arc and the exit climb reserves a landing's
# worth per block still to be gained -- 27 m with a staircase, 18 m with a
# ladder, which is why the exit is a ladder. ``breaks=0`` is the other
# half: any break at all forces the lock, which is one to four landings of
# machinery on every run, and this level does not need it -- the moats cut
# into the walking line and the shelf's own wobble hold a no-jump walker
# to 27%. A beat short of budget is *truncated*, not skipped, so a
# three-node showpiece loses its third node and the bounce with it. Hence
# short beats with the identity in the first three.
LEVEL = Level("THE GATEHOUSE", "plains", rise=4, gap=2.8, exit="ladder",
              band=12.0, shelf=5.0, breaks=0, landmark="cabin",
              ground="grass", sub="podzol", rock="mossy", accent="oak",
              liquid="water", glow="lantern",
              props=("grasstuft", "flower", "mcfence", "lilypad"),
              candy=("oak", "mossy"), step=("mossy", "hop"), beats=[
    # The threshold: one emissive block flush in the floor, on a rise,
    # with the palette changing completely at it, and a lamplit bay cut
    # back into the cliff around the arrival -- so the level is enclosed
    # inside its first second rather than opening on sky.
    ("sill", [n("glow", arc=3.2, lift=1, form="slab", spread=0,
                deco="lamp", orbs=1),
              n("mossy", arc=3.0, lift=1, spread=1, ceiling=2)]),
    # The green mire at the head of the moat: a long flat jump onto a
    # slime pad standing in dug water, and the bounce off it.
    #
    # **Two nodes, and both written from the terrace floor.** Everything
    # else was tried: the lock is machinery inserted *between* beats and
    # it puts the body back down here, so a drop written in the beat
    # before is a drop that is not there when the pad is landed on; and a
    # beat short of budget is truncated, so a third node is a node that
    # goes missing. The 4.9 m arrival is the load-bearing number -- a
    # bounce can never out-reach the fall that fed it, and gaining a block
    # off the pad needs 7.5 m/s of launch, which needs a four-metre
    # arrival to supply it.
    ("mire", [n("mossy", arc=3.0, lift=2, spread=1),
              n("slime", arc=4.4, lift=1, spread=0, moat=True,
                pedestal_style="podzol", orbs=1),
              n("mossy", arc=3.6, lift=2, kind="bounce", spread=1,
                orbs=3)]),
    # The gate tower: one step to the foot of the pier and a ladder four
    # blocks up its face. The pier is a solid stack and that is what the
    # ladder hangs on -- ``pedestal=False``, which is how the rest of the
    # roster writes a climb, leaves it nothing, and "no anchor face" was
    # 85% of every refusal this beat had.
    ("wallhead", [n("mossy", arc=3.2, lift=1, hug=2.2, spread=1),
                  n("oak", arc=2.4, step_y=4, kind="climb",
                    climb_style="ladder", hug=1.6, spread=0,
                    pedestal_style="cobble", orbs=2)]),
    # The moat crossing, and the level's descent: a long jump down off the
    # wall-head onto a cobble standing in dug water, and a second under a
    # lintel so the crossing has to stay flat.
    #
    # The tunnel is on the *second* node and not on ``postern``, which is
    # where it started: a shell only fills the frame on the beats that
    # actually play, and this level lays about four authored landings a
    # run -- ``causeway`` comes out 13 of 13 and ``postern`` 1 of 1.
    ("causeway", [n("cobble", arc=4.6, lift=2, spread=0, moat=True),
                  n("cobble", arc=3.4, lift=2, spread=0, moat=True,
                    ceiling=2, orbs=1)]),
    # Out through the postern -- a short lamplit tunnel, two metres of it.
    ("postern", [n("cobble", arc=3.2, lift=3, spread=0, deco="lamp"),
                 n("cobble", arc=3.3, lift=2, spread=1, orbs=1)]),
], filler=[
    # The character, because the filler is what a long terrace actually
    # plays: the bank of the moat. An oak stump standing in the water, a
    # stride of the gravel path, and back up onto the mossy verge.
    #
    # Everything here stands a block or two off the terrace on purpose.
    # Measured across two configurations of this level: with a third of
    # the landings on plinths the frame was 63% empty sky, and with two
    # thirds of them it was 46% -- a pedestal is a column of masonry in
    # the near ground, and the near ground is what the reference's frames
    # are full of and ours are not.
    ("verge", [n("oak", arc=4.2, lift=2, spread=0, moat=True),
               n("gravel", arc=3.4, lift=1, spread=1, ceiling=2, orbs=1),
               n("mossy", arc=3.3, lift=2, spread=1)]),
])
