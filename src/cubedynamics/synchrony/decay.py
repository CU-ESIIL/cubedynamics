"""Empirical, kernel-agnostic summaries of synchrony decay with distance.

This module characterizes the shape of saved pairwise synchrony-distance
relationships. It does not infer a hard neighborhood boundary and does not fit
an exponential, Gaussian, power-law, or other parametric kernel.
"""

from __future__ import annotations

import json
from typing import Literal, Sequence

import numpy as np
import xarray as xr

from .ranges import _curve_summary, _smooth_supported, _validate_config, _validate_pairs


DECAY_STATUS = {
    0: "insufficient_support",
    1: "nonpositive_local_excess",
    2: "right_censored_or_boundary_dependent",
    3: "resolved",
}

_TAILS = {"cold": "cold_synchrony", "warm": "warm_synchrony"}
_FRACTIONS = (25, 50, 75)


def empirical_decay_curve(
    distance_km,
    synchrony,
    *,
    discovery_radius_km: float,
    bin_width_km: float = 20.0,
    min_annulus_count: int = 30,
    background_shell_count: int = 4,
    background_method: Literal[
        "outer_annuli", "smoothed_outer_annuli", "distant_pairs"
    ] = "outer_annuli",
    local_shell_count: int = 2,
    crossing_persistence_bins: int = 2,
    min_local_excess: float = 0.04,
    initial_window_km: float = 100.0,
    initial_windows_km: Sequence[float] = (50.0, 100.0, 150.0, 200.0),
) -> xr.Dataset:
    """Characterize one empirical synchrony-distance curve.

    Fractional distances use a centered three-annulus median smoother and a
    persistent empirical crossing; the original annular curve is retained and
    is never forced to be monotonic. ``L`` is the positive area under the
    normalized excess curve. Initial slopes are Theil-Sen medians of pairwise
    slopes among supported annular medians and do not require a background.
    """

    if local_shell_count < 1:
        raise ValueError("local_shell_count must be at least 1")
    if crossing_persistence_bins < 1:
        raise ValueError("crossing_persistence_bins must be at least 1")
    if min_local_excess < 0:
        raise ValueError("min_local_excess must be non-negative")
    windows = tuple(float(value) for value in initial_windows_km)
    if not windows or any(value <= 0 for value in windows):
        raise ValueError("initial_windows_km must contain positive distances")
    if initial_window_km <= 0:
        raise ValueError("initial_window_km must be positive")

    config = _validate_config(
        discovery_radius_km=discovery_radius_km,
        bin_width_km=bin_width_km,
        min_annulus_count=min_annulus_count,
        background_shell_count=background_shell_count,
        background_method=background_method,
        persistence_bins=max(2, crossing_persistence_bins),
        annular_abs_tolerance=0.03,
        cumulative_abs_tolerance=0.01,
        min_profile_range=min_local_excess,
        censor_fraction=0.80,
    )
    summary = _curve_summary(
        np.asarray(distance_km, dtype=float),
        np.asarray(synchrony, dtype=float),
        **config,
    )
    edges = np.asarray(config["edges"], dtype=float)
    centers = (edges[:-1] + edges[1:]) / 2.0
    annular = np.asarray(summary["annular_median"], dtype=float)
    counts = np.asarray(summary["annular_count"], dtype=np.int32)
    supported = np.isfinite(annular) & (counts >= min_annulus_count)
    smoothed = _smooth_supported(annular)
    supported_index = np.flatnonzero(supported)

    local_sync = background = local_excess = float("nan")
    normalized = np.full(centers.size, np.nan, dtype=float)
    fractional = {fraction: (float("nan"), 0) for fraction in _FRACTIONS}
    effective_length = boundary_excess = tail_fraction = float("nan")
    effective_status = 0

    if supported_index.size >= max(local_shell_count, background_shell_count):
        near_index = supported_index[:local_shell_count]
        local_sync = float(np.median(annular[near_index]))
        background = float(summary["selected_background"])
        local_excess = local_sync - background
        if np.isfinite(local_excess) and local_excess >= min_local_excess:
            normalized[supported] = (smoothed[supported] - background) / local_excess
            for fraction in _FRACTIONS:
                fractional[fraction] = _fractional_crossing(
                    centers,
                    normalized,
                    supported,
                    target=1.0 - fraction / 100.0,
                    persistence_bins=crossing_persistence_bins,
                )
            effective_length, boundary_excess, tail_fraction = _effective_length(
                centers,
                normalized,
                supported,
                float(discovery_radius_km),
            )
            if np.isfinite(effective_length):
                boundary_dependent = boundary_excess > 0.10 or tail_fraction > 0.15
                effective_status = 2 if boundary_dependent else 3
        else:
            fractional = {fraction: (float("nan"), 1) for fraction in _FRACTIONS}
            effective_status = 1

    slope_rows = {
        window: _theil_sen_annular(centers, annular, supported, 0.0, window)
        for window in windows
    }
    initial = _theil_sen_annular(
        centers, annular, supported, 0.0, float(initial_window_km)
    )
    near = _theil_sen_annular(centers, annular, supported, 0.0, 100.0)
    mid = _theil_sen_annular(centers, annular, supported, 100.0, 300.0)
    far = _theil_sen_annular(centers, annular, supported, 300.0, 500.0)

    at_100 = _interpolate_supported(centers, smoothed, supported, 100.0)
    excess_remaining_100 = (
        (at_100 - background) / local_excess
        if np.isfinite(at_100) and np.isfinite(local_excess) and local_excess > 0
        else float("nan")
    )
    decay_fraction_100 = (
        1.0 - excess_remaining_100 if np.isfinite(excess_remaining_100) else float("nan")
    )
    first_half = _median_between(centers, annular, supported, 0.0, 50.0)
    second_half = _median_between(centers, annular, supported, 50.0, 100.0)
    local_drop = (
        first_half - second_half
        if np.isfinite(first_half) and np.isfinite(second_half)
        else float("nan")
    )

    result = xr.Dataset(
        {
            "annular_median": ("radial_bin", annular.astype(np.float32)),
            "annular_q25": ("radial_bin", np.asarray(summary["annular_q25"], dtype=np.float32)),
            "annular_q75": ("radial_bin", np.asarray(summary["annular_q75"], dtype=np.float32)),
            "annular_iqr": ("radial_bin", np.asarray(summary["annular_iqr"], dtype=np.float32)),
            "annular_count": ("radial_bin", counts),
            "cumulative_median": ("radial_bin", np.asarray(summary["cumulative_median"], dtype=np.float32)),
            "smoothed_annular_median": ("radial_bin", smoothed.astype(np.float32)),
            "normalized_excess": ("radial_bin", normalized.astype(np.float32)),
        },
        coords={
            "radial_bin": np.arange(centers.size, dtype=np.int32),
            "radius_lower_km": ("radial_bin", edges[:-1]),
            "radius_upper_km": ("radial_bin", edges[1:]),
            "radius_km": ("radial_bin", centers),
        },
        attrs={
            "local_synchrony": local_sync,
            "selected_background": background,
            "local_excess": local_excess,
            "effective_length_km": effective_length,
            "effective_length_status": effective_status,
            "boundary_normalized_excess": boundary_excess,
            "last_100km_area_fraction": tail_fraction,
            "beta_initial_per_100km": initial[0],
            "beta_initial_fit_score": initial[1],
            "beta_initial_status": initial[2],
            "beta_near_per_100km": near[0],
            "beta_mid_per_100km": mid[0],
            "beta_far_per_100km": far[0],
            "excess_remaining_100km": excess_remaining_100,
            "decay_fraction_100km": decay_fraction_100,
            "local_drop_0_50_to_50_100": local_drop,
            "background_method": background_method,
            "background_outer_annuli": float(summary["background_outer_annuli"]),
            "background_smoothed_outer_annuli": float(summary["background_smoothed_outer_annuli"]),
            "background_distant_pairs": float(summary["background_distant_pairs"]),
            "curve_is_monotonicized": False,
            "fractional_crossing_rule": (
                "centered three-annulus median; linear interpolation at the first "
                "crossing supported by consecutive bins and at least 70% later agreement"
            ),
            "effective_length_definition": (
                "trapezoidal integral of positive normalized excess from 0 to discovery radius"
            ),
            "initial_slope_definition": (
                "Theil-Sen median slope of supported annular medians; units per 100 km"
            ),
        },
    )
    for fraction, (distance, status) in fractional.items():
        result.attrs[f"d{fraction}_km"] = distance
        result.attrs[f"d{fraction}_status"] = status
    for window, (slope, score, status) in slope_rows.items():
        label = int(window) if float(window).is_integer() else str(window).replace(".", "p")
        result.attrs[f"beta_0_{label}_per_100km"] = slope
        result.attrs[f"beta_0_{label}_fit_score"] = score
        result.attrs[f"beta_0_{label}_status"] = status
    return result


