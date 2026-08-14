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
            # ...and stopping short of the outer wall, where this stretch has
            # one. The wall is solid on purpose -- it is the outboard side of
            # the groove, and the reference has rock there a third of the way
            # round -- so sampling past it is asking whether a cliff is clear
            # air. Everything inboard of it still has to be, which is what
            # this test is for.
            face = c.buttress_face(u)
            if face < float("inf"):
                hi = max(lo + 0.8, min(hi, face - sp.BUTTRESS_STANDOFF))
            if not c.has_floor(u):
                continue            # the chasm at the end of a level
            for frac in (0.2, 0.5, 0.8):
                r = lo + (hi - lo) * frac
                x, z = pk.iround(ct * r), pk.iround(st * r)
                samples += 1
                # Each cell against *its own* level's floor, not against the
                # sample's: a cell rounded across a level boundary belongs to
                # the level next door, which is four to six blocks up.
                cyf = c.floor_at(c.unwrap(x, z, yf + 1))
                if c.rock((x, cyf, z)) or c.rock((x, cyf + 1, z)):
                    bad_air += 1
                if not c.rock((x, cyf - 1, z)):
                    bad_ground += 1
                # ...unless the level a turn above has its *own* chasm here,
                # in which case the hole goes straight through and the trough
                # is open to the sky on purpose. That is a shaft of daylight,
                # not a missing ceiling.
                up = c.unwrap(x, z, yf + 1) + 2 * math.pi
                if c.has_floor(up) and not any(
                        c.rock((x, cyf + h, z))
                        for h in range(1, sp.TURN_MAX + 1)):
                    bad_ceiling += 1
    assert samples > 1000
    assert bad_air / samples < 0.005, f"{bad_air} of {samples} not standable"
    # A little more slack under the feet than over the head. A level's outer
    # rim is where its own chasm and the *next* level's rim wobble past each
    # other, so a cell sampled near the edge can legitimately be over nothing.
    assert bad_ground / samples < 0.04, f"{bad_ground} of {samples} unsupported"
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


def test_one_turn_rises_by_a_whole_number_of_levels() -> None:
    """Not by a fixed amount -- that was the complaint. But the ceiling over a
    level is the floor of the level exactly one turn above, so the turn has to
    be a whole number of levels or soffit and floor step at different bearings
    and saw against each other."""
    c = cone(6)
    for u in (-3.0, 0.0, 2.5, 11.0):
        rise = c.floor_at(u + 2 * math.pi) - c.floor_at(u)
        assert sp.TURN_MIN <= rise <= sp.TURN_MAX


def test_the_tower_does_not_climb_at_a_constant_rate() -> None:
    """A tower that gains exactly the same height every revolution reads as a
    machine part, which is what it was."""
    c = cone(11)
    rises = {c.level(i).rise for i in range(2, 30)}
    assert len(rises) > 1, "every level rises by the same amount"


def test_a_level_is_flat() -> None:
    c = cone(9)
    for i in range(1, 20):
        lv = c.level(i)
        heights = {c.floor_at(lv.u0 + (lv.u1 - lv.u0) * f)
                   for f in (0.05, 0.3, 0.6, 0.95)}
        assert heights == {lv.y}


def test_every_level_ends_in_a_chasm_with_nothing_in_it() -> None:
    """The reason the parkour is not optional."""
    c = cone(10)
    for i in range(1, 20):
        lv = c.level(i)
        mid = (lv.u_edge + lv.u1) / 2
        th = mid * c.wind
        out = c.outer_at(mid)
        for frac in (0.25, 0.5, 0.75):
            r = out - sp.BAND + sp.BAND * frac
            x, z = pk.iround(math.cos(th) * r), pk.iround(math.sin(th) * r)
            assert not c.rock((x, lv.y - 1, z)), "the chasm has a floor in it"


def test_the_step_between_levels_cannot_be_walked_up() -> None:
    """A body steps up 0.6 without trying and jumps 1.25, so one block is free
    and two is not. Every level boundary is at least four."""
    c = cone(12)
    for i in range(2, 25):
        assert c.level(i).rise >= 4


def test_nothing_can_walk_up_the_tower() -> None:
    """The acceptance test for the whole rebuild.

    A walker that may step up one block and drop any survivable distance, let
    loose on the **cone alone** -- no course blocks, no pedestals, no dressing
    -- must not get anywhere. If it can, the parkour is decoration on a ramp,
    which is exactly what the previous version was.
    """
    for run in (1, 3):
        c = cone(run)
        course = sp.Course(random.Random(run * 6151 + 29), c)
        start = course.blocks[0]
        y0 = start["y"] + 1
        seen = {(start["x"], y0, start["z"])}
        queue = [(start["x"], y0, start["z"])]
        best = y0
        while queue and len(seen) < 40000:
            x, y, z = queue.pop()
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, nz = x + dx, z + dz
                for ny in range(y + 1, y - 24, -1):
                    if not c.rock((nx, ny - 1, nz)):
                        continue
                    if c.rock((nx, ny, nz)) or c.rock((nx, ny + 1, nz)):
                        break
                    cell = (nx, ny, nz)
                    if cell not in seen:
                        seen.add(cell)
                        queue.append(cell)
                        best = max(best, ny)
                    break
        assert best - y0 < sp.LEVEL_RISE[0], \
            f"a walker climbed {best - y0} blocks without touching the parkour"


