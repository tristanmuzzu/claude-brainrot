"""Handing control of a scene to a person, and taking it back.

The two properties that matter: while someone is driving the scene must stop
driving itself (a runner that keeps saving you is not one you are steering),
and when they stop, it must pick the run back up rather than sit there.
"""

from __future__ import annotations

import pytest

from conftest import H, W, ensure_window

from brainrot.engine import scene as scene_api
from brainrot.engine.input import IDLE_HANDBACK, Controller, Intent
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed

DT = 1 / 60


@pytest.fixture(scope="module", autouse=True)
def _window():
    ensure_window()


def build(run: int = 4):
    seed = Seed.for_run(run)
    return scene_api.build(
        "runner", scene_api.SceneContext(W, H, generate_palette(seed), seed))


def settle(scene, seconds: float = 1.0):
    for _ in range(int(seconds / DT)):
        scene.update(DT)
        scene.elapsed += DT


# -- the controller ---------------------------------------------------------


def test_no_keys_are_read_without_focus() -> None:
    """The overlay never has focus, so it must never read the keyboard.

    This is the whole reason there is no global key hook: without focus there
    is no legitimate way to know what was typed, and no attempt is made.
    """
    c = Controller()
    intent = c.poll(now=10.0, focused=False)
    assert not intent.any()
    assert not c.engaged


def test_control_hands_back_after_a_pause() -> None:
    c = Controller()
    c.engaged = True
    c.last_input = 100.0
    c.poll(now=100.0 + IDLE_HANDBACK - 0.1, focused=True)
    assert c.engaged, "handed back while still within the idle window"
    c.poll(now=100.0 + IDLE_HANDBACK + 0.1, focused=True)
    assert not c.engaged


def test_losing_focus_hands_back_immediately() -> None:
    c = Controller()
    c.engaged = True
    c.poll(now=5.0, focused=False)
    assert not c.engaged


# -- the runner under control ----------------------------------------------


def test_steering_moves_the_runner_and_silences_the_planner() -> None:
    scene = build()
    settle(scene, 2.0)
    assert scene.playable

    start = scene.motion.target_lane
    want = 0 if start > 0 else 2
    step = Intent(left=start > 0, right=start == 0)

    for _ in range(int(1.5 / DT)):
        scene.control(step)
        scene.update(DT)
        scene.elapsed += DT
        assert scene.driven, "the planner should be standing down"
        if scene.motion.target_lane == want:
            break
    assert scene.motion.target_lane == want, "steering did not take effect"
    assert not scene._booked, "the planner kept its bookings while driven"


def test_a_jump_key_actually_jumps() -> None:
    scene = build(6)
    settle(scene, 2.0)
    while scene.motion.busy if hasattr(scene.motion, "busy") else scene.airborne:
        scene.update(DT)
        scene.elapsed += DT
    scene.control(Intent(jump=True))
    assert scene.airborne


def test_the_run_resumes_on_its_own_afterwards() -> None:
    """Stop steering and the planner takes the wheel back, still clean."""
    scene = build(9)
    settle(scene, 2.0)
    for _ in range(int(1.0 / DT)):
        scene.control(Intent(right=True))
        scene.update(DT)
        scene.elapsed += DT

    before = scene.travel
    settle(scene, 3.0)
    assert not scene.driven, "never handed back"
    assert scene.travel > before + 20, "the run did not continue"

    # and from here it keeps its own guarantee again
    scene.contacts = 0
    settle(scene, 25.0)
    assert scene.contacts == 0, "autopilot did not resume cleanly"


def test_driving_does_not_disable_the_contact_response() -> None:
    """A player may crash. It still has to read as a hit, not a pass-through."""
    scene = build(11)
    settle(scene, 2.0)
    scene.control(Intent(right=True))
    scene.entities.append({"kind": "barrier", "lane": scene.lane, "d": 0.0})
    scene.update(DT)
    assert scene.contacts > 0
    assert scene.impact_t >= 0.0
    hit = scene.entities[-1]
    assert scene.body_box().penetration(scene.solid_box(hit)) == 0.0


def test_the_overlay_needs_the_chord_but_a_demo_window_does_not() -> None:
    """An ordinary window just needs focus; the overlay has to be handed the
    keyboard, because it is built never to have focus in the first place."""
    from brainrot.engine.input import Takeover
    from brainrot.engine.window import DesktopWindow, OverlayWindow

    assert Takeover(DesktopWindow()).needs_chord() is False
    overlay = Takeover(OverlayWindow())
    assert overlay.needs_chord() is True
    assert overlay.focused() is False, "unfocused overlay claimed the keyboard"


