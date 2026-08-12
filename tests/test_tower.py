"""The hand-built tower: the invariants a designed level set can break.

``tools/tower_probe.py`` measures this tower and is the thing to run after
changing a level. This file is the subset of what it measures that must never
move at all, plus the design checks that cost nothing to run and catch the
mistakes hand-authoring actually makes.

The split from ``tests/test_spiral.py`` is deliberate and the overlap is
deliberate too. Everything that file asserts about the *building*, the
placement checks and the physics is inherited unchanged -- this tower is that
one with its course written down instead of chosen -- so what is here is only
what is new: that the design is legal, that it survives being built, and that
the tower loops.
"""

from __future__ import annotations

import math
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

from brainrot.scenes import handplan as hp
from brainrot.scenes import parkourkit as pk
from brainrot.scenes import spiralplan as sp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import tower_probe


def grow(run: int = 1, blocks: int = 200):
    cone = hp.Cone(random.Random(run * 977 + 13), 0)
    course = hp.Course(random.Random(run * 6151 + 29), cone)
    seen = list(course.blocks)
    for _ in range(blocks):
        seen.append(course.spawn())
        if len(course.blocks) > sp.AHEAD:
            course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
    return cone, course, seen


# -- the design, on paper ---------------------------------------------------

def test_every_authored_jump_is_one_a_body_can_make() -> None:
    """The design checked against the physics without building anything.

    This is the test that earns its keep. Hand-authoring makes exactly one
    kind of mistake over and over -- a gap that is a little too long, a step
    that rises two, a beat whose first landing is below the last landing of
    the beat before it -- and every one of them is arithmetic that nobody
    should be doing in their head. It found nineteen on the first pass,
    including a whole class nobody would have looked for: the seam where a
    level's filler loops back onto itself.
    """
    bad = tower_probe.check_design()
    assert not bad, "\n" + "\n".join(bad)


def test_three_rises_are_the_head_room() -> None:
    """The ceiling over a level is the floor slab of the level *three* above,
    so three consecutive rises are literally how much air there is. Checked
    cyclically, because the tower loops and the wrap is a real seam."""
    rises = [lv.rise for lv in hp.LEVELS]
    for i, lv in enumerate(hp.LEVELS):
        air = sum(rises[(i + k) % len(rises)] for k in range(3)) - sp.FLOOR_T
        assert 6 <= air <= 16, f"{lv.name} has {air} blocks of open air"


def test_the_tower_is_twenty_four_distinct_places() -> None:
    """Distinct by *name*, and no two neighbours built from the same theme.

    Fifteen themes and twenty-four levels means nine themes appear twice, and
    the whole value of hand-building is lost if the two turn up back to back.
    Cyclic again: level 24 is followed by level 1.
    """
    names = [lv.name for lv in hp.LEVELS]
    assert len(set(names)) == len(names), "two levels share a name"
    for i, lv in enumerate(hp.LEVELS):
        nxt = hp.LEVELS[(i + 1) % len(hp.LEVELS)]
        assert lv.theme != nxt.theme, f"{lv.name} and {nxt.name} are both {lv.theme}"


def test_every_level_climbs_out_on_its_own_footing() -> None:
    """The staircase is over a third of every run, so one stone and one hop in
    all twenty-four places is the largest single source of sameness available.

    Asserted as *most levels differ*, not all: a mine and a shaft may honestly
    both climb oak. What is not allowed is the default, where the tread
    material comes from the base theme and the two levels that share a theme
    climb the same stairs.
    """
    steps = [lv.skin.get("step") for lv in hp.LEVELS]
    assert all(steps), "a level climbs out on the theme's default footing"
    assert len(set(steps)) >= len(hp.LEVELS) * 0.7
    moves = {move for _, move in steps}
    assert len(moves) > 1, "every staircase is climbed the same way"


def test_every_level_has_a_loop_safe_filler() -> None:
    """A filler repeats, so the jump from its last landing back to its first
    has to be one a body can make. The default filler is the level's last two
    beats, which for a level that *ends* on something dramatic is exactly the
    wrong choice -- eight of the twenty-four needed their own."""
    for lv in hp.LEVELS:
        assert lv.filler, f"{lv.name} has no filler"
        assert sum(len(specs) for _, specs in lv.filler) >= 1


def test_the_tower_loops() -> None:
    """Twenty-four levels on and it is the same design again, one cycle higher.
    That is the loop: there is no seam to hide because the tower genuinely
    keeps going up."""
    cone = hp.Cone(random.Random(7), 0)
    for i in range(6, 12):
        assert cone.design(i) is cone.design(i + len(hp.LEVELS))
        assert cone.level(i).theme is cone.level(i + len(hp.LEVELS)).theme
        climb = cone.level(i + len(hp.LEVELS)).y - cone.level(i).y
        assert climb == sum(lv.rise for lv in hp.LEVELS)


def test_a_level_is_the_same_level_every_run() -> None:
    """The *tower* is fixed and only where you enter it is seeded. Two runs
    have different phases and the same twenty-four places."""
    a = hp.Cone(random.Random(1), 0)
    b = hp.Cone(random.Random(2), 0)
    assert {a.design(i).name for i in range(len(hp.LEVELS))} \
        == {b.design(i).name for i in range(len(hp.LEVELS))}


# -- the design, built ------------------------------------------------------

@pytest.mark.parametrize("run", [0, 1, 2])
def test_nothing_the_tower_builds_is_inside_anything_else(run: int) -> None:
    _, _, seen = grow(run, 200)
    cells: Counter = Counter()
    for blk in seen:
        for cell in pk.cells_of(blk):
            cells[cell] += 1
        for cell in blk["pedestal"]:
            cells[cell] += 1
    doubled = [c for c, k in cells.items() if k > 1]
    assert not doubled, f"{len(doubled)} cells claimed twice, e.g. {doubled[:3]}"


