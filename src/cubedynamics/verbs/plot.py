"""Plotting verb for displaying cubes via :class:`CubePlot`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import overload

import xarray as xr

from cubedynamics.plotting.cube_plot import CubePlot, ScaleFillContinuous
from cubedynamics.streaming import VirtualCube
from cubedynamics.utils import _infer_time_y_x_dims
from ..piping import Verb
from ..vase import extract_vase_from_attrs

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
    fig_text: str | None = None


@overload
def plot(
    da: xr.DataArray | VirtualCube,
    *,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
) -> xr.DataArray | VirtualCube:
    ...


@overload
def plot(
    *,
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
    ...


def plot(
    da: xr.DataArray | VirtualCube | None = None,
    *,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
):
    """Plot a cube or return a plotting verb.

    When ``da`` is provided this function builds a :class:`CubePlot` and passes
    the original object through unchanged so pipe chains can continue. Without a
    ``da`` argument a :class:`~cubedynamics.piping.Verb` is returned for use with
    ``pipe(...) | v.plot(...)``.
    """

    opts = PlotOptions(
        title=title,
        cmap=cmap,
        size_px=size_px,
        thin_time_factor=thin_time_factor,
        time_dim=time_dim,
        clim=clim,
        fig_id=fig_id,
        fig_title=fig_title,
        fig_text=fig_text,
    )

    def _plot(value: xr.DataArray | VirtualCube):
        da_value = value.materialize() if isinstance(value, VirtualCube) else value
        if not isinstance(da_value, xr.DataArray):
            raise TypeError(
                "v.plot expects an xarray.DataArray or VirtualCube. "
                f"Got type {type(da_value)!r}."
            )

        t_dim, y_dim, x_dim = _infer_time_y_x_dims(da_value)
        resolved_time = opts.time_dim or t_dim
        default_title = da_value.name or f"{resolved_time} × {y_dim} × {x_dim} cube"

        caption_payload = None
        if opts.fig_id is not None or opts.fig_title is not None or opts.fig_text is not None:
            caption_payload = {"id": opts.fig_id, "title": opts.fig_title, "text": opts.fig_text}

        # 1. Build CubePlot for this cube
        cube = CubePlot(
            da_value,
            title=opts.title or default_title,
            caption=caption_payload,
            size_px=opts.size_px,
            cmap=opts.cmap,
            thin_time_factor=opts.thin_time_factor,
            time_dim=resolved_time,
            fill_scale=ScaleFillContinuous(cmap=opts.cmap, limits=opts.clim),
            fig_title=opts.fig_title,
        )

        # 2. Draw cube
        cube = cube.geom_cube(cmap=opts.cmap)

        # 3. If a vase is present, overlay outline
        vase = extract_vase_from_attrs(da_value)
        if vase is not None:
            cube = cube.stat_vase(vase).geom_vase_outline(
                color="limegreen",
                alpha=0.6,
            )

        # 4. Apply studio theme with tight axes (implementation in CubePlot)
        cube = cube.theme_cube_studio(tight_axes=True)

        return cube

    verb = Verb(_plot)
    verb._cd_passthrough_on_pipe = True
    verb._cd_passthrough_on_call = True
    if da is None:
        return verb
    verb(da)
    return da
