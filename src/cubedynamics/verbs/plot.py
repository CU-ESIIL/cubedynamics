"""Plotting verb for displaying cubes via :class:`CubePlot`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import overload

import logging

import xarray as xr

from cubedynamics.plotting.cube_plot import CubePlot, ScaleFillContinuous
from cubedynamics.streaming import VirtualCube
from cubedynamics.utils import _infer_time_y_x_dims
from ..piping import Verb
from ..vase import extract_vase_from_attrs

__all__ = ["plot"]


logger = logging.getLogger(__name__)


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

    The helper builds a streaming-first :class:`CubePlot` and returns it so pipe
    chains (``pipe(cube) | v.plot()``) can continue with the viewer object. When
    used as a verb (no ``da`` argument), it can be composed in pipes and the
    resulting :class:`CubePlot` is available via ``.unwrap()``.
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

        logger.info(
            "v.plot() called with da name=%s dims=%s", getattr(da_value, "name", None), da_value.dims
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
    if da is None:
        return verb
    return verb(da)
