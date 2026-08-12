"""Are the tower's landmarks ever actually *seen*?

The owner watched five minutes of live strip and saw one structure. Ninety-
seven per cent of them were placed. Placement rate was therefore never the
question, and this probe asks the one that is: over a real run, driven frame
by frame through the real camera, **how much of the time is a level's
signature structure large and unoccluded in front of the lens**.

A landmark counts as *seen* on a frame when three things hold together:

- its centroid is inside the frame (the scene's own 82-degree vertical field
  at the strip's aspect, so about 52 degrees across),
- nothing solid stands between the eye and it -- its own cells excepted,
  which is the point of ``Cone.mark_cells``,
- and it subtends at least ``--degrees`` (10 by default) across its widest
  axis, so a windmill three hundred metres off does not score the same as one
  you are about to run through.

The headline is **structures seen per minute** and **the share of the levels
a run passes through whose landmark was seen for at least ``--hold``
seconds**. Both are per *run*, because that is the unit the owner watches.

Not a substitute for a contact sheet: it says a structure filled some of the
frame, not that the frame looked good. It is the number that must move.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brainrot.scenes import parkourkit as pk  # noqa: E402

DT = 1.0 / 60.0
W, H = 360, 640
#: The scene's own camera: ``spiral.FOV`` is the vertical field, and the strip
#: is much taller than it is wide, so the horizontal one is the tight one and
#: is what decides whether a structure beside the course is in shot at all.
FOVY = math.radians(82.0)
FOVX = 2.0 * math.atan(math.tan(FOVY / 2.0) * (W / H))

_window = None


def ensure_window():
    global _window
    if _window is None:
        from brainrot.config import Config
        from brainrot.engine.window import HeadlessWindow
        cfg = Config()
        cfg.width, cfg.height = W, H
        _window = HeadlessWindow()
        _window.create(cfg)
    return _window


def build_scene(name: str, run: int):
    from brainrot.engine import scene as scene_api
    from brainrot.palette import generate as generate_palette
    from brainrot.rng import Seed
    seed = Seed.for_run(run)
    ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
    return scene_api.build(name, ctx)


def _wrap(a: float) -> float:
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def _extent(cells, mark) -> float:
    """Half the structure's widest span, as a radius about its centroid."""
    if not cells:
        return 0.0
    return max(math.dist((c[0], c[1], c[2]), mark) for c in cells) + 0.5


def _clear(scene, eye, mark, own) -> bool:
    """Is the line from the eye to the structure free of anything else solid?"""
    d = math.dist(eye, mark)
    if d < 1e-6:
        return True
    step = 0.35
    n = int(d / step)
    course = scene.course
    for i in range(1, n):
        t = i * step
        p = (eye[0] + (mark[0] - eye[0]) * t / d,
             eye[1] + (mark[1] - eye[1]) * t / d,
             eye[2] + (mark[2] - eye[2]) * t / d)
        cell = (pk.iround(p[0]), pk.ifloor(p[1]), pk.iround(p[2]))
        if cell in own:
            # Arrived at the structure itself: everything before it was air.
            return True
        if course.blocked(cell):
            return False
    return True


def look(scene, index: int, degrees: float) -> tuple[bool, float]:
    """``(seen, subtended degrees)`` for one landmark on this frame."""
    cone = scene.cone
    mark = cone.marks.get(index)
    if mark is None:
        return False, 0.0
    x, y, z = scene.pos
    eye = (x, y + pk.EYE, z)
    dist = math.dist(eye, mark)
    if dist < 1e-6:
        return False, 0.0
    cells = cone.mark_cells.get(index, ())
    sub = math.degrees(2.0 * math.atan(_extent(cells, mark) / dist))
    if sub < degrees:
        return False, sub
    # In frame: yaw against the horizontal field, pitch against the vertical.
    yaw = math.atan2(mark[0] - eye[0], -(mark[2] - eye[2]))
    if abs(_wrap(yaw - scene.yaw)) > FOVX / 2.0:
        return False, sub
    flat = math.hypot(mark[0] - eye[0], mark[2] - eye[2])
    pitch = math.atan2(eye[1] - mark[1], max(1e-6, flat))
    if abs(_wrap(pitch - scene.pitch)) > FOVY / 2.0:
        return False, sub
    if not _clear(scene, eye, mark, set(cells)):
        return False, sub
    return True, sub


