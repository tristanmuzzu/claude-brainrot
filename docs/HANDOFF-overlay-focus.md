# Handoff: the overlay follows the wrong window

**Status: the overlay is currently disabled.** Hooks uninstalled, daemon
stopped. Nothing will appear until someone runs `brainrot install && brainrot
run` again. Do not re-enable it until this is fixed — appearing over a YouTube
video is worse than not appearing at all.

## The complaint

> "the whole thing seems to be tied to my Google Chrome and not to the actual
> Claude Code desktop app. If I'm in the desktop app and start working on it, I
> don't see anything pop up, but if I switch to Chrome and watch YouTube,
> suddenly it'll pop up all over my screen. I want it only showing if I'm
> actively looking at what Claude Code is writing."

That last sentence is the requirement, and it is **stronger than what the code
was built to do**. The design layers the overlay one z-level above the Claude
Code window and lets any other window cover it. The ask is different: *hide it
entirely unless Claude Code is the focused window.*

## What is actually wrong

Measured on the live daemon before it was stopped:

```
overlay hwnd : 590800
owner        : NONE
TOPMOST      : False
```

Neither owned nor topmost — a plain window in ordinary z-order, which is
exactly how it ends up sitting above Chrome. Three separate faults get it
there:

1. **The topmost fallback is backwards.** `apply_overlay_styles` starts the
   window `HWND_TOPMOST` and stays there until a `UserPromptSubmit` arrives
   carrying a host handle (`loop._on_event` only calls `attach_host` for that
   one event). So for the whole window between daemon start and the next
   prompt, it floats above *everything*. "Show over everything until we learn
   better" is precisely the wrong default; it should show over nothing.

2. **Attachment latches and never recovers.** `OverlayWindow._reattach()`
   returns early when `self._attached` is True, and `detach_host()` returns
   early when it is False. Nothing ever checks `IsWindow(self._host_hwnd)`. So
   when the owner window goes away, `attach_to_host`'s earlier
   `SetWindowPos(HWND_NOTOPMOST)` has already dropped it out of the topmost
   band, the owner becomes invalid, and it is left as the unowned non-topmost
   window measured above — permanently, with `_attached` still True.

3. **Nothing is keyed to focus at all.** Even with ownership working
   perfectly, ownership only controls *stacking*. Tristan runs several Claude
   Code sessions; the overlay follows whichever one submitted a prompt most
   recently, and stays on screen while he is reading something else entirely.

There is also a multi-session wrinkle: hooks from *every* Claude Code session
hit the same daemon on port 47821, and `ThinkingState` refcounts them by
session id. So "is Claude Code focused" really means "is the foreground window
the host of a session that is currently thinking".

## What to build

Make visibility conditional on focus, not just stacking.

- Each frame, take `GetForegroundWindow()` and its `GA_ROOT`, and compare
  against the known host handle(s). Not the host → do not show. Treat it like
  the existing `hide_on_notification` path so it fades rather than pops.
- **Unknown host means hidden**, not topmost. Delete the topmost fallback, or
  put it behind a config flag that defaults off.
- Validate the host every frame with `IsWindow`; when it dies, clear
  `_host_hwnd` / `_attached` and go back to hidden.
- Track the host **per session id** (`Event.session` already carries it), since
  more than one session is normal here. Show while any *thinking* session's
  host is foreground.
- Keep the existing landmine in mind: an owned window is destroyed with its
  owner, which is why the daemon detaches when idle. See `CLAUDE.md`.

Config worth adding: `follow_focus = true` (the new behaviour) so the old
always-visible mode is still reachable for demos.

## How to verify it

Do not ship this on reasoning alone — the last round of window bugs all looked
correct in the source. `tests/test_overlay_win32.py` runs against the real
Win32 API and is the right place. Suggested cases:

- Host window exists but is not foreground → overlay hidden.
- Host foreground → overlay shown.
- Host destroyed while shown → overlay hidden, state cleared, no leftover
  non-topmost unowned window.
- No host known → hidden, and *not* topmost.

Then a manual pass: start the daemon, submit a prompt in Claude Code, switch to
Chrome, confirm it disappears; switch back, confirm it returns.

`scratchpad` scripts used for the diagnosis above are worth recreating — a
dozen lines reading `GWL_EXSTYLE` and `GWLP_HWNDPARENT` off the live window
told us more than reading the source did.

## Do not disturb

Another session is doing the parkour content pass (see
`docs/HANDOFF-parkour.md`) and is editing `scenes/parkour.py` and friends. This
work is confined to `engine/loop.py`, `engine/window.py`, `overlay/win32.py`
and `config.py`, which should not collide — but that session's tooling has been
seen running `git stash` across the whole tree, so commit early and check
`git stash list` if edits vanish.

---

## Prompt to paste

> Read `docs/HANDOFF-overlay-focus.md` in claude-brainrot and fix what it
> describes. Short version: the overlay is supposed to appear only while I'm
> actually looking at Claude Code, but it shows up over Chrome while I'm
> watching YouTube. It's currently disabled (hooks uninstalled, daemon
> stopped) — leave it disabled until the fix is verified, then re-enable with
> `brainrot install && brainrot run` and check it by hand: submit a prompt,
> switch to Chrome, it should vanish; switch back, it should return.
>
> Verify against the real Win32 API in `tests/test_overlay_win32.py` rather
> than reasoning about the source — every window bug on this project so far
> looked correct when read.
