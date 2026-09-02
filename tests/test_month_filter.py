"""Supported calendar filtering and legacy forwarding, without remote data."""
import warnings

import dask.array as da
from dask.callbacks import Callback
import numpy as np
import pandas as pd
import pytest
import xarray as xr

import cubedynamics
from cubedynamics import pipe, verbs as v
from cubedynamics.ops import month_filter as old_ops_filter
from cubedynamics.ops.transforms import month_filter as old_transform_filter


@pytest.fixture
def cube():
    return xr.DataArray(da.arange(90, chunks=15), dims="time",
        coords={"time": pd.date_range("2024-01-01", periods=90)},
        name="temperature", attrs={"units": "degC", "source": "unit-test input"})


@pytest.mark.parametrize("as_dataset", [False, True])
def test_supported_filter_direct_pipe_and_lazy(cube, as_dataset):
    value = cube.to_dataset() if as_dataset else cube
    tasks = []
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        with Callback(pretask=lambda *args: tasks.append(args)):
            stage = v.month_filter(iter([2]))
            direct = stage(value)
            piped = (pipe(value) | stage).unwrap()
    assert not tasks
    assert isinstance((direct.temperature if as_dataset else direct).data, da.Array)
    xr.testing.assert_identical(direct, piped)
    expected = value.where(value.time.dt.month == 2, drop=True)
    expected.attrs["selected_calendar_months"] = "2"
    xr.testing.assert_identical(direct, expected)
    assert direct.sizes["time"] == 29


@pytest.mark.parametrize("legacy", [old_ops_filter, old_transform_filter, cubedynamics.month_filter])
def test_legacy_paths_warn_and_forward(legacy, cube):
    with pytest.warns(DeprecationWarning, match="use cubedynamics.verbs.month_filter") as caught:
        result = legacy([1])(cube)
    assert len(caught) == 1
    xr.testing.assert_identical(result, v.month_filter([1])(cube))


@pytest.mark.parametrize("months", [[], [12], [0, 13]])
def test_empty_selection_keeps_historical_behavior(cube, months):
    assert v.month_filter(months)(cube).sizes["time"] == 0


def test_filter_preserves_historical_coercion(cube):
    xr.testing.assert_identical(v.month_filter(["2"])(cube), v.month_filter([2])(cube))


@pytest.mark.parametrize("value, message", [
    (xr.DataArray([1], dims="x"), "requires a 'time'"),
    (xr.DataArray([1], dims="time", coords={"time": [0]}), "datetime-like"),
])
def test_invalid_coordinates_fail_clearly(value, message):
    with pytest.raises(ValueError, match=message):
        v.month_filter([1])(value)
