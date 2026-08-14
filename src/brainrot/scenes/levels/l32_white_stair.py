"""Level 32: THE WHITE STAIR.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A white court with the sea standing in it.
#
# One sentence: *you come up out of the black shaft onto a lit block of
# quartz, walk through a gilded doorway, climb two piers, and fall three
# blocks off the top of them into a reflecting basin cut out of the
# court's own paving -- and from there the level is a rank of gold-capped
# piers marching along a flooded white pavement to the great arch, and
# the stair the level is named after going up through it.*
#
# The thing a viewer would remember is the arch: two white piers and a
# gold lintel with a lantern hung under each side of it, standing where
# the court ends, with the stair behind it. The course runs *through*
# it, which is the only reason a structure in this tower is ever seen.
#
# ---------------------------------------------------------------------
# **The frozen landmark decided the profile, and the old profile was
# throwing it away.** ``landmark="arch"`` is assigned centrally and this
# level was left on ``profile="channel"`` under it -- which is the one
# combination the roster has a measurement for and it is unambiguous:
# the liquid cut runs exactly where the lane runs, ``Cone.rock`` is
# False under it, and a gated structure's base cells have nothing to
# stand on (``docs/RULES.md`` §7: 1 reservation in 8 runs on a channel
# against 8 in 8 on a ledge). The level paid the whole bill of holding a
# gate and got 1.2 s of structure on screen for it, against a 1.5 s
# rule. Measured here, same seeds, channel against plaza with nothing
# else changed:
#
# | | channel | plaza |
# |---|---|---|
# | structure held at 25 deg, from the approach in | 1.2 s | **4.8 s** |
# | ...at 40 deg | 0.9 s | **3.0 s** |
# | designed content | 54% | **57%** |
# | walker coverage, mean / worst | 39 / 59% | **34 / 45%** |
# | unchecked emergency placements | 0 | 0 |
#
# The walker number is the surprise and it is worth stating why, because
# the intuition is the other way round: a plaza is *more* ground, and
# the thing that stops a walker is not width, it is a **hole**
# (``docs/RULES.md`` §7 -- water is see-through and lava is solid, so
# neither liquid blocks anything; what blocks is the bowl a ``moat``
# digs, which a walker drops into and cannot climb out of). A channel's
# cut is a long shallow trench along the lane and the walker skirts it;
# three radius-three ponds sunk in a wide floor are three barriers it
# has to be *thrown* over, and the lock across the level's break is a
# fourth. So the water in this level went from a decorative rill to the
# reason there is one route through it.
#
# **And the brightest level in the tower was being lit as a cave.** Two
# things did that, both of them one line. ``quartz``'s own sky is
# (228, 232, 244) -- a white court under a white sky is one value from
# the top of the frame to the bottom, which is the owner's "white cubes
# on a pale wash" and is exactly the trap THE CORNICE climbed out of
# three levels down. It is a deep azure now, and the floor is the
# lightest thing in the frame by ninety points of luminance. The other
# was the lids: ``spiral._indoor_want`` returns ``max(theme.dark, 0.85)``
# the moment any cell three to eight over the body is solid, and that
# takes 32% off every tint in the shot -- the old version lidded two
# nodes of every four in a filler that plays three times and put a
# ``hall`` shell in the middle of the level as well. A third of the
# landings carry a beam now and there is no walled interior, which is
# also what the reference measures as: a rock lid overhead on 98% of
# samples and fully enclosed 6% of the way.
#
# **Every beat climbs and then falls off the end of itself.** That shape
# is not decoration, it is the two rules meeting: the owner's "half the
# jumps are at ground level" wants the middle of a beat high, and
# ``docs/RULES.md`` §7's "machinery is inserted between beats and leaves
# the body at lift 1" wants a beat to *end* low, because the lock's own
# approach hops are written at ``arc`` 2.6 and cannot come down four
# blocks. So each beat here goes 1 - 2 - 3 - 4 and then throws the
# height away in one long descent, which is also the only long jump this
# motion model has and the reference's own way of losing altitude: eleven
# blocks travelled to gain four, by falling off edges rather than jumping
# down.
LEVEL = Level("THE WHITE STAIR", "quartz", rise=5, gap=2.8, exit="stair",
              landmark="arch",
              band=13.0, profile="plaza", breaks=2,
              # Six roles, each doing one job. Quartz paving underfoot;
              # calcite for everything built, so the piers, the plinths
              # and the arch's own two columns are a shade off the floor
              # rather than a contrasting jump block; gold at every
              # trim; and deepslate -- (92, 92, 100) against quartz's
              # (228, 226, 218) -- as the paved stripe down the middle
              # and the dark beams overhead. The level has to carry a
              # dark value somewhere or it is a white shape on a pale
              # wash, and the composition rule says where: dark high and
              # light low, which here is the beams and the route.
              ground="quartz", sub="deepslate", rock="calcite",
              accent="gold", glow="lantern", liquid="water",
              props=("lanternpost", "mcfence", "chain", "lilypad",
                     "pebbles"),
              # A court sky, not the theme's own near-white. The ring
              # light is ``mix(white, sky, 0.35 + 0.45 * dark)``, so at
              # 0.10 this is a cool daylight that leaves the near paving
              # at full brightness and puts ninety points of luminance
              # between the floor and the sky behind it.
              sky=(104, 148, 202), dark=0.10,
              step=("calcite", "hop"),
              # Fifteen materials with the dominant one at 19%, which is
              # the shape a real terrace measures as (median 14 kinds,
              # dominant 26%) -- against the two this level used to have.
              # The greys are the ones that had to go: ``andesite``
              # (150, 150, 148) and ``stone`` (146, 146, 150) are one
              # value with two names and neither is white, so a white
              # court paved in them comes back the colour of the cone.
              # What is left is a family of pale stones that differ in
              # *hue* -- quartz warm-white, calcite neutral, diorite
              # cool, plaster cream, chiselled and sandstone sand, iron
              # and glass cold -- with the gold and the two darks as the
              # tail.
              floor=(("quartz", 3), ("calcite", 3), ("diorite", 2),
                     ("plaster", 2), ("chiselled", 2), ("sandstone", 2),
                     ("iron", 2), ("deepslate", 2), ("gold", 1),
                     ("terra_white", 1), ("glass", 1), ("blackstone", 1),
                     ("copper", 1), ("stone", 1)),
              beats=[
    # THE SILL -- the threshold, the doorway, the two piers and the fall
    # into the basin. Six nodes in one beat, because this is the beat
    # that is never truncated (it opens the level and competes with
    # nothing for terrace) and because the rise and the drop have to be
    # in the *same* beat: machinery between beats hands the body back at
    # lift 1, so a fall written as a beat's first node is not a fall.
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
    # 4. And up again onto the second, under a dark beam. Surface 4.0 by
    #    the fourth landing of the level, which is what "get off the
    #    floor" means: 55% of authored landings across this roster sit
    #    at lift 0 or 1.
    # 5. **Three blocks down into the basin, and it is the level's long
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
    # 6. Out of the basin onto a calcite kerb, floating, because a
    #    pedestal cannot stand in the hole the node before it just dug.
    ("sill", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1, deco="lamp",
                orbs=1),
              n("accent", arc=2.9, lift=1, hug=3.0, kind="walk", ceiling=3,
                pedestal_style="gold"),
              n("rock", arc=3.2, step_y=1, hug=3.0, orbs=1),
              n("chiselled", arc=3.2, step_y=1, hug=3.2, ceiling=3,
                pedestal_style="deepslate"),
              n("ground", arc=4.9, lift=0, form="floor", hug=3.6, spread=0,
                moat=True, orbs=2),
              n("rock", arc=3.2, step_y=1, hug=3.4, pedestal=False,
                orbs=1)]),
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
    # 4. Up a whole block onto the tall pier, with a gold baluster on it.
    # 5. **Off the end of the colonnade, two blocks down onto a bar
    #    standing in the water**, floating, with the second of the
    #    level's three ponds cut under the jump. Reach 4.22 against a -2
    #    window of 3.12-5.56. It is the beat's last node for two
    #    reasons: it leaves the body at lift 1 where the machinery that
    #    follows can pick it up, and a ``moat`` blocks the *next*
    #    landing of its own beat, so it can only ever be last.
    ("colonnade", [n("rock", arc=3.4, lift=1, hug=2.8, spread=1, orbs=1),
                   n("ground", arc=2.8, step_y=1, form="slab", kind="walk",
                     hug=2.8, deco="lamp"),
                   n("accent", arc=3.2, step_y=1, hug=3.0, ceiling=5,
                     pedestal_style="gold", orbs=1),
                   n("rock", arc=2.9, step_y=0, hug=3.0, kind="walk",
                     ceiling=5, deco="post"),
                   n("chiselled", arc=3.2, step_y=1, hug=3.2, orbs=1),
                   n("sub", arc=4.9, step_y=-2, hug=3.6, pedestal=False,
                     moat=True, orbs=2)]),
    # THE BASIN -- the flooded half of the court, and the level's most
    # exposed stretch: out over the standing water on a gold bollard and
    # down onto an island of paving with the pool round three sides of
    # it. This is the beat that plays about twice in eight runs, so
    # nothing the level is *about* is in here; what is in here is the
    # widest the course ever stands from the core wall, which is the one
    # place a viewer sees the whole court at once.
    #
    # The stride is a dark one: the deepslate route stripe under a
    # five-cell beam, which is the reference's own answer to ground that
    # could be read two ways -- a carpet runner down the hall, a dirt
    # path across grass. ``ceiling=5`` rather than 3 because a lid is a
    # one-cell beam spread along the direction of travel and five of
    # them roof nearly the whole arc in the one column of the ray fan
    # that looks where you are going.
    ("basin", [n("rock", arc=3.4, lift=1, hug=3.0, spread=1, orbs=1),
               n("sub", arc=2.9, step_y=0, hug=3.0, kind="walk", ceiling=5,
                 pedestal_style="deepslate"),
               n("accent", arc=3.2, step_y=1, hug=3.6, deco="post",
                 pedestal_style="gold", orbs=1),
               n("ground", arc=2.9, step_y=0, hug=3.8, kind="walk",
                 pedestal_style="gold"),
               n("ground", arc=4.9, lift=0, form="floor", hug=4.0, spread=0,
                 moat=True, orbs=2),
               n("rock", arc=3.4, step_y=1, hug=3.6, pedestal=False,
                 orbs=1)]),
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
    ("court", [n("sub", arc=3.4, lift=1, hug=2.8, spread=1, orbs=1),
               n("ground", arc=2.9, step_y=0, hug=2.8, kind="walk",
                 ceiling=3, pedestal_style="gold"),
               n("accent", arc=3.2, step_y=1, hug=3.0, deco="lamp",
                 pedestal_style="gold", orbs=1),
               n("rock", arc=3.4, step_y=-1, hug=3.2, pedestal=False)]),
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
