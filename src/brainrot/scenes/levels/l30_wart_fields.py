"""Level 30: WART FIELDS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The wart fields. Vivid crimson nylium, wart blocks in ranks, giant
# fungus trunks against the wall, and the exit is a ladder up one of
# them. The loudest colour in the tower, kept brief.
LEVEL = Level("WART FIELDS", "crimson", rise=6, gap=3.0, exit="ladder",
              band=9.5, shelf=4.5, step=("crimson", "hop"), beats=[
    ("fields", [n("accent", arc=3.5, lift=1, spread=0, orbs=1),
                n("accent", arc=3.4, lift=1, spread=0),
                n("accent", arc=3.5, lift=2, spread=0, orbs=1)]),
    ("trunks", [n("rock", arc=3.4, lift=2, spread=0, radial=1.4),
                n("rock", arc=3.3, lift=3, spread=0, radial=-1.4,
                  orbs=1)]),
    ("nylium", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("canes", [n("rock", arc=3.4, lift=1, spread=0, ceiling=2),
               n("rock", arc=3.3, lift=2, spread=0, ceiling=2,
                 orbs=1)]),
    ("glow", [n("shroomlight", arc=3.5, lift=2, spread=0),
              n("accent", arc=4.6, lift=2, spread=0, orbs=1)]),
])
