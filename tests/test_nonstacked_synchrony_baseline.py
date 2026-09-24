"""Contracts for the deliberately non-stacked synchrony baseline."""

from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics.synchrony.baseline import (
    nonstacked_synchrony_summary,
    tiled_nonstacked_synchrony_summary,
)
from cubedynamics.synchrony.production import local_synchrony_pairs
from cubedynamics.synchrony.surfaces import local_synchrony_surface


def _cube() -> xr.Dataset:
    rng = np.random.default_rng(20260923)
    time = np.datetime64("2023-11-01") + np.arange(30).astype("timedelta64[D]")
    y = np.linspace(40.25, 39.75, 8)
    x = np.linspace(-105.25, -104.75, 8)
    shared = rng.normal(size=(time.size, 1, 1))
    tmin = np.round(shared + rng.normal(scale=0.7, size=(30, 8, 8)), 1)
    tmax = np.round(-0.2 * shared + rng.normal(scale=0.8, size=(30, 8, 8)), 1)
    result = xr.Dataset(
        {"tmin": (("time", "y", "x"), tmin), "tmax": (("time", "y", "x"), tmax)},
        coords={"time": time, "y": y, "x": x},
        attrs={"source": "deterministic test cube", "serving_revision": "test-v1"},
    )
    result.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    result.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    return result


def _mask(cube: xr.Dataset) -> xr.DataArray:
    values = np.zeros((8, 8), dtype=bool)
    values[2:6, 2:6] = True
    return xr.DataArray(values, dims=("y", "x"), coords={"y": cube.y, "x": cube.x})


def test_reduction_matches_direct_surface_and_excludes_self() -> None:
    cube = _cube()
    mask = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    mask.values[3, 4] = True
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=50,
        min_t=5,
    )
    summary = nonstacked_synchrony_summary(pairs, radii_km=(25, 50))
    surface = local_synchrony_surface(pairs, focal_y_index=3, focal_x_index=4)
    within = (surface.distance_km.values > 0) & (surface.distance_km.values <= 50 + 1e-7)

    for surface_name, summary_name in (
        ("cold_synchrony", "cold_median"),
        ("warm_synchrony", "warm_median"),
        ("delta_s", "delta_pair_median"),
    ):
        observed = surface[surface_name].values[within]
        observed = observed[np.isfinite(observed)]
        actual = summary[summary_name].sel(radius_km=50).values[0, 3, 4]
        np.testing.assert_allclose(actual, np.median(observed), atol=0, rtol=0)

    expected_nonself = int(np.count_nonzero(within))
    assert int(summary.expected_pair_count.sel(radius_km=50).values[0, 3, 4]) == expected_nonself
    self_pair = (pairs.source_index.values == 28) & (pairs.target_index.values == 28)
    assert np.count_nonzero(self_pair) == 1
    assert summary.attrs["self_pair_policy"] == "excluded before every reduction"


def test_pairwise_delta_is_kept_separate_from_difference_of_medians() -> None:
    cube = _cube()
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=_mask(cube),
        max_radius_km=50,
        min_t=5,
    )
    summary = nonstacked_synchrony_summary(pairs, radii_km=(50,))
    xr.testing.assert_allclose(
        summary.delta_median_difference,
        summary.cold_median - summary.warm_median,
    )
    xr.testing.assert_allclose(
        summary.delta_reduction_gap,
        summary.delta_pair_median - summary.delta_median_difference,
    )
    assert summary.delta_pair_median.attrs["definition"].startswith("median of nonself pairwise")


def test_tiled_matches_untiled_and_restarts(tmp_path) -> None:
    cube = _cube()
    mask = _mask(cube)
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=50,
        min_t=5,
    )
    expected = nonstacked_synchrony_summary(pairs, radii_km=(25, 50))
    actual = tiled_nonstacked_synchrony_summary(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        radii_km=(25, 50),
        tile_shape=(3, 3),
        min_t=5,
        checkpoint_dir=tmp_path,
    )
    for name in expected.data_vars:
        xr.testing.assert_allclose(actual[name].where(mask), expected[name].where(mask))
    resumed = tiled_nonstacked_synchrony_summary(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        radii_km=(25, 50),
        tile_shape=(3, 3),
        min_t=5,
        checkpoint_dir=tmp_path,
    )
    assert resumed.attrs["computed_tile_count"] == 0
    assert resumed.attrs["resumed_tile_count"] == resumed.attrs["tile_count"]


def test_computation_mask_excludes_nodata_nodes_without_changing_valid_pairs(tmp_path) -> None:
    cube = _cube()
    cube["tmin"].values[:, 1, 1] = np.nan
    cube["tmax"].values[:, 1, 1] = np.nan
    output = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    output.values[2, 2] = True
    eligible = np.isfinite(cube.tmin).all("time") & np.isfinite(cube.tmax).all("time")

    unmasked_pairs = local_synchrony_pairs(
        cube, lower_var="tmin", upper_var="tmax", output_mask=output,
        max_radius_km=50, min_t=5,
    )
    masked_pairs = local_synchrony_pairs(
        cube, lower_var="tmin", upper_var="tmax", output_mask=output,
        computation_mask=eligible, max_radius_km=50, min_t=5,
    )
    assert masked_pairs.attrs["computation_pixel_count"] == 63
    assert masked_pairs.attrs["cold_threshold_strategy"].startswith("precomputed")
    assert int(masked_pairs.sizes["pair"]) == int(unmasked_pairs.sizes["pair"]) - 1

    summary = tiled_nonstacked_synchrony_summary(
        cube, lower_var="tmin", upper_var="tmax", output_mask=output,
        computation_mask=eligible, radii_km=(50,), tile_shape=(4, 4),
        min_t=5, checkpoint_dir=tmp_path,
    )
    expected = int(summary.expected_pair_count.sel(radius_km=50).values[0, 2, 2])
    valid = int(summary.valid_pair_count.sel(radius_km=50).values[0, 2, 2])
    unmasked_summary = nonstacked_synchrony_summary(unmasked_pairs, radii_km=(50,))
    unmasked_expected = int(unmasked_summary.expected_pair_count.sel(radius_km=50).values[0, 2, 2])
    assert expected == unmasked_expected - 1
    np.testing.assert_allclose(
        float(summary.valid_pair_fraction.sel(radius_km=50).values[0, 2, 2]),
        valid / expected,
    )
    np.testing.assert_allclose(
        float(summary.delta_pair_median.sel(radius_km=50).values[0, 2, 2]),
        float(unmasked_summary.delta_pair_median.sel(radius_km=50).values[0, 2, 2]),
    )
    assert summary.attrs["computation_mask_policy"] == "explicit eligible spatial nodes"


def test_output_mask_must_be_inside_computation_mask() -> None:
    cube = _cube()
    output = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
    output.values[2, 2] = True
    eligible = xr.zeros_like(output, dtype=bool)
    with np.testing.assert_raises_regex(ValueError, "subset of computation_mask"):
        local_synchrony_pairs(
            cube, lower_var="tmin", upper_var="tmax", output_mask=output,
            computation_mask=eligible, max_radius_km=50, min_t=5,
        )
