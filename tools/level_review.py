"""Everything you need to judge one designed level, in one command.

The tower is redesigned a level at a time, and until now every one of those
questions was a different tool with no ``--level`` flag on any of them:
``level_shot`` renders a run, ``tower_probe`` prints fidelity for all
thirty-three, ``bypass_probe`` computes per-level walkability and throws the
level's name away, and the clipping check was a hand-rolled snippet that had to
get the phase-pin landmine right or silently measure a different world.

This puts them behind one name and gets the pin right in one place:

    python tools/level_review.py --level 7 --all
    python tools/level_review.py --level "CANOPY" --report --blueprint
    python tools/level_review.py --level 7 --seam

Four artefacts, and they answer different questions:

**sheet.png** -- the game camera over the whole level and eight seconds into
the next one. This is the judge. Everything else is a floor.

**blueprint.png** -- the level drawn flat: an elevation along the corridor and
a plan looking down on it, with the ground the level actually has, the course
laid over it, and the holes in between. A first-person sheet cannot show you
that the ground runs continuously past three of your jumps; this can, and that
is the complaint this tower keeps failing on.

**outside.png** -- the same level as solid geometry, rendered orthographically
in Blender from three sides. The shape of the place, with no camera in it.

**report.txt** -- the numbers for this level alone: per-beat fidelity, the move
mix, how much of it a walker covers without jumping, whether the body ever ends
up inside the world, and how long the level's own structure is on screen.

One level per process, always: the pin is a class-level monkeypatch, so a
second level in the same interpreter would be measured against the first one's
world. Rendering shells out, so ten of these run happily side by side.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from brainrot.scenes import handplan as hp  # noqa: E402
from brainrot.scenes import parkourkit as pk  # noqa: E402
from brainrot.scenes import spiralplan as sp  # noqa: E402

#: Segments that are aimed at a world feature rather than written down landing
#: by landing. Fidelity is counted over the design alone, so these are excluded
#: from it -- but they are *reported*, because a level whose course is two
#: thirds machinery is a level that has not been designed.
MACHINERY = hp.MACHINERY

#: Colours for the blueprint, by what laid the landing.
SEGMENT_COLOUR = {
    "design": (54, 122, 220),
    "ascent": (232, 146, 44),
    "lock": (44, 176, 118),
    "landmark": (168, 92, 214),
    "stuck": (220, 52, 52),
    "recover": (200, 200, 60),
    "start": (140, 140, 140),
}

_pinned = False


# ---------------------------------------------------------------------------
# The pin
# ---------------------------------------------------------------------------

def resolve(want: str) -> int:
    """Level number or name substring -> 0-based index into the roster."""
    names = [lv.name for lv in hp.LEVELS]
    try:
        i = int(want) - 1
        if not 0 <= i < len(names):
            raise ValueError
        return i
    except ValueError:
        pass
    hits = [i for i, n in enumerate(names) if want.upper() in n.upper()]
    if len(hits) != 1:
        raise SystemExit(f"level {want!r} matches {len(hits)}: "
                         + ", ".join(names[i] for i in hits) if hits
                         else f"level {want!r} matches nothing")
    return hits[0]


def pin(index: int) -> None:
    """Make every run in this process open on the level at ``index``.

    Patches the **base** class. ``handplan.Cone.__init__`` draws the phase from
    the rng before delegating, and replacing that one would skip the draw and
    shift every roll after it -- which is a different world from the one a
    normal run of the same seed builds, and is exactly what a measuring harness
    must never do. This way the draw still happens and the pin overwrites it.
    """
    global _pinned
    if _pinned:
        raise RuntimeError("one level per process: the pin is already set")
    _pinned = True
    phase = (index - sp.START_LEVEL) % len(hp.LEVELS)
    base_init = sp.Cone.__init__

    def pinned(self, rng, base_y=0):
        base_init(self, rng, base_y)
        self.phase = phase

    sp.Cone.__init__ = pinned            # type: ignore[method-assign]
    # Read inside _extend_section during construction, so it has to exist
    # before the first section does.
    hp.Cone.phase = phase                # type: ignore[attr-defined]


def grow(run: int, blocks: int):
    """A course grown without a body. Returns ``(cone, course, seen, starts)``.

    Landings are collected as they are laid: the course keeps only the last
    couple of dozen, so anything read off it at the end is a sample of the tail.
    ``starts`` is each level's first landing, which is what a walker needs.
    """
    cone = hp.Cone(random.Random(run * 977 + 13), 0)
    course = hp.Course(random.Random(run * 6151 + 29), cone)
    seen = list(course.blocks)
    starts: dict[int, dict] = {}
    for blk in seen:                    # the opening level's first landing is
        starts.setdefault(cone.level_index(course.u_of(blk)), blk)
    for _ in range(blocks):             # laid before the spawn loop begins
        blk = course.spawn()
        seen.append(blk)
        starts.setdefault(cone.level_index(course.u_of(blk)), blk)
        if len(course.blocks) > hp.AHEAD:
            course.advance(len(course.blocks) - hp.AHEAD + sp.TRAIL)
    return cone, course, seen, starts


# ---------------------------------------------------------------------------
# The numbers
# ---------------------------------------------------------------------------

def walk(name: str, runs: int, blocks: int) -> dict:
    """How much of this level a walker covers without jumping. **Unpinned.**

    Deliberately measured in an unpinned world, which is why it is its own
    entry point and gets its own process: a pinned run *opens* on the level,
    a fifth of the way along it and often on a floating landing with nothing
    standable under it, and the walk then reads zero -- not because the level
    is unwalkable but because the walker had nowhere to stand. Entered
    normally, off the level below's exit climb, it is the real number and it
    is the one ``bypass_probe`` prints tower-wide.
    """
    import bypass_probe

    covers: list[float] = []
    full = 0
    for run in range(1, runs + 1):
        cone, course, seen, starts = grow(run, blocks)
        for i in sorted(starts):
            if i == 0 or cone.design(i).name != name:
                continue
            cover, done = bypass_probe.walk_level(course, cone.level(i),
                                                  starts[i])
            if cover <= 0.0:
                continue        # this level's landings are already retired
            covers.append(cover)
            full += done
    covers.sort()
    return {"mean": sum(covers) / max(1, len(covers)),
            "worst": covers[-1] if covers else 0.0,
            "full": full, "n": len(covers)}


def _walk_unpinned(index: int, runs: int, blocks: int) -> dict:
    """``walk`` in a fresh process, because this one is pinned and it must not
    be."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools/level_review.py"), "--level",
         str(index + 1), "--walk-json", "--runs", str(runs), "--blocks",
         str(blocks)], capture_output=True, text=True, cwd=ROOT)
    for line in r.stdout.splitlines():
        if line.startswith("{"):
            return json.loads(line)
    return {"mean": 0.0, "worst": 0.0, "full": 0, "n": 0}


