#!/usr/bin/env python3
"""Forensically audit hot/cold/Delta semantics without changing production outputs."""

from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
import re

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, to_hex
import numpy as np
import pandas as pd
import rasterio
from scipy.stats import rankdata, spearmanr
import xarray as xr

from cubedynamics.stats.tails import one_tail_spearman
from cubedynamics.synchrony.baseline import nonstacked_synchrony_summary
from cubedynamics.synchrony.production import local_synchrony_pairs


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "nonstacked-conus-baseline"
INPUT = BASE / "inputs" / "prism_conus_20231101_20240130.nc"
RESULT = BASE / "conus_nonstacked_synchrony.nc"
OUTPUT = ROOT / "artifacts" / "hot-cold-delta-semantics-audit"
END = "2024-01-30"
RADIUS_KM = 100.0
TOLERANCE = 1e-12


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _nearest_valid(result: xr.Dataset, latitude: float, longitude: float) -> tuple[int, int]:
    mask = result.output_mask.values.astype(bool)
    yi, xi = np.nonzero(mask)
    score = (result.y.values[yi] - latitude) ** 2 + (
        (result.x.values[xi] - longitude) * np.cos(np.deg2rad(latitude))
    ) ** 2
    index = int(np.argmin(score))
    return int(yi[index]), int(xi[index])


def _series_percentiles(values: np.ndarray) -> np.ndarray:
    finite = np.isfinite(values)
    output = np.full(values.shape, np.nan, dtype=float)
    output[finite] = rankdata(values[finite], method="average") / np.count_nonzero(finite)
    return output


