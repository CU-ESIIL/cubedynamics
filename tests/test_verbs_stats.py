"""Unit tests for standardized cube verbs."""

from __future__ import annotations

import numpy as np

from cubedynamics import pipe, verbs as v


def test_mean_keep_dim_preserves_cube_shape(tiny_cube):
    result = (pipe(tiny_cube) | v.mean(dim="time", keep_dim=True)).unwrap()
    assert result.dims == tiny_cube.dims
    assert result.sizes["time"] == 1


def test_variance_drop_dim_when_requested(tiny_cube):
    result = (pipe(tiny_cube) | v.variance(dim="time", keep_dim=False)).unwrap()
    assert "time" not in result.dims


def test_anomaly_keep_dim_true_is_cube_ready(tiny_cube):
    result = (pipe(tiny_cube) | v.anomaly(dim="time", keep_dim=True)).unwrap()
    assert result.dims == tiny_cube.dims
    mean = result.mean(dim="time")
    assert float(np.abs(mean).max()) < 1e-6


def test_zscore_mean_zero_with_keep_dim(tiny_cube):
    z = (pipe(tiny_cube) | v.zscore(dim="time", keep_dim=True)).unwrap()
    assert z.dims == tiny_cube.dims
    mean = z.mean(dim="time")
    assert float(np.abs(mean).max()) < 1e-6
