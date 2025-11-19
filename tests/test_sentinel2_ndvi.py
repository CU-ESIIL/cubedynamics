"""Smoke tests for the Sentinel-2 NDVI convenience loader."""

from __future__ import annotations

import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v

pytestmark = pytest.mark.online


def _load_s2_ndvi_cube():
    pytest.importorskip("cubo", reason="cubo client is required for Sentinel-2 online tests")
    from cubedynamics.data.sentinel2 import load_s2_ndvi_cube

    return load_s2_ndvi_cube


@pytest.mark.online
def test_load_s2_ndvi_cube_smoke() -> None:
    load_helper = _load_s2_ndvi_cube()
    try:
        ndvi = load_helper(
            lat=43.89,
            lon=-102.18,
            start="2023-06-01",
            end="2023-06-05",
            edge_size=64,
            resolution=10,
            cloud_lt=80,
            chunks={"time": 4, "y": 32, "x": 32},
        )
    except Exception as exc:  # pragma: no cover - network dependent
        pytest.skip(f"Sentinel-2 streaming unavailable: {exc}")

    assert isinstance(ndvi, xr.DataArray)
    assert ndvi.name == "ndvi"
    for dim in ("time", "y", "x"):
        assert dim in ndvi.dims
        assert ndvi.sizes[dim] >= 1


@pytest.mark.online
def test_ndvi_variance_pipeline_smoke() -> None:
    load_helper = _load_s2_ndvi_cube()
    try:
        ndvi = load_helper(
            lat=43.89,
            lon=-102.18,
            start="2023-06-01",
            end="2023-06-10",
            edge_size=64,
            resolution=10,
            cloud_lt=80,
            chunks={"time": 4, "y": 32, "x": 32},
        )
    except Exception as exc:  # pragma: no cover - network dependent
        pytest.skip(f"Sentinel-2 streaming unavailable: {exc}")

    ndvi_var = (
        pipe(ndvi)
        | v.month_filter([6])
        | v.variance(dim="time", keep_dim=False)
    ).unwrap()

    assert isinstance(ndvi_var, xr.DataArray)
    assert ndvi_var.dims == ("y", "x")
    assert ndvi_var.sizes["y"] >= 1 and ndvi_var.sizes["x"] >= 1
