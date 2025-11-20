import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import verbs as v


def test_plot_returns_widget():
    times = pd.date_range("2024-01-01", periods=3, freq="D")
    data = xr.DataArray(
        np.ones((3, 2, 2)),
        coords={"time": times, "y": [0, 1], "x": [0, 1]},
        dims=("time", "y", "x"),
        name="test",
    )

    widget = v.plot()(data)

    # The verb should return a VBox container with the slider + output elements.
    from ipywidgets import VBox

    assert isinstance(widget, VBox)
    assert len(widget.children) == 2
