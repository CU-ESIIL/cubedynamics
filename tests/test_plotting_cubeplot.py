import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics.plotting.cube_plot import CubePlot
from cubedynamics.plotting.cube_viewer import (
    _axis_range_from_ticks,
    _infer_axis_ticks,
    cube_from_dataarray,
)


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


def test_cubeplot_legend_includes_units(tmp_path):
    data = xr.DataArray(
        np.arange(8).reshape(2, 2, 2),
        dims=("time", "y", "x"),
        name="ndvi",
        attrs={"units": "unitless"},
    )

    cube_plot = CubePlot(
        data,
        show_progress=False,
        out_html=str(tmp_path / "cube_units.html"),
    )

    cube_plot.to_html()
    viewer_html = (tmp_path / "cube_units.html").read_text()

    assert "ndvi (unitless)" in viewer_html


def test_axis_tick_inference_includes_units_and_time_format(tmp_path):
    times = pd.date_range("2020-01-01", periods=4, freq="MS")
    y_vals = xr.DataArray(np.linspace(40, 40.1, 4), dims=("y",), attrs={"units": "degrees_north"})
    x_vals = xr.DataArray(np.linspace(-105.3, -105.1, 4), dims=("x",), attrs={"units": "degrees_east"})
    data = xr.DataArray(
        np.arange(4 * 4 * 4).reshape(4, 4, 4),
        dims=("time", "y", "x"),
        coords={"time": times, "y": y_vals, "x": x_vals},
        name="demo",
    )

    time_ticks = _infer_axis_ticks(data, "time", n_ticks=3, time_format="%Y-%m-%d")
    x_ticks = _infer_axis_ticks(data, "x", n_ticks=3)
    y_ticks = _infer_axis_ticks(data, "y", n_ticks=3)

    assert len(time_ticks) == 3
    assert len(x_ticks) == 3
    assert len(y_ticks) == 3
    assert any("degrees_east" in label for _, label in x_ticks)
    assert any("degrees_north" in label for _, label in y_ticks)
    assert any(label.startswith("2020-") for _, label in time_ticks)
    assert "→" in _axis_range_from_ticks(time_ticks)


def test_cube_layout_structure_includes_new_containers(tmp_path):
    data = xr.DataArray(
        np.arange(8).reshape(2, 2, 2), dims=("time", "y", "x"), name="layout"
    )

    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "structure.html"),
        show_progress=False,
        return_html=True,
    )

    assert "cube-figure" in html
    assert "cube-main" in html
    assert "cube-inner" in html
    assert "cube-legend-card" in html