def empirical_synchrony_decay(
    pairs: xr.Dataset,
    *,
    discovery_radius_km: float | None = None,
    bin_width_km: float = 20.0,
    min_annulus_count: int = 30,
    background_shell_count: int = 4,
    background_method: Literal[
        "outer_annuli", "smoothed_outer_annuli", "distant_pairs"
    ] = "outer_annuli",
    local_shell_count: int = 2,
    crossing_persistence_bins: int = 2,
    min_local_excess: float = 0.04,
    initial_window_km: float = 100.0,
) -> xr.Dataset:
    """Characterize cold and warm decay from an existing canonical pair table."""

    _validate_pairs(pairs)
    available = float(pairs.attrs["max_radius_km"])
    discovery = available if discovery_radius_km is None else float(discovery_radius_km)
    if discovery <= 0 or discovery > available + 1e-7:
        raise ValueError("discovery_radius_km must be positive and within pair support")

    y_dim, x_dim = pairs.output_mask.dims
    y_size, x_size = pairs.sizes[y_dim], pairs.sizes[x_dim]
    node_count = y_size * x_size
    output = np.asarray(pairs.output_mask.values, dtype=bool).reshape(-1)
    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    nonself = source != target
    source_selected = output[source] & nonself
    target_selected = output[target] & nonself
    contribution_node = np.concatenate((source[source_selected], target[target_selected]))
    contribution_pair = np.concatenate(
        (np.flatnonzero(source_selected), np.flatnonzero(target_selected))
    )
    order = np.argsort(contribution_node, kind="stable")
    contribution_node = contribution_node[order]
    contribution_pair = contribution_pair[order]
    unique_nodes, starts, counts = np.unique(
        contribution_node, return_index=True, return_counts=True
    )
    lookup = {
        int(node): (int(start), int(count))
        for node, start, count in zip(unique_nodes, starts, counts)
    }

    edges = np.arange(0.0, discovery + bin_width_km, bin_width_km, dtype=float)
    if edges[-1] > discovery:
        edges[-1] = discovery
    elif edges[-1] < discovery:
        edges = np.append(edges, discovery)
    bins = edges.size - 1
    radial_names = (
        "annular_median", "annular_q25", "annular_q75", "annular_iqr",
        "annular_count", "cumulative_median", "smoothed_annular_median",
        "normalized_excess",
    )
    scalar_names = (
        "local_synchrony", "background", "local_excess",
        "d25_km", "d50_km", "d75_km",
        "effective_length_km", "boundary_normalized_excess",
        "last_100km_area_fraction", "beta_initial_per_100km",
        "beta_initial_fit_score", "beta_near_per_100km",
        "beta_mid_per_100km", "beta_far_per_100km",
        "excess_remaining_100km", "decay_fraction_100km",
        "local_drop_0_50_to_50_100",
        "beta_0_50_per_100km", "beta_0_100_per_100km",
        "beta_0_150_per_100km", "beta_0_200_per_100km",
    )
    status_names = (
        "d25_status", "d50_status", "d75_status",
        "effective_length_status", "beta_initial_status",
        "beta_0_50_status", "beta_0_100_status",
        "beta_0_150_status", "beta_0_200_status",
    )
    radial: dict[str, np.ndarray] = {}
    scalar: dict[str, np.ndarray] = {}
    status: dict[str, np.ndarray] = {}
    for tail in _TAILS:
        for name in radial_names:
            dtype = np.int32 if name == "annular_count" else np.float32
            fill = 0 if name == "annular_count" else np.nan
            radial[f"{tail}_{name}"] = np.full((bins, node_count), fill, dtype=dtype)
        for name in scalar_names:
            scalar[f"{tail}_{name}"] = np.full(node_count, np.nan, dtype=np.float64)
        for name in status_names:
            status[f"{tail}_{name}"] = np.zeros(node_count, dtype=np.int8)

    distance = np.asarray(pairs.distance_km.values, dtype=float)
    values = {
        tail: np.asarray(pairs[name].values, dtype=float)
        for tail, name in _TAILS.items()
    }
    for node in np.flatnonzero(output):
        item = lookup.get(int(node))
        if item is None:
            continue
        start, count = item
        selected = contribution_pair[start : start + count]
        local_distance = distance[selected]
        for tail, all_values in values.items():
            curve = empirical_decay_curve(
                local_distance,
                all_values[selected],
                discovery_radius_km=discovery,
                bin_width_km=bin_width_km,
                min_annulus_count=min_annulus_count,
                background_shell_count=background_shell_count,
                background_method=background_method,
                local_shell_count=local_shell_count,
                crossing_persistence_bins=crossing_persistence_bins,
                min_local_excess=min_local_excess,
                initial_window_km=initial_window_km,
            )
            for name in radial_names:
                radial[f"{tail}_{name}"][:, node] = np.asarray(curve[name].values)
            attribute_map = {
                "background": "selected_background",
                **{name: name for name in scalar_names if name != "background"},
            }
            for output_name, attr_name in attribute_map.items():
                scalar[f"{tail}_{output_name}"][node] = float(curve.attrs[attr_name])
            for name in status_names:
                status[f"{tail}_{name}"][node] = int(curve.attrs[name])

    contrast = {
        "delta_d50_cold_minus_warm_km": np.full(node_count, np.nan),
        "delta_effective_length_cold_minus_warm_km": np.full(node_count, np.nan),
        "delta_beta_cold_minus_warm_per_100km": np.full(node_count, np.nan),
    }
    for node in np.flatnonzero(output):
        if status["cold_d50_status"][node] == status["warm_d50_status"][node] == 3:
            contrast["delta_d50_cold_minus_warm_km"][node] = (
                scalar["cold_d50_km"][node] - scalar["warm_d50_km"][node]
            )
        if (
            status["cold_effective_length_status"][node]
            == status["warm_effective_length_status"][node]
            == 3
        ):
            contrast["delta_effective_length_cold_minus_warm_km"][node] = (
                scalar["cold_effective_length_km"][node]
                - scalar["warm_effective_length_km"][node]
            )
        if (
            status["cold_beta_initial_status"][node]
            == status["warm_beta_initial_status"][node]
            == 3
        ):
            contrast["delta_beta_cold_minus_warm_per_100km"][node] = (
                scalar["cold_beta_initial_per_100km"][node]
                - scalar["warm_beta_initial_per_100km"][node]
            )

    radial_dims = ("time_window_end", "radial_bin", y_dim, x_dim)
    scalar_dims = ("time_window_end", y_dim, x_dim)
    coords = {
        "time_window_end": [np.datetime64(pairs.time_window_end.values)],
        "radial_bin": np.arange(bins, dtype=np.int32),
        "radius_lower_km": ("radial_bin", edges[:-1]),
        "radius_upper_km": ("radial_bin", edges[1:]),
        "radius_km": ("radial_bin", (edges[:-1] + edges[1:]) / 2.0),
        y_dim: pairs[y_dim],
        x_dim: pairs[x_dim],
    }
    data_vars = {
        name: (radial_dims, values_.reshape((1, bins, y_size, x_size)))
        for name, values_ in radial.items()
    }
    data_vars.update(
        {
            name: (scalar_dims, values_.reshape((1, y_size, x_size)))
            for name, values_ in {**scalar, **status, **contrast}.items()
        }
    )
    result = xr.Dataset(data_vars, coords=coords)
    result["output_mask"] = pairs.output_mask
    result["computation_mask"] = pairs.computation_mask
    for name in result.data_vars:
        if name.endswith("_status"):
            result[name].attrs["codes"] = json.dumps(DECAY_STATUS, sort_keys=True)
        if name.endswith("_km") or "length" in name:
            result[name].attrs["units"] = "km"
        elif "per_100km" in name:
            result[name].attrs["units"] = "1 per 100 km"
        elif name.endswith("_count") or name.endswith("_mask"):
            continue
        else:
            result[name].attrs["units"] = "1"
    result.attrs.update(
        {
            "analysis": "empirical_synchrony_decay",
            "semantic_kind": "focal_spatial_decay_summary",
            "source_pair_analysis_fingerprint": pairs.attrs.get("analysis_fingerprint", ""),
            "source_pair_count": int(pairs.sizes["pair"]),
            "discovery_radius_km": discovery,
            "bin_width_km": float(bin_width_km),
            "min_annulus_count": int(min_annulus_count),
            "background_shell_count": int(background_shell_count),
            "background_method": background_method,
            "local_shell_count": int(local_shell_count),
            "crossing_persistence_bins": int(crossing_persistence_bins),
            "min_local_excess": float(min_local_excess),
            "initial_window_km": float(initial_window_km),
            "parametric_kernel": "none",
            "monotonic_curve_enforced": False,
            "interpretation": (
                "decay characteristics, not a hard cutoff, dispersal distance, "
                "kernel bandwidth, or exponential correlation length"
            ),
        }
    )
    return result


