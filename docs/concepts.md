# Concepts Overview

CubeDynamics is organized into three conceptual layers that compose to produce
climate lexcubes:

1. **Sources** – streaming adapters for Sentinel-2, PRISM, gridMET, and other
   gridded datasets. Each returns `xarray.Dataset` objects with shared
   `(time, y, x)` axes.
2. **Cube math primitives** – functions inside `cubedynamics.stats`,
   `cubedynamics.indices`, and `cubedynamics.lexcubes` that compute anomalies,
   correlations, and derived indicators.
3. **Pipelines & exports** – recipes that connect cubes to dashboards or models
   (NetCDF/Zarr writers, QA plots, and asynchronous workflows).

The sections below summarize how these layers interact.

## Source adapters

Every loader enforces consistent naming (time, y, x, band) and metadata (CRS,
units, history). Streaming-first behavior is preferred: data arrive chunked via
HTTP range requests, STAC assets, or cloud object storage signed URLs. Offline
fallbacks download only the required slices.

## Lexcube builders

Lexcubes are multi-dimensional cubes that store derived metrics such as
variance, synchrony, or NDVI anomalies along the same axes as the source data.
They can be nested (e.g., a `dataset` containing multiple diagnostics) and are
ready for export.

## Analysis & visualization

Downstream helpers provide rolling correlation, tail dependence, QA plots, and
hooks for interactive dashboards. See [Climate cubes](climate_cubes.md) and
[Correlation cubes](correlation_cubes.md) for example notebooks and API usage.
