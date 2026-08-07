"""The overlay run loop.

Responsibilities, in priority order:

1. **Cost nothing when idle.** This process exists alongside whatever Claude is
   compiling. While hidden it renders nothing, holds no scene, and parks on a
   long sleep. A brainrot overlay that makes your builds slower has negative
   value.
2. **Generate fresh content on every show.** A new seed and a brand new scene
   are built each time the overlay comes up, so nothing is ever a rerun.
3. **Only be there while it is being watched.** Claude working is a necessary
   condition for the overlay, not a sufficient one: it also has to be a Claude
   Code window you are actually looking at (``follow_focus``). Otherwise the
   thing turns up over your browser, which is the one behaviour nobody wants.
4. Fade in and out rather than popping.
"""

from __future__ import annotations

import time

from ..config import Config
from ..ipc import Event, EventListener
from ..palette import generate as generate_palette
from ..rng import RunCounter, Seed
from ..state import ThinkingState, Visibility
from . import rl, scene as scene_api
from .hud import chip

#: How long to sleep per iteration while hidden. Long enough to be free, short
#: enough that the overlay still appears promptly once the grace period passes.
IDLE_SLEEP = 0.08

#: How long the foreground has to be somewhere else before that counts as the
#: user looking away. Windows that come and go in a few frames -- the alt-tab
#: switcher, a hook's console, a notification -- are not somebody leaving, and
#: without this every one of them takes a bite out of the fade. Only the
#: leaving edge waits; coming back is immediate, because that is the half you
#: can feel.
FOCUS_GRACE = 0.4


