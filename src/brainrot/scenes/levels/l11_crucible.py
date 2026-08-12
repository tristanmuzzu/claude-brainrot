"""Level 11: THE CRUCIBLE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A nether cavern lit by its own lava. The seam zigzags through the
# floor of a black cave, glowstone knots in the walls, and every jump
# has the glow underneath it.
LEVEL = Level("THE CRUCIBLE", "nether", rise=7, gap=3.2, exit="stair",
              band=12.0, profile="plaza", landmark="totem", step=("blackstone", "hop"),
              beats=[
    ("mouth", [n("rock", arc=3.4, lift=1, spread=1, orbs=1)]),
    ("vault", [n("rock", arc=3.3, lift=1, hug=2.6, spread=0,
                 shell="grotto"),
               n("rock", arc=3.4, lift=2, hug=2.6, spread=0,
                 shell="grotto", orbs=1),
               n("rock", arc=3.3, lift=2, hug=2.6, spread=0,
                 shell="grotto")]),
    ("seam", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
              n("accent", arc=3.4, lift=1, spread=0, moat=True, orbs=1),
              n("accent", arc=3.5, lift=1, spread=0, moat=True)]),
    ("crust", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
    ("stacks", [n("rock", arc=3.3, lift=1, spread=0, radial=1.4),
                n("rock", arc=3.2, lift=2, spread=0, radial=-1.4,
                  orbs=1)]),
    ("soul", [n("soulsand", arc=4.4, lift=1, spread=0),
              n("soulsand", arc=2.9, lift=1, spread=0, orbs=1)]),
])
