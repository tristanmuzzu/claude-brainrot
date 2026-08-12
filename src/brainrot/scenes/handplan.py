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

from . import spiralplan as sp
from .handlevels import LEVELS, ROLES, Level, n  # noqa: F401
from .spiralplan import (  # noqa: F401  -- the renderer reads these off the plan
    HANGING,
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
        "step": base.step,
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
        #: Beats asked for, and beats that came out with every landing placed
        #: as authored. The fidelity numbers; see ``tools/tower_probe.py``.
        self.authored = 0
        self.as_designed = 0
        super().__init__(rng, cone, hop_rng)

    ahead = AHEAD

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

    def _choose_feature(self, lv) -> list[dict]:
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
        self.authored += len(specs)
        return [self._node(**_resolve(spec, lv.theme)) for spec in specs]

    def _feat_ascent(self, rng, lv, need: int) -> list[dict]:
        """The way out, as the level's design says rather than as dice say.

        Three tiers. A level with ``exit_beats`` wrote the way out landing by
        landing and gets exactly that, with the crossing appended. A level
        with only a *kind* gets the generated climb of that kind. Either way
        the whole reliability chain -- the re-aimed crossing, ``_climb_on``,
        ``_grab_the_wall`` -- sits underneath, because the climb out is the
        one move a run cannot do without.
        """
        design = self.cone.design(lv.index)
        if design.exit_beats:
            theme = THEME_BY_NAME[design.name]
            out = [self._node(**{**_resolve(spec, theme), "label": "ascent"})
                   for spec in design.exit_beats]
            out.append(self._crossing(rng, lv))
            return out
        kind = design.exit
        if kind != "stair" and need >= 3:
            built = self._ascent_climb(rng, lv, need, kind)
            if built:
                return built
        return self._ascent_stair(rng, lv, need)


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
