import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.streaming import VirtualCube, make_spatial_tiler, make_time_tiler
from cubedynamics import variables


def _make_base_cube():
    times = pd.date_range("2000-01-01", periods=4, freq="D")
    y = np.arange(2)
    x = np.arange(3)
    data = np.arange(times.size * y.size * x.size).reshape(times.size, y.size, x.size)
    return xr.DataArray(data, coords={"time": times, "y": y, "x": x}, dims=("time", "y", "x"), name="fake")


def _tile_loader_factory(full: xr.DataArray):
    final_end = pd.to_datetime(full.time.values[-1])

    def loader(start=None, end=None, bbox=None, **_kwargs):
        da = full
        if start is not None or end is not None:
            start_ts = pd.to_datetime(start) if start is not None else pd.to_datetime(da.time.values[0])
            end_ts = pd.to_datetime(end) if end is not None else final_end
            selector = (da.time >= start_ts) & (da.time < end_ts)
            if end_ts >= final_end:
                selector = (da.time >= start_ts) & (da.time <= end_ts)
            da = da.sel(time=selector)

        if bbox is not None:
            xmin, ymin, xmax, ymax = bbox
            x_mask = (da.x >= xmin) & ((da.x < xmax) | ((da.x <= xmax) & (xmax >= da.x.max())))
            y_mask = (da.y >= ymin) & ((da.y < ymax) | ((da.y <= ymax) & (ymax >= da.y.max())))
            da = da.sel(x=x_mask, y=y_mask)

        return da

    return loader


def test_virtual_cube_variance_over_time_matches_materialized():
    base = _make_base_cube()
    loader = _tile_loader_factory(base)
    vc = VirtualCube(
        dims=("time", "y", "x"),
        coords_metadata={},
        loader=loader,
        loader_kwargs={"start": base.time.values[0], "end": base.time.values[-1]},
        time_tiler=make_time_tiler(base.time.values[0], base.time.values[-1], freq="2D"),
        spatial_tiler=lambda _kw: ({} for _ in [None]),
    )

    streamed = (pipe(vc) | v.variance(dim="time", keep_dim=False)).unwrap()
    expected = base.var(dim="time")
    xr.testing.assert_allclose(streamed, expected)


def test_virtual_cube_variance_over_space_matches_materialized():
    base = _make_base_cube()
    loader = _tile_loader_factory(base)
    vc = VirtualCube(
        dims=("time", "y", "x"),
        coords_metadata={},
        loader=loader,
        loader_kwargs={},
        time_tiler=lambda _kw: ({} for _ in [None]),
        spatial_tiler=lambda _kw: ({} for _ in [None]),
    )

    streamed = (pipe(vc) | v.variance(dim=("y", "x"), keep_dim=False)).unwrap()
    expected = base.var(dim=("y", "x"))
    xr.testing.assert_allclose(streamed, expected)


def test_temperature_streaming_strategy(monkeypatch):
    base = _make_base_cube()

    def fake_loader(**kwargs):
        da = base
        start = kwargs.get("start")
        end = kwargs.get("end")
        if start is not None or end is not None:
            da = da.sel(time=slice(start, end))
        return da

    monkeypatch.setattr(variables, "_load_temperature", fake_loader)

    materialized = variables.temperature(
        lat=40.0,
        lon=-105.0,
        start=base.time.values[0],
        end=base.time.values[-1],
        streaming_threshold=1e9,
    )
    assert isinstance(materialized, xr.DataArray)

    virtual = variables.temperature(
        lat=40.0,
        lon=-105.0,
        start=base.time.values[0],
        end=base.time.values[-1],
        streaming_strategy="virtual",
    )
    assert isinstance(virtual, VirtualCube)
    xr.testing.assert_allclose(virtual.materialize(), base)
