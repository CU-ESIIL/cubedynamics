"""Reconstruct and diagnose local synchrony surfaces.

The scientific object in this module is ``S_p(dx, dy)``: the synchrony values
contributed by center locations around one focal pixel.  Distance and direction
are coordinates of that surface.  Radial and angular profiles are projections,
not substitutes for the two-dimensional object.
"""

from __future__ import annotations

import json
from typing import Literal

import numpy as np
import xarray as xr
from scipy.stats import spearmanr


_METRICS = ("cold_synchrony", "warm_synchrony", "delta_s")


def local_synchrony_surface(
    pairs: xr.Dataset,
    *,
    focal_y_index: int | None = None,
    focal_x_index: int | None = None,
    focal_index: int | None = None,
) -> xr.Dataset:
    """Recover one complete local ``S_p(dx, dy)`` surface from sparse pairs.

    Canonical pairs are calculated once.  When the focal pixel is the canonical
    target, signed displacement is reversed and bearing is rotated 180 degrees
    so every returned coordinate is center-relative-to-focal.
    """

    _validate_pair_table(pairs)
    y_dim, x_dim = pairs.output_mask.dims
    y_size = pairs.sizes[y_dim]
    x_size = pairs.sizes[x_dim]
    if focal_index is None:
        if focal_y_index is None or focal_x_index is None:
            raise ValueError("Provide focal_index or both focal_y_index and focal_x_index")
        focal_index = int(focal_y_index) * x_size + int(focal_x_index)
    focal_index = int(focal_index)
    if focal_index < 0 or focal_index >= y_size * x_size:
        raise IndexError("focal_index is outside the pair table grid")
    focal_y_index, focal_x_index = divmod(focal_index, x_size)
    selected_mask = np.asarray(pairs.output_mask.values, dtype=bool).reshape(-1)
    if not selected_mask[focal_index]:
        raise ValueError("The focal pixel is not selected by the pair table output mask")

    source = np.asarray(pairs.source_index.values, dtype=np.int64)
    target = np.asarray(pairs.target_index.values, dtype=np.int64)
    incident = (source == focal_index) | (target == focal_index)
    pair_index = np.flatnonzero(incident)
    if pair_index.size == 0:
        raise ValueError("No pairs are incident to the focal pixel")
    reverse = (target[pair_index] == focal_index) & (source[pair_index] != focal_index)
    other = np.where(source[pair_index] == focal_index, target[pair_index], source[pair_index])
    other_y, other_x = np.divmod(other, x_size)
    offset_y = other_y - focal_y_index
    offset_x = other_x - focal_x_index
    y_offsets = np.arange(offset_y.min(), offset_y.max() + 1, dtype=np.int32)
    x_offsets = np.arange(offset_x.min(), offset_x.max() + 1, dtype=np.int32)
    row = offset_y - y_offsets[0]
    column = offset_x - x_offsets[0]
    shape = (y_offsets.size, x_offsets.size)

    data_vars: dict[str, tuple[tuple[str, str], np.ndarray]] = {}
    for name in (*_METRICS, "distance_km", "cold_joint_count", "warm_joint_count"):
        fill = np.full(shape, np.nan, dtype=float)
        fill[row, column] = np.asarray(pairs[name].values, dtype=float)[pair_index]
        data_vars[name] = (("offset_y_index", "offset_x_index"), fill)

    bearing = np.asarray(pairs.bearing_degrees.values, dtype=float)[pair_index].copy()
    bearing[reverse & np.isfinite(bearing)] = (
        bearing[reverse & np.isfinite(bearing)] + 180.0
    ) % 360.0
    dx_km = np.asarray(pairs.dx_km.values, dtype=float)[pair_index].copy()
    dy_km = np.asarray(pairs.dy_km.values, dtype=float)[pair_index].copy()
    dx_km[reverse] *= -1.0
    dy_km[reverse] *= -1.0
    for name, values in (
        ("bearing_degrees", bearing),
        ("dx_km", dx_km),
        ("dy_km", dy_km),
    ):
        fill = np.full(shape, np.nan, dtype=float)
        fill[row, column] = values
        data_vars[name] = (("offset_y_index", "offset_x_index"), fill)

    center_y = np.full(shape, np.nan, dtype=float)
    center_x = np.full(shape, np.nan, dtype=float)
    center_y[row, column] = np.asarray(pairs[y_dim].values, dtype=float)[other_y]
    center_x[row, column] = np.asarray(pairs[x_dim].values, dtype=float)[other_x]
    data_vars["center_y"] = (("offset_y_index", "offset_x_index"), center_y)
    data_vars["center_x"] = (("offset_y_index", "offset_x_index"), center_x)

    result = xr.Dataset(
        data_vars,
        coords={"offset_y_index": y_offsets, "offset_x_index": x_offsets},
        attrs={
            "analysis": "local_synchrony_surface",
            "semantic_kind": "field",
            "scientific_object": "S_p(dx,dy)",
            "source_pair_fingerprint": pairs.attrs.get("analysis_fingerprint", "unknown"),
            "focal_index": focal_index,
            "focal_y_index": focal_y_index,
            "focal_x_index": focal_x_index,
            "focal_y": float(pairs[y_dim].values[focal_y_index]),
            "focal_x": float(pairs[x_dim].values[focal_x_index]),
            "observation_radius_km": float(
                pairs.attrs.get("observation_radius_km", pairs.attrs["max_radius_km"])
            ),
            "observation_radius_definition": (
                "maximum observed pair distance; not an inferred characteristic scale"
            ),
            "endpoint_orientation": (
                "all displacement and bearing values point from the focal pixel to the center"
            ),
        },
    )
    result["bearing_degrees"].attrs.update(
        {"units": "degrees", "definition": "forward bearing from focal pixel to center"}
    )
    result["dx_km"].attrs.update(
        {"units": "km", "definition": "signed eastward center displacement from focal"}
    )
    result["dy_km"].attrs.update(
        {"units": "km", "definition": "signed northward center displacement from focal"}
    )
    return result


