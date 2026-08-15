"""Level 23: SPORE HOLLOW.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE HOLLOW. The mycelium crust over this turn has fallen in. What is
# left is a bowl carpeted in the fallen flesh of one enormous red cap --
# the cap itself still standing over the far half of it on a bone-white
# stem you run under -- with black water standing in the bottom, shelf
# fungus bracketed out of the cliff to get across on, and the gills of
# the cap stepping up the wall at the end. You leave up the inside of a
# stem that has flooded and is pushing the water back out of itself.
#
# The route, in one breath. In over a shroomlight set flush in the
# crust, a stride down the spore path under a lid of rock; two steps up
# a stem and then **off the top of it, two blocks down into the pool**
# onto the spore mat, which throws you two blocks back out -- the only
# move in this engine that gains two, and the reference's one rationed
# gadget. Out of the pool along the brackets, cantilevered off the cliff
# over their own water with nothing under them. Up the gills. Then the
# flooded stem, ridden.
#
# **What this pass changed, and every one of the four was measured on
# the level as it stood rather than reasoned about.** The previous
# version is in the history; it was a good design with two structural
# faults that no per-beat fidelity number could see, because both of
# them were things the *machinery* did with what the design handed it.
#
# **1. The way out was a vine, and a vine is a ladder.** Read off the
# contact sheet before any number: four consecutive frames of flat green
# and, just before them, four of flat grey cliff -- nine dead frames in
# sixty-three, and the level measured 16.9% of its frames with a wall in
# the lens against a tower that is trying to hold 1.8%. It is not
# tunable. A body rides a climb at 2.35 m/s and the wall a vine hangs on
# *is* the wall in the lens, so four blocks of vine is 1.7 seconds --
# a hundred frames -- of the body's face against a stem. A bubble column
# goes up at **11.0 m/s**: the same four blocks are on screen for a third
# of a second. ``docs/LEVEL_BRIEF.md`` has the tower-wide version of this
# (one level measured 14.9% -> 6.6% swapping ladder for bubble at no
# other cost) and it is the reason ladders are being taken off the
# roster. The level loses nothing for it: a bowl with a pool in the
# bottom and a hollow stem standing in the pool is a *better* reason for
# a water column than the vine ever was for itself.
#
# **2. The climb overshot the next level by two blocks, and then fell
# back down.** This is the one worth writing down, because the per-beat
# table read 100% through it and the move mix read ``climb`` by name, so
# every check this file is held to said the exit was fine. Instrumented
# over eight unpinned runs -- print every landing's walking surface
# against ``Section.y`` -- the exit read:
#
#     ascent  lift 2   climb        <- the launch
#     ascent  lift 6   hop          <- the top of the vine
#     ascent  lift 1   hop  plaster <- the crossing, five blocks DOWN
#     ascent  lift 2   climb        <- and a second climb, to fix it
#
# The next level's floor is at lift 4. A launch at lift 2 plus a
# ``step_y`` of four tops out at lift 6, which is two above where the
# crossing wants to be; the crossing is written to descend *one*, could
# not find the far ground from up there, and fell back onto our own
# terrace -- after which the reliability chain quite correctly climbed
# out again. Five ascent landings a visit, a quarter of the level, and
# the shape of it is the owner's "it puts a ladder there and then jumps
# back down to a lower part than where the ladder was" exactly.
#
# The launch is now at **lift 1** and the ride still gains **four**, so
# the top is lift 5, one above the next floor, and the crossing comes
# down that one block onto it. The four is not free to shrink: a climb
# anchors on solid rock within one cell of its column at the column's
# middle index *and* at its top, which out in the lane means the top
# landing's own pedestal stack, and a rise under four puts the middle
# index below the stack. So the height had to come off the *launch*.
#
# **3. The floor was the family's, not the level's.** No ``floor=`` at
# all, so the bowl was painted from the stock mushroom mix -- bone stem
# 21%, dirt, coarse, stone, gravel, mossy -- and the contact sheet came
# back brown and grey with two violet patches in it. Identity comes from
# the ground (``docs/RULES.md`` 5): a real leg of the reference uses a
# median fourteen materials with the commonest at about a quarter. Ten
# named here, dominant at 24%, and the dominant one is the **cap's own
# red**, so the floor of the bowl is the thing that fell into it. That
# also settles the seam: level 22 below is cream endstone, black
# obsidian and lilac purpur under pale sea-lantern light, and a violet
# mycelium plate next door to it would have been the same level twice.
# Red ground, bone stems, orange shroomlight.
#
# **4. Every landing was hugged to 2.4-2.8 and the cliff filled the
# lens.** The hugs are load-bearing on a ``ledge`` -- unhugged, a landing
# is pulled to the middle of the *band*, which on a five-block shelf
# inside a ten-block band is out over the drop -- but the previous file
# treated "the wall is a couple of metres off the shoulder for the whole
# run" as the point of a hollow, and a couple of metres is where a wall
# stops being a groove and becomes the frame. The reference's own
# measurement is a wall within **four** metres on one side of 71% of
# samples, not two. Everything is at 2.8-3.4 now, which is still well
# inside a shelf that wobbles about +/-1.3 around 5.0.
#
# What did **not** change, and deliberately: the sinkhole. It is the
# level's showpiece, it is the second beat because a terrace this length
# lays two beats whole and truncates the third, and it fires -- ``bounce``
# is in the move mix on every run. Its heights are 2 / 3 / 1 / 3 and none
# of them may move: the fall has to be **two** blocks and cross 4.4 m or
# more, because a bounce fires at an arrival of 7.0 m/s and only throws
# *two* at 11.0, and its pad may not stand at lift 0, which is the
# terrace's own top cell and is refused with the rest of the beat behind
# it.
#
# One thing this level knows about itself that the numbers hide: **the
# filler is almost never reached.** Twenty-four unpinned runs laid
# ``spores`` fifteen times in five hundred and eight landings, because
# the script plus the lock plus the landmark crossing already fill the
# terrace. So the level's identity has to be in the first three beats,
# and ``gills`` at 1.3 landings a visit is a beat written knowing it
# plays about one visit in two and shows its first node when it does.
#
# Measured, before this pass and after, on the same eight runs and the
# same seed 3 for the camera:
#
#   | | before | after |
#   |---|---|---|
#   | lens jammed by a wall | 115 of 681 frames (**16.9%**) | 18 of 504 (**3.6%**) |
#   | frame empty | 45% | **40%** |
#   | unchecked emergency placements | 2 (1.16%) | **0** |
#   | designed landings placed as authored | 99%, ``gills`` 92% | **100%, every beat** |
#   | designed share of the level | 52% | **55%** |
#   | the exit climb | 40 landings | **35** |
#   | plain hop | 77% | 80% (walk 11, bounce 5, bubble 5) |
#   | structure held at 25 deg from the approach | 1.3 s | **1.7 s** (the rule is 1.5) |
#   | walker coverage / body inside the world | 21% / 0 | 20% / **0** |
#
# The hop share is the one row that went the wrong way, and it is the
# ride: eight blocks of vine and two recovery climbs were three landings
# of ``climb`` a visit, and a four-block bubble is one. The walk in the
# brackets is what pays for it -- see that beat.
LEVEL = Level("SPORE HOLLOW", "mushroom", rise=4, gap=3.0, exit="bubble",
              band=10.0, shelf=5.0, profile="ledge", breaks=2,
              landmark="greatcap",
              # Red ground, bone-white stem, black water, and the
              # shroomlight doing the only job light does here.
              # ``_lm_g_greatcap`` names ``mushroomstem`` and
              # ``mushroomred`` literally whatever the theme is, so the
              # structure the course is steered through is built out of
              # the same two materials as the floor it stands in and the
              # blocks you land on -- which is REEF GARDEN's trick with
              # its coral, in reverse: there the level was skinned to
              # match the structure, here the structure is already the
              # level's own colours and the floor is skinned to finish
              # the job.
              ground="mycelium", sub="podzol", rock="mushroomstem",
              accent="mushroomred", glow="shroomlight", liquid="water",
              # Pale, because the ground is now the red one. A floating
              # block in the cap's own red over a floor of the cap's own
              # red is a block nobody sees.
              candy=("mushroomstem", "mycelium"),
              props=("mushroomcap", "vinehang", "grasstuft", "flower"),
              sky=(158, 136, 176), dark=0.25,
              # Ten materials, dominant at 24%: the fallen cap flesh, the
              # podzol under the crust where it has worn through, patches
              # of the old violet mycelium, wet moss at the waterline,
              # and a scatter of shroomlight in the crust that is the
              # only warm thing in the bottom of the bowl.
              floor=(("mushroomred", 5), ("podzol", 3), ("mycelium", 2),
                     ("moss", 2), ("coarse", 2), ("dirt", 1), ("mossy", 1),
                     ("gravel", 1), ("mushroomstem", 1), ("shroomlight", 1)),
              step=("mushroomstem", "hop"), beats=[
    # THE CRUST. The threshold, written the way the reference writes one:
    # an emissive block set flush in the floor, on a rise, with the
    # palette changing completely at that block and no blend -- pale
    # endstone and lilac purpur out at the colonnade below, red crust and
    # orange spore light here.
    #
    # The lid is *walked* under and never jumped under. One jump impulse
    # always rises 1.25 m, so the head sweeps the three cells over every
    # take-off and an arc under a lid low enough to read as a lid is
    # refused every time; over a ``walk`` there is no arc at all, which is
    # what makes ``ceiling=3`` an honest head-hitter -- the genre's 2bc,
    # the one obstacle this kernel can express. The ``tunnel`` over the
    # same leg is what the lid is not: five to seven cells wide, so it
    # answers the whole ray fan rather than its centre column, and it
    # survives whole only over a walk (a shell roof sits in the cell a
    # hop's apex sweeps, so a tunnel over a jump is a roof with a hole in
    # it). It is on the beat's **last** node because a shell is painted
    # the moment its landing commits and its walls are then in the way of
    # the next landing of the same beat.
    ("crust", [n("glow", arc=3.0, lift=1, hug=3.0, spread=0, deco="lamp",
                 orbs=1),
               n("coarse", arc=2.9, lift=2, hug=3.0, kind="walk", spread=0,
                 ceiling=3, shell="tunnel")]),
    # THE SINKHOLE. The crust gives way: two steps up a stem, the
    # two-block fall into the pool onto the spore mat, and the throw two
    # blocks back out onto the gill above it.
    #
    # It is the second beat and not the fourth, and that is arithmetic
    # rather than taste. A terrace this length lays two beats whole and
    # truncates the third, so a showpiece written late is a showpiece
    # nobody sees -- measured, this beat lays all four of its landings on
    # every run of eight, and the beat after it lays two and a half.
    #
    # Four things hold the bounce up and none is free:
    #
    # * **The rise and the fall are inside one beat.** Machinery -- the
    #   lock, the landmark crossing, a recovery -- is inserted *between*
    #   script beats and leaves the body back at lift 1, so a rise
    #   written in one beat and spent in the next is a rise that does not
    #   happen: the fall becomes a one-block drop and a one-block drop is
    #   refused as a +2 bounce on every candidate.
    # * **The feed jump is 5.0 m.** A bounce fires at an arrival of
    #   7.0 m/s and throws *two* blocks only at 11.0, which wants a
    #   two-block drop across 4.4 m or more -- and ``_node`` offers
    #   ``arc * 0.84`` as its fallback, so a feed written at 4.4 arrives
    #   at 6.75 against a 6.72 threshold when it falls back and silently
    #   becomes a hop. 5.0 keeps the fallback at 4.2.
    # * **The pad lands at lift 1, not lift 0.** Lift 0 is the terrace's
    #   own top cell: solid, so the landing is refused and the rest of
    #   the beat is abandoned behind it, while the recovery drops a plain
    #   cube under the beat's own name and the table still reads it as
    #   placed.
    # * **``pedestal=False`` and ``spread`` >= 1 on the throw.** A pad
    #   with a pedestal is only offered cells with ground under them and
    #   at the bottom of a hole there are none; a bounce with ``spread=0``
    #   is refused and placed a block lower as an ordinary hop, which
    #   looks exactly like it worked.
    #
    # The pad sits half a metre further out than the rest of the level,
    # which is what makes the fall read as a fall *into* something.
    ("sinkhole", [n("rock", arc=3.3, lift=3, hug=3.0, spread=0),
                  n("accent", arc=3.2, lift=4, hug=3.0, spread=0),
                  n("slime", arc=5.0, lift=2, hug=3.4, form="slime",
                    spread=0, pedestal=False, moat=True, orbs=1),
                  n("accent", arc=3.6, lift=4, hug=3.0, kind="bounce",
                    spread=1, orbs=3)]),
    # THE BRACKETS. Shelf fungus cantilevered out of the cliff over its
    # own pool, climbing a block at a time.
    #
    # **Nothing here stands on anything.** Every landing behind the
    # opener is ``pedestal=False``, which is two things at once: it is
    # what a bracket fungus *is* -- a shelf growing out of a wall with
    # nothing under it -- and it is the fix for the beat that sits at
    # 89-92% for several passes, because a plinth on a ledge has to find
    # ground under a shelf that wobbles about +/-1.3 and, here, has a
    # radius-three bowl cut out of it 2.5 m upstream. The moat is on the
    # opener for the same reason it works on THE SILENCE's sill: a beat's
    # tail is almost never laid, so a pool written second is a pool
    # authored and never seen, and the landings after it float, so the
    # bowl cannot take the ground out from under them.
    #
    # It is eight metres downstream of the sinkhole's pool, and that is
    # the minimum: a moat digs a radius-three disc at commit and a second
    # one inside that radius stands in the hole the first dug.
    #
    # The opener is 4.4 m because it has three heights to be legal from.
    # It follows the bounce at lift 3 (a two-block drop, reach 3.72
    # against a window of 3.12-5.56), or machinery back down at lift 1
    # (level, 3.72 against 4.26), or a recovery at lift 2 (down one). The
    # two behind it are ``step_y`` rather than ``lift``, so they are
    # measured from wherever the opener actually landed rather than from
    # the terrace, and at ``arc`` 3.2 a +1 hop reaches 2.52 -- centred in
    # the 2.00-3.10 a one-block rise allows rather than pressed against
    # the top of it, where the arc is what has to fall back.
    #
    # **The stride across the first bracket is at position two**, which
    # is the whole reason it exists rather than being a fourth hop. A
    # beat lays about three of its four nodes -- so a non-hop verb
    # written at the tail is written and never seen, and one written
    # first follows machinery at an arbitrary height where a walk needs
    # its predecessor within half a metre. It is also the level's whole
    # margin against the verb rule: without it the level measured **84%
    # plain hop** with a 6% walk share, one point under the 85% limit,
    # because the only other non-hop moves it has are the bounce and the
    # ride out. With it, 82% and 9% over twenty-four runs and 80% and 11%
    # over eight.
    ("brackets", [n("rock", arc=4.4, lift=2, hug=3.0, spread=1, moat=True,
                    orbs=1),
                  n("sub", arc=2.4, step_y=0, hug=3.0, kind="walk", spread=0,
                    pedestal=False, ceiling=3),
                  n("accent", arc=3.2, step_y=1, hug=2.8, spread=0,
                    pedestal=False, orbs=1),
                  n("rock", arc=3.2, step_y=1, hug=3.0, spread=0,
                    pedestal=False)]),
    # THE GILLS. Three tiers of the cap's underside stepping up against
    # the stem, and the last of them roofed.
    #
    # Written knowing it plays about one visit in two and shows its first
    # node when it does -- so the first node is the one that is worth
    # something: it opens at **lift 2**, which is the one real lever a
    # level has against "half the jumps are at ground level". ``arc`` 3.2
    # is the length that is legal from every height the beat before it
    # can leave the body at: +1 from machinery at lift 1 (a reach of 2.52
    # against a window that shuts at 3.10), level, and down one off the
    # top of the brackets.
    #
    # **The two tiers are slabs**, and they are the only half-height
    # landings in the level. Stairs and slabs are the commonest non-cube
    # form in the reference by a wide margin, a gill *is* a half-height
    # ledge, and the arithmetic is worth stating because it is easy to
    # get backwards: a slab stands half a block **down** in its own cell,
    # so ``lift=3, form="slab"`` is a surface of 2.5 -- a +0.5 step off
    # the opener -- and ``lift=4`` behind it is 3.5, a +1.0 step. Written
    # at the *same* lift as the block before it a slab is a step
    # **down**, and the node after it then asks for +1.5, which no hop in
    # this model has. They are absolute lifts and the opener is
    # ``spread=0`` for that reason: a slab chain behind an opener that
    # may settle a block high is a chain asking for a rise of two.
    #
    # The ``cave`` is on the beat's last node, and it is the second and
    # last shell in the level. One shell is a pinch and three in a row
    # jam the lens on 10-21% of frames; the version this replaces had
    # four, one of which was a ``grotto`` -- a bay carved into the core
    # wall, which is to say a lens full of cliff by construction.
    ("gills", [n("accent", arc=3.2, lift=3, hug=3.0, spread=0, orbs=1),
               n("rock", arc=3.4, lift=4, hug=2.8, spread=0, form="slab"),
               n("accent", arc=3.2, lift=4, hug=3.0, spread=0,
                 shell="cave", orbs=1)]),
], filler=[
    # THE SPORE PATH. Off the gills, a lit stride along the crust under
    # the rock, and back up onto the next bracket. Three nodes and a
    # cycle rather than a line: it climbs one and falls one every lap,
    # which is the only way a repeating beat does not read as a corridor.
    #
    # The walk is at position **two**. A beat lays about half its nodes,
    # so a non-hop verb at the tail is written and never seen, and one
    # written first follows machinery at an arbitrary height where a walk
    # needs its predecessor within half a metre. It is also the route
    # painted: the reference lights the place you are *going* and nothing
    # else, and on a floor of red crust the lit brown path is the only
    # thing saying which way the hollow runs.
    #
    # **No moat in here.** The filler loops, and the second lap digs away
    # the ground the first lap's pedestals are standing on -- 27,859
    # refusals from one keyword on the level that found it.
    #
    # The loop seam is checked like any other jump: the last landing at
    # lift 2 back to the first at lift 1 is a one-block drop across 4.4,
    # a reach of 3.72 against the 2.35-4.98 a descent of one allows, and
    # the same number is legal level, which is what it is asked from when
    # machinery lands between two laps.
    ("spores", [n("accent", arc=4.4, lift=4, hug=3.0, spread=1, orbs=1),
                n("coarse", arc=2.4, step_y=0, kind="walk", hug=3.0,
                  spread=0, ceiling=3, deco="lamp"),
                n("rock", arc=3.2, step_y=0, hug=2.8, spread=0,
                  pedestal=False, orbs=1)]),
], exit_beats=[
    # THE FLOODED STEM. A lit block at its foot and then the water column
    # inside it, ridden four blocks out of the bowl.
    #
    # **It is water and not a vine, and that is this pass's largest
    # change.** A climb is ridden at 2.35 m/s with the column a hand's
    # width from an eighty-degree lens, so four blocks of vine is 1.7
    # seconds of flat green -- four consecutive frames of it on the sheet
    # this replaces, and 16.9% of the level's frames with a wall in the
    # lens. A bubble goes up at 11.0: the same four blocks are a third of
    # a second. It is also the better idea for this place. The bowl has
    # standing water in the bottom of it, the sinkhole's pool is water,
    # the brackets stand in water; a stem that has filled and is pushing
    # it back out is what a flooded hollow would actually do, and it is
    # the *only* way out of a bowl, which a staircase is not.
    #
    # **The arithmetic of the height, which the version this replaces got
    # wrong by two blocks and paid a whole second climb for.** The next
    # level's floor is at lift 4. The launch is lift 1, the column gains
    # four, so the top is lift 5 -- one above -- and the crossing is
    # written to come down exactly that one block, because a flat sprint
    # jump reaches 4.26 m and dropping a block buys nearly another metre.
    # The four may not shrink: ``_climb_move`` wants solid rock within one
    # cell of the column at its **middle index** and at its **top**, out
    # in the lane the only candidate is the top landing's own pedestal
    # stack, and a rise under four puts the middle index below that
    # stack -- 1 anchored column in 1,559 candidates when it was
    # instrumented, and the level then gets a silent eight-step
    # staircase. So the two blocks came off the launch instead.
    #
    # **``pedestal=True`` is the load-bearing keyword** and the stack it
    # builds is the stem itself, in the stem's own material.
    #
    # The launch stands at ``hug=2.8``. One level measured 69 wall-jammed
    # frames of 1,293 with its launch at 2.2 and **0 of 1,280** at 2.8,
    # and only the launch matters -- ``hug`` on the climb node itself
    # produces worlds identical to the frame, because the camera locks
    # onto the *landing* through take-off and flight and a launch tucked
    # against the core aims the whole ride at the cliff. There is
    # deliberately no ``shell="shaft"`` round the column: a tube is what
    # puts the body inside the wall, and taking one off elsewhere took
    # body-inside-the-world from 3 frames of 556 to 0. The ``cave`` is on
    # the launch instead, where its roof takes a chimney from the
    # reserved climb cells for free, and it is worth about four points of
    # empty frame -- the exit is the emptiest third of any level and
    # nothing else in this file is over it.
    #
    # **Check ``--report``'s move mix for the word ``bubble``.** If it is
    # missing, this is a staircase and the level has lost its way out.
    n("rock", arc=4.2, step_y=0, hug=2.8, spread=1, deco="lamp",
      shell="cave"),
    n("mushroomstem", arc=2.6, step_y=1, kind="bubble", climb_style="water",
      pedestal=True, spread=0, orbs=2),
])
