#!/usr/bin/env python3
"""Sample real Colorado local surfaces and compare compact representations."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np
import xarray as xr

from cubedynamics.synchrony import (
    local_synchrony_pairs,
    local_synchrony_surface,
    low_order_surface_reconstruction,
    synchrony_surface_diagnostics,
)


SEED = 20260923
OBSERVATION_RADIUS_KM = 100.0
RADIAL_BIN_WIDTH_KM = 5.0
ANGULAR_BIN_WIDTH_DEGREES = 15.0
METRICS = ("cold_synchrony", "warm_synchrony", "delta_s")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/synchrony-stack-phase2"),
    )
    parser.add_argument("--sample-size", type=int, default=64)
    parser.add_argument("--force", action="store_true")
    return parser


def _finite_map(data: xr.DataArray, mask: np.ndarray) -> np.ndarray:
    values = np.asarray(data.squeeze().values, dtype=float)
    return np.where(mask, values, np.nan)


def _ranked_cells(values: np.ndarray, mask: np.ndarray, count: int, high: bool) -> list[tuple[int, int]]:
    valid = np.argwhere(mask & np.isfinite(values))
    order = np.argsort(values[valid[:, 0], valid[:, 1]])
    if high:
        order = order[::-1]
    if valid.size == 0:
        return []
    spaced = np.linspace(0, max(0, order.size - 1), min(count, order.size)).astype(int)
    return [tuple(map(int, valid[order[index]])) for index in spaced]


def _select_sample(
    signature: xr.Dataset,
    change: xr.Dataset,
    sample_size: int,
) -> tuple[list[tuple[int, int]], dict[str, list[str]]]:
    mask = np.asarray(signature.output_mask.values, dtype=bool)
    valid = np.argwhere(mask)
    rng = np.random.default_rng(SEED)
    selected: dict[tuple[int, int], set[str]] = {}

    def add(cells: list[tuple[int, int]] | np.ndarray, label: str) -> None:
        for cell in cells:
            key = tuple(map(int, cell))
            selected.setdefault(key, set()).add(label)

    random_count = min(20, sample_size)
    add(valid[rng.choice(valid.shape[0], size=random_count, replace=False)], "random")

    # Geographic coverage: one random valid cell from each occupied 4 x 4 grid stratum.
    y_edges = np.linspace(0, mask.shape[0], 5).astype(int)
    x_edges = np.linspace(0, mask.shape[1], 5).astype(int)
    for y0, y1 in zip(y_edges[:-1], y_edges[1:]):
        for x0, x1 in zip(x_edges[:-1], x_edges[1:]):
            cells = np.argwhere(mask[y0:y1, x0:x1])
            if cells.size:
                cell = cells[rng.integers(cells.shape[0])] + np.array([y0, x0])
                add([cell], "geographic_stratum")

    iqr = _finite_map(signature.delta_iqr.sel(radius_km=100), mask)
    eta = _finite_map(signature.delta_directional_eta_squared.sel(radius_km=100), mask)
    gradient_values = np.asarray(change.gradient_vector_rmse.values, dtype=float)
    gradient = np.max(np.where(np.isfinite(gradient_values), gradient_values, -np.inf), axis=0)
    gradient[gradient == -np.inf] = np.nan
    for values, low_label, high_label in (
        (iqr, "low_heterogeneity", "high_heterogeneity"),
        (eta, "low_directional_structure", "high_directional_structure"),
        (gradient, "low_landscape_gradient", "high_landscape_gradient"),
    ):
        add(_ranked_cells(values, mask, 4, False), low_label)
        add(_ranked_cells(values, mask, 4, True), high_label)

    # State-border sample: cells with at least one four-neighbor outside the output mask.
    padded = np.pad(mask, 1, constant_values=False)
    interior = (
        padded[1:-1, 1:-1]
        & padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )
    border = np.argwhere(mask & ~interior)
    if border.size:
        add(border[np.linspace(0, border.shape[0] - 1, 6).astype(int)], "state_border")
    deep_interior = np.argwhere(interior)
    if deep_interior.size:
        add(
            deep_interior[rng.choice(deep_interior.shape[0], size=min(6, deep_interior.shape[0]), replace=False)],
            "interior",
        )

    # The production tile shape is 32 x 32. Choose cells immediately around seams.
    seam = np.argwhere(
        mask
        & (
            np.isin(np.arange(mask.shape[0])[:, None] % 32, (0, 31))
            | np.isin(np.arange(mask.shape[1])[None, :] % 32, (0, 31))
        )
    )
    if seam.size:
        add(seam[np.linspace(0, seam.shape[0] - 1, 8).astype(int)], "tile_boundary")

    # Fill deterministically if strata overlapped heavily, or trim random-only cells last.
    remaining = [tuple(map(int, cell)) for cell in valid if tuple(map(int, cell)) not in selected]
    rng.shuffle(remaining)
    for cell in remaining:
        if len(selected) >= sample_size:
            break
        selected[cell] = {"random_fill"}
    if len(selected) > sample_size:
        priority = sorted(
            selected,
            key=lambda cell: (len(selected[cell]), "random" in selected[cell], cell),
            reverse=True,
        )
        selected = {cell: selected[cell] for cell in priority[:sample_size]}
    cells = sorted(selected)
    strata = {f"{y},{x}": sorted(selected[(y, x)]) for y, x in cells}
    return cells, strata


def _subset_for_focal(cube: xr.Dataset, yi: int, xi: int) -> tuple[xr.Dataset, int, int]:
    latitude = float(cube.y.values[yi])
    longitude = float(cube.x.values[xi])
    lat_margin = OBSERVATION_RADIUS_KM / 110.5 + 0.08
    lon_margin = OBSERVATION_RADIUS_KM / (111.0 * np.cos(np.deg2rad(latitude))) + 0.08
    y_values = np.asarray(cube.y.values, dtype=float)
    x_values = np.asarray(cube.x.values, dtype=float)
    y_indices = np.flatnonzero(np.abs(y_values - latitude) <= lat_margin)
    x_indices = np.flatnonzero(np.abs(x_values - longitude) <= lon_margin)
    y0, y1 = int(y_indices.min()), int(y_indices.max()) + 1
    x0, x1 = int(x_indices.min()), int(x_indices.max()) + 1
    return cube.isel(y=slice(y0, y1), x=slice(x0, x1)), yi - y0, xi - x0


def _write_surface(
    cube: xr.Dataset,
    yi: int,
    xi: int,
    path: Path,
) -> xr.Dataset:
    subset, local_y, local_x = _subset_for_focal(cube, yi, xi)
    mask = xr.zeros_like(subset.tmin.isel(time=0), dtype=bool)
    mask.values[local_y, local_x] = True
    pairs = local_synchrony_pairs(
        subset,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=OBSERVATION_RADIUS_KM,
        window_days=90,
        min_t=10,
    )
    surface = local_synchrony_surface(pairs, focal_y_index=local_y, focal_x_index=local_x)
    surface.attrs.update(
        {
            "global_focal_y_index": int(yi),
            "global_focal_x_index": int(xi),
            "sampling_seed": SEED,
        }
    )
    temporary = path.with_suffix(".partial.nc")
    surface.to_netcdf(temporary)
    temporary.replace(path)
    return surface


def _align_surfaces(surfaces: list[xr.Dataset], metric: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    min_y = min(int(surface.offset_y_index.min()) for surface in surfaces)
    max_y = max(int(surface.offset_y_index.max()) for surface in surfaces)
    min_x = min(int(surface.offset_x_index.min()) for surface in surfaces)
    max_x = max(int(surface.offset_x_index.max()) for surface in surfaces)
    y = np.arange(min_y, max_y + 1)
    x = np.arange(min_x, max_x + 1)
    matrix = np.stack(
        [surface[metric].reindex(offset_y_index=y, offset_x_index=x).values for surface in surfaces]
    )
    return matrix, y, x


def _radial_prediction(surface: xr.Dataset, values: np.ndarray, width: float = 5.0) -> np.ndarray:
    distance = np.asarray(surface.distance_km.values, dtype=float)
    valid = np.isfinite(values) & np.isfinite(distance)
    prediction = np.full(values.shape, np.nan)
    bins = np.floor(np.where(np.isfinite(distance), distance, 0.0) / width).astype(np.int32)
    for index in np.unique(bins[valid]):
        selected = valid & (bins == index)
        prediction[np.isfinite(distance) & (bins == index)] = np.median(values[selected])
    return prediction


def _nested_prediction(surface: xr.Dataset, values: np.ndarray) -> np.ndarray:
    distance = np.asarray(surface.distance_km.values, dtype=float)
    valid = np.isfinite(values) & np.isfinite(distance)
    prediction = np.full(values.shape, np.nan)
    for radius in (25.0, 50.0, 75.0, 100.0):
        support = valid & (distance <= radius)
        ring = np.isfinite(distance) & (distance > radius - 25.0) & (distance <= radius)
        if np.any(support):
            prediction[ring] = np.median(values[support])
    return prediction


def _radial_angular_prediction(surface: xr.Dataset, values: np.ndarray) -> np.ndarray:
    radial = _radial_prediction(surface, values)
    bearing = np.asarray(surface.bearing_degrees.values, dtype=float)
    valid = np.isfinite(values) & np.isfinite(radial) & np.isfinite(bearing)
    residual = values - radial
    sector = np.floor(np.where(np.isfinite(bearing), bearing, 0.0) / ANGULAR_BIN_WIDTH_DEGREES).astype(int)
    prediction = radial.copy()
    for index in np.unique(sector[valid]):
        selected = valid & (sector == index)
        target = np.isfinite(prediction) & np.isfinite(bearing) & (sector == index)
        prediction[target] += np.median(residual[selected])
    return prediction


def _rmse(values: np.ndarray, prediction: np.ndarray) -> tuple[float, float]:
    valid = np.isfinite(values) & np.isfinite(prediction)
    error = float(np.sqrt(np.mean((values[valid] - prediction[valid]) ** 2)))
    scale = float(np.std(values[valid]))
    return error, error / scale if scale > 0 else 0.0


def _representation_rows(surfaces: list[xr.Dataset], metric: str) -> list[dict[str, float | str | int]]:
    methods = {
        "median_iqr": (2, lambda s, v: np.full(v.shape, np.nanmedian(v))),
        "nested_25_50_75_100": (8, _nested_prediction),
        "fine_radial_profile": (20, _radial_prediction),
        "radial_plus_directional": (43, _radial_angular_prediction),
        "low_order_2d_basis": (
            7,
            lambda s, v: low_order_surface_reconstruction(s, metric=metric).values,
        ),
    }
    rows: list[dict[str, float | str | int]] = []
    rng = np.random.default_rng(SEED + 100 + METRICS.index(metric))
    for name, (parameters, function) in methods.items():
        normalized = []
        errors = []
        missing_normalized = []
        started = time.perf_counter()
        for surface in surfaces:
            values = np.asarray(surface[metric].values, dtype=float)
            prediction = function(surface, values)
            error, relative = _rmse(values, prediction)
            errors.append(error)
            normalized.append(relative)
            valid_cells = np.argwhere(np.isfinite(values))
            withheld = valid_cells[
                rng.choice(valid_cells.shape[0], size=max(1, valid_cells.shape[0] // 10), replace=False)
            ]
            training_values = values.copy()
            training_values[withheld[:, 0], withheld[:, 1]] = np.nan
            if name == "low_order_2d_basis":
                training_surface = surface.copy(deep=True)
                training_surface[metric].values[:] = training_values
                missing_prediction = low_order_surface_reconstruction(
                    training_surface, metric=metric
                ).values
            else:
                missing_prediction = function(surface, training_values)
            held_out_values = np.full(values.shape, np.nan)
            held_out_values[withheld[:, 0], withheld[:, 1]] = values[
                withheld[:, 0], withheld[:, 1]
            ]
            _, missing_relative = _rmse(held_out_values, missing_prediction)
            missing_normalized.append(missing_relative)
        rows.append(
            {
                "representation": name,
                "per_pixel_parameters": parameters,
                "median_rmse": float(np.median(errors)),
                "median_normalized_rmse": float(np.median(normalized)),
                "p90_normalized_rmse": float(np.quantile(normalized, 0.9)),
                "missing_10pct_median_normalized_rmse": float(
                    np.median(missing_normalized)
                ),
                "seconds_for_sample": float(time.perf_counter() - started),
            }
        )
    return rows


def _pca_experiment(
    surfaces: list[xr.Dataset],
    metric: str,
) -> tuple[dict[str, object], np.ndarray, np.ndarray, np.ndarray]:
    matrix3d, y, x = _align_surfaces(surfaces, metric)
    complete = np.all(np.isfinite(matrix3d), axis=0)
    matrix = matrix3d[:, complete]
    rng = np.random.default_rng(SEED + METRICS.index(metric))
    order = rng.permutation(matrix.shape[0])
    split = max(2, int(round(matrix.shape[0] * 0.75)))
    train_index, test_index = order[:split], order[split:]
    mean = matrix[train_index].mean(axis=0)
    centered = matrix[train_index] - mean
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    variance = singular**2
    explained = variance / variance.sum()
    cumulative = np.cumsum(explained)
    test = matrix[test_index]
    test_scale = np.std(test, axis=1)
    results = []
    for components in range(1, min(12, vt.shape[0]) + 1):
        basis = vt[:components]
        scores = (test - mean) @ basis.T
        reconstructed = mean + scores @ basis
        rmse = np.sqrt(np.mean((test - reconstructed) ** 2, axis=1))
        results.append(
            {
                "components": components,
                "training_cumulative_variance": float(cumulative[components - 1]),
                "held_out_median_rmse": float(np.median(rmse)),
                "held_out_median_normalized_rmse": float(np.median(rmse / test_scale)),
                "held_out_p90_normalized_rmse": float(np.quantile(rmse / test_scale, 0.9)),
            }
        )
    chosen = next(
        (row["components"] for row in results if row["held_out_median_normalized_rmse"] <= 0.60),
        min(8, len(results)),
    )
    basis = vt[:chosen]
    missing_errors = []
    for row_index, observed in enumerate(test):
        local_rng = np.random.default_rng(SEED + 500 + row_index + METRICS.index(metric) * 100)
        withheld = local_rng.choice(
            observed.size, size=max(1, observed.size // 10), replace=False
        )
        retained = np.ones(observed.size, dtype=bool)
        retained[withheld] = False
        scores, *_ = np.linalg.lstsq(
            basis[:, retained].T,
            observed[retained] - mean[retained],
            rcond=None,
        )
        prediction = mean + scores @ basis
        error = float(np.sqrt(np.mean((observed[withheld] - prediction[withheld]) ** 2)))
        missing_errors.append(error / float(np.std(observed[withheld])))

    stability: dict[str, float] = {}
    split_order = np.random.default_rng(SEED + 900 + METRICS.index(metric)).permutation(
        train_index
    )
    halves = np.array_split(split_order, 2)
    half_bases = []
    for half in halves:
        half_centered = matrix[half] - matrix[half].mean(axis=0)
        _, _, half_vt = np.linalg.svd(half_centered, full_matrices=False)
        half_bases.append(half_vt)
    for components in (3, 5, 8):
        if components <= min(half_bases[0].shape[0], half_bases[1].shape[0]):
            principal_cosines = np.linalg.svd(
                half_bases[0][:components] @ half_bases[1][:components].T,
                compute_uv=False,
            )
            stability[str(components)] = float(np.mean(principal_cosines**2))

    yy, xx = np.meshgrid(y, x, indexing="ij")
    prototypes = {
        "radial": np.hypot(xx, yy),
        "east_west_gradient": xx.astype(float),
        "north_south_gradient": yy.astype(float),
        "axis_east_west_vs_north_south": (xx**2 - yy**2).astype(float),
        "diagonal_axis": (2 * xx * yy).astype(float),
    }
    component_screens = []
    for index in range(min(6, vt.shape[0])):
        correlations = {
            name: float(np.corrcoef(vt[index], values[complete])[0, 1])
            for name, values in prototypes.items()
        }
        strongest = max(correlations, key=lambda name: abs(correlations[name]))
        component_screens.append(
            {
                "component": index + 1,
                "strongest_prototype": strongest,
                "correlation": correlations[strongest],
                "all_correlations": correlations,
                "status": "descriptive correlation screen, not assigned interpretation",
            }
        )
    component_images = np.full((min(6, vt.shape[0]), y.size, x.size), np.nan)
    for index in range(component_images.shape[0]):
        component_images[index][complete] = vt[index]
    mean_image = np.full((y.size, x.size), np.nan)
    mean_image[complete] = mean
    return (
        {
            "metric": metric,
            "sample_count": int(matrix.shape[0]),
            "train_count": int(train_index.size),
            "test_count": int(test_index.size),
            "common_cell_count": int(matrix.shape[1]),
            "chosen_component_count": int(chosen),
            "selection_rule": "smallest k with held-out median normalized RMSE <= 0.60, else k=8",
            "missing_10pct_median_normalized_rmse": float(np.median(missing_errors)),
            "split_half_subspace_stability": stability,
            "component_correlation_screens": component_screens,
            "results": results,
            "train_indices": train_index.tolist(),
            "test_indices": test_index.tolist(),
        },
        component_images,
        mean_image,
        complete,
    )


def _surface_record(surface: xr.Dataset, strata: list[str]) -> dict[str, object]:
    diagnostics = synchrony_surface_diagnostics(
        surface,
        metric="delta_s",
        radial_bin_width_km=RADIAL_BIN_WIDTH_KM,
        angular_bin_width_degrees=ANGULAR_BIN_WIDTH_DEGREES,
        min_count=3,
    )
    names = (
        "overall_median",
        "overall_iqr",
        "overall_mad",
        "radial_spearman",
        "radial_turn_count",
        "candidate_characteristic_scale_km",
        "first_harmonic_strength",
        "first_harmonic_bearing_degrees",
        "second_harmonic_strength",
        "anisotropy_axis_degrees",
        "directional_harmonic_r_squared",
        "maximum_half_plane_contrast",
        "high_side_bearing_degrees",
        "low_order_reconstruction_rmse",
        "low_order_reconstruction_r_squared",
    )
    return {
        "global_y_index": int(surface.attrs["global_focal_y_index"]),
        "global_x_index": int(surface.attrs["global_focal_x_index"]),
        "latitude": float(surface.attrs["focal_y"]),
        "longitude": float(surface.attrs["focal_x"]),
        "strata": strata,
        "valid_pair_count": int(np.count_nonzero(np.isfinite(surface.delta_s.values))),
        "characteristic_scale_status": diagnostics.attrs["characteristic_scale_status"],
        "diagnostics": {name: float(diagnostics[name].item()) for name in names},
    }


def _decision_status(rows: list[dict[str, object]], pca: dict[str, object]) -> list[dict[str, object]]:
    by_name = {str(row["representation"]): row for row in rows}
    pca_row = pca["results"][int(pca["chosen_component_count"]) - 1]
    return [
        {
            **by_name["median_iqr"],
            "status": "KEEP AS DIAGNOSTIC",
            "interpretation": "magnitude and heterogeneity only; no geometry",
        },
        {
            **by_name["nested_25_50_75_100"],
            "status": "KEEP AS DIAGNOSTIC",
            "interpretation": "Phase 1 compatibility baseline; coarse radial compression",
        },
        {
            **by_name["fine_radial_profile"],
            "status": "KEEP",
            "interpretation": "continuous radial projection; preserves nonmonotonic structure",
        },
        {
            **by_name["radial_plus_directional"],
            "status": "KEEP",
            "interpretation": "separates distance and direction with transparent support",
        },
        {
            **by_name["low_order_2d_basis"],
            "status": "EXPERIMENTAL",
            "interpretation": "interpretable but residual complexity must remain visible",
        },
        {
            "representation": "empirical_pca_svd",
            "per_pixel_parameters": int(pca["chosen_component_count"]),
            "median_rmse": float(pca_row["held_out_median_rmse"]),
            "median_normalized_rmse": float(pca_row["held_out_median_normalized_rmse"]),
            "p90_normalized_rmse": float(pca_row["held_out_p90_normalized_rmse"]),
            "missing_10pct_median_normalized_rmse": float(
                pca["missing_10pct_median_normalized_rmse"]
            ),
            "status": "EXPERIMENTAL",
            "interpretation": "best low-dimensional test requires temporal and regional stability checks",
        },
    ]


def main() -> None:
    args = _parser().parse_args()
    artifact_dir = args.artifact_dir.resolve()
    sample_dir = artifact_dir / "surface_samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    with xr.open_dataset(artifact_dir / "prism_colorado_plus_100km_20231101_20240130.nc") as source:
        cube = source.load()
    # This artifact predates the loader metadata repair; the saved coordinate
    # values are the original PRISM latitude/longitude grid.
    cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    with xr.open_dataset(artifact_dir / "colorado_synchrony_signature.nc") as source:
        signature = source.load()
    with xr.open_dataset(artifact_dir / "colorado_landscape_change.nc") as source:
        change = source.load()
    cells, strata = _select_sample(signature, change, args.sample_size)
    surfaces: list[xr.Dataset] = []
    records: list[dict[str, object]] = []
    started = time.perf_counter()
    for number, (yi, xi) in enumerate(cells, start=1):
        path = sample_dir / f"surface_y{yi:04d}_x{xi:04d}.nc"
        if path.exists() and not args.force:
            with xr.open_dataset(path) as source:
                surface = source.load()
        else:
            surface = _write_surface(cube, yi, xi, path)
        surfaces.append(surface)
        records.append(_surface_record(surface, strata[f"{yi},{xi}"]))
        print(f"[{number:02d}/{len(cells):02d}] y={yi} x={xi} pairs={records[-1]['valid_pair_count']}")

    representation: dict[str, list[dict[str, object]]] = {}
    pca_results: dict[str, dict[str, object]] = {}
    basis_arrays: dict[str, np.ndarray] = {}
    basis_coordinates: dict[str, np.ndarray] = {}
    for metric in METRICS:
        representation[metric] = _representation_rows(surfaces, metric)
        pca, components, mean, complete = _pca_experiment(surfaces, metric)
        pca_results[metric] = pca
        basis_arrays[f"{metric}_components"] = components
        basis_arrays[f"{metric}_mean"] = mean
        basis_arrays[f"{metric}_complete_mask"] = complete
    _, common_y, common_x = _align_surfaces(surfaces, "delta_s")
    basis_coordinates["offset_y_index"] = common_y
    basis_coordinates["offset_x_index"] = common_x
    np.savez_compressed(sample_dir / "empirical_surface_basis.npz", **basis_arrays, **basis_coordinates)

    statuses = [record["characteristic_scale_status"] for record in records]
    summary = {
        "analysis": "phase2_revised_local_surface_experiment",
        "scientific_object": "S_p(dx,dy)",
        "source": signature.attrs.get("source", "unknown"),
        "date_range": signature.attrs.get("date_range", "2023-11-01/2024-01-30"),
        "observation_radius_km": OBSERVATION_RADIUS_KM,
        "observation_radius_definition": "maximum observed pair distance; not an inferred scale",
        "sampling_seed": SEED,
        "sample_size": len(records),
        "sample_selection": (
            "deterministic random plus geographic, heterogeneity, landscape-gradient, directional, "
            "interior, state-border, and tile-boundary strata"
        ),
        "surfaces": records,
        "characteristic_scale_status_counts": {
            status: statuses.count(status) for status in sorted(set(statuses))
        },
        "representation_results": representation,
        "pca_svd": pca_results,
        "decision_table": _decision_status(representation["delta_s"], pca_results["delta_s"]),
        "runtime_seconds": float(time.perf_counter() - started),
        "storage": {
            "sample_surface_bytes": int(sum(path.stat().st_size for path in sample_dir.glob("surface_*.nc"))),
            "basis_bytes": int((sample_dir / "empirical_surface_basis.npz").stat().st_size),
        },
        "limitations": [
            "one 90-day observed PRISM window",
            "Colorado sample only; no regime classification",
            "PCA/SVD basis is experimental and not accepted for temporal or CONUS production",
            "100 km is an observation limit; unresolved scales are right-censored",
        ],
    }
    encoded = json.dumps(summary, indent=2, sort_keys=True)
    (artifact_dir / "surface_representation_report.json").write_text(encoded + "\n")
    summary_hash = sha256(encoded.encode()).hexdigest()
    manifest = {
        "report": "surface_representation_report.json",
        "sha256": summary_hash,
        "sample_count": len(records),
        "surface_directory": "surface_samples",
    }
    (artifact_dir / "surface_representation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
