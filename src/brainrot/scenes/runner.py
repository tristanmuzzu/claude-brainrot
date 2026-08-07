"""The endless runner, rebuilt on real 3D assets.

Layout follows the reference format exactly: three locked lanes, a chase
camera behind and above, trains and barriers streaming toward the player,
coin arcs along a guaranteed-clear corridor, city canyon either side.

World model: the runner stays at the origin; the world flows past. Every
entity carries ``d`` -- its distance ahead of the runner along the track --
which shrinks by the run speed each frame and maps to ``z = -d`` at draw
time. Content is generated per 6 m *row* from a per-row substream, so a run
number always replays the same world.

The solvability invariant is inherited from the first version: each row is
assigned a clear lane before obstacles are placed, and that lane moves at
most one lane between rows. Blocking obstacles only ever go in the lanes the
corridor does not occupy; the corridor itself only carries things the runner
can jump or roll through.
"""

from __future__ import annotations

import math

from .. import assets
from ..engine import rl
from ..engine.fx import Burst, Weather, blob_shadow, glow_billboard
from ..engine.hud import text
from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import SkyDome

LANE_X = 2.4                  # must match assets/src/track.py LANE_SPACING
ROW = 6.0                     # generation stride; also the track tile length
VIEW_AHEAD = 96.0             # spawn horizon
VIEW_BEHIND = 16.0
FOG_FAR = 88.0

BASE_SPEED = 8.5
TOP_SPEED = 15.5
RAMP_SECONDS = 75.0

JUMP_TIME = 0.62
JUMP_HEIGHT = 1.5
ROLL_TIME = 0.55
RAIL_TOP = 0.30               # y of the railhead the runner runs on


