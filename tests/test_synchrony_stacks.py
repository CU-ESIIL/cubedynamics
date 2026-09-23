"""Contracts for moving-center synchrony stacks."""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.stats.tails import one_tail_spearman, partial_tail_spearman
from cubedynamics.synchrony import (
    load_stack_checkpoint,
    stack_edges,
    write_stack_checkpoint,
)


def _cube(*, missing: bool = False, ties: bool = False) -> xr.Dataset:
    rng = np.random.default_rng(14)
    time = np.datetime64("2024-01-01") + np.arange(18).astype("timedelta64[D]")
    y = np.array([40.1, 40.0, 39.9])
    x = np.array([-105.2, -105.1, -105.0])
    base = rng.normal(size=(time.size, y.size, x.size))
    tmin = base + np.linspace(-2, 2, time.size)[:, None, None]
    tmax = 0.6 * base + rng.normal(scale=0.5, size=base.shape)
    if ties:
        tmin = np.round(tmin, 0)
        tmax = np.round(tmax, 0)
    if missing:
        tmin[[1, 5], 0, 0] = np.nan
        tmin[[2, 7], 2, 2] = np.nan
        tmax[[0, 4], 0, 0] = np.nan
        tmax[[3, 8], 2, 2] = np.nan
    result = xr.Dataset(
        {
            "tmin": (("time", "y", "x"), tmin),
            "tmax": (("time", "y", "x"), tmax),
        },
        coords={"time": time, "y": y, "x": x},
    )
    result["y"].attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    result["x"].attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    return result


@pytest.mark.parametrize("missing,ties,min_t", [(False, False, 4), (True, False, 4), (False, True, 4), (True, True, 12)])
def test_pair_statistic_is_exactly_symmetric(missing: bool, ties: bool, min_t: int) -> None:
    cube = _cube(missing=missing, ties=ties)
    for variable, output_index in (("tmin", 0), ("tmax", 1)):
        left = cube[variable].values[:, 0, 0]
        right = cube[variable].values[:, 2, 2]
        forward = partial_tail_spearman(left, right, min_t=min_t)[output_index]
        reverse = partial_tail_spearman(right, left, min_t=min_t)[output_index]
        np.testing.assert_allclose(forward, reverse, atol=0, rtol=0, equal_nan=True)


def test_single_tail_kernel_matches_existing_two_tail_source_of_truth() -> None:
    cube = _cube(missing=True, ties=True)
    for variable in ("tmin", "tmax"):
        left = cube[variable].values[:, 0, 0]
        right = cube[variable].values[:, 2, 2]
        lower, upper, _ = partial_tail_spearman(left, right, min_t=4)
        lower_single, lower_count = one_tail_spearman(
            left, right, tail="lower", min_t=4
        )
        upper_single, upper_count = one_tail_spearman(
            left, right, tail="upper", min_t=4
        )
        np.testing.assert_allclose(lower_single, lower, atol=0, rtol=0, equal_nan=True)
        np.testing.assert_allclose(upper_single, upper, atol=0, rtol=0, equal_nan=True)
        assert lower_count >= 0
        assert upper_count >= 0


def test_stack_matches_center_reference_verb_pixel_by_pixel() -> None:
    cube = _cube()
    center_result = v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=40,
        min_t=4,
        output_times=[cube.time.values[-1]],
    )(cube)
    stack = v.local_synchrony_stack(
        lower_var="tmin",
        upper_var="tmax",
        window_days=40,
        min_t=4,
        center_y_indices=[1],
        center_x_indices=[1],
    )(cube)
    np.testing.assert_allclose(
        stack.cold_synchrony.isel(center=0),
        center_result.bottom_synchrony.isel(time_window_end=0),
        atol=1e-7,
        rtol=0,
        equal_nan=True,
    )
    np.testing.assert_allclose(
        stack.warm_synchrony.isel(center=0),
        center_result.top_synchrony.isel(time_window_end=0),
        atol=1e-7,
        rtol=0,
        equal_nan=True,
    )
    np.testing.assert_allclose(
        stack.delta_s.isel(center=0),
        center_result.bottom_minus_top.isel(time_window_end=0),
        atol=1e-7,
        rtol=0,
        equal_nan=True,
    )


