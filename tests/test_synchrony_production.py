"""Production contracts for bounded spatial synchrony signatures."""

from __future__ import annotations

import json

import numpy as np
import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.stats.tails import one_tail_spearman
from cubedynamics.synchrony import (
    angular_profile,
    expand_spatial_domain,
    landscape_change_signature,
    load_signature_checkpoint,
    local_synchrony_pairs,
    local_synchrony_surface,
    low_order_surface_reconstruction,
    radial_profile,
    spatial_output_mask,
    synchrony_signature,
    synchrony_surface_diagnostics,
    tiled_landscape_change_signature,
    tiled_synchrony_signature,
    write_signature_checkpoint,
)


def _cube(*, missing: bool = False) -> xr.Dataset:
    rng = np.random.default_rng(20260922)
    time = np.datetime64("2023-11-01") + np.arange(30).astype("timedelta64[D]")
    y = np.linspace(40.20, 39.80, 6)
    x = np.linspace(-105.20, -104.80, 6)
    common = rng.normal(size=(time.size, 1, 1))
    tmin = common + rng.normal(scale=0.8, size=(time.size, y.size, x.size))
    tmax = -0.25 * common + rng.normal(scale=0.9, size=tmin.shape)
    tmin = np.round(tmin, 1)
    tmax = np.round(tmax, 1)
    if missing:
        tmin[[2, 8], 0, 0] = np.nan
        tmin[[4, 11], 4, 3] = np.nan
        tmax[[1, 7], 0, 0] = np.nan
        tmax[[6, 12], 4, 3] = np.nan
    result = xr.Dataset(
        {
            "tmin": (("time", "y", "x"), tmin),
            "tmax": (("time", "y", "x"), tmax),
        },
        coords={"time": time, "y": y, "x": x},
        attrs={"source": "test", "serving_revision": "fixture-v1"},
    )
    result.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    result.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    return result


def _all_mask(cube: xr.Dataset) -> xr.DataArray:
    return xr.DataArray(
        np.ones((cube.sizes["y"], cube.sizes["x"]), dtype=bool),
        dims=("y", "x"),
        coords={"y": cube.y, "x": cube.x},
    )


