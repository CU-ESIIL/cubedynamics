"""Regression coverage for event scope and long-record scientific semantics."""

from __future__ import annotations

import time
from pathlib import Path

import dask.array as da
import numpy as np
import pandas as pd
import pytest
import xarray as xr

import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.events import EventResult


ROOT = Path(__file__).resolve().parents[1]


def _state(values: np.ndarray, times=None) -> xr.Dataset:
    values = np.asarray(values, dtype=bool)
    if times is None:
        times = pd.date_range("2020-01-01", periods=values.shape[0], freq="D")
    array = xr.DataArray(
        values,
        dims=("time", "y", "x"),
        coords={"time": times, "y": np.arange(values.shape[1]), "x": np.arange(values.shape[2])},
        name="state",
    )
    result = (pipe(array) | v.binary_state(name="test condition")).unwrap()
    result.attrs["temporal_resolution"] = "daily"
    return result


def _toy_local_events() -> EventResult:
    values = np.zeros((6, 3, 3), dtype=bool)
    values[0:2, 0, 0] = True
    values[1:3, 0, 1] = True
    values[0:2, 2, 2] = True
    values[4:6, 2, 2] = True
    return (pipe(_state(values)) | v.detect_events()).unwrap()


def test_event_result_declares_local_scope_and_spatial_identity() -> None:
    events = _toy_local_events()
    assert events.event_scope == "local_cell"
    assert events.spatial_identity_fields == ("y_index", "x_index")
    assert events.catalog.attrs["event_scope"] == "local_cell"
    assert "one spatial grid cell" in events.catalog.attrs["event_row_meaning"]


def test_event_result_repr_is_bounded_and_rejects_regional_interpretation() -> None:
    events = _toy_local_events()
    text = repr(events)
    assert "local-cell events" in text
    assert "not a count of independent regional" in text
    assert text.count("Catalog preview") == 1


@pytest.mark.parametrize("constructor", ["threshold", "quantile", "overlap", "change"])
def test_detect_events_preserves_explicit_local_scope(constructor: str) -> None:
    data = xr.DataArray(
        np.arange(24.0).reshape(6, 2, 2),
        dims=("time", "y", "x"),
        coords={"time": pd.date_range("2020-01-01", periods=6), "y": [0, 1], "x": [0, 1]},
        name="signal",
    )
    if constructor == "threshold":
        condition = (pipe(data) | v.threshold_state(threshold=10, direction="above")).unwrap()
    elif constructor == "quantile":
        condition = (pipe(data) | v.quantile_state(quantile=0.5, direction="above")).unwrap()
    elif constructor == "change":
        condition = (pipe(data) | v.change_state(change="absolute", threshold=1, lag=1)).unwrap()
    else:
        first = (pipe(data) | v.threshold_state(threshold=6, direction="above")).unwrap()
        second = (pipe(data) | v.threshold_state(threshold=10, direction="above")).unwrap()
        condition = (pipe(first) | v.overlap(second)).unwrap()
    events = (pipe(condition) | v.detect_events()).unwrap()
    assert events.event_scope == "local_cell"
    assert events.dataset.attrs["event_scope"] == "local_cell"


def test_consolidation_builds_known_regional_components() -> None:
    regional = (
        pipe(_toy_local_events())
        | v.consolidate_events(spatial_relation="neighbors", max_gap="0D")
    ).unwrap()
    assert regional.event_scope == "regional_episode"
    assert len(regional.catalog) == 3
    first = regional.catalog.loc[regional.catalog["local_event_count"] == 2].iloc[0]
    assert first["start"] == np.datetime64("2020-01-01")
    assert first["end"] == np.datetime64("2020-01-03")
    assert first["duration"] == 3
    assert first["local_event_count"] == 2
    assert first["participating_cell_count"] == 2
    assert first["peak_participation"] == 2


def test_consolidation_does_not_merge_spatially_unrelated_same_date_events() -> None:
    values = np.zeros((2, 1, 3), dtype=bool)
    values[:, 0, 0] = True
    values[:, 0, 2] = True
    local = (pipe(_state(values)) | v.detect_events()).unwrap()
    regional = (pipe(local) | v.consolidate_events(spatial_relation="neighbors")).unwrap()
    assert len(regional.catalog) == 2


def test_consolidation_respects_max_temporal_gap() -> None:
    values = np.zeros((4, 1, 2), dtype=bool)
    values[0, 0, 0] = True
    values[2, 0, 1] = True
    local = (pipe(_state(values)) | v.detect_events()).unwrap()
    separate = (pipe(local) | v.consolidate_events(max_gap="0D")).unwrap()
    merged = (pipe(local) | v.consolidate_events(max_gap="2D")).unwrap()
    assert len(separate.catalog) == 2
    assert len(merged.catalog) == 1


