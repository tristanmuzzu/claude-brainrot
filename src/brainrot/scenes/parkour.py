"""First-person Minecraft-style infinite parkour. (Being rebuilt -- stub.)"""

from __future__ import annotations

from ..engine.scene import Scene, SceneContext, register
from ..engine.sky import SkyDome


@register("parkour")
class ParkourScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        self.sky = SkyDome(ctx.palette, ctx.seed, ctx.width, ctx.height)

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        self.sky.draw(self.elapsed)
