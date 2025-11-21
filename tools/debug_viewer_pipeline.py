"""
Small script to exercise the viewer pipeline on a synthetic cube.

Run with:
    python tools/debug_viewer_pipeline.py
inside an environment where cubedynamics is installed.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.plotting import CubePlot


def make_tiny_cube():
    data = np.random.rand(4, 6, 6)
    time = xr.date_range("2000-01-01", periods=4)
    y = np.arange(6)
    x = np.arange(6)
    return xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="debugvar",
    )


if __name__ == "__main__":
    cube = make_tiny_cube()

    # 1) Direct CubePlot
    p = CubePlot(cube)
    print("CubePlot type:", type(p))

    # 2) v.plot via pipe
    vp = (pipe(cube) | v.plot()).unwrap()
    print("v.plot return type:", type(vp))
