"""Level 14: THE BELFRY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Vertical. Inside the bell tower: sills and beams up the shaft, the
# ladder in the middle of the level rather than at its end, and the
# bell hanging where the climb tops out. Eight blocks gained.
LEVEL = Level("THE BELFRY", "village", rise=8, gap=2.6, exit="ladder",
              band=9.5, profile="plaza", landmark="bell", step=("plaster", "hop"),
              rock="brick", accent="plaster", beats=[
    ("porch", [n("rock", arc=3.4, lift=1, hug=2.6, spread=1, orbs=1)]),
    ("sills", [n("rock", arc=3.4, lift=2, hug=2.6, spread=0,
                 shell="hall"),
               n("accent", arc=3.3, lift=3, hug=2.8, spread=0,
                 shell="hall", orbs=1)]),
    ("rungs", [n("rock", arc=3.0, lift=3, hug=2.2, spread=1),
               n("oak", arc=2.4, step_y=4, kind="climb",
                 climb_style="ladder", hug=2.0, pedestal=False, spread=0,
                 shell="shaft", orbs=2)]),
    ("loft", [n("accent", arc=3.4, lift=6, spread=0, hug=3.2,
                pedestal=False),
              n("accent", arc=3.5, lift=6, spread=0, hug=4.2,
                pedestal=False, orbs=1)]),
    ("beams", [n("oak", arc=3.6, lift=6, form="slab", spread=0, hug=3.6,
                 pedestal=False, ceiling=1),
               n("oak", arc=3.5, lift=6, form="slab", spread=0, hug=4.6,
                 pedestal=False, orbs=1)]),
], filler=[
    ("joists", [n("oak", arc=3.5, lift=5, form="slab", spread=0,
                  hug=3.4, pedestal=False, orbs=1),
                n("oak", arc=3.6, lift=5, form="slab", spread=0,
                  hug=4.6, pedestal=False)]),
])
