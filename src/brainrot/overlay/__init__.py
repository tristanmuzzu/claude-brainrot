"""Platform-specific window treatment for the overlay strip.

The engine's :mod:`brainrot.engine.window` owns the window itself; this
package holds the Win32 surgery that raylib has no API for -- alt-tab
suppression, activation-proofing, and attaching the overlay just above the
Claude Code host window instead of floating above everything.
"""
