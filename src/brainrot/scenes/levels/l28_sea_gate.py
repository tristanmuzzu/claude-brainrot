"""Level 28: THE SEA GATE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A drowned causeway through a monument gate.
#
# The idea in one line: the sea has come in over the terrace, and you
# cross it on the monument's own piers -- past a lit gold marker, through
# a lamplit bay cut into the cliff, and out along the broken causeway.
#
# The old one was a **plaza**: a full floor twelve blocks wide, unbroken
# for the whole eighty-two metres of the level. The blueprint's plan view
# was one continuous grey plate from end to end, which is the thing the
# owner has rejected three times in a sentence -- *you can just run past
# half the obstacles*. It measured 45% covered by a no-jump walker and
# 58% at worst, inside the rule only by accident, on 25% designed content
# and 100% plain hop.
#
# It is a ``ledge`` now: a shelf against the core with the drop genuinely
# outboard, and moats cut into the shelf on top of that. The plan view is
# three islands with real water and real holes between them.
#
# **The shelf is six blocks and not four, and that one number is most of
# this level's empty frame.** The owner picked it out of a contact sheet as
# a couple of cubes against a pale wash, and the rule tightened to *under
# 48% of the view empty*. At ``shelf=4.0`` with every landing hugged
# 3.2-3.8 the body ran along the outer edge of its own shelf with the rim
# half a block away, so the whole lower-outboard half of the ray fan flew
# off into the sea: **51.0% empty over eight seeds**. Widening the shelf to
# six, pulling every hug in by about 0.6 so the body stands *mid*-shelf,
# and putting a checked ``ceiling`` over the arcs of all four beats gives
# **47.4%** -- and the lens stops being jammed as well (4.3% -> 1.7%),
# because the wall that used to be at the lens is now a shelf's width away.
# The bill is the walker, 32% -> 38% against a limit of 55, which is what
# the third break is doing here; the reference's own number is 46%.
#
# The palette is the other half of it. Prismarine on prismarine is one
# value and reads as a teal plate, so the *accent is gold* -- the
# monument's own block, and the one warm thing in a cold level. Six roles
# set, four literals on top (sand, coral, calcite, dark prismarine), four
# props. Every light here is doing a job: the threshold lantern and the
# gold marker at the mouth of the bay. There is no ambient decorative
# lighting anywhere in the reference and there is none here.
#
# Against DUST DEVILS below (hot orange, band 9.5, dry, a tight canyon)
# and THE CORNICE above (white snow, band 8.5, an exposed rim) this is
# dark blue-green, the widest band of the three, half of it standing in
# water, and the only one of the three with a lamplit interior in it.
#
# Things here that only the per-beat table would tell you:
#
# * **The threshold lantern carries no moat**, and that one keyword was
#   eight points of the beat's fidelity: a moat digs a radius-three disc
#   the moment its landing commits, and the stride onto the sand bar
#   2.9 m later lands *inside the hole*. The water is in the nave, where
#   the jump onto it is long enough to clear the bowl.
# * **The interior is a ``grotto``, not a ``hall``.** A hall or a tunnel
#   on a *ledge* grows its walls only where the terrain gives them a
#   footing, which on a shelf is the core side -- so it stands a wall
#   right beside the lens and jammed it on 7% of frames, against 0% on
#   the plaza it replaced. A grotto is carved *into* the cliff instead:
#   same two-metre pinch, same lid, and it takes rock away rather than
#   adding it.
# * **The level ends at lift 3 on purpose.** The exit staircase is one
#   landing per block and ``need`` is measured from wherever the body is
#   when the climb triggers, so a level that finishes on its own high
#   ground hands the machinery a two-step job instead of a five-step one
#   -- and every frame of that staircase is sky.
# * **The arch is a hop gate**, the only kind that reserves on a ledge:
#   the walk gates (watchtower, windmill, cabin) want five supported
#   cells across the corridor and are refused on every bearing here.
# * **A ``ceiling`` is a one-cell beam along the arc, not a lid across the
#   corridor**, and that is why every beat here carries ``ceiling=5``
#   rather than one or two beats carrying a shell. ``_ceiling_cells``
#   spreads ``n`` cells along the *direction of travel* over the middle of
#   the jump, so five of them roof nearly the whole arc in the one column
#   of the ray fan that is looking where you are going -- and chained from
#   beat to beat they read as the lintels of a sea wall. A ``shell`` roof
#   is five cells wide but is punched out over the apex of every hop,
#   because the body's head sweeps the same cell the roof wants; it only
#   survives whole over a ``walk``.
# * **The causeway's middle landing is a ``walk``.** It is the level's
#   only non-hop besides the two strides, it sits at position two of the
#   beat where truncation still reaches it, and it is what keeps the hop
#   share from rising when the third break eats a filler lap: 90% -> 89%.
#   A ``shell="tunnel"`` on it was tried and refused the +1 hop out of it,
#   taking the beat from 80% to 73%; the ``ceiling`` alone does not.
LEVEL = Level("THE SEA GATE", "prismarine", rise=5, gap=2.8, exit="stair",
              band=12.0, profile="ledge", shelf=6.0, breaks=3,
              landmark="watchtower",
              ground="prismarine", sub="darkprismarine", rock="prismarine",
              accent="gold", glow="sealantern", liquid="water",
              candy=("sealantern", "gold"),
              props=("lilypad", "coralfan", "pebbles", "lanternpost"),
              sky=(96, 158, 168),
              step=("darkprismarine", "hop"), beats=[
    # The threshold: a sea lantern flush in the floor on a rise, a stride
    # onto the sand bar the tide has left, under the lintel of the old
    # sea wall -- and then the drop into the flooded court. The palette
    # changes completely at that lantern: red sand to dark teal in one
    # frame.
    #
    # **The threshold is written at lift 1 and that is the whole of why
    # it places.** Machinery is inserted between beats and leaves the body
    # back at lift 1, so a first node asking for lift 2 is asking for a
    # rise it only sometimes gets -- and the ``walk`` after it then needs
    # its predecessor within half a block and does not have it. Measured
    # on this beat alone: lift 2 with one walk, 67%; lift 2 with two,
    # 50%; the same beat at lift 1 with one, below.
    ("tideline", [n("glow", arc=3.2, lift=1, hug=2.8, spread=1,
                    deco="lamp", ceiling=5, orbs=1),
                  n("sand", arc=2.9, lift=1, hug=2.8, kind="walk",
                    spread=0, ceiling=5),
                  n("prismarine", arc=3.4, lift=2, hug=3.0, spread=0,
                    ceiling=5, orbs=1),
                  n("ground", arc=4.6, lift=0, hug=3.0, form="floor",
                    spread=0, ceiling=5, orbs=1)]),
    # The nave, and the showpiece, about half way: a pier standing in the
    # water, the gold marker over it under a checked lid, a stride, and
    # the lamplit bay cut into the cliff. The rise and the water are
    # inside one beat on purpose -- written across a beat boundary the
    # machinery lands the body back at lift 1 and the moat digs nothing.
    #
    # **The node a ``walk`` steps off is pinned at the same ``lift`` as
    # the tolerant one before it**, and that is the whole recipe. A beat's
    # first node has to carry ``spread`` because it is placed from
    # wherever the machinery left the body; the node after it therefore
    # sits a block high or low about a fifth of the time. Asking for
    # ``lift + 1`` there is asking for a rise of two on that fifth, which
    # nothing can make -- this beat measured 78%. Asking for the *same*
    # lift is a hop of +1, level or -1, all three of which are legal, and
    # the walk after it then has its predecessor at a known height.
    ("nave", [n("darkprismarine", arc=3.5, lift=1, hug=2.6, spread=1,
                moat=True, ceiling=5, orbs=1),
              n("accent", arc=3.4, lift=1, hug=2.6, spread=0, ceiling=5,
                deco="lamp"),
              n("prismarine", arc=2.9, lift=1, hug=2.6, kind="walk",
                spread=0, ceiling=5),
              n("darkprismarine", arc=3.3, lift=1, hug=3.0, spread=0,
                shell="grotto", ceiling=5, orbs=1)]),
    # Out along the broken causeway: a half-height slab of the monument's
    # facing stone -- stairs and slabs are the reference's commonest
    # non-cube form by a wide margin and this tower has almost none -- a
    # calcite step, and a coral-crusted pier hung out over the water with
    # nothing under it. It ends on the level's high ground.
    #
    # There is no ``form="slab"`` here and the reason is worth recording
    # honestly, because the first reading of it was wrong. A slab on this
    # level came with 15 frames of "body 0.75 m inside the cone" and 7% of
    # frames with the lens jammed, and dropping the slab took both to
    # zero -- but a later revision with no slab at all brought both back
    # at exactly the same magnitude. So the slab is **not** the cause: the
    # camera check is one seed's run, the world is re-rolled by *any*
    # change to any node, and the residue is machinery -- the lock's
    # island, the landmark crossing, the exit staircase -- not the design.
    # Read that row as noisy at this sample size and check it twice before
    # attributing it to a keyword.
    ("causeway", [n("prismarine", arc=3.2, lift=2, hug=3.2, spread=1),
                  n("calcite", arc=2.9, lift=2, hug=3.0, kind="walk",
                    spread=0, ceiling=5),
                  n("coral_blue", arc=3.2, lift=3, hug=3.0, spread=0,
                    pedestal=False, deco="post", ceiling=5, orbs=1)]),
], filler=[
    # The character, repeated: a long drop back into the flooded court, a
    # wade between two piers, the gold marker again under its lid, and a
    # coral stack standing free out towards the rim. Every lap ends at
    # lift 3, so the climb out is asked for from the top of the level.
    #
    # No moat in here. The filler loops, and the second lap digs away the
    # ground the first lap's pedestals are standing on.
    ("piers", [n("darkprismarine", arc=3.9, lift=1, hug=2.6, spread=2,
                 ceiling=5, orbs=1),
               n("prismarine", arc=2.9, lift=1, hug=2.6, kind="walk",
                 spread=0, ceiling=5),
               n("accent", arc=3.5, lift=2, hug=2.6, spread=0,
                 ceiling=5),
               n("coral_blue", arc=3.4, lift=3, hug=3.2, spread=0,
                 pedestal=False, ceiling=5, orbs=1)]),
])
