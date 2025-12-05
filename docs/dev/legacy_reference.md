# Legacy reference

## Legacy Technical Reference (kept for context)

This is a new page; there is no prior content to preserve.


## Legacy Technical Reference (kept for context)
# Operations – transform verbs

**In plain English:**  
Transform verbs reshape or filter a cube before you calculate statistics.
They are small, chainable steps that keep the cube structure intact.

**You will learn:**  
- What each transform verb does in plain language
- How to combine transforms in a short pipe
- Where to find the original technical reference

## What this is

These functions live in `cubedynamics.ops.transforms` and are re-exported as `cubedynamics.verbs`.
Each one returns a callable so you configure it once and feed it a cube through the `|` operator.

## Why it matters

Transforming cubes in-place keeps your workflow compact and reproducible.
You can center, filter, or subset data without losing metadata, which makes it easy to hand analyses to collaborators.

## How to use it

### `anomaly(dim)`
Calculates how far each value is from the mean along the chosen dimension.

```python
from cubedynamics import pipe, verbs as v

daily_anom = pipe(cube) | v.anomaly(dim="time")
```
This mean-centers the cube along `time` so values show departures from the average.

### `month_filter(months)`
Keeps only the month numbers you list, such as `[6, 7, 8]` for June–August.

```python
summer = pipe(cube) | v.month_filter([6, 7, 8])
```
This is a quick way to create seasonal subsets before running statistics.

You can combine transforms freely:

```python
pipe(cube) | v.anomaly(dim="time") | v.month_filter([6, 7, 8])
```
This first mean-centers the cube and then keeps only summer timesteps.

---

## Original Reference (kept for context)
# Operations Reference – Transforms

Transform verbs reshape or filter cubes before you compute downstream statistics. All functions live under `cubedynamics.ops.transforms` and are re-exported via `cubedynamics.verbs`. Examples assume `from cubedynamics import pipe, verbs as v` and a `cube` variable that is an `xarray` object.

## `anomaly(dim)`

Computes anomalies by subtracting the mean along a dimension.

```python
result = pipe(cube) | v.anomaly(dim="time")
```

- **Parameters**
  - `dim`: dimension name (e.g., `"time"`).
- **Returns**: `xarray.DataArray`/`Dataset` with mean-centered values.

## `month_filter(months)`

Filters a cube to the specified month numbers (1–12). Useful for seasonal composites before running statistics.

```python
result = pipe(cube) | v.month_filter([6, 7, 8]) | v.anomaly(dim="time")
```

- **Parameters**
  - `months`: iterable of integers representing desired months.
- **Behavior**: keeps the original metadata while dropping other timesteps.

Use these verbs as building blocks ahead of stats like variance or correlation.


## Legacy Technical Reference (kept for context)
# Climate cubes

**In plain English:**  
A climate cube is a stack of maps through time, usually arranged as `(time, y, x)` with an optional `band` axis.
CubeDynamics loads these cubes for you so you can analyze them with clear, chained verbs.

**You will learn:**  
- How to create cubes from PRISM, gridMET, or Sentinel-2
- How to run quick statistics without reshaping data
- How to keep cubes ready for visualization or export

## What this is

Climate cubes are `xarray` objects with consistent dimensions and metadata.
CubeDynamics loaders take care of coordinate reference systems, chunking, and naming so every cube works with the same verbs.

## Why it matters

Having time and space aligned in one object makes downstream analysis much simpler.
You can filter, standardize, or correlate data without worrying about mismatched grids.
This structure also matches how educators explain maps stacked through time, which helps new learners.

## How to use it

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```
This streams monthly precipitation, keeps only summer months, and computes their variance.

You can create other cubes with the same pattern: `cd.load_prism_cube` for PRISM, `cd.load_sentinel2_cube` for Sentinel-2 bands, or `cd.load_sentinel2_ndvi_cube` for NDVI reflectance.
Each loader accepts one area-of-interest definition (`lat`/`lon`, `bbox`, or `aoi_geojson` when supported) so your code stays explicit.

## Exporting and visualizing

```python
pipe(cube) \
    | v.anomaly(dim="time") \
    | v.show_cube_lexcube(title="Summer anomaly", cmap="RdBu_r")
