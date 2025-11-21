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
    """Compute a boolean vase mask for a time-varying polygon hull.

    This verb wraps :func:`cubedynamics.vase.build_vase_mask` so it can be used
    inline with ``pipe(...)``. It only inspects coordinate arrays and streams
    over time slices, leaving dask-backed cubes lazy.

    Parameters match the cube's dimension names and default to ``("time", "y", "x")``.
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
    """Mask a cube so that values outside the vase become ``NaN``.

    Under the hood this computes the same boolean mask as :func:`vase_mask`
    (via :func:`cubedynamics.vase.build_vase_mask`) and applies ``cube.where``
    to preserve laziness. Use it when you want a cube restricted to the vase
    volume while keeping the streaming-first pipeline intact.
    """
    mask = build_vase_mask(
        cube,
        vase,
        time_dim=time_dim,
        y_dim=y_dim,
        x_dim=x_dim,
    )
    da_out = cube.where(mask)

    # Attach the vase definition so plotting helpers can auto-detect it later
    da_out.attrs["vase"] = vase

    return da_out
