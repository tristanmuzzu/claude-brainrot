"""Rebuild every committed .glb from its Blender script.

One subprocess per script -- bpy can only be imported once per process.

    python assets/build.py            # everything
    python assets/build.py character  # just one
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).parent / "src"


def main(argv: list[str]) -> int:
    wanted = set(argv)
    scripts = sorted(
        p for p in SRC.glob("*.py")
        if p.stem != "common" and (not wanted or p.stem in wanted)
    )
    if not scripts:
        print(f"nothing to build (available: "
              f"{', '.join(p.stem for p in SRC.glob('*.py') if p.stem != 'common')})")
        return 1
    failures = []
    for script in scripts:
        start = time.monotonic()
        result = subprocess.run([sys.executable, str(script)])
        took = time.monotonic() - start
        status = "ok" if result.returncode == 0 else "FAILED"
        print(f"[assets] {script.stem}: {status} ({took:.1f}s)")
        if result.returncode != 0:
            failures.append(script.stem)
    if failures:
        print(f"[assets] failed: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
