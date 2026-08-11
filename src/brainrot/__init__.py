"""claude-brainrot: procedurally generated distraction for Claude Code's thinking time."""

#: Kept as a literal, and pinned to pyproject.toml by a test rather than read
#: from the installed distribution at import time: `importlib.metadata` costs
#: 36 ms to answer, on every `import brainrot`, for a string that changes
#: about once a month. This project counts milliseconds -- the hook shim exists
#: in the shape it does to save exactly that kind of time.
__version__ = "0.2.0"

__all__ = ["__version__"]
