"""Left alone for an hour, does the tower keep climbing, or does it get stuck?

Every other probe in this project measures a *sample*: twelve runs of three
hundred landings, which is four or five minutes of strip each. That is the
right size for asking whether a level is built as designed, and it is the wrong
size for asking the only question a viewer can ask by leaving it running --
**does it ever stop making progress?**

Three failure shapes, and none of them shows up in a short sweep:

* a **stall** -- consecutive landings that go almost nowhere along the
  corridor, which on screen is the body hopping back and forth between two
  blocks a foot apart;
* a **give-back** -- a level climbed and then dropped, which is the owner's
  "it goes up and then jumps all the way back down to the beginning";
* a **wall** -- a level the course cannot leave at all, so it grinds on the
  same terrace forever.

So: one simulated hour per run, every landing checked, and the run reported by
level so a bad level is named rather than averaged away.

    python tools/endurance_probe.py --hours 1 --runs 4
    python tools/endurance_probe.py --hours 3 --runs 1 --levels

No window and no renderer -- the plan modules import neither -- so an hour of
tower costs a couple of minutes.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.scenes import handplan as hp  # noqa: E402
from brainrot.scenes import spiralplan as sp  # noqa: E402

#: Landings a second, measured: the tower runs 2.0-2.3 depending on the move
#: mix. Used only to turn ``--hours`` into a landing count; the *reported*
#: seconds are summed from the moves themselves and are exact.
LANDINGS_PER_SECOND = 2.2

#: How far along the corridor a landing has to carry the body before it counts
#: as going somewhere, in metres. A jump is 2.1 to 5.9 m long, but much of that
#: can be *across* the band rather than along it -- a staircase tread is
#: deliberately mostly a lane change. Under this and two in a row, the body is
#: visibly hopping on the spot.
STALL_ARC = 0.6

#: ...and how many in a row before it is reported. Two is a pair of blocks a
#: foot apart, which is what the owner saw on THE VAULT.
STALL_RUN = 2

#: How much height a level may take back after climbing, before it is a
#: give-back rather than a designed drop. THE VAULT's showpiece is a three
#: block fall onto a magma pad, so three is legal by design and four is not.
GIVE_BACK = 4.0


def grow(plan, run: int, landings: int):
    cone = plan.Cone(random.Random(run * 977 + 13), 0)
    course = plan.Course(random.Random(run * 6151 + 29), cone)
    seen = list(course.blocks)
    for _ in range(landings):
        seen.append(course.spawn())
        if len(course.blocks) > sp.AHEAD:
            course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
    return cone, course, seen


def walk(cone, course, seen):
    """One run, landing by landing. Returns the findings and the per-level rows."""
    out = {
        "landings": len(seen), "seconds": 0.0, "climb": 0.0,
        "stalls": [], "give_backs": [], "back": 0, "visits": 0,
        "adrift": 0, "arcs": [],
        "levels": Counter(), "per_level": defaultdict(lambda: {
            "visits": 0, "landings": 0, "stalls": 0, "give_backs": 0,
            "seconds": 0.0, "worst_give": 0.0, "min_arc": 99.0}),
    }
    prev_u = prev_xz = None
    #: ``[crossings so far, the level the run started on]``.
    seq = [0, cone.level_index(course.u_of(seen[0]))]
    run_stall = 0
    cur_idx = None
    cur = None
    out["adrift"] = 0

    def close(group, idx):
        if group is None or idx is None:
            return
        lv = cone.level(idx)
        row = out["per_level"][lv.theme.name]
        row["visits"] += 1
        row["landings"] += group["n"]
        row["seconds"] += group["s"]
        out["visits"] += 1
        # The give-back: climbed at least three and then lost at least
        # ``GIVE_BACK`` of it inside the same level visit.
        if group["gain"] >= 3.0 and group["worst"] >= GIVE_BACK:
            row["give_backs"] += 1
            row["worst_give"] = max(row["worst_give"], group["worst"])
            out["give_backs"].append((lv.theme.name, group["start"],
                                      group["peak"], group["worst"],
                                      group["n"]))

    for blk in seen:
        u = course.u_of(blk)
        here = cone.level_index(u)
        # **Bucketed by the level whose plan emitted the landing, not by where
        # the landing physically is.** A landing laid out over the chasm sits
        # at a bearing that belongs to the *next* level, at a height below that
        # level's floor -- so ``unwrap``, which answers "the last turn at or
        # below this height", correctly names a level a revolution down, and
        # the position tells you nothing. Bucketed that way, an hour of tower
        # read 169 visits to THE CRUCIBLE against 18 to everything else, which
        # looks exactly like the loop this probe is for and is the probe's own
        # doing. ``author`` is not ambiguous.
        idx = blk.get("author", here)
        if idx < 0:
            idx = here
        if idx != here:
            out["adrift"] += 1
        # ...and a *visit* is segmented by the crossing, which is the one
        # landing per genuine level transition and the only unambiguous mark
        # there is. ``author`` is set from the frontier's own position, so it
        # flickers over a chasm exactly as ``unwrap`` does: bucketed by it, an
        # hour of tower read 119 visits to THE CRUCIBLE against 16 to
        # everything else, which is the same artefact one layer along. Counted
        # by crossings the same run reads 126 transitions with a median rise of
        # six blocks, which is the tower working.
        crossed = blk.get("origin") == "crossing"
        # ...and labelled by **how many crossings have happened**, which is
        # the only label on this course that is not derived from a position.
        #
        # Four things were tried before this and three of them produced a
        # false alarm that looked exactly like a loop -- one level reported
        # six times more often than every other. ``unwrap`` names a level a
        # revolution down for any landing out over the chasm; ``author`` is
        # set from the frontier's position and inherits it; ``to_level`` is
        # ``from_level + 1`` and ``from_level`` was read the same way. A
        # crossing advances exactly one level, so counting them cannot be
        # ambiguous. If the run's *first* landing is one of the 4% whose
        # position lies, every name in the table is rotated by a constant --
        # which leaves the distribution, and therefore the finding, intact.
        if crossed:
            seq[0] += 1
        idx = seq[1] + seq[0]
        lv = cone.level(idx)
        surf = course.surface(blk)
        move = blk.get("move")
        if move is not None:
            out["seconds"] += move.dur
        if crossed or cur is None:
            close(cur, cur_idx)
            cur_idx = idx
            cur = {"n": 0, "s": 0.0, "start": surf, "peak": surf,
                   "worst": 0.0, "gain": 0.0}
            out["levels"][lv.theme.name] += 1
        cur["n"] += 1
        cur["s"] += move.dur if move is not None else 0.0
        cur["peak"] = max(cur["peak"], surf)
        cur["gain"] = cur["peak"] - cur["start"]
        cur["worst"] = max(cur["worst"], cur["peak"] - surf)
        r = max(6.0, math.hypot(blk["x"], blk["z"]))
        if prev_u is not None:
            arc = (u - prev_u) * r
            if -20.0 < arc < 20.0:
                # Sane ones only: a landing over the chasm unwraps to a level
                # a revolution down and reports a few hundred metres either
                # way, which is the ``adrift`` line and not a distance.
                out["arcs"].append(arc)
            row = out["per_level"][lv.theme.name]
            row["min_arc"] = min(row["min_arc"], arc)
            if arc < 0.0:
                out["back"] += 1
            if arc < STALL_ARC:
                run_stall += 1
                if run_stall == STALL_RUN:
                    row["stalls"] += 1
                    out["stalls"].append(
                        (lv.theme.name, blk.get("segment", ""),
                         str(blk.get("origin")), (blk["x"], blk["y"],
                                                  blk["z"]), round(arc, 2)))
            else:
                run_stall = 0
        prev_u, prev_xz = u, (blk["x"], blk["z"])
    close(cur, cur_idx)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", default="tower", choices=("tower", "spiral"))
    ap.add_argument("--hours", type=float, default=1.0)
    ap.add_argument("--runs", type=int, default=4)
    ap.add_argument("--levels", action="store_true",
                    help="print the per-level table")
    ap.add_argument("--show", default="",
                    help="print every stall and give-back on this level")
    args = ap.parse_args()

    plan = hp if args.plan == "tower" else sp
    n = int(args.hours * 3600 * LANDINGS_PER_SECOND)
    totals = {"landings": 0, "seconds": 0.0, "stalls": 0, "give_backs": 0,
              "back": 0, "visits": 0, "stuck": 0, "climb": 0.0, "adrift": 0,
              "levels_seen": Counter()}
    arcs: list = []
    per_level: dict = defaultdict(lambda: {
        "visits": 0, "landings": 0, "stalls": 0, "give_backs": 0,
        "seconds": 0.0, "worst_give": 0.0, "min_arc": 99.0})
    shown: list = []
    for run in range(args.runs):
        cone, course, seen = grow(plan, run, n)
        got = walk(cone, course, seen)
        totals["landings"] += got["landings"]
        totals["seconds"] += got["seconds"]
        totals["back"] += got["back"]
        totals["adrift"] += got["adrift"]
        arcs += got["arcs"]
        totals["visits"] += got["visits"]
        totals["stuck"] += course.stuck
        totals["climb"] += course.surface(seen[-1]) - course.surface(seen[0])
        totals["levels_seen"].update(got["levels"])
        for name, row in got["per_level"].items():
            dst = per_level[name]
            for k in ("visits", "landings", "stalls", "give_backs"):
                dst[k] += row[k]
            dst["seconds"] += row["seconds"]
            dst["worst_give"] = max(dst["worst_give"], row["worst_give"])
            dst["min_arc"] = min(dst["min_arc"], row["min_arc"])
        totals["stalls"] += sum(r["stalls"] for r in got["per_level"].values())
        totals["give_backs"] += sum(r["give_backs"]
                                    for r in got["per_level"].values())
        if args.show:
            shown += [s for s in got["stalls"]
                      if args.show.lower() in s[0].lower()]
            shown += [g for g in got["give_backs"]
                      if args.show.lower() in g[0].lower()]

    hours = totals["seconds"] / 3600.0
    print(f"ENDURANCE -- {args.plan}, {args.runs} runs x "
          f"{args.hours:.1f} h asked, {hours:.2f} h simulated")
    print(f"  landings                    {totals['landings']}")
    print(f"  level visits                {totals['visits']}  "
          f"({totals['seconds'] / max(1, totals['visits']):.1f} s each)")
    print(f"  distinct levels seen        {len(totals['levels_seen'])} of "
          f"{len(hp.LEVELS) if args.plan == 'tower' else '?'}")
    print(f"  climbed                     {totals['climb']:.0f} blocks "
          f"({3600 * totals['climb'] / max(1.0, totals['seconds']):.0f} an hour)")
    print()
    print("  THE THREE WAYS IT COULD STOP")
    print(f"    stalls (>={STALL_RUN} landings under {STALL_ARC} m of arc)   "
          f"{totals['stalls']}"
          f"   {totals['stalls'] / max(1, totals['visits']):.3f} a visit")
    print(f"    give-backs (climbed 3+, lost {GIVE_BACK:.0f}+)             "
          f"{totals['give_backs']}"
          f"   {totals['give_backs'] / max(1, totals['visits']):.3f} a visit")
    print(f"    landings that went backwards along the corridor  "
          f"{totals['back']}")
    print(f"    unchecked emergency placements                   "
          f"{totals['stuck']}  "
          f"({100 * totals['stuck'] / max(1, totals['landings']):.2f}%)")
    arcs.sort()
    if arcs:
        def pc(f):
            return arcs[min(len(arcs) - 1, int(len(arcs) * f))]
        print(f"\n  HOW FAR A LANDING CARRIES THE BODY ALONG THE CORRIDOR")
        print(f"    min {arcs[0]:.2f}   1% {pc(0.01):.2f}   5% {pc(0.05):.2f}"
              f"   median {pc(0.5):.2f}   95% {pc(0.95):.2f}   max {arcs[-1]:.2f} m")
        for edge in (0.3, 0.6, 1.0, 1.5):
            k = sum(1 for a in arcs if a < edge)
            print(f"    under {edge:.1f} m   {k:>6}  ({100 * k / len(arcs):.2f}%)")
    print(f"\n  reported, not gated")
    print(f"    landings whose position names a different level than their"
          f" plan does   {totals['adrift']}"
          f"  ({100 * totals['adrift'] / max(1, totals['landings']):.2f}%)")

    if args.levels:
        print()
        print(f"  {'level':<18} {'visits':>6} {'land':>6} {'s/visit':>8} "
              f"{'stalls':>7} {'giveback':>9} {'worst':>6} {'min arc':>8}")
        for name in sorted(per_level,
                           key=lambda k: (-per_level[k]["stalls"],
                                          -per_level[k]["give_backs"])):
            row = per_level[name]
            print(f"  {name:<18} {row['visits']:>6} {row['landings']:>6} "
                  f"{row['seconds'] / max(1, row['visits']):>8.1f} "
                  f"{row['stalls']:>7} {row['give_backs']:>9} "
                  f"{row['worst_give']:>6.1f} {row['min_arc']:>8.2f}")
    if shown:
        print(f"\n  {args.show}:")
        for s in shown[:40]:
            print("   ", s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
