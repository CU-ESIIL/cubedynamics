# Capabilities & Verbs

*What data you can analyze, what you can do to it, and how those pieces fit together.*

Climate Cube Math is organized around a grammar: **data sources → cubes & geometries → verbs → visualizations**. Data inputs become cubes or geometry contexts, verbs transform or summarize those cubes, and visualization verbs make the space–time structure legible. This page is a **complete, structured inventory** of the package’s capabilities.

## Data Sources You Can Pipe

`pipe(...)` accepts multiple types of inputs that define the *starting object* of analysis.

### Cube-backed datasets (space × time)

| Input | Description | Example use |
|-------|-------------|-------------|
| `xarray.DataArray` | In-memory spatiotemporal cube with named dims (typically `time`, `y`, `x`). | Custom cube from your own preprocessing. |
| `xarray.Dataset` | Multi-variable cube; verbs normalize to a single variable where needed. | Multi-band cube with a primary data variable. |
| `VirtualCube` | Streaming/lazy cube that yields tiles without full download. | Large AOIs or long time ranges streamed chunk by chunk. |
| `load_gridmet_cube` / `stream_gridmet_to_cube` | GRIDMET climate cubes (eager or streaming). | Daily temperature, humidity, or VPD over a bounding box or AOI. |
| `load_prism_cube` / `stream_prism_to_cube` | PRISM climate cubes (eager; streaming stub is exposed but not yet implemented). | Long-term precipitation or temperature stacks. |
| `load_s2_cube` / `load_s2_ndvi_cube` | Sentinel-2 surface reflectance and NDVI cubes. | Vegetation condition monitoring. |
| `load_sentinel2_cube` / `load_sentinel2_bands_cube` / `load_sentinel2_ndvi_cube` / `load_sentinel2_ndvi_zscore_cube` | Sentinel-2 helpers re-exported for convenience. | Rapid Sentinel-2 ingestion with derived NDVI variants. |
| `gridmet(...)` API wrapper | Convenience API loader returning a GRIDMET `DataArray` around a point. | Quick point-centered climate pulls. |

### Event and Geometry Inputs

These inputs define **regions or events in space–time** used for masking, extraction, or hull construction.

| Input | Description | Example use |
|-------|-------------|-------------|
| `geopandas.GeoDataFrame` / shapely geometries | Spatial AOIs for masking or alignment. | Clip or align a cube to a watershed polygon. |
| `FireEventDaily` (from `fired_event(...)`) | FIRED daily perimeter event with centroid/time metadata. | Drive time-hull extraction and vase visualizations. |

## Core Verbs (from basic to advanced)

Verbs are intentionally layered: **inspection → aggregation → statistics → events → visualization**. The list below enumerates the complete verb surface, ordered by conceptual dependency.

### 2.1 Structural / inspection verbs

- `apply`: wrapper for custom elementwise operations.
- `month_filter`: keep or drop months to align seasonal windows.
- `flatten_space`, `flatten_cube`: reshape cubes for downstream analysis or ML.
- `fit_model`: placeholder hook for model fitting on flattened cubes.
- `to_netcdf`: persist cubes while preserving attrs.
- `ndvi_from_s2`: derive NDVI from Sentinel-2 bands.
- `landsat8_mpc`, `landsat_vis_ndvi`: prepare Landsat 8 MPC and visualization-friendly NDVI cubes.

### 2.2 Aggregation verbs

- `mean` (supports `VirtualCube` reductions with `keep_dim`).
- `variance` (same streaming support).
- `plot_mean`: quick spatial summary plot built on aggregation.

### 2.3 Distributional & tail verbs

- `rolling_tail_dep_vs_center`: rolling tail dependence helper.
- `zscore`: standardize over a dimension.
- `anomaly`: departures from climatology or baseline.

### 2.4 Variability & synchrony verbs

- `correlation_cube`: correlation coefficients between locations or series.
- `tubes`: suitability tube extraction for synchronized signals (optionally converts to vase definitions).

### 2.5 Trend & temporal structure verbs

- `rolling_tail_dep_vs_center` (rolling structure across time windows).
- `month_filter` (seasonal framing) and `anomaly` (temporal reference frames).

### 2.6 Event- and hull-based verbs

- `extract`: attach fire time-hulls, climate summaries, and vase metadata.
- `vase`, `vase_demo`, `vase_extract`, `vase_mask`: build or visualize vase-shaped space–time hulls.
- `climate_hist`: inside vs outside climate histograms tied to hull metadata.
- `fire_plot`, `fire_panel`, `fire_derivative`: higher-level fire event visualizations and diagnostics.

## Visualization Verbs

Visualization is treated as a **terminal verb**: it renders and returns the original object so pipes can continue.

- `plot`: interactive cube viewer for slices and summaries.
- `show_cube_lexcube`: Lexcube widget showing 3D cube structure (expects `(time, y, x)`).
- `vase`: 3D vase/time-hull visualization (attrs- or argument-driven).
- `plot_mean`, `landsat_ndvi_plot`, `fire_plot` / `fire_panel`, `climate_hist`: specialized plots for aggregates, NDVI, and fire panels.

## Putting It Together: The Grammar

Data source → structural verbs → statistical verbs → event verbs → visualization.

Example pipelines:

- `gridmet(...) → mean(time) → plot` (temporal average then spatial view).
- `stream_gridmet_to_cube(...) → variance(time, keep_dim=True) → show_cube_lexcube` (variability mapped in 3D with streaming input).
- `load_gridmet_cube(...) → extract(fired_event=...) → vase` (event-aligned hull visualization).

## Where to go next

- [Concepts](concepts/index.md)
- [Getting Started](quickstart.md)
- [How-tos](howto/index.md)
- [API Reference](api/index.md)
