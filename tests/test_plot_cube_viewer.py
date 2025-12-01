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


def test_cube_viewer_keeps_depth_when_heavily_thinned(monkeypatch):
    data = xr.DataArray(
        np.random.random((5, 3, 4)),
        dims=("time", "y", "x"),
    )

    captured_shapes = []

    def _capture_colormap(arr, **kwargs):
        captured_shapes.append(arr.shape)
        # Return a transparent RGBA array matching the expected shape.
        return np.zeros((*arr.shape, 4), dtype=np.uint8)

    monkeypatch.setattr(
        "cubedynamics.plotting.cube_viewer._colormap_to_rgba", _capture_colormap
    )

    cube_from_dataarray(
        data,
        thin_time_factor=10,
        show_progress=False,
        return_html=True,
    )

    # Faces that include the time dimension should still span at least two slices.
    # left/right faces are (ny, nt_eff); top/bottom are (nx, nt_eff)
    assert captured_shapes[2][1] == 2
    assert captured_shapes[3][1] == 2
    assert captured_shapes[4][1] == 2
    assert captured_shapes[5][1] == 2
