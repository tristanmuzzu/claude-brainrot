"""Level 7: CANOPY WALK.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Two storeys of jungle. Logs on the shelf, a vine into the canopy,
# leaf decks at the soffit, then a deliberate long drop back through
# the leaves. The giant tree is the landmark and the level.
LEVEL = Level("CANOPY WALK", "jungle", rise=7, gap=3.0, exit="vine",
              band=11.5, shelf=5.0, landmark="tree", step=("junglelog", "hop"), beats=[
    ("roots", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
               n("rock", arc=3.5, lift=2, spread=1)]),
    ("liana", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
               n("junglelog", arc=2.4, step_y=4, kind="climb",
                 climb_style="vine", hug=2.0, pedestal=False, spread=0,
                 orbs=2)]),
    ("canopy", [n("accent", arc=3.4, lift=6, spread=0, hug=4.6,
                  pedestal=False),
                n("accent", arc=3.5, lift=6, spread=0, hug=5.4,
                  pedestal=False, orbs=1),
                n("accent", arc=3.4, lift=6, spread=0, hug=4.8,
                  pedestal=False)]),
    ("fall", [n("ground", arc=6.4, lift=0, form="floor", orbs=2)]),
    ("logs", [n("rock", arc=3.5, lift=1, spread=1),
              n("rock", arc=4.4, lift=1, spread=1, orbs=1)]),
    ("bough", [n("rock", arc=3.4, lift=2, spread=0),
               n("accent", arc=3.5, lift=3, spread=0, orbs=1)]),
], filler=[
    ("understory", [n("rock", arc=4.2, lift=2, spread=1, orbs=1),
                    n("accent", arc=3.4, lift=2, spread=1)]),
], exit_beats=[
    n("rock", arc=2.8, lift=1, hug=2.2, spread=1),
    n("junglelog", arc=2.4, step_y=7, kind="climb", climb_style="vine",
      hug=2.0, pedestal=False, spread=0, orbs=2),
    n("accent", arc=3.0, step_y=1, hug=2.8, spread=0),
])
