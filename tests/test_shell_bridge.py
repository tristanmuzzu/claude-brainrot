"""The half of the Linux backend that has no desktop in it.

Everything the daemon concludes from what gnome-shell tells it -- which window
is the Claude Code host, how big a pixel is, whether the answer is fresh
enough to act on -- is decided here, from a datagram. So it is all testable
without a compositor, and it is all tested here rather than by looking at a
screen and believing it.
"""

from __future__ import annotations

import json

from brainrot.overlay import shell


def snapshot(**over) -> dict:
    data = {
        "kind": "shell",
        "seq": 3,
        "focus": 11,
        "windows": [
            {"id": 11, "pid": 900, "cls": "com.anthropic.Claude",
             "rect": [100, 50, 1200, 800], "mon": 0, "hidden": False},
            {"id": 12, "pid": 901, "cls": "google-chrome",
             "rect": [0, 0, 600, 400], "mon": 0, "hidden": False},
        ],
        "monitors": [{"index": 0, "work": [0, 30, 1536, 834], "scale": 2,
                      "primary": True}],
        "pointer": [400, 300, 0],
        "logical": [1536, 864],
    }
    data.update(over)
    return data


def test_a_snapshot_parses_into_windows_and_monitors() -> None:
    shot = shell.Snapshot.parse(snapshot())
    assert shot is not None
    assert [w.id for w in shot.windows] == [11, 12]
    assert shot.window(11).wm_class == "com.anthropic.Claude"
    assert shot.monitors[0].work == (0, 30, 1536, 834)


def test_anything_that_is_not_ours_is_refused() -> None:
    """This socket carries hook events too, and anything on the machine can
    write to it. A packet that is not a snapshot must be handed back, not
    half-parsed into one."""
    assert shell.Snapshot.parse({"kind": "Stop"}) is None
    assert shell.Snapshot.parse({"windows": []}) is None
    assert shell.Snapshot.parse([1, 2, 3]) is None


def test_a_malformed_window_is_dropped_rather_than_the_snapshot() -> None:
    shot = shell.Snapshot.parse(snapshot(windows=[
        {"id": 11, "pid": 900, "cls": "x", "rect": [1, 2, 3, 4]},
        {"id": 12, "cls": "no rect at all"},
        {"id": "not a number", "rect": [1, 2, 3, 4]},
    ]))
    assert shot is not None
    assert [w.id for w in shot.windows] == [11]


def test_the_host_is_the_nearest_ancestor_that_owns_a_window() -> None:
    """The shim sends its ancestry nearest-first. A shell inside tmux inside a
    terminal has three candidates and only the terminal has a window -- but if
    two of them did, the nearest one is the window you are looking at."""
    shot = shell.Snapshot.parse(snapshot())
    assert shot.host_for([555, 901, 900]) == 12      # chrome is nearer than claude
    assert shot.host_for([555, 900]) == 11
    assert shot.host_for([1, 2, 3]) == 0
    assert shot.host_for([]) == 0


def test_scale_is_measured_against_the_x_screen_not_trusted() -> None:
    """Device pixels per logical pixel comes from two numbers each side can
    read directly, rather than from a scale factor either side reports."""
    shot = shell.Snapshot.parse(snapshot())
    assert shot.scale_against(3072) == 2.0
    assert shot.scale_against(1536) == 1.0
    # Mid-resolution-change readings are refused in favour of the reported
    # monitor scale, because a ratio of 20 would place the strip off-screen.
    assert shot.scale_against(99999) == 2.0
    assert shot.scale_against(0) == 2.0


def test_scale_falls_back_to_one_when_nothing_can_be_measured() -> None:
    shot = shell.Snapshot.parse(snapshot(logical=[0, 0], monitors=[]))
    assert shot.scale_against(3072) == 1.0


def test_a_stale_snapshot_is_not_an_answer() -> None:
    """The extension heartbeats once a second. Silence means it is gone, and
    placing the strip against a window that may have moved or closed is worse
    than not placing it at all."""
    shot = shell.Snapshot.parse(snapshot(), now=100.0)
    assert shot.fresh(now=101.0)
    assert not shot.fresh(now=110.0)


def test_the_bridge_routes_snapshots_takeovers_and_nothing_else() -> None:
    bridge = shell.Bridge()
    assert not bridge.live(now=0.0)

    assert bridge.offer(json.dumps(snapshot()).encode())
    assert bridge.live()
    assert bridge.snapshot.focus == 11

    assert not bridge.offer(b'{"kind": "Stop", "session": "x"}')
    assert not bridge.offer(b"not json at all")
    assert bridge.snapshot.focus == 11, "a rejected packet must change nothing"

    assert bridge.claim_takeover() is None
    assert bridge.offer(b'{"kind": "takeover", "on": true}')
    assert bridge.claim_takeover() is True
    assert bridge.claim_takeover() is None, "a request is claimed exactly once"
    assert bridge.offer(b'{"kind": "takeover", "on": false}')
    assert bridge.claim_takeover() is False