```
This shows the mean-centered cube in Lexcube and returns the cube so you can continue processing.
Use IO verbs like `v.to_netcdf("out.nc")` when you want to save results without breaking the chain.

---

## Original Reference (kept for context)
# Climate cubes

Climate cubes are the core abstraction in CubeDynamics. They are `xarray`
objects with shared `(time, y, x)` axes (and optional `band` or `variable`
dimensions) produced by the streaming loaders.

## Creating cubes

```python
import cubedynamics as cd

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)
print(cube.dims)
```

The loader harmonizes CRS, attaches metadata, and returns a lazily-evaluated
`xarray.Dataset`. Other loaders follow the same interface (`cd.load_prism_cube`,
`cd.load_sentinel2_cube`, `cd.load_sentinel2_ndvi_cube`,
`cd.load_sentinel2_ndvi_zscore_cube`), using the keyword-only AOI grammar:
pick a `lat`/`lon` point, a `[min_lon, min_lat, max_lon, max_lat]` bounding box,
or a GeoJSON Feature/FeatureCollection via `aoi_geojson` (for loaders that
support it).

## Derived diagnostics

Once a cube exists, run statistics directly on the labeled dimensions:

```python
from cubedynamics import pipe, verbs as v

ndvi_z = pipe(ndvi_cube) | v.zscore(dim="time")
var_cube = pipe(cube) | v.variance(dim="time")
```

Every helper keeps the input axes intact so that downstream visualizations and
exports can consume the resulting lexcube without regridding.

## Exporting cubes

`cubedynamics` exposes helpers like `cube.to_netcdf(...)`, `cube.to_zarr(...)`,
and visualization verbs such as `v.show_cube_lexcube` for interactive dashboards.
Large analyses rely on chunked writes through `dask` so the same scripts run in
cloud environments.


## Legacy Technical Reference (kept for context)
# Getting started with CubeDynamics

**In plain English:**  
This guide walks you through installing CubeDynamics, loading your first cube, and seeing how the pipe `|` syntax works.
Everything stays light and copy-friendly so you can paste examples into a notebook.

**You will learn:**  
- How to install from GitHub or PyPI
- How to build a first cube and send it through verbs
- Where to find deeper notebook tutorials

## What this is

CubeDynamics runs anywhere `xarray` runs: laptops, HPC clusters, or hosted notebooks.
You use the loader helpers to stream data, then chain verbs that describe each step in plain English.

## Why it matters

Climate archives are large, but most projects need only a slice or a simple statistic.
Streaming cubes let you explore without heavy downloads, and the pipe syntax keeps the steps transparent for students or collaborators.

## How to use it

Install the package, then try a short pipeline.

```bash
pip install cubedynamics
# or install straight from GitHub for the freshest commits
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

# Find how variable summer precipitation is
pipe(cube) \
    | v.anomaly(dim="time") \
    | v.month_filter([6, 7, 8]) \
    | v.variance(dim="time")
```
This chain loads, mean-centers, filters, and summarizes the cube without breaking the flow.

If you prefer gridMET or Sentinel-2, swap in `cd.load_gridmet_cube` or `cd.load_sentinel2_ndvi_cube` with the same pattern.

## A second quick example

```python
# Stream gridMET precipitation for Boulder and visualize it
boulder_pr = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)

