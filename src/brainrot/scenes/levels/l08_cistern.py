"""Level 8: THE CISTERN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A flooded cave. Calcite stones barely above the water, dripstone
# teeth low enough to lid the jumps, and the way out is a bubble
# column ridden up a stone well.
LEVEL = Level("THE CISTERN", "dripstone", rise=6, gap=2.8, exit="bubble",
              band=11.0, profile="plaza", step=("calcite", "hop"), beats=[
    ("stones", [n("accent", arc=3.4, lift=1, spread=0, moat=True),
                n("accent", arc=3.5, lift=1, spread=0, moat=True,
                  orbs=1),
                n("accent", arc=3.4, lift=1, spread=0, moat=True)]),
    ("grotto", [n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                  shell="cave"),
                n("rock", arc=3.4, lift=1, hug=3.0, spread=0,
                  shell="cave", orbs=1)]),
    ("teeth", [n("rock", arc=3.4, lift=2, spread=0, ceiling=2),
               n("rock", arc=3.3, lift=2, spread=0, ceiling=2, orbs=1)]),
    ("pool", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("shelf", [n("rock", arc=3.5, lift=1, hug=2.8, spread=1),
               n("accent", arc=3.4, lift=2, hug=2.8, spread=0,
                 orbs=1)]),
    ("basin", [n("accent", arc=4.6, lift=1, spread=0, moat=True,
                 orbs=1)]),
], exit_beats=[
    n("rock", arc=2.8, lift=1, hug=2.2, spread=1),
    n("prismarine", arc=2.4, step_y=7, kind="bubble",
      climb_style="water", hug=2.0, pedestal=False, spread=0, orbs=2),
    n("accent", arc=3.0, step_y=1, hug=2.8, spread=0),
])
