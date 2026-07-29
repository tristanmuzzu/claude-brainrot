"""Test configuration.

Every test renders offscreen, so SDL is pinned to the dummy driver before
pygame is imported anywhere. This has to happen at collection time -- pygame
reads the variable when the display initialises, not when it is asked to draw.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
