"""Common pytest fixtures for cubedynamics tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr


@pytest.fixture
def tiny_cube() -> xr.DataArray:
    """Small synthetic cube for testing with dims (time=6, y=2, x=3)."""

    time = pd.date_range("2000-01-01", periods=6, freq="D")
    y = np.arange(2)
    x = np.arange(3)
    rng = np.random.RandomState(0)
    data = rng.randn(len(time), len(y), len(x))
    cube = xr.DataArray(
        data,
        coords={"time": time, "y": y, "x": x},
        dims=("time", "y", "x"),
        name="tiny",
    )
    return cube


@pytest.fixture
def monotone_series() -> xr.DataArray:
    """Monotone increasing 1D series useful for rank-based tests."""

    time = pd.date_range("2001-01-01", periods=5, freq="D")
    data = xr.DataArray(np.linspace(1.0, 5.0, num=time.size), coords={"time": time}, dims="time")
    return data
