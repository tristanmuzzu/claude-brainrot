"""Continuous clearance and progression regressions for the tower course."""

import math
import random

import pytest

from brainrot.scenes import handplan as hp
from brainrot.scenes import parkourkit as pk
from brainrot.scenes import spiralplan as sp


def test_swept_arc_checks_the_exact_apex_and_corner():
    # The apex is between samples and the head enters the beam by just 1 mm.
    leg = {"kind": "arc", "frm": (0., 0., 0.), "to": (4., 0., 0.),
           "dur": 2 * pk.JUMP_V / pk.GRAVITY, "vy0": pk.JUMP_V}
    move = pk.Move("hop", [leg])
    top = pk.JUMP_V ** 2 / (2 * pk.GRAVITY) + pk.BODY_H
    assert move.intersects_box((1.9, top - .001, -.5), (2.1, top + 1, .5))
    assert not move.intersects_box((1.9, top + .001, -.5), (2.1, top + 1, .5))
    diagonal = pk.Move("walk", [pk.line_leg((0., 1., 0.), (3., 1., 3.), 5.)])
    assert (1, 1, 0) in diagonal.swept_cells()
    assert (0, 0, 0) not in diagonal.swept_cells()  # touching the floor is legal


def test_swept_cells_cover_dense_independent_samples():
    for rise in (-3., -1., 0., 1.):
        leg = pk.arc_leg((0., 4., 0.), (3., 4. + rise, 2.))
        move = pk.Move("hop", [leg])
        cells = move.swept_cells()
        for i in range(2001):
            t = leg["dur"] * i / 2000
            x, z = 3 * i / 2000, 2 * i / 2000
            y = 4 + leg["vy0"] * t - .5 * pk.GRAVITY * t * t
            assert set(pk.body_cells(x, y, z)) <= cells


def test_retired_drawn_terrain_and_transparent_blocks_stay_solid():
    course = hp.Course(random.Random(29), hp.Cone(random.Random(13), 0))
    old = course.blocks[0]
    support = (1000, 20, 1000)
    course.write(support, "oak")
    old["pedestal"] = (support,)
    course.advance(sp.TRAIL + 1)
    assert course.blocked(support)
    for index, style in enumerate(("glass", "leaves", "scaffold")):
        cell = (1000 + index, 30, 1000)
        course.write(cell, style)
        assert course.blocked(cell)


def test_landing_keeps_its_turn_when_below_the_next_terrace():
    cone = hp.Cone(random.Random(13), 0)
    course = hp.Course(random.Random(29), cone)
    lv = cone.level(25)
    u = lv.u0 + .1
    r = sum(cone.floor_range(u)) / 2
    x, z = round(math.cos(u * cone.wind) * r), round(math.sin(u * cone.wind) * r)
    course.u = u
    block = course._block(x, lv.y - 3, z, "stone", "full", (1, 0), "ascent")
    assert abs(course.u_of(block) - u) < .1
    course.u += math.tau
    assert abs(course.u_of(block) - u) < .1


@pytest.mark.parametrize("run, count", [(0, 1200), (1, 1200), (2, 3000), (3, 3000), (4, 3000)])
def test_each_run_completes_every_level_without_unchecked_jumps(run, count):
    cone = hp.Cone(random.Random(run * 977 + 13), 0)
    course = hp.Course(random.Random(run * 6151 + 29), cone)
    start = cone.level_index(course.u_of(course.blocks[0]))
    levels = set()
    previous = course.blocks[0]
    seen = list(course.blocks[1:])
    for _ in range(count):
        seen.append(course.spawn())
        course.advance(max(0, len(course.blocks) - sp.AHEAD + sp.TRAIL))
    for block in seen:
        progress = course.u_of(block) - course.u_of(previous)
        if progress <= 0:
            assert progress * course.radius_of(previous) >= -3.0
            assert course.surface(block) > course.surface(previous)
            assert cone.level_index(course.u_of(block)) == cone.level_index(course.u_of(previous))
        assert course.surface(previous) - course.surface(block) <= 3.0
        assert not previous["unchecked"], (run, previous["laid"], previous["theme"])
        move = previous["move"]
        for leg in move.legs:
            if leg["kind"] == "arc" and move.kind in ("hop", "slide"):
                assert pk.VY_MIN <= leg["vy0"] <= pk.VY_MAX
                assert leg["dur"] >= leg["vy0"] / pk.GRAVITY
        levels.add(cone.level_index(course.u_of(block)))
        previous = block
    assert set(range(start + 1, start + len(hp.LEVELS) + 1)) <= levels
    assert course.stuck == 0


def test_clearance_checks_structures_between_samples():
    from types import SimpleNamespace

    course = object.__new__(sp.Course)
    course.solid = {(1, 1, 0)}
    course.struct, course._rock = {}, {}
    course.carved, course._hold_cells = set(), set()
    course.blocks = []
    course.cone = SimpleNamespace(rock=lambda cell: False, rim_at=lambda y: -100.)
    move = pk.Move("walk", [pk.line_leg((0., 1., 0.), (3., 1., 3.), 5.)])
    assert not course._path_clear(move, set())
    course.solid.clear()
    assert course._path_clear(move, set())
    assert not course._path_clear(move, set(), extra={(1, 1, 0)})
