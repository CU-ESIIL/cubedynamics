"""Statistical cube verbs with consistent cube->cube semantics."""

from __future__ import annotations

import re
from typing import Any, Hashable, Iterable

import numpy as np
import xarray as xr

from ..config import STD_EPS
from ..stats.spatial_units import (
    aoi_signature as _aoi_signature,
    block_signature as _block_signature,
    collect_blocks as _collect_blocks,
    compare_aoi_signatures as _compare_aoi_signatures,
    compare_blocks as _compare_blocks,
)
from ..stats.tails import rolling_tail_dep_vs_center as _rolling_tail_dep_vs_center
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


def _resolve_over(
    dim: Hashable | Iterable[Hashable],
    over: Hashable | Iterable[Hashable] | None,
) -> Hashable | Iterable[Hashable]:
    """Resolve the readable ``over=`` spelling without breaking ``dim=``."""

    if over is None:
        return dim
    if dim != "time" and dim != over:
        raise ValueError("Use either dim= or over=, not conflicting values for both.")
    return over


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


def _dimension_names(dim: Hashable | Iterable[Hashable]) -> tuple[str, ...]:
    """Return stable string names for one or more reduction dimensions."""

    if isinstance(dim, set):
        return tuple(sorted(str(name) for name in dim))
    if isinstance(dim, (list, tuple)):
        return tuple(str(name) for name in dim)
    return (str(dim),)


def _variance_units(units: object) -> str | None:
    """Return a conservative squared spelling for one physical unit string."""

    if units is None:
        return None
    text = str(units).strip()
    if not text:
        return None
    normalized = text.casefold()
    if normalized in {"1", "dimensionless", "unitless"}:
        return "1"
    if normalized in {"unknown", "n/a", "na", "none", "unspecified"}:
        return text
    if re.fullmatch(r"[A-Za-zµμ°%]+", text):
        return f"{text}^2"
    return f"({text})^2"


def _annotate_variance_units(attrs: dict[str, Any]) -> None:
    """Update both physical and semantic units without inventing missing units."""

    source_units = attrs.get("semantic_units") or attrs.get("units")
    squared = _variance_units(source_units)
    if squared is None:
        attrs.pop("semantic_units", None)
        attrs.pop("units", None)
        return
    attrs["units"] = squared
    attrs["semantic_units"] = squared


def _annotate_summary(
    original: xr.Dataset | xr.DataArray,
    reduced: xr.Dataset | xr.DataArray,
    *,
    operation: str,
    dim: Hashable | Iterable[Hashable],
) -> xr.Dataset | xr.DataArray:
    """Replace inherited state labels with truthful reduction semantics."""

    original_attrs = dict(original.attrs)
    original_name = (
        original_attrs.get("semantic_name")
        or original_attrs.get("state_name")
        or getattr(original, "name", None)
        or "values"
    )
    attrs = dict(reduced.attrs)
    for key in (
        "analysis",
        "state_name",
        "semantic_name",
        "semantic_kind",
        "semantic_category",
        "semantic_units",
    ):
        attrs.pop(key, None)
    attrs.update(
        {
            "analysis": "reduction_summary",
            "semantic_name": f"{operation} of {original_name}",
            "semantic_kind": "summary",
            "semantic_category": "summary",
            "summary_operation": operation,
            "summary_dimensions": ",".join(_dimension_names(dim)),
        }
    )

    if operation == "variance":
        _annotate_variance_units(attrs)
        if isinstance(reduced, xr.Dataset):
            for name in reduced.data_vars:
                variable_attrs = dict(reduced[name].attrs)
                _annotate_variance_units(variable_attrs)
                reduced[name].attrs = variable_attrs

    is_condition = (
        original_attrs.get("semantic_kind") == "condition"
        or original_attrs.get("analysis") == "state_cube"
        or (isinstance(original, xr.DataArray) and original.dtype == bool)
    )
    if is_condition and operation == "mean":
        if isinstance(reduced, xr.DataArray):
            attrs.update({"semantic_units": "proportion", "units": "1"})
        elif "state" in reduced.data_vars:
            # The summary Dataset contains a unitless state proportion plus
            # magnitude/threshold variables in source units, so one global
            # units label would be misleading.
            attrs.pop("units", None)
            state_attrs = dict(reduced["state"].attrs)
            state_attrs.update(
                {
                    "long_name": f"Proportion of {original_name}",
                    "semantic_name": f"proportion of {original_name}",
                    "semantic_kind": "summary",
                    "semantic_category": "condition_frequency",
                    "semantic_units": "proportion",
                    "units": "1",
                }
            )
            reduced["state"].attrs = state_attrs
            reduced = xr.Dataset({"state": reduced["state"]})
            attrs.update(
                {
                    "condition_summary": "occurrence_proportion",
                    "reduced_condition_fields": "state",
                    "excluded_condition_fields": "magnitude,threshold",
                }
            )

    reduced.attrs = attrs
    return reduced


