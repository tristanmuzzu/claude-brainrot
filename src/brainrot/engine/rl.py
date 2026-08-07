"""The raylib access layer.

Everything in the engine imports raylib through this module rather than
directly. It owns the two quirks that must not leak anywhere else:

* **Headless capture correction.** The software rasteriser used in CI and by
  ``brainrot shoot`` returns screen captures vertically flipped and with red
  and blue swapped relative to what a GPU presents. :func:`capture_frame`
  produces identical, correct pixels on both paths -- which is the entire
  basis for trusting CI screenshots as art review.

* **cffi structs.** Long-lived pointers (cameras, models) must stay referenced
  or cffi frees them under raylib's feet. Helpers here hand back objects that
  keep their storage alive.
"""

from __future__ import annotations

import os

# Must be decided before InitWindow. The software build renders through SDL,
# which needs the dummy driver when there is no display server.
HEADLESS = bool(os.environ.get("BRAINROT_HEADLESS")) or (
    os.name != "nt"
    and not os.environ.get("DISPLAY")
    and not os.environ.get("WAYLAND_DISPLAY")
)
if HEADLESS:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ["BRAINROT_HEADLESS"] = "1"

from raylib import *  # noqa: F401,F403  (the engine's vocabulary)
from raylib import ffi

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

WHITE4: RGBA = (255, 255, 255, 255)


def rgba(color: RGB, alpha: int = 255) -> RGBA:
    return (color[0], color[1], color[2], alpha)


def scale_rgb(color: RGB, factor: float) -> RGB:
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


def mix_rgb(a: RGB, b: RGB, t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def make_camera(fovy: float = 55.0):
    """A perspective Camera3D whose storage survives as long as the handle."""
    cam = ffi.new("Camera3D *")
    cam.position = (0.0, 2.0, 6.0)
    cam.target = (0.0, 1.0, 0.0)
    cam.up = (0.0, 1.0, 0.0)
    cam.fovy = fovy
    cam.projection = CAMERA_PERSPECTIVE
    return cam


def capture_frame() -> "bytes | None":
    """The current frame as raw RGBA bytes (width*height*4), corrected so the
    same scene yields the same bytes on GPU and software backends."""
    img = LoadImageFromScreen()
    try:
        ImageFlipVertical(ffi.addressof(img))
        ImageFormat(ffi.addressof(img), PIXELFORMAT_UNCOMPRESSED_R8G8B8A8)
        size = img.width * img.height * 4
        raw = bytes(ffi.buffer(img.data, size))
        if HEADLESS:
            # RLSW stores BGRA; swap back to true RGBA.
            swapped = bytearray(raw)
            swapped[0::4], swapped[2::4] = raw[2::4], raw[0::4]
            raw = bytes(swapped)
        return raw
    finally:
        UnloadImage(img)


def save_frame(path: str) -> None:
    """Write the current frame to a PNG, colour-correct on every backend."""
    from PIL import Image as PILImage

    raw = capture_frame()
    if raw is None:
        return
    w, h = GetScreenWidth(), GetScreenHeight()
    PILImage.frombytes("RGBA", (w, h), raw).save(path)
