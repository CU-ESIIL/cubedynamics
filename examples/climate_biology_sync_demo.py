"""Synthetic climate-biology coupling demo."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v


def make_climate_cube() -> xr.DataArray:
    time = np.arange("2024-01-01", "2024-01-09", dtype="datetime64[D]").astype(
        "datetime64[ns]"
    )
    y = np.array([40.0, 40.5])
    x = np.array([-105.0, -104.5])
    base = np.linspace(30.0, 42.0, len(time))[:, None, None]
    offsets = np.array([[0.0, 2.0], [3.0, -1.0]])[None, :, :]
    return xr.DataArray(
        base + offsets,
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="tmax",
    )


if __name__ == "__main__":
    climate_cube = make_climate_cube()
    observations = pd.DataFrame(
        {
            "date": climate_cube.time.values[[0, 1, 2, 4]],
            "y": [40.0, 40.0, 40.5, 40.5],
            "x": [-105.0, -105.0, -104.5, -104.5],
            "abundance": [1.0, 2.0, 2.0, 4.0],
        }
    )

    hot = (
        pipe(climate_cube)
        | v.threshold_state(threshold=35, direction="above", name="hot_state")
    ).unwrap()
    bio_cube = v.rasterize_observations(
        observations,
        template=climate_cube,
        time_col="date",
        value_col="abundance",
        reducer="sum",
    )
    bio_aligned = (
        pipe(bio_cube)
        | v.align_cube(like=climate_cube, spatial_method="nearest", temporal_method="nearest")
    ).unwrap()
    boom = (
        pipe(bio_aligned)
        | v.change_state(change="relative", threshold=0.5, lag=1, name="population_boom")
    ).unwrap()
    coupling = (
        pipe(hot)
        | v.sync_with(
            boom,
            synchrony="occurrence",
            spatial_relation="same_pixel",
            lags=["0D", "1D", "2D"],
        )
    ).unwrap()

    print(coupling)
