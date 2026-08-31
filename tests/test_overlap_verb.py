"""Tests for the strict aligned-state overlap verb."""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from cubedynamics import pipe
from cubedynamics import verbs as v


def _state(values: list[list[bool]], *, x: tuple[int, int] = (0, 1)) -> xr.Dataset:
    state = xr.DataArray(
        np.asarray(values, dtype=bool),
        dims=("time", "x"),
        coords={"time": [0, 1], "x": list(x)},
        name="state",
    )
    return xr.Dataset({"state": state, "magnitude": state.astype(float)})


def test_overlap_composes_state_datasets_in_a_pipe() -> None:
    hot = _state([[True, False], [True, True]])
    dry = _state([[True, True], [False, True]])

    result = (pipe(hot) | v.overlap(dry, name="hot_and_dry")).unwrap()

    assert isinstance(result, xr.Dataset)
    assert set(result.data_vars) == {"state"}
    assert result["state"].dtype == bool
    assert result.attrs["alignment"] == "exact"
    assert result.attrs["semantic_kind"] == "condition"
    assert result.attrs["analysis"] == "state_cube"
    assert result.attrs["condition_operation"] == "aligned_boolean_overlap"
    assert result.attrs["left_condition"] == "state"
    assert result.attrs["right_condition"] == "state"
    np.testing.assert_array_equal(result["state"], [[True, False], [False, True]])


def test_overlap_reports_shifted_spatial_coordinates() -> None:
    left = _state([[True, False], [True, True]])
    shifted = _state([[True, True], [False, True]], x=(1, 2))

    with pytest.raises(ValueError, match="spatial coordinates differ along 'x'"):
        (pipe(left) | v.overlap(shifted)).unwrap()


def test_overlap_reports_shifted_temporal_coordinates() -> None:
    left = _state([[True, False], [True, True]])
    shifted = _state([[True, True], [False, True]]).assign_coords(time=[1, 2])

    with pytest.raises(ValueError, match="temporal coordinates differ along 'time'"):
        (pipe(left) | v.overlap(shifted)).unwrap()


def test_overlap_normalizes_harmless_dimension_order() -> None:
    left = _state([[True, False], [True, True]])
    reordered = _state([[True, True], [False, True]]).transpose("x", "time")

    result = (pipe(left) | v.overlap(reordered)).unwrap()

    assert result["state"].dims == ("time", "x")
    np.testing.assert_array_equal(result["state"], [[True, False], [False, True]])


def test_overlap_composes_three_conditions_and_reduces_to_proportion() -> None:
    first = _state([[True, True], [True, True]])
    second = _state([[True, False], [True, True]])
    third = _state([[True, True], [False, True]])

    combined = (
        pipe(first)
        | v.overlap(second, name="first_and_second")
        | v.overlap(third, name="all_three")
    ).unwrap()
    summary = (pipe(combined) | v.mean(dim="time", keep_dim=False)).unwrap()

    assert set(combined.data_vars) == {"state"}
    assert set(summary.data_vars) == {"state"}
    assert summary.attrs["semantic_kind"] == "summary"
    assert summary["state"].attrs["semantic_units"] == "proportion"
    np.testing.assert_array_equal(summary["state"], [0.5, 0.5])


def test_overlap_requires_explicit_variable_for_ambiguous_dataset() -> None:
    ambiguous = xr.Dataset(
        {
            "a": xr.DataArray([True, False], dims="x"),
            "b": xr.DataArray([False, True], dims="x"),
        }
    )

    with pytest.raises(ValueError, match="right_variable"):
        v.overlap(ambiguous)