def test_the_loop_wires_the_keyboard_through_to_the_scene(monkeypatch) -> None:
    """End to end through Overlay._drive, with raylib's key state faked.

    Everything above tests the pieces. This one checks they are actually
    connected: a held key reaches the scene, the scene reacts, and the loop
    stops asking the planner for an opinion.
    """
    from brainrot.config import Config
    from brainrot.engine import input as input_mod, rl
    from brainrot.engine.loop import Overlay
    from brainrot.engine.window import HeadlessWindow

    overlay = Overlay(Config(), HeadlessWindow())
    overlay.scene = build(4)
    settle(overlay.scene, 2.0)
    monkeypatch.setattr(overlay.takeover, "focused", lambda: True)
    monkeypatch.setattr(overlay.takeover, "update", lambda: None)

    # Hold whichever direction there is actually room to move in.
    start = overlay.scene.motion.target_lane
    held = {rl.KEY_LEFT if start > 0 else rl.KEY_RIGHT: True}
    monkeypatch.setattr(input_mod.rl, "IsKeyDown",
                        lambda key: held.get(key, False))
    for i in range(int(1.5 / DT)):
        overlay._drive(now=100.0 + i * DT)
        overlay.scene.update(DT)
        overlay.scene.elapsed += DT
        if overlay.scene.motion.target_lane != start:
            break

    assert overlay.controller.engaged, "the loop never handed over control"
    assert overlay.scene.driven, "the scene did not know it was being driven"
    assert overlay.scene.motion.target_lane != start, "the key did nothing"


# -- the takeover chord -----------------------------------------------------


@pytest.mark.parametrize("spec,size", [
    ("ctrl+alt+shift+home", 4),
    ("Ctrl + Alt + B", 3),
    ("win+f13", 2),
    ("scrolllock", 1),
    ("pause", 1),
    ("ctrl+7", 2),
])
def test_chords_parse(spec: str, size: int) -> None:
    from brainrot.engine.keys import parse_chord

    assert len(parse_chord(spec)) == size


@pytest.mark.parametrize("spec", [
    "", "   ", "ctrl+", "ctrl+alt", "shift", "ctrl+nonsense", "ctrl++",
])
def test_unusable_chords_are_rejected(spec: str) -> None:
    """Modifiers alone would fire constantly while someone typed, and a typo
    must not silently mean "no takeover ever"."""
    from brainrot.engine.keys import parse_chord

    assert parse_chord(spec) == frozenset()


def test_a_bad_hotkey_falls_back_rather_than_disabling_takeover() -> None:
    from brainrot.config import Config
    from brainrot.engine.keys import parse_chord

    cfg = Config()
    cfg.hotkey = "ctrl+alt"          # modifiers only: unusable
    cfg._validate()
    assert cfg.hotkey == Config.hotkey
    assert parse_chord(cfg.hotkey)


def test_describe_round_trips_a_chord() -> None:
    """`brainrot hotkey` prints what describe() produces, and the config then
    parses it back -- so the two have to agree exactly."""
    from brainrot.engine.keys import describe, parse_chord

    for spec in ("ctrl+alt+shift+home", "win+f13", "ctrl+alt+b", "pause"):
        codes = parse_chord(spec)
        assert parse_chord(describe(codes)) == codes


def test_the_configured_chord_is_what_gets_watched() -> None:
    from brainrot.engine.input import Takeover
    from brainrot.engine.keys import parse_chord
    from brainrot.engine.window import OverlayWindow

    t = Takeover(OverlayWindow(), "win+f13")
    assert t.codes == parse_chord("win+f13")
    # An unusable chord means no takeover, not a crash.
    assert Takeover(OverlayWindow(), "shift").codes == frozenset()
    assert Takeover(OverlayWindow(), "shift")._chord_down() is False


def test_the_loop_takes_the_chord_from_config() -> None:
    from brainrot.config import Config
    from brainrot.engine.keys import parse_chord
    from brainrot.engine.loop import Overlay
    from brainrot.engine.window import HeadlessWindow

    cfg = Config()
    cfg.hotkey = "ctrl+shift+f9"
    cfg.handback_seconds = 3.0
    overlay = Overlay(cfg, HeadlessWindow())
    assert overlay.takeover.codes == parse_chord("ctrl+shift+f9")
    assert overlay.controller.handback == 3.0


def test_parkour_is_not_offered_the_keyboard_yet() -> None:
    """Scenes opt in. Parkour's control scheme is still to be designed, and
    the loop must not hand it input it has no idea what to do with."""
    seed = Seed.for_run(5)
    parkour = scene_api.build(
        "parkour", scene_api.SceneContext(W, H, generate_palette(seed), seed))
    assert parkour.playable is False
