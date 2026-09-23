"""Scientific diagnostics for already-computed spatial synchrony stacks.

These functions analyze a Phase 1 stack without recalculating climate
correlations. They deliberately keep panel change, radius support, dispersion,
and spatial partitioning as separate concepts.
"""

from __future__ import annotations

from collections import deque
from typing import Sequence
import warnings

import numpy as np
import xarray as xr
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde, wasserstein_distance

from ..stats.tails import _rank_1d


_STACK_METRICS = ("cold_synchrony", "warm_synchrony", "delta_s")
_PREFIXES = {
    "cold_synchrony": "cold",
    "warm_synchrony": "warm",
    "delta_s": "delta",
}


def compare_panels(
    left: np.ndarray,
    right: np.ndarray,
    *,
    deadband: float = 0.02,
    near_tie_epsilon: float = 0.005,
) -> dict[str, float | int]:
    """Compare two synchrony landscapes with complementary metrics.

    Normalized RMSE is RMSE divided by the pooled 5th-to-95th percentile
    range. Wasserstein distance compares value distributions and ignores their
    spatial positions. Gradient metrics compare the two raster gradient fields.
    """

    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    if left_array.shape != right_array.shape or left_array.ndim != 2:
        raise ValueError("Panel comparison requires two equally shaped two-dimensional arrays")
    if deadband < 0 or near_tie_epsilon < 0:
        raise ValueError("deadband and near_tie_epsilon must be non-negative")
    valid = np.isfinite(left_array) & np.isfinite(right_array)
    left_valid = left_array[valid]
    right_valid = right_array[valid]
    count = int(left_valid.size)
    result: dict[str, float | int] = {"shared_valid_count": count}
    if count == 0:
        for name in (
            "spearman",
            "pearson",
            "rmse",
            "mae",
            "normalized_rmse",
            "wasserstein",
            "sign_disagreement",
            "gradient_vector_rmse",
            "gradient_magnitude_rmse",
            "left_standard_deviation",
            "right_standard_deviation",
            "left_robust_range",
            "right_robust_range",
            "pooled_robust_range",
            "left_near_tie_fraction",
            "right_near_tie_fraction",
        ):
            result[name] = float("nan")
        result.update({"left_unique_count": 0, "right_unique_count": 0})
        return result

    difference = left_valid - right_valid
    rmse = float(np.sqrt(np.mean(difference**2)))
    mae = float(np.mean(np.abs(difference)))
    pooled = np.concatenate((left_valid, right_valid))
    pooled_q05, pooled_q95 = np.quantile(pooled, (0.05, 0.95))
    pooled_range = float(pooled_q95 - pooled_q05)
    left_q05, left_q95 = np.quantile(left_valid, (0.05, 0.95))
    right_q05, right_q95 = np.quantile(right_valid, (0.05, 0.95))
    left_sign = _deadband_sign(left_valid, deadband)
    right_sign = _deadband_sign(right_valid, deadband)
    gradient_vector_rmse, gradient_magnitude_rmse = _gradient_difference(
        left_array, right_array
    )
    result.update(
        {
            "spearman": _pearson(_rank_1d(left_valid), _rank_1d(right_valid)),
            "pearson": _pearson(left_valid, right_valid),
            "rmse": rmse,
            "mae": mae,
            "normalized_rmse": rmse / pooled_range if pooled_range > 0 else float("nan"),
            "wasserstein": float(wasserstein_distance(left_valid, right_valid)),
            "sign_disagreement": float(np.mean(left_sign != right_sign)),
            "gradient_vector_rmse": gradient_vector_rmse,
            "gradient_magnitude_rmse": gradient_magnitude_rmse,
            "left_standard_deviation": float(np.std(left_valid)),
            "right_standard_deviation": float(np.std(right_valid)),
            "left_robust_range": float(left_q95 - left_q05),
            "right_robust_range": float(right_q95 - right_q05),
            "pooled_robust_range": pooled_range,
            "left_unique_count": int(np.unique(left_valid).size),
            "right_unique_count": int(np.unique(right_valid).size),
            "left_near_tie_fraction": _near_tie_fraction(left_valid, near_tie_epsilon),
            "right_near_tie_fraction": _near_tie_fraction(right_valid, near_tie_epsilon),
        }
    )
    return result


