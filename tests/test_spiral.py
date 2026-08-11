"""The spiral scene's invariants, stated rather than hoped for.

Split the way the scene is: everything about the *geometry* runs against
``scenes/spiralplan``, which imports no renderer, so those tests need no window
and a sweep costs a second or two. Only the tests that watch a body move build
a scene.

The numbers here are the ones ``tools/spiral_probe.py`` prints. Where a
threshold is not zero it is because the probe says it is not zero, and the
comment says what the residue is.

Several of these guard a specific defect that cost a session to find. Each one
says which, because a threshold with no story behind it is the first thing
somebody relaxes.
"""

from __future__ import annotations

import math
import random
from collections import Counter

import pytest

from brainrot.scenes import spiralplan as sp
from brainrot.scenes import towerplan as tp

from conftest import ensure_window


def grow(run: int, blocks: int = 260):
    """A course grown without a body. Returns the course and every block laid."""
    spiral = sp.Spiral(random.Random(run * 977 + 13), 0)
    course = sp.Course(random.Random(run * 6151 + 29), spiral)
    laid = list(course.blocks)
    for _ in range(blocks):
        laid.append(course.spawn())
        if len(course.blocks) > sp.AHEAD:
            course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
    return course, laid


def solid_claims(course) -> Counter:
    seen: Counter = Counter()
    for cell, style in course.struct.items():
        if style not in sp.SEE_THROUGH:
            seen[cell] += 1
    for blk in course.blocks:
        for cell in tp._footprint(blk["x"], blk["y"], blk["z"], blk["form"]):
            seen[cell] += 1
        for d in blk["deco"]:
            if d.get("solid"):
                seen[(blk["x"] + round(d["dx"]), blk["y"] + round(d["dy"]),
                      blk["z"] + round(d["dz"]))] += 1
    return seen


# -- the building -----------------------------------------------------------

def test_every_dressing_material_exists():
    """A platform's scenery is named by string, and a name the atlas has never
    heard of is a ``KeyError`` in the middle of a frame rather than anything
    the generator would notice. One typo (``sand`` for ``sandstone``) got as
    far as the second seed of a smoke run."""
    verbs = {"lamp", "post", "block", "pool", "hollow"}
    for theme, kit in sp.DRESSING.items():
        for what in kit:
            if what in verbs:
                continue
            assert what in tp.MATERIALS, f"{theme}: {what}"


def test_a_cave_has_a_way_in_and_a_way_out():
    """Five cells wide, not one. A body is 0.6 m across and plants its feet
    0.4 m off the middle of a block along the way it is going, so a one-cell
    doorway refuses every diagonal entry -- and a bridge crosses the wall line
    a metre or two to one side of the cell it is aiming at."""
    seen = 0
    for run in range(1, 9):
        spiral = sp.Spiral(random.Random(run * 977 + 13), 0)
        cells: dict = {}
        spiral.build_to(5, lambda c, s: cells.__setitem__(c, s))
        for pad in spiral.pads[:6]:
            if not pad.enclosed:
                continue
            seen += 1
            # Only the heights a body occupies: it stands 1.8 m tall on the
            # floor, and a lamp in the ceiling over the doorway is a lamp over
            # the doorway.
            for door in (pad.enter, pad.leave):
                for h in range(1, 4):
                    assert (door[0], pad.y - 1 + h, door[2]) not in cells
                    for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        at = (door[0] + ox, pad.y - 1 + h, door[2] + oz)
                        assert at not in cells or \
                            cells[at] in sp.SEE_THROUGH, at
    assert seen, "no cave in eight runs -- the fixture stopped testing anything"


def test_the_spiral_climbs_and_comes_back_round():
    spiral = sp.Spiral(random.Random(11), 0)
    pads = [spiral.pad(i) for i in range(13)]
    for a, b in zip(pads, pads[1:]):
        assert b.y > a.y, "a platform must be higher than the one before"
    first, again = pads[0], pads[sp.PADS_PER_TURN]
    assert math.dist((first.cx, first.cz), (again.cx, again.cz)) < 8.0, \
        "one revolution should come back over where it started"


def test_a_platform_lane_never_climbs_two_at_once():
    """A lane's own steps are three cells apart on purpose: landings are a hop
    apart, and nothing in the game rises two blocks in one jump."""
    for run in range(1, 7):
        spiral = sp.Spiral(random.Random(run * 977 + 13), 0)
        for i in range(8):
            pad = spiral.pad(i)
            for a, b in zip(pad.lane, pad.lane[1:]):
                assert abs(b[1] - a[1]) <= 1


# -- placement --------------------------------------------------------------

def test_nothing_is_ever_inside_anything_else():
    for run in range(1, 9):
        course, _ = grow(run)
        worst = [c for c, n in solid_claims(course).items() if n > 1]
        assert not worst, f"run {run}: {worst[:4]}"


def test_every_block_is_on_a_whole_cell():
    for run in range(1, 7):
        _, laid = grow(run)
        for blk in laid:
            assert all(float(blk[k]).is_integer() for k in "xyz")