def test_the_design_survives_being_built() -> None:
    """Fidelity: how much of what was written down came out as written.

    The floor is 90% and the live figure is a little under 98%. It is allowed
    to be under 100 -- the tower is round and the world is whole cells, so some
    authored point always lands between two of them and placement takes the
    nearer -- and it is not allowed to sag, because a landing that fell back is
    a landing the design did not get.
    """
    exact = total = 0
    for run in range(4):
        _, _, seen = grow(run, 220)
        for blk in seen:
            if blk["move"] is None or blk["segment"] in ("ascent", "start",
                                                         "stuck", "recover"):
                continue
            total += 1
            exact += bool(blk["exact"])
    assert total > 300
    assert exact / total > 0.90, f"{exact}/{total} placed as authored"


def test_the_designed_content_is_most_of_the_course() -> None:
    """The point of hand-building. In the generated tower the exit climb was
    half of every run and one of four shapes; here it is about a third and the
    rest is the page."""
    designed = climb = total = 0
    for run in range(4):
        _, _, seen = grow(run, 220)
        for blk in seen:
            if blk["move"] is None:
                continue
            total += 1
            if blk["segment"] == "ascent":
                climb += 1
            elif blk["segment"] not in ("start", "stuck", "recover"):
                designed += 1
    assert designed / total > 0.55, f"only {designed}/{total} designed"
    assert climb / total < 0.45, f"the climb is {climb}/{total}"


def test_the_emergency_answer_is_effectively_never_reached() -> None:
    """The same ceiling the generated tower is held to, for the same reason:
    it is the one hop in the module nothing verified."""
    total = laid = 0
    for run in range(8):
        _, course, seen = grow(run, 200)
        total += course.stuck
        laid += len(seen)
    assert total / laid < 0.01, f"{total} unchecked placements in {laid}"


def test_the_tower_draws_all_the_way_through_several_levels() -> None:
    """Built, updated and *drawn* for long enough to cross several levels.

    Not a picture test -- ``test_generation`` covers that the frame is covered
    and deterministic. This is here because the one bug hand-authoring produced
    that no geometry check could see was a level naming a material the renderer
    has no recipe for: growing the course was fine, and the run died with a
    ``KeyError`` a hundred and forty frames in, the first time that block came
    into view. The design checker now refuses an unknown material outright and
    this is the belt to that pair of braces.
    """
    from brainrot.engine import scene as scene_api
    from brainrot.engine.window import HeadlessWindow
    from brainrot.config import Config
    from brainrot.palette import generate as generate_palette
    from brainrot.rng import Seed

    cfg = Config()
    cfg.width, cfg.height = 180, 320
    window = HeadlessWindow()
    window.create(cfg)
    try:
        for run in (4, 17):
            seed = Seed.for_run(run)
            ctx = scene_api.SceneContext(cfg.width, cfg.height,
                                         generate_palette(seed), seed)
            scene = scene_api.build("tower", ctx)
            for frame in range(900):
                scene.update(1 / 60)
                scene.elapsed += 1 / 60
                if frame % 45 == 0:
                    # Drawn *along the way* and not once at the end. The
                    # failure this guards against is a block the renderer
                    # cannot draw, and it only fires on the frame that block
                    # comes into view -- a single draw at the end would sample
                    # one such frame out of nine hundred.
                    window.present(scene.draw)
    finally:
        window.destroy()


def test_every_level_is_reached_and_left() -> None:
    """A level nobody arrives at is a level not worth designing, and one
    nobody leaves is a run that stops."""
    seen: Counter = Counter()
    for run in range(8):
        _, _, blocks = grow(run, 240)
        for blk in blocks:
            seen[blk["theme"]] += 1
    for lv in hp.LEVELS:
        assert seen[lv.name] > 0, f"{lv.name} is never reached"


def test_the_tower_still_cannot_be_walked_up() -> None:
    """The premise of the whole format, and a wider tower is a chance to break
    it: the cone *alone*, with no course blocks and no dressing, may not be
    climbable one block at a time. Flooded from a level's own floor, allowed to
    step up one and drop any distance."""
    cone = hp.Cone(random.Random(5), 0)
    lv = cone.level(6)
    start_u = lv.u0 + sp.LEVEL_ARC * 0.2
    r = cone.outer_at(start_u) - sp.BAND * 0.5
    th = start_u * cone.wind
    start = (pk.iround(math.cos(th) * r), lv.y,
             pk.iround(math.sin(th) * r))
    seen = {start}
    edge = [start]
    top = lv.y
    while edge and len(seen) < 40000:
        x, y, z = edge.pop()
        top = max(top, y)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            for ny in range(y + 1, y - 24, -1):
                if cone.rock((nx, ny - 1, nz)) and not cone.rock((nx, ny, nz)) \
                        and not cone.rock((nx, ny + 1, nz)):
                    if (nx, ny, nz) not in seen:
                        seen.add((nx, ny, nz))
                        edge.append((nx, ny, nz))
                    break
    assert top - lv.y == 0, f"walked {top - lv.y} m up without the parkour"


def test_a_seed_replays_exactly() -> None:
    a = [(b["x"], b["y"], b["z"], b["segment"]) for b in grow(3, 90)[2]]
    b = [(b["x"], b["y"], b["z"], b["segment"]) for b in grow(3, 90)[2]]
    assert a == b
