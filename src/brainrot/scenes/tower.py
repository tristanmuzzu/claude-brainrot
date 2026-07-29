"""Voxel parkour tower.

A blocky spire generated from the top down, with a figure hopping its way to the
bottom while the camera orbits.

**Path first, geometry second.** The descent route is generated before a single
block exists: a spiral of nodes whose vertical drop and horizontal reach are
clamped to what a jump can actually cover. The tower is then built *around*
that route. Generating a tower and then searching it for a route would mean
sometimes finding none, and there is no good answer to that inside a render
loop.

**Faces, not lighting.** Each cube draws at most three faces at three fixed
brightness levels. It is the oldest voxel trick there is and it stays legible
at 360 pixels wide, where any real shading model turns to mush.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from ..engine import postfx
from ..engine.draw import Particles, text
from ..engine.projection import Camera, ease_in_out, fogged, project
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import Sky
from ..engine.texture import ambient_occlusion, apply_texels, edge_shade, texel_pattern
from ..palette import RGB, lerp_rgb, shade

BLOCK = 1.0
#: Vertical drop per path step. Kept modest so the hop always looks survivable.
DROP_MIN, DROP_MAX = 1.0, 2.0
#: Horizontal reach per step, in blocks. Beyond ~3 the jump stops reading.
REACH_MIN, REACH_MAX = 1.6, 3.0
HOP_TIME = 0.46
#: Orbit distance. Close enough that blocks have readable surface detail, far
#: enough that the whole spire and the route spiralling down it are in frame --
#: at 12 the tower filled the strip and the descent was invisible.
CAMERA_RADIUS = 21.0

#: How many of the nearest blocks get texels, ambient occlusion and fringing.
#: A hard cap keeps the frame cost flat regardless of how large a tower the
#: generator produced -- texturing every face of every block cost roughly 9,600
#: polygon draws a frame and dominated the whole process.
DETAIL_BUDGET = {"high": 60, "balanced": 32, "low": 0}


@dataclass
class Block:
    x: float
    y: float
    z: float
    color: RGB
    size: float = BLOCK
    #: Which texel pattern to draw on this block's faces.
    material: str = "stone"
    #: Grass blocks get a fringe of top colour bleeding down their sides -- the
    #: single most recognisable detail in the whole voxel idiom.
    fringe: bool = False


@dataclass
class Node:
    x: float
    y: float
    z: float


@register("tower")
class TowerScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        self.rng = ctx.stream("tower-shape")
        self.rng_decor = ctx.stream("tower-decor")

        self.cam = Camera(y=0.0, horizon=0.42, far=78.0, focal=self.height * 0.82)
        self.yaw = 0.0
        self.blocks: list[Block] = []
        self.path: list[Node] = []

        self.hop_index = 0
        self.hop_t = 0.0
        self.player_pos = (0.0, 0.0, 0.0)
        self.height_climbed = 0.0

        self.particles = Particles(self.palette, self.width, self.height, ctx.stream("weather"))

        art = ctx.stream("tower-art")
        self.sky = Sky(self.palette, self.width, self.height, art, horizon=self.cam.horizon)
        self.texels = {
            name: texel_pattern(name, art) for name in ("stone", "grass", "wood", "generic")
        }
        # Grass and foliage do not inherit the run's hue: a purple lawn reads as
        # a bug, however consistent it is with the palette.
        self.grass = lerp_rgb((104, 168, 74), self.palette.accent, 0.18)
        self.soil = (108, 82, 58)
        # Fixed character colours, for the same reason the runner has them: the
        # figure has to stay legible against every palette this can generate.
        self.skin_tone = (232, 178, 136)
        self.shirt = lerp_rgb(self.palette.accent, (255, 255, 255), 0.25)
        self.legs = (52, 62, 92)

        self._detail_budget = DETAIL_BUDGET.get(ctx.quality, 60)

        self._generate()

    # -- generation -------------------------------------------------------

    def _generate(self) -> None:
        """Build a fresh tower: route first, then the structure around it."""
        self.blocks.clear()
        self.path.clear()

        rng = self.rng
        steps = rng.randint(24, 34)
        radius = rng.uniform(4.0, 7.0)
        angle = rng.uniform(0.0, math.tau)
        # Consistent spin direction per tower reads as a deliberate spiral
        # rather than a random walk that happens to go down.
        spin = rng.choice((-1, 1))
        y = float(steps) * 1.6

        for i in range(steps):
            # Advance far enough around the axis that the next platform is a
            # real jump, but never further than REACH_MAX of arc.
            drop = rng.uniform(DROP_MIN, DROP_MAX)
            reach = rng.uniform(REACH_MIN, REACH_MAX)
            radius = max(3.0, min(9.0, radius + rng.uniform(-0.7, 0.7)))
            angle += spin * (reach / max(1.0, radius))
            y -= drop

            node = Node(x=math.sin(angle) * radius, y=y, z=math.cos(angle) * radius)
            self.path.append(node)
            self._build_platform(node, i, steps)

        self._build_core(y, self.path[0].y)
        self.player_pos = (self.path[0].x, self.path[0].y + 1.0, self.path[0].z)

    def _build_platform(self, node: Node, index: int, total: int) -> None:
        """A small slab under a path node, plus occasional decoration."""
        rng = self.rng_decor
        pal = self.palette

        # Platforms alternate material so successive hops are visually countable
        # and the tower is not one texture from top to bottom.
        checkpoint = index % 4 == 0
        if checkpoint:
            base, material, fringe = pal.accent, "generic", False
        else:
            base, material, fringe = self.grass, "grass", True
        width = rng.choice((1, 1, 2, 2, 3))

        for dx in range(-(width // 2), width // 2 + 1):
            for dz in range(-(width // 2), width // 2 + 1):
                tint = 0.88 + rng.random() * 0.24
                self.blocks.append(
                    Block(
                        x=node.x + dx * BLOCK,
                        y=node.y,
                        z=node.z + dz * BLOCK,
                        color=shade(base, tint),
                        material=material,
                        fringe=fringe,
                    )
                )

        # Occasional overhang above the platform for silhouette interest.
        if rng.random() < 0.18:
            self.blocks.append(
                Block(
                    x=node.x + rng.choice((-1, 1)) * BLOCK,
                    y=node.y + 2 * BLOCK,
                    z=node.z,
                    color=shade(pal.structure, 0.8),
                    material="wood",
                )
            )

    def _build_core(self, bottom: float, top: float) -> None:
        """The central pillar the route spirals around."""
        rng = self.rng_decor
        pal = self.palette
        y = bottom
        while y <= top:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    # The centre column is enclosed on all four sides and by the
                    # levels above and below, so it can never be seen. Not
                    # generating it is free geometry removed from every frame.
                    if dx == 0 and dz == 0:
                        continue
                    # Corners are chipped away for silhouette variety, but the
                    # cross-shaped remainder is unbroken: a pillar with gaps in
                    # it reads as floating debris, not as a tower.
                    if abs(dx) == 1 and abs(dz) == 1 and rng.random() < 0.45:
                        continue
                    self.blocks.append(
                        Block(
                            x=dx * BLOCK,
                            y=y,
                            z=dz * BLOCK,
                            color=shade(pal.ground, 0.85 + rng.random() * 0.3),
                        )
                    )
            y += BLOCK

    # -- view transform ---------------------------------------------------

    def _to_view(self, wx: float, wy: float, wz: float) -> tuple[float, float, float]:
        """World to camera space.

        The shared projection has no yaw, so the orbit is applied here: rotate
        the world about the tower axis, then hand a plain forward-looking camera
        the result. Keeping rotation local to the scene that needs it leaves
        :mod:`projection` small enough to reason about.
        """
        sin_y, cos_y = math.sin(self.yaw), math.cos(self.yaw)
        cam_x, cam_z = sin_y * CAMERA_RADIUS, cos_y * CAMERA_RADIUS
        dx, dz = wx - cam_x, wz - cam_z
        depth = dx * -sin_y + dz * -cos_y
        right = dx * cos_y + dz * -sin_y
        return right, wy, depth

    def _project(self, wx: float, wy: float, wz: float):
        right, up, depth = self._to_view(wx, wy, wz)
        return project(self.cam, right, up, depth, self.width, self.height)

    # -- simulation -------------------------------------------------------

    def update(self, dt: float) -> None:
        if len(self.path) < 2:
            return

        self.hop_t += dt
        while self.hop_t >= HOP_TIME:
            self.hop_t -= HOP_TIME
            self.hop_index += 1
            if self.hop_index >= len(self.path) - 1:
                # Reached the bottom -- build a brand new tower and keep going.
                self._generate()
                self.hop_index = 0

        a = self.path[self.hop_index]
        b = self.path[min(self.hop_index + 1, len(self.path) - 1)]
        t = self.hop_t / HOP_TIME
        smooth = ease_in_out(t)

        x = a.x + (b.x - a.x) * smooth
        z = a.z + (b.z - a.z) * smooth
        # Parabolic arc on top of the linear descent, so the hop pops.
        y = a.y + (b.y - a.y) * smooth + math.sin(t * math.pi) * 0.85 + 1.0
        self.player_pos = (x, y, z)

        # Camera trails the player's angle rather than snapping to it.
        target_yaw = math.atan2(x, z)
        delta = (target_yaw - self.yaw + math.pi) % math.tau - math.pi
        self.yaw += delta * min(1.0, dt * 2.2)
        self.cam.y = y + 5.5

        self.particles.update(dt)
        self.sky.update(dt, wind=0.5)

    # -- rendering --------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        pal = self.palette
        self.sky.draw(surface, parallax=self.yaw * 40.0)

        # Depth-sort every cube once per frame, far to near. At a few hundred
        # blocks this is cheaper than any spatial structure would be to maintain.
        visible: list[tuple[float, Block]] = []
        # Depth of the tower's own axis. Core blocks further away than this are
        # on the far side of a solid pillar and cannot be seen through it, so
        # they are dropped before projection rather than drawn and then painted
        # over -- roughly half the core, every frame.
        self._view_basis = (
            math.sin(self.yaw),
            math.cos(self.yaw),
            math.sin(self.yaw) * CAMERA_RADIUS,
            math.cos(self.yaw) * CAMERA_RADIUS,
        )
        axis_depth = self._to_view(0.0, 0.0, 0.0)[2]
        for block in self.blocks:
            _r, _u, depth = self._to_view(block.x, block.y, block.z)
            if depth <= 1.0 or depth > self.cam.far:
                continue
            # Cull anything far above or below the camera before projecting.
            if abs(block.y - self.cam.y) > 40:
                continue
            if abs(block.x) <= 1.05 and abs(block.z) <= 1.05 and depth > axis_depth + 0.25:
                continue
            visible.append((depth, block))

        visible.sort(key=lambda item: -item[0])

        # Surface detail is capped to a fixed budget of the *nearest* blocks
        # rather than applied to everything in view. Texturing every face of
        # every block cost around 9,600 polygon draws per frame and dominated
        # the whole process; the far ones are a handful of pixels across and
        # nobody can tell they are flat.
        detail_from = max(0, len(visible) - self._detail_budget)
        for index, (depth, block) in enumerate(visible):
            self._draw_cube(surface, block, depth, detailed=index >= detail_from)

        self._draw_player(surface)
        self.particles.draw(surface)

        postfx.apply_all(
            surface,
            bloom_threshold=postfx.auto_threshold(pal.sky_bottom),
            bloom_intensity=0.85 if pal.time_of_day == "night" else 0.45,
            vignette_strength=0.32,
            quality=self.ctx.quality,
        )
        self._draw_hud(surface)

    def _draw_cube(
        self, surface: pygame.Surface, block: Block, depth: float, detailed: bool = True
    ) -> None:
        """Three faces, three brightness levels.

        The corner transform is written out inline rather than going through
        :meth:`_project`. Eight corners per cube across hundreds of cubes was
        thousands of function calls and thousands of ``Projected`` allocations
        every frame, and it was the largest single cost in the scene. The maths
        is identical -- yaw rotation about the tower axis, then perspective
        divide -- it just does not build an object per corner.
        """
        pal = self.palette
        s = block.size
        x, y, z = block.x, block.y, block.z

        cam = self.cam
        sin_y, cos_y, cam_x, cam_z = self._view_basis
        half_w = self.width * 0.5
        horizon_px = self.height * cam.horizon
        focal = cam.focal
        cam_y = cam.y

        half = s * 0.5
        top_y = y + s * 0.5
        bottom_y = y - s * 0.5

        top_pts: list[tuple[float, float]] = []
        bottom_pts: list[tuple[float, float]] = []
        for dx, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            wx = x + dx * half
            wz = z + dz * half
            ox, oz = wx - cam_x, wz - cam_z
            corner_depth = ox * -sin_y + oz * -cos_y
            if corner_depth <= 0.4:
                return
            scale = focal / corner_depth
            sx = half_w + (ox * cos_y + oz * -sin_y) * scale
            top_pts.append((sx, horizon_px + (cam_y - top_y) * scale))
            bottom_pts.append((sx, horizon_px + (cam_y - bottom_y) * scale))

        colour_top = fogged(cam, pal.face(block.color, "top"), depth, pal.fog)
        colour_side = fogged(cam, pal.face(block.color, "side"), depth, pal.fog)
        colour_front = fogged(cam, pal.face(block.color, "front"), depth, pal.fog)

        # Only the two vertical faces pointing at the camera are drawn; which
        # ones those are falls out of the sign of the block's view-space offset.
        right = (x - cam_x) * cos_y + (z - cam_z) * -sin_y
        sign_x = 1 if right < 0 else -1

        texels = self.texels.get(block.material, self.texels["stone"])
        # Offsetting the shared pattern by the block's own position stops a wall
        # of one material looking like the same tile stamped over and over.
        uv_offset = ((block.x * 0.37 + block.y * 0.11) % 1.0, (block.z * 0.29) % 1.0)

        def quad(indices) -> list[tuple[float, float]]:
            return [top_pts[i] if kind == "t" else bottom_pts[i] for i, kind in indices]

        # Near vertical face (the one closest to the camera in depth).
        near_idx = 0 if sign_x > 0 else 2
        side_a = (near_idx + 1) % 4
        side_b = (near_idx + 2) % 4

        faces = (
            (quad([(near_idx, "t"), (near_idx + 1, "t"), (near_idx + 1, "b"), (near_idx, "b")]), colour_front),
            (quad([(side_a, "t"), (side_b, "t"), (side_b, "b"), (side_a, "b")]), colour_side),
        )

        for corners, colour in faces:
            pygame.draw.polygon(surface, colour, corners)
            if detailed:
                apply_texels(surface, corners, texels, colour, offset=uv_offset)
                if block.fringe:
                    # Top quarter of each side face takes the top colour, which
                    # is what makes a grass block read as grass rather than as a
                    # green cube.
                    a, b, c, d = corners
                    band = [
                        a,
                        b,
                        (b[0] + (c[0] - b[0]) * 0.28, b[1] + (c[1] - b[1]) * 0.28),
                        (a[0] + (d[0] - a[0]) * 0.28, a[1] + (d[1] - a[1]) * 0.28),
                    ]
                    pygame.draw.polygon(surface, colour_top, band)
                ambient_occlusion(surface, corners, colour)
                edge_shade(surface, corners, shade(colour, 0.55), 1)

        # Top last: the camera always sits above the blocks it can see.
        top_quad = top_pts
        pygame.draw.polygon(surface, colour_top, top_quad)
        if detailed:
            apply_texels(surface, top_quad, texels, colour_top, offset=uv_offset)
            ambient_occlusion(surface, top_quad, colour_top)
            edge_shade(surface, top_quad, shade(colour_top, 0.6), 1)

    def _draw_player(self, surface: pygame.Surface) -> None:
        """A blocky figure built from the same cubes as the tower.

        Drawing it as flat screen-space rectangles made it the one thing in the
        scene with no perspective, so it read as a UI element pasted over the
        world rather than as something standing in it.
        """
        x, y, z = self.player_pos
        _r, _u, depth = self._to_view(x, y, z)
        if depth <= 1.0:
            return

        # Legs swing through the hop so the figure is not a rigid statue.
        swing = math.sin(self.hop_t / HOP_TIME * math.pi) * 0.20
        parts = (
            (-0.17, 0.10 + swing, 0.0, 0.30, self.legs),
            (0.17, 0.10 - swing, 0.0, 0.30, self.legs),
            (0.0, 0.48, 0.0, 0.46, self.shirt),
            (0.0, 0.90, 0.0, 0.40, self.skin_tone),
        )
        for dx, dy, dz, size, colour in parts:
            self._draw_cube(
                surface,
                Block(x=x + dx, y=y + dy, z=z + dz, color=colour, size=size, material="generic"),
                depth,
            )

    def _draw_hud(self, surface: pygame.Surface) -> None:
        pal = self.palette
        remaining = max(0, len(self.path) - self.hop_index - 1)
        text(surface, f"{remaining} to go", self.width - 10, 8, size=18, color=pal.ink, anchor="topright")
        text(surface, f"{pal.time_of_day} · {pal.weather}", 10, 8, size=12, color=pal.ink)
