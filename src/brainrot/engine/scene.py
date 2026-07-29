"""Scene interface and registry.

A scene is a self-contained generated world with a fixed lifetime contract:
built from a seed, updated with a delta time, drawn to a surface. Scenes never
touch windowing, hooks or config -- which is what makes them cheap to write and
possible to test offscreen.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pygame

from ..palette import Palette
from ..rng import Seed


@dataclass(frozen=True)
class SceneContext:
    """Everything a scene needs to generate itself."""

    width: int
    height: int
    palette: Palette
    seed: Seed

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
    def draw(self, surface: pygame.Surface) -> None:
        """Render the current state. Must fully cover the surface."""

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
    return sorted(_REGISTRY)


def build(name: str, ctx: SceneContext) -> Scene:
    """Instantiate a registered scene by name."""
    # Import for side effects; the registry is populated by decorators.
    from .. import scenes  # noqa: F401

    try:
        cls = _REGISTRY[name]
    except KeyError:
        raise KeyError(f"unknown scene {name!r}; available: {available()}") from None
    return cls(ctx)


def choose(names: list[str], seed: Seed) -> str:
    """Pick which scene plays for a run.

    Seeded rather than random so a run number always replays the same scene.
    """
    from .. import scenes  # noqa: F401

    eligible = [n for n in names if n in _REGISTRY] or available()
    if not eligible:
        raise RuntimeError("no scenes registered")
    return eligible[seed.index("scene-choice", len(eligible))]
