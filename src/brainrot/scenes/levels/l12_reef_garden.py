"""Level 12: REEF GARDEN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE TIDE SHELF. Straight out of the black foundry into daylight: a
# flooded terrace with a channel of sea running its whole length, sand
# bars standing half a block out of it, a lagoon you fall into, coral
# growing out of the water and a prismarine grotto cut into the cliff.
# It leaves up a bubble column in a well, which is the one way out a
# reef has.
#
# The seam is half the point. Level 11 is black rock, a red sky and
# orange lava pressed against the wall at 2.6; this is pale sand, blue
# water and a bright sky out at 3-5, and the palette changes completely
# at the sea lantern in the first beat. No two adjacent levels share a
# hue.
#
# Half-height sand bars are the shape here. Stairs and slabs are the
# reference's commonest non-cube form by a wide margin, and a slab is
# worth reach as well as looks: two slab steps gain a block across
# seven metres of ground where one hop could only manage 3.10.
LEVEL = Level("REEF GARDEN", "coral", rise=5, gap=2.8, exit="bubble",
              band=12.5, profile="channel", breaks=3, landmark="arch",
              ground="sand", sub="sandstone", rock="prismarine",
              accent="coral_blue", glow="sealantern", liquid="water",
              props=("coralfan", "lilypad", "pebbles", "grasstuft",
                     "flower"),
              step=("darkprismarine", "hop"), beats=[
    # The threshold: a sea lantern flush in the sand with the water dug
    # out round it, and a stride onto the shelf. A ``walk`` is never the
    # first node of a beat -- beats are separated by machinery arriving
    # at its own height and a walk needs its predecessor within 0.55 m.
    ("tideline", [n("glow", arc=3.2, lift=1, hug=4.2, spread=1,
                    deco="lamp", moat=True, orbs=1),
                  n("ground", arc=2.9, lift=1, hug=4.2, kind="walk",
                    spread=0)]),
    # The lagoon, the showpiece, and it is the *second* beat because
    # this is where a beat still gets laid whole. Measured over eight
    # pinned runs: the first two beats lay 2.0 and 3.75 of their
    # landings, and everything from the third on lays 1.2 to 1.75 --
    # the lock and the gate crossing come between beats and the clip
    # eats the tail of whatever is due. A showpiece in beat three is a
    # showpiece nobody sees.
    #
    # Two steps up the coral, a two-block fall onto the sponge, and the
    # throw two blocks back up -- the only move in this engine that
    # gains two. The rise is *inside* the beat: written across a beat
    # boundary the fall is one block about half the time, and a one-
    # block fall is refused as a bounce on every candidate (it arrives
    # at 9.3 m/s against the 10.6 a +2 needs).
    ("lagoon", [n("coral_red", arc=3.5, lift=2, hug=3.6, spread=0),
                n("coral_red", arc=3.5, lift=3, hug=3.6, spread=0),
                n("slime", arc=4.9, lift=1, hug=4.0, form="slime",
                  spread=0, pedestal_style="sand"),
                n("coral_red", arc=3.6, lift=3, hug=4.0, kind="bounce",
                  spread=1, orbs=3)]),
    # The bars: half-height sand standing out of the channel, one of
    # them a stride from the last rather than a jump. Stairs and slabs
    # are the reference's commonest non-cube form by a wide margin and
    # this tower had almost none.
    #
    # Its first landing asks for lift 1 and not lift 2 on purpose: a
    # third-position beat is the one the clip lands on, so its opening
    # landing is placed from wherever the machinery left the body, and
    # the more tolerant height measures the better.
    #
    # Do not "centre" these arcs in their rise's band. It is a good rule
    # on THE CRUCIBLE and it is the wrong one here: lengthening this
    # landing's hop from 4.2 to 5.0 and the grotto's from 4.4 to 3.9 --
    # both toward the middle of their bands -- took this level from 0
    # unchecked placements to 7 and cost four points of fidelity. On a
    # channel level the binding constraint is which lane has ground
    # under it, not how far the jump is.
    ("bars", [n("ground", arc=4.2, lift=1, hug=4.2, spread=1, moat=True),
              n("ground", arc=3.4, lift=1, hug=4.2, form="slab", spread=0,
                moat=True),
              n("ground", arc=2.9, lift=1, hug=4.2, form="slab",
                kind="walk", spread=0, orbs=1),
              n("coral_pink", arc=3.2, lift=2, hug=3.6, form="slab",
                spread=0, moat=True)]),
    # The grotto: a lamplit bay carved into the core wall with a lid
    # over its mouth, walked through. Two metres of pinch, which is what
    # the real map's enclosure actually measures -- and a *script* beat
    # rather than the filler, because the filler loops several times on
    # a terrace this long and five grottoes in one corridor is a tunnel
    # level.
    ("grotto", [n("rock", arc=4.4, lift=1, hug=2.6, spread=1,
                  shell="grotto"),
                n("darkprismarine", arc=2.9, lift=1, hug=2.6,
                  kind="walk", spread=0, orbs=1)]),
], filler=[
    # The character, repeated -- and on a terrace this long the filler
    # is over a third of the level, so it is where the identity has to
    # live. It falls to the sand strip against the cliff (a level goes
    # down as well as up, and the real map does it by falling rather
    # than by jumping), then coral back out of the channel and a stride
    # along the reef.
    #
    # Nothing enclosed, nothing lidded and above all **no moat** in a
    # filler. A moat digs a radius-three disc out of the ground and
    # fills it; asked for again on the next loop of the same corridor it
    # digs away the ground the previous loop's pedestals are standing
    # on, and "pedestal will not stand" was 27,859 refusals and a third
    # of this beat's fidelity.
    #
    # And every landing in it hugs 2.4-2.8, on the sand strip between
    # the channel and the cliff. Out over the channel a pedestal has
    # nothing to stand on -- the cut is two cells of water carved out of
    # the ground -- and the same beat written at hug 3.2-4.6 lost a
    # third of its landings to recoveries that still read as placed.
    #
    # The landing before the walk carries ``spread=0`` for the same
    # class of reason: let it settle a block high and the stride after
    # it is a one-block drop, which a walk refuses, and the rest of the
    # loop goes with it.
    ("fans", [n("ground", arc=4.9, lift=0, hug=2.4, form="floor",
                spread=0, orbs=1),
              n("accent", arc=3.3, lift=1, hug=2.6, spread=0),
              n("darkprismarine", arc=2.9, lift=1, hug=2.6, kind="walk",
                spread=0),
              n("coral_pink", arc=3.2, lift=2, hug=2.8, spread=0,
                orbs=1)]),
], exit_beats=[
    # Out up a bubble column in a prismarine well. Declared as the
    # level's exit as well, so the climb reserve is three landings
    # rather than the staircase's seven -- that one line is worth about
    # fifteen points of designed content on a level this length.
    #
    # It keeps its **pedestal** and asks for no ``hug``, and that is the
    # difference between a bubble column and a silent staircase. The
    # column has to find solid rock beside it at its middle cell and at
    # its top; hugged to the core with no pedestal it is relying on a
    # cliff that leans away, and a climb that cannot anchor is refused
    # and falls through to the generated stair with nothing reporting
    # it. Standing the landing on its own stack gives the column
    # something to hang on for its whole height. **Check the move mix
    # in ``--report`` for the word ``bubble``**: if it is missing, this
    # beat is six steps of staircase.
    n("rock", arc=3.0, lift=1, hug=2.2, spread=2, deco="lamp"),
    n("prismarine", arc=3.0, step_y=5, kind="bubble", spread=0,
      shell="shaft", orbs=2),
])
