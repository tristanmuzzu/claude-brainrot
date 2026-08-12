"""Level 18: BLUE RUN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Relentless ice at the rim: long slides with nothing inboard or out,
# then the shelf pinches and the last stretch is a blue ice tunnel cut
# into the cliff. The fastest level, and the exit slides too.
LEVEL = Level("BLUE RUN", "ice", rise=6, gap=3.2, exit="stair",
              band=9.0, shelf=4.0, ground="packedice", rock="frost", accent="snow",
              step=("blueice", "slide"), beats=[
    ("run", [n("blueice", arc=4.6, lift=1, kind="slide", form="ice",
               spread=0, hug=4.6, pedestal=False, orbs=1),
             n("blueice", arc=4.8, lift=1, kind="slide", form="ice",
               spread=0, hug=5.4, pedestal=False),
             n("blueice", arc=4.8, lift=1, kind="slide", form="ice",
               spread=0, hug=5.6, pedestal=False, orbs=1)]),
    ("shear", [n("rock", arc=4.4, lift=2, kind="slide", form="ice",
                 spread=0, hug=5.0, pedestal=False, orbs=1)]),
    ("tunnel", [n("blueice", arc=4.2, lift=1, kind="slide", form="ice",
                  spread=0, hug=3.6, shell="tunnel"),
                n("blueice", arc=4.4, lift=1, kind="slide", form="ice",
                  spread=0, hug=2.6, shell="tunnel", orbs=1)]),
    ("out", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("floe", [n("blueice", arc=4.0, lift=1, kind="slide", form="ice",
                spread=0, hug=5.0, pedestal=False, orbs=1)]),
])
