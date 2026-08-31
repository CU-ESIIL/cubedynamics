"""Unit tests for standardized cube verbs."""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v


def test_mean_keep_dim_preserves_cube_shape(tiny_cube):
    result = (pipe(tiny_cube) | v.mean(dim="time", keep_dim=True)).unwrap()
    assert result.dims == tiny_cube.dims
    assert result.sizes["time"] == 1


def test_variance_drop_dim_when_requested(tiny_cube):
    result = (pipe(tiny_cube) | v.variance(dim="time", keep_dim=False)).unwrap()
    assert "time" not in result.dims


def test_mean_of_condition_relabels_state_as_proportion_summary(tiny_cube):
    tiny_cube.attrs.update(
        {
            "semantic_name": "observed temperature",
            "source_provider": "test fixture",
        }
    )
    condition = (
        pipe(tiny_cube)
        | v.threshold_state(threshold=0.5, direction="above", name="warm")
    ).unwrap()

    result = (
        pipe(condition)
        | v.mean(dim=("time", "y", "x"), keep_dim=False)
    ).unwrap()

    assert isinstance(result, xr.Dataset)
    assert set(result.data_vars) == {"state"}
    assert result.attrs["semantic_kind"] == "summary"
    assert result.attrs["semantic_category"] == "summary"
    assert result.attrs["analysis"] == "reduction_summary"
    assert result.attrs["summary_dimensions"] == "time,y,x"
    assert "semantic_units" not in result.attrs
    assert "units" not in result.attrs
    assert result.attrs["source_provider"] == "test fixture"
    assert result.attrs["threshold_value"] == 0.5
    assert result.attrs["excluded_condition_fields"] == "magnitude,threshold"
    assert result["state"].attrs["semantic_kind"] == "summary"
    assert result["state"].attrs["semantic_category"] == "condition_frequency"
    assert result["state"].attrs["semantic_units"] == "proportion"
    assert result["state"].attrs["units"] == "1"
    assert 0.0 <= result["state"].item() <= 1.0


@pytest.mark.parametrize(
    ("units", "expected"),
    [
        ("degC", "degC^2"),
        ("mm", "mm^2"),
        ("kPa", "kPa^2"),
        ("m s-1", "(m s-1)^2"),
        ("1", "1"),
        ("dimensionless", "1"),
        ("unknown", "unknown"),
    ],
)
def test_variance_propagates_units_deterministically(tiny_cube, units, expected):
    source = tiny_cube.assign_attrs(units=units, semantic_units=units)

    result = (pipe(source) | v.variance(dim="time", keep_dim=False)).unwrap()

    assert result.attrs["units"] == expected
    assert result.attrs["semantic_units"] == expected
    assert result.attrs["semantic_kind"] == "summary"


def test_variance_does_not_invent_missing_units(tiny_cube):
    source = tiny_cube.assign_attrs({})

    result = (pipe(source) | v.variance(dim="time", keep_dim=False)).unwrap()

    assert "units" not in result.attrs
    assert "semantic_units" not in result.attrs


def test_anomaly_keep_dim_true_is_cube_ready(tiny_cube):
    source = tiny_cube.assign_attrs(
        units="degC", semantic_name="observed temperature", source_provider="fixture"
    )
    result = (pipe(source) | v.anomaly(dim="time", keep_dim=True)).unwrap()
    assert result.dims == tiny_cube.dims
    mean = result.mean(dim="time")
    assert float(np.abs(mean).max()) < 1e-6
    assert result.attrs["analysis"] == "anomaly"
    assert result.attrs["semantic_name"] == "anomaly of observed temperature"
    assert result.attrs["semantic_kind"] == "continuous_field"
    assert result.attrs["units"] == "degC"
    assert result.attrs["source_provider"] == "fixture"


def test_zscore_mean_zero_with_keep_dim(tiny_cube):
    source = tiny_cube.assign_attrs(
        units="degC", semantic_name="observed temperature", source_provider="fixture"
    )
    z = (pipe(source) | v.zscore(dim="time", keep_dim=True)).unwrap()
    assert z.dims == tiny_cube.dims
    mean = z.mean(dim="time")
    assert float(np.abs(mean).max()) < 1e-6
    assert z.attrs["analysis"] == "zscore"
    assert z.attrs["semantic_name"] == "zscore of observed temperature"
    assert z.attrs["semantic_kind"] == "continuous_field"
    assert z.attrs["units"] == "1"
    assert z.attrs["semantic_units"] == "standard deviations"
    assert z.attrs["source_provider"] == "fixture"


def test_anomaly_and_zscore_keep_dask_arrays_lazy(tiny_cube):
    da = pytest.importorskip("dask.array")
    source = tiny_cube.copy(data=da.from_array(tiny_cube.data, chunks=(2, 1, 1)))

    anomaly = (pipe(source) | v.anomaly(dim="time")).unwrap()
    zscore = (pipe(source) | v.zscore(dim="time")).unwrap()

    assert hasattr(anomaly.data, "dask")
    assert hasattr(zscore.data, "dask")
