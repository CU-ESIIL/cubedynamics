#!/usr/bin/env python3
"""Validate the non-stacked CONUS synchrony map with real GHCN-Daily stations.

The comparison has three levels: daily station versus nearest-PRISM values,
station-pair versus matched PRISM-pixel synchrony, and incident station-edge
medians versus the final collapsed CONUS raster.  It is observational
agreement, not a claim of strict independence: exact PRISM station-ingestion
membership is unavailable for the selected date window.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
import xarray as xr

from cubedynamics.stats.tails import one_tail_spearman


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "nonstacked-conus-baseline" / "station_validation"
PRISM = ROOT / "artifacts" / "nonstacked-conus-baseline" / "inputs" / "prism_conus_20231101_20240130.nc"
MAP = ROOT / "artifacts" / "nonstacked-conus-baseline" / "conus_nonstacked_synchrony.nc"
METADATA = ROOT / "artifacts" / "relational-convolution-feasibility" / "station_raw"
START = "2023-11-01"
END = "2024-01-30"
BBOX = (24.0, -124.75, 50.0, -66.5)
DATA_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
METADATA_URL = "https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily"
MAXIMUM_PAIR_DISTANCE_KM = 100.0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("acquire", "analyze", "all"), default="all")
    parser.add_argument("--candidate-count", type=int, default=1800)
    parser.add_argument("--station-count", type=int, default=1500)
    parser.add_argument("--batch-size", type=int, default=60)
    parser.add_argument("--download-workers", type=int, default=3)
    parser.add_argument("--minimum-completeness", type=float, default=.80)
    parser.add_argument("--minimum-neighbors", type=int, default=3)
    parser.add_argument("--bootstrap-replicates", type=int, default=500)
    return parser


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stations(path: Path) -> pd.DataFrame:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = {
                "station_id": line[:11], "latitude": float(line[12:20]),
                "longitude": float(line[21:30]), "elevation_m": float(line[31:37]),
                "state": line[38:40].strip(), "station_name": line[41:71].strip(),
                "gsn_flag": line[72:75].strip(), "hcn_flag": line[76:79].strip(),
                "wmo_id": line[80:85].strip(),
            }
        except ValueError:
            continue
        if (
            row["station_id"].startswith("US")
            and BBOX[0] <= row["latitude"] <= BBOX[2]
            and BBOX[1] <= row["longitude"] <= BBOX[3]
            and row["state"] not in {"AK", "HI", "AS", "GU", "MP", "PR", "VI"}
        ):
            rows.append(row)
    return pd.DataFrame(rows).set_index("station_id")


def _inventory(path: Path, ids: set[str]) -> pd.DataFrame:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        station_id = line[:11]
        element = line[31:35]
        if station_id in ids and element in {"TMIN", "TMAX"}:
            rows.append(
                {"station_id": station_id, "element": element,
                 "first_year": int(line[36:40]), "last_year": int(line[41:45])}
            )
    return pd.DataFrame(rows)


def _unit_xyz(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat = np.deg2rad(latitude); lon = np.deg2rad(longitude)
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


def _maximin(frame: pd.DataFrame, count: int, score: pd.Series | None = None) -> pd.DataFrame:
    """Memory-bounded farthest-point selection over candidate stations."""
    if frame.shape[0] <= count:
        return frame.copy()
    xyz = _unit_xyz(frame.latitude.to_numpy(float), frame.longitude.to_numpy(float))
    center = _unit_xyz(np.asarray([frame.latitude.mean()]), np.asarray([frame.longitude.mean()]))[0]
    first = int(np.argmax(xyz @ center))
    selected = [first]
    minimum = np.linalg.norm(xyz - xyz[first], axis=1)
    quality = np.ones(frame.shape[0]) if score is None else score.reindex(frame.index).fillna(0).to_numpy(float)
    quality = .75 + .25 * quality / max(float(np.nanmax(quality)), 1.0)
    while len(selected) < count:
        adjusted = minimum * quality
        adjusted[selected] = -1
        index = int(np.argmax(adjusted))
        selected.append(index)
        minimum = np.minimum(minimum, np.linalg.norm(xyz - xyz[index], axis=1))
    return frame.iloc[selected].copy()


def choose_candidates(count: int) -> pd.DataFrame:
    stations_path = METADATA / "ghcnd-stations.txt"
    inventory_path = METADATA / "ghcnd-inventory.txt"
    if not stations_path.exists() or not inventory_path.exists():
        raise FileNotFoundError("The retained official GHCN station and inventory files are missing")
    stations = _stations(stations_path)
    inventory = _inventory(inventory_path, set(stations.index))
    eligible = []
    for station_id, group in inventory.groupby("station_id"):
        if set(group.element) == {"TMIN", "TMAX"} and group.first_year.min() <= 2023 and group.last_year.min() >= 2024:
            eligible.append(station_id)
    return _maximin(stations.loc[sorted(eligible)], count)


def download_batches(candidates: pd.DataFrame, *, batch_size: int, workers: int) -> list[dict[str, object]]:
    batch_dir = OUTPUT / "station_raw" / "batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    ids = candidates.index.tolist()
    jobs = []
    for number, start in enumerate(range(0, len(ids), batch_size)):
        station_ids = ids[start : start + batch_size]
        target = batch_dir / f"ghcn_daily_batch_{number:03d}.csv"
        query = {
            "dataset": "daily-summaries", "stations": ",".join(station_ids),
            "startDate": START, "endDate": END, "format": "csv", "units": "metric",
            "includeAttributes": "true", "includeStationName": "true", "includeStationLocation": "true",
        }
        url = f"{DATA_URL}?{urlencode(query)}"
        jobs.append((number, station_ids, target, url))

    def fetch(job):
        number, station_ids, target, url = job
        if not target.exists():
            request = Request(url, headers={"User-Agent": "CubeDynamics-CONUS-station-validation/0.1"})
            with urlopen(request, timeout=240) as response:
                payload = response.read()
            if len(payload) < 100 or b"STATION" not in payload[:500]:
                raise RuntimeError(f"Unexpected GHCN response for batch {number}")
            temporary = target.with_suffix(".partial.csv")
            temporary.write_bytes(payload); temporary.replace(target)
        return {"batch": number, "station_count": len(station_ids), "path": str(target.relative_to(ROOT)),
                "sha256": _digest(target), "bytes": target.stat().st_size}

    records = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(fetch, job): job[0] for job in jobs}
        for future in as_completed(pending):
            record = future.result(); records.append(record)
            print(f"GHCN batch {record['batch'] + 1}/{len(jobs)}: {record['bytes']:,} bytes", flush=True)
    return sorted(records, key=lambda item: item["batch"])


def _attributes(value: object) -> tuple[str, str, str, str]:
    if pd.isna(value):
        return "", "", "", ""
    parts = str(value).split(",") + [""] * 4
    return tuple(parts[:4])  # type: ignore[return-value]


def clean_daily(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    expected = pd.date_range(START, END, freq="D").size
    records = []; manifest = []
    for station_id, group in raw.groupby("STATION"):
        item = {
            "station_id": station_id, "station_name": str(group.NAME.iloc[0]),
            "latitude": float(group.LATITUDE.iloc[0]), "longitude": float(group.LONGITUDE.iloc[0]),
            "elevation_m": float(group.ELEVATION.iloc[0]), "expected_day_count": expected,
            "network_source": "NOAA/NCEI GHCN-Daily",
            "prism_contribution_status": "UNKNOWN",
        }
        for variable in ("TMIN", "TMAX"):
            values = pd.to_numeric(group.get(variable), errors="coerce")
            attributes = group.get(f"{variable}_ATTRIBUTES", pd.Series(index=group.index, dtype=object))
            parsed = [_attributes(value) for value in attributes]
            quality = np.asarray([value[1] for value in parsed], dtype=object)
            valid = values.notna().to_numpy() & (quality == "")
            item[f"{variable.lower()}_reported_count"] = int(values.notna().sum())
            item[f"{variable.lower()}_qc_exclusion_count"] = int(np.count_nonzero(values.notna().to_numpy() & ~valid))
            item[f"{variable.lower()}_valid_count"] = int(valid.sum())
            item[f"{variable.lower()}_completeness"] = float(valid.sum() / expected)
            item[f"{variable.lower()}_source_flags"] = ",".join(sorted({p[2] for p, keep in zip(parsed, valid) if keep and p[2]}))
            item[f"{variable.lower()}_observation_time_known_count"] = int(sum(bool(p[3]) for p, keep in zip(parsed, valid) if keep))
            for (_, row), keep, flags in zip(group.iterrows(), valid, parsed):
                records.append(
                    {"station_id": station_id, "date": str(row.DATE), "variable": variable,
                     "value_c": float(row[variable]) if keep else np.nan,
                     "measurement_flag": flags[0], "quality_flag": flags[1],
                     "source_flag": flags[2], "observation_time_local": flags[3], "qc_valid": bool(keep)}
                )
        manifest.append(item)
    return pd.DataFrame(records), pd.DataFrame(manifest)


def _agreement(observed: np.ndarray, modeled: np.ndarray) -> dict[str, float | int]:
    valid = np.isfinite(observed) & np.isfinite(modeled)
    a = observed[valid]; b = modeled[valid]
    if a.size < 3:
        return {"n": int(a.size), "bias": np.nan, "mae": np.nan, "rmse": np.nan, "pearson": np.nan, "spearman": np.nan}
    return {
        "n": int(a.size), "bias": float(np.mean(b - a)), "mae": float(np.mean(np.abs(b - a))),
        "rmse": float(np.sqrt(np.mean((b - a) ** 2))), "pearson": float(np.corrcoef(a, b)[0, 1]),
        "spearman": float(spearmanr(a, b).statistic),
    }


def _haversine(lat1, lon1, lat2, lon2) -> np.ndarray:
    p1 = np.deg2rad(lat1); p2 = np.deg2rad(lat2)
    dl = np.deg2rad(lon2 - lon1); dp = p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 6371.0088 * 2 * np.arctan2(np.sqrt(a), np.sqrt(np.maximum(0, 1 - a)))


def _block_bootstrap(frame: pd.DataFrame, observed: str, modeled: str, *, replicates: int) -> dict[str, object]:
    valid = frame[["block", observed, modeled]].dropna()
    groups = {name: group for name, group in valid.groupby("block")}
    names = np.asarray(sorted(groups))
    rng = np.random.default_rng(20240924)
    values = {name: [] for name in ("bias", "mae", "rmse", "pearson", "spearman")}
    for _ in range(replicates):
        sampled = rng.choice(names, size=names.size, replace=True)
        rows = pd.concat([groups[name] for name in sampled], ignore_index=True)
        metric = _agreement(rows[observed].to_numpy(float), rows[modeled].to_numpy(float))
        for name in values:
            values[name].append(float(metric[name]))
    return {
        "spatial_block_degrees": 5, "block_count": int(names.size), "replicates": replicates,
        "confidence_intervals_95": {
            name: [float(np.nanquantile(item, .025)), float(np.nanquantile(item, .975))]
            for name, item in values.items()
        },
    }


def analyze(candidates: pd.DataFrame, args) -> None:
    if not PRISM.exists() or not MAP.exists():
        raise FileNotFoundError("Run the CONUS PRISM acquisition and map analysis before station validation")
    batch_paths = sorted((OUTPUT / "station_raw" / "batches").glob("ghcn_daily_batch_*.csv"))
    if not batch_paths:
        raise FileNotFoundError("No station batches; rerun with --download")
    raw = pd.concat((pd.read_csv(path, low_memory=False) for path in batch_paths), ignore_index=True)
    clean, manifest = clean_daily(raw)
    manifest = manifest.merge(candidates.reset_index(), on="station_id", how="inner", suffixes=("", "_meta"))
    qualified = manifest[
        (manifest.tmin_completeness >= args.minimum_completeness)
        & (manifest.tmax_completeness >= args.minimum_completeness)
    ].copy()
    qualified["selection_score"] = qualified[["tmin_completeness", "tmax_completeness"]].min(axis=1)
    selected = _maximin(
        qualified.set_index("station_id"), min(args.station_count, qualified.shape[0]),
        score=qualified.set_index("station_id").selection_score,
    ).reset_index()
    ids = selected.station_id.tolist()
    dates = pd.date_range(START, END, freq="D")
    station_values = {}
    for variable in ("TMIN", "TMAX"):
        subset = clean[(clean.variable == variable) & clean.station_id.isin(ids)].copy()
        subset["date"] = pd.to_datetime(subset.date)
        station_values[variable] = subset.pivot(index="date", columns="station_id", values="value_c").reindex(index=dates, columns=ids).to_numpy(float)

    with xr.open_dataset(PRISM, engine="h5netcdf") as cube:
        y = np.asarray(cube.y.values, dtype=float); x = np.asarray(cube.x.values, dtype=float)
        yi = np.abs(y[:, None] - selected.latitude.to_numpy(float)).argmin(axis=0)
        xi = np.abs(x[:, None] - selected.longitude.to_numpy(float)).argmin(axis=0)
        y_index = xr.DataArray(yi, dims="station", coords={"station": ids})
        x_index = xr.DataArray(xi, dims="station", coords={"station": ids})
        prism_values = {
            "TMIN": np.asarray(cube.tmin.isel(y=y_index, x=x_index).transpose("time", "station").values, dtype=float),
            "TMAX": np.asarray(cube.tmax.isel(y=y_index, x=x_index).transpose("time", "station").values, dtype=float),
        }
        selected["prism_y_index"] = yi; selected["prism_x_index"] = xi
        selected["prism_latitude"] = y[yi]; selected["prism_longitude"] = x[xi]
        selected["station_to_pixel_center_km"] = _haversine(selected.latitude, selected.longitude, y[yi], x[xi])

    raw_rows = []
    for variable in ("TMIN", "TMAX"):
        for shift in (-1, 0, 1):
            shifted = np.full_like(prism_values[variable], np.nan)
            if shift < 0: shifted[-shift:] = prism_values[variable][:shift]
            elif shift > 0: shifted[:-shift] = prism_values[variable][shift:]
            else: shifted[:] = prism_values[variable]
            for index, station_id in enumerate(ids):
                raw_rows.append({"station_id": station_id, "variable": variable, "prism_label_shift_days": shift, **_agreement(station_values[variable][:, index], shifted[:, index])})
    raw_comparison = pd.DataFrame(raw_rows)

    xyz = _unit_xyz(selected.latitude.to_numpy(float), selected.longitude.to_numpy(float))
    chord = 2 * np.sin((MAXIMUM_PAIR_DISTANCE_KM / 6371.0088) / 2)
    edges = cKDTree(xyz).query_pairs(chord, output_type="ndarray")
    pair_rows = []
    for left, right in edges:
        if yi[left] == yi[right] and xi[left] == xi[right]:
            continue
        sc, scn = one_tail_spearman(station_values["TMIN"][:, left], station_values["TMIN"][:, right], tail="lower", min_t=10)
        sw, swn = one_tail_spearman(station_values["TMAX"][:, left], station_values["TMAX"][:, right], tail="upper", min_t=10)
        pc, pcn = one_tail_spearman(prism_values["TMIN"][:, left], prism_values["TMIN"][:, right], tail="lower", min_t=10)
        pw, pwn = one_tail_spearman(prism_values["TMAX"][:, left], prism_values["TMAX"][:, right], tail="upper", min_t=10)
        pair_rows.append(
            {"station_i": ids[left], "station_j": ids[right],
             "distance_km": float(_haversine(selected.latitude.iloc[left], selected.longitude.iloc[left], selected.latitude.iloc[right], selected.longitude.iloc[right])),
             "station_cold": sc, "station_warm": sw, "station_delta": sc - sw,
             "prism_cold": pc, "prism_warm": pw, "prism_delta": pc - pw,
             "station_cold_valid_n": scn, "station_warm_valid_n": swn,
             "prism_cold_valid_n": pcn, "prism_warm_valid_n": pwn,
             "prism_contribution_status": "UNKNOWN"}
        )
    pairs = pd.DataFrame(pair_rows)

    incident = {station_id: [] for station_id in ids}
    for index, row in pairs.iterrows():
        incident[row.station_i].append(index); incident[row.station_j].append(index)
    collapsed_rows = []
    with xr.open_dataset(MAP, engine="h5netcdf") as mapped:
        for position, station_id in enumerate(ids):
            edge_index = incident[station_id]
            row = {"station_id": station_id, "neighbor_count": len(edge_index)}
            for name in ("cold", "warm", "delta"):
                values = pairs.loc[edge_index, f"station_{name}"].to_numpy(float) if edge_index else np.asarray([])
                row[f"station_{name}_valid_pair_count"] = int(np.count_nonzero(np.isfinite(values)))
                row[f"station_{name}_median"] = float(np.nanmedian(values)) if np.isfinite(values).any() else np.nan
            for name, variable in (("cold", "cold_median"), ("warm", "warm_median"), ("delta", "delta_pair_median")):
                row[f"map_{name}_median"] = float(mapped[variable].sel(radius_km=100).isel(time_window_end=0, y=int(yi[position]), x=int(xi[position])).values)
            collapsed_rows.append(row)
    collapsed = selected.merge(pd.DataFrame(collapsed_rows), on="station_id")
    collapsed["block"] = (np.floor(collapsed.latitude / 5).astype(int).astype(str) + "_" + np.floor(collapsed.longitude / 5).astype(int).astype(str))
    collapsed["minimum_valid_pair_count"] = collapsed[
        [f"station_{name}_valid_pair_count" for name in ("cold", "warm", "delta")]
    ].min(axis=1)
    eligible = collapsed[collapsed.minimum_valid_pair_count >= args.minimum_neighbors].copy()

    pair_summary = {name: _agreement(pairs[f"station_{name}"].to_numpy(float), pairs[f"prism_{name}"].to_numpy(float)) for name in ("cold", "warm", "delta")}
    map_summary = {}
    for name in ("cold", "warm", "delta"):
        observed = f"station_{name}_median"; modeled = f"map_{name}_median"
        map_summary[name] = _agreement(eligible[observed].to_numpy(float), eligible[modeled].to_numpy(float))
        map_summary[name]["block_bootstrap"] = _block_bootstrap(eligible, observed, modeled, replicates=args.bootstrap_replicates)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    selected.to_csv(OUTPUT / "station_manifest.csv", index=False)
    clean[clean.station_id.isin(ids)].to_csv(OUTPUT / "station_daily_qc.csv.gz", index=False, compression="gzip")
    raw_comparison.to_csv(OUTPUT / "station_prism_daily_agreement.csv", index=False)
    pairs.to_csv(OUTPUT / "station_prism_pair_synchrony.csv", index=False)
    collapsed.to_csv(OUTPUT / "station_map_collapsed_agreement.csv", index=False)

    figure_dir = OUTPUT / "figures"; figure_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12.5, 6.5), constrained_layout=True)
    scatter = ax.scatter(selected.longitude, selected.latitude, c=collapsed.neighbor_count, s=14, cmap="viridis", vmin=0)
    ax.set(xlabel="Longitude", ylabel="Latitude", title=f"GHCN-Daily CONUS validation network: {len(selected):,} stations, {len(pairs):,} non-self edges <= 100 km")
    ax.set_aspect(1 / np.cos(np.deg2rad(37.5))); fig.colorbar(scatter, ax=ax, label="Neighbors within 100 km")
    network_path = figure_dir / "station_network.png"; fig.savefig(network_path, dpi=190, facecolor="white"); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)
    for ax, name in zip(axes, ("cold", "warm", "delta")):
        a = eligible[f"station_{name}_median"].to_numpy(float); b = eligible[f"map_{name}_median"].to_numpy(float)
        valid = np.isfinite(a) & np.isfinite(b); lo = min(float(np.nanmin(a[valid])), float(np.nanmin(b[valid]))); hi = max(float(np.nanmax(a[valid])), float(np.nanmax(b[valid])))
        ax.scatter(a[valid], b[valid], s=9, alpha=.45); ax.plot([lo, hi], [lo, hi], color="black", lw=.8)
        ax.set(xlabel=f"Station-neighborhood {name}", ylabel=f"PRISM-map {name}", title=f"{name.title()}  Spearman={map_summary[name]['spearman']:.2f}\nN={map_summary[name]['n']:,}; min neighbors={args.minimum_neighbors}")
    map_path = figure_dir / "collapsed_station_vs_map.png"; fig.savefig(map_path, dpi=190, facecolor="white"); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)
    for ax, name in zip(axes, ("cold", "warm", "delta")):
        a = pairs[f"station_{name}"].to_numpy(float); b = pairs[f"prism_{name}"].to_numpy(float); valid = np.isfinite(a) & np.isfinite(b)
        ax.hexbin(a[valid], b[valid], gridsize=32, mincnt=1, cmap="viridis"); ax.plot([-2, 2], [-2, 2], color="white", lw=.8)
        ax.set(xlim=(-1 if name != "delta" else -2, 1 if name != "delta" else 2), ylim=(-1 if name != "delta" else -2, 1 if name != "delta" else 2), xlabel=f"Station pair {name}", ylabel=f"Nearest-pixel pair {name}", title=f"{name.title()}  Spearman={pair_summary[name]['spearman']:.2f}\nN={pair_summary[name]['n']:,}")
    pair_path = figure_dir / "pair_station_vs_prism.png"; fig.savefig(pair_path, dpi=190, facecolor="white"); plt.close(fig)

    same_day = raw_comparison[raw_comparison.prism_label_shift_days == 0]
    daily_summary = {
        variable: {
            metric: float(same_day[same_day.variable == variable][metric].median())
            for metric in ("bias", "mae", "rmse", "pearson", "spearman")
        }
        for variable in ("TMIN", "TMAX")
    }
    temporal_shift_summary = {
        variable: {
            str(int(shift)): {
                metric: float(group[metric].median())
                for metric in ("mae", "pearson", "spearman")
            }
            for shift, group in raw_comparison[raw_comparison.variable == variable].groupby(
                "prism_label_shift_days"
            )
        }
        for variable in ("TMIN", "TMAX")
    }
    provenance = {
        "status": "complete", "analysis": "CONUS GHCN-Daily observational agreement for non-stacked synchrony baseline",
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "source": "NOAA/NCEI GHCN-Daily Daily Summaries",
        "source_metadata_url": METADATA_URL, "date_range": [START, END], "bbox_south_west_north_east": list(BBOX),
        "candidate_count": int(candidates.shape[0]), "qualified_count": int(qualified.shape[0]), "selected_count": int(selected.shape[0]),
        "minimum_completeness": args.minimum_completeness, "maximum_pair_distance_km": MAXIMUM_PAIR_DISTANCE_KM,
        "minimum_neighbors_for_map_comparison": args.minimum_neighbors,
        "map_comparison_support_definition": "minimum finite cold, warm, and Delta incident station-pair count",
        "pair_count": int(pairs.shape[0]),
        "eligible_collapsed_station_count": int(eligible.shape[0]), "quality_policy": "exclude nonnumeric values and every nonblank GHCN quality flag",
        "daily_same_label_station_median_metrics": daily_summary,
        "daily_temporal_shift_sensitivity": temporal_shift_summary,
        "pair_agreement": pair_summary, "collapsed_map_agreement": map_summary,
        "temporal_alignment": {"primary": "same date label", "sensitivity": "PRISM labels shifted -1, 0, and +1 days", "warning": "No silent date shift was applied."},
        "dependence_warning": "Pair edges share stations; pair rows are not independent. Spatial-block bootstrap is used only for collapsed station-map summaries.",
        "prism_independence_warning": "PRISM AN daily uses all ingested station networks. Exact membership for this period was unavailable, so GHCN agreement is not claimed as independent validation.",
        "sampling_warning": "Station-neighborhood medians use an irregular and much sparser graph than the raster's complete grid neighborhood.",
        "prism_input_sha256": _digest(PRISM), "map_sha256": _digest(MAP),
        "metadata_sha256": {"stations": _digest(METADATA / "ghcnd-stations.txt"), "inventory": _digest(METADATA / "ghcnd-inventory.txt")},
        "figures": [str(path.relative_to(ROOT)) for path in (network_path, map_path, pair_path)],
    }
    _json(OUTPUT / "validation_summary.json", provenance)
    with (OUTPUT / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("level", "metric", "n", "bias", "mae", "rmse", "pearson", "spearman")); writer.writeheader()
        for level, summary in (("pair", pair_summary), ("collapsed_map", map_summary)):
            for name, values in summary.items():
                writer.writerow({"level": level, "metric": name, **{key: values[key] for key in ("n", "bias", "mae", "rmse", "pearson", "spearman")}})


def main() -> int:
    args = _parser().parse_args()
    candidates = choose_candidates(args.candidate_count)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    candidates.reset_index().to_csv(OUTPUT / "candidate_stations.csv", index=False)
    if args.stage in {"acquire", "all"}:
        batches = download_batches(candidates, batch_size=args.batch_size, workers=args.download_workers)
        _json(OUTPUT / "station_raw" / "download_manifest.json", {"source": DATA_URL, "batches": batches})
    if args.stage in {"analyze", "all"}:
        analyze(candidates, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