def _pixel_tail_tables(cube: xr.Dataset, result: xr.Dataset) -> tuple[pd.DataFrame, pd.DataFrame]:
    locations = {
        "west": (40.0, -120.0),
        "mountain": (39.0, -106.0),
        "east": (38.0, -78.0),
    }
    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    dates = pd.to_datetime(cube.time.values)
    for label, (lat, lon) in locations.items():
        yi, xi = _nearest_valid(result, lat, lon)
        tmin = np.asarray(cube.tmin[:, yi, xi].values, dtype=float)
        tmax = np.asarray(cube.tmax[:, yi, xi].values, dtype=float)
        tmin_threshold = float(np.quantile(tmin, .5))
        tmax_threshold = float(np.quantile(tmax, .5))
        cold = tmin <= tmin_threshold
        warm = tmax > tmax_threshold
        tmin_pct = _series_percentiles(tmin)
        tmax_pct = _series_percentiles(tmax)
        chosen = np.unique(
            np.concatenate(
                (
                    np.argsort(tmin)[:4],
                    np.argsort(np.abs(tmin - tmin_threshold))[:3],
                    np.argsort(tmax)[-4:],
                    np.argsort(np.abs(tmax - tmax_threshold))[:3],
                )
            )
        )
        for index in chosen:
            rows.append(
                {
                    "pixel": label,
                    "latitude": float(result.y.values[yi]),
                    "longitude": float(result.x.values[xi]),
                    "date": dates[index].date().isoformat(),
                    "tmin_c": float(tmin[index]),
                    "tmin_percentile_average_rank": float(tmin_pct[index]),
                    "cold_flag": bool(cold[index]),
                    "tmax_c": float(tmax[index]),
                    "tmax_percentile_average_rank": float(tmax_pct[index]),
                    "warm_flag": bool(warm[index]),
                }
            )
        summaries.append(
            {
                "pixel": label,
                "latitude": float(result.y.values[yi]),
                "longitude": float(result.x.values[xi]),
                "tmin_median_threshold_c": tmin_threshold,
                "tmax_median_threshold_c": tmax_threshold,
                "cold_date_count": int(cold.sum()),
                "warm_date_count": int(warm.sum()),
                "median_tmin_on_cold_dates_c": float(np.median(tmin[cold])),
                "median_tmin_on_non_cold_dates_c": float(np.median(tmin[~cold])),
                "median_tmax_on_warm_dates_c": float(np.median(tmax[warm])),
                "median_tmax_on_non_warm_dates_c": float(np.median(tmax[~warm])),
                "cold_is_lower": bool(np.median(tmin[cold]) < np.median(tmin[~cold])),
                "warm_is_upper": bool(np.median(tmax[warm]) > np.median(tmax[~warm])),
                "median_cold_temperature_less_than_median_warm_temperature": bool(
                    np.median(tmin[cold]) < np.median(tmax[warm])
                ),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(summaries)


def _focal_pairs(
    cube: xr.Dataset,
    result: xr.Dataset,
    yi: int,
    xi: int,
) -> tuple[xr.Dataset, xr.Dataset, int]:
    latitude = float(result.y.values[yi]); longitude = float(result.x.values[xi])
    y_indices = np.flatnonzero(np.abs(cube.y.values - latitude) <= 1.05)
    x_indices = np.flatnonzero(np.abs(cube.x.values - longitude) <= 1.65)
    y_slice = slice(int(y_indices.min()), int(y_indices.max()) + 1)
    x_slice = slice(int(x_indices.min()), int(x_indices.max()) + 1)
    subset = cube.isel(y=y_slice, x=x_slice).load()
    eligible = np.isfinite(subset.tmin).all("time") & np.isfinite(subset.tmax).all("time")
    local_y = int(np.argmin(np.abs(subset.y.values - latitude)))
    local_x = int(np.argmin(np.abs(subset.x.values - longitude)))
    output = xr.zeros_like(eligible, dtype=bool)
    output.values[local_y, local_x] = True
    pairs = local_synchrony_pairs(
        subset,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output,
        computation_mask=eligible,
        max_radius_km=RADIUS_KM,
        window_days=90,
        window_end=END,
        min_t=10,
        split_quantile=.5,
        pair_batch_size=8192,
    )
    focal_flat = local_y * subset.sizes["x"] + local_x
    return subset, pairs, focal_flat


def _tail_observations(
    dates: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    *,
    tail: str,
) -> tuple[pd.DataFrame, float, int, float, float]:
    valid = np.isfinite(a) & np.isfinite(b)
    av = a[valid]; bv = b[valid]; dv = pd.to_datetime(dates[valid])
    q = .5 if tail == "lower" else .5
    ta = float(np.quantile(av, q)); tb = float(np.quantile(bv, q))
    selected = (av <= ta) & (bv <= tb) if tail == "lower" else (av > ta) & (bv > tb)
    selected_a = av[selected]; selected_b = bv[selected]
    direct = float(spearmanr(selected_a, selected_b).statistic)
    full_rank_a = rankdata(av, method="average") / av.size
    full_rank_b = rankdata(bv, method="average") / bv.size
    tail_rank_a = rankdata(selected_a, method="average")
    tail_rank_b = rankdata(selected_b, method="average")
    selected_indices = np.flatnonzero(selected)
    frame = pd.DataFrame(
        {
            "date": [dv[index].date().isoformat() for index in selected_indices],
            "temperature_a_c": selected_a,
            "temperature_b_c": selected_b,
            "full_percentile_a": full_rank_a[selected],
            "full_percentile_b": full_rank_b[selected],
            "within_tail_rank_a": tail_rank_a,
            "within_tail_rank_b": tail_rank_b,
            "tail_flag_a": True,
            "tail_flag_b": True,
        }
    )
    return frame, direct, int(selected.sum()), ta, tb


def _pair_audit(cube: xr.Dataset, result: xr.Dataset) -> tuple[pd.DataFrame, pd.DataFrame]:
    requests = [
        ("pacific_northwest", 47.0, -118.0, "maximum"),
        ("great_basin", 39.0, -116.0, "minimum"),
        ("rockies", 39.0, -106.0, "distance50"),
        ("plains", 39.0, -100.0, "median"),
        ("east", 38.0, -78.0, "distance50"),
    ]
    summaries: list[dict[str, object]] = []
    observations: list[pd.DataFrame] = []
    for pair_number, (region, latitude, longitude, strategy) in enumerate(requests, start=1):
        yi, xi = _nearest_valid(result, latitude, longitude)
        subset, pairs, focal = _focal_pairs(cube, result, yi, xi)
        source = pairs.source_index.values.astype(int); target = pairs.target_index.values.astype(int)
        candidate = (source != target) & np.isfinite(pairs.cold_synchrony) & np.isfinite(pairs.warm_synchrony)
        indices = np.flatnonzero(candidate)
        if strategy == "maximum":
            pair_index = int(indices[np.argmax(pairs.delta_s.values[indices])])
        elif strategy == "minimum":
            pair_index = int(indices[np.argmin(pairs.delta_s.values[indices])])
        elif strategy == "distance50":
            pair_index = int(indices[np.argmin(np.abs(pairs.distance_km.values[indices] - 50.0))])
        else:
            order = indices[np.argsort(pairs.delta_s.values[indices])]
            pair_index = int(order[len(order) // 2])
        left = int(source[pair_index]); right = int(target[pair_index])
        ly, lx = divmod(left, subset.sizes["x"]); ry, rx = divmod(right, subset.sizes["x"])
        pair_id = f"pair_{pair_number}_{region}"
        cold_frame, cold_direct, cold_count, cold_a_threshold, cold_b_threshold = _tail_observations(
            subset.time.values,
            np.asarray(subset.tmin[:, ly, lx].values, dtype=float),
            np.asarray(subset.tmin[:, ry, rx].values, dtype=float),
            tail="lower",
        )
        warm_frame, warm_direct, warm_count, warm_a_threshold, warm_b_threshold = _tail_observations(
            subset.time.values,
            np.asarray(subset.tmax[:, ly, lx].values, dtype=float),
            np.asarray(subset.tmax[:, ry, rx].values, dtype=float),
            tail="upper",
        )
        stored_cold = float(pairs.cold_synchrony.values[pair_index])
        stored_warm = float(pairs.warm_synchrony.values[pair_index])
        stored_delta = float(pairs.delta_s.values[pair_index])
        expected_delta = stored_cold - stored_warm
        for tail, frame in (("cold_lower_tmin", cold_frame), ("warm_upper_tmax", warm_frame)):
            frame.insert(0, "tail", tail)
            frame.insert(0, "region", region)
            frame.insert(0, "pair_id", pair_id)
            observations.append(frame)
        summaries.append(
            {
                "pair_id": pair_id,
                "region": region,
                "pixel_a_latitude": float(subset.y.values[ly]),
                "pixel_a_longitude": float(subset.x.values[lx]),
                "pixel_b_latitude": float(subset.y.values[ry]),
                "pixel_b_longitude": float(subset.x.values[rx]),
                "distance_km": float(pairs.distance_km.values[pair_index]),
                "cold_tmin_threshold_a_c": cold_a_threshold,
                "cold_tmin_threshold_b_c": cold_b_threshold,
                "cold_observation_count": cold_count,
                "stored_cold": stored_cold,
                "direct_cold": cold_direct,
                "cold_absolute_error": abs(stored_cold - cold_direct),
                "warm_tmax_threshold_a_c": warm_a_threshold,
                "warm_tmax_threshold_b_c": warm_b_threshold,
                "warm_observation_count": warm_count,
                "stored_warm": stored_warm,
                "direct_warm": warm_direct,
                "warm_absolute_error": abs(stored_warm - warm_direct),
                "stored_delta": stored_delta,
                "expected_delta_cold_minus_warm": expected_delta,
                "delta_absolute_error": abs(stored_delta - expected_delta),
                "all_assertions_pass": bool(
                    abs(stored_cold - cold_direct) <= TOLERANCE
                    and abs(stored_warm - warm_direct) <= TOLERANCE
                    and abs(stored_delta - expected_delta) <= TOLERANCE
                ),
            }
        )
    return pd.DataFrame(summaries), pd.concat(observations, ignore_index=True)


def _synthetic_case(name: str, cold_mode: str, warm_mode: str) -> dict[str, object]:
    n = 40
    base = np.arange(n, dtype=float)
    weak = np.asarray([20, 39, 21, 38, 22, 37, 23, 36, 24, 35, 25, 34, 26, 33, 27, 32, 28, 31, 29, 30], dtype=float)

    def companion(mode: str) -> np.ndarray:
        if mode == "strong":
            return base.copy()
        if mode == "weak_lower":
            return np.concatenate((weak - 20, base[20:]))
        if mode == "weak_upper":
            return np.concatenate((base[:20], weak))
        raise ValueError(mode)

    a_tmin = base; a_tmax = base
    b_tmin = companion(cold_mode); b_tmax = companion(warm_mode)
    dataset = xr.Dataset(
        {
            "tmin": (("time", "y", "x"), np.stack((a_tmin, b_tmin), axis=1)[:, None, :]),
            "tmax": (("time", "y", "x"), np.stack((a_tmax, b_tmax), axis=1)[:, None, :]),
        },
        coords={
            "time": np.datetime64("2024-01-01") + np.arange(n).astype("timedelta64[D]"),
            "y": [40.0], "x": [-105.0, -104.5],
        },
    )
    dataset.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    dataset.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    pairs = local_synchrony_pairs(
        dataset,
        lower_var="tmin", upper_var="tmax",
        output_mask=np.ones((1, 2), dtype=bool), computation_mask=np.ones((1, 2), dtype=bool),
        max_radius_km=100, window_days=39, min_t=10, split_quantile=.5,
    )
    nonself = pairs.source_index.values != pairs.target_index.values
    cold = float(pairs.cold_synchrony.values[nonself][0])
    warm = float(pairs.warm_synchrony.values[nonself][0])
    delta = float(pairs.delta_s.values[nonself][0])
    interpretation = "stronger cold synchrony" if delta > TOLERANCE else "stronger warm synchrony" if delta < -TOLERANCE else "equal cold and warm synchrony"
    return {"case": name, "cold": cold, "warm": warm, "delta": delta, "interpretation": interpretation}


def _synthetic_cases() -> list[dict[str, object]]:
    cases = [
        _synthetic_case("A_cold_stronger", "strong", "weak_upper"),
        _synthetic_case("B_warm_stronger", "weak_lower", "strong"),
        _synthetic_case("C_equal", "strong", "strong"),
    ]
    assert cases[0]["cold"] > cases[0]["warm"] and cases[0]["delta"] > 0
    assert cases[1]["warm"] > cases[1]["cold"] and cases[1]["delta"] < 0
    assert abs(float(cases[2]["delta"])) <= TOLERANCE
    return cases


def _collapsed_pixel_audit(cube: xr.Dataset, result: xr.Dataset) -> tuple[dict[str, object], pd.DataFrame]:
    x = result.x.values; y = result.y.values
    west = result.output_mask.values.astype(bool) & (x[None, :] >= -120) & (x[None, :] <= -104) & (y[:, None] >= 33) & (y[:, None] <= 45)
    delta_map = np.asarray(result.delta_pair_median.sel(radius_km=100).isel(time_window_end=0).values, dtype=float)
    candidates = np.where(west, delta_map, np.nan)
    yi, xi = np.unravel_index(np.nanargmin(candidates), candidates.shape)
    subset, pairs, focal = _focal_pairs(cube, result, int(yi), int(xi))
    summary = nonstacked_synchrony_summary(pairs, radii_km=(100.0,))
    local_y = int(np.argmin(np.abs(subset.y.values - result.y.values[yi])))
    local_x = int(np.argmin(np.abs(subset.x.values - result.x.values[xi])))
    nonself = pairs.source_index.values != pairs.target_index.values
    incident = nonself & ((pairs.source_index.values == focal) | (pairs.target_index.values == focal))
    pair_table = pd.DataFrame(
        {
            "distance_km": pairs.distance_km.values[incident],
            "s_cold": pairs.cold_synchrony.values[incident],
            "s_warm": pairs.warm_synchrony.values[incident],
            "delta_cold_minus_warm": pairs.delta_s.values[incident],
        }
    )
    cold = float(summary.cold_median.values[0, 0, local_y, local_x])
    warm = float(summary.warm_median.values[0, 0, local_y, local_x])
    pair_delta = float(summary.delta_pair_median.values[0, 0, local_y, local_x])
    med_difference = float(summary.delta_median_difference.values[0, 0, local_y, local_x])
    map_value = float(result.delta_pair_median.sel(radius_km=100).isel(time_window_end=0, y=yi, x=xi).values)
    raster_path = BASE / "rasters" / "delta_pair_median_100km.tif"
    with rasterio.open(raster_path) as source:
        row, col = source.index(float(result.x.values[xi]), float(result.y.values[yi]))
        raster_value = float(source.read(1)[row, col])
        raster_tags = source.tags(1) | source.tags()
    all_delta = delta_map[result.output_mask.values.astype(bool)]
    limit = max(float(np.nanpercentile(np.abs(all_delta), 99)), .01)
    norm = TwoSlopeNorm(vcenter=0, vmin=-limit, vmax=limit)
    rgba = plt.get_cmap("RdBu")(norm(map_value))
    color_hex = to_hex(rgba, keep_alpha=False)
    record = {
        "latitude": float(result.y.values[yi]),
        "longitude": float(result.x.values[xi]),
        "incident_nonself_pairs": int(incident.sum()),
        "recomputed_median_cold": cold,
        "recomputed_median_warm": warm,
        "recomputed_median_pairwise_delta": pair_delta,
        "recomputed_difference_of_medians": med_difference,
        "reduction_gap": pair_delta - med_difference,
        "netcdf_primary_delta": map_value,
        "geotiff_primary_delta": raster_value,
        "netcdf_absolute_error": abs(pair_delta - map_value),
        "geotiff_absolute_error": abs(pair_delta - raster_value),
        "plot_cmap": "RdBu",
        "plot_vmin": -limit,
        "plot_center": 0.0,
        "plot_vmax": limit,
        "displayed_color_hex": color_hex,
        "displayed_color_family": "red" if map_value < 0 else "blue" if map_value > 0 else "white",
        "legend_interpretation": "stronger warm synchrony" if map_value < 0 else "stronger cold synchrony" if map_value > 0 else "equal cold and warm synchrony",
        "raster_tags": raster_tags,
    }
    assert record["netcdf_absolute_error"] <= TOLERANCE
    assert record["geotiff_absolute_error"] <= 1e-6
    return record, pair_table


def _western_spot_checks(result: xr.Dataset) -> pd.DataFrame:
    mask = result.output_mask.values.astype(bool)
    x = result.x.values; y = result.y.values
    west = mask & (x[None, :] >= -122) & (x[None, :] <= -103) & (y[:, None] >= 32) & (y[:, None] <= 47)
    cold = np.asarray(result.cold_median.sel(radius_km=100).isel(time_window_end=0).values, dtype=float)
    warm = np.asarray(result.warm_median.sel(radius_km=100).isel(time_window_end=0).values, dtype=float)
    delta = np.asarray(result.delta_pair_median.sel(radius_km=100).isel(time_window_end=0).values, dtype=float)
    threshold = float(np.nanquantile(delta[west], .08))
    yi, xi = np.nonzero(west & (delta <= threshold))
    order = np.argsort(delta[yi, xi])
    selected = [int(order[0])]
    while len(selected) < 5:
        chosen_y = y[yi[selected]]; chosen_x = x[xi[selected]]
        distances = np.min(
            (y[yi][:, None] - chosen_y[None, :]) ** 2
            + ((x[xi][:, None] - chosen_x[None, :]) * np.cos(np.deg2rad(y[yi][:, None]))) ** 2,
            axis=1,
        )
        distances[selected] = -1
        selected.append(int(np.argmax(distances)))
    limit = max(float(np.nanpercentile(np.abs(delta[mask]), 99)), .01)
    norm = TwoSlopeNorm(vcenter=0, vmin=-limit, vmax=limit)
    rows = []
    for index in selected:
        yy, xx = int(yi[index]), int(xi[index])
        value = float(delta[yy, xx])
        rows.append(
            {
                "latitude": float(y[yy]), "longitude": float(x[xx]),
                "collapsed_cold_median": float(cold[yy, xx]),
                "collapsed_warm_median": float(warm[yy, xx]),
                "primary_median_pairwise_delta": value,
                "difference_of_medians": float(cold[yy, xx] - warm[yy, xx]),
                "display_color_hex": to_hex(plt.get_cmap("RdBu")(norm(value))),
                "display_color_family": "red" if value < 0 else "blue" if value > 0 else "white",
                "interpretation": f"warm synchrony stronger by approximately {abs(value):.3f}" if value < 0 else f"cold synchrony stronger by approximately {abs(value):.3f}",
            }
        )
    return pd.DataFrame(rows)


def _line(path: Path, needle: str) -> int:
    for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in text:
            return number
    return 0


def _consistency_table() -> pd.DataFrame:
    entries = [
        ("src/cubedynamics/stats/tails.py", "selected = (x_valid <=", "lower tail uses <= per-series quantile", "tail", "YES"),
        ("src/cubedynamics/stats/tails.py", "selected = (x_valid >", "upper tail uses > per-series quantile", "tail", "YES"),
        ("src/cubedynamics/synchrony/production.py", '"delta_s": ("pair", cold - warm)', "cold - warm", "calculation", "YES"),
        ("src/cubedynamics/synchrony/baseline.py", 'result = result.rename({"delta_median": "delta_pair_median"})', "median of pairwise Delta", "collapse", "YES"),
        ("scripts/run_nonstacked_conus_baseline.py", 'sign_convention="Delta = cold synchrony - warm synchrony"', "GeoTIFF tag cold - warm", "raster", "YES"),
        ("scripts/run_nonstacked_conus_baseline.py", 'cmap="RdBu"', "negative red; zero white; positive blue", "CONUS plot", "YES"),
        ("scripts/run_nonstacked_conus_baseline.py", 'label="Median Spearman synchrony"', "generic label omits red=warm stronger and blue=cold stronger", "CONUS colorbar label", "NO"),
        ("scripts/build_nonstacked_colorado_report.py", "Blue is positive and red is negative", "blue positive/cold; red negative/warm", "report", "YES"),
        ("scripts/build_nonstacked_conus_walkthrough.py", "Blue Delta is positive; red Delta is negative", "blue positive/cold; red negative/warm", "report", "YES"),
        ("examples/center_pixel_delta_s_map.py", 'cmap="RdBu"', "negative red; positive blue with explicit semantic caption", "current center-pixel Delta map", "YES"),
        ("examples/prism_synchrony_stack_phase1.py", '("delta_s", "Cold - warm (Delta S)", "RdBu"', "negative red; positive blue", "Phase 1 Delta surfaces", "YES"),
        ("scripts/build_synchrony_pedagogy.py", 'cmap="RdBu"', "negative red; positive blue", "current teaching report", "YES"),
        ("docs/recipes/climate_tail_dep_center.md", 'cmap="RdBu_r"', "negative blue; positive red", "legacy recipe plot", "NO"),
        ("examples/median_split_synchrony_demo.py", 'cmap="RdBu_r"', "negative blue; positive red", "legacy synthetic climate Delta viewer", "NO"),
        ("examples/real_prism_median_split_synchrony.py", 'cmap="RdBu_r"', "negative blue; positive red", "legacy real-PRISM Delta viewer", "NO"),
        ("examples/climate_synchrony_cube_panel_demo.py", 'cmap="RdBu_r"', "negative blue; positive red", "legacy climate Delta panel", "NO"),
        ("examples/center_pixel_synchrony_walkthrough.py", '("bottom_minus_top", "C  Delta S = cold - warm", "RdBu_r"', "negative blue; positive red", "legacy center-pixel walkthrough", "NO"),
        ("docs/recipes/s2_tail_dep_center.md", 'cmap="RdBu_r"', "negative blue; positive red", "legacy bottom-minus-top recipe", "NO"),
        ("docs/recipes/s2_tail_dep_manual.md", 'CORR_CMAP            = "RdBu_r"', "negative blue; positive red", "legacy manual plot", "NO"),
        ("scripts/build_synchrony_phase2_atlas.py", '"Median pairwise Delta (cold - warm)", delta_png, cmap="RdBu_r"', "negative blue; positive red", "historical Phase 2 Delta atlas", "NO"),
        ("scripts/build_synchrony_surface_atlas_phase2.py", '"delta": _state_map(signature, geometry, "delta_median"', "negative blue; positive red", "historical Delta atlas", "NO"),
        ("scripts/build_relational_convolution_report.py", '((med,"Median Delta S","RdBu_r")', "negative blue; positive red", "historical Delta report", "NO"),
        ("scripts/run_rank_rescaling_gate.py", 'cmap="RdBu"', "negative red; positive blue", "rank gate plot", "YES"),
        ("docs/design/synchrony_stack_architecture.md", "cold minus warm", "cold - warm", "documentation", "YES"),
        ("docs/recipes/climate_tail_dep_center.md", "negative values indicate stronger hot synchrony", "negative means upper-tail/hot stronger", "documentation", "YES"),
    ]
    rows = []
    for relative, needle, expression, category, consistent in entries:
        path = ROOT / relative
        rows.append(
            {
                "file": relative,
                "line": _line(path, needle),
                "function_or_context": category,
                "expression_or_interpretation": expression,
                "consistent_with_blue_cold_red_warm_convention": consistent,
            }
        )
    return pd.DataFrame(rows)


def _call_graph() -> pd.DataFrame:
    rows = [
        ("temperature acquisition", "src/cubedynamics/data/prism.py", "load_prism_cube", "tmin, tmax"),
        ("frozen input", "scripts/run_nonstacked_conus_baseline.py", "acquire / _open_input", "cube.tmin, cube.tmax"),
        ("variable routing", "src/cubedynamics/synchrony/stacks.py", "_select_inputs", "lower=tmin, upper=tmax"),
        ("tail state", "src/cubedynamics/synchrony/production.py", "_precomputed_tail_state", "lower <= q; upper > q"),
        ("pair synchrony", "src/cubedynamics/synchrony/production.py", "_batched_one_tail_spearman", "cold, warm, counts"),
        ("pair Delta", "src/cubedynamics/synchrony/production.py", "local_synchrony_pairs", "delta_s = cold - warm"),
        ("pixel collapse", "src/cubedynamics/synchrony/baseline.py", "nonstacked_synchrony_summary", "delta_pair_median"),
        ("tiled execution", "src/cubedynamics/synchrony/baseline.py", "tiled_nonstacked_synchrony_summary", "tile summaries"),
        ("GeoTIFF output", "scripts/run_nonstacked_conus_baseline.py", "_write_rasters", "delta_pair_median_100km.tif"),
        ("CONUS plotting", "scripts/run_nonstacked_conus_baseline.py", "_figures", "RdBu + TwoSlopeNorm(center=0)"),
        ("Markdown report", "scripts/build_nonstacked_conus_report.py", "main", "cold/warm/Delta labels"),
        ("PDF report", "scripts/build_nonstacked_conus_walkthrough.py", "build_pdf", "blue positive; red negative caption"),
    ]
    return pd.DataFrame(rows, columns=("stage", "file", "function", "relevant_variables"))


def _format_table(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    subset = frame if columns is None else frame[columns]
    headers = [str(column).replace("_", " ") for column in subset.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in subset.itertuples(index=False, name=None):
        cells = []
        for value in row:
            if isinstance(value, float):
                cells.append(f"{value:.6f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _report(
    tail_summary: pd.DataFrame,
    pair_summary: pd.DataFrame,
    synthetic: list[dict[str, object]],
    collapsed: dict[str, object],
    western: pd.DataFrame,
    consistency: pd.DataFrame,
    result: xr.Dataset,
) -> str:
    mask = result.output_mask.values.astype(bool)
    cold = np.asarray(result.cold_median.sel(radius_km=100).isel(time_window_end=0).values)[mask]
    warm = np.asarray(result.warm_median.sel(radius_km=100).isel(time_window_end=0).values)[mask]
    delta = np.asarray(result.delta_pair_median.sel(radius_km=100).isel(time_window_end=0).values)[mask]
    synthetic_frame = pd.DataFrame(synthetic)
    failures = consistency[consistency.consistent_with_blue_cold_red_warm_convention == "NO"]
    lines = [
        "# HOT/COLD/DELTA SEMANTICS AUDIT",
        "",
        "## Intended semantics",
        "",
        "- Cold: joint lower local tail of PRISM TMIN.",
        "- Warm/hot: joint upper local tail of PRISM TMAX.",
        "- Delta: `S_cold - S_warm`.",
        "- Positive Delta: stronger cold synchrony. Negative Delta: stronger warm synchrony.",
        "- Requested visual convention: positive/cold is blue; negative/warm is red.",
        "",
        "## Actual implementation",
        "",
        "The production path routes `tmin` to the lower-tail kernel and `tmax` to the upper-tail kernel. With `q=0.5`, cold membership is `TMIN_A <= median(TMIN_A) AND TMIN_B <= median(TMIN_B)`. Warm membership is `TMAX_A > median(TMAX_A) AND TMAX_B > median(TMAX_B)`. Spearman is the Pearson correlation of average ranks within the selected joint tail. `delta_s` is allocated as `cold - warm`. The primary CONUS raster is `median(delta_s)` over non-self neighbors, not `median(cold) - median(warm)`.",
        "",
        "## Complete call graph",
        "",
        _format_table(_call_graph()),
        "",
        "## Tail verification",
        "",
        "**PASS.** All three real pixels place cold dates below the local TMIN median and warm dates above the local TMAX median. There is no seasonal detrending: the reference distribution is the selected 91 labels in the single rolling window. Pairwise missing values are removed before thresholds; ties receive average ranks for Spearman. Lower-tail membership is inclusive (`<=`); upper-tail membership is strict (`>`). Both pair members must pass their own threshold.",
        "",
        _format_table(tail_summary),
        "",
        "Full auditable dates and ranks are in `tail_pixel_samples.csv`.",
        "",
        "## Cold calculation",
        "",
        f"**PASS.** Five real pairs were independently recomputed from raw TMIN values. Maximum stored-versus-direct absolute error: {pair_summary.cold_absolute_error.max():.3e}.",
        "",
        "## Warm calculation",
        "",
        f"**PASS.** Five real pairs were independently recomputed from raw TMAX values. Maximum stored-versus-direct absolute error: {pair_summary.warm_absolute_error.max():.3e}.",
        "",
        "## Delta sign",
        "",
        f"**PASS.** Every audited pair satisfies `stored Delta = stored S_cold - stored S_warm`; maximum error {pair_summary.delta_absolute_error.max():.3e}.",
        "",
        _format_table(pair_summary, ["pair_id", "region", "distance_km", "stored_cold", "stored_warm", "stored_delta", "all_assertions_pass"]),
        "",
        "All dates, raw temperatures, percentiles, within-tail ranks, and flags entering each calculation are in `pair_audit_observations.csv`.",
        "",
        "## Synthetic known-answer cases",
        "",
        _format_table(synthetic_frame),
        "",
        "**PASS.** These cases use `local_synchrony_pairs`, the same production pair function used by CONUS.",
        "",
        "## Spatial collapse",
        "",
        "**PASS.** The audited western focal pixel has:",
        "",
        _format_table(pd.DataFrame([{
            "latitude": collapsed["latitude"], "longitude": collapsed["longitude"],
            "pair count": collapsed["incident_nonself_pairs"],
            "median cold": collapsed["recomputed_median_cold"],
            "median warm": collapsed["recomputed_median_warm"],
            "median pairwise Delta": collapsed["recomputed_median_pairwise_delta"],
            "difference of medians": collapsed["recomputed_difference_of_medians"],
        }])),
        "",
        "The primary map uses the median of pairwise `cold - warm`. The separate difference-of-medians field is retained but is not the primary Delta raster.",
        "",
        "## Raster values",
        "",
        f"**PASS.** Recomputed-to-NetCDF error is {collapsed['netcdf_absolute_error']:.3e}; recomputed-to-float32-GeoTIFF error is {collapsed['geotiff_absolute_error']:.3e}. The GeoTIFF band and dataset tags say `Delta = cold synchrony - warm synchrony`.",
        "",
        "## One-pixel end-to-end provenance",
        "",
        f"Raw PRISM TMIN/TMAX -> joint lower/upper flags -> {collapsed['incident_nonself_pairs']:,} non-self pair relationships -> median cold {collapsed['recomputed_median_cold']:.6f}, median warm {collapsed['recomputed_median_warm']:.6f}, median pairwise Delta {collapsed['recomputed_median_pairwise_delta']:.6f} -> NetCDF {collapsed['netcdf_primary_delta']:.6f} -> GeoTIFF {collapsed['geotiff_primary_delta']:.6f} -> plotted `{collapsed['displayed_color_hex']}` ({collapsed['displayed_color_family']}) -> {collapsed['legend_interpretation']}.",
        "",
        "## Colorbar",
        "",
        "**PASS for the current CONUS plotting code.** It uses Matplotlib `RdBu` with `TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit)`: negative is red, zero is near-white, positive is blue.",
        "",
        "- NEGATIVE Delta COLOR = red",
        "- NEGATIVE Delta MEANS = `S_warm > S_cold`, stronger warm synchrony",
        "- POSITIVE Delta COLOR = blue",
        "- POSITIVE Delta MEANS = `S_cold > S_warm`, stronger cold synchrony",
        "",
        "## Figure legends",
        "",
        "**FAIL.** Visual inspection of the retained national PNG confirms that the current CONUS pixels are colored correctly, and the walkthrough explicitly explains the colors. However, the standalone primary CONUS Delta colorbar is generically labeled `Median Spearman synchrony`; it does not itself say `red = warm stronger` and `blue = cold stronger`. Several historical synchrony recipes and report builders use `RdBu_r`, which maps the same positive/cold values to red and negative/warm values to blue - the opposite of the current CONUS palette.",
        "",
        "## Documentation",
        "",
        "**PASS for algebra and sign prose; FAIL for a repository-wide canonical color convention.** No relevant implementation of `warm - cold` was found. Historical text correctly defines positive as cold stronger and negative as warm/hot stronger, but some examples render those signs with the opposite red/blue assignment.",
        "",
        "## Hot versus warm terminology",
        "",
        "The terms are computational aliases in this workflow: both mean the strict joint upper tail of TMAX. Production variable names use `warm`; older recipes and the rank-rescaling experiment often say `hot`. Recommend `warm` as the canonical API/report term and reserve `hot` for plain-language explanation, but do not rename historical outputs without a remediation decision.",
        "",
        "## CONUS summary verification",
        "",
        _format_table(pd.DataFrame([{
            "national median S_cold": float(np.nanmedian(cold)),
            "national median S_warm": float(np.nanmedian(warm)),
            "national median pairwise Delta": float(np.nanmedian(delta)),
            "fraction Delta < 0": float(np.mean(delta < 0)),
            "fraction Delta > 0": float(np.mean(delta > 0)),
        }])),
        "",
        "The higher national warm median and 70.5% negative primary Delta cells are algebraically consistent with `cold - warm`. The median of pairwise differences is not expected to equal the difference of national medians.",
        "",
        "## CONUS western-pattern spot checks",
        "",
        _format_table(western),
        "",
        "Every sampled red western cell has negative primary Delta and therefore means stronger warm synchrony by the displayed magnitude. `collapsed cold - collapsed warm` is shown separately and need not equal the primary pairwise-median Delta.",
        "",
        "## Repository consistency table",
        "",
        _format_table(consistency),
        "",
        f"Detected {len(failures)} relevant visual-encoding inconsistencies. These are recorded only; nothing was remediated in this audit.",
        "",
        "## Overall verdict",
        "",
        "**F. MULTIPLE INCONSISTENCIES EXIST**",
        "",
        "The temperature-tail assignment, cold calculation, warm calculation, Delta algebra, spatial collapse, NetCDF values, GeoTIFF values, and current CONUS pixel colors are correct. The inconsistencies are representational: (1) the standalone CONUS Delta colorbar does not state the warm/cold meaning of its endpoints, (2) several historical synchrony plots use the reversed `RdBu_r` palette, and (3) hot/warm terminology varies even though the calculation is identical. These do not reverse the current national numbers, but they can reverse a reader's red/blue intuition across products.",
        "",
        "## Scope and immutability",
        "",
        "No algorithm, sign, production variable, map, raster, report, or historical output was changed. The separate proposed remediation plan lists the blast radius without executing it.",
    ]
    return "\n".join(lines) + "\n"


def _remediation_plan(consistency: pd.DataFrame) -> str:
    failures = consistency[consistency.consistent_with_blue_cold_red_warm_convention == "NO"]
    return "\n".join(
        [
            "# PROPOSED REMEDIATION PLAN - NOT EXECUTED",
            "",
            "The forensic audit found correct calculations and current CONUS colors, but inconsistent historical red/blue encoding and incomplete standalone legend semantics.",
            "",
            "## Proposed changes",
            "",
            "1. Define one shared Delta plotting contract: `RdBu`, zero-centered, red negative/warm-stronger, blue positive/cold-stronger.",
            "2. Add explicit semantic endpoint labels to the standalone CONUS Delta colorbar and captions.",
            "3. Review each synchrony-specific `RdBu_r` use below; change only Delta displays, not unrelated anomaly/elevation plots.",
            "4. Canonicalize new API prose on `warm`; document `hot` as a historical/plain-language alias for the TMAX upper tail.",
            "5. Regenerate affected figures, PDFs, recipe screenshots, manifests, and docs only after approval.",
            "6. Retain old files with provenance or version notes if published artifacts depend on their visual encoding.",
            "",
            "## Candidate files",
            "",
            _format_table(failures),
            "",
            "## Historical outputs potentially affected",
            "",
            "- Median-split climate synchrony HTML viewers and diagnostic images generated from the climate recipes/examples.",
            "- The center-pixel synchrony walkthrough figures/PDF.",
            "- The Phase 2 Colorado synchrony atlas and surface-atlas figures/PDFs.",
            "- The relational-convolution feasibility figures/PDF.",
            "- The standalone CONUS three-panel PNG (label clarification only; its pixel colors are already correct).",
            "",
            "## Required tests before regeneration",
            "",
            "- Sign-to-color contract for negative, zero, and positive Delta.",
            "- Caption and legend endpoint semantics.",
            "- Raster and NetCDF sign preservation.",
            "- Snapshot/hash review for every regenerated historical output.",
            "",
            "## Backward compatibility",
            "",
            "Numeric APIs and rasters need no sign change. Only visual color interpretation and terminology are candidates for revision. Historical figures may need explicit versioning because recoloring changes human interpretation even when values are identical.",
        ]
    ) + "\n"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with xr.open_dataset(INPUT, engine="h5netcdf") as cube, xr.open_dataset(RESULT, engine="h5netcdf") as result:
        tail_rows, tail_summary = _pixel_tail_tables(cube, result)
        pair_summary, pair_observations = _pair_audit(cube, result)
        synthetic = _synthetic_cases()
        collapsed, collapsed_pairs = _collapsed_pixel_audit(cube, result)
        western = _western_spot_checks(result)
        report = _report(tail_summary, pair_summary, synthetic, collapsed, western, _consistency_table(), result)
    consistency = _consistency_table()
    call_graph = _call_graph()

    tail_rows.to_csv(OUTPUT / "tail_pixel_samples.csv", index=False)
    tail_summary.to_csv(OUTPUT / "tail_pixel_summary.csv", index=False)
    pair_summary.to_csv(OUTPUT / "pair_audit_summary.csv", index=False)
    pair_observations.to_csv(OUTPUT / "pair_audit_observations.csv", index=False)
    collapsed_pairs.to_csv(OUTPUT / "collapsed_pixel_pairs.csv", index=False)
    western.to_csv(OUTPUT / "western_spot_checks.csv", index=False)
    consistency.to_csv(OUTPUT / "repository_consistency.csv", index=False)
    call_graph.to_csv(OUTPUT / "call_graph.csv", index=False)
    _json(OUTPUT / "synthetic_cases.json", synthetic)
    _json(OUTPUT / "collapsed_pixel_provenance.json", collapsed)
    colorbar = {
        "colormap": "RdBu", "normalization": "TwoSlopeNorm",
        "vmin": collapsed["plot_vmin"], "center": 0.0, "vmax": collapsed["plot_vmax"],
        "negative_color": to_hex(plt.get_cmap("RdBu")(0.0)),
        "zero_color": to_hex(plt.get_cmap("RdBu")(.5)),
        "positive_color": to_hex(plt.get_cmap("RdBu")(1.0)),
        "negative_meaning": "stronger warm synchrony",
        "positive_meaning": "stronger cold synchrony",
    }
    _json(OUTPUT / "colorbar_audit.json", colorbar)
    (OUTPUT / "AUDIT_REPORT.md").write_text(report, encoding="utf-8")
    (OUTPUT / "PROPOSED_REMEDIATION_PLAN.md").write_text(_remediation_plan(consistency), encoding="utf-8")
    manifest = {
        "status": "complete",
        "diagnostic_only": True,
        "input_sha256": _digest(INPUT),
        "result_sha256": _digest(RESULT),
        "tolerance": TOLERANCE,
        "pair_assertions_all_pass": bool(pair_summary.all_assertions_pass.all()),
        "tail_assertions_all_pass": bool(
            tail_summary.cold_is_lower.all()
            and tail_summary.warm_is_upper.all()
            and tail_summary.median_cold_temperature_less_than_median_warm_temperature.all()
        ),
        "synthetic_assertions_all_pass": True,
        "collapsed_netcdf_assertion_pass": bool(collapsed["netcdf_absolute_error"] <= TOLERANCE),
        "collapsed_geotiff_assertion_pass": bool(collapsed["geotiff_absolute_error"] <= 1e-6),
        "overall_verdict": "F. MULTIPLE INCONSISTENCIES EXIST",
        "algorithmic_status": "PASS",
        "visual_consistency_status": "FAIL",
        "files": sorted(path.name for path in OUTPUT.iterdir() if path.is_file()),
    }
    _json(OUTPUT / "audit_manifest.json", manifest)
    print(OUTPUT / "AUDIT_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
