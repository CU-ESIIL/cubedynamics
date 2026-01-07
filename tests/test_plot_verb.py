import dask.array as da
import xarray as xr

from cubedynamics import verbs as v
from cubedynamics.piping import pipe
from cubedynamics.plotting import CubePlot
from cubedynamics.plotting.cube_plot import DEFAULT_CAMERA


def _make_tiny_cube():
    data = da.random.random((5, 8, 8), chunks=(2, 8, 8))
    time = xr.cftime_range("2000-01-01", periods=5)
    y = xr.DataArray(range(8), dims=("y",))
    x = xr.DataArray(range(8), dims=("x",))
    return xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="testvar",
    )


def test_plot_returns_cubeplot():
    cube = _make_tiny_cube()
    result = (pipe(cube) | v.plot()).unwrap()
    assert isinstance(result, CubePlot)


def test_plot_does_not_materialize_dask():
    cube = _make_tiny_cube()
    result = (pipe(cube) | v.plot()).unwrap()
    assert isinstance(result, CubePlot)
    assert cube.data.__class__.__name__.lower().startswith("array")


def test_plot_default_camera():
    cube = _make_tiny_cube()
    result = (pipe(cube) | v.plot()).unwrap()
    assert result.camera == DEFAULT_CAMERA
    assert result.camera["eye"]["x"] > 0


def test_plot_camera_override():
    cube = _make_tiny_cube()
    custom_camera = {"eye": {"x": 2.0, "y": 1.5, "z": 1.2}}
    result = (pipe(cube) | v.plot(camera=custom_camera)).unwrap()
    assert result.camera["eye"] == custom_camera["eye"]
