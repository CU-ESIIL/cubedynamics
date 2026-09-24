#!/usr/bin/env python3
"""Characterize empirical synchrony decay from retained pair checkpoints.

This is Experiment 2 after the finite-horizon Experiment 1. It never streams
PRISM and never recomputes pair synchrony. Reproduce with::

    .venv/bin/python scripts/run_empirical_synchrony_decay_pilot.py
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
from scipy.stats import pearsonr, spearmanr, wilcoxon
import xarray as xr

from cubedynamics.synchrony.decay import DECAY_STATUS, empirical_synchrony_decay
from cubedynamics.synchrony.ranges import RANGE_STATUS


ROOT = Path(__file__).resolve().parents[1]
RANGE_ROOT = ROOT / "artifacts" / "empirical-synchrony-range"
PAIR_ROOT = RANGE_ROOT / "pair_checkpoints"
OUTPUT = ROOT / "artifacts" / "empirical-synchrony-decay"
FIGURES = OUTPUT / "figures"
PREVIOUS_COLORADO = RANGE_ROOT / "colorado_25_site_range_pilot.nc"
PREVIOUS_REPRESENTATIVE = RANGE_ROOT / "representative_pixels.csv"

DISCOVERY_RADII = (200.0, 300.0, 400.0, 500.0)
BIN_WIDTHS = (10.0, 20.0, 40.0)
BACKGROUNDS = ("outer_annuli", "smoothed_outer_annuli", "distant_pairs")
PRIMARY_RADIUS = 500.0
PRIMARY_BIN = 20.0
PRIMARY_BACKGROUND = "outer_annuli"
TAILS = ("cold", "warm")
REPRESENTATIVE = (
    ("Colorado mountains", "colorado_mountains"),
    ("Great Plains", "great_plains"),
    ("Southeast", "southeast"),
    ("Northeast", "northeast"),
    ("Pacific region", "pacific_region"),
)

# Declared before pilot evaluation. Coverage alone is not sufficient.
GATE = {
    "minimum_colorado_valid_fraction_each_tail": 0.70,
    "minimum_representative_valid_count_each_tail": 4,
    "minimum_stable_fraction_each_tail": 0.70,
    "d50_discovery_absolute_tolerance_km": 30.0,
    "d50_bin_width_range_tolerance_km": 40.0,
    "d50_background_range_tolerance_km": 40.0,
    "effective_length_discovery_relative_tolerance": 0.10,
    "effective_length_bin_relative_tolerance": 0.20,
    "effective_length_background_relative_tolerance": 0.20,
    "beta_discovery_absolute_tolerance_per_100km": 0.02,
    "beta_bin_absolute_tolerance_per_100km": 0.03,
    "beta_minimum_fit_score": 0.25,
}

NAVY = "#123F70"
BLUE = "#2878B5"
RED = "#B63A3A"
GOLD = "#F0B43C"
GREEN = "#3A8D6D"
PURPLE = "#6B4C9A"
INK = "#17212B"


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
        for key in row:
            if key not in fields:
                fields.append(key)
    temporary = path.with_suffix(".partial.csv")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _load_checkpoint(key: str) -> tuple[xr.Dataset, dict[str, object]]:
    path = PAIR_ROOT / f"{key}.nc"
    manifest_path = path.with_suffix(".json")
    if not path.exists() or not manifest_path.exists():
        raise FileNotFoundError(f"Required retained pair checkpoint is missing: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_sha = sha256(path.read_bytes()).hexdigest()
    if manifest.get("status") != "complete" or manifest.get("sha256") != actual_sha:
        raise ValueError(f"Pair checkpoint manifest/hash mismatch: {path}")
    with xr.open_dataset(path, engine="h5netcdf") as opened:
        pairs = opened.load()
    if manifest.get("analysis_fingerprint") != pairs.attrs.get("analysis_fingerprint"):
        raise ValueError(f"Pair checkpoint fingerprint mismatch: {path}")
    record = {
        "key": key,
        "path": str(path.relative_to(ROOT)),
        "sha256": actual_sha,
        "analysis_fingerprint": pairs.attrs.get("analysis_fingerprint"),
        "pair_count": int(pairs.sizes["pair"]),
        "nonself_pair_count": int(pairs.attrs.get("nonself_pair_count", 0)),
        "reused_without_pair_recomputation": True,
    }
    return pairs, record


def _sites(pairs: xr.Dataset) -> list[dict[str, object]]:
    output = np.asarray(pairs.output_mask.values, dtype=bool)
    rows = []
    for yi, xi in np.argwhere(output):
        rows.append(
            {
                "y_index": int(yi),
                "x_index": int(xi),
                "latitude": float(pairs.y.values[yi]),
                "longitude": float(pairs.x.values[xi]),
            }
        )
    return rows


def _at(result: xr.Dataset, name: str, site: dict[str, object]) -> float:
    return float(
        result[name].isel(
            time_window_end=0,
            y=int(site["y_index"]),
            x=int(site["x_index"]),
        ).values
    )


def _extract(result: xr.Dataset, site: dict[str, object]) -> dict[str, object]:
    row: dict[str, object] = dict(site)
    names = [
        name for name in result.data_vars
        if name not in {"output_mask", "computation_mask"} and "radial_bin" not in result[name].dims
    ]
    for name in names:
        value = _at(result, name, site)
        row[name] = int(value) if name.endswith("_status") and np.isfinite(value) else value
        if name.endswith("_status"):
            row[f"{name}_label"] = DECAY_STATUS.get(int(value), "unknown")
    return row


def _curve_extract(result: xr.Dataset, site: dict[str, object]) -> dict[str, object]:
    selection = dict(
        time_window_end=0,
        y=int(site["y_index"]),
        x=int(site["x_index"]),
    )
    return {
        "radius_km": np.asarray(result.radius_km.values, dtype=float),
        **{
            f"{tail}_{name}": np.asarray(result[f"{tail}_{name}"].isel(**selection).values)
            for tail in TAILS
            for name in (
                "annular_median", "annular_q25", "annular_q75", "annular_count",
                "cumulative_median", "smoothed_annular_median", "normalized_excess",
            )
        },
    }


def _run_config(
    pairs: xr.Dataset,
    sites: list[dict[str, object]],
    *,
    discovery: float,
    bin_width: float,
    background: str,
) -> tuple[list[dict[str, object]], dict[int, dict[str, object]], float]:
    started = time.perf_counter()
    result = empirical_synchrony_decay(
        pairs,
        discovery_radius_km=discovery,
        bin_width_km=bin_width,
        min_annulus_count=30,
        background_shell_count=4,
        background_method=background,
        local_shell_count=2,
        crossing_persistence_bins=2,
        min_local_excess=0.04,
        initial_window_km=100.0,
    )
    rows = [_extract(result, site) for site in sites]
    curves = {index: _curve_extract(result, site) for index, site in enumerate(sites)}
    elapsed = time.perf_counter() - started
    result.close()
    return rows, curves, elapsed


def _configuration_results(
    pairs: xr.Dataset,
    sites: list[dict[str, object]],
) -> tuple[dict[tuple[float, float, str], list[dict[str, object]]], dict[int, dict[str, object]], list[dict[str, object]]]:
    configs = {(radius, PRIMARY_BIN, PRIMARY_BACKGROUND) for radius in DISCOVERY_RADII}
    configs.update((PRIMARY_RADIUS, width, PRIMARY_BACKGROUND) for width in BIN_WIDTHS)
    configs.update((PRIMARY_RADIUS, PRIMARY_BIN, background) for background in BACKGROUNDS)
    rows_by_config: dict[tuple[float, float, str], list[dict[str, object]]] = {}
    primary_curves: dict[int, dict[str, object]] = {}
    timing = []
    for discovery, width, background in sorted(configs):
        rows, curves, elapsed = _run_config(
            pairs,
            sites,
            discovery=discovery,
            bin_width=width,
            background=background,
        )
        key = (discovery, width, background)
        rows_by_config[key] = rows
        timing.append(
            {
                "discovery_radius_km": discovery,
                "bin_width_km": width,
                "background_method": background,
                "elapsed_seconds": elapsed,
            }
        )
        if key == (PRIMARY_RADIUS, PRIMARY_BIN, PRIMARY_BACKGROUND):
            primary_curves = curves
    return rows_by_config, primary_curves, timing


def _previous_colorado_statuses() -> dict[tuple[float, float], dict[str, object]]:
    with xr.open_dataset(PREVIOUS_COLORADO, engine="h5netcdf") as opened:
        previous = opened.load()
    result = {}
    for yi, xi in np.argwhere(np.asarray(previous.output_mask.values, dtype=bool)):
        key = (round(float(previous.y.values[yi]), 6), round(float(previous.x.values[xi]), 6))
        row = {}
        for tail in ("cold", "warm", "common"):
            code = int(previous[f"{tail}_range_status"].isel(time_window_end=0, y=yi, x=xi))
            row[f"previous_{tail}_range_status"] = RANGE_STATUS[code]
            row[f"previous_{tail}_range_status_code"] = code
        row["fixed_cold_synchrony"] = float(previous.fixed_cold_median.isel(time_window_end=0, y=yi, x=xi))
        row["fixed_warm_synchrony"] = float(previous.fixed_warm_median.isel(time_window_end=0, y=yi, x=xi))
        row["fixed_delta_s"] = float(previous.fixed_delta_pair_median.isel(time_window_end=0, y=yi, x=xi))
        result[key] = row
    return result


def _previous_representative_statuses() -> dict[str, dict[str, object]]:
    with PREVIOUS_REPRESENTATIVE.open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return {
        row["label"]: {
            f"previous_{tail}_range_status": row[f"{tail}_status"]
            for tail in ("cold", "warm", "common")
        }
        for row in rows
    }


def _join_primary(
    primary: list[dict[str, object]],
    configs: dict[tuple[float, float, str], list[dict[str, object]]],
    previous: dict,
    *,
    representative_label: str | None = None,
) -> list[dict[str, object]]:
    rows = []
    radius_rows = {radius: configs[(radius, PRIMARY_BIN, PRIMARY_BACKGROUND)] for radius in DISCOVERY_RADII}
    bin_rows = {width: configs[(PRIMARY_RADIUS, width, PRIMARY_BACKGROUND)] for width in BIN_WIDTHS}
    background_rows = {method: configs[(PRIMARY_RADIUS, PRIMARY_BIN, method)] for method in BACKGROUNDS}
    for index, source in enumerate(primary):
        row = dict(source)
        if representative_label is not None:
            row["label"] = representative_label
            row.update(previous[representative_label])
        else:
            row["site_id"] = f"CO-{index + 1:02d}"
            row["label"] = f"Colorado site {index + 1:02d}"
            key = (round(float(row["latitude"]), 6), round(float(row["longitude"]), 6))
            row.update(previous[key])
        for tail in TAILS:
            for radius in DISCOVERY_RADII:
                item = radius_rows[radius][index]
                row[f"L_{int(radius)}_{tail}_km"] = item[f"{tail}_effective_length_km"]
                row[f"L_{int(radius)}_{tail}_status"] = item[f"{tail}_effective_length_status_label"]
                row[f"d50_{int(radius)}_{tail}_km"] = item[f"{tail}_d50_km"]
                row[f"d50_{int(radius)}_{tail}_status"] = item[f"{tail}_d50_status_label"]
                row[f"beta_{int(radius)}_{tail}_per_100km"] = item[f"{tail}_beta_initial_per_100km"]
            d50_bins = [bin_rows[width][index][f"{tail}_d50_km"] for width in BIN_WIDTHS]
            d50_backgrounds = [background_rows[method][index][f"{tail}_d50_km"] for method in BACKGROUNDS]
            length_bins = [bin_rows[width][index][f"{tail}_effective_length_km"] for width in BIN_WIDTHS]
            length_backgrounds = [background_rows[method][index][f"{tail}_effective_length_km"] for method in BACKGROUNDS]
            beta_bins = [bin_rows[width][index][f"{tail}_beta_initial_per_100km"] for width in BIN_WIDTHS]
            row[f"{tail}_d50_discovery_stable"] = _abs_stable(
                radius_rows[400.0][index][f"{tail}_d50_km"],
                radius_rows[500.0][index][f"{tail}_d50_km"],
                GATE["d50_discovery_absolute_tolerance_km"],
            )
            row[f"{tail}_d50_bin_range_km"] = _finite_range(d50_bins)
            row[f"{tail}_d50_background_range_km"] = _finite_range(d50_backgrounds)
            row[f"{tail}_L_discovery_relative_change"] = _relative_change(
                radius_rows[400.0][index][f"{tail}_effective_length_km"],
                radius_rows[500.0][index][f"{tail}_effective_length_km"],
            )
            row[f"{tail}_L_bin_relative_range"] = _relative_range(length_bins)
            row[f"{tail}_L_background_relative_range"] = _relative_range(length_backgrounds)
            row[f"{tail}_beta_discovery_change"] = _absolute_change(
                radius_rows[400.0][index][f"{tail}_beta_initial_per_100km"],
                radius_rows[500.0][index][f"{tail}_beta_initial_per_100km"],
            )
            row[f"{tail}_beta_bin_range"] = _finite_range(beta_bins)
        rows.append(row)
    return rows


def _finite(values) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array[np.isfinite(array)]


def _finite_range(values) -> float:
    original = np.asarray(values, dtype=float)
    return (
        float(np.max(original) - np.min(original))
        if original.size and np.all(np.isfinite(original))
        else float("nan")
    )


def _relative_range(values) -> float:
    original = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(original)):
        return float("nan")
    scale = max(abs(float(np.median(original))), 1e-8)
    return float((np.max(original) - np.min(original)) / scale)


def _absolute_change(left, right) -> float:
    return float(abs(float(right) - float(left))) if np.isfinite(left) and np.isfinite(right) else float("nan")


def _relative_change(left, right) -> float:
    return _absolute_change(left, right) / max(abs(float(right)), 1e-8) if np.isfinite(left) and np.isfinite(right) else float("nan")


def _abs_stable(left, right, tolerance) -> bool:
    change = _absolute_change(left, right)
    return bool(np.isfinite(change) and change <= tolerance)


def _long_sensitivity(
    label: str,
    configs: dict[tuple[float, float, str], list[dict[str, object]]],
) -> list[dict[str, object]]:
    rows = []
    for (radius, width, background), sites in sorted(configs.items()):
        for index, site in enumerate(sites):
            for tail in TAILS:
                rows.append(
                    {
                        "scope": label,
                        "site_index": index,
                        "label": site.get("label", label),
                        "latitude": site["latitude"],
                        "longitude": site["longitude"],
                        "tail": tail,
                        "discovery_radius_km": radius,
                        "bin_width_km": width,
                        "background_method": background,
                        "d25_km": site[f"{tail}_d25_km"],
                        "d25_status": site[f"{tail}_d25_status_label"],
                        "d50_km": site[f"{tail}_d50_km"],
                        "d50_status": site[f"{tail}_d50_status_label"],
                        "d75_km": site[f"{tail}_d75_km"],
                        "d75_status": site[f"{tail}_d75_status_label"],
                        "effective_length_km": site[f"{tail}_effective_length_km"],
                        "effective_length_status": site[f"{tail}_effective_length_status_label"],
                        "beta_initial_per_100km": site[f"{tail}_beta_initial_per_100km"],
                        "beta_fit_score": site[f"{tail}_beta_initial_fit_score"],
                    }
                )
    return rows


def _gate_metric(
    colorado: list[dict[str, object]],
    representatives: list[dict[str, object]],
    metric: str,
) -> dict[str, object]:
    result: dict[str, object] = {"metric": metric, "predeclared_gate": GATE}
    tail_passes = []
    for tail in TAILS:
        if metric == "d50":
            valid = [row[f"{tail}_d50_status"] == 3 for row in colorado]
            rep_valid = [row[f"{tail}_d50_status"] == 3 for row in representatives]
            stable = [bool(row[f"{tail}_d50_discovery_stable"]) for row in colorado]
            bin_stable = [
                np.isfinite(row[f"{tail}_d50_bin_range_km"])
                and row[f"{tail}_d50_bin_range_km"] <= GATE["d50_bin_width_range_tolerance_km"]
                for row in colorado
            ]
            bg_stable = [
                np.isfinite(row[f"{tail}_d50_background_range_km"])
                and row[f"{tail}_d50_background_range_km"] <= GATE["d50_background_range_tolerance_km"]
                for row in colorado
            ]
        elif metric == "effective_length":
            valid = [row[f"{tail}_effective_length_status"] == 3 for row in colorado]
            rep_valid = [row[f"{tail}_effective_length_status"] == 3 for row in representatives]
            stable = [
                np.isfinite(row[f"{tail}_L_discovery_relative_change"])
                and row[f"{tail}_L_discovery_relative_change"] <= GATE["effective_length_discovery_relative_tolerance"]
                for row in colorado
            ]
            bin_stable = [
                np.isfinite(row[f"{tail}_L_bin_relative_range"])
                and row[f"{tail}_L_bin_relative_range"] <= GATE["effective_length_bin_relative_tolerance"]
                for row in colorado
            ]
            bg_stable = [
                np.isfinite(row[f"{tail}_L_background_relative_range"])
                and row[f"{tail}_L_background_relative_range"] <= GATE["effective_length_background_relative_tolerance"]
                for row in colorado
            ]
        else:
            valid = [
                row[f"{tail}_beta_initial_status"] == 3
                and row[f"{tail}_beta_initial_fit_score"] >= GATE["beta_minimum_fit_score"]
                for row in colorado
            ]
            rep_valid = [
                row[f"{tail}_beta_initial_status"] == 3
                and row[f"{tail}_beta_initial_fit_score"] >= GATE["beta_minimum_fit_score"]
                for row in representatives
            ]
            stable = [
                np.isfinite(row[f"{tail}_beta_discovery_change"])
                and row[f"{tail}_beta_discovery_change"] <= GATE["beta_discovery_absolute_tolerance_per_100km"]
                for row in colorado
            ]
            bin_stable = [
                np.isfinite(row[f"{tail}_beta_bin_range"])
                and row[f"{tail}_beta_bin_range"] <= GATE["beta_bin_absolute_tolerance_per_100km"]
                for row in colorado
            ]
            bg_stable = [True for _ in colorado]
        tail_result = {
            "colorado_valid_fraction": float(np.mean(valid)),
            "representative_valid_count": int(np.count_nonzero(rep_valid)),
            "discovery_stable_fraction": float(np.mean(stable)),
            "bin_stable_fraction": float(np.mean(bin_stable)),
            "background_stable_fraction": float(np.mean(bg_stable)),
        }
        passed = (
            tail_result["colorado_valid_fraction"] >= GATE["minimum_colorado_valid_fraction_each_tail"]
            and tail_result["representative_valid_count"] >= GATE["minimum_representative_valid_count_each_tail"]
            and tail_result["discovery_stable_fraction"] >= GATE["minimum_stable_fraction_each_tail"]
            and tail_result["bin_stable_fraction"] >= GATE["minimum_stable_fraction_each_tail"]
            and tail_result["background_stable_fraction"] >= GATE["minimum_stable_fraction_each_tail"]
        )
        tail_result["decision"] = "PASS" if passed else "HOLD"
        result[tail] = tail_result
        tail_passes.append(passed)
    result["overall_decision"] = "PASS" if all(tail_passes) else "HOLD"
    return result


def _correlation(rows: list[dict[str, object]], left: str, right: str) -> dict[str, object]:
    x = np.asarray([row[left] for row in rows], dtype=float)
    y = np.asarray([row[right] for row in rows], dtype=float)
    use = np.isfinite(x) & np.isfinite(y)
    if np.count_nonzero(use) < 3:
        return {"n": int(np.count_nonzero(use)), "pearson": None, "spearman": None}
    return {
        "n": int(np.count_nonzero(use)),
        "pearson": float(pearsonr(x[use], y[use]).statistic),
        "spearman": float(spearmanr(x[use], y[use]).statistic),
    }


def _paired_summary(rows: list[dict[str, object]], name: str) -> dict[str, object]:
    values = _finite([row[name] for row in rows])
    if not values.size:
        return {"n": 0, "median": None, "iqr": None, "positive_fraction": None, "wilcoxon_p": None}
    q25, q75 = np.quantile(values, (0.25, 0.75))
    nonzero = values[~np.isclose(values, 0.0)]
    p_value = float(wilcoxon(nonzero).pvalue) if nonzero.size >= 5 else None
    return {
        "n": int(values.size),
        "median": float(np.median(values)),
        "iqr": float(q75 - q25),
        "positive_fraction": float(np.mean(values > 0)),
        "wilcoxon_p": p_value,
    }


def _incident(pairs: xr.Dataset, site: dict[str, object]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    node = int(site["y_index"]) * pairs.sizes["x"] + int(site["x_index"])
    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    use = ((source == node) | (target == node)) & (source != target)
    return np.asarray(pairs.distance_km.values, dtype=float)[use], {
        tail: np.asarray(pairs[f"{tail}_synchrony"].values, dtype=float)[use]
        for tail in TAILS
    }


def _diagnostic_figure(
    label: str,
    pairs: xr.Dataset,
    site: dict[str, object],
    primary: dict[str, object],
    curves: dict[str, object],
) -> Path:
    distance, pair_values = _incident(pairs, site)
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 7.2), sharex=True, constrained_layout=True)
    rng = np.random.default_rng(20260924)
    for ax, tail, color in zip(axes, TAILS, (BLUE, RED)):
        values = pair_values[tail]
        valid = np.isfinite(distance) & np.isfinite(values) & (distance > 0)
        indices = np.flatnonzero(valid)
        if indices.size > 14000:
            indices = rng.choice(indices, 14000, replace=False)
        ax.scatter(distance[indices], values[indices], s=3, alpha=.09, color=color, rasterized=True)
        radius = curves["radius_km"]
        median = curves[f"{tail}_annular_median"]
        q25 = curves[f"{tail}_annular_q25"]
        q75 = curves[f"{tail}_annular_q75"]
        ax.fill_between(radius, q25, q75, color=color, alpha=.17, label="Annular IQR")
        ax.plot(radius, median, color=color, lw=2, marker="o", ms=3, label="Annular median")
        ax.plot(radius, curves[f"{tail}_cumulative_median"], color=INK, ls="--", lw=1.5, label="Cumulative median")
        background = float(primary[f"{tail}_background"])
        local = float(primary[f"{tail}_local_synchrony"])
        ax.axhline(background, color=GOLD, lw=1.6, label="Empirical background")
        ax.axhline(local, color=GREEN, lw=1.2, ls=":", label="Near-field level")
        for fraction, linestyle in zip((25, 50, 75), (":", "-", "--")):
            value = float(primary[f"{tail}_d{fraction}_km"])
            if np.isfinite(value):
                ax.axvline(value, color=PURPLE, lw=1.4, ls=linestyle)
                ax.text(value, .02, f"d{fraction}", rotation=90, transform=ax.get_xaxis_transform(), ha="right", va="bottom", color=PURPLE)
        text = (
            f"old R*: {primary[f'previous_{tail}_range_status']}\n"
            f"d50: {_fmt(primary[f'{tail}_d50_km'], ' km')}\n"
            f"L: {_fmt(primary[f'{tail}_effective_length_km'], ' km')}\n"
            f"beta: {_fmt(primary[f'{tail}_beta_initial_per_100km'], ' /100 km')}"
        )
        ax.text(.99, .97, text, transform=ax.transAxes, ha="right", va="top", fontsize=9, bbox=dict(fc="white", ec="#CCD7DF", alpha=.9))
        ax.set_ylabel(f"{tail.capitalize()} synchrony")
        ax.grid(alpha=.14)
    axes[0].legend(frameon=False, ncol=5, fontsize=8, loc="lower left")
    axes[-1].set_xlabel("Physical distance (km)")
    fig.suptitle(f"{label}: empirical synchrony decay from retained pairs", color=NAVY, weight="bold")
    path = FIGURES / f"diagnostic_{label.lower().replace(' ', '_')}.png"
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)
    return path


def _fmt(value, suffix="") -> str:
    return f"{float(value):.2f}{suffix}" if np.isfinite(value) else "unresolved"


def _pedagogical_figures() -> list[Path]:
    x = np.linspace(0, 500, 251)
    curve = 0.22 + 0.68 * np.exp(-x / 135) + 0.035 * np.sin(x / 45)
    local, background = curve[0], 0.22
    half = background + .5 * (local - background)
    d50 = float(np.interp(half, curve[::-1], x[::-1]))
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    ax.plot(x, curve, color=BLUE, lw=3, label="Conceptual empirical curve")
    ax.axhline(local, color=GREEN, ls=":", label="S_local")
    ax.axhline(background, color=GOLD, label="S_background")
    ax.axhline(half, color=PURPLE, ls="--", label="Half of local excess remains")
    ax.axvline(d50, color=PURPLE, lw=2)
    ax.annotate(f"d50 = {d50:.0f} km", (d50, half), (d50 + 45, half + .13), arrowprops=dict(arrowstyle="->", color=PURPLE), color=PURPLE, weight="bold")
    ax.set(xlabel="Physical distance (km)", ylabel="Synchrony", title="Conceptual: d50 is half-loss relative to background, not zero synchrony")
    ax.legend(frameon=False)
    ax.grid(alpha=.15)
    path_d50 = FIGURES / "pedagogical_d50.png"
    fig.savefig(path_d50, dpi=220, facecolor="white")
    plt.close(fig)

    excess = np.clip((curve - background) / (local - background), 0, None)
    length = float(np.trapz(excess, x))
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    ax.plot(x, excess, color=BLUE, lw=3, label="Normalized excess synchrony")
    ax.fill_between(x, 0, excess, color=BLUE, alpha=.25, label="Observed positive area")
    ax.add_patch(plt.Rectangle((0, 0), length, 1, fill=False, ec=RED, lw=2.5, ls="--", label=f"Equal-area rectangle: L = {length:.0f} km"))
    ax.set(xlabel="Physical distance (km)", ylabel="Normalized excess", ylim=(0, 1.08), title="Conceptual: effective length is the width of an equal-area rectangle")
    ax.legend(frameon=False)
    ax.grid(alpha=.15)
    path_l = FIGURES / "pedagogical_effective_length.png"
    fig.savefig(path_l, dpi=220, facecolor="white")
    plt.close(fig)
    return [path_d50, path_l]


def _summary_figures(colorado: list[dict[str, object]], gates: dict[str, dict[str, object]]) -> list[Path]:
    paths = []
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), constrained_layout=True)
    for ax, metric, title in zip(axes, ("d50", "effective_length", "beta_initial"), ("d50", "Effective length", "Initial slope")):
        gate = gates[metric]
        x = np.arange(2)
        values = [gate[tail]["colorado_valid_fraction"] for tail in TAILS]
        ax.bar(x, values, color=(BLUE, RED))
        ax.axhline(GATE["minimum_colorado_valid_fraction_each_tail"], color=INK, ls="--", lw=1)
        ax.set(xticks=x, xticklabels=("Cold", "Warm"), ylim=(0, 1), title=title, ylabel="Valid fraction")
    fig.suptitle("Colorado pilot coverage under the predeclared gate", color=NAVY, weight="bold")
    path = FIGURES / "metric_coverage.png"; fig.savefig(path, dpi=220, facecolor="white"); plt.close(fig); paths.append(path)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    for tail, color in zip(TAILS, (BLUE, RED)):
        axes[0].scatter([row[f"d50_400_{tail}_km"] for row in colorado], [row[f"d50_500_{tail}_km"] for row in colorado], color=color, alpha=.75, label=tail.capitalize())
        axes[1].scatter([row[f"L_400_{tail}_km"] for row in colorado], [row[f"L_500_{tail}_km"] for row in colorado], color=color, alpha=.75)
        axes[2].scatter([row[f"beta_400_{tail}_per_100km"] for row in colorado], [row[f"beta_500_{tail}_per_100km"] for row in colorado], color=color, alpha=.75)
    for ax, title, unit in zip(axes, ("d50", "Effective length", "Initial slope"), ("km", "km", "per 100 km")):
        limits = np.asarray(ax.get_xlim())
        ax.plot(limits, limits, color=INK, ls="--", lw=1)
        ax.set(xlabel=f"400 km support ({unit})", ylabel=f"500 km support ({unit})", title=title)
        ax.grid(alpha=.15)
    axes[0].legend(frameon=False)
    fig.suptitle("Discovery-radius stability", color=NAVY, weight="bold")
    path = FIGURES / "discovery_stability.png"; fig.savefig(path, dpi=220, facecolor="white"); plt.close(fig); paths.append(path)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    metrics = (("d50", "km"), ("effective_length", "km"), ("beta_initial", "per 100 km"))
    for ax, (metric, units) in zip(axes, metrics):
        for tail, color in zip(TAILS, (BLUE, RED)):
            x = [row[f"{tail}_{metric if metric != 'effective_length' else 'effective_length'}_km"] if metric != "beta_initial" else row[f"{tail}_beta_initial_per_100km"] for row in colorado]
            y = [row[f"{tail}_decay_fraction_100km"] for row in colorado]
            ax.scatter(x, y, color=color, alpha=.75, label=tail.capitalize())
        ax.set(xlabel=f"{metric.replace('_', ' ')} ({units})", ylabel="Fraction of excess lost by 100 km", title=metric.replace("_", " ").title())
        ax.grid(alpha=.15)
    axes[0].legend(frameon=False)
    fig.suptitle("What 100 km represents on the empirical curves", color=NAVY, weight="bold")
    path = FIGURES / "fixed_100km_interpretation.png"; fig.savefig(path, dpi=220, facecolor="white"); plt.close(fig); paths.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    for tail, color in zip(TAILS, (BLUE, RED)):
        axes[0].scatter([row[f"{tail}_beta_near_per_100km"] for row in colorado], [row[f"{tail}_beta_mid_per_100km"] for row in colorado], color=color, alpha=.75, label=tail.capitalize())
        axes[1].scatter([row[f"{tail}_beta_mid_per_100km"] for row in colorado], [row[f"{tail}_beta_far_per_100km"] for row in colorado], color=color, alpha=.75)
    axes[0].set(xlabel="Near slope 0-100", ylabel="Mid slope 100-300", title="Near vs mid")
    axes[1].set(xlabel="Mid slope 100-300", ylabel="Far slope 300-500", title="Mid vs far")
    for ax in axes: ax.axhline(0, color=INK, lw=.8); ax.axvline(0, color=INK, lw=.8); ax.grid(alpha=.15)
    axes[0].legend(frameon=False)
    fig.suptitle("Multiscale decay diagnostic", color=NAVY, weight="bold")
    path = FIGURES / "multiscale_slopes.png"; fig.savefig(path, dpi=220, facecolor="white"); plt.close(fig); paths.append(path)

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), constrained_layout=True)
    sensitivity_specs = (
        ("d50", "d50_bin_range_km", GATE["d50_bin_width_range_tolerance_km"], "Range across 10/20/40 km bins (km)"),
        ("L", "L_bin_relative_range", GATE["effective_length_bin_relative_tolerance"], "Relative range across bin widths"),
        ("Beta", "beta_bin_range", GATE["beta_bin_absolute_tolerance_per_100km"], "Range across bin widths (/100 km)"),
    )
    for ax, (title, suffix, threshold, ylabel) in zip(axes, sensitivity_specs):
        data = [[row[f"{tail}_{suffix}"] for row in colorado if np.isfinite(row[f"{tail}_{suffix}"])] for tail in TAILS]
        ax.boxplot(data, tick_labels=("Cold", "Warm"), patch_artist=True, boxprops=dict(facecolor="#DDEAF3"))
        ax.axhline(threshold, color=RED, ls="--", label="Gate tolerance")
        ax.set(title=title, ylabel=ylabel); ax.grid(axis="y", alpha=.15)
    axes[0].legend(frameon=False)
    fig.suptitle("Bin-width sensitivity", color=NAVY, weight="bold")
    path = FIGURES / "bin_width_sensitivity.png"; fig.savefig(path, dpi=220, facecolor="white"); plt.close(fig); paths.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    for ax, suffix, threshold, title, ylabel in (
        (axes[0], "d50_background_range_km", GATE["d50_background_range_tolerance_km"], "d50", "Range across backgrounds (km)"),
        (axes[1], "L_background_relative_range", GATE["effective_length_background_relative_tolerance"], "Effective length", "Relative range across backgrounds"),
    ):
        data = [[row[f"{tail}_{suffix}"] for row in colorado if np.isfinite(row[f"{tail}_{suffix}"])] for tail in TAILS]
        ax.boxplot(data, tick_labels=("Cold", "Warm"), patch_artist=True, boxprops=dict(facecolor="#F8E9C1"))
        ax.axhline(threshold, color=RED, ls="--", label="Gate tolerance")
        ax.set(title=title, ylabel=ylabel); ax.grid(axis="y", alpha=.15)
    axes[0].legend(frameon=False)
    fig.suptitle("Empirical-background sensitivity", color=NAVY, weight="bold")
    path = FIGURES / "background_sensitivity.png"; fig.savefig(path, dpi=220, facecolor="white"); plt.close(fig); paths.append(path)

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), constrained_layout=True)
    for ax, name, title, units in (
        (axes[0], "delta_d50_cold_minus_warm_km", "Cold - warm d50", "km"),
        (axes[1], "delta_effective_length_cold_minus_warm_km", "Cold - warm L", "km"),
        (axes[2], "delta_beta_cold_minus_warm_per_100km", "Cold - warm beta", "per 100 km"),
    ):
        values = _finite([row[name] for row in colorado])
        ax.hist(values, bins=max(5, min(10, values.size)), color=PURPLE, alpha=.78)
        ax.axvline(0, color=INK, lw=1)
        if values.size: ax.axvline(np.median(values), color=GOLD, lw=2, label=f"Median {np.median(values):.2f}")
        ax.set(title=title, xlabel=units, ylabel="Pilot sites"); ax.legend(frameon=False); ax.grid(axis="y", alpha=.15)
    fig.suptitle("Cold and warm decay properties remain separate contrasts", color=NAVY, weight="bold")
    path = FIGURES / "cold_warm_contrasts.png"; fig.savefig(path, dpi=220, facecolor="white"); plt.close(fig); paths.append(path)
    return paths


def _questions(colorado, representatives, gates, contrasts) -> dict[str, object]:
    old_common = sum(row["previous_common_range_status"] == "resolved" for row in colorado)
    d50_valid = {tail: sum(row[f"{tail}_d50_status"] == 3 for row in colorado) for tail in TAILS}
    d50_rep = {tail: sum(row[f"{tail}_d50_status"] == 3 for row in representatives) for tail in TAILS}
    median_decay_100 = {
        tail: float(np.nanmedian([row[f"{tail}_decay_fraction_100km"] for row in colorado]))
        for tail in TAILS
    }
    multiscale = {
        tail: float(np.mean([
            np.isfinite(row[f"{tail}_beta_near_per_100km"])
            and np.isfinite(row[f"{tail}_beta_far_per_100km"])
            and abs(row[f"{tail}_beta_near_per_100km"]) > abs(row[f"{tail}_beta_far_per_100km"]) + 0.02
            for row in colorado
        ]))
        for tail in TAILS
    }
    return {
        "1_d50_resolves_more_often_than_old_Rstar": {
            "answer": any(value > old_common for value in d50_valid.values()),
            "old_common_Rstar_resolved": old_common,
            "colorado_d50_resolved": d50_valid,
            "representative_d50_resolved": d50_rep,
        },
        "2_d50_stable_to_discovery_radius": {tail: gates["d50"][tail]["discovery_stable_fraction"] for tail in TAILS},
        "3_d50_stable_to_bin_width": {tail: gates["d50"][tail]["bin_stable_fraction"] for tail in TAILS},
        "4_d50_robust_to_background": {tail: gates["d50"][tail]["background_stable_fraction"] for tail in TAILS},
        "5_effective_length_stabilizes": {tail: gates["effective_length"][tail]["discovery_stable_fraction"] for tail in TAILS},
        "6_effective_length_boundary_dependence": {tail: 1.0 - gates["effective_length"][tail]["discovery_stable_fraction"] for tail in TAILS},
        "7_initial_decay_rate_stable": {tail: gates["beta_initial"][tail]["discovery_stable_fraction"] for tail in TAILS},
        "8_initial_rate_background_independent": "yes by definition; beta uses annular medians only and is identical across background choices",
        "9_cold_warm_have_different_scales": contrasts,
        "10_difference_dimensions": {
            "answer": "strength, extent, and decay rate all remain separate; no synthetic index is formed",
            "fixed_strength_delta": _paired_summary(colorado, "fixed_delta_s"),
            "d50_extent_delta": contrasts["delta_d50_cold_minus_warm_km"],
            "effective_length_delta": contrasts["delta_effective_length_cold_minus_warm_km"],
            "initial_rate_delta": contrasts["delta_beta_cold_minus_warm_per_100km"],
        },
        "11_multiscale_evidence_fraction_fast_near_slow_far": multiscale,
        "12_median_fraction_excess_decay_by_100km": median_decay_100,
        "13_support_for_100km_local_summary": "assessed from decay-at-100 and multiscale diagnostics; it remains a local control, not an endpoint",
        "14_metric_ready_for_full_colorado": {metric: value["overall_decision"] for metric, value in gates.items()},
        "15_metric_ready_for_CONUS": "none unless a candidate passes the Colorado gate; CONUS is not run in this task",
    }


def _audit(pair_records: list[dict[str, object]]) -> None:
    lines = [
        "# Audit of retained empirical-range products",
        "",
        "Experiment 1 remains unchanged: the predeclared finite-horizon criterion usually did not resolve within 500 km.",
        "Experiment 2 reads the completed pair checkpoints directly and does not stream PRISM or invoke the pair kernel.",
        "",
        "## Reused checkpoints",
        "",
    ]
    for record in pair_records:
        lines.append(f"- `{record['path']}`: {record['nonself_pair_count']:,} nonself pairs; SHA-256 `{record['sha256']}`.")
    lines.extend(
        [
            "",
            "## Preserved scientific semantics",
            "",
            "- Cold is joint lower-tail TMIN synchrony using inclusive pair-valid medians.",
            "- Warm is joint upper-tail TMAX synchrony using strict `>` pair-valid medians.",
            "- `Delta_S = S_cold - S_warm` remains a strength contrast and is not d50, L, or beta.",
            "- No curve is forced monotonic and no parametric kernel or distance weight is fitted.",
            "- The fixed 100 km products and all Experiment 1 R* outputs remain unchanged.",
        ]
    )
    (OUTPUT / "implementation_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    _json(OUTPUT / "predeclared_gate.json", GATE)
    started = time.perf_counter()
    pair_records = []
    timings = []

    colorado_pairs, record = _load_checkpoint("colorado_25_site_pilot")
    pair_records.append(record)
    colorado_sites = _sites(colorado_pairs)
    colorado_configs, colorado_curves, elapsed = _configuration_results(colorado_pairs, colorado_sites)
    timings.extend({"scope": "Colorado", **row} for row in elapsed)
    colorado_primary = colorado_configs[(PRIMARY_RADIUS, PRIMARY_BIN, PRIMARY_BACKGROUND)]
    colorado_rows = _join_primary(
        colorado_primary,
        colorado_configs,
        _previous_colorado_statuses(),
    )

    representative_rows = []
    representative_sensitivity = []
    representative_figures = []
    previous_rep = _previous_representative_statuses()
    for label, key in REPRESENTATIVE:
        pairs, record = _load_checkpoint(key)
        pair_records.append(record)
        sites = _sites(pairs)
        configs, curves, elapsed_rows = _configuration_results(pairs, sites)
        timings.extend({"scope": label, **row} for row in elapsed_rows)
        primary = configs[(PRIMARY_RADIUS, PRIMARY_BIN, PRIMARY_BACKGROUND)]
        joined = _join_primary(primary, configs, previous_rep, representative_label=label)
        representative_rows.extend(joined)
        representative_sensitivity.extend(_long_sensitivity(label, configs))
        representative_figures.append(_diagnostic_figure(label, pairs, sites[0], joined[0], curves[0]))
        pairs.close()

    gates = {
        metric: _gate_metric(colorado_rows, representative_rows, metric)
        for metric in ("d50", "effective_length", "beta_initial")
    }
    correlations = {
        tail: {
            "d50_vs_L": _correlation(colorado_rows, f"{tail}_d50_km", f"{tail}_effective_length_km"),
            "d50_vs_beta": _correlation(colorado_rows, f"{tail}_d50_km", f"{tail}_beta_initial_per_100km"),
            "L_vs_beta": _correlation(colorado_rows, f"{tail}_effective_length_km", f"{tail}_beta_initial_per_100km"),
        }
        for tail in TAILS
    }
    contrasts = {
        name: _paired_summary(colorado_rows, name)
        for name in (
            "delta_d50_cold_minus_warm_km",
            "delta_effective_length_cold_minus_warm_km",
            "delta_beta_cold_minus_warm_per_100km",
        )
    }
    questions = _questions(colorado_rows, representative_rows, gates, contrasts)
    figures = _pedagogical_figures() + _summary_figures(colorado_rows, gates) + representative_figures

    _csv(OUTPUT / "colorado_25_site_decay_metrics.csv", colorado_rows)
    _csv(OUTPUT / "representative_5_site_decay_metrics.csv", representative_rows)
    _csv(OUTPUT / "colorado_sensitivity_long.csv", _long_sensitivity("Colorado", colorado_configs))
    _csv(OUTPUT / "representative_sensitivity_long.csv", representative_sensitivity)
    _json(OUTPUT / "pair_reuse_manifest.json", pair_records)
    _json(OUTPUT / "metric_gates.json", gates)
    _json(OUTPUT / "metric_correlations.json", correlations)
    _json(OUTPUT / "final_questions.json", questions)
    _json(
        OUTPUT / "summary.json",
        {
            "status": "complete",
            "experiment_1": "finite synchrony horizon usually unresolved; preserved unchanged",
            "experiment_2": "empirical decay characterization from retained pair tables",
            "metric_decisions": {name: gate["overall_decision"] for name, gate in gates.items()},
            "colorado_site_count": len(colorado_rows),
            "representative_site_count": len(representative_rows),
            "pair_relationships_reused": int(sum(record["nonself_pair_count"] for record in pair_records)),
            "colorado_nonself_pairs_reused": int(pair_records[0]["nonself_pair_count"]),
            "pair_recomputation_performed": False,
            "full_colorado_or_conus_run_performed": False,
            "correlations": correlations,
            "cold_warm_contrasts": contrasts,
            "questions": questions,
            "figures": [str(path.relative_to(ROOT)) for path in figures],
            "reproduction_command": ".venv/bin/python scripts/run_empirical_synchrony_decay_pilot.py",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    _json(
        OUTPUT / "performance.json",
        {
            "analysis_wall_seconds": time.perf_counter() - started,
            "configuration_timings": timings,
            "pair_kernel_invocations": 0,
            "network_or_PRISM_streaming": False,
        },
    )
    _audit(pair_records)
    (OUTPUT / "REPRODUCE.md").write_text(
        "# Reproduce empirical synchrony-decay pilot\n\n"
        "This command reuses the retained, SHA-validated pair checkpoints and does not restream PRISM:\n\n"
        "```bash\n.venv/bin/python scripts/run_empirical_synchrony_decay_pilot.py\n```\n",
        encoding="utf-8",
    )
    status_text = subprocess.run(
        ["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    diff_text = subprocess.run(
        ["git", "diff", "--stat"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    (OUTPUT / "git_diff_summary.txt").write_text(
        "# Working-tree status (includes untracked files)\n"
        + status_text
        + "\n# Tracked diff summary\n"
        + diff_text,
        encoding="utf-8",
    )
    colorado_pairs.close()
    print(json.dumps({"status": "PASS", "metric_decisions": {k: v["overall_decision"] for k, v in gates.items()}, "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
