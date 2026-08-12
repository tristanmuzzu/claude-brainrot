"""Level 31: ECHO SHAFT.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Echo shaft. The dark vertical: a sculk well climbed from inside,
# amethyst light partway, the hardest one-cell landings in the tower
# at the top. Eight blocks gained in near-silence.
LEVEL = Level("ECHO SHAFT", "deepdark", rise=8, gap=2.6, exit="ladder",
              band=8.0, profile="plaza", landmark="cluster", rock="deepslate",
              accent="sculk", step=("sculk", "hop"), beats=[
    ("lip", [n("rock", arc=3.4, lift=1, hug=2.8, spread=1, orbs=1)]),
    ("well", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
              n("oak", arc=2.4, step_y=4, kind="climb",
                climb_style="ladder", hug=2.0, pedestal=False, spread=0,
                shell="shaft", orbs=2)]),
    ("gallery", [n("accent", arc=3.4, lift=5, spread=0, hug=3.2,
                   pedestal=False),
                 n("accent", arc=3.3, lift=5, spread=0, hug=4.0,
                   pedestal=False, orbs=1)]),
    ("reach", [n("rock", arc=4.7, lift=5, spread=0, pedestal=False),
               n("rock", arc=4.6, lift=5, spread=0, pedestal=False,
                 orbs=1)]),
    ("thread", [n("accent", arc=3.0, lift=6, spread=0, pedestal=False,
                  radial=1.6),
                n("accent", arc=3.4, lift=6, spread=0, pedestal=False,
                  radial=-1.6, orbs=1)]),
], filler=[
    ("dark", [n("rock", arc=4.5, lift=5, spread=0, pedestal=False,
                orbs=1),
              n("accent", arc=4.4, lift=5, spread=0, pedestal=False)]),
])
