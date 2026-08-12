"""The hand-built tower: twenty-four designed levels, climbed in order.

This module is :mod:`brainrot.scenes.spiralplan` with one thing taken away and
one thing put in its place. Taken away: the weighted table that chose what the
next stretch of course would be. Put in its place: a page of levels, each
written down landing by landing. Everything else -- the building, vanilla's
motion numbers, the occupancy ledger, the reservations, the pedestals, the
terrain painting, the props, the exit climb and every check that says a landing
is legal -- is the generator's and is reused unchanged. ``docs/TOWER.md`` is
the design; this file is that design as data.

**Authored intent, mechanical placement, verified physics.** The three layers
are the whole idea and it is worth being precise about which is which.

*Authored* is every landing: its material, how far along the terrace, how far
in or out of the corridor, how high off the floor, what shape it is, what is
underneath it and whether there is a lid over the jump that reaches it.
Nothing here is rolled.

*Mechanical* is the lattice. The tower is round and the world is whole cells,
so "3.6 further along and 1.2 further out" is not a cell; :meth:`Course._targets`
resolves it to the nearest ones exactly as it always did. That is not
generation -- the shape is authored and the machine only picks which cell is
closest to what was asked for.

*Verified* is :meth:`Course._attempt`, untouched. An authored jump no body can
make is refused exactly as a generated one would be, and ``tools/tower_probe.py``
says which. **A level that measures badly is a level designed badly**, and the
fix belongs in the table below rather than in a tolerance.

Three constraints bind every design here and all three come from the physics
rather than from taste:

* **Nothing rises two blocks in one ballistic move.** Consecutive ``lift``
  values on hops may go up by at most one. Height is gained by a flight of
  ones, or by a verb that is not a jump.
* **The reach is fixed and small.** Stand-point to stand-point, a level jump
  is at most 4.26 m and an ``arc`` is about 0.68 longer than the jump it
  produces, so an arc over about 4.9 has no answer. Rising one costs a metre
  of that; dropping buys about one back per block dropped.
* **``arc`` is along the corridor and ``radial`` is across it**, so a landing
  offset both ways is further away than its arc says. The distance is the
  hypotenuse and the checker measures the hypotenuse.
"""

from __future__ import annotations

from . import spiralplan as sp
from .spiralplan import (  # noqa: F401  -- the renderer reads these off the plan
    HANGING,
    PROP_BUDGET,
    PROP_KINDS,
    THEMES,
    TRAIL,
    Section,
    Theme,
)

#: How many landings generation keeps in front of the body, and higher than the
#: generated tower's sixteen because the terraces are half as long again. A
#: section is dressed when the *generator* leaves it, so with sixteen the body
#: was standing in an undressed section a third of the time and the terraces
#: came back swept. Read by the renderer off the plan module.
AHEAD = 26

#: Material roles a level may name instead of a material. Writing ``"rock"``
#: rather than ``"cobble"`` is what lets one design be re-skinned by giving its
#: level a different theme, and what keeps a level readable as a *shape*.
ROLES = frozenset(("ground", "sub", "rock", "accent", "glow", "liquid"))


def n(style: str = "rock", **kw) -> dict:
    """One authored landing: a role or material, and the node's own arguments.

    Thin on purpose. The keywords are :meth:`Course._node`'s own, so the design
    below is written in the same vocabulary the generator's features were and
    anything expressible there is expressible here.
    """
    return {"style": style, **kw}


class Level:
    """One designed level: a place, a shape, and the way out of it.

    ``beats`` is the level in order. Each beat is ``(name, [node, ...])`` and
    is laid whole or not at all, exactly as a generated feature was -- a beat
    is a sentence and half of one says something else. The name is what the
    probe and the HUD call that stretch.

    ``filler`` is what repeats if the terrace outlasts the script. Every level
    has one, because how much terrace a level has depends on how far up the
    tower it is (the cone flares) and on how tall the level above it is, and a
    design that assumed a fixed length would run out on the wide turns. Put the
    level's *character* in the filler, not its surprise: the filler is what a
    viewer sees twice.

    ``rise`` is how far above this level the next one sits, and it is a design
    decision rather than a random one -- a three-block rise is a step between
    two rooms and an eight-block rise is a shaft. ``gap`` is the chasm at the
    end, in blocks.

    ``exit`` is *a kind*, not coordinates: ``stair``, ``ladder``, ``vine`` or
    ``bubble``. The climb out is the one move a run cannot do without, and the
    generator's version of it is the most-tested code in the project. Authoring
    the shape of it and not its arithmetic keeps that guarantee.

    ``skin`` re-skins the base theme for this level. Two levels may share a
    theme -- there are twenty-four levels and fifteen themes -- and this is
    what stops the second one looking like the first.
    """

    __slots__ = ("beats", "exit", "filler", "gap", "name", "rise", "skin",
                 "theme")

    def __init__(self, name: str, theme: str, rise: int, gap: float,
                 exit: str, beats, filler=(), **skin) -> None:
        self.name = name
        self.theme = theme
        self.rise = rise
        self.gap = gap
        self.exit = exit
        self.beats = tuple(beats)
        #: Defaults to the last two beats. A level whose tail is its best
        #: material usually wants exactly that, and saying so every time is
        #: noise.
        self.filler = tuple(filler) or self.beats[-2:]
        self.skin = skin


# ---------------------------------------------------------------------------
# The tower
# ---------------------------------------------------------------------------
#
# Twenty-four levels, three to a revolution, so the cycle is eight revolutions
# and a little under three minutes of distinct content. They are listed in
# climb order and the order is a design: consecutive levels differ on at least
# three of band, altitude, form, verb, constraint, rhythm and light.
#
# The rises are chosen so that any three consecutive ones sum to between 13 and
# 20. That is not a style rule -- the ceiling over a level is the floor slab of
# the level three above it, so three rises *are* the head-room, and a run of
# short levels would put the soffit inside the parkour. There is a test.

