import math

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics.plotting.axis_rig import AxisRigSpec, axis_rig_css, build_axis_rig_meta
from cubedynamics.plotting.cube_viewer import cube_from_dataarray


def _make_da(times: pd.DatetimeIndex) -> xr.DataArray:
    data = np.zeros((len(times), 2, 2), dtype="float32")
    return xr.DataArray(
        data,
        coords={"time": times, "y": [0.0, 1.0], "x": [10.0, 11.0]},
        dims=("time", "y", "x"),
        name="test",
    )


def test_axis_rig_monthly_ticks_and_fracs():
    times = pd.date_range("2020-01-01", "2020-06-01", freq="MS")
    da = _make_da(times)
    spec = AxisRigSpec(time_tick="monthly")

    meta = build_axis_rig_meta(da, "time", "y", "x", axis_meta=None, spec=spec)
    ticks = meta["time"]["ticks"]

    assert len(ticks) == len(times)
    assert ticks[0]["label"] == "01.01.2020"
    assert ticks[-1]["label"] == "01.06.2020"
    assert math.isclose(ticks[0]["frac"], 0.0, abs_tol=1e-9)
    assert math.isclose(ticks[-1]["frac"], 1.0, abs_tol=1e-9)


def test_axis_rig_time_label_subsampling():
    times = pd.date_range("2019-01-01", "2021-12-01", freq="MS")
    da = _make_da(times)
    spec = AxisRigSpec(time_tick="monthly", time_label_max=10)

    meta = build_axis_rig_meta(da, "time", "y", "x", axis_meta=None, spec=spec)
    ticks = meta["time"]["ticks"]

    label_step = max(1, math.ceil(len(ticks) / spec.time_label_max))
    label_count = sum(
        1 for idx, tick in enumerate(ticks)
        if tick["label"] and (idx % label_step == 0 or idx == len(ticks) - 1)
    )

    assert label_count <= spec.time_label_max


def test_axis_billboards_invert_camera_and_local_time_rotation():
    css = axis_rig_css(AxisRigSpec())
    assert "rotateY(var(--cd-bb-rot-y)) rotateX(var(--cd-bb-rot-x))" in css
    assert "rotateY(-90deg) rotateY(var(--cd-bb-rot-y)) rotateX(var(--cd-bb-rot-x))" in css
    assert "--cd-axis-color: var(--cube-axis-color," in css
    for selector in (".cd-axis-label", ".cd-axis-ticks", ".cd-axis-tick", ".cd-axis-tick-label"):
        rule = css.split("\n    " + selector + " {", 1)[1].split("}", 1)[0]
        assert "transform-style: preserve-3d" in rule


def test_small_geographic_extent_has_distinguishable_endpoint_labels():
    da = _make_da(pd.date_range("2024-01-01", periods=2)).assign_coords(
        y=[40.05, 40.15], x=[-105.35, -105.25])
    meta = build_axis_rig_meta(da, "time", "y", "x", None, AxisRigSpec())
    assert meta["y"]["min_label"] == "40.05°N"
    assert meta["y"]["max_label"] == "40.15°N"
    assert meta["x"]["min_label"] == "105.35°W"
    assert meta["x"]["max_label"] == "105.25°W"


def test_axis_rig_can_shorten_dates_without_changing_time_direction():
    da = _make_da(pd.date_range("2024-01-01", periods=30))
    meta = build_axis_rig_meta(da, "time", "y", "x", None, AxisRigSpec(time_format="%d %b"))
    assert meta["time"]["min_label"] == "01 Jan"
    assert meta["time"]["max_label"] == "30 Jan"


def test_cube_viewer_axis_rig_html_includes_meta(tmp_path):
    times = pd.date_range("2020-01-01", "2020-03-01", freq="MS")
    da = _make_da(times)
    out_html = tmp_path / "axis_rig.html"

    html = cube_from_dataarray(
        da,
        out_html=str(out_html),
        return_html=True,
        show_progress=False,
        axis_rig=True,
    )

    assert "cd-axis-rig-" in html
    assert "cd-axis-rig" in html
    assert "window.__CD_AXIS_META__" in html
    assert 'data-axis-rig="true"' in html

    html_no_rig = cube_from_dataarray(
        da,
        out_html=str(tmp_path / "axis_rig_off.html"),
        return_html=True,
        show_progress=False,
        axis_rig=False,
    )
    assert 'data-axis-rig="true"' not in html_no_rig
