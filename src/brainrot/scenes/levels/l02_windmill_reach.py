"""Level 2: WINDMILL REACH.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A farm on a shelf: hay ranks at near-full reach, crop rows underfoot,
# and the windmill standing on its apron. The rhythm is a metronome --
# the same big jump asked four times, which no dice ever ask.
LEVEL = Level("WINDMILL REACH", "farm", rise=4, gap=2.8, exit="stair",
              band=10.0, landmark="windmill", step=("hay", "hop"), beats=[
    ("rank", [n("hay", arc=4.4, lift=1, spread=0, orbs=1),
              n("hay", arc=4.4, lift=1, spread=0),
              n("hay", arc=4.4, lift=1, spread=0, orbs=1),
              n("hay", arc=4.4, lift=1, spread=0)]),
    ("furrow", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("bales", [n("hay", arc=3.4, lift=1, spread=0),
               n("hay", arc=3.3, lift=2, spread=0, orbs=1)]),
    ("cart", [n("oak", arc=4.7, lift=2, spread=1, orbs=1)]),
    ("trough", [n("rock", arc=3.5, lift=1, spread=0, moat=True),
                n("ground", arc=4.4, lift=0, form="floor", orbs=1)]),
    ("stack", [n("hay", arc=3.4, lift=1, spread=0),
               n("hay", arc=3.3, lift=2, spread=0, orbs=1)]),
], filler=[
    ("rank", [n("hay", arc=4.4, lift=1, spread=0, orbs=1),
              n("hay", arc=4.4, lift=1, spread=0)]),
], exit_beats=[
    n("hay", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
    n("hay", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9, orbs=1),
    n("oak", arc=2.9, step_y=1, form="fence", hug=2.4, spread=0,
      pedestal=False),
    n("hay", arc=3.0, step_y=1, hug=2.4, spread=0, radial=-0.9, orbs=1),
    n("hay", arc=2.9, step_y=1, hug=2.6, spread=0),
])
