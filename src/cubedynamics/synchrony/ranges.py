"""Kernel-agnostic empirical local synchrony-range estimation.

This module extends the validated sparse-pair workflow without changing its
pair statistic. A large physical discovery radius supplies canonical
cold/warm/Delta relationships. Annular and cumulative empirical summaries are
then used to identify the earliest persistent approach to a nonzero distant
background. The inferred range selects neighbors; it is never a kernel weight.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Literal, Sequence

import numpy as np
import xarray as xr

from ..config import TIME_DIM
from ..runtime import version_info
from .baseline import _normalize_output_mask
from .production import expand_spatial_domain, local_synchrony_pairs
from .spatial import infer_spatial_dims
from .stacks import _coordinate_values, _is_lat_lon, _select_inputs


RANGE_SCHEMA_VERSION = "1"
RANGE_STATUS = {
    0: "insufficient_support",
    1: "flat_or_no_identifiable_focal_signal",
    2: "right_censored_or_unresolved",
    3: "resolved",
}
_METRICS = {
    "cold": "cold_synchrony",
    "warm": "warm_synchrony",
    "delta": "delta_s",
}
_BACKGROUND_METHODS = {
    "outer_annuli",
    "smoothed_outer_annuli",
    "distant_pairs",
}


def empirical_range_curve(
    distance_km: Sequence[float] | np.ndarray,
    values: Sequence[float] | np.ndarray,
    *,
    discovery_radius_km: float,
    bin_width_km: float = 20.0,
    min_annulus_count: int = 30,
    background_shell_count: int = 4,
    background_method: Literal[
        "outer_annuli", "smoothed_outer_annuli", "distant_pairs"
    ] = "outer_annuli",
    persistence_bins: int = 3,
    annular_abs_tolerance: float = 0.03,
    cumulative_abs_tolerance: float = 0.01,
    min_profile_range: float = 0.04,
    censor_fraction: float = 0.80,
) -> xr.Dataset:
    """Summarize one empirical distance-response and estimate its local range.

    The primary range is the outer edge of the first of ``persistence_bins``
    consecutive, well-supported annuli whose medians are near the selected
    distant background and whose cumulative medians are stable. At least 80%
    of later supported annuli must remain within twice the annular tolerance.
    A candidate at or beyond ``censor_fraction`` of the discovery radius is
    reported as unresolved rather than as an observed range.
    """

    config = _validate_config(
        discovery_radius_km=discovery_radius_km,
        bin_width_km=bin_width_km,
        min_annulus_count=min_annulus_count,
        background_shell_count=background_shell_count,
        background_method=background_method,
        persistence_bins=persistence_bins,
        annular_abs_tolerance=annular_abs_tolerance,
        cumulative_abs_tolerance=cumulative_abs_tolerance,
        min_profile_range=min_profile_range,
        censor_fraction=censor_fraction,
    )
    distance = np.asarray(distance_km, dtype=float).reshape(-1)
    observed = np.asarray(values, dtype=float).reshape(-1)
    if distance.shape != observed.shape:
        raise ValueError("distance_km and values must have the same shape")
    summary = _curve_summary(distance, observed, **config)
    edges = config["edges"]
    result = xr.Dataset(
        {
            "annular_median": ("radial_bin", summary["annular_median"]),
            "annular_q25": ("radial_bin", summary["annular_q25"]),
            "annular_q75": ("radial_bin", summary["annular_q75"]),
            "annular_iqr": ("radial_bin", summary["annular_iqr"]),
            "annular_count": ("radial_bin", summary["annular_count"]),
            "cumulative_median": ("radial_bin", summary["cumulative_median"]),
            "cumulative_count": ("radial_bin", summary["cumulative_count"]),
        },
        coords={
            "radial_bin": np.arange(edges.size - 1, dtype=np.int32),
            "radius_lower_km": ("radial_bin", edges[:-1]),
            "radius_upper_km": ("radial_bin", edges[1:]),
            "radius_km": ("radial_bin", (edges[:-1] + edges[1:]) / 2.0),
        },
        attrs={
            "analysis": "empirical_range_curve",
            "range_km": summary["range_km"],
            "status_code": summary["status_code"],
            "status": RANGE_STATUS[summary["status_code"]],
            "censored": bool(summary["status_code"] == 2),
            "selected_background": summary["selected_background"],
            "background_outer_annuli": summary["background_outer_annuli"],
            "background_smoothed_outer_annuli": summary[
                "background_smoothed_outer_annuli"
            ],
            "background_distant_pairs": summary["background_distant_pairs"],
            "annular_tolerance": summary["annular_tolerance"],
            "near_background_fraction": summary["near_background_fraction"],
            "range_reliability": summary["range_reliability"],
            "radial_turn_count": summary["radial_turn_count"],
            "criterion": _criterion_text(config),
        },
    )
    return result


def empirical_synchrony_range(
    pairs: xr.Dataset,
    *,
    bin_width_km: float = 20.0,
    min_annulus_count: int = 30,
    background_shell_count: int = 4,
    background_method: Literal[
        "outer_annuli", "smoothed_outer_annuli", "distant_pairs"
    ] = "outer_annuli",
    persistence_bins: int = 3,
    annular_abs_tolerance: float = 0.03,
    cumulative_abs_tolerance: float = 0.01,
    min_profile_range: float = 0.04,
    censor_fraction: float = 0.80,
    fixed_radius_km: float = 100.0,
) -> xr.Dataset:
    """Estimate cold/warm ranges and fixed/adaptive reductions from one pair table.

    Canonical pair calculations are reused for annular curves, fixed 100 km
    control values, empirical ranges, and adaptive reductions. Cold and warm
    ranges are estimated separately. Primary adaptive Delta uses the same
    neighbors for both tails: ``R_common = max(R_cold, R_warm)`` when both
    ranges are resolved.
    """

    _validate_pairs(pairs)
    discovery_radius_km = float(pairs.attrs["max_radius_km"])
    if fixed_radius_km <= 0 or fixed_radius_km > discovery_radius_km + 1e-9:
        raise ValueError("fixed_radius_km must be positive and no greater than discovery radius")
    config = _validate_config(
        discovery_radius_km=discovery_radius_km,
        bin_width_km=bin_width_km,
        min_annulus_count=min_annulus_count,
        background_shell_count=background_shell_count,
        background_method=background_method,
        persistence_bins=persistence_bins,
        annular_abs_tolerance=annular_abs_tolerance,
        cumulative_abs_tolerance=cumulative_abs_tolerance,
        min_profile_range=min_profile_range,
        censor_fraction=censor_fraction,
    )
    edges = config["edges"]
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

    bins = edges.size - 1
    radial_float = {
        f"{metric}_{name}": np.full((bins, node_count), np.nan, dtype=np.float32)
        for metric in _METRICS
        for name in (
            "annular_median",
            "annular_q25",
            "annular_q75",
            "annular_iqr",
            "cumulative_median",
        )
    }
    radial_count = {
        f"{metric}_{name}": np.zeros((bins, node_count), dtype=np.int32)
        for metric in _METRICS
        for name in ("annular_count", "cumulative_count")
    }
    scalar_float_names = []
    for metric in ("cold", "warm"):
        scalar_float_names.extend(
            (
                f"{metric}_range_km",
                f"{metric}_background",
                f"{metric}_background_outer_annuli",
                f"{metric}_background_smoothed_outer_annuli",
                f"{metric}_background_distant_pairs",
                f"{metric}_annular_tolerance",
                f"{metric}_near_background_fraction",
                f"{metric}_range_reliability",
            )
        )
    scalar_float_names.extend(
        (
            "common_range_km",
            "range_difference_cold_minus_warm_km",
            "common_range_reliability",
            "fixed_cold_median",
            "fixed_warm_median",
            "fixed_delta_pair_median",
            "fixed_delta_iqr",
            "fixed_delta_reduction_gap",
            "adaptive_cold_median",
            "adaptive_warm_median",
            "adaptive_common_cold_median",
            "adaptive_common_warm_median",
            "adaptive_delta_pair_median",
            "adaptive_delta_iqr",
            "adaptive_delta_reduction_gap",
            "adaptive_minus_fixed_delta",
        )
    )
    scalar_float = {
        name: np.full(node_count, np.nan, dtype=np.float64) for name in scalar_float_names
    }
    scalar_int = {
        "cold_range_status": np.zeros(node_count, dtype=np.int8),
        "warm_range_status": np.zeros(node_count, dtype=np.int8),
        "common_range_status": np.zeros(node_count, dtype=np.int8),
        "cold_radial_turn_count": np.zeros(node_count, dtype=np.int16),
        "warm_radial_turn_count": np.zeros(node_count, dtype=np.int16),
        "fixed_pair_count": np.zeros(node_count, dtype=np.int32),
        "adaptive_pair_count": np.zeros(node_count, dtype=np.int32),
    }
    distance = np.asarray(pairs.distance_km.values, dtype=float)
    metric_values = {
        metric: np.asarray(pairs[name].values, dtype=float)
        for metric, name in _METRICS.items()
    }
    started = time.perf_counter()

    for node in np.flatnonzero(output):
        item = lookup.get(int(node))
        if item is None:
            continue
        start, count = item
        selected_pairs = contribution_pair[start : start + count]
        local_distance = distance[selected_pairs]
        summaries: dict[str, dict[str, object]] = {}
        for metric, all_values in metric_values.items():
            summary = _curve_summary(
                local_distance,
                all_values[selected_pairs],
                **config,
            )
            summaries[metric] = summary
            for name in radial_float:
                prefix = f"{metric}_"
                if name.startswith(prefix):
                    radial_float[name][:, node] = np.asarray(
                        summary[name[len(prefix) :]], dtype=np.float32
                    )
            for name in radial_count:
                prefix = f"{metric}_"
                if name.startswith(prefix):
                    radial_count[name][:, node] = np.asarray(
                        summary[name[len(prefix) :]], dtype=np.int32
                    )

        for metric in ("cold", "warm"):
            summary = summaries[metric]
            scalar_float[f"{metric}_range_km"][node] = float(summary["range_km"])
            scalar_float[f"{metric}_background"][node] = float(summary["selected_background"])
            for method_name in (
                "background_outer_annuli",
                "background_smoothed_outer_annuli",
                "background_distant_pairs",
            ):
                scalar_float[f"{metric}_{method_name}"][node] = float(summary[method_name])
            scalar_float[f"{metric}_annular_tolerance"][node] = float(
                summary["annular_tolerance"]
            )
            scalar_float[f"{metric}_near_background_fraction"][node] = float(
                summary["near_background_fraction"]
            )
            scalar_float[f"{metric}_range_reliability"][node] = float(
                summary["range_reliability"]
            )
            scalar_int[f"{metric}_range_status"][node] = int(summary["status_code"])
            scalar_int[f"{metric}_radial_turn_count"][node] = int(
                summary["radial_turn_count"]
            )

        cold_range = scalar_float["cold_range_km"][node]
        warm_range = scalar_float["warm_range_km"][node]
        cold_status = int(scalar_int["cold_range_status"][node])
        warm_status = int(scalar_int["warm_range_status"][node])
        if cold_status == 3 and warm_status == 3:
            common = max(cold_range, warm_range)
            scalar_float["common_range_km"][node] = common
            scalar_float["range_difference_cold_minus_warm_km"][node] = (
                cold_range - warm_range
            )
            scalar_float["common_range_reliability"][node] = min(
                scalar_float["cold_range_reliability"][node],
                scalar_float["warm_range_reliability"][node],
            )
            scalar_int["common_range_status"][node] = 3
        else:
            unresolved = {cold_status, warm_status}
            scalar_int["common_range_status"][node] = (
                2 if 2 in unresolved else 1 if 1 in unresolved else 0
            )

        cold_values = metric_values["cold"][selected_pairs]
        warm_values = metric_values["warm"][selected_pairs]
        delta_values = metric_values["delta"][selected_pairs]
        fixed = (local_distance > 0) & (local_distance <= fixed_radius_km + 1e-7)
        scalar_int["fixed_pair_count"][node] = int(np.count_nonzero(fixed))
        scalar_float["fixed_cold_median"][node] = _finite_median(cold_values[fixed])
        scalar_float["fixed_warm_median"][node] = _finite_median(warm_values[fixed])
        fixed_delta = delta_values[fixed & np.isfinite(delta_values)]
        scalar_float["fixed_delta_pair_median"][node] = _finite_median(fixed_delta)
        scalar_float["fixed_delta_iqr"][node] = _finite_iqr(fixed_delta)
        scalar_float["fixed_delta_reduction_gap"][node] = (
            scalar_float["fixed_delta_pair_median"][node]
            - (
                scalar_float["fixed_cold_median"][node]
                - scalar_float["fixed_warm_median"][node]
            )
        )

        if cold_status == 3:
            use = (local_distance > 0) & (local_distance <= cold_range + 1e-7)
            scalar_float["adaptive_cold_median"][node] = _finite_median(cold_values[use])
        if warm_status == 3:
            use = (local_distance > 0) & (local_distance <= warm_range + 1e-7)
            scalar_float["adaptive_warm_median"][node] = _finite_median(warm_values[use])
        common = scalar_float["common_range_km"][node]
        if np.isfinite(common):
            use = (local_distance > 0) & (local_distance <= common + 1e-7)
            scalar_int["adaptive_pair_count"][node] = int(np.count_nonzero(use))
            scalar_float["adaptive_common_cold_median"][node] = _finite_median(
                cold_values[use]
            )
            scalar_float["adaptive_common_warm_median"][node] = _finite_median(
                warm_values[use]
            )
            adaptive_delta = delta_values[use & np.isfinite(delta_values)]
            scalar_float["adaptive_delta_pair_median"][node] = _finite_median(adaptive_delta)
            scalar_float["adaptive_delta_iqr"][node] = _finite_iqr(adaptive_delta)
            scalar_float["adaptive_delta_reduction_gap"][node] = (
                scalar_float["adaptive_delta_pair_median"][node]
                - (
                    scalar_float["adaptive_common_cold_median"][node]
                    - scalar_float["adaptive_common_warm_median"][node]
                )
            )
            scalar_float["adaptive_minus_fixed_delta"][node] = (
                scalar_float["adaptive_delta_pair_median"][node]
                - scalar_float["fixed_delta_pair_median"][node]
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
        name: (radial_dims, values.reshape((1, bins, y_size, x_size)))
        for name, values in {**radial_float, **radial_count}.items()
    }
    data_vars.update(
        {
            name: (scalar_dims, values.reshape((1, y_size, x_size)))
            for name, values in {**scalar_float, **scalar_int}.items()
        }
    )
    result = xr.Dataset(data_vars, coords=coords)
    result["output_mask"] = pairs.output_mask
    result["computation_mask"] = pairs.computation_mask
    result["cold_range_censored"] = result.cold_range_status == 2
    result["warm_range_censored"] = result.warm_range_status == 2
    result["common_range_censored"] = result.common_range_status == 2
    result["common_range_stable"] = (
        (result.common_range_status == 3) & (result.common_range_reliability >= 0.60)
    )
    for name in result.data_vars:
        if name.endswith("range_km") or name.endswith("_km"):
            result[name].attrs["units"] = "km"
        elif name.endswith("count") or name.endswith("mask") or name.endswith("censored"):
            continue
        else:
            result[name].attrs["units"] = "1"
    result.cold_range_status.attrs["codes"] = json.dumps(RANGE_STATUS, sort_keys=True)
    result.warm_range_status.attrs["codes"] = json.dumps(RANGE_STATUS, sort_keys=True)
    result.common_range_status.attrs["codes"] = json.dumps(RANGE_STATUS, sort_keys=True)
    result.common_range_km.attrs["definition"] = (
        "max(cold_range_km, warm_range_km) only when both ranges are resolved"
    )
    result.range_difference_cold_minus_warm_km.attrs["definition"] = (
        "cold empirical synchrony range minus warm empirical synchrony range"
    )
    result.adaptive_delta_pair_median.attrs["definition"] = (
        "median pairwise cold_synchrony - warm_synchrony over the shared common-range neighbor set"
    )
    result.adaptive_cold_median.attrs["definition"] = (
        "median cold synchrony within the resolved cold empirical range"
    )
    result.adaptive_warm_median.attrs["definition"] = (
        "median warm synchrony within the resolved warm empirical range"
    )
    fingerprint_payload = {
        "schema": RANGE_SCHEMA_VERSION,
        "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
        "config": {key: value for key, value in config.items() if key != "edges"},
        "fixed_radius_km": float(fixed_radius_km),
    }
    fingerprint = sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result.attrs.update(dict(pairs.attrs))
    result.attrs.update(
        {
            "analysis": "empirical_synchrony_range",
            "semantic_kind": "summary",
            "range_schema_version": RANGE_SCHEMA_VERSION,
            "analysis_fingerprint": f"sha256:{fingerprint}",
            "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
            "discovery_radius_km": discovery_radius_km,
            "discovery_radius_definition": (
                "maximum observed search support; not the empirical synchrony range"
            ),
            "fixed_control_radius_km": float(fixed_radius_km),
            "range_criterion": _criterion_text(config),
            "background_method": background_method,
            "bin_width_km": float(bin_width_km),
            "min_annulus_count": int(min_annulus_count),
            "background_shell_count": int(background_shell_count),
            "persistence_bins": int(persistence_bins),
            "annular_abs_tolerance": float(annular_abs_tolerance),
            "cumulative_abs_tolerance": float(cumulative_abs_tolerance),
            "min_profile_range": float(min_profile_range),
            "censor_fraction": float(censor_fraction),
            "primary_common_range": "max of resolved cold and warm ranges",
            "adaptive_delta_neighbor_policy": "same neighbors within common range",
            "kernel_weighting": "none",
            "stacking": "none",
            "second_stage_convolution": "none",
            "range_reduction_seconds": float(time.perf_counter() - started),
        }
    )
    return result


def tiled_empirical_synchrony_range(
    obj: xr.Dataset | xr.DataArray,
    *,
    output_mask: xr.DataArray | np.ndarray,
    computation_mask: xr.DataArray | np.ndarray | None = None,
    lower_var: str | None = None,
    upper_var: str | None = None,
    discovery_radius_km: float = 300.0,
    fixed_radius_km: float = 100.0,
    tile_shape: tuple[int, int] = (8, 8),
    window_days: int = 90,
    window_end: object | None = None,
    min_t: int = 10,
    split_quantile: float = 0.5,
    time_dim: str = TIME_DIM,
    pair_batch_size: int = 16384,
    bin_width_km: float = 20.0,
    min_annulus_count: int = 30,
    background_shell_count: int = 4,
    background_method: Literal[
        "outer_annuli", "smoothed_outer_annuli", "distant_pairs"
    ] = "outer_annuli",
    persistence_bins: int = 3,
    annular_abs_tolerance: float = 0.03,
    cumulative_abs_tolerance: float = 0.01,
    min_profile_range: float = 0.04,
    censor_fraction: float = 0.80,
    checkpoint_dir: str | Path | None = None,
) -> xr.Dataset:
    """Run empirical range estimation in restartable full-halo output tiles."""

    if discovery_radius_km <= 0:
        raise ValueError("discovery_radius_km must be positive")
    if len(tile_shape) != 2 or tile_shape[0] < 1 or tile_shape[1] < 1:
        raise ValueError("tile_shape must contain two positive integers")
    range_config = _validate_config(
        discovery_radius_km=discovery_radius_km,
        bin_width_km=bin_width_km,
        min_annulus_count=min_annulus_count,
        background_shell_count=background_shell_count,
        background_method=background_method,
        persistence_bins=persistence_bins,
        annular_abs_tolerance=annular_abs_tolerance,
        cumulative_abs_tolerance=cumulative_abs_tolerance,
        min_profile_range=min_profile_range,
        censor_fraction=censor_fraction,
    )
    lower, _, lower_name, upper_name = _select_inputs(obj, lower_var, upper_var)
    y_dim, x_dim = infer_spatial_dims(lower)
    y_values = _coordinate_values(lower, y_dim)
    x_values = _coordinate_values(lower, x_dim)
    _is_lat_lon(lower, y_dim, x_dim, y_values, x_values)
    mask = _normalize_output_mask(output_mask, lower, y_dim, x_dim)
    eligible = (
        np.ones_like(mask)
        if computation_mask is None
        else _normalize_output_mask(computation_mask, lower, y_dim, x_dim)
    )
    if np.any(mask & ~eligible):
        raise ValueError("output_mask must be a subset of computation_mask")
    if not np.any(mask):
        raise ValueError("output_mask selects no pixels")

    checkpoint_root = Path(checkpoint_dir) if checkpoint_dir is not None else None
    pieces: list[xr.Dataset] = []
    computed_tiles = resumed_tiles = 0
    pair_count = nonself_pair_count = 0
    kernel_seconds = geometry_seconds = materialization_seconds = reduction_seconds = 0.0
    runtime = version_info()
    source_attrs = dict(getattr(obj, "attrs", {}))
    common = {
        "range_schema_version": RANGE_SCHEMA_VERSION,
        "source": source_attrs.get("source", "unknown"),
        "source_provider": source_attrs.get("source_provider", "unknown"),
        "serving_revision": source_attrs.get("serving_revision", "unknown"),
        "lower_variable": lower_name,
        "upper_variable": upper_name,
        "coordinate_hashes": {
            "time": sha256(np.asarray(lower[time_dim].values).tobytes()).hexdigest(),
            "y": sha256(y_values.tobytes()).hexdigest(),
            "x": sha256(x_values.tobytes()).hexdigest(),
        },
        "discovery_radius_km": float(discovery_radius_km),
        "fixed_radius_km": float(fixed_radius_km),
        "range_config": {key: value for key, value in range_config.items() if key != "edges"},
        "window_days": int(window_days),
        "window_end": None if window_end is None else str(np.datetime64(window_end)),
        "min_t": int(min_t),
        "split_quantile": float(split_quantile),
        "computation_mask_hash": sha256(eligible.tobytes()).hexdigest(),
        "cubedynamics_version": runtime.version,
        "cubedynamics_git_sha": runtime.git_sha or "unavailable",
    }
    for y_start in range(0, y_values.size, int(tile_shape[0])):
        y_stop = min(y_start + int(tile_shape[0]), y_values.size)
        for x_start in range(0, x_values.size, int(tile_shape[1])):
            x_stop = min(x_start + int(tile_shape[1]), x_values.size)
            tile_values = mask[y_start:y_stop, x_start:x_stop]
            if not np.any(tile_values):
                continue
            tile_mask = np.zeros_like(mask)
            tile_mask[y_start:y_stop, x_start:x_stop] = tile_values
            yi, xi = np.nonzero(tile_mask)
            output_bounds = (
                float(x_values[xi].min()),
                float(y_values[yi].min()),
                float(x_values[xi].max()),
                float(y_values[yi].max()),
            )
            halo_bounds = expand_spatial_domain(output_bounds, float(discovery_radius_km)).bounds
            halo_y = np.flatnonzero((y_values >= halo_bounds[1]) & (y_values <= halo_bounds[3]))
            halo_x = np.flatnonzero((x_values >= halo_bounds[0]) & (x_values <= halo_bounds[2]))
            if halo_y.size == 0 or halo_x.size == 0:
                raise ValueError("A tile halo does not intersect the computation cube")
            y_slice = slice(int(halo_y.min()), int(halo_y.max()) + 1)
            x_slice = slice(int(halo_x.min()), int(halo_x.max()) + 1)
            subset = obj.isel({y_dim: y_slice, x_dim: x_slice})
            subset_mask = xr.DataArray(
                tile_mask[y_slice, x_slice],
                dims=(y_dim, x_dim),
                coords={y_dim: subset[y_dim], x_dim: subset[x_dim]},
            )
            subset_computation = xr.DataArray(
                eligible[y_slice, x_slice],
                dims=(y_dim, x_dim),
                coords={y_dim: subset[y_dim], x_dim: subset[x_dim]},
            )
            payload = {
                **common,
                "tile": [y_start, y_stop, x_start, x_stop],
                "tile_output_mask_hash": sha256(tile_values.tobytes()).hexdigest(),
                "halo_index_bounds": [y_slice.start, y_slice.stop, x_slice.start, x_slice.stop],
            }
            compatibility = "sha256:" + sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            checkpoint = (
                checkpoint_root
                / f"range_y{y_start:05d}-{y_stop:05d}_x{x_start:05d}-{x_stop:05d}.nc"
                if checkpoint_root is not None
                else None
            )
            output_y = lower[y_dim].isel({y_dim: slice(y_start, y_stop)})
            output_x = lower[x_dim].isel({x_dim: slice(x_start, x_stop)})
            if checkpoint is not None and checkpoint.exists() and checkpoint.with_suffix(".json").exists():
                summary = _load_checkpoint(checkpoint, compatibility)
                summary = summary.reindex({y_dim: output_y, x_dim: output_x})
                resumed_tiles += 1
            else:
                pairs = local_synchrony_pairs(
                    subset,
                    lower_var=lower_var,
                    upper_var=upper_var,
                    output_mask=subset_mask,
                    computation_mask=subset_computation,
                    max_radius_km=discovery_radius_km,
                    window_days=window_days,
                    window_end=window_end,
                    min_t=min_t,
                    split_quantile=split_quantile,
                    time_dim=time_dim,
                    pair_batch_size=pair_batch_size,
                )
                summary = empirical_synchrony_range(
                    pairs,
                    bin_width_km=bin_width_km,
                    min_annulus_count=min_annulus_count,
                    background_shell_count=background_shell_count,
                    background_method=background_method,
                    persistence_bins=persistence_bins,
                    annular_abs_tolerance=annular_abs_tolerance,
                    cumulative_abs_tolerance=cumulative_abs_tolerance,
                    min_profile_range=min_profile_range,
                    censor_fraction=censor_fraction,
                    fixed_radius_km=fixed_radius_km,
                )
                summary.attrs["checkpoint_compatibility_fingerprint"] = compatibility
                summary.attrs.update(
                    {
                        "tile_index_bounds": json.dumps([y_start, y_stop, x_start, x_stop]),
                        "halo_index_bounds": json.dumps(
                            [y_slice.start, y_slice.stop, x_slice.start, x_slice.stop]
                        ),
                        "output_tile_shape": f"{y_stop-y_start},{x_stop-x_start}",
                        "computation_tile_shape": (
                            f"{y_slice.stop-y_slice.start},{x_slice.stop-x_slice.start}"
                        ),
                        "maximum_halo_radius_km": float(discovery_radius_km),
                    }
                )
                summary = summary.reindex({y_dim: output_y, x_dim: output_x})
                if checkpoint is not None:
                    _write_checkpoint(summary, checkpoint)
                computed_tiles += 1
            pair_count += int(summary.attrs.get("unique_pair_count", 0))
            nonself_pair_count += int(summary.attrs.get("nonself_pair_count", 0))
            kernel_seconds += float(summary.attrs.get("pair_kernel_seconds", 0.0))
            geometry_seconds += float(summary.attrs.get("geometry_seconds", 0.0))
            materialization_seconds += float(summary.attrs.get("input_materialization_seconds", 0.0))
            reduction_seconds += float(summary.attrs.get("range_reduction_seconds", 0.0))
            pieces.append(summary)

    combined = xr.combine_by_coords(pieces, combine_attrs="override")
    combined = combined.reindex({y_dim: lower[y_dim], x_dim: lower[x_dim]})
    combined["output_mask"] = xr.DataArray(
        mask, dims=(y_dim, x_dim), coords={y_dim: lower[y_dim], x_dim: lower[x_dim]}
    )
    combined["computation_mask"] = xr.DataArray(
        eligible, dims=(y_dim, x_dim), coords={y_dim: lower[y_dim], x_dim: lower[x_dim]}
    )
    combined.attrs.update(
        {
            "analysis": "empirical_synchrony_range",
            "execution": "restartable output tiling with full discovery-radius coordinate halos",
            "tile_shape": f"{int(tile_shape[0])},{int(tile_shape[1])}",
            "tile_count": int(len(pieces)),
            "computed_tile_count": int(computed_tiles),
            "resumed_tile_count": int(resumed_tiles),
            "pair_calculation_count_with_tile_recompute": int(pair_count),
            "nonself_pair_calculation_count_with_tile_recompute": int(nonself_pair_count),
            "pair_kernel_seconds_sum": float(kernel_seconds),
            "pair_geometry_seconds_sum": float(geometry_seconds),
            "input_materialization_seconds_sum": float(materialization_seconds),
            "range_reduction_seconds_sum": float(reduction_seconds),
            "cross_tile_pair_policy": "endpoint-tile recompute; no nationwide dense pair tensor",
            "pair_product_reuse": (
                "each tile pair table supplies annuli, fixed control, ranges, and adaptive reductions"
            ),
            "cubedynamics_version": runtime.version,
            "cubedynamics_git_sha": runtime.git_sha or "unavailable",
        }
    )
    return combined


def _validate_config(**kwargs) -> dict[str, object]:
    discovery = float(kwargs["discovery_radius_km"])
    width = float(kwargs["bin_width_km"])
    if discovery <= 0 or width <= 0 or width > discovery:
        raise ValueError("discovery_radius_km and bin_width_km must be positive, with width <= radius")
    if int(kwargs["min_annulus_count"]) < 1:
        raise ValueError("min_annulus_count must be at least 1")
    if int(kwargs["background_shell_count"]) < 2:
        raise ValueError("background_shell_count must be at least 2")
    if kwargs["background_method"] not in _BACKGROUND_METHODS:
        raise ValueError(f"background_method must be one of {sorted(_BACKGROUND_METHODS)}")
    if int(kwargs["persistence_bins"]) < 2:
        raise ValueError("persistence_bins must be at least 2")
    for name in (
        "annular_abs_tolerance",
        "cumulative_abs_tolerance",
        "min_profile_range",
    ):
        if float(kwargs[name]) < 0:
            raise ValueError(f"{name} must be non-negative")
    censor = float(kwargs["censor_fraction"])
    if not 0 < censor <= 1:
        raise ValueError("censor_fraction must be in (0, 1]")
    edges = np.arange(0.0, discovery + width, width, dtype=float)
    if edges[-1] > discovery:
        edges[-1] = discovery
    elif edges[-1] < discovery:
        edges = np.append(edges, discovery)
    return {
        "discovery_radius_km": discovery,
        "bin_width_km": width,
        "min_annulus_count": int(kwargs["min_annulus_count"]),
        "background_shell_count": int(kwargs["background_shell_count"]),
        "background_method": str(kwargs["background_method"]),
        "persistence_bins": int(kwargs["persistence_bins"]),
        "annular_abs_tolerance": float(kwargs["annular_abs_tolerance"]),
        "cumulative_abs_tolerance": float(kwargs["cumulative_abs_tolerance"]),
        "min_profile_range": float(kwargs["min_profile_range"]),
        "censor_fraction": censor,
        "edges": edges,
    }


def _curve_summary(
    distance: np.ndarray,
    values: np.ndarray,
    *,
    discovery_radius_km: float,
    bin_width_km: float,
    min_annulus_count: int,
    background_shell_count: int,
    background_method: str,
    persistence_bins: int,
    annular_abs_tolerance: float,
    cumulative_abs_tolerance: float,
    min_profile_range: float,
    censor_fraction: float,
    edges: np.ndarray,
) -> dict[str, object]:
    del bin_width_km
    distance = np.asarray(distance, dtype=float).reshape(-1)
    values = np.asarray(values, dtype=float).reshape(-1)
    valid = (
        np.isfinite(distance)
        & np.isfinite(values)
        & (distance > 0)
        & (distance <= discovery_radius_km + 1e-7)
    )
    bins = edges.size - 1
    annular_median = np.full(bins, np.nan, dtype=float)
    q25 = np.full(bins, np.nan, dtype=float)
    q75 = np.full(bins, np.nan, dtype=float)
    annular_count = np.zeros(bins, dtype=np.int32)
    cumulative_median = np.full(bins, np.nan, dtype=float)
    cumulative_count = np.zeros(bins, dtype=np.int32)
    if np.any(valid):
        index = np.searchsorted(edges, distance[valid], side="right") - 1
        index[np.isclose(distance[valid], discovery_radius_km)] = bins - 1
        local_values = values[valid]
        local_distance = distance[valid]
        for radial_bin in range(bins):
            shell = local_values[index == radial_bin]
            annular_count[radial_bin] = int(shell.size)
            if shell.size >= min_annulus_count:
                q25[radial_bin], annular_median[radial_bin], q75[radial_bin] = np.quantile(
                    shell, (0.25, 0.50, 0.75)
                )
            cumulative = local_values[local_distance <= edges[radial_bin + 1] + 1e-7]
            cumulative_count[radial_bin] = int(cumulative.size)
            if cumulative.size:
                cumulative_median[radial_bin] = np.median(cumulative)
    supported = np.isfinite(annular_median) & (annular_count >= min_annulus_count)
    supported_index = np.flatnonzero(supported)
    background_outer = background_smooth = background_distant = float("nan")
    selected_background = tolerance = near_fraction = reliability = float("nan")
    range_km = float("nan")
    status_code = 0
    turn_count = 0
    if supported_index.size >= background_shell_count:
        outer_index = supported_index[-background_shell_count:]
        background_outer = float(np.median(annular_median[outer_index]))
        smoothed = _smooth_supported(annular_median)
        background_smooth = float(np.median(smoothed[outer_index]))
        distant_cutoff = max(0.75 * discovery_radius_km, edges[outer_index[0]])
        distant = values[valid & (distance >= distant_cutoff)]
        if distant.size >= min_annulus_count:
            background_distant = float(np.median(distant))
        backgrounds = {
            "outer_annuli": background_outer,
            "smoothed_outer_annuli": background_smooth,
            "distant_pairs": background_distant,
        }
        selected_background = float(backgrounds[background_method])
        outer_values = annular_median[outer_index]
        outer_mad = float(np.median(np.abs(outer_values - np.median(outer_values))))
        tolerance = min(0.10, max(annular_abs_tolerance, 1.5 * 1.4826 * outer_mad))
        profile_values = annular_median[supported]
        profile_span = float(np.max(profile_values) - np.min(profile_values))
        smooth_values = smoothed[supported]
        differences = np.diff(smooth_values)
        meaningful = np.sign(
            np.where(np.abs(differences) >= max(0.01, 0.1 * profile_span), differences, 0.0)
        )
        nonzero = meaningful[meaningful != 0]
        turn_count = int(np.count_nonzero(np.diff(nonzero) != 0)) if nonzero.size > 1 else 0
        if not np.isfinite(selected_background):
            status_code = 0
        elif profile_span < min_profile_range:
            status_code = 1
        else:
            candidate = None
            for radial_bin in range(1, bins - persistence_bins + 1):
                window = np.arange(radial_bin, radial_bin + persistence_bins)
                if not np.all(supported[window]):
                    continue
                annular_near = np.all(
                    np.abs(annular_median[window] - selected_background) <= tolerance
                )
                cumulative_change = np.abs(
                    cumulative_median[window] - cumulative_median[window - 1]
                )
                cumulative_stable = np.all(
                    np.isfinite(cumulative_change)
                    & (cumulative_change <= cumulative_abs_tolerance)
                )
                later = supported & (np.arange(bins) >= radial_bin)
                later_count = int(np.count_nonzero(later))
                later_fraction = (
                    float(
                        np.mean(
                            np.abs(annular_median[later] - selected_background)
                            <= 2.0 * tolerance
                        )
                    )
                    if later_count
                    else 0.0
                )
                if annular_near and cumulative_stable and later_fraction >= 0.80:
                    candidate = radial_bin
                    near_fraction = later_fraction
                    break
            if candidate is None:
                status_code = 2
            else:
                proposed = float(edges[candidate + 1])
                if proposed >= censor_fraction * discovery_radius_km - 1e-9:
                    status_code = 2
                else:
                    status_code = 3
                    range_km = proposed
                    support_fraction = float(np.mean(supported[candidate:]))
                    boundary_margin = max(
                        0.0,
                        1.0 - proposed / (censor_fraction * discovery_radius_km),
                    )
                    tolerance_score = max(0.0, 1.0 - tolerance / 0.10)
                    reliability = float(
                        np.clip(
                            0.45 * near_fraction
                            + 0.25 * support_fraction
                            + 0.20 * boundary_margin
                            + 0.10 * tolerance_score,
                            0.0,
                            1.0,
                        )
                    )
    return {
        "annular_median": annular_median,
        "annular_q25": q25,
        "annular_q75": q75,
        "annular_iqr": q75 - q25,
        "annular_count": annular_count,
        "cumulative_median": cumulative_median,
        "cumulative_count": cumulative_count,
        "range_km": range_km,
        "status_code": status_code,
        "selected_background": selected_background,
        "background_outer_annuli": background_outer,
        "background_smoothed_outer_annuli": background_smooth,
        "background_distant_pairs": background_distant,
        "annular_tolerance": tolerance,
        "near_background_fraction": near_fraction,
        "range_reliability": reliability,
        "radial_turn_count": turn_count,
    }


def _smooth_supported(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    for index in range(result.size):
        lower = max(0, index - 1)
        upper = min(result.size, index + 2)
        local = values[lower:upper]
        local = local[np.isfinite(local)]
        result[index] = np.median(local) if local.size else np.nan
    return result


def _finite_median(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if values.size else float("nan")


def _finite_iqr(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not values.size:
        return float("nan")
    q25, q75 = np.quantile(values, (0.25, 0.75))
    return float(q75 - q25)


def _criterion_text(config: dict[str, object]) -> str:
    return (
        "first of {persistence} consecutive supported annuli near the selected nonzero "
        "background (adaptive tolerance >= {annular:.3f}) with cumulative-median changes "
        "<= {cumulative:.3f}; >=80% of later supported annuli must remain within twice "
        "the annular tolerance; candidates at or beyond {censor:.0%} of discovery radius "
        "are unresolved"
    ).format(
        persistence=config["persistence_bins"],
        annular=config["annular_abs_tolerance"],
        cumulative=config["cumulative_abs_tolerance"],
        censor=config["censor_fraction"],
    )


def _validate_pairs(pairs: xr.Dataset) -> None:
    required = {
        "cold_synchrony",
        "warm_synchrony",
        "delta_s",
        "distance_km",
        "output_mask",
        "computation_mask",
        "source_index",
        "target_index",
    }
    missing = sorted(required.difference(set(pairs.variables)))
    if missing:
        raise TypeError(f"Pair table is missing required variables: {missing}")
    if pairs.attrs.get("analysis") != "local_synchrony_pairs":
        raise TypeError("Expected a local_synchrony_pairs Dataset")


def _write_checkpoint(summary: xr.Dataset, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.nc")
    clean = summary.copy()
    for name in clean.variables:
        clean[name].encoding = {}
    clean.to_netcdf(temporary, engine="scipy")
    temporary.replace(path)
    manifest = {
        "status": "complete",
        "path": path.name,
        "analysis_fingerprint": summary.attrs["analysis_fingerprint"],
        "checkpoint_compatibility_fingerprint": summary.attrs[
            "checkpoint_compatibility_fingerprint"
        ],
        "schema_version": RANGE_SCHEMA_VERSION,
        "sizes": dict(summary.sizes),
    }
    temporary_manifest = path.with_suffix(".partial.json")
    temporary_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary_manifest.replace(path.with_suffix(".json"))


def _load_checkpoint(path: Path, expected_compatibility: str) -> xr.Dataset:
    manifest = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise ValueError("Checkpoint manifest is not complete")
    if manifest.get("checkpoint_compatibility_fingerprint") != expected_compatibility:
        raise ValueError("Checkpoint compatibility fingerprint mismatch")
    with xr.open_dataset(path, engine="scipy") as opened:
        result = opened.load()
    if result.attrs.get("checkpoint_compatibility_fingerprint") != expected_compatibility:
        raise ValueError("Checkpoint dataset compatibility mismatch")
    return result


__all__ = [
    "RANGE_STATUS",
    "empirical_range_curve",
    "empirical_synchrony_range",
    "tiled_empirical_synchrony_range",
]