def radial_profile(
    surface: xr.Dataset,
    *,
    metric: str = "delta_s",
    bin_width_km: float = 5.0,
    min_count: int = 3,
    reducer: Literal["median", "mean"] = "median",
) -> xr.Dataset:
    """Project a local surface onto fine radial numerical support."""

    _validate_surface(surface, metric)
    if bin_width_km <= 0:
        raise ValueError("bin_width_km must be positive")
    if min_count < 1:
        raise ValueError("min_count must be at least 1")
    if reducer not in {"median", "mean"}:
        raise ValueError("reducer must be 'median' or 'mean'")
    maximum = float(surface.attrs["observation_radius_km"])
    edges = np.arange(0.0, maximum + bin_width_km, bin_width_km)
    if edges[-1] < maximum:
        edges = np.append(edges, maximum)
    distance = np.asarray(surface.distance_km.values, dtype=float).ravel()
    values = np.asarray(surface[metric].values, dtype=float).ravel()
    valid = np.isfinite(distance) & np.isfinite(values)
    bin_index = np.digitize(distance, edges, right=False) - 1
    bin_index[np.isclose(distance, maximum)] = edges.size - 2
    profile = np.full(edges.size - 1, np.nan, dtype=float)
    q25 = np.full_like(profile, np.nan)
    q75 = np.full_like(profile, np.nan)
    count = np.zeros(profile.size, dtype=np.int32)
    for index in range(profile.size):
        observed = values[valid & (bin_index == index)]
        count[index] = observed.size
        if observed.size >= min_count:
            profile[index] = np.median(observed) if reducer == "median" else np.mean(observed)
            q25[index], q75[index] = np.quantile(observed, (0.25, 0.75))
    result = xr.Dataset(
        {
            "profile": ("radial_bin", profile),
            "q25": ("radial_bin", q25),
            "q75": ("radial_bin", q75),
            "valid_count": ("radial_bin", count),
        },
        coords={
            "radial_bin": np.arange(profile.size),
            "radius_km": ("radial_bin", (edges[:-1] + edges[1:]) / 2.0),
            "radius_lower_km": ("radial_bin", edges[:-1]),
            "radius_upper_km": ("radial_bin", edges[1:]),
        },
        attrs={
            "analysis": "radial_profile",
            "metric": metric,
            "reducer": reducer,
            "bin_width_km": float(bin_width_km),
            "scientific_role": (
                "fine annuli approximate the continuous S_p(r) projection; bins are not "
                "prescribed characteristic scales"
            ),
        },
    )
    return result


def angular_profile(
    surface: xr.Dataset,
    *,
    metric: str = "delta_s",
    bin_width_degrees: float = 15.0,
    min_count: int = 3,
    radial_detrend_bin_width_km: float | None = 10.0,
) -> xr.Dataset:
    """Project a surface onto bearing, optionally after fine radial detrending."""

    _validate_surface(surface, metric)
    if bin_width_degrees <= 0 or 360 % bin_width_degrees > 1e-9:
        raise ValueError("bin_width_degrees must divide 360")
    bearing = np.asarray(surface.bearing_degrees.values, dtype=float).ravel()
    values = np.asarray(surface[metric].values, dtype=float).ravel().copy()
    distance = np.asarray(surface.distance_km.values, dtype=float).ravel()
    valid = np.isfinite(bearing) & np.isfinite(values)
    if radial_detrend_bin_width_km is not None:
        width = float(radial_detrend_bin_width_km)
        if width <= 0:
            raise ValueError("radial_detrend_bin_width_km must be positive or None")
        radial_index = np.floor(np.where(np.isfinite(distance), distance, 0.0) / width).astype(
            np.int32
        )
        for index in np.unique(radial_index[valid]):
            selected = valid & (radial_index == index)
            values[selected] -= np.median(values[selected])
    edges = np.arange(0.0, 360.0 + bin_width_degrees, bin_width_degrees)
    index = np.floor(
        np.where(np.isfinite(bearing), bearing, 0.0) / bin_width_degrees
    ).astype(np.int32)
    profile = np.full(edges.size - 1, np.nan, dtype=float)
    count = np.zeros(profile.size, dtype=np.int32)
    for sector in range(profile.size):
        observed = values[valid & (index == sector)]
        count[sector] = observed.size
        if observed.size >= min_count:
            profile[sector] = np.median(observed)
    return xr.Dataset(
        {
            "profile": ("angular_bin", profile),
            "valid_count": ("angular_bin", count),
        },
        coords={
            "angular_bin": np.arange(profile.size),
            "bearing_degrees": ("angular_bin", (edges[:-1] + edges[1:]) / 2.0),
            "bearing_lower_degrees": ("angular_bin", edges[:-1]),
            "bearing_upper_degrees": ("angular_bin", edges[1:]),
        },
        attrs={
            "analysis": "angular_profile",
            "metric": metric,
            "radial_detrend_bin_width_km": (
                "none" if radial_detrend_bin_width_km is None else float(radial_detrend_bin_width_km)
            ),
            "scientific_role": "S_p(theta) projection; direction remains distinct from distance",
        },
    )


def low_order_surface_reconstruction(
    surface: xr.Dataset,
    *,
    metric: str = "delta_s",
) -> xr.DataArray:
    """Fit a small interpretable 2-D basis for diagnostic reconstruction."""

    _validate_surface(surface, metric)
    values = np.asarray(surface[metric].values, dtype=float)
    x = np.asarray(surface.dx_km.values, dtype=float)
    y = np.asarray(surface.dy_km.values, dtype=float)
    valid = np.isfinite(values) & np.isfinite(x) & np.isfinite(y)
    if np.count_nonzero(valid) < 10:
        raise ValueError("At least 10 valid surface cells are required")
    scale = float(np.nanmax(np.hypot(x[valid], y[valid])))
    xn = x[valid] / scale
    yn = y[valid] / scale
    radius = np.hypot(xn, yn)
    design = np.column_stack(
        (
            np.ones(xn.size),
            radius,
            radius**2,
            xn,
            yn,
            xn**2 - yn**2,
            2.0 * xn * yn,
        )
    )
    coefficients, *_ = np.linalg.lstsq(design, values[valid], rcond=None)
    predicted = design @ coefficients
    geometry_valid = np.isfinite(x) & np.isfinite(y)
    all_x = x[geometry_valid] / scale
    all_y = y[geometry_valid] / scale
    all_radius = np.hypot(all_x, all_y)
    all_design = np.column_stack(
        (
            np.ones(all_x.size),
            all_radius,
            all_radius**2,
            all_x,
            all_y,
            all_x**2 - all_y**2,
            2.0 * all_x * all_y,
        )
    )
    output = np.full(values.shape, np.nan, dtype=float)
    output[geometry_valid] = all_design @ coefficients
    residual = values[valid] - predicted
    total = np.sum((values[valid] - np.mean(values[valid])) ** 2)
    r_squared = 1.0 - np.sum(residual**2) / total if total > 0 else 1.0
    result = xr.DataArray(
        output,
        dims=surface[metric].dims,
        coords=surface[metric].coords,
        name=f"{metric}_low_order_reconstruction",
        attrs={
            "analysis": "low_order_surface_reconstruction",
            "metric": metric,
            "basis": "1,r,r2,x,y,x2-y2,2xy",
            "coefficients": json.dumps(coefficients.tolist()),
            "rmse": float(np.sqrt(np.mean(residual**2))),
            "r_squared": float(r_squared),
            "status": "experimental diagnostic",
        },
    )
    return result


def synchrony_surface_diagnostics(
    surface: xr.Dataset,
    *,
    metric: str = "delta_s",
    radial_bin_width_km: float = 5.0,
    angular_bin_width_degrees: float = 15.0,
    min_count: int = 3,
) -> xr.Dataset:
    """Return candidate descriptors without declaring a final signature schema."""

    _validate_surface(surface, metric)
    radial = radial_profile(
        surface,
        metric=metric,
        bin_width_km=radial_bin_width_km,
        min_count=min_count,
    )
    angular = angular_profile(
        surface,
        metric=metric,
        bin_width_degrees=angular_bin_width_degrees,
        min_count=min_count,
        radial_detrend_bin_width_km=radial_bin_width_km,
    )
    reconstruction = low_order_surface_reconstruction(surface, metric=metric)
    values = np.asarray(surface[metric].values, dtype=float).ravel()
    distance = np.asarray(surface.distance_km.values, dtype=float).ravel()
    bearing = np.asarray(surface.bearing_degrees.values, dtype=float).ravel()
    x = np.asarray(surface.dx_km.values, dtype=float).ravel()
    y = np.asarray(surface.dy_km.values, dtype=float).ravel()
    valid = np.isfinite(values) & np.isfinite(distance)
    observed = values[valid]
    q25, median, q75 = np.quantile(observed, (0.25, 0.5, 0.75))
    mad = np.median(np.abs(observed - median))

    radial_values = np.asarray(radial.profile.values, dtype=float)
    radial_radius = np.asarray(radial.radius_km.values, dtype=float)
    radial_finite = np.isfinite(radial_values)
    radial_rho = float("nan")
    turns = 0
    characteristic_scale = float("nan")
    scale_status = "no_identifiable_scale"
    if np.count_nonzero(radial_finite) >= 3:
        if np.ptp(radial_values[radial_finite]) > 0:
            radial_rho = float(
                spearmanr(
                    radial_radius[radial_finite], radial_values[radial_finite]
                ).statistic
            )
        smooth = _smooth_profile(radial_values[radial_finite])
        differences = np.diff(smooth)
        tolerance = max(0.01, 0.1 * float(np.nanmax(smooth) - np.nanmin(smooth)))
        signs = np.sign(np.where(np.abs(differences) >= tolerance, differences, 0.0))
        nonzero = signs[signs != 0]
        turns = int(np.count_nonzero(np.diff(nonzero) != 0)) if nonzero.size > 1 else 0
        profile_range = float(np.nanmax(smooth) - np.nanmin(smooth))
        if profile_range > 0.02:
            outer = float(np.median(smooth[-min(3, smooth.size) :]))
            plateau_tolerance = max(0.02, 0.1 * profile_range)
            candidates = [
                index
                for index in range(smooth.size)
                if np.all(np.abs(smooth[index:] - outer) <= plateau_tolerance)
            ]
            if candidates:
                characteristic_scale = float(radial_radius[radial_finite][candidates[0]])
                maximum = float(surface.attrs["observation_radius_km"])
                scale_status = (
                    "right_censored_or_unresolved"
                    if characteristic_scale >= 0.85 * maximum
                    else "candidate_plateau_scale"
                )
            else:
                scale_status = "right_censored_or_unresolved"
            if turns >= 2:
                scale_status = "multiple_candidate_scales"

    directional = valid & np.isfinite(bearing)
    theta = np.deg2rad(bearing[directional])
    directional_values = values[directional]
    directional_distance = distance[directional]
    radial_bin = np.floor(directional_distance / radial_bin_width_km).astype(np.int32)
    residual = directional_values.copy()
    for index in np.unique(radial_bin):
        selected = radial_bin == index
        residual[selected] -= np.median(residual[selected])
    design = np.column_stack(
        (np.ones(theta.size), np.cos(theta), np.sin(theta), np.cos(2 * theta), np.sin(2 * theta))
    )
    coefficients, *_ = np.linalg.lstsq(design, residual, rcond=None)
    predicted = design @ coefficients
    total = float(np.sum((residual - residual.mean()) ** 2))
    directional_r2 = 1.0 - float(np.sum((residual - predicted) ** 2)) / total if total > 0 else 0.0
    first_strength = float(np.hypot(coefficients[1], coefficients[2]))
    second_strength = float(np.hypot(coefficients[3], coefficients[4]))
    first_bearing = float(np.rad2deg(np.arctan2(coefficients[2], coefficients[1])) % 360.0)
    axis_orientation = float(
        (0.5 * np.rad2deg(np.arctan2(coefficients[4], coefficients[3]))) % 180.0
    )

    boundary_contrast, boundary_bearing = _maximum_half_plane_contrast(
        values[directional], x[directional], y[directional]
    )
    result = xr.merge(
        [
            radial.rename({"profile": "radial_profile", "valid_count": "radial_valid_count"}),
            angular.rename({"profile": "angular_profile", "valid_count": "angular_valid_count"}),
        ],
        compat="override",
    )
    result["low_order_reconstruction"] = reconstruction
    scalar_values = {
        "overall_median": median,
        "overall_iqr": q75 - q25,
        "overall_mad": mad,
        "radial_spearman": radial_rho,
        "radial_turn_count": turns,
        "candidate_characteristic_scale_km": characteristic_scale,
        "first_harmonic_strength": first_strength,
        "first_harmonic_bearing_degrees": first_bearing,
        "second_harmonic_strength": second_strength,
        "anisotropy_axis_degrees": axis_orientation,
        "directional_harmonic_r_squared": directional_r2,
        "maximum_half_plane_contrast": boundary_contrast,
        "high_side_bearing_degrees": boundary_bearing,
        "boundary_line_orientation_degrees": (boundary_bearing + 90.0) % 180.0,
        "low_order_reconstruction_rmse": reconstruction.attrs["rmse"],
        "low_order_reconstruction_r_squared": reconstruction.attrs["r_squared"],
    }
    for name, value in scalar_values.items():
        result[name] = xr.DataArray(value)
    result["candidate_characteristic_scale_km"].attrs["status"] = scale_status
    result.attrs.update(
        {
            "analysis": "synchrony_surface_diagnostics",
            "scientific_object": "S_p(dx,dy)",
            "status": "candidate descriptors; no final SynchronySignature schema adopted",
            "characteristic_scale_status": scale_status,
            "observation_limit_warning": (
                "a scale near the observation radius is right-censored or unresolved, never "
                "identified as the observation radius"
            ),
            "three_level_distinction": (
                "within-surface structure; between-center landscape change; geographic change "
                "in surface descriptors"
            ),
        }
    )
    return result


def _maximum_half_plane_contrast(
    values: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[float, float]:
    best_contrast = float("nan")
    best_bearing = float("nan")
    best_score = float("-inf")
    for bearing in np.arange(0.0, 180.0, 5.0):
        radians = np.deg2rad(bearing)
        projection = x * np.sin(radians) + y * np.cos(radians)
        zero_tolerance = max(1e-12, 1e-9 * float(np.nanmax(np.hypot(x, y))))
        positive = projection > zero_tolerance
        negative = projection < -zero_tolerance
        if np.count_nonzero(positive) < 3 or np.count_nonzero(negative) < 3:
            continue
        positive_median = float(np.median(values[positive]))
        negative_median = float(np.median(values[negative]))
        contrast = positive_median - negative_median
        within_error = float(
            np.mean(np.abs(values[positive] - positive_median))
            + np.mean(np.abs(values[negative] - negative_median))
        )
        score = abs(contrast) / max(within_error, 1e-12)
        if score > best_score + 1e-12:
            best_score = score
            best_contrast = contrast
            best_bearing = bearing if contrast >= 0 else (bearing + 180.0) % 360.0
    return abs(best_contrast), best_bearing


def _smooth_profile(values: np.ndarray) -> np.ndarray:
    if values.size < 3:
        return values.copy()
    padded = np.pad(values, (1, 1), mode="edge")
    return np.asarray([np.median(padded[index : index + 3]) for index in range(values.size)])


def _validate_pair_table(pairs: xr.Dataset) -> None:
    if not isinstance(pairs, xr.Dataset) or pairs.attrs.get("analysis") != "local_synchrony_pairs":
        raise TypeError("Expected a Dataset produced by local_synchrony_pairs")
    required = {
        "cold_synchrony",
        "warm_synchrony",
        "delta_s",
        "distance_km",
        "bearing_degrees",
        "dx_km",
        "dy_km",
        "output_mask",
    }
    missing = sorted(required - set(pairs.data_vars))
    if missing:
        raise ValueError(f"Pair table is missing surface geometry variables: {missing!r}")


def _validate_surface(surface: xr.Dataset, metric: str) -> None:
    if not isinstance(surface, xr.Dataset) or surface.attrs.get("analysis") != "local_synchrony_surface":
        raise TypeError("Expected a Dataset produced by local_synchrony_surface")
    if metric not in _METRICS or metric not in surface:
        raise ValueError(f"metric must be one of {_METRICS!r}")


__all__ = [
    "angular_profile",
    "local_synchrony_surface",
    "low_order_surface_reconstruction",
    "radial_profile",
    "synchrony_surface_diagnostics",
]
