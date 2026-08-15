"""If you fall off this level, where do you end up -- and can you cheat?

The acceptance test for the parkour rehash in ``docs/REHASH.md``, and it is the
owner's own criterion turned into a number:

    if you fall, you should theoretically have to go back to the beginning of
    that level to attempt the parkour again. There should not be any point in
    the level where you go down to a ground block and from there can go up
    again.

So the question is *not* "is there void under this jump" -- void is a flavour,
and a jump out over the rim is wanted for its own sake rather than as a rule.
The question is **reachability**: a body that misses a jump, lands wherever it
lands, and then walks (stepping up at most one block, dropping any distance,
never jumping) must not arrive back at the middle of the course it just fell
out of.

Three outcomes for a missed jump, and only one of them is a defect:

* **dead** -- it lands where nothing connects, or in the void. Fine.
* **start** -- it can walk back to the level's *first* landing. Fine, and it is
  what the owner describes: you go back to the beginning and start again.
* **shortcut** -- it can walk back to landing 1 or later. **This is the
  defect.** The fall cost nothing, the climb is optional, and every jump before
  the one it re-enters at was decoration.

Four sections:

**Re-entry.** The criterion above, per level and per missed jump. Target: zero
shortcuts.

**Floor contact.** How many landings of a level rest on the terrace -- a
pedestal built down to the cone's own terrain, or terrain directly beneath the
block. The rehash allows one, or two where the level's idea needs it. Measured
on the tower as it stands: 83.2%, which is the whole complaint.

**The climb.** Whether a level rises monotonically from its floor to its exit,
how far above the terrace each landing stands, and where it drops. The chasm
crossing is the one sanctioned descent (``hop_span(-1)`` reaches further than
a level jump, which is why it descends by design) and is excluded.

**Reported, not gated.** How much air is under a landing. It is the number the
complaint sounds like and it is deliberately *not* the criterion: a landing on
a spur over the sea and a landing on a tower of its own read the same here and
differently above. The other half of the old criterion -- how much of a level a
no-jump walker covers -- stays in ``tools/bypass_probe.py``, and stops being a
target; see ``docs/REHASH.md`` § "What this retires".

    python tools/reentry_probe.py --runs 6 --blocks 260
    python tools/reentry_probe.py --runs 4 --blocks 200 --levels   # per level

Needs no window: ``scenes/handplan`` imports no renderer.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from collections import Counter, deque
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.scenes import handplan as hp
from brainrot.scenes import spiralplan as sp

#: A body steps up one block and survives any drop. Anything more is a jump,
#: which is the thing whose absence is being measured.
STEP_UP = 1
#: How far a walker may drop in one step and still be walking. Deep enough that
#: falling off the level is a *stop* rather than a route.
DROP = 4
#: How far a missed jump falls before the probe calls it the void. The band is
#: seven to thirteen blocks of open air and the drop outboard is the sea.
FALL_MAX = 60
#: Cells one level's flood may visit. A level is eighty to a hundred blocks of
#: arc and a corridor nine wide, so this is an order of magnitude of slack.
BUDGET = 40000
#: Points sampled along a jump to fall from. A miss happens anywhere along the
#: arc, not only at its middle -- and the two ends are excluded because a body
#: standing on either landing has not missed anything.
MISS_SAMPLES = 7
#: Landings kept live while a level is being judged. Placement releases cells
#: behind the body (``Course.advance``), so a level looked at after the fact is
#: walked against a world that has had its own floor taken away -- which reads
#: as a catastrophic pass and is the probe's own doing. Two levels of slack.
KEEP = 96
#: How far behind the frontier a level is judged. Its own exit climb and
#: crossing are laid *after* its last terrace landing, so a level judged the
#: moment the bearing leaves it is judged without its way out.
LAG = 2


# --------------------------------------------------------------------------
# the walker
# --------------------------------------------------------------------------

def stands(course, x: int, y: int, z: int) -> bool:
    """Can a body stand with its feet at ``y`` in this column?"""
    return (course.blocked((x, y - 1, z))
            and not course.blocked((x, y, z))
            and not course.blocked((x, y + 1, z)))


def surface(course, x: int, z: int, y: int) -> int | None:
    """The height a body near ``y`` in this column would stand at."""
    for cy in range(y + STEP_UP, y - DROP - 1, -1):
        if stands(course, x, cy, z):
            return cy
    return None


def fall_to(course, x: int, z: int, y: float):
    """Where a body falling from ``(x, y, z)`` comes to rest, or ``None``.

    ``None`` is the void, and the void is a pass: nothing is recoverable from
    the sea.
    """
    top = math.floor(y)
    for cy in range(top, top - FALL_MAX, -1):
        if stands(course, x, cy, z):
            return (x, cy, z)
    return None


class Union:
    """Union-find over walkable surface cells.

    One flood per level rather than one per missed jump: the answer to "can
    these two spots reach each other" is a component id, and a component map is
    the same work for ten landings as for one.
    """

    def __init__(self) -> None:
        self.up: dict[tuple[int, int, int], tuple[int, int, int]] = {}

    def find(self, c):
        up = self.up
        root = c
        while up.get(root, root) != root:
            root = up[root]
        while up.get(c, c) != c:
            up[c], c = root, up[c]
        return root

    def join(self, a, b) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.up[ra] = rb


def flood(course, lv, seeds, uf: Union) -> None:
    """Walk out from every seed, joining everything one walk can connect."""
    cone = course.cone
    seen = set()
    queue = deque()
    for s in seeds:
        if s is None or s in seen:
            continue
        seen.add(s)
        uf.up.setdefault(s, s)
        queue.append(s)
    steps = 0
    while queue and steps < BUDGET:
        x, y, z = queue.popleft()
        steps += 1
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            ny = surface(course, nx, nz, y)
            if ny is None:
                continue
            cell = (nx, ny, nz)
            uf.up.setdefault(cell, cell)
            uf.join((x, y, z), cell)
            if cell in seen:
                continue
            # Wandering onto another level is not this walk: getting back up
            # from there is that level's exit climb, which is parkour.
            nu = cone.unwrap(nx, nz, ny)
            if not (lv.u0 - 0.02 <= nu <= lv.u1 + 0.02):
                continue
            seen.add(cell)
            queue.append(cell)


# --------------------------------------------------------------------------
# one level
# --------------------------------------------------------------------------

def miss_points(blk: dict):
    """Where along the jump *leaving* ``blk`` a body might miss.

    A move belongs to the block it leaves, not the one it arrives on
    (``Course._commit``: ``prev["move"] = got["move"]``), so the jump that
    arrives at landing ``i`` is stored on landing ``i - 1``.
    """
    move = blk.get("move")
    if move is None:
        return ()
    pts = move.points(MISS_SAMPLES)
    return tuple(pts[1:-1]) if len(pts) > 2 else ()


def judge(course, lv, blocks: list[dict]) -> dict:
    """Every number this probe reports, for one level."""
    cone = course.cone
    out = {
        "level": lv.index, "theme": lv.theme.name, "landings": len(blocks),
        "shortcut": 0, "to_start": 0, "dead": 0, "misses": 0,
        "worst_reentry": -1, "floor_contact": 0, "drops": 0, "drop_total": 0,
        "held": 0,
        "air": [], "lift_first": None, "lift_last": None, "climb": 0,
        "authors": Counter(), "shortcut_at": [],
    }
    if not blocks:
        return out

    # -- floor contact, air, and the climb ---------------------------------
    for i, blk in enumerate(blocks):
        out["authors"][blk.get("author") or blk.get("theme", "?")] += 1
        # Terrain under the landing, either directly or by way of the stack
        # this landing built down to it. ``cone.rock`` and not ``blocked``:
        # what is being asked is whether it reaches the *terrace*, and every
        # course block in the column is the thing the question is about.
        cell = (blk["x"], blk["y"] - 1, blk["z"])
        on_terrain = cone.rock(cell)
        stack = blk.get("pedestal") or ()
        if on_terrain or (stack and any(cone.rock((x, y - 1, z))
                                        for x, y, z in stack)):
            out["floor_contact"] += 1
        # Air under the landing, against the world as it stands.
        gap = FALL_MAX
        for k in range(1, FALL_MAX + 1):
            if course.blocked((blk["x"], blk["y"] - k, blk["z"])):
                gap = k - 1
                break
        out["air"].append(gap)

    surfaces = [course.surface(b) for b in blocks]
    out["lift_first"] = surfaces[0] - lv.y
    out["lift_last"] = surfaces[-1] - lv.y
    out["climb"] = surfaces[-1] - surfaces[0]
    for i in range(1, len(blocks)):
        # The chasm crossing is the one sanctioned descent: dropping a block
        # reaches 4.98 m against a level jump's 4.26, which is why the format
        # crosses downhill by design.
        if blocks[i].get("origin") == "crossing" or blocks[i].get("cross"):
            continue
        fell = surfaces[i - 1] - surfaces[i]
        if fell > 0.01:
            out["drops"] += 1
            out["drop_total"] += fell

    # -- re-entry ----------------------------------------------------------
    stand = []
    for blk in blocks:
        s = surface(course, blk["x"], blk["z"], int(course.surface(blk)))
        stand.append(None if s is None else (blk["x"], s, blk["z"]))
    # The two landings a jump is *between* are not a fall. Early in an arc the
    # body is still over the block it left and late in one it is over the block
    # it is arriving at, so a sample that comes to rest on either of them is a
    # jump that was made, not missed -- and counting it reads as a shortcut on
    # every jump in the tower.
    endpoints = [frozenset(sp.cells_of(b)) for b in blocks]
    falls = []                      # (landing index, resting cell or None)
    held = 0
    for i in range(1, len(blocks)):
        own = endpoints[i - 1] | endpoints[i]
        for px, py, pz in miss_points(blocks[i - 1]):
            rest = fall_to(course, round(px), round(pz), py)
            if rest is not None and (rest[0], rest[1] - 1, rest[2]) in own:
                held += 1
                continue
            falls.append((i, rest))
    out["held"] = held
    uf = Union()
    flood(course, lv, [c for c in stand if c] + [c for _i, c in falls if c],
          uf)

    # A landing's own cell is where the body would be standing had it not
    # missed, so the walk back is judged against the *earlier* landings only.
    roots = {}
    for j, cell in enumerate(stand):
        if cell is not None:
            roots.setdefault(uf.find(cell), []).append(j)
    for i, rest in falls:
        out["misses"] += 1
        if rest is None:
            out["dead"] += 1
            continue
        reach = [j for j in roots.get(uf.find(rest), ()) if j < i]
        if not reach:
            out["dead"] += 1
        elif max(reach) == 0:
            out["to_start"] += 1
        else:
            out["shortcut"] += 1
            out["worst_reentry"] = max(out["worst_reentry"], max(reach))
            out["shortcut_at"].append(i)
    return out


# --------------------------------------------------------------------------
# growing the tower
# --------------------------------------------------------------------------

def run_once(run_i: int, blocks: int):
    """Grow one tower, judging each level while its own cells are still live."""
    cone = hp.Cone(random.Random(run_i * 977 + 13), 0)
    course = hp.Course(random.Random(run_i * 6151 + 29), cone)
    #: ``(ordinal, block)`` in the order the course holds them, which is the
    #: order ``advance`` releases them in -- so "ordinal below the number
    #: retired" is exactly "its cells are gone".
    per: dict[int, list[tuple[int, dict]]] = {}
    ordinal = 0
    for blk in course.blocks:
        per.setdefault(cone.level_index(course.u_of(blk)), []) \
            .append((ordinal, blk))
        ordinal += 1
    retired = 0
    done: list[dict] = []
    judged: set[int] = set()
    for _ in range(blocks):
        blk = course.spawn()
        if blk is None:
            continue
        here = cone.level_index(course.u_of(blk))
        per.setdefault(here, []).append((ordinal, blk))
        ordinal += 1
        if len(course.blocks) > KEEP:
            retired += course.advance(len(course.blocks) - KEEP)
        # A level is judged once the frontier is two levels past it: its exit
        # climb and its crossing are laid after its last terrace landing.
        for idx in sorted(per):
            if idx in judged or idx >= here - LAG:
                continue
            judged.add(idx)
            rows = per[idx]
            if rows and rows[0][0] < retired:
                continue            # part of it was released: not a fair walk
            done.append(judge(course, cone.level(idx),
                              [b for _o, b in rows]))
    return done


def run(runs: int, blocks: int) -> dict:
    levels = []
    for i in range(1, runs + 1):
        levels.extend(run_once(i, blocks))
    levels = [lv for lv in levels if lv["landings"] >= 3]
    n = max(1, len(levels))
    misses = sum(lv["misses"] for lv in levels)
    landings = sum(lv["landings"] for lv in levels)
    air = sorted(a for lv in levels for a in lv["air"])
    contact = [lv["floor_contact"] for lv in levels]
    return {
        "runs": runs, "levels": len(levels), "landings": landings,
        "misses": misses,
        "shortcut": sum(lv["shortcut"] for lv in levels),
        "to_start": sum(lv["to_start"] for lv in levels),
        "dead": sum(lv["dead"] for lv in levels),
        "held": sum(lv["held"] for lv in levels),
        "levels_with_shortcut": sum(1 for lv in levels if lv["shortcut"]),
        "floor_contact": sum(contact),
        "contact_mean": sum(contact) / n,
        "contact_worst": max(contact) if contact else 0,
        "levels_over_two": sum(1 for c in contact if c > 2),
        "drops": sum(lv["drops"] for lv in levels),
        "levels_monotonic": sum(1 for lv in levels if not lv["drops"]),
        "climb_mean": sum(lv["climb"] for lv in levels) / n,
        "lift_last_mean": sum(lv["lift_last"] for lv in levels) / n,
        "air_median": air[len(air) // 2] if air else 0,
        "air_zero": sum(1 for a in air if a <= 0) / max(1, len(air)),
        "per_level": levels,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--blocks", type=int, default=260)
    ap.add_argument("--levels", action="store_true",
                    help="one line per level judged")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    got = run(args.runs, args.blocks)
    if args.json:
        got.pop("per_level", None)
        print(json.dumps(got))
        return 0

    m = max(1, got["misses"])
    print(f"re-entry -- {got['runs']} runs, {got['levels']} levels, "
          f"{got['landings']} landings, {got['misses']} missed jumps")
    print(f"  SHORTCUT   {got['shortcut']:5d}  "
          f"{100 * got['shortcut'] / m:5.1f}%   "
          f"(target 0 -- fell, walked back into the middle of the course)")
    print(f"  to start   {got['to_start']:5d}  "
          f"{100 * got['to_start'] / m:5.1f}%   (fine: back to the beginning)")
    print(f"  dead       {got['dead']:5d}  {100 * got['dead'] / m:5.1f}%   "
          f"(fine: the void, or ground that connects to nothing)")
    print(f"  levels with a shortcut   {got['levels_with_shortcut']} of "
          f"{got['levels']}")
    print("floor contact -- landings standing on the terrace "
          "(target: 1, or 2 where the level's idea needs it)")
    print(f"  mean {got['contact_mean']:.1f} a level, worst "
          f"{got['contact_worst']}, over two on "
          f"{got['levels_over_two']} of {got['levels']} levels")
    print(f"  share of all landings   "
          f"{100 * got['floor_contact'] / max(1, got['landings']):.1f}%")
    print("the climb")
    print(f"  levels that never drop   {got['levels_monotonic']} of "
          f"{got['levels']}   ({got['drops']} drops outside the crossing)")
    print(f"  climbed over a level     {got['climb_mean']:+.1f} blocks, "
          f"ending {got['lift_last_mean']:+.1f} above its own floor")
    print("reported, not gated")
    print(f"  air under a landing      median {got['air_median']} blocks, "
          f"{100 * got['air_zero']:.1f}% sitting on something")

    if args.levels:
        print("\nper level (worst first)")
        rows = sorted(got["per_level"],
                      key=lambda r: (-r["shortcut"], -r["floor_contact"]))
        print(f"  {'lvl':>4} {'place':16} {'land':>4} {'short':>6} "
              f"{'floor':>6} {'drops':>6} {'climb':>6}")
        for r in rows[:40]:
            print(f"  {r['level']:>4} {r['theme'][:16]:16} "
                  f"{r['landings']:>4} {r['shortcut']:>6} "
                  f"{r['floor_contact']:>6} {r['drops']:>6} "
                  f"{r['climb']:>+6.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
