"""The spiral tower: the invariants, stated so they cannot quietly lapse.

``tools/spiral_probe.py`` measures this scene in numbers and is the thing to
run after changing it. This file is the subset of those numbers that must
never move at all, in a form that fits in the suite.

The split is deliberate. A probe answers "how good is it"; a test answers "is
it still correct". Two things can only ever be zero -- two solid things in one
cell, and a landing off the lattice -- and a handful more have a ceiling that
is a promise rather than a measurement.
"""

from __future__ import annotations

import math
import random
from collections import Counter

import pytest

from brainrot.scenes import parkourkit as pk
from brainrot.scenes import spiralplan as sp


def cone(run: int = 1) -> sp.Cone:
    return sp.Cone(random.Random(run * 977 + 13), 0)


def grow(run: int = 1, blocks: int = 160):
    """A course grown without a body, collecting every landing as it is laid.

    Collected on the way past rather than read off the end, because the course
    keeps nineteen at a time and anything read afterwards is a sample of the
    last nineteen.
    """
    c = cone(run)
    course = sp.Course(random.Random(run * 6151 + 29), c)
    seen = list(course.blocks)
    for _ in range(blocks):
        seen.append(course.spawn())
        if len(course.blocks) > sp.AHEAD:
            course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
    return course, seen


# ---------------------------------------------------------------------------
# The cone
# ---------------------------------------------------------------------------

def test_the_trough_is_walkable_all_the_way_round() -> None:
    """Ground under the feet, air where the body is, a ceiling within one turn.

    The whole format rests on :meth:`Cone.rock` and its first draft had two
    branches that :meth:`Cone.unwrap` made unreachable -- which produced a
    smooth cylinder with the themes painted on as stripes and nothing to run
    along. This is the test that would have caught it in a second.
    """
    bad_air = bad_ground = bad_ceiling = samples = 0
    for run in range(4):
        c = cone(run)
        for i in range(120):
            u = -4.0 + i * 0.32
            yf = c.floor_at(u)
            out = c.outer_at(u)
            th = u * c.wind
            ct, st = math.cos(th), math.sin(th)
            # Sampled across the lane the course may actually use, not the
            # raw band. The band's edges are ragged by construction -- the rim
            # wobbles and the core is round -- and a cell centre rounded up
            # against either one is the world working, not a hole in it.
            lo = out - sp.BAND + sp.BAND_MARGIN
            hi = out - sp.BAND_MARGIN
            for frac in (0.2, 0.5, 0.8):
                r = lo + (hi - lo) * frac
                x, z = pk.iround(ct * r), pk.iround(st * r)
                samples += 1
                # Each cell against *its own* floor, not against the sample's.
                # The trough is a staircase -- a block every eight of arc --
                # so the cell just past a step has its floor one higher, and
                # the cell at the old height is that step's riser and is
                # rightly solid. Asking every cell about one shared floor
                # measures the staircase and calls it a hole: 2.8% of samples,
                # all of them the world working correctly.
                cyf = c.floor_at(c.unwrap(x, z, yf + 1))
                if c.rock((x, cyf, z)) or c.rock((x, cyf + 1, z)):
                    bad_air += 1
                if not c.rock((x, cyf - 1, z)):
                    bad_ground += 1
                if not any(c.rock((x, cyf + h, z)) for h in
                           range(sp.TURN_RISE - sp.FLOOR_T, sp.TURN_RISE + 1)):
                    bad_ceiling += 1
    assert samples > 1000
    assert bad_air / samples < 0.005, f"{bad_air} of {samples} not standable"
    assert bad_ground / samples < 0.005, f"{bad_ground} of {samples} unsupported"
    assert bad_ceiling == 0, "the trough is open to the sky somewhere"


def test_the_cone_is_analytic() -> None:
    """The same cell is the same answer every time it is asked.

    This is what lets the building have no memory, and it is what removed the
    entire class of bug where a wall was built through a jump that had already
    been solved.
    """
    c = cone(5)
    rng = random.Random(4)
    cells = [(rng.randint(-40, 40), rng.randint(-30, 90), rng.randint(-40, 40))
             for _ in range(2000)]
    first = {cell: c.rock(cell) for cell in cells}
    rng.shuffle(cells)
    assert all(c.rock(cell) == first[cell] for cell in cells)
    assert any(first.values()), "nothing at all is rock"
    assert not all(first.values()), "everything is rock"


def test_the_tower_flares_as_it_rises() -> None:
    """An inverted cone, which is the reference's whole silhouette."""
    c = cone(2)
    assert c.rim_at(200) > c.rim_at(0) > c.rim_at(-50) > 0


def test_the_trough_floor_is_always_a_whole_number() -> None:
    """A helix that climbs continuously puts the walking surface three quarters
    of the way up a cell, and every hop off it is then solved against a height
    no block has."""
    c = cone(3)
    for i in range(400):
        assert isinstance(c.floor_at(-6.0 + i * 0.1), int)


