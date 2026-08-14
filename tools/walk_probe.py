"""Is a *solved* move still legal when it is played?

The generator's contract is that an illegal move is never laid, so nothing is
checked at run time. This asks whether that contract holds, by walking every
committed move against the world as it stands *when the body would reach it*
-- sixteen landings after the move was solved, which is how far ahead
generation runs -- and asking two questions of every sample along the path:

**Is anything solid inside the body?**  The one :mod:`spiral_probe` already
asks, but asked here of the whole path rather than of the frames a run happens
to land on, and bucketed by the leg that was being played.

**Is there ground under the feet, when the leg is one the body is walking?**
Nothing has ever asked this. A ``line`` leg is a straight line from A to B at a
constant speed; ``Course._move_for`` validates a ``walk`` by the distance
between its endpoints and their difference in height and by nothing else, so a
walk whose middle passes over a hole is a body crossing a gap on air.

Arc legs are exempt from the ground question by construction -- being off the
ground is what they are -- as are the vertical ride of a ladder or a bubble
column and a leg across placed cobweb, which is soft.

    python tools/walk_probe.py --plan tower --runs 8 --blocks 240
    python tools/walk_probe.py --plan spiral --runs 8 --blocks 240

No window and no renderer: both plan modules import raylib not at all.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.scenes import parkourkit as pk
from brainrot.scenes import spiralplan as sp

#: How finely a leg is walked. A body moves at 5.6 m/s and a cell is a metre,
#: so a sample every few centimetres of path is needed before a one-cell hole
#: is guaranteed to be stepped in rather than stepped over.
STEP = 0.05

#: Legs the body is on its feet for. Everything else is either a ballistic arc
#: or a ride up something, and neither wants ground under it.
GROUNDED = frozenset(("walk",))


def _cells_under(x: float, y: float, z: float):
    """The cells a body's feet at ``(x, y, z)`` could be standing on.

    Both of the cells it straddles, because half a boot over an edge is still
    standing -- the same generosity :func:`parkourkit.body_cells` applies to
    the other five sides of the box.
    """
    cy = pk.ifloor(y - 0.05)
    x0 = pk.ifloor(x - pk.BODY_HALF_W + 0.5)
    x1 = pk.ifloor(x + pk.BODY_HALF_W + 0.5)
    z0 = pk.ifloor(z - pk.BODY_HALF_W + 0.5)
    z1 = pk.ifloor(z + pk.BODY_HALF_W + 0.5)
    for cx in ((x0,) if x0 == x1 else (x0, x1)):
        for cz in ((z0,) if z0 == z1 else (z0, z1)):
            yield (cx, cy, cz)


def _own(course, blk: dict) -> set:
    """The cells this landing is, and the cells it stands on.

    The generator's own three exemptions, stated the same way
    :func:`spiral_probe._body_depth` states them so neither can widen alone:
    the landing being left, the landing being arrived on, and the slab whose
    walking surface is halfway up its own cell.
    """
    out = set(pk.footprint(blk["x"], blk["y"], blk["z"], blk["form"])
              or ((blk["x"], blk["y"], blk["z"]),))
    out |= set(blk.get("pedestal", ()))
    out |= set(blk.get("footing", ()))
    for s in blk.get("soft", ()):
        out.add((blk["x"] + s["dx"], blk["y"] + s["dy"], blk["z"] + s["dz"]))
    return out


def _check_move(course, blk: dict, nxt: dict, out: dict) -> None:
    """Walk one committed move and record what it passes through."""
    move = blk.get("move")
    if move is None:
        return
    own = _own(course, blk) | _own(course, nxt)
    kind = move.kind
    hit = [0.0, ""]
    for leg in move.legs:
        frm, to = leg["frm"], leg["to"]
        span = math.dist(frm, to)
        n = max(2, int(span / STEP) + 1)
        # A line leg the body is on its feet for. A climb's ride and its step
        # off are line legs too, so the leg has to be identified by what the
        # *move* is, not by the leg's own kind.
        grounded = leg["kind"] == "line" and kind in GROUNDED
        run = 0.0            # unsupported ground covered without a break
        worst_run = 0.0
        holes = 0
        was_hole = False
        for i in range(n + 1):
            f = i / n
            x = frm[0] + (to[0] - frm[0]) * f
            z = frm[2] + (to[2] - frm[2]) * f
            if leg["kind"] == "arc":
                t = leg["dur"] * f
                y = frm[1] + leg["vy0"] * t - 0.5 * pk.GRAVITY * t * t
            else:
                y = frm[1] + (to[1] - frm[1]) * f
            floor = pk.ifloor(y + 0.05)
            for cell in pk.body_cells(x, y, z):
                if cell[1] < floor or cell in own:
                    continue
                if course.blocked(cell):
                    out["inside"][kind] += 1
                    out["inside_total"] += 1
                    # How far in, on the axis it is least far in on -- the
                    # honest depth of a penetration rather than the diagonal,
                    # measured the way ``spiral_probe._body_depth`` measures it.
                    dx = min(abs(x - (cell[0] - 0.5)), abs((cell[0] + 0.5) - x))
                    dz = min(abs(z - (cell[2] - 0.5)), abs((cell[2] + 0.5) - z))
                    d = min(dx + pk.BODY_HALF_W, dz + pk.BODY_HALF_W, 1.0)
                    if d > hit[0]:
                        hit[0] = d
                        hit[1] = course.struct.get(cell, "cone")
                    break
            if not grounded:
                continue
            out["ground_samples"] += 1
            if any(course.blocked(c) or c in own
                   for c in _cells_under(x, y, z)):
                was_hole = False
                run = 0.0
                continue
            out["airwalk"] += 1
            run += span / n
            worst_run = max(worst_run, run)
            if not was_hole:
                holes += 1
                was_hole = True
        if grounded and holes:
            out["legs_bad"] += 1
            out["worst_gap"] = max(out["worst_gap"], worst_run)
            out["gaps"].append(worst_run)
        if grounded:
            out["legs"] += 1
    if hit[0]:
        out["moves_inside"] += 1
        out["through"][hit[1]] += 1
        if hit[0] > out["worst_depth"]:
            out["worst_depth"] = hit[0]
            out["worst_what"] = f"{hit[1]} on a {kind}"


def sweep(runs: int, blocks: int) -> dict:
    out = {
        "runs": runs, "blocks": blocks,
        "moves": 0, "legs": 0, "legs_bad": 0,
        "ground_samples": 0, "airwalk": 0,
        "inside": Counter(), "inside_total": 0, "samples": 0,
        "moves_inside": 0, "through": Counter(),
        "worst_depth": 0.0, "worst_what": "",
        "worst_gap": 0.0, "gaps": [], "kinds": Counter(),
    }
    for run in range(runs):
        cone = sp.Cone(random.Random(run * 977 + 13), 0)
        course = sp.Course(random.Random(run * 6151 + 29), cone)
        # A move is checked at the moment its landing becomes the oldest one
        # still live, which is where the body is: generation has run its full
        # ``AHEAD`` past it so everything that was going to be built around
        # that path has been, and ``advance`` has not yet released the block
        # itself. Checking it any later measures a world with the ground
        # already taken out from under it -- which reads as a catastrophic
        # air-walk and is the probe's own doing.
        laid: list[dict] = list(course.blocks)
        nxt = 0
        for _ in range(blocks):
            laid.append(course.spawn())
            if len(course.blocks) > sp.AHEAD:
                course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
            first_live = len(laid) - len(course.blocks)
            while nxt < first_live and nxt + 1 < len(laid):
                a, b = laid[nxt], laid[nxt + 1]
                nxt += 1
                out["moves"] += 1
                if a.get("move") is not None:
                    out["kinds"][a["move"].kind] += 1
                _check_move(course, a, b, out)
    return out


def report(o: dict) -> str:
    gaps = sorted(o["gaps"])
    mean = sum(gaps) / len(gaps) if gaps else 0.0
    pct = (100.0 * o["legs_bad"] / o["legs"]) if o["legs"] else 0.0
    air = (100.0 * o["airwalk"] / o["ground_samples"]
           ) if o["ground_samples"] else 0.0
    lines = [
        f"walk probe -- {o['runs']} runs x {o['blocks']} landings",
        f"  moves checked                    {o['moves']}",
        "  move mix                         "
        + ", ".join(f"{k} {v}" for k, v in o["kinds"].most_common(8)),
        "",
        "  ground under the feet (walk legs only)",
        f"    walk legs                      {o['legs']}",
        f"    legs crossing air              {o['legs_bad']}  ({pct:.1f}%)",
        f"    unsupported path samples       {air:.1f}%",
        f"    worst unsupported stretch      {o['worst_gap']:.2f} m",
        f"    mean unsupported stretch       {mean:.2f} m",
        "",
        "  solid inside the body, along the whole path",
        (f"    moves passing through solid    {o['moves_inside']}"
         f"  ({100.0 * o['moves_inside'] / max(1, o['moves']):.2f}%)"),
        (f"    worst depth                    {o['worst_depth']:.2f} m"
         f"  ({o['worst_what'] or 'none'})"),
        "    what was passed through        "
        + (", ".join(f"{k} {v}" for k, v in o["through"].most_common(8))
           or "none"),
        f"    samples inside                 {o['inside_total']}",
        "    by move                        "
        + (", ".join(f"{k} {v}" for k, v in o["inside"].most_common(8))
           or "none"),
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--blocks", type=int, default=240)
    ap.add_argument("--plan", choices=("spiral", "tower"), default="tower")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.plan == "tower":
        global sp
        from brainrot.scenes import handplan

        sp = handplan
    o = sweep(args.runs, args.blocks)
    if args.json:
        o = dict(o, inside=dict(o["inside"]), kinds=dict(o["kinds"]),
                 through=dict(o["through"]))
        print(json.dumps(o))
    else:
        print(report(o))


if __name__ == "__main__":
    main()
