"""Namespace exposing pipe-friendly cube verbs."""

from __future__ import annotations

from .. import viz
from ..ops.io import to_netcdf
from ..ops.ndvi import ndvi_from_s2
from ..ops.stats import correlation_cube, variance, zscore
from ..ops.transforms import anomaly, month_filter


def show_cube_lexcube(**kwargs):
    """Pipe verb that renders the current cube via Lexcube widgets."""

    def _op(da):
        viz.show_cube_lexcube(da, **kwargs)
        return da

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
