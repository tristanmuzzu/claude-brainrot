"""Level 15: WOOLWORKS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The dye house, and the one deliberately artificial place in the tower.
#
# One sentence: *the colour is on the things that hang, not on the
# floor you are standing on.* The floor is dye-stained flagstone -- deep
# violet and indigo with the spills of every other vat ground into it,
# dark, and cut clean through by the vats themselves. Everything you
# stand on is bright: bolts of undyed quartz-white wool standing in the
# vats, and a line of dyed skeins hung three blocks up over the works.
# You come in through the dye-house door on foot, run the drying line
# high over the vat floor, come off the end of it in a two-block fall,
# cross the vats on the bolts, jump through the hole in the loom wall
# and leave up the hoist ladder to the drying loft.
#
# **The value split is the whole design and it was the previous
# version's one real failure.** That one skinned a rainbow level in
# rainbow: seven wools at equal weight underfoot, seven wools standing
# on them, quartz walls behind. Every surface in the frame was the same
# *value* at a different hue, so the contact sheet read as confetti --
# a chessboard of pink, blue, red and yellow with nothing in it saying
# which cells were the route. Hue does not separate a landing from its
# floor at speed; value does. So the floor here is 53% dark by weight
# with one violet dominant at a quarter (the shape ``docs/RESEARCH.md``
# measures on the real map: sixteen materials, commonest at 26%), and
# every landing is quartz, wool_yellow or glowstone. A bright thing on
# a dark ground is legible from the far end of the terrace, and that is
# what "loud" is supposed to buy.
#
# Five things about the shape are the machinery's rather than mine:
#
# * **A beat lays about half its nodes and the tail is never seen**, so
#   the level is three beats of three or four and everything it is
#   about is inside the first three. The old table had five beats and
#   its last two measured 9 and 1 landings against 21 and 28 for the
#   first two.
# * **A beat opens at lift 1** because machinery is inserted between
#   beats and hands the body over at lift 1, and the climb inside a
#   beat is on ``step_y`` rather than on an absolute ``lift`` -- an
#   opener carries ``spread`` and lands a block high about a fifth of
#   the time, and ``lift + 1`` behind it is then a rise of two, which
#   nothing in this motion model makes.
# * **The rise and the drop are inside one beat.** Written across a
#   beat boundary the fall silently becomes a level hop, because the
#   machinery between them puts the body back on the floor -- and the
#   beat still reports as placed.
# * **No ``moat`` in the filler.** The filler loops and the second lap
#   digs the ground out from under the pedestals the first lap stood
#   up.
# * **``breaks=0``.** Any break at all forces the lock, which lays five
#   landings and eighteen blocks of arc in one decision on a terrace
#   that has about eleven -- and on a gated level it also walks the
#   frontier straight past the doorway. The walk number is held down by
#   the three vats instead: it is the *hole* a moat digs and not the
#   water in it that stops a walker, and everything downstream of one
#   is ``pedestal=False`` and has nothing under it at all.
LEVEL = Level("WOOLWORKS", "rainbow", rise=6, gap=2.4, exit="ladder",
              band=10.0, shelf=4.5, profile="ledge", breaks=0,
              landmark="stripes",
              # Six roles, all set. Violet ground and indigo sub are the
              # dye that has soaked into the building; quartz is every
              # undyed bolt and every rack the works is built of, which
              # is what makes the *route* the light thing in the frame;
              # wool_yellow is the one dyed colour that is bright enough
              # to hold its own beside it.
              ground="wool_purple", sub="wool_blue", rock="quartz",
              accent="wool_yellow", glow="glowstone", liquid="water",
              props=("mcfence", "lanternpost", "rail", "torch", "pebbles"),
              step=("quartz", "hop"), dark=0.25,
              # Sixteen materials with the dominant at 25%, and a *value*
              # spread rather than only a hue one: violet, indigo,
              # deepslate, blackstone and red are 53% of the floor by
              # weight and agree with each other in value, so the pale
              # bolts standing on them read as objects rather than as
              # more floor. The base rainbow mix is seven wools at equal
              # weight and is exactly the confetti this replaces.
              floor=(("wool_purple", 4), ("deepslate", 3), ("blackstone", 2),
                     ("wool_red", 2), ("wool_pink", 2), ("oak", 2),
                     ("wool_cyan", 1), ("wool_lime", 1), ("wool_orange", 1),
                     ("diorite", 1), ("gravel", 1), ("glass", 1),
                     ("stone", 1)),
              # A steam-heavy lilac rather than the theme's near-white:
              # half of every frame here is the thing behind a pale bolt,
              # and at (240, 220, 250) the bolt and the sky were the same
              # value. The level below is a grey-blue belfry.
              sky=(206, 196, 224), beats=[
    # The threshold, and the level's one interior. Three ideas in three
    # landings rather than three hops at one height:
    #
    #   0. a glowstone panel laid flush in the flagstone as a half step,
    #      on the rise. The light to aim at, and the palette stops being
    #      the belfry's grey plaster at that block.
    #   1. the dye-house door -- a lintel at three, *walked* under at a
    #      run, with the first vat cut out beneath it. One jump impulse
    #      always rises 1.25 m and the head then sweeps the two cells
    #      above every take-off, so a beam low enough to read as a
    #      doorway refuses every arc under it: the genre's 2bc is only
    #      expressible over a leg that never leaves the ground. The walk
    #      is second and never first -- first in a beat it follows
    #      machinery at an arbitrary height, and a walk needs its
    #      predecessor within half a metre.
    #   2. off the floor and onto the first undyed bolt, standing out of
    #      the vat the landing before it just dug. ``pedestal=False``
    #      because a plinth 3.2 m along would have to stand in that hole.
    #
    # Surfaces 1.5 / 2.0 / 3.0. A slab stands half a block down in its
    # own cell, so the panel into the doorway is +0.5, inside the 0.55 a
    # walk allows; the jump off it is +1.0 at ``arc`` 3.2, a reach of
    # 2.52 against a +1 window that shuts at 3.10. Written at 3.6 it
    # would be a reach of 2.92 and would spend its life falling back.
    #
    # The shell is on the beat's **last** node: a shell is painted the
    # moment its landing commits and its walls are then in the way of the
    # next landing of the same beat. At lift 2 it comes out as a roof
    # with open sides -- ``_shell`` skips a wall column with nothing
    # under it -- which is the reference's own groove and is what this
    # level wants over its head anyway.
    ("dyehouse", [n("glow", arc=3.2, lift=1, hug=3.0, form="slab", spread=1,
                    deco="lamp", orbs=1),
                  n("oak", arc=2.9, lift=1, hug=3.0, kind="walk", spread=0,
                    ceiling=3, moat=True, deco="lintel"),
                  n("rock", arc=3.2, lift=2, hug=2.8, spread=0,
                    pedestal=False, shell="tunnel", orbs=1)]),
    # The drying line, and this is the beat that answers "half the jumps
    # are at ground level". Its middle two landings are skeins hung over
    # the works with nothing whatever under them, at three and four
    # blocks off the flagstone, and the beat ends by coming off the end
    # of the line.
    #
    # Surfaces 2.0 / 3.0 / 4.0 / 2.0: a stone standing in the wash
    # trough, up onto the first skein, up onto the second, and then the
    # level's long jump and its descent -- a two-block fall out into the
    # works. Nothing rises two blocks in one impulse, so stepping *down*
    # is the only way to make a jump read as long: ``arc`` 4.9 is a
    # reach of 4.22 against a -2 window of 3.12 to 5.56, where a level
    # hop stops at 4.26 of arc and 3.58 of reach.
    #
    # It lands at surface 2.0 and that is not a free choice. A ``step_y``
    # descent onto surface 1.0 asks for the terrace's own top cell,
    # which is solid: the landing is refused, the rest of the beat goes
    # with it, and the recovery drops a plain cube a block lower under
    # this beat's own name, so the table still reads it as placed.
    #
    # The whole descent is inside the level's first two thirds and
    # nothing after the high point goes down more than the two blocks
    # here -- the vats run at 2.0 to 3.0 and the hoist is the highest
    # thing in the level.
    # The two skeins carry a ``ceiling=3`` each and those are the rack
    # beams they are hung from -- overhead mass on the two highest
    # landings in the level, which is where the frame is emptiest (the
    # ray fan's shallow down-rows fly over the shelf into the void from
    # up here, and only something over the head answers them). A lid at
    # three above the take-off is legal over a +1 hop: one impulse rises
    # 1.25 m, so the arc passes a metre and a half under it.
    ("skeins", [n("rock", arc=3.4, lift=1, hug=2.8, spread=1, moat=True,
                  orbs=1),
                n("accent", arc=3.2, step_y=1, hug=2.6, spread=0,
                  pedestal=False, ceiling=3, orbs=1),
                n("rock", arc=3.2, step_y=1, hug=2.4, spread=0,
                  pedestal=False, ceiling=3, orbs=2),
                n("accent", arc=4.9, step_y=-2, hug=3.0, spread=0,
                  pedestal=False, orbs=2)]),
    # The vat floor: water cut through the width of the shelf with a bolt
    # of wool standing in it, and the duckboard between two vats walked
    # under the rack beam. This is the reference's answer to ground too
    # wide to be a course -- where the floor is wide, its whole width is
    # hazard, and the landings are single blocks standing in it -- and it
    # is the level's idea, which is why it is also what the filler is.
    #
    # The two vats in the script are eleven metres apart. A moat digs a
    # radius-three bowl at commit, and two any closer means the second
    # stands in the hole the first dug.
    #
    # It ends by climbing the stack at the end of the row, 2.0 / 2.0 /
    # 3.0 / 4.0. That last landing is a fourth node and will be cut about
    # half the time, which is the right place for it: a beat's tail is
    # where a thing goes when it is worth having and not worth losing the
    # beat over.
    ("vats", [n("rock", arc=3.4, lift=1, hug=3.0, spread=1, moat=True,
                orbs=1),
              n("oak", arc=2.9, lift=1, hug=2.8, kind="walk", spread=0,
                pedestal=False, ceiling=3, deco="lintel"),
              n("accent", arc=3.2, lift=2, hug=2.6, spread=0,
                pedestal=False, orbs=2),
              n("rock", arc=3.2, lift=3, hug=2.4, spread=0,
                pedestal=False, ceiling=3, orbs=1)]),
], filler=[
    # The works, repeated, and on the long turns this is most of what the
    # viewer sees -- a script's tail is never laid and the filler is. A
    # bolt on the works floor under the beams, the duckboard between the
    # racks on foot, and up onto a dyed hank. Lifts 1, 1, 2: it never
    # puts two landings at the same height twice running, which is the
    # "a couple of ground-level hops and then a couple higher" complaint
    # written as a rule.
    #
    # The walk is at position two and never last, because a beat lays
    # about half its nodes and a non-hop verb written at the tail is
    # written and never seen. And no ``moat`` anywhere in here.
    #
    # The opener's ``arc`` of 4.4 is arithmetic and not taste, and the
    # paper checker found it: this landing is asked for from three
    # different heights. The loop seam comes round off a hank at surface
    # 3.0, the script hands over off the stack at 4.0, and machinery
    # between them leaves the body on the floor at 2.0 -- so it must be
    # legal at -2, at -1 and level at once. 4.4 is a reach of 3.72
    # against a -2 window that opens at 3.12 and a level one that shuts
    # at 4.26; 3.2 is 2.54 and is refused outright at -2.
    ("hanks", [n("rock", arc=4.4, lift=1, hug=2.8, spread=1, ceiling=3,
                 orbs=1),
               n("oak", arc=2.9, lift=1, hug=2.8, kind="walk", spread=0,
                 ceiling=3, deco="lintel"),
               n("accent", arc=3.2, lift=2, hug=2.6, spread=0,
                 pedestal=False, orbs=2)]),
], exit_beats=[
    # The hoist to the drying loft: a lit bolt at the foot of the rack
    # frame, and the ladder up it. Written out rather than left to the
    # generated climb, because that one hangs its column mid-lane at
    # ``hug`` 2.0 with no pedestal and the only thing it can anchor on is
    # a cliff that leans away -- instrumented elsewhere at 11,097 of
    # 13,000 candidates refused for "no anchor", which becomes a
    # six-tread staircase, a third of the level, with nothing at all
    # reporting it. A works has a hoist to its loft; this is the one
    # place in the level where a climb is the thing the building would
    # actually have.
    #
    # So the column keeps its **pedestal** and the ladder hangs on it:
    # ``_climb_move`` wants solid rock or pedestal within one cell of the
    # column at its middle index and at its top, and ``step_y`` of four
    # or more is what puts that middle cell inside the stack rather than
    # below it. Four and not five, with a rack platform jumped up to
    # first: six blocks of climb is 2.2 s of the strip with the body's
    # face against the column it is hanging on, and that came out as
    # eight consecutive frames of flat plank on the contact sheet -- the
    # worst thing on it. The stair up to the loft is one landing of
    # design in place of two rungs of that. The total is still the six
    # ``rise`` asks for: surface 2.0, 3.0, then four blocks of ladder to
    # 7.0, which is the next terrace, with the crossing coming down onto
    # it. A column that overshoots is the owner's "it puts a ladder there
    # and then jumps back down to a lower part".
    #
    # The launch block sits at ``hug`` 2.8 and that is the level's
    # jammed-lens number, not a preference: measured elsewhere on this
    # tower, 69 wall-jammed frames of 1,293 at 2.2 against 0 of 1,280 at
    # 2.8. ``hug`` on the climb node itself is inert. No ``shell="shaft"``
    # around it either -- the tube is what puts the body inside the wall
    # -- and nothing overhead on the launch, because a lid that will not
    # fit refuses the launch outright and the fallback for a refused
    # ascent node is the generated staircase.
    #
    # **Check ``--report``'s move mix for the word ``climb``.** If it is
    # missing, this is a staircase again and the level has lost a third
    # of itself with no error anywhere.
    n("rock", arc=2.8, lift=1, hug=2.8, spread=1, confine=True,
      deco="lamp", orbs=1),
    n("accent", arc=3.2, step_y=1, hug=2.6, spread=0, confine=True,
      orbs=1),
    n("ladder", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
      hug=2.4, pedestal_style="oak", spread=0, confine=True, orbs=2),
])
