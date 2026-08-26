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

    assert result.name == "hot_and_dry"
    assert result.dtype == bool
    assert result.attrs["alignment"] == "exact"
    np.testing.assert_array_equal(result, [[True, False], [False, True]])


def test_overlap_refuses_silent_coordinate_alignment() -> None:
    left = _state([[True, False], [True, True]])
    shifted = _state([[True, True], [False, True]], x=(1, 2))

    with pytest.raises(ValueError, match="identical dimensions and coordinates"):
        (pipe(left) | v.overlap(shifted)).unwrap()


def test_overlap_requires_explicit_variable_for_ambiguous_dataset() -> None:
    ambiguous = xr.Dataset(
        {
            "a": xr.DataArray([True, False], dims="x"),
            "b": xr.DataArray([False, True], dims="x"),
        }
    )

    with pytest.raises(ValueError, match="right_variable"):
        v.overlap(ambiguous)
