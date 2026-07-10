"""Tests for the synchrony grammar primitives."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.events import EventResult


def _cube() -> xr.DataArray:
    time = np.array(
        [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-06",
        ],
        dtype="datetime64[ns]",
    )
    data = np.array(
        [
            [[30.0, 36.0], [38.0, 32.0]],
            [[36.0, 37.0], [39.0, 30.0]],
            [[37.0, 20.0], [40.0, 31.0]],
            [[20.0, 38.0], [41.0, 32.0]],
            [[36.0, 39.0], [20.0, 33.0]],
            [[37.0, 40.0], [42.0, 34.0]],
        ]
    )
    return xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": time, "y": [40.0, 40.5], "x": [-105.0, -104.5]},
        name="tmax",
    )


def test_threshold_state_preserves_coords_and_metadata() -> None:
    state = (pipe(_cube()) | v.threshold_state(threshold=35, direction="above")).unwrap()

    assert list(state.data_vars) == ["state", "magnitude", "threshold"]
    assert state["state"].dtype == bool
    assert state.attrs["threshold_method"] == "threshold"
    assert state.attrs["direction"] == "above"
    assert state["state"].sel(time="2024-01-01", y=40.0, x=-105.0).item() is False
    assert state["state"].sel(time="2024-01-02", y=40.0, x=-105.0).item() is True


def test_occurrence_synchrony_reference_reports_rare_event_counts() -> None:
    state = (pipe(_cube()) | v.threshold_state(threshold=35, direction="above")).unwrap()

    result = (
        pipe(state)
        | v.occurrence_synchrony(spatial_mode="reference", reference=(1, 0))
    ).unwrap()

    assert "occurrence_synchrony" in result
    assert "joint_event_count" in result
    assert "event_union_count" in result
    assert result.sizes["time_window_end"] == 1
    center_score = result["occurrence_synchrony"].sel(y=40.5, x=-105.0).item()
    assert np.isclose(center_score, 1.0)


def test_severity_synchrony_returns_joint_diagnostics() -> None:
    state = (pipe(_cube()) | v.threshold_state(threshold=35, direction="above")).unwrap()

    result = (
        pipe(state)
        | v.severity_synchrony(
            spatial_mode="reference",
            reference="center",
            min_joint_events=1,
        )
    ).unwrap()

    assert "severity_synchrony" in result
    assert "joint_observation_count" in result
    assert "mean_absolute_magnitude_difference" in result
    assert np.isfinite(result["joint_observation_count"].max())


def test_detect_events_timing_and_duration_synchrony() -> None:
    state = (pipe(_cube()) | v.threshold_state(threshold=35, direction="above")).unwrap()
    events = (pipe(state) | v.detect_events(min_duration=2, max_gap=1)).unwrap()

    assert isinstance(events, EventResult)
    assert "event_id" in events.dataset
    assert len(events.catalog) == 3

    timing = (
        pipe(events)
        | v.timing_synchrony(
            spatial_mode="reference",
            reference="center",
            match_tolerance="5D",
        )
    ).unwrap()
    duration = (
        pipe(events)
        | v.duration_synchrony(
            spatial_mode="reference",
            reference="center",
            match_tolerance="5D",
            min_matched_events=1,
        )
    ).unwrap()

    assert "timing_synchrony" in timing
    assert "mean_lag" in timing
    assert "duration_synchrony" in duration
    assert "duration_similarity" in duration


def test_biological_cube_and_same_pixel_coupling() -> None:
    cube = _cube()
    observations = pd.DataFrame(
        {
            "date": cube.time.values[:3],
            "y": [40.0, 40.5, 40.5],
            "x": [-105.0, -104.5, -104.5],
            "abundance": [1.0, 2.0, 4.0],
        }
    )
    hot = (pipe(cube) | v.threshold_state(threshold=35, direction="above")).unwrap()
    bio = v.rasterize_observations(
        observations,
        template=cube,
        value_col="abundance",
        reducer="sum",
    )
    boom = (pipe(bio) | v.change_state(change="relative", threshold=0.5, lag=1)).unwrap()

    coupling = (
        pipe(hot)
        | v.sync_with(
            boom,
            synchrony="occurrence",
            spatial_relation="same_pixel",
            lags=["0D", "1D"],
        )
    ).unwrap()

    assert "coupling_score" in coupling
    assert "best_lag" in coupling
    assert coupling.sizes["lag"] == 2
    assert bio.attrs["missing_value_semantics"].startswith("NaN means unobserved")


def test_sync_with_positive_lag_means_right_cube_responds_later() -> None:
    cube = _cube()
    climate = (pipe(cube > 35) | v.binary_state()).unwrap()
    response_mask = climate["state"].shift(time=1, fill_value=False)
    response = (pipe(response_mask) | v.binary_state()).unwrap()

    coupling = (
        pipe(climate)
        | v.sync_with(
            response,
            synchrony="occurrence",
            spatial_relation="same_pixel",
            lags=["0D", "1D"],
        )
    ).unwrap()

    assert coupling["coupling_score"].sel(lag="1D").mean() > coupling[
        "coupling_score"
    ].sel(lag="0D").mean()
