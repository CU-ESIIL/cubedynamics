"""Pipeable cube operations."""

from .transforms import anomaly, month_filter
from .stats import variance, correlation_cube
from .io import to_netcdf

__all__ = [
    "anomaly",
    "month_filter",
    "variance",
    "correlation_cube",
    "to_netcdf",
]
