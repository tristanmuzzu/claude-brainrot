"""Level 11: THE CRUCIBLE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE CRUCIBLE. A smelting gallery cut into the cliff: a black casting
# floor veined with magma, a lava runner tapped out across it, an
# obsidian furnace standing over the whole thing, and a brick flue at
# the far end that you climb out of on a ladder.
#
# The route is a bank, a pit and a deck, and it goes up, falls, goes up
# again, falls again, and only then leaves. You come in over a glowstone
# sill set flush in the black floor -- one block at which the palette
# stops being the apiary's honey and grass and becomes blackstone, magma
# and obsidian -- cross the tap lip on foot under a duct beam, jump the
# lava cut onto the bank of the runner, walk the bank under the next
# duct, and take two treads up to its head, which is lit and is the
# highest ground in the body of the level. Then **off the head of the
# bank, three blocks down and 4.6 of arc out into the casting pit**,
# whose floor is the melt; through the furnace door on foot under its
# lintel; the charging stair up the inside of the furnace, two treads,
# the top one glowstone and the brightest thing here; and off the front
# of that deck, **two blocks down and 4.6 of arc out again** -- the long
# jump of the level, and the only kind of long jump this motion model
# has, because falling takes time and the body does not slow down while
# it falls. The slag run repeats after it for as long as the terrace
# lasts: a lit pier, a soul-sand stride at 2.51 m/s against a normal
# 5.612, and a magma step back up. The way out is the flue: a lit
# landing hard against the core, four blocks of ladder, and a magma lip
# out over the chasm.
#
# The one thing you would remember is the **obsidian gate**. ``totem``
# renders as two three-wide obsidian piers under a lintel with the
# level's own glow at its shoulders, which in a nether skin is a portal
# frame standing over a lava floor, and the course is steered *through*
# it rather than past it.
#
# Everything here hugs the core at 2.4-3.2 and the drop is off the other
# shoulder. That is the *groove* -- rock within four metres on one side
# on 71% of the real map's samples -- and on a ledge it is also
# load-bearing: unhugged, ``_targets`` pulls a landing to the middle of
# the *band*, which on a five-block shelf inside a nine-block band is
# out over the drop.
#
# Six things here are answers to measurements rather than to taste.
#
# **The exit ladder was not firing.** It was written ``pedestal=False``
# inside ``shell="shaft"``, and ``_climb_move`` wants solid rock within
# one cell of the column at its middle index and at its top: measured,
# ``climb`` was 1% of the move mix over eight runs, which is one run in
# eight, and the other seven silently got the generated staircase --
# thirty-four landings of exit against sixty-six of design. It now
# carries its own pedestal, which is the wall the column hangs on, and
# the tube is gone (RULES 7: a shaft round an authored climb is what
# puts the body *inside* the wall).
#
# **The level was flat.** The elevation in the blueprint was a straight
# line at lift 1-2 from the threshold to the exit -- the owner's "half
# the jumps are at ground level" in one picture. Both beats now climb
# inside themselves on ``step_y``, which is measured from the landing
# before rather than from the terrace and is therefore true wherever the
# body actually is: the level runs 1-1-2-2-3-4 up the tap bank, falls
# three into the pit, climbs 1-1-2-3 up the charging stair and drops two
# off the deck, against the 1-2-1 it used to be. Landings at lift 2 or
# higher went from 40% of the design to **50%**.
#
# **The descent is in the middle, not at the end.** 36 of the real map's
# 43 legs descend somewhere and they do it by falling off an edge; but a
# level that drops after its own high point reads as climb-then-fall,
# and the exit must be the last word. Both drops here are inside the
# body -- off the tap bank into the pit, off the charging deck into the
# slag -- and nothing after the flue goes down.
#
# **A beat cannot start high.** Machinery -- the lock across the level's
# first floor break, and the crossing through the gate -- is inserted
# *between* beats and leaves the body back at lift 1, so a beat whose
# opener asks for lift 2 is asking for a two-block rise a third of the
# time, which nothing in this motion model makes. Every beat here opens
# at lift 1 with `spread`, and every node behind the opener is written
# on `step_y`, which has no lift fallback at all and does not need one:
# a rise measured from the landing before is right wherever the opener
# actually came down.
#
# **The non-hop verbs sit at positions two and four, never at the tail.**
# A beat lays about four fifths of its nodes and a verb written last is
# written and never seen. Three walks in the body plus the flue ladder
# is what takes this level off 93% plain hop; there is nothing else on
# a nether level that fires reliably -- ice is another biome, cobweb
# appears zero times in the entire reference save, and the slime pad
# placed on 6 runs of 24 and fired on 1 when it was measured.
#
# **The floor is the identity.** A real leg of the reference uses a
# median fourteen floor materials with no single one over about a
# quarter; the stock nether mix is ten and two of them are nylium, which
# is a forest floor and not a foundry's. This one is blackstone casting
# sand with magma veins, obsidian spill, coal, iron and raw gold in the
# slag, and soul sand blown into the corners.
LEVEL = Level("THE CRUCIBLE", "nether", rise=5, gap=3.0, exit="ladder",
              band=9.0, profile="ledge", shelf=5.0, breaks=3,
              landmark="totem",
              # Black casting floor, netherrack in the cut face at the
              # rim, netherbrick for everything built, magma for the hot
              # marks, glowstone for the light -- magma is the theme's
              # own ``glow`` and is far too dim to find a landing by --
              # and lava for the runner.
              ground="blackstone", sub="netherrack", rock="netherbrick",
              accent="magma", glow="glowstone", liquid="lava",
              props=("netherfungus", "deadbush", "chain", "torch",
                     "lanternpost", "pebbles"),
              step=("blackstone", "hop"),
              # Twelve materials, dominant at 18%, against the roster's
              # usual two or three. Slag, spill and metal: this is a
              # foundry floor rather than a nether biome, which is the
              # difference between a place and a palette.
              floor=(("blackstone", 3), ("netherbrick", 2), ("magma", 2),
                     ("obsidian", 2), ("deepslate", 1), ("gravel", 1),
                     ("coalore", 1), ("iron", 1), ("rawgold", 1),
                     ("soulsand", 1), ("glowstone", 1), ("tuff", 1)),
              beats=[
    # THE TAP-HOLE. The threshold and the whole of the level's first
    # climb in one beat, because a rise written in one beat and spent in
    # the next is a rise that does not happen: machinery is inserted
    # *between* beats and leaves the body back at lift 1.
    #
    # 1. A glowstone sill flush in the black floor, lit, with a duct
    #    beam over it. This is the reference's own way of saying where a
    #    level begins: an emissive block on a rise, on screen two
    #    seconds before it is reached, and the palette changing
    #    completely at that block with no blend.
    # 2. Across the tap lip on foot, under a beam three cells over the
    #    take-off. A body cannot *jump* under a lid that low -- one
    #    impulse always rises 1.25 m and the head then sweeps the two
    #    cells above every take-off -- so this is the genre's 2bc, the
    #    lid you sprint under, and the only honest form of it this
    #    kernel has.
    # 3. Up onto the bank of the runner, with the lava cut in underneath
    #    the jump. One moat to a beat: the bowl is a radius of three and
    #    a second one inside that digs away the ground the first one's
    #    pedestal is standing on.
    # 4. Along the bank on foot, under the next duct. Floating, because
    #    it lands about three metres downstream of the bowl the moat has
    #    just dug and a stack of terrain cannot stand in a hole.
    # 5-6. Two treads up to the head of the bank, the top one glowstone
    #    and lit: lift 4, and the highest ground in the body of the
    #    level.
    #
    # Everything after the opener is written on `step_y` rather than on
    # `lift`, and that is the difference between a level that climbs and
    # one that reads flat. `lift` is measured from the terrace, so a
    # beat whose opener landed a block high or low (it carries `spread`,
    # so it does, about a fifth of the time) then asks for a rise of two
    # or of nothing; `step_y` is measured from the landing before and is
    # therefore true wherever the body actually is. Measured on this
    # level, converting the chain took exactness from 96% to 99% with
    # every beat at or above 98%, and took landings at lift 2 or higher
    # from 40% to 50%.
    #
    # The second walk at node 4 is the level's cheapest verb and it was
    # measured against the alternatives: it takes the move mix from 84%
    # plain hop to **80%** and *raises* designed content from 50% to
    # 55%, because a flat leg costs the terrace two metres where a jump
    # costs three and the beats behind it then fit.
    ("taphole", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                   ceiling=2, orbs=1),
                 n("blackstone", arc=2.9, step_y=0, hug=2.8, kind="walk",
                   ceiling=3),
                 n("accent", arc=3.2, step_y=1, hug=2.6, moat=True, orbs=1),
                 n("rock", arc=2.9, step_y=0, hug=2.8, kind="walk",
                   pedestal=False, ceiling=3),
                 n("blackstone", arc=3.2, step_y=1, hug=3.0,
                   pedestal=False),
                 n("glow", arc=3.2, step_y=1, hug=3.0, pedestal=False,
                   deco="lamp", orbs=2)]),
    # THE FURNACE. The showpiece, and the level's whole shape in one
    # beat: down, through, up, and off.
    #
    # 1. Off the head of the tap bank and **down** into the casting pit,
    #    4.6 of arc out. Written at lift 1 with `spread=1` and a long
    #    arc on purpose: this beat follows either the bank at lift 4, or
    #    the bank truncated at lift 3, or a piece of machinery at lift 1
    #    -- and 4.6 is a reach of 3.92, which is inside the window at
    #    level, -1, -2 *and* -3. A short arc here is a jump that exists
    #    on paper at one of those heights and at none of the others.
    #    The pit floor is the melt.
    # 2. Through the furnace door on foot, under its lintel. Floating,
    #    because the moat on the node before it has just dug the ground
    #    out from under this one.
    # 3-4. The charging stair inside the furnace, a tread at a time on
    #    `step_y`, so it is a stair wherever the body actually arrived.
    #    The top tread is glowstone and lit -- the brightest thing in
    #    the level, and what you aim at from the door.
    # 5. Off the front of the deck: **two blocks down and 4.6 of arc
    #    out**, the longest jump here. A descent is the only long jump
    #    this model has, and it is written at the same reach of 3.92 for
    #    the same reason as node 1.
    ("furnace", [n("rock", arc=4.6, lift=1, hug=3.2, spread=1,
                   pedestal=False, moat=True, ceiling=2, orbs=2),
                 n("accent", arc=2.9, step_y=0, hug=3.0, kind="walk",
                   pedestal=False, ceiling=3, deco="lintel"),
                 n("blackstone", arc=3.2, step_y=1, hug=2.8,
                   pedestal=False),
                 n("glow", arc=3.2, step_y=1, hug=2.6, pedestal=False,
                   deco="lamp", orbs=1),
                 n("rock", arc=4.6, step_y=-2, hug=3.8, pedestal=False,
                   orbs=2)]),
], filler=[
    # THE SLAG RUN, and this is what the level mostly *is*, because the
    # filler repeats and a script's tail does not: a lit brick pier with
    # a duct beam over it, a soul-sand stride -- 2.51 m/s against a
    # normal 5.612, which is a slow beat and reads as one -- and a magma
    # step back up onto the heap. No moat anywhere in here: the filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on.
    ("slagrun", [n("blackstone", arc=3.4, lift=1, hug=2.8, spread=1,
                   ceiling=2, orbs=1),
                 n("soulsand", arc=2.9, step_y=0, hug=2.6, kind="walk",
                   ceiling=3),
                 n("accent", arc=3.2, step_y=1, hug=3.2, pedestal=False,
                   orbs=1)]),
], exit_beats=[
    # THE FLUE. Written out rather than left to the generated climb,
    # because that one hangs its column mid-lane with nothing within a
    # cell of its middle index to anchor on and is refused silently: the
    # level then gets a six- or seven-step staircase and is never told.
    # Check `--report`'s move mix for the word `climb`; if it is
    # missing, this is a staircase again.
    #
    # Three landings. The foot of the flue, lit and hugged in against
    # the core; four blocks of ladder; and a magma lip **out over the
    # chasm at hug 3.8**, so the last thing before the leap is a lit
    # floor with sky behind it and not a wall -- a single climb of the
    # level's whole rise is nine consecutive frames of flat brick at
    # arm's length, which is the one thing a strip this narrow cannot
    # afford. The lip is written far out rather than at 3.0 because the
    # camera locks onto the landing through take-off and flight: a lip
    # tucked against the core aims the whole ride at the cliff, and the
    # four frames after this ladder were the level's only jammed ones.
    # Measured over four seeds, jam 2.4% -> 2.3% and empty frame 51.3%
    # -> 50.3%, at identical fidelity, unchecked count and move mix --
    # small, and free, and in the right direction on both.
    #
    # `pedestal=True` on the column is the load-bearing line and the
    # reason this branch fires at all: standing the landing on its own
    # stack is what gives the ladder something to hang on for its whole
    # height. There is deliberately **no** `shell="shaft"` round it --
    # the tube is what puts the body inside the wall, and the pedestal
    # plus a rise of at least four is sufficient on its own.
    #
    # The arithmetic of the height: the flue's foot is lift 1, the
    # ladder gains four, the lip gains one, and the crossing into the
    # next level descends one -- lift 5, which is exactly this level's
    # `rise`. A column that overshoots is a level above that opens by
    # dropping back down to its own terrace, which is the owner's "it
    # puts a ladder there and then jumps back down to a lower part".
    n("rock", arc=3.2, lift=1, hug=2.4, spread=2, deco="lamp", orbs=1),
    n("blackstone", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=True, pedestal_style="netherbrick", spread=0,
      orbs=2),
    n("accent", arc=3.2, step_y=1, hug=3.8, spread=0, pedestal=False,
      ceiling=3, orbs=2),
])