def _annotate_centered_transform(
    original: xr.Dataset | xr.DataArray,
    transformed: xr.Dataset | xr.DataArray,
    *,
    operation: str,
) -> xr.Dataset | xr.DataArray:
    """Describe an anomaly or z-score without evaluating its array values."""

    source_attrs = dict(original.attrs)
    source_name = (
        source_attrs.get("semantic_name")
        or source_attrs.get("scientific_noun")
        or getattr(original, "name", None)
        or "values"
    )
    attrs = dict(source_attrs)
    attrs.update(
        {
            "analysis": operation,
            "semantic_name": f"{operation} of {source_name}",
            "semantic_kind": "continuous_field",
            "semantic_category": "centered_transform",
            "transform_operation": operation,
        }
    )
    if operation == "zscore":
        attrs.update({"units": "1", "semantic_units": "standard deviations"})

    transformed.attrs = attrs
    if isinstance(transformed, xr.Dataset):
        for name in transformed.data_vars:
            variable_source = original[name] if name in original.data_vars else original
            variable_attrs = dict(getattr(variable_source, "attrs", {}))
            variable_name = (
                variable_attrs.get("semantic_name")
                or variable_attrs.get("scientific_noun")
                or name
            )
            variable_attrs.update(
                {
                    "analysis": operation,
                    "semantic_name": f"{operation} of {variable_name}",
                    "semantic_kind": "continuous_field",
                    "semantic_category": "centered_transform",
                    "transform_operation": operation,
                }
            )
            if operation == "zscore":
                variable_attrs.update(
                    {"units": "1", "semantic_units": "standard deviations"}
                )
            transformed[name].attrs = variable_attrs
    return transformed


def month_filter(months: Iterable[int]):
    """Keep the requested calendar months on a datetime-like time coordinate.

    Parameters
    ----------
    months : iterable of int
        Calendar months to retain (1-12). Empty selections return an empty
        time axis. The iterable is captured once so the stage is reusable.

    Returns
    -------
    callable
        Stage accepting an xarray Dataset or DataArray. Values remain lazy
        for Dask-backed inputs; coordinates determine the selected rows.

    Raises
    ------
    ValueError
        If the input lacks a datetime-like ``time`` coordinate.

    Notes
    -----
    Preserves the historical integer coercion and selection behavior. This
    is the supported implementation; the old ops import forwards here.
    """

    months = tuple(int(month) for month in months)

    def _op(cube: xr.DataArray | xr.Dataset):
        if "time" not in cube.coords:
            raise ValueError("month_filter requires a 'time' coordinate.")
        try:
            month_values = cube["time"].dt.month
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("month_filter: 'time' coordinate must be datetime-like.") from exc
        result = cube.where(month_values.isin(months), drop=True)
        result.attrs.update(cube.attrs)
        result.attrs["selected_calendar_months"] = ",".join(str(month) for month in months)
        return result

    return _op


