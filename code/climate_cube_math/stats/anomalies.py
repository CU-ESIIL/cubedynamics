"""Anomaly and z-score utilities."""

from __future__ import annotations

import numpy as np
import xarray as xr

from ..config import STD_EPS


def zscore_over_time(
    da: xr.DataArray,
    dim: str = "time",
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
