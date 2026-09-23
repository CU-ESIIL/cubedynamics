"""Focused contracts for Phase 1.5 synchrony-stack diagnostics."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.synchrony import compare_panels


def _observed_shape_stack() -> xr.Dataset:
    time = np.datetime64("2024-01-01") + np.arange(18).astype("timedelta64[D]")
    y = np.array([40.1, 40.0, 39.9])
    x = np.array([-105.2, -105.1, -105.0])
    rng = np.random.default_rng(22)
    common = rng.normal(size=(18, 3, 3))
    cube = xr.Dataset(
        {
            "tmin": (("time", "y", "x"), common + np.arange(18)[:, None, None] * 0.1),
            "tmax": (("time", "y", "x"), 0.5 * common + rng.normal(size=common.shape)),
        },
        coords={"time": time, "y": y, "x": x},
    )
    cube["y"].attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube["x"].attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    return v.local_synchrony_stack(
        lower_var="tmin", upper_var="tmax", window_days=40, min_t=4
    )(cube)


def _partitioned_stack() -> xr.Dataset:
    center_y, center_x = np.meshgrid(np.arange(4), np.arange(4), indexing="ij")
    center_y = center_y.ravel()
    center_x = center_x.ravel()
    center = np.arange(16)
    y = np.arange(2)
    x = np.arange(2)
    values = np.empty((16, 2, 2), dtype=np.float32)
    for index, (_, xi) in enumerate(zip(center_y, center_x)):
        base = -1.0 if xi < 2 else 1.0
        values[index] = base + 0.02 * index
    distance = np.empty_like(values)
    direction = np.empty(values.shape, dtype=np.int8)
    for index, (cy, cx) in enumerate(zip(center_y, center_x)):
        for yi in range(2):
            for xi in range(2):
                dy, dx = yi - cy, xi - cx
                distance[index, yi, xi] = np.hypot(dx, dy) * 4.0
                direction[index, yi, xi] = -1 if dx == 0 and dy == 0 else int(
                    np.floor((np.degrees(np.arctan2(dx, dy)) % 360 + 22.5) / 45) % 8
                )
    return xr.Dataset(
        {
            "cold_synchrony": (("center", "y", "x"), values + 0.2),
            "warm_synchrony": (("center", "y", "x"), np.full_like(values, 0.2)),
            "delta_s": (("center", "y", "x"), values),
            "distance_km": (("center", "y", "x"), distance),
            "direction_code": (("center", "y", "x"), direction),
        },
        coords={
            "center": center,
            "y": y,
            "x": x,
            "center_y_index": ("center", center_y),
            "center_x_index": ("center", center_x),
        },
        attrs={"analysis": "local_synchrony_stack", "analysis_fingerprint": "sha256:test"},
    )


def test_panel_identity_has_perfect_structure_and_zero_change() -> None:
    panel = np.array([[-1.0, -0.2], [0.4, 1.2]])
    result = compare_panels(panel, panel)
    assert result["spearman"] == 1.0
    assert result["pearson"] == 1.0
    assert result["rmse"] == 0.0
    assert result["mae"] == 0.0
    assert result["wasserstein"] == 0.0
    assert result["sign_disagreement"] == 0.0
    assert result["gradient_vector_rmse"] == 0.0


def test_panel_metrics_are_symmetric_and_constant_offset_is_explicit() -> None:
    left = np.arange(9, dtype=float).reshape(3, 3)
    right = left + 2.0
    forward = compare_panels(left, right, deadband=0)
    reverse = compare_panels(right, left, deadband=0)
    for name in (
        "spearman",
        "pearson",
        "rmse",
        "mae",
        "normalized_rmse",
        "wasserstein",
        "sign_disagreement",
        "gradient_vector_rmse",
    ):
        np.testing.assert_allclose(forward[name], reverse[name], atol=0, rtol=0)
    assert forward["spearman"] == 1.0
    assert forward["pearson"] == 1.0
    assert forward["rmse"] == 2.0
    assert forward["mae"] == 2.0
    assert forward["wasserstein"] == 2.0


def test_monotonic_transform_preserves_ranks_but_not_linear_structure() -> None:
    left = np.linspace(-2, 2, 25).reshape(5, 5)
    right = left**3
    result = compare_panels(left, right)
    assert result["spearman"] == 1.0
    assert result["pearson"] < 0.95
    assert result["rmse"] > 0


def test_sign_disagreement_respects_near_zero_deadband() -> None:
    left = np.full((2, 2), 0.01)
    right = np.full((2, 2), -0.01)
    assert compare_panels(left, right, deadband=0.02)["sign_disagreement"] == 0.0
    assert compare_panels(left, right, deadband=0.0)["sign_disagreement"] == 1.0


def test_panel_table_contains_cold_warm_delta_decomposition() -> None:
    stack = _observed_shape_stack()
    result = (pipe(stack) | v.panel_change_diagnostics()).unwrap()
    assert result.sizes["comparison"] == 12
    for prefix in ("cold", "warm", "delta"):
        for suffix in ("spearman", "rmse", "mae", "normalized_rmse", "wasserstein"):
            assert f"{prefix}_{suffix}" in result
    np.testing.assert_allclose(result.delta_mae, result.delta_mean_absolute_change)


def test_radius_subsets_are_nested_and_statistics_match_manual_values() -> None:
    stack = _observed_shape_stack()
    radii = [0.0, 15.0, 30.0]
    result = v.stack_radius_diagnostics(
        radii_km=radii, stable_min_centers=1
    )(stack)
    counts = result.eligible_center_count.values
    assert np.all(np.diff(counts, axis=0) >= 0)
    yi, xi = 1, 1
    mask = stack.distance_km[:, yi, xi].values <= 15.0
    expected = np.nanmedian(stack.delta_s[:, yi, xi].values[mask])
    np.testing.assert_allclose(result.delta_median.sel(radius_km=15).values[yi, xi], expected)
    assert float(result.delta_median.sel(radius_km=0).values[yi, xi]) == 0.0


def test_radius_diagnostics_match_for_eager_and_chunked_stacks() -> None:
    eager = _observed_shape_stack()
    chunked = eager.chunk({"center": 3})
    expected = v.stack_radius_diagnostics(radii_km=[0, 20, 40], stable_min_centers=1)(eager)
    observed = v.stack_radius_diagnostics(radii_km=[0, 20, 40], stable_min_centers=1)(chunked)
    xr.testing.assert_allclose(expected, observed)


def test_structure_diagnostics_map_candidate_groups_back_to_center_geography() -> None:
    stack = _partitioned_stack()
    result = v.stack_structure_diagnostics(
        metric="delta_s",
        distance_bin_edges_km=[0, 10, 20, 40],
        minimum_group_size=2,
    )(stack)
    assert np.all(result.kde_mode_count.values >= 2)
    assert np.all(result.kde_multimodal_bandwidth_consensus.values == 1)
    assert np.all(result.two_group_separation.values > 5)
    assert np.all(result.two_group_balance.values > 0.8)
    assert np.all(result.two_group_neighbor_agreement_excess.values > 0.5)
    assert np.all(result.two_group_component_coverage.values > 0.9)
    labels = result.two_group_label[:, 0, 0].values.reshape(4, 4)
    assert np.all(labels[:, :2] == labels[0, 0])
    assert np.all(labels[:, 2:] != labels[0, 0])


def test_distance_and_direction_bins_preserve_counts() -> None:
    stack = _partitioned_stack()
    result = v.stack_structure_diagnostics(
        metric="delta_s", distance_bin_edges_km=[0, 10, 20, 40], minimum_group_size=2
    )(stack)
    np.testing.assert_array_equal(
        result.distance_bin_count.sum("distance_bin"),
        stack.delta_s.count("center"),
    )
    # A self-center has undefined bearing, so directional counts need not equal
    # the complete stack count, but can never exceed it.
    assert bool((result.direction_count.sum("direction") <= stack.delta_s.count("center")).all())