def mean(
    dim: str = "time",
    *,
    over: Hashable | Iterable[Hashable] | None = None,
    keep_dim: bool = True,
    skipna: bool | None = True,
):
    """Summary
    Compute the mean along a dimension while keeping cubes pipe-ready.

    Grammar contract
    Reducer verb (cube → cube with reduced dim). Direct-call and pipe-ready.

    Parameters
    dim : str, default "time"
        Dimension to reduce.
    over : hashable or iterable of hashable, optional
        Readable alias for ``dim``. Existing ``dim=`` calls remain supported.
    keep_dim : bool, default True
        Preserve the reduced dimension with length 1 to keep a (time, y, x)
        layout when applicable.
    skipna : bool | None, default True
        Whether to ignore NaN values during reduction.

    Returns
    xr.Dataset | xr.DataArray | VirtualCube
        Reduced cube with source/provenance attrs preserved and semantic attrs
        normalized to describe a summary; VirtualCube inputs stay lazy.

    Notes
    Streaming VirtualCube inputs are processed tile-by-tile without forcing a
    full load. Dask-backed arrays remain lazy. When ``keep_dim`` is False the
    reduced dimension is dropped. A mean of a condition Dataset returns a
    summary Dataset containing only its reduced ``state`` proportion. The
    condition definition remains in Dataset metadata; auxiliary magnitude and
    threshold arrays are not averaged implicitly.

    Examples
    --------
    >>> import xarray as xr
    >>> import numpy as np
    >>> from cubedynamics import pipe, verbs as v
    >>> da = xr.DataArray(np.random.rand(3, 2, 2), dims=("time", "y", "x"))
    >>> smoothed = pipe(da) | v.mean()
    >>> smoothed.unwrap().dims
    ('time', 'y', 'x')

    See Also
    --------
    cubedynamics.verbs.stats.variance, cubedynamics.verbs.stats.anomaly
    """

    dim = _resolve_over(dim, over)

    def _op(obj: xr.Dataset | xr.DataArray | VirtualCube) -> xr.Dataset | xr.DataArray:
        if isinstance(obj, VirtualCube):
            if isinstance(dim, (tuple, list)) and set(dim) == {"y", "x"}:
                return _mean_virtual_space(obj)
            if dim == "time":
                return _mean_virtual_time(obj, keep_dim=keep_dim)
            raise NotImplementedError(f"Streaming mean for dim={dim} not implemented")

        _ensure_dim(obj, dim)
        reduced = obj.mean(dim=dim, skipna=skipna, keep_attrs=True)
        reduced = _expand_dim(reduced, dim, keep_dim)
        return _annotate_summary(obj, reduced, operation="mean", dim=dim)

    return _op


def variance(
    dim: str = "time",
    *,
    over: Hashable | Iterable[Hashable] | None = None,
    keep_dim: bool = True,
    skipna: bool | None = True,
):
    """Return a variance reducer along ``dim`` with optional dimension retention."""

    dim = _resolve_over(dim, over)

    def _variance_xarray(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)
        reduced = obj.var(dim=dim, skipna=skipna, keep_attrs=True)
        reduced = _expand_dim(reduced, dim, keep_dim)
        return _annotate_summary(obj, reduced, operation="variance", dim=dim)

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


def _mean_virtual_time(vc: VirtualCube, *, keep_dim: bool) -> xr.DataArray:
    total = None
    count = None
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

            if total is None:
                total = np.zeros_like(x, dtype=float)
                count = np.zeros_like(x, dtype=np.int64)

            total = total + np.where(mask, x, 0.0)
            count = count + mask.astype(np.int64)

    if total is None or count is None:
        raise ValueError("VirtualCube produced no tiles during mean computation")

    mean_vals = total / np.maximum(count, 1)
    mean_da = xr.DataArray(mean_vals, coords={}, dims=("y", "x"), name="mean")
    if y_coords is not None:
        mean_da = mean_da.assign_coords(y=y_coords)
    if x_coords is not None:
        mean_da = mean_da.assign_coords(x=x_coords)

    return _expand_dim(mean_da, "time", keep_dim)


def _variance_virtual_space(vc: VirtualCube) -> xr.DataArray:
    stats: dict[Any, tuple[float, float, int]] = {}

    for cube in vc.iter_spatial_tiles():
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


def _mean_virtual_space(vc: VirtualCube) -> xr.DataArray:
    totals: dict[Any, float] = {}
    counts: dict[Any, int] = {}

    for cube in vc.iter_spatial_tiles():
        ordered = cube.transpose(*[d for d in vc.dims if d in cube.dims])
        times = ordered["time"].values
        data = np.asarray(ordered.data)

        for idx, tval in enumerate(times):
            flat = np.asarray(data[idx, ...]).ravel()
            mask = np.isfinite(flat)
            vals = flat[mask]
            totals[tval] = totals.get(tval, 0.0) + float(vals.sum())
            counts[tval] = counts.get(tval, 0) + int(mask.sum())

    times_sorted = sorted(totals.keys())
    means = [totals[t] / max(counts.get(t, 1), 1) for t in times_sorted]

    return xr.DataArray(
        np.array(means),
        coords={"time": times_sorted},
        dims=("time",),
        name="mean",
    )


