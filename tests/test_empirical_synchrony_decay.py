"""Contracts for empirical synchrony-decay characterization."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.synchrony.decay import empirical_decay_curve, empirical_synchrony_decay


def _curve(levels: list[float], *, count: int = 60) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260924)
    distance = []
    values = []
    for index, level in enumerate(levels):
        distance.extend(rng.uniform(index * 20 + 0.2, (index + 1) * 20 - 0.2, count))
        values.extend(level + rng.normal(0, 0.004, count))
    return np.asarray(distance), np.asarray(values)


def _pairs() -> xr.Dataset:
    levels_cold = np.asarray(
        [0.90, 0.84, 0.76, 0.66, 0.56, 0.48, 0.42, 0.37, 0.33, 0.30]
        + [0.27, 0.25, 0.24, 0.23, 0.22] + [0.20] * 10
    )
    levels_warm = np.asarray(
        [0.88, 0.80, 0.70, 0.60, 0.51, 0.44, 0.39, 0.35, 0.32, 0.29]
        + [0.26, 0.24, 0.23, 0.22, 0.21] + [0.19] * 10
    )
    count = levels_cold.size
    output = np.zeros((1, count + 1), dtype=bool)
    output[0, 0] = True
    return xr.Dataset(
        {
            "cold_synchrony": ("pair", levels_cold),
            "warm_synchrony": ("pair", levels_warm),
            "delta_s": ("pair", levels_cold - levels_warm),
            "distance_km": ("pair", np.arange(10.0, 10.0 + 20.0 * count, 20.0)),
            "output_mask": (("y", "x"), output),
            "computation_mask": (("y", "x"), np.ones_like(output)),
        },
        coords={
            "pair": np.arange(count),
            "source_index": ("pair", np.zeros(count, dtype=np.int64)),
            "target_index": ("pair", np.arange(1, count + 1, dtype=np.int64)),
            "time_window_end": np.datetime64("2024-01-30"),
            "y": [40.0],
            "x": np.arange(count + 1, dtype=float),
        },
        attrs={
            "analysis": "local_synchrony_pairs",
            "semantic_kind": "relationship",
            "semantic_category": "sparse_local_relationships",
            "analysis_fingerprint": "sha256:test",
            "max_radius_km": 500.0,
        },
    )


def test_fractional_decay_is_interpolated_and_not_a_hard_horizon() -> None:
    levels = [0.90, 0.82, 0.74, 0.65, 0.56, 0.49, 0.43, 0.38, 0.34, 0.31]
    levels += [0.28, 0.26, 0.24, 0.23, 0.22] + [0.20] * 10
    distance, values = _curve(levels)
    result = empirical_decay_curve(
        distance,
        values,
        discovery_radius_km=500,
        min_annulus_count=30,
    )
    assert result.attrs["d25_status"] == 3
    assert result.attrs["d50_status"] == 3
    assert result.attrs["d75_status"] == 3
    assert result.attrs["d25_km"] < result.attrs["d50_km"] < result.attrs["d75_km"]
    assert result.attrs["curve_is_monotonicized"] is False
    assert result.attrs["d50_km"] != 500


def test_noisy_single_crossing_is_not_selected_immediately() -> None:
    levels = [0.90, 0.82, 0.76, 0.35, 0.78, 0.74, 0.70, 0.66, 0.62, 0.58]
    levels += [0.54, 0.50, 0.47, 0.44, 0.42, 0.40, 0.38, 0.36, 0.34, 0.32]
    distance, values = _curve(levels)
    result = empirical_decay_curve(
        distance,
        values,
        discovery_radius_km=400,
        min_annulus_count=30,
    )
    assert result.attrs["d50_status"] == 3
    assert result.attrs["d50_km"] > 100


def test_effective_length_retains_value_and_flags_boundary_dependence() -> None:
    levels = list(np.linspace(0.90, 0.30, 16)) + [0.30, 0.30, 0.30, 0.60]
    distance, values = _curve(levels)
    result = empirical_decay_curve(
        distance,
        values,
        discovery_radius_km=400,
        min_annulus_count=30,
    )
    assert result.attrs["effective_length_km"] > 0
    assert result.attrs["effective_length_status"] == 2
    assert result.attrs["boundary_normalized_excess"] > 0.10


def test_initial_slope_is_background_free() -> None:
    levels = [0.90, 0.80, 0.70, 0.60, 0.50] + [0.45] * 15
    distance, values = _curve(levels)
    slopes = []
    for method in ("outer_annuli", "smoothed_outer_annuli", "distant_pairs"):
        result = empirical_decay_curve(
            distance,
            values,
            discovery_radius_km=400,
            min_annulus_count=30,
            background_method=method,
        )
        slopes.append(result.attrs["beta_initial_per_100km"])
    np.testing.assert_allclose(slopes, slopes[0], atol=0, rtol=0)
    assert slopes[0] < 0


def test_pair_reducer_keeps_tails_independent_and_pipe_matches() -> None:
    pairs = _pairs()
    direct = empirical_synchrony_decay(
        pairs,
        bin_width_km=20,
        min_annulus_count=1,
        background_shell_count=4,
    )
    piped = (
        pipe(pairs)
        | v.empirical_synchrony_decay(
            bin_width_km=20,
            min_annulus_count=1,
            background_shell_count=4,
        )
    ).unwrap()
    xr.testing.assert_equal(piped, direct)
    focal = dict(time_window_end=0, y=0, x=0)
    assert int(direct.cold_d50_status.isel(**focal)) == 3
    assert int(direct.warm_d50_status.isel(**focal)) == 3
    assert np.isfinite(direct.delta_d50_cold_minus_warm_km.isel(**focal))
    assert direct.attrs["parametric_kernel"] == "none"


def test_fractional_contrasts_require_both_valid_components() -> None:
    pairs = _pairs()
    pairs["warm_synchrony"] = xr.full_like(pairs.warm_synchrony, 0.5)
    pairs["delta_s"] = pairs.cold_synchrony - pairs.warm_synchrony
    result = empirical_synchrony_decay(
        pairs,
        min_annulus_count=1,
        background_shell_count=4,
    )
    focal = dict(time_window_end=0, y=0, x=0)
    assert int(result.warm_d50_status.isel(**focal)) == 1
    assert np.isnan(result.delta_d50_cold_minus_warm_km.isel(**focal))