def test_stack_is_pipe_friendly_and_symmetric_with_self_layers() -> None:
    cube = _cube(missing=True, ties=True)
    stack = (
        pipe(cube)
        | v.local_synchrony_stack(
            lower_var="tmin",
            upper_var="tmax",
            window_days=40,
            min_t=4,
        )
    ).unwrap()
    assert stack.sizes["center"] == 9
    assert stack.attrs["unique_pair_count"] == 45
    assert stack.attrs["requested_relationship_count"] == 81
    for left in range(9):
        left_y, left_x = divmod(left, 3)
        for right in range(9):
            right_y, right_x = divmod(right, 3)
            for name in ("cold_synchrony", "warm_synchrony", "delta_s"):
                np.testing.assert_allclose(
                    stack[name].values[left, right_y, right_x],
                    stack[name].values[right, left_y, left_x],
                    atol=0,
                    rtol=0,
                    equal_nan=True,
                )
    edges = stack_edges(stack)
    assert edges.sizes["pair"] == 45


def test_reductions_retain_coverage_distance_and_direction() -> None:
    stack = v.local_synchrony_stack(
        lower_var="tmin", upper_var="tmax", window_days=40, min_t=4
    )(_cube())
    reduced = v.reduce_synchrony_stack(
        metric="delta_s", near_field_km=20, distance_decay_km=50
    )(stack)
    required = {
        "valid_center_count",
        "spatial_coverage",
        "mean",
        "median",
        "standard_deviation",
        "iqr",
        "mad",
        "minimum",
        "maximum",
        "distance_weighted_mean",
        "near_field_median",
        "direction_n_mean",
    }
    assert required <= set(reduced.data_vars)
    assert float(reduced.spatial_coverage.max()) <= 1.0


def test_panel_similarity_is_distinct_and_returns_change_map() -> None:
    stack = v.local_synchrony_stack(
        lower_var="tmin", upper_var="tmax", window_days=40, min_t=4
    )(_cube())
    result = v.synchrony_landscape_similarity(min_overlap=4)(stack)
    assert result.sizes["comparison"] == 12
    assert result.mean_adjacent_landscape_change.shape == (3, 3)
    assert result.attrs["pair_synchrony_distinction"] == "Q compares panels and is not S(A,B)"
    np.testing.assert_allclose(
        result.landscape_change,
        1.0 - result.panel_similarity,
        equal_nan=True,
    )


def test_checkpoint_rejects_incompatible_resume(tmp_path) -> None:
    stack = v.local_synchrony_stack(
        lower_var="tmin", upper_var="tmax", window_days=40, min_t=4
    )(_cube())
    target = write_stack_checkpoint(stack, tmp_path / "tile.nc")
    restored = load_stack_checkpoint(
        target, expected_fingerprint=stack.attrs["analysis_fingerprint"]
    )
    xr.testing.assert_allclose(restored.delta_s, stack.delta_s)
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        load_stack_checkpoint(target, expected_fingerprint="sha256:not-the-same")


def test_radius_masks_distant_focals_but_preserves_stack_shape() -> None:
    stack = v.local_synchrony_stack(
        lower_var="tmin",
        upper_var="tmax",
        window_days=40,
        min_t=4,
        max_radius_km=1.0,
    )(_cube())
    assert stack.delta_s.shape == (9, 3, 3)
    assert stack.attrs["unique_pair_count"] == 9
    assert stack.attrs["computed_relationship_count"] == 9
    assert int(stack.delta_s.count()) == 9
    np.testing.assert_array_equal(stack.distance_km.values == 0, stack.delta_s.notnull().values)


def test_stack_refuses_to_guess_geographic_coordinates() -> None:
    cube = _cube()
    cube["y"].attrs.clear()
    cube["x"].attrs.clear()
    with pytest.raises(ValueError, match="explicit latitude/longitude metadata"):
        v.local_synchrony_stack(
            lower_var="tmin", upper_var="tmax", window_days=40, min_t=4
        )(cube)