LEVELS: tuple[Level, ...] = (

    # ---- 1 ---------------------------------------------------------------
    # The gentlest thing in the tower and still two four-block jumps. Open
    # daylight, wide platforms, a pond dug into the terrace so the long jump
    # is over water. The fence posts are the first one-cell landings a run
    # sees and they weave, so the corridor is read as having width.
    Level("MEADOW GATE", "plains", rise=5, gap=3.0, exit="stair", step=("oak", "hop"), beats=[
        ("meadow", [n("rock", arc=4.5, lift=2, spread=1, orbs=1),
                    n("rock", arc=4.6, lift=2, spread=1, moat=True)]),
        ("posts", [n("accent", arc=3.0, lift=3, spread=0, radial=1.5),
                   n("accent", arc=3.0, lift=3, spread=0, radial=-1.5,
                     orbs=1),
                   n("accent", arc=3.1, lift=3, spread=0, radial=1.5)]),
        ("bank", [n("ground", arc=5.2, lift=0, form="floor", orbs=2)]),
        ("weir", [n("rock", arc=3.6, lift=1, spread=0, moat=True, orbs=1),
                  n("rock", arc=4.4, lift=1, spread=1)]),
    ]),

    # ---- 2 ---------------------------------------------------------------
    # A straight rank of hay at the standard four-block jump, over and over,
    # with nothing else in it. The whole level is one question asked six
    # times, which no weighted table will ever produce and which is exactly
    # what a rank of bales in a field looks like.
    Level("THE LONG FURROW", "farm", rise=4, gap=2.8, exit="stair", step=("hay", "hop"), beats=[
        ("furrow", [n("rock", arc=4.6, lift=1, spread=0, orbs=1),
                    n("rock", arc=4.6, lift=1, spread=0),
                    n("rock", arc=4.6, lift=1, spread=0, orbs=1)]),
        ("headland", [n("ground", arc=4.9, lift=0, form="floor"),
                      n("rock", arc=3.4, lift=1, spread=1, ceiling=1)]),
        ("stack", [n("rock", arc=3.2, lift=2, spread=0),
                   n("rock", arc=3.4, lift=3, spread=0, orbs=2)]),
        ("drop", [n("rock", arc=5.2, lift=1, spread=0, orbs=1)]),
    ], filler=[
        ("furrow", [n("rock", arc=4.6, lift=1, spread=0, orbs=1),
                    n("rock", arc=4.6, lift=1, spread=0)]),
    ]),

    # ---- 3 ---------------------------------------------------------------
    # Roofs. Three heights, slab awnings between them, and doorway lids that
    # keep the jumps flat -- the level is crossed almost entirely under
    # something. It runs against the core so the houses read as built into
    # the wall rather than as blocks in a corridor.
    Level("ROOFTOPS", "village", rise=6, gap=3.2, exit="ladder", step=("brick", "hop"), beats=[
        ("eaves", [n("rock", arc=3.3, lift=2, hug=2.6, spread=1, ceiling=2),
                   n("accent", arc=3.4, lift=3, hug=2.6, spread=0, orbs=1)]),
        ("ridge", [n("rock", arc=3.5, lift=4, hug=3.0, spread=0),
                   n("rock", arc=4.4, lift=4, hug=3.0, spread=0, ceiling=1,
                     orbs=1)]),
        ("awning", [n("accent", arc=4.6, lift=2, form="slab", hug=3.4,
                      spread=0),
                    n("accent", arc=4.0, lift=2, form="slab", hug=3.4,
                      spread=0, orbs=1)]),
        ("yard", [n("ground", arc=5.0, lift=0, form="floor", orbs=2)]),
        ("gable", [n("rock", arc=3.4, lift=1, hug=2.8, spread=1),
                   n("rock", arc=3.5, lift=2, hug=2.8, spread=0, ceiling=2)]),
    ]),

    # ---- 4 ---------------------------------------------------------------
    # Dunes, then the tower's first genuinely mean sequence: four one-cell
    # sandstone pillars at the top of the up-jump, alternating in and out,
    # with a beam over the middle two. Bright, open, nowhere to hide.
    Level("SUNSTRUCK", "desert", rise=5, gap=3.4, exit="stair", step=("sandstone", "hop"), beats=[
        ("dunes", [n("rock", arc=4.4, lift=2, spread=1, pedestal_style="sand"),
                   n("rock", arc=3.6, lift=3, spread=1,
                     pedestal_style="sand", orbs=1)]),
        ("pillars", [n("accent", arc=3.3, lift=4, spread=0, radial=1.4),
                     n("accent", arc=3.2, lift=4, spread=0, radial=-1.4,
                       ceiling=1),
                     n("accent", arc=3.2, lift=4, spread=0, radial=1.4,
                       ceiling=1, orbs=1),
                     n("accent", arc=3.3, lift=4, spread=0, radial=-1.4)]),
        ("slip", [n("ground", arc=6.0, lift=0, form="floor", orbs=2)]),
        ("scarp", [n("rock", arc=3.6, lift=1, spread=1),
                   n("rock", arc=3.6, lift=2, spread=0, ceiling=1)]),
    ]),

    # ---- 5 ---------------------------------------------------------------
    # The longest jumps in the tower and the biggest drops. Thin terracotta
    # spires with nothing between them, out toward the rim so the fall is
    # visible under every one. Rhythm is deliberately uneven: up, up, up,
    # then all the way down in one go.
    Level("RED SPIRES", "mesa", rise=7, gap=3.6, exit="stair", step=("terra_white", "hop"), beats=[
        ("spires", [n("rock", arc=3.4, lift=3, spread=0, hug=5.4,
                      pedestal_style="terra_orange"),
                    n("accent", arc=3.3, lift=4, spread=0, hug=5.8),
                    n("rock", arc=3.4, lift=5, spread=0, hug=5.4, orbs=1)]),
        ("plunge", [n("rock", arc=6.2, lift=1, spread=0, hug=6.0, orbs=2)]),
        ("mesa", [n("accent", arc=4.8, lift=1, spread=1, hug=5.0),
                  n("rock", arc=3.5, lift=2, spread=0, hug=4.6, orbs=1)]),
        ("shelf", [n("ground", arc=5.4, lift=0, form="floor"),
                   n("rock", arc=3.5, lift=1, spread=1, orbs=1)]),
    ]),

    # ---- 6 ---------------------------------------------------------------
    # Two storeys. Logs at floor level, a vine to gain the canopy, leaf
    # platforms up in the soffit, then a long drop back down through it.
    # The only level that uses the full height of the corridor.
    Level("CANOPY", "jungle", rise=4, gap=3.0, exit="vine", step=("junglelog", "hop"), beats=[
        ("logs", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                  n("rock", arc=3.5, lift=2, spread=1)]),
        ("liana", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
                   n("junglelog", arc=2.4, step_y=4, kind="climb",
                     climb_style="vine", hug=1.6, pedestal=False, spread=0,
                     orbs=2)]),
        ("canopy", [n("accent", arc=3.5, lift=6, spread=0, hug=4.4),
                    n("accent", arc=3.4, lift=6, spread=0, hug=5.2, orbs=1),
                    n("accent", arc=3.6, lift=6, spread=0, hug=4.4)]),
        ("fall", [n("rock", arc=6.6, lift=1, spread=1, orbs=2)]),
        ("floor", [n("ground", arc=4.6, lift=0, form="floor"),
                   n("rock", arc=3.5, lift=1, spread=1, orbs=1)]),
    ], filler=[
        ("understory", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                        n("rock", arc=4.4, lift=1, spread=1)]),
    ]),

    # ---- 7 ---------------------------------------------------------------
    # Wide caps with wide gaps -- the platforms are generous and the jumps
    # between them are at the limit, which is a different kind of hard from
    # the pillar levels and reads completely differently. A slime pad in the
    # middle throws you up onto the last one.
    Level("SPORE DECK", "mushroom", rise=5, gap=3.0, exit="vine", step=("mushroomstem", "hop"), beats=[
        ("caps", [n("accent", arc=5.4, lift=2, form="wide", spread=1,
                    pedestal_style="mushroomstem", orbs=1),
                  n("accent", arc=5.6, lift=2, form="wide", spread=1,
                    pedestal_style="mushroomstem")]),
        ("stems", [n("rock", arc=3.8, lift=3, spread=0),
                   n("rock", arc=3.3, lift=4, spread=0, orbs=1)]),
        ("pad", [n("slime", arc=4.9, lift=1, form="slime", spread=0),
                 n("accent", arc=4.4, lift=2, form="wide", spread=1,
                   orbs=2)]),
        ("litter", [n("ground", arc=5.0, lift=0, form="floor"),
                    n("rock", arc=3.6, lift=1, spread=1)]),
    ]),

    # ---- 8 ---------------------------------------------------------------
    # A flooded cave. Dripstone hangs from the soffit as head-hitters you
    # cannot see coming, the floor is water you cross on calcite stepping
    # stones, and the way up is a bubble column out of the pool. Tall, so
    # the exit is a genuine ride rather than a flight of steps.
    Level("THE DRIP", "dripstone", rise=8, gap=2.8, exit="bubble", step=("calcite", "hop"), beats=[
        ("stones", [n("accent", arc=3.4, lift=1, spread=0, moat=True),
                    n("accent", arc=3.5, lift=1, spread=0, moat=True,
                      orbs=1),
                    n("accent", arc=3.4, lift=1, spread=0, moat=True)]),
        ("spikes", [n("rock", arc=3.3, lift=2, spread=1, ceiling=2),
                    n("rock", arc=3.4, lift=2, spread=0, ceiling=2, orbs=1)]),
        ("pool", [n("ground", arc=5.2, lift=0, form="floor", orbs=2)]),
        ("shelf", [n("rock", arc=3.6, lift=1, hug=2.8, spread=1),
                   n("rock", arc=3.5, lift=2, hug=2.8, spread=0)]),
    ]),

    # ---- 9 ---------------------------------------------------------------
    # A mine gallery: a lid over the whole thing, rails underfoot, cobweb to
    # wade through, and it is dark. Almost no height variation on purpose --
    # this is the flattest level in the tower and it is the ceiling that
    # makes it hard.
    Level("CUT AND COVER", "mine", rise=4, gap=2.6, exit="ladder", step=("oak", "hop"), beats=[
        ("gallery", [n("rock", arc=3.2, lift=1, hug=3.0, spread=0, ceiling=2),
                     n("rock", arc=3.3, lift=1, hug=3.0, spread=0, ceiling=2,
                       orbs=1),
                     n("rock", arc=3.2, lift=1, hug=3.0, spread=0,
                       ceiling=2)]),
        ("web", [n("web", arc=2.6, lift=1, kind="web", form="web", spread=0,
                   orbs=1)]),
        ("sleepers", [n("accent", arc=3.6, lift=1, spread=0, radial=1.3),
                      n("accent", arc=3.5, lift=1, spread=0, radial=-1.3,
                        orbs=1)]),
        ("floor", [n("ground", arc=4.2, lift=0, form="floor"),
                   n("rock", arc=3.4, lift=1, spread=1, ceiling=1)]),
    ]),

    # ---- 10 --------------------------------------------------------------
    # Black. The landings are one cell, the gaps have nothing in them, and
    # the only light is the amethyst on the blocks themselves. Everything is
    # floating -- no pedestals -- so there is no terrain to read the course
    # against, which is the point.
    Level("SCULK", "deepdark", rise=5, gap=3.2, exit="ladder", step=("deepslate", "hop"), beats=[
        ("void", [n("rock", arc=4.4, lift=3, spread=0, pedestal=False),
                  n("accent", arc=4.5, lift=3, spread=0, pedestal=False,
                    orbs=1)]),
        ("silence", [n("rock", arc=3.4, lift=4, spread=0, pedestal=False),
                     n("rock", arc=3.3, lift=4, spread=0, pedestal=False,
                       radial=1.6),
                     n("rock", arc=3.3, lift=4, spread=0, pedestal=False,
                       radial=-1.6, orbs=1)]),
        ("shelf", [n("ground", arc=5.2, lift=0, form="floor", orbs=2)]),
        ("catwalk", [n("accent", arc=4.2, lift=1, form="slab", spread=0),
                     n("accent", arc=4.0, lift=1, form="slab", spread=0,
                       orbs=1)]),
    ]),

    # ---- 11 --------------------------------------------------------------
    # Ice. The move is a slide rather than a hop and it reaches further for
    # the same rise, so this level's jumps are longer than anything else in
    # the tower and the body is visibly quicker across them.
    Level("GLACIER RUN", "ice", rise=5, gap=3.4, exit="stair", step=("packedice", "slide"), beats=[
        ("shelf", [n("rock", arc=5.0, lift=1, kind="slide", form="ice",
                     spread=0, orbs=1),
                   n("rock", arc=5.2, lift=1, kind="slide", form="ice",
                     spread=0)]),
        ("floes", [n("accent", arc=4.6, lift=2, kind="slide", form="ice",
                     spread=0, radial=1.4),
                   n("accent", arc=4.6, lift=2, kind="slide", form="ice",
                     spread=0, radial=-1.4, orbs=1)]),
        ("snowfield", [n("ground", arc=5.4, lift=0, form="floor", orbs=2)]),
        ("bergs", [n("rock", arc=3.4, lift=1, spread=1),
                   n("rock", arc=5.4, lift=1, kind="slide", form="ice",
                     spread=0, orbs=1)]),
    ]),

    # ---- 12 --------------------------------------------------------------
    # Lava under every jump, magma columns to land on, and one stretch of
    # soul sand in the middle that drops the pace to a crawl. The slow beat
    # is the design: everything either side of it reads faster for it.
    Level("LAVA LEAP", "nether", rise=6, gap=3.6, exit="stair", step=("soulsand", "hop"), beats=[
        ("leap", [n("rock", arc=4.6, lift=2, spread=0, moat=True, orbs=1),
                  n("accent", arc=4.7, lift=2, spread=0, moat=True)]),
        ("columns", [n("accent", arc=3.3, lift=3, spread=0, radial=1.5),
                     n("accent", arc=3.2, lift=4, spread=0, radial=-1.5,
                       orbs=1)]),
        ("soul", [n("soulsand", arc=4.6, lift=1, spread=0),
                  n("soulsand", arc=2.9, lift=1, spread=0, orbs=1)]),
        ("basalt", [n("ground", arc=5.0, lift=0, form="floor"),
                    n("rock", arc=3.6, lift=1, spread=1, moat=True, orbs=1)]),
    ]),

    # ---- 13 --------------------------------------------------------------
    # Teal light, a bubble column halfway up the level rather than at the end
    # of it, and wide warped caps above. The lift in the middle is what makes
    # this different from every other themed terrace: the level has an upper
    # half you are carried to.
    Level("WARPED GROVE", "warped", rise=5, gap=3.0, exit="bubble", step=("warped", "hop"), beats=[
        ("nylium", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                    n("rock", arc=3.5, lift=2, spread=1)]),
        ("lift", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
                  n("prismarine", arc=2.4, step_y=4, kind="bubble",
                    climb_style="water", hug=1.6, pedestal=False, spread=0,
                    orbs=2)]),
        ("crowns", [n("accent", arc=5.0, lift=6, form="wide", spread=0,
                      pedestal=False),
                    n("accent", arc=5.2, lift=6, form="wide", spread=0,
                      pedestal=False, orbs=1)]),
        ("descent", [n("rock", arc=6.4, lift=2, spread=1, orbs=1),
                     n("ground", arc=5.0, lift=0, form="floor")]),
    ], filler=[
        ("thicket", [n("rock", arc=3.4, lift=1, spread=1, orbs=1),
                     n("accent", arc=3.6, lift=1, spread=1)]),
    ]),

    # ---- 14 --------------------------------------------------------------
    # Obsidian pillars standing in nothing, purpur slabs between them, and
    # the terrace itself barely used. The most exposed level in the tower:
    # it runs out at the rim with the whole drop under it.
    Level("ENDPILLARS", "end", rise=7, gap=3.4, exit="bubble", step=("purpur", "hop"), beats=[
        ("pillars", [n("accent", arc=3.4, lift=4, spread=0, hug=6.0,
                       pedestal=False),
                     n("accent", arc=3.3, lift=5, spread=0, hug=6.4,
                       pedestal=False, orbs=1),
                     n("accent", arc=3.4, lift=6, spread=0, hug=6.0,
                       pedestal=False)]),
        ("slabs", [n("rock", arc=4.6, lift=4, form="slab", spread=0,
                     hug=5.6, pedestal=False),
                   n("rock", arc=4.4, lift=4, form="slab", spread=0,
                     hug=5.2, pedestal=False, orbs=1)]),
        ("void", [n("rock", arc=6.4, lift=1, spread=0, hug=5.0, orbs=2)]),
        ("stone", [n("ground", arc=4.8, lift=0, form="floor"),
                   n("accent", arc=3.4, lift=1, spread=1, orbs=1)]),
    ], filler=[
        ("shards", [n("accent", arc=3.6, lift=1, spread=0, hug=5.4),
                    n("rock", arc=4.4, lift=1, spread=0, hug=5.8,
                      orbs=1)]),
    ]),

    # ---- 15 --------------------------------------------------------------
    # The candy level, and the one place in the tower where floating blocks
    # over nothing are the *theme* rather than a failure. Wool checks, a
    # slime pad, quartz slabs. Bright, weightless, and short.
    Level("WOOLWORK", "rainbow", rise=4, gap=2.8, exit="stair", step=("quartz", "hop"), beats=[
        ("check", [n("wool_pink", arc=3.6, lift=3, spread=0, pedestal=False),
                   n("wool_lime", arc=3.5, lift=3, spread=0, pedestal=False,
                     radial=1.6),
                   n("wool_cyan", arc=3.5, lift=3, spread=0, pedestal=False,
                     radial=-1.6, orbs=1)]),
        ("bounce", [n("slime", arc=4.6, lift=1, form="slime", spread=0),
                    n("wool_yellow", arc=3.6, lift=2, spread=0, pedestal=False,
                      orbs=2)]),
        ("quartz", [n("rock", arc=4.2, lift=2, form="slab", spread=0,
                      pedestal=False),
                    n("rock", arc=4.0, lift=2, form="slab", spread=0,
                      pedestal=False, orbs=1)]),
        ("deck", [n("ground", arc=5.2, lift=0, form="floor", orbs=1)]),
    ], filler=[
        ("ribbon", [n("wool_orange", arc=3.4, lift=1, spread=0,
                     pedestal=False),
                    n("wool_purple", arc=3.8, lift=1, spread=0,
                      pedestal=False, orbs=1)]),
    ]),

    # ---- 16 --------------------------------------------------------------
    # Plains again and nothing like level 1. A water channel is cut the
    # length of the terrace and crossed on stepping stones barely above it,
    # then one long leap at the very limit onto the far bank.
    Level("THE WEIR", "plains", rise=5, gap=3.0, exit="stair", step=("cobble", "hop"), beats=[
        ("ford", [n("cobble", arc=3.0, lift=1, spread=0, moat=True),
                  n("cobble", arc=3.0, lift=1, spread=0, moat=True, orbs=1),
                  n("cobble", arc=3.1, lift=1, spread=0, moat=True),
                  n("cobble", arc=3.0, lift=1, spread=0, moat=True,
                    orbs=1)]),
        ("bank", [n("cobble", arc=4.6, lift=1, spread=1)]),
        ("leap", [n("oak", arc=4.8, lift=1, spread=0, moat=True, orbs=2)]),
        ("mill", [n("oak", arc=3.4, lift=2, spread=1, ceiling=1),
                  n("cobble", arc=3.5, lift=3, spread=0, orbs=1)]),
    ], rock="cobble", accent="oak"),

    # ---- 17 --------------------------------------------------------------
    # Vertical. Barely a jump in it: a ladder, a short run, a second ladder,
    # a scaffold. The level is eight blocks tall and you climb nearly all of
    # them, which is the only way this format ever reads as being *inside*
    # something rather than running along a ledge.
    Level("THE SHAFT", "mine", rise=8, gap=2.6, exit="ladder", step=("oak", "hop"), beats=[
        ("footing", [n("rock", arc=3.4, lift=1, hug=2.8, spread=1, orbs=1)]),
        ("rungs", [n("rock", arc=3.0, lift=1, hug=2.2, spread=1),
                   n("oak", arc=2.4, step_y=4, kind="climb",
                     climb_style="ladder", hug=1.6, pedestal=False, spread=0,
                     orbs=2)]),
        ("landing", [n("accent", arc=3.4, lift=5, spread=0, hug=3.2,
                       pedestal=False),
                     n("accent", arc=3.3, lift=5, spread=0, hug=4.0,
                       pedestal=False, orbs=1)]),
        ("higher", [n("rock", arc=3.0, lift=5, hug=2.2, spread=1),
                    n("scaffold", arc=2.4, step_y=3, kind="climb",
                      climb_style="scaffold", hug=1.6, pedestal=False,
                      spread=0, orbs=2)]),
        ("gantry", [n("rock", arc=4.6, lift=6, form="slab", spread=0,
                      hug=3.4, pedestal=False, ceiling=1),
                    n("rock", arc=3.8, lift=6, form="slab", spread=0,
                      hug=4.2, pedestal=False, orbs=1)]),
    ], rock="deepslate", accent="oak"),

    # ---- 18 --------------------------------------------------------------
    # Ice again, and this one is relentless: no floor beat anywhere in it,
    # every landing a slide at close to the limit, out at the rim. The
    # fastest thirty seconds in the tower.
    Level("BLUE ICE", "ice", rise=4, gap=3.2, exit="stair", step=("blueice", "slide"), beats=[
        ("run", [n("blueice", arc=5.4, lift=1, kind="slide", form="ice",
                   spread=0, hug=5.6, orbs=1),
                 n("blueice", arc=5.6, lift=1, kind="slide", form="ice",
                   spread=0, hug=6.0),
                 n("blueice", arc=5.4, lift=1, kind="slide", form="ice",
                   spread=0, hug=5.6, orbs=1)]),
        ("shelves", [n("rock", arc=4.8, lift=2, kind="slide", form="ice",
                       spread=0, hug=5.0),
                     n("rock", arc=4.8, lift=2, kind="slide", form="ice",
                       spread=0, hug=6.2, orbs=1)]),
        ("crevasse", [n("blueice", arc=6.2, lift=1, kind="slide", form="ice",
                        spread=0, hug=5.4, orbs=2)]),
    ], ground="packedice", rock="frost", accent="snow"),

    # ---- 19 --------------------------------------------------------------
    # A quarry cut down into the terrace: you go *below* the floor line, in
    # steps, and come back out. Every jump in the middle of it is a drop, and
    # a drop is the only way this motion model reaches past four and a half
    # metres -- so the level is also the tower's longest single jump.
    Level("THE QUARRY", "desert", rise=5, gap=3.0, exit="stair", step=("chiselled", "hop"), beats=[
        ("benches", [n("rock", arc=3.4, lift=4, spread=0,
                       pedestal_style="sand"),
                     n("rock", arc=4.6, lift=3, spread=0, orbs=1),
                     n("rock", arc=5.4, lift=2, spread=0),
                     n("rock", arc=5.4, lift=1, spread=0, orbs=1)]),
        ("floor", [n("ground", arc=5.0, lift=0, form="floor", orbs=2)]),
        ("haul", [n("accent", arc=3.4, lift=1, spread=1),
                  n("accent", arc=3.4, lift=2, spread=0),
                  n("accent", arc=3.5, lift=3, spread=0, orbs=1)]),
    ], rock="chiselled", accent="sandstone"),

    # ---- 20 --------------------------------------------------------------
    # One-wide plank runs held out at the rim with two hundred blocks of air
    # underneath and nothing on either side. Nothing here is difficult to
    # land; all of it is difficult to watch, which for a strip that is on
    # screen while somebody waits is the same thing.
    Level("ROPE BRIDGE", "jungle", rise=6, gap=3.4, exit="vine", step=("oak", "hop"), beats=[
        ("planks", [n("oak", arc=3.2, lift=2, spread=0, hug=6.4,
                      pedestal=False),
                    n("oak", arc=3.2, lift=2, spread=0, hug=6.6,
                      pedestal=False, orbs=1),
                    n("oak", arc=3.2, lift=2, spread=0, hug=6.4,
                      pedestal=False),
                    n("oak", arc=3.3, lift=2, spread=0, hug=6.6,
                      pedestal=False, orbs=1)]),
        ("post", [n("rock", arc=3.4, lift=3, spread=0, hug=6.0,
                    pedestal=False)]),
        ("span", [n("oak", arc=4.6, lift=3, spread=0, hug=6.2,
                    pedestal=False, orbs=2)]),
        ("land", [n("ground", arc=5.4, lift=0, form="floor"),
                  n("rock", arc=3.5, lift=1, spread=1, orbs=1)]),
    ], filler=[
        ("cable", [n("oak", arc=3.4, lift=1, spread=0, hug=6.2,
                    pedestal=False, orbs=1),
                   n("oak", arc=3.4, lift=1, spread=0, hug=6.6,
                     pedestal=False)]),
    ], rock="junglelog", accent="jungleleaf"),

    # ---- 21 --------------------------------------------------------------
    # Blackstone columns packed close under a low soffit -- short jumps, but
    # every one of them under a lid, and magma glowing under the gaps. The
    # opposite design to Lava Leap with the same materials, which is the
    # point of having the theme twice.
    Level("BASALT DELTAS", "nether", rise=5, gap=2.8, exit="stair", step=("blackstone", "hop"), beats=[
        ("deltas", [n("rock", arc=3.0, lift=2, spread=0, ceiling=2),
                    n("rock", arc=3.0, lift=2, spread=0, ceiling=2, orbs=1),
                    n("rock", arc=3.1, lift=2, spread=0, ceiling=2)]),
        ("glow", [n("accent", arc=3.4, lift=3, spread=0, moat=True),
                  n("accent", arc=3.3, lift=3, spread=0, moat=True,
                    orbs=1)]),
        ("crust", [n("ground", arc=5.2, lift=0, form="floor", orbs=2)]),
        ("stacks", [n("rock", arc=3.2, lift=1, spread=0, radial=1.4,
                      ceiling=1),
                    n("rock", arc=3.2, lift=1, spread=0, radial=-1.4,
                      ceiling=1, orbs=1)]),
    ], ground="blackstone", rock="blackstone", accent="magma"),

    # ---- 22 --------------------------------------------------------------
    # The hardest level in the tower. Every landing is one cell, floating,
    # unlit except for its own vein, and every jump is at the top of its
    # envelope. There is no floor beat and no rest.
    Level("SILENCE", "deepdark", rise=6, gap=3.6, exit="ladder", step=("sculk", "hop"), beats=[
        ("reach", [n("rock", arc=4.8, lift=3, spread=0, pedestal=False),
                   n("rock", arc=4.8, lift=3, spread=0, pedestal=False,
                     orbs=1)]),
        ("thread", [n("accent", arc=3.6, lift=4, spread=0, pedestal=False),
                    n("accent", arc=3.5, lift=4, spread=0, pedestal=False,
                      radial=1.7),
                    n("accent", arc=3.5, lift=4, spread=0, pedestal=False,
                      radial=-1.7, orbs=1)]),
        ("gulf", [n("rock", arc=6.2, lift=2, spread=0, pedestal=False,
                    orbs=2)]),
        ("ledge", [n("rock", arc=4.6, lift=2, spread=0, pedestal=False),
                   n("rock", arc=3.5, lift=3, spread=0, pedestal=False,
                     orbs=1)]),
    ], filler=[
        ("dark", [n("accent", arc=4.7, lift=3, spread=0,
                   pedestal=False),
                  n("rock", arc=4.7, lift=3, spread=0,
                    pedestal=False, orbs=1)]),
    ], rock="deepslate", accent="sculk"),

    # ---- 23 --------------------------------------------------------------
    # Inside a bell tower: beams across the shaft, ledges up the wall, and a
    # ladder in the middle of it rather than at the end. Eight blocks gained
    # in a level you barely travel along -- the second of the two vertical
    # levels and deliberately nothing like the mine.
    Level("BELFRY", "village", rise=8, gap=2.6, exit="ladder", step=("plaster", "hop"), beats=[
        ("sill", [n("rock", arc=3.4, lift=1, hug=2.6, spread=1, orbs=1),
                  n("rock", arc=3.4, lift=2, hug=2.6, spread=0)]),
        ("beams", [n("oak", arc=3.6, lift=3, form="slab", spread=0, hug=3.4,
                     pedestal=False, ceiling=1),
                   n("oak", arc=3.6, lift=3, form="slab", spread=0, hug=4.6,
                     pedestal=False, orbs=1)]),
        ("rungs", [n("rock", arc=3.0, lift=3, hug=2.2, spread=1),
                   n("oak", arc=2.4, step_y=4, kind="climb",
                     climb_style="ladder", hug=1.6, pedestal=False, spread=0,
                     orbs=2)]),
        ("loft", [n("accent", arc=3.5, lift=6, spread=0, hug=3.2,
                    pedestal=False),
                  n("accent", arc=3.4, lift=6, spread=0, hug=4.2,
                    pedestal=False, orbs=1)]),
        ("bell", [n("rock", arc=4.4, lift=5, form="slab", spread=0, hug=3.8,
                    pedestal=False, ceiling=1, orbs=1)]),
    ], filler=[
        ("joists", [n("oak", arc=3.5, lift=5, form="slab", spread=0,
                      hug=3.4, pedestal=False, orbs=1),
                    n("oak", arc=3.5, lift=5, form="slab", spread=0,
                      hug=4.6, pedestal=False)]),
    ], rock="brick", accent="plaster"),

    # ---- 24 --------------------------------------------------------------
    # The gate, and the place the loop is legible. An obsidian arch stands
    # across the corridor, you go under it and off the end, and the level
    # above is the meadow again a hundred and thirty blocks higher. Short and
    # deliberately calm: it is a threshold, not a test.
    Level("THE GATE", "end", rise=4, gap=3.0, exit="stair", step=("obsidian", "hop"), beats=[
        ("approach", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                      n("rock", arc=3.4, lift=1, spread=1)]),
        ("arch", [n("accent", arc=3.2, lift=2, spread=0, ceiling=3),
                  n("accent", arc=3.2, lift=2, spread=0, ceiling=3,
                    orbs=2)]),
        ("threshold", [n("rock", arc=4.6, lift=1, spread=1),
                       n("ground", arc=5.0, lift=0, form="floor", orbs=1)]),
    ], filler=[
        ("court", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                   n("accent", arc=4.4, lift=1, spread=1)]),
    ], rock="purpur", accent="obsidian"),
)


