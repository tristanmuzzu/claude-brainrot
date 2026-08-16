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
    """A player may crash. It still has to read as a hit.

    And since the run stopped having a top speed, walking squarely into
    something *is* the end of it -- for a person at the controls exactly as
    for the autopilot. What this asserts is that the response is not
    suppressed while somebody is driving, which it was written for; what it no
    longer asserts is a push-out, because a wreck does not push out.
    """
    scene = build(11)
    settle(scene, 2.0)
    # On the ground, explicitly. "Put a barrier on top of the runner" is only
    # a crash if the runner is standing there -- and two seconds into run 11
    # it happens to be a metre and a half up in the middle of a jump, which
    # made this test a statement about the speed ramp rather than about the
    # contact response.
    while scene.motion.airborne or scene.motion.rolling:
        scene.update(DT)
        scene.elapsed += DT
    scene.control(Intent(right=True))
    scene.entities.append({"kind": "barrier", "lane": scene.lane, "d": 0.0})
    scene.x = scene._lane_x(scene.lane)
    scene.update(DT)
    assert scene.contacts > 0
    assert scene.impact_t >= 0.0
    assert scene.crash_t >= 0.0, "a driven runner walked through a barrier"
    assert scene.cam_shake > 0.0, "the camera did not register the hit"


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


# -- parkour ----------------------------------------------------------------


def parkour(run: int = 5):
    seed = Seed.for_run(run)
    return scene_api.build(
        "parkour", scene_api.SceneContext(W, H, generate_palette(seed), seed))


def drive(scene, intent: Intent, seconds: float) -> None:
    for _ in range(int(seconds / DT)):
        scene.control(intent)
        scene.update(DT)
        scene.elapsed += DT


def test_parkour_steering_bends_the_course() -> None:
    """There is no free movement to give a first-person parkour runner, so
    what a player gets is the decision the generator makes: which way to go.
    Holding a direction has to actually take the course that way."""
    for run in (5, 7, 11):
        left, right = parkour(run), parkour(run)
        drive(left, Intent(left=True), 12.0)
        drive(right, Intent(right=True), 12.0)
        apart = right.pos[0] - left.pos[0]
        assert apart > 8.0, f"run {run}: steering only moved it {apart:.1f} m"


def test_parkour_steering_leaves_the_committed_blocks_alone() -> None:
    """The block being landed on and the one after it are committed. Rebuilding
    them would move the ground out from under a jump in progress."""
    scene = parkour(7)
    drive(scene, Intent(), 2.0)
    committed = [id(b) for b in scene.blocks[scene.jump_index:scene.jump_index + 2]]
    scene.control(Intent(right=True))
    scene._steer_course()
    assert [id(b) for b in scene.blocks[scene.jump_index:scene.jump_index + 2]] \
        == committed
    assert len(scene.blocks) - scene.jump_index >= 14


def test_parkour_jump_leaves_the_block_early() -> None:
    scene = parkour(7)
    while scene.phase != "ground":
        scene.update(DT)
        scene.elapsed += DT
    scene.ground_dur = 0.9
    scene.control(Intent(jump=True))
    assert scene.ground_dur <= scene.phase_t


def test_a_steered_run_still_collects_every_orb_it_lays() -> None:
    """The guarantee the course is built on -- an orb hangs on the arc the
    body will fly -- must survive being driven. Steering re-lays the course
    through the same generator, and an early take-off changes the timing of an
    arc rather than its endpoints."""
    scene = parkour(11)
    turn = Intent(right=True)
    for i in range(3600):
        # hold a direction, change it now and then, and jump off the beat
        if i % 600 < 300:
            turn = Intent(right=True, jump=i % 7 == 0)
        else:
            turn = Intent(left=True, duck=i % 11 == 0)
        scene.control(turn)
        scene.update(DT)
        scene.elapsed += DT
    assert scene.orbs > 20
    assert scene.orbs_missed == 0


def test_parkour_hands_itself_back() -> None:
    """Stop pressing keys and the scene drives itself again."""
    scene = parkour(7)
    drive(scene, Intent(right=True), 1.0)
    assert scene.driven and scene.steer != 0.0
    settle(scene, 1.0)
    assert not scene.driven and scene.steer == 0.0
