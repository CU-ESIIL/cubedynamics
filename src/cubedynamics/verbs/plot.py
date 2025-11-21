"""Plotting verb for displaying the default cube viewer."""

from __future__ import annotations

from typing import Any, Callable, Optional

import xarray as xr
from IPython.display import display

from cubedynamics.plotting.cube_plot import (
    CoordCube,
    CubePlot,
    ScaleFillContinuous,
    theme_cube_studio,
)
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
    legend_title: str | None = None,
    theme_kwargs: dict[str, Any] | None = None,
    caption: dict | None = None,
    show_progress: bool = True,
    progress_style: str = "bar",
    time_dim: str | None = None,
    view_elev: float | None = None,
    view_azim: float | None = None,
    view_zoom: float | None = None,
    fill_mode: str = "shell",
    volume_density: dict[str, int] | None = None,
    volume_downsample: dict[str, int] | None = None,
    **_: Any,
) -> xr.DataArray:
    """Render the cube viewer and return the original DataArray."""

    theme = theme_cube_studio()
    if theme_kwargs:
        for key, val in theme_kwargs.items():
            if hasattr(theme, key) and val is not None:
                setattr(theme, key, val)

    coord = CoordCube()
    if view_elev is not None:
        coord.elev = view_elev
    if view_azim is not None:
        coord.azim = view_azim
    if view_zoom is not None:
        coord.zoom = view_zoom

    cube_plot = CubePlot(
        da,
        title=title,
        legend_title=legend_title,
        theme=theme,
        caption=caption,
        size_px=size_px,
        cmap=cmap,
        thin_time_factor=thin_time_factor,
        time_label=time_label,
        x_label=x_label,
        y_label=y_label,
        time_dim=time_dim,
        show_progress=show_progress,
        progress_style=progress_style,
        out_html=out_html,
        coord=coord,
        fill_scale=ScaleFillContinuous(cmap=cmap, name=legend_title),
        fill_mode=fill_mode,
        volume_density=volume_density or {"time": 6, "x": 2, "y": 2},
        volume_downsample=volume_downsample or {"time": 4, "space": 4},
    )

    display(cube_plot)
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
    legend_title: str | None = None,
    bg: str | None = None,
    lighting: str | None = None,
    fig_id: int | str | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
    caption: dict | None = None,
    show_progress: bool = True,
    progress_style: str = "bar",
    time_dim: str | None = None,
    view_elev: float | None = None,
    view_azim: float | None = None,
    view_zoom: float | None = None,
    fill_mode: str = "shell",
    volume_density: dict[str, int] | None = None,
    volume_downsample: dict[str, int] | None = None,
    **kwargs: Any,
) -> Callable[[xr.DataArray], xr.DataArray] | xr.DataArray:
    """Display a streaming 3D CSS cube viewer for a ``DataArray``.

    The verb is the public entry point for the grammar: ``pipe(cube) | v.plot()``
    renders a cube with captions, legend, and progress feedback, while advanced
    users can lean on :class:`cubedynamics.plotting.cube_plot.CubePlot` to
    combine stats, geoms, scales, themes, and facets. All rendering remains
    streaming-first and avoids materializing large cubes in memory.
    """

    def _op(obj: xr.DataArray) -> xr.DataArray:
        if not isinstance(obj, xr.DataArray):
            raise TypeError(
                "v.plot expects an xarray.DataArray. " f"Got type {type(obj)!r}."
            )

        t_dim, y_dim, x_dim = _infer_time_y_x_dims(obj)
        default_title = obj.name or f"{t_dim} × {y_dim} × {x_dim} cube"

        caption_payload = caption or None
        if caption_payload is None and any(v is not None for v in (fig_id, fig_title, fig_text)):
            caption_payload = {"id": fig_id, "title": fig_title, "text": fig_text}

        theme_overrides = {"bg_color": bg, "panel_color": bg, "lighting_style": lighting}

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
            legend_title=legend_title,
            theme_kwargs=theme_overrides,
            caption=caption_payload,
            show_progress=show_progress,
            progress_style=progress_style,
            time_dim=time_dim or t_dim,
            view_elev=view_elev,
            view_azim=view_azim,
            view_zoom=view_zoom,
            fill_mode=fill_mode,
            volume_density=volume_density,
            volume_downsample=volume_downsample,
            **kwargs,
        )

    # If a DataArray is provided directly, render immediately; otherwise return
    # a callable so the verb can be used in pipelines.
    if da is None:
        return _op

    return _op(da)
