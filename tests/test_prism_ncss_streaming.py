"""Tests for lazy PRISM NcSS streaming."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

import cubedynamics.data.prism as prism


def test_prism_ncss_streaming_defers_daily_subset_requests(monkeypatch) -> None:
    paths = ["prism/day-1.nc", "prism/day-2.nc", "prism/day-3.nc"]
    calls: list[str] = []

    monkeypatch.setattr(prism, "_discover_prism_daily_paths", lambda times: paths)

    def fake_subset(dataset_path, variables, aoi):
        calls.append(dataset_path)
        value = float(paths.index(dataset_path) + 1)
        coords = {"y": [40.0, 40.1], "x": [-105.4, -105.3]}
        return xr.Dataset(
            {
                name: xr.DataArray(
                    np.full((2, 2), value, dtype="float32"),
                    dims=("y", "x"),
                    coords=coords,
                    attrs={"units": "C"},
                )
                for name in variables
            }
        )

    monkeypatch.setattr(prism, "_request_prism_ncss_subset", fake_subset)

    def fake_array(dataset_path, variables, aoi, expected_shape, expected_y, expected_x):
        calls.append(dataset_path)
        value = float(paths.index(dataset_path) + 1)
        return np.full(expected_shape, value, dtype="float32")

    monkeypatch.setattr(prism, "_request_prism_ncss_array", fake_array)

    cube = prism.load_prism_cube(
        variables=["tmin", "tmax"],
        bbox=[-105.4, 40.0, -105.3, 40.1],
        start="2024-01-01",
        end="2024-01-03",
        freq="D",
        show_progress=False,
    )

    assert calls == [paths[0]]
    assert all(variable.chunks is not None for variable in cube.data_vars.values())
    assert cube.attrs["source"] == "prism_streaming"
    assert cube.attrs["is_synthetic"] is False
    assert cube.attrs["streaming_protocol"] == "NcSS"

    computed = cube.isel(time=1).compute()
    np.testing.assert_allclose(computed["tmin"], 2.0)
    np.testing.assert_allclose(computed["tmax"], 2.0)


def test_prism_catalog_discovery_uses_each_requested_date(monkeypatch) -> None:
    catalogs = {
        2023: {"20231231": "prism/2023/day.nc"},
        2024: {"20240101": "prism/2024/day.nc"},
    }
    monkeypatch.setattr(prism, "_prism_daily_catalog", catalogs.__getitem__)
    times = pd.date_range("2023-12-31", "2024-01-01", freq="D")

    assert prism._discover_prism_daily_paths(times) == [
        "prism/2023/day.nc",
        "prism/2024/day.nc",
    ]


def test_prism_catalog_keeps_canonical_path_when_catalog_has_alias(
    monkeypatch,
) -> None:
    class FakeResponse:
        text = """
        <a href="catalog.html?dataset=prism/daily/combo/1981/PRISM_combo_19810101.nc">
        <a href="catalog.html?dataset=prism/daily/combo/1981/prism_combo_4km_19810101.nc">
        """

        def raise_for_status(self) -> None:
            return None

    class FakeSession:
        def get(self, *args, **kwargs):
            return FakeResponse()

    prism._prism_daily_catalog.cache_clear()
    monkeypatch.setattr(prism, "_prism_http_session", lambda: FakeSession())

    try:
        paths = prism._prism_daily_catalog(1981)
    finally:
        prism._prism_daily_catalog.cache_clear()

    assert paths["19810101"] == "prism/daily/combo/1981/PRISM_combo_19810101.nc"


def test_prism_default_chunks_keep_streaming_windows_bounded() -> None:
    assert prism._resolve_chunks(None)["time"] == 31


def test_prism_streaming_failure_does_not_silently_make_synthetic_data(
    monkeypatch,
) -> None:
    def fail(*args, **kwargs):
        raise RuntimeError("service offline")

    monkeypatch.setattr(prism, "_open_prism_streaming", fail)

    with pytest.warns(RuntimeWarning, match="streaming backend unavailable"):
        with pytest.raises(RuntimeError, match="synthetic fallback is disabled"):
            prism.load_prism_cube(
                variable="tmin",
                bbox=[-105.4, 40.0, -105.3, 40.1],
                start="2024-01-01",
                end="2024-01-03",
                freq="D",
                show_progress=False,
            )
