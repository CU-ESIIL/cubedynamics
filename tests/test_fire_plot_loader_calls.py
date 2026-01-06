import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
import xarray as xr
from shapely.geometry import box

from cubedynamics.verbs import fire as fire_verbs

from tests.helpers.contracts import assert_not_all_nan, assert_spatiotemporal_cube_contract


def _fired_daily_fixture():
    dates = pd.date_range("2020-07-01", periods=3, freq="D")
    geoms = [box(-105.1, 40.0, -105.0, 40.1) for _ in dates]
    return gpd.GeoDataFrame({"id": [1, 1, 1], "date": dates, "geometry": geoms}, crs="EPSG:4326")


def _stub_dataset(var: str, start, end, freq: str, source: str = "gridmet_streaming") -> xr.Dataset:
    times = pd.date_range(start, end, freq=freq)
    data = np.ones((len(times), 1, 1))
    da = xr.DataArray(
        data,
        coords={"time": times, "y": [40.0], "x": [-105.0]},
        dims=("time", "y", "x"),
        name=var,
    )
    ds = xr.Dataset({var: da})
    ds.attrs.update(
        {
            "source": source,
            "is_synthetic": False,
            "freq": freq,
            "requested_start": str(start),
            "requested_end": str(end),
        }
    )
    return ds


def _patch_plot_and_hull(monkeypatch, dates_len: int):
    def _fake_hull(*args, **kwargs):
        return type(
            "Hull",
            (),
            {
                "metrics": {"days": dates_len},
                "verts_km": np.zeros((3, 3)),
                "tris": np.array([[0, 1, 2]]),
                "t_days_vert": np.array([1.0, 2.0, 3.0]),
            },
        )

    monkeypatch.setattr(fire_verbs, "compute_time_hull_geometry", _fake_hull)
    monkeypatch.setattr(fire_verbs, "plot_climate_filled_hull", lambda *args, **kwargs: "fig")


@pytest.mark.parametrize("freq_override", [None, "MS"])
def test_fire_plot_legacy_gridmet_freq(monkeypatch, freq_override):
    fired_daily = _fired_daily_fixture()
    calls = {}

    def _fake_loader(*, lat, lon, start, end, variable=None, freq=None, **kwargs):
        calls["freq"] = freq
        calls["allow_synthetic"] = kwargs.get("allow_synthetic")
        return _stub_dataset(variable or "vpd", start, end, freq or "D")

    _patch_plot_and_hull(monkeypatch, len(fired_daily))
    monkeypatch.setattr("cubedynamics.data.gridmet.load_gridmet_cube", _fake_loader)

    results = fire_verbs.fire_plot(
        fired_daily=fired_daily,
        event_id=1,
        climate_variable="vpd",
        freq=freq_override,
        time_buffer_days=0,
        allow_synthetic=False,
        prefer_streaming=False,
    )

    expected_freq = freq_override or "D"
    assert calls["freq"] == expected_freq
    assert calls["allow_synthetic"] is False
    cube = results["cube"].da
    assert_spatiotemporal_cube_contract(cube)
    assert cube.attrs.get("freq") == expected_freq
    assert_not_all_nan(cube)


@pytest.mark.parametrize("freq_override", [None, "MS"])
def test_fire_plot_legacy_prism_freq(monkeypatch, freq_override):
    fired_daily = _fired_daily_fixture()
    calls = {}

    def _fake_loader(*, lat, lon, start, end, variable=None, freq=None, **kwargs):
        calls["freq"] = freq
        calls["allow_synthetic"] = kwargs.get("allow_synthetic")
        return _stub_dataset(variable or "ppt", start, end, freq or "D", source="prism_streaming")

    _patch_plot_and_hull(monkeypatch, len(fired_daily))
    monkeypatch.setattr("cubedynamics.data.prism.load_prism_cube", _fake_loader)

    results = fire_verbs.fire_plot(
        fired_daily=fired_daily,
        event_id=1,
        climate_variable="ppt",
        freq=freq_override,
        time_buffer_days=0,
        allow_synthetic=False,
        prefer_streaming=False,
    )

    expected_freq = freq_override or "D"
    assert calls["freq"] == expected_freq
    assert calls["allow_synthetic"] is False
    cube = results["cube"].da
    assert_spatiotemporal_cube_contract(cube)
    assert cube.attrs.get("freq") == expected_freq
    assert cube.attrs.get("source") == "prism_streaming"
    assert_not_all_nan(cube)