def anomaly(
    dim: str = "time",
    *,
    over: Hashable | Iterable[Hashable] | None = None,
    keep_dim: bool = True,
):
    """Return a pipe verb that subtracts the mean over ``dim``.

    ``keep_dim`` is accepted for API symmetry; anomalies always preserve the
    input shape so Lexcube visualization remains valid. Result metadata names
    the anomaly transform, retains source identity and physical units, and
    describes the result as a continuous field.
    """

    dim = _resolve_over(dim, over)

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
        _ensure_dim(obj, dim)
        mean_op = obj.mean(dim=dim, skipna=True, keep_attrs=True)
        mean_op = _broadcast_like(obj, mean_op)
        result = obj - mean_op
        return _annotate_centered_transform(obj, result, operation="anomaly")

    return _op


def zscore(
    dim: str = "time",
    *,
    over: Hashable | Iterable[Hashable] | None = None,
    keep_dim: bool = True,
    std_eps: float = STD_EPS,
    skipna: bool | None = True,
):
    """Return a standardized anomaly verb (z-score) along ``dim``.

    ``keep_dim`` is included for API symmetry; z-scores preserve the incoming
    cube shape regardless of the flag. ``std_eps`` prevents division-by-zero for
    flat series. Result metadata retains source identity while recording
    physical units as ``1`` and semantic units as standard deviations.
    """

    dim = _resolve_over(dim, over)

    def _op(obj: xr.Dataset | xr.DataArray | VirtualCube) -> xr.Dataset | xr.DataArray:
        if isinstance(obj, VirtualCube):
            if dim != "time":
                raise NotImplementedError("Streaming z-score is implemented for dim='time' only")
            mean_da = _mean_virtual_time(obj, keep_dim=False)
            var_da = _variance_virtual_time(obj, keep_dim=False)
            std_da = xr.apply_ufunc(np.sqrt, var_da)
            std_safe = std_da.where(std_da > std_eps, np.nan)

            tiles = []
            for tile in obj.iter_tiles():
                mean_broadcast = mean_da.broadcast_like(tile)
                std_broadcast = std_safe.broadcast_like(tile)
                z = (tile - mean_broadcast) / std_broadcast
                name = tile.name or "var"
                tiles.append(z.rename(f"{name}_zscore"))

            combined = xr.combine_by_coords(tiles)
            if isinstance(combined, xr.Dataset) and len(combined.data_vars) == 1:
                only_var = next(iter(combined.data_vars))
                result = combined[only_var]
            else:
                result = combined
            result.attrs.update(
                {
                    "analysis": "zscore",
                    "semantic_name": "zscore of streamed values",
                    "semantic_kind": "continuous_field",
                    "semantic_category": "centered_transform",
                    "transform_operation": "zscore",
                    "units": "1",
                    "semantic_units": "standard deviations",
                }
            )
            return result

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
        return _annotate_centered_transform(obj, z, operation="zscore")

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

        source_units = getattr(obj, "attrs", {}).get("semantic_units") or getattr(obj, "attrs", {}).get("units")
        squared_units = _variance_units(source_units)
        attrs = dict(getattr(result, "attrs", {}))
        attrs.update(
            {
                "analysis": "rolling_upper_tail_variance_contrast",
                "metric_definition": "upper-tail variance minus full-window variance",
                "interpretation": "negative values mean upper-tail variance is smaller than full-window variance",
                "valid_range": "unbounded real numbers",
                "window_observations": window,
                "minimum_observations": min_periods,
                "tail_quantile": tail_quantile,
                "output_time_semantics": "input coordinate labels the inclusive rolling-window end",
            }
        )
        if squared_units:
            attrs.update({"units": squared_units, "semantic_units": squared_units})
        result.attrs = attrs

        return result

    return _op


