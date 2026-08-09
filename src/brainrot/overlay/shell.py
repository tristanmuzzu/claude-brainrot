"""What gnome-shell knows and will not tell an ordinary client.

On a Wayland session a client cannot ask which window is in front, where any
window is, or where the pointer is. The overlay needs all three: it appears
only while you are looking at Claude Code, it stands beside that window rather
than on a screen edge, and it can be dragged. ``org.gnome.Shell.Introspect``
exists for the first of them and is refused ("GetWindows is not allowed").

So a small gnome-shell extension answers instead, pushing snapshots to the
daemon's existing UDP port. This module is the receiving half: it keeps the
last snapshot, converts it out of the compositor's coordinate space, and
answers the questions :mod:`brainrot.overlay.linux` asks.

**Two coordinate spaces, and the ratio between them is measured.** The
compositor works in *logical* pixels; the overlay's own window is an X11
window and X11 works in *device* pixels. On a 200% display those differ by a
factor of two, and getting it wrong puts the strip in the right shape at half
the size in the wrong place. Rather than trusting a scale factor from either
side, :meth:`Snapshot.scale_against` divides the X screen width by the logical
desktop width -- two numbers each side can measure directly.

Everything degrades to None rather than raising: a desktop with no extension
installed is a supported configuration (the strip docks to the work area and
stays up for the whole turn), not an error.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

#: Clutter modifier bits, as the extension masks them before sending.
CLUTTER_SHIFT = 1 << 0
CLUTTER_CONTROL = 1 << 2
CLUTTER_ALT = 1 << 3
CLUTTER_SUPER = 1 << 6
CLUTTER_BUTTON1 = 1 << 8

#: Virtual-key codes (:mod:`brainrot.engine.keys` speaks these, because the
#: chords are configured once and mean the same thing on both platforms) to
#: the compositor's modifier bits.
VK_TO_CLUTTER = {
    0x10: CLUTTER_SHIFT,
    0x11: CLUTTER_CONTROL,
    0x12: CLUTTER_ALT,
    0x5B: CLUTTER_SUPER,
}

#: A snapshot older than this describes a desktop that has moved on. The
#: extension heartbeats once a second, so anything past a few seconds means it
#: is not running -- and the overlay must not place itself against a window
#: that may no longer be there.
STALE_AFTER = 3.0


@dataclass(frozen=True)
class ShellWindow:
    id: int
    pid: int
    wm_class: str
    #: Frame rectangle in *logical* pixels: x, y, width, height.
    rect: tuple[int, int, int, int]
    monitor: int = 0
    hidden: bool = False


@dataclass(frozen=True)
class ShellMonitor:
    index: int
    #: Work area in logical pixels: x, y, width, height.
    work: tuple[int, int, int, int]
    scale: float = 1.0
    primary: bool = False


@dataclass(frozen=True)
class Snapshot:
    """One reading of the desktop, as the compositor sees it."""

    focus: int = 0
    windows: tuple[ShellWindow, ...] = ()
    monitors: tuple[ShellMonitor, ...] = ()
    #: Pointer position in logical pixels, and the held modifier mask.
    pointer: tuple[int, int, int] = (0, 0, 0)
    #: Logical size of the whole desktop.
    logical: tuple[int, int] = (0, 0)
    seq: int = 0
    at: float = 0.0

    @classmethod
    def parse(cls, data: dict, now: float | None = None) -> "Snapshot | None":
        """Build one from a datagram, or None if it is not one of ours.

        Every field is defended individually. This arrives over a UDP socket
        that anything on the machine can write to, and while that is not a
        privilege boundary worth defending -- anything that can send here can
        already run code as you -- a malformed packet must cost a dropped
        snapshot rather than the daemon.
        """
        if not isinstance(data, dict) or data.get("kind") != "shell":
            return None
        windows = []
        for raw in data.get("windows") or ():
            if not isinstance(raw, dict):
                continue
            rect = _rect(raw.get("rect"))
            if rect is None:
                continue
            try:
                windows.append(ShellWindow(
                    id=int(raw.get("id") or 0),
                    pid=int(raw.get("pid") or 0),
                    wm_class=str(raw.get("cls") or ""),
                    rect=rect,
                    monitor=int(raw.get("mon") or 0),
                    hidden=bool(raw.get("hidden")),
                ))
            except (TypeError, ValueError):
                continue
        monitors = []
        for raw in data.get("monitors") or ():
            if not isinstance(raw, dict):
                continue
            work = _rect(raw.get("work"))
            if work is None:
                continue
            try:
                monitors.append(ShellMonitor(
                    index=int(raw.get("index") or 0),
                    work=work,
                    scale=float(raw.get("scale") or 1.0),
                    primary=bool(raw.get("primary")),
                ))
            except (TypeError, ValueError):
                continue
        pointer = _rect(data.get("pointer"), length=3) or (0, 0, 0)
        logical = _rect(data.get("logical"), length=2) or (0, 0)
        try:
            focus = int(data.get("focus") or 0)
            seq = int(data.get("seq") or 0)
        except (TypeError, ValueError):
            return None
        return cls(
            focus=focus,
            windows=tuple(windows),
            monitors=tuple(monitors),
            pointer=(pointer[0], pointer[1], pointer[2]),
            logical=(logical[0], logical[1]),
            seq=seq,
            at=time.monotonic() if now is None else now,
        )

    # -- questions --------------------------------------------------------

    def fresh(self, now: float | None = None, max_age: float = STALE_AFTER) -> bool:
        return (time.monotonic() if now is None else now) - self.at < max_age

    def window(self, window_id: int) -> "ShellWindow | None":
        for win in self.windows:
            if win.id == window_id:
                return win
        return None

    def host_for(self, pids) -> int:
        """The window belonging to one of these processes, or 0.

        The hook shim cannot discover a window id -- there is no such thing to
        discover from inside a Wayland client -- so it sends its own ancestry
        instead, and the match is made here. A terminal running Claude Code is
        an ancestor of the hook; so is the desktop app. The *nearest* ancestor
        with a window wins, which is what makes a terminal inside a terminal
        multiplexer resolve to the window you are actually looking at.
        """
        wanted = [int(p) for p in pids if p]
        by_pid = {win.pid: win.id for win in self.windows if win.pid}
        for pid in wanted:                    # ordered nearest-ancestor-first
            if pid in by_pid:
                return by_pid[pid]
        return 0

    def scale_against(self, screen_width: int) -> float:
        """Device pixels per logical pixel, measured rather than assumed.

        The X screen is one number this process can read directly and the
        logical desktop width is one the compositor reports; their ratio is
        the conversion, whatever fractional-scaling settings are in force.
        Falls back to the monitor scale the extension reported, and then to 1.
        """
        if self.logical[0] > 0 and screen_width > 0:
            ratio = screen_width / self.logical[0]
            # Anything outside this is a reading taken mid-resolution-change.
            if 0.5 <= ratio <= 8.0:
                return ratio
        for monitor in self.monitors:
            if monitor.primary and monitor.scale > 0:
                return float(monitor.scale)
        return 1.0

    def monitor_for(self, window_id: int) -> "ShellMonitor | None":
        win = self.window(window_id)
        index = win.monitor if win else None
        for monitor in self.monitors:
            if index is not None and monitor.index == index:
                return monitor
        for monitor in self.monitors:
            if monitor.primary:
                return monitor
        return self.monitors[0] if self.monitors else None


def _rect(value, length: int = 4) -> "tuple[int, ...] | None":
    if not isinstance(value, (list, tuple)) or len(value) < length:
        return None
    try:
        return tuple(int(v) for v in value[:length])
    except (TypeError, ValueError):
        return None


@dataclass
class Bridge:
    """The last thing the extension said, and whether it is still saying it.

    Written from the IPC thread and read from the render thread. Both are
    single attribute assignments of an immutable snapshot under the GIL, so
    there is nothing to lock: a reader either sees the previous snapshot or
    the next one, never half of one.
    """

    snapshot: Snapshot = field(default_factory=Snapshot)
    #: What the extension's takeover chord last asked for, or None for "no
    #: news". The extension owns the on/off state rather than sending an edge,
    #: because it is also what puts focus back where it was afterwards.
    takeover_pending: "bool | None" = None
    #: Snapshots seen at all, ever. Distinguishes "extension not installed"
    #: from "extension went quiet", which want different advice from doctor.
    seen: int = 0

    def offer(self, payload: bytes) -> bool:
        """Take a datagram if it is one of the extension's. True if it was."""
        try:
            data = json.loads(payload.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError):
            return False
        if not isinstance(data, dict):
            return False
        if data.get("kind") == "takeover":
            self.takeover_pending = bool(data.get("on", True))
            return True
        shot = Snapshot.parse(data)
        if shot is None:
            return False
        self.snapshot = shot
        self.seen += 1
        return True

    def live(self, now: float | None = None) -> bool:
        return self.seen > 0 and self.snapshot.fresh(now)

    def claim_takeover(self) -> "bool | None":
        pending, self.takeover_pending = self.takeover_pending, None
        return pending


#: One per process. The daemon has exactly one desktop to know about, and
#: threading a bridge through the window, the input handling and the loop
#: would be ceremony around a fact that is genuinely global.
_bridge = Bridge()


def bridge() -> Bridge:
    return _bridge


def mods_from_vk(codes) -> int:
    """VK codes from a configured chord to the compositor's modifier mask."""
    mask = 0
    for code in codes:
        bit = VK_TO_CLUTTER.get(int(code))
        if bit is None:
            return 0        # a chord we cannot express is a chord we never fire
        mask |= bit
    return mask
