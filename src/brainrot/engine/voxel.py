"""Voxel blocks: pixel-art atlas textures on a shared unit-cube mesh.

The entire Minecraft look is two cheap tricks, both baked here at texture
build time so the renderer stays a plain textured draw:

* **Directional face shading** -- vanilla's exact constants: top 1.0,
  bottom 0.5, north/south 0.8, east/west 0.6. An unlit cube reads as 3D
  because its faces disagree about brightness, not because of any light.
* **16x16 texel noise** with a darkened 1-px rim, which separates adjacent
  blocks the way baked vertex AO would.

One cube mesh is shared by every style; each style is a Model wrapping that
mesh with its own atlas texture, drawn per block with a distance-fog tint.
"""

from __future__ import annotations

import random

from PIL import Image

from . import rl, textures

#: vanilla face-shade constants, in atlas order
FACES = ("top", "bottom", "north", "south", "east", "west")
SHADE = {"top": 1.00, "bottom": 0.50, "north": 0.80, "south": 0.80,
         "east": 0.60, "west": 0.60}

_MESH_KEEP: list = []
_CUBE_MESH = None
_MODELS: dict[str, object] = {}


def _hash01(x: int, y: int, salt: int) -> float:
    """Deterministic 0..1 noise from a coordinate.

    Patterns index this rather than drawing from the atlas's ``random.Random``,
    so a pattern is a pure function of the texel: adding one cannot shift the
    jitter sequence and silently redraw every other block in the scene.
    """
    n = (x * 374761393 + y * 668265263 + salt * 2654435761) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


#: Texel patterns. A cube of flat colour reads as a cube of flat colour however
#: well it is shaded; what makes a Minecraft frame legible at a glance is that
#: every material has its own *grain* -- courses in brick, boards in wood, a
#: lattice in glowstone -- so the eye separates the structures without needing
#: to resolve their edges.
PATTERNS = ("noise", "planks", "bricks", "checker", "grain", "speck",
            "lantern", "leaves", "cobble")


