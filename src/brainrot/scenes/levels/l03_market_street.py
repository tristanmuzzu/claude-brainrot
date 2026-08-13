"""Level 3: MARKET STREET.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A covered market street, and everything about it is low, warm and near.
#
# The idea in one sentence: *you run the length of a terracotta street
# with the awnings closing over your head and the gutter cut through the
# middle of it.* The level above is a black timber yard over water with
# a headframe to climb; this one never leaves the ground -- nothing in
# it stands higher than three blocks except the chimney you leave by --
# and the two are not confusable from a single frame.
#
# Its identity is the **floor**: terracotta paving, brick kerbs and
# steps, plaster house fronts, dark red roof tiles, oak stall rails,
# water in the gutter and a lantern set flush in the paving. Every lit
# slab here is a threshold stone you run over -- the route painted, in
# the reference's own way -- and there is no decorative light anywhere:
# the lamps are at the gate, on the awning line and at the foot of the
# chimney out.
#
# **Written for four beats, not for ten.** Measured over eight runs, a
# level of this tower lays nine to twelve landings and only three or
# four of them are the script's; everything past the third beat is
# written and never seen. So the threshold, the palette and the
# showpiece are all inside the first three, and the character lives in
# the filler, which repeats: gutter, threshold stone, stall rail,
# paving. The tail is there for the wide turns higher up the flare.
LEVEL = Level("MARKET STREET", "village", rise=7, gap=3.0, exit="ladder",
              band=8.5, profile="plaza", breaks=1, landmark="watchtower",
              ground="terracotta", sub="brick", rock="plaster", accent="roof",
              glow="lantern", liquid="water", step=("brick", "hop"),
              props=("mcfence", "lanternpost", "torch", "crop", "flower",
                     "grasstuft"),
              beats=[
    # The threshold. A lantern flush in the paving on a half step, then
    # the gate itself -- walked through, because one jump impulse always
    # rises 1.25 m and no arc gets under a lintel low enough to read as
    # a door. The tunnel shell is a two-metre pinch, not a room. The
    # walk is *second* on purpose: first in a beat it follows machinery
    # at an arbitrary height and a walk needs its predecessor within
    # half a metre, and it then fires two times in eight.
    ("gate", [n("glow", arc=3.2, lift=1, form="slab", spread=0,
                deco="lamp", orbs=1),
              n("rock", arc=2.8, lift=1, form="slab", kind="walk",
                spread=0, shell="tunnel")]),
    # The stalls, and the showpiece is the last two landings of the
    # same beat rather than a beat of its own. That is not tidiness:
    # machinery is inserted *between* script beats and leaves the body
    # back at lift 1, so a beat that opens by dropping off the height
    # the beat before it climbed to drops nothing about half the time
    # -- the slime is fed a flat approach, the bounce is silently
    # refused and becomes a hop, and the beat still reads as placed.
    # Split, this measured 50%; joined, 94%.
    #
    # So: the fence rail along the front of a counter, up over the
    # counters under the awning beam, and then off the top one onto
    # the market awning, which is slime, and the bounce out of it.
    # Two blocks of drop and no more -- at one the pad is fed 9.7 m/s
    # and the bounce is refused about a third of the time; at four it
    # buys a two-block bounce, costs the level its whole idea of
    # staying on the ground, and measured six frames of nothing but a
    # wall.
    ("stalls", [n("oak", arc=3.0, lift=1, form="fence", spread=0,
                  orbs=1),
                n("rock", arc=3.0, lift=2, spread=0),
                n("accent", arc=3.0, lift=3, spread=0, orbs=1),
                n("slime", arc=4.4, lift=1, form="slime", spread=0),
                n("rock", arc=3.6, lift=2, kind="bounce", spread=1,
                  orbs=2)]),
], exit_beats=[
    # The way out is the plaster chimney at the end of the street, and
    # it is authored rather than left to the generated climb for a
    # measured reason: the generated ladder hangs at ``hug`` 2.0 with no
    # pedestal, so the only thing it can anchor on is the cliff, and
    # over half the runs it found nothing and fell back to a staircase
    # eight landings long -- which on a level that lays ten is the whole
    # level. A ladder up a stack anchors on the stack, and ``step_y`` of
    # four or more is what puts the column's middle cell inside that
    # stack. The generated staircase is still underneath as the
    # fallback, in ``spawn``. Measured: exit climb 7.0 landings a level
    # before, 3.9 after.
    n("rock", arc=2.8, lift=1, hug=2.8, spread=1, confine=True),
    n("ladder", arc=2.4, step_y=6, kind="climb", climb_style="ladder",
      hug=2.6, pedestal_style="plaster", spread=0, confine=True,
      deco="lamp", orbs=2),
], filler=[
    # The street itself, and on a level that only lays ten landings
    # this is most of what is seen -- there is no third beat, because
    # a third beat is a beat nothing ever reaches, and the gutter that
    # used to be one read 42% for the one reason a beat ever does:
    # it opened by dropping off a height the beat before it only
    # reaches when its own last landing did not fall back. Four things, in the order a street
    # has them: the gutter, a lit threshold stone run over, the stall
    # rail, and the paving.
    # No ``form="floor"`` landing in it, and that is measured: the
    # first landing digs a pond of radius three and the paving stone
    # three and a half metres later kept landing in it -- a floor
    # landing places no block and needs ground that is already there,
    # and it failed a third of the time. A plank laid on the paving
    # (``form="trapdoor"``) says the same thing and builds its own.
    # The awning beam moved onto the *walk* for the same class of
    # reason: a lid at three refuses the arcs that climb hardest, and
    # a walk never climbs at all.
    #
    # The gutter is dug under the *last* landing rather than the
    # first: a moat is a pond of radius three and the loop's entry
    # landing is the one place in this beat whose height is not known
    # in advance, so asking it to dig as well cost it a quarter of its
    # placements.
    #
    # Its first landing is written at 3.9 rather than 3.2 for one
    # reason: the beat before it ends on a bounce, whose ``spread``
    # lets it come down at lift 1, 2 or 3, so the jump into the filler
    # is a drop of nought, one or two blocks depending on the run --
    # and 3.9 is the only arc legal at all three. At 3.2 this read
    # 85%. The paving is second and the fence last so that the loop
    # back to the first landing is legal too.
    ("street", [n("accent", arc=3.9, lift=1, spread=2, orbs=1),
                n("glow", arc=2.8, lift=1, form="slab", kind="walk",
                  spread=0, ceiling=3, deco="lamp"),
                n("oak", arc=3.0, lift=1, form="fence", spread=0),
                n("ground", arc=3.6, lift=1, form="trapdoor", spread=0,
                  moat=True, orbs=1)]),
])
