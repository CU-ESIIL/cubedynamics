"""Exact non-stacked reductions of bounded local synchrony surfaces.

This module implements the deliberately simple baseline

``local pair relationships -> immediate per-focal scalar summaries``.

It does not retain a focal-by-offset stack, align overlapping surfaces, or
perform a second spatial reduction.  Canonical undirected pairs are evaluated
once within each computation tile and contribute to both endpoints when both
are requested focal pixels.  The self-pair is always excluded.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Sequence

import numpy as np
import xarray as xr

from ..config import TIME_DIM
from ..runtime import version_info
from .production import expand_spatial_domain, local_synchrony_pairs
from .spatial import infer_spatial_dims
from .stacks import _coordinate_values, _is_lat_lon, _select_inputs


BASELINE_SCHEMA_VERSION = "2"
_METRICS = {
    "cold": "cold_synchrony",
    "warm": "warm_synchrony",
    "delta": "delta_s",
}
_FLOAT_STATS = ("median", "mean", "std", "iqr", "mad", "min", "max", "p10", "p25", "p75", "p90")


def nonstacked_synchrony_summary(
    pairs: xr.Dataset,
    *,
    radii_km: Sequence[float] = (25.0, 50.0, 75.0, 100.0),
) -> xr.Dataset:
    """Immediately reduce each selected focal pixel's incident nonself pairs.

    Exact NumPy quantiles are calculated independently for cold, warm, and
    pairwise Delta values.  ``delta_pair_median`` is therefore kept separate
    from ``delta_median_difference = cold_median - warm_median``.
    """

    _validate_pairs(pairs)
    radii = np.asarray(tuple(float(value) for value in radii_km), dtype=float)
    if radii.ndim != 1 or radii.size == 0 or np.any(radii <= 0) or np.any(np.diff(radii) <= 0):
        raise ValueError("radii_km must be positive and strictly increasing")
    maximum = float(pairs.attrs["max_radius_km"])
    if radii[-1] > maximum + 1e-9:
        raise ValueError("radii_km cannot exceed the pair table's max_radius_km")

    y_dim, x_dim = pairs.output_mask.dims
    y_size, x_size = pairs.sizes[y_dim], pairs.sizes[x_dim]
    mask = np.asarray(pairs.output_mask.values, dtype=bool).reshape(-1)
    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    nonself = source != target

    source_selected = mask[source] & nonself
    target_selected = mask[target] & nonself
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

    shape = (radii.size, y_size * x_size)
    floats = {
        f"{metric}_{stat}": np.full(shape, np.nan, dtype=np.float64)
        for metric in _METRICS
        for stat in _FLOAT_STATS
    }
    integers = {
        f"{metric}_valid_pair_count": np.zeros(shape, dtype=np.int32)
        for metric in _METRICS
    }
    integers["expected_pair_count"] = np.zeros(shape, dtype=np.int32)
    fractions = {
        f"{metric}_valid_pair_fraction": np.full(shape, np.nan, dtype=np.float64)
        for metric in _METRICS
    }
    distance = np.asarray(pairs.distance_km.values, dtype=float)
    values = {
        metric: np.asarray(pairs[name].values, dtype=float)
        for metric, name in _METRICS.items()
    }
    started = time.perf_counter()

    for node in np.flatnonzero(mask):
        item = lookup.get(int(node))
        if item is None:
            continue
        start, count = item
        selected_pairs = contribution_pair[start : start + count]
        local_distance = distance[selected_pairs]
        for radius_index, radius in enumerate(radii):
            within = local_distance <= radius + 1e-7
            expected = int(np.count_nonzero(within))
            integers["expected_pair_count"][radius_index, node] = expected
            for metric, metric_values in values.items():
                local_values = metric_values[selected_pairs]
                valid = within & np.isfinite(local_values)
                observed = local_values[valid]
                valid_count = int(observed.size)
                integers[f"{metric}_valid_pair_count"][radius_index, node] = valid_count
                fractions[f"{metric}_valid_pair_fraction"][radius_index, node] = (
                    valid_count / expected if expected else np.nan
                )
                if not valid_count:
                    continue
                q10, q25, q50, q75, q90 = np.quantile(
                    observed, (0.10, 0.25, 0.50, 0.75, 0.90)
                )
                floats[f"{metric}_median"][radius_index, node] = q50
                floats[f"{metric}_mean"][radius_index, node] = np.mean(observed)
                floats[f"{metric}_std"][radius_index, node] = np.std(observed)
                floats[f"{metric}_iqr"][radius_index, node] = q75 - q25
                floats[f"{metric}_mad"][radius_index, node] = np.median(
                    np.abs(observed - q50)
                )
                floats[f"{metric}_min"][radius_index, node] = np.min(observed)
                floats[f"{metric}_max"][radius_index, node] = np.max(observed)
                for stat, value in zip(
                    ("p10", "p25", "p75", "p90"), (q10, q25, q75, q90)
                ):
                    floats[f"{metric}_{stat}"][radius_index, node] = value

    dims = ("time_window_end", "radius_km", y_dim, x_dim)
    coords = {
        "time_window_end": [np.datetime64(pairs.time_window_end.values)],
        "radius_km": radii,
        y_dim: pairs[y_dim],
        x_dim: pairs[x_dim],
    }
    data_vars = {
        name: (dims, array.reshape((1, radii.size, y_size, x_size)))
        for name, array in {**floats, **integers, **fractions}.items()
    }
    result = xr.Dataset(data_vars, coords=coords)
    result["output_mask"] = pairs.output_mask
    result = result.rename({"delta_median": "delta_pair_median"})
    result["delta_median_difference"] = result.cold_median - result.warm_median
    result["delta_reduction_gap"] = (
        result.delta_pair_median - result.delta_median_difference
    )
    result["valid_pair_count"] = result.delta_valid_pair_count
    result["valid_pair_fraction"] = result.delta_valid_pair_fraction

    for name in result.data_vars:
        if name == "output_mask" or name.endswith("count"):
            continue
        result[name].attrs["units"] = "1"
    result.delta_pair_median.attrs["definition"] = (
        "median of nonself pairwise (cold_synchrony - warm_synchrony)"
    )
    result.delta_median_difference.attrs["definition"] = (
        "nonself cold_median - nonself warm_median"
    )
    result.delta_reduction_gap.attrs["definition"] = (
        "delta_pair_median - delta_median_difference"
    )
    result.valid_pair_count.attrs["definition"] = "alias of delta_valid_pair_count"
    result.valid_pair_fraction.attrs["definition"] = (
        "alias of delta_valid_pair_fraction; valid nonself Delta pairs / expected nonself pairs"
    )

    fingerprint_payload = {
        "schema": BASELINE_SCHEMA_VERSION,
        "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
        "radii_km": radii.tolist(),
        "self_pair": "excluded",
        "quantile_method": "exact_numpy_quantile",
    }
    fingerprint = sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result.attrs.update(dict(pairs.attrs))
    result.attrs.update(
        {
            "analysis": "nonstacked_synchrony_summary",
            "semantic_kind": "summary",
            "baseline_schema_version": BASELINE_SCHEMA_VERSION,
            "analysis_fingerprint": f"sha256:{fingerprint}",
            "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
            "radii_km": ",".join(str(value) for value in radii),
            "self_pair_policy": "excluded before every reduction",
            "surface_retention_policy": "discarded after immediate scalar reduction",
            "stacking": "none",
            "overlap_alignment": "none",
            "second_stage_convolution": "none",
            "pair_reuse": "canonical undirected pairs contribute to both selected endpoints",
            "quantile_method": "exact numpy quantile over retained bounded nonself pairs",
            "primary_delta": "median of pairwise cold_synchrony - warm_synchrony",
            "signature_reduction_seconds": float(time.perf_counter() - started),
        }
    )
    return result


def tiled_nonstacked_synchrony_summary(
    obj: xr.Dataset | xr.DataArray,
    *,
    output_mask: xr.DataArray | np.ndarray,
    computation_mask: xr.DataArray | np.ndarray | None = None,
    lower_var: str | None = None,
    upper_var: str | None = None,
    radii_km: Sequence[float] = (25.0, 50.0, 75.0, 100.0),
    tile_shape: tuple[int, int] = (32, 32),
    window_days: int = 90,
    window_end: object | None = None,
    min_t: int = 10,
    split_quantile: float = 0.5,
    time_dim: str = TIME_DIM,
    pair_batch_size: int = 16384,
    checkpoint_dir: str | Path | None = None,
) -> xr.Dataset:
    """Run the exact non-stacked baseline in restartable halo-complete tiles."""

    radii = np.asarray(tuple(float(value) for value in radii_km), dtype=float)
    if radii.ndim != 1 or radii.size == 0 or np.any(radii <= 0) or np.any(np.diff(radii) <= 0):
        raise ValueError("radii_km must be positive and strictly increasing")
    if len(tile_shape) != 2 or tile_shape[0] < 1 or tile_shape[1] < 1:
        raise ValueError("tile_shape must contain two positive integers")
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
    pair_calculation_count = nonself_pair_calculation_count = 0
    pair_kernel_seconds = pair_geometry_seconds = 0.0
    input_materialization_seconds = reduction_seconds = 0.0
    source_attrs = dict(getattr(obj, "attrs", {}))
    runtime = version_info()
    common = {
        "baseline_schema_version": BASELINE_SCHEMA_VERSION,
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
        "radii_km": radii.tolist(),
        "window_days": int(window_days),
        "window_end": None if window_end is None else str(np.datetime64(window_end)),
        "min_t": int(min_t),
        "split_quantile": float(split_quantile),
        "self_pair": "excluded",
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
                float(x_values[xi].min()), float(y_values[yi].min()),
                float(x_values[xi].max()), float(y_values[yi].max()),
            )
            halo_bounds = expand_spatial_domain(output_bounds, float(radii[-1])).bounds
            halo_y = np.flatnonzero((y_values >= halo_bounds[1]) & (y_values <= halo_bounds[3]))
            halo_x = np.flatnonzero((x_values >= halo_bounds[0]) & (x_values <= halo_bounds[2]))
            if halo_y.size == 0 or halo_x.size == 0:
                raise ValueError("A tile halo does not intersect the computation cube")
            y_slice = slice(int(halo_y.min()), int(halo_y.max()) + 1)
            x_slice = slice(int(halo_x.min()), int(halo_x.max()) + 1)
            subset = obj.isel({y_dim: y_slice, x_dim: x_slice})
            subset_mask = xr.DataArray(
                tile_mask[y_slice, x_slice], dims=(y_dim, x_dim),
                coords={y_dim: subset[y_dim], x_dim: subset[x_dim]},
            )
            subset_computation_mask = xr.DataArray(
                eligible[y_slice, x_slice], dims=(y_dim, x_dim),
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
                checkpoint_root / f"baseline_y{y_start:05d}-{y_stop:05d}_x{x_start:05d}-{x_stop:05d}.nc"
                if checkpoint_root is not None else None
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
                    computation_mask=subset_computation_mask,
                    max_radius_km=float(radii[-1]),
                    window_days=window_days,
                    window_end=window_end,
                    min_t=min_t,
                    split_quantile=split_quantile,
                    time_dim=time_dim,
                    pair_batch_size=pair_batch_size,
                )
                summary = nonstacked_synchrony_summary(pairs, radii_km=radii)
                summary.attrs["checkpoint_compatibility_fingerprint"] = compatibility
                summary.attrs.update(
                    {
                        "tile_index_bounds": json.dumps([y_start, y_stop, x_start, x_stop]),
                        "halo_index_bounds": json.dumps([y_slice.start, y_slice.stop, x_slice.start, x_slice.stop]),
                        "output_tile_shape": f"{y_stop-y_start},{x_stop-x_start}",
                        "computation_tile_shape": f"{y_slice.stop-y_slice.start},{x_slice.stop-x_slice.start}",
                        "maximum_halo_radius_km": float(radii[-1]),
                    }
                )
                summary = summary.reindex({y_dim: output_y, x_dim: output_x})
                if checkpoint is not None:
                    _write_checkpoint(summary, checkpoint)
                computed_tiles += 1
            pair_calculation_count += int(summary.attrs.get("unique_pair_count", 0))
            nonself_pair_calculation_count += int(summary.attrs.get("nonself_pair_count", 0))
            pair_kernel_seconds += float(summary.attrs.get("pair_kernel_seconds", 0.0))
            pair_geometry_seconds += float(summary.attrs.get("geometry_seconds", 0.0))
            input_materialization_seconds += float(summary.attrs.get("input_materialization_seconds", 0.0))
            reduction_seconds += float(summary.attrs.get("signature_reduction_seconds", 0.0))
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
            "analysis": "nonstacked_synchrony_summary",
            "execution": "restartable output tiling with full-radius coordinate halos",
            "tile_shape": f"{int(tile_shape[0])},{int(tile_shape[1])}",
            "tile_count": int(len(pieces)),
            "computed_tile_count": int(computed_tiles),
            "resumed_tile_count": int(resumed_tiles),
            "pair_calculation_count_with_tile_recompute": int(pair_calculation_count),
            "nonself_pair_calculation_count_with_tile_recompute": int(nonself_pair_calculation_count),
            "pair_kernel_seconds_sum": float(pair_kernel_seconds),
            "pair_geometry_seconds_sum": float(pair_geometry_seconds),
            "input_materialization_seconds_sum": float(input_materialization_seconds),
            "signature_reduction_seconds_sum": float(reduction_seconds),
            "cross_tile_pair_policy": "endpoint_tile_recompute; no permanent pair store",
            "computation_mask_policy": (
                "explicit eligible spatial nodes" if computation_mask is not None
                else "all rectangular-grid nodes"
            ),
            "surface_retention_policy": "discarded after immediate scalar reduction",
            "quantile_method": "exact within each complete focal neighborhood",
            "cubedynamics_version": runtime.version,
            "cubedynamics_git_sha": runtime.git_sha or "unavailable",
        }
    )
    return combined


def _normalize_output_mask(value, reference, y_dim: str, x_dim: str) -> np.ndarray:
    if isinstance(value, xr.DataArray):
        template = reference.isel(
            {dim: 0 for dim in reference.dims if dim not in (y_dim, x_dim)}
        )
        aligned, _ = xr.align(value.transpose(y_dim, x_dim), template, join="exact")
        array = np.asarray(aligned.values, dtype=bool)
    else:
        array = np.asarray(value, dtype=bool)
    expected = (reference.sizes[y_dim], reference.sizes[x_dim])
    if array.shape != expected:
        raise ValueError(f"output_mask shape {array.shape!r} does not match {expected!r}")
    return array


def _validate_pairs(pairs: xr.Dataset) -> None:
    required = {
        "cold_synchrony", "warm_synchrony", "delta_s", "distance_km",
        "output_mask", "source_index", "target_index",
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
        "checkpoint_compatibility_fingerprint": summary.attrs["checkpoint_compatibility_fingerprint"],
        "schema_version": BASELINE_SCHEMA_VERSION,
        "sizes": dict(summary.sizes),
    }
    temporary_manifest = path.with_suffix(".partial.json")
    temporary_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
