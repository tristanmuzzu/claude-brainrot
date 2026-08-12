"""Level 3: MARKET STREET.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A street. The one place near the bottom that keeps the full floor,
# because a street is a *place* and dresses it: facades against the
# core, awning slabs, and one stretch crossed inside a house -- the
# tower's first interior, twenty seconds in.
LEVEL = Level("MARKET STREET", "village", rise=6, gap=3.0, exit="ladder",
              band=12.5, profile="plaza", landmark="watchtower", step=("brick", "hop"),
              beats=[
    ("street", [n("ground", arc=4.6, lift=0, form="floor", orbs=1),
                n("rock", arc=3.4, lift=1, spread=1)]),
    ("stalls", [n("oak", arc=3.0, lift=1, form="fence", spread=0,
                  radial=1.3),
                n("accent", arc=3.2, lift=2, spread=0, radial=-1.3,
                  orbs=1),
                n("oak", arc=3.0, lift=2, form="fence", spread=0,
                  radial=1.3)]),
    ("awnings", [n("accent", arc=4.4, lift=2, form="slab", spread=0),
                 n("accent", arc=3.6, lift=3, form="slab", spread=0,
                   orbs=1)]),
    ("parlour", [n("rock", arc=3.6, lift=1, hug=2.8, spread=0,
                   shell="hall"),
                 n("rock", arc=3.4, lift=1, hug=2.8, spread=0,
                   shell="hall", orbs=1)]),
    ("yard", [n("ground", arc=5.2, lift=0, form="floor", orbs=1)]),
    ("gables", [n("rock", arc=3.4, lift=1, hug=3.0, spread=0),
                n("rock", arc=3.5, lift=2, hug=3.0, spread=0, ceiling=2,
                  orbs=1),
                n("accent", arc=3.6, lift=3, hug=3.2, spread=0)]),
])
