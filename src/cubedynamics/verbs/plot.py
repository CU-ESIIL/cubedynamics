"""Plotting verb for displaying the default cube viewer."""

from __future__ import annotations

from typing import Any, Callable, Optional

import xarray as xr
from IPython.display import display

from cubedynamics.plotting.cube_viewer import cube_from_dataarray
from cubedynamics.utils import _infer_time_y_x_dims


__all__ = ["plot"]


def _render_and_return(
    da: xr.DataArray,
    *,
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    out_html: str = "cube_da.html",
    title: str | None = None,
    time_label: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    **_: Any,
) -> xr.DataArray:
    """Render the cube viewer and return the original DataArray."""

    viewer = cube_from_dataarray(
        da,
        out_html=out_html,
        cmap=cmap,
        size_px=size_px,
        thin_time_factor=thin_time_factor,
        title=title,
        time_label=time_label,
        x_label=x_label,
        y_label=y_label,
    )

    display(viewer)
    return da


def plot(
    da: Optional[xr.DataArray] = None,
    *,
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    out_html: str = "cube_da.html",
    title: str | None = None,
    time_label: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    **kwargs: Any,
) -> Callable[[xr.DataArray], xr.DataArray] | xr.DataArray:
    """Display a 3D CSS cube viewer for a ``DataArray``.

    This verb supports both pipe-style usage (``pipe(cube) | v.plot(...)``)
    and direct invocation (``v.plot(...)(cube)`` or ``cd.plot(cube, ...)``).
    It renders the HTML viewer produced by :func:`cube_from_dataarray`,
    displays it in the active notebook, and returns the original DataArray so
    additional verbs can be chained.
    """

    def _op(obj: xr.DataArray) -> xr.DataArray:
        if not isinstance(obj, xr.DataArray):
            raise TypeError(
                "v.plot expects an xarray.DataArray. " f"Got type {type(obj)!r}."
            )

        t_dim, y_dim, x_dim = _infer_time_y_x_dims(obj)
        default_title = obj.name or f"{t_dim} × {y_dim} × {x_dim} cube"

        return _render_and_return(
            obj,
            cmap=cmap,
            size_px=size_px,
            thin_time_factor=thin_time_factor,
            out_html=out_html,
            title=title or default_title,
            time_label=time_label or t_dim,
            x_label=x_label or x_dim,
            y_label=y_label or y_dim,
            **kwargs,
        )

    # If a DataArray is provided directly, render immediately; otherwise return
    # a callable so the verb can be used in pipelines.
    if da is None:
        return _op

    return _op(da)
