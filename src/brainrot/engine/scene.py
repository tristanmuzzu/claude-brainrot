"""Scene interface and registry.

A scene is a self-contained generated world with a fixed lifetime contract:
built from a seed, updated with a delta time, drawn through raylib. Scenes
never touch windowing, hooks or config -- which is what makes them cheap to
write and possible to render headlessly.

The draw contract: ``draw()`` is called between ``BeginDrawing`` and
``EndDrawing`` and must fully cover the frame (sky first, then world). The
loop adds nothing but the caption.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..palette import Palette
from ..rng import Seed


@dataclass(frozen=True)
class SceneContext:
    """Everything a scene needs to generate itself."""

    width: int
    height: int
    palette: Palette
    seed: Seed
    #: "high", "balanced" or "low". Scenes scale their detail against this.
    quality: str = "high"

    def stream(self, label: str):
        return self.seed.stream(label)


class Scene(ABC):
    #: Registry key, set by :func:`register`.
    name: str = "scene"

    def __init__(self, ctx: SceneContext) -> None:
        self.ctx = ctx
        self.width = ctx.width
        self.height = ctx.height
        self.palette = ctx.palette
        self.elapsed = 0.0

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance simulation by ``dt`` seconds."""

    @abstractmethod
    def draw(self) -> None:
        """Render the current state. Must fully cover the frame."""

    #: Whether this scene can be driven by hand. Scenes that opt in implement
    #: :meth:`control`; the rest keep driving themselves and the loop simply
    #: never offers them the keyboard.
    playable: bool = False

    def control(self, intent) -> None:
        """Take a player's :class:`~brainrot.engine.input.Intent` for one frame.

        Called *before* ``update``, and only while someone is actually driving.
        A scene is expected to keep every guarantee it makes on autopilot --
        except the ones that were about its own choices. The runner will not
        clip through a train because it plans not to, but a person steering it
        into one gets to hit it.
        """

    def teardown(self) -> None:
        """Release anything expensive. Optional."""


_REGISTRY: dict[str, type[Scene]] = {}


def register(name: str):
    """Class decorator adding a scene to the registry."""

    def wrap(cls: type[Scene]) -> type[Scene]:
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return wrap


def available() -> list[str]:
    """Every registered scene name. Importing the scenes package populates the
    registry as a side effect, so do that before reporting."""
    from .. import scenes  # noqa: F401

    return sorted(_REGISTRY)


def build(name: str, ctx: SceneContext) -> Scene:
    from .. import scenes  # noqa: F401

    try:
        cls = _REGISTRY[name]
    except KeyError:
        raise KeyError(f"unknown scene {name!r}; available: {available()}") from None

    # Exactly one scene is ever alive. Building the next one evicts the
    # previous scene's textures and block models -- without this a long-lived
    # daemon leaks a scene's textures per run, and the software rasteriser
    # exhausts its texture slots within a handful of runs.
    from . import textures, voxel

    voxel.clear()
    textures.end_scene()
    return cls(ctx)


def choose(names: list[str], seed: Seed) -> str:
    """Seeded rather than random so a run number always replays its scene."""
    from .. import scenes  # noqa: F401

    eligible = [n for n in names if n in _REGISTRY] or available()
    if not eligible:
        raise RuntimeError("no scenes registered")
    return eligible[seed.index("scene-choice", len(eligible))]
