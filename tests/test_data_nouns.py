"""Offline contracts for noun-first data access."""

from __future__ import annotations

import json

import dask.array as da
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics import data, pipe, verbs as v


def _climate_dataset(variable: str, *, synthetic: bool = False) -> xr.Dataset:
    values = da.from_array(
        np.arange(24, dtype="float32").reshape(3, 2, 4), chunks=(1, 2, 2)
    )
    cube = xr.DataArray(
        values,
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2024-01-01", periods=3, freq="D"),
            "y": [40.0, 40.05],
            "x": [-105.4, -105.35, -105.3, -105.25],
        },
        name=variable,
        attrs={"units": "provider units"},
    )
    result = cube.to_dataset()
    result.attrs.update(
        {
            "source": "synthetic" if synthetic else "mock_streaming_backend",
            "is_synthetic": synthetic,
            "requested_start": "2024-01-01",
            "requested_end": "2024-01-03",
        }
    )
    return result


@pytest.fixture()
def noun_backends(monkeypatch):
    calls: list[tuple[str, dict]] = []

    def gridmet(**kwargs):
        calls.append(("gridmet", kwargs))
        return _climate_dataset(kwargs["variable"])

    def prism(**kwargs):
        calls.append(("prism", kwargs))
        dataset = _climate_dataset(kwargs["variable"])
        array = dataset[kwargs["variable"]].copy(deep=False)
        array.attrs.update(dataset.attrs)
        return array

    monkeypatch.setattr("cubedynamics.data.nouns._gridmet.load_gridmet_cube", gridmet)
    monkeypatch.setattr("cubedynamics.data.nouns._prism.load_prism_cube", prism)
    return calls


def test_discovery_lists_only_implemented_nouns_and_sources() -> None:
    catalog = data.list_sources()

    assert catalog["temperature"] == ("gridmet", "prism")
    assert catalog["surface_reflectance"] == ("sentinel2",)
    assert data.sources("precipitation") == ("gridmet", "prism")
    assert "daymet" not in data.sources("temperature")

    description = data.describe("temperature", source="prism")
    assert description["provider"] == "PRISM Climate Group, Oregon State University"
    assert description["source_variables"]["mean"] == "tmean"
    assert description["backend"] == "NCSCO THREDDS NetCDF Subset Service"
    assert description["source_mode"] == "rolling"
    assert description["current_serving_revision"] == "temperature.prism@2026-08-26.1"
    assert description["revision_status"] == "VALIDATED"
    assert description["live_health"] == "STALE"


def test_discovery_errors_name_available_choices() -> None:
    with pytest.raises(ValueError, match="Available nouns"):
        data.sources("roads")
    with pytest.raises(ValueError, match="Available sources: gridmet"):
        data.describe("wind", source="prism")


@pytest.mark.parametrize(
    ("function", "source", "extra", "expected_variable", "expected_name"),
    [
        (data.temperature, "gridmet", {"statistic": "minimum"}, "tmmn", "temperature"),
        (data.temperature, "prism", {"statistic": "mean"}, "tmean", "temperature"),
        (data.precipitation, "gridmet", {}, "pr", "precipitation"),
        (data.precipitation, "prism", {}, "ppt", "precipitation"),
        (data.vpd, "gridmet", {}, "vpd", "vpd"),
        (data.wind, "gridmet", {}, "vs", "wind"),
        (data.humidity, "gridmet", {"statistic": "minimum"}, "rmin", "humidity"),
        (data.radiation, "gridmet", {}, "srad", "radiation"),
    ],
)
def test_climate_nouns_hide_provider_variables_and_preserve_laziness(
    noun_backends, function, source, extra, expected_variable, expected_name
) -> None:
    result = function(
        source=source,
        bbox=[-105.4, 40.0, -105.25, 40.05],
        start="2024-01-01",
        end="2024-01-03",
        show_progress=False,
        **extra,
    )

    backend, request = noun_backends[-1]
    assert backend == source
    assert request["variable"] == expected_variable
    assert request["allow_synthetic"] is False
    assert request["freq"] == "D"
    assert result.name == expected_name
    assert isinstance(result.data, da.Array)
    assert result.attrs["scientific_noun"] == expected_name
    assert result.attrs["semantic_name"] == expected_name
    assert result.attrs["semantic_kind"] == "continuous_field"
    assert result.attrs["semantic_category"] == "climate"
    assert json.loads(result.attrs["semantic_dimensions"]) == ["time", "y", "x"]
    assert result.attrs["source_flavor"] == source
    assert result.attrs["serving_revision"].startswith(f"{expected_name}.{source}@")
    assert result.attrs["source_mode"] == "rolling"
    assert result.attrs["qa_profile"] == "climate_continuous_daily"
    assert result.attrs["revision_status"] == "VALIDATED"
    assert result.attrs["live_health"] == "STALE"
    # NetCDF-safe public metadata uses integer flags rather than unsupported
    # Python Boolean attributes; truth semantics remain explicit.
    assert result.attrs["bounded_access"] == 1
    assert result.attrs["schema_fingerprint"].startswith("sha256:")
    assert json.loads(result.attrs["upstream_identity"])["endpoint"]
    assert result.attrs["is_synthetic"] == 0
    assert result.attrs["temporal_support_type"] == "interval"
    assert result.attrs["temporal_support_known"] == 1
    assert result.attrs["temporal_reference_timezone"] == "UTC"
    expected_offsets = {
        "prism": ("-12h", "12h", "day_ending"),
        "gridmet": ("7h", "31h", "calendar_day_starting"),
    }
    start_offset, end_offset, convention = expected_offsets[source]
    assert result.attrs["temporal_support_start_offset"] == start_offset
    assert result.attrs["temporal_support_end_offset"] == end_offset
    assert result.attrs["temporal_label_convention"] == convention
    assert json.loads(result.attrs["source_variables"]) == [expected_variable]
    assert json.loads(result.attrs["spatial_query"])["bbox"] == [
        -105.4,
        40.0,
        -105.25,
        40.05,
    ]

    summary = (pipe(result) | v.mean(dim="time", keep_dim=False)).unwrap()
    assert summary.dims == ("y", "x")
    assert isinstance(summary.data, da.Array)


