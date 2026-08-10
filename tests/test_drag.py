"""Dragging the strip somewhere better, and it staying there.

Automatic placement is a guess from geometry; it knows where the Claude Code
window is and nothing about where that window keeps its toolbar. This is the
correction, and the properties that matter are the ones that keep the overlay
from becoming the thing it exists not to be: it must never take focus, and it
must never swallow a click that was meant for the app behind it.

Every input is injected, so the whole gesture runs without a mouse.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from brainrot import placement as placement_store
from brainrot.config import Config
from brainrot.engine.input import Mover
from brainrot.engine.keys import parse_chord, parse_modifiers
from brainrot.engine.window import Placement, Rect, place


class FakeWindow:
    """An overlay window that records what was asked of it."""

    def __init__(self, rect: Rect = Rect(1600, 100, 1900, 500)) -> None:
        self._rect = rect
        self.click_through = True
        self.remembered = 0
        self.cleared = 0

    def rect(self) -> Rect:
        return self._rect

    def set_click_through(self, through: bool) -> None:
        self.click_through = through

    def move_to(self, x: int, y: int) -> None:
        self._rect = Rect(x, y, x + self._rect.width, y + self._rect.height)

    def remember_placement(self) -> None:
        self.remembered += 1

    def clear_placement(self) -> None:
        self.cleared += 1


class Hand:
    """Where the pointer is, whether the button is down, what is held."""

    def __init__(self) -> None:
        self.at = (0, 0)
        self.down = False
        self.held = False
        self.now = 100.0


@pytest.fixture
def hand() -> Hand:
    return Hand()


@pytest.fixture
def window() -> FakeWindow:
    return FakeWindow()


@pytest.fixture
def mover(window: FakeWindow, hand: Hand) -> Mover:
    return Mover(window, "ctrl+alt", clock=lambda: hand.now,
                 held=lambda: hand.held, cursor=lambda: hand.at,
                 button=lambda: hand.down)


def test_the_chord_is_modifiers_only() -> None:
    """parse_chord refuses these on purpose -- a key chord of modifiers alone
    would fire while you typed. A mouse gesture is the opposite case."""
    assert not parse_chord("ctrl+alt")
    assert parse_modifiers("ctrl+alt") == frozenset({0x11, 0x12})
    assert not parse_modifiers("ctrl+alt+home"), "not a mouse gesture"
    assert not parse_modifiers("nonsense")


def test_nothing_happens_without_the_chord(mover: Mover, window: FakeWindow,
                                           hand: Hand) -> None:
    """The whole point: an ordinary click goes to whatever is behind."""
    hand.at = (1700, 200)               # over the strip
    hand.down = True
    mover.update()
    assert window.click_through is True, "swallowed a click meant for the app"
    assert mover.dragging is False
    assert window._rect == Rect(1600, 100, 1900, 500)


def test_the_chord_alone_does_not_catch_clicks_away_from_the_strip(
        mover: Mover, window: FakeWindow, hand: Hand) -> None:
    hand.held = True
    hand.at = (200, 200)                # elsewhere entirely
    mover.update()
    assert window.click_through is True
    assert mover.armed is False


def test_holding_the_chord_over_the_strip_arms_it(mover: Mover,
                                                  window: FakeWindow,
                                                  hand: Hand) -> None:
    hand.held = True
    hand.at = (1700, 200)
    mover.update()
    assert mover.armed is True
    assert window.click_through is False, "the click would fall through mid-drag"
    assert mover.caption() == "drag to move"

    hand.held = False                   # let go without clicking
    mover.update()
    assert mover.armed is False
    assert window.click_through is True, "left the overlay eating clicks"


def test_dragging_moves_the_strip_by_exactly_the_pointer(
        mover: Mover, window: FakeWindow, hand: Hand) -> None:
    hand.held = True
    hand.at = (1700, 200)               # 100,100 into a strip at 1600,100
    hand.down = True
    mover.update()
    assert mover.dragging is True

    hand.at = (1000, 600)
    mover.update()
    assert window._rect.left == 900 and window._rect.top == 500, \
        "the strip did not stay under the pointer"
    assert window._rect.width == 300 and window._rect.height == 400, \
        "dragging resized it"

    hand.down = False
    mover.update()
    assert mover.dragging is False
    assert window.remembered == 1, "the drop was not remembered"


def test_the_pointer_may_outrun_the_window(mover: Mover, window: FakeWindow,
                                           hand: Hand) -> None:
    """A dragged window lags the pointer, so the pointer leaves it. Dropping
    what you are holding at that moment would make dragging nearly impossible.
    """
    hand.held, hand.down, hand.at = True, True, (1700, 200)
    mover.update()
    hand.at = (10, 10)                  # miles away, still holding
    mover.update()
    assert mover.dragging is True
    assert window._rect.left == -90


def test_double_click_goes_back_to_automatic_placement(
        mover: Mover, window: FakeWindow, hand: Hand) -> None:
    hand.held, hand.at = True, (1700, 200)
    hand.down = True
    mover.update()
    hand.down = False
    mover.update()

    hand.now += 0.2                     # inside the double-click window
    hand.down = True
    mover.update()
    assert window.cleared == 1
    assert mover.dragging is False, "started dragging on the reset click"


def test_two_slow_clicks_are_two_drags_not_a_reset(
        mover: Mover, window: FakeWindow, hand: Hand) -> None:
    hand.held, hand.at = True, (1700, 200)
    for _ in range(2):
        hand.down = True
        mover.update()
        hand.down = False
        mover.update()
        hand.now += 1.0
    assert window.cleared == 0
    assert window.remembered == 2


def test_going_off_screen_gives_the_clicks_back(mover: Mover,
                                                window: FakeWindow,
                                                hand: Hand) -> None:
    """A hidden window that still eats clicks eats them for no reason."""
    hand.held, hand.at, hand.down = True, (1700, 200), True
    mover.update()
    assert window.click_through is False

    mover.release()                     # what the daemon does when it hides
    assert window.click_through is True
    assert mover.dragging is False
    assert window.remembered == 1, "a drag interrupted by hiding was thrown away"


def test_dragging_can_be_turned_off_entirely(window: FakeWindow, hand: Hand) -> None:
    off = Mover(window, "", clock=lambda: hand.now, held=lambda: True,
                cursor=lambda: (1700, 200), button=lambda: True)
    off.update()
    assert off.dragging is False
    assert window.click_through is True


# -- what the drop is remembered as -----------------------------------------


def cfg(**kwargs) -> Config:
    settings = dict(width=280, height=400, margin_x=12, margin_y=20,
                    anchor_y=0.0, dock="right")
    settings.update(kwargs)
    return Config(**settings)


WORK = Rect(0, 0, 1920, 1040)


def test_a_remembered_spot_beats_the_geometry() -> None:
    host = Rect(0, 0, 1200, 900)
    auto = place(cfg(), WORK, host)
    manual = place(cfg(), WORK, host, placement_store.Manual(dx=500, dy=300))
    assert auto != manual
    assert manual.x == 1200 - 280 - 500
    assert manual.y == 300


def test_a_remembered_spot_still_follows_the_window() -> None:
    """Offsets from the host window, not screen coordinates -- so moving the
    window takes the strip with it rather than leaving it behind."""
    manual = placement_store.Manual(dx=40, dy=120)
    here = place(cfg(), WORK, Rect(0, 0, 1200, 900), manual)
    moved = place(cfg(), WORK, Rect(100, 50, 1300, 950), manual)
    assert moved.x - here.x == 100
    assert moved.y - here.y == 50


def test_a_remembered_spot_cannot_strand_it_off_screen() -> None:
    """Dropped on a second monitor that is not there any more."""
    host = Rect(0, 0, 1920, 1040)
    for offset in (placement_store.Manual(dx=-4000, dy=-4000),
                   placement_store.Manual(dx=9000, dy=9000)):
        spot = place(cfg(), WORK, host, offset)
        assert WORK.left <= spot.x and spot.x + spot.width <= WORK.right
        assert WORK.top <= spot.y and spot.y + spot.height <= WORK.bottom


def test_a_remembered_spot_survives_a_change_of_display_scale() -> None:
    """The offset is logical pixels, so it means the same *distance* at any
    scale.

    Stored in device pixels it did not: a strip dropped at one scale came back
    at another a different distance from the window it was dropped against --
    far enough, on a single screen, to be clamped against the edge and vanish.
    """
    manual = placement_store.Manual(dx=100, dy=60)
    host = Rect(0, 0, 1200, 900)
    at_100 = place(cfg(), WORK, host, manual, scale=1.0)
    # The same desktop at 200%: every rectangle doubles, and so must the gap.
    big_work = Rect(0, 0, 3840, 2080)
    big_host = Rect(0, 0, 2400, 1800)
    at_200 = place(cfg(), big_work, big_host, manual, scale=2.0)
    assert (big_host.right - (at_200.x + at_200.width)) == 2 * (
        host.right - (at_100.x + at_100.width))
    assert at_200.y - big_host.top == 2 * (at_100.y - host.top)


def test_docking_left_measures_the_offset_from_the_left_edge() -> None:
    host = Rect(200, 0, 1400, 900)
    spot = place(cfg(dock="left"), WORK, host, placement_store.Manual(dx=60, dy=10))
    assert spot.x == 260


def test_a_dropped_position_survives_a_restart(tmp_path: Path) -> None:
    assert placement_store.load(tmp_path) is None
    placement_store.save(placement_store.Manual(dx=17, dy=42), tmp_path)
    assert placement_store.load(tmp_path) == placement_store.Manual(17, 42)
    placement_store.clear(tmp_path)
    assert placement_store.load(tmp_path) is None


def test_a_corrupt_placement_file_is_not_a_crash(tmp_path: Path) -> None:
    (tmp_path / "placement.json").write_text("{ this is not json", encoding="utf-8")
    assert placement_store.load(tmp_path) is None


def test_placement_survives_a_missing_directory(tmp_path: Path) -> None:
    nested = tmp_path / "not" / "there"
    placement_store.save(placement_store.Manual(dx=1, dy=2), nested)
    assert placement_store.load(nested) == placement_store.Manual(1, 2)


def test_the_default_placement_is_a_placement() -> None:
    assert isinstance(place(cfg(), WORK), Placement)
