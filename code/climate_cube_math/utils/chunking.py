"""Chunking and subsampling utilities."""

from __future__ import annotations

import xarray as xr


def coarsen_and_stride(
    cube: xr.DataArray,
    coarsen_factor: int = 1,
    time_stride: int = 1,
    y_dim: str = "y",
    x_dim: str = "x",
    time_dim: str = "time",
) -> xr.DataArray:
    """Optionally coarsen spatially and subsample in time."""

    result = cube
    if coarsen_factor > 1:
        result = result.coarsen({y_dim: coarsen_factor, x_dim: coarsen_factor}, boundary="trim").mean()
    if time_stride > 1:
        result = result.isel({time_dim: slice(0, None, time_stride)})
    return result
