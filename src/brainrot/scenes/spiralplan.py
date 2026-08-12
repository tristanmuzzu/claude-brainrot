"""The spiral tower: one solid cone, one helical trough, and the climb up it.

This module is the whole of the *Parkour Spiral* format and none of its
rendering. There is no raylib import on purpose -- the geometry, the physics
and every guarantee the scene makes are testable in a plain interpreter with
no window, which is what makes a sweep of forty runs something you can afford
after every change.

What the format actually is
---------------------------

Two earlier attempts in this project got the shape wrong, in opposite
directions, and it is worth writing down what settled it. The first built a
cylinder with jump blocks hung round the outside. The second read the owner's
reference screenshot -- a view of the tower's underside, showing what looks
like a forest of grey columns -- as *platforms standing on stilts*, and built a
stack of hexagonal plates.

Hielke's own screenshots of Parkour Spiral 1-3 say it is neither:

* The tower is **one solid mass**, and it is an **inverted cone** -- narrow at
  the waterline, flaring as it rises. Every wide shot shows it.
* The "column forest" is the **skin**, not the structure: vertical one-cell
  ribs alternating in and out for the tower's whole height, a corduroy
  surface. Full-resolution crops of the underside show them running unbroken
  from the themed lip down into the sea with nothing behind them.
* The parkour is a **continuous helical trough** cut round the outside. You
  are always in a corridor: the drop on your outboard side, the flank of the
  revolution above on your inboard side, and its floor slab as a ceiling
  eighteen blocks over your head.
* **Several themed sections fit in one revolution**, not one -- a single band
  in the reference runs end, farm, village, plains, mesa in one arc -- and the
  seam between two is *hard*, with no blending.
* **The parkour is built into the theme's own ground.** You run over the
  desert's dunes and across its pond on lily pads. Floating blocks over the
  void are the minority, and they are a *theme* (the wool section) rather than
  the default.

Which is why the generation order here is the opposite of the last attempt's,
and that inversion is the single most important thing in the file:

**The course is laid first, and the terrain is painted around it afterwards.**

The old order -- build the world, then negotiate a course through it --
started at thirteen per cent of nodes falling through to an unchecked
emergency hop and took a long session of counters to get down. Terrain that is
laid *second* cannot block a course, because it is simply not written into the
cells the course has already reserved. A human map-maker builds this way too.

The building is analytic
------------------------

:meth:`Cone.rock` answers "is this cell inside the tower" in closed form, for
any cell, at any time, with no memory. Nothing has to be generated ahead of the
course and nothing can appear behind it. The previous version's building was
streamed into an occupancy map as the course advanced, which meant a wall
could be built through a jump that had already been solved -- and the four
reservations existed largely to defend against that. Three of them are still
here, because terrain and course blocks are still written; the class of bug
where the *building* grows into a solved arc is gone by construction.
"""

from __future__ import annotations

import math

from .parkourkit import (  # noqa: F401
    AIR_MAX,
    AIR_MIN,
    AIR_SPEED,
    ARC_SAMPLES,
    BODY_H,
    BUBBLE_SPEED,
    CHEST,
    CLIMB_SPEED,
    EDGE,
    EYE,
    FORMS,
    GRAVITY,
    HEADROOM,
    ICE_AIR,
    ICE_RUN,
    JUMP_V,
    MATERIALS,
    MIN_HOP,
    ORB_FRACTIONS,
    RUN_SPEED,
    SCAFFOLD_SPEED,
    SEE_THROUGH,
    SOUL_SPEED,
    SPREAD,
    SPRINGY,
    VY_MAX,
    VY_MIN,
    WALK_SPEED,
    WEB_SPEED,
    Move,
    arc_leg,
    body_cells,
    bounce_launch,
    cells_of,
    deco,
    fall_speed,
    fit_gap,
    footprint,
    hop_span,
    ifloor,
    iround,
    land_point,
    line_cells,
    line_leg,
    quantise,
    standing_cells,
    takeoff_point,
    unit,
    wrap_angle,
)

# ---------------------------------------------------------------------------
# Materials this format adds
# ---------------------------------------------------------------------------
#
# The kernel ships the ones every scene in the project shares. These are the
# ground cover, and the reason there are so many is the one thing the reference
# is loudest about: the tower is a **grey mass with saturated stripes on it**.
# Neutral architecture, loud terrain. A theme whose ground is another shade of
# stone is a theme nobody will notice going past at seven metres a second.
MATERIALS.update({
    # -- overworld ground
    "grass": ((104, 168, 70), "dirt", 0.04),
    "podzol": ((110, 82, 48), "dirt", 0.04),
    "coarse": ((136, 106, 76), "dirt", 0.03),
    "gravel": ((136, 132, 128), "speck", 0.04),
    "farmland": ((104, 74, 46), "dirt", 0.03),
    "hay": ((214, 176, 46), "grain", 0.03),
    "sand": ((238, 226, 168), "sand", 0.02),
    "redsand": ((208, 118, 56), "sand", 0.03),
    "clay": ((166, 170, 180), "concrete", 0.02),
    # -- mesa
    "terra_orange": ((198, 106, 50), "bricks", 0.03),
    "terra_white": ((214, 200, 190), "bricks", 0.02),
    "terra_red": ((150, 60, 42), "bricks", 0.03),
    "terra_yellow": ((216, 168, 68), "bricks", 0.03),
    # -- village
    "brick": ((160, 84, 68), "bricks", 0.02),
    "plaster": ((226, 218, 200), "stonebrick", 0.02),
    "roof": ((150, 72, 56), "bricks", 0.03),
    # -- jungle
    "junglelog": ((110, 84, 46), "grain", 0.03),
    "jungleleaf": ((58, 140, 44), "leaves", 0.05),
    "bamboo": ((150, 176, 62), "grain", 0.03),
    # -- nether, both flavours
    "crimson": ((136, 44, 56), "grain", 0.03),
    "crimsonnylium": ((132, 40, 44), "dirt", 0.04),
    "warped": ((44, 122, 118), "grain", 0.03),
    "warpednylium": ((30, 108, 104), "dirt", 0.04),
    "shroomlight": ((248, 168, 74), "lantern", 0.02),
    "lava": ((236, 132, 32), "lantern", 0.05),
    # -- the end
    "chorus": ((136, 96, 148), "grain", 0.03),
    # -- the deep
    "sculk": ((28, 40, 48), "speck", 0.04),
    "sculkvein": ((44, 92, 96), "leaves", 0.05),
    "dripstone": ((150, 120, 104), "grain", 0.03),
    "calcite": ((222, 222, 216), "speck", 0.02),
    "amethyst": ((156, 116, 204), "grain", 0.04),
    # -- mushroom
    "mushroomred": ((196, 66, 58), "speck", 0.05),
    "mushroomstem": ((224, 218, 202), "grain", 0.03),
    # -- the wool section, which is the one place floating parkour is on-theme
    "wool_red": ((176, 62, 58), "wool", 0.02),
    "wool_orange": ((222, 132, 48), "wool", 0.02),
    "wool_yellow": ((232, 202, 68), "wool", 0.02),
    "wool_lime": ((124, 196, 62), "wool", 0.02),
    "wool_cyan": ((44, 168, 178), "wool", 0.02),
    "wool_blue": ((60, 96, 190), "wool", 0.02),
    "wool_purple": ((136, 62, 178), "wool", 0.02),
    "wool_pink": ((228, 132, 176), "wool", 0.02),
    # -- the designed tower's own places
    "bookshelf": ((146, 108, 62), "bricks", 0.04),
    "honeycomb": ((222, 156, 40), "bricks", 0.03),
    "rawgold": ((216, 176, 72), "cobble", 0.03),
    "coral_red": ((202, 62, 72), "speck", 0.04),
    "coral_pink": ((230, 122, 152), "speck", 0.04),
    "coral_blue": ((72, 112, 204), "speck", 0.04),
    "wartblock": ((146, 24, 30), "leaves", 0.04),
    "pumpkin": ((218, 126, 34), "grain", 0.03),
    "diorite": ((216, 212, 208), "speck", 0.02),
    # -- the neutral mass everything else is set against. A *cliff*, not
    # masonry: the reference's core face is dark weathered rock with the
    # course's own colours set against it, and the light stone brick this
    # used to be filled half of every frame with something that read as a
    # castle wall from a different game.
    "conestone": ((88, 84, 82), "cobble", 0.03),
    "conerib": ((74, 71, 69), "cobble", 0.03),
    # The soffit is its own material and its base is deliberately far brighter
    # than the stone beside it. Vanilla shades a downward face to 0.50 and this
    # project keeps that constant honestly, so a mid-grey ceiling measured
    # RGB 62 against a bright sky -- a black lid over every frame. Minecraft
    # gets away with 0.50 because its smooth lighting carries skylight in under
    # an overhang; this renderer has no such thing, so the compensation goes
    # into the material. The soffit is the single largest surface in the format
    # and it has to read as stone.
    "conesoffit": ((206, 202, 194), "cobble", 0.03),
})

#: Props whose origin is at the *top* of the model, so they hang from the cell
#: they are given rather than stand on it. Getting this wrong buries them.
HANGING = frozenset(("vinehang", "dripstone", "chain"))

#: Every furniture model the scene has to load. Derived from the themes rather
#: than typed out again, because a theme that names a prop nobody loaded draws
#: nothing and says nothing about it.
PROP_KINDS: tuple[str, ...] = ()

#: The eight wools, in the order a rainbow section lays them.
WOOLS = ("wool_red", "wool_orange", "wool_yellow", "wool_lime",
         "wool_cyan", "wool_blue", "wool_purple", "wool_pink")


# ---------------------------------------------------------------------------
# The cone
# ---------------------------------------------------------------------------

#: Rim radius at the world's base, and how much of it a block of height buys.
#:
#: The flare is the reference's whole silhouette and it is not a free
#: parameter: measured off ``parkour-spiral-3_pic_0`` the tower is about 1.7
#: times as wide at the crown as at the waterline over roughly fourteen
#: revolutions, which is a shade under a twentieth of a block of radius per
#: block of height.
BASE_R = 24.0
FLARE = 0.05

# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------
#
# The trough is not a ramp. This is the second-biggest correction this format
# has had and it came from the owner looking at a render of the finished tower
# and saying: without the parkour you could still just walk up this.
#
# He was right, and it was a property of the geometry rather than of the
# course. The trough used to climb one block every eight of arc -- a spiral
# staircase, and a one-block step is something a body walks up without
# jumping. Every landing the generator laid was therefore optional scenery on
# top of a ramp that already went all the way to the top.
#
# So the trough is now a stack of **levels**: a flat terrace, then a chasm with
# no floor in it at all, then the next terrace four to six blocks higher.
# Neither half of that is walkable -- you cannot walk over a hole and you
# cannot walk up four blocks -- so the only way out of a level is the parkour
# out of it. ``tools/spiral_probe.py`` has a walker that tries, and reports how
# far it gets.

#: Levels in one revolution. An integer, and that matters: the ceiling over
#: level ``i`` is the floor slab of level ``i + LEVELS_PER_TURN``, and if that
#: were not a whole number of levels the two would step at different bearings
#: and the soffit would saw up and down against the floor under it.
LEVELS_PER_TURN = 3
LEVEL_ARC = 2 * math.pi / LEVELS_PER_TURN

#: How much higher each level is than the one before.
#:
#: The floor is five because a body jumps 1.25 and steps up one block without
#: thinking about it, so anything up to two is walkable and three is one
#: block-place away from it. The ceiling is six because the sum of
#: ``LEVELS_PER_TURN`` of these is the height of one turn of the trough, and
#: what is left after the floor slab has to stay taller than a body can jump.
LEVEL_RISE = (4, 6)
#: ...which makes one revolution 16 to 28 blocks rather than a fixed 22. That
#: variation is deliberate and is the other half of the same complaint: a tower
#: that gains exactly the same height every revolution reads as a machine part.
TURN_MIN = LEVEL_RISE[0] * LEVELS_PER_TURN
TURN_MAX = LEVEL_RISE[1] * LEVELS_PER_TURN

#: Blocks of arc at the end of every level with **no floor at all** -- not a
#: thin bridge, not a step down, nothing.
#:
#: Sized to be exactly the genre's signature jump, against this project's own
#: numbers rather than against a guess. The crossing descends one block, and
#: ``hop_span(-1)`` allows 2.35 to 4.98 m stand-point to stand-point; the arc
#: asked for is the chasm plus 1.4, and the edge offsets take about 0.74 back.
#: At a 4.4-block chasm that lands on 5.1 m and the jump is refused outright --
#: so the widest chasms were the ones nothing could cross.
#:
#: And only a *climb* makes it crossable at all: the level beyond is four to six
#: blocks up, and you cannot jump a chasm and gain four blocks in the same move.
#: So the chasm is crossable and the boundary as a whole is not.
#:
#: It was ten blocks in the first draft and that was wrong in an instructive
#: way. A staircase gaining seven blocks needs twenty of arc; past the chasm
#: the next level's floor slab is six cells of solid rock; so the stair ran
#: straight into it and every candidate for the last four steps was inside the
#: tower. The climb belongs on the ground you are standing on, and the chasm is
#: the jump at the top of it.
GAP_ARC = (2.8, 3.9)

#: How deep the walkable trough is, radially.
#:
#: The reference's band is ten to twenty blocks and this is at the bottom of
#: that range, for a reason that is pure geometry and cost an afternoon to see.
#: The body runs *outside* a convex core, so a camera looking along the trough
#: is looking down a tangent -- and a tangent to a circle you are outside of
#: never meets it. Measured at a thirteen-block band: the core wall sits fifty
#: to ninety degrees off the direction of travel at every bearing, and the
#: strip's horizontal field is fifty-two. The wall was drawn, correctly, on
#: every frame, and appeared on none of them; every frame was ground, sky and
#: soffit, which reads as floating islands rather than as a tower.
#:
#: What brings it back is not aiming at it -- aiming at it means running
#: sideways -- it is standing nearer to it. At four and a half metres the wall
#: enters the frame about nine metres ahead, which is inside the distance over
#: which the trough's own curvature carries it away again.
BAND = 9.5
#: The widest corridor any level may ask for. The continuous face check in
#: ``_path_clear`` uses it as its cheap radial bound, so a level wider than
#: this would put its course outside the guard.
BAND_MAX = 13.5
#: Cells of terrace floor slab -- which is also, seen from the trough below,
#: the thickness of your ceiling.
#:
#: This number and the level rises are one decision, and it is the decision
#: that makes the tower read as a *mass* rather than as a screw thread. Solid
#: fraction is ``FLOOR_T`` over the height of one turn: at three in sixteen the
#: ledges came out as thin plates with daylight between them from every angle,
#: which is not what any reference shot looks like. At five in twelve-to-
#: eighteen it is between a quarter and a half solid, the soffit overhead has
#: real depth to it, and the open gap is still seven to thirteen blocks -- as
#: tall as the band is wide or better, so the sky and the drop are both still
#: there on your outboard side.
#:
#: A thick slab is not expensive: only its top cell (walked on) and its bottom
#: cell (the soffit) are ever seen across the whole band, and :meth:`Cone._slab`
#: emits the rest of it as a rim only.
FLOOR_T = 5
#: How many cells deep the flank and the core are actually built. The inside
#: of a solid cone is never seen; :meth:`Cone.rock` still says it is rock.
SKIN = 2
#: Ribs round the circumference. At the base that is a rib every 1.9 cells,
#: which is what the reference's corduroy measures.
RIBS = 56
#: How far a rib stands proud.
RIB_D = 1

#: How far below the body the world is drawn.
BUILD_BELOW = 46
#: ...and how far above. One trough's ceiling is up to ``TURN_MAX`` up, and you
#: must be able to see the one above that or the tower stops at the top of the
#: frame.
BUILD_ABOVE = 40




class Theme:
    """One themed section: what its ground is made of and what happens on it.

    ``features`` is the multiplier table on the shared feature vocabulary. A
    theme is a change of *emphasis* rather than a different game -- every
    feature stays available to every theme -- except where a feature names a
    material only one theme has, and those carry a weight of zero everywhere
    else.
    """

    __slots__ = (
        "accent",
        "candy",
        "dark",
        "exits",
        "step",
        "features",
        "glow",
        "ground",
        "liquid",
        "name",
        "props",
        "rock",
        "sky",
        "sub",
    )

    def __init__(self, name: str, ground: str, sub: str, rock: str,
                 accent: str, liquid: str | None, glow: str,
                 props: tuple[str, ...], features: dict[str, float],
                 sky: tuple[int, int, int], dark: float = 0.0,
                 candy: tuple[str, ...] = (),
                 exits: tuple[str, ...] = ("stair",),
                 step: tuple[str, str] | None = None) -> None:
        self.name = name
        #: The top cell of the terrace floor: what you are standing on.
        self.ground = ground
        #: The two cells under it, seen in the cut face at the rim.
        self.sub = sub
        #: What this theme's own built parkour -- humps, pillars, steps -- is
        #: made of. Usually a harder version of its ground.
        self.rock = rock
        self.accent = accent
        #: What pools on it, if anything. Water, lava, or nothing.
        self.liquid = liquid
        self.glow = glow
        #: Sub-block furniture, drawn as models by the scene.
        self.props = props
        self.features = features
        self.sky = sky
        #: 0 for a section lit by the sky, 1 for one lit only by its own lamps.
        self.dark = dark
        #: Materials this theme's *floating* jump blocks use, where it has any.
        self.candy = candy or (accent, rock)
        #: How a body may get out of this level. Every theme can be left by a
        #: staircase; a place with something better to climb says so.
        self.exits = exits
        #: ``(material, move)`` for the treads of this level's exit staircase,
        #: where the place has something to say about them. The climb is over
        #: forty per cent of every run, so a staircase that is the same stone
        #: and the same hop in all fifteen places is the single largest source
        #: of sameness in the format.
        self.step = step


