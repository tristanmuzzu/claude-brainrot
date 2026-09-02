/*
 * claude-brainrot — GNOME Shell extension.
 *
 * The overlay daemon is an ordinary application, and on GNOME/Wayland an
 * ordinary application is not allowed to know:
 *
 *   1. which window is in front (org.gnome.Shell.Introspect.GetWindows is
 *      refused: "GetWindows is not allowed"), so the strip cannot tell
 *      whether you are still looking at Claude Code;
 *   2. where any window is, including its own, so the strip cannot stand
 *      beside the Claude Code window instead of on a screen edge;
 *   3. where the pointer is when it is over a Wayland surface — XQueryPointer
 *      answers, and answers with a stale position — so the strip cannot be
 *      dragged.
 *
 * Inside the compositor all three are ordinary calls. This extension makes
 * them, and pushes the answers to the daemon over the same loopback UDP
 * socket the Claude Code hooks already use: no D-Bus client in the daemon, no
 * new dependency, and a daemon that is not running simply drops the packets.
 *
 * It sends nothing but window geometry, window class, process ids and the
 * pointer. No titles, no contents, no keystrokes.
 */

import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

/* Idle cadence. A packet a second is enough to tell a daemon that has just
 * started where everything is; anything faster is only worth paying for while
 * something is actually moving. */
const IDLE_MS = 250;
const HEARTBEAT_MS = 1000;

/* While a modifier is held the pointer is probably being used to drag the
 * strip, and the gesture wants to keep up with the hand. */
const DRAGGING_MS = 16;

/* Clutter modifier bits. Sent as a mask so the daemon can compare against its
 * own configured chord without knowing anything about Clutter, and masked
 * down to these on the way out so nothing else about the keyboard leaves the
 * compositor -- lock state included. */
const SHIFT = 1 << 0;
const CONTROL = 1 << 2;
const ALT = 1 << 3;          /* MOD1 */
const SUPER = 1 << 6;        /* MOD4 */
const BUTTONS = (1 << 8) | (1 << 9) | (1 << 10);
const MOD_MASK = SHIFT | CONTROL | ALT | SUPER | BUTTONS;

/* How switched-off looks. The strip is off far more often than it is on for
 * anybody who uses the switch at all, so "off" has to be legible at a glance
 * in a bar of full-strength symbolic icons without becoming a second icon to
 * learn. Dimmed is what the shell itself does everywhere else. */
const ICON_ON = 255;
const ICON_OFF = 85;

/*
 * The top-bar switch.
 *
 * The overlay is deliberately hard to dismiss from inside itself: it never
 * takes focus, never appears on alt-tab and passes every click through to
 * whatever is behind it, so there is nowhere on the strip to put a close
 * button that a click could ever reach. The one place a toggle can live is
 * the panel, and the panel belongs to the shell -- which is where this
 * extension already is.
 *
 * No menu (`dontCreateMenu`): one press is the whole interaction, and a
 * popup asking which of one thing you meant is a second click for nothing.
 */
