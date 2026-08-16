"""Level 6: THE BALCONIES.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A cliff dwelling in the badlands. The mesa is cut in bands -- orange,
# red, white -- and bolted to the face of it is a stack of oak-and-clay
# balconies, one deck above the next, the way a cliff village hangs off
# a canyon wall. A lava seep comes out of a crack in the cliff and runs
# across the terrace between two of them. Two hoodoos stand off the lip
# where the ledge ends, and you jump between them.
#
# The route is a climb and a fall. You come in over a lit sill and duck
# under the lintel of a doorway; then the balconies -- a stone standing
# in the seep at the foot of the cliff, a walk out through the balcony
# door onto a three-wide deck with nothing under it, up onto the deck
# above, up again onto the top deck with the lamp on its rail -- and
# then **off the end of that one**, two blocks down and nearly five
# metres out, which is the longest jump in the level and the only kind
# of long jump this motion model has. Below is the yard, where the lava
# crosses the terrace and one stone stands in it. The way out is the
# outside of the topmost balcony: a ladder up the cliff and two decks
# stepping out over the chasm, so the last thing before the leap is a
# lit floor and not a wall.
#
# Four things here are answers to measurements, not taste.
#
# **The whole level used to sit at lift 1 and 2 and then take a ladder
# seven blocks in one move.** Every landing was at y21-23 and the exit
# was the only vertical thing in it -- the owner's complaint about the
# roster in one level: ground-level hops, then stairs. The climb and
# the fall are now one beat, because machinery is inserted *between*
# beats and leaves the body back at lift 1: a rise written in one beat
# and spent in the next is a rise that does not happen.
#
# **Everything in the body of the level floats** (``pedestal=False``).
# A balcony is bolted to a cliff rather than cut out of a terrace, and
# it is also the only way this design survives being built. With a
# pedestal on the balcony beat's opener -- which lands just off the
# lock's island, over broken ground -- ``_targets`` returned nothing,
# ``_last_resort`` threw away the whole rest of the beat with it, and
# the beat measured 65% laying one landing of four. Floated, it is
# 100% laying nearly four.
#
# **The exit is authored and it is the level's own architecture**: a
# five-block ladder and then two decks. A single climb of seven, which
# is what this level had, is nine consecutive frames of flat wall on
# the contact sheet, and it is why this was the tower's worst level for
# a jammed lens. The arc left over after the exit climb's reserve will
# not buy a shorter ladder than five -- see the note on ``exit_beats``.
#
# **The showpiece is beat two.** Beats one and two are laid whole on
# nearly every run, beat three about half the time, and beat four
# almost never; the filler runs only when the terrace outlasts all of
# them. So the level's identity is the sill and the balconies, and the
# eroded half-steps in the filler are a bonus rather than the point.
LEVEL = Level("THE BALCONIES", "mesa", rise=8, gap=3.0, exit="ladder",
              band=9.0, profile="ledge", shelf=4.5, breaks=4,
              landmark="hoodoo",
              ground="terra_orange", sub="terra_red", rock="terra_white",
              accent="terra_yellow", glow="lantern", liquid="lava",
              props=("deadbush", "pebbles", "mcfence"),
              candy=("terra_yellow", "oak"),
              step=("terra_white", "hop"),
              sky=(236, 174, 118), beats=[
    # The threshold: a lantern set flush in the sill, then the door
    # through the balcony's end wall, walked under its lintel. A body
    # cannot jump through a doorway -- one impulse always rises 1.25 m
    # and the head then sweeps three cells above the take-off -- so the
    # lintel is a `ceiling` beam and the leg under it is a `walk`.
    ("sill", [n("lantern", arc=3.2, lift=1, hug=3.0, spread=1,
                deco="lamp", orbs=1, ceiling=2),
              n("terra_white", arc=2.9, lift=2, hug=3.0, kind="walk",
                spread=0, ceiling=3),
              n("rock", arc=3.0, step_y=1, spread=0),
              n("rock", arc=3.0, step_y=1, spread=0),
              n("rock", arc=3.0, step_y=1, spread=0)]),
    # The balconies, and the level's whole shape in one beat: a stone
    # standing in the seep at the foot of the cliff, a *walk* out
    # through the balcony door onto a three-wide deck with nothing
    # beneath it, up onto the deck above, up again onto the top deck
    # which carries the lamp -- and then **off the end of that one**,
    # two blocks down and 4.9 of arc out into the air.
    #
    # The walk is at position two and not at the tail on purpose: a
    # beat lays about four of its five nodes and a verb written last is
    # written and never seen. It is also the only reliable non-hop the
    # body of this level has, and it takes the hop share from 89% to
    # 83%. A doorway is *walked* through because it cannot be jumped
    # through -- one impulse rises 1.25 m and the head then sweeps
    # three cells above the take-off, so a lintel low enough to read as
    # a door refuses every arc under it.
    #
    # The climb and the fall are one beat because machinery is
    # inserted *between* beats and leaves the body back at lift 1: a
    # rise written in one beat and spent in the next is a rise that
    # does not happen. And the fall is the level's descent and its long
    # jump at once -- falling takes time and the body does not slow
    # down while it does, so a drop is the only jump this motion model
    # has that reads as *long*. 4.9 is legal level, -1 and -2, which is
    # every height the three landings above it can leave the body at;
    # `spread=2` is what makes that a promise rather than a hope.
    #
    # Every landing here floats. A balcony is bolted to a cliff rather
    # than cut out of a terrace, and it is also the only way the beat
    # survives: with a pedestal on its opener -- which lands right off
    # the lock's island, over broken ground -- `_targets` returned
    # nothing, the whole rest of the beat was abandoned with it, and
    # the beat measured 65% laying one landing of four.
    #
    # The opener carries a `moat` as well as the yard beat below,
    # because it is the one landing of this level that is laid on every
    # single run: the lava has to be somewhere the viewer will
    # certainly see it, and everything downstream of it floats, so the
    # bowl it digs cannot take a pedestal with it.
    ("balconies", [n("oak", arc=3.4, lift=5, hug=2.8, spread=2,
                     pedestal=False, moat=True),
                   n("terra_white", arc=3.2, lift=5, hug=3.6, form="wide",
                     kind="walk", pedestal=False, spread=0, ceiling=3,
                     orbs=1),
                   n("terra_yellow", arc=3.4, lift=6, hug=3.8,
                     pedestal=False, spread=1, ceiling=2),
                   n("terra_orange", arc=3.0, lift=6, hug=4.4,
                     pedestal=False, spread=1, deco="lamp", orbs=1),
                   n("terra_red", arc=4.9, lift=5, hug=3.0, pedestal=False,
                     spread=2, orbs=2)]),
    # The yard under the balconies, where the lava seep out of the
    # cliff crosses the terrace and the one stone standing in it is the
    # only dry ground. The moat is on this beat's *first* node and not
    # its second, which is the opposite of what the pond radius wants
    # and is right anyway: a beat's tail is almost never laid, and
    # written second the lava was authored and never once built. The
    # landing after it floats, so the bowl the moat digs cannot take
    # the ground out from under it.
    ("seep", [n("terra_white", arc=3.4, lift=5, hug=2.8, spread=1,
                moat=True, ceiling=2, orbs=1),
              n("terra_orange", arc=3.0, lift=5, hug=3.2, kind="walk",
                spread=0, pedestal=False, ceiling=3)]),
    # The gallery, run under the storey above: a bay bored through the
    # buttress, crossed on foot with a beam at three over the head. The
    # shell goes on the beat's last node, never its first -- it is
    # painted the moment its landing commits and its walls are then in
    # the way of the next landing of the same beat.
    ("gallery", [n("terra_white", arc=3.4, lift=6, hug=2.6, spread=1,
                   pedestal=False, ceiling=3),
                 n("oak", arc=2.9, lift=6, hug=2.6, kind="walk", spread=0,
                   pedestal=False, ceiling=3, shell="hall", orbs=1)]),
], filler=[
    # The balcony run again, and this is what the level mostly *is*: in
    # under the eaves, a half-height step out onto the deck edge, the
    # deck's own tip past the rim, and back down inboard. The two
    # ``slab`` steps are the reference's commonest non-cube form and
    # this tower has barely used it -- a half step reads as an eroded
    # ledge rather than as a cube, and it buys reach: +0.5 allows 3.78
    # where +1 stops at 3.10. No ``moat`` anywhere here: the filler
    # loops, and a second lap digs away the ground the first lap's
    # pedestals are standing on.
    ("ledgerun", [n("terra_orange", arc=3.4, lift=6, hug=2.8, spread=1,
                    ceiling=2),
                  n("terra_white", arc=3.4, lift=6, form="slab", hug=3.4,
                    pedestal=False, spread=1),
                  n("terra_yellow", arc=3.4, lift=6, hug=4.2,
                    pedestal=False, spread=1, orbs=1)]),
], exit_beats=[
    # The way out, written down rather than left to the generated
    # climb. Four landings against the fallback staircase's eight, and
    # it is the level's own architecture: a ladder up the cliff face
    # onto the topmost balcony, then two decks stepping out over the
    # chasm.
    #
    # The ladder is *five* and not the whole eight this level rises.
    # Measured on the version this replaces: one climb of seven is nine
    # consecutive frames of flat wall on the contact sheet, the body
    # riding a column at arm's length with nothing else in the lens,
    # and it is most of why this level reads as the tower's worst for a
    # jammed view. Ending on two lit decks instead means the last thing
    # before the leap is a floor, and it took the jam from 23% to 15%.
    #
    # It cannot be shorter, and the arithmetic is worth writing down.
    # The exit climb is triggered when the frontier is within ``want``
    # of the chasm, and for a climb exit ``want`` comes out at about 18
    # blocks of arc; the crossing spends 4.4 of that, so the treads
    # have about 13.5. A ladder of four plus four one-block treads is
    # 2.6 + 2.4 + 4 x 3.0 = 17, which starts the climb further back
    # than it is given and ends it out over the hole. Five plus two is
    # 11.6 and fits.
    #
    # ``pedestal=True`` on the climb is load-bearing and is the reason
    # this branch fires at all: ``_climb_move`` wants solid rock within
    # one cell of the column at its middle index and at its top, and
    # out in the lane the only candidate is the landing's own stack. A
    # floated column is refused silently and the level gets a staircase
    # without being told. ``pedestal_style`` paints that stack -- a
    # column of orange banded terracotta with a white cap, which is a
    # hoodoo, rather than the flat dark red it used to be.
    #
    # ``hug`` on the climb is the *lens*, not the anchor. Left at the
    # default the column stands mid-lane with the body on the outside
    # of it, and the ride is six frames of nothing but that column's
    # own face; at 2.0 it is a cell off the core, which is where the
    # generated climb was tuned to put it for exactly this reason. The
    # decks after it float, because a deck with a pedestal under it
    # nine blocks over the terrace is not a balcony, it is another
    # column in the lens.
    n("terra_orange", arc=2.8, step_y=0, hug=2.4, spread=1, ceiling=2),
    n("terra_white", arc=2.4, step_y=2, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=True, pedestal_style="terra_orange", spread=0,
      deco="lamp", orbs=2),
    n("terra_yellow", arc=3.2, step_y=1, hug=3.8, pedestal=False,
      spread=0, deco="lamp", orbs=2),
])