# ---------------------------------------------------------------------------
# The building
# ---------------------------------------------------------------------------

class Cone(sp.Cone):
    """The generated cone, with its levels read off the table instead of rolled.

    Everything analytic about the building -- :meth:`rock`, :meth:`unwrap`, the
    flare, the ribs, the soffit -- is inherited untouched. What changes is that
    a level's theme, height and chasm are a design decision.

    The one thing still rolled is **where in the cycle the tower starts**
    (:attr:`phase`), and it is worth keeping: the tower is the same tower every
    run, so without it every run would open in the meadow. With it, two runs a
    minute apart open in different places on a building the viewer comes to
    recognise, which is the whole reason to hand-build one.
    """

    #: Half as wide again as the generated tower, and the reason is the whole
    #: economics of a designed level. A level is a third of a revolution, its
    #: exit climb needs a fixed run-up in *blocks*, and what is left over is
    #: the design. At the generated radius that left about four landings a
    #: level against seven for the climb -- so a hand-built tower would have
    #: been three fifths staircase, which is what hand-building it was meant to
    #: stop. A wider circle lengthens every terrace and nothing else: the
    #: corridor is the same width, the ceiling is the same height, the flare is
    #: the same. It also straightens the corridor, which the camera likes.
    base_r = 36.0

    def __init__(self, rng, base_y: int = 0) -> None:
        # Drawn before ``super().__init__``, which lays the first section.
        self.phase = rng.randrange(len(LEVELS))
        super().__init__(rng, base_y)

    def design(self, index: int) -> Level:
        """The designed level at a section index. Cyclic: that is the loop."""
        return LEVELS[(index + self.phase) % len(LEVELS)]

    def _extend_section(self) -> None:
        i = len(self.sections)
        u0 = self._u_lo + i * sp.LEVEL_ARC
        design = self.design(i)
        if i == 0:
            y, rise = self.base, 0
        else:
            # A section's ``rise`` is how much higher it is than the one
            # *before* it, so it belongs to the design of the level below.
            rise = self.design(i - 1).rise
            y = self.sections[-1].y + rise
        # The chasm is authored in blocks and converted here, because a fixed
        # angle would be six blocks wide at the bottom of the tower and ten at
        # the top -- and how far a body can jump does not care how wide the
        # tower is.
        radius = max(6.0, self.rim_at(y))
        self.sections.append(Section(
            i, THEME_BY_NAME[design.name], u0, u0 + sp.LEVEL_ARC, y, rise,
            min(design.gap / radius, sp.LEVEL_ARC * 0.45),
            # The design *is* the difficulty here, so nothing is scaled by a
            # pitch drawn per level. Held at one so that the exit climb and the
            # dressing behave as they do at the top of the generated range.
            1.0, ""))


