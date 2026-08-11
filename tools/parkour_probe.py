"""Measure the parkour scene's geometry and motion.

A probe, not a test: it reports numbers a rewrite can be judged against rather
than asserting a threshold. Every solid box comes from the same arithmetic
``ParkourScene._draw_course`` draws with, so an overlap it reports is one you
can see. Run: ``python tools/parkour_probe.py --runs 20``
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.config import Config                       # noqa: E402
from brainrot.engine import scene as scene_api           # noqa: E402
from brainrot.engine.collide import AABB                 # noqa: E402
from brainrot.engine.window import HeadlessWindow        # noqa: E402
from brainrot.palette import generate as generate_palette  # noqa: E402
from brainrot.rng import Seed                            # noqa: E402

W, H = 360, 640
DT = 1.0 / 60.0
CELL = 2.0          # spatial hash cell, in metres
TOUCH = 0.001       # penetration below this is "faces meeting"
_window = None


def ensure_window():
    """One offscreen window per process, as tests/conftest.py does it."""
    global _window
    if _window is None:
        cfg = Config()
        cfg.width, cfg.height = W, H
        _window = HeadlessWindow()
        _window.create(cfg)
    return _window


def build(run: int):
    seed = Seed.for_run(run)
    ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
    return scene_api.build("parkour", ctx)


def box(cx: float, cy: float, cz: float, sx: float, sy: float, sz: float) -> AABB:
    return AABB(cx - sx / 2, cy - sy / 2, cz - sz / 2,
                cx + sx / 2, cy + sy / 2, cz + sz / 2)


def solids(blk: dict) -> list[tuple[str, AABB]]:
    """Every solid box a block draws, from ``_draw_course``'s own arithmetic."""
    bx, by, bz = blk["x"], blk["y"], blk["z"]
    form = blk["form"]
    out: list[tuple[str, AABB]] = []
    if form == "wide":
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                out.append((f"wide{ox:+d}{oz:+d}",
                            box(bx + ox, by + 0.5, bz + oz, 1.0, 1.0, 1.0)))
    elif form == "slab":
        out.append(("slab", box(bx, by + 0.25, bz, 1.0, 0.5, 1.0)))
    else:
        out.append(("core", box(bx, by + 0.5, bz, 1.0, 1.0, 1.0)))
    for i, d in enumerate(blk["deco"]):
        out.append((f"deco{i}:{d['style']}",
                    box(bx + d["dx"], by + d["dy"] + d["sy"] / 2, bz + d["dz"],
                        d["sx"], d["sy"], d["sz"])))
    return out


def deco_centres(blk: dict) -> list[tuple[float, float, float]]:
    """A decoration's *cell*, not its centre.

    A cube's centre is half a metre up from the cell it fills, so measuring
    centres against the lattice reports nought per cent for a decoration set
    that is perfectly aligned. What has to be integral is where the piece sits
    -- and for sub-block furniture (fence posts, rails, wall torches) only the
    cell is: those are deliberately offset within it, exactly as vanilla's are.
    """
    out = []
    for d in blk["deco"]:
        if d["sx"] > 0.5 and d["sz"] > 0.5:
            out.append((blk["x"] + d["dx"], blk["y"] + d["dy"],
                        blk["z"] + d["dz"]))
        else:
            out.append((blk["x"] + round(d["dx"]), blk["y"] + round(d["dy"]),
                        blk["z"] + round(d["dz"])))
    return out


def overlapping_pairs(boxes: list[tuple[int, str, AABB]]):
    """Yield (i, j, depth) for boxes that interpenetrate, via a spatial hash."""
    grid: dict[tuple[int, int], list[int]] = {}
    for idx, (_, _, b) in enumerate(boxes):
        for cx in range(int(math.floor(b.x0 / CELL)), int(math.floor(b.x1 / CELL)) + 1):
            for cz in range(int(math.floor(b.z0 / CELL)),
                            int(math.floor(b.z1 / CELL)) + 1):
                grid.setdefault((cx, cz), []).append(idx)
    seen: set[tuple[int, int]] = set()
    for bucket in grid.values():
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                key = (bucket[a], bucket[b])
                if key in seen:
                    continue
                seen.add(key)
                depth = boxes[key[0]][2].penetration(boxes[key[1]][2])
                if depth > TOUCH:
                    yield key[0], key[1], depth


def is_int(v: float) -> bool:
    return abs(v - round(v)) < 1e-6


#: Block-index buckets the hop distribution is reported in. The ramp reaches
#: full difficulty at RAMP_BLOCKS (80), so the first two buckets straddle it and
#: the last two show that it then holds rather than running away.
BUCKETS = ((0, 40), (40, 80), (80, 200), (200, 10 ** 6))


