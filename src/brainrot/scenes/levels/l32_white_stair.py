"""Level 32: THE WHITE STAIR.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The white stair. A quartz colonnade with long views: pale galleries,
# gold trims, diorite underfoot. Deliberately elegant and mild -- the
# breath before the gate, and the light after the dark shaft.
LEVEL = Level("THE WHITE STAIR", "quartz", rise=5, gap=2.8, exit="stair",
              band=13.0, profile="plaza", landmark="arch", step=("diorite", "hop"),
              beats=[
    ("gallery", [n("ground", arc=4.6, lift=0, form="floor", orbs=1),
                 n("rock", arc=3.4, lift=1, spread=1)]),
    ("colonnade", [n("rock", arc=3.4, lift=2, spread=0, radial=1.3),
                   n("rock", arc=3.3, lift=2, spread=0, radial=-1.3,
                     orbs=1),
                   n("rock", arc=3.4, lift=2, spread=0, radial=1.3)]),
    ("trim", [n("accent", arc=3.5, lift=3, spread=0),
              n("accent", arc=3.4, lift=3, form="slab", spread=0,
                orbs=1)]),
    ("terrace", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("plinths", [n("rock", arc=3.4, lift=1, spread=0),
                 n("sub", arc=3.5, lift=2, spread=0, orbs=1)]),
], exit_beats=[
    n("quartz", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      deco="lamp"),
    n("diorite", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("quartz", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("diorite", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("quartz", arc=2.9, step_y=1, hug=2.4, spread=0, deco="lamp"),
    n("quartz", arc=3.0, step_y=1, hug=2.6, spread=0, orbs=1),
])
