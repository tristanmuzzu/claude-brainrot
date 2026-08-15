"""Level 16: THE VAULT.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE VAULT. A strongroom cut into the cliff, and its floor is the melt:
# lava tapped in under the paving so that nothing can be carried out
# across it. The bullion was never on that floor. It stands clear of it
# on the strongroom's own **racking** -- an iron shelf, a course of
# bars, a lit top tier -- cantilevered further out over the lava the
# higher it goes, and that racking is the route.
#
# You come in over a glowstone sill and through the vault door on foot
# under its lintel; climb the rack four blocks up, walking one shelf and
# jumping the next; and then **fall three blocks off the top of it, out
# into the middle of the room, onto a magma pad standing in the melt** --
# the level's showpiece and its long jump, because a descent is the only
# long jump this motion model has. **The pad throws you two blocks
# straight back up** onto a stack of bullion, which is a thing no jump
# in this engine can do. After that it is the ledger room and then piers
# over the lava for as long as the terrace lasts, and out up a flight of
# gold treads in the corner.
#
# The one thing a viewer would remember is that fall: off the top of the
# racking, past the lit gold gate, down into a room whose whole floor is
# glowing, and straight back up off it.
#
# ---------------------------------------------------------------------
# **How the plaza earns itself, and it is neither level 3's answer nor
# level 10's.** Level 3 put its route on the roofs *above* its street;
# level 10 made everything you stand on a hive. Here the floor is not
# something the route declines to use -- it *is* the hazard, and the
# level is the shelving bolted to the wall over it. Half the landings
# have nothing under them at all, four floor breaks are cut through the
# paving, and both moats are wide enough to see across: a no-jump walker
# gets 50% of the way and 0 runs of 8 reach the end.
#
# One honest note against that premise, because it is the kind of thing
# that reads as design and is not: **the lava does nothing for the walk
# number.** Lava is solid, so a walker strolls across the top of a moat;
# what actually stops one is the pit a moat digs, and only a see-through
# liquid leaves a pit. The moats here are atmosphere, and the breaks and
# the floating landings are the barrier.
#
# ---------------------------------------------------------------------
# What was here before was this same premise stated and not delivered.
# Its elevation in the blueprint was a **flat line at lift 1** from the
# threshold to the exit -- the owner's "half the jumps are at ground
# level" drawn as a picture -- with three beats of near-identical
# 2.85-3.2 m hops laid along it, and a generated exit staircase that was
# thirty of its eighty-four machinery landings. Four things changed, and
# each is a measurement rather than a preference; they are written out
# at the beats they belong to. The shape of it:
#
# * the level climbs *inside its first beat*, and that beat carries the
#   showpiece too, because it is the only stretch of this level that is
#   laid whole on every single visit;
# * the way out is written down, and it is a **stair and not a ladder**
#   -- the ladder was built and measured, and a fifth of its ride was a
#   flat wall at arm's length;
# * three beats became two and a filler;
# * the floor palette is written out, because the theme's own is five
#   kinds of pale grey and painted this level as a car park.
#
# Measured over 24 unpinned runs after all four: designed content 59% of
# the level, 97% of it placed exactly as authored, no beat under 94%,
# hop share 81%, and **0 jammed frames of 550** against the 85 of 619 it
# started at.
LEVEL = Level("THE VAULT", "gold", rise=5, gap=2.4, exit="ladder",
              band=8.5, profile="plaza", breaks=4,
              landmark="hoard",
              # Warm-dark and committed: raw gold paving underfoot,
              # blackstone for everything built, bullion for the prize,
              # lava for the light. Dark enough to need lighting, which
              # is what puts a lamp at the far end of every stretch and
              # nothing decorative in between.
              ground="rawgold", sub="deepslate", rock="blackstone",
              accent="gold", glow="glowstone", liquid="lava",
              props=("torch", "chain", "lanternpost", "pebbles"),
              dark=0.62, step=("gold", "hop"),
              # Twelve materials with the dominant one at 17%, which is
              # the shape a real terrace of the reference measures as:
              # one committed hue with a long tail of grit under it. The
              # gold theme's own mix is deepslate, stone, gravel,
              # andesite, cobble and iron -- five kinds of pale grey --
              # and half of the last contact sheet of this level was a
              # grey plate with gold cubes standing on it.
              floor=(("blackstone", 3), ("rawgold", 3), ("gold", 2),
                     ("deepslate", 2), ("goldore", 1), ("copper", 1),
                     ("iron", 1), ("magma", 1), ("obsidian", 1),
                     ("chiselled", 1), ("tuff", 1), ("gravel", 1)),
              # ``breaks=4`` on a full floor, against the default of two
              # and the three this level used to carry. The old note here
              # said a fourth break "took the whole level's placement
              # down with it", and it was right about a design whose
              # landings all wanted ground: a landing that needs a
              # pedestal cannot be laid over a hole. Nearly everything
              # here floats, so the objection is gone -- measured, same
              # pin and same seeds, breaks 3 -> 4 moved the no-jump
              # walker from 49% to 46% with fidelity, exactness, jam and
              # empty frame all unchanged to the decimal.
              beats=[
    # THE DOOR, THE RACKING AND THE MELT -- the whole idea of the level
    # in one beat, and *why* it is one beat is the most useful thing
    # measured on this module.
    #
    # A beat is laid whole or not at all and is truncated from the end,
    # and **machinery is inserted between beats**: the lock across the
    # first floor break and the crossing through the hoard gate both
    # leave the body back at lift 1. So a rise written in one beat and
    # spent in the next is a rise that mostly does not happen, and a
    # showpiece that depends on that rise fails silently while still
    # reading as placed. That is exactly what happened here. With the
    # fall and the bounce written as their own beat the pad was usually
    # fed by a level hop rather than by a three-block drop: **the bounce
    # fired 5 times in 20**, its landing was placed at a fallback height
    # on 9 of 9 tries and never once as authored -- 0% exact -- and that
    # one node dragged its beat to 76% and took the two landings behind
    # it down with it.
    #
    # Moved inside this beat, where the drop off the rack is guaranteed
    # because the rack is four nodes earlier in the same list, the
    # **bounce fires 11 times in 16 and every node of this beat is 100%
    # exact over 24 runs**. The whole level moved with it: designed
    # content 51% -> 59%, exactness 93% -> 97%, hop share 85% -> 81%.
    #
    # An eight-node beat is against the usual advice -- a beat lays
    # about four fifths of its nodes and the tail is where a design goes
    # to die. It is right here because this particular beat measured
    # **149 landings asked and 149 laid** over 24 runs: it opens the
    # level, so it never competes with anything for terrace and it is
    # never truncated. Check that number before adding a ninth node.
    #
    # 1. A glowstone sill flush in the raw-gold paving, lit, with a lid
    #    two cells over it. The reference's own way of saying where a
    #    level begins: an emissive block on a rise, on screen two
    #    seconds before it is reached, with the palette changing
    #    completely at that block and no blend. Below is WOOLWORKS,
    #    which is pink wool and timber; from here it is gold and black.
    # 2. Through the vault door on foot, under its lintel three cells
    #    over the take-off. **A doorway is walked and never jumped**:
    #    one impulse always rises 1.25 m and the head then sweeps the
    #    two cells above every take-off, so an arc under a lid low
    #    enough to read as a door is refused every time. This is the
    #    genre's 2bc -- the lid you sprint under -- and the only honest
    #    form of it this kernel has. It is second in the beat and not
    #    first because a walk needs its predecessor within half a metre
    #    and a beat boundary does not promise that.
    # 3. Up onto the bottom shelf of the racking. +1 at arc 3.2: a reach
    #    of 2.53 against a +1 window of 2.00-3.10, centred rather than
    #    at the top of it, because a +1 written at 3.6 is a reach of
    #    2.92 and is the arc that has to fall back. The first lava cut
    #    is under this jump.
    # 4. Along that shelf on foot, under the next bar. The level's
    #    second walk, at position four, which is where the cheapest verb
    #    this engine has belongs: a flat leg costs the terrace two
    #    metres where a jump costs three, so the beats behind it fit. It
    #    floats because the moat on node 3 has just dug a bowl of radius
    #    three and a pedestal cannot stand in a hole.
    # 5-6. Two more +1 hops, to the course of bars and then to the lit
    #    top tier, four blocks up and the highest ground in the body of
    #    the level. What varies across the rack is not the jump -- all
    #    three are the same 3.2 -- it is the ``hug``: 2.6, 2.8, 3.0, so
    #    the shelving steps *out* over the lava as it climbs and the top
    #    tier stands clear of the wall with the room under it.
    # 7. **Off the top and down into the melt.** ``step_y=-3`` at arc
    #    4.6: a reach of 3.92 against a -3 window of 3.72-6.05, and all
    #    three of the arcs placement may try (4.6, 5.24, 5.89) are
    #    inside it. Written on ``step_y`` rather than on ``lift`` so
    #    that it is three blocks below *the tier the body actually
    #    reached* -- which is what makes the next node possible.
    # 8. **The melt throws you back out.** A slime pad is fed by the
    #    fall onto it and by nothing else: off this drop the arrival is
    #    13.37 m/s and the pad returns 12.83, against the 10.58 that
    #    clearing two blocks needs, so ``step_y=2`` -- the only rise in
    #    this engine that is not a hop -- onto a stack of bullion. Off a
    #    two-block drop it would be 11.22 and still fire; off one block,
    #    8.87, and it silently becomes an ordinary hop with the beat
    #    still reading as placed. The pad is ``magma`` and not slime
    #    because a pad's material is free -- ``SPRINGY`` is imported by
    #    ``spiralplan`` and never read, and the physics is entirely
    #    ``kind="bounce"`` against the previous landing's impact -- and
    #    a green cube in a strongroom is not a place. Both nodes float:
    #    a pad offered only cells with ground under them finds none at
    #    the foot of a fall.
    ("door", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                ceiling=2, orbs=1),
              n("blackstone", arc=3.2, step_y=1, hug=2.8,
                ceiling=3, deco="lintel"),
              n("iron", arc=2.9, step_y=0, hug=2.6, kind="walk", moat=True, orbs=1),
              n("chiselled", arc=2.9, step_y=0, hug=2.8, kind="walk",
                pedestal=False, ceiling=3),
              n("gold", arc=3.2, step_y=1, hug=2.8, pedestal=False),
              n("glow", arc=3.2, step_y=1, hug=3.0, pedestal=False,
                deco="lamp", orbs=2),
              n("magma", arc=4.6, lift=2, step_y=-2, form="slime", hug=3.4,
                pedestal=False, moat=True, orbs=2),
              n("gold", arc=3.6, step_y=2, kind="bounce", hug=2.8,
                spread=1, pedestal=False, orbs=3)]),
    # THE LEDGER ROOM. The quiet beat, and the level's only interior.
    # Four landings: onto a pier, across the ledger plank on foot under
    # a bar, up onto the bullion with the second lava cut under the
    # jump, and then **down one block and 4.4 of arc out** onto the last
    # pier -- a reach of 3.79 against a -1 window of 2.35-4.98, the
    # level's second-longest jump, and the one that hands the filler a
    # body at lift 2 over the lava rather than back on the floor.
    #
    # It opens at ``lift=2`` with ``spread=2``. Following the beat above
    # that is free, and it is the one real lever a level has against
    # "half the jumps are at ground level"; following machinery it costs
    # a fallback, which the spread covers.
    #
    # The second moat is here rather than in the filler and it is for
    # the eye, not for a number: measured, adding it moved empty frame,
    # jam, fidelity and walk coverage by nothing at all. What it does is
    # make the level's own premise true past its first third. The
    # contact sheet before it had a glowing floor for eight frames and
    # then black and grey towers against open sky for the rest.
    #
    # The ``shell="cave"`` is on the beat's **last** node, which is the
    # only place a shell may go: it is painted the moment its landing
    # commits and its roof then refuses the next arc of the same beat.
    # At lift 2 it grows a roof and open sides -- ``_shell`` skips a
    # wall column with nothing under it -- which is what is wanted here,
    # because what this level's sheet is short of is not walls but the
    # dark brow across the top of the frame that the reference has in
    # 73% of its shots.
    ("ledger", [n("blackstone", arc=3.4, lift=3, hug=2.8, spread=2,
                  ceiling=2, orbs=1),
                n("chiselled", arc=2.9, step_y=0, hug=3.0, kind="walk",
                  ceiling=3, deco="lintel"),
                n("gold", arc=3.2, step_y=1, hug=2.6, pedestal=False,
                  moat=True, orbs=1),
                n("blackstone", arc=4.4, lift=2, step_y=-1, hug=3.4,
                  pedestal=False, shell="cave", orbs=2)]),
], filler=[
    # THE PIERS. The filler repeats and a script's tail does not, so the
    # level's character lives here: a blackstone pier standing in the
    # melt, a gold ledger plank walked across to the next one, and a
    # half-height shelf of iron bars.
    #
    # The shelf is ``form="slab"``, written on ``lift`` and deliberately
    # not on ``step_y``: a slab stands half a block down in its own
    # cell, so ``lift 3`` is a walking surface at 3.5 and a *half* step
    # up off the plank. Stairs and slabs are the commonest non-cube form
    # in the reference by a wide margin and this tower barely uses them;
    # a half-height ledge is cheap, reads as deliberate architecture and
    # buys reach -- 3.78 m at +0.5 against 3.10 at +1.
    #
    # The seam where the loop closes is a jump like any other, and half
    # of what a filler ever loses is there: it is -0.5 off the slab
    # across 3.4 of arc, a reach of 2.73 against a window that opens at
    # 2.00.
    #
    # No ``moat`` anywhere in here, and that is not taste. The filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on -- measured elsewhere at 27,859
    # "pedestal will not stand" refusals from one keyword. This level's
    # lava is in the two beats that play once.
    ("piers", [n("blackstone", arc=3.4, lift=2, hug=2.8, spread=2,
                 ceiling=2, orbs=1),
               n("gold", arc=2.9, step_y=0, hug=2.6, kind="walk",
                 ceiling=3),
               n("iron", arc=3.6, lift=3, hug=3.0,
                 pedestal=False, orbs=1)]),
], exit_beats=[
    # THE STRONGROOM STAIR. Five landings written out rather than left
    # to the generated climb, which hangs its ladder column mid-lane
    # with nothing within a cell of its middle index to anchor on, is
    # refused silently, and hands the level a six- or seven-step
    # staircase instead -- thirty of the eighty-four machinery landings
    # this level used to spend, with nothing anywhere reporting it.
    #
    # **It is a stair and not a ladder, and that is this module's
    # largest single measurement.** A ladder was written first and
    # exactly to the recipe -- launch at ``hug=2.8``, ``step_y=4``, its
    # own pedestal to anchor on, no shaft shell, the lip thrown out to
    # 3.8 -- and it worked: ``climb`` appeared in the move mix 16 times
    # and the exit cost three landings instead of five. And a fifth of
    # the ride was a flat blackstone wall at arm's length. Instrumented
    # over four seeds by bucketing every jammed frame by the segment
    # *and the move* that laid it:
    #
    #     ascent/climb    545 frames   114 jammed   20.9%
    #     every other move in the level              0.0%
    #
    # 114 of the level's 135 jammed frames were the ride, and the rays
    # were hitting the column's own pedestal. That is not something to
    # tune around: the wall a ladder hangs on *is* the wall in the lens,
    # and no ``hug`` moves it, because ``hug`` on a climb node is inert.
    # Four arms, same pin, same seeds, swapped on the live ``Level``
    # inside one process with nothing else changed:
    #
    #     ladder, 3 landings             designed 145  jam 5.4%  ride jam 114
    #     6-tread stair, stair budget    designed 137  jam 1.0%  ride jam   0
    #     6-tread stair, ladder budget   designed 146  jam 1.1%  ride jam   4
    #     **5-tread stair, ladder budget designed 145  jam 1.0%  ride jam   0**
    #
    # Unchecked placements were 0 and exactness 100% in all four. RULES
    # 3 says a climb exit belongs on about one level in five and is for
    # a level whose *idea* is the climb; this level's idea is the melt
    # and the racking, and the ladder was spending a fifth of its worst
    # frames to say otherwise.
    #
    # ``exit="ladder"`` in the header is therefore a **budget
    # declaration and not a description of this list**: it reserves
    # three landings' worth of terrace rather than a staircase's seven.
    # The authored exit is five, so it is under-reserved by about five
    # metres of arc -- deliberately, and measured. With the honest stair
    # reserve the beats above lose the terrace they need and the
    # ``piers`` filler never plays at all: 0 landings in 16 runs against
    # 7, and designed content 137 against 145. If a neighbour's rewrite
    # ever pushes this exit into the chasm -- the symptoms are unchecked
    # placements above zero, or ``ascent`` landings climbing past six --
    # set ``exit="stair"`` and take that loss.
    #
    # The shape: the foot of the stair is a lit landing at **lift 2**,
    # which is what makes it five treads and not six; then gold and
    # blackstone treads a block at a time on ``step_y``, so each is a
    # rise from the tread before rather than from a terrace the body may
    # not be standing on; and the last is a lit lip **out at hug 3.6**
    # with nothing under it. The lip is thrown out rather than tucked in
    # at 2.4 because the camera locks onto the landing through take-off
    # and flight: a lip against the core aims the last second of the
    # level at the cliff.
    #
    # Every tread carries a lid. The exit is the emptiest third of any
    # level in this tower -- a staircase with sky on five sides of it --
    # and a ``ceiling`` beam is the cheapest overhead mass a level
    # author has and is legal over a +1 hop, whose apex is 1.25 against
    # a lid at three. Measured here, same pin and same seeds: empty
    # frame 46.7% -> 45.9%, for no change at all in fidelity, exactness,
    # unchecked count or jam. It also darkens the climb, which on a
    # vault is the right direction.
    #
    # The arithmetic of the height: the foot is lift 2, four treads gain
    # four, and the crossing into THE WEIR descends one -- a surface of
    # 7.0 against the next terrace's 6.0, which is exactly this level's
    # ``rise`` of 5. A stair that overshoots is a level above that opens
    # by dropping back down onto its own terrace, which is the owner's
    # "it puts a ladder there and then jumps back down to a lower part".
    n("glow", arc=3.2, step_y=0, hug=2.8, spread=2, deco="lamp", ceiling=3,
      orbs=1),
    n("gold", arc=3.0, step_y=1, hug=2.6, spread=0, confine=True,
      ceiling=3),
    n("blackstone", arc=3.0, step_y=0, hug=2.8, spread=0, confine=True,
      ceiling=3),
    n("gold", arc=3.0, step_y=0, hug=3.0, spread=0, confine=True,
      ceiling=3, orbs=1),
    n("glow", arc=3.0, step_y=1, hug=3.6, spread=0, pedestal=False,
      ceiling=3, deco="lamp", orbs=2),
])
