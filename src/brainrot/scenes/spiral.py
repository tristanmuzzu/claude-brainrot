"""First-person parkour up the outside of a spiral tower.

The renderer. :mod:`brainrot.scenes.spiralplan` owns the building, the course
and the physics and imports nothing from here; this file meshes what that
module describes, moves a body along it, and points a camera.

The camera is the half of this scene that is not obvious, and it is worth
saying why it is first-person at all. The tower is a solid cone seventy metres
across, and the strip is 360x640 -- about fifty degrees of horizontal field.
You cannot see the whole thing and you are not meant to: the format is a
*corridor*. The trough has the drop and the sky on your outboard side, the
fluted core on your inboard side, and the floor slab of the turn above as a
ceiling. What sells the climb is not the silhouette, which you never see. It
is that the drop beside you keeps deepening, the ground under your feet keeps
becoming somewhere else, and the ceiling overhead keeps arriving and passing.

Everything below this line is meshing, weather, a body and a lens. None of it
knows what shape the building is beyond the two questions in ``_indoor_want``
and ``_aim_camera``.
"""

from __future__ import annotations

import math

from .. import assets
from ..engine import chunk, rl, textures, voxel
from ..engine.collide import AABB
from ..engine.fx import Burst, Weather, glow_pass, no_depth_write
from ..engine.hud import chip, text
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import SkyDome
from ..engine.textures import cloud_blob
from . import handplan as hp
from . import parkourkit as tp
from . import spiralplan as sp

#: Vertical field of view. A touch wider than the flat scene's, because the
#: subject here is tall and close: the wall is three metres away and the thing
#: worth seeing is how far it goes up and how far it goes down.
FOV = 82.0
#: The camera's own smoothing, and the flat scene's reasoning applies here
#: unchanged -- see ``parkour.FOV_GAIN`` and the block beneath it. Every one of
#: these replaced a value that was switched between two constants at a phase
#: boundary: the lens zoomed two degrees at every take-off and back at every
#: landing, the eye was dropped 0.17 m in a single frame when the feet touched
#: down, and the walk bob appeared and vanished whole. Eight steps a second,
#: which is what "he clicks into something and sticks to the block" is from
#: inside the head.
FOV_GAIN = 1.4
FOV_EASE = 6.0
DIP_W = 13.0
DIP_ZETA = 1.0
DIP_KEEP = 0.6
#: The impact an ordinary jump lands with, which costs the lens nothing, and
#: the fastest fall past it the legs will pass on. See ``parkour.DIP_FREE``.
DIP_FREE = tp.JUMP_V
DIP_CAP = 6.0
#: What every landing is worth regardless -- the beat. See the flat scene's.
DIP_BASE = 1.6
#: How fast the peak-hold on the running speed bleeds away, in m/s per second.
#: A second and a half from a sprint down to a walk: long enough that the
#: air/ground alternation never reaches the lens, short enough that stepping
#: onto soul sand still says so.
PACE_FALL = 2.0
FOOT_EASE = 9.0
#: How far a piece of furniture is still drawn, and how far out of the camera's
#: own direction. The strip is portrait with about fifty degrees of horizontal
#: field, so most of a sphere around the body is behind it.
PROP_FAR = 30.0
PROP_AHEAD = -0.2

#: How far a landing is still lit. Past this it is a few pixels in the haze and
#: the glow is a draw call for nothing.
LAND_LIT_FAR = 26.0

#: Distance at which the course has faded fully into the haze.
FOG_FAR = 110.0
#: How far below the body the tower is still drawn. Beyond this it is a smudge
#: in the fog and every chunk of it is a draw call for nothing.
BELOW = 62
#: ...and how far above. Generation runs sixteen blocks ahead of the body, but
#: the *building* is worth seeing a long way further than that -- a tower whose
#: top is fourteen blocks up is a chimney.
ABOVE = 40

#: Where the sea is. A long way under the bottom of the built tower, so what
#: is under you is *haze* with water somewhere in it rather than a floor -- and
#: so the drop keeps reading as a drop after a hundred blocks of climbing.
SEA_Y = -90.0
#: How much further away everything below the body is treated as being. The
#: tower is only built fifty blocks down, and without this its bottom edge is a
#: crisply lit stub hanging in mid-air.
UNDER_FOG = 2.6

# ---------------------------------------------------------------------------
# What else is out there
# ---------------------------------------------------------------------------
#
# The tower stood in an empty ocean under an empty sky: one flat blue plane a
# hundred metres down, a few drifting cloud sheets, and nothing else in any
# direction. Every sense of *height* the format has came from the fog, which
# is a wash rather than a thing -- there was no object anywhere whose apparent
# size could say how far up you had got.
#
# So the sea has islands and wrecks in it and the air has ruins and airships
# in it, and their whole job is parallax: a sky island you look up at on level
# four, are level with on level twelve and look down on by level twenty is the
# only thing in this scene that says a hundred blocks were climbed. They are
# placed once at scene construction from the run's own seed, they never move
# (except the airships), and they are pure scenery -- nothing collides with
# them and the course does not know they exist, because they stand well
# outside the widest the cone ever gets.
#
# The assets are ``assets/src/props_world.py``. Read its origin conventions
# before changing a ``y`` here: the sea pieces measure from their waterline,
# the two floating ones from their *top* surface, and the waterfall hangs.

#: How far a scenery piece is still drawn. Far past ``FOG_FAR``, because these
#: are forty-metre objects and the point of them is that they are a long way
#: off; the fog tint is what makes the distance read.
SCENERY_FAR = 620.0
#: ...and how far outside the camera's own direction, as a cosine. Wider than
#: ``PROP_AHEAD`` because a big object at the edge of the frame is still most
#: of a second's worth of parallax.
SCENERY_AHEAD = -0.35

#: One entry per kind: how many, the band of radii from the tower's axis, and
#: the band of altitudes. ``sea`` pieces sit on the waterline and are drawn
#: with the sea, under the haze; the rest hang in the air and are drawn with
#: the tower. ``clear`` is how far outside the cone's own rim at that altitude
#: the piece must stand -- a floating island that intersects a terrace reads
#: as a rendering fault, which is the same reasoning ``_spawn_shelf`` uses.
SCENERY = (
    # name          n   radius        altitude        sea   clear  scale
    ("startisle",   1, (125.0, 175.0), (0.0, 0.0),     True,   0.0, 1.00),
    ("seastack",    5, (100.0, 400.0), (0.0, 0.0),     True,   0.0, 1.00),
    ("seaarch",     1, (150.0, 260.0), (0.0, 0.0),     True,   0.0, 1.00),
    ("shipwreck",   2, (95.0, 190.0),  (0.0, 0.0),     True,   0.0, 1.00),
    ("lighthouse",  1, (230.0, 350.0), (0.0, 0.0),     True,   0.0, 1.00),
    ("skyisland",   8, (75.0, 175.0),  (-20.0, 235.0), False, 34.0, 1.00),
    ("skyruin",     6, (95.0, 240.0),  (10.0, 255.0),  False, 44.0, 1.00),
    ("airship",     3, (70.0, 150.0),  (0.0, 225.0),   False, 38.0, 1.00),
)

#: Every kind the scene has to load, plus the waterfall, which is never placed
#: on its own -- it hangs off a sky island's spout.
SCENERY_KINDS = tuple(row[0] for row in SCENERY) + ("waterfall",)

#: Where ``props_world.skyisland`` puts its spout, in the island's own local
#: axes, and the height of the fall. Written down here rather than measured
#: because the model is committed geometry and this is the contract between
#: the two assets.
SPOUT = (8.4, -0.6)

#: How fast an airship travels, in metres a second, and how far round the
#: tower it goes before it turns. Slow: the whole read is "that is under way",
#: and anything quick enough to notice moving is quick enough to notice being
#: on rails.
AIRSHIP_SPEED = 2.6

#: How far the look-at point is pushed *outward*, away from the tower's axis,
#: and how much further down the camera aims than the next landing.
#:
#: Outward, and only just. The ring tower this renderer grew out of pulled its
#: aim *inward*, because there the building was a slim cylinder you ran around
#: the outside of and the subject was the cylinder. Here you are in a trough
#: cut into a solid cone and inboard is a wall, so aiming at it fills the frame
#: with masonry -- measured, half of every frame.
#:
#: But the correction is small, and the first attempt at it was six times this
#: and wrong in the other direction: at -0.16 the camera looked past the rim
#: and every frame was sky and horizon with a strip of ground along the bottom.
#: What actually moved the wall off the frame was widening the band and pulling
#: the *course* outboard (``COURSE_OUT``), not turning the head. The head only
#: has to stop pointing at masonry.
#:
#: The pitch bias is separate, unconditional, and large. The subject of this
#: format is the ground: the terrace you are on, the landings ahead of you, and
#: the drop off the rim beside them. A camera levelled at the next landing
#: spends the run looking at sky, and this strip is 360x640 -- there is a great
#: deal of vertical to waste on it.
AXIS_BIAS = 0.05
#: How much of the head's bearing comes from the trough's own direction rather
#: than from the next few landings, and how far down it that direction is
#: sampled.
#:
#: Without this the camera aims at landings one to three ahead -- eight metres
#: -- and those wander across the band, so on any frame where the next hop goes
#: outboard the head swings out over the rim and the frame is sea and sky. The
#: tower is then never in shot at all, which is the single loudest complaint
#: the previous version of this scene got. A player running a corridor looks
#: *down* it; the corridor here is a helix of radius twenty-odd, so looking
#: down it puts the core wall along the inboard edge of the frame exactly where
#: it belongs and keeps it there.
TANGENT_MIX = 0.45
TANGENT_LOOK = 15.0
PITCH_BIAS = 0.30
#: The ride: how far past the wall the head aims, how far up it, how hard, and
#: how quickly it gets there and back.
#:
#: **A ride looks at the ladder.** This used to swing the aim fourteen metres
#: radially *outward* -- a ninety-degree snap the instant the body grabbed the
#: column, held for the whole ride, and snapped back. It was written to answer
#: a jam metric (42% of climb frames were most-of-the-frame-one-near-surface)
#: and it answered it by turning the camera away from the move, so a climb was
#: eight blocks of blank wall sliding past on one side and empty sky on the
#: other, with the ladder never once in shot. The owner's report is the honest
#: reading of that: *it looks very far to the outside, and it would be better
#: if it looked towards the ladder instead of doing a full ninety-degree
#: switch all of a sudden.*
#:
#: The metric was measuring the wrong thing. Climbing a ladder in the real game
#: *is* a near surface filling most of the frame -- that is what a wall you are
#: two feet from looks like -- and what makes it read as climbing rather than
#: as being stuck is that the rungs are there, moving. So the head turns to the
#: wall the column is bolted to, eased over about a quarter of a second, and
#: the ladder is drawn on that wall's face (:data:`LADDER_HUG`) instead of
#: floating half a block off it.
#:
#: ``RIDE_WALL`` is past the wall rather than at it -- the wall is one cell
#: away, and an aim point *on* it swings wildly as the body drifts within its
#: own cell.
RIDE_WALL = 2.6
RIDE_RISE = 2.2
RIDE_MIX = 0.88
#: ...and how much of the aim comes from along the corridor instead of square
#: at the wall. Aimed dead at it, the ladder plate is 0.42 m from the eye and
#: fills the entire frame with rungs -- which is worse than the ninety-degree
#: swing it replaced, and only the frames say so. A three-quarter view puts the
#: ladder up one side of the frame with the wall it climbs behind it, which is
#: what a climb looks like from behind the shoulder in the real game.
RIDE_SIDE = 0.26
#: ...and how far up the head tilts while riding, in radians, taken over
#: outright: about thirty-six degrees. See the note at the blend.
RIDE_PITCH = -0.62
#: Ease rate for the turn, in units a second: about a quarter of a second in
#: and the same out. Driven by the body's own vertical speed rather than by the
#: phase, so the turn arrives with the grab and leaves with the step-off
#: instead of at a boundary the viewer cannot see.
RIDE_EASE = 4.0

