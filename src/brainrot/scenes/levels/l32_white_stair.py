"""Level 32: THE WHITE STAIR.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A white court with the sea standing in it.
#
# One sentence: *you come up out of the black shaft onto a lit block of
# quartz, walk through a gilded doorway, climb a pier, step out onto the
# parapet over the drop, climb again and then fall three blocks into a
# basin cut out of the court's own paving -- and from there the level is
# a rank of gold-capped piers marching along a flooded white pavement to
# the great arch, and the stair the level is named after going up
# through it.*
#
# The thing a viewer would remember is the arch: two calcite piers and a
# gold lintel with a lantern hung under each side, standing where the
# court ends, with the stair behind it. The course runs *through* it,
# which is the only reason a structure in this tower is ever seen.
#
# ---------------------------------------------------------------------
# **The frozen landmark decided the profile, and the old profile threw
# it away.** ``landmark="arch"`` is assigned centrally and this level was
# left on ``profile="channel"`` under it, which is the one combination
# ``docs/RULES.md`` §7 has a measurement for: the liquid cut runs exactly
# where the lane runs, ``Cone.rock`` is False under it, and the gate's
# base cells have nothing to stand on. Instrumented here on the final
# design over twelve runs, counting ``Course.landmark_cross``,
# ``_crossed`` and ``_gate_hit`` directly rather than inferring from the
# frame:
#
# | over 20 level visits | channel | plaza |
# |---|---|---|
# | the gate reserved at all | **0** | **17** |
# | the crossing offered | 0 | 18 |
# | a landing *inside* the structure | 0 | 11 |
# | designed content (24 runs) | 50% | 44% |
# | placed as authored | 95% | **97%** |
# | unchecked emergency placements | 0 | 0 |
# | plain hop | 81% | 84% |
# | walker coverage, mean / worst | 41 / 59% | 43 / 59% |
#
# So the bill for the arch is six points of designed content and three
# of hop share, and it is worth paying: on a channel this level holds a
# gate it can never stand up, pays the reservation anyway, and its one
# structure does not exist. Everything else the channel was doing --
# hazard across the whole width, ground a walker falls into and cannot
# climb out of -- the three ``moat`` ponds do on a plaza, and the walk
# number is the same to within noise. Water on the walking line stops
# nothing; the *hole* it is standing in stops everything
# (``docs/RULES.md`` §7).
#
# ---------------------------------------------------------------------
# **The court was being painted as somebody else's cliff, and that is
# the biggest thing in this file.** ``docs/RULES.md`` §7 records it as a
# symptom "reported, not reproduced": a level whose floor comes back grey
# cone stone, fixed by dropping the band. It reproduces exactly, and the
# mechanism is the paint order. At one layer of the world the cone draws
# the *core wall of the level whose trough is at that height* -- three
# levels below this one -- before it draws the slab that is this level's
# terrace, and ``_ring`` skips a cell another ring already claimed. So
# everything inboard of ``outer - band(level - 3)`` is painted as that
# level's banded cliff and this level's floor palette never gets to it.
# At ``band=13.0`` against THE CORNICE's 10.5 that was a **2.5-block
# strip against the core wall -- exactly the lane the course hugs**, and
# it is why the old sheet came back grey whatever the palette said. The
# proof is one render: with ``floor`` forced to solid gold the ground
# under the body did not change colour at all.
#
# The rule that falls out, and it is a tower-wide one: **a level's band
# may not exceed the band of the section three below it, and its
# smallest ``hug`` must clear the difference.** This level is at 10.5,
# which is CORNICE's own; measured at 24 runs, 10.0 / 10.5 / 11.0 read
# unchecked 2 / **0** / 3 and exact 97 / **97** / 94, and 10.5 also read
# the lowest empty frame of the three. If a neighbour ever narrows, the
# course is still clear of the strip while ``hug >= band - band_below``,
# which at this level's smallest ``hug`` of 2.4 holds until the section
# three below drops under 8.1 -- and only the foot of the wall greys
# before that.
#
# **And the pond beds were the other half of the grey.** ``_slab`` paints
# the cell under the terrace top as ``theme.sub``, and a ``moat`` digs
# the top cell out -- so what you see through the water is ``sub``, and
# ``sub`` was deepslate. Three ponds of dark bed under blue water is most
# of the lower frame on a level whose subject is brightness. ``sub`` is
# ``diorite`` now (216, 212, 208), the basins read as water over white
# stone, and the dark value the composition rule wants is carried where
# it belongs -- overhead in the beams, and as an inlay in the paving --
# by naming ``deepslate`` on the nodes that want it rather than by the
# role.
#
# **Lids are free on this level, which is not true of most.**
# ``spiral._indoor_want`` returns ``max(theme.dark, 0.85)`` the moment
# any cell three to eight over the body is solid, and this level's
# head-room is **eight blocks** -- the tightest in the tower, since its
# own rise and its two neighbours' sum to the minimum the head-room rule
# allows. Measured: the body is under a roof on **26 landings of 26**
# here, against 5 of 23 on THE CORNICE and 7 of 24 on ECHO SHAFT. So the
# 32% the tint takes off is already being taken whatever this file does,
# and a ``ceiling`` beam costs nothing but the cells it stands in. Half
# the landings carry one, which is how the top of the frame gets the
# entablature the composition rule asks for.
#
# One correction worth recording while it is in front of somebody: the
# ``sky`` role is **not the sky**. ``SkyDome`` is built from the run's
# palette and never sees a theme; ``theme.sky`` only feeds
# ``ring_light``, the colour distant geometry is tinted toward. A deep
# azure here therefore buys depth in the far half of the frame and
# changes nothing above the horizon.
#
# **Every beat climbs and then falls off the end of itself.** That shape
# is the two rules meeting: the owner's "half the jumps are at ground
# level" wants the middle of a beat high, and ``docs/RULES.md`` §7's
# "machinery is inserted between beats and leaves the body at lift 1"
# wants a beat to *end* low, because the lock's own approach hops are
# written at ``arc`` 2.6 and cannot come down four blocks. So each beat
# goes 1 - 2 - 3 - 4 and then throws the height away in one long
# descent, which is also the only long jump this motion model has and
# the reference's own way of losing altitude: eleven blocks travelled to
# gain four, by falling off edges rather than jumping down.
#
# Against ECHO SHAFT below (sculk, amethyst, a black well) and THE GATE
# above (obsidian, endstone, lava) this is the one bright place in the
# last third of the tower, and the only one of the three with standing
# water in it.
LEVEL = Level("THE WHITE STAIR", "quartz", rise=5, gap=2.8, exit="bubble",
              landmark="arch",
              band=10.5, profile="plaza", breaks=2,
              # Six roles. Quartz paving underfoot and calcite for
              # everything built, so the piers, the plinths, the treads
              # and the arch's own two columns are a shade off the floor
              # rather than a contrasting jump block -- a cake and a
              # cobblestone have the same hitbox, and what marks a
              # landing here is that it is lit. ``sub`` is the pale
              # stone the basins are cut into (see above); gold is every
              # trim; and the dark value is named block by block.
              ground="quartz", sub="diorite", rock="calcite",
              accent="gold", glow="lantern", liquid="water",
              props=("lanternpost", "mcfence", "chain", "lilypad",
                     "pebbles"),
              # A deep azure *light*, not a sky (see above): distant
              # stone is pulled toward it, which is what keeps the far
              # half of a white level from washing out into the haze.
              # ``dark`` is nearly nothing -- this is the brightest
              # place in the tower and the only thing dimming it is the
              # soffit eight blocks up, which no level can help.
              sky=(104, 148, 202), dark=0.10,
              step=("calcite", "hop"),
              # Thirteen materials with the dominant one at 23% and a
              # mean luminance of 198, which is the shape a real terrace
              # measures as (median 14 kinds, dominant 26%) -- against
              # the two this level used to have. The mid-greys are the
              # ones that had to go: ``andesite`` (150, 150, 148) and
              # ``stone`` (146, 146, 150) are one value with two names
              # and neither is white, so a white court paved in them
              # comes back the colour of the cone it stands on. What is
              # left is a family of pale stones that differ in *hue* --
              # quartz warm-white, calcite neutral, plaster cream,
              # chiselled and sandstone sand, iron and glass cold --
              # with gold, deepslate and blackstone as the dark inlay.
              floor=(("quartz", 3), ("calcite", 3), ("plaster", 2),
                     ("chiselled", 2), ("sandstone", 2), ("iron", 2),
                     ("deepslate", 2), ("gold", 1), ("terra_white", 1),
                     ("glass", 1), ("blackstone", 1), ("stone", 1)),
              beats=[
    # THE SILL -- the threshold, the doorway, the two piers, the parapet
    # and the fall into the basin. Seven nodes in one beat, because this
    # is the beat that is never truncated (it opens the level and
    # competes with nothing for terrace -- measured, its first six
    # landings are laid on 23 visits of 23 and its seventh on 21) and
    # because the rise and the drop have to be in the *same* beat:
    # machinery between beats hands the body back at lift 1, so a fall
    # written as a beat's first node is not a fall.
    #
    # 1. A lantern set flush in the quartz, lit, on a rise. The
    #    reference's own way of saying a level begins -- an emissive
    #    block in the floor with the palette changing completely at it
    #    and no blend. Eleven seconds of black sculk and amethyst behind
    #    it; white stone, gold and a blue sky from here. ``lift=1`` and
    #    not 2: an opener is placed from wherever the machinery before
    #    it left the body, and the identical beat measures 67% at lift 2
    #    against 100% at lift 1.
    # 2. **Through the gilded doorway on foot**, under a gold beam three
    #    cells over the take-off. This is the genre's ``2bc`` and the
    #    only honest form of it this kernel has: one impulse rises
    #    1.25 m and the head then sweeps the two cells above every
    #    take-off, so a lintel low enough to read as a doorway refuses
    #    every arc under it -- it is expressible only over a leg that
    #    never leaves the ground. 2.9 of arc is 2.22 m of ground against
    #    a walk's 2.4 limit. It asks for the **same lift** as the opener,
    #    which is the other half of that rule: the opener carries
    #    ``spread`` and sits a block high or low about a fifth of the
    #    time, and ``lift + 1`` after it is a rise of two, which nothing
    #    in this motion model makes. ``pedestal_style="gold"`` paints the
    #    lid as well as the plinth, so the beam over the doorway is gold
    #    and not one more white slab -- left unset a ``ceiling=`` lid
    #    comes out as ``theme.rock``, which on this level is calcite.
    # 3. Up onto the first pier. ``arc`` 3.2 is a reach of 2.52 against
    #    a +1 window of 2.00-3.10 -- centred rather than at the top of
    #    it, because a +1 written at 3.6 is a reach of 2.92 and is the
    #    arc that has to fall back, and a fallback is not ``exact``.
    # 4. **Out onto the parapet over the drop, on foot.** A deepslate
    #    coping block with a gold baluster on it, floated at the far
    #    edge of the court, level with the pier -- the one place in the
    #    level the body stands with nothing but sea under the frame.
    #    It is the beat's second walk and it is here rather than at the
    #    tail for the usual reason (a verb written last is written and
    #    never seen); it is also the cheapest landing in the level, and
    #    a cheap landing is worth more than it looks, because designed
    #    content is a *share* and a beat written in 4.9s buys fewer
    #    landings per metre of terrace than one written in 2.9s.
    # 5. And up again onto the second pier, under a dark beam. Surface
    #    4.0 by the fifth landing of the level, which is what "get off
    #    the floor" means: 55% of authored landings across this roster
    #    sit at lift 0 or 1.
    # 6. **Three blocks down into the basin, and it is the level's long
    #    jump.** A descent is the only long jump this engine has --
    #    falling takes time and the body does not slow down while it
    #    does -- so 4.9 of arc is a reach of 4.22 against a -3 window of
    #    3.72-6.05, and it stays legal at -2 (3.12-5.56) and at -1
    #    (2.35-4.98), which means it does not care which of the two
    #    piers the body actually reached.
    #
    #    ``form="floor"`` puts the body on the court's own paving and
    #    ``moat=True`` digs the paving out from round it: what is left
    #    standing in the water is the one flag the basin was cut around.
    #    A no-jump walker that reaches it is in a bowl it cannot climb
    #    out of, which is what a moat is actually for -- the liquid
    #    stops nothing, the hole stops everything.
    # 7. **Out of the water up a half-height kerb, walked.** A slab
    #    stands half a block down in its own cell, so ``step_y=1`` on one
    #    is a +0.5 step -- inside the 0.55 a walk allows -- and this is
    #    the one place a landing that had to exist anyway could be a verb
    #    instead of a hop. Worth a point of the level's hop share on its
    #    own. It floats, because a pedestal cannot stand in the hole the
    #    node before it just dug.
    ("sill", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                orbs=1),
              n("accent", arc=2.9, lift=1, hug=3.0, kind="walk", ceiling=3,
                pedestal_style="gold"),
              n("rock", arc=3.2, step_y=1, hug=3.0, orbs=1),
              n("deepslate", arc=2.9, step_y=0, hug=4.2, kind="walk",
                pedestal=False, deco="post"),
              n("chiselled", arc=3.2, step_y=1, hug=3.2, ceiling=3,
                pedestal_style="deepslate"),
              n("ground", arc=4.9, lift=0, form="floor", hug=3.6, spread=0,
                moat=True, orbs=2),
              n("rock", arc=2.9, step_y=1, form="slab", kind="walk",
                hug=3.4, pedestal=False, ceiling=3,
                pedestal_style="deepslate", orbs=1)]),
    # THE COLONNADE -- the rank of piers the court is built round, and
    # the level's half-height architecture. Stairs and slabs are the
    # commonest non-cube form in the reference by a wide margin and this
    # tower has almost none of them.
    #
    # 1. A calcite kerb on the paved stripe, at lift 1 with ``spread``,
    #    because whatever ran before this is machinery and put the body
    #    back on the floor.
    # 2. **A half-height step, walked.** ``form="slab"`` stands half a
    #    block down in its own cell, so this is a +0.5 stride -- inside
    #    the 0.55 of height and the 2.4 m of ground a walk allows -- and
    #    it is at position **two** because a beat lays about half its
    #    nodes and a non-hop verb written at the tail is written and
    #    never seen.
    # 3. Off the slab onto the first gold cap: another +0.5, because
    #    ``step_y`` is measured between walking surfaces and floors the
    #    result, so a whole block asked for from a slab is half a block
    #    got. The two of them together are the split climb
    #    ``docs/RULES.md`` §1 recommends and could not be done in one
    #    hop -- and they read as two shallow marble steps, which is what
    #    the level is named after.
    # 4. **Along the top of the entablature at a run**, under the next
    #    beam, with a gold baluster on the block. A walk is level by
    #    definition, so this is the one node in the beat that costs no
    #    height, and it is what makes the colonnade read as a colonnade
    #    rather than as three steps: you are *in* the architecture, not
    #    stepping over it.
    # 5. Up a whole block onto the tall pier.
    # 6. **Off the end of the colonnade, two blocks down onto a bar
    #    standing in the water**, floating, with the second of the
    #    level's three ponds cut under the jump. Reach 4.22 against a -2
    #    window of 3.12-5.56. It is the beat's last node for two
    #    reasons: it leaves the body at lift 1 where the machinery that
    #    follows can pick it up, and a ``moat`` blocks the *next*
    #    landing of its own beat, so it can only ever be last.
    ("colonnade", [n("rock", arc=3.4, lift=1, hug=2.8, spread=1, orbs=1),
                   n("ground", arc=2.8, step_y=1, form="slab", kind="walk",
                     hug=2.8, ceiling=3, pedestal_style="gold",
                     deco="lamp"),
                   n("accent", arc=3.2, step_y=1, hug=3.0, ceiling=5,
                     pedestal_style="gold", orbs=1),
                   n("rock", arc=2.9, step_y=0, hug=3.0, kind="walk",
                     ceiling=3, deco="post"),
                   n("chiselled", arc=3.2, step_y=1, hug=3.2, ceiling=3,
                     pedestal_style="deepslate", orbs=1),
                   n("deepslate", arc=4.9, step_y=-2, hug=3.6, pedestal=False,
                     moat=True, orbs=2)]),
    # THE BASIN -- the flooded half of the court, and the stretch that
    # goes furthest out from the wall: along the dark route stripe, up
    # onto a gold bollard, out along the water's edge and down onto an
    # island of paving with the pool round three sides of it. This is
    # the beat that plays about twice in eight runs, so nothing the
    # level is *about* is in here; what is in here is the one place a
    # viewer sees the whole court at once.
    #
    # The stride is a dark one: the deepslate route stripe under a
    # five-cell beam, which is the reference's own answer to ground that
    # could be read two ways -- a carpet runner down the hall, a dirt
    # path across grass. ``ceiling=5`` rather than 3 because a lid is a
    # one-cell beam spread along the direction of travel and five of
    # them roof nearly the whole arc in the one column of the ray fan
    # that looks where you are going.
    ("basin", [n("rock", arc=3.4, lift=1, hug=3.0, spread=1, orbs=1),
               n("deepslate", arc=2.9, step_y=0, hug=3.0, kind="walk",
                 ceiling=5, pedestal_style="deepslate"),
               n("accent", arc=3.2, step_y=1, hug=3.6, deco="post",
                 pedestal_style="gold", orbs=1),
               n("ground", arc=2.9, step_y=0, hug=3.8, kind="walk",
                 pedestal_style="gold"),
               n("ground", arc=4.9, lift=0, form="floor", hug=4.0, spread=0,
                 moat=True, orbs=2),
               n("rock", arc=3.4, step_y=1, hug=3.6, pedestal=False,
                 ceiling=3, orbs=1)]),
], filler=[
    # THE COURT -- the character, repeated, because the filler loops and
    # a script's tail does not. The paved stripe, a stride under a gold
    # architrave, up onto a gold-capped pier, and down off it again.
    #
    # It neither climbs nor sinks across a lap: 2.0 - 2.0 - 3.0 - 2.0,
    # and the loop seam back onto the opener is a level hop of reach
    # 2.72 in a window of 2.00-4.26. That matters for a reason that is
    # not obvious -- the exit column is sized by what the body still has
    # to climb when it starts, so a filler drifting downhill buys the
    # level a longer staircase every time it plays.
    #
    # **No ``moat`` anywhere in here.** The filler loops, and the second
    # lap digs away the ground the first lap's pedestals are standing on
    # -- 27,859 "pedestal will not stand" refusals on the level that
    # found it. All three of this level's ponds are in beats that play
    # once.
    ("court", [n("deepslate", arc=3.4, lift=1, hug=2.8, spread=1, orbs=1),
               n("ground", arc=2.9, step_y=0, hug=2.8, kind="walk",
                 ceiling=3, pedestal_style="gold"),
               n("accent", arc=3.2, step_y=1, hug=3.0, deco="lamp",
                 pedestal_style="gold", orbs=1),
               n("rock", arc=3.4, step_y=-1, hug=3.2, pedestal=False,
                 ceiling=3, pedestal_style="deepslate")]),
], exit_beats=[
    # THE WHITE STAIR itself: the flight through the arch, and the only
    # staircase in this tower that is *meant* to be one rather than
    # reduced to one. Quartz and calcite treads with a gold newel at the
    # turn, a lantern at the foot and another at the head, and a beam
    # over the middle of it.
    #
    # **Five treads and not six, and the arithmetic is the whole of it.**
    # The foot is an absolute ``lift=2`` rather than a ``step_y``, so it
    # re-bases off whatever height the machinery before it left the body
    # at instead of adding to it; four ``step_y`` treads then finish at a
    # walking surface of **7.0** against the next terrace's 6.0, which is
    # this level's ``rise`` of 5 plus the one block ``hop_span(-1)``
    # brings the crossing down. Written on ``step_y`` and never on
    # ``lift``: ``lift`` is clamped to ``LIFT_MAX = 6`` in silence, with
    # nothing in the fidelity table to say it happened, and a stair that
    # overshoots is the level above opening by dropping back onto its own
    # terrace -- the owner's "it puts a ladder there and then jumps back
    # down to a lower part".
    #
    # **``exit="bubble"`` in the header is a reserve declaration and not
    # a description of this list.** ``handplan._feat_ascent`` takes the
    # ``exit_beats`` branch before it ever looks at the kind, so nothing
    # bubbles anywhere; what the kind does is ``Course._level_budget``,
    # which hands any non-stair exit back ``(need - 2) * 3.2`` metres of
    # terrace it would otherwise have reserved for a seven-tread
    # staircase this level does not build. Measured over 24 runs on the
    # design as it stood, that one word and nothing else: designed
    # content **37% -> 42%**, plain hop
    # 90% -> 88%, exit landings 306 -> 270 and unchecked emergency
    # placements **1 -> 0**. The fallback still costs seven, so this is
    # under-reserved by about two treads on purpose; if a neighbour's
    # rewrite ever pushes the climb into the chasm the symptoms are
    # unchecked placements above zero or ``ascent`` landings climbing
    # past seven, and the fix is ``exit="stair"`` and the loss.
    #
    # **A stair and deliberately not a ladder.** The measurement is not
    # close: an ``ascent/climb`` ride reads 20.9% of its frames with the
    # lens jammed against 0.0% for every other move in the same level,
    # because the wall a ladder hangs on *is* the wall in the lens and
    # ``hug`` on a climb node is inert. Same level, same seeds, a
    # five-tread stair read 1.0% against the ladder's 5.4% for identical
    # designed content. This level's idea is the court and the arch at
    # the end of it; the way out is a quiet flight of steps through it,
    # and it is the one place in the tower where a staircase is the
    # subject rather than the leftover.
    #
    # The foot stands at ``hug=2.8`` and not 2.4: measured elsewhere at
    # 69 wall-jammed frames of 1,293 with the launch landing tucked in
    # against 0 of 1,280 with it moved out, and it is the *launch* that
    # matters -- ``hug`` on the treads above it barely moves the frame.
    # The last tread is thrown out to 3.0 for the same reason the other
    # way round: the camera locks onto the landing through take-off and
    # flight, so a lip tucked against the core aims the last second of
    # the level at a cliff face.
    n("glow", arc=3.2, lift=2, hug=2.8, spread=1, confine=True, deco="lamp",
      ceiling=3, orbs=1),
    n("ground", arc=2.9, step_y=1, hug=2.6, spread=0, confine=True,
      radial=0.9),
    n("accent", arc=3.0, step_y=1, hug=2.6, spread=0, confine=True,
      ceiling=3, radial=-0.9, orbs=1),
    n("rock", arc=2.9, step_y=1, hug=2.8, spread=0, confine=True,
      radial=0.9),
    n("ground", arc=3.0, step_y=1, hug=3.0, spread=0, deco="lamp", orbs=1),
])
