"""Where the strip goes.

The overlay used to dock to the left edge of the *monitor*, which on a
maximised editor means straight on top of its sidebar -- click-through, so
usable, and unreadable. Placement is now derived from the host window's own
rectangle, and this is the geometry, tested without a desktop.
"""

from __future__ import annotations

import pytest

from brainrot.config import Config
from brainrot.engine.window import Rect, place

#: 1920x1080 with a 40px taskbar.
WORK = Rect(0, 0, 1920, 1040)
#: What a maximised window actually reports: a few pixels of border overhang.
MAXIMISED = Rect(-9, -9, 1929, 1049)


def cfg(**kwargs) -> Config:
    settings = dict(width=280, height=400, margin_x=12, margin_y=20,
                    anchor_y=0.0, dock="right")
    settings.update(kwargs)
    return Config(**settings)


def test_a_maximised_host_keeps_the_strip_off_the_sidebar() -> None:
    """The complaint. A maximised window leaves no room beside it, so the
    strip goes in its own margin -- and the margin it goes in is the one the
    navigation is *not* in."""
    spot = place(cfg(), WORK, MAXIMISED)
    assert spot.x > MAXIMISED.left + MAXIMISED.width // 2, "back on the sidebar"
    assert spot.x + spot.width <= WORK.right


def test_a_windowed_host_gets_the_strip_beside_it_covering_nothing() -> None:
    host = Rect(0, 0, 1200, 900)
    spot = place(cfg(), WORK, host)
    assert spot.x >= host.right, "overlapped a window it did not have to"
    assert spot.x + spot.width <= WORK.right


def test_no_room_beside_it_falls_back_to_the_margin() -> None:
    host = Rect(700, 0, 1920, 1040)
    spot = place(cfg(), WORK, host)
    assert spot.x < host.right
    assert spot.x + spot.width <= host.right


def test_docking_left_mirrors_all_of_it() -> None:
    host = Rect(700, 0, 1920, 1040)
    beside = place(cfg(dock="left"), WORK, host)
    assert beside.x + beside.width <= host.left, "should fit in the space left of it"

    inside = place(cfg(dock="left"), WORK, MAXIMISED)
    assert inside.x < MAXIMISED.left + MAXIMISED.width // 2


def test_the_taskbar_is_not_a_place_to_hide() -> None:
    spot = place(cfg(anchor_y=1.0), WORK, MAXIMISED)
    assert spot.y + spot.height <= WORK.bottom


def test_anchor_y_runs_the_height_of_the_host_window() -> None:
    host = Rect(200, 100, 1400, 900)
    top = place(cfg(anchor_y=0.0), WORK, host)
    bottom = place(cfg(anchor_y=1.0), WORK, host)
    assert top.y == host.top + 20
    assert bottom.y > top.y
    assert bottom.y + bottom.height <= host.bottom


def test_a_host_shorter_than_the_strip_still_lands_on_screen() -> None:
    host = Rect(1500, 900, 1900, 1000)
    spot = place(cfg(), WORK, host)
    assert WORK.left <= spot.x and spot.x + spot.width <= WORK.right
    assert WORK.top <= spot.y and spot.y + spot.height <= WORK.bottom


def test_the_strip_never_exceeds_the_work_area() -> None:
    small = Rect(0, 0, 400, 300)
    spot = place(cfg(width=360, height=640), small)
    assert spot.width <= small.width and spot.height <= small.height
    assert spot.x >= small.left and spot.y >= small.top
    assert spot.x + spot.width <= small.right
    assert spot.y + spot.height <= small.bottom


def test_with_no_host_it_docks_to_the_work_area() -> None:
    spot = place(cfg(), WORK)
    assert spot.x + spot.width == WORK.right - 12
    assert place(cfg(dock="left"), WORK).x == WORK.left + 12


@pytest.mark.parametrize("dock", ["right", "left"])
@pytest.mark.parametrize("host", [None, MAXIMISED, Rect(0, 0, 1200, 900),
                                  Rect(1500, 900, 1900, 1000)])
def test_the_strip_is_always_somewhere_on_the_desktop(dock, host) -> None:
    spot = place(cfg(dock=dock), WORK, host)
    assert spot.width > 0 and spot.height > 0
    assert WORK.left <= spot.x and spot.x + spot.width <= WORK.right
    assert WORK.top <= spot.y and spot.y + spot.height <= WORK.bottom
