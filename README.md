# CubeDynamics (`cubedynamics`)

CubeDynamics is a streaming-first climate cube math library with ggplot-style piping. It brings high-resolution climate archives (PRISM, gridMET, NDVI, and more) directly into your workflows so you can compose anomaly, synchrony, and correlation cubes without mirroring entire datasets.

## Features

- **Streaming PRISM/gridMET/Sentinel-2 helpers** (`cd.load_prism_cube`, `cd.load_gridmet_cube`, `cd.load_sentinel2_cube`, `cd.load_sentinel2_bands_cube`, `cd.load_sentinel2_ndvi_cube`, `cd.load_sentinel2_ndvi_zscore_cube`) for immediate analysis without bulk downloads. Legacy `load_s2_*` aliases still work but the `load_sentinel2_*` names are the canonical entry points.
- **Climate variance, correlation, trend, and synchrony cubes** that run on `xarray` objects and scale from laptops to clusters.
- **Pipe + verb system** – build readable cube workflows with `pipe(cube) | v.month_filter(...) | v.variance(...)` syntax inspired by ggplot/dplyr.
- **Verbs namespace (`cubedynamics.verbs`)** so transforms, stats, IO, and visualization live in focused modules.
- **Cloud-ready architecture** that embraces chunked processing, lazy execution, and storage backends like NetCDF or Zarr.

## Quickstart

Install CubeDynamics from PyPI (or GitHub while the release cadence is rapid) and use the pipe + verbs API everywhere:

```bash
pip install cubedynamics
# or pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Load a PRISM precipitation cube that streams from the archive
cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

# Compute June–August variance directly through the pipe
pipe(cube) \
    | v.month_filter([6, 7, 8]) \
    | v.variance(dim="time")
```

`cd.load_prism_cube` accepts exactly one area-of-interest (AOI) option: a
`lat`/`lon` point, a `[min_lon, min_lat, max_lon, max_lat]` bounding box via
`bbox`, or a GeoJSON Feature/FeatureCollection via `aoi_geojson`. The keyword
API shown above matches the documentation and is preferred, though the legacy
positional form (`load_prism_cube(["ppt"], "2000-01-01", "2000-12-31", aoi)`) is
still available for backward compatibility.

### Semantic variable loaders

Skip provider-specific variable names with the semantic helpers:

```python
# Daily mean temperature from the default provider (gridMET)
temp = cd.temperature(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
)

# Minimum / maximum temperature from explicit providers
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

# Temperature anomaly cube (mean-centered along time)
tanom = cd.temperature_anomaly(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    source="gridmet",
    kind="mean",
)

# Sentinel-2 NDVI z-score cube
ndvi_z = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
    source="sentinel2",
    as_zscore=True,
)
```

These helpers delegate to `cd.load_prism_cube`, `cd.load_gridmet_cube`, and
`cd.load_sentinel2_ndvi_zscore_cube` (or raw Sentinel-2 bands) so advanced users
can always drop back to the sensor-specific loaders when they need full control.

### Pipe ergonomics

- `pipe(value)` wraps any `xarray.DataArray` or `xarray.Dataset` without copying it.
- Apply verbs with `| v.verb_name(...)`. Each verb is a callable defined in `cubedynamics.verbs`.
- In notebooks, the last `Pipe` expression in a cell auto-displays the inner `xarray` object, so calling `.unwrap()` is optional unless you need the object immediately.

The same pattern works for gridMET via `cd.load_gridmet_cube(...)`, Sentinel-2 NDVI through `cd.load_sentinel2_ndvi_cube(...)` (raw) or `cd.load_sentinel2_ndvi_zscore_cube(...)` (standardized), and any custom `xarray` object you create.

### Example: stream a gridMET cube for Boulder, CO

The streaming helpers work the same way as the in-memory example above. Define an AOI, call the loader, and the resulting cube
can flow directly into the pipe system.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Stream a monthly gridMET precipitation cube for Boulder
cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    start="2000-01-01",
    end="2020-12-31",
    variable="pr",
    freq="MS",
    chunks={"time": 120},
)

# Feed directly into the pipe to compute JJA variance
pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```

### Sentinel-2 loaders

CubeDynamics works on remote-sensing image stacks in addition to climate
archives. The Sentinel helpers stream Sentinel-2 Level-2A chips via
[`cubo`](https://github.com/carbonplan/cubo) and plug directly into the verbs
API.

#### All Sentinel-2 bands

```python
import cubedynamics as cd

s2_all = cd.load_sentinel2_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2018-12-31",
)

s2_all
```

`load_sentinel2_cube` returns a `(time, y, x, band)` cube with all Sentinel-2
L2A bands that `cubo` provides by default (or a user-specified subset via the
``bands`` keyword). The helper keeps dimensions consistently ordered so it can
feed directly into downstream verbs.

#### Selected bands

```python
s2_rgbn = cd.load_sentinel2_bands_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2018-12-31",
    bands=["B02", "B03", "B04", "B08"],  # blue, green, red, NIR
)
```

`load_sentinel2_bands_cube` enforces that a band list is provided (raising a
``ValueError`` when empty) and otherwise mirrors the generic loader.

#### NDVI cubes

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.load_sentinel2_ndvi_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
)

pipe(ndvi) | v.show_cube_lexcube(title="Sentinel-2 NDVI (raw)")
```

`load_sentinel2_ndvi_cube` uses the band loader to grab the red (B04) and NIR
(B08) bands, runs `v.ndvi_from_s2(...)`, and returns **raw NDVI reflectance** in
the physical range `[-1, 1]` with dims `(time, y, x)`. Pass ``return_raw=True``
to also grab the reflectance stack before NDVI is computed:

