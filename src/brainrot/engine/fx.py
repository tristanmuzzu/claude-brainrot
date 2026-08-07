"""Screen-space weather, 3D glows, blob shadows and particle bursts."""

from __future__ import annotations

import math
import random

from ..palette import Palette
from . import rl, textures

_QUAD_CACHE: dict[str, object] = {}


def unit_quad(key: str):
    """A flat unit quad in the XZ plane, with UVs and its own material.

    One place builds these. Every scene that wanted a textured sheet used to
    hand-roll the mesh, and a hand-rolled one that gets a detail wrong does not
    fail -- it draws the tint over the whole quad and ignores the texture's
    alpha, which looks like a deliberate opaque slab rather than like a bug.

    Cached per ``key``, so each caller owns its own material and can hang its
    own texture on it without disturbing anyone else's.
    """
    model = _QUAD_CACHE.get(key)
    if model is not None:
        return model
    mesh = rl.ffi.new("Mesh *")
    verts = [(-0.5, 0, -0.5), (0.5, 0, -0.5), (0.5, 0, 0.5), (-0.5, 0, 0.5)]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    tris = [0, 2, 1, 0, 3, 2]
    mesh.vertexCount = 4
    mesh.triangleCount = 2
    keep = []
    mesh.vertices = vb = rl.ffi.new("float[]", [c for v in verts for c in v]); keep.append(vb)
    mesh.normals = nb = rl.ffi.new("float[]", [0, 1, 0] * 4); keep.append(nb)
    mesh.texcoords = tb = rl.ffi.new("float[]", [c for uv in uvs for c in uv]); keep.append(tb)
    mesh.indices = ib = rl.ffi.new("unsigned short[]", tris); keep.append(ib)
    rl.UploadMesh(mesh, False)
    model = rl.LoadModelFromMesh(mesh[0])
    _QUAD_CACHE[key] = model
    _QUAD_CACHE[f"{key}-keep"] = (mesh, keep)
    return model


def ground_quad():
    """The blob-shadow quad: a unit XZ quad wearing a soft disc."""
    model = _QUAD_CACHE.get("ground")
    if model is None:
        model = unit_quad("ground")
        model.materials[0].maps[rl.MATERIAL_MAP_ALBEDO].texture = textures.soft_disc(64)
    return model


def blob_shadow(x: float, y: float, z: float, radius: float, alpha: int = 110) -> None:
    """A soft dark disc on the ground plane under something airborne."""
    rl.DrawModelEx(ground_quad(), (x, y + 0.02, z), (0, 1, 0), 0.0,
                   (radius * 2, 1.0, radius * 2), (0, 0, 0, alpha))


def glow_billboard(camera, x: float, y: float, z: float, size: float,
                   color: rl.RGB, alpha: int = 160) -> None:
    """Additive radial glow facing the camera -- coins, lamps, pickups."""
    rl.BeginBlendMode(rl.BLEND_ADDITIVE)
    rl.DrawBillboard(camera[0], textures.radial_glow(), (x, y, z), size,
                     rl.rgba(color, alpha))
    rl.EndBlendMode()


class Weather:
    """Rain streaks or snow flakes in screen space, on top of the world.

    Screen space rather than world space because that is what the reference
    material does: the streaks read as being on the lens, and they never need
    culling or respawning logic in the world.
    """

    def __init__(self, palette: Palette, width: int, height: int, seed_val: int = 0) -> None:
        self.kind = palette.weather
        self.width = width
        self.height = height
        rng = random.Random(seed_val)
        self.drops = []
        if self.kind == "rain":
            for _ in range(70):
                self.drops.append([rng.uniform(0, width), rng.uniform(0, height),
                                   rng.uniform(380, 560), rng.uniform(0.35, 0.8)])
        elif self.kind == "snow":
            for _ in range(60):
                self.drops.append([rng.uniform(0, width), rng.uniform(0, height),
                                   rng.uniform(35, 80), rng.uniform(0.4, 1.0),
                                   rng.uniform(0, math.tau)])

    def draw(self, elapsed: float) -> None:
        if self.kind == "rain":
            for x0, y0, speed, depth in self.drops:
                y = (y0 + elapsed * speed) % (self.height + 30) - 15
                x = (x0 - elapsed * speed * 0.12) % self.width
                length = 10 + depth * 12
                a = int(90 + depth * 90)
                rl.DrawLineEx((x, y), (x - length * 0.18, y + length), 1.2,
                              (210, 225, 245, a))
        elif self.kind == "snow":
            for x0, y0, speed, depth, phase in self.drops:
                y = (y0 + elapsed * speed) % (self.height + 12) - 6
                x = (x0 + math.sin(elapsed * 1.3 + phase) * 14 * depth) % self.width
                r = 1.0 + depth * 1.8
                rl.DrawCircle(int(x), int(y), r, (255, 255, 255, int(120 + depth * 110)))


class Burst:
    """A one-shot particle burst: coin pickups, landings, confetti."""

    def __init__(self) -> None:
        self.particles: list[list[float]] = []

    def spawn(self, x: float, y: float, z: float, color: rl.RGB, count: int = 10,
              speed: float = 2.6, rng: random.Random | None = None) -> None:
        rng = rng or random
        for _ in range(count):
            ang = rng.uniform(0, math.tau)
            up = rng.uniform(0.6, 1.0) * speed
            self.particles.append([
                x, y, z,
                math.cos(ang) * speed * rng.uniform(0.2, 0.6),
                up,
                math.sin(ang) * speed * rng.uniform(0.2, 0.6),
                rng.uniform(0.35, 0.7),  # ttl
                *color,
            ])

    def update(self, dt: float) -> None:
        alive = []
        for p in self.particles:
            p[0] += p[3] * dt
            p[1] += p[4] * dt
            p[2] += p[5] * dt
            p[4] -= 9.0 * dt
            p[6] -= dt
            if p[6] > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, camera) -> None:
        if not self.particles:
            return
        rl.BeginBlendMode(rl.BLEND_ADDITIVE)
        for p in self.particles:
            a = int(255 * min(1.0, p[6] * 2.5))
            rl.DrawBillboard(camera[0], textures.radial_glow(48), (p[0], p[1], p[2]),
                             0.22, (int(p[7]), int(p[8]), int(p[9]), a))
        rl.EndBlendMode()
