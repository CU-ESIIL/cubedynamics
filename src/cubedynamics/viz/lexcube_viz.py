"""Lexcube visualization helpers."""

from __future__ import annotations

import lexcube
import xarray as xr

from ..config import TIME_DIM, X_DIM, Y_DIM


def show_cube_lexcube(
    cube: xr.DataArray,
    title: str = "",
    cmap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
) -> lexcube.Cube3DWidget:
    """Create a Lexcube Cube3DWidget from a 3D cube (time, y, x)."""

    expected_dims = {TIME_DIM, Y_DIM, X_DIM}
    if cube.ndim != 3 or set(cube.dims) != expected_dims:
        raise ValueError(
            "Lexcube visualization requires dims exactly (time, y, x); "
            f"received dims {cube.dims}"
        )

    cube = cube.transpose(TIME_DIM, Y_DIM, X_DIM)
    widget = lexcube.Cube3DWidget(
        cube,
        title=title,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )
    return widget
