"""Offline contracts for live certification and persistent health evidence."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import data


def _sample() -> xr.Dataset:
    return xr.Dataset(
        {"temperature": (("time", "y", "x"), np.ones((2, 2, 2)), {"units": "K"})},
        coords={
            "time": pd.date_range("2024-01-01", periods=2),
            "y": [40.0, 40.1],
            "x": [-105.2, -105.1],
        },
        attrs={"source": "observed", "spatial_reference": "EPSG:4326"},
    )


def test_live_certification_reuses_profile_and_reports_health(tmp_path) -> None:
    result = data.certify_live_sample(
        _sample(),
        qa_profile="climate_continuous_daily",
        serving_revision="temperature.gridmet@2026-08-26.1",
        endpoint_verified=True,
        bounded_access_verified=True,
        upstream_identity_verified=None,
        caveats=("identity header unavailable",),
    )
    output = tmp_path / "gridmet.json"
    data.write_live_certification(result, output)

    persisted = json.loads(output.read_text())
    assert persisted["live_health"] == "DEGRADED"
    assert persisted["certification"]["outcome"] == "PASS_WITH_CAVEATS"
    assert persisted["certification"]["gates"]["upstream_identity_verified"] == "NOT_TESTED"


def test_blocked_live_certification_does_not_invalidate_revision() -> None:
    result = data.blocked_live_certification(
        serving_revision="temperature.daymet@2026-08-26.1",
        reason="EARTHDATA_TOKEN missing",
    )
    assert result["live_health"] == "UNAVAILABLE"
    assert result["certification"]["outcome"] == "BLOCKED"
