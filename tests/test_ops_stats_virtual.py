import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.streaming import VirtualCube


@pytest.fixture
def ground_truth_cube():
    t = 4
    y = 2
    x = 3
    time_index = pd.date_range("2001-01-01", periods=t, freq="D")
    y_vals = np.arange(y)
    x_vals = np.arange(x)
    data = np.arange(t * y * x).reshape(t, y, x)
    return xr.DataArray(
        data=data,
        dims=("time", "y", "x"),
        coords={"time": time_index, "y": y_vals, "x": x_vals},
        name="var",
    )


def _virtual_from_dense(cube: xr.DataArray) -> VirtualCube:
    def loader(start=None, end=None, bbox=None, **_kwargs):
        da = cube
        if start is not None or end is not None:
            da = da.sel(time=slice(start, end))
        if bbox is not None:
            xmin, ymin, xmax, ymax = bbox
            da = da.sel(x=slice(xmin, xmax), y=slice(ymin, ymax))
        return da

    times = list(cube.time.values)

    def time_tiler(_kwargs):
        for ts in times:
            yield {"start": ts, "end": ts}

    def spatial_tiler(_kwargs):
        xs = cube.x.values
        ys = cube.y.values
        for x0 in xs[:-1]:
            yield {"bbox": (x0, ys.min(), x0, ys.max())}
        yield {"bbox": (xs[-1], ys.min(), xs[-1], ys.max())}

    return VirtualCube(
        dims=cube.dims,
        coords_metadata={},
        loader=loader,
        loader_kwargs={},
        time_tiler=time_tiler,
        spatial_tiler=spatial_tiler,
    )


@pytest.mark.parametrize(
    "operation",
    [
        lambda arr: pipe(arr) | v.mean(dim="time"),
        lambda arr: pipe(arr) | v.variance(dim="time"),
        lambda arr: pipe(arr) | v.mean(dim=("y", "x")),
        lambda arr: pipe(arr) | v.variance(dim=("y", "x")),
        lambda arr: pipe(arr) | v.zscore(dim="time"),
    ],
)
def test_virtual_cube_matches_dense(operation, ground_truth_cube):
    cube = ground_truth_cube
    vc = _virtual_from_dense(cube)

    dense = operation(cube).unwrap()
    streamed = operation(vc).unwrap()
    xr.testing.assert_allclose(dense, streamed)
    assert isinstance(streamed, xr.DataArray)
    assert set(streamed.dims).issubset(set(cube.dims))