THEMES = (
    Theme("plains", "grass", "dirt", "cobble", "oak", "water", "lantern",
          ("grasstuft", "flower", "mcfence", "sugarcane"),
          {"pond": 2.4, "fencehop": 2.0, "treestump": 1.8,
           "slimebounce": 1.6},
          (150, 200, 240),
          exits=("stair", "ladder")),
    Theme("farm", "farmland", "dirt", "hay", "oak", "water", "lantern",
          ("crop", "mcfence", "sugarcane", "grasstuft"),
          {"haystack": 3.0, "channel": 2.4, "fencehop": 2.2, "croprow": 2.0},
          (176, 202, 226),
          exits=("stair", "ladder"),
          step=("hay", "hop")),
    Theme("desert", "sand", "sandstone", "sandstone", "terracotta", "water",
          "lantern", ("deadbush", "cactus", "mcfence"),
          {"dune": 3.0, "pond": 2.0, "cactusrun": 2.4, "headhitter": 1.6},
          (240, 216, 168),
          exits=("stair",),
          step=("sandstone", "hop")),
    Theme("mesa", "redsand", "terra_orange", "terra_red", "terra_white", None,
          "lantern", ("deadbush", "pebbles"),
          {"spire": 3.0, "dune": 1.8, "slabline": 1.8, "corner": 1.6},
          (232, 168, 112),
          exits=("stair", "ladder"),
          step=("terra_white", "hop")),
    Theme("jungle", "moss", "podzol", "junglelog", "jungleleaf", "water",
          "lantern", ("bamboo", "grasstuft", "vinehang", "flower"),
          {"vineclimb": 3.2, "canopy": 2.4, "logstep": 2.0, "pond": 1.4},
          (128, 190, 132),
          exits=("vine", "stair"),
          step=("junglelog", "hop")),
    Theme("mushroom", "mycelium", "dirt", "mushroomstem", "mushroomred", None,
          "shroomlight", ("mushroomcap", "grasstuft", "flower"),
          {"capstep": 3.4, "slimebounce": 2.0, "slabline": 1.6,
           "vineclimb": 1.4},
          (196, 176, 208),
          exits=("vine", "stair"),
          step=("mushroomstem", "hop")),
    Theme("village", "gravel", "coarse", "plaster", "brick", "water", "torch",
          ("mcfence", "lanternpost", "grasstuft", "torch"),
          {"rooftop": 3.2, "doorway": 2.4, "fencehop": 1.8, "corner": 1.8},
          (188, 196, 208),
          exits=("ladder", "stair"),
          step=("plaster", "hop")),
    Theme("mine", "gravel", "deepslate", "deepslate", "goldore", None, "torch",
          ("rail", "torch", "pebbles"),
          {"railrun": 3.0, "ladderrun": 2.6, "webwalk": 2.2, "headhitter": 2.0},
          (86, 84, 96), 0.74,
          exits=("ladder", "stair"),
          step=("oak", "hop")),
    Theme("deepdark", "sculk", "deepslate", "deepslate", "sculkvein", None,
          "amethyst", ("pebbles", "torch"),
          {"voidgap": 2.6, "slabline": 2.0, "corner": 2.0, "webwalk": 1.6},
          (34, 44, 56), 0.86,
          exits=("ladder", "stair"),
          step=("deepslate", "hop")),
    Theme("dripstone", "dripstone", "tuff", "dripstone", "calcite", "water",
          "lantern", ("dripstone", "pebbles", "chain"),
          {"spire": 2.6, "pond": 1.8, "headhitter": 2.2, "bubblelift": 2.0},
          (108, 100, 96), 0.55,
          exits=("bubble", "stair")),
    Theme("ice", "snow", "packedice", "packedice", "blueice", "water",
          "lantern", ("pebbles",),
          {"iceline": 3.4, "slabline": 1.8, "voidgap": 1.8, "hump": 1.4},
          (206, 226, 248),
          exits=("stair",),
          step=("packedice", "slide")),
    Theme("nether", "netherrack", "netherbrick", "netherbrick", "magma",
          "lava", "magma", ("netherfungus", "deadbush"),
          {"lavaleap": 3.2, "soulwalk": 2.4, "headhitter": 2.0, "spire": 1.6},
          (176, 66, 48), 0.6,
          exits=("stair", "ladder"),
          step=("soulsand", "hop")),
    Theme("warped", "warpednylium", "warped", "warped", "shroomlight", "lava",
          "shroomlight", ("netherfungus", "grasstuft"),
          {"capstep": 2.4, "lavaleap": 2.0, "vineclimb": 2.0, "soulwalk": 1.8,
           "bubblelift": 1.6},
          (36, 128, 130), 0.5,
          exits=("vine", "bubble", "stair"),
          step=("warped", "hop")),
    Theme("end", "endstone", "endstone", "purpur", "obsidian", None, "lantern",
          ("chorus", "endrod"),
          {"endpillar": 3.2, "voidgap": 2.6, "rodline": 2.4, "corner": 1.8},
          (46, 38, 66), 0.62,
          exits=("bubble", "stair"),
          step=("purpur", "hop")),
    Theme("rainbow", "wool_cyan", "quartz", "quartz", "wool_pink", None,
          "glowstone", (),
          {"woolcheck": 4.0, "slimebounce": 2.6, "slabline": 2.0,
           "voidgap": 1.6},
          (240, 220, 250), 0.0, WOOLS,
          exits=("stair",)),
    # -- places the designed tower asked for. In the generated rotation they
    # are simply eight more themes in the bag; in the hand-built tower each
    # is the base skin of one or two named levels.
    Theme("honey", "hay", "honeycomb", "honeycomb", "honey", None,
          "shroomlight", ("mcfence", "grasstuft", "flower"),
          {"slimebounce": 2.8, "haystack": 2.0, "headhitter": 1.8},
          (232, 196, 128),
          exits=("stair", "ladder"),
          step=("honeycomb", "hop")),
    Theme("coral", "sand", "coral_pink", "coral_red", "coral_blue", "water",
          "sealantern", ("flower", "pebbles", "grasstuft"),
          {"pond": 2.6, "channel": 2.2, "pillars": 1.8, "spire": 1.6},
          (140, 208, 216),
          exits=("stair",),
          step=("coral_red", "hop")),
    Theme("gold", "tuff", "deepslate", "rawgold", "gold", "lava",
          "glowstone", ("pebbles", "torch", "chain"),
          {"headhitter": 2.2, "lavaleap": 2.0, "corner": 1.8},
          (150, 118, 62), 0.72,
          exits=("stair", "ladder"),
          step=("rawgold", "hop")),
    Theme("library", "spruce", "oak", "bookshelf", "oak", None, "lantern",
          ("torch", "lanternpost"),
          {"doorway": 2.6, "slabline": 2.2, "corner": 1.8, "headhitter": 1.6},
          (172, 148, 112), 0.58,
          exits=("ladder", "stair"),
          step=("oak", "hop")),
    Theme("prismarine", "prismarine", "darkprismarine", "prismarine",
          "sealantern", "water", "sealantern", ("pebbles",),
          {"pond": 2.4, "channel": 2.2, "doorway": 2.0, "slabline": 1.6},
          (86, 148, 158), 0.5,
          exits=("stair", "bubble"),
          step=("darkprismarine", "hop")),
    Theme("snow", "snow", "packedice", "frost", "spruce", None, "lantern",
          ("pebbles", "mcfence", "lanternpost"),
          {"iceline": 2.4, "slabline": 2.0, "hump": 1.8, "voidgap": 1.6},
          (222, 230, 242),
          exits=("stair",),
          step=("frost", "hop")),
    Theme("crimson", "crimsonnylium", "netherrack", "crimson", "wartblock",
          "lava", "shroomlight", ("netherfungus", "vinehang"),
          {"capstep": 2.4, "lavaleap": 2.0, "vineclimb": 2.0, "spire": 1.6},
          (150, 58, 56), 0.55,
          exits=("ladder", "vine", "stair"),
          step=("crimson", "hop")),
    Theme("quartz", "quartz", "diorite", "quartz", "gold", None, "lantern",
          ("lanternpost", "pebbles"),
          {"slabline": 2.4, "corner": 2.0, "pillars": 1.8, "doorway": 1.6},
          (228, 232, 244),
          exits=("stair",),
          step=("diorite", "hop")),
)
THEME_BY_NAME = {t.name: t for t in THEMES}
#: ``ladder`` and ``vine`` are here rather than in a theme's prop list because
#: they belong to a *move*, not to a place: any level may be left by climbing.
PROP_KINDS = tuple(sorted({k for t in THEMES for k in t.props}
                          | {"lilypad", "ladder", "vine"}))
MATERIALS.setdefault("mycelium", ((150, 132, 146), "dirt", 0.04))


def _lm_box(cells, t0, t1, y0, y1, r0, r1, style) -> None:
    for dt in range(t0, t1 + 1):
        for dy in range(y0, y1 + 1):
            for dr in range(r0, r1 + 1):
                cells.append((dt, dy, dr, style))


def _lm_windmill(rng, theme):
    cells: list = []
    _lm_box(cells, -1, 1, 0, 2, -1, 1, "plaster")
    _lm_box(cells, 0, 1, 3, 5, 0, 1, "plaster")
    _lm_box(cells, -1, 2, 6, 6, -1, 2, "roof")
    cells.append((0, 1, -2, theme.glow))
    return cells


def _lm_watchtower(rng, theme):
    cells: list = []
    _lm_box(cells, 0, 1, 0, 4, 0, 1, theme.rock)
    _lm_box(cells, -1, 2, 5, 5, -1, 2, theme.accent)
    for dt, dr in ((-1, -1), (2, -1), (-1, 2), (2, 2)):
        cells.append((dt, 6, dr, theme.rock))
    cells.append((0, 6, 0, theme.glow))
    return cells


def _lm_tree(rng, theme):
    cells: list = []
    trunk = "junglelog" if theme.name in ("jungle", "CANOPY WALK") else "log"
    leaf = "jungleleaf" if trunk == "junglelog" else "leaves"
    _lm_box(cells, 0, 0, 0, 4, 0, 0, trunk)
    _lm_box(cells, -1, 1, 4, 5, -1, 1, leaf)
    cells.append((0, 6, 0, leaf))
    return cells


def _lm_bell(rng, theme):
    cells: list = []
    _lm_box(cells, -1, -1, 0, 3, 0, 0, theme.rock)
    _lm_box(cells, 1, 1, 0, 3, 0, 0, theme.rock)
    _lm_box(cells, -1, 1, 4, 4, 0, 0, "oak")
    cells.append((0, 3, 0, "gold"))
    return cells


def _lm_crane(rng, theme):
    cells: list = []
    _lm_box(cells, 0, 0, 0, 5, 0, 0, "spruce")
    _lm_box(cells, 0, 3, 5, 5, 0, 0, "spruce")
    cells.append((3, 4, 0, "spruce"))
    return cells


def _lm_totem(rng, theme):
    cells: list = []
    _lm_box(cells, 0, 0, 0, 4, 0, 0, "obsidian")
    _lm_box(cells, 0, 0, 2, 4, 1, 1, "obsidian")
    cells.append((0, 3, 0, theme.glow))
    return cells


def _lm_comb(rng, theme):
    cells: list = []
    _lm_box(cells, -1, 2, 0, 3, 1, 1, "honeycomb")
    cells.append((0, 1, 1, theme.glow))
    cells.append((1, 2, 1, "honey"))
    return cells


def _lm_greatcap(rng, theme):
    cells: list = []
    _lm_box(cells, 0, 0, 0, 2, 0, 0, "mushroomstem")
    _lm_box(cells, -2, 2, 3, 3, -2, 2, "mushroomred")
    _lm_box(cells, -1, 1, 4, 4, -1, 1, "mushroomred")
    return cells


def _lm_hoard(rng, theme):
    cells: list = []
    _lm_box(cells, 0, 1, 0, 0, 0, 1, "rawgold")
    cells.append((0, 1, 0, "gold"))
    cells.append((1, 1, 1, "rawgold"))
    cells.append((2, 0, 0, "gold"))
    return cells


def _lm_stripes(rng, theme):
    cells: list = []
    for i, dt in enumerate(range(-2, 4)):
        _lm_box(cells, dt, dt, 0, 3, 1, 1, WOOLS[i % len(WOOLS)])
    return cells


def _lm_cabin(rng, theme):
    cells: list = []
    _lm_box(cells, -1, 1, 0, 1, -1, 1, "spruce")
    _lm_box(cells, -1, 1, 2, 2, -1, 1, "roof")
    cells.append((0, 0, -2, theme.glow))
    return cells


def _lm_hoodoo(rng, theme):
    cells: list = []
    h1, h2 = rng.randint(3, 4), rng.randint(5, 6)
    _lm_box(cells, 0, 0, 0, h1, 0, 0, "terra_red")
    cells.append((0, h1 + 1, 0, "terra_white"))
    _lm_box(cells, 2, 2, 0, h2, 1, 1, "terra_orange")
    cells.append((2, h2 + 1, 1, "terra_white"))
    return cells


def _lm_arch(rng, theme):
    cells: list = []
    _lm_box(cells, -2, -2, 0, 3, 0, 0, theme.rock)
    _lm_box(cells, 2, 2, 0, 3, 0, 0, theme.rock)
    _lm_box(cells, -2, 2, 4, 4, 0, 0, theme.accent)
    return cells


def _lm_cluster(rng, theme):
    cells: list = []
    _lm_box(cells, 0, 0, 0, 1, 0, 0, "amethyst")
    cells.append((1, 0, 0, "amethyst"))
    cells.append((0, 2, 0, "amethyst"))
    cells.append((-1, 0, 1, "amethyst"))
    return cells


#: The signature structure a level is recognised by, by name. Built in the
#: trough's own frame and painted by :meth:`Course._landmark` -- off the
#: course, on real ground, or not at all.
LANDMARKS = {
    "windmill": _lm_windmill,
    "watchtower": _lm_watchtower,
    "tree": _lm_tree,
    "bell": _lm_bell,
    "crane": _lm_crane,
    "totem": _lm_totem,
    "comb": _lm_comb,
    "greatcap": _lm_greatcap,
    "hoard": _lm_hoard,
    "stripes": _lm_stripes,
    "cabin": _lm_cabin,
    "hoodoo": _lm_hoodoo,
    "arch": _lm_arch,
    "cluster": _lm_cluster,
}


class Section:
    """One **level**: a flat themed terrace, and the chasm at the end of it.

    ``u0``/``u1`` are *unwrapped* angles -- they keep increasing for the whole
    run, so a level is a half-open interval on a line rather than an arc that
    has to be compared modulo anything. Every level is exactly ``LEVEL_ARC``
    wide, which is what makes "the level one turn above this one" the plain
    index arithmetic ``index + LEVELS_PER_TURN``.

    ``y`` is flat across the whole level. ``rise`` is how much higher it is
    than the level before it, and ``gap`` is how much of its far end has no
    floor. Those two are the whole reason the parkour is not optional.
    """

    __slots__ = ("band", "breaks", "gap", "hard", "index", "landmark",
                 "profile", "rise", "shelf", "signature", "theme", "u0",
                 "u1", "y")

    def __init__(self, index: int, theme: Theme, u0: float, u1: float,
                 y: int, rise: int, gap: float, hard: float = 1.0,
                 signature: str = "", profile: str = "plaza",
                 shelf: float = 4.0, landmark: str = "",
                 band: float = BAND) -> None:
        self.index = index
        self.theme = theme
        self.u0 = u0
        self.u1 = u1
        #: The height a body's feet stand at, anywhere on this level.
        self.y = y
        self.rise = rise
        #: Radians at the far end of the level with no floor slab in them.
        self.gap = gap
        #: How hard *this level* is, 0 to 1, and the unit the whole ramp is
        #: expressed in.
        #:
        #: A single ramp over the first seventy landings makes every run the
        #: same shape and every level after the seventieth landing the same
        #: level. A level is the natural unit instead: it is a themed terrace
        #: with a beginning and an end, it is six to ten seconds of strip, and
        #: the eye reads it as one place. Drawn from a distribution that
        #: *widens* with altitude rather than one that slides upward, so the
        #: bottom of the tower is uniformly mild and the top is where a level
        #: might be anything -- which is the difference between a course that
        #: gets harder and one that gets more varied. Tower of Hell does the
        #: same thing and for the same reason: the ramp lives in what the pool
        #: is made of, not in a hand-placed sequence.
        self.hard = hard
        #: The one feature this level is *about*, weighted well above the rest
        #: of its theme's pool. Every reference map has a verb per section and
        #: this format's themes only half did: a jungle that occasionally has a
        #: vine in it is not a jungle level.
        self.signature = signature
        #: What the terrace's *ground* is. ``plaza`` is the full band, and is
        #: what every generated level is; ``ledge`` keeps ground only for
        #: ``shelf`` cells out from the core, with the drop genuinely outboard
        #: -- the reference's course is a shelf on a cliff, not a floor with
        #: toys on it, and this is that shape; ``channel`` is the full band
        #: with the theme's liquid cut along the middle of it. The hand-built
        #: levels choose; dice never do.
        self.profile = profile
        self.shelf = shelf
        #: The one structure this level is recognised by, or "". A place you
        #: remember needs one thing to remember it by, and no amount of good
        #: parkour is that thing. Painted during dressing, off the course.
        self.landmark = landmark
        #: How wide this level's corridor is, core face to rim. The global
        #: constant is only the default: the real map's levels visibly vary
        #: between tight galleries and broad courts, and one width for all
        #: thirty-three places was the last global left in the geometry.
        self.band = band
        #: How many breaks the level's own floor has: short mini-chasms cut
        #: *inside* the level, so the ground is islands rather than a ribbon.
        #: The owner's complaint, verbatim: you could run ninety per cent of
        #: a level in a straight line and only jump if you felt like it. The
        #: end chasm makes levels unwalkable *between*; the breaks make them
        #: unwalkable *along*. Zero for generated levels (their contract is
        #: unchanged); the hand-built ones choose.
        self.breaks = 0

    @property
    def u_edge(self) -> float:
        """Where the ground stops and the chasm begins."""
        return self.u1 - self.gap


