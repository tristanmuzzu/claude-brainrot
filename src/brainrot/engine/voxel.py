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
from functools import lru_cache

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
#:
#: The frequencies matter as much as the shapes. The first version of these
#: drew four enormous bricks and an eight-texel checkerboard, which at the size
#: a block actually occupies on the strip read as a *stamp* on a plastic cube
#: rather than as a material. Vanilla's textures are busy at the texel and calm
#: at the block, and everything here is now cut to that rule: detail lives in
#: the top of the range (small amplitude, high frequency), and the only strong
#: darks are structural -- mortar, seams, the gaps between stones.
PATTERNS = ("noise", "planks", "bricks", "stonebrick", "checker", "grain",
            "speck", "lantern", "leaves", "cobble", "wool", "concrete",
            "sand", "dirt")


@lru_cache(maxsize=256)
def _cobble_face(salt: int) -> tuple[tuple[int, float], ...]:
    """The whole 16x16 Voronoi for one salt, computed once.

    Cobble is by a long way the most expensive pattern here -- sixteen
    candidate cells per texel -- and it does not depend on which *face* is
    being drawn, so the naive call site evaluated the same 256 answers six
    times per material. Measured: 34 ms for one cobble strip, against about
    one for every other pattern, and a scene that bakes half a dozen stone
    materials paid it every time.
    """
    # The jitter of a cell centre depends only on which of the four wrapped
    # cells it is, so the sixteen candidate centres are eight hash calls for
    # the whole face rather than thirty-two per texel.
    centres = []
    for cy in range(-1, 3):
        for cx in range(-1, 3):
            gx, gy = cx % 2, cy % 2
            centres.append((
                (cx + 0.5 + (_hash01(gx, gy, salt) - 0.5) * 1.1) * 8.0,
                (cy + 0.5 + (_hash01(gx, gy, salt + 7) - 0.5) * 1.1) * 8.0,
                gy * 2 + gx))
    out = []
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            best, second, which = 9e9, 9e9, 0
            for jx, jy, cell in centres:
                d = (px - jx) ** 2 + (py - jy) ** 2
                if d < best:
                    best, second, which = d, best, cell
                elif d < second:
                    second = d
            out.append((which, second ** 0.5 - best ** 0.5))
    return tuple(out)


def _cobble_cell(x: int, y: int, salt: int) -> tuple[int, float]:
    """Which stone of a cobble face a texel belongs to, and how far inside it.

    A Voronoi over jittered cell centres, wrapped so the face tiles with
    itself. Cobblestone is the one vanilla texture whose whole character is
    that its cells are *irregular* -- laid out on a 4x4 grid it stops being
    cobble and becomes tile, which is what the previous version drew.
    """
    best, second, which = 9e9, 9e9, 0
    for cy in range(-1, 3):
        for cx in range(-1, 3):
            gx, gy = cx % 2, cy % 2          # 2x2 cells of 8 texels, wrapped
            jx = (cx + 0.5 + (_hash01(gx, gy, salt) - 0.5) * 1.1) * 8.0
            jy = (cy + 0.5 + (_hash01(gx, gy, salt + 7) - 0.5) * 1.1) * 8.0
            d = (x + 0.5 - jx) ** 2 + (y + 0.5 - jy) ** 2
            if d < best:
                best, second, which = d, best, gy * 2 + gx
            elif d < second:
                second = d
    return which, second ** 0.5 - best ** 0.5


