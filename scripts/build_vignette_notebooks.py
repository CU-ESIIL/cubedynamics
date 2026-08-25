#!/usr/bin/env python3
"""Build the small, source-controlled publication vignettes.

The notebook content is kept here as plain text so metadata and cell structure
can be reviewed and regenerated consistently. Run this script only when editing
the vignettes; normal validation uses ``scripts/run_vignettes.py``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


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
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NOTEBOOKS = {
    "cube_from_arrays.ipynb": notebook(
        markdown(
            """
# 01 · From an array to a scientific cube

## Context

A simulation has returned monthly temperature values as a three-dimensional
NumPy array. The numbers are useful, but the axes do not yet say which direction
is time, latitude, or longitude.

## Question

How can we turn those values into a self-describing scientific object and
inspect both its spatial and temporal structure?

## Analysis story

We will name the axes and attach coordinates, units, and provenance. Then we
will compare two familiar slices before sending the same cube through one
minimal plotting pipe into CubeDynamics' interactive viewer.
"""
        ),
        markdown("## Give the array space, time, a name, units, and provenance"),
        code(
            """
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

# Coordinates turn anonymous array axes into scientific dimensions. Here each
# monthly time step contains a 5-row × 6-column spatial grid.
time = pd.date_range("2025-01-01", periods=18, freq="MS")
y = np.linspace(40.4, 39.6, 5)
x = np.linspace(-105.5, -104.5, 6)

# The singleton axes make NumPy broadcast a temporal signal across space and a
# spatial signal across time. Their sum has shape (time, y, x).
month = np.arange(time.size)[:, None, None]
season = 8 * np.sin(2 * np.pi * month / 12)
spatial = 3 * (y[None, :, None] - y.mean()) - 2 * (x[None, None, :] - x.mean())

# A DataArray pairs values with dimension names, coordinates, a variable name,
# units, and provenance—the minimum useful cube contract for these examples.
cube = xr.DataArray(
    16 + season + spatial,
    dims=("time", "y", "x"),
    coords={"time": time, "y": y, "x": x},
    name="air_temperature",
    attrs={"units": "degC", "source": "deterministic vignette example"},
)

# Assertions double as executable documentation: if the cube contract changes,
# the notebook stops here with a useful failure instead of producing a bad plot.
assert cube.dims == ("time", "y", "x")
cube
"""
        ),
        markdown(
            """
## Figure 1 · Read the cube in familiar views

Before using an interactive cube, compare a single map with the history of one
pixel. Both views come from the same labeled object.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# Two familiar 2D views help participants understand the 3D object: isel chooses
# a slice by integer position; sel chooses one location by coordinate value.
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
cube.isel(time=6).plot(ax=axes[0], cmap="magma", cbar_kwargs={"label": "°C"})
axes[0].set_title("One spatial slice")
cube.sel(y=y[2], x=x[3]).plot(ax=axes[1], marker="o", color="#2f6f6d")
axes[1].set_title("One pixel through time")
axes[1].set_ylabel("Air temperature (°C)")
plt.show()
"""
        ),
        markdown(
            """
## Pipe · Open the repository-native cube viewer

The analytical sentence is deliberately small. `pipe` introduces the value,
`v.plot` says what to do, and `unwrap()` returns the viewer object. Drag the
resulting cube to rotate it and use the wheel or trackpad to zoom.
"""
        ),
        code(
            """
from html import escape

from IPython.display import HTML

# The scientific intent stays visible even though the renderer is sophisticated.
viewer = (
    pipe(cube)
    | v.plot(title="Synthetic air-temperature cube", cmap="magma")
).unwrap()

