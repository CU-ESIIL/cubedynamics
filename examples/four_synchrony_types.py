"""Run all four synchrony primitives on a small synthetic climate cube."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v


def make_tmax_cube() -> xr.DataArray:
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


if __name__ == "__main__":
    tmax_cube = make_tmax_cube()
    hot = pipe(tmax_cube) | v.threshold_state(threshold=35, direction="above")
    hot_events = hot | v.detect_events(state_var="state", min_duration=2, max_gap=1)

    occurrence = hot | v.occurrence_synchrony(spatial_mode="neighbors", radius_km=100)
    severity = hot | v.severity_synchrony(
        spatial_mode="neighbors",
        radius_km=100,
        min_joint_events=1,
    )
    timing = hot_events | v.timing_synchrony(
        spatial_mode="neighbors",
        radius_km=100,
        match_tolerance="5D",
    )
    duration = hot_events | v.duration_synchrony(
        spatial_mode="neighbors",
        radius_km=100,
        match_tolerance="5D",
        min_matched_events=1,
    )

    print(occurrence.unwrap())
    print(severity.unwrap())
    print(timing.unwrap())
    print(duration.unwrap())
