"""Level 2: WINDMILL REACH.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A working mill on the lip of the tower. Where THE GATEHOUSE is a green
# court behind a gate, this is a groove: a five-cell shelf of farmland in
# a nine-and-a-half-metre band, cliff at your shoulder and the drop
# directly outboard, so there is nothing to walk around. Yellow the whole
# way -- hay, pumpkin, farmland, gravel -- against the mossy green below
# and the grey street above. Out of the flooded silage pit, up the mill's
# own ladder, down off its stage onto the stock trough, and away over the
# field.
#
# Same budget arithmetic as ``l01_gatehouse``: about 59 m of terrace, an
# exit reserve of a landing per block still to gain, and a lock across
# this level's wide breaks. The exit is a ladder for that reason -- a
# staircase reserves six more metres than a ladder does, and six metres
# is two landings of design.
LEVEL = Level("WINDMILL REACH", "farm", rise=4, gap=3.0, exit="ladder",
              band=9.5, shelf=5.0, breaks=4, landmark="windmill",
              ground="farmland", sub="coarse", rock="hay", accent="oak",
              liquid="water", glow="lantern",
              props=("crop", "mcfence", "scarecrow", "grasstuft"),
              candy=("hay", "oak"), step=("hay", "hop"), beats=[
    # The threshold: a lantern set flush in the headland, and everything
    # past it is yellow. The mossy green of the gatehouse stops here.
    ("headland", [n("glow", arc=3.2, lift=1, form="slab", spread=0,
                    deco="lamp", orbs=1),
                  n("hay", arc=3.0, lift=1, spread=1)]),
    # The flooded silage pit: a long flat jump onto the pad standing in
    # dug water -- ``moat`` digs the ground out round it and fills it, so
    # this level's water is in a beat that always plays -- and the bounce
    # off it. Two nodes, both written from the terrace floor: written
    # after the ladder instead, so that the drop off the mill's stage fed
    # the bounce, this beat measured **0% as authored**, because the lock
    # is machinery inserted between beats that puts the body back down
    # here and the fall the bounce needed was not there.
    ("silage", [n("slime", arc=4.9, lift=1, spread=0, moat=True,
                  pedestal_style="coarse", orbs=1),
                n("hay", arc=3.6, lift=2, kind="bounce", spread=1,
                  orbs=3)]),
    # The mill: a step in at its foot and a ladder four blocks up the
    # outside of the tower onto the stage. The pier's own stack is what
    # the ladder hangs on; ``pedestal=False`` leaves it nothing.
    #
    # No ``shell="shaft"`` here, and it was tried: a tube round a ladder
    # is a dark box with the lens inside it, and it took frames mostly
    # filled by a wall from 0% to 16%. Four of eight frames on the climb
    # came back black.
    ("mill", [n("hay", arc=3.2, lift=1, hug=2.2, spread=1),
              n("oak", arc=2.4, step_y=4, kind="climb",
                climb_style="ladder", hug=1.6, spread=0,
                pedestal_style="plaster", orbs=2)]),
    # The stock trough, and the level's descent: a long jump down off the
    # mill's stage onto an oak board standing in water cut into the field,
    # and a second under the sail beam so the crossing has to stay flat.
    #
    # The undercroft is on the *second* node: a shell only fills the frame
    # on the beats that actually play, and ``trough`` comes out 15 of 15
    # where the tail of the script comes out once or not at all.
    ("trough", [n("oak", arc=4.6, lift=2, spread=0, moat=True),
                n("oak", arc=3.4, lift=2, spread=0, moat=True,
                  ceiling=2, shell="tunnel", orbs=1)]),
    # The field itself: up onto a bale, down onto the farmland, over the
    # pumpkin standing in it, onto a hay slab. Four materials underfoot in
    # four landings.
    ("furrow", [n("hay", arc=3.2, lift=3, spread=1),
                n("farmland", arc=4.6, lift=0, form="floor", orbs=1),
                n("pumpkin", arc=3.2, lift=1, spread=0, ceiling=2),
                n("hay", arc=3.5, lift=2, form="slab", spread=0, orbs=1)]),
], filler=[
    # The rank of bales, which is what the terrace plays when it outlasts
    # the script: bale, half-bale, the fence rail between them, and back
    # down. A metronome, but at the reference's three metres rather than
    # at the top of the envelope.
    ("rank", [n("hay", arc=3.4, lift=2, spread=0, ceiling=2, orbs=1),
              n("hay", arc=3.2, lift=3, form="slab", spread=0),
              n("oak", arc=3.0, lift=3, form="fence", spread=0,
                radial=0.9, ceiling=2),
              n("hay", arc=3.5, lift=2, spread=1, orbs=1)]),
])