def test_temperature_rejects_a_statistic_the_source_does_not_publish(noun_backends) -> None:
    with pytest.raises(ValueError, match="gridmet.*Available choices: maximum, minimum"):
        data.temperature(
            source="gridmet",
            statistic="mean",
            lat=40.0,
            lon=-105.3,
            start="2024-01-01",
            end="2024-01-03",
        )


def test_noun_api_refuses_explicit_synthetic_fallback() -> None:
    with pytest.raises(ValueError, match="never return synthetic fallback"):
        data.precipitation(
            source="gridmet",
            lat=40.0,
            lon=-105.3,
            start="2024-01-01",
            end="2024-01-03",
            allow_synthetic=True,
        )


def test_noun_api_rejects_a_backend_that_mislabels_generated_data(monkeypatch) -> None:
    monkeypatch.setattr(
        "cubedynamics.data.nouns._gridmet.load_gridmet_cube",
        lambda **kwargs: _climate_dataset(kwargs["variable"], synthetic=True),
    )

    with pytest.raises(RuntimeError, match="refuse"):
        data.wind(
            source="gridmet",
            lat=40.0,
            lon=-105.3,
            start="2024-01-01",
            end="2024-01-03",
        )


def test_surface_reflectance_tracks_bands_and_source(monkeypatch) -> None:
    calls = {}

    def fake_s2(**kwargs):
        calls.update(kwargs)
        values = da.ones((2, 2, 3, 4), chunks=(1, 2, 3, 2))
        return xr.DataArray(
            values,
            dims=("time", "y", "x", "band"),
            coords={
                "time": pd.date_range("2024-06-01", periods=2),
                "y": [0, 1],
                "x": [0, 1, 2],
                "band": kwargs["bands"],
            },
            name="reflectance",
            attrs={"crs": "EPSG:32613", "source": "sentinel2"},
        )

    monkeypatch.setattr("cubedynamics.data.nouns._sentinel2.load_s2_cube", fake_s2)
    result = data.surface_reflectance(
        source="sentinel2",
        lat=40.0,
        lon=-105.3,
        start="2024-06-01",
        end="2024-06-02",
        variables=["B02", "B03", "B04", "B08"],
    )

    assert calls["bands"] == ["B02", "B03", "B04", "B08"]
    assert result.attrs["scientific_noun"] == "surface_reflectance"
    assert result.attrs["data_state"] == "raw"
    assert result.attrs["crs"] == "EPSG:32613"
    assert isinstance(result.data, da.Array)


def test_vegetation_index_is_explicitly_derived(monkeypatch) -> None:
    values = da.from_array(np.array([[[0.2]], [[0.6]]], dtype="float32"), chunks=(1, 1, 1))
    ndvi = xr.DataArray(
        values,
        dims=("time", "y", "x"),
        coords={"time": pd.date_range("2024-06-01", periods=2), "y": [0], "x": [0]},
        name="ndvi",
    )
    monkeypatch.setattr(
        "cubedynamics.data.nouns._sentinel2.load_s2_ndvi_cube", lambda **kwargs: ndvi
    )

    result = data.vegetation_index(
        source="sentinel2",
        index="ndvi",
        lat=40.0,
        lon=-105.3,
        start="2024-06-01",
        end="2024-06-02",
    )

    assert result.name == "ndvi"
    assert result.attrs["scientific_noun"] == "vegetation_index"
    assert result.attrs["data_state"] == "derived"
    assert "NDVI" in result.attrs["normalization"]
    assert json.loads(result.attrs["source_variables"]) == ["B08", "B04"]
