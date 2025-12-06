import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.plotting.cube_plot import CubePlot


def test_plot_mean_attaches_viewer_and_returns_original_cube():
    times = pd.date_range("2024-01-01", periods=3, freq="D")
    da = xr.DataArray(
        np.arange(3 * 2 * 2, dtype=float).reshape(3, 2, 2),
        coords={"time": times, "y": [0, 1], "x": [0, 1]},
        dims=("time", "y", "x"),
        name="ndvi",
    )

    result = pipe(da) | v.plot_mean()

    assert result.unwrap() is da

    viewer = getattr(da, "_cd_last_viewer", None)
    assert isinstance(viewer, CubePlot)

    html = viewer._repr_html_()
    assert "cube-figure" in html

