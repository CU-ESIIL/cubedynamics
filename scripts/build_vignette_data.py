#!/usr/bin/env python3
"""Build the publication vignette fixture from cached official PRISM grids.

The checked-in NetCDF is intentionally small enough for offline documentation
and CI execution. This script is the auditable derivation path from the 60
official daily PRISM archives recorded in the source manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
import requests
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = ROOT / "artifacts" / "prism-real-cache"
DEFAULT_OUTPUT = ROOT / "data" / "vignettes" / "prism_boulder_january_2024.nc"
DEFAULT_PROVENANCE = (
    ROOT / "data" / "vignettes" / "prism_boulder_january_2024.provenance.json"
)
DEFAULT_SOURCE_MANIFEST = DEFAULT_PROVENANCE
BBOX = (-105.75, 39.50, -104.75, 40.50)
VARIABLES = ("tmin", "tmax")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_source_records(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    source_records = payload.get("files", payload.get("source_archives", []))
    records = [
        record
        for record in source_records
        if record["variable"] in VARIABLES
        and "2024-01-01" <= record["date"] <= "2024-01-30"
    ]
    if len(records) != 60:
        raise RuntimeError(f"Expected 60 PRISM source records, found {len(records)}")
    return sorted(records, key=lambda item: (item["date"], item["variable"]))


def _read_crop(archive: Path, variable: str, date_text: str):
    stem = f"prism_{variable}_us_25m_{date_text.replace('-', '')}"
    raster_url = f"zip://{archive.resolve()}!{stem}.tif"
    with rasterio.open(raster_url) as source:
        if source.crs is None or source.crs.to_epsg() != 4269:
            raise RuntimeError(f"Unexpected PRISM CRS in {archive}: {source.crs}")
        window = from_bounds(*BBOX, transform=source.transform)
        window = window.round_offsets().round_lengths()
        values = source.read(1, window=window, masked=True).filled(np.nan).astype("float32")
        transform = source.window_transform(window)
        x = transform.c + (np.arange(values.shape[1]) + 0.5) * transform.a
        y = transform.f + (np.arange(values.shape[0]) + 0.5) * transform.e
    return values, y.astype("float64"), x.astype("float64")


def _download(record: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    with requests.get(record["url"], stream=True, timeout=120) as response:
        response.raise_for_status()
        with partial.open("wb") as stream:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    stream.write(chunk)
    partial.replace(destination)


def build_fixture(
    cache_dir: Path, source_manifest: Path, *, download_missing: bool = False
) -> tuple[xr.Dataset, dict]:
    records = _load_source_records(source_manifest)
    by_variable: dict[str, list[np.ndarray]] = {name: [] for name in VARIABLES}
    source_evidence = []
    expected_y = None
    expected_x = None

    for record in records:
        archive = cache_dir / Path(record["url"]).name
        if not archive.exists():
            if download_missing:
                print(f"downloading {record['url']}")
                _download(record, archive)
            else:
                raise FileNotFoundError(
                    f"Missing cached PRISM archive: {archive}. Re-run with --download-missing."
                )
        actual_bytes = archive.stat().st_size
        actual_sha256 = _sha256(archive)
        if actual_bytes != int(record["bytes"]):
            raise RuntimeError(f"Byte-count mismatch for {archive.name}")
        if actual_sha256 != record["sha256"]:
            raise RuntimeError(f"SHA-256 mismatch for {archive.name}")

        values, y, x = _read_crop(archive, record["variable"], record["date"])
        if expected_y is None:
            expected_y, expected_x = y, x
        else:
            np.testing.assert_array_equal(y, expected_y)
            np.testing.assert_array_equal(x, expected_x)
        by_variable[record["variable"]].append(values)
        source_evidence.append(
            {
                "variable": record["variable"],
                "date": record["date"],
                "url": record["url"],
                "bytes": actual_bytes,
                "sha256": actual_sha256,
            }
        )

    assert expected_y is not None and expected_x is not None
    time = pd.date_range("2024-01-01", "2024-01-30", freq="D")
    dataset = xr.Dataset(
        {
            "tmin": (
                ("time", "y", "x"),
                np.stack(by_variable["tmin"]),
                {
                    "long_name": "daily minimum air temperature",
                    "standard_name": "air_temperature",
                    "units": "degC",
                    "source_variable": "PRISM tmin",
                    "is_synthetic": 0,
                },
            ),
            "tmax": (
                ("time", "y", "x"),
                np.stack(by_variable["tmax"]),
                {
                    "long_name": "daily maximum air temperature",
                    "standard_name": "air_temperature",
                    "units": "degC",
                    "source_variable": "PRISM tmax",
                    "is_synthetic": 0,
                },
            ),
        },
        coords={
            "time": time,
            "y": ("y", expected_y, {"standard_name": "latitude", "units": "degrees_north"}),
            "x": ("x", expected_x, {"standard_name": "longitude", "units": "degrees_east"}),
        },
        attrs={
            "title": "PRISM Boulder County daily temperature teaching extract",
            "source": "PRISM Group, Oregon State University",
            "source_url": "https://prism.oregonstate.edu",
            "source_product": "AN91d daily 4 km time series",
            "source_resolution": "2.5 arc-minute (~4 km)",
            "source_accessed": "2026-08-25",
            "terms_url": "https://prism.oregonstate.edu/terms/",
            "dataset_documentation": "https://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf",
            "spatial_reference": "EPSG:4269",
            "geospatial_bounds": "-105.75,39.50,-104.75,40.50",
            "processing": "windowed extraction from checksum-verified official daily GeoTIFF archives",
            "is_synthetic": 0,
        },
    )
    dataset["diurnal_range"] = (dataset["tmax"] - dataset["tmin"]).assign_attrs(
        long_name="daily air-temperature range",
        units="degC",
        source_variable="derived exactly as tmax - tmin",
        is_synthetic=0,
    )

    provenance = {
        "schema_version": 1,
        "fixture": DEFAULT_OUTPUT.name,
        "source": dataset.attrs["source"],
        "source_url": dataset.attrs["source_url"],
        "source_product": dataset.attrs["source_product"],
        "source_accessed": dataset.attrs["source_accessed"],
        "terms_url": dataset.attrs["terms_url"],
        "dataset_documentation": dataset.attrs["dataset_documentation"],
        "is_synthetic": False,
        "bbox": list(BBOX),
        "time_coverage": ["2024-01-01", "2024-01-30"],
        "dimensions": {name: int(size) for name, size in dataset.sizes.items()},
        "variables": {
            name: {
                "units": dataset[name].attrs["units"],
                "minimum": float(dataset[name].min()),
                "maximum": float(dataset[name].max()),
                "finite_cells": int(np.isfinite(dataset[name]).sum()),
            }
            for name in dataset.data_vars
        },
        "processing": dataset.attrs["processing"],
        "source_archives": source_evidence,
    }
    return dataset, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument(
        "--download-missing",
        action="store_true",
        help="Download missing official PRISM archives before checksum validation.",
    )
    args = parser.parse_args()

    dataset, provenance = build_fixture(
        args.cache_dir, args.source_manifest, download_missing=args.download_missing
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_netcdf(args.output, engine="scipy")
    provenance["fixture_bytes"] = args.output.stat().st_size
    provenance["fixture_sha256"] = _sha256(args.output)
    args.provenance.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output.relative_to(ROOT)}")
    print(f"wrote {args.provenance.relative_to(ROOT)}")
    print(f"fixture sha256: {provenance['fixture_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
