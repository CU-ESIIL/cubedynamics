"""Four-round empirical synchrony-scale experiment.

This module separates the 1000 km observation domain from the estimated local
break.  It consumes reusable pair relationships, detects the first robust
local-to-regional transition independently for cold and warm synchrony, and
compares one common adaptive neighborhood with a fixed 500 km control.
"""

from __future__ import annotations

from hashlib import sha256
import json
import time
from typing import Sequence

import numpy as np
import xarray as xr


BREAK_STATUS = {
    0: "insufficient_support",
    1: "flat_or_no_local_decay",
    2: "right_censored_beyond_domain",
    3: "unstable",
    4: "ambiguous",
    5: "resolved",
    6: "resolved_multiple_breaks",
}
VALID_BREAK_CODES = (5, 6)


def _weighted_quantile(
    values: np.ndarray,
    quantiles: float | Sequence[float],
    weights: np.ndarray,
) -> np.ndarray | float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    q = np.atleast_1d(np.asarray(quantiles, dtype=float))
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(valid):
        result = np.full(q.shape, np.nan)
    else:
        order = np.argsort(values[valid], kind="stable")
        observed = values[valid][order]
        mass = weights[valid][order]
        centers = (np.cumsum(mass) - 0.5 * mass) / np.sum(mass)
        result = np.interp(q, centers, observed, left=observed[0], right=observed[-1])
    return float(result[0]) if np.ndim(quantiles) == 0 else result


def _theil_sen_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    slopes = []
    for index in range(x.size - 1):
        dx = x[index + 1 :] - x[index]
        valid = dx != 0
        slopes.extend(((y[index + 1 :][valid] - y[index]) / dx[valid]).tolist())
    slope = float(np.median(slopes)) if slopes else 0.0
    intercept = float(np.median(y - slope * x))
    return slope, intercept


def _centered_running_median(values: np.ndarray, width: int) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    if width <= 1:
        return result
    half = width // 2
    for index in range(values.size):
        local = values[max(0, index - half) : min(values.size, index + half + 1)]
        finite = local[np.isfinite(local)]
        result[index] = np.median(finite) if finite.size else np.nan
    return result