pipe(boulder_pr) | v.month_filter([6, 7, 8]) | v.show_cube_lexcube(title="Summer precipitation")
```
This shows a seasonal slice inside Lexcube without saving anything to disk first.

## Keep exploring

- Open the quickstart notebook at `notebooks/quickstart_cubedynamics.ipynb` for a runnable tour.
- Peek at the semantic variable helpers in [docs/semantic_variables.md](semantic_variables.md) when you want temperature or NDVI without memorizing provider variable names.
- Browse the operation references for more verbs: [docs/ops_transforms.md](ops_transforms.md), [docs/ops_stats.md](ops_stats.md), and [docs/ops_io.md](ops_io.md).

---

## Original Reference (kept for context)
# Getting Started

CubeDynamics (`cubedynamics`) runs anywhere `xarray` does—laptops, clusters, or hosted notebooks. Use this guide to install the package, spin up the first pipe chain, and know where the notebook vignette lives.

## Installation

### Install from GitHub today

Grab the latest commits straight from the main branch. Installing inside a virtual environment (via `venv` or Conda) is recommended but optional.

```bash
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

### Install from PyPI once released

As soon as the first release is uploaded to PyPI you will be able to run:

```bash
pip install cubedynamics
```

Until then, use the GitHub install above for the working package.

## First pipeline in a notebook

1. Install CubeDynamics in your notebook environment (see the command above).
2. Load or create an `xarray` cube—anything with time/space coordinates works.
3. Chain a few verbs with the pipe syntax:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

pipe(cube) \
    | v.anomaly(dim="time") \
    | v.month_filter([6, 7, 8]) \
    | v.variance(dim="time")
```

The loader accepts exactly one AOI definition: a `lat`/`lon` point, a bounding
box via `bbox=[min_lon, min_lat, max_lon, max_lat]`, or a GeoJSON Feature (or
FeatureCollection) via `aoi_geojson`. The old positional signature is deprecated
but still works for existing notebooks.

This pipeline is dimension-agnostic—the verbs accept any axes you provide. `pipe(value)` wraps the `xarray` object and the `|` operator forwards it through each verb. In notebooks the final `Pipe` expression auto-displays the inner DataArray/Dataset so `.unwrap()` is optional.

## Beyond the minimal example

- Read the [Pipe Syntax & Verbs](pipe_syntax.md) page for more callables such as `month_filter`, `to_netcdf`, and how to author your own verbs.
- Explore future climate streaming examples (PRISM/gridMET/NDVI) as they land in the docs and notebooks.
- Run the full [CubeDynamics Quickstart notebook](https://github.com/CU-ESIIL/climate_cube_math/blob/main/notebooks/quickstart_cubedynamics.ipynb) for a ready-made walkthrough that matches this guide.
- Walk through the Sentinel-2 NDVI anomaly tutorial in [notebooks/example_sentinel2_ndvi_zscore.ipynb](https://github.com/CU-ESIIL/climate_cube_math/blob/main/notebooks/example_sentinel2_ndvi_zscore.ipynb) to see the vegetation workflow that complements the PRISM and gridMET examples.

## Worked examples

Use the recipes below as ready-made pipelines. They all rely on the same pipe + verbs grammar, so you can mix and match cubes (and correlate them) with minimal code changes.

- [PRISM precipitation anomaly / z-score cube](recipes/prism_variance_cube.md)
- [GRIDMET variance / z-score cube](recipes/gridmet_variance_cube.md)
- [Sentinel-2 NDVI anomaly (z-score) cube + Lexcube](recipes/s2_ndvi_zcube.md)

## Streaming a gridMET cube for Boulder, CO

Copy/paste the snippet below into a notebook cell to stream a monthly precipitation cube straight into `xarray`:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Define a rough AOI around Boulder, CO (lon/lat pairs in EPSG:4326)
cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```


## Legacy Technical Reference (kept for context)
# Lexcube integration

**In plain English:**  
Lexcube is an interactive viewer for `(time, y, x)` cubes.
CubeDynamics includes verbs and helpers so you can send a cube to Lexcube with one line and keep working.

**You will learn:**  
- How to display a cube in Lexcube from inside a pipe
- How to call the helper directly without the pipe
- Where the original technical notes live for reference

## What this is

The verb `v.show_cube_lexcube` and helper `cd.show_cube_lexcube` open a Lexcube widget for exploration.
They display the data as a side effect and return the original cube so your analysis can continue.

