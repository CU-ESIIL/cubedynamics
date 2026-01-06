import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics.data.gridmet import load_gridmet_cube


@pytest.mark.parametrize("allow_synthetic", [False, True])
def test_gridmet_empty_time_handling(allow_synthetic):
    start = "2018-07-17"
    end = "2018-07-25"

    if not allow_synthetic:
        with pytest.raises(RuntimeError, match="freq='MS'"):
            load_gridmet_cube(
                lat=40.0,
                lon=-105.0,
                start=start,
                end=end,
                variable="tmmx",
                freq="MS",
                prefer_streaming=False,
                show_progress=False,
                allow_synthetic=False,
            )
    else:
        ds = load_gridmet_cube(
            lat=40.0,
            lon=-105.0,
            start=start,
            end=end,
            variable="tmmx",
            freq="MS",
            prefer_streaming=False,
            show_progress=False,
            allow_synthetic=True,
        )
        assert ds.sizes.get("time", 0) > 0
        assert ds.attrs.get("is_synthetic") is True
        assert ds.attrs.get("source") == "synthetic"
        assert "freq" in ds.attrs
        assert "backend_error" in ds.attrs


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


@pytest.mark.filterwarnings("ignore:Positional GRIDMET arguments")
def test_fire_plot_daily_default(monkeypatch, _fake_gridmet):
    import geopandas as gpd
    from shapely.geometry import box

    from cubedynamics.verbs import fire as fire_verbs

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
    assert cube.sizes.get("time", 0) > 0
    assert cube.attrs.get("freq") == "D"
    assert cube.attrs.get("source") == "gridmet_streaming"
