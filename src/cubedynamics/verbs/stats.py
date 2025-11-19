"""Statistical cube verbs with consistent cube->cube semantics."""

from __future__ import annotations

from typing import Hashable

import numpy as np
import xarray as xr

from ..config import STD_EPS


def _ensure_dim(obj: xr.Dataset | xr.DataArray, dim: Hashable) -> None:
    if dim not in obj.dims:
        raise ValueError(f"Dimension {dim!r} not found in object dims: {tuple(obj.dims)}")


def _expand_dim(
    reduced: xr.Dataset | xr.DataArray,
    dim: Hashable,
    keep_dim: bool,
) -> xr.Dataset | xr.DataArray:
    """Return ``reduced`` with ``dim`` added back as a length-1 dimension."""

    if not keep_dim:
        return reduced
    if dim in reduced.dims:
        return reduced
    return reduced.expand_dims(dim)


def _broadcast_like(
    obj: xr.Dataset | xr.DataArray,
    stat: xr.Dataset | xr.DataArray,
) -> xr.Dataset | xr.DataArray:
    """Broadcast ``stat`` so it can be combined elementwise with ``obj``."""

    return stat.broadcast_like(obj)


def mean(dim: str = "time", *, keep_dim: bool = True, skipna: bool | None = True):
    """Return a pipe-ready reducer computing the mean along ``dim``.

    When ``keep_dim`` is True the reduced dimension is preserved with length 1 so
    that the resulting object keeps a (time, y, x) cube layout and remains
    Lexcube-ready.
    """

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)
        reduced = obj.mean(dim=dim, skipna=skipna, keep_attrs=True)
        return _expand_dim(reduced, dim, keep_dim)

    return _op


def variance(dim: str = "time", *, keep_dim: bool = True, skipna: bool | None = True):
    """Return a variance reducer along ``dim`` with optional dimension retention."""

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)
        reduced = obj.var(dim=dim, skipna=skipna, keep_attrs=True)
        return _expand_dim(reduced, dim, keep_dim)

    return _op


def anomaly(dim: str = "time", *, keep_dim: bool = True):
    """Return a pipe verb that subtracts the mean over ``dim``.

    ``keep_dim`` is accepted for API symmetry; anomalies always preserve the
    input shape so Lexcube visualization remains valid.
    """

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)
        mean_op = obj.mean(dim=dim, skipna=True, keep_attrs=True)
        mean_op = _broadcast_like(obj, mean_op)
        return obj - mean_op

    return _op


def zscore(
    dim: str = "time",
    *,
    keep_dim: bool = True,
    std_eps: float = STD_EPS,
    skipna: bool | None = True,
):
    """Return a standardized anomaly verb (z-score) along ``dim``.

    ``keep_dim`` is included for API symmetry; z-scores preserve the incoming
    cube shape regardless of the flag. ``std_eps`` prevents division-by-zero for
    flat series.
    """

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)
        mean_op = obj.mean(dim=dim, skipna=skipna, keep_attrs=True)
        std_op = obj.std(dim=dim, skipna=skipna, keep_attrs=True)
        mean_op = _broadcast_like(obj, mean_op)
        std_op = _broadcast_like(obj, std_op)
        std_safe = std_op.where(std_op > std_eps, np.nan)
        z = (obj - mean_op) / std_safe
        if isinstance(z, xr.DataArray):
            name = obj.name or "var"
            z = z.rename(f"{name}_zscore")
        return z

    return _op


def rolling_tail_dep_vs_center(
    window: int,
    *,
    dim: str = "time",
    min_periods: int = 5,
    tail_quantile: float = 0.8,
):
    """Return a rolling "tail dependence vs center" contrast along ``dim``.

    For each rolling window this computes the difference between variability in
    the upper tail (values above ``tail_quantile``) and variability across the
    full window. The verb preserves the original cube shape.

    Parameters
    ----------
    window : int
        Rolling window size in number of time steps.
    dim : str, optional
        Dimension to roll over (default: ``"time"``).
    min_periods : int, optional
        Minimum periods in window required to compute the statistic.
    tail_quantile : float, optional
        Quantile threshold defining the upper tail (default: ``0.8``).
    """

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)

        window_dim = f"{dim}_window"
        rolled = obj.rolling({dim: window}, min_periods=min_periods)
        constructed = rolled.construct(window_dim)

        counts = constructed.count(dim=window_dim)
        center_var = constructed.var(dim=window_dim, skipna=True, keep_attrs=True)

        q = constructed.quantile(tail_quantile, dim=window_dim)
        tail_vals = constructed.where(constructed >= q)
        tail_counts = tail_vals.count(dim=window_dim)
        tail_var = tail_vals.var(dim=window_dim, skipna=True, keep_attrs=True)

        result = tail_var - center_var
        valid = (counts >= min_periods) & (tail_counts > 0)
        result = result.where(valid)

        if isinstance(result, xr.DataArray) and obj.name:
            result = result.rename(f"{obj.name}_tail_dep_vs_center")

        return result

    return _op


__all__ = ["anomaly", "mean", "rolling_tail_dep_vs_center", "variance", "zscore"]
