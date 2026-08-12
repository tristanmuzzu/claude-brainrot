"""Level 26: THE GROVE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The warped grove. Teal nylium, shroomlight crowns, and a bubble lift
# in the middle of the level that carries the body to an upper storey
# of caps before the drop back down.
LEVEL = Level("THE GROVE", "warped", rise=6, gap=3.0, exit="bubble",
              band=11.0, shelf=5.0, step=("warped", "hop"), beats=[
    ("nylium", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                n("rock", arc=3.5, lift=2, spread=1)]),
    ("lift", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
              n("prismarine", arc=2.4, step_y=4, kind="bubble",
                climb_style="water", hug=2.0, pedestal=False, spread=0,
                orbs=2)]),
    ("crowns", [n("accent", arc=4.8, lift=6, form="wide", spread=0,
                  pedestal=False),
                n("accent", arc=5.0, lift=6, form="wide", spread=0,
                  pedestal=False, orbs=1)]),
    ("descent", [n("ground", arc=6.8, lift=0, form="floor", orbs=2)]),
    ("fungus", [n("rock", arc=3.4, lift=1, spread=1),
                n("accent", arc=4.6, lift=1, spread=1, orbs=1)]),
], filler=[
    ("thicket", [n("rock", arc=3.4, lift=1, spread=1, orbs=1),
                 n("accent", arc=3.6, lift=1, spread=1)]),
])
