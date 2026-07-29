"""Per-frame post-processing.

This is the single biggest difference between "shapes on a background" and
something that reads as a rendered image. Three effects, applied in order:

1. **Bloom** -- bright areas bleed light into their surroundings. Neon windows,
   the sun, coins and specular highlights stop looking like flat fills and start
   looking like they emit.
2. **Grade** -- a split-tone plus contrast lift. Warms highlights, cools
   shadows, and stops the palette from looking like raw sRGB primaries.
3. **Chromatic aberration** -- a one-pixel channel offset at the edges. Barely
   visible, and doing the work of a much more expensive lens model.

Everything here is deliberately implemented with pygame's C-side blend
operations rather than numpy. A numpy round trip (``array3d`` -> process ->
``make_surface``) costs ~3ms per frame on this size; the blend-op versions cost
about 0.05ms combined. numpy is reserved for scene construction, where a few
milliseconds once is free.
"""

from __future__ import annotations

import math

import pygame

from ..palette import RGB

_scratch: dict[tuple[str, int, int], pygame.Surface] = {}


def auto_threshold(sky: RGB, floor: int = 142, ceiling: int = 246, margin: int = 30) -> int:
    """Pick a bloom threshold that sits just above the sky's own brightness.

    Real engines bloom in HDR, where the sky sits near 1.0 and a lamp sits at
    10.0, so a fixed threshold separates them cleanly. Rendering in plain 8-bit
    sRGB there is no such headroom: a bright daytime sky is numerically as
    bright as a light source, so a fixed threshold blooms the entire sky and
    smears its colour over the whole frame.

    Deriving the threshold from the sky the run actually generated keeps the
    backdrop out of the bloom while still catching windows, coins and the sun.
    """
    luminance = 0.2126 * sky[0] + 0.7152 * sky[1] + 0.0722 * sky[2]
    return int(max(floor, min(ceiling, luminance + margin)))


def reset_caches() -> None:
    _scratch.clear()
    _edge_masks.clear()


def _scratch_surface(key: str, width: int, height: int, alpha: bool = False) -> pygame.Surface:
    """Reusable working surfaces.

    Post-processing runs every frame; allocating three surfaces per frame would
    hand the garbage collector a steady stream of megabyte objects for no
    reason.
    """
    cache_key = (key, width, height)
    surface = _scratch.get(cache_key)
    if surface is None:
        surface = pygame.Surface((width, height), pygame.SRCALPHA if alpha else 0)
        if len(_scratch) > 16:
            _scratch.clear()
        _scratch[cache_key] = surface
    return surface


