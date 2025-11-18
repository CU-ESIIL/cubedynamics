"""Tests for the ggplot-style pipe syntax and verbs."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

import cubedynamics.viz as viz
from cubedynamics import pipe, verbs as v


def _make_time_series(count: int = 12):
    time = pd.date_range("2000-01-01", periods=count, freq="MS")
    data = xr.DataArray(
        np.arange(count, dtype=float),
        dims=("time",),
        coords={"time": time},
    )
    return data


def test_pipe_basic_chain():
    da = _make_time_series()

    result = (pipe(da) | v.anomaly(dim="time") | v.variance(dim="time")).unwrap()

    assert isinstance(result, xr.DataArray)
    assert result.dims == ()
    assert float(result) >= 0


def test_month_filter_reduces_time():
    da = _make_time_series(24)

    summer = (pipe(da) | v.month_filter([6, 7, 8])).unwrap()

    assert set(int(m) for m in summer["time"].dt.month.values) == {6, 7, 8}


def test_to_netcdf_roundtrip(tmp_path):
    da = _make_time_series()
    path = tmp_path / "out.nc"

    result = (pipe(da) | v.to_netcdf(path)).unwrap()

    assert path.exists()
    loaded = xr.load_dataarray(path)
    xr.testing.assert_identical(da, loaded)
    xr.testing.assert_identical(da, result)


def test_show_cube_lexcube_returns_original_cube(monkeypatch):
    da = _make_time_series()
    captured = {}

    def fake_show(cube, **kwargs):
        captured["cube"] = cube
        captured["kwargs"] = kwargs
        return "widget"

    monkeypatch.setattr(viz, "show_cube_lexcube", fake_show)

    result = (pipe(da) | v.show_cube_lexcube(cmap="Blues")).unwrap()

    assert result is da
    assert captured["cube"] is da
    assert captured["kwargs"] == {"cmap": "Blues"}
