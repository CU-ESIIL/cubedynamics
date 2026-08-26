#!/usr/bin/env python3
"""Build the executable South Dakota Decision Lab notebook."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "decision_vignettes" / "working_lands.ipynb"


def markdown(source: str) -> dict:
    source = source.strip()
    return {
        "cell_type": "markdown",
        "id": hashlib.sha256(f"markdown:{source}".encode()).hexdigest()[:12],
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code(source: str) -> dict:
    source = source.strip()
    return {
        "cell_type": "code",
        "id": hashlib.sha256(f"code:{source}".encode()).hexdigest()[:12],
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


NOTEBOOK = {
    "cells": [
        markdown(
            """
# Working Lands · Read hot-and-dry weather as two nouns

## The decision

Where did unusually warm July days and days with little or no measured
precipitation coincide in this bounded central South Dakota window?

This is a first-pass climate screening question. A land manager could use it
to decide where to request vegetation, soil-moisture, or field observations
before interpreting working-land sensitivity.

## The missing information

A temperature map alone does not show whether the same days were dry. A
precipitation map alone does not show the thermal context. Reading both nouns
together reveals co-occurrence, while still keeping each observation visible.

It does **not** identify rangeland or cropland, diagnose drought, estimate
forage loss, or measure economic impact.
"""
        ),
        markdown(
            """
## The nouns

| Noun | Public source flavor | Meaning here |
|---|---|---|
| `temperature` | PRISM | Observed daily maximum air temperature (°C) |
| `precipitation` | PRISM | Observed daily precipitation total (mm) |

The area is a small window southwest of Pierre (`-101.2, 43.7, -100.4,
44.3`) and the period is 1–31 July 2024. The AOI keeps the remote acquisition
and notebook compact; it was not selected to imply a known impact hotspot.

## Source and reproducibility

The repository carries a small, checksum-controlled observational fixture so
this lesson runs offline. It was acquired through the actual public
`data.temperature(...)` and `data.precipitation(...)` loaders by
`scripts/build_sd_working_lands_fixture.py`; no random or generated
measurements are substituted. The adjacent provenance record freezes the
query, source service, physical checks, values, and fixture SHA-256.
"""
        ),
        code(
            """
from pathlib import Path
import json

import numpy as np
import xarray as xr

# Locate the repository whether the kernel starts at the project root or in a
# documentation subdirectory. The notebook never depends on a private path.
root = next(
    candidate
    for candidate in (Path.cwd(), *Path.cwd().parents)
    if (candidate / "data" / "decision_vignettes" / "sd_working_lands_july_2024.nc").exists()
)
fixture = root / "data" / "decision_vignettes" / "sd_working_lands_july_2024.nc"
provenance_path = fixture.with_suffix(".provenance.json")

observed = xr.open_dataset(fixture, engine="scipy").load()
provenance = json.loads(provenance_path.read_text(encoding="utf-8"))

# Fail loudly if the teaching evidence loses its source identity, daily time
# axis, declared units, or complete finite observations.
assert observed.attrs["is_synthetic"] == 0
assert provenance["is_synthetic"] is False
assert observed.sizes == {"time": 31, "y": 15, "x": 19}
assert observed.temperature.attrs["units"] == "degC"
assert observed.precipitation.attrs["units"] == "mm"
assert bool(np.isfinite(observed.to_array()).all())

# These names are the environmental nouns that enter the grammar below.
temperature = observed["temperature"]
precipitation = observed["precipitation"]
print(
    f"Loaded {observed.sizes['time']} daily observations on a "
    f"{observed.sizes['y']} × {observed.sizes['x']} grid: "
    f"{', '.join(observed.data_vars)}"
)
"""
        ),
        markdown(
            """
## QA · Check the nouns before trusting the sentence

