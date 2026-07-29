"""Pseudo-3D perspective projection.

A pinhole camera looking down +Z. Every scene shares this, which is why the
runner and the voxel tower feel like the same world despite having nothing else
in common.

The entire illusion of motion comes from one property: world features placed at
*constant* Z spacing project to *shrinking* screen spacing as they recede. Lay
down track ties every 4 units and drive the camera forward and it reads as
speed without a single frame of animation.

Coordinates: X right, Y up, Z forward (away from the viewer).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..palette import RGB, lerp_rgb

#: Nothing closer than this is drawn. Below it, ``focal / dz`` explodes and
#: geometry smears across the screen.
NEAR_PLANE = 0.4


@dataclass
class Camera:
    x: float = 0.0
    y: float = 2.4
    z: float = 0.0
    #: Focal length in pixels. Larger is a narrower, more telephoto view.
    focal: float = 340.0
    #: Vanishing point as a fraction of surface height. Below 0.5 pushes the
    #: horizon up and shows more ground, which suits a downward-looking runner.
    horizon: float = 0.42
    #: Distance at which geometry has fully faded into fog.
    far: float = 90.0
    #: Horizontal sway, in world units. Purely cosmetic camera life.
    roll: float = 0.0


@dataclass(frozen=True)
class Projected:
    x: float
    y: float
    #: Pixels per world unit at this depth. Multiply object sizes by it.
    scale: float
    #: Distance ahead of the camera, for depth sorting and fog.
    depth: float


def project(
    cam: Camera, wx: float, wy: float, wz: float, width: int, height: int
) -> Projected | None:
    """World point to screen. ``None`` when behind the near plane."""
    depth = wz - cam.z
    if depth <= NEAR_PLANE:
        return None
    scale = cam.focal / depth
    sx = width * 0.5 + (wx - cam.x) * scale
    sy = height * cam.horizon + (cam.y - wy) * scale
    if cam.roll:
        # Roll is applied after projection and scaled by depth so near geometry
        # sways more than far -- a cheap approximation of a real camera tilt
        # that costs one multiply instead of a rotation matrix.
        sx += cam.roll * scale * 0.25
    return Projected(sx, sy, scale, depth)


def fog_amount(cam: Camera, depth: float, onset: float = 0.35) -> float:
    """How much fog applies at ``depth``, 0..1.

    Fog starts at ``onset`` of the far plane rather than at the camera, so
    nearby geometry keeps full contrast while the horizon dissolves. Squaring
    the ramp keeps the falloff from looking like a flat grey wash.
    """
    if depth <= 0:
        return 0.0
    start = cam.far * onset
    if depth <= start:
        return 0.0
    t = (depth - start) / max(1e-6, cam.far - start)
    return min(1.0, t) ** 2


def fogged(cam: Camera, color: RGB, depth: float, fog: RGB) -> RGB:
    """Blend a colour toward the fog colour by its depth."""
    return lerp_rgb(color, fog, fog_amount(cam, depth))


def visible(p: Projected | None, width: int, height: int, margin: float = 200.0) -> bool:
    """Cheap on-screen test with slack for objects larger than their origin."""
    if p is None:
        return False
    return -margin <= p.x <= width + margin and -margin <= p.y <= height + margin


def horizon_y(cam: Camera, height: int) -> float:
    return height * cam.horizon


def ease_out(t: float) -> float:
    return 1.0 - (1.0 - max(0.0, min(1.0, t))) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def jump_height(t: float, peak: float, duration: float) -> float:
    """Parabolic arc height at time ``t`` into a jump of ``duration``."""
    if duration <= 0 or t < 0 or t > duration:
        return 0.0
    n = t / duration
    return peak * 4.0 * n * (1.0 - n)


def wrap_angle(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi
