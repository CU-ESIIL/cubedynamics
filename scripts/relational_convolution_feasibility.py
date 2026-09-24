"""Experimental relational-surface alignment and overlap diagnostics.

This module is intentionally outside the installed CubeDynamics package.  It
operates on validated stack products without changing the synchrony statistic
or exposing a production verb.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata


METRICS = ("cold_synchrony", "warm_synchrony", "delta_s")
RADII_KM = (20.0, 40.0, 60.0)
SEED = 20260923


@dataclass(frozen=True)
class GridGeometry:
    y: np.ndarray
    x: np.ndarray
    focal_y: np.ndarray
    focal_x: np.ndarray

    @property
    def shape(self) -> tuple[int, int]:
        return (self.y.size, self.x.size)


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_phase1_stack(path: Path) -> xr.Dataset:
    with xr.open_dataset(path) as source:
        stack = source.load()
    required = {
        "cold_synchrony",
        "warm_synchrony",
        "delta_s",
        "cold_joint_count",
        "warm_joint_count",
        "distance_km",
        "bearing_degrees",
    }
    missing = sorted(required - set(stack.data_vars))
    if stack.attrs.get("analysis") != "local_synchrony_stack" or missing:
        raise ValueError(f"Expected a complete local_synchrony_stack; missing={missing!r}")
    if stack.sizes["center"] != stack.sizes["y"] * stack.sizes["x"]:
        raise ValueError("Experiment requires one center for every focal-grid cell")
    expected_y, expected_x = np.divmod(
        np.arange(stack.sizes["center"]), stack.sizes["x"]
    )
    np.testing.assert_array_equal(stack.center_y_index.values, expected_y)
    np.testing.assert_array_equal(stack.center_x_index.values, expected_x)
    return stack


def complete_surface_object(stack: xr.Dataset) -> xr.Dataset:
    """Return explicit S(focal, comparison) with relative and absolute geometry."""

    ny, nx = stack.sizes["y"], stack.sizes["x"]
    n = ny * nx
    focal = np.arange(n, dtype=np.int32)
    comparison = np.arange(n, dtype=np.int32)
    fy, fx = np.divmod(focal, nx)
    qy, qx = np.divmod(comparison, nx)
    bearing = np.asarray(stack.bearing_degrees.values, dtype=float).reshape(n, n)
    distance = np.asarray(stack.distance_km.values, dtype=float).reshape(n, n)
    radians = np.deg2rad(np.nan_to_num(bearing, nan=0.0))
    canonical = np.minimum(focal[:, None], comparison[None, :]).astype(np.int64) * n
    canonical += np.maximum(focal[:, None], comparison[None, :]).astype(np.int64)
    variables: dict[str, tuple[tuple[str, str], np.ndarray]] = {}
    for name in (*METRICS, "cold_joint_count", "warm_joint_count"):
        variables[name] = (
            ("focal", "comparison"),
            np.asarray(stack[name].values).reshape(n, n),
        )
    variables.update(
        {
            "distance_km": (("focal", "comparison"), distance.astype(np.float32)),
            "bearing_degrees": (("focal", "comparison"), bearing.astype(np.float32)),
            "dx_km": (
                ("focal", "comparison"),
                (distance * np.sin(radians)).astype(np.float32),
            ),
            "dy_km": (
                ("focal", "comparison"),
                (distance * np.cos(radians)).astype(np.float32),
            ),
            "dx_index": (
                ("focal", "comparison"),
                np.broadcast_to(qx[None, :] - fx[:, None], (n, n)).astype(np.int16),
            ),
            "dy_index": (
                ("focal", "comparison"),
                np.broadcast_to(qy[None, :] - fy[:, None], (n, n)).astype(np.int16),
            ),
            "canonical_pair_id": (("focal", "comparison"), canonical),
            "reverse_endpoint_view": (
                ("focal", "comparison"),
                np.broadcast_to(focal[:, None] > comparison[None, :], (n, n)),
            ),
        }
    )
    result = xr.Dataset(
        variables,
        coords={
            "focal": focal,
            "comparison": comparison,
            "focal_y_index": ("focal", fy.astype(np.int16)),
            "focal_x_index": ("focal", fx.astype(np.int16)),
            "comparison_y_index": ("comparison", qy.astype(np.int16)),
            "comparison_x_index": ("comparison", qx.astype(np.int16)),
            "focal_y": ("focal", np.asarray(stack.y.values)[fy]),
            "focal_x": ("focal", np.asarray(stack.x.values)[fx]),
            "comparison_y": ("comparison", np.asarray(stack.y.values)[qy]),
            "comparison_x": ("comparison", np.asarray(stack.x.values)[qx]),
            "y": stack.y,
            "x": stack.x,
        },
        attrs={
            "analysis": "experimental_complete_relational_surface_object",
            "scientific_object": "S(x,y,dx,dy)",
            "source_analysis_fingerprint": stack.attrs.get(
                "analysis_fingerprint", "unknown"
            ),
            "window_start": stack.attrs.get("window_start", "unknown"),
            "window_end": stack.attrs.get("window_end", "unknown"),
            "pair_symmetry_policy": (
                "canonical_pair_id identifies endpoint reversals; reverse views are not "
                "independent evidence"
            ),
            "status": "experimental; not a public CubeDynamics verb",
        },
    )
    return result


def long_relationship_table(surfaces: xr.Dataset) -> pd.DataFrame:
    """Create the inspectable, unreduced relative/absolute support table."""

    n = surfaces.sizes["focal"]
    frame = pd.DataFrame(
        {
            "focal": np.repeat(surfaces.focal.values, n),
            "comparison": np.tile(surfaces.comparison.values, n),
        }
    )
    for name in (
        "focal_y_index",
        "focal_x_index",
        "focal_y",
        "focal_x",
    ):
        frame[name] = np.repeat(surfaces[name].values, n)
    for name in (
        "comparison_y_index",
        "comparison_x_index",
        "comparison_y",
        "comparison_x",
    ):
        frame[name] = np.tile(surfaces[name].values, n)
    for name in (
        *METRICS,
        "cold_joint_count",
        "warm_joint_count",
        "distance_km",
        "bearing_degrees",
        "dx_km",
        "dy_km",
        "dx_index",
        "dy_index",
        "canonical_pair_id",
        "reverse_endpoint_view",
    ):
        frame[name] = np.asarray(surfaces[name].values).reshape(-1)
    frame["is_self"] = frame.focal == frame.comparison
    return frame


def _pearson(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 3 or np.std(left) == 0 or np.std(right) == 0:
        return np.nan
    return float(np.corrcoef(left, right)[0, 1])


def _metrics(left: np.ndarray, right: np.ndarray, deadband: float = 0.02) -> dict[str, float | int]:
    valid = np.isfinite(left) & np.isfinite(right)
    a, b = left[valid], right[valid]
    if a.size == 0:
        return {
            "overlap_count": 0,
            "rmse": np.nan,
            "mae": np.nan,
            "pearson": np.nan,
            "spearman": np.nan,
            "sign_agreement": np.nan,
            "gradient_similarity": np.nan,
        }
    sign_valid = (np.abs(a) > deadband) & (np.abs(b) > deadband)
    return {
        "overlap_count": int(a.size),
        "rmse": float(np.sqrt(np.mean((a - b) ** 2))),
        "mae": float(np.mean(np.abs(a - b))),
        "pearson": _pearson(a, b),
        "spearman": _pearson(rankdata(a), rankdata(b)),
        "sign_agreement": (
            float(np.mean(np.sign(a[sign_valid]) == np.sign(b[sign_valid])))
            if np.any(sign_valid)
            else np.nan
        ),
        "gradient_similarity": np.nan,
    }


def _edge_vector(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    horizontal = values[:, 1:] - values[:, :-1]
    hvalid = valid[:, 1:] & valid[:, :-1]
    vertical = values[1:, :] - values[:-1, :]
    vvalid = valid[1:, :] & valid[:-1, :]
    return np.concatenate((horizontal[hvalid], vertical[vvalid]))


def _alignment_arrays(
    values: np.ndarray,
    distance: np.ndarray,
    a: int,
    b: int,
    nx: int,
    radius_km: float,
    alignment: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ny = values.shape[1] // nx
    ay, ax = divmod(a, nx)
    by, bx = divmod(b, nx)
    left = values[a].reshape(ny, nx)
    right = values[b].reshape(ny, nx)
    left_valid = np.isfinite(left) & (distance[a].reshape(ny, nx) <= radius_km)
    right_valid = np.isfinite(right) & (distance[b].reshape(ny, nx) <= radius_km)
    left_valid[ay, ax] = False
    right_valid[by, bx] = False
    if alignment == "absolute":
        return left, right, left_valid, right_valid
    if alignment != "relative":
        raise ValueError("alignment must be 'relative' or 'absolute'")
    dy, dx = by - ay, bx - ax
    y0a, y1a = max(0, -dy), min(ny, ny - dy)
    x0a, x1a = max(0, -dx), min(nx, nx - dx)
    y0b, y1b = y0a + dy, y1a + dy
    x0b, x1b = x0a + dx, x1a + dx
    return (
        left[y0a:y1a, x0a:x1a],
        right[y0b:y1b, x0b:x1b],
        left_valid[y0a:y1a, x0a:x1a],
        right_valid[y0b:y1b, x0b:x1b],
    )


def neighboring_surface_similarity(
    surfaces: xr.Dataset,
    *,
    metric: str,
    radii_km: Iterable[float] = RADII_KM,
    center_margin: int = 2,
) -> pd.DataFrame:
    """Compare adjacent surfaces before and after known geographic alignment."""

    if metric not in METRICS:
        raise ValueError(f"metric must be one of {METRICS!r}")
    ny, nx = surfaces.sizes["y"], surfaces.sizes["x"]
    values = np.asarray(surfaces[metric].values, dtype=float)
    distance = np.asarray(surfaces.distance_km.values, dtype=float)
    rows: list[dict[str, object]] = []
    for ay in range(center_margin, ny - center_margin):
        for ax in range(center_margin, nx - center_margin):
            a = ay * nx + ax
            for orientation, dy, dx in (("east_west", 0, 1), ("north_south", 1, 0)):
                by, bx = ay + dy, ax + dx
                if by >= ny - center_margin + 1 or bx >= nx - center_margin + 1:
                    continue
                b = by * nx + bx
                for radius in radii_km:
                    for alignment in ("relative", "absolute"):
                        left, right, left_valid, right_valid = _alignment_arrays(
                            values, distance, a, b, nx, float(radius), alignment
                        )
                        common = left_valid & right_valid
                        record = _metrics(left[common], right[common])
                        edge_left = _edge_vector(left, common)
                        edge_right = _edge_vector(right, common)
                        if edge_left.size == edge_right.size and edge_left.size >= 3:
                            record["gradient_similarity"] = _pearson(edge_left, edge_right)
                        rows.append(
                            {
                                "metric": metric,
                                "radius_km": float(radius),
                                "orientation": orientation,
                                "center_a": a,
                                "center_b": b,
                                "center_a_y_index": ay,
                                "center_a_x_index": ax,
                                "center_b_y_index": by,
                                "center_b_x_index": bx,
                                "alignment": alignment,
                                **record,
                            }
                        )
    result = pd.DataFrame(rows)
    wide = result.pivot_table(
        index=[
            "metric",
            "radius_km",
            "orientation",
            "center_a",
            "center_b",
            "center_a_y_index",
            "center_a_x_index",
            "center_b_y_index",
            "center_b_x_index",
        ],
        columns="alignment",
        values=[
            "overlap_count",
            "rmse",
            "mae",
            "pearson",
            "spearman",
            "sign_agreement",
            "gradient_similarity",
        ],
    )
    wide.columns = [f"{name}_{alignment}" for name, alignment in wide.columns]
    wide = wide.reset_index()
    for name in ("pearson", "spearman", "sign_agreement", "gradient_similarity"):
        wide[f"{name}_alignment_gain"] = (
            wide[f"{name}_absolute"] - wide[f"{name}_relative"]
        )
    for name in ("rmse", "mae"):
        wide[f"{name}_alignment_gain"] = wide[f"{name}_relative"] - wide[f"{name}_absolute"]
    return wide


def absolute_overlap_support(
    surfaces: xr.Dataset, *, metric: str, radius_km: float
) -> xr.Dataset:
    """Summarize while retaining the complete contribution axis in ``surfaces``."""

    values = np.asarray(surfaces[metric].values, dtype=float)
    distance = np.asarray(surfaces.distance_km.values, dtype=float)
    focal = np.asarray(surfaces.focal.values)
    comparison = np.asarray(surfaces.comparison.values)
    valid = np.isfinite(values) & (distance <= radius_km)
    valid &= focal[:, None] != comparison[None, :]
    masked = np.where(valid, values, np.nan)
    count = np.sum(valid, axis=0)
    median = np.nanmedian(masked, axis=0)
    q25, q75 = np.nanquantile(masked, (0.25, 0.75), axis=0)
    mad = np.nanmedian(np.abs(masked - median[None, :]), axis=0)
    global_iqr = float(np.nanquantile(values, 0.75) - np.nanquantile(values, 0.25))
    coherence = np.clip(1.0 - mad / max(global_iqr, 1e-12), 0.0, 1.0)
    ny, nx = surfaces.sizes["y"], surfaces.sizes["x"]
    return xr.Dataset(
        {
            "contributing_surface_count": (("y", "x"), count.reshape(ny, nx)),
            "unique_canonical_pair_count": (("y", "x"), count.reshape(ny, nx)),
            "median": (("y", "x"), median.reshape(ny, nx)),
            "iqr": (("y", "x"), (q75 - q25).reshape(ny, nx)),
            "mad": (("y", "x"), mad.reshape(ny, nx)),
            "overlap_coherence": (("y", "x"), coherence.reshape(ny, nx)),
        },
        coords={"y": surfaces.y, "x": surfaces.x},
        attrs={
            "analysis": "experimental_absolute_overlap_support",
            "metric": metric,
            "radius_km": float(radius_km),
            "aggregation_warning": (
                "The unreduced contributor values and canonical_pair_id remain in "
                "real_complete_surfaces.nc; this file is a diagnostic projection."
            ),
            "symmetry_policy": (
                "Each absolute target receives at most one contribution from each focal; "
                "endpoint-reversal views are not counted as replicate support at one target."
            ),
        },
    )


def translated_edge_support(
    values: np.ndarray,
    distance: np.ndarray,
    *,
    radius: float,
    y: np.ndarray | None = None,
    x: np.ndarray | None = None,
) -> xr.Dataset:
    """Aggregate gradients at fixed absolute raster edges across focal surfaces."""

    if values.ndim != 3 or distance.shape != values.shape:
        raise ValueError("values and distance must have shape (focal, y, x)")
    nfocal, ny, nx = values.shape
    focal_y, focal_x = np.divmod(np.arange(nfocal), nx)
    outputs: dict[str, tuple[tuple[str, str], np.ndarray]] = {}
    for orientation, axis in (("east_west", 2), ("north_south", 1)):
        if axis == 2:
            gradient = values[:, :, 1:] - values[:, :, :-1]
            valid = (
                np.isfinite(values[:, :, 1:])
                & np.isfinite(values[:, :, :-1])
                & (distance[:, :, 1:] <= radius)
                & (distance[:, :, :-1] <= radius)
            )
            yy, xx = np.indices((ny, nx - 1))
            endpoint = (
                ((focal_y[:, None, None] == yy) & (focal_x[:, None, None] == xx))
                | ((focal_y[:, None, None] == yy) & (focal_x[:, None, None] == xx + 1))
            )
        else:
            gradient = values[:, 1:, :] - values[:, :-1, :]
            valid = (
                np.isfinite(values[:, 1:, :])
                & np.isfinite(values[:, :-1, :])
                & (distance[:, 1:, :] <= radius)
                & (distance[:, :-1, :] <= radius)
            )
            yy, xx = np.indices((ny - 1, nx))
            endpoint = (
                ((focal_y[:, None, None] == yy) & (focal_x[:, None, None] == xx))
                | ((focal_y[:, None, None] == yy + 1) & (focal_x[:, None, None] == xx))
            )
        valid &= ~endpoint
        observed = np.where(valid, gradient, np.nan)
        count = np.sum(valid, axis=0)
        signed_median = np.nanmedian(observed, axis=0)
        absolute_median = np.nanmedian(np.abs(observed), axis=0)
        mad = np.nanmedian(np.abs(observed - signed_median[None, ...]), axis=0)
        sign_valid = valid & (np.abs(gradient) > 1e-12)
        signed_sum = np.sum(np.where(sign_valid, np.sign(gradient), 0.0), axis=0)
        signed_count = np.sum(sign_valid, axis=0)
        sign_coherence = np.full(signed_sum.shape, np.nan, dtype=float)
        np.divide(
            np.abs(signed_sum),
            signed_count,
            out=sign_coherence,
            where=signed_count > 0,
        )
        support_weight = np.sqrt(count / max(int(np.nanmax(count)), 1))
        transition_evidence = absolute_median * support_weight
        dims = ("edge_y", "edge_x")
        prefix = orientation
        outputs[f"{prefix}_contributing_surface_count"] = (dims, count.astype(np.int32))
        outputs[f"{prefix}_signed_gradient_median"] = (dims, signed_median)
        outputs[f"{prefix}_absolute_gradient_median"] = (dims, absolute_median)
        outputs[f"{prefix}_gradient_mad"] = (dims, mad)
        outputs[f"{prefix}_sign_coherence"] = (dims, sign_coherence)
        outputs[f"{prefix}_transition_evidence"] = (dims, transition_evidence)
    max_y, max_x = max(ny, ny - 1), max(nx, nx - 1)
    padded: dict[str, tuple[tuple[str, str], np.ndarray]] = {}
    for name, (_, array) in outputs.items():
        fill = np.full((max_y, max_x), np.nan)
        fill[: array.shape[0], : array.shape[1]] = array
        padded[name] = (("edge_y", "edge_x"), fill)
    return xr.Dataset(
        padded,
        coords={
            "edge_y": np.arange(max_y) if y is None else np.asarray(y)[:max_y],
            "edge_x": np.arange(max_x) if x is None else np.asarray(x)[:max_x],
        },
        attrs={
            "analysis": "experimental_translated_edge_support",
            "radius": float(radius),
            "self_edge_policy": "gradients incident to the focal self cell are excluded",
            "transition_status": "one candidate; not a classified boundary product",
        },
    )


def _relative_surface(values: np.ndarray, focal_index: int, nx: int) -> xr.Dataset:
    ny = values.shape[1]
    fy, fx = divmod(focal_index, nx)
    oy = np.arange(ny) - fy
    ox = np.arange(nx) - fx
    distance = np.hypot(
        np.broadcast_to(oy[:, None], (ny, nx)),
        np.broadcast_to(ox[None, :], (ny, nx)),
    )
    bearing = np.rad2deg(
        np.arctan2(np.broadcast_to(ox[None, :], (ny, nx)), -np.broadcast_to(oy[:, None], (ny, nx)))
    ) % 360.0
    return xr.Dataset(
        {
            "delta_s": (("offset_y_index", "offset_x_index"), values[focal_index]),
            "distance_km": (("offset_y_index", "offset_x_index"), distance),
            "bearing_degrees": (("offset_y_index", "offset_x_index"), bearing),
            "dx_km": (("offset_y_index", "offset_x_index"), np.broadcast_to(ox[None, :], (ny, nx))),
            "dy_km": (("offset_y_index", "offset_x_index"), -np.broadcast_to(oy[:, None], (ny, nx))),
        },
        coords={"offset_y_index": oy, "offset_x_index": ox},
        attrs={"analysis": "local_synchrony_surface", "observation_radius_km": float(np.nanmax(distance))},
    )


def representation_comparison(
    surfaces: xr.Dataset,
    *,
    metric: str = "delta_s",
    radius_km: float = 40.0,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Compare independent reductions and a held-out relative-coordinate SVD."""

    ny, nx = surfaces.sizes["y"], surfaces.sizes["x"]
    values = np.asarray(surfaces[metric].values, dtype=float).reshape(-1, ny, nx)
    distance = np.asarray(surfaces.distance_km.values, dtype=float).reshape(-1, ny, nx)
    selected = [y * nx + x for y in range(6, ny - 6) for x in range(6, nx - 6)]
    rows: list[dict[str, object]] = []
    errors: dict[str, list[float]] = {
        "median_only": [],
        "median_iqr_mad": [],
        "nested_radii": [],
        "fine_radial_profile": [],
        "radial_plus_directional": [],
    }
    relative_vectors = []
    offsets = np.arange(-6, 7)
    yy, xx = np.meshgrid(offsets, offsets, indexing="ij")
    for focal in selected:
        fy, fx = divmod(focal, nx)
        local = values[focal, fy - 6 : fy + 7, fx - 6 : fx + 7]
        local_distance = distance[focal, fy - 6 : fy + 7, fx - 6 : fx + 7]
        valid = np.isfinite(local) & (local_distance <= radius_km)
        observed = local[valid]
        if observed.size < 20:
            continue
        scale = float(np.std(observed))
        if scale == 0:
            scale = 1.0
        median = float(np.median(observed))
        errors["median_only"].append(float(np.sqrt(np.mean((observed - median) ** 2)) / scale))
        errors["median_iqr_mad"].append(errors["median_only"][-1])
        predictions: dict[str, np.ndarray] = {}
        nested = np.full(local.shape, np.nan)
        lower = 0.0
        for upper in (20.0, 40.0):
            support = valid & (local_distance <= upper)
            ring = valid & (local_distance > lower) & (local_distance <= upper)
            if np.any(support):
                nested[ring] = np.median(local[support])
            lower = upper
        predictions["nested_radii"] = nested
        radial = np.full(local.shape, np.nan)
        bins = np.floor(local_distance / 5.0).astype(int)
        for index in np.unique(bins[valid]):
            ring = valid & (bins == index)
            radial[ring] = np.median(local[ring])
        predictions["fine_radial_profile"] = radial
        bearing = np.rad2deg(np.arctan2(xx, -yy)) % 360.0
        sector = np.floor(bearing / 45.0).astype(int)
        radial_directional = radial.copy()
        residual = local - radial
        for index in range(8):
            support = valid & (sector == index) & np.isfinite(residual)
            if np.any(support):
                radial_directional[valid & (sector == index)] += np.median(residual[support])
        predictions["radial_plus_directional"] = radial_directional
        for name, prediction in predictions.items():
            keep = valid & np.isfinite(prediction)
            errors[name].append(float(np.sqrt(np.mean((local[keep] - prediction[keep]) ** 2)) / scale))
        vector = np.full(local.shape, np.nan)
        vector[valid] = local[valid]
        relative_vectors.append(vector)
    for name, observed_errors in errors.items():
        rows.append(
            {
                "representation": name,
                "median_normalized_rmse": float(np.median(observed_errors)),
                "p90_normalized_rmse": float(np.quantile(observed_errors, 0.9)),
                "surface_count": len(observed_errors),
            }
        )
    matrix3d = np.asarray(relative_vectors)
    common = np.all(np.isfinite(matrix3d), axis=0)
    matrix = matrix3d[:, common]
    rng = np.random.default_rng(SEED)
    order = rng.permutation(matrix.shape[0])
    split = max(2, int(matrix.shape[0] * 0.75))
    train, test = matrix[order[:split]], matrix[order[split:]]
    mean = train.mean(axis=0)
    _, singular, vt = np.linalg.svd(train - mean, full_matrices=False)
    cumulative = np.cumsum(singular**2 / np.sum(singular**2))
    pca_rows = []
    for components in (1, 2, 4, 8, 12):
        if components > vt.shape[0]:
            continue
        basis = vt[:components]
        reconstructed = mean + ((test - mean) @ basis.T) @ basis
        rmse = np.sqrt(np.mean((test - reconstructed) ** 2, axis=1))
        scale = np.std(test, axis=1)
        pca_rows.append(
            {
                "components": components,
                "training_cumulative_variance": float(cumulative[components - 1]),
                "held_out_median_normalized_rmse": float(np.median(rmse / scale)),
            }
        )
    chosen = next(row for row in pca_rows if row["components"] == min(8, pca_rows[-1]["components"]))
    rows.append(
        {
            "representation": "pca_svd",
            "median_normalized_rmse": chosen["held_out_median_normalized_rmse"],
            "p90_normalized_rmse": np.nan,
            "surface_count": int(test.shape[0]),
        }
    )
    return pd.DataFrame(rows), {
        "surface_count": int(matrix.shape[0]),
        "common_cell_count": int(matrix.shape[1]),
        "train_count": int(train.shape[0]),
        "test_count": int(test.shape[0]),
        "results": pca_rows,
        "autoencoder_tested": False,
        "autoencoder_reason": (
            "Not justified: the feasibility decision can be made with transparent operators "
            "and held-out SVD; no new learned dependency was added."
        ),
    }


