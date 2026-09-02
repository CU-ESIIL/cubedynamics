"""Pipe-friendly event verbs."""

from __future__ import annotations

from ..events.detection import detect_events as _detect_events
from ..events.consolidation import consolidate_events as _consolidate_events
from ..events.metrics import event_metrics as _event_metrics


def detect_events(
    *,
    state_var: str = "state",
    magnitude_var: str = "magnitude",
    min_duration: int = 1,
    max_gap: int = 0,
):
    """Summary
    Detect contiguous state runs as events.

    Grammar contract
    State Dataset -> EventResult containing event cube variables and a catalog.
    """

    def _op(obj):
        return _detect_events(
            obj,
            state_var=state_var,
            magnitude_var=magnitude_var,
            min_duration=min_duration,
            max_gap=max_gap,
        )

    return _op


def consolidate_events(
    *,
    spatial_relation: str = "neighbors",
    max_gap: str | int = "0D",
    radius_km: float | None = None,
    min_participating_cells: int = 1,
    min_local_events: int = 1,
):
    """Consolidate local-cell events into explicit regional episodes."""

    def _op(obj):
        return _consolidate_events(
            obj,
            spatial_relation=spatial_relation,
            max_gap=max_gap,
            radius_km=radius_km,
            min_participating_cells=min_participating_cells,
            min_local_events=min_local_events,
        )

    return _op


def event_metrics(
    *,
    period: str = "year",
    metrics=("event_count", "mean_duration", "max_duration"),
    date_field: str = "start",
):
    """Summarize local events or regional episodes by calendar period."""

    selected = tuple(metrics)

    def _op(obj):
        return _event_metrics(obj, period=period, metrics=selected, date_field=date_field)

    return _op


__all__ = ["consolidate_events", "detect_events", "event_metrics"]
