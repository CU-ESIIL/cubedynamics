"""Contracts for kernel-agnostic empirical synchrony-range estimation."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.synchrony.baseline import nonstacked_synchrony_summary
from cubedynamics.synchrony.production import local_synchrony_pairs
from cubedynamics.synchrony.ranges import (
    empirical_range_curve,
    empirical_synchrony_range,
    tiled_empirical_synchrony_range,
)


def _curve(levels: list[float], *, count: int = 100) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260924)
    distance = []
    values = []
    for index, level in enumerate(levels):
        distance.extend(rng.uniform(index * 20 + 0.1, (index + 1) * 20 - 0.1, count))
        values.extend(level + rng.normal(0, 0.006, count))
    return np.asarray(distance), np.asarray(values)


def _cube() -> xr.Dataset:
    rng = np.random.default_rng(20260924)
    time = np.datetime64("2023-11-01") + np.arange(35).astype("timedelta64[D]")
    y = np.linspace(40.3, 39.7, 9)
    x = np.linspace(-105.3, -104.7, 9)
    shared = rng.normal(size=(time.size, 1, 1))
    tmin = shared + rng.normal(scale=0.45, size=(35, 9, 9))
    tmax = -0.3 * shared + rng.normal(scale=0.65, size=(35, 9, 9))
    cube = xr.Dataset(
        {"tmin": (("time", "y", "x"), tmin), "tmax": (("time", "y", "x"), tmax)},
        coords={"time": time, "y": y, "x": x},
        attrs={"source": "deterministic test cube", "serving_revision": "test-v1"},
    )
    cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    return cube


def _mask(cube: xr.Dataset) -> xr.DataArray:
    mask = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    mask.values[3:6, 3:6] = True
    return mask


def test_curve_finds_persistent_nonzero_background_without_kernel() -> None:
    levels = [0.80, 0.60, 0.40, 0.30, 0.25, 0.22, 0.205] + [0.20] * 13
    distance, values = _curve(levels)
    result = empirical_range_curve(
        distance,
        values,
        discovery_radius_km=400,
        bin_width_km=20,
        min_annulus_count=30,
    )
    assert result.attrs["status"] == "resolved"
    assert result.attrs["range_km"] == 240.0
    assert 0.19 < result.attrs["selected_background"] < 0.21
    assert result.attrs["range_reliability"] >= 0.60
    assert result.attrs["range_km"] < 0.80 * 400
    assert "kernel" not in result.attrs["criterion"].lower()


def test_flat_curve_is_not_mislabeled_as_a_range() -> None:
    distance, _ = _curve([0.5] * 20)
    result = empirical_range_curve(
        distance,
        np.full(distance.size, 0.5),
        discovery_radius_km=400,
        min_annulus_count=30,
    )
    assert result.attrs["status"] == "flat_or_no_identifiable_focal_signal"
    assert np.isnan(result.attrs["range_km"])


def test_boundary_limited_curve_is_unresolved_not_equal_to_discovery_radius() -> None:
    distance, values = _curve(list(np.linspace(0.9, 0.2, 20)))
    result = empirical_range_curve(
        distance,
        values,
        discovery_radius_km=400,
        min_annulus_count=30,
    )
    assert result.attrs["status"] == "right_censored_or_unresolved"
    assert result.attrs["censored"]
    assert np.isnan(result.attrs["range_km"])


def test_three_background_definitions_are_retained() -> None:
    distance, values = _curve([0.8, 0.6, 0.4, 0.3] + [0.2] * 16)
    result = empirical_range_curve(
        distance,
        values,
        discovery_radius_km=400,
        min_annulus_count=30,
        background_method="distant_pairs",
    )
    for name in (
        "background_outer_annuli",
        "background_smoothed_outer_annuli",
        "background_distant_pairs",
    ):
        assert np.isfinite(result.attrs[name])
    assert result.attrs["selected_background"] == result.attrs["background_distant_pairs"]


def test_pair_reducer_reuses_fixed_control_exactly_and_excludes_self() -> None:
    cube = _cube()
    mask = _mask(cube)
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=65,
        min_t=5,
    )
    expected = nonstacked_synchrony_summary(pairs, radii_km=(50,))
    result = empirical_synchrony_range(
        pairs,
        bin_width_km=10,
        min_annulus_count=2,
        background_shell_count=2,
        persistence_bins=2,
        fixed_radius_km=50,
    )
    for actual_name, expected_name in (
        ("fixed_cold_median", "cold_median"),
        ("fixed_warm_median", "warm_median"),
        ("fixed_delta_pair_median", "delta_pair_median"),
        ("fixed_delta_iqr", "delta_iqr"),
        ("fixed_delta_reduction_gap", "delta_reduction_gap"),
    ):
        xr.testing.assert_allclose(
            result[actual_name].where(mask),
            expected[expected_name].sel(radius_km=50, drop=True).where(mask),
        )
    assert result.attrs["kernel_weighting"] == "none"
    assert result.attrs["adaptive_delta_neighbor_policy"] == "same neighbors within common range"
    assert int(result.fixed_pair_count.where(mask).min(skipna=True)) > 0


def test_pipe_verb_matches_direct_reducer() -> None:
    cube = _cube()
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=_mask(cube),
        max_radius_km=65,
        min_t=5,
    )
    direct = empirical_synchrony_range(
        pairs,
        bin_width_km=10,
        min_annulus_count=2,
        background_shell_count=2,
        persistence_bins=2,
        fixed_radius_km=50,
    )
    piped = (
        pipe(pairs)
        | v.empirical_synchrony_range(
            bin_width_km=10,
            min_annulus_count=2,
            background_shell_count=2,
            persistence_bins=2,
            fixed_radius_km=50,
        )
    ).unwrap()
    xr.testing.assert_equal(piped, direct)


def test_tiled_range_matches_untiled_and_restarts(tmp_path) -> None:
    cube = _cube()
    mask = _mask(cube)
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=65,
        min_t=5,
    )
    expected = empirical_synchrony_range(
        pairs,
        bin_width_km=10,
        min_annulus_count=2,
        background_shell_count=2,
        persistence_bins=2,
        fixed_radius_km=50,
    )
    actual = tiled_empirical_synchrony_range(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        discovery_radius_km=65,
        fixed_radius_km=50,
        tile_shape=(2, 2),
        min_t=5,
        bin_width_km=10,
        min_annulus_count=2,
        background_shell_count=2,
        persistence_bins=2,
        checkpoint_dir=tmp_path,
    )
    for name in expected.data_vars:
        xr.testing.assert_allclose(actual[name].where(mask), expected[name].where(mask))
    resumed = tiled_empirical_synchrony_range(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        discovery_radius_km=65,
        fixed_radius_km=50,
        tile_shape=(2, 2),
        min_t=5,
        bin_width_km=10,
        min_annulus_count=2,
        background_shell_count=2,
        persistence_bins=2,
        checkpoint_dir=tmp_path,
    )
    assert resumed.attrs["computed_tile_count"] == 0
    assert resumed.attrs["resumed_tile_count"] == resumed.attrs["tile_count"]
