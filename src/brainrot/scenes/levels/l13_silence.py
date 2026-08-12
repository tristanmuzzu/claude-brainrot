"""Level 13: THE SILENCE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The first dark-floating level: one-cell sculk landings over the void
# side of the shelf, amethyst the only light. Quiet, slow to look at,
# genuinely hard -- every landing one cell, every gap at reach.
LEVEL = Level("THE SILENCE", "deepdark", rise=6, gap=3.4, exit="ladder",
              band=8.0, shelf=3.5, landmark="cluster", step=("deepslate", "hop"), beats=[
    ("hush", [n("rock", arc=4.6, lift=2, spread=0, pedestal=False),
              n("rock", arc=4.6, lift=2, spread=0, pedestal=False,
                orbs=1)]),
    ("thread", [n("accent", arc=3.0, lift=3, spread=0, pedestal=False,
                  radial=1.6),
                n("accent", arc=3.4, lift=3, spread=0, pedestal=False,
                  radial=-1.6, orbs=1)]),
    ("gulf", [n("rock", arc=4.4, lift=1, spread=0, pedestal=False,
                hug=8.0, orbs=1),
              n("rock", arc=4.4, lift=1, spread=0, pedestal=False,
                hug=9.6, orbs=1)]),
    ("shelf", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("veins", [n("accent", arc=3.4, lift=1, spread=0, pedestal=False),
               n("rock", arc=3.3, lift=2, spread=0, pedestal=False,
                 orbs=1)]),
], filler=[
    ("dark", [n("rock", arc=4.6, lift=2, spread=0, pedestal=False,
                orbs=1),
              n("accent", arc=4.4, lift=2, spread=0, pedestal=False)]),
])
