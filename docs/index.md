# CubeDynamics home

**In plain English:**  
CubeDynamics helps you load climate and NDVI grids as tidy "cubes" and process them with readable pipe steps. The new VirtualCube system streams huge requests so you can handle decades of data without running out of memory. You get simple examples up front and deeper debugging notes if you ever need them.

**What this page helps you do:**  
- Understand the CubeDynamics mindset
- See how streaming with VirtualCube works in practice
- Find examples, verbs, and debugging tips for large cubes

## CubeDynamics in one minute

CubeDynamics wraps `xarray` DataArrays/Datasets with a light `pipe(cube)` helper. You then chain verbs such as `v.anomaly` or `v.mean` using the `|` operator. The cube keeps its shape `(time, y, x [, band])`, and you keep readable notebooks.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="1970-01-01",
    end="2020-12-31",
    show_progress=True,  # optional progress bar when tqdm is installed
)

# Even though this is a 50-year request, it streams under the hood
trend = pipe(ndvi) | v.mean(dim=("y", "x"))
```

### What can I see?

```python
from cubedynamics import pipe, verbs as v

pipe(ndvi) | v.plot(title="NDVI cube (streaming)")
```

The default viewer keeps axes tight around the cube, shows a bottom colorbar, and overlays vase outlines automatically when `attrs["vase"]` is present. *(Screenshot placeholder: cube with tight axes + green vase overlay.)*

Turn the bar off when you prefer a quiet log:

```python
ndvi_quiet = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="1970-01-01",
    end="2020-12-31",
    show_progress=False,
)
```

You do not have to toggle anything for large requests—VirtualCube starts streaming tiles automatically. See the
[Interactive cube viewer](cube_viewer.md) page for controls, HTML export, and interactivity troubleshooting.

## Why VirtualCube exists

Large AOIs or long time ranges used to require careful chunking. VirtualCube now slices requests into time and spatial tiles automatically. Each tile is processed and combined, so memory stays small while you keep the same pipe + verbs syntax.

Behind the scenes:
- When a cube is very large, CubeDynamics switches to a streaming VirtualCube.
- The request is split into small tiles across time and/or space.
- Each tile flows through the verbs, incremental statistics are tracked, and the final result looks like any other cube.

## Working With Large Datasets (New in 2025)

CubeDynamics can now work with extremely large climate or NDVI datasets — 
even decades of data or very large spatial areas — without loading everything 
into memory at once.

It does this using a new system called **VirtualCube**, which streams data in 
small 'tiles'. You can think of these tiles as puzzle pieces. CubeDynamics 
processes each piece, keeps track of running statistics, and never holds the 
whole puzzle in memory.

## A quick streaming walkthrough

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Request a continental-scale NDVI cube
ndvi_big = cd.ndvi(
    bbox=[-125.0, 24.0, -66.5, 49.5],
    start="1985-01-01",
    end="2024-12-31",
)

# Compute a streaming variance over space
variance_ts = pipe(ndvi_big) | v.variance(dim=("y", "x"))

# Visualize the time series without materializing the entire cube
pipe(variance_ts) | v.plot_timeseries()
```

The code mirrors small-cube examples. VirtualCube handles tiling so the variance runs in memory-safe chunks.

## Data Streams

The CubeDynamics grammar can stream multiple data sources into time–space cubes:

- PRISM climate grids
- gridMET climate grids
- Sentinel-2 imagery (where available)
- **Landsat-8 Collection 2 Level-2 from Microsoft Planetary Computer** via `landsat8_mpc`

```python
from cubedynamics import pipe, verbs as v

cube = (
    pipe(None)
    | v.landsat8_mpc(
        bbox=[-105.35, 39.9, -105.15, 40.1],
        start="2019-07-01",
        end="2019-08-01",
    )
).unwrap()
```

## How to force or inspect streaming

Most users never need to touch these options, but they are here when you want to debug:

```python
# Force streaming mode
ndvi_stream = cd.ndvi(lat=40.0, lon=-105.25, start="1970", end="2020", streaming_strategy="virtual")
print(ndvi_stream)  # shows tile metadata
ndvi_stream.debug_tiles()  # print tile boundaries

# Force materialization (loads everything; use with caution)
ndvi_materialized = ndvi_stream.materialize()
```

Use smaller `time_tile` or `spatial_tile` arguments when you see memory pressure or slow progress.

## Debugging a VirtualCube request

- Call `debug_tiles()` to see time and spatial tile boundaries.
- Pass `streaming_strategy="virtual"` to loaders to confirm streaming is active.
- Use `.materialize()` only when you genuinely need the full cube in memory.
- When plotting large cubes, CubeDynamics streams tiles to the plotting verb; if you hit rate limits, reduce the date span.
- Check provider limits and your network speed when performance feels slow.

## Learn more

- [Interactive cube viewer](cube_viewer.md) collects controls, saving/debug tips, and developer invariants for `v.plot()`.
- [Virtual Cubes](virtual_cubes.md) explains the tiling model and shows more code.
- [Streaming Large Data](streaming_large_data.md) covers when streaming activates and how to debug.
- [Semantic Variable Loaders](semantic_variables.md) gives quick access to NDVI and temperature variables without memorizing provider names.

---

## Legacy Technical Reference (kept for context)
# CubeDynamics home

**In plain English:**  
This site shows how to load climate data as easy-to-think-about cubes and process them with simple pipe verbs.
You will see plain-language guides, code snippets, and the original technical notes for deeper reference.

**You will learn:**  
- What a cube is and why CubeDynamics uses the idea
- How the pipe `|` operator keeps analyses readable
- Where to find transform, statistics, and visualization verbs

