"""Explicit consolidation of local-cell events into regional episodes."""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from .schemas import EventResult


def consolidate_events(
    events: EventResult,
    *,
    spatial_relation: str = "neighbors",
    max_gap: str | int = "0D",
    radius_km: float | None = None,
    min_participating_cells: int = 1,
    min_local_events: int = 1,
) -> EventResult:
    """Join local event instances using explicit space-time connectivity.

    Events are connected only when their label intervals overlap (or are within
    ``max_gap``) *and* their cells satisfy ``spatial_relation``. Connected
    components become regional episodes. This operation never groups rows by
    date alone.
    """

    if not isinstance(events, EventResult):
        raise TypeError("consolidate_events requires an EventResult")
    if events.event_scope != "local_cell":
        raise ValueError(
            "consolidate_events requires local_cell events; received "
            f"{events.event_scope!r}"
        )
    if spatial_relation not in {"neighbors", "same_cell", "radius"}:
        raise ValueError("spatial_relation must be 'neighbors', 'same_cell', or 'radius'")
    if spatial_relation == "radius":
        if radius_km is None or radius_km <= 0:
            raise ValueError("spatial_relation='radius' requires radius_km > 0")
    elif radius_km is not None:
        raise ValueError("radius_km is only valid with spatial_relation='radius'")
    if min_participating_cells < 1 or min_local_events < 1:
        raise ValueError("minimum cell and event counts must be at least 1")

    gap = _parse_gap(max_gap)
    catalog = events.catalog.copy().reset_index(drop=True)
    required = {"event_id", "start", "end", "y_index", "x_index"}
    missing = sorted(required.difference(catalog.columns))
    if missing:
        raise ValueError(f"Local event catalog is missing required columns: {missing}")
    if catalog.empty:
        return _empty_result(events, spatial_relation, gap, radius_km)

    catalog["start"] = pd.to_datetime(catalog["start"])
    catalog["end"] = pd.to_datetime(catalog["end"])
    order = np.argsort(catalog["start"].to_numpy(), kind="stable")
    parent = list(range(len(catalog)))
    active: list[int] = []
    spatial_names = _spatial_coordinate_names(events)

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for current in order:
        current = int(current)
        start = catalog.at[current, "start"]
        active = [
            candidate
            for candidate in active
            if catalog.at[candidate, "end"] + gap >= start
        ]
        for candidate in active:
            if _spatially_connected(
                catalog.iloc[candidate],
                catalog.iloc[current],
                relation=spatial_relation,
                radius_km=radius_km,
                spatial_names=spatial_names,
            ):
                union(candidate, current)
        active.append(current)

    components: dict[int, list[int]] = {}
    for index in range(len(catalog)):
        components.setdefault(find(index), []).append(index)

    records: list[dict[str, Any]] = []
    source_times = pd.DatetimeIndex(events.dataset.coords.get("time", []))
    y_name, x_name = spatial_names
    for indices in components.values():
        rows = catalog.iloc[indices]
        cells = rows[["y_index", "x_index"]].drop_duplicates()
        if len(rows) < min_local_events or len(cells) < min_participating_cells:
            continue
        start, end = rows["start"].min(), rows["end"].max()
        duration = _coordinate_duration(source_times, start, end)
        episode_id = len(records) + 1
        record: dict[str, Any] = {
            "episode_id": episode_id,
            "start": start.to_datetime64(),
            "end": end.to_datetime64(),
            "duration": duration,
            "local_event_count": int(len(rows)),
            "participating_cell_count": int(len(cells)),
            "peak_participation": _peak_participation(events, rows),
            "source_event_ids": ",".join(str(value) for value in rows["event_id"]),
        }
        if "peak" in rows:
            finite = pd.to_numeric(rows["peak"], errors="coerce")
            record["peak_severity"] = float(finite.max()) if finite.notna().any() else np.nan
        if y_name in rows and x_name in rows:
            unique_cells = rows.drop_duplicates(["y_index", "x_index"])
            record[f"centroid_{y_name}"] = float(pd.to_numeric(unique_cells[y_name]).mean())
            record[f"centroid_{x_name}"] = float(pd.to_numeric(unique_cells[x_name]).mean())
        records.append(record)

    rules = {
        "spatial_relation": spatial_relation,
        "radius_km": radius_km,
        "max_gap": str(gap),
        "min_participating_cells": min_participating_cells,
        "min_local_events": min_local_events,
    }
    return _regional_result(events, records, rules)


