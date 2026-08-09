"""Configuration loading.

Defaults are chosen to be immediately usable: a narrow strip on the left edge
of the primary monitor, translucent, click-through. Everything is overridable
from ``config.toml`` next to the state file, or via ``BRAINROT_*`` env vars.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from .rng import state_dir

DEFAULT_PORT = 47821


@dataclass
class Config:
    # --- IPC -------------------------------------------------------------
    port: int = DEFAULT_PORT
    host: str = "127.0.0.1"

    # --- Window ----------------------------------------------------------
    width: int = 360
    height: int = 640
    #: Which side of the Claude Code window to sit on, "right" or "left".
    #: The strip goes *beside* that window when the desktop has room and into
    #: that side's margin when it does not -- never onto the screen edge for
    #: its own sake, which is how it used to land on top of the sidebar.
    dock: str = "right"
    #: Gap from the docked edge, in pixels.
    margin_x: int = 12
    #: Gap from the top and bottom of the window it is following.
    margin_y: int = 20
    #: Vertical placement within that window, 0.0 = top, 1.0 = bottom.
    anchor_y: float = 0.0
    #: Which monitor to dock to (0 = primary).
    monitor: int = 0
    opacity: float = 0.88
    fps: int = 60
    #: Z-order mode (Windows): "host" layers the overlay one level above the
    #: window running Claude Code (discovered by the hook shim), so any other
    #: window you focus covers it. "topmost" floats above everything, always.
    attach: str = "host"
    #: Show only while a Claude Code window that is actually working is the
    #: window you are looking at. Z-order alone is not enough for that: it
    #: decides what covers what, not whether the overlay is on screen, so a
    #: window that happens not to overlap the strip leaves it visible over
    #: whatever you switched to. Off restores "visible whenever Claude is
    #: busy", which is what demos and screen recordings want.
    follow_focus: bool = True

    # --- Behaviour -------------------------------------------------------
    #: Ignore thinking bursts shorter than this, so quick turns do not strobe.
    grace_seconds: float = 1.5
    #: Once shown, stay up at least this long even if Claude finishes early.
    min_visible_seconds: float = 3.0
    fade_seconds: float = 0.35
    #: Hide when Claude asks for permission or input -- you need the terminal.
    hide_on_notification: bool = True
    #: Give up on a session that has said nothing for this long. The transport
    #: cannot promise the Stop arrives, and a session that never sends one --
    #: killed mid-answer, terminal closed, datagram dropped -- would otherwise
    #: keep the strip on screen for the life of the daemon. Generous, because
    #: a real turn can run for a long time. 0 disables it.
    max_thinking_seconds: float = 900.0
    #: Chord that hands the keyboard to the overlay, as "mod+mod+key".
    #:
    #: Deliberately obscure, and deliberately configurable. The overlay watches
    #: for this by polling rather than registering it, so it never takes a
    #: combination away from another program -- which cuts both ways: pick one
    #: something else already uses and *both* will fire. `brainrot hotkey`
    #: prints the setting for whatever you press, so you can find a free one
    #: rather than guess.
    hotkey: str = "ctrl+alt+shift+home"
    #: Seconds without input before a driven scene resumes driving itself.
    handback_seconds: float = 8.0
    #: Modifiers to hold to drag the strip somewhere else with the mouse.
    #: Modifiers only, and only these ones catch a click: the rest of the time
    #: the mouse falls straight through. Empty disables dragging entirely.
    #: Double-click while holding them to go back to automatic placement.
    drag_chord: str = "ctrl+alt"

    # --- Content ---------------------------------------------------------
    #: Scenes eligible to play. Order is irrelevant; selection is seeded.
    scenes: list[str] = field(default_factory=lambda: ["runner", "parkour"])
    #: Force one scene (debugging). Empty means "pick per run".
    force_scene: str = ""
    #: Replay a specific run number instead of advancing the counter.
    force_seed: int = 0
    show_caption: bool = True
    #: Visual quality: "high", "balanced" or "low". Trades detail against CPU.
    #: The overlay runs while Claude is working, so this is the knob to reach
    #: for if it ever competes with a build.
    quality: str = "high"

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        cfg = cls()
        path = path or (state_dir() / "config.toml")
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            raw = {}

        # Flatten one level of tables so [window] width = 400 works alongside a
        # bare top-level width = 400.
        flat: dict[str, object] = {}
        for key, value in raw.items():
            if isinstance(value, dict):
                flat.update(value)
            else:
                flat[key] = value

        known = {f.name: f for f in fields(cls)}
        for key, value in flat.items():
            if key in known:
                setattr(cfg, key, value)

        cfg._apply_env()
        cfg._validate()
        return cfg

    def _apply_env(self) -> None:
        for f in fields(self):
            env = os.environ.get(f"BRAINROT_{f.name.upper()}")
            if env is None:
                continue
            try:
                if f.type is int or f.name in ("port", "width", "height", "margin_x", "margin_y", "monitor", "fps", "force_seed"):
                    setattr(self, f.name, int(env))
                elif f.name in ("opacity", "anchor_y", "grace_seconds",
                                "min_visible_seconds", "fade_seconds",
                                "handback_seconds", "max_thinking_seconds"):
                    setattr(self, f.name, float(env))
                elif f.name in ("hide_on_notification", "show_caption", "follow_focus"):
                    setattr(self, f.name, env.strip().lower() in ("1", "true", "yes", "on"))
                elif f.name == "scenes":
                    setattr(self, f.name, [s.strip() for s in env.split(",") if s.strip()])
                else:
                    setattr(self, f.name, env)
            except ValueError:
                # A malformed override should not stop the overlay starting.
                continue

    def _validate(self) -> None:
        self.width = max(120, int(self.width))
        self.height = max(160, int(self.height))
        self.fps = max(10, min(120, int(self.fps)))
        self.opacity = max(0.15, min(1.0, float(self.opacity)))
        self.anchor_y = max(0.0, min(1.0, float(self.anchor_y)))
        self.grace_seconds = max(0.0, float(self.grace_seconds))
        self.min_visible_seconds = max(0.0, float(self.min_visible_seconds))
        self.fade_seconds = max(0.0, float(self.fade_seconds))
        self.handback_seconds = max(1.0, float(self.handback_seconds))
        self.max_thinking_seconds = max(0.0, float(self.max_thinking_seconds))
        # A hotkey that will not parse would silently mean "no takeover ever",
        # so fall back to the default rather than leaving it unusable.
        from .engine.keys import parse_chord, parse_modifiers

        if not parse_chord(self.hotkey):
            self.hotkey = Config.hotkey
        # "" is a deliberate "no dragging"; anything else that will not parse
        # is a typo, and silently disabling the gesture would be a mystery.
        if self.drag_chord and not parse_modifiers(self.drag_chord):
            self.drag_chord = Config.drag_chord
        if not self.scenes:
            self.scenes = ["runner"]
        if self.quality not in ("high", "balanced", "low"):
            self.quality = "high"
        if self.attach not in ("host", "topmost"):
            self.attach = "host"
        if self.dock not in ("left", "right"):
            self.dock = "right"
        self.margin_x = max(0, int(self.margin_x))
        self.margin_y = max(0, int(self.margin_y))
        self.follow_focus = bool(self.follow_focus)
