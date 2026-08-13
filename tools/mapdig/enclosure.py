"""Is the real corridor a shelf with one wall, or a canyon with two?

``docs/RESEARCH.md`` §4 asked whether there was *a* wall within 4 m **on at
least one side** and answered 71%. That question cannot distinguish the two
buildings it might be, and they are completely different places to stand in:

* a **shelf** cut into the outside of a tower -- rock inboard, open drop and
  open sky outboard, which is what this project builds; or
* a **canyon** cut into a mountain -- rock inboard *and* outboard, the two
  closing overhead into a slot of sky, which is what a contact sheet of the
  real map looks like.

Watching the footage says canyon and the one-sided number cannot contradict
it, so this asks the two-sided question directly against the world save.

At every metre along the checkpoint spine it stands a body on the floor and
casts four rays from head height: inward (toward the tower axis), outward
(away from it), and up. What comes back is the share of the route that has
rock on both sides, on one, and on neither.

Needs the save unpacked. Point ``--save`` at the directory holding
``dimensions/minecraft/overworld/region``; ``docs/reference/README.md`` says
where the zip lives and what it is.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import anvil

HERE = os.path.dirname(os.path.abspath(__file__))
PLATES = os.path.join(HERE, "..", "..", "docs", "reference", "data",
                      "plates.json")

#: Anything a body sees through or walks past. Deliberately *not* the walking
#: classification: a pane of glass is a wall for the purpose of "am I in a
#: canyon", and a torch is not.
AIRLIKE = {
    "air", "cave_air", "void_air", "light", "structure_void", "barrier",
    "torch", "wall_torch", "soul_torch", "soul_wall_torch", "redstone_torch",
    "lever", "rail", "powered_rail", "detector_rail", "activator_rail",
    "tripwire", "tripwire_hook", "vine", "cave_vines", "cave_vines_plant",
    "glow_lichen", "sculk_vein", "ladder", "scaffolding", "cobweb",
    "lily_pad", "sugar_cane", "bamboo", "kelp", "kelp_plant", "seagrass",
    "tall_seagrass", "dead_bush", "short_grass", "grass", "tall_grass",
    "fern", "large_fern", "nether_sprouts", "warped_roots", "crimson_roots",
    "hanging_roots", "twisting_vines", "twisting_vines_plant",
    "weeping_vines", "weeping_vines_plant", "chorus_flower", "sea_pickle",
    "end_rod", "chain", "lantern", "soul_lantern", "flower_pot",
    "redstone_wire", "repeater", "comparator", "string", "snow",
    "moss_carpet", "snow_layer", "sculk_shrieker", "water", "lava",
    "bubble_column", "flowing_water", "flowing_lava",
}

#: How far a ray looks before giving up, in blocks.
SIDE_REACH = 14
UP_REACH = 40

#: "Close" for the purpose of the headline number. Four is what RESEARCH used
#: for its one-sided question, so the two-sided one is asked at the same
#: distance and the rows can be read against each other.
CLOSE = 4


def load(save: str, bound: int, y0: int, y1: int) -> set:
    """Every non-airlike cell in the tower's bounding box, as a set."""
    region = os.path.join(save, "dimensions", "minecraft", "overworld",
                          "region")
    if not os.path.isdir(region):
        region = os.path.join(save, "region")
    solid = set()
    files = sorted(glob.glob(os.path.join(region, "*.mca")))
    if not files:
        raise SystemExit(f"no region files under {region}")
    for path in files:
        rx, rz = (int(p) for p in os.path.basename(path).split(".")[1:3])
        if abs(rx * 512) > bound + 512 or abs(rz * 512) > bound + 512:
            continue
        reg = anvil.Region.from_file(path)
        for cx in range(32):
            for cz in range(32):
                wx, wz = (rx * 32 + cx) * 16, (rz * 32 + cz) * 16
                if wx > bound or wx + 15 < -bound or wz > bound \
                        or wz + 15 < -bound:
                    continue
                try:
                    chunk = anvil.Chunk.from_region(reg, cx, cz)
                except Exception:
                    continue
                for y in range(y0, y1):
                    for dx in range(16):
                        for dz in range(16):
                            x, z = wx + dx, wz + dz
                            if abs(x) > bound or abs(z) > bound:
                                continue
                            try:
                                b = chunk.get_block(dx, y, dz)
                            except Exception:
                                continue
                            if b is not None and b.id not in AIRLIKE:
                                solid.add((x, y, z))
        print(f"  {os.path.basename(path)}: {len(solid)} solid so far",
              file=sys.stderr)
    return solid