## Why it matters

Seeing the cube helps you spot patterns, cloud issues, or extreme events before running heavier statistics.
The one-line verb keeps visualization close to your computations, which is great for teaching and quick QA.

## How to use it

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

pipe(cube) \
    | v.month_filter([6, 7, 8]) \
    | v.show_cube_lexcube(title="PRISM JJA precipitation", cmap="RdBu_r")
```
This filters to summer months, opens the Lexcube widget, and leaves the cube intact for more processing.

You can also call the helper outside a pipe:

```python
cd.show_cube_lexcube(cube, cmap="RdBu_r")
```
This is handy when you already have an `xarray` object and just want a quick look.

Lexcube widgets render only in live notebook environments (JupyterLab, VS Code, Colab, Binder).
On the static docs site you will see screenshots or Binder links instead.

---

## Original Reference (kept for context)
# Lexcube integration

Lexcube provides interactive 3D exploration of `(time, y, x)` climate cubes. CubeDynamics exposes both a pipe verb (`v.show_cube_lexcube`) and a functional helper (`cd.show_cube_lexcube`) so you can embed the widget anywhere in your workflow. The verb displays the widget as a side effect and returns the original cube so the pipe chain can continue unchanged.

## Example workflow

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

# Focus on summer months and show the cube in Lexcube
pipe(cube) \
    | v.month_filter([6, 7, 8]) \
    | v.show_cube_lexcube(title="PRISM JJA precipitation", cmap="RdBu_r")
```

Pick whichever AOI input fits your workflow—`lat`/`lon` point, `bbox`, or a
GeoJSON feature via `aoi_geojson`. Only one AOI option may be set per call.

Behind the scenes the verb routes `(time, y, x)` data into Lexcube's widget API. As long as the cube is a 3D `xarray.DataArray` (or a Dataset with a single variable), the visualization launches instantly in a live notebook.

You can also call the helper directly when you are not inside a pipe:

```python
cd.show_cube_lexcube(cube, cmap="RdBu_r")
```

## Notebook-only behavior

Lexcube widgets run only in live Python environments (JupyterLab, VS Code, Colab, Binder). They will not render on the static documentation site, so screenshots and Binder links are provided for reference.

![Stylized Lexcube example](img/lexcube_example.svg)

*The SVG is a stylized capture so the documentation can ship a "screenshot" without introducing binary assets.*

