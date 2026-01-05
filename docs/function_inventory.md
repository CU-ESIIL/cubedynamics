# Function Inventory (User-facing)
Generated: 2026-01-05T20:43:00Z

This page summarizes the user-facing CubeDynamics surface area in a verb-first layout. It links to the dedicated API pages for details and examples.

- [Pipe API](api/pipe.md)
- [Verbs API](api/verbs.md)
- [Data loaders & variables](api/data.md)
- [Visualization](api/viz.md)
- [Full inventory (developer)](api/inventory_full.md)

## Recommended API paths

> Most workflows:
> - Use `from cubedynamics import pipe, verbs as v`
> - Then `pipe(cube) | v.<verb>(...) | v.plot(...)` (or call verbs directly).
> - Use `cubedynamics.variables.*` for common “semantic variables” (e.g., temperature, NDVI).
> - Use `cubedynamics.data.*` when you need explicit control over the data source (PRISM/GRIDMET/Sentinel-2).
> - Use `cubedynamics.streaming.*` when you need tiled/virtual streaming behavior.
> - Prefer `cubedynamics.verbs.*` over `cubedynamics.ops.*` (legacy shims).
>   - If a function lives under `cubedynamics.ops.*`, treat it as legacy unless docs explicitly say otherwise.

## Core verbs (verb-first)

Grouped by theme; all verbs are pipe-friendly (`pipe(cube) | v.<verb>(...)`). See [Verbs API](api/verbs.md) for signatures and examples.

### Reduce

- **cubedynamics.verbs.mean** — Compute the mean along a dimension with optional `keep_dim` semantics and VirtualCube streaming support.
- **cubedynamics.verbs.variance** — Variance counterpart to `mean`, preserving attributes and streaming paths.
- **cubedynamics.verbs.rolling_tail_dep_vs_center** — Rolling tail-dependence vs. center pixel contrast for fire/vase analyses.

### Transform

- **cubedynamics.verbs.anomaly** — Subtract the mean over a dimension to produce anomalies.
- **cubedynamics.verbs.zscore** — Standardize values via mean/std; preserves metadata.
- **cubedynamics.verbs.month_filter** — Keep or drop specific calendar months.
- **cubedynamics.verbs.apply** — Wrap an arbitrary callable for custom pipe stages.
- **cubedynamics.verbs.fit_model** — Placeholder modeling verb (experimental surface).

### Shape

- **cubedynamics.verbs.flatten_space** — Reshape `(time, y, x)` cubes to `(time, space)` while tracking coordinates.
- **cubedynamics.verbs.flatten_cube** — Flatten cubes to a long table suitable for modeling.

### Event / fire / vase

- **cubedynamics.verbs.extract** — Attach fire time-hull geometry, vase metadata, and climate summaries to a cube.
- **cubedynamics.verbs.vase** — Plot a vase/time-hull around an event.
- **cubedynamics.verbs.vase_extract** — Mask cubes using vase polygons, returning both cube and vase.
- **cubedynamics.verbs.vase_mask** — Boolean vase mask aligned to the cube grid.
- **cubedynamics.verbs.vase_demo** — Build a synthetic vase/time-hull for demos.
- **cubedynamics.verbs.tubes** — Identify suitability “tubes” and compute per-component metrics.
- **cubedynamics.verbs.fire_plot** — Fire time-hull + climate visualization wrapper.
- **cubedynamics.verbs.fire_panel** — Compact panel combining hull outlines and climate histograms.
- **cubedynamics.verbs.climate_hist** — Inside/outside climate histograms for a fire event.
- **cubedynamics.verbs.landsat8_mpc / landsat_vis_ndvi / landsat_ndvi_plot** — Landsat MPC helpers for visualization-ready NDVI.

### Plotting verbs

- **cubedynamics.verbs.plot** — Interactive cube viewer; attaches the viewer while returning the cube for continued piping.
- **cubedynamics.verbs.plot_mean** — Show mean/variance cubes side by side.
- **cubedynamics.verbs.show_cube_lexcube** — Render a Lexcube widget as a side effect and return the original cube.

## Data entrypoints

User-facing constructors for cubes and semantic variables. Prefer these over low-level helpers.

### Semantic variables (``cubedynamics.variables``)

- **temperature / temperature_max / temperature_min** — GRIDMET/PRISM temperature series with optional streaming tiling.
- **temperature_anomaly** — Temperature anomalies built on `verbs.anomaly`.
- **ndvi / ndvi_chunked** — Sentinel-2 NDVI cubes (eager or time-chunked streaming).
- **estimate_cube_size** — Quick size estimate for planned cube pulls.

### Dataset loaders (``cubedynamics.data``)

- **gridmet.load_gridmet_cube** — Streaming-first GRIDMET loader with AOI/time controls.
- **prism.load_prism_cube** — PRISM analogue with identical AOI/time semantics.
- **sentinel2.load_s2_cube** — Sentinel-2 L2A streaming via `cubo`/`stackstac`.
- **sentinel2.load_s2_ndvi_cube** — Sentinel-2 NDVI convenience wrapper.
- **sentinel2.load_s2_ndvi_zscore_cube** — NDVI z-scores combining the NDVI loader with `verbs.zscore`.

### Streaming entrypoints (``cubedynamics.streaming``)

- **streaming.gridmet.stream_gridmet_to_cube** — GridMET tiling/streaming into cube form.
- **streaming.virtual.VirtualCube** — Virtual cube abstraction (materialize-on-demand) used by verbs for tiled pipelines.
- **streaming.virtual.make_time_tiler / make_spatial_tiler** — Helpers for chunking large AOIs or time ranges.

## Visualization entrypoints

Plotting primitives and viewer helpers used by the verbs and directly callable.

- **cubedynamics.plotting.cube_plot.CubePlot** — Grammar-of-graphics plotting core with `to_html`/`save` and rich repr support.
- **cubedynamics.plotting.cube_plot.theme_cube_studio** — Default CubePlot theme factory.
- **cubedynamics.plotting.viewer.show_cube_viewer** — Write HTML and return an IFrame for notebooks.
- **cubedynamics.plotting.viewer._write_cube_html** — Low-level helper that materializes viewer HTML to disk.
- **cubedynamics.viewers.cube_viewer.write_cube_viewer** — Generate a standalone HTML/JS cube viewer for 3D cubes.
- **cubedynamics.verbs.show_cube_lexcube / cubedynamics.viz.lexcube_viz.show_cube_lexcube** — Render Lexcube widgets for `(time, y, x)` cubes.

## Legacy and shims (prefer verbs when possible)

- **cubedynamics.ops.transforms.anomaly / month_filter** — Legacy shims; use `cubedynamics.verbs` equivalents.
- **cubedynamics.ops.viz.plot** — Legacy plotting wrapper; prefer `cubedynamics.verbs.plot`.
- **cubedynamics.ops.ndvi.ndvi_from_s2** — NDVI helper kept for backward compatibility.
- **cubedynamics.ops.io.to_netcdf** — Pipe-friendly NetCDF writer available for side-effect saving.

## Where to go next

- Use the dedicated API guides for signatures, examples, and edge cases.
- For the exhaustive symbol list (including private helpers and tests), see [Inventory (Full / Dev)](api/inventory_full.md).
- Deprecated shims and replacements are summarized in [Reference](api/reference.md).
