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
    width_px: int | None = None
    height_px: int | None = None
    thin_time_factor: int = 4
    time_dim: str | None = None
    clim: tuple[float, float] | None = None
    fig_id: int | None = None
    fig_title: str | None = None
    fig_text: str | None = None
    debug: bool = False
    viewer_id: str | None = None
    full_res: bool = False


def _decimate_for_view(
    da: xr.DataArray,
    *,
    max_time: int = 120,
    step_xy: int = 2,
    xy_threshold: int = 512,
) -> xr.DataArray:
    """Return a lighter-weight view for interactive plotting.

    If the cube exceeds ``max_time`` or ``xy_threshold``, subsample time and space
    so the viewer remains responsive. Intended for visualization only; callers
    can disable via ``full_res=True`` in :func:`plot`.
    """

    t_dim, y_dim, x_dim = _infer_time_y_x_dims(da)
    if t_dim is None or y_dim is None or x_dim is None:
        return da

    sizes = da.sizes
    needs_downsample = (
        sizes.get(t_dim, 0) > max_time
        or sizes.get(x_dim, 0) > xy_threshold
        or sizes.get(y_dim, 0) > xy_threshold
    )
    if not needs_downsample:
        return da

    t_step = max(1, sizes[t_dim] // max_time)
    return da.isel(
        {
            t_dim: slice(0, sizes[t_dim], t_step),
            x_dim: slice(None, None, step_xy),
            y_dim: slice(None, None, step_xy),
        }
    )


@overload
def plot(
    da: xr.DataArray | VirtualCube,
    *,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int = 260,
    width_px: int | None = None,
    height_px: int | None = None,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
    debug: bool = False,
    viewer_id: str | None = None,
    full_res: bool = False,
) -> xr.DataArray | VirtualCube:
    ...


@overload
def plot(
    *,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int = 260,
    width_px: int | None = None,
    height_px: int | None = None,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
    debug: bool = False,
    viewer_id: str | None = None,
    full_res: bool = False,
) -> Verb:
    ...


def plot(
    da: xr.DataArray | VirtualCube | None = None,
    *,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int = 260,
    width_px: int | None = None,
    height_px: int | None = None,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
    debug: bool = False,
    viewer_id: str | None = None,
    full_res: bool = False,
):
    """Plot a cube or return a plotting verb.

    The helper builds a streaming-first :class:`CubePlot` and returns it so pipe
    chains (``pipe(cube) | v.plot()``) can continue with the viewer object. When
    used as a verb (no ``da`` argument), it can be composed in pipes and the
    resulting :class:`CubePlot` is available via ``.unwrap()``.

    For large cubes the viewer automatically decimates to keep rotations smooth
    (time slices capped around ``max_time=120`` and spatial steps of ``step_xy=2``).
    Pass ``full_res=True`` to disable this safety net.
    """

    opts = PlotOptions(
        title=title,
        cmap=cmap,
        size_px=size_px,
        width_px=width_px,
        height_px=height_px,
        thin_time_factor=thin_time_factor,
        time_dim=time_dim,
        clim=clim,
        fig_id=fig_id,
        fig_title=fig_title,
        fig_text=fig_text,
        debug=debug,
        viewer_id=viewer_id,
        full_res=full_res,
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

        da_for_view = da_value if opts.full_res else _decimate_for_view(da_value)
        if da_for_view is not da_value:
            logger.info(
                "Downsampling cube for viewer: original %s -> view %s",
                da_value.sizes,
                da_for_view.sizes,
            )

        caption_payload = None
        if opts.fig_id is not None or opts.fig_title is not None or opts.fig_text is not None:
            caption_payload = {"id": opts.fig_id, "title": opts.fig_title, "text": opts.fig_text}

        # 1. Build CubePlot for this cube
        cube = CubePlot(
            da_for_view,
            title=opts.title or default_title,
            caption=caption_payload,
            size_px=opts.size_px,
            viewer_width=opts.width_px,
            viewer_height=opts.height_px,
            cmap=opts.cmap,
            thin_time_factor=opts.thin_time_factor,
            time_dim=resolved_time,
            fill_scale=ScaleFillContinuous(cmap=opts.cmap, limits=opts.clim),
            fig_title=opts.fig_title,
            debug=opts.debug,
            viewer_id=opts.viewer_id,
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
