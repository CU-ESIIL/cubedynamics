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
