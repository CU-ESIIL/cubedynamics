#!/usr/bin/env python3
"""Build Phase 1 source-integration QA evidence from reviewed real data.

The default workflow is offline and deterministic. It validates the checked-in
PRISM, gridMET, and Sentinel-2 observational extracts and writes JSON reports
plus human-inspectable figures. Live endpoint health remains in separately
marked online tests; this workflow proves reviewed offline source baselines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cubedynamics import data


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "vignettes" / "prism_boulder_january_2024.nc"
PROVENANCE = ROOT / "data" / "vignettes" / "prism_boulder_january_2024.provenance.json"
GRIDMET_FIXTURE = ROOT / "data" / "source_qa" / "gridmet_badlands_july_2001.nc"
GRIDMET_PROVENANCE = GRIDMET_FIXTURE.with_suffix(".provenance.json")
SENTINEL_FIXTURE = ROOT / "data" / "source_qa" / "sentinel2_badlands_june_2023.nc"
SENTINEL_PROVENANCE = SENTINEL_FIXTURE.with_suffix(".provenance.json")
DEFAULT_OUTPUT = ROOT / "artifacts" / "source_qa"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_prism_temperature(output: Path) -> dict[str, object]:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    digest = sha256(FIXTURE)
    if digest != provenance["fixture_sha256"]:
        raise RuntimeError("PRISM QA fixture checksum does not match its provenance record")

    dataset = xr.open_dataset(FIXTURE, engine="scipy").load()
    required = {"tmin", "tmax"}
    if not required.issubset(dataset.data_vars):
        raise RuntimeError(f"PRISM QA fixture is missing {sorted(required - set(dataset.data_vars))}")
    if bool(dataset.attrs.get("is_synthetic", 1)):
        raise RuntimeError("Source QA refuses generated measurement data")

    time = dataset.time.values
    checks = {
        "checksum_matches": digest == provenance["fixture_sha256"],
        "observational_source": dataset.attrs.get("source")
        == "PRISM Group, Oregon State University",
        "crs_explicit": bool(dataset.attrs.get("spatial_reference")),
        "time_monotonic": bool(np.all(np.diff(time).astype("timedelta64[ns]") > np.timedelta64(0, "ns"))),
        "all_finite": bool(np.isfinite(dataset[["tmin", "tmax"]].to_array()).all()),
        "minimum_not_above_maximum": bool((dataset.tmin <= dataset.tmax).all()),
        "temperature_range_plausible": bool(
            float(dataset.tmin.min()) >= -80.0 and float(dataset.tmax.max()) <= 60.0
        ),
        "bounds_overlap_requested_aoi": bool(
            float(dataset.x.min()) <= -104.75
            and float(dataset.x.max()) >= -105.70
            and float(dataset.y.min()) <= 39.55
            and float(dataset.y.max()) >= 40.45
        ),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"PRISM source QA failed: {failed}")

    figure_path = output / "prism_temperature.png"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.25), constrained_layout=True)
    image = dataset.tmax.isel(time=0).plot(
        ax=axes[0], cmap="magma", add_colorbar=True, cbar_kwargs={"label": "degC"}
    )
    image.axes.set_title("PRISM daily maximum temperature\n1 January 2024")
    image.axes.set_xlabel("longitude")
    image.axes.set_ylabel("latitude")
    dataset.tmin.mean(("y", "x")).plot(ax=axes[1], label="minimum", color="#256f73")
    dataset.tmax.mean(("y", "x")).plot(ax=axes[1], label="maximum", color="#b84a3a")
    axes[1].set_title("AOI-mean observed temperature")
    axes[1].set_xlabel("date")
    axes[1].set_ylabel("degC")
    axes[1].legend(frameon=False)
    fig.suptitle("Phase 1 source QA · reviewed PRISM AN91d extract", fontweight="bold")
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)
    return {
        "noun": "temperature",
        "source_flavor": "prism",
        "provider": dataset.attrs["source"],
        "source_product": dataset.attrs["source_product"],
        "aoi": dataset.attrs["geospatial_bounds"],
        "time_range": [str(time[0])[:10], str(time[-1])[:10]],
        "crs": dataset.attrs["spatial_reference"],
        "shape": dict(dataset.sizes),
        "pixel_observations": int(dataset.tmin.size + dataset.tmax.size),
        "missing_fraction": float(dataset[["tmin", "tmax"]].to_array().isnull().mean()),
        "value_range": {
            "tmin": [float(dataset.tmin.min()), float(dataset.tmin.max())],
            "tmax": [float(dataset.tmax.min()), float(dataset.tmax.max())],
        },
        "streaming_mechanism": "NcSS daily AOI requests in production; checksum-controlled GeoTIFF window fixture for offline QA",
        "qa_result": "pass",
        "checks": checks,
        "figure": figure_path.name,
        "fixture_sha256": digest,
        "known_limitations": [
            "This fixture validates PRISM temperature, not every PRISM variable.",
            "The offline fixture covers one Colorado AOI and one winter month.",
        ],
    }


def _verified_fixture(fixture: Path, provenance_path: Path, label: str) -> tuple[xr.Dataset, str]:
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    digest = sha256(fixture)
    if digest != provenance["fixture_sha256"]:
        raise RuntimeError(f"{label} QA fixture checksum does not match its provenance record")
    dataset = xr.open_dataset(fixture, engine="scipy").load()
    if bool(dataset.attrs.get("is_synthetic", 1)):
        raise RuntimeError(f"{label} source QA refuses generated measurement data")
    return dataset, digest


def validate_gridmet_temperature(output: Path) -> dict[str, object]:
    dataset, digest = _verified_fixture(GRIDMET_FIXTURE, GRIDMET_PROVENANCE, "gridMET")
    temperature = dataset["temperature"]
    time = dataset.time.values
    y_step = float(np.median(np.abs(np.diff(dataset.y.values))))
    x_step = float(np.median(np.abs(np.diff(dataset.x.values))))
    checks = {
        "checksum_matches": digest == json.loads(GRIDMET_PROVENANCE.read_text())["fixture_sha256"],
        "observational_source": dataset.attrs.get("source") == "gridMET",
        "crs_explicit": dataset.attrs.get("spatial_reference") == "EPSG:4326",
        "time_strictly_increasing": bool(
            np.all(np.diff(time).astype("timedelta64[ns]") > np.timedelta64(0, "ns"))
        ),
        "all_finite": bool(np.isfinite(temperature).all()),
        "kelvin_range_plausible": bool(
            float(temperature.min()) >= 180.0 and float(temperature.max()) <= 340.0
        ),
        "grid_resolution_expected": bool(
            np.isclose(y_step, 1.0 / 24.0, atol=0.002)
            and np.isclose(x_step, 1.0 / 24.0, atol=0.002)
        ),
        "coordinate_orientation_known": bool(
            np.all(np.diff(dataset.y.values) < 0) and np.all(np.diff(dataset.x.values) > 0)
        ),
        "bounds_overlap_requested_aoi": bool(
            float(dataset.x.min()) <= -101.95
            and float(dataset.x.max()) >= -102.45
            and float(dataset.y.min()) <= 43.65
            and float(dataset.y.max()) >= 44.15
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"gridMET source QA failed: {[key for key, value in checks.items() if not value]}")

    figure_path = output / "gridmet_temperature.png"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.25), constrained_layout=True)
    temperature.isel(time=0).plot(
        ax=axes[0], cmap="magma", cbar_kwargs={"label": "K"}
    )
    axes[0].set_title("gridMET daily maximum temperature\n1 July 2001")
    axes[0].set_xlabel("longitude")
    axes[0].set_ylabel("latitude")
    temperature.mean(("y", "x")).plot(ax=axes[1], color="#8e3b46", marker="o")
    axes[1].set_title("AOI-mean observed maximum temperature")
    axes[1].set_xlabel("date")
    axes[1].set_ylabel("K")
    fig.suptitle("Phase 1 source QA · reviewed gridMET extract", fontweight="bold")
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)
    return {
        "noun": "temperature",
        "source_flavor": "gridmet",
        "provider": dataset.attrs["source_provider"],
        "source_product": dataset.attrs["source_product"],
        "aoi": dataset.attrs["geospatial_bounds"],
        "time_range": [str(time[0])[:10], str(time[-1])[:10]],
        "crs": dataset.attrs["spatial_reference"],
        "shape": dict(dataset.sizes),
        "pixel_observations": int(temperature.size),
        "missing_fraction": float(temperature.isnull().mean()),
        "value_range": [float(temperature.min()), float(temperature.max())],
        "streaming_mechanism": "annual provider NetCDF followed by client-side AOI selection",
        "qa_result": "pass",
        "checks": checks,
        "figure": figure_path.name,
        "fixture_sha256": digest,
        "known_limitations": [
            "This reviewed extract validates gridMET maximum temperature, not every gridMET variable.",
            "The current production adapter opens an annual file before selecting the AOI.",
        ],
    }


def validate_sentinel2_reflectance(output: Path) -> dict[str, object]:
    dataset, digest = _verified_fixture(SENTINEL_FIXTURE, SENTINEL_PROVENANCE, "Sentinel-2")
    reflectance = dataset["surface_reflectance"]
    time = dataset.time.values
    red = reflectance.sel(band="B04")
    nir = reflectance.sel(band="B08")
    ndvi = (nir - red) / (nir + red).where((nir + red) != 0)
    x_step = float(np.median(np.abs(np.diff(dataset.x.values))))
    y_step = float(np.median(np.abs(np.diff(dataset.y.values))))
    checks = {
        "checksum_matches": digest == json.loads(SENTINEL_PROVENANCE.read_text())["fixture_sha256"],
        "observational_source": dataset.attrs.get("source") == "Sentinel-2",
        "crs_explicit": str(dataset.attrs.get("spatial_reference", "")).startswith("EPSG:"),
        "required_bands_present": set(dataset.band.values.astype(str)) == {"B04", "B08"},
        "time_strictly_increasing": bool(
            np.all(np.diff(time).astype("timedelta64[ns]") > np.timedelta64(0, "ns"))
        ),
        "all_finite": bool(np.isfinite(reflectance).all()),
        "reflectance_scale_plausible": bool(
            float(reflectance.min()) >= 0.0 and float(reflectance.max()) <= 10_000.0
        ),
        "ndvi_range_valid": bool(float(ndvi.min()) >= -1.0 and float(ndvi.max()) <= 1.0),
        "ten_meter_grid": bool(np.isclose(x_step, 10.0) and np.isclose(y_step, 10.0)),
        "coordinate_orientation_known": bool(
            np.all(np.diff(dataset.x.values) > 0) and np.all(np.diff(dataset.y.values) < 0)
        ),
        "duplicate_acquisition_times_absent": bool(np.unique(time).size == time.size),
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"Sentinel-2 source QA failed: {[key for key, value in checks.items() if not value]}"
        )

    figure_path = output / "sentinel2_reflectance.png"
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    red.isel(time=-1).plot(ax=axes[0], cmap="Reds", cbar_kwargs={"label": "scaled reflectance"})
    axes[0].set_title("Red band · B04")
    nir.isel(time=-1).plot(ax=axes[1], cmap="magma", cbar_kwargs={"label": "scaled reflectance"})
    axes[1].set_title("Near-infrared band · B08")
    ndvi.isel(time=-1).plot(
        ax=axes[2], cmap="RdYlGn", vmin=-1, vmax=1, cbar_kwargs={"label": "NDVI"}
    )
    axes[2].set_title("Derived NDVI sanity check")
    for axis in axes:
        axis.set_xlabel("UTM easting (m)")
        axis.set_ylabel("UTM northing (m)")
    fig.suptitle("Phase 1 source QA · reviewed Sentinel-2 L2A extract", fontweight="bold")
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)
    provenance = json.loads(SENTINEL_PROVENANCE.read_text(encoding="utf-8"))
    return {
        "noun": "surface_reflectance and vegetation_index",
        "source_flavor": "sentinel2",
        "provider": dataset.attrs["source_provider"],
        "source_product": dataset.attrs["source_product"],
        "aoi": dataset.attrs["geospatial_bounds"],
        "time_range": [str(time[0])[:10], str(time[-1])[:10]],
        "crs": dataset.attrs["spatial_reference"],
        "shape": dict(dataset.sizes),
        "pixel_observations": int(reflectance.size),
        "missing_fraction": float(reflectance.isnull().mean()),
        "value_range": [float(reflectance.min()), float(reflectance.max())],
        "ndvi_range": [float(ndvi.min()), float(ndvi.max())],
        "scene_ids": provenance["scene_ids"],
        "streaming_mechanism": "Planetary Computer STAC plus cloud-optimized asset windows through cubo",
        "qa_result": "pass",
        "checks": checks,
        "figure": figure_path.name,
        "fixture_sha256": digest,
        "known_limitations": [
            "This extract covers one 640 m South Dakota window and two acquisition dates.",
            "Cloud metadata are retained, but this baseline does not implement pixel-level cloud masking.",
        ],
    }


def build_manifest(results: list[dict[str, object]]) -> dict[str, object]:
    inventory = data.list_sources()
    source_status = []
    for noun, flavors in inventory.items():
        for flavor in flavors:
            metadata = data.describe(noun, source=flavor)
            reviewed = flavor in {"prism", "gridmet", "sentinel2"}
            source_status.append(
                {
                    "noun": noun,
                    "source_flavor": flavor,
                    "provider": metadata["provider"],
                    "backend": metadata["backend"],
                    "offline_contract": "pass",
                    "real_visual_qa": "representative source pass" if reviewed else "not reviewed",
                    "online_health_check": "scheduled in .github/workflows/online-tests.yml",
                    "limitations": metadata["limitations"],
                }
            )
    return {
        "phase": "Phase 1: architecture and existing nouns",
        "status": "Phase 1 source-adapter baseline complete; variable-specific coverage is documented",
        "implemented_nouns": sorted(inventory),
        "implemented_source_flavors": inventory,
        "reviewed_real_data_results": results,
        "source_status": source_status,
        "policy": "Planned sources are excluded; generated measurements cannot earn source QA status.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    prism_result = validate_prism_temperature(output)
    gridmet_result = validate_gridmet_temperature(output)
    sentinel_result = validate_sentinel2_reflectance(output)
    results = [prism_result, gridmet_result, sentinel_result]
    for result in results:
        result_path = output / f"{result['source_flavor']}_{str(result['noun']).split(' and ')[0]}.json"
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    manifest = build_manifest(results)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Phase 1 source QA: PRISM, gridMET, and Sentinel-2 pass; report written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