def measure(index: int, runs: int, blocks: int) -> dict:
    """Fidelity, beats and move mix for this level alone."""
    name = hp.LEVELS[index].name
    beats: dict[str, list] = defaultdict(lambda: [0, 0])
    tally: Counter = Counter()
    moves: Counter = Counter()
    forms: Counter = Counter()
    for run in range(1, runs + 1):
        cone, course, seen, starts = grow(run, blocks)
        for blk in seen:
            if blk["theme"] != name:
                continue
            seg = blk["segment"]
            tally["landings"] += 1
            if blk["unchecked"]:
                tally["stuck"] += 1
            if blk["move"] is not None:
                moves[blk["move"].kind] += 1
            forms[blk["form"]] += 1
            if not blk["pedestal"] and blk["form"] != "floor":
                tally["floating"] += 1
            if seg in MACHINERY:
                tally["machinery"] += 1
                tally["climb" if seg == "ascent" else "inserted"] += 1
                continue
            tally["design"] += 1
            key = seg
            beats[key][0] += 1
            if blk["exact"]:
                beats[key][1] += 1
                tally["exact"] += 1
    return {"name": name, "runs": runs, "beats": dict(beats),
            "tally": dict(tally), "moves": dict(moves), "forms": dict(forms)}


def motion(index: int, seed: int, seconds: float) -> dict:
    """Drive the real scene through this level and watch the body and the lens.

    Only the frames actually spent on the level count -- the run opens on it,
    so that is the opening stretch, and it ends when the tier moves on.
    """
    import landmark_probe
    import spiral_probe as spp

    spp.SCENE = "tower"
    spp.sp = hp
    spp.ensure_window()
    scene = spp.build_scene(seed)
    here = scene.tier
    frames = inside = jam = held = 0
    empty = 0.0
    worst, what = 0.0, ""
    run = 0.0
    for _ in range(int(seconds / spp.DT)):
        scene.update(spp.DT)
        if scene.tier != here:
            break
        frames += 1
        depth, mat = spp._body_depth(scene)
        if depth > 0.02:
            inside += 1
            if depth > worst:
                worst, what = depth, mat
        rays = spp._lens_rays(scene)
        # A ray that reaches the probe's 8 m horizon hit nothing: sky, sea, or
        # the drop. The roster sheet's complaint, counted -- every level is a
        # cliff on one side and two thirds empty frame everywhere else.
        empty += sum(1 for d in rays if d >= 7.99) / len(rays)
        jam += spp._lens_jammed(scene)
        big, _ = landmark_probe.look(scene, here, 25.0)
        if big:
            run += spp.DT
            held = max(held, run)
        else:
            run = 0.0
    return {"frames": frames, "seconds": frames * spp.DT, "inside": inside,
            "worst": worst, "what": what, "jam": jam, "landmark_hold": held,
            "empty": empty / max(1, frames)}


