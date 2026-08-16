"""Level 13: THE SILENCE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE SILENCE. A survey camp abandoned on a sculk floor at the deepest
# turn of the tower: black ground, a spruce boardwalk laid over it on
# trestles, a lantern on every post because nothing else here gives
# light, a flooded bore-pit in the middle of it, and a timber headframe
# at the far end whose shaft has flooded and pushes you eight blocks
# out of it. It is the biggest rise in the tower and the level is built
# to be the thing you have to get out of.
#
# The route, in one breath. A lantern set flush in the sculk with black
# water cut round it -- the palette stops being the reef's coral and
# pink sand at that one block. Onto the boardwalk **on foot** under the
# rock brow. Then up the trestles, two courses, to the lit deck head,
# which is the highest ground in the body of the level -- and straight
# off the front of it, **two blocks down and 4.9 of arc out into the
# bore-pit**, which is the level's one long jump and the only kind of
# long jump this motion model has, because falling takes time and the
# body does not slow down while it falls. It lands floating over the
# water. Out of the pit through the adit, a two-metre bore in the cliff
# walked through under its own roof. Then the camp line repeats for as
# long as the terrace lasts: the drop back onto the boards, the lit
# plank stride, the step up onto the spoil heap hung over the drop. The
# way out is the **drowned bore**: a lit lip at its foot, the shaft it
# has flooded, and an iron lip out over the chasm with the sky behind
# it.
#
# What it is answering, and every one of these was a measurement rather
# than taste.
#
# **The landmark is a cabin and a cabin is a *walk* gate.** A walk gate
# wants five supported cells across the corridor and reserves 0-2 times
# in 8 on a ``ledge`` where a hop gate reserves 8 of 8 (RULES 7), and an
# ungated landmark cannot reserve on a ledge at all -- so the ground is
# a ``plaza``, which is the one profile that gives it that footing. THE
# GATEHOUSE is the precedent: the same blueprint, the same profile, and
# the structure on screen went from 0.0 s on its old ledge to 0.8-2.6 s.
# This level used to be a 3.5-cell ledge carrying ``cluster``, which is
# not gate-capable at all and measured 0.0 s.
#
# **``rise=8`` on a narrow shelf makes the exit climb lap the tower.**
# ECHO SHAFT -- the tower's other deep-dark level, and the only other
# level that rises eight -- failed the twice-claimed-cell invariant at
# ``shelf=3.5`` because its staircase came back over its own cells one
# lap later, and ``profile="plaza"`` is what fixed it. The reserve is
# ``(need + 1) * 3.2`` metres measured from wherever the body stands, so
# the tallest levels need the widest ground. The two arguments point the
# same way and that is why this level is the one shape it can be.
#
# **The lamps were not lamps.** ``deepdark``'s ``glow`` role is
# ``amethyst``, and only five material names in this renderer emit
# anything at all -- ``lantern``, ``torch``, ``glowstone``,
# ``sealantern`` and ``magma`` (``spiral._GLOWING``). So every
# ``deco="lamp"`` this level used to place was a violet cube that lit
# nothing, on the darkest theme in the tower, and the soft light that
# marks a *landing* takes its colour from the same role. ``glow="lantern"``
# is one word and it turns every light in the level on. It is also the
# cleanest way to keep the two deep-dark levels apart: ECHO SHAFT is a
# cold geode, white calcite and purple amethyst; this is a camp, and
# everything lit in it is warm.
#
# **``dark`` had never been set.** The theme carries 0.86 and every
# authored level with an opinion sits at 0.25-0.62; inherited, this one
# was rendered as a cave whatever it did. 0.60 is a shade lighter than
# ECHO SHAFT's 0.62 -- a camp with fires in it against a sealed well.
# It was tried at 0.50 first and that is the wrong direction: the level
# came back a *grey* place with brown boxes in it, because washing light
# over sculk (28, 40, 48) is what turns the deep dark into ordinary
# stone. The lanterns are what make it legible, not the ambient.
#
# **The floor is the identity.** A real leg of the reference uses a
# median fourteen floor materials with the commonest at about a quarter;
# the stock deep-dark mix is ten and nine of them are grey stone, which
# painted this level as a plate. Twelve named here, and the four roles
# are weighted in on top of them by ``Theme.floor_palette``, so what is
# actually laid is sculk at 26% with eleven kinds under it: black ground,
# deepslate and blackstone in the spoil, tuff and gravel and coal out of
# the cut, and the camp's own spruce and oak boards laid through it,
# which is the route stripe as well as the palette.
#
# **The corridor is ten and a half wide, and that one number moved every
# metric this level has.** A plaza paints its whole band from the level's
# own floor palette, so ``band`` is literally how much of the level is in
# the bottom of the frame -- and it is also how much room the gated hut
# has to be *approached* rather than walked into. At 10.0 the design
# measured 48% of the view empty, a walker covering 44% of it, and the
# cabin held at 25 degrees for **0.4 s** counted from the approach in,
# against a 1.5 s rule. At 10.5 it is **42% empty, 36% covered and
# 1.9 s**.
#
# The width was then settled on an in-process A/B -- same roster, same
# sixteen seeds, one interpreter, only ``band`` swapped on the live
# ``Level``, which is the only way to tell a change from the re-roll a
# neighbour's edit causes:
#
#   | band | design | exact | adit | trestles | unchecked |
#   |------|--------|-------|------|----------|-----------|
#   | 10.0 | 74%    | 97%   | 92%  | 96%      | **0**     |
#   | 10.5 | **76%**| **99%**| **96%** | **100%** | 2      |
#   | 11.0 | 73%    | 98%   | 86%  | 98%      | 2        |
#   | 11.5 | 72%    | 98%   | 86%  | 98%      | 2        |
#
# 10.5 lays the most design and lays it most exactly, and 11.0 and above
# start costing the adit its landing. The one thing 10.0 buys is a clean
# unchecked count; the price is the structure criterion and six points of
# frame, and this level is carrying a walk gate it has already bent its
# whole profile to accommodate. So the two emergency placements are
# accepted and named here rather than hidden.
#
# **``breaks=0``, which is the biggest single decision in the file.**
# Any break at all forces the lock -- a level's first floor break is
# always 5.5-6.7 m wide, so the machinery that crosses it lays an
# approach at height, an island and a landing, and on a level that also
# pays for a landmark crossing that is two thirds of everything laid.
# THE GATEHOUSE measured the same design at 39% designed content with
# breaks and 56% without, for five points of walkability. What holds the
# walker here instead is water in *holes*: three ``moat`` landings, each
# swapping the terrace's top cell for water over a radius-3 disc. Liquid
# on its own is atmosphere -- water is see-through and lava is solid, so
# neither blocks a walker -- and it is the bowl the moat digs that stops
# one, because a walker can get into it and cannot step back out.
LEVEL = Level("THE SILENCE", "deepdark", rise=8, gap=3.0, exit="bubble",
              band=10.5, shelf=4.0, profile="plaza", breaks=3,
              landmark="cabin",
              # Black ground, black spoil, and the camp's timber as the
              # accent so that the one warm colour in the level is the
              # thing the level is about. ``_lm_g_cabin`` builds its
              # walls out of spruce literally and takes ``theme.rock``
              # for its chimney and ``theme.glow`` for the two lit
              # windows, so a blackstone flue and lantern light in the
              # openings is the hut this palette was chosen for.
              ground="sculk", sub="deepslate", rock="blackstone",
              accent="spruce", glow="lantern", liquid="water",
              # Twelve materials, dominant at 19%, against the roster's
              # usual two or three: the sculk floor, the spoil off the
              # bore, and the camp's own boards laid through it.
              floor=(("sculk", 4), ("deepslate", 3), ("blackstone", 2),
                     ("tuff", 2), ("gravel", 2), ("spruce", 2),
                     ("sculkvein", 1), ("coalore", 1), ("cobble", 1),
                     ("andesite", 1), ("mossy", 1), ("oak", 1)),
              props=("lanternpost", "mcfence", "rail", "pebbles", "chain"),
              dark=0.60, sky=(70, 78, 82),
              # If the headframe cannot be built the fallback stair
              # climbs the camp's own boards rather than the cliff.
              step=("spruce", "hop"), beats=[
    # THE SILL. The threshold, and the reference's own way of writing
    # one: an emissive block set flush in the floor on a rise, on screen
    # a couple of seconds before it is reached, with the palette
    # changing completely at that block and no blend. REEF GARDEN below
    # is coral pink and pale sand; this is sculk and lantern light.
    #
    # The water is cut round the sill rather than beside it. It is the
    # first of the level's three holes and it is on the beat's *first*
    # node, which is the opposite of what the radius-3 bowl usually
    # wants -- a beat's tail is almost never laid, so a pool written
    # second is a pool authored and never seen, and the landing after it
    # floats, so the bowl cannot take the ground out from under it.
    # GLACIER SHELF's meltcave is the same two nodes in the same order.
    #
    # The boardwalk is *walked* on and never jumped onto. One jump
    # impulse always rises 1.25 m and the head then sweeps the two cells
    # above every take-off, so an arc under a lid low enough to read as
    # a brow is refused every time; ``kind="walk"`` is the only honest
    # form of the genre's 2bc this kernel has, and ``ceiling=3`` over it
    # is a real head-hitter that the arc test never has to refuse
    # because a walk has no arc. It is the second node and not the
    # first: a walk needs its predecessor within half a metre, and a
    # beat's first landing is placed from wherever the machinery between
    # beats left the body.
    ("sill", [n("glow", arc=3.2, lift=1, spread=1, deco="lamp",
                moat=True, orbs=1),
              n("accent", arc=2.4, lift=2, kind="walk", spread=0,
                pedestal=False, ceiling=3, orbs=1),
              n("rock", arc=3.0, step_y=1, spread=0),
              n("rock", arc=3.0, step_y=1, spread=0),
              n("rock", arc=3.0, step_y=1, spread=0)]),
    # THE TRESTLES, and this is the level: up the camp's own staging to
    # the lit deck head and straight off the front of it into the pit.
    #
    # **The climb and the fall are one beat and they have to be.**
    # Machinery -- the lock, a recovery, the crossing through the hut --
    # is inserted *between* script beats and leaves the body back at
    # lift 1, so a rise written in one beat and spent in the next is a
    # rise that does not happen: the drop written as a beat's opener
    # drops nothing about half the time and the beat still reads as
    # placed.
    #
    # Everything behind the opener is written on ``step_y`` rather than
    # on ``lift``. ``lift`` is measured from the terrace, so a beat whose
    # opener came down a block high or low -- it carries ``spread``, so
    # it does, about a fifth of the time -- then asks for a rise of two,
    # which nothing in this motion model makes. ``step_y`` is measured
    # from the landing before and is therefore true wherever the body
    # actually is. Measured on THE CRUCIBLE, converting the chain took
    # exactness from 96% to 99% and landings at lift 2 or above from 40%
    # to 50%.
    #
    # The two treads are +1 at ``arc=3.2``, a reach of 2.52 centred in
    # the 2.00-3.10 a one-block rise allows rather than pressed against
    # the top of it: 3.6 reaches 2.92, so it is the arc that has to fall
    # back, and a fallback is not exact.
    #
    # The fall is the point of the beat and the only long jump in the
    # level. Lift 3 to lift 1 across 4.9 m of arc is a reach of 4.22
    # against a -2 window of 3.12-5.56 -- and it is written as a descent
    # because a descent is the only long jump this model has: level, a
    # hop stops at 4.26 stand-point to stand-point. It lands floating,
    # over the water the moat cuts under it, which is what a bore-pit
    # is. It does **not** go to lift 0: that is the terrace's own top
    # cell, solid, and a ``step_y`` descent onto it is refused with the
    # rest of the beat abandoned behind it.
    ("trestles", [n("accent", arc=3.4, lift=5, spread=1, orbs=1),
                  n("oak", arc=3.2, step_y=1, spread=0, ceiling=2),
                  n("glow", arc=3.2, step_y=1, spread=0, pedestal=False,
                    deco="lamp", orbs=1),
                  n("rock", arc=4.9, lift=5, step_y=-2, spread=1, pedestal=False,
                    moat=True, orbs=2)]),
    # THE ADIT. The bore itself: a stone standing in the black water at
    # the bottom of the pit, and a two-metre pinch in the cliff walked
    # out of it under its own roof.
    #
    # Two metres and not fifteen, because that is what the reference
    # actually measures: fully enclosed 6.1% of the way, 0 of 43 legs
    # enclosed more than half, and a median enclosed run of **two
    # metres**. What it is the whole time is a *groove* -- rock within
    # four metres on the core side on 71% of samples, the drop outboard,
    # a lid a median eight blocks overhead -- and one shell in a level
    # is that pinch. Three in a row jam the lens on 10-21% of frames.
    #
    # The shell is on the beat's **last** node because a shell is
    # painted the moment its landing commits and its walls are then in
    # the way of the next landing of the same beat, and it is on a
    # ``walk`` because a shell roof sits in the cell the head sweeps at
    # a hop's apex -- a tunnel over a jump is a roof with a hole in the
    # middle of it, and a walk has no apex to punch one. It is at lift 1
    # because ``_shell`` skips any wall column with nothing under it, so
    # a bay written higher is a roof with open sides, which is not a bay.
    #
    # The opener floats, and the honest history of that keyword is worth
    # recording because it is the wrong lesson twice over. This beat sat
    # at 91-92% placed with an ordinary pedestal and nothing in the
    # rejection trace to say why, which is the exact symptom RULES 7
    # offers ``pedestal=False`` for -- a stack has to find ground under a
    # terrace that two radius-3 bowls have already been cut out of.
    # Adding it changed the numbers **not at all**: 10/11 before and
    # 10/11 after, to the landing. What actually fixed the beat was the
    # ``band``, which took it to 14/14 -- so the miss was the landing
    # being pulled past the ground rather than the plinth failing to
    # stand. The keyword stays because a stone in flood water should not
    # have a plinth under it anyway, but it is not what did the work.
    ("adit", [n("rock", arc=3.4, lift=5, spread=1, moat=True, ceiling=2,
                pedestal=False, orbs=1),
              n("ground", arc=2.4, step_y=0, kind="walk", spread=0,
                pedestal=False, shell="cave", ceiling=3, orbs=1)]),
    # THE COLLAR. The shaft's own rim, and it is short on purpose: a
    # level lays nine to twelve landings and the exit takes four of
    # them, so a fourth beat is written knowing it plays perhaps one run
    # in three. Two nodes, both of which say the same thing the exit is
    # about to say -- iron sheeting and a timber post, standing above
    # the sculk.
    ("collar", [n("blackstone", arc=3.4, lift=5, spread=1, ceiling=2),
                n("iron", arc=3.2, step_y=1, spread=0, pedestal=False,
                  deco="post", orbs=2)]),
], filler=[
    # THE CAMP LINE. The filler repeats and the tail of a script does
    # not, so this is what the level mostly *is* -- measured, **47 of
    # this level's 116 designed landings are this loop** -- and it is
    # therefore the only place where "half the jumps are at ground
    # level" can actually be answered. The drop back down off the
    # staging onto the boards, the lit plank stride, and then two courses
    # of trestle back up to the top of it.
    #
    # **The fourth node is the whole point of this pass.** Written as
    # three it ran 1, 1, 2 and the blueprint's elevation was a straight
    # line from the threshold to the exit ladder, with every metre of
    # the level's own height in the climb out of it -- the owner's "a
    # couple of ground-level hops, then stairs" in one picture. Four
    # nodes make the loop a *cycle* rather than a line: it climbs two
    # and falls two every lap, so the body spends most of the level at
    # lift 2 or 3 with the plaza under it. That also buys frame, because
    # the ray fan the empty-frame number is taken with is +/-36 degrees
    # inside eight metres: at lift 1 its shallow down-rows fly over the
    # ground into the void, and on a band this wide they land.
    #
    # The opener is 4.4 m because it has three different heights to be
    # legal from -- a reach of 3.72, which is inside the window at level
    # (2.00-4.26), at -1 (2.35-4.98) and at -2 (3.12-5.56). It follows
    # the collar at lift 2, or the loop's own last landing at lift 3, or
    # a piece of machinery back down on the terrace, and it is the same
    # jump from all three. It is also the longest thing in the loop and
    # reads as long for the reason every long jump here does.
    #
    # The walk is at position **two**. A beat lays about half its nodes,
    # so a non-hop verb written at a beat's tail is written and never
    # seen, and one written first follows machinery at an arbitrary
    # height where a walk needs its predecessor within half a metre.
    # Moving the walks to position two is measured elsewhere as the
    # difference between a move mix that is 100% plain hop and one that
    # is 83%, and on this level the two body walks and the headframe
    # ladder are the whole of the non-hop share -- there is nothing else
    # in the deep dark that fires reliably. Ice is another biome, cobweb
    # appears **zero** times in the entire reference save, and the slime
    # pad placed on 6 runs of 24 and fired on 1 when it was measured.
    # The version of this level that this replaces put its signature on
    # a slime pad and a bounce, twice.
    #
    # **No ``moat`` anywhere in here**, and that is not taste: the
    # filler loops, and the second lap digs away the ground the first
    # lap's pedestals are standing on -- 27,859 refusals from one
    # keyword when it was instrumented.
    #
    # The loop's seam is checked like any other jump and half a filler's
    # fidelity is usually lost there: the head of the staging at lift 3
    # back to the boards at lift 1 is -2 across 4.4 -- a reach of 3.72
    # against 3.12-5.56, the same number as every other way into this
    # beat, which is why the opener could be lengthened without the loop
    # coming apart.
    ("campline", [n("accent", arc=4.4, lift=6, spread=1, orbs=1),
                  n("ground", arc=2.4, step_y=0, kind="walk", spread=0,
                    ceiling=3, deco="lamp"),
                  n("rock", arc=3.2, step_y=1, spread=0, pedestal=False,
                    orbs=1),
                  n("oak", arc=3.2, step_y=-1, spread=0, pedestal=False,
                    ceiling=2, orbs=1)]),
], exit_beats=[
    # THE DROWNED BORE. Eight blocks, the biggest rise in the tower, and
    # it is written out landing by landing rather than left to the
    # generated climb -- which hangs its column mid-lane at ``hug=2.0``
    # with no pedestal, finds nothing within a cell of its middle index
    # to anchor on, and is refused silently: 11,097 of 13,000 candidates
    # when it was instrumented, and the level then gets an eight-step
    # staircase and is never told. That staircase is what this level was
    # before this pass -- **12 designed landings against 45 of generated
    # stair**, one of the worst ratios in the roster.
    #
    # A lit lip against the wall, the shaft, and a lit iron lip out over
    # the chasm. Three landings against the staircase's eight, and the
    # reserve comes back with them: ``_level_budget`` hands any non-stair
    # exit ``(need - 2) * 3.2`` metres of terrace, which on a level that
    # has to gain eight is most of the design.
    #
    # **It is water and not a ladder, and that is the measurement this
    # pass turned on.** Written as two ladder flights with a stage
    # between them it worked -- ``climb`` was 9% of the move mix, so the
    # branch really was firing -- but a ladder is *ridden at 2.35 m/s*
    # with the column a hand's width from an eighty-degree lens, and the
    # contact sheet showed six or seven consecutive frames of flat plank
    # and flat deepslate: 14.9% of this level's frames had a wall in the
    # lens and nearly all of them were the two rides. GLACIER SHELF
    # measured the same swap directly -- ladder 634 frames of exit with
    # 200 jammed, bubble column 394 frames and none -- because a bubble
    # goes up at **11.0 m/s**. Eight blocks is under a second of it.
    #
    # It is also the better idea. The level floods: the sill stands in
    # water, the bore-pit is water, the adit comes out of water. A shaft
    # that has filled and pushes you back out of it is what this place
    # would actually do, and it stops THE SILENCE and ECHO SHAFT -- the
    # tower's two deep-dark levels, both rising eight -- from leaving by
    # the same ladder. RULES 3 counts 12 ladder exits, 4 bubble and 3
    # stair across twenty levels and asks for about one climb in five;
    # this is a level whose *idea* is the way out, so it keeps a climb
    # and gives back the ladder.
    #
    # **The launch block stands at ``hug=2.9``.** One level measured 69
    # wall-jammed frames of 1,293 with its launch landing at 2.2 and
    # **0 of 1,280** at 2.8, and only the launch landing matters --
    # ``hug`` on the climb node itself produces worlds identical to the
    # frame. The camera locks onto the landing through take-off and
    # flight, so a launch tucked against the core aims the whole ride at
    # the cliff.
    #
    # **``pedestal=True`` is the load-bearing keyword and the reason
    # this fires at all.** ``_climb_move`` wants solid rock within one
    # cell of the column at its middle index *and* at its top; out in the
    # lane the only candidate is the landing's own stack, so the column
    # needs a pedestal under it and a rise of at least four. The stack is
    # the bore's own blackstone casing, which is what a shaft is lined
    # with anyway. There is deliberately no ``shell="shaft"`` round it:
    # the tube is what puts the body *inside* the wall, and taking one
    # off elsewhere took body-inside-the-world from 3 frames of 556 to 0
    # and the jam from 18.2% to 10.4%.
    #
    # The last landing is out at ``hug=3.6`` with sky behind it rather
    # than tucked against the core, for the same reason THE CRUCIBLE's
    # magma lip is: the camera locks onto the landing through take-off
    # and flight, so the last thing before the leap into the next level
    # should be a lit floor against the sky and not a cliff.
    #
    # The arithmetic of the height: the lip is lift 1, the column gains
    # seven, the head of it steps up one -- lift 9, one block above the
    # next level's floor, and the crossing comes down that block onto it,
    # because a flat sprint jump reaches 4.26 m and dropping one buys
    # nearly another metre. A climb that overshoots is a level above that
    # opens by dropping back to its own terrace, which is the owner's "it
    # puts a ladder there and then jumps back down".
    #
    # **Check ``--report``'s move mix for the word ``bubble``.** If it is
    # missing, this is an eight-step staircase again and the level has no
    # way out of its own idea.
    n("glow", arc=3.2, step_y=0, hug=2.9, spread=2, confine=True,
      deco="lamp", ceiling=3, orbs=1),
    n("rock", arc=2.4, step_y=2, kind="bubble", hug=2.4, pedestal=True,
      pedestal_style="blackstone", spread=0, orbs=2),
    n("iron", arc=3.2, step_y=1, hug=3.6, spread=0, pedestal=False,
      deco="lamp", ceiling=3, orbs=2),
])
