import re

import numpy as np
import xarray as xr

from cubedynamics.plotting.cube_plot import CubePlot


def test_cube_viewer_dom_ids_are_unique():
    da = xr.DataArray(np.arange(8).reshape(2, 2, 2), dims=("time", "y", "x"))

    html_first = CubePlot(da).to_html()
    html_second = CubePlot(da).to_html()

    ids_first = re.findall(r"cube-figure-([a-zA-Z0-9-]+)", html_first)
    ids_second = re.findall(r"cube-figure-([a-zA-Z0-9-]+)", html_second)

    assert ids_first and ids_second
    assert ids_first[0] != ids_second[0]
