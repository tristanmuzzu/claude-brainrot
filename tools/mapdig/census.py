"""Palette census of the real Parkour Spiral map: which blocks, how often.

Reads section palettes only (cheap) plus a sampled block count on the four
central regions, and finds the tower's bounding cylinder.
"""
import collections
import glob
import json
import os
import sys

import anvil

base = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
        "ae099ecc-79f8-4994-8bb6-bf154d746d6b/scratchpad/psmap/"
        "Parkour Spiral/dimensions/minecraft/overworld/region")

palette = collections.Counter()
occupied = []          # (cx, cz) world-chunk coords with real content
for path in sorted(glob.glob(base + "/*.mca")):
    name = os.path.basename(path)[2:-4]
    rx, rz = (int(v) for v in name.split("."))
    try:
        region = anvil.Region.from_file(path)
    except Exception:
        continue
    for cx in range(32):
        for cz in range(32):
            try:
                chunk = anvil.Chunk.from_region(region, cx, cz)
            except Exception:
                continue
            ids = set()
            try:
                for sec in getattr(chunk, "data", {}).get("sections", []):
                    bs = sec.get("block_states")
                    if bs is None:
                        continue
                    for ent in bs.get("palette", []):
                        bid = str(ent.get("Name", "")).replace(
                            "minecraft:", "")
                        if bid:
                            ids.add(bid)
            except Exception:
                # fall back: sample a few blocks
                for y in range(0, 200, 8):
                    for x in range(0, 16, 4):
                        for z in range(0, 16, 4):
                            try:
                                ids.add(chunk.get_block(x, y, z).id)
                            except Exception:
                                pass
            solid = {i for i in ids if i not in
                     ("air", "cave_air", "void_air", "bedrock")}
            if solid:
                occupied.append((rx * 32 + cx, rz * 32 + cz))
                palette.update(solid)

out = {
    "chunks_with_content": len(occupied),
    "chunk_x_range": [min(c[0] for c in occupied),
                      max(c[0] for c in occupied)] if occupied else None,
    "chunk_z_range": [min(c[1] for c in occupied),
                      max(c[1] for c in occupied)] if occupied else None,
    "distinct_blocks": len(palette),
    "palette_by_chunk_presence": palette.most_common(120),
}
dst = os.path.join(os.path.dirname(base.rsplit("/psmap", 1)[0] + "/x"),
                   "census.json")
dst = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
       "ae099ecc-79f8-4994-8bb6-bf154d746d6b/scratchpad/census.json")
with open(dst, "w") as f:
    json.dump(out, f, indent=1)
print("chunks with content:", len(occupied))
print("distinct block types:", len(palette))
for bid, k in palette.most_common(60):
    print(f"{k:5d}  {bid}")
