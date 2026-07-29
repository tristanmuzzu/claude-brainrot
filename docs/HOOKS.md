# Hooks

## What gets installed

`brainrot install` does two things:

1. Writes a shim to `brainrot_hook.py` in the state directory.
2. Merges hook entries into `~/.claude/settings.json` (or the project's
   `.claude/settings.json` with `--scope project`).

The resulting entry looks like:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\Python311\\pythonw.exe\" -S \"C:\\Users\\you\\AppData\\Roaming\\claude-brainrot\\brainrot_hook.py\""
          }
        ]
      }
    ]
  }
}
```

## Events used

| Event | Frequency | Purpose |
|---|---|---|
| `UserPromptSubmit` | once per turn | start the thinking window |
| `Stop` | once per turn | end it |
| `Notification` | when Claude needs you | hide — your attention belongs on the terminal |
| `SessionEnd` | once per session | release that session's refcount |
| `PreToolUse` / `PostToolUse` | **every tool call** | opt-in, `--with-tool-events`, live tool captions only |

The default four are all low-frequency. The tool events are deliberately
opt-in: they fire constantly, and the overlay needs nothing from them that the
others do not already provide.

## Why one shim covers every event

The hook payload arrives on stdin as JSON and already contains
`hook_event_name`, so the shim reads its own event kind from the payload. There
is nothing to parameterise, which means one file, one install path, and no way
for the registered command and the event to drift apart.

It also forwards `session_id` (for refcounting across concurrent Claude Code
windows) and `tool_name` (for captions).

## The three properties the shim must have

**It must not block.** One UDP datagram, no connect, no response read. If the
daemon is down, stopped, or wedged, the kernel drops the packet and Claude Code
carries on. Anything connection-oriented could stall your session.

**It must not fail.** The entire body is wrapped in a bare `except`. A
traceback from a toy overlay has no business appearing in a real session.

**It must start fast.** `python -S` skips `site` — most of a cold interpreter's
startup — and the script imports only builtins. On Windows it runs under
`pythonw.exe`; plain `python.exe` would pop a console window on every prompt
and every response.

Roughly 30ms per fire, twice per turn.

## Install and uninstall are safe to repeat

Our entries are identified by the `brainrot_hook.py` filename in the command
string. Install removes any previous entry of ours before adding the current
one, so re-running never stacks duplicates. Uninstall removes only entries
carrying that marker and leaves every other hook — and every other settings key
— untouched.

`settings.json` is written write-then-replace, so an interrupted install cannot
leave you with a truncated file and a broken Claude Code.

## Checking it works

Drive the daemon by hand, with `brainrot run -v` in another terminal:

```bash
brainrot ping UserPromptSubmit
# ...wait more than grace_seconds, the strip should appear
brainrot ping Stop
```

To verify the real shim end to end:

```bash
echo '{"hook_event_name":"UserPromptSubmit","session_id":"test"}' \
  | python -S ~/.local/state/claude-brainrot/brainrot_hook.py
```

`brainrot run -v` prints every event it receives.

## Troubleshooting

**Nothing appears.** Check the daemon is running and that hooks are registered
(`brainrot install` is separate from `brainrot run`). Confirm the port matches
if you changed it — the shim has the port baked in at install time, so changing
`port` in config means re-running `brainrot install`.

**A console window flashes on Windows.** The installer could not find
`pythonw.exe` next to your interpreter and fell back to `python.exe`. Install
Python from python.org rather than the Store build, or edit the command in
`settings.json` to point at `pythonw.exe`.

**It appears but never goes away.** Something is sending start events without
matching `Stop` events. `brainrot run -v` will show it.

**It steals focus or eats clicks.** You are not on the win32 backend — check
`pywin32` is installed. `brainrot run` prints which backend it selected.
