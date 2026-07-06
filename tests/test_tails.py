"""Tests for tail dependence helpers."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics.stats.tails import _rank_1d, partial_tail_spearman, rolling_tail_dep_vs_center


def test_rank_1d_monotone() -> None:
    a = np.array([10, 11, 12], dtype=float)
    ranks = _rank_1d(a)
    assert ranks.shape == a.shape
    assert np.allclose(ranks, np.array([1.0, 2.0, 3.0]))


def test_rank_1d_uses_average_ranks_for_ties() -> None:
    ranks = _rank_1d(np.array([20.0, 10.0, 20.0, 30.0]))
    assert np.allclose(ranks, np.array([2.5, 1.0, 2.5, 4.0]))


def test_partial_tail_spearman_monotone() -> None:
    x = np.arange(1, 11, dtype=float)
    y = 2 * x + 1
    left, right, diff = partial_tail_spearman(x, y, b=0.5, min_t=3)
    assert left > 0
    assert right > 0
    assert np.isfinite(diff)


def test_partial_tail_spearman_splits_each_series_at_its_median() -> None:
    x = np.array([0, 1, 2, 3, 10, 11, 12, 13], dtype=float)
    y = np.array([0, 1, 2, 3, 13, 12, 11, 10], dtype=float)

    bottom, top, diff = partial_tail_spearman(x, y, b=0.5, min_t=3)

    assert np.isclose(bottom, 1.0)
    assert np.isclose(top, -1.0)
    assert np.isclose(diff, 2.0)


def test_partial_tail_spearman_noise_symmetry() -> None:
    rng = np.random.RandomState(42)
    x = rng.standard_normal(200)
    y = x + rng.standard_normal(200) * 0.01
    left, right, diff = partial_tail_spearman(x, y, b=0.4, min_t=20)
    assert abs(diff) < 0.2
    assert np.isfinite(left)
    assert np.isfinite(right)


def test_rolling_tail_dep_vs_center_returns_separate_climate_tail_cubes() -> None:
    time = np.datetime64("2024-01-01") + np.arange(12).astype("timedelta64[D]")
    y = np.arange(3)
    x = np.arange(3)
    center = np.linspace(-8.0, 12.0, time.size)
    data = np.empty((time.size, y.size, x.size), dtype=float)

    for yi in range(y.size):
        for xi in range(x.size):
            data[:, yi, xi] = center + (yi * 0.05) - (xi * 0.02)

    data[:, 0, 1] = center**2
    data[:, 2, 0] = np.sin(np.linspace(0.0, np.pi, time.size))

    cube = xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="tmean",
        attrs={"units": "degC", "source": "synthetic-prism"},
    )

    bottom_tail, top_tail, diff_tail = rolling_tail_dep_vs_center(
        cube,
        window_days=20,
        min_t=5,
        b=0.5,
    )

    assert bottom_tail.dims == ("time_window_end", "y", "x")
    assert top_tail.dims == bottom_tail.dims
    assert diff_tail.dims == bottom_tail.dims
    assert bottom_tail.sizes["time_window_end"] > 0

    assert bottom_tail.attrs["long_name"] == "Below-median Spearman synchrony vs center"
    assert top_tail.attrs["long_name"] == "Above-median Spearman synchrony vs center"
    assert diff_tail.attrs["long_name"] == "Below minus above median Spearman synchrony"
    assert bottom_tail.attrs["reference_pixel_y"] == 1
    assert bottom_tail.attrs["reference_pixel_x"] == 1
    assert bottom_tail.attrs["tail_b"] == 0.5
    assert bottom_tail.attrs["split_method"] == "per_series_quantile"

    np.testing.assert_allclose(
        diff_tail.values,
        (bottom_tail - top_tail).values,
        atol=1e-7,
        equal_nan=True,
    )
    assert np.isfinite(float(bottom_tail.isel(time_window_end=-1, y=1, x=1)))
    assert np.isfinite(float(top_tail.isel(time_window_end=-1, y=1, x=1)))
