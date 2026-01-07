import numpy as np
import pytest
import xarray as xr

from cubedynamics import verbs as v
from cubedynamics.plotting.cube_plot import DEFAULT_CAMERA, plotly_camera_to_coord


def _cube():
    data = np.ones((2, 3, 4), dtype="float32")
    coords = {
        "time": xr.cftime_range("2001-01-01", periods=2),
        "y": np.arange(3),
        "x": np.arange(4),
    }
    return xr.DataArray(data, coords=coords, dims=("time", "y", "x"), name="demo")


def test_plot_default_camera_applied():
    cube = _cube()
    viewer = v.plot(cube)

    assert viewer.camera["eye"]["x"] == DEFAULT_CAMERA["eye"]["x"]
    assert viewer.camera["eye"]["y"] == DEFAULT_CAMERA["eye"]["y"]
    assert viewer.camera["eye"]["z"] == DEFAULT_CAMERA["eye"]["z"]

    expected_coord = plotly_camera_to_coord(DEFAULT_CAMERA)
    assert viewer.coord.azim == pytest.approx(expected_coord.azim)
    assert viewer.coord.elev == pytest.approx(expected_coord.elev)
    assert viewer.coord.zoom == pytest.approx(expected_coord.zoom)


def test_plot_camera_override_merges_defaults():
    cube = _cube()
    viewer = v.plot(cube, camera={"eye": {"x": 0.5}})

    assert viewer.camera["eye"]["x"] == 0.5
    assert viewer.camera["eye"]["y"] == DEFAULT_CAMERA["eye"]["y"]
    assert viewer.camera["eye"]["z"] == DEFAULT_CAMERA["eye"]["z"]

    expected_camera = {
        "eye": {
            "x": 0.5,
            "y": DEFAULT_CAMERA["eye"]["y"],
            "z": DEFAULT_CAMERA["eye"]["z"],
        },
        "up": DEFAULT_CAMERA["up"],
        "center": DEFAULT_CAMERA["center"],
    }
    expected_coord = plotly_camera_to_coord(expected_camera)
    assert viewer.coord.azim == pytest.approx(expected_coord.azim)
    assert viewer.coord.elev == pytest.approx(expected_coord.elev)
    assert viewer.coord.zoom == pytest.approx(expected_coord.zoom)
