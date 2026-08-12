"""Level 9: GLACIER SHELF.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Ice in the open. Slides at reach with the drop beside them, and the
# crevasse: a stretch where the shelf itself is missing and the course
# floats over the blue. Fast and bright after the cave.
LEVEL = Level("GLACIER SHELF", "ice", rise=4, gap=3.2, exit="stair",
              band=10.5, shelf=4.5, step=("packedice", "slide"), beats=[
    ("sheet", [n("rock", arc=5.0, lift=1, kind="slide", form="ice",
                 spread=0, orbs=1),
               n("rock", arc=5.2, lift=1, kind="slide", form="ice",
                 spread=0)]),
    ("crevasse", [n("blueice", arc=4.8, lift=2, kind="slide", form="ice",
                    hug=7.2, pedestal=False, spread=0, orbs=1),
                  n("blueice", arc=4.6, lift=2, kind="slide", form="ice",
                    hug=8.8, pedestal=False, spread=0, orbs=1)]),
    ("snow", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("floes", [n("accent", arc=4.6, lift=1, kind="slide", form="ice",
                 spread=0, radial=1.3),
               n("accent", arc=4.6, lift=1, kind="slide", form="ice",
                 spread=0, radial=-1.3, orbs=1)]),
    ("serac", [n("rock", arc=3.4, lift=2, spread=0),
               n("rock", arc=4.8, lift=2, kind="slide", form="ice",
                 spread=0, orbs=1)]),
], exit_beats=[
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, confine=True),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, radial=0.9, orbs=1),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, radial=-0.9),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, orbs=1),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.8, spread=0),
])
