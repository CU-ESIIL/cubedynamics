"""Statistical cube verbs with consistent cube->cube semantics."""

from __future__ import annotations

from typing import Any, Hashable, Iterable

import numpy as np
import xarray as xr

from ..config import STD_EPS
from ..streaming import VirtualCube


def _ensure_dim(obj: xr.Dataset | xr.DataArray, dim: Hashable | Iterable[Hashable]) -> None:
    if isinstance(dim, (list, tuple, set)):
        missing = [d for d in dim if d not in obj.dims]
        if missing:
            raise ValueError(
                f"Dimensions {missing!r} not found in object dims: {tuple(obj.dims)}"
            )
        return

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
    if isinstance(dim, (list, tuple, set)):
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

    def _variance_xarray(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)
        reduced = obj.var(dim=dim, skipna=skipna, keep_attrs=True)
        return _expand_dim(reduced, dim, keep_dim)

    def _variance_virtual_cube(vc: VirtualCube):  # type: ignore[return-value]
        if isinstance(dim, (tuple, list)) and set(dim) == {"y", "x"}:
            return _variance_virtual_space(vc)
        if dim == "time":
            return _variance_virtual_time(vc, keep_dim=keep_dim)
        raise NotImplementedError(f"Streaming variance for dim={dim} not implemented")

    def _op(obj: xr.Dataset | xr.DataArray | VirtualCube):  # type: ignore[type-arg]
        if isinstance(obj, VirtualCube):
            return _variance_virtual_cube(obj)
        return _variance_xarray(obj)

    return _op


def _variance_virtual_time(vc: VirtualCube, *, keep_dim: bool) -> xr.DataArray:
    mean = None
    m2 = None
    n = None
    y_coords = None
    x_coords = None

    for cube in vc.iter_time_tiles():
        ordered = cube.transpose(*[d for d in vc.dims if d in cube.dims])
        data = np.asarray(ordered.data)
        if "y" in ordered.coords:
            y_coords = ordered.coords.get("y")
        if "x" in ordered.coords:
            x_coords = ordered.coords.get("x")

        for idx in range(data.shape[0]):
            x = np.asarray(data[idx, ...])
            mask = np.isfinite(x)

            if mean is None:
                mean = np.zeros_like(x, dtype=float)
                m2 = np.zeros_like(x, dtype=float)
                n = np.zeros_like(x, dtype=np.int64)

            n_new = n + mask.astype(np.int64)
            delta = x - mean
            mean = mean + np.where(mask, delta / np.maximum(n_new, 1), 0.0)
            delta2 = x - mean
            m2 = m2 + np.where(mask, delta * delta2, 0.0)
            n = n_new

    if mean is None or m2 is None or n is None:
        raise ValueError("VirtualCube produced no tiles during variance computation")

    var = m2 / np.maximum(n, 1)
    var_da = xr.DataArray(var, coords={}, dims=("y", "x"), name="variance")
    if y_coords is not None:
        var_da = var_da.assign_coords(y=y_coords)
    if x_coords is not None:
        var_da = var_da.assign_coords(x=x_coords)

    return _expand_dim(var_da, "time", keep_dim)


def _variance_virtual_space(vc: VirtualCube) -> xr.DataArray:
    stats: dict[Any, tuple[float, float, int]] = {}

    for cube in vc.iter_tiles():
        ordered = cube.transpose(*[d for d in vc.dims if d in cube.dims])
        times = ordered["time"].values
        data = np.asarray(ordered.data)

        for idx, tval in enumerate(times):
            flat = np.asarray(data[idx, ...]).ravel()
            mask = np.isfinite(flat)
            vals = flat[mask]
            if vals.size == 0:
                continue

            mean, m2, n = stats.get(tval, (0.0, 0.0, 0))
            for v in vals:
                n_new = n + 1
                delta = v - mean
                mean = mean + delta / n_new
                delta2 = v - mean
                m2 = m2 + delta * delta2
                n = n_new

            stats[tval] = (mean, m2, n)

    times_sorted = sorted(stats.keys())
    values = []
    for tval in times_sorted:
        mean, m2, n = stats[tval]
        values.append(m2 / max(n, 1))

    return xr.DataArray(
        np.array(values),
        coords={"time": times_sorted},
        dims=("time",),
        name="variance",
    )


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
