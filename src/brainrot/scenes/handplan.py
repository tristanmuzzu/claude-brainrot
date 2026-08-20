"""The hand-built tower: thirty-three designed levels, climbed in order.

This module is :mod:`brainrot.scenes.spiralplan` with one thing taken away and
one thing put in its place. Taken away: the weighted table that chose what the
next stretch of course would be. Put in its place: a page of levels, each
written down landing by landing. Everything else -- the building, vanilla's
motion numbers, the occupancy ledger, the reservations, the pedestals, the
terrain painting, the props, the exit climb and every check that says a landing
is legal -- is the generator's and is reused unchanged. ``docs/TOWER.md`` is
the design; :mod:`brainrot.scenes.handlevels` is that design as data; this
file is the machinery that reads it.

**Authored intent, mechanical placement, verified physics.** The three layers
are the whole idea. *Authored* is every landing: material, distance, height,
form, lid, liquid, shell, all written down in ``handlevels``. *Mechanical* is
the lattice: :meth:`Course._targets` resolves an authored point to the nearest
whole cells exactly as it always did. *Verified* is :meth:`Course._attempt`,
untouched: an authored jump no body can make is refused exactly as a generated
one would be, and ``tools/tower_probe.py`` says which. **A level that measures
badly is a level designed badly**, and the fix belongs in ``handlevels``
rather than in a tolerance.
"""

from __future__ import annotations

import math
import random

from . import spiralplan as sp
from .handlevels import LEVELS, ROLES, Level, n  # noqa: F401
from .spiralplan import (  # noqa: F401  -- the renderer reads these off the plan
    HANGING,
    ODDITIES,
    PROP_BUDGET,
    PROP_KINDS,
    THEMES,
    TRAIL,
    Section,
    Theme,
)

#: How many landings generation keeps in front of the body, and higher than the
#: generated tower's sixteen because the terraces are half as long again. A
#: section is dressed when the *generator* leaves it, so with sixteen the body
#: was standing in an undressed section a third of the time and the terraces
#: came back swept. Read by the renderer off the plan module.
AHEAD = 26

#: Segments that are *machinery*, not design: the climb out of a level, the
#: recoveries, the lock across the level's wide break, and the crossing through
#: a gated landmark. They are inserted between script beats and aimed at world
#: features, so a fidelity number that counts them is answering a different
#: question from "did the design survive being built" -- the lock alone took
#: that number from 97% to 91.5% when it landed, and it was never a fallen-back
#: authored landing. Read by ``tools/tower_probe.py`` and ``tests/test_tower``.
MACHINERY = frozenset({"ascent", "start", "stuck", "recover", "lock",
                       "landmark"})

#: The lowest a landing of this tower may stand over its own terrace, apart
#: from the one apron landing a level opens on. A body steps up one block, so
#: anything at one is something a fall walks straight back onto -- and a jump
#: you can walk back to is a jump that cost nothing to miss. The design side
#: of the same rule is ``tools/tower_probe.py`` ``check_climb``; the number it
#: is held to is ``tools/reentry_probe.py``. See ``docs/REHASH.md``.
DECK_MIN = 2


# ---------------------------------------------------------------------------
# The building
# ---------------------------------------------------------------------------

