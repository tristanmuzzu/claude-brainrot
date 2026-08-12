"""Level 33: THE GATE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The gate. An obsidian arch across the corridor, one last leap under
# it, and the meadow again a hundred and eighty blocks higher. Short
# and calm: a threshold, not a test, and the one place the loop shows.
LEVEL = Level("THE GATE", "end", rise=4, gap=3.0, exit="stair",
              band=11.0, shelf=5.0, landmark="totem", rock="purpur", accent="obsidian",
              step=("obsidian", "hop"), beats=[
    ("approach", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                  n("rock", arc=3.4, lift=1, spread=1)]),
    ("arch", [n("accent", arc=3.2, lift=2, spread=0, ceiling=3),
              n("accent", arc=3.2, lift=2, spread=0, ceiling=3,
                orbs=2)]),
    ("threshold", [n("rock", arc=4.6, lift=1, spread=1),
                   n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("pylons", [n("accent", arc=3.4, lift=1, spread=1),
                n("rock", arc=3.5, lift=2, spread=0, orbs=1)]),
    ("span", [n("accent", arc=4.6, lift=2, spread=1, orbs=1)]),
], filler=[
    ("court", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
               n("accent", arc=4.4, lift=1, spread=1)]),
], exit_beats=[
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
    n("accent", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
      orbs=1),
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, orbs=1),
    n("rock", arc=2.9, step_y=1, hug=2.6, spread=0),
])
