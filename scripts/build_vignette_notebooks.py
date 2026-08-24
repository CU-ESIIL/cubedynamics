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
# 01 · Build a cube from arrays

Start here when a simulation, sensor, or raster workflow already gives you a
three-dimensional NumPy array. We give the axes scientific names and
coordinates, then view the same cube as a map, a time series, and an interactive
CubeDynamics cube.

**Pattern:** array → `xarray.DataArray` → `pipe(cube)` or a direct verb call.
"""
        ),
        markdown("## Give the array space, time, a name, units, and provenance"),
        code(
            """
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import verbs as v

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
    attrs={"units": "degC", "source": "deterministic hackathon example"},
)

# Assertions double as executable documentation: if the cube contract changes,
# the notebook stops here with a useful failure instead of producing a bad plot.
assert cube.dims == ("time", "y", "x")

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
## Open the repository-native cube viewer

Direct calls are useful when you want one operation immediately. Drag the
resulting HTML cube to rotate it and use the wheel or trackpad to zoom.
"""
        ),
        code(
            """
from html import escape

from IPython.display import HTML

# v.plot can also be called directly. Escape its complete HTML document into an
# iframe srcdoc so the viewer cannot interfere with the surrounding site header
# or styles and does not create a random helper file beside the notebook.
viewer = v.plot(cube, title="Synthetic air-temperature cube", cmap="magma")
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
    ),
    "cube_from_tidy_table.ipynb": notebook(
        markdown(
            """
# 02 · Build a cube from a tidy table

Field observations often arrive as one row per time and location. A complete
time × y × x table can become a cube by indexing its coordinate columns and
using xarray. We then call a verb directly and plot what standardization did.

**Pattern:** tidy `DataFrame` → indexed xarray cube → direct verb call.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cubedynamics import verbs as v

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

# Direct verb style: configure zscore first, then pass the cube to the returned
# callable. Each pixel is standardized independently along time.
standardized = v.zscore(dim="time")(cube)

# A temporal z-score should have mean zero at every location (up to rounding).
assert cube.shape == (14, 3, 4)
assert abs(float(standardized.mean("time").max())) < 1e-12

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
    ),
    "cube_from_dataset.ipynb": notebook(
        markdown(
            """
# 03 · Work with a multi-variable Dataset

An xarray `Dataset` can hold several aligned cubes. Select the variable whose
meaning matches a verb, run separate pipelines, and bring the results together
in one explanatory figure.

**Pattern:** `Dataset` → select a `DataArray` → one pipeline per scientific question.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt
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

# Select one variable before applying a verb whose scientific meaning matches
# it. anomaly preserves the cube shape while subtracting each pixel's mean.
temperature_anomaly = (
    pipe(dataset["temperature"])
    | v.anomaly(dim="time")
).unwrap()

# Reducing both spatial axes produces one regional value for every date.
# keep_dim=False intentionally returns a 1D time series rather than a 3D cube.
regional_precipitation = (
    pipe(dataset["precipitation"])
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()

assert temperature_anomaly.dims == ("time", "y", "x")
assert regional_precipitation.dims == ("time",)

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
    ),
    "grammar_basics.ipynb": notebook(
        markdown(
            """
# 04 · The core CubeDynamics grammar

The stable idea is a small composition protocol. Wrap a cube with `pipe`, place
configured verbs after `|`, and use `unwrap()` when ordinary Python resumes.
The same verb can also be called directly, and `v.apply` admits a compatible
project function without registration.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt
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

# Direct style and pipe style are equivalent. The outer zscore call stores the
# dimension setting; the resulting callable receives the current cube.
direct = v.zscore(dim="time")(cube)
through_pipe = (pipe(cube) | v.zscore(dim="time")).unwrap()

# A pipe can mix built-in verbs with v.apply, which adapts an ordinary function
# to the same cube → cube protocol. unwrap() returns to regular Python/xarray.
scaled_anomaly = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.apply(lambda value, factor: value * factor, factor=1.5)
).unwrap()

# This is a compact regression test embedded in the lesson.
xr.testing.assert_allclose(direct, through_pipe)

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
    ),
    "verbs_gallery.ipynb": notebook(
        markdown(
            """
# 05 · A visual gallery of core verbs

Use this notebook as a hackathon menu. It applies reducers, transforms, a
generic function, and a shape-changing verb to the same cube. Every panel is a
different question expressed with the same grammar.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt
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

# Reducers remove the time axis because keep_dim=False. These return 2D maps.
mean_map = (pipe(cube) | v.mean(dim="time", keep_dim=False)).unwrap()
variance_map = (pipe(cube) | v.variance(dim="time", keep_dim=False)).unwrap()

# Elementwise transforms preserve (time, y, x), so they remain cube-ready.
anomaly = (pipe(cube) | v.anomaly(dim="time")).unwrap()
zscore = (pipe(cube) | v.zscore(dim="time")).unwrap()

# v.apply introduces a small project function; flatten_space intentionally
# changes the data model from a cube to a time × pixel matrix for modeling.
clipped = (pipe(zscore) | v.apply(lambda value: value.clip(min=-1, max=1))).unwrap()
flat = (pipe(anomaly) | v.flatten_space(new_dim="pixel")).unwrap()

assert flat.dims == ("time", "pixel")

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
    ),
    "states_and_events.ipynb": notebook(
        markdown(
            """
# 06 · From continuous values to states, events, and synchrony

Some questions are about episodes rather than raw values. Here a heat cube
becomes a standard state Dataset, contiguous states become event objects, and
occurrence synchrony measures where heat episodes co-occur with a reference
pixel. These are specialized verbs built on the same pipe protocol.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt
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

# threshold_state converts continuous values into a standard Dataset containing
# boolean state, exceedance magnitude, and the threshold used for classification.
states = (
    pipe(cube)
    | v.threshold_state(threshold=34.0, direction="above", name="hot_day")
).unwrap()

# detect_events labels contiguous runs. min_duration=2 removes isolated hot
# days; max_gap=0 means a cool day always separates two events.
events = (pipe(states) | v.detect_events(min_duration=2, max_gap=0)).unwrap()

# Compare every pixel's hot-day occurrence with the center pixel. The result is
# a map where 1 means identical occurrence and 0 means no shared occurrence.
synchrony = (
    pipe(states)
    | v.occurrence_synchrony(spatial_mode="reference", reference="center")
).unwrap()

# EventResult deliberately separates a cube-like Dataset from a tabular event
# catalog. Accumulate catalog rows here to make an event-count map for teaching.
event_count = xr.zeros_like(cube.isel(time=0), dtype=int)
for row in events.catalog.itertuples():
    event_count.values[row.y_index, row.x_index] += 1
sync_map = synchrony["occurrence_synchrony"].isel(time_window_end=0)

# These checks document the expected output contracts before visualization.
assert states["state"].dtype == bool
assert len(events.catalog) > 0

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
    ),
    "custom_verb_project.ipynb": notebook(
        markdown(
            """
# 07 · Build a project-specific verb

Domain add-ons are usually projects that define their own verbs. This notebook
implements a small heat-stress vocabulary without modifying or registering
anything inside CubeDynamics, verifies direct and pipe use, and plots the
derived state and magnitude.
"""
        ),
        code(
            """
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# A project verb should behave identically when called directly or through a
# pipe. This assertion is the first regression test a new add-on should keep.
direct = heat_stress(threshold=35.0)(temperature)
through_pipe = (pipe(temperature) | heat_stress(threshold=35.0)).unwrap()
xr.testing.assert_identical(direct, through_pipe)

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
In a real add-on, move `heat_stress` into `my_project.verbs`, document the
threshold's scientific meaning, and keep the direct-versus-pipe regression test
with that project. The repository's `examples/custom_verb_project/` directory
provides a minimal package layout.
"""
        ),
    ),
    "lazy_composition.ipynb": notebook(
        markdown(
            """
# 08 · Lazy composition with Dask

Large cubes should not be loaded merely because a workflow was described. This
notebook constructs a chunked xarray cube, verifies that verbs build a lazy
graph, and computes only the small final map needed for the plot.
"""
        ),
        code(
            """
import dask.array as da
import matplotlib.pyplot as plt
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

# These verbs construct a task graph; neither one requests concrete values.
# The final result is a 2D variance map because the time dimension is reduced.
result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time", keep_dim=False)
).unwrap()

# chunks proves the arrays remain lazy. Counting graph tasks is safe because it
# inspects the plan rather than computing the array values.
assert cube.chunks is not None
assert result.chunks is not None
graph_tasks = len(result.data.__dask_graph__())

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
