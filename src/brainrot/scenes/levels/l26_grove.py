"""Level 26: THE GROVE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# **A warped fungus grove, run under the caps.** The old version was a
# teal staircase with two orange slabs floating over it and nothing at
# all above head height: 59% of the view was empty sky, the worst figure
# of the roster, and it stood no structure because it named none.
#
# What replaces it is the reference's groove, built out of the biome's
# own parts. Teal nylium underfoot on a broad shelf, warped stems close
# on the core side, orange caps overhead for most of the level, a spring
# cut through the ground, and one great fungus standing where the ledge
# turns with the course going *through* it rather than past it.
#
# The structure is ``greatcap`` and it was ``arch`` first, which is the
# one measurement in this file that could not have been guessed. Both
# are hop gates, both reserve on a ledge, and both get crossed -- the
# arch's crossing landings show up in the segment counts as often as any
# other level's. But a gate is only worth having if the *viewer* sees it,
# and the arch is two three-cell posts under a two-cell lintel: measured
# through the real camera from the approach in, it held 25 degrees for
# 1.4 s, 0.1 s, 0.0 s and 0.0 s on four seeds. The great cap is a
# seven-wide canopy at dy 5-6 and reads as one mass: **1.8 / 1.7 / 0.9 s
# on the same seeds.** Placement rate was identical; silhouette was the
# whole difference. Its red is literal in the blueprint rather than taken
# from the theme, and that is the other reason it stays -- one saturated
# complementary mass against a level committed to teal is the
# reference's own composition, not an accident.
#
# Against PUMPKIN ROWS below it: nine metres of band against twelve, hot
# orange lamplight against cold cyan, a low weaving field against a
# three-block fall and a seven-block climb, and a stair out against a
# spring. Against DUST DEVILS above it: teal against terracotta.
#
# The things that are not free choices:
#
# * **``glow`` is ``sealantern``, not the theme's ``shroomlight``.**
#   ``shroomlight`` is a bright orange texture that emits nothing --
#   ``spiral._GLOWING`` is five names and it is not one of them. The
#   caps stay ``shroomlight`` because they are meant to be lit *by*
#   something; the light itself is the pale cyan sea lantern, which is
#   the other half of a bioluminescent grove and the opposite end of the
#   spectrum from the farm below.
# * **The canopy is ``ceiling`` painted with ``pedestal_style``.** A lid
#   is real cells three above the take-off, refused only if the arc would
#   climb through it, and every hop here rises at most one block. The
#   cells are written as ``pedestal_style or theme.rock``, so naming
#   ``shroomlight`` there is what makes the thing over your head a cap
#   rather than more stem -- and on a floating landing there is no
#   pedestal for that keyword to affect. Half the landings carry one:
#   a lid within eight blocks of the head sends ``_indoor_want`` to 0.85
#   and takes 27% off every tint in the frame, so lidding all of them
#   makes a dark level whatever ``dark`` says.
# * **``hug`` is what stops the frame being sky**, and it is also what
#   keeps the body out of the cliff. Unset, ``_targets`` pulls a ledge
#   course to the outer edge of its own shelf and points the lens over
#   the drop.
# * **The liquid is water, not the theme's lava.** Lava is solid to the
#   no-jump walker, so a lava moat is atmosphere and nothing else; a
#   water moat digs a bowl the walker falls into and cannot climb out of,
#   and this level was sitting exactly on the 55% limit. Water is also
#   the coherent choice here, because the way out of the grove is a
#   bubble column, and a bubble column is a spring.
# * **Soul sand is the slow beat.** It runs at 2.51 m/s against a normal
#   5.61, so a stride across it is a genuinely different tempo rather
#   than a differently-coloured cube -- and a ``walk`` is the only verb
#   this kernel has that can pass under a lid at all.
# * **The bubble column keeps its pedestal and asks for no ``hug``.** A
#   climb anchors on solid rock within one cell of its column at the
#   column's middle index *and* at its top; hugged to a core that leans
#   away it finds nothing, is refused, and falls silently through to a
#   generated staircase with nothing reporting it. The landing's own
#   stack is the anchor. Check ``--report``'s move mix for the word
#   ``bubble``: if it is missing, this is six steps of stairs.
# * **...and no ``shell="shaft"`` around it.** The tube is what the
#   *generated* climb hangs on; an authored column standing on its own
#   pedestal does not need one, and it is expensive to look at. Measured
#   on identical worlds, dropping it took frames mostly filled by a wall
#   from **11.1% to 6.3%** with the bubble still firing on the same
#   share of runs -- it costs seven points of empty frame, which this
#   level has to spare and that figure did not.
# * **A ``walk`` is never a beat's first node** -- it needs its
#   predecessor within half a block and a beat boundary does not promise
#   that -- and there is **no moat in the filler**, because the loop's
#   second lap digs out the first lap's footings.
LEVEL = Level("THE GROVE", "warped", rise=6, gap=3.0, exit="bubble",
              band=12.0, shelf=4.5, breaks=2, landmark="greatcap",
              ground="warpednylium", sub="soulsand", rock="warped",
              accent="shroomlight", liquid="water", glow="sealantern",
              candy=("shroomlight", "warped"),
              props=("netherfungus", "vinehang", "grasstuft", "pebbles"),
              sky=(96, 204, 190), dark=0.16,
              step=("warped", "hop"), beats=[
    # The threshold: a sea lantern set flush in the nylium with the
    # spring dug out around it -- the palette goes from the farm's orange
    # to teal at that one block -- and then up onto the first stem under
    # the first cap.
    ("spores", [n("glow", arc=3.2, lift=1, hug=3.4, spread=0, deco="lamp",
                  moat=True, orbs=1),
                n("rock", arc=3.4, lift=2, hug=3.2, spread=1, ceiling=3,
                  pedestal_style="warped"),
                n("warped", arc=2.9, lift=2, hug=3.2, kind="walk",
                  spread=0)]),
    # The grove itself, and the level's one idea: three landings with a
    # cap over every one of them, the middle one crossed at soul-sand
    # pace, and then the drop off the shelf into the hollow -- three
    # blocks, the reference's own way of losing height, which is to fall
    # off an edge rather than to jump down.
    #
    # The climb and the fall are in one beat because machinery is
    # inserted *between* beats and puts the body back at lift 1; written
    # across a boundary the fall is not a fall.
    ("canopy", [n("accent", arc=3.4, lift=3, hug=3.2, spread=0,
                  pedestal=False, ceiling=5,
                  pedestal_style="shroomlight"),
                n("soulsand", arc=2.9, lift=3, hug=3.2, kind="walk",
                  spread=0, ceiling=3, pedestal_style="shroomlight",
                  orbs=1),
                n("soulsand", arc=2.9, lift=3, hug=3.4, kind="walk",
                  spread=0),
                n("ground", arc=5.4, lift=0, hug=3.4, form="floor",
                  orbs=2),
                n("rock", arc=3.4, lift=1, hug=3.2, spread=1,
                  moat=True)]),
], filler=[
    # The thicket, which is most of what the terrace actually plays: stem,
    # cap, two slow strides under the canopy, and down onto the nylium.
    # The walks are what keep this level's plain-hop share honest -- the
    # exit climb is a third of the landings and only the column itself is
    # not a hop.
    ("thicket", [n("rock", arc=3.4, lift=2, hug=3.0, spread=0, radial=1.3,
                   ceiling=3, pedestal_style="shroomlight", orbs=1),
                 n("accent", arc=3.3, lift=2, hug=3.4, spread=0,
                   radial=-1.3, deco="lamp"),
                 n("soulsand", arc=2.9, lift=2, hug=3.4, kind="walk",
                   spread=0, ceiling=3, pedestal_style="shroomlight"),
                 n("soulsand", arc=2.9, lift=2, hug=3.2, kind="walk",
                   spread=0),
                 n("rock", arc=3.5, lift=1, hug=3.2, spread=1, orbs=1)]),
    # The seep, the loop's other half: up onto a cap, a lit stride along
    # the stem, and a half-height shelf of it. Slabs and stairs are the
    # reference's commonest non-cube form by a wide margin and this tower
    # has almost none; a slab lands at +0.5 and reaches 3.78 where a whole
    # block reaches 3.10.
    ("seep", [n("accent", arc=3.4, lift=2, hug=3.2, spread=0, ceiling=3,
                pedestal_style="shroomlight", orbs=1),
              n("warped", arc=2.9, lift=2, hug=3.2, kind="walk", spread=0,
                deco="lamp"),
              n("rock", arc=3.4, lift=2, hug=3.4, form="slab", spread=0,
                orbs=1)]),
], exit_beats=[
    # Out up a spring in a hollow stem: a lit step in at the foot of it
    # and then six blocks of bubble column inside a shaft. Declared as
    # the level's exit as well as authored, so the climb reserves three
    # landings rather than the staircase's seven -- on a level this
    # length that one line is worth about fifteen points of designed
    # content.
    n("rock", arc=3.0, lift=1, hug=2.2, spread=2, deco="lamp"),
    n("warped", arc=3.0, step_y=6, kind="bubble", spread=0, orbs=2),
])
