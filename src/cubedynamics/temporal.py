"""Temporal-support metadata and diagnostics for scientific cubes.

Time coordinates are labels.  The observations attached to those labels may
represent instants or intervals, and two equal labels need not describe the
same interval in the physical world.  This module keeps that distinction
metadata-only: it never shifts, resamples, aggregates, or computes cube data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd
import xarray as xr


_SUPPORT_ATTRS = {
    "resolution": "temporal_resolution",
    "support_type": "temporal_support_type",
    "label_convention": "temporal_label_convention",
    "reference_timezone": "temporal_reference_timezone",
    "start_offset": "temporal_support_start_offset",
    "end_offset": "temporal_support_end_offset",
    "known": "temporal_support_known",
    "evidence": "temporal_support_evidence",
}


@dataclass(frozen=True)
class TemporalSupport:
    """Source-qualified meaning of one object's temporal observations."""

    resolution: str | None = None
    support_type: str = "unknown"
    label_convention: str | None = None
    reference_timezone: str | None = None
    start_offset: str | None = None
    end_offset: str | None = None
    known: bool = False
    evidence: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation using public metadata names."""

        return {
            attr: getattr(self, field)
            for field, attr in _SUPPORT_ATTRS.items()
        }

    @property
    def interval(self) -> bool:
        """Whether the support is a known observation interval."""

        return self.known and self.support_type == "interval"

    @property
    def instant(self) -> bool:
        """Whether the support is a known point observation."""

        return self.known and self.support_type == "instant"

    def scientifically_equal(self, other: "TemporalSupport") -> bool | None:
        """Return exact support equality, or ``None`` when either is unknown."""

        if not self.known or not other.known:
            return None
        return (
            self.resolution,
            self.support_type,
            self.label_convention,
            self.reference_timezone,
            self.start_offset,
            self.end_offset,
        ) == (
            other.resolution,
            other.support_type,
            other.label_convention,
            other.reference_timezone,
            other.start_offset,
            other.end_offset,
        )


@dataclass(frozen=True)
class TemporalAlignmentReport:
    """Metadata-only comparison of coordinate labels and temporal support."""

    coordinates: str
    temporal_support: str
    left: TemporalSupport
    right: TemporalSupport
    left_source: str | None = None
    right_source: str | None = None

    @property
    def exact(self) -> bool:
        """Whether both coordinate labels and known supports are exact."""

        return self.coordinates == "exact" and self.temporal_support == "exact"

    def as_dict(self) -> dict[str, Any]:
        """Return a stable, serializable diagnostic record."""

        return {
            "coordinates": self.coordinates,
            "temporal_support": self.temporal_support,
            "left_source": self.left_source,
            "right_source": self.right_source,
            "left": self.left.as_dict(),
            "right": self.right.as_dict(),
        }


def temporal_support(obj: Any) -> TemporalSupport:
    """Inspect temporal-support metadata without touching array values.

    Missing metadata is represented as an unknown support, never inferred from
    a daily-looking coordinate alone.
    """

    attrs: Mapping[str, Any] = getattr(obj, "attrs", {}) or {}
    known = _as_bool(attrs.get(_SUPPORT_ATTRS["known"], False))
    support_type = str(attrs.get(_SUPPORT_ATTRS["support_type"], "unknown"))
    if not known:
        support_type = "unknown" if support_type in {"", "None"} else support_type
    return TemporalSupport(
        resolution=_optional_text(attrs.get(_SUPPORT_ATTRS["resolution"])),
        support_type=support_type,
        label_convention=_optional_text(attrs.get(_SUPPORT_ATTRS["label_convention"])),
        reference_timezone=_optional_text(attrs.get(_SUPPORT_ATTRS["reference_timezone"])),
        start_offset=_optional_text(attrs.get(_SUPPORT_ATTRS["start_offset"])),
        end_offset=_optional_text(attrs.get(_SUPPORT_ATTRS["end_offset"])),
        known=known,
        evidence=_optional_text(attrs.get(_SUPPORT_ATTRS["evidence"])),
    )


def observation_intervals(
    obj: xr.DataArray | xr.Dataset,
    *,
    time_dim: str = "time",
) -> xr.Dataset:
    """Derive one-dimensional observation starts and ends from support rules.

    Only the time coordinate is materialized.  Cube values are neither copied
    nor computed, so a Dask-backed input remains lazy and unchanged.
    """

    if time_dim not in obj.coords:
        raise ValueError(f"observation_intervals requires coordinate {time_dim!r}")
    support = temporal_support(obj)
    if not support.known:
        raise ValueError(
            "Temporal support is unknown; observation intervals cannot be derived."
        )
    labels = obj.coords[time_dim]
    if getattr(labels.dtype, "kind", None) != "M":
        raise TypeError("observation_intervals requires a datetime64 time coordinate")

    if support.support_type == "instant":
        starts = labels
        ends = labels
    elif support.support_type == "interval":
        if support.start_offset is None or support.end_offset is None:
            raise ValueError(
                "Known interval support requires start and end offset metadata."
            )
        starts = labels + _timedelta64(support.start_offset)
        ends = labels + _timedelta64(support.end_offset)
    else:
        raise ValueError(
            f"Unsupported temporal_support_type {support.support_type!r}; "
            "expected 'instant' or 'interval'."
        )

    result = xr.Dataset(
        {
            "observation_start": starts.rename("observation_start"),
            "observation_end": ends.rename("observation_end"),
        }
    )
    support_attrs = support.as_dict()
    support_attrs["temporal_support_known"] = int(support.known)
    result.attrs.update(support_attrs)
    result.attrs.update(
        {
            "analysis": "temporal_support_intervals",
            "source_flavor": str(getattr(obj, "attrs", {}).get("source_flavor", "")),
        }
    )
    return result


def compare_temporal_support(
    left: xr.DataArray | xr.Dataset,
    right: xr.DataArray | xr.Dataset,
    *,
    time_dim: str = "time",
) -> TemporalAlignmentReport:
    """Compare time-coordinate labels separately from observation support."""

    coordinates = _coordinate_relationship(left, right, time_dim=time_dim)
    left_support = temporal_support(left)
    right_support = temporal_support(right)
    support_equal = left_support.scientifically_equal(right_support)
    support_status = (
        "unknown" if support_equal is None else "exact" if support_equal else "different"
    )
    return TemporalAlignmentReport(
        coordinates=coordinates,
        temporal_support=support_status,
        left=left_support,
        right=right_support,
        left_source=_source_name(left),
        right_source=_source_name(right),
    )


def _coordinate_relationship(left: Any, right: Any, *, time_dim: str) -> str:
    left_coords = getattr(left, "coords", {})
    right_coords = getattr(right, "coords", {})
    if time_dim not in left_coords or time_dim not in right_coords:
        return "absent"
    left_index = left.get_index(time_dim)
    right_index = right.get_index(time_dim)
    return "exact" if left_index.equals(right_index) else "different"


def _source_name(obj: Any) -> str | None:
    attrs = getattr(obj, "attrs", {}) or {}
    value = attrs.get("source_flavor") or attrs.get("source_provider")
    return str(value) if value not in (None, "") else None


def _timedelta64(value: str) -> np.timedelta64:
    try:
        nanoseconds = int(pd.to_timedelta(value).value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid temporal-support offset {value!r}") from exc
    return np.timedelta64(nanoseconds, "ns")


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "known"}
    return bool(value)


def _optional_text(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


__all__ = [
    "TemporalAlignmentReport",
    "TemporalSupport",
    "compare_temporal_support",
    "observation_intervals",
    "temporal_support",
]
