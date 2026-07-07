"""Smoke tests for lexcube visualization helpers."""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from cubedynamics.viz.lexcube_viz import _prepare_lexcube_cube, show_cube_lexcube


def _require_lexcube() -> None:
    try:
        import lexcube  # noqa: F401
    except Exception as exc:  # pragma: no cover - optional dependency varies by Python
        pytest.skip(f"lexcube is not importable in this environment: {exc}")


def test_show_cube_lexcube_smoke() -> None:
    _require_lexcube()

    time = np.arange(3)
    y = np.arange(2)
    x = np.arange(4)
    data = np.random.randn(len(time), len(y), len(x))
    cube = xr.DataArray(data, coords={"time": time, "y": y, "x": x}, dims=("time", "y", "x"))

    widget = show_cube_lexcube(cube, title="Test cube")
    assert widget is not None


def test_prepare_lexcube_cube_adds_source_for_integer_day_like_time() -> None:
    time = np.arange(3)
    y = np.arange(2)
    x = np.arange(4)
    data = np.random.randn(len(time), len(y), len(x))
    cube = xr.DataArray(data, coords={"time": time, "y": y, "x": x}, dims=("time", "y", "x"))

    prepared = _prepare_lexcube_cube(cube)

    assert prepared.dims == ("time", "y", "x")
    assert prepared.encoding["source"] == ""
    assert "source" not in cube.encoding


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
