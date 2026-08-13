"""Level 16: THE VAULT.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The strongroom, and its floor is molten. A dark gallery cut into the
# cliff: gold-veined paving, lamps in the wall because nothing else
# lights it, and where the floor is wide enough to walk it is lava the
# whole way across with the bullion standing in it on single stones.
# That is the reference's answer to wide ground -- fill its whole
# width with hazard and leave isolated blocks standing in it -- and it
# is this level's premise. The old version was the same full plaza
# with gold cubes scattered on walkable grey stone, open to the sky,
# and it read as neither a vault nor a place.
#
# Four things here were measured and are worth knowing before editing:
#
# * The level stays *low*. A landing asked for two or three blocks off
#   this terrace came out as authored 12-40% of the time against 100%
#   at one, so the piers became stones standing in the lava.
# * Three floor breaks, not four. The fourth took the whole level's
#   placement down with it: a landing that needs ground under it
#   cannot be laid over a hole, and four holes in eighty metres is
#   enough that most of them cannot.
# * The showpiece is the second beat. Written fourth it laid its pad
#   and never once reached the bounce; written second it is whole
#   every run.
# * ``ceiling=`` is a checked lid, and against this cliff it is often
#   refused for a reason nothing reports -- the cells it wants are
#   inside the rock. The two beats that carried one measured 48% and
#   86% placed; without it, 100% and 93%.
LEVEL = Level("THE VAULT", "gold", rise=5, gap=2.4, exit="ladder",
              band=10.0, profile="plaza", breaks=3,
              landmark="hoard",
              # Warm-dark and committed: gold-veined paving underfoot,
              # blackstone for everything built, bullion for the prize,
              # lava for the light. Dark enough to light itself, which
              # is what puts a lamp at the far end of every stretch.
              ground="rawgold", sub="deepslate", rock="blackstone",
              accent="gold", glow="glowstone", liquid="lava",
              props=("pebbles", "torch", "chain"), dark=0.62,
              step=("gold", "hop"), beats=[
    # The adit: a lit sill flush in the floor, stepped off on foot,
    # then two metres of tunnel crossed at a run. The palette changes
    # completely at the sill -- pink wool in the works below, gold and
    # blackstone here. A doorway is walked through and never jumped
    # through: one impulse rises 1.25 m and the head then sweeps three
    # cells over the take-off, so an arc under a lintel low enough to
    # read as a door is refused every time.
    ("adit", [n("glowstone", arc=3.0, lift=1, form="slab", spread=1),
              n("blackstone", arc=2.9, lift=1, kind="walk", spread=1,
                shell="tunnel", orbs=1),
              n("gold", arc=2.85, lift=1, kind="walk", spread=1,
                shell="tunnel")]),
    # The melt: the level's idea and its showpiece in one beat. A lava
    # lake dug clean across the vault floor, a stone standing in it, a
    # bale of slime on the far side of that, and the bounce across the
    # rest. The rise and the drop have to be inside one beat -- written
    # across a boundary the machinery in between puts the body back on
    # the floor, the drop becomes a level hop, the bounce becomes a
    # hop, and the beat still reads as placed.
    ("melt", [n("gold", arc=2.9, lift=2, spread=1, moat=True,
                shell="cave"),
              n("slime", arc=3.6, lift=1, form="slime", spread=0,
                pedestal_style="deepslate"),
              n("gold", arc=3.6, lift=1, kind="bounce", spread=1,
                moat=True, orbs=3),
              n("iron", arc=2.85, lift=1, kind="walk", spread=1)]),
    # The strongroom itself, and the level's third and last beat. It is
    # the last one for a measured reason: on this terrace a beat laid
    # fourth places its first landing on a fallback half the time --
    # the ground is running out, the exit reserve is biting, and the
    # lock and the crossing have both had a turn. Two beats came out
    # at 50% and 74% there against 100% for the two laid first, and
    # the honest answer was to write two fewer beats rather than to
    # keep asking for landings the level has no room for.
    ("strongroom", [n("chiselled", arc=3.1, lift=1, spread=1,
                      shell="hall", orbs=1),
                    n("iron", arc=2.85, lift=1, kind="walk", spread=1),
                    n("gold", arc=3.2, lift=2, spread=1, moat=True)]),
], filler=[
    # The character: a stone in the lava, a ledger plank walked over
    # it, and a stack of bullion. It loops, so the seam from its last
    # landing to its first is a jump too.
    ("seams", [n("gold", arc=3.2, lift=1, spread=1, moat=True, orbs=1),
               n("blackstone", arc=2.85, lift=1, kind="walk", spread=1),
               n("iron", arc=3.2, lift=2, spread=1)]),
])
