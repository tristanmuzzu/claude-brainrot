"""Level 24: THE ARCHIVE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# THE FLOODED STACKS. A hall of bookshelves on pale flagstones with a
# red runner painted down the middle of it, a bookshelf gateway to run
# through, water standing in the bay where the roof has let go, and oak
# reading galleries slung out over the drop.
#
# The old version was brown on brown: spruce ground, oak landings, oak
# beams, no liquid, no structure, three hall-shelled landings in a row
# that jammed the lens on 10% of frames, and an exit ladder that never
# fired and turned into **twelve landings of staircase out of twenty**
# -- so three quarters of the level was machinery and only two of its
# six beats were ever laid.
#
# What answers that:
#
# * **Value contrast, not another brown.** The flags are the lightest
#   thing in the lower half of the frame and the shelves and deepslate
#   are the darkest in the upper, which is how every reference frame is
#   built. The one saturated thing is the red runner.
# * **The route is painted.** Every wide stretch of a reference terrace
#   has a stripe of another floor material down the middle of it, and
#   this tower has never used it. Here it is the runner, and it is also
#   what the body walks along under the shelf overhangs -- so the same
#   material carries the level's colour, its wayfinding and its verb.
# * **The floor is hazard where it is wide.** This is the one level of
#   the pair that keeps ``plaza``, because a library *is* a hall -- so
#   it is broken instead: floor breaks, a pond cut through the reading
#   bay, and a gallery of floating slabs. A water moat digs a bowl a
#   walker can get into and not out of, which is the mechanism that
#   actually moves the walk number; the liquid on its own is only
#   weather. Three breaks and three ponds measured **4% covered**,
#   which is as wrong as a level you can stroll -- the real map sits at
#   46% and lets you walk its widest terrace for a few seconds.
# * **A gate to run through.** ``arch`` is the one blueprint that takes
#   the level's own roles rather than naming materials literally, so it
#   comes out as two bookshelf piers under an oak lintel with a lantern
#   on each -- a doorway between two stacks, and the course is steered
#   through it. The old level had no structure at all and held one on
#   screen for 0.0 s.
#
# **Short beats, and the level's identity in the first two.** This is
# the number that decides everything else here and it was measured
# rather than guessed. The exit climb's reserve is
# ``(need + 1) * 3.2 + gap + 5.4`` blocks of arc, where ``need`` is how
# far the body still has to climb *from wherever it happens to be
# standing* -- so on an eighty-metre terrace carrying a lock and a gate
# crossing there is room for about eight authored landings, and any
# beat that leaves the body low costs six more metres of reserve on top
# of that. Written as four long beats this level laid one and a half of
# them and spent 81% of itself on machinery.
#
# A beat is also truncated *in the middle*: the budget is in metres and
# whatever does not fit is dropped off the end. So the beats here are
# three and four nodes long rather than five or six, and each one puts
# its own point first -- the pond, the balcony -- because a beat that
# comes third gets its first node and often nothing else.
#
# The corollary is that **the descent has to be in the first beat**, and
# it is: you come in over the threshold and step straight down into the
# sunken hall. Everything after that climbs -- the bay, the galleries,
# the aisle -- and the exit is the highest thing in the level.
#
# The way out is the stair behind the shelves, on the level's own oak.
# A library's height gain is its staircase; the tower already exits by
# a climb far more often than the real map does (17 of 20 rebuilt levels
# against 7 of the real map's 43 legs), and a quiet ending is not a
# worse one. Left to the generated stair on purpose, too: it sizes
# itself to what is actually left to climb, where an authored one is a
# fixed number of steps against a starting height that moves.
LEVEL = Level("THE ARCHIVE", "library", rise=6, gap=2.8, exit="stair",
              band=8.5, profile="plaza", breaks=3, landmark="arch",
              ground="plaster", sub="deepslate", rock="bookshelf",
              accent="oak", glow="lantern", liquid="water",
              candy=("bookshelf", "oak"),
              props=("lanternpost", "torch", "pebbles"),
              sky=(126, 116, 132), dark=0.5,
              step=("oak", "hop"), beats=[
    # The threshold, and the level's descent in the same breath: a
    # lantern set flush in the flagstones on a rise, the head of the red
    # runner stepped onto on foot, the step down into the sunken hall,
    # and two metres of shelf tunnel. The palette changes completely at
    # that lantern -- violet mycelium and red caps in the hollow below,
    # pale stone and dark shelves here.
    #
    # The shell sits on the beat's last node, because a shell is painted
    # the moment its landing commits and its roof then refuses the arc
    # *out* of it.
    ("threshold", [n("glow", arc=3.0, lift=1, hug=3.0, form="slab",
                     spread=1, deco="lamp"),
                   n("wool_red", arc=2.9, lift=1, hug=3.0, form="slab",
                     kind="walk", spread=1),
                   n("ground", arc=2.4, lift=0, hug=3.0, form="floor",
                     kind="walk", spread=0, orbs=1),
                   n("bookshelf", arc=3.3, lift=1, hug=2.8, spread=0,
                     shell="tunnel", orbs=1)]),
    # The reading bay: a reading table, a stride under the shelf
    # overhang, up onto the stack end and along the top of it with the
    # flood standing in the aisle below.
    #
    # The **pond is on the beat's last node** and it began on its first.
    # A moat is painted the moment its landing commits and it digs a
    # radius-three bowl out of the ground -- which on a beat whose next
    # landing is two and a half metres away is the ground that landing
    # needed. It held this beat at 67% placed through four passes and
    # neither ``spread``, ``hug`` nor the lid was the cause.
    # This beat's landings keep their pedestals -- a stride *between two
    # cantilevered slabs* is a walk with nothing under either end, and
    # it was refused often enough to hold the beat at 75% placed. The
    # cantilever belongs on the gallery above, where it is arrived at by
    # a jump.
    #
    # The **walk is the second node**, and that ordering is measured
    # rather than aesthetic. A beat is truncated in the middle when the
    # budget runs out and this terrace only ever lays this beat's first
    # two landings, so whatever the level is about has to be in them.
    # Written with the balcony second and the walk third the whole level
    # came out at 87% plain hop; written this way it does not.
    #
    # And this walk carries **no ``ceiling``**, where the two in the
    # gallery and the filler do. A lid is a checked thing -- four free
    # cells three above the take-off -- and immediately downstream of a
    # moat, which digs the ground out from under them, it is refused
    # often enough to hold the beat at 67% placed. The other two lids
    # measure 100%.
    ("bay", [n("darkoak", arc=3.2, lift=1, hug=3.4, spread=1),
             n("wool_red", arc=2.4, lift=1, hug=3.4, kind="walk",
               spread=1),
             n("accent", arc=3.4, lift=2, hug=3.0, spread=1),
             n("wool_red", arc=2.4, lift=2, hug=3.0, kind="walk",
               spread=1, moat=True)]),
    # The upper gallery: the second oak balcony with nothing at all
    # under it, out at 4.0 over the hall with a pond dug in the floor
    # beneath and a lantern on the end of it, then back in against the
    # shelves and a last stride under the overhang. A run of floating
    # landings cannot be walked by construction, which is the cheapest
    # answer there is on a full floor -- and this is the level's high
    # point, which is where a high point belongs.
    ("gallery", [n("accent", arc=3.4, lift=3, hug=4.0, form="slab",
                   spread=0, pedestal=False, moat=True, deco="lamp",
                   orbs=1),
                 n("bookshelf", arc=3.4, lift=3, hug=3.0, spread=0),
                 n("wool_red", arc=2.4, lift=3, hug=3.0, kind="walk",
                   spread=0, ceiling=4, orbs=1)]),
], filler=[
    # If the terrace outlasts three beats: a shelf end, a stride under
    # the overhang, and a step down the aisle. It loops, so the seam
    # from its last landing back to its first is a jump too -- and it
    # stays at lift 2-3 on purpose. The exit stair is sized by what the
    # body still has to climb when it starts, so a lap that finishes on
    # the hall floor buys ten steps and one that finishes two tiers up
    # buys four. **No moat in here**: the filler loops, and the second
    # lap would dig away the ground the first lap's pedestals stand on.
    ("aisles", [n("bookshelf", arc=3.4, lift=3, hug=3.0, spread=0),
                n("wool_red", arc=2.4, lift=3, hug=3.0, kind="walk",
                  spread=0, ceiling=4),
                n("ground", arc=3.6, lift=2, hug=3.0, spread=0, orbs=1)]),
])
