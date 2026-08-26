#!/usr/bin/env python3
"""Generate machine-readable and visual QA for the Decision Lab workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "real_data" / "sd_working_lands_july_2024.nc"
PROVENANCE = FIXTURE.with_suffix(".provenance.json")
DEFAULT_OUTPUT = ROOT / "artifacts" / "decision_qa"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pipeline(observed: xr.Dataset) -> tuple[xr.Dataset, xr.Dataset, xr.DataArray]:
    warm = (
        pipe(observed.temperature)
        | v.quantile_state(quantile=0.75, direction="above", name="warm_july_day")
    ).unwrap()
    dry = (
        pipe(observed.precipitation)
        | v.threshold_state(threshold=0.1, direction="below", name="trace_or_no_rain")
    ).unwrap()
    frequency = (
        pipe(warm)
        | v.overlap(dry, name="warm_and_dry")
        | v.mean(dim="time", keep_dim=False)
    ).unwrap() * 100
    return warm, dry, frequency


def _write_source_qa(observed: xr.Dataset, output: Path) -> None:
    point = {"y": observed.sizes["y"] // 2, "x": observed.sizes["x"] // 2}
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.2), constrained_layout=True)
    observed.temperature.isel(**point).plot(ax=axes[0, 0], color="#a44f3f")
    axes[0, 0].set_title("Center cell · maximum temperature")
    axes[0, 0].set_ylabel("°C")
    axes[0, 0].xaxis.set_major_locator(mdates.DayLocator(interval=7))
    axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[0, 0].set_xlabel("")
    axes[0, 1].bar(
        observed.time.values,
        observed.precipitation.isel(**point).values,
        color="#39788a",
        width=0.8,
    )
    axes[0, 1].set_title("Center cell · precipitation")
    axes[0, 1].set_ylabel("mm")
    axes[0, 1].xaxis.set_major_locator(mdates.DayLocator(interval=7))
    axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[0, 1].set_xlabel("")
    observed.temperature.max("time").plot(
        ax=axes[1, 0], cmap="magma", cbar_kwargs={"label": "July maximum (°C)"}
    )
    axes[1, 0].set_title("Spatial maximum temperature")
    axes[1, 0].set_xlabel("Longitude")
    axes[1, 0].set_ylabel("Latitude")
    observed.precipitation.sum("time").plot(
        ax=axes[1, 1], cmap="Blues", cbar_kwargs={"label": "July total (mm)"}
    )
    axes[1, 1].set_title("Spatial precipitation total")
    axes[1, 1].set_xlabel("Longitude")
    axes[1, 1].set_ylabel("Latitude")
    fig.suptitle("Decision Lab source QA · observed PRISM nouns", fontweight="bold")
    fig.savefig(output / "source_qa.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def _write_decision_view(frequency: xr.DataArray, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 5.2), constrained_layout=True)
    frequency.plot(
        ax=ax,
        cmap="YlOrBr",
        vmin=0,
        vmax=25,
        cbar_kwargs={"label": "July days warm and dry (%)"},
    )
    ax.set_title("Observed warm-and-dry day frequency · July 2024")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.savefig(output / "decision_view.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    observed = xr.open_dataset(FIXTURE, engine="scipy").load()
    warm, dry, frequency = _pipeline(observed)
    direct = (warm.state & dry.state).mean("time") * 100

    checks = {
        "fixture_checksum": _sha256(FIXTURE) == provenance["fixture_sha256"],
        "observational_source": observed.attrs.get("is_synthetic") == 0
        and provenance.get("is_synthetic") is False,
        "dimensions_exact": dict(observed.sizes) == {"time": 31, "y": 15, "x": 19},
        "all_cells_finite": bool(np.isfinite(observed.to_array()).all()),
        "temperature_physical_range": -60 < float(observed.temperature.min())
        < float(observed.temperature.max()) < 60,
        "precipitation_physical_range": 0 <= float(observed.precipitation.min())
        < float(observed.precipitation.max()) < 500,
        "coordinates_exactly_aligned": all(
            np.array_equal(observed.temperature[dim], observed.precipitation[dim])
            for dim in ("time", "y", "x")
        ),
        "pipe_matches_direct_logic": bool(
            np.allclose(frequency, direct, rtol=0, atol=0, equal_nan=True)
        ),
        "frequency_is_bounded": 0 <= float(frequency.min())
        <= float(frequency.max()) <= 100,
    }
    payload = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "fixture_sha256": provenance["fixture_sha256"],
        "checks": checks,
        "summary": {
            "warm_state_percent": float(warm.state.mean() * 100),
            "dry_state_percent": float(dry.state.mean() * 100),
            "coincidence_percent_min": float(frequency.min()),
            "coincidence_percent_mean": float(frequency.mean()),
            "coincidence_percent_max": float(frequency.max()),
        },
        "interpretation_limit": (
            "weather co-occurrence screening only; not drought, working-land "
            "sensitivity, forage loss, economic impact, causation, or risk"
        ),
    }
    (args.output / "result.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    _write_source_qa(observed, args.output)
    _write_decision_view(frequency, args.output)
    print(f"{payload['status']} · decision QA evidence: {args.output}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
