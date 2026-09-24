#!/usr/bin/env python3
"""Retrieve and evaluate a bounded GHCN-Daily station network for Phase 2.

The script freezes no method parameters from station performance.  It first
selects a spatially distributed candidate set from the official station and
inventory files, optionally downloads a bounded Daily Summaries CSV, applies
GHCN quality flags, and then evaluates already-frozen synchrony operators.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import rankdata

from cubedynamics.stats.tails import one_tail_spearman


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/relational-convolution-feasibility"
DEFAULT_PRISM = ROOT / "artifacts/synchrony-stack-phase2/prism_colorado_plus_100km_20231101_20240130.nc"
START = "2023-11-01"
END = "2024-01-30"
BBOX = (36.125, -110.208333, 41.875, -100.875)
METADATA_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
DATA_URL = "https://www.ncei.noaa.gov/access/services/data/v1"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prism", type=Path, default=DEFAULT_PRISM)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--candidate-count", type=int, default=60)
    parser.add_argument("--station-count", type=int, default=30)
    parser.add_argument("--minimum-completeness", type=float, default=0.70)
    parser.add_argument("--maximum-pair-distance-km", type=float, default=150.0)
    return parser


def _digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stations(path: Path) -> pd.DataFrame:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = {
                "station_id": line[:11],
                "latitude": float(line[12:20]),
                "longitude": float(line[21:30]),
                "elevation_m": float(line[31:37]),
                "state": line[38:40].strip(),
                "station_name": line[41:71].strip(),
                "gsn_flag": line[72:75].strip(),
                "hcn_flag": line[76:79].strip(),
                "wmo_id": line[80:85].strip(),
            }
        except ValueError:
            continue
        if (
            BBOX[0] <= record["latitude"] <= BBOX[2]
            and BBOX[1] <= record["longitude"] <= BBOX[3]
        ):
            records.append(record)
    return pd.DataFrame(records).set_index("station_id")


def _inventory(path: Path, station_ids: set[str]) -> pd.DataFrame:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        station_id = line[:11]
        if station_id not in station_ids:
            continue
        element = line[31:35]
        if element not in {"TMIN", "TMAX"}:
            continue
        records.append(
            {
                "station_id": station_id,
                "element": element,
                "first_year": int(line[36:40]),
                "last_year": int(line[41:45]),
            }
        )
    return pd.DataFrame(records)


def _distance_matrix(frame: pd.DataFrame) -> np.ndarray:
    lat = np.deg2rad(frame.latitude.to_numpy(float))
    lon = np.deg2rad(frame.longitude.to_numpy(float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * np.arctan2(np.sqrt(a), np.sqrt(np.maximum(0, 1 - a)))


def _maximin(frame: pd.DataFrame, count: int, score: pd.Series | None = None) -> pd.DataFrame:
    if frame.shape[0] <= count:
        return frame.copy()
    distance = _distance_matrix(frame)
    center = np.array([frame.latitude.mean(), frame.longitude.mean()])
    normalized = np.column_stack(
        (
            frame.latitude.to_numpy() - center[0],
            (frame.longitude.to_numpy() - center[1]) * np.cos(np.deg2rad(center[0])),
        )
    )
    first = int(np.argmin(np.sum(normalized**2, axis=1)))
    selected = [first]
    eligible_score = np.ones(frame.shape[0]) if score is None else score.reindex(frame.index).fillna(0).to_numpy()
    while len(selected) < count:
        minimum = distance[:, selected].min(axis=1)
        minimum[selected] = -np.inf
        adjusted = minimum * (0.75 + 0.25 * eligible_score / max(float(np.max(eligible_score)), 1.0))
        selected.append(int(np.argmax(adjusted)))
    return frame.iloc[selected].copy()


def choose_candidates(stations_path: Path, inventory_path: Path, count: int) -> pd.DataFrame:
    stations = _stations(stations_path)
    inventory = _inventory(inventory_path, set(stations.index))
    eligible_ids = []
    for station_id, group in inventory.groupby("station_id"):
        elements = set(group.element)
        if elements == {"TMIN", "TMAX"} and group.first_year.min() <= 2023 and group.last_year.max() >= 2024:
            eligible_ids.append(station_id)
    eligible = stations.loc[sorted(eligible_ids)]
    return _maximin(eligible, count)


def download_daily(candidate_ids: list[str], target: Path) -> str:
    query = {
        "dataset": "daily-summaries",
        "stations": ",".join(candidate_ids),
        "startDate": START,
        "endDate": END,
        "format": "csv",
        "units": "metric",
        "includeAttributes": "true",
        "includeStationName": "true",
        "includeStationLocation": "true",
    }
    url = f"{DATA_URL}?{urlencode(query)}"
    request = Request(url, headers={"User-Agent": "CubeDynamics-relational-feasibility/0.1"})
    with urlopen(request, timeout=180) as response:
        payload = response.read()
    temporary = target.with_suffix(".partial.csv")
    temporary.write_bytes(payload)
    temporary.replace(target)
    return url


def _attributes(value: object) -> tuple[str, str, str, str]:
    if pd.isna(value):
        return "", "", "", ""
    parts = str(value).split(",")
    parts.extend([""] * (4 - len(parts)))
    return tuple(parts[:4])  # type: ignore[return-value]


def clean_daily(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = []
    manifest = []
    expected = pd.date_range(START, END, freq="D").size
    for station_id, group in raw.groupby("STATION"):
        station_row = {
            "station_id": station_id,
            "station_name": str(group.NAME.iloc[0]),
            "latitude": float(group.LATITUDE.iloc[0]),
            "longitude": float(group.LONGITUDE.iloc[0]),
            "elevation_m": float(group.ELEVATION.iloc[0]),
            "coverage_start": str(group.DATE.min()),
            "coverage_end": str(group.DATE.max()),
            "expected_day_count": expected,
            "network_source": "NOAA/NCEI GHCN-Daily",
            "prism_contribution_status": "UNKNOWN",
            "prism_status_basis": (
                "Exact PRISM AN81d station roster for this product period was not available "
                "in the retrieved public artifacts."
            ),
        }
        for variable in ("TMIN", "TMAX"):
            values = pd.to_numeric(group.get(variable), errors="coerce")
            attributes = group.get(f"{variable}_ATTRIBUTES", pd.Series(index=group.index, dtype=object))
            parsed = [_attributes(value) for value in attributes]
            qflag = np.asarray([item[1] for item in parsed], dtype=object)
            valid = values.notna().to_numpy() & (qflag == "")
            station_row[f"{variable.lower()}_reported_count"] = int(values.notna().sum())
            station_row[f"{variable.lower()}_qc_exclusion_count"] = int(np.count_nonzero(values.notna().to_numpy() & ~valid))
            station_row[f"{variable.lower()}_valid_count"] = int(np.count_nonzero(valid))
            station_row[f"{variable.lower()}_completeness"] = float(np.count_nonzero(valid) / expected)
            station_row[f"{variable.lower()}_source_flags"] = ",".join(sorted({item[2] for item, keep in zip(parsed, valid) if keep and item[2]}))
            station_row[f"{variable.lower()}_observation_time_known_count"] = int(sum(bool(item[3]) for item, keep in zip(parsed, valid) if keep))
            for (_, row), keep, attrs in zip(group.iterrows(), valid, parsed):
                records.append(
                    {
                        "station_id": station_id,
                        "date": str(row.DATE),
                        "variable": variable,
                        "value_c": float(row[variable]) if keep else np.nan,
                        "measurement_flag": attrs[0],
                        "quality_flag": attrs[1],
                        "source_flag": attrs[2],
                        "observation_time_local": attrs[3],
                        "qc_valid": bool(keep),
                    }
                )
        manifest.append(station_row)
    return pd.DataFrame(records), pd.DataFrame(manifest)


def _haversine_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
    p1, p2 = np.deg2rad((lat1, lat2))
    dlambda = np.deg2rad(lon2 - lon1)
    dphi = p2 - p1
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlambda / 2) ** 2
    distance = 6371.0088 * 2 * np.arctan2(np.sqrt(a), np.sqrt(max(0.0, 1 - a)))
    y = np.sin(dlambda) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dlambda)
    return float(distance), float(np.rad2deg(np.arctan2(y, x)) % 360.0)


def _agreement(left: np.ndarray, right: np.ndarray) -> dict[str, float | int]:
    valid = np.isfinite(left) & np.isfinite(right)
    a, b = left[valid], right[valid]
    if a.size < 3:
        return {"n": int(a.size), "bias": np.nan, "mae": np.nan, "rmse": np.nan, "correlation": np.nan}
    return {
        "n": int(a.size),
        "bias": float(np.mean(b - a)),
        "mae": float(np.mean(np.abs(b - a))),
        "rmse": float(np.sqrt(np.mean((b - a) ** 2))),
        "correlation": float(np.corrcoef(a, b)[0, 1]),
    }


def station_prism_analysis(
    clean: pd.DataFrame,
    manifest: pd.DataFrame,
    prism_path: Path,
    *,
    maximum_pair_distance_km: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    with xr.open_dataset(prism_path) as source:
        prism = source.load()
    dates = pd.DatetimeIndex(prism.time.values)
    station_series: dict[str, dict[str, np.ndarray]] = {}
    prism_series: dict[str, dict[str, np.ndarray]] = {}
    sampling_rows = []
    raw_rows = []
    for row in manifest.itertuples(index=False):
        yi = int(np.argmin(np.abs(np.asarray(prism.y.values, dtype=float) - row.latitude)))
        xi = int(np.argmin(np.abs(np.asarray(prism.x.values, dtype=float) - row.longitude)))
        pixel_lat = float(prism.y.values[yi])
        pixel_lon = float(prism.x.values[xi])
        offset_km, _ = _haversine_bearing(row.latitude, row.longitude, pixel_lat, pixel_lon)
        sampling_rows.append(
            {
                "station_id": row.station_id,
                "prism_y_index": yi,
                "prism_x_index": xi,
                "prism_latitude": pixel_lat,
                "prism_longitude": pixel_lon,
                "station_to_pixel_center_km": offset_km,
            }
        )
        station_series[row.station_id] = {}
        prism_series[row.station_id] = {}
        for station_variable, prism_variable in (("TMIN", "tmin"), ("TMAX", "tmax")):
            subset = clean.query("station_id == @row.station_id and variable == @station_variable").copy()
            subset["date"] = pd.to_datetime(subset.date)
            station_values = subset.set_index("date").value_c.reindex(dates).to_numpy(float)
            pixel_values = np.asarray(prism[prism_variable].values[:, yi, xi], dtype=float)
            station_series[row.station_id][station_variable] = station_values
            prism_series[row.station_id][station_variable] = pixel_values
            for shift in (-1, 0, 1):
                shifted = np.full_like(pixel_values, np.nan)
                if shift < 0:
                    shifted[-shift:] = pixel_values[:shift]
                elif shift > 0:
                    shifted[:-shift] = pixel_values[shift:]
                else:
                    shifted[:] = pixel_values
                raw_rows.append(
                    {
                        "station_id": row.station_id,
                        "variable": station_variable,
                        "prism_label_shift_days": shift,
                        **_agreement(station_values, shifted),
                    }
                )
    samples = pd.DataFrame(sampling_rows)
    pair_rows = []
    manifest_index = manifest.set_index("station_id")
    ids = sorted(station_series)
    for left_index, left_id in enumerate(ids):
        for right_id in ids[left_index + 1 :]:
            left = manifest_index.loc[left_id]
            right = manifest_index.loc[right_id]
            distance, bearing = _haversine_bearing(
                left.latitude, left.longitude, right.latitude, right.longitude
            )
            if distance > maximum_pair_distance_km:
                continue
            left_sample = samples.set_index("station_id").loc[left_id]
            right_sample = samples.set_index("station_id").loc[right_id]
            if (
                left_sample.prism_y_index == right_sample.prism_y_index
                and left_sample.prism_x_index == right_sample.prism_x_index
            ):
                continue
            station_cold, station_cold_n = one_tail_spearman(
                station_series[left_id]["TMIN"],
                station_series[right_id]["TMIN"],
                tail="lower",
                min_t=10,
            )
            station_warm, station_warm_n = one_tail_spearman(
                station_series[left_id]["TMAX"],
                station_series[right_id]["TMAX"],
                tail="upper",
                min_t=10,
            )
            prism_cold, prism_cold_n = one_tail_spearman(
                prism_series[left_id]["TMIN"],
                prism_series[right_id]["TMIN"],
                tail="lower",
                min_t=10,
            )
            prism_warm, prism_warm_n = one_tail_spearman(
                prism_series[left_id]["TMAX"],
                prism_series[right_id]["TMAX"],
                tail="upper",
                min_t=10,
            )
            pair_rows.append(
                {
                    "station_i": left_id,
                    "station_j": right_id,
                    "distance_km": distance,
                    "bearing_degrees": bearing,
                    "elevation_difference_m": float(right.elevation_m - left.elevation_m),
                    "provenance_class": "UNKNOWN",
                    "station_cold": station_cold,
                    "prism_cold": prism_cold,
                    "station_warm": station_warm,
                    "prism_warm": prism_warm,
                    "station_delta": station_cold - station_warm,
                    "prism_delta": prism_cold - prism_warm,
                    "station_cold_valid_n": station_cold_n,
                    "station_warm_valid_n": station_warm_n,
                    "prism_cold_valid_n": prism_cold_n,
                    "prism_warm_valid_n": prism_warm_n,
                }
            )
    pairs = pd.DataFrame(pair_rows)
    pair_summary: dict[str, object] = {
        "station_count": len(ids),
        "pair_count": int(pairs.shape[0]),
        "maximum_pair_distance_km": maximum_pair_distance_km,
        "dependence_warning": (
            "Edges share stations; pair rows are not independent samples. No pair-level "
            "p-values or independent-edge confidence intervals are reported."
        ),
        "recommended_future_resampling": "leave-one-station-out plus spatial-block holdout",
    }
    if not pairs.empty:
        for label in ("cold", "warm", "delta"):
            pair_summary[label] = _agreement(
                pairs[f"station_{label}"].to_numpy(float),
                pairs[f"prism_{label}"].to_numpy(float),
            )
            valid = pairs[[f"station_{label}", f"prism_{label}"]].dropna()
            pair_summary[label]["rank_correlation"] = (
                float(np.corrcoef(rankdata(valid.iloc[:, 0]), rankdata(valid.iloc[:, 1]))[0, 1])
                if valid.shape[0] >= 3
                else np.nan
            )
        degrees = pd.concat((pairs.station_i, pairs.station_j)).value_counts()
        pair_summary["edges_per_station_median"] = float(degrees.median())
        pair_summary["edges_per_station_maximum"] = int(degrees.max())
    return samples, pd.DataFrame(raw_rows), pairs, pair_summary


def main() -> int:
    args = _parser().parse_args()
    output = args.output.resolve()
    raw_dir = output / "station_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stations_path = raw_dir / "ghcnd-stations.txt"
    inventory_path = raw_dir / "ghcnd-inventory.txt"
    readme_path = raw_dir / "ghcnd-readme.txt"
    missing = [path for path in (stations_path, inventory_path, readme_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Download the official GHCN metadata files first: " + ", ".join(str(path) for path in missing)
        )
    candidates = choose_candidates(stations_path, inventory_path, args.candidate_count)
    raw_daily_path = raw_dir / "ghcn_daily_candidates_20231101_20240130.csv"
    request_url = "cached"
    if args.download:
        request_url = download_daily(candidates.index.tolist(), raw_daily_path)
    if not raw_daily_path.exists():
        raise FileNotFoundError(f"Missing bounded Daily Summaries response: {raw_daily_path}; rerun with --download")
    raw = pd.read_csv(raw_daily_path, low_memory=False)
    clean, manifest = clean_daily(raw)
    manifest = manifest.merge(
        candidates.reset_index()[["station_id", "state", "gsn_flag", "hcn_flag", "wmo_id"]],
        on="station_id",
        how="left",
    )
    qualified = manifest[
        (manifest.tmin_completeness >= args.minimum_completeness)
        & (manifest.tmax_completeness >= args.minimum_completeness)
    ].copy()
    qualified["selection_score"] = qualified[["tmin_completeness", "tmax_completeness"]].min(axis=1)
    selected = _maximin(
        qualified.set_index("station_id"),
        min(args.station_count, qualified.shape[0]),
        score=qualified.set_index("station_id").selection_score,
    ).reset_index()
    selected_ids = set(selected.station_id)
    clean_selected = clean[clean.station_id.isin(selected_ids)].copy()
    samples, raw_comparison, pairs, pair_summary = station_prism_analysis(
        clean_selected,
        selected,
        args.prism.resolve(),
        maximum_pair_distance_km=args.maximum_pair_distance_km,
    )
    selected = selected.merge(samples, on="station_id", how="left")
    selected.to_csv(output / "station_manifest.csv", index=False)
    clean_selected.to_csv(output / "station_daily_qc.csv.gz", index=False, compression="gzip")
    raw_comparison.to_csv(output / "station_prism_raw_value_comparison.csv", index=False)
    pairs.to_csv(output / "station_prism_pair_synchrony.csv", index=False)
    provenance = {
        "analysis": "ghcn_daily_station_validation_feasibility",
        "source": "NOAA/NCEI GHCN-Daily Daily Summaries",
        "source_metadata_url": METADATA_URL,
        "daily_summaries_request_url": request_url,
        "date_range": [START, END],
        "bbox_south_west_north_east": list(BBOX),
        "candidate_station_count": int(candidates.shape[0]),
        "qualified_station_count": int(qualified.shape[0]),
        "selected_station_count": int(selected.shape[0]),
        "minimum_completeness": args.minimum_completeness,
        "quality_policy": "exclude nonnumeric values and every nonblank GHCN quality flag",
        "station_threshold_policy": "derive each conditional tail threshold from the station pair's own quality-controlled observations",
        "temporal_alignment": {
            "primary": "same date label",
            "sensitivity": "PRISM labels shifted -1, 0, and +1 days relative to station labels",
            "prism_daily_definition": "1200 UTC to 1200 UTC, day-ending label",
            "station_definition": "local observation time when GHCN attribute is present; otherwise unknown",
            "warning": "No silent date shift was applied.",
        },
        "prism_contribution_status": "UNKNOWN for all selected stations",
        "prism_independence_warning": (
            "PRISM AN daily uses station networks. The retrieved public material did not "
            "establish exact product-period membership for these stations, so none is "
            "called independent."
        ),
        "raw_file_sha256": _digest(raw_daily_path),
        "stations_file_sha256": _digest(stations_path),
        "inventory_file_sha256": _digest(inventory_path),
        "prism_file_sha256": _digest(args.prism.resolve()),
        "pair_summary": pair_summary,
    }
    (output / "station_qc_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    decision_path = output / "method_decision_table.csv"
    if decision_path.exists():
        decision = pd.read_csv(decision_path)
        direct = {
            "median only",
            "median + IQR/MAD",
            "nested radii",
            "radial profile",
            "radial + directional",
            "PCA/SVD",
        }
        decision.loc[
            decision.method.isin(direct), "station_support"
        ] = "first-stage only: 30 stations / 35 dependent edges"
        decision.loc[
            ~decision.method.isin(direct), "station_support"
        ] = "not directly evaluated; irregular graph is sparse"
        decision.to_csv(decision_path, index=False)
    summary_path = output / "feasibility_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["station_feasibility"] = {
            "selected_station_count": provenance["selected_station_count"],
            "qualified_station_count": provenance["qualified_station_count"],
            "pair_summary": pair_summary,
            "prism_contribution_status": provenance["prism_contribution_status"],
            "temporal_alignment": provenance["temporal_alignment"],
        }
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