def bloom(
    surface: pygame.Surface,
    threshold: int = 168,
    intensity: float = 0.75,
    passes: int = 3,
    downscale: int = 5,
) -> None:
    """Additive bloom, in place.

    The blur is a downscale/upscale ladder rather than a gaussian kernel:
    ``smoothscale`` is bilinear in C, so repeatedly shrinking and growing a
    surface approximates a wide blur for almost nothing. Three passes at 1/5
    resolution gives a soft, wide falloff that a separable gaussian would need
    dozens of taps to match.
    """
    width, height = surface.get_size()
    small_w, small_h = max(2, width // downscale), max(2, height // downscale)

    bright = _scratch_surface("bloom-bright", small_w, small_h)
    pygame.transform.smoothscale(surface, (small_w, small_h), bright)

    # Isolate highlights by subtracting the threshold, then multiplying what
    # survives back up. Anything below the threshold clamps to black and
    # contributes nothing to the additive pass.
    cut = min(255, max(0, threshold))
    bright.fill((cut, cut, cut), special_flags=pygame.BLEND_RGB_SUB)
    gain = 255.0 / max(1, 255 - cut)
    boost = min(255, int(gain * 64))
    bright.fill((boost, boost, boost), special_flags=pygame.BLEND_RGB_MULT)

    ladder_w, ladder_h = max(2, small_w // 2), max(2, small_h // 2)
    tiny = _scratch_surface("bloom-tiny", ladder_w, ladder_h)
    for _ in range(passes):
        pygame.transform.smoothscale(bright, (ladder_w, ladder_h), tiny)
        pygame.transform.smoothscale(tiny, (small_w, small_h), bright)

    glow = _scratch_surface("bloom-glow", width, height)
    pygame.transform.smoothscale(bright, (width, height), glow)

    strength = max(0, min(255, int(intensity * 255)))
    if strength < 255:
        glow.fill((strength, strength, strength), special_flags=pygame.BLEND_RGB_MULT)
    surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


def grade(
    surface: pygame.Surface,
    highlight: RGB = (255, 250, 241),
    shadow: RGB = (214, 222, 255),
    lift: int = 7,
) -> None:
    """Split-tone colour grade, in place.

    Multiplying by a warm tint pulls highlights toward it while leaving darks
    almost untouched (multiplication is proportional), and a small additive
    cool lift then tints the shadows without washing out the brights. Two
    C-side fills, and it is most of what makes a palette look deliberate.
    """
    surface.fill(highlight, special_flags=pygame.BLEND_RGB_MULT)
    if lift > 0:
        cool = (
            int(shadow[0] * lift / 255),
            int(shadow[1] * lift / 255),
            int(shadow[2] * lift / 255),
        )
        surface.fill(cool, special_flags=pygame.BLEND_RGB_ADD)


_edge_masks: dict[tuple[int, int], pygame.Surface] = {}


def _edge_mask(width: int, height: int) -> pygame.Surface:
    """Radial alpha ramp: transparent at the centre, opaque at the corners.

    Built once per size with numpy. The obvious pygame approach -- a stack of
    concentric rectangle outlines -- does not produce a ramp at all, it produces
    *rings*, and multiplying a colour fringe by rings paints banded haloes
    across the whole frame instead of tinting only the edges.
    """
    import numpy as np

    cached = _edge_masks.get((width, height))
    if cached is not None:
        return cached

    xs = (np.arange(width, dtype=np.float32) - width / 2) / (width / 2)
    ys = (np.arange(height, dtype=np.float32) - height / 2) / (height / 2)
    radius = np.sqrt(xs[:, None] ** 2 + ys[None, :] ** 2) / math.sqrt(2.0)
    ramp = np.clip((radius - 0.42) / 0.58, 0.0, 1.0) ** 2.0

    rgba = np.zeros((width, height, 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (ramp * 205).astype(np.uint8)

    surface = pygame.image.frombytes(
        np.ascontiguousarray(rgba.transpose(1, 0, 2)).tobytes(), (width, height), "RGBA"
    ).convert_alpha()

    if len(_edge_masks) > 8:
        _edge_masks.clear()
    _edge_masks[(width, height)] = surface
    return surface


def chromatic_aberration(surface: pygame.Surface, strength: int = 1) -> None:
    """Offset the red and blue channels near the frame edges.

    Masked to the edges by a radial alpha ramp so the centre of the image stays
    sharp -- a uniform offset just reads as a blurry render.

    The image is *reconstructed* from three separated channels rather than
    having a colour fringe added on top of it. Adding red and blue back over an
    untouched frame is not aberration at all: it brightens everything it touches
    and stains it magenta, because red plus blue is magenta.
    """
    if strength <= 0:
        return
    width, height = surface.get_size()

    source = _scratch_surface("ca-src", width, height)
    source.blit(surface, (0, 0))
    mask = _edge_mask(width, height)

    channels = (
        ("ca-red", (255, 0, 0), -strength),
        ("ca-green", (0, 255, 0), 0),
        ("ca-blue", (0, 0, 255), strength),
    )

    composite = _scratch_surface("ca-composite", width, height, alpha=True)
    composite.fill((0, 0, 0, 255))
    for key, filter_rgb, offset in channels:
        layer = _scratch_surface(key, width, height)
        layer.blit(source, (0, 0))
        layer.fill(filter_rgb, special_flags=pygame.BLEND_RGB_MULT)
        composite.blit(layer, (offset, 0), special_flags=pygame.BLEND_RGB_ADD)

    # The mask is opaque white at the edges, so this multiply sets the
    # composite's alpha without touching its colour.
    composite.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(composite, (0, 0))


def vignette(surface: pygame.Surface, strength: float = 0.45) -> None:
    """Radial edge darkening.

    Cached per size and multiplied in, rather than the old two-band gradient --
    a real radial falloff pulls the eye to the centre of a tall strip instead of
    just dimming the top and bottom.
    """
    if strength <= 0:
        return
    width, height = surface.get_size()
    key = ("vignette", width, height)
    cached = _scratch.get(key)
    if cached is None:
        cached = pygame.Surface((width, height)).convert()
        cached.fill((255, 255, 255))
        steps = 42
        for i in range(steps):
            t = i / steps
            value = int(255 * (1.0 - strength * (t**2.2)))
            inset_x = int(width * 0.5 * (1.0 - t) * 0.62)
            inset_y = int(height * 0.5 * (1.0 - t) * 0.62)
            rect = pygame.Rect(
                inset_x - width // 6,
                inset_y - height // 6,
                width - inset_x * 2 + width // 3,
                height - inset_y * 2 + height // 3,
            )
            pygame.draw.rect(cached, (value, value, value), rect, border_radius=int(width * 0.4))
        if len(_scratch) > 16:
            _scratch.clear()
        _scratch[key] = cached
    surface.blit(cached, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


def apply_all(
    surface: pygame.Surface,
    bloom_threshold: int = 168,
    bloom_intensity: float = 0.75,
    highlight: RGB = (255, 250, 241),
    shadow: RGB = (214, 222, 255),
    aberration: int = 1,
    vignette_strength: float = 0.45,
    quality: str = "high",
) -> None:
    """The full chain, in the order the effects assume.

    Lower quality tiers drop the effects with the worst cost-to-benefit ratio
    first: chromatic aberration goes before bloom, because at this size it is
    the least visible of the three, and bloom is doing most of the work.
    """
    passes = {"high": 3, "balanced": 2, "low": 1}.get(quality, 3)
    bloom(surface, threshold=bloom_threshold, intensity=bloom_intensity, passes=passes)
    grade(surface, highlight=highlight, shadow=shadow)
    if quality == "high":
        chromatic_aberration(surface, aberration)
    vignette(surface, vignette_strength)