[🔗 Launch this example on Binder](https://mybinder.org/v2/gh/CU-ESIIL/climate_cube_math/HEAD?labpath=notebooks/lexcube_example.ipynb)


## Legacy Technical Reference (kept for context)
# Operations – statistic verbs

**In plain English:**  
Statistic verbs summarize or standardize a cube along one dimension.
They build on transforms to answer questions like “how variable is summer rainfall?”

**You will learn:**  
- How to compute means, variances, and z-scores
- How to control dimensions you keep or drop
- Where the deeper technical notes live

## What this is

These functions live in `cubedynamics.ops.stats` and are also available under `cubedynamics.verbs`.
They expect an `xarray` cube and return an object with the same labeled coordinates unless you choose to drop dimensions.

## Why it matters

Summaries like variance or z-score highlight unusual events and trends.
Keeping the cube structure intact makes it easy to compare climate and vegetation or to hand off results to visualization tools.

## How to use it

### `mean(dim="time", keep_dim=True)`
Computes the average along a dimension.

```python
from cubedynamics import pipe, verbs as v

avg = pipe(cube) | v.mean(dim="time", keep_dim=True)
```
Setting `keep_dim=True` leaves the dimension in place with length 1, which helps when you want to broadcast results later.

### `variance(dim="time", keep_dim=True)`
Measures spread along a dimension.

```python
var = pipe(cube) | v.variance(dim="time", keep_dim=True)
```
Use this to see how much a season or band varies over time.

### `zscore(dim="time", std_eps=1e-4)`
Standardizes values by subtracting the mean and dividing by the standard deviation.

```python
z = pipe(cube) | v.zscore(dim="time")
```
This returns unitless scores that show how unusual each timestep is relative to its own history.

---

## Original Reference (kept for context)
# Operations Reference – Stats

Statistic verbs summarize cubes along dimensions or compare axes. They live in `cubedynamics.ops.stats` and are re-exported via `cubedynamics.verbs`. Examples assume `from cubedynamics import pipe, verbs as v` and a `cube` variable bound to an `xarray` object.

## `mean(dim="time", keep_dim=True)`

Compute the mean along a dimension.

```python
result = pipe(cube) | v.mean(dim="time", keep_dim=True)
```

- **Parameters**
  - `dim`: dimension to summarize.
  - `keep_dim`: retain the dimension as length 1 (default) or drop it entirely.

## `variance(dim="time", keep_dim=True)`

Compute the variance along a dimension.

```python
result = pipe(cube) | v.variance(dim="time", keep_dim=True)
```

- **Parameters**
  - `dim`: dimension to collapse.
  - `keep_dim`: retain the dimension as length 1 (default) or drop it entirely.
- **Returns**: variance cube matching the input layout when `keep_dim=True`.

## `zscore(dim="time", std_eps=1e-4)`

Standardize each pixel/voxel along a dimension by subtracting the mean and dividing by the standard deviation.

```python
result = pipe(cube) | v.zscore(dim="time")
```

- **Parameters**
  - `dim`: dimension to standardize along.
  - `std_eps`: mask threshold to avoid dividing by values with near-zero spread.
- **Returns**: anomaly cube whose values are unitless z-scores per pixel. The verb always preserves the original cube shape.

## `correlation_cube` (planned)

The exported factory currently raises `NotImplementedError` and is reserved for a future streaming implementation.

- **Intended behavior**: compute rolling or full-period correlations between named data variables or coordinates, returning an `xarray` cube with correlation coefficients.
- **Alternatives today**: use `xr.corr` for per-pixel correlations or the rolling helpers in `cubedynamics.stats.correlation`/`stats.tails`.

Combine these stats with transforms and IO verbs to produce complete analyses.


## Legacy Technical Reference (kept for context)
# Semantic variable loaders

**In plain English:**  
These helpers give you common climate variables like temperature or NDVI without remembering provider-specific codes.
You ask for "temperature" and CubeDynamics calls the right loader under the hood.

**You will learn:**  
- How to request temperature cubes with one function call
- How to grab anomalies and z-scores without custom code
- How to fall back to raw loaders when you need full control

## What this is

Semantic loaders are small wrappers around the PRISM, gridMET, and Sentinel-2 helpers.
They turn friendly names such as `temperature` or `ndvi` into the correct provider variables and return standard `(time, y, x)` cubes.

## Why it matters

Remembering that gridMET uses `pr` while PRISM uses `ppt` is error-prone.
Semantic helpers smooth that friction so new researchers can focus on questions instead of variable catalogs.
They also encourage consistent naming when you share notebooks with students or community partners.

## How to use it

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Daily mean temperature (gridMET by default)
temp = cd.temperature(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
)

# Minimum and maximum temperature with explicit sources
tmin = cd.temperature_min(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="gridmet",
)

tmax = cd.temperature_max(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="prism",
)

# An anomaly cube using the same API
tanom = cd.temperature_anomaly(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    source="gridmet",
    kind="mean",
)

pipe(tanom) | v.show_cube_lexcube(title="GridMET temperature anomaly")
```
These calls delegate to the provider-specific loaders, so you keep the convenience without losing accuracy.

A second example shows NDVI:

```python
ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
    source="sentinel2",
)

