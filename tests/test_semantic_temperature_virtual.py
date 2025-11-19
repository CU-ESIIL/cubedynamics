import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics import variables
from cubedynamics.streaming import VirtualCube


@pytest.fixture
def tiny_temp_cube():
    time = pd.date_range("2020-01-01", periods=2, freq="D")
    return xr.DataArray(
        data=np.arange(8).reshape(2, 2, 2),
        dims=("time", "y", "x"),
        coords={"time": time, "y": [0.0, 1.0], "x": [0.0, 1.0]},
        name="temp",
    )


def _patch_loader(monkeypatch, cube):
    def fake_loader(**kwargs):
        start = kwargs.get("start")
        end = kwargs.get("end")
        subset = cube
        if start is not None or end is not None:
            subset = subset.sel(time=slice(start, end))
        return subset

    monkeypatch.setattr(variables, "_load_temperature", fake_loader)


def test_temperature_streaming_strategy_materialize(monkeypatch, tiny_temp_cube):
    _patch_loader(monkeypatch, tiny_temp_cube)
    monkeypatch.setattr(variables, "estimate_cube_size", lambda *args, **kwargs: 1)

    temp = variables.temperature(lat=40.0, lon=-105.0, start="2020-01-01", end="2020-01-02", streaming_strategy="materialize")
    assert isinstance(temp, xr.DataArray)


def test_temperature_streaming_strategy_virtual(monkeypatch, tiny_temp_cube):
    _patch_loader(monkeypatch, tiny_temp_cube)
    monkeypatch.setattr(variables, "estimate_cube_size", lambda *args, **kwargs: 1e12)

    temp = variables.temperature(lat=40.0, lon=-105.0, start="2020-01-01", end="2020-01-02", streaming_strategy="virtual")
    assert isinstance(temp, VirtualCube)
    xr.testing.assert_allclose(temp.materialize(), tiny_temp_cube)


def test_temperature_streaming_strategy_auto_switches(monkeypatch, tiny_temp_cube):
    _patch_loader(monkeypatch, tiny_temp_cube)

    monkeypatch.setattr(variables, "estimate_cube_size", lambda *args, **kwargs: 1)
    small = variables.temperature(lat=40.0, lon=-105.0, start="2020-01-01", end="2020-01-02", streaming_strategy="auto")
    assert isinstance(small, xr.DataArray)

    monkeypatch.setattr(variables, "estimate_cube_size", lambda *args, **kwargs: 1e12)
    large = variables.temperature(lat=40.0, lon=-105.0, start="2020-01-01", end="2020-01-02", streaming_strategy="auto")
    assert isinstance(large, VirtualCube)
