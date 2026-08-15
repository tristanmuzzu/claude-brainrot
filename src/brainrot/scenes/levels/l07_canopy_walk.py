"""Level 7: CANOPY WALK.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A plank walkway strung through the boughs of a strangler fig, three
# blocks above a flooded forest floor.
#
# One sentence: *you leave the ground on the third landing and you touch
# it once more, on purpose, falling.* The floor of this level is scenery
# -- black standing water, moss and leaf litter, seen from above between
# the boards -- and the route is the walkway: pale oak planks and jungle
# boughs floating at lift two and three with a leaf lid three blocks over
# your head for most of the level. The one thing to remember from a run
# of it is the fall: off the end of the boardwalk, two blocks down and
# four and a half metres out into the swamp, onto a giant red mushroom
# cap standing in the water -- and then straight back up two blocks into
# the boughs off the top of it, which is the only move in this engine
# that gains two.
#
# **The level it replaces was a walk with decorations on it**, and the
# blueprint said so more plainly than any number: the elevation ran along
# the terrace floor line for sixty of its eighty-two metres, touched lift
# three twice, and then went vertical in an orange staircase at the end.
# That is the owner's complaint about the whole roster drawn as a graph.
# The rebuild moves the running line up and leaves the ground where it
# was: the ground is what you *see*, not what you are on.
#
# Five things here are answers to the machinery rather than to taste.
#
# **The lid is painted with ``pedestal_style``, and that is the whole
# composition.** ``Course.write`` paints a ``ceiling=`` lid with
# ``pedestal_style or theme.rock``, and this theme's rock is
# ``junglelog`` -- so every lid in the old version came out as a brown
# beam. On a landing that floats there is no plinth for
# ``pedestal_style`` to paint, so it paints the lid alone: five of the
# level's landings now carry three cells of ``jungleleaf`` at head height
# for nothing, and five more carry the brown bough the default gives.
# The reference's frames are a dark rock brow across the top
# and the level's own colour across the bottom (RULES 5); this level's
# brow is green.
#
# **The way out is the walkway, not a ladder.** The version this
# replaces exited by the generated climb, and the contact sheet of it has
# *six consecutive frames of flat brown plank* -- that climb's own oak
# column, at arm's length, with nothing else in the lens. It was most of
# a 16% jammed-lens figure, the worst row this level had, and it is 0.0%
# now. It was also one of the seventeen levels in twenty exiting by a
# climb against the reference's one in six, and this level's idea is a
# walk. So the exit is written out: a lit last board, then three more
# each a block higher, the last two floating clear over the chasm with
# nothing overhead, so the final thing before the leap is a lit floor and
# a view of where you are going.
#
# **``gap=2.2``, and it is the exit's arithmetic rather than a taste in
# chasms.** The crossing is a fixed ``gap + 1.4`` of arc from wherever
# the treads finished, and at 2.2 that is a reach of 2.86 -- legal *up*
# one (which stops at 3.10), level, and down one. So the treads may
# finish one block **below** the next level's floor and still make it,
# which is what lets this exit be four landings instead of six: the
# launch board is an absolute ``lift=3`` with two of fallback, three
# ``step_y`` treads follow it, and the three arrival heights that
# actually occur -- lift 2, 3 and 4 -- all land the last tread within
# that window. At the 2.6 this started on, a +1 crossing is illegal and
# the exit needs a fifth tread to be safe; measured, that fifth tread
# cost **five points of designed content** (59% against 54%), because a
# landing of exit is a landing of terrace the script does not get.
#
# ``exit="vine"`` is a *reserve declaration* and not the way out, and it
# is worth being plain about. Once ``exit_beats`` is written the field
# has one job left: ``handplan._level_budget`` reserves ``(need + 1) *
# 3.2`` blocks of terrace for a ``stair`` and a flat three landings for
# anything else, and this exit costs four. Declaring the stair reserved
# ten blocks nothing was going to spend and truncated the level's own
# showpiece out of the run. The vine is also the right fallback for a
# jungle if the authored exit ever cannot be built.
#
# **``breaks=0``.** Any break at all forces the lock -- a level's first
# floor break is always 5.5-6.7 m wide and the lock is three or four
# landings and fifteen metres of arc -- and this level already spends
# fifteen on the gated fig. Between them they left ten metres of an
# eighty-metre terrace for the design last time. The walk number is held
# down instead by the two ponds and by the fact that three quarters of
# the landings are two or three blocks over the ground with nothing under
# them: a walker on the terrace can walk the terrace, and the terrace is
# not the route. Measured over 24 runs it covers 21% of the level and 0
# of 15 walks got down it.
#
# **Nothing stands higher than lift 3.** ``_lm_g_tree`` hangs its canopy
# at five and six blocks over the terrace, so a body at lift 4 has its
# eyes at 5.6 and is standing *in* the leaves; the first rebuild of this
# level climbed to 4 and a whole row of the contact sheet came back solid
# green. At 3 the same leaves are a foot over the head, which is the
# thing this level is for.
LEVEL = Level("CANOPY WALK", "jungle", rise=6, gap=2.2, exit="vine",
              band=7.5, profile="ledge", shelf=5.0, breaks=0,
              landmark="tree",
              ground="moss", sub="podzol", rock="junglelog",
              accent="jungleleaf", liquid="water", glow="lantern",
              props=("vinehang", "bamboo", "grasstuft", "flower",
                     "mushroomcap", "lilypad"),
              # Twelve materials with moss at 23% and nothing else over a
              # sixth, which is the shape a real terrace measures as (a
              # median 14 kinds, dominant share 26%). The jungle theme's
              # own mix is a third brown -- podzol, junglelog, coarse,
              # dirt, gravel, bamboo -- and painted a jungle that came
              # back the colour of a woodpile. Green is pulled forward
              # and ``oak`` is deliberately *not* in here: the pale
              # planks of the walkway are the one thing in the level that
              # is built rather than grown, and they only read as built
              # if the ground is never made of them.
              floor=(("moss", 3), ("podzol", 3), ("grass", 2),
                     ("jungleleaf", 2), ("mossy", 2), ("coarse", 2),
                     ("vine", 1), ("dirt", 1), ("gravel", 1), ("clay", 1),
                     ("bamboo", 1), ("junglelog", 1)),
              candy=("jungleleaf", "moss", "bamboo"),
              step=("oak", "hop"),
              sky=(116, 178, 126), dark=0.30, beats=[
    # The threshold. A lantern set flush in the moss on a rise, then the
    # fig's lowest bough, ducked under at a walk. The palette goes from
    # the badlands' orange terracotta to green in one block, which is
    # what the reference's seams do -- nine of them in two minutes, every
    # one abrupt.
    #
    # It is walked and not jumped because it cannot be jumped: one
    # impulse always rises 1.25 m and the head then sweeps the two cells
    # above every take-off, so a lintel low enough to read as a bough is
    # a lintel no arc gets under. ``ceiling=3`` is the genre's ``2bc``
    # -- the lid you sprint under -- and a walk is the one leg this
    # motion model can honestly put one over.
    ("sill", [n("glow", arc=3.0, lift=1, hug=2.8, spread=1, ceiling=3,
                deco="lamp", orbs=1),
              n("mossy", arc=2.9, lift=2, hug=2.8, kind="walk", spread=0,
                ceiling=3, deco="lintel", shell="cave")]),
    # **The whole level is this beat**, and it is five nodes rather than
    # two beats of two and three because of where the terrace runs out.
    # Measured on the version this replaces, which split it: beat two was
    # laid whole on seven runs of eight and beat three laid *one* landing
    # of its three, because ``_truncate`` clips the last feature before
    # the exit reserve and the first thing it eats is the longest arc in
    # it -- which was the fall. The showpiece was written down and never
    # happened. Beats one and two are the reliable ones on this engine;
    # anything a level actually wants seen goes in them.
    #
    # Five landings, and each asks something different:
    #
    # * **the deadfall** -- a fallen bough two blocks up with black water
    #   standing round its foot, the pond dug by the landing itself. A
    #   +1 hop at arc 3.2, a reach of 2.52 against a window that stops at
    #   3.10: centred, not at the top of it, because 3.6 is a reach of
    #   2.92 and is the arc that has to fall back. It opens at lift 2 and
    #   not lift 1 -- a beat's opener is placed from wherever machinery
    #   left the body, which is always lift 1, and +1 from there is legal
    #   every time. Two landings on the floor is a threshold; four is the
    #   walk with decorations on it that this rebuild exists to end.
    # * **the first board** -- 1.92 m on foot, no jump at all. A plank
    #   laid from the bough across the water, floating, crossed at a
    #   walking pace. It is at position two and not at the tail because a
    #   beat lays about half its nodes and a verb written last is written
    #   and never seen. It carries ``spread=1`` for the same reason its
    #   predecessor does: a walk needs its take-off within half a metre,
    #   so if the opener fell a block it has to be able to fall with it.
    # * **up onto the walkway** -- the last +1, onto a floating oak board
    #   with three cells of leaf overhead. This is where the level stops
    #   being a terrace, and everything after it is three blocks up.
    # * **the fall** -- lift 3 to lift 1, arc 5.2, a reach of 4.52
    #   against a two-block-drop window of 3.12 to 5.56. The longest jump
    #   in the level and the only kind of long jump this motion model
    #   has: falling takes time and the body does not slow down while it
    #   does. It lands on a giant red mushroom cap standing in the water
    #   it digs -- the level's descent, its long jump and its bounce pad
    #   in one landing, and the thing a viewer would remember.
    #
    #   5.2 and not 4.9, and this is arithmetic rather than feel.
    #   ``_node`` offers ``arc * 0.84`` as a fallback, and a bounce fires
    #   on the speed the *arrival* had: two blocks of gain wants
    #   ``impact >= 11.0``, a two-block drop across 4.42 m arrives at
    #   11.68 and across the 0.84 fallback of a 4.9 arc at 10.91 -- under
    #   it, so the bounce silently becomes an ordinary hop with the beat
    #   still reading as placed. At 5.2 the fallback still arrives at
    #   11.13.
    # * **the bounce** -- lift 1 to lift 3, straight back into the
    #   boughs. Two blocks in one move, which nothing else in this engine
    #   does: a ballistic hop has no solution for +2, here or in vanilla.
    #   ``spread=1`` so a feed that arrived a little slow degrades to a
    #   one-block throw instead of failing, and ``pedestal=False`` on the
    #   pad because at the foot of a fall there is no terrace for a stack
    #   to find -- with a pedestal the pad is only offered cells that
    #   have ground under them and it is refused about half the time.
    #
    #   The pad is a mushroom and not slime, and that is free: ``SPRINGY``
    #   is imported by ``spiralplan`` and never read, so the physics is
    #   entirely ``kind="bounce"`` against the previous landing's impact
    #   and the *material* is a colour. A green slime cube in a jungle is
    #   a video game; a red cap in the leaf litter is a place.
    #
    # The two ``moat`` landings are fourteen metres apart, which they
    # have to be: the pond is a radius-three bowl dug the moment its
    # landing commits, and a second one inside that radius stands in the
    # hole the first made.
    ("boardwalk", [n("junglelog", arc=3.2, lift=3, hug=2.6, spread=1,
                     moat=True, ceiling=3, orbs=1),
                   n("oak", arc=2.6, lift=3, hug=3.0, kind="walk", spread=1,
                     pedestal=False),
                   n("oak", arc=3.2, lift=4, hug=3.2, spread=0,
                     pedestal=False, pedestal_style="jungleleaf", ceiling=3),
                   n("mushroomred", arc=5.2, lift=2, hug=2.8, spread=0,
                     pedestal=False, moat=True, orbs=2),
                   n("junglelog", arc=3.4, lift=4, hug=3.0, kind="bounce",
                     spread=1, pedestal=False, orbs=3)]),
    # The spur, and it is the level's turn signal: the walkway branches
    # out past the edge of its own shelf on a bough that leans over the
    # drop, with the level's second lantern on the tip of it. The
    # reference does this and this tower has not -- a lamp post at the
    # end of the promontory where the course turns, nothing decorative
    # in the middle distance, and a silhouette against sky rather than
    # against the cliff, which is the only kind that reads at speed.
    #
    # ``hug=5.0`` is past the shelf on about half the bearings -- a
    # ledge's width wobbles about 1.3 either side of the 5.0 it asked
    # for -- so the landing floats over nothing, which is the point, and
    # ``pedestal=False`` is therefore not optional but structural.
    ("spur", [n("oak", arc=3.4, lift=4, hug=3.4, spread=2, pedestal=False,
                pedestal_style="jungleleaf", ceiling=3),
              n("glow", arc=3.2, lift=4, hug=5.0, spread=1, pedestal=False,
                deco="lamp", orbs=2)]),
], filler=[
    # The walkway itself, and on a terrace this long it is a third of
    # what is seen -- measured over 24 runs, a visit lays about fourteen
    # designed landings and five of them are this loop, which is more
    # than any single beat gets. Three boards that close into a loop,
    # weaving in and out
    # across the corridor on their ``hug``: a plank two and a half metres
    # off the cliff, a mossy board crossed on foot, and a bough that
    # leans out past the shelf edge over the drop.
    #
    # The loop's seam is the thing half a filler's fidelity is usually
    # lost to, so it is written rather than hoped for: the bough at lift
    # 3 back down to the plank at lift 2 is a one-block drop across 3.4
    # of arc, a reach of 2.72 against a window of 2.35 to 4.98.
    #
    # No ``moat`` anywhere in here, and that is not taste. The filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on -- one keyword in a filler once produced
    # 27,859 "pedestal will not stand" refusals. This level's water is
    # the two ponds in the script.
    ("understory", [n("oak", arc=3.4, lift=4, hug=2.6, spread=1,
                      pedestal=False, pedestal_style="jungleleaf",
                      ceiling=3, orbs=1),
                    n("mossy", arc=2.6, lift=4, hug=3.0, kind="walk",
                      spread=0, pedestal=False,
                      pedestal_style="jungleleaf", ceiling=3),
                    n("junglelog", arc=3.2, lift=4, hug=3.4, spread=0,
                      pedestal_style="junglelog", orbs=1)]),
], exit_beats=[
    # The way out is the walkway carrying on: four boards climbing the
    # last boughs, the first two on trunks that go down to the forest
    # floor and the last two hanging clear over the chasm. The generated
    # climb is still underneath as the fallback.
    #
    # **The launch board is an absolute ``lift`` and the three after it
    # are ``step_y``**, and the split is what makes four landings enough.
    # A ``lift`` is measured from the level's own floor, so ``lift=3`` at
    # ``spread=2`` pins the height whatever the filler or a doorway left
    # the body at -- from lift 1 the ballistic clamp puts it at 2, from
    # lift 3 or 4 it takes the height it asked for. From there the three
    # treads must be ``step_y``, because the level's floor means one thing
    # on this side of the chasm and six blocks something else on the
    # other, and the last two are already over the boundary.
    #
    # ``arc=2.9`` is a reach of 2.22, and both of the longer fallbacks a
    # ``step_y`` node is offered -- 1.14 and 1.28 -- are 2.63 and 3.03,
    # still inside the +1 window that stops at 3.10. A shorter arc would
    # be worse than useless: the shorter fallback is not offered to a
    # ``step_y`` node at all, precisely because it lands under
    # ``MIN_HOP``.
    #
    # The first three carry a leaf lid and the last does not, and that is
    # the one place in the level where the sky is *wanted*: the exit climb
    # is the emptiest third of any level in this tower, but it is also the
    # only place the run needs to see where it is going, and a roofed leap
    # into a hole reads as a wall. Lidding some landings and not all is
    # also what keeps the level lit -- ``_indoor_want`` returns 0.85
    # within eight blocks of a lid, which takes 27% off every tint.
    #
    # The two ``pedestal_style="junglelog"`` treads are the frame lever
    # here, not the lids: a tread standing on its own column of trunk is
    # mass under the eye where an open shelf has nothing, and it took the
    # empty frame from 44% to 42% at no cost to fidelity at all.
    n("oak", arc=3.2, step_y=0, hug=2.8, spread=2, pedestal_style="junglelog",
      ceiling=3, orbs=1),
    n("junglelog", arc=2.9, step_y=1, hug=2.6, spread=0,
      pedestal_style="junglelog", ceiling=3),
    n("oak", arc=2.9, step_y=1, hug=2.8, spread=0, pedestal=False,
      pedestal_style="jungleleaf", ceiling=3, orbs=1),
    n("glow", arc=2.9, step_y=1, hug=2.6, spread=0, pedestal=False,
      deco="lamp", orbs=2),
])
