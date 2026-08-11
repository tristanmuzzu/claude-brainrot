"""First-person spiral-tower parkour: the other Minecraft reel format.

``scenes/parkour.py`` is *infinite parkour* -- a course of floating blocks that
runs away from you over an ocean. This is the other thing those reels are made
of, and it is a genuinely different format rather than a reskin: a **parkour
tower**, the Parkour Spiral / Tower of Hell genre, where the course winds up the
outside of a building that keeps going out of the top of the frame.

What that changes, and why it needed its own scene:

* **Progress is altitude, round a fixed axis.** The course comes back over
  itself every revolution, so the occupancy map has to survive a generator that
  is climbing through the space it was in twenty seconds ago.
* **Most of what you see is architecture**, not course: a wall, windows,
  cornices, buttresses, galleries. That is thousands of static cells, drawn
  through :mod:`brainrot.engine.chunk` as meshed patches -- one draw call each,
  face-culled -- because at one call per cube it would be the whole frame
  budget spent on scenery nobody lands on.
* **The rings are themed and they change abruptly**, at a gallery, which is the
  one structural note every spiral map in the reference material agrees on.
  Eleven themes, in a shuffled bag: a stone keep, a timber ring, a mine, an
  overgrown ruin, a desert ring, the nether, an ice ring, a slime laboratory,
  a prismarine deep, the end, and a gold summit.
* **The moves are the game's, not one move repeated.** A tower has nowhere to
  go but up, and vanilla's single jump impulse reaches 1.25 blocks -- so it has
  to have ladders, bubble columns, slime, ice and cobweb, and each of them has
  to be checked against its own physics. :mod:`brainrot.scenes.towerplan` owns
  all of that; this file draws it and moves a body along it.

The split is the same one the runner uses: the plan module has no renderer in
it, so a sixty-run sweep of the geometry costs four seconds and no window.
"""

from __future__ import annotations

import math

from . import towerplan as tp
from ..engine import chunk, rl, voxel
from ..engine.collide import AABB
from ..engine.fx import Burst, Weather, glow_pass, no_depth_write
from ..engine.hud import chip, text
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import SkyDome
from ..engine import textures
from ..engine.textures import cloud_blob

#: Vertical field of view. A touch wider than the flat scene's, because the
#: subject here is tall and close: the wall is three metres away and the thing
#: worth seeing is how far it goes up and how far it goes down.
FOV = 78.0
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

#: How far the look-at point is pulled back toward the tower's axis, and how
#: much further down the camera aims than the next landing.
#:
#: The bias is small and both directions of error were measured. At a quarter
#: of the way in, the camera spends a run with its nose against masonry -- the
#: strip is portrait, so its *horizontal* field is only about fifty degrees and
#: a wall four metres away fills all of it. At zero, the head looks straight
#: along the helix, the wall sits at ninety degrees to that, and the building
#: the whole format is about is off the side of the frame entirely. An eighth
#: of the way in puts it along one edge, which is where a player hugging a wall
#: actually sees it. The pitch bias is separate and unconditional: the drop is
#: underneath you, and a camera levelled at the next landing never shows it.
AXIS_BIAS = 0.12
PITCH_BIAS = 0.17

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
WRITE_BUDGET = 900


