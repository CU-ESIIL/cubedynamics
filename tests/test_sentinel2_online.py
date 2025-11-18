"""Online tests that hit cubo for Sentinel-2 data."""

from __future__ import annotations

import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.indices.vegetation import compute_ndvi_from_s2

pytestmark = pytest.mark.online


def _load_s2_cube():
    pytest.importorskip("cubo", reason="cubo client is required for Sentinel-2 online tests")
    from cubedynamics.data.sentinel2 import load_s2_cube

    return load_s2_cube


@pytest.mark.online
def test_load_s2_cube_smoke() -> None:
    load_s2_cube = _load_s2_cube()
    s2 = load_s2_cube(
        lat=43.89,
        lon=-102.18,
        start="2023-06-01",
        end="2023-06-03",
        edge_size=64,
        resolution=10,
        cloud_lt=80,
    )
    assert isinstance(s2, xr.DataArray)
    for dim in ("time", "band", "y", "x"):
        assert dim in s2.dims
    assert s2.sizes["y"] > 0 and s2.sizes["x"] > 0
    assert s2.sizes["time"] >= 1


@pytest.mark.online
def test_s2_ndvi_zscore_pipeline_smoke() -> None:
    load_s2_cube = _load_s2_cube()
    s2 = load_s2_cube(
        lat=43.89,
        lon=-102.18,
        start="2023-06-01",
        end="2023-06-10",
        edge_size=64,
        resolution=10,
        cloud_lt=80,
    )
    ndvi = compute_ndvi_from_s2(s2)
    ndvi_z = (
        pipe(s2)
        | v.ndvi_from_s2()
        | v.zscore(dim="time")
    ).unwrap()

    assert ndvi_z.ndim == 3
    assert ndvi_z.dims == ("time", "y", "x")
    assert ndvi_z.sizes["time"] >= 1
