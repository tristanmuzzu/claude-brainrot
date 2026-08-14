"""Level 18: BLUE RUN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A cut ice-run: a flume sawn down the terrace in blue ice, flooded
# black at the bottom of it, and staged over with spruce cribbing. This
# is the *worked* ice level -- a thing built and used -- against GLACIER
# SHELF nine levels below, which is the natural one: a crevasse you fall
# into, seracs, meltwater, a moulin. Nothing here is a glacier. The route
# never touches the flume floor except once, on purpose, falling.
#
# One sentence: *you run the staging over the run, take one flat slide
# no body could jump, drop into the sump and are thrown straight back
# out of it.*
#
# The route. A sea lantern set flush in the ice at the head of the run,
# and a walked step in under the first ice beam -- a two-metre pinch
# with rock either side, which is the groove the reference is in 71% of
# the time. Then the staging: up onto the boards over the meltwater and
# **the long slide**, 5.4 m of arc across the cut at ten metres a second.
# That is the jump this level exists for and it is written where it will
# certainly be laid, second node of the second beat: a hop reaches 4.26 m
# stand-point to stand-point and this is 4.72, so it is a distance only
# the ice has. Up onto the ice beam over it, and then off the end of the
# staging -- two blocks down and 4.52 m out into the flooded run, onto
# the outrun's timber kicker, which throws you two blocks back up onto
# the boards. Then the sump: down to the run's own floor between its
# banks, and the ice back out of it.
#
# **The thing that is different about this level's palette is that it is
# not white.** GLACIER SHELF is snow at 21% under a pale sky, and the
# contact sheet of the version this replaces was the same: pale blue
# cubes, grey cliff, pale sky, one value from the top of the frame to
# the bottom. Here the ground is blue ice with dark worked grit under it
# -- spruce, deepslate, gravel, andesite -- twelve materials with nothing
# over 19%, and **every plinth and every lid in the level is spruce or
# blue ice by name** (``pedestal_style``). That last is the composition
# rule doing real work: ``Course.write`` paints a ``ceiling=`` lid and a
# pedestal stack with ``pedestal_style or theme.rock``, so naming it puts
# a dark timber brow across the top of the frame and a dark timber column
# under the eye, where the old version had a four-block face of flat blue
# ice filling half of every shot.
#
# Six things here are answers to a measurement rather than to taste.
#
# **The seven-tread ice staircase is gone.** It was the way out and it
# was thirty-three of the level's landings over eight runs -- more than a
# fifth of everything a viewer sees, all of it the same slide. Four
# landings replace it, and ``exit="ladder"`` is the other half: it is a
# *reserve declaration* rather than the way out, because
# ``handplan._level_budget`` gives any non-stair exit back
# ``(need - 2) * 3.2`` blocks of terrace, which is the design's.
#
# **``gap=2.8`` is arithmetic, not a taste in chasms.** The crossing is a
# fixed ``gap + 1.4`` of arc from wherever the treads finished. The launch
# board is an absolute ``lift=2`` and can only be placed at 1, 2 or 3 (the
# ballistic clamp forbids +2 from the lift 1 machinery leaves the body
# at), so with three ``step_y`` treads the last tread stands 4, 5 or 6
# above this level's floor against a next floor 4 up -- level, down one,
# down two. At 2.8 the crossing's reach is about 3.5, which is legal at
# all three; at 2.2 the two-block case is refused and the whole authored
# exit is discarded with it.
#
# **``breaks=0``, so there is no lock.** Any break at all forces one -- a
# level's first floor break is always 5.5-6.7 m wide -- and it is three
# or four landings on a level that only lays a dozen. The walk number is
# held down instead by three ponds and by the fact that **69% of this
# level's landings float** with nothing under them: measured, a no-jump
# walker covers 30% of it and 0 of 8 walks get down it, against 42% and
# the roster's 55% ceiling.
#
# **The kicker is spruce and not slime.** ``SPRINGY`` is imported by
# ``spiralplan`` and never read, so a bounce is entirely ``kind="bounce"``
# against the previous landing's impact and the pad's *material* is a
# colour. A green slime cube was the single brightest thing in the old
# sheet of a level that is otherwise blue and grey, and it read as a
# fault. A timber board at the foot of a flume does not.
#
# **``band=9.0`` is what decides whether this level's arch is ever
# seen, and that was not guessable.** The design was built at 7.5 -- a
# gallery, and better on every other row: 42% empty frame against 46,
# 26% walker coverage against 30, two points more designed content. And
# its structure held at 25 degrees for **0.0 seconds on four seeds out
# of four**, where the version this replaces held it for 0.7 to 1.3.
# The gate machinery was innocent: over twelve runs both read *exactly*
# 6 reservations of 14 visits, 6 offers, 4 entered. What differs is
# **occlusion**, and the reason is that a level's structure is framed
# from the *approach* -- from the level below, across the chasm -- so
# what hides it is this level's own terrain rather than anything on its
# course. Instrumenting ``landmark_probe.look``'s refusals frame by
# frame over four seeds: 148 frames clear at 7.5, 249 at 9.0, 278 at
# 10.5, against 433 / 318 / 329 occluded. At 9.0 two of four seeds hold
# it for 1.97 and 1.38 s, which is parity with what this level had.
# Nothing on the course moved that number at all -- lids, the threshold
# shell and every ``hug`` in the level raised by 0.6 each produced a
# world identical to the frame, which is RULES 7's "lids and shells are
# near-noise on a narrow ledge" showing up as an exact tie.
#
# **The fall is written at ``arc=5.2`` and that is the bounce's
# arithmetic.** ``_node`` offers ``arc * 0.84`` as a fallback and a
# two-block throw wants an arrival at 11.0 m/s: a two-block drop across
# 5.2 arrives well over it and across the 4.37 fallback still at 11.1.
# Written at 4.9 the fallback arrives at 10.9, the bounce is silently
# refused, and the beat still reads as placed.
LEVEL = Level("BLUE RUN", "ice", rise=4, gap=2.8, exit="ladder",
              band=9.0, profile="ledge", shelf=5.0, breaks=0,
              landmark="arch",
              ground="blueice", sub="spruce", rock="packedice",
              accent="calcite", glow="sealantern", liquid="water",
              props=("pebbles", "mcfence", "lanternpost", "chain"),
              # Twelve materials, dominant share 19%, which is the shape
              # a real terrace measures as (a median 14 kinds, dominant
              # 26%). Roughly half the weight is the ice family and half
              # is worked grit -- the run is cut and staged, not fallen.
              # The ice theme's own mix runs stone, diorite, andesite and
              # cobble at a third of its weight and paints a grey plate;
              # this one keeps the greys but makes them dark rather than
              # pale, so the floor is the *blue* thing in the lower half
              # of the frame and nothing else in the level is.
              floor=(("packedice", 3), ("spruce", 2), ("frost", 2),
                     ("deepslate", 2), ("gravel", 2), ("calcite", 1),
                     ("snow", 1), ("clay", 1), ("andesite", 1),
                     ("iron", 1), ("stone", 1)),
              candy=("blueice", "packedice"),
              sky=(120, 156, 200), dark=0.30,
              step=("blueice", "slide"), beats=[
    # The threshold, at the head of the run: one sea lantern set flush in
    # the ice on a rise, then a walked step in under the first ice beam
    # onto the timber. The palette changes completely at that block --
    # green-grey wet masonry behind, blue ice ahead -- which is what the
    # reference's seams do, nine of them in two minutes and every one
    # abrupt.
    #
    # It is walked and not jumped because it cannot be jumped: one
    # impulse always rises 1.25 m and the head then sweeps the two cells
    # above every take-off, so a beam low enough to read as a lintel is
    # a beam no arc gets under. ``ceiling=3`` over a ``walk`` is the
    # genre's ``2bc`` -- the lid you sprint under -- and a walk is the
    # one leg this motion model can honestly put one over.
    #
    # Both nodes at ``lift=1``, which is a fidelity lever rather than a
    # preference: a first beat is placed from wherever machinery left the
    # body, and machinery always leaves it at lift 1. The identical beat
    # measures 67% at lift 2 and 100% at lift 1. Everything after this
    # is off the floor.
    ("startgate", [n("glow", arc=3.2, lift=1, hug=2.8, spread=1,
                     ceiling=3, deco="lamp", orbs=1),
                   n("spruce", arc=2.9, lift=1, hug=2.8, kind="walk",
                     spread=0, pedestal_style="spruce", ceiling=3,
                     deco="lintel", shell="cave")]),
    # **The level is this beat**, and it is five nodes in one rather than
    # two beats because of where the terrace runs out: ``_truncate``
    # clips the last feature before the exit reserve and eats the longest
    # arc in it first, which is always the thing the level is about.
    # Beats one and two are the reliable ones on this engine.
    #
    # Five landings, and each asks something different:
    #
    # * **onto the staging** -- a +1 hop at arc 3.2, a reach of 2.52
    #   against a window that stops at 3.10. Centred and not at the top
    #   of it: 3.6 is a reach of 2.92 and is the arc that has to fall
    #   back, and a fallback is not exact. The pond it digs is the
    #   meltwater standing in the cut, and it is what the boards are over.
    # * **the long slide** -- level, ``arc=5.4``, a reach of 4.72. A
    #   sprint hop stops at 4.26, so **this is a distance a body on foot
    #   cannot cover at all**, and that is the whole point of it: the
    #   level's signature is speed rather than height. It is written
    #   second because a beat lays about half its nodes and what a level
    #   is about has to be in the first two.
    # * **onto the beam** -- the last +1, up to the ice slab left
    #   standing across the run. This is the level's high point and
    #   everything from here is on the way down.
    # * **the fall** -- lift 3 to lift 1, ``arc=5.2``, a reach of 4.52
    #   against a two-block-drop window of 3.12 to 5.56. The only kind of
    #   long jump this motion model has besides the ice: falling takes
    #   time and the body does not slow down while it does. It lands on
    #   the outrun's kicker, floating, in the water it digs.
    # * **the kick** -- lift 1 back to lift 3, two blocks in one move,
    #   which nothing else in this engine does; a ballistic hop has no
    #   solution for +2, here or in vanilla. ``spread=1`` so a feed that
    #   arrived a little slow degrades to a one-block throw instead of
    #   failing, and ``pedestal=False`` on both pad and landing because at
    #   the foot of a fall there is no terrace for a stack to find.
    #
    # The rise and the drop are in the same beat on purpose. Machinery is
    # inserted *between* beats and leaves the body back at lift 1, so a
    # beat that spends a height the last one climbed to drops nothing
    # about half the time -- and a bounce there silently becomes a hop
    # with the beat still reading as placed.
    #
    # The two ponds are 13.8 m apart, which they have to be: the bowl is
    # a radius-three disc dug the moment its landing commits, and a
    # second one inside that radius stands in the hole the first made.
    ("flume", [n("rock", arc=3.2, lift=2, hug=2.6, spread=1, moat=True,
                 pedestal_style="spruce", ceiling=3, orbs=1),
               n("ground", arc=5.4, lift=2, kind="slide", form="ice",
                 hug=3.0, spread=1, pedestal=False,
                 pedestal_style="blueice", ceiling=3, orbs=2),
               n("rock", arc=3.2, lift=3, hug=2.6, spread=1,
                 pedestal_style="spruce", ceiling=3),
               n("spruce", arc=5.2, lift=1, hug=3.0, spread=1,
                 form="slime", pedestal=False, moat=True, orbs=2),
               n("ground", arc=3.4, lift=3, hug=2.6, kind="bounce",
                 spread=1, pedestal=False, pedestal_style="spruce",
                 orbs=3)]),
    # The sump: down between the run's own banks to the flooded floor of
    # it, and the ice back out. Two landings and both of them are the
    # descent this level owes -- the real map's legs travel eleven blocks
    # vertically to gain four, and every level in this tower used to be a
    # monotonic climb.
    #
    # The drop is a −2 at ``arc=4.4``, a reach of 3.72 against a window
    # of 3.12 to 5.56, and it is the one place the route touches the
    # bottom of the run. The way out of it is a +1 **slide**, a reach of
    # 2.92 against an ice window of 2.67 to 4.36 -- a hop would do it
    # too, and the ice is what the bank is made of.
    ("sump", [n("rock", arc=4.4, lift=1, hug=2.6, spread=1, moat=True,
                pedestal_style="spruce", ceiling=3, orbs=1),
              n("ground", arc=3.6, lift=2, kind="slide", form="ice",
                hug=3.0, spread=1, pedestal=False,
                pedestal_style="blueice", ceiling=3, orbs=1)]),
], filler=[
    # The staging itself, and on a terrace this long it is a third of
    # what is seen: the script is nine landings and a visit lays a dozen,
    # so this loop is the level's voice rather than its surprise. Three
    # boards over the run, none of them standing on anything, weaving in
    # and out across the corridor on their ``hug`` -- a blue-ice cap two
    # and a half metres off the cliff, a long flat slide out to a board
    # near the rim, and a timber plank a block down.
    #
    # The loop's seam is where half a filler's fidelity is usually lost,
    # so it is written rather than hoped for: the plank at lift 2 back up
    # to the cap at lift 3 is a +1 slide across 3.6 of arc, a reach of
    # 2.92 against 2.67 to 4.36.
    #
    # No ``moat`` anywhere in here, and that is not taste. The filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals stand on -- one keyword in a filler once produced 27,859
    # "pedestal will not stand" refusals. This level's water is the three
    # ponds in the script.
    ("staging", [n("ground", arc=3.6, lift=3, kind="slide", form="ice",
                   hug=2.6, spread=1, pedestal=False,
                   pedestal_style="blueice", ceiling=3, orbs=1),
                 n("rock", arc=4.8, lift=3, kind="slide", form="ice",
                   hug=3.4, spread=0, pedestal=False,
                   pedestal_style="spruce", orbs=2),
                 n("spruce", arc=3.6, lift=2, hug=3.0, spread=0,
                   pedestal=False, pedestal_style="spruce", ceiling=3)]),
], exit_beats=[
    # The way out is the run's headwall: a timber launch board on the
    # staging, then three treads cut into the bank and taken on **slides**
    # -- a slide gains its block across 4.36 m where a hop stops at 3.10,
    # so the way out of the ice level climbs like a ramp rather than a
    # stair, and it is three treads rather than seven.
    #
    # **The launch board stands at ``hug=2.8`` and that one number is the
    # level's jammed lens.** Measured elsewhere on this tower: 69 frames
    # of flat wall in 1,293 with the launch landing at 2.2, and 0 of
    # 1,280 at 2.8. ``hug`` on the treads themselves is nearly inert; only
    # the block the climb launches from decides whether the approach to it
    # is a wall at arm's length.
    #
    # **The launch board is an absolute ``lift`` and the three after it
    # are ``step_y``**, and the split is what makes four landings enough.
    # A ``lift`` is measured from this level's own floor and pins the
    # height whatever the filler left the body at; from there the treads
    # must be ``step_y``, because "the floor" means one thing on this side
    # of the chasm and four blocks something else on the other.
    #
    # ``arc=3.6`` is a reach of 2.92, and both of the longer fallbacks a
    # ``step_y`` node is offered -- 1.14 and 1.28 -- are 3.42 and 3.93,
    # still inside the +1 ice window that stops at 4.36. A hop tread at
    # this arc would be legal too; a *slide* tread shorter than 3.35 would
    # not, because an ice jump has a floor of 2.67 as well as a ceiling.
    #
    # The first two treads carry a lid and the last does not, and that is
    # the one place in the level where the sky is wanted: the exit climb
    # is the emptiest third of every level in this tower, but it is also
    # the only place the run needs to see where it is going, and a roofed
    # leap into a hole reads as a wall.
    n("spruce", arc=3.2, lift=2, hug=2.8, spread=1,
      pedestal_style="spruce", ceiling=3, orbs=1),
    n("ground", arc=3.6, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, pedestal_style="spruce", ceiling=3),
    n("ground", arc=3.6, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, pedestal_style="spruce", ceiling=3, orbs=1),
    n("rock", arc=3.6, step_y=1, kind="slide", form="ice", hug=2.6,
      spread=0, pedestal_style="spruce", deco="lamp", orbs=2),
])
