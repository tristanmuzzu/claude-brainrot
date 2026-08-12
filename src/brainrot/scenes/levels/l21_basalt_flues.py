"""Level 21: BASALT FLUES.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Basalt flues under a low soffit: blackstone columns packed close,
# every jump under a lid, magma glowing in the gaps. The opposite
# design to the Crucible with the same palette -- tight, not cavern.
LEVEL = Level("BASALT FLUES", "nether", rise=7, gap=2.8, exit="stair",
              band=7.5, shelf=4.5, ground="blackstone", rock="blackstone", accent="magma",
              step=("blackstone", "hop"), beats=[
    ("flues", [n("rock", arc=3.0, lift=2, spread=0, ceiling=2),
               n("rock", arc=3.0, lift=2, spread=0, ceiling=2, orbs=1),
               n("rock", arc=3.1, lift=2, spread=0, ceiling=2)]),
    ("vents", [n("accent", arc=3.4, lift=3, spread=0, moat=True),
               n("accent", arc=3.3, lift=3, spread=0, moat=True,
                 orbs=1)]),
    ("crust", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("stacks", [n("rock", arc=3.2, lift=1, spread=0, radial=1.4,
                  ceiling=1),
                n("rock", arc=3.2, lift=1, spread=0, radial=-1.4,
                  ceiling=1, orbs=1)]),
    ("draught", [n("rock", arc=3.2, lift=2, spread=0, ceiling=2),
                 n("accent", arc=3.4, lift=3, spread=0, moat=True,
                   orbs=1)]),
], filler=[
    ("flues", [n("rock", arc=3.2, lift=2, spread=0, ceiling=2, orbs=1),
               n("rock", arc=3.0, lift=2, spread=0, ceiling=2)]),
    ("vents", [n("accent", arc=3.4, lift=3, spread=0, moat=True),
               n("accent", arc=3.3, lift=3, spread=0, moat=True,
                 orbs=1)]),
], exit_beats=[
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=1),
    n("oak", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=False, spread=0, orbs=2),
])
