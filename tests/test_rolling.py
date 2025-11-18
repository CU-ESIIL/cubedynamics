"""Tests for rolling statistics utilities."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics.stats.rolling import rolling_pairwise_stat_cube


def test_rolling_pairwise_stat_cube_shapes(tiny_cube: xr.DataArray) -> None:
    ref = tiny_cube.isel(y=0, x=0)

    def mean_diff(x_ts: np.ndarray, ref_ts: np.ndarray) -> float:
        return float(np.nanmean(x_ts - ref_ts))

    result = rolling_pairwise_stat_cube(
        cube=tiny_cube,
        ref=ref,
        stat_func=mean_diff,
        window_days=3,
        min_t=2,
        time_dim="time",
    )

    assert result.ndim == 3
    end_dim = "time_window_end"
    assert end_dim in result.dims
    assert "y" in result.dims
    assert "x" in result.dims
    assert result.sizes["y"] == tiny_cube.sizes["y"]
    assert result.sizes["x"] == tiny_cube.sizes["x"]
    assert result.sizes[end_dim] >= 1


def test_rolling_pairwise_stat_cube_window_growth() -> None:
    time = np.arange("2000-01-01", "2000-01-10", dtype="datetime64[D]")
    y = np.arange(1)
    x = np.arange(2)
    data = np.tile(np.arange(time.size)[:, None, None], (1, y.size, x.size)).astype(float)
    cube = xr.DataArray(data, coords={"time": time, "y": y, "x": x}, dims=("time", "y", "x"))
    ref = cube.isel(y=0, x=0)

    def diff_last(x_ts: np.ndarray, ref_ts: np.ndarray) -> float:
        return float((x_ts - ref_ts)[-1])

    result = rolling_pairwise_stat_cube(
        cube=cube,
        ref=ref,
        stat_func=diff_last,
        window_days=5,
        min_t=2,
        time_dim="time",
    )

    end_dim = "time_window_end"
    assert result.sizes[end_dim] == cube.sizes["time"] - 1
    last_vals = result.isel({end_dim: -1}).values
    assert np.allclose(last_vals, np.zeros_like(last_vals))