The time series checks continuity and plausible event timing at the center
cell. The maps check spatial coverage and reveal whether either noun is empty,
constant, clipped, or obviously misaligned. July total precipitation is a sum
of daily totals; the temperature panel shows the hottest day by AOI mean.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Use one documented center cell for temporal QA, not as a claim that the cell
# represents the whole AOI.
point_temperature = temperature.isel(y=temperature.sizes["y"] // 2, x=temperature.sizes["x"] // 2)
point_precipitation = precipitation.isel(y=precipitation.sizes["y"] // 2, x=precipitation.sizes["x"] // 2)
hottest_day = temperature.mean(("y", "x")).argmax("time")

fig, axes = plt.subplots(2, 2, figsize=(11, 7.2), constrained_layout=True)
point_temperature.plot(ax=axes[0, 0], color="#a44f3f", linewidth=1.8)
axes[0, 0].set_title("Center cell · daily maximum temperature")
axes[0, 0].set_ylabel("Temperature (°C)")
axes[0, 0].xaxis.set_major_locator(mdates.DayLocator(interval=7))
axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
axes[0, 0].set_xlabel("")

axes[0, 1].bar(
    point_precipitation.time.values,
    point_precipitation.values,
    width=0.8,
    color="#39788a",
)
axes[0, 1].set_title("Center cell · daily precipitation")
axes[0, 1].set_ylabel("Precipitation (mm)")
axes[0, 1].xaxis.set_major_locator(mdates.DayLocator(interval=7))
axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
axes[0, 1].set_xlabel("")

temperature.isel(time=hottest_day).plot(
    ax=axes[1, 0], cmap="magma", cbar_kwargs={"label": "Maximum temperature (°C)"}
)
axes[1, 0].set_title("Spatial QA · hottest AOI-mean day")
axes[1, 0].set_xlabel("Longitude")
axes[1, 0].set_ylabel("Latitude")

precipitation.sum("time").plot(
    ax=axes[1, 1], cmap="Blues", cbar_kwargs={"label": "July total (mm)"}
)
axes[1, 1].set_title("Spatial QA · July precipitation total")
axes[1, 1].set_xlabel("Longitude")
axes[1, 1].set_ylabel("Latitude")
plt.show()
"""
        ),
        markdown(
            """
## The analytical sentence

First, each noun becomes a transparent state. “Warm” means the upper quartile
of that cell's July maximum temperatures. “Dry day” means daily precipitation
at or below 0.1 mm. These are screening definitions for this month—not a
climatological heat or drought classification.
"""
        ),
        code(
            """
from cubedynamics import pipe, verbs as v

# Each threshold is visible and replaceable. quantile_state computes a
# cell-specific July threshold; threshold_state applies the stated rain cutoff.
warm_days = (
    pipe(temperature)
    | v.quantile_state(quantile=0.75, direction="above", name="warm_july_day")
).unwrap()

dry_days = (
    pipe(precipitation)
    | v.threshold_state(threshold=0.1, direction="below", name="trace_or_no_rain")
).unwrap()

# The hero sentence asks where both aligned states are true, then summarizes
# the fraction of July days. overlap refuses silent coordinate alignment.
coincidence_frequency = (
    pipe(warm_days)
    | v.overlap(dry_days, name="warm_and_dry")
    | v.mean(dim="time", keep_dim=False)
).unwrap() * 100

coincidence_frequency = coincidence_frequency.assign_attrs(
    long_name="July days that were both locally warm and dry",
    units="percent",
)

assert coincidence_frequency.dims == ("y", "x")
assert float(coincidence_frequency.min()) >= 0
assert float(coincidence_frequency.max()) <= 100
print(
    "Decision grid: "
    f"{coincidence_frequency.sizes['y']} × {coincidence_frequency.sizes['x']} cells; "
    f"range {float(coincidence_frequency.min()):.1f}–"
    f"{float(coincidence_frequency.max()):.1f}%"
)
"""
        ),
        markdown(
            """
### Read it left to right

**WARM JULY DAYS → OVERLAP DRY DAYS → MEAN THROUGH TIME**

- `quantile_state` makes “warm” explicit relative to each cell's July values.
- `threshold_state` makes the trace-or-no-rain cutoff explicit.
- `overlap` keeps only times and cells where both states are true and requires
  exact coordinates.
- `mean` turns the daily boolean cube into the percentage of July days meeting
  both definitions.
"""
        ),
        markdown(
            """
## Decision view

The final map is intentionally one result: the frequency of observed
co-occurrence under the stated screening definitions. The two source maps
above remain visible so the result is not an opaque composite score.
"""
        ),
        code(
            """
fig, ax = plt.subplots(figsize=(8.4, 5.2), constrained_layout=True)
coincidence_frequency.plot(
    ax=ax,
    cmap="YlOrBr",
    vmin=0,
    vmax=25,
    cbar_kwargs={"label": "July days warm and dry (%)"},
)
ax.set_title("Observed warm-and-dry day frequency · July 2024")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.text(
    0.01,
    -0.16,
    "PRISM daily observations · warm = cell-specific July upper quartile · dry ≤ 0.1 mm",
    transform=ax.transAxes,
    fontsize=8,
    color="#4f5d60",
)
plt.show()
"""
        ),
        markdown(
            """
## What this does and does not tell us

The map shows that the two observed weather conditions did not occur with the
same frequency everywhere in this bounded window during July 2024. It can
support a question such as: *where should we seek vegetation, soil-moisture,
or field evidence next?*

It does not identify a working landscape, compare 2024 with a long-term
climatology, attribute causes, or estimate agricultural/ecological harm. A
defensible working-lands sensitivity analysis still needs public land-cover or
cropland and vegetation-response nouns, plus longer climate baselines.

## Fork this question

- Replace the upper-quartile definition with a threshold justified for a
  specific management question.
- Expand the time range to a climatological baseline before using the word
  “anomaly.”
- Once vetted land-cover and vegetation nouns exist, ask where weather
  co-occurrence and observed vegetation response align on working lands.
"""
        ),
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "cubedynamics": {
            "network": False,
            "plot_required": True,
            "minimum_plot_outputs": 2,
            "supported_vignette": True,
            "supported_decision_vignette": True,
            "data_fixture": "data/decision_vignettes/sd_working_lands_july_2024.nc",
            "provenance": (
                "data/decision_vignettes/sd_working_lands_july_2024.provenance.json"
            ),
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(NOTEBOOK, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
