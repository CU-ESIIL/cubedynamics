"""Lexcube visualization helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import xarray as xr

from ..config import TIME_DIM, X_DIM, Y_DIM

if TYPE_CHECKING:  # pragma: no cover - import-time dependency hint only
    import lexcube


def show_cube_lexcube(
    cube: xr.DataArray,
    title: str = "",
    cmap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
) -> "lexcube.Cube3DWidget":
    """Create a Lexcube Cube3DWidget from a 3D cube (time, y, x)."""

    import lexcube

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
