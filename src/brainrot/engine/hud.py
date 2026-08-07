"""HUD text in the chunky default raylib font, with a drop shadow so it reads
on any sky. The slightly pixelated look at integer scales is a feature -- it
matches the mobile-game register the scenes imitate."""

from __future__ import annotations

from . import rl


def text(s: str, x: int, y: int, size: int = 20,
         color: rl.RGB = (255, 255, 255), anchor: str = "topleft",
         alpha: int = 255, shadow: bool = True) -> None:
    data = s.encode()
    w = rl.MeasureText(data, size)
    if anchor.endswith("center"):
        x -= w // 2
    elif anchor.endswith("right"):
        x -= w
    if anchor.startswith("bottom"):
        y -= size
    if shadow:
        rl.DrawText(data, x + 2, y + 2, size, (0, 0, 0, int(alpha * 0.55)))
    rl.DrawText(data, x, y, size, rl.rgba(color, alpha))


def chip(s: str, x: int, y: int, size: int = 14,
         fg: rl.RGB = (255, 255, 255), bg: rl.RGBA = (0, 0, 0, 110)) -> None:
    """Small rounded label on a translucent pill -- captions, scene tags."""
    data = s.encode()
    w = rl.MeasureText(data, size)
    pad = 7
    rl.DrawRectangleRounded((x - pad, y - pad // 2, w + pad * 2, size + pad), 0.5, 6, bg)
    rl.DrawText(data, x, y, size, rl.rgba(fg, 235))