def _fractional_crossing(
    centers: np.ndarray,
    normalized: np.ndarray,
    supported: np.ndarray,
    *,
    target: float,
    persistence_bins: int,
) -> tuple[float, int]:
    indices = np.flatnonzero(supported & np.isfinite(normalized))
    if indices.size < persistence_bins + 1:
        return float("nan"), 0
    for position in range(1, indices.size):
        current = indices[position]
        previous = indices[position - 1]
        if not (normalized[previous] > target and normalized[current] <= target):
            continue
        window = indices[position : position + persistence_bins]
        if window.size < persistence_bins:
            continue
        if not np.all(normalized[window] <= target + 0.05):
            continue
        later = indices[position:]
        if np.mean(normalized[later] <= target + 0.10) < 0.70:
            continue
        x0, x1 = centers[previous], centers[current]
        y0, y1 = normalized[previous], normalized[current]
        if np.isclose(y0, y1):
            return float(x1), 3
        crossing = x0 + (target - y0) * (x1 - x0) / (y1 - y0)
        return float(np.clip(crossing, x0, x1)), 3
    return float("nan"), 2


def _effective_length(
    centers: np.ndarray,
    normalized: np.ndarray,
    supported: np.ndarray,
    discovery_radius_km: float,
) -> tuple[float, float, float]:
    indices = np.flatnonzero(supported & np.isfinite(normalized))
    if indices.size < 3:
        return float("nan"), float("nan"), float("nan")
    x = np.concatenate(([0.0], centers[indices], [discovery_radius_km]))
    y = np.concatenate(
        ([1.0], np.clip(normalized[indices], 0.0, None), [max(0.0, normalized[indices[-1]])])
    )
    total = float(np.trapz(y, x))
    cutoff = max(0.0, discovery_radius_km - 100.0)
    tail_x = np.concatenate(([cutoff], x[x > cutoff]))
    tail_y = np.interp(tail_x, x, y)
    tail_area = float(np.trapz(tail_y, tail_x))
    return total, float(max(0.0, normalized[indices[-1]])), tail_area / total if total > 0 else np.nan


