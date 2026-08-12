"""Level 15: WOOLWORKS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The loom. Wool stripes on the wall, wool checks floating over the
# drop, a slime pad in the middle. Short, loud, and gone -- the candy
# level earns its keep by being the only one.
LEVEL = Level("WOOLWORKS", "rainbow", rise=4, gap=2.8, exit="stair",
              band=10.0, shelf=4.0, landmark="stripes", step=("quartz", "hop"), beats=[
    ("check", [n("wool_pink", arc=3.6, lift=2, spread=0, pedestal=False),
               n("wool_lime", arc=3.0, lift=3, spread=0, pedestal=False,
                 radial=1.5),
               n("wool_cyan", arc=3.4, lift=3, spread=0, pedestal=False,
                 radial=-1.5, orbs=1)]),
    ("bounce", [n("slime", arc=4.6, lift=1, form="slime", spread=0),
                n("wool_yellow", arc=3.6, lift=2, spread=0,
                  pedestal=False, orbs=2)]),
    ("deck", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
    ("bolts", [n("wool_red", arc=3.5, lift=1, spread=0, pedestal=False),
               n("wool_purple", arc=3.6, lift=2, spread=0,
                 pedestal=False, orbs=1)]),
    ("selvedge", [n("wool_orange", arc=4.4, lift=2, form="slab",
                    spread=0, pedestal=False, orbs=1)]),
])
