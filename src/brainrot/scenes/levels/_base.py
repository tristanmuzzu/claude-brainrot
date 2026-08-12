"""The vocabulary a designed level is written in.

``docs/TOWER.md`` is the intent, ``brainrot.scenes.levels`` is that intent as
data -- one module per level -- and ``brainrot.scenes.handplan`` is the
machinery that places it. Every number in a level module was chosen against
the physics table in the doc: one jump impulse, one speed. Run
`tools/tower_probe.py --design-only` after touching any of them; it checks
the whole roster on paper in under a second.

The vocabulary, briefly. ``arc`` is metres along the corridor, ``lift`` is
height above the level's floor, ``radial`` weaves across the corridor,
``hug`` is distance out from the core wall (big = out at the rim over the
drop), ``ceiling`` is a checked lid, ``moat`` digs liquid under the jump,
``shell`` builds an interior (tunnel/hall/cave/shaft) around the move,
``step_y`` is a signed absolute rise for climbs and rim-descents,
``pedestal=False`` floats the landing. Rules that bind every line:

* consecutive hops may rise at most one block, and a rising hop's arc stays
  at or under 3.6 (a +1 jump reaches 3.10 stand-point to stand-point);
* a flat hop's arc stays under 4.9; only a *descending* jump may ask more;
* levels rise 4-8 to the next, and any three consecutive rises sum to 13-20
  because three rises are literally the head-room over the lowest of them;
* ledge is the default ground -- the plaza died with the first tower -- and
  a level that wants the full floor says ``plaza`` and dresses it.
"""

from __future__ import annotations

#: Material roles a level may name instead of a material. Writing ``"rock"``
#: rather than ``"cobble"`` is what lets one design be re-skinned by giving
#: its level a different theme, and what keeps a level readable as a *shape*.
ROLES = frozenset(("ground", "sub", "rock", "accent", "glow", "liquid"))


def n(style: str = "rock", **kw) -> dict:
    """One authored landing: a role or material, and the node's own arguments.

    Thin on purpose. The keywords are ``Course._node``'s own, so the design
    below is written in the same vocabulary the generator's features were and
    anything expressible there is expressible here.
    """
    return {"style": style, **kw}


class Level:
    """One designed level: a place, a shape, and the way out of it.

    ``beats`` is the level in order. Each beat is ``(name, [node, ...])`` and
    is laid whole or not at all. ``filler`` repeats if the terrace outlasts
    the script -- put the level's *character* there, not its surprise.
    ``rise`` is how far above this level the next one sits. ``gap`` is the
    chasm at the end, in blocks. ``exit`` is a kind (stair/ladder/vine/
    bubble); ``exit_beats`` optionally writes the way out landing by landing,
    with the generated climb still underneath as the fallback. ``profile``,
    ``shelf`` and ``landmark`` are the ground and the one structure the level
    is recognised by. ``skin`` re-skins the base theme.
    """

    __slots__ = ("band", "beats", "breaks", "exit", "exit_beats", "filler",
                 "gap", "landmark", "name", "profile", "rise", "shelf",
                 "skin", "theme")

    def __init__(self, name: str, theme: str, rise: int, gap: float,
                 exit: str, beats, filler=(), profile: str = "ledge",
                 shelf: float = 4.0, landmark: str = "",
                 exit_beats=(), breaks: int | None = None,
                 band: float = 9.5, **skin) -> None:
        self.name = name
        self.theme = theme
        self.rise = rise
        self.gap = gap
        self.exit = exit
        self.beats = tuple(beats)
        self.filler = tuple(filler) or self.beats[-2:]
        self.profile = profile
        self.shelf = shelf
        self.landmark = landmark
        self.exit_beats = tuple(exit_beats)
        #: In-level floor gaps -- the islands-not-a-ribbon rule. Measured on
        #: the real map: no checkpoint leg is walkable end to end and a
        #: no-jump walker covers 46% on average. Three breaks for a ledge,
        #: two for a full floor, unless the level says otherwise.
        self.breaks = breaks if breaks is not None else \
            (3 if profile == "ledge" else 2)
        #: The corridor's width for this level, core face to rim: a tight
        #: gallery at 7.5 and a broad court at 13 are different places
        #: before a single block is laid. Capped by ``BAND_MAX``.
        self.band = band
        self.skin = skin


# ---------------------------------------------------------------------------
# The tower: thirty-three levels, eleven revolutions, and the cycle loops.
# Consecutive levels differ on at least three of band, enclosure, form, verb,
# constraint, rhythm and light; interiors never come twice in a row; each
# third of the tower gets at least three interiors and a vertical level.
# ---------------------------------------------------------------------------