def _theil_sen_annular(
    centers: np.ndarray,
    values: np.ndarray,
    supported: np.ndarray,
    lower_km: float,
    upper_km: float,
) -> tuple[float, float, int]:
    use = supported & (centers > lower_km) & (centers <= upper_km)
    x = centers[use]
    y = values[use]
    if x.size < 3:
        return float("nan"), float("nan"), 0
    slopes = []
    for left in range(x.size - 1):
        delta_x = x[left + 1 :] - x[left]
        slopes.extend(((y[left + 1 :] - y[left]) / delta_x).tolist())
    slope = float(np.median(slopes))
    intercept = float(np.median(y - slope * x))
    residual = y - (intercept + slope * x)
    scale = float(np.median(np.abs(y - np.median(y))))
    score = float(np.clip(1.0 - np.median(np.abs(residual)) / max(scale, 1e-8), 0.0, 1.0))
    return 100.0 * slope, score, 3


def _interpolate_supported(
    centers: np.ndarray,
    values: np.ndarray,
    supported: np.ndarray,
    distance_km: float,
) -> float:
    use = supported & np.isfinite(values)
    if np.count_nonzero(use) < 2:
        return float("nan")
    x = centers[use]
    if distance_km < x[0] or distance_km > x[-1]:
        return float("nan")
    return float(np.interp(distance_km, x, values[use]))


def _median_between(
    centers: np.ndarray,
    values: np.ndarray,
    supported: np.ndarray,
    lower_km: float,
    upper_km: float,
) -> float:
    use = supported & (centers > lower_km) & (centers <= upper_km)
    return float(np.median(values[use])) if np.any(use) else float("nan")


__all__ = ["DECAY_STATUS", "empirical_decay_curve", "empirical_synchrony_decay"]
