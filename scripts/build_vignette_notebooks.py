#!/usr/bin/env python3
"""Build the source-controlled publication vignettes from reviewed text."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from vignette_shell import with_shell


ROOT = Path(__file__).resolve().parents[1]
VIGNETTE_DIR = ROOT / "docs" / "vignettes"


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


def notebook(*cells: dict) -> dict:
    return {
        "cells": list(cells),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
            "cubedynamics": {
                "network": False,
                "plot_required": True,
                "supported_vignette": True,
                "data_fixture": "tests/fixtures/real_data/prism_boulder_january_2024.nc",
                "provenance": "tests/fixtures/real_data/prism_boulder_january_2024.provenance.json",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


DATA_NOTE = """
### Data used in this lesson

Every value comes from the PRISM Group at Oregon State University's AN91d
daily 4 km climate product. This repository carries a small Boulder-region
extract for 1–30 January 2024 so the lesson runs offline without replacing
observations with generated values. The [data validation page](../validation/data.md)
records source URLs, terms, checksums, bounds, units, and acceptance tests.
"""


LOAD_PRISM = """
from pathlib import Path

import xarray as xr

# Find the repository from either a root-level documentation build or a kernel
# started beside this notebook, then open the checksum-controlled PRISM extract.
data_path = next(
    candidate / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc"
    for candidate in (Path.cwd(), *Path.cwd().parents)
    if (candidate / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc").exists()
)
prism = xr.open_dataset(data_path, engine="scipy").load()

# These assertions are part of the teaching contract: official source,
# canonical cube dimensions, complete daily time, and declared Celsius units.
assert prism.attrs["source"] == "PRISM Group, Oregon State University"
assert prism.attrs["is_synthetic"] == 0
assert prism.sizes == {"time": 30, "y": 24, "x": 24}
assert prism["tmax"].attrs["units"] == "degC"
"""


NOTEBOOKS = {
    "cube_from_arrays.ipynb": notebook(
        markdown(
            f"""
# 01 · From an array to a scientific cube

## Context

A raster workflow has returned a three-dimensional array of observed daily
maximum temperatures. The values are real, but the array alone does not retain
which axis represents time, latitude, or longitude.

## Question

How can we reconstruct a self-describing cube and verify it as a map, a site
history, and an interactive space-time object?

## Analysis story

We will deliberately separate values from metadata, rebuild their scientific
context, and send the result through one minimal plotting pipe.

{DATA_NOTE}
"""
        ),
        markdown("## Prepare · Recover coordinates and provenance for the array"),
        code(
            LOAD_PRISM
            + """
import numpy as np

# Use an inspectable 18-day, 5-row × 6-column portion of the official grid.
source = prism["tmax"].isel(time=slice(0, 18), y=slice(8, 13), x=slice(8, 14))
values = source.values

# Reattach the coordinate and provenance fields that an anonymous NumPy array
# cannot carry. No temperatures are generated or altered in this conversion.
cube = xr.DataArray(
    values,
    dims=("time", "y", "x"),
    coords={name: source[name] for name in ("time", "y", "x")},
    name="tmax",
    attrs=dict(source.attrs),
)
cube.attrs.update(source=prism.attrs["source"], is_synthetic=0)

np.testing.assert_array_equal(cube.values, source.values)
assert cube.dims == ("time", "y", "x")
cube
"""
        ),
        markdown(
            """
## Figure 1 · Read the cube in familiar views

Compare a map from the cold outbreak with the history of one grid cell. Both
views must retain the observed PRISM values.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
cube.isel(time=15).plot(ax=axes[0], cmap="magma", cbar_kwargs={"label": "°C"})
axes[0].set_title("PRISM maximum temperature · 16 January")
cube.isel(y=2, x=3).plot(ax=axes[1], marker="o", color="#2f6f6d")
axes[1].set_title("One PRISM grid cell through time")
axes[1].set_ylabel("Daily maximum temperature (°C)")
plt.show()
"""
        ),
        markdown(
            """
## Pipe · Inspect the same evidence as a cube

The method remains one short sentence. The viewer is generated from the same
validated `DataArray`; it does not become a second data authority.
"""
        ),
        code(
            """
from html import escape
from IPython.display import HTML
from cubedynamics import pipe, verbs as v

viewer = (
    pipe(cube)
    | v.plot(
        title="PRISM daily maximum temperature · Boulder region",
        cmap="magma",
        thin_time_factor=1,
    )
).unwrap()

# Isolate the complete viewer document from the surrounding MkDocs page.
viewer_srcdoc = escape(viewer.to_html(), quote=True)
HTML(
    f'''<iframe
        title="Interactive PRISM maximum-temperature cube"
        srcdoc="{viewer_srcdoc}"
        style="width: 100%; height: 760px; border: 1px solid #b8c5c2; border-radius: 4px;"
        sandbox="allow-scripts"
        loading="lazy"
    ></iframe>'''
)
"""
        ),
        markdown(
            """
## What the figure tells us

The mid-January cold outbreak is visible through depth and across the map. The
validation suite independently decodes all six HTML textures and checks them
against these source indices, including the declared back-face reversal.

## Try the next variation

Choose a different observed time window or spatial subset. The reconstruction
and pipe stay unchanged.
"""
        ),
    ),
    "cube_from_tidy_table.ipynb": notebook(
        markdown(
            f"""
# 02 · From observations to a comparable signal

## Context

Climate observations are often exchanged as one row per date and location.
Here we flatten official PRISM minimum temperature into that familiar table,
then recover the cube without changing a value.

## Question

Can we compare departures through time at sites with different baseline
temperatures?

## Analysis story

We will prove the table-to-cube round trip, standardize each location through
time, and compare the observed and standardized series at one grid cell.

{DATA_NOTE}
"""
        ),
        markdown("## Prepare · Round-trip real observations through a tidy table"),
        code(
            LOAD_PRISM
            + """
import numpy as np

source = prism["tmin"].isel(y=slice(9, 14), x=slice(9, 15))
table = source.to_dataframe(name="tmin").reset_index()

cube = (
    table.set_index(["time", "y", "x"])
    .to_xarray()["tmin"]
    .transpose("time", "y", "x")
    .sel(time=source.time, y=source.y, x=source.x)
)
cube.attrs.update(source.attrs)
cube.attrs.update(source=prism.attrs["source"], is_synthetic=0)

np.testing.assert_array_equal(cube.values, source.values)
assert len(table) == source.size
cube
"""
        ),
        markdown(
            """
## Pipe · Standardize each location through time

Preparation is complete. The analytical method is one verb.
"""
        ),
        code(
            """
from cubedynamics import pipe, verbs as v

standardized = (
    pipe(cube)
    | v.zscore(dim="time")
).unwrap()

assert float(abs(standardized.mean("time")).max()) < 1e-5
standardized
"""
        ),
        markdown("## Figure · Compare the observed and standardized records"),
        code(
            """
import matplotlib.pyplot as plt

site = {"y": float(cube.y[2]), "x": float(cube.x[3])}
fig, axes = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True, constrained_layout=True)
cube.sel(**site).plot(ax=axes[0], marker="o", color="#8b543c")
axes[0].set_title("Observed PRISM daily minimum temperature")
axes[0].set_ylabel("Temperature (°C)")
standardized.sel(**site).plot(ax=axes[1], marker="o", color="#3f6f72")
axes[1].axhline(0, color="0.35", linewidth=0.8)
axes[1].set_title("The same grid cell after v.zscore(dim='time')")
axes[1].set_ylabel("Standard deviations")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

