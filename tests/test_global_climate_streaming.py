"""Tests for generic global climate streaming adapters."""

from __future__ import annotations

import dask.array as da
import numpy as np
import pytest
import xarray as xr

from cubedynamics.streaming import stream_global_climate_cube


def _global_source() -> xr.Dataset:
    time = np.array(["2001-01-01", "2001-01-02"], dtype="datetime64[ns]")
    latitude = np.array([45.0, 40.0, 35.0])
    longitude = np.array([250.0, 255.0, 260.0])
    data = da.arange(time.size * latitude.size * longitude.size, chunks=6).reshape(
        (time.size, latitude.size, longitude.size)
    )
    return xr.Dataset(
        {
            "t2m": xr.DataArray(
                data,
                coords={"time": time, "latitude": latitude, "longitude": longitude},
                dims=("time", "latitude", "longitude"),
            )
        }
    )


def test_stream_global_climate_cube_normalizes_dims_and_keeps_lazy() -> None:
    cube = stream_global_climate_cube(
        _global_source(),
        variables=["t2m"],
        bbox=[-105.0, 35.0, -100.0, 45.0],
        chunks={"time": 1, "y": 2, "x": 1},
        source_name="era5_zarr",
    )

    assert cube["t2m"].dims == ("time", "y", "x")
    assert cube.sizes == {"time": 2, "y": 3, "x": 2}
    assert cube["t2m"].chunks is not None
    assert cube.attrs["source"] == "era5_zarr"
    assert cube.attrs["streaming_protocol"] == "xarray"
    assert cube.attrs["is_synthetic"] is False
    np.testing.assert_allclose(cube["x"], [255.0, 260.0])


def test_stream_global_climate_cube_rejects_dateline_crossing_360_bbox() -> None:
    with pytest.raises(NotImplementedError, match="dateline"):
        stream_global_climate_cube(
            _global_source(),
            bbox={
                "min_lon": -170.0,
                "min_lat": 35.0,
                "max_lon": 170.0,
                "max_lat": 45.0,
            },
        )


def test_stream_global_climate_cube_requires_unambiguous_dims() -> None:
    source = xr.Dataset(
        {
            "value": xr.DataArray(
                np.ones((2, 2)),
                dims=("row", "col"),
            )
        }
    )

    with pytest.raises(ValueError, match="Could not infer"):
        stream_global_climate_cube(source)
