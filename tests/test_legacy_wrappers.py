import numpy as np
import pytest
import xarray as xr

import cubedynamics as cd
import cubedynamics.sentinel as sentinel


def test_sentinel_wrapper_warns_and_delegates(monkeypatch):
    called = {}

    def fake_load_s2_cube(**kwargs):
        called["kwargs"] = kwargs
        return xr.DataArray(
            np.zeros((1, 1, 1, 1)), dims=("time", "y", "x", "band")
        )

    monkeypatch.setattr(sentinel, "load_s2_cube", fake_load_s2_cube)

    with pytest.warns(DeprecationWarning):
        result = sentinel.load_sentinel2_cube(
            40.0,
            -105.0,
            "2020-01-01",
            "2020-02-01",
            bands=["B02", "B03"],
        )

    assert called["kwargs"]["bands"] == ["B02", "B03"]
    assert result.dims == ("time", "y", "x", "band")


def test_ops_fire_time_hull_wrapper_warns(monkeypatch):
    sentinel = {}

    def fake_build(*args, **kwargs):
        sentinel["called"] = (args, kwargs)
        return "wrapped"

    monkeypatch.setattr(cd.fire_time_hull, "build_fire_event", fake_build)

    from cubedynamics.ops_fire import time_hull

    with pytest.warns(DeprecationWarning):
        result = time_hull.build_fire_event("evt", min_days=5)

    assert sentinel["called"] == (("evt",), {"min_days": 5})
    assert result == "wrapped"