class Cone(sp.Cone):
    """The generated cone, with its levels read off the table instead of rolled.

    Everything analytic about the building -- :meth:`rock`, :meth:`unwrap`, the
    flare, the ribs, the soffit, the profiles, the aprons -- is inherited
    untouched. What changes is that a level's theme, height, chasm, ground
    profile and landmark are a design decision.

    The one thing still rolled is **where in the cycle the tower starts**
    (:attr:`phase`), and it is worth keeping: the tower is the same tower every
    run, so without it every run would open at the gatehouse. With it, two runs
    a minute apart open in different places on a building the viewer comes to
    recognise, which is the whole reason to hand-build one.
    """

    #: Half as wide again as the generated tower, and the reason is the whole
    #: economics of a designed level. A level is a third of a revolution, its
    #: exit climb needs a fixed run-up in *blocks*, and what is left over is
    #: the design. At the generated radius that left about four landings a
    #: level against seven for the climb -- so a hand-built tower would have
    #: been three fifths staircase, which is what hand-building it was meant to
    #: stop. A wider circle lengthens every terrace and nothing else. It also
    #: straightens the corridor, which the camera likes.
    base_r = 36.0

    def __init__(self, rng, base_y: int = 0) -> None:
        # Drawn before ``super().__init__``, which lays the first section.
        self.phase = rng.randrange(len(LEVELS))
        super().__init__(rng, base_y)

    def design(self, index: int) -> Level:
        """The designed level at a section index. Cyclic: that is the loop."""
        return LEVELS[(index + self.phase) % len(LEVELS)]

    def _extend_section(self) -> None:
        i = len(self.sections)
        u0 = self._u_lo + i * sp.LEVEL_ARC
        design = self.design(i)
        if i == 0:
            y, rise = self.base, 0
        else:
            # A section's ``rise`` is how much higher it is than the one
            # *before* it, so it belongs to the design of the level below.
            rise = self.design(i - 1).rise
            y = self.sections[-1].y + rise
        # The chasm is authored in blocks and converted here, because a fixed
        # angle would be six blocks wide at the bottom of the tower and ten at
        # the top -- and how far a body can jump does not care how wide the
        # tower is.
        radius = max(6.0, self.rim_at(y))
        section = Section(
            i, THEME_BY_NAME[design.name], u0, u0 + sp.LEVEL_ARC, y, rise,
            min(design.gap / radius, sp.LEVEL_ARC * 0.45),
            # The design *is* the difficulty here, so nothing is scaled by a
            # pitch drawn per level. Held at one so that the exit climb and the
            # dressing behave as they do at the top of the generated range.
            1.0, "", design.profile, design.shelf, design.landmark,
            design.band)
        section.breaks = design.breaks
        #: The height this level's course runs at, which the machinery aims
        #: at: a gated landmark is stood on a plinth this tall, so the course
        #: goes through its passage instead of past its foot.
        section.deck = design.deck
        self.sections.append(section)


def _skin(design: Level) -> Theme:
    """The level's own theme: its base one, renamed, with its materials swapped.

    Renamed because the scene puts :attr:`Theme.name` on screen as the name of
    the place you are in, and two levels sharing a base theme is exactly the
    thing this tower exists to stop being visible.
    """
    base = sp.THEME_BY_NAME[design.theme]
    kw = {
        "ground": base.ground, "sub": base.sub, "rock": base.rock,
        "accent": base.accent, "liquid": base.liquid, "glow": base.glow,
        "props": base.props, "features": base.features, "sky": base.sky,
        "dark": base.dark, "candy": base.candy, "exits": (design.exit,),
        "step": base.step, "floor": base.floor,
    }
    kw.update(design.skin)
    return Theme(design.name, **kw)


#: Every theme the renderer may be handed, by name. The generated themes are
#: still in here because a block records the *name* of the theme it was laid
#: in and the scene looks that name up again when it draws it -- and a level's
#: theme is its own, renamed after the level.
THEME_BY_NAME: dict[str, Theme] = dict(sp.THEME_BY_NAME)
THEME_BY_NAME.update({lv.name: _skin(lv) for lv in LEVELS})


# ---------------------------------------------------------------------------
# The course
# ---------------------------------------------------------------------------

