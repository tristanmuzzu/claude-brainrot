"""The tower scene's invariants, stated rather than hoped for.

Split the way the scene is: everything about the *geometry* runs against
``scenes/towerplan``, which imports no renderer, so those tests need no window
and a twelve-run sweep costs about a second. Only the tests that actually watch
a body move build a scene.

The numbers here are the ones ``tools/tower_probe.py`` prints. Where a
threshold is not zero it is because the probe says it is not zero, and the
comment says what the residue is.
"""

from __future__ import annotations

import math
import random
from collections import Counter

import pytest

from brainrot.scenes import towerplan as tp

from conftest import ensure_window


def grow(run: int, blocks: int = 260):
    """A course grown without a body. Returns the course and every block laid."""
    tower = tp.Tower(random.Random(run * 977 + 13), 0)
    course = tp.Course(random.Random(run * 6151 + 29), tower)
    laid = list(course.blocks)
    for _ in range(blocks):
        laid.append(course.spawn())
        if len(course.blocks) > tp.AHEAD:
            course.advance(len(course.blocks) - tp.AHEAD + tp.TRAIL)
    return course, laid


def solid_claims(course) -> Counter:
    seen: Counter = Counter()
    for cell, style in course.struct.items():
        if style not in tp.SEE_THROUGH:
            seen[cell] += 1
    for blk in course.blocks:
        for cell in tp._footprint(blk["x"], blk["y"], blk["z"], blk["form"]):
            seen[cell] += 1
        for d in blk["deco"]:
            if d.get("solid"):
                seen[(blk["x"] + round(d["dx"]), blk["y"] + round(d["dy"]),
                      blk["z"] + round(d["dz"]))] += 1
    return seen


# -- the lattice ------------------------------------------------------------

def test_nothing_is_ever_inside_anything_else():
    """The whole reason the tower is on an integer lattice.

    The building and the course share one occupancy map, so two solid things
    interpenetrating would mean one cell claimed twice -- there is no partial
    case, which is what makes this assertable rather than a tolerance.
    """
    for run in range(1, 13):
        course, _ = grow(run)
        doubled = [c for c, n in solid_claims(course).items() if n > 1]
        assert not doubled, f"run {run}: {doubled[:5]}"


def test_every_block_is_on_a_whole_cell():
    for run in range(1, 9):
        _, laid = grow(run)
        for blk in laid:
            assert all(float(blk[k]).is_integer() for k in "xyz")


def test_ladders_and_water_are_never_solid():
    """A ladder you cannot climb through is not a ladder."""
    for run in range(1, 9):
        course, _ = grow(run)
        for blk in course.blocks:
            for s in blk["soft"]:
                cell = (blk["x"] + s["dx"], blk["y"] + s["dy"],
                        blk["z"] + s["dz"])
                assert cell not in course.solid
                assert course.struct.get(cell, "") not in ("", ) or True
                assert course.struct.get(cell) is None or \
                    course.struct[cell] in tp.SEE_THROUGH


def test_the_emergency_answer_is_effectively_never_reached():
    """``stuck`` counts the one placement in the module nobody has checked.

    Not asserted at zero, and the reason is measured rather than conceded: over
    sixty runs of four hundred blocks the probe finds four, all of them a
    set-piece that had built its own scaffolding into a corner. One in six
    thousand blocks is about one every ninety minutes of runtime. What is
    asserted at zero is the thing an emergency hop could actually break --
    interpenetration -- and that is the test above.
    """
    total = bailed = blocks = 0
    for run in range(1, 13):
        course, laid = grow(run, 300)
        total += course.stuck
        bailed += course.bailed
        blocks += len(laid)
    assert total / blocks < 1 / 200, f"{total} emergency hops in {blocks}"
    assert bailed / blocks < 1 / 200, f"{bailed} loose bails in {blocks}"


# -- the physics ------------------------------------------------------------

