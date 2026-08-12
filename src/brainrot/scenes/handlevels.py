"""Backwards-compatible re-export of the level roster.

The design used to live here as one 1,000-line table. It is now one module
per level under :mod:`brainrot.scenes.levels`, so that levels can be worked
on independently; this module stays so that nothing importing
``handlevels`` has to change.
"""

from __future__ import annotations

from .levels import LEVELS, ROLES, Level, n

__all__ = ["LEVELS", "ROLES", "Level", "n"]
