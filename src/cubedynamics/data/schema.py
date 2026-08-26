"""Deterministic scientific schema descriptions for xarray source results."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import numpy as np
import xarray as xr


SCHEMA_FINGERPRINT_VERSION = 1


def normalize_xarray_schema(value: xr.Dataset | xr.DataArray) -> dict[str, Any]:
    """Return scientifically relevant structural metadata in canonical order.

    Array values, chunk shapes, retrieval timestamps, and dimension sizes are
    deliberately excluded so equivalent bounded requests share a fingerprint.
    Variable dimension order is retained because it can affect interpretation.
    """

    if isinstance(value, xr.DataArray):
        variable_name = str(value.name or "__dataarray__")
        dataset = value.to_dataset(name=variable_name)
        object_type = "DataArray"
    elif isinstance(value, xr.Dataset):
        dataset = value
        object_type = "Dataset"
    else:
        raise TypeError("Schema fingerprinting currently supports xarray Dataset/DataArray.")

    coordinates = {
        str(name): _array_schema(coordinate, coordinate=True)
        for name, coordinate in sorted(dataset.coords.items(), key=lambda item: str(item[0]))
    }
    variables = {
        str(name): _array_schema(variable, coordinate=False)
        for name, variable in sorted(dataset.data_vars.items(), key=lambda item: str(item[0]))
    }
    grid_mappings: dict[str, Any] = {}
    for name, variable in sorted(dataset.variables.items(), key=lambda item: str(item[0])):
        if "grid_mapping_name" in variable.attrs:
            grid_mappings[str(name)] = _selected_mapping(variable.attrs)

    return {
        "fingerprint_version": SCHEMA_FINGERPRINT_VERSION,
        "object_type": object_type,
        "dimensions": sorted(str(name) for name in dataset.dims),
        "coordinates": coordinates,
        "variables": variables,
        "crs": _infer_crs(dataset),
        "grid_mappings": grid_mappings,
    }


def schema_fingerprint(value: xr.Dataset | xr.DataArray) -> str:
    """Hash the canonical scientific schema without reading array values."""

    normalized = normalize_xarray_schema(value)
    return fingerprint_normalized_schema(normalized)


def fingerprint_normalized_schema(normalized: Mapping[str, Any]) -> str:
    """Hash any normalized schema representation deterministically."""

    payload = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def normalize_vector_schema(
    *,
    fields: Mapping[str, str],
    geometry_type: str,
    crs: str,
    layer_id: str | None = None,
    coded_domains: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize a vector schema without requiring a geospatial dependency."""

    return {
        "fingerprint_version": SCHEMA_FINGERPRINT_VERSION,
        "object_type": "vector",
        "fields": {str(key): str(value) for key, value in sorted(fields.items())},
        "geometry_type": str(geometry_type),
        "crs": str(crs),
        "layer_id": layer_id,
        "coded_domains": _json_mapping(coded_domains or {}),
    }


def normalize_api_schema(
    *,
    fields: Mapping[str, str],
    units: Mapping[str, str] | None = None,
    parameter_ids: Mapping[str, str] | None = None,
    geography_ids: tuple[str, ...] = (),
    datetime_representation: str,
) -> dict[str, Any]:
    """Normalize an API/tabular response contract for later source families."""

    return {
        "fingerprint_version": SCHEMA_FINGERPRINT_VERSION,
        "object_type": "api",
        "fields": {str(key): str(value) for key, value in sorted(fields.items())},
        "units": _json_mapping(units or {}),
        "parameter_ids": _json_mapping(parameter_ids or {}),
        "geography_ids": sorted(str(item) for item in geography_ids),
        "datetime_representation": str(datetime_representation),
    }


def compare_normalized_schemas(
    expected: Mapping[str, Any], observed: Mapping[str, Any]
) -> dict[str, Any]:
    """Return deterministic, path-level schema drift evidence."""

    changes: list[dict[str, Any]] = []
    _compare_values(expected, observed, path="$", changes=changes)
    return {
        "matches": not changes,
        "expected_fingerprint": fingerprint_normalized_schema(expected),
        "observed_fingerprint": fingerprint_normalized_schema(observed),
        "changes": changes,
    }


def _array_schema(array: xr.DataArray, *, coordinate: bool) -> dict[str, Any]:
    attrs = array.attrs
    encoding = array.encoding
    fill = _first_present(attrs, encoding, names=("_FillValue", "missing_value", "nodata"))
    calendar = _first_present(attrs, encoding, names=("calendar",))
    return {
        "dims": [str(dim) for dim in array.dims],
        "dtype": _dtype_name(array.dtype),
        "units": _optional_text(attrs.get("units")),
        "calendar": _optional_text(calendar),
        "fill_value": _json_scalar(fill),
        "categorical": _is_categorical(array),
        "role": "coordinate" if coordinate else "variable",
        "grid_mapping": _optional_text(attrs.get("grid_mapping")),
    }


def _dtype_name(dtype: Any) -> str:
    try:
        return np.dtype(dtype).name
    except TypeError:
        return str(dtype)


def _is_categorical(array: xr.DataArray) -> bool:
    attrs = array.attrs
    return bool(
        np.dtype(array.dtype).kind == "b"
        or any(name in attrs for name in ("flag_values", "flag_meanings", "categories"))
    )


def _infer_crs(dataset: xr.Dataset) -> str | None:
    for attrs in (dataset.attrs, *(variable.attrs for variable in dataset.variables.values())):
        for name in ("crs", "spatial_reference", "crs_wkt"):
            if attrs.get(name) not in (None, ""):
                return str(attrs[name])
        if attrs.get("epsg") not in (None, ""):
            return f"EPSG:{attrs['epsg']}"
    return None


def _selected_mapping(attrs: Mapping[str, Any]) -> dict[str, Any]:
    names = (
        "grid_mapping_name",
        "spatial_ref",
        "crs_wkt",
        "epsg_code",
        "semi_major_axis",
        "inverse_flattening",
        "longitude_of_prime_meridian",
    )
    return {
        name: _json_scalar(attrs[name])
        for name in names
        if name in attrs and attrs[name] not in (None, "")
    }


def _first_present(*mappings: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    for mapping in mappings:
        for name in names:
            if name in mapping:
                return mapping[name]
    return None


def _optional_text(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


def _json_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_json_scalar(item) for item in value]
    return str(value)


def _json_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): (
            _json_mapping(item) if isinstance(item, Mapping) else _json_scalar(item)
        )
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
    }


def _compare_values(
    expected: Any,
    observed: Any,
    *,
    path: str,
    changes: list[dict[str, Any]],
) -> None:
    if isinstance(expected, Mapping) and isinstance(observed, Mapping):
        keys = sorted(set(expected) | set(observed), key=str)
        for key in keys:
            child = f"{path}.{key}"
            if key not in expected:
                changes.append({"path": child, "change": "added", "observed": observed[key]})
            elif key not in observed:
                changes.append({"path": child, "change": "removed", "expected": expected[key]})
            else:
                _compare_values(expected[key], observed[key], path=child, changes=changes)
        return
    if expected != observed:
        changes.append(
            {"path": path, "change": "changed", "expected": expected, "observed": observed}
        )


__all__ = [
    "SCHEMA_FINGERPRINT_VERSION",
    "compare_normalized_schemas",
    "fingerprint_normalized_schema",
    "normalize_api_schema",
    "normalize_vector_schema",
    "normalize_xarray_schema",
    "schema_fingerprint",
]
