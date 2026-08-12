"""Level 4: THE TIMBERWORKS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Underground. A timbered gallery the whole way -- the first full
# interior level -- with rails underfoot, one cobweb wade, and the
# course brushing a headframe at the door. Dark, lamp-lit.
LEVEL = Level("THE TIMBERWORKS", "mine", rise=5, gap=2.6, exit="ladder",
              band=7.5, profile="plaza", landmark="crane", step=("oak", "hop"), beats=[
    ("adit", [n("rock", arc=3.2, lift=1, hug=3.0, spread=0,
                shell="tunnel"),
              n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                shell="tunnel", orbs=1)]),
    ("rails", [n("accent", arc=3.6, lift=1, spread=0, radial=1.2,
                 shell="tunnel"),
               n("accent", arc=3.5, lift=1, spread=0, radial=-1.2,
                 shell="tunnel", orbs=1)]),
    ("web", [n("web", arc=2.6, lift=1, kind="web", form="web", spread=0,
               shell="tunnel", orbs=1)]),
    ("gallery", [n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                   shell="tunnel"),
                 n("rock", arc=3.2, lift=2, hug=3.0, spread=0,
                   shell="tunnel", orbs=1),
                 n("rock", arc=3.3, lift=2, hug=3.0, spread=0,
                   shell="tunnel")]),
    ("sump", [n("ground", arc=4.4, lift=0, form="floor", orbs=1)]),
    ("boards", [n("oak", arc=3.2, lift=1, form="trapdoor", spread=0,
                  shell="tunnel"),
                n("oak", arc=3.2, lift=1, form="trapdoor", spread=0,
                  shell="tunnel", orbs=1),
                n("rock", arc=3.2, lift=1, spread=0, shell="tunnel")]),
])
