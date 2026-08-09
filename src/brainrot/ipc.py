"""Hook -> daemon transport.

UDP, deliberately. The hook shim runs *inside* Claude Code's critical path, so
the transport is chosen for what it cannot do rather than what it can:

  * no connection handshake, so the shim never blocks on a dead daemon;
  * no delivery guarantee, so a wedged daemon cannot apply backpressure to the
    thing you actually care about (your Claude Code session);
  * a lost packet costs at worst one missed show/hide, self-correcting on the
    next event.

A dropped brainrot frame is free. A hung editor is not. That asymmetry is the
whole design.
"""

from __future__ import annotations

import json
import socket
import threading
from collections.abc import Callable
from dataclasses import dataclass

MAX_DATAGRAM = 4096


@dataclass(frozen=True)
class Event:
    """One hook firing."""

    kind: str
    session: str = ""
    tool: str = ""
    #: Native handle of the window hosting the Claude Code session, when the
    #: shim could discover one (Windows only). 0 means unknown.
    hwnd: int = 0
    #: The shim's own process ancestry, nearest first (Linux). A Wayland
    #: client cannot discover a window handle -- there is nothing to discover,
    #: the protocol has no such concept -- so the shim sends what it *can*
    #: know and the daemon matches it against the window list the compositor
    #: reports. The terminal or app running Claude Code is an ancestor of the
    #: hook; nothing else in the list owns a window.
    pids: tuple[int, ...] = ()

    @classmethod
    def parse(cls, payload: bytes) -> "Event | None":
        try:
            data = json.loads(payload.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        kind = str(data.get("kind") or data.get("hook_event_name") or "").strip()
        if not kind:
            return None
        try:
            hwnd = int(data.get("hwnd") or 0)
        except (TypeError, ValueError):
            hwnd = 0
        pids: list[int] = []
        for value in data.get("pids") or ():
            try:
                pids.append(int(value))
            except (TypeError, ValueError):
                continue
        return cls(
            kind=kind,
            session=str(data.get("session") or data.get("session_id") or ""),
            tool=str(data.get("tool") or data.get("tool_name") or ""),
            hwnd=hwnd,
            pids=tuple(pids),
        )


class EventListener:
    """Background UDP receiver.

    Bound to loopback only. Anything that can send to this port can already run
    code as you, so there is nothing further to defend here, but binding to
    ``127.0.0.1`` keeps it off the network regardless of firewall state.
    """

    def __init__(self, host: str, port: int, on_event: Callable[[Event], None],
                 on_raw: "Callable[[bytes], bool] | None" = None) -> None:
        self.host = host
        self.port = port
        self._on_event = on_event
        # Not everything on this socket is a hook. On GNOME the shell
        # extension pushes desktop snapshots to the same port -- one socket,
        # one thing to get wrong, one thing for `brainrot doctor` to check --
        # and this is the first refusal: if the backend claims a datagram, it
        # never reaches the hook parser.
        self._on_raw = on_raw
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        # Periodic wakeups so stop() is responsive without a self-pipe.
        sock.settimeout(0.25)
        self._sock = sock
        self._thread = threading.Thread(target=self._run, name="brainrot-ipc", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                payload, _addr = self._sock.recvfrom(MAX_DATAGRAM)
            except socket.timeout:
                continue
            except OSError:
                break
            if self._on_raw is not None:
                try:
                    if self._on_raw(payload):
                        continue
                except Exception:
                    pass
            event = Event.parse(payload)
            if event is not None:
                try:
                    self._on_event(event)
                except Exception:
                    # A scene bug must not kill the listener; the next event
                    # gets a fresh attempt.
                    pass

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        if self._sock is not None:
            self._sock.close()
            self._sock = None


def send(host: str, port: int, kind: str, session: str = "", tool: str = "",
         hwnd: int = 0, pids: "tuple[int, ...] | list[int]" = ()) -> None:
    """Fire a single event. Never raises -- used by the CLI and tests."""
    payload = json.dumps(
        {"kind": kind, "session": session, "tool": tool, "hwnd": hwnd,
         "pids": list(pids)}
    ).encode("utf-8")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(payload, (host, port))
    except OSError:
        pass
