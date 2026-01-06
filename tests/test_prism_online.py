"""Online tests for the PRISM loader."""

from __future__ import annotations

import pytest
import xarray as xr

from cubedynamics.data.prism import load_prism_cube

from tests.conftest import assert_is_lazy_xarray


pytestmark = [pytest.mark.online, pytest.mark.integration]


@pytest.mark.online
def test_load_prism_cube_streaming_default(recwarn):
    aoi = {
        "min_lon": -105.4,
        "max_lon": -105.3,
        "min_lat": 40.0,
        "max_lat": 40.1,
    }

    ds = load_prism_cube(
        variables=["ppt"],
        start="2000-01-01",
        end="2000-12-31",
        aoi=aoi,
        prefer_streaming=True,
    )

    assert isinstance(ds, xr.Dataset)
    assert "time" in ds.dims
    assert "y" in ds.dims
    assert "x" in ds.dims
    assert "ppt" in ds.data_vars

    assert_is_lazy_xarray(ds)
    assert not any(
        "PRISM streaming backend unavailable" in str(w.message) for w in recwarn
    )


@pytest.mark.online
def test_load_prism_cube_fallback_download(monkeypatch, recwarn):
    import cubedynamics.data.prism as prism_mod

    def _always_fail(*args, **kwargs):  # pragma: no cover - used in test
        raise RuntimeError("streaming backend offline for test")

    monkeypatch.setattr(prism_mod, "_open_prism_streaming", _always_fail)

    aoi = {
        "min_lon": -105.4,
        "max_lon": -105.3,
        "min_lat": 40.0,
        "max_lat": 40.1,
    }

    ds = load_prism_cube(
        variables=["ppt"],
        start="2000-01-01",
        end="2000-03-31",
        aoi=aoi,
        prefer_streaming=True,
    )

    assert isinstance(ds, xr.Dataset)
    assert "ppt" in ds.data_vars
    assert any(
        "PRISM streaming backend unavailable" in str(w.message) for w in recwarn
    )
