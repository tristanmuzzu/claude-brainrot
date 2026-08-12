"""Find every checkpoint plate in the real map: the course's spine.

Palette-guided: only decodes sections whose palette contains the plate, so
the whole map costs seconds. Also fits the tower's centre from the plate
cloud and reports the radius band the course lives in.
"""
import glob
import json
import math
import os

import anvil

base = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
        "ae099ecc-79f8-4994-8bb6-bf154d746d6b/scratchpad/psmap/"
        "Parkour Spiral/dimensions/minecraft/overworld/region")
WANT = ("light_weighted_pressure_plate",)

plates = []
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
            secs = []
            try:
                for sec in chunk.data.get("sections", []):
                    bs = sec.get("block_states")
                    if bs is None:
                        continue
                    names = [str(e.get("Name", "")) for e in
                             bs.get("palette", [])]
                    if any(w in n for n in names for w in WANT):
                        secs.append(int(str(sec.get("Y"))))
            except Exception:
                continue
            for sy in secs:
                for y in range(sy * 16, sy * 16 + 16):
                    for x in range(16):
                        for z in range(16):
                            try:
                                b = chunk.get_block(x, y, z)
                            except Exception:
                                continue
                            if b.id in WANT:
                                plates.append(
                                    ((rx * 32 + cx) * 16 + x, y,
                                     (rz * 32 + cz) * 16 + z))

plates.sort(key=lambda p: p[1])
if plates:
    mx = sum(p[0] for p in plates) / len(plates)
    mz = sum(p[2] for p in plates) / len(plates)
    radii = [math.hypot(p[0] - mx, p[2] - mz) for p in plates]
    ys = [p[1] for p in plates]
    print(f"{len(plates)} plates")
    print(f"centre ~ ({mx:.1f}, {mz:.1f})")
    print(f"radius min/mean/max {min(radii):.1f} / "
          f"{sum(radii)/len(radii):.1f} / {max(radii):.1f}")
    print(f"y range {min(ys)} .. {max(ys)}")
    for p, r in list(zip(plates, radii))[:60]:
        print(f"  y={p[1]:3d}  r={r:5.1f}  at ({p[0]}, {p[2]})")
out = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
       "ae099ecc-79f8-4994-8bb6-bf154d746d6b/scratchpad/plates.json")
json.dump(plates, open(out, "w"))
