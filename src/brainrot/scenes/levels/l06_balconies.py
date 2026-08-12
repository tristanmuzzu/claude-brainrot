"""Level 6: THE BALCONIES.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Back into daylight hard: narrow terracotta balconies on the cliff,
# the biggest drops so far under every jump, and one slab bridge out
# over the rim. Uneven rhythm on purpose -- up, up, then one long fall.
LEVEL = Level("THE BALCONIES", "mesa", rise=7, gap=3.4, exit="stair",
              band=9.0, shelf=4.5, landmark="hoodoo", step=("terra_white", "hop"), beats=[
    ("ledges", [n("rock", arc=3.4, lift=2, spread=0),
                n("accent", arc=3.3, lift=3, spread=0, orbs=1),
                n("rock", arc=3.4, lift=4, spread=0)]),
    ("plunge", [n("ground", arc=6.0, lift=0, form="floor", orbs=2)]),
    ("spur", [n("rock", arc=3.4, lift=1, hug=7.5, pedestal=False,
                spread=0),
              n("accent", arc=3.4, lift=1, form="slab", hug=9.5,
                pedestal=False, spread=0, orbs=1),
              n("accent", arc=3.2, lift=2, form="slab", hug=11.0,
                pedestal=False, spread=0, orbs=1),
              n("accent", arc=3.4, lift=1, form="slab", hug=8.5,
                pedestal=False, spread=0)]),
    ("landing", [n("rock", arc=4.2, lift=1, spread=1, orbs=1)]),
    ("spurs", [n("rock", arc=3.4, lift=2, spread=0, radial=1.4),
               n("accent", arc=3.3, lift=3, spread=0, radial=-1.4,
                 orbs=1)]),
    ("brink", [n("rock", arc=4.8, lift=3, spread=0, hug=5.8,
                 pedestal=False, orbs=1)]),
])
