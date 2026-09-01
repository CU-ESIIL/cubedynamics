"""Scientific contracts for coordinate, observation-support, and event time."""

from __future__ import annotations

import json
from pathlib import Path

import dask.array as da
import numpy as np
import pandas as pd
import pytest
import xarray as xr

import cubedynamics as cd
from cubedynamics import data, pipe, verbs as v


def _support_attrs(source: str, *, start: str, end: str) -> dict[str, object]:
    return {
        "source_flavor": source,
        "temporal_resolution": "daily",
        "temporal_support_type": "interval",
        "temporal_label_convention": "day_ending",
        "temporal_reference_timezone": "UTC",
        "temporal_support_start_offset": start,
        "temporal_support_end_offset": end,
        "temporal_support_known": 1,
    }


def _field(
    source: str = "source_a",
    *,
    start: str = "-24h",
    end: str = "0h",
    lazy: bool = False,
) -> xr.DataArray:
    values = np.arange(12, dtype=float).reshape(3, 2, 2)
    payload = da.from_array(values, chunks=(1, 2, 2)) if lazy else values
    return xr.DataArray(
        payload,
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2024-07-01", periods=3, freq="D"),
            "y": [44.0, 44.1],
            "x": [-101.0, -100.9],
        },
        name="temperature",
        attrs={"units": "degC", "crs": "EPSG:4326", **_support_attrs(source, start=start, end=end)},
    )


def _condition(**kwargs) -> xr.Dataset:
    return (pipe(_field(**kwargs)) | v.threshold_state(threshold=5, direction="above")).unwrap()


def test_catalog_represents_source_specific_daily_interval_support() -> None:
    prism = data.describe("temperature", source="prism")
    gridmet = data.describe("temperature", source="gridmet")

    assert prism["temporal_support_type"] == "interval"
    assert prism["temporal_label_convention"] == "day_ending"
    assert prism["temporal_support_start_offset"] == "-12h"
    assert prism["temporal_support_end_offset"] == "12h"
    assert gridmet["temporal_support_type"] == "interval"
    assert gridmet["temporal_support_start_offset"] == "7h"
    assert gridmet["temporal_support_end_offset"] == "31h"


def test_instant_observation_support_is_publicly_inspectable() -> None:
    point = _field().assign_attrs(
        temporal_support_type="instant",
        temporal_label_convention="acquisition_instant",
        temporal_support_start_offset="0h",
        temporal_support_end_offset="0h",
        temporal_support_known=1,
    )

    support = cd.temporal_support(point)
    intervals = cd.observation_intervals(point)

    assert support.instant
    xr.testing.assert_equal(intervals.observation_start, point.time.rename("observation_start"))
    xr.testing.assert_equal(intervals.observation_end, point.time.rename("observation_end"))


def test_unknown_support_is_not_treated_as_exact() -> None:
    unknown = _field().assign_attrs({"source_flavor": "unknown"})
    for key in list(unknown.attrs):
        if key.startswith("temporal_support_") or key == "temporal_label_convention":
            unknown.attrs.pop(key)
    report = cd.compare_temporal_support(unknown, unknown.copy())

    assert not cd.temporal_support(unknown).known
    assert report.coordinates == "exact"
    assert report.temporal_support == "unknown"
    with pytest.raises(ValueError, match="Temporal support is unknown"):
        cd.observation_intervals(unknown)


def test_observation_intervals_are_derived_from_label_offsets() -> None:
    intervals = cd.observation_intervals(_field(start="-12h", end="12h"))

    assert intervals.observation_start.values[0] == np.datetime64("2024-06-30T12:00")
    assert intervals.observation_end.values[0] == np.datetime64("2024-07-01T12:00")
    assert intervals.sizes == {"time": 3}


def test_semantic_state_tracks_known_temporal_support() -> None:
    state = pipe(_field()).semantic_state

    assert state.temporal
    assert state.temporal_resolution == "daily"
    assert state.temporal_support_type == "interval"
    assert state.temporal_support_known is True
    assert state.temporal_label_convention == "day_ending"


def test_reducing_over_time_removes_time_varying_support_from_state() -> None:
    reduced = pipe(_field()) | v.mean(dim="time", keep_dim=False)

    assert not reduced.semantic_state.temporal
    assert reduced.semantic_state.temporal_support_type is None
    assert reduced.semantic_state.temporal_support_known is None


