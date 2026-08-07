# Handoff: the overlay follows the wrong window

**Status: the overlay is disabled.** Hooks uninstalled, daemon stopped, no
window running — verified at commit `425aee7`. Nothing appears until someone
runs `brainrot install && brainrot run`. Leave it disabled until this is
fixed: appearing over a YouTube video is worse than not appearing at all.

Everything else in the project is healthy at this commit: **349 tests green**,
and the runner's collision guarantee still holds (zero interpenetration over
16 seeds × 150 s, re-checked here). The parkour content pass is finished and
its handoff retired. Nothing else is in flight — clean tree, no stashes. This
is the only outstanding defect.

## The complaint

> "the whole thing seems to be tied to my Google Chrome and not to the actual
> Claude Code desktop app. If I'm in the desktop app and start working on it, I
> don't see anything pop up, but if I switch to Chrome and watch YouTube,
> suddenly it'll pop up all over my screen. I want it only showing if I'm
> actively looking at what Claude Code is writing."

That last sentence is the requirement, and it is **stronger than what the code
was built to do**. The design layers the overlay one z-level above the Claude
Code window and lets any other window cover it. The ask is different: *hide it
entirely unless Claude Code is the window being looked at.*

## What is actually wrong

Measured on the live daemon before it was stopped:

```
overlay hwnd : 590800
owner        : NONE
TOPMOST      : False
```

Neither owned nor topmost — a plain window in ordinary z-order, which is how it
ends up over Chrome. Three faults, all still present and re-confirmed against
the source at this commit:

1. **The topmost fallback is backwards.** `overlay/win32.py:95` —
   `apply_overlay_styles` ends in `_order_topmost(hwnd)`, and only a
   `UserPromptSubmit` carrying a host handle ever moves it out of that band
   (`engine/loop.py:66`). So between daemon start and the next prompt it floats
   above *everything*. "Show over everything until we learn better" is exactly
   the wrong default; unknown should mean show over nothing.

2. **Attachment latches and never recovers.** `engine/window.py:183` —
   `_reattach()` returns early when `self._attached` is True; `detach_host()`
   at `:201` returns early when it is False. **Nothing anywhere calls
   `IsWindow` on `_host_hwnd`** (the only `IsWindow*` in that file is
   `IsWindowReady` in `HeadlessWindow`, unrelated). So when the owner window
   dies, `attach_to_host`'s earlier `SetWindowPos(HWND_NOTOPMOST)` has already
   dropped it out of the topmost band, the owner handle goes invalid, and it is
   stranded as the unowned non-topmost window measured above — permanently,
   with `_attached` still True.

3. **Nothing is keyed to focus at all.** `GetForegroundWindow` appears in only
   two places: the hook shim, which captures the host at event time
   (`hookinstall.py:66`), and the takeover, which restores focus afterwards
   (`engine/input.py:170`). Visibility never consults it. Ownership controls
   *stacking*, not whether the thing is on screen.

Multi-session wrinkle: hooks from *every* Claude Code session hit the same
daemon on port 47821, and `ThinkingState` refcounts them by session id. So
"is Claude Code focused" really means "is the foreground window the host of a
session that is currently thinking".

## The trap to avoid

Both scenes are now playable, and `Ctrl+Alt+Shift+Home` hands the overlay the
keyboard. Look at `engine/input.py:_grab` — taking control calls
`SetForegroundWindow(overlay_hwnd)`.

So a naive rule of "hide unless the host window is foreground" **hides the
overlay the instant you take control of it**, because the overlay itself is now
the foreground window and the host is not. The condition has to be:

> show while (a thinking session's host is foreground) **or** (the takeover is
> active and the overlay itself has focus)

Getting this wrong is not subtle — the strip vanishes the moment you press the
chord — but it is very easy to miss when writing the focus check on its own.

## What to build

- Each frame, take `GetForegroundWindow()` and its `GA_ROOT`, compare against
  the known host handle(s). Not the host (and not the takeover case above) →
  do not show. Route it through the existing fade so it eases out rather than
  popping, like `hide_on_notification` does.
- **Unknown host means hidden**, not topmost. Remove the topmost fallback, or
  put it behind a config flag that defaults off.
- Validate the host with `IsWindow` every frame; when it dies, clear
  `_host_hwnd` and `_attached` and go back to hidden. Fix the latching guards
  while you are in there.
- Track the host **per session id** — `Event.session` already carries it, and
  more than one session running at once is normal on this machine.
- Landmine, already documented in `CLAUDE.md`: an owned window is destroyed
  along with its owner, which is why the daemon detaches when it goes idle.
  Do not "simplify" that away.

Config worth adding: `follow_focus = true` for the new behaviour, so the
always-visible mode stays reachable for demos and for `brainrot demo`.

## How to verify it

Do not ship this on reasoning alone. Every window bug on this project so far
looked correct when read and only failed when measured — the upside-down
captures, the off-thread GLFW deadlock, the contradictory z-order calls, and
this one. `tests/test_overlay_win32.py` already drives the real Win32 API and
is the right home. Cases:

- Host exists but is not foreground → hidden.
- Host is foreground → shown.
- Host destroyed while shown → hidden, `_host_hwnd`/`_attached` cleared, and
  no leftover unowned non-topmost window.
- No host known → hidden, and *not* topmost.
- Takeover active → shown, even though the host is not foreground.

A dozen lines reading `GWL_EXSTYLE` and `GWLP_HWNDPARENT` off the live window
told us more than reading the source did; write that as a test rather than a
scratch script this time.

Then a manual pass, which is the only thing that actually answers the
complaint: `brainrot install && brainrot run`, submit a prompt in Claude Code,
switch to Chrome — it should disappear. Switch back — it should return. Leave
it installed and running afterwards if it behaves.

---

## Prompt to paste

> Read `docs/HANDOFF-overlay-focus.md` in claude-brainrot and fix what it
> describes.
>
> Short version: the overlay is supposed to appear only while I'm actually
> looking at Claude Code, but it shows up over Chrome while I'm watching
> YouTube and stays hidden while I'm using Claude Code. It is currently
> disabled (hooks uninstalled, daemon stopped) — keep it disabled until the fix
> is verified, then re-enable it with `brainrot install && brainrot run` and
> check it by hand: submit a prompt, switch to Chrome, it should vanish; switch
> back, it should return. Leave it running if it behaves.
>
> The handoff names the three faults with file and line, and one trap that will
> bite you if you write the obvious focus check (taking keyboard control makes
> the overlay itself the foreground window, so "hide unless the host is
> foreground" would hide it the moment I press the takeover chord).
>
> Verify against the real Win32 API in `tests/test_overlay_win32.py` rather
> than reasoning about the source — every window bug on this project so far
> looked correct when read and only failed when measured. Keep the 349 tests
> green.