def rolling_median_split_synchrony(
    *,
    window_days: int = 90,
    min_t: int = 5,
    split_quantile: float = 0.5,
    time_dim: str = "time",
    output_stride: int = 1,
    output_times: Iterable[object] | None = None,
    lower_var: str | None = None,
    upper_var: str | None = None,
):
    """Compute rolling synchrony in lower and upper per-series sets.

    Grammar contract
    ----------------
    Statistical verb returning a three-variable :class:`xarray.Dataset`. For a
    DataArray, both sets come from the same variable. For a multi-variable
    Dataset, ``lower_var`` and ``upper_var`` select the variables used for the
    lower and upper sets, respectively.

    With ``split_quantile=0.5``, the lower set contains dates when a pixel and
    its cube's center pixel are both at or below their rolling medians. The
    upper set contains dates when both are above their rolling medians.
    ``output_stride`` controls how many input timestamps to advance between
    outputs; use 30 for approximately monthly results from daily climate data.
    ``output_times`` can be used by streaming jobs to request a bounded batch of
    explicit rolling window end timestamps.

    Examples
    --------
    >>> result = pipe(prism_temperature) | v.rolling_median_split_synchrony(
    ...     lower_var="tmin", upper_var="tmax", window_days=90
    ... )
    """

    if (lower_var is None) != (upper_var is None):
        raise ValueError("lower_var and upper_var must be provided together")

    target_output_times = tuple(output_times) if output_times is not None else None

    def _select_inputs(
        obj: xr.Dataset | xr.DataArray,
    ) -> tuple[xr.DataArray, xr.DataArray, str, str]:
        if isinstance(obj, xr.DataArray):
            if lower_var is not None or upper_var is not None:
                raise ValueError(
                    "lower_var and upper_var are only valid for Dataset inputs"
                )
            name = obj.name or "value"
            return obj, obj, name, name

        if lower_var is None:
            if len(obj.data_vars) != 1:
                raise ValueError(
                    "Dataset inputs with multiple variables require lower_var and upper_var"
                )
            name = next(iter(obj.data_vars))
            return obj[name], obj[name], name, name

        missing = [name for name in (lower_var, upper_var) if name not in obj.data_vars]
        if missing:
            raise ValueError(
                f"Variables {missing!r} not found in Dataset variables: "
                f"{list(obj.data_vars)!r}"
            )
        return obj[lower_var], obj[upper_var], lower_var, upper_var

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset:
        if isinstance(obj, VirtualCube):
            raise NotImplementedError(
                "rolling_median_split_synchrony requires a DataArray or Dataset; "
                "iterate VirtualCube spatial tiles before applying the verb"
            )
        if not isinstance(obj, (xr.DataArray, xr.Dataset)):
            raise TypeError(
                "rolling_median_split_synchrony requires an xarray DataArray or Dataset"
            )

        lower_cube, upper_cube, lower_name, upper_name = _select_inputs(obj)
        if lower_cube.dims != upper_cube.dims:
            raise ValueError(
                f"Selected variables must have matching dims; got "
                f"{lower_cube.dims!r} and {upper_cube.dims!r}"
            )

        bottom, same_top, same_diff = _rolling_tail_dep_vs_center(
            lower_cube,
            window_days=window_days,
            min_t=min_t,
            b=split_quantile,
            time_dim=time_dim,
            output_stride=output_stride,
            output_times=target_output_times,
        )
        if lower_name == upper_name:
            top = same_top
            difference = same_diff
        else:
            _, top, _ = _rolling_tail_dep_vs_center(
                upper_cube,
                window_days=window_days,
                min_t=min_t,
                b=split_quantile,
                time_dim=time_dim,
                output_stride=output_stride,
                output_times=target_output_times,
            )
            bottom, top = xr.align(bottom, top, join="exact")
            difference = bottom - top

        bottom = bottom.rename("bottom_synchrony")
        top = top.rename("top_synchrony")
        difference = difference.rename("bottom_minus_top")
        bottom.attrs.update(
            {
                "long_name": "Below-quantile Spearman synchrony vs center",
                "source_variable": lower_name,
                "units": "1",
                "description": "Spearman correlation for dates where the pixel and center reference are both in their lower rolling-quantile sets",
                "valid_range": "-1 to 1",
            }
        )
        top.attrs.update(
            {
                "long_name": "Above-quantile Spearman synchrony vs center",
                "source_variable": upper_name,
                "units": "1",
                "description": "Spearman correlation for dates where the pixel and center reference are both in their upper rolling-quantile sets",
                "valid_range": "-1 to 1",
            }
        )
        difference.attrs.update(
            {
                "long_name": "Bottom minus top Spearman synchrony",
                "bottom_variable": lower_name,
                "top_variable": upper_name,
                "valid_range": (-2.0, 2.0),
                "units": "1",
                "description": "Lower-set synchrony minus upper-set synchrony",
            }
        )
        result = xr.Dataset(
            {
                "bottom_synchrony": bottom,
                "top_synchrony": top,
                "bottom_minus_top": difference,
            }
        )
        result.attrs.update(
            {
                "analysis": "rolling_median_split_synchrony",
                "window_days": window_days,
                "min_time_points_per_set": min_t,
                "split_quantile": split_quantile,
                "reference": "center_pixel",
                "reference_pixel_y_index": int(bottom.attrs.get("reference_pixel_y", -1)),
                "reference_pixel_x_index": int(bottom.attrs.get("reference_pixel_x", -1)),
                "output_stride": output_stride,
                "split_definition": (
                    "each pixel and the center reference use their own rolling-window "
                    f"quantiles; lower uses <= {split_quantile}, upper uses > {1.0 - split_quantile}"
                ),
                "window_definition": f"inclusive trailing {window_days}-day coordinate-label window",
                "output_time_semantics": "time_window_end is the inclusive end label of each evaluated rolling window",
                "edge_behavior": (
                    "windows with fewer than min_t total or tail observations are omitted or NaN; "
                    "output_stride selects evaluated end labels"
                ),
                "semantic_name": "rolling median-split synchrony",
                "semantic_kind": "relationship",
                "semantic_units": "1",
            }
        )
        result["time_window_end"].attrs.update(
            {"long_name": "Inclusive rolling-window end coordinate label"}
        )
        return result

    return _op