class Cone:
    """The building: a fluted inverted cone with a helical trough cut round it.

    Answers three questions and owns no memory of having answered them:

    * :meth:`rock` -- is this cell inside the tower?
    * :meth:`floor_of` -- what height is the trough's floor at this bearing?
    * :meth:`section_at` -- which theme is this stretch of trough?

    Drawing is separate (:meth:`emit`), because what is *drawn* is only the
    skin: a solid cone's interior is never seen, and building it would be a
    hundred thousand cells nobody looks at.
    """

    #: How wide the tower is at its base and how fast it flares, as class
    #: attributes rather than module constants so that a *differently sized*
    #: tower is a subclass rather than a fork. The hand-built tower is wider,
    #: because a terrace has to be long enough to hold a designed level and the
    #: only thing that lengthens one is a bigger circle.
    base_r = BASE_R
    flare = FLARE

    def __init__(self, rng, base_y: int = 0) -> None:
        self.rng = rng
        self.base = base_y
        #: Which way round the helix climbs. Both handednesses look right and
        #: a run that always turns the same way is a run you recognise.
        self.wind = 1 if rng.random() < 0.5 else -1
        self.sections: list[Section] = []
        self._bag: list[Theme] = []
        #: Where the themed sections begin. A revolution and a half below the
        #: base, because the world is drawn ``BUILD_BELOW`` under the body from
        #: the very first frame and an unthemed stretch of it is visible.
        self._u_lo = -3.0 * math.pi
        #: Phases for the rim wobble. Analytic, so the rim is jagged in a way
        #: that costs no memory and cannot disagree with itself between the
        #: collision test and the drawing.
        self._w1 = rng.uniform(0, 6.283)
        self._w2 = rng.uniform(0, 6.283)
        self._w3 = rng.uniform(0, 6.283)
        self.built_to = base_y
        self.built_from = base_y
        #: Per-level cache of :meth:`floor_breaks`, which ``rock`` asks for.
        self._breaks_cache: dict[int, tuple] = {}
        #: ``(cell, kind, yaw)`` for sub-block furniture, drawn as models.
        self.props: list[tuple[tuple[int, int, int], str, float]] = []
        #: Cells the renderer should hang a glow on. A dark section lit only by
        #: its own lamps is most of what makes it read as a different place
        #: from the one below it.
        self.lamps: list[tuple[int, int, int]] = []
        self._extend_section()

    # -- the helix ---------------------------------------------------------

    def level_index(self, u: float) -> int:
        """Which level covers this unwrapped angle. Every level is the same
        angular width, which is what keeps this arithmetic rather than a
        search."""
        return max(0, ifloor((u - self._u_lo) / LEVEL_ARC))

    def level(self, index: int) -> Section:
        """The level at ``index``, generated on demand."""
        while len(self.sections) <= index:
            self._extend_section()
        return self.sections[index]

    def unwrap(self, x: float, z: float, y: float) -> float:
        """The unwrapped angle of the level at or below ``y`` under ``(x, z)``.

        This is the one piece of arithmetic the whole shape rests on. A bearing
        on its own is ambiguous -- the trough passes over every bearing once a
        revolution -- so it is resolved against a height, by asking which turn
        is the last one at or below it.

        The levels at one bearing are ``j``, ``j + LEVELS_PER_TURN``,
        ``j + 2 * LEVELS_PER_TURN`` and so on, and their floors strictly
        increase, so the answer is the last of those whose floor is at or below
        ``y``. It used to be a division, back when every turn rose by the same
        fixed amount; it cannot be one now that they do not, and this walk is
        why :attr:`Course._rock` memoises.
        """
        theta = math.atan2(z, x) * self.wind
        j = self.level_index(theta)
        n = LEVELS_PER_TURN
        # Start from where a constant-rate tower would have put it, then walk.
        # The estimate is never more than a turn or two out, because the rises
        # only vary between four and seven.
        k = max(0, ifloor((y - self.base) / TURN_MAX))
        i = j + k * n
        while self.level(i + n).y <= y:
            i += n
        while i >= n and self.level(i).y > y:
            i -= n
        return theta + 2 * math.pi * ((i - j) // n)

    def floor_at(self, u: float) -> int:
        """The ``y`` a body's feet stand at, at unwrapped angle ``u``.

        Flat across a whole level, and a whole number. Both matter. Everything
        in this project that reasons about standing on a block depends on a
        surface being an integer; and a floor that is *flat* rather than
        stepping is what makes the boundary between two levels a wall you have
        to climb rather than a stair you walk up without noticing.
        """
        return self.level(self.level_index(u)).y

    def trough_height(self, u: float) -> int:
        """How much open air there is over this level, floor to soffit.

        Varies from turn to turn now that the rises do -- which is exactly the
        point -- so anything that wants to hang something from the ceiling, or
        to know how tall a feature may stand, has to ask rather than assume.
        """
        i = self.level_index(u)
        return (self.level(i + LEVELS_PER_TURN).y - self.level(i).y) - FLOOR_T

    def has_floor(self, u: float) -> bool:
        """Is there any ground at this bearing, or is this a hole?

        Two kinds of hole and they earn their keep differently. The end
        chasm makes levels unwalkable *between* -- that was the original
        walkability rebuild. The breaks make a level unwalkable *along*:
        short mini-chasms cut inside the level so its ground is islands
        rather than a ribbon. Measured on the real map with the same walker
        we hold ourselves to: not one of its 43 checkpoint legs can be
        walked end to end, and the mean distance covered without a jump is
        46%. A course whose ground carries you nine tenths of the way is a
        course the parkour is optional on, which was the owner's complaint
        in both towers.
        """
        lv = self.level(self.level_index(u))
        if u >= lv.u_edge:
            return False
        for b0, b1 in self.floor_breaks(lv):
            if b0 <= u < b1:
                return False
        return True

    def floor_breaks(self, lv: Section) -> tuple:
        """The level's own floor gaps, in unwrapped angle. Deterministic off
        the level index, kept off the entry stretch, the exit reserve and
        the landmark's apron, and sized so an ordinary hop crosses them.
        Cached: this sits inside ``has_floor``, which sits inside ``rock``,
        the hottest predicate in the module."""
        n = lv.breaks
        if not n:
            return ()
        cached = self._breaks_cache.get(lv.index)
        if cached is not None:
            return cached
        radius = max(6.0, self.rim_at(lv.y))
        span = lv.u1 - lv.u0
        au = self.apron_u(lv)
        out = []
        for k in range(n):
            h = (math.sin((lv.index * 7 + k * 3 + 1) * 12.9898)
                 * 43758.5453) % 1.0
            # Spread across the first two thirds of the level: entry landing
            # zone ends at 0.14, the exit reserve begins past ~0.66.
            f = 0.14 + (k + h) * (0.52 / n)
            c = lv.u0 + span * f
            if abs(c - au) * radius < 5.5:
                continue                # never under the landmark's apron
            w = (2.2 + 1.0 * ((h * 7.13) % 1.0)) / radius
            out.append((c - w / 2, c + w / 2))
        got = tuple(out)
        self._breaks_cache[lv.index] = got
        return got

    def rim_at(self, y: float) -> float:
        """The cone's outer radius at a height. The flare, and nothing else."""
        return self.base_r + self.flare * (y - self.base)

    def wobble(self, u: float) -> float:
        """How far the rim strays from the perfect circle at ``u``.

        A perfectly circular rim reads as a machined part. Two sines and a
        third of a cell of ripple is enough to make the outer edge look bitten
        into, and being a closed form it can never disagree with itself between
        the collision test and the mesh.
        """
        return (0.9 * math.sin(u * 0.9 + self._w1)
                + 0.6 * math.sin(u * 2.3 + self._w2)
                + 0.3 * math.sin(u * 5.1 + self._w3))

    def outer_at(self, u: float) -> float:
        """The trough's outer edge: the last radius with ground under it."""
        return self.rim_at(self.floor_at(u)) + self.wobble(u)

    def band_at(self, u: float) -> float:
        """This bearing's corridor width: the level's own, not a constant."""
        return self.level(self.level_index(u)).band

    def inner_at(self, u: float) -> float:
        """The trough's inner edge: the foot of the flank above."""
        return self.outer_at(u) - self.band_at(u)

    def floor_range(self, u: float, apron: bool = True) -> tuple[float, float]:
        """The radial extent of the ground at this bearing.

        The full band for a ``plaza`` level -- every generated level, and the
        designed streets and halls that dress a wide floor as a place. A
        ``ledge`` level keeps only a shelf against the core, wobbled a little
        so the edge reads as broken ground rather than a sawn plank, and
        everything outboard of it is the drop. The shelf never narrows under
        three cells: the exit stair hugs the core at 2.4 and has to have
        ground under its piers.
        """
        out = self.outer_at(u)
        lv = self.level(self.level_index(u))
        if lv.profile == "ledge":
            w = max(3.0, min(lv.band - 2.0,
                             lv.shelf + 0.9 * math.sin(u * 1.7 + self._w2)
                             + 0.4 * math.sin(u * 4.3 + self._w3)))
            # The apron: one stretch of every ledge swells out to hold the
            # level's landmark. A shelf four cells wide has no room for a
            # windmill beside the course, and a constant-width ribbon reads
            # as machined anyway. Closed form off the level's own index, so
            # collision, mesh and the landmark painter all agree on where.
            if apron:
                # ``apron=False`` is the course's view: the pull toward the
                # shelf edge must not follow the bulge, or the course parks
                # itself exactly where the landmark was meant to stand.
                au = self.apron_u(lv)
                d = abs(u - au) * max(6.0, self.rim_at(lv.y))
                if d < 5.0:
                    w += 4.5 * (1.0 - d / 5.0)
            return out - lv.band, out - lv.band + w
        return out - lv.band, out

    def apron_u(self, lv: Section) -> float:
        """Where this level's ledge swells, in unwrapped angle."""
        f = 0.3 + 0.4 * ((math.sin(lv.index * 12.9898) * 43758.5453) % 1.0)
        return lv.u0 + (lv.u1 - lv.u0) * f

    def on_floor(self, u: float, r: float) -> bool:
        """Is this radius over ground, at a bearing that has any?"""
        r0, r1 = self.floor_range(u)
        return r <= r1 + 1e-9

    def channel_range(self, u: float) -> tuple[float, float] | None:
        """The radial extent of the liquid cut along a ``channel`` level, or
        ``None``. Two cells wide, mid-band, wandering just enough that the
        stepping stones across it are never twice the same jump."""
        lv = self.level(self.level_index(u))
        if lv.profile != "channel":
            return None
        out = self.outer_at(u)
        mid = out - lv.band + 3.6 + 1.1 * math.sin(u * 1.3 + self._w1)
        return mid, mid + 2.2

    def core_r(self, u: float, y: int) -> float:
        """The core wall's radius at a height -- the cliff at your back.

        Not a cylinder any more. Two or three cells under the soffit the wall
        leans *out* over the course -- the reference's cliff overhangs and the
        smooth flute was the single most procedural-looking thing left -- and
        above head height it carries a knuckle of roughness. Both are closed
        forms keyed on the bearing and the height, so collision and mesh can
        never disagree; and the roughness starts three cells off the floor so
        the walker can never use it as a stair (one knob at +3 with nothing at
        +1 is unreachable, and the walkability probe holds that at zero).
        """
        lv = self.level(self.level_index(u))
        inner = self.outer_at(u) - lv.band
        if not self.has_floor(u + 2 * math.pi):
            # No ceiling overhead means a bulge would have open air above its
            # top cell -- a standable shelf on the cliff face, which is
            # exactly the thing the walkability probe exists to refuse.
            return inner
        soffit = self.level(lv.index + LEVELS_PER_TURN).y - FLOOR_T
        h = y - lv.y
        span = max(1.0, soffit - lv.y - 2.0)
        # Monotone in height, by construction and not by tuning: the wall
        # only ever leans *further out* as it rises, so no cell of the face
        # ever has free air above it and nothing can stand on the cliff. The
        # first walkability regression this project had came from a knuckle
        # of rock noise here whose bumps made one-block stairs at the level
        # seams; a profile that cannot un-lean cannot make a stair.
        t = min(1.0, max(0.0, (h - 2.0) / span)) ** 1.3
        # Capped at just over one block. At 1.5 the lean reached far enough
        # that a body riding a ladder at the wall grazed the face with its
        # shoulders near the top of the climb -- measured at 0.14% of frames,
        # every one of them on an ascent, and from inside the lens it reads
        # as phasing through the tower.
        ridge = (0.25 + 0.5 * (0.5 + 0.5 * math.sin(u * 2.1 + self._w3))
                 + 0.35 * (0.5 + 0.5 * math.sin(u * 7.7 + self._w1)))
        return inner + ridge * t

    def tooth(self, u: float) -> bool:
        """Does the ceiling slab hang a tooth at this bearing? The soffit's
        underside is dead flat otherwise, and a flat plate overhead is the
        other half of what read as procedural."""
        return (math.sin(u * 6.3 + self._w2)
                + 0.6 * math.sin(u * 15.7 + self._w1)) > 1.05

    def rib_out(self, x: float, z: float) -> float:
        """How far the flute stands proud at this bearing. Either 0 or 1.

        Taken from the bearing alone rather than from arc length, so the ribs
        stay strictly vertical all the way up a cone whose circumference is
        growing. Arc-length ribs drift and read as a barber's pole.
        """
        theta = math.atan2(z, x)
        return float(int((theta / (2 * math.pi) + 0.5) * RIBS) % 2) * RIB_D

    # -- the solid test ----------------------------------------------------

    def rock(self, cell) -> bool:
        """Is this cell inside the tower? Closed form, no memory, always true
        of the same cell whenever it is asked.

        There are exactly two rules, and it is worth saying why there are not
        more. :meth:`unwrap` answers with the turn *at or below* the cell, so
        ``y`` is never less than that turn's floor -- a first draft of this
        method had three branches and the two that dealt with heights below the
        floor were unreachable, which produced a smooth cylinder with the themes
        painted on it as stripes and nothing to run along at all. Every height
        belongs to some level's trough, and within one trough a cell is either
        the core behind you or the floor slab of the level a turn above, which
        is your ceiling.

        The third thing it has to know is where the floor **is not**. Every
        level ends in a chasm with nothing in it, and that hole is what makes
        the parkour load-bearing rather than decorative.
        """
        x, y, z = cell
        r = math.hypot(x, z)
        # Cheap rejection first: nothing this far out is ever rock, and this is
        # the hottest predicate in the module by a distance.
        if r > self.base_r + self.flare * (y - self.base) + 6.0:
            return False
        u = self.unwrap(x, z, y)
        i = self.level_index(u)
        above = self.level(i + LEVELS_PER_TURN)
        if y >= above.y - FLOOR_T:
            # The floor slab of the level one turn above: the full width of the
            # band, cantilevered off the core with nothing under it. That
            # overhang is the reference's stepped underside and the trough's
            # ceiling at the same time -- and it is also the *ground* of that
            # level, so its chasm is a hole in both at once.
            up = u + 2 * math.pi
            if not self.has_floor(up):
                return False
            if r > self.floor_range(up)[1]:
                return False            # outboard of a ledge level's shelf
            ch = self.channel_range(up)
            if ch and ch[0] <= r <= ch[1] and y >= above.y - 2:
                return False            # the cut the channel's liquid sits in
            return True
        if y == above.y - FLOOR_T - 1 and self.tooth(u):
            # A tooth hanging off the soffit, out near the slab's edge.
            up = u + 2 * math.pi
            if self.has_floor(up):
                r1f = self.floor_range(up)[1]
                if r1f - 1.6 <= r <= r1f:
                    return True
        return r <= self.core_r(u, y)           # the core, behind your back

    def surface_y(self, x: float, z: float, y_hint: float) -> int:
        """The ``y`` a body standing at this bearing has its feet at."""
        return self.floor_at(self.unwrap(x, z, y_hint))

    # -- themed sections ---------------------------------------------------

    def _next_theme(self) -> Theme:
        if not self._bag:
            self._bag = list(THEMES)
            self.rng.shuffle(self._bag)
            if self.sections and self._bag[0] is self.sections[-1].theme \
                    and len(self._bag) > 1:
                self._bag[0], self._bag[1] = self._bag[1], self._bag[0]
        return self._bag.pop(0)

    def section_at(self, u: float) -> Section:
        """The level covering unwrapped angle ``u``, generated on demand.

        Levels begin a revolution and a half *below* where a run starts, so
        that the world drawn under the body's feet on the first frame is
        already themed and already has floors in it.
        """
        return self.level(self.level_index(u))

    def _extend_section(self) -> None:
        i = len(self.sections)
        u0 = self._u_lo + i * LEVEL_ARC
        if i == 0:
            y, rise = self.base, 0
        else:
            prev = self.sections[-1]
            rise = self.rng.randint(*LEVEL_RISE)
            y = prev.y + rise
        # The chasm is measured in blocks of arc and converted here, because a
        # fixed *angle* would be six blocks wide at the bottom of the tower and
        # ten at the top -- and how far a body can jump does not care how wide
        # the tower is.
        radius = max(6.0, self.rim_at(y))
        gap = self.rng.uniform(*GAP_ARC) / radius
        theme = self._next_theme()
        # How much of the range this level's difficulty may be drawn from. It
        # is the *top* end that opens up with altitude, never the bottom: a run
        # that simply got harder would spend its second half at one pitch, and
        # what makes a course read as varied is that a mild level can still
        # turn up late.
        reach = min(1.0, max(0, i - START_LEVEL) / HARD_SPAN)
        top = HARD_FLOOR + (HARD_TOP - HARD_FLOOR) * (0.45 + 0.55 * reach)
        # Skewed toward the top of whatever range is open, because the draw has
        # to keep the *average* pitch up while widening the spread: a plain
        # uniform between a floor and a rising ceiling makes the course easier
        # on the whole than the flat ramp it replaces, which is the opposite of
        # what was asked for.
        hard = HARD_FLOOR + (top - HARD_FLOOR) * self.rng.random() ** 0.38
        # Preferring a verb that is not a jump, where the theme owns one. The
        # course is over nine tenths plain hop and the exit climb -- half of
        # every run -- can only ever be hops, so the one place a level can say
        # something else is its own signature. A theme with nothing but hops to
        # its name still gets one; it just will not change the mix.
        own = [f for f in theme.features if f in THEMED]
        verbs = [f for f in own if f in NON_HOP] or own
        signature = verbs[self.rng.randrange(len(verbs))] if verbs else ""
        self.sections.append(Section(i, theme, u0,
                                     u0 + LEVEL_ARC, y, rise,
                                     min(gap, LEVEL_ARC * 0.45), hard,
                                     signature))

    def theme_at(self, y: float, x: float = 0.0, z: float = 0.0) -> Theme:
        """The theme of the trough under a point. The scene asks this for the
        sky tint and the fog, so it has to answer for the body's own position
        rather than for a height alone -- one revolution holds three or four
        themes and a height alone cannot tell them apart."""
        return self.section_at(self.unwrap(x, z, y)).theme

    # -- drawing -----------------------------------------------------------

    def emit(self, y_lo: int, y_hi: int, place) -> None:
        """Hand every *visible* cell between two heights to ``place``.

        Visible means the skin: the outer few cells of the flank, the outer few
        of the core, and the floor slab, which is the only part of the mass a
        body ever stands on. Iterated by bearing rather than by cell, because
        a disc of radius twenty-five is two thousand cells of which forty are
        wanted.
        """
        for y in range(y_lo, y_hi + 1):
            self.emit_layer(y, place)
        self.built_to = max(self.built_to, y_hi)
        self.built_from = min(self.built_from, y_lo)

    def emit_layer(self, y: int, place) -> None:
        seen: set[tuple[int, int, int]] = set()
        rough = self.rim_at(y)
        steps = max(48, int(2 * math.pi * (rough + 4)) * 2)
        for i in range(steps):
            theta = (i / steps) * 2 * math.pi - math.pi
            ct, st = math.cos(theta), math.sin(theta)
            u = self.unwrap(ct, st, y)
            lv = self.level(self.level_index(u))
            above = self.level(lv.index + LEVELS_PER_TURN)
            h = y - lv.y
            inner = self.outer_at(u) - lv.band
            # The core, at every height: the wall at the back of the trough,
            # fluted, browed and knuckled -- ``core_r`` is the collision
            # radius, so the mesh follows it and the two cannot disagree.
            # Its lowest two cells carry the theme's own subsoil, so the wall
            # reads as a cut bank through the level rather than as bare
            # masonry meeting grass.
            self._ring(ct, st, inner - SKIN, self.core_r(u, y), y,
                       lv.theme.sub if 0 <= h < 2 else "conerib",
                       seen, place, rib=True)
            if y == above.y - FLOOR_T - 1 and self.tooth(u) \
                    and self.has_floor(u + 2 * math.pi):
                r1f = self.floor_range(u + 2 * math.pi)[1]
                self._ring(ct, st, r1f - 1.6, r1f, y, "conesoffit",
                           seen, place)
            if y >= above.y - FLOOR_T and self.has_floor(u + 2 * math.pi):
                self._slab(ct, st, u + 2 * math.pi, y, above.y - 1 - y,
                           seen, place)

    def _slab(self, ct: float, st: float, up: float, y: int, depth: int,
              seen: set, place) -> None:
        """The floor slab of the turn above: this trough's ceiling, and the
        next one's ground.

        ``depth`` counts down from the walking surface. Only the top cell and
        the bottom one are ever *seen* across the whole band -- the top is what
        you stand on, the bottom is the soffit over the trough below -- so
        everything between them is emitted as a rim only. That is what lets the
        slab be nine cells thick, which is what makes the tower a mass rather
        than a stack of plates, for the price of two.
        """
        theme = self.section_at(up).theme
        out = self.floor_range(up)[1]
        upband = self.band_at(up)
        if depth == 0:
            style, r0 = theme.ground, self.outer_at(up) - upband - SKIN
        elif depth == 1:
            # The cut face under the ground: a slice through the place, which
            # is what stops the rim reading as a painted line.
            style, r0 = theme.sub, self.outer_at(up) - upband - SKIN
        elif depth == FLOOR_T - 1:
            style, r0 = "conesoffit", self.outer_at(up) - upband - SKIN
        else:
            style, r0 = "conestone", out - 2.0
        ch = self.channel_range(up) if depth <= 1 else None
        lv = self.level(self.level_index(up))
        if ch or lv.profile == "ledge":
            # A cut profile must be painted with exactly the test collision
            # uses -- paint deciding by the float radius of the march while
            # ``rock`` decides by the cell's own is how a course grows
            # invisible walls and fall-through ledges. Same cell, same answer.
            liquid = theme.liquid or "water"
            edge = out

            def styler(cell):
                r = math.hypot(cell[0], cell[2])
                if r > edge + 1e-9:
                    return None
                if ch and ch[0] <= r <= ch[1]:
                    return liquid if depth == 1 else None
                return style
            self._ring(ct, st, r0, out + 0.6, y, style, seen, place,
                       styler=styler)
            return
        self._ring(ct, st, r0, out, y, style, seen, place)

    def _ring(self, ct: float, st: float, r0: float, r1: float, y: int,
              style: str, seen: set, place, rib: bool = False,
              styler=None) -> None:
        if rib:
            r1 += self.rib_out(ct, st)
        r0 = max(0.0, r0)
        r = r0
        while r <= r1 + 1e-9:
            cell = (iround(ct * r), y, iround(st * r))
            if cell not in seen:
                seen.add(cell)
                got = styler(cell) if styler else style
                if got:
                    place(cell, got)
            r += 0.5
        cell = (iround(ct * r1), y, iround(st * r1))
        if cell not in seen:
            seen.add(cell)
            got = styler(cell) if styler else style
            if got:
                place(cell, got)


# ---------------------------------------------------------------------------
# The course
# ---------------------------------------------------------------------------

#: How far ahead of the body the course is generated, and how far behind it is
#: kept. Both are the flat scene's numbers and for the flat scene's reasons: a
#: dozen-odd landings ahead is what the camera can see, and three behind is
#: what an orb the body has not quite reached yet needs.
AHEAD = 16
TRAIL = 3
#: Blocks laid before a run is at full difficulty.
RAMP_BLOCKS = 70
#: How much wider every gap gets between the start of a run and full
#: difficulty. Applied centrally in :meth:`Course._node` rather than left to
#: each feature's own tables, because most features want a *fixed* shape -- a
#: staircase, a ladder approach -- and would otherwise sit out the ramp
#: entirely. Measured before this existed: mean hop 2.62 m at the start of a
#: run and 2.67 m two hundred landings in, which is a flat line with noise on
#: it, in a scene whose whole pacing story is that it gets harder.
GAP_RAMP = 0.26
#: How far into the band from each edge the course may go. The rim is ragged
#: by construction (:meth:`Cone.wobble`) and the core wall is round, so a
#: landing right against either is a landing whose neighbours are sometimes
#: rock and sometimes sky.
BAND_MARGIN = 2.0
#: Where in the band the course would rather be, as a fraction from the inner
#: edge. Mid-lane: far enough out that the drop is beside you rather than a
#: cliff you are hard against, near enough in that the core wall is in shot.
#: A pull rather than a clamp, so a feature can still send the body right up to
#: either edge and be brought back afterwards.
COURSE_OUT = 0.5
#: How hard. Gentle -- this competes with every feature's own radial intent.
COURSE_PULL = 0.34

#: How a level may be left, and how likely each is where a theme allows it.
#:
#: There is no slime here and there was, briefly. Dropping onto a slime pad and
#: launching out of the level is the most spectacular exit this vocabulary can
#: build, and measured it cost 0.46 points of unchecked placements to buy 0.2%
#: more bounces -- a bounce only works when the fall that fed it was big enough,
#: and an exit is *mandatory*. A mandatory move has to be the most reliable one
#: available rather than the best one. Slime stays where it belongs, as a
#: feature inside a level (``_feat_slimebounce``), which is free to fail.
#:
#: The staircase is weighted well above the vertical climbs, and not for looks.
#: Measured over ten runs: stair-only exits fall through to the unchecked hop on
#: 2.35% of landings, mixed exits on 3.05% -- a ladder needs a free column, an
#: anchor and a launch block hard against the core, and any of the three can be
#: missing. They are worth having as the thing a mine or a jungle does instead;
#: they are not worth being the default.
ASCENTS = {"stair": 2.4, "ladder": 1.0, "vine": 1.0, "bubble": 0.8}
#: The material the climb is hung on, and the move that rides it.
ASCENT_STYLE = {"ladder": ("oak", "climb"), "vine": ("junglelog", "climb"),
                "bubble": ("prismarine", "bubble")}
#: ...and what is drawn in the column itself.
ASCENT_SOFT = {"ladder": "ladder", "vine": "vine", "bubble": "water"}

#: Blocks of arc allowed for each landing of a level's exit climb.
#:
#: The trigger multiplies this by how many landings the climb needs and then
#: adds the chasm, so a six-block rise starts its staircase further back than a
#: four-block one. It has to be the *top* of the range the stair actually
#: asks for, not the middle: reserving the average leaves the last step or two
#: hanging over the hole.
ASCENT_ARC = 3.2

#: Which level a run opens on. Not the first: the world is drawn well below the
#: body from the very first frame, and a run starting at the bottom of the
#: tower has nothing under it to draw.
START_LEVEL = 4

#: Levels over which a level's difficulty may open out to the full range. Nine
#: is three revolutions, which is about as far as a strip that lives for one
#: thinking turn ever gets.
HARD_SPAN = 9.0
#: The mildest a level may be. Not zero: an easy level is a *breather*, not an
#: empty terrace, and the gap tables it draws from still have to be jumped.
HARD_FLOOR = 0.30
#: ...and the hardest. Over one, because the pitch a level is drawn at has to
#: keep its *average* where the flat ramp had it while spreading either side of
#: it, and one was the flat ramp's ceiling. Everything downstream either
#: saturates on it (a probability) or scales gently (the gap ramp).
HARD_TOP = 1.15
#: How far above the rest of its theme's pool a level's signature verb sits.
SIGNATURE_WEIGHT = 2.0

#: Blocks of arc of head start the exit climb is given on top of what it needs.
#:
#: Small, because it no longer has to absorb a whole feature: ``_plan_feature``
#: truncates whatever it picks to the room actually left. It was nine while it
#: did, and the exit climb was then reserving over half of every level -- so a
#: run was mostly climbing out of places rather than being in them.
FEATURE_SLACK = 4.0

#: The tallest a feature may stand above the terrace's own ground. Six, because
#: the trough is seven to thirteen blocks of open air (it varies now that the
#: level rises do -- ask :meth:`Cone.trough_height`) and a body needs two over
#: its
#: head -- and because a landing higher than this has the next section's floor
#: slab for a ceiling before it has anywhere to jump to.
LIFT_MAX = 6

#: Kinds whose rise is bounded by one jump impulse. Everything else in the
#: vocabulary exists precisely because it is not.
BALLISTIC = frozenset(("hop", "slide", "walk"))

#: Ground materials a body moves across at something other than sprint pace.
SURFACE_SPEED = {
    "soulsand": SOUL_SPEED,
    "packedice": ICE_RUN,
    "blueice": ICE_RUN,
    "web": WEB_SPEED,
}


def _pick(rng, table: dict) -> str:
    """One weighted key. Shared by the feature table and the theme tables."""
    total = sum(table.values())
    roll = rng.random() * total
    upto = 0.0
    name = next(iter(table))
    for key, w in table.items():
        upto += w
        if roll <= upto:
            return key
    return name


class Course:
    """The parkour: features, landings, moves, and the reservations.

    The order everything happens in is the point of this class, so it is worth
    stating once:

    1. A **feature** is chosen from the current section's theme and expands
       into a list of *nodes*. A node says how far along the trough to go, how
       far in or out, how high above the terrace's own ground to land, and what
       shape the landing is.
    2. Each node is resolved against the world **one at a time**, never in
       advance. A plan several nodes deep is a chain in which the first landing
       that comes down a cell to one side makes every node after it ask for a
       step the physics does not have.
    3. The landing is placed, its **pedestal** is built down to the ground
       under it, and the arc that reaches it, the run across it and the two
       cells over it are all **reserved**.
    4. Only *then* is the terrain around it painted -- and painted around what
       is reserved, never through it.

    Step four is the whole difference from the previous attempt, which built
    the world first and then negotiated with it.
    """

    #: How many landings generation keeps in front of the body. A class
    #: attribute because it is really "how far ahead of the camera the world is
    #: finished", and that is a distance: a tower with longer terraces needs
    #: more landings to cover the same stretch of corridor, and dressing a
    #: section is triggered by the *generator* leaving it. Measured on the
    #: hand-built tower at sixteen, the section the body was standing in had
    #: not been dressed yet a third of the time.
    ahead = AHEAD

    def __init__(self, rng, cone: Cone, hop_rng=None) -> None:
        self.rng = rng
        self.hop_rng = hop_rng or rng
        self.cone = cone
        #: cell -> style for everything *drawn* that is not the cone: pedestals,
        #: terrain dressing, liquids. Handed to the renderer as a stream.
        self.struct: dict[tuple[int, int, int], str] = {}
        self.writes: list[tuple[tuple[int, int, int], str]] = []
        #: Everything solid that the cone does not already account for.
        self.solid: set[tuple[int, int, int]] = set()
        #: Cells dug *out* of the cone -- a pond, a lava channel, a doorway.
        #: Consulted by :meth:`blocked`, which is why a carved pond is water
        #: you fall into rather than a hole painted on a floor.
        self.carved: set[tuple[int, int, int]] = set()
        #: The two cells over every live landing. Checking head-room when a
        #: block is placed is not the same as reserving it: a spiral comes back
        #: over itself, so something laid later lands in the space an earlier
        #: landing was given to stand in.
        self.headroom: set[tuple[int, int, int]] = set()
        #: Every cell the body will pass through on a move already solved.
        self.pathcells: set[tuple[int, int, int]] = set()
        #: Ladders, vines, water columns, cobweb. Drawn, never solid, but
        #: reserved -- a wall built through a ladder is a ladder in a wall.
        self.softcells: set[tuple[int, int, int]] = set()
        #: Cells that are load-bearing *under* a landing. Head-room reserves
        #: what is over a landing and the path reserves what the body passes
        #: through; neither covers the ground a ``floor`` landing stands on,
        #: which places no block of its own. Without this a pond dug during
        #: dressing takes the floor out from under a landing already committed.
        self.ground: set[tuple[int, int, int]] = set()
        self.blocks: list[dict] = []
        self._pending: list[dict] = []
        self.segment = ""
        self.laid = 0
        #: Landings that fell through to the one unchecked answer. Held near
        #: zero by the probe; it is the only hop in the module nothing verified.
        self.stuck = 0
        self.orbs_missed = 0
        #: :meth:`Cone.rock` is six transcendental operations and placement asks
        #: it a few thousand times per landing. Memoised, and pruned in
        #: :meth:`advance` along with everything else that falls off the back.
        self._rock: dict[tuple[int, int, int], bool] = {}
        #: Populated only while :data:`TRACE` is on. See there.
        self.rejects: dict[str, int] = {}
        #: The band of heights whose cone cells have been handed to the
        #: renderer. See :meth:`build_world`.
        self._drawn_lo: int | None = None
        self._drawn_hi: int | None = None
        #: The section whose terrain has been painted, so a section is dressed
        #: once and only after the course has finished crossing it.
        self._painted = -1
        #: Where the last feature left the body, in unwrapped angle. The
        #: course's own progress coordinate.
        self.u = 0.0

        # Start a fifth of the way into a level, not wherever the arithmetic
        # lands. A run that opens near a chasm opens looking at sea and sky
        # with a handful of blocks in it -- and the first three seconds are the
        # ones every viewer sees, on a strip that is up for one thinking turn.
        # A fifth in means a whole themed terrace ahead before the first climb.
        start_u = (cone.level(START_LEVEL).u0 + LEVEL_ARC * 0.2)
        y = cone.floor_at(start_u)
        cone.built_to = y + BUILD_ABOVE
        cone.built_from = y - BUILD_BELOW
        r = sum(cone.floor_range(start_u)) / 2
        th = start_u * cone.wind
        first = self._block(iround(math.cos(th) * r), y - 1,
                            iround(math.sin(th) * r),
                            style=cone.section_at(start_u).theme.ground,
                            form="floor", step=(1, 0), segment="start")
        self.u = start_u
        self.blocks.append(first)
        self.headroom.update((first["x"], y + h, first["z"])
                             for h in range(HEADROOM))
        self.ground.add((first["x"], y - 1, first["z"]))
        while len(self.blocks) < self.ahead:
            self.spawn()

    # -- the world ---------------------------------------------------------

    def build_world(self, y_lo: int, y_hi: int, y_from: int | None = None) -> None:
        """Hand the renderer every cone cell between two heights, once.

        Emitted **outward from ``y_from``**, which is the body, rather than
        upward from the bottom. The chunk mesher builds in the order cells were
        dirtied, so whichever layers are emitted first are the ones meshed
        first -- and emitting bottom-up means the first thing built is the
        world forty-six blocks *below* the camera, which is fog. Measured: 422
        chunks still unmeshed after the priming pass, three and a half seconds
        of a strip that lives for one thinking turn watching its own world
        assemble around it. Nearest-first costs nothing and puts what is in
        shot at the front of the queue.

        Drawn cells only. The cone is *analytic* -- :meth:`Cone.rock` already
        answers every collision question about it without any of this existing
        -- so what is emitted here is a picture and nothing depends on it. That
        is why it can be a one-way frontier that never re-emits and never has
        to be taken back: the body only ever climbs.
        """
        if self._drawn_hi is None:
            start = y_lo if y_from is None else min(max(y_from, y_lo), y_hi)
            self._drawn_lo = start
            self._drawn_hi = start - 1
        # Alternating out from the middle while both ends still have work, so
        # the ceiling overhead and the terrace below arrive together.
        while self._drawn_hi < y_hi or self._drawn_lo > y_lo:
            if self._drawn_hi < y_hi:
                self._drawn_hi += 1
                self.cone.emit_layer(self._drawn_hi, self._draw_only)
            if self._drawn_lo > y_lo:
                self._drawn_lo -= 1
                self.cone.emit_layer(self._drawn_lo, self._draw_only)

    def _draw_only(self, cell, style: str) -> None:
        """A cone cell: drawn, and deliberately not written into ``struct``.

        ``struct`` is what the dressing pass consults to know whether a cell is
        already spoken for, and every cell of the terrace is a cone cell -- put
        them in and nothing may ever be planted anywhere.
        """
        self.writes.append((cell, style))

    def blocked(self, cell) -> bool:
        """Is this cell something a body cannot pass through?

        Three sources and one answer: what the course has built, what the cone
        is made of, and what has been dug out of the cone since.
        """
        if cell in self.solid:
            return True
        if cell in self.carved:
            return False
        hit = self._rock.get(cell)
        if hit is None:
            hit = self.cone.rock(cell)
            self._rock[cell] = hit
        return hit

    def free(self, cells) -> bool:
        return not any(self.blocked(c) for c in cells)

    def reserved(self, cells) -> bool:
        soft = self.softcells
        return any(c in soft for c in cells)

    def band(self, u: float, hug: bool = False) -> tuple[float, float]:
        """The radial range a landing may stand in at this bearing.

        ``hug`` lets a landing sit one cell off the core instead of the usual
        margin, which is what a ladder or a vine needs: the thing it hangs on
        is the tower.

        The upper bound gives way when a landing *asks* to stand beyond the
        rim: the real map's course wanders between radius 28 and 52 around a
        tower whose own silhouette is narrower -- spurs and piers jutting out
        over the sea are half of how its levels read as places rather than a
        corridor. A hug past the band width is exactly that ask, and such a
        landing is necessarily floating or authored structure, because there
        is no ground past the rim for a pedestal to reach.
        """
        out = self.cone.outer_at(u)
        lo = out - self.cone.band_at(u) + (hug or BAND_MARGIN)
        return lo, max(out - BAND_MARGIN, lo + 0.8)

    @property
    def difficulty(self) -> float:
        """How hard the course is being *here*: 0 mild, 1 as hard as it goes.

        Two things multiplied, and they answer different questions. The first
        is the opening ramp, counted in blocks laid rather than in metres
        travelled, because generation runs sixteen landings ahead of the body
        and half the tests grow a course without ever moving one. The second is
        the **level's own** difficulty, which is what stops every level past
        the seventieth landing being the same level: a level is a themed
        terrace with a beginning and an end and six to ten seconds of strip,
        and it is the unit the eye actually reads a course in.
        """
        return (min(1.0, self.laid / RAMP_BLOCKS)
                * self.cone.section_at(self.u).hard)

    # -- blocks ------------------------------------------------------------

    def _block(self, x: int, y: int, z: int, style: str, form: str,
               step: tuple[int, int], segment: str, theme: str = "",
               lift: int = 0) -> dict:
        if not theme:
            theme = self.cone.theme_at(y + 1, x, z).name
        return {"x": x, "y": y, "z": z, "style": style, "form": form,
                "step": step, "out": None, "segment": segment, "theme": theme,
                "yaw": math.atan2(step[0], -step[1]), "laid": self.laid,
                "lift": lift, "born": -1e9,
                "deco": [], "soft": [], "orbs": [], "move": None,
                "path": (), "unchecked": False, "impact": 0.0, "exact": False,
                "pedestal": (), "footing": (), "ceiling": ()}

    def surface(self, blk: dict) -> float:
        return blk["y"] + FORMS[blk["form"]]

    def land_point(self, blk: dict):
        return land_point(blk["x"], self.surface(blk), blk["z"], blk["form"],
                          blk["step"])

    def takeoff_point(self, blk: dict):
        return takeoff_point(blk["x"], self.surface(blk), blk["z"],
                             blk["form"], blk["out"] or blk["step"])

    def ground_speed(self, blk: dict) -> float:
        return SURFACE_SPEED.get(blk["style"], RUN_SPEED)

    def radius_of(self, blk: dict) -> float:
        return math.hypot(blk["x"], blk["z"])

    def u_of(self, blk: dict) -> float:
        return self.cone.unwrap(blk["x"], blk["z"], blk["y"] + 1)

    def _no(self, why: str):
        """Refuse a candidate, and say why if anyone is listening."""
        if TRACE:
            self.rejects[why] = self.rejects.get(why, 0) + 1

    def _far_floor(self, u: float) -> int:
        """The floor of the level on the far side of the chasm at ``u``.

        Nothing may be placed in a chasm below this, and that one rule is what
        makes being stranded impossible rather than merely unlikely. A landing
        low in the hole is a landing nothing can leave: the far wall is four to
        six blocks up and a body cannot jump a chasm and climb it in the same
        move, so the exit climb re-plans from inside the hole and lays its
        staircase through the one already there. Every unchecked landing this
        format had traced back to that, and negotiating it away one case at a
        time never got below two per cent.
        """
        i = self.cone.level_index(u)
        return self.cone.level(i + 1).y

    def _u_at(self, u_ref: float, x: float, z: float) -> float:
        """The unwrapped angle of a point, resolved against one already known.

        Hint-free, and deliberately so. The obvious alternative -- unwrap the
        point against a nearby height -- picks the turn *at or below* that
        height, so a candidate whose terrace floor is a block or two above the
        hint resolves to the turn twenty-two blocks below the right one. Taking
        the small angular difference from a reference angle cannot do that.
        """
        th = math.atan2(z, x) * self.cone.wind
        return u_ref + wrap_angle(th - u_ref)

    def floor_at_cell(self, u_ref: float, x: int, z: int) -> int:
        """The ``y`` a body stands at on the trough's own ground, here."""
        return self.cone.floor_at(self._u_at(u_ref, x, z))

    # -- laying a landing --------------------------------------------------

    def spawn(self) -> dict:
        """Lay the next landing. Never fails, and counts it when it nearly
        does."""
        if not self._pending:
            self._plan_feature()
        prev = self.blocks[-1]
        node = self._pending.pop(0)
        self.laid += 1
        got = self._try_node(prev, node)
        if got is None and node.get("label") == "ascent":
            # The exit climb is the one feature a run cannot do without, so a
            # failure here is answered by trying the other way out rather than
            # by giving up on leaving the level.
            cone = self.cone
            lv = cone.level(cone.level_index(self.u_of(prev)))
            need = cone.level(lv.index + 1).y - int(self.surface(prev))
            self._pending = self._ascent_stair(self.rng, lv, need)
            if self._pending:
                node = self._pending.pop(0)
                got = self._try_node(prev, node)
        if got is None:
            got = self._last_resort(prev)
        if got is None:
            self.stuck += 1
            got = self._emergency(prev, node)
            node = dict(node, label="stuck")
        blk = self._commit(prev, node, got)
        self.u = self.u_of(blk)
        self._paint_behind()
        return blk

    def _try_node(self, prev: dict, node: dict):
        """The node as asked for, then its runners-up, then its fallbacks.

        Every node carries alternatives it would have accepted, because
        placement has to answer questions the feature cannot see -- a rim that
        wobbled in, a pedestal that met the section below -- and a plan that
        offers exactly one answer turns each of those into a failure.
        """
        if node["cross"]:
            node = self._aim_crossing(prev, node)
        steps = (node["step_y"],)
        if node["step_y"] is not None and node["step_y"] > 1:
            # A step may be shortened, never cancelled. Allowing zero looks
            # like generosity and is the opposite: the stair spends its arc,
            # arrives at the chasm no higher than it started, and the jump
            # across -- which is the last node of the feature and the only one
            # that matters -- is then asked to reach a level five blocks up.
            # Measured, that was 68 of 71 stuck landings, every one of them the
            # crossing failing from a staircase that had not climbed.
            steps = (node["step_y"], node["step_y"] - 1)
        # Sideways alternatives, but only for a climb. Every other node's
        # radial offset is the *shape* the feature asked for and moving it is
        # moving the feature; a stair step has no shape to lose and one that
        # cannot be placed where it was aimed is the single most expensive
        # failure in the module -- it drops the body a block short of the level
        # it was climbing to and the crossing then has no jump that reaches.
        sides = ((0.0, 1.6, -1.6)
                 if node["step_y"] is not None or node["label"] == "ascent"
                 else (0.0,))
        for step in steps:
            for side in sides:
                for lift in node["lifts"]:
                    for arc in node["arcs"]:
                        trial = node
                        if (lift != node["lift"] or arc != node["arc"]
                                or step != node["step_y"] or side):
                            trial = dict(node, lift=lift, arc=arc, step_y=step)
                            if node["hug"]:
                                # A hugging node's radius is pinned to the band
                                # and its ``radial`` is never read, so nudging
                                # that would be nudging nothing. Move the lane
                                # instead, and keep it inside the margins.
                                trial["hug"] = min(
                                    max(node["hug"] + side, 2.0),
                                    self.cone.section_at(self.u).band
                                    - BAND_MARGIN)
                            else:
                                trial["radial"] = node["radial"] + side
                        for cell in self._targets(prev, trial):
                            got = self._place(prev, trial, cell)
                            if got is not None:
                                # Whether the landing came out *as asked for*
                                # or on one of the fallbacks. Nothing in the
                                # generator reads it; it is the acceptance
                                # criterion for a hand-built level, where a
                                # fallback means the design did not survive
                                # contact with the lattice and the fix belongs
                                # in the design. See ``tools/tower_probe.py``.
                                got["exact"] = trial is node
                                return got
        # Nothing at any height. Relax the comfort rules -- never the
        # correctness ones -- before giving up on the feature entirely.
        for cell in self._targets(prev, node):
            got = self._place(prev, node, cell, strict=False)
            if got is not None:
                got["exact"] = False
                return got
        return None

    def _aim_crossing(self, prev: dict, node: dict) -> dict:
        """Re-measure the jump over the chasm from where the climb *got to*.

        A crossing planned at the foot of a staircase is aimed from there, and
        by the time it is asked for the body is five landings and a dozen
        blocks of arc further on. So the arc is worked out here, against the
        far lip, and the fallbacks are added rather than scaled: what varies is
        how far onto the far terrace it lands, not how wide the hole is.

        When the body is still well short of the lip this asks for a jump no
        physics has, the crossing is refused, and the climb lays another step
        and asks again -- which is the right answer, and much better than the
        one it used to give.
        """
        u = self.u_of(prev)
        lv = self.cone.level(self.cone.level_index(u))
        reach = max(0.0, (lv.u1 - u) * max(6.0, self.radius_of(prev)))
        arc = reach + 1.2
        return dict(node, arc=arc,
                    arcs=(arc, arc + 0.9, arc + 1.9, max(2.4, arc - 0.7)))

    def _place(self, prev: dict, node: dict, cell, strict: bool = True):
        return self._attempt(prev, node, cell, strict=strict)

    def _last_resort(self, prev: dict):
        """A plain hop along the trough, at whatever height will take it.

        Reached when a feature asks for something the world cannot give. The
        feature is abandoned rather than argued with: the remaining nodes of a
        set-piece whose first landing could not be placed describe a shape that
        no longer exists.
        """
        self._pending = []
        theme = self.cone.section_at(self.u).theme
        if self.segment == "ascent":
            got = self._climb_on(prev, theme)
            if got is not None:
                return got
        for arc in (3, 4, 2, 5, 6):
            for lift in (1, 0, 2, 3, 4):
                for radial in (0.0, 2.0, -2.0, 4.0, -4.0):
                    node = self._node(theme.rock, arc=arc, lift=lift,
                                      radial=radial,
                                      form="floor" if lift == 0 else "full",
                                      label="recover")
                    for cell in self._targets(prev, node):
                        got = self._attempt(prev, node, cell, strict=False)
                        if got is not None:
                            return got
        # Still nothing, which over a chasm is the normal case: everything
        # above wanted ground under it. Two answers, in this order, and the
        # order is the whole point.
        #
        # First, the far side. A recovery that hangs another block in the hole
        # leaves the body lower and further out than it started, the exit climb
        # re-triggers from inside the chasm, and its staircase is laid through
        # the one laid a moment ago -- measured, that cascade was most of the
        # unchecked placements in the module, and it began every time with a
        # *downward* recovery.
        lv = self.cone.level(self.cone.level_index(self.u_of(prev)))
        nxt = self.cone.level(lv.index + 1)
        for arc in (3.0, 4.0, 5.0, 2.4):
            node = self._node(nxt.theme.ground, arc=arc, lift=0, form="floor",
                              label="recover")
            for cell in self._targets(prev, node):
                got = self._attempt(prev, node, cell, strict=False)
                if got is not None:
                    return got
        # ...and only then a block in the air, and only ever *upward*.
        for step in (1, 0):
            for arc in (2.7, 3.1, 2.4, 3.5):
                node = self._node(theme.rock, arc=arc, step_y=step,
                                  pedestal=False, spread=0, label="recover")
                for cell in self._targets(prev, node):
                    got = self._attempt(prev, node, cell, strict=False)
                    if got is not None:
                        return got
        return None

    def _climb_on(self, prev: dict, theme) -> dict | None:
        """Recovery for a failed exit climb that does not throw the climb away.

        The ordinary recovery is a hop at a height measured from the *level's
        own floor*, and during an ascent that is a descent: the body is already
        three or four blocks up its own staircase, so ``lift=1`` puts it back
        on the terrace having spent the arc it needed in order to climb. The
        next step then fails for the same reason from a worse place, and the
        run arrives at the chasm lip having gained nothing -- at which point
        there is no jump in the physics that reaches the far level and the only
        answer left is the unchecked one. Measured, that cascade was two thirds
        of every emergency placement in the module, and every one of them began
        with a *flat* recovery from a climb.

        So the recovery for a climb is another climb. It keeps the height it
        has or gains one, and it is allowed to go sideways across the corridor
        rather than along it -- which is the one direction a staircase that has
        run out of terrace still has, and the reason the arcs here run down to
        under a metre.

        It climbs only while there is climbing left to do. A staircase that has
        already reached the height of the level it is leaving for still has to
        walk to the lip before the crossing is a jump anything can make, and a
        recovery that gains a block every time it fills a stride runs the body
        up into the slab overhead -- at which point every cell round it is
        solid and the only answer left is the unchecked one.
        """
        u = self.u_of(prev)
        lv = self.cone.level(self.cone.level_index(u))
        need = self.cone.level(lv.index + 1).y - int(self.surface(prev))
        on_ground = self.cone.has_floor(u)
        for step in ((1, 0) if need > 0 else (0, 1)):
            for radial in (0.0, 2.6, -2.6, 4.2, -4.2):
                for arc in (2.8, 3.2, 2.4, 3.8, 1.6, 0.8):
                    for hug in (2.4, 0.0):
                        node = self._node(theme.rock, arc=arc, step_y=step,
                                          radial=radial, hug=hug,
                                          pedestal=on_ground,
                                          pedestal_style=theme.sub,
                                          spread=0, confine=on_ground,
                                          label="ascent")
                        for cell in self._targets(prev, node):
                            got = self._attempt(prev, node, cell, strict=False)
                            if got is not None:
                                return got
        return self._grab_the_wall(prev, theme)

    def _grab_the_wall(self, prev: dict, theme) -> dict | None:
        """The last thing to try before the unchecked hop: climb the far wall.

        What is left when everything above has failed is always the same
        picture -- the body on the level's own ground at the chasm lip, two to
        five blocks below the terrace on the other side, with no terrace left
        to climb on and no jump in the physics that both crosses a hole and
        gains that much height. Read as a place rather than as a search
        failure, that is not a dead end at all: there is a wall three metres
        away with four blocks of climbable rock in it.

        So a ladder or a vine goes up the far side of the chasm and the body
        crosses at the top of it. Every part of that is checked by the ordinary
        machinery -- ``_climb_move`` still wants a free column, an anchor to
        hang it on and a reachable grab -- and the far wall is the best anchor
        on the tower. It is also, being a climb, the one recovery in the module
        that makes the move mix *better* rather than more of the same.
        """
        u = self.u_of(prev)
        lv = self.cone.level(self.cone.level_index(u))
        need = self.cone.level(lv.index + 1).y - int(self.surface(prev))
        if need < 2:
            return None                 # a jump would have done, and did not
        kind = "vine" if "vine" in theme.exits else "ladder"
        style, climb = ASCENT_STYLE[kind]
        for step in (need + 1, need, need + 2):
            for hug in (1.6, 2.2, 1.2):
                node = self._node(style, arc=2.4, step_y=step, kind=climb,
                                  climb_style=ASCENT_SOFT[kind], hug=hug,
                                  pedestal=False, spread=0, cross=True,
                                  label="ascent", orbs=2)
                for cell in self._targets(prev, node):
                    got = self._attempt(prev, node, cell, strict=False)
                    if got is not None:
                        return got
        return None

    def _emergency(self, prev: dict, node: dict):
        """The one unchecked answer in the module.

        Clamped into the band and onto the trough's own ground, so that even
        unchecked it is somewhere a body could stand. ``stuck`` counts these
        and the probe holds it near zero.
        """
        pu = self.u_of(prev)
        cone = self.cone
        lv = cone.level(cone.level_index(pu))
        if not cone.has_floor(pu):
            # Stranded out over a chasm. Aim for the far side rather than for
            # another three and a half blocks of nothing: a body left in the
            # hole re-triggers the exit climb from inside it, and the climb
            # then lays its staircase through the one it laid a moment ago.
            # Measured, that cascade was every stuck landing in the module --
            # the first failure cost one, and the loop cost the other nine.
            u = lv.u1 + 2.0 / max(6.0, cone.rim_at(lv.y))
        else:
            u = pu + 3.5 / max(6.0, self.radius_of(prev))
        lo, hi = self.band(u)
        r = min(max(self.radius_of(prev), lo), hi)
        th = u * cone.wind
        cx, cz = iround(math.cos(th) * r), iround(math.sin(th) * r)
        cy = self.floor_at_cell(u, cx, cz)
        # A tuple is truthy whether or not it is (0, 0), so this cannot be
        # written as ``step or (1, 0)`` -- which is what it said until ruff
        # pointed out that the fallback was unreachable. A zero step gives a
        # direction of no length, and the take-off point then lands exactly on
        # the landing point.
        step = (cx - prev["x"], cz - prev["z"])
        if step == (0, 0):
            step = (self.cone.wind, 0)
        frm = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                            prev["form"], step)
        to = land_point(cx, cy + 1.0, cz, "full", step)
        return {"cell": (cx, cy, cz), "step": step, "form": "full",
                "move": Move("hop", [arc_leg(frm, to)]), "soft": (),
                "pedestal": (), "footing": (), "ceiling": ()}

    def _targets(self, prev: dict, node: dict):
        """Candidate landing cells, nearest first to where the helix wants one.

        The ideal point is worked out in the trough's own coordinates -- go
        this far along the arc, this far in or out of the band, this high above
        the ground -- and the *cells* near it are then ranked by how close they
        come. So the course curves continuously along a helix and still lands
        on whole cells, which cannot interpenetrate.
        """
        pu = self.u_of(prev)
        prev_surface = self.surface(prev)
        form = node["form"]
        #: The level a crossing has to have left behind. Resolved here rather
        #: than carried on the node, because a crossing is re-aimed from
        #: wherever the climb actually got to and that may be a level on.
        beyond = self.cone.level_index(pu) if node["cross"] else None
        wants_ground = form == "floor" or (node["pedestal"]
                                           and node["step_y"] is None)
        # A staircase that *started* on solid ground is kept on it: it is the
        # thing that climbs, and the crossing is the thing that leaves. Allowed
        # out over the chasm it arrives at the far wall too low to cross, the
        # climb re-plans from inside the hole, and its new staircase is laid
        # through the old one. But a staircase that starts out over the chasm
        # already -- because something before it went wrong -- has nothing to
        # stand on and must be allowed to hang in the air, or it cannot begin
        # at all and every attempt to recover fails the same way.
        if node["confine"]:
            wants_ground = True
        radius = self.radius_of(prev) + node["radial"]
        u = pu + node["arc"] / max(6.0, radius)
        hug = node["hug"]
        lo, hi = self.band(u, hug)
        if hug:
            radius = lo
        else:
            # Mid-band on a plaza; the *outer edge* of the shelf on a ledge.
            # Two reasons and they compound: the course near the rim stands
            # against sky and drop, which is the exposure this profile
            # exists for -- and the camera rides the course, so a course
            # against the core is a lens full of cliff.
            r0f, r1f = self.cone.floor_range(u, apron=False)
            if r1f < hi:
                want = max(lo + 0.3, r1f - 1.4)
            else:
                want = lo + (hi - lo) * COURSE_OUT
            radius += (want - radius) * COURSE_PULL
            radius = min(max(radius, lo), hi)
        th = u * self.cone.wind
        ix, iz = math.cos(th) * radius, math.sin(th) * radius
        bx, bz = iround(ix), iround(iz)
        span = 3
        scored = []
        for dz in range(-span, span + 1):
            for dx in range(-span, span + 1):
                x, z = bx + dx, bz + dz
                if x == prev["x"] and z == prev["z"]:
                    continue
                cu = self._u_at(u, x, z)
                if cu <= pu + 1e-6:
                    continue            # never backwards along the trough
                if beyond is not None and self.cone.level_index(cu) <= beyond:
                    continue            # a crossing that does not cross
                clo, chi = self.band(cu, hug)
                r = math.hypot(x, z)
                if not (clo - 1.0 <= r <= chi + 1.0):
                    continue
                over_chasm = not self.cone.has_floor(cu)
                if wants_ground and over_chasm:
                    # A landing that needs something under it -- a pedestal
                    # down to the terrace, or the terrace itself -- can never
                    # work out over the chasm, and finding that out one full
                    # attempt at a time was two thirds of every rejection in
                    # the module.
                    continue
                if wants_ground and not self.cone.on_floor(cu, r):
                    # The radial version of the same rule: on a ledge level
                    # everything outboard of the shelf is the drop.
                    continue
                ground = self.cone.floor_at(cu)
                if node["step_y"] is not None:
                    # An absolute step. Deliberately *not* checked against the
                    # floor here: a stair climbing out of a chasm is below the
                    # next level's floor for its whole length, which is the
                    # entire point of it. Whether the cell is inside rock is a
                    # question ``_attempt`` already asks properly.
                    #
                    # Measured between *walking surfaces* and not between block
                    # floors, and the difference is a whole class of failure. A
                    # slab's surface is halfway up its own cell, so a stair
                    # starting from one -- which happens whenever an ordinary
                    # feature left the body on a slab and the exit climb is
                    # what comes next -- asked ``prev["y"] + 1`` for a full
                    # block and got a rise of *one and a half*, which no hop in
                    # this motion model has. Every candidate then failed for
                    # the same reason at every distance. Flooring rather than
                    # rounding is what makes the half-block case legal: it
                    # asks for +0.5, which is a jump a body has, and the step
                    # after is back on whole numbers.
                    y = ifloor(prev_surface + node["step_y"]
                               - FORMS[form] + 1e-6)
                    if over_chasm and y + FORMS[form] < self._far_floor(cu):
                        continue
                    scored.append((math.hypot(x - ix, z - iz), x, y, z))
                    continue
                y = ground + node["lift"] - 1
                if form != "floor" and node["kind"] in BALLISTIC:
                    # **Nothing rises two blocks**, here or in the game -- the
                    # discriminant in ``hop_span`` has no solution for it. On a
                    # helix that is itself a staircase this bites in a way a
                    # flat course never sees: the trough steps up a block every
                    # eight of arc, so a landing one above the ground, reached
                    # from a landing *on* the ground across a step, asks for
                    # two. Measured before this clamp, every single candidate
                    # at two thirds of the stuck cases had a rise of exactly
                    # +2.0, and the feature's own fallback lifts could not
                    # reach below one to fix it.
                    #
                    # Only the ballistic kinds. A ladder, a bubble column and a
                    # slime bounce all rise several blocks by design and that
                    # is the entire reason a map builds one -- clamping those
                    # too took climbs and lifts from three per cent of moves to
                    # none at all.
                    over = (y + FORMS[form]) - (prev_surface + 1.0)
                    if over > 0.0:
                        y -= int(math.ceil(over - 1e-6))
                    if y < ground:
                        continue        # clamped into the floor itself
                scored.append((math.hypot(x - ix, z - iz), x, y, z))
        scored.sort()
        return [(x, y, z) for _, x, y, z in scored[:24]]

    def _attempt(self, prev: dict, node: dict, cell, strict: bool = True):
        """Everything that has to be true, in the order that rejects soonest.

        ``strict`` separates the two kinds of requirement, and the split is
        load-bearing. Without it a landing must be empty, have head-room, sit
        on something, be reachable by a move the physics has, and have a clear
        path -- those are **correctness** and they never relax. With it the
        body must also fit comfortably where it lands and all the way across
        it -- those are **comfort**, and a course that cannot satisfy them
        anywhere is better off grazing a bank than falling through to the one
        answer nothing checked.
        """
        cx, cy, cz = cell
        step = (cx - prev["x"], cz - prev["z"])
        if step == (0, 0) and node["kind"] not in ("climb", "bubble"):
            return self._no("same cell")
        form = node["form"]
        cells = footprint(cx, cy, cz, form)
        if form == "floor":
            # Standing on the trough's own ground: the cell has to be *solid*,
            # which is the exact opposite of every other form's test.
            if not self.blocked((cx, cy, cz)):
                return self._no("floor: no ground")
            # ...and it has to be one nothing has stood on yet. A floor landing
            # places no block, so on its own it gives the course no ratchet at
            # all and a body can shuffle between two cells forever. The
            # head-room over every landing is already reserved; this is simply
            # asking about it.
            if (cx, cy + 1, cz) in self.headroom:
                return self._no("floor: stood on already")
            cells = ((cx, cy, cz),)
        elif not self.free(cells):
            return self._no("landing occupied")
        if not self.free((x, y + h, z)
                         for x, y, z in cells for h in range(1, HEADROOM + 1)):
            return self._no("no head-room")
        if self.reserved(cells) or any(c in self.headroom for c in cells):
            return self._no("reserved")
        if any(c in self.pathcells for c in cells):
            return self._no("in a solved arc")
        got_pedestal = self._pedestal(node, cx, cy, cz, form)
        if got_pedestal is None:
            return self._no("pedestal will not stand")
        pedestal, footing = got_pedestal
        surface = cy + FORMS[form]
        if strict and not self._body_fits(
                land_point(cx, surface, cz, form, step), cells):
            return self._no("body does not fit on landing")
        if strict:
            # The same question about the block being *left*. Which edge the
            # feet leave from is not known until the next landing is chosen --
            # it is chosen here -- and the run across a block toward that edge
            # is a stretch of walking nothing else checks.
            here = self.land_point(prev)
            own = set(footprint(prev["x"], prev["y"], prev["z"], prev["form"]))
            own |= set(body_cells(*here))
            gone = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                                 prev["form"], step)
            for f in (0.34, 0.67, 1.0):
                at = tuple(here[i] + (gone[i] - here[i]) * f for i in range(3))
                if not self._body_fits(at, own):
                    return self._no("body does not fit leaving")
        built = self._move_for(prev, node, cx, cy, cz, form, step, pedestal)
        if built is None:
            return self._no("no move: " + node["kind"])
        move, soft = built
        lid = self._ceiling_cells(prev, node, move)
        if lid is None:
            return self._no("head-hitter will not fit")
        exempt = standing_cells(prev) | standing_cells(
            {"x": cx, "y": cy, "z": cz, "form": form})
        exempt |= set(soft)
        if not self._path_clear(
                move, exempt,
                footprint(prev["x"], prev["y"], prev["z"], prev["form"]),
                tuple(pedestal) + lid):
            return self._no("path blocked")
        return {"cell": (cx, cy, cz), "step": step, "form": form,
                "move": move, "soft": soft, "pedestal": pedestal,
                "footing": footing, "ceiling": lid}

    def _pedestal(self, node: dict, cx: int, cy: int, cz: int, form: str):
        """The stack of terrain under a landing, down to the trough's ground.

        This is what makes the parkour read as *built into the place* rather
        than as cubes hung in the air: a landing three blocks up is the top of
        a three-block dune, a mushroom cap has a stem under it, a wool block
        over the drop has nothing. Returns ``None`` when the stack cannot be
        built, which is a rejection and not a silent drop -- a mushroom cap
        with no stem is a cube floating over a field.
        """
        if not node["pedestal"] or form == "floor":
            return (), ()
        out = []
        #: The cells the stack came to rest *on*. Reserved with it, because a
        #: pond dug during the dressing pass will otherwise happily carve away
        #: the ground a dune is standing on -- the stack itself is protected and
        #: the cell under it was not. Caught by the test that asks whether every
        #: pedestal still reaches something.
        feet = []
        for x, _y, z in footprint(cx, cy, cz, form) or ((cx, cy, cz),):
            for y in range(cy - 1, cy - 1 - LEVEL_RISE[1] - 3, -1):
                c = (x, y, z)
                if self.blocked(c):
                    feet.append(c)
                    break               # it has reached the ground
                if c in self.headroom or c in self.pathcells \
                        or c in self.softcells:
                    # It has reached the air over a landing somewhere below,
                    # or a jump already solved. Neither is free space even
                    # though nothing is drawn in it, and a column driven
                    # through one is a body running with rock through its head.
                    return None
                out.append(c)
            else:
                return None             # never found ground: it is a stilt
        return tuple(out), tuple(feet)

    def _ceiling_cells(self, prev: dict, node: dict, move: Move):
        """The head-hitter over this jump, or ``()`` if it has none.

        **Three above the take-off, not two, and that is a compromise worth
        stating plainly.** The genre's head-hitter is a ``2bc``: a ceiling two
        blocks over the floor, which the player's head strikes, cancelling
        vertical momentum and conserving horizontal. It is the most-used
        obstacle in serious Minecraft parkour precisely because it makes a gap
        harder without making it longer.

        This motion model cannot have one. A body is 1.8 m tall and a jump
        reaches 1.25, so the head sweeps the cells one and two above the
        take-off on *every* hop -- a lid at two is a lid inside the player, and
        the clearance test rightly refuses every jump under it. A faithful
        version needs the game's jump-cancel response in
        :mod:`brainrot.scenes.parkourkit`: hitting the lid zeroes the rise and
        keeps the run. That is a real change to the physics and it is not this
        one.

        At three it is honest and mild: it refuses the arcs that climb hardest
        and passes the flat and descending ones, and it reads as a beam you go
        under. ``None`` means it cannot be built at all.
        """
        n = node["ceiling"]
        if not n:
            return ()
        top = ifloor(self.surface(prev)) + 3
        pts = move.points(ARC_SAMPLES)
        if max(p[1] for p in pts) > top - 0.05:
            return None                 # the jump cannot get under it
        mid = len(pts) // 2
        span = range(-(n // 2), n - n // 2)
        out = []
        for k in span:
            i = min(max(mid + k * 2, 1), len(pts) - 2)
            cell = (iround(pts[i][0]), top, iround(pts[i][2]))
            if cell in out:
                continue
            if self.blocked(cell) or cell in self.pathcells \
                    or cell in self.softcells or cell in self.headroom:
                return None
            out.append(cell)
        return tuple(out)

    def _body_fits(self, at, own) -> bool:
        """Can a body stand at ``at`` without being inside anything?"""
        floor = ifloor(at[1] + 0.05)
        own = set(own)
        for cell in body_cells(*at):
            if cell[1] < floor or cell in own:
                continue
            if self.blocked(cell):
                return False
        return True

    def _path_clear(self, move: Move, exempt, leaving=(), extra=()) -> bool:
        """Nothing solid along the path, except what the body is already in.

        That last clause is the difference between a check that works and one
        that deadlocks: a body is 0.6 m wide and takes off from a block's far
        edge, so on the lattice it routinely straddles the cell next door, and
        which edge it leaves from is not known when the block it stands on is
        placed. The exemption is bounded to the first third of the path, so a
        move that arcs back into what it started beside is still refused.

        ``extra`` is the pedestal this landing is *about* to build. It is not
        in the occupancy map yet and it must still be checked, because a column
        driven down from the block you are jumping to is a column built through
        the arc that gets you there.
        """
        extra = set(extra)
        leaving = set(leaving)
        points = move.points(ARC_SAMPLES)
        early = len(points) // 3
        for i, (x, y, z) in enumerate(points):
            for cell in body_cells(x, y, z):
                if cell in exempt:
                    continue
                if cell not in extra and not self.blocked(cell):
                    continue
                if i <= early and cell in leaving:
                    continue
                return False
            # The cell test cannot see the core's *fractional* face: the
            # browed wall leans by tenths of a block, so a cell whose centre
            # rounds outside it can still hold a body shoulder that is
            # inside. Continuous check against the face alone -- the one
            # solid in the format that is not on the lattice. Waist height
            # is enough: the face only ever leans outward going up, so a
            # clear waist means a clear knee.
            r = math.hypot(x, z) - 0.30
            if r < self.cone.rim_at(y) - BAND_MAX + 3.0:
                # Near the wall (cheap flare arithmetic; no unwrap): now the
                # real question, with the real face.
                u = self.cone.unwrap(x, z, y + 0.9)
                if r < self.cone.core_r(u, ifloor(y + 0.9)) - 1e-6:
                    return False
        return True

    # -- the move vocabulary -----------------------------------------------

    def _move_for(self, prev: dict, node: dict, cx: int, cy: int, cz: int,
                  form: str, step, pedestal):
        """The move that gets from ``prev`` to this cell, or ``None``.

        Every kind answers the same question -- is this a thing a body can
        actually do -- against vanilla's numbers rather than against a table of
        gaps somebody chose. Adding the next verb is an entry here and a
        feature that asks for it, never a branch in a state machine.
        """
        kind = node["kind"]
        frm = takeoff_point(prev["x"], self.surface(prev), prev["z"],
                            prev["form"], step)
        to = land_point(cx, cy + FORMS[form], cz, form, step)
        if kind in ("hop", "slide"):
            speed = ICE_AIR if kind == "slide" else AIR_SPEED
            leg = arc_leg(frm, to, speed)
            if math.dist((frm[0], frm[2]), (to[0], to[2])) < MIN_HOP:
                return None
            if not (VY_MIN <= leg["vy0"] <= VY_MAX):
                return None
            if not (AIR_MIN <= leg["dur"] <= AIR_MAX):
                return None
            # You have to be on the way *down* when you arrive, or the body has
            # come up through the side of the block rather than onto it.
            if leg["dur"] < leg["vy0"] / GRAVITY:
                return None
            return Move(kind, [leg]), ()
        if kind == "bounce":
            vy0 = bounce_launch(prev["impact"])
            if vy0 < JUMP_V * 0.8:
                return None             # the drop that fed it was not enough
            disc = vy0 * vy0 - 2.0 * GRAVITY * (to[1] - frm[1])
            if disc < 0.0:
                return None             # the bounce cannot reach that high
            dur = (vy0 + math.sqrt(disc)) / GRAVITY
            speed = math.dist((frm[0], frm[2]), (to[0], to[2])) / dur
            # A bounce gives no sprint momentum, so what a body can steer to in
            # the air is a band rather than one speed.
            if not (2.6 <= speed <= AIR_SPEED * 1.1):
                return None
            return Move("bounce", [{"kind": "arc", "frm": tuple(frm),
                                    "to": tuple(to), "dur": dur,
                                    "vy0": vy0}]), ()
        if kind in ("climb", "bubble"):
            return self._climb_move(prev, node, cx, cy, cz, form, step, frm,
                                    to, pedestal)
        if kind == "web":
            dist = math.dist(frm, to)
            if not (1.4 <= dist <= 3.6) or abs(to[1] - frm[1]) > 1.01:
                return None
            webs = line_cells(frm, to)
            if not self.free(webs) or self.reserved(webs):
                return None
            return Move("web", [line_leg(frm, to, WEB_SPEED)]), tuple(
                (c, "web", None) for c in webs)
        if kind == "walk":
            dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
            if dist > 2.4 or abs(to[1] - frm[1]) > 0.55:
                return None
            return Move("walk", [line_leg(frm, to, RUN_SPEED)]), ()
        return None

    def _climb_move(self, prev, node, cx, cy, cz, form, step, frm, to,
                    pedestal):
        """A ladder, a vine or a bubble column: grab it, ride it, step off.

        The column stands beside the stack the landing caps, on the side the
        body arrives from, which is the only arrangement where all three legs
        are things a body can do: a short hop onto it, a vertical ride, and a
        step off onto the block at the top. Put the column *under* the landing
        and the last leg has to pass through the block it is aiming at.
        """
        fx, fz = quantise(*step)
        lx, lz = cx - fx, cz - fz
        foot = self.surface(prev)
        top = cy + FORMS[form]
        if not 1.5 <= top - foot <= 9.5:
            return None                 # not worth one, or a ride nobody sits
        column = [(lx, y, lz) for y in range(ifloor(foot), int(top) + 1)]
        if not self.free(column) or self.reserved(column):
            return None
        if any(c in self.pathcells or c in self.headroom for c in column):
            return None
        if not self.free(((lx, int(top) + 1, lz),)):
            return None
        # A ladder has to hang on something: the stack under the landing is the
        # usual answer, and the core wall behind will do just as well.
        pedset = set(pedestal)
        face = None
        for ax, az in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if any(self.blocked((lx + ax, y, lz + az))
                   or (lx + ax, y, lz + az) in pedset
                   for y in (column[len(column) // 2][1], column[-1][1])):
                face = (ax, az)
                break
        if face is None:
            return None
        grab = (lx, foot, lz)
        reach = math.dist((frm[0], frm[2]), (grab[0], grab[2]))
        if not (0.9 <= reach <= 4.2):
            return None
        speed = BUBBLE_SPEED if node["kind"] == "bubble" else CLIMB_SPEED
        legs = [arc_leg(frm, grab, AIR_SPEED),
                line_leg(grab, (lx, top, lz), speed),
                line_leg((lx, top, lz), to, WALK_SPEED)]
        if not (VY_MIN <= legs[0]["vy0"] <= VY_MAX):
            return None
        style = "water" if node["kind"] == "bubble" else node["climb_style"]
        # Which side the wall is on, kept from here rather than worked out
        # again at draw time. A ladder is a plate on a *face*; without knowing
        # which face, the only honest thing to draw is a cube, which is what
        # this scene used to do and what it was rightly pulled up on.
        soft = tuple((c, style, face) for c in column)
        if node["kind"] == "bubble":
            # Soul sand under the column is what makes it push upward. One
            # invisible cell at the bottom of a shaft, skipped rather than
            # forced when the floor is already something else.
            base = (lx, ifloor(foot) - 1, lz)
            if not self.blocked(base):
                soft += ((base, "soulsand", None),)
        return Move(node["kind"], legs), soft

    # -- committing --------------------------------------------------------

    def write(self, cell, style: str) -> None:
        """Draw a cell of terrain, and make it solid unless it is see-through.

        Terrain only. The cone streams itself to the renderer separately and is
        never written here -- it is analytic, and a hundred thousand cells of
        it in a dictionary is the memory this format was rewritten to stop
        spending.
        """
        if cell in self.softcells or cell in self.pathcells \
                or cell in self.headroom or cell in self.ground:
            return
        self.struct[cell] = style
        self.writes.append((cell, style))
        if style not in SEE_THROUGH:
            self.solid.add(cell)
        self._rock.pop(cell, None)

    def carve(self, cell) -> None:
        """Dig a cell out of the cone: a pond, a lava channel, a doorway."""
        if cell in self.pathcells or cell in self.headroom \
                or cell in self.ground:
            return
        self.carved.add(cell)
        self.solid.discard(cell)
        self.struct[cell] = "air"
        self.writes.append((cell, "air"))
        self._rock.pop(cell, None)

    def _commit(self, prev: dict, node: dict, got: dict) -> dict:
        cx, cy, cz = got["cell"]
        theme = self.cone.theme_at(cy + 1, cx, cz)
        blk = self._block(cx, cy, cz, style=node["style"], form=got["form"],
                          step=got["step"],
                          segment=node.get("label") or self.segment,
                          theme=theme.name, lift=node["lift"])
        prev["out"] = got["step"]
        prev["move"] = got["move"]
        # A move belongs to the block it *leaves*, so the emergency answer's
        # label has to be written back one block.
        prev["unchecked"] = node.get("label") == "stuck"
        # The run *across* prev as well as the jump off it. Both are only known
        # now -- which edge the feet leave from is decided by where the course
        # goes next -- and both are corridors terrain must not be painted into.
        run = self.land_point(prev), self.takeoff_point(prev)
        walk = [tuple(run[0][i] + (run[1][i] - run[0][i]) * f
                      for i in range(3)) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
        prev["path"] = tuple({
            c for x, y, z in list(got["move"].points(ARC_SAMPLES)) + walk
            for c in body_cells(x, y, z)})
        self.pathcells.update(prev["path"])
        last = got["move"].legs[-1]
        blk["impact"] = (abs(last["vy0"] - GRAVITY * last["dur"])
                         if last["kind"] == "arc" else 0.0)
        for cell, style, face in got["soft"]:
            self._place_soft(blk, cell, style, face)
        blk["pedestal"] = got["pedestal"]
        blk["footing"] = got["footing"]
        blk["ceiling"] = got["ceiling"]
        blk["exact"] = got.get("exact", False)
        for cell in got["ceiling"]:
            self.write(cell, node["pedestal_style"] or theme.rock)
        for cell in got["pedestal"]:
            self.write(cell, node["pedestal_style"] or node["style"])
        self.blocks.append(blk)
        self.headroom.update(
            (x, y + h, z)
            for x, y, z in footprint(cx, cy, cz, got["form"]) or ((cx, cy, cz),)
            for h in range(1, HEADROOM + 1))
        self.solid.update(cells_of(blk))
        self.ground.update((x, y - 1, z) for x, y, z in
                           footprint(cx, cy, cz, got["form"])
                           or ((cx, cy, cz),))
        self.ground.update(got["pedestal"])
        self.ground.update(got["footing"])
        if node["moat"]:
            self._moat(blk, theme, node)
        if node["shell"]:
            self._shell(prev, blk, theme, node["shell"])
        if got["form"] != "floor":
            for cell in footprint(cx, cy, cz, got["form"]):
                self.struct.setdefault(cell, node["style"])
        if node["deco"]:
            self._decorate(blk, node, theme, got["move"])
        if node["orbs"]:
            self._hang_orbs(prev, blk, node["orbs"])
        return blk

    def _place_soft(self, blk: dict, cell, style: str, face=None) -> None:
        """Ladders, vines, water and webs: drawn, never solid, owned by the
        landing they belong to, and gone when it falls off the back."""
        self.softcells.add(cell)
        self.solid.discard(cell)
        blk["soft"].append({"dx": cell[0] - blk["x"], "dy": cell[1] - blk["y"],
                            "dz": cell[2] - blk["z"], "style": style,
                            "face": face})

    def _decorate(self, blk: dict, node: dict, theme: Theme,
                  move: Move) -> None:
        """The trim on a landing: a lantern, a lintel, a rail, a post."""
        kind = node["deco"]
        fx, fz = quantise(*(blk["out"] or blk["step"]))
        if kind == "lamp":
            blk["deco"].append(deco(0.0, 1.0, 0.0, 0.62, 0.62, 0.62,
                                    theme.glow, glow=True))
        elif kind == "lintel":
            # A beam over the arc, forcing the jump flat. Its height comes from
            # the arc it spans rather than from a number: a beam a fixed
            # distance over the *landing* is either scenery or a wall.
            apex = max(p[1] for p in move.points(9))
            dy = apex - blk["y"] + 0.35
            if dy < 3.6:
                blk["deco"].append(deco(-fx * 1.5, dy, -fz * 1.5,
                                        1.0, 1.0, 1.0, theme.rock))
        elif kind == "post":
            blk["deco"].append(deco(0.0, 1.0, 0.0, 0.22, 1.0, 0.22,
                                    theme.accent))

    def _hang_orbs(self, prev: dict, blk: dict, count: int) -> None:
        """Strung *on* the path that is about to be flown, at chest height,
        which makes "every orb laid down is collected" a property of
        generation rather than a hope about the simulation."""
        move = prev["move"]
        if move is None:
            return
        spread = ORB_FRACTIONS.get(count)
        if spread is None:
            return
        for f in spread:
            x, y, z = move.at(move.dur * f)
            blk["orbs"].append({"x": x, "y": y + CHEST, "z": z, "taken": False})

    def advance(self, index: int) -> int:
        """Drop what is behind the body. Returns how many landings went.

        Cells are released here and nowhere else. This course comes back over
        itself every revolution, so an occupancy map that only grew would
        refuse the tower after two turns of it.
        """
        if index <= TRAIL:
            return 0
        drop = index - TRAIL
        for blk in self.blocks[:drop]:
            self.orbs_missed += sum(1 for o in blk["orbs"] if not o["taken"])
            for cell in cells_of(blk):
                self.solid.discard(cell)
            for cell in (blk["pedestal"] + blk.get("footing", ())
                         + blk.get("ceiling", ())):
                self.solid.discard(cell)
                self.ground.discard(cell)
            for x, y, z in footprint(blk["x"], blk["y"], blk["z"],
                                     blk["form"]) or ((blk["x"], blk["y"],
                                                       blk["z"]),):
                self.ground.discard((x, y - 1, z))
            for s in blk["soft"]:
                self.softcells.discard((blk["x"] + s["dx"], blk["y"] + s["dy"],
                                        blk["z"] + s["dz"]))
            for x, y, z in footprint(blk["x"], blk["y"], blk["z"],
                                     blk["form"]) or ((blk["x"], blk["y"],
                                                       blk["z"]),):
                for h in range(1, HEADROOM + 1):
                    self.headroom.discard((x, y + h, z))
            self.pathcells.difference_update(blk["path"])
        self.blocks = self.blocks[drop:]
        if len(self._rock) > 90000:
            floor = self.blocks[0]["y"] - BUILD_BELOW
            self._rock = {c: v for c, v in self._rock.items() if c[1] >= floor}
        return drop

    # -- features ----------------------------------------------------------

    def _node(self, style: str, arc: float = 3.0, lift: int = 1,
              radial: float = 0.0, kind: str = "hop", form: str = "full",
              deco: str | None = None, orbs: int = 0, pedestal: bool = True,
              pedestal_style: str | None = None, climb_style: str = "ladder",
              spread: int = 2, moat: bool = False, step_y: int | None = None,
              hug: float = 0.0, confine: bool = False, ceiling: int = 0,
              cross: bool = False, ramp: bool = True,
              shell: str | None = None,
              label: str | None = None) -> dict:
        """One entry in a feature's expansion.

        ``lift`` is the height of the landing's walking surface above the
        trough's own ground, and it is the coordinate this whole format is
        expressed in. Saying "three blocks up" rather than "three blocks above
        the last landing" is what keeps the course glued to a helix that is
        itself climbing: the terrace does the climbing, and a feature only says
        how far off the floor it stands.

        ``spread`` is how many neighbouring lifts placement may fall back
        through. Two is generous and right for a free hop; a staircase wants
        zero, because a stair whose steps are sometimes two blocks apart is not
        a staircase.
        """
        if label != "ascent" and ramp:
            # Not the exit climb, and not a distance somebody chose on purpose.
            # A hand-built level's gaps are the design: stretching them by a
            # quarter turns a jump written as "the standard four-block jump"
            # into one no body can make, and the checker then refuses the
            # landing the level was about.
            #
            # Its shape is set by how tall the level is,
            # and the trigger reserves room for exactly that many landings at
            # exactly this spacing -- so ramping it stretches the staircase
            # past the run-up it was promised and the last steps end up out
            # over the chasm, where a stack of terrain cannot stand.
            arc *= 1.0 + GAP_RAMP * self.difficulty
        top = 0 if form == "floor" else LIFT_MAX
        low = 0 if form == "floor" else 1
        lift = min(max(lift, low), top)
        lifts = [lift]
        for d in range(1, spread + 1):
            for cand in (lift - d, lift + d):
                if low <= cand <= top:
                    lifts.append(cand)
        if step_y is not None:
            lifts = [lift]
        return {"style": style, "arc": arc, "lift": lift, "lifts": lifts,
                #: An absolute rise from the landing before, used instead of a
                #: height above the level's own floor. The climb out of a level
                #: needs it: it crosses the boundary where that floor jumps by
                #: four to six blocks at once, so a height measured against
                #: "the floor here" means two different things either side of
                #: one hop.
                "step_y": step_y,
                #: How close to the core to lay this landing, in blocks, or 0
                #: for the usual mid-band pull.
                #:
                #: A distance and not a flag, because the two things that want
                #: it want different amounts. A ladder has to *hang on
                #: something* and out over the chasm the only thing always
                #: there is the tower, so a ladder's column goes to 1.6 -- an
                #: exit climb laid mid-lane finds no anchor and fails, and that
                #: was 96% of every run that got stuck. A staircase only wants
                #: to read as ledges cut into the wall rather than as
                #: free-standing columns and sits at 2.4. Neither may go to
                #: 1.0: that is close enough to put the *camera* in the wall.
                "hug": hug,
                #: Gaps placement may fall back through when the one asked for
                #: has no legal landing. A staircase out of a chasm cannot
                #: settle for a different *height* -- there is only one that
                #: works -- so it has to be allowed a different distance.
                #:
                #: A climb only ever falls back *longer*. Both ends of a
                #: landing are set back from its centre by ``EDGE``, so an arc
                #: of 2.7 is a jump of 2.0 and the shorter fallback would be
                #: 1.6 -- under ``MIN_HOP``, refused before it is even solved.
                #: Offering it wastes a third of every retry on a distance that
                #: cannot work.
                "arcs": ((arc, arc * 1.14, arc * 1.28) if step_y is not None
                         else (arc, arc * 0.84, arc * 1.18)),
                "radial": radial, "kind": kind, "form": form, "deco": deco,
                "orbs": orbs, "pedestal": pedestal,
                "pedestal_style": pedestal_style, "climb_style": climb_style,
                #: Dig the ground away round this landing and fill it with the
                #: theme's liquid. A pond you cross on stepping stones is the
                #: reference's signature overworld beat and it cannot be a
                #: decoration -- the water has to be *under* the jump.
                "moat": moat,
                #: Build an interior around the move onto this landing:
                #: ``tunnel``, ``hall``, ``cave`` or ``shaft``. Painted at
                #: commit, cell by cell through :meth:`write`, whose refusal
                #: of reserved cells is what cuts the doorways -- the shell
                #: cannot close over a path the course has claimed.
                "shell": shell,
                #: Keep this landing over ground that exists. See ``_targets``.
                "confine": confine,
                #: This landing must be on the **far side of the chasm**, and
                #: nothing else will do.
                #:
                #: Without it the jump out of a level was simply a landing on
                #: the trough's own ground at whatever bearing the arc reached
                #: -- and the nearest such ground is the terrace the body is
                #: standing on. Measured, that is what it took: a staircase
                #: climbed its five blocks, the crossing landed back on the
                #: floor it had just climbed off, and the whole climb was spent
                #: again from a worse place with less terrace left. It was the
                #: single largest source of unchecked placements in the module
                #: and it never once looked like a bug in the crossing, because
                #: the crossing always *succeeded*.
                "cross": cross,
                #: Blocks of solid ceiling to hang over the *middle* of the jump
                #: that reaches this landing, at two above the take-off. A real
                #: head-hitter, checked rather than drawn: the arc has to pass
                #: under it or the landing is refused. The genre's most-used
                #: obstacle, and the reason is that it costs no exotic block and
                #: makes an ordinary gap into a jump you have to keep flat.
                "ceiling": ceiling, "label": label}

    def _gap(self, easy, hard) -> float:
        """A feature's gap, ramped between two of its own tables.

        Two tables per feature rather than one shared pair, because "harder"
        does not mean the same thing for all of them: a staircase with a
        four-block gap is not a staircase. Both lean short on purpose -- a
        course of nothing but its longest jump reads as a stunt reel rather
        than as running.
        """
        table = hard if self.rng.random() < self.difficulty else easy
        return table[self.rng.randrange(len(table))]

    def _plan_feature(self) -> None:
        """Decide the next stretch of course, or start the climb out.

        Split into three so that a *hand-built* tower can be the same class
        with one method replaced. The budget and the climb trigger are true of
        any course on this building; only :meth:`_choose_feature` knows that
        this one picks its content from a weighted table rather than reading it
        off a page. See :mod:`brainrot.scenes.handplan`.
        """
        lv, need, want, radius = self._level_budget()
        # The climb out of a level takes priority over everything, and it has
        # to be started early enough that the last landing clears the chasm.
        # Nothing else in the vocabulary can cross a hole with no floor in it
        # and a four-to-seven block wall on the far side.
        if (lv.u_edge - self.u) * radius <= want:
            self.segment = "ascent"
            self._pending = self._feat_ascent(self.rng, lv, need)
            return
        self._pending = self._choose_feature(lv)
        self._truncate(lv, radius, want)

    def _level_budget(self):
        """This level, how much of it is left to climb, and what the climb
        wants: ``(level, need, want, radius)``."""
        cone = self.cone
        lv = cone.level(cone.level_index(self.u))
        need = cone.level(lv.index + 1).y - int(self.surface(self.blocks[-1]))
        radius = max(6.0, cone.rim_at(lv.y))
        gap_blocks = lv.gap * radius
        # One landing of slack. Widening this is the obvious answer to a climb
        # that arrives short and it is the wrong one -- measured, three landings
        # of slack took the unchecked rate from 2.5% to 4.5%, because the
        # reserve is taken out of the level and ``_plan_feature`` then truncates
        # every ordinary feature down to a single node, and single nodes fail
        # far more often than the sequences they were cut from.
        want = ((max(1, need) + 1) * ASCENT_ARC + gap_blocks + 1.4
                + FEATURE_SLACK)
        return lv, need, want, radius

    def _choose_feature(self, lv) -> list[dict]:
        """One feature from the theme's pool, expanded into nodes."""
        section = lv
        theme = section.theme
        weights = {}
        for name, base in FEATURES.items():
            if name in theme.features:
                weights[name] = base * theme.features[name]
            elif name in THEMED:
                continue                # a verb only one theme owns
            elif name == self.segment:
                weights[name] = base * 0.15     # never twice running
            else:
                weights[name] = base
        if lv.signature in weights:
            # The verb this level is *about*. Every reference map builds a
            # section around one and reads as a place because of it; a pool
            # weighted only by theme gives a jungle with the occasional vine
            # in it, which is a different thing.
            weights[lv.signature] *= SIGNATURE_WEIGHT
        if "flat" in weights:
            # The easy beat, and a hard level does not get one. Chaining two or
            # three demanding landings with no rest between them is the
            # cheapest difficulty there is -- it costs no geometry, only the
            # decision not to offer a breather.
            weights["flat"] *= max(0.1, 1.0 - self.difficulty)
        # ...and the demanding half of the shared grammar comes out on a hard
        # level. This is where "harder" actually lives: a longer gap is bounded
        # by one jump impulse and runs out almost at once, whereas a lid to
        # stay under, a one-cell landing and a hole with nothing in it are
        # different *questions* and the pool can ask them as often as it likes.
        for name, extra in HARDER.items():
            if name in weights:
                weights[name] *= 1.0 + extra * self.difficulty
        name = _pick(self.rng, weights)
        self.segment = name
        return getattr(self, f"_feat_{name}")(self.rng, theme)

    def _truncate(self, lv, radius: float, want: float) -> None:
        """Never let a feature run into the run-up the exit climb needs.

        Features are chosen and expanded *whole*, so the one picked while there
        is still room can carry the frontier past the chasm edge on its own --
        and the climb then starts three or four blocks out over the void, where
        a stack of terrain cannot stand and nothing can be placed. Measured,
        that single case was every stuck run in the module. Reserving a wider
        margin instead would work and would cost the levels a third of their
        length; truncating costs nothing.
        """
        budget = (lv.u_edge - self.u) * radius - want
        if budget <= 0:
            return
        keep, spent = [], 0.0
        for node in self._pending:
            if keep and spent + node["arc"] > budget:
                break
            keep.append(node)
            spent += node["arc"]
        self._pending = keep

    # -- painting the place ------------------------------------------------

    def _landmark(self, section: Section) -> None:
        """Paint the level's signature structure, if it names one.

        Placed on the level's own ground, off the course (every cell goes
        through :meth:`_dressable` with a margin, and every base cell must
        have support), and tried at a handful of bearings before giving up --
        a landmark half-built where the course happened to be is worse than
        none. Structures are authored in the trough's own frame: ``dt`` along
        the corridor, ``dy`` up, ``dr`` outward toward the rim.
        """
        name = section.landmark
        build = LANDMARKS.get(name)
        if not build:
            return
        rng = self.rng
        cone = self.cone
        cells = build(rng, section.theme)
        for attempt in range(8):
            # The apron first: on a ledge level it is the one place with room.
            if attempt < 3 and section.profile == "ledge":
                u = cone.apron_u(section) + rng.uniform(-0.4, 0.4) \
                    / max(6.0, cone.rim_at(section.y))
            else:
                f = 0.2 + 0.6 * rng.random()
                u = section.u0 + (section.u1 - section.u0) * f
            if not cone.has_floor(u):
                continue
            r0f, r1f = cone.floor_range(u)
            r = min(r0f + 1.8, r1f - 2.2)
            if section.profile == "ledge":
                r = max(r0f + 1.2, r1f - 3.0)
            th = u * cone.wind
            ct, st = math.cos(th), math.sin(th)
            tx, tz = -st * cone.wind, ct * cone.wind
            top = cone.trough_height(u) - 1
            y = cone.floor_at(u)
            placed = []
            ok = True
            for dt, dy, dr, style in cells:
                if dy > top:
                    continue            # truncated against the soffit
                x = iround(ct * r + tx * dt + ct * dr)
                z = iround(st * r + tz * dt + st * dr)
                cell = (x, y + dy, z)
                if not self._dressable(cell, margin=1):
                    # An accent reaching toward the course -- a doorway lamp,
                    # a cap's rim -- is dropped alone; a structural cell
                    # failing moves the whole structure. One lantern must not
                    # cost a windmill its terrace.
                    if dy > 0:
                        continue
                    ok = False
                    break
                if dy == 0 and not self.blocked((x, y - 1, z)):
                    ok = False          # a base cell over the drop
                    break
                placed.append((cell, style))
            if not ok:
                continue
            seen: set[tuple[int, int, int]] = set()
            for cell, style in placed:
                if cell in seen:
                    continue
                seen.add(cell)
                self.write(cell, style)
                if style == section.theme.glow:
                    cone.lamps.append(cell)
            return

    def _paint_behind(self) -> None:
        """Dress every section the *generator* has finished crossing.

        Never the one it is still in. Terrain painted ahead of the course is
        terrain the course then has to negotiate with, which is the whole
        failure mode this file was written the other way round to avoid; and
        because generation runs sixteen landings ahead of the body, a section
        the frontier has left is still a long way in front of the camera.
        """
        here = self.cone.section_at(self.u).index
        while self._painted < here - 1:
            self._painted += 1
            if self._painted >= 0:
                self._paint(self.cone.sections[self._painted])

    def _paint(self, section: Section) -> None:
        rng = self.rng
        theme = section.theme
        cone = self.cone
        span = section.u1 - section.u0
        if span <= 0:
            return
        self._landmark(section)
        steps = max(6, int(span * cone.outer_at(section.u0) * 1.6))
        pool_at = rng.uniform(0.2, 0.8) if theme.liquid else -1.0
        # Per *block of terrace*, not per section. A section is a third of a
        # revolution and a revolution is as long as the tower is wide, so a
        # fixed count per section is a density that halves when somebody
        # builds a bigger tower -- which is exactly what the hand-built one
        # did, and the terraces came back looking swept.
        budget = max(6, int(span * cone.outer_at(section.u0)
                             * PROP_DENSITY))
        for i in range(steps):
            f = i / steps
            u = section.u0 + span * f
            yf = cone.floor_at(u)
            out = cone.outer_at(u)
            th = u * cone.wind
            ct, st = math.cos(th), math.sin(th)
            r0f, r1f = cone.floor_range(u)
            for _ in range(4):
                # Dressing goes where the ground is. On a ledge level the
                # band's outer half is the drop, and a prop over the drop is
                # a prop floating in the sky.
                r = r1f - (r1f - r0f) * rng.uniform(0.12, 0.92)
                x, z = iround(ct * r), iround(st * r)
                cell = (x, yf, z)
                if not self._dressable(cell):
                    continue
                if theme.liquid and abs(f - pool_at) < 0.06 \
                        and rng.random() < 0.6:
                    self._pool(theme, x, yf, z)
                    break
                if theme.dark > 0.35 and rng.random() < 0.10:
                    # A dark section has to light itself. At the *wall*, not
                    # mid-shelf: the renderer hangs a near-four-metre glow on
                    # every lamp cell, and one sitting beside the running
                    # line is a bloom filling the lens from a metre away.
                    wx = iround(ct * (r0f + 1.2))
                    wz = iround(st * (r0f + 1.2))
                    lamp = (wx, yf, wz)
                    if self._dressable(lamp) and self.blocked(
                            (wx, yf - 1, wz)):
                        self.write(lamp, theme.glow)
                        cone.lamps.append(lamp)
                    break
                if budget > 0 and theme.props and rng.random() < 0.5:
                    budget -= 1
                    kind = theme.props[rng.randrange(len(theme.props))]
                    at = (x, yf, z)
                    if kind in HANGING:
                        # It hangs from its own origin, so it belongs under the
                        # ceiling and not on the floor. Dropped on the floor it
                        # is simply buried, which is the sort of thing that
                        # costs an hour to notice from a contact sheet.
                        at = (x, yf + cone.trough_height(u) - 1, z)
                        if self.blocked(at) or not self.blocked(
                                (x, at[1] + 1, z)):
                            break
                    cone.props.append((at, kind, rng.uniform(0, 6.283)))
                    break
                if rng.random() < 0.22:
                    # A one- or two-block outcrop of the theme's own rock:
                    # what stops a terrace reading as a painted plate.
                    for h in range(rng.randint(1, 2)):
                        if self._dressable((x, yf + h, z)):
                            self.write((x, yf + h, z), theme.rock)
                    break

    def _dressable(self, cell, margin: int = 1) -> bool:
        """Is this a cell dressing may be put in, or dug out of?

        ``margin`` widens the test around the running line, and it is not
        optional. ``pathcells`` is exactly body-width, so a cell merely
        *adjacent* to a jump is free by that test -- and a block face half a
        metre from an eighty-degree lens is most of the frame. Measured without
        it: a fifth of a contact sheet was solid green, which reads as the
        camera being inside the world and is really the camera standing beside
        a boulder nobody meant to put there.
        """
        if (cell in self.headroom or cell in self.ground
                or cell in self.softcells or cell in self.struct):
            return False
        x, y, z = cell
        for dx in range(-margin, margin + 1):
            for dz in range(-margin, margin + 1):
                for dy in (0, 1):
                    if (x + dx, y + dy, z + dz) in self.pathcells:
                        return False
        return True

    def _pool(self, theme: Theme, cx: int, cy: int, cz: int) -> None:
        """A pond, or a lava pool: dug one cell into the ground and filled.

        Dug rather than drawn, so it is genuinely a hole -- the reference's
        desert terrace has a pond you cross, and a blue square painted on sand
        is not one.
        """
        rad = self.rng.randint(2, 3)
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if dx * dx + dz * dz > rad * rad:
                    continue
                cell = (cx + dx, cy - 1, cz + dz)
                if not self._dressable(cell) or not self.blocked(cell):
                    continue
                if not self.blocked((cx + dx, cy - 2, cz + dz)):
                    continue            # over the rim: it would drain away
                self.carve(cell)
                self.write(cell, theme.liquid)

    def _moat(self, blk: dict, theme: Theme, node: dict) -> None:
        """Dig the ground away round a landing and fill it with the theme's
        liquid, so the jump onto it is a jump over water or lava rather than
        over a coloured patch of floor."""
        liquid = node["pedestal_style"] or theme.liquid
        if not liquid:
            return
        gy = self.floor_at_cell(self.u_of(blk), blk["x"], blk["z"]) - 1
        rad = 3
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if dx * dx + dz * dz > rad * rad:
                    continue
                cell = (blk["x"] + dx, gy, blk["z"] + dz)
                if not self._dressable(cell) or not self.blocked(cell):
                    continue
                if not self.blocked((cell[0], gy - 1, cell[2])):
                    continue
                self.carve(cell)
                self.write(cell, liquid)

    def _shell(self, prev: dict, blk: dict, theme: Theme, kind: str) -> None:
        """Build an interior around the move just committed.

        The reference alternates exposed ledge with enclosed rooms every ten
        or twenty seconds, and the old tower had no interior anywhere -- this
        is that other half. Everything goes through :meth:`write`, which
        refuses reserved cells, so the course's own paths punch the doorways
        and nothing here can wall off a jump. Walls only stand where the
        terrain gives them a footing; a column with nothing under it is
        skipped, which is what ends a shell naturally at the chasm.

        ``tunnel`` is tight and flat-roofed, ``hall`` is tall with lamp
        niches, ``cave`` closes down and opens up as it goes, ``shaft`` is a
        tube around a climb.
        """
        if kind == "shaft":
            self._shell_shaft(blk, theme)
            return
        if kind == "grotto":
            self._shell_grotto(prev, blk, theme)
            return
        off, roof_h = {"tunnel": (2, 4), "hall": (3, 6), "cave": (2, 4)}[kind]
        x0, y0, z0 = self.takeoff_point(prev)
        x1, y1, z1 = self.land_point(blk)
        dx, dz = x1 - x0, z1 - z0
        d = math.hypot(dx, dz)
        if d < 0.5:
            return
        dx, dz = dx / d, dz / d
        px, pz = -dz, dx
        wall = theme.rock
        roof = theme.sub
        steps = max(2, int(d / 0.7))
        for i in range(steps + 1):
            f = i / steps
            x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            by = ifloor(min(y0, y1) + (max(y0, y1) - min(y0, y1)) * f + 0.01)
            h_roof = roof_h
            w_off = off
            if kind == "cave":
                # The roof falls and rises and the walls breathe. One closed
                # form keyed on world position, so the two sides agree.
                h_roof = roof_h + iround(1.2 * math.sin(x * 0.9 + z * 1.3))
                w_off = off + (1 if math.sin(x * 1.7 - z * 0.8) > 0.55 else 0)
            for side in (-1, 1):
                wx = iround(x + px * side * w_off)
                wz = iround(z + pz * side * w_off)
                if not self.blocked((wx, by - 1, wz)):
                    continue        # nothing to stand a wall on
                for h in range(h_roof):
                    cell = (wx, by + h, wz)
                    # A lamp *in* the wall, sparingly. The renderer hangs a
                    # near-four-metre glow billboard on every lamp cell, so a
                    # lamp at the course's own floor line is a bloom filling
                    # the lens from a metre away -- wall height keeps it out
                    # of the frame's centre, and one every seven steps keeps
                    # an interior lit without turning it into a lightbox.
                    if h == 2 and i % 7 == 3 and side == 1:
                        self.write(cell, theme.glow)
                        self.cone.lamps.append(cell)
                        continue
                    self.write(cell, wall)
            for lat in range(-w_off, w_off + 1):
                rx = iround(x + px * lat)
                rz = iround(z + pz * lat)
                self.write((rx, by + h_roof, rz), roof)

    def _shell_grotto(self, prev: dict, blk: dict, theme: Theme) -> None:
        """Open the core wall into a bay beside the move: the inward half of
        radial wandering, where the spur past the rim is the outward half.

        The course itself stays legal against the *uncarved* wall -- a
        landing is checked before its shell paints, so a course that entered
        the rock would be refused before the grotto existed. What moves is
        the wall: carved two cells deep along the move, three and a bit
        high, and then *lined*, because the cone's interior is analytic and
        was never painted -- a bare carve would open a window into nothing.
        A lamp on the back wall makes the bay read as a place.
        """
        x0, y0, z0 = self.takeoff_point(prev)
        x1, y1, z1 = self.land_point(blk)
        d = math.hypot(x1 - x0, z1 - z0)
        if d < 0.5:
            return
        steps = max(2, int(d / 0.7))
        cone = self.cone
        lined = theme.sub
        for i in range(steps + 1):
            f = i / steps
            x = x0 + (x1 - x0) * f
            z = z0 + (z1 - z0) * f
            by = ifloor(min(y0, y1) + abs(y1 - y0) * f + 0.01)
            th = math.atan2(z, x)
            ix, iz = math.cos(th), math.sin(th)     # outward radial unit
            u = cone.unwrap(x, z, by)
            face = cone.core_r(u, by)
            for depth in (0.4, -0.6, -1.6):
                cx = iround(ix * (face + depth))
                cz = iround(iz * (face + depth))
                for h in range(4):
                    self.carve((cx, by + h, cz))
                # The bay's floor: the cell under a carve is cone interior,
                # solid but never painted. Line it or the bay looks
                # bottomless.
                self.write((cx, by - 1, cz), theme.ground)
            # The lining, written unconditionally: the bay's back and roof
            # are inside the cone, which is *analytically* solid but was
            # never painted -- the skin is all the emitter draws -- so an
            # unlined carve opens a window onto invisible rock, which is the
            # oldest landmine this project has. Writing makes it visible;
            # it was already solid.
            bx = iround(ix * (face - 2.6))
            bz = iround(iz * (face - 2.6))
            for h in range(5):
                self.write((bx, by + h, bz), lined)
            rx = iround(ix * (face - 1.0))
            rz = iround(iz * (face - 1.0))
            self.write((rx, by + 4, rz), lined)
            self.write((iround(ix * (face - 1.8)), by + 4,
                        iround(iz * (face - 1.8))), lined)
            if i % 6 == 3:
                lamp = (iround(ix * (face - 1.8)), by + 2,
                        iround(iz * (face - 1.8)))
                if not self.blocked(lamp):
                    self.write(lamp, theme.glow)
                    cone.lamps.append(lamp)

    def _shell_shaft(self, blk: dict, theme: Theme) -> None:
        """A tube of the theme's rock around a climb: the belfry, the mine
        shaft, the echo well. The approach and exit paths are reserved cells,
        so the tube gets its doorway for free."""
        soft = blk.get("soft") or ()
        if not soft:
            return
        ys = [blk["y"] + s["dy"] for s in soft]
        lx = blk["x"] + soft[0]["dx"]
        lz = blk["z"] + soft[0]["dz"]
        # The tube stops a course below the top of the climb. The landing
        # *after* the climb does not exist yet when this paints, so a tube
        # sealed to the top has no reserved path to refuse against and walls
        # off the exit -- placement then negotiates around its own shell,
        # and the stuck rate doubles. Open at the top, the ride is still
        # enclosed for its whole length and the dismount has sky.
        lo, hi = min(ys), max(ys) - 1
        # Which way is *out*: the ride faces the tube for three seconds, and
        # a sealed tube is three seconds of bare wall. Louvre slits on the
        # outboard side -- every other course, like a belfry -- put slivers
        # of sky in the climb without opening a way in.
        r = math.hypot(lx, lz)
        ox_out = 1 if lx > 0 else -1
        oz_out = 1 if lz > 0 else -1
        out_axis = 0 if abs(lx) >= abs(lz) else 1
        for ox in (-2, -1, 0, 1, 2):
            for oz in (-2, -1, 0, 1, 2):
                ring = max(abs(ox), abs(oz))
                if ring != 2:
                    continue
                outward = (ox == 2 * ox_out if out_axis == 0
                           else oz == 2 * oz_out)
                for y in range(lo, hi + 1):
                    if outward and y % 2 == (lo % 2) and lo + 1 < y < hi:
                        continue        # the louvre slit
                    self.write((lx + ox, y, lz + oz), theme.rock)
        # Two lamps up the inside of the tube, so the ride is lit.
        for f in (0.33, 0.75):
            cell = (lx + 1, lo + int((hi - lo) * f), lz + 1)
            self.write(cell, theme.glow)
            self.cone.lamps.append(cell)

    def _feat_ascent(self, rng, lv, need: int) -> list[dict]:
        """Dispatch: every level's exit, in whichever way this one climbs."""
        theme = lv.theme
        kind = _pick(rng, {k: w for k, w in ASCENTS.items()
                           if k in theme.exits}) if theme.exits else "stair"
        if kind != "stair" and need >= 3:
            built = self._ascent_climb(rng, lv, need, kind)
            if built:
                return built
        return self._ascent_stair(rng, lv, need)

    def _crossing(self, rng, lv) -> dict:
        """The jump over the chasm onto the next level. The hero jump of the
        format, and the reason everything before it was necessary."""
        nxt = self.cone.level(lv.index + 1)
        gap = lv.gap * max(6.0, self.cone.rim_at(lv.y))
        # It *descends* one block, and that is what makes the widest chasm
        # crossable at all. A flat sprint jump reaches 4.26 m stand-point to
        # stand-point in this project's numbers; dropping a block buys about a
        # metre more, because falling takes longer and the body does not slow
        # down while it does. So the staircase climbs one higher than the level
        # it is heading for and the last jump comes down onto it -- which also
        # means you can see where you are going, from above, before you commit.
        return self._node(nxt.theme.ground, arc=gap + 1.4, lift=0,
                          form="floor", orbs=3, cross=True, label="ascent")

    def _ascent_climb(self, rng, lv, need: int, kind: str) -> list[dict]:
        """Out of the level in one vertical move: a ladder, a vine, a water
        column.

        Short in *arc*, which is the whole reason it exists beside the
        staircase. A staircase gaining seven blocks one at a time eats twenty
        blocks of a level that is only fifty long, and measured with nothing
        but staircases the exit climb was 57% of the entire course -- so a run
        was mostly hopping up cubes over a hole and barely saw the places it
        was climbing past.
        """
        nxt = self.cone.level(lv.index + 1)
        style, climb = ASCENT_STYLE[kind]
        return [
            # A block against the wall to launch from, still over solid ground.
            self._node(lv.theme.rock, arc=2.8, lift=1, hug=2.2, spread=1),
            # 1.6 and not 1.0. The column stands one cell back from the landing,
            # so at 1.6 it is still against the core and finds its anchor -- and
            # the *body*, which stands on the landing rather than on the column,
            # is no longer close enough to the wall to fill the lens with it.
            # 2.0 and not 1.6 since the face grew its lean: the brow bulges
            # up to a block outward near the soffit, and a ride at 1.6 put
            # the body's shoulders through it at the top of tall climbs.
            self._node(style, arc=2.4, step_y=need + 1, kind=climb,
                       climb_style=ASCENT_SOFT[kind], hug=2.0,
                       pedestal=False, spread=0, label="ascent", orbs=2),
            self._crossing(rng, lv),
        ]

    def _ascent_stair(self, rng, lv, need: int) -> list[dict]:
        """The staircase out: a landing a block higher, over and over.

        Every level is flat and ends in a hole with nothing in it, and the next
        level is four to six blocks higher. A body cannot walk over a hole
        and cannot walk up four blocks, so this is not one feature among many
        -- it is the load-bearing one, and if it fails the run is stuck against
        a wall.

        It is a staircase because it has to be: **nothing rises two blocks in
        one ballistic move**, so gaining seven takes seven landings whatever
        else is true. They are laid with ``step_y`` rather than a height above
        the level's floor, because that floor means one thing on the near side
        of the boundary and something four to six blocks different on the far
        side. And they carry no pedestal: a stack of terrain down to the ground
        would fill in the very hole that makes the climb necessary.
        """
        theme = lv.theme
        out = []
        # A stair standing on the level's own ground is built terrain; one that
        # has already been carried out over the chasm can only be hung in the
        # air. Both happen, so ask rather than assume.
        on_ground = self.cone.has_floor(self.u_of(self.blocks[-1]))
        steps = max(0, min(need + 1, LEVEL_RISE[1] + 2))
        for i in range(steps):
            # Standing on the level's own ground, so these carry a stack down
            # to it and read as built terrain -- a flight of piers against the
            # wall -- rather than as cubes hung in the air. Each is one block
            # higher and three along, which is a jump and not a step.
            out.append(self._node(
                # Weaving in and out as it climbs, and the odd half-height
                # step. A straight column of identical hops is the single
                # most monotonous thing a generator can produce, and this is
                # forty per cent of every run.
                (theme.step[0] if theme.step and i % 3 else
                 theme.rock if i % 3 else theme.accent),
                kind=theme.step[1] if theme.step else "hop",
                # Barely any arc at all, because the *lane change* is what
                # carries the jump: a step travels a little over three blocks
                # across the corridor and about one along it, which comes to a
                # hop of two and a half -- comfortably inside the 2.0 to 3.1 a
                # one-block rise allows -- while costing the terrace a third of
                # what a stair walking along the trough costs it.
                # 2.9 to 3.3 and not 2.6 to 3.0. A landing's take-off and
                # touch-down are both set back from the block's centre by
                # ``EDGE``, so an arc of 2.6 is a *jump* of 1.92 -- under
                # ``MIN_HOP``, refused outright, and the shorter of the two
                # fallback arcs was shorter still. Measured, that was every
                # remaining stuck landing: on the ground, below the level it
                # was climbing to, with no legal hop at any offered distance.
                arc=rng.uniform(2.7, 3.1) if on_ground else 2.7,
                step_y=1, pedestal=on_ground, pedestal_style=theme.sub,
                spread=0, confine=on_ground, label="ascent",
                # Weaves, but does not change *form*: a slab step stands half
                # a block up, so the step after it is asked for one and a half
                # and there is no such jump. The climb's arithmetic is exactly
                # one block a landing and nothing in it may be half of one.
                radial=(0.9 if i % 2 else -0.9) * rng.uniform(0.4, 1.0),
                # Against the core. A staircase built out in the middle of the
                # band is a forest of free-standing columns with a cube on top
                # of each -- which is the floating-block look this format is
                # trying not to have, rebuilt at forty per cent of the course.
                # Hard against the wall the same blocks read as ledges cut into
                # the tower, which is what a real map does with them.
                hug=2.4 if i else 0.0,
                orbs=1 if i % 2 == 0 else 0))
        out.append(self._crossing(rng, lv))
        return out

    # -- the shared grammar ------------------------------------------------

    def _feat_hump(self, rng, theme) -> list[dict]:
        """The bread and butter: two or three raised bits of the theme's own
        rock, jumped between. Every landing is the top of something that goes
        down to the ground, which is the whole difference between this format
        and floating-block parkour."""
        out = []
        for _ in range(rng.randint(2, 3)):
            out.append(self._node(theme.rock, arc=self._gap((2.8, 3.2, 3.6),
                                                            (3.2, 3.8, 4.4)),
                                  lift=rng.randint(2, 4),
                                  radial=rng.uniform(-2.0, 2.0),
                                  orbs=1 if rng.random() < 0.5 else 0))
        return out

    def _feat_stairs(self, rng, theme) -> list[dict]:
        """A flight cut into the bank: short hops, each exactly one higher.
        ``spread`` is zero on purpose -- a staircase whose steps are sometimes
        two blocks apart is not a staircase."""
        lift = rng.randint(1, 2)
        out = []
        for i in range(rng.randint(3, 4)):
            out.append(self._node(theme.rock, arc=2.7, lift=lift + i,
                                  radial=rng.uniform(-0.6, 0.6), spread=0,
                                  form="stair"))
        return out

    def _feat_corner(self, rng, theme) -> list[dict]:
        """The around-the-block jump, which the reference playthroughs name as
        the hardest recurring type in these maps: out toward the drop and then
        hard back in, so the second take-off is at right angles to the first."""
        swing = rng.choice((1.0, -1.0)) * rng.uniform(3.0, 4.5)
        lift = rng.randint(1, 3)
        return [self._node(theme.rock, arc=3.4, lift=lift, radial=swing,
                           orbs=1),
                self._node(theme.rock, arc=3.4, lift=lift + rng.randint(0, 1),
                           radial=-swing * rng.uniform(0.9, 1.3))]

    def _feat_slabline(self, rng, theme) -> list[dict]:
        """Half-height landings. Half a block is under the resolution of the
        lattice, so a slab is the one way this format gets a step that is not a
        whole block."""
        return [self._node(theme.accent, arc=self._gap((2.8, 3.2), (3.2, 3.8)),
                           lift=rng.randint(1, 3), form="slab",
                           radial=rng.uniform(-1.5, 1.5))
                for _ in range(rng.randint(2, 3))]

    def _feat_headhitter(self, rng, theme) -> list[dict]:
        """A ceiling two blocks over the take-off, so the jump has to stay flat.

        The genre calls this a ``2bc`` and it is the most-used obstacle in
        serious Minecraft parkour, for a reason worth restating: it makes a gap
        harder *without making it longer*. Difficulty in this format used to
        come only from distance, which is the one axis that runs out -- nothing
        reaches five blocks flat, ever.

        It is a checked constraint and not a decoration. The lid goes into the
        arc's own clearance test, so a landing whose jump would rise through it
        is refused rather than drawn with a beam through the player's head.
        """
        wide = 1 + int(self.difficulty * 2)
        return [self._node(theme.rock, arc=3.2, lift=rng.randint(1, 2),
                           ceiling=rng.randint(1, max(1, wide)), spread=1,
                           orbs=1),
                self._node(theme.rock, arc=3.4, lift=rng.randint(1, 3))]

    def _feat_duckrun(self, rng, theme) -> list[dict]:
        """Two or three head-hitters back to back, with no recovery between.

        Removing the recovery time between jumps is one of the four ways the
        reference material says hard parkour is actually made -- the others
        being a constrained run-up, a ceiling, and an obstacle in the flight
        path. This is two of them at once, and it costs no new block.
        """
        return [self._node(theme.rock, arc=rng.uniform(3.0, 3.4),
                           lift=rng.randint(1, 2), ceiling=1, spread=1,
                           radial=rng.uniform(-1.4, 1.4), orbs=1)
                for _ in range(rng.randint(2, 3))]

    def _feat_voidgap(self, rng, theme) -> list[dict]:
        """One long jump out over the drop, bought with a drop of its own.

        The furthest a body can reach is fixed by one jump impulse and one
        horizontal speed -- about 4.3 m level. Reaching further is only
        available by *descending*, because falling takes longer and the body
        does not slow down while it does. So this feature steps down, exactly
        as a player clears a gap they cannot make level.
        """
        drop = rng.randint(1, 3)
        return [self._node(theme.rock, arc=rng.uniform(3.4, 4.0),
                           lift=min(LIFT_MAX, 2 + drop),
                           radial=rng.uniform(1.0, 2.5), orbs=1),
                self._node(theme.rock, arc=self._gap((4.2, 4.6), (4.6, 5.4)),
                           lift=max(1, 2 + drop - drop), radial=-1.0, orbs=3)]

    def _feat_pillars(self, rng, theme) -> list[dict]:
        """Three narrow columns, tight together and tall. The one shape in the
        shared grammar that is genuinely vertical."""
        lift = rng.randint(3, 5)
        return [self._node(theme.rock, arc=2.9, lift=lift + rng.randint(-1, 1),
                           radial=rng.uniform(-1.8, 1.8), spread=1,
                           pedestal_style=theme.sub)
                for _ in range(3)]

    def _feat_spire(self, rng, theme) -> list[dict]:
        """A climb onto something tall, in two hops because one cannot rise
        two blocks -- here or in the game."""
        top = rng.randint(4, LIFT_MAX)
        return [self._node(theme.rock, arc=3.4, lift=top - 2, spread=1),
                self._node(theme.accent, arc=3.4, lift=top - 1, spread=1),
                self._node(theme.accent, arc=3.2, lift=top, spread=1,
                           deco="lamp" if theme.dark > 0.4 else None)]

    def _feat_flat(self, rng, theme) -> list[dict]:
        """A beat of running on the terrace's own ground. Rare on purpose: it
        is the rest between two phrases, and a course made of it is the "walk a
        bit, jump, jump, walk a bit" this format was rebuilt to stop being."""
        # The walk leg goes *between* two ground landings and not onto the
        # first of them: a walk is capped at 2.4 m and half a block of rise, so
        # a walk node arriving from a landing three blocks up is a walk that
        # never once succeeds. Measured at 0.3% of moves before this order.
        out = [self._node(theme.ground, arc=rng.uniform(2.4, 3.0), lift=0,
                          form="floor", radial=rng.uniform(-2.0, 2.0))]
        for _ in range(rng.randint(1, 2)):
            out.append(self._node(theme.ground, arc=rng.uniform(1.5, 2.0),
                                  lift=0, form="floor", kind="walk",
                                  radial=rng.uniform(-1.2, 1.2)))
        return out

    # -- water, lava and the things you cross them on ----------------------

    def _feat_pond(self, rng, theme) -> list[dict]:
        """Stepping stones across a pond dug into the terrace.

        ``moat`` is what makes it a pond: the ground round each stone is dug
        out and filled, so the jump is genuinely over water. A blue patch
        painted on the floor is not a pond and does not read as one.
        """
        return [self._node(theme.rock, arc=self._gap((2.8, 3.2), (3.2, 3.8)),
                           lift=1, radial=rng.uniform(-1.5, 1.5), moat=True,
                           orbs=1)
                for _ in range(rng.randint(2, 4))]

    def _feat_channel(self, rng, theme) -> list[dict]:
        """One irrigation channel, jumped in one go."""
        return [self._node(theme.rock, arc=3.4, lift=1, moat=True),
                self._node(theme.rock, arc=self._gap((3.8, 4.2), (4.2, 4.8)),
                           lift=1, orbs=2)]

    def _feat_lavaleap(self, rng, theme) -> list[dict]:
        """The nether's pond: the same shape, and it reads completely
        differently because of what is under it."""
        return [self._node(theme.accent, arc=self._gap((3.0, 3.4), (3.4, 4.2)),
                           lift=rng.randint(1, 2),
                           radial=rng.uniform(-2.0, 2.0), moat=True,
                           pedestal_style=theme.liquid, orbs=1)
                for _ in range(rng.randint(2, 3))]

    # -- the verbs ---------------------------------------------------------

    def _feat_iceline(self, rng, theme) -> list[dict]:
        """Packed ice: the body carries its speed off the end of it.

        What ice buys is *carried momentum*, not a longer arc -- the flight
        time of a jump is fixed by its height -- so the jumps *off* ice are the
        long ones and the run onto it is ordinary.
        """
        out = [self._node("packedice", arc=3.4, lift=rng.randint(1, 2))]
        for _ in range(rng.randint(1, 2)):
            out.append(self._node("packedice", arc=rng.uniform(3.6, 4.4),
                                  lift=rng.randint(1, 2), kind="slide",
                                  orbs=2))
        out.append(self._node(theme.rock, arc=rng.uniform(4.0, 5.0),
                              lift=rng.randint(1, 3), kind="slide", orbs=3))
        return out

    def _feat_soulwalk(self, rng, theme) -> list[dict]:
        """Soul sand: two fifths of walking pace, and the slowest ground in the
        scene. Everything either side of it reads faster for it."""
        return [self._node("soulsand", arc=2.9, lift=rng.randint(1, 2),
                           radial=rng.uniform(-1.2, 1.2))
                for _ in range(rng.randint(2, 3))]

    def _feat_webwalk(self, rng, theme) -> list[dict]:
        """A clump of cobweb, waded through. Vanilla divides horizontal
        movement by four, which is three seconds for two metres; the kernel
        leaves the game behind here and says so, because the strip is on screen
        for fifteen seconds and cannot spend a fifth of it in one web."""
        out = [self._node(theme.rock, arc=2.9, lift=rng.randint(1, 2))]
        for _ in range(rng.randint(1, 2)):
            out.append(self._node(theme.rock, arc=3.4, lift=rng.randint(1, 2),
                                  kind="web"))
        out.append(self._node(theme.rock, arc=3.2, lift=rng.randint(1, 3)))
        return out

    def _feat_ladderrun(self, rng, theme) -> list[dict]:
        """A ladder up the side of something. The trade a ladder makes is time
        for height, and one that climbs at running pace is a lift."""
        out = [self._node(theme.rock, arc=2.7, lift=1, spread=1)]
        for _ in range(rng.randint(1, 2)):
            out.append(self._node(theme.rock, arc=2.5,
                                  lift=rng.randint(4, LIFT_MAX), kind="climb",
                                  climb_style="ladder", spread=1,
                                  pedestal_style=theme.sub, orbs=1))
            out.append(self._node(theme.rock, arc=3.2, lift=1, spread=1))
        out.append(self._node(theme.rock, arc=3.4, lift=rng.randint(2, 4)))
        return out

    def _feat_vineclimb(self, rng, theme) -> list[dict]:
        """The jungle's ladder. Same physics, and the reference playthroughs
        are unanimous that vines are the part everyone remembers."""
        return [self._node(theme.rock, arc=2.7, lift=1, spread=1),
                self._node("junglelog", arc=2.5,
                           lift=rng.randint(4, LIFT_MAX), kind="climb",
                           climb_style="vine", spread=1,
                           pedestal_style="junglelog", orbs=1),
                self._node(theme.rock, arc=3.4, lift=rng.randint(2, 4))]

    def _feat_bubblelift(self, rng, theme) -> list[dict]:
        """A soul-sand bubble column: eleven blocks a second, twice sprinting,
        and by a distance the fastest way up anything in the game. Not a number
        worth softening -- arriving six blocks higher in half a second is the
        whole reason a map builds one."""
        return [self._node(theme.rock, arc=2.7, lift=1, spread=1),
                self._node(theme.accent, arc=2.5,
                           lift=rng.randint(4, LIFT_MAX), kind="bubble",
                           spread=1, pedestal_style=theme.sub, orbs=2),
                self._node(theme.rock, arc=3.4, lift=rng.randint(2, 4))]

    def _feat_slimebounce(self, rng, theme) -> list[dict]:
        """Fall onto slime, come back up somewhere else.

        Vanilla's restitution is exactly 1.0 and holding jump *cancels* a
        bounce, so slime is **not** a way to gain height: a bounce can never
        reach past the fall that fed it. What it is for is spending a drop
        somewhere else, which is what the drop below sets up.
        """
        high = rng.randint(4, LIFT_MAX)
        return [self._node(theme.accent, arc=3.4, lift=high, spread=1),
                self._node("slime", arc=rng.uniform(3.0, 3.8), lift=1,
                           pedestal_style=theme.sub),
                self._node(theme.rock, arc=rng.uniform(3.0, 4.0),
                           lift=rng.randint(2, high - 1), kind="bounce",
                           orbs=3)]

    # -- places ------------------------------------------------------------

    def _feat_haystack(self, rng, theme) -> list[dict]:
        """Hay bales, stacked. The farm's staircase."""
        return [self._node("hay", arc=2.7, lift=1 + i, spread=0,
                           pedestal_style="hay")
                for i in range(rng.randint(2, 3))]

    def _feat_rooftop(self, rng, theme) -> list[dict]:
        """Two cottages, jumped roof to roof. ``wide`` because a roof you land
        on the corner of is a chimney."""
        lift = rng.randint(4, 5)
        return [self._node("roof", arc=self._gap((3.2, 3.6), (3.6, 4.4)),
                           lift=lift + rng.randint(-1, 0), form="wide",
                           pedestal_style="plaster",
                           radial=rng.uniform(-2.0, 2.0), orbs=1)
                for _ in range(2)]

    def _feat_doorway(self, rng, theme) -> list[dict]:
        """Through a house rather than over it: a lintel at head height and a
        landing the far side."""
        return [self._node("plaster", arc=3.4, lift=1, deco="lintel",
                           pedestal_style="plaster", spread=1),
                self._node("brick", arc=3.4, lift=rng.randint(1, 2))]

    def _feat_capstep(self, rng, theme) -> list[dict]:
        """Giant mushroom caps: a wide flat top on a thin stem, which is the
        one silhouette in the game that is genuinely a platform."""
        cap = "mushroomred" if theme.name == "mushroom" else theme.accent
        stem = "mushroomstem" if theme.name == "mushroom" else theme.sub
        return [self._node(cap, arc=self._gap((3.0, 3.4), (3.4, 4.2)),
                           lift=rng.randint(3, 5), form="wide",
                           pedestal_style=stem,
                           radial=rng.uniform(-2.0, 2.0), orbs=1)
                for _ in range(rng.randint(2, 3))]

    def _feat_canopy(self, rng, theme) -> list[dict]:
        """Leaf platforms on log trunks."""
        return [self._node("jungleleaf", arc=self._gap((3.0, 3.6), (3.6, 4.2)),
                           lift=rng.randint(4, LIFT_MAX), form="wide",
                           pedestal_style="junglelog",
                           radial=rng.uniform(-2.5, 2.5), orbs=2)
                for _ in range(2)]

    def _feat_logstep(self, rng, theme) -> list[dict]:
        """Fallen logs across the floor."""
        return [self._node("junglelog", arc=3.4, lift=rng.randint(1, 2),
                           radial=rng.uniform(-2.0, 2.0),
                           pedestal_style="podzol")
                for _ in range(rng.randint(2, 3))]

    def _feat_endpillar(self, rng, theme) -> list[dict]:
        """Obsidian columns capped in purpur, with a rod on top. The End's
        whole visual grammar is vertical."""
        return [self._node("purpur", arc=self._gap((3.0, 3.4), (3.4, 4.2)),
                           lift=rng.randint(4, LIFT_MAX), spread=1,
                           pedestal_style="obsidian", deco="post", orbs=1)
                for _ in range(rng.randint(2, 3))]

    def _feat_rodline(self, rng, theme) -> list[dict]:
        """End rods: thin, bright, and floating, because in the End nothing
        needs holding up."""
        return [self._node("quartz", arc=2.7, lift=rng.randint(2, 4),
                           form="slab", pedestal=False,
                           radial=rng.uniform(-1.6, 1.6), deco="lamp",
                           orbs=1)
                for _ in range(rng.randint(2, 3))]

    def _feat_woolcheck(self, rng, theme) -> list[dict]:
        """The wool section: the one place floating parkour is on-theme.

        Every other section's landings are the tops of things. These are cubes
        hung over the drop in sixteen colours, which is the reference's
        signature abstract band -- and it only reads as deliberate because
        nothing else in the tower does it.
        """
        i = rng.randrange(len(WOOLS))
        out = []
        for n in range(rng.randint(3, 4)):
            out.append(self._node(WOOLS[(i + n) % len(WOOLS)],
                                  arc=self._gap((3.0, 3.4), (3.4, 4.2)),
                                  lift=rng.randint(2, 5), pedestal=False,
                                  radial=(2.2 if n % 2 else -2.2)
                                  * rng.uniform(0.6, 1.2), orbs=1))
        return out

    def _feat_dune(self, rng, theme) -> list[dict]:
        """Wide sandy humps, which is what the desert terrace in the reference
        is almost entirely made of."""
        return [self._node(theme.rock, arc=self._gap((3.0, 3.4), (3.4, 4.2)),
                           lift=rng.randint(2, 4), form="wide",
                           pedestal_style=theme.ground,
                           radial=rng.uniform(-2.5, 2.5))
                for _ in range(2)]

    def _feat_railrun(self, rng, theme) -> list[dict]:
        """Sleepers along a mine floor, with the rail drawn on them."""
        return [self._node("oak", arc=2.9, lift=1, radial=rng.uniform(-1, 1),
                           pedestal_style="deepslate",
                           deco="lamp" if rng.random() < 0.4 else None)
                for _ in range(rng.randint(3, 4))]

    def _feat_croprow(self, rng, theme) -> list[dict]:
        """Low hops along the furrows."""
        return [self._node("farmland", arc=2.9, lift=1,
                           radial=rng.uniform(-2.5, 2.5),
                           pedestal_style="dirt")
                for _ in range(rng.randint(2, 3))]

    def _feat_fencehop(self, rng, theme) -> list[dict]:
        """Fence posts, which are the narrowest thing anybody stands on in
        these maps. Slabs, because a fence post is not a whole block."""
        return [self._node("oak", arc=3.4, lift=2, form="slab",
                           radial=rng.uniform(-2.0, 2.0),
                           pedestal_style="oak")
                for _ in range(rng.randint(2, 3))]

    def _feat_cactusrun(self, rng, theme) -> list[dict]:
        """Low sand hops with the cactus scattered round them by the dressing
        pass, which is the only reason this is not just ``hump``: the props go
        in afterwards and go round what is reserved."""
        return [self._node(theme.rock, arc=3.4, lift=rng.randint(1, 2),
                           radial=rng.uniform(-2.5, 2.5),
                           pedestal_style=theme.ground)
                for _ in range(rng.randint(2, 3))]

    def _feat_treestump(self, rng, theme) -> list[dict]:
        """Cut stumps: wide, low, and the plains' only vertical furniture."""
        return [self._node("oak", arc=self._gap((2.8, 3.2), (3.2, 3.8)),
                           lift=rng.randint(2, 3), form="wide",
                           pedestal_style="oak",
                           radial=rng.uniform(-2.0, 2.0))
                for _ in range(2)]


# ---------------------------------------------------------------------------
# The feature vocabulary
# ---------------------------------------------------------------------------
#
# Every feature is a stretch of trough decided *whole* -- its landings and the
# terrain those landings are the tops of, together -- because that is the only
# way to express "three sandstone dunes with a pond between them" at all. A
# feature that only chose landings would be laying cubes in the air and
# hoping the dressing agreed with them afterwards.
#
# The base weight is what a feature is worth to a theme that has not asked for
# it. Anything in :data:`THEMED` is worth nothing to such a theme -- those are
# the verbs a place owns, and an ice run in a nether section is how a themed
# tower stops reading as themed.

#: Record *which* check refused each candidate landing.
#:
#: Off by default because placement asks these questions a few thousand times
#: per landing and a counter on that path is measurable. Turn it on and the
#: answer to "why is the course falling through to its emergency hop" stops
#: being a guess: every reduction this format has had -- from thirteen per cent
#: of nodes to a fraction of one -- came from reading this table, and not one
#: of them was found by reading the code.
TRACE = False

#: How many pieces of sub-block furniture one section gets. Each is its own
#: draw call against a whole terrace that costs a handful, so this is set by
#: the frame budget rather than by how much room there is.
PROP_BUDGET = 14
#: ...expressed as a rate, which is what the dressing pass actually uses.
#: Set so that the generated tower's count is unchanged.
PROP_DENSITY = PROP_BUDGET / (LEVEL_ARC * BASE_R)

# The shared grammar is deliberately worth *less* than a theme's own verbs.
# Measured at the first weights that worked at all, the move mix came out 96.6%
# plain hop -- which is precisely the "jump, jump, jump, then walk a bit" this
# rebuild exists to stop being. A section has to be mostly the thing it is: the
# ice section mostly slides, the mine mostly climbs, the nether mostly leaps
# lava. The shared features are the connective tissue between those, not the
# substance.
FEATURES: dict[str, float] = {
    # -- the shared grammar, available everywhere
    "hump": 1.9, "stairs": 1.0, "corner": 1.2, "slabline": 0.8,
    "headhitter": 1.1, "voidgap": 0.9, "pillars": 0.9, "spire": 0.7,
    "flat": 0.5, "duckrun": 0.9,
    # -- verbs a place owns
    "pond": 2.4, "channel": 2.4, "lavaleap": 2.4, "iceline": 1.6,
    "soulwalk": 2.4, "webwalk": 2.4, "ladderrun": 2.4, "vineclimb": 1.6,
    "bubblelift": 2.4, "slimebounce": 2.4, "haystack": 2.4, "rooftop": 1.6,
    "doorway": 2.4, "capstep": 2.4, "canopy": 2.4, "logstep": 1.6,
    "endpillar": 2.4, "rodline": 2.4, "woolcheck": 2.4, "dune": 1.6,
    "railrun": 2.4, "croprow": 2.4, "fencehop": 2.4, "cactusrun": 1.6,
    "treestump": 2.4,
}

#: Extra weight a feature gets at full difficulty, over its base.
#:
#: These are the shared grammar's demanding entries, and they are the honest
#: answer to "make it harder": a head-hitter to stay flat under, one-cell
#: landings, a spire, a run at a ceiling, a hole with nothing in it. Gap length
#: is a poor difficulty dial in this motion model -- there is one jump impulse,
#: so the whole usable range is 2.0 to 4.3 m and a course spends most of it by
#: the second landing. What kind of question the landing asks is not bounded
#: like that.
HARDER: dict[str, float] = {
    "headhitter": 1.8, "pillars": 1.3, "spire": 1.5, "voidgap": 1.1,
    "duckrun": 1.0, "slabline": 0.8,
}

#: Features whose landings are reached by something other than a jump. Named
#: rather than derived, because a feature's move kind is a keyword buried in
#: its own expansion and nothing else has cause to go looking for it.
NON_HOP = frozenset((
    "iceline", "webwalk", "ladderrun", "vineclimb", "bubblelift",
    "slimebounce",
))

#: Features that appear only in a theme that names them.
THEMED = frozenset((
    "pond", "channel", "lavaleap", "iceline", "soulwalk", "webwalk",
    "ladderrun", "vineclimb", "bubblelift", "slimebounce", "haystack",
    "rooftop", "doorway", "capstep", "canopy", "logstep", "endpillar",
    "rodline", "woolcheck", "dune", "railrun", "croprow", "fencehop",
    "cactusrun", "treestump",
))
