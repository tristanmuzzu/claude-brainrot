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

from ..engine.draw import Particles, text, vertical_gradient, vignette
from ..engine.projection import Camera, ease_in_out, fogged, project
from ..engine.scene import Scene, SceneContext, register
from ..palette import RGB, lerp_rgb, shade

BLOCK = 1.0
#: Vertical drop per path step. Kept modest so the hop always looks survivable.
DROP_MIN, DROP_MAX = 1.0, 2.0
#: Horizontal reach per step, in blocks. Beyond ~3 the jump stops reading.
REACH_MIN, REACH_MAX = 1.6, 3.0
HOP_TIME = 0.46
CAMERA_RADIUS = 12.0


@dataclass
class Block:
    x: float
    y: float
    z: float
    color: RGB
    size: float = BLOCK


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

        self.cam = Camera(y=0.0, horizon=0.45, far=70.0, focal=self.height * 0.7)
        self.yaw = 0.0
        self.blocks: list[Block] = []
        self.path: list[Node] = []

        self.hop_index = 0
        self.hop_t = 0.0
        self.player_pos = (0.0, 0.0, 0.0)
        self.height_climbed = 0.0

        self.particles = Particles(self.palette, self.width, self.height, ctx.stream("weather"))
        self._generate()

    # -- generation -------------------------------------------------------

    def _generate(self) -> None:
        """Build a fresh tower: route first, then the structure around it."""
        self.blocks.clear()
        self.path.clear()

        rng = self.rng
        steps = rng.randint(26, 44)
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

        # Platforms alternate tint so successive hops are visually countable.
        base = pal.accent if index % 4 == 0 else pal.structure
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
        self.cam.y = y + 4.5

        self.particles.update(dt)

    # -- rendering --------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        pal = self.palette
        surface.blit(vertical_gradient(self.width, self.height, pal.sky_top, pal.sky_bottom), (0, 0))
        if "stars" in pal.particles:
            self.particles.draw(surface)

        # Depth-sort every cube once per frame, far to near. At a few hundred
        # blocks this is cheaper than any spatial structure would be to maintain.
        visible: list[tuple[float, Block]] = []
        for block in self.blocks:
            _r, _u, depth = self._to_view(block.x, block.y, block.z)
            if depth <= 1.0 or depth > self.cam.far:
                continue
            # Cull anything far above or below the camera before projecting.
            if abs(block.y - self.cam.y) > 40:
                continue
            visible.append((depth, block))

        visible.sort(key=lambda item: -item[0])
        for depth, block in visible:
            self._draw_cube(surface, block, depth)

        self._draw_player(surface)

        if "stars" not in pal.particles:
            self.particles.draw(surface)

        vignette(surface, 0.42)
        self._draw_hud(surface)

    def _draw_cube(self, surface: pygame.Surface, block: Block, depth: float) -> None:
        """Three faces, three brightness levels."""
        pal = self.palette
        s = block.size
        x, y, z = block.x, block.y, block.z

        # Corners named by (dx, dz) in world space; y0 bottom, y1 top.
        def corner(dx: float, dz: float, dy: float):
            return self._project(x + dx * s * 0.5, y + dy * s, z + dz * s * 0.5)

        top_pts = [corner(-1, -1, 0.5), corner(1, -1, 0.5), corner(1, 1, 0.5), corner(-1, 1, 0.5)]
        if any(p is None for p in top_pts):
            return

        colour_top = fogged(self.cam, pal.face(block.color, "top"), depth, pal.fog)
        colour_side = fogged(self.cam, pal.face(block.color, "side"), depth, pal.fog)
        colour_front = fogged(self.cam, pal.face(block.color, "front"), depth, pal.fog)

        # Only the two vertical faces pointing at the camera are drawn; which
        # ones those are falls out of the sign of the block's view-space offset.
        right, _up, _d = self._to_view(x, y, z)
        sign_x = 1 if right < 0 else -1

        bottom_pts = [corner(-1, -1, -0.5), corner(1, -1, -0.5), corner(1, 1, -0.5), corner(-1, 1, -0.5)]
        if any(p is None for p in bottom_pts):
            return

        def poly(indices, colour):
            pts = [(top_pts[i].x, top_pts[i].y) if kind == "t" else (bottom_pts[i].x, bottom_pts[i].y)
                   for i, kind in indices]
            pygame.draw.polygon(surface, colour, pts)

        # Near vertical face (the one closest to the camera in depth).
        near_idx = 0 if sign_x > 0 else 2
        poly(
            [(near_idx, "t"), (near_idx + 1, "t"), (near_idx + 1, "b"), (near_idx, "b")],
            colour_front,
        )
        # The adjacent visible face.
        side_a = (near_idx + 1) % 4
        side_b = (near_idx + 2) % 4
        poly([(side_a, "t"), (side_b, "t"), (side_b, "b"), (side_a, "b")], colour_side)

        # Top last: the camera always sits above the blocks it can see.
        pygame.draw.polygon(surface, colour_top, [(p.x, p.y) for p in top_pts])

    def _draw_player(self, surface: pygame.Surface) -> None:
        x, y, z = self.player_pos
        p = self._project(x, y, z)
        if p is None:
            return
        pal = self.palette
        s = p.scale

        body = pygame.Rect(0, 0, max(2, int(0.55 * s)), max(3, int(0.85 * s)))
        body.midbottom = (int(p.x), int(p.y))
        pygame.draw.rect(surface, lerp_rgb(pal.accent, (255, 255, 255), 0.15), body)

        head = max(2, int(0.3 * s))
        pygame.draw.rect(
            surface,
            lerp_rgb(pal.accent, pal.ink, 0.3),
            pygame.Rect(int(p.x - head), int(body.top - head * 2), head * 2, head * 2),
        )

    def _draw_hud(self, surface: pygame.Surface) -> None:
        pal = self.palette
        remaining = max(0, len(self.path) - self.hop_index - 1)
        text(surface, f"{remaining} to go", self.width - 10, 8, size=18, color=pal.ink, anchor="topright")
        text(surface, f"{pal.time_of_day} · {pal.weather}", 10, 8, size=12, color=pal.ink)