def _synthetic_surface(values: np.ndarray, *, radius_km: float = 5.0) -> xr.Dataset:
    size = values.shape[0]
    offsets = np.arange(-(size // 2), size // 2 + 1)
    yy, xx = np.meshgrid(offsets, offsets, indexing="ij")
    distance = np.hypot(xx, yy)
    bearing = np.rad2deg(np.arctan2(xx, yy)) % 360.0
    bearing[distance == 0] = np.nan
    valid = distance <= radius_km
    return xr.Dataset(
        {
            "cold_synchrony": (("offset_y_index", "offset_x_index"), np.where(valid, values + 0.1, np.nan)),
            "warm_synchrony": (("offset_y_index", "offset_x_index"), np.where(valid, values - 0.1, np.nan)),
            "delta_s": (("offset_y_index", "offset_x_index"), np.where(valid, values, np.nan)),
            "distance_km": (("offset_y_index", "offset_x_index"), np.where(valid, distance, np.nan)),
            "bearing_degrees": (("offset_y_index", "offset_x_index"), np.where(valid, bearing, np.nan)),
            "dx_km": (("offset_y_index", "offset_x_index"), np.where(valid, xx, np.nan)),
            "dy_km": (("offset_y_index", "offset_x_index"), np.where(valid, yy, np.nan)),
        },
        coords={"offset_y_index": offsets, "offset_x_index": offsets},
        attrs={
            "analysis": "local_synchrony_surface",
            "observation_radius_km": radius_km,
        },
    )


@pytest.mark.parametrize("missing", [False, True])
def test_pair_kernel_matches_validated_reference_with_ties_and_missing(missing: bool) -> None:
    cube = _cube(missing=missing)
    mask = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    mask[0, 0] = True
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=100,
        window_days=90,
        min_t=5,
        pair_batch_size=7,
    )
    selected = np.flatnonzero(
        (pairs.source_index.values == 0) & (pairs.target_index.values == 35)
    )[0]
    cold, cold_count = one_tail_spearman(
        cube.tmin.values[:, 0, 0], cube.tmin.values[:, 5, 5], tail="lower", min_t=5
    )
    warm, warm_count = one_tail_spearman(
        cube.tmax.values[:, 0, 0], cube.tmax.values[:, 5, 5], tail="upper", min_t=5
    )
    np.testing.assert_allclose(pairs.cold_synchrony.values[selected], cold, atol=0, rtol=0)
    np.testing.assert_allclose(pairs.warm_synchrony.values[selected], warm, atol=0, rtol=0)
    assert int(pairs.cold_joint_count.values[selected]) == cold_count
    assert int(pairs.warm_joint_count.values[selected]) == warm_count


def test_pair_table_is_canonical_and_pipe_friendly() -> None:
    cube = _cube()
    pairs = (
        pipe(cube)
        | v.local_synchrony_pairs(
            lower_var="tmin", upper_var="tmax", max_radius_km=12, min_t=5
        )
    ).unwrap()
    left = pairs.source_index.values
    right = pairs.target_index.values
    assert np.all(left <= right)
    assert len(set(zip(left.tolist(), right.tolist()))) == pairs.sizes["pair"]
    assert pairs.attrs["pair_symmetry"].startswith("canonical undirected")
    np.testing.assert_array_equal(
        pairs.dx_index.values,
        pairs.target_x_index.values - pairs.source_x_index.values,
    )
    np.testing.assert_array_equal(
        pairs.dy_index.values,
        pairs.target_y_index.values - pairs.source_y_index.values,
    )
    assert pairs.attrs["observation_radius_definition"].endswith(
        "not an inferred synchrony scale"
    )


def test_surface_reconstruction_reverses_endpoint_geometry_exactly() -> None:
    cube = _cube()
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=_all_mask(cube),
        max_radius_km=20,
        min_t=5,
    )
    source_surface = local_synchrony_surface(pairs, focal_index=14)
    target_surface = local_synchrony_surface(pairs, focal_index=15)
    pair_index = np.flatnonzero(
        (pairs.source_index.values == 14) & (pairs.target_index.values == 15)
    )[0]
    source_value = source_surface.delta_s.sel(offset_y_index=0, offset_x_index=1).item()
    target_value = target_surface.delta_s.sel(offset_y_index=0, offset_x_index=-1).item()
    np.testing.assert_allclose(source_value, pairs.delta_s.values[pair_index], atol=0, rtol=0)
    np.testing.assert_allclose(target_value, source_value, atol=0, rtol=0)
    np.testing.assert_allclose(
        source_surface.dx_km.sel(offset_y_index=0, offset_x_index=1),
        -target_surface.dx_km.sel(offset_y_index=0, offset_x_index=-1),
    )
    source_bearing = source_surface.bearing_degrees.sel(
        offset_y_index=0, offset_x_index=1
    ).item()
    target_bearing = target_surface.bearing_degrees.sel(
        offset_y_index=0, offset_x_index=-1
    ).item()
    np.testing.assert_allclose((source_bearing + 180.0) % 360.0, target_bearing)
    piped = (
        pipe(pairs) | v.local_synchrony_surface(focal_y_index=2, focal_x_index=2)
    ).unwrap()
    xr.testing.assert_allclose(piped.delta_s, source_surface.delta_s)


def test_profiles_preserve_nonmonotonic_radial_and_directional_structure() -> None:
    offsets = np.arange(-5, 6)
    yy, xx = np.meshgrid(offsets, offsets, indexing="ij")
    distance = np.hypot(xx, yy)
    bearing = np.arctan2(xx, yy)
    nonmonotonic = np.cos(distance * 1.7)
    radial_surface = _synthetic_surface(nonmonotonic)
    radial = radial_profile(radial_surface, bin_width_km=1.0, min_count=1)
    finite = radial.profile.values[np.isfinite(radial.profile.values)]
    assert np.any(np.diff(finite) > 0) and np.any(np.diff(finite) < 0)

    directional_surface = _synthetic_surface(np.cos(2.0 * (bearing - np.deg2rad(30.0))))
    angular = angular_profile(
        directional_surface,
        bin_width_degrees=30,
        min_count=1,
        radial_detrend_bin_width_km=None,
    )
    assert float(np.nanmax(angular.profile) - np.nanmin(angular.profile)) > 1.5
    diagnostics = synchrony_surface_diagnostics(
        directional_surface,
        radial_bin_width_km=1.0,
        angular_bin_width_degrees=30,
        min_count=1,
    )
    orientation = diagnostics.anisotropy_axis_degrees.item()
    assert min(abs(orientation - 30.0), abs(orientation - 120.0)) < 2.0
    assert diagnostics.directional_harmonic_r_squared.item() > 0.95


