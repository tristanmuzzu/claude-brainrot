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

from ..engine import postfx
from ..engine.draw import Particles, text
from ..engine.projection import Camera, fog_amount, fogged, jump_height, project
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import Sky
from ..engine.texture import apply_texels, facade, soft_glow, sphere, texel_pattern
from ..palette import RGB, lerp_rgb, shade

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

#: Facades are pre-tinted at this many discrete fog depths. Blending a fog
#: colour over a scaled bitmap per building per frame would need a per-pixel
#: alpha surface every time; quantising lets it be a plain blit of a bitmap
#: that was already tinted at construction.
FOG_LEVELS = 7


@dataclass
class Obstacle:
    lane: int
    z: float
    kind: str
    length: float = 2.0
    height: float = 1.0
    style: int = 0

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
    style: int = 0


@dataclass
class Effect:
    """A short-lived visual: dust, sparkle or debris."""

    x: float
    y: float
    z: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: RGB
    kind: str = "dust"
    size: float = 0.2


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

        # Framed for a tall narrow strip: horizon high enough to leave room for
        # the skyline, camera close enough that the character is a readable
        # figure rather than a distant sprite, and the runner sitting around
        # two-thirds down so the track ahead gets the space instead of empty
        # asphalt behind.
        self.cam = Camera(y=3.4, horizon=0.34, far=VIEW_DISTANCE, focal=self.height * 0.62)
        self.player = Player()

        self.speed = 19.0
        self.max_speed = 38.0
        self.obstacles: list[Obstacle] = []
        self.coins: list[Coin] = []
        self.buildings: list[Building] = []
        self.effects: list[Effect] = []

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

        self._build_art(ctx)
        self._warm_up()

    # -- art construction -------------------------------------------------

    def _build_art(self, ctx: SceneContext) -> None:
        """Bake every bitmap this scene will need. Runs once."""
        pal = self.palette
        rng = ctx.stream("runner-art")

        self.sky = Sky(pal, self.width, self.height, rng, horizon=self.cam.horizon)

        lit = lerp_rgb(pal.accent, (255, 236, 170), 0.62)
        dark = shade(pal.structure, 0.42)
        lit_chance = 0.55 if pal.time_of_day == "night" else 0.14

        # Several facade variants so the skyline is not one building repeated.
        self.facades: list[list[pygame.Surface]] = []
        for i in range(5):
            wall = shade(pal.structure, 0.72 + i * 0.13)
            base = facade(48, 192, wall, lit, dark, rng, lit_chance=lit_chance)
            self.facades.append(self._fog_variants(base))

        self.texels_metal = texel_pattern("metal", rng)
        self.texels_stone = texel_pattern("stone", rng)
        self.texels_brick = texel_pattern("brick", rng)

        self.coin_sprite = sphere(14, (255, 206, 74), rim=(255, 246, 190))
        self.coin_glow = soft_glow(22, (255, 190, 60))
        self.spark_glow = soft_glow(16, lerp_rgb(pal.accent, (255, 255, 255), 0.5))

        # Character colours are mostly *fixed* rather than derived from the run.
        # Themed characters sounded good and looked terrible: a green runner on
        # a green day and a pale-haired one at night, because `ink` flips to
        # near-white on dark palettes. Real runners in this genre have a
        # consistent design precisely so they read against any backdrop; only
        # the jacket picks up the run's accent, and only at a guaranteed
        # brightness.
        self.skin = (236, 183, 142)
        self.hair = (44, 34, 40)
        self.trousers = (46, 54, 78)
        self.shoes = (232, 238, 245)
        self.jacket = lerp_rgb(pal.accent, (255, 255, 255), 0.18)
        self.pack = lerp_rgb(pal.hazard, (255, 240, 220), 0.25)

        self._ground_plane = self._build_ground_plane()

    def _fog_variants(self, base: pygame.Surface) -> list[pygame.Surface]:
        """Pre-tint a facade at every fog depth we will ask for."""
        variants = []
        fog = self.palette.fog
        for level in range(FOG_LEVELS):
            amount = level / (FOG_LEVELS - 1)
            copy = base.copy()
            if amount > 0:
                veil = pygame.Surface(base.get_size()).convert()
                veil.fill(fog)
                veil.set_alpha(int(amount * 255))
                copy.blit(veil, (0, 0))
            variants.append(copy.convert())
        return variants

    def _facade_for(self, style: int, depth: float) -> pygame.Surface:
        level = int(fog_amount(self.cam, depth) * (FOG_LEVELS - 1) + 0.5)
        return self.facades[style % len(self.facades)][max(0, min(FOG_LEVELS - 1, level))]

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

        # The gap to the next row is decided up front, because train length has
        # to be clamped against it. A train longer than the gap reaches into the
        # *next* row, where its lane may be that row's safe lane -- and three
        # such overlaps in three lanes wall the track off completely. The
        # per-row corridor guarantee is only a guarantee if obstacles stay
        # inside their own row.
        gap = ROW_SPACING * rng.uniform(0.85, 1.25)
        max_train = max(4.0, gap - 2.5)

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
                    self.obstacles.append(self._make(lane, z, kind, rng, max_train))
                continue

            if rng.random() > self.density:
                continue

            kind = rng.choices(
                ("barrier", "overhead", "cone", "train"),
                weights=(3, 2, 2, 3),
            )[0]
            self.obstacles.append(self._make(lane, z, kind, rng, max_train))

        # Coins trace the corridor between this row and the next.
        if rng.random() < 0.75:
            count = rng.randint(3, 7)
            for i in range(count):
                self.coins.append(Coin(lane=safe, z=z + 3.0 + i * 2.4, y=1.1))

        self._next_row_z += gap

    def _make(
        self, lane: int, z: float, kind: str, rng: random.Random, max_train: float = 12.0
    ) -> Obstacle:
        style = rng.randint(0, 3)
        if kind == "train":
            length = min(rng.uniform(9.0, 18.0), max_train)
            return Obstacle(lane, z, kind, length=length, height=3.2, style=style)
        if kind == "overhead":
            return Obstacle(lane, z, kind, length=1.2, height=2.6, style=style)
        if kind == "barrier":
            return Obstacle(lane, z, kind, length=1.0, height=1.15, style=style)
        return Obstacle(lane, z, kind, length=0.9, height=0.8, style=style)

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
                    style=rng.randint(0, len(self.facades) - 1) if self.facades else 0,
                )
            )
        self._next_building_z += rng.uniform(5.0, 11.0)

    # -- simulation -------------------------------------------------------

    def update(self, dt: float) -> None:
        player = self.player
        was_airborne = player.airborne

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
        self.cam.z = player.z - 6.2
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

        if was_airborne and not player.airborne:
            self._spawn_dust(6)

        player.run_cycle += dt * (self.speed * 0.55)
        player.x += (LANE_X[player.lane] - player.x) * min(1.0, dt * 9.0)

        self._collide()
        self._stream_world()
        self._update_effects(dt)
        self.particles.update(dt)
        self.sky.update(dt, wind=0.6 + self.speed / self.max_speed)
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
            bonus = (
                1.5
                if any(
                    c.lane == lane and not c.taken and ahead_start <= c.z <= ahead_end
                    for c in self.coins
                )
                else 0.0
            )
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
                self._spawn_dust(4)
            elif obs.kind == "overhead":
                player.slide_t = 0.0
                self._spawn_dust(5)
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
            self._spawn_debris()
            return

        for coin in self.coins:
            if coin.taken or coin.lane != player.lane:
                continue
            if abs(coin.z - player.z) < 1.0:
                coin.taken = True
                player.coins += 1
                self._spawn_sparkle(coin)

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

    # -- effects ----------------------------------------------------------

    def _spawn_dust(self, count: int) -> None:
        rng = self.rng_flavour
        for _ in range(count):
            self.effects.append(
                Effect(
                    x=self.player.x + rng.uniform(-0.3, 0.3),
                    y=rng.uniform(0.0, 0.25),
                    z=self.player.z - rng.uniform(0.0, 0.6),
                    vx=rng.uniform(-1.2, 1.2),
                    vy=rng.uniform(0.4, 1.8),
                    life=rng.uniform(0.3, 0.6),
                    max_life=0.6,
                    color=lerp_rgb(self.palette.ground_alt, (255, 255, 255), 0.35),
                    kind="dust",
                    size=rng.uniform(0.14, 0.3),
                )
            )

    def _spawn_sparkle(self, coin: Coin) -> None:
        rng = self.rng_flavour
        for _ in range(7):
            self.effects.append(
                Effect(
                    x=LANE_X[coin.lane] + rng.uniform(-0.3, 0.3),
                    y=coin.y + rng.uniform(-0.2, 0.3),
                    z=coin.z,
                    vx=rng.uniform(-2.0, 2.0),
                    vy=rng.uniform(-0.6, 2.6),
                    life=rng.uniform(0.25, 0.5),
                    max_life=0.5,
                    color=(255, 214, 96),
                    kind="spark",
                    size=rng.uniform(0.08, 0.16),
                )
            )

    def _spawn_debris(self) -> None:
        rng = self.rng_flavour
        for _ in range(14):
            self.effects.append(
                Effect(
                    x=self.player.x + rng.uniform(-0.4, 0.4),
                    y=rng.uniform(0.2, 1.4),
                    z=self.player.z + rng.uniform(-0.3, 0.3),
                    vx=rng.uniform(-3.5, 3.5),
                    vy=rng.uniform(1.0, 4.5),
                    life=rng.uniform(0.4, 0.9),
                    max_life=0.9,
                    color=self.palette.hazard,
                    kind="debris",
                    size=rng.uniform(0.1, 0.24),
                )
            )

    def _update_effects(self, dt: float) -> None:
        alive: list[Effect] = []
        for e in self.effects:
            e.life -= dt
            if e.life <= 0:
                continue
            e.x += e.vx * dt
            e.y += e.vy * dt
            e.vy -= 6.0 * dt  # gravity
            if e.y < 0:
                e.y = 0.0
                e.vy *= -0.3
            alive.append(e)
        # Hard cap: a long crash streak should not accumulate unbounded work.
        self.effects = alive[-160:]

    # -- rendering --------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        pal = self.palette

        self.sky.draw(surface, parallax=self.player.z)

        offset_x = 0
        if self.shake > 0:
            offset_x = int(math.sin(self.elapsed * 60) * self.shake * 5)

        self._draw_ground(surface)
        self._draw_buildings(surface, offset_x)
        self._draw_track(surface, offset_x)

        # Painter's algorithm: everything in the world sorted far to near.
        drawables: list[tuple[float, object]] = []
        drawables += [(o.z, o) for o in self.obstacles]
        drawables += [(c.z, c) for c in self.coins if not c.taken]
        drawables += [(e.z, e) for e in self.effects]
        drawables.append((self.player.z, self.player))
        drawables.sort(key=lambda item: -item[0])

        for _, item in drawables:
            if isinstance(item, Obstacle):
                self._draw_obstacle(surface, item, offset_x)
            elif isinstance(item, Coin):
                self._draw_coin(surface, item, offset_x)
            elif isinstance(item, Effect):
                self._draw_effect(surface, item, offset_x)
            else:
                self._draw_player(surface, offset_x)

        self._draw_speed_lines(surface)
        self.particles.draw(surface)

        postfx.apply_all(
            surface,
            bloom_threshold=postfx.auto_threshold(pal.sky_bottom),
            bloom_intensity=0.95 if pal.time_of_day == "night" else 0.5,
            vignette_strength=0.30,
            quality=self.ctx.quality,
        )
        self._draw_hud(surface)

    def _draw_ground(self, surface: pygame.Surface) -> None:
        """The world below the horizon.

        Without this the sky gradient shows through everywhere the track does
        not cover, so buildings appear to float in mid-air and the strip either
        side of the rails is the wrong colour entirely. Cached, because it never
        changes: the camera's horizon is fixed.
        """
        surface.blit(self._ground_plane, (0, int(self.height * self.cam.horizon)))

    def _build_ground_plane(self) -> pygame.Surface:
        pal = self.palette
        top = int(self.height * self.cam.horizon)
        band = self.height - top
        plane = pygame.Surface((self.width, band)).convert()
        # Fogged at the horizon, resolving to true ground colour underfoot --
        # the same aerial-perspective cue the geometry uses.
        for y in range(band):
            t = (y / max(1, band - 1)) ** 0.55
            pygame.draw.line(
                plane, lerp_rgb(pal.fog, shade(pal.ground, 0.82), t), (0, y), (self.width, y)
            )
        return plane

    def _draw_buildings(self, surface: pygame.Surface, ox: int) -> None:
        """Textured facades with a visible side face for volume."""
        pal = self.palette
        for b in sorted(self.buildings, key=lambda b: -b.z):
            near_top = project(self.cam, b.x, b.height, b.z, self.width, self.height)
            near_base = project(self.cam, b.x, 0.0, b.z, self.width, self.height)
            if near_top is None or near_base is None:
                continue

            half = b.width * 0.5 * near_top.scale
            left, right = near_top.x - half + ox, near_top.x + half + ox
            if right < -60 or left > self.width + 60:
                continue

            # Side face first, so the front overlaps it cleanly.
            far_top = project(self.cam, b.x, b.height, b.z + b.depth, self.width, self.height)
            far_base = project(self.cam, b.x, 0.0, b.z + b.depth, self.width, self.height)
            if far_top is not None and far_base is not None:
                far_half = b.width * 0.5 * far_top.scale
                side_colour = fogged(
                    self.cam, shade(pal.structure, b.tint * 0.62), near_top.depth, pal.fog
                )
                if near_top.x > self.width * 0.5:
                    fx, nx = far_top.x - far_half + ox, left
                else:
                    fx, nx = far_top.x + far_half + ox, right
                pygame.draw.polygon(
                    surface,
                    side_colour,
                    [
                        (nx, near_top.y),
                        (fx, far_top.y),
                        (fx, far_base.y),
                        (nx, near_base.y),
                    ],
                )

            rect = pygame.Rect(
                int(left),
                int(near_top.y),
                max(1, int(right - left)),
                max(1, int(near_base.y - near_top.y)),
            )
            if rect.width < 2 or rect.height < 2:
                continue
            art = self._facade_for(b.style, near_top.depth)
            surface.blit(pygame.transform.scale(art, (rect.width, rect.height)), rect.topleft)

    def _draw_track(self, surface: pygame.Surface, ox: int) -> None:
        """Ground bands, rails and sleepers.

        Constant Z spacing plus perspective division is the whole motion
        illusion -- the bands bunch up toward the horizon on their own. Rails and
        sleepers give the eye something with real structure to track against.
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

        # Sleepers: short crossbars between the rails, one per band.
        sleeper = shade(pal.ground, 0.62)
        for i in range(len(bands) - 1, 0, -1):
            z_far, _lf, _rf, _yf = bands[i]
            if z_far - cam.z > cam.far * 0.55:
                continue
            a = project(cam, -TRACK_HALF * 0.62, 0.02, z_far, self.width, self.height)
            b = project(cam, TRACK_HALF * 0.62, 0.02, z_far, self.width, self.height)
            c = project(cam, TRACK_HALF * 0.62, 0.02, z_far + 0.8, self.width, self.height)
            d = project(cam, -TRACK_HALF * 0.62, 0.02, z_far + 0.8, self.width, self.height)
            if None in (a, b, c, d):
                continue
            pygame.draw.polygon(
                surface,
                fogged(cam, sleeper, z_far - cam.z, pal.fog),
                [(a.x + ox, a.y), (b.x + ox, b.y), (c.x + ox, c.y), (d.x + ox, d.y)],
            )

        # Rails: two bright metal lines, the strongest depth cue on the track.
        rail_colour = lerp_rgb(pal.ground_alt, (255, 255, 255), 0.55)
        for rail_x in (-TRACK_HALF * 0.62, TRACK_HALF * 0.62):
            points = []
            for z, _l, _r, _y in bands:
                p = project(cam, rail_x, 0.06, z, self.width, self.height)
                if p is not None:
                    points.append((p.x + ox, p.y))
            if len(points) > 1:
                pygame.draw.lines(surface, rail_colour, False, points, 2)

        # Lane dividers, thinner and dimmer than the rails.
        for divider in (-TRACK_HALF / 3, TRACK_HALF / 3):
            points = []
            for z, _l, _r, _y in bands:
                p = project(cam, divider, 0.01, z, self.width, self.height)
                if p is not None:
                    points.append((p.x + ox, p.y))
            if len(points) > 1:
                pygame.draw.lines(surface, shade(pal.ground_alt, 1.2), False, points, 1)

        # Raised curbs at the track boundary. Without them the asphalt and the
        # ground plane are two similar greys meeting at an invisible seam, and
        # the track stops reading as a track.
        curb_top = lerp_rgb(pal.ground_alt, (255, 255, 255), 0.35)
        curb_side = shade(pal.ground, 0.55)
        for edge in (-TRACK_HALF, TRACK_HALF):
            top_pts, side_pts = [], []
            for z, _l, _r, _y in bands:
                high = project(cam, edge, 0.34, z, self.width, self.height)
                low = project(cam, edge, 0.0, z, self.width, self.height)
                if high is None or low is None:
                    continue
                top_pts.append((high.x + ox, high.y))
                side_pts.append((low.x + ox, low.y))
            if len(top_pts) > 1:
                # Fill between the curb's top and base as one long quad strip.
                pygame.draw.polygon(surface, curb_side, top_pts + side_pts[::-1])
                pygame.draw.lines(surface, curb_top, False, top_pts, 2)

    def _draw_obstacle(self, surface: pygame.Surface, obs: Obstacle, ox: int) -> None:
        pal = self.palette
        x = LANE_X[obs.lane]
        half_w = 0.95

        if obs.kind == "train":
            self._draw_train(surface, obs, x, half_w, ox)
            return
        if obs.kind == "overhead":
            # Hangs from above with a gap underneath to slide through.
            self._draw_box(
                surface,
                x,
                1.35,
                obs.z,
                half_w,
                obs.height - 1.35,
                obs.length,
                pal.hazard,
                ox,
                texels=self.texels_metal,
                stripes=True,
            )
            return

        color = pal.hazard if obs.kind == "barrier" else pal.accent
        self._draw_box(
            surface,
            x,
            0.0,
            obs.z,
            half_w,
            obs.height,
            obs.length,
            color,
            ox,
            texels=self.texels_stone,
            stripes=obs.kind == "barrier",
        )

    def _draw_train(self, surface: pygame.Surface, obs: Obstacle, x: float, half_w: float, ox: int) -> None:
        """A train carriage: body, window band and a headlamp."""
        pal = self.palette
        body = shade(pal.structure, 1.05 + 0.12 * (obs.style % 3))
        self._draw_box(
            surface,
            x,
            0.0,
            obs.z,
            half_w,
            obs.height,
            obs.length,
            body,
            ox,
            texels=self.texels_metal,
        )

        # Window strip along the visible side, drawn as a run of small quads.
        cam = self.cam
        y0, y1 = obs.height * 0.55, obs.height * 0.82
        side_x = x + (half_w if x > self.cam.x else -half_w)
        glass = lerp_rgb(pal.sky_bottom, (255, 255, 255), 0.45)
        if pal.time_of_day == "night":
            glass = lerp_rgb((255, 226, 150), pal.accent, 0.3)

        step = 1.6
        z = obs.z + 0.6
        while z < obs.z_end - 0.9:
            a = project(cam, side_x, y1, z, self.width, self.height)
            b = project(cam, side_x, y1, z + step * 0.62, self.width, self.height)
            c = project(cam, side_x, y0, z + step * 0.62, self.width, self.height)
            d = project(cam, side_x, y0, z, self.width, self.height)
            if None not in (a, b, c, d) and abs(b.x - a.x) > 1.5:
                pygame.draw.polygon(
                    surface,
                    fogged(cam, glass, a.depth, pal.fog),
                    [(a.x + ox, a.y), (b.x + ox, b.y), (c.x + ox, c.y), (d.x + ox, d.y)],
                )
            z += step

        # Headlamp on the near face, with an additive glow.
        lamp = project(cam, x, obs.height * 0.35, obs.z, self.width, self.height)
        if lamp is not None and lamp.scale > 6:
            radius = max(2, int(0.28 * lamp.scale))
            glow = pygame.transform.smoothscale(self.coin_glow, (radius * 6, radius * 6))
            surface.blit(
                glow,
                glow.get_rect(center=(int(lamp.x + ox), int(lamp.y))),
                special_flags=pygame.BLEND_RGB_ADD,
            )

    def _draw_box(
        self,
        surface: pygame.Surface,
        x: float,
        y0: float,
        z: float,
        half_w: float,
        height: float,
        length: float,
        color: RGB,
        ox: int,
        texels: list | None = None,
        stripes: bool = False,
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
        side = fogged(cam, shade(color, 0.66), near_bl.depth, self.palette.fog)
        top = fogged(cam, shade(color, 1.2), near_bl.depth, self.palette.fog)

        # Which side face is visible depends on which way the box sits relative
        # to the camera's x.
        if near_bl.x + ox > self.width * 0.5:
            side_quad = [
                (near_bl.x + ox, near_bl.y),
                (far_bl.x + ox, far_bl.y),
                (far_bl.x + ox, far_tr.y),
                (near_bl.x + ox, near_tr.y),
            ]
        else:
            side_quad = [
                (near_tr.x + ox, near_bl.y),
                (far_tr.x + ox, far_bl.y),
                (far_tr.x + ox, far_tr.y),
                (near_tr.x + ox, near_tr.y),
            ]
        pygame.draw.polygon(surface, side, side_quad)
        if texels:
            apply_texels(surface, side_quad, texels, side, offset=(z * 0.07, 0.0))

        top_quad = [
            (near_bl.x + ox, near_tr.y),
            (near_tr.x + ox, near_tr.y),
            (far_tr.x + ox, far_tr.y),
            (far_bl.x + ox, far_tr.y),
        ]
        pygame.draw.polygon(surface, top, top_quad)

        front_quad = [
            (near_bl.x + ox, near_bl.y),
            (near_tr.x + ox, near_bl.y),
            (near_tr.x + ox, near_tr.y),
            (near_bl.x + ox, near_tr.y),
        ]
        pygame.draw.polygon(surface, front, front_quad)

        if stripes and near_bl.scale > 10:
            # Hazard chevrons: the visual language for "do not run into this".
            warn = lerp_rgb(front, (255, 244, 210), 0.75)
            for i in range(3):
                t0 = i / 3 + 0.06
                t1 = t0 + 0.18
                ax = near_bl.x + (near_tr.x - near_bl.x) * t0 + ox
                bx = near_bl.x + (near_tr.x - near_bl.x) * t1 + ox
                pygame.draw.polygon(
                    surface,
                    warn,
                    [
                        (ax, near_bl.y),
                        (bx, near_bl.y),
                        (bx, near_tr.y),
                        (ax, near_tr.y),
                    ],
                )

        # Rim highlight along the top edge catches the eye and separates the
        # box from whatever is behind it.
        pygame.draw.line(
            surface,
            lerp_rgb(top, (255, 255, 255), 0.4),
            (near_bl.x + ox, near_tr.y),
            (near_tr.x + ox, near_tr.y),
            max(1, int(near_bl.scale * 0.02)),
        )

    def _draw_coin(self, surface: pygame.Surface, coin: Coin, ox: int) -> None:
        p = project(self.cam, LANE_X[coin.lane], coin.y, coin.z, self.width, self.height)
        if p is None:
            return
        radius = max(1, int(0.34 * p.scale))
        if radius < 2:
            return

        # Spin: squash horizontally on a sine so it reads as a rotating disc.
        squash = abs(math.sin(self.elapsed * 4.0 + coin.z * 0.5))
        width = max(2, int(radius * 2 * (0.28 + squash * 0.72)))
        height = radius * 2

        if radius > 3:
            glow = pygame.transform.smoothscale(self.coin_glow, (int(width * 2.6), int(height * 2.6)))
            surface.blit(
                glow,
                glow.get_rect(center=(int(p.x + ox), int(p.y))),
                special_flags=pygame.BLEND_RGB_ADD,
            )

        sprite = pygame.transform.smoothscale(self.coin_sprite, (width, height))
        surface.blit(sprite, sprite.get_rect(center=(int(p.x + ox), int(p.y))))

    def _draw_effect(self, surface: pygame.Surface, e: Effect, ox: int) -> None:
        p = project(self.cam, e.x, e.y, e.z, self.width, self.height)
        if p is None:
            return
        fade = max(0.0, e.life / e.max_life)
        radius = max(1, int(e.size * p.scale * (0.6 + fade)))
        if radius < 1:
            return

        if e.kind == "spark":
            size = radius * 5
            glow = pygame.transform.smoothscale(self.spark_glow, (size, size))
            glow.set_alpha(int(255 * fade))
            surface.blit(
                glow, glow.get_rect(center=(int(p.x + ox), int(p.y))), special_flags=pygame.BLEND_RGB_ADD
            )
            return

        colour = lerp_rgb(self.palette.fog, e.color, fade)
        pygame.draw.circle(surface, colour, (int(p.x + ox), int(p.y)), radius)

    def _draw_speed_lines(self, surface: pygame.Surface) -> None:
        """Radial streaks from the vanishing point at high speed.

        Purely a velocity cue -- the track already moves correctly, but streaks
        are what make it *feel* fast.
        """
        ratio = (self.speed - 26.0) / max(1.0, self.max_speed - 26.0)
        if ratio <= 0.05:
            return
        cx, cy = self.width * 0.5, self.height * self.cam.horizon

        # Streaks live only in the outer margin. Drawn across the whole frame
        # they stop reading as motion and start reading as scratches on the
        # lens, which is worse than having no speed cue at all.
        streaks = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        colour = lerp_rgb(self.palette.fog, (255, 255, 255), 0.75)
        count = int(9 * ratio)
        for i in range(count):
            angle = (i / max(1, count)) * math.tau + self.elapsed * 0.9
            inner = self.width * (0.72 + 0.10 * math.sin(angle * 3.0 + self.elapsed * 2))
            outer = inner + self.width * 0.16 * ratio
            sin_a, cos_a = math.sin(angle), math.cos(angle)
            pygame.draw.line(
                streaks,
                (*colour, int(90 * ratio)),
                (cx + cos_a * inner, cy + sin_a * inner),
                (cx + cos_a * outer, cy + sin_a * outer),
                2,
            )
        surface.blit(streaks, (0, 0))

    # -- character --------------------------------------------------------

    def _draw_player(self, surface: pygame.Surface, ox: int) -> None:
        """An articulated runner seen from behind.

        Two-segment limbs with real joints, a run cycle driven by one phase
        value, and distinct poses for jumping, sliding and crashing. A capsule
        with two lines reads as a placeholder; this reads as a character.
        """
        player = self.player
        p = project(self.cam, player.x, player.y, player.z, self.width, self.height)
        if p is None:
            return

        s = p.scale
        if s < 4:
            return
        cx = p.x + ox
        ground_y = p.y
        phase = player.run_cycle

        # Contact shadow first, so everything else sits on top of it.
        ground = project(self.cam, player.x, 0.0, player.z, self.width, self.height)
        if ground is not None:
            lift = 1.0 - min(1.0, player.y / (JUMP_PEAK + 0.6))
            shadow_w = max(3, int(0.85 * s * (0.4 + 0.6 * lift)))
            shadow = pygame.Surface((shadow_w * 2, max(3, shadow_w)), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, int(110 * lift)), shadow.get_rect())
            surface.blit(shadow, shadow.get_rect(center=(int(ground.x + ox), int(ground.y))))

        crashed = player.crashed
        sliding = player.sliding
        airborne = player.airborne

        # Pose parameters. Everything below is expressed relative to `s`, so the
        # character scales correctly with distance.
        if crashed:
            tumble = player.crash_t * 9.0
            lean = math.sin(tumble) * 0.9
            crouch = 0.55
        elif sliding:
            lean = 1.25
            crouch = 0.42
        elif airborne:
            lean = 0.18
            crouch = 0.86
        else:
            lean = 0.10 + math.sin(phase * 2) * 0.05
            crouch = 1.0

        hip_y = ground_y - 0.78 * s * crouch
        shoulder_y = hip_y - 0.52 * s * crouch
        lean_px = lean * 0.32 * s

        # -- legs
        if sliding:
            leg_angles = (-1.25, -1.05)
        elif airborne:
            leg_angles = (-0.42, 0.55)
        else:
            # +/- 0.52 rad is about 30 degrees of swing. The 0.95 this started
            # at is 54 degrees, which is not a run -- it is doing the splits.
            leg_angles = (math.sin(phase) * 0.52, math.sin(phase + math.pi) * 0.52)

        for i, angle in enumerate(leg_angles):
            knee_bend = 0.30 + 0.34 * max(0.0, math.cos(phase + i * math.pi))
            self._limb(
                surface,
                cx + lean_px * 0.3 + (i - 0.5) * 0.16 * s,
                hip_y,
                angle,
                0.42 * s * crouch,
                angle + knee_bend,
                0.40 * s * crouch,
                max(2, int(0.15 * s)),
                self.trousers,
                foot_color=self.shoes,
                foot_size=max(2, int(0.13 * s)),
            )

        # -- torso: a tapered quad, wider at the shoulders
        hip_w = 0.24 * s
        shoulder_w = 0.32 * s
        torso = [
            (cx - hip_w + lean_px * 0.25, hip_y),
            (cx + hip_w + lean_px * 0.25, hip_y),
            (cx + shoulder_w + lean_px, shoulder_y),
            (cx - shoulder_w + lean_px, shoulder_y),
        ]
        pygame.draw.polygon(surface, self.jacket, torso)
        # Centre seam gives the flat jacket some form.
        pygame.draw.line(
            surface,
            shade(self.jacket, 0.82),
            (cx + lean_px * 0.25, hip_y),
            (cx + lean_px, shoulder_y),
            max(1, int(0.04 * s)),
        )

        # -- backpack, the single most recognisable runner silhouette cue
        if s > 12:
            pack_w = int(0.34 * s)
            pack_h = int(0.40 * s)
            pack_rect = pygame.Rect(0, 0, pack_w, pack_h)
            pack_rect.center = (
                int(cx + lean_px * 0.8),
                int(shoulder_y + 0.16 * s),
            )
            pygame.draw.rect(surface, self.pack, pack_rect, border_radius=max(2, pack_w // 4))
            pygame.draw.rect(
                surface, shade(self.pack, 0.7), pack_rect, width=max(1, int(0.03 * s)),
                border_radius=max(2, pack_w // 4),
            )

        # -- arms, swinging opposite the legs
        if sliding:
            arm_angles = (1.35, 1.15)
        elif airborne:
            arm_angles = (-1.05, -0.75)
        else:
            arm_angles = (math.sin(phase + math.pi) * 0.62, math.sin(phase) * 0.62)

        for i, angle in enumerate(arm_angles):
            self._limb(
                surface,
                cx + lean_px + (i - 0.5) * 0.56 * s,
                shoulder_y + 0.06 * s,
                angle,
                0.30 * s * crouch,
                angle + 0.6,
                0.26 * s * crouch,
                max(2, int(0.11 * s)),
                self.jacket,
                foot_color=self.skin,
                foot_size=max(1, int(0.09 * s)),
            )

        # -- head. Seen from behind, so it is mostly hair with a sliver of neck;
        # layering skin over hair the other way round just looked like a mask.
        head_r = max(2, int(0.22 * s))
        head_cx = int(cx + lean_px * 1.25)
        head_cy = int(shoulder_y - head_r * 0.80)
        pygame.draw.circle(surface, self.skin, (head_cx, head_cy + head_r // 2), int(head_r * 0.72))
        pygame.draw.circle(surface, self.hair, (head_cx, head_cy), head_r)
        if head_r > 4:
            # Off-centre highlight suggests a light source and rounds the head.
            pygame.draw.circle(
                surface,
                lerp_rgb(self.hair, (255, 255, 255), 0.28),
                (head_cx - head_r // 3, head_cy - head_r // 3),
                max(1, head_r // 3),
            )

    def _limb(
        self,
        surface: pygame.Surface,
        x: float,
        y: float,
        angle_a: float,
        len_a: float,
        angle_b: float,
        len_b: float,
        width: int,
        color: RGB,
        foot_color: RGB | None = None,
        foot_size: int = 0,
    ) -> None:
        """Two-segment limb with a rounded joint.

        Drawing the joint as a circle at the knee/elbow is what stops the two
        segments reading as a broken stick.
        """
        joint_x = x + math.sin(angle_a) * len_a
        joint_y = y + math.cos(angle_a) * len_a
        end_x = joint_x + math.sin(angle_b) * len_b
        end_y = joint_y + math.cos(angle_b) * len_b

        pygame.draw.line(surface, color, (x, y), (joint_x, joint_y), width)
        pygame.draw.circle(surface, color, (int(joint_x), int(joint_y)), max(1, width // 2))
        pygame.draw.line(surface, shade(color, 0.9), (joint_x, joint_y), (end_x, end_y), width)

        if foot_color is not None and foot_size > 0:
            pygame.draw.circle(surface, foot_color, (int(end_x), int(end_y)), foot_size)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        pal = self.palette
        text(surface, f"{int(self.score):,}", self.width - 10, 8, size=22, color=pal.ink, anchor="topright")
        text(surface, f"{self.player.coins} coins", self.width - 10, 34, size=13, color=pal.ink, anchor="topright")
        text(surface, f"{pal.time_of_day} · {pal.weather}", 10, 8, size=12, color=pal.ink)
