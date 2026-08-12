"""Level 10: THE APIARY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A working apiary: a broad hay terrace on the rim, a hive shed run
# through at the start of it, the comb frame at the far end, and water
# ponds dug into the ground under every jump in the second half.
#
# The old version was 100% plain hop over 20% designed content, and a
# walker got 96% of the way down it on one run. Three things replace that:
# the shed is *walked* through, which is how a body gets under a lintel
# when one impulse always rises 1.25 m; the hive is *climbed* on a ladder,
# the one special block the real map leans on hard; and the fallen comb is
# the level's single slime pad, rationed exactly as the save rations them,
# one per level, used once. Gold against dark timber, warm light against
# the level of blue ice below it.
#
# It *descends* four blocks in the middle of gaining five -- off the top
# of the hive onto the pad, out of the pad onto the pond stones -- which
# is the reference's own ratio and the thing every level in this tower
# lacked.
#
# On the ground: ``channel``, the full band with a two-cell water trough
# cut down the middle of it, which is the reference's own answer to wide
# ground -- where it widens, its whole width is hazard -- and the thing
# that makes this level unmistakable in a still. It costs the *gated*
# landmark: the cut runs exactly where the running lane does and takes
# the rock out from under a gate's base cells, so the comb reserves 1/8
# on a channel against 8/8 on a ledge. Both were built and measured; the
# ledge version read worse on almost every other row (designed 38%
# against 51%, two unchecked placements against none, hop 84% against
# 75%, and the bounce beat stopped being reached at all), so the trough
# stays and the structure is the small comb frame beside the course.
LEVEL = Level("THE APIARY", "honey", rise=5, gap=3.0, exit="ladder",
              profile="channel", band=10.5, breaks=4, landmark="comb",
              ground="hay", sub="darkoak", rock="honeycomb",
              accent="honey", liquid="water", glow="shroomlight",
              candy=("honey", "honeycomb"),
              props=("mcfence", "grasstuft", "flower", "crop",
                     "lanternpost"),
              sky=(198, 208, 234),
              step=("honeycomb", "hop"), beats=[
    # The threshold: a shroomlight block flush in the hay on a rise, and
    # then the shed door, walked under a checked lid.
    ("gate", [n("glow", arc=3.2, lift=1, spread=0, deco="lamp", orbs=1),
              n("darkoak", arc=2.9, lift=1, kind="walk", spread=0,
                ceiling=3)]),
    # Inside the shed, crossed at a run between the frames. One shelled
    # landing and not three: the reference's interiors are pinches a couple
    # of metres long, not rooms, and three shelled landings in a row jammed
    # the lens on 10% of this level's frames with a tunnel and 21% with a
    # hall. ``hall`` rather than ``tunnel`` for the one that is left --
    # a tunnel stands its walls two cells off the line and its roof four
    # above, which against a 52-degree lens is most of the frame.
    ("shed", [n("honeycomb", arc=2.9, lift=1, kind="walk", spread=0),
              n("darkoak", arc=2.9, lift=1, kind="walk", spread=0,
                shell="hall", orbs=1),
              n("honeycomb", arc=3.4, lift=2, spread=1)]),
    # The hive: up its side on a ladder rather than round it on steps, and
    # off the top plate. Six blocks up is the highest the body stands on
    # this level and the view back down the terrace is the point of it.
    #
    # The ladder needs the hive *under* it. A climb is refused unless the
    # column has something solid on one of its four sides at both its
    # middle and its top, and out in the lane the only thing that can be
    # there is the landing's own stack -- so ``pedestal=False``, which is
    # what the generated climbs use inside a shaft shell, silently gives up
    # the anchor and the whole beat falls back to hops. It measured 43%
    # placed as authored with it and 89% without.
    #
    # ``step_y`` is 4 and not 3 for the same reason and with no better
    # explanation: at 3 the beat measured 43% again, the climb vanished
    # from the move mix entirely, and the level's exit climb fell back
    # from a ladder to a staircase. The ride is also this level's whole
    # lens-jam figure -- 10% of frames are honeycomb wall a metre away,
    # which is what climbing a hive looks like and what the real map's
    # six-second ladder shaft looks like too. Shortening it to buy that
    # number back costs the verb, and the verb is worth more.
    ("hive", [n("hay", arc=3.0, lift=2, hug=2.4, spread=1, moat=True,
                orbs=1),
              n("oak", arc=2.4, step_y=4, kind="climb",
                climb_style="ladder", hug=2.4, spread=0, orbs=2),
              n("honeycomb", arc=3.6, lift=5, spread=0, ceiling=2,
                deco="lamp", orbs=1)]),
    # The showpiece, three fifths of the way through: a four-block fall
    # off the hive onto the one fallen comb, which is slime and throws the
    # body two blocks back up. The fall is what makes it work -- a pad only
    # ever gives back the drop that fed it.
    ("comb", [n("slime", arc=6.0, lift=1, form="slime", spread=0,
                moat=True, orbs=2),
              n("honey", arc=4.4, lift=3, kind="bounce", spread=1,
                orbs=3)]),
    # Down onto the pond stones and along a plank under a beam. Both
    # stones dig the water out around themselves, so the jump is over
    # water rather than over a blue patch of floor.
    ("ponds", [n("darkoak", arc=3.6, lift=2, spread=0, moat=True,
                 radial=-1.8, orbs=1),
               n("honeycomb", arc=3.4, lift=1, spread=0, moat=True,
                 radial=1.8),
               n("hay", arc=2.9, lift=1, kind="walk", spread=0,
                 ceiling=3, orbs=1)]),
], filler=[
    # The level's voice: a hive box out of the water, and a beam to run
    # under. Whatever terrace is left after the script plays this, so the
    # walk and the lid come round again rather than the parkour.
    ("meadow", [n("darkoak", arc=3.3, lift=1, spread=0, moat=True,
                  orbs=1),
                n("honeycomb", arc=2.9, lift=1, kind="walk", spread=0,
                  ceiling=3)]),
])
