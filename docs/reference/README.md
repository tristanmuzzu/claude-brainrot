# The reference material

Everything this project's spiral tower is measured against. It used to live in
a session scratchpad under `/tmp`, which is a bad place for the only copy of
the thing every design decision is justified by.

## What is here

- `frames/ps1/` — 47 frames of the Parkour Spiral 1 walkthrough, one per 15 s.
  **Shader-rendered** — see the provenance note below before comparing any
  pixel of ours against one of these.
- `frames/ps3/` — 75 frames of the Parkour Spiral **3** walkthrough, one per
  30 s. A different map from the world save. Also shader-rendered.
- `frames/speedrun/` — 49 frames of the speedrun.
- `frames/vanilla_2hz/` — **125 frames of the speedrun at 2.22 fps**, which is
  the same 0.45 s spacing a `brainrot shoot --every 27` produces. This is the
  only reference set that is *vanilla-lit* and *matched in sampling rate*, and
  it is therefore the only one against which a pixel statistic or a
  frame-to-frame change figure means anything. Added 2026-08-13; everything
  before that date compared our flat baked light against a shader pack.
- `sheets/` — the four contact sheets those frames were read off.
- `data/plates.json` — the 44 checkpoint pressure plates of the real map, in
  world coordinates. Consecutive plates bound one *level*, which is the unit
  every per-level number here is computed over.
- `data/census.json` — the palette census: 6,532 chunks with content, **485
  distinct block types**, and each block's presence by chunk.

## What is deliberately not here

- **The videos** (711 MB). Reproduce with `yt-dlp`; frames were extracted with
  one linear `ffmpeg -vf fps=1/N` pass and tiled with `magick montage` —
  seeking is far slower on long VP9. **The provenance, read off the titles
  with `yt-dlp --skip-download --print "%(title)s"` on 2026-08-13:**

  | id | actual title | lighting |
  |---|---|---|
  | `AXBlPPbZFjg` | Minecraft Parkour Spiral [Shaders \| No Commentary \| Walkthrough], 11:43 | **shaders** |
  | `PZlCfIRy5b4` | Minecraft Parkour Spiral **3** [Shaders \| No Commentary \| Walkthrough], 37:16 | **shaders** |
  | `aNwDMKzYfgo` | Parkour Spiral - Fastest Time Possible (6:14) | vanilla |

  Two corrections fall out of that table and both mattered. `docs/RESEARCH.md`
  records that *"two of the three reference videos are Parkour Volcano, not
  Parkour Spiral"* — **that is wrong**; none of them is Volcano, and the real
  mismatch is that `ps3` is Parkour Spiral *3*, a different map from the save.
  And **both walkthroughs run a shader pack**: soft shadows, volumetric light,
  bloom and a colour grade. Any comparison of this project's flat baked light
  against `ps1` or `ps3` pixels is measuring the shader pack. Use
  `frames/vanilla_2hz/`. Re-derived: our frames read as *less* unlit than
  `ps1`/`ps3` (28% against 38 and 49) and *more* unlit than vanilla (28%
  against 17).
- **The world save** (12 MB zipped, 49 MB unpacked). The owner's copy is
  `~/Downloads/parkour-spiral-2347-v3.0.3.zip`; the map is Hielke's *Parkour
  Spiral*, 1.2M downloads, saved at Minecraft `26.2` / DataVersion 4903. Only
  the overworld has region files; the tower is centred on the origin, y 52 to
  230.
- **`realworld.json`** (39 MB) — a voxel dump of the tower produced by
  `tools/mapdig/realwalk.py`, regenerable from the save.

## The parsers

`tools/mapdig/` holds the three scripts that read the save. They need
`anvil-parser2` and `NBT` (both in `requirements.txt`; note there is no numpy
in this venv, which is why they are pure-Python loops and why they sample).

| script | what it answers |
|---|---|
| `plates.py` | where the checkpoints are, and hence where a level begins and ends; fits the tower centre from the plate cloud and reports course radius |
| `census.py` | what the map is built from, by chunk presence |
| `realwalk.py` | can a checkpoint leg be walked without jumping — the islands-not-a-ribbon number, and the voxel dump everything else is computed from |

## What was read off it

`docs/RESEARCH.md` — the findings. `docs/RULES.md` — the findings as rules a
level must satisfy. `docs/TOWER.md` — the design of this project's own tower
against them. Read them in that order.

The source material is other people's work and is here as reference for
measurement only.