#: How far along the wall's own face a ladder or a vine plate is drawn, from
#: the centre of the cell the body rides in.
#:
#: It was zero: the plate sat in the middle of its cell, half a block clear of
#: the block it is supposed to be nailed to, so a ladder read as a wooden
#: lattice hanging in the air near a wall. In the game a ladder is *on* the
#: face, and the player stands in the cell next to it -- so at 0.42 the body's
#: eye is about half a metre from the rungs, which is the real game's number.
LADDER_HUG = 0.34

#: Head under water: how blue the frame goes at most, and how fast it gets
#: there. A bubble column is a column of *liquid* and the body rides up the
#: inside of it -- so for those two seconds the eye is submerged, and nothing
#: in the frame said so. Tinted toward the liquid's own colour rather than a
#: fixed blue, because the nether family's column is lava.
SUBMERGE_ALPHA = 96
SUBMERGE_EASE = 7.0
#: The furthest *in* the camera's aim point may be, measured from the rim. The
#: outer clamp beside it has always existed; this is the same rule at the other
#: end and it was missing.
#:
#: The aim is the weighted next few landings, so wherever the course hugs the
#: core the camera is aimed at the core -- and the course hugs it for the whole
#: exit climb, a third of every run. Measured by segment, masonry filled the
#: lens on 10% of climb frames and 0% of every designed beat: one arrangement
#: the aim had no answer for, not a constant that was wrong everywhere. Swept:
#: 3.5 halves it and 2.5 buys almost nothing more while pushing the aim toward
#: the rim, which is the failure at the other end of this axis (see
#: ``AXIS_BIAS`` -- at -0.16 every frame was sky and horizon).
AIM_INSET = 3.5

ORB_SCALE = 0.24
ORB_COLOR = (120, 240, 190)
PICKUP_REACH = 0.85
COMBO_HOLD = 1.8
POP_IN = 0.28
STRIDE_RATE = 2.9
#: Chunks meshed per frame, and structure cells copied into the volume per
#: frame. Both are budgets rather than limits: generation runs far enough ahead
#: that nothing is ever wanted on the frame it is made, so the only thing these
#: buy is that no single frame pays for a whole floor at once.
CHUNK_BUDGET = 2
#: Chunks meshed during scene construction. See ``_pump``.
PRIME_CHUNKS = 190
WRITE_BUDGET = 900


