"""The Linux overlay window, against a real X server.

The Windows suite (``test_overlay_win32.py``) exercises the real window API
rather than a mock for a reason that applies just as hard here: every bug this
layer has ever had was a disagreement between what the code believed it had
asked for and what the window manager actually did. A fake window manager
agrees with you by construction.

So this runs the real :class:`OverlayWindow` against the real X server, in a
**subprocess** -- raylib allows one window per process and the rest of the
suite already owns this one's. Skipped where there is no display, which is
every CI machine.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux") or not os.environ.get("DISPLAY"),
    reason="needs a Linux machine with an X display (XWayland counts)",
)

#: Runs in a fresh interpreter: builds the overlay window for real, and reports
#: what the X server says about it at each step rather than what we asked for.
PROBE = r"""
import json, sys, time
from brainrot.config import Config
from brainrot.engine.window import OverlayWindow
from brainrot.overlay import x11

cfg = Config()
cfg.width, cfg.height = 200, 300
window = OverlayWindow()
window.create(cfg)
win = window._win
out = {"found": bool(win)}

# Created hidden and styled before it is ever on screen: the whole point, and
# the reason the keyboard never moves when it appears.
out["hidden_at_first"] = not x11.is_mapped(win)
out["click_through_at_first"] = x11.is_click_through(win)
out["states"] = sorted(
    name for name in x11.OVERLAY_STATES
    if x11.lib().atom(name) in x11._prop(x11.lib(), win, "_NET_WM_STATE"))

# Wait for the server to agree. Mapping is a request, not an assignment: a
# reparenting window manager maps the frame in its own time.
def settle(want, limit=2.0):
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if x11.is_mapped(win) == want:
            return want
        time.sleep(0.02)
    return x11.is_mapped(win)


window.set_visible(True)
out["mapped_when_shown"] = settle(True)
out["above_when_blind"] = x11.lib().atom(x11.ABOVE_STATE) in x11._prop(
    x11.lib(), win, "_NET_WM_STATE")
out["states_when_shown"] = sorted(
    name for name in x11.QUIET_STATES
    if x11.lib().atom(name) in x11._prop(x11.lib(), win, "_NET_WM_STATE"))

# The window manager reconfigures the frame asynchronously, so this waits for
# the move rather than assuming it has landed by the next line.
window.move_to(140, 90)
out["rect"] = None
for _ in range(100):
    rect = window.rect()
    if rect is not None:
        out["rect"] = [rect.left, rect.top, rect.width, rect.height]
        if (rect.left, rect.top) == (140, 90):
            break
    time.sleep(0.02)

window.set_click_through(False)
out["catches_clicks"] = not x11.is_click_through(win)
window.set_click_through(True)
out["click_through_again"] = x11.is_click_through(win)

window.set_visible(False)
out["hidden_again"] = not settle(False)

# Shown a second time: mutter does not carry window states across an unmap,
# and the strip is unmapped at the end of every turn.
window.set_visible(True)
out["states_second_time"] = sorted(
    name for name in x11.QUIET_STATES
    if x11.lib().atom(name) in x11._prop(x11.lib(), win, "_NET_WM_STATE"))
window.set_visible(False)

window.destroy()
print("RESULT=" + json.dumps(out))
"""


@pytest.fixture(scope="module")
def probe() -> dict:
    result = subprocess.run([sys.executable, "-c", PROBE], capture_output=True,
                            text=True, timeout=180)
    for line in result.stdout.splitlines():
        if line.startswith("RESULT="):
            return json.loads(line.removeprefix("RESULT="))
    pytest.fail(f"probe produced no result:\n{result.stdout}\n{result.stderr}")


def test_the_window_is_found_at_all(probe: dict) -> None:
    """raylib hands out a ``GLFWwindow *`` on Linux and the X11 window behind
    it is not reachable through the cffi module, so it is discovered by
    ``_NET_WM_PID``. If that ever stops working, everything else here is a
    no-op that passes."""
    assert probe["found"]


def test_it_is_styled_before_it_is_ever_on_screen(probe: dict) -> None:
    """A window that appears and *then* becomes click-through and unfocusable
    has a frame in which it is neither, and that frame is when it takes the
    keyboard out of a sentence someone was typing."""
    assert probe["hidden_at_first"]
    assert probe["click_through_at_first"]
    assert probe["states"] == sorted(
        ["_NET_WM_STATE_ABOVE", "_NET_WM_STATE_SKIP_PAGER",
         "_NET_WM_STATE_SKIP_TASKBAR"])


def test_showing_and_hiding_maps_and_unmaps(probe: dict) -> None:
    assert probe["mapped_when_shown"]
    assert probe["hidden_again"]


def test_it_is_not_always_above_when_it_cannot_hide_itself(probe: dict) -> None:
    """The probe runs with no shell extension talking to it, so nothing can
    say which window is in front and the strip cannot hide when you look
    away. A window that is both always-above *and* unable to hide is a window
    that sits on top of your browser -- the one behaviour this project exists
    to avoid -- so in that state it goes in the ordinary band instead."""
    assert not probe["above_when_blind"]


def test_the_states_survive_being_hidden_and_shown_again(probe: dict) -> None:
    """mutter drops ``_NET_WM_STATE_ABOVE`` across an unmap and remap. The
    strip goes idle at the end of every turn, so without re-asserting them it
    is correct on the first turn of a session and behind the Claude Code
    window on every turn after -- which is a bug you only see on the second
    prompt, and therefore blame on something else."""
    wanted = sorted(["_NET_WM_STATE_SKIP_PAGER", "_NET_WM_STATE_SKIP_TASKBAR"])
    assert probe["states_when_shown"] == wanted
    assert probe["states_second_time"] == wanted


def test_it_goes_exactly_where_it_is_put(probe: dict) -> None:
    """Placement is the whole reason for using X11 on a Wayland session; a
    Wayland client cannot do this at all."""
    assert probe["rect"] is not None
    left, top, width, height = probe["rect"]
    assert (left, top) == (140, 90)
    assert (width, height) > (0, 0)


def test_clicks_fall_through_except_when_they_are_asked_for(probe: dict) -> None:
    """The input shape, not the bounding shape: emptying the bounding shape
    would make the strip invisible rather than intangible."""
    assert probe["catches_clicks"]
    assert probe["click_through_again"]
