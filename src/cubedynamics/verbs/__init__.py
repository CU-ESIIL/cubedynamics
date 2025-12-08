"""Namespace exposing pipe-friendly cube verbs."""

from __future__ import annotations

import cubedynamics.viz as viz
import xarray as xr
from IPython.display import display

from ..config import TIME_DIM, X_DIM, Y_DIM
from ..ops.io import to_netcdf
from ..ops.ndvi import ndvi_from_s2
from ..ops.stats import correlation_cube
from ..ops.transforms import month_filter
from .custom import apply
from .flatten import flatten_cube, flatten_space
from .models import fit_model
from .plot import plot
from .plot_mean import plot_mean
from .vase import vase, vase_extract, vase_mask
from .stats import anomaly, mean, rolling_tail_dep_vs_center, variance, zscore


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
    "vase",
    "vase_extract",
    "vase_mask",
]