def _pattern_factor(kind: str, face: str, x: int, y: int, salt: int) -> float:
    """Brightness multiplier for one texel of one face."""
    if kind == "planks":
        # Four boards, a dark seam between them, end joints staggered from
        # board to board, and grain running *along* the board rather than a
        # flat fill -- the flat fill is what made these read as painted stripes.
        board = y // 4
        if y % 4 == 0:
            return 0.74
        if (x + board * 5) % 16 == 0:
            return 0.80                      # end joint
        base = 0.93 + _hash01(0, board, salt) * 0.09
        streak = (_hash01(x, board * 4 + (y % 4), salt) - 0.5) * 0.10
        knot = 0.90 if _hash01(x // 2, board, salt + 3) > 0.965 else 1.0
        return base + streak + (knot - 1.0)
    if kind == "bricks":
        row = y // 4
        if y % 4 == 0:
            return 0.72                      # mortar course
        if (x + (0 if row % 2 == 0 else 4)) % 8 == 0:
            return 0.72                      # staggered vertical joint
        brick = (x + (0 if row % 2 == 0 else 4)) // 8
        return (0.92 + _hash01(brick, row, salt) * 0.12
                + (_hash01(x, y, salt + 11) - 0.5) * 0.05)
    if kind == "stonebrick":
        # Two courses of two, offset -- vanilla's stone brick, which is what
        # makes a tower read as masonry instead of as a grey column.
        row = y // 8
        if y % 8 == 0:
            return 0.76
        if (x + (0 if row % 2 == 0 else 4)) % 8 == 0:
            return 0.76
        return (0.93 + _hash01((x + row * 4) // 8, row, salt) * 0.10
                + (_hash01(x, y, salt + 5) - 0.5) * 0.06)
    if kind == "checker":
        # Kept for compatibility, but at a fraction of its old contrast: the
        # 8-texel two-tone chequer was legible from across the room and made
        # every platform look like a bathroom floor.
        base = 1.02 if ((x // 4) + (y // 4)) % 2 == 0 else 0.94
        return base + (_hash01(x, y, salt) - 0.5) * 0.06
    if kind == "grain":
        # Quartz: near-white with the faintest vertical striation.
        return (0.96 + _hash01(x, 0, salt) * 0.06
                + (_hash01(x, y, salt + 2) - 0.5) * 0.04)
    if kind == "speck":
        # Ore: a handful of flecks in clusters, not salt-and-pepper. Random
        # per-texel flecks average out to grey the moment a block is small.
        h = _hash01(x // 3, y // 3, salt)
        if h > 0.86 and _hash01(x, y, salt + 1) > 0.35:
            return 1.28
        return 0.95 + _hash01(x, y, salt + 9) * 0.10
    if kind == "lantern":
        edge = min(x, y, 15 - x, 15 - y)
        if edge == 0:
            return 0.66                      # iron frame
        if edge == 1:
            return 0.80
        if 3 <= x <= 12 and 3 <= y <= 12:
            # a lattice over a blown-out core: reads as emissive without any
            # lighting, and the lattice is what stops it reading as a flat chip
            return 1.10 if (x % 4 == 0 or y % 4 == 0) else 1.48
        return 1.02
    if kind == "leaves":
        # Dense, with holes you can see sky through in vanilla. Here the holes
        # are just very dark, which reads the same at this size.
        h = _hash01(x, y, salt)
        if h < 0.12:
            return 0.58
        return 0.82 + h * 0.34
    if kind == "cobble":
        which, edge = _cobble_face(salt)[y * 16 + x]
        if edge < 0.85:
            return 0.70                      # gap between stones
        return (0.86 + _hash01(which, which * 3, salt) * 0.22
                + (_hash01(x, y, salt + 13) - 0.5) * 0.07)
    if kind == "wool":
        # Fabric: a fine weave, deliberately low contrast. This is what the
        # course's own colours wear, and vanilla wool is calm at the block.
        weave = 1.0 - 0.035 * ((x + y) % 3 == 0) + 0.03 * ((x - y) % 4 == 0)
        return weave + (_hash01(x, y, salt) - 0.5) * 0.07
    if kind == "concrete":
        return 0.985 + _hash01(x, y, salt) * 0.03
    if kind == "sand":
        return 0.94 + _hash01(x, y, salt) * 0.11
    if kind == "dirt":
        h = _hash01(x // 2, y // 2, salt)
        return 0.86 + h * 0.22 + (_hash01(x, y, salt + 4) - 0.5) * 0.08
    return 0.96 + _hash01(x, y, salt) * 0.08


@lru_cache(maxsize=1)
def _ao_table() -> tuple[float, ...]:
    """:func:`_ao` for all 256 texels, computed once for the process.

    It has no salt in it, so every material and every face has always been
    asking for the same 256 answers."""
    return tuple(_ao(x, y) for y in range(16) for x in range(16))


def _ao(x: int, y: int) -> float:
    """Baked corner shading for one texel of a face.

    Vanilla's smooth lighting darkens a face toward the edges and harder still
    into the corners, where two neighbours occlude at once. That gradient is
    most of why a solid wall of identical cubes still reads as *cubes* rather
    than as one large surface -- and it is why a course drawn without it looks
    like coloured card. There is no neighbour information at texture-build
    time, so it is baked as if every block had them: the error on a lone
    floating block is a slightly rounded look, which is the harmless direction.

    Turned up from 5% to 9% when the tower arrived, and that is about scale
    rather than taste. A course is a dozen separate cubes with sky between them
    and the eye separates those without help; a *wall* is forty cubes meeting
    edge to edge, and at the old amplitude a ring of gold or quartz -- materials
    whose texel pattern is deliberately almost flat -- read as one extruded
    plastic surface with no blocks in it at all.
    """
    u = min(x, 15 - x) / 7.5               # 0 at the rim, 1 down the middle
    v = min(y, 15 - y) / 7.5
    edge = max(0.0, 1.0 - min(u, v) * 2.6)
    corner = max(0.0, 1.0 - u * 1.9) * max(0.0, 1.0 - v * 1.9)
    return 1.0 - 0.09 * edge ** 1.6 - 0.075 * corner


def _atlas(base: rl.RGB, noise: float, seed: int,
           top: rl.RGB | None = None, side_band: rl.RGB | None = None,
           pattern: str = "noise") -> Image.Image:
    """A 96x16 strip of six 16x16 face tiles, shaded, patterned and noised."""
    rng = random.Random(seed)
    # Built as a flat RGBA buffer rather than through ``Image.load()``.
    # Identical pixels -- the loop order, and therefore the jitter sequence, is
    # unchanged -- but ``px[x, y] = tuple`` costs about two microseconds a
    # texel, and the tower scene bakes fifty-odd materials at once: measured,
    # that one call was 280 ms of a 315 ms scene construction, which the
    # overlay pays as a delay before its first frame.
    buf = bytearray(96 * 16 * 4)
    ao = _ao_table()
    for fi, face in enumerate(FACES):
        colour = base
        if top is not None and face == "top":
            colour = top
        shade = SHADE[face]
        for y in range(16):
            for x in range(16):
                c = colour
                # Side blocks with a distinct top get a cap band (grass), and
                # the band's lower edge is ragged rather than a ruled line --
                # vanilla's grass overlay dribbles down the side, and a
                # perfectly straight join is the single most obvious tell that
                # a texture was drawn by an equation.
                if side_band is not None and face not in ("top", "bottom"):
                    if y < 2 + int(_hash01(x, 0, seed + 21) * 3.0):
                        c = side_band
                jitter = 1.0 + rng.uniform(-noise, noise)
                f = (shade * jitter * ao[y * 16 + x]
                     * _pattern_factor(pattern, face, x, y, seed))
                i = (y * 96 + fi * 16 + x) * 4
                buf[i] = max(0, min(255, int(c[0] * f)))
                buf[i + 1] = max(0, min(255, int(c[1] * f)))
                buf[i + 2] = max(0, min(255, int(c[2] * f)))
                buf[i + 3] = 255
    return Image.frombytes("RGBA", (96, 16), bytes(buf))


def face_strip(base: rl.RGB, noise: float = 0.05, seed: int = 0,
               top: rl.RGB | None = None, side_band: rl.RGB | None = None,
               pattern: str = "noise") -> Image.Image:
    """One style's six face tiles, for callers assembling their own atlas.

    :mod:`brainrot.engine.chunk` stacks a whole catalogue of these into a
    single texture so that a meshed chunk of architecture is one draw call
    whatever it is made of. Same pixels as a block model's own atlas -- there
    is exactly one place a material's look is decided.
    """
    return _atlas(base, noise, seed, top, side_band, pattern)


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