def symmetric_synthetic_field(
    case: str,
    *,
    size: int = 17,
    radius_cells: float = 7.0,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    """Construct a known symmetric relational field S(p,q)."""

    names = {
        "uniform",
        "isotropic_distance_decay",
        "smooth_geographic_gradient",
        "directional_anisotropy",
        "sharp_geographic_transition",
        "nonmonotonic_radial",
        "spatially_varying_distance",
        "noise_only",
        "transition_plus_distance",
        "anisotropy_no_transition",
    }
    if case not in names:
        raise ValueError(f"Unknown synthetic case {case!r}")
    n = size * size
    py, px = np.divmod(np.arange(n), size)
    qy, qx = np.divmod(np.arange(n), size)
    dy = qy[None, :] - py[:, None]
    dx = qx[None, :] - px[:, None]
    distance = np.hypot(dx, dy)
    bearing = np.arctan2(dx, -dy)
    midpoint_x = (px[:, None] + qx[None, :]) / 2.0
    midpoint_y = (py[:, None] + qy[None, :]) / 2.0
    center = (size - 1) / 2.0
    same_region = (px[:, None] < center) == (qx[None, :] < center)
    if case == "uniform":
        values = np.full((n, n), 0.25)
    elif case == "isotropic_distance_decay":
        values = np.exp(-distance / 3.0)
    elif case == "smooth_geographic_gradient":
        values = 0.08 * (midpoint_x - center) + 0.02 * (midpoint_y - center)
    elif case in {"directional_anisotropy", "anisotropy_no_transition"}:
        values = 0.55 * np.cos(2.0 * (bearing - np.deg2rad(30.0)))
        if case == "anisotropy_no_transition":
            values += 0.08 * np.cos(distance)
    elif case == "sharp_geographic_transition":
        values = np.where(same_region, 0.55, -0.55)
    elif case == "nonmonotonic_radial":
        values = 0.55 * np.cos(distance * 1.2)
    elif case == "spatially_varying_distance":
        scale = 1.8 + 4.0 * midpoint_x / max(size - 1, 1)
        values = np.exp(-distance / scale)
    elif case == "noise_only":
        rng = np.random.default_rng(seed)
        upper = rng.normal(scale=0.35, size=(n, n))
        values = np.triu(upper) + np.triu(upper, 1).T
    else:
        values = np.where(same_region, 0.45, -0.45) + 0.35 * np.exp(-distance / 3.0)
    values = np.where(distance <= radius_cells, values, np.nan)
    values = values.reshape(n, size, size)
    distance3 = np.broadcast_to(distance.reshape(n, size, size), values.shape).copy()
    metadata = {
        "case": case,
        "size": size,
        "radius_cells": radius_cells,
        "pair_symmetry_max_error": float(
            np.nanmax(
                np.abs(values.reshape(n, n) - values.reshape(n, n).T)
            )
        ),
        "has_transition": case in {"sharp_geographic_transition", "transition_plus_distance"},
        "has_anisotropy": case in {"directional_anisotropy", "anisotropy_no_transition"},
        "has_distance_structure": case in {
            "isotropic_distance_decay",
            "nonmonotonic_radial",
            "spatially_varying_distance",
            "transition_plus_distance",
        },
    }
    return values, distance3, metadata


def _edge_ratio(edge_map: np.ndarray, *, transition: bool) -> float:
    finite = np.isfinite(edge_map)
    if not np.any(finite):
        return np.nan
    if not transition:
        return float(np.nanmax(edge_map) / max(np.nanmedian(edge_map), 1e-12))
    boundary_column = edge_map.shape[1] // 2 - 1
    on = edge_map[:, boundary_column]
    off_mask = finite.copy()
    off_mask[:, max(0, boundary_column - 1) : boundary_column + 2] = False
    return float(np.nanmedian(on) / max(np.nanmedian(edge_map[off_mask]), 1e-12))


def synthetic_benchmark() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    cases = (
        "uniform",
        "isotropic_distance_decay",
        "smooth_geographic_gradient",
        "directional_anisotropy",
        "sharp_geographic_transition",
        "nonmonotonic_radial",
        "spatially_varying_distance",
        "noise_only",
        "transition_plus_distance",
        "anisotropy_no_transition",
    )
    for case in cases:
        values, distance, metadata = symmetric_synthetic_field(case)
        support = translated_edge_support(values, distance, radius=7.0)
        transition_map = np.asarray(support.east_west_transition_evidence.values)
        focal_summary = np.nanmedian(values, axis=(1, 2)).reshape(17, 17)
        smoothed = gaussian_filter(focal_summary, sigma=1.0)
        smooth_edge = np.abs(np.diff(smoothed, axis=1))
        rows.append(
            {
                **metadata,
                "translated_transition_edge_ratio": _edge_ratio(
                    transition_map[:, :16], transition=bool(metadata["has_transition"])
                ),
                "smoothed_median_edge_ratio": _edge_ratio(
                    smooth_edge, transition=bool(metadata["has_transition"])
                ),
                "median_transition_evidence": float(np.nanmedian(transition_map)),
                "maximum_transition_evidence": float(np.nanmax(transition_map)),
                "median_gradient_sign_coherence": (
                    float(np.median(support.east_west_sign_coherence.values[np.isfinite(support.east_west_sign_coherence.values)]))
                    if np.any(np.isfinite(support.east_west_sign_coherence.values))
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def window_stability(
    surfaces: xr.Dataset, *, metric: str = "delta_s", radii_km: Iterable[float] = RADII_KM
) -> pd.DataFrame:
    values = np.asarray(surfaces[metric].values, dtype=float).reshape(
        surfaces.sizes["focal"], surfaces.sizes["y"], surfaces.sizes["x"]
    )
    distance = np.asarray(surfaces.distance_km.values, dtype=float).reshape(values.shape)
    maps = {}
    for radius in radii_km:
        support = translated_edge_support(values, distance, radius=float(radius))
        maps[float(radius)] = np.asarray(support.east_west_transition_evidence.values)
    rows = []
    radii = sorted(maps)
    for left, right in zip(radii[:-1], radii[1:]):
        a, b = maps[left], maps[right]
        valid = np.isfinite(a) & np.isfinite(b)
        rows.append(
            {
                "metric": metric,
                "left_radius_km": left,
                "right_radius_km": right,
                "shared_edge_count": int(np.count_nonzero(valid)),
                "pearson": _pearson(a[valid], b[valid]),
                "spearman": _pearson(rankdata(a[valid]), rankdata(b[valid])),
                "normalized_rmse": float(
                    np.sqrt(np.mean((a[valid] - b[valid]) ** 2))
                    / max(np.std(np.concatenate((a[valid], b[valid]))), 1e-12)
                ),
            }
        )
    return pd.DataFrame(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = [
    "METRICS",
    "RADII_KM",
    "absolute_overlap_support",
    "complete_surface_object",
    "load_phase1_stack",
    "long_relationship_table",
    "neighboring_surface_similarity",
    "representation_comparison",
    "sha256_file",
    "symmetric_synthetic_field",
    "synthetic_benchmark",
    "translated_edge_support",
    "window_stability",
    "write_json",
]
