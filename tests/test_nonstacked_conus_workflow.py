"""Offline contracts for the CONUS baseline and point-station validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.run_nonstacked_conus_baseline import CONUS_BBOX, RADII_KM
from scripts.validate_nonstacked_conus_stations import (
    _agreement,
    _block_bootstrap,
    _maximin,
    clean_daily,
)


def test_conus_driver_preserves_colorado_method_geometry() -> None:
    assert RADII_KM == (25.0, 50.0, 75.0, 100.0)
    assert CONUS_BBOX == (-124.75, 24.0, -66.5, 50.0)


def test_station_maximin_is_deterministic_and_unique() -> None:
    frame = pd.DataFrame(
        {
            "latitude": [25, 25, 35, 35, 45, 45],
            "longitude": [-120, -70, -110, -80, -120, -70],
        },
        index=[f"S{i}" for i in range(6)],
    )
    first = _maximin(frame, 4)
    second = _maximin(frame, 4)
    assert first.index.tolist() == second.index.tolist()
    assert first.index.is_unique
    assert first.shape[0] == 4


def test_station_cleaning_excludes_nonblank_quality_flags() -> None:
    raw = pd.DataFrame(
        {
            "STATION": ["USX", "USX"],
            "NAME": ["TEST", "TEST"],
            "LATITUDE": [40.0, 40.0],
            "LONGITUDE": [-105.0, -105.0],
            "ELEVATION": [1600.0, 1600.0],
            "DATE": ["2023-11-01", "2023-11-02"],
            "TMIN": [1.0, 2.0],
            "TMAX": [10.0, 11.0],
            "TMIN_ATTRIBUTES": [",,7,", ",S,7,"],
            "TMAX_ATTRIBUTES": [",,7,", ",,7,"],
        }
    )
    clean, manifest = clean_daily(raw)
    tmin = clean[clean.variable == "TMIN"]
    assert tmin.qc_valid.tolist() == [True, False]
    assert np.isnan(tmin.value_c.iloc[1])
    assert int(manifest.tmin_qc_exclusion_count.iloc[0]) == 1
    assert int(manifest.tmax_qc_exclusion_count.iloc[0]) == 0


def test_agreement_and_block_bootstrap_are_explicit_and_deterministic() -> None:
    frame = pd.DataFrame(
        {
            "block": ["a", "a", "b", "b", "c", "c"],
            "station": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "map": [0.12, 0.18, 0.31, 0.39, 0.55, 0.58],
        }
    )
    metrics = _agreement(frame.station.to_numpy(), frame["map"].to_numpy())
    assert metrics["n"] == 6
    assert metrics["mae"] > 0
    first = _block_bootstrap(frame, "station", "map", replicates=25)
    second = _block_bootstrap(frame, "station", "map", replicates=25)
    assert first == second
    assert first["block_count"] == 3

