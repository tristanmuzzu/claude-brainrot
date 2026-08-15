"""Level 29: THE CORNICE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE CORNICE. The crest of the tower's snowfield, where the wind has
# built a wave of slab out over the drop -- and it has broken.
#
# What is left is three things, and the level is the three of them in
# order. The **crown wall**: the clean torn face where the slab pulled
# away, standing three or four blocks proud of the field and running the
# whole length of the level. The **crown crack** behind it, full of
# standing melt, with the pieces that settled back rather than falling
# sitting in it as islands. And out past the crown, the **lip** itself,
# what is left of the cornice, hanging on nothing over four hundred
# metres of air.
#
# One sentence: *you come in under the brow, climb the torn face, drop
# three blocks into the crack onto a slab that has come loose, get back
# out of it, take the long glaze slide along the crest, and then go out
# onto the hanging lip and fall off the end of it into the crack again.*
#
# The one thing a viewer would remember is the avalanche bell -- a dark
# frame standing on the crest exactly where the snow tore, run between
# its two posts with the drop underneath -- and after it, the two-block
# fall off the lip with nothing under either end of it.
#
# ---------------------------------------------------------------------
# **How the plaza earns itself, and it is a fifth answer.** Level 3 put
# its route on the roofs *above* a street you could still walk. Level 10
# stood you on the hives standing in a meadow you could still walk.
# Level 16 made the floor lethal and bolted the route to the wall over
# it. Level 24 took the floor away altogether and ran the route over the
# flood on the tops of the bookcases. All four get off the ground and
# stay off it.
#
# **This one lands on the ground twice, on purpose, and the ground is an
# island both times.** ``form="floor"`` with ``moat=True`` is the whole
# device: ``Course._moat`` digs a radius-three disc of the terrace out
# from under the landing and fills it with the melt, and the only thing
# it may not touch is the landing's own reserved ``ground`` -- so what is
# left standing in the pond is exactly the slab the body came down on. A
# no-jump walker that reaches one drops into the bowl and cannot step
# back out (``docs/RULES.md`` §7: the *hole* is the barrier, not the
# liquid; 65.8% -> 25.8% on identical worlds). So this level is on the
# terrace's own snow more often than any other plaza level in the tower,
# and the terrace never once takes it anywhere. Three breaks and seven
# floating landings do the rest.
#
# That device is also the reference's own, which the other four are not:
# read frame by frame the real map does not break its wide ground into
# five-block chasms, it makes *the whole width hazard with isolated
# single blocks standing in it* (``docs/RULES.md`` §3).
#
# ---------------------------------------------------------------------
# What was here before stated a good premise and measured badly on the
# only thing that decides. It was an avalanche gallery: a timber deck,
# spruce for every role that builds anything, and a ``ceiling`` beam on
# **every single landing** of the level. Four things came out of the
# contact sheet, and three of them are one mistake:
#
# * **A lid within eight blocks of the head makes the whole frame an
#   interior.** ``spiral._indoor_want`` returns ``max(theme.dark, 0.85)``
#   the moment any cell three to eight above the body is solid, and that
#   takes 27% off every tint in the shot. Lidding all eighteen landings
#   *plus* nine ``shell="tunnel"`` bays meant the level was lit as a cave
#   from end to end -- so a white level came out grey-brown. It is a
#   third of the landings now, and two shells, which is the reference's
#   own figure (a roof within six blocks on 25% of samples) rather than
#   an attempt to win the empty-frame number outright.
# * **Everything built was ``rock``, and ``rock`` was ``spruce``.** The
#   pedestal stacks, the lids, the shell walls and the bell frame all
#   take ``theme.rock``, so a level that builds a lot in spruce is a
#   level of dark brown columns whatever its floor is made of -- and the
#   old sheet is a lumber yard with some pale blue in the gaps. ``rock``
#   is ``deepslate`` now: the ridge's own dark banded stone, blown clear
#   of snow. Cold, and the darkest thing in the level, which is what the
#   composition rule wants above the eye and under the foot.
# * **The sky was the theme's own 222/230/242**, which against snow is
#   one value from the top of the frame to the bottom -- the owner's
#   "white cubes on a pale wash" is as much the sky as the ground. A
#   ridge crest at altitude has a deep sky and it is free contrast:
#   146/176/214.
# * **The way out was seven treads and 38% of the level.** Six now, and
#   ``exit="ladder"`` is a *reserve declaration* rather than a
#   description of the list below -- see the exit.
#
# Against THE SEA GATE below (prismarine, a six-block ledge on band 12,
# drowned causeway, blue-green) and WART FIELDS above (crimson nylium,
# lava, a fungus canopy) this is white ground under a deep blue sky with
# black rock through it: a different hue from either, a wider floor than
# either, and the only one of the three you fall three blocks in.
#
# And against the tower's other two cold levels: GLACIER SHELF (9) is the
# natural one, a crevasse you fall into with seracs and a moulin, and
# BLUE RUN (18) is the worked one, a flume sawn in blue ice and staged
# over with timber. Neither is white -- 9 is glacier blue and 18 is blue
# ice on dark grit. This is the one that is actually **snow**: a wind
# crest, dry and bright, with no ice run in it and nothing built on it
# but a bell frame.
LEVEL = Level("THE CORNICE", "snow", rise=6, gap=3.0, exit="ladder",
              band=10.5, profile="plaza", breaks=3,
              landmark="bell",
              # Six roles set. The floor is the palest thing in the level
              # and everything standing on it is the darkest, which is
              # how every reference frame is built; ``accent`` is the
              # rimed slab of the torn face, ``glow`` the marker lanterns
              # and ``liquid`` the melt standing in the crack.
              ground="snow", sub="packedice", rock="deepslate",
              accent="frost", glow="lantern", liquid="water",
              props=("chain", "mcfence", "lanternpost", "pebbles"),
              # A crest sky, not the theme's own pale wash. And a little
              # darkness so the two lanterns and the underside of the
              # brow read at all -- but only a little: this is the one
              # level in the tower whose subject is brightness.
              sky=(146, 176, 214), dark=0.15,
              step=("frost", "hop"),
              # Twelve materials with the dominant one at 22%, which is
              # the shape a real terrace measures as (median 14 kinds,
              # dominant 26%). Snow over a wind-scoured tail: rimed slab,
              # packed ice where it has been walked, and the ridge's own
              # black rock showing through wherever the wind has stripped
              # it. The snow theme's own mix has *no snow in it at all*
              # -- packedice, frost, spruce, stone, gravel -- which is
              # most of why this level has never looked like snow.
              floor=(("snow", 5), ("frost", 3), ("packedice", 2),
                     ("calcite", 2), ("deepslate", 2), ("stone", 2),
                     ("gravel", 2), ("diorite", 1), ("andesite", 1),
                     ("cobble", 1), ("coarse", 1), ("blueice", 1)),
              beats=[
    # THE CROWN -- the threshold, the torn face, and the first slab in
    # the crack. Six nodes in one beat, and the reason is
    # ``docs/RULES.md`` §7: machinery is inserted *between* script beats
    # and hands the body back at lift 1, so a rise written in one beat
    # and spent in the next is a rise that mostly does not happen. This
    # level's whole idea is a three-block fall, and the only way to be
    # sure of having three blocks under the feet is to have climbed them
    # three nodes earlier in the same list. It is also the one beat that
    # is never truncated: it opens the level, so it never competes with
    # anything for terrace.
    #
    # 1. A lantern set flush in the snow on the ridge marker, with the
    #    cliff brow three cells over it. The reference's own way of
    #    saying a level begins -- an emissive block on a rise with the
    #    palette changing completely at that block and no blend. Below is
    #    THE SEA GATE, which is prismarine and sea light; from here it is
    #    snow and black rock. ``lift=1`` and not 2: the identical beat
    #    measures 67% at lift 2 and 100% at lift 1, because an opener is
    #    placed from wherever the machinery before it left the body.
    # 2. In under the overhang on foot. A walk is the genre's ``2bc`` --
    #    the lid you sprint under -- and the only honest form of it this
    #    kernel has, because one impulse rises 1.25 m and the head then
    #    sweeps the two cells above every take-off, so a lintel low
    #    enough to read as one refuses any arc beneath it. 2.9 of arc is
    #    2.22 m of ground against a walk's 2.4 limit. Position **two**,
    #    which is where a non-hop verb has to go: a beat lays about half
    #    its nodes and a verb written at the tail is written and never
    #    seen.
    # 3. Up onto the crown wall -- the torn face of the slab, standing
    #    proud of the field. +1 at ``arc`` 3.2 is a reach of 2.52 against
    #    a +1 window of 2.00-3.10, centred rather than at the top of it,
    #    because a +1 written at 3.6 is a reach of 2.92 and is the arc
    #    that has to fall back.
    # 4. And up again, on the glaze along the top of it. A ``slide``
    #    gaining a block reaches 2.67-4.36 where a hop reaches 3.10, so
    #    this is a longer, faster step for the same block of rise -- the
    #    difference between two identical hops in a row, which is one
    #    idea, and two different questions.
    # 5. **Off the crown and three blocks down into the crack.** The
    #    level's descent, in its first third, which is where the
    #    reference puts one -- and it is a *fall off an edge* rather than
    #    a jump down, which is how the real map spends eleven blocks of
    #    travel to gain four. 5.0 of arc from an ice take-off onto the
    #    terrace's own ground is a reach of 4.26 against a -3 window of
    #    3.72-6.05, and it stays legal at -2 (3.12-5.56) and at -4
    #    (4.22-6.48), so it does not care which height the two treads
    #    before it actually reached.
    #
    #    **This is the level's device.** ``form="floor"`` puts the body
    #    on the terrace itself and ``moat=True`` digs the terrace out
    #    from round it: what is left standing in the melt is the slab
    #    that came loose, and a walker that reaches it is in a bowl it
    #    cannot climb.
    # 6. Back out of the crack onto the far lip. It floats, and it has
    #    to: the moat one node back has just dug a bowl of radius three
    #    and a pedestal cannot stand in a hole -- that one keyword is
    #    27,859 "pedestal will not stand" refusals elsewhere in this
    #    roster.
    ("crown", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                 ceiling=5, orbs=1),
               n("deepslate", arc=3.2, step_y=1, hug=3.0,
                 ceiling=5),
               n("frost", arc=2.9, step_y=0, hug=3.0, kind="walk", orbs=1),
               n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
                 hug=3.2, orbs=1),
               n("ground", arc=4.2, lift=2, hug=3.4,
                 spread=0, moat=True, orbs=2),
               n("frost", arc=3.2, step_y=1, hug=3.2, pedestal=False,
                 orbs=1)]),
    # THE GLAZE AND THE LIP -- the wind-polished crest, the level's long
    # jump, and the fall off the end of the cornice.
    #
    # **The lip used to be a beat of its own and that was measured and
    # wrong.** Beats are laid whole or not at all, in order, and what
    # decides how many play is the terrace budget: over eight runs this
    # level asked ``crown`` 5.7 times, ``glaze`` 4.3, a third beat
    # **2.0** and the filler 1.0. So a showpiece written into the third
    # beat is a showpiece the viewer sees on fewer than a third of
    # visits, which is the brief's own landmine restated in this level's
    # numbers. The fall off the lip is in here now, as the tail of the
    # beat that plays second, and what is left in the third beat is the
    # quieter half.
    #
    # It opens at ``lift=2`` with ``spread=1``. Following the beat above
    # that is free; following machinery it costs a fallback, which the
    # spread covers -- and everything after the opener is on ``step_y``,
    # so a beat that started a block low still has the shape it was
    # written with.
    #
    # 1. Up onto the crest itself.
    # 2. **The long slide**, and it is the second node for the same
    #    reason the walk was above: it is the thing this beat is about
    #    and a beat's tail is almost never laid. 5.2 of arc between two
    #    ice blocks is a reach of **4.52 m level, where a hop tops out at
    #    4.26** -- so it is not a long jump, it is a distance no jump in
    #    this engine has, and it is the only gap in the level a body
    #    could not have crossed on foot and hop alone. Ice is a
    #    speciality and not a staple (three levels of forty-three on the
    #    real map); this level gets three ice blocks in its body and two
    #    treads in its exit, which is a wind crest rather than an ice
    #    level.
    # 3. Out onto the hanging lip on foot, under the brow, and the second
    #    of the level's two walks. ``hug`` steps out to 3.4 here and 3.6
    #    and 3.8 after it, so the last three landings of the beat are the
    #    furthest out over the drop the level ever goes.
    # 4. Up onto the last block of the lip still standing, with the melt
    #    cut out from under the jump.
    # 5. **Off the end of it, two blocks down.** A reach of 4.12 against
    #    a -2 window of 3.12-5.56, and the jump the level exists for: a
    #    descent is the only long jump this motion model has, because
    #    falling takes time and the body does not slow down while it
    #    does. Both ends float, so it is a fall from nothing to nothing.
    #    Written on ``step_y`` rather than on ``lift`` so it is two
    #    blocks below *the lip the body actually reached*.
    #
    # The ``shell="cave"`` is on the beat's **last** node, which is the
    # only place a shell may go -- it is painted the moment its landing
    # commits and its roof then refuses the next arc of the same beat.
    # Off a floating landing it grows a roof and open sides (``_shell``
    # skips a wall column with nothing under it), which is exactly what
    # is wanted: what this tower's sheets are short of is not walls but
    # the dark brow across the top of the frame that the reference has in
    # 73% of its shots.
    ("glaze", [n("frost", arc=3.4, lift=4, hug=3.2, spread=1, ceiling=5,
                 orbs=1),
               n("blueice", arc=5.2, step_y=0, kind="slide", form="ice",
                 hug=3.2, pedestal=False, orbs=2),
               n("deepslate", arc=2.9, step_y=0, hug=3.4, kind="walk",
                 ceiling=5),
               n("frost", arc=3.2, step_y=1, hug=3.6, pedestal=False,
                 moat=True, orbs=1),
               n("snow", arc=4.8, lift=3, step_y=-2, hug=3.8, pedestal=False,
                 shell="cave", orbs=2)]),
    # THE SECOND CRACK -- the quiet beat, and the level's device said a
    # second time in three landings rather than six.
    #
    # Three nodes and not four, because this is the beat that plays about
    # twice in eight runs: whatever it is about has to be at its head,
    # and a short beat is a beat that fits. Up onto a canted slab, down
    # two blocks onto the second loose block in the crack with the melt
    # dug out round it, and out of the hole on the ice that has formed at
    # its edge -- which is a ``slide`` rather than a hop because the exit
    # staircase and this level's two crack landings are the only places
    # a non-hop verb can live at all, and the hop share is a rule.
    ("crack", [n("frost", arc=3.4, lift=4, hug=3.4, spread=1, ceiling=5,
                 orbs=1),
               n("ground", arc=4.4, lift=2, hug=3.6,
                 spread=0, moat=True, orbs=2),
               n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
                 hug=3.4, pedestal=False, orbs=1)]),
], filler=[
    # THE SLAB FIELD. The filler repeats and a script's tail does not, so
    # the level's character lives here, and this level's character is the
    # broken crest: a canted slab, a stride across it under the brow, and
    # off the far end of it onto the glaze a block below.
    #
    # It neither climbs nor sinks across a lap -- +1, level, -1 -- and
    # that matters for a reason that is not obvious: the exit column is
    # sized by what the body still has to climb when it starts, so a
    # filler that drifted downhill would buy the level a longer staircase
    # every time it played.
    #
    # The seam where the loop closes is a jump like any other and half of
    # what a filler ever loses is there: it is +1 off the ice back onto a
    # slab end, a reach of 2.55 against a window opening at 2.00.
    #
    # **No ``moat`` anywhere in here.** The filler loops, and the second
    # lap digs away the ground the first lap's pedestals are standing on.
    # This level's three ponds are all in beats that play once.
    ("slabs", [n("frost", arc=3.2, lift=3, hug=3.0, spread=1, ceiling=5,
                 orbs=1),
               n("deepslate", arc=2.9, step_y=0, hug=3.0, kind="walk",
                 ceiling=5),
               n("packedice", arc=4.4, lift=3, step_y=0, kind="slide", form="ice",
                 hug=3.4, pedestal=False, orbs=1)]),
], exit_beats=[
    # THE FRACTURE STAIR. The crown wall steps as it tears, and the way
    # off this level is up those steps to the ridge -- a chimney cut into
    # the torn face, lit at the foot and the head, with a beam over every
    # tread and one roofed pinch in the middle of it.
    #
    # **A stair and deliberately not a climb.** The brief's measurement
    # is unambiguous -- an ``ascent/climb`` ride measured 20.9% jammed
    # against 0.0% for every other move in that level, because the wall a
    # ladder hangs on *is* the wall in the lens and ``hug`` on a climb
    # node is inert -- and ``docs/RULES.md`` §3 puts a climb exit on
    # about one level in five, for a level whose *idea* is the climb.
    # Seventeen of the twenty rebuilt levels leave by one against the
    # real map's seven of forty-three. This level's idea is the crest.
    #
    # **``exit="ladder"`` in the header is a reserve declaration and not
    # a description of this list.** ``handplan._feat_ascent`` takes the
    # ``exit_beats`` branch before it ever looks at the kind, so no
    # ladder is built anywhere; what the kind does is
    # ``_level_budget``, which gives any non-stair exit back
    # ``(need - 2) * 3.2`` metres of terrace -- sixteen metres on a
    # six-block level, which on a level whose design was 36% of its own
    # landings is the single biggest lever there is. The exit is
    # therefore under-reserved by about two treads, deliberately. If a
    # neighbour's rewrite ever pushes it into the chasm -- the symptoms
    # are unchecked placements above zero, or ``ascent`` landings
    # climbing past seven -- set ``exit="stair"`` and take the loss.
    #
    # **Six treads and not seven**, and the difference is one line: the
    # foot is an absolute ``lift=2`` rather than a ``step_y``, so it
    # re-bases off whatever height the machinery before it left the body
    # at instead of adding to it. Five ``step_y`` treads then finish at
    # lift 7 -- a walking surface of 8 against the next terrace's 7,
    # which is this level's ``rise`` of 6 plus the one block the crossing
    # comes down. The old seven-tread version started on ``step_y`` too
    # and finished a block higher than that; a stair that overshoots is a
    # level above that opens by dropping back onto its own terrace, which
    # is the owner's "it puts a ladder there and then jumps back down to
    # a lower part".
    #
    # Two of the treads are glaze and taken as slides. The exit is a
    # third of every run and can otherwise only ever be hops, and a slide
    # gaining a block reaches 2.67-4.36 against a hop's 2.00-3.10, so an
    # icy tread is written a little longer than a stone one.
    #
    # Every tread carries a lid, which is the opposite of the rule in the
    # body of the level and is right for the same reason: the exit is the
    # emptiest third of any level in this tower -- a staircase with sky
    # on five sides of it -- and here being read as an interior is the
    # point. ``shell="cave"`` on the **launch** landing is
    # ``docs/RULES.md`` §7's largest single frame win, worth about four
    # points on its own, and it takes its chimney out of the climb's
    # already-reserved cells for free.
    #
    # The last tread is a lit lip thrown **out** at ``hug=3.2`` rather
    # than tucked in at 2.4, because the camera locks onto the landing
    # through take-off and flight: a lip against the core aims the last
    # second of the level at the cliff.
    n("glow", arc=3.0, step_y=0, hug=2.8, spread=1, deco="lamp", ceiling=3,
      shell="cave", orbs=1),
    n("frost", arc=3.0, step_y=1, hug=2.6, spread=0, confine=True,
      ceiling=3),
    n("packedice", arc=3.6, step_y=0, kind="slide", form="ice", hug=2.6,
      spread=0, confine=True, ceiling=3, orbs=1),
    n("deepslate", arc=3.0, step_y=1, hug=2.6, spread=0, confine=True,
      ceiling=3, shell="tunnel"),
    n("packedice", arc=3.6, step_y=1, kind="slide", form="ice", hug=2.8,
      spread=0, confine=True, ceiling=3, orbs=1),
    n("glow", arc=3.0, step_y=1, hug=3.2, spread=0, pedestal=False,
      ceiling=3, deco="lamp", orbs=2),
])