Standardization preserves the January timing—including the sharp cold
outbreak—while expressing each value relative to that location's own record.

## Try the next variation

Replace `v.zscore` with `v.anomaly` and explain which scale is more useful for
your question.
"""
        ),
    ),
    "cube_from_dataset.ipynb": notebook(
        markdown(f"""
# 03 · Two variables, two questions

## Context

PRISM minimum and maximum temperature share one coordinate system, so we can
ask related questions without juggling separate grids.

## Question

Where was maximum temperature unusual on the coldest regional day, and how did
the day-to-night temperature range change through January?

## Analysis story

We validate the physical relationship between variables, then answer a spatial
and a temporal question with two readable pipes.

{DATA_NOTE}
"""),
        markdown("## Prepare · Validate the shared dataset"),
        code(LOAD_PRISM + """
import numpy as np

# Minimum temperature cannot exceed maximum temperature, and the derived range
# must be exactly traceable to those two observed PRISM variables.
assert bool((prism["tmin"] <= prism["tmax"]).all())
np.testing.assert_allclose(
    prism["diurnal_range"], prism["tmax"] - prism["tmin"], rtol=0, atol=1e-5
)
coldest_day = prism["tmax"].mean(("y", "x")).argmin("time")
"""),
        markdown("## Pipes · Express each analysis as one sentence"),
        code("""
from cubedynamics import pipe, verbs as v

maximum_temperature_anomaly = (
    pipe(prism["tmax"])
    | v.anomaly(dim="time")
).unwrap()

