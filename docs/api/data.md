# Scientific nouns and source loaders
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

New analyses should load the scientific thing they need through
`cubedynamics.data`, then express analysis with verbs.

```python
from cubedynamics import data, pipe, verbs as v

cube = data.precipitation(
    source="prism",
    bbox=[-105.75, 39.50, -104.75, 40.50],
    start="2024-05-01",
    end="2024-05-31",
)
result = pipe(cube) | v.anomaly(dim="time")
```

Implemented nouns are `temperature`, `precipitation`, `vpd`, `wind`,
`humidity`, `radiation`, `surface_reflectance`, and `vegetation_index`.
Use `data.sources(noun)` and `data.describe(noun, source=...)` for discovery.
Scientific noun loaders never return synthetic fallback data.

Catalog descriptions also expose source mode, access backend, update cadence,
upstream identity strategy, current serving revision, reusable QA profile,
revision status, and live health. Noun results retain existing provenance and
add those lifecycle fields plus `schema_fingerprint`, `adapter_version`, and
request-specific `upstream_identity`. See the
[source lifecycle contract](../dev/source_lifecycle.md).

For integration QA, use `data.list_qa_profiles()`,
`data.get_qa_profile()`, and `data.evaluate_qa_profile()`. The lower-level
`data.normalize_xarray_schema()` and `data.schema_fingerprint()` helpers make
schema drift inspectable without materializing array values.

Serving-history helpers include `data.serving_history()`,
`data.current_revision_record()`, `data.validate_promotion()`, and
`data.rollback_target()`. Vector/API normalization and
`data.compare_normalized_schemas()` support future non-raster integrations.
`data.certify_live_sample()` writes the same profile evidence in live mode;
the scheduled command persists results under `artifacts/source_qa/live/`.

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

## Compatibility semantic helpers

The older top-level and `cubedynamics.variables` temperature/NDVI helpers remain
available for compatibility. Prefer `cubedynamics.data` in new documentation.

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
