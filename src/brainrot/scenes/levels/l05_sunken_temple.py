"""Level 5: SUNKEN TEMPLE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A sandstone hall with a lava seam down the middle of the floor and
# doorway lids that keep every arc flat. Bright at the openings, dim in
# the middle, and the temple front stands where the course turns.
LEVEL = Level("SUNKEN TEMPLE", "desert", rise=6, gap=3.0, exit="stair",
              band=12.0, profile="plaza", landmark="arch", step=("sandstone", "hop"),
              liquid="lava", beats=[
    ("porch", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
               n("rock", arc=3.4, lift=1, spread=1)]),
    ("nave", [n("rock", arc=3.3, lift=1, hug=3.2, spread=0,
                shell="hall"),
              n("rock", arc=3.4, lift=1, hug=3.2, spread=0,
                shell="hall", orbs=1),
              n("rock", arc=3.3, lift=2, hug=3.2, spread=0,
                shell="hall")]),
    ("seam", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
              n("accent", arc=3.4, lift=1, spread=0, moat=True,
                orbs=1)]),
    ("lintels", [n("rock", arc=3.4, lift=2, spread=0, ceiling=2),
                 n("rock", arc=3.3, lift=2, spread=0, ceiling=2,
                   orbs=1)]),
    ("court", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("altar", [n("chiselled", arc=3.4, lift=1, spread=0),
               n("chiselled", arc=3.3, lift=2, spread=0, orbs=1)]),
], exit_beats=[
    n("chiselled", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      deco="lamp"),
    n("chiselled", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("chiselled", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("chiselled", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("chiselled", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("chiselled", arc=3.0, step_y=1, hug=2.4, spread=0, deco="lamp"),
    n("chiselled", arc=2.9, step_y=1, hug=2.6, spread=0),
])
