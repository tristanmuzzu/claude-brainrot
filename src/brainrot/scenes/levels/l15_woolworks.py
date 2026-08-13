"""Level 15: WOOLWORKS.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# The dyeworks. You come in through the door of the dye house onto a
# pink wool carpet; the vats are cut through the whole width of the
# floor with one bolt of colour standing in each, and the duckboard
# between them is walked rather than jumped; then a bale of slime
# throws you along the drying racks.
#
# The old version of this level was eight candy cubes hung in the sky
# over nothing -- 62% of its landings floated, half the frame was sky,
# and "rainbow" was the only thing it said. This one puts the colour
# on the ground, where the reference keeps a level's identity, and
# hangs the parkour on things that stand in it.
#
# Five things about the shape were measured rather than chosen:
#
# * A beat is offered ten to twenty metres and is cut to fit, and the
#   budget *recovers* between beats -- so three-node beats are the
#   unit. A six-node beat measured as one to three landings, and its
#   tail, which is where the showpiece was, never once played.
#   Everything this level is about is inside the first three beats;
#   the last two are for the longer terraces higher up the tower.
# * A beat's first landing must be reachable from wherever the
#   *previous* beat stopped, since beats truncate mid-way and the
#   machinery between them lands where it likes. Every beat here opens
#   at lift 1 or 2, within one block of anything before it.
# * ``kind="walk"`` needs its predecessor within half a block, so it is
#   never the first node of a beat. Second, it always fires. It is
#   also the cheapest non-hop there is -- two metres of terrace, at
#   sprint speed, and the only leg a doorway can use.
# * The rise and the drop live in the *same* beat. Written across a
#   beat boundary the drop silently becomes a level hop, because the
#   machinery in between puts the body back on the floor -- and the
#   beat still reports as placed.
# * A bounce is fed by the fall onto the pad. Off a one-block drop it
#   will carry the body *along* but not up: the +1 version of this
#   beat placed its pad twenty-two times and fired the bounce zero
#   times, silently, while reading as 100% placed.
LEVEL = Level("WOOLWORKS", "rainbow", rise=4, gap=2.4, exit="bubble",
              band=9.0, shelf=4.0, profile="ledge", breaks=3,
              landmark="stripes",
              # Eleven materials, one committed hue: pink underfoot,
              # purple for the painted route and for the cut face at
              # the rim, timber for everything the works is built of,
              # and the bolts in every other colour.
              ground="wool_pink", sub="wool_purple", rock="oak",
              accent="wool_yellow", glow="glowstone", liquid="water",
              props=("mcfence", "lanternpost", "torch", "pebbles"),
              step=("wool_purple", "hop"), beats=[
    # The threshold, and the level's one interior: a lit slab set flush
    # in the floor on the rise, stepped off on foot through the dye
    # house's door. The palette changes completely at that slab --
    # gravel and plaster in the belfry below, wool from here.
    ("sill", [n("glowstone", arc=3.0, lift=1, form="slab", spread=1),
              n("oak", arc=2.9, lift=1, kind="walk", spread=1,
                shell="tunnel"),
              n("wool_purple", arc=2.85, lift=1, kind="walk", spread=1,
                orbs=1)]),
    # The vat floor: water cut through the whole width of the shelf
    # with a bolt of wool standing in each vat, and the duckboard
    # walked between them. The reference's answer to ground too wide
    # to be a course, and the level's idea.
    ("vats", [n("wool_red", arc=3.1, lift=1, spread=1, moat=True),
              n("oak", arc=2.85, lift=1, kind="walk", spread=1),
              n("wool_blue", arc=3.2, lift=1, spread=1, moat=True,
                orbs=1),
              n("oak", arc=2.85, lift=1, kind="walk", spread=1)]),
    # The showpiece and the level's drop: up onto the stacked bales,
    # off the top onto the slime bolt a block below, and thrown down
    # the works on the bounce.
    ("bales", [n("wool_purple", arc=2.9, lift=2, spread=1),
               n("slime", arc=3.6, lift=1, form="slime", spread=0,
                 pedestal_style="wool_lime", orbs=1),
               n("wool_yellow", arc=3.6, lift=1, kind="bounce",
                 spread=1, orbs=3)]),
    # The drying racks, under the beams, and down into the last vat.
    ("racks", [n("wool_orange", arc=3.4, lift=2, spread=1, ceiling=2),
               n("oak", arc=2.85, lift=2, kind="walk", spread=1),
               n("wool_lime", arc=3.2, lift=1, spread=1, moat=True,
                 orbs=1)]),
    # The selvedge: the ledge narrows to a tongue and ends in air. The
    # reference does not signpost an exit; it lets geometry say it.
    ("selvedge", [n("wool_orange", arc=3.4, lift=1, spread=1),
                  n("oak", arc=3.0, lift=1, form="slab", spread=1,
                    radial=1.4, orbs=1)]),
], filler=[
    # The character, not the surprise: another vat, another plank,
    # another bolt. It opens at lift 1, within half a block of the slab
    # the script ends on and within one of anywhere else the level can
    # leave the body, and it loops, so the seam back to its own first
    # landing is a jump too.
    ("dyeing", [n("wool_lime", arc=3.4, lift=1, spread=1, moat=True),
                n("oak", arc=2.85, lift=1, kind="walk", spread=1,
                  orbs=1),
                n("wool_orange", arc=3.0, lift=2, spread=1)]),
])
