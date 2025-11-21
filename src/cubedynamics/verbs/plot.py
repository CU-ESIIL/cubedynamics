"""Plotting verb for displaying the default cube viewer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import xarray as xr

from cubedynamics.plotting.cube_plot import CubePlot, ScaleFillContinuous
from cubedynamics.streaming import VirtualCube
from cubedynamics.utils import _infer_time_y_x_dims
from cubedynamics.piping import Verb


__all__ = ["plot"]


@dataclass
class PlotOptions:
    title: str | None = None
    cmap: str = "viridis"
    size_px: int = 260
    thin_time_factor: int = 4
    time_dim: str | None = None
    clim: tuple[float, float] | None = None
    fig_id: int | None = None
    fig_title: str | None = None


def plot(
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
) -> Verb:
    """Return a cube plotting verb that yields a single displayable object."""

    opts = PlotOptions(
        title=title,
        cmap=cmap,
        size_px=size_px,
        thin_time_factor=thin_time_factor,
        time_dim=time_dim,
        clim=clim,
        fig_id=fig_id,
        fig_title=fig_title,
    )

    def _plot(da: xr.DataArray | VirtualCube):
        if isinstance(da, VirtualCube):
            da = da.materialize()
        if not isinstance(da, xr.DataArray):
            raise TypeError(
                "v.plot expects an xarray.DataArray or VirtualCube. "
                f"Got type {type(da)!r}."
            )

        t_dim, y_dim, x_dim = _infer_time_y_x_dims(da)
        resolved_time = opts.time_dim or t_dim
        default_title = da.name or f"{resolved_time} × {y_dim} × {x_dim} cube"

        caption_payload = None
        if opts.fig_id is not None or opts.fig_title is not None or fig_text is not None:
            caption_payload = {"id": opts.fig_id, "title": opts.fig_title, "text": fig_text}

        cube = CubePlot(
            da,
            title=opts.title or default_title,
            caption=caption_payload,
            size_px=opts.size_px,
            cmap=opts.cmap,
            thin_time_factor=opts.thin_time_factor,
            time_dim=resolved_time,
            fill_scale=ScaleFillContinuous(cmap=opts.cmap, limits=opts.clim),
            fig_title=opts.fig_title,
        )
        return cube

    return Verb(_plot)
