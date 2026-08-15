"""The re-entry probe measures what it claims to.

``tools/reentry_probe.py`` is the acceptance test for the parkour rehash
(``docs/REHASH.md``), and a probe nobody checks reads whatever it likes -- this
project has had two that exempted precisely the thing they were measuring. So
the walker is exercised against worlds small enough to reason about by hand,
where the answer is known before the probe runs:

* a course laid on a continuous floor is a **shortcut** -- fall, step back up,
  carry on from where you were;
* the same course with nothing under it is **dead** -- the fall goes to the sea;
* a floor only at the level's opening is **back to the start**, which is the
  thing the owner asked for.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from brainrot.scenes import parkourkit as pk

ROOT = Path(__file__).resolve().parent.parent


def _probe():
    """Import the probe by path: ``tools/`` is not a package."""
    path = ROOT / "tools" / "reentry_probe.py"
    spec = importlib.util.spec_from_file_location("reentry_probe", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("reentry_probe", mod)
    spec.loader.exec_module(mod)
    return mod


probe = _probe()


class FakeCone:
    """A world whose terrain is a set of cells, all of it inside one level."""

    def __init__(self, rock) -> None:
        self.rock_cells = set(rock)

    def rock(self, cell) -> bool:
        return cell in self.rock_cells

    def unwrap(self, x, z, y) -> float:
        return 0.5


class FakeCourse:
    def __init__(self, cone, solid=()) -> None:
        self.cone = cone
        self.solid = set(solid)

    def blocked(self, cell) -> bool:
        return cell in self.solid or self.cone.rock(cell)

    def surface(self, blk) -> float:
        return blk["y"] + pk.FORMS[blk["form"]]


class FakeMove:
    """A straight hop from one stand point to the next, apex a metre up."""

    def __init__(self, frm, to) -> None:
        self.frm, self.to = frm, to

    def points(self, samples):
        out = []
        for i in range(samples + 1):
            t = i / samples
            out.append(tuple(self.frm[k] + (self.to[k] - self.frm[k]) * t
                             for k in range(3)))
            out[-1] = (out[-1][0], out[-1][1] + 1.0 * (1 - (2 * t - 1) ** 2),
                       out[-1][2])
        return out


def block(x, y, z, **kw) -> dict:
    out = {"x": x, "y": y, "z": z, "form": "full", "deco": [], "pedestal": (),
           "origin": "design", "author": "TEST", "theme": "test",
           "move": None}
    out.update(kw)
    return out


def course_of(blocks, rock=(), y=0):
    """Wire up landings, their moves and a world holding them."""
    cone = FakeCone(rock)
    course = FakeCourse(cone, [(b["x"], b["y"], b["z"]) for b in blocks])
    for i in range(len(blocks) - 1):
        a, b = blocks[i], blocks[i + 1]
        blocks[i]["move"] = FakeMove(
            (a["x"], course.surface(a), a["z"]),
            (b["x"], course.surface(b), b["z"]))
    level = SimpleNamespace(index=1, u0=0.0, u1=1.0, y=y,
                            theme=SimpleNamespace(name="TEST"))
    return course, level


def floor(x0, x1, z0, z1, y):
    return {(x, y, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)}


# ---------------------------------------------------------------------------


def test_a_course_on_a_continuous_floor_is_all_shortcut():
    """Four landings on a terrace: every fall walks straight back up."""
    blocks = [block(x, 1, 0) for x in (0, 3, 6, 9)]
    course, level = course_of(blocks, rock=floor(-4, 14, -4, 4, 0))
    got = probe.judge(course, level, blocks)
    assert got["misses"] > 0
    # The first jump can only ever reach landing 0, which is "back to the
    # start" and legitimate; every later one re-enters mid-course.
    assert got["to_start"] > 0 and got["shortcut"] > 0, got
    assert got["shortcut"] + got["to_start"] == got["misses"], got
    assert got["worst_reentry"] >= 1
    # ...and it is the floor doing it.
    assert got["floor_contact"] == len(blocks)


def test_the_same_course_over_the_void_is_dead():
    """Take the terrace away and there is nothing to walk back from."""
    blocks = [block(x, 1, 0) for x in (0, 3, 6, 9)]
    course, level = course_of(blocks, rock=())
    got = probe.judge(course, level, blocks)
    assert got["misses"] > 0
    assert got["shortcut"] == 0, got
    assert got["dead"] == got["misses"]
    assert got["floor_contact"] == 0


def test_a_floor_only_at_the_opening_sends_you_back_to_the_start():
    """The shape the rehash asks for: the fall lands where only the level's
    first landing is reachable."""
    blocks = [block(0, 1, 0), block(3, 1, 0), block(6, 1, 0)]
    # Ground under the opening landing only. A fall from the first jump comes
    # down on it and can step back up onto landing 0; a fall from the second
    # is over the void and connects to nothing. Note how tight this is: extend
    # the slab to x=4 and the fall reaches landing 1 instead, which is the
    # defect -- one row of terrace past the opener is the whole difference.
    course, level = course_of(blocks, rock=floor(-2, 1, -2, 2, 0))
    got = probe.judge(course, level, blocks)
    assert got["shortcut"] == 0, got
    assert got["to_start"] > 0 and got["dead"] > 0, got


def test_a_pedestal_down_to_the_terrace_counts_as_floor_contact():
    """A landing three up is still standing on the terrace if its stack is."""
    blocks = [block(0, 4, 0, pedestal=((0, 3, 0), (0, 2, 0), (0, 1, 0))),
              block(3, 4, 0)]
    course, level = course_of(blocks, rock=floor(-2, 6, -2, 2, 0))
    got = probe.judge(course, level, blocks)
    assert got["floor_contact"] == 1, got


def test_a_jump_that_is_made_is_not_counted_as_a_fall():
    """Coming to rest on either end of a jump means the jump was made.

    Without this every landing in the tower reads as a shortcut off its own
    take-off block.
    """
    blocks = [block(0, 1, 0), block(2, 1, 0)]
    course, level = course_of(blocks, rock=())
    got = probe.judge(course, level, blocks)
    assert got["held"] > 0
    assert got["misses"] + got["held"] == probe.MISS_SAMPLES - 1


def test_the_climb_is_measured_and_the_crossing_is_exempt():
    blocks = [block(0, 1, 0), block(3, 2, 0), block(6, 3, 0),
              block(9, 2, 0, origin="crossing")]
    course, level = course_of(blocks, rock=(), y=0)
    got = probe.judge(course, level, blocks)
    assert got["drops"] == 0, "the crossing descends by design"
    assert got["climb"] == pytest.approx(1.0)
    blocks[2] = block(6, 1, 0)
    course, level = course_of(blocks, rock=())
    assert probe.judge(course, level, blocks)["drops"] == 1
