"""Level 12: REEF GARDEN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Colour after the dark: a reef garden on the shelf, coral heads as
# the parkour, sea lanterns in the water, and a water channel crossed
# twice. The palette does the work here and the jumps stay honest.
LEVEL = Level("REEF GARDEN", "coral", rise=5, gap=3.0, exit="stair",
              band=11.5, profile="channel", step=("coral_red", "hop"), beats=[
    ("shallows", [n("coral_pink", arc=3.4, lift=1, spread=0, moat=True),
                  n("coral_blue", arc=3.5, lift=1, spread=0, moat=True,
                    orbs=1)]),
    ("heads", [n("coral_red", arc=3.4, lift=2, spread=0),
               n("coral_blue", arc=3.3, lift=3, spread=0, orbs=1),
               n("coral_pink", arc=3.4, lift=3, spread=0, radial=1.3)]),
    ("sand", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("lanterns", [n("sealantern", arc=3.5, lift=1, spread=0, moat=True),
                  n("sealantern", arc=3.4, lift=1, spread=0, moat=True,
                    orbs=1)]),
    ("fans", [n("coral_red", arc=3.4, lift=2, spread=0, radial=-1.3),
              n("coral_pink", arc=4.6, lift=2, spread=0, orbs=1)]),
    ("brain", [n("coral_blue", arc=3.4, lift=1, spread=0),
               n("coral_red", arc=3.5, lift=2, spread=0, orbs=1)]),
])