def geometry(runs: int, blocks: int) -> dict:
    pairs = 0
    stuck = 0
    ramp: list[list[float]] = [[] for _ in BUCKETS]
    worst = 0.0
    top: list[tuple[float, str]] = []      # deepest offenders, max 3 per run
    boxes_total = 0
    aligned_blocks = aligned_deco = n_blocks = n_deco = 0
    for run in range(1, runs + 1):
        scene = build(run)
        while len(scene.blocks) < blocks:
            scene._spawn_block()
        stuck += scene.stuck
        for i, (a, b) in enumerate(zip(scene.blocks, scene.blocks[1:])):
            frm, to = scene._takeoff_point(a), scene._land_point(b)
            d = math.dist((frm[0], frm[2]), (to[0], to[2]))
            for bucket, (lo, hi) in zip(ramp, BUCKETS):
                if lo <= i < hi:
                    bucket.append(d)
                    break
        flat: list[tuple[int, str, AABB]] = []
        for bi, blk in enumerate(scene.blocks):
            n_blocks += 1
            if is_int(blk["x"]) and is_int(blk["y"]) and is_int(blk["z"]):
                aligned_blocks += 1
            for cx, cy, cz in deco_centres(blk):
                n_deco += 1
                if is_int(cx) and is_int(cy) and is_int(cz):
                    aligned_deco += 1
            for what, b in solids(blk):
                flat.append((bi, what, b))
        boxes_total += len(flat)
        here: list[tuple[float, str]] = []
        for i, j, depth in overlapping_pairs(flat):
            pairs += 1
            worst = max(worst, depth)
            ai, aw, _ = flat[i]
            bj, bw, _ = flat[j]
            here.append((depth, f"run={run} a={ai}/{aw} b={bj}/{bw} "
                                f"depth={depth:.3f}"))
        here.sort(key=lambda e: -e[0])
        top = sorted(top + here[:3], key=lambda e: -e[0])[:10]
    return {"runs": runs, "blocks_per_run": blocks, "boxes": boxes_total,
            "overlapping_pairs": pairs, "stuck": stuck, "worst_penetration": worst,
            "ramp": [stats(b) for b in ramp],
            "examples": [e for _, e in top],
            "block_grid_fraction": aligned_blocks / max(1, n_blocks),
            "deco_grid_fraction": aligned_deco / max(1, n_deco),
            "n_blocks": n_blocks, "n_deco": n_deco}