def _regional_result(
    source: EventResult,
    records: list[dict[str, Any]],
    rules: dict[str, Any],
) -> EventResult:
    catalog = pd.DataFrame.from_records(records)
    episode = np.arange(1, len(records) + 1, dtype=np.int64)
    data_vars: dict[str, tuple[str, np.ndarray]] = {}
    for column in catalog.columns:
        if column == "source_event_ids":
            continue
        values = catalog[column].to_numpy()
        data_vars[column] = ("episode", values)
    dataset = xr.Dataset(data_vars, coords={"episode": episode})
    dataset.attrs.update(source.dataset.attrs)
    dataset.attrs.update(
        {
            "analysis": "consolidated_events",
            "semantic_name": "regional episodes",
            "semantic_kind": "event",
            "semantic_category": "event",
            "event_scope": "regional_episode",
            "source_event_scope": source.event_scope,
            "event_count": len(records),
            "consolidation_rule": json.dumps(rules, sort_keys=True),
            "consolidation_temporal_basis": "event start/end coordinate labels",
            "event_time_support_note": (
                "Episode bounds are the earliest and latest source event labels; "
                "observation support is not shifted or resampled."
            ),
        }
    )
    if "duration" in dataset:
        dataset["duration"].attrs.update(
            {"long_name": "Episode duration in source observation coordinates", "units": "observation periods"}
        )
    for name in ("local_event_count", "participating_cell_count", "peak_participation"):
        if name in dataset:
            dataset[name].attrs["units"] = "count"
    if "peak_severity" in dataset:
        source_units = source.dataset.attrs.get("magnitude_units") or source.dataset.attrs.get("units")
        if source_units:
            dataset["peak_severity"].attrs["units"] = str(source_units)
    return EventResult(
        dataset=dataset,
        catalog=catalog,
        event_scope="regional_episode",
        spatial_identity_fields=("episode_id",),
    )


def _empty_result(
    source: EventResult,
    spatial_relation: str,
    gap: pd.Timedelta,
    radius_km: float | None,
) -> EventResult:
    return _regional_result(
        source,
        [],
        {
            "spatial_relation": spatial_relation,
            "radius_km": radius_km,
            "max_gap": str(gap),
            "min_participating_cells": 1,
            "min_local_events": 1,
        },
    )


def _parse_gap(value: str | int) -> pd.Timedelta:
    if isinstance(value, int):
        if value < 0:
            raise ValueError("max_gap must be nonnegative")
        return pd.Timedelta(days=value)
    gap = pd.Timedelta(value)
    if gap < pd.Timedelta(0):
        raise ValueError("max_gap must be nonnegative")
    return gap


def _spatial_coordinate_names(events: EventResult) -> tuple[str, str]:
    active = events.dataset.get("event_active")
    if active is None:
        return ("y", "x")
    dims = [dim for dim in active.dims if dim != "time"]
    return (dims[0], dims[1]) if len(dims) >= 2 else ("y", "x")


def _spatially_connected(
    left: pd.Series,
    right: pd.Series,
    *,
    relation: str,
    radius_km: float | None,
    spatial_names: tuple[str, str],
) -> bool:
    if relation == "same_cell":
        return left["y_index"] == right["y_index"] and left["x_index"] == right["x_index"]
    if relation == "neighbors":
        return max(
            abs(int(left["y_index"]) - int(right["y_index"])),
            abs(int(left["x_index"]) - int(right["x_index"])),
        ) <= 1
    y_name, x_name = spatial_names
    if y_name not in left or x_name not in left:
        raise ValueError("radius consolidation requires spatial coordinate columns")
    lat1, lon1 = float(left[y_name]), float(left[x_name])
    lat2, lon2 = float(right[y_name]), float(right[x_name])
    if any((abs(lat1) > 90, abs(lat2) > 90, abs(lon1) > 180, abs(lon2) > 180)):
        raise ValueError(
            "radius_km requires geographic latitude/longitude coordinates; "
            "projected coordinates must be transformed explicitly first"
        )
    return _haversine_km(lat1, lon1, lat2, lon2) <= float(radius_km)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 6371.0088 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _coordinate_duration(times: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp) -> int:
    if len(times):
        return int(((times >= start) & (times <= end)).sum())
    return int((end.normalize() - start.normalize()) / pd.Timedelta(days=1)) + 1


def _peak_participation(source: EventResult, rows: pd.DataFrame) -> int:
    if "event_active" not in source.dataset or "event_id" not in source.dataset:
        return 0
    active = np.asarray(source.dataset["event_active"].values, dtype=bool)
    identifiers = np.asarray(source.dataset["event_id"].values)
    selected = np.isin(identifiers, rows["event_id"].to_numpy()) & active
    if selected.ndim < 2:
        return int(selected.max(initial=False))
    participation = selected.sum(axis=tuple(range(1, selected.ndim)))
    return int(participation.max(initial=0))


__all__ = ["consolidate_events"]