@register("spiral")
class SpiralScene(Scene):
    #: The module that owns the building and the course. Everything below this
    #: line is a *renderer* -- meshing, the body, the camera, the weather --
    #: and none of it knows what shape the building is; the spiral scene is
    #: this class against :mod:`brainrot.scenes.spiralplan` instead, and the
    #: only thing it has to say for itself is which way "indoors" is.
    plan = sp
    #: How far under the body the world is kept. A ring tower is a few
    #: metres across and its whole silhouette is what is directly below you;
    #: a spiral of platforms is seventy metres across, so the same depth is
    #: several times as many chunks and most of them are behind a platform.
    below = BELOW

    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        pal = ctx.palette
        seed = ctx.seed
        self.sky = SkyDome(pal, seed, ctx.width, ctx.height)
        self.weather = Weather(pal, ctx.width, ctx.height, seed.root & 0xFFFF)
        self.burst = Burst()
        self.camera = rl.make_camera(FOV)
        self.detail = {"high": 1.0, "balanced": 0.7, "low": 0.45}.get(ctx.quality, 1.0)
        self._glows: list[tuple[float, float, float, float, rl.RGB, int]] = []

        self.recipe = _recipes(pal, seed.run)
        self.atlas = chunk.BlockAtlas(f"run{seed.run}-spiral",
                                      [(n, k) for n, k in self.recipe.items()],
                                      see_through=tp.SEE_THROUGH)
        self.volume = chunk.ChunkedVolume(self.atlas)

        self.cone = self.plan.Cone(ctx.stream("cone"), 0)
        self.course = self.plan.Course(ctx.stream("course"), self.cone,
                                       hop_rng=ctx.stream("hops"))
        self.hop_rng = ctx.stream("hops2")
        self._written = 0

        self.deep = rl.mix_rgb(rl.mix_rgb(pal.sky_bottom, (10, 46, 96), 0.74),
                               pal.fog, 0.10)
        # Sub-block furniture. A terrace reads as a *place* because of the
        # parts of Minecraft that are not cubes -- grass, crops, fences, vines,
        # rails -- and as cells those all come out as the same coloured box.
        self.props = {name: assets.load(name)
                      for name in self.plan.PROP_KINDS}
        for model in self.props.values():
            model.recolor({
                "leaf": rl.mix_rgb(pal.accent, (110, 160, 60), 0.55),
                "stem": rl.mix_rgb(pal.accent, (80, 120, 50), 0.66),
                "wood": rl.mix_rgb(pal.structure, (120, 84, 46), 0.5),
                "metal": rl.mix_rgb(pal.structure, (86, 88, 96), 0.55),
                "glow": pal.window_lit,
            })
        # The far world. Loaded apart from ``props`` because these are not
        # furniture: they are drawn at hundreds of metres with their own fog
        # and their own culling, and none of them is ever placed on a landing.
        self.scene_props = {name: assets.load(name)
                            for name in SCENERY_KINDS}
        for model in self.scene_props.values():
            model.recolor({
                "leaf": rl.mix_rgb(pal.accent, (110, 160, 60), 0.55),
                "wood": rl.mix_rgb(pal.structure, (120, 84, 46), 0.5),
                "metal": rl.mix_rgb(pal.structure, (86, 88, 96), 0.55),
                "glow": pal.window_lit,
            })
        self.kit = _choose_kit(ctx.stream("kit"))
        self.swing = 0.0
        self.mine = 0.0

        # -- the body ------------------------------------------------------
        self.index = 0
        self.landings = 0
        self.phase = "ground"
        self.phase_t = 0.0
        blk = self.course.blocks[0]
        self.pos = list(self.course.land_point(blk))
        self.stand = list(self.pos)
        self.move: tp.Move | None = None
        self.vy = 0.0
        self.stride = 0.0
        self.climbed = 0.0
        self.base_y = blk["y"]
        #: The eye's own suspension: how far below its resting place it is, and
        #: how fast it is getting there. See :data:`DIP_W`.
        self.dip = 0.0
        self.dip_v = 0.0
        self._pace = tp.RUN_SPEED
        #: Height of the surface last landed on -- see ``_land``. Initialised
        #: here because ``_look`` reads it on the first frame.
        self.land_y = self.pos[1]
        #: How much of the walk bob is showing, 0..1. Eased, never switched.
        self.foot = 1.0
        #: Field of view, eased toward what the speed asks for.
        self.fov = FOV
        #: Ground speed this frame, which is what the lens is hung off.
        self.speed = 0.0
        self.run_s = 0.0
        self.yaw = 0.0
        self.pitch = 0.10
        self._flick = 0.0
        self._roll = 0.0
        #: How much of the ride camera is showing, 0..1, eased. See
        #: :data:`RIDE_EASE`; it is also what tells the pitch to measure from
        #: the body rather than from the surface the feet left.
        self.ride = 0.0
        #: ...and how much of the frame is under the liquid of a bubble
        #: column, with the colour to wash it toward.
        self.submerged = 0.0
        self.submerged_rgb = (60, 130, 210)
        #: The cell the head is in, refreshed once a frame by ``_draw_course``
        #: and read by ``_draw_furniture``. Seeded here because a scene may be
        #: asked to draw before it has ever updated.
        self._eye_cell = (0, 0, 0)
        self._begin_ground()
        self.yaw = math.atan2(blk["step"][0], -blk["step"][1])

        # -- scoring -------------------------------------------------------
        self.orbs = 0
        self.orbs_missed = 0
        self.combo = 0
        self.combo_t = 0.0
        # From where the *body* is, not from where generation has got to. The
        # frontier runs sixteen landings ahead, so seeding this from it labels
        # the first two sections of every run with the name of a place the
        # viewer will not reach for ten seconds.
        self.tier = self.cone.section_at(
            self.cone.unwrap(self.pos[0], self.pos[2], self.pos[1])).index
        self.ring = self.theme_here().name
        self.ring_flash = 0.0
        self.ring_light = (255, 255, 255)
        #: 0 outside the wall, 1 well inside it, eased. Drives how dark the
        #: world goes and how hard the building's own lamps read -- which is
        #: the whole difference between "a room" and "the same course with a
        #: wall round it".
        self.indoor = 0.0

        # -- weather below -------------------------------------------------
        # Cloud shelves at absolute altitudes, so the climb goes *through*
        # them. Nothing else in the scene says "you are two hundred blocks up"
        # as cheaply as a sheet of cloud passing the camera going down.
        crng = ctx.stream("shelves")
        self.shelves: list[dict] = []
        self._next_shelf = blk["y"] - 30.0
        for _ in range(int(10 * self.detail) or 5):
            self._spawn_shelf(crng)
        self.crng = crng
        self.cloud_tint = rl.mix_rgb(pal.sky_bottom, (255, 255, 255), 0.6)
        self._place_scenery(ctx.stream("scenery"))
        self._pump(prime=True)

    # -- materials ---------------------------------------------------------

    def _model(self, name: str):
        """The single-cube model for a style, built on first use.

        Lazily, because the atlas already holds all fifty materials and only
        the dozen or so a run's rings actually reach need a model of their own.
        The rest never cost a texture.
        """
        return voxel.block_model(f"run{self.ctx.seed.run}-{name}",
                                 **self.recipe[name])

    def _colour(self, name: str) -> rl.RGB:
        return self.recipe[name]["base"]

    def _style_of(self, blk: dict) -> str:
        """What a block is made of. A ``floor`` landing has no material of its
        own -- it is standing on the building -- so it borrows the ring's."""
        return blk["style"] or self.plan.THEME_BY_NAME[blk["theme"]].sub

    # -- world streaming ---------------------------------------------------

    def theme_here(self) -> sp.Theme:
        """The section the body is standing in.

        Resolved from a *point* and not from a height, and that is not a
        detail: one revolution of this tower holds three or four sections, so
        a height alone cannot tell a nether band from the farm directly above
        it.
        """
        return self.cone.theme_at(self.pos[1], self.pos[0], self.pos[2])

    def _pump(self, prime: bool = False) -> None:
        """Move generated structure into the renderer, a budget at a time."""
        floor_y = int(self.pos[1]) - self.below
        self.course.build_world(floor_y, int(self.pos[1]) + ABOVE,
                                int(self.pos[1]))
        writes = self.course.writes
        budget = len(writes) if prime else WRITE_BUDGET
        if writes:
            take = writes[:budget]
            del writes[:budget]
            floor = int(self.pos[1]) - self.below
            for cell, style in take:
                if cell[1] < floor:
                    continue
                if style == "air":
                    # A pond, a lava channel: dug out of the terrace rather
                    # than laid on top of it.
                    self.volume.clear(cell)
                else:
                    self.volume.set(cell, style)
            self._written += len(take)
        # The priming pass meshes enough to fill the frame and no more.
        #
        # It cannot simply mesh everything: ``_begin_scene`` runs at the moment
        # the strip becomes visible, so every millisecond here is a millisecond
        # the strip is late and the event loop is deaf. Meshing the lot took
        # scene construction from 1.1 s to 1.6 s. What makes a bounded prime
        # enough is that the cone is now emitted outward from the body rather
        # than upward from the bottom, so these are the chunks in shot.
        self.volume.build_pending(PRIME_CHUNKS if prime else CHUNK_BUDGET)

    def _place_scenery(self, rng) -> None:
        """Stand the islands, wrecks and ruins up, once, for this run.

        Placed rather than spawned: a cloud shelf streams past and is gone, but
        these are the landmarks the climb is measured against, so the one on
        the horizon at the start of a run has to be the same one still on the
        horizon four minutes later. Nothing here is ever re-rolled or moved --
        an airship is translated along a fixed bearing and that is the only
        motion in the list.

        Bearings are spread round the tower rather than drawn freely: a run
        covers about a revolution a minute, so four pieces that happen to land
        on the same bearing are four pieces you see at once and then nothing
        for a minute. Each kind gets its own even spread with a jitter inside
        it, which is what a scatter looks like when it is not clumped.
        """
        self.scenery: list[dict] = []
        for name, count, (r0, r1), (y0, y1), sea, clear, scale in SCENERY:
            for i in range(count):
                # An even spread with a jitter, per kind and per index.
                base = (i + rng.random() * 0.7) / count * math.tau
                ang = base + rng.uniform(0.0, 0.4)
                y = SEA_Y if sea else rng.uniform(y0, y1)
                r = rng.uniform(r0, r1)
                if not sea:
                    r = max(r, self.cone.rim_at(y) + clear)
                piece = {
                    "kind": name, "s": scale,
                    "x": math.cos(ang) * r, "z": math.sin(ang) * r, "y": y,
                    "yaw": rng.uniform(0.0, math.tau),
                    # Only the airships have one, and it is a bearing rather
                    # than a heading: they orbit, so the model's own yaw and
                    # the direction it travels stay consistent for free.
                    "orbit": (AIRSHIP_SPEED / max(1.0, r)
                              * (1 if rng.random() < 0.5 else -1)
                              if name == "airship" else 0.0),
                    "ang": ang, "r": r,
                }
                self.scenery.append(piece)
                if name == "skyisland":
                    # Hung off the island's own spout, in the island's local
                    # axes turned by its yaw. A waterfall placed anywhere else
                    # pours out of thin air beside it.
                    ox = SPOUT[0] * math.cos(piece["yaw"])
                    oz = -SPOUT[0] * math.sin(piece["yaw"])
                    self.scenery.append({
                        "kind": "waterfall", "s": scale,
                        "x": piece["x"] + ox, "z": piece["z"] + oz,
                        "y": y + SPOUT[1], "yaw": piece["yaw"],
                        "orbit": 0.0, "ang": ang, "r": r,
                    })

    def _draw_scenery(self, sea: bool) -> None:
        """The far world: everything in the water, or everything in the air.

        Split because the two halves belong on opposite sides of the haze band.
        The sea and what floats on it are washed by it -- that band *is* the
        hundred metres of air between the body and the water. What hangs in the
        sky is at the body's own altitude and must not be, or a floating island
        level with the runner comes out paler than the terrace next to it.
        """
        cam = self.camera[0]
        eye = (cam.position.x, cam.position.y, cam.position.z)
        fx = cam.target.x - eye[0]
        fy = cam.target.y - eye[1]
        fz = cam.target.z - eye[2]
        n = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / n, fy / n, fz / n
        sky = self.palette.sky_bottom
        for piece in self.scenery:
            if (piece["y"] <= SEA_Y) != sea:
                continue
            x, y, z = piece["x"], piece["y"], piece["z"]
            dx, dy, dz = x - eye[0], y - eye[1], z - eye[2]
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > SCENERY_FAR * SCENERY_FAR:
                continue
            dist = math.sqrt(d2)
            if dx * fx + dy * fy + dz * fz < SCENERY_AHEAD * dist:
                continue
            model = self.scene_props.get(piece["kind"])
            if model is None:
                continue
            # Aerial perspective, and further than the course's own fog goes:
            # ``_fog`` saturates at 110 m, which is nothing to something four
            # hundred metres away, so the tint keeps going toward the sky's
            # own colour and the horizon pieces end up as silhouettes.
            far = min(1.0, dist / SCENERY_FAR) ** 0.7
            tint = rl.mix_rgb(
                rl.mix_rgb((255, 255, 255),
                           rl.mix_rgb(self.ring_light, self.palette.fog, 0.35),
                           min(1.0, dist / FOG_FAR) ** 0.85 * 0.5),
                sky, far * 0.72)
            rl.DrawModelEx(model.model, (x, y, z), (0, 1, 0),
                           math.degrees(piece["yaw"]), (piece["s"],) * 3,
                           rl.rgba(tint, 255))

    def _spawn_shelf(self, rng) -> None:
        y = self._next_shelf + rng.uniform(18, 46)
        self._next_shelf = y
        # Clear of the tower. A shelf is sized 55-120 and drifts, so one
        # spawned over the footprint slides across a terrace as a translucent
        # sheet at ankle height -- which is what it looks like: a rendering
        # fault, not weather. Ringing them around the building keeps the
        # climb-past-the-cloud-layer read without ever putting one indoors.
        keep_out = self.cone.rim_at(y) + 85.0
        for _ in range(8):
            x, z = rng.uniform(-260, 260), rng.uniform(-260, 260)
            if math.hypot(x, z) > keep_out:
                break
        else:
            ang = rng.uniform(0, 6.283)
            x, z = math.cos(ang) * (keep_out + 40), math.sin(ang) * (keep_out + 40)
        self.shelves.append({
            "tex": cloud_blob(int(y) * 31 + 7, 160),
            "x": x, "z": z,
            "y": y, "s": rng.uniform(55, 120), "drift": rng.uniform(0.3, 1.1),
            "phase": rng.uniform(0, 6.283),
        })

    # -- simulation --------------------------------------------------------

    def _block(self) -> dict:
        return self.course.blocks[self.index]

    def _indoor_want(self) -> float:
        """1 when the body is under a roof, 0 when it is under the sky.

        Two answers, and the larger wins. The theme's own darkness is the old
        one: a deep-dark or a mine section is a cave with the roof taken off,
        and it has to *read* as one or fifteen themes become fifteen shades
        of daylight. The new one is literal: the shells build real roofs now,
        so ask whether there is one overhead. Sampled once a frame over the
        body -- the analytic rock test plus the course's own solids, both
        cheap -- and eased by the caller like every exposure change.
        """
        x, z = tp.iround(self.pos[0]), tp.iround(self.pos[2])
        y = tp.ifloor(self.pos[1])
        roofed = any(self.course.blocked((x, y + h, z)) for h in range(3, 9))
        return max(self.theme_here().dark, 0.85 if roofed else 0.0)

    def _begin_ground(self) -> None:
        """Set up the run across the block just landed on.

        The feet keep going: the landing was on the near edge, the take-off is
        from the far one, and the time between them is not a number anybody
        chose -- it is that distance at whatever pace the block's material
        allows. Soul sand takes twice as long as stone to cross and ice half,
        and that one number is most of what makes a ring feel like what it is
        made of.

        And the pace is a *profile* between the two moves either side of it,
        not a constant for the length of the block. Set as a constant, the
        crossing began and ended with the body's speed jumping by a metre and
        a half a second in one frame -- more for a web or a ladder, which it
        used to arrive at and leave from as if teleported. :class:`GroundRun`
        brakes as hard as the ground allows, spends whatever room is left at
        the material's own speed, and is back up to the next move's speed by
        the far edge; on a one-cell landing there is no room, so the body
        simply runs over it, which is what a player chaining jumps does.
        """
        blk = self._block()
        self.run_from = list(self.course.land_point(blk))
        self.run_to = list(self.course.takeoff_point(blk))
        self.run_len = math.dist((self.run_from[0], self.run_from[2]),
                                 (self.run_to[0], self.run_to[2]))
        self.run_s = 0.0
        self.ground_speed = self.course.ground_speed(blk)
        out = blk["move"]
        if out is None:
            self.course.spawn()
            out = blk["move"]
        self.run = tp.GroundRun(
            self.run_len,
            self.move.speed_out() if self.move is not None else self.ground_speed,
            out.speed_in() if out is not None else tp.AIR_SPEED,
            self.ground_speed)
        self.ground_dur = max(0.05, self.run.dur)
        self.phase = "ground"
        self.phase_t = 0.0
        self.pos = list(self.run_from)

    def _begin_move(self) -> None:
        blk = self._block()
        self.move = blk["move"]
        if self.move is None:
            self.course.spawn()
            self.move = blk["move"]
        self.phase = "move"
        self.phase_t = 0.0
        self._flick = 1.0
        if self.move.kind in ("hop", "slide", "bounce") \
                and self.hop_rng.random() < 0.3:
            self.mine = 1.0

    def _land(self) -> None:
        self.index += 1
        #: Only ever up, unlike ``index``, which is walked back as the course
        #: drops blocks off its tail. Probes segment hops by this.
        self.landings += 1
        blk = self._block()
        self.pos = list(self.course.land_point(blk))
        #: Height of the surface just landed on -- see the flat scene's.
        self.land_y = self.pos[1]
        # The eye carries the body's downward speed into the legs rather than
        # being dropped a fixed distance in one frame.
        # Only the part of the impact that is more than an ordinary jump
        # arrives with -- see the flat scene's ``DIP_FREE``. A hop lands at
        # about the speed it left at, so measured off the raw speed this fired
        # on every landing, twice a second, on a camera vanilla holds still.
        self.dip_v = max(self.dip_v, DIP_KEEP * (
            DIP_BASE + min(DIP_CAP, max(0.0, abs(self.vy) - DIP_FREE))))
        self.swing = 1.0
        self.burst.spawn(self.pos[0], self.pos[1] - 0.1, self.pos[2],
                         self._colour(self._style_of(blk)),
                         count=6, speed=1.5, rng=self.hop_rng)
        # The ring the body is *on*, and it only ever goes up. A course that
        # steps down over a floor boundary and back up would otherwise flip the
        # theme twice in a second, which measured as rings lasting half a
        # second and reads on screen as the whole tower blinking.
        tier = self.cone.section_at(
            self.cone.unwrap(blk["x"], blk["z"], blk["y"] + 1)).index
        # Strictly increasing. The body's bearing wobbles by a cell or two
        # inside a landing, and a section boundary it happens to straddle then
        # flickers -- measured, that reported sections lasting under a second
        # when the shortest a body can actually cross is five.
        if tier > self.tier:
            self.tier = tier
            # The landing's own theme, not the body's. The body is still on
            # the previous section at the moment its next landing crosses into
            # a new one, so asking where the *body* is names the section it is
            # leaving and then corrects itself a moment later -- which the
            # probe saw as themed sections lasting under a second.
            name = blk["theme"]
            if name != self.ring:
                self.ring = name
                self.ring_flash = 1.0
        # Keep the horizon of generated course ahead of the body, then let go
        # of what is behind it -- cells and chunks both. An occupancy map that
        # only grew would refuse the whole tower within a couple of hundred
        # blocks, and this course comes back over itself every revolution.
        while len(self.course.blocks) - self.index < self.plan.AHEAD:
            self.course.spawn()["born"] = self.elapsed
        dropped = self.course.advance(self.index)
        if dropped:
            self.index -= dropped
        floor = int(self.pos[1]) - self.below
        self.volume.drop_below(floor)
        if len(self.cone.lamps) > 60:
            self.cone.lamps = [c for c in self.cone.lamps if c[1] >= floor]
        self._begin_ground()

    def _step_ground(self, dt: float) -> float:
        """Run some of the way across the block. Returns the time it took."""
        remain = self.run_len - self.run_s
        if remain <= 1e-6:
            self._begin_move()
            return 0.0
        v = self.run.speed_at(self.run_s)
        step = v * dt
        used = dt
        if step >= remain:
            # Only the time that actually crossed the block is spent here. The
            # rest of the frame belongs to the flight, and handing it back is
            # the difference between a take-off and a fraction of a frame
            # standing on the far edge at nothing much a second.
            used = min(dt, remain / v)
            step = remain
        self.run_s += step
        f = self.run_s / self.run_len
        self.pos = [self.run_from[i] + (self.run_to[i] - self.run_from[i]) * f
                    for i in range(3)]
        self.stride += step
        self.vy = 0.0
        self.phase_t += used
        if self.run_s >= self.run_len - 1e-9:
            self._begin_move()
        return used

    def _step_move(self, dt: float) -> float:
        """Fly, climb or ride some of the move. Returns the time it took."""
        move = self.move
        remain = move.dur - self.phase_t
        if remain <= 1e-9:
            self._land()
            return 0.0
        used = min(dt, remain)
        was = self.pos[1]
        self.phase_t += used
        self.pos = list(move.at(self.phase_t))
        self.vy = (self.pos[1] - was) / max(1e-5, used)
        if move.kind in ("climb", "bubble", "web"):
            self.stride += 0.4 * used
        if self.phase_t >= move.dur - 1e-9:
            self._land()
        return used

    def update(self, dt: float) -> None:
        self.elapsed += dt
        was = (self.pos[0], self.pos[2])
        # A frame is spent across as many phases as it reaches into. A landing
        # or a take-off almost never falls on a frame boundary, and the old
        # loop threw whatever was left of the frame away at every one of them.
        left = dt
        for _ in range(8):
            if left <= 1e-9:
                break
            left -= (self._step_ground(left) if self.phase == "ground"
                     else self._step_move(left))
        self.speed = math.dist(was, (self.pos[0], self.pos[2])) / dt \
            if dt > 0.0 else 0.0
        self.climbed = self.pos[1] - self.base_y
        want = self._indoor_want()
        # Eased over about a third of a second, because the transition happens
        # in one stride through an archway and a step change in the whole
        # frame's exposure reads as a rendering fault rather than as going
        # indoors.
        self.indoor += (want - self.indoor) * min(1.0, dt * 3.2)
        # Head under water. A bubble column is a column of liquid and the body
        # rides up the *inside* of it, so for those two seconds the eye is
        # submerged -- and until now the only thing that said so was the
        # translucent cell you were in the middle of, which from the inside is
        # nearly nothing. Eased, because a whole-frame colour switched at a
        # phase boundary reads as a rendering fault.
        ride = self._ride_face()
        under = 0.0
        if ride is not None and self.move.kind == "bubble" \
                and ride[1] in _TRANSLUCENT and self.vy > 0.4:
            under = 1.0
            self.submerged_rgb = self._colour(ride[1])
        self.submerged += (under - self.submerged) * min(1.0, dt * SUBMERGE_EASE)
        self._settle(dt)
        self.swing = max(0.0, self.swing - dt * 3.0)
        self.mine = max(0.0, self.mine - dt * 3.2)
        self.ring_flash = max(0.0, self.ring_flash - dt * 0.5)
        self.combo_t = max(0.0, self.combo_t - dt)
        if self.combo_t <= 0.0:
            self.combo = 0
        self.burst.update(dt)
        self._collect()
        self._look(dt)
        self._pump()
        for shelf in self.shelves:
            shelf["x"] += math.cos(shelf["phase"]) * shelf["drift"] * dt
            shelf["z"] += math.sin(shelf["phase"]) * shelf["drift"] * dt
        while self._next_shelf < self.pos[1] + 120:
            self._spawn_shelf(self.crng)
        if self.shelves and self.shelves[0]["y"] < self.pos[1] - 90:
            self.shelves.pop(0)
        for piece in self.scenery:
            if not piece["orbit"]:
                continue
            # Round the tower rather than across the frame, so the model's
            # nose keeps pointing the way it is going without a second angle
            # to keep in step.
            piece["ang"] += piece["orbit"] * dt
            piece["x"] = math.cos(piece["ang"]) * piece["r"]
            piece["z"] = math.sin(piece["ang"]) * piece["r"]
            piece["yaw"] += piece["orbit"] * dt

    def body_box(self) -> AABB:
        return AABB.around(self.pos[0], self.pos[1], self.pos[2],
                           tp.BODY_HALF_W, tp.BODY_H, tp.BODY_HALF_W)

    def orb_hover(self) -> float:
        return math.sin(self.elapsed * 3.4) * 0.08

    def _collect(self) -> None:
        body = self.body_box().grown(PICKUP_REACH, PICKUP_REACH, PICKUP_REACH)
        hover = self.orb_hover()
        for blk in self.course.blocks[max(0, self.index - 1):self.index + 3]:
            for orb in blk["orbs"]:
                if orb["taken"]:
                    continue
                if body.overlaps(AABB.around(orb["x"], orb["y"] + hover,
                                             orb["z"], ORB_SCALE * 0.5,
                                             ORB_SCALE, ORB_SCALE * 0.5)):
                    orb["taken"] = True
                    self.orbs += 1
                    self.combo += 1
                    self.combo_t = COMBO_HOLD
                    self.burst.spawn(orb["x"], orb["y"], orb["z"], ORB_COLOR,
                                     count=8, speed=2.2, rng=self.hop_rng)

    # -- camera ------------------------------------------------------------

    def _ride_face(self):
        """The wall this ride is bolted to, as ``((ax, az), style)``, or None.

        Worked out when the move was solved and carried on the *landing's* soft
        cells -- the column belongs to the block being climbed to, not to the
        one being left -- because at draw time the only honest answer would be
        a cube. :meth:`spiralplan.Course._climb_move` is where it is chosen: it
        is the first of the four horizontal neighbours with solid rock or
        pedestal beside the column's middle and its top, which is the thing a
        ladder in this world can actually hang on.
        """
        if self.phase != "move" or self.move is None:
            return None
        if self.move.kind not in ("climb", "bubble"):
            return None
        last = len(self.course.blocks) - 1
        nxt = self.course.blocks[min(self.index + 1, last)]
        for s in nxt["soft"]:
            if s.get("face"):
                return s["face"], s["style"]
        return None

    def _look(self, dt: float) -> None:
        """Turn the head toward where the climb is going.

        In ``update`` and not in ``draw``, so that drawing a frame twice draws
        the same frame twice -- every screenshot this scene is judged from is
        captured by presenting a frame a second time.

        The profile is a *flick*: a player commits to the next move as their
        feet leave the ground, snaps the view onto it, and then holds still.
        A constant ease is a camera on rails, and reads as one.
        """
        x, z = self.pos[0], self.pos[2]
        last = len(self.course.blocks) - 1
        ahead = [(self.course.blocks[min(self.index + n, last)], w)
                 for n, w in ((1, 0.46), (2, 0.30), (3, 0.24))]
        aim = [sum(b["x"] * w for b, w in ahead),
               sum(self.course.surface(b) * w for b, w in ahead),
               sum(b["z"] * w for b, w in ahead)]
        # How hard the head is locked onto the landing it is actually jumping
        # to. A player looks down the corridor while crossing a block and
        # snaps onto the landing as they commit; the old blend never exceeded
        # half a weight on the next landing, so at take-off the block the body
        # was flying at was routinely off-centre -- read from outside as the
        # character not looking where it is jumping, which is what it was.
        # Ramps up through the run across the block and holds through the
        # flight; climbs and bubble rides keep the corridor view (their look
        # is the pitch override below).
        nxt = self.course.blocks[min(self.index + 1, last)]
        if self.phase == "move" and self.move.kind not in ("climb", "bubble"):
            lock = 1.0
        elif self.phase == "ground":
            lock = min(1.0, self.phase_t / max(1e-5, self.ground_dur)) * 0.85
        else:
            lock = 0.0
        target = self.course.land_point(nxt)
        # ...and a quarter of the way back toward the axis. Looking straight
        # along a helix points the camera tangentially, which puts the tower
        # off the side of a portrait strip and fills the frame with sky: the
        # course is what you are following, but the *building* is the subject.
        # A player hugging a wall looks along it, not past it.
        # Down the trough, not at the next block.
        u = self.cone.unwrap(x, z, self.pos[1])
        th = u * self.cone.wind
        tx = -math.sin(th) * self.cone.wind
        tz = math.cos(th) * self.cone.wind
        aim[0] += (x + tx * TANGENT_LOOK - aim[0]) * TANGENT_MIX
        aim[2] += (z + tz * TANGENT_LOOK - aim[2]) * TANGENT_MIX
        aim[0] *= 1.0 - AXIS_BIAS
        aim[2] *= 1.0 - AXIS_BIAS
        # ...and never further out than the rim, or the camera swings off the
        # tower altogether on the frames where the next landing is already
        # near the edge.
        # +6.5 and not +3: landings may now stand well past the rim on spurs
        # and piers, and an aim clamped to the old silhouette turned the head
        # away from exactly the landings that are the most worth watching.
        far = self.cone.outer_at(self.course.u) + 6.5
        flat_r = math.hypot(aim[0], aim[2])
        if flat_r > far:
            aim[0] *= far / flat_r
            aim[2] *= far / flat_r
        # ...and never further *in* than a few metres off the core, which is
        # the same rule at the other end and was missing.
        #
        # The aim is the weighted next few landings, so wherever the course
        # hugs the wall the camera is aimed at the wall -- and the course hugs
        # the wall for the whole exit climb, which is over a third of a run.
        # Measured by segment, the lens was filled by masonry on 10% of climb
        # frames and on **0%** of every designed beat in the tower; that is not
        # a camera constant being wrong everywhere, it is one arrangement the
        # aim had no answer for. Pushing the aim point out to the middle of the
        # band leaves the wall where a wall belongs, along the inboard edge of
        # the frame, without turning the head off the course.
        near = self.cone.outer_at(self.course.u) - AIM_INSET
        if flat_r < near:
            aim[0] *= near / max(1e-6, flat_r)
            aim[2] *= near / max(1e-6, flat_r)
        # The glance: while running -- never in flight -- the head leans
        # toward the level's own landmark when it stands roughly ahead and
        # near. Structures placed and never framed may as well not exist,
        # which is exactly what the owner reported after watching five
        # minutes of strip: the aim rode the landings and the tangent, and
        # a windmill on the apron went by in the blind spot every time.
        if self.phase == "ground" and lock < 0.7:
            for ti in (self.tier, self.tier + 1):
                mark = self.cone.marks.get(ti)
                if mark is None:
                    continue
                mx, my, mz = mark
                dist = math.hypot(mx - x, mz - z)
                if not 4.0 < dist < 24.0:
                    continue
                want_yaw = math.atan2(mx - x, -(mz - z))
                if abs(_wrap(want_yaw - self.yaw)) > 0.75:
                    continue
                g = 0.35 * (1.0 - lock)
                aim[0] += (mx - aim[0]) * g
                aim[1] += (my - aim[1]) * g
                aim[2] += (mz - aim[2]) * g
                break
        # The lock happens *after* the tangent pull and both radial clamps:
        # they are corridor framing, and the landing is the course itself --
        # clamping the head off the block it is jumping to is how the old
        # camera lost it.
        if lock > 0.0:
            aim[0] += (target[0] - aim[0]) * lock
            aim[1] += (target[1] - aim[1]) * lock
            aim[2] += (target[2] - aim[2]) * lock
        # **A ride looks out, not at the wall it is hanging on.** A ladder or a
        # bubble column has to anchor on the core, so the body spends the whole
        # ride with its face against the one surface in the scene it cannot see
        # past. Measured over six runs of the tower: 42% of climb frames and
        # 30% of bubble frames were most-of-the-frame-one-near-surface, against
        # 1.0% of hops -- three quarters of every jammed frame in the run, and
        # the longest-standing visual complaint the project has. The pitch
        # already tilts up for the view; the yaw was still aimed at the rungs.
        ride = self._ride_face()
        # Driven by the body's own vertical speed, not by the phase: a ride is
        # three legs -- a hop onto the column, the climb, a step off -- and
        # only the middle one is the thing the camera turns for. Keyed to the
        # phase, the turn began before the hands were on the ladder and let go
        # before the feet were off it.
        want_ride = 1.0 if (ride is not None and self.vy > 0.4) else 0.0
        self.ride += (want_ride - self.ride) * min(1.0, dt * RIDE_EASE)
        if self.ride > 0.01 and ride is not None:
            ax, az = ride[0]
            # Square at the wall, then swung along the corridor: see
            # ``RIDE_SIDE``. The tangent is the one already computed for the
            # corridor pull, and its sign is chosen so the swing is *forward*
            # -- swung backwards the climb is spent looking at where you came
            # from, which is the same defect as before with a different angle.
            sx, sz = tx, tz
            if sx * ax + sz * az > 0.0:
                sx, sz = -sx, -sz
            px = ax * (1.0 - RIDE_SIDE) + sx * RIDE_SIDE
            pz = az * (1.0 - RIDE_SIDE) + sz * RIDE_SIDE
            n = math.hypot(px, pz) or 1.0
            g = self.ride * RIDE_MIX
            aim[0] += (x + px / n * RIDE_WALL - aim[0]) * g
            aim[1] += (self.pos[1] + RIDE_RISE - aim[1]) * g
            aim[2] += (z + pz / n * RIDE_WALL - aim[2]) * g

        # The flick, and it is half what it was. A landing here is a tenth of
        # a second and the next move begins straight out of it, so at 22 the
        # head snapped onto the next block within four frames of the feet
        # touching down -- four times a second, which reads as an agitated
        # player rather than a decisive one. Softer and decaying more slowly
        # is still a flick and not a drift: the turn is committed at take-off
        # and mostly done a third of a second later.
        self._flick = max(0.0, self._flick - dt * 4.0)
        rate = min(1.0, (5.0 + 10.0 * self._flick ** 2) * dt)
        self.yaw += _wrap(math.atan2(aim[0] - x, -(aim[2] - z)) - self.yaw) * rate

        flat = math.hypot(aim[0] - x, aim[2] - z)
        # From the surface the feet left rather than from the body: measured
        # off the arc, the wanted pitch swings against the jump and the world
        # pitches about twice as far as the body does. See the flat scene's
        # ``_look`` for the whole of it.
        # ...except on a ride, where the surface the feet left is at the bottom
        # of the climb and gets further away every frame: measured from it, the
        # pitch winds steadily further up the longer the ladder is, and an
        # eight-block column ends with the camera looking at the sky. A
        # climbing body's reference is the body.
        from_y = self.pos[1] if self.ride > 0.01 else self.land_y
        want = math.atan2(from_y + tp.EYE - (aim[1] + tp.EYE * 0.95),
                          max(3.2, flat))
        # Riding something looks *up* it. A ladder or a bubble column is the
        # one moment in the run with time to spare, and spending it looking at
        # the rungs is the difference between a lift and a climb.
        if self.ride > 0.01:
            # Taken over outright rather than nudged, and it replaces
            # ``PITCH_BIAS`` too. The eye is half a metre from a wall, so the
            # only thing a level camera can frame is that wall -- measured off
            # the frames, two thirds of a ladder ride was one flat untextured
            # face with the rungs off the top edge. Pitched up, the plate the
            # body is holding sits along the bottom of the frame where a pair
            # of hands would be and the ladder runs away up the middle of it,
            # which is what climbing one looks like.
            want += (RIDE_PITCH - PITCH_BIAS - want) * self.ride
        elif self.phase == "move" and self.move.kind in ("climb", "bubble"):
            want -= 0.42
        else:
            # Gently: a jump swings ``vy`` from +8.4 to -8.4, so at the 0.028
            # this used to be the view pitched twenty-five degrees over every
            # hop, on top of the body's own rise, twice a second. Vanilla does
            # not move the view when you jump at all.
            want -= max(-0.09, min(0.12, self.vy * 0.012))
        # And a touch further down than the next landing, always. The drop is
        # the entire point of a tower and it is underneath you; a camera
        # levelled at the next block spends the run looking at sky.
        want += PITCH_BIAS
        # And the head is nearly still while the feet are off the ground on a
        # *ballistic* move. The aim is a landing a few metres away and the eye
        # rises over a metre above it, so chasing it mid-flight pitches the
        # view down on the way up and back up on the way down -- against the
        # body, so the world swings about twice as far as the jump does. A
        # climb or a bubble ride is exempt: those are seconds long, the body
        # is pinned to the wall, and the camera has real work to do (see
        # ``RIDE_OUT``).
        self.pitch += _wrap(max(-0.62, min(0.62, want)) - self.pitch) * rate * 0.8

        roll = math.sin(self.stride * STRIDE_RATE) * 0.035 \
            if self.phase == "ground" else 0.0
        self._roll += (roll - self._roll) * min(1.0, dt * 9.0)

    def _settle(self, dt: float) -> None:
        """Advance everything the camera rides on that is not a position.

        A damped spring for the landing, an ease for the bob and another for
        the lens. All three replaced a value switched at a phase boundary, and
        a whole-frame step in the eye or the field of view reads as a jolt
        however correct the frames either side of it are.
        """
        acc = -DIP_W * DIP_W * self.dip - 2.0 * DIP_ZETA * DIP_W * self.dip_v
        self.dip_v += acc * dt
        self.dip += self.dip_v * dt
        want_foot = 1.0 if self.phase == "ground" else 0.0
        self.foot += (want_foot - self.foot) * min(1.0, dt * FOOT_EASE)
        # Off a peak-hold of the speed rather than the speed itself. The body
        # genuinely is faster in the air than across a block, so hung off the
        # instantaneous figure the lens zoomed in and out twice a second in
        # step with the jumps -- a lens breathing on the beat is a good part of
        # what reads as bouncing. Held and bled off slowly, an ordinary run
        # holds one field of view and only the *materials* move it: soul sand
        # and cobweb still narrow the lens, because being slow for a second is
        # what they are for.
        self._pace = max(self.speed, self._pace - dt * PACE_FALL)
        want_fov = FOV + FOV_GAIN * max(0.0, self._pace - tp.RUN_SPEED)
        self.fov += (want_fov - self.fov) * min(1.0, dt * FOV_EASE)

    def _aim_camera(self) -> None:
        step = self.stride * STRIDE_RATE
        # ``sin^2``: ``|sin|`` with the corner taken off. The head still rises
        # twice a stride, without the eye's velocity reversing inside one frame
        # at the bottom of every step.
        bob = (0.5 - 0.5 * math.cos(2.0 * step)) * 0.055 * self.foot
        sway = math.sin(step * 0.5) * 0.045 * self.foot
        cam = self.camera
        eye_y = self.pos[1] + tp.EYE - self.dip + bob
        cam.position = (self.pos[0] + math.cos(self.yaw) * sway, eye_y,
                        self.pos[2] + math.sin(self.yaw) * sway)
        look = 5.5
        flat = math.cos(self.pitch) * look
        cam.target = (cam.position.x + math.sin(self.yaw) * flat,
                      eye_y - math.sin(self.pitch) * look,
                      cam.position.z - math.cos(self.yaw) * flat)
        fx, fz = math.sin(self.yaw), -math.cos(self.yaw)
        cam.up = (math.sin(self._roll) * -fz, math.cos(self._roll),
                  math.sin(self._roll) * fx)
        cam.fovy = self.fov

    # -- drawing -----------------------------------------------------------

    def _lamp_glows(self) -> None:
        """A glow on every lamp the building has placed near the camera.

        The tower is drawn as meshed chunks, so there is no per-block draw to
        hang an emissive billboard on -- the generator hands the cells back
        instead. Indoors this is the only light there is, which is why it
        brightens as ``indoor`` rises rather than being a constant.
        """
        eye = (self.camera.position.x, self.camera.position.y,
               self.camera.position.z)
        colour = self._colour(self.theme_here().glow)
        alpha = int(80 + 150 * self.indoor)
        for x, y, z in self.cone.lamps:
            if abs(y - eye[1]) > 26:
                continue
            if math.dist(eye, (x, y + 0.5, z)) > 42.0:
                continue
            self._glows.append((x, y + 0.5, z, 3.8 + 2.2 * self.indoor,
                                colour, alpha))

    def _fog(self, dist: float, alpha: int = 255) -> rl.RGBA:
        """Distance fog as a draw tint, tinted by the ring you are in.

        A tint multiplies, so this cannot lighten anything toward a pale fog --
        what it does is pull every material toward the ring's own light, which
        is why the nether ring is red-lit and the deep is green even though
        nothing in the renderer knows what a light is.
        """
        f = min(1.0, max(0.0, dist / FOG_FAR)) ** 0.85
        c = rl.mix_rgb(self.ring_light, self.palette.fog, 0.35)
        tint = rl.mix_rgb((255, 255, 255), c, f * 0.82)
        if self.indoor > 0.01:
            # Indoors the sky is not lighting anything. Everything goes down
            # together and the lamps come up to meet it, which is what makes a
            # hall read as a hall rather than as an outdoor course with a wall
            # in front of it.
            tint = rl.scale_rgb(tint, 1.0 - 0.32 * self.indoor)
        return rl.rgba(tint, alpha)

    def draw(self) -> None:
        pal = self.palette
        theme = self.theme_here()
        # The ring's own light, softened toward white so a dark ring dims the
        # world rather than painting it.
        self.ring_light = rl.mix_rgb((255, 255, 255), theme.sky,
                                     0.35 + 0.45 * theme.dark)
        self.sky.draw(self.elapsed)
        self._aim_camera()
        self._glows.clear()

        rl.BeginMode3D(self.camera[0])
        # The sea, a long way down. Drawn first and flushed immediately: a
        # batched plane is otherwise issued after every model in the frame and
        # loses the depth test to all of them, which is how a sea grows holes
        # in the shape of whatever is floating above it.
        # Toward the run's own fog rather than toward the ring's light: a ring
        # lit like daylight would otherwise bleach the sea on a night run, and
        # the sea being brighter than the sky above it is the one thing that
        # cannot be true.
        rl.DrawPlane((self.pos[0], SEA_Y, self.pos[2]), (5000, 5000),
                     rl.rgba(rl.mix_rgb(self.deep, pal.fog,
                                        min(0.82, (self.pos[1] - SEA_Y) / 240.0)),
                             255))
        rl.flush()
        rl.EndMode3D()

        # Aerial perspective over the sea *only*. It is a screen-space band, so
        # it goes in the gap between the world below and everything you are
        # actually looking at -- drawn after the tower instead, it bleaches the
        # wall three metres away as hard as the water a hundred metres down,
        # which is not haze, it is a wash laid over the middle of the frame.
        self._draw_haze(pal)

        rl.BeginMode3D(self.camera[0])
        # Before the tower: they are further away than all of it, and drawing
        # them first lets the wall in front reject them by depth for free.
        #
        # *After* the haze band, and that is not a preference. The band is a
        # screen-space wash at alpha 205 covering half the frame below the
        # horizon -- everything drawn before it in that region is 80% fog
        # colour, which for an island four hundred metres out on a flat sea is
        # not aerial perspective, it is deletion. Drawn here they keep their
        # own distance tint, which does the same job honestly (see
        # :meth:`_draw_scenery`), and the sea behind them stays hazed.
        self._draw_scenery(sea=True)
        self._draw_scenery(sea=False)
        self._draw_tower()
        self._draw_props()
        self._draw_course()
        self._draw_orbs()
        self.burst.draw(self.camera)
        self._draw_clouds()
        self._lamp_glows()
        self._draw_held()
        glow_pass(self.camera, self._glows)
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        self._draw_submerged()
        self._draw_crosshair()
        self._draw_hud()

    def _draw_tower(self) -> None:
        eye = (self.camera.position.x, self.camera.position.y,
               self.camera.position.z)

        def tint(x: float, y: float, z: float) -> rl.RGBA:
            return self._fog(self._depth(eye, (x, y, z)))

        aim = self.camera.target
        dx, dy, dz = aim.x - eye[0], aim.y - eye[1], aim.z - eye[2]
        n = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        self.volume.draw(tint, near=eye, far=FOG_FAR * 1.6,
                         look=(dx / n, dy / n, dz / n))

    def _depth(self, eye, at) -> float:
        """Fog distance, with everything below the body pushed further away.

        The tower is only built fifty blocks down. Without this its lowest
        chunk is a sharply lit stub with nothing under it, which reads as the
        building having been cut off -- and the whole point of the format is
        that it goes down as far as it goes up.
        """
        d = math.dist(eye, at)
        under = eye[1] - at[1]
        if under > 12.0:
            d += (under - 12.0) * (UNDER_FOG - 1.0)
        return d

    def _arrival(self, born: float) -> tuple[float, int]:
        """Scale and alpha of a block that has just been generated.

        Blocks arrive sixteen ahead of the body, which at this fog distance is
        right on the edge of visibility -- so without this they wink into
        existence in plain sight.
        """
        age = self.elapsed - born
        if age >= POP_IN:
            return 1.0, 255
        f = max(0.0, age / POP_IN)
        return 0.55 + 0.45 * f, int(60 + 195 * f)

    def _draw_props(self) -> None:
        """Every piece of furniture near enough and ahead of the camera.

        One draw call each, so the cost is set by how many are *drawn* rather
        than by how many exist -- and a body in a trough has most of a
        revolution of them behind it.
        """
        cam = self.camera
        eye = (cam.position.x, cam.position.y, cam.position.z)
        fx = cam.target.x - eye[0]
        fy = cam.target.y - eye[1]
        fz = cam.target.z - eye[2]
        n = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / n, fy / n, fz / n
        far2 = PROP_FAR * PROP_FAR
        for (x, y, z), kind, yaw in self.cone.props:
            dx, dy, dz = x - eye[0], y - eye[1], z - eye[2]
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > far2:
                continue
            if dx * fx + dy * fy + dz * fz < PROP_AHEAD * math.sqrt(d2):
                continue
            model = self.props.get(kind)
            if model is None:
                continue
            tint = self._fog(self._depth(eye, (x, y, z)))
            rl.DrawModelEx(model.model, (x, y, z), (0, 1, 0),
                           math.degrees(yaw), (1.0, 1.0, 1.0), tint)

    def _draw_course(self) -> None:
        eye = (self.camera.position.x, self.camera.position.y,
               self.camera.position.z)
        # The cell the head is in this frame. ``x`` and ``z`` of a cell are its
        # centre and ``y`` is its floor, which is the project's oldest landmine
        # and the reason this is not three calls to the same rounding.
        self._eye_cell = (round(eye[0]), math.floor(eye[1]), round(eye[2]))
        for blk in self.course.blocks:
            if blk["form"] == "floor":
                continue          # it is the building; the volume drew it
            dist = self._depth(eye, (blk["x"], blk["y"], blk["z"]))
            if dist > FOG_FAR * 1.4:
                continue
            scale, alpha = self._arrival(blk["born"])
            tint = self._fog(dist, alpha)
            style = self._style_of(blk)
            model = self._model(style)
            form = blk["form"]
            h = tp.FORMS[form]
            if form == "wide":
                for ox in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        voxel.draw_box(model, blk["x"] + ox, blk["y"] + 0.5,
                                       blk["z"] + oz, tint, scale, scale, scale)
            elif form == "slab":
                voxel.draw_box(model, blk["x"], blk["y"] + 0.25, blk["z"], tint,
                               scale, 0.5 * scale, scale)
            elif form == "web":
                # Crossed gauze sheets, like the soft cells: a cobweb as a
                # full translucent cube fills the whole lens while the body
                # wades through its middle.
                for yaw in (45.0, -45.0):
                    voxel.draw_box(model, blk["x"], blk["y"] + 0.5, blk["z"],
                                   tint, 1.3 * scale, scale, 0.10, yaw=yaw)
            elif form == "fence":
                # A post with a cap: the real map's signature obstacle, a
                # landing you cannot jump onto from the ground beside it.
                voxel.draw_box(model, blk["x"], blk["y"] + 0.7, blk["z"],
                               tint, 0.24 * scale, 1.4 * scale, 0.24 * scale)
                voxel.draw_box(model, blk["x"], blk["y"] + 1.44, blk["z"],
                               tint, 0.4 * scale, 0.12, 0.4 * scale)
            elif form == "wall":
                voxel.draw_box(model, blk["x"], blk["y"] + 0.75, blk["z"],
                               tint, 0.55 * scale, 1.5 * scale, 0.55 * scale)
            elif form == "trapdoor":
                voxel.draw_box(model, blk["x"], blk["y"] + 0.1, blk["z"],
                               tint, scale, 0.19, scale)
            else:
                voxel.draw_box(model, blk["x"], blk["y"] + h * 0.5, blk["z"],
                               tint, scale, h * scale, scale)
            if style in _GLOWING:
                self._glows.append((blk["x"], blk["y"] + h + 0.1, blk["z"],
                                    1.5, self._colour(style), 90))
            elif dist < LAND_LIT_FAR:
                # A soft light on the face you land on.
                #
                # This is how the route is made readable, and it is deliberately
                # not done with colour. Every landing here is made of the
                # level's own material -- the map-making consensus is that
                # contrasting jump blocks wreck the theme and buy nothing,
                # because a cake and a cobblestone have the same hitbox -- so
                # what marks a landing is that it is *lit*, which is the fix
                # real mappers converged on. Small radius, low alpha: enough to
                # pick the next block out of a wall at a glance, not enough to
                # read as a lamp.
                fade = 1.0 - dist / LAND_LIT_FAR
                self._glows.append((
                    blk["x"], blk["y"] + h + 0.05, blk["z"], 1.15,
                    rl.mix_rgb(self._colour(
                        self.plan.THEME_BY_NAME[blk["theme"]].glow),
                               (255, 250, 235), 0.45),
                    int(52 * fade * alpha / 255)))
            self._draw_furniture(blk, dist, alpha)

    def _draw_furniture(self, blk: dict, dist: float, alpha: int) -> None:
        for d in blk["deco"]:
            tint = self._fog(dist, alpha)
            voxel.draw_box(self._model(d["style"]),
                           blk["x"] + d["dx"],
                           blk["y"] + d["dy"] + d["sy"] * 0.5,
                           blk["z"] + d["dz"], tint,
                           d["sx"], d["sy"], d["sz"], yaw=0.0)
            if d["glow"]:
                self._glows.append((blk["x"] + d["dx"],
                                    blk["y"] + d["dy"] + d["sy"] * 0.5,
                                    blk["z"] + d["dz"], 2.2,
                                    self._colour(d["style"]), 120))
        if not blk["soft"]:
            return
        # A ladder is a plate on a wall, water fills its cell, a web is a cell
        # of gauze -- the same cube at three different scales, which is why
        # this scene has no new geometry in it at all.
        #
        # Water and web are translucent, and a translucent draw that writes
        # depth deletes everything drawn after it and further away. A seven
        # block bubble column is a very large hole to punch in a tower, and it
        # is the exact failure this project has a probe for.
        opaque = [s for s in blk["soft"] if s["style"] not in _TRANSLUCENT]
        clear = [s for s in blk["soft"] if s["style"] in _TRANSLUCENT]
        for s in opaque:
            at = (blk["x"] + s["dx"], blk["y"] + s["dy"], blk["z"] + s["dz"])
            model = self.props.get(s["style"])
            if model is not None and s.get("face"):
                # A ladder is a thin lattice on the face of a block and a vine
                # is a thin sheet on one. Drawn as a 0.84-wide cube -- which is
                # what this was -- they read as a solid pillar of wood, which
                # is not a thing the game has.
                ax, az = s["face"]
                # ...and *on* that face, not in the middle of the cell. See
                # ``LADDER_HUG``: a plate at the cell's centre stands half a
                # block clear of the block it is nailed to, which is a lattice
                # hanging in the air rather than a ladder.
                rl.DrawModelEx(model.model,
                               (at[0] + ax * LADDER_HUG, at[1],
                                at[2] + az * LADDER_HUG), (0, 1, 0),
                               math.degrees(math.atan2(-ax, az)),
                               (1.0, 1.0, 1.0), self._fog(dist, alpha))
                continue
            voxel.draw_box(self._model(s["style"]), at[0], at[1] + 0.5, at[2],
                           self._fog(dist, alpha), 0.84, 1.0, 0.84)
        if not clear:
            return
        with no_depth_write():
            for s in clear:
                at = (blk["x"] + s["dx"], blk["y"] + s["dy"] + 0.5,
                      blk["z"] + s["dz"])
                if s["style"] == "web":
                    # A cobweb is a crossed pair of gauze sheets, exactly as
                    # the game draws it. As a full translucent cube -- which
                    # is what this was -- the body wades through the *inside*
                    # of it and the whole lens goes speckled for a second.
                    # The yaw is salted per cell: a wade lays several webs in
                    # a row, and identically angled sheets read as one long
                    # curtain instead of a webbed-up gallery.
                    salt = (at[0] * 7 + at[2] * 13) % 5 * 11.0
                    for yaw in (45.0 + salt, -45.0 + salt):
                        voxel.draw_box(self._model("web"), at[0], at[1],
                                       at[2], self._fog(dist, 150),
                                       1.15, 1.0, 0.10, yaw=yaw)
                    continue
                narrow = 0.66 if s["style"] in _COLUMN_GLOW else 0.94
                voxel.draw_box(self._model(s["style"]), at[0], at[1], at[2],
                               self._fog(dist, 120), narrow, 1.0, narrow)
        glow = _COLUMN_GLOW.get(clear[0]["style"])
        if glow is not None:
            top = max(s["dy"] for s in clear)
            self._glows.append((blk["x"] + clear[0]["dx"],
                                blk["y"] + top + 0.6,
                                blk["z"] + clear[0]["dz"], 3.0,
                                glow, 110))

    def _draw_orbs(self) -> None:
        model = self._model("glowstone")
        hover = self.orb_hover()
        spin = (self.elapsed * 150.0) % 360.0
        eye = (self.camera.position.x, self.camera.position.y,
               self.camera.position.z)
        for blk in self.course.blocks:
            for orb in blk["orbs"]:
                if orb["taken"]:
                    continue
                dist = math.dist(eye, (orb["x"], orb["y"], orb["z"]))
                if dist > FOG_FAR:
                    continue
                voxel.draw_box(model, orb["x"], orb["y"] + hover, orb["z"],
                               rl.rgba(ORB_COLOR, 255), ORB_SCALE, ORB_SCALE,
                               ORB_SCALE, yaw=spin)
                self._glows.append((orb["x"], orb["y"] + hover, orb["z"], 1.1,
                                    ORB_COLOR, 150))

    def _horizon_y(self) -> int:
        """Screen row the sea's horizon falls on, this frame.

        A point at eye height and effectively infinite distance projects to it
        exactly, whatever the camera is doing -- and the camera here pitches a
        long way, so a fixed fraction of the frame is wrong most of the time.
        """
        cam = self.camera
        far = (cam.position.x + math.sin(self.yaw) * 1e5, cam.position.y,
               cam.position.z - math.cos(self.yaw) * 1e5)
        try:
            y = int(rl.GetWorldToScreen(far, cam[0]).y)
        except Exception:
            y = int(self.height * 0.5)
        return max(int(self.height * 0.05), min(int(self.height * 0.95), y))

    def _draw_submerged(self) -> None:
        """Wash the frame toward the liquid while the head is inside it.

        Over the weather and under the HUD: rain falling *behind* a wall of
        water is the one ordering that is obviously wrong, and a tinted score
        readout is the other. Two draws -- a flat wash and a heavier edge --
        because a uniform tint reads as a colour-grade and the darkening at
        the sides is what says you are looking through something.
        """
        if self.submerged <= 0.01:
            return
        a = int(SUBMERGE_ALPHA * self.submerged)
        rl.DrawRectangle(0, 0, self.width, self.height,
                         rl.rgba(self.submerged_rgb, a))
        edge = max(1, int(self.width * 0.18))
        for i in range(3):
            f = (i + 1) / 3.0
            w = int(edge * f)
            b = rl.rgba(self.submerged_rgb, int(a * 0.55 * f))
            rl.DrawRectangle(0, 0, w, self.height, b)
            rl.DrawRectangle(self.width - w, 0, w, self.height, b)

    def _draw_haze(self, pal) -> None:
        """Aerial perspective at the horizon, in two directions.

        The sea is one flat plane a hundred metres down with no distance
        shading of its own, so without this it meets the sky along a *drawn
        line* and the whole drop reads as a pale plate ten metres under your
        feet rather than as the ground a long way below. The band therefore has
        to be strongest exactly where the water ends.

        It starts a little *above* the true horizon and fades in, because the
        eye finds a hard edge in a clear sky instantly and a band that begins at
        full strength draws exactly the line it was meant to hide, a few rows
        higher up.

        Where the horizon falls is projected rather than guessed: the camera
        pitches a long way in this scene, and a fixed fraction of the frame
        leaves a strip of unhazed water above the haze every time the head goes
        up.

        A 2D draw, in the gap between the sea and everything else: it writes no
        depth at all, and nothing drawn after it is touched by it.
        """
        band = textures.alpha_band(f"tower-haze-{self.ctx.seed.run}", pal.fog,
                                   205, 1.7, ramp=0.24)
        horizon = self._horizon_y()
        rl.DrawTexturePro(band, (0, 0, 4, 128),
                          (0, horizon - int(self.height * 0.07), self.width,
                           int(self.height * 0.5)), (0, 0), 0.0, rl.WHITE4)

    def _draw_clouds(self) -> None:
        """Sheets of cloud at absolute altitudes, drawn after the tower.

        Depth *writing* off, depth *test* on: a shelf behind the tower is
        rejected by the wall in front of it, and a shelf in front of the tower
        hides nothing it should not. Both halves matter -- a translucent quad
        that writes depth deletes everything drawn after it and further away,
        which in this scene would be most of the building.
        """
        with no_depth_write():
            for shelf in self.shelves:
                dy = shelf["y"] - self.pos[1]
                if not (-70 < dy < 110):
                    continue
                fade = 1.0 - min(1.0, abs(dy) / 110.0)
                rl.DrawBillboardRec(
                    self.camera[0], shelf["tex"],
                    (0.0, 0.0, float(shelf["tex"].width),
                     float(shelf["tex"].height)),
                    (shelf["x"], shelf["y"], shelf["z"]),
                    (shelf["s"], shelf["s"] * 0.5),
                    rl.rgba(self.cloud_tint, int(120 * fade)))

    # -- the hand ----------------------------------------------------------

    def _camera_basis(self):
        cam = self.camera
        fx = cam.target.x - cam.position.x
        fy = cam.target.y - cam.position.y
        fz = cam.target.z - cam.position.z
        n = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / n, fy / n, fz / n
        ux, uy, uz = cam.up.x, cam.up.y, cam.up.z
        rx, ry, rz = fy * uz - fz * uy, fz * ux - fx * uz, fx * uy - fy * ux
        n = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
        return (rx / n, ry / n, rz / n), (ux, uy, uz), (fx, fy, fz)

    def _draw_held(self) -> None:
        """Whatever is in your hand, swinging in the corner of the frame.

        A first-person shot without it reads as a flying camera rather than as
        somebody playing, which is most of what this scene is for. Positioned
        off the camera basis rather than through a second view matrix: it is
        nearer than anything else in the world, so the ordinary depth test puts
        it in front without any special handling.
        """
        right, up, fwd = self._camera_basis()
        cam = self.camera
        bob = math.sin(self.stride * STRIDE_RATE) * 0.02
        swing = math.sin(self.swing * math.pi) * 0.12 + self.mine * 0.22
        for part in self.kit["parts"]:
            u = 0.44 + part["u"]
            v = -0.38 + part["v"] + bob + swing * 0.5
            f = 1.10 + part["f"] - swing * 0.34
            x = cam.position.x + right[0] * u + up[0] * v + fwd[0] * f
            y = cam.position.y + right[1] * u + up[1] * v + fwd[1] * f
            z = cam.position.z + right[2] * u + up[2] * v + fwd[2] * f
            sx, sy, sz = part["size"]
            voxel.draw_box(self._model(part["style"]), x, y, z,
                           rl.rgba((255, 255, 255), 255), sx, sy, sz,
                           yaw=math.degrees(-self.yaw) + part["yaw"])
            if part.get("glow"):
                self._glows.append((x, y, z, 1.6, self._colour(part["style"]),
                                    120))

    # -- overlays ----------------------------------------------------------

    def _draw_crosshair(self) -> None:
        cx, cy = self.width // 2, self.height // 2
        col = (235, 235, 235, 150)
        rl.DrawRectangle(cx - 7, cy - 1, 14, 2, col)
        rl.DrawRectangle(cx - 1, cy - 7, 2, 14, col)

    def _draw_hud(self) -> None:
        pal = self.palette
        text(f"{self.climbed:.0f} m", 12, 10, 22, (255, 255, 255))
        # The ring's name, flashed brighter for a moment after it changes:
        # the theme switching at a gallery is the loudest beat the scene has
        # and it deserves to be said as well as shown.
        chip(self.ring.upper(), 16, 40, 14,
             rl.mix_rgb(pal.accent, (255, 255, 255), self.ring_flash),
             (0, 0, 0, int(110 + 90 * self.ring_flash)))
        if self.orbs:
            text(f"{self.orbs}", self.width - 14, 10, 22, ORB_COLOR,
                 anchor="topright")
        if self.combo > 1:
            text(f"x{self.combo}", self.width - 14, 36, 16, pal.accent2,
                 anchor="topright")

    def teardown(self) -> None:
        self.volume.teardown()


