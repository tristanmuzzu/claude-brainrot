"""Level 31: ECHO SHAFT.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# ECHO SHAFT. Somebody sank a shaft straight down through this terrace
# into the geode under it and then walked away. The timber crane still
# stands over the mouth of it with its jib out across the run; the
# sculk has grown back over the spoil; black water stands in the holes
# where the crust fell in; and the only light in the place is the cold
# blue of the sea lanterns set in the collar and down the treads. What
# you get out on is the **cut stair** -- eight calcite treads winding
# up the inside of the shaft wall, alternating white and black, lit at
# every second one -- and that stair is the level, not the price of it.
#
# The route in one breath. A sea lantern set flush in the sculk with
# the water cut out round it; a stride in **on foot** under the rock
# brow; two calcite kerbs up onto the shaft's collar; and then **off
# the front of the collar, two blocks down and 4.9 of arc out into the
# mouth of the shaft**, which is the level's long jump, its descent and
# the thing a viewer remembers -- black water under it and nothing else
# at all. Across onto the hoist stage, out through the drip bay bitten
# into the cliff, and then the winding ledges, and then the stair.
#
# **It has to be a different deep place from THE SILENCE**, which is the
# tower's other ``deepdark`` level and the only other level that rises
# eight. That one is a survey camp: spruce boardwalk, warm lanterns on
# every post, a bore-pit that has flooded, and a way out that is the
# flood coming back *up* the shaft. So this one is the opposite on every
# axis that reads at a glance -- **cold** where that is warm (sea lantern
# blue against lantern orange, and it is the same one word, ``glow``,
# that decides it), **cut stone** where that is timber, and **a stair**
# where that is a column of water. The palette is the geode: black sculk
# and deepslate for the ground and the cliff, white calcite for
# everything the level built, amethyst speckled through the floor.
#
# Six things this file is careful about, every one of them measured
# elsewhere and every one of them silent when got wrong.
#
# * **The way out is a stair and not a ladder.** Bucketed by segment and
#   move over four seeds, an ``ascent/climb`` ride measured 20.9% of its
#   frames with a wall jammed in the lens against 0.0% for every other
#   move in that level, and it is not tunable -- the wall a ladder hangs
#   on *is* the wall in the lens and ``hug`` on a climb node is inert. A
#   five-tread stair read 1.0% against the same ladder's 5.4% for
#   identical designed content. The other good answer is a bubble
#   column, and THE SILENCE has it; ``docs/RULES.md`` §3 counts twelve
#   ladder exits against three stairs across twenty rebuilt levels and
#   asks for a climb on about one level in five, so this is the level
#   that gives one back.
# * **The exit is written on ``step_y`` and never on ``lift``.** ``lift``
#   is clamped to ``LIFT_MAX = 6`` silently -- no error, nothing in the
#   fidelity table -- and one level wrote an authored exit at lifts 2..9,
#   had it clamped to 6, and laid 755 landings over eight runs grinding
#   against its own chasm before anybody found out. ``step_y`` is an
#   absolute rise from the landing before and is not clamped at all.
#   The arithmetic: the foot of the stair is ``lift=1``, eight treads
#   gain eight, so the head of it stands at 9 -- one block above the
#   next level's floor, and the crossing comes down that block, because
#   a flat sprint jump reaches 4.26 m and dropping one buys nearly
#   another metre.
# * **Nine landings of exit is what ``rise=8`` costs, and the answer is
#   to design them rather than to fight them.** The reserve is
#   ``(need + 1) * 3.2`` metres of terrace taken off the front of the
#   level, so the tallest level in the tower pays about thirty metres
#   before a single beat is laid and no arrangement of the vocabulary
#   gets a stair up eight blocks in fewer than eight treads. So the
#   treads are the architecture: banded calcite and deepslate, lit at
#   every second one, lidded on the odd ones, winding *out* from the
#   wall as they climb (``hug`` 3.0 -> 3.6) so the head of the stair
#   stands against sky rather than tucked into the cliff.
# * **``profile="plaza"``, and this level is the one that proved why.**
#   At ``shelf=3.5`` on a ledge its exit staircase came back over its
#   own cells one lap later and failed the twice-claimed-cell invariant
#   outright -- the reserve is measured in metres of arc from wherever
#   the body stands, so the tallest levels need the widest ground. The
#   walk number is then held down by holes rather than by the shelf
#   edge: three ``moat`` landings, each swapping the terrace's top cell
#   for water over a radius-three disc. Liquid on its own is atmosphere
#   -- water is see-through and lava is solid, so neither stops a walker
#   -- and it is the **bowl** that stops one, because a walker gets into
#   it and cannot step back out.
# * **``breaks=0``.** Any break at all forces the lock, and a level's
#   first floor break is always 5.5-6.7 m wide, so the machinery that
#   crosses it lays an approach at height, an island and a landing. On a
#   level that is already paying for a landmark crossing and a nine-
#   landing exit that is most of everything laid: THE GATEHOUSE measured
#   the same design at 39% designed content with breaks and 56% without.
# * **``deepdark``'s own ``glow`` role is ``amethyst``, which emits
#   nothing.** Only five material names are in ``spiral._GLOWING`` --
#   ``lantern``, ``torch``, ``glowstone``, ``sealantern`` and ``magma``
#   -- so every ``deco="lamp"`` on the inherited role was a violet cube
#   lighting nothing, on the darkest theme in the tower. ``sealantern``
#   turns every light in the level on *and* is the one cold one, which
#   is the whole difference between this place and the camp. The theme
#   also carries ``dark=0.86``, at which a lid is worth nothing at all
#   (``_indoor_want`` returns ``max(theme.dark, 0.85)``); 0.56 is light
#   enough for calcite to read as white against the sculk, and it is the
#   calcite that carries every frame's value contrast.
LEVEL = Level("ECHO SHAFT", "deepdark", rise=8, gap=2.6, exit="stair",
              band=10.5, shelf=4.5, profile="plaza", breaks=0,
              landmark="crane",
              # Black ground, black cliff, and everything the shaft-
              # sinkers built in white calcite, so the level is the one
              # thing the reference builds every frame out of: the
              # palest material in the lower half of the frame and the
              # darkest across the top. ``sub`` is what the rim's cut
              # face shows in section, and tuff is what a geode sits in.
              ground="sculk", sub="tuff", rock="deepslate",
              accent="calcite", glow="sealantern", liquid="water",
              candy=("calcite", "amethyst"),
              # Fourteen materials with the dominant at 23%, which is
              # the shape a real terrace measures as (median 14 kinds,
              # dominant 26%) against this tower's usual two or three.
              # The stock deep-dark mix is ten and nine of them are grey
              # stone. Here it is the sculk crust, the spoil that came
              # up the shaft, the geode broken open through it, and the
              # white calcite of everything that was cut.
              #
              # Weighted **dark**, and that was a correction off the first
              # contact sheet: the first draft carried andesite, cobble,
              # gravel and tuff at two apiece and came back a *mid grey*
              # plate with black boxes on it, which is the one thing this
              # palette exists to avoid. The mid greys are the long tail
              # now and the top of the list is black, so the calcite is
              # the only pale value in the lower half of any frame.
              floor=(("sculk", 8), ("deepslate", 4), ("blackstone", 3),
                     ("sculkvein", 3), ("calcite", 3), ("amethyst", 2),
                     ("tuff", 2), ("obsidian", 1), ("coalore", 1),
                     ("gravel", 1), ("andesite", 1), ("dripstone", 1),
                     ("moss", 1), ("cobble", 1)),
              # A shaft head's furniture: the spoil trams, the guard
              # fence round the mouth, the chain off the crane's hook,
              # and the dripstone hanging out of the roof of the bay.
              # ``dripstone`` and ``chain`` hang from their *top*, which
              # is what a shaft has over it and a camp does not.
              props=("dripstone", "chain", "rail", "mcfence", "pebbles"),
              dark=0.62, sky=(54, 62, 96),
              # If the cut stair ever falls back to the generated one it
              # climbs the same white treads rather than the cliff.
              step=("calcite", "hop"), beats=[
    # THE SHAFTHEAD. The whole level in one beat, and that is deliberate:
    # machinery -- the lock, a recovery, the crossing under the crane's
    # jib -- is inserted *between* script beats and hands the body back
    # at lift 1, so a rise written in one beat and spent in the next is a
    # rise that mostly does not happen. The fall needs two blocks of
    # height under it and the only way to be sure of having them is to
    # have climbed them three nodes earlier in the same list. This is
    # also the one beat that is never truncated, because it opens the
    # level and never competes with anything for terrace, which is why
    # the level's showpiece is in it and not in a later beat:
    # ``_truncate`` spends a beat's budget on ``arc`` and eats the
    # *longest* arc in the last beat first, which is always the level's
    # best jump.
    #
    # 1. The threshold, written the way the reference writes one: an
    #    emissive block set flush in the floor, on a rise, with the
    #    palette changing completely at that block and no blend. WART
    #    FIELDS below is crimson nylium and lava; from here it is black
    #    sculk and cold blue. The water is cut round the sill rather
    #    than beside it -- the first of the level's three holes, and it
    #    is on the beat's *first* node because a beat's tail is almost
    #    never laid, so a pool written second is a pool authored and
    #    never seen. ``lift=1`` and not 2: the identical threshold beat
    #    measured 67% at lift 2 and 100% at lift 1, because a beat's
    #    opener is placed from wherever machinery left the body.
    # 2. The stride in off the sill, **on foot**, under the rock brow.
    #    A walk is the genre's ``2bc`` -- the lid you sprint under --
    #    and the only honest form of it this kernel has, because one
    #    jump impulse rises 1.25 m and the head then sweeps the two
    #    cells above every take-off, so a lintel low enough to read as a
    #    brow refuses any arc under it. ``ceiling=3`` over a walk is a
    #    real head-hitter that the arc test never has to refuse, because
    #    a walk has no arc. 2.9 of arc is 2.22 m of ground against a
    #    walk's 2.4 m limit. It is at position **two** and not three: a
    #    beat lays about half its nodes and a non-hop verb written late
    #    is written and never seen -- moving each walk to position two
    #    took one level from 100% plain hop to 83% -- and one written
    #    *first* follows machinery at an arbitrary height where a walk
    #    needs its predecessor within half a metre. It floats, because
    #    the bowl one node back has just been dug and a pedestal cannot
    #    stand in a hole.
    # 3. **Up onto the first calcite kerb, and that is the third landing
    #    of the level with nothing but a stride before it.** 55% of
    #    authored landings across this roster sit at lift 0-1 and that
    #    is the owner's "half the jumps are at ground level" measured;
    #    from here nothing in this level touches the floor again except
    #    the bottom of the shaft. +1 at ``arc`` 3.0 is a reach of 2.32
    #    against a +1 window of 2.00-3.10, centred rather than pressed
    #    against the top of it, because a +1 written at 3.6 is the arc
    #    that has to fall back and a fallback is not ``exact``.
    # 4. +1 again onto the shaft's collar, and out from the wall: the
    #    ``hug`` goes 3.2, 3.2, 3.4, 3.8, so the kerbs step *out* over
    #    the mouth as they climb and the collar stands clear of the
    #    cliff. It keeps its pedestal -- a calcite collar is masonry
    #    built up off the terrace, and terrain under the body is also
    #    what the empty-frame ray fan's shallow down-rows land on.
    # 5. **Off the collar into the shaft.** ``step_y=-2`` at ``arc``
    #    4.9: a reach of 4.22 against a -2 window of 3.12-5.56, and the
    #    level's one long jump, because a descent is the only long jump
    #    this motion model has -- falling takes time and the body does
    #    not slow down while it does. Level, a hop stops at 4.26 stand
    #    point to stand point and this is out past it. Written on
    #    ``step_y`` so it is two blocks below *the collar the body
    #    actually reached* rather than two below where the collar was
    #    drawn. It lands floating over the second pool, which is what
    #    the bottom of a shaft is, and it does **not** go to lift 0 --
    #    that is the terrace's own top cell, solid, and a ``step_y``
    #    descent onto it is refused with the whole rest of the beat
    #    abandoned silently behind it.
    # 6. Across the water onto the hoist stage. It floats, and it has to:
    #    the moat one node back has cut a radius-three bowl and a
    #    pedestal will not stand in one -- that single keyword is 27,859
    #    "pedestal will not stand" refusals elsewhere in this roster.
    ("shafthead", [n("glow", arc=3.2, lift=1, hug=3.2, spread=1,
                     deco="lamp", moat=True, ceiling=3, orbs=1),
                   n("ground", arc=3.2, step_y=1, hug=3.2,
                     pedestal=False, ceiling=3),
                   n("accent", arc=2.9, step_y=0, hug=3.4, kind="walk", pedestal=False,
                     ceiling=2, orbs=1),
                   n("accent", arc=3.0, step_y=1, hug=3.8, orbs=1),
                   n("rock", arc=4.9, lift=2, step_y=-1, hug=4.4, spread=1,
                     pedestal=False, moat=True, orbs=2),
                   n("accent", arc=3.2, step_y=1, hug=4.0, pedestal=False,
                     orbs=1)]),
    # THE DRIP. The level's one interior, and it is a **two-metre pinch**
    # rather than a room: a deepslate boulder standing in the third pool
    # at the foot of the shaft, and a bay bitten into the cliff beside it,
    # walked out of under its own rough roof with the dripstone hanging
    # in it. Measured over 1,662 metre-samples of the real map, fully
    # enclosed is 6.1% of the way, no leg of forty-three is enclosed more
    # than half, and an enclosed run lasts a median of two metres. What
    # the reference is the whole time instead is a *groove* -- rock
    # within four metres on the core side on 71% of samples, the drop
    # outboard, a lid a median eight blocks overhead -- and one shell in
    # a level is that pinch. Three in a row jam the lens on 10-21% of
    # frames.
    #
    # Two nodes and no more, because a beat lays about half of what is
    # written in it and everything this beat is about has to be inside
    # the half that gets laid. The ``shell`` is on the **last** node,
    # which is the only place one may go: a shell is painted the moment
    # its landing commits and its walls are then in the way of the next
    # landing of the same beat. It is on a ``walk`` because a shell roof
    # sits in the cell the head sweeps at a hop's apex -- a tunnel over
    # a jump is a roof with a hole in the middle of it -- and at lift 1
    # because ``_shell`` skips any wall column with nothing under it, so
    # a bay written higher is a roof with open sides, which is not a bay.
    ("drip", [n("rock", arc=3.4, lift=2, hug=3.4, spread=1, moat=True,
                ceiling=2, orbs=1),
              n("accent", arc=2.9, step_y=0, hug=3.4, kind="walk",
                pedestal=False, shell="cave", ceiling=3, deco="lamp",
                orbs=1)]),
], filler=[
    # THE WINDING LEDGES. The filler repeats and a script's tail does
    # not, so this loop is what the level mostly *is*, and it is
    # therefore the only place where "half the jumps are at ground
    # level" can actually be answered. **Nothing in it is at lift 1.**
    # It opens at 2 on a calcite ledge cut into the shaft wall, strides
    # it on foot under the rock, steps up to 3, strides that one too,
    # steps up to a lit ledge at 4 -- the highest ground in the body of
    # the level -- and comes off the end of it two blocks down onto the
    # next ledge round, at 2, where it began.
    #
    # A **cycle and not a line**, which is the shape a filler has to
    # have. Written as a monotonic climb the loop would buy the level a
    # longer exit every lap; written as a monotonic fall it would buy a
    # taller one. Climbing two and falling two a lap leaves the body
    # where the exit expects it and spends the whole of the level's
    # middle at lift 2-4 with the plaza underneath. That also buys
    # frame: the ray fan the empty-frame number is taken with is +/-36
    # degrees inside eight metres, so at lift 1 its shallow down-rows
    # land on the ground a metre below and at lift 4 they fly clean over
    # the terrace into the void -- 2 to 4 is the band where a wide plaza
    # is still under them.
    #
    # The opener is ``arc`` 3.4, a reach of 2.72, and that number is
    # chosen to be legal from all three heights this beat is ever
    # entered at: +1 from machinery or the drip bay at lift 1
    # (2.00-3.10), level from its own last landing at 2 (2.00-4.26), and
    # -1 from a recovery at 3 (2.35-4.98). Everything behind it is on
    # ``step_y`` so that a loop which opened a block high or low still
    # has the shape it was written with.
    #
    # **There are two walks in the loop, at positions two and four**,
    # and that is this level's only lever on its move mix. A stair up
    # eight blocks is eight hops and nothing else -- the only verbs that
    # gain height are the ladder, which the brief forbids on measurement,
    # and the bubble, which THE SILENCE has -- so the exit is a third to
    # a half of every visit and can only ever be plain hops. The mix is
    # therefore decided entirely by the body of the level, and this beat
    # is the biggest thing in it: measured over eight runs it laid 44 of
    # the level's 101 designed landings, more than every script beat put
    # together. A beat lays about half its nodes, so a non-hop verb
    # written at a tail is written and never seen; moving the walks to
    # position two is measured elsewhere as the difference between a
    # move mix that is 100% plain hop and one that is 83%. And in the
    # deep dark there is nothing else that fires reliably: ice is
    # another biome, cobweb appears **zero** times in the entire
    # reference save, and the slime pad placed on 6 runs of 24 and fired
    # on 1 when it was measured.
    #
    # **No ``moat`` anywhere in here**, and that is not taste: the filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on. The level's three holes are all in
    # beats that play once.
    #
    # The seam where the loop closes is a jump like any other and half of
    # what a filler ever loses is there: it is the last ledge at 2 back
    # onto the opener at 2, level across 3.4, which is the same jump the
    # opener is written for.
    ("ledges", [n("accent", arc=3.4, lift=2, hug=3.6, spread=1,
                  ceiling=2, orbs=1),
                n("ground", arc=2.9, step_y=0, hug=3.6, kind="walk",
                  ceiling=3),
                n("rock", arc=3.0, step_y=1, hug=3.4, pedestal=False,
                  orbs=1),
                n("ground", arc=2.9, step_y=0, hug=3.4, kind="walk",
                  pedestal=False, ceiling=3),
                n("glow", arc=3.0, step_y=1, hug=3.0, pedestal=False,
                  deco="lamp", ceiling=2, orbs=1),
                n("accent", arc=4.4, lift=2, step_y=-2, hug=3.8, pedestal=False,
                  orbs=2)]),
], exit_beats=[
    # THE CUT STAIR. Eight treads winding up the inside of the shaft
    # wall, banded white and black, lit at every second one and lidded
    # on the odd ones, and it is the level rather than the bill for it.
    #
    # **Eight, because ``rise=8`` cannot be climbed in fewer.** One jump
    # impulse rises 1.25 m and nothing in this motion model gains two
    # blocks in one ballistic move -- the discriminant has no solution,
    # exactly as in vanilla -- so a stair up eight blocks is eight
    # treads whatever anybody would prefer. What is a choice is whether
    # those eight landings are the generated staircase, which is grey
    # cone stone against sky and about a third of everything the viewer
    # sees, or the thing the level is named after.
    #
    # The arithmetic of the height. The foot is ``lift=1``, the eight
    # treads gain one each on ``step_y``, so the head stands at 9 -- one
    # block above the next level's floor, and the crossing comes down
    # that block, because dropping one buys nearly another metre of
    # reach over a flat jump's 4.26. A stair that *overshoots* is a
    # level above that opens by dropping back onto its own terrace,
    # which is the owner's "it puts a ladder there and then jumps back
    # down to a lower part"; a stair that undershoots asks the crossing
    # to gain height it has no impulse for, and that is 68 of 71 stuck
    # landings when it was instrumented.
    #
    # Each tread is ``arc`` 3.0, a reach of 2.32 in a +1 window of
    # 2.00-3.10. Nine landings at three metres is 27.2 m of terrace
    # against the ``(need + 1) * 3.2`` the trigger reserves, so the head
    # of the stair clears the chasm with a landing in hand. Note that a
    # ``step_y`` node's fallback arcs are *longer* than the one written
    # (``arc``, 1.14x, 1.28x) rather than shorter, so a tread written at
    # the top of its window has nowhere to fall back to.
    #
    # **The foot stands at ``hug=3.0`` and the head at 3.6.** One level
    # measured 69 wall-jammed frames of 1,293 with its launch landing at
    # 2.2 and **0 of 1,280** at 2.8; the camera locks onto the landing
    # through take-off and flight, so a foot tucked against the core
    # aims the whole climb at the cliff. Winding out as it rises also
    # puts sky rather than rock behind the last thing before the leap
    # into the next level.
    #
    # **No ``shell`` on any of it**, on purpose. A shell is painted the
    # moment its landing commits and its roof then refuses the next arc
    # of the same feature, and every tread here has a tread after it;
    # ``shell="shaft"`` round an authored exit is worse again -- taking
    # one off a vine elsewhere took *body inside the world* from 3
    # frames of 556 to 0 and the jammed lens from 18.2% to 10.4%. What
    # the treads carry instead is a ``ceiling`` beam on **every** one of
    # them, which is the cheapest overhead mass a level author has:
    # chained tread to tread they fill the one column of the ray fan
    # that looks where the body is going, and beams on an exit climb
    # alone took one level from 64% to 55% empty. Lidding half of them
    # is the usual advice and it is advice about *light* -- a lid within
    # eight blocks of the head makes ``_indoor_want`` return 0.85 and
    # takes 27% off every tint in the frame. On this level that is the
    # right answer rather than a cost: a body climbing a stair cut up
    # the inside of a shaft ought to read as indoors, and at the theme's
    # inherited ``dark=0.86`` the lid would have been free *and*
    # invisible, which is the arrangement worth avoiding.
    n("accent", arc=3.2, step_y=0, hug=3.0, spread=2, confine=True,
      deco="lamp", ceiling=3, orbs=1),
    n("deepslate", arc=3.0, step_y=1, hug=3.2, spread=0, ceiling=2, orbs=1),
    n("calcite", arc=3.0, step_y=1, hug=3.2, spread=0, ceiling=2),
    n("glow", arc=3.0, step_y=1, hug=3.2, spread=0, deco="lamp",
      ceiling=2, orbs=1),
    n("calcite", arc=3.0, step_y=1, hug=3.4, spread=0, ceiling=2),
    n("deepslate", arc=3.0, step_y=1, hug=3.4, spread=0, ceiling=2, orbs=1),
    n("calcite", arc=3.0, step_y=1, hug=3.4, spread=0, ceiling=2),
    n("glow", arc=3.0, step_y=1, hug=3.6, spread=0, deco="lamp",
      ceiling=3, orbs=2),
])
