"""What each level's course does vertically, as authored.

The reading tool for the rehash in ``docs/REHASH.md``: for one level or the
whole roster it prints the walking height of every authored landing above its
own terrace, the deck the filler holds, and what the exit still has to climb.
Instant -- it reads the design and builds nothing.

Three numbers matter and they are the whole shape of a level now. **low** is
the lowest landing after the level's first: two or more, or a fall walks back
onto it. **deck** is where the script and the filler leave the body, and it is
what the machinery aims at -- a gated landmark stands on a plinth that tall.
**exit** is ``rise + 1 - deck``, what the way out still has to gain, and a
level that flies high enough has nothing left to climb at all.

    python tools/level_climb.py                   # the roster, one line each
    python tools/level_climb.py "THE GATEHOUSE"   # every landing of one level
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tower_probe import _surface, cruise

from brainrot.scenes import handplan as hp


def height(spec: dict) -> str:
    """How this landing says where it is: absolute, or a step from the last."""
    if spec.get("step_y") is not None:
        return f"step {spec['step_y']:+d}"
    return f"lift {spec.get('lift', 1):<2}"


def line(where: str, k: int, spec: dict, was: float, surf: float) -> str:
    return (f"   {where:12} [{k}] {spec['style']:12} "
            f"arc {spec.get('arc', 3.0):4.1f} {height(spec):8} "
            f"{spec.get('kind', 'hop'):6} -> {surf - 1.0:+.1f} "
            f"({surf - was:+.1f})")


def show(lv) -> None:
    print(f"\n{lv.name}   rise {lv.rise}  exit {lv.exit}  "
          f"profile {lv.profile}  breaks {lv.breaks}  deck +{lv.deck}")
    surf = 1.0
    for label, beats in (("", lv.beats), ("FILLER", lv.filler)):
        if label:
            print(f"   {label}")
        for name, specs in beats:
            for k, spec in enumerate(specs):
                was, surf = surf, _surface(spec, surf)
                print(line(name, k, spec, was, surf))
    print(f"   {'EXIT':12}  from deck {cruise(lv) - 1.0:+.1f}, "
          f"wants {lv.rise + 1 - (cruise(lv) - 1.0):+.1f} more")
    for k, spec in enumerate(lv.exit_beats):
        was, surf = surf, _surface(spec, surf)
        print(line("exit", k, spec, was, surf))


def main() -> int:
    want = " ".join(sys.argv[1:]).strip().upper()
    if want:
        for lv in hp.LEVELS:
            if want in lv.name:
                show(lv)
        return 0
    print(f"{'level':18} {'rise':>4} {'deck':>5} {'exit':>5} {'low':>4} "
          f"{'top':>4}  beats")
    for lv in hp.LEVELS:
        surf, low, top = 1.0, 99.0, 0.0
        for i, (_name, specs) in enumerate(list(lv.beats) + list(lv.filler)):
            for k, spec in enumerate(specs):
                surf = _surface(spec, surf)
                if not (i == 0 and k == 0):
                    low = min(low, surf - 1.0)
                top = max(top, surf - 1.0)
        deck = cruise(lv) - 1.0
        print(f"{lv.name:18} {lv.rise:>4} {deck:>5.1f} "
              f"{lv.rise + 1 - deck:>5.1f} {low:>4.1f} {top:>4.1f}  "
              f"{len(lv.beats)}+{len(lv.filler)}f+{len(lv.exit_beats)}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
