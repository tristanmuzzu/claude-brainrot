"""Level 6: THE BALCONIES.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# Out of the drowned temple and straight into the sun: terracotta
# balconies bolted to a mesa cliff. A lantern in the sill, the door
# through the balcony's end wall walked under its lintel, then out
# onto the balcony's own tip past the rim -- and you go off the end of
# it, onto a sprung stone in the yard that throws you back against the
# wall. What is left is the gallery, run UNDER the storey above with a
# lintel at three over the jump and the cliff a metre off the
# shoulder, and a lava pour crossing the yard. The way out is a ladder
# up the cliff, not another staircase.
#
# A balcony is bolted to the cliff rather than cut out of the terrace,
# so the whole course here is ``pedestal=False``. That is also what
# makes it survive being built: a landing that needs ground under it
# is refused outright wherever one of the level's floor breaks happens
# to fall, and the gallery measured 0% placed as authored for exactly
# that reason. ``wide`` is the other half -- a balcony is a
# three-by-three deck, which is nine cells of floor in the bottom of a
# frame that was otherwise nine tenths sky.
#
# The showpiece is beat two and not beat three because ``_truncate``
# cuts the last beat of a level and always leaves exactly one node:
# with the fall last, the sprung stone was laid every run and the
# bounce off it never once was.
LEVEL = Level("THE BALCONIES", "mesa", rise=7, gap=3.0, exit="ladder",
              band=9.0, profile="ledge", shelf=4.5, breaks=4,
              landmark="hoodoo",
              ground="terra_orange", sub="terra_red", rock="terra_white",
              accent="terra_yellow", glow="lantern", liquid="lava",
              props=("deadbush", "pebbles", "mcfence"),
              candy=("terra_yellow", "terra_red"),
              step=("terra_white", "hop"),
              sky=(236, 174, 118), beats=[
    # The threshold: a lantern set in the sill, then the door through
    # the balcony's end wall, walked under its lintel.
    ("sill", [n("lantern", arc=3.3, lift=1, hug=3.0, spread=1,
                deco="lamp", orbs=1),
              n("terra_white", arc=2.9, lift=1, hug=3.0, kind="walk",
                spread=0, ceiling=3)]),
    # The showpiece: out onto the balcony's tip past the rim -- nothing
    # under it and the sea a long way down -- and then off the end of
    # it onto the sprung stone in the yard.
    ("brink", [n("terra_yellow", arc=4.0, lift=2, hug=4.8, form="wide",
                 pedestal=False, spread=0, ceiling=2, deco="lamp",
                 orbs=1),
               n("slime", arc=5.0, lift=1, form="slime", hug=4.0,
                 spread=0, ceiling=2, pedestal_style="terra_red"),
               n("terra_white", arc=3.6, lift=3, kind="bounce", hug=3.0,
                 spread=1, orbs=2)]),
    # The gallery, run under the storey above: a beam at three over
    # the jump, then a bay bored clean through the buttress. The shell
    # goes on the beat's last node, never its first.
    ("gallery", [n("terra_white", arc=3.4, lift=2, hug=3.2, spread=1,
                   pedestal=False, ceiling=2),
                 n("terra_red", arc=2.9, lift=2, hug=3.2, kind="walk",
                   spread=0, pedestal=False, ceiling=3, shell="hall",
                   orbs=1)]),
], filler=[
    # The lava pour comes off the cliff and crosses the yard; the
    # stones standing in it are the only dry ground there is.
    ("pour", [n("terra_red", arc=4.6, lift=1, hug=3.0, spread=0,
                ceiling=2, moat=True, orbs=1),
              n("terra_white", arc=3.4, lift=2, hug=2.8, spread=1,
                pedestal=False, ceiling=2)]),
], exit_beats=[
    # The ladder up the cliff, written out rather than left to the
    # generated climb: that one hangs its column at ``hug`` 2.0
    # mid-lane, where there is nothing within a cell of the column's
    # middle to anchor on, and a climb with no anchor is refused
    # silently and replaced by a staircase. A column beside a
    # *pedestal* finds its anchor on the stack.
    n("terra_white", arc=2.8, lift=1, hug=2.4, spread=1),
    # A lamp on the climb and no ``shell="shaft"``: the tube is the
    # obvious answer to three seconds of one flat red face during the
    # ride, and it measured worse on the one criterion that cannot
    # move -- the body ends up inside its wall on three frames of
    # every run. The lamp is a glow billboard, so it lights the ride
    # and collides with nothing.
    n("terra_red", arc=2.4, step_y=7, kind="climb", climb_style="ladder",
      spread=0, deco="lamp", orbs=2),
])
