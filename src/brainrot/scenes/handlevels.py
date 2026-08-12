"""The thirty-three designed levels of the hand-built tower.

This module is nothing but the design: ``docs/TOWER.md`` is the intent, this
is that intent as data, and ``brainrot.scenes.handplan`` is the machinery that
places it. Every number here was chosen against the physics table in the doc
-- one jump impulse, one speed -- and `tools/tower_probe.py --design-only`
checks the whole file on paper in under a second. Run it after touching
anything here. A beat under 98% fidelity is a design to look at.

The vocabulary, briefly. ``arc`` is metres along the corridor, ``lift`` is
height above the level's floor, ``radial`` weaves across the corridor,
``hug`` is distance out from the core wall (big = out at the rim over the
drop), ``ceiling`` is a checked lid, ``moat`` digs liquid under the jump,
``shell`` builds an interior (tunnel/hall/cave/shaft) around the move,
``step_y`` is a signed absolute rise for climbs and rim-descents,
``pedestal=False`` floats the landing. Rules that bind every line:

* consecutive hops may rise at most one block, and a rising hop's arc stays
  at or under 3.6 (a +1 jump reaches 3.10 stand-point to stand-point);
* a flat hop's arc stays under 4.9; only a *descending* jump may ask more;
* levels rise 4-8 to the next, and any three consecutive rises sum to 13-20
  because three rises are literally the head-room over the lowest of them;
* ledge is the default ground -- the plaza died with the first tower -- and
  a level that wants the full floor says ``plaza`` and dresses it.
"""

from __future__ import annotations

#: Material roles a level may name instead of a material. Writing ``"rock"``
#: rather than ``"cobble"`` is what lets one design be re-skinned by giving
#: its level a different theme, and what keeps a level readable as a *shape*.
ROLES = frozenset(("ground", "sub", "rock", "accent", "glow", "liquid"))


def n(style: str = "rock", **kw) -> dict:
    """One authored landing: a role or material, and the node's own arguments.

    Thin on purpose. The keywords are ``Course._node``'s own, so the design
    below is written in the same vocabulary the generator's features were and
    anything expressible there is expressible here.
    """
    return {"style": style, **kw}


class Level:
    """One designed level: a place, a shape, and the way out of it.

    ``beats`` is the level in order. Each beat is ``(name, [node, ...])`` and
    is laid whole or not at all. ``filler`` repeats if the terrace outlasts
    the script -- put the level's *character* there, not its surprise.
    ``rise`` is how far above this level the next one sits. ``gap`` is the
    chasm at the end, in blocks. ``exit`` is a kind (stair/ladder/vine/
    bubble); ``exit_beats`` optionally writes the way out landing by landing,
    with the generated climb still underneath as the fallback. ``profile``,
    ``shelf`` and ``landmark`` are the ground and the one structure the level
    is recognised by. ``skin`` re-skins the base theme.
    """

    __slots__ = ("band", "beats", "breaks", "exit", "exit_beats", "filler",
                 "gap", "landmark", "name", "profile", "rise", "shelf",
                 "skin", "theme")

    def __init__(self, name: str, theme: str, rise: int, gap: float,
                 exit: str, beats, filler=(), profile: str = "ledge",
                 shelf: float = 4.0, landmark: str = "",
                 exit_beats=(), breaks: int | None = None,
                 band: float = 9.5, **skin) -> None:
        self.name = name
        self.theme = theme
        self.rise = rise
        self.gap = gap
        self.exit = exit
        self.beats = tuple(beats)
        self.filler = tuple(filler) or self.beats[-2:]
        self.profile = profile
        self.shelf = shelf
        self.landmark = landmark
        self.exit_beats = tuple(exit_beats)
        #: In-level floor gaps -- the islands-not-a-ribbon rule. Measured on
        #: the real map: no checkpoint leg is walkable end to end and a
        #: no-jump walker covers 46% on average. Three breaks for a ledge,
        #: two for a full floor, unless the level says otherwise.
        self.breaks = breaks if breaks is not None else \
            (3 if profile == "ledge" else 2)
        #: The corridor's width for this level, core face to rim: a tight
        #: gallery at 7.5 and a broad court at 13 are different places
        #: before a single block is laid. Capped by ``BAND_MAX``.
        self.band = band
        self.skin = skin


# ---------------------------------------------------------------------------
# The tower: thirty-three levels, eleven revolutions, and the cycle loops.
# Consecutive levels differ on at least three of band, enclosure, form, verb,
# constraint, rhythm and light; interiors never come twice in a row; each
# third of the tower gets at least three interiors and a vertical level.
# ---------------------------------------------------------------------------

