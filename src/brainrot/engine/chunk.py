"""Meshed voxel chunks: a whole wall of blocks for one draw call.

:mod:`brainrot.engine.voxel` draws one cube per call, which is the right answer
for a course of a dozen platforms that pop in, fade and move. It is the wrong
answer for *architecture*. A tower with a shell, floors, arches and buttresses
is thousands of cells, and at seven microseconds of Python per ``DrawModelEx``
that is the whole frame budget spent on scenery nobody lands on.

So the static half of a world is built the way the game itself builds it:

* **One texture for every material.** Each style's six face tiles
  (:func:`voxel.face_strip`) are stacked into a single image, so a mesh may mix
  brick, glass and gold and still be one draw call. Without this a chunk costs
  one call per material in it, and the interesting chunks are exactly the ones
  with six materials.
* **Only the faces you can see.** A face is emitted only where its neighbour
  cell is empty (or see-through). A solid cylinder of radius nine is 250 cells
  a layer and about 40 faces; the interior is never built, so hollowing a tower
  out costs nothing and filling it in costs nothing either.
* **Cut into cubic chunks**, and this is about *fog* rather than about culling.
  Distance fog here is a per-draw tint, so everything in one mesh recedes by
  the same amount. A whole tower in one mesh would fog its near wall and its
  far wall identically; at eight metres a chunk the error inside one is under a
  tenth of the fog range, which is below what the eye picks out of a gradient.

Building the mesh is the expensive half -- measured at about 7 us a face, so a
250-face chunk is under two milliseconds -- and it happens off the frame that
needs it: :meth:`ChunkedVolume.build_pending` takes a budget and the scene
gives it one chunk a frame, generating far enough ahead that the mesh is ready
before it is looked at. Drawing is nearly free: measured at 0.78 ms for twenty
chunks of 3,600 faces each, which is forty times more geometry than a tower
ever has on screen.

Two raylib details this module owns, because they are the kind that corrupt
memory rather than look wrong:

* **A mesh raylib will free must be allocated by raylib.** ``UnloadMesh`` calls
  ``RL_FREE`` on ``mesh.vertices``; hand it a cffi buffer and the process dies
  inside libc. Every array here is ``MemAlloc``'d and filled with a memmove, so
  the mesh owns its storage and can be unloaded when its chunk falls behind.
  (``voxel.py`` takes the other way out -- it keeps its one shared cube mesh
  alive for the life of the process and never unloads anything.)
* **The material is process-global and its texture is swapped per draw.**
  ``LoadMaterialDefault`` allocates, and a scene that built one per run would
  leak one map array per run for the life of the daemon. The texture it points
  at is owned by the texture cache, so this module must never unload it.
"""

from __future__ import annotations

import array
from typing import Callable, Iterable, Sequence

from PIL import Image

from . import rl, textures, voxel

