"""Measure the runner scene's safety and its pacing.

A probe, not a test: it reports numbers a rewrite can be judged against rather
than asserting a threshold. The safety half re-derives every obstacle box from
``RunnerScene.solid_box`` -- the same call the draw uses -- so an overlap it
reports is one you can see. The pacing half watches the autopilot and asks the
only question "is it boring?" can be turned into: how often does the runner
have to *do* something, and how long are the gaps when it does not.

Run: ``python tools/runner_probe.py --runs 12 --seconds 120``
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import Counter
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.config import Config                       # noqa: E402
from brainrot.engine import scene as scene_api           # noqa: E402
from brainrot.engine.window import HeadlessWindow        # noqa: E402
from brainrot.palette import generate as generate_palette  # noqa: E402
from brainrot.rng import Seed                            # noqa: E402
from brainrot.scenes import runner as R                  # noqa: E402

W, H = 420, 760
DT = 1.0 / 60.0
CELL = 6.0          # spatial hash cell along the track, in metres
TOUCH = 0.001       # penetration below this is "faces meeting"
#: A gap between required inputs longer than this is dead air -- the runner is
#: on rails and the viewer has nothing to watch. Three seconds is about how
#: long a Subway Surfers reel goes without a dodge before it looks like a
#: screensaver.
DEAD_AIR = 3.0
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
    return scene_api.build("runner", ctx)


def stats(v: list[float]) -> dict:
    """Percentiles as well as extremes: one 7-second gap in sixteen minutes
    says much less about the pacing than the shape of the other 99% does, and
    a max on its own invites tuning against an outlier."""
    if not v:
        return {"n": 0, "min": 0.0, "median": 0.0, "mean": 0.0, "p95": 0.0,
                "max": 0.0}
    ordered = sorted(v)
    return {"n": len(v), "min": ordered[0], "median": statistics.median(v),
            "mean": statistics.fmean(v),
            "p95": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))],
            "max": ordered[-1]}


# ---------------------------------------------------------------------------
# Safety: nothing is drawn inside anything else, and nothing is unavoidable
# ---------------------------------------------------------------------------


def overlapping_pairs(boxes: list[tuple[dict, object]]):
    """Yield (i, j, depth) for obstacle boxes that interpenetrate.

    Hashed along the track only: everything here is within a few metres of the
    centreline, so a Z hash is the whole win.
    """
    grid: dict[int, list[int]] = {}
    for idx, (_, b) in enumerate(boxes):
        for cz in range(int(math.floor(b.z0 / CELL)),
                        int(math.floor(b.z1 / CELL)) + 1):
            grid.setdefault(cz, []).append(idx)
    seen: set[tuple[int, int]] = set()
    for bucket in grid.values():
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                key = (bucket[a], bucket[b])
                if key in seen:
                    continue
                seen.add(key)
                depth = boxes[key[0]][1].penetration(boxes[key[1]][1])
                if depth > TOUCH:
                    yield key[0], key[1], depth


def safety(runs: int, seconds: float, warm: float) -> dict:
    """Simulate real runs and count everything that should never happen."""
    frames = int(seconds / DT)
    contacts = 0
    worst = 0.0
    worst_where = ""
    unsolvable = 0
    reflexes = 0
    stuck_pairs = 0
    stuck_worst = 0.0
    stuck_ex: list[str] = []
    travel = 0.0
    for run in range(1, runs + 1):
        scene = build(run)
        scene.elapsed = warm
        for _ in range(frames):
            scene.update(DT)
            scene.elapsed += DT
            # obstacle-vs-obstacle: two things drawn into the same space
            boxes = [(e, b) for e, b in scene._solids_near(R.VIEW_AHEAD)]
            for i, j, depth in overlapping_pairs(boxes):
                stuck_pairs += 1
                if depth > stuck_worst:
                    stuck_worst = depth
                    if len(stuck_ex) < 10:
                        stuck_ex.append(
                            f"run={run} {boxes[i][0]['kind']} x "
                            f"{boxes[j][0]['kind']} depth={depth:.3f}")
        contacts += scene.contacts
        if scene.worst_penetration > worst:
            worst = scene.worst_penetration
            worst_where = f"run={run} {scene.last_contact}"
        unsolvable += scene.unsolvable
        reflexes += scene.reflexes
        travel += scene.travel
    return {"runs": runs, "seconds": seconds, "warm": warm,
            "body_contacts": contacts, "worst_penetration": worst,
            "worst_where": worst_where[:180],
            "unsolvable_plans": unsolvable, "reflexes": reflexes,
            "obstacle_pairs": stuck_pairs, "obstacle_worst": stuck_worst,
            "obstacle_examples": stuck_ex,
            "travel_per_run": travel / max(1, runs)}


# ---------------------------------------------------------------------------
# Pacing: does the runner ever have to do anything?
# ---------------------------------------------------------------------------


def pacing(runs: int, seconds: float) -> dict:
    """Watch the autopilot and record every moment it is forced to act.

    An "action" is a take-off, a slide, or the start of a lane change -- the
    three things a player would have had to press a key for. The gaps between
    them are the pacing: a long one is a stretch of track with nothing in it,
    which is exactly what "it feels a bit boring" describes.
    """
    frames = int(seconds / DT)
    gaps: list[float] = []
    actions = Counter()
    per_run_actions: list[float] = []
    dead_air = 0.0
    longest_gap = 0.0
    longest_where = ""
    speed_at: dict[str, list[float]] = {}
    marks = [0.0, 15.0, 30.0, 60.0, 120.0, 180.0]
    kinds = Counter()
    kind_windows: list[int] = []       # distinct obstacle kinds per 30 s
    segments = Counter()
    mounts = 0
    ride_time = 0.0
    pops = 0
    worst_pop = 0.0
    for run in range(1, runs + 1):
        scene = build(run)
        prev_ground = 0.0
        ride_at_action = 0.0
        prev_air = scene.motion.airborne
        prev_roll = scene.motion.rolling
        prev_target = scene.motion.target_lane
        last_action = 0.0
        ride_at_action = 0.0
        n_actions = 0
        window_kinds: dict[str, int] = {}
        for f in range(frames):
            scene.update(DT)
            scene.elapsed += DT
            now = scene.elapsed
            for m in marks:
                if abs(now - m) < DT * 0.51 or (m == 0.0 and f == 0):
                    speed_at.setdefault(f"{m:.0f}s", []).append(scene.speed)
            was_air = prev_air
            fired = None
            if scene.motion.airborne and not prev_air:
                fired = "jump"
            elif scene.motion.rolling and not prev_roll:
                fired = "roll"
            elif scene.motion.target_lane != prev_target:
                fired = "lane"
            prev_air = scene.motion.airborne
            prev_roll = scene.motion.rolling
            prev_target = scene.motion.target_lane
            if fired:
                actions[fired] += 1
                n_actions += 1
                gap = now - last_action
                gaps.append(gap)
                # Riding a train roof asks nothing of the player and is the
                # least boring thing in the scene, so it does not count
                # against the idle budget -- what this measures is stretches
                # with nothing to do *and* nothing to look at.
                idle = gap - (getattr(scene, "ride_time", 0.0) - ride_at_action)
                if idle > DEAD_AIR:
                    dead_air += idle - DEAD_AIR
                if idle > longest_gap:
                    longest_gap = idle
                    longest_where = f"run={run} t={now:.1f}s"
                last_action = now
                ride_at_action = getattr(scene, "ride_time", 0.0)
            # A surface that rises under a body which is not jumping is a
            # runner being teleported upward. Running up a ramp is exactly
            # that, done slowly enough to look like running; anything more
            # than a slope's worth in one frame is a pop.
            # ``was_air`` matters: the frame a mount lands on is a legal
            # 1.44 m rise, and counting it reports the feature working as if
            # it were the bug.
            if not scene.motion.airborne and not was_air:
                rise = getattr(scene.motion, "ground", 0.0) - prev_ground
                slope = (getattr(R, "RAMP_LIP_H", 1.0) * scene.speed * DT
                         / getattr(R, "RAMP_RUN", 3.0))
                if rise > slope * 1.5 + 1e-6:
                    pops += 1
                    worst_pop = max(worst_pop, rise)
            prev_ground = getattr(scene.motion, "ground", 0.0)
            if int(now / 30.0) != int((now - DT) / 30.0):
                spawned = getattr(scene, "spawned", {})
                fresh = {k for k, v in spawned.items()
                         if v != window_kinds.get(k)}
                kind_windows.append(len({k for k in fresh if k != "coin"}))
                window_kinds = dict(spawned)
        per_run_actions.append(n_actions / seconds * 60.0)
        # ``getattr`` throughout so the probe also runs against an older
        # scene: a before/after tool that only works on "after" measures
        # nothing. The runner grew set-pieces, spawn counting and train roofs
        # in one pass, and the point of the numbers is the comparison.
        segments.update(getattr(scene, "segments", {}))
        # Only things the runner has to answer. Lamps and buildings are the
        # most numerous objects in the scene by an order of magnitude and say
        # nothing at all about whether it repeats itself.
        kinds.update({k: v for k, v in getattr(scene, "spawned", {}).items()
                      if k in R.SOLID_KINDS or k.startswith("train")
                      or k == "ramp"})
        mounts += getattr(scene, "mounts", 0)
        ride_time += getattr(scene, "ride_time", 0.0)
    # Coins are everywhere by design, and counting them swamps the mix. What a
    # viewer sees as variety is the things that make the runner move.
    coins = kinds.pop("coin", 0)
    total_kinds = sum(kinds.values()) or 1
    top3 = sum(c for _, c in kinds.most_common(3))
    per_min = {k: v / (runs * seconds) * 60.0 for k, v in kinds.items()}
    minutes = runs * seconds / 60.0
    return {"runs": runs, "seconds": seconds, "coins": coins,
            "obstacles_per_minute": per_min,
            "segments": dict(segments.most_common()),
            "segments_per_minute": {k: v / minutes for k, v in segments.items()},
            "mounts_per_minute": mounts / minutes,
            "ride_seconds_per_minute": ride_time / minutes,
            "surface_pops": pops, "worst_pop": worst_pop,
            "actions": dict(actions),
            "actions_per_minute": stats(per_run_actions),
            "gap": stats(gaps),
            "longest_gap": longest_gap, "longest_gap_where": longest_where,
            "dead_air_fraction": dead_air / max(1e-9, runs * seconds),
            "speed_at": {k: stats(v) for k, v in sorted(speed_at.items())},
            "variety": dict(kinds.most_common()),
            "top3_share": top3 / total_kinds,
            "kinds_per_30s": stats([float(k) for k in kind_windows])}


# ---------------------------------------------------------------------------
# Framing
# ---------------------------------------------------------------------------


def _project(pos, target, fovy, p) -> tuple[float, float]:
    """World point to screen pixels, with raylib's own perspective convention.

    Up is +Y and the camera never rolls, so the basis is the simple one; that
    is all `BeginMode3D` does with these numbers.
    """
    fwd = [target[i] - pos[i] for i in range(3)]
    n = math.dist((0, 0, 0), fwd) or 1.0
    fwd = [c / n for c in fwd]
    right = [-fwd[2], 0.0, fwd[0]]          # normalize(cross(fwd, +Y))
    n = math.dist((0, 0, 0), right) or 1.0
    right = [c / n for c in right]
    up = [right[1] * fwd[2] - right[2] * fwd[1],
          right[2] * fwd[0] - right[0] * fwd[2],
          right[0] * fwd[1] - right[1] * fwd[0]]
    rel = [p[i] - pos[i] for i in range(3)]
    z = sum(rel[i] * fwd[i] for i in range(3))
    if z <= 1e-4:
        return (float("nan"), float("nan"))
    x = sum(rel[i] * right[i] for i in range(3))
    y = sum(rel[i] * up[i] for i in range(3))
    ty = math.tan(math.radians(fovy) * 0.5)
    tx = ty * (W / H)
    return (W * 0.5 * (1.0 + (x / z) / tx), H * 0.5 * (1.0 - (y / z) / ty))


def framing() -> dict:
    """Where the three lanes land on a 9:16 frame, and how much of it the
    action occupies.

    Degrees are the wrong unit for this question. A vertical FOV chosen on a
    16:9 monitor leaves a very narrow horizontal one, and the symptom is not
    "the FOV is 32 degrees", it is that the outer lanes are half off the
    frame, or that the whole track is a thin ribbon down the middle with the
    interesting part of the picture too small to read.
    """
    scene = build(1)
    out: dict = {"aspect": W / H, "size": [W, H]}
    if not hasattr(scene, "camera_pose"):
        return out                       # an older scene: skip this section
    for label, speed in (("base", R.BASE_SPEED), ("top", R.TOP_SPEED)):
        scene.speed = speed
        scene.run_phase = 0.0
        scene.cam_shake = 0.0
        pos, target, fovy = scene.camera_pose()
        fovx = 2.0 * math.degrees(math.atan(math.tan(math.radians(fovy) / 2)
                                            * (W / H)))
        lanes: dict[str, list[float]] = {}
        for d in (4.0, 12.0, 30.0):
            xs = [_project(pos, target, fovy,
                           (scene._lane_x(ln), R.RAIL_TOP, -d))[0]
                  for ln in (0, 1, 2)]
            lanes[f"d={d:.0f}m"] = [x / W for x in xs]
        # the runner's own head, which is what the eye tracks
        head = _project(pos, target, fovy, (0.0, R.RAIL_TOP + 2.2, 0.0))
        feet = _project(pos, target, fovy, (0.0, R.RAIL_TOP, 0.0))
        out[label] = {"fovy": fovy, "fovx": fovx, "lanes": lanes,
                      "runner_height_fraction": abs(feet[1] - head[1]) / H,
                      "runner_feet_y_fraction": feet[1] / H}
    return out


# ---------------------------------------------------------------------------


def report(saf: dict, pac: dict, frm: dict) -> str:
    out = []
    out.append(f"== safety ({saf['runs']} runs x {saf['seconds']:.0f}s"
               f"{', warmed to top speed' if saf['warm'] else ''}) ==")
    out.append(f"  body inside an obstacle : {saf['body_contacts']} frames, "
               f"worst {saf['worst_penetration']:.3f} m")
    if saf["worst_where"]:
        out.append(f"    {saf['worst_where']}")
    out.append(f"  obstacle pairs overlapping : {saf['obstacle_pairs']}, "
               f"worst {saf['obstacle_worst']:.3f} m")
    for ex in saf["obstacle_examples"]:
        out.append(f"    {ex}")
    out.append(f"  plans with no answer   : {saf['unsolvable_plans']}")
    out.append(f"  reflex saves           : {saf['reflexes']}")
    out.append(f"  travel per run         : {saf['travel_per_run']:.0f} m")

    out.append(f"== pacing ({pac['runs']} runs x {pac['seconds']:.0f}s) ==")
    a = pac["actions"]
    out.append(f"  actions: " + ", ".join(f"{k}={v}" for k, v in sorted(a.items()))
               + f"  (total {sum(a.values())})")
    s = pac["actions_per_minute"]
    out.append(f"  actions per minute     : min={s['min']:.1f} "
               f"mean={s['mean']:.1f} max={s['max']:.1f}")
    g = pac["gap"]
    out.append(f"  idle between actions   : n={g['n']} med={g['median']:.2f} "
               f"mean={g['mean']:.2f} p95={g['p95']:.2f} max={g['max']:.2f} s")
    out.append(f"  longest gap            : {pac['longest_gap']:.2f} s "
               f"({pac['longest_gap_where']})")
    out.append(f"  dead air (>{DEAD_AIR:.0f}s idle)   : "
               f"{pac['dead_air_fraction'] * 100:.1f}% of the run")
    out.append("  speed:  " + "  ".join(
        f"{k}={v['mean']:.2f}" for k, v in pac["speed_at"].items()))
    out.append(f"  obstacle mix           : " + ", ".join(
        f"{k}={v}" for k, v in pac["variety"].items()) + f"  (+{pac['coins']} coins)")
    out.append("  per minute             : " + ", ".join(
        f"{k}={v:.1f}" for k, v in sorted(pac["obstacles_per_minute"].items(),
                                          key=lambda kv: -kv[1])))
    out.append(f"  top-3 share of spawns  : {pac['top3_share'] * 100:.1f}%")
    kw = pac["kinds_per_30s"]
    out.append(f"  distinct kinds / 30s   : min={kw['min']:.0f} "
               f"mean={kw['mean']:.1f} max={kw['max']:.0f}")
    out.append("  set-pieces / minute    : " + ", ".join(
        f"{k}={v:.1f}" for k, v in sorted(pac["segments_per_minute"].items(),
                                          key=lambda kv: -kv[1])))
    out.append(f"== riding a train roof ==")
    out.append(f"  mounts per minute      : {pac['mounts_per_minute']:.2f}")
    out.append(f"  seconds on a roof / min: {pac['ride_seconds_per_minute']:.2f}")
    out.append(f"  surface pops           : {pac['surface_pops']} "
               f"(worst {pac['worst_pop']:.3f} m in a frame)")

    if "base" not in frm:
        return "\n".join(out)
    out.append(f"== framing ({W}x{H}, aspect {frm['aspect']:.3f}) ==")
    for label in ("base", "top"):
        f = frm[label]
        out.append(f"  {label:<4} fov vertical {f['fovy']:.1f} deg, "
                   f"horizontal {f['fovx']:.1f} deg")
        for where, xs in f["lanes"].items():
            span = xs[2] - xs[0]
            flag = "  <-- outer lanes off frame" if (xs[0] < 0 or xs[2] > 1) else ""
            out.append(f"       lanes {where:<8} x = "
                       + " ".join(f"{x:+.2f}" for x in xs)
                       + f"  span {span:.2f} of width{flag}")
        out.append(f"       runner fills {f['runner_height_fraction'] * 100:.1f}% "
                   f"of frame height, feet at y={f['runner_feet_y_fraction']:.2f}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=90.0)
    ap.add_argument("--safety-runs", type=int, default=4)
    ap.add_argument("--safety-seconds", type=float, default=40.0)
    ap.add_argument("--warm", type=float, default=0.0,
                    help="start this far up the speed ramp (safety half)")
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    ensure_window()
    saf = safety(args.safety_runs, args.safety_seconds, args.warm)
    pac = pacing(args.runs, args.seconds)
    frm = framing()
    text = report(saf, pac, frm)
    print(text)
    if args.json:
        Path(args.json).write_text(json.dumps(
            {"safety": saf, "pacing": pac, "framing": frm}, indent=2))


if __name__ == "__main__":
    main()
