"""Level 4: THE TIMBERWORKS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A sawmill yard over a flooded log pond, standing under its own crane.
#
# One sentence: *you climb the timber, not the ground.* The yard is a
# wide oak deck with water standing in the cuts, and everything you land
# on after the threshold is stacked lumber -- a log floating in the
# pond, a sawn board a block higher, the top of the pile above that --
# so the route is a flight of timber that lifts off the deck at the
# second landing and comes off the end of each pile in a two-block fall.
# The crane is over your head twice: as the tie-beam ducked under at the
# threshold, and as the whole standing crane, whose mast and jib the
# course runs *between*. You leave up the headframe ladder.
#
# The level below is a covered terracotta street that never leaves the
# ground; this one is brown timber over blue water and is off the deck
# by its second landing. They are not confusable from a single frame.
#
# Its identity is the **floor**, which is the thing the reference does
# and this tower did not. Thirteen materials, no one of them over 18%,
# with spruce, dark oak, oak and log between them owning 61% and a tail
# of gravel, bark, moss and mill iron underneath. Before this pass the
# level named three materials and inherited the mine theme's own grey
# palette behind them, so 59% of the ground in a level called THE
# TIMBERWORKS was deepslate and cobble, and the contact sheet was grey.
#
# **Written for two beats and a filler, not for ten.** Measured over
# twenty-four runs this level lays about ten landings and only two and
# a half of them are the script's: the exit climb takes four and the
# lock takes three. So the threshold, the palette, the head-hitter and
# the water are all inside the *first* beat, and everything after it is
# written knowing it may not be reached. That budget is not stable
# either -- it moved from four script landings to two and a half while
# the levels *below* this one were being rewritten, with this file
# untouched, so read any absolute fidelity number here against the
# world it was taken in.
#
# ``profile`` was ``channel`` and that is the largest single change
# here. A channel cuts its liquid two cells wide at 3.6 out from the
# core -- which is exactly where ``Course.lane_radius`` puts the running
# line, so ``Cone.rock`` is False under the lane and a gated structure's
# base cells can never find footing there. Measured on the old design:
# the crane's gate never once reserved in eight runs, the course never
# went through it, and the level held its own landmark on screen for
# 0.6 s against the 1.5 s rule. A plaza gives the crane ground to stand
# on -- 2.0-2.7 s over three seeds now -- and the water comes back as
# moats, which is the reference's own way of doing it anyway: liquid in
# a *hole*, under the jump, rather than a ribbon beside it. It is the
# hole and not the liquid that stops a walker.
#
# ``breaks`` is 1, and that is measured rather than chosen. The number
# moves *every* break rather than adding one, so the four values are
# four different levels: 0 gives 60% designed content and a walker that
# covers 57% of the level (over the 55% rule, and 97% on its worst
# lap); 1 gives 44% and **34%**; 2 gives 45% and 40%; 3 gives 39% and
# 48%. One break is the only one that is comfortably inside both.
LEVEL = Level("THE TIMBERWORKS", "mine", rise=5, gap=2.6, exit="ladder",
              band=11.0, profile="plaza", breaks=1, landmark="crane",
              ground="oak", sub="darkoak", rock="spruce", accent="log",
              glow="lantern", liquid="water", dark=0.45,
              step=("oak", "hop"),
              # The yard floor. Four timbers carry it and the tail is
              # what a working yard has underfoot: bark and sawdust
              # (podzol, moss), the gravel road, the mill's iron plate,
              # and enough stone that the terrace still reads as cut
              # into a mountain rather than rafted onto it.
              floor=(("spruce", 3), ("darkoak", 2), ("log", 2),
                     ("gravel", 2), ("coarse", 2), ("mossy", 1),
                     ("cobble", 1), ("iron", 1), ("stone", 1),
                     ("andesite", 1), ("moss", 1), ("podzol", 1)),
              props=("rail", "torch", "pebbles", "mcfence", "lanternpost",
                     "lilypad"),
              beats=[
    # The beat that *is* the level. It gets three and a half of its four
    # landings on an ordinary run and nothing later is reliable, so the
    # threshold, the one head-hitter, the water and the climb off the
    # deck are all inside it.
    #
    # Four ideas in four landings, which is the density the complaint
    # asked for -- not three hops at the same height:
    #
    #   0. a lantern set flush in the decking, on a half step. The
    #      threshold: a light to aim at and the complete change of
    #      palette from the terracotta street below.
    #   1. the plank over the mill race: the crane's tie-beam three
    #      cells over the take-off, *walked* under at a run, with the
    #      pond dug out either side of it. A jump's apex sweeps the two
    #      cells above every take-off, so a lid low enough to read as a
    #      beam refuses every arc under it -- the genre's 2bc is only
    #      expressible over a leg that never leaves the ground. The
    #      walk is second and never first: first in a beat it follows
    #      machinery at an arbitrary height, and a walk needs its
    #      predecessor within half a metre. The water is on *this*
    #      landing rather than the next because this is the last one a
    #      short terrace is certain to lay -- measured, the beat gets
    #      between one and a half and three and a half of its four.
    #   2. a log floating over the pond's far lip, with nothing under
    #      it.
    #   3. the sawn stack above it, under a second beam.
    #
    # The surfaces are 1.5 / 2.0 / 3.0 / 4.0 and every step between them
    # is legal by construction: a slab stands half a block down in its
    # own cell, so the lantern into the tie-beam is +0.5, inside the
    # 0.55 a walk allows. The two jumps after it are +1.0 at ``arc``
    # 3.2, a reach of 2.52 against a +1 window that shuts at 3.10 --
    # written at the 3.6 this roster used to default to they would be
    # reaches of 2.92 and would spend their lives falling back.
    #
    # Landing 2 is ``pedestal=False`` for two reasons at once: a log in
    # a pond has nothing under it, and the moat on landing 1 digs a bowl
    # of radius three that a plinth 3.2 m along would have to stand in.
    #
    # And a trap that cost this level one of its two ponds without
    # anything reporting it: ``Course._moat`` fills the bowl with
    # ``node["pedestal_style"] or theme.liquid``. Both keys on one node
    # and the pond fills with the *plinth's* material -- this one was
    # written ``pedestal_style="log"`` and dug a hole full of logs,
    # which is solid, which a no-jump walker strolls across. Never put
    # ``pedestal_style`` on a ``moat`` node.
    ("sawbench", [n("glow", arc=3.2, lift=1, spread=0,
                    deco="lamp", orbs=1),
                  n("sub", arc=3.0, lift=2, spread=0,
                    ceiling=3, moat=True),
                  n("accent", arc=3.2, lift=3, spread=0, pedestal=False,
                    orbs=1),
                  n("ground", arc=3.2, lift=4, spread=0,
                    pedestal_style="darkoak", ceiling=3, orbs=2)]),
    # Off the end of the pile, and this is the level's long jump. It is
    # written at 4.4 because it is a *descent*: nothing rises two blocks
    # in one impulse, but a fall of two buys a reach of 3.72, and a
    # descent is the only way this motion model makes a jump read as
    # long. 4.4 is also the only arc legal from all the heights it may
    # be asked from -- two blocks down off the stack when this beat
    # follows the one above it, and level when machinery has been
    # inserted between them and left the body back on the deck, which
    # is about half the time.
    #
    # Then the plank across the second pond cut with a beam over it, and
    # up onto the next pile. The level's two ``moat`` landings are eight
    # metres apart: the pond a moat digs is three cells across, and two
    # any closer means the second stands in the hole the first dug.
    ("pond", [n("rock", arc=4.4, lift=2, spread=2, orbs=2),
              n("ground", arc=3.2, lift=2, spread=0, moat=True,
                ceiling=3),
              n("accent", arc=3.2, lift=3, spread=0, pedestal=False,
                orbs=1)]),
], exit_beats=[
    # The headframe: a launch board hard against the rock inside a
    # timber shed, and a ladder up out of it. Authored rather than left
    # to the generated climb, because the generated ladder hangs at
    # ``hug`` 2.0 with no pedestal and the only thing it can anchor on
    # is the cliff -- swept across ``hug`` 1.4-3.0 it managed twelve
    # successful climb-moves in 2,751 candidates, and a level whose exit
    # falls through to the staircase spends seven of its ten landings on
    # it. A ladder up a stack anchors on the stack, and ``step_y`` of
    # four or more is what puts the column's middle cell inside it.
    # Five, here, because the crossing appended after the climb comes
    # down one block onto the next terrace and this level's ``rise`` is
    # five. The generated staircase is still underneath as the fallback,
    # and the move mix shows ``climb`` at 10% either way, which is how
    # it is known the ladder is really firing.
    #
    # The launch is *roofed*, and this is the level's one shell. The
    # exit climb is the emptiest third of every level in this tower, and
    # a shell on the landing the climb starts from takes its chimney out
    # of cells the climb has already reserved, so the doorway cuts
    # itself. Measured on identical worlds, seed 3 over 24 runs: no
    # shell 42% of the view empty, ``hall`` **39%**, ``cave`` 37% --
    # and the cave is the one that put the body 0.34 m inside a dark oak
    # block on one frame of 746. A hall is also the right room: a
    # sawmill's headframe stands in a tall shed, not in a cave.
    #
    # Known and not fixed: **the ride itself is six flat frames of
    # plank wall.** A body on a ladder has its face against whatever the
    # ladder hangs on, and the thing it hangs on has to be solid or the
    # climb is refused, so the lens is jammed for about a second and a
    # half near the end of the level. Rendering the same seed with the
    # shell taken off gives the same six frames, so it is the ladder and
    # not the room. The only two levers are shortening the climb --
    # ``step_y`` is already the smallest that anchors, and ``rise`` is
    # frozen -- and exiting by a staircase instead, which costs seven of
    # this level's ten landings. It is also, for what it is worth,
    # exactly what the reference's own ladder levels look like: a dark
    # climb with a lit doorway at the top.
    n("rock", arc=2.8, step_y=0, hug=2.8, spread=1, confine=True,
      ceiling=3, shell="hall"),
    n("ladder", arc=2.4, step_y=3, kind="climb", climb_style="ladder",
      hug=2.6, pedestal_style="darkoak", spread=0, confine=True,
      deco="lamp", orbs=2),
], filler=[
    # The stacking ground, and it repeats: fall two blocks onto a log in
    # the water, walk the lit gangway between the piles, up onto the top
    # of the next pile, and off the end of it again. Lifts 1, 2 and 3,
    # which is the whole point of it -- the filler is most of what a
    # level shows, and the one that was here before was four landings
    # all at lift 1, which is the owner's "half the jumps are at ground
    # level" written down as a beat.
    #
    # The middle landing is the level's second ``walk``: a sawn board on
    # dark-oak trestles with a lantern on it and a beam over it, crossed
    # on foot rather than jumped. A walk wants its predecessor within
    # half a metre and inside 2.4 m of ground, which a slab one lift up
    # at 2.8 of arc is exactly; and it is the only non-hop verb reliable
    # enough to put in a loop. Without it this level measured 86% plain
    # hop against a rule of 85; with it, 83%. The lamp on it is the
    # route painted: the reference lights the place you are going to and
    # nothing else, and on eleven cells of open deck the lit board is
    # the only thing saying which way the yard runs.
    #
    # The loop seam is checked as a jump like any other and it is what
    # sets the opening arc: the last landing is a slab at surface 3.5
    # and the first stands at 2.0, so coming back round is a drop of one
    # and a half and wants a reach in that window. 4.4 has it, and stays
    # legal level and one block down as well, which is what the
    # ``spread`` on that node is there to use.
    #
    # No ``moat`` anywhere in here, and that is a rule rather than a
    # preference: the filler loops, and a second lap digs the ground out
    # from under the pedestals the first lap stood up -- 27,859 refusals
    # from one keyword, on the level that found it.
    ("stacks", [n("accent", arc=4.4, lift=3, spread=2, pedestal=False,
                  orbs=2),
                n("ground", arc=2.8, lift=3, form="slab", kind="walk",
                  spread=0, pedestal_style="darkoak", ceiling=3,
                  deco="lamp"),
                n("rock", arc=3.2, lift=3, spread=0,
                  pedestal_style="log", orbs=2)]),
])