def _pattern_factor(kind: str, face: str, x: int, y: int, salt: int) -> float:
    """Brightness multiplier for one texel of one face."""
    if kind == "planks":
        if y % 4 == 0:
            return 0.70                      # seam between boards
        return 0.94 + _hash01(0, y // 4, salt) * 0.14
    if kind == "bricks":
        row = y // 4
        if y % 4 == 0:
            return 0.68                      # mortar course
        if (x + (0 if row % 2 == 0 else 8)) % 8 == 0:
            return 0.68                      # staggered vertical joint
        return 0.93 + _hash01(x // 8, row, salt) * 0.12
    if kind == "checker":
        return 1.06 if ((x // 8) + (y // 8)) % 2 == 0 else 0.80
    if kind == "grain":
        if face in ("top", "bottom"):
            return 0.92 + _hash01(x // 2, y // 2, salt) * 0.16
        return 0.88 + _hash01(x, 0, salt) * 0.24
    if kind == "speck":
        h = _hash01(x, y, salt)
        if h > 0.94:
            return 1.35                      # ore fleck
        if h < 0.10:
            return 0.74
        return 0.96 + h * 0.08
    if kind == "lantern":
        if min(x, y, 15 - x, 15 - y) <= 1:
            return 0.72                      # dark frame
        if 3 <= x <= 12 and 3 <= y <= 12 and (x + y) % 3:
            return 1.45                      # blown-out core: reads as emissive
        return 1.05
    if kind == "leaves":
        return 0.66 + _hash01(x, y, salt) * 0.62
    if kind == "cobble":
        cell = _hash01(x // 4, y // 4, salt)
        if (x % 4 == 0 or y % 4 == 0) and cell > 0.35:
            return 0.66                      # gap between stones
        return 0.84 + cell * 0.30
    return 1.0


def _atlas(base: rl.RGB, noise: float, seed: int,
           top: rl.RGB | None = None, side_band: rl.RGB | None = None,
           pattern: str = "noise") -> Image.Image:
    """A 96x16 strip of six 16x16 face tiles, shaded, patterned and noised."""
    rng = random.Random(seed)
    im = Image.new("RGBA", (96, 16))
    px = im.load()
    for fi, face in enumerate(FACES):
        colour = base
        if top is not None and face == "top":
            colour = top
        shade = SHADE[face]
        for y in range(16):
            for x in range(16):
                c = colour
                # side blocks with a distinct top get a 3px cap band (grass)
                if side_band is not None and face not in ("top", "bottom") and y < 3:
                    c = side_band
                jitter = 1.0 + rng.uniform(-noise, noise)
                rim = 0.90 if (x in (0, 15) or y in (0, 15)) else 1.0
                f = shade * jitter * rim * _pattern_factor(pattern, face, x, y, seed)
                px[fi * 16 + x, y] = (
                    max(0, min(255, int(c[0] * f))),
                    max(0, min(255, int(c[1] * f))),
                    max(0, min(255, int(c[2] * f))),
                    255,
                )
    return im


def _cube_mesh():
    """A unit cube whose UVs map each face to its atlas tile."""
    global _CUBE_MESH
    if _CUBE_MESH is not None:
        return _CUBE_MESH

    # face -> (normal, four corners CCW seen from outside)
    h = 0.5
    faces = {
        "top": ((0, 1, 0), [(-h, h, h), (h, h, h), (h, h, -h), (-h, h, -h)]),
        "bottom": ((0, -1, 0), [(-h, -h, -h), (h, -h, -h), (h, -h, h), (-h, -h, h)]),
        "north": ((0, 0, -1), [(h, -h, -h), (-h, -h, -h), (-h, h, -h), (h, h, -h)]),
        "south": ((0, 0, 1), [(-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)]),
        "east": ((1, 0, 0), [(h, -h, h), (h, -h, -h), (h, h, -h), (h, h, h)]),
        "west": ((-1, 0, 0), [(-h, -h, -h), (-h, -h, h), (-h, h, h), (-h, h, -h)]),
    }
    verts: list[float] = []
    norms: list[float] = []
    uvs: list[float] = []
    tris: list[int] = []
    for fi, face in enumerate(FACES):
        normal, corners = faces[face]
        u0, u1 = fi / 6, (fi + 1) / 6
        base = len(verts) // 3
        for ci, (x, y, z) in enumerate(corners):
            verts += [x, y, z]
            norms += list(normal)
            u = u0 if ci in (0, 3) else u1
            v = 1.0 if ci in (0, 1) else 0.0
            uvs += [u, v]
        tris += [base, base + 1, base + 2, base, base + 2, base + 3]

    mesh = rl.ffi.new("Mesh *")
    mesh.vertexCount = len(verts) // 3
    mesh.triangleCount = len(tris) // 3
    vb = rl.ffi.new("float[]", verts)
    nb = rl.ffi.new("float[]", norms)
    tb = rl.ffi.new("float[]", uvs)
    ib = rl.ffi.new("unsigned short[]", tris)
    mesh.vertices = vb
    mesh.normals = nb
    mesh.texcoords = tb
    mesh.indices = ib
    _MESH_KEEP.extend([mesh, vb, nb, tb, ib])
    rl.UploadMesh(mesh, False)
    _CUBE_MESH = mesh
    return mesh


def block_model(key: str, base: rl.RGB, noise: float = 0.05, seed: int = 0,
                top: rl.RGB | None = None, side_band: rl.RGB | None = None,
                pattern: str = "noise"):
    """The cached Model for one block style."""
    model = _MODELS.get(key)
    if model is not None:
        return model
    mesh = _cube_mesh()
    model = rl.LoadModelFromMesh(mesh[0])
    tex = textures.from_pil(
        f"block-{key}",
        lambda: _atlas(base, noise, seed, top, side_band, pattern))
    rl.SetTextureFilter(tex, rl.TEXTURE_FILTER_POINT)  # crisp texels
    model.materials[0].maps[rl.MATERIAL_MAP_ALBEDO].texture = tex
    _MODELS[key] = model
    return model


def draw_block(model, x: float, y: float, z: float, tint, scale: float = 1.0) -> None:
    rl.DrawModelEx(model, (x, y, z), (0, 1, 0), 0.0, (scale, scale, scale), tint)


def draw_box(model, x: float, y: float, z: float, tint,
             sx: float = 1.0, sy: float = 1.0, sz: float = 1.0,
             yaw: float = 0.0) -> None:
    """A block scaled per axis: slabs, panes, posts, beams, trunks.

    One mesh and one texture cover every shape a course is built from, which is
    what keeps a hundred assorted blocks on screen cheaper than a handful of
    distinct meshes would be. The texture stretches with the box, exactly as a
    slab's texture does in the game.
    """
    rl.DrawModelEx(model, (x, y, z), (0, 1, 0), yaw, (sx, sy, sz), tint)


def clear() -> None:
    """Forget models (textures are owned by the textures cache). The shared
    mesh is deliberately kept -- scenes reload styles cheaply."""
    _MODELS.clear()
