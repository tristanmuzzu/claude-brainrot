"""Voxel parkour tower.

A blocky spire generated from the top down, with a figure hopping its way to the
bottom while the camera orbits.

**Path first, geometry second.** The descent route is generated before a single
block exists: a spiral of nodes whose vertical drop and horizontal reach are
clamped to what a jump can actually cover. The tower is then built *around*
that route. Generating a tower and then searching it for a route would mean
sometimes finding none, and there is no good answer to that inside a render
loop.

**Everything is on the integer grid.** Blocks sit at whole-number coordinates
and are exactly one unit across, because the moment a "voxel" world has
platforms at 3.47 it stops looking like a voxel world and starts looking like
scattered boxes. The path is snapped to the grid too, and the reach constraint
is enforced after snapping rather than before.

**Terrain colour does not follow the run palette.** Grass is grass-coloured and
stone is stone-coloured in every run; only the sky, the lighting and the
character's shirt pick up the generated palette. Terrain that changes hue every
run reads as a bug, not as variety.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from ..engine import model, postfx
from ..engine.draw import Particles, text
from ..engine.model import Box, Humanoid
from ..engine.pixelart import build_atlas, humanoid_skin
from ..engine.projection import Camera, ease_in_out, fog_amount, project
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import Sky
from ..palette import lerp_rgb

BLOCK = 1.0
#: Vertical drop per path step, in whole blocks.
DROP_MIN, DROP_MAX = 1.0, 2.0
#: Horizontal reach per step, in blocks. Beyond ~3 the jump stops reading.
REACH_MIN, REACH_MAX = 1.6, 3.0
HOP_TIME = 0.46
#: Orbit distance. Close enough that block textures are legible, far enough
#: that the whole spire and the route spiralling down it are in frame.
CAMERA_RADIUS = 19.0

#: How many of the nearest blocks are drawn with real textures. Beyond this the
#: faces are a few pixels across and a flat fill is indistinguishable, so the
#: budget caps frame cost without capping how large a tower may be generated.
DETAIL_BUDGET = {"high": 110, "balanced": 65, "low": 0}

#: Depth fog is quantised so the shaded-texture cache stays small; a continuous
#: value would mint a new cache entry for every block.
FOG_STEPS = 3


@dataclass
class Node:
    x: float
    y: float
    z: float


def _platform_kit(index: int) -> tuple[str, dict[str, str]]:
    """Which block a platform is made of, cycling so hops are countable."""
    kind = index % 4
    if kind == 0:
        return "planks", {}
    if kind == 2:
        return "cobblestone", {}
    return "dirt", {
        "top": "grass_top",
        "north": "grass_side",
        "south": "grass_side",
        "east": "grass_side",
        "west": "grass_side",
    }


@register("tower")
class TowerScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        self.rng = ctx.stream("tower-shape")
        self.rng_decor = ctx.stream("tower-decor")

        self.cam = Camera(y=0.0, horizon=0.44, far=70.0, focal=self.height * 0.78)
        self.yaw = 0.0
        self.blocks: list[Box] = []
        self.path: list[Node] = []

        self.hop_index = 0
        self.hop_t = 0.0
        self.player_pos = (0.0, 0.0, 0.0)

        self.particles = Particles(self.palette, self.width, self.height, ctx.stream("weather"))

        art = ctx.stream("tower-art")
        self.sky = Sky(self.palette, self.width, self.height, art, horizon=self.cam.horizon)
        self.atlas = build_atlas(art)
        self.atlas.update(
            humanoid_skin(
                art,
                skin=(232, 178, 136),
                hair=(58, 42, 32),
                # Only the shirt follows the run, so the figure stays legible
                # against any sky while still belonging to this run.
                shirt=lerp_rgb(self.palette.accent, (255, 255, 255), 0.25),
                trousers=(62, 72, 132),
                shoes=(92, 74, 60),
            )
        )
        self.figure = Humanoid()
        self._detail_budget = DETAIL_BUDGET.get(ctx.quality, 150)
        self._view_basis = (0.0, 1.0, 0.0, CAMERA_RADIUS)

        self._generate()

    # -- generation -------------------------------------------------------

    def _generate(self) -> None:
        """Build a fresh tower: route first, then the structure around it."""
        self.blocks.clear()
        self.path.clear()

        rng = self.rng
        steps = rng.randint(22, 32)
        radius = rng.uniform(4.0, 6.5)
        angle = rng.uniform(0.0, math.tau)
        spin = rng.choice((-1, 1))
        y = float(steps) * 1.6

        previous: Node | None = None
        for i in range(steps):
            drop = float(rng.randint(int(DROP_MIN), int(DROP_MAX)))
            radius = max(3.0, min(8.0, radius + rng.choice((-1.0, 0.0, 0.0, 1.0))))
            y -= drop

            # Step around the axis, then snap to the grid and only accept the
            # result if it is still within jumping distance. Snapping after the
            # reach check would let rounding push a hop out of range.
            node = previous
            for attempt in range(6):
                step = (REACH_MAX - 0.4 * attempt) / max(1.0, radius)
                candidate = Node(
                    x=float(round(math.sin(angle + spin * step) * radius)),
                    y=y,
                    z=float(round(math.cos(angle + spin * step) * radius)),
                )
                if previous is None:
                    node = candidate
                    angle += spin * step
                    break
                reach = math.hypot(candidate.x - previous.x, candidate.z - previous.z)
                if REACH_MIN * 0.5 <= reach <= REACH_MAX:
                    node = candidate
                    angle += spin * step
                    break
            else:
                node = candidate  # last attempt, still the closest available

            assert node is not None
            self.path.append(node)
            self._build_platform(node, i)
            previous = node

        self._build_core(y, self.path[0].y)
        self.player_pos = (self.path[0].x, self.path[0].y + BLOCK * 0.5, self.path[0].z)

    def _build_platform(self, node: Node, index: int) -> None:
        rng = self.rng_decor
        default, faces = _platform_kit(index)
        half = rng.choice((0, 0, 1, 1))

        for dx in range(-half, half + 1):
            for dz in range(-half, half + 1):
                self.blocks.append(
                    Box(
                        x=node.x + dx,
                        y=node.y,
                        z=node.z + dz,
                        w=BLOCK,
                        h=BLOCK,
                        d=BLOCK,
                        default=default,
                        textures=dict(faces),
                    )
                )

        # A small tree now and then: a log with a leaf cap. Cheap, and it is
        # what makes the spire read as terrain rather than as architecture.
        if rng.random() < 0.16:
            tx, tz = node.x + rng.choice((-1, 1)), node.z + rng.choice((-1, 1))
            for h in range(2):
                self.blocks.append(
                    Box(
                        x=tx,
                        y=node.y + 1 + h,
                        z=tz,
                        w=BLOCK,
                        h=BLOCK,
                        d=BLOCK,
                        default="log_side",
                        textures={"top": "log_top", "bottom": "log_top"},
                    )
                )
            for lx in (-1, 0, 1):
                for lz in (-1, 0, 1):
                    if lx and lz and rng.random() < 0.5:
                        continue
                    self.blocks.append(
                        Box(
                            x=tx + lx,
                            y=node.y + 3,
                            z=tz + lz,
                            w=BLOCK,
                            h=BLOCK,
                            d=BLOCK,
                            default="leaves",
                        )
                    )

    def _build_core(self, bottom: float, top: float) -> None:
        """The central pillar the route spirals around."""
        rng = self.rng_decor
        y = bottom
        while y <= top:
            # A 2x2 column rather than 3x3. From outside, a 3x3 pillar only
            # ever shows its outer shell -- the rest was generated, projected
            # and then painted over every frame. Two-by-two looks identical
            # from any orbit angle and is a third of the geometry.
            for dx in (-1, 0):
                for dz in (-1, 0):
                    self.blocks.append(
                        Box(
                            x=float(dx),
                            y=y,
                            z=float(dz),
                            w=BLOCK,
                            h=BLOCK,
                            d=BLOCK,
                            default="cobblestone" if rng.random() < 0.65 else "stone",
                        )
                    )
            y += BLOCK

    # -- view transform ---------------------------------------------------

    def _to_view(self, wx: float, wy: float, wz: float) -> tuple[float, float, float]:
        """World to camera space.

        The shared projection has no yaw, so the orbit is applied here: rotate
        the world about the tower axis, then hand a plain forward-looking camera
        the result.
        """
        sin_y, cos_y, cam_x, cam_z = self._view_basis
        dx, dz = wx - cam_x, wz - cam_z
        return (dx * cos_y + dz * -sin_y, wy, dx * -sin_y + dz * -cos_y)

    def _project(self, wx: float, wy: float, wz: float):
        right, up, depth = self._to_view(wx, wy, wz)
        p = project(self.cam, right, up, depth, self.width, self.height)
        return None if p is None else (p.x, p.y, p.depth)

    def _refresh_basis(self) -> None:
        sin_y, cos_y = math.sin(self.yaw), math.cos(self.yaw)
        self._view_basis = (sin_y, cos_y, sin_y * CAMERA_RADIUS, cos_y * CAMERA_RADIUS)

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
        y = a.y + (b.y - a.y) * smooth + math.sin(t * math.pi) * 0.9 + BLOCK * 0.5
        self.player_pos = (x, y, z)

        # Camera trails the player's angle rather than snapping to it.
        target_yaw = math.atan2(x, z)
        delta = (target_yaw - self.yaw + math.pi) % math.tau - math.pi
        self.yaw += delta * min(1.0, dt * 2.2)
        self.cam.y = y + 4.0

        self.particles.update(dt)
        self.sky.update(dt, wind=0.5)

    # -- rendering --------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        pal = self.palette
        self._refresh_basis()
        self.sky.draw(surface, parallax=self.yaw * 40.0)

        visible: list[tuple[float, Box]] = []
        axis_depth = self._to_view(0.0, 0.0, 0.0)[2]
        for block in self.blocks:
            _r, _u, depth = self._to_view(block.x, block.y, block.z)
            if depth <= 1.0 or depth > self.cam.far:
                continue
            if abs(block.y - self.cam.y) * self.cam.focal > depth * self.height * 0.85:
                continue
            # Core blocks behind the axis are hidden by a solid pillar.
            if abs(block.x) <= 1.05 and abs(block.z) <= 1.05 and depth > axis_depth + 0.25:
                continue
            visible.append((depth, block))

        visible.sort(key=lambda item: -item[0])
        textured_from = max(0, len(visible) - self._detail_budget)

        for index, (depth, block) in enumerate(visible):
            # Aerial perspective, folded into the face tint so it costs nothing
            # extra and quantised so it does not explode the texture cache.
            fog = fog_amount(self.cam, depth)
            block.tint = 1.0 - round(fog * FOG_STEPS) / FOG_STEPS * 0.45
            model.draw_box(
                surface, self._project, block, self.atlas, textured=index >= textured_from
            )

        self._draw_player(surface)
        self.particles.draw(surface)

        postfx.apply_all(
            surface,
            bloom_threshold=postfx.auto_threshold(pal.sky_bottom),
            bloom_intensity=0.7 if pal.time_of_day == "night" else 0.35,
            vignette_strength=0.30,
            quality=self.ctx.quality,
        )
        self._draw_hud(surface)

    def _draw_player(self, surface: pygame.Surface) -> None:
        x, y, z = self.player_pos
        # Legs tuck through the arc of a jump and reach for the landing.
        phase = self.hop_t / HOP_TIME
        tuck = math.sin(phase * math.pi) * 0.55
        for box in self.figure.parts(
            x, y, z, swing=phase * math.tau, lean=0.12, amplitude=0.45, tuck=tuck
        ):
            model.draw_box(surface, self._project, box, self.atlas)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        pal = self.palette
        remaining = max(0, len(self.path) - self.hop_index - 1)
        text(surface, f"{remaining} to go", self.width - 10, 8, size=18, color=pal.ink, anchor="topright")
        text(surface, f"{pal.time_of_day} · {pal.weather}", 10, 8, size=12, color=pal.ink)