# Escape the viewer's complete HTML document into an iframe srcdoc so it cannot
# interfere with the surrounding documentation header or styles.
assert viewer.data.dims == ("time", "y", "x")
viewer_srcdoc = escape(viewer.to_html(), quote=True)
HTML(
    f'''<iframe
        title="Interactive synthetic air-temperature cube"
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

The map shows a smooth spatial gradient while the pixel history preserves the
seasonal cycle. The interactive viewer confirms that these are not separate
products: they are different readings of one `(time, y, x)` cube.

## Try the next variation

Change the seasonal amplitude or reverse the `y` coordinates. Which visual
features change, and which parts of the pipe remain identical?
"""
        ),
    ),
    "cube_from_tidy_table.ipynb": notebook(
        markdown(
            """
# 02 · From observations to a comparable signal

## Context

A sensor network stores one observation per date and location in a tidy table.
The sites share a weekly temperature pattern, but their raw values differ
slightly because of geography.

## Question

How can we reshape the observations into a cube and compare change through time
on the same scale at every site?

## Analysis story

We will turn coordinate columns into cube dimensions, standardize each pixel
through time with one verb, and compare one site's raw and standardized series.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd

from cubedynamics import pipe, verbs as v

# Build every time/location combination. Real field data would usually be read
# from CSV or Parquet, but the following table has the same tidy structure.
time = pd.date_range("2025-06-01", periods=14, freq="D")
y = [40.2, 40.0, 39.8]
x = [-105.2, -105.0, -104.8, -104.6]
index = pd.MultiIndex.from_product([time, y, x], names=["time", "y", "x"])
table = index.to_frame(index=False)

# Create a deterministic weekly cycle plus small latitude/longitude effects.
# Vectorized columns keep the recipe close to ordinary pandas workflows.
day = (table["time"] - time[0]).dt.days.to_numpy()
table["temperature"] = (
    27
    + 5 * np.sin(2 * np.pi * day / 7)
    + 1.5 * (table["y"].to_numpy() - 40)
    - 0.8 * (table["x"].to_numpy() + 105)
)

# Indexing by time, y, and x tells xarray which columns define cube axes.
# transpose makes the conventional (time, y, x) order explicit.
cube = (
    table.set_index(["time", "y", "x"])
    .to_xarray()["temperature"]
    .transpose("time", "y", "x")
)
cube.name = "temperature"
cube.attrs.update(units="degC", source="synthetic tidy table")

assert cube.shape == (14, 3, 4)
cube
"""
        ),
        markdown(
            """
## Pipe · Standardize every location through time

Data preparation is complete. The full analytical method is now one verb:
`v.zscore(dim="time")`.
"""
        ),
        code(
            """
standardized = (
    pipe(cube)
    | v.zscore(dim="time")
).unwrap()

# A temporal z-score should have mean zero at every location (up to rounding).
assert abs(float(standardized.mean("time").max())) < 1e-12
standardized
"""
        ),
        markdown(
            """
## Figure · Compare before and after

Hold the location constant so the visual difference comes from the verb rather
than from comparing different sites.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# Compare the same coordinate before and after the verb so its effect is clear.
site = {"y": 40.0, "x": -105.0}
fig, axes = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True, constrained_layout=True)
cube.sel(**site).plot(ax=axes[0], marker="o", color="#8b543c")
axes[0].set_title("Table values after reshaping to a cube")
axes[0].set_ylabel("Temperature (°C)")
standardized.sel(**site).plot(ax=axes[1], marker="o", color="#3f6f72")
axes[1].axhline(0, color="0.35", linewidth=0.8)
axes[1].set_title("The same pixel after v.zscore(dim='time')")
axes[1].set_ylabel("Standard deviations")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

The peaks and troughs occur on the same dates in both panels, but the lower
panel expresses them as deviations from that site's own mean. The pipe changed
the scale, not the temporal story.

## Try the next variation

Select another site or replace `v.zscore` with `v.anomaly`. Which comparison is
more useful for your scientific question?
"""
        ),
    ),
    "cube_from_dataset.ipynb": notebook(
        markdown(
            """
# 03 · Two variables, two questions

## Context

A field campaign has collected temperature and precipitation on the same grid.
The variables align in space and time, but they answer different questions and
carry different units.

## Question

Where is the latest temperature unusual, and how did average precipitation
change across the region?

## Analysis story

We will keep both variables in one xarray `Dataset`, select each by meaning, and
write a separate compact pipe for each scientific question.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

# A fixed seed makes the example exactly repeatable while still looking like
# measurements with natural variation.
rng = np.random.default_rng(19)
time = pd.date_range("2024-04-01", periods=20, freq="D")
y = np.linspace(41.0, 40.0, 4)
x = np.linspace(-106.0, -105.0, 5)
temperature = 18 + np.linspace(0, 7, time.size)[:, None, None] + rng.normal(0, 1, (20, 4, 5))
precipitation = rng.gamma(1.4, 2.2, size=(20, 4, 5))

# A Dataset is a labeled collection of aligned DataArrays. Each variable has
# its own units but shares the same time/y/x coordinate system.
dataset = xr.Dataset(
    {
        "temperature": (("time", "y", "x"), temperature, {"units": "degC"}),
        "precipitation": (("time", "y", "x"), precipitation, {"units": "mm day-1"}),
    },
    coords={"time": time, "y": y, "x": x},
    attrs={"source": "deterministic multi-variable example"},
)
dataset
"""
        ),
        markdown(
            """
## Pipes · Let each question choose its verb

The first pipe preserves a cube of anomalies. The second deliberately reduces
the two spatial dimensions to one regional time series.
"""
        ),
        code(
            """
# Question 1: how unusual is temperature at every grid cell?
temperature_anomaly = (
    pipe(dataset["temperature"])
    | v.anomaly(dim="time")
).unwrap()

# Question 2: what was the region-wide precipitation on each date?
regional_precipitation = (
    pipe(dataset["precipitation"])
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()

assert temperature_anomaly.dims == ("time", "y", "x")
assert regional_precipitation.dims == ("time",)
"""
        ),
        markdown(
            """
## Figure · Bring the answers together

The outputs have different shapes because the questions differ: a map for
spatial departures and a line for regional change through time.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# The side-by-side views answer different questions from the same Dataset.
fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), constrained_layout=True)
temperature_anomaly.isel(time=-1).plot(
    ax=axes[0], cmap="RdBu_r", center=0, cbar_kwargs={"label": "°C anomaly"}
)
axes[0].set_title("Latest temperature anomaly")
regional_precipitation.plot(ax=axes[1], marker="o", color="#2f6267")
axes[1].set_title("Spatial mean precipitation")
axes[1].set_ylabel("mm day⁻¹")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

Temperature departures vary across the final map, while precipitation is
summarized as one value per date. A shared `Dataset` does not force a shared
analysis; each short pipe makes its own question and output shape explicit.

## Try the next variation

Compute a precipitation anomaly instead of a spatial mean. How does the output
shape—and therefore the figure you would choose—change?
"""
        ),
    ),
    "grammar_basics.ipynb": notebook(
        markdown(
            """
# 04 · Write the analysis as a sentence

## Context

A collaborator needs to review a transformation before trusting its result.
They should be able to distinguish the input, each scientific operation, and
the point where ordinary Python resumes without reading framework machinery.

## Question

Can a complete method remain both compact and explicit?

## Analysis story

We will compare direct and piped calls, then compose a built-in anomaly with an
ordinary project function. The pipe is the readable analytical sentence; the
surrounding cells provide evidence and interpretation.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

# This signal combines a repeating temporal pattern, a spatial offset, and a
# tiny seeded noise term so each operation has something visible to transform.
rng = np.random.default_rng(42)
time = pd.date_range("2024-01-01", periods=12, freq="MS")
season = np.sin(np.linspace(0, 2 * np.pi, time.size, endpoint=False))[:, None, None]
spatial = np.array([[0.0, 0.2, 0.4], [0.1, 0.3, 0.5]])[None, :, :]
cube = xr.DataArray(
    season + spatial + rng.normal(0, 0.02, size=(12, 2, 3)),
    dims=("time", "y", "x"),
    coords={"time": time, "y": [40.1, 40.0], "x": [-105.2, -105.1, -105.0]},
    name="environmental_signal",
    attrs={"units": "1", "source": "deterministic synthetic vignette"},
)
cube
"""
        ),
        markdown(
            """
## Pipe · Read from top to bottom

`pipe(cube)` supplies the subject. Each verb adds one operation. `unwrap()`
marks the return to xarray and ordinary Python.
"""
        ),
        code(
            """
# Direct and piped calls use the same verb contract.
direct = v.zscore(dim="time")(cube)
through_pipe = (
    pipe(cube)
    | v.zscore(dim="time")
).unwrap()

# v.apply lets a compatible project function join the same sentence.
scaled_anomaly = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.apply(lambda value, factor: value * factor, factor=1.5)
).unwrap()

# This is a compact regression test embedded in the lesson.
xr.testing.assert_allclose(direct, through_pipe)
"""
        ),
        markdown(
            """
## Figure · Verify meaning, not just syntax

Compare the same location before and after standardization, then check that the
composed anomaly still preserves the spatial cube.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# Hold location constant so the first two panels compare like with like; use a
# map in the third panel to show that the full spatial cube was preserved.
site = {"y": 40.0, "x": -105.1}
fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), constrained_layout=True)
cube.sel(**site).plot(ax=axes[0], color="#8b543c")
axes[0].set_title("Input cube at one pixel")
through_pipe.sel(**site).plot(ax=axes[1], color="#3f6f72")
axes[1].axhline(0, color="0.4", linewidth=0.8)
axes[1].set_title("Direct call = pipe call")
scaled_anomaly.isel(time=3).plot(ax=axes[2], cmap="RdBu_r", center=0)
axes[2].set_title("v.anomaly | v.apply")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

The standardized series retains timing while expressing values on a comparable
scale. The map shows that chaining `v.anomaly` and `v.apply` preserved spatial
structure. The code reads like the method because each line adds one idea.

## Try the next variation

Change the `factor` passed to `v.apply`, or insert `v.mean` at the end. Predict
the output shape before running the cell.
"""
        ),
    ),
    "verbs_gallery.ipynb": notebook(
        markdown(
            """
# 05 · Ask several questions of one cube

## Context

A single environmental record can support several legitimate summaries. A
researcher may care about typical conditions, variability, departures from a
baseline, comparable scales, or a matrix suitable for modeling.

## Question

How does the choice of verb change both the scientific meaning and the shape of
the result?

## Analysis story

We will hold the evidence constant and vary only the analytical question. A
small set of parallel pipes makes those choices easy to compare.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

# Build one cube with temporal trend, seasonality, spatial structure, and noise.
# Every verb below therefore starts from exactly the same evidence.
rng = np.random.default_rng(8)
time = pd.date_range("2023-01-01", periods=24, freq="MS")
y = np.arange(5)
x = np.arange(6)
trend = np.linspace(0, 2, time.size)[:, None, None]
season = 2 * np.sin(2 * np.pi * np.arange(time.size)[:, None, None] / 12)
landscape = np.linspace(-1, 1, y.size)[None, :, None] + np.linspace(0, 1, x.size)[None, None, :]
cube = xr.DataArray(
    10 + trend + season + landscape + rng.normal(0, 0.3, (24, 5, 6)),
    dims=("time", "y", "x"),
    coords={"time": time, "y": y, "x": x},
    name="signal",
)
cube
"""
        ),
        markdown(
            """
## Pipes · One input, six analytical questions

Each expression is intentionally short. Reducers remove a dimension,
transforms preserve it, and `v.flatten_space` prepares a matrix for modeling.
"""
        ),
        code(
            """
# What is typical at each location?
mean_map = (
    pipe(cube)
    | v.mean(dim="time", keep_dim=False)
).unwrap()

# Where does the signal vary most?
variance_map = (
    pipe(cube)
    | v.variance(dim="time", keep_dim=False)
).unwrap()

# How far is each value from its local baseline?
anomaly = (
    pipe(cube)
    | v.anomaly(dim="time")
).unwrap()

# How unusual is each value on a common scale?
zscore = (
    pipe(cube)
    | v.zscore(dim="time")
).unwrap()

# How can a project rule limit extreme standardized values?
clipped = (
    pipe(zscore)
    | v.apply(lambda value: value.clip(min=-1, max=1))
).unwrap()

# How can the anomaly become a time × feature matrix?
flat = (
    pipe(anomaly)
    | v.flatten_space(new_dim="pixel")
).unwrap()

assert flat.dims == ("time", "pixel")
"""
        ),
        markdown(
            """
## Figure · Compare the consequences

The six panels make shape and meaning visible. Read each title as the question
answered by the pipe above it.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# Each panel is labeled with the verb and the question its output can answer.
fig, axes = plt.subplots(2, 3, figsize=(12, 7), constrained_layout=True)
mean_map.plot(ax=axes[0, 0], cmap="viridis")
axes[0, 0].set_title("v.mean: typical spatial pattern")
variance_map.plot(ax=axes[0, 1], cmap="magma")
axes[0, 1].set_title("v.variance: variable locations")
anomaly.isel(time=-1).plot(ax=axes[0, 2], cmap="RdBu_r", center=0)
axes[0, 2].set_title("v.anomaly: departure from normal")
zscore.sel(y=2, x=3).plot(ax=axes[1, 0], color="#3f6f72")
axes[1, 0].axhline(0, color="0.45", linewidth=0.8)
axes[1, 0].set_title("v.zscore: comparable units")
clipped.isel(time=-1).plot(ax=axes[1, 1], cmap="RdBu_r", vmin=-1, vmax=1)
axes[1, 1].set_title("v.apply: project function")
axes[1, 2].imshow(flat.values.T, aspect="auto", cmap="RdBu_r")
axes[1, 2].set(title="v.flatten_space: time × pixel", xlabel="time index", ylabel="pixel")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

No verb is universally “best.” Means and variance summarize across time;
anomalies and z-scores preserve timing; clipping expresses a project decision;
flattening changes representation for a downstream model. The pipe keeps each
choice visible and reviewable.

## Try the next variation

Add one new pipe with `v.sum`, or change the reduction dimension from `time` to
space. State the question first, then choose the verb.
"""
        ),
    ),
    "states_and_events.ipynb": notebook(
        markdown(
            """
# 06 · Follow heat from value to event

## Context

Daily maximum temperature is continuous, but many impact questions concern
episodes: when heat crossed a meaningful threshold, how long it persisted, and
whether nearby locations experienced it together.

## Question

Where did multi-day heat events occur, and how closely did their occurrence
match the center of the study area?

## Analysis story

We will move through three scientific representations—value, state, and
event—then compare occurrence in space. Specialized verbs extend the same
minimal grammar rather than creating a separate workflow language.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

# The two pulse groups create two heat episodes. Adding a spatial offset makes
# some pixels cross the threshold sooner or remain active longer than others.
time = pd.date_range("2025-07-01", periods=14, freq="D")
y = [40.2, 40.0, 39.8]
x = [-105.2, -105.0, -104.8]
pulse = np.array([0, 0, 5, 7, 6, 0, 0, 4, 6, 7, 5, 0, 0, 0])[:, None, None]
spatial = np.array([[-1.0, 0.0, 0.5], [-0.5, 1.0, 1.5], [-1.0, 0.5, 2.0]])[None, :, :]
cube = xr.DataArray(
    29 + pulse + spatial,
    dims=("time", "y", "x"),
    coords={"time": time, "y": y, "x": x},
    name="daily_max_temperature",
    attrs={"units": "degC"},
)
cube
"""
        ),
        markdown(
            """
## Pipes · Translate values into episodes and relationships

Each pipe names one conceptual step. Keeping them separate lets us inspect the
state Dataset before detecting events or measuring synchrony.
"""
        ),
        code(
            """
# Which observations count as hot days?
states = (
    pipe(cube)
    | v.threshold_state(threshold=34.0, direction="above", name="hot_day")
).unwrap()

# Which hot spells persist for at least two days?
events = (
    pipe(states)
    | v.detect_events(min_duration=2, max_gap=0)
).unwrap()

# Where does hot-day occurrence match the center pixel?
synchrony = (
    pipe(states)
    | v.occurrence_synchrony(spatial_mode="reference", reference="center")
).unwrap()

# These checks document the output contracts before visualization.
assert states["state"].dtype == bool
assert len(events.catalog) > 0
"""
        ),
        markdown(
            """
## Figure · Read the progression from value to relation

The event catalog is tabular, so we count catalog rows at each pixel for a map.
That small presentation step is intentionally outside the scientific pipes.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# EventResult deliberately separates a cube-like Dataset from a tabular event
# catalog. Accumulate catalog rows here to make an event-count map for teaching.
event_count = xr.zeros_like(cube.isel(time=0), dtype=int)
for row in events.catalog.itertuples():
    event_count.values[row.y_index, row.x_index] += 1
sync_map = synchrony["occurrence_synchrony"].isel(time_window_end=0)

# The four panels tell the full progression: value → state → event → relation.
fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
cube.mean(("y", "x")).plot(ax=axes[0, 0], marker="o", color="#8b543c")
axes[0, 0].axhline(34, color="0.3", linestyle="--", label="threshold")
axes[0, 0].legend()
axes[0, 0].set_title("Continuous regional temperature")
states["state"].mean(("y", "x")).plot(ax=axes[0, 1], marker="o", color="#3f6f72")
axes[0, 1].set_title("v.threshold_state: active fraction")
event_count.plot(ax=axes[1, 0], cmap="YlOrRd", vmin=0)
axes[1, 0].set_title("v.detect_events: events per pixel")
sync_map.plot(ax=axes[1, 1], cmap="viridis", vmin=0, vmax=1)
axes[1, 1].set_title("v.occurrence_synchrony: reference map")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

The regional series crosses the threshold twice. The active-fraction panel
shows that sites enter those episodes differently, the event map counts
qualifying runs, and the synchrony map shows where timing most closely matches
the center pixel.

## Try the next variation

Raise the threshold or allow a one-day gap in `v.detect_events`. Which change
alters event identity, and which changes only state classification?
"""
        ),
    ),
    "custom_verb_project.ipynb": notebook(
        markdown(
            """
# 07 · Give a project its own verb

## Context

A research team defines heat stress as temperature at or above 35 °C. That
threshold is a project assumption, not a universal CubeDynamics primitive, but
the team still wants its method to compose cleanly with the shared grammar.

## Question

How can a project package its scientific rule as a reusable verb without
modifying CubeDynamics itself?

## Analysis story

We will write a small callable factory, apply it in one readable pipe, verify
the direct and piped forms agree, and visualize both occurrence and magnitude.
"""
        ),
        code(
            """
import xarray as xr

from cubedynamics import pipe


def heat_stress(*, threshold: float = 35.0):
    '''Return a project-owned cube → Dataset verb.'''
    # The outer function captures user configuration. CubeDynamics pipes call
    # the inner function later with the value currently moving through the pipe.
    def _op(cube: xr.DataArray) -> xr.Dataset:
        # Fail early when the incoming object cannot satisfy this method's
        # scientific contract.
        if "time" not in cube.dims:
            raise ValueError("heat_stress requires a 'time' dimension")

        # Keep occurrence (state) separate from excess heat (magnitude). A
        # Dataset lets downstream verbs choose the component they need.
        state = (cube >= threshold).rename("state")
        magnitude = (cube - threshold).where(state, 0).rename("magnitude")
        result = xr.Dataset({"state": state, "magnitude": magnitude})

        # Preserve input provenance and record the project method configuration.
        result.attrs.update(cube.attrs)
        result.attrs.update(project_verb="heat_stress", threshold=float(threshold))
        return result

    # Returning the callable—not a computed result—is what makes this a verb
    # factory compatible with pipe(cube) | heat_stress(...).
    return _op
"""
        ),
        markdown(
            """
## Prepare a small test case

A project verb needs a deterministic example that crosses the threshold at
different times and locations. This becomes both a lesson and a regression
fixture for the project's scientific contract.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd


# Build a small heat pulse with spatial offsets so state and magnitude differ
# across both time and location.
time = pd.date_range("2025-07-01", periods=10, freq="D")
y = [1, 0]
x = [0, 1, 2]
pulse = np.array([0, 1, 3, 6, 8, 5, 2, 0, -1, 1])[:, None, None]
spatial = np.array([[-1.0, 0.0, 1.0], [0.0, 1.0, 2.0]])[None, :, :]
temperature = xr.DataArray(
    31 + pulse + spatial,
    dims=("time", "y", "x"),
    coords={"time": time, "y": y, "x": x},
    name="air_temperature",
    attrs={"units": "degC", "source": "deterministic synthetic vignette"},
)
temperature
"""
        ),
        markdown(
            """
## Pipe · Apply the project rule

The project-owned verb fits the same analytical sentence as a built-in verb.
The direct call remains useful as a small equivalence test.
"""
        ),
        code(
            """
through_pipe = (
    pipe(temperature)
    | heat_stress(threshold=35.0)
).unwrap()

# A project verb should behave identically when called directly or through a
# pipe. This assertion is the first regression test a new add-on should keep.
direct = heat_stress(threshold=35.0)(temperature)
xr.testing.assert_identical(direct, through_pipe)
through_pipe
"""
        ),
        markdown(
            """
## Figure · Audit the scientific rule

Summaries belong outside the verb unless they are part of its stated contract.
Here we derive two communication-ready views from the returned Dataset.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# Reduce the Dataset into two communication-ready summaries: affected area
# through time and accumulated magnitude across the study period.
daily_fraction = through_pipe["state"].mean(("y", "x"))
cumulative_magnitude = through_pipe["magnitude"].sum("time")

# Plot input, occurrence, and magnitude together so participants can audit how
# the custom scientific rule produced its outputs.
fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), constrained_layout=True)
temperature.mean(("y", "x")).plot(ax=axes[0], marker="o", color="#8b543c")
axes[0].axhline(35, color="0.35", linestyle="--")
axes[0].set_title("Input and project threshold")
daily_fraction.plot(ax=axes[1], marker="o", color="#3f6f72")
axes[1].set_title("Derived heat-stress fraction")
axes[1].set_ylim(-0.05, 1.05)
cumulative_magnitude.plot(ax=axes[2], cmap="YlOrRd", cbar_kwargs={"label": "degree-days"})
axes[2].set_title("Derived cumulative magnitude")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

The threshold line explains when heat stress begins, the middle panel shows the
fraction of the study area affected each day, and the map accumulates excess
heat through time. The project rule is explicit in one verb, while the pipe
stays as small as a built-in analysis.

## Take it into a project

Move `heat_stress` into `my_project.verbs`, document why 35 °C is meaningful,
and keep the direct-versus-pipe regression test. The repository's
`examples/custom_verb_project/` directory provides a minimal package layout.
"""
        ),
    ),
    "lazy_composition.ipynb": notebook(
        markdown(
            """
# 08 · Scale the analysis lazily

## Context

A monthly cube has grown beyond comfortable in-memory analysis. The scientific
method should remain readable even when execution must be divided into bounded
chunks.

## Question

Can we compose an anomaly-variance analysis without loading the source cube,
then compute only the small final map needed for interpretation?

## Analysis story

We will place deterministic values behind Dask, apply the same two-verb grammar
used for in-memory cubes, inspect the deferred graph, and materialize only at an
explicit execution boundary.
"""
        ),
        code(
            """
import dask.array as da
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

# Start with ordinary NumPy values, then wrap them in a Dask array split into
# bounded chunks: 6 time steps × 4 rows × 5 columns per chunk.
rng = np.random.default_rng(7)
values = rng.normal(size=(24, 8, 10)).astype("float32")
lazy_values = da.from_array(values, chunks=(6, 4, 5))

# xarray adds scientific coordinates without changing the lazy Dask backing.
cube = xr.DataArray(
    lazy_values,
    dims=("time", "y", "x"),
    coords={
        "time": pd.date_range("2023-01-01", periods=24, freq="MS"),
        "y": np.arange(8),
        "x": np.arange(10),
    },
    name="signal",
    attrs={"source": "deterministic synthetic vignette"},
)

assert cube.chunks is not None
cube
"""
        ),
        markdown(
            """
## Pipe · Describe the work without executing it

Nothing about the analytical sentence mentions Dask. Laziness is a property of
the data, and the verbs preserve it.
"""
        ),
        code(
            """
result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time", keep_dim=False)
).unwrap()

# chunks proves the arrays remain lazy. Counting graph tasks is safe because it
# inspects the plan rather than computing the array values.
assert result.chunks is not None
graph_tasks = len(result.data.__dask_graph__())
graph_tasks
"""
        ),
        markdown(
            """
## Figure · Compute only at the interpretation boundary

`compute()` appears once and visibly. It materializes the reduced 2D result,
not the full source cube.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt

# compute() is the intentional execution boundary. Only the small final map is
# materialized, and that map—not the full source cube—is sent to Matplotlib.
materialized = result.compute()
assert materialized.chunks is None
fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
materialized.plot(ax=ax, cmap="magma", cbar_kwargs={"label": "anomaly variance"})
ax.set_title(f"Computed final map · graph previously had {graph_tasks} tasks")
plt.show()
"""
        ),
        markdown(
            """
## What the figure tells us

The map locates pixels with the greatest variance after removing each pixel's
mean. More importantly, the method stayed identical to an in-memory pipe; only
the final, explicit execution boundary changed.

## Try the next variation

Change the chunk sizes and inspect `graph_tasks` again. The execution plan will
change while the scientific pipe remains the same.
"""
        ),
    ),
}


def main() -> None:
    VIGNETTE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in NOTEBOOKS.items():
        path = VIGNETTE_DIR / name
        path.write_text(json.dumps(content, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
