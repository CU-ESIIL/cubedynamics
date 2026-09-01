#!/usr/bin/env python3
"""Black-box semantic and Fire smoke requested by the RC1 triage review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.fire_time_hull import FireEventDaily


def run() -> dict[str, object]:
    time = pd.date_range("2024-07-01", periods=5, freq="D")
    y = np.linspace(39.9, 40.3, 5)
    x = np.linspace(-105.2, -104.8, 6)
    shape = (time.size, y.size, x.size)
    temperature = xr.DataArray(
        np.linspace(18.0, 34.0, np.prod(shape)).reshape(shape),
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="temperature",
        attrs={"units": "degC", "crs": "EPSG:4326", "source": "black-box unit control"},
    )
    precipitation = xr.DataArray(
        np.linspace(0.0, 20.0, np.prod(shape)).reshape(shape),
        dims=temperature.dims,
        coords=temperature.coords,
        name="precipitation",
        attrs={"units": "mm", "crs": "EPSG:4326", "source": "black-box unit control"},
    )

    anomaly_variance = pipe(temperature) | v.anomaly(over="time") | v.variance(
        over="time", keep_dim=False
    )
    assert anomaly_variance.unwrap().attrs["units"] == "degC^2"

    hot = pipe(temperature) | v.threshold_state(
        threshold=25.0, direction="above", name="hot"
    )
    frequency_plot = hot | v.mean(over="time", keep_dim=False) | v.plot(
        title="Hot-day frequency"
    )
    assert frequency_plot.unwrap().kind == "spatial_map"
    frequency_plot.unwrap()._repr_html_()

    quantile = pipe(temperature) | v.quantile_state(
        quantile=0.8, direction="above", name="warm tail"
    )
    assert set(quantile.unwrap().data_vars) == {"state", "magnitude", "threshold"}

    wet = pipe(precipitation) | v.threshold_state(
        threshold=5.0, direction="above", name="wet"
    )
    very_wet = pipe(precipitation) | v.quantile_state(
        quantile=0.8, direction="above", name="very wet"
    )
    overlap_plot = wet | v.overlap(very_wet.unwrap(), name="wet overlap") | v.mean(
        over="time", keep_dim=False
    ) | v.plot(title="Wet overlap frequency")
    assert overlap_plot.unwrap().kind == "spatial_map"
    overlap_plot.unwrap()._repr_html_()

    events = hot | v.detect_events(min_duration=1)
    assert events.semantic_state.semantic_kind == "event"

    fire_event = FireEventDaily.example()
    hull = fire_event.to_hull(n_ring_samples=16, n_theta=12)
    geometry_figure = hull.plot()
    assert len(geometry_figure.data) == 1

    climate_time = pd.date_range(fire_event.t0, fire_event.t1, freq="D")
    climate = xr.Dataset(
        {
            name: xr.DataArray(
                np.full((climate_time.size, y.size, x.size), float(index + 1)),
                dims=("time", "y", "x"),
                coords={"time": climate_time, "y": y, "x": x},
                attrs={"units": "1", "crs": "EPSG:4326"},
            )
            for index, name in enumerate(
                ("temperature", "precipitation", "vpd", "wind", "humidity", "radiation")
            )
        },
        attrs={"crs": "EPSG:4326", "source": "black-box unit control"},
    )
    enriched = hull.attach_environment(climate)
    climate_figure = enriched.plot(color="vpd")
    assert len(climate_figure.data) == 1

    return {
        "status": "PASS",
        "condition_representation": sorted(hot.unwrap().data_vars),
        "overlap_representation": sorted(
            (wet | v.overlap(very_wet.unwrap())).unwrap().data_vars
        ),
        "condition_mean_units": frequency_plot.unwrap().data.attrs["semantic_units"],
        "variance_units": anomaly_variance.unwrap().attrs["units"],
        "fire_environment_variables": sorted(enriched.environment),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