def test_every_hop_is_one_a_body_can_make():
    """Re-derived from the move itself, not from the table that produced it.

    A hop is legal exactly when its take-off is between stepping off an edge
    and vanilla's one jump impulse, and when the body is on its way *down* when
    it arrives -- land while still rising and it has come up through the side
    of the block rather than onto it.
    """
    for run in range(1, 9):
        _, laid = grow(run)
        for blk in laid:
            move = blk["move"]
            if move is None or move.kind not in ("hop", "slide"):
                continue
            if blk["unchecked"]:
                continue          # the one unchecked answer; counted elsewhere
            leg = move.legs[0]
            assert tp.VY_MIN <= leg["vy0"] <= tp.VY_MAX + 1e-6
            assert tp.AIR_MIN <= leg["dur"] <= tp.AIR_MAX + 1e-6
            assert leg["dur"] >= leg["vy0"] / tp.GRAVITY - 1e-6


def test_a_bounce_never_beats_the_fall_that_fed_it():
    """Vanilla's slime restitution is 1.0 and drag takes a little off, so a
    bounce cannot reach higher than the drop that produced it. Getting this
    wrong is the obvious design and it is free energy."""
    for run in range(1, 13):
        _, laid = grow(run, 300)
        for blk in laid:
            move = blk["move"]
            if move is None or move.kind != "bounce":
                continue
            assert move.legs[0]["vy0"] <= tp.bounce_launch(blk["impact"]) + 1e-6
            assert move.legs[0]["vy0"] <= abs(blk["impact"]) + 1e-6


def test_nothing_rises_two_blocks_in_one_hop():
    """The same reason vanilla cannot: the discriminant has no solution."""
    assert tp.hop_span(2)[1] == 0.0
    # Level, vanilla's own longest sprint-jump is 4.32 m stand to stand and
    # this model reaches 4.26. Climbing a block costs most of that reach --
    # 3.10 m -- because the arc has to be past its apex when it arrives, and
    # dropping buys it back, which is why a chasm steps down.
    assert tp.hop_span(0)[1] == pytest.approx(4.26, abs=0.05)
    assert tp.hop_span(1)[1] == pytest.approx(3.10, abs=0.05)
    assert tp.hop_span(-2)[1] > tp.hop_span(0)[1] > tp.hop_span(1)[1]


def test_a_ladder_is_slower_than_running_and_a_bubble_column_is_faster():
    assert tp.CLIMB_SPEED < tp.WALK_SPEED < tp.RUN_SPEED < tp.BUBBLE_SPEED
    for run in range(1, 13):
        _, laid = grow(run, 300)
        for blk in laid:
            move = blk["move"]
            if move is None or move.kind not in ("climb", "bubble"):
                continue
            ride = move.legs[1]
            want = tp.BUBBLE_SPEED if move.kind == "bubble" else tp.CLIMB_SPEED
            rise = ride["to"][1] - ride["frm"][1]
            assert rise > 1.0
            assert ride["dur"] == pytest.approx(rise / want, rel=1e-3)


def test_a_move_is_continuous():
    """Each leg starts where the last one ended, and the whole move starts at
    the block it left and ends at the block it arrives on. A path assembled
    from legs that do not meet is a body that teleports."""
    for run in range(1, 9):
        _, laid = grow(run)
        for blk in laid:
            move = blk["move"]
            if move is None:
                continue
            for a, b in zip(move.legs, move.legs[1:]):
                assert math.dist(a["to"], b["frm"]) < 1e-6
            assert math.dist(move.at(0.0), move.frm) < 1e-6
            assert math.dist(move.at(move.dur), move.to) < 1e-6


# -- the shape of a run -----------------------------------------------------

def test_the_course_climbs():
    """A tower where "went down a bit" is a variation rather than a failure is
    not a tower. Measured over three hundred blocks a run."""
    for run in range(1, 13):
        course, laid = grow(run, 300)
        gained = course.blocks[-1]["y"] - laid[0]["y"]
        assert gained / 300 > 0.3, f"run {run} climbed {gained} in 300 blocks"


