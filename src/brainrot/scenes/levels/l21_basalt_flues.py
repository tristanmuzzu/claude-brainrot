"""Level 21: BASALT FLUES.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# BASALT FLUES. A vent field on a cooling crust: red netherrack plates
# with molten cracks between them, and standing out of them the flues --
# black basalt stacks, each one capped with magma, each one venting. The
# crust is the whole width of the terrace and it is the hazard; the
# stacks are the route.
#
# You come in over a glowstone eye set flush in the red rock, duck under
# a fallen basalt lintel, and go up the caps -- magma, then black stone,
# then a lit crown four blocks over the crust, which is the highest
# ground in the body of the level. Then **off that crown, three blocks
# down and 5.2 of arc out, onto the mouth of a live vent** standing in
# the lava -- the longest jump here, and the only kind of long jump this
# motion model has -- and **the vent throws you two blocks straight back
# up** onto a basalt shelf, which is a rise no jump in this engine makes.
# After that it is the soffit: a low run under the rock brow, through
# the obsidian gate where the crust has chilled over an old flue mouth,
# and then the ash bank for as long as the terrace lasts. The way out is
# the tallest stack, climbed on its own weathered treads.
#
# The one thing a viewer would remember is the vent: falling off a lit
# black crown into a hole full of light and being spat out of it.
#
# ---------------------------------------------------------------------
# **What was already working here, and it is the reason this is a
# rewrite and not a replacement.** On the first contact sheet of the
# whole rebuild this was the one level that read as a real place, and
# the frames that did it are all the same frame: a bright orange magma
# floor filling the bottom, black basalt columns standing out of it, red
# rock behind, and a slot of sky between. That is the reference's own
# composition -- dark brow at the top, the level's own colour at the
# bottom, sky as a slot -- and it arrived by accident, because a
# pedestal is a stack of terrain down to the ground and a pedestalled
# landing on a plaza *is* a basalt stack.
#
# **And the reason the rest of the sheet was grey is that the level
# climbed away from it.** Every beat ended at lift 4 or 5 and the filler
# held there, on purpose, to shorten the exit climb -- and lift 4 on a
# nine-block band is a body above its own coloured floor with nothing
# under two thirds of its view but cone stone and sky. Frames 1-5 of the
# old sheet are the level; frames 10-40 are grey slabs against blue.
# So the pedestals are now written down as the level's *material* -- the
# flues are pedestals, ``pedestal_style`` is blackstone, and the route
# spends its length at lift 1-4 where its own crust is still in frame --
# and the height the exit needs is taken back out of the exit itself
# rather than out of the body of the level.
#
# **The lights were not lights.** ``glow`` was ``shroomlight``, which is
# a bright *texture* that emits nothing: only ``lantern``, ``torch``,
# ``glowstone``, ``sealantern`` and ``magma`` are in ``spiral._GLOWING``.
# Every "lit" landing and every ``deco="lamp"`` in the old file was an
# orange block in the dark. It is glowstone now, and magma keeps the
# accent, which is the pair the reference lights a nether frame with.
#
# **The floor is written out.** A real leg of the reference uses a
# median fourteen floor materials with the dominant one at about a
# quarter; this level named four. Twelve now, at 16% dominant: red
# crust, black basalt, magma veins, ash, soot and the obsidian where it
# has chilled -- so the ground says nether before a single block of the
# course does.
#
# **How it differs from THE CRUCIBLE, which is the other nether level
# and eleven below.** That one is *built*: a smelting gallery on a
# ledge, a tap-hole, a casting pit, a furnace with a charging stair, and
# a ladder up a brick flue. This one is *geological*: an open crust on a
# full floor, no masonry anywhere in it, a natural vent for its gadget,
# and a stair up the outside of a stack for its exit. Same theme, same
# gated totem blueprint, and the two frames have nothing in common but
# the colour of the rock: THE CRUCIBLE reads its obsidian gate as a
# portal frame standing over a tapped floor, and here the same five-high
# obsidian frame is a flue that went out -- the crust chilled around a
# vent mouth, and you run through the hole it left.
#
# ---------------------------------------------------------------------
# Three constraints this level is built around, all of them arithmetic.
#
# **``rise=6`` is above the tower's median and the exit is not
# allowed to be a ladder** (measured elsewhere: a ladder ride is 20.9%
# jammed lens against 0.0% for every other move in the same level, and
# no ``hug`` moves it, because the wall a ladder hangs on *is* the wall
# in the lens). Nothing rises two blocks in one ballistic move, so
# leaving a six-block level on foot is six landings whatever else is
# true. They are written out here rather than left to the generated
# staircase, which is the same six landings unlit, unlidded and hung
# in the corridor -- and the exit is the emptiest third of any level in
# this tower.
#
# **A bubble was considered for it and rejected on one line of the
# renderer.** ``_climb_move`` draws a bubble column as ``water``
# whatever ``climb_style`` says, so a flue that blows would be a blue
# column standing in a lava field -- and the level's whole argument is
# that its palette is red, black and hot.
#
# **Machinery is inserted between beats and leaves the body back at lift
# 1.** So the rise and the fall are in the same beat: a drop written
# across a beat boundary falls off nothing about half the time, and a
# bounce fed by a level hop is silently an ordinary hop with the beat
# still reading as placed.
LEVEL = Level("BASALT FLUES", "nether", rise=6, gap=2.8, exit="stair",
              band=9.0, profile="plaza", breaks=4, landmark="totem",
              # Red crust, black stacks, hot cracks, and glowstone for
              # anything that has to be aimed at. ``magma`` is the only
              # warm material in the engine that emits, and it is far
              # too dim to find a landing by, so the *accent* is magma
              # and the *glow* is glowstone -- one is the heat and the
              # other is the light.
              ground="netherrack", sub="crimsonnylium", rock="blackstone",
              accent="magma", glow="glowstone", liquid="lava",
              # Ash clinker, dead scrub, fungus, and basalt spikes under
              # the brow -- ``dripstone`` is in ``HANGING`` so it is
              # given a ceiling cell and hangs from it, which is the
              # only prop in the set that puts detail in the *top* of
              # the frame.
              props=("netherfungus", "deadbush", "dripstone", "pebbles",
                     "torch"),
              # Only the *fallback* footing -- the way out of here is
              # written landing by landing below and the generated climb
              # never runs. It is soul sand and not blackstone because
              # ``step`` is a roster invariant as well as a level's
              # choice (``test_every_level_climbs_out_on_its_own_footing``
              # counts distinct footings across all thirty-three), and
              # THE CRUCIBLE eleven below genuinely climbs a blackstone
              # stair. Ash-choked treads are this level's version of the
              # same idea.
              step=("soulsand", "hop"),
              # Twelve materials with the dominant at 16%, against the
              # four this level used to name. The reference's identity
              # is its floor, not its structure: a real leg measures a
              # median fourteen kinds with no single one over about a
              # quarter. Crust, basalt, hot veins, ash drift, soot and
              # chilled obsidian.
              floor=(("netherrack", 3), ("blackstone", 3), ("magma", 2),
                     ("gravel", 2), ("soulsand", 2), ("crimsonnylium", 1),
                     ("obsidian", 1), ("wartblock", 1), ("netherbrick", 1),
                     ("glowstone", 1), ("tuff", 1), ("coalore", 1)),
              beats=[
    # THE CRUST. The threshold, the flues, the vent and the blast, all
    # in one beat -- and *why* it is one beat is the only structural
    # thing worth knowing about this file. A beat is laid whole or not
    # at all and is truncated from the end, and machinery is inserted
    # *between* beats: the lock across the level's first floor break and
    # the crossing through the gate both hand the body back at lift 1.
    # So a rise written in one beat and spent in the next is a rise that
    # mostly does not happen, and the fall that feeds the vent would
    # then be a fall off nothing. This beat opens the level, so it never
    # competes with anything for terrace and is never truncated.
    #
    # 1. **A glowstone eye flush in the red crust**, lit, with a plate
    #    of basalt two cells over it. The reference signposts where a
    #    level *begins* with an emissive block set into the floor, on
    #    screen two seconds before it is reached, and the palette
    #    changing completely at that block with no blend. Below is ROPE
    #    BRIDGE -- jungle leaves, planks and lantern poles; from here it
    #    is red rock, black basalt and one hot colour.
    # 2. **Under the fallen lintel, on foot.** A beam three cells over
    #    the take-off. A body cannot *jump* under a lid that low -- one
    #    impulse always rises 1.25 m and the head then sweeps the two
    #    cells above every take-off -- so this is the genre's 2bc, the
    #    lid you sprint under, and the only honest form of it this
    #    kernel has. Second in the beat and not first: a walk needs its
    #    predecessor within half a metre and a beat boundary does not
    #    promise that, and a verb written at a beat's tail is written
    #    and never seen.
    # 3. **Up onto the first cap**, +1 at arc 3.2 -- a reach of 2.52
    #    against a window of 2.00-3.10, centred rather than at the top
    #    of it, because a +1 written at 3.6 is a reach of 2.92 and is
    #    the arc that has to fall back. The crack under the jump is
    #    tapped: one ``moat`` to a beat, because the bowl has a radius
    #    of three and a second one inside it digs away the ground the
    #    first one's pedestal is standing on.
    # 4. **The ash drift**, walked. Floating, because the moat on node 3
    #    has just dug a bowl about three metres upstream of it and a
    #    stack of terrain cannot stand in a hole.
    # 5-6. **Two more caps**, +1 each, to a lit crown four blocks over
    #    the crust. Node 5 carries its own pedestal and node 6 does not,
    #    and that is what a flue *is* here: ``_pedestal`` writes the
    #    stack under a landing in ``pedestal_style or the node's own
    #    style``, so a blackstone landing three blocks up **is** a
    #    three-block basalt column standing out of a red floor, and a
    #    magma one is a lit vent. Nothing else in this file is drawn on
    #    purpose above head height, and this is the mass the first
    #    contact sheet of the rebuild liked.
    # 7. **Off the crown into the vent.** ``step_y=-3`` at arc 5.2: a
    #    reach of 4.52 against a -3 window of 3.72-6.05, and all three
    #    arcs placement may try (5.2, 5.93, 6.66) are inside it. The
    #    longest jump in the level, and a descent is the only long jump
    #    this model has -- falling takes time and the body does not slow
    #    down while it does. Written on ``step_y`` rather than on
    #    ``lift`` so that it is three blocks below *the crown the body
    #    actually reached*, which is what makes node 8 possible.
    # 8. **The vent throws you out.** A pad is fed by the fall onto it
    #    and by nothing else: off three blocks the arrival is about 15
    #    m/s against the 11.0 that clearing two blocks needs, so
    #    ``step_y=2`` -- the only rise in this engine that is not a hop.
    #    ``spread >= 1`` or the bounce is refused silently and placed a
    #    block lower as an ordinary hop; ``pedestal=False`` on both,
    #    because a pad offered only cells with ground under them finds
    #    none at the foot of a fall. The pad's *material* is free --
    #    ``SPRINGY`` is imported by ``spiralplan`` and never read, and
    #    the physics is entirely ``kind="bounce"`` against the previous
    #    landing's impact -- so it is magma, and a green cube in a vent
    #    field is not a place.
    ("crust", [n("glow", arc=3.2, lift=1, hug=3.2, spread=1, deco="lamp",
                 ceiling=2, orbs=1),
               n("blackstone", arc=3.2, step_y=1, hug=3.0,
                 ceiling=3, deco="lintel"),
               n("accent", arc=2.9, step_y=0, hug=2.8, kind="walk", moat=True,
                       orbs=1),
               n("soulsand", arc=2.9, step_y=0, hug=3.0, kind="walk",
                 pedestal=False, ceiling=3),
               n("blackstone", arc=3.2, step_y=1, hug=3.4),
               n("glow", arc=3.2, step_y=1, hug=3.6, pedestal=False,
                 deco="lamp", orbs=2),
               n("magma", arc=5.2, lift=2, step_y=-2, form="slime", hug=3.8,
                 pedestal=False, moat=True, orbs=2),
               n("accent", arc=3.6, step_y=2, kind="bounce", hug=3.2,
                 spread=1, pedestal=False, orbs=3),
               n("rock", arc=3.0, step_y=1, spread=0),
               n("rock", arc=3.0, step_y=1, spread=0),
               n("rock", arc=3.0, step_y=1, spread=0),
               n("rock", arc=3.0, step_y=1, spread=0)]),
    # THE SOFFIT. The quiet beat and the level's only enclosure -- a
    # two-metre pinch and not a room, which is what the reference
    # actually does: fully enclosed 6.1% of the way, an enclosed run
    # lasting a median two metres, but a wall within four metres on one
    # side 71% of the time and a lid overhead on 98%.
    #
    # It opens at lift 1 with ``spread=2`` because it follows machinery
    # -- the lock, or the crossing through the gate -- and a beat whose
    # opener asks for lift 2 is asking for a two-block rise a third of
    # the time, which nothing in this motion model makes. And it is
    # written **long**, at arc 4.0, for the other half of the same
    # problem: when no machinery intervenes it follows the bounce and
    # drops two. A reach of 3.32 is inside the window at level, at -1
    # *and* at -2, so the opener exists whichever of the three heights
    # the body is handed over at; at 3.4 it existed at only two of them
    # and ``--design-only`` refused it.
    #
    # Four landings: in under the brow, the ash drag on foot beneath the
    # rock lid, up onto a hot ledge, and then **down one and 4.4 out**
    # onto a floating plate with a cave roof over it -- a reach of 3.72
    # against a -1 window of 2.35-4.98, the level's second-longest jump,
    # and the one that hands the filler a body already off the floor.
    # The ``shell`` is on the beat's **last** node, which is the only
    # place a shell may go: it is painted the moment its landing commits
    # and its roof then refuses the next arc of the same beat.
    #
    # **Every landing in this beat floats**, and it is the same
    # measurement as the filler's: three arms in one process over the
    # same 24 seeds, only this beat swapped. As written, with stacks
    # under the first three, 62 of 66 (93%); floating the opener and the
    # drift, 66 of 68 (97%); floating all four, **69 of 69**, and the
    # level's exactness 98% -> 99%. This beat runs over the middle of a
    # full floor that has four breaks cut through it, and a landing that
    # wants terrain under it cannot be laid over a hole. What it costs
    # is one basalt column, and the crust's own cap, the ash bank's cap
    # every lap and the whole flight of the exit still stand on theirs.
    ("soffit", [n("blackstone", arc=4.0, lift=6, hug=3.0, spread=2,
                  ceiling=2, pedestal=False, orbs=1),
                n("soulsand", arc=2.9, step_y=0, hug=2.8, kind="walk",
                  pedestal=False, ceiling=3, deco="lintel"),
                n("accent", arc=3.2, step_y=1, hug=3.4, pedestal=False,
                  orbs=1),
                n("netherrack", arc=4.4, lift=6, step_y=-1, hug=3.8,
                  pedestal=False, shell="cave", orbs=2)]),
], filler=[
    # THE ASH BANK, and this is what the level mostly *is*, because the
    # filler repeats and a script's tail does not: a red crust plate
    # under a lid, an ash stride across the drift, and a magma cap on a
    # column of its own. Every lap plants one more vent in the field.
    #
    # It runs at lift 2-3 rather than at 4-5, and that is the change
    # this file exists for. The old filler held the top of the flues to
    # shorten the exit climb and spent the level's whole second half
    # above its own crust, looking at cone stone; the ash bank keeps the
    # glow in the bottom of the frame and the brow across the top of it,
    # and the height the exit wants is now written into the exit.
    #
    # No ``moat`` anywhere in here, and that is not taste: the filler
    # loops, and the second lap digs away the ground the first lap's
    # pedestals are standing on. This level's liquid is in the two beats
    # that play once, plus whatever the crust's own breaks expose.
    #
    # The seam where the loop closes is a jump like any other and half
    # of what a filler ever loses is there: it is -1 off the cap across
    # 3.4 of arc, a reach of 2.72 against a window that opens at 2.35.
    #
    # The cap keeps its pedestal and names no ``pedestal_style``, so the
    # stack under it is magma for its whole height: every lap of the
    # filler plants **a lit vent** in the field, where the crust beat
    # plants a black one and the exit's treads alternate. That is the
    # cheapest colour in the file -- a column is free, it is over head
    # height where this format is otherwise all sky, and it is the
    # difference between a red plate with cubes on it and a vent field.
    #
    # **The first two landings float and the third does not**, and that
    # one keyword is worth fourteen points of this beat. Four arms in
    # one process, same roster and the same 24 seeds, only the filler
    # swapped on the live ``Level``: as written with pedestals under the
    # plate and the drift it laid 44 of 51 (86%); floating the *cap*
    # instead changed nothing at all, to the landing; opening at lift 1
    # rather than 2 made it 90% and cost the level a point of designed
    # content; **floating the plate and the drift laid 56 of 56**, took
    # the level's exactness from 96% to 98% and its hop share from 81%
    # to 80%. The reason is the profile: this is a full floor with four
    # breaks cut through it, the filler is what runs over the late
    # stretch where those breaks are, and a landing that wants a stack
    # of terrain under it cannot be laid over a hole. The cap keeps its
    # pedestal because that pedestal is the flue -- one lit vent a lap,
    # and it stands where the ground is.
    ("ashbank", [n("netherrack", arc=3.4, lift=6, hug=3.2, spread=2,
                   ceiling=2, pedestal=False, orbs=1),
                 n("soulsand", arc=2.9, step_y=0, hug=3.0, kind="walk",
                   pedestal=False, ceiling=3),
                 n("accent", arc=3.2, step_y=0, hug=3.6, orbs=1)]),
], exit_beats=[
    # THE TALL STACK. Six landings up the outside of the last flue,
    # written out rather than left to the generated staircase.
    #
    # It is a stair and not a climb, and that is not a preference. A
    # ladder ride was measured on another level by bucketing every
    # jammed frame by segment *and* move over four seeds: the ride was
    # 20.9% jammed and every other move in that level was 0.0%, with the
    # rays hitting the ladder's own pedestal. It is not tunable -- the
    # wall a ladder hangs on *is* the wall in the lens, and ``hug`` on a
    # climb node is inert. A bubble is the other good answer and this
    # level cannot have one: ``_climb_move`` draws a bubble column as
    # ``water`` whatever its ``climb_style`` says, and a blue column in
    # a lava field is a rendering fault with a story attached.
    #
    # It begins with a threshold of its own: the foot of the stack is a
    # lit landing, and then **a stride on foot under the brow** before
    # the first tread. That is a landing spent on a verb rather than on
    # height, and it is bought back twice -- the exit is the emptiest
    # third of every level in this tower and a lidded walk fills the one
    # column of the ray fan that looks where you are going, and the
    # level's whole non-hop share is otherwise four legs against a
    # staircase that can only ever be hops.
    #
    # The arithmetic of the height. The foot is at lift 2, so its
    # walking surface is 3.0; the walk holds it there; five landings
    # gain five; the top is 8.0
    # against the next terrace's 7.0, and the crossing descends one --
    # which is exactly this level's ``rise`` of 6. A stair that
    # overshoots is a level above that opens by dropping back down onto
    # its own terrace, which is the owner's "it puts a ladder there and
    # then jumps back down to a lower part". The chasm here is 2.8
    # blocks, so the crossing is 4.2 of arc, a reach of 3.52 -- inside
    # the window at level, at -1 *and* at -2, which is what makes the
    # foot's ``spread`` safe: if it comes down at lift 1 the whole stair
    # is a block low and the crossing is simply flat.
    #
    # Every tread is a block up and about three along, written at arc
    # 2.9 -- a reach of 2.22, and its 1.14 fallback is 2.74, both inside
    # the 2.00-3.10 a one-block rise allows. The ``hug`` weaves 2.6 to
    # 3.8 and back, so the flight winds round the outside of the stack
    # instead of being a straight column of identical hops, which is the
    # single most monotonous thing this format can produce and is a
    # third of what a viewer sees. ``confine=True`` keeps the treads on
    # the level's own ground; only the last lip hangs.
    #
    # Every tread carries a lid, and the last one carries none. A
    # ``ceiling`` beam is the cheapest overhead mass a level author has,
    # it is legal over a +1 hop (apex 1.25 against a lid at three), and
    # the exit is the emptiest third of every level in this tower --
    # measured on another level, lidding the treads took empty frame
    # 46.7% to 45.9% at no cost to anything. The lip is bare and lit and
    # thrown **out** at hug 4.2, because the camera locks onto the
    # landing through take-off and flight: a lip tucked against the core
    # aims the last second of the level at the cliff, and a lip over the
    # drop aims it at sky with the next level standing in it.
    n("glow", arc=3.2, step_y=0, hug=3.0, spread=2, deco="lamp", ceiling=3,
      orbs=1),
    n("blackstone", arc=2.9, step_y=0, hug=2.8, kind="walk", spread=0,
      confine=True, ceiling=3, deco="lintel"),
    n("glow", arc=3.0, step_y=1, hug=4.2, spread=0, pedestal=False,
      deco="lamp", orbs=2),
])
