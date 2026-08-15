"""Did the hand-built tower come out as it was designed?

A different question from the one ``tools/spiral_probe.py`` asks, and both have
to be answered. That probe asks whether the course is *safe* -- nothing inside
anything, nothing unreachable, the cone alone unclimbable -- and it works on
this tower too (``--plan hand``). This one asks whether the tower is the tower
in ``docs/TOWER.md``, which is a question only a hand-built one can fail.

Three sections:

**The design, checked on paper.** Every authored jump against the physics,
before a single cell is placed: an ``arc`` and a change of ``lift`` either name
a move a body has or they do not, and the answer is arithmetic. This catches
the whole class of "I wrote a four-block up-jump" without running anything, and
names the level, the beat and the node. It also checks the three-window rule on
the rises -- the ceiling over a level is the floor of the level three above, so
three consecutive rises *are* the head-room.

**Fidelity.** What actually got built. A landing is *exact* when placement took
it as authored, on a *fallback* when the lattice or the terrain forced a
different height or distance, and *lost* when the beat was truncated to protect
the exit climb's run-up or refused outright. Exact is the number that matters:
it is the fraction of the design that survived contact with the world.

**Coverage.** Which levels and which beats a run actually shows, because a
level nobody reaches is a level not worth designing, and a beat that is always
the one truncated should be earlier in its level.

    python tools/tower_probe.py --runs 12 --blocks 320
    python tools/tower_probe.py --design-only        # instant, no course grown
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ["BRAINROT_HEADLESS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from brainrot.scenes import handplan as hp
from brainrot.scenes import parkourkit as pk
from brainrot.scenes import spiralplan as sp

#: Kinds whose reach is one jump impulse. Everything else in the vocabulary is
#: there precisely because it is not, and checking a ladder against ``hop_span``
#: would be checking the wrong thing.
BALLISTIC = ("hop", "slide")


def _surface(node: dict, was: float) -> float:
    """The walking height an authored node lands at, above the terrace floor.

    Stateful, because half the vocabulary is. ``lift`` is measured from the
    terrace and ``step_y`` is measured from the landing before -- a ladder does
    not know or care how high off the floor it started -- so a checker that
    reads ``lift`` off a climb node is reading a default, and every jump after
    a climb is then measured against the wrong height. That is exactly what
    was happening: the two beats the fidelity probe reported as never once
    coming out as authored were both the beat *after* a climb.
    """
    if node.get("step_y") is not None:
        return was + node["step_y"]
    form = node.get("form", "full")
    lift = node.get("lift", 1)
    # ``form="floor"`` places no block: the cell must already be solid ground,
    # so ``Course._node`` clamps its lift to exactly zero. A checker that reads
    # the authored value instead measures a landing a whole block above the one
    # that gets built, passes it on paper, and then every jump after it in the
    # beat is checked against a height the body never reaches.
    if form == "floor":
        lift = 0
    return lift + pk.FORMS.get(form, 1.0)


def _beats(lv) -> list:
    """A level's beats, each once. ``filler`` defaults to the last two beats,
    so the naive concatenation reports every complaint about them twice."""
    out, seen = [], set()
    for beat in lv.beats + tuple(lv.filler):
        if id(beat) in seen:
            continue
        seen.add(id(beat))
        out.append(beat)
    return out


#: The one landing of a level that is allowed to stand on the terrace: the
#: first of the first beat, which is where the crossing from the level below
#: puts the body down. Every other landing is at least two blocks up, because
#: a body steps up one -- so a landing at ``lift=1`` is one a fall walks
#: straight back onto, and a jump you can walk back to is a jump that cost
#: nothing to miss. ``docs/REHASH.md`` is the whole argument.
DECK_MIN = 2


#: The most a single authored landing may lose. A fall onto another platform
#: is a showpiece and the format's only genuinely long jump; a fall of four or
#: more is the deck coming back down to meet the terrace.
DROP_MAX = 3.0


def cruise(lv) -> float:
    """The walking height the level's own course leaves the body at.

    Its filler repeats and holds its height (``check_climb``), so this is
    where the exit starts from -- and on a level whose deck reaches the next
    terrace on its own, there is nothing left for an exit to climb.
    """
    surf = 1.0
    for _name, specs in list(lv.beats) + list(lv.filler):
        for spec in specs:
            surf = _surface(spec, surf)
    return surf


def check_climb(lv) -> list[str]:
    """A level flies over its terrace, and it climbs on balance.

    Four rules. The first is the safety criterion of ``docs/REHASH.md`` in
    design data, and the rest are the owner's shape:

    * **only the threshold touches the floor.** Everything after the level's
      first landing stands at least ``DECK_MIN`` blocks over the terrace, so a
      body that falls to the ground cannot step back up onto it. One block up
      is one step up, and one step up is a jump that cost nothing to miss.
    * **a drop is a showpiece, not a route.** Descents are allowed -- a
      crevasse you fall into, a balcony you come off, the quarry -- because a
      fall onto another platform four blocks over the terrace is not the thing
      the criterion forbids. Falling more than ``DROP_MAX`` at once is.
    * **the level ends higher than it began.** Whatever happens in between,
      the way out is up.
    * **the filler holds its height.** It repeats, so anything it gains it
      gives back at the seam where it loops -- the one descent nobody writes
      and everybody ships. Put the level's character in its materials, its
      verbs and its lids; put the climb in the script.
    """
    out: list[str] = []
    floor = 1.0                     # the terrace's own walking surface
    surf, prev_name, opened = None, "", None
    for b, (name, specs) in enumerate(lv.beats):
        for k, spec in enumerate(specs):
            got = _surface(spec, surf if surf is not None else floor)
            if b == 0 and k == 0:
                opened = got
            elif got < floor + DECK_MIN - 1e-6:
                out.append(f"{lv.name}/{name}[{k}]: stands {got - floor:.1f} "
                           f"over the terrace -- only a level's first landing "
                           f"may be under {DECK_MIN:.0f}")
            if surf is not None and surf - got > DROP_MAX + 1e-6:
                out.append(f"{lv.name}/{name}[{k}]: falls {surf - got:.1f} "
                           f"from {prev_name} -- more than {DROP_MAX:.0f} is "
                           f"the deck coming back down to the terrace")
            surf, prev_name = got, f"{name}[{k}]"
    if surf is not None and opened is not None and surf < opened - 1e-6:
        out.append(f"{lv.name}: the script ends {opened - surf:.1f} below "
                   f"where it opened -- the way out is up")
    if lv.filler:
        top, fsurf = surf, surf
        for name, specs in lv.filler:
            for k, spec in enumerate(specs):
                got = _surface(spec, fsurf if fsurf is not None else floor)
                if got < floor + DECK_MIN - 1e-6:
                    out.append(f"{lv.name}/{name}[{k}] (filler): stands "
                               f"{got - floor:.1f} over the terrace")
                if fsurf is not None and fsurf - got > DROP_MAX + 1e-6:
                    out.append(f"{lv.name}/{name}[{k}] (filler): falls "
                               f"{fsurf - got:.1f}")
                fsurf = got
        if top is not None and fsurf is not None and abs(fsurf - top) > 1e-6:
            out.append(f"{lv.name}: the filler ends {fsurf - floor:.1f} over "
                       f"the terrace where it began {top - floor:.1f} -- it "
                       f"repeats, so anything it gains it gives back at the "
                       f"seam")
    return out


def check_design() -> list[str]:
    """Every authored jump against the physics. Returns the complaints."""
    bad: list[str] = []
    rises = [lv.rise for lv in hp.LEVELS]
    for i, lv in enumerate(hp.LEVELS):
        window = rises[i] + rises[(i + 1) % len(rises)] + rises[(i + 2) % len(rises)]
        head = window - sp.FLOOR_T
        if not 6 <= head <= 16:
            bad.append(f"{lv.name}: three rises from here sum to {window}, "
                       f"leaving {head} blocks of open air (want 6..16)")
        # A level's band used to be checked against the band of the section
        # three below it, because a wider one had a strip of *that* level's
        # cliff painted over its own lane. That was never a design rule: the
        # cone painted the core wall before the terrace slab and ``_ring``
        # skips a claimed cell. Fixed in ``Cone.emit_layer`` on 2026-08-13 --
        # the slab is laid first and the wall under it is capped at the slab's
        # own inner edge -- and a band is free again. See
        # ``test_the_terrace_is_painted_in_its_own_levels_floor``.
        if lv.exit not in sp.ASCENTS:
            bad.append(f"{lv.name}: exit {lv.exit!r} is not one of "
                       f"{sorted(sp.ASCENTS)}")
        for key, val in lv.skin.items():
            if isinstance(val, str) and key in hp.ROLES \
                    and val not in pk.MATERIALS:
                bad.append(f"{lv.name}: skin {key}={val!r} is no material")
        # **Where an authored exit tops out**, which is a whole class of bug and
        # was invisible until a level instrumented it. A climb that ends higher
        # than one block over the next level's floor cannot find the far ground
        # from up there: the crossing is refused, the body comes back down onto
        # *this* terrace, and the reliability chain climbs out all over again --
        # five ascent landings a visit, reading 100% on every per-beat check
        # because every landing was placed. It is the owner's "it climbs and
        # then drops back to where it started" in level data rather than in the
        # engine, and it is pure arithmetic, so it belongs here where it costs
        # nothing to ask.
        if lv.exit_beats:
            # From where the level's own course leaves the body, not from the
            # terrace. The design climbs now (``check_climb``), so an exit
            # written on ``step_y`` starts at the deck the script cruises at
            # and a checker that assumes the floor under-counts it by the whole
            # height of the level.
            surface = cruise(lv) - 1.0
            for spec in lv.exit_beats:
                if spec.get("step_y") is not None:
                    surface += spec["step_y"]
                elif spec.get("lift") is not None:
                    surface = spec["lift"]
            if surface is not None and surface > lv.rise + 1:
                bad.append(f"{lv.name}: the authored exit tops out {surface} "
                           f"over the terrace against a rise of {lv.rise} -- "
                           f"the crossing cannot reach the far ground from "
                           f"more than {lv.rise + 1} and the body falls back")
        # Across beat boundaries as well as within them, because beats play in
        # the order they are written and the jump from the last landing of one
        # to the first of the next is a jump like any other. Checking only
        # inside a beat missed exactly that: a climb ending eight blocks up and
        # the next beat opening two and a half below it, which is a drop no
        # hop has and which the fidelity probe reported as a beat that never
        # once came out as authored. The filler is walked twice so that the
        # seam where it loops back on itself is checked too.
        bad.extend(check_climb(lv))
        prev = None
        surf = 1.0
        for beat, specs in list(lv.beats) + list(lv.filler) * 2:
            for k, spec in enumerate(specs):
                style = spec["style"]
                # No escape hatch for "it looks like a colour". The renderer
                # builds one face-strip recipe per entry in ``MATERIALS`` and
                # asks for a landing's style by name at draw time, so a style
                # that is not in there is a ``KeyError`` a hundred and forty
                # frames into a run -- which is exactly how this check came to
                # be strict.
                for extra in ("pedestal_style", "climb_style"):
                    val = spec.get(extra)
                    if val and val not in hp.ROLES and val not in pk.MATERIALS:
                        bad.append(f"{lv.name}/{beat}[{k}]: {extra}="
                                   f"{val!r} is no material")
                if style not in hp.ROLES and style not in pk.MATERIALS:
                    bad.append(f"{lv.name}/{beat}[{k}]: no material {style!r}")
                kind = spec.get("kind", "hop")
                was, surf = surf, _surface(spec, surf)
                if prev is not None and kind in BALLISTIC:
                    rise = surf - was
                    # The authored point is ``arc`` along the corridor and
                    # ``radial`` across it -- and a change of ``hug`` is across
                    # it too -- so what the body actually jumps is the
                    # hypotenuse. Both ends are then set back from their own
                    # block's centre by that form's ``EDGE``, which is three
                    # times as far off a ``wide`` platform as off a cube: a
                    # five-block gap between two mushroom caps is a three-block
                    # jump and reading it as five condemns a good design.
                    across = spec.get("radial", 0.0)
                    if spec.get("hug") and prev.get("hug"):
                        across += spec["hug"] - prev["hug"]
                    reach = (math.hypot(spec.get("arc", 3.0), across)
                             - pk.EDGE[prev.get("form", "full")]
                             - pk.EDGE[spec.get("form", "full")])
                    speed = pk.ICE_AIR if kind == "slide" else pk.AIR_SPEED
                    lo, hi = pk.hop_span(rise, speed)
                    if rise > 1.001:
                        bad.append(f"{lv.name}/{beat}[{k}]: rises {rise:+.1f} "
                                   f"on a {kind} -- nothing rises two blocks")
                    elif not lo - 0.01 <= reach <= hi + 0.01:
                        bad.append(
                            f"{lv.name}/{beat}[{k}]: {reach:.2f} m at "
                            f"{rise:+.1f} is outside {lo:.2f}..{hi:.2f}")
                if spec.get("lift", 1) > sp.LIFT_MAX:
                    bad.append(f"{lv.name}/{beat}[{k}]: lift "
                               f"{spec['lift']} over LIFT_MAX {sp.LIFT_MAX}")
                prev = spec
    return bad


def grow(run: int, blocks: int):
    cone = hp.Cone(random.Random(run * 977 + 13), 0)
    course = hp.Course(random.Random(run * 6151 + 29), cone)
    seen = list(course.blocks)
    for _ in range(blocks):
        seen.append(course.spawn())
        if len(course.blocks) > sp.AHEAD:
            course.advance(len(course.blocks) - sp.AHEAD + sp.TRAIL)
    return cone, course, seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=int, default=12)
    ap.add_argument("--blocks", type=int, default=320)
    ap.add_argument("--design-only", action="store_true")
    args = ap.parse_args()

    print(f"THE DESIGN  ({len(hp.LEVELS)} levels, "
          f"{sum(len(b[1]) for lv in hp.LEVELS for b in lv.beats)} "
          f"authored landings)")
    bad = check_design()
    if bad:
        for line in bad:
            print(f"  BAD  {line}")
    else:
        print("  every authored jump is one a body can make")
    print(f"  cycle climbs {sum(lv.rise for lv in hp.LEVELS)} blocks over "
          f"{len(hp.LEVELS) / sp.LEVELS_PER_TURN:.0f} revolutions")
    if args.design_only:
        return 1 if bad else 0

    exact = fallback = stuck = 0
    exits: Counter = Counter()
    machinery = machined = 0
    by_level: dict[str, Counter] = defaultdict(Counter)
    beats: Counter = Counter()
    by_beat: dict[str, list] = defaultdict(lambda: [0, 0])
    levels_seen: Counter = Counter()
    laid = 0
    ascent = 0
    reach: list[float] = []
    for run in range(args.runs):
        _, course, seen = grow(run, args.blocks)
        for blk in seen:
            if blk["move"] is None:
                continue
            laid += 1
            name = blk["theme"]
            levels_seen[name] += 1
            if blk["segment"] == "ascent":
                ascent += 1
                by_level[name]["ascent"] += 1
                # What actually wrote this landing. The exit climb is labelled
                # ``ascent`` whether the level authored it landing by landing
                # or the engine improvised it, and the label is load-bearing
                # in eight other places -- so until ``origin`` existed, a
                # third of the course sat outside every fidelity number the
                # project had, and "the exit climb is machinery" was an
                # assumption nobody had ever been able to check.
                exits[blk.get("origin") or "other"] += 1
                if blk.get("origin") == "design":
                    exits["exact" if blk["exact"] else "fallback"] += 1
                    by_level[name]["exit_design"] += 1
                    by_level[name]["exit_exact"] += bool(blk["exact"])
                else:
                    by_level[name]["exit_" + (blk.get("origin") or "other")] \
                        += 1
                continue
            if blk["segment"] == "stuck":
                stuck += 1
                by_level[name]["stuck"] += 1
                continue
            if blk["segment"] in hp.MACHINERY:
                # The lock across the level's break and the crossing through
                # its landmark are aimed at world features, not written down
                # landing by landing. Counting them as design answers a
                # different question from the one this section asks.
                machinery += 1
                machined += bool(blk["exact"])
                by_level[name]["machinery"] += 1
                continue
            beats[blk["segment"]] += 1
            key = f"{name}/{blk['segment']}"
            by_beat[key][0] += 1
            if blk["exact"]:
                exact += 1
                by_level[name]["exact"] += 1
                by_beat[key][1] += 1
            else:
                fallback += 1
                by_level[name]["fallback"] += 1
            if blk["move"].kind in BALLISTIC:
                frm, to = blk["move"].frm, blk["move"].to
                reach.append(math.dist((frm[0], frm[2]), (to[0], to[2])))
        stuck += course.stuck - by_level[name]["stuck"] * 0

    designed = exact + fallback
    print(f"\nFIDELITY  ({args.runs} runs x {args.blocks} landings)")
    print(f"  landings laid                   {laid}")
    print(f"  designed content                {designed} "
          f"({100 * designed / max(1, laid):.0f}% of the course)")
    print(f"  ...placed as authored           {exact} "
          f"({100 * exact / max(1, designed):.1f}%)")
    print(f"  ...placed on a fallback         {fallback} "
          f"({100 * fallback / max(1, designed):.1f}%)")
    print(f"  machinery (lock, crossing)      {machinery} "
          f"({100 * machined / max(1, machinery):.0f}% aimed as planned)")
    print(f"  the exit climb                  {ascent} "
          f"({100 * ascent / max(1, laid):.0f}% of the course)")
    if reach:
        reach.sort()
        print(f"  designed jump min/mean/max      {reach[0]:.2f} / "
              f"{sum(reach) / len(reach):.2f} / {reach[-1]:.2f} m")
        print(f"  jumps over 4 m                  "
              f"{100 * sum(1 for r in reach if r >= 4.0) / len(reach):.0f}%")

    designed_exit = exits["design"]
    print("\nTHE WAY OUT  (what the exit climb is actually made of)")
    print(f"  exit-climb landings             {ascent}")
    print(f"  ...the level wrote them         {designed_exit} "
          f"({100 * designed_exit / max(1, ascent):.0f}%), "
          f"{100 * exits['exact'] / max(1, designed_exit):.1f}% as authored")
    print(f"  ...the crossing                 {exits['crossing']} "
          f"({100 * exits['crossing'] / max(1, ascent):.0f}%)")
    print(f"  ...a generated staircase        {exits['stair']} "
          f"({100 * exits['stair'] / max(1, ascent):.0f}%)")
    print(f"  ...walking to the chasm lip     {exits['approach']} "
          f"({100 * exits['approach'] / max(1, ascent):.0f}%)")
    print(f"  ...a generated climb            {exits['climb']}")
    print(f"  ...the reliability chain        "
          f"{exits['recover'] + exits['other']}")
    worst = sorted(((by_level[k]["exit_stair"], k) for k in by_level),
                   reverse=True)[:5]
    if worst and worst[0][0]:
        print("  most staircase, by level        "
              + ", ".join(f"{k} {v}" for v, k in worst if v))

    print(f"\nCOVERAGE  ({len(levels_seen)} of {len(hp.LEVELS)} levels seen, "
          f"{len(beats)} distinct beats)")
    order = {lv.name: i for i, lv in enumerate(hp.LEVELS)}
    for name in sorted(levels_seen, key=lambda k: order.get(k, 99)):
        c = by_level[name]
        tot = c["exact"] + c["fallback"]
        print(f"  {name:<16} {levels_seen[name]:4d} landings   "
              f"design {tot:3d}  exact {100 * c['exact'] / max(1, tot):3.0f}%"
              f"   climb {c['ascent']:3d}"
              + (f"   STUCK {c['stuck']}" if c["stuck"] else ""))
    missing = [lv.name for lv in hp.LEVELS if lv.name not in levels_seen]
    if missing:
        print(f"  never reached: {', '.join(missing)}")

    weak = sorted(((h / t, t, k) for k, (t, h) in by_beat.items() if t >= 12),
                  key=lambda kv: kv[0])[:10]
    print("\nBEATS THAT DID NOT COME OUT AS AUTHORED")
    if weak and weak[0][0] < 0.98:
        for rate, tot, k in weak:
            if rate >= 0.98:
                break
            print(f"  {100 * rate:3.0f}% of {tot:4d}   {k}")
    else:
        print("  none: every beat placed as authored at least 98% of the time")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
