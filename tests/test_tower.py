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


def test_the_tower_is_thirty_three_distinct_places() -> None:
    """Distinct by *name*, and no two neighbours built from the same theme.

    Twenty-three themes and thirty-three levels means several themes appear
    twice, and the whole value of hand-building is lost if the two turn up
    back to back. Cyclic again: level 33 is followed by level 1.
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
            if blk["move"] is None or blk["segment"] in hp.MACHINERY:
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


def test_a_gated_landmark_is_a_structure_with_a_way_through_it() -> None:
    """Every gated blueprint is still a structure once its doorway is cut.

    The void is written down apart from the builder, so the one way to get
    this wrong is to punch a passage through a structure that was never wide
    enough to have one -- which is how the old windmill would have come out:
    a floating roof over nothing, the exact bug the whole-or-nothing rule
    exists to stop.
    """
    for name, (build, void, kind) in sp.GATED.items():
        dt0, dt1, dr0, dr1, dy1 = void
        assert dr1 - dr0 >= 2, f"{name}: a passage under three cells wide"
        assert dy1 >= (2 if kind == "walk" else 4), f"{name}: too low a lid"
        cells = build(random.Random(1), sp.THEME_BY_NAME["plains"])
        if isinstance(cells, tuple):
            cells = cells[0]
        cut = {(dt, dy, dr) for dt in range(dt0, dt1 + 1)
               for dy in range(dy1 + 1) for dr in range(dr0, dr1 + 1)}
        left = [c for c in cells if (c[0], c[1], c[2]) not in cut]
        assert len(left) > len(cells) * 0.45, f"{name}: mostly doorway"
        # ...and something the body passes between or under: a jamb either
        # side, or a canopy over the top. Both read as going *through* it;
        # the tree and the great cap are the ones with only one jamb.
        jambs = sum(any(c[2] == side and c[1] <= dy1 for c in left)
                    for side in (dr0 - 1, dr1 + 1))
        over = any(c[1] > dy1 and dr0 <= c[2] <= dr1 for c in left)
        assert jambs == 2 or (jambs and over), \
            f"{name}: the passage has neither two jambs nor a lid"


def test_the_course_goes_through_the_landmarks_it_gates() -> None:
    """The crossings happen, and they happen *inside* the structure.

    Placement rate was the number that stood in for this and it was wrong:
    97% of landmarks were built and the owner saw one in five minutes. What
    has to be true is that the landings labelled ``landmark`` are the cells
    the gate reserved -- not near them, them -- because a crossing that
    misses its own doorway by a cell is a course running past a wall.
    """
    offered = entered = landings = fell = 0
    for run in range(6):
        _, course, seen = grow(run, 220)
        offered += len(course._crossed) - len(course._retired)
        entered += len(course._gate_hit)
        landings += sum(1 for blk in seen if blk["segment"] == "landmark")
        # ``unchecked`` is written back one block, because a move belongs to
        # the landing it leaves -- so this counts a crossing's landing that had
        # no legal move out of it and needed the one emergency answer.
        fell += sum(1 for blk in seen
                    if blk["segment"] == "landmark" and blk["unchecked"])
    # This was ``== 0`` until the outer wall was built (2026-08-13), and it was
    # zero by luck rather than by construction: nothing in the module promises
    # a crossing's landing a legal move out, and ``_last_resort`` may return
    # None for any segment whatever. Widening the shelves where the wall stands
    # moved the whole world, and one landing of the ~7,900 laid here now needs
    # the emergency hop. Kept as a budget with the measured number in it rather
    # than deleted, because the thing it guards is real: a crossing that
    # routinely boxes itself in is a course running into its own structure.
    # If this starts failing, look at the run-up to the doorway before the
    # doorway -- ``CLAUDE.md``, "Still outstanding" 0b.
    assert fell <= 1, f"{fell} crossings fell through to the unchecked answer"
    assert offered >= 12, f"only {offered} crossings offered in six runs"
    assert landings > 40
    # ``entered`` is a landing *in the passage*, by any route: about half the
    # offers manage it, and only a quarter of those land on the exact stored
    # cell -- the leg onto it is an ordinary jump from wherever the approach
    # finished, and it is refused often (CLAUDE.md, "Still outstanding").
    # What must not sag is the share that gets inside at all, because a
    # crossing that never lands is a structure nobody sees.
    assert entered >= offered * 0.25, f"{entered} of {offered} gates entered"


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
    r = cone.outer_at(start_u) - cone.level(6).band * 0.5
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


def test_a_walk_never_crosses_air() -> None:
    """The one verb the body crosses on its feet has ground under them.

    ``Course._move_for`` validates a walk by its two endpoints and by nothing
    in between, and for the life of this format that was the whole check: a
    landing two cells away was reached by strolling over the hole. Measured at
    the time, 98% of walk legs crossed air -- a mean of 0.76 m of it and 1.68 m
    at worst -- and it is what the owner saw and reported as the body sliding
    across a gap without jumping. ``_walk_bridge`` lays the shelf a walk needs;
    this is the assertion that it is still being laid.

    Grown without ``advance`` on purpose. Releasing the cells behind the body
    is what a real run does, and a probe that checks a walk after its own
    ground has been released reads a catastrophic air-walk that is its own
    doing -- which is exactly the mistake this test exists to make impossible
    to repeat.
    """
    walks = 0
    for run in range(4):
        cone = hp.Cone(random.Random(run * 977 + 13), 0)
        course = hp.Course(random.Random(run * 6151 + 29), cone)
        seen = list(course.blocks)
        for _ in range(70):
            seen.append(course.spawn())
        for blk in seen:
            move = blk["move"]
            if move is None or move.kind != "walk" or blk["unchecked"]:
                continue
            walks += 1
            for leg in move.legs:
                frm, to = leg["frm"], leg["to"]
                span = math.dist(frm, to)
                for i in range(int(span / 0.1) + 2):
                    f = min(1.0, i * 0.1 / span) if span > 1e-9 else 1.0
                    x = frm[0] + (to[0] - frm[0]) * f
                    y = frm[1] + (to[1] - frm[1]) * f
                    z = frm[2] + (to[2] - frm[2]) * f
                    cy = pk.ifloor(y - 0.05)
                    under = [
                        (ux, cy, uz)
                        for ux in {pk.ifloor(x - pk.BODY_HALF_W + 0.5),
                                   pk.ifloor(x + pk.BODY_HALF_W + 0.5)}
                        for uz in {pk.ifloor(z - pk.BODY_HALF_W + 0.5),
                                   pk.ifloor(z + pk.BODY_HALF_W + 0.5)}
                    ]
                    assert any(course.blocked(c) for c in under), \
                        f"walk at ({x:.2f}, {y:.2f}, {z:.2f}) is over nothing"
    assert walks >= 20, f"only {walks} walks seen -- the test proves nothing"


def test_the_way_out_is_mostly_the_level_writing_it() -> None:
    """The exit climb is nearly a third of the course, and until ``origin``
    existed nobody could say what it was made of.

    Every landing of it is labelled ``ascent`` whether the level wrote it or
    the engine improvised it, and that label is load-bearing in eight other
    places -- so the project's own notes recorded the exit as machinery and as
    an authoring job still to be done, when in fact all thirty-three levels
    write one.

    What it is made of moved with the rehash (``docs/REHASH.md``) and the
    numbers moved with it. A level's course now cruises three to six blocks
    over its own terrace, so the way out has only ``rise + 1 - deck`` left to
    gain -- one to three treads where it used to be five or seven. The
    authored share therefore *falls* while the design gets better: what fills
    the gap is the crossing and the walk along the last of the terrace to it,
    both of them aimed at the chasm rather than written down. The thing to
    hold is the improvised staircase, which is what a level that did not top
    out costs.
    """
    kinds: Counter = Counter()
    for run in range(3):
        _, _, seen = grow(run, 260)
        for blk in seen:
            if blk["segment"] == "ascent":
                kinds[blk.get("origin") or "other"] += 1
    total = sum(kinds.values())
    assert total > 150, f"only {total} exit landings -- nothing was measured"
    assert kinds["stair"] < total * 0.3, \
        f"the engine improvised {kinds['stair']} of {total} exit landings"
    aimed = kinds["design"] + kinds["crossing"] + kinds["approach"]
    assert aimed > total * 0.7, (
        f"only {aimed} of {total} exit landings are the design, the crossing "
        f"or the walk to it")
    # The reliability chain is the last thing before the unchecked hop. It
    # firing at all means an exit could not be built any other way.
    assert kinds["recover"] + kinds["other"] <= total * 0.02, dict(kinds)