def test_regional_scope_survives_pipe_semantic_state() -> None:
    result = pipe(_toy_local_events()) | v.consolidate_events()
    assert result.semantic_state.event_scope == "regional_episode"
    assert "regional_episode" in result.explain()


def test_event_metrics_by_year_are_scope_aware_and_correct() -> None:
    times = pd.to_datetime(
        ["2020-01-01", "2020-01-02", "2020-01-03", "2021-01-01", "2021-01-02", "2021-01-03"]
    )
    values = np.array([True, True, False, True, True, True])[:, None, None]
    local = (pipe(_state(values, times)) | v.detect_events()).unwrap()
    metrics = (
        pipe(local)
        | v.event_metrics(
            period="year",
            metrics=("event_count", "mean_duration", "median_duration", "max_duration", "event_days"),
        )
    ).unwrap()
    np.testing.assert_array_equal(metrics.year, [2020, 2021])
    np.testing.assert_array_equal(metrics.event_count, [1, 1])
    np.testing.assert_array_equal(metrics.mean_duration, [2, 3])
    np.testing.assert_array_equal(metrics.event_days, [2, 3])
    assert metrics.attrs["event_scope"] == "local_cell"
    assert "not independent regional" in metrics.attrs["event_count_interpretation"]


def test_seasonal_coordinate_gap_breaks_event_contiguity() -> None:
    times = pd.to_datetime(
        ["2020-09-29", "2020-09-30", "2021-05-01", "2021-05-02", "2021-05-03"]
    )
    values = np.ones((5, 1, 1), dtype=bool)
    events = (pipe(_state(values, times)) | v.detect_events()).unwrap()
    assert len(events.catalog) == 2
    np.testing.assert_array_equal(events.catalog.duration, [2, 3])


def test_block_signature_explain_preserves_physical_units() -> None:
    cube = xr.DataArray(
        np.arange(24.0).reshape(3, 2, 4),
        dims=("time", "y", "x"),
        coords={"time": pd.date_range("2020-01-01", periods=3), "y": [0, 1], "x": range(4)},
        name="temperature",
        attrs={"units": "degC"},
    )
    result = pipe(cube) | v.block_signature(block_id="west", reducer="median")
    assert result.unwrap().temperature.attrs["units"] == "degC"
    assert result.semantic_state.units == "degC"
    assert "Units: degC" in result.explain()


def test_compare_blocks_assigns_metric_specific_units() -> None:
    cube = xr.DataArray(
        np.arange(24.0).reshape(3, 2, 4),
        dims=("time", "y", "x"),
        coords={"time": pd.date_range("2020-01-01", periods=3), "y": [0, 1], "x": range(4)},
        name="temperature",
        attrs={"units": "degC"},
    )
    west = (pipe(cube) | v.block_signature(block_id="west")).unwrap()
    east = (pipe(cube + 1) | v.block_signature(block_id="east")).unwrap()
    result = (pipe(west) | v.collect_blocks(east) | v.compare_blocks()).unwrap()
    assert result.pearson_r.attrs["units"] == "1"
    assert result.mean_difference.attrs["units"] == "degC"
    assert result.rmse.attrs["units"] == "degC"
    assert result.n.attrs["units"] == "count"
    assert result.source_units.sel(variable="temperature").item() == "degC"


def test_compare_blocks_preserves_another_physical_unit() -> None:
    cube = xr.DataArray(
        np.arange(16.0).reshape(4, 2, 2),
        dims=("time", "y", "x"),
        coords={"time": pd.date_range("2020-01-01", periods=4), "y": [0, 1], "x": [0, 1]},
        name="precipitation",
        attrs={"units": "mm"},
    )
    first = (pipe(cube) | v.block_signature(block_id="first")).unwrap()
    second = (pipe(cube * 1.1) | v.block_signature(block_id="second")).unwrap()
    result = (pipe(first) | v.collect_blocks(second) | v.compare_blocks()).unwrap()
    assert result.mean_difference.attrs["units"] == "mm"
    assert result.rmse.attrs["units"] == "mm"
    assert result.pearson_r.attrs["units"] == "1"


def test_multi_year_quantile_explains_pooled_reference_population() -> None:
    time_coord = pd.date_range("2019-01-01", "2021-12-31", freq="MS")
    cube = xr.DataArray(
        np.arange(len(time_coord), dtype=float)[:, None, None],
        dims=("time", "y", "x"),
        coords={"time": time_coord, "y": [0], "x": [0]},
        name="temperature",
    )
    result = pipe(cube) | v.month_filter([5, 6, 7, 8, 9]) | v.quantile_state(quantile=0.9, direction="above")
    text = result.explain()
    assert "pooled across 'time'" in text
    assert "selected calendar months 5,6,7,8,9" in text
    assert "estimated independently at each remaining coordinate" in text