class Course(sp.Course):
    """The generated course, reading its content off the page.

    One method is replaced. :meth:`_choose_feature` no longer rolls against a
    weighted table; it takes the next beat of the level the frontier is
    standing in. Everything either side of that -- when the exit climb starts,
    how a beat is truncated so it cannot eat the climb's run-up, how a node
    becomes a cell, every check that says the cell is legal, what happens when
    one is not -- is the generator's, unchanged and already measured.
    """

    def __init__(self, rng, cone: Cone, hop_rng=None) -> None:
        #: Section index -> how many beats of that level have been laid. Kept
        #: per level rather than as one counter because generation runs ahead
        #: and can be part-way into the next level while the body is still in
        #: this one.
        self._cursor: dict[int, int] = {}
        #: Break lips whose lock crossing was already laid.
        self._locked: set[float] = set()
        #: Levels whose landmark crossing was already offered.
        self._crossed: set[int] = set()
        #: ...and those whose gate the frontier got past before it could be
        #: offered, so the structure came down. Counted apart because the two
        #: are opposite outcomes and one number cannot say which happened.
        self._retired: set[int] = set()
        #: Levels where at least one of the crossing's own landings is built:
        #: the structure has been entered, so it stays whatever happens next.
        self._gate_hit: set[int] = set()
        #: Beats asked for, and beats that came out with every landing placed
        #: as authored. The fidelity numbers; see ``tools/tower_probe.py``.
        self.authored = 0
        self.as_designed = 0
        super().__init__(rng, cone, hop_rng)

    ahead = AHEAD

    #: **The course flies over its terrace; it does not stand on it.** A stack
    #: of terrain down to the ground is a staircase back up to the landing it
    #: holds, and a landing you can walk back up to is a jump that cost nothing
    #: to miss. See ``docs/REHASH.md`` and ``tools/reentry_probe.py``; the
    #: generated tower keeps the opposite default and its own contract.
    pedestal_default = False

    #: ...and a landing never falls back under the deck. See
    #: ``spiralplan.Course._node``.
    lift_floor = DECK_MIN

    def _body_lift(self) -> int:
        """Where the body actually is over its terrace, unfloored."""
        prev = self.blocks[-1]
        lv = self.cone.level(self.cone.level_index(self.u_of(prev)))
        return round(self.surface(prev) - lv.y)

    def _here_lift(self) -> int:
        """How far above its own terrace the course is standing, in blocks.

        Machinery -- the lock, the approach to a doorway, a recovery hop -- is
        inserted *between* script beats, and every one of them used to ask for
        ``lift=1``. On a level whose course climbs, that is not a neutral
        default but a staircase back down to the terrace: it undoes the climb,
        it lands the body a step above the ground it is meant to have left, and
        the fall from the next jump walks straight back up. Asking where the
        body actually is costs one lookup.
        """
        prev = self.blocks[-1]
        lv = self.cone.level(self.cone.level_index(self.u_of(prev)))
        # Floored at two, and that floor is the whole rule: one block over the
        # terrace is one step up, so a machinery landing there is a landing a
        # fall walks back onto -- and the body reaches it off the apron, which
        # is the one place a level *is* one block up. A hop from the apron to
        # two is an ordinary +1 and legal from anywhere.
        return max(DECK_MIN, min(sp.LIFT_MAX,
                                 round(self.surface(prev) - lv.y)))

    def _level_budget(self):
        """As the generator's, except that a climb out is not a staircase.

        The reserve is what the exit is *going* to cost, and the generator has
        to assume the worst because it does not know which of the four shapes
        it will get until it asks. A designed level does know. A staircase
        spends a landing a block and needs seven of them to leave a six-block
        level; a ladder spends three whatever the height -- a block to launch
        from, the ride, and the jump across. Reserving seven for a ladder threw
        away sixteen blocks of terrace, which on a level that only has forty is
        most of the design.

        The fallback still exists and still costs seven, so this reserves a
        landing more than the ladder needs. If the ladder cannot be built the
        stair takes over with less room than it wants, and what catches that is
        the same chain that catches it in the generated tower, ending in a
        ladder up the far wall of the chasm.
        """
        lv, need, want, radius = super()._level_budget()
        kind = self.cone.design(lv.index).exit
        if kind != "stair" and need >= 3:
            want -= (max(1, need) - 2) * sp.ASCENT_ARC
        return lv, need, want, radius

    def _commit(self, prev: dict, node: dict, got: dict) -> dict:
        blk = super()._commit(prev, node, got)
        self._reserve_noclimb(blk)
        return blk

    def _reserve_noclimb(self, blk: dict) -> None:
        """Hold the cells a fall could climb back up on, beside this landing.

        The course flies over its terrace now, so a fall lands on the terrace
        -- and the terrace is *dressed*: outcrops, dunes, pond rims, the foot
        of a landmark. Measured, that dressing was three quarters of what was
        left of the re-entry rate after the design itself was raised: the
        landings were out of reach and the scenery beside them was a
        staircase. Nothing may be built in the ring around a landing between
        the terrace and the landing's own height.

        Reserved rather than checked, and for the reason everything else here
        is: dressing runs *after* the course is laid, so a check at placement
        time would be asking about cells nothing has filled in yet.
        """
        lv = self.cone.level(self.cone.level_index(self.u_of(blk)))
        top = int(self.surface(blk))
        if top - lv.y < DECK_MIN:
            return                      # the apron: it is meant to be reachable
        for x, y, z in sp.footprint(blk["x"], blk["y"], blk["z"],
                                    blk["form"]) or ((blk["x"], blk["y"],
                                                      blk["z"]),):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for cy in range(lv.y, top):
                        self.noclimb.add((x + dx, cy, z + dz))

    def _recover_lifts(self):
        """As the kernel's, but starting from where the body is.

        A recovery hop is the commonest machinery there is and it used to be
        laid at ``lift=1`` -- so a single refused landing on a level running
        four blocks up put the body back on the terrace, and everything after
        it inherited the mistake. Upward before downward for the same reason
        the far-side recovery exists: a hop that loses height on this format
        cascades.
        """
        here = self._here_lift()
        out = [here, here + 1, here - 1, here + 2, here - 2, DECK_MIN, 1]
        return tuple(dict.fromkeys(x for x in out if 1 <= x <= sp.LIFT_MAX))

    def _choose_feature(self, lv) -> list[dict]:
        # Two machinery-inserted features and one script, in the order the
        # ground puts them in. A lock is never *clipped* -- half a lock is an
        # approach to a hole with no island in it -- so a lock beyond the
        # doorway simply waits, and the crossing goes first.
        gate = self._gate_dist(lv)
        lock = self._lock_nodes(lv, limit=gate)
        if lock:
            return lock
        cross = self._landmark_nodes(lv)
        if cross:
            return cross
        design = self.cone.design(lv.index)
        cursor = self._cursor.get(lv.index, 0)
        self._cursor[lv.index] = cursor + 1
        if cursor < len(design.beats):
            name, specs = design.beats[cursor]
        else:
            # The terrace outlasted the script. How much terrace a level has
            # depends on how far up the flare it is and on how tall the level
            # above it is, so this is the normal case on the wide turns rather
            # than a design that ran short.
            fill = design.filler
            name, specs = fill[(cursor - len(design.beats)) % len(fill)]
        self.segment = name
        out = self._clip_to_landmark(
            lv, [self._node(**_resolve(spec, lv.theme)) for spec in specs])
        # Counted after the clip, not before: a beat cut short of a gate was
        # never asked for, and charging the design for a landing the machinery
        # withdrew is how a fidelity number stops meaning anything.
        self.authored += len(out)
        return out

    def _landmark_nodes(self, lv) -> list[dict] | None:
        """Run the course *through* the level's landmark.

        A structure beside the course is scenery, and the owner's report was
        that he watched five minutes of strip and saw one -- against a 97%
        placement rate. Measured with ``tools/landmark_probe.py``, only 18% of
        landmarked levels ever held their structure at 25 degrees for a second
        and a half, and none ever reached 40: they were placed, and they were
        never framed.

        So the big structures carry a passage (``spiralplan.GATED``), laid out
        and held open with the structure itself, and this is the machinery that
        aims the course at it: ordinary approach hops to cover the ground, then
        the three stored landings -- short of the doorway, inside it, out the
        far side. Exactly the shape of :meth:`_lock_nodes`, for the same
        reason: a world feature the course has to answer, inserted between
        script beats, cursor untouched.

        A walk gate is an interior three cells high and is crossed at a run,
        because one jump impulse always rises 1.25 m and the head then sweeps
        three cells above the take-off -- a lintel low enough to read as a
        doorway is a lintel every arc under it is refused by. A hop gate is
        five high, and those are jumped through.
        """
        dist = self._gate_dist(lv)
        if dist is None or dist > 18.0:
            # Wide, because the *other* inserted feature -- the lock across the
            # level's wide break -- lays five landings and eighteen blocks in
            # one go, and a doorway the frontier is already past is a wall.
            return None
        cells, void, kind = self.landmark_cross[lv.index]
        ahead = self._gate_ahead(lv)
        # Offered once. Retrying the ones whose first leg is refused sounds
        # free and measures badly: a refused leg ends in ``_last_resort``,
        # whose recovery hop is three to five blocks in whatever direction
        # will take one, so by the second attempt the doorway is behind the
        # body. Measured, offering up to three times took retirements from 18
        # in twelve runs to 65 and unchecked placements from 0.34% to 0.60%.
        self._crossed.add(lv.index)
        # The passage was held against the whole world including us. Handing
        # it over is what makes the crossing placeable -- ``_path_clear``
        # treats a held cell as solid, so an arc through a held doorway is
        # refused exactly as an arc through a wall is.
        self._hold_cells -= set(void)
        theme = lv.theme
        out: list[dict] = []
        run = max(0.0, dist - 3.4)
        if run > 1.2:
            legs = max(1, int(math.ceil(run / 4.0)))
            # At the height the body is already at, not at one -- and
            # *climbing* to the doorway's own, a block a leg. The stored
            # landings inside the structure are cells and cannot move: the
            # gate stands on a plinth as tall as the level's deck, so an
            # approach that stays low arrives under the passage and the leg
            # into it is a jump of two or three, which no body has. Measured
            # before this climbed, seven crossings a sweep fell through to the
            # unchecked answer and the test that says they must not, failed.
            here = self._here_lift()
            want = max(DECK_MIN, self._gate_lift(lv))
            for i in range(legs):
                step = max(here, min(want, here + i + 1)) if want > here \
                    else here
                out.append(self._node(theme.rock, arc=run / legs, lift=step,
                                      spread=1, ramp=False, label="landmark"))
                here = step
        prev = None
        inside = set(void)
        for cell in ahead:
            arc = 3.4 if prev is None else math.dist(
                (prev[0], prev[2]), (cell[0], cell[2]))
            out.append(self._node(
                theme.accent if cell in inside else theme.rock, arc=arc,
                lift=1,
                # A landing *inside* a walk gate is arrived at at a run: the
                # arc of a jump would take the head through the lintel. Every
                # other leg -- including the way in, which comes off ordinary
                # course laid where the helix put it -- is a jump.
                kind="walk" if (kind == "walk" and cell in inside) else "hop",
                spread=0, ramp=False, at=cell, label="landmark"))
            prev = cell
        self.segment = "landmark"
        return out

    def _gate_lift(self, lv) -> int:
        """How high over its terrace this level's doorway stands, in blocks.

        The stored crossing cells are the answer -- they were laid out with the
        structure and they carry the plinth's height with them -- rather than
        the design's ``deck``, which is what the plinth was *asked* for and not
        always what fitted.
        """
        plan = self.landmark_cross.get(lv.index)
        if not plan or not plan[0]:
            return DECK_MIN
        return max(DECK_MIN, int(plan[0][0][1] - lv.y) + 1)

    def _gate_ahead(self, lv) -> list:
        """The stored landings the frontier has not gone past yet.

        A crossing is offered again if its first leg was refused, and by then
        the body may be standing between two of its landings -- so what is
        emitted is what is left, not what was planned.
        """
        plan = self.landmark_cross.get(lv.index)
        if plan is None:
            return []
        radius = max(6.0, self.cone.rim_at(lv.y))
        return [c for c in plan[0]
                if (self._u_at(self.u, c[0], c[2]) - self.u) * radius > 0.5]

    def spawn(self) -> dict:
        self._retire_gates()
        blk = super().spawn()
        if blk["segment"] == "landmark":
            # A crossing counts as *made* when the body is through the
            # doorway, not when the crossing was offered. The leg onto the
            # first stored cell is an ordinary jump from wherever the approach
            # happened to land, and it is refused often enough to matter --
            # measured, ten of twenty-three offered crossings never reached
            # their structure. Marking on the offer threw those away; this
            # lets the next feature pick up the landings that are left, from a
            # few blocks closer, which is what the approach legs are for.
            idx = self.cone.level_index(self.u_of(blk))
            plan = self.landmark_cross.get(idx)
            cell = (blk["x"], blk["y"], blk["z"])
            # *In the passage*, which is not the same as *on a stored cell*
            # and is the thing that matters. Measured over six runs: forty-one
            # crossings offered, eighteen put a landing inside the structure,
            # and only four of those were the exact stored landing. The
            # crossing's real work turns out to be handing the doorway over at
            # the right moment -- the approach hops then find it themselves,
            # because it is the only clear ground on the lane.
            if plan is not None and (cell in plan[1] or cell in plan[0]):
                self._gate_hit.add(idx)
        return blk

    def _retire_gates(self) -> None:
        """Give up on a gate the course has already run past, and take it down.

        A gated landmark is a structure standing across the running lane with
        one held passage through it. That is a good trade while the crossing is
        still to come and a bad one the moment it is not: what is left is a
        wall, and the level's remaining beats grind their whole recovery chain
        against it. Measured, holding the big structures without ever crossing
        them costs 1.96% unchecked against 0.30%; crossing them costs 0.77%,
        and retiring the ones that got away is the rest of the way back.
        """
        here = self.cone.section_at(self.u).index
        for idx in (here - 1, here):
            plan = self.landmark_cross.get(idx)
            if plan is None or idx in self._crossed:
                continue
            lv = self.cone.level(idx)
            if self._gate_ahead(lv):
                continue            # there is still a way through to take
            self._take_down(idx, lv, plan)

    def _take_down(self, idx: int, lv, plan, replace: bool = True) -> None:
        """Mark a gate crossed and, unless the body got through it, remove it."""
        self._crossed.add(idx)
        if idx in self._gate_hit:
            # The body went through it. Taking down a building the course has
            # already run into is the one thing worse than leaving a wall
            # standing.
            return
        self._retired.add(idx)
        self.landmark_cross.pop(idx, None)
        held = self.landmark_hold.pop(idx, None)
        self._hold_cells -= set(plan[1])
        if held is not None:
            self._hold_cells -= {c for c, _ in held[0]}
        if replace:
            self._replace_landmark(lv)

    def _abandon(self, prev: dict) -> None:
        """A crossing that has run out of answers takes its doorway with it.

        The passage is *held* while the crossing is live, and a held cell is
        solid to :meth:`_path_clear`. So a crossing whose leg cannot be placed
        used to leave the recovery chain arguing with the very wall the
        crossing existed to get through, and the run fell all the way to the
        one unchecked placement -- which is what
        ``test_the_course_goes_through_the_landmarks_it_gates`` asserts can
        never happen. Taking the gate down here hands those cells back before
        the first recovery hop is tried, which is the module's own rule
        (:meth:`_retire_gates`) applied one step earlier.
        """
        if self.segment != "landmark":
            return
        idx = self.cone.level_index(self.u_of(prev))
        plan = self.landmark_cross.get(idx)
        if plan is None or idx in self._crossed:
            return
        # ...and *without* standing the small landmark in its place. That
        # replacement is reserved ahead of the frontier, which is exactly
        # where the body is when a crossing dies, so it would hand the
        # recovery a fresh obstacle in the same breath as clearing one.
        self._take_down(idx, self.cone.level(idx), plan, replace=False)

    def _replace_landmark(self, lv) -> None:
        """Stand the *small* landmark ahead of the body instead.

        A retired gate leaves the level with nothing to be recognised by,
        which is the complaint this whole pass exists to answer. The fallback
        blueprint is a third the size and stands beside the course rather than
        across it, so it can go anywhere there is still terrace: a few bearings
        ahead of the frontier, ending before the exit climb's ground.
        """
        build = sp.LANDMARKS.get(lv.landmark)
        if not build:
            return
        cone = self.cone
        radius = max(6.0, cone.rim_at(lv.y))
        rng = random.Random(lv.index * 977 + cone.wind * 31)
        built = build(rng, lv.theme)
        if isinstance(built, tuple) and len(built) == 2 \
                and isinstance(built[0], list):
            cells, props = built
        else:
            cells, props = built, ()
        top = min(lv.u0 + (lv.u1 - lv.u0) * 0.55, self._gate_reach(lv))
        for ahead in (6.0, 9.0, 13.0, 17.0):
            u = self.u + ahead / radius
            if u > top:
                return
            if self._try_reserve_at(lv, u, cells, props):
                return

    def _gate_dist(self, lv) -> float | None:
        """How far ahead the next landing of this level's crossing is, or
        ``None`` if there is no crossing left to make on it."""
        if lv.index in self._crossed:
            return None
        ahead = self._gate_ahead(lv)
        if not ahead:
            return None
        radius = max(6.0, self.cone.rim_at(lv.y))
        return (self._u_at(self.u, ahead[0][0], ahead[0][2]) - self.u) * radius

    def _clip_to_landmark(self, lv, nodes: list[dict]) -> list[dict]:
        """Stop a script beat short of a crossing it would run past.

        A feature is chosen as a whole and a crossing is offered between
        features, so a long beat laid just before a gate walks the frontier
        past its own doorway -- and a doorway behind you is a wall.
        """
        dist = self._gate_dist(lv)
        if dist is None:
            return nodes
        room = dist - 3.0
        if room <= 0.0:
            return nodes
        keep, spent = [], 0.0
        for node in nodes:
            if keep and spent + node["arc"] > room:
                break
            keep.append(node)
            spent += node["arc"]
        return keep

    def _lock_nodes(self, lv, limit: float | None = None) -> list[dict] | None:
        """Cross the level's wide break: the one stretch no walker can.

        Every level's first floor break is cut too wide for any flat jump,
        and the course crosses it here -- an approach that gains height, an
        island floated over the hole, and a landing on the far ground. The
        island is the lock: it hangs one to two blocks up over a five-plus
        gap, so from the ground at the lip there is no jump onto it, and the
        only way across is to arrive the way the course arrives. The script
        beat that was due plays right after; the cursor is untouched.
        """
        if self._here_lift() > DECK_MIN:
            # **A course already above the terrace needs no lock.** The lock
            # exists to get a body across a hole in ground it is running on;
            # three blocks up, the hole is scenery it flies over, and the lock's
            # own approach legs would be a staircase down to the lip and back.
            # The break stays uncrossed and unmarked, so a level whose course
            # comes back down to the terrace is still offered it.
            return None
        cone = self.cone
        radius = max(6.0, cone.rim_at(lv.y))
        for b0, b1 in cone.floor_breaks(lv):
            width = (b1 - b0) * radius
            if width < 4.5 or b0 in self._locked:
                continue
            dist = (b0 - self.u) * radius
            if not 0.5 < dist < 11.0:
                continue
            if limit is not None and dist + width + 3.0 >= limit:
                # The level's doorway comes first. Left un-marked on purpose:
                # the break is offered again once the course is through the
                # structure, and a level that loses its lock is a level a
                # walker gets down end to end.
                continue
            self._locked.add(b0)
            theme = lv.theme
            out = []
            # Approach legs: cover the ground to just before the lip in
            # ordinary hops, ending two blocks up so the island is a drop.
            run = max(0.0, dist - 1.3)
            legs = max(1, int(math.ceil(run / 4.2)))
            # At the height the body is running at, and one higher for the
            # last approach so the island is still a drop. Written as ``1``
            # and ``2`` this laid a staircase down to the terrace and back --
            # the lock was 19 of the landings a sweep that a fall could walk
            # onto, second only to the crossing's own.
            here = self._here_lift()
            for i in range(legs):
                out.append(self._node(
                    theme.rock, arc=max(2.6, run / legs),
                    lift=here + 1 if i == legs - 1 else here, spread=1,
                    label="lock"))
            out.append(self._node(
                theme.accent, arc=width / 2 + 1.4, lift=here,
                pedestal=False, spread=0, orbs=1, label="lock"))
            out.append(self._node(
                theme.rock, arc=width / 2 + 1.2, lift=here, spread=1,
                label="lock"))
            self.segment = "lock"
            return out
        return None

    def _feat_ascent(self, rng, lv, need: int) -> list[dict]:
        """The way out, as the level's design says rather than as dice say.

        Three tiers. A level with ``exit_beats`` wrote the way out landing by
        landing and gets exactly that, with the crossing appended. A level
        with only a *kind* gets the generated climb of that kind. Either way
        the whole reliability chain -- the re-aimed crossing, ``_climb_on``,
        ``_grab_the_wall`` -- sits underneath, because the climb out is the
        one move a run cannot do without.
        """
        # **A climb with nothing left to climb is just the crossing.** The
        # budget is the next level's floor minus wherever the body actually
        # got to, and a designed level that ends at lift 4, or comes off a
        # landing standing above its own terrace, arrives at the chasm already
        # at or above the height it was aiming for. Measured, ``need`` is zero
        # or negative on 13% of budget calls and 18.5% of level visits fire
        # **two** separate ascents -- the second climbing ground already won,
        # and the crossing then dropping the body back down. That is the
        # owner's "it climbs and then drops back to where it started, on a new
        # level", and two of the six agents rewriting levels reported it out of
        # their own frames before it was measured here.
        if need <= 0:
            return [self._crossing(rng, lv)]
        design = self.cone.design(lv.index)
        # **Off the apron first.** A level entered near its own end has no room
        # for the beats that would have climbed, so the exit is asked for with
        # the body still one block over the terrace -- and every landing of it
        # is then something a fall walks back onto. One ordinary +1 hop fixes
        # it, and it is the same hop the level's first beat would have made.
        lead = []
        if self._body_lift() < DECK_MIN:
            lead = [self._node(lv.theme.rock, arc=3.0, lift=DECK_MIN,
                               spread=0, ramp=False, label="ascent",
                               origin="deck")]
        if design.exit_beats:
            theme = THEME_BY_NAME[design.name]
            out = lead + [self._node(**{**_resolve(spec, theme),
                                        "label": "ascent",
                                        "origin": "design"})
                          for spec in design.exit_beats]
            out.append(self._crossing(rng, lv))
            return out
        kind = design.exit
        if kind != "stair" and need >= 3:
            built = self._ascent_climb(rng, lv, need, kind)
            if built:
                return lead + built
        return lead + self._ascent_stair(rng, lv, need)


def _resolve(spec: dict, theme: Theme) -> dict:
    """An authored node against the level it is in.

    Roles become the level's own materials; anything else is taken literally.
    ``ramp`` is off for everything here: a hand-built gap is the design, and
    stretching it by a quarter turns "the standard four-block jump" into a jump
    no body has.
    """
    out = dict(spec)
    style = out["style"]
    if style in ROLES:
        out["style"] = getattr(theme, style)
    out.setdefault("ramp", False)
    return out
