"""Runtime access to the committed .glb assets.

Loading a model gives back a :class:`ModelAsset` that knows its animation
clips by name and its material *zones* by name, so scenes recolour parts per
seed without caring about mesh order:

    runner = assets.load("character")
    runner.recolor({"hoodie": palette.accent, "cap": palette.structure})
    runner.play("run", t)

Zone names come from the glTF material names the Blender scripts assigned.
raylib does not expose them, but material order in the file is stable and
raylib maps glTF material ``i`` to slot ``i + 1`` (slot 0 is its default
material), so the GLB's JSON chunk is the source of truth.
"""

from __future__ import annotations

import json
import struct
from importlib import resources
from pathlib import Path

from ..engine import rl
from ..engine.rl import ffi

_CACHE: dict[str, "ModelAsset"] = {}


def data_path(name: str) -> Path:
    """Filesystem path of a committed asset, wheel- and checkout-friendly."""
    root = resources.files(__package__) / "data" / f"{name}.glb"
    return Path(str(root))


def _gltf_material_names(path: Path) -> list[str]:
    """Material names in glTF order, read straight from the GLB JSON chunk."""
    blob = path.read_bytes()
    if blob[:4] != b"glTF":
        return []
    length, = struct.unpack_from("<I", blob, 12)
    header = json.loads(blob[20:20 + length].decode("utf-8"))
    return [m.get("name", f"material{i}") for i, m in enumerate(header.get("materials", []))]


class ModelAsset:
    def __init__(self, name: str) -> None:
        path = data_path(name)
        self.name = name
        self.model = rl.LoadModel(str(path).encode())
        if self.model.meshCount == 0:
            raise RuntimeError(f"asset {name!r} failed to load from {path}")

        count = ffi.new("int *")
        self._anims = rl.LoadModelAnimations(str(path).encode(), count)
        self.clips: dict[str, object] = {}
        for i in range(count[0]):
            anim = self._anims[i]
            self.clips[ffi.string(anim.name).decode()] = anim

        #: zone name -> raylib material slot (glTF order + 1)
        self.zones = {n: i + 1 for i, n in enumerate(_gltf_material_names(path))}
        self._base_colors = {
            n: self._color_of(slot) for n, slot in self.zones.items()
        }

    def _color_of(self, slot: int) -> rl.RGB:
        c = self.model.materials[slot].maps[rl.MATERIAL_MAP_ALBEDO].color
        return (c.r, c.g, c.b)

    # -- palette ----------------------------------------------------------

    def recolor(self, colors: dict[str, rl.RGB]) -> None:
        """Write zone colours. Unknown zones are ignored so palettes can be
        speculative about which assets carry which zones."""
        for zone, color in colors.items():
            slot = self.zones.get(zone)
            if slot is None:
                continue
            self.model.materials[slot].maps[rl.MATERIAL_MAP_ALBEDO].color = (
                color[0], color[1], color[2], 255,
            )

    def reset_colors(self) -> None:
        self.recolor(self._base_colors)

    # -- animation --------------------------------------------------------

    def clip_length(self, clip: str) -> int:
        anim = self.clips.get(clip)
        return anim.keyframeCount if anim else 0

    def pose(self, clip: str, t01: float) -> None:
        """CPU-skin the mesh to clip position ``t01`` in [0, 1)."""
        anim = self.clips.get(clip)
        if anim is None:
            return
        frame = int((t01 % 1.0) * (anim.keyframeCount - 1))
        rl.UpdateModelAnimation(self.model, anim, frame)


def load(name: str) -> ModelAsset:
    """Load (or fetch the cached) asset. Models stay resident until
    :func:`unload_all`; they are shared, so recolour before every draw pass
    rather than assuming your colours survived another scene's use."""
    asset = _CACHE.get(name)
    if asset is None:
        asset = _CACHE[name] = ModelAsset(name)
    return asset


def unload_all() -> None:
    for asset in _CACHE.values():
        try:
            rl.UnloadModel(asset.model)
        except Exception:
            pass
    _CACHE.clear()


def available() -> list[str]:
    return sorted(p.stem for p in (Path(str(resources.files(__package__))) / "data").glob("*.glb"))
