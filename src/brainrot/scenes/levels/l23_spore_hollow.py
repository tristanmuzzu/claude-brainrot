"""Level 23: SPORE HOLLOW.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A cave of giant mushrooms. The great red cap fills the room, stem
# columns carry the course, shroomlight does the lighting. Soft
# shapes, low light, bouncy middle.
LEVEL = Level("SPORE HOLLOW", "mushroom", rise=5, gap=3.0, exit="vine",
              band=11.0, profile="plaza", landmark="greatcap",
              step=("mushroomstem", "hop"), beats=[
    ("litter", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                n("rock", arc=3.4, lift=1, spread=1)]),
    ("hollow", [n("rock", arc=3.3, lift=1, hug=2.6, spread=0,
                  shell="grotto"),
                n("rock", arc=3.4, lift=2, hug=2.6, spread=0,
                  shell="grotto", orbs=1)]),
    ("caps", [n("accent", arc=5.2, lift=2, form="wide", spread=1,
                pedestal_style="mushroomstem", orbs=1),
              n("accent", arc=5.4, lift=2, form="wide", spread=1,
                pedestal_style="mushroomstem")]),
    ("pad", [n("slime", arc=4.8, lift=1, form="slime", spread=0),
             n("accent", arc=4.4, lift=2, form="wide", spread=1,
               orbs=2)]),
    ("stems", [n("rock", arc=3.6, lift=3, spread=0),
               n("rock", arc=3.4, lift=3, spread=0, orbs=1)]),
    ("gills", [n("accent", arc=4.6, lift=2, form="wide", spread=1,
                 orbs=1)]),
])
