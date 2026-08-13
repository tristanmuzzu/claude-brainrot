"""What the *viewer* sees, measured off pixels, and calibrated against the real map.

Every acceptance number this tower has ever had was computed from the plan:
where landings sit, what the ray fan hits, how much of the design survived
being placed. All of them read green while the strip looked wrong, which is
the failure ``docs/HANDOFF.md`` was written about. The reason is structural --
a ray fan cannot see that the surface it hit is a flat unlit slab, and a
fidelity count cannot see that the frame is the same frame it was four seconds
ago.

So this probe reads the rendered image and nothing else. It runs unchanged
over ``brainrot shoot`` output and over ``docs/reference/frames/`` -- 122
frames of the real Parkour Spiral -- which is the point: **the target values
are the real map's own, not anybody's taste.** Five numbers, each tied to one
thing the owner said while watching the strip:

``dark``      share of the frame darker than 18% luma. "The core face is a
              near-black slab down one edge of most frames."
``dominant``  share held by the single commonest colour, quantised to 24.
              "A wall fills the lens." Also catches a frame that is mostly
              blank sky -- both are one surface owning the picture.
``palette``   how many quantised colours hold at least 1.5% of the frame.
              ``docs/RESEARCH.md`` measured the real map's terraces at a
              median 14 materials with the dominant one at 26%; ours run two
              or three. "Identity comes from the floor."
``detail``    share of pixels on a colour boundary. A featureless slab and a
              face with masonry on it are the same ``dominant`` and different
              here.
``churn``     mean pixel distance between one sampled frame and the next, at
              thumbnail size. "The levels keep going a long time without much
              happening" is this number being low for a long stretch.

Aspect is reconciled by cropping: the strip is 9:16 and the reference footage
is 16:9, so reference frames are centre-cropped to the strip's aspect before
anything is measured. That is not a perfect comparison -- the field of view
differs and cropping cannot fix that -- but it is an honest one, and it is
applied to the reference rather than to us so our own frames are never
touched.

**Corrected 2026-08-13, and the correction is the lesson.** The paragraphs
immediately below compared this tower against ``frames/ps1`` and
``frames/ps3``, and *both of those videos run a shader pack* -- soft shadows,
volumetric light, bloom and a colour grade. Comparing flat baked light against
that measures the shader pack. ``docs/reference/frames/vanilla_2hz/`` is the
control that was missing: 125 frames of the vanilla speedrun at 2.22 fps,
which is the same 0.45 s spacing ``--every 27`` produces, so ``churn`` is
finally comparable too. Against *it*, four rows separate --

    frame-to-frame change   ours  9.8%   vanilla 20.3%   shaders 29.4%
    lopsidedness            ours 41.3%   vanilla 32.6%
    unlit                   ours 28.3%   vanilla 17.3%
    detail overhead         ours  4.5%   vanilla  6.9%

-- and the biggest of them is a **camera** finding: a real player whips the
view constantly and this scene moves like a tram. The rows that still do not
separate (surface dominance, materials on screen, empty ninths, edge detail)
are genuinely level with the real map. Always check what a reference *is*
before concluding from it; the paragraphs below are kept as the record of
getting that wrong.

**What this tool found first, and it is not what it was built to find.**
Measured over 100 frames of the hand-built tower against 122 frames of the
real Parkour Spiral, *every single-frame statistic here says our tower matches
or beats the real map*: less unlit (28% against 38 and 49), no more surface
dominance (35% against 31 and 39), the same materials on screen (8.4 against
10.2 and 8.3), more edge detail (6.3% against 6.0 and 5.1), fewer empty ninths
(24% against 34 and 40) and the same lopsidedness (41% against 39 and 45).
This was run at a moment when the owner had just watched the live strip and
said ninety per cent of the levels were bad, and the contact sheet agreed with
him.

So: **the gap between this tower and the real one is not in any aggregate of
the pixels of one frame.** Not lighting, not palette, not texture, not how
much sky is in shot. Whatever is wrong is arrangement and meaning -- a
recognisable structure, a route you can read, a sense of having climbed -- and
none of that survives being averaged. The lesson ``docs/HANDOFF.md`` drew from
the last pass was that a metric can measure the thing you can build rather
than the thing the viewer sees; the sharper version is that for this
particular gap **there may be no aggregate that closes it**, and the effort
belongs in design and in looking rather than in a better rubric. Use these
numbers as a regression guard -- they will catch a level going dark, blank or
monochrome -- and never as a definition of good.

The one column that does differ is ``churn``, and its comparison is invalid as
printed: reference frames are 15-30 s apart and a shoot samples every 0.45 s.
Within one run of our own it ranks levels roughly the way the eye does (the
two stretches that read as monotonous on the sheet came bottom), so it is
worth something as an internal measure. Making it comparable needs the real
footage resampled to match, which means the videos in
``docs/reference/README.md`` and a download nobody has done yet.

Usage::

    python tools/frame_probe.py --shoot tower --seed 7 --frames 2700
    python tools/frame_probe.py --dir shots/run7
    python tools/frame_probe.py --reference          # the real map
    python tools/frame_probe.py --shoot tower --reference   # side by side
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent

#: Luma below which a pixel counts as unlit. 46/255. Chosen by eye against the
#: contact sheets that started this: the core face reads 20-40, a lit terrace
#: 90-180, the dusk sky 120-200.
DARK = 46

#: Levels per channel in the fixed colour cube. Five gives 125 bins, which is
#: coarse enough that two shades of the same stone merge -- which is what a
#: viewer does -- and fine enough that hay, oak, path and stone do not.
CUBE = 5


def _cube_palette() -> Image.Image:
    """A fixed uniform RGB cube as a PIL palette image."""
    step = 255 / (CUBE - 1)
    table: list[int] = []
    for r in range(CUBE):
        for g in range(CUBE):
            for b in range(CUBE):
                table += [round(r * step), round(g * step), round(b * step)]
    img = Image.new("P", (1, 1))
    img.putpalette(table + [0] * (768 - len(table)))
    return img


_CUBE = _cube_palette()
_CUBE_N = CUBE ** 3

#: A colour must hold this much of the frame to count as a material the viewer
#: registers. Below it you are counting texture noise and antialiasing.
FLOOR = 0.015

#: Gradient magnitude above which a pixel is on a boundary.
EDGE = 28

#: Everything is measured at this width; the height follows the aspect. Big
#: enough that a block face still has its texture, small enough that PIL's C
#: paths do two hundred frames in a few seconds.
WIDE = 180

#: The strip's aspect, and what reference frames are cropped to.
ASPECT = 9 / 16

#: Both sources wear a heads-up display and neither of them is the world. The
#: real footage carries hearts, hunger and a hotbar across the bottom centre --
#: which is exactly where a 9:16 centre crop lands -- and the strip carries its
#: distance, level name and orb count along the top. Trimmed off *both*, by the
#: same fractions, so the comparison is world against world.
TRIM_TOP = 0.08
TRIM_BOTTOM = 0.14


def _prepare(path: Path) -> Image.Image:
    """One frame, cropped to the strip's aspect and scaled to ``WIDE``."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if w / h > ASPECT:
        # Landscape reference footage: take the centre 9:16 of it.
        keep = int(round(h * ASPECT))
        left = (w - keep) // 2
        im = im.crop((left, 0, left + keep, h))
        w, h = im.size
    im = im.crop((0, int(h * TRIM_TOP), w, int(h * (1 - TRIM_BOTTOM))))
    w, h = im.size
    return im.resize((WIDE, max(1, int(round(WIDE * h / w)))), Image.BILINEAR)