def stats(v: list[float]) -> dict:
    """Both averages, on purpose.

    A hop length is one of a handful of discrete values -- whole cells, minus
    two edge offsets -- so a median snaps from one mode to the next and can
    move the wrong way between two samples that differ by a few per cent. The
    mean is what the difficulty ramp is legible in; the median is what the
    distribution is honestly described by. Reporting one without the other has
    already produced one wrong conclusion.
    """
    if not v:
        return {"n": 0, "min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0}
    return {"n": len(v), "min": min(v), "median": statistics.median(v),
            "mean": statistics.fmean(v), "max": max(v)}


def motion(runs: int, seconds: float) -> dict:
    frames = int(seconds / DT)
    speeds: list[float] = []
    air: list[float] = []
    ground: list[float] = []
    hops: list[float] = []
    #: Take-off point to landing point: the jump itself, and the number
    #: ``fit_gap`` and ``hop_span`` are written in. ``hops`` above is landing to
    #: landing, which also contains the run across the block in between -- a
    #: different and larger quantity, and the one this probe has always
    #: reported, so both are kept.
    flights: list[float] = []
    #: The same flights, per run and in the order they were made, so the
    #: difficulty ramp can be read off a run rather than asserted about it.
    per_run: list[list[float]] = []
    frozen = 0
    body_hits = 0
    body_worst = 0.0
    body_where = ""
    body_frames = 0
    for run in range(1, runs + 1):
        scene = build(run)
        prev = list(scene.pos)
        phase = scene.phase
        phase_started = 0.0
        stand = list(scene.stand)
        here: list[float] = []
        per_run.append(here)
        for f in range(frames):
            scene.update(DT)
            scene.elapsed += DT
            now = scene.elapsed
            speed = math.dist((prev[0], prev[2]),
                              (scene.pos[0], scene.pos[2])) / DT
            speeds.append(speed)
            if speed < 0.05:
                frozen += 1
            prev = list(scene.pos)
            if scene.phase != phase:
                dur = now - phase_started
                (air if phase == "air" else ground).append(dur)
                if scene.phase == "air":
                    flights.append(math.dist(
                        (scene.takeoff[0], scene.takeoff[2]),
                        (scene.land_at[0], scene.land_at[2])))
                    here.append(flights[-1])
                else:
                    hops.append(math.dist((stand[0], stand[2]),
                                          (scene.stand[0], scene.stand[2])))
                    stand = list(scene.stand)
                phase, phase_started = scene.phase, now
            # body against the world
            body = scene.body_box()
            body_frames += 1
            feet = scene.pos[1]
            hit = 0.0
            where = ""
            for bi, blk in enumerate(scene.blocks):
                for what, b in solids(blk):
                    if abs(b.y1 - feet) < 0.05:
                        continue                     # standing on it
                    depth = body.penetration(b)
                    if depth > hit:
                        hit, where = depth, f"run={run} frame={f} {bi}/{what}"
            if hit > 0.02:
                body_hits += 1
                if hit > body_worst:
                    body_worst, body_where = hit, where
    # The ramp, read off the runs rather than asserted: each run's flights cut
    # into three, and the same third of every run pooled. A course that gets
    # harder shows it here and nowhere else.
    thirds = []
    for k in range(3):
        pooled: list[float] = []
        for run_flights in per_run:
            n = len(run_flights) // 3
            pooled += run_flights[k * n:(k + 1) * n] if n else []
        thirds.append(stats(pooled))
    return {"runs": runs, "seconds": seconds, "frames": len(speeds),
            "speed": stats(speeds), "frozen_fraction": frozen / max(1, len(speeds)),
            "air": stats(air), "ground": stats(ground), "hop": stats(hops),
            "flight": stats(flights), "thirds": thirds,
            "body_frames": body_frames, "body_hit_frames": body_hits,
            "body_worst": body_worst, "body_worst_where": body_where}


def line(label: str, s: dict, unit: str) -> str:
    return (f"  {label:<22} n={s['n']:<6} min={s['min']:.3f} "
            f"med={s['median']:.3f} mean={s['mean']:.3f} "
            f"max={s['max']:.3f} {unit}")


def report(geo: dict, mot: dict) -> str:
    out = []
    out.append("== interpenetration ==")
    out.append(f"  {geo['runs']} runs x {geo['blocks_per_run']} blocks "
               f"= {geo['boxes']} solid boxes")
    out.append(f"  overlapping pairs : {geo['overlapping_pairs']}")
    out.append(f"  worst penetration : {geo['worst_penetration']:.3f} m")
    # The emergency hop. Must be zero: when it was not, the visible symptom
    # was a flight of stairs stacked nearly vertically.
    out.append(f"  emergency hops    : {geo['stuck']}")
    for ex in geo["examples"]:
        out.append(f"    {ex}")
    out.append("== difficulty ramp (flight, by block index) ==")
    for (lo, hi), s in zip(BUCKETS, geo["ramp"]):
        out.append(line(f"blocks {lo}-{hi if hi < 10 ** 6 else ''}", s, "m"))
    out.append("== grid alignment ==")
    out.append(f"  course blocks on integer grid : "
               f"{geo['block_grid_fraction'] * 100:.1f}% of {geo['n_blocks']}")
    out.append(f"  deco cells on integer grid    : "
               f"{geo['deco_grid_fraction'] * 100:.1f}% of {geo['n_deco']}")
    out.append(f"== motion ({mot['runs']} runs x {mot['seconds']:.0f}s, "
               f"{mot['frames']} frames) ==")
    out.append(line("horiz speed", mot["speed"], "m/s"))
    out.append(f"  {'frozen (<0.05 m/s)':<22} {mot['frozen_fraction'] * 100:.1f}%"
               " of frames")
    out.append(line("air phase", mot["air"], "s"))
    out.append(line("ground phase", mot["ground"], "s"))
    out.append(line("stand to stand", mot["hop"], "m"))
    out.append(line("flight (jump)", mot["flight"], "m"))
    out.append("== difficulty ramp (flight, by third of a played run) ==")
    for k, s in enumerate(mot["thirds"]):
        out.append(line(f"third {k + 1}", s, "m"))
    out.append("== body vs world ==")
    out.append(f"  frames inside a solid : {mot['body_hit_frames']} of "
               f"{mot['body_frames']}")
    out.append(f"  worst depth           : {mot['body_worst']:.3f} m "
               f"{mot['body_worst_where']}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=40)
    ap.add_argument("--blocks", type=int, default=400)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--motion-runs", type=int, default=3,
                    help="runs simulated for the motion and ramp figures")
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    ensure_window()
    geo = geometry(args.runs, args.blocks)
    mot = motion(min(args.motion_runs, args.runs), args.seconds)
    text = report(geo, mot)
    print(text)
    if args.json:
        Path(args.json).write_text(json.dumps({"geometry": geo, "motion": mot},
                                              indent=2))


if __name__ == "__main__":
    main()
