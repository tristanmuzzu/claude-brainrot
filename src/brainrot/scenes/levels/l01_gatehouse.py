"""Level 1: THE GATEHOUSE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The gentle open. A garden path between hedges, a pond crossed on oak
# rounds, and the tower's first one-cell landings kept mild. The arch at
# the end frames the run ahead.
LEVEL = Level("THE GATEHOUSE", "plains", rise=5, gap=2.8, exit="stair",
              band=11.0, shelf=5.0, landmark="arch", step=("oak", "hop"), beats=[
    ("lawn", [n("ground", arc=4.6, lift=0, form="floor", orbs=1),
              n("rock", arc=3.4, lift=1, spread=1)]),
    ("hedge", [n("accent", arc=3.2, lift=2, spread=0, radial=1.2),
               n("accent", arc=3.3, lift=2, spread=0, radial=-1.2,
                 orbs=1)]),
    ("pond", [n("oak", arc=3.5, lift=1, spread=0, moat=True),
              n("oak", arc=3.4, lift=1, spread=0, moat=True, orbs=1)]),
    ("bench", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("pickets", [n("rock", arc=3.4, lift=1, spread=1),
                 n("oak", arc=3.0, lift=1, form="fence", spread=0,
                   radial=1.2),
                 n("oak", arc=3.0, lift=1, form="fence", spread=0,
                   radial=-1.2, orbs=1),
                 n("rock", arc=3.2, lift=2, spread=0)]),
    ("gate", [n("accent", arc=3.3, lift=3, spread=0, ceiling=2),
              n("rock", arc=4.6, lift=2, spread=1, orbs=1)]),
])
