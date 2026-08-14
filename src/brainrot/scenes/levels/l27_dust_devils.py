"""Level 27: DUST DEVILS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A hoodoo field standing out of a dry wash, and the route goes over the
# **tops** of it.
#
# The place in one line: the wind has eaten the rim away into a stand of
# thin banded spires with white capstones, the wash they stand in still
# holds one green pool, and the only water left in the badlands is coming
# back *up* a chimney at the head of the slot.
#
# The route: a lantern set flush in the red sand, a stride under the slab
# leaning across the mouth of the slot, up the shoulder of the first
# hoodoo and onto its cap -- and then **off the undercut side of it, two
# blocks down and four and a half metres out**, into the pool at the
# bottom of the wash. You wade it, squeeze under the boulder wedged
# across the slot, climb the strata back out on an eroded half-step into
# a wind-hollowed bay, and cross the hoodoo field itself: three spires
# weaving across the lane, the middle one hanging over the wash on
# nothing. The way out is the seep -- a block to launch from with the
# rock closing over it, the spring pushing water up the chimney, and a
# lit shelf on the rim to leap from.
#
# The thing to remember is the fall off the capstone: it is the longest
# jump in the level, it is the level's descent, and it is written into
# the one beat that is laid on every single run.
#
# ---------------------------------------------------------------------
# **The way out is now three landings, and that is the biggest single
# change in the file.** What was here was an eight-tread authored
# staircase -- itself a rebuild, and a real improvement on the generated
# one -- but measured over eight runs it was **76 of 225 landings, 34% of
# everything the viewer sees**, and the blueprint's elevation was the
# owner's complaint drawn as a picture: forty metres of design lying flat
# on the terrace, then forty metres of evenly spaced orange staircase
# climbing away from it. The contact sheet agrees. The level opens hot
# orange and ends grey, because the cliff a staircase rides is
# ``CLIFF_MIX`` and only five parts in twenty-six of that are the level's
# own colour.
#
# Two mechanisms, and the second is the one that is easy to miss:
#
# * **A climb spends three landings whatever the height; a stair spends
#   one a block.** ``rise=7`` is near the tallest in the tower, so the
#   stair was always going to be seven or eight of them.
# * **``Cone._level_budget`` reserves the terrace for the *kind* of exit
#   the level declares, before a single beat is laid** -- and for
#   anything but ``"stair"`` it gives back ``(need - 2) * ASCENT_ARC``,
#   which here is **sixteen metres of an eighty-one metre corridor**.
#   That is why this level could only ever lay its first two beats: the
#   third and the filler were writing for terrace the exit had already
#   booked.
#
# So ``exit="bubble"``: the spring at the head of the wash. It is the one
# thing in a dry level that is wet, the pool in the wash below is the
# same water, and it is the level's *idea* rather than a way of getting
# out -- which is the test ``docs/RULES.md`` §3 sets for spending a climb
# on a level at all. A bubble is ridden at 11.0 m/s against a ladder's
# 2.35, so the ride is a fifth of a second rather than three, and the
# brief's measurement on the ladder -- the ride 20.9% jammed against
# 0.0% for every other move in the level -- cannot arise.
#
# THE GROVE below also leaves by a bubble and that is the one real cost
# here; it is taken deliberately. Its column is a bare six-block ride out
# of a teal nylium floor. This one is five blocks with the rock shelled
# over the launch and **two lit terracotta shelves above it**, so the
# last thing before the leap is a floor rather than the top of a shaft,
# and ten seconds of orange badlands stand between the two rides.
#
# ---------------------------------------------------------------------
# Three other things that are measurements rather than taste.
#
# * **Beat one carries the whole level.** Over eight runs the old
#   ``rimlight`` laid 30 of 30 and ``wash`` 37 of 40, while ``hoodoos``
#   managed 13 of 16 and the filler 6 of 7 -- the level gets about three
#   visits and the script is truncated in the middle of whichever beat is
#   in progress. So the threshold, both rises, the fall and the water are
#   all in the first beat, in that order, and beats two and three are
#   what the level does with the room the exit gave back.
# * **Only the opening beat is written at ``lift=1``.** It is placed from
#   wherever the ``start`` machinery left the body, and the identical
#   beat measures 67% at lift 2 against 100% at lift 1. Every *other*
#   beat opens at ``lift=2, spread=1`` and then works in ``step_y``, so
#   the shape it was written with survives an opener that settled a block
#   off -- and the level stops spending its first four landings on the
#   floor, which is the owner's complaint measured (55% of the roster's
#   authored landings sit at lift 0-1; nine of this level's thirteen used
#   to).
# * **``shelf=6.0`` inside ``band=10.5`` is kept from the pass before
#   this one**, where it was measured against 4.0 inside 9.5: the fan's
#   bottom row went 32% -> 19% empty and the row under the horizon 44% ->
#   33%, *and* fidelity improved, because a pedestal on a ledge then has
#   ground to find. It contradicts the "a wide shelf costs the exit climb
#   its lane" note in ``docs/RULES.md`` §7, which was measured at
#   ``band=9.0``; with a block of band to spare it does not hold.
#
# And the floor is written out. ``docs/RESEARCH.md`` says identity comes
# from the ground -- a real terrace runs a median fourteen materials with
# the commonest at 26% -- and the mesa family mix underneath this one is
# a fifth grey (``clay`` is (166,170,180), ``stone`` is (146,146,150)).
# What is here is fifteen kinds and none of them cold: burnt orange, red
# and yellow bands, terracotta, fired brick, oxidised copper, coarse
# dirt, two sands, with gravel and a little clay for grit.
#
# Against THE BALCONIES, the other mesa level, this is a deliberate
# opposite. That one is *bolted to the cliff* -- oak-and-clay decks hung
# off a banded face, a lava seep, everything hugging the wall. This one
# stands *free of it*: spires with air all round them, the drop on one
# shoulder and the wash on the other, water instead of lava, and no
# timber anywhere in it.
LEVEL = Level("DUST DEVILS", "mesa", rise=7, gap=3.0, exit="bubble",
              band=10.5, profile="ledge", shelf=6.0, breaks=3,
              landmark="hoodoo",
              ground="redsand", sub="terra_orange", rock="terra_red",
              accent="terra_white", glow="lantern", liquid="water",
              candy=("terra_yellow", "terra_white"),
              props=("deadbush", "pebbles", "cactus", "mcfence",
                     "grasstuft"),
              sky=(238, 178, 116),
              step=("terra_yellow", "hop"),
              # Fifteen materials with the commonest at 17%, against the
              # roster's usual six at 55%. The four roles are added on
              # top of this at high weight by ``Theme.floor_palette``,
              # so the list below is the tail -- and it is the mesa
              # family's own tail with the two grey entries taken out
              # and warm ones put in: fired brick and oxidised copper
              # for the baked crust, sandstone and sand for the wash
              # bed, coarse dirt and podzol for the scree.
              floor=(("terra_orange", 3), ("terra_red", 3),
                     ("terra_yellow", 3), ("redsand", 2),
                     ("terracotta", 2), ("coarse", 2), ("sandstone", 2),
                     ("brick", 2), ("copper", 1), ("sand", 1),
                     ("chiselled", 1), ("dirt", 1), ("podzol", 1),
                     ("gravel", 1), ("clay", 1)),
              beats=[
    # THE CAPSTONE -- the threshold, both rises and the fall, in the one
    # beat that is never truncated. Every other beat here is what the
    # level does with whatever terrace is left; this is what it *is*.
    #
    # 1. A lantern set flush in the red sand on a rise, with the rock
    #    closing seven cells over it. The palette changes completely at
    #    that block -- THE GROVE below is teal warped nylium and
    #    shroomlight, and from here it is burnt orange -- which is what
    #    the reference does at every one of its nine seams, in one or two
    #    frames with no blend. `lift=1` and not 2, because a beat's
    #    opener is placed from wherever machinery left the body: the
    #    identical beat reads 67% at lift 2 and 100% at lift 1.
    # 2. The stride under the slab leaning across the mouth of the slot.
    #    A body cannot jump through a gap this low -- one impulse rises
    #    1.25 m and the head then sweeps the two cells above every
    #    take-off -- so the lintel is a `ceiling=3` and the leg under it
    #    is a `walk`. This is the genre's `2bc`, the lid you sprint
    #    under, and it is the only form of it this kernel has. It asks
    #    for the *same* `lift` as the opener, which is the whole reason
    #    it survives an opener that settled a block off: +1, level and -1
    #    are all legal, and `lift + 1` after a spread opener is a rise of
    #    two about a fifth of the time, which nothing makes.
    # 3. Up the weathered shoulder of the first hoodoo. +1 at `arc` 3.2
    #    is a reach of 2.52 against a +1 window of 2.00-3.10 -- centred,
    #    not at the top of it, because 3.6 is the arc that has to fall
    #    back and a fallback is not `exact`.
    # 4. **Onto the capstone**, +1 again, and this is the second landing
    #    of the level that is off the floor. `pedestal_style` paints the
    #    plinth under it: an orange banded column with a white cap on top
    #    of it *is* a hoodoo, and it costs nothing.
    # 5. **Off the undercut side of it.** `step_y=-2` at `arc` 5.2 is a
    #    reach of 4.52 against a -2 window of 3.12-5.56, and it is the
    #    longest jump in the level by a metre and a half -- a descent is
    #    the only long jump this motion model has, because falling takes
    #    time and the body does not slow down while it does. It lands at
    #    lift 1 and not lift 0 on purpose: lift 0 is the terrace's own
    #    top cell, which is solid, so the landing would be refused and
    #    the rest of the beat abandoned behind it under the beat's own
    #    name. The `moat` is on this node because the pool has to be
    #    *under* the jump rather than beside it, and because a bowl dug
    #    here is a hole a no-jump walker can get into and not out of --
    #    which is the mechanism that moves the walk number, not the
    #    water.
    # 6. The wade across the last of it onto the sand bar. It floats: the
    #    moat one node back has just dug a radius-three bowl and a
    #    pedestal cannot stand in a hole.
    ("capstone", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1,
                    deco="lamp", ceiling=7, orbs=1),
                  n("terra_white", arc=3.0, lift=1, hug=3.2, kind="walk",
                    spread=0, ceiling=3),
                  n("terra_orange", arc=3.2, step_y=1, hug=3.4,
                    pedestal_style="terra_red", ceiling=7, orbs=1),
                  n("terra_white", arc=3.2, step_y=1, hug=3.0,
                    pedestal_style="terra_orange", orbs=1),
                  n("terra_red", arc=5.2, step_y=-2, hug=3.8, moat=True,
                    orbs=2),
                  n("redsand", arc=3.0, step_y=0, hug=3.4, kind="walk",
                    spread=0, pedestal=False)]),
    # THE SLOT -- the bottom of the wash, and the only enclosed stretch
    # in the level. The reference is a *groove* rather than a tunnel:
    # rock within four metres on one side on 71% of its samples, a lid
    # overhead on 98%, and fully enclosed only 6% of the way. So this is
    # a two-metre pinch and not a room -- a lid to sprint under, a
    # half-step up the strata, and one bay carved into the bank.
    #
    # It opens at `lift=2` with `spread=1`, which is the one real lever a
    # level has against "half the jumps are at ground level": following
    # another script beat that measures 100% exact, and following
    # machinery the spread covers the fallback. Everything after the
    # opener is on `step_y`, so a beat that started a block low still has
    # the shape it was written with.
    #
    # The `slab` is the fourth node: the commonest non-cube form in the
    # whole reference map, and a form this tower has barely used. Note
    # what it does *not* buy here -- `form="slab"` is a half-height step
    # only when the rise is written as `lift + 1`; written as `step_y=1`
    # the rise between walking surfaces is a full block whatever the
    # form, and `--design-only` says so. So it is an eroded ledge to look
    # at and an ordinary +1 to jump, and its `arc` is centred at 3.2 like
    # every other +1 in the file.
    #
    # The beat then **drops into the bay** rather than climbing into it.
    # A grotto is a hollow the wind has cut into the bank, and you get
    # into one by stepping down off the ledge above it; -1 at `arc` 4.0
    # is a reach of 3.32 against a -1 window of 2.35-4.98, which is
    # further than any rising jump in the level can go. It also leaves
    # the beat at lift 3 rather than 5, so THE FIELD's opener at lift 2
    # is a one-block descent instead of the three-block one nothing
    # makes.
    #
    # The `grotto` is on the beat's **last** node, which is the only
    # place a shell may go: it is painted the moment its landing commits
    # and its walls would then be in the way of the next landing of the
    # same beat.
    ("slot", [n("terra_yellow", arc=3.2, lift=2, hug=3.0, spread=1,
                ceiling=7, orbs=1),
              n("terra_white", arc=3.0, step_y=0, hug=3.0, kind="walk",
                spread=0, ceiling=3),
              n("terra_orange", arc=3.2, step_y=1, hug=3.4,
                pedestal_style="terra_red", orbs=1),
              n("terra_yellow", arc=3.2, step_y=1, form="slab", hug=3.2),
              n("terra_red", arc=4.0, step_y=-1, hug=3.0, shell="grotto",
                orbs=1)]),
    # THE FIELD -- the hoodoos themselves, and the level's high ground.
    # Three spires weaving across the lane: one out toward the rim, the
    # middle one hung over the wash on nothing at all with a beam drawn
    # across the jump onto it, the last and tallest back inboard. Then a
    # stride across the wind-cut bridge between the last two caps, with
    # the rock closed over it.
    #
    # `radial` is what makes this read as a *field* rather than as a line
    # of blocks: +1.2 then -1.3 puts two and a half metres of side-step
    # between consecutive caps, so the lane visibly weaves and the spires
    # stand off each other. The middle one is `pedestal=False` because a
    # column of rock under it would make it a buttress; a hoodoo that has
    # lost its own footing is the thing worth looking at.
    #
    # This ends at lift 4 and nothing after it goes down more than two,
    # which is `docs/RULES.md` §3: a level's descent belongs in its first
    # two thirds and the exit is the highest thing in it.
    ("field", [n("terra_white", arc=3.4, lift=2, hug=3.2, spread=1,
                 radial=1.2, pedestal_style="terra_orange", orbs=1),
               n("terra_red", arc=3.2, step_y=1, hug=3.6, radial=-1.3,
                 pedestal=False, deco="lintel"),
               n("terra_yellow", arc=3.2, step_y=1, hug=3.0,
                 pedestal_style="terra_red", ceiling=7, orbs=1),
               n("terra_white", arc=3.0, step_y=0, hug=3.2, kind="walk",
                 spread=0, shell="tunnel")]),
], filler=[
    # THE WINDGAP, repeated. A script's tail does not repeat and the
    # filler does, so the level's *character* lives here rather than its
    # surprise: along a bench under the overhang, off the end of it and
    # down one out over the wash -- the longest flat-ish jump the level
    # owns after the capstone fall -- and back up a stratum onto the next
    # bench.
    #
    # It neither climbs nor sinks across a lap. lift 3, 3, 2, 3, and the
    # seam back onto the opener is a level hop at `arc` 3.4. Half of what
    # a filler ever loses is at that seam, and a filler that drifted
    # downhill would also buy the level a longer exit every lap, since
    # the exit is sized from wherever the body is when it triggers.
    #
    # **No `moat` anywhere in here.** The filler loops, and a second lap
    # digs away the ground the first lap's pedestals are standing on --
    # one keyword, 27,859 refusals.
    ("windgap", [n("terra_orange", arc=3.4, lift=3, hug=3.0, spread=2,
                   ceiling=7, orbs=1),
                 n("terra_white", arc=3.0, step_y=0, hug=3.0, kind="walk",
                   spread=0, ceiling=3),
                 n("terra_yellow", arc=4.6, step_y=-1, hug=3.6, orbs=1),
                 n("terra_red", arc=3.2, step_y=1, hug=3.0,
                   pedestal_style="terra_orange")]),
], exit_beats=[
    # THE SEEP -- the spring at the head of the slot, and the only water
    # in the badlands that is going anywhere.
    #
    # Three landings against the eight-tread staircase this replaces, and
    # the arithmetic of the height is the part to check if anything here
    # is ever touched: the launch is lift 2, the column gains five, the
    # shelf one -- lift 8, against the next terrace's floor at `rise` 7
    # plus the one block the crossing comes down. An exit that overshoots
    # is a level above that opens by dropping onto its own terrace, which
    # is the owner's "it puts a ladder there and then jumps back down to
    # a lower part". The old stair reached lift 9 and the seam showed it:
    # the first landing of THE SEA GATE was built two cells *below* the
    # last landing of this level.
    #
    # `pedestal=True` and `step_y=5` are the recipe and both are
    # load-bearing. `_climb_move` wants solid rock within one cell of the
    # column at its **middle index** and at its **top**, and out in the
    # lane the only candidate is the landing's own stack; floated, the
    # column is refused silently -- 11,097 of 13,000 candidates on a
    # generated bubble exit -- and the level gets a staircase without
    # being told. **Check the move mix for the word `bubble` by name
    # after touching anything here**; its absence reads as 100% placed.
    # `arc=2.4` for the same reason: 3.0 often does not fire.
    #
    # The launch block stands at `hug=2.8` and not 2.2, and that one
    # number is most of a level's jammed lens -- measured elsewhere, 69
    # wall-jammed frames of 1,293 at 2.2 against 0 of 1,280 at 2.8. Its
    # `shell="cave"` takes the chimney out of the climb's own reserved
    # cells for free, which is the single biggest thing a level can do
    # about the exit being the emptiest third of it. And both ends carry
    # a `ceiling` beam, because a beam is spread along the direction of
    # travel and fills the one column of the ray fan that looks where you
    # are going.
    # `arc=3.4` on the launch is chosen to be legal at *every* height the
    # thing before it can leave the body at: a reach of 2.72 sits inside
    # the +1 window (2.00-3.10), the level one and the -1 one (2.35-4.98)
    # at once, which 2.8 does not -- 2.12 of reach is under a descent's
    # minimum, because a descending arc covers that much ground before it
    # arrives.
    n("terra_orange", arc=3.4, lift=2, hug=2.8, spread=1, confine=True,
      ceiling=3, shell="cave"),
    n("terra_white", arc=2.4, step_y=5, kind="bubble", hug=2.0,
      pedestal=True, pedestal_style="terra_orange", spread=0, deco="lamp",
      orbs=2),
    n("terra_yellow", arc=3.0, step_y=1, hug=3.2, spread=0,
      pedestal=False, ceiling=3, deco="lamp", orbs=1),
])