@register("runner")
class RunnerScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        seed = ctx.seed
        pal = ctx.palette

        self.sky = SkyDome(pal, seed, ctx.width, ctx.height)
        self.weather = Weather(pal, ctx.width, ctx.height, seed.root & 0xFFFF)
        self.burst = Burst()
        self.camera = rl.make_camera(58.0)

        # -- assets ------------------------------------------------------
        self.track = assets.load("track")
        self.character = assets.load("character")
        self.train_cab = assets.load("train_cab")
        self.train_car = assets.load("train_car")
        self.barrier = assets.load("barrier")
        self.gantry = assets.load("gantry")
        self.fence = assets.load("fence")
        self.pillar = assets.load("pillar")
        self.coin = assets.load("coin")
        self.buildings = [assets.load(f"building_{c}") for c in "abc"]

        style = seed.stream("wardrobe")
        self.outfit = {
            "hoodie": pal.accent,
            "cap": pal.accent2,
            "pants": (40, 48, 82) if not pal.is_dark else (58, 62, 96),
            "pack": pal.hazard if style.random() < 0.5 else pal.accent2,
        }
        self.train_liveries = [pal.accent, pal.accent2, pal.train, pal.hazard]

        # -- world state -------------------------------------------------
        self.rng = ctx.stream("runner-layout")
        self.travel = 0.0
        self.speed = BASE_SPEED
        self.next_row = 2          # rows 0-1 stay clear, like the original
        self.corridor: dict[int, int] = {0: 1, 1: 1}
        self.entities: list[dict] = []
        self.score = 0.0
        self.coins = 0

        # -- runner state ------------------------------------------------
        self.lane = 1              # 0 left, 1 centre, 2 right
        self.x = 0.0
        self.jump_t = -1.0         # active while in [0, JUMP_TIME]
        self.roll_t = -1.0
        self.run_phase = 0.0
        self.cam_shake = 0.0

        self._spawn_to_horizon()

    # -- generation -------------------------------------------------------

    def _lane_clear(self, row: int) -> int:
        lane = self.corridor.get(row)
        if lane is None:
            prev = self._lane_clear(row - 1) if row > 0 else 1
            step = self.rng.choice((-1, 0, 0, 1))
            lane = max(0, min(2, prev + step))
            self.corridor[row] = lane
        return lane

    def _spawn_to_horizon(self) -> None:
        while self.next_row * ROW < self.travel + VIEW_AHEAD:
            self._spawn_row(self.next_row)
            self.next_row += 1

    def _spawn_row(self, row: int) -> None:
        d0 = row * ROW - self.travel
        rng = self.ctx.seed.stream(f"row{row}")
        clear = self._lane_clear(row)
        blocked = [ln for ln in (0, 1, 2) if ln != clear]

        roll = rng.random()
        if roll < 0.27 and row > 3:
            # a train: 2-4 cars in a blocked lane, parked or oncoming. At most
            # one oncoming train exists at a time: with two, the dodge search
            # can find every lane swept at once and the runner has no answer.
            lane = rng.choice(blocked)
            cars = rng.randint(2, 4)
            oncoming = rng.random() < 0.35 and not any(
                e["kind"] == "train" and e["vel"] for e in self.entities)
            livery = rng.choice(self.train_liveries)
            self.entities.append({
                "kind": "train", "lane": lane, "d": d0 + ROW * 0.5,
                "cars": cars, "vel": (self.speed * 0.55 + 4.5) if oncoming else 0.0,
                "color": livery,
            })
        elif roll < 0.55 and row > 2:
            # barriers: all blocked lanes, sometimes the corridor too (jumpable)
            for lane in blocked:
                if rng.random() < 0.75:
                    self.entities.append({"kind": "barrier", "lane": lane, "d": d0})
            if rng.random() < 0.5:
                self.entities.append({"kind": "barrier", "lane": clear, "d": d0})
        elif roll < 0.68 and row > 2:
            # low gantry across the whole track: everyone rolls
            self.entities.append({"kind": "gantry", "lane": 1, "d": d0, "low": True})
        elif roll < 0.78:
            self.entities.append({"kind": "gantry", "lane": 1, "d": d0, "low": False})

        # coins ride the corridor, arcing over any jumpable on it
        if rng.random() < 0.6 and row > 1:
            over = any(e["kind"] == "barrier" and e["lane"] == clear
                       and abs(e["d"] - d0) < 1.0 for e in self.entities)
            n = rng.randint(4, 7)
            for i in range(n):
                dd = d0 + (i - n / 2) * 0.9
                y = 0.55 + (1.35 * math.sin(math.pi * i / (n - 1)) if over else 0.0)
                self.entities.append({"kind": "coin", "lane": clear, "d": dd,
                                      "y": y, "taken": False})

        # city canyon: a building per side on an independent cadence
        for side in (-1, 1):
            srng = self.ctx.seed.stream(f"city{side}{row}")
            if srng.random() < 0.8:
                idx = srng.randrange(3)
                dist = srng.uniform(10.5, 16.0)
                tone = 0.55 + srng.random() * 0.5
                self.entities.append({
                    "kind": "building", "x": side * dist, "d": d0 + srng.uniform(0, ROW),
                    "idx": idx, "yaw": 90.0 if side < 0 else -90.0,
                    "tone": tone,
                })
            if srng.random() < 0.22:
                self.entities.append({"kind": "pillar",
                                      "x": side * srng.uniform(6.8, 8.4),
                                      "d": d0 + srng.uniform(0, ROW)})

    # -- simulation -------------------------------------------------------

    def update(self, dt: float) -> None:
        self.speed = min(TOP_SPEED, BASE_SPEED
                         + (TOP_SPEED - BASE_SPEED) * (self.elapsed / RAMP_SECONDS))
        step = self.speed * dt
        self.travel += step
        self.score += self.speed * dt * 3.2
        self.run_phase += dt * (2.6 + self.speed * 0.34)
        self.cam_shake = max(0.0, self.cam_shake - dt * 3.0)

        for e in self.entities:
            e["d"] -= step
            if e["kind"] == "train" and e["vel"]:
                e["d"] -= e["vel"] * dt
        self.entities = [e for e in self.entities if e["d"] > -VIEW_BEHIND]
        self._spawn_to_horizon()

        # steer toward the corridor of the nearest upcoming row
        row_ahead = int((self.travel + 7.0) / ROW)
        target = self._lane_clear(row_ahead)

        # The corridor only guarantees a path through *static* obstacles. An
        # oncoming train sweeps across rows, so its lane is dangerous wherever
        # the train currently is -- dodge it live, like the game it imitates.
        danger: dict[int, float] = {}
        for e in self.entities:
            if e["kind"] == "train":
                length = e["cars"] * 5.1
                horizon = 34.0 if e["vel"] else 10.0
                if -length < e["d"] < horizon:
                    danger[e["lane"]] = min(danger.get(e["lane"], 1e9), e["d"])
        if target in danger:
            safe = [ln for ln in (0, 1, 2) if ln not in danger]
            if safe:
                target = min(safe, key=lambda ln: abs(ln - self.lane))
            else:
                # every lane threatened: take the one whose train is furthest
                target = max(danger, key=lambda ln: danger[ln])
        # Lane changes work mid-air too (they do in the reference game) --
        # freezing them during a jump would let a dodge arrive too late.
        self.lane = target
        self.x += (self._lane_x(self.lane) - self.x) * min(1.0, dt * 7.5)

        # react to whatever is coming up in my lane
        if self.jump_t < 0 and self.roll_t < 0:
            for e in self.entities:
                if e["kind"] == "barrier" and e["lane"] == self.lane and 1.8 < e["d"] < 2.9:
                    self.jump_t = 0.0
                    break
                if e["kind"] == "gantry" and e.get("low") and 1.6 < e["d"] < 2.7:
                    self.roll_t = 0.0
                    break
            else:
                # style jumps only in calm moments, never while dodging
                if not danger and self.rng.random() < dt * 0.06:
                    self.jump_t = 0.0

        if self.jump_t >= 0:
            self.jump_t += dt
            if self.jump_t >= JUMP_TIME:
                self.jump_t = -1.0
                self.cam_shake = 0.5
        if self.roll_t >= 0:
            self.roll_t += dt
            if self.roll_t >= ROLL_TIME:
                self.roll_t = -1.0

        # coin pickup
        y_me = self._jump_y()
        for e in self.entities:
            if e["kind"] == "coin" and not e["taken"] and abs(e["d"]) < 0.6:
                if abs(self._lane_x(e["lane"]) - self.x) < 0.9 and abs(e["y"] - 0.4 - y_me) < 1.1:
                    e["taken"] = True
                    self.coins += 1
                    self.score += 25
                    self.burst.spawn(self.x, RAIL_TOP + e["y"], -e["d"], (255, 215, 80),
                                     count=8, rng=self.rng)
        self.burst.update(dt)

    def _lane_x(self, lane: int) -> float:
        return (lane - 1) * LANE_X

    def _jump_y(self) -> float:
        if self.jump_t < 0:
            return 0.0
        t = self.jump_t / JUMP_TIME
        return JUMP_HEIGHT * 4.0 * t * (1.0 - t)

    # -- drawing ----------------------------------------------------------

    def _fog(self, d: float, alpha: int = 255):
        f = max(0.0, min(1.0, d / FOG_FAR))
        f = f * f * (3 - 2 * f)
        return rl.rgba(rl.mix_rgb((255, 255, 255), self.palette.fog, f), alpha)

    def draw(self) -> None:
        pal = self.palette
        self.sky.draw(self.elapsed)

        cam = self.camera
        bob = math.sin(self.run_phase * 2.0) * 0.05 * (self.speed / TOP_SPEED)
        shake = (math.sin(self.elapsed * 43.0) * 0.05 + math.sin(self.elapsed * 61.0) * 0.03) * self.cam_shake
        # Ride directly behind the runner: with the camera between lanes, a
        # passing train in the next lane would wipe across the whole frame.
        cam.position = (self.x * 0.92 + shake, 3.7 + bob, 7.4)
        cam.target = (self.x, 1.45 + bob * 0.5 + shake * 0.6, -5.0)
        cam.fovy = 56.0 + 6.0 * (self.speed - BASE_SPEED) / (TOP_SPEED - BASE_SPEED)

        rl.BeginMode3D(cam[0])

        # ground plane under everything; fog handled by the horizon haze
        rl.DrawPlane((0, -0.05, -30), (240, 160), rl.rgba(pal.ground, 255))

        # track tiles, snapped to the row grid
        first = int((self.travel - 8) / ROW)
        for k in range(first, first + int((VIEW_AHEAD + 16) / ROW)):
            d = k * ROW - self.travel + ROW / 2
            if d < -VIEW_BEHIND:
                continue
            rl.DrawModelEx(self.track.model, (0, 0, -d), (0, 1, 0), 0.0,
                           (1, 1, 1), self._fog(d))
            # lineside fences ride the same grid
            for side in (-1, 1):
                rl.DrawModelEx(self.fence.model, (side * 6.3, 0, -d), (0, 1, 0), 90.0,
                               (1, 1, 1), self._fog(d))
                rl.DrawModelEx(self.fence.model, (side * 6.3, 0, -d + 3.0), (0, 1, 0), 90.0,
                               (1, 1, 1), self._fog(d))

        # far-to-near keeps alpha'd glows honest without a sort pass
        for e in sorted(self.entities, key=lambda e: -e["d"]):
            d = e["d"]
            if d > VIEW_AHEAD:
                continue
            fog = self._fog(d)
            kind = e["kind"]
            if kind == "building":
                b = self.buildings[e["idx"]]
                t = e["tone"]
                b.recolor({"wall": rl.scale_rgb(pal.structure, t),
                           "trim": rl.scale_rgb(pal.structure, t * 0.7),
                           "window": pal.window_lit if pal.is_dark
                           else rl.mix_rgb(pal.sky_bottom, (255, 255, 255), 0.35)})
                rl.DrawModelEx(b.model, (e["x"], 0, -d), (0, 1, 0), e["yaw"], (1, 1, 1), fog)
            elif kind == "pillar":
                rl.DrawModelEx(self.pillar.model, (e["x"], 0, -d), (0, 1, 0), 0, (1, 1, 1), fog)
            elif kind == "train":
                self._draw_train(e, fog)
            elif kind == "barrier":
                self.barrier.recolor({"stripe": pal.hazard})
                rl.DrawModelEx(self.barrier.model, (self._lane_x(e["lane"]), 0.28, -d),
                               (0, 1, 0), 0, (1, 1, 1), fog)
            elif kind == "gantry":
                y = 0.0 if e.get("low") else 0.9
                rl.DrawModelEx(self.gantry.model, (0, y + 0.28, -d), (0, 1, 0), 0,
                               (1, 1, 1), fog)
            elif kind == "coin" and not e["taken"]:
                x = self._lane_x(e["lane"])
                y = RAIL_TOP + e["y"] + math.sin(self.elapsed * 3 + d) * 0.06
                rl.DrawModelEx(self.coin.model, (x, y, -d), (0, 1, 0),
                               (self.elapsed * 220 + d * 40) % 360,
                               (0.55, 0.55, 0.55), fog)

        self._draw_runner()
        for e in self.entities:
            if e["kind"] == "coin" and not e["taken"] and e["d"] < 30:
                glow_billboard(self.camera, self._lane_x(e["lane"]),
                               RAIL_TOP + e["y"], -e["d"], 0.6, (255, 200, 60), 55)
            elif e["kind"] == "train" and e["vel"] and pal.is_dark and e["d"] < 70:
                # oncoming headlights punching through the dark
                x_t = self._lane_x(e["lane"])
                for side in (-1, 1):
                    glow_billboard(self.camera, x_t + side * 0.6, 1.05,
                                   -e["d"] - 2.9, 1.6, (255, 235, 170), 120)
        self.burst.draw(self.camera)
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        self._draw_hud()

    def _draw_train(self, e: dict, fog) -> None:
        x = self._lane_x(e["lane"])
        self.train_cab.recolor({"body": e["color"]})
        self.train_car.recolor({"body": e["color"]})
        yaw = 0.0 if e["vel"] else 180.0     # oncoming trains face the runner
        d = e["d"]
        rl.DrawModelEx(self.train_cab.model, (x, 0, -d), (0, 1, 0), 90.0 + yaw,
                       (1, 1, 1), fog)
        for i in range(1, e["cars"]):
            rl.DrawModelEx(self.train_car.model, (x, 0, -(d + i * 5.1)), (0, 1, 0),
                           90.0 + yaw, (1, 1, 1), self._fog(d + i * 5.1))

    def _draw_runner(self) -> None:
        ch = self.character
        ch.recolor(self.outfit)
        y = self._jump_y()

        if self.jump_t >= 0:
            ch.pose("jump", self.jump_t / JUMP_TIME)
        elif self.roll_t >= 0:
            ch.pose("roll", self.roll_t / ROLL_TIME)
        else:
            ch.pose("run", self.run_phase % 1.0)

        lean = (self._lane_x(self.lane) - self.x) * -14.0
        transform = rl.MatrixMultiply(
            rl.MatrixRotateY(math.radians(90)),
            rl.MatrixRotateZ(math.radians(lean)),
        )
        ch.model.transform = transform
        blob_shadow(self.x, RAIL_TOP + 0.04, 0.0, 0.62, alpha=int(110 * (1.0 - y / 3.0)))
        rl.DrawModelEx(ch.model, (self.x, RAIL_TOP + y, 0), (0, 1, 0), 0.0,
                       (0.86, 0.86, 0.86), rl.WHITE4)

    def _draw_hud(self) -> None:
        pal = self.palette
        text(f"{int(self.score):06d}", self.width - 14, 12, 26, pal.ink, anchor="topright")
        # coin counter with a little gold disc
        rl.DrawCircle(self.width - 66, 58, 7, (255, 205, 60, 255))
        rl.DrawCircle(self.width - 66, 58, 4, (255, 235, 140, 255))
        text(f"{self.coins}", self.width - 14, 48, 20, (255, 215, 90), anchor="topright")
