"""Marble race.

A generated zigzag course, seven marbles, real collision physics and no
predetermined winner. This scene exists because the original third slot was
going to be a clip player, and clips mean sourcing content by hand -- the whole
point of this project is that nothing is ever uploaded, so the third scene is
generated too.

Unlike the other two this is honestly 2D: the course is a side elevation, so a
full perspective camera would buy nothing but a smaller playfield in a strip
that is already only a few hundred pixels wide.

The physics is circle-versus-segment with restitution, run on fixed substeps.
Substepping is not optional here -- marbles reach speeds where a single 30 Hz
step would tunnel them straight through a ramp.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

from ..engine import postfx
from ..engine.draw import Particles, text
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import Sky
from ..engine.texture import soft_glow, sphere
from ..palette import RGB, hsv, lerp_rgb, shade
from ..rng import golden_sequence

#: How many past positions each marble remembers, for its motion trail.
TRAIL_LENGTH = 9

#: Course width in world units. Screen width maps onto exactly this.
WORLD_W = 12.0
GRAVITY = 26.0
RESTITUTION = 0.42
FRICTION = 0.86
MARBLE_R = 0.34
SUBSTEPS = 4
RAMP_SPACING = 6.5
MARBLE_COUNT = 7


@dataclass
class Segment:
    x1: float
    y1: float
    x2: float
    y2: float
    thickness: float = 0.22


@dataclass
class Peg:
    x: float
    y: float
    r: float = 0.28


@dataclass
class Marble:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    color: RGB = (255, 255, 255)
    trail: list[tuple[float, float]] = field(default_factory=list)


@register("marbles")
class MarbleScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        self.rng = ctx.stream("marble-course")
        self.rng_start = ctx.stream("marble-start")

        self.scale = self.width / WORLD_W
        self.segments: list[Segment] = []
        self.pegs: list[Peg] = []
        self.marbles: list[Marble] = []

        self._next_ramp_y = 4.0
        self._ramp_index = 0
        self.cam_y = 0.0
        self.peg_chance = self.rng.uniform(0.3, 0.9)

        self._build_walls()
        self._spawn_marbles()
        # Generate a screenful of course before the first frame is drawn.
        while self._next_ramp_y < self._world_bottom() + RAMP_SPACING * 2:
            self._generate_ramp()

        self.particles = Particles(self.palette, self.width, self.height, ctx.stream("weather"))

        art = ctx.stream("marble-art")
        self.sky = Sky(self.palette, self.width, self.height, art, horizon=0.0)
        # One lit sphere sprite per racer, rendered once. Shading a ball with
        # nested pygame ellipses every frame would cost far more and look worse.
        sprite_r = max(6, int(MARBLE_R * self.scale * 1.6))
        self.sprites = [sphere(sprite_r, m.color) for m in self.marbles]
        self.glow = soft_glow(sprite_r * 2, (255, 255, 255))
        self.sparks: list[list[float]] = []

    # -- geometry ---------------------------------------------------------

    def _world_bottom(self) -> float:
        return self.cam_y + self.height / self.scale

    def _build_walls(self) -> None:
        # Walls are regenerated as the camera descends; these are the initial
        # pair and are extended in _stream_course.
        self._wall_to = 0.0

    def _extend_walls(self, to_y: float) -> None:
        while self._wall_to < to_y:
            top = self._wall_to
            bottom = top + 40.0
            self.segments.append(Segment(0.15, top, 0.15, bottom, 0.3))
            self.segments.append(Segment(WORLD_W - 0.15, top, WORLD_W - 0.15, bottom, 0.3))
            self._wall_to = bottom

    def _generate_ramp(self) -> None:
        """One zigzag ramp, alternating direction, with an open end to fall off."""
        rng = self.rng
        y = self._next_ramp_y
        drop = rng.uniform(2.4, 4.2)
        # Alternating direction is what makes the course a zigzag rather than a
        # slide; marbles roll one way, drop, then roll back.
        rightward = self._ramp_index % 2 == 0

        inset = rng.uniform(1.4, 2.8)
        if rightward:
            x1, x2 = 0.3, WORLD_W - inset
        else:
            x1, x2 = WORLD_W - 0.3, inset

        self.segments.append(Segment(x1, y, x2, y + drop))

        # A short lip at the high end stops marbles escaping backwards.
        lip = 0.9
        self.segments.append(Segment(x1, y - lip, x1, y))

        if rng.random() < self.peg_chance:
            count = rng.randint(2, 5)
            for _ in range(count):
                self.pegs.append(
                    Peg(
                        x=rng.uniform(1.2, WORLD_W - 1.2),
                        y=y + drop + rng.uniform(1.6, RAMP_SPACING - 1.6),
                        r=rng.uniform(0.22, 0.36),
                    )
                )

        self._ramp_index += 1
        self._next_ramp_y += RAMP_SPACING * rng.uniform(0.9, 1.15)

    def _spawn_marbles(self) -> None:
        rng = self.rng_start
        for i in range(MARBLE_COUNT):
            # Golden-ratio hues so the field is always maximally distinguishable
            # rather than occasionally three shades of the same blue.
            hue = golden_sequence(i + 1)
            self.marbles.append(
                Marble(
                    x=1.2 + (WORLD_W - 2.4) * (i + 0.5) / MARBLE_COUNT,
                    y=rng.uniform(0.0, 1.2),
                    vx=rng.uniform(-1.0, 1.0),
                    color=hsv(hue, 0.75, 0.95),
                )
            )

    # -- physics ----------------------------------------------------------

    def update(self, dt: float) -> None:
        step = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            self._step(step)

        # Follow the middle of the pack, not the leader. Tracking the leader
        # looks correct until the field spreads out, at which point everyone
        # else is off the top of the screen and the race stops being a race.
        ranked = sorted(self.marbles, key=lambda m: m.y)
        pacer = ranked[len(ranked) // 2 + 1] if len(ranked) > 2 else ranked[-1]
        target = pacer.y - (self.height / self.scale) * 0.45
        self.cam_y += (target - self.cam_y) * min(1.0, dt * 3.0)

        for m in self.marbles:
            m.trail.append((m.x, m.y))
            if len(m.trail) > TRAIL_LENGTH:
                del m.trail[0]

        alive = []
        for spark in self.sparks:
            spark[4] -= dt
            if spark[4] <= 0:
                continue
            spark[0] += spark[2] * dt
            spark[1] += spark[3] * dt
            spark[3] += GRAVITY * 0.5 * dt
            alive.append(spark)
        self.sparks = alive[-90:]

        self._stream_course()
        self.particles.update(dt)
        self.sky.update(dt, wind=0.35)

    def _step(self, dt: float) -> None:
        for m in self.marbles:
            m.vy += GRAVITY * dt
            m.x += m.vx * dt
            m.y += m.vy * dt

            for seg in self.segments:
                self._collide_segment(m, seg)
            for peg in self.pegs:
                self._collide_circle(m, peg.x, peg.y, peg.r)

            # Terminal velocity keeps the substep count honest.
            speed = math.hypot(m.vx, m.vy)
            if speed > 34.0:
                m.vx *= 34.0 / speed
                m.vy *= 34.0 / speed

    def _collide_segment(self, m: Marble, seg: Segment) -> None:
        dx, dy = seg.x2 - seg.x1, seg.y2 - seg.y1
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-9:
            return
        # Closest point on the segment to the marble centre.
        t = ((m.x - seg.x1) * dx + (m.y - seg.y1) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        cx, cy = seg.x1 + dx * t, seg.y1 + dy * t

        nx, ny = m.x - cx, m.y - cy
        dist = math.hypot(nx, ny)
        radius = MARBLE_R + seg.thickness * 0.5
        if dist >= radius or dist < 1e-9:
            return

        nx, ny = nx / dist, ny / dist
        # Positional correction first, so the marble is never left inside the
        # surface where the next frame would resolve it in a random direction.
        overlap = radius - dist
        m.x += nx * overlap
        m.y += ny * overlap

        normal_v = m.vx * nx + m.vy * ny
        if normal_v < 0:
            m.vx -= (1.0 + RESTITUTION) * normal_v * nx
            m.vy -= (1.0 + RESTITUTION) * normal_v * ny
            # Tangential friction, applied only on contact.
            tx, ty = -ny, nx
            tangent_v = m.vx * tx + m.vy * ty
            m.vx += tx * tangent_v * (FRICTION - 1.0)
            m.vy += ty * tangent_v * (FRICTION - 1.0)

    def _collide_circle(self, m: Marble, cx: float, cy: float, r: float) -> None:
        nx, ny = m.x - cx, m.y - cy
        dist = math.hypot(nx, ny)
        radius = MARBLE_R + r
        if dist >= radius or dist < 1e-9:
            return
        nx, ny = nx / dist, ny / dist
        m.x += nx * (radius - dist)
        m.y += ny * (radius - dist)
        normal_v = m.vx * nx + m.vy * ny
        if normal_v < 0:
            m.vx -= (1.0 + RESTITUTION * 1.2) * normal_v * nx
            m.vy -= (1.0 + RESTITUTION * 1.2) * normal_v * ny
            # Peg strikes throw sparks. They are the moment a lead changes, so
            # they are worth drawing attention to.
            if -normal_v > 6.0:
                for i in range(3):
                    angle = math.atan2(ny, nx) + (i - 1) * 0.5
                    self.sparks.append(
                        [cx, cy, math.cos(angle) * 5.0, math.sin(angle) * 5.0, 0.28]
                    )

    def _stream_course(self) -> None:
        horizon = self._world_bottom() + RAMP_SPACING * 2
        while self._next_ramp_y < horizon:
            self._generate_ramp()
        self._extend_walls(horizon + 40.0)

        # Discard anything comfortably above the camera.
        cutoff = self.cam_y - 12.0
        self.segments = [s for s in self.segments if max(s.y1, s.y2) > cutoff]
        self.pegs = [p for p in self.pegs if p.y > cutoff]

    # -- rendering --------------------------------------------------------

    def _sx(self, x: float) -> float:
        return x * self.scale

    def _sy(self, y: float) -> float:
        return (y - self.cam_y) * self.scale

    def draw(self, surface: pygame.Surface) -> None:
        pal = self.palette
        self.sky.draw(surface, parallax=self.cam_y * 6.0)

        # Ramps are drawn as filled quads with a lit upper edge rather than as
        # plain lines, which gives the course a thickness the marbles can look
        # like they are resting on.
        rail = pal.structure
        rail_lit = lerp_rgb(rail, (255, 255, 255), 0.45)
        for seg in self.segments:
            y_top = min(self._sy(seg.y1), self._sy(seg.y2))
            y_bot = max(self._sy(seg.y1), self._sy(seg.y2))
            if y_bot < -20 or y_top > self.height + 20:
                continue
            thickness = max(2, int(seg.thickness * self.scale))
            a = (self._sx(seg.x1), self._sy(seg.y1))
            b = (self._sx(seg.x2), self._sy(seg.y2))
            pygame.draw.line(surface, shade(rail, 0.6), a, (b[0], b[1] + thickness), thickness)
            pygame.draw.line(surface, rail, a, b, thickness)
            pygame.draw.line(surface, rail_lit, a, b, max(1, thickness // 3))

        for peg in self.pegs:
            y = self._sy(peg.y)
            if y < -20 or y > self.height + 20:
                continue
            # Course furniture shares one colour family with the ramps, so the
            # only saturated things on screen are the marbles themselves.
            r = max(2, int(peg.r * self.scale))
            x = int(self._sx(peg.x))
            pygame.draw.circle(surface, shade(pal.structure, 0.62), (x, int(y) + 1), r)
            pygame.draw.circle(surface, shade(pal.structure, 0.95), (x, int(y)), r)
            if r > 3:
                pygame.draw.circle(surface, rail_lit, (x - r // 3, int(y) - r // 3), max(1, r // 3))

        radius = max(3, int(MARBLE_R * self.scale))
        for index, m in enumerate(self.marbles):
            y = self._sy(m.y)
            if y < -40 or y > self.height + 40:
                continue
            x = self._sx(m.x)

            # Motion trail: past positions, shrinking and fading. Cheap, and it
            # is what conveys speed on a ball that has no other animation.
            for i, (tx, ty) in enumerate(m.trail):
                t = (i + 1) / len(m.trail)
                tr = max(1, int(radius * t * 0.8))
                pygame.draw.circle(
                    surface,
                    lerp_rgb(pal.sky_bottom, m.color, t * 0.75),
                    (int(self._sx(tx)), int(self._sy(ty))),
                    tr,
                )

            sprite = self.sprites[index]
            scaled = pygame.transform.smoothscale(sprite, (radius * 2, radius * 2))
            surface.blit(scaled, scaled.get_rect(center=(int(x), int(y))))

        for sx, sy, _vx, _vy, life in self.sparks:
            size = max(2, int(life * 26))
            glow = pygame.transform.smoothscale(self.glow, (size, size))
            surface.blit(
                glow,
                glow.get_rect(center=(int(self._sx(sx)), int(self._sy(sy)))),
                special_flags=pygame.BLEND_RGB_ADD,
            )

        self.particles.draw(surface)

        postfx.apply_all(
            surface,
            bloom_threshold=postfx.auto_threshold(pal.sky_bottom),
            bloom_intensity=0.8 if pal.time_of_day == "night" else 0.45,
            vignette_strength=0.32,
            quality=self.ctx.quality,
        )
        self._draw_hud(surface)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        pal = self.palette
        ranked = sorted(self.marbles, key=lambda m: -m.y)
        text(surface, "RACE", 10, 8, size=16, color=pal.ink)

        # Podium chips down the left edge, in current race order.
        for i, m in enumerate(ranked[:5]):
            y = 30 + i * 16
            pygame.draw.circle(surface, m.color, (16, y + 5), 5)
            text(surface, f"{i + 1}", 28, y, size=12, color=pal.ink)

        depth = int(max(m.y for m in self.marbles))
        text(surface, f"{depth} m", self.width - 10, 8, size=18, color=pal.ink, anchor="topright")
