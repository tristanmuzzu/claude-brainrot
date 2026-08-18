"""Measure how *continuous* the first-person body is, frame by frame.

The owner's complaint about the parkour scenes, in his words: the body lands,
"clicks into something", sticks to the block for a quarter of a second, then
jumps off again -- clean, but bot-like rather than a person running and
jumping the whole time. Every existing probe reads green on that scene,
because every existing probe measures *geometry* (nothing interpenetrates,
every orb is collected, no emergency placements) and the complaint is about
the derivative of the camera.

So this one measures nothing but the derivative. Three families of number,
and each is a thing the eye can see:

* **cadence** -- how long the feet are on the ground between two flights, and
  what fraction of the frames drawn that is. Vanilla, chaining sprint jumps,
  is on the ground for one or two ticks; a body that spends a fifth of its
  life standing still is a body that stops.
* **continuity** -- the size of the *one-frame* change in the things the eye
  integrates: ground speed, eye height, field of view, yaw. A step change in
  any of them is a pop, and it does not matter that the frame either side of
  it is correct. These are reported as a distribution and as a count of
  frames over a threshold, because the maximum alone hides how often it
  happens.
* **shape** -- the apex of each hop against the 1.25 m a vanilla jump reaches.
  One jump impulse is the whole of Minecraft's vertical vocabulary, so a
  course whose arcs peak at a third of that is not doing the move the viewer
  recognises however legal the arithmetic is.

Run: ``python tools/flow_probe.py --scene parkour --runs 4 --seconds 25``
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

from brainrot.config import Config                         # noqa: E402
from brainrot.engine import scene as scene_api             # noqa: E402
from brainrot.engine.window import HeadlessWindow          # noqa: E402
from brainrot.palette import generate as generate_palette  # noqa: E402
from brainrot.rng import Seed                              # noqa: E402

W, H = 360, 640
DT = 1.0 / 60.0

#: A vanilla jump apexes here, and every jump in the game apexes here. The
#: number is not a target the generator can hit on every gap -- a two-metre
#: hop cannot -- but it is what the eye is comparing against.
VANILLA_APEX = 1.25

#: What counts as a pop.
#:
#: The eye is judged on its *second* difference and not its first, and the
#: distinction is the whole reason the number means anything. A camera falling
#: with the body moves a tenth of a metre a frame and is perfectly smooth; a
#: camera dropped 0.17 m at the instant of a landing moves the same distance
#: and is a jolt. Acceleration is what separates them: gravity alone is
#: 0.008 m/frame^2, a firm landing spring is about 0.013, and a step in
#: position is an order of magnitude past both.
POP_EYE = 0.030
POP_FOV = 0.20
POP_SPEED = 1.20

_window = None


def ensure_window():
    global _window
    if _window is None:
        cfg = Config()
        cfg.width, cfg.height = W, H
        _window = HeadlessWindow()
        _window.create(cfg)
    return _window


def build(name: str, run: int):
    seed = Seed.for_run(run)
    ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
    return scene_api.build(name, ctx)


def aim(scene) -> None:
    """Point the camera exactly as ``draw`` would, without drawing."""
    try:
        scene._aim_camera()
    except TypeError:
        scene._aim_camera(scene.pos[0], scene.pos[1], scene.pos[2])


def _stats(v: list[float]) -> dict:
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "min": s[0], "med": statistics.median(s),
            "mean": statistics.fmean(s), "p95": s[int(len(s) * 0.95)],
            "p99": s[int(len(s) * 0.99)], "max": s[-1]}


def _airborne(scene) -> bool:
    """True while the feet are off the block.

    The two scene families spell the phase differently -- the flat scene's is
    ``air`` and the tower's is ``move`` -- and nothing else in either of them
    needs to know, so the translation lives here rather than in a scene.
    """
    return scene.phase != "ground"


def measure(name: str, runs: int, seconds: float) -> dict:
    frames = int(seconds / DT)
    ground: list[float] = []
    airs: list[float] = []
    speeds: list[float] = []
    d_speed: list[float] = []
    d_eye: list[float] = []
    d_fov: list[float] = []
    d_yaw: list[float] = []
    apex: list[float] = []
    landings = 0
    ground_frames = 0
    total = 0
    pops = {"eye": 0, "jump": 0, "fov": 0, "speed": 0}

    for run in range(1, runs + 1):
        scene = build(name, run)
        aim(scene)
        prev_pos = list(scene.pos)
        prev_eye = scene.camera.position.y
        prev_de = None
        prev_fov = float(scene.camera.fovy)
        prev_yaw = scene.yaw
        prev_speed = None
        phase_air = _airborne(scene)
        phase_t0 = 0.0
        elapsed = 0.0
        peak = scene.pos[1]
        launch = scene.pos[1]
        since_launch = 99
        prev_landed = getattr(scene, "landings", None)
        for _ in range(frames):
            scene.update(DT)
            # ``elapsed`` is the scene's on some scenes and not on others, and
            # the tower's is advanced by the daemon rather than by ``update``.
            elapsed += DT
            aim(scene)
            total += 1
            # Resolved before anything is judged, so the frame the feet leave
            # the ground is itself inside the take-off window.
            now_air = _airborne(scene)
            since_launch = 0 if (now_air and not phase_air) else since_launch + 1
            speed = math.dist((prev_pos[0], prev_pos[2]),
                              (scene.pos[0], scene.pos[2])) / DT
            speeds.append(speed)
            if prev_speed is not None:
                ds = abs(speed - prev_speed)
                d_speed.append(ds)
                if ds > POP_SPEED:
                    pops["speed"] += 1
            prev_speed = speed
            prev_pos = list(scene.pos)

            eye = scene.camera.position.y
            de = eye - prev_eye
            if prev_de is not None:
                jolt = abs(de - prev_de)
                d_eye.append(jolt)
                if jolt > POP_EYE:
                    # A take-off is *supposed* to be a step: one tick you are
                    # standing and the next you are moving up at the only jump
                    # impulse the game has, and softening that would be the one
                    # change here a Minecraft player would notice as wrong. Its
                    # frames are counted separately rather than forgiven, so
                    # the number stays honest about what the camera is doing.
                    pops["jump" if since_launch <= 1 else "eye"] += 1
            prev_de, prev_eye = de, eye

            fov = float(scene.camera.fovy)
            df = abs(fov - prev_fov)
            d_fov.append(df)
            if df > POP_FOV:
                pops["fov"] += 1
            prev_fov = fov

            dy = abs(math.degrees(_wrap(scene.yaw - prev_yaw)))
            d_yaw.append(dy)
            prev_yaw = scene.yaw

            if phase_air:
                peak = max(peak, scene.pos[1])
            # A landing is read off the scene's own count of them, not off the
            # phase changing between two frames. The feet are down for a tenth
            # of the time they are up, and on a one-cell landing that is now
            # routinely *shorter than a frame*: watching the phase, the probe
            # missed those landings entirely, merged the two hops either side
            # into one air phase, and measured that phase's apex against the
            # wrong block. It read 88% of a vanilla jump for a scene whose
            # take-offs measure 97% of the impulse.
            landed = getattr(scene, "landings", None)
            if landed is not None and landed != prev_landed:
                prev_landed = landed
                if phase_air:
                    airs.append(elapsed - phase_t0)
                    apex.append(peak - launch)
                landings += 1
                # Whether the body is still down at the end of this frame is
                # what ``now_air`` says; either way the next hop starts from
                # the surface just landed on -- read off the scene rather than
                # off the body, which by the end of such a frame is already
                # back in the air and a jump impulse higher.
                launch = peak = getattr(scene, "land_y", scene.pos[1])
                phase_air = now_air
                phase_t0 = elapsed
            elif now_air != phase_air:
                dur = elapsed - phase_t0
                if phase_air:
                    airs.append(dur)
                    apex.append(peak - launch)
                    if landed is None:
                        landings += 1
                else:
                    ground.append(dur)
                    # The surface, not the body: a frame that reaches across a
                    # take-off has the body a fraction of a jump up it already,
                    # and measuring the apex from there loses 0.08 m of it.
                    launch = peak = getattr(scene, "land_y", scene.pos[1])
                phase_air = now_air
                phase_t0 = elapsed
            if not now_air:
                ground_frames += 1

    return {
        "scene": name, "runs": runs, "seconds": seconds, "frames": total,
        "ground": _stats(ground), "air": _stats(airs),
        "ground_fraction": ground_frames / max(1, total),
        "landings_per_min": landings / max(1e-9, runs * seconds) * 60.0,
        "speed": _stats(speeds),
        "d_speed": _stats(d_speed), "d_eye": _stats(d_eye),
        "d_fov": _stats(d_fov), "d_yaw": _stats(d_yaw),
        "apex": _stats(apex),
        "apex_vanilla_fraction": (statistics.fmean(apex) / VANILLA_APEX)
        if apex else 0.0,
        "pops": {k: v / max(1, total) for k, v in pops.items()},
    }


def _wrap(a: float) -> float:
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def line(label: str, s: dict, unit: str) -> str:
    if not s.get("n"):
        return f"  {label:<22} (none)"
    return (f"  {label:<22} min {s['min']:.3f}  med {s['med']:.3f}  "
            f"mean {s['mean']:.3f}  p99 {s['p99']:.3f}  max {s['max']:.3f} {unit}")


def report(m: dict) -> str:
    out = [f"== {m['scene']}: flow ({m['runs']} runs x {m['seconds']:.0f}s, "
           f"{m['frames']} frames) =="]
    out.append("-- cadence --")
    out.append(line("ground phase", m["ground"], "s"))
    out.append(line("flight", m["air"], "s"))
    out.append(f"  {'frames on the ground':<22} {m['ground_fraction'] * 100:.1f}%")
    out.append(f"  {'landings per minute':<22} {m['landings_per_min']:.1f}")
    out.append("-- continuity (one-frame changes) --")
    out.append(line("horiz speed", m["speed"], "m/s"))
    out.append(line("d speed", m["d_speed"], "m/s"))
    out.append(line("eye jolt", m["d_eye"], "m/frame^2"))
    out.append(line("d fov", m["d_fov"], "deg"))
    out.append(line("d yaw", m["d_yaw"], "deg"))
    p = m["pops"]
    out.append(f"  {'popped frames':<22} eye {p['eye'] * 100:.2f}%  "
               f"fov {p['fov'] * 100:.2f}%  speed {p['speed'] * 100:.2f}%")
    out.append(f"  {'(the jump impulse)':<22} {p['jump'] * 100:.2f}% "
               "-- vanilla, and instant there too")
    out.append("-- shape --")
    out.append(line("hop apex", m["apex"], "m"))
    out.append(f"  {'mean vs vanilla 1.25m':<22} "
               f"{m['apex_vanilla_fraction'] * 100:.0f}%")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default="parkour",
                    help="parkour, tower, spiral, or 'all'")
    ap.add_argument("--runs", type=int, default=4)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    ensure_window()
    names = ["parkour", "tower", "spiral"] if args.scene == "all" \
        else [args.scene]
    blobs = []
    for name in names:
        m = measure(name, args.runs, args.seconds)
        blobs.append(m)
        print(report(m))
        print()
    if args.json:
        Path(args.json).write_text(json.dumps(blobs, indent=2))


if __name__ == "__main__":
    main()
