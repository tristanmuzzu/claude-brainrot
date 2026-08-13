"""Level 8: THE CISTERN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A flooded rock tank, and the water is the level. ``profile="channel"``
# cuts the theme's liquid down the whole length of the floor rather than
# leaving it as two decorative moats -- which is the reference's single
# most-used mechanic and its answer to a wide floor: where the ground
# widens, its width is hazard and the landings are isolated blocks standing
# in it. The old design was an eleven-cell brown plate with white cubes on
# it and no water in shot anywhere, which is a cistern with nothing in it.
#
# The band can afford to be wide here where CANOPY WALK's could not. The
# cliff at your back belongs to SUNKEN TEMPLE three levels below, whose band
# is 12.0, so the overhang stands at about ``out - 10.9`` and anything up to
# 10.5 is this level's own ground rather than the level below's rock -- the
# opposite of level 7's problem and the reason these two neighbours want
# opposite numbers. The lid is THE CRUCIBLE's floor slab, a full plaza, so
# this level is roofed end to end ten blocks up: the tower's one real
# interior of the turn, and the loudest possible contrast with the jungle
# ledge before it.
#
# The landmark is an ``arch`` and not the ``hoodoo`` this level was first
# given, for a reason worth writing down: ``_lm_g_hoodoo`` names
# ``terra_red``/``terra_orange`` literally rather than taking the level's
# roles, so it stood two brick-orange mesa columns in a grey-and-teal
# cistern. ``_lm_g_arch`` is built from ``theme.rock``, ``theme.accent`` and
# ``theme.glow``, so here it comes out as two calcite piers carrying a
# prismarine lintel with sea lanterns on it -- a broken aqueduct over the
# water, which is what a cistern should be recognised by. Check what a
# blueprint is made of before choosing it; about half of them are literal.
LEVEL = Level("THE CISTERN", "dripstone", rise=6, gap=2.8, exit="bubble",
              band=10.5, profile="channel", breaks=0, landmark="cluster",
              ground="dripstone", sub="tuff", rock="calcite",
              accent="prismarine", liquid="water", glow="sealantern",
              props=("dripstone", "pebbles", "chain"),
              sky=(72, 96, 104), dark=0.62,
              candy=("calcite", "prismarine", "darkprismarine"),
              step=("calcite", "hop"), beats=[
    # The sluice gate. A sea lantern set in the sill on a rise, then the sill
    # itself crossed on foot -- the palette goes from jungle green to wet
    # white-and-teal in one block, which is what the reference's seams do.
    ("sluice", [n("glow", arc=3.0, lift=1, hug=3.2, spread=1, ceiling=3,
                  shell="tunnel", orbs=1),
                n("calcite", arc=2.2, lift=1, hug=3.2, kind="walk",
                  spread=0)]),
    # Stepping stones out over the tank, climbing as they go. Each one digs
    # its own pool, so the water is genuinely *under* the jump rather than a
    # blue patch beside it -- and the last one is high enough for the drop
    # that follows to be worth something.
    ("stones", [n("calcite", arc=3.4, lift=2, hug=3.4, spread=1, moat=True,
                  ceiling=3),
                n("darkprismarine", arc=3.4, lift=1, hug=3.0, spread=1,
                  moat=True, ceiling=3, orbs=1),
                n("calcite", arc=3.4, lift=2, hug=3.4, spread=1, moat=True,
                  ceiling=3)]),
    # The drain: onto the tank wall, a block down onto slime lying in the
    # bottom, and back out.
    #
    # The rise and the drop are inside *one* beat and that is not tidiness.
    # A lock or a landmark crossing is inserted between script beats and
    # leaves the body back on the floor at lift 1, so a beat that opens by
    # dropping off the height the beat before it climbed to is a beat that
    # drops nothing about half the time. Measured: with the climb in
    # ``stones`` the slime landed level with its take-off in every run, the
    # bounce silently became an ordinary hop, and the beat read 50%.
    #
    # It gains one block and not two, and that is the arithmetic rather than
    # timidity: a bounce is thrown by the speed it arrived with, and one
    # block of drop across a four-and-a-half-metre arc arrives at 9.2 m/s --
    # enough to be thrown back a block, not two. Two would want a two-block
    # drop, which wants a second rise, which makes this a four-node beat, and
    # a four-node beat here is truncated to three every single run.
    ("drain", [n("calcite", arc=3.4, lift=2, hug=3.0, spread=1,
                 shell="hall"),
               n("slime", arc=4.4, lift=1, hug=3.0, spread=0,
                 pedestal_style="tuff", moat=True),
               n("prismarine", arc=3.4, lift=2, hug=3.0, kind="bounce",
                 spread=1, orbs=3)]),
    # The gallery: a lamplit bay carved back into the core wall, and the
    # level's one enclosed pinch. Two metres of interior, not fifteen
    # seconds of tunnel (RESEARCH.md 4 -- the real map is fully enclosed 6%
    # of the way, in runs with a median length of two metres).
    ("gallery", [n("calcite", arc=3.6, lift=2, hug=2.2, spread=1,
                   shell="grotto"),
                 n("dripstone", arc=3.4, lift=1, hug=2.2, spread=1,
                   shell="grotto", orbs=1)]),
    # Under the teeth. A checked lid at three, which is where a lid is
    # honest in this kernel: the head sweeps two cells above every take-off,
    # so a beam at two refuses every arc under it.
    ("teeth", [n("dripstone", arc=3.6, lift=1, spread=0, ceiling=3),
               n("calcite", arc=3.6, lift=1, spread=0, ceiling=3, orbs=1)]),
], filler=[
    # The tank itself, repeating: a stone standing in the water, a lit shelf
    # against the wall, and a low slab under the drip-stone.
    ("tank", [n("calcite", arc=3.4, lift=1, spread=1, moat=True, orbs=1),
              n("glow", arc=3.2, lift=2, hug=3.0, spread=1),
              n("darkprismarine", arc=3.2, lift=1, spread=1, ceiling=3)]),
])
