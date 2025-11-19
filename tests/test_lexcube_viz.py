"""Smoke tests for lexcube visualization helpers."""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

pytest.importorskip("lexcube", reason="lexcube is required for these visualization tests")

from cubedynamics.viz.lexcube_viz import show_cube_lexcube


def test_show_cube_lexcube_smoke() -> None:
    time = np.arange(3)
    y = np.arange(2)
    x = np.arange(4)
    data = np.random.randn(len(time), len(y), len(x))
    cube = xr.DataArray(data, coords={"time": time, "y": y, "x": x}, dims=("time", "y", "x"))

    widget = show_cube_lexcube(cube, title="Test cube")
    assert widget is not None


def test_show_cube_lexcube_requires_three_dims() -> None:
    time = np.arange(3)
    y = np.arange(2)
    data = np.random.randn(len(time), len(y))
    bad_cube = xr.DataArray(data, coords={"time": time, "y": y}, dims=("time", "y"))

    with pytest.raises(ValueError):
        show_cube_lexcube(bad_cube)


def test_show_cube_lexcube_requires_time_y_x_dims() -> None:
    time = np.arange(3)
    y = np.arange(2)
    band = np.arange(4)
    data = np.random.randn(len(time), len(y), len(band))
    bad_cube = xr.DataArray(data, coords={"time": time, "y": y, "band": band}, dims=("time", "y", "band"))

    with pytest.raises(ValueError):
        show_cube_lexcube(bad_cube)
