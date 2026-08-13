"""Level 25: PUMPKIN ROWS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# **Last light on the pumpkin field, and the lit fruit is the route.** A
# ploughed headland with the drop hard outboard and the cliff a yard off
# your shoulder, water cut into the rows, a crop lid over half the
# landings, and the only saturated thing in any frame is a jack-o-lantern.
# You come out of THE ARCHIVE's brown reading room onto gold and orange
# and the palette changes completely at one glowing block.
#
# Seven things here are not free choices, and most of them cost a pass:
#
# * **``magma`` is the jack-o-lantern.** ``spiral._GLOWING`` is a
#   draw-time set of five names -- lantern, torch, glowstone, sealantern,
#   magma -- and nothing outside it lights its own cell. ``shroomlight``
#   and ``pumpkin`` are bright *textures* and emit nothing. Of the five,
#   only ``magma`` is orange (214, 118, 52), so the lit pumpkins, the
#   ``glow`` role, the lamp deco and half the treads of the way out are
#   all ``magma``: an orange cube that actually throws light, sitting a
#   shade darker than the unlit ``pumpkin`` (218, 126, 34) beside it.
# * **A level cannot be at night, and it took a pass to find out.** The
#   sky dome is built once per run from the *run's* palette
#   (``SkyDome(pal, seed, ...)``), so a level's own ``sky`` and ``dark``
#   never touch it: they own ``ring_light``, which is
#   ``mix(white, theme.sky, 0.35 + 0.45 * dark)`` -- the light everything
#   in the level is lit *by* -- and the fog it is mixed into. A lilac sky
#   at ``dark=0.35`` therefore reads as low warm light on the field with
#   whatever sky the run drew still bright above it, which is the
#   reference's own composition and not a night. Do not push it further:
#   at ``dark=0.5`` a fifth of the contact sheet came back solid black,
#   because a lid overhead *also* darkens -- see ``ceiling`` below.
# * **``hug`` is what stops the frame being sky.** Left unset,
#   ``_targets`` pulls a ledge course to the *outer* edge of its own
#   shelf, which points the lens over the drop: 57% of the view empty
#   with everything else on this level already in place. Hugged to three
#   metres -- the reference's own median distance to a wall -- the cliff
#   is in the frame on the core side for most of the run.
# * **The structure is a hop gate or there is no structure.** The old
#   version named ``scarecrow``, which is not in ``spiralplan.GATED``, and
#   an ungated landmark cannot reserve on a ledge at all -- measured 0.0 s
#   of anything held at 25 degrees. ``bell`` takes ``theme.rock`` for its
#   posts, so it builds as two hay stacks with an oak headstock over the
#   way through: the harvest bell at the end of the rows, and five blocks
#   of it directly over the lens.
# * **...and ``tree`` was measured against it and lost, on the row that
#   is easy to forget.** The oak is the bigger silhouette and it shows:
#   held at 25 degrees for 1.85 and 1.92 s on two seeds against the
#   bell's 1.43 and 1.48, and it took the lens-jam figure to zero. But
#   its trunk stands *off* the run at dr 2-3 and its canopy hangs at dy
#   5-6, clear above the lids, where the bell's two five-tall posts stand
#   either side of the way through -- so the empty-frame figure went
#   **54% to 60%** on the same seed and blew the one budget this level
#   had no room in. A structure you run *between* is worth more here than
#   a bigger one you run *under*.
# * **The descent is in the first half.** Off the top of the row into the
#   ploughed hollow, three blocks down and then two strides along the
#   bottom of the furrow; everything after that climbs, and the way out
#   is the highest thing in the level. A drop *after* a level's high
#   point reads as climb-then-fall and is what the last preview run was
#   rejected for.
# * **``ceiling`` is the cheapest overhead mass there is, and it is not
#   free.** It writes real cells three above the take-off, painted
#   ``pedestal_style`` or the level's rock, and the lens probe counts
#   them. But a lid within eight blocks of the head also makes
#   ``_indoor_want`` return 0.85, which takes 27% off every tint in the
#   frame -- so a level that lids every landing goes dark whatever its
#   ``dark`` says. Half the landings, and the light set for that.
# * **No moat in the filler.** It loops, and the second lap digs out the
#   ground the first lap's pedestals stand on.
LEVEL = Level("PUMPKIN ROWS", "farm", rise=4, gap=2.8, exit="stair",
              band=11.0, shelf=4.5, breaks=3, landmark="bell",
              ground="farmland", sub="coarse", rock="hay",
              accent="pumpkin", liquid="water", glow="magma",
              candy=("pumpkin", "hay"),
              props=("crop", "mcfence", "scarecrow", "lanternpost",
                     "grasstuft"),
              sky=(150, 112, 150), dark=0.35,
              step=("magma", "hop"), beats=[
    # The threshold: one lit pumpkin set flush on a rise in the ploughed
    # ground with its lamp on it, and two metres on, the field gate --
    # walked under a checked lid of pumpkin, because one impulse always
    # rises 1.25 m and a lintel low enough to read as a gate refuses
    # every jump.
    ("dusk", [n("magma", arc=3.2, lift=1, hug=3.2, spread=0, deco="lamp",
                orbs=1),
              n("coarse", arc=2.9, lift=1, hug=3.2, kind="walk", spread=0,
                ceiling=3, pedestal_style="pumpkin"),
              n("farmland", arc=2.9, lift=1, hug=3.4, kind="walk",
                spread=0)]),
    # The rows, and the whole idea of the level in one beat -- second
    # position, which is where a beat still gets laid whole. Two steps up
    # the drills between a dark pumpkin and a lit one, the three-block
    # fall off the headland into the ploughed hollow, a stride along the
    # bottom of the furrow, and back up onto a bale standing in the dug
    # irrigation.
    #
    # The rise and the drop are in the *same* beat on purpose: machinery
    # is inserted between beats and leaves the body back at lift 1, so a
    # fall written across a boundary is not a fall about half the time.
    #
    # A slime pad was built here and taken out again, and the measurement
    # is worth keeping. One fallen bale of slime at the foot of the fall,
    # written exactly to the recipe -- ``pedestal=False``, ``spread=1``,
    # a three-block drop over a 6.0 arc so the 0.84 fallback is still a
    # three-block drop -- placed on 6 of 24 runs and *fired* on 1. It
    # also cost the rest of the level two beats, because a five-node beat
    # spends the terrace the filler wanted. The reference's own footage
    # has no slime in 2,900 seconds; two reliable strides are worth more
    # than one pad that lands one run in twenty-four.
    ("rows", [n("pumpkin", arc=3.4, lift=2, hug=3.0, spread=0, radial=1.4,
                moat=True, ceiling=3, pedestal_style="hay"),
              n("hay", arc=2.9, lift=2, hug=3.2, kind="walk", spread=0,
                radial=-1.0),
              n("magma", arc=3.4, lift=3, hug=3.6, spread=0, radial=-1.4,
                deco="lamp", orbs=1),
              n("ground", arc=5.4, lift=0, hug=3.2, form="floor", orbs=2),
              n("coarse", arc=2.9, lift=0, hug=3.2, form="floor",
                kind="walk", spread=0),
              n("farmland", arc=2.9, lift=0, hug=3.4, form="floor",
                kind="walk", spread=0),
              n("hay", arc=3.4, lift=1, hug=3.2, spread=0, orbs=1)]),
], filler=[
    # The furrows, which is what the terrace plays once the script is
    # done -- and on a level that lays nine to twelve landings and only
    # four or five of them are the script, this is where the level's
    # voice actually lives. Bale, lit pumpkin, a stride under the rail,
    # and down onto the fruit.
    #
    # Two of the four are walked, and that is deliberate arithmetic
    # rather than atmosphere: the exit staircase is a third of this
    # level's landings and can only ever be hops, so the only place a
    # plain-hop share of 85% can be bought is the beat that repeats.
    # And there is no ``moat`` in here, because the loop's second lap
    # would dig away the first lap's footings.
    ("furrows", [n("hay", arc=3.4, lift=2, hug=3.0, spread=0, radial=1.2,
                   ceiling=3, pedestal_style="pumpkin", orbs=1),
                 n("magma", arc=2.9, lift=2, hug=3.0, kind="walk",
                   spread=0, deco="lamp"),
                 n("oak", arc=2.9, lift=2, hug=3.2, kind="walk", spread=0,
                   deco="lintel"),
                 n("farmland", arc=2.9, lift=2, hug=3.2, kind="walk",
                   spread=0),
                 n("pumpkin", arc=3.5, lift=1, hug=3.4, spread=0,
                   orbs=1)]),
    # The fruit store, the second half of the loop: in under its roof on
    # a stack of boards, across on foot past the lamp, and down onto the
    # last lit pumpkin. ``ceiling=5`` is a five-cell lid rather than a
    # three-cell one -- the store has a roof, not a lintel -- and it is
    # painted pumpkin, so what is over your head is the crop rather than
    # the cliff.
    #
    # It is a *filler* beat and not the third of the script because a
    # third beat is laid about once in two visits where the filler comes
    # round every time, and because both halves of this loop have to be
    # able to run twice: no ``moat`` anywhere in here, since the second
    # lap would dig away the first lap's footings.
    ("store", [n("oak", arc=3.4, lift=2, hug=3.0, spread=1, ceiling=5,
                 pedestal_style="pumpkin"),
               n("magma", arc=2.9, lift=2, hug=3.0, kind="walk", spread=0,
                 deco="lamp", orbs=1),
               n("hay", arc=2.9, lift=2, hug=3.2, kind="walk", spread=0),
               n("farmland", arc=2.9, lift=2, hug=3.4, kind="walk",
                 spread=0),
               n("pumpkin", arc=3.5, lift=1, hug=3.4, spread=0, orbs=1)]),
], exit_beats=[
    # Out up the bale stack, and the treads alternate hay and lit
    # pumpkin, so the way out of a dark level is a flight of lamps. A
    # stair and not a ladder: the climb is not this level's idea, and an
    # authored staircase is a quieter ending rather than a worse one.
    n("hay", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      deco="lamp"),
    n("magma", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("hay", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9, orbs=1),
    n("magma", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("hay", arc=2.9, step_y=1, hug=2.6, spread=0, deco="lamp", orbs=1),
])
