"""Unit tests for the Sentinel-2 Sentinel helper family."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
SRC_STR = str(SRC_PATH)
if SRC_STR in sys.path:
    sys.path.remove(SRC_STR)
sys.path.insert(0, SRC_STR)

import cubedynamics
from cubedynamics.sentinel import (
    load_sentinel2_bands_cube,
    load_sentinel2_cube,
    load_sentinel2_ndvi_cube,
    load_sentinel2_ndvi_zscore_cube,
)


class DummyCubo:
    """Minimal cubo shim that returns deterministic cubes."""

    @staticmethod
    def create(**kwargs):
        rng = np.random.default_rng(0)
        time = np.arange(3)
        y = np.arange(4)
        x = np.arange(5)
        bands = kwargs.get("bands", ["B02", "B03", "B04", "B08"])
        data = rng.random((len(time), len(y), len(x), len(bands))).astype(np.float32)
        return xr.DataArray(
            data,
            coords={"time": time, "y": y, "x": x, "band": bands},
            dims=("time", "y", "x", "band"),
            name="reflectance",
        )


@pytest.fixture(autouse=True)
def patch_cubo(monkeypatch):
    import cubedynamics.sentinel as sentinel_mod

    monkeypatch.setattr(sentinel_mod, "cubo", DummyCubo)
    return sentinel_mod


def test_public_api_exposes_loader():
    assert hasattr(cubedynamics, "load_sentinel2_cube")
    assert hasattr(cubedynamics, "load_sentinel2_bands_cube")
    assert hasattr(cubedynamics, "load_sentinel2_ndvi_cube")
    assert hasattr(cubedynamics, "load_sentinel2_ndvi_zscore_cube")


def test_load_sentinel2_cube_all_bands():
    s2 = load_sentinel2_cube(40.0, -105.25, "2018-01-01", "2018-01-31")
    assert s2.dims == ("time", "y", "x", "band")
    assert set(s2.coords["band"].values) == {"B02", "B03", "B04", "B08"}


def test_load_sentinel2_bands_cube_subset():
    bands = ["B04", "B08"]
    s2 = load_sentinel2_bands_cube(
        40.0,
        -105.25,
        "2018-01-01",
        "2018-01-31",
        bands=bands,
    )
    assert s2.dims == ("time", "y", "x", "band")
    assert set(s2.coords["band"].values) == set(bands)


def test_load_sentinel2_bands_cube_requires_band_list():
    with pytest.raises(ValueError):
        load_sentinel2_bands_cube(40.0, -105.25, "2018-01-01", "2018-01-31", bands=[])


def test_load_sentinel2_ndvi_cube_returns_raw_ndvi():
    ndvi = load_sentinel2_ndvi_cube(
        lat=40.0,
        lon=-105.25,
        start="2018-01-01",
        end="2018-12-31",
    )

    assert ndvi.dims == ("time", "y", "x")
    assert ndvi.name == "ndvi"
    assert float(ndvi.max()) <= 1.0
    assert float(ndvi.min()) >= -1.0


def test_load_sentinel2_ndvi_cube_return_raw():
    raw_s2, ndvi = load_sentinel2_ndvi_cube(
        lat=40.0,
        lon=-105.25,
        start="2018-01-01",
        end="2018-12-31",
        return_raw=True,
    )

    assert raw_s2.dims == ("time", "y", "x", "band")
    assert set(raw_s2.coords["band"].values) == {"B04", "B08"}
    assert ndvi.shape == raw_s2.sel(band="B08").shape


def test_load_sentinel2_ndvi_zscore_cube_returns_standardized_cube():
    ndvi_z = load_sentinel2_ndvi_zscore_cube(
        lat=40.0,
        lon=-105.25,
        start="2018-01-01",
        end="2018-12-31",
    )

    assert ndvi_z.dims == ("time", "y", "x")
    mean_over_time = ndvi_z.mean(dim="time")
    assert float(mean_over_time.max()) < 1e-5
    assert float(mean_over_time.min()) > -1e-5
