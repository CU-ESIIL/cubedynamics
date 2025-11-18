"""Lexcube visualization helpers."""

from __future__ import annotations

import lexcube
import xarray as xr


def show_cube_lexcube(
    cube: xr.DataArray,
    title: str = "",
    cmap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
) -> lexcube.Cube3DWidget:
    """Create a Lexcube Cube3DWidget from a 3D cube (time, y, x)."""

    if cube.ndim != 3:
        raise ValueError("Cube must have exactly three dimensions (time, y, x)")
    widget = lexcube.Cube3DWidget(
        cube,
        title=title,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )
    return widget
