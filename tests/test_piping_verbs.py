import numpy as np
import xarray as xr

from cubedynamics import verbs as v
from cubedynamics.piping import pipe
from cubedynamics.plotting import CubePlot


def _cube():
    data = np.ones((3, 4, 4), dtype="float32")
    coords = {
        "time": np.array(["2001-01-01", "2001-01-02", "2001-01-03"], dtype="datetime64[ns]"),
        "y": np.arange(4),
        "x": np.arange(4),
    }
    return xr.DataArray(data, coords=coords, dims=("time", "y", "x"), name="demo")


def test_pipe_chain_returns_viewer():
    cube = _cube()
    viewer = (pipe(cube) | v.zscore(dim="time") | v.plot()).unwrap()
    assert isinstance(viewer, CubePlot)
    assert cube.identical(cube)  # original not mutated


def test_unwrap_returns_object():
    cube = _cube()
    viewer = (pipe(cube) | v.plot(title="demo")).unwrap()
    assert isinstance(viewer, CubePlot)
