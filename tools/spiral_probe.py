"""Measure the spiral tower: is it safe, does it climb, and is it a *place*.

This file is the scene's acceptance criteria written as numbers. "It feels
boring", "the blocks are inside each other" and "it doesn't look like a tower"
are all real complaints and none of them is actionable until something counts
them, so everything the format promises is counted here.

Three sections, and they answer different questions:

**Safety.** Can two things be in the same place, is anything off the lattice,
how often did placement fall through to the one answer nothing checked, does a
ladder ever end up buried in rock, and -- the one that matters most and is the
hardest to get to zero -- is the *body* ever inside the world. The last one is
measured by simulating a real run and asking, every frame, whether any cell the
body occupies is solid. Three exemptions, and they are exactly the three the
generator makes: the landing being left, the landing being arrived on, and a
slab, whose walking surface is halfway up its own cell so the feet are
genuinely inside it.

**The course.** What the parkour is made of. The move mix, the feature mix, how
far the hops are and whether they ramp, and the number this format exists for:
**how many landings are the section's own ground or something built down to it,
rather than a cube hung in the air.** A spiral tower whose landings are mostly
floating blocks is the flat scene wearing a hat, whatever the screenshots look
like.

**The climb and the pacing.** Metres a second gained, revolutions a minute,
seconds spent on one themed section, how often the body is forced to act, the
distribution of idle between those moments, and whether it is ever simply
stopped.

    python tools/spiral_probe.py --runs 40 --blocks 400 --motion-runs 10
    python tools/spiral_probe.py --no-motion        # needs no window at all

``--no-motion`` is worth knowing about: :mod:`brainrot.scenes.spiralplan`
imports no renderer, so the whole geometry half runs in a plain interpreter and
a forty-run sweep costs a few seconds.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.scenes import parkourkit as pk
from brainrot.scenes import spiralplan as sp

#: Which plan module and which scene are being measured. Rebound by ``--plan``,
#: because the hand-built tower in :mod:`brainrot.scenes.handplan` is the same
#: building, the same physics and the same renderer with its course written down
#: instead of chosen -- so every safety and pacing number here means exactly the
#: same thing for it, and holding it to the standards the generated tower
#: reached is the point. ``tools/tower_probe.py`` asks the other question, which
#: is whether it came out as designed.
SCENE = "spiral"

DT = 1.0 / 60.0
W, H = 360, 640
_window = None


def ensure_window():
    """One offscreen window per process, as ``tests/conftest.py`` does it.

    Only one raylib window may be alive at a time, so every run in a sweep
    shares this one and the scenes are built and dropped against it.
    """
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
    return scene_api.build(SCENE, ctx)


def grow(run: int, blocks: int, seen: list | None = None) -> sp.Course:
    """A course grown without a body.

    Landings are collected as they are laid rather than read off the course at
    the end: it keeps nineteen at a time, so anything measured afterwards would
    be a sample of the last nineteen.
    """
    cone = sp.Cone(random.Random(run * 977 + 13), 0)
    course = sp.Course(random.Random(run * 6151 + 29), cone)
    if seen is not None:
        seen.extend(course.blocks)
    for _ in range(blocks):
        blk = course.spawn()
        if seen is not None:
            seen.append(blk)
        if len(course.blocks) > sp.AHEAD:
            course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
    return course


def claimed_cells(course: sp.Course) -> Counter:
    """Every cell the course has *built*, counted by how many things built it.

    The cone is not in here and must not be: it is analytic, it is the ground
    everything stands on, and a pedestal meeting the terrace it is built down
    to is the pedestal working. What this catches is two course-placed things
    occupying one cell, which is interpenetration and is never acceptable.
    """
    seen: Counter = Counter()
    for cell in course.struct:
        seen[cell] += 1
    return seen


def geometry(runs: int, blocks: int) -> dict:
    clashes = stuck = off_grid = n_blocks = n_cells = soft_in_rock = 0
    ground = built = floating = 0
    orbs_laid = orbs_missed = 0
    move_mix: Counter = Counter()
    feat_mix: Counter = Counter()
    theme_mix: Counter = Counter()
    hops: list[float] = []
    ramp: list[list[float]] = [[] for _ in BUCKETS]
    lifts: Counter = Counter()
    for run in range(1, runs + 1):
        seen: list = []
        course = grow(run, blocks, seen)
        stuck += course.stuck
        orbs_missed += course.orbs_missed
        cells = claimed_cells(course)
        n_cells += len(cells)
        clashes += sum(v - 1 for v in cells.values() if v > 1)
        for cell in course.softcells:
            if course.cone.rock(cell) and cell not in course.carved:
                soft_in_rock += 1
        for i, blk in enumerate(seen):
            n_blocks += 1
            feat_mix[blk["segment"]] += 1
            theme_mix[blk["theme"]] += 1
            lifts[blk["lift"]] += 1
            orbs_laid += len(blk["orbs"])
            if any(not isinstance(v, int) for v in
                   (blk["x"], blk["y"], blk["z"])):
                off_grid += 1
            if blk["form"] == "floor":
                ground += 1
            elif blk["pedestal"] or blk["lift"] <= 1:
                built += 1
            else:
                floating += 1
            move = blk["move"]
            if move is None:
                continue
            move_mix[move.kind] += 1
            if move.kind in ("hop", "slide"):
                d = math.dist((move.frm[0], move.frm[2]),
                              (move.to[0], move.to[2]))
                hops.append(d)
                for b, (lo, hi) in enumerate(BUCKETS):
                    if lo <= i < hi:
                        ramp[b].append(d)
    return {
        "runs": runs, "blocks": n_blocks, "cells": n_cells,
        "clashes": clashes, "stuck": stuck, "off_grid": off_grid,
        "soft_in_rock": soft_in_rock,
        "orbs_laid": orbs_laid, "orbs_missed": orbs_missed,
        "ground": ground, "built": built, "floating": floating,
        "moves": move_mix, "features": feat_mix, "themes": theme_mix,
        "lifts": lifts, "hops": stats(hops),
        "ramp": [stats(v) for v in ramp],
    }


BUCKETS = ((0, 40), (40, 80), (80, 200), (200, 10 ** 6))


def stats(v: list[float]) -> dict:
    if not v:
        return {"n": 0, "min": 0.0, "med": 0.0, "mean": 0.0, "max": 0.0}
    s = sorted(v)
    return {"n": len(v), "min": s[0], "med": s[len(s) // 2],
            "mean": sum(s) / len(s), "max": s[-1],
            "p95": s[int(len(s) * 0.95)]}


#: How far a body steps up without doing anything about it. Minecraft's step
#: height is 0.6 and its jump reaches 1.25, so one block is free and two is
#: not -- which is the whole basis of the question below.
WALK_STEP = 1


def walkability(runs: int, reach: int = 60000) -> dict:
    """Can you get up the tower **without touching the parkour**?

    This is the acceptance test for the complaint that started the rebuild:
    *without the parkour you could still just walk up this*. It was true. The
    trough used to climb a block every eight of arc, which is a spiral
    staircase, and a body walks up one-block steps without noticing -- so every
    landing the generator laid was decoration on a ramp that already reached the
    top.

    So: flood-fill the **cone alone**. No course blocks, no pedestals, no
    dressing -- if it was placed, it is parkour and it does not count. From the
    start, take any horizontal step onto ground at most one block higher, and
    any drop. Report the highest the walker gets.

    A number near zero means the levels are doing their job: a flat terrace
    ending in a hole, with the next one four to six blocks up, is not something
    you can walk out of.
    """
    gains = []
    stuck_at = Counter()
    for run in range(1, runs + 1):
        cone = sp.Cone(random.Random(run * 977 + 13), 0)
        course = sp.Course(random.Random(run * 6151 + 29), cone)
        start = course.blocks[0]
        y0 = start["y"] + 1
        seen = {(start["x"], y0, start["z"])}
        queue = [(start["x"], y0, start["z"])]
        best = y0
        while queue and len(seen) < reach:
            x, y, z = queue.pop()
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, nz = x + dx, z + dz
                # Where the ground is at that column, searched from a step up
                # to a drop a body survives.
                for ny in range(y + WALK_STEP, y - 24, -1):
                    if not cone.rock((nx, ny - 1, nz)):
                        continue
                    if cone.rock((nx, ny, nz)) or cone.rock((nx, ny + 1, nz)):
                        break
                    cell = (nx, ny, nz)
                    if cell not in seen:
                        seen.add(cell)
                        queue.append(cell)
                        if ny > best:
                            best = ny
                    break
        gains.append(best - y0)
        stuck_at[best - y0] += 1
    return {"runs": runs, "gain": stats([float(g) for g in gains]),
            "worst": max(gains), "spread": sorted(stuck_at.items())}


def _body_depth(scene) -> tuple[float, str]:
    """How deep the body is inside anything solid, and what.

    The three exemptions are the three the generator itself makes, and they are
    stated in both files so neither can quietly widen them: the landing being
    left, the landing being arrived on, and a slab's own cell.
    """
    course = scene.course
    blk = course.blocks[min(scene.index, len(course.blocks) - 1)]
    nxt = course.blocks[min(scene.index + 1, len(course.blocks) - 1)]
    own = set()
    for b in (blk, nxt):
        own |= set(pk.footprint(b["x"], b["y"], b["z"], b["form"])
                   or ((b["x"], b["y"], b["z"]),))
        own |= set(b["pedestal"])
    x, y, z = scene.pos
    floor = pk.ifloor(y + 0.05)
    worst, what = 0.0, ""
    for cell in pk.body_cells(x, y, z):
        if cell[1] < floor or cell in own:
            continue
        if not course.blocked(cell):
            continue
        # How far in, measured on the axis it is least far in on -- which is
        # the honest depth of a penetration rather than the diagonal.
        dx = min(abs(x - (cell[0] - 0.5)), abs((cell[0] + 0.5) - x))
        dz = min(abs(z - (cell[2] - 0.5)), abs((cell[2] + 0.5) - z))
        d = min(dx + pk.BODY_HALF_W, dz + pk.BODY_HALF_W, 1.0)
        if d > worst:
            worst, what = d, course.struct.get(cell, "cone")
    return worst, what


def _lens_clearance(scene) -> float:
    """How far it is from the eye to the first solid thing dead ahead.

    The body being outside the world is one question and the *camera* having
    room to see is another: a block face half a metre from an eighty-degree
    lens is most of the frame while the body it belongs to is comfortably
    clear. Contact sheets kept turning up frames that were one flat colour and
    nothing in the safety section could explain them.

    Cast from the body rather than from ``scene.camera``, deliberately.
    ``_aim_camera`` runs in ``draw`` and this probe only calls ``update``, so
    the camera object is a frame stale or never set at all -- reading it gave a
    clearance of 0.12 m on every frame of every run, which looked like a
    catastrophe and was an artefact of the harness.
    """
    rays = _lens_rays(scene)
    return rays[len(rays) // 2]


#: The lens sampled across the frame rather than dead ahead: five by five
#: directions spanning most of the field of view.
#:
#: One ray was not enough and the contact sheets said so. A frame can be
#: nine tenths flat wall with a gap of corridor straight down the middle,
#: and a single centre ray reports that as eight metres of clear air. What
#: the eye calls "the lens is jammed" is *most of the frame* being one near
#: surface, so most of the frame is what has to be measured.
LENS_GRID = 5
LENS_HFOV = 0.46
LENS_VFOV = 0.62


def _lens_rays(scene) -> list[float]:
    """Distance to the first solid thing along each sampled direction."""
    eye = (scene.pos[0], scene.pos[1] + pk.EYE, scene.pos[2])
    out: list[float] = []
    half = LENS_GRID // 2
    for gy in range(-half, half + 1):
        for gx in range(-half, half + 1):
            yaw = scene.yaw + gx * LENS_HFOV / half
            pitch = scene.pitch + gy * LENS_VFOV / half
            flat = math.cos(pitch)
            fx = math.sin(yaw) * flat
            fy = -math.sin(pitch)
            fz = -math.cos(yaw) * flat
            hit = 8.0
            for i in range(1, 67):
                t = i * 0.12
                p = (eye[0] + fx * t, eye[1] + fy * t, eye[2] + fz * t)
                if scene.course.blocked((pk.iround(p[0]), pk.ifloor(p[1]),
                                         pk.iround(p[2]))):
                    hit = t
                    break
            out.append(hit)
    out.sort()
    return out


def _lens_jammed(scene) -> bool:
    """Is most of the frame one near surface? The contact-sheet complaint,
    counted: over half the sampled directions inside three metres."""
    rays = _lens_rays(scene)
    return sum(1 for d in rays if d < 3.0) > len(rays) * 0.5


def motion(runs: int, seconds: float) -> dict:
    ensure_window()
    frames = int(seconds / DT)
    climbs: list[float] = []
    theme_spans: list[float] = []
    revolutions: list[float] = []
    idles: list[float] = []
    moves: Counter = Counter()
    lens: list[float] = []
    jammed = 0
    frozen = body_frames = 0
    body_worst = 0.0
    body_where = ""
    orbs_taken = orbs_missed = 0
    total_frames = 0
    for run in range(1, runs + 1):
        scene = build_scene(run)
        y0 = scene.pos[1]
        prev = list(scene.pos)
        theme, theme_at = scene.ring, 0.0
        last_move_at = 0.0
        angle = math.atan2(scene.pos[2], scene.pos[0])
        turned = 0.0
        phase = scene.phase
        for f in range(frames):
            scene.update(DT)
            now = f * DT
            total_frames += 1
            # Three-dimensional, because a ladder is a move with no horizontal
            # component at all and a "frozen" count that measured only the
            # ground plane would report every climb as a stall.
            step = math.dist(prev, scene.pos)
            if step / DT < 0.05:
                frozen += 1
            prev = list(scene.pos)
            here = math.atan2(scene.pos[2], scene.pos[0])
            turned += abs(_wrap(here - angle))
            angle = here
            rays = _lens_rays(scene)
            lens.append(rays[len(rays) // 2])
            jammed += sum(1 for d in rays if d < 3.0) > len(rays) * 0.5
            depth, what = _body_depth(scene)
            if depth > 0.02:
                body_frames += 1
                if depth > body_worst:
                    body_worst, body_where = depth, what
            if scene.phase != phase:
                if scene.phase == "move":
                    moves[scene.move.kind if scene.move else "?"] += 1
                    idles.append(now - last_move_at)
                    last_move_at = now
                phase = scene.phase
            if scene.ring != theme:
                # The first span of a run is discarded: a run starts partway
                # into whatever section it opens in, so counting from zero
                # reports sections lasting under a second that were really
                # most-of-a-section already gone by.
                if theme_at > 0.0:
                    theme_spans.append(now - theme_at)
                theme_at = now
                theme = scene.ring
        climbs.append((scene.pos[1] - y0) / seconds)
        revolutions.append(turned / (2 * math.pi) / seconds * 60.0)
        orbs_taken += scene.orbs
        orbs_missed += scene.course.orbs_missed
    n = sum(moves.values())
    return {
        "runs": runs, "seconds": seconds, "frames": total_frames,
        "climb": stats(climbs), "revs": stats(revolutions),
        "theme_span": stats(theme_spans), "idle": stats(idles),
        "moves": moves, "per_min": n / (runs * seconds) * 60.0,
        "dead": sum(1 for i in idles if i > 3.0) / max(1, len(idles)),
        "frozen": frozen / max(1, total_frames),
        "lens": stats(lens),
        "lens_tight": sum(1 for d in lens if d < 0.8) / max(1, len(lens)),
        "lens_jammed": jammed / max(1, len(lens)),
        "body_frames": body_frames, "body_worst": body_worst,
        "body_where": body_where,
        "orbs_taken": orbs_taken, "orbs_missed": orbs_missed,
    }


def _wrap(a: float) -> float:
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def line(label: str, s: dict, unit: str) -> str:
    return (f"  {label:<34}{s['min']:6.2f} /{s['mean']:6.2f} /"
            f"{s['max']:6.2f} {unit}")


def mix(c: Counter, total: int, top: int = 12) -> str:
    return ", ".join(f"{k} {100 * v / max(1, total):.0f}%"
                     for k, v in c.most_common(top))


def runnable(runs: int, levels: int = 8, reach: int = 30000) -> dict:
    """How far along a level a no-jump walker gets: the islands metric.

    The owner's second complaint, measured: you could run most of a level's
    ground in a straight line and only jump if you felt like it. The end
    chasm makes levels unwalkable *between*; this asks whether one is
    walkable *along*. The target comes from the real map, measured with the
    same walker: none of its 43 checkpoint legs walk end to end, and the
    mean distance covered without a jump is 46%.

    Cone alone, no course blocks: start a fifth into a level on its own
    floor, step up one, drop up to three, and report how much of the arc to
    the chasm lip was covered.
    """
    from brainrot.scenes import spiralplan as base_sp
    covers = []
    full = 0
    for run in range(1, runs + 1):
        cone = sp.Cone(random.Random(run * 431 + 7), 0)
        for li in range(base_sp.START_LEVEL,
                        base_sp.START_LEVEL + levels):
            lv = cone.level(li)
            span = lv.u1 - lv.u0
            start_u = lv.u0 + span * 0.16
            radius = sum(cone.floor_range(start_u)) / 2
            th = start_u * cone.wind
            start = (round(math.cos(th) * radius), lv.y,
                     round(math.sin(th) * radius))
            if not cone.rock((start[0], start[1] - 1, start[2])):
                continue
            seen = {start}
            edge = [start]
            far = start_u
            while edge and len(seen) < reach:
                x, y, z = edge.pop()
                u = cone.unwrap(x, z, y)
                if lv.u0 <= u <= lv.u_edge:
                    far = max(far, u)
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, nz = x + dx, z + dz
                    for ny in range(y + 1, y - 4, -1):
                        if not cone.rock((nx, ny - 1, nz)):
                            continue
                        if cone.rock((nx, ny, nz)) \
                                or cone.rock((nx, ny + 1, nz)):
                            break
                        cell = (nx, ny, nz)
                        if cell not in seen:
                            seen.add(cell)
                            edge.append(cell)
                        break
            cover = (far - start_u) / max(1e-9, lv.u_edge - start_u)
            covers.append(min(1.0, cover))
            full += cover >= 0.999
    return {"legs": len(covers), "full": full,
            "mean": sum(covers) / max(1, len(covers)),
            "worst": max(covers) if covers else 0.0}


def report(geo: dict, mot: dict | None, walk: dict | None = None) -> str:
    out = [f"SAFETY   ({geo['runs']} runs x {geo['blocks'] // geo['runs']}"
           f" landings)"]
    out.append(f"  cells claimed twice               {geo['clashes']}"
               f"  (of {geo['cells']})")
    out.append(f"  landings off the lattice          {geo['off_grid']}"
               f"  (of {geo['blocks']})")
    out.append(f"  ladders/water inside rock         {geo['soft_in_rock']}")
    out.append(f"  unchecked emergency placements    {geo['stuck']}"
               f"  ({100 * geo['stuck'] / max(1, geo['blocks']):.2f}%)")
    if mot:
        # Only meaningful with a body: ``grow`` has none, so every orb it lays
        # falls off the back uncollected by construction. Reported here and
        # nowhere else.
        out.append(f"  orbs laid but not collected       "
                   f"{mot['orbs_missed']}  (of"
                   f" {mot['orbs_taken'] + mot['orbs_missed']})")
        out.append(f"  body inside the world             "
                   f"{mot['body_frames']} frames of {mot['frames']}"
                   f"  ({100 * mot['body_frames'] / max(1, mot['frames']):.2f}%,"
                   f" worst {mot['body_worst']:.2f} m"
                   f"{' in ' + mot['body_where'] if mot['body_where'] else ''})")

    if walk:
        out.append(f"  climbable without the parkour       "
                   f"{walk['gain']['max']:.0f} m at worst,"
                   f" {walk['gain']['mean']:.1f} m mean"
                   f"  ({walk['runs']} runs)")
        run = walk.get("runnable")
        if run:
            out.append(f"  runnable along a level (no jumps) "
                       f"{run['mean']:.0%} mean, {run['worst']:.0%} worst,"
                       f" {run['full']}/{run['legs']} fully"
                       f"  (real map: 46% mean, 0 fully)")
    n = geo["ground"] + geo["built"] + geo["floating"]
    out.append("")
    out.append("THE COURSE")
    # The headline number of the whole format. "On the ground" and "built down
    # to it" are both *terrain* -- the first stands on the terrace itself, the
    # second is the top of a dune, a hay stack or a mushroom stem that reaches
    # it -- and only the third is a cube hung over the drop. Reporting the
    # first alone reads as 3% and is the wrong question.
    out.append(f"  landings on built terrain         "
               f"{100 * (geo['ground'] + geo['built']) / max(1, n):.1f}%"
               f"   (terrace itself {100 * geo['ground'] / max(1, n):.1f}%)")
    out.append(f"  landings floating over the drop   "
               f"{100 * geo['floating'] / max(1, n):.1f}%")
    out.append(f"  move mix                          "
               f"{mix(geo['moves'], sum(geo['moves'].values()))}")
    out.append(f"  non-hop share                     "
               f"{100 * (1 - geo['moves']['hop'] / max(1, sum(geo['moves'].values()))):.1f}%")
    out.append(f"  features                          {len(geo['features'])}"
               f" kinds, commonest"
               f" {mix(geo['features'], geo['blocks'], 5)}")
    out.append(f"  themes seen                       {len(geo['themes'])}"
               f" of {len(sp.THEMES)}")
    out.append(line("hop length (min/mean/max)", geo["hops"], "m"))
    out.append("  mean hop by landing index         "
               + " -> ".join(f"{b['mean']:.2f}" for b in geo["ramp"]))

    if mot:
        out.append("")
        out.append(f"THE CLIMB AND THE PACING  ({mot['runs']} runs x"
                   f" {mot['seconds']:.0f}s)")
        out.append(line("altitude gained", mot["climb"], "m/s"))
        out.append(line("revolutions", mot["revs"], "per min"))
        out.append(line("seconds on one theme", mot["theme_span"], "s"))
        out.append(f"  moves per minute                  "
                   f"{mot['per_min']:.1f}")
        out.append(f"  median idle between moves         "
                   f"{mot['idle']['med']:.2f} s"
                   f"  (95th {mot['idle'].get('p95', 0):.2f},"
                   f" worst {mot['idle']['max']:.2f})")
        out.append(f"  dead air (idle over 3 s)          "
                   f"{100 * mot['dead']:.1f}%")
        out.append(f"  frozen (under 0.05 m/s, 3-D)      "
                   f"{100 * mot['frozen']:.2f}%")
        out.append(f"  moves actually taken              "
                   f"{mix(mot['moves'], sum(mot['moves'].values()))}")
        out.append(f"  orbs taken / missed               "
                   f"{mot['orbs_taken']} / {mot['orbs_missed']}")
        out.append(f"  lens to the nearest surface       "
                   f"median {mot['lens']['med']:.2f} m,"
                   f" {100 * mot['lens_tight']:.2f}% of frames under 0.8 m")
        out.append(f"  frames mostly filled by a wall    "
                   f"{100 * mot['lens_jammed']:.1f}%")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=24)
    ap.add_argument("--blocks", type=int, default=300)
    ap.add_argument("--motion-runs", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=45.0)
    ap.add_argument("--no-motion", action="store_true")
    ap.add_argument("--walk-runs", type=int, default=6)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--plan", choices=("spiral", "tower"), default="spiral",
                    help="which tower to measure: the generated one or the "
                         "hand-built one in scenes/handplan.py")
    args = ap.parse_args()
    if args.plan == "tower":
        # Rebound, not imported at the top, so that measuring the generated
        # tower never pays for importing the hand-built one's level table.
        global sp, SCENE
        from brainrot.scenes import handplan

        sp = handplan
        SCENE = "tower"

    geo = geometry(args.runs, args.blocks)
    walk = walkability(args.walk_runs)
    walk["runnable"] = runnable(max(2, args.walk_runs // 2))
    mot = None if args.no_motion else motion(args.motion_runs, args.seconds)
    if args.json:
        print(json.dumps({"geometry": geo, "motion": mot, "walk": walk},
                         default=str))
    else:
        print(report(geo, mot, walk))


if __name__ == "__main__":
    main()
