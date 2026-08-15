"""Level 28: THE SEA GATE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The monument's tide gate, with the sea coming through it.
#
# One sentence: *you come in over a sea lantern set flush in the paving,
# duck under the gate's own gilded beam at a run, climb the gate stone
# two blocks to the coping, and then step off it into a two-block fall
# out onto a sand bar in the notch the sea has eaten out of the terrace
# -- and you leave on the sluice, a column of water forced back up
# through the gate.*
#
# The thing a viewer would remember is that fall: off the top of the
# gate, out past the broken edge of the shelf, down onto pale sand with
# open water round three sides of it.
#
# ---------------------------------------------------------------------
# **What was wrong with the old one, measured.** It was a decent-looking
# ledge with a fatal shape: 39% designed content, **97 of its 214
# landings over eight runs were the exit staircase**, and the elevation
# in ``blueprint.png`` was a flat line of design with one long orange
# diagonal bolted on the end. That is the owner's complaint verbatim --
# *a couple of ground-level hops, then a couple higher, then stairs* --
# and it is one keyword: a level with no ``exit_beats`` reserves seven
# landings for a staircase before a single beat is laid
# (``handplan.Course._level_budget``), so the staircase costs the level
# twice, once in terrace it never gets and once in frames of grey stair
# against sky. It was also 91% plain hop against an 85% rule, and one
# moat in the whole level on the theme whose liquid is the point.
#
# Three things were tried against it and measured in one process --
# same roster, same seeds, both arms on the live ``Level`` object,
# because the absolutes swing thirty points between processes while
# thirty-two neighbours are being rewritten.
#
# * **``plaza`` was tried and rejected.** ``docs/RULES.md`` §7 says a
#   ``walk`` gate -- and ``watchtower`` is one -- almost never reserves
#   on a ledge, which would make this level's frozen landmark invisible
#   and argue for the full floor. On *this* level it is not true: at
#   ``band=12.0`` with a six-cell shelf the gatehouse reserves and the
#   course is steered through it on 9 landings in 8 runs, against 7 on
#   the plaza. The plaza's bill was the walker -- **35% -> 45% mean, 53%
#   -> 59% worst**, the last of those over the rule -- for nothing at
#   all. The wide shelf is what buys the gate here, not the profile.
# * **The way out is written down and it is a bubble column.** Same
#   worlds, stair against sluice: exit climb **45% -> 20%** of the
#   level's landings, designed content **58% -> 68%**, hop share 85% ->
#   83% with ``bubble`` appearing in the mix by name. A ladder is
#   forbidden by the brief on measurement (its ride is the wall in your
#   lens, 20.9% jammed against 0.0% for every other move in the level
#   that measured it) and a prismarine gate is the one place a column of
#   water needs no excuse.
# * **On a `ledge`, a moat belongs at the shelf's *edge*, not under the
#   lane.** This cost two passes and is the one finding here worth
#   carrying to another level. ``_moat`` digs a radius-**three** bowl,
#   and a six-cell shelf is six cells wide: a pond centred on the
#   running line at ``hug`` 3.0-3.6 takes the whole terrace out for six
#   metres of arc, and then the *next* feature -- a beat opener, the
#   lock, the crossing -- has nowhere to stand. Instrumented, every
#   unchecked emergency placement in the level was the landing
#   immediately after a moat. Moved outboard to ``hug`` 4.4-4.8 and
#   floated (``pedestal=False``), the bowl is clipped by the shelf edge
#   and cuts a *notch* instead of a hole, leaving the inboard lane dry
#   for the machinery: unchecked **5 -> 1** in twelve runs, exact 95% ->
#   **97%**, and both ponds kept. Deleting the moats altogether measured
#   *worse* than moving them (3 unchecked), which is the part nobody
#   would guess. It is also the better fiction: the sea has broken the
#   sea wall, and what it eats is the edge.
#
# Three more things were measured here and **rejected**, recorded so
# nobody spends the hour again:
#
# * **Pulling every ordinary landing 0.4 in from the shelf edge** buys
#   1.8 points of empty frame (52.3% -> 50.5% over four seeds) and costs
#   the basin beat 91% -> 84%, the causeway 96% -> 92%, three of sixteen
#   landmark crossings and an extra unchecked placement. The frame is not
#   worth a beat.
# * **``ceiling=5`` instead of 3 on every lidded node, and a ``tunnel``
#   over the causeway's highest landing, both produced worlds identical
#   to the frame** -- same jam, same empty, same buckets, over four
#   seeds. The lens probe reaches 4.6 m above the eye and a beam is one
#   cell wide, so overhead mass on a shelf this wide is a thing you build
#   for the *sheet*; no number here can see it.
# * **Moving the sluice column outboard is a straight trade, and 2.0 is
#   the right end of it** -- which contradicts ``docs/RULES.md`` §7's
#   note that ``hug`` on a climb node is inert. That is true of a ladder
#   hanging on a wall and false of a column standing on its own plinth:
#   ``hug`` 2.0 / 2.6 / 3.2 measures jam **1.8 / 4.0 / 4.9%** against
#   empty 50.5 / 48.7 / 47.6%. The plinth is the wall in the lens, and a
#   jammed frame is worse than an empty one.
#
# ---------------------------------------------------------------------
# **It is a place, and the place is a machine.** Everything built here
# is the monument's dressed stone -- ``darkprismarine``, the darkest
# thing in the level -- standing on a mid-teal prismarine pavement with
# pale sand drifted through it, and the only warm things in a cold level
# are the gate's gilding and its bronze bollards. Value contrast is how
# every reference frame is built: the darkest mass in the upper half,
# the level's own colour across the bottom. Fourteen materials with the
# dominant one about a quarter, which is what a real terrace measures
# as; two lights, and both are doing a job -- the threshold lantern and
# the lit sill of the sluice, which is the route painted.
#
# Against DUST DEVILS below (red sand, an orange sky, a dry canyon) the
# palette changes completely at the first lantern, and against THE
# CORNICE above (snow, white timber, an open rim) this is the dark one
# with water in it.
LEVEL = Level("THE SEA GATE", "prismarine", rise=5, gap=2.8, exit="bubble",
              band=12.0, profile="ledge", shelf=6.0, breaks=3,
              landmark="watchtower",
              # Six roles, all set, each doing one job: prismarine
              # paving underfoot, the sand the tide has put over it in
              # the cut face and on the bar, the monument's dark dressed
              # stone for everything built, gold for the gate's own
              # gilding, and one sea lantern at a time.
              ground="prismarine", sub="sand", rock="darkprismarine",
              accent="gold", glow="sealantern", liquid="water",
              candy=("darkprismarine", "gold"),
              props=("chain", "coralfan", "lilypad", "vinehang", "pebbles",
                     "mcfence"),
              sky=(88, 150, 162), dark=0.45,
              step=("darkprismarine", "hop"),
              # The tail under the four roles. A drowned monument court
              # is not a teal plate: it is cut stone with sand drifted
              # across it, shell grit and gravel where the surge sorts
              # it, clay and moss in the cells the water stands in, and
              # the bronze and coral crust of everything that has been
              # under water. Thirteen kinds here plus the four roles on
              # top at high weight, which is the median-14 shape the real
              # map measures as. **No ``sealantern`` in the floor mix**,
              # unlike the theme's own: there is no ambient decorative
              # lighting anywhere in the reference and there is none
              # here.
              floor=(("darkprismarine", 3), ("sand", 3), ("gravel", 2),
                     ("calcite", 2), ("clay", 2), ("sandstone", 2),
                     ("moss", 2), ("stone", 2), ("mossy", 1), ("cobble", 1),
                     ("copper", 1), ("coral_blue", 1), ("gold", 1)),
              beats=[
    # THE SILL -- the whole idea of the level in one beat, and it is one
    # beat because machinery is inserted *between* beats and hands the
    # body back at lift 1 (``docs/RULES.md`` §7): a rise written in one
    # beat and spent in the next is a rise that mostly does not happen,
    # and this beat's point is the two blocks it climbs and the two it
    # then throws away. It is also the beat that is never truncated, and
    # measured -- every node given its own label over twelve runs -- its
    # first six landings are laid on 15 visits of 15 and its seventh on
    # 13, which is why everything the level is about is in here.
    #
    # 0. A sea lantern flush in the paving, lit, on a rise. The
    #    reference's way of saying a level begins: an emissive block in
    #    the floor with the palette changing completely at it and no
    #    blend -- red sand and an orange sky below, teal stone and sea
    #    light from here. ``lift=1`` and not 2: a beat's opener is placed
    #    from wherever machinery left the body, and the identical beat
    #    measures 67% at lift 2 against 100% at lift 1.
    # 1. The gate's outer threshold plate, level. The node after an
    #    opener asks for the **same** ``lift``, because the opener
    #    carries ``spread`` and sits a block high or low about a fifth of
    #    the time -- ``lift + 1`` there is a rise of two, which nothing
    #    in this motion model makes.
    # 2. **Under the gate's beam at a run.** The gilded lintel three
    #    cells over the take-off, sprinted under. This is the genre's
    #    ``2bc`` and the only honest form of it this kernel has: one jump
    #    impulse rises 1.25 m and the head then sweeps the two cells
    #    above every take-off, so a lid low enough to read as a doorway
    #    refuses every arc under it -- it is only expressible over a leg
    #    that never leaves the ground. 2.9 of arc is 2.22 m of ground
    #    against a walk's 2.4 m limit, and it is at position two because
    #    a beat lays about half its nodes and a non-hop verb written last
    #    is written and never seen.
    # 3. **Up onto the gate stone, and that is the third landing of the
    #    level.** 55% of authored landings in this tower sit at lift 0-1;
    #    from here nothing in this level touches the terrace again until
    #    the exit. +1 at ``arc`` 3.2 is a reach of 2.52 against a +1
    #    window that shuts at 3.10 -- centred, not at the top of it,
    #    because the arc that has to fall back is not ``exact``.
    # 4. +1 again onto the coping, surface 4.0, and out: ``hug`` steps
    #    3.0, 3.2, 3.4 so the gate leans out over the water as it gets
    #    taller.
    # 5. **Off the coping into the notch.** ``step_y=-2`` at ``arc=4.9``:
    #    a reach of 4.22 against a -2 window of 3.12-5.56, and the
    #    level's long jump, because a descent is the only long jump this
    #    motion model has -- falling takes time and the body does not
    #    slow down while it does. It lands on the sand bar the tide has
    #    left, out at ``hug=4.8`` where the moat's bowl is clipped by the
    #    shelf edge (see the note above -- this one number is four fifths
    #    of the level's unchecked placements), and it floats, because a
    #    pedestal cannot stand in the hole its own moat digs.
    # 6. Back in off the bar onto a bronze bollard standing in the water.
    ("sill", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                ceiling=3, orbs=1),
              n("rock", arc=3.2, lift=2, hug=3.0, ceiling=3),
              n("accent", arc=2.9, step_y=0, hug=3.0, kind="walk", ceiling=3),
              n("ground", arc=3.2, step_y=1, hug=3.2, orbs=1),
              n("ground", arc=3.2, step_y=1, hug=3.4),
              n("sub", arc=4.9, lift=2, step_y=-2, hug=4.8, moat=True, pedestal=False,
                orbs=2),
              n("copper", arc=3.2, step_y=1, hug=3.0, pedestal=False,
                orbs=1)]),
    # THE BASIN -- the drowned court behind the gate, and the level's
    # half-height architecture. Stairs and slabs are the reference's
    # commonest non-cube form by a wide margin and this tower has almost
    # none; a slab stands half a block *down* in its own cell, so
    # ``lift=2, form="slab"`` off a lift-1 landing is a **+0.5 stride**,
    # inside the 0.55 a walk allows and inside its 2.4 m of ground at
    # ``arc=2.8``. It is the lit one: on a wide shelf of open pavement
    # the lamp on the sluice sill is the only thing saying which way the
    # gate runs, and the reference lights the place you are going to and
    # nothing else.
    #
    # The second pond is nine metres downstream of the first -- two moats
    # any closer and the second landing stands in the bowl the first dug
    # -- and it is out at ``hug=4.4`` for the same reason the first is,
    # with the gold mooring block floating over it.
    #
    # The ``grotto`` is on the beat's **last** node, which is the only
    # place a shell may go: it is painted the moment its landing commits
    # and its walls then refuse the next arc of the same beat. A grotto
    # rather than a hall or a tunnel because it is carved *into* the
    # cliff -- on a ledge a walled shell can only find footing on the
    # core side, which stands a wall right beside the lens.
    ("basin", [n("rock", arc=3.4, lift=2, hug=3.0, spread=1, ceiling=3,
                 orbs=1),
               n("ground", arc=2.8, lift=3, hug=2.8, form="slab", kind="walk",
                 deco="lamp"),
               n("accent", arc=3.4, lift=3, hug=4.4, moat=True,
                 pedestal=False, orbs=1),
               n("rock", arc=3.2, lift=4, hug=3.2, pedestal=False,
                 shell="grotto", orbs=2)]),
    # THE CAUSEWAY -- what is left of the road out to the gate: three
    # piers over open water with nothing under two of them, at the
    # level's high ground. A run of floating landings cannot be walked by
    # construction, which is the cheapest unwalkability there is, and it
    # is the last beat because a beat is truncated in the *middle* and a
    # third beat is a beat the terrace may not reach -- so nothing the
    # level is about is in here. Measured, it lays 11 / 10 / 8 of its
    # three nodes over 15 visits.
    #
    # ``ceiling=5`` and not 3: a lid is a one-cell beam spread along the
    # direction of travel, so five of them roof nearly the whole arc in
    # the one column of the ray fan that looks where you are going, and
    # chained landing to landing they read as the causeway's remaining
    # arches.
    #
    # **The last landing is a stride, not a jump, and it is written on
    # ``step_y`` for a reason worth carrying to another level.** You walk
    # out to the end of the pier and stand where it breaks off. Written
    # as ``lift=3`` -- the same height in absolute terms -- the beat fell
    # from 96% to **82%**, twice, in two separately measured arms: the
    # node before it carries the default ``spread=2`` and lands a block
    # high or low often enough, and a walk whose predecessor is a block
    # below is a rise of one against the 0.55 a walk allows. ``step_y=0``
    # is level with wherever the body actually got to and is never
    # refused. Worth three points of hop share on its own -- 84% -> 81%,
    # walk 10% -> 13% -- for no fidelity at all.
    ("causeway", [n("rock", arc=3.4, lift=3, hug=3.2, spread=1, ceiling=5,
                    orbs=1),
                  n("accent", arc=3.2, lift=4, hug=3.4, pedestal=False,
                    ceiling=5, orbs=1),
                  n("copper", arc=2.9, step_y=0, hug=3.6, kind="walk",
                    pedestal=False, deco="post", ceiling=5, orbs=1)]),
], filler=[
    # THE MOORINGS -- the character, repeated, because the filler loops
    # and a script's tail does not. The quay stone, a stride along the
    # boom under the next beam, and up onto a bollard standing free out
    # towards the rim. It neither climbs nor sinks across a lap: the loop
    # seam is a jump like any other and half of what a filler ever loses
    # is there, so the last landing at lift 3 back onto the first at lift
    # 2 is a -1 of ``arc`` 3.6, a reach of 2.92 in a window of 2.35-4.98,
    # and legal level as well, which is what the ``spread`` is for.
    #
    # **No moat anywhere in here.** The filler loops, and the second lap
    # digs away the ground the first lap's pedestals are standing on --
    # 27,859 "pedestal will not stand" refusals on the level that found
    # it. Both of this level's ponds are in beats that play once.
    ("moorings", [n("rock", arc=3.6, lift=4, hug=3.0, spread=2, ceiling=3,
                    orbs=1),
                  n("ground", arc=2.9, lift=4, hug=3.0, kind="walk",
                    ceiling=3, deco="lamp"),
                  n("copper", arc=3.2, lift=4, hug=3.2, pedestal=False,
                    orbs=1)]),
], exit_beats=[
    # THE SLUICE. The gate's own culvert, with the tide forcing water
    # back up it: a block of quay stone to launch from, the column, and a
    # lit curb at the top to stand on before the leap across the chasm.
    #
    # **Three landings against the staircase's six or seven**, and that
    # is the largest lever a level author has: the exit climb was 45% of
    # everything a viewer saw on this level and is 20% now. It is a
    # bubble and not a ladder because a body rides a ladder at 2.35 m/s
    # and a column at 11.0 -- the same five blocks are on screen for a
    # fifth of the time -- and because a climbing body has its face
    # against the thing it is climbing, which is what makes a ladder ride
    # the single biggest visual defect this tower has left.
    #
    # ``pedestal=True`` and ``step_y=4`` are the recipe and both are
    # load-bearing: ``_climb_move`` wants solid rock within one cell of
    # the column at its **middle index** and at its **top**, and out in
    # the lane the only candidate is the landing's own stack. Floated,
    # the column is refused silently -- 11,097 of 13,000 candidates on a
    # *generated* bubble exit -- and the level gets a staircase without
    # being told. **Check the move mix in ``--report`` for the word
    # ``bubble`` by name after touching anything here**; its absence
    # reads as 100% placed.
    #
    # The launch block stands at ``hug=2.8`` and not 2.2, which is
    # measured elsewhere at 69 wall-jammed frames of 1,293 against 0 of
    # 1,280, and ``hug`` on the climb node itself is inert. No
    # ``shell="shaft"``: a tube around an authored climb puts the body
    # inside the wall, and the pedestal anchors without it. A ``cave``
    # over the launch was tried here and produced a world identical to
    # the last landing -- shells are near-noise on a narrow ledge -- so
    # the overhead mass is the ``ceiling`` beam at both ends instead.
    #
    # The arithmetic of the height: launch at lift 1, the column gains
    # four, the curb one -- a walking surface of 7.0 against the next
    # terrace's 6.0, which is this level's ``rise`` of 5 plus the one
    # block ``hop_span(-1)`` comes down on the crossing. A climb that
    # overshoots is the owner's "it puts a ladder there and then jumps
    # back down to a lower part".
    n("ground", arc=2.8, step_y=0, hug=2.8, spread=1, confine=True, ceiling=3),
    n("rock", arc=2.4, step_y=1, kind="bubble", climb_style="water", hug=2.0,
      pedestal=True, pedestal_style="prismarine", spread=0, deco="lamp",
      orbs=2),
    n("glow", arc=3.0, step_y=1, hug=3.2, spread=0, pedestal=False,
      ceiling=3, deco="lamp", orbs=1),
])
