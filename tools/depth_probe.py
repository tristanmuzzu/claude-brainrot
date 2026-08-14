"""Measure what a translucent draw is hiding.

Every translucent draw in a scene is a suspect, because a blend mode changes
how a fragment is *combined* and not whether it is recorded: an additive glow
or a faded cloud shelf still stamps its whole quad into the depth buffer, and
everything drawn afterwards and further away is then rejected. The visible
symptom is geometry that is simply missing, which is indistinguishable from a
generation bug until somebody measures it.

Two instruments, because one question has two shapes.

**depth** -- render the frame twice, the second time with that one draw's depth
*writing* turned off, and count the pixels that change. Nothing else moves: the
same sprites are drawn in the same order with the same blending, and the depth
*test* is untouched. A pixel can therefore only differ if its visibility was
decided by the suspect's depth write, which is exactly the question. Zero
changed pixels is proof the draw hides nothing.

**reveal** -- render once normally and once with the draw removed entirely, and
count the pixels that get *brighter*. Removing an additive draw can only take
light away, so a pixel that gains light is one the sprite was hiding. This is
the weaker instrument -- it cannot separate "was occluding" from "was darker
than what is behind it" -- and it is used only where the depth instrument does
not apply, i.e. for opaque geometry that has to write depth and is merely being
drawn at reduced alpha.

    python tools/depth_probe.py                 # every suspect, four seeds
    python tools/depth_probe.py --only glows
    python tools/depth_probe.py --legacy        # the pre-fix draw order
    python tools/depth_probe.py --dump shots/   # write the compared frames out
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.config import Config
from brainrot.engine import fx, rl, textures
from brainrot.engine import scene as scene_api
from brainrot.engine.window import HeadlessWindow
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed
from brainrot.scenes import parkour as pk
from brainrot.scenes import spiral as sr

W, H = 420, 760
DT = 1.0 / 60.0
#: Which scene is under the knife. Rebound by ``--scene``.
SCENE = "parkour"
#: A pixel has to change by this much light before it counts. Below it the two
#: renders differ by rasteriser dither on a gradient rather than by occlusion.
THRESHOLD = 6
_window = None


def ensure_window():
    global _window
    if _window is None:
        cfg = Config()
        cfg.width, cfg.height = W, H
        _window = HeadlessWindow()
        _window.create(cfg)
    return _window


@contextlib.contextmanager
def stubbed(obj, name: str, value):
    """Replace an attribute for the duration of one render."""
    missing = object()
    old = getattr(obj, name, missing)
    setattr(obj, name, value)
    try:
        yield
    finally:
        if old is missing:
            delattr(obj, name)
        else:
            setattr(obj, name, old)


def nothing(*a, **k) -> None:
    return None


def without_depth(obj, name: str):
    """Run one draw with depth writing off, changing nothing else."""
    inner = getattr(obj, name)

    def wrapper(*a, **k):
        with fx.no_depth_write():
            return inner(*a, **k)

    return stubbed(obj, name, wrapper)


#: name -> (instrument, how to perturb the draw). One entry, one suspect, and
#: the perturbation touches that draw and nothing else.
PARKOUR_SUSPECTS = {
    # Lanterns, gate lamps, orbs, and whatever is in your hand. Stubbing the
    # per-glow call rather than the pass covers --legacy too, where there is no
    # pass and each glow is drawn where it stands.
    "glows": ("depth", lambda: without_depth(pk.ParkourScene, "_glow")),
    "burst": ("depth", lambda: without_depth(fx.Burst, "draw")),
    "shelves": ("depth", lambda: without_depth(pk.ParkourScene, "_draw_shelves")),
    "reefs": ("depth", lambda: without_depth(pk.ParkourScene, "_draw_reefs")),
    # Islands are solid land and *must* write depth: a tree in front of a mound
    # has to hide the mound, and the depth instrument's variant -- the same
    # geometry with depth writing off -- does not render at all, which is the
    # measurement agreeing. So they are measured by removing them, and the
    # question asked of them is only whether they can reach the course.
    "islands": ("reveal", lambda: stubbed(pk.ParkourScene, "_draw_islands",
                                          nothing)),
    "haze": ("depth", lambda: without_depth(pk.ParkourScene, "_draw_haze")),
    # Blocks fade in as they arrive at the generation horizon. They are opaque
    # geometry that has to write depth, so the depth instrument does not apply
    # -- what is being asked here is whether the faded ones hide each other.
    "arrival": ("reveal", lambda: stubbed(pk.ParkourScene, "_arrival",
                                          lambda self, born: (0.0, 255))),
}

#: The same question asked of the spiral tower, which this tool could not see
#: at all until now: it patched the flat scene's draw methods *by name*, so
#: the two scenes with a whole cone of geometry in front of the lens were the
#: two it had never measured. Every translucent draw in this scene does go
#: through ``fx.no_depth_write`` and ``tests/test_rendering.py`` proves that
#: guard is load-bearing at the ``fx`` level -- what was never measured is how
#: many pixels each individual draw would hide if it were not guarded, which
#: is the only form of the question that names a culprit.
SPIRAL_SUSPECTS = {
    # Orbs, lanterns, landing lights, the tops of water and lava columns.
    # Patched on ``sr`` and not on ``fx``: the scene does
    # ``from ..engine.fx import glow_pass, no_depth_write``, so its module
    # global is a *reference* and rebinding the one in ``fx`` reaches nothing.
    # Both of these read a flat clean zero while patched the other way, which
    # is exactly what a probe that is not connected to anything reads.
    "glows": ("depth", lambda: without_depth(sr, "glow_pass")),
    "burst": ("depth", lambda: without_depth(fx.Burst, "draw")),
    # Every guarded draw in the scene at once -- water, lava, cobweb, glass,
    # the emissives -- by turning the guard itself into a no-op. This is the
    # spiral's answer to ``--legacy``: what the frame would look like if
    # ``fx.no_depth_write`` were not there, measured rather than argued.
    #
    # It is a whole-scene switch and not a per-draw one on purpose. Wrapping
    # ``_draw_furniture`` was tried and measures the wrong thing: that method
    # draws the *opaque* ladders and vines as well, those must write depth,
    # and taking it away lets the tower behind them reappear -- 28,000 px of
    # "the course is hidden" that is the instrument breaking the scene rather
    # than the scene hiding anything.
    "guards": ("depth", lambda: stubbed(sr, "no_depth_write",
                                        contextlib.nullcontext)),
    "clouds": ("depth", lambda: without_depth(sr.SpiralScene, "_draw_clouds")),
    "haze": ("depth", lambda: without_depth(sr.SpiralScene, "_draw_haze")),
    # The tower itself is opaque and must write depth; the question asked of it
    # is only whether the props hung on it can reach the course.
    "props": ("reveal", lambda: stubbed(sr.SpiralScene, "_draw_props",
                                        nothing)),
}


# -- the pre-fix draw order, reconstructed ---------------------------------


def _legacy_glow(self, x, y, z, size, color, alpha) -> None:
    """One glow, drawn the way they were: additive, inline, writing depth."""
    rl.BeginBlendMode(rl.BLEND_ADDITIVE)
    rl.DrawBillboard(self.camera[0], textures.radial_glow(), (x, y, z), size,
                     rl.rgba(color, alpha))
    rl.EndBlendMode()


def _legacy_burst(self, camera) -> None:
    if not self.particles:
        return
    rl.BeginBlendMode(rl.BLEND_ADDITIVE)
    for p in self.particles:
        a = int(255 * min(1.0, p[6] * 2.5))
        rl.DrawBillboard(camera[0], textures.radial_glow(48), (p[0], p[1], p[2]),
                         0.22, (int(p[7]), int(p[8]), int(p[9]), a))
    rl.EndBlendMode()


@contextlib.contextmanager
def legacy():
    """Put the emissive draws back where they were: inline, writing depth.

    So that "before" and "after" are measured by the same instrument in the
    same process, rather than by checking out an older tree and hoping nothing
    else moved. A faithful reconstruction of the code this tool was written to
    indict: each glow issued at the point the geometry loop reaches it, with
    the depth mask left on, and every alpha drawn including zero.
    """
    with stubbed(pk.ParkourScene, "_glow", _legacy_glow), \
            stubbed(pk.ParkourScene, "_draw_glows", nothing), \
            stubbed(fx.Burst, "draw", _legacy_burst):
        yield


# -- measuring -------------------------------------------------------------


def build(run: int, frames: int):
    seed = Seed.for_run(run)
    ctx = scene_api.SceneContext(W, H, generate_palette(seed), seed)
    scene = scene_api.build(SCENE, ctx)
    for _ in range(frames):
        scene.update(DT)
        scene.elapsed += DT
    return scene


def capture(window, scene) -> bytes:
    window.present(scene.draw)
    return bytes(rl.capture_frame())


def changed(base: bytes, other: bytes, brighter_only: bool) -> set[int]:
    """Pixel indices that differ between two renders of the same frame."""
    out = set()
    for i in range(0, len(base), 4):
        gain = ((other[i] - base[i]) + (other[i + 1] - base[i + 1])
                + (other[i + 2] - base[i + 2]))
        if (gain if brighter_only else abs(gain)) > THRESHOLD:
            out.add(i)
    return out


def worst_of(base: bytes, other: bytes, where: set[int]) -> int:
    return max((abs((other[i] - base[i]) + (other[i + 1] - base[i + 1])
                    + (other[i + 2] - base[i + 2])) for i in where), default=0)


#: Everything in the frame that is not the course itself. Stubbing the lot
#: leaves a silhouette of solid course geometry on the cleared background.
PARKOUR_NOT_THE_COURSE = (
    (pk.ParkourScene, "_draw_ocean"), (pk.ParkourScene, "_draw_reefs"),
    (pk.ParkourScene, "_draw_islands"), (pk.ParkourScene, "_draw_shelves"),
    (pk.ParkourScene, "_draw_haze"), (pk.ParkourScene, "_draw_glows"),
    (pk.ParkourScene, "_draw_held"), (pk.ParkourScene, "_draw_crosshair"),
    (pk.ParkourScene, "_draw_hud"), (fx.Burst, "draw"), (fx.Weather, "draw"),
)

#: The spiral's version. ``_draw_tower`` stays: in this scene the building is
#: not scenery a long way below, it is the thing the course is cut into, and a
#: silhouette taken without it is a handful of floating cubes that no draw
#: could plausibly hide. What comes out is everything hung on it or drawn past
#: it.
SPIRAL_NOT_THE_COURSE = (
    (sr.SpiralScene, "_draw_haze"), (sr.SpiralScene, "_draw_clouds"),
    (sr.SpiralScene, "_draw_props"), (sr.SpiralScene, "_draw_orbs"),
    (sr.SpiralScene, "_draw_held"), (sr.SpiralScene, "_draw_crosshair"),
    (sr.SpiralScene, "_draw_hud"), (fx.Burst, "draw"), (fx.Weather, "draw"),
)

#: scene -> (suspects, the stubs that leave a course silhouette).
SCENES = {
    "parkour": (PARKOUR_SUSPECTS, PARKOUR_NOT_THE_COURSE),
    "spiral": (SPIRAL_SUSPECTS, SPIRAL_NOT_THE_COURSE),
    "tower": (SPIRAL_SUSPECTS, SPIRAL_NOT_THE_COURSE),
}
SUSPECTS, _NOT_THE_COURSE = SCENES["parkour"]


def course_pixels(window, scene) -> set[int]:
    """Which pixels of this frame solid course geometry paints.

    Everything else in the scene is scenery a long way below and behind the
    course, so the question that decides whether a translucent draw matters is
    not how many pixels it changes but whether any of them are *these*. A cloud
    shelf mis-tinting another cloud shelf sixty metres down is not what anybody
    is looking at; a lantern deleting the block you are about to land on is.

    Taken as a silhouette against the cleared background rather than as "what
    changes when the course is removed", because the latter counts the glow
    halos too -- and a glow is an additive overlay whose composited value moves
    whenever anything behind it moves, which is not the course being hidden.
    """
    with contextlib.ExitStack() as stack:
        for obj, name in _NOT_THE_COURSE:
            stack.enter_context(stubbed(obj, name, nothing))
        stack.enter_context(stubbed(pk.SkyDome, "draw", nothing))
        only = capture(window, scene)
    return {i for i in range(0, len(only), 4)
            if only[i] + only[i + 1] + only[i + 2] > THRESHOLD}


def png(path: Path, raw: bytes) -> None:
    img = rl.ffi.new("Image *")
    img.data = rl.ffi.from_buffer(bytearray(raw))
    img.width, img.height, img.mipmaps = W, H, 1
    img.format = rl.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8
    rl.ExportImage(img[0], str(path).encode())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, nargs="*", default=[3, 11, 27, 41])
    ap.add_argument("--frames", type=int, nargs="*", default=[90, 300])
    ap.add_argument("--only", type=str, default=None,
                    help="measure one suspect by name")
    ap.add_argument("--dump", type=str, default=None,
                    help="directory to write the compared frames into")
    ap.add_argument("--legacy", action="store_true",
                    help="measure the pre-fix draw order instead")
    ap.add_argument("--scene", choices=tuple(SCENES), default="parkour")
    args = ap.parse_args()
    if args.legacy and args.scene != "parkour":
        ap.error("--legacy reconstructs the flat scene's old draw order only")
    global SCENE, SUSPECTS, _NOT_THE_COURSE
    SCENE = args.scene
    SUSPECTS, _NOT_THE_COURSE = SCENES[args.scene]

    names = [args.only] if args.only else list(SUSPECTS)
    window = ensure_window()
    total = W * H
    dump = Path(args.dump) if args.dump else None
    if dump:
        dump.mkdir(parents=True, exist_ok=True)

    print(f"frame {W}x{H} = {total} px; a pixel counts at {THRESHOLD} of light"
          + ("  [LEGACY draw order]" if args.legacy else ""))
    with legacy() if args.legacy else contextlib.nullcontext():
        # The course mask depends only on the frame, so it is taken once per
        # frame and shared by every suspect measured against it.
        masks: dict[tuple[int, int], set[int]] = {}
        for name in names:
            instrument, perturb = SUSPECTS[name]
            rows = []
            worst_anywhere = worst_on_course = 0
            for run in args.runs:
                for frames in args.frames:
                    scene = build(run, frames)
                    base = capture(window, scene)
                    with perturb():
                        other = capture(window, scene)
                    hit = changed(base, other, brighter_only=instrument == "reveal")
                    key = (run, frames)
                    if key not in masks:
                        masks[key] = course_pixels(window, scene)
                    on_course = hit & masks[key]
                    worst_anywhere = max(worst_anywhere, len(hit))
                    worst_on_course = max(worst_on_course, len(on_course))
                    rows.append(
                        f"run {run} @{frames}f: {len(hit):>6} px "
                        f"({len(hit) / total * 100:5.2f}%) worst "
                        f"{worst_of(base, other, hit):>3}  |  on the course: "
                        f"{len(on_course):>5} px")
                    if dump and hit:
                        png(dump / f"{name}-run{run}-{frames}-as-drawn.png", base)
                        png(dump / f"{name}-run{run}-{frames}-perturbed.png", other)
            if worst_on_course:
                verdict = f"HIDES up to {worst_on_course} px OF THE COURSE"
            elif worst_anywhere:
                verdict = (f"changes up to {worst_anywhere} px of scenery, "
                           "none of the course")
            else:
                verdict = "clean"
            print(f"\n== {name} [{instrument}]: {verdict} ==")
            for row in rows:
                print(f"  {row}")


if __name__ == "__main__":
    main()
