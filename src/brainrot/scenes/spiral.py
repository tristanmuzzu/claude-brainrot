"""The spiral-platform scene: the tower's renderer against a different plan.

There is deliberately almost nothing here. :class:`brainrot.scenes.tower.
TowerScene` turned out to be a *renderer* -- meshed chunks, the body, the
camera, the orbs, the weather, the sky -- and none of that cares whether the
building it is drawing is a cylinder with rooms in it or a stack of built
platforms on a forest of columns. What differs is the plan, and the plan is a
module: :mod:`brainrot.scenes.spiralplan` against
:mod:`brainrot.scenes.towerplan`.

Two things a renderer cannot work out for itself, and they are the whole file:

* **which way indoors is.** On a ring tower it is which side of the wall you
  are on; here it is whether the platform under your feet happens to have a
  lid.
* **the furniture that is not made of cells.** A platform is a *place*, and
  what makes a farm read as a farm is exactly the parts of the game that are
  not cubes -- crops, flowers, fences, lantern posts, sugar cane, chains. Those
  are models, built by ``assets/src/props_mc.py``, and a meshed building has no
  room in it for a model.
"""

from __future__ import annotations

import math

from .. import assets
from ..engine import rl
from ..engine.scene import SceneContext, register
from . import spiralplan as sp
from .tower import TowerScene

#: How far a piece of furniture is still drawn. Each one is its own draw call,
#: and at anything past this it is a few pixels in the haze.
PROP_FAR = 34.0
#: ...and how far out of the camera's own direction. The strip is portrait,
#: with about fifty degrees of horizontal field, so most of a sphere around the
#: body is behind it.
PROP_AHEAD = -0.25


@register("spiral")
class SpiralScene(TowerScene):
    plan = sp
    #: A spiral of platforms is seventy metres across, against a ring tower's
    #: sixteen, so the same depth of kept world is several times as many chunks
    #: and most of them are behind a platform.
    below = 40

    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        pal = ctx.palette
        self.props = {name: assets.load(name)
                      for name in ("crop", "flower", "mcfence", "lanternpost",
                                   "sugarcane", "chain")}
        # Recoloured once, from the palette, so a run's furniture belongs to
        # the same world as its blocks. Zones a model does not carry are
        # ignored, which is why one dictionary does for all six.
        for model in self.props.values():
            model.recolor({
                "leaf": rl.mix_rgb(pal.accent, (110, 160, 60), 0.62),
                "stem": rl.mix_rgb(pal.accent, (80, 120, 50), 0.72),
                "wood": rl.mix_rgb(pal.structure, (120, 84, 46), 0.55),
                "metal": rl.mix_rgb(pal.structure, (86, 88, 96), 0.6),
                "glow": pal.window_lit,
            })

    def _indoor_want(self) -> float:
        return 1.0 if self.tower.roofed(*self.pos) else 0.0

    def _begin_ground(self) -> None:
        super()._begin_ground()
        # Furniture goes the same way the lamps do: a run that climbs for four
        # minutes has left several hundred pieces of it a long way below, and a
        # list that only grows is a list walked every frame.
        if len(self.tower.props) > 400:
            floor = int(self.pos[1]) - self.below
            self.tower.props = [p for p in self.tower.props
                                if p[0][1] >= floor]

    def _draw_tower(self) -> None:
        super()._draw_tower()
        self._draw_props()

    def _draw_props(self) -> None:
        """Every piece of furniture near enough and ahead of the camera.

        The near/ahead test is the same one the chunk renderer does and for the
        same reason: these are one draw call each, so the cost is set by how
        many are *drawn* rather than by how many exist, and a body on a
        platform has the rest of the spiral behind it.
        """
        cam = self.camera
        eye = (cam.position.x, cam.position.y, cam.position.z)
        fx = cam.target.x - eye[0]
        fy = cam.target.y - eye[1]
        fz = cam.target.z - eye[2]
        n = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / n, fy / n, fz / n
        far2 = PROP_FAR * PROP_FAR
        for (x, y, z), kind, yaw in self.tower.props:
            dx, dy, dz = x - eye[0], y - eye[1], z - eye[2]
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > far2:
                continue
            if dx * fx + dy * fy + dz * fz < PROP_AHEAD * math.sqrt(d2):
                continue
            model = self.props[kind]
            tint = self._fog(self._depth(eye, (x, y, z)))
            # A chain hangs from the cell it is given rather than standing on
            # it, which is the only thing about these that is not "drop it on
            # the floor".
            at = (x, y - 2.0 if kind == "chain" else y, z)
            rl.DrawModelEx(model.model, at, (0, 1, 0), math.degrees(yaw),
                           (1.0, 1.0, 1.0), tint)

    def _lamp_glows(self) -> None:
        super()._lamp_glows()
        # A lantern post carries its own light, and without this it is a lamp
        # that does not glow standing next to cells that do.
        eye = (self.camera.position.x, self.camera.position.y,
               self.camera.position.z)
        colour = self._colour(self.tower.theme_at(self.pos[1]).glow)
        alpha = int(70 + 130 * self.indoor)
        for (x, y, z), kind, _yaw in self.tower.props:
            if kind != "lanternpost":
                continue
            if math.dist(eye, (x, y + 1.5, z)) > PROP_FAR:
                continue
            self._glows.append((x, y + 1.5, z, 2.6 + 1.6 * self.indoor,
                                colour, alpha))
