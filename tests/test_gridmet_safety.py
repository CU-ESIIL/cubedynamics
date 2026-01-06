import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics.data.gridmet import load_gridmet_cube
from cubedynamics.verbs import fire as fire_verbs

from tests.helpers.contracts import (
    assert_not_all_nan,
    assert_provenance_attrs,
    assert_spatiotemporal_cube_contract,
)


@pytest.fixture()
def _fake_gridmet(monkeypatch):
    calls = {}

    def _fake_loader(*, lat, lon, start, end, variable=None, freq=None, **kwargs):
        calls["freq"] = freq
        times = pd.date_range(start, end, freq="D")
        data = np.ones((len(times), 1, 1))
        da = xr.DataArray(
            data,
            coords={"time": times, "y": [lat], "x": [lon]},
            dims=("time", "y", "x"),
            name=variable or "vpd",
        )
        ds = xr.Dataset({da.name: da})
        ds.attrs.update(
            {
                "source": "gridmet_streaming",
                "is_synthetic": False,
                "freq": freq,
                "requested_start": str(start),
                "requested_end": str(end),
            }
        )
        return ds

    monkeypatch.setattr("cubedynamics.data.gridmet.load_gridmet_cube", _fake_loader)
    return calls


def _empty_time_dataset(variable: str = "vpd") -> xr.Dataset:
    coords = {"time": pd.DatetimeIndex([]), "y": np.array([0.0, 1.0]), "x": np.array([0.0, 1.0])}
    data = xr.DataArray(
        np.empty((0, 2, 2)),
        coords=coords,
        dims=("time", "y", "x"),
        name=variable,
    )
    return xr.Dataset({variable: data})


def _all_nan_dataset(variable: str = "vpd") -> xr.Dataset:
    coords = {
        "time": pd.date_range("2018-07-17", periods=3, freq="D"),
        "y": np.array([0.0, 1.0]),
        "x": np.array([0.0, 1.0]),
    }
    data = xr.DataArray(
        np.full((3, 2, 2), np.nan),
        coords=coords,
        dims=("time", "y", "x"),
        name=variable,
    )
    return xr.Dataset({variable: data})


def test_gridmet_freq_ms_short_window_raises_when_not_allowed(monkeypatch):
    def _stub_streaming(*args, **kwargs):
        return _empty_time_dataset()

    monkeypatch.setattr("cubedynamics.data.gridmet._open_gridmet_streaming", _stub_streaming)

    with pytest.raises(RuntimeError, match="empty time.*freq.*MS"):
        load_gridmet_cube(
            lat=40.0,
            lon=-105.0,
            start="2018-07-17",
            end="2018-07-25",
            variable="vpd",
            freq="MS",
            prefer_streaming=True,
            show_progress=False,
            allow_synthetic=False,
        )


def test_gridmet_freq_ms_short_window_allows_synthetic_when_allowed(monkeypatch):
    def _stub_streaming(*args, **kwargs):
        return _empty_time_dataset()

    monkeypatch.setattr("cubedynamics.data.gridmet._open_gridmet_streaming", _stub_streaming)

    ds = load_gridmet_cube(
        lat=40.0,
        lon=-105.0,
        start="2018-07-17",
        end="2018-07-25",
        variable="vpd",
        freq="MS",
        prefer_streaming=True,
        show_progress=False,
        allow_synthetic=True,
    )

    assert_spatiotemporal_cube_contract(ds)
    assert_provenance_attrs(
        ds,
        expected_source="synthetic",
        expected_is_synthetic=True,
        require_freq=True,
    )
    assert "empty time" in ds.attrs.get("backend_error", "")
    assert "freq" in ds.attrs.get("backend_error", "")


@pytest.mark.parametrize("allow_synthetic", [False, True])
def test_gridmet_all_nan_handling(monkeypatch, allow_synthetic):
    def _stub_streaming(*args, **kwargs):
        return _all_nan_dataset()

    monkeypatch.setattr("cubedynamics.data.gridmet._open_gridmet_streaming", _stub_streaming)

    if not allow_synthetic:
        with pytest.raises(RuntimeError, match="all-NaN"):
            load_gridmet_cube(
                lat=40.0,
                lon=-105.0,
                start="2018-07-17",
                end="2018-07-25",
                variable="vpd",
                prefer_streaming=True,
                show_progress=False,
                allow_synthetic=False,
            )
    else:
        ds = load_gridmet_cube(
            lat=40.0,
            lon=-105.0,
            start="2018-07-17",
            end="2018-07-25",
            variable="vpd",
            prefer_streaming=True,
            show_progress=False,
            allow_synthetic=True,
        )
        assert_spatiotemporal_cube_contract(ds)
        assert_provenance_attrs(
            ds,
            expected_source="synthetic",
            expected_is_synthetic=True,
            require_freq=True,
        )
        assert_not_all_nan(ds)
        assert "all-NaN" in ds.attrs.get("backend_error", "")


@pytest.mark.filterwarnings("ignore:Positional GRIDMET arguments")
def test_fire_plot_daily_default(monkeypatch, _fake_gridmet):
    import geopandas as gpd
    from shapely.geometry import box

    dates = pd.date_range("2020-07-01", periods=3, freq="D")
    geoms = [box(-105.1, 40.0, -105.0, 40.1) for _ in dates]
    fired_daily = gpd.GeoDataFrame({"id": [1, 1, 1], "date": dates, "geometry": geoms}, crs="EPSG:4326")

    def _fake_hull(*args, **kwargs):
        return type(
            "Hull",
            (),
            {
                "metrics": {"days": len(dates)},
                "verts_km": np.zeros((3, 3)),
                "tris": np.array([[0, 1, 2]]),
                "t_days_vert": np.array([1.0, 2.0, 3.0]),
            },
        )

    monkeypatch.setattr(fire_verbs, "compute_time_hull_geometry", _fake_hull)
    monkeypatch.setattr(fire_verbs, "plot_climate_filled_hull", lambda *args, **kwargs: "fig")

    results = fire_verbs.fire_plot(
        fired_daily=fired_daily,
        event_id=1,
        climate_variable="vpd",
        time_buffer_days=0,
        allow_synthetic=False,
        prefer_streaming=False,
    )

    assert _fake_gridmet["freq"] == "D"
    cube = results["cube"].da
    assert_spatiotemporal_cube_contract(cube)
    assert cube.attrs.get("freq") == "D"
    assert cube.attrs.get("source") == "gridmet_streaming"
    assert_not_all_nan(cube)
