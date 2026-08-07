"""The sky: a 2D backdrop drawn before the 3D world.

Layers, back to front: gradient, stars (night), sun or moon disc with an
additive glow, then two parallax bands of drifting clouds. Everything is
seeded, so run 4712's sky is run 4712's sky forever.
"""

from __future__ import annotations

import math

from ..palette import Palette
from ..rng import Seed
from . import rl, textures


class SkyDome:
    def __init__(self, palette: Palette, seed: Seed, width: int, height: int) -> None:
        self.palette = palette
        self.width = width
        self.height = height
        rng = seed.stream("sky")

        self.gradient = textures.vertical_gradient(
            f"sky-{seed.run}",
            [(0.0, palette.sky_top),
             (0.62, palette.sky_bottom),
             (1.0, rl.mix_rgb(palette.sky_bottom, palette.fog, 0.8))],
        )

        night = palette.time_of_day == "night"
        self.body_is_moon = night
        # The sun sits high off-centre; dawn/dusk pull it toward the horizon.
        horizon_pull = {"day": 0.18, "dawn": 0.46, "dusk": 0.5, "night": 0.2}[palette.time_of_day]
        self.body_x = width * rng.uniform(0.25, 0.75)
        self.body_y = height * horizon_pull * rng.uniform(0.8, 1.2)
        self.body_r = width * (0.10 if not night else 0.07) * rng.uniform(0.9, 1.25)
        self.body_color = {
            "day": (255, 246, 220),
            "dawn": (255, 190, 120),
            "dusk": (255, 160, 96),
            "night": (232, 238, 248),
        }[palette.time_of_day]

        self.stars = []
        if "stars" in palette.particles or night:
            for _ in range(90):
                x = rng.uniform(0, width)
                y = rng.uniform(0, height * 0.75)
                # density thins toward the horizon
                if rng.random() < (y / (height * 0.75)) * 0.7:
                    continue
                self.stars.append((x, y, rng.choice((1, 1, 1, 2)), rng.uniform(0, math.tau)))

        self.clouds = []
        n_clouds = {"clear": 4, "rain": 7, "snow": 6}[palette.weather]
        for i in range(n_clouds):
            tex = textures.cloud_blob(seed.run * 16 + i)
            layer = i % 2
            self.clouds.append({
                "tex": tex,
                "x": rng.uniform(-0.2, 1.2) * width,
                "y": rng.uniform(0.04, 0.42) * height,
                "scale": rng.uniform(0.7, 1.5) * (1.25 if layer else 0.8),
                "speed": (6.0 if layer else 11.0) * rng.uniform(0.8, 1.3),
                "alpha": int(rng.uniform(120, 200)) if not night else int(rng.uniform(60, 110)),
            })
        overcast = palette.weather != "clear"
        self.cloud_tint = rl.mix_rgb(
            rl.mix_rgb(palette.sky_bottom, (255, 255, 255), 0.15 if overcast else 0.75),
            self.body_color, 0.15,
        )

    def draw(self, elapsed: float) -> None:
        rl.DrawTexturePro(
            self.gradient,
            (0, 0, 4, 256),
            (0, 0, self.width, self.height),
            (0, 0), 0.0, rl.WHITE4,
        )

        for x, y, size, phase in self.stars:
            tw = 0.75 + 0.25 * math.sin(elapsed * 1.7 + phase)
            rl.DrawRectangle(int(x), int(y), size, size, (255, 255, 255, int(230 * tw)))

        glow = textures.radial_glow()
        disc = textures.soft_disc()
        gr = self.body_r * 3.2
        rl.BeginBlendMode(rl.BLEND_ADDITIVE)
        rl.DrawTexturePro(glow, (0, 0, 96, 96),
                          (self.body_x - gr, self.body_y - gr, gr * 2, gr * 2),
                          (0, 0), 0.0, rl.rgba(self.body_color, 130))
        rl.EndBlendMode()
        rl.DrawTexturePro(disc, (0, 0, 64, 64),
                          (self.body_x - self.body_r, self.body_y - self.body_r,
                           self.body_r * 2, self.body_r * 2),
                          (0, 0), 0.0, rl.rgba(self.body_color, 255))
        if self.body_is_moon:
            # a bite of sky turns the disc into a crescent
            bite = self.body_r * 1.7
            rl.DrawTexturePro(disc, (0, 0, 64, 64),
                              (self.body_x - self.body_r * 0.55 - bite / 2,
                               self.body_y - self.body_r * 0.4 - bite / 2, bite, bite),
                              (0, 0), 0.0, rl.rgba(self.palette.sky_top, 255))

        for cloud in self.clouds:
            tex = cloud["tex"]
            w = tex.width * cloud["scale"]
            h = tex.height * cloud["scale"]
            x = (cloud["x"] + elapsed * cloud["speed"]) % (self.width + w * 2) - w
            rl.DrawTexturePro(tex, (0, 0, tex.width, tex.height),
                              (x, cloud["y"], w, h), (0, 0), 0.0,
                              rl.rgba(self.cloud_tint, cloud["alpha"]))
