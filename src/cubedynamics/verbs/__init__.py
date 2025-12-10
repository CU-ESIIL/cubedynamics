"""Namespace exposing pipe-friendly cube verbs."""

from __future__ import annotations

import cubedynamics.viz as viz
import xarray as xr
from IPython.display import display

from ..config import TIME_DIM, X_DIM, Y_DIM
from ..ops_fire.time_hull import (
    FireEventDaily,
    TimeHull,
    compute_time_hull_geometry,
    time_hull_to_vase,
)
from ..ops_fire.climate_hull_extract import (
    HullClimateSummary,
    build_inside_outside_climate_samples,
)
from ..ops.io import to_netcdf
from ..ops.ndvi import ndvi_from_s2
from ..ops.stats import correlation_cube
from ..ops.transforms import month_filter
from ..piping import Verb
from ..streaming import VirtualCube
from .custom import apply
from .flatten import flatten_cube, flatten_space
from .models import fit_model
from .plot import plot
from .plot_mean import plot_mean
from .tubes import tubes
from .vase import vase, vase_demo, vase_extract, vase_mask
from .stats import anomaly, mean, rolling_tail_dep_vs_center, variance, zscore


def _unwrap_dataarray(
    obj: xr.DataArray | VirtualCube | None,
) -> tuple[xr.DataArray, xr.DataArray | VirtualCube]:
    """
    Normalize a verb input to an (xarray.DataArray, original_obj) pair.

    - If obj is a VirtualCube, materialize its underlying DataArray while
      returning the original VirtualCube so downstream callers can keep
      working with the same type.
    - If obj is a DataArray, return it as both (base_da, original_obj).
    - If obj is None, raise a clear error.
    """

    if obj is None:
        raise ValueError("extract() requires an input cube/DataArray; got None.")

    if isinstance(obj, VirtualCube):
        base_da = obj.materialize()
        if not isinstance(base_da, xr.DataArray):
            raise TypeError("VirtualCube underlying data is not a DataArray.")
        return base_da, obj

    if isinstance(obj, xr.DataArray):
        return obj, obj

    raise TypeError(f"Unsupported type for extract(): {type(obj)!r}")


def landsat8_mpc(*args, **kwargs):
    """Lazy import wrapper for the Landsat MPC helper.

    Avoids importing optional heavy dependencies (e.g., rioxarray) unless the
    verb is actually invoked.
    """

    from .landsat_mpc import landsat8_mpc as _landsat8_mpc

    return _landsat8_mpc(*args, **kwargs)


def landsat_vis_ndvi(*args, **kwargs):
    """Lazy import wrapper for a visualization-friendly Landsat NDVI cube."""

    from .landsat_mpc import landsat_vis_ndvi as _landsat_vis_ndvi

    return _landsat_vis_ndvi(*args, **kwargs)


def landsat_ndvi_plot(*args, **kwargs):
    """Lazy import wrapper for Landsat NDVI plotting."""

    from .landsat_mpc import landsat_ndvi_plot as _landsat_ndvi_plot

    return _landsat_ndvi_plot(*args, **kwargs)


def show_cube_lexcube(**kwargs):
    """Render a Lexcube widget as a side-effect and return the original cube.

    The incoming object must represent a 3D cube with dims ``(time, y, x)``.
    Reducers such as :func:`mean`, :func:`variance`, :func:`anomaly`, and
    :func:`zscore` keep the cube Lexcube-ready when ``keep_dim=True``.
    """

    def _op(obj):
        # normalize to DataArray if needed (Dataset with 1 var)
        if isinstance(obj, xr.Dataset):
            if len(obj.data_vars) != 1:
                raise ValueError(
                    "show_cube_lexcube verb expects a Dataset with exactly one data variable."
                )
            var = next(iter(obj.data_vars))
            da = obj[var]
        else:
            da = obj

        required_dims = {TIME_DIM, Y_DIM, X_DIM}
        if da.ndim != 3 or set(da.dims) != required_dims:
            raise ValueError(
                "show_cube_lexcube expects a 3D cube with dims (time, y, x); "
                f"received dims {da.dims}"
            )

        da = da.transpose(TIME_DIM, Y_DIM, X_DIM)
        widget = viz.show_cube_lexcube(da, **kwargs)
        display(widget)

        # return original object so the pipe chain can continue
        return obj

    return _op


def extract(
    da: xr.DataArray | VirtualCube | None = None,
    *,
    fired_event: FireEventDaily,
    date_col: str = "date",
    n_ring_samples: int = 100,
    n_theta: int = 96,
):
    """
    Verb: attach fire time-hull + climate summary (and a vase-like hull)
    to a climate cube.

    Typical usage (v1)
    ------------------
    >>> import cubedynamics as cd
    >>> from cubedynamics import pipe, verbs as v
    >>>
    >>> clim = cd.gridmet(
    ...     lat=43.11,
    ...     lon=-122.74,
    ...     start="2002-07-01",
    ...     end="2002-09-15",
    ...     variable="tmmx",
    ... )
    >>> fired_evt = cd.fired_event(event_id=21281)
    >>>
    >>> cube = pipe(clim) | v.extract(fired_event=fired_evt)

    After this call, the underlying DataArray will have:
        da.attrs["fire_time_hull"]        = TimeHull(...)
        da.attrs["fire_climate_summary"]  = HullClimateSummary(...)
        da.attrs["vase"]                  = Vase(...)

    and the verb will return the same type it received (DataArray or VirtualCube).
    """

    def _op(value: xr.DataArray | VirtualCube):
        base_da, original_obj = _unwrap_dataarray(value)

        hull: TimeHull = compute_time_hull_geometry(
            fired_event,
            n_ring_samples=n_ring_samples,
            n_theta=n_theta,
        )

        summary: HullClimateSummary = build_inside_outside_climate_samples(
            fired_event,
            base_da,
            date_col=date_col,
        )

        vase_obj = time_hull_to_vase(hull)

        base_da.attrs["fire_time_hull"] = hull
        base_da.attrs["fire_climate_summary"] = summary
        base_da.attrs["vase"] = vase_obj

        return original_obj

    if da is None:
        return Verb(_op)
    return _op(da)


__all__ = [
    "anomaly",
    "apply",
    "mean",
    "month_filter",
    "flatten_space",
    "flatten_cube",
    "rolling_tail_dep_vs_center",
    "variance",
    "correlation_cube",
    "to_netcdf",
    "zscore",
    "ndvi_from_s2",
    "landsat8_mpc",
    "landsat_vis_ndvi",
    "landsat_ndvi_plot",
    "show_cube_lexcube",
    "fit_model",
    "plot",
    "plot_mean",
    "extract",
    "tubes",
    "vase",
    "vase_demo",
    "vase_extract",
    "vase_mask",
]