const BrainrotIndicator = GObject.registerClass(
class BrainrotIndicator extends PanelMenu.Button {
    _init(settings, onChanged) {
        super._init(0.0, 'Claude Brainrot', true);
        this._settings = settings;
        this._onChanged = onChanged;
        this._icon = new St.Icon({
            /* In the standard icon set on every shell version this extension
             * claims, so there is no asset to ship and nothing to fall back
             * to when a user's icon theme is not Adwaita. */
            icon_name: 'applications-games-symbolic',
            style_class: 'system-status-icon',
        });
        this.add_child(this._icon);
        this._changedId = this._settings.connect(
            'changed::overlay-enabled', () => this._sync(false));
        this._bindClick();
        this._sync(true);
    }

    /* GNOME 49 moved the panel off event signals and onto Clutter gestures --
     * `PanelMenu.Button` itself opens its menu from a `ClickGesture` now, and
     * a gesture that recognises a press is not obliged to let the old
     * `button-press-event` signal through afterwards. Use the same mechanism
     * the panel uses where it exists, and the old signals where it does not,
     * because this extension claims shell 45 upwards and 45-48 have no
     * `ClickGesture` at all. */
    _bindClick() {
        if (Clutter.ClickGesture) {
            const gesture = new Clutter.ClickGesture();
            gesture.set_recognize_on_press(true);
            gesture.connect('recognize', () => this._toggle());
            this.add_action(gesture);
            return;
        }
        this.connect('button-press-event', () => this._toggle());
        this.connect('touch-event', event => {
            if (event.type() === Clutter.EventType.TOUCH_BEGIN)
                return this._toggle();
            return Clutter.EVENT_PROPAGATE;
        });
    }

    _toggle() {
        this._settings.set_boolean(
            'overlay-enabled', !this._settings.get_boolean('overlay-enabled'));
        return Clutter.EVENT_STOP;
    }

    _sync(quiet) {
        const on = this._settings.get_boolean('overlay-enabled');
        this._icon.opacity = on ? ICON_ON : ICON_OFF;
        /* Both of these are read aloud by a screen reader and shown by the
         * accessibility inspector; a dimmed icon says nothing to either. */
        this.accessible_name = on
            ? 'Claude Brainrot: on' : 'Claude Brainrot: off';
        this._icon.accessible_name = this.accessible_name;
        if (!quiet && this._onChanged)
            this._onChanged(on);
    }

    destroy() {
        if (this._changedId) {
            this._settings.disconnect(this._changedId);
            this._changedId = 0;
        }
        super.destroy();
    }
});

export default class BrainrotExtension extends Extension {
    enable() {
        /* A headless gnome-shell (`gnome-shell --headless --virtual-monitor
         * ...`, e.g. a second invisible session for computer-use tooling)
         * loads the same enabled-extensions list as the real one -- and two
         * extensions pushing snapshots of two different desktops to one
         * daemon port made the strip flap between them: scale, work area and
         * host window alternated with every datagram, which on screen is the
         * strip jumping side to side (2026-08-25). This extension's whole job
         * is to describe the desktop the user is looking at, so in a
         * compositor nobody can look at it stays silent. */
        if (this._isHeadless())
            return;
        this._settings = this.getSettings();
        this._encoder = new TextEncoder();
        this._socket = null;
        this._address = null;
        this._timer = 0;
        this._interval = 0;
        this._lastPayload = '';
        this._lastSent = 0;
        this._seq = 0;

        this._openSocket();
        this._bindTakeover();
        /* Leftmost of the right-hand group: beside the other things that are
         * about this session rather than about the machine. */
        this._indicator = new BrainrotIndicator(
            this._settings, () => this._tick());
        Main.panel.addToStatusArea(this.uuid, this._indicator, 0, 'right');
        this._portChangedId = this._settings.connect('changed::port', () => {
            this._address = null;
            this._openSocket();
        });
        this._schedule(IDLE_MS);
    }

    disable() {
        /* The lock screen disables session-mode "user" extensions, so this
         * runs with a takeover genuinely active: give the keyboard back
         * exactly as the chord would, or the previously focused window never
         * regains focus and the daemon stays latched until the turn idles. */
        if (this._takeoverActive)
            this._toggleTakeover();
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
        if (this._timer) {
            GLib.source_remove(this._timer);
            this._timer = 0;
        }
        if (this._portChangedId) {
            this._settings.disconnect(this._portChangedId);
            this._portChangedId = 0;
        }
        if (this._takeoverBound) {
            Main.wm.removeKeybinding('takeover');
            this._takeoverBound = false;
        }
        if (this._socket) {
            try {
                this._socket.close();
            } catch (e) {
                /* Closing a socket that is already gone is not a problem. */
            }
            this._socket = null;
        }
        this._settings = null;
    }

