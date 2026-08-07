"""First-person infinite parkour, the way the actual background reels do it.

The reference footage is first-person Minecraft: an endless course of
brightly coloured blocks floating high over scenic terrain, one flawless
sprint-jump every beat, blocks materialising a few hops ahead and vanishing
a couple behind. The generator here follows the plugin that produces most of
that footage: every jump draws a gap of 1-4 blocks and a height change of
-2..+1 from weighted tables, plus a small Gaussian sideways drift, with the
heading steered back when the course wanders too far off its spine.

Far below: an ocean, drifting cloud shelves, and grass-capped voxel islands
-- the drop is what supplies the vertigo, so the world down there exists to
be fallen toward, never reached.
"""

from __future__ import annotations

import math

from ..engine import rl, voxel
from ..engine.fx import Burst, Weather
from ..engine.hud import text
from ..engine.scene import Scene, SceneContext, register
from ..engine import textures
from ..engine.sky import SkyDome
from ..engine.textures import cloud_blob

#: weighted like the reference generator: mostly short hops, rare long ones
GAP_TABLE = (1, 1, 1, 2, 2, 2, 2, 3, 3, 4)
RISE_TABLE = (-2, -1, -1, 0, 0, 0, 0, 0, 1, 1)

EYE = 1.62
COURSE_ALT = 58.0          # block altitude above the ocean
TRAIL = 2                  # blocks kept behind the player
AHEAD = 14                 # blocks generated ahead
FOG_FAR = 70.0
BELOW_FOG = 0.55           # extra fog on the world far below