def test_the_course_is_either_outside_the_wall_or_in_a_room():
    """Never *in* it. The building is one cell thick, so the only legal places
    for a landing are the band outside it and the interior of a ring -- and the
    interior only through an archway, which is what the next test checks."""
    for run in range(1, 9):
        course, _ = grow(run)
        for blk in course.blocks:
            if blk["form"] == "floor":
                continue          # a gallery or a hall floor *is* the building
            wall = course.tower.radius_at(blk["y"])
            r = math.hypot(blk["x"], blk["z"])
            if r > wall - 0.5:
                continue                      # outside, in the course's band
            # Inside, so it must be in a *room*: between that ring's floor and
            # its ceiling. A block out over the oculus is allowed and welcome --
            # a stepping stone with the shaft under it is the best thing in the
            # room -- and only ``floor`` landings need something solid beneath
            # them, which the occupancy test refuses there anyway.
            base = course.tower.tier_base(course.tower.tier_of(blk["y"]))
            assert base - 1 <= blk["y"] < base + tp.TIER_H - 1, \
                f"run {run}: indoor block at y={blk['y']} against base {base}"


def test_a_run_goes_indoors():
    """The interiors are the point of the arcade, and nothing else in the suite
    would notice if they silently stopped happening."""
    spells = 0
    for run in range(1, 13):
        course, laid = grow(run, 300)
        wall = course.tower.radius_at
        inside = [math.hypot(b["x"], b["z"]) < wall(b["y"]) - 0.5 for b in laid]
        spells += sum(1 for a, b in zip(inside, inside[1:]) if b and not a)
    assert spells >= 6, f"only {spells} interiors in twelve runs"


def test_the_course_never_stays_indoors():
    """A room is a change of subject, not a destination. Its floor is flat, so
    a course that settles in one stops climbing -- measured at fifty-seven
    blocks in a single room before ``INDOOR_MAX`` existed."""
    for run in range(1, 13):
        course, laid = grow(run, 300)
        wall = course.tower.radius_at
        longest = spell = 0
        for b in laid:
            if math.hypot(b["x"], b["z"]) < wall(b["y"]) - 0.5:
                spell += 1
                longest = max(longest, spell)
            else:
                spell = 0
        assert longest <= 44, f"run {run} spent {longest} blocks indoors"


def test_the_ramp_makes_later_hops_longer_and_then_holds():
    """Reported on the *mean*: a hop length is one of a handful of discrete
    values, so the median snaps between modes and can move the wrong way
    between two samples that differ by a few per cent."""
    early: list[float] = []
    late: list[float] = []
    for run in range(1, 13):
        _, laid = grow(run, 300)
        for blk in laid:
            move = blk["move"]
            if move is None or move.kind != "hop":
                continue
            d = math.dist((move.frm[0], move.frm[2]), (move.to[0], move.to[2]))
            (early if blk["laid"] < 40 else late).append(d)
    assert sum(late) / len(late) > sum(early) / len(early)


def test_a_run_visits_several_themed_rings():
    for run in range(1, 9):
        _, laid = grow(run, 300)
        names = [b["theme"] for b in laid]
        assert len(set(names)) >= 3
        # ...and never the same theme twice in a row across a floor boundary.
        seen = [k for k, _ in zip(names, names[1:]) if k != _]
        assert all(a != b for a, b in zip(seen, seen[1:]))


def test_every_set_piece_can_actually_happen():
    """A vocabulary entry that never fires is a vocabulary entry that is
    broken, and nothing else in the suite would notice."""
    fired: Counter = Counter()
    for run in range(1, 25):
        _, laid = grow(run, 300)
        fired.update(b["segment"] for b in laid)
    missing = set(tp.SEGMENTS) - set(fired)
    assert not missing, f"never generated: {sorted(missing)}"


def test_a_seed_replays_exactly():
    def fingerprint(run: int):
        _, laid = grow(run, 120)
        return [(b["x"], b["y"], b["z"], b["form"], b["style"],
                 b["move"].kind if b["move"] else None) for b in laid]

    assert fingerprint(7) == fingerprint(7)
    assert fingerprint(7) != fingerprint(8)


# -- with a body on it ------------------------------------------------------

def build_scene(run: int):
    from brainrot.engine import scene as scene_api
    from brainrot.palette import generate
    from brainrot.rng import Seed
    ensure_window()
    seed = Seed.for_run(run)
    return scene_api.build("tower", scene_api.SceneContext(
        360, 640, generate(seed), seed))


def test_every_orb_laid_down_is_collected():
    """A property of generation rather than a hope about the simulation: orbs
    are hung *on* the path the body is about to be carried through."""
    for run in (3, 11):
        scene = build_scene(run)
        for _ in range(1800):
            scene.update(1 / 60)
        assert scene.orbs > 20
        assert scene.course.orbs_missed == 0


