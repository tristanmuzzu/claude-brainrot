"""How far can a walker get along a level without jumping?

The walkability probe in ``spiral_probe`` asks whether the *cone alone* is
climbable and holds it at zero metres: that is the guarantee that levels are
levels. It says nothing about the level you are standing on, because it does
not include a single block the course or the dressing built -- and the owner's
complaint about the last tower was exactly there: you could run nine tenths of
a level in a straight line and only jump if you felt like it.

So this one walks the **built world**: cone, course blocks, pedestals,
terrain, shells, landmarks. From the level's first landing, step one cell at a
time, up one at most, down any survivable drop, never jumping. What comes out
is how much of the level's arc the walker covers before the ground runs out,
and whether any level can be walked end to end.

The real map, measured with the same walker off the map file itself: **mean
46% of a checkpoint leg covered, and not one leg passable end to end.** That
is the target, and it is why the levels carry floor breaks and why the course
crosses them with a lock.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brainrot.scenes import handplan as hp  # noqa: E402
from brainrot.scenes import spiralplan as sp  # noqa: E402

#: A body can step up one block and survive any drop the format ever asks of
#: it; anything more is a jump, which is the thing being measured the absence
#: of. Deep enough that "it fell off the level" is a *stop*, not a route.
STEP_UP = 1
DROP = 4
#: How far a flood may wander before it is called an answer. Levels are eighty
#: to a hundred blocks of arc and a few cells wide.
BUDGET = 26000


def _surface(course, x: int, z: int, y: int) -> int | None:
    """The height a body standing at ``(x, z)`` near ``y`` would stand at."""
    for cy in range(y + STEP_UP, y - DROP - 1, -1):
        if course.blocked((x, cy - 1, z)) and not course.blocked((x, cy, z)) \
                and not course.blocked((x, cy + 1, z)):
            return cy
    return None


def walk_level(course, lv, start) -> tuple[float, bool]:
    """``(fraction of the level's arc covered, reached the far end)``.

    ``start`` is the level's first landing, kept as it was laid: the course
    keeps only the last couple of dozen blocks, so a level looked up after the
    fact has no entry to walk from and every level but the newest reads zero.
    """
    cone = course.cone
    if start is None:
        return 0.0, False
    y0 = int(course.surface(start))
    seed = _surface(course, start["x"], start["z"], y0)
    if seed is None:
        return 0.0, False
    span = lv.u1 - lv.u0
    best = 0.0
    seen = {(start["x"], seed, start["z"])}
    queue = deque(seen)
    steps = 0
    while queue and steps < BUDGET:
        x, y, z = queue.popleft()
        steps += 1
        u = cone.unwrap(x, z, y)
        f = (u - lv.u0) / span
        if 0.0 <= f <= 1.0 and f > best:
            best = f
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            ny = _surface(course, nx, nz, y)
            if ny is None or (nx, ny, nz) in seen:
                continue
            nu = cone.unwrap(nx, nz, ny)
            if not (lv.u0 - 0.02 <= nu <= lv.u1 + 0.02):
                continue        # wandered onto another level: not this walk
            seen.add((nx, ny, nz))
            queue.append((nx, ny, nz))
    return best, best >= 0.995


def run(runs: int, blocks: int) -> dict:
    covers: list[float] = []
    full = 0
    levels = 0
    for run_i in range(1, runs + 1):
        cone = hp.Cone(random.Random(run_i * 977 + 13), 0)
        course = hp.Course(random.Random(run_i * 6151 + 29), cone)
        starts: dict[int, dict] = {}
        for _ in range(blocks):
            blk = course.spawn()
            starts.setdefault(cone.level_index(course.u_of(blk)), blk)
            if len(course.blocks) > hp.AHEAD:
                course.advance(len(course.blocks) - hp.AHEAD + sp.TRAIL)
        here = cone.section_at(course.u).index
        for i in range(1, max(2, here)):
            lv = cone.level(i)
            cover, done = walk_level(course, lv, starts.get(i))
            if cover <= 0.0:
                continue        # the level's landings are already retired
            levels += 1
            covers.append(cover)
            full += done
    covers.sort()
    return {
        "runs": runs, "levels": levels, "full": full,
        "mean": sum(covers) / max(1, len(covers)),
        "worst": covers[-1] if covers else 0.0,
        "median": covers[len(covers) // 2] if covers else 0.0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--blocks", type=int, default=240)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    got = run(args.runs, args.blocks)
    if args.json:
        print(json.dumps(got))
        return
    print(f"walking the built world -- {got['runs']} runs, "
          f"{got['levels']} levels")
    print(f"  covered without a jump   mean {100 * got['mean']:.0f}%, "
          f"median {100 * got['median']:.0f}%, worst {100 * got['worst']:.0f}%")
    print(f"  levels walkable end to end   {got['full']} of {got['levels']}"
          f"   (the real map: 0 of 43, mean 46%)")


if __name__ == "__main__":
    main()
