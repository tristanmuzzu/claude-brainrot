# The reference material

Everything this project's spiral tower is measured against. It used to live in
a session scratchpad under `/tmp`, which is a bad place for the only copy of
the thing every design decision is justified by.

## What is here

- `frames/ps1/` — 47 frames of the Parkour Spiral 1 walkthrough, one per 15 s.
- `frames/ps3/` — 75 frames of the Parkour Spiral 3 walkthrough, one per 30 s.
- `frames/speedrun/` — 49 frames of the speedrun.
- `sheets/` — the four contact sheets those frames were read off.
- `data/plates.json` — the 44 checkpoint pressure plates of the real map, in
  world coordinates. Consecutive plates bound one *level*, which is the unit
  every per-level number here is computed over.
- `data/census.json` — the palette census: 6,532 chunks with content, **485
  distinct block types**, and each block's presence by chunk.

## What is deliberately not here

- **The videos** (711 MB). Reproduce with `yt-dlp`: `AXBlPPbZFjg` (Parkour
  Spiral 1 walkthrough), `PZlCfIRy5b4` (Parkour Spiral 3), `aNwDMKzYfgo`
  (speedrun). Frames were extracted with one linear `ffmpeg -vf fps=1/N` pass
  and tiled with `magick montage` — seeking is far slower on long VP9.
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