class Overlay:
    def __init__(self, cfg: Config, window, verbose: bool = False) -> None:
        self.cfg = cfg
        self.window = window
        self.verbose = verbose

        self.state = ThinkingState(
            grace_seconds=cfg.grace_seconds,
            min_visible_seconds=cfg.min_visible_seconds,
            hide_on_notification=cfg.hide_on_notification,
        )
        self.counter = RunCounter()
        self.listener = EventListener(cfg.host, cfg.port, self._on_event)

        self.scene: scene_api.Scene | None = None
        self.alpha = 0.0
        self.running = False
        self._window_shown = False
        self._focus_ok = True
        self._focus_left_at = 0.0

        from .input import Controller, Takeover

        self.controller = Controller(handback=cfg.handback_seconds)
        self.takeover = Takeover(window, cfg.hotkey)

    # -- events -----------------------------------------------------------

    def _on_event(self, event: Event) -> None:
        # Called from the listener thread. ThinkingState mutations are simple
        # set/scalar writes under the GIL and the render thread only ever reads
        # derived values, so no lock is warranted here.
        if self.verbose:
            print(f"[brainrot] {event.kind} session={event.session[:8]} tool={event.tool}")
        self.state.handle(event.kind, event.session, event.tool, event.hwnd)
        # A prompt submission tells us which window hosts Claude Code; layer
        # the overlay one level above it (no-op off Windows / when attached).
        if event.kind == "UserPromptSubmit" and event.hwnd:
            self.window.attach_host(event.hwnd)

    # -- scene lifecycle --------------------------------------------------

    def _begin_scene(self) -> None:
        """Build a fresh world. Called on every transition to visible."""
        if self.cfg.force_seed:
            seed = Seed.for_run(self.cfg.force_seed)
        else:
            seed = self.counter.next()

        palette = generate_palette(seed)
        name = self.cfg.force_scene or scene_api.choose(self.cfg.scenes, seed)
        ctx = scene_api.SceneContext(
            width=self.cfg.width,
            height=self.cfg.height,
            palette=palette,
            seed=seed,
            quality=self.cfg.quality,
        )
        self._end_scene()
        self.scene = scene_api.build(name, ctx)
        if self.verbose:
            print(
                f"[brainrot] run {seed.run}: {name} "
                f"({palette.time_of_day}/{palette.weather})"
            )

    def _end_scene(self) -> None:
        if self.scene is not None:
            try:
                self.scene.teardown()
            except Exception:
                pass
            self.scene = None

    # -- main loop --------------------------------------------------------

    def run(self) -> None:
        self.window.create(self.cfg)
        self.listener.start()
        self.running = True

        frame_budget = 1.0 / self.cfg.fps
        last = time.monotonic()

        try:
            while self.running:
                now = time.monotonic()
                dt = min(now - last, 0.1)  # clamp so a stall never teleports the world
                last = now

                if self.window.should_close() or rl.IsKeyPressed(rl.KEY_ESCAPE):
                    self.running = False

                visibility = self.state.tick()
                wants_visible = (
                    visibility in (Visibility.VISIBLE, Visibility.LINGERING)
                    and self._focus_allows()
                )

                if wants_visible and self.scene is None:
                    self._begin_scene()

                self._advance_fade(dt, wants_visible)

                if self.alpha <= 0.001 and not wants_visible:
                    self._go_idle()
                    time.sleep(IDLE_SLEEP)
                    continue

                # Before showing, not after: appearing in last turn's position
                # and then jumping is worse than a frame's delay. Cheap enough
                # to redo every frame, which is also how it keeps up with a
                # window being dragged around under it.
                self.window.follow_host()
                self._show_window()
                if self.scene is not None:
                    try:
                        self._drive(now)
                        self.scene.update(dt)
                        self.scene.elapsed += dt
                        self.window.begin()
                        self.scene.draw()
                        self._draw_caption()
                        self.window.end()
                    except Exception as exc:
                        # A bug in one generated world should cost that world,
                        # not the daemon. Drop it; the next show builds a fresh
                        # one from a new seed.
                        if self.verbose:
                            import traceback

                            traceback.print_exc()
                        else:
                            print(f"[brainrot] scene error, regenerating: {exc}")
                        self._end_scene()
                        continue

                self.window.set_opacity(self.alpha * self.cfg.opacity)

                # Sleep the remainder of the frame rather than spinning.
                spare = frame_budget - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
        finally:
            self.shutdown()

    def _focus_allows(self) -> bool:
        """Whether the window in front is one the overlay belongs over.

        Falls through the ordinary fade, so losing focus eases the strip out
        rather than blinking it away, and a bad answer from the window API
        fails open: a brainrot overlay that appears when it should not is a
        nuisance, one that can never appear again is broken.
        """
        if not self.cfg.follow_focus:
            return True
        try:
            here = bool(self.window.focus_allows(self.state.hosts))
        except Exception:
            return True

        now = time.monotonic()
        if here:
            self._focus_left_at = 0.0
            allowed = True
        else:
            if not self._focus_left_at:
                self._focus_left_at = now
            allowed = now - self._focus_left_at < FOCUS_GRACE

        if self.verbose and allowed != self._focus_ok:
            print(f"[brainrot] focus: {'on Claude Code' if allowed else 'elsewhere'}"
                  f" (hosts: {sorted(self.state.hosts)})")
        self._focus_ok = allowed
        return allowed

    def _drive(self, now: float) -> None:
        """Offer the keyboard to the scene, if anyone is asking for it."""
        scene = self.scene
        if scene is None or not scene.playable:
            return
        self.takeover.update()
        intent = self.controller.poll(now, self.takeover.focused())
        if self.controller.engaged:
            scene.control(intent)

    def _draw_caption(self) -> None:
        if self.cfg.show_caption and self.state.caption:
            chip(self.state.caption, 14, self.cfg.height - 30)
        note = self.controller.caption(time.monotonic())
        if note:
            chip(note, 14, self.cfg.height - 56)

    def _advance_fade(self, dt: float, wants_visible: bool) -> None:
        target = 1.0 if wants_visible else 0.0
        if self.cfg.fade_seconds <= 0:
            self.alpha = target
            return
        step = dt / self.cfg.fade_seconds
        if self.alpha < target:
            self.alpha = min(target, self.alpha + step)
        elif self.alpha > target:
            self.alpha = max(target, self.alpha - step)

    def _go_idle(self) -> None:
        """Drop to zero cost: hide the window and discard the world."""
        if self._window_shown:
            # Never hold the keyboard or the foreground across an idle spell:
            # the overlay is about to vanish, and a vanished window that still
            # owns focus is a window that has stolen it.
            if self.takeover.active:
                self.takeover.toggle()
            self.window.set_visible(False)
            # Let go of the host while we have nothing to show. On Windows the
            # overlay is an *owned* window, and Windows destroys owned windows
            # along with their owner -- so remaining attached while idle means
            # closing the terminal takes the daemon's window with it.
            self.window.detach_host()
            self._window_shown = False
        self._end_scene()
        # Even hidden, the window's event queue must be drained or the OS
        # flags the process unresponsive.
        self.window.pump()

    def _show_window(self) -> None:
        if not self._window_shown:
            self.window.set_visible(True)
            self._window_shown = True

    def shutdown(self) -> None:
        self.running = False
        self._end_scene()
        self.listener.stop()
        try:
            from .. import assets
            from . import textures, voxel

            assets.unload_all()
            # Voxel models reference cached textures, so both caches go
            # together or later loads would dangle.
            voxel.clear()
            textures.clear()
        except Exception:
            pass
        try:
            self.window.destroy()
        except Exception:
            pass
