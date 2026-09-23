"""Run the Phase 2 Colorado synchrony-signature demonstration.

The reusable science lives in ``cubedynamics.synchrony`` and ``verbs``. This
file only acquires one bounded PRISM window, runs the engineering gate, and
orchestrates restartable statewide output tiles.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import resource
import time

import numpy as np
import requests
import xarray as xr
from shapely.geometry import mapping, shape

import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.serialization import sanitize_netcdf_attrs
from cubedynamics.stats.tails import one_tail_spearman
from cubedynamics.synchrony import (
    expand_spatial_domain,
    local_synchrony_pairs,
    local_synchrony_surface,
    spatial_output_mask,
    synchrony_signature,
    tiled_landscape_change_signature,
    tiled_synchrony_signature,
)


START = "2023-11-01"
END = "2024-01-30"
RADII_KM = (25.0, 50.0, 75.0, 100.0)
WINDOW_DAYS = 90
MIN_T = 10
TILE_SHAPE = (32, 32)
COLORADO_FIPS = "08"
COLORADO_BOUNDARY_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/State_County/MapServer/2/query"
)


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.json")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _atomic_netcdf(dataset: xr.Dataset, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.nc")
    clean = sanitize_netcdf_attrs(dataset, copy=True)
    for name in clean.variables:
        clean[name].encoding = {}
    clean.to_netcdf(temporary, engine="scipy")
    temporary.replace(path)


def _colorado_geometry(output_dir: Path):
    target = output_dir / "colorado_boundary.geojson"
    if target.exists():
        document = json.loads(target.read_text(encoding="utf-8"))
    else:
        response = requests.get(
            COLORADO_BOUNDARY_URL,
            params={
                "where": f"STATE='{COLORADO_FIPS}'",
                "outFields": "NAME,STATE,GEOID",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "geojson",
            },
            timeout=60,
        )
        response.raise_for_status()
        document = response.json()
        if len(document.get("features", [])) != 1:
            raise RuntimeError("Census TIGERweb did not return one Colorado feature")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return shape(document["features"][0]["geometry"])


def _dask_task_count(dataset: xr.Dataset) -> int:
    graph = dataset.__dask_graph__()
    return 0 if graph is None else len(graph)


@contextmanager
def _performance_record():
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record = {}
    yield record
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes; Linux reports KiB.
    peak_bytes = int(after if after > 10_000_000 else after * 1024)
    before_bytes = int(before if before > 10_000_000 else before * 1024)
    record.update(
        wall_seconds=time.perf_counter() - wall_start,
        cpu_seconds=time.process_time() - cpu_start,
        process_peak_rss_bytes=peak_bytes,
        process_peak_rss_increase_bytes=max(0, peak_bytes - before_bytes),
    )


def _load_or_stream_prism(path: Path, bbox: tuple[float, float, float, float]):
    if path.exists():
        with xr.open_dataset(path, engine="scipy") as saved:
            cube = saved.load()
        if bool(cube.attrs.get("is_synthetic", 1)):
            raise RuntimeError("Refusing a synthetic PRISM checkpoint")
        cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
        cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
        return cube, {"resumed_input_snapshot": True, "dask_task_count": 0}
    lazy = cd.load_prism_cube(
        variables=["tmin", "tmax"],
        bbox=bbox,
        start=START,
        end=END,
        freq="D",
        chunks={"time": 31, "y": 64, "x": 64},
        prefer_streaming=True,
        show_progress=False,
        allow_synthetic=False,
    )
    if bool(lazy.attrs.get("is_synthetic", 1)):
        raise RuntimeError("Refusing to run Phase 2 without real PRISM observations")
    task_count = _dask_task_count(lazy)
    cube = lazy.compute(scheduler="threads", num_workers=4)
    cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    _atomic_netcdf(cube, path)
    return cube, {"resumed_input_snapshot": False, "dask_task_count": task_count}


def _centered_gate_cube(cube: xr.Dataset) -> xr.Dataset:
    if cube.sizes["y"] < 100 or cube.sizes["x"] < 100:
        raise RuntimeError(f"PRISM gate needs at least 100x100 cells; got {dict(cube.sizes)}")
    y0 = (cube.sizes["y"] - 100) // 2
    x0 = (cube.sizes["x"] - 100) // 2
    return cube.isel(y=slice(y0, y0 + 100), x=slice(x0, x0 + 100))


def run_gate(cube: xr.Dataset, output_dir: Path) -> dict[str, object]:
    gate = _centered_gate_cube(cube)
    mask_values = np.zeros((100, 100), dtype=bool)
    mask_values[25:75, 25:75] = True
    mask = xr.DataArray(mask_values, dims=("y", "x"), coords={"y": gate.y, "x": gate.x})
    with _performance_record() as performance:
        pairs = (
            pipe(gate)
            | v.local_synchrony_pairs(
                lower_var="tmin",
                upper_var="tmax",
                output_mask=mask,
                max_radius_km=100,
                window_days=WINDOW_DAYS,
                window_end=END,
                min_t=MIN_T,
                pair_batch_size=8192,
            )
        ).unwrap()
        untiled = (pipe(pairs) | v.synchrony_signature(radii_km=RADII_KM)).unwrap()
        tiled = tiled_synchrony_signature(
            gate,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=mask,
            radii_km=RADII_KM,
            tile_shape=(25, 25),
            window_days=WINDOW_DAYS,
            window_end=END,
            min_t=MIN_T,
            pair_batch_size=8192,
            checkpoint_dir=output_dir / "gate_tiles",
        )
    comparison = {}
    for name in untiled.data_vars:
        if name == "output_mask":
            continue
        left = np.asarray(untiled[name].where(mask).values, dtype=float)
        right = np.asarray(tiled[name].where(mask).values, dtype=float)
        difference = np.abs(left - right)
        comparison[name] = float(np.nanmax(difference)) if np.isfinite(difference).any() else 0.0
    if max(comparison.values(), default=0.0) > 1e-12:
        raise RuntimeError(f"100x100 gate failed halo equivalence: {comparison}")
    resumed = tiled_synchrony_signature(
        gate,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        radii_km=RADII_KM,
        tile_shape=(25, 25),
        window_days=WINDOW_DAYS,
        window_end=END,
        min_t=MIN_T,
        pair_batch_size=8192,
        checkpoint_dir=output_dir / "gate_tiles",
    )
    if resumed.attrs["resumed_tile_count"] != resumed.attrs["tile_count"]:
        raise RuntimeError("100x100 gate failed checkpoint restart")
    _atomic_netcdf(tiled, output_dir / "gate_signature.nc")
    report = {
        "status": "PASS",
        "real_data": True,
        "computation_shape": [100, 100],
        "output_shape": [50, 50],
        "output_pixels": int(mask.sum()),
        "unique_pairs_untiled": int(pairs.attrs["unique_pair_count"]),
        "nonself_pairs_untiled": int(pairs.attrs["nonself_pair_count"]),
        "pair_calculations_tiled": int(tiled.attrs["pair_calculation_count_with_tile_recompute"]),
        "tile_count": int(tiled.attrs["tile_count"]),
        "checkpoint_resume_tiles": int(resumed.attrs["resumed_tile_count"]),
        "max_absolute_errors": comparison,
        "pair_kernel_seconds": float(pairs.attrs["pair_kernel_seconds"]),
        "pair_calculations_per_second": float(pairs.attrs["pairs_per_kernel_second"]),
        "output_bytes": int((output_dir / "gate_signature.nc").stat().st_size),
        **performance,
    }
    _atomic_json(output_dir / "gate_report.json", report)
    run_surface_gate(cube, output_dir)
    return report


def run_surface_gate(cube: xr.Dataset, output_dir: Path) -> dict[str, object]:
    """Validate complete local surfaces inside the real 100 x 100 gate."""

    gate = _centered_gate_cube(cube)
    focal_cells = ((49, 49), (49, 50), (50, 50))
    mask = xr.zeros_like(gate.tmin.isel(time=0), dtype=bool)
    for yi, xi in focal_cells:
        mask.values[yi, xi] = True
    kwargs = dict(
        lower_var="tmin",
        upper_var="tmax",
        output_mask=mask,
        max_radius_km=100,
        window_days=WINDOW_DAYS,
        window_end=END,
        min_t=MIN_T,
        pair_batch_size=4096,
    )
    eager = local_synchrony_pairs(gate, **kwargs)
    chunked = local_synchrony_pairs(gate.chunk({"time": 31, "y": 25, "x": 25}), **kwargs)
    eager_surfaces = {
        cell: local_synchrony_surface(eager, focal_y_index=cell[0], focal_x_index=cell[1])
        for cell in focal_cells
    }
    chunked_surfaces = {
        cell: local_synchrony_surface(chunked, focal_y_index=cell[0], focal_x_index=cell[1])
        for cell in focal_cells
    }
    chunk_errors = {}
    for metric in ("cold_synchrony", "warm_synchrony", "delta_s", "dx_km", "dy_km"):
        errors = []
        for cell in focal_cells:
            difference = np.abs(
                eager_surfaces[cell][metric].values - chunked_surfaces[cell][metric].values
            )
            errors.append(float(np.nanmax(difference)))
        chunk_errors[metric] = max(errors)

    # Independent Phase 1 kernel values on a deterministic subset of one surface.
    focal = focal_cells[-1]
    focal_index = focal[0] * gate.sizes["x"] + focal[1]
    source = np.asarray(eager.source_index.values, dtype=int)
    target = np.asarray(eager.target_index.values, dtype=int)
    incident = np.flatnonzero((source == focal_index) | (target == focal_index))
    checks = incident[np.linspace(0, incident.size - 1, 25).astype(int)]
    reference_errors = {"cold_synchrony": 0.0, "warm_synchrony": 0.0, "delta_s": 0.0}
    tmin = np.asarray(gate.tmin.values, dtype=float).reshape(gate.sizes["time"], -1).T
    tmax = np.asarray(gate.tmax.values, dtype=float).reshape(gate.sizes["time"], -1).T
    for pair_index in checks:
        left, right = source[pair_index], target[pair_index]
        cold, _ = one_tail_spearman(tmin[left], tmin[right], tail="lower", min_t=MIN_T)
        warm, _ = one_tail_spearman(tmax[left], tmax[right], tail="upper", min_t=MIN_T)
        expected = {"cold_synchrony": cold, "warm_synchrony": warm, "delta_s": cold - warm}
        for metric, value in expected.items():
            reference_errors[metric] = max(
                reference_errors[metric], abs(float(eager[metric].values[pair_index]) - value)
            )

    west = eager_surfaces[(50, 50)]
    north_west = eager_surfaces[(49, 50)]
    forward = west.bearing_degrees.sel(offset_y_index=-1, offset_x_index=0).item()
    reverse = north_west.bearing_degrees.sel(offset_y_index=1, offset_x_index=0).item()
    reversal_error = abs(((forward + 180.0) % 360.0) - reverse)
    displacement_error = max(
        abs(
            west.dx_km.sel(offset_y_index=-1, offset_x_index=0).item()
            + north_west.dx_km.sel(offset_y_index=1, offset_x_index=0).item()
        ),
        abs(
            west.dy_km.sel(offset_y_index=-1, offset_x_index=0).item()
            + north_west.dy_km.sel(offset_y_index=1, offset_x_index=0).item()
        ),
    )

    # Recompute one seam focal from its own full coordinate halo.
    latitude = float(gate.y.values[focal[0]])
    longitude = float(gate.x.values[focal[1]])
    y_selection = np.flatnonzero(np.abs(gate.y.values - latitude) <= 100 / 110.5 + 0.08)
    x_selection = np.flatnonzero(
        np.abs(gate.x.values - longitude)
        <= 100 / (111.0 * np.cos(np.deg2rad(latitude))) + 0.08
    )
    y0, y1 = int(y_selection.min()), int(y_selection.max()) + 1
    x0, x1 = int(x_selection.min()), int(x_selection.max()) + 1
    halo = gate.isel(y=slice(y0, y1), x=slice(x0, x1))
    halo_mask = xr.zeros_like(halo.tmin.isel(time=0), dtype=bool)
    halo_mask.values[focal[0] - y0, focal[1] - x0] = True
    halo_pairs = local_synchrony_pairs(
        halo,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=halo_mask,
        max_radius_km=100,
        window_days=WINDOW_DAYS,
        window_end=END,
        min_t=MIN_T,
    )
    halo_surface = local_synchrony_surface(
        halo_pairs,
        focal_y_index=focal[0] - y0,
        focal_x_index=focal[1] - x0,
    )
    seam_errors = {}
    for metric in ("cold_synchrony", "warm_synchrony", "delta_s", "distance_km"):
        left, right = xr.align(eager_surfaces[focal][metric], halo_surface[metric], join="exact")
        seam_errors[metric] = float(np.nanmax(np.abs(left.values - right.values)))

    maximum_error = max(
        [*chunk_errors.values(), *reference_errors.values(), reversal_error, displacement_error, *seam_errors.values()]
    )
    report = {
        "status": "PASS" if maximum_error <= 1e-12 else "FAIL",
        "real_data": True,
        "computation_shape": [100, 100],
        "focal_surface_count": len(focal_cells),
        "phase1_reference_pair_checks": len(checks),
        "chunking_max_absolute_errors": chunk_errors,
        "phase1_kernel_max_absolute_errors": reference_errors,
        "endpoint_bearing_reversal_error_degrees": float(reversal_error),
        "endpoint_displacement_reversal_error_km": float(displacement_error),
        "tile_halo_surface_max_absolute_errors": seam_errors,
        "relative_index_coordinates_verified": bool(
            np.all(eager.dx_index.values == eager.target_x_index.values - eager.source_x_index.values)
            and np.all(eager.dy_index.values == eager.target_y_index.values - eager.source_y_index.values)
        ),
        "maximum_absolute_error": float(maximum_error),
        "observation_radius_km": 100.0,
        "observation_radius_definition": "maximum observed support; not an inferred scale",
    }
    if report["status"] != "PASS":
        raise RuntimeError(f"100x100 surface gate failed: {report}")
    _atomic_json(output_dir / "surface_gate_report.json", report)
    return report


def _select_audit_pixels(signature: xr.Dataset) -> list[dict[str, object]]:
    mask = np.asarray(signature.output_mask.values, dtype=bool)
    delta_iqr = signature.delta_iqr.sel(radius_km=100).values[0]
    sensitivity = np.abs(signature.delta_median_increment.sel(radius_km=100).values[0])
    candidates = {
        "low_delta_iqr": np.where(mask, delta_iqr, np.nan),
        "high_delta_iqr": np.where(mask, delta_iqr, np.nan),
        "low_radius_sensitivity": np.where(mask, sensitivity, np.nan),
        "high_radius_sensitivity": np.where(mask, sensitivity, np.nan),
    }
    selectors = {
        "low_delta_iqr": np.nanargmin,
        "high_delta_iqr": np.nanargmax,
        "low_radius_sensitivity": np.nanargmin,
        "high_radius_sensitivity": np.nanargmax,
    }
    records = []
    for label, values in candidates.items():
        index = int(selectors[label](values))
        yi, xi = np.unravel_index(index, values.shape)
        records.append(
            {
                "label": label,
                "y_index": int(yi),
                "x_index": int(xi),
                "latitude": float(signature.y.values[yi]),
                "longitude": float(signature.x.values[xi]),
                "delta_iqr_100km": float(delta_iqr[yi, xi]),
                "absolute_delta_increment_75_100km": float(sensitivity[yi, xi]),
            }
        )
    return records


def _write_audit_pairs(cube: xr.Dataset, signature: xr.Dataset, output_dir: Path) -> list[dict[str, object]]:
    records = _select_audit_pixels(signature)
    audit_dir = output_dir / "audit_pairs"
    audit_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        mask = xr.zeros_like(cube.tmin.isel(time=0), dtype=bool)
        mask.values[record["y_index"], record["x_index"]] = True
        pairs = local_synchrony_pairs(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=mask,
            max_radius_km=100,
            window_days=WINDOW_DAYS,
            window_end=END,
            min_t=MIN_T,
        )
        target = audit_dir / f"{record['label']}.nc"
        _atomic_netcdf(pairs, target)
        record["pair_count"] = int(pairs.sizes["pair"])
        record["path"] = str(target)
    _atomic_json(output_dir / "audit_pixels.json", records)
    return records


def run_statewide(cube: xr.Dataset, colorado, output_dir: Path) -> tuple[xr.Dataset, dict[str, object]]:
    output_mask = spatial_output_mask(cube, colorado)
    with _performance_record() as performance:
        signature = tiled_synchrony_signature(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=output_mask,
            radii_km=RADII_KM,
            tile_shape=TILE_SHAPE,
            window_days=WINDOW_DAYS,
            window_end=END,
            min_t=MIN_T,
            pair_batch_size=8192,
            checkpoint_dir=output_dir / "colorado_tiles_surface_v2",
        )
        signature.attrs.update(
            {
                "output_geometry": "Colorado Census TIGERweb state boundary",
                "output_geometry_geojson": json.dumps(mapping(colorado), separators=(",", ":")),
                "computation_domain_policy": "Colorado output geometry plus 100 km external climate halo",
                "date_range": f"{START}/{END}",
                "source_bytes_streamed": "unavailable: existing PRISM loader does not expose wire-byte accounting",
            }
        )
        _atomic_netcdf(signature, output_dir / "colorado_synchrony_signature.nc")
    audits = _write_audit_pairs(cube, signature, output_dir)
    output_path = output_dir / "colorado_synchrony_signature.nc"
    checkpoint_bytes = sum(
        path.stat().st_size
        for path in (output_dir / "colorado_tiles_surface_v2").glob("*")
    )
    report = {
        "status": "PASS",
        "real_data": True,
        "date_range": [START, END],
        "radii_km": list(RADII_KM),
        "scientific_role": "statewide magnitude/heterogeneity plus nested-radius baseline",
        "observation_radius_km": 100.0,
        "observation_radius_definition": "maximum observed support; not an inferred scale",
        "output_pixels": int(output_mask.sum()),
        "computation_domain_pixels": int(cube.sizes["y"] * cube.sizes["x"]),
        "computation_shape": [int(cube.sizes["y"]), int(cube.sizes["x"])],
        "pair_calculations_with_tile_recompute": int(
            signature.attrs["pair_calculation_count_with_tile_recompute"]
        ),
        "nonself_pair_calculations_with_tile_recompute": int(
            signature.attrs["nonself_pair_calculation_count_with_tile_recompute"]
        ),
        "tile_count": int(signature.attrs["tile_count"]),
        "computed_tiles": int(signature.attrs["computed_tile_count"]),
        "resumed_tiles": int(signature.attrs["resumed_tile_count"]),
        "pair_geometry_seconds_sum": float(signature.attrs["pair_geometry_seconds_sum"]),
        "input_materialization_seconds_sum": float(
            signature.attrs["input_materialization_seconds_sum"]
        ),
        "pair_kernel_seconds_sum": float(signature.attrs["pair_kernel_seconds_sum"]),
        "signature_reduction_seconds_sum": float(
            signature.attrs["signature_reduction_seconds_sum"]
        ),
        "output_bytes": int(output_path.stat().st_size),
        "checkpoint_bytes": int(checkpoint_bytes),
        "input_snapshot_bytes": 0,
        "source_bytes_streamed": None,
        "source_bytes_note": "Existing PRISM loader does not expose wire-byte accounting.",
        "dask_task_count_compute": 0,
        "audit_pixel_count": len(audits),
        **performance,
    }
    _atomic_json(output_dir / "statewide_performance.json", report)
    return signature, report


def run_landscape_change(cube: xr.Dataset, colorado, output_dir: Path) -> dict[str, object]:
    output_mask = spatial_output_mask(cube, colorado)
    with _performance_record() as performance:
        change = tiled_landscape_change_signature(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=output_mask,
            max_radius_km=100,
            tile_shape=TILE_SHAPE,
            window_days=WINDOW_DAYS,
            window_end=END,
            min_t=MIN_T,
            pair_batch_size=8192,
            metric="delta_s",
            deadband=0.02,
            near_tie_epsilon=0.005,
            min_overlap=25,
            checkpoint_dir=output_dir / "landscape_tiles",
        )
        change.attrs.update(
            {
                "output_geometry": "Colorado Census TIGERweb state boundary",
                "computation_domain_policy": "Colorado output geometry plus 100 km external climate halo",
                "date_range": f"{START}/{END}",
            }
        )
        target = output_dir / "colorado_landscape_change.nc"
        _atomic_netcdf(change, target)
    report = {
        "status": "PASS",
        "metric": "delta_s",
        "output_pixels": int(output_mask.sum()),
        "tile_count": int(change.attrs["tile_count"]),
        "computed_tiles": int(change.attrs["computed_tile_count"]),
        "resumed_tiles": int(change.attrs["resumed_tile_count"]),
        "pair_calculations_with_tile_recompute": int(
            change.attrs["pair_calculation_count_with_tile_recompute"]
        ),
        "pair_kernel_seconds_sum": float(change.attrs["pair_kernel_seconds_sum"]),
        "output_bytes": int(target.stat().st_size),
        **performance,
    }
    _atomic_json(output_dir / "landscape_performance.json", report)
    return report


def main(output_dir: Path, *, mode: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    colorado = _colorado_geometry(output_dir)
    halo = expand_spatial_domain(colorado, max(RADII_KM))
    _atomic_json(
        output_dir / "domain.json",
        {
            "output_geometry": mapping(colorado),
            "computation_geometry": mapping(halo),
            "maximum_radius_km": max(RADII_KM),
            "boundary_source": COLORADO_BOUNDARY_URL,
        },
    )
    bbox = tuple(float(value) for value in halo.bounds)
    snapshot = output_dir / "prism_colorado_plus_100km_20231101_20240130.nc"
    with _performance_record() as acquisition_performance:
        cube, acquisition = _load_or_stream_prism(snapshot, bbox)
    acquisition.update(
        {
            "bbox": bbox,
            "shape": dict(cube.sizes),
            "snapshot_bytes": int(snapshot.stat().st_size),
            "source": cube.attrs.get("source"),
            "is_synthetic": bool(cube.attrs.get("is_synthetic", 1)),
            **acquisition_performance,
        }
    )
    _atomic_json(output_dir / "acquisition_report.json", acquisition)
    if mode in {"gate", "all"}:
        gate = run_gate(cube, output_dir)
        print(json.dumps({"engineering_gate": gate}, indent=2), flush=True)
    if mode in {"statewide", "all"}:
        gate_path = output_dir / "gate_report.json"
        if not gate_path.exists() or json.loads(gate_path.read_text())["status"] != "PASS":
            raise RuntimeError("Statewide run requires a passing 100x100 gate")
        _, statewide = run_statewide(cube, colorado, output_dir)
        statewide["input_snapshot_bytes"] = int(snapshot.stat().st_size)
        statewide["acquisition_wall_seconds"] = acquisition_performance["wall_seconds"]
        statewide["acquisition_dask_task_count"] = acquisition["dask_task_count"]
        _atomic_json(output_dir / "statewide_performance.json", statewide)
        print(json.dumps({"statewide": statewide}, indent=2), flush=True)
    if mode in {"landscape", "all"}:
        gate_path = output_dir / "gate_report.json"
        if not gate_path.exists() or json.loads(gate_path.read_text())["status"] != "PASS":
            raise RuntimeError("Landscape-change run requires a passing 100x100 gate")
        landscape = run_landscape_change(cube, colorado, output_dir)
        print(json.dumps({"landscape_change": landscape}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/synchrony_phase2"),
    )
    parser.add_argument(
        "--mode", choices=("gate", "statewide", "landscape", "all"), default="all"
    )
    args = parser.parse_args()
    main(args.output_dir, mode=args.mode)