def test_one_turn_of_the_helix_is_exactly_turn_rise() -> None:
    c = cone(6)
    for u in (-3.0, 0.0, 2.5, 11.0):
        assert c.floor_at(u + 2 * math.pi) - c.floor_at(u) == sp.TURN_RISE


def test_sections_tile_the_helix_without_gaps() -> None:
    c = cone(7)
    c.section_at(30.0)
    for a, b in zip(c.sections, c.sections[1:]):
        assert a.u1 == b.u0
        assert b.u1 > b.u0


def test_no_two_sections_running_are_the_same_theme() -> None:
    c = cone(8)
    c.section_at(40.0)
    for a, b in zip(c.sections, c.sections[1:]):
        assert a.theme is not b.theme


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run", [1, 2, 3])
def test_nothing_the_course_builds_is_inside_anything_else(run: int) -> None:
    course, seen = grow(run, 200)
    cells: Counter = Counter()
    for blk in seen:
        for cell in pk.cells_of(blk):
            cells[cell] += 1
        for cell in blk["pedestal"]:
            cells[cell] += 1
    doubled = [c for c, n in cells.items() if n > 1]
    assert not doubled, f"{len(doubled)} cells claimed twice, e.g. {doubled[:3]}"


@pytest.mark.parametrize("run", [1, 2, 3])
def test_every_landing_is_on_a_whole_cell(run: int) -> None:
    _, seen = grow(run, 200)
    for blk in seen:
        assert all(isinstance(v, int) for v in (blk["x"], blk["y"], blk["z"]))


def test_the_emergency_answer_is_effectively_never_reached() -> None:
    """``stuck`` counts the one hop in the module nothing verified.

    It is allowed to be non-zero -- the alternative is a generator that can
    deadlock -- and it is not allowed to be common. The ceiling here is well
    above what it measures, so that an ordinary bad seed does not fail the
    suite and a regression of any size does.
    """
    total = laid = 0
    for run in range(6):
        course, seen = grow(run, 150)
        total += course.stuck
        laid += len(seen)
    assert total / laid < 0.02, f"{total} unchecked placements in {laid}"


def test_no_ladder_or_water_column_is_buried_in_the_tower() -> None:
    for run in range(4):
        course, _ = grow(run, 150)
        for cell in course.softcells:
            assert not (course.cone.rock(cell) and cell not in course.carved)


def test_a_pedestal_always_reaches_the_ground() -> None:
    """A landing three blocks up is the top of a three-block dune. One with
    nothing under it is a cube floating over a field, which is the thing this
    format exists not to be."""
    for run in range(4):
        # Deliberately short and *unadvanced*: ``advance`` releases a retired
        # landing's cells, so asking a grown-and-trimmed course whether an old
        # pedestal still stands on something asks about cells nothing owns any
        # more. The invariant is about the moment of placement.
        c = cone(run)
        course = sp.Course(random.Random(run * 6151 + 29), c)
        for _ in range(60):
            course.spawn()
        for blk in course.blocks:
            if not blk["pedestal"]:
                continue
            lowest = min(c[1] for c in blk["pedestal"])
            assert course.blocked((blk["x"], lowest - 1, blk["z"])) or \
                any(course.blocked((c[0], lowest - 1, c[2]))
                    for c in blk["pedestal"])


# ---------------------------------------------------------------------------
# The moves
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run", [1, 2, 3, 4])
def test_every_hop_is_one_a_body_can_make(run: int) -> None:
    """Against ``hop_span``, which is derived from one jump impulse and one
    horizontal speed rather than from a table anybody chose."""
    _, seen = grow(run, 200)
    for blk in seen:
        move = blk["move"]
        if move is None or move.kind != "hop" or blk["unchecked"]:
            continue
        rise = move.to[1] - move.frm[1]
        lo, hi = pk.hop_span(rise)
        d = math.dist((move.frm[0], move.frm[2]), (move.to[0], move.to[2]))
        assert lo - 1e-6 <= d <= hi + 1e-6, \
            f"{d:.2f} m hop rising {rise:.2f} is outside {lo:.2f}..{hi:.2f}"


def test_nothing_rises_two_blocks_in_one_ballistic_move() -> None:
    """The discriminant in ``hop_span`` has no solution for it, here or in the
    game. On a helix that is itself a staircase this is easy to violate by
    accident: the trough steps up a block every eight of arc, so a landing one
    above the ground reached from a landing on it asks for two."""
    for run in range(5):
        _, seen = grow(run, 200)
        for blk in seen:
            move = blk["move"]
            if move is None or blk["unchecked"]:
                continue
            if move.kind in sp.BALLISTIC:
                assert move.rise() <= 1.001, f"{move.kind} rose {move.rise():.2f}"


def test_every_move_kind_the_vocabulary_has_actually_happens() -> None:
    """A verb nobody can reach is a verb that is not in the scene, whatever the
    table says."""
    kinds: Counter = Counter()
    for run in range(14):
        _, seen = grow(run, 200)
        kinds.update(b["move"].kind for b in seen if b["move"])
    for kind in ("hop", "walk", "slide", "climb", "bubble", "bounce", "web"):
        assert kinds[kind] > 0, f"no {kind} in fourteen runs"