#: The bands the answer is reported in, because one threshold is an argument
#: and three are a measurement. Ten degrees is "it was on screen"; twenty-five
#: is a structure you would describe afterwards; forty is one filling a third
#: of the frame -- the "ran through it" band.
TIERS = (10.0, 25.0, 40.0)


def run_once(name: str, run: int, seconds: float, hold: float) -> dict:
    scene = build_scene(name, run)
    frames = int(seconds / DT)
    #: (tier index, section index) -> frames seen at or above that tier.
    on: Counter = Counter()
    best: dict[int, float] = {}      # section index -> largest angle seen
    passed: set[int] = set()
    landmarked: set[int] = set()
    for _ in range(frames):
        scene.update(DT)
        here = scene.tier
        for i in (here, here + 1, here + 2):
            lv = scene.cone.level(i)
            if i <= here:
                passed.add(i)
                # The denominator is what the run was *offered*: a level whose
                # structure was standing while the body was still in or short
                # of it. A run opens part-way into a level whose landmark is
                # behind it and whose section is never dressed, and counting
                # that against the camera measures the run's starting point.
                if lv.landmark and i in scene.cone.marks:
                    landmarked.add(i)
            seen, sub = look(scene, i, TIERS[0])
            if seen:
                for t, deg in enumerate(TIERS):
                    if sub >= deg:
                        on[(t, i)] += 1
            if sub > best.get(i, 0.0):
                best[i] = sub
    held = [{i for (t, i), f in on.items()
             if t == tier and f * DT >= hold} for tier in range(len(TIERS))]
    return {
        "run": run,
        "levels": len(passed),
        "landmarked": len(landmarked),
        "seen": [len(h) for h in held],
        "seen_ids": [sorted(h) for h in held],
        "frames_on": [sum(f for (t, _), f in on.items() if t == tier)
                      for tier in range(len(TIERS))],
        "biggest": round(max(best.values(), default=0.0), 1),
        "frames": frames,
    }


def report(rows: list[dict], seconds: float, hold: float) -> str:
    runs = len(rows)
    levels = sum(r["levels"] for r in rows)
    marked = sum(r["landmarked"] for r in rows)
    frames = sum(r["frames"] for r in rows)
    out = [f"landmarks seen -- {runs} runs x {seconds:.0f} s; a structure "
           f"counts at a tier when it holds that angle, unoccluded and in "
           f"frame, for {hold:.1f} s"]
    out.append(f"  levels entered / with a landmark   {levels} / {marked}")
    for t, deg in enumerate(TIERS):
        seen = sum(r["seen"][t] for r in rows)
        on = sum(r["frames_on"][t] for r in rows)
        out.append(
            f"  over {deg:4.0f} deg   {seen:3d} seen "
            f"({100.0 * seen / max(1, marked):3.0f}% of landmarked levels), "
            f"{seen / (runs * seconds) * 60.0:4.2f}/min, "
            f"{100.0 * on / max(1, frames):4.1f}% of frames")
    out.append(f"  biggest angle subtended (per run)  "
               f"{', '.join(str(r['biggest']) for r in rows)}")
    per_run = ", ".join("%d/%d" % (r["seen"][1], r["landmarked"])
                        for r in rows)
    out.append(f"  seen per run (over {TIERS[1]:.0f} deg)       {per_run}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default="tower", choices=("tower", "spiral"))
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--seconds", type=float, default=45.0)
    ap.add_argument("--hold", type=float, default=1.5)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    ensure_window()
    rows = [run_once(args.scene, run, args.seconds, args.hold)
            for run in range(1, args.runs + 1)]
    if args.json:
        print(json.dumps(rows, default=str))
    else:
        print(report(rows, args.seconds, args.hold))


if __name__ == "__main__":
    main()