#: Materials that light their own cell. Purely a draw-time list -- the
#: generator does not know or care which of its blocks glow.
_GLOWING = frozenset(("lantern", "torch", "glowstone", "sealantern", "magma"))
#: Soft cells drawn see-through, which therefore must not write depth.
_TRANSLUCENT = frozenset(("water", "lava", "web", "glass"))
#: Columns a body rides up, and the light that spills off the top of one. A
#: bubble column used to be water whatever the node asked for, so this table
#: had no reason to exist; it does now, and the nether family's exit is a
#: column of lava rather than a blue one standing in an orange field.
_COLUMN_GLOW = {"water": (150, 210, 255), "lava": (255, 168, 72)}


def _wrap(a: float) -> float:
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def _recipes(pal, run: int) -> dict[str, dict]:
    """Every material this scene can draw, as face-strip arguments.

    One dictionary feeds both the meshed atlas and the individual cube models,
    which is the point: a course block and the wall behind it are drawn by
    completely different code paths and must not be able to disagree about what
    brick looks like.

    The building's materials keep recognisable colours -- netherrack is red
    wherever the run's palette went -- and are only dimmed toward the run's
    ambient, so a night tower is lit like a night tower.
    """
    # Floored well above zero. A night run scales every material toward its
    # ambient, and the darkest ones -- blackstone, obsidian, deepslate -- came
    # out near black: at four metres from the lens that does not read as dark
    # stone, it reads as a hole in the tower.
    lit = max(0.62, 0.45 + 0.55 * pal.ambient)
    out: dict[str, dict] = {}
    for i, (name, (base, pattern, noise)) in enumerate(tp.MATERIALS.items()):
        out[name] = dict(base=rl.scale_rgb(base, lit), noise=noise,
                         seed=run * 17 + i, pattern=pattern)
    # No candy colours. Every other scene in this project gives its jump
    # blocks three bright per-run colours so the eye can find them; this one
    # deliberately does not, because the owner's complaint and the map-making
    # consensus agree -- a landing that is a different colour from the place it
    # is in stops the place being a place. Landings here are the level's own
    # stone, and what marks them is the light on their top face.
    return out


