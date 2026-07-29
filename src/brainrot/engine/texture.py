"""Procedurally generated materials.

No image files ship with this project, so every surface detail is synthesised at
scene-construction time. Two different techniques are used, because the geometry
they have to cover is different:

* **Screen-aligned rectangles** (building facades, backdrops) get real generated
  bitmaps, blitted and scaled like ordinary sprites.
* **Arbitrary projected quads** (voxel faces, obstacle sides) cannot be
  texture-mapped by pygame at all, so they get *texel patterns* -- small sets of
  UV-space rectangles that are mapped onto the quad's corners at draw time. It
  is affine rather than perspective-correct, which is invisible at the size a
  single block occupies, and it gives blocks genuine surface detail instead of
  a flat fill.

Everything here runs once per scene. None of it is on the frame path.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pygame

from ..palette import RGB, lerp_rgb, shade
from .noise import fbm, turbulence

#: A texel: (u0, v0, u1, v1, brightness) in unit face space.
Texel = tuple[float, float, float, float, float]


def _to_surface(rgb: np.ndarray) -> pygame.Surface:
    """(W, H, 3) float array -> Surface."""
    return pygame.surfarray.make_surface(np.clip(rgb, 0, 255).astype(np.uint8)).convert()


# ---------------------------------------------------------------------------
# Shaded sphere
# ---------------------------------------------------------------------------


def sphere(
    radius: int,
    color: RGB,
    light: tuple[float, float, float] = (-0.45, -0.6, 0.66),
    rim: RGB = (255, 255, 255),
    glossiness: float = 34.0,
) -> pygame.Surface:
    """A lit sphere sprite with diffuse, specular and rim terms.

    Pre-rendering this once and scaling the sprite is what separates a marble
    from a filled circle. Doing the same shading with pygame draw calls would
    need dozens of nested ellipses per ball per frame; here it is one blit.

    The alpha edge is feathered from the analytic circle coverage, so the sprite
    antialiases correctly at any size without pygame's draw antialiasing.
    """
    size = radius * 2
    coords = (np.arange(size, dtype=np.float32) - radius + 0.5) / radius
    nx = coords[:, None]
    ny = coords[None, :]

    r2 = nx**2 + ny**2
    inside = r2 <= 1.0
    nz = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))

    lx, ly, lz = light
    norm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / norm, ly / norm, lz / norm

    diffuse = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)

    # Blinn-Phong: the half vector between light and a head-on viewer.
    hx, hy, hz = lx, ly, lz + 1.0
    hn = math.sqrt(hx * hx + hy * hy + hz * hz)
    spec = np.clip(nx * (hx / hn) + ny * (hy / hn) + nz * (hz / hn), 0.0, 1.0) ** glossiness

    # Rim light: grazing angles pick up the background, which is what stops a
    # sphere reading as a flat disc against a dark scene.
    rim_term = np.power(1.0 - nz, 3.5) * 0.55

    base = np.array(color, dtype=np.float32)[None, None, :]
    rim_rgb = np.array(rim, dtype=np.float32)[None, None, :]

    shaded = base * (0.26 + 0.82 * diffuse)[:, :, None]
    shaded += 255.0 * spec[:, :, None]
    shaded += rim_rgb * rim_term[:, :, None]

    # Contact darkening on the lower edge grounds the ball a little.
    shaded *= (1.0 - np.clip(ny * 0.22, 0.0, 0.22))[:, :, None]

    coverage = np.clip((1.0 - np.sqrt(r2)) * radius, 0.0, 1.0)
    alpha = np.where(inside, 255.0, 0.0) * coverage

    rgba = np.dstack([np.clip(shaded, 0, 255), alpha[:, :, None]]).astype(np.uint8)
    # surfarray is (x, y); frombytes wants row-major (y, x), hence the swap.
    return pygame.image.frombytes(
        np.ascontiguousarray(rgba.transpose(1, 0, 2)).tobytes(), (size, size), "RGBA"
    ).convert_alpha()


def soft_glow(radius: int, color: RGB, falloff: float = 2.6) -> pygame.Surface:
    """Additive radial glow sprite, for lamps, coins and impact flashes."""
    size = radius * 2
    coords = (np.arange(size, dtype=np.float32) - radius + 0.5) / radius
    dist = np.sqrt(coords[:, None] ** 2 + coords[None, :] ** 2)
    intensity = np.clip(1.0 - dist, 0.0, 1.0) ** falloff

    rgb = np.array(color, dtype=np.float32)[None, None, :] * intensity[:, :, None]
    rgba = np.dstack([rgb, intensity[:, :, None] * 255]).astype(np.uint8)
    return pygame.image.frombytes(
        np.ascontiguousarray(rgba.transpose(1, 0, 2)).tobytes(), (size, size), "RGBA"
    ).convert_alpha()


# ---------------------------------------------------------------------------
# Screen-aligned bitmaps
# ---------------------------------------------------------------------------


def facade(
    width: int,
    height: int,
    wall: RGB,
    window_lit: RGB,
    window_dark: RGB,
    rng: random.Random,
    lit_chance: float = 0.35,
) -> pygame.Surface:
    """A building facade with a window grid.

    Windows are drawn as a real grid rather than noise: regular structure is
    what makes a rectangle read as a *building*, and randomising only which
    windows are lit keeps the skyline varied without losing that structure.
    """
    surface = pygame.Surface((width, height)).convert()

    mottle = fbm(height, width, rng, octaves=4, base=3)
    base = np.array(wall, dtype=np.float32)[None, None, :]
    canvas = base * (0.86 + 0.28 * mottle.T[:, :, None])
    pygame.surfarray.blit_array(surface, np.clip(canvas, 0, 255).astype(np.uint8))

    cell_w = max(3, width // rng.randint(3, 6))
    cell_h = max(3, height // max(3, height // rng.randint(7, 13)))
    pad_x = max(1, cell_w // 4)
    pad_y = max(1, cell_h // 3)

    for gy in range(pad_y, height - cell_h, cell_h):
        for gx in range(pad_x, width - cell_w, cell_w):
            colour = window_lit if rng.random() < lit_chance else window_dark
            pygame.draw.rect(
                surface,
                colour,
                pygame.Rect(gx, gy, max(1, cell_w - pad_x * 2), max(1, cell_h - pad_y)),
            )
    return surface


def marble_slab(width: int, height: int, color: RGB, rng: random.Random) -> pygame.Surface:
    """Veined stone. Turbulence creases are what read as veins."""
    veins = turbulence(height, width, rng, octaves=5, base=4)
    veins = np.power(veins, 0.4)
    base = np.array(color, dtype=np.float32)[None, None, :]
    light = np.array(lerp_rgb(color, (255, 255, 255), 0.55), dtype=np.float32)[None, None, :]
    canvas = base + (light - base) * veins.T[:, :, None]
    return _to_surface(canvas)


# ---------------------------------------------------------------------------
# Texel patterns for projected quads
# ---------------------------------------------------------------------------


def texel_pattern(kind: str, rng: random.Random, count: int = 7) -> list[Texel]:
    """Generate a reusable UV-space detail pattern for a material.

    Applied to voxel faces and obstacle sides via :func:`quad_texel`. Patterns
    are generated once per material per run, then shared by every block using
    that material -- with a per-block offset at draw time so they do not all
    look stamped from the same die.
    """
    texels: list[Texel] = []

    if kind == "stone":
        for _ in range(count):
            u = rng.uniform(0.0, 0.78)
            v = rng.uniform(0.0, 0.78)
            w = rng.uniform(0.10, 0.24)
            h = rng.uniform(0.10, 0.24)
            texels.append((u, v, min(1.0, u + w), min(1.0, v + h), rng.uniform(0.80, 1.16)))

    elif kind == "brick":
        rows = 4
        for row in range(rows):
            offset = 0.5 if row % 2 else 0.0
            for col in range(2):
                u = (col * 0.5 + offset) % 1.0
                v = row / rows
                texels.append((u, v, min(1.0, u + 0.46), v + 1.0 / rows - 0.04, rng.uniform(0.88, 1.10)))

    elif kind == "metal":
        for i in range(4):
            v = i / 4
            texels.append((0.04, v, 0.96, v + 0.03, 0.74))

    elif kind == "wood":
        for i in range(5):
            u = i / 5
            texels.append((u, 0.0, u + 0.04, 1.0, rng.uniform(0.78, 0.94)))

    else:  # generic speckle
        for _ in range(count):
            u = rng.uniform(0.0, 0.85)
            v = rng.uniform(0.0, 0.85)
            s = rng.uniform(0.08, 0.16)
            texels.append((u, v, u + s, v + s, rng.uniform(0.84, 1.14)))

    return texels


def quad_texel(
    surface: pygame.Surface,
    corners: list[tuple[float, float]],
    texel: Texel,
    color: RGB,
    offset: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Draw one texel onto a projected quad.

    ``corners`` is the quad in order (u0v0, u1v0, u1v1, u0v1). The texel's UV
    rectangle is mapped through bilinear interpolation of those corners, so the
    detail follows the face as it rotates and recedes. Affine rather than
    perspective-correct -- across a single block that difference is well under a
    pixel.
    """
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = corners
    u0, v0, u1, v1, _ = texel
    ou, ov = offset
    u0, u1 = (u0 + ou) % 1.0, (u1 + ou) % 1.0
    v0, v1 = (v0 + ov) % 1.0, (v1 + ov) % 1.0
    if u1 <= u0 or v1 <= v0:
        return

    def at(u: float, v: float) -> tuple[float, float]:
        top_x = ax + (bx - ax) * u
        top_y = ay + (by - ay) * u
        bottom_x = dx + (cx - dx) * u
        bottom_y = dy + (cy - dy) * u
        return top_x + (bottom_x - top_x) * v, top_y + (bottom_y - top_y) * v

    points = [at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)]
    # Sub-pixel quads are not worth the draw call and can render as artefacts.
    width = max(abs(points[1][0] - points[0][0]), abs(points[2][0] - points[3][0]))
    height = max(abs(points[3][1] - points[0][1]), abs(points[2][1] - points[1][1]))
    if width < 1.2 or height < 1.2:
        return
    pygame.draw.polygon(surface, color, points)