def test_the_course_is_mostly_but_not_only_plain_hops() -> None:
    """The complaint this rebuild answered was "jump, jump, jump, then walk a
    bit". Most parkour is jumping and should be; a tower with no ladders,
    no ice and no slime in it is one move repeated."""
    kinds: Counter = Counter()
    for run in range(10):
        _, seen = grow(run, 200)
        kinds.update(b["move"].kind for b in seen if b["move"])
    n = sum(kinds.values())
    assert 0.80 < kinds["hop"] / n < 0.96
    assert (n - kinds["hop"]) / n > 0.045


# ---------------------------------------------------------------------------
# The place
# ---------------------------------------------------------------------------

def test_most_landings_are_built_terrain_rather_than_floating_blocks() -> None:
    """The headline claim of the format, and the one the previous two attempts
    both failed: you are running over a place, not over cubes in the sky."""
    terrain = floating = 0
    for run in range(6):
        _, seen = grow(run, 200)
        for blk in seen:
            if blk["form"] == "floor" or blk["pedestal"] or blk["lift"] <= 1:
                terrain += 1
            else:
                floating += 1
    assert terrain / (terrain + floating) > 0.7


def test_a_run_meets_several_different_places() -> None:
    for run in range(4):
        _, seen = grow(run, 200)
        assert len({b["theme"] for b in seen}) >= 4


def test_every_feature_can_actually_happen() -> None:
    got: Counter = Counter()
    for run in range(24):
        _, seen = grow(run, 200)
        got.update(b["segment"] for b in seen)
    missing = sorted(set(sp.FEATURES) - set(got))
    assert not missing, f"never laid: {missing}"


def test_every_theme_names_materials_and_props_that_exist() -> None:
    from brainrot import assets
    have = set(assets.available())
    for theme in sp.THEMES:
        for slot in (theme.ground, theme.sub, theme.rock, theme.accent,
                     theme.glow):
            assert slot in pk.MATERIALS, f"{theme.name}: no material {slot}"
        if theme.liquid:
            assert theme.liquid in pk.MATERIALS
        for kind in theme.props:
            assert kind in have, f"{theme.name}: no asset {kind}"
        for feat in theme.features:
            assert feat in sp.FEATURES, f"{theme.name}: no feature {feat}"


def test_every_prop_a_theme_names_is_one_the_scene_loads() -> None:
    """A theme that names a prop nobody loaded draws nothing and says nothing
    about it."""
    for theme in sp.THEMES:
        for kind in theme.props:
            assert kind in sp.PROP_KINDS


def test_a_hanging_prop_is_hung_and_not_buried() -> None:
    """``vinehang`` and ``dripstone`` have their origin at the *top*. Dropped
    on a floor cell they are simply invisible."""
    for run in range(6):
        course, _ = grow(run, 200)
        for (x, y, z), kind, _yaw in course.cone.props:
            if kind not in sp.HANGING:
                continue
            assert course.blocked((x, y + 1, z)), \
                f"{kind} at {(x, y, z)} hangs from nothing"


# ---------------------------------------------------------------------------
# Pacing
# ---------------------------------------------------------------------------

def test_the_course_climbs() -> None:
    for run in range(4):
        _, seen = grow(run, 200)
        assert seen[-1]["y"] - seen[0]["y"] > 60


def test_the_course_never_turns_back_on_itself() -> None:
    """Progress is the unwrapped angle, and it only ever increases. A course
    that came back would be running into the section it just left."""
    for run in range(4):
        course, seen = grow(run, 120)
        us = [course.cone.unwrap(b["x"], b["z"], b["y"] + 1) for b in seen]
        for a, b in zip(us, us[1:]):
            assert b >= a - 0.35


def test_the_gaps_ramp_and_then_hold() -> None:
    """Reported on the mean, not the median: a hop length is one of a handful
    of discrete values, so a median snaps between modes and can move the wrong
    way between two samples that differ by a few per cent."""
    early: list[float] = []
    late: list[float] = []
    for run in range(8):
        _, seen = grow(run, 240)
        for i, blk in enumerate(seen):
            move = blk["move"]
            if move is None or move.kind != "hop":
                continue
            d = math.dist((move.frm[0], move.frm[2]), (move.to[0], move.to[2]))
            (early if i < 40 else late).append(d)
    assert sum(late) / len(late) > sum(early) / len(early) + 0.1


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_a_seed_replays_exactly() -> None:
    def fingerprint(run: int):
        course, seen = grow(run, 120)
        return ([(b["x"], b["y"], b["z"], b["form"], b["style"], b["segment"])
                 for b in seen],
                sorted(course.struct.items())[:400],
                list(course.cone.props)[:80])
    for run in (1, 4):
        assert fingerprint(run) == fingerprint(run)


def test_two_seeds_are_different_runs() -> None:
    _, a = grow(1, 60)
    _, b = grow(2, 60)
    assert [x["x"] for x in a] != [x["x"] for x in b]
