"""Deterministic, never-repeating seed management.

The guarantee this module provides: *every run looks different, forever, and
any run can be replayed exactly.*

Those two goals fight each other unless you separate "which run is this" from
"how is this run generated":

  * A monotonic ``run`` counter persists to disk and increments on every show.
    Two runs can never share a seed because two runs can never share a counter
    value -- there is no randomness involved in the uniqueness guarantee, so
    there is no birthday-collision to worry about.

  * Every generator (palette, terrain, obstacles, ...) draws from its own
    *substream* derived from the run seed plus a label. Substreams are
    independent: changing how obstacles are generated does not shift the
    palette, so tweaking one system while debugging does not invalidate your
    mental model of another.

Replay is therefore just ``--seed N``: pass a run number and you get that run
back, byte for byte.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import struct
from dataclasses import dataclass
from pathlib import Path

# Bumping this re-rolls every generator without disturbing the run counter.
# Useful when generation logic changes and old seeds would produce stale-looking
# output that no longer matches the current art direction.
# Epoch 2: the raylib/3D-asset rebuild.
GENERATION_EPOCH = 2

_STATE_FILENAME = "state.json"


def state_dir() -> Path:
    """Where the run counter lives. Honours XDG on Linux, APPDATA on Windows."""
    override = os.environ.get("BRAINROT_STATE_DIR")
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return Path(base) / "claude-brainrot"
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return Path(base) / "claude-brainrot"


def _mix(*parts: object) -> int:
    """Hash arbitrary values into a 64-bit seed.

    BLAKE2b rather than :func:`hash` because Python's string hashing is salted
    per-process: the same label would derive a different substream on every
    daemon restart, which would silently break replay.
    """
    payload = "\x1f".join(repr(p) for p in parts).encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()
    return struct.unpack("<Q", digest)[0]


@dataclass(frozen=True)
class Seed:
    """A single run's identity, and the factory for its substreams."""

    run: int
    root: int

    @classmethod
    def for_run(cls, run: int) -> "Seed":
        return cls(run=run, root=_mix("brainrot", GENERATION_EPOCH, run))

    def stream(self, label: str) -> random.Random:
        """An independent RNG for one subsystem.

        Callers should use a stable label (``"palette"``, ``"obstacles"``).
        Distinct labels never share a stream, so consuming a different number
        of values in one system cannot desync another.
        """
        return random.Random(_mix(self.root, label))

    def index(self, label: str, modulus: int) -> int:
        """A stable integer in ``[0, modulus)`` without burning an RNG object.

        Used for run-level choices such as which scene plays.
        """
        if modulus <= 0:
            raise ValueError("modulus must be positive")
        return _mix(self.root, label) % modulus


class RunCounter:
    """Monotonic run counter, persisted so uniqueness survives restarts.

    Failure here must never take the overlay down -- an unreadable or corrupt
    state file degrades to "start counting again", which costs some repeated
    visuals and nothing else.
    """

    def __init__(self, directory: Path | None = None) -> None:
        self.dir = directory or state_dir()
        self.path = self.dir / _STATE_FILENAME
        self._value = self._load()

    def _load(self) -> int:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            value = int(data.get("run", 0))
            return max(value, 0)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    def _persist(self) -> None:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            # Write-then-replace: a crash mid-write leaves the old counter
            # intact rather than a truncated file that reads back as run 0.
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({"run": self._value}), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            pass

    @property
    def value(self) -> int:
        return self._value

    def next(self) -> Seed:
        """Advance the counter and return the seed for the new run."""
        self._value += 1
        self._persist()
        return Seed.for_run(self._value)


def golden_sequence(n: int) -> float:
    """The ``n``-th value of the golden-ratio low-discrepancy sequence.

    Returns a float in ``[0, 1)``. Successive values are spread about as far
    apart as any infinite sequence can manage, which is exactly what hue
    selection wants: uniform random hues cluster, so consecutive runs would
    sometimes come out near-identical colours and read as "the same thing
    again". This never does that.
    """
    return (n * 0.6180339887498949) % 1.0
