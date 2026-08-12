"""Level 24: THE ARCHIVE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The archive. Bookshelf walls, a gallery hall with lanterns, oak
# beams over a reading room, and the ladder out is behind the shelves.
# Warm interior light and not one block of stone parkour.
LEVEL = Level("THE ARCHIVE", "library", rise=6, gap=2.8, exit="ladder",
              band=10.0, profile="plaza", step=("spruce", "hop"), beats=[
    ("lobby", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
               n("oak", arc=3.4, lift=1, spread=1)]),
    ("stacks", [n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                  shell="hall"),
                n("rock", arc=3.4, lift=2, hug=3.0, spread=0,
                  shell="hall", orbs=1),
                n("rock", arc=3.3, lift=2, hug=3.0, spread=0,
                  shell="hall")]),
    ("desks", [n("oak", arc=3.5, lift=1, spread=0, radial=1.3),
               n("oak", arc=3.4, lift=2, spread=0, radial=-1.3,
                 orbs=1)]),
    ("gallery", [n("oak", arc=3.6, lift=2, form="slab", spread=0,
                   hug=3.4, pedestal=False, ceiling=1),
                 n("oak", arc=3.5, lift=3, form="slab", spread=0,
                   hug=4.4, pedestal=False, orbs=1)]),
    ("hearth", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("lectern", [n("rock", arc=3.4, lift=1, spread=0),
                 n("rock", arc=3.3, lift=2, spread=0, orbs=1)]),
], exit_beats=[
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
      orbs=1),
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=1, radial=-0.9),
    n("oak", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=False, spread=0, orbs=2),
])