def test_reducing_space_preserves_temporal_support() -> None:
    reduced = pipe(_field()) | v.mean(dim=("x", "y"), keep_dim=False)

    assert reduced.semantic_state.temporal
    assert reduced.semantic_state.temporal_support_known is True
    assert reduced.semantic_state.temporal_support_start_offset == "-24h"


def test_threshold_preserves_support_while_time_remains() -> None:
    thresholded = pipe(_field()) | v.threshold_state(threshold=4, direction="above")

    assert thresholded.semantic_state.temporal_support_known is True
    assert thresholded.unwrap().attrs["temporal_support_end_offset"] == "0h"


def test_overlap_accepts_exact_labels_and_exact_support() -> None:
    result = (pipe(_condition()) | v.overlap(_condition(source="source_b"))).unwrap()

    assert result.attrs["temporal_alignment_coordinates"] == "exact"
    assert result.attrs["temporal_alignment_support"] == "exact"


def test_overlap_requires_choice_for_exact_labels_but_different_support() -> None:
    left = _condition()
    right = _condition(source="source_b", start="-18h", end="6h")

    with pytest.raises(ValueError, match="different known observation intervals"):
        pipe(left) | v.overlap(right)


def test_overlap_labels_policy_records_known_support_caveat() -> None:
    left = _condition()
    right = _condition(source="source_b", start="-18h", end="6h")
    result = (pipe(left) | v.overlap(right, temporal_alignment="labels")).unwrap()

    assert result.attrs["temporal_alignment_support"] == "different"
    assert result.attrs["temporal_alignment_policy"] == "labels"
    assert result.attrs["temporal_support_known"] == 0
    assert result.attrs["temporal_alignment_modified_coordinates"] == 0


def test_overlap_unknown_support_proceeds_with_visible_check() -> None:
    left = _condition()
    unknown = _condition().assign_attrs({"source_flavor": "unknown"})
    for key in list(unknown.attrs):
        if key.startswith("temporal_support_") or key == "temporal_label_convention":
            unknown.attrs.pop(key)

    result = pipe(left) | v.overlap(unknown)

    assert result.unwrap().attrs["temporal_alignment_support"] == "unknown"
    assert any(c.code == "temporal_support_compatibility_unknown" for c in result.validate().checks)


def test_explain_and_validate_report_cross_source_support_mismatch() -> None:
    result = pipe(_condition()) | v.overlap(
        _condition(source="source_b", start="-18h", end="6h"),
        temporal_alignment="labels",
    )

    explanation = result.explain()
    report = result.validate()
    assert "Observation support: different" in explanation
    assert "different declared observation intervals" in explanation
    assert any(c.code == "temporal_support_different" and c.severity == "WARNING" for c in report.checks)


def test_align_time_exact_support_succeeds_without_changing_data() -> None:
    original = _field(lazy=True)
    result = (pipe(original) | v.align_time(_field(source="source_b"))).unwrap()

    assert result.identical(original.assign_attrs(result.attrs))
    assert result.attrs["temporal_alignment_support"] == "exact"
    assert isinstance(result.data, da.Array)


def test_align_time_exact_support_rejects_known_mismatch() -> None:
    with pytest.raises(ValueError, match="different known observation intervals"):
        pipe(_field()) | v.align_time(
            _field(source="source_b", start="-18h", end="6h"),
            mode="require_exact_support",
        )


def test_align_time_labels_acknowledges_but_does_not_shift_or_resample() -> None:
    original = _field()
    other = _field(source="source_b", start="-18h", end="6h")
    result = (pipe(original) | v.align_time(other, mode="labels")).unwrap()

    xr.testing.assert_equal(result.drop_attrs(), original.drop_attrs())
    np.testing.assert_array_equal(result.time, original.time)
    assert result.sizes == original.sizes
    assert result.attrs["temporal_alignment_modified_values"] == 0
    assert result.attrs["temporal_alignment_modified_coordinates"] == 0


def test_align_time_never_accepts_shifted_labels() -> None:
    shifted = _field().assign_coords(time=pd.date_range("2024-07-02", periods=3))
    with pytest.raises(ValueError, match="time-coordinate labels differ"):
        pipe(_field()) | v.align_time(shifted, mode="labels")


