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
