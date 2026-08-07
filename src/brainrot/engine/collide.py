"""Axis-aligned boxes, and the placement maths that keeps them honest.

The rule this module exists to enforce: **a hitbox is derived from the same
numbers as the draw call, never typed in by hand.** An obstacle's box comes
from the model's own bounding box pushed through the same position, yaw and
scale that ``DrawModelEx`` is given, so a box can only disagree with the
picture if the scene passes different arguments to the two -- which is exactly
what the scene tests check.

Everything here is plain arithmetic on tuples: no raylib types escape, so the
collision model can be simulated headlessly with no window at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AABB:
    """A world-space axis-aligned box. ``lo`` is the min corner."""

    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float

    # -- construction -----------------------------------------------------

    @staticmethod
    def around(cx: float, cy: float, cz: float,
               half_w: float, height: float, half_d: float) -> "AABB":
        """A box standing on ``cy``: centred horizontally, rising by height."""
        return AABB(cx - half_w, cy, cz - half_d,
                    cx + half_w, cy + height, cz + half_d)

    # -- queries ----------------------------------------------------------

    def overlaps(self, other: "AABB", pad: float = 0.0) -> bool:
        return (self.x0 - pad < other.x1 and self.x1 + pad > other.x0
                and self.y0 - pad < other.y1 and self.y1 + pad > other.y0
                and self.z0 - pad < other.z1 and self.z1 + pad > other.z0)

    def penetration(self, other: "AABB") -> float:
        """Depth of the shallowest axis of overlap; 0.0 when disjoint.

        This is the number the tests assert is zero: it answers "how far did
        the runner get inside that train" rather than merely "did it touch".
        """
        dx = min(self.x1, other.x1) - max(self.x0, other.x0)
        dy = min(self.y1, other.y1) - max(self.y0, other.y0)
        dz = min(self.z1, other.z1) - max(self.z0, other.z0)
        if dx <= 0 or dy <= 0 or dz <= 0:
            return 0.0
        return min(dx, dy, dz)

    def overlaps_xz(self, other: "AABB", pad: float = 0.0) -> bool:
        """Footprint overlap, ignoring height -- the "am I over it" test."""
        return (self.x0 - pad < other.x1 and self.x1 + pad > other.x0
                and self.z0 - pad < other.z1 and self.z1 + pad > other.z0)

    def moved(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "AABB":
        return AABB(self.x0 + dx, self.y0 + dy, self.z0 + dz,
                    self.x1 + dx, self.y1 + dy, self.z1 + dz)

    def grown(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "AABB":
        return AABB(self.x0 - dx, self.y0 - dy, self.z0 - dz,
                    self.x1 + dx, self.y1 + dy, self.z1 + dz)

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) * 0.5


def rotate_y(box: AABB, yaw_deg: float) -> AABB:
    """Rotate a box about the Y axis and re-fit an axis-aligned box to it.

    Uses raylib's convention (``DrawModelEx`` with axis ``(0, 1, 0)``): the
    same right-handed rotation, so a 90-degree yaw sends model +X to world -Z
    exactly as the draw call does. Multiples of 90 degrees are exact; other
    angles produce the conservative fit around the rotated corners.
    """
    rad = math.radians(yaw_deg)
    c, s = math.cos(rad), math.sin(rad)
    if abs(c) < 1e-12:
        c = 0.0
    if abs(s) < 1e-12:
        s = 0.0
    xs, zs = [], []
    for x in (box.x0, box.x1):
        for z in (box.z0, box.z1):
            xs.append(x * c + z * s)
            zs.append(-x * s + z * c)
    return AABB(min(xs), box.y0, min(zs), max(xs), box.y1, max(zs))


def scaled(box: AABB, sx: float, sy: float, sz: float) -> AABB:
    xs = sorted((box.x0 * sx, box.x1 * sx))
    ys = sorted((box.y0 * sy, box.y1 * sy))
    zs = sorted((box.z0 * sz, box.z1 * sz))
    return AABB(xs[0], ys[0], zs[0], xs[1], ys[1], zs[1])


def placed(local: AABB, position: tuple[float, float, float],
           yaw_deg: float = 0.0,
           scale: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> AABB:
    """Model-space box -> world box, in ``DrawModelEx``'s own order.

    raylib composes scale, then rotation, then translation; mirroring that
    order here is what makes the box and the picture the same object.
    """
    box = scaled(local, *scale)
    if yaw_deg:
        box = rotate_y(box, yaw_deg)
    return box.moved(*position)


def model_aabb(model) -> AABB:
    """The bind-pose bounding box of a raylib model.

    Note this is the *bind* pose: ``UpdateModelAnimation`` skins into
    ``animVertices`` and leaves ``vertices`` alone, so animated models need
    :func:`posed_aabb` instead.
    """
    from . import rl

    bb = rl.GetModelBoundingBox(model)
    return AABB(bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z)


def posed_aabb(model) -> AABB:
    """The box around a model's *currently skinned* vertices.

    Walks ``animVertices``, which is where ``UpdateModelAnimation`` puts the
    CPU-skinned result. Only used offline (asset measuring and tests) -- the
    runtime reads the recorded profile instead of re-measuring every frame.
    """
    from . import rl

    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for i in range(model.meshCount):
        mesh = model.meshes[i]
        src = mesh.animVertices if mesh.animVertices else mesh.vertices
        count = mesh.vertexCount * 3
        if count <= 0:
            continue
        buf = rl.ffi.unpack(src, count)
        for j in range(0, count, 3):
            for k in range(3):
                v = buf[j + k]
                if v < lo[k]:
                    lo[k] = v
                if v > hi[k]:
                    hi[k] = v
    if lo[0] == float("inf"):
        return AABB(0, 0, 0, 0, 0, 0)
    return AABB(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])