def panel_change_diagnostics(
    stack: xr.Dataset,
    *,
    adjacency: int = 4,
    deadband: float = 0.02,
    near_tie_epsilon: float = 0.005,
) -> xr.Dataset:
    """Compare every adjacent pair of cold, warm, and Delta landscapes."""

    y_dim, x_dim = _validate_stack(stack)
    if adjacency not in (4, 8):
        raise ValueError("adjacency must be 4 or 8")
    center_y = np.asarray(stack["center_y_index"].values, dtype=int)
    center_x = np.asarray(stack["center_x_index"].values, dtype=int)
    comparisons = _adjacent_center_pairs(center_y, center_x, adjacency)
    count = len(comparisons)
    variables: dict[str, tuple[tuple[str], np.ndarray]] = {}
    scalar_names = (
        "spearman",
        "pearson",
        "rmse",
        "mae",
        "normalized_rmse",
        "wasserstein",
        "sign_disagreement",
        "gradient_vector_rmse",
        "gradient_magnitude_rmse",
        "left_standard_deviation",
        "right_standard_deviation",
        "left_robust_range",
        "right_robust_range",
        "pooled_robust_range",
        "left_near_tie_fraction",
        "right_near_tie_fraction",
    )
    integer_names = ("shared_valid_count", "left_unique_count", "right_unique_count")
    for metric in _STACK_METRICS:
        prefix = _PREFIXES[metric]
        records = [
            compare_panels(
                stack[metric].isel(center=left).values,
                stack[metric].isel(center=right).values,
                deadband=deadband,
                near_tie_epsilon=near_tie_epsilon,
            )
            for left, right in comparisons
        ]
        for name in scalar_names:
            variables[f"{prefix}_{name}"] = (
                ("comparison",),
                np.asarray([record[name] for record in records], dtype=np.float32),
            )
        for name in integer_names:
            variables[f"{prefix}_{name}"] = (
                ("comparison",),
                np.asarray([record[name] for record in records], dtype=np.int32),
            )
    variables["delta_mean_absolute_change"] = variables["delta_mae"]

    left_indices = np.asarray([pair[0] for pair in comparisons], dtype=np.int32)
    right_indices = np.asarray([pair[1] for pair in comparisons], dtype=np.int32)
    distance = np.full(count, np.nan, dtype=np.float32)
    direction = np.full(count, -1, dtype=np.int8)
    for index, (left, right) in enumerate(comparisons):
        ry = int(center_y[right])
        rx = int(center_x[right])
        distance[index] = stack["distance_km"].values[left, ry, rx]
        direction[index] = stack["direction_code"].values[left, ry, rx]
    result = xr.Dataset(
        variables,
        coords={
            "comparison": np.arange(count, dtype=np.int32),
            "center_a": ("comparison", left_indices),
            "center_b": ("comparison", right_indices),
            "center_a_y_index": ("comparison", center_y[left_indices]),
            "center_a_x_index": ("comparison", center_x[left_indices]),
            "center_b_y_index": ("comparison", center_y[right_indices]),
            "center_b_x_index": ("comparison", center_x[right_indices]),
            "center_distance_km": ("comparison", distance),
            "center_direction_code": ("comparison", direction),
        },
    )
    result.attrs.update(
        {
            "analysis": "panel_change_diagnostics",
            "semantic_kind": "summary",
            "source_analysis_fingerprint": stack.attrs.get("analysis_fingerprint", "unknown"),
            "adjacency": adjacency,
            "deadband": float(deadband),
            "near_tie_epsilon": float(near_tie_epsilon),
            "normalized_rmse_definition": "RMSE divided by pooled panel q95-q05",
            "wasserstein_interpretation": "distribution-only distance; ignores focal spatial arrangement",
            "gradient_vector_rmse_definition": "root mean squared difference between panel x/y gradient vectors",
            "panel_change_signature": "magnitude,rank_structure,sign_change,spatial_gradient_change",
            "no_universal_scalar": 1,
        }
    )
    return result