def aoi_signature(
    *,
    unit_id: str,
    variables: Iterable[str] | None = None,
    time_dim: str | None = None,
    spatial_dims: Iterable[str] | None = None,
    reducer: str = "median",
    unit_dim: str = "unit",
    skipna: bool = True,
):
    """Summarize an AOI cube into a named spatial-unit time signature.

    Grammar contract
    ----------------
    Reducer verb that keeps time and adds a length-one ``unit`` dimension. This
    is the first step toward pairwise and many-unit spatial meta-analysis.

    Examples
    --------
    >>> signature = pipe(sync_cube) | v.aoi_signature(unit_id="boulder")
    """

    resolved_spatial_dims = tuple(spatial_dims) if spatial_dims is not None else None

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset:
        if isinstance(obj, VirtualCube):
            raise NotImplementedError(
                "aoi_signature requires a materialized DataArray or Dataset; "
                "summarize each VirtualCube tile before building signatures"
            )
        return _aoi_signature(
            obj,
            unit_id=unit_id,
            variables=variables,
            time_dim=time_dim,
            spatial_dims=resolved_spatial_dims,
            reducer=reducer,
            unit_dim=unit_dim,
            skipna=skipna,
        )

    return _op


def compare_aoi_signature(
    other: xr.Dataset | xr.DataArray,
    *,
    variables: Iterable[str] | None = None,
    time_dim: str | None = None,
    unit_dim: str = "unit",
    join: str = "inner",
):
    """Compare one AOI signature with another over shared time."""

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset:
        return _compare_aoi_signatures(
            obj,
            other,
            variables=variables,
            time_dim=time_dim,
            unit_dim=unit_dim,
            join=join,
        )

    return _op


def block_signature(
    *,
    block_id: str,
    variables: Iterable[str] | None = None,
    time_dim: str | None = None,
    spatial_dims: Iterable[str] | None = None,
    reducer: str = "median",
    block_dim: str = "block",
    skipna: bool = True,
):
    """Summarize a local cube into a named block time signature."""

    resolved_spatial_dims = tuple(spatial_dims) if spatial_dims is not None else None

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset:
        if isinstance(obj, VirtualCube):
            raise NotImplementedError(
                "block_signature requires a materialized DataArray or Dataset; "
                "summarize each VirtualCube tile before building block signatures"
            )
        return _block_signature(
            obj,
            block_id=block_id,
            variables=variables,
            time_dim=time_dim,
            spatial_dims=resolved_spatial_dims,
            reducer=reducer,
            block_dim=block_dim,
            skipna=skipna,
        )

    return _op


def collect_blocks(
    *others: xr.Dataset | xr.DataArray,
    block_dim: str = "block",
    join: str = "outer",
):
    """Collect block signatures into one block collection."""

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset:
        return _collect_blocks(obj, *others, block_dim=block_dim, join=join)

    return _op


def compare_blocks(
    *,
    variables: Iterable[str] | None = None,
    time_dim: str | None = None,
    block_dim: str = "block",
    join: str = "inner",
):
    """Compare all unique pairs in a block collection."""

    def _op(obj: xr.Dataset | xr.DataArray) -> xr.Dataset:
        return _compare_blocks(
            obj,
            variables=variables,
            time_dim=time_dim,
            block_dim=block_dim,
            join=join,
        )

    return _op


__all__ = [
    "aoi_signature",
    "anomaly",
    "block_signature",
    "collect_blocks",
    "compare_blocks",
    "compare_aoi_signature",
    "mean",
    "month_filter",
    "rolling_median_split_synchrony",
    "rolling_tail_dep_vs_center",
    "variance",
    "zscore",
]
