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

CubeDynamics wraps `xarray.DataArray` and `xarray.Dataset` objects whose dimensions follow the cube pattern `(time, y, x [, band])`. Load data with helpers such as `load_prism_cube`, `load_gridmet_cube`, `load_sentinel2_ndvi_cube` (raw NDVI), or `load_sentinel2_ndvi_zscore_cube` (standardized NDVI), then keep the cube intact as you build analyses. The package leans on lazy loading (Dask) so you can process multi-decade archives from PRISM, gridMET, and Sentinel-2 NDVI chips without downloading everything locally.

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