def stack_radius_diagnostics(
    stack: xr.Dataset,
    *,
    radii_km: Sequence[float] | None = None,
    stable_tolerance: float = 0.02,
    stable_min_centers: int = 25,
) -> xr.Dataset:
    """Describe nested focal stacks as the center-support radius expands."""

    y_dim, x_dim = _validate_stack(stack)
    if stable_tolerance <= 0 or stable_min_centers < 1:
        raise ValueError("stable_tolerance must be positive and stable_min_centers at least 1")
    maximum = float(np.nanmax(stack["distance_km"].values))
    if radii_km is None:
        upper = np.ceil(maximum / 5.0) * 5.0
        radii = np.arange(0.0, upper + 0.1, 5.0, dtype=float)
    else:
        radii = np.asarray(tuple(float(value) for value in radii_km), dtype=float)
    if radii.ndim != 1 or radii.size == 0 or np.any(~np.isfinite(radii)):
        raise ValueError("radii_km must contain finite one-dimensional values")
    if np.any(radii < 0) or np.any(np.diff(radii) <= 0):
        raise ValueError("radii_km must be non-negative and strictly increasing")
    distance = np.asarray(stack["distance_km"].values, dtype=float)
    dims = ("radius_km", y_dim, x_dim)
    coords = {"radius_km": radii, y_dim: stack[y_dim], x_dim: stack[x_dim]}
    eligible = np.stack([np.count_nonzero(distance <= radius, axis=0) for radius in radii])
    variables: dict[str, tuple[tuple[str, ...], np.ndarray]] = {
        "eligible_center_count": (dims, eligible.astype(np.int16))
    }
    for metric in _STACK_METRICS:
        prefix = _PREFIXES[metric]
        values = np.asarray(stack[metric].values, dtype=float)
        summaries: dict[str, list[np.ndarray]] = {
            "valid_count": [],
            "mean": [],
            "median": [],
            "standard_deviation": [],
            "iqr": [],
            "mad": [],
            "q05": [],
            "q25": [],
            "q50": [],
            "q75": [],
            "q95": [],
        }
        for radius in radii:
            masked = np.where(distance <= radius, values, np.nan)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                median = np.nanmedian(masked, axis=0)
                q05, q25, q50, q75, q95 = np.nanquantile(
                    masked, (0.05, 0.25, 0.50, 0.75, 0.95), axis=0
                )
                summaries["valid_count"].append(np.count_nonzero(np.isfinite(masked), axis=0))
                summaries["mean"].append(np.nanmean(masked, axis=0))
                summaries["median"].append(median)
                summaries["standard_deviation"].append(np.nanstd(masked, axis=0))
                summaries["iqr"].append(q75 - q25)
                summaries["mad"].append(np.nanmedian(np.abs(masked - median[None, :, :]), axis=0))
                summaries["q05"].append(q05)
                summaries["q25"].append(q25)
                summaries["q50"].append(q50)
                summaries["q75"].append(q75)
                summaries["q95"].append(q95)
        for name, arrays in summaries.items():
            dtype = np.int16 if name == "valid_count" else np.float32
            variables[f"{prefix}_{name}"] = (dims, np.asarray(arrays, dtype=dtype))

        median_series = np.asarray(summaries["median"], dtype=float)
        iqr_series = np.asarray(summaries["iqr"], dtype=float)
        summary_dims = (y_dim, x_dim)
        variables[f"{prefix}_median_radius_range"] = (
            summary_dims,
            _nan_range(median_series, axis=0).astype(np.float32),
        )
        variables[f"{prefix}_iqr_radius_range"] = (
            summary_dims,
            _nan_range(iqr_series, axis=0).astype(np.float32),
        )
        variables[f"{prefix}_maximum_absolute_median_step"] = (
            summary_dims,
            _nanmax_abs_diff(median_series).astype(np.float32),
        )
        variables[f"{prefix}_maximum_absolute_iqr_step"] = (
            summary_dims,
            _nanmax_abs_diff(iqr_series).astype(np.float32),
        )
        variables[f"{prefix}_maximum_absolute_median_derivative_per_km"] = (
            summary_dims,
            _nanmax_abs_derivative(median_series, radii).astype(np.float32),
        )
        variables[f"{prefix}_maximum_absolute_iqr_derivative_per_km"] = (
            summary_dims,
            _nanmax_abs_derivative(iqr_series, radii).astype(np.float32),
        )
        variables[f"{prefix}_experimental_median_stable_radius_km"] = (
            summary_dims,
            _stable_radius(
                median_series,
                eligible,
                radii,
                tolerance=stable_tolerance,
                minimum_count=stable_min_centers,
            ),
        )
        variables[f"{prefix}_experimental_iqr_stable_radius_km"] = (
            summary_dims,
            _stable_radius(
                iqr_series,
                eligible,
                radii,
                tolerance=stable_tolerance,
                minimum_count=stable_min_centers,
            ),
        )
    result = xr.Dataset(variables, coords=coords)
    result.attrs.update(
        {
            "analysis": "stack_radius_diagnostics",
            "semantic_kind": "summary",
            "source_analysis_fingerprint": stack.attrs.get("analysis_fingerprint", "unknown"),
            "nested_support": 1,
            "maximum_available_radius_km": maximum,
            "experimental_stability_rule": (
                "first radius with eligible_center_count >= "
                f"{stable_min_centers} and all remaining values spanning <= {stable_tolerance}"
            ),
            "stability_interpretation": "descriptive and experimental; not a universal synchrony radius",
        }
    )
    return result


