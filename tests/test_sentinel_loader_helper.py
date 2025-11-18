"""Unit tests for the Sentinel-2 NDVI helper."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import xarray as xr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
SRC_STR = str(SRC_PATH)
if SRC_STR in sys.path:
    sys.path.remove(SRC_STR)
sys.path.insert(0, SRC_STR)

import cubedynamics
from cubedynamics.sentinel import load_sentinel2_ndvi_cube


class DummyCubo:
    """Minimal cubo shim that returns a deterministic cube."""

    @staticmethod
    def create(**kwargs):
        rng = np.random.default_rng(0)
        time = np.arange(3)
        y = np.arange(4)
        x = np.arange(5)
        band = ["B04", "B08"]
        data = rng.random((len(time), len(y), len(x), len(band))).astype(np.float32)
        return xr.DataArray(
            data,
            coords={"time": time, "y": y, "x": x, "band": band},
            dims=("time", "y", "x", "band"),
            name="reflectance",
        )


def test_public_api_exposes_loader():
    assert hasattr(cubedynamics, "load_sentinel2_ndvi_cube")


def test_load_sentinel2_ndvi_cube_returns_zscores(monkeypatch):
    import cubedynamics.sentinel as sentinel_mod

    monkeypatch.setattr(sentinel_mod, "cubo", DummyCubo)

    ndvi_z = load_sentinel2_ndvi_cube(
        lat=40.0,
        lon=-105.25,
        start="2018-01-01",
        end="2018-12-31",
    )

    assert ndvi_z.dims == ("time", "y", "x")
    assert ndvi_z.name == "ndvi_zscore"
    mean_over_time = ndvi_z.mean(dim="time")
    assert mean_over_time.max().item() < 1e-6
    assert mean_over_time.min().item() > -1e-6


def test_load_sentinel2_ndvi_cube_return_raw(monkeypatch):
    import cubedynamics.sentinel as sentinel_mod

    monkeypatch.setattr(sentinel_mod, "cubo", DummyCubo)

    raw_s2, ndvi, ndvi_z = load_sentinel2_ndvi_cube(
        lat=40.0,
        lon=-105.25,
        start="2018-01-01",
        end="2018-12-31",
        return_raw=True,
    )

    assert raw_s2.dims == ("time", "y", "x", "band")
    assert set(raw_s2.coords["band"].values) == {"B04", "B08"}
    assert ndvi.shape == raw_s2.sel(band="B08").shape
    assert ndvi_z.shape == ndvi.shape