def _line_error(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    slope, intercept = _theil_sen_line(x, y)
    error = float(np.median(np.abs(y - (intercept + slope * x))))
    return slope, intercept, error


def _segmented_candidates(
    x: np.ndarray,
    y: np.ndarray,
    *,
    min_break_km: float,
    max_break_km: float,
    min_segment_bins: int,
) -> list[dict[str, float]]:
    _, _, one_error = _line_error(x, y)
    candidates: list[dict[str, float]] = []
    for split in range(min_segment_bins, x.size - min_segment_bins + 1):
        break_km = float((x[split - 1] + x[split]) / 2.0)
        if break_km < min_break_km or break_km > max_break_km:
            continue
        near_slope, near_intercept, near_error = _line_error(x[:split], y[:split])
        far_slope, far_intercept, far_error = _line_error(x[split:], y[split:])
        fitted = np.concatenate(
            (
                near_intercept + near_slope * x[:split],
                far_intercept + far_slope * x[split:],
            )
        )
        error = float(np.median(np.abs(y - fitted)))
        improvement = 1.0 - error / max(one_error, 1e-12)
        candidates.append(
            {
                "split": float(split),
                "break_km": break_km,
                "near_slope_per_100km": near_slope * 100.0,
                "far_slope_per_100km": far_slope * 100.0,
                "slope_change_per_100km": (far_slope - near_slope) * 100.0,
                "error": error,
                "single_line_error": one_error,
                "improvement": improvement,
                "near_error": near_error,
                "far_error": far_error,
            }
        )
    return candidates


def empirical_break_curve(
    distance_km: np.ndarray,
    synchrony: np.ndarray,
    *,
    sampling_probability: np.ndarray | None = None,
    discovery_radius_km: float = 1000.0,
    bin_width_km: float = 25.0,
    min_annulus_count: int = 30,
    smoothing_bins: int = 3,
    min_segment_bins: int = 3,
    min_break_km: float = 50.0,
    max_break_fraction: float = 0.85,
    min_improvement: float = 0.15,
    min_near_decay_per_100km: float = 0.01,
    min_slope_change_per_100km: float = 0.015,
    ambiguity_fraction: float = 0.10,
) -> xr.Dataset:
    """Estimate a first empirical local-to-regional break without a kernel.

    Raw annular medians remain available.  A centered running median is used
    only for candidate placement.  The primary candidate minimizes robust
    two-segment absolute error and must improve on one robust line while moving
    from a decaying near field toward a flatter far field.
    """

    distance = np.asarray(distance_km, dtype=float)
    values = np.asarray(synchrony, dtype=float)
    if distance.shape != values.shape:
        raise ValueError("distance_km and synchrony must have matching shapes")
    if discovery_radius_km <= 0 or bin_width_km <= 0:
        raise ValueError("discovery_radius_km and bin_width_km must be positive")
    if smoothing_bins < 1 or smoothing_bins % 2 == 0:
        raise ValueError("smoothing_bins must be a positive odd integer")
    probability = (
        np.ones(distance.shape, dtype=float)
        if sampling_probability is None
        else np.asarray(sampling_probability, dtype=float)
    )
    if probability.shape != distance.shape:
        raise ValueError("sampling_probability must match distance_km")
    valid = (
        (distance > 0)
        & (distance <= discovery_radius_km + 1e-7)
        & np.isfinite(values)
        & np.isfinite(probability)
        & (probability > 0)
        & (probability <= 1)
    )
    distance = distance[valid]
    values = values[valid]
    weights = 1.0 / probability[valid]

    edges = np.arange(0.0, discovery_radius_km + bin_width_km, bin_width_km)
    if edges[-1] > discovery_radius_km:
        edges[-1] = discovery_radius_km
    elif edges[-1] < discovery_radius_km:
        edges = np.append(edges, discovery_radius_km)
    centers = (edges[:-1] + edges[1:]) / 2.0
    count = np.zeros(centers.size, dtype=np.int32)
    estimated_count = np.zeros(centers.size, dtype=float)
    q25 = np.full(centers.size, np.nan)
    median = np.full(centers.size, np.nan)
    q75 = np.full(centers.size, np.nan)
    for index, (lower, upper) in enumerate(zip(edges[:-1], edges[1:])):
        above_lower = distance > lower if index else distance > 0
        selected = above_lower & (distance <= upper + 1e-7)
        count[index] = int(np.count_nonzero(selected))
        if count[index] < min_annulus_count:
            continue
        estimated_count[index] = float(np.sum(weights[selected]))
        q25[index], median[index], q75[index] = _weighted_quantile(
            values[selected], (0.25, 0.5, 0.75), weights[selected]
        )
    smoothed = _centered_running_median(median, smoothing_bins)
    supported = np.isfinite(smoothed)
    sx = centers[supported]
    sy = smoothed[supported]

    status = 0
    primary = np.nan
    uncertainty = np.nan
    improvement = np.nan
    near_slope = np.nan
    far_slope = np.nan
    slope_change = np.nan
    multiple_break_count = 0
    segmented = np.nan
    candidates: list[dict[str, float]] = []
    if sx.size >= max(2 * min_segment_bins, 7):
        candidates = _segmented_candidates(
            sx,
            sy,
            min_break_km=min_break_km,
            max_break_km=max_break_fraction * discovery_radius_km,
            min_segment_bins=min_segment_bins,
        )
        eligible = [
            item
            for item in candidates
            if item["improvement"] >= min_improvement
            and item["near_slope_per_100km"] <= -min_near_decay_per_100km
            and item["slope_change_per_100km"] >= min_slope_change_per_100km
        ]
        if eligible:
            best = min(eligible, key=lambda item: (item["error"], item["break_km"]))
            segmented = best["break_km"]
            comparable = [
                item
                for item in eligible
                if item["error"] <= best["error"] * (1.0 + ambiguity_fraction) + 1e-12
            ]
            locations = np.asarray([item["break_km"] for item in comparable])
            uncertainty = max(bin_width_km / 2.0, float(np.ptp(locations) / 2.0))
            separated = np.any(np.abs(locations - best["break_km"]) > 2 * bin_width_km)
            if separated:
                status = 4
            else:
                status = 5
                primary = best["break_km"]
            improvement = best["improvement"]
            near_slope = best["near_slope_per_100km"]
            far_slope = best["far_slope_per_100km"]
            slope_change = best["slope_change_per_100km"]

            split = int(best["split"])
            if status == 5 and sx.size - split >= 2 * min_segment_bins:
                later = _segmented_candidates(
                    sx[split:],
                    sy[split:],
                    min_break_km=float(sx[split] + min_break_km),
                    max_break_km=max_break_fraction * discovery_radius_km,
                    min_segment_bins=min_segment_bins,
                )
                later_valid = [
                    item
                    for item in later
                    if item["improvement"] >= min_improvement
                    and abs(item["slope_change_per_100km"]) >= min_slope_change_per_100km
                ]
                if later_valid:
                    status = 6
                    multiple_break_count = 2
                else:
                    multiple_break_count = 1
        else:
            overall_slope, _, _ = _line_error(sx, sy)
            profile_range = float(np.nanmax(sy) - np.nanmin(sy))
            if overall_slope * 100 <= -min_near_decay_per_100km:
                status = 2
            elif profile_range < min_slope_change_per_100km:
                status = 1
            else:
                status = 4

    knee = np.nan
    derivative_break = np.nan
    d50 = np.nan
    background_break = np.nan
    if sx.size >= 4:
        x_norm = (sx - sx[0]) / max(sx[-1] - sx[0], 1e-12)
        y_norm = (sy - sy[0]) / max(np.ptp(sy), 1e-12)
        chord = y_norm[0] + (y_norm[-1] - y_norm[0]) * x_norm
        knee = float(sx[np.argmax(np.abs(y_norm - chord))])
        local_slopes = np.diff(sy) / np.diff(sx) * 100.0
        if local_slopes.size >= 2:
            derivative_break = float(sx[1:-1][np.argmax(np.diff(local_slopes))])
        local = _weighted_quantile(values[distance <= min(50.0, discovery_radius_km)], 0.5, weights[distance <= min(50.0, discovery_radius_km)])
        outer = _weighted_quantile(values[distance >= 0.8 * discovery_radius_km], 0.5, weights[distance >= 0.8 * discovery_radius_km])
        if np.isfinite(local) and np.isfinite(outer) and local > outer:
            target = outer + 0.5 * (local - outer)
            crossed = sy <= target
            for index in range(crossed.size - 1):
                if crossed[index] and crossed[index + 1]:
                    d50 = float(sx[index])
                    break
            tolerance = max(0.03, 0.1 * (local - outer))
            approached = np.abs(sy - outer) <= tolerance
            for index in range(approached.size - 1):
                if approached[index] and approached[index + 1]:
                    background_break = float(sx[index])
                    break

    result = xr.Dataset(
        {
            "annular_median": ("radius_km", median.astype(np.float32)),
            "annular_q25": ("radius_km", q25.astype(np.float32)),
            "annular_q75": ("radius_km", q75.astype(np.float32)),
            "annular_iqr": ("radius_km", (q75 - q25).astype(np.float32)),
            "annular_count": ("radius_km", count),
            "annular_estimated_population": ("radius_km", estimated_count.astype(np.float32)),
            "smoothed_annular_median": ("radius_km", smoothed.astype(np.float32)),
        },
        coords={
            "radius_km": centers,
            "radius_lower_km": ("radius_km", edges[:-1]),
            "radius_upper_km": ("radius_km", edges[1:]),
        },
        attrs={
            "break_km": float(primary),
            "break_status": int(status),
            "break_status_label": BREAK_STATUS[status],
            "break_uncertainty_km": float(uncertainty),
            "segmented_candidate_km": float(segmented),
            "knee_candidate_km": float(knee),
            "derivative_candidate_km": float(derivative_break),
            "d50_candidate_km": float(d50),
            "background_approach_candidate_km": float(background_break),
            "segmented_improvement": float(improvement),
            "near_slope_per_100km": float(near_slope),
            "far_slope_per_100km": float(far_slope),
            "slope_change_per_100km": float(slope_change),
            "multiple_break_count": int(multiple_break_count),
            "discovery_radius_km": float(discovery_radius_km),
            "bin_width_km": float(bin_width_km),
            "smoothing_bins": int(smoothing_bins),
            "estimator": "first robust two-segment local-to-regional transition",
            "parametric_kernel": "none",
            "monotonicity_forced": "no",
        },
    )
    return result


def _incident_pairs(pairs: xr.Dataset, node: int) -> np.ndarray:
    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    return np.flatnonzero(((source == node) | (target == node)) & (source != target))


def _weighted_reduction(
    cold: np.ndarray,
    warm: np.ndarray,
    delta: np.ndarray,
    weights: np.ndarray,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for name, values in (("cold", cold), ("warm", warm), ("delta", delta)):
        valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
        if not np.any(valid):
            result[f"{name}_median"] = np.nan
            result[f"{name}_iqr"] = np.nan
            result[f"{name}_valid_pair_count"] = 0.0
            result[f"{name}_estimated_pair_count"] = 0.0
            continue
        q25, q50, q75 = _weighted_quantile(
            values[valid], (0.25, 0.5, 0.75), weights[valid]
        )
        result[f"{name}_median"] = float(q50)
        result[f"{name}_iqr"] = float(q75 - q25)
        result[f"{name}_valid_pair_count"] = float(np.count_nonzero(valid))
        result[f"{name}_estimated_pair_count"] = float(np.sum(weights[valid]))
    expected = float(np.sum(weights[np.isfinite(weights) & (weights > 0)]))
    result["observed_pair_count"] = float(weights.size)
    result["estimated_pair_count"] = expected
    result["valid_pair_fraction"] = (
        result["delta_estimated_pair_count"] / expected if expected else np.nan
    )
    result["delta_median_difference"] = result["cold_median"] - result["warm_median"]
    result["delta_reduction_gap"] = (
        result["delta_median"] - result["delta_median_difference"]
    )
    return result


def adaptive_synchrony_experiment(
    pairs: xr.Dataset,
    *,
    discovery_radius_km: float = 1000.0,
    fixed_radius_km: float = 500.0,
    bin_width_km: float = 25.0,
    min_annulus_count: int = 30,
    smoothing_bins: int = 3,
    common_rule: str = "max",
    time_window_id: str | None = None,
) -> xr.Dataset:
    """Run discovery, adaptive reduction, and fixed comparison from one pair table."""

    required = {
        "cold_synchrony",
        "warm_synchrony",
        "delta_s",
        "distance_km",
        "source_index",
        "target_index",
        "output_mask",
    }
    missing = sorted(required.difference(pairs.variables))
    if missing or pairs.attrs.get("analysis") != "local_synchrony_pairs":
        raise TypeError(f"Expected a local_synchrony_pairs Dataset; missing={missing}")
    available = float(pairs.attrs["max_radius_km"])
    if discovery_radius_km > available + 1e-7 or fixed_radius_km > discovery_radius_km:
        raise ValueError("fixed and discovery radii must be within pair-table support")
    if common_rule not in {"max", "mean", "min"}:
        raise ValueError("common_rule must be max, mean, or min")

    started = time.perf_counter()
    y_dim, x_dim = pairs.output_mask.dims
    y_size, x_size = pairs.sizes[y_dim], pairs.sizes[x_dim]
    node_count = y_size * x_size
    output = np.asarray(pairs.output_mask.values, dtype=bool).reshape(-1)
    bins = int(np.ceil(discovery_radius_km / bin_width_km))
    centers = (np.arange(bins, dtype=float) + 0.5) * bin_width_km
    centers[-1] = (min((bins - 1) * bin_width_km, discovery_radius_km) + discovery_radius_km) / 2
    radial_names = (
        "annular_median",
        "annular_q25",
        "annular_q75",
        "annular_iqr",
        "annular_count",
        "annular_estimated_population",
        "smoothed_annular_median",
    )
    radial = {
        f"{tail}_{name}": np.full((bins, node_count), np.nan, dtype=np.float32)
        for tail in ("cold", "warm")
        for name in radial_names
    }
    for tail in ("cold", "warm"):
        radial[f"{tail}_annular_count"] = np.zeros((bins, node_count), dtype=np.int32)

    scalar_names = (
        "break_km",
        "break_uncertainty_km",
        "segmented_candidate_km",
        "knee_candidate_km",
        "derivative_candidate_km",
        "d50_candidate_km",
        "background_approach_candidate_km",
        "segmented_improvement",
        "near_slope_per_100km",
        "far_slope_per_100km",
        "slope_change_per_100km",
        "multiple_break_count",
    )
    scalar = {
        f"{tail}_{name}": np.full(node_count, np.nan, dtype=float)
        for tail in ("cold", "warm")
        for name in scalar_names
    }
    status = {
        "cold_break_status": np.zeros(node_count, dtype=np.int8),
        "warm_break_status": np.zeros(node_count, dtype=np.int8),
        "common_break_status": np.zeros(node_count, dtype=np.int8),
    }
    common_break = np.full(node_count, np.nan)
    common_uncertainty = np.full(node_count, np.nan)
    delta_r = np.full(node_count, np.nan)

    reduction_fields = (
        "cold_median",
        "warm_median",
        "delta_median",
        "cold_iqr",
        "warm_iqr",
        "delta_iqr",
        "cold_valid_pair_count",
        "warm_valid_pair_count",
        "delta_valid_pair_count",
        "cold_estimated_pair_count",
        "warm_estimated_pair_count",
        "delta_estimated_pair_count",
        "observed_pair_count",
        "estimated_pair_count",
        "valid_pair_fraction",
        "delta_median_difference",
        "delta_reduction_gap",
    )
    reductions = {
        f"{domain}_{name}": np.full(node_count, np.nan)
        for domain in ("fixed", "adaptive")
        for name in reduction_fields
    }
    distance = np.asarray(pairs.distance_km.values, dtype=float)
    probability = (
        np.asarray(pairs.sampling_probability.values, dtype=float)
        if "sampling_probability" in pairs
        else np.ones(distance.shape, dtype=float)
    )
    values = {
        name: np.asarray(pairs[name].values, dtype=float)
        for name in ("cold_synchrony", "warm_synchrony", "delta_s")
    }

    for node in np.flatnonzero(output):
        selected = _incident_pairs(pairs, int(node))
        local_distance = distance[selected]
        local_probability = probability[selected]
        for tail, variable in (("cold", "cold_synchrony"), ("warm", "warm_synchrony")):
            curve = empirical_break_curve(
                local_distance,
                values[variable][selected],
                sampling_probability=local_probability,
                discovery_radius_km=discovery_radius_km,
                bin_width_km=bin_width_km,
                min_annulus_count=min_annulus_count,
                smoothing_bins=smoothing_bins,
            )
            for name in radial_names:
                radial[f"{tail}_{name}"][:, node] = np.asarray(curve[name].values)
            for name in scalar_names:
                scalar[f"{tail}_{name}"][node] = float(curve.attrs[name])
            status[f"{tail}_break_status"][node] = int(curve.attrs["break_status"])

        cold_valid = status["cold_break_status"][node] in VALID_BREAK_CODES
        warm_valid = status["warm_break_status"][node] in VALID_BREAK_CODES
        if cold_valid and warm_valid:
            cold_break = scalar["cold_break_km"][node]
            warm_break = scalar["warm_break_km"][node]
            common_break[node] = {
                "max": max,
                "min": min,
                "mean": lambda a, b: (a + b) / 2.0,
            }[common_rule](cold_break, warm_break)
            common_uncertainty[node] = max(
                scalar["cold_break_uncertainty_km"][node],
                scalar["warm_break_uncertainty_km"][node],
            )
            delta_r[node] = cold_break - warm_break
            status["common_break_status"][node] = (
                6
                if status["cold_break_status"][node] == 6
                or status["warm_break_status"][node] == 6
                else 5
            )
        else:
            component_codes = (
                status["cold_break_status"][node],
                status["warm_break_status"][node],
            )
            for priority in (3, 4, 2, 1, 0):
                if priority in component_codes:
                    status["common_break_status"][node] = priority
                    break

        for domain, radius in (("fixed", fixed_radius_km), ("adaptive", common_break[node])):
            if not np.isfinite(radius):
                continue
            within = local_distance <= radius + 1e-7
            local = _weighted_reduction(
                values["cold_synchrony"][selected][within],
                values["warm_synchrony"][selected][within],
                values["delta_s"][selected][within],
                1.0 / local_probability[within],
            )
            for name, value in local.items():
                reductions[f"{domain}_{name}"][node] = value

    difference = {
        "cold_difference_adaptive_minus_fixed": reductions["adaptive_cold_median"]
        - reductions["fixed_cold_median"],
        "warm_difference_adaptive_minus_fixed": reductions["adaptive_warm_median"]
        - reductions["fixed_warm_median"],
        "delta_difference_adaptive_minus_fixed": reductions["adaptive_delta_median"]
        - reductions["fixed_delta_median"],
    }
    sign_change = np.full(node_count, -1, dtype=np.int8)
    valid_sign = np.isfinite(reductions["adaptive_delta_median"]) & np.isfinite(
        reductions["fixed_delta_median"]
    )
    sign_change[valid_sign] = (
        np.sign(reductions["adaptive_delta_median"][valid_sign])
        != np.sign(reductions["fixed_delta_median"][valid_sign])
    ).astype(np.int8)

    time_value = np.datetime64(pairs.time_window_end.values)
    dims = ("time_window_end", y_dim, x_dim)
    radial_dims = ("time_window_end", "radius_km", y_dim, x_dim)
    data_vars: dict[str, tuple] = {
        name: (radial_dims, array.reshape((1, bins, y_size, x_size)))
        for name, array in radial.items()
    }
    all_scalar = {
        **scalar,
        **status,
        **reductions,
        **difference,
        "common_break_km": common_break,
        "common_break_uncertainty_km": common_uncertainty,
        "delta_r_cold_minus_warm_km": delta_r,
        "delta_sign_change": sign_change,
    }
    data_vars.update(
        {
            name: (dims, array.reshape((1, y_size, x_size)))
            for name, array in all_scalar.items()
        }
    )
    data_vars["output_mask"] = ((y_dim, x_dim), np.asarray(pairs.output_mask.values))
    result = xr.Dataset(
        data_vars,
        coords={
            "time_window_end": [time_value],
            "radius_km": centers,
            y_dim: pairs[y_dim],
            x_dim: pairs[x_dim],
        },
    )
    result["delta_r_cold_minus_warm_km"].attrs.update(
        {
            "units": "km",
            "definition": "cold empirical break minus warm empirical break",
            "positive": "cold synchrony extends farther",
            "negative": "warm synchrony extends farther",
        }
    )
    result["adaptive_delta_median"].attrs["definition"] = (
        "design-weighted median of pairwise cold_synchrony - warm_synchrony within common break"
    )
    result["fixed_delta_median"].attrs["definition"] = (
        "design-weighted median of pairwise cold_synchrony - warm_synchrony within fixed radius"
    )
    for name in status:
        result[name].attrs["labels"] = json.dumps(BREAK_STATUS, sort_keys=True)
    window_id = time_window_id or str(time_value)
    fingerprint_payload = {
        "source_pair_fingerprint": pairs.attrs.get("analysis_fingerprint"),
        "discovery_radius_km": discovery_radius_km,
        "fixed_radius_km": fixed_radius_km,
        "bin_width_km": bin_width_km,
        "min_annulus_count": min_annulus_count,
        "smoothing_bins": smoothing_bins,
        "common_rule": common_rule,
        "time_window_id": window_id,
    }
    fingerprint = sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result.attrs.update(dict(pairs.attrs))
    result.attrs.update(
        {
            "analysis": "adaptive_synchrony_experiment",
            "semantic_kind": "summary",
            "analysis_fingerprint": f"sha256:{fingerprint}",
            "source_pair_fingerprint": pairs.attrs.get("analysis_fingerprint", "unknown"),
            "time_window_id": window_id,
            "maximum_discovery_radius_km": float(discovery_radius_km),
            "maximum_discovery_radius_role": "standardized observation domain, not estimated scale",
            "fixed_comparison_radius_km": float(fixed_radius_km),
            "break_estimator": "first robust two-segment local-to-regional transition",
            "break_estimator_parameters": json.dumps(
                {
                    "bin_width_km": bin_width_km,
                    "min_annulus_count": min_annulus_count,
                    "smoothing_bins": smoothing_bins,
                },
                sort_keys=True,
            ),
            "common_radius_rule": common_rule,
            "reduction_statistic": "design-weighted empirical median; Delta reduced pairwise",
            "distance_sampling_design": pairs.attrs.get(
                "distance_sampling_design", "dense all eligible pairs"
            ),
            "distance_units": "km",
            "parametric_kernel": "none",
            "monotonicity_forced": "no",
            "adaptive_reduction_seconds": float(time.perf_counter() - started),
            "temporal_extension": (
                "repeat by time_window_id, then summarize median/IQR/trend over time"
            ),
        }
    )
    return result


__all__ = [
    "BREAK_STATUS",
    "VALID_BREAK_CODES",
    "adaptive_synchrony_experiment",
    "empirical_break_curve",
]
