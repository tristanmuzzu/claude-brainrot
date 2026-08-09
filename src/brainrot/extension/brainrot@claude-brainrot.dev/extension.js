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

import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
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

export default class BrainrotExtension extends Extension {
    enable() {
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
        this._portChangedId = this._settings.connect('changed::port', () => {
            this._address = null;
            this._openSocket();
        });
        this._schedule(IDLE_MS);
    }

    disable() {
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
        this._timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT_IDLE, interval, () => {
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
                this._takeoverReturnTo.activate(global.get_current_time());
            } catch (e) {
                /* The window went away while the overlay had the keyboard. */
            }
            this._takeoverReturnTo = null;
        }
        this._send(JSON.stringify({kind: 'takeover', on: this._takeoverActive}));
    }
}