ndvi_z = pipe(ndvi) | v.zscore(dim="time")
```
`cd.ndvi` now returns raw NDVI; standardize explicitly with ``v.zscore``. The
``as_zscore`` flag is deprecated and will be removed in a future release.

---

## Original Reference (kept for context)
# Semantic variable loaders

CubeDynamics now provides a thin "semantic" layer on top of the sensor-specific
loaders so you can work with common variables like temperature and NDVI with a
single function call.

## Temperature cubes

Use `cd.temperature`, `cd.temperature_min`, and `cd.temperature_max` to request
mean, minimum, or maximum daily temperature from PRISM or gridMET without
memorizing provider-specific variable names:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

temp = cd.temperature(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    # default: gridMET
)

tmin = cd.temperature_min(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="gridmet",
)

tmax = cd.temperature_max(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="prism",
)
```

Behind the scenes, these helpers delegate to `cd.load_prism_cube` and
`cd.load_gridmet_cube` with the appropriate variable names.

## Temperature anomalies

`cd.temperature_anomaly` wraps the temperature loaders and the `v.anomaly` verb
to compute anomalies along the time axis:

```python
tanom = cd.temperature_anomaly(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    source="gridmet",
    kind="mean",
)

pipe(tanom) | v.show_cube_lexcube(title="GridMET temperature anomaly")
```

## NDVI cubes

For greenness dynamics, use `cd.ndvi`:

```python
ndvi_z = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
    source="sentinel2",
    as_zscore=True,
)
```

When `as_zscore=True`, this calls `cd.load_sentinel2_ndvi_zscore_cube` and
returns an NDVI z-score cube. When `as_zscore=False`, it computes raw NDVI from
Sentinel-2 bands using `v.ndvi_from_s2`.

As always, you can fall back to the sensor-specific loaders when you need full
control over band selection, cloud filtering, or temporal aggregation.


## Legacy Technical Reference (kept for context)

This is a new page; there is no prior content to preserve.


## Legacy Technical Reference (kept for context)
# Pipe syntax and verbs

**In plain English:**  
The pipe `|` symbol lets you chain cube operations in the order you think about them.
You wrap a cube with `pipe(cube)` and then pass it through verbs like `anomaly`, `variance`, or `show_cube_lexcube`.

**You will learn:**  
- How the `Pipe` object works
- How to combine verbs into readable workflows
- How to define your own verb when you need a custom step

## What this is

CubeDynamics exposes a lightweight `Pipe` object that holds any `xarray` DataArray or Dataset.
Verbs are small callables that accept the cube and return a new cube, making the code read like a recipe.

## Why it matters

Pipes keep notebooks tidy and self-documenting.
Each verb name describes its action, so collaborators can follow your workflow without digging through helper functions.

## How to use it

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.month_filter([6, 7, 8])
    | v.variance(dim="time")
)
```
This pipeline mean-centers the cube, keeps summer months, and computes their variance.
In notebooks the last `Pipe` expression auto-displays the inner `xarray` object, so `.unwrap()` is optional unless you need it immediately.

You can also visualize within the chain:

```python
pipe(cube) | v.anomaly(dim="time") | v.show_cube_lexcube(title="Anomalies")
```
The cube is passed to Lexcube for inspection and then returned for any further steps.

## Make your own verb

Verbs follow a simple factory pattern: accept configuration now, operate on the cube later.

```python
def my_custom_op(param):
    def _inner(da):
        # operate on da (xarray DataArray/Dataset)
        return da
    return _inner

pipe(cube) | my_custom_op(param=42)
```
Register your custom verb in your own module or import it in notebooks and use it alongside built-in verbs.

---

## Original Reference (kept for context)
# Pipe Syntax & Verbs

CubeDynamics exposes a lightweight `Pipe` object so `xarray` workflows read like a recipe. Every verb returns a callable that accepts the cube later, keeping the `|` chaining syntax clean.

## The Pipe object

```python
from cubedynamics import pipe

pipe_obj = pipe(cube)
```

`pipe(value)` wraps any `xarray.DataArray` or `xarray.Dataset` without altering it. Use the `|` operator to apply verbs. In notebooks the last `Pipe` expression in a cell auto-displays the wrapped object, so calling `.unwrap()` is optional unless you immediately need the `xarray` object.

## Chaining verbs

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time")
)
```

