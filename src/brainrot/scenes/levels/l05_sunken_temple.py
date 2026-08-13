"""Level 5: SUNKEN TEMPLE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A temple that has sunk into its own water table. You come in over a
# lit doorstep and walk under the lintel -- the palette turns from the
# mine's grey to wet sandstone, moss and gold at that one block. Then
# the gold dais, and you go off the front of it: a drop onto a mossy
# sprung stone that throws you back up and down into the nave, whose
# whole floor is water and whose landings are the tops of its own
# drowned columns. The way out is the flooded well, a bubble column,
# not another staircase.
#
# Everything hugs the core wall (2.8-3.4) on purpose. This level used
# to frame 50% empty sky, and the fix is not more blocks but standing
# in the groove the reference stands in: rock within three metres on
# one side, the drop on the other, and something overhead -- the hall
# roof over the nave, and a checked beam over the jumps outside it.
#
# Three things about the *machinery* shaped the beat list, and all
# three were measured rather than guessed:
#
# * a level only has room for seven or eight script landings before
#   the climb out claims the rest, so beats five and six of the first
#   draft were written and never once laid;
# * ``_truncate`` cuts the LAST beat, and it always leaves exactly one
#   node -- so the showpiece is beat two, not beat four, or the bounce
#   never fires;
# * a landing that needs ground under it is refused outright wherever
#   one of the level's floor breaks happens to fall, which is why the
#   dais and the drowned columns are ``pedestal=False``.
LEVEL = Level("SUNKEN TEMPLE", "desert", rise=6, gap=2.6, exit="bubble",
              band=9.0, profile="plaza", shelf=4.0, breaks=4,
              landmark="watchtower",
              ground="sandstone", sub="terracotta", rock="chiselled",
              accent="gold", glow="glowstone", liquid="water",
              props=("deadbush", "mcfence"),
              candy=("gold", "mossy"),
              step=("chiselled", "hop"),
              sky=(172, 198, 190), beats=[
    # The threshold. One emissive block flush on the rise at the door,
    # then the doorway itself -- walked, because the head sweeps three
    # cells above every take-off and a lintel low enough to read as a
    # door is a lintel no jump gets under.
    ("doorstep", [n("glowstone", arc=3.2, lift=1, hug=3.0, spread=1,
                    deco="lamp", orbs=1),
                  n("chiselled", arc=2.9, lift=1, hug=3.0, kind="walk",
                    spread=0, ceiling=3)]),
    # The showpiece, at about two thirds of the way through what
    # actually gets laid: the gold dais -- three cells wide, lit, the
    # one loud colour in the level -- and then off the front of it, a
    # drop onto a mossy sprung stone that throws you back up. The
    # level's descent and its one non-ballistic move.
    ("altar", [n("gold", arc=3.9, lift=2, hug=3.4, form="wide",
                 pedestal=False, spread=1, ceiling=2, deco="lamp",
                 orbs=1),
               n("slime", arc=4.4, lift=1, form="slime", hug=3.2,
                 spread=0, ceiling=2, pedestal_style="mossy"),
               n("chiselled", arc=3.6, lift=3, kind="bounce", hug=2.8,
                 spread=1, orbs=2)]),
    # The nave: the room's whole floor is water and the landings are
    # the drowned column tops. The hall shell puts its roof over the
    # course, which is the one thing that stops this level framing as
    # sky -- and it goes on the beat's LAST node, never its first,
    # because a shell is painted the moment its landing commits and
    # the walls it puts up are then in the way of the next landing of
    # the same beat.
    ("nave", [n("mossy", arc=4.2, lift=1, hug=3.4, spread=0,
                pedestal=False, ceiling=2),
              n("chiselled", arc=3.6, lift=1, hug=3.4, spread=0,
                pedestal=False, moat=True, shell="hall", orbs=1)]),
], filler=[
    # The colonnade down the side of the nave: a beam over one jump, a
    # bay door walked through, a flooded bay under the last. The gap
    # between the moat and the next landing has to be wider than the
    # pond -- a moat digs a radius-three disc at commit, and a landing
    # three metres on is standing in the hole the last one dug.
    ("colonnade", [n("terracotta", arc=3.7, lift=2, hug=2.8, spread=0,
                     ceiling=2, orbs=1),
                   n("chiselled", arc=2.9, lift=2, hug=2.8, kind="walk",
                     spread=0, ceiling=3),
                   n("chiselled", arc=3.3, lift=1, hug=3.2, spread=1,
                     pedestal=False, ceiling=2, moat=True)]),
], exit_beats=[
    # The flooded well. Written out rather than left to the generated
    # climb because that one hangs its column at ``hug`` 2.0 mid-lane,
    # where there is nothing within a cell of the column's middle to
    # anchor on -- and a climb with no anchor is refused silently and
    # replaced by a six-step staircase, which is a third of the level.
    # A column beside a *pedestal* finds its anchor on the stack.
    n("chiselled", arc=2.8, lift=1, hug=2.4, spread=1),
    n("prismarine", arc=2.4, step_y=6, kind="bubble", climb_style="water",
      spread=0, deco="lamp", orbs=2),
])
