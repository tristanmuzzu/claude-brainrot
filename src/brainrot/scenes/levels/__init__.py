"""The thirty-three designed levels, in the order they are climbed.

One module per level, so that a level can be rewritten without touching any
other. ``_base`` holds the shared vocabulary (``Level``, ``n``, ``ROLES``);
``docs/RULES.md`` holds the rules a level must satisfy.
"""

from __future__ import annotations

from ._base import ROLES, Level, n
from .l01_gatehouse import LEVEL as _l01
from .l02_windmill_reach import LEVEL as _l02
from .l03_market_street import LEVEL as _l03
from .l04_timberworks import LEVEL as _l04
from .l05_sunken_temple import LEVEL as _l05
from .l06_balconies import LEVEL as _l06
from .l07_canopy_walk import LEVEL as _l07
from .l08_cistern import LEVEL as _l08
from .l09_glacier_shelf import LEVEL as _l09
from .l10_apiary import LEVEL as _l10
from .l11_crucible import LEVEL as _l11
from .l12_reef_garden import LEVEL as _l12
from .l13_silence import LEVEL as _l13
from .l14_belfry import LEVEL as _l14
from .l15_woolworks import LEVEL as _l15
from .l16_vault import LEVEL as _l16
from .l17_weir import LEVEL as _l17
from .l18_blue_run import LEVEL as _l18
from .l19_quarry import LEVEL as _l19
from .l20_rope_bridge import LEVEL as _l20
from .l21_basalt_flues import LEVEL as _l21
from .l22_pillars import LEVEL as _l22
from .l23_spore_hollow import LEVEL as _l23
from .l24_archive import LEVEL as _l24
from .l25_pumpkin_rows import LEVEL as _l25
from .l26_grove import LEVEL as _l26
from .l27_dust_devils import LEVEL as _l27
from .l28_sea_gate import LEVEL as _l28
from .l29_cornice import LEVEL as _l29
from .l30_wart_fields import LEVEL as _l30
from .l31_echo_shaft import LEVEL as _l31
from .l32_white_stair import LEVEL as _l32
from .l33_gate import LEVEL as _l33

#: The roster. Order is the order of the climb, and it loops: level 33's exit
#: lands on level 1. Adjacent levels may not share a theme, and any three
#: consecutive ``rise`` values are the head-room over the lowest of them --
#: which is why ``rise`` is not a per-level decision.
LEVELS: tuple[Level, ...] = (
    _l01,  # THE GATEHOUSE
    _l02,  # WINDMILL REACH
    _l03,  # MARKET STREET
    _l04,  # THE TIMBERWORKS
    _l05,  # SUNKEN TEMPLE
    _l06,  # THE BALCONIES
    _l07,  # CANOPY WALK
    _l08,  # THE CISTERN
    _l09,  # GLACIER SHELF
    _l10,  # THE APIARY
    _l11,  # THE CRUCIBLE
    _l12,  # REEF GARDEN
    _l13,  # THE SILENCE
    _l14,  # THE BELFRY
    _l15,  # WOOLWORKS
    _l16,  # THE VAULT
    _l17,  # THE WEIR
    _l18,  # BLUE RUN
    _l19,  # THE QUARRY
    _l20,  # ROPE BRIDGE
    _l21,  # BASALT FLUES
    _l22,  # THE PILLARS
    _l23,  # SPORE HOLLOW
    _l24,  # THE ARCHIVE
    _l25,  # PUMPKIN ROWS
    _l26,  # THE GROVE
    _l27,  # DUST DEVILS
    _l28,  # THE SEA GATE
    _l29,  # THE CORNICE
    _l30,  # WART FIELDS
    _l31,  # ECHO SHAFT
    _l32,  # THE WHITE STAIR
    _l33,  # THE GATE
)

__all__ = ["LEVELS", "ROLES", "Level", "n"]
