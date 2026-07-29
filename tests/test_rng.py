"""Seeding: the never-repeat guarantee and its replay counterpart."""

from __future__ import annotations

from pathlib import Path

from brainrot.palette import generate
from brainrot.rng import RunCounter, Seed, golden_sequence


def test_distinct_runs_never_share_a_seed() -> None:
    roots = {Seed.for_run(n).root for n in range(1, 5000)}
    assert len(roots) == 4999


def test_replay_is_exact() -> None:
    a = Seed.for_run(4712)
    b = Seed.for_run(4712)
    assert a.root == b.root
    assert a.stream("layout").random() == b.stream("layout").random()


def test_substreams_are_independent() -> None:
    """Consuming from one stream must not shift another.

    This is what lets a scene's generation change without re-rolling the
    palette, which in turn is what makes tuning generated content tractable.
    """
    seed = Seed.for_run(99)
    palette_first = seed.stream("palette")
    layout = seed.stream("layout")
    for _ in range(1000):
        layout.random()

    expected = Seed.for_run(99).stream("palette").random()
    assert palette_first.random() == expected


def test_streams_differ_by_label() -> None:
    seed = Seed.for_run(7)
    assert seed.stream("a").random() != seed.stream("b").random()


def test_counter_persists_and_increments(tmp_path: Path) -> None:
    counter = RunCounter(tmp_path)
    assert counter.value == 0
    first = counter.next()
    second = counter.next()
    assert (first.run, second.run) == (1, 2)

    # A fresh process must not restart the sequence -- that is what would let
    # content repeat.
    reopened = RunCounter(tmp_path)
    assert reopened.value == 2
    assert reopened.next().run == 3


def test_corrupt_state_file_degrades_gracefully(tmp_path: Path) -> None:
    (tmp_path / "state.json").write_text("{ not json", encoding="utf-8")
    counter = RunCounter(tmp_path)
    assert counter.value == 0
    assert counter.next().run == 1


def test_golden_sequence_spreads_hues() -> None:
    """Consecutive runs must land far apart on the colour wheel."""
    values = [golden_sequence(n) for n in range(1, 60)]
    gaps = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    # Wrapped distance, so a gap of 0.9 is really 0.1.
    wrapped = [min(g, 1.0 - g) for g in gaps]
    assert min(wrapped) > 0.2


def test_consecutive_runs_look_different() -> None:
    """End-to-end: neighbouring runs should not produce the same sky."""
    skies = [generate(Seed.for_run(n)).sky_bottom for n in range(1, 30)]
    for i in range(1, len(skies)):
        assert skies[i] != skies[i - 1]
