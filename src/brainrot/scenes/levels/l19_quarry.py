"""Level 19: THE QUARRY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The undercut. The course leaves the shelf and steps DOWN the outside
# of the tower -- jutting sandstone benches below the rim with the sea
# under them -- then climbs back over the crane. The tower's one
# descent, and the longest jumps in it are the drops.
LEVEL = Level("THE QUARRY", "desert", rise=4, gap=3.0, exit="stair",
              band=9.5, shelf=3.5, landmark="crane", rock="chiselled", accent="sandstone",
              step=("chiselled", "hop"), beats=[
    ("brink", [n("rock", arc=3.6, lift=1, spread=1, orbs=1)]),
    ("undercut", [n("rock", arc=4.4, step_y=-2, hug=6.8,
                    pedestal=False, spread=0, orbs=1),
                  n("rock", arc=4.6, step_y=-2, hug=7.0,
                    pedestal=False, spread=0, orbs=1),
                  n("accent", arc=4.4, step_y=-1, hug=6.8,
                    pedestal=False, spread=0)]),
    ("benches", [n("accent", arc=3.2, step_y=1, hug=6.6,
                   pedestal=False, spread=0, orbs=1),
                 n("accent", arc=3.1, step_y=1, hug=6.6,
                   pedestal=False, spread=0),
                 n("rock", arc=3.2, step_y=1, hug=6.2,
                   pedestal=False, spread=0, orbs=1),
                 n("rock", arc=3.1, step_y=1, hug=6.0,
                   pedestal=False, spread=0),
                 n("rock", arc=3.2, step_y=1, hug=5.8,
                   pedestal=False, spread=0, orbs=1)]),
    ("rim", [n("rock", arc=3.4, lift=1, spread=1, orbs=1)]),
    ("floor", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("blocks", [n("rock", arc=3.4, lift=1, spread=1),
                n("accent", arc=3.4, lift=2, spread=0, orbs=1)]),
], filler=[
    ("blocks", [n("rock", arc=3.4, lift=1, spread=1, orbs=1),
                n("accent", arc=4.4, lift=1, spread=1)]),
], exit_beats=[
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
    n("accent", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
      orbs=1),
    n("oak", arc=2.9, step_y=1, form="fence", hug=2.4, spread=0,
      pedestal=False),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("rock", arc=2.9, step_y=1, hug=2.6, spread=0),
])
