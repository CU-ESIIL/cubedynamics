"""Reusable QA profiles cover the first planned source families."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import data


def _climate() -> xr.Dataset:
    return xr.Dataset(
        {
            "temperature": (
                ("time", "y", "x"),
                np.ones((3, 2, 2), dtype="float32"),
                {"units": "K"},
            )
        },
        coords={
            "time": pd.date_range("2024-01-01", periods=3, freq="D"),
            "y": [40.0, 40.1],
            "x": [-105.2, -105.1],
        },
        attrs={
            "source": "reviewed observation",
            "is_synthetic": False,
            "spatial_reference": "EPSG:4326",
        },
    )


def test_required_qa_profiles_are_registered_and_nonempty() -> None:
    assert set(data.list_qa_profiles()) == {
        "climate_continuous_daily",
        "continuous_raster_static",
        "feature_line",
        "station_timeseries",
    }
    for name in data.list_qa_profiles():
        profile = data.get_qa_profile(name)
        assert profile.description
        assert profile.applies_to


def test_climate_and_raster_profiles_run_real_structural_checks() -> None:
    climate = data.evaluate_qa_profile("climate_continuous_daily", _climate())
    raster = data.evaluate_qa_profile("continuous_raster_static", _climate())

    assert climate.outcome is data.CertificationOutcome.PASS
    assert raster.outcome is data.CertificationOutcome.PASS
    assert len(climate.checks) >= 8
    assert len(raster.checks) >= 7


def test_climate_profile_fails_non_daily_or_undocumented_data() -> None:
    dataset = _climate().drop_attrs()
    dataset.temperature.attrs = {}
    dataset = dataset.assign_coords(time=pd.date_range("2024-01-01", periods=3, freq="2D"))
    result = data.evaluate_qa_profile("climate_continuous_daily", dataset)

    assert result.outcome is data.CertificationOutcome.FAIL
    assert result.checks["daily_interval"] is False
    assert result.checks["units_documented"] is False
    assert result.checks["crs_documented"] is False


def test_climate_profile_reads_dataarray_provenance_without_hiding_synthetic() -> None:
    array = _climate()["temperature"].copy(deep=False)
    array.attrs.update(
        {
            "source_provider": "reviewed observation provider",
            "is_synthetic": False,
            "spatial_reference": "EPSG:4326",
        }
    )

    observed = data.evaluate_qa_profile("climate_continuous_daily", array)
    assert observed.outcome is data.CertificationOutcome.PASS
    assert observed.checks["source_identity_documented"] is True
    assert observed.checks["observational_source"] is True

    generated = array.copy(deep=False)
    generated.attrs["is_synthetic"] = True
    rejected = data.evaluate_qa_profile("climate_continuous_daily", generated)
    assert rejected.outcome is data.CertificationOutcome.FAIL
    assert rejected.checks["observational_source"] is False


def test_feature_line_profile_checks_geometry_identity_and_crs() -> None:
    result = data.evaluate_qa_profile(
        "feature_line",
        {
            "feature_count": 14,
            "geometry_types": ["LineString", "MultiLineString"],
            "crs": "EPSG:4326",
            "identifier_field": "reach_id",
            "valid_geometry_fraction": 1.0,
        },
    )

    assert result.outcome is data.CertificationOutcome.PASS
    assert all(result.checks.values())


def test_station_timeseries_profile_checks_sites_locations_units_and_time() -> None:
    dataset = xr.Dataset(
        {
            "discharge": (
                ("time", "station"),
                np.ones((3, 2), dtype="float32"),
                {"units": "m3 s-1"},
            )
        },
        coords={
            "time": pd.date_range("2024-01-01", periods=3),
            "station": ["A", "B"],
            "latitude": ("station", [40.0, 40.5]),
            "longitude": ("station", [-105.0, -104.5]),
        },
    )
    result = data.evaluate_qa_profile("station_timeseries", dataset)

    assert result.outcome is data.CertificationOutcome.PASS
    assert all(result.checks.values())