def _measure(im: Image.Image) -> dict:
    """The four per-frame numbers. PIL primitives only -- no numpy here."""
    n = im.width * im.height

    luma = im.convert("L")
    hist = luma.histogram()
    dark = sum(hist[:DARK]) / n

    # Quantise before counting colours: a viewer sees "stone, hay, path", not
    # the four hundred shades the baked light actually puts on screen. The bins
    # must be **fixed**, not fitted per frame: an adaptive palette finds its
    # ``BUCKETS`` colours in any picture whatsoever and splits them roughly
    # evenly, so `dominant` reads about 1/BUCKETS and `palette` about BUCKETS
    # for a blank wall and for a market square alike. Measured on the way in --
    # a black cliff and the real map's terraces both came out at 20-23
    # "materials" until this was a uniform cube.
    quant = im.quantize(palette=_CUBE, dither=Image.Dither.NONE)
    counts = sorted((c for c, _ in quant.getcolors(_CUBE_N * 2) or []),
                    reverse=True)
    dominant = counts[0] / n if counts else 1.0
    palette = sum(1 for c in counts if c / n >= FLOOR)

    # FIND_EDGES leaves a one-pixel border of garbage; crop it off rather than
    # let a frame's rim decide its detail score.
    edges = luma.filter(ImageFilter.FIND_EDGES).crop(
        (1, 1, im.width - 1, im.height - 1))
    ehist = edges.histogram()
    detail = sum(ehist[EDGE:]) / max(1, sum(ehist))

    # Where the world *is* in the picture. Single-frame histograms turned out
    # not to separate this tower from the real map at all -- ours is brighter,
    # has more edges and holds the same number of materials -- so what is left
    # is arrangement, and this is arrangement without needing to segment sky
    # from rock. Sky is smooth and world is not, so per-tile edge density is a
    # map of where the mass sits. ``blank`` is how many of the nine tiles are
    # effectively empty; ``lean`` is how lopsided the frame is, which is the
    # signature of a cliff down one edge and a drop down the other.
    tiles = []
    tw, th = im.width / 3, edges.height / 3
    for row in range(3):
        for col in range(3):
            t = edges.crop((int(col * tw), int(row * th),
                            int((col + 1) * tw), int((row + 1) * th)))
            th_hist = t.histogram()
            tiles.append(sum(th_hist[EDGE:]) / max(1, sum(th_hist)))
    blank = sum(1 for t in tiles if t < 0.02) / 9
    left = sum(tiles[i] for i in (0, 3, 6))
    right = sum(tiles[i] for i in (2, 5, 8))
    lean = abs(left - right) / max(1e-6, left + right)
    top = sum(tiles[:3]) / 3

    return {"dark": dark, "dominant": dominant,
            "palette": float(palette), "detail": detail,
            "blank": blank, "lean": lean, "top": top}