regional_diurnal_range = (
    pipe(prism["diurnal_range"])
    | v.mean(dim=("y", "x"))
).unwrap()
"""),
        markdown("## Figure · Put the spatial and temporal answers together"),
        code("""
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
maximum_temperature_anomaly.isel(time=coldest_day).plot(
    ax=axes[0], cmap="RdBu_r", center=0, cbar_kwargs={"label": "Anomaly (°C)"}
)
date = str(prism.time.isel(time=coldest_day).values)[:10]
axes[0].set_title(f"Maximum-temperature anomaly · {date}")
regional_diurnal_range.plot(ax=axes[1], marker="o", color="#775a3a")
axes[1].set_title("Boulder-region diurnal temperature range")
axes[1].set_ylabel("Daily range (°C)")
plt.show()
"""),
        markdown("""
## What the figure tells us

The coldest regional day was not equally unusual everywhere, while the
day-to-night range followed a separate trajectory.

## Try the next variation

Pipe `tmin` through the same anomaly verb and compare its spatial pattern.
"""),
    ),
    "grammar_basics.ipynb": notebook(
        markdown(f"""
# 04 · Read the analysis from left to right

## Context

CubeDynamics makes the order of operations visible: a cube flows through small
verbs instead of disappearing inside a long function call.

## Question

Does the pipe grammar change the calculation, or only make the method easier
to read and extend?

## Analysis story

We compare direct and piped standardization exactly, then compose a regional
anomaly in one compact expression.

{DATA_NOTE}
"""),
        markdown("## Prepare · Select an observed temperature cube"),
        code(LOAD_PRISM + """
# Keep the labeled PRISM DataArray intact as it enters the grammar.
cube = prism["tmax"]
cube
"""),
        markdown("## Pipe · Verify equivalence, then compose"),
        code("""
import numpy as np
from cubedynamics import pipe, verbs as v

# The grammar must preserve the mathematical definition of a z-score.
direct = (cube - cube.mean("time")) / cube.std("time")
through_grammar = (pipe(cube) | v.zscore(dim="time")).unwrap()
np.testing.assert_allclose(through_grammar, direct, rtol=1e-6, atol=1e-6)

# The method reads left to right: anomaly first, then spatial mean.
regional_anomaly = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"))
).unwrap()
"""),
        markdown("## Figure · See the effect of each method"),
        code("""
import matplotlib.pyplot as plt

site = cube.isel(y=12, x=12)
fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True, constrained_layout=True)
site.plot(ax=axes[0], marker="o", color="#8f513b")
axes[0].set_title("Observed PRISM maximum temperature")
axes[0].set_ylabel("°C")
through_grammar.isel(y=12, x=12).plot(ax=axes[1], marker="o", color="#3b6d74")
axes[1].axhline(0, color="0.4", linewidth=0.8)
axes[1].set_title("pipe(cube) | v.zscore(dim='time')")
axes[1].set_ylabel("Standard deviations")
regional_anomaly.plot(ax=axes[2], marker="o", color="#5b6848")
axes[2].axhline(0, color="0.4", linewidth=0.8)
axes[2].set_title("pipe(cube) | v.anomaly(...) | v.mean(dim=('y', 'x'))")
axes[2].set_ylabel("Regional anomaly (°C)")
plt.show()
"""),
        markdown("""
## What the figure tells us

The exact comparison proves that the pipe is a composition language, not a new
statistical definition. Its advantage is a method that remains visible.

## Try the next variation

Replace the final mean with a variance and explain how the question changes.
"""),
    ),
    "verbs_gallery.ipynb": notebook(
        markdown(f"""
# 05 · One cube, six analytical views

## Context

Verbs should be small enough to understand independently and consistent enough
to combine. Every panel answers a real question about the same observations.

## Question

How do summaries, departures, standardization, clipping, and reshaping reveal
different aspects of January minimum temperature?

## Analysis story

Each result begins from the same PRISM cube, so the verb remains the focus.

{DATA_NOTE}
"""),
        markdown("## Prepare · Use the reviewed minimum-temperature cube"),
        code(LOAD_PRISM + """
cube = prism["tmin"]
cube
"""),
        markdown("## Pipes · Build a small, auditable verb gallery"),
        code("""
from cubedynamics import pipe, verbs as v

temporal_mean = (pipe(cube) | v.mean(dim="time")).unwrap()
temporal_variance = (pipe(cube) | v.variance(dim="time")).unwrap()
anomaly = (pipe(cube) | v.anomaly(dim="time")).unwrap()
standardized = (pipe(cube) | v.zscore(dim="time")).unwrap()
bounded = (pipe(standardized) | v.apply(lambda x: x.clip(-2, 2))).unwrap()
flat = (pipe(cube) | v.flatten_cube()).unwrap()

