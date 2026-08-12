"""Level 22: THE PILLARS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The pillars. Obsidian columns out at the rim with purpur slabs slung
# between them, chorus light, and the whole drop under every arc. The
# most exposed level, left by a bubble ride.
LEVEL = Level("THE PILLARS", "end", rise=6, gap=3.4, exit="bubble",
              band=10.5, shelf=3.5, landmark="totem", step=("purpur", "hop"), beats=[
    ("pillars", [n("accent", arc=3.4, lift=3, spread=0, hug=6.8,
                   pedestal=False),
                 n("accent", arc=3.3, lift=4, spread=0, hug=8.4,
                   pedestal=False, orbs=1),
                 n("accent", arc=3.4, lift=5, spread=0, hug=9.6,
                   pedestal=False)]),
    ("slabs", [n("rock", arc=4.4, lift=4, form="slab", spread=0,
                 hug=5.6, pedestal=False),
               n("rock", arc=4.2, lift=4, form="slab", spread=0,
                 hug=5.2, pedestal=False, orbs=1)]),
    ("void", [n("rock", arc=6.2, lift=1, spread=0, hug=5.0, orbs=2)]),
    ("stone", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("rods", [n("accent", arc=3.4, lift=1, hug=5.6, spread=0,
                pedestal=False),
              n("accent", arc=3.5, lift=2, hug=6.0, spread=0,
                pedestal=False, orbs=1)]),
], filler=[
    ("shards", [n("accent", arc=3.6, lift=1, spread=0, hug=5.4,
                  pedestal=False, orbs=1),
                n("rock", arc=4.4, lift=1, spread=0, hug=5.8,
                  pedestal=False)]),
])
