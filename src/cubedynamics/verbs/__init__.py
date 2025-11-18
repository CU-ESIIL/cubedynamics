"""Namespace exposing pipe-friendly cube verbs."""

from __future__ import annotations

import xarray as xr
from IPython.display import display

from .. import viz
from ..ops.io import to_netcdf
from ..ops.ndvi import ndvi_from_s2
from ..ops.stats import correlation_cube, variance, zscore
from ..ops.transforms import anomaly, month_filter


def show_cube_lexcube(**kwargs):
    """Pipe verb: render a Lexcube widget as a side-effect and return the cube.

    Example:
        jja = (
            pipe(cube)
            | v.month_filter([6, 7, 8])
            | v.show_cube_lexcube(cmap="RdBu_r")
        ).unwrap()
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

        widget = viz.show_cube_lexcube(da, **kwargs)
        display(widget)

        # return original object so the pipe chain can continue
        return obj

    return _op


__all__ = [
    "anomaly",
    "month_filter",
    "variance",
    "correlation_cube",
    "to_netcdf",
    "zscore",
    "ndvi_from_s2",
    "show_cube_lexcube",
]
