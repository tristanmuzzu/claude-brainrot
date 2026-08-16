"""Generated-content invariants.

The point of these is that generation is *structurally* correct rather than
usually correct. A layout that misbehaves one run in fifty would be a bug you
could stare at for an hour without reproducing.
"""

from __future__ import annotations

import collections
import math
import os
import statistics
import subprocess
import sys

import pytest

from conftest import H, W, ensure_window

from brainrot.engine import rl, scene as scene_api
from brainrot.engine.input import Intent
from brainrot.engine.collide import AABB
from brainrot.palette import generate as generate_palette
from brainrot.rng import Seed
from brainrot.scenes.runner import ROW as RUNNER_ROW
from brainrot.scenes.runner import SEGMENT_TABLE as RUNNER_SEGMENTS
from brainrot.scenes.parkour import (
    AIR_MAX, AIR_MIN, AIR_SPEED, APPROACH_MIN, BAND, COURSE_ALT, EDGE, FORMS,
    GRAVITY, HEADROOM, MIN_HOP, RAMP_BLOCKS, SEGMENT_TABLE, VY_MAX, VY_MIN,
    fit_gap, flight, hop_span, max_gap)


def context(run: int) -> scene_api.SceneContext:
    seed = Seed.for_run(run)
    return scene_api.SceneContext(W, H, generate_palette(seed), seed)


@pytest.fixture(scope="module", autouse=True)
def _window():
    ensure_window()


def build_runner(run: int):
    # Through the registry, so per-scene texture eviction applies -- the
    # software rasteriser's texture pool cannot survive 25 unevicted scenes.
    return scene_api.build("runner", context(run))


def build_parkour(run: int):
    return scene_api.build("parkour", context(run))


# -- runner ---------------------------------------------------------------


@pytest.mark.parametrize("run", range(1, 25))
def test_runner_corridor_is_always_reachable(run: int) -> None:
    """The safe lane may never jump more than one lane between rows.

    This is the invariant the whole generator is built around: satisfy it and
    an unwinnable track is impossible to express.
    """
    scene = build_runner(run)
    lanes = [scene._lane_clear(row) for row in range(300)]
    for i in range(1, len(lanes)):
        assert abs(lanes[i] - lanes[i - 1]) <= 1
        assert 0 <= lanes[i] <= 2


def generate_runner(run: int, rows: int = 200):
    """A scene whose track is laid out well past the spawn horizon.

    Generation is by set-piece, and a set-piece decides a stretch of track and
    the corridor through it together -- so it is driven by walking the horizon
    forward, never by asking for one row.
    """
    scene = build_runner(run)
    while scene.next_row < rows:
        # Move the world past the runner exactly as ``update`` does: every
        # entity's distance is relative to where the runner is *now*, so
        # winding ``travel`` on without winding them back leaves every
        # already-placed obstacle claiming to be somewhere it is not.
        step = RUNNER_ROW
        scene.travel += step
        for e in scene.entities:
            e["d"] -= step
        scene._spawn_to_horizon()
    return scene


