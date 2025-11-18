"""Tests for utility helpers."""

from __future__ import annotations

import xarray as xr

from cubedynamics.utils.chunking import coarsen_and_stride
from cubedynamics.utils.reference import center_pixel_series


def test_coarsen_and_stride(tiny_cube: xr.DataArray) -> None:
    coarsened = coarsen_and_stride(
        tiny_cube,
        coarsen_factor=2,
        time_stride=2,
        y_dim="y",
        x_dim="x",
        time_dim="time",
    )
    assert coarsened.sizes["y"] == tiny_cube.sizes["y"] // 2
    assert coarsened.sizes["x"] == tiny_cube.sizes["x"] // 2
    assert coarsened.sizes["time"] == (tiny_cube.sizes["time"] + 1) // 2


def test_center_pixel_series(tiny_cube: xr.DataArray) -> None:
    series = center_pixel_series(tiny_cube)
    assert series.ndim == 1
    assert "time" in series.dims
    assert series.sizes["time"] == tiny_cube.sizes["time"]
