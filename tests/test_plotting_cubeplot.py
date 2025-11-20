import numpy as np
import xarray as xr

from cubedynamics.plotting.cube_plot import CubePlot
from cubedynamics.plotting.cube_viewer import cube_from_dataarray


def test_cubeplot_to_html_includes_caption_and_theme(tmp_path):
    data = xr.DataArray(
        np.arange(8).reshape(2, 2, 2), dims=("time", "y", "x"), name="demo"
    )

    cube_plot = CubePlot(
        data,
        caption={"id": 1, "title": "Example", "text": "Value \\(x\\)"},
        show_progress=False,
        out_html=str(tmp_path / "cube.html"),
    )

    html = cube_plot.to_html()
    assert "Figure 1" in html
    assert "cornflowerblue" in html
    assert "Value \\(x\\)" in html


def test_cube_viewer_avoids_full_values(monkeypatch, tmp_path):
    data = xr.DataArray(
        np.arange(27).reshape(3, 3, 3), dims=("time", "y", "x"), name="demo"
    )

    original_getter = xr.DataArray.values.fget

    def guarded_values(self):
        if self.ndim > 2:
            raise AssertionError("Full values access")
        return original_getter(self)

    monkeypatch.setattr(xr.DataArray, "values", property(guarded_values))

    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "guard.html"),
        show_progress=False,
        return_html=True,
    )

    assert "data:image/png;base64" in html