#: Faces in atlas order, their outward normals, and the four corners of each
#: seen from outside. Same order and winding as ``voxel._cube_mesh``, so the
#: two agree about which sixth of a strip is which face.
_N = {"top": (0, 1, 0), "bottom": (0, -1, 0), "north": (0, 0, -1),
      "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0)}
_H = 0.5
_CORNERS = {
    "top": ((-_H, _H, _H), (_H, _H, _H), (_H, _H, -_H), (-_H, _H, -_H)),
    "bottom": ((-_H, -_H, -_H), (_H, -_H, -_H), (_H, -_H, _H), (-_H, -_H, _H)),
    "north": ((_H, -_H, -_H), (-_H, -_H, -_H), (-_H, _H, -_H), (_H, _H, -_H)),
    "south": ((-_H, -_H, _H), (_H, -_H, _H), (_H, _H, _H), (-_H, _H, _H)),
    "east": ((_H, -_H, _H), (_H, -_H, -_H), (_H, _H, -_H), (_H, _H, _H)),
    "west": ((-_H, -_H, -_H), (-_H, -_H, _H), (-_H, _H, _H), (-_H, _H, -_H)),
}
#: Per-face constants, hoisted out of the inner loop once: the neighbour
#: offset, the corner positions, and the u range of the face's tile.
_FACE_DATA = tuple(
    (_N[f], _CORNERS[f], fi / 6.0, (fi + 1) / 6.0)
    for fi, f in enumerate(voxel.FACES)
)

_material = None


def _shared_material():
    """The one Material every chunk is drawn with. See the module docstring."""
    global _material
    if _material is None:
        _material = rl.LoadMaterialDefault()
    return _material


class BlockAtlas:
    """Every style in one texture, plus the row each of them lives on.

    ``recipe`` is a sequence of ``(name, kwargs)`` where the keyword arguments
    are :func:`voxel.face_strip`'s -- ``base`` positional, then ``noise``,
    ``seed``, ``top``, ``side_band``, ``pattern``. The order fixes the rows, so
    it must be stable for a given key: the texture is cached under that key and
    a second atlas with the same key and a different order would draw the first
    one's pixels with the second one's indices.
    """

    def __init__(self, key: str, recipe: Sequence[tuple[str, dict]],
                 see_through: Iterable[str] = ()) -> None:
        self.names = [name for name, _ in recipe]
        self.index = {name: i for i, name in enumerate(self.names)}
        self.count = len(recipe)
        #: Styles a neighbouring face is still drawn against -- glass, water,
        #: leaves, iron bars. Without this the pane between two rooms is culled
        #: from both sides and the wall has a hole in it.
        self.see_through = frozenset(see_through)
        self.clear_index = frozenset(self.index[n] for n in self.see_through
                                     if n in self.index)
        self.texture = textures.from_pil(f"atlas-{key}",
                                         lambda: _stack(recipe))
        rl.SetTextureFilter(self.texture, rl.TEXTURE_FILTER_POINT)

    def of(self, style: str) -> int:
        return self.index[style]


def _stack(recipe: Sequence[tuple[str, dict]]) -> Image.Image:
    """The catalogue as one 96 x 16N image, one style a row."""
    im = Image.new("RGBA", (96, 16 * len(recipe)))
    for i, (_name, kwargs) in enumerate(recipe):
        im.paste(voxel.face_strip(**kwargs), (0, i * 16))
    return im


class ChunkMesh:
    """One uploaded patch of geometry, and where it is."""

    __slots__ = ("mesh", "faces", "cx", "cy", "cz", "centre")

    def __init__(self, mesh, faces: int, key: tuple[int, int, int],
                 size: int) -> None:
        self.mesh = mesh
        self.faces = faces
        self.cx, self.cy, self.cz = key
        self.centre = ((self.cx + 0.5) * size, (self.cy + 0.5) * size,
                       (self.cz + 0.5) * size)

    def unload(self) -> None:
        if self.mesh is not None:
            rl.UnloadMesh(self.mesh[0])
            self.mesh = None


def build_mesh(world: dict, keys: Iterable[tuple[int, int, int]],
               atlas: BlockAtlas) -> "tuple[object, int] | None":
    """Mesh the cells in ``keys``, culled against the whole of ``world``.

    The neighbour test reads ``world`` and not just the chunk, which is the
    difference between a tower with clean seams and one with a lattice of
    invisible interior faces at every chunk boundary -- geometry that costs
    build time and draw time and can never be seen.
    """
    verts = array.array("f")
    norms = array.array("f")
    uvs = array.array("f")
    idx = array.array("H")
    n = 0
    get = world.get
    rows = atlas.count
    clear = atlas.clear_index
    for cell in keys:
        si = get(cell)
        if si is None:
            continue
        cx, cy, cz = cell
        v0, v1 = si / rows, (si + 1) / rows
        for (nx, ny, nz), corners, u0, u1 in _FACE_DATA:
            other = get((cx + nx, cy + ny, cz + nz))
            if other is not None:
                if other not in clear:
                    continue         # opaque neighbour: nothing of mine shows
                if other == si:
                    continue         # glass against the same glass, as vanilla
            for ci, (vx, vy, vz) in enumerate(corners):
                verts.append(cx + vx)
                # +0.5, because this project counts a cell's y as the height of
                # its *floor* and its x and z as the centre. Everything that
                # reasons about standing on a block -- ``surface = y + 1`` --
                # depends on that, and a mesh centred on y instead would draw
                # the whole building half a block below the world it collides
                # with.
                verts.append(cy + vy + 0.5)
                verts.append(cz + vz)
                norms.append(nx)
                norms.append(ny)
                norms.append(nz)
                uvs.append(u0 if ci in (0, 3) else u1)
                uvs.append(v1 if ci in (0, 1) else v0)
            idx.extend((n, n + 1, n + 2, n, n + 2, n + 3))
            n += 4
            if n > 65000:
                # Indices are 16-bit, which is raylib's Mesh, so a chunk that
                # somehow reached sixteen thousand visible faces would wrap
                # silently and draw garbage. Stop instead: the caller's chunk
                # size is what needs fixing, and a chunk with a corner missing
                # is a legible symptom where a wrapped index is not.
                break
        if n > 65000:
            break
    if n == 0:
        return None
    return _upload(verts, norms, uvs, idx, n), n // 4


def _upload(verts, norms, uvs, idx, n):
    mesh = rl.ffi.new("Mesh *")
    mesh.vertexCount = n
    mesh.triangleCount = len(idx) // 3
    for field, arr, ctype in (("vertices", verts, "float *"),
                              ("normals", norms, "float *"),
                              ("texcoords", uvs, "float *"),
                              ("indices", idx, "unsigned short *")):
        raw = arr.tobytes()
        buf = rl.MemAlloc(len(raw))
        rl.ffi.memmove(buf, raw, len(raw))
        setattr(mesh, field, rl.ffi.cast(ctype, buf))
    rl.UploadMesh(mesh, False)
    return mesh


class ChunkedVolume:
    """A world of cells, meshed a chunk at a time and drawn tinted.

    The contract is deliberately small: write cells, mark what changed, build
    what is pending when there is time for it, draw what is near. Nothing here
    knows what a tower is.
    """

    #: Cells a chunk is on a side. Eight is the fog argument in the module
    #: docstring; it is also small enough that a chunk rebuilds in about a
    #: millisecond and large enough that a tower is tens of chunks rather than
    #: hundreds.
    SIZE = 8

    def __init__(self, atlas: BlockAtlas) -> None:
        self.atlas = atlas
        #: cell -> style index. The single source of truth; meshes are derived.
        self.cells: dict[tuple[int, int, int], int] = {}
        self._by_chunk: dict[tuple[int, int, int], list] = {}
        self._meshes: dict[tuple[int, int, int], ChunkMesh] = {}
        self._dirty: set[tuple[int, int, int]] = set()
        self.built = 0
        self.faces = 0

    # -- writing -----------------------------------------------------------

    def key_of(self, cell) -> tuple[int, int, int]:
        s = self.SIZE
        x, y, z = cell
        return (x // s, y // s, z // s)

    def set(self, cell: tuple[int, int, int], style: str) -> None:
        """Put one cell down. Silently wins over whatever was there."""
        si = self.atlas.of(style)
        if self.cells.get(cell) == si:
            return
        key = self.key_of(cell)
        if cell not in self.cells:
            self._by_chunk.setdefault(key, []).append(cell)
        self.cells[cell] = si
        self._touch(key, cell)

    def _touch(self, key, cell) -> None:
        """Mark this chunk and any neighbour whose culling this changes."""
        self._dirty.add(key)
        s = self.SIZE
        x, y, z = cell
        for within, (ox, oy, oz) in ((x % s, (1, 0, 0)), (y % s, (0, 1, 0)),
                                     (z % s, (0, 0, 1))):
            if within == 0:
                self._dirty.add((key[0] - ox, key[1] - oy, key[2] - oz))
            elif within == s - 1:
                self._dirty.add((key[0] + ox, key[1] + oy, key[2] + oz))

    # -- building ----------------------------------------------------------

    def pending(self) -> int:
        return len(self._dirty)

    def build_pending(self, budget: int = 1) -> int:
        """Mesh up to ``budget`` dirty chunks. Returns how many it did.

        Nearest-to-nothing ordering on purpose: chunks are built in the order
        they were dirtied, which for a course generated bottom-up is the order
        they will be looked at. A priority queue keyed on distance to the
        camera would be better and is not worth the machinery -- generation
        runs far enough ahead that no chunk is ever wanted the frame it is
        made.
        """
        done = 0
        while self._dirty and done < budget:
            key = next(iter(self._dirty))
            self._dirty.discard(key)
            self._build(key)
            done += 1
        return done

    def build_all(self) -> int:
        done = 0
        while self._dirty:
            done += self.build_pending(64)
        return done

    def _build(self, key) -> None:
        old = self._meshes.pop(key, None)
        if old is not None:
            self.faces -= old.faces
            old.unload()
        keys = self._by_chunk.get(key)
        if not keys:
            return
        # Cells removed from the world stay in the per-chunk list until its
        # next rebuild, which is here: filtering them now keeps the list from
        # growing without bound on a volume that is written and rewritten.
        live = [c for c in keys if c in self.cells]
        if len(live) != len(keys):
            self._by_chunk[key] = live
        got = build_mesh(self.cells, live, self.atlas)
        if got is None:
            return
        mesh, faces = got
        self._meshes[key] = ChunkMesh(mesh, faces, key, self.SIZE)
        self.built += 1
        self.faces += faces

    # -- reading and drawing ----------------------------------------------

    def solid(self, cell) -> bool:
        return cell in self.cells

    def drop_below(self, y: int) -> int:
        """Forget everything under ``y``. Returns how many chunks went.

        A tower climbed for four minutes is a few thousand cells of scenery
        that can no longer be seen, and an occupancy map that only grows is
        also a generator that slows down forever.
        """
        s = self.SIZE
        limit = y // s
        gone = 0
        for key in [k for k in self._meshes if k[1] < limit]:
            mesh = self._meshes.pop(key)
            self.faces -= mesh.faces
            mesh.unload()
            gone += 1
        for key in [k for k in self._by_chunk if k[1] < limit]:
            for cell in self._by_chunk.pop(key):
                self.cells.pop(cell, None)
            self._dirty.discard(key)
            # The layer that was resting on what just went now has its
            # underside exposed. Cheap to say and wrong to leave: a tower whose
            # lowest built chunk has no floor reads as a hovering slice.
            above = (key[0], key[1] + 1, key[2])
            if above in self._by_chunk:
                self._dirty.add(above)
        return gone

    def draw(self, tint: Callable[[float, float, float], rl.RGBA],
             near: "tuple[float, float, float] | None" = None,
             far: float = 1e9) -> int:
        """Draw every built chunk, tinted per chunk. Returns chunks drawn.

        ``tint`` is handed a chunk's centre and answers with the colour it
        should be multiplied by -- which is how distance fog reaches meshed
        geometry at all, there being no per-vertex colour to put it in (the
        software rasteriser ignores material colour whenever a colour attribute
        exists, so a vertex-coloured mesh would render differently in CI than
        on a GPU).
        """
        material = _shared_material()
        material.maps[rl.MATERIAL_MAP_ALBEDO].texture = self.atlas.texture
        xform = rl.MatrixIdentity()
        drawn = 0
        far2 = far * far
        for mesh in self._meshes.values():
            cx, cy, cz = mesh.centre
            if near is not None:
                dx, dy, dz = cx - near[0], cy - near[1], cz - near[2]
                if dx * dx + dy * dy + dz * dz > far2:
                    continue
            material.maps[rl.MATERIAL_MAP_ALBEDO].color = tint(cx, cy, cz)
            rl.DrawMesh(mesh.mesh[0], material, xform)
            drawn += 1
        return drawn

    def teardown(self) -> None:
        for mesh in self._meshes.values():
            mesh.unload()
        self._meshes.clear()
        self._by_chunk.clear()
        self.cells.clear()
        self._dirty.clear()
