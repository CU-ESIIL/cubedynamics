#!/usr/bin/env python3
"""Build the real-response streamflow lesson; no network or invented data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from vignette_shell import with_shell

ROOT=Path(__file__).resolve().parents[1]
PATH="docs/vignettes/streamflow_snapshots.ipynb"


def build():
    cells=[]
    def cell(kind,text,key=None):
        item={"cell_type":kind,"id":hashlib.sha256(text.encode()).hexdigest()[:12],
              "metadata":{},"source":text.splitlines(keepends=True)}
        if kind=="code":
            item.update(execution_count=None,outputs=[])
            if key: item["metadata"]["visual_example"]={"kind":"figure","key":key}
        cells.append(item)
    cell("markdown","""# Streamflow: keep the observations, keep the evidence

## Context

[Download this notebook](streamflow_snapshots.ipynb?download=1).

Streamgages record discharge at points, not on a raster grid. Reproducibility
requires retaining the observations and their quality status together.

## Question

How did discharge vary within one observed day—and can we reproduce the
analysis after the provider revises its provisional measurements?

We use real USGS measurements for August 26, 2026 at Boulder Creek, the Potomac,
and the Colorado River at Lees Ferry. Their magnitudes are different; these
plots are not a comparison of watershed health or a flood-risk assessment.
The [streamflow reference](../library/nouns/streamflow.md) documents the loader,
its supported scope and quality-status handling.

## Pipe

`pipe(observations) | v.anomaly(dim="time")`

Acquisition and provenance come before the pipe. The one verb subtracts each
station's mean over this one-day window. It does not establish a climatology.

## Analysis story

### 1. Replay what the provider actually returned

The saved HTTP bodies are real, checksum-verified observations. Offline replay
never silently replaces missing files with a new download. This noun is a
`time × station` Dataset, not a raster with invented spatial dimensions.
""")
    cell("code","""from pathlib import Path
import hashlib
import json
import matplotlib.pyplot as plt
import warnings
from cubedynamics import pipe, verbs as v
from cubedynamics.data.usgs import streamflow

# Locate the cloned checkout whether Jupyter starts here or at its root.
root = next(p for p in (Path.cwd(), *Path.cwd().parents)
            if (p / "tests/fixtures/real_data/usgs_streamflow/provenance.json").exists())
fixture = root / "tests/fixtures/real_data/usgs_streamflow"
provenance = json.loads((fixture / "provenance.json").read_text())
for relative, expected in provenance["files"].items():
    assert hashlib.sha256((fixture / relative).read_bytes()).hexdigest() == expected

def observations(name):
    # One explicit consuming noun call. Later verbs perform the analysis.
    with warnings.catch_warnings(record=True) as notices:
        warnings.simplefilter("always")
        result = streamflow(site=provenance["sites"][name], start=provenance["start"],
                            end=provenance["end"], snapshot_dir=fixture / name, offline=True)
    # Keep quality warnings visible without publishing machine-specific paths.
    for notice in notices:
        print(f"{name}: {notice.message}")
    return result

boulder = observations("boulder")
fig, ax = plt.subplots(figsize=(8, 3.5), layout="constrained")
boulder.streamflow.isel(station=0).plot(ax=ax)
ax.set(title="Boulder Creek · real provisional discharge", xlabel="2026-08-26 · UTC",
       ylabel=f"Discharge ({boulder.streamflow.attrs['units']})")
plt.show()
""","raw-discharge")
    cell("markdown","""### 2. Put the analytical sentence in one line

Subtracting the observed window mean makes within-day departures visible.
Negative departures mean below this day's mean—not negative river discharge.
""")
    cell("code","""# The entire transformation: one input, one verb, one explicit result.
departures = (pipe(boulder) | v.anomaly(dim="time")).unwrap()

fig, ax = plt.subplots(figsize=(8, 3.5), layout="constrained")
departures.streamflow.isel(station=0).plot(ax=ax)
ax.axhline(0, color="#555", linestyle=":")
ax.set(title="Boulder Creek · departures from this day's mean", xlabel="2026-08-26 · UTC",
       ylabel=f"Discharge departure ({boulder.streamflow.attrs['units']})")
plt.show()
""","daily-departures")
    cell("markdown","""### 3. Reuse the sentence without erasing station differences

We repeat the same operation separately for three stations. Native units,
station identities, and sampling intervals remain attached. Separate axes
avoid suggesting that equal plot heights represent equal discharge changes.
No temporal interpolation, spatial gridding or implicit averaging occurs.
""")
    cell("code","""fig, axes = plt.subplots(3, 1, figsize=(8, 8), layout="constrained")
for name, ax in zip(provenance["sites"], axes):
    station = observations(name)
    result = (pipe(station) | v.anomaly(dim="time")).unwrap()
    result.streamflow.isel(station=0).plot(ax=ax)
    ax.axhline(0, color="#555", linestyle=":")
    ax.set(title=f"{name.replace('_', ' ').title()} · {station.station.item()}",
           xlabel="2026-08-26 · UTC", ylabel=f"Departure ({station.streamflow.attrs['units']})")
plt.show()
""","three-stations")
    cell("markdown","""## Figure

The three inline results show native discharge, departures from a one-day
mean, and that same transformation at three independently identified stations.

## What the figure tells us

These are within-day changes at the recorded stations. All retained examples
were provisional when retrieved. A working loader, exact response replay and
correct subtraction do not independently validate USGS discharge estimation
or suitability for a particular decision.

For a deliberate live refresh, call `streamflow` with a **new** `snapshot_dir`
and `offline=False`. Keep both snapshots. `compare_observations(before, after)`
reports changes in values/status/qualifiers while ignoring routine row-ID
refreshes; it refuses incompatible station, units or analysis windows.
""")
    notebook={"nbformat":4,"nbformat_minor":5,"cells":cells,"metadata":{
        "kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python"},"cubedynamics":{
            "supported_vignette":True,"network":False,"plot_required":True,"minimum_plot_outputs":3,
            "data_fixture":"tests/fixtures/real_data/usgs_streamflow",
            "provenance":"tests/fixtures/real_data/usgs_streamflow/provenance.json",
            "source_reference":"../library/sources/usgs.md", "source_label":"USGS source reference",
            "source_support_label":"supported scope, quality checks, and limits",
            "related_nouns":"[streamflow](../library/nouns/streamflow.md)"}}}
    return with_shell(notebook,PATH)


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--check",action="store_true"); args=parser.parse_args()
    text=json.dumps(build(),indent=1,ensure_ascii=False)+"\n"
    path=ROOT/PATH
    if args.check:
        if not path.exists() or path.read_text()!=text: raise SystemExit("Stale streamflow notebook; run builder")
    else: path.write_text(text)