def apply_texels(
    surface: pygame.Surface,
    corners: list[tuple[float, float]],
    texels: list[Texel],
    base: RGB,
    offset: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Draw a whole pattern onto one face."""
    for texel in texels:
        quad_texel(surface, corners, texel, shade(base, texel[4]), offset)


def edge_shade(
    surface: pygame.Surface,
    corners: list[tuple[float, float]],
    color: RGB,
    width: int = 1,
) -> None:
    """Outline a face.

    Adjacent same-coloured blocks otherwise merge into one silhouette; a single
    darker edge is what makes a wall read as individual blocks.
    """
    if len(corners) < 3:
        return
    span = max(abs(corners[0][0] - corners[2][0]), abs(corners[0][1] - corners[2][1]))
    if span < 3:
        return
    pygame.draw.polygon(surface, color, corners, width)


def ambient_occlusion(
    surface: pygame.Surface,
    corners: list[tuple[float, float]],
    base: RGB,
    bands: int = 2,
) -> None:
    """Darken a face toward its edges -- a stand-in for contact shadow.

    Drawn as inset outlines in progressively darker shades of the face colour
    rather than as alpha over a scratch surface. An SRCALPHA surface per face
    per frame would mean hundreds of full-screen allocations a second; shading
    the base colour reaches the same place with plain polygon draws and no
    allocation at all.
    """
    if len(corners) != 4:
        return
    span = max(abs(corners[0][0] - corners[2][0]), abs(corners[0][1] - corners[2][1]))
    if span < 7:
        return

    cx = sum(p[0] for p in corners) / 4.0
    cy = sum(p[1] for p in corners) / 4.0
    thickness = max(1, int(span * 0.09))

    for i in range(bands):
        t = i / max(1, bands)
        factor = 0.62 + 0.24 * (i / max(1, bands - 1) if bands > 1 else 0.0)
        ring = [
            (cx + (x - cx) * (1.0 - t * 0.30), cy + (y - cy) * (1.0 - t * 0.30))
            for x, y in corners
        ]
        pygame.draw.polygon(surface, shade(base, factor), ring, thickness)
