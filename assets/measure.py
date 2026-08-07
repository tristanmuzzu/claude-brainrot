"""Measure the committed assets and record what the runtime needs to know.

The runner's collision model needs real numbers: how tall the character is
while running, how low it actually gets while rolling, how big a train is,
where a train's roof surface sits. Guessing any of these is how a jump ends up
passing through a barrier, so they are *measured* -- from the same meshes that
get drawn -- and written to ``metrics.json`` next to the .glb files.

Recording them rather than measuring at startup keeps the overlay's launch
cheap (CPU-skinning 30 poses is not free) and, more importantly, makes drift
detectable: ``tests/test_assets.py`` re-measures and fails if a rebuilt asset
no longer matches what the scenes were tuned against.

    python assets/measure.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("BRAINROT_HEADLESS", "1")

from brainrot import assets                      # noqa: E402
from brainrot.engine import rl                   # noqa: E402
from brainrot.engine.collide import model_aabb, posed_aabb  # noqa: E402

#: Samples per animation clip. The profile is used to bound the body over a
#: whole clip, so this only needs to be fine enough to catch the extremes.
SAMPLES = 24

#: Half-width of the running corridor, in model X. Props that bridge the whole
#: track -- gantries, hoardings -- have legs standing on the ground well
#: outside the lanes, so their overall bounding box says "blocks everything
#: from the ballast up" when what actually threatens the runner is the soffit
#: of the beam. The corridor profile measures only the geometry over the
#: lanes, which is the part a body can hit.
CORRIDOR_HALF_X = 3.0

OUT = Path(__file__).resolve().parent.parent / "src" / "brainrot" / "assets" / "data" / "metrics.json"


def _round(box, nd=4):
    return [round(v, nd) for v in
            (box.x0, box.y0, box.z0, box.x1, box.y1, box.z1)]


def _corridor_span(model) -> list[float] | None:
    """Vertical extent of the geometry standing over the lanes, or None when
    the asset has nothing there.

    Tested per triangle, not per vertex: a beam that bridges the whole track
    is built from boxes whose corners all sit *outside* the corridor, so a
    vertex test reports that a hoarding has nothing over the lanes at all.
    """
    lo, hi = float("inf"), float("-inf")
    for i in range(model.meshCount):
        mesh = model.meshes[i]
        count = mesh.vertexCount * 3
        if count <= 0:
            continue
        verts = rl.ffi.unpack(mesh.vertices, count)
        if mesh.indices:
            idx = rl.ffi.unpack(mesh.indices, mesh.triangleCount * 3)
        else:
            idx = range(mesh.vertexCount)
        for t in range(0, len(idx) - 2, 3):
            xs, ys = [], []
            for k in range(3):
                v = idx[t + k] * 3
                xs.append(verts[v])
                ys.append(verts[v + 1])
            if min(xs) <= CORRIDOR_HALF_X and max(xs) >= -CORRIDOR_HALF_X:
                lo = min(lo, min(ys))
                hi = max(hi, max(ys))
    if lo == float("inf"):
        return None
    return [round(lo, 4), round(hi, 4)]


def measure() -> dict:
    result: dict[str, dict] = {}
    for name in assets.available():
        asset = assets.load(name)
        entry: dict = {"bounds": _round(model_aabb(asset.model))}
        span = _corridor_span(asset.model)
        if span is not None:
            entry["corridor"] = span
        if asset.clips:
            clips = {}
            for clip in sorted(asset.clips):
                frames = []
                for i in range(SAMPLES):
                    asset.pose(clip, i / SAMPLES)
                    frames.append(_round(posed_aabb(asset.model)))
                # The union is what a hitbox must respect for the whole clip.
                union = [min(f[k] for f in frames) for k in range(3)] + \
                        [max(f[k] for f in frames) for k in range(3, 6)]
                clips[clip] = {
                    "union": [round(v, 4) for v in union],
                    "frames": frames,
                }
            entry["clips"] = clips
        result[name] = entry
    return result


def main() -> int:
    rl.SetTraceLogLevel(rl.LOG_ERROR)
    rl.InitWindow(64, 64, b"measure")
    data = {"samples": SAMPLES, "assets": measure()}
    rl.CloseWindow()
    OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[assets] wrote {OUT} ({len(data['assets'])} assets)")
    for name, entry in sorted(data["assets"].items()):
        b = entry["bounds"]
        note = ""
        if "clips" in entry:
            tall = max(c["union"][4] for c in entry["clips"].values())
            low = min(c["union"][1] for c in entry["clips"].values())
            note = f"  posed y[{low:.2f},{tall:.2f}] over {len(entry['clips'])} clips"
        print(f"  {name:12s} {b[3]-b[0]:5.2f} x {b[4]-b[1]:5.2f} x {b[5]-b[2]:5.2f}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
