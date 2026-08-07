"""Where you put the strip, remembered.

Automatic placement is a guess from geometry: it knows where the Claude Code
window is and where the desktop ends, and nothing whatever about where that
window keeps its toolbar. Dragging the strip somewhere is the user correcting
that guess, so the correction has to outlive the drag -- and the daemon
restart, and the next turn.

What is stored is an *offset from the host window*, not a screen position, so
a remembered placement still follows that window around, still survives it
being moved to another monitor, and still means the same thing at a different
screen resolution. Absolute coordinates would be right exactly once.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .rng import state_dir

_FILENAME = "placement.json"


@dataclass(frozen=True)
class Manual:
    """A dropped position, relative to the window it was dropped against."""

    #: Gap between the docked edge of the host window and the strip's outer
    #: edge. Negative when the strip was dragged past that edge, which is how
    #: "just outside the window" survives a restart.
    dx: int
    #: Offset from the top of the host window.
    dy: int


def _path(directory: Path | None = None) -> Path:
    return (directory or state_dir()) / _FILENAME


def load(directory: Path | None = None) -> Manual | None:
    """The remembered placement, or None to place automatically."""
    try:
        data = json.loads(_path(directory).read_text(encoding="utf-8"))
        return Manual(int(data["dx"]), int(data["dy"]))
    except (OSError, ValueError, KeyError, TypeError):
        # A corrupt or absent file means "no preference", never a crash: this
        # runs on the render thread of a toy overlay.
        return None


def save(manual: Manual, directory: Path | None = None) -> None:
    path = _path(directory)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"dx": manual.dx, "dy": manual.dy}),
                        encoding="utf-8")
    except OSError:
        pass


def clear(directory: Path | None = None) -> None:
    try:
        _path(directory).unlink()
    except OSError:
        pass
