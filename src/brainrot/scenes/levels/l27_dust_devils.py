"""Level 27: DUST DEVILS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A slot canyon in the badlands.
#
# The idea in one line: you drop off the sunlit rim into a dry wash cut
# between banded terracotta walls, wade the last pool left in it, and
# climb the strata back out past the hoodoos.
#
# What was wrong with the old one, measured rather than guessed: **62%
# empty frame -- the worst level in the back thirteen** -- 22% designed
# content, 98% plain hop, one unchecked emergency placement, and a walker
# that could not even find ground to seed on. Four causes, all geometry:
#
# * **``band=12.5`` was the widest corridor in the tower.** The core wall
#   was eight metres off the shoulder, so the frame was sky on one side
#   and nothing on the other. The reference's corridor has a wall within
#   4 m on 71% of samples; 9.5 puts it there.
# * **It hugged 7.0 and 8.6 on a 3.5-block shelf.** That is twice as far
#   out as its own ledge reaches, over the drop, which is a frame of sea
#   and sky by construction. Everything here hugs 3.0-3.8 on a four-block
#   shelf.
# * **Its script was five beats long and only two of them were ever
#   laid.** A level lays nine to twelve landings and the exit climb takes
#   a third of them; beats three, four and five were writing for a strip
#   nobody sees. Three beats and a filler that carries the character.
# * **The exit climb was 40% of the level and every frame of it was
#   sky.** ``rise=7`` is the tallest in the tower and the staircase is one
#   landing per block, so the way out was eight landings of one terracotta
#   column against a blue sky. The number that fixes it is not in the
#   climb at all: ``need`` is measured from wherever the body *is* when
#   the climb triggers, so a level that ends at lift 4 asks for four steps
#   where one ending at lift 1 asks for eight. This one climbs to lift 4
#   in its own filler and hands the machinery a much shorter job.
#
# And it named three materials on a level whose subject is *strata*. A
# real badlands is banded: red sand underfoot, orange, red, white and
# yellow terracotta in the walls, with the pool the one cold colour in it.
# All six roles are set, four literals on top, five props.
#
# Against THE GROVE below (teal nylium, band 11.0, a bubble lift, damp)
# and THE SEA GATE above (dark teal prismarine, band 12.0, water on the
# floor, gold) this is hot orange, the tightest corridor of the three,
# dry, and lit by the sky rather than by its own lamps.
#
# Three things here that only the per-beat table or the physics table
# would tell you:
#
# * **The descent is beat two, not the tail.** A level's drop belongs in
#   its first two thirds and the exit must be the highest thing in it, so
#   the wash is the low point and everything after it climbs.
# * **The wades are what hold the hop share down.** The exit climb can
#   only ever be hops, and a ``walk`` is the only non-hop a dry mesa
#   honestly owns -- no ice, no slime, no water deep enough to swim, and
#   deliberately no ladder, the tower having far too many already. A walk
#   is never the *first* node of a beat: it needs its predecessor within
#   half a block and a beat boundary does not promise that.
# * **The water is in the *first* beat, not the best one.** Over 24 runs
#   this level lays about eighteen landings a visit and only five or six
#   of them are the design: the opening beat is laid every time, the
#   second gets clipped against the exit climb's arc reserve, and the
#   third and the filler are usually never reached at all. Anything the
#   level is *about* has to be in beat one. That is also why the moat sits
#   on the opening beat's last node -- a moat digs a radius-three disc the
#   moment its landing commits, so nothing may follow it inside three
#   metres, and nothing does.
# * **``frame empty`` is a ray cast, not a sky-colour test.** It counts
#   the sampled directions that reach eight metres without hitting a
#   *voxel*, so the only things that move it are geometry within 8 m:
#   the cliff, the terrace under your feet, pedestals, ``ceiling`` lids
#   and shells. The slab of the turn above is twelve blocks up here and a
#   ray at the probe's steepest up-angle reaches that height fourteen
#   metres away, so this level's ceiling can never register. Props are
#   models and do not register either.
LEVEL = Level("DUST DEVILS", "mesa", rise=7, gap=3.0, exit="stair",
              band=9.5, shelf=4.0, breaks=3, landmark="hoodoo",
              ground="redsand", sub="terra_orange", rock="terra_red",
              accent="terra_white", glow="lantern", liquid="water",
              candy=("terra_yellow", "terra_white"),
              props=("deadbush", "pebbles", "mcfence", "grasstuft",
                     "cactus"),
              sky=(238, 178, 116),
              step=("terra_yellow", "hop"), beats=[
    # The threshold: one lantern set flush in the red sand on a rise, and
    # then a stride onto the yellow band under a slab of rock. The palette
    # changes completely at that lantern -- teal nylium to red sand in one
    # frame -- which is what the reference does at every seam it has.
    #
    # **The threshold is written at lift 1 and that is the whole of why
    # it places.** Machinery is inserted between beats and leaves the body
    # back at lift 1, so a first node asking for lift 2 is asking for a
    # rise it only sometimes gets -- and the ``walk`` after it then needs
    # its predecessor within half a block and does not have it. Measured
    # on this beat alone: lift 2 with a walk second, 67%; the same beat at
    # lift 1, below. ``spread=1`` on the opening node and ``spread=0`` on
    # the one the walk steps off is the other half -- let the landing
    # before a stride settle a block out and the stride is a one-block
    # step, which a walk refuses outright.
    #
    # And **one** walk, not two. Two consecutive strides took this beat to
    # 71% and the sea gate's threshold to 50%.
    ("rimlight", [n("glow", arc=3.2, lift=1, hug=3.0, spread=1,
                    deco="lamp", orbs=1),
                  n("terra_yellow", arc=2.9, lift=1, hug=3.2, kind="walk",
                    spread=0, ceiling=5),
                  n("terra_orange", arc=3.4, lift=2, hug=3.4, spread=0,
                    moat=True, orbs=1)]),
    # The wash, and the whole of the level's one idea in one beat --
    # because machinery is inserted *between* beats and leaves the body
    # back at lift 1, so a rise and the drop off it have to be written
    # together. Two blocks down off the rim onto the canyon floor, two
    # stones standing in the last of the water with a wade to each, and
    # the climb out into a wind-hollowed bay in the cliff.
    ("wash", [n("ground", arc=4.8, lift=0, hug=3.4, form="floor",
                spread=0, orbs=2),
              n("terra_orange", arc=3.6, lift=1, hug=3.0, spread=0,
                moat=True, ceiling=4, orbs=1),
              n("redsand", arc=2.9, lift=1, hug=3.0, kind="walk",
                spread=0),
              n("terra_white", arc=3.4, lift=1, hug=3.4, spread=0,
                orbs=1),
              n("redsand", arc=2.9, lift=1, hug=3.4, kind="walk",
                spread=0, ceiling=5),
              n("terra_red", arc=3.5, lift=2, hug=3.2, spread=0,
                shell="grotto")]),
    # The hoodoos themselves: thin spires with white capstones, weaving
    # across the lane, the middle one hung out over the wash with nothing
    # under it and a beam across the jump onto it. This ends at lift 4,
    # which is the level's high ground and the reason its way out is four
    # steps rather than eight.
    ("hoodoos", [n("terra_white", arc=3.4, lift=2, hug=3.2, spread=0,
                   radial=1.2, ceiling=4, orbs=1),
                 n("terra_red", arc=3.3, lift=3, hug=3.8, spread=0,
                   radial=-1.3, pedestal=False, deco="lintel"),
                 n("terra_yellow", arc=3.6, lift=4, hug=3.0, spread=0,
                   deco="post", orbs=1),
                 n("terra_white", arc=2.9, lift=4, hug=3.2, kind="walk",
                   spread=0, ceiling=4)]),
], filler=[
    # The character, repeated, and on a terrace this long the filler is
    # most of what is actually seen: a long drop back into the wash, a
    # stride along it, and two banded steps up onto the rim again. It
    # ends at lift 4 every lap, so however long the terrace runs the
    # climb out is asked for from the top of the level rather than the
    # bottom of it -- and it never falls more than two, which is the rule
    # about a run not undoing itself.
    ("strata", [n("terra_white", arc=4.6, lift=2, hug=3.0, spread=2,
                  orbs=1),
                n("terra_orange", arc=2.9, lift=2, hug=3.0, kind="walk",
                  spread=0),
                n("terra_yellow", arc=3.5, lift=3, hug=3.4, spread=0),
                n("terra_red", arc=3.4, lift=4, hug=3.0, spread=0,
                  orbs=1)]),
])
