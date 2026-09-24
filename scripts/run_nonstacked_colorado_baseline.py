#!/usr/bin/env python3
"""Run the exact, immediately reduced, non-stacked Colorado baseline.

Reproduction:

    .venv/bin/python scripts/run_nonstacked_colorado_baseline.py

The script requires the real observed-PRISM snapshot produced by the existing
Phase 2 workflow. It performs no network access and refuses synthetic input.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import resource
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, TwoSlopeNorm
import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy import ndimage
from scipy.stats import spearmanr
from shapely.geometry import shape
import xarray as xr

from cubedynamics.serialization import sanitize_netcdf_attrs
from cubedynamics.synchrony.baseline import (
    nonstacked_synchrony_summary,
    tiled_nonstacked_synchrony_summary,
)
from cubedynamics.synchrony.production import local_synchrony_pairs
from cubedynamics.synchrony.surfaces import local_synchrony_surface


ROOT = Path(__file__).resolve().parents[1]
PHASE2 = ROOT / "artifacts" / "synchrony-stack-phase2"
OUTPUT = ROOT / "artifacts" / "nonstacked-colorado-baseline"
CUBE_PATH = PHASE2 / "prism_colorado_plus_100km_20231101_20240130.nc"
MASK_PATH = PHASE2 / "colorado_synchrony_signature.nc"
BOUNDARY_PATH = PHASE2 / "colorado_boundary.geojson"
RADII_KM = (25.0, 50.0, 75.0, 100.0)
WINDOW_DAYS = 90
WINDOW_END = "2024-01-30"
MIN_T = 10
TILE_SHAPE = (32, 32)
PRIMARY = ("cold_median", "warm_median", "delta_pair_median")


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.json")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _netcdf(path: Path, dataset: xr.Dataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.nc")
    clean = sanitize_netcdf_attrs(dataset, copy=True)
    for name in clean.variables:
        clean[name].encoding = {}
    clean.to_netcdf(temporary, engine="scipy")
    temporary.replace(path)


@contextmanager
def _performance():
    started_at = datetime.now(timezone.utc)
    wall = time.perf_counter()
    cpu = time.process_time()
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record: dict[str, object] = {"started_at_utc": started_at.isoformat()}
    yield record
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = int(after if after > 10_000_000 else after * 1024)
    baseline = int(before if before > 10_000_000 else before * 1024)
    record.update(
        {
            "ended_at_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": time.perf_counter() - wall,
            "cpu_seconds": time.process_time() - cpu,
            "process_peak_rss_bytes": peak,
            "process_peak_rss_increase_bytes": max(0, peak - baseline),
        }
    )


def _load_inputs() -> tuple[xr.Dataset, xr.DataArray, object]:
    if not CUBE_PATH.exists() or not MASK_PATH.exists() or not BOUNDARY_PATH.exists():
        raise FileNotFoundError("Run the existing Phase 2 workflow first; required snapshots are missing")
    with xr.open_dataset(CUBE_PATH, engine="scipy") as opened:
        cube = opened.load()
    if bool(cube.attrs.get("is_synthetic", 1)):
        raise RuntimeError("Refusing synthetic PRISM input")
    cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    with xr.open_dataset(MASK_PATH, engine="scipy") as opened:
        mask = opened.output_mask.load().astype(bool)
    boundary_document = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    boundary = shape(boundary_document["features"][0]["geometry"])
    return cube, mask, boundary


def _center_mask(cube: xr.Dataset, height: int, width: int) -> xr.DataArray:
    values = np.zeros((cube.sizes["y"], cube.sizes["x"]), dtype=bool)
    y0 = (cube.sizes["y"] - height) // 2
    x0 = (cube.sizes["x"] - width) // 2
    values[y0 : y0 + height, x0 : x0 + width] = True
    return xr.DataArray(values, dims=("y", "x"), coords={"y": cube.y, "x": cube.x})


def _gate(
    cube: xr.Dataset,
    *,
    name: str,
    mask: xr.DataArray,
    tile_shape: tuple[int, int],
    checkpoint_dir: Path,
) -> dict[str, object]:
    with _performance() as timing:
        pairs = local_synchrony_pairs(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=mask,
            max_radius_km=100,
            window_days=WINDOW_DAYS,
            window_end=WINDOW_END,
            min_t=MIN_T,
            pair_batch_size=8192,
        )
        direct = nonstacked_synchrony_summary(pairs, radii_km=RADII_KM)
        tiled = tiled_nonstacked_synchrony_summary(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=mask,
            radii_km=RADII_KM,
            tile_shape=tile_shape,
            window_days=WINDOW_DAYS,
            window_end=WINDOW_END,
            min_t=MIN_T,
            pair_batch_size=8192,
            checkpoint_dir=checkpoint_dir,
        )
    errors = {}
    for variable in direct.data_vars:
        left = np.asarray(direct[variable].where(mask).values, dtype=float)
        right = np.asarray(tiled[variable].where(mask).values, dtype=float)
        difference = np.abs(left - right)
        errors[variable] = float(np.nanmax(difference)) if np.isfinite(difference).any() else 0.0
    if max(errors.values(), default=0.0) > 1e-12:
        raise RuntimeError(f"{name} failed tiled equivalence: {errors}")

    yi, xi = np.argwhere(mask.values)[len(np.argwhere(mask.values)) // 2]
    surface = local_synchrony_surface(pairs, focal_y_index=int(yi), focal_x_index=int(xi))
    manual = {}
    for radius in RADII_KM:
        within = (surface.distance_km.values > 0) & (surface.distance_km.values <= radius + 1e-7)
        for metric, output_name in (
            ("cold_synchrony", "cold_median"),
            ("warm_synchrony", "warm_median"),
            ("delta_s", "delta_pair_median"),
        ):
            values = surface[metric].values[within]
            values = values[np.isfinite(values)]
            expected = float(np.median(values))
            actual = float(direct[output_name].sel(radius_km=radius).values[0, yi, xi])
            manual[f"{radius:g}km_{output_name}"] = abs(expected - actual)
    if max(manual.values(), default=0.0) > 1e-12:
        raise RuntimeError(f"{name} failed manual surface reduction: {manual}")
    _netcdf(OUTPUT / "gates" / f"{name}.nc", tiled)
    return {
        "status": "PASS",
        "name": name,
        "computation_shape": [cube.sizes["y"], cube.sizes["x"]],
        "focal_pixel_count": int(mask.sum()),
        "focal_mask_bounds": [
            float(cube.x.values[np.nonzero(mask.values)[1]].min()),
            float(cube.y.values[np.nonzero(mask.values)[0]].min()),
            float(cube.x.values[np.nonzero(mask.values)[1]].max()),
            float(cube.y.values[np.nonzero(mask.values)[0]].max()),
        ],
        "unique_pairs_untiled_including_self": int(pairs.attrs["unique_pair_count"]),
        "nonself_pairs_untiled": int(pairs.attrs["nonself_pair_count"]),
        "self_pairs_excluded_from_reduction": int(pairs.attrs["unique_pair_count"] - pairs.attrs["nonself_pair_count"]),
        "pair_calculations_tiled": int(tiled.attrs["pair_calculation_count_with_tile_recompute"]),
        "tile_count": int(tiled.attrs["tile_count"]),
        "max_tiled_absolute_error": max(errors.values(), default=0.0),
        "max_manual_surface_absolute_error": max(manual.values(), default=0.0),
        "manual_focal_index": [int(yi), int(xi)],
        **timing,
    }


def _geometry_record(cube: xr.Dataset, mask: xr.DataArray) -> dict[str, object]:
    dy = abs(float(np.median(np.diff(cube.y.values))))
    dx = abs(float(np.median(np.diff(cube.x.values))))
    latitude = float(np.mean(cube.y.values[np.nonzero(mask.values)[0]]))
    ns_km = dy * 111.195
    ew_km = dx * 111.195 * np.cos(np.deg2rad(latitude))
    return {
        "interpretation": "100 km great-circle radius, not a literal 100 by 100 pixel footprint",
        "raster_resolution_degrees": {"longitude": dx, "latitude": dy},
        "approximate_pixel_resolution_km_at_colorado_mean_latitude": {"east_west": ew_km, "north_south": ns_km},
        "maximum_center_to_neighbor_distance_km": 100.0,
        "approximate_diameter_km": 200.0,
        "approximate_diameter_pixels": {"east_west": 200.0 / ew_km, "north_south": 200.0 / ns_km},
        "footprint_exactly_100_by_100": False,
        "footprint": "irregular circular great-circle neighborhood clipped only by the acquired input domain",
        "focal_centering": "exact PRISM grid-cell center; no half-pixel shift and no even-window convention",
        "phase2_100_by_100_meaning": "engineering-gate computation grid; its established output mask is the central 50 by 50 cells",
        "statewide_input_shape": [cube.sizes["y"], cube.sizes["x"]],
        "statewide_output_pixels": int(mask.sum()),
        "input_bounds": [float(cube.x.min()), float(cube.y.min()), float(cube.x.max()), float(cube.y.max())],
    }


def _write_geotiffs(result: xr.Dataset) -> list[str]:
    raster_dir = OUTPUT / "rasters"
    raster_dir.mkdir(parents=True, exist_ok=True)
    x = result.x.values.astype(float)
    y = result.y.values.astype(float)
    dx = abs(float(np.median(np.diff(x))))
    dy = abs(float(np.median(np.diff(y))))
    transform = from_origin(float(x.min() - dx / 2), float(y.max() + dy / 2), dx, dy)
    variables = (
        "cold_median", "warm_median", "delta_pair_median", "delta_median_difference",
        "valid_pair_count", "valid_pair_fraction",
        "cold_iqr", "warm_iqr", "delta_iqr",
        "cold_mad", "warm_mad", "delta_mad",
        "cold_mean", "warm_mean", "delta_mean",
    )
    paths = []
    for variable in variables:
        array = result[variable].sel(radius_km=100).isel(time_window_end=0).where(result.output_mask)
        values = np.asarray(array.values, dtype=np.float32)
        path = raster_dir / f"{variable}_100km.tif"
        with rasterio.open(
            path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1],
            count=1, dtype="float32", crs="EPSG:4326", transform=transform,
            nodata=np.float32(-9999.0), compress="deflate",
        ) as destination:
            destination.write(np.where(np.isfinite(values), values, -9999.0).astype(np.float32), 1)
            destination.set_band_description(1, variable)
            destination.update_tags(
                observation_radius_km="100", self_pair_policy="excluded",
                sign_convention="Delta = cold synchrony - warm synchrony",
                stacking="none",
            )
        paths.append(str(path.relative_to(ROOT)))
    return paths


def _boundary_xy(boundary) -> list[tuple[np.ndarray, np.ndarray]]:
    geometries = [boundary] if boundary.geom_type == "Polygon" else list(boundary.geoms)
    return [(np.asarray(poly.exterior.xy[0]), np.asarray(poly.exterior.xy[1])) for poly in geometries]


def _map(ax, result, variable: str, boundary, *, title: str, cmap, norm) -> object:
    values = result[variable].sel(radius_km=100).isel(time_window_end=0).where(result.output_mask)
    mesh = ax.pcolormesh(result.x, result.y, values, shading="nearest", cmap=cmap, norm=norm, rasterized=True)
    for bx, by in _boundary_xy(boundary):
        ax.plot(bx, by, color="#17202a", lw=0.7)
    ax.set_title(title, loc="left", weight="bold", fontsize=11)
    ax.set_aspect(1 / np.cos(np.deg2rad(39)))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    return mesh


def _figures(result: xr.Dataset, boundary, example_surface: xr.Dataset) -> dict[str, object]:
    figure_dir = OUTPUT / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    mask = result.output_mask.values.astype(bool)
    cold = result.cold_median.sel(radius_km=100).values[0][mask]
    warm = result.warm_median.sel(radius_km=100).values[0][mask]
    common = float(np.nanpercentile(np.abs(np.concatenate((cold, warm))), 99))
    delta = result.delta_pair_median.sel(radius_km=100).values[0][mask]
    delta_limit = float(np.nanpercentile(np.abs(delta), 99))
    common = max(common, 0.01)
    delta_limit = max(delta_limit, 0.01)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)
    for ax, variable, title, limit in zip(
        axes, PRIMARY, ("A  COLD SYNCHRONY", "B  WARM SYNCHRONY", "C  DELTA = COLD - WARM"),
        (common, common, delta_limit),
    ):
        mesh = _map(ax, result, variable, boundary, title=title, cmap="RdBu", norm=TwoSlopeNorm(0, -limit, limit))
        fig.colorbar(mesh, ax=ax, shrink=0.78, label="Median Spearman synchrony")
    fig.suptitle("Immediate 100 km local-surface reduction — no stacking", fontsize=15, weight="bold")
    fig.text(
        0.5, -0.01,
        "Each Colorado focal pixel is reduced independently to its median. "
        "No information from overlapping focal neighborhoods was combined.",
        ha="center", fontsize=10,
    )
    primary_path = figure_dir / "primary_three_panel.png"
    fig.savefig(primary_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    specs = (
        ("valid_pair_count", "A  VALID DELTA PAIRS", "viridis", None),
        ("valid_pair_fraction", "B  VALID DELTA FRACTION", "viridis", Normalize(0, 1)),
        ("delta_iqr", "C  DELTA IQR", "magma", None),
        ("delta_reduction_gap", "D  MEDIAN DIFFERENCE GAP", "RdBu", None),
    )
    for ax, (variable, title, cmap, norm) in zip(axes.ravel(), specs):
        if norm is None:
            values = result[variable].sel(radius_km=100).values[0][mask]
            if variable == "delta_reduction_gap":
                limit = max(float(np.nanpercentile(np.abs(values), 99)), 0.01)
                norm = TwoSlopeNorm(0, -limit, limit)
            else:
                norm = Normalize(float(np.nanpercentile(values, 1)), float(np.nanpercentile(values, 99)))
        mesh = _map(ax, result, variable, boundary, title=title, cmap=cmap, norm=norm)
        fig.colorbar(mesh, ax=ax, shrink=0.75)
    qc_path = figure_dir / "qc_maps.png"
    fig.savefig(qc_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4), constrained_layout=True)
    count = result.valid_pair_count.sel(radius_km=100).values[0][mask]
    support_correlations = {}
    for ax, variable, title in zip(axes, PRIMARY, ("Cold", "Warm", "Pairwise Delta")):
        values = result[variable].sel(radius_km=100).values[0][mask]
        finite = np.isfinite(count) & np.isfinite(values)
        rho = float(spearmanr(count[finite], values[finite]).statistic)
        support_correlations[variable] = rho
        hb = ax.hexbin(count[finite], values[finite], gridsize=45, mincnt=1, cmap="viridis")
        ax.set_title(f"{title}\nSpearman ρ = {rho:.3f}")
        ax.set_xlabel("Valid pair count")
        ax.set_ylabel("Median synchrony")
        fig.colorbar(hb, ax=ax, label="Focal pixels")
    support_path = figure_dir / "support_sensitivity.png"
    fig.savefig(support_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(1, 4, figsize=(15, 4), constrained_layout=True)
    all_delta = result.delta_pair_median.values[0, :, mask]
    window_limit = max(float(np.nanpercentile(np.abs(all_delta), 99)), 0.01)
    window_correlations = {}
    reference = result.delta_pair_median.sel(radius_km=100).values[0][mask]
    for ax, radius in zip(axes, RADII_KM):
        variable = result.delta_pair_median.sel(radius_km=radius).values[0][mask]
        finite = np.isfinite(reference) & np.isfinite(variable)
        rho = float(spearmanr(reference[finite], variable[finite]).statistic)
        window_correlations[f"{radius:g}_vs_100km"] = rho
        mesh = _map(
            ax, result.sel(radius_km=[radius]).assign_coords(radius_km=[100.0]),
            "delta_pair_median", boundary, title=f"{radius:g} km  (ρ={rho:.2f})",
            cmap="RdBu", norm=TwoSlopeNorm(0, -window_limit, window_limit),
        )
        fig.colorbar(mesh, ax=ax, shrink=0.68)
    fig.suptitle("Nested-window sensitivity of the simple Delta median", weight="bold")
    window_path = figure_dir / "window_sensitivity.png"
    fig.savefig(window_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    surface = example_surface.delta_s.where(example_surface.distance_km > 0)
    fig = plt.figure(figsize=(15, 7.5), constrained_layout=True)
    grid = fig.add_gridspec(2, 5, width_ratios=(1.1, 1.3, 1.3, 0.55, 1.1))
    ax0 = fig.add_subplot(grid[0, 0])
    ax0.scatter([0], [0], s=250, marker="*", color="#f4b942", edgecolor="black")
    ax0.set(xlim=(-1, 1), ylim=(-1, 1), xticks=[], yticks=[], title="1  One focal pixel")
    ax1 = fig.add_subplot(grid[0, 1])
    circle = plt.Circle((0, 0), 1, facecolor="#d9eef8", edgecolor="#174a7e")
    ax1.add_patch(circle); ax1.scatter([0], [0], marker="*", s=140, color="#f4b942", edgecolor="black")
    ax1.set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1), aspect="equal", xticks=[], yticks=[], title="2  100 km neighborhood")
    ax2 = fig.add_subplot(grid[0, 2])
    limit = max(float(np.nanpercentile(np.abs(surface.values), 99)), 0.01)
    im = ax2.imshow(surface.values, origin="upper", cmap="RdBu", norm=TwoSlopeNorm(0, -limit, limit))
    ax2.set(title="3  Full local Delta surface", xticks=[], yticks=[])
    fig.colorbar(im, ax=ax2, shrink=0.7)
    ax3 = fig.add_subplot(grid[0, 3]); ax3.axis("off")
    ax3.text(0.5, 0.55, "→", ha="center", va="center", fontsize=38)
    ax3.text(0.5, 0.35, "MEDIAN", ha="center", va="center", weight="bold", rotation=90)
    ax4 = fig.add_subplot(grid[0, 4])
    cell = float(np.nanmedian(surface.values))
    ax4.imshow([[cell]], cmap="RdBu", norm=TwoSlopeNorm(0, -limit, limit))
    ax4.set(title=f"4  One output cell\n{cell:+.3f}", xticks=[], yticks=[])
    ax5 = fig.add_subplot(grid[1, 0:2]); ax5.axis("off")
    ax5.text(0.5, 0.65, "5  MOVE TO NEXT FOCAL PIXEL  →", ha="center", fontsize=16, weight="bold")
    ax5.text(0.5, 0.35, "EACH LOCAL SURFACE IS REDUCED\nBEFORE MOVING ON.", ha="center", fontsize=14)
    ax6 = fig.add_subplot(grid[1, 2]); ax6.axis("off")
    ax6.text(0.5, 0.55, "6  REPEAT\nACROSS\nCOLORADO", ha="center", va="center", fontsize=17, weight="bold")
    ax7 = fig.add_subplot(grid[1, 3:5])
    _map(ax7, result, "delta_pair_median", boundary, title="7  Completed one-value-per-pixel map", cmap="RdBu", norm=TwoSlopeNorm(0, -delta_limit, delta_limit))
    fig.suptitle("NO STACKING", fontsize=24, weight="bold", color="#9b2226")
    pedagogy_path = figure_dir / "pedagogical_reduction.png"
    fig.savefig(pedagogy_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return {
        "paths": [str(path.relative_to(ROOT)) for path in (primary_path, qc_path, support_path, window_path, pedagogy_path)],
        "color_limits": {"cold_warm_common_symmetric": [-common, common], "delta_symmetric": [-delta_limit, delta_limit]},
        "support_spearman_correlations": support_correlations,
        "window_spearman_correlations_against_100km": window_correlations,
    }


def _qc(result: xr.Dataset) -> dict[str, object]:
    mask = result.output_mask.values.astype(bool)
    interior = ndimage.binary_erosion(mask)
    border = mask & ~interior
    record: dict[str, object] = {
        "output_pixels": int(mask.sum()),
        "border_pixels": int(border.sum()),
        "interior_pixels": int(interior.sum()),
        "variables": {},
    }
    for variable in PRIMARY:
        array = result[variable].sel(radius_km=100).values[0]
        missing = mask & ~np.isfinite(array)
        values = array[mask & np.isfinite(array)]
        horizontal = np.abs(np.diff(array, axis=1))
        horizontal_valid = mask[:, 1:] & mask[:, :-1] & np.isfinite(horizontal)
        vertical = np.abs(np.diff(array, axis=0))
        vertical_valid = mask[1:, :] & mask[:-1, :] & np.isfinite(vertical)
        seam_h = np.zeros_like(horizontal_valid); seam_h[:, 31::32] = True
        seam_v = np.zeros_like(vertical_valid); seam_v[31::32, :] = True
        seam_values = np.concatenate((horizontal[horizontal_valid & seam_h], vertical[vertical_valid & seam_v]))
        all_values = np.concatenate((horizontal[horizontal_valid], vertical[vertical_valid]))
        seam_median = float(np.nanmedian(seam_values)) if seam_values.size else np.nan
        all_median = float(np.nanmedian(all_values)) if all_values.size else np.nan
        record["variables"][variable] = {
            "missing_pixels": int(missing.sum()),
            "minimum": float(np.nanmin(values)), "maximum": float(np.nanmax(values)),
            "median": float(np.nanmedian(values)), "iqr": float(np.nanquantile(values, .75)-np.nanquantile(values, .25)),
            "border_median": float(np.nanmedian(array[border])),
            "interior_median": float(np.nanmedian(array[interior])),
            "tile_seam_neighbor_jump_median": seam_median,
            "all_neighbor_jump_median": all_median,
            "tile_seam_to_all_jump_ratio": seam_median / all_median if all_median else np.nan,
        }
    count = result.valid_pair_count.sel(radius_km=100).values[0]
    fraction = result.valid_pair_fraction.sel(radius_km=100).values[0]
    record["support"] = {
        "valid_pair_count_min": int(np.nanmin(count[mask])),
        "valid_pair_count_median": float(np.nanmedian(count[mask])),
        "valid_pair_count_max": int(np.nanmax(count[mask])),
        "valid_pair_fraction_min": float(np.nanmin(fraction[mask])),
        "valid_pair_fraction_median": float(np.nanmedian(fraction[mask])),
        "valid_pair_fraction_max": float(np.nanmax(fraction[mask])),
        "low_support_threshold_count_p05": float(np.nanquantile(count[mask], .05)),
    }
    record["artifact_checks"] = {
        "tile_seam_flag_threshold_ratio": 1.5,
        "tile_seam_flagged_variables": [
            name for name, values in record["variables"].items()
            if values["tile_seam_to_all_jump_ratio"] > 1.5
        ],
        "missing_output_flag": any(values["missing_pixels"] for values in record["variables"].values()),
        "checkerboard_or_repeated_block_assessment": "inspect qc_maps.png; no smoothing-based correctness assumption",
    }
    return record


def _summary_csv(result: xr.Dataset) -> None:
    mask = result.output_mask.values.astype(bool)
    variables = (
        "cold_median", "warm_median", "delta_pair_median", "delta_median_difference",
        "delta_reduction_gap", "valid_pair_count", "valid_pair_fraction",
        "cold_iqr", "warm_iqr", "delta_iqr", "cold_mad", "warm_mad", "delta_mad",
        "cold_mean", "warm_mean", "delta_mean",
    )
    path = OUTPUT / "summary.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("radius_km", "variable", "valid_pixels", "mean", "std", "min", "p10", "p25", "median", "p75", "p90", "max"))
        writer.writeheader()
        for radius in RADII_KM:
            for variable in variables:
                values = np.asarray(result[variable].sel(radius_km=radius).values[0], dtype=float)[mask]
                values = values[np.isfinite(values)]
                quantiles = np.quantile(values, (.10, .25, .50, .75, .90))
                writer.writerow({
                    "radius_km": radius, "variable": variable, "valid_pixels": values.size,
                    "mean": np.mean(values), "std": np.std(values), "min": np.min(values),
                    "p10": quantiles[0], "p25": quantiles[1], "median": quantiles[2],
                    "p75": quantiles[3], "p90": quantiles[4], "max": np.max(values),
                })


def _findings(result: xr.Dataset, example_surface: xr.Dataset) -> dict[str, object]:
    mask = result.output_mask.values.astype(bool)
    arrays = {
        name: np.asarray(result[name].sel(radius_km=100).values[0], dtype=float)
        for name in (
            "cold_median", "warm_median", "delta_pair_median",
            "delta_median_difference", "delta_reduction_gap",
            "cold_iqr", "warm_iqr", "delta_iqr",
            "cold_mad", "warm_mad", "delta_mad",
        )
    }

    def adjacency_correlation(array: np.ndarray) -> float:
        left = array[:, :-1]; right = array[:, 1:]
        horizontal = mask[:, :-1] & mask[:, 1:] & np.isfinite(left) & np.isfinite(right)
        top = array[:-1, :]; bottom = array[1:, :]
        vertical = mask[:-1, :] & mask[1:, :] & np.isfinite(top) & np.isfinite(bottom)
        first = np.concatenate((left[horizontal], top[vertical]))
        second = np.concatenate((right[horizontal], bottom[vertical]))
        return float(np.corrcoef(first, second)[0, 1])

    gap = arrays["delta_reduction_gap"][mask]
    delta_pair = arrays["delta_pair_median"][mask]
    delta_difference = arrays["delta_median_difference"][mask]
    example_values = example_surface.delta_s.values[
        (example_surface.distance_km.values > 0)
        & (example_surface.distance_km.values <= 100 + 1e-7)
        & np.isfinite(example_surface.delta_s.values)
    ]
    return {
        "statewide_100km": {
            "cold_median_across_focal_pixels": float(np.nanmedian(arrays["cold_median"][mask])),
            "warm_median_across_focal_pixels": float(np.nanmedian(arrays["warm_median"][mask])),
            "delta_pair_median_across_focal_pixels": float(np.nanmedian(delta_pair)),
            "delta_positive_fraction": float(np.mean(delta_pair > 0)),
            "delta_negative_fraction": float(np.mean(delta_pair < 0)),
            "cold_warm_map_spearman": float(spearmanr(arrays["cold_median"][mask], arrays["warm_median"][mask]).statistic),
        },
        "delta_reduction_comparison": {
            "median_gap": float(np.nanmedian(gap)),
            "median_absolute_gap": float(np.nanmedian(np.abs(gap))),
            "p95_absolute_gap": float(np.nanquantile(np.abs(gap), .95)),
            "maximum_absolute_gap": float(np.nanmax(np.abs(gap))),
            "spearman_between_maps": float(spearmanr(delta_pair, delta_difference).statistic),
        },
        "local_surface_dispersion_medians": {
            name: float(np.nanmedian(array[mask]))
            for name, array in arrays.items() if name.endswith("_iqr") or name.endswith("_mad")
        },
        "adjacent_pixel_pearson": {
            name: adjacency_correlation(arrays[name]) for name in PRIMARY
        },
        "example_focal_surface": {
            "focal_latitude": float(example_surface.attrs["focal_y"]),
            "focal_longitude": float(example_surface.attrs["focal_x"]),
            "nonself_valid_delta_pairs": int(example_values.size),
            "delta_median": float(np.median(example_values)),
            "delta_iqr": float(np.quantile(example_values, .75) - np.quantile(example_values, .25)),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-gates", action="store_true", help="Resume/finalize without rerunning gates")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cube, colorado_mask, boundary = _load_inputs()
    geometry = _geometry_record(cube, colorado_mask)
    _json(OUTPUT / "geometry.json", geometry)

    gate_records = []
    if not args.skip_gates:
        gate_records.append(_gate(
            cube, name="complete_25x25_focal_gate", mask=_center_mask(cube, 25, 25),
            tile_shape=(13, 13), checkpoint_dir=OUTPUT / "gate_tiles_25",
        ))
        gate_cube = cube.isel(y=slice((cube.sizes["y"]-100)//2, (cube.sizes["y"]-100)//2+100), x=slice((cube.sizes["x"]-100)//2, (cube.sizes["x"]-100)//2+100))
        gate_records.append(_gate(
            gate_cube, name="phase2_100x100_computation_gate", mask=_center_mask(gate_cube, 50, 50),
            tile_shape=(25, 25), checkpoint_dir=OUTPUT / "gate_tiles_100",
        ))
        _json(OUTPUT / "engineering_gates.json", {"status": "PASS", "gates": gate_records, "geometry_note": geometry["interpretation"]})

    with _performance() as performance:
        result = tiled_nonstacked_synchrony_summary(
            cube,
            lower_var="tmin", upper_var="tmax", output_mask=colorado_mask,
            radii_km=RADII_KM, tile_shape=TILE_SHAPE,
            window_days=WINDOW_DAYS, window_end=WINDOW_END, min_t=MIN_T,
            pair_batch_size=8192, checkpoint_dir=OUTPUT / "tiles",
        )
    result.attrs.update({
        "experiment": "simple non-stacked Colorado synchrony baseline",
        "input_snapshot": str(CUBE_PATH.relative_to(ROOT)),
        "output_domain": "Colorado focal grid cells",
        "input_domain": "Colorado plus approximately 100 km halo",
        "delta_sign_convention": "cold synchrony - warm synchrony; positive means stronger cold-tail synchrony",
        "neighborhood_geometry": geometry["interpretation"],
    })
    result_path = OUTPUT / "colorado_nonstacked_synchrony.nc"
    _netcdf(result_path, result)

    selected = np.argwhere(colorado_mask.values)
    yi, xi = selected[len(selected) // 2]
    one_mask = xr.zeros_like(colorado_mask, dtype=bool)
    one_mask.values[yi, xi] = True
    one_pairs = local_synchrony_pairs(
        cube, lower_var="tmin", upper_var="tmax", output_mask=one_mask,
        max_radius_km=100, window_days=WINDOW_DAYS, window_end=WINDOW_END,
        min_t=MIN_T, pair_batch_size=4096,
    )
    example_surface = local_synchrony_surface(one_pairs, focal_y_index=int(yi), focal_x_index=int(xi))
    _netcdf(OUTPUT / "example_local_surface.nc", example_surface)

    raster_paths = _write_geotiffs(result)
    figure_record = _figures(result, boundary, example_surface)
    qc = _qc(result)
    _json(OUTPUT / "qc.json", qc)
    _summary_csv(result)
    findings = _findings(result, example_surface)
    _json(OUTPUT / "findings.json", findings)
    performance.update({
        "status": "PASS",
        "run_mode": "computed" if int(result.attrs["computed_tile_count"]) else "checkpoint_resume_and_finalization",
        "input_snapshot_bytes": CUBE_PATH.stat().st_size,
        "network_data_transferred_bytes": 0,
        "output_pixels": int(colorado_mask.sum()),
        "tile_count": int(result.attrs["tile_count"]),
        "computed_tile_count": int(result.attrs["computed_tile_count"]),
        "resumed_tile_count": int(result.attrs["resumed_tile_count"]),
        "pair_calculations_with_tile_recompute": int(result.attrs["pair_calculation_count_with_tile_recompute"]),
        "nonself_pair_calculations_with_tile_recompute": int(result.attrs["nonself_pair_calculation_count_with_tile_recompute"]),
        "global_unique_pair_count": None,
        "global_unique_pair_count_status": "not materialized; canonical pairs are unique within a tile and cross-tile endpoint pairs may be recomputed to preserve bounded memory",
        "failures": 0,
        "retries": 0,
        "checkpoint_bytes": sum(path.stat().st_size for path in (OUTPUT / "tiles").glob("*")),
        "final_netcdf_bytes": result_path.stat().st_size,
        "pair_kernel_seconds_sum": float(result.attrs["pair_kernel_seconds_sum"]),
        "pair_geometry_seconds_sum": float(result.attrs["pair_geometry_seconds_sum"]),
        "input_materialization_seconds_sum": float(result.attrs["input_materialization_seconds_sum"]),
        "exact_reduction_seconds_sum": float(result.attrs["signature_reduction_seconds_sum"]),
    })
    tile_paths = sorted((OUTPUT / "tiles").glob("*.nc"))
    if tile_paths:
        first_mtime = min(path.stat().st_mtime for path in tile_paths)
        last_mtime = max(path.stat().st_mtime for path in tile_paths)
        performance["checkpoint_compute_started_at_utc"] = datetime.fromtimestamp(first_mtime, timezone.utc).isoformat()
        performance["checkpoint_compute_ended_at_utc"] = datetime.fromtimestamp(last_mtime, timezone.utc).isoformat()
        performance["checkpoint_compute_span_seconds"] = last_mtime - first_mtime
    _json(OUTPUT / "performance.json", performance)
    provenance = {
        "status": "complete",
        "real_observations": True,
        "input_sha256": sha256(CUBE_PATH.read_bytes()).hexdigest(),
        "input_path": str(CUBE_PATH.relative_to(ROOT)),
        "output_sha256": sha256(result_path.read_bytes()).hexdigest(),
        "output_path": str(result_path.relative_to(ROOT)),
        "source": cube.attrs.get("source"),
        "source_provider": cube.attrs.get("source_provider"),
        "date_range": [str(cube.time.values[0]), str(cube.time.values[-1])],
        "variables": ["tmin", "tmax"],
        "window_days": WINDOW_DAYS,
        "window_end": WINDOW_END,
        "min_t_per_tail": MIN_T,
        "split_quantile": 0.5,
        "pair_statistic": "one-tail Spearman using current CubeDynamics validated kernel",
        "delta_sign_convention": "cold - warm",
        "self_pair_policy": "excluded",
        "stacking": False,
        "overlap_alignment": False,
        "second_stage_convolution": False,
        "quantile_method": "exact numpy quantile",
        "raster_outputs": raster_paths,
        "figures": figure_record,
        "reproduction_command": ".venv/bin/python scripts/run_nonstacked_colorado_baseline.py",
    }
    _json(OUTPUT / "provenance.json", provenance)
    (OUTPUT / "REPRODUCE.md").write_text(
        "# Reproduce the non-stacked Colorado baseline\n\n"
        "From the repository root, with the existing Phase 2 observed-PRISM snapshot present:\n\n"
        "```bash\n.venv/bin/python scripts/run_nonstacked_colorado_baseline.py\n```\n\n"
        "The command is restartable: completed tile checkpoints are fingerprint-validated and reused. "
        "Use `--skip-gates` only to finalize an already gated run. No network access is performed.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "output": str(result_path), "performance": performance}, indent=2))


if __name__ == "__main__":
    main()
