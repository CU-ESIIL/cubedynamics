# Data loaders and variables
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

User-facing entry points for constructing cubes from remote or synthetic
backends. These functions live under ``cubedynamics.data`` and
``cubedynamics.variables``.

## Core dataset loaders

### ``cubedynamics.data.gridmet.load_gridmet_cube(...)``
Streaming-first GRIDMET helper supporting keyword AOI arguments (``lat``/``lon``,
``bbox``, or ``aoi_geojson``). Accepts ``variable``/``variables``, time range,
``prefer_streaming``, and ``show_progress`` flags.

Example:

```python
from cubedynamics.data.gridmet import load_gridmet_cube

da = load_gridmet_cube(variable="tmmx", lat=40.0, lon=-105.2, start="2020-06-01", end="2020-06-10")
```

### ``cubedynamics.data.prism.load_prism_cube(...)``
PRISM analogue to GRIDMET with the same AOI and time arguments. The loader
constructs a PRISM-like cube and preserves coordinate metadata.

### ``cubedynamics.data.sentinel2.load_s2_cube(...)``
Stream Sentinel-2 L2A data via ``stackstac``/``cubo`` with standard AOI
arguments, band selection, and chunking controls.

### ``cubedynamics.data.sentinel2.load_s2_ndvi_cube(...)``
Convenience wrapper that loads Sentinel-2 and computes NDVI as a ready-to-plot
cube.

### ``cubedynamics.data.sentinel2.load_s2_ndvi_zscore_cube(...)``
Build an NDVI z-score cube by combining the NDVI loader with :func:`verbs.zscore`.

## Semantic variable helpers

These wrappers choose the appropriate loader and variable name, with optional
streaming and tiling behavior baked in.

### ``cubedynamics.variables.temperature(...)``
Mean temperature cube from GRIDMET or PRISM. Accepts AOI/time arguments plus
``source``, ``streaming_strategy`` (``"auto"``/``"materialize"``), ``time_chunk``
for streaming, and ``spatial_tile``.

### ``cubedynamics.variables.temperature_max(...)`` / ``temperature_min(...)``
Maximum or minimum daily temperature cube; parameters mirror
:func:`temperature`.

### ``cubedynamics.variables.temperature_anomaly(...)``
Compute anomalies on the chosen temperature series using :func:`verbs.anomaly`.

### ``cubedynamics.variables.ndvi(...)`` / ``ndvi_chunked(...)``
Sentinel-2 NDVI convenience loaders. ``ndvi_chunked`` streams in time chunks and
concatenates along ``time``; both preserve attrs indicating variable/source.

## Minimal examples

```python
import cubedynamics as cd

# GRIDMET
max_t = cd.variables.temperature_max(lat=35.0, lon=-118.5, start="2020-08-01", end="2020-08-15")

# PRISM mean temperature with streaming over monthly tiles
prism_mean = cd.variables.temperature(lat=45.0, lon=-123.1, start="2020-01-01", end="2020-03-31", source="prism", streaming_strategy="auto")

# Sentinel-2 NDVI cube
ndvi = cd.variables.ndvi(lat=37.7, lon=-122.5, start="2020-06-01", end="2020-06-15")
```
