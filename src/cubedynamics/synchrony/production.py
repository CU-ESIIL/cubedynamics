"""Bounded production primitives for local climate-tail synchrony.

The sparse pair table in this module is an in-memory relationship object.  It
exists so exact pair values can feed several independent reductions without
requiring a permanent dense center-by-focal stack.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Mapping, Sequence
import warnings

import numpy as np
import xarray as xr
from pyproj import CRS, Transformer
from scipy.spatial import cKDTree
from scipy.stats import rankdata
from shapely.geometry import box, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from ..config import TIME_DIM
from ..runtime import version_info
from .diagnostics import compare_panels
from .spatial import infer_spatial_dims
from .stacks import (
    _coordinate_values,
    _is_lat_lon,
    _materialize_pixel_time,
    _select_inputs,
)


PAIR_SCHEMA_VERSION = "3"
SIGNATURE_SCHEMA_VERSION = "2"
EARTH_RADIUS_KM = 6371.0088
_DIRECTION_LABELS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def expand_spatial_domain(
    output_geometry: BaseGeometry | Mapping[str, object] | Sequence[float],
    radius_km: float,
) -> BaseGeometry:
    """Return a WGS84 geometry buffered by a geodesically meaningful radius.

    The buffer is constructed in a local azimuthal-equidistant projection
    centered on the output geometry, then transformed back to EPSG:4326.
    """

    if radius_km <= 0:
        raise ValueError("radius_km must be positive")
    geometry = _coerce_geometry(output_geometry)
    if geometry.is_empty:
        raise ValueError("output_geometry must not be empty")
    centroid = geometry.centroid
    local = CRS.from_proj4(
        f"+proj=aeqd +lat_0={centroid.y:.12f} +lon_0={centroid.x:.12f} "
        "+datum=WGS84 +units=m +no_defs"
    )
    forward = Transformer.from_crs("EPSG:4326", local, always_xy=True).transform
    reverse = Transformer.from_crs(local, "EPSG:4326", always_xy=True).transform
    return transform(reverse, transform(forward, geometry).buffer(radius_km * 1000.0))


def spatial_output_mask(
    obj: xr.Dataset | xr.DataArray,
    output_geometry: BaseGeometry | Mapping[str, object] | Sequence[float],
) -> xr.DataArray:
    """Map an arbitrary WGS84 output geometry to spatial cell centers."""

    reference = obj if isinstance(obj, xr.DataArray) else next(iter(obj.data_vars.values()))
    y_dim, x_dim = infer_spatial_dims(reference)
    y = _coordinate_values(reference, y_dim)
    x = _coordinate_values(reference, x_dim)
    _is_lat_lon(reference, y_dim, x_dim, y, x)
    geometry = _coerce_geometry(output_geometry)
    try:
        from shapely import contains_xy, intersects_xy

        xx, yy = np.meshgrid(x, y)
        values = contains_xy(geometry, xx, yy) | intersects_xy(geometry.boundary, xx, yy)
    except ImportError:  # pragma: no cover - Shapely 2 is a project dependency
        from shapely.geometry import Point

        values = np.asarray(
            [[geometry.covers(Point(float(xv), float(yv))) for xv in x] for yv in y],
            dtype=bool,
        )
    return xr.DataArray(
        values,
        dims=(y_dim, x_dim),
        coords={y_dim: reference[y_dim], x_dim: reference[x_dim]},
        name="output_mask",
        attrs={
            "definition": "cell center is covered by requested WGS84 output geometry",
            "output_geometry_geojson": json.dumps(mapping(geometry), separators=(",", ":")),
        },
    )


def local_synchrony_pairs(
    obj: xr.Dataset | xr.DataArray,
    *,
    lower_var: str | None = None,
    upper_var: str | None = None,
    output_mask: xr.DataArray | np.ndarray | None = None,
    max_radius_km: float = 100.0,
    window_days: int = 90,
    window_end: object | None = None,
    min_t: int = 10,
    split_quantile: float = 0.5,
    time_dim: str = TIME_DIM,
    pair_batch_size: int = 16384,
) -> xr.Dataset:
    """Calculate unique local cold/warm/Delta pairs for a bounded cube.

    Only pairs within ``max_radius_km`` and incident to at least one requested
    output pixel are retained. Pair thresholds are precomputed only when every
    pixel has identical valid-time support; otherwise exact pairwise filtering
    and thresholds are used.
    """

    if max_radius_km <= 0:
        raise ValueError("max_radius_km must be positive")
    if window_days < 0:
        raise ValueError("window_days must be non-negative")
    if min_t < 2:
        raise ValueError("min_t must be at least 2")
    if not 0 < split_quantile <= 0.5:
        raise ValueError("split_quantile must be greater than 0 and no greater than 0.5")
    if pair_batch_size < 1:
        raise ValueError("pair_batch_size must be at least 1")

    started = time.perf_counter()
    lower, upper, lower_name, upper_name = _select_inputs(obj, lower_var, upper_var)
    if lower.dims != upper.dims:
        raise ValueError("Selected lower and upper variables must have matching dimensions")
    y_dim, x_dim = infer_spatial_dims(lower)
    if time_dim not in lower.dims:
        raise ValueError(f"Synchrony pairs require time dimension {time_dim!r}")
    end_value = lower[time_dim].values[-1] if window_end is None else np.datetime64(window_end)
    start_value = end_value - np.timedelta64(window_days, "D")
    lower_window = lower.sel({time_dim: slice(start_value, end_value)})
    upper_window = upper.sel({time_dim: slice(start_value, end_value)})
    lower_window, upper_window = xr.align(lower_window, upper_window, join="exact")
    if lower_window.sizes.get(time_dim, 0) < min_t:
        raise ValueError("Selected rolling window has fewer time labels than min_t")

    y_values = _coordinate_values(lower, y_dim)
    x_values = _coordinate_values(lower, x_dim)
    _is_lat_lon(lower, y_dim, x_dim, y_values, x_values)
    y_size, x_size = y_values.size, x_values.size
    mask = _normalize_output_mask(output_mask, lower, y_dim, x_dim)
    output_flat = mask.reshape(-1)
    if not np.any(output_flat):
        raise ValueError("output_mask selects no pixels")

    geometry_started = time.perf_counter()
    lat, lon = np.meshgrid(y_values, x_values, indexing="ij")
    xyz = _unit_sphere_xyz(lat.reshape(-1), lon.reshape(-1))
    chord = 2.0 * np.sin((max_radius_km / EARTH_RADIUS_KM) / 2.0)
    nonself = cKDTree(xyz).query_pairs(chord, output_type="ndarray")
    if nonself.size:
        nonself = nonself[
            output_flat[nonself[:, 0]] | output_flat[nonself[:, 1]]
        ]
    self_indices = np.flatnonzero(output_flat)
    self_pairs = np.column_stack((self_indices, self_indices))
    pairs = np.vstack((self_pairs, nonself)).astype(np.int64, copy=False)
    order = np.lexsort((pairs[:, 1], pairs[:, 0]))
    pairs = pairs[order]
    pair_left, pair_right = pairs[:, 0], pairs[:, 1]
    distance, bearing = _pair_geometry(pair_left, pair_right, lat.reshape(-1), lon.reshape(-1))
    bearing_radians = np.deg2rad(np.nan_to_num(bearing, nan=0.0))
    dx_km = distance * np.sin(bearing_radians)
    dy_km = distance * np.cos(bearing_radians)
    geometry_seconds = time.perf_counter() - geometry_started

    materialize_started = time.perf_counter()
    lower_values = _materialize_pixel_time(lower_window, time_dim, y_dim, x_dim)
    upper_values = _materialize_pixel_time(upper_window, time_dim, y_dim, x_dim)
    materialize_seconds = time.perf_counter() - materialize_started

    lower_thresholds, lower_states, lower_strategy = _precomputed_tail_state(
        lower_values, tail="lower", quantile=split_quantile
    )
    upper_thresholds, upper_states, upper_strategy = _precomputed_tail_state(
        upper_values, tail="upper", quantile=split_quantile
    )
    cold = np.full(pair_left.size, np.nan, dtype=np.float64)
    warm = np.full(pair_left.size, np.nan, dtype=np.float64)
    cold_count = np.zeros(pair_left.size, dtype=np.int16)
    warm_count = np.zeros(pair_left.size, dtype=np.int16)
    kernel_started = time.perf_counter()
    for start in range(0, pair_left.size, pair_batch_size):
        stop = min(start + pair_batch_size, pair_left.size)
        batch = slice(start, stop)
        cold_batch, cold_count_batch = _batched_one_tail_spearman(
            lower_values,
            pair_left[batch],
            pair_right[batch],
            tail="lower",
            quantile=split_quantile,
            min_t=min_t,
            thresholds=lower_thresholds,
            states=lower_states,
        )
        warm_batch, warm_count_batch = _batched_one_tail_spearman(
            upper_values,
            pair_left[batch],
            pair_right[batch],
            tail="upper",
            quantile=split_quantile,
            min_t=min_t,
            thresholds=upper_thresholds,
            states=upper_states,
        )
        cold[batch] = cold_batch
        warm[batch] = warm_batch
        cold_count[batch] = cold_count_batch
        warm_count[batch] = warm_count_batch
    kernel_seconds = time.perf_counter() - kernel_started

    left_y, left_x = np.divmod(pair_left, x_size)
    right_y, right_x = np.divmod(pair_right, x_size)
    direction = _direction_codes(bearing)
    result = xr.Dataset(
        {
            "cold_synchrony": ("pair", cold),
            "warm_synchrony": ("pair", warm),
            "delta_s": ("pair", cold - warm),
            "cold_joint_count": ("pair", cold_count),
            "warm_joint_count": ("pair", warm_count),
            "distance_km": ("pair", distance.astype(np.float32)),
            "bearing_degrees": ("pair", bearing.astype(np.float32)),
            "dx_km": ("pair", dx_km.astype(np.float32)),
            "dy_km": ("pair", dy_km.astype(np.float32)),
            "dx_index": ("pair", (right_x - left_x).astype(np.int32)),
            "dy_index": ("pair", (right_y - left_y).astype(np.int32)),
            "direction_code": ("pair", direction),
            "output_mask": ((y_dim, x_dim), mask),
        },
        coords={
            "pair": np.arange(pair_left.size, dtype=np.int64),
            y_dim: lower[y_dim],
            x_dim: lower[x_dim],
            "source_index": ("pair", pair_left),
            "target_index": ("pair", pair_right),
            "source_y_index": ("pair", left_y.astype(np.int32)),
            "source_x_index": ("pair", left_x.astype(np.int32)),
            "target_y_index": ("pair", right_y.astype(np.int32)),
            "target_x_index": ("pair", right_x.astype(np.int32)),
            "time_window_end": np.datetime64(end_value),
        },
    )
    for name in ("cold_synchrony", "warm_synchrony"):
        result[name].attrs.update({"units": "1", "valid_range": "-1 to 1"})
    result["delta_s"].attrs.update(
        {
            "units": "1",
            "definition": "pairwise cold_synchrony - warm_synchrony",
            "valid_range": "-2 to 2",
        }
    )
    result["distance_km"].attrs.update({"units": "km", "geometry": "great_circle"})
    result["bearing_degrees"].attrs.update(
        {"units": "degrees", "definition": "forward bearing from canonical source to target"}
    )
    result["dx_km"].attrs.update(
        {
            "units": "km",
            "definition": "signed eastward displacement from canonical source to target",
        }
    )
    result["dy_km"].attrs.update(
        {
            "units": "km",
            "definition": "signed northward displacement from canonical source to target",
        }
    )
    result["dx_index"].attrs["definition"] = "target x index minus source x index"
    result["dy_index"].attrs["definition"] = "target y index minus source y index"
    result["direction_code"].attrs.update(
        {"labels": ",".join(f"{i}:{name}" for i, name in enumerate(_DIRECTION_LABELS)), "undefined": -1}
    )
    source_attrs = dict(getattr(obj, "attrs", {}))
    runtime = version_info()
    fingerprint_payload = {
        "schema": PAIR_SCHEMA_VERSION,
        "source": source_attrs.get("source", "unknown"),
        "serving_revision": source_attrs.get("serving_revision", "unknown"),
        "variables": [lower_name, upper_name],
        "window_start": str(np.datetime64(start_value)),
        "window_end": str(np.datetime64(end_value)),
        "window_days": window_days,
        "min_t": min_t,
        "split_quantile": split_quantile,
        "max_radius_km": max_radius_km,
        "y_hash": sha256(y_values.tobytes()).hexdigest(),
        "x_hash": sha256(x_values.tobytes()).hexdigest(),
        "output_mask_hash": sha256(mask.tobytes()).hexdigest(),
    }
    fingerprint = sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result.attrs.update(
        {
            "analysis": "local_synchrony_pairs",
            "semantic_kind": "relationship",
            "semantic_category": "sparse_local_relationships",
            "pair_schema_version": PAIR_SCHEMA_VERSION,
            "analysis_fingerprint": f"sha256:{fingerprint}",
            "source": source_attrs.get("source", "unknown"),
            "source_provider": source_attrs.get("source_provider", "unknown"),
            "serving_revision": source_attrs.get("serving_revision", "unknown"),
            "cubedynamics_version": runtime.version,
            "cubedynamics_git_sha": runtime.git_sha or "unavailable",
            "lower_variable": lower_name,
            "upper_variable": upper_name,
            "window_days": int(window_days),
            "window_start": str(np.datetime64(start_value)),
            "window_end": str(np.datetime64(end_value)),
            "min_time_points_per_tail": int(min_t),
            "split_quantile": float(split_quantile),
            "split_definition": (
                "per-series pair-valid quantiles; cold joint <= thresholds; "
                "warm joint > thresholds"
            ),
            "max_radius_km": float(max_radius_km),
            "observation_radius_km": float(max_radius_km),
            "observation_radius_definition": (
                "maximum pair distance observed around each focal pixel; not an inferred "
                "synchrony scale"
            ),
            "pair_symmetry": "canonical undirected pair calculated once within bounded input",
            "unique_pair_count": int(pair_left.size),
            "nonself_pair_count": int(np.count_nonzero(pair_left != pair_right)),
            "output_pixel_count": int(np.count_nonzero(mask)),
            "computation_pixel_count": int(mask.size),
            "cold_threshold_strategy": lower_strategy,
            "warm_threshold_strategy": upper_strategy,
            "spearman_kernel": "batched exact average-rank Pearson on pairwise joint-tail values",
            "pair_batch_size": int(pair_batch_size),
            "geometry_seconds": float(geometry_seconds),
            "input_materialization_seconds": float(materialize_seconds),
            "pair_kernel_seconds": float(kernel_seconds),
            "total_seconds": float(time.perf_counter() - started),
            "pairs_per_kernel_second": float(pair_left.size / kernel_seconds) if kernel_seconds else np.nan,
            "computation_domain_bounds": json.dumps(
                [float(x_values.min()), float(y_values.min()), float(x_values.max()), float(y_values.max())]
            ),
            "output_domain_bounds": json.dumps(_mask_bounds(mask, y_values, x_values)),
        }
    )
    return result


def synchrony_signature(
    pairs: xr.Dataset,
    *,
    radii_km: Sequence[float] = (25.0, 50.0, 75.0, 100.0),
    include_directional: bool = True,
) -> xr.Dataset:
    """Baseline-compress sparse pairs across exact nested observation radii."""

    _validate_pairs(pairs)
    radii = np.asarray(tuple(float(value) for value in radii_km), dtype=float)
    if radii.ndim != 1 or radii.size == 0 or np.any(radii <= 0) or np.any(np.diff(radii) <= 0):
        raise ValueError("radii_km must be positive and strictly increasing")
    maximum = float(pairs.attrs["max_radius_km"])
    if radii[-1] > maximum + 1e-9:
        raise ValueError("radii_km cannot exceed the pair table's max_radius_km")
    y_dim, x_dim = pairs["output_mask"].dims
    y_size, x_size = pairs.sizes[y_dim], pairs.sizes[x_dim]
    mask = np.asarray(pairs.output_mask.values, dtype=bool).reshape(-1)
    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    nonself = source != target
    source_selected = mask[source]
    target_selected = mask[target] & nonself
    contribution_node = np.concatenate((source[source_selected], target[target_selected]))
    contribution_pair = np.concatenate((np.flatnonzero(source_selected), np.flatnonzero(target_selected)))
    contribution_reverse = np.concatenate(
        (np.zeros(np.count_nonzero(source_selected), dtype=bool), np.ones(np.count_nonzero(target_selected), dtype=bool))
    )
    order = np.argsort(contribution_node, kind="stable")
    contribution_node = contribution_node[order]
    contribution_pair = contribution_pair[order]
    contribution_reverse = contribution_reverse[order]
    unique_nodes, starts, counts = np.unique(contribution_node, return_index=True, return_counts=True)
    lookup = {int(node): (int(start), int(count)) for node, start, count in zip(unique_nodes, starts, counts)}

    shape = (radii.size, y_size * x_size)
    floats = {
        name: np.full(shape, np.nan, dtype=np.float64)
        for name in (
            "cold_median", "warm_median", "delta_median", "delta_iqr", "delta_mad",
            "neighborhood_coverage", "delta_directional_range",
            "delta_directional_eta_squared",
        )
    }
    integers = {
        name: np.zeros(shape, dtype=np.int32)
        for name in ("valid_pair_count", "cold_valid_pair_count", "warm_valid_pair_count", "expected_pair_count")
    }
    direction_codes = {
        name: np.full(shape, -1, dtype=np.int8)
        for name in ("delta_strongest_direction_code", "delta_weakest_direction_code")
    }
    pair_distance = np.asarray(pairs.distance_km.values, dtype=float)
    pair_bearing = np.asarray(pairs.bearing_degrees.values, dtype=float)
    metric_values = {
        name: np.asarray(pairs[name].values, dtype=float)
        for name in ("cold_synchrony", "warm_synchrony", "delta_s")
    }
    started = time.perf_counter()
    for node in np.flatnonzero(mask):
        start, count = lookup[int(node)]
        selected_pairs = contribution_pair[start : start + count]
        reverse = contribution_reverse[start : start + count]
        distance = pair_distance[selected_pairs]
        bearing = pair_bearing[selected_pairs].copy()
        bearing[reverse & np.isfinite(bearing)] = (bearing[reverse & np.isfinite(bearing)] + 180.0) % 360.0
        cold = metric_values["cold_synchrony"][selected_pairs]
        warm = metric_values["warm_synchrony"][selected_pairs]
        delta = metric_values["delta_s"][selected_pairs]
        for radius_index, radius in enumerate(radii):
            within = distance <= radius + 1e-7
            expected = int(np.count_nonzero(within))
            integers["expected_pair_count"][radius_index, node] = expected
            cold_valid = within & np.isfinite(cold)
            warm_valid = within & np.isfinite(warm)
            delta_valid = within & np.isfinite(delta)
            integers["cold_valid_pair_count"][radius_index, node] = int(np.count_nonzero(cold_valid))
            integers["warm_valid_pair_count"][radius_index, node] = int(np.count_nonzero(warm_valid))
            valid_count = int(np.count_nonzero(delta_valid))
            integers["valid_pair_count"][radius_index, node] = valid_count
            floats["neighborhood_coverage"][radius_index, node] = valid_count / expected if expected else np.nan
            if np.any(cold_valid):
                floats["cold_median"][radius_index, node] = np.median(cold[cold_valid])
            if np.any(warm_valid):
                floats["warm_median"][radius_index, node] = np.median(warm[warm_valid])
            if np.any(delta_valid):
                observed = delta[delta_valid]
                q25, q50, q75 = np.quantile(observed, (0.25, 0.5, 0.75))
                floats["delta_median"][radius_index, node] = q50
                floats["delta_iqr"][radius_index, node] = q75 - q25
                floats["delta_mad"][radius_index, node] = np.median(np.abs(observed - q50))
            if include_directional:
                directional = delta_valid & np.isfinite(bearing)
                if np.any(directional):
                    codes = _direction_codes(bearing[directional])
                    values = delta[directional]
                    means = np.full(8, np.nan, dtype=float)
                    for code in range(8):
                        if np.any(codes == code):
                            means[code] = np.mean(values[codes == code])
                    finite = np.isfinite(means)
                    if np.any(finite):
                        floats["delta_directional_range"][radius_index, node] = np.nanmax(means) - np.nanmin(means)
                        direction_codes["delta_strongest_direction_code"][radius_index, node] = int(np.nanargmax(means))
                        direction_codes["delta_weakest_direction_code"][radius_index, node] = int(np.nanargmin(means))
                    floats["delta_directional_eta_squared"][radius_index, node] = _eta_squared(values, codes)

    dims = ("time_window_end", "radius_km", y_dim, x_dim)
    coords = {
        "time_window_end": [np.datetime64(pairs.time_window_end.values)],
        "radius_km": radii,
        y_dim: pairs[y_dim],
        x_dim: pairs[x_dim],
    }
    data_vars: dict[str, tuple[tuple[str, ...], np.ndarray]] = {}
    for name, values in {**floats, **integers, **direction_codes}.items():
        reshaped = values.reshape((1, radii.size, y_size, x_size))
        data_vars[name] = (dims, reshaped)
    result = xr.Dataset(data_vars, coords=coords)
    result["output_mask"] = pairs.output_mask
    result["delta_median_increment"] = result.delta_median.diff("radius_km", label="upper").reindex(radius_km=radii)
    result["delta_iqr_increment"] = result.delta_iqr.diff("radius_km", label="upper").reindex(radius_km=radii)
    for name in (
        "cold_median", "warm_median", "delta_median", "delta_iqr", "delta_mad",
        "delta_directional_range",
    ):
        result[name].attrs["units"] = "1"
    result["delta_median"].attrs["definition"] = "median of pairwise (cold_synchrony - warm_synchrony)"
    result["delta_iqr"].attrs["definition"] = "q75-q25 of pairwise (cold_synchrony - warm_synchrony)"
    result["delta_mad"].attrs["definition"] = (
        "median absolute deviation of pairwise (cold_synchrony - warm_synchrony)"
    )
    result["neighborhood_coverage"].attrs.update({"units": "1", "valid_range": "0 to 1", "definition": "valid_pair_count / expected_pair_count"})
    result["delta_directional_eta_squared"].attrs.update({"units": "1", "status": "diagnostic", "definition": "between-sector Delta variance / total Delta variance"})
    for name in ("delta_strongest_direction_code", "delta_weakest_direction_code"):
        result[name].attrs.update({"labels": ",".join(f"{i}:{label}" for i, label in enumerate(_DIRECTION_LABELS)), "undefined": -1, "status": "diagnostic"})
    fingerprint_payload = {
        "schema": SIGNATURE_SCHEMA_VERSION,
        "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
        "radii_km": radii.tolist(),
        "quantile_method": "exact_numpy_nanquantile",
        "directional": bool(include_directional),
    }
    fingerprint = sha256(json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result.attrs.update(dict(pairs.attrs))
    result.attrs.update(
        {
            "analysis": "synchrony_signature",
            "semantic_kind": "summary",
            "semantic_category": "spatial_synchrony_signature",
            "signature_schema_version": SIGNATURE_SCHEMA_VERSION,
            "analysis_fingerprint": f"sha256:{fingerprint}",
            "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
            "radii_km": ",".join(str(value) for value in radii),
            "scientific_role": "baseline compression of the full local S_p(dx,dy) surface",
            "radius_support": "nested cumulative great-circle distance used as a baseline",
            "observation_radius_km": maximum,
            "observation_radius_definition": (
                "maximum observed support; not an inferred characteristic synchrony scale"
            ),
            "quantile_method": "exact numpy quantile over retained bounded pair values",
            "delta_reduction": "median/IQR/MAD of pairwise cold_synchrony - warm_synchrony",
            "output_domain_policy": "only output_mask focal pixels; computation domain includes halo",
            "directional_status": "diagnostic" if include_directional else "not requested",
            "multimodality_status": "not computed in production signature",
            "signature_reduction_seconds": float(time.perf_counter() - started),
        }
    )
    return result


def landscape_change_signature(
    pairs: xr.Dataset,
    *,
    metric: str = "delta_s",
    deadband: float = 0.02,
    near_tie_epsilon: float = 0.005,
    min_overlap: int = 25,
) -> xr.Dataset:
    """Compare adjacent center landscapes from a bounded sparse pair table.

    The returned orientation dimension retains east-west and north-south
    comparisons. No scalar composite is constructed.
    """

    _validate_pairs(pairs)
    if metric not in {"cold_synchrony", "warm_synchrony", "delta_s"}:
        raise ValueError("metric must be cold_synchrony, warm_synchrony, or delta_s")
    y_dim, x_dim = pairs.output_mask.dims
    y_size, x_size = pairs.sizes[y_dim], pairs.sizes[x_dim]
    mask = np.asarray(pairs.output_mask.values, dtype=bool).reshape(-1)
    source = np.asarray(pairs.source_index.values, dtype=int)
    target = np.asarray(pairs.target_index.values, dtype=int)
    values = np.asarray(pairs[metric].values, dtype=float)
    landscapes: dict[int, dict[int, float]] = {int(node): {} for node in np.flatnonzero(mask)}
    for left, right, value in zip(source, target, values):
        if mask[left]:
            landscapes[int(left)][int(right)] = float(value)
        if right != left and mask[right]:
            landscapes[int(right)][int(left)] = float(value)
    names = ("normalized_rmse", "spearman", "sign_disagreement", "gradient_vector_rmse", "pooled_robust_range")
    arrays = {name: np.full((2, y_size, x_size), np.nan, dtype=np.float32) for name in names}
    overlap = np.zeros((2, y_size, x_size), dtype=np.int32)
    offsets = ((0, 1), (1, 0))
    for orientation, (dy, dx) in enumerate(offsets):
        for node in np.flatnonzero(mask):
            yi, xi = divmod(int(node), x_size)
            other_y, other_x = yi + dy, xi + dx
            if other_y >= y_size or other_x >= x_size:
                continue
            other = other_y * x_size + other_x
            if not mask[other]:
                continue
            left_map, right_map = landscapes[int(node)], landscapes[int(other)]
            shared = sorted(set(left_map).intersection(right_map))
            if len(shared) < min_overlap:
                continue
            left_panel = np.full((y_size, x_size), np.nan, dtype=float)
            right_panel = np.full_like(left_panel, np.nan)
            flat_left = left_panel.reshape(-1)
            flat_right = right_panel.reshape(-1)
            flat_left[shared] = [left_map[index] for index in shared]
            flat_right[shared] = [right_map[index] for index in shared]
            record = compare_panels(left_panel, right_panel, deadband=deadband, near_tie_epsilon=near_tie_epsilon)
            overlap[orientation, yi, xi] = int(record["shared_valid_count"])
            for name in names:
                arrays[name][orientation, yi, xi] = record[name]
    result = xr.Dataset(
        {**{name: (("orientation", y_dim, x_dim), array) for name, array in arrays.items()}, "shared_valid_count": (("orientation", y_dim, x_dim), overlap)},
        coords={"orientation": ["east_west", "north_south"], y_dim: pairs[y_dim], x_dim: pairs[x_dim], "time_window_end": np.datetime64(pairs.time_window_end.values)},
    )
    for name in names:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result[f"mean_{name}"] = result[name].mean("orientation", skipna=True)
    fingerprint_payload = {
        "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
        "metric": metric,
        "deadband": float(deadband),
        "near_tie_epsilon": float(near_tie_epsilon),
        "minimum_overlap": int(min_overlap),
    }
    fingerprint = sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result.attrs.update(dict(pairs.attrs))
    result.attrs.update(
        {
            "analysis": "landscape_change_signature",
            "semantic_kind": "summary",
            "analysis_fingerprint": f"sha256:{fingerprint}",
            "source_metric": metric,
            "source_pair_fingerprint": pairs.attrs["analysis_fingerprint"],
            "panel_change_axes": "normalized_rmse,spearman,sign_disagreement,gradient_vector_rmse",
            "pair_synchrony_distinction": "compares center landscapes; not pair S(i,j) and not stack heterogeneity",
            "deadband": float(deadband),
            "near_tie_epsilon": float(near_tie_epsilon),
            "minimum_overlap": int(min_overlap),
        }
    )
    return result


def tiled_landscape_change_signature(
    obj: xr.Dataset | xr.DataArray,
    *,
    output_mask: xr.DataArray | np.ndarray,
    lower_var: str | None = None,
    upper_var: str | None = None,
    max_radius_km: float = 100.0,
    tile_shape: tuple[int, int] = (32, 32),
    window_days: int = 90,
    window_end: object | None = None,
    min_t: int = 10,
    split_quantile: float = 0.5,
    time_dim: str = TIME_DIM,
    pair_batch_size: int = 16384,
    metric: str = "delta_s",
    deadband: float = 0.02,
    near_tie_epsilon: float = 0.005,
    min_overlap: int = 25,
    checkpoint_dir: str | Path | None = None,
) -> xr.Dataset:
    """Compute restartable neighboring-landscape diagnostics with tile halos.

    One extra output-center row and column are included while each tile is
    evaluated so east-west and north-south comparisons anchored at tile seams
    have both landscapes available. The returned diagnostics remain separate
    from the focal stack signature.
    """

    if max_radius_km <= 0:
        raise ValueError("max_radius_km must be positive")
    if len(tile_shape) != 2 or tile_shape[0] < 1 or tile_shape[1] < 1:
        raise ValueError("tile_shape must contain two positive integers")
    lower, _, lower_name, upper_name = _select_inputs(obj, lower_var, upper_var)
    y_dim, x_dim = infer_spatial_dims(lower)
    y_values = _coordinate_values(lower, y_dim)
    x_values = _coordinate_values(lower, x_dim)
    _is_lat_lon(lower, y_dim, x_dim, y_values, x_values)
    mask = _normalize_output_mask(output_mask, lower, y_dim, x_dim)
    checkpoint_root = Path(checkpoint_dir) if checkpoint_dir is not None else None
    runtime = version_info()
    source_attrs = dict(getattr(obj, "attrs", {}))
    common = {
        "source": source_attrs.get("source", "unknown"),
        "serving_revision": source_attrs.get("serving_revision", "unknown"),
        "lower_variable": lower_name,
        "upper_variable": upper_name,
        "coordinate_hashes": {
            "time": sha256(np.asarray(lower[time_dim].values).tobytes()).hexdigest(),
            "y": sha256(y_values.tobytes()).hexdigest(),
            "x": sha256(x_values.tobytes()).hexdigest(),
        },
        "max_radius_km": float(max_radius_km),
        "window_days": int(window_days),
        "window_end": None if window_end is None else str(np.datetime64(window_end)),
        "min_t": int(min_t),
        "split_quantile": float(split_quantile),
        "metric": metric,
        "deadband": float(deadband),
        "near_tie_epsilon": float(near_tie_epsilon),
        "min_overlap": int(min_overlap),
        "cubedynamics_git_sha": runtime.git_sha or "unavailable",
    }
    y_step_km = float(np.max(np.abs(np.diff(y_values)))) * 111.2 if y_values.size > 1 else 0.0
    x_step_km = (
        float(np.max(np.abs(np.diff(x_values))))
        * 111.2
        * float(np.cos(np.deg2rad(np.min(np.abs(y_values)))))
        if x_values.size > 1
        else 0.0
    )
    gradient_guard_km = 1.5 * max(y_step_km, x_step_km)
    pieces: list[xr.Dataset] = []
    computed_tiles = 0
    resumed_tiles = 0
    pair_calculation_count = 0
    pair_kernel_seconds = 0.0
    for y_start in range(0, y_values.size, int(tile_shape[0])):
        y_stop = min(y_start + int(tile_shape[0]), y_values.size)
        for x_start in range(0, x_values.size, int(tile_shape[1])):
            x_stop = min(x_start + int(tile_shape[1]), x_values.size)
            anchor_values = mask[y_start:y_stop, x_start:x_stop]
            if not np.any(anchor_values):
                continue
            center_mask = np.zeros_like(mask)
            center_mask[y_start:y_stop, x_start:x_stop] = anchor_values
            if y_stop < y_values.size:
                center_mask[y_stop, x_start:x_stop] |= mask[y_stop, x_start:x_stop]
            if x_stop < x_values.size:
                center_mask[y_start:y_stop, x_stop] |= mask[y_start:y_stop, x_stop]
            yi, xi = np.nonzero(center_mask)
            center_bounds = (
                float(x_values[xi].min()),
                float(y_values[yi].min()),
                float(x_values[xi].max()),
                float(y_values[yi].max()),
            )
            # The extra cell-width guard keeps finite relationship values away
            # from the local array edge, so np.gradient has the same NaN
            # neighborhood as an untiled full-domain panel.
            halo_bounds = expand_spatial_domain(
                center_bounds, max_radius_km + gradient_guard_km
            ).bounds
            halo_y = np.flatnonzero((y_values >= halo_bounds[1]) & (y_values <= halo_bounds[3]))
            halo_x = np.flatnonzero((x_values >= halo_bounds[0]) & (x_values <= halo_bounds[2]))
            y_slice = slice(int(halo_y.min()), int(halo_y.max()) + 1)
            x_slice = slice(int(halo_x.min()), int(halo_x.max()) + 1)
            payload = {
                **common,
                "tile": [y_start, y_stop, x_start, x_stop],
                "center_mask_hash": sha256(center_mask[y_slice, x_slice].tobytes()).hexdigest(),
                "halo_index_bounds": [y_slice.start, y_slice.stop, x_slice.start, x_slice.stop],
            }
            compatibility = "sha256:" + sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            checkpoint = (
                checkpoint_root / f"landscape_y{y_start:05d}-{y_stop:05d}_x{x_start:05d}-{x_stop:05d}.nc"
                if checkpoint_root is not None
                else None
            )
            manifest_path = checkpoint.with_suffix(".json") if checkpoint is not None else None
            if checkpoint is not None and checkpoint.exists() and manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("checkpoint_compatibility_fingerprint") != compatibility:
                    raise ValueError("Landscape checkpoint compatibility fingerprint mismatch")
                with xr.open_dataset(checkpoint) as saved:
                    change = saved.load()
                resumed_tiles += 1
            else:
                subset = obj.isel({y_dim: y_slice, x_dim: x_slice})
                subset_mask = xr.DataArray(
                    center_mask[y_slice, x_slice],
                    dims=(y_dim, x_dim),
                    coords={y_dim: subset[y_dim], x_dim: subset[x_dim]},
                )
                pairs = local_synchrony_pairs(
                    subset,
                    lower_var=lower_var,
                    upper_var=upper_var,
                    output_mask=subset_mask,
                    max_radius_km=max_radius_km,
                    window_days=window_days,
                    window_end=window_end,
                    min_t=min_t,
                    split_quantile=split_quantile,
                    time_dim=time_dim,
                    pair_batch_size=pair_batch_size,
                )
                change = landscape_change_signature(
                    pairs,
                    metric=metric,
                    deadband=deadband,
                    near_tie_epsilon=near_tie_epsilon,
                    min_overlap=min_overlap,
                )
                change.attrs["checkpoint_compatibility_fingerprint"] = compatibility
                if checkpoint is not None:
                    checkpoint.parent.mkdir(parents=True, exist_ok=True)
                    temporary = checkpoint.with_suffix(".partial.nc")
                    change.to_netcdf(temporary)
                    temporary.replace(checkpoint)
                    temporary_manifest = manifest_path.with_suffix(".partial.json")
                    temporary_manifest.write_text(
                        json.dumps(
                            {
                                "status": "complete",
                                "checkpoint_compatibility_fingerprint": compatibility,
                                "analysis_fingerprint": change.attrs["analysis_fingerprint"],
                            },
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    temporary_manifest.replace(manifest_path)
                computed_tiles += 1
            pair_calculation_count += int(change.attrs.get("unique_pair_count", 0))
            pair_kernel_seconds += float(change.attrs.get("pair_kernel_seconds", 0.0))
            output_y = lower[y_dim].isel({y_dim: slice(y_start, y_stop)})
            output_x = lower[x_dim].isel({x_dim: slice(x_start, x_stop)})
            pieces.append(change.reindex({y_dim: output_y, x_dim: output_x}))
    combined = xr.combine_by_coords(pieces, combine_attrs="override")
    combined = combined.reindex({y_dim: lower[y_dim], x_dim: lower[x_dim]})
    combined["output_mask"] = xr.DataArray(
        mask, dims=(y_dim, x_dim), coords={y_dim: lower[y_dim], x_dim: lower[x_dim]}
    )
    combined.attrs.update(
        {
            "analysis": "landscape_change_signature",
            "execution": "restartable output tiling with full-radius halos and seam neighbors",
            "tile_shape": f"{int(tile_shape[0])},{int(tile_shape[1])}",
            "tile_count": int(len(pieces)),
            "computed_tile_count": int(computed_tiles),
            "resumed_tile_count": int(resumed_tiles),
            "pair_calculation_count_with_tile_recompute": int(pair_calculation_count),
            "pair_kernel_seconds_sum": float(pair_kernel_seconds),
            "cubedynamics_version": runtime.version,
            "cubedynamics_git_sha": runtime.git_sha or "unavailable",
        }
    )
    return combined


def tiled_synchrony_signature(
    obj: xr.Dataset | xr.DataArray,
    *,
    output_mask: xr.DataArray | np.ndarray,
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
    include_directional: bool = True,
    checkpoint_dir: str | Path | None = None,
) -> xr.Dataset:
    """Compute a signature in restartable output tiles with complete halos.

    Each tile is a disjoint set of focal/output pixels. Its computation subset
    is expanded by the largest requested radius, so a focal pixel receives the
    same neighborhood at a tile seam as it does in an untiled calculation.
    Pairs that serve focal pixels in two different tiles can be recalculated;
    this bounded-memory tradeoff avoids a permanent statewide pair store.
    """

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
    if not np.any(mask):
        raise ValueError("output_mask selects no pixels")

    checkpoint_root = Path(checkpoint_dir) if checkpoint_dir is not None else None
    pieces: list[xr.Dataset] = []
    computed_tiles = 0
    resumed_tiles = 0
    pair_calculation_count = 0
    nonself_pair_calculation_count = 0
    pair_kernel_seconds = 0.0
    pair_geometry_seconds = 0.0
    input_materialization_seconds = 0.0
    signature_reduction_seconds = 0.0
    source_attrs = dict(getattr(obj, "attrs", {}))
    runtime = version_info()
    time_values = np.asarray(lower[time_dim].values)
    common_fingerprint = {
        "source": source_attrs.get("source", "unknown"),
        "source_provider": source_attrs.get("source_provider", "unknown"),
        "serving_revision": source_attrs.get("serving_revision", "unknown"),
        "lower_variable": lower_name,
        "upper_variable": upper_name,
        "coordinate_hashes": {
            "time": sha256(time_values.tobytes()).hexdigest(),
            "y": sha256(y_values.tobytes()).hexdigest(),
            "x": sha256(x_values.tobytes()).hexdigest(),
        },
        "radii_km": radii.tolist(),
        "window_days": int(window_days),
        "window_end": None if window_end is None else str(np.datetime64(window_end)),
        "min_t": int(min_t),
        "split_quantile": float(split_quantile),
        "include_directional": bool(include_directional),
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
            halo_bounds = expand_spatial_domain(output_bounds, float(radii[-1])).bounds
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
            tile_payload = {
                **common_fingerprint,
                "tile": [y_start, y_stop, x_start, x_stop],
                "tile_output_mask_hash": sha256(tile_values.tobytes()).hexdigest(),
                "halo_index_bounds": [y_slice.start, y_slice.stop, x_slice.start, x_slice.stop],
            }
            compatibility = "sha256:" + sha256(
                json.dumps(tile_payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            checkpoint = (
                checkpoint_root / f"signature_y{y_start:05d}-{y_stop:05d}_x{x_start:05d}-{x_stop:05d}.nc"
                if checkpoint_root is not None
                else None
            )
            if checkpoint is not None and checkpoint.exists() and checkpoint.with_suffix(".json").exists():
                signature = load_signature_checkpoint(
                    checkpoint,
                    expected_compatibility_fingerprint=compatibility,
                )
                resumed_tiles += 1
            else:
                pairs = local_synchrony_pairs(
                    subset,
                    lower_var=lower_var,
                    upper_var=upper_var,
                    output_mask=subset_mask,
                    max_radius_km=float(radii[-1]),
                    window_days=window_days,
                    window_end=window_end,
                    min_t=min_t,
                    split_quantile=split_quantile,
                    time_dim=time_dim,
                    pair_batch_size=pair_batch_size,
                )
                signature = synchrony_signature(
                    pairs,
                    radii_km=radii,
                    include_directional=include_directional,
                )
                signature.attrs["checkpoint_compatibility_fingerprint"] = compatibility
                signature.attrs.update(
                    {
                        "tile_index_bounds": json.dumps([y_start, y_stop, x_start, x_stop]),
                        "halo_index_bounds": json.dumps(
                            [y_slice.start, y_slice.stop, x_slice.start, x_slice.stop]
                        ),
                        "output_tile_shape": f"{y_stop - y_start},{x_stop - x_start}",
                        "computation_tile_shape": (
                            f"{y_slice.stop - y_slice.start},{x_slice.stop - x_slice.start}"
                        ),
                        "maximum_halo_radius_km": float(radii[-1]),
                    }
                )
                if checkpoint is not None:
                    write_signature_checkpoint(signature, checkpoint)
                computed_tiles += 1
            pair_calculation_count += int(signature.attrs.get("unique_pair_count", 0))
            nonself_pair_calculation_count += int(signature.attrs.get("nonself_pair_count", 0))
            pair_kernel_seconds += float(signature.attrs.get("pair_kernel_seconds", 0.0))
            pair_geometry_seconds += float(signature.attrs.get("geometry_seconds", 0.0))
            input_materialization_seconds += float(
                signature.attrs.get("input_materialization_seconds", 0.0)
            )
            signature_reduction_seconds += float(
                signature.attrs.get("signature_reduction_seconds", 0.0)
            )
            output_y = lower[y_dim].isel({y_dim: slice(y_start, y_stop)})
            output_x = lower[x_dim].isel({x_dim: slice(x_start, x_stop)})
            pieces.append(signature.reindex({y_dim: output_y, x_dim: output_x}))

    combined = xr.combine_by_coords(pieces, combine_attrs="override")
    combined = combined.reindex({y_dim: lower[y_dim], x_dim: lower[x_dim]})
    combined["output_mask"] = xr.DataArray(
        mask,
        dims=(y_dim, x_dim),
        coords={y_dim: lower[y_dim], x_dim: lower[x_dim]},
    )
    combined.attrs.update(
        {
            "analysis": "synchrony_signature",
            "execution": "restartable output tiling with full-radius coordinate halos",
            "tile_shape": f"{int(tile_shape[0])},{int(tile_shape[1])}",
            "tile_count": int(len(pieces)),
            "computed_tile_count": int(computed_tiles),
            "resumed_tile_count": int(resumed_tiles),
            "pair_calculation_count_with_tile_recompute": int(pair_calculation_count),
            "nonself_pair_calculation_count_with_tile_recompute": int(
                nonself_pair_calculation_count
            ),
            "pair_kernel_seconds_sum": float(pair_kernel_seconds),
            "pair_geometry_seconds_sum": float(pair_geometry_seconds),
            "input_materialization_seconds_sum": float(input_materialization_seconds),
            "signature_reduction_seconds_sum": float(signature_reduction_seconds),
            "cross_tile_pair_policy": "endpoint_tile_recompute; no permanent pair store",
            "quantile_method": "exact within each complete focal neighborhood",
            "input_domain_bounds": json.dumps(
                [float(x_values.min()), float(y_values.min()), float(x_values.max()), float(y_values.max())]
            ),
            "output_domain_bounds": json.dumps(_mask_bounds(mask, y_values, x_values)),
            "cubedynamics_version": runtime.version,
            "cubedynamics_git_sha": runtime.git_sha or "unavailable",
        }
    )
    return combined


def write_signature_checkpoint(signature: xr.Dataset, path: str | Path) -> Path:
    """Atomically write one complete fingerprint-bound signature tile."""

    if signature.attrs.get("analysis") != "synchrony_signature":
        raise TypeError("Expected a synchrony_signature Dataset")
    target = Path(path)
    if target.suffix != ".nc":
        raise ValueError("Signature checkpoints currently require a .nc path")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".partial.nc")
    signature.to_netcdf(temporary)
    temporary.replace(target)
    manifest = {
        "status": "complete",
        "path": target.name,
        "analysis_fingerprint": signature.attrs["analysis_fingerprint"],
        "source_pair_fingerprint": signature.attrs["source_pair_fingerprint"],
        "schema_version": signature.attrs["signature_schema_version"],
        "checkpoint_compatibility_fingerprint": signature.attrs.get(
            "checkpoint_compatibility_fingerprint"
        ),
        "provenance": {
            key: signature.attrs.get(key)
            for key in (
                "cubedynamics_version",
                "cubedynamics_git_sha",
                "source",
                "source_provider",
                "serving_revision",
                "lower_variable",
                "upper_variable",
                "window_start",
                "window_end",
                "window_days",
                "split_quantile",
                "min_time_points_per_tail",
                "radii_km",
                "tile_index_bounds",
                "halo_index_bounds",
                "output_tile_shape",
                "computation_tile_shape",
                "maximum_halo_radius_km",
                "quantile_method",
                "spearman_kernel",
            )
        },
        "sizes": dict(signature.sizes),
    }
    temporary_manifest = target.with_suffix(".partial.json")
    temporary_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_manifest.replace(target.with_suffix(".json"))
    return target


def load_signature_checkpoint(
    path: str | Path,
    *,
    expected_fingerprint: str | None = None,
    expected_compatibility_fingerprint: str | None = None,
) -> xr.Dataset:
    """Load a complete signature checkpoint after exact fingerprint validation."""

    target = Path(path)
    manifest_path = target.with_suffix(".json")
    if not target.exists() or not manifest_path.exists():
        raise FileNotFoundError("Checkpoint data and manifest must both exist")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise ValueError("Checkpoint manifest is not complete")
    if expected_fingerprint is None and expected_compatibility_fingerprint is None:
        raise ValueError("An expected analysis or compatibility fingerprint is required")
    if expected_fingerprint is not None and manifest.get("analysis_fingerprint") != expected_fingerprint:
        raise ValueError("Checkpoint fingerprint mismatch")
    if (
        expected_compatibility_fingerprint is not None
        and manifest.get("checkpoint_compatibility_fingerprint")
        != expected_compatibility_fingerprint
    ):
        raise ValueError("Checkpoint compatibility fingerprint mismatch")
    result = xr.open_dataset(target).load()
    if (
        expected_fingerprint is not None
        and result.attrs.get("analysis_fingerprint") != expected_fingerprint
    ):
        raise ValueError("Checkpoint dataset fingerprint does not match manifest")
    if (
        expected_compatibility_fingerprint is not None
        and result.attrs.get("checkpoint_compatibility_fingerprint")
        != expected_compatibility_fingerprint
    ):
        raise ValueError("Checkpoint dataset compatibility does not match manifest")
    return result


def _coerce_geometry(value: BaseGeometry | Mapping[str, object] | Sequence[float]) -> BaseGeometry:
    if isinstance(value, BaseGeometry):
        return value
    if isinstance(value, Mapping):
        if value.get("type") == "Feature":
            return shape(value["geometry"])
        return shape(value)
    values = tuple(float(item) for item in value)
    if len(values) != 4:
        raise ValueError("Bounding boxes must be (min_lon, min_lat, max_lon, max_lat)")
    return box(*values)


def _normalize_output_mask(
    value: xr.DataArray | np.ndarray | None,
    reference: xr.DataArray,
    y_dim: str,
    x_dim: str,
) -> np.ndarray:
    if value is None:
        return np.ones((reference.sizes[y_dim], reference.sizes[x_dim]), dtype=bool)
    if isinstance(value, xr.DataArray):
        if set(value.dims) != {y_dim, x_dim}:
            raise ValueError("output_mask must use the cube's two spatial dimensions")
        aligned, _ = xr.align(value.transpose(y_dim, x_dim), reference.isel({dim: 0 for dim in reference.dims if dim not in (y_dim, x_dim)}), join="exact")
        array = np.asarray(aligned.values, dtype=bool)
    else:
        array = np.asarray(value, dtype=bool)
    expected = (reference.sizes[y_dim], reference.sizes[x_dim])
    if array.shape != expected:
        raise ValueError(f"output_mask shape {array.shape!r} does not match {expected!r}")
    return array


def _unit_sphere_xyz(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat = np.deg2rad(latitude)
    lon = np.deg2rad(longitude)
    cos_lat = np.cos(lat)
    return np.column_stack((cos_lat * np.cos(lon), cos_lat * np.sin(lon), np.sin(lat)))


def _pair_geometry(
    left: np.ndarray,
    right: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    lat1 = np.deg2rad(latitude[left])
    lat2 = np.deg2rad(latitude[right])
    dlat = lat2 - lat1
    dlon = np.deg2rad(longitude[right] - longitude[left])
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    distance = EARTH_RADIUS_KM * 2 * np.arctan2(np.sqrt(a), np.sqrt(np.maximum(0, 1 - a)))
    bearing = np.rad2deg(
        np.arctan2(
            np.sin(dlon) * np.cos(lat2),
            np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon),
        )
    )
    bearing = (bearing + 360.0) % 360.0
    bearing[left == right] = np.nan
    return distance, bearing


def _direction_codes(bearing: np.ndarray) -> np.ndarray:
    result = np.full(bearing.shape, -1, dtype=np.int8)
    finite = np.isfinite(bearing)
    result[finite] = (np.floor((bearing[finite] + 22.5) / 45).astype(int) % 8).astype(np.int8)
    return result


def _precomputed_tail_state(
    values: np.ndarray,
    *,
    tail: str,
    quantile: float,
) -> tuple[np.ndarray | None, np.ndarray | None, str]:
    valid = np.isfinite(values)
    if not np.all(valid == valid[0]):
        return None, None, "pairwise exact thresholds because valid-time masks differ"
    q = quantile if tail == "lower" else 1.0 - quantile
    thresholds = np.nanquantile(values, q, axis=1)
    states = valid & (values <= thresholds[:, None] if tail == "lower" else values > thresholds[:, None])
    return thresholds, states, "precomputed exact per-pixel threshold/state on shared valid-time support"


def _batched_one_tail_spearman(
    values: np.ndarray,
    left: np.ndarray,
    right: np.ndarray,
    *,
    tail: str,
    quantile: float,
    min_t: int,
    thresholds: np.ndarray | None,
    states: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    x = values[left]
    y = values[right]
    valid = np.isfinite(x) & np.isfinite(y)
    if states is None or thresholds is None:
        q = quantile if tail == "lower" else 1.0 - quantile
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            x_threshold = np.nanquantile(np.where(valid, x, np.nan), q, axis=1)
            y_threshold = np.nanquantile(np.where(valid, y, np.nan), q, axis=1)
        selected = valid & (
            (x <= x_threshold[:, None]) & (y <= y_threshold[:, None])
            if tail == "lower"
            else (x > x_threshold[:, None]) & (y > y_threshold[:, None])
        )
    else:
        selected = states[left] & states[right] & valid
    count = np.count_nonzero(selected, axis=1).astype(np.int16)
    ranked_x = rankdata(np.where(selected, x, np.nan), axis=1, method="average", nan_policy="omit")
    ranked_y = rankdata(np.where(selected, y, np.nan), axis=1, method="average", nan_policy="omit")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean_x = np.nanmean(ranked_x, axis=1)
        mean_y = np.nanmean(ranked_y, axis=1)
    centered_x = np.where(selected, ranked_x - mean_x[:, None], 0.0)
    centered_y = np.where(selected, ranked_y - mean_y[:, None], 0.0)
    denominator = np.sqrt(np.sum(centered_x**2, axis=1) * np.sum(centered_y**2, axis=1))
    output = np.divide(
        np.sum(centered_x * centered_y, axis=1),
        denominator,
        out=np.full(left.size, np.nan, dtype=float),
        where=denominator > 0,
    )
    output[count < min_t] = np.nan
    return output, count


def _eta_squared(values: np.ndarray, groups: np.ndarray) -> float:
    if values.size < 2:
        return float("nan")
    total = float(np.sum((values - values.mean()) ** 2))
    if total <= 0:
        return 0.0
    between = 0.0
    for group in np.unique(groups):
        selected = values[groups == group]
        between += selected.size * float((selected.mean() - values.mean()) ** 2)
    return between / total


def _mask_bounds(mask: np.ndarray, y: np.ndarray, x: np.ndarray) -> list[float]:
    yi, xi = np.nonzero(mask)
    return [float(x[xi].min()), float(y[yi].min()), float(x[xi].max()), float(y[yi].max())]


def _validate_pairs(pairs: xr.Dataset) -> None:
    if not isinstance(pairs, xr.Dataset) or pairs.attrs.get("analysis") != "local_synchrony_pairs":
        raise TypeError("Expected a Dataset produced by local_synchrony_pairs")
    required = {
        "cold_synchrony", "warm_synchrony", "delta_s", "distance_km",
        "bearing_degrees", "output_mask",
    }
    missing = sorted(required - set(pairs.data_vars))
    if missing:
        raise ValueError(f"Pair table is missing required variables: {missing!r}")


__all__ = [
    "expand_spatial_domain",
    "landscape_change_signature",
    "load_signature_checkpoint",
    "local_synchrony_pairs",
    "spatial_output_mask",
    "synchrony_signature",
    "tiled_landscape_change_signature",
    "tiled_synchrony_signature",
    "write_signature_checkpoint",
]
