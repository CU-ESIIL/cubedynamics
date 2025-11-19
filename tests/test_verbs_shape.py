"""Tests for custom and flattening verbs."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v


def test_apply_lambda_preserves_dims(tiny_cube):
    doubled = (pipe(tiny_cube) | v.apply(lambda da: da * 2)).unwrap()
    np.testing.assert_allclose(doubled.values, tiny_cube.values * 2)
    assert doubled.dims == tiny_cube.dims


def test_apply_handles_dataset():
    data = xr.Dataset({"var": xr.DataArray([1, 2, 3], dims=("time",))})
    result = (pipe(data) | v.apply(lambda ds: ds * 3)).unwrap()
    np.testing.assert_allclose(result["var"].values, [3, 6, 9])


def test_flatten_space_replaces_spatial_dims(tiny_cube):
    flattened = (pipe(tiny_cube) | v.flatten_space(new_dim="pixel")).unwrap()
    assert flattened.dims == ("time", "pixel")
    assert flattened.sizes["pixel"] == tiny_cube.sizes["y"] * tiny_cube.sizes["x"]


def test_flatten_cube_stacks_all_non_time_dims(tiny_cube):
    cube = tiny_cube.expand_dims(band=["B04", "B08"])
    flattened = (pipe(cube) | v.flatten_cube(sample_dim="sample")).unwrap()
    assert flattened.dims == ("time", "sample")
    assert flattened.sizes["sample"] == cube.sizes["y"] * cube.sizes["x"] * cube.sizes["band"]
