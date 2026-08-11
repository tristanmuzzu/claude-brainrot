"""Measure the tower scene: is it safe, does it climb, and is it worth watching.

A probe, not a test: it reports numbers a rewrite can be judged against rather
than asserting a threshold. Three sections, and they answer three different
complaints.

**safety** -- blocks inside each other, the body inside a block, and how often
placement fell through to its one unchecked answer. The first two are the
things that make a generated course look broken; the third is the thing that
causes them. All three must be zero.

**climb** -- how fast the run gains altitude, how long a themed ring lasts, and
how much of a revolution a viewer sees. A tower whose spiral is too slow to
read is not a tower, it is a wall, and this is the section that says so.

**pacing** -- how often the body is made to do something, what the gaps between
those moments look like, and how varied the move and set-piece mix is. "It
feels boring" is not actionable; "the ninety-fifth percentile idle is 3.5
seconds and eight in ten moves are the same move" is.

The geometry half needs no window at all -- ``scenes/towerplan`` imports no
renderer -- so a sixty-run sweep costs a few seconds. Run:

    python tools/tower_probe.py --runs 24 --motion-runs 6
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.scenes import towerplan as tp            # noqa: E402

W, H = 360, 640
DT = 1.0 / 60.0
TOUCH = 0.001
_window = None


def ensure_window():
    """One offscreen window per process, as tests/conftest.py does it."""
    global _window
    if _window is None:
        from brainrot.config import Config
        from brainrot.engine.window import HeadlessWindow
        cfg = Config()
        cfg.width, cfg.height = W, H
        _window = HeadlessWindow()
        _window.create(cfg)
    return _window


def build_scene(run: int):
    from brainrot.engine import scene as scene_api
    from brainrot.palette import generate as generate_palette
    from brainrot.rng import Seed
    seed = Seed.for_run(run)
    ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
    return scene_api.build("tower", ctx)


def grow(run: int, blocks: int, seen: list | None = None) -> tp.Course:
    """A course grown without a body, which is what the geometry half wants.

    Blocks are collected as they are laid rather than read off the live course
    at the end: the course keeps only nineteen at a time, so anything measured
    afterwards is a sample of the *last* nineteen and every difficulty-ramp
    bucket but the top one comes back empty. Which it did.
    """
    tower = tp.Tower(random.Random(run * 977 + 13), 0)
    course = tp.Course(random.Random(run * 6151 + 29), tower)
    if seen is not None:
        seen.extend(course.blocks)
    for _ in range(blocks):
        blk = course.spawn()
        if seen is not None:
            seen.append(blk)
        if len(course.blocks) > tp.AHEAD:
            course.advance(len(course.blocks) - tp.AHEAD + tp.TRAIL)
    return course


# -- safety -----------------------------------------------------------------

def solid_cells(course: tp.Course) -> Counter:
    """Every whole cell claimed by anything solid, and by how many things.

    Both the building and the course live on the same integer lattice, so
    interpenetration is a *count*: two whole cells at whole coordinates either
    are the same cell or do not touch. Anything above one is two things drawn
    inside each other, and there is no partial case to measure the depth of.
    """
    seen: Counter = Counter()
    for cell in course.struct:
        if course.struct[cell] not in tp.SEE_THROUGH:
            seen[cell] += 1
    for blk in course.blocks:
        for cell in tp._footprint(blk["x"], blk["y"], blk["z"], blk["form"]):
            seen[cell] += 1
        for d in blk["deco"]:
            if d.get("solid"):
                seen[(blk["x"] + round(d["dx"]), blk["y"] + round(d["dy"]),
                      blk["z"] + round(d["dz"]))] += 1
    return seen


def geometry(runs: int, blocks: int) -> dict:
    clashes = 0
    stuck = 0
    off_grid = 0
    n_blocks = 0
    n_cells = 0
    soft_in_solid = 0
    move_mix: Counter = Counter()
    seg_mix: Counter = Counter()
    hops: list[float] = []
    ramp: list[list[float]] = [[] for _ in BUCKETS]
    examples: list[str] = []
    for run in range(1, runs + 1):
        laid: list[dict] = []
        course = grow(run, blocks, laid)
        live = {id(b) for b in course.blocks}
        stuck += course.stuck
        cells = solid_cells(course)
        n_cells += len(cells)
        for cell, count in cells.items():
            if count > 1:
                clashes += 1
                if len(examples) < 8:
                    examples.append(f"run={run} cell={cell} claimed x{count}")
        for blk in laid:
            n_blocks += 1
            if not all(float(blk[k]).is_integer() for k in "xyz"):
                off_grid += 1
            seg_mix[blk["segment"]] += 1
            # Ladders, water and cobweb are drawn but must never be inside
            # masonry -- and only the *live* course can be asked, because a
            # block that fell off the back released its reservation and the
            # tower is entitled to build through where it was. Asking about
            # retired blocks reports the building doing exactly what it should.
            if id(blk) in live:
                for s in blk["soft"]:
                    cell = (blk["x"] + s["dx"], blk["y"] + s["dy"],
                            blk["z"] + s["dz"])
                    if cell in course.struct and \
                            course.struct[cell] not in tp.SEE_THROUGH:
                        soft_in_solid += 1
            move = blk["move"]
            if move is None:
                continue
            move_mix[move.kind] += 1
            d = math.dist((move.frm[0], move.frm[2]), (move.to[0], move.to[2]))
            hops.append(d)
            for bucket, (lo, hi) in zip(ramp, BUCKETS):
                if lo <= blk["laid"] < hi:
                    bucket.append(d)
                    break
    return {"runs": runs, "blocks_per_run": blocks, "cells": n_cells,
            "clashes": clashes, "stuck": stuck, "off_grid": off_grid,
            "n_blocks": n_blocks, "soft_in_solid": soft_in_solid,
            "moves": dict(move_mix.most_common()),
            "segments": dict(seg_mix.most_common()),
            "hop": stats(hops), "ramp": [stats(b) for b in ramp],
            "examples": examples}


BUCKETS = ((0, 40), (40, 80), (80, 200), (200, 10 ** 6))


def stats(v: list[float]) -> dict:
    """Both averages, on purpose: a hop length is one of a handful of discrete
    values, so a median snaps between modes and can move the wrong way between
    two samples that differ by a few per cent."""
    if not v:
        return {"n": 0, "min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0}
    return {"n": len(v), "min": min(v), "median": statistics.median(v),
            "mean": statistics.fmean(v), "max": max(v)}


# -- the run ----------------------------------------------------------------

def motion(runs: int, seconds: float) -> dict:
    ensure_window()
    frames = int(seconds / DT)
    climbs: list[float] = []
    ring_spans: list[float] = []
    revolutions: list[float] = []
    idles: list[float] = []
    moves: Counter = Counter()
    move_secs: Counter = Counter()
    speeds: list[float] = []
    frozen = 0
    body_hits = 0
    body_worst = 0.0
    body_where = ""
    body_frames = 0
    orbs_taken = orbs_missed = 0
    for run in range(1, runs + 1):
        scene = build_scene(run)
        y0 = scene.pos[1]
        prev = list(scene.pos)
        ring, ring_at = scene.ring, 0.0
        last_move_at = 0.0
        angle = math.atan2(scene.pos[2], scene.pos[0])
        turned = 0.0
        phase = scene.phase
        for f in range(frames):
            scene.update(DT)
            now = f * DT
            # Three-dimensional, because a ladder is a move with no
            # horizontal component at all and a "frozen" count that measured
            # only the ground plane reported every climb as a stall.
            step = math.dist(prev, scene.pos)
            speeds.append(step / DT)
            if step / DT < 0.05:
                frozen += 1
            prev = list(scene.pos)
            a = math.atan2(scene.pos[2], scene.pos[0])
            turned += abs(_wrap(a - angle))
            angle = a
            if scene.phase != phase:
                if scene.phase == "move":
                    # A "move" is a moment the body is made to do something.
                    # The gap between them is what "dead air" means here.
                    idles.append(now - last_move_at)
                    last_move_at = now
                    moves[scene.move.kind] += 1
                    move_secs[scene.move.kind] += scene.move.dur
                phase = scene.phase
            if scene.ring != ring:
                ring_spans.append(now - ring_at)
                ring, ring_at = scene.ring, now
            body_frames += 1
            hit, where = _body_depth(scene)
            if hit > 0.02:
                body_hits += 1
                if hit > body_worst:
                    body_worst, body_where = hit, f"run={run} frame={f} {where}"
        climbs.append((scene.pos[1] - y0) / seconds)
        revolutions.append(turned / (2 * math.pi) / seconds * 60.0)
        orbs_taken += scene.orbs
        orbs_missed += scene.course.orbs_missed
    return {"runs": runs, "seconds": seconds,
            "climb_rate": stats(climbs), "ring_seconds": stats(ring_spans),
            "revs_per_min": stats(revolutions), "idle": stats(idles),
            "speed": stats(speeds), "frozen_fraction": frozen / max(1, len(speeds)),
            "moves_per_min": sum(moves.values()) / (runs * seconds) * 60.0,
            "move_mix": dict(moves.most_common()),
            "move_seconds": {k: round(v, 1) for k, v in move_secs.most_common()},
            "dead_air": sum(1 for i in idles if i > 3.0) / max(1, len(idles)),
            "body_frames": body_frames, "body_hit_frames": body_hits,
            "body_worst": body_worst, "body_worst_where": body_where,
            "orbs_taken": orbs_taken, "orbs_missed": orbs_missed}


def _body_depth(scene) -> tuple[float, str]:
    """How far into a solid cell the body is, and which cell.

    Cells rather than boxes, because everything solid in this scene *is* a
    whole cell -- so the depth is how far the body's box reaches into it. The
    cell the feet are standing on is excluded: standing on a block is not being
    inside it.
    """
    worst, where = 0.0, ""
    x, y, z = scene.pos
    feet = tp._floor(y + 0.05)
    # The block being left and the block being arrived on are both exempt, and
    # that is a statement about the model rather than a fudge. A slab's walking
    # surface is halfway up its own cell, so standing on one *is* being inside
    # it; a take-off from a block's far edge leaves half the body over that
    # block for the first moment of the arc; and a landing on a near edge puts
    # the body over the destination before the feet are down. Generation makes
    # exactly the same three allowances and nothing else. Everything the course
    # did not put under your feet counts.
    blocks = scene.course.blocks
    ends = [blocks[scene.index]]
    if scene.phase == "move" and scene.index + 1 < len(blocks):
        ends.append(blocks[scene.index + 1])
    own = {c for b in ends
           for c in tp._footprint(b["x"], b["y"], b["z"], b["form"])}
    for cell in tp.body_cells(x, y, z):
        if cell not in scene.course.solid:
            continue
        if cell[1] < feet or cell in own:
            continue
        dx = 0.5 + tp.BODY_HALF_W - abs(x - cell[0])
        dz = 0.5 + tp.BODY_HALF_W - abs(z - cell[2])
        dy = min(y + tp.BODY_H, cell[1] + 1.0) - max(y, float(cell[1]))
        depth = min(dx, dy, dz)
        if depth > worst:
            worst, where = depth, str(cell)
    return worst, where


def _wrap(a: float) -> float:
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


# -- report -----------------------------------------------------------------

def line(label: str, s: dict, unit: str) -> str:
    return (f"  {label:<24} n={s['n']:<6} min={s['min']:.2f} "
            f"med={s['median']:.2f} mean={s['mean']:.2f} "
            f"max={s['max']:.2f} {unit}")


def report(geo: dict, mot: dict | None) -> str:
    out = ["== safety =="]
    out.append(f"  {geo['runs']} runs x {geo['blocks_per_run']} blocks, "
               f"{geo['cells']} solid cells")
    out.append(f"  cells claimed twice   : {geo['clashes']}")
    out.append(f"  emergency placements  : {geo['stuck']}")
    out.append(f"  blocks off the lattice: {geo['off_grid']} of {geo['n_blocks']}")
    out.append(f"  ladders/water in solid: {geo['soft_in_solid']}")
    for ex in geo["examples"]:
        out.append(f"    {ex}")
    out.append("== the course ==")
    out.append(line("move length", geo["hop"], "m"))
    for (lo, hi), s in zip(BUCKETS, geo["ramp"]):
        out.append(line(f"  blocks {lo}-{hi if hi < 10 ** 6 else ''}", s, "m"))
    total = max(1, sum(geo["moves"].values()))
    out.append("  move mix    : " + ", ".join(
        f"{k} {v * 100 / total:.1f}%" for k, v in geo["moves"].items()))
    segs = max(1, sum(geo["segments"].values()))
    out.append("  set-pieces  : " + ", ".join(
        f"{k} {v * 100 / segs:.1f}%" for k, v in geo["segments"].items()))
    if mot is None:
        return "\n".join(out)
    out.append(f"== the climb ({mot['runs']} runs x {mot['seconds']:.0f}s) ==")
    out.append(line("altitude gained", mot["climb_rate"], "m/s"))
    out.append(line("seconds on a ring", mot["ring_seconds"], "s"))
    out.append(line("revolutions", mot["revs_per_min"], "per min"))
    out.append("== pacing ==")
    out.append(f"  moves per minute      : {mot['moves_per_min']:.1f}")
    out.append(line("idle between moves", mot["idle"], "s"))
    out.append(f"  dead air (idle > 3 s) : {mot['dead_air'] * 100:.1f}%")
    out.append(line("horizontal speed", mot["speed"], "m/s"))
    out.append(f"  frozen (<0.05 m/s)    : {mot['frozen_fraction'] * 100:.1f}%"
               " of frames")
    played = max(1, sum(mot["move_mix"].values()))
    out.append("  moves played: " + ", ".join(
        f"{k} {v * 100 / played:.1f}%" for k, v in mot["move_mix"].items()))
    out.append("  seconds spent: " + ", ".join(
        f"{k} {v}" for k, v in mot["move_seconds"].items()))
    out.append("== body vs world ==")
    out.append(f"  frames inside a solid : {mot['body_hit_frames']} of "
               f"{mot['body_frames']}")
    out.append(f"  worst depth           : {mot['body_worst']:.3f} m "
               f"{mot['body_worst_where']}")
    out.append(f"  orbs taken / missed   : {mot['orbs_taken']} / "
               f"{mot['orbs_missed']}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=24)
    ap.add_argument("--blocks", type=int, default=400)
    ap.add_argument("--motion-runs", type=int, default=4)
    ap.add_argument("--seconds", type=float, default=45)
    ap.add_argument("--no-motion", action="store_true",
                    help="geometry only -- needs no window and no renderer")
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    geo = geometry(args.runs, args.blocks)
    mot = None if args.no_motion else motion(args.motion_runs, args.seconds)
    print(report(geo, mot))
    if args.json:
        Path(args.json).write_text(json.dumps({"geometry": geo, "motion": mot},
                                              indent=2))


if __name__ == "__main__":
    main()
