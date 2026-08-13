"""Level 11: THE CRUCIBLE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE FOUNDRY. The tower's smelting gallery: a black casting floor cut
# into the cliff, a lava runner poured across it and stepped over, an
# obsidian furnace gate you run through, a slag pad you drop into its
# pool onto, and a netherbrick flue you climb out of on a ladder.
#
# Everything here hugs the core at 2.6-3.6 and the drop is off the
# other shoulder. That is the *groove* -- rock within four metres on
# one side on 71% of the real map's samples -- and it is the one thing
# no level of this tower was doing: left unhugged, a ledge level is
# pulled to the outer edge of its own shelf (``_targets``, ``COURSE_OUT``)
# and then frames as sky.
#
# The script is deliberately short and its arcs deliberately near three
# metres. This terrace lays about a dozen landings before the climb
# reserve takes the rest, and the level's two inserted machinery
# features -- the lock across its break and the crossing through the
# totem -- take a good half of those; a long script is a design whose
# last two thirds is never built, which is exactly what stood here.
LEVEL = Level("THE CRUCIBLE", "nether", rise=5, gap=3.0, exit="ladder",
              band=9.0, profile="ledge", shelf=5.0, breaks=2,
              landmark="totem",
              # Fourteen materials, not three: the floor is what a level
              # is recognised by. Black casting floor, netherrack in the
              # cut face at the rim, netherbrick for everything built,
              # magma for the hot marks, glowstone for the light (magma
              # is too dim to find a landing by) and lava for the runner.
              ground="blackstone", sub="netherrack", rock="netherbrick",
              accent="magma", glow="glowstone", liquid="lava",
              props=("netherfungus", "deadbush", "chain", "torch"),
              step=("blackstone", "hop"), beats=[
    # ONE beat, and that is the whole design of this level.
    #
    # A level of this tower lays about ten landings, and the climb out
    # takes four of them even with the ladder while the lock and the
    # gate crossing take two more. So the threshold and the showpiece
    # cannot be separate beats: beats are separated by that machinery,
    # which arrives at its own height, and a beat whose first landing
    # asks for lift 2 is asking for a two-block rise a third of the time
    # and is refused -- measured, 2 of 6 placed as authored, with the
    # fall and the bounce behind it unravelling too. Written as one beat
    # the chain is internal and every link is a rise of one.
    #
    # Four landings, because four is what there is. A six-landing
    # version of this beat was clipped short of its own slag pad on
    # every pass -- the terrace runs out, and a showpiece written past
    # the fourth landing of this level is a showpiece nobody sees.
    #
    # What it is: an emissive sill flush in the floor, a step up onto
    # the furnace under a beam, a long fall out into the lava pool onto
    # the slag pad, and a step back up onto the brick.
    #
    # That last landing is a plain hop and **not** a ``bounce``, and the
    # reason is measured rather than chosen. A bounce is fed by the
    # impact of the fall onto the pad, and every one-block fall written
    # here -- at 4.4 m of arc and at 5.4 -- was refused with ``no move:
    # bounce`` on every candidate at every height, so it fell through to
    # an ordinary hop that *reads as placed* and is not the move that
    # was written. REEF GARDEN's bounce, off a two-block fall, fires.
    # A two-block fall needs one more rising step and this beat is
    # already being clipped to three of its four landings.
    #
    # Only the pad carries the ``moat``. Two moats in one beat dig each
    # other's ground away and the step measured 33% placed with one on
    # it against 100% without.
    #
    # Every arc here is written at the **middle** of its rise's band and
    # not near an end of it. A +1 reaches 2.00-3.10 stand-point to
    # stand-point and a -1 reaches 2.35-4.98; the lattice moves a
    # placed reach by up to half a metre either way, so an arc aimed at
    # 2.9 of a +1 or 4.7 of a -1 falls outside about a third of the
    # time and is quietly recovered. Aimed at 2.55 and 3.65 it does not.
    ("forge", [n("glow", arc=3.0, lift=1, hug=3.2, spread=1, deco="lamp",
                 orbs=1),
               n("accent", arc=3.3, lift=2, hug=3.2, spread=0, ceiling=2,
                 orbs=1),
               n("slime", arc=4.3, lift=1, hug=3.6, form="slime", spread=0,
                 moat=True, pedestal_style="netherbrick"),
               n("rock", arc=3.3, lift=2, hug=3.6, spread=1, orbs=3)]),
    # The runner: slag standing in a lava cut through the level's own
    # ground, the middle block a stride from the last rather than a
    # jump. Lava and water are the reference's mechanic -- 26 and 20 of
    # its 43 levels.
    ("cast", [n("rock", arc=4.4, lift=1, hug=2.8, spread=1, moat=True),
              n("accent", arc=2.9, lift=1, hug=2.8, kind="walk", spread=0,
                moat=True),
              n("rock", arc=3.4, lift=1, hug=3.8, spread=1, moat=True,
                orbs=1)]),
    # The vault: a two-metre pinch pressed against the core, not a room.
    # The real map is fully enclosed 6% of the way, in runs of two
    # metres, so one short tunnel is the right amount of interior for a
    # level and a level that is a tunnel throughout is as wrong as one
    # that is an open plate.
    ("vault", [n("rock", arc=3.3, lift=2, hug=2.6, spread=0,
                 shell="tunnel"),
               n("rock", arc=3.5, lift=2, hug=2.6, spread=0,
                 shell="tunnel", orbs=1)]),
], filler=[
    # The character, repeated: down onto the casting floor itself and
    # across the soul sand, which a body walks at 2.5 m/s against a
    # normal 5.6 -- a slow beat that reads as one. This is also where
    # the level goes *down*: 36 of the real map's 43 descend somewhere,
    # and they do it by falling off an edge rather than by jumping. No
    # moat in here: a filler that digs its own liquid takes away the
    # ground the last loop's pedestals are standing on.
    ("tap", [n("ground", arc=4.4, lift=0, hug=2.8, form="floor", spread=0,
               orbs=1),
             n("soulsand", arc=3.5, lift=1, hug=2.6, spread=1),
             n("soulsand", arc=2.9, lift=1, hug=2.6, kind="walk", spread=0,
               orbs=1)]),
], exit_beats=[
    # Out through the flue. The generated ladder climb hangs its rungs
    # on a bare block at the lens and a second and a half of the strip
    # is then brown; the same climb inside ``shell="shaft"`` is a
    # chimney of the level's own brick with a lamp at its foot, which is
    # what the reference's one ladder level actually looks like. If
    # either landing is refused the generated staircase takes over
    # underneath, which is the reason to write only two.
    n("rock", arc=3.0, lift=1, hug=2.2, spread=2, confine=True,
      deco="lamp"),
    n("blackstone", arc=2.4, step_y=7, kind="climb", climb_style="ladder",
      hug=2.0, pedestal=False, spread=0, shell="shaft", orbs=2),
])
