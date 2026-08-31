import dask.array as da
import numpy as np
import pytest
import xarray as xr

from cubedynamics import verbs as v
from cubedynamics.piping import pipe
from cubedynamics.plotting import CubePlot
from cubedynamics.plotting.cube_plot import DEFAULT_CAMERA


def _make_tiny_cube():
    data = da.random.random((5, 8, 8), chunks=(2, 8, 8))
    time = np.array(
        ["2000-01-01", "2000-01-02", "2000-01-03", "2000-01-04", "2000-01-05"],
        dtype="datetime64[ns]",
    )
    y = xr.DataArray(range(8), dims=("y",))
    x = xr.DataArray(range(8), dims=("x",))
    return xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="testvar",
    )


def test_plot_returns_cubeplot():
    cube = _make_tiny_cube()
    result = (pipe(cube) | v.plot()).unwrap()
    assert isinstance(result, CubePlot)


def test_plot_does_not_materialize_dask():
    cube = _make_tiny_cube()
    result = (pipe(cube) | v.plot()).unwrap()
    assert isinstance(result, CubePlot)
    assert cube.data.__class__.__name__.lower().startswith("array")


def test_plot_default_camera():
    cube = _make_tiny_cube()
    result = (pipe(cube) | v.plot()).unwrap()
    assert result.camera == DEFAULT_CAMERA
    assert result.camera["eye"]["x"] > 0


def test_plot_camera_override():
    cube = _make_tiny_cube()
    custom_camera = {"eye": {"x": 2.0, "y": 1.5, "z": 1.2}}
    result = (pipe(cube) | v.plot(camera=custom_camera)).unwrap()
    assert result.camera["eye"] == custom_camera["eye"]


def test_plot_condition_dataset_selects_state_and_preserves_laziness():
    cube = _make_tiny_cube()
    condition = (
        pipe(cube)
        | v.threshold_state(threshold=0.5, direction="above", name="warm")
    ).unwrap()

    result = (pipe(condition) | v.plot()).unwrap()

    assert isinstance(result, CubePlot)
    assert result.data.name == "state"
    assert result.title == "warm"
    assert result.data.attrs["semantic_kind"] == "condition"
    assert result.data.data.__class__.__name__.lower().startswith("array")


def test_plot_event_result_selects_event_active():
    event = (
        pipe(_make_tiny_cube())
        | v.threshold_state(threshold=0.5, direction="above", name="warm")
        | v.detect_events(min_duration=1)
    ).unwrap()

    result = (pipe(event) | v.plot(title="Warm events")).unwrap()

    assert isinstance(result, CubePlot)
    assert result.data.name == "event_active"
    assert result.data.attrs["semantic_kind"] == "event"


def test_plot_dataset_supports_explicit_variable_selection():
    cube = _make_tiny_cube()
    dataset = xr.Dataset({"first": cube, "second": cube + 1})

    result = (pipe(dataset) | v.plot(variable="second")).unwrap()

    assert result.data.name == "second"


def test_plot_ambiguous_dataset_requires_variable():
    cube = _make_tiny_cube()
    dataset = xr.Dataset({"first": cube, "second": cube + 1})

    with pytest.raises(ValueError, match="requires variable=.*first.*second"):
        (pipe(dataset) | v.plot()).unwrap()


def test_plot_rejects_missing_dataset_variable_and_dataarray_variable():
    cube = _make_tiny_cube()
    dataset = xr.Dataset({"first": cube})

    with pytest.raises(ValueError, match="not present in the Dataset"):
        (pipe(dataset) | v.plot(variable="missing")).unwrap()
    with pytest.raises(ValueError, match="variable= for a DataArray"):
        (pipe(cube) | v.plot(variable="first")).unwrap()


def test_plot_two_dimensional_summary_renders_before_returning():
    summary = (
        pipe(_make_tiny_cube())
        | v.mean(dim="time", keep_dim=False)
        | v.plot(title="Mean field")
    )

    result = summary.unwrap()
    assert result.kind == "spatial_map"
    assert result.data.dims == ("y", "x")
    assert "data:image/png;base64" in result._repr_html_()
    assert summary.semantic_state.semantic_kind == "summary"


def test_plot_condition_summary_selects_state_proportion():
    cube = _make_tiny_cube()
    result = (
        pipe(cube)
        | v.threshold_state(threshold=0.5, direction="above", name="warm")
        | v.mean(dim="time", keep_dim=False)
        | v.plot(title="Warm-day frequency")
    ).unwrap()

    assert result.kind == "spatial_map"
    assert result.data.name == "state"
    assert result.data.attrs["semantic_units"] == "proportion"
    assert "data:image/png;base64" in result._repr_html_()


def test_plot_one_dimensional_temporal_summary_uses_line_view():
    series = _make_tiny_cube().mean(("y", "x"))

    result = (pipe(series) | v.plot(title="Regional mean")).unwrap()

    assert result.kind == "temporal_line"
    assert result.data.dims == ("time",)
    assert "data:image/png;base64" in result._repr_html_()


def test_plot_rejects_unsupported_shape_before_notebook_repr():
    scalar = _make_tiny_cube().mean()

    with pytest.raises(ValueError, match="received 0 dimensions"):
        (pipe(scalar) | v.plot()).unwrap()