def _skin(design: Level) -> Theme:
    """The level's own theme: its base one, renamed, with its materials swapped.

    Renamed because the scene puts :attr:`Theme.name` on screen as the name of
    the place you are in, and "SCULK" and "SILENCE" being the same deepdark
    theme is exactly the thing this tower exists to stop being visible.
    """
    base = sp.THEME_BY_NAME[design.theme]
    kw = {
        "ground": base.ground, "sub": base.sub, "rock": base.rock,
        "accent": base.accent, "liquid": base.liquid, "glow": base.glow,
        "props": base.props, "features": base.features, "sky": base.sky,
        "dark": base.dark, "candy": base.candy, "exits": (design.exit,),
        "step": base.step,
    }
    kw.update(design.skin)
    return Theme(design.name, **kw)


#: Every theme the renderer may be handed, by name. The generated themes are
#: still in here because a block records the *name* of the theme it was laid
#: in and the scene looks that name up again when it draws it -- and a level's
#: theme is its own, renamed after the level.
THEME_BY_NAME: dict[str, Theme] = dict(sp.THEME_BY_NAME)
THEME_BY_NAME.update({lv.name: _skin(lv) for lv in LEVELS})


# ---------------------------------------------------------------------------
# The course
# ---------------------------------------------------------------------------

