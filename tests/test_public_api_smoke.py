"""Smoke tests for the documented public API surface.

These tests avoid network and large data by using small synthetic cubes while
importing the public entry points.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

import cubedynamics as cd


def _tiny_cube() -> xr.DataArray:
    data = np.arange(24, dtype=float).reshape(3, 2, 4)
    times = np.array(["2000-01-01", "2000-01-02", "2000-01-03"], dtype="datetime64[ns]")
    y = np.array([0.0, 1.0])
    x = np.array([0.0, 1.0, 2.0, 3.0])
    return xr.DataArray(data, coords={"time": times, "y": y, "x": x}, dims=("time", "y", "x"))


def test_public_symbols_available():
    loaders = [
        "load_gridmet_cube",
        "load_prism_cube",
        "load_sentinel2_cube",
        "load_sentinel2_bands_cube",
        "load_sentinel2_ndvi_cube",
    ]
    legacy_aliases = [
        "load_s2_cube",
        "load_s2_ndvi_cube",
        "load_sentinel2_ndvi_zscore_cube",
    ]

    for name in loaders + legacy_aliases:
        assert hasattr(cd, name), f"Expected cubedynamics to expose {name}"

    assert hasattr(cd, "pipe")
    assert hasattr(cd, "verbs")


def test_pipe_and_verbs_smoke():
    cube = _tiny_cube()

    result = (
        cd.pipe(cube)
        | cd.verbs.anomaly(dim="time", keep_dim=True)
        | cd.verbs.zscore(dim="time", keep_dim=True)
        | cd.verbs.mean(dim="time")
    ).unwrap()

    assert isinstance(result, xr.DataArray)
    assert set(result.dims) == {"y", "x"}
    assert result.shape == (2, 4)


def test_flatten_and_plot_stub():
    cube = _tiny_cube()
    flattened = (cd.pipe(cube) | cd.verbs.flatten_space(new_dim="space")).unwrap()

    assert {"time", "space"} == set(flattened.dims)
    assert flattened.shape[0] == cube.sizes["time"]
    assert flattened.shape[1] == cube.sizes["y"] * cube.sizes["x"]

    # Ensure the convenience plot helper can be called without raising.
    plotted = cd.plot(cube, time_dim="time", cmap="viridis")
    assert plotted is not None
