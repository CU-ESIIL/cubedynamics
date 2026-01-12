"""Unit tests for the modern PRISM loader API."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

import cubedynamics.data.prism as prism


@pytest.fixture()
def stub_prism_backends(monkeypatch):
    calls: dict[str, dict] = {}

    def _fake_dataset(var_names: list[str]):
        coords = {
            "time": pd.date_range("2000-01-01", periods=1, freq="D"),
            "y": np.array([40.0, 40.1]),
            # Align with the AOI used in legacy positional tests to avoid
            # creating an empty selection when cropping to the bbox.
            "x": np.array([-105.35, -105.30]),
        }
        data_vars = {
            name: xr.DataArray(
                np.zeros((1, 2, 2)),
                coords=coords,
                dims=("time", "y", "x"),
                name=name,
            )
            for name in var_names
        }
        return xr.Dataset(data_vars)

    def fake_stream(variables, start, end, aoi, freq):
        calls["stream"] = {
            "variables": list(variables),
            "start": start,
            "end": end,
            "aoi": dict(aoi),
            "freq": freq,
        }
        return _fake_dataset(list(variables))

    def fake_download(*args, **kwargs):  # pragma: no cover - fallback not used
        return _fake_dataset(list(args[0]))

    monkeypatch.setattr(prism, "_open_prism_streaming", fake_stream)
    monkeypatch.setattr(prism, "_open_prism_download", fake_download)
    return calls


def test_load_prism_cube_with_point_aoi(stub_prism_backends):
    da = prism.load_prism_cube(
        lat=40.0,
        lon=-105.25,
        start="2000-01-01",
        end="2000-12-31",
        variable="ppt",
    )

    assert isinstance(da, xr.DataArray)
    assert da.name == "ppt"
    aoi = stub_prism_backends["stream"]["aoi"]
    assert aoi["min_lat"] < 40.0 < aoi["max_lat"]
    assert aoi["min_lon"] < -105.25 < aoi["max_lon"]


def test_load_prism_cube_with_bbox(stub_prism_backends):
    da = prism.load_prism_cube(
        bbox=[-105.4, 40.0, -105.2, 40.2],
        start="2000-01-01",
        end="2000-12-31",
        variable="ppt",
    )

    assert isinstance(da, xr.DataArray)
    assert da.name == "ppt"
    assert stub_prism_backends["stream"]["aoi"] == {
        "min_lon": -105.4,
        "min_lat": 40.0,
        "max_lon": -105.2,
        "max_lat": 40.2,
    }


def test_load_prism_cube_with_geojson(stub_prism_backends):
    boulder = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-105.35, 40.00],
                [-105.35, 40.10],
                [-105.20, 40.10],
                [-105.20, 40.00],
                [-105.35, 40.00],
            ]],
        },
        "properties": {"name": "Boulder"},
    }

    da = prism.load_prism_cube(
        aoi_geojson=boulder,
        start="2000-01-01",
        end="2000-12-31",
        variable="ppt",
    )

    assert isinstance(da, xr.DataArray)
    assert da.name == "ppt"
    aoi = stub_prism_backends["stream"]["aoi"]
    assert aoi["min_lon"] == pytest.approx(-105.35)
    assert aoi["max_lon"] == pytest.approx(-105.20)
    assert aoi["min_lat"] == pytest.approx(40.00)
    assert aoi["max_lat"] == pytest.approx(40.10)


def test_load_prism_cube_requires_single_aoi():
    with pytest.raises(ValueError):
        prism.load_prism_cube(
            start="2000-01-01",
            end="2000-12-31",
            variable="ppt",
        )

    with pytest.raises(ValueError):
        prism.load_prism_cube(
            lat=40.0,
            lon=-105.25,
            bbox=[-105.4, 40.0, -105.2, 40.2],
            start="2000-01-01",
            end="2000-12-31",
            variable="ppt",
        )


def test_load_prism_cube_legacy_positional(stub_prism_backends):
    aoi = {
        "min_lon": -105.4,
        "max_lon": -105.3,
        "min_lat": 40.0,
        "max_lat": 40.1,
    }

    ds = prism.load_prism_cube(["ppt"], "2000-01-01", "2000-12-31", aoi)

    assert "ppt" in ds.data_vars
    assert stub_prism_backends["stream"]["aoi"] == aoi


def test_load_prism_cube_variable_returns_dataarray(stub_prism_backends):
    da = prism.load_prism_cube(
        lat=40.0,
        lon=-105.25,
        start="2000-01-01",
        end="2000-12-31",
        variable="ppt",
    )

    assert isinstance(da, xr.DataArray)
    assert da.name == "ppt"