def test_the_emergency_answer_is_effectively_never_reached():
    """The one unchecked placement. It started at 13% of nodes; the fixes are
    recorded in ``spiralplan`` where they live. The probe reads 0.19% over
    40 runs x 400 blocks, so half a per cent is a ceiling with room in it and
    not a number to relax."""
    stuck = laid = 0
    for run in range(1, 13):
        course, blocks = grow(run, 300)
        stuck += course.stuck
        laid += len(blocks)
    assert stuck / laid < 0.005, f"{stuck} of {laid}"


def test_every_hop_is_one_a_body_can_make():
    """Vanilla's numbers, not a table of gaps. The exemption is the unchecked
    answer, which is counted separately above."""
    for run in range(1, 7):
        _, laid = grow(run)
        for blk in laid:
            move = blk["move"]
            if move is None or blk["unchecked"] or move.kind != "hop":
                continue
            leg = move.legs[0]
            assert tp.VY_MIN <= leg["vy0"] <= tp.VY_MAX
            assert tp.AIR_MIN <= leg["dur"] <= tp.AIR_MAX
            flat = math.dist((move.frm[0], move.frm[2]),
                             (move.to[0], move.to[2]))
            assert flat >= tp.MIN_HOP - 1e-6


def test_the_band_agrees_with_the_move_it_is_planning():
    """``_band`` converts ``hop_span`` from take-off points to cell centres,
    and it has to account for the *direction*: the feet plant against a
    block's face, so running into a corner they plant 1.41 times as far out as
    running into a side. Ignoring that is worth nearly half a metre, and the
    band for a hop that climbs a block is only a metre wide -- so the plan asks
    for steps the physics does not have about one time in three."""
    course, _ = grow(2, 40)
    prev = course.blocks[-1]
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            if dx == dz == 0:
                continue
            for rise in (-1, 0, 1):
                cell = (prev["x"] + dx, prev["y"] + rise, prev["z"] + dz)
                lo, hi = sp._band(prev["form"], "full",
                                  cell[1] + 1.0 - (prev["y"]
                                                   + tp.FORMS[prev["form"]]),
                                  dx, dz)
                if hi < lo:
                    continue
                d = math.hypot(dx, dz)
                # Exactly on an edge of the band the two agree to within
                # floating-point noise and the answer is arbitrary; what this
                # test is about is the half-metre the direction is worth.
                if min(abs(d - lo), abs(d - hi)) < 0.02:
                    continue
                inside = lo <= d <= hi
                frm = tp.takeoff_point(prev["x"], course.surface(prev),
                                       prev["z"], prev["form"], (dx, dz))
                to = tp.land_point(cell[0], cell[1] + 1.0, cell[2], "full",
                                   (dx, dz))
                leg = tp.arc_leg(frm, to)
                span = math.dist((frm[0], frm[2]), (to[0], to[2]))
                real = (span >= tp.MIN_HOP
                        and tp.VY_MIN <= leg["vy0"] <= tp.VY_MAX
                        and tp.AIR_MIN <= leg["dur"] <= tp.AIR_MAX
                        and leg["dur"] >= leg["vy0"] / tp.GRAVITY)
                assert inside == real, (dx, dz, rise, d, lo, hi)


def test_a_bridge_steps_across_onto_a_platform_and_never_up_into_it():
    """A platform's ground is two cells deep, so a landing hop that still has
    to climb crosses the lower of the two with the body's head. The bridge
    climbs beside the platform first and then walks in. Worth 0.68% of nodes
    against 0.25%."""
    for run in range(1, 9):
        _, laid = grow(run, 300)
        for prev, blk in zip(laid, laid[1:]):
            if blk["form"] != "floor" or prev["form"] == "floor":
                continue
            if blk["unchecked"] or prev["unchecked"]:
                continue
            assert blk["y"] <= prev["y"], (prev["y"], blk["y"])


def test_a_course_block_is_never_built_in_a_flight_already_solved():
    """``pathcells`` is the corridor a solved move flies through. The ring
    version only asks the *building* about it, because a course that keeps
    moving forward never lays a block where it has already agreed to fly --
    this one comes back over the same three cells every time it climbs a
    flight of steps beside a rim. Before the check, the body was inside a
    course block on 3.2% of frames, every one of them a block two to four
    ahead of the one it was standing on."""
    for run in range(1, 7):
        course, _ = grow(run, 260)
        live = course.blocks
        for i, blk in enumerate(live):
            for cell in tp._footprint(blk["x"], blk["y"], blk["z"],
                                      blk["form"]):
                for other in live[:max(0, i - 1)]:
                    assert cell not in other["path"], (run, cell)


def test_a_seed_replays_exactly():
    a, first = grow(5, 120)
    b, again = grow(5, 120)
    assert [(x["x"], x["y"], x["z"], x["style"], x["form"]) for x in first] == \
           [(x["x"], x["y"], x["z"], x["style"], x["form"]) for x in again]
    assert a.stuck == b.stuck


