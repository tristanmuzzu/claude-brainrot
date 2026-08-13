"""Level 10: THE APIARY.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A bee yard on a green terrace: a mown meadow with hive stacks standing
# in it, a water trough cut into the ground for the bees, and the great
# comb frame at the end of the yard that the course runs *through*.
#
# One sentence: *you climb the hives, not the ground.* You come in under
# the yard gate on foot, and from the second landing everything you stand
# on is a hive -- a brood box in the trough, the honey super floating
# above it, the top of the stack three blocks off the meadow -- and then
# you come off the end of the row in the level's one long jump, a
# two-block fall into the yard, and cross the trough on a stone.
#
# The colour is the thing to remember, and it is the *floor*: green
# meadow, twelve materials of it, with everything built on it in amber
# honeycomb and hay. The level below is white and blue ice and the level
# above is black basalt and lava, so this is the one green frame in that
# stretch of the tower and it is not confusable with either.
#
# Four things about the machinery decided this table, and each is
# measured rather than chosen:
#
# * **The exit was the level.** With no ``exit_beats`` the way out fell
#   through to the generated staircase: 55 of this level's 140 landings
#   over eight runs -- 39% of everything the viewer saw -- against 63 of
#   design. ``rise`` is 4, the smallest in the tower, so the way out is
#   one launch block and a four-block ladder, and that is what is written
#   below. The generated staircase stays underneath as the fallback;
#   check ``--report``'s move mix for the word ``climb``, and if it is
#   missing this is a staircase again.
# * **``breaks=0``, and it is worth thirteen points of the level.** Any
#   ``breaks >= 1`` forces the lock -- a level's first floor break is
#   always 5.5-6.7 m wide -- and the lock lays three landings in one
#   decision, on a terrace that only has about seventeen. Measured in
#   one process, same roster, same eight seeds, the number swapped on the
#   live ``Level``: breaks 0/1/2/3 give designed content **58.9 / 45.3 /
#   45.3 / 44.9%**, and 1 and 2 are the same world to the decimal because
#   the break positions are ``0.14 + (k + h) * (0.52 / n)`` and both
#   land in the same place. What breaks buy is the walk number, 51.7%
#   against 39.9%, and the two ponds hold that inside the rule on their
#   own. It is the hole a moat digs and not the liquid in it that stops a
#   walker, so the trade is real: with no lock, ``trough`` and ``meadow``
#   go from 1.25 and 1.38 landings a run to 2.62 and 2.25 -- which is the
#   difference between a level that shows its design and one that shows
#   the machinery inserted between it.
# * **``channel`` cost the level its landmark.** The old version cut a
#   two-cell water trough down the middle of the band, which is exactly
#   where ``Course.lane_radius`` puts the running line -- so ``Cone.rock``
#   is False under the lane and the gated comb's base cells never find
#   footing. Measured on the old table: the structure was held at 25
#   degrees for **0.0 s** on the level itself. A plaza gives the frame
#   ground to stand on, and the water comes back as *moats*, which is the
#   reference's own way of doing it anyway: liquid in a hole, under the
#   jump, rather than a ribbon beside it. It is the hole and not the
#   liquid that stops a walker.
# * **The in-body ladder was half the flat frames.** The old design
#   climbed the hive on a ladder as well as leaving on one, and a body on
#   a ladder has its face against whatever the ladder hangs on: 18% of
#   frames were a wall a metre from the lens. There is one climb in the
#   level now and it is the way out. What replaces the verb is the walk,
#   which is reliable, is what the reference actually does at a doorway,
#   and appears three times -- once in each of the two beats a run is
#   certain to lay and once in the filler, always in a beat's reliable
#   middle and never at its tail, because a beat lays about half its
#   nodes and a verb written last is written and never seen. It measures
#   at 13% of all moves and takes the hop share to 82%.
LEVEL = Level("THE APIARY", "honey", rise=4, gap=2.8, exit="ladder",
              band=11.0, profile="plaza", breaks=0, landmark="comb",
              # Green ground, amber everything-that-is-built. The old
              # table made the ground hay as well as the hives, so the
              # whole frame was one value of gold and the hive stacks
              # disappeared into the terrace they stood on -- the same
              # mistake GLACIER SHELF found with pale ice on pale snow.
              ground="grass", sub="podzol", rock="honeycomb",
              accent="honey", glow="lantern", liquid="water", dark=0.32,
              # Twelve materials with the dominant one at a quarter, which
              # is the shape the real map's floors have: one strong colour
              # and a long tail underneath, never a two-tone plate. A
              # working bee yard -- mown meadow and clover, the bare
              # trodden ground round the stands, the forage strip, moss
              # and gravel where the terrace was cut into the hill, and
              # the hay and honeycomb of the yard itself underfoot.
              #
              # Green is 33% of it between grass and moss and that is
              # deliberate: written with grass at 3 of 18 the palette came
              # out a *brown-grey* on the contact sheet, because podzol,
              # coarse, farmland and dirt are all one colour at glance
              # distance and between them they were a third of the floor.
              # The reference's dominant material sits at 26%.
              floor=(("grass", 5), ("podzol", 2), ("coarse", 2),
                     ("farmland", 2), ("hay", 2), ("moss", 2),
                     ("mossy", 1), ("dirt", 1), ("gravel", 1),
                     ("oak", 1), ("honeycomb", 1), ("stone", 1)),
              props=("mcfence", "flower", "grasstuft", "crop",
                     "lanternpost", "scarecrow"),
              # A hazy summer sky rather than the blue the old table
              # borrowed: the level below is a deep blue ice sky and half
              # of every frame here is the thing behind the hives.
              sky=(214, 212, 190),
              step=("hay", "hop"), beats=[
    # The threshold. A lantern set flush in the mown grass on the rise at
    # the yard gate -- the palette stops being white ice at that block --
    # and then the gate itself, *walked* under its crossbar. A lintel is
    # never jumped: one impulse always rises 1.25 m, so the head sweeps
    # the two cells above every take-off and an arc under a beam low
    # enough to read as a gate is refused every time. The beam at three
    # is the genre's 2bc, and a walk is the only leg this motion model
    # can honestly put one over.
    #
    # Then straight off the floor onto the first brood box. Written at
    # ``arc`` 3.2 and not 3.6: a +1 hop reaches 3.10 stand-point to
    # stand-point and 3.6 is a reach of 2.92 against that ceiling, so it
    # is the arc that spends its life falling back.
    ("yardgate", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1,
                    deco="lamp", orbs=1),
                  n("sub", arc=2.9, lift=1, hug=3.0, kind="walk", spread=0,
                    ceiling=3, deco="lintel"),
                  n("rock", arc=3.2, lift=2, hug=2.8, spread=0,
                    ceiling=3, orbs=1)]),
    # The stack, and this is the beat that answers "half the jumps are at
    # ground level". Its four landings stand at one, two, two and three
    # blocks off the meadow and only the first of them has anything under
    # it: a brood box standing in the water it dug, the honey super
    # floating over the trough, the frame board *walked* along the top of
    # the row, and the crown board above it.
    #
    # The walk is at the third position and at ``lift`` 2, and both halves
    # of that were measured. A walk allows 2.4 m of ground and 0.55 of
    # height, so it can be anywhere the landing before it is -- and put
    # down at lift 1 instead, so that the beat is box / walk / super /
    # crown, the same four landings measure **35.6%** of designed landings
    # at lift 2 or above against **43.2%** this way, because the walk
    # spends the beat's reliable middle at ground level instead of on top
    # of the hives. Designed content 61.3% against 62.0%, hop share and
    # exactness identical. It is also the better picture: you run along
    # the roofs of the row rather than beside them.
    #
    # The moat is on the *first* node because it is the landing a short
    # terrace is certain to lay, and everything after it is
    # ``pedestal=False`` because a plinth cannot stand in the radius-three
    # bowl the moat just dug 3.2 m back. Water and not lava on purpose:
    # lava is solid and a no-jump walker strolls over the top of it,
    # water is in ``SEE_THROUGH`` and the walker falls into the hole and
    # cannot climb out. Liquid on its own is atmosphere; liquid in a hole
    # is a barrier.
    #
    # (A third moat was tried under the yard gate's walk and is not here:
    # it changed the world by nothing at all -- design, exactness, move
    # mix and every walk figure identical to the last decimal over eight
    # runs. Recorded as a lead rather than a rule, but do not spend a
    # pass on it.)
    ("stack", [n("rock", arc=3.2, lift=1, hug=2.8, spread=1, moat=True,
                 orbs=1),
               n("accent", arc=3.2, lift=2, hug=2.6, spread=0,
                 pedestal=False, orbs=1),
               n("sub", arc=2.9, lift=2, hug=2.6, kind="walk", spread=0,
                 pedestal=False, ceiling=3),
               n("rock", arc=3.2, lift=3, hug=2.6, spread=0,
                 pedestal=False, ceiling=3, orbs=2)]),
    # Off the end of the row, and this is the level's long jump and its
    # descent. Nothing rises two blocks in one impulse, so the only way
    # to make a jump read as *long* is to step it down: a two-block fall
    # buys a reach of 3.72 where a level hop stops at 4.26 of arc. 4.4 is
    # also the only arc that is legal from every height this node may be
    # asked from -- two down off the crown board when this beat follows
    # the one above it, one down or level when machinery has been
    # inserted between them and left the body back on the meadow, which
    # is about half the time.
    #
    # Then the trough itself, crossed on the one stone standing in it,
    # and up onto the far bank's super. The level's two ponds are
    # fourteen metres apart; a moat digs three cells and two any closer
    # means the second stands in the hole the first dug.
    #
    # The whole descent is inside the first two thirds of the level and
    # nothing after it goes down: the drop from the crown board to the
    # exit ladder's launch is two blocks, under the three the rule
    # allows, and the ladder is the highest thing here.
    ("trough", [n("ground", arc=4.4, lift=1, hug=3.2, spread=2, orbs=2),
                n("rock", arc=3.4, lift=1, hug=3.2, spread=0, moat=True,
                  pedestal=False, ceiling=3, orbs=1),
                n("accent", arc=3.2, lift=2, hug=3.0, spread=0,
                  pedestal=False, orbs=1)]),
], exit_beats=[
    # The hive house at the end of the yard: a lit board hard against the
    # rock, and the ladder up its gable. Written out rather than left to
    # the generated climb, because a level whose exit falls through to the
    # staircase spends seven of its ten landings on it -- and on ``rise``
    # 4 the ladder is only four blocks, which is the shortest ride in the
    # tower and the reason this level can afford a climb at all.
    #
    # The launch keeps its **pedestal** and so does the column. A ladder
    # hangs on something: ``_climb_move`` wants solid rock or pedestal
    # within one cell of the column at its middle index and at its top,
    # and out in the lane the core's lean reaches neither -- floated, the
    # climb is refused essentially always and nothing reports it.
    # ``step_y`` of four is both what this level's rise wants and the
    # smallest that puts the column's middle cell inside the stack.
    #
    # Nothing overhead on the launch board, and that is measured rather
    # than an omission: both lids RULES 7 recommends for an exit were
    # tried on SUNKEN TEMPLE and both cost designed content, because a lid
    # that will not fit refuses the launch outright and the fallback for a
    # refused ascent node is the generated staircase.
    n("rock", arc=2.8, lift=1, hug=2.6, spread=1, confine=True,
      deco="lamp", orbs=1),
    n("ladder", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
      hug=2.4, pedestal_style="oak", spread=0, confine=True, orbs=2),
], filler=[
    # The yard, and this is where the level's character actually lives:
    # the filler repeats and a script's tail does not. A hive box out of
    # the clover, the plank between two stands walked under the rail that
    # carries the frames, and up onto the super above it. Lifts 1, 1 and
    # 2 -- it never puts two landings at the same height in a row, which
    # is the "a couple of ground-level hops and then a couple higher"
    # complaint written as a rule.
    #
    # The walk is at position two and never last: a beat lays about half
    # its nodes, so a non-hop verb written at the tail is written and
    # never seen. And no ``moat`` anywhere in here, which is a rule rather
    # than a preference -- the filler loops, and the second lap digs the
    # ground out from under the pedestals the first lap stood up.
    #
    # The loop seam is checked as a jump like any other: the last landing
    # is a super at lift 2 and the first is a box at lift 1, so coming
    # back round is a drop of one across 3.2 of arc -- a reach of 2.52
    # against a window of 2.35 to 4.98 -- and it stays legal level as
    # well, which is what the ``spread`` on the opener is there to use.
    ("meadow", [n("rock", arc=3.2, lift=1, hug=2.8, spread=1,
                  ceiling=3, orbs=1),
                n("sub", arc=2.9, lift=1, hug=2.8, kind="walk", spread=0,
                  ceiling=3, deco="lintel"),
                n("accent", arc=3.2, lift=2, hug=2.6, spread=0,
                  pedestal=False, orbs=2)]),
])