# Flattening changes layout, not the number of observed spatial samples.
assert flat.sizes["sample"] == cube.sizes["y"] * cube.sizes["x"]
"""),
        markdown("## Figure · Compare what each verb preserves and changes"),
        code("""
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 3, figsize=(12, 7), constrained_layout=True)
temporal_mean.plot(ax=axes[0, 0], cmap="coolwarm", cbar_kwargs={"label": "°C"})
axes[0, 0].set_title("Mean through time")
temporal_variance.plot(ax=axes[0, 1], cmap="viridis", cbar_kwargs={"label": "°C²"})
axes[0, 1].set_title("Variance through time")
anomaly.isel(time=15).plot(ax=axes[0, 2], cmap="RdBu_r", center=0)
axes[0, 2].set_title("Anomaly · 16 January")
standardized.isel(y=12, x=12).plot(ax=axes[1, 0], color="#356d76")
axes[1, 0].set_title("Standardized site history")
bounded.isel(time=15).plot(ax=axes[1, 1], cmap="RdBu_r", vmin=-2, vmax=2)
axes[1, 1].set_title("Custom clipped z-score")
flat.mean("sample").plot(ax=axes[1, 2], color="#6b6544")
axes[1, 2].set_title("Flattened regional mean")
plt.show()
"""),
        markdown("""
## What the figure tells us

Summary verbs remove dimensions deliberately; anomaly and z-score preserve the
cube; `apply` opens a controlled extension point; flattening changes layout.

## Try the next variation

Change the clipping bound and identify which dates and places are affected.
"""),
    ),
    "states_and_events.ipynb": notebook(
        markdown(f"""
# 06 · From cold observations to event evidence

## Context

A threshold is useful when its meaning is explicit. Here, severe cold means an
observed PRISM daily minimum below −10 °C.

## Question

Where did severe cold persist for at least two days, and how synchronized was
its occurrence with the center of the study region?

## Analysis story

We move from temperature to states, from states to events, and from states to a
synchrony map. Each transition is one named verb.

{DATA_NOTE}
"""),
        markdown("## Prepare · Keep the threshold next to its units"),
        code(LOAD_PRISM + """
cube = prism["tmin"]
assert cube.attrs["units"] == "degC"
"""),
        markdown("## Pipes · Keep state, event, and synchrony questions separate"),
        code("""
from cubedynamics import pipe, verbs as v

severe_cold = (
    pipe(cube)
    | v.threshold_state(threshold=-10.0, direction="below", name="severe_cold")
).unwrap()

events = (pipe(severe_cold) | v.detect_events(min_duration=2)).unwrap()

synchrony = (
    pipe(severe_cold)
    | v.occurrence_synchrony(spatial_mode="reference", reference="center")
).unwrap()

assert len(events.catalog) > 0
"""),
        markdown("## Figure · Follow the evidence from values to events"),
        code("""
import matplotlib.pyplot as plt

event_count = events.dataset["event_active"].sum("time")
reference_sync = synchrony["occurrence_synchrony"].isel(time_window_end=0)

fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
cube.isel(time=15).plot(ax=axes[0, 0], cmap="coolwarm", cbar_kwargs={"label": "°C"})
axes[0, 0].set_title("Observed minimum temperature · 16 January")
severe_cold["state"].isel(time=15).plot(ax=axes[0, 1], cmap="Blues", add_colorbar=False)
axes[0, 1].set_title("Below −10 °C state")
event_count.plot(ax=axes[1, 0], cmap="magma", cbar_kwargs={"label": "Event days"})
axes[1, 0].set_title("Days retained in ≥2-day events")
reference_sync.plot(ax=axes[1, 1], cmap="viridis", vmin=0, vmax=1)
axes[1, 1].set_title("Occurrence synchrony with center cell")
plt.show()
"""),
        markdown("""
## What the figure tells us

The threshold isolates the observed mid-January outbreak. Duration filtering
distinguishes persistence, while synchrony shows where its timing matched the
region's center.

## Try the next variation

Change only the threshold to −15 °C and compare retained events.
"""),
    ),
    "custom_verb_project.ipynb": notebook(
        markdown(f"""
# 07 · Build a project-owned verb

## Context

The core package supplies the grammar; projects supply domain verbs. A good
custom verb states its input contract and returns labeled data.

## Question

How much below-freezing exposure accumulated across the observed January
minimum-temperature record?

## Analysis story

We write one small verb, test direct and piped use, then visualize its state
and magnitude outputs.

