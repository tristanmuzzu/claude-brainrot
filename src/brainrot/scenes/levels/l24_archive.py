"""Level 24: THE ARCHIVE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE ARCHIVE. A reading room built into the tower, and **its floor has
# gone**. The paving survives at the two ends of the hall; between them
# it has dropped into the cistern below and the water has come up, so
# what is left standing in the flood is the shelving -- oak-topped
# bookcases three and four blocks tall, in rows, with the stack tower
# rising out of the middle of them. The route is the tops of the cases.
#
# One sentence: *you get up on the shelving at the second landing, run
# it, come off the end of the tall stack in a two-block fall out into
# the middle of the flooded room, and cross the water on the cases
# before climbing out of the wellhead on the column of water coming back
# up through it.*
#
# The one thing a viewer would remember is that fall: off the top of the
# stacks, out over open water with the lantern on the far case, and
# down.
#
# ---------------------------------------------------------------------
# **How the plaza earns itself, and it is a fourth answer.** Level 3 put
# its route on the roofs *above* a street you could still walk; level 10
# stood you on the furniture standing in a meadow you could still walk;
# level 16 made the floor lethal and bolted the route to the wall over
# it. Here the floor is *not there*. A plaza is a full floor and this
# one is a full floor with its middle removed: three floor breaks, and
# three ponds cut through what is left, each one a radius-three bowl a
# walker drops into and cannot step back out of. That mechanism -- the
# hole, not the liquid -- is the one that actually moves the number
# (`docs/RULES.md` §7: 65.8% -> 25.8% on identical worlds), and it is
# the only one this level uses, because **water is see-through and lava
# is a floor**: THE VAULT's own note says its lava bought atmosphere and
# nothing for the walk. A library's liquid is water, so this level gets
# to be the one where the hazard floor is real.
#
# And it is a *room*. The reference is a groove -- rock within 4 m on
# one side on 71% of samples and a lid overhead on 98% -- and 73% of its
# frames are more than half dark rock across the top. So everything
# built here is `bookshelf`, which is the darkest thing in the level and
# stands four blocks over a pale plaster floor; nearly every landing
# carries a `ceiling` beam (the shelf overhang you run under); three
# shells roof it -- a `hall` over the catalogue, a `tunnel` over the
# highest landing in the level and a `cave` over the wellhead, which is
# `docs/RULES.md`'s "roof the exit's launch" and measured here at two
# points of empty frame for a fifth of a point of jam; and the **gated
# watchtower is a five-by-five gatehouse of bookshelves with a tower of
# them on top of it**, which is the biggest single mass on the level and
# is walked *through* rather than admired. On a `plaza` it has ground to
# stand on -- a `walk` gate is refused on a ledge every time (§7) -- so
# the profile and the frozen landmark want each other.
#
# ---------------------------------------------------------------------
# What was here before was brown on brown with a generated staircase for
# an ending: **73 of its 193 landings over eight runs were the exit
# climb**, 38% of everything the viewer saw, and the sheet's last third
# was a grey stair against sky. Four things changed:
#
# * the way out is written down, and it is a **bubble column** -- the
#   flood coming back up the wellhead. A ladder is ridden at 2.35 m/s
#   and a column at 11.0, and a climbing body has its face against the
#   thing it is climbing, which is why the brief forbids a ladder exit
#   outright. Three landings against the staircase's seven;
# * the level climbs and *falls* inside its first beat, which is the one
#   beat that is never truncated;
# * the floor palette is written out. The library theme's own mix is oak
#   on oak on darkoak, and the last contact sheet of this level was
#   brown boxes on a grey plate;
# * the water stopped being weather. Every pond is now under a jump --
#   the fall lands in one, the catalogue climbs out of one, the gallery
#   hangs over one -- and it is the *hole* a pond digs and not the
#   liquid in it that a walker cannot get out of.
LEVEL = Level("THE ARCHIVE", "library", rise=5, gap=2.8, exit="bubble",
              band=8.5, profile="plaza", breaks=3, landmark="watchtower",
              # Value contrast, which is how every reference frame is
              # built: the palest thing in the level is the floor and
              # the darkest is everything standing on it. Plaster flags
              # underfoot, bookshelf for every case, gatehouse and shell
              # wall, dark oak for the galleries and the merlons, and
              # one lantern at a time doing an actual job.
              ground="plaster", sub="cobble", rock="bookshelf",
              accent="darkoak", glow="lantern", liquid="water",
              candy=("bookshelf", "oak"),
              props=("chain", "lanternpost", "torch", "mcfence", "pebbles"),
              sky=(158, 168, 182), dark=0.5,
              step=("oak", "hop"),
              # Fourteen materials with the dominant one at 23%, which is
              # the shape a real terrace measures as (median 14 kinds,
              # dominant 26%) and the single biggest reason its levels
              # read as places -- against the library theme's own mix,
              # which is oak on darkoak on bookshelf and painted the last
              # contact sheet of this level brown on brown.
              #
              # **Not one brown in it**, and that is the whole point: the
              # reference builds every frame out of a light floor and a
              # dark brow, and here the only wood in the level is the
              # cases standing *on* the flags. So the floor is a flagged
              # reading-room floor -- plaster, cobble, calcite, diorite,
              # the moss where the water has been standing -- and the red
              # runner is the one saturated thing in the level, laid down
              # the middle of it where the reference paints its route.
              floor=(("plaster", 6), ("cobble", 3), ("andesite", 2),
                     ("stone", 2), ("calcite", 2), ("diorite", 2),
                     ("stonebrick", 2), ("wool_red", 2), ("brick", 1),
                     ("chiselled", 1), ("mossy", 1), ("moss", 1),
                     ("gravel", 1), ("clay", 1)),
              beats=[
    # THE STACKS AND THE FLOOD -- the whole level in one beat, and the
    # reason it is one beat is `docs/RULES.md` §7: machinery is inserted
    # *between* beats and hands the body back at lift 1, so a rise
    # written in one beat and spent in the next is a rise that mostly
    # does not happen. The fall needs three blocks of height under it
    # and the only way to be sure of having them is to have climbed them
    # four nodes earlier in the same list. This is also the one beat
    # that is never truncated, because it opens the level and never
    # competes with anything for terrace.
    #
    # 1. A lantern set flush in the flagstones, lit, with the shelf
    #    overhang three cells over it. The reference's way of saying a
    #    level begins: an emissive block on a rise with the palette
    #    changing completely at it and no blend. Below is SPORE HOLLOW,
    #    which is violet mycelium and bone stem; from here it is pale
    #    stone and black oak. `lift=1` and not 2 -- the identical beat
    #    measured 67% at lift 2 and 100% at lift 1, because a beat's
    #    opener is placed from wherever machinery left the body.
    # 2. **Up onto the end of the first case, and that is the second
    #    landing of the level.** 55% of authored landings in this tower
    #    sit at lift 0-1 and that is the owner's "half the jumps are at
    #    ground level" measured; from here to the wellhead nothing in
    #    this level touches the floor again. +1 at `arc` 3.0 is a reach
    #    of 2.32 against a +1 window of 2.00-3.10, centred rather than
    #    at the top of it, because a +1 written at 3.6 is the arc that
    #    has to fall back and a fallback is not `exact`.
    # 3. Along the top of the case on foot, under the next shelf. A walk
    #    is the genre's `2bc` -- the lid you sprint under -- and the only
    #    honest form of it this kernel has, because one jump impulse
    #    rises 1.25 m and the head then sweeps the two cells above every
    #    take-off, so a lintel low enough to read as one refuses any arc
    #    under it. 2.9 of arc is 2.22 m of ground against a walk's 2.4 m
    #    limit.
    # 4. +1 again onto the tall stack, and out from the wall: `hug` goes
    #    3.2, 3.2, 3.6, so the rows step *out* over the room as they get
    #    taller and the top of the stack stands clear with the water
    #    under it.
    #
    #    **Those three numbers were 2.6, 2.6, 3.0 and that was nearly all
    #    of this level's jammed lens.** Bucketed by segment and move over
    #    four seeds -- the method `docs/TOWER.md` asks for and the only
    #    one that finds this -- the beat read `stacks/walk` **41% jammed**
    #    and `stacks/hop` 6.8% against 0.0% for every other move in the
    #    level, and the level as a whole 5.7% against THE VAULT's 1.4%
    #    measured the same way in the same session. Moved out by six
    #    tenths of a block: **1.5%**, `stacks/hop` 0.2%, `stacks/walk`
    #    12.7%, for two points of empty frame (44% -> 46%). On a `plaza`
    #    the core face is a wall like any other and a body hugging it at
    #    2.6 has it inside the lens' three-metre threshold for half the
    #    fan; the launch-block measurement in the brief (`hug` 2.2 -> 2.8,
    #    69 jammed frames -> 0) is the same lever on a different node.
    #
    #    Recorded because it cost an hour and generalises: **`deco` is
    #    not a voxel.** The same beat carried `deco="lintel"` and the
    #    obvious suspect was that beam hanging at head height over a walk
    #    (`_decorate` puts it at the arc's apex + 0.35, and a walk's apex
    #    is the walk, so 1.35 above the feet). Removing it changed the
    #    jam table by **not one frame in any bucket** -- decoration is
    #    drawn and never written to a cell, so it cannot move any probe
    #    that raycasts the world. It is gone anyway: a block at eye
    #    height 1.5 cells in front of the camera is not a thing to leave
    #    in on the strength of a metric that cannot see it.
    # 5. **Off the end and down into the flood.** `step_y=-2` at
    #    `arc` 4.9: a reach of 4.22 against a -2 window of 3.12-5.56,
    #    and the level's long jump, because a descent is the only long
    #    jump this motion model has -- falling takes time and the body
    #    does not slow down while it does. Written on `step_y` rather
    #    than on `lift` so it is two blocks below *the stack the body
    #    actually reached*. It lands on a half-sunk case standing in the
    #    water: the `moat` is on this node and not a later one because
    #    the pond has to be under the jump, not beside it.
    # 6. Across the water onto the next case. It floats, and it has to:
    #    the moat one node back has just dug a bowl of radius three and
    #    a pedestal cannot stand in a hole -- that one keyword is 27,859
    #    "pedestal will not stand" refusals elsewhere in this roster.
    ("stacks", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                  ceiling=3, orbs=1),
                n("bookshelf", arc=3.0, step_y=1, hug=3.2, ceiling=3),
                n("oak", arc=2.9, step_y=0, hug=3.2, kind="walk",
                  ceiling=3),
                n("bookshelf", arc=3.0, step_y=1, hug=3.6, orbs=1),
                n("darkoak", arc=4.9, lift=2, step_y=-1, hug=4.0, moat=True, orbs=2),
                n("bookshelf", arc=3.2, step_y=1, hug=3.6, pedestal=False,
                  orbs=1)]),
    # THE CATALOGUE. The quiet beat and the level's only interior: the
    # card cabinets along the inboard wall, walked rather than jumped,
    # and then up the shelf end onto the gallery deck with the reading
    # room's roof closing over it.
    #
    # It opens at `lift=2` with `spread=1`. Following the beat above
    # that is free; following machinery it costs a fallback, which the
    # spread covers -- and everything after the opener is on `step_y`,
    # so a beat that started a block low still has the shape it was
    # written with.
    #
    # The `walk` is the **second** node and that ordering is measured
    # rather than aesthetic: a beat lays about half its nodes and a
    # non-hop verb written last is written and never seen. Moving each
    # walk to position two took one level from 100% plain hop to 83%.
    #
    # The `shell="hall"` is on the beat's **last** node, which is the
    # only place a shell may go -- it is painted the moment its landing
    # commits and its roof then refuses the next arc of the same beat.
    # At lift 4 it grows a roof and open sides (`_shell` skips a wall
    # column with nothing under it), which is exactly what is wanted:
    # what this tower's sheets are short of is not walls but the dark
    # brow across the top of the frame.
    ("catalogue", [n("darkoak", arc=3.4, lift=3, hug=3.2, spread=1,
                     ceiling=3, orbs=1),
                   n("oak", arc=2.9, step_y=0, hug=3.2, kind="walk",
                     ceiling=3),
                   n("bookshelf", arc=3.0, step_y=1, hug=2.6, moat=True),
                   n("plaster", arc=3.2, step_y=1, hug=2.8, pedestal=False,
                     shell="hall", orbs=2)]),
    # THE GALLERY. The reading balcony slung out over the water on
    # nothing at all, a stride along it under the fallen floor above,
    # and back in against the stacks. A run of floating landings cannot
    # be walked by construction, which is the cheapest unwalkability
    # there is over a full floor, and the balcony at `hug=3.8` stands
    # further out over the room than anything else in the level.
    #
    # Short, and its point first: a beat is truncated in the *middle*
    # once the terrace budget runs out, so whatever a third beat is
    # about has to be in its first node or it is not about anything.
    #
    # The `shell="tunnel"` is on the level's **highest** landing, which
    # is where `docs/RULES.md` §7 says a shell is worth five points of
    # empty frame rather than half of one: at lift 4 a `_shell` finds no
    # footing for its wall columns and skips them, and its roof builds
    # anyway, which is the dark brow over the top of the frame with none
    # of the corridor. It shares the node with a `moat`, which is legal
    # and deliberate -- `_moat` runs first and takes the footing out
    # from under the walls, so what is left is exactly the roof. Adding
    # it took this beat to 100% placed and the level's designed content
    # to 74%; it is on the last node because a shell is painted the
    # moment its landing commits and its roof then refuses the next arc
    # of the same beat.
    ("gallery", [n("darkoak", arc=3.4, lift=4, hug=3.8, spread=1,
                   pedestal=False, deco="lamp", orbs=1),
                 n("oak", arc=2.9, step_y=0, hug=3.8, kind="walk",
                   pedestal=False, ceiling=3),
                 n("bookshelf", arc=3.0, step_y=1, hug=2.8, moat=True,
                   shell="tunnel", orbs=1)]),
], filler=[
    # THE AISLES. The filler repeats and a script's tail does not, so
    # the level's character lives here: the end of a case, the top of it
    # walked under the shelf above, and then off the end and down one
    # into the next aisle. It is the level's shape in three landings,
    # and it neither climbs nor sinks across a lap: case end, case top,
    # down one into the aisle, and back up onto the next case end. The
    # exit column is sized by what the body still has to climb when it
    # starts, so a filler that drifted downhill would buy the level a
    # longer climb every lap.
    #
    # **No `moat` anywhere in here.** The filler loops, and the second
    # lap digs away the ground the first lap's pedestals are standing
    # on. This level's four ponds are all in beats that play once.
    #
    # The seam where the loop closes is a jump like any other and half
    # of what a filler ever loses is there: it is +1 off the low case
    # back onto a case end, which is what the opener asks for.
    ("aisles", [n("bookshelf", arc=3.2, lift=5, hug=2.8, spread=1,
                  ceiling=3, orbs=1),
                n("oak", arc=2.9, step_y=0, hug=2.8, kind="walk",
                  ceiling=3),
                n("darkoak", arc=3.6, lift=5, step_y=0, hug=3.4, pedestal=False,
                  orbs=1)]),
], exit_beats=[
    # THE WELLHEAD. The hall drains into the well at the end of it and
    # the water is coming back *up*: a block of paving to launch from, a
    # column of it up the shaft, and a lit curb at the top to stand on
    # before the leap across the chasm.
    #
    # **A bubble and not a ladder, and not a staircase.** The brief's
    # measurement is unambiguous: an `ascent/climb` ride was 20.9%
    # jammed against 0.0% for every other move in that level, because
    # the wall a ladder hangs on *is* the wall in the lens and `hug` on
    # a climb node is inert. A column is ridden at 11.0 m/s against a
    # ladder's 2.35, so the same six blocks are on screen for a fifth of
    # the time -- one level measured 14.9% -> 6.6% swapping to it. And a
    # flooded archive is the level whose *idea* is the water, which is
    # the one level in five `docs/RULES.md` §3 says a climb exit belongs
    # on.
    #
    # `pedestal=True` and `step_y=4` are the recipe and both are
    # load-bearing. `_climb_move` wants solid rock within one cell of
    # the column at its **middle index** and at its **top**, and out in
    # the lane the only candidate is the landing's own stack; floated,
    # the column is refused silently -- 11,097 of 13,000 candidates on a
    # generated bubble exit -- and the level gets a staircase without
    # being told. **Check the move mix for the word `bubble` by name
    # after touching anything here**; its absence is silent and reads as
    # 100% placed.
    #
    # The launch block stands at `hug=2.8` and not 2.2, and that one
    # number is most of a level's jammed lens: measured elsewhere, 69
    # wall-jammed frames of 1,293 at 2.2 against **0 of 1,280** at 2.8.
    # Both ends carry a `ceiling` beam, which is the cheapest overhead
    # mass a level author has -- the exit is the emptiest third of any
    # level in this tower, a climb with sky on five sides of it.
    #
    # The arithmetic of the height: the launch is lift 1, the column
    # gains four, the curb one -- lift 6, a walking surface of 7.0
    # against the next terrace's 6.0, which is this level's `rise` of 5
    # plus the one block the crossing comes down. A stair that
    # overshoots is a level above that opens by dropping onto its own
    # terrace, which is the owner's "it puts a ladder there and then
    # jumps back down to a lower part".
    n("plaster", arc=2.8, step_y=0, hug=2.8, spread=1, confine=True,
      ceiling=3, shell="cave"),
    n("oak", arc=2.4, step_y=1, kind="bubble", hug=2.0, pedestal=True,
      pedestal_style="cobble", spread=0, deco="lamp", orbs=2),
    n("glow", arc=3.0, step_y=0, hug=3.2, spread=0, pedestal=False,
      ceiling=3, deco="lamp", orbs=1),
])
