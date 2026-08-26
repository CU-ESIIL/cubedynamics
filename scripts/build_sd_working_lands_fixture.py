#!/usr/bin/env python3
"""Build the small observed-data fixture for the South Dakota Decision Lab.

The acquisition deliberately goes through the public CubeDynamics noun API.
It requests one bounded South Dakota window from the official PRISM service,
refuses synthetic fallback, validates the returned cube, and records the exact
query and fixture checksum used by the offline publication notebook.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import xarray as xr

from cubedynamics import data


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "decision_vignettes" / "sd_working_lands_july_2024.nc"
DEFAULT_PROVENANCE = DEFAULT_OUTPUT.with_suffix(".provenance.json")
BBOX = (-101.2, 43.7, -100.4, 44.3)
START = "2024-07-01"
END = "2024-07-31"
SOURCE = "prism"
SOURCE_SERVICE = "https://thredds.climate.ncsu.edu/thredds/catalog/prism/daily/combo/catalog.html"
SOURCE_DOCUMENTATION = "https://prism.oregonstate.edu/documents/PRISM_datasets.pdf"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _netcdf_safe_attrs(attrs: dict) -> dict:
    """Convert boolean metadata to classic-NetCDF-compatible integers."""

    return {key: int(value) if isinstance(value, bool) else value for key, value in attrs.items()}


def acquire() -> xr.Dataset:
    """Acquire the two public nouns and return one validated observed Dataset."""

    temperature = data.temperature(
        source=SOURCE,
        statistic="maximum",
        bbox=BBOX,
        start=START,
        end=END,
        show_progress=False,
    ).compute()
    precipitation = data.precipitation(
        source=SOURCE,
        bbox=BBOX,
        start=START,
        end=END,
        show_progress=False,
    ).compute()

    if bool(temperature.attrs.get("is_synthetic")):
        raise RuntimeError("temperature noun unexpectedly reported synthetic data")
    if bool(precipitation.attrs.get("is_synthetic")):
        raise RuntimeError("precipitation noun unexpectedly reported synthetic data")

    temperature, precipitation = xr.align(temperature, precipitation, join="exact")
    dataset = xr.Dataset(
        {
            "temperature": temperature.assign_attrs(_netcdf_safe_attrs(dict(temperature.attrs))),
            "precipitation": precipitation.assign_attrs(
                _netcdf_safe_attrs(dict(precipitation.attrs))
            ),
        },
        attrs={
            "title": "Observed PRISM climate window southwest of Pierre, South Dakota",
            "source": "PRISM Climate Group, Oregon State University",
            "source_flavor": SOURCE,
            "source_service": SOURCE_SERVICE,
            "source_documentation": SOURCE_DOCUMENTATION,
            "source_accessed": datetime.now(timezone.utc).date().isoformat(),
            "geospatial_bounds": ",".join(str(value) for value in BBOX),
            "time_coverage_start": START,
            "time_coverage_end": END,
            "processing": (
                "public cubedynamics.data.temperature and precipitation noun loaders; "
                "server-side daily AOI subsets; no interpolation or synthetic fallback"
            ),
            "is_synthetic": 0,
        },
    )
    _validate(dataset)
    return dataset


def _validate(dataset: xr.Dataset) -> None:
    expected = {"time", "y", "x"}
    if set(dataset.dims) != expected:
        raise RuntimeError(f"Expected dimensions {expected}, received {set(dataset.dims)}")
    if dataset.sizes["time"] != 31:
        raise RuntimeError(f"Expected 31 daily observations, received {dataset.sizes['time']}")
    if not bool(np.isfinite(dataset.to_array()).all()):
        raise RuntimeError("Fixture contains non-finite observations")
    if float(dataset.temperature.min()) < -60 or float(dataset.temperature.max()) > 60:
        raise RuntimeError("Temperature values fall outside the physical QA range")
    if float(dataset.precipitation.min()) < 0 or float(dataset.precipitation.max()) > 500:
        raise RuntimeError("Precipitation values fall outside the physical QA range")


def _provenance(dataset: xr.Dataset) -> dict:
    return {
        "schema_version": 1,
        "fixture": DEFAULT_OUTPUT.name,
        "is_synthetic": False,
        "decision_scope": (
            "climate screening only; the fixture does not identify cropland, rangeland, "
            "ecological sensitivity, forage loss, or economic impact"
        ),
        "aoi": {
            "name": "bounded central South Dakota window southwest of Pierre",
            "bbox_wgs84": list(BBOX),
            "selection_reason": (
                "A modest CONUS interior window keeps daily PRISM requests and notebook "
                "runtime bounded; it was not selected to imply a known impact hotspot."
            ),
        },
        "time_coverage": [START, END],
        "source": {
            "flavor": SOURCE,
            "provider": "PRISM Climate Group, Oregon State University",
            "product": "PRISM AN81d/AN91d daily time series",
            "service": SOURCE_SERVICE,
            "documentation": SOURCE_DOCUMENTATION,
            "accessed": dataset.attrs["source_accessed"],
            "revision_note": (
                "PRISM grids may be revised as station data and quality control mature; "
                "the fixture checksum freezes the observations used for publication."
            ),
        },
        "public_loader_calls": [
            {
                "noun": "temperature",
                "call": "data.temperature",
                "arguments": {
                    "source": SOURCE,
                    "statistic": "maximum",
                    "bbox": list(BBOX),
                    "start": START,
                    "end": END,
                },
            },
            {
                "noun": "precipitation",
                "call": "data.precipitation",
                "arguments": {
                    "source": SOURCE,
                    "bbox": list(BBOX),
                    "start": START,
                    "end": END,
                },
            },
        ],
        "dimensions": {name: int(size) for name, size in dataset.sizes.items()},
        "variables": {
            name: {
                "units": str(dataset[name].attrs.get("units", "")),
                "minimum": float(dataset[name].min()),
                "maximum": float(dataset[name].max()),
                "finite_cells": int(np.isfinite(dataset[name]).sum()),
            }
            for name in dataset.data_vars
        },
        "processing": dataset.attrs["processing"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    args = parser.parse_args()

    dataset = acquire()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_netcdf(args.output, engine="scipy")
    provenance = _provenance(dataset)
    provenance["fixture_bytes"] = args.output.stat().st_size
    provenance["fixture_sha256"] = _sha256(args.output)
    args.provenance.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output.relative_to(ROOT)}")
    print(f"wrote {args.provenance.relative_to(ROOT)}")
    print(f"fixture sha256: {provenance['fixture_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
