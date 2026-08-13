"""Level 30: WART FIELDS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A crimson fungus forest: ranks of nether wart farmed between the
# stems, a lava cut running through them, and the way out is a ladder
# up a hollow stem.
#
# What was already right here is kept. The old version placed 100% of
# what it wrote -- the healthiest fidelity in the back third of the
# tower -- because every gap is short and every landing is on the
# terrace's own ground at a sane hug, and none of that changes. What it
# had none of was a *place*: no light anywhere, no liquid on a level
# whose theme's liquid is lava (26 of the real map's 43 legs use lava),
# nothing overhead, no structure, and a profile that climbed from its
# first landing to its last without ever going down.
#
# So the same shape gains four things, in the order they are worth:
#
# * **The canopy.** ``greatcap`` is a hop gate, and a hop gate reserves 8
#   of 8 on a ledge where the walk gates reserve 0-2 (``docs/RULES.md``
#   §7). Its cap spans the corridor five blocks up and the course is
#   steered under it, which is both the thing you would name the place
#   after and a lid in the top of the frame -- and half of every frame
#   in this tower is sky.
# * **Lava.** Two dug cuts, the first of them at the threshold with a
#   shroomlight standing in it. A lava moat buys atmosphere rather than
#   walkability -- lava is solid to the no-jump walker, so what stops a
#   walker is the hole, not what is in it -- and this level keeps its
#   floor breaks for that job. THE CORNICE below runs on one break,
#   because water moats dig a bowl a walker cannot climb out of; do the
#   same here and coverage goes from 51% to **88%**, which is the whole
#   complaint this tower keeps failing on. Three and not two, which is
#   not a fidelity decision either: at two, seed 3 puts the body inside
#   the world on three frames of 630 and at three it is clean.
# * **A descent, in the first half.** Two blocks off the top of a stem
#   into the hollow underneath it, by falling off an edge rather than
#   jumping down. The real map travels eleven blocks vertically to gain
#   four; this level used to be a monotonic staircase.
# * **A ladder that actually fires.** The level's exit has always said
#   ladder and it has always got a staircase: the generated climb writes
#   its column at ``hug=2.0, pedestal=False`` and a ladder needs solid
#   rock beside it at its middle cell and at its top, which the cone's
#   lean never reaches -- one anchored column in 1,559 candidates. An
#   authored climb keeps its **pedestal**, which gives the column
#   something to hang on for its whole height. Check the move mix in
#   ``--report`` for the word ``climb``: if it is missing this beat is
#   six steps of staircase and nothing says so.
#
# This is one of the six climb exits in the last thirteen levels and it
# is one on purpose -- a six-second ladder up a dark shaft is the one
# special block the reference leans on, and a fungus stem is the reason
# this level has a shaft to climb.
#
# Against THE CORNICE below (a narrow snow-and-timber gallery, band 8.5,
# white on dark) and ECHO SHAFT above (a black sculk plaza at band 8.0)
# this is a broad red field under a canopy: different band, different
# enclosure, different light, and the loudest hue in the tower.
LEVEL = Level("WART FIELDS", "crimson", rise=6, gap=3.0, exit="ladder",
              band=10.0, shelf=4.0, breaks=3, landmark="greatcap",
              ground="crimsonnylium", sub="netherrack", rock="crimson",
              accent="wartblock", glow="shroomlight", liquid="lava",
              props=("netherfungus", "vinehang", "pebbles"),
              step=("crimson", "hop"), beats=[
    # The threshold: one shroomlight flush in the nylium on a rise with
    # the lava cut out round it, then a stride in under the first cap.
    # Snow and pale timber below, and this is where it stops -- the
    # palette changes completely at that block and no two adjacent
    # levels share a hue.
    #
    # The lid rides the *walk*: three cells up is refused over any arc
    # that climbs, because one impulse always lifts the head through
    # them, and a walk has no arc at all.
    ("threshold", [n("glow", arc=3.4, lift=1, hug=3.0, spread=2,
                     deco="lamp", moat=True, orbs=1),
                   n("accent", arc=2.9, lift=1, hug=3.0, kind="walk",
                     spread=0, ceiling=3, orbs=1)]),
    # The fields themselves, and the second beat because a second beat
    # is still laid whole: a stride along the first rank on foot and then
    # wart weaving up between the stems.
    #
    # The walk is the *second* node and not the last. A walk is never
    # first in a beat -- it needs its predecessor within half a block and
    # a beat boundary does not promise that -- but everything past the
    # second or third landing of a beat is routinely clipped, so a verb
    # written at the tail of a beat is a verb that mostly does not
    # happen: moving this one from fourth to second took the level from
    # 86% plain hop to 83%.
    #
    # Short gaps, 2.9 to 3.3 m of arc, which is the real map's own modal
    # jump -- and short gaps are what buy a level enough landings to
    # outnumber the machinery inserted between its beats.
    ("fields", [n("accent", arc=3.2, lift=1, hug=3.2, spread=0),
                n("accent", arc=2.9, lift=1, hug=3.2, kind="walk",
                  spread=0, ceiling=3),
                n("accent", arc=3.2, lift=2, hug=3.0, spread=0,
                  radial=1.2),
                n("rock", arc=3.3, lift=3, hug=3.2, spread=1,
                  radial=-1.2, orbs=1)]),
    # The hollow: two blocks off the top of the stem onto the nylium,
    # and then up into the bay rotted out under the cap with lava
    # standing in it. The fall is the level's descent and it is in its
    # first half, where the reference puts one -- the exit is the
    # highest thing here and nothing after it goes down.
    #
    # It lands on a *block* and not on ``form="floor"``. A floor landing
    # places nothing and needs the terrace to be solid under it already,
    # and on a level with floor breaks the cell it wants is sometimes a
    # hole: written that way this beat lost its first node in one run of
    # seven and took the rest of the beat with it. 4.2 m of arc is a
    # reach of 3.52 -- a -2 against a window of 3.12-5.56 and a level
    # jump against 2.00-4.26, so it is legal whichever height the
    # machinery between beats left the body at.
    ("hollow", [n("ground", arc=4.2, lift=1, hug=3.2, spread=1,
                  ceiling=3, orbs=1),
                n("accent", arc=3.2, lift=2, hug=3.0, spread=1,
                  moat=True, orbs=1)]),
    # The showpiece, a little past halfway: single wart blocks standing
    # out of the lava with the caps pressed low over them, the last of
    # them ducked under on foot.
    ("canes", [n("accent", arc=3.4, lift=2, hug=3.2, spread=0),
               n("glow", arc=2.9, lift=2, hug=3.0, kind="walk",
                 spread=0, ceiling=3, orbs=1)]),
], filler=[
    # The level's voice, repeated for as long as the terrace lasts: a
    # rank of wart, a stride under a cap on foot, off the end of the row
    # onto the nylium, and back up. No moat in here -- a filler loops,
    # and the second lap digs away the ground the first lap's pedestals
    # stand on.
    ("rows", [n("accent", arc=3.2, lift=2, hug=3.2, spread=1, orbs=1),
              n("rock", arc=2.9, lift=2, hug=3.2, kind="walk", spread=0,
                ceiling=3),
              n("ground", arc=4.4, lift=0, form="floor", hug=3.4,
                spread=0, orbs=1),
              n("accent", arc=3.2, lift=1, hug=3.2, spread=1)]),
], exit_beats=[
    # Out up a ladder inside a hollow stem, lit at its foot. Declared as
    # the way out landing by landing so the climb reserve is two rungs
    # rather than the staircase's seven, and so the ladder is a ladder:
    # it keeps its **pedestal**, which is the whole difference between a
    # column with something to hang on and a silent flight of stairs.
    #
    # Two things about it that only the frames and the probe say. It
    # works -- ``climb`` is in the move mix and the contact sheet shows
    # rungs -- and it costs about two seconds with the ladder against the
    # lens, which is most of this level's 19% of frames "jammed by a
    # wall". That is what climbing a ladder in first person looks like
    # and ECHO SHAFT above does the same. And **do not shorten it into a
    # stair plus a four-block climb**: measured, that took the level from
    # 0 unchecked placements to 1 and from 0 frames with the body inside
    # the world to 4, for three points of lens. One column of six is the
    # cheap shape.
    n("rock", arc=3.0, lift=1, hug=2.4, spread=2, deco="lamp"),
    n("crimson", arc=2.6, step_y=6, kind="climb", climb_style="ladder",
      spread=0, shell="shaft", orbs=2),
])
