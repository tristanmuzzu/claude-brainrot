"""Level 16: THE VAULT.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The vault. A treasure cave: raw gold in tuff walls, the hoard piled
# where the lamplight lands, and one ledge crossed over lava with the
# glow on the ceiling. Interior, warm-dark, greedy.
LEVEL = Level("THE VAULT", "gold", rise=5, gap=2.8, exit="stair",
              band=10.5, profile="plaza", landmark="hoard", step=("rawgold", "hop"), beats=[
    ("adit", [n("rock", arc=3.4, lift=1, spread=1, orbs=1)]),
    ("strongroom", [n("rock", arc=3.3, lift=1, hug=2.6, spread=0,
                      shell="grotto"),
                    n("gold", arc=3.4, lift=2, hug=2.6, spread=0,
                      shell="grotto", orbs=1),
                    n("rock", arc=3.3, lift=2, hug=2.6, spread=0,
                      shell="grotto")]),
    ("melt", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
              n("accent", arc=3.4, lift=1, spread=0, moat=True,
                orbs=1)]),
    ("floor", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("seams", [n("gold", arc=3.4, lift=1, spread=0, radial=1.3),
               n("rock", arc=3.3, lift=2, spread=0, radial=-1.3,
                 orbs=1)]),
    ("counting", [n("gold", arc=3.4, lift=1, spread=0, ceiling=2),
                  n("rock", arc=3.5, lift=2, spread=0, ceiling=2,
                    orbs=1)]),
])
