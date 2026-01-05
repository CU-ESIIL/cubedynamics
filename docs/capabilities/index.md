# Capabilities Overview

This section answers: **What can Climate Cube Math do once your data is in a cube?** It surveys supported inputs, verbs, and visualization endpoints so you can plan pipelines before diving into API details.

Use it to:
- Understand which inputs `pipe(...)` accepts and how they map into cubes or geometry contexts.
- Skim the full verb surface, from structural helpers to event- and visualization-oriented operations.
- See example pipelines that demonstrate the "overview → verbs → visualization" flow.

## Data sources you can pipe

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

### Event and geometry inputs

These inputs define **regions or events in space–time** used for masking, extraction, or hull construction.

| Input | Description | Example use |
|-------|-------------|-------------|
| `geopandas.GeoDataFrame` / shapely geometries | Spatial AOIs for masking or alignment. | Clip or align a cube to a watershed polygon. |
| `FireEventDaily` (from `fired_event(...)`) | FIRED daily perimeter event with centroid/time metadata. | Drive time-hull extraction and vase visualizations. |

## Core verbs (from basic to advanced)

Verbs are layered: **inspection → aggregation → statistics → events → visualization**. The list below enumerates the verb surface, ordered by conceptual dependency.

### Structural / inspection verbs

- `apply`: wrapper for custom elementwise operations.
- `month_filter`: keep or drop months to align seasonal windows.
- `flatten_space`, `flatten_cube`: reshape cubes for downstream analysis or ML.
- `fit_model`: placeholder hook for model fitting on flattened cubes.
- `to_netcdf`: persist cubes while preserving attrs.
- `ndvi_from_s2`: derive NDVI from Sentinel-2 bands.
- `landsat8_mpc`, `landsat_vis_ndvi`: prepare Landsat 8 MPC and visualization-friendly NDVI cubes.

### Aggregation verbs

- `mean` (supports `VirtualCube` reductions with `keep_dim`).
- `variance` (same streaming support).
- `plot_mean`: quick spatial summary plot built on aggregation.

### Distributional & tail verbs

- `rolling_tail_dep_vs_center`: rolling tail dependence helper.
- `zscore`: standardize over a dimension.
- `anomaly`: departures from climatology or baseline.

### Variability & synchrony verbs

- `correlation_cube`: correlation coefficients between locations or series.
- `tubes`: suitability tube extraction for synchronized signals (optionally converts to vase definitions).

### Trend & temporal structure verbs

- `rolling_tail_dep_vs_center` (rolling structure across time windows).
- `month_filter` (seasonal framing) and `anomaly` (temporal reference frames).

### Event- and hull-based verbs

- `extract`: attach fire time-hulls, climate summaries, and vase metadata.
- `vase`, `vase_demo`, `vase_extract`, `vase_mask`: build or visualize vase-shaped space–time hulls.
- `climate_hist`: inside vs outside climate histograms tied to hull metadata.
- `fire_plot`, `fire_panel`, `fire_derivative`: higher-level fire event visualizations and diagnostics.

## Visualization verbs

Visualization is treated as a **terminal verb**: it renders and returns the original object so pipes can continue.

- `plot`: interactive cube viewer for slices and summaries.
- `show_cube_lexcube`: Lexcube widget showing 3D cube structure (expects `(time, y, x)`).
- `vase`: 3D vase/time-hull visualization (attrs- or argument-driven).
- `plot_mean`, `landsat_ndvi_plot`, `fire_plot` / `fire_panel`, `climate_hist`: specialized plots for aggregates, NDVI, and fire panels.

## Putting it together: the grammar

Data source → structural verbs → statistical verbs → event verbs → visualization.

Example pipelines:

- `gridmet(...) → mean(time) → plot` (temporal average then spatial view).
- `stream_gridmet_to_cube(...) → variance(time, keep_dim=True) → show_cube_lexcube` (variability mapped in 3D with streaming input).
- `load_gridmet_cube(...) → extract(fired_event=...) → vase` (event-aligned hull visualization).

## Read next
- If you are new: [Getting Started](../quickstart.md)
- If you want operations: [Verbs & Examples](textbook_verbs.md)
- If you want data: [Datasets Overview](../datasets/index.md)
- If you want workflows: [Recipes Overview](../recipes/index.md)
- If you want visualization: [Visualization Overview](../viz/index.md)
