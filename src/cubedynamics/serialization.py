"""Deterministic NetCDF metadata and Boolean-state encoding helpers.

NetCDF attributes do not support Python/NumPy booleans, ``None``, mappings,
or arbitrary nested objects.  CubeDynamics keeps public source metadata in a
portable subset so ordinary source results can use xarray's ``to_netcdf``
directly.  The explicit pipe verb additionally writes a sanitized shallow copy
and encodes Boolean data variables as int8 without mutating the analysis object.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import xarray as xr


METADATA_ENCODING = "netcdf-safe-v1"


def _json_value(value: Any) -> Any:
    """Return a JSON-compatible value or raise for unsupported metadata."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, (datetime, date, np.datetime64)):
        return str(value)
    if isinstance(value, (Path, Enum)):
        return _json_value(value.value if isinstance(value, Enum) else str(value))
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [_json_value(item) for item in value]
        return sorted(converted, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist())
    if is_dataclass(value):
        return _json_value(asdict(value))
    for method_name in ("as_dict", "to_dict", "model_dump"):
        method = getattr(value, method_name, None)
        if callable(method):
            return _json_value(method())
    geo_interface = getattr(value, "__geo_interface__", None)
    if geo_interface is not None:
        return _json_value(geo_interface)
    raise TypeError(
        "unsupported metadata value of type "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def netcdf_safe_attr(value: Any) -> str | bytes | int | float | np.number:
    """Encode one attribute using the documented portable NetCDF policy.

    Scalars stay scalars, booleans become ``0``/``1``, missing values become
    the JSON literal ``"null"``, datetime-like values become ISO-style text,
    and structured values become canonical JSON.  Unsupported custom objects
    raise rather than being silently discarded or reduced to an unstable repr.
    """

    if isinstance(value, (bool, np.bool_)):
        return int(value)
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value
    if isinstance(value, np.generic):
        return netcdf_safe_attr(value.item())
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (datetime, date, np.datetime64, Path, Enum)):
        return str(_json_value(value))
    if isinstance(value, (Mapping, list, tuple, set, frozenset, np.ndarray)) or is_dataclass(value):
        return json.dumps(
            _json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
    for method_name in ("as_dict", "to_dict", "model_dump"):
        if callable(getattr(value, method_name, None)):
            return json.dumps(
                _json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
    if getattr(value, "__geo_interface__", None) is not None:
        return json.dumps(
            _json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
    raise TypeError(
        "CubeDynamics cannot encode NetCDF attribute value "
        f"{value!r}: unsupported type {type(value).__module__}.{type(value).__qualname__}. "
        "Store a stable string/number or a JSON-compatible structure instead."
    )


def netcdf_safe_attrs(attrs: Mapping[Any, Any]) -> dict[str, Any]:
    """Return a deterministic, NetCDF-compatible copy of an attrs mapping."""

    encoded: dict[str, Any] = {}
    for key, value in attrs.items():
        try:
            encoded[str(key)] = netcdf_safe_attr(value)
        except TypeError as exc:
            raise TypeError(f"NetCDF attribute {key!r} is not serializable. {exc}") from exc
    return encoded


def sanitize_netcdf_attrs(
    obj: xr.DataArray | xr.Dataset,
    *,
    copy: bool = True,
) -> xr.DataArray | xr.Dataset:
    """Make container, variable, and coordinate attrs NetCDF-compatible."""

    target = obj.copy(deep=False) if copy else obj
    target.attrs = netcdf_safe_attrs(target.attrs)
    if isinstance(target, xr.Dataset):
        for name in target.data_vars:
            target[name].attrs = netcdf_safe_attrs(target[name].attrs)
    for name in target.coords:
        target[name].attrs = netcdf_safe_attrs(target[name].attrs)
    return target


def prepare_netcdf_output(obj: xr.DataArray | xr.Dataset) -> xr.DataArray | xr.Dataset:
    """Return a write-only copy with portable attrs and Boolean variables.

    NetCDF has no native Boolean variable type.  Boolean data variables are
    stored as int8 and identified in file-level metadata so their scientific
    meaning remains explicit.  The in-memory input retains its Boolean dtype.
    """

    target = sanitize_netcdf_attrs(obj, copy=True)
    metadata_changed = any(
        key not in target.attrs
        or type(value) is not type(target.attrs[key])
        or value != target.attrs[key]
        for key, value in obj.attrs.items()
    )
    if isinstance(obj, xr.Dataset):
        metadata_changed = metadata_changed or any(
            key not in target[name].attrs
            or type(value) is not type(target[name].attrs[key])
            or value != target[name].attrs[key]
            for name in obj.data_vars
            for key, value in obj[name].attrs.items()
        )
    metadata_changed = metadata_changed or any(
        key not in target[name].attrs
        or type(value) is not type(target[name].attrs[key])
        or value != target[name].attrs[key]
        for name in obj.coords
        for key, value in obj[name].attrs.items()
    )
    boolean_variables: list[str] = []
    if isinstance(target, xr.Dataset):
        for name in list(target.data_vars):
            if target[name].dtype == bool:
                attrs = dict(target[name].attrs)
                attrs.update(
                    {
                        "cubedynamics_original_dtype": "bool",
                        "flag_values": "0,1",
                        "flag_meanings": "false true",
                    }
                )
                target[name] = target[name].astype("int8").assign_attrs(attrs)
                boolean_variables.append(str(name))
    elif target.dtype == bool:
        attrs = dict(target.attrs)
        attrs.update(
            {
                "cubedynamics_original_dtype": "bool",
                "flag_values": "0,1",
                "flag_meanings": "false true",
            }
        )
        target = target.astype("int8").assign_attrs(attrs)
        boolean_variables.append(target.name or "__dataarray__")

    if metadata_changed or boolean_variables:
        target.attrs["cubedynamics_metadata_encoding"] = METADATA_ENCODING
    if boolean_variables:
        target.attrs["cubedynamics_boolean_variables"] = json.dumps(boolean_variables)
    return target


__all__ = [
    "METADATA_ENCODING",
    "netcdf_safe_attr",
    "netcdf_safe_attrs",
    "prepare_netcdf_output",
    "sanitize_netcdf_attrs",
]
