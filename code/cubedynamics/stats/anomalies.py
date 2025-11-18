"""Anomaly and z-score utilities."""

from __future__ import annotations

import numpy as np
import xarray as xr
from typing import Hashable

from ..config import STD_EPS, TIME_DIM


def zscore_over_time(
    da: xr.DataArray,
    dim: Hashable = TIME_DIM,
    std_eps: float | None = None,
) -> xr.DataArray:
    """Compute per-location z-scores over a time dimension."""

    eps = STD_EPS if std_eps is None else std_eps
    mean = da.mean(dim=dim, skipna=True)
    std = da.std(dim=dim, skipna=True)
    valid_std = (std > eps).broadcast_like(da)
    z = xr.where(valid_std, (da - mean) / std, np.nan)
    # Keep the original dimension ordering so callers don't have to
    # defensively transpose results. xarray broadcasting can sometimes
    # reorder axes depending on the order of intermediate operations,
    # so normalize here explicitly.
    z = z.transpose(*da.dims)
    z = z.astype("float32")
    z.name = f"{da.name}_z" if da.name else "zscore"
    z.attrs = {
        **da.attrs,
        "long_name": f"Z-score of {da.name or 'variable'}",
        "definition": f"(x - mean_{dim}) / std_{dim}",
    }
    return z


def temporal_anomaly(
    da: xr.DataArray,
    dim: Hashable = TIME_DIM,
    baseline_slice: slice | None = None,
) -> xr.DataArray:
    """Compute anomalies relative to a baseline mean over a time-like dimension."""

    da_baseline = da if baseline_slice is None else da.sel({dim: baseline_slice})
    baseline_mean = da_baseline.mean(dim=dim, skipna=True)
    anomalies = da - baseline_mean
    baseline_desc = "full" if baseline_slice is None else str(baseline_slice)
    anomalies.attrs = {
        **da.attrs,
        "long_name": f"{da.name or 'variable'} anomaly",
        "baseline_period": baseline_desc,
    }
    return anomalies


def temporal_difference(
    da: xr.DataArray,
    lag: int = 1,
    dim: Hashable = TIME_DIM,
) -> xr.DataArray:
    """Compute lagged differences along a time-like dimension."""

    lagged = da.shift({dim: lag})
    diff = da - lagged
    diff.attrs = {
        **da.attrs,
        "long_name": f"{da.name or 'variable'} difference (lag={lag})",
    }
    return diff


def rolling_mean(
    da: xr.DataArray,
    window: int,
    dim: Hashable = TIME_DIM,
    min_periods: int | None = None,
    center: bool = False,
) -> xr.DataArray:
    """Compute a simple rolling mean along a time-like dimension."""

    min_periods = window if min_periods is None else min_periods
    rolled = da.rolling({dim: window}, min_periods=min_periods, center=center).mean()
    rolled.attrs = {
        **da.attrs,
        "long_name": f"{da.name or 'variable'} rolling mean (window={window})",
    }
    return rolled
