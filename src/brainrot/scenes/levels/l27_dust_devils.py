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
#   4 m on 71% of samples.
# * **It hugged 7.0 and 8.6 on a 3.5-block shelf.** That is twice as far
#   out as its own ledge reaches, over the drop, which is a frame of sea
#   and sky by construction. Everything here hugs 3.0-3.8.
# * **Its script was five beats long and only two of them were ever
#   laid.** A level lays nine to twelve landings and the exit climb takes
#   a third of them; beats three, four and five were writing for a strip
#   nobody sees. Three beats and a filler that carries the character.
# * **The exit climb was 40% of the level and every frame of it was
#   sky.** ``rise=6`` is the tallest in the tower and the staircase is one
#   landing per block, so the way out was eight landings of one terracotta
#   column against a blue sky.
#
# **That pass took the empty frame from 62% to 60% and no further**, and
# a second one (2026-08-13) against a rule that is now *under 48%* had to
# find out why. The answer was measured with a ray fan bucketed by the
# feature the body was standing on, and it is two things, neither of them
# the corridor:
#
# * **The ground beside the lane was empty, not the corridor.**
#   ``shelf=4.0`` inside ``band=9.5`` is a four-block ribbon with five
#   and a half blocks of drop beside it, and the fan's two lower rows
#   spend that drop on the sea. ``shelf=6.0`` inside ``band=10.5`` is
#   the same corridor with a terrace carrying it: the bottom row of the
#   frame goes **32% -> 19% empty** and the one under the horizon
#   **44% -> 33%**, for *better* fidelity (90% -> 92% exact,
#   ``rimlight`` 93% -> 96%, ``strata`` back to 100%) and still no
#   unchecked placement. This is the opposite of the rule of thumb in
#   ``docs/RULES.md`` that a wide shelf costs the exit climb its lane --
#   which was measured at ``band=9.0``, where widening the shelf leaves
#   the climb nothing, and does not hold with a block of band to spare.
# * **The exit climb is asked for from lift 1, not from lift 4.** The
#   note this file used to carry -- that the level climbs to lift 4 in
#   its own filler and hands the machinery a shorter job -- is false, and
#   the segment table says so: machinery is inserted *between* beats and
#   leaves the body back at lift 1, so ``need`` is six or seven every
#   time and the climb is 40% of every frame however the design ends. It
#   cannot be shortened from here; it can only be roofed, which is what
#   ``exit_beats`` below does.
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
# * **And on a ledge, a ``shell`` is a roof and nothing else.** Its walls
#   only stand where the cell under them is solid, and the two columns a
#   five-wide shell wants sit one cell *inside* the cliff and one cell
#   *past* the shelf edge -- so a ``cave`` or a ``hall`` on this level
#   wrote about thirteen cells, all of them roof, and moved the number by
#   nothing measurable. A single lid or shell anywhere in a script beat
#   is noise here: the design is a third of the level and a beat is four
#   landings of it. Only the things that touch every frame -- the ground
#   under the lane, and the climb -- are worth spending a pass on.
LEVEL = Level("DUST DEVILS", "mesa", rise=7, gap=3.0, exit="stair",
              band=10.5, shelf=6.0, breaks=3, landmark="hoodoo",
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
                    deco="lamp", ceiling=7, orbs=1),
                  n("terra_yellow", arc=2.9, lift=1, hug=3.2, kind="walk",
                    spread=0, ceiling=7),
                  n("terra_orange", arc=3.4, lift=1, hug=3.4, spread=0,
                    moat=True, ceiling=3, orbs=1)]),
    # The wash, and the whole of the level's one idea in one beat --
    # because machinery is inserted *between* beats and leaves the body
    # back at lift 1, so a rise and the drop off it have to be written
    # together. Down off the rim onto the canyon floor, two stones
    # standing in the last of the water with a wade to each, and the
    # climb out into a wind-hollowed bay in the cliff.
    #
    # The rim above ends at lift 1, not lift 2, and that is a *frame*
    # decision as much as a fidelity one: the drop is a block shallower
    # and the beat below it is reached twice as often (its landings went
    # 61 to 120 over four seeds), which is worth two points of empty
    # frame on its own -- the wash is the fullest thing in the level at
    # 42% against ``rimlight``'s 59%, so screen time spent down here is
    # screen time not spent looking off the rim.
    ("wash", [n("ground", arc=4.8, lift=0, hug=3.4, form="floor",
                spread=0, ceiling=5, orbs=2),
              n("terra_orange", arc=3.6, lift=1, hug=3.0, spread=0,
                moat=True, ceiling=4, orbs=1),
              n("redsand", arc=2.9, lift=1, hug=3.0, kind="walk",
                spread=0),
              n("terra_white", arc=3.4, lift=1, hug=3.4, spread=0,
                ceiling=7, orbs=1),
              n("redsand", arc=2.9, lift=1, hug=3.4, kind="walk",
                spread=0, ceiling=7),
              n("terra_red", arc=3.5, lift=2, hug=3.2, spread=0,
                shell="grotto")]),
    # The hoodoos themselves: thin spires with white capstones, weaving
    # across the lane, the middle one hung out over the wash with nothing
    # under it and a beam across the jump onto it. This ends at lift 4,
    # which is the level's high ground -- but see the head of the file:
    # it does *not* shorten the way out, because machinery is inserted
    # after it and puts the body back on the floor first.
    ("hoodoos", [n("terra_white", arc=3.4, lift=2, hug=3.2, spread=0,
                   radial=1.2, ceiling=4, orbs=1),
                 n("terra_red", arc=3.3, lift=3, hug=3.8, spread=0,
                   radial=-1.3, pedestal=False, deco="lintel"),
                 n("terra_yellow", arc=3.6, lift=4, hug=3.0, spread=0,
                   deco="post", ceiling=3, orbs=1),
                 n("terra_white", arc=2.9, lift=4, hug=3.2, kind="walk",
                   spread=0, ceiling=5, shell="tunnel")]),
], filler=[
    # The character, repeated, and on a terrace this long the filler is
    # most of what is actually seen: a long drop back into the wash, a
    # stride along it, and two banded steps up onto the rim again. It
    # ends at lift 4 every lap and never falls more than two, which is
    # the rule about a run not undoing itself. It does **not** shorten
    # the climb out -- that was the belief this file was written on and
    # the segment table refuted it; see the head of the file.
    ("strata", [n("terra_white", arc=4.6, lift=2, hug=3.0, spread=2,
                  orbs=1),
                n("terra_orange", arc=2.9, lift=2, hug=3.0, kind="walk",
                  spread=0, ceiling=5),
                n("terra_yellow", arc=3.5, lift=3, hug=3.4, spread=0),
                n("terra_red", arc=3.4, lift=4, hug=3.0, spread=0,
                  ceiling=7, orbs=1)]),
], exit_beats=[
    # Out up the strata, written down tread by tread instead of left to the
    # generated staircase -- and this is the single biggest thing in the
    # file. The exit climb is **40% of every frame spent on this level**
    # and it was the emptiest thing in the tower at 68% sky; the design
    # beats put together are a third of that. Two numbers do the work and
    # neither is guessable:
    #
    # * **Eight treads, not four.** ``need`` is measured from wherever the
    #   body is when the climb triggers, and machinery is inserted between
    #   beats and leaves it back at lift 1 -- so the note above about this
    #   level "climbing to lift 4 and handing the machinery a shorter job"
    #   is not what happens: it asks for six or seven. An authored list
    #   shorter than that runs out, the crossing is refused, and
    #   ``_pending`` is replaced wholesale by the generated stair, which
    #   carries no lid at all. Measured over four seeds: four treads took
    #   the climb 68% -> 59% empty, eight took it to **49%**.
    # * **``hug=1.8``, against the generated stair's 2.4.** Hard against
    #   the cliff the treads read as ledges cut into the tower and the
    #   weathered face fills the inboard half of every frame of the climb;
    #   0.6 of a block was worth a point and a half of the level's total.
    #
    # And it is **free**: measured over 24 runs against the generated
    # stair on the same ground, exact 91% either way, unchecked 0 either
    # way, the same move mix to a landing. A tread that cannot be placed
    # simply hands ``_pending`` back to ``_ascent_stair``, so the whole
    # reliability chain is still underneath this.
    #
    # Each tread carries the two things a level author has against the
    # sky -- a ``ceiling`` beam along its own arc and a ``tunnel`` roof
    # over the jump that arrived -- and a pedestal, so the flight reads as
    # built terrain rather than as eight cubes hung one above the other.
    # The first is unhugged because it is placed from wherever the body
    # happens to be standing; the rest are pinned.
    n("terra_yellow", arc=3.0, step_y=1, spread=0, confine=True,
      pedestal_style="terra_orange", ceiling=7, shell="tunnel", orbs=1),
    n("terra_white", arc=2.9, step_y=1, hug=1.8, spread=0, confine=True,
      pedestal_style="terra_red", ceiling=7, shell="tunnel"),
    n("terra_orange", arc=3.0, step_y=1, hug=1.8, spread=0, confine=True,
      pedestal_style="terra_yellow", ceiling=7, shell="tunnel", orbs=1),
    n("terra_red", arc=2.9, step_y=1, hug=1.8, spread=0, confine=True,
      pedestal_style="terra_white", ceiling=7, shell="tunnel"),
    n("terra_yellow", arc=3.0, step_y=1, hug=1.8, spread=0, confine=True,
      pedestal_style="terra_orange", ceiling=7, shell="tunnel", orbs=1),
    n("terra_white", arc=2.9, step_y=1, hug=1.8, spread=0, confine=True,
      pedestal_style="terra_red", ceiling=7, shell="tunnel"),
    n("terra_orange", arc=3.0, step_y=1, hug=1.8, spread=0, confine=True,
      pedestal_style="terra_yellow", ceiling=7, shell="tunnel", orbs=1),
    n("terra_red", arc=2.9, step_y=1, hug=1.8, spread=0, confine=True,
      pedestal_style="terra_white", ceiling=7, shell="tunnel"),
])