def stack_structure_diagnostics(
    stack: xr.Dataset,
    *,
    metric: str = "delta_s",
    distance_bin_edges_km: Sequence[float] | None = None,
    minimum_group_size: int = 20,
) -> xr.Dataset:
    """Describe distance, direction, modality, and geographic group coherence."""

    y_dim, x_dim = _validate_stack(stack)
    if metric not in _STACK_METRICS:
        raise ValueError(f"metric must be one of {_STACK_METRICS!r}")
    values = np.asarray(stack[metric].values, dtype=float)
    distance = np.asarray(stack["distance_km"].values, dtype=float)
    direction = np.asarray(stack["direction_code"].values, dtype=int)
    center_y = np.asarray(stack["center_y_index"].values, dtype=int)
    center_x = np.asarray(stack["center_x_index"].values, dtype=int)
    maximum = float(np.nanmax(distance))
    if distance_bin_edges_km is None:
        upper = max(20.0, np.ceil(maximum / 20.0) * 20.0)
        edges = np.arange(0.0, upper + 20.0, 20.0, dtype=float)
    else:
        edges = np.asarray(tuple(float(value) for value in distance_bin_edges_km), dtype=float)
    if edges.ndim != 1 or edges.size < 2 or np.any(np.diff(edges) <= 0):
        raise ValueError("distance_bin_edges_km must be strictly increasing")
    if edges[0] > 0 or edges[-1] < maximum:
        raise ValueError("distance bins must cover zero through the maximum stack distance")
    n_bins = edges.size - 1
    y_size = int(stack.sizes[y_dim])
    x_size = int(stack.sizes[x_dim])
    shape = (y_size, x_size)
    scalar_names = (
        "distance_spearman",
        "distance_bin_eta_squared",
        "direction_eta_squared",
        "distance_residual_iqr",
        "kde_mode_count",
        "kde_mode_count_narrow_bandwidth",
        "kde_mode_count_wide_bandwidth",
        "kde_multimodal_bandwidth_consensus",
        "two_group_separation",
        "two_group_balance",
        "two_group_neighbor_agreement",
        "two_group_neighbor_agreement_excess",
        "two_group_component_coverage",
    )
    scalars = {name: np.full(shape, np.nan, dtype=np.float32) for name in scalar_names}
    group_labels = np.full((stack.sizes["center"], y_size, x_size), -1, dtype=np.int8)
    distance_median = np.full((n_bins, y_size, x_size), np.nan, dtype=np.float32)
    distance_iqr = np.full_like(distance_median, np.nan)
    distance_count = np.zeros((n_bins, y_size, x_size), dtype=np.int16)
    direction_mean = np.full((8, y_size, x_size), np.nan, dtype=np.float32)
    direction_count = np.zeros((8, y_size, x_size), dtype=np.int16)

    for yi in range(y_size):
        for xi in range(x_size):
            focal_values = values[:, yi, xi]
            focal_distance = distance[:, yi, xi]
            focal_direction = direction[:, yi, xi]
            valid = np.isfinite(focal_values) & np.isfinite(focal_distance)
            observed = focal_values[valid]
            observed_distance = focal_distance[valid]
            if observed.size < 3:
                continue
            scalars["distance_spearman"][yi, xi] = _pearson(
                _rank_1d(observed_distance), _rank_1d(observed)
            )
            bin_index = np.digitize(observed_distance, edges[1:-1], right=True)
            residual = np.full(observed.size, np.nan, dtype=float)
            for band in range(n_bins):
                selected = bin_index == band
                count = int(np.count_nonzero(selected))
                distance_count[band, yi, xi] = count
                if count:
                    band_values = observed[selected]
                    median = float(np.median(band_values))
                    distance_median[band, yi, xi] = median
                    distance_iqr[band, yi, xi] = float(
                        np.quantile(band_values, 0.75) - np.quantile(band_values, 0.25)
                    )
                    residual[selected] = band_values - median
            scalars["distance_bin_eta_squared"][yi, xi] = _eta_squared(observed, bin_index)
            if np.any(np.isfinite(residual)):
                scalars["distance_residual_iqr"][yi, xi] = float(
                    np.nanquantile(residual, 0.75) - np.nanquantile(residual, 0.25)
                )

            valid_direction = valid & (focal_direction >= 0)
            direction_values = focal_values[valid_direction]
            direction_groups = focal_direction[valid_direction]
            scalars["direction_eta_squared"][yi, xi] = _eta_squared(
                direction_values, direction_groups
            )
            for code in range(8):
                selected = direction_groups == code
                direction_count[code, yi, xi] = int(np.count_nonzero(selected))
                if np.any(selected):
                    direction_mean[code, yi, xi] = float(np.mean(direction_values[selected]))

            narrow_modes = _kde_mode_count(observed, bandwidth_factor=0.75)
            scott_modes = _kde_mode_count(observed, bandwidth_factor=1.0)
            wide_modes = _kde_mode_count(observed, bandwidth_factor=1.25)
            scalars["kde_mode_count_narrow_bandwidth"][yi, xi] = narrow_modes
            scalars["kde_mode_count"][yi, xi] = scott_modes
            scalars["kde_mode_count_wide_bandwidth"][yi, xi] = wide_modes
            if np.all(np.isfinite((narrow_modes, scott_modes, wide_modes))):
                scalars["kde_multimodal_bandwidth_consensus"][yi, xi] = float(
                    min(narrow_modes, scott_modes, wide_modes) >= 2
                )
            labels, separation, balance = _two_group_split(observed)
            scalars["two_group_separation"][yi, xi] = separation
            scalars["two_group_balance"][yi, xi] = balance
            full_labels = np.full(focal_values.size, -1, dtype=np.int8)
            full_labels[np.flatnonzero(valid)] = labels
            group_labels[:, yi, xi] = full_labels
            if np.count_nonzero(labels == 0) >= minimum_group_size and np.count_nonzero(labels == 1) >= minimum_group_size:
                agreement, excess, coverage = _spatial_group_coherence(
                    full_labels, center_y, center_x
                )
                scalars["two_group_neighbor_agreement"][yi, xi] = agreement
                scalars["two_group_neighbor_agreement_excess"][yi, xi] = excess
                scalars["two_group_component_coverage"][yi, xi] = coverage

    coords = {
        y_dim: stack[y_dim],
        x_dim: stack[x_dim],
        "distance_bin": np.arange(n_bins, dtype=np.int16),
        "direction": np.arange(8, dtype=np.int8),
        "center": stack["center"],
        "distance_bin_lower_km": ("distance_bin", edges[:-1]),
        "distance_bin_upper_km": ("distance_bin", edges[1:]),
    }
    data_vars: dict[str, tuple[tuple[str, ...], np.ndarray]] = {
        name: ((y_dim, x_dim), array) for name, array in scalars.items()
    }
    data_vars.update(
        {
            "distance_bin_median": (("distance_bin", y_dim, x_dim), distance_median),
            "distance_bin_iqr": (("distance_bin", y_dim, x_dim), distance_iqr),
            "distance_bin_count": (("distance_bin", y_dim, x_dim), distance_count),
            "direction_mean": (("direction", y_dim, x_dim), direction_mean),
            "direction_count": (("direction", y_dim, x_dim), direction_count),
            "two_group_label": (("center", y_dim, x_dim), group_labels),
        }
    )
    result = xr.Dataset(data_vars, coords=coords)
    result.attrs.update(
        {
            "analysis": "stack_structure_diagnostics",
            "semantic_kind": "summary",
            "source_metric": metric,
            "source_analysis_fingerprint": stack.attrs.get("analysis_fingerprint", "unknown"),
            "distance_bin_definition": "left-closed bands except digitize boundary behavior recorded by edges",
            "direction_labels": "0:N,1:NE,2:E,3:SE,4:S,5:SW,6:W,7:NW",
            "eta_squared_interpretation": "descriptive fraction of stack variance associated with group means",
            "kde_mode_count_status": (
                "experimental; Gaussian KDE with 5% density prominence, reported at "
                "0.75x, 1.0x, and 1.25x Scott bandwidth"
            ),
            "kde_multimodal_bandwidth_consensus_definition": (
                "one only when all three tested bandwidths retain at least two modes"
            ),
            "two_group_status": "experimental descriptive split; not evidence of climate regimes",
            "spatial_coherence_requirement": "map two_group_label back to center geography before interpretation",
        }
    )
    return result