def test_sync_with_negative_lag_means_right_occurs_earlier() -> None:
    time_coord = pd.date_range("2020-01-01", periods=8)
    left_values = np.zeros((8, 1, 1), dtype=bool)
    left_values[[3, 6], 0, 0] = True
    right_values = np.zeros_like(left_values)
    right_values[[2, 5], 0, 0] = True
    left = (pipe(xr.DataArray(left_values, dims=("time", "y", "x"), coords={"time": time_coord, "y": [0], "x": [0]})) | v.binary_state()).unwrap()
    right = (pipe(xr.DataArray(right_values, dims=("time", "y", "x"), coords={"time": time_coord, "y": [0], "x": [0]})) | v.binary_state()).unwrap()
    result = (pipe(left) | v.sync_with(right, lags=["0D", "-1D"])).unwrap()
    assert result.coupling_score.sel(lag="-1D").item() > result.coupling_score.sel(lag="0D").item()
    assert result.attrs["negative_lag_meaning"] == "the right-hand condition occurs earlier than the left-hand condition"


def test_rolling_synchrony_outputs_are_self_describing() -> None:
    rng = np.random.default_rng(2)
    cube = xr.DataArray(
        rng.normal(size=(40, 3, 3)),
        dims=("time", "y", "x"),
        coords={"time": pd.date_range("2020-01-01", periods=40), "y": range(3), "x": range(3)},
        name="temperature",
    )
    result = v.rolling_median_split_synchrony(window_days=20, min_t=3)(cube)
    for name in ("bottom_synchrony", "top_synchrony", "bottom_minus_top"):
        assert result[name].attrs["units"] == "1"
        assert result[name].attrs["description"]
    for name in ("split_definition", "window_definition", "output_time_semantics", "edge_behavior"):
        assert result.attrs[name]


def test_rolling_tail_variance_contrast_declares_negative_interpretation_and_units() -> None:
    values = np.tile(np.array([0.0, 10.0, 0.0, 10.0, 5.0, 5.0, 5.0, 5.0]), (1, 1, 1))
    cube = xr.DataArray(
        values.reshape(8, 1, 1),
        dims=("time", "y", "x"),
        coords={"time": range(8), "y": [0], "x": [0]},
        attrs={"units": "degC"},
        name="temperature",
    )
    result = v.rolling_tail_dep_vs_center(window=8, min_periods=8, tail_quantile=0.5)(cube)
    assert result.attrs["metric_definition"] == "upper-tail variance minus full-window variance"
    assert result.attrs["valid_range"] == "unbounded real numbers"
    assert result.attrs["units"] == "degC^2"
    assert result.isel(time=-1, y=0, x=0).item() < 0


def test_twenty_year_small_domain_state_workflow_is_lazy_until_events() -> None:
    n_days = 365 * 20
    time_coord = pd.date_range("2001-01-01", periods=n_days, freq="D")
    values = da.random.default_rng(7).normal(size=(n_days, 2, 2), chunks=(365, 2, 2))
    cube = xr.DataArray(values, dims=("time", "y", "x"), coords={"time": time_coord, "y": [0, 1], "x": [0, 1]}, name="temperature")
    warm = (pipe(cube) | v.month_filter([5, 6, 7, 8, 9]) | v.quantile_state(quantile=0.9, direction="above")).unwrap()
    dry = (pipe(cube + 0.2) | v.month_filter([5, 6, 7, 8, 9]) | v.quantile_state(quantile=0.8, direction="above")).unwrap()
    combined = (pipe(warm) | v.overlap(dry)).unwrap()
    assert warm.state.chunks is not None
    assert combined.state.chunks is not None
    started = time.monotonic()
    events = (pipe(combined) | v.detect_events()).unwrap()
    elapsed = time.monotonic() - started
    assert events.event_scope == "local_cell"
    assert elapsed < 20


def test_runtime_version_info_identifies_current_checkout() -> None:
    info = cd.version_info()
    assert info.version == cd.__version__
    assert info.package_location.endswith("src/cubedynamics")
    assert info.artifact_kind == "development checkout"
    assert info.git_sha and len(info.git_sha) == 40
    assert "Imported from:" in str(info)


def test_notebook_install_guidance_avoids_dependency_breaking_force_install() -> None:
    text = (ROOT / "docs/getting_started/install.md").read_text(encoding="utf-8")
    assert "Do not use `--ignore-installed`" in text
    assert "--no-deps --upgrade" in text
    assert "restart the kernel" in text
    assert "version_info()" in text


def test_maintained_notebook_builder_records_runtime_identity() -> None:
    shell = (ROOT / "scripts/vignette_shell.py").read_text(encoding="utf-8")
    assert "print(cd.version_info())" in shell
    assert "runtime-identity" in shell
