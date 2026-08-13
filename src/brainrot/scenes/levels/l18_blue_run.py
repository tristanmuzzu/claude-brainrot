"""Level 18: BLUE RUN.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A glacier's edge, and the fastest level in the tower. A blue ice
# bench taken at ten metres a second under the ice arch, and then the
# floor opens: two blocks down into the crevasse, onto the moss, thrown
# two blocks straight back out, and along a roofed shear face with a
# lid over the way in. Then floes for as long as the terrace lasts --
# a bench up, a step down to the meltwater, and a slab of frost with
# the glacier over your head -- and the way out is ice too: the exit is
# authored as blue ice treads taken on *slides*, which reach further
# than a hop for the same rise and are the reason this level's move mix
# is not a column of plain jumps.
#
# The old version of this level was pale ice against a pale sky over a
# pale sea and sixty per cent of every frame was empty. What moved that
# was not the parkour: terrain under the body (the floating pans are
# gone, and every landing but the pad stands on something), landings
# inboard of the shelf edge, and two roofed beats. Committing the
# ground to blue and the rim's cut face to dark stone did the rest.
#
# The measured things, all of which apply to any level in this tower:
#
# * **A level lays nine or ten landings and only a handful are yours.**
#   Script short, character in the filler; the tail of a long script is
#   never seen.
# * **``breaks=0``, so there is no lock** eating a landing. The shelf's
#   own wobble, the crevasse and the moats hold the walker to 27%.
# * **Authored nodes are not ramped** (``handplan._resolve``), so
#   ``arc`` is the real distance: 4.0 up one on ice, 5.4 level on ice,
#   5.7 for the fall into the crevasse.
# * **The bounce needs a three-block fall** -- see l17_weir, where it
#   was measured. Two blocks gives vy0 = 10.4 against the 10.58 that
#   +2 needs, and the pad silently becomes a hop.
# * **A shell belongs on the landing *after* the move you want roofed,**
#   not on the move's own landing: ``_shell`` wraps the arc that arrived
#   and its roof then refuses the arc that leaves. The crevasse's cave
#   is on the two landings after the bounce for that reason.
#
# Against THE WEIR below (green-grey wet masonry, full-band channel,
# water, waded and bounced) this is blue ice on a narrow shelf, taken at
# slide speed, half of it enclosed.
LEVEL = Level("BLUE RUN", "ice", rise=4, gap=3.2, exit="stair",
              band=9.0, shelf=5.0, breaks=0, landmark="arch",
              ground="packedice", sub="deepslate", rock="blueice",
              accent="frost", glow="sealantern", liquid="water",
              props=("pebbles", "mcfence", "lanternpost"),
              step=("blueice", "slide"), beats=[
    # The threshold: a sea lantern set in the ice on a rise, then a
    # shelf of frost with the glacier's own lid over the jump.
    ("brink", [n("sealantern", arc=3.6, lift=1, spread=1, hug=3.0,
                 deco="lamp", orbs=1),
               n("frost", arc=3.6, lift=2, spread=0, hug=3.0)]),
    # The showpiece, second, because a level lays nine or ten landings
    # and a beat any later than this is never reached -- measured, the
    # same three nodes as beat three fired the bounce 0 times in 8 runs
    # and as beat two fire it 6 of 6. One bench up on the ice, then the
    # floor opens: two blocks down onto the moss and bounced two blocks
    # back out. Rise and drop in the same beat -- machinery is
    # inserted *between* beats and leaves the body back at lift 1, so a
    # beat that assumes the height the last one climbed to drops nothing
    # about half the time and the bounce quietly becomes a hop.
    ("crevasse", [n("blueice", arc=4.0, lift=3, kind="slide", form="ice",
                    spread=1, hug=3.0, orbs=1),
                  n("slime", arc=5.2, lift=1, form="slime", spread=0,
                    hug=3.0, pedestal=False),
                  n("blueice", arc=4.0, lift=3, kind="bounce", spread=1,
                    hug=3.0, orbs=2)]),
    # The shear face: roofed, with a lid over the way in and a long
    # slide out of it.
    ("shear", [n("packedice", arc=3.9, lift=3, spread=0, hug=3.4,
                 shell="cave", ceiling=2),
               n("blueice", arc=5.4, lift=3, kind="slide", form="ice",
                 spread=0, hug=3.4, shell="cave", orbs=1)]),
], filler=[
    # Floes: one bench up on the ice, one step back down to the
    # meltwater. The level's character rather than its surprise, and it
    # descends.
    ("floe", [n("blueice", arc=4.2, lift=2, kind="slide", form="ice",
                spread=1, hug=3.4, orbs=1),
              n("packedice", arc=4.4, lift=1, spread=0, hug=3.4,
                moat=True),
              n("frost", arc=3.9, lift=1, spread=0, hug=3.0,
                ceiling=2)]),
], exit_beats=[
    # Blue ice treads against the cliff, taken on slides. Authored
    # because the climb is the biggest single consumer of a level's
    # landings, and because a slide gains its block across 4.36 m where
    # a hop stops at 3.10 -- so the way out of the ice level is still
    # the ice level.
    n("blueice", arc=3.8, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, confine=True, deco="lamp"),
    n("blueice", arc=3.8, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, radial=0.9),
    n("blueice", arc=3.8, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, radial=-0.9, orbs=1),
    n("blueice", arc=3.8, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, radial=0.9),
    n("blueice", arc=3.8, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, radial=-0.9, orbs=1),
    n("blueice", arc=3.8, step_y=1, kind="slide", form="ice", hug=2.4,
      spread=0, radial=0.9),
    n("frost", arc=3.8, step_y=1, kind="slide", form="ice", hug=2.6,
      spread=0, deco="lamp"),
])
