"""Tests for correlation helpers."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics.stats.correlation import pearson_corr_stat, rolling_corr_vs_center


def test_pearson_corr_stat_basic() -> None:
    x = np.array([1, 2, 3, 4, 5], dtype=float)
    y = np.array([2, 4, 6, 8, 10], dtype=float)
    r = pearson_corr_stat(x, y)
    assert np.isfinite(r)
    assert r > 0.99


def test_pearson_corr_stat_handles_constant_series() -> None:
    x = np.ones(5, dtype=float)
    y = np.arange(5, dtype=float)
    r = pearson_corr_stat(x, y)
    assert np.isnan(r)


def test_rolling_corr_vs_center_on_identical_pixels(tiny_cube: xr.DataArray) -> None:
    center_series = tiny_cube.isel(y=0, x=0)
    data = np.broadcast_to(center_series.values[:, None, None], tiny_cube.shape)
    cube = xr.DataArray(data, coords=tiny_cube.coords, dims=tiny_cube.dims, name="identical")

    corr_cube = rolling_corr_vs_center(
        zcube=cube,
        window_days=10,
        min_t=2,
        time_dim="time",
    )

    assert np.all(np.isfinite(corr_cube.values))
    assert float(np.nanmin(corr_cube.values)) > 0.9
    assert "time_window_end" in corr_cube.dims
