"""Online tests for the GRIDMET loader."""

from __future__ import annotations

import pytest
import xarray as xr

from climate_cube_math.data.gridmet import load_gridmet_cube

from tests.conftest import assert_is_lazy_xarray


pytestmark = [pytest.mark.online, pytest.mark.integration]


@pytest.mark.online
def test_load_gridmet_cube_streaming_default(recwarn):
    aoi = {
        "min_lon": -105.4,
        "max_lon": -105.3,
        "min_lat": 40.0,
        "max_lat": 40.1,
    }

    ds = load_gridmet_cube(
        variables=["tmax"],
        start="2000-01-01",
        end="2000-01-10",
        aoi=aoi,
        prefer_streaming=True,
    )

    assert isinstance(ds, xr.Dataset)
    assert "time" in ds.dims
    assert "y" in ds.dims
    assert "x" in ds.dims
    assert "tmax" in ds.data_vars

    assert_is_lazy_xarray(ds)
    assert not any(
        "GRIDMET streaming backend unavailable" in str(w.message) for w in recwarn
    )


@pytest.mark.online
def test_load_gridmet_cube_fallback_download(monkeypatch, recwarn):
    import climate_cube_math.data.gridmet as gridmet_mod

    def _always_fail(*args, **kwargs):  # pragma: no cover - used in test
        raise RuntimeError("streaming backend offline for test")

    monkeypatch.setattr(gridmet_mod, "_open_gridmet_streaming", _always_fail)

    aoi = {
        "min_lon": -105.4,
        "max_lon": -105.3,
        "min_lat": 40.0,
        "max_lat": 40.1,
    }

    ds = load_gridmet_cube(
        variables=["tmax"],
        start="2000-01-01",
        end="2000-01-03",
        aoi=aoi,
        prefer_streaming=True,
    )

    assert isinstance(ds, xr.Dataset)
    assert "tmax" in ds.data_vars
    assert any(
        "GRIDMET streaming backend unavailable" in str(w.message) for w in recwarn
    )
