"""Level 27: DUST DEVILS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Dust devils. Hoodoo country: thin terracotta spires with capstones,
# the biggest single drops in the tower, and a rhythm that never
# settles -- three up, one long fall, two up, gone.
LEVEL = Level("DUST DEVILS", "mesa", rise=7, gap=3.6, exit="stair",
              band=12.5, shelf=3.5, landmark="hoodoo", step=("terra_white", "hop"), beats=[
    ("spires", [n("rock", arc=3.4, lift=3, spread=0,
                  pedestal_style="terra_orange"),
                n("accent", arc=3.3, lift=4, spread=0,
                  pedestal_style="terra_orange", orbs=1),
                n("rock", arc=3.4, lift=5, spread=0,
                  pedestal_style="terra_orange")]),
    ("fall", [n("ground", arc=6.2, lift=0, form="floor", orbs=2)]),
    ("caps", [n("accent", arc=3.4, lift=1, spread=0, radial=1.4),
              n("rock", arc=3.3, lift=2, spread=0, radial=-1.4,
                orbs=1)]),
    ("mesa", [n("accent", arc=4.2, lift=1, spread=0, hug=7.0,
                pedestal=False, orbs=1),
              n("accent", arc=3.6, lift=1, spread=0, hug=8.6,
                pedestal=False, orbs=1)]),
    ("devils", [n("rock", arc=3.4, lift=2, spread=0,
                  pedestal_style="terra_orange"),
                n("accent", arc=3.5, lift=3, spread=0,
                  pedestal_style="terra_orange", orbs=1)]),
])
