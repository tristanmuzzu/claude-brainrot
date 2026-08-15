# If the tower were made in Blender

Speculative. Nothing here is planned work — the owner asked for it as a
bookmark to experiment with later. Written 2026-08-16.

## Where Blender already is

Blender builds **assets only**: `assets/src/*.py` are scripts that model, bake
light into, and export the sixteen committed `.glb` files (the character rig,
the props, the ladders and vines and crops). `assets/build.py` drives them one
subprocess each, against the standalone Blender 5.0.1 unpacked at
`~/.local/share/blender/` because there is no `bpy` wheel for Python 3.14.
`tools/level_review.py --outside` already renders a built level as solid
geometry orthographically in Blender, so the pipeline *from* the world *into*
Blender exists and works.

What Blender does **not** touch is the world. The tower is generated in Python
at runtime: `scenes/levels/*.py` (33 design modules) → `scenes/handplan.py`
(placement) → `scenes/spiralplan.py` (the cone, the terrain, the dressing).

## Three different things "made in Blender" could mean

### A. Blender as the level *editor* — the one worth trying

Author a level as cubes on the lattice in the Blender viewport, export the
cells, and let the existing engine take it from there. Physics kernel, course
solver, chunk mesher, camera: all unchanged.

What it needs:

- **A convention.** One collection per level; one Blender material per game
  material (`MATERIALS` in `parkourkit` is already the name list); cubes on
  integer coordinates, which Blender's grid snapping gives free.
- **An exporter addon.** Walks the collection, reads each cube's location and
  material, emits `levels/lNN_slug.cells.json` (or `.npz` — 33 levels of a few
  thousand cells each is small). A landing is an **Empty** named in route
  order, so the course is authored by placing markers, not by writing `arc`
  and `lift` numbers against a physics table.
- **A validator on export.** The existing `tools/tower_probe.py --design-only`
  already checks every authored jump against the physics on paper and is
  instant. Run it on the exported route and refuse an export that writes a
  jump the body cannot make. That closes the one real hazard of hand-editing:
  a beautiful level nobody can complete.
- **A round-trip importer.** Generate a level with the current engine, import
  it into Blender, edit it, export it back. This is what makes the migration
  incremental instead of 33 levels of blank page.

Why this is the good version: it keeps every guarantee the lattice buys
(nothing interpenetrates, reservations hold, the walkability and re-entry
probes still mean something) and it removes the thing that actually costs time
here — designing blind against numbers and finding out what the level looks
like two probes later. It also fits how the owner prefers to work: hand-built
over procedural, judged by looking.

Cost: an addon of a few hundred lines, plus the authoring time for however
many levels get redrawn. Seeds stop varying those levels, which for a
hand-built tower they effectively already do not.

### B. Blender as the *geometry* source

Model levels as meshes rather than cubes, export glTF, draw them directly.
Gets arches, curves, sculpted rock — things a cell grid cannot say.

The problem is collision. Every guarantee in this project comes from the
lattice: `Cone.rock` answers "is this inside the tower" in closed form,
`_solid` says what is occupied, the reservations (`headroom`, `pathcells`,
`softcells`, `ground`) defend a solved jump from being built through. Mesh
collision means either a hand-built voxel proxy per level (two descriptions of
one surface, which this project has already been bitten by — the flutes drawn
a cell proud of `core_r` and walked straight through) or a voxeliser at build
time, which is Blender work of its own.

Verdict: worth it for *decoration* — landmarks, the windmill's blades, coral
fans, the bell — which is exactly what `assets/src/props_*.py` already does.
Not worth it for anything the body stands on.

### C. Blender as the *renderer* — pre-baked strip

Render each level offline as an image sequence or short video and play the
frames back as the overlay. Cycles-quality light, no runtime cost worth
mentioning, no raylib.

Dead end for this project, and worth writing down why: the strip's whole point
is that it runs while Claude thinks, for an unpredictable length of time, and
it is playable by hand (`Scene.playable`, the takeover chord). A canned video
cannot be entered, cannot be steered, and cannot be the right length. It would
also be gigabytes.

## If it were tried

Smallest useful experiment, in order:

1. Export one existing level's cells out of the engine into a `.blend` (the
   `--outside` renderer already builds the geometry — teach it to *save*
   rather than render).
2. Move ten blocks by hand in the viewport, export back through a throwaway
   script, render the level with `tools/level_review.py --level N --all`.
3. If that loop feels good, write the addon properly: collections, materials,
   route Empties, validate-on-export.

The whole question is answered by step 2 — whether seeing the level while
editing it is worth losing per-seed variation. Everything after that is
plumbing.
