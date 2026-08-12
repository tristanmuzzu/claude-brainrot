"""Level 28: THE SEA GATE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The sea gate. A monument hall: prismarine, sea lantern light, water
# slots in the floor, and the gate arch the course passes through at
# the end. Cool, ordered, symmetrical where the mesa was chaos.
LEVEL = Level("THE SEA GATE", "prismarine", rise=5, gap=2.8, exit="stair",
              band=12.0, profile="plaza", landmark="arch",
              step=("darkprismarine", "hop"), beats=[
    ("steps", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
               n("rock", arc=3.4, lift=1, spread=1)]),
    ("hall", [n("rock", arc=3.3, lift=1, hug=3.2, spread=0,
                shell="hall"),
              n("rock", arc=3.4, lift=1, hug=3.2, spread=0,
                shell="hall", orbs=1),
              n("rock", arc=3.3, lift=2, hug=3.2, spread=0,
                shell="hall")]),
    ("slots", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
               n("accent", arc=3.4, lift=1, spread=0, moat=True,
                 orbs=1)]),
    ("court", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("dark", [n("darkprismarine", arc=3.4, lift=1, spread=0,
                radial=1.3),
              n("darkprismarine", arc=3.3, lift=2, spread=0,
                radial=-1.3, orbs=1)]),
    ("gate", [n("rock", arc=3.4, lift=2, spread=0, ceiling=2),
              n("accent", arc=4.6, lift=2, spread=0, orbs=1)]),
])
