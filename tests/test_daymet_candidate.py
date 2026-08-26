"""Daymet remains a bounded, credentialed candidate until certified."""

from __future__ import annotations

import pytest

from cubedynamics.data.daymet import build_daymet_ncss_request, load_daymet_candidate


def test_daymet_request_is_spatially_and_temporally_bounded() -> None:
    url, params = build_daymet_ncss_request(
        variable="tmax",
        year=2020,
        bbox=[-105.35, 39.95, -105.20, 40.10],
        start="2020-07-01",
        end="2020-07-03",
    )
    assert "daymet_v4_daily_na_tmax_2020.nc" in url
    assert params["west"] == "-105.35"
    assert params["time_start"].startswith("2020-07-01")
    assert params["time_end"].startswith("2020-07-03")


def test_daymet_candidate_requires_earthdata_credentials(monkeypatch) -> None:
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    with pytest.raises(PermissionError, match="EARTHDATA_TOKEN"):
        load_daymet_candidate(
            variable="tmax",
            bbox=[-105.35, 39.95, -105.20, 40.10],
            start="2020-07-01",
            end="2020-07-03",
        )