def test_sections_tile_the_helix_without_gaps() -> None:
    c = cone(7)
    c.section_at(30.0)
    for a, b in zip(c.sections, c.sections[1:]):
        assert abs(a.u1 - b.u0) < 1e-9
        assert b.u1 > b.u0
        assert b.index == a.index + 1


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
    deadlock -- and it is not allowed to be common.

    The ceiling is 1%, and it took getting there twice. When the trough became
    a stack of levels this stood at 4% and the docstring said so, because a
    *mandatory* move -- every level must be left, over a chasm, onto ground
    four to six blocks up -- is a much harder guarantee than a free one. What
    finally paid was not a better search but noticing that the crossing was
    never required to actually **cross**: it was a landing on the trough's own
    ground, and the nearest such ground is the terrace the body has just spent
    five landings climbing off. ``tools/spiral_probe.py`` prints the live
    figure, which is a little under 0.5%.

    Twelve runs and not six. A ceiling this close to the live figure needs a
    sample that can carry it: at six runs of a hundred and fifty the count is
    single digits and one unlucky level moves it by half a point, so the test
    fails on seeds that are not worse, only different.
    """
    total = laid = 0
    for run in range(12):
        course, seen = grow(run, 200)
        total += course.stuck
        laid += len(seen)
    assert total / laid < 0.01, f"{total} unchecked placements in {laid}"


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
    assert 0.80 < kinds["hop"] / n < 0.97
    assert (n - kinds["hop"]) / n > 0.03


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


def test_a_level_is_about_something() -> None:
    """Its signature verb turns up on it more than it does anywhere else.

    Weighted rather than forced, on purpose: a level that is *only* its own
    verb is a tutorial stage. What is being asserted is that the emphasis
    survives the shared grammar it competes with -- a jungle with the
    occasional vine in it is not a jungle level.
    """
    own = other = 0
    for run in range(8):
        course, seen = grow(run, 240)
        cone = course.cone
        for blk in seen:
            if blk["segment"] in ("ascent", "start", "stuck", "recover"):
                continue
            lv = cone.section_at(cone.unwrap(blk["x"], blk["z"], blk["y"] + 1))
            if not lv.signature:
                continue
            if blk["segment"] == lv.signature:
                own += 1
            elif blk["segment"] in sp.THEMED:
                other += 1
    assert own > other, f"signature {own} against other themed verbs {other}"


def test_a_hard_level_is_actually_harder_than_a_mild_one() -> None:
    """The ramp lives in the *level*, and it has to be visible in the course.

    Two things are asserted and they are different claims. That the levels
    genuinely differ -- a run that drew the same pitch every time would pass
    any check on the mean -- and that the difference reaches the parkour: a
    landing on a hard level is further away than one on a mild level. Measured
    on the mean rather than the median, for the reason
    ``test_the_gaps_ramp_and_then_hold`` gives.

    The exit climb is left out. It is nearly half of every run, its shape is
    set by how tall the level is rather than by how hard it is, and it would
    drown the signal it is not part of.
    """
    mild: list[float] = []
    stiff: list[float] = []
    pitches: list[float] = []
    for run in range(12):
        course, seen = grow(run, 240)
        cone = course.cone
        pitches += [s.hard for s in cone.sections if s.index >= sp.START_LEVEL]
        for blk in seen:
            if blk["move"] is None or blk["segment"] == "ascent":
                continue
            if blk["move"].kind not in ("hop", "slide"):
                # A climb's start and end are three legs apart and most of the
                # distance between them is vertical. It is not a gap and it
                # does not belong in a measurement of how far the gaps are.
                continue
            lv = cone.section_at(cone.unwrap(blk["x"], blk["z"], blk["y"] + 1))
            frm, to = blk["move"].frm, blk["move"].to
            reach = math.dist((frm[0], frm[2]), (to[0], to[2]))
            if lv.hard >= 0.9:
                stiff.append(reach)
            elif lv.hard < 0.6:
                mild.append(reach)
    assert min(pitches) < 0.55 and max(pitches) > 1.0, "levels all one pitch"
    assert len(mild) > 100 and len(stiff) > 100
    assert sum(stiff) / len(stiff) - sum(mild) / len(mild) > 0.12, (
        f"mild {sum(mild)/len(mild):.2f} vs hard {sum(stiff)/len(stiff):.2f}")


def test_a_level_is_never_left_and_then_re_entered() -> None:
    """The exit climb crosses the chasm, and crossing it is not optional.

    Stated on the *level index* rather than on height, because that is the
    thing that used to go backwards without ever failing a check. The jump out
    of a level was a landing on the trough's own ground at whatever bearing the
    arc reached, and the nearest such ground is the terrace the body has just
    climbed off -- so a staircase would gain its five blocks, come down on the
    floor it started from, and spend the rest of the level climbing out of it
    again with less room each time. Nothing in the module noticed, because the
    crossing always succeeded.
    """
    for run in range(6):
        course, seen = grow(run, 200)
        levels = [course.cone.level_index(
            course.cone.unwrap(b["x"], b["z"], b["y"] + 1)) for b in seen]
        for a, b in zip(levels, levels[1:]):
            assert b >= a, f"run {run} fell back from level {a} to {b}"


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


def test_every_floor_material_exists() -> None:
    """A misspelt material is not an error anywhere -- it is a hole.

    ``FLOOR_MIX`` is the level's ground beyond the one material it is named
    for, and nothing between here and the mesher looks a name up in a way that
    would complain.
    """
    bad = [(theme, mat) for theme, mix in sp.FLOOR_MIX.items()
           for mat, _ in mix if mat not in sp.MATERIALS]
    assert not bad, f"unknown floor materials: {bad}"
    assert set(sp.FLOOR_MIX) == {t.name for t in sp.THEMES}, \
        "a theme has no floor palette, or a palette has no theme"


def test_a_level_floor_is_more_than_one_material() -> None:
    """The identity lever. ``docs/RESEARCH.md`` §1 measured the real map at a
    median 14 materials with the commonest at 26%; this tower painted its
    terraces in one material until 2026-08-13."""
    for theme in sp.THEMES:
        pal = theme.floor_palette()
        assert len(pal) >= 8, f"{theme.name}: only {len(pal)} floor materials"
        total = sum(w for _, w in pal)
        assert pal[0][1] / total < 0.35, \
            f"{theme.name}: {pal[0][0]} holds {100 * pal[0][1] / total:.0f}%"
        # Stable per cell, or re-emitting a layer redraws a different floor.
        assert all(theme.floor_style(x, z) == theme.floor_style(x, z)
                   for x in range(-8, 8) for z in range(-8, 8))


def test_the_terrace_is_painted_in_its_own_levels_floor() -> None:
    """The ground under the body is that level's floor, all the way across.

    Two bugs met on this row and neither was visible from the code. The paint
    laid the core wall of the level three below *before* the terrace slab and
    ``_ring`` skips a claimed cell, so a level with a wider band than that one
    wore a strip of its cliff -- and ``_slab``'s depth chain let depth 0 fall
    into the rim branch, which threw the full-width radius away and left 45%
    of every cell a body can stand on painted by nothing at all. Both read as
    a grey plate through the lens and neither moves a single number in the
    course probes, because ``Cone.rock`` is analytic and none of this is
    collision. Enumerated from ``rock`` rather than from the emitter's own
    marching, so the test cannot inherit the emitter's mistakes.
    """
    c = cone(3)
    bad_style: list[tuple] = []
    unpainted = surfaces = 0
    for lv in [c.level(i) for i in range(4, 12)]:
        y = lv.y - 1                      # the cell whose top face you stand on
        painted: dict = {}
        c.emit_layer(y, painted.__setitem__)
        pal = {m for m, _ in lv.theme.floor_palette()}
        lim = int(c.rim_at(y)) + 3
        for x in range(-lim, lim + 1):
            for z in range(-lim, lim + 1):
                if not c.rock((x, y, z)) or c.rock((x, y + 1, z)):
                    continue          # not ground, or buried under the wall
                if c.level_index(c.unwrap(x, z, y + 1)) != lv.index:
                    continue          # somebody else's terrace at this height
                surfaces += 1
                got = painted.get((x, y, z))
                if got is None:
                    unpainted += 1
                elif got not in pal:
                    bad_style.append((lv.theme.name, (x, y, z), got))
    assert surfaces > 2000, f"only {surfaces} cells of terrace measured"
    assert len(bad_style) <= surfaces // 200, \
        f"{len(bad_style)} of {surfaces} terrace cells are not the level's " \
        f"own floor: {bad_style[:6]}"
    assert unpainted <= surfaces // 100, \
        f"{unpainted} of {surfaces} cells a body stands on are painted by " \
        f"nothing and show the row beneath them"


def test_what_the_tower_draws_is_what_the_tower_is() -> None:
    """Every cell of skin is a cell ``rock`` calls solid, and nothing else.

    Two independent descriptions of one surface is how this format grew
    geometry you could see and walk through. ``emit_layer`` marched a float
    radius and rounded each step to a cell, and it drew the flutes a cell
    proud of ``core_r`` while ``rock`` knew nothing about them -- so half of
    the fifty-six ribs, which are the tower's signature forest of columns,
    stood in the corridor as blocks the body passed straight through.
    Measured before the fix: 24,000 drawn cells that were air, 3.3% of body
    samples along a course inside one of them, up to 0.80 m deep.
    """
    for run in range(2):
        c = cone(run)
        lo, hi = c.level(4).y, c.level(10).y
        painted: dict = {}
        for y in range(lo, hi):
            c.emit_layer(y, lambda cell, style: painted.__setitem__(cell,
                                                                    style))
        assert len(painted) > 10_000, "nothing was painted; the test is blind"
        phantom = [(cell, style) for cell, style in painted.items()
                   if not c.rock(cell)]
        assert not phantom, \
            f"{len(phantom)} drawn cells are air, e.g. {phantom[:3]}"
