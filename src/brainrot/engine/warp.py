"""Textured quad rasterisation.

pygame can fill a polygon with a flat colour and nothing else -- there is no
texture mapping in the library at all. The previous approach approximated it by
scattering small "texel" polygons across each face, which gave surfaces
*detail* but never actual texture: you could not put a legible 16x16
cobblestone pattern on a cube and have it read as cobblestone.

This does the real thing. Each face is treated as a parallelogram, the pixels
inside it are inverse-mapped back into texture space with numpy, and the
texture is sampled nearest-neighbour so pixel art stays hard-edged.

**Why it is fast enough.** Warping per face per frame in numpy would be far too
slow -- the per-call overhead on small arrays dominates. But a face's *shape*
depends only on the camera angle and the distance, not on where the block is,
so at any moment almost every visible face of a given orientation is the same
parallelogram at one of a handful of sizes. Quantising the two edge vectors to
whole pixels turns that into a cache key with a very high hit rate: the warp
runs a few dozen times per frame at most, and everything else is a plain blit.

**Affine, not perspective-correct.** A cube face in perspective is really a
trapezoid, and this approximates it with a parallelogram. Across a block a few
dozen pixels wide the difference is under a pixel. Large near faces (a train
carriage alongside the camera) are subdivided along their length by the caller
so each segment stays small enough for the approximation to hold.
"""

from __future__ import annotations

import math

import numpy as np
import pygame

Point = tuple[float, float]

#: Faces larger than this are drawn but not cached -- a handful of huge entries
#: would evict all the small ones that actually repeat.
_MAX_CACHE_AREA = 130 * 130
_MAX_ENTRIES = 1500
#: How much of the cache to discard when it fills. Clearing it outright dropped
#: the hit rate to about 30%: every eviction threw away the whole working set
#: mid-frame and the next frame had to rebuild it from nothing.
_EVICT_FRACTION = 0.25


def _quantise(value: float) -> int:
    """Snap an edge component to a bucket, coarsely for long edges.

    Every distinct (edge1, edge2) pair is a separate cache entry, so
    whole-pixel buckets on a large face mint an entry for almost every depth
    the camera passes through. Large faces tolerate a coarser bucket -- a
    two-pixel error on a sixty-pixel face is invisible once faces overlap
    slightly -- and it collapses the key space enormously.
    """
    magnitude = abs(value)
    step = 2 if magnitude < 16 else (3 if magnitude < 34 else 5)
    return int(round(value / step)) * step


_cache: dict[tuple, pygame.Surface] = {}
_hits = 0
_misses = 0


def reset_cache() -> None:
    global _hits, _misses
    _cache.clear()
    _hits = _misses = 0


def stats() -> tuple[int, int]:
    """(hits, misses) since the last reset. Used by the benchmark."""
    return _hits, _misses


def _build(texture: np.ndarray, e1: tuple[int, int], e2: tuple[int, int]) -> pygame.Surface | None:
    """Rasterise one parallelogram of ``texture`` into an RGBA surface."""
    e1x, e1y = e1
    e2x, e2y = e2
    det = e1x * e2y - e2x * e1y
    if abs(det) < 1e-6:
        return None  # degenerate: edge-on face, nothing to draw

    corners = ((0, 0), (e1x, e1y), (e1x + e2x, e1y + e2y), (e2x, e2y))
    min_x = min(c[0] for c in corners)
    max_x = max(c[0] for c in corners)
    min_y = min(c[1] for c in corners)
    max_y = max(c[1] for c in corners)

    width = int(max_x - min_x) + 1
    height = int(max_y - min_y) + 1
    if width <= 0 or height <= 0 or width > 2000 or height > 2000:
        return None

    px = (np.arange(width, dtype=np.float32) + min_x)[None, :]
    py = (np.arange(height, dtype=np.float32) + min_y)[:, None]

    # Inverse of the 2x2 edge matrix: screen offset -> (u, v) in the unit square.
    u = (e2y * px - e2x * py) / det
    v = (-e1y * px + e1x * py) / det

    inside = (u >= 0.0) & (u < 1.0) & (v >= 0.0) & (v < 1.0)

    tex_h, tex_w = texture.shape[:2]
    tu = np.clip((u * tex_w).astype(np.int32), 0, tex_w - 1)
    tv = np.clip((v * tex_h).astype(np.int32), 0, tex_h - 1)

    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[..., :3] = texture[tv, tu]
    rgba[..., 3] = inside * np.uint8(255)

    return pygame.image.frombytes(
        np.ascontiguousarray(rgba).tobytes(), (width, height), "RGBA"
    ).convert_alpha()


