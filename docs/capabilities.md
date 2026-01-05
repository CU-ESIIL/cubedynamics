# Capabilities & Verbs

*What data you can analyze, what you can do to it, and how those pieces fit together.*

Climate Cube Math is organized around a grammar: **data sources → cubes & geometries → verbs → visualizations**. Data inputs become cubes or geometry contexts, verbs transform or summarize those cubes, and visualization verbs make the space–time structure legible. This page is a **complete, structured inventory** of the package’s capabilities.

## Data Sources You Can Pipe

`pipe(...)` accepts multiple types of inputs that define the *starting object* of analysis.

### Cube-backed datasets (space × time)

| Input | Description | Example use |
|-------|-------------|-------------|
| `xarray.DataArray` | In-memory spatiotemporal cube with named dims (typically `time`, `y`, `x`). | Custom cube from your own preprocessing. |
| `xarray.Dataset` | Multi-variable cube; verbs normalize to a single variable where needed (e.g., `show_cube_lexcube`). | Multi-band cube with a single primary variable. |
| `VirtualCube` | Streaming/lazy cube that yields tiles without full download. | Continental-scale climate analyses where eager IO is impractical. |
| `load_gridmet_cube` / `stream_gridmet_to_cube` | Predefined gridMET climate cubes (eager or streaming). | Daily temperature/humidity over a bounding box. |
| `load_prism_cube` / `stream_prism_to_cube` | PRISM climate cubes (eager or streaming). | Long-term precipitation or temperature stacks. |
| `load_s2_cube` / `load_s2_ndvi_cube` / `load_s2_ndvi_zscore_cube` | Sentinel-2 surface reflectance and NDVI cubes (eager). | Vegetation condition monitoring. |
| `load_sentinel2_cube` / `load_sentinel2_ndvi_cube` / `load_sentinel2_ndvi_zscore_cube` | Sentinel helpers re-exported for convenience. | Rapid Sentinel-2 ingestion with NDVI diagnostics. |
| `gridmet()` API wrapper | Convenience API loader that returns a cube for a given point/period. | Quick point-centered climate pulls. |

### Event and Geometry Inputs

These inputs define **regions or events in space–time** used for masking, extraction, or hull construction.

| Input | Description | Example use |
|-------|-------------|-------------|
| `geopandas.GeoDataFrame` / shapely geometries | Spatial AOIs for masking or alignment. | Clip cube to a watershed polygon. |
| `FireEventDaily` (from `fired_event(...)`) | FIRED daily perimeter event with centroid/time metadata. | Drive time-hull extraction and vase visualizations. |

## Core Verbs (from basic to advanced)

Verbs are intentionally layered: **inspection → aggregation → statistics → events → visualization**. The list below enumerates the complete verb surface, ordered by conceptual dependency.

### 2.1 Structural / inspection verbs

- `apply`: wrapper for custom elementwise operations.
- `month_filter`: keep or drop months to align seasonal windows.
- `flatten_space`, `flatten_cube`: reshape cubes for downstream analysis or ML.
- `fit_model`: fit statistical/ML models on flattened cubes.
- `to_netcdf`: persist cubes while preserving attrs.
- `ndvi_from_s2`, `landsat8_mpc`, `landsat_vis_ndvi`: loaders/helpers that prepare cube structure for later verbs.

### 2.2 Aggregation verbs

- `mean` (supports `VirtualCube` time or space reduction with `keep_dim`), `variance` (same streaming support).
- `plot_mean`: quick spatial summary plot built on aggregation.

### 2.3 Distributional & tail verbs

- `rolling_tail_dep_vs_center`: rolling tail dependence helper.
- `zscore`: standardize over a dimension.
- `anomaly`: departures from climatology or baseline.

### 2.4 Variability & synchrony verbs

- `correlation_cube`: correlation coefficients between locations or series.
- `tubes`: suitability tube extraction for synchronized signals.

### 2.5 Trend & temporal structure verbs

- `rolling`-style behaviors exposed via `rolling_tail_dep_vs_center` and `rolling` arguments on stats verbs.
- `month_filter` (seasonal framing) and `anomaly` (temporal reference frames).

### 2.6 Event- and hull-based verbs

- `extract`: attach fire time-hulls, climate summaries, and vase metadata.
- `vase`, `vase_demo`, `vase_extract`, `vase_mask`: build or visualize vase-shaped space–time hulls.
- `climate_hist`: inside vs outside climate histograms tied to hull metadata.
- `fire_plot`, `fire_derivative`, `fire_panel`: higher-level fire event visualizations and diagnostics.

## Visualization Verbs

Visualization is treated as a **terminal verb**: it renders and returns the original object so pipes can continue.

- `plot`: interactive cube viewer for slices and summaries.
- `show_cube_lexcube`: Lexcube widget showing 3D cube structure (expects `(time, y, x)`).
- `vase`: 3D vase/time-hull visualization (attrs- or argument-driven).
- `plot_mean`, `climate_hist`, `landsat_ndvi_plot`, `fire_plot`/`fire_panel`: specialized plots for aggregates, distributions, NDVI, and fire panels.

## Putting It Together: The Grammar

Data source → structural verbs → statistical verbs → event verbs → visualization.

Example pipelines:

- `gridmet(...) → mean(time) → plot` (temporal average then spatial view).
- `stream_prism_to_cube(...) → variance(time, keep_dim=True) → show_cube_lexcube` (variability mapped in 3D).
- `load_gridmet_cube(...) → extract(fired_event=...) → vase` (event-aligned hull visualization).

## Where to go next

- [Concepts](concepts/index.md)
- [Getting Started](quickstart.md)
- [Recipes / How-tos](recipes/index.md)
- [API Reference](api/index.md)
