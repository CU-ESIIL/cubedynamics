import json
import numpy as np
import pandas as pd
import xarray as xr
import pytest

from cubedynamics.plotting.cube_plot import CubePlot
from cubedynamics.plotting.cube_viewer import (
    _axis_range_from_ticks,
    _infer_axis_ticks,
    _render_cube_html,
    cube_from_dataarray,
)
from cubedynamics.verbs import plot


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


def test_plot_returns_cubeplot_without_full_values(monkeypatch):
    data = xr.DataArray(np.arange(27).reshape(3, 3, 3), dims=("time", "y", "x"))

    original_getter = xr.DataArray.values.fget

    def guarded_values(self):
        if self.ndim > 2:
            raise AssertionError("Full values access")
        return original_getter(self)

    monkeypatch.setattr(xr.DataArray, "values", property(guarded_values))

    viewer = plot()(data)
    assert isinstance(viewer, CubePlot)


def test_axis_meta_formats_time_and_latlon():
    times = pd.to_datetime(["1979-01-05", "1979-01-15"])
    lats = xr.DataArray([45.2, -12.7], dims=("y",))
    lons = xr.DataArray([100.4, -80.2], dims=("x",))
    data = xr.DataArray(
        np.arange(8).reshape(2, 2, 2),
        dims=("time", "y", "x"),
        coords={"time": times, "y": lats, "x": lons},
        name="demo",
    )

    cube_plot = CubePlot(data, show_progress=False)
    axis_meta = cube_plot.axis_meta

    assert axis_meta["time"]["min"] == "05.01.1979"
    assert axis_meta["time"]["max"] == "15.01.1979"
    assert axis_meta["y"]["min"].endswith("S")
    assert axis_meta["y"]["max"].endswith("N")
    assert axis_meta["x"]["min"].endswith("W")
    assert axis_meta["x"]["max"].endswith("E")


def test_axis_meta_generic_numeric():
    times = pd.to_datetime(["2020-01-01", "2020-02-01"])
    data = xr.DataArray(
        np.arange(16).reshape(2, 2, 4),
        dims=("time", "row", "col"),
        coords={"time": times, "row": [0, 1], "col": [10.0, 20.0, 30.0, 40.0]},
    )

    cube_plot = CubePlot(data, show_progress=False)
    meta = cube_plot.axis_meta

    assert meta["y"]["name"] == "Row"
    assert meta["x"]["name"] == "Col"
    assert meta["x"]["max"].startswith("40.")


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


def test_shell_fill_mode_returns_shell_html(monkeypatch, tmp_path):
    data = xr.DataArray(np.arange(27).reshape(3, 3, 3), dims=("time", "y", "x"))

    recorded = {}

    def capture(**kwargs):
        recorded["planes"] = kwargs.get("interior_planes")
        return _render_cube_html(**kwargs)

    monkeypatch.setattr("cubedynamics.plotting.cube_viewer._render_cube_html", capture)

    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "shell.html"),
        show_progress=False,
        return_html=True,
        fill_mode="shell",
    )

    assert recorded.get("planes") is None
    assert "<div class=\"interior-plane\"" not in html


def test_progressive_mode_builds_interior_planes(monkeypatch, tmp_path):
    data = xr.DataArray(np.arange(64).reshape(4, 4, 4), dims=("time", "y", "x"))

    calls = {}

    def capture(**kwargs):
        calls["planes"] = kwargs.get("interior_planes")
        return "<html></html>"

    monkeypatch.setattr("cubedynamics.plotting.cube_viewer._render_cube_html", capture)

    cube_from_dataarray(
        data,
        out_html=str(tmp_path / "progressive.html"),
        show_progress=False,
        return_html=True,
        fill_mode="progressive",
        volume_density={"time": 2, "x": 1, "y": 1},
        volume_downsample={"time": 1, "space": 2},
    )

    planes = calls.get("planes")
    assert planes is not None
    axes = [axis for axis, *_ in planes]
    assert "time" in axes
    assert any(meta["nt"] == 4 and meta["nx"] == 2 and meta["ny"] == 2 for *_, meta in planes)


def test_progressive_html_contains_interior_planes(tmp_path):
    data = xr.DataArray(np.arange(64).reshape(4, 4, 4), dims=("time", "y", "x"))

    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "progressive_html.html"),
        show_progress=False,
        return_html=True,
        fill_mode="progressive",
        volume_density={"time": 1, "x": 1, "y": 1},
        volume_downsample={"time": 2, "space": 2},
    )

    assert "interior-plane" in html


def test_progressive_values_access_is_2d(monkeypatch, tmp_path):
    data = xr.DataArray(
        np.arange(64).reshape(4, 4, 4), dims=("time", "y", "x"), name="guard"
    )

    original_getter = xr.DataArray.values.fget

    def guarded_values(self):
        if self.ndim > 2:
            raise AssertionError("Full values access")
        return original_getter(self)

    monkeypatch.setattr(xr.DataArray, "values", property(guarded_values))

    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "guard_progressive.html"),
        show_progress=False,
        return_html=True,
        fill_mode="progressive",
        volume_density={"time": 1, "x": 1, "y": 1},
        volume_downsample={"time": 2, "space": 2},
    )

    assert "data:image/png;base64" in html
