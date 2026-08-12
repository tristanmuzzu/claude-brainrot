"""Level 29: THE CORNICE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The cornice. A snow ridge at the rim with icicles under it, wind in
# the fog, and halfway along -- a lit cabin crossed *inside*, three
# seconds of warm lamplight between two cold exposures.
LEVEL = Level("THE CORNICE", "snow", rise=5, gap=3.0, exit="stair",
              band=8.5, shelf=4.0, landmark="cabin", step=("spruce", "hop"), beats=[
    ("ridge", [n("rock", arc=3.6, lift=1, spread=0, hug=5.8, orbs=1),
               n("rock", arc=3.5, lift=2, spread=0, hug=6.0),
               n("accent", arc=3.4, lift=2, spread=0, hug=5.6,
                 orbs=1)]),
    ("cabin", [n("spruce", arc=3.3, lift=1, hug=2.8, spread=0,
                 shell="tunnel"),
               n("spruce", arc=3.4, lift=1, hug=2.8, spread=0,
                 shell="tunnel", orbs=1)]),
    ("drift", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("cornice", [n("rock", arc=3.4, lift=1, spread=0, hug=7.4,
                   pedestal=False),
                 n("rock", arc=3.3, lift=2, spread=0, hug=8.8,
                   pedestal=False, orbs=1)]),
    ("posts", [n("spruce", arc=3.0, lift=2, form="fence", spread=0,
                 radial=1.2),
               n("spruce", arc=3.0, lift=2, form="fence", spread=0,
                 radial=-1.2, orbs=1)]),
])