class Course(sp.Course):
    """The generated course, reading its content off the page.

    One method is replaced. :meth:`_choose_feature` no longer rolls against a
    weighted table; it takes the next beat of the level the frontier is
    standing in. Everything either side of that -- when the exit climb starts,
    how a beat is truncated so it cannot eat the climb's run-up, how a node
    becomes a cell, every check that says the cell is legal, what happens when
    one is not -- is the generator's, unchanged and already measured.
    """

    def __init__(self, rng, cone: Cone, hop_rng=None) -> None:
        #: Section index -> how many beats of that level have been laid. Kept
        #: per level rather than as one counter because generation runs sixteen
        #: landings ahead and can be part-way into the next level while the
        #: body is still in this one.
        self._cursor: dict[int, int] = {}
        #: Beats asked for, and beats that came out with every landing placed
        #: as authored. The fidelity numbers; see ``tools/tower_probe.py``.
        self.authored = 0
        self.as_designed = 0
        super().__init__(rng, cone, hop_rng)

    ahead = AHEAD

    def _level_budget(self):
        """As the generator's, except that a climb out is not a staircase.

        The reserve is what the exit is *going* to cost, and the generator has
        to assume the worst because it does not know which of the four shapes
        it will get until it asks. A designed level does know. A staircase
        spends a landing a block and needs seven of them to leave a six-block
        level; a ladder spends three whatever the height -- a block to launch
        from, the ride, and the jump across. Reserving seven for a ladder threw
        away sixteen blocks of terrace, which on a level that only has forty is
        most of the design.

        The fallback still exists and still costs seven, so this reserves a
        landing more than the ladder needs. If the ladder cannot be built the
        stair takes over with less room than it wants, and what catches that is
        the same chain that catches it in the generated tower, ending in a
        ladder up the far wall of the chasm.
        """
        lv, need, want, radius = super()._level_budget()
        kind = self.cone.design(lv.index).exit
        if kind != "stair" and need >= 3:
            want -= (max(1, need) - 2) * sp.ASCENT_ARC
        return lv, need, want, radius

    def _choose_feature(self, lv) -> list[dict]:
        design = self.cone.design(lv.index)
        cursor = self._cursor.get(lv.index, 0)
        self._cursor[lv.index] = cursor + 1
        if cursor < len(design.beats):
            name, specs = design.beats[cursor]
        else:
            # The terrace outlasted the script. How much terrace a level has
            # depends on how far up the flare it is and on how tall the level
            # above it is, so this is the normal case on the wide turns rather
            # than a design that ran short.
            fill = design.filler
            name, specs = fill[(cursor - len(design.beats)) % len(fill)]
        self.segment = name
        self.authored += len(specs)
        return [self._node(**_resolve(spec, lv.theme)) for spec in specs]

    def _feat_ascent(self, rng, lv, need: int) -> list[dict]:
        """The way out, as the level's design says rather than as dice say.

        A *kind* and not coordinates, and that is deliberate. The climb out is
        the one move a run cannot do without -- every level ends in a hole with
        nothing in it and a wall on the far side -- and the generator's version
        of it is the most-tested code in the project, at 0.30% of landings
        falling through to the unchecked answer. Authoring which of the four
        shapes a level uses changes how it looks without touching any of that.
        """
        kind = self.cone.design(lv.index).exit
        if kind != "stair" and need >= 3:
            built = self._ascent_climb(rng, lv, need, kind)
            if built:
                return built
        return self._ascent_stair(rng, lv, need)


def _resolve(spec: dict, theme: Theme) -> dict:
    """An authored node against the level it is in.

    Roles become the level's own materials; anything else is taken literally.
    ``ramp`` is off for everything here: a hand-built gap is the design, and
    stretching it by a quarter turns "the standard four-block jump" into a jump
    no body has.
    """
    out = dict(spec)
    style = out["style"]
    if style in ROLES:
        out["style"] = getattr(theme, style)
    out.setdefault("ramp", False)
    return out
