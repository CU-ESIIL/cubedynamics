import numpy as np
import pandas as pd
import pytest
import xarray as xr

import cubedynamics as cd


def fake_cube(variable: str, *args, **kwargs) -> xr.DataArray:
    time = pd.date_range("2000-01-01", periods=3, freq="D")
    data = np.arange(len(time), dtype=float)
    da = xr.DataArray(data, coords={"time": time}, dims=("time",))
    da.attrs["variable"] = variable
    da.attrs["source_args"] = {"args": args, "kwargs": kwargs}
    return da


def test_temperature_uses_gridmet(monkeypatch):
    called = {}

    def fake_gridmet_loader(*args, **kwargs):
        variable = kwargs.pop("variable", "unknown")
        called["kwargs"] = dict(kwargs, variable=variable)
        return fake_cube(variable, *args, **kwargs).to_dataset(name=variable)

    monkeypatch.setattr(
        "cubedynamics.variables.load_gridmet_cube",
        fake_gridmet_loader,
    )

    da = cd.temperature(
        lat=40.0,
        lon=-105.25,
        start="2000-01-01",
        end="2000-01-03",
        source="gridmet",
    )

    assert isinstance(da, xr.DataArray)
    assert da.attrs["variable"] == "tmmx"
    assert called["kwargs"]["variable"] == "tmmx"


def test_temperature_uses_prism(monkeypatch):
    called = {}

    def fake_prism_loader(*args, **kwargs):
        variable = kwargs.pop("variable", "unknown")
        called["kwargs"] = dict(kwargs, variable=variable)
        return fake_cube(variable, *args, **kwargs).to_dataset(name=variable)

    monkeypatch.setattr(
        "cubedynamics.variables.load_prism_cube",
        fake_prism_loader,
    )

    da = cd.temperature(
        lat=40.0,
        lon=-105.25,
        start="2000-01-01",
        end="2000-01-03",
        source="prism",
    )

    assert isinstance(da, xr.DataArray)
    assert da.attrs["variable"] == "tmean"
    assert called["kwargs"]["variable"] == "tmean"


def test_temperature_min_and_max(monkeypatch):
    calls = {"gridmet": {}, "prism": {}}

    def fake_gridmet_loader(*args, **kwargs):
        variable = kwargs.pop("variable", "unknown")
        calls["gridmet"] = dict(kwargs, variable=variable)
        return fake_cube(variable, *args, **kwargs).to_dataset(name=variable)

    def fake_prism_loader(*args, **kwargs):
        variable = kwargs.pop("variable", "unknown")
        calls["prism"] = dict(kwargs, variable=variable)
        return fake_cube(variable, *args, **kwargs).to_dataset(name=variable)

    monkeypatch.setattr(
        "cubedynamics.variables.load_gridmet_cube",
        fake_gridmet_loader,
    )
    monkeypatch.setattr(
        "cubedynamics.variables.load_prism_cube",
        fake_prism_loader,
    )

    tmin = cd.temperature_min(lat=1.0, lon=2.0, start="2000-01-01", end="2000-01-03", source="gridmet")
    tmax = cd.temperature_max(lat=1.0, lon=2.0, start="2000-01-01", end="2000-01-03", source="prism")

    assert tmin.attrs["variable"] == "tmmn"
    assert calls["gridmet"]["variable"] == "tmmn"
    assert tmax.attrs["variable"] == "tmax"
    assert calls["prism"]["variable"] == "tmax"


def test_temperature_anomaly_mean_centered(monkeypatch):
    def fake_gridmet_loader(*args, **kwargs):
        variable = kwargs.pop("variable", "unknown")
        data = xr.DataArray(
            [1.0, 2.0, 3.0],
            coords={"time": pd.date_range("2000-01-01", periods=3, freq="D")},
            dims=("time",),
            attrs={"variable": variable},
        )
        return data.to_dataset(name=variable)

    monkeypatch.setattr(
        "cubedynamics.variables.load_gridmet_cube",
        fake_gridmet_loader,
    )

    anom = cd.temperature_anomaly(lat=0.0, lon=0.0, start="2000-01-01", end="2000-01-03", source="gridmet")

    assert np.allclose(float(anom.mean().compute()), 0.0)
    np.testing.assert_allclose(anom.values, np.array([-1.0, 0.0, 1.0]))


def test_ndvi_uses_sentinel_ndvi_helper(monkeypatch):
    called = {}

    def fake_ndvi_loader(*args, **kwargs):
        called["kwargs"] = kwargs
        time = pd.date_range("2020-01-01", periods=2, freq="D")
        da = xr.DataArray(
            np.zeros((2, 1, 1)),
            coords={"time": time, "y": [0], "x": [0]},
            dims=("time", "y", "x"),
        )
        return da

    monkeypatch.setattr(
        "cubedynamics.variables.load_sentinel2_ndvi_cube",
        fake_ndvi_loader,
    )

    out = cd.ndvi(
        lat=40.0,
        lon=-105.25,
        start="2020-01-01",
        end="2020-01-31",
        as_zscore=False,
    )

    assert isinstance(out, xr.DataArray)
    assert out.dims == ("time", "y", "x")
    assert called["kwargs"]["lat"] == 40.0
