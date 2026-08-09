"""Installing the gnome-shell extension.

Everything the overlay needs that Wayland will not give a client comes from
:mod:`brainrot.overlay.shell`'s other half, a small extension that lives in
gnome-shell. This module puts it in place: copy, compile its schema, tell it
which port the daemon is on, enable it.

Deliberately *optional*. The overlay runs without it -- docked to the work
area, up for the whole turn rather than only while you are looking at Claude
Code -- because "install a shell extension before you can see anything" is a
bad first five minutes. ``brainrot doctor`` says which of the two you are on.

Nothing here needs root, and nothing here touches a file outside the user's
own ``~/.local/share/gnome-shell/extensions``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .config import Config

UUID = "brainrot@claude-brainrot.dev"
SCHEMA_ID = "org.gnome.shell.extensions.brainrot"


def source_dir() -> Path:
    """The copy that ships inside the package."""
    return Path(__file__).resolve().parent / "extension" / UUID


def target_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return Path(base) / "gnome-shell" / "extensions" / UUID


def is_gnome() -> bool:
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP") or "").lower()
    return "gnome" in desktop


def installed() -> bool:
    return (target_dir() / "metadata.json").is_file()


def up_to_date() -> bool:
    """Whether what is installed is the version that shipped with this build."""
    try:
        here = (source_dir() / "extension.js").read_bytes()
        there = (target_dir() / "extension.js").read_bytes()
    except OSError:
        return False
    return here == there


def enabled() -> bool:
    """Enabled as far as the *shell* is concerned -- it is running."""
    out = _run(["gnome-extensions", "list", "--enabled"])
    return out is not None and UUID in out.split()


def enabled_next_session() -> bool:
    """Enabled in gsettings, which is what the shell reads when it starts.

    Different from :func:`enabled` in exactly one situation, and it is the
    common one right after installing: the extension is switched on but the
    running shell has never heard of it.
    """
    out = _run(["gsettings", "get", "org.gnome.shell", "enabled-extensions"])
    return out is not None and UUID in out


def _run(cmd: list[str]) -> "str | None":
    """Run a desktop tool, or return None when it is absent or unhappy."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def install(cfg: Config) -> tuple[bool, str]:
    """Copy, compile, configure, enable. Returns (ok, what happened)."""
    source = source_dir()
    if not (source / "metadata.json").is_file():
        return False, f"the extension did not ship with this install ({source})"
    if not is_gnome():
        return False, ("this is not a GNOME session; the extension is "
                       "gnome-shell-specific and would do nothing here")

    target = target_dir()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, dirs_exist_ok=True)
    except OSError as exc:
        return False, f"cannot write {target}: {exc}"

    schemas = target / "schemas"
    if schemas.is_dir() and _run(["glib-compile-schemas", str(schemas)]) is None:
        return False, ("glib-compile-schemas failed or is missing "
                       "(install libglib2.0-bin)")

    # The extension has to send to the port the daemon actually listens on,
    # and it cannot read the daemon's config.toml -- gnome-shell has no
    # business reading files out of an application's state directory.
    if cfg.port != Config.port:
        _run(["gsettings", "--schemadir", str(schemas), "set", SCHEMA_ID,
              "port", str(cfg.port)])

    if _run(["gnome-extensions", "enable", UUID]) is not None:
        return True, f"installed and enabled ({target})"

    # gnome-shell only learns about extension directories at startup or when it
    # installs one itself, so `gnome-extensions enable` on a brand new one
    # fails with "does not exist" -- and on Wayland the shell cannot be
    # restarted without ending the session. Measured on GNOME Shell 50.1;
    # ReloadExtension over D-Bus answers "deprecated and does not work".
    #
    # Marking it enabled in gsettings is what that command would have done
    # anyway, and it is read at startup, so the extension comes up with the
    # next session rather than needing to be enabled again by hand.
    if not _mark_enabled():
        return True, (f"copied to {target}, but could not mark it enabled -- "
                      f"run: gnome-extensions enable {UUID}")
    return True, (f"installed ({target}) and enabled for the next session. "
                  "gnome-shell only picks up a new extension at startup, so "
                  "log out and back in to switch it on now.")


def _mark_enabled() -> bool:
    """Add ourselves to the shell's enabled list, leaving the rest alone."""
    current = _run(["gsettings", "get", "org.gnome.shell", "enabled-extensions"])
    if current is None:
        return False
    if UUID in current:
        return True
    body = current.strip()
    if not body.startswith("[") or not body.endswith("]"):
        return False
    inner = body[1:-1].strip()
    updated = f"[{inner}, '{UUID}']" if inner else f"['{UUID}']"
    return _run(["gsettings", "set", "org.gnome.shell",
                 "enabled-extensions", updated]) is not None


def uninstall() -> tuple[bool, str]:
    target = target_dir()
    if not installed():
        return True, "not installed"
    _run(["gnome-extensions", "disable", UUID])
    try:
        shutil.rmtree(target)
    except OSError as exc:
        return False, f"cannot remove {target}: {exc}"
    return True, f"removed {target}"


def configured_port() -> "int | None":
    """The port the installed extension is set to send to."""
    schemas = target_dir() / "schemas"
    out = _run(["gsettings", "--schemadir", str(schemas), "get", SCHEMA_ID, "port"])
    if out is None:
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def shell_version() -> str:
    out = _run(["gnome-shell", "--version"])
    return out.strip() if out else ""


def supported_versions() -> list[str]:
    try:
        data = json.loads((source_dir() / "metadata.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(v) for v in data.get("shell-version", [])]
