"""Level 9: GLACIER SHELF.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A crevasse in a blue glacier.
#
# The old version was pale ice cubes against a pale sky with nothing over
# the body and nothing to stand under: 58% of the frame was empty and its
# structure was on screen for zero seconds. Three things answer that and
# they are all geometry rather than decoration -- the corridor is narrow
# enough that the cliff is always a few metres off the shoulder, five
# beats carry a checked lid or a cave roof so the top of the frame is rock
# rather than sky, and an ice arch stands across the lane with its lintel
# passing overhead.
#
# The palette commits to *blue*, and to value contrast, which is the half
# that was missed the first time round. A blue-ice terrace under pale
# snow landings is one value: every frame came back the same wash of pale
# blue on a pale sky. So the terrace is snow -- the lightest thing in the
# lower half of the frame, which is how the reference builds every shot --
# and everything *built* on it is blue ice, with the dark cliff filling
# the top and one warm lantern at the threshold doing the only job light
# does here.
#
# The shape: a lit sill walked under an ice lintel, three slides up the
# seracs, then the split -- a three-block fall onto a slab caught in the
# meltwater, which throws the body straight back out of the hole -- then
# stepping stones through a melt cave and floes calving off the rim. It
# descends three blocks in the middle of a level that gains four, which is
# the reference's ratio and the thing every level in this tower lacked.
#
# Jumps are written at 3.0-3.4 m, which is the real map's own modal jump,
# and the one that runs to 4.6 is the fall into the crevasse. Short jumps
# are not only more faithful; they are what buys a designed level enough
# landings to outnumber the machinery inserted between its beats.
LEVEL = Level("GLACIER SHELF", "ice", rise=5, gap=3.2, exit="stair",
              band=11.5, shelf=5.0, breaks=0, landmark="arch",
              ground="snow", sub="packedice", rock="blueice",
              accent="calcite", liquid="water", glow="lantern",
              candy=("blueice", "packedice"),
              props=("pebbles", "lanternpost", "mcfence"),
              sky=(150, 188, 228),
              step=("packedice", "slide"), beats=[
    # The threshold: one lantern block flush in the floor on a rise, then a
    # doorway *walked* through under a checked lid. A lintel is never
    # jumped -- one impulse always rises 1.25 m, so the head sweeps the two
    # cells above every take-off and an arc under a low beam is refused.
    ("sill", [n("glow", arc=3.0, lift=1, spread=0, deco="lamp", orbs=1),
              n("frost", arc=2.9, lift=1, kind="walk", spread=0,
                ceiling=3)]),
    # Up the seracs on ice. Ice is a speciality -- three levels of
    # forty-three on the real map -- and this is the level that gets to
    # spend it: a slide reaches 4.36 m gaining a block where a hop reaches
    # 3.10, so the climb reads long instead of stepped.
    ("seracs", [n("packedice", arc=3.4, lift=2, kind="slide", form="ice",
                  spread=0, orbs=1),
                n("packedice", arc=3.2, lift=2, kind="slide", form="ice",
                  spread=0, ceiling=2),
                n("blueice", arc=3.4, lift=3, kind="slide", form="ice",
                  spread=0, radial=-0.9, orbs=1)]),
    # The showpiece, a little past halfway: the crevasse. A two-block fall
    # onto the one slab caught in the bottom of the split, standing in its
    # own meltwater, and the slab throws the body back out. The drop is
    # what makes the bounce work at all -- a pad only ever returns the fall
    # that fed it.
    ("crevasse", [n("slime", arc=4.6, lift=1, form="slime", spread=0,
                    moat=True, orbs=2),
                  n("blueice", arc=3.6, lift=3, kind="bounce", spread=1,
                    orbs=3)]),
    # Down again, through the melt cave: two stones in the water with a
    # rough roof over them, and one slide out into the light.
    ("melt", [n("calcite", arc=3.1, lift=2, spread=0, moat=True,
                shell="cave", orbs=1),
              n("frost", arc=3.0, lift=2, spread=0, moat=True,
                shell="cave"),
              n("blueice", arc=3.2, lift=2, kind="slide", form="ice",
                spread=0, ceiling=2, orbs=1)]),
    # Calving: two pans of ice with nothing under them, weaving out over
    # the drop. The exit is announced by the ledge running out.
    ("calving", [n("blueice", arc=3.2, lift=2, kind="slide", form="ice",
                   spread=0, radial=1.4, pedestal=False, orbs=1),
                 n("packedice", arc=4.0, lift=1, kind="slide", form="ice",
                   spread=0, radial=-1.4, pedestal=False)]),
], filler=[
    # The level's voice, not its surprise: a slide up under a beam and a
    # slide back down into the meltwater.
    ("floes", [n("packedice", arc=3.4, lift=2, kind="slide", form="ice",
                 spread=0, ceiling=2, orbs=1),
               n("blueice", arc=4.0, lift=1, kind="slide", form="ice",
                 spread=0, moat=True)]),
], exit_beats=[
    # The ice staircase against the core wall: the one place in the tower
    # where the climb out is a run of slides rather than hops, and worth
    # keeping because it is half of every run and this level's own voice.
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, confine=True),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, radial=0.9, orbs=1),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, radial=-0.9),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.6, spread=0, orbs=1),
    n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
      hug=2.8, spread=0),
])