@register("tower")
class TowerScene(Scene):
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
        self.atlas = chunk.BlockAtlas(f"run{seed.run}-tower",
                                      [(n, k) for n, k in self.recipe.items()],
                                      see_through=tp.SEE_THROUGH)
        self.volume = chunk.ChunkedVolume(self.atlas)

        self.tower = tp.Tower(ctx.stream("tower"), 0)
        self.course = tp.Course(ctx.stream("course"), self.tower,
                                hop_rng=ctx.stream("hops"))
        self.hop_rng = ctx.stream("hops2")
        self._written = 0

        self.deep = rl.mix_rgb(rl.mix_rgb(pal.sky_bottom, (10, 46, 96), 0.74),
                               pal.fog, 0.10)
        self.kit = _choose_kit(ctx.stream("kit"))
        self.swing = 0.0
        self.mine = 0.0

        # -- the body ------------------------------------------------------
        self.index = 0
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
        self.land_dip = 0.0
        self.yaw = 0.0
        self.pitch = 0.10
        self._flick = 0.0
        self._roll = 0.0
        self._begin_ground()
        self.yaw = math.atan2(blk["step"][0], -blk["step"][1])

        # -- scoring -------------------------------------------------------
        self.orbs = 0
        self.orbs_missed = 0
        self.combo = 0
        self.combo_t = 0.0
        self.tier = self.tower.tier_of(self.pos[1])
        self.ring = self.tower.theme(self.tier).name
        self.ring_flash = 0.0
        self.ring_light = (255, 255, 255)

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
        return blk["style"] or self.tower.theme_at(blk["y"]).trim

    # -- world streaming ---------------------------------------------------

    def _pump(self, prime: bool = False) -> None:
        """Move generated structure into the renderer, a budget at a time."""
        writes = self.course.writes
        budget = len(writes) if prime else WRITE_BUDGET
        if writes:
            take = writes[:budget]
            del writes[:budget]
            floor = int(self.pos[1]) - BELOW
            for cell, style in take:
                if cell[1] >= floor:
                    self.volume.set(cell, style)
            self._written += len(take)
        self.volume.build_pending(64 if prime else CHUNK_BUDGET)

    def _spawn_shelf(self, rng) -> None:
        y = self._next_shelf + rng.uniform(18, 46)
        self._next_shelf = y
        self.shelves.append({
            "tex": cloud_blob(int(y) * 31 + 7, 160),
            "x": rng.uniform(-150, 150), "z": rng.uniform(-150, 150),
            "y": y, "s": rng.uniform(55, 120), "drift": rng.uniform(0.3, 1.1),
            "phase": rng.uniform(0, 6.283),
        })

    # -- simulation --------------------------------------------------------

    def _block(self) -> dict:
        return self.course.blocks[self.index]

    def _begin_ground(self) -> None:
        """Set up the run across the block just landed on.

        The feet keep going: the landing was on the near edge, the take-off is
        from the far one, and the time between them is not a number anybody
        chose -- it is that distance at whatever pace the block's material
        allows. Soul sand takes twice as long as stone to cross and ice half,
        and that one number is most of what makes a ring feel like what it is
        made of.
        """
        blk = self._block()
        self.run_from = list(self.course.land_point(blk))
        self.run_to = list(self.course.takeoff_point(blk))
        self.run_len = math.dist((self.run_from[0], self.run_from[2]),
                                 (self.run_to[0], self.run_to[2]))
        self.ground_speed = self.course.ground_speed(blk)
        self.ground_dur = max(0.07, self.run_len / self.ground_speed)
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
        blk = self._block()
        self.pos = list(self.course.land_point(blk))
        self.land_dip = 1.0
        self.swing = 1.0
        self.burst.spawn(self.pos[0], self.pos[1] - 0.1, self.pos[2],
                         self._colour(self._style_of(blk)),
                         count=6, speed=1.5, rng=self.hop_rng)
        # The ring the body is *on*, and it only ever goes up. A course that
        # steps down over a floor boundary and back up would otherwise flip the
        # theme twice in a second, which measured as rings lasting half a
        # second and reads on screen as the whole tower blinking.
        tier = self.tower.tier_of(blk["y"])
        if tier > self.tier:
            self.tier = tier
            name = self.tower.theme(tier).name
            if name != self.ring:
                self.ring = name
                self.ring_flash = 1.0
        # Keep the horizon of generated course ahead of the body, then let go
        # of what is behind it -- cells and chunks both. An occupancy map that
        # only grew would refuse the whole tower within a couple of hundred
        # blocks, and this course comes back over itself every revolution.
        while len(self.course.blocks) - self.index < tp.AHEAD:
            self.course.spawn()["born"] = self.elapsed
        dropped = self.course.advance(self.index)
        if dropped:
            self.index -= dropped
        self.volume.drop_below(int(self.pos[1]) - BELOW)
        self._begin_ground()

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.phase_t += dt
        if self.phase == "ground":
            f = min(1.0, self.phase_t / self.ground_dur)
            self.pos = [self.run_from[i] + (self.run_to[i] - self.run_from[i]) * f
                        for i in range(3)]
            self.stride += self.ground_speed * dt
            self.vy = 0.0
            if self.phase_t >= self.ground_dur:
                self._begin_move()
        else:
            move = self.move
            was = self.pos[1]
            self.pos = list(move.at(self.phase_t))
            self.vy = (self.pos[1] - was) / max(1e-5, dt)
            if move.kind in ("climb", "bubble", "web"):
                self.stride += 0.4 * dt
            if self.phase_t >= move.dur:
                self._land()
        self.climbed = self.pos[1] - self.base_y
        self.land_dip = max(0.0, self.land_dip - dt * 4.6)
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
        # ...and a quarter of the way back toward the axis. Looking straight
        # along a helix points the camera tangentially, which puts the tower
        # off the side of a portrait strip and fills the frame with sky: the
        # course is what you are following, but the *building* is the subject.
        # A player hugging a wall looks along it, not past it.
        aim[0] *= 1.0 - AXIS_BIAS
        aim[2] *= 1.0 - AXIS_BIAS

        self._flick = max(0.0, self._flick - dt * 5.5)
        rate = min(1.0, (5.0 + 22.0 * self._flick ** 2) * dt)
        self.yaw += _wrap(math.atan2(aim[0] - x, -(aim[2] - z)) - self.yaw) * rate

        flat = math.hypot(aim[0] - x, aim[2] - z)
        want = math.atan2(self.pos[1] + tp.EYE - (aim[1] + tp.EYE * 0.95),
                          max(3.2, flat))
        # Riding something looks *up* it. A ladder or a bubble column is the
        # one moment in the run with time to spare, and spending it looking at
        # the rungs is the difference between a lift and a climb.
        if self.phase == "move" and self.move.kind in ("climb", "bubble"):
            want -= 0.42
        else:
            want -= max(-0.22, min(0.30, self.vy * 0.028))
        # And a touch further down than the next landing, always. The drop is
        # the entire point of a tower and it is underneath you; a camera
        # levelled at the next block spends the run looking at sky.
        want += PITCH_BIAS
        self.pitch += _wrap(max(-0.62, min(0.62, want)) - self.pitch) * rate * 0.8

        roll = math.sin(self.stride * STRIDE_RATE) * 0.035 \
            if self.phase == "ground" else 0.0
        self._roll += (roll - self._roll) * min(1.0, dt * 9.0)

    def _aim_camera(self) -> None:
        dip = self.land_dip ** 1.4 * 0.17 - math.sin(self.land_dip * math.pi) * 0.02
        step = self.stride * STRIDE_RATE
        ground = self.phase == "ground"
        bob = abs(math.sin(step)) * 0.055 if ground else 0.0
        sway = math.sin(step * 0.5) * 0.045 if ground else 0.0
        cam = self.camera
        eye_y = self.pos[1] + tp.EYE - dip + bob
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
        cam.fovy = FOV + (2.0 if self.phase == "move" else 0.0)

    # -- drawing -----------------------------------------------------------

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
        return rl.rgba(tint, alpha)

    def draw(self) -> None:
        pal = self.palette
        theme = self.tower.theme_at(self.pos[1])
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
        self._draw_tower()
        self._draw_course()
        self._draw_orbs()
        self.burst.draw(self.camera)
        self._draw_clouds()
        self._draw_held()
        glow_pass(self.camera, self._glows)
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        self._draw_crosshair()
        self._draw_hud()

    def _draw_tower(self) -> None:
        eye = (self.camera.position.x, self.camera.position.y,
               self.camera.position.z)

        def tint(x: float, y: float, z: float) -> rl.RGBA:
            return self._fog(self._depth(eye, (x, y, z)))

        self.volume.draw(tint, near=eye, far=FOG_FAR * 1.6)

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

    def _draw_course(self) -> None:
        eye = (self.camera.position.x, self.camera.position.y,
               self.camera.position.z)
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
            else:
                voxel.draw_box(model, blk["x"], blk["y"] + h * 0.5, blk["z"],
                               tint, scale, h * scale, scale)
            if style in _GLOWING:
                self._glows.append((blk["x"], blk["y"] + h + 0.1, blk["z"],
                                    1.5, self._colour(style), 90))
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
            voxel.draw_box(self._model(s["style"]), blk["x"] + s["dx"],
                           blk["y"] + s["dy"] + 0.5, blk["z"] + s["dz"],
                           self._fog(dist, alpha), 0.84, 1.0, 0.84)
        if not clear:
            return
        with no_depth_write():
            for s in clear:
                narrow = 0.66 if s["style"] == "water" else 0.94
                voxel.draw_box(self._model(s["style"]), blk["x"] + s["dx"],
                               blk["y"] + s["dy"] + 0.5, blk["z"] + s["dz"],
                               self._fog(dist, 120), narrow, 1.0, narrow)
        if clear[0]["style"] == "water":
            top = max(s["dy"] for s in clear)
            self._glows.append((blk["x"] + clear[0]["dx"],
                                blk["y"] + top + 0.6,
                                blk["z"] + clear[0]["dz"], 3.0,
                                (150, 210, 255), 110))

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
_TRANSLUCENT = frozenset(("water", "web", "glass"))


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
    ambient, so a night tower is lit like a night tower. The three *candy*
    colours come from the palette, because the jump blocks are the one thing
    that has to differ run to run and the one thing the eye needs to pick out
    of a wall at a glance.
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
    for j, name in enumerate(tp.CANDY):
        out[name] = dict(base=pal.blocks[j % len(pal.blocks)], noise=0.03,
                         seed=run * 17 + 90 + j,
                         pattern=("wool", "concrete", "wool")[j % 3])
    return out


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
