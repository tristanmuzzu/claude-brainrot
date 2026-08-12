"""Level 25: PUMPKIN ROWS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Dusk on the pumpkin rows. Jack-o-lantern glow, hay underfoot, the
# scarecrow's cousin standing guard as a lantern post, and the farm
# read the second time round with the lights on.
LEVEL = Level("PUMPKIN ROWS", "farm", rise=4, gap=2.8, exit="stair",
              band=10.5, landmark="scarecrow", glow="glowstone", step=("pumpkin", "hop"),
              beats=[
    ("rows", [n("pumpkin", arc=3.6, lift=1, spread=0, orbs=1),
              n("pumpkin", arc=3.5, lift=1, spread=0),
              n("pumpkin", arc=3.6, lift=1, spread=0, orbs=1)]),
    ("patch", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("wain", [n("oak", arc=3.4, lift=1, spread=1, ceiling=1),
              n("hay", arc=3.3, lift=2, spread=0, orbs=1)]),
    ("lanterns", [n("glowstone", arc=3.5, lift=1, spread=0,
                    radial=1.3),
                  n("pumpkin", arc=3.4, lift=1, spread=0, radial=-1.3,
                    orbs=1)]),
    ("bales", [n("hay", arc=3.4, lift=2, spread=0),
               n("hay", arc=4.6, lift=2, spread=0, orbs=1)]),
])
