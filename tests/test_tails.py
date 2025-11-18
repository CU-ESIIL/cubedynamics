"""Tests for tail dependence helpers."""

from __future__ import annotations

import numpy as np

from cubedynamics.stats.tails import _rank_1d, partial_tail_spearman


def test_rank_1d_monotone() -> None:
    a = np.array([10, 11, 12], dtype=float)
    ranks = _rank_1d(a)
    assert ranks.shape == a.shape
    assert np.allclose(ranks, np.array([1.0, 2.0, 3.0]))


def test_partial_tail_spearman_monotone() -> None:
    x = np.arange(1, 11, dtype=float)
    y = 2 * x + 1
    left, right, diff = partial_tail_spearman(x, y, b=0.5, min_t=3)
    assert left > 0
    assert right > 0
    assert np.isfinite(diff)


def test_partial_tail_spearman_noise_symmetry() -> None:
    rng = np.random.RandomState(42)
    x = rng.standard_normal(200)
    y = x + rng.standard_normal(200) * 0.01
    left, right, diff = partial_tail_spearman(x, y, b=0.4, min_t=20)
    assert abs(diff) < 0.2
    assert np.isfinite(left)
    assert np.isfinite(right)
