import numpy as np
import xarray as xr

from cubedynamics.plotting.cube_viewer import cube_from_dataarray


def test_cube_viewer_generates_faces():
    data = xr.DataArray(
        np.arange(3 * 4 * 5, dtype=float).reshape(3, 4, 5),
        dims=("time", "y", "x"),
        name="demo",
    )

    html = cube_from_dataarray(
        data,
        show_progress=False,
        return_html=True,
        fill_mode="shell",
    )

    assert "cube-container" in html
    assert html.count("cd-face") >= 6
    assert "data:image/png;base64" in html
    assert len(html) > 1000
