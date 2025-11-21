from __future__ import annotations

import xarray as xr

from ..vase import VaseDefinition, build_vase_mask


def vase_mask(
    cube: xr.DataArray,
    vase: VaseDefinition,
    time_dim: str = "time",
    y_dim: str = "y",
    x_dim: str = "x",
) -> xr.DataArray:
    """
    Compute a boolean vase mask. Streaming-safe: does not touch cube.values.
    """
    return build_vase_mask(
        cube,
        vase,
        time_dim=time_dim,
        y_dim=y_dim,
        x_dim=x_dim,
    )


def vase_extract(
    cube: xr.DataArray,
    vase: VaseDefinition,
    time_dim: str = "time",
    y_dim: str = "y",
    x_dim: str = "x",
) -> xr.DataArray:
    """
    Mask cube so that values outside the vase become NaN.
    """
    mask = build_vase_mask(
        cube,
        vase,
        time_dim=time_dim,
        y_dim=y_dim,
        x_dim=x_dim,
    )
    return cube.where(mask)