def _thumb(im: Image.Image) -> bytes:
    return im.resize((16, 28), Image.BILINEAR).convert("L").tobytes()


def survey(paths: list[Path]) -> dict:
    """Measure a sequence of frames in order. ``churn`` needs the order."""
    rows, thumbs = [], []
    for p in paths:
        im = _prepare(p)
        rows.append(_measure(im))
        thumbs.append(_thumb(im))

    churn = []
    for a, b in zip(thumbs, thumbs[1:]):
        churn.append(sum(abs(x - y) for x, y in zip(a, b)) / len(a) / 255)

    out = {k: sum(r[k] for r in rows) / len(rows) for k in rows[0]} if rows \
        else {}
    out["churn"] = sum(churn) / len(churn) if churn else 0.0
    out["frames"] = float(len(rows))
    # The tail of each distribution is the part the owner notices: one frame in
    # twenty being a black wall is what "the levels are bad" is made of.
    out["dark_p90"] = _pct([r["dark"] for r in rows], 0.90)
    out["dominant_p90"] = _pct([r["dominant"] for r in rows], 0.90)
    out["palette_p10"] = _pct([r["palette"] for r in rows], 0.10)
    out["blank_p90"] = _pct([r["blank"] for r in rows], 0.90)
    out["churn_p10"] = _pct(sorted(churn), 0.10) if churn else 0.0
    return out


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(q * len(s)))]


