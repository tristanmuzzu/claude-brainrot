"""Level 16: THE VAULT.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE VAULT. A strongroom cut into the cliff, and its floor is the melt:
# lava tapped in under the paving so nothing can be carried out across
# it. The bullion was never on that floor. It stands clear of it on the
# strongroom's own **racking** -- an iron shelf, a course of bars, a lit
# top tier -- cantilevered further out over the lava the higher it goes,
# and that racking is the route.
#
# **How the plaza earns itself, and it is not level 3's answer or level
# 10's.** Level 3 put its route on the roofs *above* its street; level 10
# made everything you stand on a hive. Here the floor is not something
# you decline to use -- it is the hazard, and the level is the shelving
# bolted to the wall over it. You come in through the vault door on foot
# under its lintel, climb three tiers of racking to four blocks up, and
# then **fall three blocks out into the middle of the room onto a magma
# pad standing in the melt** -- the level's showpiece and its one long
# jump, because a descent is the only long jump this motion model has --
# and the pad throws you two blocks straight back up onto a stack of
# bullion. From there it is piers over the lava for as long as the
# terrace lasts, and out up the strongroom ladder in the corner.
#
# The one thing a viewer would remember is that fall: off the top of the
# racking, down past the lit gold gate, into a room whose floor is
# glowing.
#
# What was here before was the same premise stated and not delivered.
# Its elevation in the blueprint was a **flat line at lift 1** from the
# threshold to the exit -- the owner's "half the jumps are at ground
# level" drawn as a picture -- with three beats of nearly identical
# 2.85-3.2 m hops on it. Six things changed and each is a measurement:
#
# * **The level now climbs inside its first beat.** The threshold, the
#   door and the whole rack are one beat, because machinery -- the lock
#   across the first floor break, the crossing through the hoard gate --
#   is inserted *between* script beats and puts the body back at lift 1.
#   A rise written in one beat and spent in the next is a rise that
#   happens once in three visits.
# * **Three beats became two and a filler.** A level lays nine to twelve
#   landings; the old third beat measured 92% and was competing with the
#   filler for a terrace that had already spent thirty landings on a
#   generated exit staircase.
# * **The way out is written down.** ``exit_beats`` was empty, so the
#   exit was the generated climb -- thirty of the level's eighty-four
#   machinery landings, and six consecutive frames of flat wall at
#   arm's length on the contact sheet (85 jammed frames of 619, 13.7%,
#   against the tower's 1.8%). The launch block is what does that, not
#   the ladder: it is now at ``hug=2.8`` with the lip out at 3.8, so the
#   last thing before the leap is a lit floor with sky behind it.
# * **The lava was doing nothing for the walker.** Lava is solid, so a
#   no-jump walker simply walks across the top of a lava moat -- the
#   moats here are atmosphere and always were. What holds the number
#   down is that from the door onward almost every landing is
#   ``pedestal=False``: there is nothing under the route to walk to.
# * **The floor is written out.** The gold theme's own mix is deepslate,
#   stone, gravel, andesite, cobble and iron -- five kinds of pale grey
#   -- and half the old sheet was a grey plate with gold cubes standing
#   on it. Twelve materials now, all of them warm-dark or metal.
# * **``ceiling=`` is a checked lid and against this cliff it is often
#   refused** for a reason nothing reports: the cells it wants are
#   inside the rock. It is spent here on the two nodes that are moves
#   under something -- the vault door and the ledger plank -- where it
#   is the genre's 2bc, the lid you sprint under, rather than on every
#   landing.
LEVEL = Level("THE VAULT", "gold", rise=5, gap=2.4, exit="ladder",
              band=10.0, profile="plaza", breaks=3,
              landmark="hoard",
              # Warm-dark and committed: raw gold paving underfoot,
              # blackstone for everything built, bullion for the prize,
              # lava for the light. Dark enough to light itself, which
              # is what puts a lamp at the far end of every stretch and
              # nowhere in between.
              ground="rawgold", sub="deepslate", rock="blackstone",
              accent="gold", glow="glowstone", liquid="lava",
              props=("torch", "chain", "lanternpost", "pebbles"),
              dark=0.62, step=("gold", "hop"),
              # Twelve materials with the dominant one at 17%, which is
              # the shape a real terrace of the reference measures as:
              # one committed hue and a long tail of grit under it. The
              # theme's own mix is five kinds of pale grey and painted
              # this level as a car park.
              floor=(("blackstone", 3), ("rawgold", 3), ("gold", 2),
                     ("deepslate", 2), ("goldore", 1), ("copper", 1),
                     ("iron", 1), ("magma", 1), ("obsidian", 1),
                     ("chiselled", 1), ("tuff", 1), ("gravel", 1)),
              beats=[
    # THE DOOR AND THE RACKING. The threshold and the whole of the
    # level's climb in one beat, for the reason above: a rise split
    # across a beat boundary is a rise the machinery in between undoes.
    #
    # 1. A glowstone sill flush in the raw-gold paving, lit, with a lid
    #    two cells over it. This is the reference's own way of saying
    #    where a level begins -- an emissive block on a rise, on screen
    #    two seconds before it is reached, and the palette changing
    #    completely at that block with no blend. Below is WOOLWORKS,
    #    which is pink wool on timber; from here it is gold and black.
    # 2. Through the vault door on foot, under its lintel, three cells
    #    over the take-off. A doorway is walked and never jumped: one
    #    impulse always rises 1.25 m and the head then sweeps the two
    #    cells above every take-off, so an arc under a lid low enough to
    #    read as a door is refused every time. It is second in the beat
    #    and not first because a walk needs its predecessor within half
    #    a metre and a beat boundary does not promise that.
    # 3-5. The racking: iron shelf, a course of bars, and the lit top
    #    tier. Three +1 hops at arc 3.2 -- a reach of 2.53 against a +1
    #    window of 2.00-3.10, centred rather than at the top of it,
    #    because a +1 written at 3.6 is a reach of 2.92 and is the arc
    #    that has to fall back. What varies is not the jump, it is the
    #    ``hug``: 2.6, 2.8, 3.0, so the rack steps *out* over the lava
    #    as it climbs and the last tier stands clear of the wall with
    #    the room under it.
    #
    # Everything after the opener is on ``step_y``, which is measured
    # from the landing before rather than from the terrace and is
    # therefore true wherever the opener actually came down -- it
    # carries ``spread``, so it lands a block high or low about a fifth
    # of the time, and ``lift + 1`` on the node after it is then a rise
    # of two, which nothing in this motion model makes.
    #
    # One moat, on node 3, and node 4 floats because of it: the bowl is
    # a radius of three and a pedestal cannot stand in the hole the
    # landing before has just dug. The lava is the light in here as much
    # as the lamps are.
    #
    # The ``cave`` shell is on the beat's **last** node, which is the
    # only place a shell may go -- it is painted the moment its landing
    # commits and its roof then refuses the next arc of the same beat.
    # At lift 4 it grows a roof and no walls (``_shell`` skips a wall
    # column with nothing under it), which is exactly what is wanted:
    # the vault's ceiling four blocks over the top of the racking, and
    # the dark brow across the top of the frame that this tower's shots
    # have never had.
    ("door", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                ceiling=2, orbs=1),
              n("blackstone", arc=2.9, step_y=0, hug=2.8, kind="walk",
                ceiling=3, deco="lintel"),
              n("iron", arc=3.2, step_y=1, hug=2.6, moat=True, orbs=1),
              n("gold", arc=3.2, step_y=1, hug=2.8, pedestal=False),
              n("glow", arc=3.2, step_y=1, hug=3.0, pedestal=False,
                deco="lamp", orbs=2, shell="cave")]),
    # THE MELT. The showpiece, written **second** and not last: a beat's
    # budget is spent on ``arc`` and the longest arc in the last beat is
    # eaten first, which is always the level's best jump.
    #
    # 1. **Off the top of the racking, three blocks down and 4.9 of arc
    #    out, onto a magma pad standing in the lava.** A reach of 4.22
    #    against a -3 window of 3.72-6.05. Written at ``lift=1`` with
    #    ``spread=1`` rather than on ``step_y``, because this beat
    #    follows either the rack at lift 4, or the rack truncated at
    #    lift 3, or a piece of machinery at lift 1 -- and 4.22 is inside
    #    the window at *every one* of those: level (2.00-4.26, by four
    #    centimetres), -1, -2 and -3. A short arc here is a jump that
    #    exists on paper at one of those heights and at none of the
    #    others.
    # 2. **The melt throws you back out.** A slime pad is fed by the
    #    fall onto it and by nothing else: the arithmetic is
    #    ``bounce_launch(impact)``, and off this drop the impact is
    #    13.37 and the launch 12.83 against the 10.58 that clearing two
    #    blocks needs -- so ``step_y=2``, the only rise in this engine
    #    that is not a hop, onto a stack of bullion. Off a two-block
    #    drop it would be 11.22 and still fire; off one block, 8.87, and
    #    it silently becomes an ordinary hop with the beat still reading
    #    as placed. The pad is ``magma`` and not slime because the
    #    material of a pad is free -- ``SPRINGY`` is imported and never
    #    read -- and a green cube in a strongroom is not a place.
    #    ``pedestal=False`` on both: a pad offered only cells with
    #    ground under them finds none at the foot of a fall, and the
    #    moat has just dug the ground out anyway.
    # 3. Across the ledger plank on foot, under an iron bar at three.
    #    The level's second walk, at position three rather than at the
    #    tail, because a beat lays about four fifths of its nodes and a
    #    verb written last is written and never seen.
    # 4. Down off the stack onto the first pier, one block and 4.4 of
    #    arc -- a reach of 3.72 against a -1 window of 2.35-4.98. The
    #    level's second-longest jump, and it hands the filler a body at
    #    lift 2 over the melt rather than on the floor.
    ("melt", [n("magma", arc=4.9, lift=1, form="slime", hug=3.4, spread=1,
                pedestal=False, moat=True, orbs=2),
              n("gold", arc=3.6, step_y=2, kind="bounce", hug=2.8,
                spread=1, pedestal=False, orbs=3),
              n("chiselled", arc=2.9, step_y=0, hug=3.0, kind="walk",
                pedestal=False, ceiling=3, deco="lintel"),
              n("blackstone", arc=4.4, step_y=-1, hug=3.2, pedestal=False,
                orbs=2)]),
], filler=[
    # THE PIERS, and on a level whose script is nine landings this is
    # most of what is seen, because the filler repeats and a script's
    # tail does not. Three landings that close into a loop: a blackstone
    # pier standing in the melt, a gold ledger plank walked across to
    # the next one, and a half-height shelf of iron bars.
    #
    # It opens at **lift 2**, not lift 1. Following another script beat
    # that is free and it is the one real lever a level has against
    # "half the jumps are at ground level"; following machinery it costs
    # a fallback, which ``spread=2`` covers. The seam where the loop
    # closes is a jump too -- half a filler's fidelity is lost there --
    # and it is a -0.5 off the slab across 3.4 of arc, a reach of 2.73
    # against a window that opens at 2.00.
    #
    # The shelf is ``form="slab"``, written on ``lift`` and not on
    # ``step_y``: a slab stands half a block down in its own cell, so
    # ``lift 3`` is a walking surface at 3.5 and a *half* step up off
    # the plank. Slabs and stairs are the commonest non-cube form in the
    # reference by a wide margin and this tower barely uses them; a
    # half-height ledge is cheap, reads as deliberate architecture, and
    # buys reach (3.78 m at +0.5 against 3.10 at +1).
    #
    # No moat anywhere in here, and that is not taste: the filler loops,
    # and the second lap digs away the ground the first lap's pedestals
    # are standing on. This level's lava is in the two beats that play
    # once.
    ("piers", [n("blackstone", arc=3.4, lift=2, hug=2.8, spread=2,
                 ceiling=2, orbs=1),
               n("gold", arc=2.9, step_y=0, hug=2.6, kind="walk",
                 ceiling=3),
               n("iron", arc=3.6, lift=3, form="slab", hug=3.0,
                 pedestal=False, orbs=1)]),
], exit_beats=[
    # THE STRONGROOM SHAFT. Written out rather than left to the
    # generated climb, which hangs its column mid-lane with nothing
    # within a cell of its middle index to anchor on, is refused
    # silently, and hands the level a six- or seven-step staircase
    # instead -- thirty landings of the eighty-four this level used to
    # spend on machinery. Check ``--report``'s move mix for the word
    # ``climb``; if it is missing, this is a staircase again.
    #
    # Three landings. The foot of the shaft, lit, at **hug 2.8**; four
    # blocks of ladder; and a gold lip **out at hug 3.8** with a lid
    # over it.
    #
    # The two ``hug`` numbers are the whole of this level's worst
    # measurement. The old sheet had six consecutive frames of flat wall
    # at arm's length during the climb out -- 13.7% of the level's
    # frames against the tower's 1.8% -- and the launch block is what
    # causes that, not the ladder: measured elsewhere on this tower, a
    # launch at ``hug=2.2`` gives 69 jammed frames of 1,293 and the same
    # level at 2.8 gives 0 of 1,280. ``hug`` on the climb node itself is
    # inert. The lip is thrown out to 3.8 for the other half of it: the
    # camera locks onto the landing through take-off and flight, so a
    # lip tucked against the core aims the whole ride at the cliff.
    #
    # ``pedestal=True`` on the column is the load-bearing line and the
    # reason this branch fires at all -- ``_climb_move`` wants solid
    # rock within one cell of the column at its middle index and at its
    # top, and out in the lane the landing's own stack is the only
    # candidate there is. There is deliberately no ``shell="shaft"``
    # round it: the tube is what puts the body inside the wall.
    #
    # The arithmetic of the height: the foot is lift 1, the ladder gains
    # four, the lip gains one, and the crossing into THE WEIR descends
    # one -- a surface of 7.0 against the next terrace's 6.0, which is
    # exactly this level's ``rise`` of 5. A column that overshoots is a
    # level above that opens by dropping back down to its own terrace,
    # which is the owner's "it puts a ladder there and then jumps back
    # down to a lower part".
    n("glow", arc=3.2, lift=1, hug=2.8, spread=2, deco="lamp", orbs=1),
    n("blackstone", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=True, pedestal_style="blackstone", spread=0,
      orbs=2),
    n("gold", arc=3.2, step_y=1, hug=3.8, spread=0, pedestal=False,
      ceiling=3, orbs=2),
])
