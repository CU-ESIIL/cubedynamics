"""Contracts for the four-round adaptive synchrony experiment."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.synchrony.adaptive import (
    VALID_BREAK_CODES,
    adaptive_synchrony_experiment,
    empirical_break_curve,
)
from cubedynamics.synchrony.production import (
    distance_stratified_pair_sample,
    local_synchrony_pairs,
)


def _curve(break_km: float, *, seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    distance: list[float] = []
    values: list[float] = []
    for index, center in enumerate(np.arange(12.5, 1000.0, 25.0)):
        level = 0.90 - 0.0022 * min(center, break_km) - 0.00015 * max(
            0.0, center - break_km
        )
        distance.extend(rng.uniform(index * 25 + 0.1, (index + 1) * 25 - 0.1, 100))
        values.extend(level + rng.normal(0.0, 0.015, 100))
    return np.asarray(distance), np.asarray(values)


def _pair_table() -> xr.Dataset:
    distance, cold = _curve(200.0, seed=1)
    _, warm = _curve(300.0, seed=2)
    warm = warm + 0.025 * np.sin(distance / 70.0)
    count = distance.size
    result = xr.Dataset(
        {
            "cold_synchrony": ("pair", cold),
            "warm_synchrony": ("pair", warm),
            "delta_s": ("pair", cold - warm),
            "distance_km": ("pair", distance.astype(np.float32)),
            "sampling_probability": ("pair", np.ones(count, dtype=np.float32)),
            "output_mask": (("y", "x"), np.r_[True, np.zeros(count, dtype=bool)][None, :]),
        },
        coords={
            "pair": np.arange(count),
            "y": [40.0],
            "x": np.arange(count + 1),
            "source_index": ("pair", np.zeros(count, dtype=np.int64)),
            "target_index": ("pair", np.arange(1, count + 1, dtype=np.int64)),
            "time_window_end": np.datetime64("2024-01-30"),
        },
        attrs={
            "analysis": "local_synchrony_pairs",
            "semantic_kind": "relationship",
            "semantic_category": "sparse_local_relationships",
            "analysis_fingerprint": "sha256:test-pairs",
            "max_radius_km": 1000.0,
            "distance_sampling_design": "dense test relationships",
        },
    )
    return result


def _cube() -> xr.Dataset:
    rng = np.random.default_rng(20260925)
    time = np.datetime64("2024-01-01") + np.arange(30).astype("timedelta64[D]")
    y = np.linspace(40.3, 39.7, 9)
    x = np.linspace(-105.3, -104.7, 9)
    shared = rng.normal(size=(30, 1, 1))
    tmin = shared + rng.normal(scale=0.5, size=(30, 9, 9))
    tmax = -0.2 * shared + rng.normal(scale=0.6, size=(30, 9, 9))
    result = xr.Dataset(
        {"tmin": (("time", "y", "x"), tmin), "tmax": (("time", "y", "x"), tmax)},
        coords={"time": time, "y": y, "x": x},
        attrs={"source": "test", "serving_revision": "test-v1"},
    )
    result.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    result.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    return result


def test_first_break_recovers_local_transition_not_final_background() -> None:
    distance, values = _curve(200.0)
    result = empirical_break_curve(
        distance,
        values,
        discovery_radius_km=1000,
        bin_width_km=25,
        min_annulus_count=30,
    )
    assert result.attrs["break_status"] in VALID_BREAK_CODES
    assert abs(result.attrs["break_km"] - 200.0) <= 50.0
    assert result.attrs["break_km"] < result.attrs["background_approach_candidate_km"]
    assert result.attrs["parametric_kernel"] == "none"
    assert result.attrs["monotonicity_forced"] == "no"


def test_local_break_is_stable_when_observation_domain_expands() -> None:
    distance, values = _curve(200.0)
    estimates = []
    for maximum in (500.0, 750.0, 1000.0):
        result = empirical_break_curve(
            distance,
            values,
            discovery_radius_km=maximum,
            bin_width_km=25,
            min_annulus_count=30,
        )
        estimates.append(result.attrs["break_km"])
    assert np.all(np.isfinite(estimates))
    assert np.ptp(estimates) <= 50.0


def test_adaptive_experiment_uses_common_max_and_pairwise_delta() -> None:
    pairs = _pair_table()
    result = adaptive_synchrony_experiment(
        pairs,
        discovery_radius_km=1000,
        fixed_radius_km=500,
        bin_width_km=25,
        min_annulus_count=30,
    )
    cold = result.cold_break_km.values[0, 0, 0]
    warm = result.warm_break_km.values[0, 0, 0]
    common = result.common_break_km.values[0, 0, 0]
    assert np.isfinite(cold) and np.isfinite(warm)
    assert common == max(cold, warm)
    distance = pairs.distance_km.values
    within = distance <= common
    expected_delta = np.median(pairs.delta_s.values[within])
    np.testing.assert_allclose(result.adaptive_delta_median.values[0, 0, 0], expected_delta)
    assert result.adaptive_delta_median.attrs["definition"].startswith(
        "design-weighted median of pairwise"
    )
    assert result.attrs["maximum_discovery_radius_role"].endswith("not estimated scale")


def test_pipe_verb_matches_direct_adaptive_experiment() -> None:
    pairs = _pair_table()
    direct = adaptive_synchrony_experiment(pairs, min_annulus_count=30)
    piped = (
        pipe(pairs) | v.adaptive_synchrony_experiment(min_annulus_count=30)
    ).unwrap()
    xr.testing.assert_equal(piped, direct)


def test_distance_sampling_is_deterministic_and_records_design_probability() -> None:
    cube = _cube()
    output = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    output.values[4, 4] = True
    plan = ((10.0, None), (100.0, 7))
    first = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        max_radius_km=100,
        min_t=5,
        distance_sampling=plan,
        sampling_seed=42,
    )
    second = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        max_radius_km=100,
        min_t=5,
        distance_sampling=plan,
        sampling_seed=42,
    )
    xr.testing.assert_equal(first, second)
    nonself = first.source_index.values != first.target_index.values
    assert int(np.count_nonzero(nonself & (first.sampling_stratum.values == 1))) == 7
    assert np.all(first.sampling_probability.values[nonself] > 0)
    assert np.any(first.sampling_probability.values[nonself] < 1)
    assert first.attrs["candidate_nonself_pair_count"] > first.attrs["nonself_pair_count"]
    assert first.attrs["pair_enumeration"] == "focal query-ball union for sparse output mask"


def test_uncapped_sampling_is_exactly_equivalent_to_dense_pair_table() -> None:
    cube = _cube()
    output = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    output.values[4, 4] = True
    dense = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        max_radius_km=100,
        min_t=5,
    )
    uncapped = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        max_radius_km=100,
        min_t=5,
        distance_sampling=((100.0, None),),
    )
    for name in ("cold_synchrony", "warm_synchrony", "delta_s", "distance_km"):
        np.testing.assert_allclose(uncapped[name], dense[name], equal_nan=True)
    np.testing.assert_array_equal(uncapped.source_index, dense.source_index)
    np.testing.assert_array_equal(uncapped.target_index, dense.target_index)


def test_posthoc_sample_reuses_exact_direct_pair_selection() -> None:
    cube = _cube()
    output = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    output.values[4, 4] = True
    plan = ((10.0, None), (100.0, 7))
    dense = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        max_radius_km=100,
        min_t=5,
    )
    posthoc = distance_stratified_pair_sample(
        dense, distance_sampling=plan, sampling_seed=42
    )
    direct = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        max_radius_km=100,
        min_t=5,
        distance_sampling=plan,
        sampling_seed=42,
    )
    np.testing.assert_array_equal(posthoc.source_index, direct.source_index)
    np.testing.assert_array_equal(posthoc.target_index, direct.target_index)
    np.testing.assert_allclose(posthoc.sampling_probability, direct.sampling_probability)
    np.testing.assert_allclose(posthoc.cold_synchrony, direct.cold_synchrony, equal_nan=True)