def _validate_stack(stack: xr.Dataset) -> tuple[str, str]:
    if not isinstance(stack, xr.Dataset) or stack.attrs.get("analysis") != "local_synchrony_stack":
        raise TypeError("Expected a Dataset produced by local_synchrony_stack")
    missing = sorted(set(_STACK_METRICS + ("distance_km", "direction_code")) - set(stack.data_vars))
    if missing:
        raise ValueError(f"Stack is missing required variables: {missing!r}")
    dims = [dim for dim in stack["delta_s"].dims if dim != "center"]
    if len(dims) != 2:
        raise ValueError("Stack metrics require center plus exactly two focal dimensions")
    return str(dims[0]), str(dims[1])


def _adjacent_center_pairs(
    center_y: np.ndarray, center_x: np.ndarray, adjacency: int
) -> list[tuple[int, int]]:
    lookup = {(int(y), int(x)): index for index, (y, x) in enumerate(zip(center_y, center_x))}
    offsets = ((0, 1), (1, 0)) if adjacency == 4 else ((0, 1), (1, -1), (1, 0), (1, 1))
    pairs: list[tuple[int, int]] = []
    for index, (y, x) in enumerate(zip(center_y, center_x)):
        for dy, dx in offsets:
            other = lookup.get((int(y + dy), int(x + dx)))
            if other is not None:
                pairs.append((index, other))
    return pairs