    _isHeadless() {
        /* The compositor's own command line is the one place its headlessness
         * is stated. Extensions run inside the gnome-shell process, so
         * /proc/self is that process; anything unreadable means a real
         * session, because every headless invocation names itself. */
        try {
            const [ok, bytes] = GLib.file_get_contents('/proc/self/cmdline');
            if (!ok)
                return false;
            const cmdline = new TextDecoder().decode(bytes);
            return cmdline.includes('--headless') ||
                cmdline.includes('--virtual-monitor');
        } catch (e) {
            return false;
        }
    }

    /* -- transport ------------------------------------------------------ */

    _openSocket() {
        try {
            if (!this._socket) {
                this._socket = new Gio.Socket({
                    family: Gio.SocketFamily.IPV4,
                    type: Gio.SocketType.DATAGRAM,
                    protocol: Gio.SocketProtocol.UDP,
                });
                this._socket.init(null);
                /* Never let a full send buffer stall the compositor's main
                 * loop: a dropped frame of brainrot costs nothing, a stalled
                 * shell costs the session. */
                this._socket.set_blocking(false);
                /* 2026-09-02: bind to loopback explicitly. Without a bind the
                 * kernel autobinds 0.0.0.0 on first send, which showed up as
                 * gnome-shell listening on a UDP port reachable from the LAN. */
                this._socket.bind(Gio.InetSocketAddress.new(
                    Gio.InetAddress.new_loopback(Gio.SocketFamily.IPV4), 0), true);
            }
            this._address = Gio.InetSocketAddress.new_from_string(
                '127.0.0.1', this._settings.get_int('port'));
        } catch (e) {
            this._socket = null;
        }
    }

    _send(text) {
        if (!this._socket || !this._address)
            return;
        try {
            this._socket.send_to(this._address, this._encoder.encode(text), null);
        } catch (e) {
            /* ECONNREFUSED on a loopback datagram means nobody is listening,
             * which is the normal state when the daemon is not running. */
        }
    }

    /* -- what the daemon needs ------------------------------------------ */

    _snapshot() {
        const display = global.display;
        const focus = display.focus_window;
        const monitorCount = display.get_n_monitors();
        const primary = display.get_primary_monitor();
        const workspace = global.workspace_manager.get_active_workspace();

        const windows = [];
        for (const actor of global.get_window_actors()) {
            const win = actor.meta_window;
            if (!win || win.is_override_redirect())
                continue;
            const type = win.window_type;
            if (type !== Meta.WindowType.NORMAL && type !== Meta.WindowType.UTILITY)
                continue;
            const rect = win.get_frame_rect();
            windows.push({
                id: win.get_id(),
                pid: win.get_pid(),
                cls: win.get_wm_class() || '',
                rect: [rect.x, rect.y, rect.width, rect.height],
                mon: win.get_monitor(),
                hidden: win.minimized || !win.showing_on_its_workspace(),
            });
        }

        const monitors = [];
        for (let i = 0; i < monitorCount; i++) {
            const area = workspace.get_work_area_for_monitor(i);
            monitors.push({
                index: i,
                work: [area.x, area.y, area.width, area.height],
                scale: this._monitorScale(i),
                primary: i === primary,
            });
        }

        const [px, py, mods] = global.get_pointer();
        return {
            kind: 'shell',
            seq: ++this._seq,
            focus: focus && !focus.is_override_redirect() ? focus.get_id() : 0,
            windows,
            monitors,
            pointer: [px, py, mods & MOD_MASK],
            /* The top-bar switch, on every snapshot rather than as an edge
             * when it changes: the daemon restarts far more often than the
             * shell does, and a toggle it missed while it was down would come
             * back on by itself. Costs a boolean a second. */
            power: this._settings.get_boolean('overlay-enabled'),
            /* The daemon works in X11 pixels and everything above is in
             * logical ones; it derives the ratio from this against the X
             * screen size rather than trusting a scale factor it cannot
             * check. */
            logical: this._logicalSize(),
        };
    }

    _logicalSize() {
        try {
            const [width, height] = global.display.get_size();
            return [width, height];
        } catch (e) {
            return [global.screen_width ?? 0, global.screen_height ?? 0];
        }
    }

