"""Level 7: CANOPY WALK.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A green gallery under a strangler fig: a mossy shelf pressed against the
# cliff with the drop hard outboard, roots to hop, a fallen log to cross at
# a run, standing water between them, and a sump to fall into and bounce out
# of. The fig itself is the landmark and the course runs through it.
#
# Three numbers here are load-bearing and none of them is a taste decision.
#
# ``band`` is 7.5. The core wall you stand against belongs to the level
# *three below* -- THE TIMBERWORKS, band 7.5 -- and ``Cone.core_r`` leans it
# out about a block further as it rises. At the old band of 11.5 the whole
# five-cell shelf sat inboard of that face: measured, 65% of the cell the
# body stands on was ``conerib`` and only 35% was this level's own moss,
# which is why a jungle came back looking like a grey cobble plate. The same
# arithmetic bit the old ``hug=2.0`` nodes -- a hug is measured from
# ``out - band``, so at band 11.5 anything under 5.1 was asking to stand
# inside rock, and the vine beat placed 57% of the time.
#
# ``breaks=0`` is a budget decision. The lock across a level's wide break is
# four landings and fifteen metres of arc, and this level has a gated tree
# taking fifteen more -- between them they left ten metres of an eighty-metre
# terrace for the design, and the level came out 72% machinery. Without the
# break a walker still covers only about a quarter of it and still cannot get
# down it end to end, because a five-cell shelf with the drop hard outboard
# and a third of the landings floating is unwalkable on width alone, which is
# how the real map does it (RESEARCH.md 8, "width and hazard, not gaps").
#
# **Nothing here stands higher than lift 3**, and that is the tree's fault in
# the good sense: ``_lm_g_tree`` hangs its canopy at five and six blocks over
# the terrace, so a body at lift 4 has its eyes at 5.6 and is standing *in*
# the leaves. The first rebuild of this level climbed to 4 and a whole row of
# the contact sheet came back as solid green.
#
# And the exit is a ``ladder`` rather than the ``vine`` a jungle obviously
# wants, for the same reason seen from the other side: a climb puts the
# camera *on* the column, so whatever the soft cells are drawn in fills the
# lens for the second and a half of the ride. Six frames of leaf-green plate
# read as being inside a bush; the ladder's brown lattice reads as a climb
# and lets the level below show through it. Judged off the sheet, not off a
# number -- ``lens jammed`` is 0.3% either way.
LEVEL = Level("CANOPY WALK", "jungle", rise=6, gap=3.0, exit="ladder",
              band=7.5, shelf=5.0, breaks=0, landmark="tree",
              ground="moss", sub="podzol", rock="junglelog",
              accent="jungleleaf", liquid="water", glow="lantern",
              props=("bamboo", "vinehang", "grasstuft", "flower", "mcfence"),
              sky=(116, 178, 126), dark=0.30,
              candy=("jungleleaf", "moss", "bamboo"),
              step=("junglelog", "hop"), beats=[
    # The threshold. A lantern set flush in the floor on a rise, then a sill
    # crossed on foot -- the reference signposts where a level *begins* and
    # the palette changes completely at that block.
    ("sill", [n("glow", arc=3.0, lift=1, hug=2.8, spread=1, ceiling=3,
                orbs=1),
              n("mossy", arc=2.2, lift=1, hug=2.8, kind="walk", spread=0)]),
    # Up the buttress roots to the lip of the hollow, under the boughs. The
    # hugs keep the body in the groove: cliff a couple of metres off the
    # left shoulder, drop off the right, leaves overhead. Left to itself the
    # course is pulled out to the shelf edge, and a contact sheet of that is
    # two thirds open sea.
    ("buttress", [n("junglelog", arc=3.4, lift=2, hug=2.6, spread=1,
                    ceiling=3),
                  n("junglelog", arc=3.4, lift=3, hug=3.0, spread=1,
                    ceiling=3),
                  n("coarse", arc=3.4, lift=3, hug=2.6, spread=1, moat=True,
                    ceiling=3, orbs=1)]),
    # The sump: two blocks down onto slime lying in the standing water at the
    # bottom of the hollow, and back out. The drop is the level's descent and
    # the bounce pad's fuel at once -- a bounce is thrown by the speed it
    # arrived with and cannot reach past the fall that fed it.
    ("sump", [n("slime", arc=4.8, lift=1, hug=2.6, spread=0,
                pedestal_style="podzol", moat=True),
              n("jungleleaf", arc=3.4, lift=2, hug=2.6, kind="bounce",
                spread=1, orbs=3),
              n("junglelog", arc=2.2, lift=2, hug=2.6, kind="walk",
                spread=0, orbs=1)]),
    # There is no vine beat here and there was, twice. A climb has to hang on
    # something: the anchor test wants solid rock within a cell of the column
    # at its *middle* and its top, and on a column shorter than four blocks
    # that middle index lands on the landing itself rather than on the stack
    # below it. Instrumented over eight runs, 674 of 819 candidate columns
    # were refused for "no anchor" and the beat placed 57% of the time. The
    # climb is this level's *exit* instead, which is where the reference puts
    # its ladders anyway.
    ("hollow", [n("moss", arc=3.6, lift=1, hug=2.8, spread=1, moat=True),
                n("mossy", arc=3.4, lift=1, hug=3.4, spread=1, ceiling=3,
                  orbs=1)]),
], filler=[
    # The character of the place, because the filler is what actually
    # repeats: a root you hop, a fallen log you cross at a run, and a mossy
    # stone standing in the water under the boughs.
    ("understory", [n("junglelog", arc=3.6, lift=2, hug=2.8, spread=1,
                      orbs=1),
                    n("mossy", arc=2.2, lift=2, hug=2.8, kind="walk",
                      spread=0),
                    n("moss", arc=3.4, lift=1, hug=3.0, spread=1, moat=True,
                      ceiling=3)]),
])
