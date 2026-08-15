"""Level 9: GLACIER SHELF.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A crevasse in a blue glacier, and the level is the crevasse: you climb
# the seracs, fall into the split, run along the bottom of it, and climb
# out of the far wall.
#
# The route, in one breath. A lantern set flush in the snow, then a walk
# under the ice lintel where two seracs have leaned together over the
# shelf. Then **up the seracs on ice** -- three slides, one block each,
# to four blocks above the terrace, which is as high as anything in this
# level stands. Then **off the top of them**, three blocks down and 4.6
# metres out into the split: the showpiece, the level's only long jump,
# and the only kind of long jump this motion model has, because falling
# takes time and the body does not slow down while it falls. It lands on
# a floe with nothing under it, over the meltwater at the bottom of the
# crevasse. Down there the roof closes over -- a stone in the pool and a
# walk under the ice, which is the one place in the level with rock on
# both sides and above. Out of the cave the shelf has calved: pans of
# ice floating off the rim with the sea a long way under them. And the
# way out is the **moulin** -- the shaft the meltwater drills down
# through a glacier, run backwards: a column of water coming up the
# crevasse wall, with a lit lip at the top of it to stand on before the
# leap across.
#
# Four things here are answers to a measurement rather than to taste.
#
# **The climb and the fall are one beat.** Machinery -- the landmark
# crossing, a recovery hop -- is inserted *between* script beats and
# leaves the body back at lift 1, so a rise written in one beat and
# spent in the next is a rise that does not happen. The version this
# replaces climbed to lift 3 in `seracs` and then opened `crevasse` with
# a two-block drop; that beat measured 71% while every other beat in the
# level measured 100%, and it is the only beat here that ever missed.
#
# **The bounce pad is gone, and with it the green cube.** The old
# showpiece was a slime pad at the bottom of the split throwing the body
# back out. Two things wrong with it: a bounce is the least reliable
# verb in the kernel (measured elsewhere at 6 placements in 24 runs and
# one firing), and a slime block is *green* -- on the contact sheet of
# the old version it is the single brightest thing in a level that is
# otherwise white and blue, and it reads as a bug. The recovery is now
# the exit climb, which is a better answer anyway: a crevasse you fall
# into and leave by a shaft of rising meltwater is a level whose *idea*
# is the climb, and that is the one level in five where
# `docs/RULES.md` says a climb exit belongs.
#
# **The exit is authored and it is three landings, not six.** Written as
# an ice staircase it was five treads and the crossing -- 35 of the 131
# landings this level lays over eight runs, better than a quarter of
# everything the viewer sees, all of it the same slide repeated. A
# launch block, the moulin and one lit lip is three, and
# `exit="bubble"` takes the reserve down with it (`_level_budget` gives
# a climb exit back `(need - 2) * 3.2` metres of terrace), so the design
# gets the arc the staircase was holding.
#
# **The floor is written out.** The ice theme's own mix is half grey --
# stone, diorite, andesite, cobble -- and the old contact sheet is pale
# blue cubes on a grey plate under a pale blue sky, which is one value
# from top to bottom of the frame. Ten materials now, weighted to snow
# and ice with moraine grit under them: snow 21%, packed ice 16, frost
# and blue ice and calcite 11 each, and gravel, spruce, clay, diorite
# and stone in the tail. The terrace is the lightest thing in the lower
# half of the frame, the cliff is the darkest in the upper, and the two
# lanterns -- the threshold and the foot of the moulin -- are the only
# warm things in the level and both of them are doing a job.
#
# **The corridor is nine wide and that is measured too.** It was 11.5,
# which is a court, and a crevasse is not a court: over four seeds and
# ten seconds each, 11.5 frames 47.7% empty, 10.0 frames 45.9%, and 9.0
# frames **42.3%** -- and the narrow one lays *more* design, 151 landings
# of 260 against 141 of 238, because a pedestal on a ledge has ground to
# find. It costs 2.0% of frames with a wall in the lens against nothing
# at 11.5, and on this level that is the level working: two of four
# seeds jam no frame at all and the worst streak is a third of a second
# at a corridor bend. It also makes this the tight level between two
# broad ones -- THE CISTERN below is 10.5 and THE APIARY above is 11.0.
LEVEL = Level("GLACIER SHELF", "ice", rise=5, gap=3.2, exit="bubble",
              band=9.0, shelf=5.0, breaks=0, landmark="arch",
              ground="snow", sub="packedice", rock="blueice",
              accent="calcite", liquid="water", glow="lantern",
              candy=("blueice", "packedice"),
              # Ten materials, dominant share 21% -- the shape the real
              # map's terraces measure as, one committed hue with a long
              # tail of grit under it. The theme's own mix runs stone,
              # diorite, andesite and cobble at a third of its weight and
              # painted this level as a grey plate.
              floor=(("snow", 4), ("packedice", 3), ("frost", 2),
                     ("blueice", 2), ("calcite", 2), ("gravel", 2),
                     ("spruce", 1), ("clay", 1), ("diorite", 1),
                     ("stone", 1)),
              props=("pebbles", "dripstone", "lanternpost", "mcfence"),
              sky=(150, 188, 228),
              step=("packedice", "slide"), beats=[
    # The threshold: one lantern block flush in the snow on a rise, then
    # the doorway under the leaning seracs, *walked* through beneath a
    # checked lid. A lintel is never jumped -- one impulse always rises
    # 1.25 m, so the head sweeps the two cells above every take-off and
    # an arc under a low beam is refused every time. At lift 1 and not
    # lift 2: a threshold beat is placed from wherever machinery left the
    # body, and the identical beat measures 67% at lift 2 against 100%
    # at lift 1.
    ("sill", [n("glow", arc=3.0, lift=1, hug=3.0, spread=0, deco="lamp",
                orbs=1),
              n("frost", arc=2.9, lift=2, hug=2.8, kind="walk", spread=0,
                ceiling=3)]),
    # The seracs, and the whole shape of the level in one beat: three
    # slides up the ice to four blocks over the terrace, then straight
    # off the top of them into the split.
    #
    # Ice is this level's own verb and the reason it exists. A slide
    # gaining a block reaches 4.36 m where a hop stops at 3.10, so the
    # climb reads as a long run up a ramp of ice rather than as three
    # cubes stacked in a stair -- and the reference does use ice, on
    # three of its forty-three legs, which is about how often this tower
    # should. All three are written at arc 3.4-3.6, a reach of 2.7-2.9
    # against a +1 slide window of 2.67-4.36, so none of them is at the
    # top of its own envelope and none has to fall back.
    #
    # The fall is the fourth node and the point of the beat. Lift 4 to
    # lift 1 is three blocks down across 4.6 m of arc -- a reach of 3.92
    # against a -3 window of 3.72-6.05 -- and `spread=1` covers the case
    # where the third slide came up short, because -2 across the same
    # 4.6 is 3.92 against 3.12-5.56 and legal too. It lands floating,
    # with nothing under it and the meltwater dug out underneath it: a
    # floe caught in the split, and the only ground within reach is the
    # far side of the crevasse.
    ("seracs", [n("packedice", arc=3.5, lift=3, kind="slide", form="ice",
                  hug=2.6, spread=0, orbs=1),
                n("blueice", arc=3.6, lift=4, kind="slide", form="ice",
                  hug=3.2, spread=0, ceiling=3),
                n("packedice", arc=3.5, lift=5, kind="slide", form="ice",
                  hug=3.8, spread=0, deco="lintel", orbs=1),
                n("frost", arc=4.6, lift=2, hug=2.4, spread=1,
                  pedestal=False, moat=True, orbs=2)]),
    # The bottom of the split. A stone standing in the meltwater, and a
    # walk out of it under the ice -- the one stretch of this level with
    # rock on the core side, a roof overhead and the drop outboard,
    # which is the groove the reference is in 71% of the time and this
    # tower almost never builds.
    #
    # The moat is on the beat's *first* node, which is the opposite of
    # what the pond radius wants and is right here for two reasons. A
    # beat's tail is almost never laid, so a pool written second is a
    # pool authored and never seen; and the landing after it floats, so
    # the bowl it digs cannot take the ground out from under it.
    #
    # It is the middle of three, and the three are what hold this level
    # unwalkable. `breaks=0` means there is no lock and no floor gap
    # anywhere, so the pools are the whole of the barrier: a walker can
    # drop into the bowl a moat digs and cannot step back out. Measured
    # over eight walks of the built world at 100% fidelity either way --
    # this pool alone 52% covered, plus the crevasse pool 50%, plus the
    # pond under the calving face **36%**, against a rule of 55 and the
    # real map's 46. This one is 3.0 m from the crevasse pool, which is
    # closer than the radius-3 bowl wants; it is here anyway because it
    # measures at 100% placed and the two ponds read as one flooded
    # crevasse floor, which is what a glacier's is.
    #
    # The shell is on the beat's last node because a shell is painted
    # the moment its landing commits and its walls are then in the way
    # of the next landing of the same beat. Over a `walk` it survives
    # whole: a shell roof sits in the cell the head sweeps at a hop's
    # apex, so a roof over a jump is a roof with a hole in it, and a
    # walk has no apex to punch one.
    ("meltcave", [n("calcite", arc=3.0, lift=2, hug=2.6, spread=1,
                    moat=True, ceiling=3, orbs=1),
                  n("frost", arc=2.8, lift=2, hug=2.6, kind="walk",
                    spread=0, pedestal=False, ceiling=3, shell="cave",
                    orbs=1)]),
    # Out of the cave and onto the calving face: two pans of ice with
    # nothing at all under them, stepping outboard toward the rim, with
    # the sea forty blocks below. This is the level's exposure, and it
    # is the reason `hug` climbs to 4.2 -- the shelf is five cells wide,
    # so a landing hugged at 4.2 is standing on its outermost cell with
    # the drop directly off the far side. The third pond is under the
    # first of them, 6.2 m clear of the one in the cave, and it is what
    # takes the walker off the last third of the terrace.
    ("calving", [n("blueice", arc=3.4, lift=3, kind="slide", form="ice",
                   hug=3.4, spread=1, pedestal=False, moat=True, orbs=1),
                 n("packedice", arc=4.4, lift=3, kind="slide", form="ice",
                   hug=4.2, spread=0, pedestal=False, ceiling=3)]),
], filler=[
    # The level's voice rather than its surprise, and on a level that
    # lays eleven landings a visit this is what runs when the terrace
    # outlasts the script: up onto a floe under a beam of ice, out to a
    # second one hanging past the rim, and then off it -- two blocks
    # down and 4.4 m out, a reach of 3.72 against a -2 window of
    # 3.12-5.56 -- back onto the ice at the shelf edge.
    #
    # The loop's seam is checked like any other jump and half a filler's
    # fidelity is usually lost there: last landing at lift 1 back to the
    # first at lift 2 is a +1 slide across 3.4, a reach of 2.72 against
    # 2.67-4.36. Legal, and only just, which is the point -- it is the
    # same step the seracs open with.
    #
    # No `moat` anywhere in here, and that is not taste: the filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on.
    ("floes", [n("packedice", arc=3.4, lift=3, kind="slide", form="ice",
                 hug=3.0, spread=2, ceiling=3, orbs=1),
               n("blueice", arc=3.5, lift=3, kind="slide", form="ice",
                 hug=4.0, spread=1, pedestal=False),
               n("frost", arc=4.4, lift=3, hug=2.6, spread=1,
                 pedestal=False, orbs=2)]),
], exit_beats=[
    # The way out of the crevasse is the **moulin**: the shaft a glacier
    # drills through itself where the meltwater finds a crack, and the
    # water comes up it. A block against the ice to launch from, the
    # column, and one lit lip at the top to stand on before the leap
    # across.
    #
    # Three landings against the ice staircase's five plus the crossing.
    # That staircase was 35 of the 131 landings this level lays over
    # eight runs -- more than a quarter of everything the viewer sees,
    # and every one of it the same slide -- and it is the single largest
    # thing a level author can take back. `exit="bubble"` is the other
    # half of it: `_level_budget` gives any climb exit back
    # `(need - 2) * 3.2` metres of terrace, which is about three
    # landings of design the staircase was holding in reserve.
    #
    # **It is a `bubble` and not a ladder, and that is measured.** Both
    # were built and both anchor; the difference is that a ladder is
    # ridden at 2.35 m/s and a bubble column at 11.0. Over three seeds
    # and ten seconds each: with a ladder the exit is 634 of the level's
    # 1,533 frames -- 41% of the level's whole time on screen spent
    # riding a column at arm's length -- and 200 of those frames are a
    # flat blue wall filling the lens. With the column it is 394 frames
    # and, once the launch block moved out (below), **none** of them.
    # The moulin is also the better idea: a crevasse you fall into and a
    # shaft of rising meltwater you leave by is a level whose *idea* is
    # the climb, and `docs/RULES.md` says that is the one level in five
    # where a climb exit belongs.
    #
    # The arithmetic of the height. The level rises five and the body
    # arrives at the chasm at lift 1 or on the terrace itself, so the
    # climb has to gain five or six. The launch block is one, the column
    # four, the lip one: six, which puts the last landing a block
    # *above* the next level's floor, and that is deliberate -- the
    # crossing comes down one block onto it, because a flat sprint jump
    # reaches 4.26 m and dropping a block buys nearly another metre.
    #
    # `pedestal=True` is load-bearing and is why this branch fires at
    # all. `_climb_move` wants solid rock within one cell of the column
    # at its middle index and at its top, and out in the lane the only
    # candidate is the landing's own stack; floated, the column is
    # refused silently -- 11,097 of 13,000 candidates on the generated
    # bubble exit -- and the level gets a staircase without being told.
    # `step_y=4` is the other half of the same recipe: shorter and the
    # middle index lands on the stack below the landing rather than on
    # the landing.
    #
    # **The launch block stands at `hug=2.8` and not 2.2, and that one
    # number is the whole of the level's jammed lens.** At 2.2 it is a
    # cell off the core face and the approach to the column is 69 frames
    # of ice wall in 1,293; at 2.8 it is 0 of 1,280, for six points of
    # empty frame that the level can afford (it sits ten under the rule
    # either way). The `ceiling` beam is the cheap half of a roof over
    # the chimney: a `cave` shell here does the same job for the sky and
    # puts a wall back beside the body, which is what was being fixed.
    n("packedice", arc=2.8, step_y=0, hug=2.8, spread=1, confine=True,
      ceiling=3),
    n("blueice", arc=2.4, step_y=2, kind="bubble", hug=2.0, pedestal=True,
      pedestal_style="packedice", spread=0, deco="lamp", orbs=2),
    n("frost", arc=3.0, step_y=1, hug=2.8, spread=0, pedestal=False,
      ceiling=3, orbs=1),
])
