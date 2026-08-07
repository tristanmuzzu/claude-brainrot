"""The raylib access layer.

Everything in the engine imports raylib through this module rather than
directly. It owns the two quirks that must not leak anywhere else:

* **Capture correction.** Screen captures come back differently depending on
  which rasteriser is underneath: the software build used in CI returns them
  vertically flipped with red and blue swapped, a GPU build does not.
  :func:`capture_frame` produces identical, correct pixels on both paths --
  which is the entire basis for trusting CI screenshots as art review.

  The correction is *measured*, not assumed. Assuming it is how ``shoot``
  came to write upside-down PNGs on Windows for every run: the platform test
  that picks the correction and the library that actually renders are
  different questions, and only one of them can be answered by looking at
  ``os.name``. :func:`_capture_fix` draws a marker frame and reads back where
  it landed, so the answer comes from the renderer in the process.

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


def flush() -> None:
    """Draw everything rlgl has queued, right now.

    raylib has two rendering paths and they do not run in call order.
    ``DrawPlane``, ``DrawLine3D`` and friends push vertices into rlgl's render
    *batch*, which is not submitted until something forces it -- typically
    ``EndMode3D``. ``DrawModelEx`` bypasses the batch and issues its draw call
    immediately. So a scene that draws a ground plane and then a hundred models
    actually draws the models first and the plane last, and the plane loses the
    depth test against every model standing above it.

    That is not a subtle difference: it punched shelf-shaped holes in the
    parkour sea, through which you saw the sky. Call this after any batched
    draw whose order matters.
    """
    rlDrawRenderBatchActive()


def make_camera(fovy: float = 55.0):
    """A perspective Camera3D whose storage survives as long as the handle."""
    cam = ffi.new("Camera3D *")
    cam.position = (0.0, 2.0, 6.0)
    cam.target = (0.0, 1.0, 0.0)
    cam.up = (0.0, 1.0, 0.0)
    cam.fovy = fovy
    cam.projection = CAMERA_PERSPECTIVE
    return cam


#: (flip_vertically, swap_red_blue), decided once per process by measurement.
_FIX: "tuple[bool, bool] | None" = None


def _raw_screen() -> "tuple[bytes, int, int] | None":
    """Screen pixels as RGBA bytes, with no correction applied at all."""
    img = LoadImageFromScreen()
    try:
        ImageFormat(ffi.addressof(img), PIXELFORMAT_UNCOMPRESSED_R8G8B8A8)
        w, h = img.width, img.height
        if w <= 0 or h <= 0:
            return None
        return bytes(ffi.buffer(img.data, w * h * 4)), w, h
    finally:
        UnloadImage(img)


def _capture_fix(attempts: int = 6) -> "tuple[bool, bool]":
    """Work out what this renderer's captures need, by drawing a known frame.

    Paints the framebuffer black with a red patch in the top-left corner, then
    reads it straight back. Where the patch turns up says whether rows arrive
    bottom-up, and which byte of it holds the 255 says whether the channels
    are RGBA or BGRA.

    The marker is drawn *repeatedly until the read-back is decisive*, because
    on a double-buffered GPU context ``LoadImageFromScreen`` after
    ``EndDrawing`` returns the frame before last -- so a single marker frame
    reads back as whatever was on screen previously. That is not a hypothetical:
    it read back a blue sky, saw more blue than red, concluded the channels
    were swapped, and every ``shoot`` PNG on this machine came out with the sky
    orange. Decisive means one saturated channel over a dark remainder at one
    corner and black at the other, which no scene frame satisfies by accident.
    """
    global _FIX
    if _FIX is not None:
        return _FIX
    _FIX = (False, False)          # provisional, so a failure cannot recurse
    try:
        for _ in range(attempts):
            BeginDrawing()
            ClearBackground((0, 0, 0, 255))
            DrawRectangle(0, 0, 8, 8, (255, 0, 0, 255))
            EndDrawing()
            probe = _raw_screen()
            if probe is None:
                continue
            raw, w, h = probe
            if w < 8 or h < 8:
                return _FIX
            top = raw[(2 * w + 2) * 4:(2 * w + 2) * 4 + 3]
            bottom = raw[((h - 3) * w + 2) * 4:((h - 3) * w + 2) * 4 + 3]
            for flip, marker, elsewhere in ((False, top, bottom),
                                            (True, bottom, top)):
                if (max(marker) > 200 and sorted(marker)[1] < 60
                        and max(elsewhere) < 60):
                    # The patch was pure red: whichever channel carries it
                    # names the order.
                    _FIX = (flip, marker[2] > marker[0])
                    return _FIX
    except Exception:
        pass
    return _FIX


def calibrate_capture() -> "tuple[bool, bool]":
    """Decide the capture correction now, while the framebuffer is expendable.

    Called once at window creation. Calibrating lazily instead means the first
    capture pays for it *and* the marker frames it draws land in the middle of
    a scene, so the next capture reads a black frame with a red square in it.
    """
    return _capture_fix()


def capture_frame() -> "bytes | None":
    """The current frame as raw RGBA bytes (width*height*4), corrected so the
    same scene yields the same bytes on GPU and software backends.

    Calibration runs on the first call and overwrites the framebuffer, so the
    frame being captured is read out *before* that happens.
    """
    probe = _raw_screen()
    if probe is None:
        return None
    raw, w, h = probe
    flip, swap = _capture_fix()
    if swap:
        swapped = bytearray(raw)
        swapped[0::4], swapped[2::4] = raw[2::4], raw[0::4]
        raw = bytes(swapped)
    if flip:
        stride = w * 4
        raw = b"".join(raw[r * stride:(r + 1) * stride]
                       for r in range(h - 1, -1, -1))
    return raw


def save_frame(path: str) -> None:
    """Write the current frame to a PNG, colour-correct on every backend."""
    from PIL import Image as PILImage

    raw = capture_frame()
    if raw is None:
        return
    w, h = GetScreenWidth(), GetScreenHeight()
    PILImage.frombytes("RGBA", (w, h), raw).save(path)
