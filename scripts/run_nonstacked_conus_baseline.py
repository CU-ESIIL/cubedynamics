#!/usr/bin/env python3
"""Acquire and run the exact non-stacked synchrony baseline over CONUS.

The workflow is deliberately restartable and refuses synthetic data.  It uses
the same 2023-11-01 through 2024-01-30 PRISM window, conditional-tail kernel,
100 km neighborhood, immediate reductions, and nested radii as the completed
Colorado baseline.

Examples
--------
.venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage acquire
.venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage analyze
.venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage finalize
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import resource
import time

import dask
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, TwoSlopeNorm
import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy import ndimage
from scipy.stats import spearmanr
import xarray as xr

from cubedynamics.data.prism import load_prism_cube
from cubedynamics.serialization import sanitize_netcdf_attrs
from cubedynamics.synchrony.baseline import tiled_nonstacked_synchrony_summary


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "nonstacked-conus-baseline"
INPUT = OUTPUT / "inputs" / "prism_conus_20231101_20240130.nc"
RESULT = OUTPUT / "conus_nonstacked_synchrony.nc"
START = "2023-11-01"
END = "2024-01-30"
WINDOW_DAYS = 90
MIN_T = 10
RADII_KM = (25.0, 50.0, 75.0, 100.0)
TILE_SHAPE = (32, 32)
# Exact extent of the NCSCO PRISM daily grid.  Requesting west=-125 returns an
# empty longitude axis; -124.75 is the first native cell-center longitude.
CONUS_BBOX = (-124.75, 24.0, -66.5, 50.0)
PRIMARY = ("cold_median", "warm_median", "delta_pair_median")
RASTERS = (
    "cold_median", "warm_median", "delta_pair_median",
    "delta_median_difference", "valid_pair_count", "valid_pair_fraction",
    "cold_iqr", "warm_iqr", "delta_iqr", "cold_mad", "warm_mad",
    "delta_mad", "cold_mean", "warm_mean", "delta_mean",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", choices=("acquire", "analyze", "merge", "finalize", "all"), default="all"
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--tile-y", type=int, default=TILE_SHAPE[0])
    parser.add_argument("--tile-x", type=int, default=TILE_SHAPE[1])
    parser.add_argument("--partition-count", type=int, default=1)
    parser.add_argument("--partition-index", type=int, default=0)
    return parser


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.json")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


@contextmanager
def _timing():
    started = datetime.now(timezone.utc)
    wall = time.perf_counter()
    cpu = time.process_time()
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record: dict[str, object] = {"started_at_utc": started.isoformat()}
    yield record
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record.update(
        {
            "ended_at_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": time.perf_counter() - wall,
            "cpu_seconds": time.process_time() - cpu,
            "process_peak_rss_bytes": int(after if after > 10_000_000 else after * 1024),
            "process_peak_rss_increase_bytes": int(
                max(0, after - before) if after > 10_000_000 else max(0, after - before) * 1024
            ),
        }
    )


def _encoding(dataset: xr.Dataset) -> dict[str, dict[str, object]]:
    encoding: dict[str, dict[str, object]] = {}
    for name, variable in dataset.data_vars.items():
        if variable.dtype.kind in "fiu" and variable.ndim:
            chunks = tuple(min(int(size), 1 if dim == "time" else 256) for dim, size in zip(variable.dims, variable.shape))
            encoding[name] = {"zlib": True, "complevel": 4, "shuffle": True, "chunksizes": chunks}
    return encoding


def _write_h5(path: Path, dataset: xr.Dataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.nc")
    clean = sanitize_netcdf_attrs(dataset, copy=True)
    clean.to_netcdf(temporary, engine="h5netcdf", encoding=_encoding(clean))
    temporary.replace(path)


def acquire(*, workers: int) -> None:
    if INPUT.exists():
        with xr.open_dataset(INPUT, engine="h5netcdf") as existing:
            if (
                existing.sizes.get("time") == 91
                and existing.sizes.get("y") == 621
                and existing.sizes.get("x") == 1399
                and not bool(existing.attrs.get("is_synthetic", True))
            ):
                print(f"Reusing validated PRISM snapshot: {INPUT}")
                return
        raise RuntimeError(f"Existing input failed identity checks: {INPUT}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    cube = load_prism_cube(
        bbox=CONUS_BBOX,
        start=START,
        end=END,
        variables=["tmin", "tmax"],
        freq="D",
        chunks={"time": 1, "y": 256, "x": 256},
        show_progress=False,
        allow_synthetic=False,
    )
    if bool(cube.attrs.get("is_synthetic", True)):
        raise RuntimeError("Refusing synthetic PRISM input")
    if tuple(cube.sizes.get(name) for name in ("time", "y", "x")) != (91, 621, 1399):
        raise RuntimeError(f"Unexpected PRISM CONUS grid: {dict(cube.sizes)}")
    cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    cube.attrs.update(
        {
            "analysis_input": "non-stacked CONUS synchrony baseline",
            "requested_bbox_west_south_east_north": json.dumps(CONUS_BBOX),
            "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
            "is_synthetic": False,
        }
    )
    with _timing() as timing, dask.config.set(scheduler="threads", num_workers=workers):
        _write_h5(INPUT, cube)
    timing.update(
        {
            "status": "PASS",
            "path": str(INPUT.relative_to(ROOT)),
            "sha256": _digest(INPUT),
            "bytes": INPUT.stat().st_size,
            "network_source": "NCSCO THREDDS NcSS daily PRISM subsets",
            "request_count": 91,
            "worker_limit": workers,
        }
    )
    _json(OUTPUT / "acquisition.json", timing)


def _open_input() -> tuple[xr.Dataset, xr.DataArray]:
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing {INPUT}; run --stage acquire")
    cube = xr.open_dataset(INPUT, engine="h5netcdf", chunks={"time": 91, "y": 256, "x": 256})
    if bool(cube.attrs.get("is_synthetic", True)):
        raise RuntimeError("Refusing synthetic PRISM input")
    if str(cube.time.values[0])[:10] != START or str(cube.time.values[-1])[:10] != END:
        raise RuntimeError("PRISM input date range does not match the frozen experiment")
    mask = (np.isfinite(cube.tmin).all("time") & np.isfinite(cube.tmax).all("time")).compute()
    mask.name = "output_mask"
    mask.attrs.update(
        {
            "definition": "all 91 TMIN and TMAX values finite on the native PRISM CONUS grid",
            "boundary_policy": "PRISM-supported CONUS cells only; national borders and coasts truncate neighborhoods",
        }
    )
    if int(mask.sum()) < 400_000:
        raise RuntimeError(f"Implausibly small CONUS output mask: {int(mask.sum())}")
    return cube, mask


def analyze(*, tile_shape: tuple[int, int], partition_index: int = 0, partition_count: int = 1) -> None:
    if partition_count < 1 or not 0 <= partition_index < partition_count:
        raise ValueError("partition-index must be in [0, partition-count)")
    cube, eligible = _open_input()
    mask = eligible.copy()
    if partition_count > 1:
        selector = np.zeros(mask.shape, dtype=bool)
        for y_start in range(0, mask.sizes["y"], tile_shape[0]):
            if (y_start // tile_shape[0]) % partition_count == partition_index:
                selector[y_start : y_start + tile_shape[0], :] = True
        mask = mask & selector
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with _timing() as timing:
        result = tiled_nonstacked_synchrony_summary(
            cube,
            lower_var="tmin",
            upper_var="tmax",
            output_mask=mask,
            computation_mask=eligible,
            radii_km=RADII_KM,
            tile_shape=tile_shape,
            window_days=WINDOW_DAYS,
            window_end=END,
            min_t=MIN_T,
            split_quantile=0.5,
            pair_batch_size=8192,
            checkpoint_dir=OUTPUT / "tiles",
        )
    result.attrs.update(
        {
            "experiment": "simple non-stacked CONUS synchrony baseline",
            "input_snapshot": str(INPUT.relative_to(ROOT)),
            "output_domain": "finite native PRISM cells in the conterminous United States",
            "input_domain": "native PRISM CONUS grid; no Canada, Mexico, or ocean halo",
            "delta_sign_convention": "cold synchrony - warm synchrony; positive means stronger cold-tail synchrony",
            "national_boundary_policy": "100 km neighborhoods are truncated at the PRISM CONUS support boundary",
            "partition_index": partition_index,
            "partition_count": partition_count,
        }
    )
    result_path = (
        RESULT
        if partition_count == 1
        else OUTPUT / "partitions" / f"conus_part_{partition_index:02d}_of_{partition_count:02d}.nc"
    )
    _write_h5(result_path, result)
    timing.update(
        {
            "status": "PASS",
            "run_mode": "computed" if int(result.attrs["computed_tile_count"]) else "checkpoint_resume_and_finalization",
            "input_snapshot_bytes": INPUT.stat().st_size,
            "network_data_transferred_bytes": 0,
            "output_pixels": int(mask.sum()),
            "tile_count": int(result.attrs["tile_count"]),
            "computed_tile_count": int(result.attrs["computed_tile_count"]),
            "resumed_tile_count": int(result.attrs["resumed_tile_count"]),
            "pair_calculations_with_tile_recompute": int(result.attrs["pair_calculation_count_with_tile_recompute"]),
            "nonself_pair_calculations_with_tile_recompute": int(result.attrs["nonself_pair_calculation_count_with_tile_recompute"]),
            "pair_kernel_seconds_sum": float(result.attrs["pair_kernel_seconds_sum"]),
            "pair_geometry_seconds_sum": float(result.attrs["pair_geometry_seconds_sum"]),
            "input_materialization_seconds_sum": float(result.attrs["input_materialization_seconds_sum"]),
            "exact_reduction_seconds_sum": float(result.attrs["signature_reduction_seconds_sum"]),
            "result_path": str(result_path.relative_to(ROOT)),
            "result_bytes": result_path.stat().st_size,
        }
    )
    performance_path = (
        OUTPUT / "performance.json"
        if partition_count == 1
        else OUTPUT / "partitions" / f"performance_part_{partition_index:02d}_of_{partition_count:02d}.json"
    )
    _json(performance_path, timing)
    cube.close()


def merge_partitions(partition_count: int) -> None:
    paths = [OUTPUT / "partitions" / f"conus_part_{index:02d}_of_{partition_count:02d}.nc" for index in range(partition_count)]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing partition products: " + ", ".join(missing))
    opened = [xr.open_dataset(path, engine="h5netcdf") for path in paths]
    try:
        masks = [dataset.output_mask.astype(bool) for dataset in opened]
        computation = opened[0].computation_mask.astype(bool)
        data_names = [name for name in opened[0].data_vars if name not in {"output_mask", "computation_mask"}]
        merged = opened[0][data_names]
        for dataset in opened[1:]:
            merged = merged.combine_first(dataset[data_names])
        merged["output_mask"] = xr.concat(masks, dim="partition").any("partition")
        merged["computation_mask"] = computation
        attrs = dict(opened[0].attrs)
        summed = (
            "tile_count", "computed_tile_count", "resumed_tile_count",
            "pair_calculation_count_with_tile_recompute", "nonself_pair_calculation_count_with_tile_recompute",
            "pair_kernel_seconds_sum", "pair_geometry_seconds_sum", "input_materialization_seconds_sum",
            "signature_reduction_seconds_sum",
        )
        for name in summed:
            attrs[name] = sum(float(dataset.attrs.get(name, 0)) for dataset in opened)
            if name.endswith("count") or name in {"tile_count", "computed_tile_count", "resumed_tile_count", "pair_calculation_count_with_tile_recompute", "nonself_pair_calculation_count_with_tile_recompute"}:
                attrs[name] = int(attrs[name])
        attrs.update({"partition_index": "merged", "partition_count": partition_count, "execution": "merged disjoint tile-row partitions"})
        merged.attrs = attrs
        _write_h5(RESULT, merged)
    finally:
        for dataset in opened:
            dataset.close()
    performance_records = [_read_json(OUTPUT / "partitions" / f"performance_part_{index:02d}_of_{partition_count:02d}.json") for index in range(partition_count)]
    performance = {
        "status": "PASS", "partition_count": partition_count, "result_bytes": RESULT.stat().st_size,
        "result_sha256": _digest(RESULT),
        "wall_seconds_max_partition": max(float(item["wall_seconds"]) for item in performance_records),
        "cpu_seconds_sum": sum(float(item["cpu_seconds"]) for item in performance_records),
        "output_pixels": sum(int(item["output_pixels"]) for item in performance_records),
        "tile_count": sum(int(item["tile_count"]) for item in performance_records),
        "computed_tile_count": sum(int(item["computed_tile_count"]) for item in performance_records),
        "resumed_tile_count": sum(int(item["resumed_tile_count"]) for item in performance_records),
        "pair_calculations_with_tile_recompute": sum(int(item["pair_calculations_with_tile_recompute"]) for item in performance_records),
        "nonself_pair_calculations_with_tile_recompute": sum(int(item["nonself_pair_calculations_with_tile_recompute"]) for item in performance_records),
        "pair_kernel_seconds_sum": sum(float(item["pair_kernel_seconds_sum"]) for item in performance_records),
    }
    _json(OUTPUT / "performance.json", performance)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _transform(result: xr.Dataset):
    x = np.asarray(result.x.values, dtype=float)
    y = np.asarray(result.y.values, dtype=float)
    dx = abs(float(np.median(np.diff(x))))
    dy = abs(float(np.median(np.diff(y))))
    return from_origin(float(x.min() - dx / 2), float(y.max() + dy / 2), dx, dy)


def _write_rasters(result: xr.Dataset) -> list[str]:
    raster_dir = OUTPUT / "rasters"
    raster_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    mask = result.output_mask.values.astype(bool)
    for name in RASTERS:
        data = np.asarray(result[name].sel(radius_km=100).isel(time_window_end=0).values)
        values = np.where(mask & np.isfinite(data), data, -9999).astype("float32")
        path = raster_dir / f"{name}_100km.tif"
        with rasterio.open(
            path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1],
            count=1, dtype="float32", crs="EPSG:4326", transform=_transform(result),
            nodata=-9999.0, compress="deflate", tiled=True, blockxsize=256, blockysize=256,
        ) as target:
            target.write(values, 1)
            target.set_band_description(1, name)
            target.update_tags(
                observation_radius_km="100", self_pair_policy="excluded",
                sign_convention="Delta = cold synchrony - warm synchrony", stacking="none",
                boundary_policy="truncated at native PRISM CONUS support",
            )
        paths.append(str(path.relative_to(ROOT)))
    return paths


def _outline(ax, result: xr.Dataset) -> None:
    mask = result.output_mask.values.astype(float)
    ax.contour(result.x, result.y, mask, levels=[0.5], colors="#18222d", linewidths=0.35)
    ax.set_aspect(1 / np.cos(np.deg2rad(37.5)))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


def _figures(result: xr.Dataset) -> list[str]:
    figure_dir = OUTPUT / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    mask = result.output_mask.values.astype(bool)
    cold = result.cold_median.sel(radius_km=100).values[0][mask]
    warm = result.warm_median.sel(radius_km=100).values[0][mask]
    delta = result.delta_pair_median.sel(radius_km=100).values[0][mask]
    common = max(float(np.nanpercentile(np.abs(np.concatenate((cold, warm))), 99)), 0.01)
    dlimit = max(float(np.nanpercentile(np.abs(delta), 99)), 0.01)

    fig, axes = plt.subplots(3, 1, figsize=(13.5, 11), constrained_layout=True)
    for ax, name, title, limit in zip(
        axes, PRIMARY,
        ("A  COLD SYNCHRONY", "B  WARM SYNCHRONY", "C  DELTA = COLD - WARM"),
        (common, common, dlimit),
    ):
        values = result[name].sel(radius_km=100).isel(time_window_end=0).where(result.output_mask)
        mesh = ax.pcolormesh(result.x, result.y, values, shading="nearest", cmap="RdBu", norm=TwoSlopeNorm(0, -limit, limit), rasterized=True)
        _outline(ax, result); ax.set_title(title, loc="left", weight="bold")
        fig.colorbar(mesh, ax=ax, shrink=.72, label="Median Spearman synchrony")
    fig.suptitle("CONUS immediate 100 km local-surface reduction - no stacking", weight="bold", fontsize=16)
    primary = figure_dir / "primary_three_panel.png"
    fig.savefig(primary, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(14, 8), constrained_layout=True)
    for ax, name, title, cmap in zip(
        axes.ravel(),
        ("valid_pair_count", "valid_pair_fraction", "delta_iqr", "delta_reduction_gap"),
        ("A  VALID DELTA PAIRS", "B  VALID DELTA FRACTION", "C  DELTA IQR", "D  DELTA REDUCTION GAP"),
        ("viridis", "viridis", "magma", "RdBu"),
    ):
        array = result[name].sel(radius_km=100).isel(time_window_end=0).where(result.output_mask)
        values = np.asarray(array.values)[mask]
        if name == "delta_reduction_gap":
            limit = max(float(np.nanpercentile(np.abs(values), 99)), .01)
            norm = TwoSlopeNorm(0, -limit, limit)
        elif name == "valid_pair_fraction":
            norm = Normalize(0, 1)
        else:
            norm = Normalize(float(np.nanpercentile(values, 1)), float(np.nanpercentile(values, 99)))
        mesh = ax.pcolormesh(result.x, result.y, array, shading="nearest", cmap=cmap, norm=norm, rasterized=True)
        _outline(ax, result); ax.set_title(title, loc="left", weight="bold")
        fig.colorbar(mesh, ax=ax, shrink=.72)
    qc_path = figure_dir / "qc_maps.png"
    fig.savefig(qc_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [str(primary.relative_to(ROOT)), str(qc_path.relative_to(ROOT))]


def _summary(result: xr.Dataset) -> None:
    mask = result.output_mask.values.astype(bool)
    variables = RASTERS + ("delta_reduction_gap",)
    with (OUTPUT / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ("radius_km", "variable", "valid_pixels", "mean", "std", "min", "p10", "p25", "median", "p75", "p90", "max")
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for radius in RADII_KM:
            for name in variables:
                values = np.asarray(result[name].sel(radius_km=radius).values[0], dtype=float)[mask]
                values = values[np.isfinite(values)]
                q = np.quantile(values, (.1, .25, .5, .75, .9))
                writer.writerow(dict(zip(fields, (radius, name, values.size, values.mean(), values.std(), values.min(), q[0], q[1], q[2], q[3], q[4], values.max()))))


def _qc(result: xr.Dataset) -> dict[str, object]:
    mask = result.output_mask.values.astype(bool)
    eroded = ndimage.binary_erosion(mask, iterations=2)
    boundary = mask & ~eroded
    record: dict[str, object] = {"output_pixels": int(mask.sum()), "boundary_pixels": int(boundary.sum()), "variables": {}}
    for name in PRIMARY:
        array = np.asarray(result[name].sel(radius_km=100).values[0], dtype=float)
        finite = mask & np.isfinite(array)
        h = np.abs(np.diff(array, axis=1)); hv = finite[:, 1:] & finite[:, :-1]
        v = np.abs(np.diff(array, axis=0)); vv = finite[1:, :] & finite[:-1, :]
        seams_h = np.zeros_like(hv); seams_h[:, 31::32] = True
        seams_v = np.zeros_like(vv); seams_v[31::32, :] = True
        all_jumps = np.concatenate((h[hv], v[vv]))
        seam_jumps = np.concatenate((h[hv & seams_h], v[vv & seams_v]))
        record["variables"][name] = {
            "missing_output_pixels": int(np.count_nonzero(mask & ~np.isfinite(array))),
            "minimum": float(np.nanmin(array[mask])), "maximum": float(np.nanmax(array[mask])),
            "median": float(np.nanmedian(array[mask])),
            "boundary_median": float(np.nanmedian(array[boundary])),
            "interior_median": float(np.nanmedian(array[eroded])),
            "tile_seam_neighbor_jump_median": float(np.nanmedian(seam_jumps)),
            "all_neighbor_jump_median": float(np.nanmedian(all_jumps)),
            "tile_seam_to_all_jump_ratio": float(np.nanmedian(seam_jumps) / np.nanmedian(all_jumps)),
        }
    count = np.asarray(result.valid_pair_count.sel(radius_km=100).values[0], dtype=float)[mask]
    fraction = np.asarray(result.valid_pair_fraction.sel(radius_km=100).values[0], dtype=float)[mask]
    record["support"] = {
        "count_min": int(np.nanmin(count)), "count_median": float(np.nanmedian(count)), "count_max": int(np.nanmax(count)),
        "fraction_min": float(np.nanmin(fraction)), "fraction_median": float(np.nanmedian(fraction)), "fraction_max": float(np.nanmax(fraction)),
    }
    record["national_boundary_warning"] = "CONUS-edge focal neighborhoods are clipped because PRISM has no Canada/Mexico/ocean halo."
    return record


def _findings(result: xr.Dataset) -> dict[str, object]:
    mask = result.output_mask.values.astype(bool)
    arrays = {
        name: np.asarray(result[name].sel(radius_km=100).values[0], dtype=float)
        for name in (*PRIMARY, "delta_median_difference", "delta_reduction_gap")
    }

    def adjacency(array: np.ndarray) -> float:
        left, right = array[:, :-1], array[:, 1:]
        hv = mask[:, :-1] & mask[:, 1:] & np.isfinite(left) & np.isfinite(right)
        top, bottom = array[:-1, :], array[1:, :]
        vv = mask[:-1, :] & mask[1:, :] & np.isfinite(top) & np.isfinite(bottom)
        return float(np.corrcoef(np.concatenate((left[hv], top[vv])), np.concatenate((right[hv], bottom[vv])))[0, 1])

    delta = arrays["delta_pair_median"][mask]
    gap = arrays["delta_reduction_gap"][mask]
    window = {}
    reference = delta
    for radius in RADII_KM:
        candidate = np.asarray(result.delta_pair_median.sel(radius_km=radius).values[0], dtype=float)[mask]
        valid = np.isfinite(reference) & np.isfinite(candidate)
        window[f"{radius:g}_vs_100km_spearman"] = float(spearmanr(reference[valid], candidate[valid]).statistic)
    return {
        "conus_100km": {
            "cold_median_across_focal_pixels": float(np.nanmedian(arrays["cold_median"][mask])),
            "warm_median_across_focal_pixels": float(np.nanmedian(arrays["warm_median"][mask])),
            "delta_pair_median_across_focal_pixels": float(np.nanmedian(delta)),
            "delta_positive_fraction": float(np.mean(delta > 0)),
            "delta_negative_fraction": float(np.mean(delta < 0)),
            "cold_warm_map_spearman": float(spearmanr(arrays["cold_median"][mask], arrays["warm_median"][mask]).statistic),
        },
        "delta_reduction_comparison": {
            "median_gap": float(np.nanmedian(gap)), "median_absolute_gap": float(np.nanmedian(np.abs(gap))),
            "p95_absolute_gap": float(np.nanquantile(np.abs(gap), .95)), "maximum_absolute_gap": float(np.nanmax(np.abs(gap))),
            "spearman_between_maps": float(spearmanr(delta, arrays["delta_median_difference"][mask]).statistic),
        },
        "adjacent_pixel_pearson": {name: adjacency(arrays[name]) for name in PRIMARY},
        "nested_radius_sensitivity": window,
    }


def _colorado_reproduction_gate(result: xr.Dataset) -> dict[str, object]:
    colorado_input = ROOT / "artifacts" / "synchrony-stack-phase2" / "prism_colorado_plus_100km_20231101_20240130.nc"
    colorado_result = ROOT / "artifacts" / "nonstacked-colorado-baseline" / "colorado_nonstacked_synchrony.nc"
    if not colorado_input.exists() or not colorado_result.exists():
        return {"status": "NOT_RUN", "reason": "retained Colorado inputs/results unavailable"}
    with xr.open_dataset(INPUT, engine="h5netcdf") as national_input, xr.open_dataset(colorado_input, engine="scipy") as local_input:
        overlap = national_input.sel(y=local_input.y, x=local_input.x)
        input_errors = {
            name: float(np.nanmax(np.abs(np.asarray(overlap[name].values) - np.asarray(local_input[name].values))))
            for name in ("tmin", "tmax")
        }
    with xr.open_dataset(colorado_result, engine="scipy") as colorado:
        national = result.sel(y=colorado.y, x=colorado.x)
        mask = colorado.output_mask.values.astype(bool)
        variables = (*RASTERS, "delta_reduction_gap")
        errors = {}
        for name in variables:
            left = np.asarray(national[name].values, dtype=float)[:, :, mask]
            right = np.asarray(colorado[name].values, dtype=float)[:, :, mask]
            errors[name] = float(np.nanmax(np.abs(left - right)))
    maximum = max((*input_errors.values(), *errors.values()), default=0.0)
    status = "PASS" if maximum <= 1e-12 else "FAIL"
    return {
        "status": status, "tolerance": 1e-12, "maximum_absolute_error": maximum,
        "input_maximum_absolute_errors": input_errors, "output_maximum_absolute_errors": errors,
        "interpretation": "CONUS expansion reproduces the retained Colorado input and all nested-radius baseline fields on the Colorado output mask",
    }


def finalize() -> None:
    if not RESULT.exists():
        raise FileNotFoundError(f"Missing {RESULT}; run --stage analyze")
    with xr.open_dataset(RESULT, engine="h5netcdf") as result:
        paths = _write_rasters(result)
        figures = _figures(result)
        _summary(result)
        qc = _qc(result)
        findings = _findings(result)
        colorado_gate = _colorado_reproduction_gate(result)
        output_pixels = int(result.output_mask.sum())
    _json(OUTPUT / "qc.json", qc)
    _json(OUTPUT / "findings.json", findings)
    _json(OUTPUT / "colorado_reproduction_gate.json", colorado_gate)
    if colorado_gate["status"] == "FAIL":
        raise RuntimeError(f"Colorado reproduction gate failed: {colorado_gate}")
    dx = (CONUS_BBOX[2] - CONUS_BBOX[0]) / 1398
    dy = (49.916667 - 24.083333) / 620
    _json(OUTPUT / "geometry.json", {
        "native_grid_shape": [621, 1399], "raster_resolution_degrees": {"longitude": dx, "latitude": dy},
        "output_pixel_count": output_pixels, "neighborhood": "100 km great-circle radius over eligible PRISM CONUS cells",
        "maximum_center_to_neighbor_distance_km": 100.0, "self_pair_policy": "excluded",
        "boundary_policy": "truncated at the native PRISM CONUS support boundary",
    })
    provenance = {
        "status": "complete",
        "analysis": "simple non-stacked CONUS synchrony baseline",
        "source": "PRISM AN daily via NCSCO THREDDS",
        "real_observations": True,
        "is_synthetic": False,
        "date_range": [START, END],
        "window_days": WINDOW_DAYS,
        "split_quantile": .5,
        "min_t_per_tail": MIN_T,
        "radii_km": list(RADII_KM),
        "primary_radius_km": 100,
        "pair_statistic": "one-tail Spearman using current CubeDynamics validated kernel",
        "delta_sign_convention": "cold - warm",
        "self_pair_policy": "excluded",
        "stacking": False,
        "overlap_alignment": False,
        "second_stage_convolution": False,
        "input_path": str(INPUT.relative_to(ROOT)),
        "input_sha256": _digest(INPUT),
        "output_path": str(RESULT.relative_to(ROOT)),
        "output_sha256": _digest(RESULT),
        "output_pixels": output_pixels,
        "national_boundary_policy": "native PRISM support; neighborhoods clipped at national borders/coasts",
        "raster_outputs": paths,
        "figures": figures,
        "reproduction_commands": [
            ".venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage acquire",
            ".venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage analyze",
            ".venv/bin/python scripts/run_nonstacked_conus_baseline.py --stage finalize",
        ],
    }
    _json(OUTPUT / "provenance.json", provenance)
    readme = f"""# Non-stacked CONUS synchrony baseline

This is the exact national expansion of the Colorado immediate-reduction
baseline for {START} through {END}. Each native PRISM focal cell receives the
median and diagnostic reductions of its non-self pair relationships inside
100 km. There is no stack, overlap alignment, or second-stage convolution.

The calculation is checkpointed under `tiles/`. The primary data product is
`{RESULT.name}` and the 100 km GeoTIFFs are under `rasters/`.

Important boundary qualification: PRISM only supplies CONUS support here, so
neighborhoods at Canada, Mexico, and coast boundaries are clipped rather than
filled with observations outside the national product domain.
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")


def main() -> int:
    args = _parser().parse_args()
    if args.stage in {"acquire", "all"}:
        acquire(workers=args.workers)
    if args.stage in {"analyze", "all"}:
        analyze(
            tile_shape=(args.tile_y, args.tile_x),
            partition_index=args.partition_index,
            partition_count=args.partition_count,
        )
    if args.stage == "merge" or (args.stage == "all" and args.partition_count > 1):
        merge_partitions(args.partition_count)
    if args.stage in {"finalize", "all"}:
        finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
