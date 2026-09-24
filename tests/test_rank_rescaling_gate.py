"""Contracts for the explicit temperature-rank synchrony decision gate."""

from __future__ import annotations

import numpy as np

from cubedynamics.stats.tails import one_tail_spearman
from scripts.run_rank_rescaling_gate import (
    _collapse,
    empirical_rank_coordinates,
    rank_rescaled_tail_spearman,
    raw_tail_membership,
)


def test_empirical_rank_coordinates_use_average_ties_and_n_plus_one() -> None:
    values = np.array([20.0, 10.0, 20.0, 30.0, np.nan])
    actual = empirical_rank_coordinates(values)
    np.testing.assert_allclose(actual[:4], np.array([2.5, 1.0, 2.5, 4.0]) / 5.0)
    assert np.isnan(actual[-1])


def test_complete_support_rank_gate_preserves_tail_membership_and_spearman() -> None:
    rng = np.random.default_rng(20260924)
    x = np.round(rng.normal(size=91), 1)
    y = np.round(0.6 * x + rng.normal(scale=0.8, size=91), 1)
    for tail in ("lower", "upper"):
        old_value, old_count = one_tail_spearman(x, y, tail=tail, b=0.5, min_t=10)
        new_value, new_count, new_mask, _, _ = rank_rescaled_tail_spearman(
            x, y, tail=tail
        )
        old_mask = raw_tail_membership(x, y, tail=tail)
        np.testing.assert_array_equal(new_mask, old_mask)
        np.testing.assert_allclose(new_value, old_value, atol=0, rtol=0)
        assert new_count == old_count


def test_rank_quantile_preserves_a_tied_raw_median_boundary() -> None:
    x = np.arange(1.0, 10.0)
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 7.0, 8.0, 9.0])
    old = raw_tail_membership(x, y, tail="lower")
    _, _, new, _, y_rank = rank_rescaled_tail_spearman(x, y, tail="lower", min_t=2)
    np.testing.assert_array_equal(new, old)
    assert np.quantile(y_rank, 0.5) > 0.5


def test_sample_grid_collapse_excludes_self_and_level2_rank_degenerates() -> None:
    import xarray as xr

    values = np.arange(400, dtype=float).reshape(20, 20) / 400
    dataset = xr.Dataset(
        {
            "old_cold": (("y", "x"), values),
            "rank_cold": (("y", "x"), values),
            "old_hot": (("y", "x"), values / 2),
            "rank_hot": (("y", "x"), values / 2),
            "old_delta": (("y", "x"), values / 2),
            "rank_delta": (("y", "x"), values / 2),
        }
    )
    collapsed = _collapse(dataset)
    assert collapsed["self_pair_excluded"] is True
    assert collapsed["nonself_pairs"] == 399
    assert collapsed["difference"] == {"cold": 0.0, "hot": 0.0, "delta": 0.0}
    assert collapsed["within_neighborhood_rank_median"] == {
        "cold": 0.5,
        "hot": 0.5,
        "delta": 0.5,
    }