def test_chords_become_compositor_modifier_bits() -> None:
    from brainrot.engine.keys import parse_modifiers

    assert shell.mods_from_vk(parse_modifiers("ctrl+alt")) == (
        shell.CLUTTER_CONTROL | shell.CLUTTER_ALT)
    assert shell.mods_from_vk(parse_modifiers("shift+super")) == (
        shell.CLUTTER_SHIFT | shell.CLUTTER_SUPER)
    # A chord naming something the compositor does not send is a chord that
    # must never fire, rather than one that fires on the modifiers it *can*
    # see -- which would arm the drag gesture on a plain Ctrl.
    assert shell.mods_from_vk([0x11, 0x24]) == 0
    assert shell.mods_from_vk([]) == 0


def test_the_strip_is_only_always_above_when_it_can_also_hide() -> None:
    """The two have to be decided together.

    Always-above is right precisely when something else decides *when* the
    strip is on screen. Without the extension nothing can, so always-above
    would mean sitting on top of whatever you switched to -- which is what
    it did, and what it is not allowed to do.
    """
    import time

    from brainrot.config import Config
    from brainrot.overlay import linux

    cfg = Config()
    bridge = shell.bridge()
    before = bridge.snapshot, bridge.seen
    try:
        bridge.snapshot, bridge.seen = shell.Snapshot(), 0
        assert not linux.focus_known()
        assert not linux.wants_above(cfg)

        bridge.snapshot = shell.Snapshot.parse(snapshot(), now=time.monotonic())
        bridge.seen = 1
        assert linux.focus_known()
        assert linux.wants_above(cfg)

        # ...unless someone asked for the blunt behaviour on purpose.
        bridge.snapshot, bridge.seen = shell.Snapshot(), 0
        cfg.attach = "topmost"
        assert linux.wants_above(cfg)
    finally:
        bridge.snapshot, bridge.seen = before


def test_the_screen_size_is_asked_of_the_server_not_read_from_the_cache(
        monkeypatch) -> None:
    """The bug that made the strip vanish when the display scale changed.

    ``XDisplayWidth`` reads ``ScreenOfDisplay(dpy, scr)->width``, which Xlib
    fills in once from the connection setup block. The daemon holds one X
    connection for the whole session, so after mutter resized the X screen for
    a new display scale that macro kept answering with the old screen -- and
    every device-pixel conversion is measured against it. The strip came out
    sized for a screen that was no longer there and clamped against edges that
    did not exist.
    """
    import ctypes

    from brainrot.overlay import x11

    class FakeX11:
        def __init__(self, size) -> None:
            self.size = size
            self.attribute_calls = 0
            self.cached_macro_calls = 0

        def XGetWindowAttributes(self, display, window, ref) -> int:
            self.attribute_calls += 1
            attrs = ref._obj
            attrs.width, attrs.height = self.size
            return 1

        def XDisplayWidth(self, display, screen) -> int:
            self.cached_macro_calls += 1
            return 3072

        def XDisplayHeight(self, display, screen) -> int:
            self.cached_macro_calls += 1
            return 1728

    class FakeHandle:
        def __init__(self, lib) -> None:
            self.x11 = lib
            self.display = ctypes.c_void_p(1)
            self.root = 1

    fake = FakeX11((3072, 1728))
    monkeypatch.setattr(x11, "lib", lambda: FakeHandle(fake))
    monkeypatch.setattr(x11, "_screen", None)
    monkeypatch.setattr(x11, "_screen_at", 0.0)

    assert x11.screen_rect() == (0, 0, 3072, 1728)
    # Asked the server, rather than reading the number Xlib cached at connect.
    assert fake.attribute_calls == 1
    assert fake.cached_macro_calls == 0

    # The scale changes: mutter resizes the X screen under the running daemon.
    fake.size = (1920, 1080)
    monkeypatch.setattr(x11, "_screen_at", 0.0)      # past the reading's life
    assert x11.screen_rect() == (0, 0, 1920, 1080)

    # ...but not once per call: several conversions happen every frame.
    calls = fake.attribute_calls
    x11.screen_rect()
    assert fake.attribute_calls == calls


def test_a_resized_screen_changes_the_measured_scale(monkeypatch) -> None:
    """The ratio is measured, so both halves have to be live -- and after the
    screen size started coming from the server, both are."""
    import time

    from brainrot.overlay import linux, x11

    bridge = shell.bridge()
    before = bridge.snapshot, bridge.seen
    try:
        # 125%: a 1536-wide logical desktop on a 3072-wide X screen.
        bridge.snapshot = shell.Snapshot.parse(
            snapshot(logical=[1536, 864]), now=time.monotonic())
        bridge.seen = 1
        monkeypatch.setattr(x11, "screen_rect", lambda: (0, 0, 3072, 1728))
        assert linux.scale() == 2.0

        # 100%: the compositor reports a wider desktop and the X screen shrinks.
        bridge.snapshot = shell.Snapshot.parse(
            snapshot(logical=[1920, 1080]), now=time.monotonic())
        monkeypatch.setattr(x11, "screen_rect", lambda: (0, 0, 1920, 1080))
        assert linux.scale() == 1.0
    finally:
        bridge.snapshot, bridge.seen = before
