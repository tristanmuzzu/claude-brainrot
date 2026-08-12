"""Level 17: THE WEIR.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The weir. A water channel runs the length of the level and the
# course lives in it: stepping stones barely above the surface, the
# mill wheel turning at the bank, and one long leap onto the far side.
LEVEL = Level("THE WEIR", "plains", rise=5, gap=3.0, exit="stair",
              band=12.0, profile="channel", landmark="watchtower", rock="cobble",
              accent="oak", step=("cobble", "hop"), beats=[
    ("ford", [n("cobble", arc=3.0, lift=1, spread=0, moat=True),
              n("cobble", arc=3.0, lift=1, spread=0, moat=True, orbs=1),
              n("cobble", arc=3.1, lift=1, spread=0, moat=True),
              n("cobble", arc=3.0, lift=1, spread=0, moat=True,
                orbs=1)]),
    ("bank", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
              n("cobble", arc=3.2, lift=1, spread=0)]),
    ("leap", [n("oak", arc=4.8, lift=1, spread=0, moat=True, orbs=2)]),
    ("mill", [n("oak", arc=3.4, lift=2, spread=1, ceiling=1),
              n("cobble", arc=3.5, lift=3, spread=0, orbs=1)]),
    ("sluice", [n("cobble", arc=3.6, lift=2, spread=1),
                n("cobble", arc=3.5, lift=2, spread=0, moat=True,
                  orbs=1)]),
    ("race", [n("oak", arc=4.9, lift=2, spread=0, moat=True, orbs=1)]),
])
