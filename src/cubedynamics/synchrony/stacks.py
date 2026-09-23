"""Spatial stacks of the validated median-split synchrony statistic.

The public stack is dense over requested centers and focal pixels because that
is the scientific object users inspect. Calculation is performed on canonical
undirected pairs so symmetric values are evaluated once.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import xarray as xr

from ..config import TIME_DIM
from ..stats.tails import _rank_1d, one_tail_spearman
from .spatial import infer_spatial_dims


STACK_SCHEMA_VERSION = "1"
_DIRECTION_LABELS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def local_synchrony_stack(
    obj: xr.Dataset | xr.DataArray,
    *,
    lower_var: str | None = None,
    upper_var: str | None = None,
    window_days: int = 90,
    window_end: object | None = None,
    min_t: int = 5,
    split_quantile: float = 0.5,
    time_dim: str = TIME_DIM,
    center_y_indices: Sequence[int] | slice | None = None,
    center_x_indices: Sequence[int] | slice | None = None,
    max_radius_km: float | None = None,
    distance_bands_km: Sequence[float] = (25.0, 50.0, 100.0, 250.0),
    pair_batch_size: int = 4096,
) -> xr.Dataset:
    """Return unreduced center-by-focal cold, warm, and difference stacks.

    This operation explicitly materializes one bounded time window. It is
    intended to be called on one center tile plus its focal halo, not on a
    national dense domain.
    """

    if not 0.0 < split_quantile <= 0.5:
        raise ValueError("split_quantile must be greater than 0 and no greater than 0.5")
    if min_t < 2:
        raise ValueError("min_t must be at least 2")
    if window_days < 0:
        raise ValueError("window_days must be non-negative")
    if pair_batch_size < 1:
        raise ValueError("pair_batch_size must be at least 1")
    if max_radius_km is not None and max_radius_km <= 0:
        raise ValueError("max_radius_km must be positive")

    lower, upper, lower_name, upper_name = _select_inputs(obj, lower_var, upper_var)
    if lower.dims != upper.dims:
        raise ValueError(
            f"Selected variables must have matching dims; got {lower.dims!r} and {upper.dims!r}"
        )
    y_dim, x_dim = infer_spatial_dims(lower)
    if time_dim not in lower.dims:
        raise ValueError(f"Synchrony stacks require time dimension {time_dim!r}")
    if lower.sizes[time_dim] == 0:
        raise ValueError("Synchrony stacks require at least one time step")

    end_value = lower[time_dim].values[-1] if window_end is None else np.datetime64(window_end)
    start_value = end_value - np.timedelta64(window_days, "D")
    lower_window = lower.sel({time_dim: slice(start_value, end_value)})
    upper_window = upper.sel({time_dim: slice(start_value, end_value)})
    if lower_window.sizes.get(time_dim, 0) < min_t:
        raise ValueError(
            "Selected rolling window has fewer time labels than min_t: "
            f"{lower_window.sizes.get(time_dim, 0)} < {min_t}"
        )
    lower_window, upper_window = xr.align(lower_window, upper_window, join="exact")

    y_size = int(lower.sizes[y_dim])
    x_size = int(lower.sizes[x_dim])
    center_y = _normalize_indices(center_y_indices, y_size, y_dim)
    center_x = _normalize_indices(center_x_indices, x_size, x_dim)
    center_flat = np.asarray(
        [yi * x_size + xi for yi in center_y for xi in center_x], dtype=np.int64
    )
    focal_flat = np.arange(y_size * x_size, dtype=np.int64)

    directed_left = np.repeat(center_flat, focal_flat.size)
    directed_right = np.tile(focal_flat, center_flat.size)
    y_values = _coordinate_values(lower, y_dim)
    x_values = _coordinate_values(lower, x_dim)
    latitude_longitude = _is_lat_lon(lower, y_dim, x_dim, y_values, x_values)
    distance_km, bearing = _center_focal_geometry(
        center_flat,
        focal_flat,
        y_values=y_values,
        x_values=x_values,
        x_size=x_size,
        latitude_longitude=latitude_longitude,
    )
    geometry_shape = (center_flat.size, y_size, x_size)
    distance_km = distance_km.reshape(geometry_shape)
    bearing = bearing.reshape(geometry_shape)
    radius_mask = np.ones(distance_km.shape, dtype=bool)
    if max_radius_km is not None:
        radius_mask = distance_km <= max_radius_km
    active_directed = radius_mask.reshape(-1)
    active_left = directed_left[active_directed]
    active_right = directed_right[active_directed]
    canonical_left = np.minimum(active_left, active_right)
    canonical_right = np.maximum(active_left, active_right)
    pair_codes = canonical_left * focal_flat.size + canonical_right
    unique_codes, gather = np.unique(pair_codes, return_inverse=True)
    pair_left = unique_codes // focal_flat.size
    pair_right = unique_codes % focal_flat.size

    lower_values = _materialize_pixel_time(lower_window, time_dim, y_dim, x_dim)
    upper_values = _materialize_pixel_time(upper_window, time_dim, y_dim, x_dim)
    cold_unique = np.full(unique_codes.size, np.nan, dtype=np.float32)
    warm_unique = np.full(unique_codes.size, np.nan, dtype=np.float32)
    cold_count_unique = np.zeros(unique_codes.size, dtype=np.int16)
    warm_count_unique = np.zeros(unique_codes.size, dtype=np.int16)

    for batch_start in range(0, unique_codes.size, pair_batch_size):
        batch_stop = min(batch_start + pair_batch_size, unique_codes.size)
        for pair_index in range(batch_start, batch_stop):
            left = int(pair_left[pair_index])
            right = int(pair_right[pair_index])
            cold, cold_count_value = one_tail_spearman(
                lower_values[left],
                lower_values[right],
                tail="lower",
                b=split_quantile,
                min_t=min_t,
            )
            warm, warm_count_value = one_tail_spearman(
                upper_values[left],
                upper_values[right],
                tail="upper",
                b=split_quantile,
                min_t=min_t,
            )
            cold_unique[pair_index] = cold
            warm_unique[pair_index] = warm
            cold_count_unique[pair_index] = cold_count_value
            warm_count_unique[pair_index] = warm_count_value

    shape = (center_flat.size, y_size, x_size)
    cold_directed = np.full(directed_left.size, np.nan, dtype=np.float32)
    warm_directed = np.full(directed_left.size, np.nan, dtype=np.float32)
    cold_count_directed = np.zeros(directed_left.size, dtype=np.int32)
    warm_count_directed = np.zeros(directed_left.size, dtype=np.int32)
    cold_directed[active_directed] = cold_unique[gather]
    warm_directed[active_directed] = warm_unique[gather]
    cold_count_directed[active_directed] = cold_count_unique[gather]
    warm_count_directed[active_directed] = warm_count_unique[gather]
    cold_stack = cold_directed.reshape(shape)
    warm_stack = warm_directed.reshape(shape)
    cold_count = cold_count_directed.reshape(shape)
    warm_count = warm_count_directed.reshape(shape)
    delta_stack = cold_stack - warm_stack

    bands = np.asarray(tuple(float(v) for v in distance_bands_km), dtype=float)
    if bands.size and (np.any(bands <= 0) or np.any(np.diff(bands) <= 0)):
        raise ValueError("distance_bands_km must be strictly increasing positive values")
    distance_band = np.digitize(distance_km, bands, right=True).astype(np.int16)
    direction_code = _direction_codes(bearing)
    center_y_idx = center_flat // x_size
    center_x_idx = center_flat % x_size
    coords = {
        "center": np.arange(center_flat.size, dtype=np.int32),
        y_dim: lower[y_dim],
        x_dim: lower[x_dim],
        "center_y_index": ("center", center_y_idx.astype(np.int32)),
        "center_x_index": ("center", center_x_idx.astype(np.int32)),
        "center_y": ("center", y_values[center_y_idx]),
        "center_x": ("center", x_values[center_x_idx]),
        "time_window_end": np.datetime64(end_value),
    }
    dims = ("center", y_dim, x_dim)
    result = xr.Dataset(
        {
            "cold_synchrony": (dims, cold_stack),
            "warm_synchrony": (dims, warm_stack),
            "delta_s": (dims, delta_stack.astype(np.float32)),
            "cold_joint_count": (dims, cold_count),
            "warm_joint_count": (dims, warm_count),
            "distance_km": (dims, distance_km.astype(np.float32)),
            "bearing_degrees": (dims, bearing.astype(np.float32)),
            "distance_band": (dims, distance_band),
            "direction_code": (dims, direction_code),
        },
        coords=coords,
    )
    for name in ("cold_synchrony", "warm_synchrony"):
        result[name].attrs.update({"units": "1", "valid_range": "-1 to 1"})
    result["delta_s"].attrs.update(
        {
            "long_name": "Cold-tail minus warm-tail Spearman synchrony",
            "units": "1",
            "valid_range": "-2 to 2",
            "positive_values": "cold-tail synchrony exceeds warm-tail synchrony",
            "negative_values": "warm-tail synchrony exceeds cold-tail synchrony",
        }
    )
    result["distance_km"].attrs.update(
        {"units": "km", "geometry": "great_circle" if latitude_longitude else "euclidean"}
    )
    result["bearing_degrees"].attrs.update(
        {"units": "degrees", "definition": "forward bearing from center to focal pixel"}
    )
    result["direction_code"].attrs.update(
        {"labels": ",".join(f"{i}:{label}" for i, label in enumerate(_DIRECTION_LABELS)), "undefined": -1}
    )
    result["distance_band"].attrs.update(
        {"edges_km": ",".join(str(value) for value in bands), "right_inclusive": 1}
    )
    fingerprint_payload = {
        "schema_version": STACK_SCHEMA_VERSION,
        "lower_variable": lower_name,
        "upper_variable": upper_name,
        "window_start": str(np.datetime64(start_value)),
        "window_end": str(np.datetime64(end_value)),
        "window_days": window_days,
        "min_t": min_t,
        "split_quantile": split_quantile,
        "shape": [y_size, x_size],
        "centers": center_flat.tolist(),
        "y_hash": sha256(y_values.tobytes()).hexdigest(),
        "x_hash": sha256(x_values.tobytes()).hexdigest(),
        "radius_km": max_radius_km,
        "distance_bands_km": bands.tolist(),
    }
    fingerprint = sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    result.attrs.update(
        {
            "analysis": "local_synchrony_stack",
            "semantic_kind": "relationship",
            "semantic_category": "relationship_stack",
            "stack_schema_version": STACK_SCHEMA_VERSION,
            "analysis_fingerprint": f"sha256:{fingerprint}",
            "lower_variable": lower_name,
            "upper_variable": upper_name,
            "window_days": window_days,
            "window_start": str(np.datetime64(start_value)),
            "window_end": str(np.datetime64(end_value)),
            "window_definition": f"inclusive trailing {window_days}-day coordinate-label window",
            "min_time_points_per_tail": min_t,
            "split_quantile": split_quantile,
            "split_definition": (
                "per-series quantiles; cold uses joint <= lower thresholds; "
                "warm uses joint > upper thresholds"
            ),
            "pair_symmetry": "S(i,j)=S(j,i); canonical undirected pair computed once",
            "unique_pair_count": int(unique_codes.size),
            "requested_relationship_count": int(directed_left.size),
            "computed_relationship_count": int(np.count_nonzero(active_directed)),
            "pair_batch_size": int(pair_batch_size),
            "materialization": "one bounded time window materialized before coarse pair batches",
            "center_tile": f"{len(center_y)}x{len(center_x)}",
            "focal_grid": f"{y_size}x{x_size}",
            "max_radius_km": "none" if max_radius_km is None else float(max_radius_km),
        }
    )
    return result


def reduce_synchrony_stack(
    stack: xr.Dataset,
    *,
    metric: str = "delta_s",
    near_field_km: float = 50.0,
    distance_decay_km: float = 100.0,
) -> xr.Dataset:
    """Reduce a center stack while retaining coverage and distribution shape."""

    _validate_stack(stack, metric)
    if near_field_km <= 0 or distance_decay_km <= 0:
        raise ValueError("near_field_km and distance_decay_km must be positive")
    values = stack[metric]
    count = values.count("center")
    median = values.median("center", skipna=True)
    q05 = values.quantile(0.05, dim="center", skipna=True).drop_vars("quantile")
    q25 = values.quantile(0.25, dim="center", skipna=True).drop_vars("quantile")
    q75 = values.quantile(0.75, dim="center", skipna=True).drop_vars("quantile")
    q95 = values.quantile(0.95, dim="center", skipna=True).drop_vars("quantile")
    weights = np.exp(-stack["distance_km"] / distance_decay_km).where(values.notnull())
    weighted = (values * weights).sum("center", skipna=True) / weights.sum("center", skipna=True)
    near = values.where(stack["distance_km"] <= near_field_km)
    output = xr.Dataset(
        {
            "valid_center_count": count,
            "spatial_coverage": count / max(int(stack.sizes["center"]), 1),
            "mean": values.mean("center", skipna=True),
            "median": median,
            "standard_deviation": values.std("center", skipna=True),
            "iqr": q75 - q25,
            "mad": abs(values - median).median("center", skipna=True),
            "minimum": values.min("center", skipna=True),
            "maximum": values.max("center", skipna=True),
            "q05": q05,
            "q25": q25,
            "q75": q75,
            "q95": q95,
            "distance_weighted_mean": weighted,
            "near_field_median": near.median("center", skipna=True),
        }
    )
    for band in np.unique(stack["distance_band"].values):
        selected = values.where(stack["distance_band"] == band)
        output[f"distance_band_{int(band)}_median"] = selected.median("center", skipna=True)
        output[f"distance_band_{int(band)}_count"] = selected.count("center")
    for direction, label in enumerate(_DIRECTION_LABELS):
        selected = values.where(stack["direction_code"] == direction)
        output[f"direction_{label.lower()}_mean"] = selected.mean("center", skipna=True)
        output[f"direction_{label.lower()}_count"] = selected.count("center")
    output.attrs.update(
        {
            "analysis": "reduce_synchrony_stack",
            "source_metric": metric,
            "source_analysis_fingerprint": stack.attrs.get("analysis_fingerprint", "unknown"),
            "near_field_km": float(near_field_km),
            "distance_weight": f"exp(-distance_km/{distance_decay_km})",
            "experimental_metrics": "none; entropy and multimodality deliberately deferred",
        }
    )
    return output


def synchrony_landscape_similarity(
    stack: xr.Dataset,
    *,
    metric: str = "delta_s",
    adjacency: int = 4,
    min_overlap: int = 5,
) -> xr.Dataset:
    """Compare adjacent centers' full landscapes as panel similarity ``Q``.

    ``Q(A, B)`` is Spearman correlation between two center landscapes over
    shared finite focal pixels. It is distinct from pair synchrony ``S(A, B)``.
    """

    _validate_stack(stack, metric)
    if adjacency not in (4, 8):
        raise ValueError("adjacency must be 4 or 8")
    if min_overlap < 2:
        raise ValueError("min_overlap must be at least 2")
    center_y = np.asarray(stack["center_y_index"].values, dtype=int)
    center_x = np.asarray(stack["center_x_index"].values, dtype=int)
    lookup = {(int(y), int(x)): index for index, (y, x) in enumerate(zip(center_y, center_x))}
    offsets = ((0, 1), (1, 0)) if adjacency == 4 else ((0, 1), (1, -1), (1, 0), (1, 1))
    comparisons: list[tuple[int, int]] = []
    for index, (y, x) in enumerate(zip(center_y, center_x)):
        for dy, dx in offsets:
            other = lookup.get((int(y + dy), int(x + dx)))
            if other is not None:
                comparisons.append((index, other))

    raw = np.asarray(stack[metric].values, dtype=float).reshape(stack.sizes["center"], -1)
    similarity = np.full(len(comparisons), np.nan, dtype=np.float32)
    pearson = np.full(len(comparisons), np.nan, dtype=np.float32)
    cosine = np.full(len(comparisons), np.nan, dtype=np.float32)
    rmse = np.full(len(comparisons), np.nan, dtype=np.float32)
    overlap = np.zeros(len(comparisons), dtype=np.int32)
    for comparison_index, (left_index, right_index) in enumerate(comparisons):
        left = raw[left_index]
        right = raw[right_index]
        valid = np.isfinite(left) & np.isfinite(right)
        overlap[comparison_index] = int(np.count_nonzero(valid))
        if overlap[comparison_index] < min_overlap:
            continue
        left_valid = left[valid]
        right_valid = right[valid]
        similarity[comparison_index] = _pearson(_rank_1d(left_valid), _rank_1d(right_valid))
        pearson[comparison_index] = _pearson(left_valid, right_valid)
        denominator = np.linalg.norm(left_valid) * np.linalg.norm(right_valid)
        if denominator > 0:
            cosine[comparison_index] = float(np.dot(left_valid, right_valid) / denominator)
        rmse[comparison_index] = float(np.sqrt(np.mean((left_valid - right_valid) ** 2)))

    change = 1.0 - similarity
    sum_change = np.zeros(stack.sizes["center"], dtype=float)
    valid_neighbors = np.zeros(stack.sizes["center"], dtype=np.int16)
    for comparison_index, (left_index, right_index) in enumerate(comparisons):
        if np.isfinite(change[comparison_index]):
            sum_change[left_index] += change[comparison_index]
            sum_change[right_index] += change[comparison_index]
            valid_neighbors[left_index] += 1
            valid_neighbors[right_index] += 1
    center_change = np.full(stack.sizes["center"], np.nan, dtype=np.float32)
    finite = valid_neighbors > 0
    center_change[finite] = sum_change[finite] / valid_neighbors[finite]

    unique_y = np.unique(center_y)
    unique_x = np.unique(center_x)
    grid_change = np.full((unique_y.size, unique_x.size), np.nan, dtype=np.float32)
    grid_neighbors = np.zeros((unique_y.size, unique_x.size), dtype=np.int16)
    y_position = {value: index for index, value in enumerate(unique_y)}
    x_position = {value: index for index, value in enumerate(unique_x)}
    for index, (y, x) in enumerate(zip(center_y, center_x)):
        grid_change[y_position[y], x_position[x]] = center_change[index]
        grid_neighbors[y_position[y], x_position[x]] = valid_neighbors[index]

    left_indices = np.asarray([pair[0] for pair in comparisons], dtype=np.int32)
    right_indices = np.asarray([pair[1] for pair in comparisons], dtype=np.int32)
    result = xr.Dataset(
        {
            "panel_similarity": ("comparison", similarity),
            "landscape_change": ("comparison", change.astype(np.float32)),
            "pearson_similarity": ("comparison", pearson),
            "cosine_similarity": ("comparison", cosine),
            "rmse": ("comparison", rmse),
            "overlap_count": ("comparison", overlap),
            "mean_adjacent_landscape_change": (("center_y", "center_x"), grid_change),
            "valid_neighbor_count": (("center_y", "center_x"), grid_neighbors),
        },
        coords={
            "comparison": np.arange(len(comparisons), dtype=np.int32),
            "center_a": ("comparison", left_indices),
            "center_b": ("comparison", right_indices),
            "center_a_y_index": ("comparison", center_y[left_indices]),
            "center_a_x_index": ("comparison", center_x[left_indices]),
            "center_b_y_index": ("comparison", center_y[right_indices]),
            "center_b_x_index": ("comparison", center_x[right_indices]),
            "center_y": unique_y,
            "center_x": unique_x,
        },
    )
    result.attrs.update(
        {
            "analysis": "synchrony_landscape_similarity",
            "source_metric": metric,
            "panel_similarity_definition": "Q(A,B): Spearman correlation between full center landscapes",
            "landscape_change_definition": "1 - Q(A,B); map is mean over valid adjacent comparisons",
            "pair_synchrony_distinction": "Q compares panels and is not S(A,B)",
            "adjacency": adjacency,
            "minimum_overlap": min_overlap,
            "source_analysis_fingerprint": stack.attrs.get("analysis_fingerprint", "unknown"),
        }
    )
    return result


def stack_edges(stack: xr.Dataset, *, validate_symmetry: bool = True) -> xr.Dataset:
    """Convert a dense stack to one row per canonical undirected pair."""

    _validate_stack(stack, "delta_s")
    y_dim, x_dim = _stack_spatial_dims(stack)
    x_size = int(stack.sizes[x_dim])
    center_flat = (
        np.asarray(stack["center_y_index"].values, dtype=np.int64) * x_size
        + np.asarray(stack["center_x_index"].values, dtype=np.int64)
    )
    focal_flat = np.arange(int(stack.sizes[y_dim]) * x_size, dtype=np.int64)
    seen: dict[tuple[int, int], tuple[int, int]] = {}
    for center_index, center_value in enumerate(center_flat):
        for focal_value in focal_flat:
            key = (int(min(center_value, focal_value)), int(max(center_value, focal_value)))
            focal_y, focal_x = divmod(int(focal_value), x_size)
            if key in seen and validate_symmetry:
                old_center, old_focal = seen[key]
                old_y, old_x = divmod(old_focal, x_size)
                for name in ("cold_synchrony", "warm_synchrony", "delta_s"):
                    old = float(stack[name].values[old_center, old_y, old_x])
                    new = float(stack[name].values[center_index, focal_y, focal_x])
                    if not np.isclose(old, new, equal_nan=True, atol=1e-7, rtol=0):
                        raise ValueError(f"Stack is not symmetric for {name!r} at canonical pair {key}")
                continue
            seen[key] = (center_index, int(focal_value))
    keys = sorted(seen)
    variables: dict[str, tuple[tuple[str], np.ndarray]] = {}
    for name in ("cold_synchrony", "warm_synchrony", "delta_s", "cold_joint_count", "warm_joint_count"):
        values = []
        for key in keys:
            center_index, focal = seen[key]
            focal_y, focal_x = divmod(focal, x_size)
            values.append(stack[name].values[center_index, focal_y, focal_x])
        variables[name] = (("pair",), np.asarray(values))
    result = xr.Dataset(
        variables,
        coords={
            "pair": np.arange(len(keys), dtype=np.int64),
            "source_index": ("pair", np.asarray([key[0] for key in keys], dtype=np.int64)),
            "target_index": ("pair", np.asarray([key[1] for key in keys], dtype=np.int64)),
        },
    )
    result.attrs.update(stack.attrs)
    result.attrs["representation"] = "canonical_undirected_edges"
    return result


def write_stack_checkpoint(stack: xr.Dataset, path: str | Path) -> Path:
    """Write one complete bounded stack and a fingerprint-bound manifest."""

    _validate_stack(stack, "delta_s")
    target = Path(path)
    if target.suffix != ".nc":
        raise ValueError("Bounded phase-one checkpoints must use a .nc path")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".partial.nc")
    stack.to_netcdf(temporary)
    temporary.replace(target)
    manifest = target.with_suffix(".json")
    manifest.write_text(
        json.dumps(
            {
                "status": "complete",
                "path": target.name,
                "analysis_fingerprint": stack.attrs["analysis_fingerprint"],
                "schema_version": stack.attrs["stack_schema_version"],
                "sizes": dict(stack.sizes),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def load_stack_checkpoint(path: str | Path, *, expected_fingerprint: str) -> xr.Dataset:
    """Load a complete checkpoint only when its fingerprint matches exactly."""

    target = Path(path)
    manifest_path = target.with_suffix(".json")
    if not target.exists() or not manifest_path.exists():
        raise FileNotFoundError("Checkpoint data and manifest must both exist")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise ValueError("Checkpoint manifest is not complete")
    observed = manifest.get("analysis_fingerprint")
    if observed != expected_fingerprint:
        raise ValueError(
            f"Checkpoint fingerprint mismatch: expected {expected_fingerprint!r}, observed {observed!r}"
        )
    result = xr.open_dataset(target).load()
    if result.attrs.get("analysis_fingerprint") != expected_fingerprint:
        raise ValueError("Checkpoint dataset fingerprint does not match its manifest")
    return result


def _select_inputs(
    obj: xr.Dataset | xr.DataArray,
    lower_var: str | None,
    upper_var: str | None,
) -> tuple[xr.DataArray, xr.DataArray, str, str]:
    if (lower_var is None) != (upper_var is None):
        raise ValueError("lower_var and upper_var must be provided together")
    if isinstance(obj, xr.DataArray):
        if lower_var is not None:
            raise ValueError("lower_var and upper_var are only valid for Dataset inputs")
        name = obj.name or "value"
        return obj, obj, name, name
    if not isinstance(obj, xr.Dataset):
        raise TypeError("local_synchrony_stack requires an xarray DataArray or Dataset")
    if lower_var is None:
        if len(obj.data_vars) != 1:
            raise ValueError("Multi-variable Dataset inputs require lower_var and upper_var")
        name = next(iter(obj.data_vars))
        return obj[name], obj[name], name, name
    missing = [name for name in (lower_var, upper_var) if name not in obj]
    if missing:
        raise ValueError(f"Variables not found in Dataset: {missing!r}")
    return obj[lower_var], obj[upper_var], lower_var, upper_var


def _normalize_indices(
    selection: Sequence[int] | slice | None, size: int, dimension: str
) -> np.ndarray:
    if selection is None:
        values = np.arange(size, dtype=int)
    elif isinstance(selection, slice):
        values = np.arange(size, dtype=int)[selection]
    else:
        values = np.asarray(tuple(selection), dtype=int)
    if values.size == 0:
        raise ValueError(f"Center selection for {dimension!r} is empty")
    if np.any(values < 0) or np.any(values >= size):
        raise ValueError(f"Center indices for {dimension!r} are outside [0, {size})")
    if np.unique(values).size != values.size:
        raise ValueError(f"Center indices for {dimension!r} contain duplicates")
    return values


def _coordinate_values(obj: xr.DataArray, dimension: str) -> np.ndarray:
    if dimension not in obj.coords or obj[dimension].ndim != 1:
        raise ValueError(f"Spatial dimension {dimension!r} requires a one-dimensional coordinate")
    values = np.asarray(obj[dimension].values, dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise ValueError(f"Spatial coordinate {dimension!r} contains non-finite values")
    return values


def _is_lat_lon(
    obj: xr.DataArray,
    y_dim: str,
    x_dim: str,
    y_values: np.ndarray,
    x_values: np.ndarray,
) -> bool:
    y_attrs = obj[y_dim].attrs
    x_attrs = obj[x_dim].attrs
    explicit = (
        y_attrs.get("standard_name") == "latitude"
        and x_attrs.get("standard_name") == "longitude"
    ) or (
        "degrees_north" in str(y_attrs.get("units", ""))
        and "degrees_east" in str(x_attrs.get("units", ""))
    )
    spatial_reference = str(obj.attrs.get("spatial_reference", "")).upper()
    geographic_crs = any(code in spatial_reference for code in ("EPSG:4326", "EPSG:4269"))
    if not (explicit or geographic_crs):
        raise ValueError(
            "Kilometer distance and bearing require explicit latitude/longitude metadata: "
            "set y/x standard_name and degree units or a geographic spatial_reference."
        )
    if not (
        np.all((-90 <= y_values) & (y_values <= 90))
        and np.all((-180 <= x_values) & (x_values <= 180))
    ):
        raise ValueError("Declared latitude/longitude coordinates fall outside valid ranges")
    return True


def _materialize_pixel_time(
    array: xr.DataArray, time_dim: str, y_dim: str, x_dim: str
) -> np.ndarray:
    ordered = array.transpose(y_dim, x_dim, time_dim)
    if ordered.chunks is not None:
        ordered = ordered.compute()
    values = np.asarray(ordered.values, dtype=float)
    return values.reshape(-1, values.shape[-1])


def _center_focal_geometry(
    centers: np.ndarray,
    focals: np.ndarray,
    *,
    y_values: np.ndarray,
    x_values: np.ndarray,
    x_size: int,
    latitude_longitude: bool,
) -> tuple[np.ndarray, np.ndarray]:
    center_y = y_values[centers // x_size][:, None]
    center_x = x_values[centers % x_size][:, None]
    focal_y = y_values[focals // x_size][None, :]
    focal_x = x_values[focals % x_size][None, :]
    if latitude_longitude:
        lat1 = np.deg2rad(center_y)
        lat2 = np.deg2rad(focal_y)
        dlat = lat2 - lat1
        dlon = np.deg2rad(focal_x - center_x)
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        distance = 6371.0088 * 2 * np.arctan2(np.sqrt(a), np.sqrt(np.maximum(0.0, 1.0 - a)))
        bearing = np.rad2deg(
            np.arctan2(
                np.sin(dlon) * np.cos(lat2),
                np.cos(lat1) * np.sin(lat2)
                - np.sin(lat1) * np.cos(lat2) * np.cos(dlon),
            )
        )
        bearing = (bearing + 360.0) % 360.0
    else:
        dy = focal_y - center_y
        dx = focal_x - center_x
        distance = np.sqrt(dx**2 + dy**2)
        bearing = (np.rad2deg(np.arctan2(dx, dy)) + 360.0) % 360.0
    self_mask = distance == 0
    bearing = np.where(self_mask, np.nan, bearing)
    return distance, bearing


def _direction_codes(bearing: np.ndarray) -> np.ndarray:
    codes = np.full(bearing.shape, -1, dtype=np.int8)
    finite = np.isfinite(bearing)
    codes[finite] = (np.floor((bearing[finite] + 22.5) / 45.0).astype(int) % 8).astype(np.int8)
    return codes


def _pearson(left: np.ndarray, right: np.ndarray) -> float:
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = np.linalg.norm(left_centered) * np.linalg.norm(right_centered)
    if denominator <= 0 or not np.isfinite(denominator):
        return float("nan")
    return float(np.dot(left_centered, right_centered) / denominator)


def _stack_spatial_dims(stack: xr.Dataset) -> tuple[str, str]:
    candidates = [
        dim
        for dim in stack["delta_s"].dims
        if dim != "center" and not dim.endswith("window_end")
    ]
    if len(candidates) != 2:
        raise ValueError("Stack must have exactly two focal spatial dimensions")
    return str(candidates[0]), str(candidates[1])


def _validate_stack(stack: xr.Dataset, metric: str) -> None:
    if not isinstance(stack, xr.Dataset) or stack.attrs.get("analysis") != "local_synchrony_stack":
        raise TypeError("Expected a Dataset produced by local_synchrony_stack")
    required = {metric, "distance_km", "distance_band", "direction_code"}
    missing = sorted(required - set(stack.data_vars))
    if missing:
        raise ValueError(f"Stack is missing required variables: {missing!r}")
    if "center" not in stack[metric].dims:
        raise ValueError(f"Stack metric {metric!r} must have a center dimension")


__all__ = [
    "STACK_SCHEMA_VERSION",
    "load_stack_checkpoint",
    "local_synchrony_stack",
    "reduce_synchrony_stack",
    "stack_edges",
    "synchrony_landscape_similarity",
    "write_stack_checkpoint",
]
