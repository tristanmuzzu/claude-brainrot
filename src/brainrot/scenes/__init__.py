"""Generated scenes.

Importing this package registers every scene. Worlds are generated per seed;
the models they are dressed with are built from the Blender scripts in
``assets/src`` -- nothing is downloaded, nothing is sourced footage.
"""

from . import parkour, runner  # noqa: F401

__all__ = ["parkour", "runner"]
