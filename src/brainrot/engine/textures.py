"""Procedural textures, generated with PIL at scene construction and uploaded
once. A keyed cache keeps the backing buffers alive for the lifetime of the
process -- raylib's software rasteriser reads texture memory at draw time, so
freeing a buffer after upload would be a use-after-free there.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

from . import rl

_CACHE: dict[str, tuple[object, object, object]] = {}  # key -> (texture, image struct, buffer)


def from_pil(key: str, build) -> object:
    """Upload ``build() -> PIL.Image`` under ``key``, once."""
    entry = _CACHE.get(key)
    if entry is not None:
        return entry[0]

    pil = build().convert("RGBA")
    raw = bytearray(pil.tobytes())
    buf = rl.ffi.from_buffer(raw)
    img = rl.ffi.new("Image *")
    img.data = buf
    img.width = pil.width
    img.height = pil.height
    img.mipmaps = 1
    img.format = rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8
    texture = rl.LoadTextureFromImage(img[0])
    rl.SetTextureFilter(texture, rl.TEXTURE_FILTER_BILINEAR)
    _CACHE[key] = (texture, img, raw)
    return texture


def clear() -> None:
    for texture, _img, _raw in _CACHE.values():
        try:
            rl.UnloadTexture(texture)
        except Exception:
            pass
    _CACHE.clear()


# -- stock builders ---------------------------------------------------------

def radial_glow(size: int = 96, hardness: float = 2.2):
    """White radial falloff on transparent black; tint at draw time."""

    def build():
        im = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        d = ImageDraw.Draw(im)
        centre = size / 2
        steps = size // 2
        for i in range(steps, 0, -1):
            a = int(255 * (1.0 - i / steps) ** hardness)
            d.ellipse([centre - i, centre - i, centre + i, centre + i],
                      fill=(255, 255, 255, a))
        return im

    return from_pil(f"glow{size}x{hardness}", build)


def soft_disc(size: int = 64):
    """Solid white disc with a short soft edge -- sun, moon, blob shadow."""

    def build():
        im = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        d = ImageDraw.Draw(im)
        pad = size // 8
        d.ellipse([pad, pad, size - pad, size - pad], fill=(255, 255, 255, 255))
        return im.filter(ImageFilter.GaussianBlur(size // 16))

    return from_pil(f"disc{size}", build)


def cloud_blob(seed: int, size: int = 160):
    """A lumpy cumulus silhouette, unique per seed."""

    def build():
        import random

        rng = random.Random(seed)
        im = Image.new("RGBA", (size, size // 2), (255, 255, 255, 0))
        d = ImageDraw.Draw(im)
        cx, base = size // 2, size // 3
        for _ in range(rng.randint(5, 8)):
            w = rng.randint(size // 5, size // 2)
            h = rng.randint(size // 8, size // 4)
            x = cx + rng.randint(-size // 3, size // 3) - w // 2
            # puffs sit on a common base line: the classic cumulus silhouette,
            # without a hard erase that would leave a visible straight edge
            y = base - h + rng.randint(0, size // 24)
            d.ellipse([x, y, x + w, y + h], fill=(255, 255, 255, 235))
        return im.filter(ImageFilter.GaussianBlur(3))

    return from_pil(f"cloud{seed}", build)


def alpha_band(key: str, color: rl.RGB, top_alpha: int = 200,
               falloff: float = 1.6, height: int = 128):
    """A vertical alpha fade of one colour -- screen-space haze bands."""

    def build():
        im = Image.new("RGBA", (4, height))
        px = im.load()
        for y in range(height):
            a = int(top_alpha * (1.0 - y / (height - 1)) ** falloff)
            for x in range(4):
                px[x, y] = (*color, a)
        return im

    return from_pil(f"band-{key}", build)


def vertical_gradient(key: str, stops: list[tuple[float, rl.RGB]], height: int = 256):
    """A 1-D gradient strip; draw stretched to fill the sky."""

    def build():
        im = Image.new("RGBA", (4, height))
        px = im.load()
        for y in range(height):
            t = y / (height - 1)
            lo = max(s for s in stops if s[0] <= t)
            hi = min((s for s in stops if s[0] >= t), default=lo)
            span = (hi[0] - lo[0]) or 1.0
            f = (t - lo[0]) / span
            c = rl.mix_rgb(lo[1], hi[1], f)
            for x in range(4):
                px[x, y] = (*c, 255)
        return im

    return from_pil(f"grad-{key}", build)
