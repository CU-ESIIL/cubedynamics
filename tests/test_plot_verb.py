import numpy as np
import pytest
import xarray as xr

import cubedynamics as cd
from cubedynamics import verbs as v
from cubedynamics.piping import pipe


def _dummy_cube():
    data = np.random.rand(4, 5, 6).astype("float32")
    return xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={
            "time": np.arange(4),
            "y": np.arange(5),
            "x": np.arange(6),
        },
        name="dummy",
    )


def test_v_plot_returns_widget():
    cube = _dummy_cube()
    widget = (pipe(cube) | v.plot(time_dim="time")).unwrap()
    import ipywidgets as widgets

    assert isinstance(widget, widgets.VBox)


def test_cd_plot_returns_widget():
    cube = _dummy_cube()
    widget = cd.plot(cube, time_dim="time")
    import ipywidgets as widgets

    assert isinstance(widget, widgets.VBox)


def test_v_plot_rejects_non_dataarray():
    non_cube = np.zeros((2, 2))

    with pytest.raises(TypeError):
        _ = (pipe(non_cube) | v.plot()).unwrap()