def report(index: int, runs: int, blocks: int, seed: int,
           seconds: float, with_motion: bool = True) -> str:
    lv = hp.LEVELS[index]
    got = measure(index, runs, blocks)
    got.update(_walk_unpinned(index, runs, blocks))
    t, n = got["tally"], max(1, got["tally"].get("landings", 1))
    des = max(1, t.get("design", 1))
    out = [f"LEVEL {index + 1}  {lv.name}   theme={lv.theme} "
           f"profile={lv.profile} band={lv.band} shelf={lv.shelf} "
           f"rise={lv.rise} gap={lv.gap} breaks={lv.breaks} "
           f"exit={lv.exit} landmark={lv.landmark or '-'}",
           f"  over {runs} runs, {t.get('landings', 0)} landings on this level",
           "",
           "FIDELITY -- how much of the design survived being built",
           f"  designed {t.get('design', 0)} ({100 * t.get('design', 0) / n:.0f}%"
           f" of the level)   exact {100 * t.get('exact', 0) / des:.0f}%",
           f"  machinery {t.get('machinery', 0)}"
           f" ({100 * t.get('machinery', 0) / n:.0f}%)"
           f"  of which exit climb {t.get('climb', 0)}",
           f"  unchecked emergency placements {t.get('stuck', 0)}"
           f"  ({100 * t.get('stuck', 0) / n:.2f}%)",
           "", "  per beat (a beat under 98% is a design to look at)"]
    for beat, (total, exact) in sorted(got["beats"].items(),
                                       key=lambda kv: kv[1][1] / max(1, kv[1][0])):
        flag = "  <--" if total >= 6 and exact / total < 0.98 else ""
        out.append(f"    {beat:14s} {exact:4d}/{total:<4d} "
                   f"{100 * exact / max(1, total):3.0f}%{flag}")
    mv = got["moves"]
    tot = max(1, sum(mv.values()))
    mix = "  ".join(f"{k} {100 * v / tot:.0f}%"
                    for k, v in sorted(mv.items(), key=lambda kv: -kv[1]))
    fm = "  ".join(f"{k} {v}" for k, v in sorted(got["forms"].items(),
                                                 key=lambda kv: -kv[1]))
    out += ["", "THE PARKOUR", f"  move mix   {mix}",
            f"  hop share  {100 * mv.get('hop', 0) / tot:.0f}%"
            "   (the rule is no more than 70%)",
            f"  forms      {fm}",
            f"  floating landings {t.get('floating', 0)}"
            f" ({100 * t.get('floating', 0) / n:.0f}%)",
            "",
            "CAN IT BE WALKED -- the complaint this tower keeps failing on",
            f"  covered without a jump   mean {100 * got['mean']:.0f}%,"
            f" worst {100 * got['worst']:.0f}%   of {got['n']} walks"
            + ("   <-- no walk seeded: this level has no standable ground at"
               " its entry at all, which is a fact about it, not a zero"
               if not got["n"] else ""),
            f"  walked end to end        {got['full']} of {got['n']}",
            "  the rule: mean at or under 55%, never end to end"
            "   (the real map: 46%, 0 of 43)"]
    if with_motion:
        m = motion(index, seed, seconds)
        out += ["", f"THROUGH THE CAMERA -- seed {seed}, "
                f"{m['seconds']:.1f} s on this level",
                f"  body inside the world   {m['inside']} of {m['frames']}"
                f" frames, worst {m['worst']:.2f} m"
                + (f" in {m['what']}" if m["what"] else ""),
                f"  lens jammed by a wall   {m['jam']} of {m['frames']} frames"
                f" ({100 * m['jam'] / max(1, m['frames']):.1f}%)",
                f"  frame empty (sky, sea, the drop)  "
                f"{100 * m['empty']:.0f}% of the view on average"
                "   (the rule is under 55%)",
                f"  structure held at 25 degrees for "
                f"{m['landmark_hold']:.1f} s   (the rule is 1.5 s)"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# The blueprint
# ---------------------------------------------------------------------------

def _ground(course, x: int, z: int, floor: int, up: int):
    """The height a body would stand at over this cell, or ``None`` for a hole.

    Scanned on the integer grid rather than in polar coordinates: sampling
    ``(bearing, radius)`` and rounding aliases badly on a circle -- whole rings
    of cells are visited twice and the ones between them never, which draws a
    solid terrace as a dashed one.
    """
    for y in range(floor + up, floor - 13, -1):
        if course.blocked((x, y - 1, z)) and not course.blocked((x, y, z)) \
                and not course.blocked((x, y + 1, z)):
            return y
    return None


def blueprint(index: int, run: int, blocks: int, path: Path) -> None:
    """The level drawn flat: elevation along the corridor, plan from above.

    The plan is the one that earns its keep. A level whose grey (ground) runs
    unbroken from one end to the other is a level you can walk, whatever the
    course does on top of it -- and that is invisible in a first-person sheet.
    """
    from PIL import Image, ImageDraw

    from brainrot.rng import Seed  # noqa: F401  (kept: import cost is the pin)

    cone, course, seen, starts = grow(run, blocks)
    name = hp.LEVELS[index].name
    lv = next(cone.level(i) for i in starts if cone.design(i).name == name)
    blks = [b for b in seen if b["theme"] == name]
    if not blks:
        raise SystemExit(f"{name}: no landings in run {run}")

    u0, u1 = lv.u0, lv.u1
    rmid = cone.outer_at((u0 + u1) / 2)
    arc = (u1 - u0) * rmid                       # metres along the corridor
    cols = 900
    du = (u1 - u0) / cols
    floor = lv.y
    head = cone.trough_height((u0 + u1) / 2)
    rlo = int(cone.outer_at((u0 + u1) / 2) - cone.band_at((u0 + u1) / 2)) - 3
    rhi = int(cone.outer_at((u0 + u1) / 2)) + 6
    rows = rhi - rlo

    pad, gap = 58, 46
    eh, ph = 300, max(150, rows * 7)
    W = cols + pad * 2
    H = pad + eh + gap + ph + pad
    img = Image.new("RGB", (W, H), (18, 18, 22))
    d = ImageDraw.Draw(img)

    ytop, ybot = floor + head + 3, floor - 14
    def ey(y):
        return pad + int(eh * (ytop - y) / max(1, ytop - ybot))
    py0 = pad + eh + gap
    def py(r):
        return py0 + int(ph * (rhi - r) / max(1, rows))

    # ground, scanned over the real cell grid inside the level's wedge
    for x in range(-rhi, rhi + 1):
        for z in range(-rhi, rhi + 1):
            r = math.hypot(x, z)
            if not (rlo <= r <= rhi):
                continue
            g = _ground(course, x, z, floor, head)
            if g is None:
                continue
            u = cone.unwrap(x, z, g)
            if not (u0 <= u <= u1):
                continue
            c = pad + int((u - u0) / max(1e-9, du))
            near = abs(g - floor) <= 1
            col = (96, 104, 96) if near else (60, 64, 74)
            # A cell subtends 1/r radians, which is many columns wide out here
            # -- drawn as a point it comes out as a Moire of dots and a solid
            # terrace reads as a hole.
            cw = max(2, int((1.0 / r) / max(1e-9, du)))
            hh = max(2, ph // max(1, rows) // 2)
            d.rectangle([c, ey(g), c + cw, ey(g) + 2], fill=col)
            d.rectangle([c, py(r) - hh, c + cw, py(r) + hh], fill=col)

    # the terrace floor line and the level's own span
    d.line([(pad, ey(floor)), (pad + cols, ey(floor))], (70, 70, 78))
    d.line([(pad, ey(floor + head)), (pad + cols, ey(floor + head))],
           (48, 48, 56))

    # the course
    pts_e, pts_p, marks = [], [], []
    for b in blks:
        u = cone.unwrap(b["x"], b["z"], b["y"] + 1)
        if not (u0 - 0.02 <= u <= u1 + 0.02):
            continue
        c = int((u - u0) / max(1e-9, du))
        x = pad + max(0, min(cols, c))
        surf = b["y"] + pk.FORMS[b["form"]]
        r = math.hypot(b["x"], b["z"])
        pts_e.append((x, ey(surf)))
        pts_p.append((x, py(r)))
        seg = b["segment"]
        col = SEGMENT_COLOUR.get(
            seg if seg in SEGMENT_COLOUR else
            ("stuck" if b["unchecked"] else "design"), SEGMENT_COLOUR["design"])
        marks.append((x, ey(surf), py(r), col, b["form"],
                      b["move"].kind if b["move"] else ""))
    if len(pts_e) > 1:
        d.line(pts_e, (120, 150, 200), 1)
        d.line(pts_p, (120, 150, 200), 1)
    for x, ye, yp, col, form, kind in marks:
        s = 3 if form in ("full", "wide", "floor") else 2
        d.rectangle([x - s, ye - s, x + s, ye + s], fill=col)
        d.rectangle([x - s, yp - s, x + s, yp + s], fill=col)
        if kind and kind != "hop":
            d.text((x - 8, ye - 16), kind[:4], fill=(240, 220, 120))

    d.text((pad, 12), f"{index + 1}. {name}   elevation along the corridor"
           f"   ({arc:.0f} m of arc, floor y={floor}, "
           f"{head} blocks of head-room)", fill=(220, 220, 226))
    d.text((pad, py0 - 22), "plan -- looking down. unbroken grey from end to "
           "end is a level you can walk.", fill=(220, 220, 226))
    for i, (k, col) in enumerate(SEGMENT_COLOUR.items()):
        d.rectangle([pad + i * 92, H - 30, pad + 8 + i * 92, H - 22], fill=col)
        d.text((pad + 12 + i * 92, H - 30), k, fill=(170, 170, 178))
    d.text((pad, py0 + ph + 8),
           f"core wall r={rlo} (top)   rim r={rhi} (bottom).  light grey is "
           "ground at the terrace floor, dark grey is anything else standable.",
           fill=(150, 150, 158))
    img.save(path)


# ---------------------------------------------------------------------------
# Blender: the level as solid geometry, from outside
# ---------------------------------------------------------------------------

_BLEND = r'''
import bpy, json, sys, math
cfg = json.load(open(sys.argv[sys.argv.index("--") + 1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("level")
mesh.from_pydata(cfg["verts"], [], cfg["faces"])
mesh.update()
ob = bpy.data.objects.new("level", mesh)
bpy.context.scene.collection.objects.link(ob)
for rgb in cfg["palette"]:
    m = bpy.data.materials.new("m")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = 0.85
    ob.data.materials.append(m)
for i, mi in enumerate(cfg["face_mat"]):
    mesh.polygons[i].material_index = mi
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 4.5
sun.rotation_euler = (0.9, 0.2, 0.8)
bpy.context.scene.collection.objects.link(sun)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.30, .34, .40, 1)
bpy.context.scene.world = w
sc = bpy.context.scene
have = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
for want in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
    if want in have:
        sc.render.engine = want
        break
if sc.render.engine == "BLENDER_WORKBENCH":
    sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 1100, 760
sc.render.film_transparent = False
cx, cy, cz = cfg["centre"]
span = cfg["span"]
# Aim with a constraint rather than by hand: an orthographic camera pointed by
# hand-computed Euler angles misses the centre of what it is looking at, and
# the level ends up in a corner of the frame.
tgt = bpy.data.objects.new("target", None)
tgt.location = (cx, cy, cz)
sc.collection.objects.link(tgt)
cam_d = bpy.data.cameras.new("c"); cam_d.type = "ORTHO"
cam_d.ortho_scale = span * 1.1
cam = bpy.data.objects.new("c", cam_d)
sc.collection.objects.link(cam); sc.camera = cam
con = cam.constraints.new("TRACK_TO")
con.target = tgt
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"
for tag, loc in cfg["views"].items():
    cam.location = loc
    cam_d.ortho_scale = span * (0.62 if tag == "out" else 1.1)
    sc.render.filepath = cfg["out"] % tag
    bpy.ops.render.render(write_still=True)
'''


def outside(index: int, run: int, blocks: int, out: Path) -> str:
    """Render the level's own cells orthographically, three ways, in Blender.

    Only faces with air on the other side are emitted, which is what keeps a
    twenty-thousand-cell level inside one mesh Blender opens instantly.
    """
    cone, course, seen, starts = grow(run, blocks)
    name = hp.LEVELS[index].name
    lv = next(cone.level(i) for i in starts if cone.design(i).name == name)
    head = cone.trough_height((lv.u0 + lv.u1) / 2)

    cells: dict[tuple, str] = {}
    for cell, mat in course.struct.items():
        u = cone.unwrap(cell[0], cell[2], cell[1] + 1)
        if lv.u0 - 0.05 <= u <= lv.u1 + 0.05 \
                and lv.y - 9 <= cell[1] <= lv.y + head + 4:
            cells[cell] = mat
    # the cone itself, sampled over the same box, so the shelf is visible
    xs = [c[0] for c in cells] or [0]
    zs = [c[2] for c in cells] or [0]
    for x in range(min(xs) - 6, max(xs) + 7):
        for z in range(min(zs) - 6, max(zs) + 7):
            for y in range(lv.y - 8, lv.y + head + 3):
                if (x, y, z) in cells:
                    continue
                if cone.rock((x, y, z)):
                    cells[(x, y, z)] = "conestone"
    if not cells:
        raise SystemExit(f"{name}: nothing built in run {run}")

    pal: list[tuple] = []
    slot: dict[str, int] = {}
    verts: list[tuple] = []
    faces: list[tuple] = []
    fmat: list[int] = []
    NB = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    CORN = {
        (1, 0, 0): ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
        (-1, 0, 0): ((0, 0, 1), (0, 1, 1), (0, 1, 0), (0, 0, 0)),
        (0, 1, 0): ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
        (0, -1, 0): ((0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1)),
        (0, 0, 1): ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
        (0, 0, -1): ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)),
    }
    for (x, y, z), mat in cells.items():
        if mat not in slot:
            rgb = pk.MATERIALS.get(mat, ((140, 140, 140),))[0]
            slot[mat] = len(pal)
            pal.append(tuple(round((c / 255.0) ** 2.2, 4) for c in rgb))
        mi = slot[mat]
        for nb in NB:
            if (x + nb[0], y + nb[1], z + nb[2]) in cells:
                continue
            base = len(verts)
            for cx, cy, cz in CORN[nb]:
                verts.append((x + cx - 0.5, z + cz - 0.5, y + cy))
            faces.append((base, base + 1, base + 2, base + 3))
            fmat.append(mi)

    mx = (min(c[0] for c in cells) + max(c[0] for c in cells)) / 2
    mz = (min(c[2] for c in cells) + max(c[2] for c in cells)) / 2
    my = lv.y + 3.0            # the terrace, not the middle of the box
    span = max(max(c[0] for c in cells) - min(c[0] for c in cells),
               max(c[2] for c in cells) - min(c[2] for c in cells)) + 8
    a = math.atan2(mz, mx)
    far = math.hypot(mx, mz) + span
    cfg = {
        "verts": verts, "faces": faces, "face_mat": fmat, "palette": pal,
        "centre": [mx, mz, my], "span": span,
        "out": str(out / "outside_%s.png"),
        "views": {
            # straight down: the plan, and where the ground runs out
            "top": [mx, mz, my + far],
            # from outside the tower, level with the terrace: the elevation
            "out": [math.cos(a) * far * 1.4, math.sin(a) * far * 1.4, my + 3],
            # three-quarters from above and outboard: the shape of the place
            "three": [math.cos(a) * far * 1.2, math.sin(a) * far * 1.2,
                      my + span * 0.75],
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    job = out / "_blender.json"
    job.write_text(json.dumps(cfg))
    script = out / "_blender.py"
    script.write_text(_BLEND)
    exe = os.environ.get("BRAINROT_BLENDER", "blender")
    # --python-exit-code: Blender exits 0 when the script raises, which for a
    # render harness is the one unforgivable failure mode.
    r = subprocess.run([exe, "-b", "--factory-startup", "--python-exit-code",
                        "1", "-P", str(script), "--", str(job)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return f"blender failed ({r.returncode}):\n{r.stderr[-1500:]}"
    return f"{len(cells)} cells, {len(faces)} faces -> outside_*.png"


# ---------------------------------------------------------------------------
# The seam: what this level is handed, and what it hands on
# ---------------------------------------------------------------------------

def seam(index: int, run: int = 1, blocks: int = 300) -> str:
    """The two handovers, from the design and from a built run.

    A level is not a thing on its own -- it is entered off the level below's
    exit climb and left into the level above's opening beat, and a designer who
    cannot see either end designs a level that reads as a non-sequitur.
    """
    n = len(hp.LEVELS)
    prev, here, nxt = hp.LEVELS[(index - 1) % n], hp.LEVELS[index], \
        hp.LEVELS[(index + 1) % n]
    out = [f"SEAM INTO {here.name}",
           f"  from {(index - 1) % n + 1}. {prev.name}  theme={prev.theme}"
           f"  band={prev.band}  profile={prev.profile}",
           f"    it leaves by a {prev.exit} climb, {prev.rise} blocks up,"
           f"  across a {prev.gap}-block chasm",
           f"    its last beat is {prev.beats[-1][0]!r}"
           f" ({len(prev.beats[-1][1])} landings);"
           f" its filler is {[b[0] for b in prev.filler]}",
           f"    its footing on the climb is {prev.skin.get('step')}",
           "",
           f"  YOU are {index + 1}. {here.name}  theme={here.theme}"
           f"  band={here.band}  profile={here.profile}"
           f"  shelf={here.shelf}  breaks={here.breaks}",
           f"    you open on beat {here.beats[0][0]!r}"
           f" and leave by a {here.exit} climb {here.rise} blocks up",
           "",
           f"SEAM OUT OF {here.name}",
           f"  into {(index + 1) % n + 1}. {nxt.name}  theme={nxt.theme}"
           f"  band={nxt.band}  profile={nxt.profile}",
           f"    it opens on beat {nxt.beats[0][0]!r}"
           f" with {len(nxt.beats[0][1])} landings, first one"
           f" {nxt.beats[0][1][0]}",
           ""]
    cone, course, seen, starts = grow(run, blocks)
    names = [b["theme"] for b in seen]
    out.append(f"AS BUILT (run {run}) -- the last landing before the seam and"
               " the first after it.")
    out.append("  (the run opens on your level, so only the seam *out* is"
               " built here; for the one in, run --seam on the level before.)")
    for i in range(1, len(seen)):
        if names[i] == names[i - 1]:
            continue
        if here.name not in (names[i], names[i - 1]):
            continue
        a, b = seen[i - 1], seen[i]
        out.append(f"  {names[i - 1]} -> {names[i]}")
        for tag, blk in (("last ", a), ("first", b)):
            out.append(f"    {tag} beat={blk['segment']:10s}"
                       f" cell=({blk['x']},{blk['y']},{blk['z']})"
                       f" form={blk['form']:8s} style={blk['style']:12s}"
                       f" move={blk['move'].kind if blk['move'] else '-':6s}"
                       f" as-authored={blk['exact']}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------

def shoot(index: int, seed: int, frames: int, every: int, out: Path) -> str:
    """The game camera, in a subprocess -- the pin is per-process."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools/level_shot.py"),
         "--level", str(index + 1), "--seed", str(seed), "--frames",
         str(frames), "--every", str(every), "--sheet", "--out",
         str(out / "frames")],
        capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return f"level_shot failed:\n{r.stderr[-1200:]}"
    return f"{len(list((out / 'frames').glob('*.png')))} frames -> frames.png"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--level", required=True,
                    help="level number (1-based) or name substring")
    ap.add_argument("--seed", type=int, default=3, help="which run to render")
    ap.add_argument("--runs", type=int, default=8, help="runs to measure over")
    ap.add_argument("--blocks", type=int, default=300)
    ap.add_argument("--frames", type=int, default=1000,
                    help="a level is ~600 frames; the default runs into the next")
    ap.add_argument("--every", type=int, default=16)
    ap.add_argument("--seconds", type=float, default=20.0,
                    help="motion probe budget")
    ap.add_argument("--out", default=None)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--blueprint", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--outside", action="store_true", help="Blender, 3 views")
    ap.add_argument("--seam", action="store_true")
    ap.add_argument("--no-motion", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="report + blueprint + sheet + seam (not --outside)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--walk-json", action="store_true",
                    help="internal: the unpinned walk, as one JSON line")
    args = ap.parse_args()

    if args.list:
        for i, lv in enumerate(hp.LEVELS, 1):
            print(f"{i:2d}  {lv.name:16s} {lv.theme:10s} "
                  f"{lv.profile:8s} band={lv.band:<5} rise={lv.rise} "
                  f"exit={lv.exit:6s} {lv.landmark}")
        return 0

    index = resolve(args.level)
    if args.walk_json:              # no pin: see walk()'s docstring
        print(json.dumps(walk(hp.LEVELS[index].name, args.runs, args.blocks)))
        return 0
    slug = hp.LEVELS[index].name.lower().replace(" ", "_").replace("the_", "")
    out = Path(args.out or ROOT / "shots/review" / f"l{index + 1:02d}_{slug}")
    out.mkdir(parents=True, exist_ok=True)
    want = {k: getattr(args, k) for k in
            ("report", "blueprint", "sheet", "outside", "seam")}
    if args.all or not any(want.values()):
        want.update(report=True, blueprint=True, sheet=True, seam=True)

    pin(index)
    if want["seam"]:
        text = seam(index)
        (out / "seam.txt").write_text(text)
        print(text)
    if want["sheet"]:
        print(shoot(index, args.seed, args.frames, args.every, out))
    if want["outside"]:
        print(outside(index, 1, args.blocks, out))
    if want["blueprint"]:
        blueprint(index, 1, args.blocks, out / "blueprint.png")
        print(f"blueprint -> {out / 'blueprint.png'}")
    if want["report"]:
        text = report(index, args.runs, args.blocks, args.seed, args.seconds,
                      with_motion=not args.no_motion)
        (out / "report.txt").write_text(text)
        print(text)
    print(f"[all artefacts in {out}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
