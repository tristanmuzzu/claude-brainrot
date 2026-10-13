# Local installation

This guide is for a user or agent setting up Brainrot on a new computer.
Use the current source for Codex support; PyPI 0.3.0 predates it.

## 1. Check the computer

- Python 3.11 or newer. On Windows, use python.org Python, not Store Python.
- A graphical desktop and a working OpenGL renderer.
- Windows 10/11 or Linux. GNOME/Wayland needs XWayland for the overlay.
- Identify the target agent: Claude Code, local Codex, or local ChatGPT Work.
- If Brainrot is installed, run `brainrot doctor` and reuse its environment.
  Do not start a second daemon or overwrite another install's configuration.

## 2. Install source and try a scene

```bash
git clone https://github.com/tristanmuzzu/claude-brainrot.git
cd claude-brainrot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
brainrot demo --scene runner --seed 4712
```

On Windows, use `py -m venv .venv` and
`.\.venv\Scripts\Activate.ps1` instead of the Linux environment commands.
The demo should show moving trains and a runner. Close it before proceeding.
If it fails, fix that first; installing hooks cannot fix a renderer failure.

## 3. Register the chosen integration

Back up the relevant hook file if it already exists. The installer preserves
foreign hooks and refuses malformed JSON.

```bash
brainrot install --agent claude
```

Choose `--agent codex` for Codex or `--agent chatgpt` for local ChatGPT Work.
Claude uses `~/.claude/settings.json`; Codex uses `$CODEX_HOME/hooks.json`
(default `~/.codex/hooks.json`). `--scope project` targets the current
repository instead. Keep the interpreter in place: hooks use its absolute path.

On Linux the command also installs the GNOME extension. Use `--no-extension`
for another desktop or if you want fallback docking. On GNOME, load the
extension with `brainrot extension load`, or log out and back in. Do not
promise full focus tracking until the extension is loaded.

Restart your coding agent after registering hooks. In Codex, review and trust
the hooks through hook settings or `/hooks`, and enable `features.hooks` if
it is disabled. Project hooks also require a trusted project. `doctor` checks
registration, but cannot prove runtime trust.

## 4. Verify the whole path

```bash
brainrot doctor --agent claude
brainrot run
```

Use the same agent flag as installation. Keep the daemon open. In a second
terminal, send it a prompt lifecycle:

```bash
brainrot ping UserPromptSubmit
# Wait for the strip to appear.
brainrot ping Stop
```

Then run a real turn in the chosen agent. Confirm the strip appears after the
grace period and fades when the turn ends. With full focus tracking, switch
away and back to check hide/show behavior. Codex automatic approval review
keeps the strip playing; it is not evidence the agent needs a human answer.

Record which checks passed and which need user login, hook trust or another
platform. A passing rendering test alone does not prove window integration.

## Removal

```bash
brainrot uninstall --agent claude
brainrot uninstall --agent codex
brainrot extension remove   # GNOME, if no longer wanted
```

Remove only the integrations you installed. Stop this daemon with Ctrl+C.
Uninstall the Python tool using the package manager used for installation.
Do not delete another app's hooks or start a background service without the
user requesting one.