{DATA_NOTE}
"""),
        markdown("## Define · Make the scientific contract visible in code"),
        code('''
import xarray as xr

def freezing_exposure(threshold=0.0):
    """Convert Celsius temperature to freezing state and magnitude."""
    def _op(cube):
        if cube.attrs.get("units") != "degC":
            raise ValueError("freezing_exposure requires units='degC'")
        if "time" not in cube.dims:
            raise ValueError("freezing_exposure requires a time dimension")

        state = cube <= threshold
        magnitude = (threshold - cube).where(state, 0.0)
        result = xr.Dataset({"state": state, "magnitude": magnitude})
        result.attrs.update(
            analysis="freezing_exposure",
            threshold_degC=float(threshold),
            source=cube.attrs.get("source", ""),
            is_synthetic=cube.attrs.get("is_synthetic", 0),
        )
        return result
    return _op
'''),
        markdown("## Pipe · Test both forms on real observations"),
        code(LOAD_PRISM + """
import numpy as np
from cubedynamics import pipe

cube = prism["tmin"]
direct = freezing_exposure(-5.0)(cube)
through_grammar = (pipe(cube) | freezing_exposure(-5.0)).unwrap()

np.testing.assert_array_equal(through_grammar["state"], direct["state"])
np.testing.assert_allclose(through_grammar["magnitude"], direct["magnitude"])
"""),
        markdown("## Figure · Interpret the custom verb's two outputs"),
        code("""
import matplotlib.pyplot as plt

freezing_fraction = through_grammar["state"].mean(("y", "x"))
cumulative_exposure = through_grammar["magnitude"].sum("time")

fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8), constrained_layout=True)
freezing_fraction.plot(ax=axes[0], marker="o", color="#365f79")
axes[0].set_title("Region below −5 °C each day")
axes[0].set_ylabel("Fraction of PRISM cells")
cumulative_exposure.plot(
    ax=axes[1], cmap="magma", cbar_kwargs={"label": "Degree-days below −5 °C"}
)
axes[1].set_title("Cumulative cold exposure")
plt.show()
"""),
        markdown("""
## What the figure tells us

The custom verb separates occurrence from intensity. Its code remains a small
project extension, while `pipe` supplies the shared composition language.

## Try the next variation

Compose this verb with `v.detect_events` rather than embedding event detection.
"""),
    ),
    "lazy_composition.ipynb": notebook(
        markdown(f"""
# 08 · Stay lazy until the answer is requested

## Context

Real cube archives quickly outgrow memory. Lazy arrays let us describe a
method first and materialize only the final analysis.

## Question

Can a composed pipe preserve Dask-backed execution while computing a compact
spatial summary from real observations?

## Analysis story

We open the reviewed fixture with chunks, compose anomaly and variance verbs,
confirm that the result stays lazy, and compute only the final map.

{DATA_NOTE}
"""),
        markdown("## Prepare · Open the official extract as a chunked cube"),
        code("""
from pathlib import Path
import xarray as xr

# The checked-in extract makes the lesson reproducible without a live service.
data_path = next(
    candidate / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc"
    for candidate in (Path.cwd(), *Path.cwd().parents)
    if (candidate / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc").exists()
)
cube = xr.open_dataset(
    data_path,
    engine="scipy",
    chunks={"time": 10, "y": 12, "x": 12},
)["tmax"]

assert cube.attrs["is_synthetic"] == 0
assert hasattr(cube.data, "chunks")
cube
"""),
        markdown("## Pipe · Describe the method without triggering computation"),
        code("""
from cubedynamics import pipe, verbs as v

lazy_variability = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time")
).unwrap()

assert hasattr(lazy_variability.data, "chunks")
lazy_variability
"""),
        markdown("## Figure · Compute only the final spatial answer"),
        code("""
import matplotlib.pyplot as plt

variability = lazy_variability.compute()
assert not hasattr(variability.data, "chunks")

fig, ax = plt.subplots(figsize=(6.5, 4.5), constrained_layout=True)
variability.plot(ax=ax, cmap="viridis", cbar_kwargs={"label": "Anomaly variance (°C²)"})
ax.set_title("January maximum-temperature variability")
plt.show()
"""),
        markdown("""
## What the figure tells us

The final map identifies locations with more variable departures while the
intermediate anomaly cube remained lazy.

## Try the next variation

Change chunk sizes and confirm that final values remain identical.
"""),
    ),
}


def main() -> None:
    VIGNETTE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in NOTEBOOKS.items():
        path = VIGNETTE_DIR / name
        content = with_shell(content, f"docs/vignettes/{name}")
        path.write_text(json.dumps(content, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
