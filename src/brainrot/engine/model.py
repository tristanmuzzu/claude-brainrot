"""Textured box models and a box-humanoid rig.

Everything in both 3D scenes is boxes, so this is the one place that knows how
to turn a box into pixels: transform eight corners, throw away the faces
pointing away from the camera, and draw the rest as textured quads.

The humanoid follows the standard voxel-game proportions, which are defined in
texture pixels where one block is 16:

    head   8 x  8 x 8      (0.50 x 0.50 x 0.50 blocks)
    torso  8 x 12 x 4      (0.50 x 0.75 x 0.25)
    arm    4 x 12 x 4      (0.25 x 0.75 x 0.25)
    leg    4 x 12 x 4      (0.25 x 0.75 x 0.25)

which makes the figure exactly two blocks tall. Those numbers matter more than
they look: a figure with a slightly-too-small head or slightly-too-long legs
stops reading as the thing it is imitating, however good the textures are.

Limbs rotate about a pivot at the shoulder or hip rather than around their own
centre, which is what makes a swing look like a joint instead of a floating
box sliding back and forth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pygame

from . import warp

#: One texture pixel, in world units. A block is 16 of these.
PX = 1.0 / 16.0

#: Face brightness. Flat per-face shading with a fixed light direction is the
#: idiom's whole lighting model, and at this resolution it beats anything
#: smoother -- the hard edge between faces is what makes a cube read as a cube.
FACE_SHADE = {
    "top": 1.00,
    "north": 0.80,
    "south": 0.80,
    "east": 0.62,
    "west": 0.62,
    "bottom": 0.48,
}

#: Corner indices per face, in UV order: (0,0), (1,0), (1,1), (0,1).
FACES: dict[str, tuple[int, int, int, int]] = {
    "north": (3, 2, 1, 0),
    "south": (6, 7, 4, 5),
    "west": (7, 3, 0, 4),
    "east": (2, 6, 5, 1),
    "top": (7, 6, 2, 3),
    "bottom": (0, 1, 5, 4),
}

#: A projector maps a world point to (screen_x, screen_y, depth), or None if it
#: is behind the camera. Each scene supplies its own.
Projector = Callable[[float, float, float], "tuple[float, float, float] | None"]


@dataclass
class Box:
    """An axis-aligned box, optionally pitched about a pivot."""

    #: Centre of the box, in world units, before rotation.
    x: float
    y: float
    z: float
    #: Full extents.
    w: float
    h: float
    d: float
    #: Texture name per face; missing faces fall back to ``default``.
    textures: dict[str, str] = field(default_factory=dict)
    default: str = "stone"
    #: Rotation about the X axis, in radians, applied around ``pivot``.
    pitch: float = 0.0
    pivot: tuple[float, float, float] | None = None
    #: Extra brightness multiplier, for tinting a whole part.
    tint: float = 1.0

    def corners(self) -> list[tuple[float, float, float]]:
        hw, hh, hd = self.w * 0.5, self.h * 0.5, self.d * 0.5
        local = (
            (-hw, -hh, -hd),
            (hw, -hh, -hd),
            (hw, hh, -hd),
            (-hw, hh, -hd),
            (-hw, -hh, hd),
            (hw, -hh, hd),
            (hw, hh, hd),
            (-hw, hh, hd),
        )
        out: list[tuple[float, float, float]] = []
        if self.pitch and self.pivot is not None:
            px, py, pz = self.pivot
            sin_p, cos_p = math.sin(self.pitch), math.cos(self.pitch)
            for lx, ly, lz in local:
                # Offset from the pivot, rotated in the YZ plane.
                oy = self.y + ly - py
                oz = self.z + lz - pz
                out.append(
                    (
                        self.x + lx,
                        py + oy * cos_p - oz * sin_p,
                        pz + oy * sin_p + oz * cos_p,
                    )
                )
        else:
            for lx, ly, lz in local:
                out.append((self.x + lx, self.y + ly, self.z + lz))
        return out


def draw_box(
    surface: pygame.Surface,
    project: Projector,
    box: Box,
    atlas: dict[str, np.ndarray],
    fog: Callable[[np.ndarray, float], tuple[np.ndarray, object]] | None = None,
    textured: bool = True,
) -> None:
    """Project a box and draw its camera-facing faces.

    Back faces are removed by screen-space winding rather than by reasoning
    about the camera's position, so this works unchanged for a fixed forward
    camera and for an orbiting one.
    """
    projected: list[tuple[float, float, float] | None] = []
    for wx, wy, wz in box.corners():
        projected.append(project(wx, wy, wz))
    if any(p is None for p in projected):
        return

    width, height = surface.get_size()
    visible: list[tuple[float, str, list[tuple[float, float]]]] = []

    for name, indices in FACES.items():
        quad = [(projected[i][0], projected[i][1]) for i in indices]  # type: ignore[index]
        if not warp.facing_camera(quad):
            continue
        if not warp.quad_is_visible(quad, width, height):
            continue
        depth = sum(projected[i][2] for i in indices) / 4.0  # type: ignore[index]
        visible.append((depth, name, quad))

    # Far to near. Culled faces of a convex box never overlap, but a consistent
    # order keeps the seams between them stable.
    visible.sort(key=lambda item: -item[0])

    for depth, name, quad in visible:
        tex_name = box.textures.get(name, box.default)
        base = atlas.get(tex_name)
        if base is None:
            continue
        shade = FACE_SHADE[name] * box.tint
        if fog is not None:
            texture, key = fog(base, depth)
        else:
            texture, key = base, tex_name
        drawn = False
        if textured:
            drawn = warp.draw_quad(
                surface, _shaded(texture, shade, (key, name)), (key, name, round(shade, 2)), quad
            )
        if not drawn:
            # Too small, degenerate, or textures disabled: a flat fill of the
            # texture's mean colour is the right low-detail fallback.
            pygame.draw.polygon(surface, _mean_colour(texture, shade, key), quad)


_shade_cache: dict[object, np.ndarray] = {}
_mean_cache: dict[tuple[int, float], tuple[int, int, int]] = {}


def reset_caches() -> None:
    _shade_cache.clear()
    _mean_cache.clear()


def _shaded(texture: np.ndarray, factor: float, key: object) -> np.ndarray:
    """Pre-shade a texture for one face orientation.

    Applied to the 16x16 source rather than to the drawn face, so it costs a
    few hundred multiplies once instead of touching every rendered pixel.
    """
    cache_key = (key, round(factor, 2))
    cached = _shade_cache.get(cache_key)
    if cached is None:
        cached = np.clip(texture.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        if len(_shade_cache) > 600:
            _shade_cache.clear()
        _shade_cache[cache_key] = cached
    return cached


def _mean_colour(texture: np.ndarray, factor: float, key: object) -> tuple[int, int, int]:
    """Average colour of a texture, for faces too small to warp.

    Keyed on the caller's texture name rather than ``id(texture)``: CPython
    reuses object ids after collection, so an id key can return another
    texture's colour once the original array is freed -- which showed up as two
    identical renders differing by a single byte.
    """
    key = (key, round(factor, 2))
    cached = _mean_cache.get(key)
    if cached is None:
        mean = texture.reshape(-1, 3).mean(axis=0) * factor
        cached = tuple(int(max(0, min(255, c))) for c in mean)  # type: ignore[assignment]
        if len(_mean_cache) > 600:
            _mean_cache.clear()
        _mean_cache[key] = cached  # type: ignore[assignment]
    return cached  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Humanoid
# ---------------------------------------------------------------------------

HEAD = (8 * PX, 8 * PX, 8 * PX)
TORSO = (8 * PX, 12 * PX, 4 * PX)
LIMB = (4 * PX, 12 * PX, 4 * PX)

HIP_Y = 12 * PX  # legs are 12px tall, so the hip sits 12px off the ground
SHOULDER_Y = HIP_Y + 12 * PX  # torso is 12px tall
HEAD_Y = SHOULDER_Y + 4 * PX  # head centre, 8px tall, sitting on the torso


@dataclass
class Humanoid:
    """A rigged box figure.

    ``swing`` is the shared phase for the walk cycle; arms and legs are driven
    in opposition from it. ``lean`` pitches the whole body forward, which is
    what separates a run from a walk.
    """

    #: Texture names for each body part.
    head_tex: str = "head"
    torso_tex: str = "torso"
    arm_tex: str = "arm"
    leg_tex: str = "leg"

    def parts(
        self,
        x: float,
        y: float,
        z: float,
        swing: float,
        lean: float = 0.0,
        amplitude: float = 0.75,
        arms_up: float | None = None,
        tuck: float = 0.0,
        head_scale: float = 1.0,
    ) -> list[Box]:
        """Build the boxes for one pose.

        ``y`` is the ground the figure stands on. ``tuck`` folds the legs for a
        jump; ``arms_up`` overrides the arm swing for a fixed pose.
        """
        leg_swing = math.sin(swing) * amplitude
        arm_swing = math.sin(swing + math.pi) * amplitude * 0.8

        hip = y + HIP_Y
        shoulder = y + SHOULDER_Y
        head_centre = y + HEAD_Y

        boxes: list[Box] = []

        # Legs, pivoting at the hip.
        for side, phase in ((-1, leg_swing), (1, -leg_swing)):
            boxes.append(
                Box(
                    x=x + side * 2 * PX,
                    y=hip - 6 * PX,
                    z=z,
                    w=LIMB[0],
                    h=LIMB[1],
                    d=LIMB[2],
                    default=self.leg_tex,
                    pitch=phase + tuck,
                    pivot=(x + side * 2 * PX, hip, z),
                )
            )

        # Torso.
        boxes.append(
            Box(
                x=x,
                y=hip + 6 * PX,
                z=z,
                w=TORSO[0],
                h=TORSO[1],
                d=TORSO[2],
                default=self.torso_tex,
                pitch=lean,
                pivot=(x, hip, z),
            )
        )

        # Arms, pivoting at the shoulder, just outside the torso.
        for side in (-1, 1):
            phase = arms_up if arms_up is not None else (arm_swing if side < 0 else -arm_swing)
            boxes.append(
                Box(
                    x=x + side * 6 * PX,
                    y=shoulder - 6 * PX,
                    z=z,
                    w=LIMB[0],
                    h=LIMB[1],
                    d=LIMB[2],
                    default=self.arm_tex,
                    pitch=phase + lean,
                    pivot=(x + side * 6 * PX, shoulder, z),
                )
            )

        # Head, with a slight counter-lean so it stays looking forward.
        # head_scale above 1 gives the exaggerated proportions the mobile-runner
        # idiom uses; it grows upward from the neck rather than about its centre
        # so the head never sinks into the shoulders.
        head_w, head_h, head_d = (d * head_scale for d in HEAD)
        boxes.append(
            Box(
                x=x,
                y=head_centre + (head_h - HEAD[1]) * 0.5,
                z=z,
                w=head_w,
                h=head_h,
                d=head_d,
                textures={
                    "north": f"{self.head_tex}_face",
                    "south": f"{self.head_tex}_back",
                    "east": f"{self.head_tex}_side",
                    "west": f"{self.head_tex}_side",
                    "top": f"{self.head_tex}_top",
                    "bottom": f"{self.head_tex}_side",
                },
                default=f"{self.head_tex}_side",
                pitch=lean * 0.35,
                pivot=(x, shoulder, z),
            )
        )
        return boxes