def draw_quad(
    target: pygame.Surface,
    texture: np.ndarray,
    tex_key: object,
    corners: list[Point],
) -> bool:
    """Draw ``texture`` over a projected quad.

    ``corners`` are in UV order: (0,0), (1,0), (1,1), (0,1). ``tex_key`` must
    identify the texture *and* any shading applied to it, since differently
    shaded copies are different cache entries.

    Returns False when the quad was degenerate or offscreen, so the caller can
    fall back to a flat fill.
    """
    global _hits, _misses

    ox, oy = corners[0]
    e1x, e1y = corners[1][0] - ox, corners[1][1] - oy
    e2x, e2y = corners[3][0] - ox, corners[3][1] - oy

    # Reject degenerate and sub-pixel faces *before* the inflation below, which
    # would otherwise floor every one of them at three pixels and draw distant
    # geometry several times larger than it should be.
    if abs(e1x) + abs(e2x) < 1.0 or abs(e1y) + abs(e2y) < 1.0:
        return False

    # Grow each edge before quantising. Rounding the origin and the edge
    # vectors independently leaves sub-pixel gaps between adjacent faces, and a
    # gap showing sky between every pair of blocks is far more visible than an
    # overlap -- which, under a painter's-order draw, is invisible. The margin
    # covers the quantisation step too, so coarse buckets cannot open a seam.
    len1 = math.hypot(e1x, e1y)
    len2 = math.hypot(e2x, e2y)
    if len1 > 1e-6:
        grow = (len1 + 3.0) / len1
        e1x, e1y = e1x * grow, e1y * grow
    if len2 > 1e-6:
        grow = (len2 + 3.0) / len2
        e2x, e2y = e2x * grow, e2y * grow

    e1 = (_quantise(e1x), _quantise(e1y))
    e2 = (_quantise(e2x), _quantise(e2y))

    span_x = abs(e1[0]) + abs(e2[0])
    span_y = abs(e1[1]) + abs(e2[1])
    if span_x < 2 or span_y < 2:
        return False

    area = span_x * span_y
    key = (tex_key, e1, e2)

    sprite = _cache.get(key)
    if sprite is None:
        _misses += 1
        sprite = _build(texture, e1, e2)
        if sprite is None:
            return False
        if area <= _MAX_CACHE_AREA:
            if len(_cache) >= _MAX_ENTRIES:
                # Drop the oldest quarter. Python dicts keep insertion order, so
                # this is a cheap approximation of LRU that preserves most of
                # the working set instead of discarding all of it.
                for stale in list(_cache)[: int(_MAX_ENTRIES * _EVICT_FRACTION)]:
                    del _cache[stale]
            _cache[key] = sprite
    else:
        _hits += 1

    min_x = min(0, e1[0], e1[0] + e2[0], e2[0])
    min_y = min(0, e1[1], e1[1] + e2[1], e2[1])
    target.blit(sprite, (int(round(ox)) + min_x, int(round(oy)) + min_y))
    return True


def quad_is_visible(corners: list[Point], width: int, height: int, margin: int = 64) -> bool:
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return not (
        max(xs) < -margin or min(xs) > width + margin
        or max(ys) < -margin or min(ys) > height + margin
    )


def facing_camera(corners: list[Point]) -> bool:
    """Winding test: is this quad's front face toward the viewer?

    Cheaper and more reliable than reasoning about which faces of a box should
    be visible from the camera's position, and it works for any orientation.
    """
    (ax, ay), (bx, by), (cx, cy) = corners[0], corners[1], corners[2]
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) > 0
