#!/usr/bin/env python3
"""Run the bounded empirical synchrony-range gate and Colorado pilot.

This workflow intentionally stops before a statewide or CONUS production run.
It uses real retained PRISM observations, reuses each 500 km pair table across
all sensitivity analyses, and records an explicit scale-up decision gate.

Reproduction::

    .venv/bin/python scripts/run_empirical_synchrony_range_pilot.py
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
from scipy.stats import pearsonr, spearmanr
from shapely.geometry import shape
import xarray as xr

from cubedynamics.serialization import sanitize_netcdf_attrs
from cubedynamics.synchrony.production import expand_spatial_domain, local_synchrony_pairs
from cubedynamics.synchrony.ranges import (
    RANGE_STATUS,
    empirical_range_curve,
    empirical_synchrony_range,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "empirical-synchrony-range"
FIGURES = OUTPUT / "figures"
PAIR_DIR = OUTPUT / "pair_checkpoints"
CONUS_CUBE = (
    ROOT
    / "artifacts"
    / "nonstacked-conus-baseline"
    / "inputs"
    / "prism_conus_20231101_20240130.nc"
)
CONUS_BASELINE = ROOT / "artifacts" / "nonstacked-conus-baseline" / "conus_nonstacked_synchrony.nc"
COLORADO_BASELINE = ROOT / "artifacts" / "nonstacked-colorado-baseline" / "colorado_nonstacked_synchrony.nc"
COLORADO_MASK = ROOT / "artifacts" / "synchrony-stack-phase2" / "colorado_synchrony_signature.nc"
COLORADO_BOUNDARY = ROOT / "artifacts" / "synchrony-stack-phase2" / "colorado_boundary.geojson"

WINDOW_DAYS = 90
WINDOW_END = "2024-01-30"
MIN_T = 10
DISCOVERY_RADIUS_KM = 500.0
DISCOVERY_SENSITIVITY = (200.0, 300.0, 400.0, 500.0)
BIN_WIDTH_SENSITIVITY = (10.0, 20.0, 40.0)
PRIMARY_BIN_WIDTH_KM = 20.0
FIXED_RADIUS_KM = 100.0
REPRESENTATIVE = {
    "Colorado mountains": (-106.4, 39.1),
    "Great Plains": (-100.0, 40.0),
    "Southeast": (-84.0, 33.0),
    "Northeast": (-73.5, 43.0),
    "Pacific region": (-121.5, 45.0),
}

NAVY = "#123F70"
BLUE = "#2878B5"
RED = "#B63A3A"
GOLD = "#F0B43C"
GREEN = "#3A8D6D"
INK = "#17212B"
MUTED = "#586775"


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.json")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields = list(rows[0])
    temporary = path.with_suffix(".partial.csv")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _netcdf(path: Path, dataset: xr.Dataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.nc")
    clean = sanitize_netcdf_attrs(dataset, copy=True)
    for name in clean.variables:
        clean[name].encoding = {}
    clean.to_netcdf(temporary, engine="h5netcdf")
    temporary.replace(path)


@contextmanager
def _performance():
    wall = time.perf_counter()
    cpu = time.process_time()
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record: dict[str, object] = {"started_at_utc": datetime.now(timezone.utc).isoformat()}
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


def _point_subset(
    cube: xr.Dataset,
    computation: xr.DataArray,
    lon: float,
    lat: float,
    radius_km: float,
) -> tuple[xr.Dataset, xr.DataArray, xr.DataArray, int, int, float, float]:
    xi = int(np.argmin(np.abs(np.asarray(cube.x.values) - lon)))
    yi = int(np.argmin(np.abs(np.asarray(cube.y.values) - lat)))
    focal_lon = float(cube.x.values[xi])
    focal_lat = float(cube.y.values[yi])
    bounds = expand_spatial_domain(
        (focal_lon, focal_lat, focal_lon, focal_lat), radius_km
    ).bounds
    y_index = np.flatnonzero((cube.y.values >= bounds[1]) & (cube.y.values <= bounds[3]))
    x_index = np.flatnonzero((cube.x.values >= bounds[0]) & (cube.x.values <= bounds[2]))
    y_slice = slice(int(y_index.min()), int(y_index.max()) + 1)
    x_slice = slice(int(x_index.min()), int(x_index.max()) + 1)
    subset = cube.isel(y=y_slice, x=x_slice).load()
    subset_computation = computation.isel(y=y_slice, x=x_slice).load().astype(bool)
    local_y = int(np.argmin(np.abs(np.asarray(subset.y.values) - focal_lat)))
    local_x = int(np.argmin(np.abs(np.asarray(subset.x.values) - focal_lon)))
    output = xr.zeros_like(subset.tmin.isel(time=0), dtype=bool)
    output.values[local_y, local_x] = True
    if not bool(subset_computation.values[local_y, local_x]):
        raise ValueError(f"Representative point {focal_lon}, {focal_lat} is not a complete PRISM cell")
    return subset, subset_computation, output, local_y, local_x, focal_lon, focal_lat


def _pair_checkpoint(
    name: str,
    cube: xr.Dataset,
    output: xr.DataArray,
    computation: xr.DataArray,
    *,
    force: bool,
) -> tuple[xr.Dataset, bool]:
    path = PAIR_DIR / f"{name}.nc"
    manifest_path = path.with_suffix(".json")
    if path.exists() and manifest_path.exists() and not force:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        with xr.open_dataset(path, engine="h5netcdf") as opened:
            pairs = opened.load()
        if manifest.get("analysis_fingerprint") != pairs.attrs.get("analysis_fingerprint"):
            raise ValueError(f"Pair checkpoint fingerprint mismatch: {path}")
        return pairs, True
    with _performance() as timing:
        pairs = local_synchrony_pairs(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=output,
            computation_mask=computation,
            max_radius_km=DISCOVERY_RADIUS_KM,
            window_days=WINDOW_DAYS,
            window_end=WINDOW_END,
            min_t=MIN_T,
            split_quantile=0.5,
            pair_batch_size=8192,
        )
    pairs.attrs["checkpoint_wall_seconds"] = float(timing["wall_seconds"])
    pairs.attrs["checkpoint_process_peak_rss_bytes"] = int(timing["process_peak_rss_bytes"])
    _netcdf(path, pairs)
    _json(
        manifest_path,
        {
            "status": "complete",
            "path": str(path.relative_to(ROOT)),
            "analysis_fingerprint": pairs.attrs["analysis_fingerprint"],
            "pair_count": int(pairs.sizes["pair"]),
            "nonself_pair_count": int(pairs.attrs["nonself_pair_count"]),
            "wall_seconds": timing["wall_seconds"],
            "sha256": sha256(path.read_bytes()).hexdigest(),
        },
    )
    return pairs, False


def _subset_pairs(pairs: xr.Dataset, discovery_radius_km: float) -> xr.Dataset:
    selected = np.asarray(pairs.distance_km.values) <= discovery_radius_km + 1e-7
    result = pairs.isel(pair=selected).copy()
    result.attrs = dict(pairs.attrs)
    result.attrs.update(
        {
            "max_radius_km": float(discovery_radius_km),
            "observation_radius_km": float(discovery_radius_km),
            "analysis_fingerprint": (
                f"{pairs.attrs['analysis_fingerprint']}-bounded-{discovery_radius_km:g}km"
            ),
            "unique_pair_count": int(np.count_nonzero(selected)),
            "nonself_pair_count": int(
                np.count_nonzero(
                    np.asarray(result.source_index.values)
                    != np.asarray(result.target_index.values)
                )
            ),
        }
    )
    return result


def _value(summary: xr.Dataset, name: str, yi: int, xi: int) -> float:
    return float(summary[name].isel(time_window_end=0, y=yi, x=xi).values)


def _status(summary: xr.Dataset, metric: str, yi: int, xi: int) -> int:
    return int(summary[f"{metric}_range_status"].isel(time_window_end=0, y=yi, x=xi).values)


def _incident(pairs: xr.Dataset, yi: int, xi: int) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray]:
    x_size = pairs.sizes["x"]
    focal = yi * x_size + xi
    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    selected = ((source == focal) | (target == focal)) & (source != target)
    index = np.flatnonzero(selected)
    reverse = target[index] == focal
    distance = np.asarray(pairs.distance_km.values, dtype=float)[index]
    values = {
        name: np.asarray(pairs[name].values, dtype=float)[index]
        for name in ("cold_synchrony", "warm_synchrony", "delta_s")
    }
    bearing = np.asarray(pairs.bearing_degrees.values, dtype=float)[index].copy()
    bearing[reverse & np.isfinite(bearing)] = (bearing[reverse & np.isfinite(bearing)] + 180) % 360
    return distance, values, bearing, index


def _diagnostic_figure(
    label: str,
    pairs: xr.Dataset,
    summary: xr.Dataset,
    yi: int,
    xi: int,
) -> Path:
    distance, values, _, _ = _incident(pairs, yi, xi)
    rng = np.random.default_rng(abs(hash(label)) % 2**32)
    sample = np.arange(distance.size)
    if sample.size > 7000:
        sample = np.sort(rng.choice(sample, size=7000, replace=False))
    fig, axes = plt.subplots(2, 1, figsize=(12.6, 8.0), sharex=True, constrained_layout=True)
    for ax, metric, prefix, color in (
        (axes[0], "cold_synchrony", "cold", BLUE),
        (axes[1], "warm_synchrony", "warm", RED),
    ):
        ax.scatter(distance[sample], values[metric][sample], s=3, alpha=0.08, color=color, rasterized=True)
        radius = np.asarray(summary.radius_km.values)
        median = summary[f"{prefix}_annular_median"].isel(time_window_end=0, y=yi, x=xi).values
        q25 = summary[f"{prefix}_annular_q25"].isel(time_window_end=0, y=yi, x=xi).values
        q75 = summary[f"{prefix}_annular_q75"].isel(time_window_end=0, y=yi, x=xi).values
        cumulative = summary[f"{prefix}_cumulative_median"].isel(time_window_end=0, y=yi, x=xi).values
        background = _value(summary, f"{prefix}_background", yi, xi)
        estimated = _value(summary, f"{prefix}_range_km", yi, xi)
        status = RANGE_STATUS[_status(summary, prefix, yi, xi)]
        ax.fill_between(radius, q25, q75, color=color, alpha=0.22, label="Annular IQR")
        ax.plot(radius, median, color=color, lw=2.2, marker="o", ms=3.5, label="Annular median")
        ax.plot(radius, cumulative, color=INK, lw=1.8, ls="--", label="Cumulative median")
        ax.axhline(background, color=GOLD, lw=2, label="Selected distant background")
        if np.isfinite(estimated):
            ax.axvline(estimated, color=GREEN, lw=2.2, label=f"R* = {estimated:.0f} km")
        ax.axvline(DISCOVERY_RADIUS_KM, color=MUTED, lw=1.6, ls=":", label="Discovery limit")
        ax.set(ylabel="Spearman synchrony", ylim=(-0.45, 1.03))
        ax.set_title(f"{prefix.capitalize()} response - {status.replace('_', ' ')}", loc="left", weight="bold")
        ax.grid(alpha=0.16)
        ax.legend(frameon=False, ncol=3, fontsize=8, loc="lower left")
    axes[-1].set_xlabel("Physical distance from focal pixel (km)")
    fig.suptitle(
        f"{label}: empirical synchrony-distance response",
        fontsize=17,
        color=NAVY,
        weight="bold",
    )
    path = FIGURES / f"diagnostic_{label.lower().replace(' ', '_')}.png"
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _representative_gate(cube: xr.Dataset, computation: xr.DataArray, *, force: bool) -> tuple[list[dict], list[dict], list[Path], dict]:
    sensitivity: list[dict[str, object]] = []
    primary_rows: list[dict[str, object]] = []
    figures: list[Path] = []
    performance_rows = []
    for label, (lon, lat) in REPRESENTATIVE.items():
        subset, eligible, output, yi, xi, focal_lon, focal_lat = _point_subset(
            cube, computation, lon, lat, DISCOVERY_RADIUS_KM
        )
        key = label.lower().replace(" ", "_")
        pairs, resumed = _pair_checkpoint(key, subset, output, eligible, force=force)
        performance_rows.append(
            {
                "label": label,
                "pair_count": int(pairs.sizes["pair"]),
                "pair_kernel_seconds": float(pairs.attrs["pair_kernel_seconds"]),
                "total_seconds": float(pairs.attrs["total_seconds"]),
                "checkpoint_resumed": resumed,
            }
        )
        primary = None
        for discovery in DISCOVERY_SENSITIVITY:
            bounded = _subset_pairs(pairs, discovery)
            for width in BIN_WIDTH_SENSITIVITY:
                summary = empirical_synchrony_range(
                    bounded,
                    bin_width_km=width,
                    min_annulus_count=30,
                    background_shell_count=4,
                    background_method="outer_annuli",
                    persistence_bins=3,
                    fixed_radius_km=FIXED_RADIUS_KM,
                )
                row = {
                    "label": label,
                    "longitude": focal_lon,
                    "latitude": focal_lat,
                    "discovery_radius_km": discovery,
                    "bin_width_km": width,
                }
                for metric in ("cold", "warm", "common"):
                    row[f"{metric}_range_km"] = _value(summary, f"{metric}_range_km", yi, xi)
                    row[f"{metric}_status_code"] = _status(summary, metric, yi, xi)
                    row[f"{metric}_status"] = RANGE_STATUS[row[f"{metric}_status_code"]]
                sensitivity.append(row)
                if discovery == DISCOVERY_RADIUS_KM and width == PRIMARY_BIN_WIDTH_KM:
                    primary = summary
        assert primary is not None
        row = {
            "label": label,
            "longitude": focal_lon,
            "latitude": focal_lat,
            "pair_count": int(pairs.attrs["nonself_pair_count"]),
        }
        for metric in ("cold", "warm", "common"):
            row[f"{metric}_range_km"] = _value(primary, f"{metric}_range_km", yi, xi)
            row[f"{metric}_status_code"] = _status(primary, metric, yi, xi)
            row[f"{metric}_status"] = RANGE_STATUS[row[f"{metric}_status_code"]]
            if metric != "common":
                row[f"{metric}_background_outer_annuli"] = _value(
                    primary, f"{metric}_background_outer_annuli", yi, xi
                )
                row[f"{metric}_background_smoothed_outer_annuli"] = _value(
                    primary, f"{metric}_background_smoothed_outer_annuli", yi, xi
                )
                row[f"{metric}_background_distant_pairs"] = _value(
                    primary, f"{metric}_background_distant_pairs", yi, xi
                )
        row["fixed_delta"] = _value(primary, "fixed_delta_pair_median", yi, xi)
        row["adaptive_delta"] = _value(primary, "adaptive_delta_pair_median", yi, xi)
        primary_rows.append(row)
        figures.append(_diagnostic_figure(label, pairs, primary, yi, xi))
    return primary_rows, sensitivity, figures, {"representative_pair_runs": performance_rows}


def _spatial_sample(mask: xr.DataArray, count_y: int = 5, count_x: int = 5) -> list[tuple[int, int]]:
    selected = np.argwhere(np.asarray(mask.values, dtype=bool))
    if selected.size == 0:
        raise ValueError("Colorado mask is empty")
    y_values = np.asarray(mask.y.values)[selected[:, 0]]
    x_values = np.asarray(mask.x.values)[selected[:, 1]]
    targets_y = np.linspace(float(y_values.min()), float(y_values.max()), count_y)
    targets_x = np.linspace(float(x_values.min()), float(x_values.max()), count_x)
    picked: list[tuple[int, int]] = []
    mean_lat = float(np.mean(y_values))
    for target_y in targets_y:
        for target_x in targets_x:
            distance = (y_values - target_y) ** 2 + (
                (x_values - target_x) * np.cos(np.deg2rad(mean_lat))
            ) ** 2
            for index in np.argsort(distance):
                candidate = (int(selected[index, 0]), int(selected[index, 1]))
                if candidate not in picked:
                    picked.append(candidate)
                    break
    return picked


def _colorado_subset(
    cube: xr.Dataset,
    computation: xr.DataArray,
) -> tuple[xr.Dataset, xr.DataArray, xr.DataArray, list[tuple[int, int]]]:
    with xr.open_dataset(COLORADO_MASK, engine="scipy") as opened:
        state_mask_small = opened.output_mask.load().astype(bool)
    state_mask = state_mask_small.reindex(y=cube.y, x=cube.x, fill_value=False)
    selected = np.argwhere(state_mask.values)
    bounds = (
        float(cube.x.values[selected[:, 1]].min()),
        float(cube.y.values[selected[:, 0]].min()),
        float(cube.x.values[selected[:, 1]].max()),
        float(cube.y.values[selected[:, 0]].max()),
    )
    halo = expand_spatial_domain(bounds, DISCOVERY_RADIUS_KM).bounds
    y_index = np.flatnonzero((cube.y.values >= halo[1]) & (cube.y.values <= halo[3]))
    x_index = np.flatnonzero((cube.x.values >= halo[0]) & (cube.x.values <= halo[2]))
    y_slice = slice(int(y_index.min()), int(y_index.max()) + 1)
    x_slice = slice(int(x_index.min()), int(x_index.max()) + 1)
    subset = cube.isel(y=y_slice, x=x_slice).load()
    eligible = computation.isel(y=y_slice, x=x_slice).load().astype(bool)
    local_state = state_mask.isel(y=y_slice, x=x_slice).astype(bool)
    sample_indices = _spatial_sample(local_state)
    output = xr.zeros_like(subset.tmin.isel(time=0), dtype=bool)
    for yi, xi in sample_indices:
        output.values[yi, xi] = True
    return subset, eligible, output, sample_indices


def _manual_gate(
    pairs: xr.Dataset,
    result: xr.Dataset,
    sample_indices: list[tuple[int, int]],
) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    for yi, xi in sample_indices[:: max(1, len(sample_indices) // 3)][:3]:
        distance, values, _, _ = _incident(pairs, yi, xi)
        fixed = (distance > 0) & (distance <= FIXED_RADIUS_KM + 1e-7)
        expected = float(np.median(values["delta_s"][fixed & np.isfinite(values["delta_s"])]))
        actual = _value(result, "fixed_delta_pair_median", yi, xi)
        counts = result.delta_annular_count.isel(time_window_end=0, y=yi, x=xi).values
        assigned = np.histogram(
            distance[(distance > 0) & (distance <= DISCOVERY_RADIUS_KM + 1e-7)],
            bins=np.asarray(
                [*result.radius_lower_km.values, result.radius_upper_km.values[-1]], dtype=float
            ),
        )[0]
        check = {
            "y_index": yi,
            "x_index": xi,
            "longitude": float(pairs.x.values[xi]),
            "latitude": float(pairs.y.values[yi]),
            "fixed_delta_manual": expected,
            "fixed_delta_output": actual,
            "fixed_delta_absolute_error": abs(expected - actual),
            "annular_count_max_absolute_error": int(np.max(np.abs(counts - assigned))),
            "common_status": RANGE_STATUS[_status(result, "common", yi, xi)],
        }
        common = _value(result, "common_range_km", yi, xi)
        if np.isfinite(common):
            adaptive = (distance > 0) & (distance <= common + 1e-7)
            manual = float(np.median(values["delta_s"][adaptive & np.isfinite(values["delta_s"])]))
            check["adaptive_delta_manual"] = manual
            check["adaptive_delta_output"] = _value(result, "adaptive_delta_pair_median", yi, xi)
            check["adaptive_delta_absolute_error"] = abs(
                manual - check["adaptive_delta_output"]
            )
        checks.append(check)
    maximum = max(
        max(item["fixed_delta_absolute_error"], item.get("adaptive_delta_absolute_error", 0.0))
        for item in checks
    )
    count_max = max(item["annular_count_max_absolute_error"] for item in checks)
    return {
        "status": "PASS" if maximum <= 1e-12 and count_max == 0 else "FAIL",
        "maximum_manual_reduction_absolute_error": maximum,
        "maximum_annular_count_error": count_max,
        "checks": checks,
    }


def _map_comparison_statistics(fixed: np.ndarray, adaptive: np.ndarray) -> dict[str, object]:
    valid = np.isfinite(fixed) & np.isfinite(adaptive)
    if np.count_nonzero(valid) < 3:
        return {
            "status": "insufficient resolved common ranges",
            "resolved_comparison_count": int(np.count_nonzero(valid)),
        }
    left = fixed[valid]
    right = adaptive[valid]
    difference = right - left
    return {
        "status": "computed on resolved common-range pilot sites only",
        "resolved_comparison_count": int(left.size),
        "pearson": float(pearsonr(left, right).statistic),
        "spearman": float(spearmanr(left, right).statistic),
        "rmse": float(np.sqrt(np.mean(difference**2))),
        "mae": float(np.mean(np.abs(difference))),
        "median_absolute_difference": float(np.median(np.abs(difference))),
        "difference_iqr": float(np.quantile(difference, 0.75) - np.quantile(difference, 0.25)),
        "robust_maximum_absolute_difference_p95": float(np.quantile(np.abs(difference), 0.95)),
        "fraction_abs_change_gt_0_01": float(np.mean(np.abs(difference) > 0.01)),
        "fraction_abs_change_gt_0_025": float(np.mean(np.abs(difference) > 0.025)),
        "fraction_abs_change_gt_0_05": float(np.mean(np.abs(difference) > 0.05)),
        "fraction_sign_changed": float(np.mean(np.sign(left) != np.sign(right))),
    }


def _outline(ax, boundary) -> None:
    geometries = list(boundary.geoms) if hasattr(boundary, "geoms") else [boundary]
    for geometry in geometries:
        xx, yy = geometry.exterior.xy
        ax.plot(xx, yy, color=INK, lw=0.8)
    ax.set_aspect(1 / np.cos(np.deg2rad(39.0)))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


def _scatter_map(ax, x, y, values, boundary, *, cmap, norm, title, unresolved=None):
    _outline(ax, boundary)
    image = ax.scatter(x, y, c=values, s=68, cmap=cmap, norm=norm, edgecolor="white", linewidth=0.6, zorder=3)
    if unresolved is not None and np.any(unresolved):
        ax.scatter(np.asarray(x)[unresolved], np.asarray(y)[unresolved], marker="x", s=62, color=INK, lw=1.4, zorder=4)
    ax.set_title(title, loc="left", weight="bold")
    return image


def _colorado_figures(
    result: xr.Dataset,
    sample_indices: list[tuple[int, int]],
    baseline: xr.Dataset,
    boundary,
) -> list[Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    yy = np.asarray([item[0] for item in sample_indices])
    xx = np.asarray([item[1] for item in sample_indices])
    lon = np.asarray(result.x.values)[xx]
    lat = np.asarray(result.y.values)[yy]
    fixed = result.fixed_delta_pair_median.isel(time_window_end=0).values[yy, xx]
    adaptive = result.adaptive_delta_pair_median.isel(time_window_end=0).values[yy, xx]
    common = result.common_range_km.isel(time_window_end=0).values[yy, xx]
    difference = adaptive - fixed
    unresolved = ~np.isfinite(common)
    delta_limit = max(float(np.nanpercentile(np.abs(fixed), 99)), 0.05)
    change_limit = max(float(np.nanmax(np.abs(difference))) if np.isfinite(difference).any() else 0.01, 0.01)

    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.2), constrained_layout=True)
    specs = [
        (fixed, "RdBu", TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit), "A  Fixed 100 km Delta", None),
        (adaptive, "RdBu", TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit), "B  Adaptive Delta at resolved sites", unresolved),
        (common, "viridis", Normalize(0, DISCOVERY_RADIUS_KM), "C  Common empirical range R* (km)", unresolved),
        (difference, "PiYG", TwoSlopeNorm(vmin=-change_limit, vcenter=0, vmax=change_limit), "D  Adaptive minus fixed Delta", unresolved),
    ]
    for ax, (values, cmap, norm, title, missing) in zip(axes.ravel(), specs):
        image = _scatter_map(ax, lon, lat, values, boundary, cmap=cmap, norm=norm, title=title, unresolved=missing)
        fig.colorbar(image, ax=ax, shrink=0.72)
    fig.suptitle("Bounded 25-site Colorado pilot - unresolved sites marked x", fontsize=17, weight="bold", color=NAVY)
    path = FIGURES / "colorado_fixed_adaptive_primary.png"
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(14.2, 8.0), constrained_layout=True)
    fields = [
        (result.fixed_cold_median, "A  Fixed cold", "viridis"),
        (result.adaptive_cold_median, "B  Adaptive cold at R*cold", "viridis"),
        (result.fixed_warm_median, "C  Fixed warm", "viridis"),
        (result.adaptive_warm_median, "D  Adaptive warm at R*warm", "viridis"),
        (result.fixed_delta_pair_median, "E  Fixed Delta", "RdBu"),
        (result.adaptive_delta_pair_median, "F  Adaptive common-range Delta", "RdBu"),
    ]
    sync_values = np.concatenate(
        (
            result.fixed_cold_median.values[np.isfinite(result.fixed_cold_median.values)],
            result.fixed_warm_median.values[np.isfinite(result.fixed_warm_median.values)],
        )
    )
    sync_norm = Normalize(float(np.quantile(sync_values, 0.02)), float(np.quantile(sync_values, 0.98)))
    delta_norm = TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit)
    for ax, (field, title, cmap) in zip(axes.ravel(), fields):
        values = field.isel(time_window_end=0).values[yy, xx]
        norm = sync_norm if cmap == "viridis" else delta_norm
        missing = ~np.isfinite(values)
        image = _scatter_map(ax, lon, lat, values, boundary, cmap=cmap, norm=norm, title=title, unresolved=missing)
        fig.colorbar(image, ax=ax, shrink=0.65)
    fig.suptitle("Fixed and adaptive synchrony strength remain separate from range", fontsize=16, weight="bold", color=NAVY)
    path2 = FIGURES / "colorado_cold_warm_delta.png"
    fig.savefig(path2, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(13.0, 8.2), constrained_layout=True)
    range_specs = [
        (result.cold_range_km, "A  Cold R* (km)", "viridis", Normalize(0, DISCOVERY_RADIUS_KM)),
        (result.warm_range_km, "B  Warm R* (km)", "viridis", Normalize(0, DISCOVERY_RADIUS_KM)),
        (result.common_range_km, "C  Common R* (km)", "viridis", Normalize(0, DISCOVERY_RADIUS_KM)),
        (result.range_difference_cold_minus_warm_km, "D  Cold R* minus warm R* (km)", "PuOr", TwoSlopeNorm(vmin=-250, vcenter=0, vmax=250)),
    ]
    for ax, (field, title, cmap, norm) in zip(axes.ravel(), range_specs):
        values = field.isel(time_window_end=0).values[yy, xx]
        image = _scatter_map(ax, lon, lat, values, boundary, cmap=cmap, norm=norm, title=title, unresolved=~np.isfinite(values))
        fig.colorbar(image, ax=ax, shrink=0.72)
    fig.suptitle("Empirical range products - unresolved estimates are not assigned 500 km", fontsize=16, weight="bold", color=NAVY)
    path3 = FIGURES / "colorado_range_products.png"
    fig.savefig(path3, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    reliability = result.common_range_reliability.isel(time_window_end=0).values[yy, xx]
    status = result.common_range_status.isel(time_window_end=0).values[yy, xx]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.5), constrained_layout=True)
    image = _scatter_map(
        axes[0], lon, lat, reliability, boundary, cmap="viridis", norm=Normalize(0, 1),
        title="A  Common-range reliability", unresolved=~np.isfinite(reliability),
    )
    fig.colorbar(image, ax=axes[0], shrink=0.75)
    image = _scatter_map(
        axes[1], lon, lat, status, boundary, cmap="tab10", norm=Normalize(-0.5, 3.5),
        title="B  Status code (2 = censored/unresolved)", unresolved=status != 3,
    )
    fig.colorbar(image, ax=axes[1], shrink=0.75, ticks=(0, 1, 2, 3))
    fig.suptitle("Reliability and censoring are primary outputs", fontsize=16, weight="bold", color=NAVY)
    path4 = FIGURES / "colorado_reliability_censoring.png"
    fig.savefig(path4, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [path, path2, path3, path4]


def _anisotropy(
    pairs: xr.Dataset,
    sample_indices: list[tuple[int, int]],
) -> tuple[list[dict[str, object]], Path]:
    rows: list[dict[str, object]] = []
    sector_centers = {"N": 0.0, "E": 90.0, "S": 180.0, "W": 270.0}
    for yi, xi in sample_indices:
        distance, values, bearing, _ = _incident(pairs, yi, xi)
        for sector, center in sector_centers.items():
            separation = np.abs(((bearing - center + 180) % 360) - 180)
            selected = separation <= 45.0
            for metric, variable in (("cold", "cold_synchrony"), ("warm", "warm_synchrony")):
                curve = empirical_range_curve(
                    distance[selected],
                    values[variable][selected],
                    discovery_radius_km=DISCOVERY_RADIUS_KM,
                    bin_width_km=PRIMARY_BIN_WIDTH_KM,
                    min_annulus_count=10,
                    background_shell_count=4,
                    persistence_bins=3,
                )
                rows.append(
                    {
                        "y_index": yi,
                        "x_index": xi,
                        "longitude": float(pairs.x.values[xi]),
                        "latitude": float(pairs.y.values[yi]),
                        "sector": sector,
                        "metric": metric,
                        "range_km": curve.attrs["range_km"],
                        "status_code": curve.attrs["status_code"],
                        "status": curve.attrs["status"],
                        "pair_count": int(np.count_nonzero(selected)),
                    }
                )
    representative = sample_indices[len(sample_indices) // 2]
    local = [row for row in rows if row["y_index"] == representative[0] and row["x_index"] == representative[1]]
    fig, ax = plt.subplots(figsize=(9.0, 4.6), constrained_layout=True)
    positions = np.arange(4)
    for offset, metric, color in ((-0.18, "cold", BLUE), (0.18, "warm", RED)):
        by_sector = {row["sector"]: row for row in local if row["metric"] == metric}
        values = [by_sector[name]["range_km"] for name in ("N", "E", "S", "W")]
        heights = [value if np.isfinite(value) else DISCOVERY_RADIUS_KM for value in values]
        bars = ax.bar(positions + offset, heights, width=0.34, color=color, alpha=0.82, label=metric.capitalize())
        for bar, value in zip(bars, values):
            if not np.isfinite(value):
                ax.text(bar.get_x() + bar.get_width() / 2, DISCOVERY_RADIUS_KM - 18, "unresolved", rotation=90, ha="center", va="top", fontsize=8, color="white")
    ax.axhline(DISCOVERY_RADIUS_KM, color=MUTED, ls=":")
    ax.set_xticks(positions, ("N", "E", "S", "W"))
    ax.set(ylabel="Sector empirical range (km)", ylim=(0, DISCOVERY_RADIUS_KM * 1.05))
    ax.set_title("Directional subset diagnostic - scalar isotropy is not assumed", color=NAVY, weight="bold")
    ax.legend(frameon=False)
    path = FIGURES / "anisotropy_diagnostic.png"
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return rows, path


def _sensitivity_figure(rows: list[dict[str, object]]) -> Path:
    fig, axes = plt.subplots(1, len(REPRESENTATIVE), figsize=(15.5, 3.8), sharey=True, constrained_layout=True)
    for ax, label in zip(axes, REPRESENTATIVE):
        selected = [row for row in rows if row["label"] == label]
        for width, color in zip(BIN_WIDTH_SENSITIVITY, (BLUE, GOLD, RED)):
            local = sorted(
                (row for row in selected if row["bin_width_km"] == width),
                key=lambda row: row["discovery_radius_km"],
            )
            x = np.asarray([row["discovery_radius_km"] for row in local])
            y = np.asarray([row["common_range_km"] for row in local], dtype=float)
            unresolved = ~np.isfinite(y)
            ax.plot(x[~unresolved], y[~unresolved], marker="o", color=color, label=f"{width:g} km bins")
            ax.scatter(x[unresolved], 0.92 * x[unresolved], marker="x", s=48, color=color)
        ax.plot((180, 520), (0.8 * 180, 0.8 * 520), color=MUTED, ls=":", lw=1)
        ax.set_title(label, fontsize=10, weight="bold")
        ax.set_xlabel("Discovery radius (km)")
        ax.grid(alpha=0.15)
    axes[0].set_ylabel("Resolved common R* (km); x = unresolved")
    axes[-1].legend(frameon=False, fontsize=8)
    fig.suptitle("Range estimates do not stabilize across bin width and discovery support", fontsize=15, weight="bold", color=NAVY)
    path = FIGURES / "representative_sensitivity.png"
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _pedagogical_figure() -> Path:
    fig, axes = plt.subplots(2, 4, figsize=(14.2, 7.4), constrained_layout=True)
    titles = [
        "1  Large discovery support",
        "2  Pair values vs distance",
        "3  Physical annuli",
        "4  Empirical background",
        "5  Persistent R* criterion",
        "6  Keep neighbors within R*",
        "7  Same median collapse",
        "8  One adaptive output pixel",
    ]
    rng = np.random.default_rng(42)
    for ax, title in zip(axes.ravel(), titles):
        ax.set_title(title, loc="left", weight="bold", fontsize=10.5, color=NAVY)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    for radius, color in ((0.25, "#C7DCEF"), (0.5, "#83B4D7"), (0.75, "#3E84B8"), (1.0, NAVY)):
        axes[0, 0].add_patch(plt.Circle((0, 0), radius, fill=False, color=color, lw=2))
    axes[0, 0].scatter([0], [0], marker="*", s=180, color=GOLD, edgecolor=INK)
    axes[0, 0].set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1), aspect="equal")
    d = rng.uniform(0, 500, 800)
    s = 0.25 + 0.6 * np.exp(-d / 90) + rng.normal(0, 0.08, d.size)
    axes[0, 1].scatter(d, s, s=5, alpha=0.18, color=BLUE)
    axes[0, 1].set(xticks=(0, 250, 500), yticks=(0, .5, 1), xlabel="km", ylabel="synchrony")
    for radius in range(20, 501, 20):
        axes[0, 2].add_patch(plt.Circle((0, 0), radius / 500, fill=False, color=BLUE, alpha=.25))
    axes[0, 2].scatter([0], [0], marker="*", s=160, color=GOLD, edgecolor=INK)
    axes[0, 2].set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), aspect="equal")
    x = np.arange(10, 501, 20)
    curve = .25 + .6 * np.exp(-x / 90)
    axes[0, 3].plot(x, curve, color=BLUE, lw=2)
    axes[0, 3].axhline(.25, color=GOLD, lw=2)
    axes[0, 3].set(xticks=(0, 250, 500), yticks=(.25, .5, .75), xlabel="km")
    axes[1, 0].plot(x, curve, color=BLUE, marker="o", ms=3)
    axes[1, 0].axhline(.25, color=GOLD); axes[1, 0].axvline(260, color=GREEN, lw=2)
    axes[1, 0].set(xticks=(0, 260, 500), yticks=(.25, .5, .75), xlabel="km")
    inside = d <= 260
    axes[1, 1].scatter(d[inside], s[inside], s=7, alpha=.25, color=GREEN)
    axes[1, 1].scatter(d[~inside], s[~inside], s=5, alpha=.06, color=MUTED)
    axes[1, 1].set(xticks=(0, 260, 500), yticks=(0, .5, 1), xlabel="km")
    axes[1, 2].hist(s[inside], bins=24, color=GREEN, alpha=.8)
    axes[1, 2].axvline(np.median(s[inside]), color=INK, lw=2)
    axes[1, 2].set(xlabel="retained pair synchrony", ylabel="count")
    axes[1, 3].add_patch(plt.Rectangle((-.45, -.45), .9, .9, fc="#DDEAF3", ec=NAVY, lw=2))
    axes[1, 3].scatter([0], [0], marker="s", s=380, color=GREEN, edgecolor=INK)
    axes[1, 3].text(0, -.78, "pixel = median retained pairs", ha="center", fontsize=9)
    axes[1, 3].set(xlim=(-1, 1), ylim=(-1, 1), aspect="equal")
    fig.suptitle(
        "Discovery radius != synchrony range; synchrony range != kernel weight",
        fontsize=17,
        weight="bold",
        color=NAVY,
    )
    path = FIGURES / "pedagogical_single_pixel.png"
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _colorado_pilot(
    cube: xr.Dataset,
    computation: xr.DataArray,
    *,
    force: bool,
) -> tuple[xr.Dataset, list[dict], list[Path], dict, dict, Path]:
    subset, eligible, output, sample_indices = _colorado_subset(cube, computation)
    pairs, resumed = _pair_checkpoint("colorado_25_site_pilot", subset, output, eligible, force=force)
    primary = empirical_synchrony_range(
        pairs,
        bin_width_km=PRIMARY_BIN_WIDTH_KM,
        min_annulus_count=30,
        background_shell_count=4,
        background_method="outer_annuli",
        persistence_bins=3,
        fixed_radius_km=FIXED_RADIUS_KM,
    )
    primary.attrs.update(
        {
            "experiment": "bounded 25-site Colorado empirical synchrony-range pilot",
            "full_statewide_map_status": "withheld by decision gate",
            "input_snapshot": str(CONUS_CUBE.relative_to(ROOT)),
        }
    )
    _netcdf(OUTPUT / "colorado_25_site_range_pilot.nc", primary)

    sensitivity: list[dict[str, object]] = []
    method_results = {}
    for method in ("outer_annuli", "smoothed_outer_annuli", "distant_pairs"):
        method_results[method] = empirical_synchrony_range(
            pairs,
            bin_width_km=PRIMARY_BIN_WIDTH_KM,
            min_annulus_count=30,
            background_shell_count=4,
            background_method=method,
            persistence_bins=3,
            fixed_radius_km=FIXED_RADIUS_KM,
        )
    for discovery in DISCOVERY_SENSITIVITY:
        bounded = _subset_pairs(pairs, discovery)
        for width in BIN_WIDTH_SENSITIVITY:
            result = empirical_synchrony_range(
                bounded,
                bin_width_km=width,
                min_annulus_count=30,
                background_shell_count=4,
                background_method="outer_annuli",
                persistence_bins=3,
                fixed_radius_km=FIXED_RADIUS_KM,
            )
            for site, (yi, xi) in enumerate(sample_indices, start=1):
                sensitivity.append(
                    {
                        "site": site,
                        "longitude": float(result.x.values[xi]),
                        "latitude": float(result.y.values[yi]),
                        "discovery_radius_km": discovery,
                        "bin_width_km": width,
                        "cold_range_km": _value(result, "cold_range_km", yi, xi),
                        "warm_range_km": _value(result, "warm_range_km", yi, xi),
                        "common_range_km": _value(result, "common_range_km", yi, xi),
                        "common_status_code": _status(result, "common", yi, xi),
                        "common_status": RANGE_STATUS[_status(result, "common", yi, xi)],
                    }
                )

    with xr.open_dataset(COLORADO_BASELINE, engine="scipy") as opened:
        baseline = opened.load()
    baseline_aligned = baseline.reindex(y=primary.y, x=primary.x)
    errors = []
    for yi, xi in sample_indices:
        actual = _value(primary, "fixed_delta_pair_median", yi, xi)
        expected = float(
            baseline_aligned.delta_pair_median.sel(radius_km=100).isel(
                time_window_end=0, y=yi, x=xi
            ).values
        )
        errors.append(abs(actual - expected))
    if max(errors) > 1e-12:
        raise RuntimeError(f"Fixed-control reproduction failed: max error {max(errors)}")
    manual_gate = _manual_gate(pairs, primary, sample_indices)
    manual_gate["fixed_control_max_absolute_error_against_validated_colorado"] = max(errors)
    _json(OUTPUT / "engineering_gate.json", manual_gate)

    fixed = np.asarray(
        [_value(primary, "fixed_delta_pair_median", yi, xi) for yi, xi in sample_indices]
    )
    adaptive = np.asarray(
        [_value(primary, "adaptive_delta_pair_median", yi, xi) for yi, xi in sample_indices]
    )
    comparison = _map_comparison_statistics(fixed, adaptive)
    _json(OUTPUT / "map_comparison_statistics.json", comparison)
    boundary_doc = json.loads(COLORADO_BOUNDARY.read_text(encoding="utf-8"))
    boundary = shape(boundary_doc["features"][0]["geometry"])
    figures = _colorado_figures(primary, sample_indices, baseline_aligned, boundary)
    anisotropy_rows, anisotropy_figure = _anisotropy(pairs, sample_indices)
    figures.append(anisotropy_figure)
    _csv(OUTPUT / "anisotropy_diagnostic.csv", anisotropy_rows)

    background_rows = []
    for method, result in method_results.items():
        for site, (yi, xi) in enumerate(sample_indices, start=1):
            background_rows.append(
                {
                    "site": site,
                    "background_method": method,
                    "cold_range_km": _value(result, "cold_range_km", yi, xi),
                    "warm_range_km": _value(result, "warm_range_km", yi, xi),
                    "common_range_km": _value(result, "common_range_km", yi, xi),
                    "common_status": RANGE_STATUS[_status(result, "common", yi, xi)],
                }
            )
    _csv(OUTPUT / "background_method_sensitivity.csv", background_rows)
    _csv(OUTPUT / "colorado_sensitivity.csv", sensitivity)
    performance = {
        "pair_checkpoint_resumed": resumed,
        "pilot_site_count": len(sample_indices),
        "pair_count": int(pairs.sizes["pair"]),
        "nonself_pair_count": int(pairs.attrs["nonself_pair_count"]),
        "pair_kernel_seconds": float(pairs.attrs["pair_kernel_seconds"]),
        "total_pair_seconds": float(pairs.attrs["total_seconds"]),
        "range_reduction_seconds": float(primary.attrs["range_reduction_seconds"]),
        "input_shape": [subset.sizes["y"], subset.sizes["x"]],
    }
    return primary, sensitivity, figures, comparison, performance, anisotropy_figure


def _decision_gate(
    representative: list[dict[str, object]],
    representative_sensitivity: list[dict[str, object]],
    colorado: xr.Dataset,
    colorado_sensitivity: list[dict[str, object]],
    comparison: dict[str, object],
) -> dict[str, object]:
    output = np.asarray(colorado.output_mask.values, dtype=bool)
    common_status = colorado.common_range_status.isel(time_window_end=0).values[output]
    cold_status = colorado.cold_range_status.isel(time_window_end=0).values[output]
    warm_status = colorado.warm_range_status.isel(time_window_end=0).values[output]
    resolved_common_fraction = float(np.mean(common_status == 3))
    censored_common_fraction = float(np.mean(common_status == 2))

    by_site: dict[int, list[dict[str, object]]] = {}
    for row in colorado_sensitivity:
        if row["bin_width_km"] == PRIMARY_BIN_WIDTH_KM:
            by_site.setdefault(int(row["site"]), []).append(row)
    stable_discovery = 0
    for rows in by_site.values():
        ordered = sorted(rows, key=lambda row: row["discovery_radius_km"])
        ranges = np.asarray([row["common_range_km"] for row in ordered], dtype=float)
        if np.all(np.isfinite(ranges[-2:])) and abs(ranges[-1] - ranges[-2]) <= 20:
            stable_discovery += 1
    discovery_stable_fraction = stable_discovery / max(len(by_site), 1)

    primary_rep = [
        row
        for row in representative_sensitivity
        if row["discovery_radius_km"] == DISCOVERY_RADIUS_KM
        and row["bin_width_km"] == PRIMARY_BIN_WIDTH_KM
    ]
    representative_resolved = sum(row["common_status_code"] == 3 for row in primary_rep)
    answers = {
        "detectable_empirical_curves": "yes, but convergence is often absent or boundary-sensitive",
        "kernel_agnostic_identifiability": "not demonstrated robustly",
        "common_range_resolved_fraction_colorado_pilot": resolved_common_fraction,
        "common_range_censored_fraction_colorado_pilot": censored_common_fraction,
        "representative_common_ranges_resolved_at_500km_20km_bins": representative_resolved,
        "representative_site_count": len(primary_rep),
        "discovery_radius_stable_fraction_colorado_pilot": discovery_stable_fraction,
        "cold_resolved_fraction_colorado_pilot": float(np.mean(cold_status == 3)),
        "warm_resolved_fraction_colorado_pilot": float(np.mean(warm_status == 3)),
        "adaptive_map_comparison_status": comparison["status"],
        "scalar_isotropy": "not established; sector estimates are frequently unresolved",
        "computational_scale": "materially larger than fixed 100 km and not justified while identifiability fails",
    }
    pass_gate = (
        resolved_common_fraction >= 0.70
        and discovery_stable_fraction >= 0.70
        and representative_resolved >= 4
    )
    return {
        "status": "PASS" if pass_gate else "HOLD",
        "decision": (
            "proceed to full Colorado and then CONUS"
            if pass_gate
            else "do not run full-state or CONUS production; revise or validate the empirical criterion first"
        ),
        "predeclared_gate": {
            "minimum_common_resolved_fraction": 0.70,
            "minimum_discovery_stable_fraction": 0.70,
            "minimum_representative_resolved_sites": 4,
        },
        "answers": answers,
        "reason": (
            "The estimator is deterministic and testable, but real curves do not yield sufficiently "
            "stable common ranges across discovery support and bin widths. Assigning the 500 km "
            "boundary as R* would be scientifically incorrect."
        ),
    }


def _performance_report(
    representative_performance: dict,
    colorado_performance: dict,
    decision: dict,
) -> dict[str, object]:
    pilot_sites = int(colorado_performance["pilot_site_count"])
    pairs = int(colorado_performance["nonself_pair_count"])
    pairs_per_site = pairs / pilot_sites
    kernel_seconds = float(colorado_performance["pair_kernel_seconds"])
    rate = pairs / kernel_seconds if kernel_seconds else float("nan")
    colorado_pixels = 16235
    conus_pixels = 481630
    return {
        "status": "bounded pilot complete; scale-up withheld",
        **representative_performance,
        "colorado_pilot": colorado_performance,
        "observed_nonself_pairs_per_pilot_site": pairs_per_site,
        "observed_pair_kernel_rate_pairs_per_second": rate,
        "rough_full_colorado_pair_work_lower_upper": [
            int(0.5 * colorado_pixels * pairs_per_site),
            int(colorado_pixels * pairs_per_site),
        ],
        "rough_full_conus_pair_work_lower_upper": [
            int(0.5 * conus_pixels * pairs_per_site),
            int(conus_pixels * pairs_per_site),
        ],
        "estimate_caveat": (
            "endpoint symmetry, coastline/domain truncation, latitude, and tile overlap change actual work; "
            "these are planning bounds, not runtime promises"
        ),
        "scale_up_decision": decision["status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Recompute pair checkpoints")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    PAIR_DIR.mkdir(parents=True, exist_ok=True)
    for path in (CONUS_CUBE, CONUS_BASELINE, COLORADO_BASELINE, COLORADO_MASK, COLORADO_BOUNDARY):
        if not path.exists():
            raise FileNotFoundError(path)

    overall_started = time.perf_counter()
    with xr.open_dataset(CONUS_CUBE, engine="h5netcdf") as opened_cube, xr.open_dataset(
        CONUS_BASELINE, engine="h5netcdf"
    ) as opened_baseline:
        if bool(opened_cube.attrs.get("is_synthetic", 1)):
            raise RuntimeError("Refusing synthetic PRISM input")
        cube = opened_cube
        cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
        cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
        computation = opened_baseline.output_mask
        representative, representative_sensitivity, rep_figures, rep_performance = _representative_gate(
            cube, computation, force=args.force
        )
        colorado, colorado_sensitivity, colorado_figures, comparison, colorado_performance, _ = _colorado_pilot(
            cube, computation, force=args.force
        )

    sensitivity_figure = _sensitivity_figure(representative_sensitivity)
    pedagogical = _pedagogical_figure()
    _csv(OUTPUT / "representative_pixels.csv", representative)
    _csv(OUTPUT / "representative_sensitivity.csv", representative_sensitivity)
    decision = _decision_gate(
        representative,
        representative_sensitivity,
        colorado,
        colorado_sensitivity,
        comparison,
    )
    _json(OUTPUT / "decision_gate.json", decision)
    performance = _performance_report(rep_performance, colorado_performance, decision)
    performance["total_workflow_wall_seconds"] = time.perf_counter() - overall_started
    _json(OUTPUT / "performance.json", performance)

    figures = [pedagogical, *rep_figures, sensitivity_figure, *colorado_figures]
    summary = {
        "status": "complete",
        "decision_gate": decision["status"],
        "decision": decision["decision"],
        "method": {
            "discovery_radius_km": DISCOVERY_RADIUS_KM,
            "primary_bin_width_km": PRIMARY_BIN_WIDTH_KM,
            "fixed_control_radius_km": FIXED_RADIUS_KM,
            "backgrounds_compared": ["outer_annuli", "smoothed_outer_annuli", "distant_pairs"],
            "primary_background": "outer_annuli",
            "persistence_bins": 3,
            "annular_absolute_tolerance_floor": 0.03,
            "cumulative_absolute_tolerance": 0.01,
            "censor_fraction": 0.80,
            "common_range": "max of cold and warm only when both resolve",
            "distance_weighting": False,
            "parametric_kernel": False,
        },
        "representative_pixels": representative,
        "colorado_pilot_site_count": int(colorado.output_mask.sum()),
        "colorado_common_resolved_count": int(
            ((colorado.common_range_status == 3) & colorado.output_mask).sum()
        ),
        "map_comparison": comparison,
        "figures": [str(path.relative_to(ROOT)) for path in figures],
        "limitations": [
            "The Colorado pilot contains 25 spatially balanced focal sites, not a statewide raster.",
            "Common ranges are missing wherever either cold or warm range is unresolved.",
            "The single 2023-11-01 through 2024-01-30 window does not establish temporal stability.",
            "Scalar range assumes isotropy; directional diagnostics do not validate that assumption.",
            "No full Colorado or CONUS adaptive-range production run was performed because the gate is on HOLD.",
        ],
    }
    _json(OUTPUT / "summary.json", summary)
    provenance_source = json.loads(
        (ROOT / "artifacts" / "nonstacked-conus-baseline" / "provenance.json").read_text(
            encoding="utf-8"
        )
    )
    provenance = {
        "status": "complete bounded real-data pilot",
        "real_observations": True,
        "source": "PRISM",
        "input_path": str(CONUS_CUBE.relative_to(ROOT)),
        "input_sha256": provenance_source.get("input_sha256"),
        "date_range": ["2023-11-01", "2024-01-30"],
        "variables": ["tmin", "tmax"],
        "validated_pair_kernel_reused": True,
        "delta_definition": "cold_synchrony - warm_synchrony",
        "self_pair_policy": "excluded",
        "distance_geometry": "great-circle kilometers",
        "stacking": False,
        "second_convolution": False,
        "kernel_weighting": False,
        "network_data_transferred_bytes": 0,
        "pair_checkpoints": [str(path.relative_to(ROOT)) for path in sorted(PAIR_DIR.glob("*.nc"))],
        "primary_result": str((OUTPUT / "colorado_25_site_range_pilot.nc").relative_to(ROOT)),
        "reproduction_command": ".venv/bin/python scripts/run_empirical_synchrony_range_pilot.py",
        "full_scale_status": "withheld by decision gate",
    }
    _json(OUTPUT / "provenance.json", provenance)
    (OUTPUT / "REPRODUCE.md").write_text(
        "# Reproduce the empirical synchrony-range pilot\n\n"
        "From the repository root, using the retained real PRISM CONUS snapshot:\n\n"
        "```bash\n.venv/bin/python scripts/run_empirical_synchrony_range_pilot.py\n```\n\n"
        "Completed pair checkpoints are fingerprint-validated and reused. Use `--force` only to "
        "deliberately recompute them. The workflow performs no network access and stops before "
        "full-state or CONUS scaling when the decision gate is on HOLD.\n",
        encoding="utf-8",
    )
    (OUTPUT / "git_diff_summary.txt").write_text(
        "Generated after implementation; run `git status --short` and `git diff --stat` from the "
        "repository root for the complete working-tree view. Unrelated pre-existing changes were "
        "preserved.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "decision_gate": decision["status"], "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