## What this is

CubeDynamics is a notebook-friendly way to handle gridded climate data.
You start with an `xarray` object shaped like `(time, y, x [, band])`, wrap it in `pipe(cube)`, and pass it through verbs such as `v.anomaly` or `v.show_cube_lexcube`.
Every example on this site follows that rhythm so you can adapt them quickly.

## Why it matters

Climate archives can be overwhelming when you just need a clean seasonal summary or greenness anomaly.
By streaming data from PRISM, gridMET, or Sentinel-2 straight into a cube, you avoid bulky downloads and keep your work reproducible.
The short, chained verbs make it easier to teach workflows to students or community partners.

## How to use it

Start with a small cube and practice chaining verbs.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Daily precipitation near Boulder, CO
daily_ppt = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

# Quick seasonal variance
pipe(daily_ppt) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```
This finds how variable summer precipitation is over the 20-year span.

You can also visualize cubes directly:

```python
pipe(daily_ppt) | v.anomaly(dim="time") | v.show_cube_lexcube(title="Summer anomalies")
```
This pipes the mean-centered cube into Lexcube for interactive exploration.

---

## Original Reference (kept for context)
# CubeDynamics

## A tidyverse-style grammar for Earth system data cubes

CubeDynamics treats every spatiotemporal grid as a **cube** and lets you compose operations with a simple `pipe(cube) | verbs` syntax. Build anomaly pipelines, correlate climate and vegetation, and publish Lexcube-ready visualizations without breaking out of Python.

[Get started](getting_started/install.md){ .md-button .md-button--primary }
[Browse examples](examples/prism_jja_variance.md){ .md-button }
[Verbs reference](reference/verbs_transforms.md){ .md-button }
[Semantic loaders](semantic_variables.md){ .md-button }

![Lexcube NDVI z-score cube](assets/img/lexcube_hero.png){ .cube-image }

## Why CubeDynamics?

- **Streaming climate cubes** assembled from PRISM, gridMET, NDVI, and other archives without local mirroring.
- **Pipe-based math** so you can write `pipe(cube) | v.anomaly() | v.variance()` and get reproducible workflows.
- **Focused verbs under `cubedynamics.verbs`** covering transforms, stats, and IO helpers for on-disk storage.

## What is CubeDynamics?

CubeDynamics wraps `xarray.DataArray` and `xarray.Dataset` objects whose dimensions follow the cube pattern `(time, y, x [, band])`. Load data with helpers such as `load_prism_cube`, `load_gridmet_cube`, or `load_sentinel2_ndvi_cube` (raw NDVI) and then apply verbs like `v.zscore(dim="time")` when you want standardized anomalies. The package leans on lazy loading (Dask) so you can process multi-decade archives from PRISM, gridMET, and Sentinel-2 NDVI chips without downloading everything locally.

If you just want temperature or NDVI without remembering provider variable names, start with the [semantic variable loaders](semantic_variables.md).

CubeDynamics is inspired by tidy data grammars: call `pipe(cube)` once, then stack verbs for transforms, statistics, IO, and visualization. Verbs are tiny factories, which means the same function works for every cube. New loaders, verbs, and models can be added without changing the mental model.

## The core grammar (pipe + verbs)

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.month_filter([6, 7, 8])
    | v.variance(dim="time")
)
```

Verbs return callables, so you configure them once (`v.anomaly(dim="time")`) and then pass the cube through with the `|` operator. The Lexcube integration follows the same pattern:

```python
pipe(ndvi_z) | v.show_cube_lexcube()
```

The result is a notebook- and script-friendly grammar where cubes, pipes, and verbs stay tightly aligned.

## Update (2025): Notebook quickstart

The original quickstart is still the fastest way to experience CubeDynamics in a notebook. Open a new session, install the package, and stream a cube straight into the pipe system.

### Installation commands

```bash
pip install cubedynamics
# or pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

### First PRISM pipeline

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
    | v.variance(dim="time")
```

`load_prism_cube` accepts keyword-only AOI definitions—pick exactly one of a `lat`/`lon` point, a `[min_lon, min_lat, max_lon, max_lat]` bounding box via `bbox`, or a GeoJSON Feature/FeatureCollection via `aoi_geojson`. The positional signature from previous releases still works but is deprecated.

`pipe(value)` wraps the `xarray` object so you can forward it through verbs with the `|` operator. In notebooks the last `Pipe` expression in a cell automatically displays the wrapped DataArray/Dataset, so `.unwrap()` is optional. See [notebooks/quickstart_cubedynamics.ipynb](https://github.com/CU-ESIIL/climate_cube_math/blob/main/notebooks/quickstart_cubedynamics.ipynb) for the runnable tutorial notebook.

### Learn more pathways

- Start with the [Installation & setup guide](getting_started/install.md) for environment tips and troubleshooting.
- Walk through [What is a cube?](concepts/cubes.md) and [Pipe syntax & verbs](concepts/pipe_and_verbs.md) to lock in the mental model.
- Visualize cubes interactively with the [Lexcube verb](reference/verbs_viz.md#vshow_cube_lexcube) or head to the [Examples & Recipes](examples/prism_jja_variance.md) section for end-to-end notebooks.

<div class="cube-card">

### Where to go next

- **New to cubes?** Start with [What is a cube?](concepts/cubes.md) and [Pipe syntax & verbs](concepts/pipe_and_verbs.md).
- **Want a working example?** Try [PRISM JJA variance](examples/prism_jja_variance.md) or [Sentinel-2 NDVI z-score](examples/s2_ndvi_zscore.md).
- **Looking for specific operations?** See the [Verbs reference](reference/verbs_transforms.md).

</div>
