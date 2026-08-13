"""Level 32: THE WHITE STAIR.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A white water court: the widest level in the tower, a shallow rill of
# sea running its whole length, gold-trimmed piers standing out of it,
# and the flight of steps the level is named after as the way out.
#
# What it is answering. The level this replaces was the right *idea* --
# the pale, quiet breath between the black shaft and the gate -- built
# as an empty grey plate: one hundred per cent plain hop over ground a
# walker covered 58% of, no liquid anywhere, and a floor whose two
# materials were both the same value as the cone's own stone, so the
# contact sheet came back grey. Elegant is not the same as empty.
#
# Three changes, and they are all the floor rather than the parkour:
#
# * **``profile="channel"``.** At band 13 this is the widest ground in
#   the tower and the reference's answer to wide ground is not a chasm,
#   it is *hazard across the whole width*: a lake with one lit block in
#   it, a room whose floor is lava. The rill is that. It is also the
#   only water in the quartz theme, which has none of its own, and the
#   cut is what a no-jump walker falls into and cannot climb out of.
# * **Eight materials on the floor, not two.** Quartz light, deepslate
#   as the paved stripe down the middle -- the reference paints its
#   route wherever ground could be read two ways -- calcite kerbs,
#   diorite and chiselled quartz in the piers, gold at every trim, and
#   the water blue under all of it. The dominant material still reads
#   white; the tail is what stops it reading as cone stone.
#
#   **The stripe was andesite and andesite is the problem.** (150, 150,
#   148) against quartz's (228, 226, 218) is one value with two names,
#   and this level had *no dark element at all* -- the reference's own
#   composition is the floor as the lightest thing low and the cliff as
#   the darkest thing high, and a court whose every surface sits within
#   thirty points of white cannot have either. ``sub`` is deepslate
#   (92, 92, 100), which is the cone's own stone to within four points,
#   so the stripe, the rim cut under the terrace and the hall's roof all
#   read as the cliff laid into the court rather than as a third grey.
# * **And the gold architraves were not gold.** ``pedestal_style``
#   paints a landing's *ceiling* as well as its plinth, and left unset a
#   ``ceiling=`` lid comes out as ``theme.rock`` -- which on this level
#   is calcite, so every architrave the paragraph below claims was in
#   fact one more white slab over a white court. The three lids over
#   gold piers are gold now, so the trim carries; the one that is not
#   trim is deepslate, because the dark value belongs *high*, the way
#   the reference hangs its cliff over a light floor.
#
#   Both changes are paint and cost nothing -- proved rather than
#   assumed, because the level below moved in the same pass and this
#   level is the next terrace up: with ECHO SHAFT held at its old
#   version, the same twenty runs read 56% designed / 98% exact / 85%
#   plain hop **before and after**. What the contact sheet reads is
#   frames carrying a dark *and* a light value at once: **11 of 30 ->
#   15 of 30**.
# * **Something overhead in every beat.** A gold architrave lidding the
#   doorway, a lid over the piers, and one tall hall shell with its own
#   lamps. A level with nothing above head height always frames as sky,
#   and this one had 51% of the view empty with a clear lens on every
#   frame of the sheet.
#
# The descent is the basin: two piers up and then two blocks down into
# the water, a third of the way in. Nothing after that goes down, and
# the stair at the end is the highest thing in the level -- a level that
# falls after its own high point reads as climb-then-fall, which is the
# note the owner left on the rebuilt twenty.
#
# ``breaks=1`` rather than the plaza's two: the rill does the walker's
# work, and every break past the first costs a lock, which is one to
# three landings of a level that only ever lays nine or ten.
#
# **And no ``landmark``, which was measured rather than assumed.** A
# gold ``hoard`` gate was stood on it and the same eight runs went from
# 67% designed content to 42%, the exit climb from 18 landings to 30,
# and the last two beats of the script -- both of the strides that hold
# the plain-hop share down -- from eight and nine landings to two and
# one, because the landmark crossing is inserted between beats and eats
# whatever is due next. It bought 0.9 s of structure on screen. The
# field note is right that a gated landmark barely reserves on a
# ``channel`` level, and the cost of holding one that the course never
# reaches is paid by the whole rest of the level. The colonnade *is*
# this level's structure: white piers in ranks with a gold architrave
# over them, which is a thing you can name after two seconds and is
# made out of the course itself.
LEVEL = Level("THE WHITE STAIR", "quartz", rise=5, gap=2.8, exit="stair", landmark="arch",
              band=13.0, shelf=4.5, profile="channel", breaks=1,
              ground="quartz", sub="deepslate", rock="calcite",
              accent="gold", glow="lantern", liquid="water",
              props=("lanternpost", "mcfence", "pebbles", "flower"),
              step=("calcite", "hop"), beats=[
    # The threshold. A lantern flush in the quartz with the rill cut out
    # round it, then the doorway -- walked, under a gold architrave.
    # The palette changes completely at that block: eleven seconds of
    # black sculk and amethyst behind, white stone and gold ahead.
    ("threshold", [n("glow", arc=3.2, lift=1, hug=2.6, spread=1,
                     deco="lamp", moat=True, orbs=1),
                   n("ground", arc=2.4, lift=1, hug=2.6, kind="walk",
                     spread=0, ceiling=3)]),
    # The piers and the basin, and the level's descent -- inside one
    # beat, because machinery between beats leaves the body back at
    # lift 1 and a fall written as a beat's first node is not a fall.
    # Two chiselled piers up, then two blocks down onto a calcite bar
    # standing in the water with nothing under it, and a slab kerb out.
    #
    # Everything here hugs 2.4-2.8, on the paved strip between the cut
    # and the cliff. Out over the channel a pedestal has nothing to
    # stand on -- the rill is two cells of ground carved away -- and the
    # same beat written wide loses a third of its landings to
    # recoveries that still read as placed.
    ("piers", [n("chiselled", arc=3.3, lift=2, hug=2.6, spread=0),
               n("ground", arc=2.4, lift=2, hug=2.6, kind="walk",
                 spread=0),
               n("accent", arc=3.3, lift=3, hug=2.8, spread=0,
                 ceiling=2, pedestal_style="gold", orbs=1),
               n("rock", arc=4.9, lift=1, hug=2.8, spread=0,
                 pedestal=False, orbs=2),
               n("sub", arc=3.4, lift=1, hug=2.6, form="slab",
                 spread=0)]),
    # The hall: the one enclosed pinch in the level, tall, with its own
    # lamps in the niches and the colonnade carrying the top of the
    # frame. Two things about it, both of which cost this beat a fifth
    # of its landings when they were got wrong -- the shell goes on the
    # beat's **last** node, because a shell is painted the moment its
    # landing commits and then refuses the move out of it; and the whole
    # beat sits at **lift 1**, because ``_shell`` only grows walls where
    # the terrain gives them a footing and a bay at lift 2 is a roof
    # with open sides, which is not a bay.
    ("colonnade", [n("ground", arc=3.4, lift=1, hug=2.6, spread=0),
                   n("sub", arc=2.4, lift=1, hug=2.6, kind="walk",
                     spread=0),
                   n("accent", arc=3.3, lift=1, hug=2.6, spread=0,
                     ceiling=2, pedestal_style="gold", deco="lamp",
                     shell="hall", orbs=1)]),
    # The far end of the court. Two landings on the paving itself --
    # ``form="floor"`` places no block and asks the terrace to already
    # be there -- then calcite bars standing in the rill with the drop
    # outboard, and one lantern where the ground runs out. Every lamp in
    # the reference is at the far end of the room; there is no ambient
    # decorative light in any frame of it.
    #
    # The paving is deliberate rather than lazy. A no-jump walker covers
    # **1%** of this level once the rill is cut through it, and the rule
    # is "no level walkable end to end", not "no metre walkable": at its
    # widest the reference stops being a course and becomes a place you
    # stroll for a couple of seconds, because the entrance and the exit
    # are still separated by a real break somewhere else. This is the
    # widest level in the tower and it should read as a court.
    ("bars", [n("ground", arc=3.9, lift=0, hug=3.0, form="floor",
                spread=1, orbs=1),
              n("sub", arc=2.4, lift=0, hug=3.0, form="floor",
                kind="walk", spread=0),
              n("rock", arc=3.4, lift=1, hug=3.2, spread=0,
                pedestal=False, orbs=1),
              n("glow", arc=3.4, lift=1, hug=2.8, spread=0,
                deco="lamp")]),
], filler=[
    # The voice, repeated, and on a court this long the filler is a
    # third of the level: the paved stripe, a gold pier under its lid,
    # and a stride through the colonnade. No moat in here -- the filler
    # loops and the second lap digs out the first lap's footings.
    # Both strides sit *second* in their pair rather than last. A beat
    # lays about half its nodes before the machinery clips it, so a verb
    # written at the tail of one is written and never seen: this level
    # read 100% plain hop with a walk in every beat of it.
    ("court", [n("sub", arc=3.4, lift=1, hug=2.6, spread=0),
               n("ground", arc=2.4, lift=1, hug=2.6, kind="walk",
                 spread=0),
               n("accent", arc=3.3, lift=2, hug=2.8, spread=0,
                 ceiling=2, pedestal_style="gold", deco="lamp", orbs=1),
               n("rock", arc=2.4, lift=2, hug=2.8, kind="walk",
                 spread=0, ceiling=3, pedestal_style="deepslate")]),
], exit_beats=[
    # The white stair itself, which is what the level is called and the
    # only thing in the tower that is *meant* to be a staircase rather
    # than reduced to one. Six treads against the core wall, quartz and
    # calcite alternating with a gold newel at the turn, a lantern at
    # the foot and another at the head. No slab in it: a slab stands
    # half a block up and the tread after one asks for +1.5, which no
    # hop in this model has.
    n("ground", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      deco="lamp"),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("accent", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("ground", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, deco="lamp"),
    n("chiselled", arc=3.0, step_y=1, hug=2.6, spread=0, orbs=1),
])
