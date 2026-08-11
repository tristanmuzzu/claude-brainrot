"""Measure the spiral scene: is it safe, does it climb, and is it a *place*.

The same instrument as ``tools/tower_probe.py`` -- it imports that file's
safety block rather than restating it, because a probe that measures the new
scene by a new definition of "safe" measures nothing you can compare. What is
added here is the question this format exists to answer, and the ring version
had no way to ask:

**is the run happening on built ground, or on floating cubes?** Three numbers
say so. The fraction of landings that are the platform's own ground rather
than a stone the course put there; the seconds spent crossing a platform
against the seconds spent out on a bridge between two; and how many platforms
a minute go by, which is how often the world changes into somewhere else.

A platform crossing and a bridge are meant to be about the same length -- the
format is "somewhere, then the drop, then somewhere else" -- so a run that is
four fifths bridge is the old cylinder wearing a hat, whatever the screenshots
look like.

The geometry half needs no window at all, because ``scenes/spiralplan``
imports no renderer. Run:

    python tools/spiral_probe.py --runs 40 --blocks 400 --motion-runs 10
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from collections import Counter
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tower_probe as tw                                # noqa: E402
from brainrot.scenes import spiralplan as sp            # noqa: E402
from brainrot.scenes import towerplan as tp             # noqa: E402

DT = tw.DT
#: Segment labels that mean "the body is on a platform's own ground". Every
#: other label is a bridge style, and the two together are the whole course.
GROUND = frozenset(("cross", "cave", "start"))


def grow(run: int, blocks: int, seen: list | None = None) -> sp.Course:
    """A course grown without a body, as ``tower_probe.grow`` does it.

    Blocks are collected as they are laid rather than read off the course at
    the end: it keeps nineteen at a time, so anything measured afterwards is a
    sample of the last nineteen.
    """
    spiral = sp.Spiral(random.Random(run * 977 + 13), 0)
    course = sp.Course(random.Random(run * 6151 + 29), spiral)
    if seen is not None:
        seen.extend(course.blocks)
    for _ in range(blocks):
        blk = course.spawn()
        if seen is not None:
            seen.append(blk)
        if len(course.blocks) > sp.AHEAD:
            course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
    return course


def geometry(runs: int, blocks: int) -> dict:
    clashes = stuck = off_grid = n_blocks = n_cells = soft_in_solid = 0
    ground = 0
    move_mix: Counter = Counter()
    seg_mix: Counter = Counter()
    hops: list[float] = []
    ramp: list[list[float]] = [[] for _ in tw.BUCKETS]
    examples: list[str] = []
    for run in range(1, runs + 1):
        laid: list[dict] = []
        course = grow(run, blocks, laid)
        live = {id(b) for b in course.blocks}
        stuck += course.stuck
        cells = tw.solid_cells(course)
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
            # A ``floor`` landing places no block: the body is standing on
            # ground the spiral built. That count *is* the difference between
            # this format and the one it replaces.
            if blk["form"] == "floor":
                ground += 1
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
            for bucket, (lo, hi) in zip(ramp, tw.BUCKETS):
                if lo <= blk["laid"] < hi:
                    bucket.append(d)
                    break
    return {"runs": runs, "blocks_per_run": blocks, "cells": n_cells,
            "clashes": clashes, "stuck": stuck, "off_grid": off_grid,
            "n_blocks": n_blocks, "soft_in_solid": soft_in_solid,
            "on_ground": ground,
            "moves": dict(move_mix.most_common()),
            "segments": dict(seg_mix.most_common()),
            "hop": tw.stats(hops), "ramp": [tw.stats(b) for b in ramp],
            "examples": examples}


def build_scene(run: int):
    from brainrot.engine import scene as scene_api
    from brainrot.palette import generate as generate_palette
    from brainrot.rng import Seed
    seed = Seed.for_run(run)
    ctx = scene_api.SceneContext(tw.W, tw.H, generate_palette(seed), seed)
    return scene_api.build("spiral", ctx)


def motion(runs: int, seconds: float) -> dict:
    tw.ensure_window()
    frames = int(seconds / DT)
    climbs: list[float] = []
    theme_spans: list[float] = []
    pad_spans: list[float] = []
    pads_per_min: list[float] = []
    idles: list[float] = []
    moves: Counter = Counter()
    speeds: list[float] = []
    frozen = 0
    body_hits = body_frames = 0
    body_worst = 0.0
    body_where = ""
    orbs_taken = orbs_missed = 0
    ground_frames = bridge_frames = 0
    roof_frames = 0
    ground_spells: list[float] = []
    bridge_spells: list[float] = []
    for run in range(1, runs + 1):
        scene = build_scene(run)
        y0 = scene.pos[1]
        prev = list(scene.pos)
        theme, theme_at = scene.ring, 0.0
        pad, pad_at, pads = scene.course.pad_i, 0.0, 0
        last_move_at = 0.0
        phase = scene.phase
        spell, on_ground = 0.0, None
        for f in range(frames):
            scene.update(DT)
            now = f * DT
            # Where the body is *standing*, which is the honest way to ask
            # whether a run happens on built ground: the block under the feet
            # says which of the two halves of this format it belongs to.
            here = scene.course.blocks[scene.index]["segment"] in GROUND
            if on_ground is None:
                on_ground = here
            if here != on_ground:
                (ground_spells if on_ground else bridge_spells).append(spell)
                on_ground, spell = here, 0.0
            spell += DT
            if here:
                ground_frames += 1
            else:
                bridge_frames += 1
            if scene.indoor > 0.5:
                roof_frames += 1
            step = math.dist(prev, scene.pos)
            speeds.append(step / DT)
            if step / DT < 0.05:
                frozen += 1
            prev = list(scene.pos)
            if scene.phase != phase:
                if scene.phase == "move":
                    idles.append(now - last_move_at)
                    last_move_at = now
                    moves[scene.move.kind] += 1
                phase = scene.phase
            if scene.ring != theme:
                theme_spans.append(now - theme_at)
                theme, theme_at = scene.ring, now
            if scene.course.pad_i != pad:
                pad_spans.append(now - pad_at)
                pad, pad_at = scene.course.pad_i, now
                pads += 1
            body_frames += 1
            hit, where = tw._body_depth(scene)
            if hit > 0.02:
                body_hits += 1
                if hit > body_worst:
                    body_worst, body_where = hit, f"run={run} frame={f} {where}"
        climbs.append((scene.pos[1] - y0) / seconds)
        pads_per_min.append(pads / seconds * 60.0)
        orbs_taken += scene.orbs
        orbs_missed += scene.course.orbs_missed
    total = max(1, ground_frames + bridge_frames)
    return {"runs": runs, "seconds": seconds,
            "climb_rate": tw.stats(climbs),
            "theme_seconds": tw.stats(theme_spans),
            "platform_seconds": tw.stats(pad_spans),
            "pads_per_min": tw.stats(pads_per_min),
            "idle": tw.stats(idles), "speed": tw.stats(speeds),
            "frozen_fraction": frozen / max(1, len(speeds)),
            "moves_per_min": sum(moves.values()) / (runs * seconds) * 60.0,
            "move_mix": dict(moves.most_common()),
            "dead_air": sum(1 for i in idles if i > 3.0) / max(1, len(idles)),
            "ground_fraction": ground_frames / total,
            "roof_fraction": roof_frames / max(1, runs * frames),
            "on_platform": tw.stats(ground_spells),
            "on_bridge": tw.stats(bridge_spells),
            "body_frames": body_frames, "body_hit_frames": body_hits,
            "body_worst": body_worst, "body_worst_where": body_where,
            "orbs_taken": orbs_taken, "orbs_missed": orbs_missed}


def report(geo: dict, mot: dict | None) -> str:
    out = ["== safety =="]
    out.append(f"  {geo['runs']} runs x {geo['blocks_per_run']} blocks, "
               f"{geo['cells']} solid cells")
    out.append(f"  cells claimed twice   : {geo['clashes']}")
    out.append(f"  emergency placements  : {geo['stuck']} of {geo['n_blocks']}"
               f" ({geo['stuck'] * 100 / max(1, geo['n_blocks']):.2f}%)")
    out.append(f"  blocks off the lattice: {geo['off_grid']} of {geo['n_blocks']}")
    out.append(f"  ladders/water in solid: {geo['soft_in_solid']}")
    for ex in geo["examples"]:
        out.append(f"    {ex}")
    out.append("== the course ==")
    out.append(f"  landings on real ground: {geo['on_ground']} of "
               f"{geo['n_blocks']} "
               f"({geo['on_ground'] * 100 / max(1, geo['n_blocks']):.1f}%)")
    out.append(tw.line("move length", geo["hop"], "m"))
    for (lo, hi), s in zip(tw.BUCKETS, geo["ramp"]):
        out.append(tw.line(f"  blocks {lo}-{hi if hi < 10 ** 6 else ''}", s, "m"))
    total = max(1, sum(geo["moves"].values()))
    out.append("  move mix    : " + ", ".join(
        f"{k} {v * 100 / total:.1f}%" for k, v in geo["moves"].items()))
    segs = max(1, sum(geo["segments"].values()))
    out.append("  set-pieces  : " + ", ".join(
        f"{k} {v * 100 / segs:.1f}%" for k, v in geo["segments"].items()))
    if mot is None:
        return "\n".join(out)
    out.append(f"== the climb ({mot['runs']} runs x {mot['seconds']:.0f}s) ==")
    out.append(tw.line("altitude gained", mot["climb_rate"], "m/s"))
    out.append(tw.line("platforms visited", mot["pads_per_min"], "per min"))
    out.append(tw.line("seconds on a platform", mot["platform_seconds"], "s"))
    out.append(tw.line("seconds on a theme", mot["theme_seconds"], "s"))
    out.append("== ground against drop ==")
    out.append(f"  time on built ground  : "
               f"{mot['ground_fraction'] * 100:.1f}%")
    out.append(f"  time under a roof     : {mot['roof_fraction'] * 100:.1f}%")
    out.append(tw.line("one stretch on ground", mot["on_platform"], "s"))
    out.append(tw.line("one stretch on bridge", mot["on_bridge"], "s"))
    out.append("== pacing ==")
    out.append(f"  moves per minute      : {mot['moves_per_min']:.1f}")
    out.append(tw.line("idle between moves", mot["idle"], "s"))
    out.append(f"  dead air (idle > 3 s) : {mot['dead_air'] * 100:.1f}%")
    out.append(tw.line("speed", mot["speed"], "m/s"))
    out.append(f"  frozen (<0.05 m/s)    : {mot['frozen_fraction'] * 100:.1f}%"
               " of frames")
    played = max(1, sum(mot["move_mix"].values()))
    out.append("  moves played: " + ", ".join(
        f"{k} {v * 100 / played:.1f}%" for k, v in mot["move_mix"].items()))
    out.append("== body vs world ==")
    out.append(f"  frames inside a solid : {mot['body_hit_frames']} of "
               f"{mot['body_frames']} "
               f"({mot['body_hit_frames'] * 100 / max(1, mot['body_frames']):.2f}%)")
    out.append(f"  worst depth           : {mot['body_worst']:.3f} m "
               f"{mot['body_worst_where']}")
    out.append(f"  orbs taken / missed   : {mot['orbs_taken']} / "
               f"{mot['orbs_missed']}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=24)
    ap.add_argument("--blocks", type=int, default=400)
    ap.add_argument("--motion-runs", type=int, default=6)
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
