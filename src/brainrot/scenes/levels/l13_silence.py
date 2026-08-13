"""Level 13: THE SILENCE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A drowned sculk gallery bored into the cliff. You go *inside* the
# rock: black floor, black water, amethyst the only light, an obsidian
# gate across the middle of it, and a sump you drop into and are thrown
# straight back out of.
#
# What it is answering. The level this replaces was one-cell sculk
# blocks hung over the drop with nothing else in the frame -- measured,
# 61% of the view was empty sky. Sky is the one thing the deep dark
# cannot be. So the course keeps to a three-and-a-half-cell shelf and
# carries a roof, a lid or a lamp the whole way, which is the groove
# the reference is in for 98% of its length: rock a few metres inboard,
# the drop outboard, something solid overhead.
#
# **The sump is the fifth landing and it is in the filler too, and
# that is deliberate.** A level lays about six of the design's landings
# before the machinery takes over, so everything past the fifth is
# written and never seen -- but the filler repeats. The slime pad and
# the bounce off it are the only non-hop verb in the level's body, so
# they go where they will actually fire, twice.
#
# **Three things about ``shell`` that are not written down anywhere**,
# each of which cost a measured pass here:
#
# * A shell's *walls* only stand where the terrain gives them a footing,
#   so only a beat at ``lift=1`` is a corridor; higher up you get the
#   roof and open sides.
# * A walled bay puts solid rock in the two cells either side of the
#   move, four high, so the landing *after* one has to stay in the
#   corridor. Shelling the doorway at lift 1 and stepping the next beat
#   up to lift 2 put its landings in the wall and took that beat from
#   100% placed to 62%.
# * And a ``kind="walk"`` node is never first in a beat: beats are
#   separated by machinery at an arbitrary height and a walk needs its
#   predecessor within half a metre.
#
# And one about the ground: **the shelf is 3.5 cells and the band 8.0
# because the exit climb needs them to be.** At shelf 5.0 the course
# drifts outboard, the ladder out of the level loses its lane, and
# emergency placements went from one in eight runs to fifteen.
LEVEL = Level("THE SILENCE", "deepdark", rise=8, gap=3.0, exit="ladder",
              band=8.0, shelf=3.5, profile="ledge", breaks=5,
              landmark="cabin",
              ground="sculk", sub="deepslate", rock="blackstone",
              accent="sculkvein", glow="amethyst", liquid="water",
              step=("deepslate", "hop"),
              props=("pebbles", "dripstone", "chain", "vinehang"),
              beats=[
    # The threshold: one lit block flush in the floor on a rise, and
    # then the door, which is the mouth of the gallery.
    ("threshold", [n("amethyst", arc=3.2, lift=1, spread=1, deco="lamp",
                     orbs=1),
                   n("sculk", arc=2.3, lift=1, kind="walk", spread=0,
                     shell="tunnel")]),
    # Inside: deepslate walls and roof, and a lamp in one of them.
    ("gallery", [n("blackstone", arc=3.3, lift=1, spread=0,
                   shell="tunnel"),
                 n("sculk", arc=2.3, lift=1, kind="walk", spread=0,
                   shell="tunnel", deco="lamp")]),
    # The level's one trick, and it is the fifth landing because a
    # level only lays about six of the design's before the machinery
    # takes over. **The step up and the drop off it are in the same
    # beat on purpose:** machinery is inserted between beats and leaves
    # the body back at lift 1, so a drop written as the first node of a
    # beat is not a drop, the pad is landed on too slowly to throw
    # anything, and the bounce silently becomes a hop.
    ("sump", [n("deepslate", arc=3.2, lift=2, spread=0, ceiling=2),
              n("slime", arc=5.2, lift=1, form="slime", spread=0,
                pedestal_style="deepslate", moat=True),
              n("sculkvein", arc=3.3, lift=2, kind="bounce", spread=1,
                orbs=2)]),
    # Up onto the ribs, under a beam.
    ("brink", [n("deepslate", arc=3.2, lift=3, spread=0, ceiling=2),
               n("sculkvein", arc=3.2, lift=4, spread=0, deco="post",
                 orbs=1)]),
    # Back under the rock, where it closes in and you walk the narrow
    # part.
    ("vault", [n("deepslate", arc=4.6, lift=1, spread=0, shell="cave"),
               n("sculk", arc=2.3, lift=1, kind="walk", spread=0,
                 shell="cave", orbs=1)]),
    # Out along a flooded ledge.
    ("cistern", [n("calcite", arc=3.4, lift=1, spread=0, moat=True),
                 n("deepslate", arc=3.5, lift=1, spread=0, moat=True,
                   orbs=1)]),
], filler=[
    # The character *and* the trick again, because this is the part
    # that repeats: a roofed bay with its lamp, a doorway, the pad in
    # the water, the bounce out.
    ("gloom", [n("slime", arc=4.9, lift=1, form="slime", spread=0,
                 pedestal_style="deepslate", moat=True),
               n("sculkvein", arc=3.3, lift=2, kind="bounce", spread=1,
                 orbs=2),
               n("blackstone", arc=3.3, lift=2, spread=0,
                 shell="tunnel", deco="lamp"),
               n("sculk", arc=2.3, lift=2, kind="walk", spread=0,
                 ceiling=2)]),
])