def spine(plates, step: float = 1.0):
    """A helical polyline through the checkpoints, sampled about every metre.

    Interpolated in polar coordinates and taking the short way round, because
    the route is a helix and a straight line between two checkpoints a third
    of a revolution apart cuts straight through the tower.
    """
    out = []
    for (x0, y0, z0), (x1, y1, z1) in zip(plates, plates[1:]):
        r0, r1 = math.hypot(x0, z0), math.hypot(x1, z1)
        a0, a1 = math.atan2(z0, x0), math.atan2(z1, x1)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        arc = abs(da) * (r0 + r1) / 2
        n = max(2, int(arc / step))
        for i in range(n):
            t = i / n
            r, a = r0 + (r1 - r0) * t, a0 + da * t
            out.append((r * math.cos(a), y0 + (y1 - y0) * t, r * math.sin(a),
                        a))
    return out


def ray(solid, x, y, z, dx, dz, reach):
    """Distance to the first solid cell along a horizontal direction."""
    for d in range(1, reach + 1):
        cx, cz = int(math.floor(x + dx * d)), int(math.floor(z + dz * d))
        if any((cx, int(y) + h, cz) in solid for h in (0, 1)):
            return d
    return reach + 1


def measure(solid, samples):
    rows = []
    for x, y, z, a in samples:
        # Stand on the floor: the plate's y is the plate itself, so the body's
        # feet are on it and its head is a block and a half up.
        head = y + 1
        inward = ray(solid, x, head, z, -math.cos(a), -math.sin(a), SIDE_REACH)
        outward = ray(solid, x, head, z, math.cos(a), math.sin(a), SIDE_REACH)
        up = UP_REACH + 1
        for d in range(2, UP_REACH + 1):
            if (int(math.floor(x)), int(y) + d, int(math.floor(z))) in solid:
                up = d
                break
        rows.append((inward, outward, up))
    return rows


def report(rows, label: str):
    n = len(rows)
    both = sum(1 for i, o, _ in rows if i <= CLOSE and o <= CLOSE)
    one = sum(1 for i, o, _ in rows
              if (i <= CLOSE) != (o <= CLOSE))
    inward_only = sum(1 for i, o, _ in rows if i <= CLOSE and o > CLOSE)
    outward_only = sum(1 for i, o, _ in rows if o <= CLOSE and i > CLOSE)
    neither = n - both - one
    either = both + one
    lid = sum(1 for _, _, u in rows if u <= UP_REACH)
    slot = sum(1 for i, o, u in rows
               if i <= CLOSE and o <= CLOSE and u <= 12)
    ups = sorted(u for _, _, u in rows if u <= UP_REACH)
    print(f"\n{label}  ({n} samples along the route)")
    print(f"  rock within {CLOSE} m on BOTH sides   {100 * both / n:5.1f}%")
    print(f"  ...on one side only                {100 * one / n:5.1f}%"
          f"   (inward {100 * inward_only / n:.0f}%, "
          f"outward {100 * outward_only / n:.0f}%)")
    print(f"  ...on neither                      {100 * neither / n:5.1f}%")
    print(f"  rock within {CLOSE} m on either      "
          f"{100 * either / n:5.1f}%   (RESEARCH read 71% for the real map)")
    print(f"  a lid within {UP_REACH}                 "
          f"{100 * lid / n:5.1f}%   median "
          f"{ups[len(ups) // 2] if ups else 0} blocks up")
    print(f"  a canyon: both sides and a lid <=12{100 * slot / n:5.1f}%")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--save", required=True,
                    help="unpacked world directory")
    ap.add_argument("--bound", type=int, default=70)
    ap.add_argument("--y0", type=int, default=45)
    ap.add_argument("--y1", type=int, default=240)
    args = ap.parse_args()

    plates = json.load(open(os.path.normpath(PLATES)))
    print(f"loading the save (|x|,|z| <= {args.bound}, "
          f"y {args.y0}..{args.y1})", file=sys.stderr)
    solid = load(args.save, args.bound, args.y0, args.y1)
    print(f"{len(solid)} solid cells", file=sys.stderr)
    rows = measure(solid, spine(plates))
    report(rows, "THE REAL PARKOUR SPIRAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
