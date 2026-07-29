"""The overlay run loop.

Responsibilities, in priority order:

1. **Cost nothing when idle.** This process exists alongside whatever Claude is
   compiling. While hidden it renders nothing, holds no scene, and parks on a
   long sleep. A brainrot overlay that makes your builds slower has negative
   value.
2. **Generate fresh content on every show.** A new seed and a brand new scene
   are built each time the overlay comes up, so nothing is ever a rerun.
3. Fade in and out rather than popping.
"""

from __future__ import annotations

import time

import pygame

from ..config import Config
from ..engine import scene as scene_api
from ..engine.draw import reset_caches, text
from ..ipc import Event, EventListener
from ..palette import generate as generate_palette
from ..rng import RunCounter, Seed
from ..state import ThinkingState, Visibility

#: How long to sleep per iteration while hidden. Long enough to be free, short
#: enough that the overlay still appears promptly once the grace period passes.
IDLE_SLEEP = 0.08


class Overlay:
    def __init__(self, cfg: Config, backend, verbose: bool = False) -> None:
        self.cfg = cfg
        self.backend = backend
        self.verbose = verbose

        self.state = ThinkingState(
            grace_seconds=cfg.grace_seconds,
            min_visible_seconds=cfg.min_visible_seconds,
            hide_on_notification=cfg.hide_on_notification,
        )
        self.counter = RunCounter()
        self.listener = EventListener(cfg.host, cfg.port, self._on_event)

        self.surface: pygame.Surface | None = None
        self.scene: scene_api.Scene | None = None
        self.alpha = 0.0
        self.running = False
        self._window_shown = False

    # -- events -----------------------------------------------------------

    def _on_event(self, event: Event) -> None:
        # Called from the listener thread. ThinkingState mutations are simple
        # set/scalar writes under the GIL and the render thread only ever reads
        # derived values, so no lock is warranted here.
        if self.verbose:
            print(f"[brainrot] {event.kind} session={event.session[:8]} tool={event.tool}")
        self.state.handle(event.kind, event.session, event.tool)

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
        pygame.init()
        reset_caches()
        self.surface = self.backend.create(self.cfg)
        self.listener.start()
        self.running = True

        frame_budget = 1.0 / self.cfg.fps
        last = time.monotonic()

        try:
            while self.running:
                now = time.monotonic()
                dt = min(now - last, 0.1)  # clamp so a stall never teleports the world
                last = now

                self._pump_events()
                visibility = self.state.tick()
                wants_visible = visibility in (Visibility.VISIBLE, Visibility.LINGERING)

                if wants_visible and self.scene is None:
                    self._begin_scene()

                self._advance_fade(dt, wants_visible)

                if self.alpha <= 0.001 and not wants_visible:
                    self._go_idle()
                    time.sleep(IDLE_SLEEP)
                    continue

                self._show_window()
                if self.scene is not None:
                    try:
                        self.scene.update(dt)
                        self.scene.elapsed += dt
                        self._render()
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

                self.backend.set_opacity(self.alpha * self.cfg.opacity)
                self.backend.present()

                # Sleep the remainder of the frame rather than spinning.
                spare = frame_budget - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
        finally:
            self.shutdown()

    def _pump_events(self) -> None:
        # Draining the event queue is not optional even for a click-through
        # window: an SDL window that never pumps is flagged unresponsive by the
        # OS and can be dimmed or killed.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

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
            self.backend.set_visible(False)
            self._window_shown = False
        self._end_scene()

    def _show_window(self) -> None:
        if not self._window_shown:
            self.backend.set_visible(True)
            self._window_shown = True

    def _render(self) -> None:
        assert self.surface is not None and self.scene is not None
        self.scene.draw(self.surface)
        if self.cfg.show_caption and self.state.caption:
            text(
                self.surface,
                self.state.caption,
                self.cfg.width // 2,
                self.cfg.height - 14,
                size=13,
                color=self.scene.palette.ink,
                anchor="midbottom",
            )

    def shutdown(self) -> None:
        self.running = False
        self._end_scene()
        self.listener.stop()
        try:
            self.backend.destroy()
        except Exception:
            pass
        # Caches hold Fonts and Surfaces bound to the SDL instance we are about
        # to tear down; leaving them would poison a subsequent daemon.
        reset_caches()
        pygame.quit()
