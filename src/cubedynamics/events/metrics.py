"""Bounded, scope-aware metrics for local events and regional episodes."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
import xarray as xr

from .schemas import EventResult


_ALIASES = {"count": "event_count"}
_SUPPORTED = {
    "event_count",
    "mean_duration",
    "median_duration",
    "max_duration",
    "event_days",
    "mean_severity",
    "max_severity",
    "mean_participating_cells",
    "max_participating_cells",
    "peak_footprint",
}


def event_metrics(
    events: EventResult,
    *,
    period: str = "year",
    metrics: Iterable[str] = ("event_count", "mean_duration", "max_duration"),
    date_field: str = "start",
) -> xr.Dataset:
    """Summarize an event catalog by an explicit calendar period."""

    if not isinstance(events, EventResult):
        raise TypeError("event_metrics requires an EventResult")
    if period not in {"year", "month", "all"}:
        raise ValueError("period must be 'year', 'month', or 'all'")
    requested = tuple(_ALIASES.get(name, name) for name in metrics)
    unknown = sorted(set(requested).difference(_SUPPORTED))
    if unknown:
        raise ValueError(f"Unsupported event metrics: {unknown}")
    if date_field not in events.catalog.columns:
        raise ValueError(f"Event catalog has no date field {date_field!r}")

    frame = events.catalog.copy()
    dates = pd.to_datetime(frame[date_field])
    dim = "period" if period == "all" else period
    if period == "year":
        frame[dim] = dates.dt.year.astype(int)
    elif period == "month":
        frame[dim] = dates.dt.to_period("M").astype(str)
    else:
        frame[dim] = "all"

    labels = pd.Index(frame[dim].drop_duplicates().sort_values())
    grouped = frame.groupby(dim, sort=True, dropna=False)
    output: dict[str, xr.DataArray] = {}
    duration_unit = _duration_unit(events)
    severity_column = "peak_severity" if "peak_severity" in frame else "peak"
    for metric in requested:
        values = _metric_values(grouped, metric, severity_column=severity_column)
        values = values.reindex(labels)
        array = xr.DataArray(values.to_numpy(), dims=(dim,), coords={dim: labels.to_numpy()}, name=metric)
        array.attrs.update(_metric_attrs(metric, events, duration_unit))
        output[metric] = array

    result = xr.Dataset(output)
    result.attrs.update(
        {
            "analysis": "event_metrics",
            "semantic_name": f"{period} event metrics",
            "semantic_kind": "summary",
            "semantic_category": "event_summary",
            "event_scope": events.event_scope,
            "event_row_meaning": events.row_meaning,
            "period": period,
            "period_assignment_field": date_field,
            "event_count_interpretation": (
                "counts local cell instances, not independent regional episodes"
                if events.event_scope == "local_cell"
                else "counts consolidated regional episodes"
            ),
        }
    )
    return result


def _metric_values(grouped, metric: str, *, severity_column: str):
    if metric == "event_count":
        return grouped.size().astype(np.int64)
    if metric == "mean_duration":
        return grouped["duration"].mean()
    if metric == "median_duration":
        return grouped["duration"].median()
    if metric == "max_duration":
        return grouped["duration"].max()
    if metric == "event_days":
        return grouped["duration"].sum()
    if metric in {"mean_severity", "max_severity"}:
        if severity_column not in grouped.obj.columns:
            raise ValueError(f"{metric} requires event severity metadata")
        return getattr(grouped[severity_column], "mean" if metric.startswith("mean") else "max")()
    if metric in {"mean_participating_cells", "max_participating_cells", "peak_footprint"}:
        column = "peak_participation" if metric == "peak_footprint" else "participating_cell_count"
        if column not in grouped.obj.columns:
            raise ValueError(f"{metric} requires consolidated regional episodes")
        method = "mean" if metric.startswith("mean") else "max"
        return getattr(grouped[column], method)()
    raise AssertionError(metric)


def _duration_unit(events: EventResult) -> str:
    resolution = events.dataset.attrs.get("temporal_resolution")
    return "days" if resolution == "daily" else "observation periods"


def _metric_attrs(metric: str, events: EventResult, duration_unit: str) -> dict[str, str]:
    scope = events.event_scope
    if metric == "event_count":
        return {"units": "count", "long_name": f"Number of {scope} events"}
    if "duration" in metric:
        return {"units": duration_unit, "long_name": metric.replace("_", " ").title()}
    if metric == "event_days":
        prefix = "cell-" if scope == "local_cell" else "episode-"
        return {
            "units": prefix + duration_unit,
            "long_name": "Summed event duration",
            "interpretation": "Local-cell durations accumulate across cells" if scope == "local_cell" else "Regional episode durations",
        }
    if "severity" in metric:
        source_units = events.dataset.attrs.get("units") or events.dataset.attrs.get("magnitude_units")
        attrs = {"long_name": metric.replace("_", " ").title()}
        if source_units:
            attrs["units"] = str(source_units)
        return attrs
    return {"units": "count", "long_name": metric.replace("_", " ").title()}


__all__ = ["event_metrics"]
