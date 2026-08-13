"""Level 4: THE TIMBERWORKS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The sawmill over the log pond, and this is the tower's vertical level.
#
# One sentence: *a plank deck floated over black water, with a headframe
# you climb and a chute you fall down.* The street below it never leaves
# the ground and is red in daylight; this is wide, dark, wet, lamp-lit,
# and the only thing you do in it that matters is go up four blocks and
# then come down all four at once.
#
# Its floor is oak decking on dark-oak beams, log ends, rails, pebbles
# and lantern light -- and the whole middle of the terrace is water
# (``profile="channel"``), so where the ground is widest it is not
# ground at all. That is the reference's own answer to "you can walk
# past it": width plus hazard, not chasms. It is also why nothing here
# is a ``form="floor"`` landing out in the middle of the band -- there
# is no floor out there to stand on. It carries exactly one ``break``,
# and that number is measured rather than chosen: any break at all
# forces the lock, which costs two and a half of the twelve landings
# this level lays -- but with none, six moats and a channel down the
# middle still left a no-jump walker covering 56-60% of it, over the
# 55% rule. One break, one lock: 39%.
#
# **Written for four beats, not for ten**, for the same measured reason
# as the street below: a level lays nine to twelve landings and only
# four or five are the script's. So the headframe and the chute -- the
# whole point of the place -- are the *second* beat, and the character
# is in the filler, which repeats.
LEVEL = Level("THE TIMBERWORKS", "mine", rise=5, gap=2.6, exit="ladder",
              band=11.0, profile="channel", breaks=1, landmark="crane",
              ground="oak", sub="darkoak", rock="darkoak", accent="log",
              glow="lantern", liquid="water", dark=0.45,
              step=("oak", "hop"),
              props=("rail", "torch", "pebbles", "mcfence", "lanternpost",
                     "lilypad"),
              beats=[
    # The threshold, the headframe and the chute are **one beat**, and
    # that is the whole design decision on this level. A beat is laid
    # whole or truncated from the end and machinery is inserted
    # between beats, so anything past the first beat competes with the
    # lock and the crane's crossing for an arc budget of about forty
    # metres -- split into two, the chute was laid in five runs of
    # sixteen. Together they are laid every run.
    #
    # The lantern flush in the decking, the timbered portal walked
    # through (a walk is second, never first: first in a beat it
    # follows machinery at an arbitrary height and a walk needs its
    # predecessor within half a metre), the launch board hard against
    # the rock, the ladder, the fall and the bounce.
    #
    # The landing at the top of the ladder keeps its pedestal because
    # whole or truncated from the end, and split in half this one spent
    # three runs in four laying the climb and cutting the fall it
    # exists for. The landing at the top keeps its pedestal because
    # that is what the ladder hangs on, and ``step_y`` of four is the
    # smallest that puts the column's middle cell inside it -- at three
    # the anchor is gone and the climb is refused nine times in ten.
    # No ``shell="shaft"`` on it, and that is measured too: the tube's
    # outer ring stands one cell beyond the landing the ride ends on,
    # exactly where the chute's take-off passes, and the body came out
    # 0.46 m inside dark oak on three frames of every run. It also cost
    # a third of the beat's frames to a wall.
    ("headframe", [n("glow", arc=3.2, lift=1, form="slab", spread=0,
                     deco="lamp", orbs=1),
                   n("rock", arc=2.8, lift=1, form="slab", kind="walk",
                     spread=0, shell="tunnel"),
                   n("rock", arc=2.9, lift=1, hug=2.8, spread=1,
                     moat=True),
                   n("ladder", arc=2.4, step_y=4, kind="climb",
                     climb_style="ladder", hug=2.6,
                     pedestal_style="darkoak", spread=0,
                     deco="lamp", orbs=2),
                   n("slime", arc=4.6, lift=2, form="slime", spread=0,
                     pedestal_style="darkoak"),
                   n("accent", arc=3.6, lift=3, kind="bounce", spread=1,
                     orbs=2)]),
    # The deck, and a log floating in the pond with nothing under it
    # and the water dug out from beneath the jump. No ``hug`` on
    # either, and that is a fix rather than a style: the landing before
    # them is laid mid-band, so a hug pulls the next one several metres
    # across the corridor as well as along it, and a jump authored at
    # 3.4 becomes one placement measures at five and refuses. These two
    # beats read 69% and 75% with hugs on. The first landing is
    # written at 3.9 for the same reason as the street's filler below:
    # the beat before it ends on a bounce whose ``spread`` lets it
    # come down at three different heights, and 3.9 is the only arc
    # legal from all of them. The log stands on a piling rather than
    # floating, because a landing hung past the shelf edge costs about
    # two and a half points of empty frame and this level was at 54.
    ("deck", [n("ground", arc=3.9, lift=2, spread=2, moat=True),
              n("accent", arc=3.4, lift=1, spread=0,
                pedestal_style="log", moat=True, orbs=1)]),
    # And out under the crane's boom.
    ("boom", [n("accent", arc=3.2, lift=1, spread=0, moat=True),
              n("rock", arc=3.0, lift=2, spread=0, ceiling=3, moat=True,
                orbs=1)]),
], exit_beats=[
    # The way out is the second headframe. Authored for the same
    # measured reason as the street's chimney below: the generated
    # ladder has no pedestal to hang on, so the only thing it can
    # anchor on is the cliff, and over half the runs it found nothing
    # and fell back to an eight-landing staircase. The generated
    # staircase is still the fallback underneath.
    n("rock", arc=2.8, lift=1, hug=2.8, spread=1, confine=True),
    n("ladder", arc=2.4, step_y=5, kind="climb", climb_style="ladder",
      hug=2.6, pedestal_style="darkoak", spread=0, confine=True,
      deco="lamp", orbs=2),
], filler=[
    # The pond, and on a level that lays twelve landings this is most
    # of what is seen: a log floating in the water, a plank walkway
    # across it, a lit threshold board run over, and a beam.
    ("pond", [n("accent", arc=3.9, lift=1, spread=1, pedestal=False,
                moat=True, orbs=1),
              n("ground", arc=3.2, lift=1, form="trapdoor", spread=0),
              n("glow", arc=2.6, lift=1, form="slab", kind="walk",
                spread=0, deco="lamp"),
              n("rock", arc=3.2, lift=1, spread=0, moat=True)]),
])