@register("parkour")
class ParkourScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        pal = ctx.palette
        seed = ctx.seed

        self.sky = SkyDome(pal, seed, ctx.width, ctx.height)
        self.weather = Weather(pal, ctx.width, ctx.height, seed.root & 0xFFFF)
        self.burst = Burst()
        self.camera = rl.make_camera(70.0)

        # block styles from the palette's candy families + one "checkpoint" ice
        self.styles = [
            voxel.block_model(f"run{seed.run}-s{i}", c, noise=0.06, seed=seed.run * 7 + i)
            for i, c in enumerate(pal.blocks)
        ]
        self.ice = voxel.block_model(f"run{seed.run}-ice", (188, 224, 247),
                                     noise=0.03, seed=seed.run * 7 + 9)
        self.grass = voxel.block_model(
            "terrain-grass", (124, 92, 62), noise=0.05, seed=4,
            top=(96, 186, 82), side_band=(104, 170, 76))

        self.rng = ctx.stream("course")
        self.irng = ctx.stream("islands")

        # course: list of dicts {x, y, z, style, wide}
        self.blocks: list[dict] = []
        self.heading = 0.0            # radians, 0 = -Z
        self.lateral = 0.0            # drift from the spine, for the director
        self._spawn_block(first=True)
        while len(self.blocks) < AHEAD:
            self._spawn_block()

        self.jump_index = 0           # block we are standing on
        self.jump_t = 0.0             # progress through the current hop
        self.jump_dur = 0.62
        self.land_dip = 0.0
        self.distance = 0.0
        self.yaw = self.heading

        # islands: spawned along the spine as the course advances
        self.islands: list[dict] = []
        self._next_island_z = 0.0
        for _ in range(6):
            self._spawn_island()

        # low cloud shelves between course and ocean
        self.shelves = []
        crng = ctx.stream("shelves")
        for i in range(10):
            self.shelves.append({
                "tex": cloud_blob(seed.run * 31 + i, 160),
                "x": crng.uniform(-70, 70),
                "z": -crng.uniform(0, 220),
                "y": crng.uniform(24, 38),
                "s": crng.uniform(18, 42),
                "drift": crng.uniform(0.4, 1.4),
            })
        self._shelf_model = None

    # -- generation -------------------------------------------------------

    def _spawn_block(self, first: bool = False) -> None:
        if first:
            self.blocks.append({"x": 0.0, "y": COURSE_ALT, "z": 0.0,
                                "style": 0, "wide": True})
            return
        prev = self.blocks[-1]
        rng = self.rng
        gap = rng.choice(GAP_TABLE)
        rise = rng.choice(RISE_TABLE)
        if prev["y"] + rise < COURSE_ALT - 14:
            rise = 1
        elif prev["y"] + rise > COURSE_ALT + 10:
            rise = -1
        # Gaussian sideways drift, steered back toward the spine. If the hop
        # would land on top of recent course, straighten and stretch instead --
        # the reference generator refuses self-overlapping placements too.
        for attempt in range(3):
            drift = rng.gauss(0.0, 0.55)
            steer = -0.028 * self.lateral
            heading = max(-0.9, min(0.9, self.heading + drift * 0.22 + steer))
            step = gap + 1.0 + attempt * 0.5
            dx = math.sin(heading) * step
            dz = -math.cos(heading) * step
            nx, nz = prev["x"] + dx, prev["z"] + dz
            if all(math.dist((nx, nz), (b["x"], b["z"])) > 1.45
                   for b in self.blocks[-7:-1]):
                break
            heading = self.heading * 0.4       # straighten out of the knot
        self.heading = heading
        self.lateral += dx

        n = len(self.blocks)
        wide = n % 24 == 0                       # breather platform
        style = 8 if (not wide and n % 17 == 0) else (n // 3) % len(self.styles)
        self.blocks.append({
            "x": prev["x"] + dx,
            "y": prev["y"] + rise,
            "z": prev["z"] + dz,
            "style": style if style != 8 else "ice",
            "wide": wide,
        })

    def _spawn_island(self) -> None:
        rng = self.irng
        z = self._next_island_z - rng.uniform(42, 95)
        self._next_island_z = z
        cubes = []
        # hug the spine: the vertigo comes from looking straight down at land
        cx = rng.gauss(0.0, 24.0)
        base = rng.uniform(7, 12)
        for i in range(rng.randint(3, 6)):
            s = rng.uniform(0.5, 1.0) * base * (1.0 - i * 0.12)
            cubes.append({
                "dx": rng.uniform(-base * 0.9, base * 0.9),
                "dz": rng.uniform(-base * 0.9, base * 0.9),
                "y": rng.uniform(0.5, 2.5) + i * rng.uniform(0.8, 1.8),
                "s": s,
            })
        self.islands.append({"x": cx, "z": z, "cubes": cubes})

    # -- simulation -------------------------------------------------------

    def _hop_points(self):
        a = self.blocks[self.jump_index]
        b = self.blocks[self.jump_index + 1]
        return a, b

    def update(self, dt: float) -> None:
        a, b = self._hop_points()
        self.jump_t += dt / self.jump_dur
        if self.jump_t >= 1.0:
            self.jump_t = 0.0
            self.jump_index += 1
            self.land_dip = 1.0
            self.distance += math.dist((a["x"], a["z"]), (b["x"], b["z"]))
            a, b = self._hop_points()
            gap = math.dist((a["x"], a["z"]), (b["x"], b["z"]))
            rise = b["y"] - a["y"]
            self.jump_dur = max(0.5, min(0.85, 0.42 + gap * 0.075 - rise * 0.03))
            # keep the horizon of generated course ahead of the player
            while len(self.blocks) - self.jump_index < AHEAD:
                self._spawn_block()
            if self.jump_index > TRAIL:
                drop = self.jump_index - TRAIL
                self.blocks = self.blocks[drop:]
                self.jump_index -= drop
            if self.islands and self.islands[0]["z"] > b["z"] + 90:
                self.islands.pop(0)
            while self._next_island_z > b["z"] - 260:
                self._spawn_island()

        self.land_dip = max(0.0, self.land_dip - dt * 6.0)
        self.burst.update(dt)

    # -- drawing ----------------------------------------------------------

    def _fog(self, dist: float, extra: float = 0.0, alpha: int = 255):
        f = max(0.0, min(1.0, dist / FOG_FAR + extra))
        f = f * f * (3 - 2 * f)
        return rl.rgba(rl.mix_rgb((255, 255, 255), self.palette.fog, f), alpha)

    def _shelf(self):
        if self._shelf_model is None:
            mesh = rl.ffi.new("Mesh *")
            verts = [(-0.5, 0, -0.25), (0.5, 0, -0.25), (0.5, 0, 0.25), (-0.5, 0, 0.25)]
            mesh.vertexCount = 4
            mesh.triangleCount = 2
            vb = rl.ffi.new("float[]", [c for v in verts for c in v])
            nb = rl.ffi.new("float[]", [0, 1, 0] * 4)
            tb = rl.ffi.new("float[]", [0, 0, 1, 0, 1, 1, 0, 1])
            ib = rl.ffi.new("unsigned short[]", [0, 2, 1, 0, 3, 2, 0, 1, 2, 0, 2, 3])
            mesh.vertices = vb; mesh.normals = nb; mesh.texcoords = tb; mesh.indices = ib
            self._keep = (vb, nb, tb, ib, mesh)
            rl.UploadMesh(mesh, False)
            self._shelf_model = rl.LoadModelFromMesh(mesh[0])
        return self._shelf_model

    def draw(self) -> None:
        pal = self.palette
        self.sky.draw(self.elapsed)

        a, b = self._hop_points()
        t = self.jump_t
        ease = t * t * (3 - 2 * t)
        x = a["x"] + (b["x"] - a["x"]) * ease
        z = a["z"] + (b["z"] - a["z"]) * ease
        rise = b["y"] - a["y"]
        apex = 1.05 + max(0.0, -rise) * 0.12
        y = a["y"] + (b["y"] - a["y"]) * t + apex * 4 * t * (1 - t) * 1.0
        y += 1.0  # stand on top of the block, block centres are at ["y"]

        target_yaw = math.atan2(b["x"] - x, -(b["z"] - z))
        dy = target_yaw - self.yaw
        while dy > math.pi:
            dy -= 2 * math.pi
        while dy < -math.pi:
            dy += 2 * math.pi
        self.yaw += dy * 0.08
        dip = math.sin(min(1.0, 1.0 - self.land_dip) * math.pi) * 0.0 + self.land_dip * 0.16

        cam = self.camera
        eye_y = y + EYE - dip
        cam.position = (x, eye_y, z)
        look = 5.5
        cam.target = (x + math.sin(self.yaw) * look,
                      eye_y - 1.45,
                      z - math.cos(self.yaw) * look)
        cam.fovy = 70.0

        rl.BeginMode3D(cam[0])

        # ocean far below; aerial perspective is added as a 2D haze band after
        # the 3D pass, which grades smoothly where geometry strips cannot
        deep = rl.mix_rgb(pal.sky_top, (8, 52, 110), 0.62)
        rl.DrawPlane((x, 0.0, z - 60), (760, 760), rl.rgba(deep, 255))

        # islands
        for isl in self.islands:
            for c in isl["cubes"]:
                bx, bz = isl["x"] + c["dx"], isl["z"] + c["dz"]
                dist = math.dist((x, z), (bx, bz))
                voxel.draw_block(self.grass, bx, c["y"] + c["s"] / 2, bz,
                                 self._fog(dist * 0.62, BELOW_FOG * 0.4), c["s"])

        # cloud shelves drift below the course
        shelf = self._shelf()
        for s in self.shelves:
            sx = s["x"] + math.sin(self.elapsed * 0.05 * s["drift"]) * 6
            sz = s["z"]
            if sz > z + 60:
                s["z"] -= 260
                continue
            shelf.materials[0].maps[rl.MATERIAL_MAP_ALBEDO].texture = s["tex"]
            rl.DrawModelEx(shelf, (sx, s["y"], sz), (0, 1, 0), 0.0,
                           (s["s"], 1.0, s["s"]), (255, 255, 255, 150))

        # Aerial perspective over the world below only: leave 3D, lay a smooth
        # alpha fade from the horizon down, then re-enter the same camera for
        # the course. The haze writes no depth, so the course draws over it
        # while still depth-testing correctly against the islands.
        rl.EndMode3D()
        band = textures.alpha_band(f"haze-{self.ctx.seed.run}", pal.fog, 205, 1.5)
        horizon = int(self.height * 0.408)
        rl.DrawTexturePro(band, (0, 0, 4, 128),
                          (0, horizon, self.width, int(self.height * 0.38)),
                          (0, 0), 0.0, rl.WHITE4)
        rl.BeginMode3D(cam[0])

        # the course
        for i, blk in enumerate(self.blocks):
            dist = math.dist((x, z), (blk["x"], blk["z"]))
            style = self.ice if blk["style"] == "ice" else self.styles[blk["style"]]
            tint = self._fog(dist)
            if blk["wide"]:
                for ox in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        voxel.draw_block(style, blk["x"] + ox, blk["y"] + 0.5,
                                         blk["z"] + oz, tint)
            else:
                voxel.draw_block(style, blk["x"], blk["y"] + 0.5, blk["z"], tint)

        self.burst.draw(self.camera)
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        text(f"{int(self.distance)}m", self.width - 12, 10, 20, pal.ink,
             anchor="topright")
