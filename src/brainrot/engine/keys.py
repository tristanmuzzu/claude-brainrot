"""Chord parsing: ``"ctrl+alt+shift+home"`` to a set of virtual-key codes.

Separate from :mod:`brainrot.engine.input` so the config can validate a chord
without importing raylib, and so the table of names is one thing rather than
scattered through the takeover code.

Virtual-key codes rather than raylib key constants because the chord is
watched with ``GetAsyncKeyState`` -- before the overlay has focus, raylib
cannot see anything at all, which is the whole problem the chord solves.
"""

from __future__ import annotations

#: Modifier names to VK codes. The plain (non-sided) codes match either side.
MODIFIERS = {
    "ctrl": 0x11,       # VK_CONTROL
    "control": 0x11,
    "alt": 0x12,        # VK_MENU
    "shift": 0x10,      # VK_SHIFT
    "win": 0x5B,        # VK_LWIN
    "super": 0x5B,
    "meta": 0x5B,
}

#: Named non-character keys. Anything not here falls through to the
#: single-character rule below.
NAMED = {
    "home": 0x24, "end": 0x23, "insert": 0x2D, "delete": 0x2E,
    "pageup": 0x21, "pagedown": 0x22,
    "pause": 0x13, "break": 0x13, "scrolllock": 0x91, "capslock": 0x14,
    "space": 0x20, "tab": 0x09, "enter": 0x0D, "return": 0x0D,
    "backspace": 0x08, "escape": 0x1B, "esc": 0x1B,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "numlock": 0x90, "apps": 0x5D, "menu": 0x5D,
    "backtick": 0xC0, "grave": 0xC0,
    "minus": 0xBD, "equals": 0xBB,
    "leftbracket": 0xDB, "rightbracket": 0xDD, "backslash": 0xDC,
    "semicolon": 0xBA, "quote": 0xDE,
    "comma": 0xBC, "period": 0xBE, "slash": 0xBF,
}
#: F1 through F24. F13+ exist as codes but not on most keyboards, which makes
#: them excellent chords for anyone who has a keyboard with them and useless
#: for everyone else.
NAMED.update({f"f{i}": 0x6F + i for i in range(1, 25)})

#: Reverse lookup, for turning what someone pressed back into a config string.
_VK_NAMES = {vk: name for name, vk in NAMED.items()}
_VK_NAMES.update({0x11: "ctrl", 0x12: "alt", 0x10: "shift", 0x5B: "win"})


def parse_chord(spec: str) -> frozenset[int]:
    """``"ctrl+alt+shift+home"`` -> the VK codes that must all be held.

    Returns an empty set when the chord is unusable, which callers treat as
    "no chord configured" rather than crashing the overlay over a typo in a
    config file.
    """
    if not isinstance(spec, str):
        return frozenset()
    codes: set[int] = set()
    parts = [p.strip().lower().replace(" ", "") for p in spec.split("+")]
    parts = [p for p in parts if p]
    if not parts:
        return frozenset()
    for part in parts:
        if part in MODIFIERS:
            codes.add(MODIFIERS[part])
        elif part in NAMED:
            codes.add(NAMED[part])
        elif len(part) == 1 and (part.isalpha() or part.isdigit()):
            codes.add(ord(part.upper()))
        else:
            return frozenset()
    # A chord of modifiers alone would fire constantly while someone typed.
    if all(code in MODIFIERS.values() for code in codes):
        return frozenset()
    return frozenset(codes)


def describe(codes: "set[int] | frozenset[int]") -> str:
    """VK codes back to a config string, modifiers first and in a fixed order."""
    order = [0x11, 0x12, 0x10, 0x5B]
    mods = [_VK_NAMES[c] for c in order if c in codes]
    rest = sorted(c for c in codes if c not in order)
    names = []
    for code in rest:
        if code in _VK_NAMES:
            names.append(_VK_NAMES[code])
        elif 0x30 <= code <= 0x5A:
            names.append(chr(code).lower())
        else:
            names.append(f"vk{code:02x}")
    return "+".join(mods + names)