def test_boundary_contrast_and_characteristic_scale_censoring() -> None:
    offsets = np.arange(-5, 6)
    yy, xx = np.meshgrid(offsets, offsets, indexing="ij")
    boundary_surface = _synthetic_surface(np.where(xx >= 0, 0.6, -0.6))
    boundary = synchrony_surface_diagnostics(
        boundary_surface,
        radial_bin_width_km=1,
        angular_bin_width_degrees=30,
        min_count=1,
    )
    assert boundary.maximum_half_plane_contrast.item() > 1.0
    assert min(
        abs(boundary.high_side_bearing_degrees.item() - 90.0),
        abs(boundary.high_side_bearing_degrees.item() - 270.0),
    ) < 6.0

    increasing_surface = _synthetic_surface(np.hypot(xx, yy) / 5.0)
    censored = synchrony_surface_diagnostics(
        increasing_surface,
        radial_bin_width_km=1,
        angular_bin_width_degrees=30,
        min_count=1,
    )
    assert censored.attrs["characteristic_scale_status"] == "right_censored_or_unresolved"


def test_low_order_basis_reconstructs_known_surface_better_than_median() -> None:
    offsets = np.arange(-5, 6)
    yy, xx = np.meshgrid(offsets, offsets, indexing="ij")
    distance = np.hypot(xx, yy)
    values = 0.2 + 0.04 * distance + 0.08 * xx - 0.05 * yy + 0.02 * (xx**2 - yy**2)
    surface = _synthetic_surface(values)
    reconstruction = low_order_surface_reconstruction(surface)
    valid = np.isfinite(surface.delta_s.values)
    median_rmse = np.sqrt(
        np.mean((surface.delta_s.values[valid] - np.median(surface.delta_s.values[valid])) ** 2)
    )
    assert reconstruction.attrs["r_squared"] > 0.999999
    assert reconstruction.attrs["rmse"] < median_rmse * 0.01


def test_signature_uses_pairwise_delta_and_nested_exact_support() -> None:
    cube = _cube()
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=_all_mask(cube),
        max_radius_km=20,
        min_t=5,
    )
    signature = (pipe(pairs) | v.synchrony_signature(radii_km=(5, 12, 20))).unwrap()
    node = 14
    incident = (pairs.source_index.values == node) | (pairs.target_index.values == node)
    within = incident & (pairs.distance_km.values <= 12 + 1e-7)
    observed = pairs.delta_s.values[within]
    observed = observed[np.isfinite(observed)]
    yi, xi = divmod(node, cube.sizes["x"])
    actual = signature.delta_median.sel(radius_km=12).values[0, yi, xi]
    np.testing.assert_allclose(actual, np.median(observed), atol=0, rtol=0)
    expected = signature.expected_pair_count.values[0, :, yi, xi]
    assert np.all(np.diff(expected) >= 0)
    assert signature.attrs["delta_reduction"].startswith("median/IQR/MAD of pairwise")
    np.testing.assert_allclose(
        signature.delta_mad.sel(radius_km=12).values[0, yi, xi],
        np.median(np.abs(observed - np.median(observed))),
        atol=0,
        rtol=0,
    )
    assert signature.attrs["multimodality_status"] == "not computed in production signature"


def test_output_geometry_mask_and_halo_are_separate() -> None:
    cube = _cube()
    geometry = (-105.12, 39.88, -104.88, 40.12)
    mask = spatial_output_mask(cube, geometry)
    halo = expand_spatial_domain(geometry, 100)
    assert 0 < int(mask.sum()) < mask.size
    assert halo.area > (geometry[2] - geometry[0]) * (geometry[3] - geometry[1])
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=12,
        min_t=5,
    )
    assert pairs.attrs["output_pixel_count"] == int(mask.sum())
    assert pairs.attrs["computation_pixel_count"] == mask.size
    assert json.loads(pairs.attrs["output_domain_bounds"]) != json.loads(
        pairs.attrs["computation_domain_bounds"]
    )


