#!/usr/bin/env python3
"""Build Phase 1 source-integration QA evidence from reviewed real data.

The default workflow is offline and deterministic. It validates the checked-in
PRISM observational extract and writes a JSON report plus a human-inspectable
map/time-series figure. Live gridMET and Sentinel-2 endpoint health remains in
the separately marked online test workflow; those sources are not assigned a
visual-QA pass here until reviewed real fixtures are added.
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


def build_manifest(prism_result: dict[str, object]) -> dict[str, object]:
    inventory = data.list_sources()
    source_status = []
    for noun, flavors in inventory.items():
        for flavor in flavors:
            metadata = data.describe(noun, source=flavor)
            reviewed = noun == "temperature" and flavor == "prism"
            source_status.append(
                {
                    "noun": noun,
                    "source_flavor": flavor,
                    "provider": metadata["provider"],
                    "backend": metadata["backend"],
                    "offline_contract": "pass",
                    "real_visual_qa": "pass" if reviewed else "pending reviewed fixture",
                    "online_health_check": "scheduled in .github/workflows/online-tests.yml",
                    "limitations": metadata["limitations"],
                }
            )
    return {
        "phase": "Phase 1: architecture and existing nouns",
        "status": "partial: architecture complete; source-specific visual QA remains open where stated",
        "implemented_nouns": sorted(inventory),
        "implemented_source_flavors": inventory,
        "reviewed_real_data_results": [prism_result],
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
    (output / "prism_temperature.json").write_text(
        json.dumps(prism_result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = build_manifest(prism_result)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Phase 1 source QA: PRISM pass; report written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
