"""Endless runner.

Three lanes, infinite track, generated forever and played by nobody.

**Solvability by construction.** The generator does not create obstacles and
then check whether the result can be survived -- rejection sampling would stall
unpredictably, which is unacceptable in a render loop. Instead every row is
assigned a guaranteed-clear lane *first*, and that clear lane is only ever
allowed to move by one lane between consecutive rows. A reachable corridor
therefore exists by construction, and obstacles are simply painted into the
lanes the corridor does not occupy.

**Coins mark the corridor.** They are spawned along the safe path, so the
route reads as deliberate rather than lucky -- which is exactly the trick the
real games use to teach you where to go.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import pygame

from ..engine.draw import Particles, rounded_rect, text, vertical_gradient, vignette
from ..engine.projection import Camera, fogged, jump_height, project
from ..engine.scene import Scene, SceneContext, register
from ..palette import lerp_rgb, shade

LANE_X = (-2.3, 0.0, 2.3)
TRACK_HALF = 3.5
ROW_SPACING = 15.0
TIE_SPACING = 3.0
VIEW_DISTANCE = 95.0

JUMP_DURATION = 0.72
JUMP_PEAK = 2.5
SLIDE_DURATION = 0.6

#: How far ahead the autopilot commits to a lane change. Tuned so it moves
#: early enough to look competent, late enough to look alive.
LOOKAHEAD = 26.0


@dataclass
class Obstacle:
    lane: int
    z: float
    kind: str
    length: float = 2.0
    height: float = 1.0

    @property
    def z_end(self) -> float:
        return self.z + self.length


@dataclass
class Coin:
    lane: int
    z: float
    y: float = 1.2
    taken: bool = False


@dataclass
class Building:
    x: float
    z: float
    width: float
    height: float
    depth: float
    tint: float


@dataclass
class Player:
    lane: int = 1
    x: float = 0.0
    z: float = 0.0
    jump_t: float = -1.0
    slide_t: float = -1.0
    crash_t: float = -1.0
    run_cycle: float = 0.0
    coins: int = 0

    @property
    def airborne(self) -> bool:
        return 0.0 <= self.jump_t <= JUMP_DURATION

    @property
    def sliding(self) -> bool:
        return 0.0 <= self.slide_t <= SLIDE_DURATION

    @property
    def crashed(self) -> bool:
        return self.crash_t >= 0.0

    @property
    def y(self) -> float:
        return jump_height(self.jump_t, JUMP_PEAK, JUMP_DURATION) if self.airborne else 0.0


@register("runner")
class RunnerScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        self.rng_layout = ctx.stream("runner-layout")
        self.rng_city = ctx.stream("runner-city")
        self.rng_flavour = ctx.stream("runner-flavour")

        self.cam = Camera(y=2.9, horizon=0.40, far=VIEW_DISTANCE, focal=self.height * 0.55)
        self.player = Player()

        self.speed = 19.0
        self.max_speed = 38.0
        self.obstacles: list[Obstacle] = []
        self.coins: list[Coin] = []
        self.buildings: list[Building] = []

        # Corridor state: the lane guaranteed clear at each generated row.
        self._safe_lane = 1
        self._next_row_z = 40.0
        self._next_building_z = 0.0
        self.score = 0.0
        self.shake = 0.0

        self.particles = Particles(self.palette, self.width, self.height, ctx.stream("weather"))

        # Each run gets its own density and sky, so two runner runs back to back
        # do not feel like the same track.
        self.density = self.rng_layout.uniform(0.45, 0.85)
        self.city_density = self.rng_city.uniform(0.5, 1.0)

        self._warm_up()

    # -- generation -------------------------------------------------------

    def _warm_up(self) -> None:
        """Pre-populate the visible world so frame one is not empty track."""
        while self._next_row_z < VIEW_DISTANCE:
            self._generate_row()
        while self._next_building_z < VIEW_DISTANCE:
            self._generate_buildings()

    def _generate_row(self) -> None:
        rng = self.rng_layout
        z = self._next_row_z

        # The corridor moves at most one lane per row, which is what makes the
        # layout reachable no matter what the rest of the row contains.
        step = rng.choice((-1, 0, 0, 1))
        self._safe_lane = max(0, min(2, self._safe_lane + step))
        safe = self._safe_lane

        for lane in range(3):
            if lane == safe:
                # Even the safe lane can hold something, but only obstacles the
                # autopilot can clear without leaving the corridor.
                if rng.random() < self.density * 0.45:
                    kind = rng.choice(("barrier", "overhead", "cone"))
                    self.obstacles.append(self._make(lane, z, kind, rng))
                continue

            if rng.random() > self.density:
                continue

            kind = rng.choices(
                ("barrier", "overhead", "cone", "train"),
                weights=(3, 2, 2, 3),
            )[0]
            self.obstacles.append(self._make(lane, z, kind, rng))

        # Coins trace the corridor between this row and the next.
        if rng.random() < 0.75:
            count = rng.randint(3, 7)
            for i in range(count):
                self.coins.append(
                    Coin(lane=safe, z=z + 3.0 + i * 2.4, y=1.1)
                )

        self._next_row_z += ROW_SPACING * self.rng_layout.uniform(0.85, 1.25)

    def _make(self, lane: int, z: float, kind: str, rng: random.Random) -> Obstacle:
        if kind == "train":
            return Obstacle(lane, z, kind, length=rng.uniform(9.0, 18.0), height=3.2)
        if kind == "overhead":
            return Obstacle(lane, z, kind, length=1.2, height=2.6)
        if kind == "barrier":
            return Obstacle(lane, z, kind, length=1.0, height=1.15)
        return Obstacle(lane, z, kind, length=0.9, height=0.8)

    def _generate_buildings(self) -> None:
        rng = self.rng_city
        z = self._next_building_z
        for side in (-1, 1):
            if rng.random() > self.city_density:
                continue
            width = rng.uniform(3.0, 7.0)
            self.buildings.append(
                Building(
                    x=side * (TRACK_HALF + 2.0 + rng.uniform(0.0, 5.0) + width * 0.5),
                    z=z,
                    width=width,
                    height=rng.uniform(6.0, 34.0),
                    depth=rng.uniform(4.0, 9.0),
                    tint=rng.uniform(0.75, 1.2),
                )
            )
        self._next_building_z += rng.uniform(5.0, 11.0)

    # -- simulation -------------------------------------------------------

    def update(self, dt: float) -> None:
        player = self.player

        if player.crashed:
            player.crash_t += dt
            self.speed = max(9.0, self.speed - 34.0 * dt)
            if player.crash_t > 1.1:
                player.crash_t = -1.0
                player.jump_t = -1.0
                player.slide_t = -1.0
                self._clear_ahead()
        else:
            self.speed = min(self.max_speed, self.speed + 0.55 * dt)

        player.z += self.speed * dt
        self.cam.z = player.z - 8.0
        self.score += self.speed * dt * 0.1

        # Camera sway, scaled by speed so it reads as momentum.
        self.cam.roll = math.sin(self.elapsed * 1.7) * 0.35 * (self.speed / self.max_speed)
        self.cam.x += (player.x * 0.35 - self.cam.x) * min(1.0, dt * 4.0)

        if not player.crashed:
            self._autopilot(dt)

        if player.airborne:
            player.jump_t += dt
            if player.jump_t > JUMP_DURATION:
                player.jump_t = -1.0
        if player.sliding:
            player.slide_t += dt
            if player.slide_t > SLIDE_DURATION:
                player.slide_t = -1.0

        player.run_cycle += dt * (self.speed * 0.55)
        player.x += (LANE_X[player.lane] - player.x) * min(1.0, dt * 9.0)

        self._collide()
        self._stream_world()
        self.particles.update(dt)
        self.shake = max(0.0, self.shake - dt * 3.0)

    def _autopilot(self, dt: float) -> None:
        """Play the game.

        Two independent decisions: which lane to be in (follow the corridor),
        and whether to jump or slide (clear whatever is in the current lane).
        """
        player = self.player
        ahead_start = player.z + 4.0
        ahead_end = player.z + LOOKAHEAD

        # -- lane choice: score each lane by how far it stays clear.
        best_lane, best_clearance = player.lane, -1.0
        for lane in range(3):
            # Only adjacent lanes are reachable in time.
            if abs(lane - player.lane) > 1:
                continue
            clearance = LOOKAHEAD
            for obs in self.obstacles:
                if obs.lane != lane or obs.z_end < ahead_start or obs.z > ahead_end:
                    continue
                if obs.kind == "train":
                    clearance = min(clearance, obs.z - player.z)
            # Prefer the lane holding coins, all else equal -- it is the
            # corridor, and it makes the autopilot look purposeful.
            bonus = 1.5 if any(
                c.lane == lane and not c.taken and ahead_start <= c.z <= ahead_end
                for c in self.coins
            ) else 0.0
            score = clearance + bonus + (0.6 if lane == player.lane else 0.0)
            if score > best_clearance:
                best_lane, best_clearance = lane, score
        player.lane = best_lane

        # -- vertical action: react to the nearest thing in the chosen lane.
        if player.airborne or player.sliding:
            return
        for obs in sorted(self.obstacles, key=lambda o: o.z):
            if obs.lane != player.lane or obs.z < player.z:
                continue
            gap = obs.z - player.z
            if gap > self.speed * 0.55:
                break
            if obs.kind in ("barrier", "cone"):
                player.jump_t = 0.0
            elif obs.kind == "overhead":
                player.slide_t = 0.0
            break

    def _collide(self) -> None:
        player = self.player
        if player.crashed:
            return
        for obs in self.obstacles:
            if obs.lane != player.lane:
                continue
            if not (obs.z - 0.7 <= player.z <= obs.z_end + 0.4):
                continue
            if obs.kind in ("barrier", "cone") and player.airborne:
                continue
            if obs.kind == "overhead" and player.sliding:
                continue
            # A crash is a feature: the tumble-and-recover beat is half the
            # charm of the genre, and a runner that never fails is hypnotic in
            # the boring way.
            player.crash_t = 0.0
            self.shake = 1.0
            return

        for coin in self.coins:
            if coin.taken or coin.lane != player.lane:
                continue
            if abs(coin.z - player.z) < 1.0:
                coin.taken = True
                player.coins += 1

    def _clear_ahead(self) -> None:
        """After a crash, sweep the immediate path so recovery is not instant death."""
        z = self.player.z
        self.obstacles = [o for o in self.obstacles if o.z_end < z - 1 or o.z > z + 18]

    def _stream_world(self) -> None:
        z = self.player.z
        while self._next_row_z < z + VIEW_DISTANCE:
            self._generate_row()
        while self._next_building_z < z + VIEW_DISTANCE:
            self._generate_buildings()

        behind = z - 12.0
        self.obstacles = [o for o in self.obstacles if o.z_end > behind]
        self.coins = [c for c in self.coins if c.z > behind and not c.taken]
        self.buildings = [b for b in self.buildings if b.z + b.depth > behind]

    # -- rendering --------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        pal = self.palette
        surface.blit(vertical_gradient(self.width, self.height, pal.sky_top, pal.sky_bottom), (0, 0))

        if "stars" in pal.particles:
            self.particles.draw(surface)

        offset_x = 0
        if self.shake > 0:
            offset_x = int(math.sin(self.elapsed * 60) * self.shake * 5)

        self._draw_buildings(surface, offset_x)
        self._draw_track(surface, offset_x)

        # Painter's algorithm: everything in the world sorted far to near.
        drawables: list[tuple[float, object]] = []
        drawables += [(o.z, o) for o in self.obstacles]
        drawables += [(c.z, c) for c in self.coins if not c.taken]
        drawables.append((self.player.z, self.player))
        drawables.sort(key=lambda item: -item[0])

        for _, item in drawables:
            if isinstance(item, Obstacle):
                self._draw_obstacle(surface, item, offset_x)
            elif isinstance(item, Coin):
                self._draw_coin(surface, item, offset_x)
            else:
                self._draw_player(surface, offset_x)

        if "stars" not in pal.particles:
            self.particles.draw(surface)

        vignette(surface, 0.4)
        self._draw_hud(surface)

    def _draw_buildings(self, surface: pygame.Surface, ox: int) -> None:
        pal = self.palette
        for b in sorted(self.buildings, key=lambda b: -b.z):
            near = project(self.cam, b.x, b.height, b.z, self.width, self.height)
            base = project(self.cam, b.x, 0.0, b.z, self.width, self.height)
            if near is None or base is None:
                continue
            half = b.width * 0.5 * near.scale
            left, right = near.x - half + ox, near.x + half + ox
            if right < -40 or left > self.width + 40:
                continue
            color = fogged(self.cam, shade(pal.structure, b.tint), near.depth, pal.fog)
            rect = pygame.Rect(int(left), int(near.y), max(1, int(right - left)), max(1, int(base.y - near.y)))
            pygame.draw.rect(surface, color, rect)

            # Lit windows at night are the cheapest way to make a skyline read
            # as a city rather than a bar chart.
            if pal.time_of_day == "night" and rect.width > 6 and near.depth < 55:
                glow = lerp_rgb(pal.accent, (255, 240, 190), 0.6)
                step = max(4, int(6 * near.scale / 8))
                for wy in range(rect.top + 4, rect.bottom - 2, max(6, step)):
                    for wx in range(rect.left + 2, rect.right - 3, max(6, step)):
                        if (wx * 7 + wy * 13) % 5 < 2:
                            surface.fill(glow, (wx, wy, 2, 3))

    def _draw_track(self, surface: pygame.Surface, ox: int) -> None:
        """Draw the ground as depth-sorted quads.

        Constant Z spacing plus perspective division is the whole motion
        illusion -- the bands bunch up toward the horizon on their own.
        """
        pal = self.palette
        cam = self.cam
        start = math.floor(self.player.z / TIE_SPACING) * TIE_SPACING - TIE_SPACING * 4

        bands: list[tuple[float, float, float, float]] = []
        z = start
        while z < cam.z + cam.far:
            left = project(cam, -TRACK_HALF, 0.0, z, self.width, self.height)
            right = project(cam, TRACK_HALF, 0.0, z, self.width, self.height)
            if left is not None and right is not None:
                bands.append((z, left.x + ox, right.x + ox, left.y))
            z += TIE_SPACING

        for i in range(len(bands) - 1, 0, -1):
            z_far, lf, rf, yf = bands[i]
            _z_near, ln, rn, yn = bands[i - 1]
            index = int(math.floor(z_far / TIE_SPACING))
            base = pal.ground if index % 2 == 0 else pal.ground_alt
            color = fogged(cam, base, z_far - cam.z, pal.fog)
            pygame.draw.polygon(surface, color, [(lf, yf), (rf, yf), (rn, yn), (ln, yn)])

        # Lane dividers, drawn after the ground so they sit on top.
        for divider in (-TRACK_HALF / 3, TRACK_HALF / 3):
            points = []
            for z, _l, _r, _y in bands:
                p = project(cam, divider, 0.01, z, self.width, self.height)
                if p is not None:
                    points.append((p.x + ox, p.y))
            if len(points) > 1:
                pygame.draw.lines(surface, shade(pal.ground_alt, 1.35), False, points, 1)

    def _draw_obstacle(self, surface: pygame.Surface, obs: Obstacle, ox: int) -> None:
        pal = self.palette
        cam = self.cam
        x = LANE_X[obs.lane]
        half_w = 0.95

        if obs.kind == "train":
            self._draw_box(surface, x, 0.0, obs.z, half_w, obs.height, obs.length, pal.structure, ox)
            return
        if obs.kind == "overhead":
            # Hangs from above with a gap underneath to slide through.
            self._draw_box(surface, x, 1.35, obs.z, half_w, obs.height - 1.35, obs.length, pal.hazard, ox)
            return

        color = pal.hazard if obs.kind == "barrier" else pal.accent
        self._draw_box(surface, x, 0.0, obs.z, half_w, obs.height, obs.length, color, ox)

    def _draw_box(
        self,
        surface: pygame.Surface,
        x: float,
        y0: float,
        z: float,
        half_w: float,
        height: float,
        length: float,
        color,
        ox: int,
    ) -> None:
        """A depth-correct box: front face plus a visible side and top."""
        cam = self.cam
        near_bl = project(cam, x - half_w, y0, z, self.width, self.height)
        near_tr = project(cam, x + half_w, y0 + height, z, self.width, self.height)
        far_bl = project(cam, x - half_w, y0, z + length, self.width, self.height)
        far_tr = project(cam, x + half_w, y0 + height, z + length, self.width, self.height)
        if near_bl is None or near_tr is None or far_bl is None or far_tr is None:
            return

        front = fogged(cam, color, near_bl.depth, self.palette.fog)
        side = fogged(cam, shade(color, 0.68), near_bl.depth, self.palette.fog)
        top = fogged(cam, shade(color, 1.18), near_bl.depth, self.palette.fog)

        # Which side face is visible depends on which way the box sits relative
        # to the camera's x.
        if near_bl.x + ox > self.width * 0.5:
            pygame.draw.polygon(
                surface,
                side,
                [
                    (near_bl.x + ox, near_bl.y),
                    (far_bl.x + ox, far_bl.y),
                    (far_bl.x + ox, far_tr.y),
                    (near_bl.x + ox, near_tr.y),
                ],
            )
        else:
            pygame.draw.polygon(
                surface,
                side,
                [
                    (near_tr.x + ox, near_bl.y),
                    (far_tr.x + ox, far_bl.y),
                    (far_tr.x + ox, far_tr.y),
                    (near_tr.x + ox, near_tr.y),
                ],
            )

        pygame.draw.polygon(
            surface,
            top,
            [
                (near_bl.x + ox, near_tr.y),
                (near_tr.x + ox, near_tr.y),
                (far_tr.x + ox, far_tr.y),
                (far_bl.x + ox, far_tr.y),
            ],
        )
        pygame.draw.polygon(
            surface,
            front,
            [
                (near_bl.x + ox, near_bl.y),
                (near_tr.x + ox, near_bl.y),
                (near_tr.x + ox, near_tr.y),
                (near_bl.x + ox, near_tr.y),
            ],
        )

    def _draw_coin(self, surface: pygame.Surface, coin: Coin, ox: int) -> None:
        p = project(self.cam, LANE_X[coin.lane], coin.y, coin.z, self.width, self.height)
        if p is None:
            return
        radius = max(1, int(0.34 * p.scale))
        # Spin: squash horizontally on a sine so it reads as a rotating disc.
        squash = abs(math.sin(self.elapsed * 4.0 + coin.z * 0.5))
        gold = fogged(self.cam, (255, 205, 70), p.depth, self.palette.fog)
        rect = pygame.Rect(0, 0, max(1, int(radius * 2 * (0.25 + squash * 0.75))), radius * 2)
        rect.center = (int(p.x + ox), int(p.y))
        pygame.draw.ellipse(surface, gold, rect)
        if radius > 3:
            pygame.draw.ellipse(surface, shade(gold, 0.75), rect, 1)

    def _draw_player(self, surface: pygame.Surface, ox: int) -> None:
        player = self.player
        pal = self.palette
        p = project(self.cam, player.x, player.y, player.z, self.width, self.height)
        if p is None:
            return

        s = p.scale
        lean = math.sin(player.run_cycle) * 0.12
        if player.crashed:
            lean = player.crash_t * 6.0

        body_h = 1.55 * (0.55 if player.sliding else 1.0)
        cx = p.x + ox
        base_y = p.y

        skin = pal.accent
        cloth = lerp_rgb(pal.accent, pal.ink, 0.55)

        # Legs -- alternating stride, frozen when airborne.
        if not player.sliding:
            swing = math.sin(player.run_cycle) * 0.35 * s
            if player.airborne:
                swing = 0.25 * s
            for sign in (-1, 1):
                pygame.draw.line(
                    surface,
                    cloth,
                    (cx, base_y - 0.55 * body_h * s),
                    (cx + sign * swing, base_y),
                    max(2, int(0.16 * s)),
                )

        torso = pygame.Rect(0, 0, max(2, int(0.62 * s)), max(2, int(0.9 * body_h * s)))
        torso.midbottom = (int(cx + lean * s), int(base_y - 0.5 * body_h * s * 0.0))
        torso.bottom = int(base_y - (0.55 * body_h * s if not player.sliding else 0.05 * s))
        rounded_rect(surface, torso, cloth, radius=max(2, int(0.2 * s)))

        head_r = max(2, int(0.26 * s))
        pygame.draw.circle(surface, skin, (int(torso.centerx), int(torso.top - head_r * 0.7)), head_r)

        # Contact shadow, so the runner is planted rather than floating.
        ground = project(self.cam, player.x, 0.0, player.z, self.width, self.height)
        if ground is not None:
            shadow_w = max(2, int(0.8 * s * (1.0 - player.y / (JUMP_PEAK + 1.0))))
            shadow = pygame.Surface((shadow_w * 2, max(2, shadow_w // 2)), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
            surface.blit(shadow, shadow.get_rect(center=(int(ground.x + ox), int(ground.y))))

    def _draw_hud(self, surface: pygame.Surface) -> None:
        pal = self.palette
        text(surface, f"{int(self.score):,}", self.width - 10, 8, size=22, color=pal.ink, anchor="topright")
        text(surface, f"{self.player.coins} coins", self.width - 10, 34, size=13, color=pal.ink, anchor="topright")
        text(surface, f"{self.palette.time_of_day} · {self.palette.weather}", 10, 8, size=12, color=pal.ink)
