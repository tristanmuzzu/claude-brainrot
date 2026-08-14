"""Level 25: PUMPKIN ROWS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# PUMPKIN ROWS. **A pumpkin field at the lift, with the mill standing at
# the top of it.** Ploughed ground the whole width of the terrace, the
# fruit lying orange in the drills, the crop stacked on dark crates
# between them, three irrigation cuts flooded across the rows -- and the
# route is the harvest: up the stacks, over the ditches, down into the
# sunken basin at the bottom of the field, and out through the mill's
# own doorway.
#
# One sentence: *you climb the crates in the first four landings, take
# the level's fall off the top of the stack three blocks down into the
# flooded basin, cross it on the fruit, half-step up the stone kerb of
# the leat on two slabs, and leave up a flight of bales against the
# cliff with a lit lantern on the top tread.*
#
# The one thing a viewer would remember is the fall: off the top of a
# black crate stack four blocks over a gold field, out over the water,
# and down three.
#
# ---------------------------------------------------------------------
# **What the last version was, and why the whole thing moved off the
# ledge.** Judged from its own contact sheet rather than from its
# numbers: the palette worked -- gold and orange, unmistakably a harvest
# -- and there was no *place* under it. On a ``ledge`` at ``shelf=4.5``
# every landing's pedestal stood in the void, so four rows of the sheet
# are a forest of identical square columns against grey cliff and bright
# blue sky with no ground, no water and no structure in any frame of the
# level. 54% of the view was empty; the windmill was never once seen on
# screen; and the level had 33 ``form="floor"`` landings, which is 33
# metres of terrace given away to a walker for nothing in return.
#
# Four things follow from that, and they are what this file is:
#
# * **``profile="plaza"``.** The columns were the good part -- a pedestal
#   is a stack of terrain down to the ground, so a landing three blocks
#   up **is** a crate stack -- and a plaza is what puts a floor under
#   them. It is also the *only* profile the frozen landmark can use:
#   ``windmill`` is a ``walk`` gate, and a walk gate wants five supported
#   cells across the corridor, so it is refused on a ledge every time
#   (``docs/RULES.md`` §7: 0-2 reservations of 8 against a hop gate's
#   8 of 8). The mill is the thing this level is named for; it has to be
#   able to stand up.
# * **...and then the floor is broken hard**, which is the half of a
#   plaza that the first tower got wrong. Four floor breaks and three
#   ponds: a ``moat`` is a radius-three bowl cut in the ground, and
#   because farm water is in ``SEE_THROUGH`` the walker drops into the
#   hole and cannot step back out. That mechanism -- the hole, not the
#   liquid -- is the one that moves the walk number, and this level's
#   liquid is water rather than lava precisely so it works. Every pond
#   is under a jump: the fall lands in one, the leat runs through one,
#   the threshold crosses one.
#
#   **And not one of them may name a ``pedestal_style``**, which cost a
#   measured pass here. ``Course._moat`` fills the bowl it digs with
#   ``pedestal_style or theme.liquid``, so a landing written
#   ``moat=True, pedestal_style="darkoak"`` cuts a radius-three hole in
#   the field and fills it with solid, walkable planks -- no error, no
#   rejection, the pond drawn as timber and the unwalkability quietly
#   gone. Two of this level's three ponds shipped that way on the first
#   build. Writing both keywords on one node is a natural thing to do
#   when the plinth under a landing wants a colour; do not.
# * **The floor is written out.** A real leg of the reference uses a
#   median fourteen materials with the dominant one at about a quarter,
#   and identity comes from the ground rather than from the structure.
#   Fourteen here: ploughed earth, the fruit itself, straw, the dry
#   headland, and the clay of the cart track.
# * **The design gets off the floor at the second landing and stays
#   off.** 55% of authored landings across this roster sit at lift 0-1,
#   which is the owner's "half the jumps are at ground level" measured.
#   Nothing here is a ``form="floor"`` landing at all, and after the
#   threshold the route runs at lift 2-4 until the fall puts it back on
#   the ground for one landing in the basin.
#
# **How it differs from WINDMILL REACH, which is the other farm level
# and twenty-three below.** That one is *the mill*: a ledge, a leat, a
# sack ladder up the roundhouse, a wheel pit, a rick -- the building and
# its working order, seen from inside. This one is *the field*: an open
# plaza, no masonry in it anywhere, the mill at the far end of the rows
# as the doorway you leave through, and the harvest itself for its
# furniture. Straw-gold there against orange here; a ladder climbed
# there against a three-block fall here; a narrow shelf there against
# the widest floor either of them stands on.
#
# ---------------------------------------------------------------------
# Four constraints, all arithmetic, all of them costing a pass somewhere
# in this roster:
#
# **``magma`` is the jack-o-lantern.** ``spiral._GLOWING`` is five names
# -- lantern, torch, glowstone, sealantern, magma -- and nothing else
# lights its own cell. ``pumpkin`` and ``shroomlight`` are bright
# *textures* that emit nothing. Of the five only ``magma`` is warm
# orange (214, 118, 52), a shade darker than the unlit ``pumpkin``
# (218, 126, 34) beside it, so every lit fruit in this level is magma
# and the two read as the same crop with a candle in one of them.
#
# **The exit is a stair and not a ladder, and that is not a
# preference.** Measured by bucketing every jammed frame by segment
# *and* move over four seeds: an ``ascent/climb`` ride is 20.9% jammed
# against 0.0% for every other move in the same level, because the wall
# a ladder hangs on *is* the wall in the lens and ``hug`` on a climb
# node is inert. A bubble is the other good answer and this level does
# not get it either: THE ARCHIVE directly below already leaves by a
# column of water, and two consecutive levels ending on the same move is
# the complaint this pass exists to fix.
#
# **Machinery is inserted between beats and hands the body back at lift
# 1.** So the climb and the fall are in the *same* beat: a drop written
# across a beat boundary is a drop off nothing about half the time. That
# beat is also the one that opens the level, so it is never truncated
# and never competes for terrace.
#
# **A ``ceiling`` lid is the cheapest overhead mass there is and it is
# not free.** The cells are real and the lens probe counts them, but a
# lid within eight blocks of the head makes ``_indoor_want`` return
# 0.85, which takes 27% off every tint in the frame. So about half the
# landings are lidded, and the ones in the body of the level carry
# ``pedestal_style`` dark timber (the exit is the other way round, and
# why is at the bottom of this file): ``pedestal_style`` paints the lid
# as well as the plinth,
# so a crate stack and the crop frame over it come out the same dark
# brown against the gold, which is the reference's own value structure
# -- the coloured ground at the bottom, the dark brow across the top.
LEVEL = Level("PUMPKIN ROWS", "farm", rise=4, gap=2.8, exit="stair",
              band=10.5, profile="plaza", breaks=4, landmark="windmill",
              # Ploughed earth underfoot, straw for everything built,
              # the fruit for the accent and a candle in one fruit in
              # ten. ``water`` is the leat, and it is the only liquid
              # in the engine that digs a hole a walker cannot climb
              # out of.
              ground="farmland", sub="coarse", rock="hay",
              accent="pumpkin", glow="magma", liquid="water",
              candy=("pumpkin", "hay"),
              props=("crop", "mcfence", "scarecrow", "lanternpost",
                     "sugarcane", "grasstuft"),
              # A warm low sun rather than the lilac dusk this used to
              # ask for. A level cannot be at night -- the sky dome is
              # built once per *run* from the run's palette, so a
              # level's ``sky`` and ``dark`` own only ``ring_light``,
              # the light everything here is lit *by*, and the fog it
              # is mixed into. Amber at 0.3 is a field an hour before
              # the end of the day with whatever sky the run drew still
              # over it, which is the reference's own composition. Past
              # about 0.45 the lids take over and the sheet goes black.
              sky=(214, 156, 104), dark=0.3,
              # Only the *fallback* footing: the way out is written
              # landing by landing below and the generated stair never
              # runs. Pumpkin rather than WINDMILL REACH's hay, because
              # ``test_every_level_climbs_out_on_its_own_footing``
              # counts distinct footings across all thirty-three.
              step=("pumpkin", "hop"),
              # Fourteen kinds with the dominant at 16%, which is the
              # shape a real terrace measures as (median 14, dominant
              # 26%) and the single biggest reason its levels read as
              # places. The last version named five and the sheet was
              # gold cubes over open sea.
              floor=(("farmland", 4), ("pumpkin", 3), ("hay", 3),
                     ("coarse", 2), ("podzol", 2), ("dirt", 2),
                     ("grass", 2), ("gravel", 1), ("terra_orange", 1),
                     ("oak", 1), ("log", 1), ("moss", 1), ("clay", 1),
                     ("stone", 1)),
              beats=[
    # THE HEADLAND. The whole level in one beat: the threshold, the
    # crates, and the fall. It opens the level, so it is the one beat
    # that never competes with anything for terrace and is never
    # truncated -- which is why the three blocks of height that the fall
    # spends are climbed four nodes earlier in the same list rather than
    # in the beat before.
    #
    # 1. **A lit jack-o-lantern set flush in the ploughed headland**,
    #    with the crop frame three cells over it. The reference's way of
    #    saying a level begins: an emissive block on a rise, on screen
    #    two seconds before it is reached, and the palette changing
    #    completely at it with no blend. Below is THE ARCHIVE -- pale
    #    plaster flags, black oak cases and a red runner; from here it
    #    is ploughed brown, straw gold and orange. ``lift=1`` and not 2:
    #    a beat's opener is placed from wherever machinery left the
    #    body, and the identical beat measures two thirds of the
    #    placement one block higher.
    # 2. **Up onto the end of the first crate stack, and that is the
    #    second landing of the level.** From here to the basin nothing
    #    touches the ground. ``+1`` at ``arc`` 3.0 is a reach of 2.32
    #    against a window of 2.00-3.10 -- centred rather than at the top
    #    of it, because a ``+1`` written at 3.6 is a reach of 2.92 and
    #    is the arc that has to fall back, and a fallback is not
    #    ``exact``.
    # 3. **Along the top of the stack on foot, under the crop frame.** A
    #    walk is the genre's ``2bc`` -- the lid you sprint under -- and
    #    the only honest form of it this kernel has: one impulse always
    #    rises 1.25 m and the head then sweeps the two cells above every
    #    take-off, so a lintel low enough to read as one refuses any arc
    #    beneath it. 2.9 of arc is 2.22 m of ground against a walk's
    #    2.4 m limit. It is the beat's *second* verb node and not its
    #    last: a beat lays about half its nodes and a non-hop written at
    #    the tail is written and never seen.
    # 4. **Over the first flooded cut onto a lit fruit**, ``+1`` again.
    #    The ``moat`` is here and not later because the pond has to be
    #    *under* the jump rather than beside it, and this is the last
    #    jump before the level leaves the floor for good.
    # 5. **The top of the stack, four blocks over the field.** It
    #    floats: the moat one node back has just cut a radius-three bowl
    #    about three metres upstream and a stack of terrain cannot stand
    #    in a hole. That one keyword is 27,859 "pedestal will not stand"
    #    refusals elsewhere in this roster.
    # 6. **Off the top and three blocks down into the basin.**
    #    ``step_y=-3`` at ``arc`` 5.2: a reach of 4.52 against a -3
    #    window of 3.72-6.05, and all three arcs placement may try
    #    (5.2, 5.93, 6.66) are inside it. The longest jump in the level
    #    and the only kind of long jump this motion model has -- falling
    #    takes time and the body does not slow down while it does.
    #    Written on ``step_y`` rather than on ``lift`` so that it is
    #    three blocks below *the stack the body actually reached*. The
    #    second pond is under it.
    # 7. **Out of the basin onto the fruit standing in the water.**
    #    Floating again, for the moat one node back.
    ("headland", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, ceiling=3,
                    pedestal_style="darkoak", deco="lamp", orbs=1),
                  n("rock", arc=3.0, step_y=1, hug=3.2, ceiling=3,
                    pedestal_style="darkoak"),
                  n("oak", arc=2.9, step_y=0, hug=3.2, kind="walk",
                    ceiling=3),
                  n("accent", arc=3.0, step_y=1, hug=3.4, moat=True,
                    orbs=1),
                  n("rock", arc=3.0, step_y=1, hug=3.6, pedestal=False,
                    ceiling=3, pedestal_style="darkoak", orbs=1),
                  n("ground", arc=5.2, step_y=-3, hug=4.0, pedestal=False,
                    moat=True, orbs=2),
                  n("accent", arc=3.2, step_y=1, hug=3.6, pedestal=False,
                    orbs=1)]),
    # THE LEAT. The second beat, which is where a beat is still laid
    # whole, and the one idea in this level that nothing else in the
    # tower does: **the stone kerb of the irrigation channel, climbed on
    # two half-steps.**
    #
    # ``form="slab"`` stands half a block down in its own cell, so a
    # slab written at ``step_y=1`` is a **+0.5** rise and the block
    # after it at ``step_y=0`` is another. Two of them gain a whole
    # block across six and a half metres of ground where one hop can
    # only manage 3.10 m -- which is the one place the real map beats
    # this envelope and the sanctioned way round it. It also reads as
    # deliberate architecture rather than as a fudge: a kerb is a
    # half-height ledge, and stairs and slabs are the commonest non-cube
    # form in the reference by a wide margin.
    #
    # It opens at ``lift=2`` with ``spread=1``, which is free following
    # the beat above and costs a fallback following machinery -- and
    # everything after the opener is on ``step_y``, so a beat that
    # started a block low still has the shape it was written with.
    #
    # It ends **downhill**: off the far kerb, down one and 3.6 out onto
    # a plank laid across the ditch, with the crop store's roof closing
    # over it. A level descends somewhere -- 36 of the real map's 43
    # legs do, and 22 dip below their own start -- and the descent
    # belongs in the first two thirds, which both of this level's are.
    # The ``shell`` is on the beat's **last** node, the only place a
    # shell may go: it is painted the moment its landing commits and its
    # roof then refuses the next arc of the same beat.
    ("leat", [n("rock", arc=3.4, lift=2, hug=3.0, spread=1, ceiling=3,
                pedestal_style="darkoak", orbs=1),
              n("gravel", arc=3.0, step_y=1, form="slab", hug=3.4,
                radial=1.2, pedestal_style="stone"),
              n("accent", arc=3.2, step_y=0, hug=2.9, radial=-1.2,
                moat=True, orbs=1),
              n("oak", arc=3.6, step_y=-1, hug=3.8, pedestal=False,
                shell="cave", orbs=2)]),
    # THE FAR ROWS. Short, and its point in its first node, because a
    # beat is truncated in the *middle* once the terrace budget runs
    # out: whatever a third beat is about has to be said immediately or
    # it is not about anything.
    #
    # It is the one place the course goes right out over the rim -- a
    # lit fruit at ``hug`` 3.9 on the last drill before the ground ends,
    # standing on nothing, with the drop under it and the sky behind it.
    # Silhouettes against sky are legible and anything against the cliff
    # is not, and this is the level's turn signal.
    ("farrows", [n("glow", arc=3.4, lift=2, hug=3.9, spread=1,
                   pedestal=False, deco="lamp", orbs=1),
                 n("rock", arc=2.9, step_y=0, kind="walk", hug=3.9,
                   pedestal=False, ceiling=3, shell="tunnel")]),
], filler=[
    # THE DRILLS, and this is what the level mostly *is*: a level lays
    # nine to twelve landings, the script is four or five of them, and
    # the filler comes round every time where a script's tail does not.
    #
    # One lap is one row of the field. A bale at the head of the drill;
    # a stride along the row on foot with a candle in the fruit under
    # the feet; up onto the next fruit, weaving a metre out across the
    # corridor; and off the end of the row, down one, back in against
    # the cliff onto a cart board. It neither climbs nor sinks across a
    # lap -- the exit column is sized by what the body still has to
    # climb when it starts, so a filler that drifted downhill would buy
    # a longer staircase every time round.
    #
    # The **lit** landing is the middle one and it keeps its pedestal,
    # so every lap plants a magma-cored lamp standing two blocks out of
    # a gold field. A column is free, it is over head height where this
    # format is otherwise all sky, and it is the cheapest colour in the
    # file.
    #
    # **No ``moat`` anywhere in here.** The filler loops, and the second
    # lap digs away the ground the first lap's pedestals are standing
    # on. This level's three ponds are all in beats that play once.
    #
    # The seam where the loop closes is a jump like any other and half
    # of what a filler ever loses is there: it is level, off the cart
    # board back onto a bale at ``arc`` 3.2, a reach of 2.52 against a
    # window that runs to 4.26.
    ("drills", [n("rock", arc=3.2, lift=2, hug=2.9, spread=1, ceiling=3,
                  pedestal_style="darkoak", orbs=1),
                n("glow", arc=2.9, step_y=0, kind="walk", hug=3.1,
                  ceiling=3, deco="lamp"),
                n("accent", arc=3.2, step_y=1, hug=3.7, radial=1.0,
                  pedestal=False, orbs=1),
                n("oak", arc=3.6, step_y=-1, hug=3.0, radial=-1.0,
                  pedestal=False, orbs=1)]),
], exit_beats=[
    # THE STACK. Six landings up a flight of bales built against the
    # cliff at the head of the field, written out rather than left to
    # the generated staircase -- which is the same landings unlit,
    # unlidded and hung in the corridor, and the exit is the emptiest
    # third of every level in this tower.
    #
    # The arithmetic of the height. The foot is at lift 1, so its
    # walking surface is 2.0; the stride holds it there; four treads
    # gain four; the top is 6.0 against the next terrace's 5.0, and the
    # crossing descends one -- which is exactly this level's ``rise`` of
    # 4. A stair that overshoots is a level above that opens by dropping
    # back onto its own terrace, which is the owner's "it puts a ladder
    # there and then jumps back down to a lower part".
    #
    # Every tread is a block up and 2.9 along: a reach of 2.22, and both
    # fallbacks (2.63 and 3.03) are inside the 2.00-3.10 a one-block
    # rise allows, so no tread of this flight can be refused for
    # distance at any of the three arcs placement tries.
    #
    # **The foot stands at ``hug=3.0`` and not at 2.4**, and that one
    # number is most of a level's jammed lens: measured elsewhere, 69
    # wall-jammed frames of 1,293 with the launch landing at 2.2 against
    # **0 of 1,280** at 2.8. On a plaza the core face is a wall like any
    # other and a body hugging it has it inside the probe's three-metre
    # threshold across half the ray fan.
    #
    # It begins with a threshold of its own -- a lit landing and then a
    # stride on foot under the frame before the first tread. That is a
    # landing spent on a verb rather than on height, and it is bought
    # back twice: a lidded walk fills the one column of the ray fan that
    # looks where you are going, and a staircase can only ever be hops.
    #
    # The ``hug`` weaves 3.0 - 3.2 - 2.8 - 3.4 - 4.0 so the flight winds
    # up the face of the stack instead of being a straight column of
    # identical hops, which is the single most monotonous thing this
    # format produces and is a third of what a viewer sees.
    # **The flight is gold and only its foot is dark**, which is the one
    # thing on the first contact sheet of this rebuild that was plainly
    # wrong: the body of the level came out exactly as intended -- orange
    # crates on warm ploughed ground, timber frames across the top of the
    # frame, blue cuts through it -- and then the last eight frames were
    # a brown staircase against a grey cliff. Value contrast is decided
    # by what is *behind* a thing. On the field the crates are the dark
    # mass against a bright floor and carry ``pedestal_style="darkoak"``;
    # the exit stands against the cone's own weathered rock, so its
    # treads are straw and fruit and read as a rick being built up the
    # cliff. Two of the four treads also lost their ``ceiling``: a lid
    # within eight blocks of the head makes ``_indoor_want`` return 0.85
    # and takes 27% off every tint in the frame, and this level had
    # already bought its overhead mass twice over on the way in.
    #
    # ``confine=True`` keeps the treads on the level's own ground; only
    # the last lip hangs, and it is thrown **out** at 4.0 and lit,
    # because the camera locks onto the landing through take-off and
    # flight -- a lip tucked against the core aims the last second of
    # the level at the cliff, and a lip over the drop aims it at sky
    # with the next level standing in it.
    n("glow", arc=3.2, lift=1, hug=3.0, spread=1, ceiling=3,
      pedestal_style="darkoak", deco="lamp", orbs=1),
    n("oak", arc=2.9, step_y=0, kind="walk", hug=3.0, spread=0,
      confine=True, ceiling=3),
    n("rock", arc=2.9, step_y=1, hug=3.2, spread=0, confine=True,
      ceiling=3, pedestal_style="hay"),
    n("accent", arc=2.9, step_y=1, hug=2.8, spread=0, confine=True,
      pedestal_style="pumpkin", orbs=1),
    n("rock", arc=2.9, step_y=1, hug=3.4, spread=0, confine=True,
      pedestal_style="hay"),
    n("glow", arc=3.0, step_y=1, hug=4.0, spread=0, pedestal=False,
      deco="lamp", orbs=2),
])
