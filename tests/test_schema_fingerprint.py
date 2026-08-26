"""Scientific schema fingerprints are stable and interpretation-sensitive."""

from __future__ import annotations

import dask.array as da
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import data


def _dataset() -> xr.Dataset:
    values = da.ones((2, 3, 4), chunks=(1, 3, 2), dtype="float32")
    array = xr.DataArray(
        values,
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2024-01-01", periods=2),
            "y": [40.0, 40.1, 40.2],
            "x": [-105.4, -105.3, -105.2, -105.1],
        },
        name="temperature",
        attrs={"units": "K", "grid_mapping": "spatial_ref"},
    )
    dataset = array.to_dataset()
    dataset.attrs["spatial_reference"] = "EPSG:4326"
    return dataset


def test_equivalent_schema_is_stable_across_size_chunks_and_retrieval_metadata() -> None:
    first = _dataset()
    second = first.isel(time=slice(0, 1)).chunk({"x": 4})
    first.attrs["retrieved_at"] = "2026-01-01T00:00:00Z"
    second.attrs["retrieved_at"] = "2026-08-26T00:00:00Z"

    assert data.schema_fingerprint(first) == data.schema_fingerprint(second)


def test_dataset_variable_order_does_not_change_fingerprint() -> None:
    first = _dataset()
    first["precipitation"] = first.temperature.assign_attrs(units="mm")
    second = first[["precipitation", "temperature"]]

    assert data.schema_fingerprint(first) == data.schema_fingerprint(second)


def test_meaningful_schema_changes_change_fingerprint() -> None:
    baseline = _dataset()
    changed_units = baseline.copy(deep=False)
    changed_units.temperature.attrs = {**baseline.temperature.attrs, "units": "degC"}
    changed_order = baseline.transpose("time", "x", "y")
    changed_dtype = baseline.astype("float64")

    fingerprint = data.schema_fingerprint(baseline)
    assert data.schema_fingerprint(changed_units) != fingerprint
    assert data.schema_fingerprint(changed_order) != fingerprint
    assert data.schema_fingerprint(changed_dtype) != fingerprint


def test_normalized_schema_does_not_contain_dimension_sizes_or_chunk_shapes() -> None:
    normalized = data.normalize_xarray_schema(_dataset())
    text = repr(normalized)

    assert normalized["dimensions"] == ["time", "x", "y"]
    assert "chunks" not in text
    assert "sizes" not in text


def test_vector_and_api_schema_drift_is_explainable() -> None:
    vector = data.normalize_vector_schema(
        fields={"reach_id": "string", "length_m": "float64"},
        geometry_type="LineString",
        crs="EPSG:4326",
        layer_id="roads",
    )
    reordered = data.normalize_vector_schema(
        fields={"length_m": "float64", "reach_id": "string"},
        geometry_type="LineString",
        crs="EPSG:4326",
        layer_id="roads",
    )
    changed = data.normalize_vector_schema(
        fields={"reach_id": "string", "length_m": "float32"},
        geometry_type="LineString",
        crs="EPSG:4326",
        layer_id="roads",
    )
    assert data.fingerprint_normalized_schema(vector) == data.fingerprint_normalized_schema(reordered)
    report = data.compare_normalized_schemas(vector, changed)
    assert report["matches"] is False
    assert report["changes"][0]["path"] == "$.fields.length_m"

    api = data.normalize_api_schema(
        fields={"time": "datetime", "value": "float64"},
        units={"value": "m3 s-1"},
        parameter_ids={"value": "00060"},
        geography_ids=("site_no",),
        datetime_representation="ISO-8601 UTC",
    )
    assert data.fingerprint_normalized_schema(api).startswith("sha256:")
