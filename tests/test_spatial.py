"""Tests for spatial cube math primitives."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics.stats.spatial import (
    mask_by_threshold,
    spatial_coarsen_mean,
    spatial_smooth_mean,
)


def test_spatial_coarsen_mean_basic() -> None:
    data = xr.DataArray(
        np.arange(4 * 4).reshape(4, 4),
        coords={"y": np.arange(4), "x": np.arange(4)},
        dims=("y", "x"),
    )
    coarsened = spatial_coarsen_mean(data, factor_y=2, factor_x=2, y_dim="y", x_dim="x")
    assert coarsened.sizes["y"] == 2
    assert coarsened.sizes["x"] == 2
    assert np.isclose(coarsened.values[0, 0], 2.5)


def test_spatial_smooth_mean_basic() -> None:
    data = xr.DataArray(
        np.zeros((5, 5)),
        coords={"y": np.arange(5), "x": np.arange(5)},
        dims=("y", "x"),
    )
    data = data.copy()
    data.loc[dict(y=2, x=2)] = 1.0

    smoothed = spatial_smooth_mean(data, kernel_size=3, y_dim="y", x_dim="x")
    center_value = smoothed.sel(y=2, x=2).item()
    assert 0.0 < center_value < 1.0


def test_mask_by_threshold() -> None:
    data = xr.DataArray(
        [0.0, 1.0, 2.0, 3.0],
        coords={"idx": np.arange(4)},
        dims=("idx",),
    )
    mask = mask_by_threshold(data, threshold=1.5, direction=">")
    assert mask.dtype == bool
    np.testing.assert_array_equal(mask.values, [False, False, True, True])


def test_mask_by_threshold_leq() -> None:
    data = xr.DataArray(
        [0.0, 1.0, 2.0],
        coords={"idx": np.arange(3)},
        dims=("idx",),
    )
    mask = mask_by_threshold(data, threshold=1.0, direction="<=")
    np.testing.assert_array_equal(mask.values, [True, True, False])