Each verb receives the previous output. Pipes simply pass the cube along, so as long as the object behaves like an `xarray` structure the chain continues.

## Core verbs

All examples below use in-memory data so you can run them in any notebook.

### `anomaly(dim="time")`

```python
import numpy as np
import xarray as xr
from cubedynamics import pipe, verbs as v

time = np.arange(4)
cube = xr.DataArray([1.0, 2.0, 3.0, 4.0], dims=["time"], coords={"time": time})

anoms = pipe(cube) | v.anomaly(dim="time")
```

`anomaly` subtracts the mean along the dimension you specify.

### `month_filter(months)`

```python
import numpy as np
import pandas as pd
import xarray as xr
from cubedynamics import pipe, verbs as v

time = pd.date_range("2000-01-01", periods=12, freq="MS")
values = np.arange(12)

cube = xr.DataArray(values, dims=["time"], coords={"time": time})

summer = pipe(cube) | v.month_filter([6, 7, 8])
```

`month_filter` keeps only the months you list (in numeric form) based on the `time` coordinate.

### `variance(dim="time")`

```python
from cubedynamics import pipe, verbs as v

var = pipe(cube) | v.variance(dim="time")
```

`variance` runs `xarray.var` under the hood, so any axis can be supplied.

### `to_netcdf(path)`

```python
from pathlib import Path
from cubedynamics import pipe, verbs as v

path = Path("example.nc")
pipe(cube) | v.to_netcdf(path)
```

`to_netcdf` writes the incoming cube to disk (returning the original object so the pipe can continue). When running docs examples you can point to a temporary directory such as `/tmp/example.nc`.

### `correlation_cube(other, dim="time")` (planned)

The exported factory currently raises `NotImplementedError` and is reserved for a future streaming implementation. Use `xr.corr` or the rolling helpers in `cubedynamics.stats.correlation`/`stats.tails` today:

```python
import xarray as xr
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ppt_anom = (pipe(prism_cube) | v.anomaly(dim="time")).unwrap()["ppt"]
ndvi_z = cd.load_sentinel2_ndvi_zscore_cube(...)

per_pixel_corr = xr.corr(ndvi_z, ppt_anom, dim="time")
```

### `show_cube_lexcube(**kwargs)`

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    start="2000-01-01",
    end="2020-12-31",
    variable="pr",
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.show_cube_lexcube(cmap="RdBu_r")
```

`show_cube_lexcube` integrates [Lexcube](https://github.com/carbonplan/lexcube) for interactive `(time, y, x)` exploration. The verb displays the widget as a side-effect and returns the original cube so the pipeline can keep flowing. The helper also exists as `cubedynamics.show_cube_lexcube(cube, **kwargs)` for non-pipe contexts.

## Example: chaining a streamed cube

Define a simple bounding box and stream gridMET data directly into the pipe:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    start="2000-01-01",
    end="2020-12-31",
    variable="pr",
    freq="MS",
    chunks={"time": 120},
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```

The streamed cube already carries a datetime `time` coordinate so verbs such as `month_filter` and `variance` work without any
extra preparation.

## How Pipe.unwrap works

`Pipe.unwrap()` simply returns the wrapped `xarray` object after the final verb. It does not copy data; it only exposes the last computed value. Because `Pipe` implements `_repr_html_`/`__repr__`, notebooks display the inner object automatically so `.unwrap()` is only necessary when you need the DataArray/Dataset immediately (e.g., assigning to a variable mid-cell).

## Define your own verbs

Verbs follow a small factory pattern: accept configuration parameters now, return a callable that receives the cube later.

```python
def my_custom_op(param):
    def _inner(da):
        # operate on da (xarray DataArray/Dataset)
        return da
    return _inner

from cubedynamics import pipe

result = pipe(cube) | my_custom_op(param=42)
```

Register your verb in your own module or import it in your notebook, then use it alongside the built-in operations.
