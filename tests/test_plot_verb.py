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


def test_plot_widget_has_slider_and_label_only():
    cube = _dummy_cube()
    widget = (pipe(cube) | v.plot(time_dim="time")).unwrap()
    import ipywidgets as widgets

    assert isinstance(widget, widgets.VBox)

    controls = widget.children[0]
    assert isinstance(controls, widgets.HBox)

    sliders = [c for c in controls.children if isinstance(c, widgets.IntSlider)]
    labels = [c for c in controls.children if isinstance(c, widgets.Label)]
    dropdowns = [c for c in controls.children if isinstance(c, widgets.Dropdown)]

    assert len(sliders) == 1
    assert len(labels) == 1
    assert dropdowns == []
    assert controls.children[1].value.startswith("time:")


def test_cd_plot_returns_widget():
    cube = _dummy_cube()
    widget = cd.plot(cube, time_dim="time")
    import ipywidgets as widgets

    assert isinstance(widget, widgets.VBox)


def test_v_plot_rejects_non_dataarray():
    non_cube = np.zeros((2, 2))

    with pytest.raises(TypeError):
        _ = (pipe(non_cube) | v.plot()).unwrap()