@pytest.mark.parametrize("run", range(1, 20))
def test_runner_static_trains_avoid_the_corridor(run: int) -> None:
    """Parked trains only ever occupy lanes the corridor does not.

    Asked over the train's whole *length*, not the row it was spawned on: a
    train is three to five rows long, and one placed beside the corridor where
    it stands can be squarely across it two rows later.
    """
    scene = generate_runner(run)
    for e in scene.entities:
        if e["kind"] != "train" or e["vel"] or e.get("ride"):
            continue
        a, b = scene._train_span(e["d"] + scene.travel, e["cars"])
        for row in range(int(a // RUNNER_ROW), int(b // RUNNER_ROW) + 1):
            if row not in scene.corridor:
                continue                     # past the end of what was laid
            assert e["lane"] != scene._lane_clear(row), (
                f"run {run}: parked train across the corridor at row {row}")


@pytest.mark.parametrize("run", range(1, 20))
def test_runner_always_has_a_train_free_lane(run: int) -> None:
    """A yard may block two lanes at once; it may never block three.

    The old generator forbade two abreast, and had to: while the corridor was
    a random walk it could not see, a second train could land across the only
    lane left. A set-piece writes the weave itself, so it can close everything
    the weave does not need -- which is what a train yard looks like -- and
    still promise a way through. The promise is this test.
    """
    scene = generate_runner(run)
    # A train being ridden is deliberately *in* the corridor: the corridor
    # goes over the top of it. That it is passable is asserted by the roof
    # tests, which check the leap onto it rather than a way round it.
    trains = [(e, *scene._train_span(e["d"] + scene.travel, e["cars"]))
              for e in scene.entities
              if e["kind"] == "train" and not e["vel"] and not e.get("ride")]
    for row in range(4, 190):
        p = row * RUNNER_ROW
        blocked = {e["lane"] for e, a, b in trains if a <= p <= b}
        assert len(blocked) <= 2, f"run {run}: row {row} blocked {blocked}"
        assert scene._lane_clear(row) not in blocked, (
            f"run {run}: row {row} corridor lane is inside a train")


@pytest.mark.parametrize("run", range(1, 12))
def test_runner_obstacles_are_never_inside_each_other(run: int) -> None:
    """The occupancy ledger, stated as a property of what gets drawn.

    Before it existed, obstacles were spaced by counting rows -- which says
    nothing about volumes, and a 25 m train against a 6 m row is a great many
    rows of nothing being said. Measured over four runs of the old generator:
    9,731 frames in which two obstacles were drawn inside each other, the
    worst 2.18 m deep, mostly trains through trains and hoardings hung through
    the middle of them.
    """
    scene = generate_runner(run, 160)
    boxes = []
    for e in scene.entities:
        box = scene.solid_box(e)
        if box is not None:
            boxes.append((e, box))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            depth = a[1].penetration(b[1])
            assert depth < 0.001, (
                f"run {run}: {a[0]['kind']} inside {b[0]['kind']} by {depth:.3f} m")


@pytest.mark.parametrize("run", range(1, 12))
def test_runner_two_moves_never_overlap(run: int) -> None:
    """Two obstacles that each demand a move are never closer together than
    one move takes to finish.

    Volumes and *moves* are different questions, and the second one cannot be
    answered by counting rows either -- least of all across a set-piece
    boundary, which is exactly where it went wrong: two hurdles a row apart,
    one either side of the seam, put the runner's feet through the second
    while it was still coming down off the first.
    """
    from brainrot.scenes.runner import ACTION_SPAN

    scene = generate_runner(run, 160)
    acts: list[tuple[int, float]] = []
    for e in scene.entities:
        if e["kind"] == "barrier":
            acts.append((e["lane"], e["d"] + scene.travel))
        elif e["kind"] == "hoarding":
            acts.append((-1, e["d"] + scene.travel))
    for i in range(len(acts)):
        for j in range(i + 1, len(acts)):
            (la, pa), (lb, pb) = acts[i], acts[j]
            if la != -1 and lb != -1 and la != lb:
                continue
            assert abs(pa - pb) >= 2 * ACTION_SPAN - 0.001, (
                f"run {run}: two moves {abs(pa - pb):.1f} m apart in lane {la}")


def test_runner_uses_its_whole_set_piece_vocabulary() -> None:
    """A vocabulary of seven that in practice reads as two is no vocabulary.

    The generator this replaced had none at all: measured over twelve minutes
    it produced 7.6 hurdles a minute, 0.2 hoardings, and the slide -- one of
    only three moves the runner has -- appeared about once every five minutes.
    """
    from collections import Counter

    seen = Counter()
    for run in range(1, 9):
        seen.update(generate_runner(run, 200).segments)
    names = {name for name, *_ in RUNNER_SEGMENTS}
    assert set(seen) == names, f"never generated: {names - set(seen)}"
    assert min(seen.values()) >= 3, f"barely generated: {seen}"


def test_runner_never_repeats_a_set_piece_back_to_back() -> None:
    """The cheapest thing that stops seven set-pieces reading like two."""
    for run in (1, 4, 9, 17):
        scene = build_runner(run)
        order: list[str] = []
        original = scene._begin_segment

        def watched(row0: int, _orig=original, _out=order, _s=scene) -> None:
            _orig(row0)
            _out.append(_s._last_segment)

        scene._begin_segment = watched
        while scene.next_row < 220:
            scene.travel += RUNNER_ROW
            for e in scene.entities:
                e["d"] -= RUNNER_ROW
            scene._spawn_to_horizon()
        assert len(order) > 12, f"run {run}: only {len(order)} set-pieces"
        for a, b in zip(order, order[1:]):
            assert a != b, f"run {run}: {a} twice running"


def test_runner_never_more_than_one_oncoming_train() -> None:
    """The live dodge can always answer one sweeping train; two can pin every
    lane at once, so the generator must never allow it."""
    for run in (3, 11, 42):
        scene = build_runner(run)
        for _ in range(3600):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            oncoming = [e for e in scene.entities if e["kind"] == "train" and e["vel"]]
            assert len(oncoming) <= 1


def test_runner_autopilot_makes_progress_and_collects() -> None:
    scene = build_runner(42)
    for _ in range(3600):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    assert scene.travel > 400, "runner went nowhere"
    assert scene.coins > 0, "corridor coins were never collected"
    # The runner must always sit in a legal lane.
    assert 0 <= scene.lane <= 2


def test_runner_dodges_oncoming_trains() -> None:
    """Whenever an oncoming train reaches the player, the player is not in
    its lane -- the dodge fired in time."""
    for run in (7, 23, 42):
        scene = build_runner(run)
        for _ in range(5400):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            for e in scene.entities:
                if e["kind"] == "train" and e["vel"]:
                    length = e["cars"] * 5.1
                    if -length + 1.0 < e["d"] < 1.0:
                        assert e["lane"] != scene.lane, (
                            f"run {run}: hit by oncoming train"
                        )


# -- parkour --------------------------------------------------------------
#
# The course is laid on an integer lattice and every solid thing in it fills
# whole cells, which is what makes "these two blocks are not inside each other"
# a question with an exact answer. The tests below are stated against volumes
# and against the motion model rather than against distances between centres:
# a centre-distance test passes cheerfully while a three-wide platform has a
# corner cube buried in the next one.


def grow_parkour(run: int, blocks: int = 400):
    """A course generated flat out, with nothing ever trailing off the back.

    Harsher than play on purpose: nothing is retired, so the occupancy map
    holds every block ever laid instead of the dozen or so that are live, and
    the generator has to thread the course through the whole of its own past.
    """
    scene = build_parkour(run)
    while len(scene.blocks) < blocks:
        scene._spawn_block()
    return scene


def _box(cx: float, cy: float, cz: float,
         sx: float, sy: float, sz: float) -> AABB:
    return AABB(cx - sx / 2, cy - sy / 2, cz - sz / 2,
                cx + sx / 2, cy + sy / 2, cz + sz / 2)


def solid_boxes(blk: dict) -> list[tuple[str, AABB]]:
    """Every solid box a block puts in the world.

    Built from the same arithmetic as ``ParkourScene._draw_course`` -- the
    3x3 of a wide platform, the half-height of a slab, and each decoration at
    its own offset and size -- so an overlap found here is one that could be
    photographed. The one thing left out is the arrival lift, which is a
    transient of the fade-in rather than where the block lives.
    """
    bx, by, bz = blk["x"], blk["y"], blk["z"]
    form = blk["form"]
    out: list[tuple[str, AABB]] = []
    if form == "wide":
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                out.append((f"wide{ox:+d}{oz:+d}",
                            _box(bx + ox, by + 0.5, bz + oz, 1.0, 1.0, 1.0)))
    elif form == "slab":
        out.append(("slab", _box(bx, by + 0.25, bz, 1.0, 0.5, 1.0)))
    else:
        # ``stair`` lands here too: it is drawn as a plain full block, having
        # lost the half-block tread that used to cut into its own neighbour.
        out.append(("core", _box(bx, by + 0.5, bz, 1.0, 1.0, 1.0)))
    for i, d in enumerate(blk["deco"]):
        out.append((f"deco{i}:{d['style']}",
                    _box(bx + d["dx"], by + d["dy"] + d["sy"] / 2, bz + d["dz"],
                         d["sx"], d["sy"], d["sz"])))
    return out


def footprint(scene, blk: dict) -> list[tuple[int, int, int]]:
    """The cells a block's walking surface stands on -- the landing itself,
    without the pillars and lintels hung off it."""
    from brainrot.scenes.parkour import SPREAD

    sp = SPREAD.get(blk["form"], 0)
    return [(blk["x"] + ox, blk["y"], blk["z"] + oz)
            for ox in range(-sp, sp + 1) for oz in range(-sp, sp + 1)]


#: Side of the spatial-hash cell the overlap test buckets boxes into, in
#: metres. Comparing four hundred blocks' worth of boxes pairwise is a quarter
#: of a million comparisons per run; bucketing by footprint makes it linear.
HASH_CELL = 2.0
#: Two faces meeting is not an overlap, but in floating point it computes as
#: one about a hundred times in thirty thousand boxes, at depths around 1e-14.
TOUCH = 1e-6


def overlapping(boxes: list[tuple[int, str, AABB]]):
    """Yield ``(i, j, depth)`` for every pair of boxes that interpenetrate."""
    grid: dict[tuple[int, int], list[int]] = {}
    for idx, (_, _, b) in enumerate(boxes):
        for cx in range(math.floor(b.x0 / HASH_CELL),
                        math.floor(b.x1 / HASH_CELL) + 1):
            for cz in range(math.floor(b.z0 / HASH_CELL),
                            math.floor(b.z1 / HASH_CELL) + 1):
                grid.setdefault((cx, cz), []).append(idx)
    seen: set[tuple[int, int]] = set()
    for bucket in grid.values():
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                key = (bucket[a], bucket[b])
                if key in seen:
                    continue
                seen.add(key)
                depth = boxes[key[0]][2].penetration(boxes[key[1]][2])
                if depth > TOUCH:
                    yield key[0], key[1], depth


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_course_sits_on_the_integer_lattice(run: int) -> None:
    """Every block is at whole coordinates, and every step between two of them
    is a whole offset.

    This is the property the rest of the geometry is bought with: two unit
    cubes on whole cells are either the same cell or disjoint, so occupancy can
    be a set of integer triples and "do these overlap" stops being a question
    about tolerances. A single float that creeps in here takes that guarantee
    with it, silently.
    """
    scene = grow_parkour(run)
    for i, blk in enumerate(scene.blocks):
        for axis in ("x", "y", "z"):
            assert isinstance(blk[axis], int), (
                f"run {run}: block {i} has {axis}={blk[axis]!r}")
        assert blk["form"] in FORMS, f"run {run}: unknown form {blk['form']}"
        sx, sz = blk["step"]
        assert isinstance(sx, int) and isinstance(sz, int)
        assert (sx, sz) != (0, 0), f"run {run}: block {i} arrived from nowhere"
        if i < len(scene.blocks) - 1:
            # ``out`` is written when the course commits to where it goes next,
            # so it must be the very step that took it there.
            assert blk["out"] == scene.blocks[i + 1]["step"], (
                f"run {run}: block {i} leaves by {blk['out']} but the next "
                f"one arrives by {scene.blocks[i + 1]['step']}")


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_course_never_intersects_itself(run: int) -> None:
    """No solid box the scene draws is inside another one.

    Stated as a volume test because the thing it replaced was a distance test:
    "block centres are at least 0.9 m apart" is satisfied by a wide platform
    with an outer cube buried halfway into its neighbour, and by every
    decoration ever drawn, since decorations have no centres of their own. The
    boxes here are the drawn boxes, so a failure is visible in a screenshot.
    """
    scene = grow_parkour(run)
    boxes = [(i, what, box)
             for i, blk in enumerate(scene.blocks)
             for what, box in solid_boxes(blk)]
    worst = []
    for i, j, depth in overlapping(boxes):
        ai, aw, _ = boxes[i]
        bj, bw, _ = boxes[j]
        worst.append((depth, f"{ai}/{aw} into {bj}/{bw} by {depth:.3f} m"))
    worst.sort(reverse=True)
    assert not worst, (f"run {run}: {len(worst)} interpenetrating pairs in "
                       f"{len(boxes)} boxes -- " + "; ".join(w for _, w in worst[:5]))


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_never_falls_back_on_its_emergency_hop(run: int) -> None:
    """Placement must always find a real answer.

    There is one last resort at the bottom of ``_choose_cell`` that returns a
    hop without checking anything, because the generator runs inside the frame
    loop and has to return. It is not a safety net anybody should be landing
    in: every hop it produces skips the reach test, the headroom test and the
    corridor test at once, and the only symptom is a set-piece that quietly
    looks wrong -- a flight of stairs stacked almost vertically, in the case
    that put this counter here. If this ever fires, the fix is upstream in
    what the set-piece asked for, not here.
    """
    scene = grow_parkour(run)
    assert scene.stuck == 0, (
        f"run {run}: placement gave up {scene.stuck} times in 400 blocks")


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_every_landing_has_headroom(run: int) -> None:
    """A body is 1.8 m tall, so the two cells over every landing are empty.

    Without this the generator will tuck a landing under an arch or a gate
    lintel it laid down three blocks earlier -- and because the course is
    generated ahead of the player, the block that steals the headroom can
    arrive long after the landing under it was approved.
    """
    scene = grow_parkour(run)
    for i, blk in enumerate(scene.blocks):
        for cx, cy, cz in footprint(scene, blk):
            for h in range(1, HEADROOM + 1):
                assert (cx, cy + h, cz) not in scene._solid, (
                    f"run {run}: block {i} ({blk['segment']}) has something "
                    f"solid {h} cell(s) over its landing")


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_jumps_stay_physical(run: int) -> None:
    """Every hop must be one a body in the game could actually make.

    The hop that matters is not centre to centre: the feet land on the near
    edge of a block, run across it, and leave from the far edge, so the jump
    the generator has to justify runs from ``_takeoff_point`` to
    ``_land_point``. It is legal exactly when the take-off it asks for is one a
    body has -- nothing between stepping off an edge (``VY_MIN``) and the one
    jump impulse the game owns (``VY_MAX``) -- and when the body is already
    falling when it arrives. Landing while still rising means it came up
    through the side of the block rather than onto it.

    Horizontal speed is checked too, and the statement is the motion model
    itself: a player has **one** jump impulse and spends all of it every time,
    so what they choose is how fast they are running when they use it. Every
    hop is therefore one of exactly three things -- a sprint jump at the top
    speed a body has, a slower approach that lands the *whole* impulse on the
    far end, or, on a gap short enough that even a sprint would overshoot a
    full jump, a lower arc taken at the floor speed. Nothing in between, and
    nothing outside.

    The version this replaces asserted a *constant* horizontal speed, which
    put the whole of the player's choice into the arc: a two-metre hop came
    out apexing at 0.28 m against vanilla's 1.25, and a run of those is a run
    of skips.
    """
    scene = grow_parkour(run)
    for i, (a, b) in enumerate(zip(scene.blocks, scene.blocks[1:])):
        frm, to = scene._takeoff_point(a), scene._land_point(b)
        gap = math.dist((frm[0], frm[2]), (to[0], to[2]))
        dur, vy0 = flight(frm, to)
        where = f"run {run}: hop {i} ({a['segment']} -> {b['segment']})"
        assert gap >= MIN_HOP, f"{where}: {gap:.2f} m is a shuffle, not a hop"
        assert VY_MIN <= vy0 <= VY_MAX, f"{where}: takes off at {vy0:.2f} m/s"
        assert AIR_MIN <= dur <= AIR_MAX, f"{where}: {dur:.2f} s in the air"
        assert dur >= vy0 / GRAVITY - 1e-9, (
            f"{where}: still rising after {dur:.3f} s, apex at "
            f"{vy0 / GRAVITY:.3f} s -- it arrives through the side")
        speed = gap / dur
        assert APPROACH_MIN - 1e-6 <= speed <= AIR_SPEED + 1e-6, (
            f"{where}: crossed at {speed:.2f} m/s")
        assert (abs(speed - AIR_SPEED) < 1e-6
                or abs(vy0 - VY_MAX) < 1e-6
                or abs(speed - APPROACH_MIN) < 1e-6), (
            f"{where}: crossed at {speed:.2f} m/s taking off at {vy0:.2f} m/s "
            "-- neither a sprint, nor the whole impulse, nor the floor")
        # and the arc genuinely ends on the surface it was solved for
        landed = frm[1] + vy0 * dur - 0.5 * GRAVITY * dur * dur
        assert landed == pytest.approx(to[1], abs=1e-6)


def test_parkour_hop_span_is_the_limit_the_generator_builds_against() -> None:
    """The gap tables are derived from the motion, not chosen alongside it.

    ``hop_span`` is the only place that knows how far a body can jump for a
    given change in height, and ``fit_gap``/``max_gap`` are what the set-pieces
    ask instead of guessing -- so if those three ever disagree, a chasm becomes
    either a stroll or an unmakeable jump and nothing else in the scene says a
    word about it.
    """
    span = 1.0 - 2 * EDGE["full"]        # centre gap -> take-off to landing
    for rise in range(-6, 3):
        lo, hi = hop_span(rise)
        assert lo >= MIN_HOP
        if rise >= 2:
            assert hi == 0.0, "two blocks up has no solution and must say so"
            continue
        assert hi > lo, f"rise {rise}: nothing is jumpable"
        # whatever fit_gap widens a gap to is inside the span...
        for asked in range(1, 5):
            reach = fit_gap(asked, rise) + span
            assert lo - 1e-6 <= reach <= hi + 1e-6, (
                f"rise {rise}, gap {asked}: fit_gap returned an "
                f"unjumpable {reach:.2f} m")
        # ...and max_gap is the widest such gap, not merely a wide one
        widest = max_gap(rise)
        assert widest + span <= hi + 1e-6
        assert widest + 1 + span > hi, f"rise {rise}: max_gap left a block on the table"
        # dropping buys reach, which is the chasm's entire premise
        assert hop_span(rise - 1)[1] > hi


@pytest.mark.parametrize("run", range(1, 25))
def test_parkour_uses_its_whole_vocabulary(run: int) -> None:
    """A run of any length must not be one set-piece over and over -- which is
    the single thing that made the old course tiring to look at."""
    scene = grow_parkour(run)
    seen = {b["segment"] for b in scene.blocks}
    assert len(seen) >= 5, f"run {run}: only {seen}"
    assert seen <= {n for n, _ in SEGMENT_TABLE} | {"start"}
    # every block carries a material the catalogue knows how to draw
    for blk in scene.blocks:
        assert blk["style"] in scene.styles
        for deco in blk["deco"]:
            assert deco["style"] in scene.styles


def test_parkour_reaches_every_set_piece() -> None:
    """Nothing in the table is unreachable.

    A set-piece can be weighted out of existence by accident -- the chooser
    vetoes climbers near the ceiling, fallers near the floor and whatever ran
    last -- and an unreachable one costs nothing at runtime and is therefore
    invisible until somebody counts.
    """
    seen: set[str] = set()
    for run in range(1, 13):
        seen |= {b["segment"] for b in grow_parkour(run, 200).blocks}
    missing = {n for n, _ in SEGMENT_TABLE} - seen
    assert not missing, f"never generated in twelve runs: {sorted(missing)}"


@pytest.mark.parametrize("run", range(1, 15))
def test_parkour_altitude_stays_in_band(run: int) -> None:
    """The course wanders further than it used to -- that is the point of the
    descent and staircase set-pieces -- but it still has to come back."""
    scene = grow_parkour(run)
    for blk in scene.blocks:
        assert COURSE_ALT - BAND <= blk["y"] <= COURSE_ALT + BAND
    # and it must actually use the room: a course pinned to one altitude has
    # no verticality however wide the band is
    heights = [blk["y"] for blk in scene.blocks]
    assert max(heights) - min(heights) > 8, f"run {run}: course is flat"


def test_parkour_body_never_ends_up_inside_the_course() -> None:
    """The camera is inside a body, so a block the body is inside is a block
    the frame is looking out of.

    Checked against the drawn boxes rather than against the occupancy map,
    because occupancy is what generation reasons with and this is about where
    the simulation actually put the feet.

    Two things are excused and neither is slack. The surface being stood on,
    because a body resting on a block shares a face with it. And seven
    centimetres, because the simulation is sampled sixty times a second: the
    last sample before a landing catches the body a frame's worth of descent
    below the top face of the block it is about to arrive on, still inside its
    footprint. Measured over three minutes of running that graze tops out at
    0.062 m and it is always the block being landed on; anything materially
    deeper is a body somewhere it should not be.
    """
    for run in (2, 9, 17):
        scene = build_parkour(run)
        for frame in range(3600):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            body = scene.body_box()
            feet = scene.pos[1]
            for i, blk in enumerate(scene.blocks):
                for what, box in solid_boxes(blk):
                    if abs(box.y1 - feet) < 0.05:
                        continue                 # the floor under the feet
                    depth = body.penetration(box)
                    assert depth <= 0.07, (
                        f"run {run} frame {frame}: body {depth:.3f} m inside "
                        f"{i}/{what} ({blk['segment']})")


def test_parkour_the_body_never_teleports() -> None:
    """No frame may move the body further than its own top speed allows.

    Stated over the *driven* path, because that is where it was false. The run
    across a block used to be positioned by ``phase_t / ground_dur`` -- a
    fraction of a duration that the jump key shortens mid-phase. Shortening the
    denominator moves the fraction, so pressing jump snapped the feet to the
    far edge of the block in a single frame: measured at 3.58 m in one frame,
    against a sprint of 5.6 m/s. In first person that is not a fast take-off,
    it is a cut. Position is integrated from a speed now, and the duration only
    decides when the phase ends.
    """
    from brainrot.scenes.parkour import AIR_SPEED

    cap = AIR_SPEED / 60.0 + 1e-9
    for run in (5, 7, 11):
        scene = build_parkour(run)
        for i in range(3600):
            scene.control(Intent(right=(i // 300) % 2 == 0,
                                 left=(i // 300) % 2 == 1,
                                 jump=i % 7 == 0))
            was = (scene.pos[0], scene.pos[2])
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            moved = math.dist(was, (scene.pos[0], scene.pos[2]))
            assert moved <= cap, (
                f"run {run} frame {i}: body moved {moved:.3f} m in one frame "
                f"({moved * 60:.0f} m/s)")


def test_parkour_holding_a_block_never_walks_backwards() -> None:
    """Holding the block down slows the crossing; it must not reverse it.

    The old answer to "duck" was to add 0.05 s to the phase's duration every
    frame -- three times faster than the frame clock advances -- while position
    was read as a fraction of that duration. The fraction therefore *fell*, and
    the body walked back the way it came at up to 4 m/s. It is a walking speed
    now, which is both what vanilla does and monotone by construction.
    """
    for run in (5, 7, 11):
        scene = build_parkour(run)
        for _ in range(3600):
            scene.control(Intent(duck=True))
            before = scene.run_s if scene.phase == "ground" else None
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            if before is not None and scene.phase == "ground":
                assert scene.run_s >= before - 1e-12, (
                    f"run {run}: the run-up went backwards")


def test_parkour_an_early_take_off_moves_the_orbs_with_it() -> None:
    """Jumping early is a different hop, and its orbs have to know.

    The guarantee is that an orb hangs on the arc the body actually flies. On
    autopilot the arc is the one generation solved; press jump and the take-off
    is wherever the feet had got to, so ``_begin_air`` re-solves and re-hangs.
    This asserts that path is genuinely exercised -- it was dead code until the
    teleport above was fixed, because the early take-off used to happen from
    the far edge either way.
    """
    scene = build_parkour(11)
    moved = total = 0
    for i in range(3600):
        scene.control(Intent(jump=i % 7 == 0))
        nominal = (scene._takeoff_point(scene.blocks[scene.jump_index])
                   if scene.phase == "ground" else None)
        was = scene.phase
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
        if was == "ground" and scene.phase == "air":
            total += 1
            if math.dist((scene.takeoff[0], scene.takeoff[2]),
                         (nominal[0], nominal[2])) > 1e-9:
                moved += 1
    assert total > 40, f"only {total} take-offs"
    assert moved > total * 0.5, f"only {moved} of {total} take-offs were early"
    assert scene.orbs_missed == 0, f"{scene.orbs_missed} orbs went past"
    assert scene.orbs > 15, f"only {scene.orbs} orbs collected"


def test_parkour_a_broken_block_gives_its_cell_back() -> None:
    """Smashing the loose block beside a landing frees the space it held.

    A crumb is a whole cube, so it holds a cell in the occupancy map. The map
    is otherwise only rebuilt when blocks fall off the back of the course, so
    a cell never released is a cell the generator refuses to build in for the
    next couple of seconds -- for a block the player watched explode.
    """
    scene = build_parkour(3)
    for _ in range(7200):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
        live = {c for blk in scene.blocks for c in scene._cells_of(blk)}
        assert scene._solid == live or scene._solid > live, "map lost a live cell"
        assert not (scene._solid - live), (
            f"{len(scene._solid - live)} cells held by nothing that exists")


def test_parkour_the_body_never_stops() -> None:
    """A body that pauses on each block is a slideshow of camera positions.

    The scene this replaced pinned the player to a point for up to nine tenths
    of a second per block, and the note it came back with was that it read as
    scripted rather than run. So the invariant is that there is no moment of
    standing still at all.

    Measured over two frames rather than one, and the reason is arithmetic
    rather than slack: a phase boundary falls wherever it falls inside a
    frame, so the last frame of a run across a block carries only the fraction
    of a millimetre that was left over. A body that had genuinely stopped
    would be still for tens of frames, and no two-frame window in a minute of
    running gets anywhere near the floor below.
    """
    for run in (1, 6, 12):
        scene = build_parkour(run)
        trail = [(scene.pos[0], scene.pos[2])]
        stalled = 0
        windows = 0
        for _ in range(3600):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
            trail.append((scene.pos[0], scene.pos[2]))
            if len(trail) > 3:
                trail.pop(0)
            if len(trail) == 3:
                moved = math.dist(trail[0], trail[1]) + math.dist(trail[1], trail[2])
                windows += 1
                if moved / (2 / 60) < 0.05:
                    stalled += 1
        assert stalled == 0, (
            f"run {run}: stationary for {stalled} of {windows} frames")


def test_parkour_orbs_are_placed_where_the_body_will_be() -> None:
    """Every orb the generator hangs is collected, because it is hung on the
    flight path rather than near it. A missed orb means the arc that was solved
    at generation is not the arc that gets flown."""
    scene = build_parkour(12)
    for _ in range(7200):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    assert scene.orbs > 40, f"only {scene.orbs} orbs in two minutes"
    assert scene.orbs_missed == 0, f"{scene.orbs_missed} orbs went past uncollected"


def test_parkour_lands_on_the_block_it_aimed_for() -> None:
    """The ballistic solve must deliver the feet onto the near edge of the
    target block -- exactly there, not merely somewhere on it.

    The landing point is where the next run-up starts, so an approximate
    arrival is a take-off point that drifts, and the orbs strung on the next
    hop were hung against the take-off that was promised.

    Stated about ``stand`` rather than about ``pos``, which is a distinction
    the frame clock forces: an arrival almost never falls on a frame boundary,
    and whatever is left of that frame is now spent running across the block
    rather than thrown away. So the *feet touch down* exactly on the near edge
    and the body is already a fraction of a frame's run past it -- along the
    line to the take-off point, and never further than one frame at the
    fastest the body ever goes.
    """
    from brainrot.scenes.parkour import AIR_SPEED

    scene = build_parkour(4)
    landings = 0
    for _ in range(7200):
        was = scene.phase
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
        if was == "air" and scene.phase == "ground":
            landings += 1
            blk = scene.blocks[scene.jump_index]
            assert scene.stand == pytest.approx(scene._land_point(blk))
            assert scene.run_s <= AIR_SPEED / 60.0 + 1e-9, (
                "a landing spent more than a frame running")
            assert math.dist(scene.pos, scene.stand) <= scene.run_s + 1e-9
            assert scene.stand[1] == pytest.approx(scene.surface(blk))
            edge = EDGE[blk["form"]]
            assert abs(scene.stand[0] - blk["x"]) <= edge + 1e-9
            assert abs(scene.stand[2] - blk["z"]) <= edge + 1e-9
    assert landings > 100, f"only {landings} landings in two minutes"


def test_parkour_advances_forever() -> None:
    scene = build_parkour(9)
    for _ in range(3600):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    assert scene.distance > 60
    assert AIR_MIN <= scene.air_dur <= AIR_MAX
    # the trail is bounded: memory cannot grow with distance
    assert len(scene.blocks) < 40
    assert sum(len(b["orbs"]) for b in scene.blocks) < 60
    assert sum(len(b["deco"]) for b in scene.blocks) < 400
    # and so is the occupancy map, which is rebuilt rather than accumulated
    assert len(scene._solid) < 2000


def test_parkour_leaves_no_transform_on_a_shared_block_model() -> None:
    """The held kit is assembled from the same block models the course is
    drawn with. A rotation left on one of them tilts every block of that
    material in the world from the next frame onward -- which is where the
    slabs of brick lying at an angle over the sea came from."""
    window = ensure_window()
    scene = build_parkour(10)          # a run whose kit is a tool, not a block
    window.present(scene.draw)
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    for name, style in scene.styles.items():
        m = style["model"].transform
        got = [getattr(m, f"m{i}") for i in range(16)]
        assert got == pytest.approx(identity), f"{name} kept a transform"


def test_parkour_draw_is_the_same_frame_twice() -> None:
    """Drawing without updating must draw the same picture.

    Every screenshot this scene has ever been judged from is captured by
    presenting a frame a second time, so a draw that quietly advances the
    camera means the frame reviewed is not the frame the simulation is in.
    """
    window = ensure_window()
    scene = build_parkour(6)
    for _ in range(120):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60

    def render() -> bytes:
        window.present(scene.draw)
        return rl.capture_frame()

    assert render() == render()


def flights_of(scene) -> list[float]:
    """Every hop in a grown course, take-off point to landing point."""
    out = []
    for a, b in zip(scene.blocks, scene.blocks[1:]):
        frm, to = scene._takeoff_point(a), scene._land_point(b)
        out.append(math.dist((frm[0], frm[2]), (to[0], to[2])))
    return out


def test_parkour_gets_harder_as_a_run_goes_on() -> None:
    """The ramp, stated as the property rather than as the constants.

    A course that is as hard after four minutes as after four seconds has no
    shape, and every real infinite-parkour server ramps. The mechanism is two
    tables per set-piece and a coin weighted by ``difficulty`` -- but what has
    to be true is only this: the hops late in a run are longer than the hops
    early in it, by enough to see.

    Asserted on the median rather than the maximum, because a maximum moves the
    moment one lucky chasm turns up and says nothing about what the run
    generally feels like.
    """
    early: list[float] = []
    late: list[float] = []
    for run in range(1, 13):
        scene = grow_parkour(run, 260)
        for i, d in enumerate(flights_of(scene)):
            (early if i < RAMP_BLOCKS // 2 else late).append(d)
    lo, hi = statistics.median(early), statistics.median(late)
    assert hi > lo * 1.15, f"the ramp is flat: {lo:.2f} m early, {hi:.2f} m late"
    # ...and it has to stop ramping, or a long enough run walks off the end of
    # what a body can do and every candidate starts getting rejected.
    assert grow_parkour(4, 400).difficulty == 1.0


def test_parkour_the_squeeze_builds_beams_and_columns_that_clear_the_body() -> None:
    """The set-piece exists, and both halves of it survive generation.

    A beam or a column in the gap is placed against the arc that arrives, and
    ``_deco_cubes`` then drops anything standing in that arc -- so a version of
    this that got the arithmetic wrong would not fail, it would silently build
    nothing and read as a plain run of blocks. Hence counting them.

    Then the two properties that make them worth having. They must *clear* the
    body, which is what the whole scene guarantees anyway. And they must be
    tight enough to read: a beam three metres over your head is not a beam you
    ducked under, it is scenery, and a course that pays for the geometry
    without getting the flinch has spent the frame budget on nothing.
    """
    from brainrot.scenes.parkour import (
        BODY_H, BODY_HALF_W, _arc_points, _in_the_way)

    def underneath(blk, d, arc):
        """Arc samples the piece is actually over or under.

        The same horizontal footprint ``_in_the_way`` uses -- the piece's own
        width plus the body's. Measuring clearance against the whole arc
        instead would compare a column in the middle of a gap against the feet
        at the far end of it, which are three metres away and a metre lower,
        and report an overlap that does not exist anywhere.
        """
        return [p for p in arc[1:-1]
                if abs(p[0] - (blk["x"] + d["dx"])) < d["sx"] / 2 + BODY_HALF_W
                and abs(p[2] - (blk["z"] + d["dz"])) < d["sz"] / 2 + BODY_HALF_W]

    kinds: collections.Counter = collections.Counter()
    pieces = 0
    tight = 0
    for run in range(1, 13):
        scene = grow_parkour(run, 300)
        for a, b in zip(scene.blocks, scene.blocks[1:]):
            arc = _arc_points(scene._takeoff_point(a), scene._land_point(b))
            # Grouped, because a beam is three cubes across and a column is
            # three deep: only the cube nearest the flight line is the one the
            # eye measures, and the others are behind or beside it by
            # construction.
            closest: dict[str, float] = {}
            for d in b["deco"]:
                if d["kind"] not in ("lintel", "hurdle"):
                    continue
                kinds[d["kind"]] += 1
                assert not _in_the_way(b, d, arc), (
                    f"run {run}: a {d['kind']} is in the flight path")
                over = underneath(b, d, arc)
                if not over:
                    continue          # nowhere near the flight: nothing to say
                face = b["y"] + d["dy"] + (d["sy"] if d["kind"] == "hurdle" else 0)
                if d["kind"] == "lintel":
                    room = min(face - (p[1] + BODY_H) for p in over)
                else:
                    room = min(p[1] - face for p in over)
                assert room >= 0.0, f"run {run}: {d['kind']} overlaps by {-room:.2f} m"
                closest[d["kind"]] = min(closest.get(d["kind"], 1e9), room)
            for room in closest.values():
                pieces += 1
                tight += room < 1.05
    assert kinds["lintel"] > 20 and kinds["hurdle"] > 20, f"barely built: {kinds}"
    assert tight > pieces * 0.8, (
        f"only {tight} of {pieces} pieces are close enough to notice")


def test_parkour_nothing_in_the_world_below_can_reach_the_course() -> None:
    """The scenery under the course must stay under it, by a clear margin.

    This is what makes the whole translucent-draw question tractable. The sea,
    the reefs, the cloud shelves and the islands are all drawn *before* the
    course and all of them blend, and whether a blended draw writes depth
    decides what it can hide -- but only among things it can get in front of.
    Keep every one of them below the lowest altitude the course is allowed to
    reach and none of them can occlude a block whatever they do with the depth
    buffer, because the straight line from an eye on the course to any block on
    the course never leaves that band.

    Islands are the case that has to be checked rather than assumed: a sea
    stack is built from a randomised height on top of a randomised mound, so
    nothing about the source says where the tallest one lands.

    ``tools/depth_probe.py`` measures the same property from the other end, by
    removing each draw and counting the course pixels that change. It reports
    zero, and this is why.
    """
    floor = COURSE_ALT - BAND
    for run in (4, 12, 23, 38):
        scene = build_parkour(run)
        # Run far enough that the island recycler has spawned a fresh set:
        # checking only the ones built in the constructor tests the seed, not
        # the generator.
        for _ in range(2400):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
        top = 0.0
        for isl in scene.islands:
            for c in isl["cubes"]:
                sy = c.get("sy", c.get("s", 0.0))
                top = max(top, c["y"] + sy / 2)
            fall = isl["waterfall"]
            if fall is not None:
                top = max(top, fall["h"])
        assert top < floor, f"run {run}: an island reaches {top:.1f} m"
        # The upper sheet of a cloud shelf is the highest thing down there
        # that is not land.
        for s in scene.shelves:
            assert s["y"] + 3.5 < floor, f"run {run}: a shelf at {s['y']:.1f} m"


def test_parkour_orb_hitbox_is_the_model_it_draws() -> None:
    """The box comes from the orb model pushed through the orb's own draw
    transform, so it cannot disagree with the picture."""
    from brainrot.engine.collide import model_aabb, placed
    from brainrot.scenes.parkour import ORB_SCALE

    scene = build_parkour(3)
    orb = next(o for blk in scene.blocks for o in blk["orbs"])
    want = placed(model_aabb(scene._model("orb")),
                  (orb["x"], orb["y"], orb["z"]),
                  scale=(ORB_SCALE, ORB_SCALE, ORB_SCALE))
    assert scene.orb_box(orb) == want


# -- every scene ----------------------------------------------------------


@pytest.mark.parametrize("name", ["runner", "parkour"])
def test_scene_renders_and_covers_the_frame(name: str) -> None:
    window = ensure_window()
    scene = scene_api.build(name, context(21))
    for _ in range(90):
        scene.update(1 / 60)
        scene.elapsed += 1 / 60
    window.present(scene.draw)
    raw = rl.capture_frame()
    assert raw is not None and len(raw) == W * H * 4
    # Fully covered (opaque) and actually drawn (not one flat colour).
    assert all(raw[i + 3] == 255 for i in range(0, len(raw), 4001 * 4 - (4001 * 4) % 4))
    samples = {raw[i:i + 3] for i in range(0, len(raw) - 3, 997 * 4)}
    assert len(samples) > 12, f"{name} rendered almost nothing"


@pytest.mark.parametrize("name", ["runner", "parkour"])
def test_scene_is_deterministic_for_a_seed(name: str) -> None:
    window = ensure_window()

    def render() -> bytes:
        scene = scene_api.build(name, context(77))
        for _ in range(60):
            scene.update(1 / 60)
            scene.elapsed += 1 / 60
        window.present(scene.draw)
        return rl.capture_frame()

    assert render() == render()


def test_scene_choice_is_stable_per_run() -> None:
    names = ["runner", "parkour"]
    for run in range(1, 50):
        seed = Seed.for_run(run)
        assert scene_api.choose(names, seed) == scene_api.choose(names, seed)


def test_scene_choice_uses_the_whole_roster() -> None:
    names = ["runner", "parkour"]
    picked = {scene_api.choose(names, Seed.for_run(run)) for run in range(1, 60)}
    assert picked == set(names)


def test_available_populates_the_registry_on_its_own() -> None:
    """It must not depend on someone else having imported the scenes first."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from brainrot.engine.scene import available; print('SCENES=' + ','.join(available()))",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "BRAINROT_HEADLESS": "1", "SDL_VIDEODRIVER": "dummy"},
    )
    assert result.returncode == 0, result.stderr
    line = next(l for l in result.stdout.splitlines() if l.startswith("SCENES="))
    assert set(line.removeprefix("SCENES=").split(",")) == {
        "runner", "parkour", "spiral", "tower"}
