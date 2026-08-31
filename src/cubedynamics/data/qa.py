"""Reusable structural QA profiles for CubeDynamics source integrations.

Profiles evaluate scientific structure and metadata. Source-specific QA may add
range, physics, checksum, or visual checks, but it should reuse one of these
profiles instead of inventing a second source-registration system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

import numpy as np
import xarray as xr

from .lifecycle import CertificationOutcome


@dataclass(frozen=True)
class QAProfile:
    """Named, documented set of reusable structural checks."""

    name: str
    description: str
    applies_to: str
    evaluator: Callable[[Any, Mapping[str, Any]], tuple[dict[str, bool], dict[str, Any]]]


@dataclass(frozen=True)
class QAProfileResult:
    """Machine-readable result from applying one profile."""

    profile: str
    outcome: CertificationOutcome
    checks: Mapping[str, bool]
    details: Mapping[str, Any]
    caveats: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.outcome in {
            CertificationOutcome.PASS,
            CertificationOutcome.PASS_WITH_CAVEATS,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "outcome": self.outcome.value,
            "checks": dict(sorted(self.checks.items())),
            "details": dict(sorted(self.details.items())),
            "caveats": list(self.caveats),
        }


def _climate_continuous_daily(
    value: Any, context: Mapping[str, Any]
) -> tuple[dict[str, bool], dict[str, Any]]:
    dataset = _as_dataset(value)
    metadata = (dataset.attrs, *(array.attrs for array in dataset.data_vars.values()))
    time = dataset.coords.get("time")
    variables = list(dataset.data_vars.values())
    time_values = np.asarray(time.values) if time is not None else np.asarray([])
    deltas = np.diff(time_values).astype("timedelta64[ns]") if time_values.size > 1 else []
    expected_units = context.get("expected_units")
    observed_units = sorted(
        {str(array.attrs.get("units")) for array in variables if array.attrs.get("units")}
    )
    numeric = dataset[list(dataset.data_vars)].to_array() if variables else None
    missing_fraction = float(numeric.isnull().mean()) if numeric is not None else 1.0
    max_missing = float(context.get("max_missing_fraction", 0.5))
    checks = {
        "xarray_object": True,
        "nonempty_dimensions": bool(dataset.sizes)
        and all(size > 0 for size in dataset.sizes.values()),
        "observational_source": not any(
            bool(attrs.get("is_synthetic", False)) for attrs in metadata
        ),
        "source_identity_documented": any(
            attrs.get(name)
            for attrs in metadata
            for name in ("source", "source_provider", "source_url")
        ),
        "time_coordinate_present": time is not None,
        "spatial_coordinates_present": {"y", "x"}.issubset(dataset.coords),
        "continuous_numeric_variables": bool(variables)
        and all(np.issubdtype(array.dtype, np.number) for array in variables),
        "units_documented": bool(variables)
        and all(bool(array.attrs.get("units")) for array in variables),
        "crs_documented": _has_crs(dataset),
        "time_strictly_increasing": bool(time_values.size)
        and (time_values.size == 1 or bool(np.all(np.asarray(deltas) > np.timedelta64(0, "ns")))),
        "time_values_unique": bool(time_values.size)
        and np.unique(time_values).size == time_values.size,
        "daily_interval": bool(time_values.size)
        and (
            time_values.size == 1
            or bool(np.all(np.asarray(deltas) == np.timedelta64(1, "D")))
        ),
        "expected_units_match": expected_units is None
        or set(observed_units).issubset(set(_string_list(expected_units))),
        "missingness_within_limit": missing_fraction <= max_missing,
        "finite_observations_present": numeric is not None
        and bool(np.isfinite(numeric).any()),
    }
    return checks, {
        "variables": sorted(str(name) for name in dataset.data_vars),
        "observed_units": observed_units,
        "dimensions": sorted(str(name) for name in dataset.dims),
        "missing_fraction": missing_fraction,
    }


def _continuous_raster_static(
    value: Any, context: Mapping[str, Any]
) -> tuple[dict[str, bool], dict[str, Any]]:
    dataset = _as_dataset(value)
    variables = list(dataset.data_vars.values())
    x = dataset.coords.get("x")
    y = dataset.coords.get("y")
    checks = {
        "xarray_object": True,
        "spatial_coordinates_present": x is not None and y is not None,
        "spatial_coordinates_one_dimensional": x is not None
        and y is not None
        and x.ndim == y.ndim == 1,
        "spatial_coordinates_finite": _coordinate_is_finite(x) and _coordinate_is_finite(y),
        "spatial_coordinates_unique": _coordinate_is_unique(x) and _coordinate_is_unique(y),
        "continuous_numeric_variables": bool(variables)
        and all(np.issubdtype(array.dtype, np.number) for array in variables),
        "units_documented": bool(variables)
        and all(bool(array.attrs.get("units")) for array in variables),
        "crs_documented": _has_crs(dataset),
    }
    return checks, {
        "variables": sorted(str(name) for name in dataset.data_vars),
        "dimensions": sorted(str(name) for name in dataset.dims),
        "temporal_layers_allowed": "time" in dataset.dims,
    }


def _feature_line(
    value: Any, context: Mapping[str, Any]
) -> tuple[dict[str, bool], dict[str, Any]]:
    evidence = _evidence_mapping(value)
    geometry_types = set(_string_list(evidence.get("geometry_types", [])))
    feature_count = int(evidence.get("feature_count", 0) or 0)
    valid_fraction = float(evidence.get("valid_geometry_fraction", 0.0) or 0.0)
    checks = {
        "features_present": feature_count > 0,
        "line_geometry_only": bool(geometry_types)
        and geometry_types.issubset({"LineString", "MultiLineString"}),
        "crs_documented": bool(evidence.get("crs")),
        "identifiers_documented": bool(evidence.get("identifier_field")),
        "geometries_valid": valid_fraction == 1.0,
    }
    return checks, {
        "feature_count": feature_count,
        "geometry_types": sorted(geometry_types),
        "valid_geometry_fraction": valid_fraction,
    }


def _station_timeseries(
    value: Any, context: Mapping[str, Any]
) -> tuple[dict[str, bool], dict[str, Any]]:
    dataset = _as_dataset(value)
    station_dim = next(
        (name for name in ("station", "site", "station_id") if name in dataset.dims),
        None,
    )
    station_coord = dataset.coords.get(station_dim) if station_dim else None
    time = dataset.coords.get("time")
    time_values = np.asarray(time.values) if time is not None else np.asarray([])
    variables = list(dataset.data_vars.values())
    checks = {
        "time_coordinate_present": time is not None,
        "station_dimension_present": station_dim is not None,
        "stations_present": station_dim is not None and dataset.sizes[station_dim] > 0,
        "station_identifiers_unique": _coordinate_is_unique(station_coord),
        "time_strictly_increasing": bool(time_values.size)
        and (
            time_values.size == 1
            or bool(
                np.all(
                    np.diff(time_values).astype("timedelta64[ns]")
                    > np.timedelta64(0, "ns")
                )
            )
        ),
        "continuous_numeric_variables": bool(variables)
        and all(np.issubdtype(array.dtype, np.number) for array in variables),
        "units_documented": bool(variables)
        and all(bool(array.attrs.get("units")) for array in variables),
        "station_locations_documented": (
            {"latitude", "longitude"}.issubset(dataset.coords)
            or {"lat", "lon"}.issubset(dataset.coords)
        ),
    }
    return checks, {
        "station_dimension": station_dim,
        "variables": sorted(str(name) for name in dataset.data_vars),
        "dimensions": sorted(str(name) for name in dataset.dims),
    }


_PROFILES = {
    profile.name: profile
    for profile in (
        QAProfile(
            "climate_continuous_daily",
            "Daily gridded continuous climate fields with explicit units, CRS, and ordered time.",
            "xarray Dataset or DataArray",
            _climate_continuous_daily,
        ),
        QAProfile(
            "continuous_raster_static",
            "Continuous raster grids with explicit spatial coordinates, units, and CRS.",
            "xarray Dataset or DataArray",
            _continuous_raster_static,
        ),
        QAProfile(
            "feature_line",
            "Line features with identifiers, valid geometry, and an explicit CRS.",
            "feature evidence mapping",
            _feature_line,
        ),
        QAProfile(
            "station_timeseries",
            "Numeric station observations with unique sites, locations, units, and ordered time.",
            "xarray Dataset or DataArray",
            _station_timeseries,
        ),
    )
}


def list_qa_profiles() -> tuple[str, ...]:
    """Return the stable names of the reusable QA profiles."""

    return tuple(sorted(_PROFILES))


def get_qa_profile(name: str) -> QAProfile:
    """Return one profile, naming available choices on error."""

    key = str(name).strip().lower()
    try:
        return _PROFILES[key]
    except KeyError as exc:
        raise ValueError(
            f"Unknown QA profile {name!r}. Available profiles: {', '.join(list_qa_profiles())}."
        ) from exc


def evaluate_qa_profile(
    name: str,
    value: Any,
    *,
    context: Mapping[str, Any] | None = None,
    caveats: tuple[str, ...] = (),
) -> QAProfileResult:
    """Evaluate a reusable profile and return an explicit certification outcome."""

    profile = get_qa_profile(name)
    try:
        checks, details = profile.evaluator(value, context or {})
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        return QAProfileResult(
            profile=name,
            outcome=CertificationOutcome.BLOCKED,
            checks={"input_compatible": False},
            details={"error": str(exc)},
            caveats=caveats,
        )
    if not checks or not all(checks.values()):
        outcome = CertificationOutcome.FAIL
    elif caveats:
        outcome = CertificationOutcome.PASS_WITH_CAVEATS
    else:
        outcome = CertificationOutcome.PASS
    return QAProfileResult(name, outcome, checks, details, caveats)


def _as_dataset(value: Any) -> xr.Dataset:
    if isinstance(value, xr.Dataset):
        return value
    if isinstance(value, xr.DataArray):
        return value.to_dataset(name=str(value.name or "value"))
    raise TypeError("This QA profile requires an xarray Dataset or DataArray.")


def _has_crs(dataset: xr.Dataset) -> bool:
    for attrs in (dataset.attrs, *(array.attrs for array in dataset.variables.values())):
        names = ("crs", "spatial_reference", "crs_wkt", "epsg")
        if any(attrs.get(name) not in (None, "") for name in names):
            return True
    return False


def _coordinate_is_finite(coordinate: xr.DataArray | None) -> bool:
    if coordinate is None:
        return False
    values = np.asarray(coordinate.values)
    return bool(values.size) and bool(np.isfinite(values).all())


def _coordinate_is_unique(coordinate: xr.DataArray | None) -> bool:
    if coordinate is None:
        return False
    values = np.asarray(coordinate.values)
    return bool(values.size) and np.unique(values).size == values.size


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _evidence_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("The feature_line profile requires a feature evidence mapping.")
    return value


__all__ = [
    "QAProfile",
    "QAProfileResult",
    "evaluate_qa_profile",
    "get_qa_profile",
    "list_qa_profiles",
]
