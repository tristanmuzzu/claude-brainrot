"""Level 10: THE APIARY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The apiary. Honeycomb frames against the wall, one slow honey beat
# that drops the pace to a crawl, and a slime pad that throws the body
# onto the high comb. Sticky, golden, unlike anything beside it.
LEVEL = Level("THE APIARY", "honey", rise=5, gap=2.8, exit="stair",
              band=9.5, shelf=4.5, landmark="comb", step=("honeycomb", "hop"), beats=[
    ("combs", [n("rock", arc=3.4, lift=1, spread=0, orbs=1),
               n("rock", arc=3.3, lift=2, spread=0)]),
    ("honey", [n("honey", arc=3.3, lift=1, spread=0),
               n("honey", arc=2.8, lift=1, spread=0, orbs=1)]),
    ("bounce", [n("slime", arc=4.6, lift=1, form="slime", spread=0),
                n("honeycomb", arc=3.6, lift=2, spread=0, orbs=2)]),
    ("frames", [n("rock", arc=3.4, lift=3, spread=0, radial=1.3),
                n("rock", arc=3.3, lift=3, spread=0, radial=-1.3,
                  orbs=1)]),
    ("meadow", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("cells", [n("honeycomb", arc=3.4, lift=1, spread=0),
               n("accent", arc=3.4, lift=2, spread=0, orbs=1)]),
])