def _offset_daily_products(kind: str) -> tuple[xr.DataArray, xr.DataArray]:
    hours = pd.date_range("2024-01-01", "2024-01-04", freq="h", inclusive="left")
    signal = pd.Series(0.0, index=hours)
    signal.loc[pd.Timestamp("2024-01-01T23:00")] = 30.0 if kind == "temperature" else 12.0
    labels = pd.date_range("2024-01-01", periods=3, freq="D")

    def aggregate(start_offset: pd.Timedelta, reducer: str) -> np.ndarray:
        values = []
        for label in labels:
            start = label + start_offset
            window = signal[(signal.index >= start) & (signal.index < start + pd.Timedelta("24h"))]
            values.append(window.max() if reducer == "max" else window.sum())
        return np.asarray(values)[:, None, None]

    reducer = "max" if kind == "temperature" else "sum"
    a = xr.DataArray(
        aggregate(pd.Timedelta("0h"), reducer),
        dims=("time", "y", "x"), coords={"time": labels, "y": [0], "x": [0]},
        name=kind, attrs=_support_attrs("midnight", start="0h", end="24h"),
    )
    b = xr.DataArray(
        aggregate(pd.Timedelta("-18h"), reducer),
        dims=a.dims, coords=a.coords, name=kind,
        attrs=_support_attrs("six_am_ending", start="-18h", end="6h"),
    )
    return a, b


def test_shifted_daily_windows_change_temperature_maximum_and_event_label() -> None:
    a, b = _offset_daily_products("temperature")
    a_events = (pipe(a) | v.threshold_state(threshold=25, direction="above") | v.detect_events()).unwrap()
    b_events = (pipe(b) | v.threshold_state(threshold=25, direction="above") | v.detect_events()).unwrap()

    assert a.sel(time="2024-01-01").item() == 30
    assert b.sel(time="2024-01-01").item() == 0
    assert a_events.catalog.iloc[0]["start"] == np.datetime64("2024-01-01")
    assert b_events.catalog.iloc[0]["start"] == np.datetime64("2024-01-02")
    assert a_events.dataset.attrs["event_time_basis"] == "observation_coordinate_labels"


def test_shifted_daily_windows_change_precipitation_accumulation_date() -> None:
    a, b = _offset_daily_products("precipitation")

    assert a.sel(time="2024-01-01").item() == 12
    assert b.sel(time="2024-01-01").item() == 0
    assert b.sel(time="2024-01-02").item() == 12
    assert cd.compare_temporal_support(a, b).temporal_support == "different"


def test_event_and_lag_metadata_distinguish_label_timing_from_support() -> None:
    state = _condition()
    events = (pipe(state) | v.detect_events()).unwrap()
    timing = (pipe(events) | v.timing_synchrony(spatial_mode="all_pairs")).unwrap()
    coupling = (pipe(state) | v.sync_with(state, lags=("0D", "1D"))).unwrap()

    assert events.dataset.attrs["event_time_support_note"].startswith("Event start and end")
    assert timing.attrs["observation_support_alignment"] == "separate_not_performed"
    assert timing.attrs["event_time_alignment"] == "event_start_label"
    assert "coordinate-label period shift" in coupling.attrs["lag_semantics"]


def test_public_temporal_helpers_preserve_xarray_interoperability_and_laziness() -> None:
    cube = _field(lazy=True)
    intervals = data.observation_intervals(cube)
    aligned = (pipe(cube) | v.align_time(cube)).unwrap()

    assert isinstance(intervals, xr.Dataset)
    assert isinstance(aligned, xr.DataArray)
    assert isinstance(aligned.data, da.Array)
    assert aligned.data is cube.data


def test_temporal_showcase_notebook_is_real_data_code_and_compiles() -> None:
    path = Path("docs/examples/temporal_alignment.ipynb")
    notebook = json.loads(path.read_text(encoding="utf-8"))
    code = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]

    for index, source in enumerate(code):
        compile(source, f"{path}:{index}", "exec")
    joined = "\n".join(code)
    assert 'source="prism"' in joined
    assert 'source="gridmet"' in joined
    assert "2024-07-01" in joined and "2024-07-31" in joined
    assert "allow_synthetic" not in joined
    assert 'v.align_time(gridmet_hot, mode="labels")' in joined