def test_tiled_halo_matches_untiled_and_resumes(tmp_path) -> None:
    cube = _cube(missing=True)
    mask = _all_mask(cube)
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=20,
        min_t=5,
    )
    untiled = synchrony_signature(pairs, radii_km=(5, 12, 20))
    tiled = tiled_synchrony_signature(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        radii_km=(5, 12, 20),
        tile_shape=(3, 2),
        min_t=5,
        checkpoint_dir=tmp_path,
    )
    for name in (
        "cold_median",
        "warm_median",
        "delta_median",
        "delta_iqr",
        "valid_pair_count",
        "expected_pair_count",
        "neighborhood_coverage",
    ):
        xr.testing.assert_allclose(tiled[name], untiled[name])
    resumed = tiled_synchrony_signature(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        radii_km=(5, 12, 20),
        tile_shape=(3, 2),
        min_t=5,
        checkpoint_dir=tmp_path,
    )
    assert resumed.attrs["computed_tile_count"] == 0
    assert resumed.attrs["resumed_tile_count"] == resumed.attrs["tile_count"]


def test_checkpoint_rejects_incompatible_resume(tmp_path) -> None:
    cube = _cube()
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=_all_mask(cube),
        max_radius_km=12,
        min_t=5,
    )
    signature = synchrony_signature(pairs, radii_km=(5, 12))
    signature.attrs["checkpoint_compatibility_fingerprint"] = "sha256:compatible"
    target = write_signature_checkpoint(signature, tmp_path / "signature.nc")
    restored = load_signature_checkpoint(
        target, expected_compatibility_fingerprint="sha256:compatible"
    )
    xr.testing.assert_allclose(restored.delta_median, signature.delta_median)
    with pytest.raises(ValueError, match="compatibility fingerprint mismatch"):
        load_signature_checkpoint(
            target, expected_compatibility_fingerprint="sha256:not-compatible"
        )


def test_chunking_does_not_change_pair_or_signature_values() -> None:
    cube = _cube(missing=True)
    chunked = cube.chunk({"time": 7, "y": 2, "x": 3})
    kwargs = dict(
        lower_var="tmin",
        upper_var="tmax",
        output_mask=_all_mask(cube),
        max_radius_km=12,
        min_t=5,
    )
    eager = local_synchrony_pairs(cube, **kwargs)
    lazy = local_synchrony_pairs(chunked, **kwargs)
    for name in ("cold_synchrony", "warm_synchrony", "delta_s"):
        xr.testing.assert_allclose(eager[name], lazy[name])
    xr.testing.assert_allclose(
        synchrony_signature(eager, radii_km=(5, 12)).delta_iqr,
        synchrony_signature(lazy, radii_km=(5, 12)).delta_iqr,
    )


def test_landscape_change_is_a_separate_multi_axis_product() -> None:
    cube = _cube()
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=_all_mask(cube),
        max_radius_km=20,
        min_t=5,
    )
    result = landscape_change_signature(pairs, min_overlap=3)
    assert result.orientation.values.tolist() == ["east_west", "north_south"]
    assert {"normalized_rmse", "spearman", "sign_disagreement", "gradient_vector_rmse"} <= set(
        result.data_vars
    )
    assert result.attrs["pair_synchrony_distinction"].startswith("compares center landscapes")


def test_tiled_landscape_change_matches_untiled_at_seams(tmp_path) -> None:
    cube = _cube()
    mask = _all_mask(cube)
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=20,
        min_t=5,
    )
    untiled = landscape_change_signature(pairs, min_overlap=3)
    tiled = tiled_landscape_change_signature(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=20,
        tile_shape=(3, 2),
        min_t=5,
        min_overlap=3,
        checkpoint_dir=tmp_path,
    )
    for name in (
        "normalized_rmse",
        "spearman",
        "sign_disagreement",
        "gradient_vector_rmse",
        "pooled_robust_range",
        "shared_valid_count",
    ):
        xr.testing.assert_allclose(tiled[name], untiled[name])