def test_the_body_is_essentially_never_inside_the_building():
    """The block being left and the block being arrived on are exempt -- a
    slab's surface is halfway up its own cell, and both take-off and landing
    are at a block's edge. Everything else counts, and the probe measures the
    residue at about one frame in a thousand."""
    inside = frames = 0
    for run in (3, 11):
        scene = build_scene(run)
        for _ in range(1200):
            scene.update(1 / 60)
            frames += 1
            blocks = scene.course.blocks
            ends = [blocks[scene.index]]
            if scene.phase == "move" and scene.index + 1 < len(blocks):
                ends.append(blocks[scene.index + 1])
            own = {c for b in ends
                   for c in tp._footprint(b["x"], b["y"], b["z"], b["form"])}
            floor = tp._floor(scene.pos[1] + 0.05)
            for cell in tp.body_cells(*scene.pos):
                if cell[1] >= floor and cell not in own \
                        and cell in scene.course.solid:
                    inside += 1
                    break
    assert inside / frames < 0.01, f"{inside} of {frames} frames"


def test_the_body_never_stops():
    """Thirty per cent of frames stationary is what made the flat scene read as
    a slideshow. Here a ladder has no horizontal component at all, so the test
    is on three-dimensional speed."""
    frozen = frames = 0
    scene = build_scene(5)
    prev = list(scene.pos)
    for _ in range(1800):
        scene.update(1 / 60)
        if math.dist(prev, scene.pos) * 60 < 0.05:
            frozen += 1
        prev = list(scene.pos)
        frames += 1
    assert frozen / frames < 0.01


def test_drawing_the_same_state_twice_draws_the_same_picture():
    """Every screenshot this scene is judged from is captured by presenting a
    frame a second time, so ``draw`` must not advance anything."""
    from brainrot.engine import rl
    window = ensure_window()
    scene = build_scene(9)
    for _ in range(240):
        scene.update(1 / 60)

    def frame():
        # Through ``present``, because a read-back shows the buffer the swap
        # chain has finished with -- one frame behind on a GPU, two on Mesa
        # under a compositor -- so a single draw reads back the frame before.
        window.present(scene.draw)
        return rl.capture_frame()

    frame()
    assert frame() == frame()


def test_the_translucent_draws_would_hide_the_tower_without_their_guard():
    """The scene's own version of ``tools/depth_probe.py``'s depth instrument.

    A blend mode changes how a fragment is combined, not whether it is
    recorded: a cloud shelf or a column of water stamps its whole quad into the
    depth buffer anyway, and everything drawn afterwards and further away is
    then rejected. In this scene that would be most of the building, and the
    symptom is missing geometry with nothing pointing at what removed it.

    Rendered twice -- once as the scene draws it, once with ``no_depth_write``
    neutered so those draws record depth again -- and the frames must *differ*.
    Identical frames mean the guard is doing nothing, which is either a scene
    with no translucent draw left in it or a guard somebody has removed.
    """
    from brainrot.engine import fx, rl
    window = ensure_window()
    scene = build_scene(4)
    for _ in range(420):
        scene.update(1 / 60)

    # A few different moments, because the guard only has something to guard
    # when a translucent draw is actually on screen -- and a frame taken deep
    # inside the building may have neither a cloud nor a column of water in it.
    for extra in (0, 120, 240):
        for _ in range(extra):
            scene.update(1 / 60)
        if _differs(window, scene):
            return
    raise AssertionError("no translucent draw is being guarded at all")


def _differs(window, scene) -> bool:
    from brainrot.engine import fx, rl
    window.present(scene.draw)
    guarded = rl.capture_frame()

    class _passthrough:
        def __enter__(self):
            rl.flush()
            return self

        def __exit__(self, *exc):
            rl.flush()

    real, fx.no_depth_write = fx.no_depth_write, _passthrough
    import brainrot.scenes.tower as tower_mod
    tower_mod.no_depth_write = _passthrough
    try:
        window.present(scene.draw)
        unguarded = rl.capture_frame()
    finally:
        fx.no_depth_write = real
        tower_mod.no_depth_write = real
    return guarded != unguarded
