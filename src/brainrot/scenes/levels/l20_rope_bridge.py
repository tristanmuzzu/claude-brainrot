"""Level 20: ROPE BRIDGE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# One plank wide, two hundred blocks of air. The rope bridge runs out
# at the rim on posts, sags a block in the middle, and comes back.
# Nothing here is hard to land; all of it is hard to watch.
LEVEL = Level("ROPE BRIDGE", "jungle", rise=5, gap=3.4, exit="vine",
              band=8.5, shelf=4.0, rock="junglelog", accent="jungleleaf",
              step=("oak", "hop"), beats=[
    ("post", [n("rock", arc=3.4, lift=2, spread=0, hug=6.0,
                pedestal=False, orbs=1)]),
    ("planks", [n("oak", arc=3.2, lift=2, form="trapdoor", spread=0,
                  hug=7.5, pedestal=False),
                n("oak", arc=3.2, lift=1, spread=0, hug=9.0,
                  pedestal=False, orbs=1),
                n("oak", arc=3.2, lift=2, form="trapdoor", spread=0,
                  hug=10.5, pedestal=False),
                n("oak", arc=3.3, lift=2, spread=0, hug=9.0,
                  pedestal=False, orbs=1)]),
    ("span", [n("oak", arc=4.6, lift=2, spread=0, hug=7.5,
                pedestal=False, orbs=2)]),
    ("land", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("guys", [n("rock", arc=3.4, lift=1, hug=6.0, spread=0,
                pedestal=False),
              n("oak", arc=3.4, lift=2, hug=6.4, spread=0,
                pedestal=False, orbs=1)]),
], filler=[
    ("cable", [n("oak", arc=3.4, lift=1, spread=0, hug=6.2,
                 pedestal=False, orbs=1),
               n("oak", arc=3.4, lift=1, spread=0, hug=6.6,
                 pedestal=False)]),
])
