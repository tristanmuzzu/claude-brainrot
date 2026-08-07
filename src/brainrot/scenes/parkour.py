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

Two things carry more of the "this is Minecraft" reading than any amount of
terrain: the held block swinging in the corner of the frame, and the crosshair
in the middle of it. Both are here, because a first-person shot without them
reads as a generic flying camera.
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

        # What the player is carrying, and the arm holding it. Deliberately a
        # stone grey rather than one of the palette's course colours: a held
        # block in the same candy family as the platforms just reads as
        # another platform floating oddly close to the lens.
        self.held = voxel.block_model("held-stone", (122, 122, 130),
                                      noise=0.07, seed=91)
        self.sleeve = voxel.block_model(f"run{seed.run}-sleeve", pal.accent,
                                        noise=0.03, seed=seed.run * 13 + 4)
        self.skin = voxel.block_model("hand-skin", (198, 148, 112),
                                      noise=0.03, seed=17)
        self.swing = 0.0

        self.rng = ctx.stream("course")
        self.irng = ctx.stream("islands")

        # course: list of dicts {x, y, z, style, wide}
        self.blocks: list[dict] = []
        self.heading = 0.0            # radians, 0 = -Z
        self.lateral = 0.0            # drift from the spine, for the director
        self._spawn_block(first=True)
        while len(self.blocks) < AHEAD:
            self._spawn_block()

        # -- motion: a ground/air state machine, not a tween ---------------
        # Real parkour footage has a beat ON each block (land, settle, aim)
        # and a ballistic arc between them: constant horizontal velocity,
        # gravity vertically. Easing positions between block centres reads as
        # teleportation, which is exactly what this replaces.
        self.hop_rng = ctx.stream("hops")
        self.jump_index = 0           # block we are standing on
        self.phase = "ground"
        self.phase_t = 0.0
        self.ground_dur = 0.5
        self.air_dur = 0.6
        first = self.blocks[0]
        self.stand = [first["x"], first["y"] + 1.0, first["z"]]
        self.takeoff = list(self.stand)
        self.land_at = list(self.stand)
        self.vy0 = 0.0
        self.pos = list(self.stand)
        self.vy = 0.0
        self.land_dip = 0.0
        self.distance = 0.0
        self.yaw = self.heading
        self._roll = 0.0

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
        # Gaussian sideways drift, steered back toward the spine. Candidate
        # headings fan out from the drifted one and the first that does not
        # land on recent course wins -- the reference generator likewise
        # refuses self-overlapping placements.
        drift = rng.gauss(0.0, 0.55)
        steer = -0.028 * self.lateral
        preferred = max(-0.9, min(0.9, self.heading + drift * 0.22 + steer))
        recent = self.blocks[-7:-1]

        def landing(heading: float, step: float):
            return (prev["x"] + math.sin(heading) * step,
                    prev["z"] - math.cos(heading) * step)

        best, best_clearance = preferred, -1.0
        step = gap + 1.0
        for fan in (0.0, 0.2, -0.2, 0.45, -0.45, 0.7, -0.7):
            heading = max(-1.1, min(1.1, preferred + fan))
            nx, nz = landing(heading, step)
            clearance = min((math.dist((nx, nz), (b["x"], b["z"])) for b in recent),
                            default=99.0)
            if clearance > 1.45:
                best = heading
                break
            if clearance > best_clearance:
                best, best_clearance = heading, clearance
        self.heading = best
        dx = math.sin(best) * step
        dz = -math.cos(best) * step
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

    GRAVITY = 26.0
    HOP_SPEED = 5.3               # horizontal m/s while airborne

    def _landing_point(self, blk: dict) -> list[float]:
        """Land somewhere ON the block, not at its centre -- nobody lands
        dead-centre every jump, and the wander is what makes the next
        takeoff angle (and therefore the camera) feel alive."""
        margin = 0.9 if blk["wide"] else 0.24
        return [blk["x"] + self.hop_rng.uniform(-margin, margin),
                blk["y"] + 1.0,
                blk["z"] + self.hop_rng.uniform(-margin, margin)]

    def _begin_air(self) -> None:
        target = self.blocks[self.jump_index + 1]
        self.takeoff = list(self.stand)
        self.land_at = self._landing_point(target)
        dist = math.dist((self.takeoff[0], self.takeoff[2]),
                         (self.land_at[0], self.land_at[2]))
        self.air_dur = max(0.42, min(0.80, dist / self.HOP_SPEED))
        dy = self.land_at[1] - self.takeoff[1]
        # launch speed that lands exactly on target under gravity
        self.vy0 = dy / self.air_dur + 0.5 * self.GRAVITY * self.air_dur
        self.phase = "air"
        self.phase_t = 0.0

    def _land(self) -> None:
        self.jump_index += 1
        self.stand = list(self.land_at)
        self.pos = list(self.stand)
        self.phase = "ground"
        self.phase_t = 0.0
        self.land_dip = 1.0
        self.swing = 1.0
        # a scuff of block-coloured dust at the feet, kicked up by the landing
        blk = self.blocks[min(self.jump_index, len(self.blocks) - 1)]
        tint = self.palette.blocks[blk["style"] % len(self.palette.blocks)] \
            if blk["style"] != "ice" else (200, 232, 250)
        self.burst.spawn(self.stand[0], self.stand[1] - 0.9, self.stand[2],
                         tint, count=7, speed=1.6, rng=self.hop_rng)
        self.distance += math.dist((self.takeoff[0], self.takeoff[2]),
                                   (self.stand[0], self.stand[2]))
        landed_on = self.blocks[self.jump_index]
        # a proper breather on checkpoint platforms, a beat everywhere else
        self.ground_dur = (self.hop_rng.uniform(0.5, 0.9) if landed_on["wide"]
                           else self.hop_rng.uniform(0.10, 0.26))

        # keep the horizon of generated course ahead of the player
        while len(self.blocks) - self.jump_index < AHEAD:
            self._spawn_block()
        if self.jump_index > TRAIL:
            drop = self.jump_index - TRAIL
            self.blocks = self.blocks[drop:]
            self.jump_index -= drop
        z_here = self.stand[2]
        if self.islands and self.islands[0]["z"] > z_here + 90:
            self.islands.pop(0)
        while self._next_island_z > z_here - 260:
            self._spawn_island()

    def update(self, dt: float) -> None:
        self.phase_t += dt
        if self.phase == "ground":
            self.pos = list(self.stand)
            self.vy = 0.0
            if self.phase_t >= self.ground_dur:
                self._begin_air()
        else:
            t = min(self.phase_t, self.air_dur)
            f = t / self.air_dur
            self.pos[0] = self.takeoff[0] + (self.land_at[0] - self.takeoff[0]) * f
            self.pos[2] = self.takeoff[2] + (self.land_at[2] - self.takeoff[2]) * f
            self.pos[1] = self.takeoff[1] + self.vy0 * t - 0.5 * self.GRAVITY * t * t
            self.vy = self.vy0 - self.GRAVITY * t
            if self.phase_t >= self.air_dur:
                self._land()

        self.land_dip = max(0.0, self.land_dip - dt * 5.0)
        self.swing = max(0.0, self.swing - dt * 2.6)
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

        x, y, z = self.pos

        # Aim: mid-air, at where we will land; on the ground, pre-aim toward
        # the NEXT landing so the turn happens as a deliberate look, not a
        # camera glued to a moving block.
        if self.phase == "air":
            aim = self.land_at
            ease = 0.14
        else:
            # aim through the course, not at one block: averaging the next
            # few keeps more of the run in frame through bends
            idx = self.jump_index
            ahead = self.blocks[min(idx + 1, len(self.blocks) - 1):
                                min(idx + 4, len(self.blocks))]
            aim = (sum(b["x"] for b in ahead) / len(ahead),
                   sum(b["y"] + 1.0 for b in ahead) / len(ahead),
                   sum(b["z"] for b in ahead) / len(ahead))
            ease = 0.06
        target_yaw = math.atan2(aim[0] - x, -(aim[2] - z))
        dy = target_yaw - self.yaw
        while dy > math.pi:
            dy -= 2 * math.pi
        while dy < -math.pi:
            dy += 2 * math.pi
        self.yaw += dy * ease
        # a touch of roll into the turn sells the head motion
        self._roll += (max(-0.05, min(0.05, dy * 0.35)) - self._roll) * 0.1

        # landing dip with a small overshoot, plus an idle breath on ground
        dip = self.land_dip ** 1.4 * 0.17 - math.sin(self.land_dip * math.pi) * 0.02
        breathe = math.sin(self.elapsed * 2.1) * 0.012 if self.phase == "ground" else 0.0

        cam = self.camera
        eye_y = y + EYE - dip + breathe
        cam.position = (x, eye_y, z)
        look = 5.5
        # pitch follows vertical velocity: rising lifts the gaze, falling
        # drops it toward the landing block. Base pitch keeps the horizon
        # near mid-frame like the reference footage.
        pitch_drop = 1.1 - max(-0.6, min(0.85, self.vy * 0.1))
        cam.target = (x + math.sin(self.yaw) * look,
                      eye_y - pitch_drop,
                      z - math.cos(self.yaw) * look)
        # roll: tilt the up vector about the view direction
        fx, fz = math.sin(self.yaw), -math.cos(self.yaw)
        cam.up = (math.sin(self._roll) * -fz, math.cos(self._roll), math.sin(self._roll) * fx)
        cam.fovy = 70.0 + (2.5 if self.phase == "air" else 0.0)

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
        self._draw_held()
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        self._draw_crosshair()
        text(f"{int(self.distance)}m", self.width - 12, 10, 20, pal.ink,
             anchor="topright")

    # -- first person -----------------------------------------------------

    def _camera_basis(self):
        """Right / up / forward of the current view, orthonormal."""
        cam = self.camera
        px, py, pz = cam.position.x, cam.position.y, cam.position.z
        fx, fy, fz = cam.target.x - px, cam.target.y - py, cam.target.z - pz
        fl = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / fl, fy / fl, fz / fl
        ux, uy, uz = cam.up.x, cam.up.y, cam.up.z
        rx, ry, rz = fy * uz - fz * uy, fz * ux - fx * uz, fx * uy - fy * ux
        rl_ = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
        rx, ry, rz = rx / rl_, ry / rl_, rz / rl_
        # re-derive up so the three are exactly orthogonal even with roll on
        ux, uy, uz = ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx
        return (rx, ry, rz), (ux, uy, uz), (fx, fy, fz)

    def _view_matrix(self, right, up, forward):
        """A rotation that puts model +X along ``right``, +Y up, +Z back.

        Built by hand rather than composed from yaw and pitch: the camera also
        rolls into its turns, and a model oriented from Euler angles ignores
        that and shears away from the frame it is supposed to be pinned to.
        """
        m = rl.ffi.new("Matrix *")
        m.m0, m.m1, m.m2, m.m3 = right[0], right[1], right[2], 0.0
        m.m4, m.m5, m.m6, m.m7 = up[0], up[1], up[2], 0.0
        m.m8, m.m9, m.m10, m.m11 = -forward[0], -forward[1], -forward[2], 0.0
        m.m12, m.m13, m.m14, m.m15 = 0.0, 0.0, 0.0, 1.0
        return m[0]

    def _draw_held(self) -> None:
        """The block in your hand, bobbing in the corner of the frame.

        Positioned from the camera basis rather than in screen space, so it
        picks up the same perspective as the world and swings with the head.
        Drawn last and very close in, which puts it in front of everything
        without needing its own pass.
        """
        cam = self.camera
        right, up, forward = self._camera_basis()
        px, py, pz = cam.position.x, cam.position.y, cam.position.z

        # Size everything against the actual frustum at the distance it is
        # drawn, so the hand keeps its share of the frame whatever the field
        # of view does -- and this view widens by 2.5 degrees in mid-air.
        near = 0.5
        half_h = near * math.tan(math.radians(cam.fovy * 0.5))
        half_w = half_h * (self.width / self.height)

        t = self.elapsed
        bob_x = math.sin(t * 4.6) * 0.05
        bob_y = abs(math.cos(t * 4.6)) * 0.05
        punch = self.swing ** 1.5

        def place(model, u, v, off_f, size, yaw, tilt):
            """u, v are fractions of the half-frame: (1, -1) is bottom-right."""
            off_r, off_u = u * half_w, v * half_h
            x = px + forward[0] * (near + off_f) + right[0] * off_r + up[0] * off_u
            y = py + forward[1] * (near + off_f) + right[1] * off_r + up[1] * off_u
            z = pz + forward[2] * (near + off_f) + right[2] * off_r + up[2] * off_u
            basis = self._view_matrix(right, up, forward)
            spin = rl.MatrixMultiply(rl.MatrixRotateX(math.radians(tilt)),
                                     rl.MatrixRotateY(math.radians(yaw)))
            model.transform = rl.MatrixMultiply(spin, basis)
            rl.DrawModelEx(model, (x, y, z), (0, 1, 0), 0.0,
                           (size[0] * half_w, size[1] * half_w, size[2] * half_w),
                           rl.WHITE4)

        # Forearm out of the bottom-right corner, hand, then the block it is
        # carrying -- turned so two faces are visible, which is what makes a
        # cube read as a cube rather than a coloured square.
        # Sat well into the corner with part of it past the frame edge, the
        # way a held item actually sits -- fully inside the frame it stops
        # being scenery you look past and becomes an object you look at.
        drop = -1.06 - bob_y * 0.6 - punch * 0.34
        place(self.sleeve, 1.08 + bob_x * 0.3, drop - 0.66, 0.02,
              (0.34, 1.30, 0.34), yaw=-26.0, tilt=-24.0 + punch * 10.0)
        place(self.skin, 0.94 + bob_x * 0.4, drop - 0.10, 0.01,
              (0.34, 0.34, 0.34), yaw=-26.0, tilt=-24.0 + punch * 10.0)
        place(self.held, 0.82 + bob_x * 0.5, drop + 0.24, 0.05,
              (0.50, 0.50, 0.50), yaw=-32.0, tilt=-16.0 + punch * 14.0)

    def _draw_crosshair(self) -> None:
        """Centre-screen, dark-edged so it survives a bright sky.

        Minecraft's own crosshair inverts whatever is behind it. There is no
        blend mode here that does that, and plain white vanishes against the
        sun -- so it gets a dark outline and a light core, which reads on
        anything.
        """
        cx, cy = self.width // 2, self.height // 2
        arm = 8
        for pad, color in ((1, (20, 20, 24, 150)), (0, (238, 238, 242, 225))):
            t = 2 + pad * 2
            rl.DrawRectangle(cx - arm - pad, cy - t // 2, (arm + pad) * 2, t, color)
            rl.DrawRectangle(cx - t // 2, cy - arm - pad, t, (arm + pad) * 2, color)
