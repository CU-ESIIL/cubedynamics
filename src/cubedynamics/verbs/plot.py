"""Plotting verb for displaying cubes via :class:`CubePlot`.

This module is part of the CubeDynamics "grammar-of-cubes":
- Data loaders produce xarray objects (often dask-backed) with dims ``(time, y, x)``.
- Verbs are pipe-friendly transformations: cube → cube (or cube → scalar/plot side-effect).
- Plotting follows a grammar-of-graphics model (aes, geoms, stats, scales, themes).

Canonical API:
- :func:`cubedynamics.verbs.plot.plot` (side-effect verb returning the viewer)
- :class:`cubedynamics.plotting.cube_plot.CubePlot`
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import html
import io
from typing import Any, Hashable, overload

import logging

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cubedynamics.plotting.axis_rig import AxisRigSpec
from cubedynamics.plotting.cube_plot import (
    CubePlot,
    ScaleFillContinuous,
    plotly_camera_to_coord,
    resolve_camera,
)
from cubedynamics.streaming import VirtualCube
from cubedynamics.utils import _infer_time_y_x_dims
from ..piping import Verb
from ..vase import VaseDefinition, extract_vase_from_attrs

__all__ = ["plot"]


logger = logging.getLogger(__name__)


@dataclass
class PlotOptions:
    title: str | None = None
    cmap: str = "viridis"
    size_px: int | None = None
    thin_time_factor: int = 4
    time_dim: str | None = None
    clim: tuple[float, float] | None = None
    camera: dict | None = None
    axis_rig: bool | AxisRigSpec = True
    fig_id: int | None = None
    fig_title: str | None = None
    fig_text: str | None = None


@dataclass
class StaticPlot:
    """Notebook-ready static rendering for non-cube semantic arrays."""

    data: xr.DataArray
    figure: object
    kind: str
    title: str

    @property
    def axes(self):
        return self.figure.axes

    def savefig(self, *args, **kwargs):
        return self.figure.savefig(*args, **kwargs)

    def _png_bytes(self) -> bytes:
        buffer = io.BytesIO()
        self.figure.savefig(buffer, format="png", dpi=140, bbox_inches="tight")
        return buffer.getvalue()

    def _repr_png_(self) -> bytes:  # pragma: no cover - exercised by notebooks
        return self._png_bytes()

    def _repr_html_(self) -> str:  # pragma: no cover - exercised by notebooks
        encoded = base64.b64encode(self._png_bytes()).decode("ascii")
        alt = html.escape(f"{self.title} ({self.kind})", quote=True)
        return (
            "<figure class='cd-static-plot'>"
            f"<img src='data:image/png;base64,{encoded}' alt='{alt}' "
            "style='max-width:100%;height:auto'/>"
            f"<figcaption>{html.escape(self.title)}</figcaption>"
            "</figure>"
        )


@overload
def plot(
    da: xr.DataArray | xr.Dataset | VirtualCube,
    *,
    variable: Hashable | None = None,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int | None = None,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    camera: dict | None = None,
    axis_rig: bool | AxisRigSpec = True,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
) -> CubePlot | StaticPlot:
    ...


@overload
def plot(
    *,
    variable: Hashable | None = None,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int | None = None,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    camera: dict | None = None,
    axis_rig: bool | AxisRigSpec = True,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
) -> Verb:
    ...


def plot(
    da: xr.DataArray | xr.Dataset | VirtualCube | Any | None = None,
    *,
    variable: Hashable | None = None,
    title: str | None = None,
    cmap: str = "viridis",
    size_px: int | None = None,
    thin_time_factor: int = 4,
    time_dim: str | None = None,
    clim: tuple[float, float] | None = None,
    camera: dict | None = None,
    axis_rig: bool | AxisRigSpec = True,
    fig_id: int | None = None,
    fig_title: str | None = None,
    fig_text: str | None = None,
):
    """Plot a cube, semantic Dataset, or EventResult using dimensional dispatch.

    Grammar contract
    ----------------
    Output verb (cube → viewer). When called with ``da`` it
    immediately builds a :class:`~cubedynamics.plotting.cube_plot.CubePlot` and
    returns it without mutating the source cube. When called without ``da`` it
    returns a pipe-ready :class:`~cubedynamics.piping.Verb` so you can write
    ``pipe(cube) | v.plot(...)``.

    Parameters
    ----------
    da : xarray.DataArray, xarray.Dataset, VirtualCube, or EventResult, optional
        Input semantic object. Three-dimensional time-space fields use the
        interactive cube viewer, 2-D spatial fields use a static map, and 1-D
        temporal fields use a static line plot. EventResult selects its
        ``event_active`` field. If ``None``, a verb is returned.
    variable : hashable, optional
        Dataset variable to render. When omitted, ``state`` then
        ``event_active`` is preferred, or the sole data variable is used.
        Ambiguous Datasets require an explicit selection.
    title : str, optional
        Override the viewer title. Defaults to ``<name> time × y × x cube``.
    cmap : str, default "viridis"
        Colormap used for the fill scale.
    size_px : int, optional
        Pixel size for each facet tile. If omitted, the viewer uses responsive sizing.
    thin_time_factor : int, default 4
        Decimation factor for time frames to keep the viewer responsive.
    time_dim : str, optional
        Name of the temporal dimension. Inferred when not provided.
    clim : tuple of float, optional
        Color limits for the continuous scale.
    camera : dict, optional
        Plotly-style camera configuration used to set the initial cube view.
        When omitted, a front-right, zoomed-out default is applied.
    fig_id, fig_title, fig_text : optional
        Caption metadata used by the viewer export helpers.

    Returns
    -------
    CubePlot, StaticPlot, or Verb
        Interactive viewer for a 3-D cube, notebook-ready static map/line view
        for a 2-D or 1-D summary, or a pipe-ready verb when ``da`` is omitted.

    Notes
    -----
    Selecting a Dataset variable preserves dask backing and merges Dataset
    semantic attrs with variable attrs on the shallow viewer input. The viewer
    only samples minimal data for
    thumbnails, keeping streaming behavior intact. If a vase is attached in
    ``da.attrs['vase']`` a thin outline overlay is attempted. The original cube
    is not mutated; the pipe's wrapped result is the viewer.

    Examples
    --------
    Direct call:
    >>> import cubedynamics as cd
    >>> cube = cd.load_gridmet_cube(lat=40.0, lon=-105.0, start="2005-01-01", end="2005-01-05", variable="tmmx")
    >>> viewer = cd.verbs.plot.plot(cube, cmap="magma")

    Pipe style:
    >>> from cubedynamics import pipe, verbs as v
    >>> viewer = (pipe(cube) | v.plot(cmap="magma")).unwrap()
    >>> cube  # cube still available

    See Also
    --------
    cubedynamics.plotting.cube_plot.CubePlot
    cubedynamics.verbs.plot_mean.plot_mean
    cubedynamics.piping.pipe
    """

    opts = PlotOptions(
        title=title,
        cmap=cmap,
        size_px=size_px,
        thin_time_factor=thin_time_factor,
        time_dim=time_dim,
        clim=clim,
        camera=camera,
        axis_rig=axis_rig,
        fig_id=fig_id,
        fig_title=fig_title,
        fig_text=fig_text,
    )

    def _static_plot(da_value: xr.DataArray) -> StaticPlot:
        semantic_name = str(
            opts.title
            or da_value.attrs.get("semantic_name")
            or da_value.name
            or "CubeDynamics summary"
        )
        units = da_value.attrs.get("semantic_units") or da_value.attrs.get("units")
        label = semantic_name if not units else f"{semantic_name} ({units})"
        figure, axis = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)

        if da_value.ndim == 2:
            dims = {str(dim).casefold() for dim in da_value.dims}
            spatial_pairs = ({"x", "y"}, {"lon", "lat"}, {"longitude", "latitude"})
            if not any(pair.issubset(dims) for pair in spatial_pairs):
                plt.close(figure)
                raise ValueError(
                    "v.plot supports 2-D spatial fields with (y, x), (lat, lon), "
                    "or (latitude, longitude) dimensions; "
                    f"received dims {da_value.dims!r}."
                )
            plot_kwargs = {"ax": axis, "cmap": opts.cmap}
            if opts.clim is not None:
                plot_kwargs.update({"vmin": opts.clim[0], "vmax": opts.clim[1]})
            da_value.plot(**plot_kwargs, cbar_kwargs={"label": label})
            kind = "spatial_map"
        elif da_value.ndim == 1:
            dim = da_value.dims[0]
            coord = da_value.coords.get(dim)
            temporal = str(dim).casefold() in {"time", "t", "date", "datetime"}
            if coord is not None:
                try:
                    temporal = temporal or np.issubdtype(coord.dtype, np.datetime64)
                except TypeError:
                    # Object/cftime coordinates are accepted only when their
                    # dimension name explicitly identifies temporal meaning.
                    pass
            if not temporal:
                plt.close(figure)
                raise ValueError(
                    "v.plot supports a 1-D temporal field when its dimension is "
                    "time/date-like; "
                    f"received dims {da_value.dims!r}."
                )
            da_value.plot.line(ax=axis)
            axis.set_ylabel(label)
            if opts.clim is not None:
                axis.set_ylim(*opts.clim)
            kind = "temporal_line"
        else:
            plt.close(figure)
            raise ValueError(
                "v.plot supports a 3-D time × space cube, a 2-D spatial field, "
                "or a 1-D temporal field; "
                f"received {da_value.ndim} dimensions {da_value.dims!r}."
            )

        axis.set_title(semantic_name)
        figure.canvas.draw()
        return StaticPlot(da_value, figure, kind, semantic_name)

    def _plot(value: object):
        materialized = value.materialize() if isinstance(value, VirtualCube) else value
        event_dataset = getattr(materialized, "dataset", None)
        if isinstance(event_dataset, xr.Dataset):
            materialized = event_dataset
        if isinstance(materialized, xr.Dataset):
            selected = variable
            if selected is None and "state" in materialized.data_vars:
                selected = "state"
            if selected is None and "event_active" in materialized.data_vars:
                selected = "event_active"
            if selected is None and len(materialized.data_vars) == 1:
                selected = next(iter(materialized.data_vars))
            if selected is None:
                raise ValueError(
                    "v.plot requires variable= for a Dataset with multiple renderable "
                    f"variables: {list(materialized.data_vars)!r}"
                )
            if selected not in materialized.data_vars:
                raise ValueError(
                    f"Variable {selected!r} is not present in the Dataset: "
                    f"{list(materialized.data_vars)!r}"
                )
            da_value = materialized[selected].copy(deep=False)
            da_value.attrs = {**materialized.attrs, **da_value.attrs}
        elif isinstance(materialized, xr.DataArray):
            if variable is not None:
                raise ValueError("v.plot received variable= for a DataArray input")
            da_value = materialized
        else:
            raise TypeError(
                "v.plot expects an xarray.DataArray, xarray.Dataset, VirtualCube, "
                "or EventResult-like object with a Dataset-valued .dataset. "
                f"Got type {type(materialized)!r}."
            )

        logger.info(
            "v.plot() called with da name=%s dims=%s", getattr(da_value, "name", None), da_value.dims
        )

        if da_value.ndim < 3:
            return _static_plot(da_value)
        if da_value.ndim != 3:
            raise ValueError(
                "v.plot supports a 3-D time × space cube, a 2-D spatial field, "
                "or a 1-D temporal field; "
                f"received {da_value.ndim} dimensions {da_value.dims!r}."
            )

        t_dim, y_dim, x_dim = _infer_time_y_x_dims(da_value)
        resolved_time = opts.time_dim or t_dim
        default_title = (
            da_value.attrs.get("semantic_name")
            or da_value.name
            or f"{resolved_time} × {y_dim} × {x_dim} cube"
        )

        caption_payload = None
        if opts.fig_id is not None or opts.fig_title is not None or opts.fig_text is not None:
            caption_payload = {"id": opts.fig_id, "title": opts.fig_title, "text": opts.fig_text}

        camera_to_use = resolve_camera(opts.camera)
        coord = plotly_camera_to_coord(camera_to_use)

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
            coord=coord,
            camera=camera_to_use,
            axis_rig=opts.axis_rig,
        )

        # 2. Draw cube
        cube = cube.geom_cube(cmap=opts.cmap)

        # 3. If a vase is present, overlay outline
        vase = extract_vase_from_attrs(da_value)
        if vase is not None:
            if not isinstance(vase, VaseDefinition):
                logger.warning(
                    "Ignoring attrs['vase'] with unexpected type %s; skipping vase overlay",
                    type(vase).__name__,
                )
            else:
                try:
                    cube = cube.stat_vase(vase).geom_vase_outline(
                        color="limegreen",
                        alpha=0.6,
                    )
                except Exception as exc:  # pragma: no cover - defensive guard
                    logger.warning("Vase overlay failed; continuing without vase: %s", exc)

        # 4. Apply studio theme with tight axes (implementation in CubePlot)
        cube = cube.theme_cube_studio(tight_axes=True)

        return cube

    verb = Verb(_plot)
    if da is None:
        return verb
    return verb(da)
