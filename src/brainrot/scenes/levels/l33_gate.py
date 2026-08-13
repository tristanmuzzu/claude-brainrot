"""Level 33: THE GATE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE GATE. The last level, and the one that hands the loop back to the
# meadow. A black gatehouse standing on a pale endstone causeway, and
# the level is a **run of doorways**: an amethyst sill with a molten
# beam over it, two strides through under the lids, a two-block fall
# into the court, a lamplit bay cut back into the cliff, the obsidian
# gate itself, and a black stair out. Nothing green, nothing white,
# nothing warm except the fire -- so THE WHITE STAIR behind (quartz,
# gold, a broad 13-block plaza) and THE GATEHOUSE ahead (grass, moss,
# oak, water) both read as a different world in one frame, and this one
# is the tightest corridor of the three at ``band=9.5``.
#
# **The doorways are the level's verb, and they are the only way this
# level could have one.** The exit stair is a quarter of every run and
# can only ever be hops; the lock and the gate crossing are hops; the
# roster is 94% plain hop. A ladder would fix the number and is exactly
# what the owner asked for less of -- 17 of the 20 rebuilt levels below
# already leave by a climb against the real map's 7 legs in 43. A
# ``walk`` is the other answer: it is the reference's own staple,
# "doorways and lintels you run under", it costs nothing, and
# ``ceiling=3`` over a walk leg is a real head-hitter the arc-clearance
# test **never refuses**, because a walk has no arc. So every stride
# here is lidded and each lid is a black or molten beam a metre over
# the head in the middle of the frame. Measured: hop 100% -> **78%**,
# walk 20%, with the exit still a stair.
#
# **``pedestal=False`` is the largest fidelity lever this engine has,
# and nothing says so.** Four landings here were placed as authored
# about 90% of the time with a pedestal and **100%** without it, over
# 24 runs, with no other change -- ``_targets`` silently returns nothing
# when a stack has no ground to stand on, which on a shelf that wobbles
# +/-1.3 around 4.5 is a lane or two of every level. THE GATE's design
# went from 92% placed to **99%** on that keyword alone. The cost is
# that a floating landing is a cube against sky, so it is spent on the
# stones and never on the causeway: the two ``form="floor"`` landings
# are the level's own ground and are what puts pale endstone in the
# bottom of the frame.
#
# **Three values, and obsidian is only the darkest of them.** Obsidian
# measures RGB (56,46,78) and this level's ring light multiplies it to
# about (34,26,54) -- a lens-filling black hole if it is what a landing
# is made of. The first draft was obsidian kerbs and it read as a
# silhouette of nothing. Pale endstone is the floor, purpur is the
# parkour, ``blackstone`` (70,64,74, neutral rather than violet) is the
# kerb and the terrace's cut face, and obsidian is kept for the four
# things that want to be a hard black shape: the gate, the lids, the
# plinths and the stair out.
#
# **The fire is a lid and a plinth, not a lake, and that is measured.**
# ``end`` has no liquid of its own and this is the one level with no
# daylight palette to fall back on, so the warm accent had to come from
# somewhere. ``moat=True`` writes about **five or six lava cells a run**
# here -- the disc is radius three, the shelf is four and a half, so
# most of it lands over the drop, and moving the node from ``hug`` 3.0
# to 2.4 did not change the count. (``docs/RULES.md`` §3 quotes ~35
# cells a moat; that is a ``plaza`` or ``channel`` number, not a
# ``ledge`` one.) What does put fire in the frame is ``pedestal_style``,
# which paints a node's plinth **and its ``ceiling`` lid**: magma over
# the sill, over the causeway and under the underway's step, lava under
# the filler's stone. The moats stay, because liquid on the walking
# line is the reference's most-used mechanic, but they are the garnish.
#
# ``dark`` and ``sky`` are lifted off the base theme on purpose. The
# ring light is ``mix(white, sky, 0.35 + 0.45 * dark)`` multiplied over
# everything, and ``end``'s own (46,38,66) at 0.62 measures a 48% grey
# cast -- against a bright sky dome that is a black hole in the sheet,
# and the old version of this level had four frames of near-black in
# twenty-eight. (78,62,118) at 0.50 is 60% and lilac: still
# unmistakably the End, and the obsidian stops being a shape with no
# faces.
LEVEL = Level("THE GATE", "end", rise=4, gap=3.0, exit="stair",
              band=9.5, shelf=4.5, breaks=3, landmark="totem",
              ground="endstone", sub="blackstone", rock="purpur",
              accent="obsidian", glow="amethyst", liquid="lava",
              dark=0.5, sky=(78, 62, 118),
              props=("endrod", "chorus", "pebbles", "lanternpost"),
              candy=("purpur", "amethyst"),
              step=("obsidian", "hop"), beats=[
    # The threshold, and the first two doorways. An amethyst block flush
    # in the floor with a lamp on it, a blackstone kerb, and two strides
    # through under a magma and an obsidian beam -- so the level is
    # roofed and lit inside its first second rather than opening on sky,
    # and the palette changes completely at one block with no blend.
    ("blacksill", [n("glow", arc=3.2, lift=1, form="slab", spread=0,
                     hug=2.6, deco="lamp", orbs=1),
                   n("sub", arc=3.0, lift=1, hug=2.6, spread=1),
                   n("rock", arc=2.9, lift=1, hug=2.6, kind="walk",
                     spread=0, ceiling=3, pedestal_style="magma",
                     orbs=1),
                   n("rock", arc=2.9, lift=1, hug=2.6, kind="walk",
                     spread=0, ceiling=3, pedestal=False)]),
    # The race, and the level's descent -- which is at about 60% of the
    # way through and never undone, because the exit stair is the
    # highest thing here and nothing after it goes down.
    #
    # **The rise and the drop are inside one beat.** Machinery is
    # inserted *between* script beats and leaves the body back at lift 1,
    # so a fall written across a beat boundary is a fall that is not
    # there about half the time. Two stones up under a lintel, then two
    # blocks down onto the causeway itself, and a stride along it under
    # a black lid with lava dug in beside the line.
    #
    # The opening node carries ``spread=1`` and the rest ``spread=0``:
    # a beat's *first* landing is placed from wherever the machinery
    # between beats left the body, so the tolerant height measures
    # better there; everything after it is a shape and wants the height
    # it was written at.
    ("race", [n("rock", arc=3.6, lift=1, hug=2.8, spread=1,
                pedestal=False, orbs=1),
              n("rock", arc=3.4, lift=2, hug=2.8, spread=0,
                pedestal=False, deco="lintel"),
              n("ground", arc=4.6, lift=0, form="floor", hug=2.8,
                spread=0, ceiling=3, pedestal_style="obsidian", orbs=2),
              n("ground", arc=2.6, lift=0, form="floor", hug=2.8,
                kind="walk", spread=0, ceiling=3, moat=True,
                pedestal_style="obsidian", orbs=1)]),
    # The underway: a lamplit bay cut back into the cliff, two metres of
    # pinch rather than a room -- the real map is fully enclosed 6% of
    # the way, in runs of about two metres. A ``grotto`` and not a
    # ``tunnel``: a tunnel walls both sides of a nine-and-a-half metre
    # band, where a grotto carves the core side only and leaves the drop
    # open. (Measured, the swap was worth about half a point of
    # lens-jammed frames, 6.2% to 5.7%; the rest of that figure is the
    # gate's own piers passing the lens, which is the gate working.)
    # The shell goes on the beat's **last** node, because a shell is
    # painted the moment its landing commits and its roof then refuses
    # the next arc of the same beat.
    ("underway", [n("rock", arc=3.2, lift=1, hug=2.6, spread=1,
                    pedestal=False, deco="lamp"),
                  n("rock", arc=3.2, lift=2, hug=2.6, spread=0,
                    pedestal_style="magma"),
                  n("rock", arc=2.9, lift=2, hug=2.6, kind="walk",
                    spread=0, ceiling=3, pedestal_style="obsidian"),
                  n("rock", arc=2.9, lift=2, hug=2.6, kind="walk",
                    spread=0, pedestal_style="blackstone",
                    shell="grotto", orbs=1)]),
    # The gate head: up onto the last plinth, a lidded hop across its
    # top, and the leap off it onto a purpur spur floating clear of the
    # ledge with the drop under it. This is the tongue that ends in air
    # -- the reference does not signpost an exit, it lets the geometry
    # say it.
    ("gatehead", [n("rock", arc=3.4, lift=3, hug=2.6, spread=1,
                    moat=True, pedestal_style="obsidian"),
                  n("rock", arc=3.2, lift=3, hug=2.8, spread=0,
                    ceiling=3, pedestal_style="obsidian"),
                  n("rock", arc=4.4, lift=2, hug=3.2, spread=1,
                    pedestal=False, ceiling=3,
                    pedestal_style="obsidian", orbs=2)]),
], filler=[
    # The character, for the runs where the terrace outlasts the script:
    # the endstone causeway itself under a molten beam, a purpur stone
    # on a cast of lava, a stride along the kerb, and a black step. It
    # falls two blocks to the causeway every lap -- the real map travels
    # eleven blocks vertically to gain four and does it by falling off
    # edges, which costs nothing.
    #
    # The loop seam is checked: the last landing is lift 2 and the first
    # is a floor landing, a two-block drop across 4.4 m, inside the -2
    # envelope (3.12-5.56 reach). And **no moat in a filler** -- the
    # second lap digs away the ground the first lap's pedestals stand on.
    ("causeway", [n("ground", arc=4.4, lift=0, form="floor", hug=2.8,
                    spread=0, ceiling=3, pedestal_style="magma",
                    orbs=1),
                  n("rock", arc=3.4, lift=1, hug=3.0, spread=0,
                    pedestal_style="lava"),
                  n("sub", arc=2.9, lift=1, hug=3.0, kind="walk",
                    spread=0, ceiling=3, pedestal_style="magma"),
                  n("rock", arc=3.2, lift=2, hug=2.6, spread=1,
                    pedestal_style="obsidian", orbs=1)]),
], exit_beats=[
    # Out up a black stair against the core wall, lit at the bottom and
    # at the top and nowhere in between -- every lamp in the reference
    # is at an end of something and doing a job. A stair and not a
    # ladder: this level's idea is the gate, not the climb, and a stair
    # on a themed footing is a quieter ending rather than a worse one.
    n("accent", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
      deco="lamp"),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
    n("accent", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
      orbs=1),
    n("rock", arc=3.0, step_y=1, hug=2.4, spread=0),
    n("accent", arc=2.9, step_y=1, hug=2.6, spread=0, deco="lamp",
      orbs=1),
])
