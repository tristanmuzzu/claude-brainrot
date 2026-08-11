"""Rebuild every committed .glb from its Blender script.

One subprocess per script -- bpy can only be imported once per process.

    python assets/build.py            # everything
    python assets/build.py character  # just one
    python assets/build.py --where    # say which Blender would be used

There are two ways to get a working ``bpy``, and this picks whichever is
available:

* the **`bpy` wheel**, imported by the interpreter running this script. It is
  the tidier option and it is not always available: the wheel trails Python
  releases by a good while, and there is none for 3.14, which is what this
  project's venv is.
* a **standalone Blender**, driven as ``blender -b -P script``. The scripts do
  their work at import, so they run unmodified either way, and Blender 5.0.1
  reproduces every committed asset's geometry exactly -- checked by
  ``tests/test_assets.py`` against ``metrics.json`` after every build.

Set ``BRAINROT_BLENDER`` to force a particular binary.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).parent / "src"

#: Where a standalone Blender is looked for, most specific first. The
#: versioned directory is the one `assets/build.py --where` tells you to
#: create, and it is deliberately outside the repo: it is 1.2 GB.
BLENDER_HOMES = (
    Path.home() / ".local/share/blender",
    Path("/opt/blender"),
)


def find_blender() -> Path | None:
    """The standalone Blender to drive, or None if there is not one."""
    override = os.environ.get("BRAINROT_BLENDER")
    if override:
        return Path(override) if Path(override).exists() else None
    on_path = shutil.which("blender")
    if on_path:
        return Path(on_path)
    for home in BLENDER_HOMES:
        # newest version directory first, so 5.0.1 beats 4.2 without anyone
        # having to say so
        for entry in sorted(home.glob("*/blender"), reverse=True):
            if entry.is_file() and os.access(entry, os.X_OK):
                return entry
    return None


def has_bpy() -> bool:
    """Can the interpreter running this script import bpy itself?"""
    probe = subprocess.run([sys.executable, "-c", "import bpy"],
                           capture_output=True)
    return probe.returncode == 0


def command(script: Path, blender: Path | None) -> list[str]:
    """How to run one asset script.

    ``--factory-startup`` so a user's add-ons and preferences cannot change
    what comes out, and ``--python-exit-code`` because **Blender exits 0 when
    the script raises**. Without it a build that failed on every asset reports
    "ok" for every asset, which is the one thing a build script must not do.
    """
    if blender is None:
        return [sys.executable, str(script)]
    return [str(blender), "-b", "--factory-startup",
            "--python-exit-code", "1", "-P", str(script)]


def explain(blender: Path | None, bpy: bool) -> None:
    # flushed, because the asset scripts write to the same inherited stdout
    # from a subprocess and would otherwise appear above this
    if blender is not None:
        print(f"[assets] Blender: {blender}", flush=True)
    elif bpy:
        print(f"[assets] bpy module: {sys.executable}", flush=True)
    else:
        newest = BLENDER_HOMES[0] / "<version>"
        print(
            "[assets] no way to run the asset scripts.\n"
            "  Either install the wheel:   pip install bpy\n"
            "  (no wheel for this Python: "
            f"{sys.version_info.major}.{sys.version_info.minor})\n"
            "  or unpack a standalone Blender so that this exists:\n"
            f"    {newest}/blender\n"
            "    curl -LO https://download.blender.org/release/Blender5.0/"
            "blender-5.0.1-linux-x64.tar.xz\n"
            f"    mkdir -p {BLENDER_HOMES[0]} && tar xf blender-5.0.1-linux-x64"
            f".tar.xz -C {BLENDER_HOMES[0]}\n"
            f"    mv {BLENDER_HOMES[0]}/blender-5.0.1-linux-x64 "
            f"{BLENDER_HOMES[0]}/5.0.1\n"
            "  or point BRAINROT_BLENDER at one you already have.")


def main(argv: list[str]) -> int:
    where_only = "--where" in argv
    wanted = {a for a in argv if not a.startswith("-")}
    blender = find_blender()
    bpy = blender is None and has_bpy()
    explain(blender, bpy)
    if where_only:
        return 0 if (blender is not None or bpy) else 1
    if blender is None and not bpy:
        return 1

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
        result = subprocess.run(command(script, blender))
        took = time.monotonic() - start
        status = "ok" if result.returncode == 0 else "FAILED"
        print(f"[assets] {script.stem}: {status} ({took:.1f}s)", flush=True)
        if result.returncode != 0:
            failures.append(script.stem)
    if failures:
        print(f"[assets] failed: {', '.join(failures)}")
        return 1
    print("[assets] now run: python assets/measure.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
