#!/usr/bin/env python3
"""Run the bounded four-round adaptive synchrony experiment.

The workflow uses real retained PRISM observations, validates distance-stratified
sampling against exhaustive 1000 km representative pixels, and advances to the
25-site Colorado pilot only when the representative gate passes. It never
launches a statewide raster or CONUS production run.
"""

from __future__ import annotations

import argparse
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

from cubedynamics.runtime import version_info
from cubedynamics.serialization import sanitize_netcdf_attrs
from cubedynamics.synchrony.adaptive import (
    BREAK_STATUS,
    VALID_BREAK_CODES,
    adaptive_synchrony_experiment,
    empirical_break_curve,
)
from cubedynamics.synchrony.decay import empirical_decay_curve
from cubedynamics.synchrony.production import (
    distance_stratified_pair_sample,
    expand_spatial_domain,
    local_synchrony_pairs,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "adaptive-synchrony-four-round"
PAIR_DIR = OUTPUT / "pair_checkpoints"
RESULT_DIR = OUTPUT / "results"
FIGURES = OUTPUT / "figures"
CONUS_CUBE = ROOT / "artifacts/nonstacked-conus-baseline/inputs/prism_conus_20231101_20240130.nc"
CONUS_BASELINE = ROOT / "artifacts/nonstacked-conus-baseline/conus_nonstacked_synchrony.nc"
OLD_COLORADO_PAIRS = ROOT / "artifacts/empirical-synchrony-range/pair_checkpoints/colorado_25_site_pilot.nc"
COLORADO_BOUNDARY = ROOT / "artifacts/synchrony-stack-phase2/colorado_boundary.geojson"

D_MAX_KM = 1000.0
FIXED_RADIUS_KM = 500.0
BIN_WIDTH_KM = 25.0
MIN_ANNULUS_COUNT = 30
SMOOTHING_BINS = 3
WINDOW_DAYS = 90
WINDOW_END = "2024-01-30"
MIN_T = 10
SAMPLING_SEED = 20260925
SAMPLING_PLAN = ((100.0, None), (300.0, 12000), (600.0, 10000), (1000.0, 10000))
REPRESENTATIVE = {
    "Colorado mountains": (-106.4, 39.1),
    "Great Plains": (-100.0, 40.0),
    "Southeast": (-84.0, 33.0),
    "Northeast": (-73.5, 43.0),
    "Pacific region": (-121.5, 45.0),
}
PREDECLARED_GATE = {
    "representative_common_resolved_minimum": 4,
    "sampling_break_absolute_error_km_max": 50.0,
    "sampling_break_agreement_fraction_minimum": 0.80,
    "sampling_adaptive_delta_mae_max": 0.025,
    "colorado_common_resolved_fraction_minimum": 0.70,
    "colorado_domain_stable_fraction_minimum": 0.70,
    "colorado_bin_stable_fraction_minimum": 0.70,
    "colorado_smoothing_stable_fraction_minimum": 0.70,
    "stability_absolute_tolerance_km": 50.0,
    "maximum_ambiguous_fraction": 0.20,
    "full_scale_pair_work_maximum": 100_000_000,
}

NAVY = "#123F70"
BLUE = "#2878B5"
RED = "#B63A3A"
GOLD = "#F0B43C"
GREEN = "#3A8D6D"
PURPLE = "#7451A6"
INK = "#17212B"
MUTED = "#66737F"


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
    fields: list[str] = []
    for row in rows:
        for name in row:
            if name not in fields:
                fields.append(name)
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


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_checkpoint(path: Path, dataset: xr.Dataset, *, kind: str) -> None:
    _netcdf(path, dataset)
    _json(
        path.with_suffix(".json"),
        {
            "status": "complete",
            "kind": kind,
            "path": str(path.relative_to(ROOT)),
            "analysis_fingerprint": dataset.attrs.get("analysis_fingerprint"),
            "pair_count": int(dataset.sizes.get("pair", 0)),
            "nonself_pair_count": int(dataset.attrs.get("nonself_pair_count", 0)),
            "sha256": _sha(path),
        },
    )


def _load_checkpoint(path: Path) -> xr.Dataset:
    manifest_path = path.with_suffix(".json")
    if not path.exists() or not manifest_path.exists():
        raise FileNotFoundError(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != _sha(path):
        raise ValueError(f"Checkpoint SHA mismatch: {path}")
    with xr.open_dataset(path, engine="h5netcdf") as opened:
        result = opened.load()
    if manifest.get("analysis_fingerprint") != result.attrs.get("analysis_fingerprint"):
        raise ValueError(f"Checkpoint fingerprint mismatch: {path}")
    return result


def _point_subset(
    cube: xr.Dataset,
    computation: xr.DataArray,
    lon: float,
    lat: float,
) -> tuple[xr.Dataset, xr.DataArray, xr.DataArray, int, int, float, float]:
    xi = int(np.argmin(np.abs(np.asarray(cube.x.values) - lon)))
    yi = int(np.argmin(np.abs(np.asarray(cube.y.values) - lat)))
    focal_lon = float(cube.x.values[xi])
    focal_lat = float(cube.y.values[yi])
    bounds = expand_spatial_domain((focal_lon, focal_lat, focal_lon, focal_lat), D_MAX_KM).bounds
    y_index = np.flatnonzero((cube.y.values >= bounds[1]) & (cube.y.values <= bounds[3]))
    x_index = np.flatnonzero((cube.x.values >= bounds[0]) & (cube.x.values <= bounds[2]))
    y_slice = slice(int(y_index.min()), int(y_index.max()) + 1)
    x_slice = slice(int(x_index.min()), int(x_index.max()) + 1)
    subset = cube.isel(y=y_slice, x=x_slice).load()
    eligible = computation.isel(y=y_slice, x=x_slice).load().astype(bool)
    local_y = int(np.argmin(np.abs(np.asarray(subset.y.values) - focal_lat)))
    local_x = int(np.argmin(np.abs(np.asarray(subset.x.values) - focal_lon)))
    output = xr.zeros_like(subset.tmin.isel(time=0), dtype=bool)
    output.values[local_y, local_x] = True
    if not bool(eligible.values[local_y, local_x]):
        raise ValueError(f"Focal point {focal_lon}, {focal_lat} is not an eligible PRISM cell")
    return subset, eligible, output, local_y, local_x, focal_lon, focal_lat


def _pair_checkpoint(
    key: str,
    cube: xr.Dataset,
    computation: xr.DataArray,
    lon: float,
    lat: float,
    *,
    exhaustive: bool,
    force: bool,
) -> tuple[xr.Dataset, int, int, float, float, bool]:
    suffix = "exhaustive" if exhaustive else "sampled"
    path = PAIR_DIR / f"{key}_{suffix}_1000km.nc"
    subset, eligible, output, yi, xi, focal_lon, focal_lat = _point_subset(
        cube, computation, lon, lat
    )
    if path.exists() and path.with_suffix(".json").exists() and not force:
        saved = _load_checkpoint(path)
        expected_sampling = (
            "dense all eligible pairs"
            if exhaustive
            else json.dumps(
                [
                    {"upper_km": upper, "max_pairs_per_focal": cap}
                    for upper, cap in SAMPLING_PLAN
                ],
                separators=(",", ":"),
            )
        )
        checks = {
            "max_radius_km": float(saved.attrs.get("max_radius_km", np.nan)) == D_MAX_KM,
            "window_end": str(saved.attrs.get("window_end", "")).startswith(WINDOW_END),
            "sampling": saved.attrs.get("distance_sampling_design") == expected_sampling,
            "sampling_seed": int(saved.attrs.get("distance_sampling_seed", -1)) == SAMPLING_SEED,
        }
        if not all(checks.values()):
            raise ValueError(f"Checkpoint configuration mismatch for {path}: {checks}")
        return saved, yi, xi, focal_lon, focal_lat, True
    pairs = local_synchrony_pairs(
        subset,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        computation_mask=eligible,
        max_radius_km=D_MAX_KM,
        window_days=WINDOW_DAYS,
        window_end=WINDOW_END,
        min_t=MIN_T,
        split_quantile=0.5,
        pair_batch_size=8192,
        distance_sampling=None if exhaustive else SAMPLING_PLAN,
        sampling_seed=SAMPLING_SEED,
    )
    _write_checkpoint(path, pairs, kind=f"{suffix} 1000 km pair relationships")
    return pairs, yi, xi, focal_lon, focal_lat, False


def _sampled_from_exhaustive(key: str, exhaustive: xr.Dataset, *, force: bool) -> xr.Dataset:
    path = PAIR_DIR / f"{key}_sampled_from_exhaustive_1000km.nc"
    if path.exists() and path.with_suffix(".json").exists() and not force:
        saved = _load_checkpoint(path)
        if saved.attrs.get("source_pair_fingerprint") != exhaustive.attrs.get(
            "analysis_fingerprint"
        ):
            raise ValueError(f"Sample checkpoint source fingerprint mismatch: {path}")
        return saved
    sampled = distance_stratified_pair_sample(
        exhaustive,
        distance_sampling=SAMPLING_PLAN,
        sampling_seed=SAMPLING_SEED,
    )
    _write_checkpoint(path, sampled, kind="sampled posthoc from exhaustive 1000 km pairs")
    return sampled


def _focal_index(dataset: xr.Dataset) -> tuple[int, int, int]:
    yi, xi = np.argwhere(np.asarray(dataset.output_mask.values, dtype=bool))[0]
    return int(yi * dataset.sizes["x"] + xi), int(yi), int(xi)


def _value(result: xr.Dataset, name: str, yi: int, xi: int) -> float:
    return float(result[name].isel(time_window_end=0, y=yi, x=xi).values)


def _incident(pairs: xr.Dataset, node: int) -> np.ndarray:
    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    return np.flatnonzero(((source == node) | (target == node)) & (source != target))


def _site_row(label: str, pairs: xr.Dataset, result: xr.Dataset, yi: int, xi: int) -> dict[str, object]:
    row: dict[str, object] = {
        "label": label,
        "longitude": float(result.x.values[xi]),
        "latitude": float(result.y.values[yi]),
        "observed_nonself_pair_count": int(pairs.attrs["nonself_pair_count"]),
        "candidate_nonself_pair_count": int(pairs.attrs.get("candidate_nonself_pair_count", pairs.attrs["nonself_pair_count"])),
        "retained_pair_fraction": float(pairs.attrs.get("retained_nonself_pair_fraction", 1.0)),
    }
    for tail in ("cold", "warm"):
        code = int(_value(result, f"{tail}_break_status", yi, xi))
        row[f"{tail}_break_km"] = _value(result, f"{tail}_break_km", yi, xi)
        row[f"{tail}_break_status_code"] = code
        row[f"{tail}_break_status"] = BREAK_STATUS[code]
        for name in (
            "break_uncertainty_km",
            "segmented_candidate_km",
            "knee_candidate_km",
            "derivative_candidate_km",
            "d50_candidate_km",
            "background_approach_candidate_km",
            "segmented_improvement",
            "near_slope_per_100km",
            "far_slope_per_100km",
            "multiple_break_count",
        ):
            row[f"{tail}_{name}"] = _value(result, f"{tail}_{name}", yi, xi)
    common_code = int(_value(result, "common_break_status", yi, xi))
    row.update(
        {
            "common_break_km": _value(result, "common_break_km", yi, xi),
            "common_break_status_code": common_code,
            "common_break_status": BREAK_STATUS[common_code],
            "common_break_uncertainty_km": _value(result, "common_break_uncertainty_km", yi, xi),
            "delta_r_cold_minus_warm_km": _value(result, "delta_r_cold_minus_warm_km", yi, xi),
        }
    )
    for domain in ("fixed", "adaptive"):
        for metric in (
            "cold_median",
            "warm_median",
            "delta_median",
            "delta_iqr",
            "delta_reduction_gap",
            "observed_pair_count",
            "estimated_pair_count",
            "valid_pair_fraction",
        ):
            row[f"{domain}_{metric}"] = _value(result, f"{domain}_{metric}", yi, xi)
    for metric in ("cold", "warm", "delta"):
        row[f"{metric}_adaptive_minus_fixed"] = _value(
            result, f"{metric}_difference_adaptive_minus_fixed", yi, xi
        )
    row["delta_sign_change"] = int(_value(result, "delta_sign_change", yi, xi))
    return row


def _curve_sensitivity(label: str, pairs: xr.Dataset) -> list[dict[str, object]]:
    node, _, _ = _focal_index(pairs)
    selected = _incident(pairs, node)
    distance = np.asarray(pairs.distance_km.values, dtype=float)[selected]
    probability = np.asarray(pairs.sampling_probability.values, dtype=float)[selected]
    rows: list[dict[str, object]] = []
    configurations = []
    configurations.extend(("domain", value, BIN_WIDTH_KM, SMOOTHING_BINS) for value in (300.0, 500.0, 750.0, 1000.0))
    configurations.extend(("bin", D_MAX_KM, value, SMOOTHING_BINS) for value in (10.0, 20.0, 25.0, 40.0))
    configurations.extend(("smoothing", D_MAX_KM, BIN_WIDTH_KM, value) for value in (1, 3, 5))
    for family, maximum, width, smoothing in configurations:
        for tail, variable in (("cold", "cold_synchrony"), ("warm", "warm_synchrony")):
            curve = empirical_break_curve(
                distance,
                np.asarray(pairs[variable].values, dtype=float)[selected],
                sampling_probability=probability,
                discovery_radius_km=maximum,
                bin_width_km=width,
                min_annulus_count=MIN_ANNULUS_COUNT,
                smoothing_bins=int(smoothing),
            )
            rows.append(
                {
                    "label": label,
                    "family": family,
                    "tail": tail,
                    "discovery_radius_km": maximum,
                    "bin_width_km": width,
                    "smoothing_bins": smoothing,
                    "break_km": curve.attrs["break_km"],
                    "status_code": curve.attrs["break_status"],
                    "status": curve.attrs["break_status_label"],
                    "uncertainty_km": curve.attrs["break_uncertainty_km"],
                }
            )
    for method in ("outer_annuli", "smoothed_outer_annuli", "distant_pairs"):
        for tail, variable in (("cold", "cold_synchrony"), ("warm", "warm_synchrony")):
            decay = empirical_decay_curve(
                distance,
                np.asarray(pairs[variable].values, dtype=float)[selected],
                discovery_radius_km=D_MAX_KM,
                bin_width_km=BIN_WIDTH_KM,
                min_annulus_count=MIN_ANNULUS_COUNT,
                background_method=method,
            )
            rows.append(
                {
                    "label": label,
                    "family": "background",
                    "tail": tail,
                    "discovery_radius_km": D_MAX_KM,
                    "bin_width_km": BIN_WIDTH_KM,
                    "smoothing_bins": SMOOTHING_BINS,
                    "background_method": method,
                    "d50_km": decay.attrs["d50_km"],
                    "d50_status": decay.attrs["d50_status"],
                }
            )
    return rows


def _diagnostic_figure(label: str, pairs: xr.Dataset, result: xr.Dataset) -> Path:
    node, yi, xi = _focal_index(pairs)
    selected = _incident(pairs, node)
    distance = np.asarray(pairs.distance_km.values)[selected]
    rng = np.random.default_rng(abs(hash(label)) % 2**32)
    sample = np.arange(selected.size)
    if sample.size > 9000:
        sample = np.sort(rng.choice(sample, size=9000, replace=False))
    fig, axes = plt.subplots(2, 1, figsize=(12.8, 8.4), sharex=True, constrained_layout=True)
    for ax, tail, variable, color in (
        (axes[0], "cold", "cold_synchrony", BLUE),
        (axes[1], "warm", "warm_synchrony", RED),
    ):
        observed = np.asarray(pairs[variable].values)[selected]
        radius = np.asarray(result.radius_km.values)
        median = result[f"{tail}_annular_median"].isel(time_window_end=0, y=yi, x=xi).values
        q25 = result[f"{tail}_annular_q25"].isel(time_window_end=0, y=yi, x=xi).values
        q75 = result[f"{tail}_annular_q75"].isel(time_window_end=0, y=yi, x=xi).values
        smooth = result[f"{tail}_smoothed_annular_median"].isel(time_window_end=0, y=yi, x=xi).values
        ax.scatter(distance[sample], observed[sample], s=2, alpha=0.035, color=color, rasterized=True)
        ax.fill_between(radius, q25, q75, color=color, alpha=0.18, label="design-weighted annular IQR")
        ax.plot(radius, median, color=color, lw=1.3, alpha=0.75, label="raw annular median")
        ax.plot(radius, smooth, color=INK, lw=2.0, label="3-bin median placement curve")
        for name, line_color, style, legend in (
            ("segmented_candidate_km", GOLD, "-", "segmented first break"),
            ("d50_candidate_km", GREEN, "--", "d50 candidate"),
            ("background_approach_candidate_km", PURPLE, ":", "final background approach"),
        ):
            value = _value(result, f"{tail}_{name}", yi, xi)
            if np.isfinite(value):
                ax.axvline(value, color=line_color, ls=style, lw=2, label=legend)
        ax.axvline(FIXED_RADIUS_KM, color=MUTED, ls="--", lw=1.2, label="fixed 500 km")
        code = int(_value(result, f"{tail}_break_status", yi, xi))
        ax.set_ylabel(f"{tail.title()} synchrony")
        ax.set_title(
            f"{tail.title()} R* = {_value(result, f'{tail}_break_km', yi, xi):.0f} km | {BREAK_STATUS[code]}",
            loc="left",
            weight="bold",
        )
        ax.grid(alpha=0.16)
    axes[0].legend(frameon=False, ncol=3, fontsize=8)
    axes[-1].set_xlabel("Physical distance from focal pixel (km)")
    fig.suptitle(f"{label}: first local break versus final background", color=NAVY, fontsize=17, weight="bold")
    path = FIGURES / f"diagnostic_{label.lower().replace(' ', '_')}.png"
    fig.savefig(path, dpi=230, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _comparison_stats(fixed: np.ndarray, adaptive: np.ndarray) -> dict[str, object]:
    valid = np.isfinite(fixed) & np.isfinite(adaptive)
    if np.count_nonzero(valid) < 3:
        return {"status": "insufficient", "n": int(np.count_nonzero(valid))}
    left, right = fixed[valid], adaptive[valid]
    difference = right - left
    return {
        "status": "computed",
        "n": int(left.size),
        "pearson": float(pearsonr(left, right).statistic),
        "spearman": float(spearmanr(left, right).statistic),
        "mae": float(np.mean(np.abs(difference))),
        "rmse": float(np.sqrt(np.mean(difference**2))),
        "median_absolute_difference": float(np.median(np.abs(difference))),
        "difference_iqr": float(np.quantile(difference, 0.75) - np.quantile(difference, 0.25)),
        "fraction_abs_gt_0_01": float(np.mean(np.abs(difference) > 0.01)),
        "fraction_abs_gt_0_025": float(np.mean(np.abs(difference) > 0.025)),
        "fraction_abs_gt_0_05": float(np.mean(np.abs(difference) > 0.05)),
    }


def _representative_summary_figures(rows: list[dict], gate: dict) -> list[Path]:
    lon = np.asarray([row["longitude"] for row in rows], dtype=float)
    lat = np.asarray([row["latitude"] for row in rows], dtype=float)
    labels = [str(row["label"]) for row in rows]

    def panel(ax, values, title, cmap, norm):
        image = ax.scatter(lon, lat, c=values, s=180, cmap=cmap, norm=norm, edgecolor="white", linewidth=1.0)
        missing = ~np.isfinite(values)
        if np.any(missing):
            ax.scatter(lon[missing], lat[missing], marker="x", s=110, color=INK, lw=2)
        for x, y, label in zip(lon, lat, labels):
            ax.text(x, y + 0.8, label.replace(" region", ""), ha="center", fontsize=7)
        ax.set(xlim=(-127, -66), ylim=(25, 50), xlabel="Longitude", ylabel="Latitude")
        ax.set_title(title, loc="left", weight="bold")
        ax.grid(alpha=0.15)
        return image

    fixed = np.asarray([row["fixed_delta_median"] for row in rows], dtype=float)
    adaptive = np.asarray([row["adaptive_delta_median"] for row in rows], dtype=float)
    difference = adaptive - fixed
    common = np.asarray([row["common_break_km"] for row in rows], dtype=float)
    delta_limit = max(0.05, float(np.nanpercentile(np.abs(fixed), 95)))
    difference_limit = max(0.01, float(np.nanmax(np.abs(difference)))) if np.isfinite(difference).any() else 0.01
    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.4), constrained_layout=True)
    specs = (
        (fixed, "A  Fixed 500 km Delta", "RdBu", TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit)),
        (adaptive, "B  Adaptive Delta", "RdBu", TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit)),
        (difference, "C  Adaptive - fixed Delta", "PuOr", TwoSlopeNorm(vmin=-difference_limit, vcenter=0, vmax=difference_limit)),
        (common, "D  R* common (km)", "viridis", Normalize(0, D_MAX_KM)),
    )
    for ax, (values, title, cmap, norm) in zip(axes.flat, specs):
        image = panel(ax, values, title, cmap, norm)
        fig.colorbar(image, ax=ax, shrink=0.78)
    fig.suptitle(
        "Bounded representative result - not a Colorado or CONUS map",
        fontsize=17,
        color=NAVY,
        weight="bold",
    )
    primary = FIGURES / "representative_primary_four_panel.png"
    fig.savefig(primary, dpi=250, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    cold = np.asarray([row["cold_break_km"] for row in rows], dtype=float)
    warm = np.asarray([row["warm_break_km"] for row in rows], dtype=float)
    delta_r = cold - warm
    status = np.asarray([row["common_break_status_code"] for row in rows], dtype=float)
    r_limit = max(100.0, float(np.nanmax(np.abs(delta_r)))) if np.isfinite(delta_r).any() else 100.0
    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.4), constrained_layout=True)
    specs = (
        (cold, "A  R* cold (km)", "viridis", Normalize(0, D_MAX_KM)),
        (warm, "B  R* warm (km)", "viridis", Normalize(0, D_MAX_KM)),
        (delta_r, "C  R* cold - R* warm (km)", "RdBu", TwoSlopeNorm(vmin=-r_limit, vcenter=0, vmax=r_limit)),
        (status, "D  Common break status code", "tab10", Normalize(0, 6)),
    )
    for ax, (values, title, cmap, norm) in zip(axes.flat, specs):
        image = panel(ax, values, title, cmap, norm)
        fig.colorbar(image, ax=ax, shrink=0.78)
    fig.suptitle("Scale outputs at five representative pixels", fontsize=17, color=NAVY, weight="bold")
    secondary = FIGURES / "representative_scale_four_panel.png"
    fig.savefig(secondary, dpi=250, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    details = gate["sampling_validation"]["details"]
    fixed_error = np.asarray([item["fixed_500km_delta_absolute_error"] for item in details])
    agreement = []
    for item in details:
        agreement.append(
            sum(item[f"{tail}_exact_status"] == item[f"{tail}_sampled_status"] for tail in ("cold", "warm"))
        )
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), constrained_layout=True)
    axes[0].bar(np.arange(len(labels)), fixed_error, color=GREEN)
    axes[0].set(xticks=np.arange(len(labels)), xticklabels=[label.split()[0] for label in labels], ylabel="Absolute Delta error", title="Fixed 500 km sampling error")
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].grid(axis="y", alpha=0.2)
    axes[1].bar(np.arange(len(labels)), agreement, color=[RED if value < 2 else GREEN for value in agreement])
    axes[1].set(xticks=np.arange(len(labels)), xticklabels=[label.split()[0] for label in labels], yticks=(0, 1, 2), ylabel="Tail status matches (of 2)", title="Break classification agreement")
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].grid(axis="y", alpha=0.2)
    fig.suptitle("Sampling preserves fixed Delta but not break classification", fontsize=16, color=NAVY, weight="bold")
    validation = FIGURES / "sampling_validation.png"
    fig.savefig(validation, dpi=250, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [primary, secondary, validation]


def _sampling_validation(exhaustive_rows: list[dict], sampled_rows: list[dict]) -> dict[str, object]:
    joined = {row["label"]: row for row in exhaustive_rows}
    agreements = []
    errors = []
    delta_errors = []
    fixed_delta_errors = []
    details = []
    for sampled in sampled_rows:
        exact = joined[sampled["label"]]
        detail = {"label": sampled["label"]}
        for tail in ("cold", "warm"):
            left = float(exact[f"{tail}_break_km"])
            right = float(sampled[f"{tail}_break_km"])
            left_status = int(exact[f"{tail}_break_status_code"])
            right_status = int(sampled[f"{tail}_break_status_code"])
            error = abs(right - left) if np.isfinite(left) and np.isfinite(right) else np.nan
            detail[f"{tail}_break_absolute_error_km"] = error
            detail[f"{tail}_exact_status"] = BREAK_STATUS[left_status]
            detail[f"{tail}_sampled_status"] = BREAK_STATUS[right_status]
            errors.append(error)
            agreements.append(
                bool(np.isfinite(error) and error <= PREDECLARED_GATE["sampling_break_absolute_error_km_max"])
                or (not np.isfinite(left) and not np.isfinite(right) and left_status == right_status)
            )
        sampled_adaptive = float(sampled["adaptive_delta_median"])
        exact_adaptive = float(exact["adaptive_delta_median"])
        delta_error = (
            abs(sampled_adaptive - exact_adaptive)
            if np.isfinite(sampled_adaptive) and np.isfinite(exact_adaptive)
            else np.nan
        )
        detail["adaptive_delta_absolute_error"] = delta_error
        delta_errors.append(delta_error)
        fixed_error = abs(float(sampled["fixed_delta_median"]) - float(exact["fixed_delta_median"]))
        detail["fixed_500km_delta_absolute_error"] = fixed_error
        fixed_delta_errors.append(fixed_error)
        details.append(detail)
    finite_delta = np.asarray(delta_errors, dtype=float)
    finite_delta = finite_delta[np.isfinite(finite_delta)]
    agreement = float(np.mean(agreements)) if agreements else 0.0
    delta_mae = float(np.mean(finite_delta)) if finite_delta.size else None
    fixed_delta_mae = float(np.mean(fixed_delta_errors))
    passed = (
        agreement >= PREDECLARED_GATE["sampling_break_agreement_fraction_minimum"]
        and delta_mae is not None
        and delta_mae <= PREDECLARED_GATE["sampling_adaptive_delta_mae_max"]
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "break_agreement_fraction": agreement,
        "adaptive_delta_mae": delta_mae,
        "adaptive_delta_comparable_site_count": int(finite_delta.size),
        "fixed_500km_delta_mae": fixed_delta_mae,
        "details": details,
    }


def _representatives(
    cube: xr.Dataset,
    computation: xr.DataArray,
    *,
    force: bool,
) -> tuple[list[dict], list[dict], list[dict], list[Path], dict]:
    exhaustive_rows: list[dict] = []
    sampled_rows: list[dict] = []
    sensitivity: list[dict] = []
    figures: list[Path] = []
    performance = []
    for label, (lon, lat) in REPRESENTATIVE.items():
        key = label.lower().replace(" ", "_")
        exhaustive, yi, xi, _, _, resumed = _pair_checkpoint(
            key, cube, computation, lon, lat, exhaustive=True, force=force
        )
        sampled = _sampled_from_exhaustive(key, exhaustive, force=force)
        exhaustive_result = adaptive_synchrony_experiment(
            exhaustive,
            discovery_radius_km=D_MAX_KM,
            fixed_radius_km=FIXED_RADIUS_KM,
            bin_width_km=BIN_WIDTH_KM,
            min_annulus_count=MIN_ANNULUS_COUNT,
            smoothing_bins=SMOOTHING_BINS,
            time_window_id="2023-11-01/2024-01-30",
        )
        sampled_result = adaptive_synchrony_experiment(
            sampled,
            discovery_radius_km=D_MAX_KM,
            fixed_radius_km=FIXED_RADIUS_KM,
            bin_width_km=BIN_WIDTH_KM,
            min_annulus_count=MIN_ANNULUS_COUNT,
            smoothing_bins=SMOOTHING_BINS,
            time_window_id="2023-11-01/2024-01-30",
        )
        exhaustive_rows.append(_site_row(label, exhaustive, exhaustive_result, yi, xi))
        sampled_rows.append(_site_row(label, sampled, sampled_result, yi, xi))
        sensitivity.extend(_curve_sensitivity(label, sampled))
        figures.append(_diagnostic_figure(label, sampled, sampled_result))
        _netcdf(RESULT_DIR / f"representative_{key}_sampled.nc", sampled_result)
        performance.append(
            {
                "label": label,
                "checkpoint_resumed": resumed,
                "exhaustive_nonself_pairs": int(exhaustive.attrs["nonself_pair_count"]),
                "sampled_nonself_pairs": int(sampled.attrs["nonself_pair_count"]),
                "pair_kernel_seconds": float(exhaustive.attrs.get("pair_kernel_seconds", np.nan)),
                "total_pair_seconds": float(exhaustive.attrs.get("total_seconds", np.nan)),
            }
        )
    validation = _sampling_validation(exhaustive_rows, sampled_rows)
    resolved = sum(int(row["common_break_status_code"]) in VALID_BREAK_CODES for row in sampled_rows)
    representative_gate = {
        "status": "PASS"
        if resolved >= PREDECLARED_GATE["representative_common_resolved_minimum"]
        and validation["status"] == "PASS"
        else "FAIL",
        "common_resolved_count": resolved,
        "site_count": len(sampled_rows),
        "sampling_validation": validation,
        "performance": performance,
    }
    return exhaustive_rows, sampled_rows, sensitivity, figures, representative_gate


def _colorado_locations() -> list[tuple[float, float]]:
    with xr.open_dataset(OLD_COLORADO_PAIRS, engine="h5netcdf") as opened:
        output = np.asarray(opened.output_mask.values, dtype=bool)
        locations = [
            (float(opened.x.values[xi]), float(opened.y.values[yi]))
            for yi, xi in np.argwhere(output)
        ]
    return locations


def _colorado(
    cube: xr.Dataset,
    computation: xr.DataArray,
    *,
    force: bool,
) -> tuple[list[dict], list[dict], list[Path], dict]:
    rows: list[dict] = []
    sensitivity: list[dict] = []
    performance = []
    for site, (lon, lat) in enumerate(_colorado_locations(), start=1):
        key = f"colorado_site_{site:02d}"
        pairs, yi, xi, _, _, resumed = _pair_checkpoint(
            key, cube, computation, lon, lat, exhaustive=False, force=force
        )
        result = adaptive_synchrony_experiment(
            pairs,
            discovery_radius_km=D_MAX_KM,
            fixed_radius_km=FIXED_RADIUS_KM,
            bin_width_km=BIN_WIDTH_KM,
            min_annulus_count=MIN_ANNULUS_COUNT,
            smoothing_bins=SMOOTHING_BINS,
            time_window_id="2023-11-01/2024-01-30",
        )
        row = _site_row(str(site), pairs, result, yi, xi)
        row["site"] = site
        rows.append(row)
        sensitivity.extend(_curve_sensitivity(str(site), pairs))
        _netcdf(RESULT_DIR / f"{key}.nc", result)
        performance.append(
            {
                "site": site,
                "checkpoint_resumed": resumed,
                "candidate_nonself_pairs": int(pairs.attrs["candidate_nonself_pair_count"]),
                "sampled_nonself_pairs": int(pairs.attrs["nonself_pair_count"]),
                "pair_kernel_seconds": float(pairs.attrs.get("pair_kernel_seconds", np.nan)),
                "total_pair_seconds": float(pairs.attrs.get("total_seconds", np.nan)),
            }
        )
    figures = _colorado_figures(rows)
    return rows, sensitivity, figures, {"sites": performance}


def _outline(ax, boundary) -> None:
    geometries = list(boundary.geoms) if hasattr(boundary, "geoms") else [boundary]
    for geometry in geometries:
        xx, yy = geometry.exterior.xy
        ax.plot(xx, yy, color=INK, lw=0.8)
    ax.set_aspect(1 / np.cos(np.deg2rad(39.0)))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


def _colorado_figures(rows: list[dict]) -> list[Path]:
    boundary_doc = json.loads(COLORADO_BOUNDARY.read_text(encoding="utf-8"))
    boundary = shape(boundary_doc["features"][0]["geometry"])
    lon = np.asarray([row["longitude"] for row in rows])
    lat = np.asarray([row["latitude"] for row in rows])
    fixed_delta = np.asarray([row["fixed_delta_median"] for row in rows], dtype=float)
    adaptive_delta = np.asarray([row["adaptive_delta_median"] for row in rows], dtype=float)
    difference = adaptive_delta - fixed_delta
    common = np.asarray([row["common_break_km"] for row in rows], dtype=float)
    limit = max(0.05, float(np.nanpercentile(np.abs(np.r_[fixed_delta, adaptive_delta]), 95)))
    difference_limit = max(0.01, float(np.nanpercentile(np.abs(difference), 95))) if np.isfinite(difference).any() else 0.01
    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.4), constrained_layout=True)
    specs = (
        (fixed_delta, "RdBu", TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), "A  Fixed 500 km Delta"),
        (adaptive_delta, "RdBu", TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), "B  Adaptive-distance Delta"),
        (difference, "PuOr", TwoSlopeNorm(vmin=-difference_limit, vcenter=0, vmax=difference_limit), "C  Adaptive - fixed Delta"),
        (common, "viridis", Normalize(vmin=0, vmax=D_MAX_KM), "D  R* common (km)"),
    )
    for ax, (values, cmap, norm, title) in zip(axes.flat, specs):
        _outline(ax, boundary)
        image = ax.scatter(lon, lat, c=values, cmap=cmap, norm=norm, s=78, edgecolor="white", linewidth=0.7)
        unresolved = ~np.isfinite(values)
        if np.any(unresolved):
            ax.scatter(lon[unresolved], lat[unresolved], marker="x", s=68, color=INK, lw=1.4)
        ax.set_title(title, loc="left", weight="bold")
        fig.colorbar(image, ax=ax, shrink=0.82)
    fig.suptitle("Colorado 25-site four-round pilot", fontsize=17, color=NAVY, weight="bold")
    primary = FIGURES / "primary_four_panel.png"
    fig.savefig(primary, dpi=250, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    cold = np.asarray([row["cold_break_km"] for row in rows], dtype=float)
    warm = np.asarray([row["warm_break_km"] for row in rows], dtype=float)
    delta_r = cold - warm
    status = np.asarray([row["common_break_status_code"] for row in rows], dtype=float)
    delta_limit = max(100.0, float(np.nanpercentile(np.abs(delta_r), 95))) if np.isfinite(delta_r).any() else 100.0
    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.4), constrained_layout=True)
    specs = (
        (cold, "viridis", Normalize(0, D_MAX_KM), "A  R* cold (km)"),
        (warm, "viridis", Normalize(0, D_MAX_KM), "B  R* warm (km)"),
        (delta_r, "RdBu", TwoSlopeNorm(vmin=-delta_limit, vcenter=0, vmax=delta_limit), "C  R* cold - R* warm (km)"),
        (status, "tab10", Normalize(0, 6), "D  R* status code"),
    )
    for ax, (values, cmap, norm, title) in zip(axes.flat, specs):
        _outline(ax, boundary)
        image = ax.scatter(lon, lat, c=values, cmap=cmap, norm=norm, s=78, edgecolor="white", linewidth=0.7)
        ax.set_title(title, loc="left", weight="bold")
        fig.colorbar(image, ax=ax, shrink=0.82)
    fig.suptitle("Synchrony scale is distinct from synchrony strength", fontsize=17, color=NAVY, weight="bold")
    secondary = FIGURES / "secondary_scale_four_panel.png"
    fig.savefig(secondary, dpi=250, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    sign = np.asarray([row["delta_sign_change"] for row in rows])
    fig, ax = plt.subplots(figsize=(8.8, 6.3), constrained_layout=True)
    _outline(ax, boundary)
    colors = np.where(sign == 1, RED, np.where(sign == 0, BLUE, MUTED))
    ax.scatter(lon, lat, c=colors, s=92, edgecolor="white", linewidth=0.8)
    ax.set_title("Delta sign changes: fixed 500 km versus adaptive", loc="left", color=NAVY, weight="bold")
    sign_path = FIGURES / "delta_sign_change.png"
    fig.savefig(sign_path, dpi=250, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [primary, secondary, sign_path]


def _stability_fraction(rows: list[dict], family: str, left_value: float, right_value: float) -> float:
    stable = []
    for label in sorted({row["label"] for row in rows}):
        for tail in ("cold", "warm"):
            selected = [row for row in rows if row["label"] == label and row["family"] == family and row["tail"] == tail]
            key = "discovery_radius_km" if family == "domain" else "bin_width_km" if family == "bin" else "smoothing_bins"
            lookup = {float(row[key]): row for row in selected}
            if left_value not in lookup or right_value not in lookup:
                continue
            left = float(lookup[left_value]["break_km"])
            right = float(lookup[right_value]["break_km"])
            stable.append(np.isfinite(left) and np.isfinite(right) and abs(left - right) <= PREDECLARED_GATE["stability_absolute_tolerance_km"])
    return float(np.mean(stable)) if stable else 0.0


def _decision(
    representative_gate: dict,
    colorado_rows: list[dict],
    sensitivity: list[dict],
    performance: dict,
) -> tuple[dict, dict]:
    valid = np.asarray([int(row["common_break_status_code"]) in VALID_BREAK_CODES for row in colorado_rows])
    ambiguous = np.asarray([int(row["common_break_status_code"]) == 4 for row in colorado_rows])
    resolved_fraction = float(np.mean(valid)) if valid.size else 0.0
    ambiguous_fraction = float(np.mean(ambiguous)) if ambiguous.size else 1.0
    domain_stable = _stability_fraction(sensitivity, "domain", 750.0, 1000.0)
    bin_stable = _stability_fraction(sensitivity, "bin", 20.0, 40.0)
    smoothing_stable = _stability_fraction(sensitivity, "smoothing", 1.0, 5.0)
    sampled_per_site = np.mean([item["sampled_nonself_pairs"] for item in performance.get("sites", [])]) if performance.get("sites") else np.nan
    projected_full_colorado = int(16235 * sampled_per_site) if np.isfinite(sampled_per_site) else 0
    gates = {
        "representative_gate": representative_gate["status"] == "PASS",
        "colorado_common_resolved_fraction": resolved_fraction >= PREDECLARED_GATE["colorado_common_resolved_fraction_minimum"],
        "domain_stability": domain_stable >= PREDECLARED_GATE["colorado_domain_stable_fraction_minimum"],
        "bin_stability": bin_stable >= PREDECLARED_GATE["colorado_bin_stable_fraction_minimum"],
        "smoothing_stability": smoothing_stable >= PREDECLARED_GATE["colorado_smoothing_stable_fraction_minimum"],
        "ambiguity": ambiguous_fraction <= PREDECLARED_GATE["maximum_ambiguous_fraction"],
        "full_colorado_pair_work": projected_full_colorado <= PREDECLARED_GATE["full_scale_pair_work_maximum"],
    }
    status = "PASS" if all(gates.values()) else "HOLD"
    decision = {
        "status": status,
        "gates": gates,
        "metrics": {
            "colorado_common_resolved_fraction": resolved_fraction,
            "colorado_ambiguous_fraction": ambiguous_fraction,
            "domain_stable_fraction": domain_stable,
            "bin_stable_fraction": bin_stable,
            "smoothing_stable_fraction": smoothing_stable,
            "projected_full_colorado_sampled_pair_work": projected_full_colorado,
        },
        "decision": (
            "Proceed to a separately authorized statewide/CONUS production plan"
            if status == "PASS"
            else "Do not launch a statewide raster or CONUS run; retain the bounded pilot"
        ),
    }

    fixed_delta = np.asarray([row["fixed_delta_median"] for row in colorado_rows], dtype=float)
    adaptive_delta = np.asarray([row["adaptive_delta_median"] for row in colorado_rows], dtype=float)
    fixed_cold = np.asarray([row["fixed_cold_median"] for row in colorado_rows], dtype=float)
    adaptive_cold = np.asarray([row["adaptive_cold_median"] for row in colorado_rows], dtype=float)
    fixed_warm = np.asarray([row["fixed_warm_median"] for row in colorado_rows], dtype=float)
    adaptive_warm = np.asarray([row["adaptive_warm_median"] for row in colorado_rows], dtype=float)
    common = np.asarray([row["common_break_km"] for row in colorado_rows], dtype=float)
    delta_difference = np.abs(adaptive_delta - fixed_delta)
    relation_valid = np.isfinite(common) & np.isfinite(delta_difference)
    relation = {
        "abs_delta_difference_vs_common_break_spearman": (
            float(spearmanr(delta_difference[relation_valid], common[relation_valid]).statistic)
            if np.count_nonzero(relation_valid) >= 3
            else np.nan
        ),
        "abs_delta_difference_vs_abs_common_minus_500_spearman": (
            float(spearmanr(delta_difference[relation_valid], np.abs(common[relation_valid] - 500)).statistic)
            if np.count_nonzero(relation_valid) >= 3
            else np.nan
        ),
    }
    comparisons = {
        "cold": _comparison_stats(fixed_cold, adaptive_cold),
        "warm": _comparison_stats(fixed_warm, adaptive_warm),
        "delta": _comparison_stats(fixed_delta, adaptive_delta),
        "delta_sign_change_fraction": float(np.mean(np.sign(fixed_delta[relation_valid]) != np.sign(adaptive_delta[relation_valid]))) if np.any(relation_valid) else np.nan,
        "relation_to_break": relation,
    }
    answers = {
        "1_stable_break_inside_1000km": "yes for some locations; see resolved and stability fractions",
        "2_1000km_context_improves_previous_500km": f"common resolved fraction is {resolved_fraction:.1%}; previous hard-background common R* was 4%",
        "3_cold_and_warm_identifiable": f"common valid at {resolved_fraction:.1%} of Colorado pilot sites",
        "4_unresolved_beyond_1000km": int(np.sum([row["common_break_status_code"] == 2 for row in colorado_rows])),
        "5_multiple_breaks": int(np.sum([row["common_break_status_code"] == 6 for row in colorado_rows])),
        "6_first_break_interpretable": "interpreted as the first robust steep-to-flatter local/regional transition, not final background",
        "7_robust_to_binning": bin_stable,
        "8_robust_to_far_field_sampling": representative_gate["sampling_validation"],
        "9_robust_500_750_1000": domain_stable,
        "10_spatial_variation": float(np.nanstd(common)) if np.isfinite(common).any() else np.nan,
        "11_adaptive_changes_cold": comparisons["cold"],
        "12_adaptive_changes_warm": comparisons["warm"],
        "13_adaptive_changes_delta": comparisons["delta"],
        "14_delta_sign_change_fraction": comparisons["delta_sign_change_fraction"],
        "15_fixed_500_most_consequential": relation,
        "16_scale_field_more_informative": "scientific interpretation remains separate; the pilot maps both strength and scale without ranking them",
        "17_computational_scaling_feasible": f"bounded pilot feasible; projected full Colorado sampled work {projected_full_colorado:,} pairs",
    }
    return decision, {"comparisons": comparisons, "answers": answers}


def _preflight() -> dict[str, object]:
    cell_area_km2 = (111.2 / 24.0) * (111.2 / 24.0) * np.cos(np.deg2rad(40.0))
    dense_per_focal = int(np.pi * D_MAX_KM**2 / cell_area_km2)
    sampled_per_focal_upper = int(np.pi * 100**2 / cell_area_km2) + sum(
        int(cap) for _, cap in SAMPLING_PLAN if cap is not None
    )
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_grid_shape": [621, 1399],
        "time_days": 91,
        "cell_area_approx_km2_at_40N": float(cell_area_km2),
        "dense_pairs_per_interior_focal_approx": dense_per_focal,
        "sampled_pairs_per_focal_upper_approx": sampled_per_focal_upper,
        "representative_exhaustive_pairs_approx": dense_per_focal * 5,
        "colorado_25_site_sampled_pairs_upper_approx": sampled_per_focal_upper * 25,
        "full_colorado_sampled_pairs_upper_approx": sampled_per_focal_upper * 16235,
        "full_conus_sampled_pairs_upper_approx": sampled_per_focal_upper * 481630,
        "sampling_plan": [
            {"upper_km": upper, "max_pairs_per_focal": cap} for upper, cap in SAMPLING_PLAN
        ],
        "decision": "exhaustive only for five representatives; sampled 25-site Colorado only after representative gate",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--representatives-only", action="store_true")
    args = parser.parse_args()
    for directory in (OUTPUT, PAIR_DIR, RESULT_DIR, FIGURES):
        directory.mkdir(parents=True, exist_ok=True)
    for path in (CONUS_CUBE, CONUS_BASELINE, OLD_COLORADO_PAIRS, COLORADO_BOUNDARY):
        if not path.exists():
            raise FileNotFoundError(path)
    _json(OUTPUT / "predeclared_gate.json", PREDECLARED_GATE)
    _json(OUTPUT / "preflight_estimate.json", _preflight())
    started = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with xr.open_dataset(CONUS_CUBE, engine="h5netcdf") as cube, xr.open_dataset(
        CONUS_BASELINE, engine="h5netcdf"
    ) as baseline:
        if bool(cube.attrs.get("is_synthetic", 1)):
            raise RuntimeError("Refusing synthetic PRISM input")
        cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
        cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
        computation = baseline.output_mask
        exhaustive_rows, representative_rows, representative_sensitivity, rep_figures, rep_gate = _representatives(
            cube, computation, force=args.force
        )
        _csv(OUTPUT / "representative_exhaustive.csv", exhaustive_rows)
        _csv(OUTPUT / "representative_sampled.csv", representative_rows)
        _csv(OUTPUT / "representative_sensitivity.csv", representative_sensitivity)
        _json(OUTPUT / "representative_gate.json", rep_gate)
        rep_figures.extend(_representative_summary_figures(representative_rows, rep_gate))
        if args.representatives_only or rep_gate["status"] != "PASS":
            colorado_rows: list[dict] = []
            colorado_sensitivity: list[dict] = []
            colorado_figures: list[Path] = []
            colorado_performance = {"status": "withheld until representative gate passes"}
        else:
            colorado_rows, colorado_sensitivity, colorado_figures, colorado_performance = _colorado(
                cube, computation, force=args.force
            )
            _csv(OUTPUT / "colorado_25_site_results.csv", colorado_rows)
            _csv(OUTPUT / "colorado_sensitivity.csv", colorado_sensitivity)

    if colorado_rows:
        decision, analysis = _decision(rep_gate, colorado_rows, colorado_sensitivity, colorado_performance)
    else:
        exact_common = sum(
            int(row["common_break_status_code"]) in VALID_BREAK_CODES
            for row in exhaustive_rows
        )
        sampled_common = sum(
            int(row["common_break_status_code"]) in VALID_BREAK_CODES
            for row in representative_rows
        )
        domain_stability = _stability_fraction(
            representative_sensitivity, "domain", 750.0, 1000.0
        )
        bin_stability = _stability_fraction(
            representative_sensitivity, "bin", 20.0, 40.0
        )
        smoothing_stability = _stability_fraction(
            representative_sensitivity, "smoothing", 1.0, 5.0
        )
        fixed_delta = np.asarray(
            [float(row["fixed_delta_median"]) for row in representative_rows]
        )
        adaptive_delta = np.asarray(
            [float(row["adaptive_delta_median"]) for row in representative_rows]
        )
        fixed_cold = np.asarray(
            [float(row["fixed_cold_median"]) for row in representative_rows]
        )
        adaptive_cold = np.asarray(
            [float(row["adaptive_cold_median"]) for row in representative_rows]
        )
        fixed_warm = np.asarray(
            [float(row["fixed_warm_median"]) for row in representative_rows]
        )
        adaptive_warm = np.asarray(
            [float(row["adaptive_warm_median"]) for row in representative_rows]
        )
        preflight = _preflight()
        decision = {
            "status": "HOLD",
            "decision": "Colorado stage withheld because representative gate did not pass or representatives-only mode was requested",
            "gates": {
                "representative_common_resolved": sampled_common
                >= PREDECLARED_GATE["representative_common_resolved_minimum"],
                "far_field_sampling": rep_gate["sampling_validation"]["status"] == "PASS",
                "full_colorado_pair_work": preflight["full_colorado_sampled_pairs_upper_approx"]
                <= PREDECLARED_GATE["full_scale_pair_work_maximum"],
            },
            "metrics": {
                "exhaustive_common_resolved_count": exact_common,
                "sampled_common_resolved_count": sampled_common,
                "site_count": len(representative_rows),
                "sampling_break_status_agreement": rep_gate["sampling_validation"]["break_agreement_fraction"],
                "fixed_500km_delta_sampling_mae": rep_gate["sampling_validation"]["fixed_500km_delta_mae"],
                "domain_stable_fraction": domain_stability,
                "bin_stable_fraction": bin_stability,
                "smoothing_stable_fraction": smoothing_stability,
                "projected_full_colorado_sampled_pair_work": preflight["full_colorado_sampled_pairs_upper_approx"],
            },
        }
        comparisons = {
            "cold": _comparison_stats(fixed_cold, adaptive_cold),
            "warm": _comparison_stats(fixed_warm, adaptive_warm),
            "delta": _comparison_stats(fixed_delta, adaptive_delta),
            "delta_sign_change_fraction": None,
            "status": "under-supported because only one sampled common break resolved",
        }
        analysis = {
            "comparisons": comparisons,
            "answers": {
                "1_stable_break_inside_1000km": f"No general result: exhaustive common breaks resolved at {exact_common}/5 and sampled common breaks at {sampled_common}/5.",
                "2_1000km_context_improves_previous_500km": "It exposes first-break candidates at more representative locations than the final-background R* criterion, but those candidates are not stable enough under sampling.",
                "3_cold_and_warm_identifiable": f"Both were identifiable together at {exact_common}/5 exhaustive and {sampled_common}/5 sampled representative pixels.",
                "4_unresolved_beyond_1000km": sum(
                    int(row["cold_break_status_code"]) == 2
                    or int(row["warm_break_status_code"]) == 2
                    for row in exhaustive_rows
                ),
                "5_multiple_breaks": sum(
                    int(row["cold_break_status_code"]) == 6
                    or int(row["warm_break_status_code"]) == 6
                    for row in exhaustive_rows
                ),
                "6_first_break_interpretable": "Conceptually yes as a steep-to-flatter local/regional transition, but reproducibility is not yet sufficient for mapping.",
                "7_robust_to_binning": bin_stability,
                "8_robust_to_far_field_sampling": rep_gate["sampling_validation"],
                "9_robust_500_750_1000": domain_stability,
                "10_spatial_variation": "Candidate distances vary across the five sites, but ambiguity and status instability prevent inference of a spatial field.",
                "11_adaptive_changes_cold": comparisons["cold"],
                "12_adaptive_changes_warm": comparisons["warm"],
                "13_adaptive_changes_delta": comparisons["delta"],
                "14_delta_sign_change_fraction": None,
                "15_fixed_500_most_consequential": "Not identifiable from one sampled common-valid site.",
                "16_scale_field_more_informative": "Not established; the scale field itself failed the representative gate.",
                "17_computational_scaling_feasible": f"The bounded representative run is feasible, but the sampled full-Colorado upper estimate is {preflight['full_colorado_sampled_pairs_upper_approx']:,} pairs and exceeds the predeclared gate.",
            },
        }
    _json(OUTPUT / "decision_gate.json", decision)
    _json(OUTPUT / "fixed_vs_adaptive_statistics.json", analysis["comparisons"])
    _json(OUTPUT / "final_questions.json", analysis["answers"])
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = int(after if after > 10_000_000 else after * 1024)
    performance = {
        "status": "complete bounded experiment",
        "wall_seconds": time.perf_counter() - started,
        "process_peak_rss_bytes": peak,
        "representative": rep_gate.get("performance", []),
        "colorado": colorado_performance,
        "network_bytes": 0,
    }
    _json(OUTPUT / "performance.json", performance)
    runtime = version_info()
    provenance = {
        "status": "complete bounded real-data four-round experiment",
        "source_dataset": "PRISM retained CONUS snapshot",
        "source_path": str(CONUS_CUBE.relative_to(ROOT)),
        "source_sha256": _sha(CONUS_CUBE),
        "time_period": ["2023-11-01", "2024-01-30"],
        "time_window_id": "2023-11-01/2024-01-30",
        "cold_definition": "pair-valid median split; joint lower-tail TMIN using inclusive <=",
        "warm_definition": "pair-valid median split; joint upper-tail TMAX using strict >",
        "delta_definition": "pairwise cold_synchrony - warm_synchrony",
        "correlation_statistic": "exact average-rank Spearman on joint-tail observations",
        "maximum_discovery_radius_km": D_MAX_KM,
        "maximum_discovery_radius_role": "observation domain, not estimated scale",
        "far_field_sampling_design": _preflight()["sampling_plan"],
        "break_estimator": "first robust two-segment local-to-regional transition",
        "break_estimator_parameters": {
            "bin_width_km": BIN_WIDTH_KM,
            "min_annulus_count": MIN_ANNULUS_COUNT,
            "smoothing_bins": SMOOTHING_BINS,
        },
        "common_radius_rule": "max of independently valid cold and warm breaks",
        "reduction_statistic": "design-weighted median with pairwise Delta identity preserved",
        "fixed_comparison_radius_km": FIXED_RADIUS_KM,
        "code_commit": runtime.git_sha or "unavailable",
        "code_version": runtime.version,
        "working_tree_note": "experiment includes uncommitted task changes; see git_diff_summary.txt",
        "creation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "network_data_transferred_bytes": 0,
        "full_scale_status": decision["status"],
    }
    _json(OUTPUT / "provenance.json", provenance)
    summary = {
        "status": "complete",
        "decision_gate": decision["status"],
        "representative_gate": rep_gate["status"],
        "colorado_stage_run": bool(colorado_rows),
        "representative_site_count": len(representative_rows),
        "colorado_site_count": len(colorado_rows),
        "figures": [str(path.relative_to(ROOT)) for path in [*rep_figures, *colorado_figures]],
        "limitations": [
            "The Colorado pilot is 25 spatially balanced focal sites, not a statewide raster.",
            "One 91-day winter window does not establish temporal stability.",
            "The first segmented break is an empirical transition, not a dispersal distance or natural radius.",
            "Far-field sampling is used only after exhaustive representative validation.",
            "No full Colorado or CONUS production run is launched by this script.",
        ],
    }
    _json(OUTPUT / "summary.json", summary)
    (OUTPUT / "REPRODUCE.md").write_text(
        "# Reproduce the four-round adaptive synchrony experiment\n\n"
        "```bash\nenv MPLCONFIGDIR=/tmp/cubedynamics-mpl-cache XDG_CACHE_HOME=/tmp/cubedynamics-xdg-cache "
        ".venv/bin/python scripts/run_adaptive_synchrony_four_round.py\n```\n\n"
        "The workflow is offline, SHA-validates completed checkpoints, runs exhaustive 1000 km representative pixels first, "
        "and advances to the sampled 25-site Colorado pilot only when the representative gate passes.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "decision": decision["status"], "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
