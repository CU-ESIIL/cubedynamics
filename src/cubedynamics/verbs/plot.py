"""Plotting verb for displaying the default cube viewer."""

from __future__ import annotations

from typing import Any

import xarray as xr
from IPython.display import display

from cubedynamics.plotting.cube_viewer import cube_from_dataarray


__all__ = ["plot"]


def plot(
    da: xr.DataArray,
    *,
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    out_html: str = "cube_da.html",
    **kwargs: Any,
) -> xr.DataArray:
    """Display a 3D CSS cube viewer for the provided ``DataArray``.

    This verb is designed for piping workflows, e.g. ``pipe(cube) | v.plot(...)``.
    It renders the HTML viewer produced by :func:`cube_from_dataarray` and then
    returns the original DataArray so additional verbs can be chained.

    Parameters
    ----------
    da : xr.DataArray
        Input cube, ideally with (time, y, x) dimensions (order inferred
        internally by :func:`cube_from_dataarray`).
    cmap : str, default "viridis"
        Matplotlib colormap to use for the cube faces.
    size_px : int, default 260
        Cube face size in pixels.
    thin_time_factor : int, default 4
        Factor used inside :func:`cube_from_dataarray` to thin very long time
        axes for performance.
    out_html : str, default "cube_da.html"
        Filename for the generated HTML viewer.
    **kwargs : Any
        Additional keyword arguments accepted for API flexibility; currently
        ignored.

    Returns
    -------
    xr.DataArray
        The original DataArray, unchanged.
    """

    viewer = cube_from_dataarray(
        da,
        out_html=out_html,
        cmap=cmap,
        size_px=size_px,
        thin_time_factor=thin_time_factor,
    )

    display(viewer)
    return da