LEVELS: tuple[Level, ...] = (

    # ---- 1 ---------------------------------------------------------------
    # The gentle open. A garden path between hedges, a pond crossed on oak
    # rounds, and the tower's first one-cell landings kept mild. The arch at
    # the end frames the run ahead.
    Level("THE GATEHOUSE", "plains", rise=5, gap=2.8, exit="stair",
          band=11.0, shelf=5.0, landmark="arch", step=("oak", "hop"), beats=[
        ("lawn", [n("ground", arc=4.6, lift=0, form="floor", orbs=1),
                  n("rock", arc=3.4, lift=1, spread=1)]),
        ("hedge", [n("accent", arc=3.2, lift=2, spread=0, radial=1.2),
                   n("accent", arc=3.3, lift=2, spread=0, radial=-1.2,
                     orbs=1)]),
        ("pond", [n("oak", arc=3.5, lift=1, spread=0, moat=True),
                  n("oak", arc=3.4, lift=1, spread=0, moat=True, orbs=1)]),
        ("bench", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("pickets", [n("rock", arc=3.4, lift=1, spread=1),
                     n("oak", arc=3.0, lift=1, form="fence", spread=0,
                       radial=1.2),
                     n("oak", arc=3.0, lift=1, form="fence", spread=0,
                       radial=-1.2, orbs=1),
                     n("rock", arc=3.2, lift=2, spread=0)]),
        ("gate", [n("accent", arc=3.3, lift=3, spread=0, ceiling=2),
                  n("rock", arc=4.6, lift=2, spread=1, orbs=1)]),
    ]),

    # ---- 2 ---------------------------------------------------------------
    # A farm on a shelf: hay ranks at near-full reach, crop rows underfoot,
    # and the windmill standing on its apron. The rhythm is a metronome --
    # the same big jump asked four times, which no dice ever ask.
    Level("WINDMILL REACH", "farm", rise=4, gap=2.8, exit="stair",
          band=10.0, landmark="windmill", step=("hay", "hop"), beats=[
        ("rank", [n("hay", arc=4.4, lift=1, spread=0, orbs=1),
                  n("hay", arc=4.4, lift=1, spread=0),
                  n("hay", arc=4.4, lift=1, spread=0, orbs=1),
                  n("hay", arc=4.4, lift=1, spread=0)]),
        ("furrow", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("bales", [n("hay", arc=3.4, lift=1, spread=0),
                   n("hay", arc=3.3, lift=2, spread=0, orbs=1)]),
        ("cart", [n("oak", arc=4.7, lift=2, spread=1, orbs=1)]),
        ("trough", [n("rock", arc=3.5, lift=1, spread=0, moat=True),
                    n("ground", arc=4.4, lift=0, form="floor", orbs=1)]),
        ("stack", [n("hay", arc=3.4, lift=1, spread=0),
                   n("hay", arc=3.3, lift=2, spread=0, orbs=1)]),
    ], filler=[
        ("rank", [n("hay", arc=4.4, lift=1, spread=0, orbs=1),
                  n("hay", arc=4.4, lift=1, spread=0)]),
    ], exit_beats=[
        n("hay", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
        n("hay", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9, orbs=1),
        n("oak", arc=2.9, step_y=1, form="fence", hug=2.4, spread=0,
          pedestal=False),
        n("hay", arc=3.0, step_y=1, hug=2.4, spread=0, radial=-0.9, orbs=1),
        n("hay", arc=2.9, step_y=1, hug=2.6, spread=0),
    ]),

    # ---- 3 ---------------------------------------------------------------
    # A street. The one place near the bottom that keeps the full floor,
    # because a street is a *place* and dresses it: facades against the
    # core, awning slabs, and one stretch crossed inside a house -- the
    # tower's first interior, twenty seconds in.
    Level("MARKET STREET", "village", rise=6, gap=3.0, exit="ladder",
          band=12.5, profile="plaza", landmark="watchtower", step=("brick", "hop"),
          beats=[
        ("street", [n("ground", arc=4.6, lift=0, form="floor", orbs=1),
                    n("rock", arc=3.4, lift=1, spread=1)]),
        ("stalls", [n("oak", arc=3.0, lift=1, form="fence", spread=0,
                      radial=1.3),
                    n("accent", arc=3.2, lift=2, spread=0, radial=-1.3,
                      orbs=1),
                    n("oak", arc=3.0, lift=2, form="fence", spread=0,
                      radial=1.3)]),
        ("awnings", [n("accent", arc=4.4, lift=2, form="slab", spread=0),
                     n("accent", arc=3.6, lift=3, form="slab", spread=0,
                       orbs=1)]),
        ("parlour", [n("rock", arc=3.6, lift=1, hug=2.8, spread=0,
                       shell="hall"),
                     n("rock", arc=3.4, lift=1, hug=2.8, spread=0,
                       shell="hall", orbs=1)]),
        ("yard", [n("ground", arc=5.2, lift=0, form="floor", orbs=1)]),
        ("gables", [n("rock", arc=3.4, lift=1, hug=3.0, spread=0),
                    n("rock", arc=3.5, lift=2, hug=3.0, spread=0, ceiling=2,
                      orbs=1),
                    n("accent", arc=3.6, lift=3, hug=3.2, spread=0)]),
    ]),

    # ---- 4 ---------------------------------------------------------------
    # Underground. A timbered gallery the whole way -- the first full
    # interior level -- with rails underfoot, one cobweb wade, and the
    # course brushing a headframe at the door. Dark, lamp-lit.
    Level("THE TIMBERWORKS", "mine", rise=5, gap=2.6, exit="ladder",
          band=7.5, profile="plaza", landmark="crane", step=("oak", "hop"), beats=[
        ("adit", [n("rock", arc=3.2, lift=1, hug=3.0, spread=0,
                    shell="tunnel"),
                  n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                    shell="tunnel", orbs=1)]),
        ("rails", [n("accent", arc=3.6, lift=1, spread=0, radial=1.2,
                     shell="tunnel"),
                   n("accent", arc=3.5, lift=1, spread=0, radial=-1.2,
                     shell="tunnel", orbs=1)]),
        ("web", [n("web", arc=2.6, lift=1, kind="web", form="web", spread=0,
                   shell="tunnel", orbs=1)]),
        ("gallery", [n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                       shell="tunnel"),
                     n("rock", arc=3.2, lift=2, hug=3.0, spread=0,
                       shell="tunnel", orbs=1),
                     n("rock", arc=3.3, lift=2, hug=3.0, spread=0,
                       shell="tunnel")]),
        ("sump", [n("ground", arc=4.4, lift=0, form="floor", orbs=1)]),
        ("boards", [n("oak", arc=3.2, lift=1, form="trapdoor", spread=0,
                      shell="tunnel"),
                    n("oak", arc=3.2, lift=1, form="trapdoor", spread=0,
                      shell="tunnel", orbs=1),
                    n("rock", arc=3.2, lift=1, spread=0, shell="tunnel")]),
    ]),

    # ---- 5 ---------------------------------------------------------------
    # A sandstone hall with a lava seam down the middle of the floor and
    # doorway lids that keep every arc flat. Bright at the openings, dim in
    # the middle, and the temple front stands where the course turns.
    Level("SUNKEN TEMPLE", "desert", rise=6, gap=3.0, exit="stair",
          band=12.0, profile="plaza", landmark="arch", step=("sandstone", "hop"),
          liquid="lava", beats=[
        ("porch", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                   n("rock", arc=3.4, lift=1, spread=1)]),
        ("nave", [n("rock", arc=3.3, lift=1, hug=3.2, spread=0,
                    shell="hall"),
                  n("rock", arc=3.4, lift=1, hug=3.2, spread=0,
                    shell="hall", orbs=1),
                  n("rock", arc=3.3, lift=2, hug=3.2, spread=0,
                    shell="hall")]),
        ("seam", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
                  n("accent", arc=3.4, lift=1, spread=0, moat=True,
                    orbs=1)]),
        ("lintels", [n("rock", arc=3.4, lift=2, spread=0, ceiling=2),
                     n("rock", arc=3.3, lift=2, spread=0, ceiling=2,
                       orbs=1)]),
        ("court", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("altar", [n("chiselled", arc=3.4, lift=1, spread=0),
                   n("chiselled", arc=3.3, lift=2, spread=0, orbs=1)]),
    ], exit_beats=[
        n("chiselled", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
          deco="lamp"),
        n("chiselled", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
        n("chiselled", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
          orbs=1),
        n("chiselled", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
        n("chiselled", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
          orbs=1),
        n("chiselled", arc=3.0, step_y=1, hug=2.4, spread=0, deco="lamp"),
        n("chiselled", arc=2.9, step_y=1, hug=2.6, spread=0),
    ]),

    # ---- 6 ---------------------------------------------------------------
    # Back into daylight hard: narrow terracotta balconies on the cliff,
    # the biggest drops so far under every jump, and one slab bridge out
    # over the rim. Uneven rhythm on purpose -- up, up, then one long fall.
    Level("THE BALCONIES", "mesa", rise=7, gap=3.4, exit="stair",
          band=9.0, shelf=4.5, landmark="hoodoo", step=("terra_white", "hop"), beats=[
        ("ledges", [n("rock", arc=3.4, lift=2, spread=0),
                    n("accent", arc=3.3, lift=3, spread=0, orbs=1),
                    n("rock", arc=3.4, lift=4, spread=0)]),
        ("plunge", [n("ground", arc=6.0, lift=0, form="floor", orbs=2)]),
        ("spur", [n("rock", arc=3.4, lift=1, hug=7.5, pedestal=False,
                    spread=0),
                  n("accent", arc=3.4, lift=1, form="slab", hug=9.5,
                    pedestal=False, spread=0, orbs=1),
                  n("accent", arc=3.2, lift=2, form="slab", hug=11.0,
                    pedestal=False, spread=0, orbs=1),
                  n("accent", arc=3.4, lift=1, form="slab", hug=8.5,
                    pedestal=False, spread=0)]),
        ("landing", [n("rock", arc=4.2, lift=1, spread=1, orbs=1)]),
        ("spurs", [n("rock", arc=3.4, lift=2, spread=0, radial=1.4),
                   n("accent", arc=3.3, lift=3, spread=0, radial=-1.4,
                     orbs=1)]),
        ("brink", [n("rock", arc=4.8, lift=3, spread=0, hug=5.8,
                     pedestal=False, orbs=1)]),
    ]),

    # ---- 7 ---------------------------------------------------------------
    # Two storeys of jungle. Logs on the shelf, a vine into the canopy,
    # leaf decks at the soffit, then a deliberate long drop back through
    # the leaves. The giant tree is the landmark and the level.
    Level("CANOPY WALK", "jungle", rise=7, gap=3.0, exit="vine",
          band=11.5, shelf=5.0, landmark="tree", step=("junglelog", "hop"), beats=[
        ("roots", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                   n("rock", arc=3.5, lift=2, spread=1)]),
        ("liana", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
                   n("junglelog", arc=2.4, step_y=4, kind="climb",
                     climb_style="vine", hug=2.0, pedestal=False, spread=0,
                     orbs=2)]),
        ("canopy", [n("accent", arc=3.4, lift=6, spread=0, hug=4.6,
                      pedestal=False),
                    n("accent", arc=3.5, lift=6, spread=0, hug=5.4,
                      pedestal=False, orbs=1),
                    n("accent", arc=3.4, lift=6, spread=0, hug=4.8,
                      pedestal=False)]),
        ("fall", [n("ground", arc=6.4, lift=0, form="floor", orbs=2)]),
        ("logs", [n("rock", arc=3.5, lift=1, spread=1),
                  n("rock", arc=4.4, lift=1, spread=1, orbs=1)]),
        ("bough", [n("rock", arc=3.4, lift=2, spread=0),
                   n("accent", arc=3.5, lift=3, spread=0, orbs=1)]),
    ], filler=[
        ("understory", [n("rock", arc=4.2, lift=2, spread=1, orbs=1),
                        n("accent", arc=3.4, lift=2, spread=1)]),
    ], exit_beats=[
        n("rock", arc=2.8, lift=1, hug=2.2, spread=1),
        n("junglelog", arc=2.4, step_y=7, kind="climb", climb_style="vine",
          hug=2.0, pedestal=False, spread=0, orbs=2),
        n("accent", arc=3.0, step_y=1, hug=2.8, spread=0),
    ]),

    # ---- 8 ---------------------------------------------------------------
    # A flooded cave. Calcite stones barely above the water, dripstone
    # teeth low enough to lid the jumps, and the way out is a bubble
    # column ridden up a stone well.
    Level("THE CISTERN", "dripstone", rise=6, gap=2.8, exit="bubble",
          band=11.0, profile="plaza", step=("calcite", "hop"), beats=[
        ("stones", [n("accent", arc=3.4, lift=1, spread=0, moat=True),
                    n("accent", arc=3.5, lift=1, spread=0, moat=True,
                      orbs=1),
                    n("accent", arc=3.4, lift=1, spread=0, moat=True)]),
        ("grotto", [n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                      shell="cave"),
                    n("rock", arc=3.4, lift=1, hug=3.0, spread=0,
                      shell="cave", orbs=1)]),
        ("teeth", [n("rock", arc=3.4, lift=2, spread=0, ceiling=2),
                   n("rock", arc=3.3, lift=2, spread=0, ceiling=2, orbs=1)]),
        ("pool", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("shelf", [n("rock", arc=3.5, lift=1, hug=2.8, spread=1),
                   n("accent", arc=3.4, lift=2, hug=2.8, spread=0,
                     orbs=1)]),
        ("basin", [n("accent", arc=4.6, lift=1, spread=0, moat=True,
                     orbs=1)]),
    ], exit_beats=[
        n("rock", arc=2.8, lift=1, hug=2.2, spread=1),
        n("prismarine", arc=2.4, step_y=7, kind="bubble",
          climb_style="water", hug=2.0, pedestal=False, spread=0, orbs=2),
        n("accent", arc=3.0, step_y=1, hug=2.8, spread=0),
    ]),

    # ---- 9 ---------------------------------------------------------------
    # Ice in the open. Slides at reach with the drop beside them, and the
    # crevasse: a stretch where the shelf itself is missing and the course
    # floats over the blue. Fast and bright after the cave.
    Level("GLACIER SHELF", "ice", rise=4, gap=3.2, exit="stair",
          band=10.5, shelf=4.5, step=("packedice", "slide"), beats=[
        ("sheet", [n("rock", arc=5.0, lift=1, kind="slide", form="ice",
                     spread=0, orbs=1),
                   n("rock", arc=5.2, lift=1, kind="slide", form="ice",
                     spread=0)]),
        ("crevasse", [n("blueice", arc=4.8, lift=2, kind="slide", form="ice",
                        hug=7.2, pedestal=False, spread=0, orbs=1),
                      n("blueice", arc=4.6, lift=2, kind="slide", form="ice",
                        hug=8.8, pedestal=False, spread=0, orbs=1)]),
        ("snow", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("floes", [n("accent", arc=4.6, lift=1, kind="slide", form="ice",
                     spread=0, radial=1.3),
                   n("accent", arc=4.6, lift=1, kind="slide", form="ice",
                     spread=0, radial=-1.3, orbs=1)]),
        ("serac", [n("rock", arc=3.4, lift=2, spread=0),
                   n("rock", arc=4.8, lift=2, kind="slide", form="ice",
                     spread=0, orbs=1)]),
    ], exit_beats=[
        n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
          hug=2.6, spread=0, confine=True),
        n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
          hug=2.6, spread=0, radial=0.9, orbs=1),
        n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
          hug=2.6, spread=0, radial=-0.9),
        n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
          hug=2.6, spread=0, orbs=1),
        n("packedice", arc=4.0, step_y=1, kind="slide", form="ice",
          hug=2.8, spread=0),
    ]),

    # ---- 10 --------------------------------------------------------------
    # The apiary. Honeycomb frames against the wall, one slow honey beat
    # that drops the pace to a crawl, and a slime pad that throws the body
    # onto the high comb. Sticky, golden, unlike anything beside it.
    Level("THE APIARY", "honey", rise=5, gap=2.8, exit="stair",
          band=9.5, shelf=4.5, landmark="comb", step=("honeycomb", "hop"), beats=[
        ("combs", [n("rock", arc=3.4, lift=1, spread=0, orbs=1),
                   n("rock", arc=3.3, lift=2, spread=0)]),
        ("honey", [n("honey", arc=3.3, lift=1, spread=0),
                   n("honey", arc=2.8, lift=1, spread=0, orbs=1)]),
        ("bounce", [n("slime", arc=4.6, lift=1, form="slime", spread=0),
                    n("honeycomb", arc=3.6, lift=2, spread=0, orbs=2)]),
        ("frames", [n("rock", arc=3.4, lift=3, spread=0, radial=1.3),
                    n("rock", arc=3.3, lift=3, spread=0, radial=-1.3,
                      orbs=1)]),
        ("meadow", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("cells", [n("honeycomb", arc=3.4, lift=1, spread=0),
                   n("accent", arc=3.4, lift=2, spread=0, orbs=1)]),
    ]),

    # ---- 11 --------------------------------------------------------------
    # A nether cavern lit by its own lava. The seam zigzags through the
    # floor of a black cave, glowstone knots in the walls, and every jump
    # has the glow underneath it.
    Level("THE CRUCIBLE", "nether", rise=7, gap=3.2, exit="stair",
          band=12.0, profile="plaza", landmark="totem", step=("blackstone", "hop"),
          beats=[
        ("mouth", [n("rock", arc=3.4, lift=1, spread=1, orbs=1)]),
        ("vault", [n("rock", arc=3.3, lift=1, hug=2.6, spread=0,
                     shell="grotto"),
                   n("rock", arc=3.4, lift=2, hug=2.6, spread=0,
                     shell="grotto", orbs=1),
                   n("rock", arc=3.3, lift=2, hug=2.6, spread=0,
                     shell="grotto")]),
        ("seam", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
                  n("accent", arc=3.4, lift=1, spread=0, moat=True, orbs=1),
                  n("accent", arc=3.5, lift=1, spread=0, moat=True)]),
        ("crust", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("stacks", [n("rock", arc=3.3, lift=1, spread=0, radial=1.4),
                    n("rock", arc=3.2, lift=2, spread=0, radial=-1.4,
                      orbs=1)]),
        ("soul", [n("soulsand", arc=4.4, lift=1, spread=0),
                  n("soulsand", arc=2.9, lift=1, spread=0, orbs=1)]),
    ]),

    # ---- 12 --------------------------------------------------------------
    # Colour after the dark: a reef garden on the shelf, coral heads as
    # the parkour, sea lanterns in the water, and a water channel crossed
    # twice. The palette does the work here and the jumps stay honest.
    Level("REEF GARDEN", "coral", rise=5, gap=3.0, exit="stair",
          band=11.5, profile="channel", step=("coral_red", "hop"), beats=[
        ("shallows", [n("coral_pink", arc=3.4, lift=1, spread=0, moat=True),
                      n("coral_blue", arc=3.5, lift=1, spread=0, moat=True,
                        orbs=1)]),
        ("heads", [n("coral_red", arc=3.4, lift=2, spread=0),
                   n("coral_blue", arc=3.3, lift=3, spread=0, orbs=1),
                   n("coral_pink", arc=3.4, lift=3, spread=0, radial=1.3)]),
        ("sand", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("lanterns", [n("sealantern", arc=3.5, lift=1, spread=0, moat=True),
                      n("sealantern", arc=3.4, lift=1, spread=0, moat=True,
                        orbs=1)]),
        ("fans", [n("coral_red", arc=3.4, lift=2, spread=0, radial=-1.3),
                  n("coral_pink", arc=4.6, lift=2, spread=0, orbs=1)]),
        ("brain", [n("coral_blue", arc=3.4, lift=1, spread=0),
                   n("coral_red", arc=3.5, lift=2, spread=0, orbs=1)]),
    ]),

    # ---- 13 --------------------------------------------------------------
    # The first dark-floating level: one-cell sculk landings over the void
    # side of the shelf, amethyst the only light. Quiet, slow to look at,
    # genuinely hard -- every landing one cell, every gap at reach.
    Level("THE SILENCE", "deepdark", rise=6, gap=3.4, exit="ladder",
          band=8.0, shelf=3.5, landmark="cluster", step=("deepslate", "hop"), beats=[
        ("hush", [n("rock", arc=4.6, lift=2, spread=0, pedestal=False),
                  n("rock", arc=4.6, lift=2, spread=0, pedestal=False,
                    orbs=1)]),
        ("thread", [n("accent", arc=3.0, lift=3, spread=0, pedestal=False,
                      radial=1.6),
                    n("accent", arc=3.4, lift=3, spread=0, pedestal=False,
                      radial=-1.6, orbs=1)]),
        ("gulf", [n("rock", arc=4.4, lift=1, spread=0, pedestal=False,
                    hug=8.0, orbs=1),
                  n("rock", arc=4.4, lift=1, spread=0, pedestal=False,
                    hug=9.6, orbs=1)]),
        ("shelf", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("veins", [n("accent", arc=3.4, lift=1, spread=0, pedestal=False),
                   n("rock", arc=3.3, lift=2, spread=0, pedestal=False,
                     orbs=1)]),
    ], filler=[
        ("dark", [n("rock", arc=4.6, lift=2, spread=0, pedestal=False,
                    orbs=1),
                  n("accent", arc=4.4, lift=2, spread=0, pedestal=False)]),
    ]),

    # ---- 14 --------------------------------------------------------------
    # Vertical. Inside the bell tower: sills and beams up the shaft, the
    # ladder in the middle of the level rather than at its end, and the
    # bell hanging where the climb tops out. Eight blocks gained.
    Level("THE BELFRY", "village", rise=8, gap=2.6, exit="ladder",
          band=9.5, profile="plaza", landmark="bell", step=("plaster", "hop"),
          rock="brick", accent="plaster", beats=[
        ("porch", [n("rock", arc=3.4, lift=1, hug=2.6, spread=1, orbs=1)]),
        ("sills", [n("rock", arc=3.4, lift=2, hug=2.6, spread=0,
                     shell="hall"),
                   n("accent", arc=3.3, lift=3, hug=2.8, spread=0,
                     shell="hall", orbs=1)]),
        ("rungs", [n("rock", arc=3.0, lift=3, hug=2.2, spread=1),
                   n("oak", arc=2.4, step_y=4, kind="climb",
                     climb_style="ladder", hug=2.0, pedestal=False, spread=0,
                     shell="shaft", orbs=2)]),
        ("loft", [n("accent", arc=3.4, lift=6, spread=0, hug=3.2,
                    pedestal=False),
                  n("accent", arc=3.5, lift=6, spread=0, hug=4.2,
                    pedestal=False, orbs=1)]),
        ("beams", [n("oak", arc=3.6, lift=6, form="slab", spread=0, hug=3.6,
                     pedestal=False, ceiling=1),
                   n("oak", arc=3.5, lift=6, form="slab", spread=0, hug=4.6,
                     pedestal=False, orbs=1)]),
    ], filler=[
        ("joists", [n("oak", arc=3.5, lift=5, form="slab", spread=0,
                      hug=3.4, pedestal=False, orbs=1),
                    n("oak", arc=3.6, lift=5, form="slab", spread=0,
                      hug=4.6, pedestal=False)]),
    ]),

    # ---- 15 --------------------------------------------------------------
    # The loom. Wool stripes on the wall, wool checks floating over the
    # drop, a slime pad in the middle. Short, loud, and gone -- the candy
    # level earns its keep by being the only one.
    Level("WOOLWORKS", "rainbow", rise=4, gap=2.8, exit="stair",
          band=10.0, shelf=4.0, landmark="stripes", step=("quartz", "hop"), beats=[
        ("check", [n("wool_pink", arc=3.6, lift=2, spread=0, pedestal=False),
                   n("wool_lime", arc=3.0, lift=3, spread=0, pedestal=False,
                     radial=1.5),
                   n("wool_cyan", arc=3.4, lift=3, spread=0, pedestal=False,
                     radial=-1.5, orbs=1)]),
        ("bounce", [n("slime", arc=4.6, lift=1, form="slime", spread=0),
                    n("wool_yellow", arc=3.6, lift=2, spread=0,
                      pedestal=False, orbs=2)]),
        ("deck", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("bolts", [n("wool_red", arc=3.5, lift=1, spread=0, pedestal=False),
                   n("wool_purple", arc=3.6, lift=2, spread=0,
                     pedestal=False, orbs=1)]),
        ("selvedge", [n("wool_orange", arc=4.4, lift=2, form="slab",
                        spread=0, pedestal=False, orbs=1)]),
    ]),

    # ---- 16 --------------------------------------------------------------
    # The vault. A treasure cave: raw gold in tuff walls, the hoard piled
    # where the lamplight lands, and one ledge crossed over lava with the
    # glow on the ceiling. Interior, warm-dark, greedy.
    Level("THE VAULT", "gold", rise=5, gap=2.8, exit="stair",
          band=10.5, profile="plaza", landmark="hoard", step=("rawgold", "hop"), beats=[
        ("adit", [n("rock", arc=3.4, lift=1, spread=1, orbs=1)]),
        ("strongroom", [n("rock", arc=3.3, lift=1, hug=2.6, spread=0,
                          shell="grotto"),
                        n("gold", arc=3.4, lift=2, hug=2.6, spread=0,
                          shell="grotto", orbs=1),
                        n("rock", arc=3.3, lift=2, hug=2.6, spread=0,
                          shell="grotto")]),
        ("melt", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
                  n("accent", arc=3.4, lift=1, spread=0, moat=True,
                    orbs=1)]),
        ("floor", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("seams", [n("gold", arc=3.4, lift=1, spread=0, radial=1.3),
                   n("rock", arc=3.3, lift=2, spread=0, radial=-1.3,
                     orbs=1)]),
        ("counting", [n("gold", arc=3.4, lift=1, spread=0, ceiling=2),
                      n("rock", arc=3.5, lift=2, spread=0, ceiling=2,
                        orbs=1)]),
    ]),

    # ---- 17 --------------------------------------------------------------
    # The weir. A water channel runs the length of the level and the
    # course lives in it: stepping stones barely above the surface, the
    # mill wheel turning at the bank, and one long leap onto the far side.
    Level("THE WEIR", "plains", rise=5, gap=3.0, exit="stair",
          band=12.0, profile="channel", landmark="watchtower", rock="cobble",
          accent="oak", step=("cobble", "hop"), beats=[
        ("ford", [n("cobble", arc=3.0, lift=1, spread=0, moat=True),
                  n("cobble", arc=3.0, lift=1, spread=0, moat=True, orbs=1),
                  n("cobble", arc=3.1, lift=1, spread=0, moat=True),
                  n("cobble", arc=3.0, lift=1, spread=0, moat=True,
                    orbs=1)]),
        ("bank", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                  n("cobble", arc=3.2, lift=1, spread=0)]),
        ("leap", [n("oak", arc=4.8, lift=1, spread=0, moat=True, orbs=2)]),
        ("mill", [n("oak", arc=3.4, lift=2, spread=1, ceiling=1),
                  n("cobble", arc=3.5, lift=3, spread=0, orbs=1)]),
        ("sluice", [n("cobble", arc=3.6, lift=2, spread=1),
                    n("cobble", arc=3.5, lift=2, spread=0, moat=True,
                      orbs=1)]),
        ("race", [n("oak", arc=4.9, lift=2, spread=0, moat=True, orbs=1)]),
    ]),

    # ---- 18 --------------------------------------------------------------
    # Relentless ice at the rim: long slides with nothing inboard or out,
    # then the shelf pinches and the last stretch is a blue ice tunnel cut
    # into the cliff. The fastest level, and the exit slides too.
    Level("BLUE RUN", "ice", rise=6, gap=3.2, exit="stair",
          band=9.0, shelf=4.0, ground="packedice", rock="frost", accent="snow",
          step=("blueice", "slide"), beats=[
        ("run", [n("blueice", arc=4.6, lift=1, kind="slide", form="ice",
                   spread=0, hug=4.6, pedestal=False, orbs=1),
                 n("blueice", arc=4.8, lift=1, kind="slide", form="ice",
                   spread=0, hug=5.4, pedestal=False),
                 n("blueice", arc=4.8, lift=1, kind="slide", form="ice",
                   spread=0, hug=5.6, pedestal=False, orbs=1)]),
        ("shear", [n("rock", arc=4.4, lift=2, kind="slide", form="ice",
                     spread=0, hug=5.0, pedestal=False, orbs=1)]),
        ("tunnel", [n("blueice", arc=4.2, lift=1, kind="slide", form="ice",
                      spread=0, hug=3.6, shell="tunnel"),
                    n("blueice", arc=4.4, lift=1, kind="slide", form="ice",
                      spread=0, hug=2.6, shell="tunnel", orbs=1)]),
        ("out", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("floe", [n("blueice", arc=4.0, lift=1, kind="slide", form="ice",
                    spread=0, hug=5.0, pedestal=False, orbs=1)]),
    ]),

    # ---- 19 --------------------------------------------------------------
    # The undercut. The course leaves the shelf and steps DOWN the outside
    # of the tower -- jutting sandstone benches below the rim with the sea
    # under them -- then climbs back over the crane. The tower's one
    # descent, and the longest jumps in it are the drops.
    Level("THE QUARRY", "desert", rise=4, gap=3.0, exit="stair",
          band=9.5, shelf=3.5, landmark="crane", rock="chiselled", accent="sandstone",
          step=("chiselled", "hop"), beats=[
        ("brink", [n("rock", arc=3.6, lift=1, spread=1, orbs=1)]),
        ("undercut", [n("rock", arc=4.4, step_y=-2, hug=6.8,
                        pedestal=False, spread=0, orbs=1),
                      n("rock", arc=4.6, step_y=-2, hug=7.0,
                        pedestal=False, spread=0, orbs=1),
                      n("accent", arc=4.4, step_y=-1, hug=6.8,
                        pedestal=False, spread=0)]),
        ("benches", [n("accent", arc=3.2, step_y=1, hug=6.6,
                       pedestal=False, spread=0, orbs=1),
                     n("accent", arc=3.1, step_y=1, hug=6.6,
                       pedestal=False, spread=0),
                     n("rock", arc=3.2, step_y=1, hug=6.2,
                       pedestal=False, spread=0, orbs=1),
                     n("rock", arc=3.1, step_y=1, hug=6.0,
                       pedestal=False, spread=0),
                     n("rock", arc=3.2, step_y=1, hug=5.8,
                       pedestal=False, spread=0, orbs=1)]),
        ("rim", [n("rock", arc=3.4, lift=1, spread=1, orbs=1)]),
        ("floor", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("blocks", [n("rock", arc=3.4, lift=1, spread=1),
                    n("accent", arc=3.4, lift=2, spread=0, orbs=1)]),
    ], filler=[
        ("blocks", [n("rock", arc=3.4, lift=1, spread=1, orbs=1),
                    n("accent", arc=4.4, lift=1, spread=1)]),
    ], exit_beats=[
        n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
        n("accent", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
          orbs=1),
        n("oak", arc=2.9, step_y=1, form="fence", hug=2.4, spread=0,
          pedestal=False),
        n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=-0.9,
          orbs=1),
        n("rock", arc=2.9, step_y=1, hug=2.6, spread=0),
    ]),

    # ---- 20 --------------------------------------------------------------
    # One plank wide, two hundred blocks of air. The rope bridge runs out
    # at the rim on posts, sags a block in the middle, and comes back.
    # Nothing here is hard to land; all of it is hard to watch.
    Level("ROPE BRIDGE", "jungle", rise=5, gap=3.4, exit="vine",
          band=8.5, shelf=4.0, rock="junglelog", accent="jungleleaf",
          step=("oak", "hop"), beats=[
        ("post", [n("rock", arc=3.4, lift=2, spread=0, hug=6.0,
                    pedestal=False, orbs=1)]),
        ("planks", [n("oak", arc=3.2, lift=2, form="trapdoor", spread=0,
                      hug=7.5, pedestal=False),
                    n("oak", arc=3.2, lift=1, spread=0, hug=9.0,
                      pedestal=False, orbs=1),
                    n("oak", arc=3.2, lift=2, form="trapdoor", spread=0,
                      hug=10.5, pedestal=False),
                    n("oak", arc=3.3, lift=2, spread=0, hug=9.0,
                      pedestal=False, orbs=1)]),
        ("span", [n("oak", arc=4.6, lift=2, spread=0, hug=7.5,
                    pedestal=False, orbs=2)]),
        ("land", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("guys", [n("rock", arc=3.4, lift=1, hug=6.0, spread=0,
                    pedestal=False),
                  n("oak", arc=3.4, lift=2, hug=6.4, spread=0,
                    pedestal=False, orbs=1)]),
    ], filler=[
        ("cable", [n("oak", arc=3.4, lift=1, spread=0, hug=6.2,
                     pedestal=False, orbs=1),
                   n("oak", arc=3.4, lift=1, spread=0, hug=6.6,
                     pedestal=False)]),
    ]),

    # ---- 21 --------------------------------------------------------------
    # Basalt flues under a low soffit: blackstone columns packed close,
    # every jump under a lid, magma glowing in the gaps. The opposite
    # design to the Crucible with the same palette -- tight, not cavern.
    Level("BASALT FLUES", "nether", rise=7, gap=2.8, exit="stair",
          band=7.5, shelf=4.5, ground="blackstone", rock="blackstone", accent="magma",
          step=("blackstone", "hop"), beats=[
        ("flues", [n("rock", arc=3.0, lift=2, spread=0, ceiling=2),
                   n("rock", arc=3.0, lift=2, spread=0, ceiling=2, orbs=1),
                   n("rock", arc=3.1, lift=2, spread=0, ceiling=2)]),
        ("vents", [n("accent", arc=3.4, lift=3, spread=0, moat=True),
                   n("accent", arc=3.3, lift=3, spread=0, moat=True,
                     orbs=1)]),
        ("crust", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("stacks", [n("rock", arc=3.2, lift=1, spread=0, radial=1.4,
                      ceiling=1),
                    n("rock", arc=3.2, lift=1, spread=0, radial=-1.4,
                      ceiling=1, orbs=1)]),
        ("draught", [n("rock", arc=3.2, lift=2, spread=0, ceiling=2),
                     n("accent", arc=3.4, lift=3, spread=0, moat=True,
                       orbs=1)]),
    ], filler=[
        ("flues", [n("rock", arc=3.2, lift=2, spread=0, ceiling=2, orbs=1),
                   n("rock", arc=3.0, lift=2, spread=0, ceiling=2)]),
        ("vents", [n("accent", arc=3.4, lift=3, spread=0, moat=True),
                   n("accent", arc=3.3, lift=3, spread=0, moat=True,
                     orbs=1)]),
    ], exit_beats=[
        n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
        n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
        n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
          orbs=1),
        n("rock", arc=3.0, step_y=1, hug=2.4, spread=1),
        n("oak", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
          hug=2.0, pedestal=False, spread=0, orbs=2),
    ]),

    # ---- 22 --------------------------------------------------------------
    # The pillars. Obsidian columns out at the rim with purpur slabs slung
    # between them, chorus light, and the whole drop under every arc. The
    # most exposed level, left by a bubble ride.
    Level("THE PILLARS", "end", rise=6, gap=3.4, exit="bubble",
          band=10.5, shelf=3.5, landmark="totem", step=("purpur", "hop"), beats=[
        ("pillars", [n("accent", arc=3.4, lift=3, spread=0, hug=6.8,
                       pedestal=False),
                     n("accent", arc=3.3, lift=4, spread=0, hug=8.4,
                       pedestal=False, orbs=1),
                     n("accent", arc=3.4, lift=5, spread=0, hug=9.6,
                       pedestal=False)]),
        ("slabs", [n("rock", arc=4.4, lift=4, form="slab", spread=0,
                     hug=5.6, pedestal=False),
                   n("rock", arc=4.2, lift=4, form="slab", spread=0,
                     hug=5.2, pedestal=False, orbs=1)]),
        ("void", [n("rock", arc=6.2, lift=1, spread=0, hug=5.0, orbs=2)]),
        ("stone", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("rods", [n("accent", arc=3.4, lift=1, hug=5.6, spread=0,
                    pedestal=False),
                  n("accent", arc=3.5, lift=2, hug=6.0, spread=0,
                    pedestal=False, orbs=1)]),
    ], filler=[
        ("shards", [n("accent", arc=3.6, lift=1, spread=0, hug=5.4,
                      pedestal=False, orbs=1),
                    n("rock", arc=4.4, lift=1, spread=0, hug=5.8,
                      pedestal=False)]),
    ]),

    # ---- 23 --------------------------------------------------------------
    # A cave of giant mushrooms. The great red cap fills the room, stem
    # columns carry the course, shroomlight does the lighting. Soft
    # shapes, low light, bouncy middle.
    Level("SPORE HOLLOW", "mushroom", rise=5, gap=3.0, exit="vine",
          band=11.0, profile="plaza", landmark="greatcap",
          step=("mushroomstem", "hop"), beats=[
        ("litter", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                    n("rock", arc=3.4, lift=1, spread=1)]),
        ("hollow", [n("rock", arc=3.3, lift=1, hug=2.6, spread=0,
                      shell="grotto"),
                    n("rock", arc=3.4, lift=2, hug=2.6, spread=0,
                      shell="grotto", orbs=1)]),
        ("caps", [n("accent", arc=5.2, lift=2, form="wide", spread=1,
                    pedestal_style="mushroomstem", orbs=1),
                  n("accent", arc=5.4, lift=2, form="wide", spread=1,
                    pedestal_style="mushroomstem")]),
        ("pad", [n("slime", arc=4.8, lift=1, form="slime", spread=0),
                 n("accent", arc=4.4, lift=2, form="wide", spread=1,
                   orbs=2)]),
        ("stems", [n("rock", arc=3.6, lift=3, spread=0),
                   n("rock", arc=3.4, lift=3, spread=0, orbs=1)]),
        ("gills", [n("accent", arc=4.6, lift=2, form="wide", spread=1,
                     orbs=1)]),
    ]),

    # ---- 24 --------------------------------------------------------------
    # The archive. Bookshelf walls, a gallery hall with lanterns, oak
    # beams over a reading room, and the ladder out is behind the shelves.
    # Warm interior light and not one block of stone parkour.
    Level("THE ARCHIVE", "library", rise=6, gap=2.8, exit="ladder",
          band=10.0, profile="plaza", step=("spruce", "hop"), beats=[
        ("lobby", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                   n("oak", arc=3.4, lift=1, spread=1)]),
        ("stacks", [n("rock", arc=3.3, lift=1, hug=3.0, spread=0,
                      shell="hall"),
                    n("rock", arc=3.4, lift=2, hug=3.0, spread=0,
                      shell="hall", orbs=1),
                    n("rock", arc=3.3, lift=2, hug=3.0, spread=0,
                      shell="hall")]),
        ("desks", [n("oak", arc=3.5, lift=1, spread=0, radial=1.3),
                   n("oak", arc=3.4, lift=2, spread=0, radial=-1.3,
                     orbs=1)]),
        ("gallery", [n("oak", arc=3.6, lift=2, form="slab", spread=0,
                       hug=3.4, pedestal=False, ceiling=1),
                     n("oak", arc=3.5, lift=3, form="slab", spread=0,
                       hug=4.4, pedestal=False, orbs=1)]),
        ("hearth", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("lectern", [n("rock", arc=3.4, lift=1, spread=0),
                     n("rock", arc=3.3, lift=2, spread=0, orbs=1)]),
    ], exit_beats=[
        n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
        n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
          orbs=1),
        n("rock", arc=2.9, step_y=1, hug=2.4, spread=1, radial=-0.9),
        n("oak", arc=2.4, step_y=4, kind="climb", climb_style="ladder",
          hug=2.0, pedestal=False, spread=0, orbs=2),
    ]),

    # ---- 25 --------------------------------------------------------------
    # Dusk on the pumpkin rows. Jack-o-lantern glow, hay underfoot, the
    # scarecrow's cousin standing guard as a lantern post, and the farm
    # read the second time round with the lights on.
    Level("PUMPKIN ROWS", "farm", rise=4, gap=2.8, exit="stair",
          band=10.5, landmark="scarecrow", glow="glowstone", step=("pumpkin", "hop"),
          beats=[
        ("rows", [n("pumpkin", arc=3.6, lift=1, spread=0, orbs=1),
                  n("pumpkin", arc=3.5, lift=1, spread=0),
                  n("pumpkin", arc=3.6, lift=1, spread=0, orbs=1)]),
        ("patch", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("wain", [n("oak", arc=3.4, lift=1, spread=1, ceiling=1),
                  n("hay", arc=3.3, lift=2, spread=0, orbs=1)]),
        ("lanterns", [n("glowstone", arc=3.5, lift=1, spread=0,
                        radial=1.3),
                      n("pumpkin", arc=3.4, lift=1, spread=0, radial=-1.3,
                        orbs=1)]),
        ("bales", [n("hay", arc=3.4, lift=2, spread=0),
                   n("hay", arc=4.6, lift=2, spread=0, orbs=1)]),
    ]),

    # ---- 26 --------------------------------------------------------------
    # The warped grove. Teal nylium, shroomlight crowns, and a bubble lift
    # in the middle of the level that carries the body to an upper storey
    # of caps before the drop back down.
    Level("THE GROVE", "warped", rise=6, gap=3.0, exit="bubble",
          band=11.0, shelf=5.0, step=("warped", "hop"), beats=[
        ("nylium", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                    n("rock", arc=3.5, lift=2, spread=1)]),
        ("lift", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
                  n("prismarine", arc=2.4, step_y=4, kind="bubble",
                    climb_style="water", hug=2.0, pedestal=False, spread=0,
                    orbs=2)]),
        ("crowns", [n("accent", arc=4.8, lift=6, form="wide", spread=0,
                      pedestal=False),
                    n("accent", arc=5.0, lift=6, form="wide", spread=0,
                      pedestal=False, orbs=1)]),
        ("descent", [n("ground", arc=6.8, lift=0, form="floor", orbs=2)]),
        ("fungus", [n("rock", arc=3.4, lift=1, spread=1),
                    n("accent", arc=4.6, lift=1, spread=1, orbs=1)]),
    ], filler=[
        ("thicket", [n("rock", arc=3.4, lift=1, spread=1, orbs=1),
                     n("accent", arc=3.6, lift=1, spread=1)]),
    ]),

    # ---- 27 --------------------------------------------------------------
    # Dust devils. Hoodoo country: thin terracotta spires with capstones,
    # the biggest single drops in the tower, and a rhythm that never
    # settles -- three up, one long fall, two up, gone.
    Level("DUST DEVILS", "mesa", rise=7, gap=3.6, exit="stair",
          band=12.5, shelf=3.5, landmark="hoodoo", step=("terra_white", "hop"), beats=[
        ("spires", [n("rock", arc=3.4, lift=3, spread=0,
                      pedestal_style="terra_orange"),
                    n("accent", arc=3.3, lift=4, spread=0,
                      pedestal_style="terra_orange", orbs=1),
                    n("rock", arc=3.4, lift=5, spread=0,
                      pedestal_style="terra_orange")]),
        ("fall", [n("ground", arc=6.2, lift=0, form="floor", orbs=2)]),
        ("caps", [n("accent", arc=3.4, lift=1, spread=0, radial=1.4),
                  n("rock", arc=3.3, lift=2, spread=0, radial=-1.4,
                    orbs=1)]),
        ("mesa", [n("accent", arc=4.2, lift=1, spread=0, hug=7.0,
                    pedestal=False, orbs=1),
                  n("accent", arc=3.6, lift=1, spread=0, hug=8.6,
                    pedestal=False, orbs=1)]),
        ("devils", [n("rock", arc=3.4, lift=2, spread=0,
                      pedestal_style="terra_orange"),
                    n("accent", arc=3.5, lift=3, spread=0,
                      pedestal_style="terra_orange", orbs=1)]),
    ]),

    # ---- 28 --------------------------------------------------------------
    # The sea gate. A monument hall: prismarine, sea lantern light, water
    # slots in the floor, and the gate arch the course passes through at
    # the end. Cool, ordered, symmetrical where the mesa was chaos.
    Level("THE SEA GATE", "prismarine", rise=5, gap=2.8, exit="stair",
          band=12.0, profile="plaza", landmark="arch",
          step=("darkprismarine", "hop"), beats=[
        ("steps", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                   n("rock", arc=3.4, lift=1, spread=1)]),
        ("hall", [n("rock", arc=3.3, lift=1, hug=3.2, spread=0,
                    shell="hall"),
                  n("rock", arc=3.4, lift=1, hug=3.2, spread=0,
                    shell="hall", orbs=1),
                  n("rock", arc=3.3, lift=2, hug=3.2, spread=0,
                    shell="hall")]),
        ("slots", [n("accent", arc=3.5, lift=1, spread=0, moat=True),
                   n("accent", arc=3.4, lift=1, spread=0, moat=True,
                     orbs=1)]),
        ("court", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("dark", [n("darkprismarine", arc=3.4, lift=1, spread=0,
                    radial=1.3),
                  n("darkprismarine", arc=3.3, lift=2, spread=0,
                    radial=-1.3, orbs=1)]),
        ("gate", [n("rock", arc=3.4, lift=2, spread=0, ceiling=2),
                  n("accent", arc=4.6, lift=2, spread=0, orbs=1)]),
    ]),

    # ---- 29 --------------------------------------------------------------
    # The cornice. A snow ridge at the rim with icicles under it, wind in
    # the fog, and halfway along -- a lit cabin crossed *inside*, three
    # seconds of warm lamplight between two cold exposures.
    Level("THE CORNICE", "snow", rise=5, gap=3.0, exit="stair",
          band=8.5, shelf=4.0, landmark="cabin", step=("spruce", "hop"), beats=[
        ("ridge", [n("rock", arc=3.6, lift=1, spread=0, hug=5.8, orbs=1),
                   n("rock", arc=3.5, lift=2, spread=0, hug=6.0),
                   n("accent", arc=3.4, lift=2, spread=0, hug=5.6,
                     orbs=1)]),
        ("cabin", [n("spruce", arc=3.3, lift=1, hug=2.8, spread=0,
                     shell="tunnel"),
                   n("spruce", arc=3.4, lift=1, hug=2.8, spread=0,
                     shell="tunnel", orbs=1)]),
        ("drift", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("cornice", [n("rock", arc=3.4, lift=1, spread=0, hug=7.4,
                       pedestal=False),
                     n("rock", arc=3.3, lift=2, spread=0, hug=8.8,
                       pedestal=False, orbs=1)]),
        ("posts", [n("spruce", arc=3.0, lift=2, form="fence", spread=0,
                     radial=1.2),
                   n("spruce", arc=3.0, lift=2, form="fence", spread=0,
                     radial=-1.2, orbs=1)]),
    ]),

    # ---- 30 --------------------------------------------------------------
    # The wart fields. Vivid crimson nylium, wart blocks in ranks, giant
    # fungus trunks against the wall, and the exit is a ladder up one of
    # them. The loudest colour in the tower, kept brief.
    Level("WART FIELDS", "crimson", rise=6, gap=3.0, exit="ladder",
          band=9.5, shelf=4.5, step=("crimson", "hop"), beats=[
        ("fields", [n("accent", arc=3.5, lift=1, spread=0, orbs=1),
                    n("accent", arc=3.4, lift=1, spread=0),
                    n("accent", arc=3.5, lift=2, spread=0, orbs=1)]),
        ("trunks", [n("rock", arc=3.4, lift=2, spread=0, radial=1.4),
                    n("rock", arc=3.3, lift=3, spread=0, radial=-1.4,
                      orbs=1)]),
        ("nylium", [n("ground", arc=4.6, lift=0, form="floor", orbs=1)]),
        ("canes", [n("rock", arc=3.4, lift=1, spread=0, ceiling=2),
                   n("rock", arc=3.3, lift=2, spread=0, ceiling=2,
                     orbs=1)]),
        ("glow", [n("shroomlight", arc=3.5, lift=2, spread=0),
                  n("accent", arc=4.6, lift=2, spread=0, orbs=1)]),
    ]),

    # ---- 31 --------------------------------------------------------------
    # Echo shaft. The dark vertical: a sculk well climbed from inside,
    # amethyst light partway, the hardest one-cell landings in the tower
    # at the top. Eight blocks gained in near-silence.
    Level("ECHO SHAFT", "deepdark", rise=8, gap=2.6, exit="ladder",
          band=8.0, profile="plaza", landmark="cluster", rock="deepslate",
          accent="sculk", step=("sculk", "hop"), beats=[
        ("lip", [n("rock", arc=3.4, lift=1, hug=2.8, spread=1, orbs=1)]),
        ("well", [n("rock", arc=3.0, lift=2, hug=2.2, spread=1),
                  n("oak", arc=2.4, step_y=4, kind="climb",
                    climb_style="ladder", hug=2.0, pedestal=False, spread=0,
                    shell="shaft", orbs=2)]),
        ("gallery", [n("accent", arc=3.4, lift=5, spread=0, hug=3.2,
                       pedestal=False),
                     n("accent", arc=3.3, lift=5, spread=0, hug=4.0,
                       pedestal=False, orbs=1)]),
        ("reach", [n("rock", arc=4.7, lift=5, spread=0, pedestal=False),
                   n("rock", arc=4.6, lift=5, spread=0, pedestal=False,
                     orbs=1)]),
        ("thread", [n("accent", arc=3.0, lift=6, spread=0, pedestal=False,
                      radial=1.6),
                    n("accent", arc=3.4, lift=6, spread=0, pedestal=False,
                      radial=-1.6, orbs=1)]),
    ], filler=[
        ("dark", [n("rock", arc=4.5, lift=5, spread=0, pedestal=False,
                    orbs=1),
                  n("accent", arc=4.4, lift=5, spread=0, pedestal=False)]),
    ]),

    # ---- 32 --------------------------------------------------------------
    # The white stair. A quartz colonnade with long views: pale galleries,
    # gold trims, diorite underfoot. Deliberately elegant and mild -- the
    # breath before the gate, and the light after the dark shaft.
    Level("THE WHITE STAIR", "quartz", rise=5, gap=2.8, exit="stair",
          band=13.0, profile="plaza", landmark="arch", step=("diorite", "hop"),
          beats=[
        ("gallery", [n("ground", arc=4.6, lift=0, form="floor", orbs=1),
                     n("rock", arc=3.4, lift=1, spread=1)]),
        ("colonnade", [n("rock", arc=3.4, lift=2, spread=0, radial=1.3),
                       n("rock", arc=3.3, lift=2, spread=0, radial=-1.3,
                         orbs=1),
                       n("rock", arc=3.4, lift=2, spread=0, radial=1.3)]),
        ("trim", [n("accent", arc=3.5, lift=3, spread=0),
                  n("accent", arc=3.4, lift=3, form="slab", spread=0,
                    orbs=1)]),
        ("terrace", [n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("plinths", [n("rock", arc=3.4, lift=1, spread=0),
                     n("sub", arc=3.5, lift=2, spread=0, orbs=1)]),
    ], exit_beats=[
        n("quartz", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True,
          deco="lamp"),
        n("diorite", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
        n("quartz", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9,
          orbs=1),
        n("diorite", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9),
        n("quartz", arc=2.9, step_y=1, hug=2.4, spread=0, deco="lamp"),
        n("quartz", arc=3.0, step_y=1, hug=2.6, spread=0, orbs=1),
    ]),

    # ---- 33 --------------------------------------------------------------
    # The gate. An obsidian arch across the corridor, one last leap under
    # it, and the meadow again a hundred and eighty blocks higher. Short
    # and calm: a threshold, not a test, and the one place the loop shows.
    Level("THE GATE", "end", rise=4, gap=3.0, exit="stair",
          band=11.0, shelf=5.0, landmark="totem", rock="purpur", accent="obsidian",
          step=("obsidian", "hop"), beats=[
        ("approach", [n("ground", arc=4.4, lift=0, form="floor", orbs=1),
                      n("rock", arc=3.4, lift=1, spread=1)]),
        ("arch", [n("accent", arc=3.2, lift=2, spread=0, ceiling=3),
                  n("accent", arc=3.2, lift=2, spread=0, ceiling=3,
                    orbs=2)]),
        ("threshold", [n("rock", arc=4.6, lift=1, spread=1),
                       n("ground", arc=4.8, lift=0, form="floor", orbs=1)]),
        ("pylons", [n("accent", arc=3.4, lift=1, spread=1),
                    n("rock", arc=3.5, lift=2, spread=0, orbs=1)]),
        ("span", [n("accent", arc=4.6, lift=2, spread=1, orbs=1)]),
    ], filler=[
        ("court", [n("rock", arc=3.6, lift=1, spread=1, orbs=1),
                   n("accent", arc=4.4, lift=1, spread=1)]),
    ], exit_beats=[
        n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, confine=True),
        n("accent", arc=3.0, step_y=1, hug=2.4, spread=0, radial=0.9,
          orbs=1),
        n("rock", arc=2.9, step_y=1, hug=2.4, spread=0, radial=-0.9),
        n("rock", arc=3.0, step_y=1, hug=2.4, spread=0, orbs=1),
        n("rock", arc=2.9, step_y=1, hug=2.6, spread=0),
    ]),
)