    _monitorScale(index) {
        try {
            return global.display.get_monitor_scale(index);
        } catch (e) {
            return 1;
        }
    }

    /* -- the pump -------------------------------------------------------- */

    _schedule(interval) {
        if (this._timer && this._interval === interval)
            return;
        if (this._timer)
            GLib.source_remove(this._timer);
        this._interval = interval;
        /* PRIORITY_DEFAULT, not DEFAULT_IDLE: the daemon calls the bridge
         * stale after 3 s of silence, and idle-priority sources are starved
         * for exactly that long whenever the shell's main loop stays busy --
         * a workspace animation under load was enough to flap the daemon
         * into degraded mode mid-turn and back. The tick is a snapshot and a
         * datagram; it costs the compositor nothing measurable. */
        this._timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, interval, () => {
            this._tick();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _tick() {
        let snapshot;
        try {
            snapshot = this._snapshot();
        } catch (e) {
            return;
        }

        /* Follow the hand while a modifier is held -- that is the drag
         * gesture arming itself -- and idle the rest of the time. */
        this._schedule(snapshot.pointer[2] ? DRAGGING_MS : IDLE_MS);

        /* Compare without the sequence number, so an unchanged desktop is
         * recognised as unchanged and costs one heartbeat a second. */
        const seq = snapshot.seq;
        snapshot.seq = 0;
        const text = JSON.stringify(snapshot);
        const now = GLib.get_monotonic_time() / 1000;
        if (text === this._lastPayload && now - this._lastSent < HEARTBEAT_MS)
            return;
        this._lastPayload = text;
        this._lastSent = now;
        snapshot.seq = seq;
        this._send(JSON.stringify(snapshot));
    }

    /* -- the takeover chord ---------------------------------------------- */

    _bindTakeover() {
        /* A Wayland client cannot register a global hotkey: gsd-media-keys
         * asks mutter to grab the accelerator and the grab is refused. Inside
         * gnome-shell it is one call -- and being *grabbed* rather than polled
         * is the stronger privacy story, because nothing else typed anywhere
         * is ever read. */
        this._takeoverActive = false;
        this._takeoverReturnTo = null;
        try {
            Main.wm.addKeybinding(
                'takeover',
                this._settings,
                Meta.KeyBindingFlags.NONE,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW,
                () => this._toggleTakeover());
            this._takeoverBound = true;
        } catch (e) {
            this._takeoverBound = false;
        }
    }

    /*
     * The on/off state lives here rather than in the daemon because the half
     * the daemon cannot do is the important half: giving the keyboard *back*.
     * A Wayland client may not activate another window, so if the compositor
     * did not remember what was focused before, letting go of the overlay
     * would leave the keyboard nowhere.
     */
    _toggleTakeover() {
        this._takeoverActive = !this._takeoverActive;
        if (this._takeoverActive) {
            const focus = global.display.focus_window;
            this._takeoverReturnTo = focus && !focus.is_override_redirect() ? focus : null;
        } else if (this._takeoverReturnTo) {
            try {
                /* Only put focus back if nothing else claimed it while the
                 * overlay had the keyboard. A window that opened mid-takeover
                 * -- a portal file chooser, a modal dialog -- holds focus
                 * legitimately, and re-activating the old window would raise
                 * it over the new one and bury it. Focus still on the window
                 * being restored, on the overlay's own strip (WM_CLASS
                 * "claude-brainrot", the title InitWindow sets), or on
                 * nothing at all means the chord is the only thing that
                 * moved focus, so give it back. */
                const focusNow = global.display.focus_window;
                if (!focusNow
                    || focusNow === this._takeoverReturnTo
                    || focusNow.get_wm_class() === 'claude-brainrot')
                    this._takeoverReturnTo.activate(global.get_current_time());
            } catch (e) {
                /* The window went away while the overlay had the keyboard. */
            }
            this._takeoverReturnTo = null;
        }
        this._send(JSON.stringify({kind: 'takeover', on: this._takeoverActive}));
    }
}