```python
s2_bands, ndvi = cd.load_sentinel2_ndvi_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
    return_raw=True,
)
```

Need standardized anomalies out of the box? Use
`cd.load_sentinel2_ndvi_zscore_cube(...)`, which wraps the raw loader and applies
`v.zscore(dim="time", keep_dim=True)` so the cube stays `(time, y, x)` and is
Lexcube-ready:

```python
ndvi_z = cd.load_sentinel2_ndvi_zscore_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
)

pipe(ndvi_z) | v.show_cube_lexcube(title="Sentinel-2 NDVI z-score")
```

If you prefer to customize every step, the helper simply wraps the manual
pipeline below:

1. Stream Level-2A chips with `cubo` using bands B04 (red) and B08 (NIR).
2. Convert the reflectance cube to NDVI with `v.ndvi_from_s2(...)`.
3. Standardize NDVI over time with `v.zscore(dim="time")` to highlight
   greenness anomalies.
4. Optionally visualize the `(time × y × x)` cube with `v.show_cube_lexcube`
   and compute QA summaries that track the spatial median.

```python
from __future__ import annotations

import warnings

import cubo

from cubedynamics import pipe, verbs as v

LAT = 43.89
LON = -102.18
START = "2023-06-01"
END = "2024-09-30"

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    s2 = cubo.create(
        lat=LAT,
        lon=LON,
        collection="sentinel-2-l2a",
        bands=["B04", "B08"],
        start_date=START,
        end_date=END,
        edge_size=512,
        resolution=10,
        query={"eo:cloud_cover": {"lt": 40}},
    )

ndvi_z = (
    pipe(s2)
    | v.ndvi_from_s2(nir_band="B08", red_band="B04")
    | v.zscore(dim="time")
).unwrap()

(pipe(ndvi_z) | v.show_cube_lexcube(title="Sentinel-2 NDVI z-score", clim=(-3, 3)))
median_series = ndvi_z.median(dim=("y", "x"))
median_series.plot.line(x="time", ylabel="Median NDVI z-score")
```

NDVI anomaly cubes capture unusual greenness events (drought stress, rapid
recovery, disturbance). Because the pipe grammar keeps every cube on the same
grid, you can compare vegetation anomalies to PRISM precipitation or gridMET
temperature variance at the exact pixels of interest. Use `xr.corr` today for
per-pixel climate/NDVI correlations; the dedicated `v.correlation_cube` factory
is a placeholder that currently raises `NotImplementedError`. The full notebook
lives at [`notebooks/example_sentinel2_ndvi_zscore.ipynb`](notebooks/example_sentinel2_ndvi_zscore.ipynb).

### Interactive Lexcube visualization

CubeDynamics integrates with [Lexcube](https://github.com/carbonplan/lexcube) to provide interactive 3D exploration of `(time, y, x)` cubes. Call the helper directly or use the pipe verb:

```python
from cubedynamics import pipe, verbs as v
import cubedynamics as cd

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    start="2000-01-01",
    end="2020-12-31",
    variable="pr",
)

# JJA cube + Lexcube widget
pipe(cube) | v.month_filter([6, 7, 8]) | v.show_cube_lexcube(cmap="RdBu_r")

# Functional helper outside of a pipe
cd.show_cube_lexcube(cube, cmap="RdBu_r")
```

Lexcube widgets require a live Python environment (Jupyter, Colab, Binder) and a
3D `(time, y, x)` cube (Datasets with a single data variable work as well). They
do not execute on the static GitHub Pages site.

## API Overview

- `pipe` for wrapping any cube before piping.
- `verbs` (``from cubedynamics import verbs as v``) exposes transforms, statistics, IO, and visualization helpers.
- Streaming helpers: `cd.load_prism_cube`, `cd.load_gridmet_cube`, `cd.load_sentinel2_cube`, `cd.load_sentinel2_bands_cube`, `cd.load_sentinel2_ndvi_cube`, `cd.load_sentinel2_ndvi_zscore_cube`. Legacy `load_s2_*` aliases resolve to the same loaders.
- Semantic loaders: `cd.temperature`, `cd.temperature_min`, `cd.temperature_max`, `cd.temperature_anomaly`, and `cd.ndvi` for quick access to common climate and greenness variables.
- Vegetation helper: `v.ndvi_from_s2` for direct NDVI calculation on Sentinel-2 cubes.
- Stats verbs: `v.mean`, `v.variance`, `v.anomaly`, `v.month_filter`, and `v.zscore`. The `v.correlation_cube` factory is reserved for a future streaming implementation and currently raises `NotImplementedError`.
- IO verbs: `v.to_netcdf`, `v.to_zarr`, etc.
- Visualization verbs/helpers: `v.show_cube_lexcube` and `cd.show_cube_lexcube` for interactive exploration.

More verbs live under `cubedynamics.ops.transforms`, `cubedynamics.ops.stats`, and `cubedynamics.ops.io` and are re-exported via `cubedynamics.verbs`. Each verb returns a callable object that receives the upstream cube when used inside a pipe chain.

## Philosophy

- **Streaming-first design** – CubeDynamics emphasizes adapters that yield data as soon as it is available so analyses can begin immediately.
- **Pipe chaining** – The `Pipe` helper makes cube math declarative: each verb describes *what* to do, and the pipe handles *when* to run it.
- **xarray-compatible processing** – Every verb consumes/produces `xarray.DataArray` or `xarray.Dataset` objects, making it easy to interoperate with the broader ecosystem.

Visit https://cu-esiil.github.io/climate_cube_math/ for full documentation, concepts, and the latest changelog.
