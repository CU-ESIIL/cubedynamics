import os

import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v

pytestmark = pytest.mark.skipif(
    os.getenv("CUBEDYNAMICS_TEST_LANDSAT_MPC") != "1",
    reason="Set CUBEDYNAMICS_TEST_LANDSAT_MPC=1 to run Landsat MPC tests",
)


def test_landsat8_mpc_basic():
    bbox = [-105.35, 39.9, -105.15, 40.1]
    cube = (
        pipe(None)
        | v.landsat8_mpc(
            bbox=bbox,
            start="2019-07-01",
            end="2019-07-10",
            band_aliases=("red", "nir"),
            max_cloud_cover=50,
            chunks_xy={"x": 2048, "y": 2048},
        )
    ).unwrap()

    assert isinstance(cube, xr.DataArray)
    assert set(cube.dims) == {"time", "band", "y", "x"}
    assert "band" in cube.coords
    assert {"red", "nir"}.issubset(set(cube["band"].values))
    assert cube.dtype == "float32"
    assert cube.sizes["time"] >= 1


def test_landsat8_mpc_ndvi_simple():
    bbox = [-105.35, 39.9, -105.15, 40.1]
    cube = (
        pipe(None)
        | v.landsat8_mpc(bbox=bbox, start="2019-07-01", end="2019-07-10")
    ).unwrap()

    red = cube.sel(band="red")
    nir = cube.sel(band="nir")
    ndvi = (nir - red) / (nir + red)
    assert ndvi.ndim == 3  # (time, y, x)
    assert (ndvi.isfinite().sum() > 0).item()
