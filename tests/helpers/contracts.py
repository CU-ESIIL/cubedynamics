"""Contract helpers for asserting cube invariants in tests."""

from __future__ import annotations

import re

import numpy as np
import xarray as xr


def _select_dataarray(obj: xr.Dataset | xr.DataArray, var: str | None) -> xr.DataArray:
    if isinstance(obj, xr.DataArray):
        return obj
    if not obj.data_vars:
        raise AssertionError("Dataset must contain at least one data variable")
    if var is None:
        name = next(iter(obj.data_vars))
    else:
        if var not in obj.data_vars:
            raise AssertionError(f"Variable {var!r} not found in Dataset")
        name = var
    return obj[name]


def assert_spatiotemporal_cube_contract(
    obj: xr.Dataset | xr.DataArray,
    *,
    require_time: bool = True,
    allow_empty_time: bool = False,
    allow_latlon: bool = True,
    allow_yx: bool = True,
    var: str | None = None,
) -> None:
    """Validate core cube structure used across loaders."""

    da = _select_dataarray(obj, var)
    dims = set(da.dims)

    if require_time:
        assert "time" in dims, "Expected 'time' dimension"
        time_len = int(da.sizes.get("time", 0))
        if not allow_empty_time:
            assert time_len > 0, "Expected non-empty time axis"
        assert "time" in da.coords, "Missing time coordinate"
        assert da["time"].ndim == 1, "time coordinate must be 1D"

    spatial_pairs: list[tuple[str, str]] = []
    if allow_yx:
        spatial_pairs.append(("y", "x"))
    if allow_latlon:
        spatial_pairs.append(("lat", "lon"))

    found_pair = None
    for y_name, x_name in spatial_pairs:
        if {y_name, x_name}.issubset(dims):
            found_pair = (y_name, x_name)
            break

    assert found_pair is not None, "Expected spatial dimensions (y/x or lat/lon)"

    y_name, x_name = found_pair
    for dim_name in (y_name, x_name):
        assert dim_name in da.coords, f"Missing coordinate for {dim_name!r}"
        coord = da[dim_name]
        assert coord.ndim == 1, f"Coordinate {dim_name!r} must be 1D"


def infer_epsg_like(obj: xr.Dataset | xr.DataArray) -> int | None:
    """Infer EPSG code from attrs/coords/crs hints, mirroring runtime priority."""

    attrs = getattr(obj, "attrs", {})
    if "epsg" in attrs:
        try:
            return int(attrs["epsg"])
        except Exception:
            pass

    if isinstance(obj, xr.Dataset):
        coords = obj.coords
    else:
        coords = obj.coords

    if "epsg" in coords:
        coord = coords["epsg"]
        try:
            if coord.ndim == 0 or coord.size == 1:
                return int(coord.item())
        except Exception:
            pass

    if hasattr(obj, "rio"):
        try:
            crs = obj.rio.crs  # type: ignore[attr-defined]
            if crs is not None:
                epsg = crs.to_epsg()
                if epsg is not None:
                    return int(epsg)
        except Exception:
            pass

    if "crs" in attrs:
        try:
            import pyproj

            epsg = pyproj.CRS.from_user_input(attrs["crs"]).to_epsg()
            if epsg is not None:
                return int(epsg)
        except Exception:
            # As a fallback, try to parse integers out of common strings like "EPSG:4326"
            match = re.search(r"(\d{3,5})", str(attrs["crs"]))
            if match:
                try:
                    return int(match.group(1))
                except Exception:
                    pass

    return None


def assert_provenance_attrs(
    obj: xr.Dataset | xr.DataArray,
    *,
    expected_source: str | None = None,
    expected_is_synthetic: bool | None = None,
    require_freq: bool = False,
) -> None:
    attrs = getattr(obj, "attrs", {})
    required = {"source", "is_synthetic", "requested_start", "requested_end"}
    if require_freq:
        required.add("freq")
    missing = required.difference(attrs)
    assert not missing, f"Missing provenance attrs: {sorted(missing)}"

    if expected_source is not None:
        assert attrs.get("source") == expected_source, f"Expected source={expected_source!r}"
    if expected_is_synthetic is not None:
        assert attrs.get("is_synthetic") is expected_is_synthetic, (
            f"Expected is_synthetic={expected_is_synthetic!r}"
        )


def assert_not_all_nan(obj: xr.Dataset | xr.DataArray, var: str | None = None) -> None:
    da = _select_dataarray(obj, var)
    data = np.asarray(da.values)
    assert np.isfinite(data).any(), "All values are NaN or non-finite"


__all__ = [
    "assert_spatiotemporal_cube_contract",
    "assert_provenance_attrs",
    "assert_not_all_nan",
    "infer_epsg_like",
]
