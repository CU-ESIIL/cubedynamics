"""Tests for anomaly utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics.config import STD_EPS
from cubedynamics.stats.anomalies import (
    rolling_mean,
    temporal_anomaly,
    temporal_difference,
    zscore_over_time,
)


def test_zscore_over_time_basic(tiny_cube: xr.DataArray) -> None:
    z = zscore_over_time(tiny_cube, dim="time", std_eps=STD_EPS)

    assert z.shape == tiny_cube.shape
    assert z.dims == tiny_cube.dims

    mean = z.mean(dim="time", skipna=True)
    std = z.std(dim="time", skipna=True)

    assert np.all(np.isfinite(mean))
    assert np.all(np.isfinite(std))

    max_abs_mean = float(np.abs(mean).max())
    max_std_dev = float(np.abs(std - 1.0).max())
    assert max_abs_mean < 1e-2
    assert max_std_dev < 1e-2


def test_zscore_over_time_std_eps_masks_flat_series() -> None:
    time = np.arange(5)
    y = np.arange(2)
    x = np.arange(2)
    data = np.ones((len(time), len(y), len(x)), dtype=float)
    da = xr.DataArray(data, coords={"time": time, "y": y, "x": x}, dims=("time", "y", "x"))

    z = zscore_over_time(da, dim="time", std_eps=1e-4)
    assert np.isnan(z).all()


def test_temporal_anomaly_full_baseline(tiny_cube: xr.DataArray) -> None:
    anomalies = temporal_anomaly(tiny_cube, dim="time")
    mean = anomalies.mean(dim="time", skipna=True)
    assert float(np.abs(mean).max()) < 1e-2


def test_temporal_anomaly_subset_baseline() -> None:
    time = pd.date_range("2000-01-01", periods=4, freq="D")
    data = xr.DataArray(
        [0.0, 0.0, 10.0, 10.0],
        coords={"time": time},
        dims=("time",),
    )
    anomalies = temporal_anomaly(
        data,
        dim="time",
        baseline_slice=slice("2000-01-01", "2000-01-02"),
    )
    np.testing.assert_allclose(anomalies.values, [0.0, 0.0, 10.0, 10.0])


def test_temporal_difference_basic() -> None:
    time = np.arange(5)
    data = xr.DataArray(
        [0.0, 1.0, 3.0, 6.0, 10.0],
        coords={"time": time},
        dims=("time",),
    )
    diff = temporal_difference(data, lag=1, dim="time")
    assert np.isnan(diff.values[0])
    np.testing.assert_allclose(diff.values[1:], [1.0, 2.0, 3.0, 4.0])


def test_rolling_mean_basic() -> None:
    time = np.arange(5)
    data = xr.DataArray(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        coords={"time": time},
        dims=("time",),
    )
    rm = rolling_mean(data, window=3, dim="time", center=False)
    assert np.isnan(rm.values[0])
    assert np.isnan(rm.values[1])
    np.testing.assert_allclose(rm.values[2:], [2.0, 3.0, 4.0])