def test_most_of_a_run_happens_on_the_platforms():
    """The whole point of the format, and the thing the version this replaced
    got wrong: a ``floor`` landing is the platform's own ground, everything
    else is a stone the course put there. A third of the blocks and, because a
    crossing is unhurried and a bridge is not, about half the *time* -- which
    is what ``tools/spiral_probe.py`` measures and this cannot."""
    ground = total = 0
    for run in range(1, 9):
        _, laid = grow(run, 300)
        total += len(laid)
        ground += sum(1 for b in laid if b["form"] == "floor")
    assert ground / total > 0.28, ground / total


def test_a_run_meets_several_different_places():
    for run in range(1, 5):
        spiral = sp.Spiral(random.Random(run * 977 + 13), 0)
        names = {spiral.pad(i).theme.name for i in range(9)}
        assert len(names) >= 6, names


def test_every_bridge_style_can_actually_happen():
    seen: Counter = Counter()
    for run in range(1, 13):
        _, laid = grow(run, 300)
        seen.update(b["segment"] for b in laid)
    for style in sp.BRIDGES:
        assert seen[style] > 0, style


# -- with a body ------------------------------------------------------------

def build_scene(run: int):
    from brainrot.engine import scene as scene_api
    from brainrot.palette import generate as generate_palette
    from brainrot.rng import Seed
    ensure_window()
    seed = Seed.for_run(run)
    ctx = scene_api.SceneContext(360, 640, generate_palette(seed), seed)
    return scene_api.build("spiral", ctx)


@pytest.mark.parametrize("run", (1, 4))
def test_every_orb_laid_down_is_collected(run: int):
    scene = build_scene(run)
    for _ in range(int(30 / (1 / 60))):
        scene.update(1 / 60)
    assert scene.course.orbs_missed == 0
    assert scene.orbs > 10


@pytest.mark.parametrize("run", (2, 6))
def test_the_body_is_never_inside_the_building(run: int):
    """Zero, and it stays zero. The ring version carries a residue of 0.33% of
    frames from structure built after an arc was solved; this scene reserves
    the flight path against its own blocks as well, and the probe reads 0 over
    27,000 frames."""
    scene = build_scene(run)
    worst = 0.0
    for _ in range(int(20 / (1 / 60))):
        scene.update(1 / 60)
        x, y, z = scene.pos
        feet = tp._floor(y + 0.05)
        blocks = scene.course.blocks
        ends = [blocks[scene.index]]
        if scene.phase == "move" and scene.index + 1 < len(blocks):
            ends.append(blocks[scene.index + 1])
        own = {c for b in ends
               for c in tp._footprint(b["x"], b["y"], b["z"], b["form"])}
        for cell in tp.body_cells(x, y, z):
            if cell not in scene.course.solid or cell[1] < feet or cell in own:
                continue
            worst = max(worst, min(
                0.5 + tp.BODY_HALF_W - abs(x - cell[0]),
                0.5 + tp.BODY_HALF_W - abs(z - cell[2]),
                min(y + tp.BODY_H, cell[1] + 1.0) - max(y, float(cell[1]))))
    assert worst < 0.05, worst


def test_the_body_never_stops():
    scene = build_scene(3)
    frozen = 0
    prev = list(scene.pos)
    for _ in range(int(20 / (1 / 60))):
        scene.update(1 / 60)
        if math.dist(prev, scene.pos) / (1 / 60) < 0.05:
            frozen += 1
        prev = list(scene.pos)
    assert frozen == 0, frozen


def test_a_run_goes_indoors_and_comes_out_again():
    """There is no wall to be inside of, so ``roofed`` answers the question a
    cylinder answered with a radius. Both halves matter: a scene that never
    goes in has lost the strongest beat the format has, and one that never
    comes out is a body stuck in a room."""
    inside = outside = 0
    for run in (3, 5, 7):
        scene = build_scene(run)
        for _ in range(int(40 / (1 / 60))):
            scene.update(1 / 60)
            if scene.tower.roofed(*scene.pos):
                inside += 1
            else:
                outside += 1
    assert inside > 0 and outside > inside


def test_the_platform_furniture_is_actually_drawn():
    """Crops, fences, lantern posts and chains are models rather than cells,
    so nothing about the meshed building will notice if the wiring between the
    plan and the renderer comes apart -- the platforms simply go back to being
    floors, and a contact sheet is the only thing that would say so. This
    renders a frame with the furniture and again without it and requires the
    two to differ."""
    from brainrot.engine import rl

    ensure_window()
    scene = build_scene(1)
    for _ in range(int(14 / (1 / 60))):
        scene.update(1 / 60)
    assert scene.tower.props, "no furniture was generated at all"
    scene.draw()
    scene.draw()
    with_it = rl.capture_frame()
    keep, scene.tower.props = scene.tower.props, []
    scene.draw()
    scene.draw()
    without = rl.capture_frame()
    scene.tower.props = keep
    assert with_it is not None and without is not None
    assert with_it != without
