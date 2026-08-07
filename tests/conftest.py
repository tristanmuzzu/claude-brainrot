"""Test configuration.

Every test renders offscreen through the software rasteriser, so the headless
flag and SDL's dummy driver are pinned before raylib is imported anywhere --
raylib reads them at window creation, and there is exactly one window per
process, shared by every test that draws.
"""

from __future__ import annotations

import os

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

W, H = 360, 640

_window = None


def ensure_window(width: int = W, height: int = H):
    """Open (or resize) the single shared offscreen window.

    raylib supports one window per process, so tests share it and it is never
    closed -- the OS reclaims it at process exit.
    """
    global _window
    from brainrot.config import Config
    from brainrot.engine import rl
    from brainrot.engine.window import HeadlessWindow

    if _window is None:
        cfg = Config()
        cfg.width, cfg.height = width, height
        _window = HeadlessWindow()
        _window.create(cfg)
    elif (rl.GetScreenWidth(), rl.GetScreenHeight()) != (width, height):
        rl.SetWindowSize(width, height)
        _window.width, _window.height = width, height
    return _window