def frames_in(d: Path) -> list[Path]:
    got = sorted(p for p in d.iterdir()
                 if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if not got:
        raise SystemExit(f"no frames in {d}")
    return got


def shoot(scene: str, seed: int, frames: int, every: int) -> Path:
    """Render a run with the real renderer and hand back its directory."""
    out = Path(tempfile.mkdtemp(prefix=f"frameprobe-{scene}-{seed}-"))
    cmd = [sys.executable, "-m", "brainrot", "shoot", "--scene", scene,
           "--seed", str(seed), "--frames", str(frames), "--every", str(every),
           "--out", str(out)]
    subprocess.run(cmd, cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


#: The two Parkour Spiral walkthroughs. ``speedrun/`` is deliberately not here:
#: ``docs/RESEARCH.md`` records that two of the three videos originally
#: gathered are Parkour *Volcano*, so only the frames whose provenance is
#: certain are allowed to set a target.
REFERENCE = ("ps1", "ps3")


def reference_frames() -> list[Path]:
    base = ROOT / "docs" / "reference" / "frames"
    got: list[Path] = []
    for name in REFERENCE:
        got += frames_in(base / name)
    return got


LABELS = [
    ("dark", "unlit (under 18% luma)", "%", 100),
    ("dark_p90", "  worst tenth of frames", "%", 100),
    ("dominant", "biggest single surface", "%", 100),
    ("dominant_p90", "  worst tenth of frames", "%", 100),
    ("palette", "materials on screen", "", 1),
    ("palette_p10", "  poorest tenth of frames", "", 1),
    ("detail", "pixels on an edge", "%", 100),
    ("blank", "ninths of frame empty", "%", 100),
    ("blank_p90", "  emptiest tenth of frames", "%", 100),
    ("top", "detail in the top third", "%", 100),
    ("lean", "left/right lopsidedness", "%", 100),
    ("churn", "frame-to-frame change", "%", 100),
    ("churn_p10", "  stillest tenth", "%", 100),
]


def report(columns: list[tuple[str, dict]]) -> None:
    width = max(len(lbl) for _, lbl, _, _ in LABELS) + 2
    head = "".join(f"{name:>14}" for name, _ in columns)
    print(f"\n{'':{width}}{head}")
    print("-" * (width + 14 * len(columns)))
    for key, label, unit, scale in LABELS:
        cells = ""
        for _, data in columns:
            v = data.get(key, 0.0) * scale
            cells += f"{v:>13.1f}{unit or ' '}" if unit else f"{v:>13.1f} "
        print(f"{label:{width}}{cells}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__ and __doc__.split("\n")[0])
    ap.add_argument("--dir", type=Path, action="append", default=[],
                    help="a directory of frames; repeatable")
    ap.add_argument("--shoot", metavar="SCENE",
                    help="render this scene first (tower/spiral/parkour)")
    ap.add_argument("--seed", type=int, action="append", default=[],
                    help="seed to render; repeatable, default 7")
    ap.add_argument("--frames", type=int, default=2700)
    ap.add_argument("--every", type=int, default=27)
    ap.add_argument("--reference", action="store_true",
                    help="measure the real map's frames as a column")
    args = ap.parse_args()

    columns: list[tuple[str, dict]] = []

    if args.shoot:
        for seed in (args.seed or [7]):
            d = shoot(args.shoot, seed, args.frames, args.every)
            columns.append((f"{args.shoot}/{seed}", survey(frames_in(d))))
    for d in args.dir:
        columns.append((d.name or str(d), survey(frames_in(d))))
    if args.reference:
        columns.append(("REAL MAP", survey(reference_frames())))

    if not columns:
        ap.error("give --dir, --shoot or --reference")
    report(columns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
