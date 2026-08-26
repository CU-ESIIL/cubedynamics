#!/usr/bin/env python3
"""Build small observational fixtures for the Phase 1 source-QA workflow.

This maintainer tool never fabricates measurements. It crops an authoritative
gridMET annual file already acquired from the provider and makes one bounded
Sentinel-2 L2A request through the public CubeDynamics adapter. Each extract is
stored with a checksum and exact acquisition query for offline review in CI.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import xarray as xr

from cubedynamics.data.sentinel2 import load_s2_cube


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRIDMET_SOURCE = (
    ROOT / "artifacts" / "fire-vase-gridmet-real" / "gridmet-cache" / "tmmx_2001.nc"
)
DEFAULT_OUTPUT = ROOT / "data" / "source_qa"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_provenance(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_gridmet(source: Path, output: Path) -> Path:
    if not source.exists():
        raise FileNotFoundError(
            f"gridMET source file not found: {source}. Supply --gridmet-source with an "
            "authoritative annual tmmx NetCDF acquired from the provider."
        )
    source_digest = sha256(source)
    dataset = xr.open_dataset(source)
    variable = "air_temperature"
    if variable not in dataset:
        raise RuntimeError(f"Expected {variable!r} in gridMET source")
    extract = dataset[variable].sel(
        day=slice("2001-07-01", "2001-07-10"),
        lat=slice(44.20, 43.60),
        lon=slice(-102.50, -101.90),
    ).load()
    if not extract.sizes.get("day") or not extract.sizes.get("lat") or not extract.sizes.get("lon"):
        raise RuntimeError("The requested gridMET QA window is empty")
    clean = xr.DataArray(
        np.asarray(extract.values, dtype="float32"),
        dims=("time", "y", "x"),
        coords={"time": extract.day.values, "y": extract.lat.values, "x": extract.lon.values},
        name="temperature",
        attrs={
            "units": "K",
            "long_name": "Daily maximum air temperature",
        },
    ).to_dataset()
    clean.attrs.update(
        {
            "source": "gridMET",
            "source_provider": "University of Idaho",
            "source_product": "gridMET daily maximum temperature",
            "source_variable": "air_temperature / tmmx",
            "source_url": "https://www.northwestknowledge.net/metdata/data/tmmx_2001.nc",
            "spatial_reference": "EPSG:4326",
            "geospatial_bounds": "[-102.50, 43.60, -101.90, 44.20]",
            "requested_start": "2001-07-01",
            "requested_end": "2001-07-10",
            "normalization": "cropped and renamed dimensions/variable; values unchanged",
            "data_state": "observational_extract",
            "is_synthetic": False,
        }
    )
    fixture = output / "gridmet_badlands_july_2001.nc"
    clean.to_netcdf(fixture, engine="scipy")
    write_provenance(
        fixture.with_suffix(".provenance.json"),
        {
            "fixture_sha256": sha256(fixture),
            "source_file_sha256": source_digest,
            "source_url": clean.attrs["source_url"],
            "provider": clean.attrs["source_provider"],
            "product": clean.attrs["source_product"],
            "query": {
                "bbox": [-102.50, 43.60, -101.90, 44.20],
                "start": "2001-07-01",
                "end": "2001-07-10",
                "variable": "tmmx",
            },
            "transformation": clean.attrs["normalization"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return fixture


def build_sentinel2(output: Path) -> Path:
    query = {
        "lat": 43.89,
        "lon": -102.18,
        "start": "2023-06-01",
        "end": "2023-06-10",
        "edge_size": 64,
        "resolution": 10,
        "cloud_lt": 80,
        "bands": ["B04", "B08"],
    }
    streamed = load_s2_cube(**query)
    scene_ids = [str(value) for value in streamed.coords["id"].compute().values]
    cloud_cover = [float(value) for value in streamed.coords["eo:cloud_cover"].compute().values]
    observed = streamed.compute()
    clean = xr.DataArray(
        np.asarray(observed.values, dtype="float32"),
        dims=("time", "band", "y", "x"),
        coords={
            "time": observed.time.values,
            "band": observed.band.values.astype(str),
            "y": observed.y.values,
            "x": observed.x.values,
        },
        name="surface_reflectance",
        attrs={"units": "scaled surface reflectance", "scale_factor_description": "provider integer scale"},
    ).to_dataset()
    clean.attrs.update(
        {
            "source": "Sentinel-2",
            "source_provider": "European Union Copernicus Programme / ESA",
            "source_product": "Sentinel-2 Level-2A surface reflectance",
            "source_variables": "B04,B08",
            "source_catalog": "Microsoft Planetary Computer STAC",
            "scene_ids": json.dumps(scene_ids),
            "scene_cloud_cover_percent": json.dumps(cloud_cover),
            "spatial_reference": f"EPSG:{int(observed.attrs['epsg'])}",
            "geospatial_bounds": json.dumps(
                [float(observed.x.min()), float(observed.y.min()), float(observed.x.max()), float(observed.y.max())]
            ),
            "requested_start": query["start"],
            "requested_end": query["end"],
            "normalization": "selected B04/B08, cropped to 640 m square, converted to float32; values unchanged",
            "data_state": "observational_extract",
            "retrieved_at": observed.attrs["retrieved_at"],
            "is_synthetic": False,
        }
    )
    fixture = output / "sentinel2_badlands_june_2023.nc"
    clean.to_netcdf(fixture, engine="scipy")
    write_provenance(
        fixture.with_suffix(".provenance.json"),
        {
            "fixture_sha256": sha256(fixture),
            "provider": clean.attrs["source_provider"],
            "product": clean.attrs["source_product"],
            "catalog": clean.attrs["source_catalog"],
            "query": query,
            "scene_ids": scene_ids,
            "scene_cloud_cover_percent": cloud_cover,
            "transformation": clean.attrs["normalization"],
            "retrieved_at": clean.attrs["retrieved_at"],
        },
    )
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gridmet-source", type=Path, default=DEFAULT_GRIDMET_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-sentinel2", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    gridmet = build_gridmet(args.gridmet_source.resolve(), output)
    print(f"Wrote {gridmet}")
    if not args.skip_sentinel2:
        sentinel2 = build_sentinel2(output)
        print(f"Wrote {sentinel2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