def _pearson(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2:
        return float("nan")
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = np.linalg.norm(left_centered) * np.linalg.norm(right_centered)
    if denominator <= 0 or not np.isfinite(denominator):
        return float("nan")
    result = float(np.dot(left_centered, right_centered) / denominator)
    if np.isclose(result, 1.0, atol=1e-15, rtol=0):
        return 1.0
    if np.isclose(result, -1.0, atol=1e-15, rtol=0):
        return -1.0
    return float(np.clip(result, -1.0, 1.0))


def _deadband_sign(values: np.ndarray, epsilon: float) -> np.ndarray:
    result = np.zeros(values.shape, dtype=np.int8)
    result[values > epsilon] = 1
    result[values < -epsilon] = -1
    return result


def _near_tie_fraction(values: np.ndarray, epsilon: float) -> float:
    if values.size < 2:
        return float("nan")
    ordered = np.sort(values)
    gaps = np.diff(ordered)
    nearest = np.full(values.size, np.inf, dtype=float)
    nearest[:-1] = np.minimum(nearest[:-1], gaps)
    nearest[1:] = np.minimum(nearest[1:], gaps)
    return float(np.mean(nearest <= epsilon))


def _gradient_difference(left: np.ndarray, right: np.ndarray) -> tuple[float, float]:
    if min(left.shape) < 2:
        return (float("nan"), float("nan"))
    left_gy, left_gx = np.gradient(left)
    right_gy, right_gx = np.gradient(right)
    valid = (
        np.isfinite(left_gx)
        & np.isfinite(left_gy)
        & np.isfinite(right_gx)
        & np.isfinite(right_gy)
    )
    if not np.any(valid):
        return (float("nan"), float("nan"))
    vector_squared = (left_gx - right_gx) ** 2 + (left_gy - right_gy) ** 2
    left_magnitude = np.sqrt(left_gx**2 + left_gy**2)
    right_magnitude = np.sqrt(right_gx**2 + right_gy**2)
    return (
        float(np.sqrt(np.mean(vector_squared[valid]))),
        float(np.sqrt(np.mean((left_magnitude[valid] - right_magnitude[valid]) ** 2))),
    )


def _nan_range(values: np.ndarray, *, axis: int) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmax(values, axis=axis) - np.nanmin(values, axis=axis)


def _nanmax_abs_diff(series: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmax(np.abs(np.diff(series, axis=0)), axis=0)


def _nanmax_abs_derivative(series: np.ndarray, radii: np.ndarray) -> np.ndarray:
    delta_radius = np.diff(radii)[:, None, None]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmax(np.abs(np.diff(series, axis=0) / delta_radius), axis=0)


def _stable_radius(
    series: np.ndarray,
    eligible: np.ndarray,
    radii: np.ndarray,
    *,
    tolerance: float,
    minimum_count: int,
) -> np.ndarray:
    result = np.full(series.shape[1:], np.nan, dtype=np.float32)
    for index, radius in enumerate(radii):
        if radii.size - index < 3:
            continue
        tail = series[index:]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            tail_range = np.nanmax(tail, axis=0) - np.nanmin(tail, axis=0)
        selected = (
            np.isnan(result)
            & (eligible[index] >= minimum_count)
            & np.isfinite(tail_range)
            & (tail_range <= tolerance)
        )
        result[selected] = radius
    return result


def _eta_squared(values: np.ndarray, groups: np.ndarray) -> float:
    valid = np.isfinite(values) & np.isfinite(groups)
    observed = values[valid]
    labels = groups[valid]
    if observed.size < 2:
        return float("nan")
    total = float(np.sum((observed - observed.mean()) ** 2))
    if total <= 0:
        return 0.0
    between = 0.0
    for label in np.unique(labels):
        selected = observed[labels == label]
        between += selected.size * float((selected.mean() - observed.mean()) ** 2)
    return float(between / total)


def _kde_mode_count(values: np.ndarray, *, bandwidth_factor: float = 1.0) -> float:
    if values.size < 10 or np.std(values) <= 0:
        return float("nan")
    if bandwidth_factor <= 0:
        raise ValueError("bandwidth_factor must be positive")
    try:
        density_model = gaussian_kde(
            values,
            bw_method=lambda estimator: estimator.scotts_factor() * bandwidth_factor,
        )
    except np.linalg.LinAlgError:
        return float("nan")
    lower, upper = np.min(values), np.max(values)
    padding = max((upper - lower) * 0.05, 1e-6)
    grid = np.linspace(lower - padding, upper + padding, 256)
    density = density_model(grid)
    peaks, _ = find_peaks(density, prominence=0.05 * float(np.max(density)))
    return float(max(1, peaks.size))


def _two_group_split(values: np.ndarray) -> tuple[np.ndarray, float, float]:
    observed = np.asarray(values, dtype=float)
    if observed.size < 2 or np.std(observed) <= 0:
        return (np.zeros(observed.size, dtype=np.int8), float("nan"), 0.0)
    centers = np.quantile(observed, (0.25, 0.75)).astype(float)
    labels = np.zeros(observed.size, dtype=np.int8)
    for _ in range(100):
        updated = np.argmin(np.abs(observed[:, None] - centers[None, :]), axis=1).astype(np.int8)
        if np.array_equal(updated, labels) and _ > 0:
            break
        labels = updated
        if not np.any(labels == 0) or not np.any(labels == 1):
            order = np.argsort(observed)
            labels[order[: observed.size // 2]] = 0
            labels[order[observed.size // 2 :]] = 1
        centers = np.asarray([observed[labels == group].mean() for group in (0, 1)])
    if centers[0] > centers[1]:
        labels = (1 - labels).astype(np.int8)
        centers = centers[::-1]
    group_zero = observed[labels == 0]
    group_one = observed[labels == 1]
    pooled = np.sqrt((np.var(group_zero) + np.var(group_one)) / 2.0)
    separation = float(abs(group_one.mean() - group_zero.mean()) / pooled) if pooled > 0 else float("inf")
    balance = float(2.0 * min(group_zero.size, group_one.size) / observed.size)
    return labels, separation, balance


def _spatial_group_coherence(
    labels: np.ndarray, center_y: np.ndarray, center_x: np.ndarray
) -> tuple[float, float, float]:
    lookup = {(int(y), int(x)): index for index, (y, x) in enumerate(zip(center_y, center_x))}
    same = 0
    total = 0
    for index, (y, x) in enumerate(zip(center_y, center_x)):
        if labels[index] < 0:
            continue
        for dy, dx in ((0, 1), (1, 0)):
            other = lookup.get((int(y + dy), int(x + dx)))
            if other is None or labels[other] < 0:
                continue
            total += 1
            same += int(labels[index] == labels[other])
    agreement = float(same / total) if total else float("nan")
    valid_labels = labels[labels >= 0]
    proportions = np.asarray([np.mean(valid_labels == group) for group in (0, 1)])
    expected = float(np.sum(proportions**2))
    excess = (
        float((agreement - expected) / (1.0 - expected))
        if np.isfinite(agreement) and expected < 1.0
        else float("nan")
    )
    largest_total = 0
    for group in (0, 1):
        group_indices = {int(index) for index in np.flatnonzero(labels == group)}
        largest_group_component = 0
        while group_indices:
            start = group_indices.pop()
            queue = deque([start])
            component = 1
            while queue:
                current = queue.popleft()
                y = int(center_y[current])
                x = int(center_x[current])
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = lookup.get((y + dy, x + dx))
                    if neighbor in group_indices:
                        group_indices.remove(neighbor)
                        queue.append(neighbor)
                        component += 1
            largest_group_component = max(largest_group_component, component)
        largest_total += largest_group_component
    coverage = float(largest_total / valid_labels.size) if valid_labels.size else float("nan")
    return agreement, excess, coverage


__all__ = [
    "compare_panels",
    "panel_change_diagnostics",
    "stack_radius_diagnostics",
    "stack_structure_diagnostics",
]
