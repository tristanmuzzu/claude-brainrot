"""Level 5: SUNKEN TEMPLE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A desert temple that has sunk into its own water table, and you cross
# it the way you would cross a flooded building: along what is still dry.
#
# You come in over a glowstone sill set flush in the sand and walk under
# the lintel -- one block at which the palette stops being the mine's
# wet grey and becomes pale sandstone, red terracotta and gold. Inside,
# the porch is already ankle-deep: the first jump lands in standing
# water, and the three treads out of it climb the temple's own stair to
# the gold top step, which is the highest dry stone in the place. Then
# you go off the front of it -- two blocks down and four metres out, the
# long jump of the level -- into the nave, whose whole floor is water
# and whose stepping stones are the tops of its own drowned columns,
# broken off at different heights and roofed over by what is left of
# the hall. The aisle beside it repeats for as long as the terrace
# lasts. The way out is the flooded well in the sanctuary: a bubble
# column, not a staircase.
#
# The one thing to remember from a run of it is the gate -- ``arch``
# renders as two chiselled piers under a **gold** lintel with a lamp on
# each shoulder, because ``_lm_g_arch`` takes ``rock``/``accent``/
# ``glow`` from the level rather than naming its own stone -- and the
# course is steered through it.
#
# Five things about the *machinery* shaped this table, and all five were
# measured on this level rather than guessed:
#
# * **The lock was eating the level.** ``breaks >= 1`` forces it, it
#   lays eighteen blocks of arc in one decision, and on a terrace whose
#   whole budget is about thirty-five blocks after the exit reserve that
#   is half the level spent on machinery: with ``breaks=4`` this level
#   measured 21% designed content. The floor of a sunken temple does not
#   want holes in it anyway -- it wants water -- so ``breaks=0`` and the
#   walk number is held down by the two moats instead, which is the
#   trade RULES 7 measures at 65.8% -> 25.8% on identical worlds.
# * **The exit column overshot by three blocks.** ``step_y=6`` off a
#   lift-1 landing reaches the next level's floor *plus three*, and the
#   level above then opens by dropping back down to its own terrace --
#   which is the owner's "it puts a ladder there and then jumps back
#   down to a lower part" in one number. ``rise`` is 4 and the crossing
#   descends one, so the column wants exactly ``step_y=4``, which is
#   also the shortest rise a bubble can anchor on.
# * **A beat cannot start high**, because machinery is inserted between
#   beats and leaves the body back at lift 1. So every beat here opens
#   at lift 1 and climbs *inside itself* on ``step_y=1``, which is
#   measured from the landing before rather than from the terrace and is
#   therefore true wherever the body actually is.
# * **A beat's tail is rarely laid**, so the overhead mass, the water
#   and the non-hop verb are all on first and second nodes, never last.
# * **A moat digs a radius-three bowl at commit**, so the landing after
#   one is ``pedestal=False``: a stack of terrain cannot stand in the
#   hole the last landing dug.
# * **The stair is three treads and not four**, which is the one place
#   "get off the floor" and "designed content" pull against each other
#   here and the A/B is worth keeping. A fourth tread reaches lift 4 and
#   turns the drop into the nave into a -3, and it measures, over 24
#   runs: designed content 47.7% -> 44.4%, hop share 82.1% -> 84.0%
#   (against an 85% ceiling), and the colonnade -- which is the filler,
#   so it is where this level's character actually lives -- from 2.6
#   landings a visit to **1.0**, because the extra tread's arc comes
#   straight out of the terrace the filler was going to use. Three
#   treads still reach lift 3 and still drop two into the flood, which
#   is the shape; the fourth only bought a block.
LEVEL = Level("SUNKEN TEMPLE", "desert", rise=4, gap=2.6, exit="bubble",
              band=9.0, profile="plaza", shelf=4.0, breaks=0,
              landmark="arch",
              ground="sandstone", sub="terracotta", rock="chiselled",
              accent="gold", glow="glowstone", liquid="water",
              props=("sugarcane", "lanternpost", "mcfence", "deadbush",
                     "vinehang"),
              candy=("gold", "prismarine"),
              step=("chiselled", "hop"),
              dark=0.30,
              # The identity is the floor, not the one structure: twelve
              # materials with no single one over a fifth of the ground,
              # against the two or three most of this roster has. Wet
              # green prismarine and moss in the low cells, red
              # terracotta and clay in the dry ones, gold where the
              # temple was rich, sand blown over all of it.
              floor=(("chiselled", 3), ("terracotta", 3), ("prismarine", 2),
                     ("mossy", 2), ("clay", 2), ("gravel", 2),
                     ("darkprismarine", 1), ("gold", 1), ("redsand", 1),
                     ("moss", 1), ("coarse", 1)),
              sky=(172, 198, 190), beats=[
    # The threshold. A glowstone sill flush on the rise at the door,
    # then the doorway itself -- *walked*, because one jump impulse
    # always rises 1.25 m and the head then sweeps the two cells above
    # every take-off, so a lintel low enough to read as a door is a
    # lintel no jump gets under. The beam at three is the genre's 2bc,
    # the lid you sprint under, and it is the one form of it this
    # motion model can express honestly.
    ("doorstep", [n("glowstone", arc=3.2, lift=1, hug=3.0, spread=1,
                    deco="lamp", orbs=1),
                  n("chiselled", arc=2.9, lift=2, hug=3.0, kind="walk",
                    spread=0, ceiling=3, deco="lintel")]),
    # The porch, already flooded, and the temple's own stair out of it.
    # The first landing stands in the water it dug; the two treads above
    # it climb a block each on ``step_y``, so the stair is a stair
    # wherever the body happened to arrive, and the top one is gold and
    # lit -- the highest dry stone in the level and the thing you aim
    # at from the door.
    ("steps", [n("chiselled", arc=3.2, lift=2, hug=3.0, spread=1,
                 moat=True, ceiling=2, orbs=1),
               n("sandstone", arc=3.0, step_y=1, hug=2.8, spread=0,
                 pedestal=False, ceiling=2),
               n("gold", arc=3.0, step_y=1, hug=2.6, spread=0,
                 deco="lamp", orbs=1)]),
    # The nave: off the front of the top step, two blocks down and four
    # metres out -- the longest jump in the level, and the only way to
    # buy one, because falling takes time and the body does not slow
    # down while it does. It lands on a drowned column top standing in
    # the flood, with nothing under it. The hall roof goes on the LAST
    # node, never the first: a shell is painted the moment its landing
    # commits and the walls it puts up are then in the way of the next
    # landing of the same beat.
    ("nave", [n("prismarine", arc=4.2, lift=2, hug=3.2, spread=1,
                pedestal=False, moat=True, ceiling=2, orbs=2),
              n("chiselled", arc=3.4, lift=3, hug=3.2, spread=0,
                pedestal=False, shell="hall", orbs=1)]),
], filler=[
    # The aisle down the side of the nave, and this is where the level's
    # character actually lives, because the filler repeats and a
    # script's tail does not: a jump under the architrave, a bay door
    # crossed on foot, and a step up on to the next column top. No moat
    # here on purpose -- the filler loops, and the second lap digs away
    # the ground the first lap's pedestals are standing on.
    ("colonnade", [n("chiselled", arc=3.2, lift=3, hug=2.8, spread=1,
                     radial=0.8, ceiling=3, orbs=1),
                   n("sandstone", arc=2.9, lift=3, hug=2.8, kind="walk",
                     spread=0, radial=-0.8, ceiling=3),
                   n("prismarine", arc=3.2, lift=3, hug=3.0, spread=0,
                     radial=0.8, pedestal=False, orbs=1)]),
], exit_beats=[
    # The flooded well in the sanctuary. Written out rather than left to
    # the generated climb because that one hangs its column mid-lane at
    # ``hug`` 2.0, where there is nothing within a cell of the column's
    # middle index to anchor on -- and a climb with no anchor is refused
    # silently and replaced by a six-step staircase, which on this level
    # was a third of everything the viewer saw. The column keeps its
    # **pedestal** and asks for no ``hug`` at all: standing the landing
    # on its own stack is what gives the column something to hang on for
    # its whole height. Check ``--report``'s move mix for the word
    # ``bubble``; if it is missing, this is a staircase again.
    # **Nothing overhead on the well head, and that is measured.** The
    # exit climb is the emptiest third of any level in this tower, so
    # both lids RULES 7 recommends for it were tried here over 24 runs:
    # ``shell="cave"`` bought 3 points of empty frame (36% -> 33%) and
    # ``ceiling=2`` bought about the same, and *both* cost 2.6 points of
    # designed content and 2 of hop share -- because a lid that will not
    # fit refuses the launch landing outright, and the fallback for a
    # refused ascent node is the generated staircase (exit-climb
    # landings 87 -> 93 of 240). This level is at 36% empty against a
    # 48% rule and at 47%/82% on the two numbers it is actually near, so
    # the trade is the wrong way round here. Try it again on a level
    # with frame trouble.
    n("chiselled", arc=3.0, step_y=0, hug=2.4, spread=2, deco="lamp",
      orbs=1),
    n("prismarine", arc=3.0, step_y=2, kind="bubble", climb_style="water",
      spread=0, deco="lamp", orbs=2),
])