@register("tower")
class TowerScene(SpiralScene):
    """The hand-built tower: this renderer against a designed course.

    Not a scene so much as a second *plan*. Everything visible here -- the
    meshing, the body, the camera, the weather, the head-up display -- is
    :class:`SpiralScene`'s, and the only difference is which module decides
    what the parkour is. See :mod:`brainrot.scenes.handplan` and
    ``docs/TOWER.md``.
    """

    plan = hp


def _choose_kit(rng) -> dict:
    """What the player is carrying this run, assembled from the same cube."""
    def part(style, u=0.0, v=0.0, f=0.0, size=(0.13, 0.13, 0.13), yaw=0.0,
             glow=False):
        return {"style": style, "u": u, "v": v, "f": f, "size": size,
                "yaw": yaw, "glow": glow}

    kits = (
        [part("stonebrick", size=(0.15, 0.15, 0.15))],
        [part("oak", v=-0.05, size=(0.035, 0.19, 0.035)),
         part("iron", v=0.10, size=(0.14, 0.045, 0.045))],
        [part("oak", v=-0.045, size=(0.035, 0.17, 0.035)),
         part("lantern", v=0.10, size=(0.06, 0.07, 0.06), glow=True)],
        [part("gold", size=(0.15, 0.15, 0.15))],
        [part("ladder", size=(0.13, 0.20, 0.04))],
    )
    return {"parts": kits[rng.randrange(len(kits))]}
