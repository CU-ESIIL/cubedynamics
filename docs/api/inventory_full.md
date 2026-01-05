# Function and Class Inventory (Full / Dev)
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

Generated: 2026-01-05T20:43:00Z

## Public surface area

### Section 1: Public API

**cubedynamics** — cubedynamics: streaming-first climate cube math.
- **cubedynamics.plot** (`function`, line 113, `src/cubedynamics/__init__.py`) — Convenience helper for plotting a 3D cube without using the pipe.

**cubedynamics.correlation_cubes** — Correlation and trend helpers for streamed cubes.
- **cubedynamics.correlation_cubes.correlation_cube** (`function`, line 10, `src/cubedynamics/correlation_cubes.py`) — Compute correlations between a reference cube and streamed targets.

**cubedynamics.data.gridmet** — GRIDMET data access helpers.
- **cubedynamics.data.gridmet.load_gridmet_cube** (`function`, line 27, `src/cubedynamics/data/gridmet.py`) — Load a GRIDMET-like climate cube.

**cubedynamics.data.prism** — PRISM data access helpers with a streaming-first contract.
- **cubedynamics.data.prism.load_prism_cube** (`function`, line 20, `src/cubedynamics/data/prism.py`) — Load a PRISM-like cube.

**cubedynamics.data.sentinel2** — Sentinel-2 data access helpers.
- **cubedynamics.data.sentinel2.load_s2_cube** (`function`, line 25, `src/cubedynamics/data/sentinel2.py`) — Stream Sentinel-2 L2A data via cubo and return a dask-backed xarray object.
- **cubedynamics.data.sentinel2.load_s2_ndvi_cube** (`function`, line 67, `src/cubedynamics/data/sentinel2.py`) — Stream Sentinel-2 and return an NDVI cube ready for downstream ops.

**cubedynamics.demo** — Synthetic event helpers used throughout the documentation.
- **cubedynamics.demo.make_demo_event** (`function`, line 23, `src/cubedynamics/demo.py`) — Create a synthetic FIRED-like GeoDataFrame for demos.

**cubedynamics.hulls** — Plotting helper that builds ruled surfaces from daily polygons.
- **cubedynamics.hulls.plot_ruled_time_hull** (`function`, line 51, `src/cubedynamics/hulls.py`) — Build a 3D ruled surface describing event growth through time.

**cubedynamics.indices.vegetation** — Vegetation index helpers.
- **cubedynamics.indices.vegetation.compute_ndvi_from_s2** (`function`, line 20, `src/cubedynamics/indices/vegetation.py`) — Compute NDVI from a Sentinel-2 Dataset or DataArray.

**cubedynamics.ops.io** — I/O helpers for pipe chains.
- **cubedynamics.ops.io.to_netcdf** (`function`, line 8, `src/cubedynamics/ops/io.py`) — Factory for a pipeable ``.to_netcdf`` side-effect operation.

**cubedynamics.ops.ndvi** — NDVI-related pipeable operations.
- **cubedynamics.ops.ndvi.ndvi_from_s2** (`function`, line 8, `src/cubedynamics/ops/ndvi.py`) — Factory returning a Sentinel-2 NDVI transform for pipe chains.

**cubedynamics.ops.stats** — Statistical pipeable operations.
- **cubedynamics.ops.stats.correlation_cube** (`function`, line 8, `src/cubedynamics/ops/stats.py`) — Factory placeholder for a future correlation cube operation.

**cubedynamics.ops.transforms** — Transform-style pipeable operations.
- **cubedynamics.ops.transforms.anomaly** (`function`, line 12, `src/cubedynamics/ops/transforms.py`) — Deprecated shim forwarding to :func:`cubedynamics.verbs.stats.anomaly`.
- **cubedynamics.ops.transforms.month_filter** (`function`, line 18, `src/cubedynamics/ops/transforms.py`) — Factory for filtering calendar months from a ``time`` coordinate.

**cubedynamics.ops.viz** — Visualization verbs wrapping simple interactive widgets.
- **cubedynamics.ops.viz.plot** (`function`, line 12, `src/cubedynamics/ops/viz.py`) — Legacy wrapper for the interactive plotting verb.

**cubedynamics.ops_fire.fired_api** —
- **cubedynamics.ops_fire.fired_api.fired_event** (`function`, line 14, `src/cubedynamics/ops_fire/fired_api.py`) — Public entry point for loading a FIRED fire event.

**cubedynamics.ops_io.gridmet_api** —
- **cubedynamics.ops_io.gridmet_api.gridmet** (`function`, line 8, `src/cubedynamics/ops_io/gridmet_api.py`) — Load a GRIDMET variable as an xarray.DataArray suitable for CubePlot.

**cubedynamics.piping** — Pipe wrapper enabling ``|`` composition for cube operations.
- **cubedynamics.piping.Pipe** (`class`, line 41, `src/cubedynamics/piping.py`) — Wrap a value so it can flow through ``|`` pipe stages.
- **cubedynamics.piping.Verb** (`class`, line 27, `src/cubedynamics/piping.py`) — Wrapper for callables used in pipe chains.
- **cubedynamics.piping.pipe** (`function`, line 87, `src/cubedynamics/piping.py`) — Wrap ``value`` in a :class:`Pipe`, enabling ``Pipe | op(...)`` syntax.

**cubedynamics.plotting.cube_plot** — Grammar-of-graphics + streaming core for cube plotting.
- **cubedynamics.plotting.cube_plot.CoordCube** (`class`, line 249, `src/cubedynamics/plotting/cube_plot.py`) — Camera/coordinate configuration for cube plots.
- **cubedynamics.plotting.cube_plot.CubeAes** (`class`, line 85, `src/cubedynamics/plotting/cube_plot.py`) — Aesthetic mapping for cube plots.
- **cubedynamics.plotting.cube_plot.CubeAnnotation** (`class`, line 262, `src/cubedynamics/plotting/cube_plot.py`) — Simple annotation container for planes/text anchored to cube axes.
- **cubedynamics.plotting.cube_plot.CubeFacet** (`class`, line 101, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubeLayer** (`class`, line 117, `src/cubedynamics/plotting/cube_plot.py`) — A plotting layer pairing a geom with data and stat.
- **cubedynamics.plotting.cube_plot.CubePlot** (`class`, line 428, `src/cubedynamics/plotting/cube_plot.py`) — Internal object model for cube visualizations.
- **cubedynamics.plotting.cube_plot.CubeTheme** (`class`, line 48, `src/cubedynamics/plotting/cube_plot.py`) — Theme configuration for cube plots.
- **cubedynamics.plotting.cube_plot.ScaleAlphaContinuous** (`class`, line 242, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.ScaleFillContinuous** (`class`, line 149, `src/cubedynamics/plotting/cube_plot.py`) — Continuous color scale used by the cube viewer.
- **cubedynamics.plotting.cube_plot.geom_cube** (`function`, line 132, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_outline** (`function`, line 140, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_path3d** (`function`, line 144, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_slice** (`function`, line 136, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.theme_cube_studio** (`function`, line 78, `src/cubedynamics/plotting/cube_plot.py`) — Return the default "studio" theme.

**cubedynamics.plotting.cube_viewer** —
- **cubedynamics.plotting.cube_viewer._axis_range_from_ticks** (`function`, line 1198, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._guess_axis_name** (`function`, line 1166, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._infer_axis_ticks** (`function`, line 1175, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer.cube_from_dataarray** (`function`, line 777, `src/cubedynamics/plotting/cube_viewer.py`) —

**cubedynamics.plotting.progress** — Notebook-friendly progress helpers for cube rendering.
- **cubedynamics.plotting.progress._CubeProgress** (`class`, line 8, `src/cubedynamics/plotting/progress.py`) — Simple progress helper that prints inline status updates.

**cubedynamics.plotting.viewer** — Utilities for rendering the cube viewer safely inside notebooks.
- **cubedynamics.plotting.viewer._write_cube_html** (`function`, line 12, `src/cubedynamics/plotting/viewer.py`) — Write a standalone cube viewer HTML file to the working directory.
- **cubedynamics.plotting.viewer.show_cube_viewer** (`function`, line 22, `src/cubedynamics/plotting/viewer.py`) — Return an IFrame pointing at a self-contained cube viewer file.

**cubedynamics.prism_streaming** — Streaming-first helpers for PRISM datasets.
- **cubedynamics.prism_streaming.stream_prism_to_cube** (`function`, line 15, `src/cubedynamics/prism_streaming.py`) — Stream PRISM data into an xarray object.

**cubedynamics.sentinel** — Sentinel-2 helper utilities for CubeDynamics.
- **cubedynamics.sentinel.load_sentinel2_bands_cube** (`function`, line 87, `src/cubedynamics/sentinel.py`) — Stream a Sentinel-2 L2A cube for a user-selected list of bands.
- **cubedynamics.sentinel.load_sentinel2_cube** (`function`, line 18, `src/cubedynamics/sentinel.py`) — Stream a Sentinel-2 L2A cube via ``cubo``.
- **cubedynamics.sentinel.load_sentinel2_ndvi_cube** (`function`, line 126, `src/cubedynamics/sentinel.py`) — Stream Sentinel-2 L2A data and compute a raw NDVI cube.
- **cubedynamics.sentinel.load_sentinel2_ndvi_zscore_cube** (`function`, line 172, `src/cubedynamics/sentinel.py`) — Convenience wrapper that returns a z-scored Sentinel-2 NDVI cube.

**cubedynamics.stats.anomalies** — Anomaly and z-score utilities.
- **cubedynamics.stats.anomalies.rolling_mean** (`function`, line 68, `src/cubedynamics/stats/anomalies.py`) — Compute a simple rolling mean along a time-like dimension.
- **cubedynamics.stats.anomalies.temporal_anomaly** (`function`, line 33, `src/cubedynamics/stats/anomalies.py`) — Compute anomalies relative to a baseline mean over a time-like dimension.
- **cubedynamics.stats.anomalies.temporal_difference** (`function`, line 52, `src/cubedynamics/stats/anomalies.py`) — Compute lagged differences along a time-like dimension.
- **cubedynamics.stats.anomalies.zscore_over_time** (`function`, line 15, `src/cubedynamics/stats/anomalies.py`) — Deprecated helper that forwards to :func:`cubedynamics.ops.stats.zscore`.

**cubedynamics.stats.correlation** — Correlation helpers.
- **cubedynamics.stats.correlation.rolling_corr_vs_center** (`function`, line 28, `src/cubedynamics/stats/correlation.py`) — Build a rolling-window correlation cube vs the center pixel.

**cubedynamics.stats.spatial** — Spatial cube math primitives.
- **cubedynamics.stats.spatial.mask_by_threshold** (`function`, line 45, `src/cubedynamics/stats/spatial.py`) — Create a boolean mask for values that satisfy a threshold condition.
- **cubedynamics.stats.spatial.spatial_coarsen_mean** (`function`, line 12, `src/cubedynamics/stats/spatial.py`) — Coarsen a DataArray by averaging blocks in the spatial dimensions.
- **cubedynamics.stats.spatial.spatial_smooth_mean** (`function`, line 28, `src/cubedynamics/stats/spatial.py`) — Apply a boxcar spatial mean filter over the y/x dimensions.

**cubedynamics.stats.tails** — Tail dependence utilities.
- **cubedynamics.stats.tails.rolling_tail_dep_vs_center** (`function`, line 64, `src/cubedynamics/stats/tails.py`) — Build rolling-window tail-dependence cubes vs the center pixel.

**cubedynamics.streaming.gridmet** —
- **cubedynamics.streaming.gridmet.stream_gridmet_to_cube** (`function`, line 168, `src/cubedynamics/streaming/gridmet.py`) — Stream a gridMET subset as an xarray.DataArray "cube" for a given AOI.

**cubedynamics.streaming.virtual** — Virtual cube streaming helpers.
- **cubedynamics.streaming.virtual.VirtualCube** (`class`, line 20, `src/cubedynamics/streaming/virtual.py`) — Representation of a lazily tiled cube.
- **cubedynamics.streaming.virtual.make_spatial_tiler** (`function`, line 123, `src/cubedynamics/streaming/virtual.py`) — Create a deterministic spatial tiler for a bounding box.
- **cubedynamics.streaming.virtual.make_time_tiler** (`function`, line 94, `src/cubedynamics/streaming/virtual.py`) — Create a deterministic time tiler.

**cubedynamics.tubes** — Backend utilities for tube detection and analysis.
- **cubedynamics.tubes.compute_suitability_from_ndvi** (`function`, line 22, `src/cubedynamics/tubes.py`) — Return a boolean mask marking suitability based on NDVI thresholds.
- **cubedynamics.tubes.compute_tube_metrics** (`function`, line 102, `src/cubedynamics/tubes.py`) — Compute per-tube metrics:
- **cubedynamics.tubes.label_tubes** (`function`, line 57, `src/cubedynamics/tubes.py`) — Label 3D connected components (tubes) in a boolean mask.
- **cubedynamics.tubes.tube_to_vase_definition** (`function`, line 216, `src/cubedynamics/tubes.py`) — Convert a single tube (tube_id) into a VaseDefinition.

**cubedynamics.utils.chunking** — Chunking and subsampling utilities.
- **cubedynamics.utils.chunking.coarsen_and_stride** (`function`, line 10, `src/cubedynamics/utils/chunking.py`) — Optionally coarsen spatially and subsample in time.

## Internal helpers (continued)

**cubedynamics.utils.cube_css** — Helpers for emitting lightweight CSS cube HTML scaffolding.
- **cubedynamics.utils.cube_css.write_css_cube_static** (`function`, line 60, `src/cubedynamics/utils/cube_css.py`) — Write a standalone HTML page with a simple CSS-based cube skeleton.

**cubedynamics.utils.dims** — Utilities for inferring canonical cube dimensions.
- **cubedynamics.utils.dims._infer_time_y_x_dims** (`function`, line 16, `src/cubedynamics/utils/dims.py`) — Infer time, y, and x dimension names from a cube-like object.

**cubedynamics.utils.drop_bad_assets** — Utilities for handling intermittent remote asset failures.
- **cubedynamics.utils.drop_bad_assets.drop_bad_assets** (`function`, line 25, `src/cubedynamics/utils/drop_bad_assets.py`) — Return a copy of ``cube`` with slices that raise errors removed.

**cubedynamics.variables** — Semantic variable loaders for common climate and vegetation variables.
- **cubedynamics.variables.ndvi** (`function`, line 426, `src/cubedynamics/variables.py`) — Load a Sentinel-2 NDVI cube.
- **cubedynamics.variables.ndvi_chunked** (`function`, line 355, `src/cubedynamics/variables.py`) — Load a Sentinel-2 NDVI cube in time chunks and concatenate along 'time'.
- **cubedynamics.variables.temperature** (`function`, line 138, `src/cubedynamics/variables.py`) — Load a mean temperature cube from the chosen climate provider.
- **cubedynamics.variables.temperature_anomaly** (`function`, line 260, `src/cubedynamics/variables.py`) — Compute a temperature anomaly cube along the time dimension.
- **cubedynamics.variables.temperature_max** (`function`, line 234, `src/cubedynamics/variables.py`) — Load a maximum daily temperature cube from the selected source.
- **cubedynamics.variables.temperature_min** (`function`, line 208, `src/cubedynamics/variables.py`) — Load a minimum daily temperature cube from the selected source.

**cubedynamics.vase** — Time-varying vase polygons and masking utilities.
- **cubedynamics.vase.VaseDefinition** (`class`, line 42, `src/cubedynamics/vase.py`) — Collection of vase sections with interpolation rules.
- **cubedynamics.vase.VasePanel** (`class`, line 74, `src/cubedynamics/vase.py`) — Rectangular patch approximating a vase hull segment.
- **cubedynamics.vase.VaseSection** (`class`, line 29, `src/cubedynamics/vase.py`) — Single cross-section of a vase at a given time.
- **cubedynamics.vase.build_vase_mask** (`function`, line 230, `src/cubedynamics/vase.py`) — Build a boolean mask for voxels inside a time-varying vase.
- **cubedynamics.vase.build_vase_panels** (`function`, line 163, `src/cubedynamics/vase.py`) — Approximate the vase hull with rectangular panels.
- **cubedynamics.vase.extract_vase_from_attrs** (`function`, line 282, `src/cubedynamics/vase.py`) — Return the VaseDefinition attached to this DataArray, if any.

**cubedynamics.verbs** — Namespace exposing pipe-friendly cube verbs.
- **cubedynamics.verbs.climate_hist** (`function`, line 315, `src/cubedynamics/verbs/__init__.py`) — Plot histogram of climate inside vs outside fire perimeters.
- **cubedynamics.verbs.extract** (`function`, line 133, `src/cubedynamics/verbs/__init__.py`) — Verb: attach fire time-hull + climate summary (and a vase-like hull)
- **cubedynamics.verbs.fire_panel** (`function`, line 493, `src/cubedynamics/verbs/__init__.py`) — Convenience helper: fire time-hull + climate distribution "panel".
- **cubedynamics.verbs.fire_plot** (`function`, line 393, `src/cubedynamics/verbs/__init__.py`) — High-level convenience verb: fire time-hull × climate visualization.
- **cubedynamics.verbs.landsat8_mpc** (`function`, line 68, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for the Landsat MPC helper.
- **cubedynamics.verbs.landsat_ndvi_plot** (`function`, line 88, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for Landsat NDVI plotting.
- **cubedynamics.verbs.landsat_vis_ndvi** (`function`, line 80, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for a visualization-friendly Landsat NDVI cube.
- **cubedynamics.verbs.show_cube_lexcube** (`function`, line 96, `src/cubedynamics/verbs/__init__.py`) — Render a Lexcube widget as a side-effect and return the original cube.
- **cubedynamics.verbs.vase** (`function`, line 274, `src/cubedynamics/verbs/__init__.py`) — High-level vase plotting verb with TimeHull support.

**cubedynamics.verbs.custom** — Generic custom-function verbs.
- **cubedynamics.verbs.custom.apply** (`function`, line 10, `src/cubedynamics/verbs/custom.py`) — Return a verb that applies ``func`` to the incoming cube.

**cubedynamics.verbs.flatten** — Shape-changing verbs for flattening cubes.
- **cubedynamics.verbs.flatten.flatten_cube** (`function`, line 31, `src/cubedynamics/verbs/flatten.py`) — Flatten all non-time dimensions into a single ``sample`` dimension.
- **cubedynamics.verbs.flatten.flatten_space** (`function`, line 8, `src/cubedynamics/verbs/flatten.py`) — Flatten spatial dimensions (``y`` and ``x``) into a ``pixel`` dimension.

**cubedynamics.verbs.landsat_mpc** — Landsat-8 streaming via Microsoft Planetary Computer (MPC).
- **cubedynamics.verbs.landsat_mpc.landsat8_mpc** (`function`, line 155, `src/cubedynamics/verbs/landsat_mpc.py`) — Landsat 8 (MPC) streaming verb for cubedynamics.
- **cubedynamics.verbs.landsat_mpc.landsat8_mpc_stream** (`function`, line 62, `src/cubedynamics/verbs/landsat_mpc.py`) — Stream Landsat-8 Collection 2 Level-2 scenes from Microsoft Planetary Computer.

**cubedynamics.verbs.models** — Stubs for future modeling verbs.
- **cubedynamics.verbs.models.fit_model** (`function`, line 6, `src/cubedynamics/verbs/models.py`) — Placeholder for upcoming modeling verbs.

**cubedynamics.verbs.plot** — Plotting verb for displaying cubes via :class:`CubePlot`.
- **cubedynamics.verbs.plot.plot** (`function`, line 38, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 55, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 70, `src/cubedynamics/verbs/plot.py`) — Plot a cube or return a plotting verb.

**cubedynamics.verbs.plot_mean** — Verb for plotting mean and variance cubes side-by-side.
- **cubedynamics.verbs.plot_mean.plot_mean** (`function`, line 21, `src/cubedynamics/verbs/plot_mean.py`) — Plot mean and variance cubes with synchronized controls.

**cubedynamics.verbs.stats** — Statistical cube verbs with consistent cube->cube semantics.
- **cubedynamics.verbs.stats.anomaly** (`function`, line 247, `src/cubedynamics/verbs/stats.py`) — Return a pipe verb that subtracts the mean over ``dim``.
- **cubedynamics.verbs.stats.mean** (`function`, line 52, `src/cubedynamics/verbs/stats.py`) — Return a pipe-ready reducer computing the mean along ``dim``.
- **cubedynamics.verbs.stats.rolling_tail_dep_vs_center** (`function`, line 315, `src/cubedynamics/verbs/stats.py`) — Return a rolling "tail dependence vs center" contrast along ``dim``.
- **cubedynamics.verbs.stats.variance** (`function`, line 75, `src/cubedynamics/verbs/stats.py`) — Return a variance reducer along ``dim`` with optional dimension retention.
- **cubedynamics.verbs.stats.zscore** (`function`, line 263, `src/cubedynamics/verbs/stats.py`) — Return a standardized anomaly verb (z-score) along ``dim``.

**cubedynamics.viewers.cube_viewer** —
- **cubedynamics.viewers.cube_viewer.write_cube_viewer** (`function`, line 102, `src/cubedynamics/viewers/cube_viewer.py`) — Generate a standalone HTML/JS cube viewer for a 3D DataArray.

**cubedynamics.viz.lexcube_viz** — Lexcube visualization helpers.
- **cubedynamics.viz.lexcube_viz.show_cube_lexcube** (`function`, line 15, `src/cubedynamics/viz/lexcube_viz.py`) — Create a Lexcube Cube3DWidget from a 3D cube (time, y, x).

**cubedynamics.viz.qa_plots** — Quality-assurance plotting helpers.
- **cubedynamics.viz.qa_plots.plot_median_over_space** (`function`, line 9, `src/cubedynamics/viz/qa_plots.py`) — Plot the median over space of a 3D cube as a time series.

### Section 2: Verbs

**cubedynamics.verbs** — Namespace exposing pipe-friendly cube verbs.
- **cubedynamics.verbs._plot_time_hull_vase** (`function`, line 201, `src/cubedynamics/verbs/__init__.py`) — Render a TimeHull-derived vase using matplotlib.
- **cubedynamics.verbs._unwrap_dataarray** (`function`, line 40, `src/cubedynamics/verbs/__init__.py`) — Normalize a verb input to an (xarray.DataArray, original_obj) pair.
- **cubedynamics.verbs.climate_hist** (`function`, line 315, `src/cubedynamics/verbs/__init__.py`) — Plot histogram of climate inside vs outside fire perimeters.
- **cubedynamics.verbs.extract** (`function`, line 133, `src/cubedynamics/verbs/__init__.py`) — Verb: attach fire time-hull + climate summary (and a vase-like hull)
- **cubedynamics.verbs.extract._op** (`method`, line 171, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.fire_panel** (`function`, line 493, `src/cubedynamics/verbs/__init__.py`) — Convenience helper: fire time-hull + climate distribution "panel".
- **cubedynamics.verbs.fire_panel._inner** (`method`, line 526, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.fire_plot** (`function`, line 393, `src/cubedynamics/verbs/__init__.py`) — High-level convenience verb: fire time-hull × climate visualization.
- **cubedynamics.verbs.fire_plot._inner** (`method`, line 470, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.landsat8_mpc** (`function`, line 68, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for the Landsat MPC helper.
- **cubedynamics.verbs.landsat_ndvi_plot** (`function`, line 88, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for Landsat NDVI plotting.
- **cubedynamics.verbs.landsat_vis_ndvi** (`function`, line 80, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for a visualization-friendly Landsat NDVI cube.
- **cubedynamics.verbs.show_cube_lexcube** (`function`, line 96, `src/cubedynamics/verbs/__init__.py`) — Render a Lexcube widget as a side-effect and return the original cube.
- **cubedynamics.verbs.show_cube_lexcube._op** (`method`, line 104, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.vase** (`function`, line 274, `src/cubedynamics/verbs/__init__.py`) — High-level vase plotting verb with TimeHull support.
- **cubedynamics.verbs.vase._inner** (`method`, line 284, `src/cubedynamics/verbs/__init__.py`) —

**cubedynamics.verbs.custom** — Generic custom-function verbs.
- **cubedynamics.verbs.custom.apply** (`function`, line 10, `src/cubedynamics/verbs/custom.py`) — Return a verb that applies ``func`` to the incoming cube.
- **cubedynamics.verbs.custom.apply._op** (`method`, line 23, `src/cubedynamics/verbs/custom.py`) —

**cubedynamics.verbs.fire** —
- **cubedynamics.verbs.fire.fire_derivative** (`function`, line 167, `src/cubedynamics/verbs/fire.py`) — Fire derivative hull visualization verb.
- **cubedynamics.verbs.fire.fire_plot** (`function`, line 25, `src/cubedynamics/verbs/fire.py`) — Fire time-hull + climate visualization verb.

**cubedynamics.verbs.flatten** — Shape-changing verbs for flattening cubes.
- **cubedynamics.verbs.flatten.flatten_cube** (`function`, line 31, `src/cubedynamics/verbs/flatten.py`) — Flatten all non-time dimensions into a single ``sample`` dimension.
- **cubedynamics.verbs.flatten.flatten_cube._op** (`method`, line 40, `src/cubedynamics/verbs/flatten.py`) —
- **cubedynamics.verbs.flatten.flatten_space** (`function`, line 8, `src/cubedynamics/verbs/flatten.py`) — Flatten spatial dimensions (``y`` and ``x``) into a ``pixel`` dimension.
- **cubedynamics.verbs.flatten.flatten_space._op** (`method`, line 20, `src/cubedynamics/verbs/flatten.py`) —

**cubedynamics.verbs.landsat_mpc** — Landsat-8 streaming via Microsoft Planetary Computer (MPC).
- **cubedynamics.verbs.landsat_mpc._bounding_box_from_mask** (`function`, line 228, `src/cubedynamics/verbs/landsat_mpc.py`) — Return slices that crop to the non-NaN footprint of ``mask``.
- **cubedynamics.verbs.landsat_mpc._coarsen_if_needed** (`function`, line 248, `src/cubedynamics/verbs/landsat_mpc.py`) — Coarsen ``da`` along y/x so sizes do not exceed ``max_*``.
- **cubedynamics.verbs.landsat_mpc._compute_ndvi_from_stack** (`function`, line 204, `src/cubedynamics/verbs/landsat_mpc.py`) — Compute NDVI from a Landsat stack with a ``band`` dimension.
- **cubedynamics.verbs.landsat_mpc.landsat8_mpc** (`function`, line 155, `src/cubedynamics/verbs/landsat_mpc.py`) — Landsat 8 (MPC) streaming verb for cubedynamics.
- **cubedynamics.verbs.landsat_mpc.landsat8_mpc_stream** (`function`, line 62, `src/cubedynamics/verbs/landsat_mpc.py`) — Stream Landsat-8 Collection 2 Level-2 scenes from Microsoft Planetary Computer.
- **cubedynamics.verbs.landsat_mpc.landsat_ndvi_plot** (`function`, line 318, `src/cubedynamics/verbs/landsat_mpc.py`) — Load Landsat NDVI, downsample for visualization, and render the cube viewer.
- **cubedynamics.verbs.landsat_mpc.landsat_vis_ndvi** (`function`, line 263, `src/cubedynamics/verbs/landsat_mpc.py`) — Return a visualization-friendly Landsat NDVI cube.
- **cubedynamics.verbs.landsat_mpc.pipeable** (`function`, line 44, `src/cubedynamics/verbs/landsat_mpc.py`) — Decorator that makes a verb callable or pipe-friendly.
- **cubedynamics.verbs.landsat_mpc.pipeable._wrapper** (`method`, line 54, `src/cubedynamics/verbs/landsat_mpc.py`) —

**cubedynamics.verbs.models** — Stubs for future modeling verbs.
- **cubedynamics.verbs.models.fit_model** (`function`, line 6, `src/cubedynamics/verbs/models.py`) — Placeholder for upcoming modeling verbs.

**cubedynamics.verbs.plot** — Plotting verb for displaying cubes via :class:`CubePlot`.
- **cubedynamics.verbs.plot.PlotOptions** (`class`, line 25, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 38, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 55, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 70, `src/cubedynamics/verbs/plot.py`) — Plot a cube or return a plotting verb.
- **cubedynamics.verbs.plot.plot._plot** (`method`, line 103, `src/cubedynamics/verbs/plot.py`) —

**cubedynamics.verbs.plot_mean** — Verb for plotting mean and variance cubes side-by-side.
- **cubedynamics.verbs.plot_mean._materialize_if_virtual** (`function`, line 15, `src/cubedynamics/verbs/plot_mean.py`) —
- **cubedynamics.verbs.plot_mean.plot_mean** (`function`, line 21, `src/cubedynamics/verbs/plot_mean.py`) — Plot mean and variance cubes with synchronized controls.
- **cubedynamics.verbs.plot_mean.plot_mean._op** (`method`, line 34, `src/cubedynamics/verbs/plot_mean.py`) —

**cubedynamics.verbs.stats** — Statistical cube verbs with consistent cube->cube semantics.
- **cubedynamics.verbs.stats._broadcast_like** (`function`, line 43, `src/cubedynamics/verbs/stats.py`) — Broadcast ``stat`` so it can be combined elementwise with ``obj``.
- **cubedynamics.verbs.stats._ensure_dim** (`function`, line 14, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._expand_dim** (`function`, line 27, `src/cubedynamics/verbs/stats.py`) — Return ``reduced`` with ``dim`` added back as a length-1 dimension.
- **cubedynamics.verbs.stats._mean_virtual_space** (`function`, line 220, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._mean_virtual_time** (`function`, line 142, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._variance_virtual_space** (`function`, line 180, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._variance_virtual_time** (`function`, line 98, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.anomaly** (`function`, line 247, `src/cubedynamics/verbs/stats.py`) — Return a pipe verb that subtracts the mean over ``dim``.
- **cubedynamics.verbs.stats.anomaly._op** (`method`, line 254, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.mean** (`function`, line 52, `src/cubedynamics/verbs/stats.py`) — Return a pipe-ready reducer computing the mean along ``dim``.
- **cubedynamics.verbs.stats.mean._op** (`method`, line 60, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.rolling_tail_dep_vs_center** (`function`, line 315, `src/cubedynamics/verbs/stats.py`) — Return a rolling "tail dependence vs center" contrast along ``dim``.
- **cubedynamics.verbs.stats.rolling_tail_dep_vs_center._op** (`method`, line 340, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.variance** (`function`, line 75, `src/cubedynamics/verbs/stats.py`) — Return a variance reducer along ``dim`` with optional dimension retention.
- **cubedynamics.verbs.stats.variance._op** (`method`, line 90, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.variance._variance_virtual_cube** (`method`, line 83, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.variance._variance_xarray** (`method`, line 78, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.zscore** (`function`, line 263, `src/cubedynamics/verbs/stats.py`) — Return a standardized anomaly verb (z-score) along ``dim``.
- **cubedynamics.verbs.stats.zscore._op** (`method`, line 277, `src/cubedynamics/verbs/stats.py`) —

**cubedynamics.verbs.tubes** —
- **cubedynamics.verbs.tubes.tubes** (`function`, line 11, `src/cubedynamics/verbs/tubes.py`) — High-level verb: find suitability tubes and plot one as a vase.
- **cubedynamics.verbs.tubes.tubes._inner** (`method`, line 40, `src/cubedynamics/verbs/tubes.py`) —

**cubedynamics.verbs.vase** —
- **cubedynamics.verbs.vase.vase** (`function`, line 67, `src/cubedynamics/verbs/vase.py`) — High-level vase plotting verb.
- **cubedynamics.verbs.vase.vase._inner** (`method`, line 91, `src/cubedynamics/verbs/vase.py`) —
- **cubedynamics.verbs.vase.vase_demo** (`function`, line 151, `src/cubedynamics/verbs/vase.py`) — Convenience verb: build a demo stacked-polygon vase and plot it.
- **cubedynamics.verbs.vase.vase_demo._inner** (`method`, line 190, `src/cubedynamics/verbs/vase.py`) —
- **cubedynamics.verbs.vase.vase_extract** (`function`, line 36, `src/cubedynamics/verbs/vase.py`) — Mask a cube so that values outside the vase become ``NaN``.
- **cubedynamics.verbs.vase.vase_mask** (`function`, line 12, `src/cubedynamics/verbs/vase.py`) — Compute a boolean vase mask for a time-varying polygon hull.

### Section 3: Dataset loaders / data access

**cubedynamics.correlation_cubes** — Correlation and trend helpers for streamed cubes.
- **cubedynamics.correlation_cubes.correlation_cube** (`function`, line 10, `src/cubedynamics/correlation_cubes.py`) — Compute correlations between a reference cube and streamed targets.

**cubedynamics.data.gridmet** — GRIDMET data access helpers.
- **cubedynamics.data.gridmet._build_coords_for_aoi** (`function`, line 339, `src/cubedynamics/data/gridmet.py`) — Create evenly spaced coordinate arrays tailored to the AOI.
- **cubedynamics.data.gridmet._coerce_legacy_gridmet_aoi** (`function`, line 251, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet._crop_to_aoi** (`function`, line 352, `src/cubedynamics/data/gridmet.py`) — Select the AOI bounds along the spatial dimensions.
- **cubedynamics.data.gridmet._load_gridmet_cube_impl** (`function`, line 148, `src/cubedynamics/data/gridmet.py`) — Internal implementation shared by legacy and modern entrypoints.
- **cubedynamics.data.gridmet._load_gridmet_cube_legacy** (`function`, line 190, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet._normalize_variables** (`function`, line 241, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet._open_gridmet_download** (`function`, line 302, `src/cubedynamics/data/gridmet.py`) — Return a small in-memory Dataset that mimics a download fallback.
- **cubedynamics.data.gridmet._open_gridmet_streaming** (`function`, line 261, `src/cubedynamics/data/gridmet.py`) — Return a dask-backed Dataset that mimics GRIDMET streaming access.
- **cubedynamics.data.gridmet._resolve_chunks** (`function`, line 362, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet.load_gridmet_cube** (`function`, line 27, `src/cubedynamics/data/gridmet.py`) — Load a GRIDMET-like climate cube.

**cubedynamics.data.prism** — PRISM data access helpers with a streaming-first contract.
- **cubedynamics.data.prism._bbox_mapping_from_geojson** (`function`, line 271, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._bbox_mapping_from_point** (`function`, line 247, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._bbox_mapping_from_sequence** (`function`, line 257, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._build_coords_for_aoi** (`function`, line 414, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._coerce_aoi** (`function`, line 220, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._coerce_legacy_aoi** (`function`, line 325, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._crop_to_aoi** (`function`, line 424, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._extract_geojson_geometries** (`function`, line 290, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._flatten_geojson_coords** (`function`, line 308, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._load_prism_cube_impl** (`function`, line 124, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._load_prism_cube_legacy** (`function`, line 159, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._normalize_variables** (`function`, line 210, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._open_prism_download** (`function`, line 380, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._open_prism_streaming** (`function`, line 338, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._resolve_chunks** (`function`, line 432, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism.load_prism_cube** (`function`, line 20, `src/cubedynamics/data/prism.py`) — Load a PRISM-like cube.

**cubedynamics.data.sentinel2** — Sentinel-2 data access helpers.
- **cubedynamics.data.sentinel2._to_dataarray** (`function`, line 15, `src/cubedynamics/data/sentinel2.py`) —
- **cubedynamics.data.sentinel2.load_s2_cube** (`function`, line 25, `src/cubedynamics/data/sentinel2.py`) — Stream Sentinel-2 L2A data via cubo and return a dask-backed xarray object.
- **cubedynamics.data.sentinel2.load_s2_ndvi_cube** (`function`, line 67, `src/cubedynamics/data/sentinel2.py`) — Stream Sentinel-2 and return an NDVI cube ready for downstream ops.

**cubedynamics.fire_time_hull** —
- **cubedynamics.fire_time_hull._infer_cube_epsg** (`function`, line 685, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._load_real_gridmet_cube** (`function`, line 584, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._load_synthetic_gridmet_cube** (`function`, line 615, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.load_climate_cube_for_event** (`function`, line 657, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.load_fired_conus_ak** (`function`, line 165, `src/cubedynamics/fire_time_hull.py`) — Load FIRED CONUS+AK polygons from a local cache, with optional download.
- **cubedynamics.fire_time_hull.load_gridmet_cube** (`function`, line 638, `src/cubedynamics/fire_time_hull.py`) —

**cubedynamics.ops.stats** — Statistical pipeable operations.
- **cubedynamics.ops.stats.correlation_cube** (`function`, line 8, `src/cubedynamics/ops/stats.py`) — Factory placeholder for a future correlation cube operation.

**cubedynamics.ops_fire.climate_hull_extract** —
- **cubedynamics.ops_fire.climate_hull_extract._infer_cube_epsg** (`function`, line 55, `src/cubedynamics/ops_fire/climate_hull_extract.py`) — Try to infer an EPSG code for the cube from attrs/coords/rioxarray.

**cubedynamics.ops_fire.fired_io** —
- **cubedynamics.ops_fire.fired_io.load_fired_conus_ak** (`function`, line 36, `src/cubedynamics/ops_fire/fired_io.py`) — Stream FIRED CONUS+AK polygons (Nov 2001–Mar 2021) from CU Scholar.
- **cubedynamics.ops_fire.fired_io.load_fired_event_by_joint_support** (`function`, line 227, `src/cubedynamics/ops_fire/fired_io.py`) — Convenience helper: load FIRED, pick an event with joint temporal support,

**cubedynamics.plotting.cube_plot** — Grammar-of-graphics + streaming core for cube plotting.
- **cubedynamics.plotting.cube_plot.geom_cube** (`function`, line 132, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.theme_cube_studio** (`function`, line 78, `src/cubedynamics/plotting/cube_plot.py`) — Return the default "studio" theme.

**cubedynamics.plotting.cube_viewer** —
- **cubedynamics.plotting.cube_viewer._render_cube_html** (`function`, line 194, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer.cube_from_dataarray** (`function`, line 777, `src/cubedynamics/plotting/cube_viewer.py`) —

**cubedynamics.plotting.viewer** — Utilities for rendering the cube viewer safely inside notebooks.
- **cubedynamics.plotting.viewer._write_cube_html** (`function`, line 12, `src/cubedynamics/plotting/viewer.py`) — Write a standalone cube viewer HTML file to the working directory.
- **cubedynamics.plotting.viewer.show_cube_viewer** (`function`, line 22, `src/cubedynamics/plotting/viewer.py`) — Return an IFrame pointing at a self-contained cube viewer file.

**cubedynamics.prism_streaming** — Streaming-first helpers for PRISM datasets.
- **cubedynamics.prism_streaming.stream_prism_to_cube** (`function`, line 15, `src/cubedynamics/prism_streaming.py`) — Stream PRISM data into an xarray object.

**cubedynamics.sentinel** — Sentinel-2 helper utilities for CubeDynamics.
- **cubedynamics.sentinel.load_sentinel2_bands_cube** (`function`, line 87, `src/cubedynamics/sentinel.py`) — Stream a Sentinel-2 L2A cube for a user-selected list of bands.
- **cubedynamics.sentinel.load_sentinel2_cube** (`function`, line 18, `src/cubedynamics/sentinel.py`) — Stream a Sentinel-2 L2A cube via ``cubo``.
- **cubedynamics.sentinel.load_sentinel2_ndvi_cube** (`function`, line 126, `src/cubedynamics/sentinel.py`) — Stream Sentinel-2 L2A data and compute a raw NDVI cube.
- **cubedynamics.sentinel.load_sentinel2_ndvi_zscore_cube** (`function`, line 172, `src/cubedynamics/sentinel.py`) — Convenience wrapper that returns a z-scored Sentinel-2 NDVI cube.

**cubedynamics.stats.rolling** — Rolling-window computation utilities.
- **cubedynamics.stats.rolling.rolling_pairwise_stat_cube** (`function`, line 18, `src/cubedynamics/stats/rolling.py`) — Compute a rolling-window pairwise statistic vs a reference time series.

**cubedynamics.streaming.gridmet** —
- **cubedynamics.streaming.gridmet.stream_gridmet_to_cube** (`function`, line 168, `src/cubedynamics/streaming/gridmet.py`) — Stream a gridMET subset as an xarray.DataArray "cube" for a given AOI.

## Tests

**cubedynamics.tests.test_gridmet_streaming** — Tests for the gridMET streaming helper.
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_bbox_padding** (`function`, line 103, `src/cubedynamics/tests/test_gridmet_streaming.py`) — Tiny AOI bounding boxes should still capture at least one grid cell.
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_default_source_smoke** (`function`, line 13, `src/cubedynamics/tests/test_gridmet_streaming.py`) — Calling the helper without `source` should return a time-indexed cube.
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_descending_lat** (`function`, line 59, `src/cubedynamics/tests/test_gridmet_streaming.py`) — Descending latitude axes should still produce non-empty subsets.

**cubedynamics.tests.test_import_and_pipe** — Basic import and pipe integration tests for cubedynamics.
- **cubedynamics.tests.test_import_and_pipe.test_import_cubedynamics_has_version** (`function`, line 10, `src/cubedynamics/tests/test_import_and_pipe.py`) — Ensure the package exposes a version attribute.

**cubedynamics.tests.test_piping_ops** — Tests for the ggplot-style pipe syntax and verbs.
- **cubedynamics.tests.test_piping_ops.test_show_cube_lexcube_returns_original_cube** (`function`, line 57, `src/cubedynamics/tests/test_piping_ops.py`) —

**cubedynamics.utils.cube_css** — Helpers for emitting lightweight CSS cube HTML scaffolding.
- **cubedynamics.utils.cube_css.write_css_cube_static** (`function`, line 60, `src/cubedynamics/utils/cube_css.py`) — Write a standalone HTML page with a simple CSS-based cube skeleton.

**cubedynamics.variables** — Semantic variable loaders for common climate and vegetation variables.
- **cubedynamics.variables._load_temperature** (`function`, line 95, `src/cubedynamics/variables.py`) —
- **cubedynamics.variables._resolve_temp_variable** (`function`, line 84, `src/cubedynamics/variables.py`) —
- **cubedynamics.variables._year_chunks** (`function`, line 329, `src/cubedynamics/variables.py`) — Yield (start_str, end_str) for consecutive chunks of up to years_per_chunk.
- **cubedynamics.variables.estimate_cube_size** (`function`, line 43, `src/cubedynamics/variables.py`) — Return a rough scalar size estimate for a requested cube.
- **cubedynamics.variables.ndvi** (`function`, line 426, `src/cubedynamics/variables.py`) — Load a Sentinel-2 NDVI cube.
- **cubedynamics.variables.ndvi_chunked** (`function`, line 355, `src/cubedynamics/variables.py`) — Load a Sentinel-2 NDVI cube in time chunks and concatenate along 'time'.
- **cubedynamics.variables.temperature** (`function`, line 138, `src/cubedynamics/variables.py`) — Load a mean temperature cube from the chosen climate provider.
- **cubedynamics.variables.temperature_anomaly** (`function`, line 260, `src/cubedynamics/variables.py`) — Compute a temperature anomaly cube along the time dimension.
- **cubedynamics.variables.temperature_max** (`function`, line 234, `src/cubedynamics/variables.py`) — Load a maximum daily temperature cube from the selected source.
- **cubedynamics.variables.temperature_min** (`function`, line 208, `src/cubedynamics/variables.py`) — Load a minimum daily temperature cube from the selected source.

**cubedynamics.verbs** — Namespace exposing pipe-friendly cube verbs.
- **cubedynamics.verbs.show_cube_lexcube** (`function`, line 96, `src/cubedynamics/verbs/__init__.py`) — Render a Lexcube widget as a side-effect and return the original cube.

**cubedynamics.verbs.flatten** — Shape-changing verbs for flattening cubes.
- **cubedynamics.verbs.flatten.flatten_cube** (`function`, line 31, `src/cubedynamics/verbs/flatten.py`) — Flatten all non-time dimensions into a single ``sample`` dimension.

**cubedynamics.viewers.cube_viewer** —
- **cubedynamics.viewers.cube_viewer.write_cube_viewer** (`function`, line 102, `src/cubedynamics/viewers/cube_viewer.py`) — Generate a standalone HTML/JS cube viewer for a 3D DataArray.

**cubedynamics.viewers.simple_plot** —
- **cubedynamics.viewers.simple_plot.simple_cube_widget** (`function`, line 56, `src/cubedynamics/viewers/simple_plot.py`) — Minimal interactive viewer for a 3D cube (time, y, x).

**cubedynamics.viz.lexcube_viz** — Lexcube visualization helpers.
- **cubedynamics.viz.lexcube_viz.show_cube_lexcube** (`function`, line 15, `src/cubedynamics/viz/lexcube_viz.py`) — Create a Lexcube Cube3DWidget from a 3D cube (time, y, x).

### Section 4: Visualization

**cubedynamics** — cubedynamics: streaming-first climate cube math.
- **cubedynamics.plot** (`function`, line 113, `src/cubedynamics/__init__.py`) — Convenience helper for plotting a 3D cube without using the pipe.

**cubedynamics.fire_time_hull** —
- **cubedynamics.fire_time_hull.plot_climate_filled_hull** (`function`, line 833, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.plot_derivative_hull** (`function`, line 1041, `src/cubedynamics/fire_time_hull.py`) — Plot a derivative hull with color and radius encoding the same
- **cubedynamics.fire_time_hull.plot_inside_outside_hist** (`function`, line 896, `src/cubedynamics/fire_time_hull.py`) —

**cubedynamics.hulls** — Plotting helper that builds ruled surfaces from daily polygons.
- **cubedynamics.hulls.plot_ruled_time_hull** (`function`, line 51, `src/cubedynamics/hulls.py`) — Build a 3D ruled surface describing event growth through time.

**cubedynamics.ops.viz** — Visualization verbs wrapping simple interactive widgets.
- **cubedynamics.ops.viz.plot** (`function`, line 12, `src/cubedynamics/ops/viz.py`) — Legacy wrapper for the interactive plotting verb.

**cubedynamics.plotting.cube_plot** — Grammar-of-graphics + streaming core for cube plotting.
- **cubedynamics.plotting.cube_plot._build_caption** (`function`, line 320, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._derive_legend_title** (`function`, line 309, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_lat** (`function`, line 348, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_lon** (`function`, line 357, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_numeric** (`function`, line 366, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_time_label** (`function`, line 340, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._infer_aes_from_data** (`function`, line 108, `src/cubedynamics/plotting/cube_plot.py`) — Infer a simple aesthetic mapping from a DataArray.
- **cubedynamics.plotting.cube_plot._looks_like_lat** (`function`, line 373, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._looks_like_lon** (`function`, line 400, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_cube** (`function`, line 132, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_outline** (`function`, line 140, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_path3d** (`function`, line 144, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_slice** (`function`, line 136, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_identity** (`function`, line 271, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_space_mean** (`function`, line 293, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_time_anomaly** (`function`, line 282, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_time_mean** (`function`, line 275, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.theme_cube_studio** (`function`, line 78, `src/cubedynamics/plotting/cube_plot.py`) — Return the default "studio" theme.

**cubedynamics.plotting.cube_viewer** —
- **cubedynamics.plotting.cube_viewer._apply_vase_tint** (`function`, line 79, `src/cubedynamics/plotting/cube_viewer.py`) — Apply an overlay color to ``rgb_arr`` wherever ``mask_2d`` is True.
- **cubedynamics.plotting.cube_viewer._array_to_png_base64** (`function`, line 117, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._axis_range_from_ticks** (`function`, line 1198, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._build_legend_html** (`function`, line 136, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._colorbar_labels** (`function`, line 124, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._colormap_to_rgba** (`function`, line 97, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._guess_axis_name** (`function`, line 1166, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._infer_axis_ticks** (`function`, line 1175, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._interior_plane_transform** (`function`, line 158, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._reduce_to_3d_time_y_x** (`function`, line 36, `src/cubedynamics/plotting/cube_viewer.py`) — Ensure the DataArray has dims (time, y, x) for the cube viewer.
- **cubedynamics.plotting.cube_viewer._render_cube_html** (`function`, line 194, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._rgba_to_png_base64** (`function`, line 111, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._vase_panel_transform** (`function`, line 178, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer.cube_from_dataarray** (`function`, line 777, `src/cubedynamics/plotting/cube_viewer.py`) —

**cubedynamics.plotting.viewer** — Utilities for rendering the cube viewer safely inside notebooks.
- **cubedynamics.plotting.viewer._write_cube_html** (`function`, line 12, `src/cubedynamics/plotting/viewer.py`) — Write a standalone cube viewer HTML file to the working directory.
- **cubedynamics.plotting.viewer.show_cube_viewer** (`function`, line 22, `src/cubedynamics/plotting/viewer.py`) — Return an IFrame pointing at a self-contained cube viewer file.

**cubedynamics.tests.test_piping_ops** — Tests for the ggplot-style pipe syntax and verbs.
- **cubedynamics.tests.test_piping_ops.test_show_cube_lexcube_returns_original_cube** (`function`, line 57, `src/cubedynamics/tests/test_piping_ops.py`) —

**cubedynamics.tests.test_progress** —
- **cubedynamics.tests.test_progress.test_ndvi_accepts_show_progress** (`function`, line 41, `src/cubedynamics/tests/test_progress.py`) —

**cubedynamics.vase_viz** — Vase visualization utilities for scientific 3-D workflows.
- **cubedynamics.vase_viz._convert_time_to_numeric** (`function`, line 60, `src/cubedynamics/vase_viz.py`) —
- **cubedynamics.vase_viz._validate_dims** (`function`, line 15, `src/cubedynamics/vase_viz.py`) —
- **cubedynamics.vase_viz.extract_vase_points** (`function`, line 21, `src/cubedynamics/vase_viz.py`) — Extract coordinates and values for voxels where ``mask`` is ``True``.
- **cubedynamics.vase_viz.vase_scatter_plot** (`function`, line 66, `src/cubedynamics/vase_viz.py`) — 3-D scientific scatter plot of voxels inside the vase.
- **cubedynamics.vase_viz.vase_scatter_with_hull** (`function`, line 158, `src/cubedynamics/vase_viz.py`) — Overlay vase scatter points with a translucent hull mesh.
- **cubedynamics.vase_viz.vase_to_mesh** (`function`, line 120, `src/cubedynamics/vase_viz.py`) — Convert VaseDefinition into a 3-D mesh using a sweep (loft) of polygons.

**cubedynamics.verbs** — Namespace exposing pipe-friendly cube verbs.
- **cubedynamics.verbs._plot_time_hull_vase** (`function`, line 201, `src/cubedynamics/verbs/__init__.py`) — Render a TimeHull-derived vase using matplotlib.
- **cubedynamics.verbs.fire_plot** (`function`, line 393, `src/cubedynamics/verbs/__init__.py`) — High-level convenience verb: fire time-hull × climate visualization.
- **cubedynamics.verbs.landsat_ndvi_plot** (`function`, line 88, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for Landsat NDVI plotting.
- **cubedynamics.verbs.show_cube_lexcube** (`function`, line 96, `src/cubedynamics/verbs/__init__.py`) — Render a Lexcube widget as a side-effect and return the original cube.

**cubedynamics.verbs.fire** —
- **cubedynamics.verbs.fire.fire_plot** (`function`, line 25, `src/cubedynamics/verbs/fire.py`) — Fire time-hull + climate visualization verb.

**cubedynamics.verbs.landsat_mpc** — Landsat-8 streaming via Microsoft Planetary Computer (MPC).
- **cubedynamics.verbs.landsat_mpc.landsat_ndvi_plot** (`function`, line 318, `src/cubedynamics/verbs/landsat_mpc.py`) — Load Landsat NDVI, downsample for visualization, and render the cube viewer.

**cubedynamics.verbs.plot** — Plotting verb for displaying cubes via :class:`CubePlot`.
- **cubedynamics.verbs.plot.plot** (`function`, line 38, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 55, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 70, `src/cubedynamics/verbs/plot.py`) — Plot a cube or return a plotting verb.

**cubedynamics.verbs.plot_mean** — Verb for plotting mean and variance cubes side-by-side.
- **cubedynamics.verbs.plot_mean._materialize_if_virtual** (`function`, line 15, `src/cubedynamics/verbs/plot_mean.py`) —
- **cubedynamics.verbs.plot_mean.plot_mean** (`function`, line 21, `src/cubedynamics/verbs/plot_mean.py`) — Plot mean and variance cubes with synchronized controls.

**cubedynamics.viewers.simple_plot** —
- **cubedynamics.viewers.simple_plot._infer_dims** (`function`, line 11, `src/cubedynamics/viewers/simple_plot.py`) — Infer time, y, x dim names for a 3D cube.
- **cubedynamics.viewers.simple_plot.simple_cube_widget** (`function`, line 56, `src/cubedynamics/viewers/simple_plot.py`) — Minimal interactive viewer for a 3D cube (time, y, x).

**cubedynamics.viz.lexcube_viz** — Lexcube visualization helpers.
- **cubedynamics.viz.lexcube_viz.show_cube_lexcube** (`function`, line 15, `src/cubedynamics/viz/lexcube_viz.py`) — Create a Lexcube Cube3DWidget from a 3D cube (time, y, x).

**cubedynamics.viz.qa_plots** — Quality-assurance plotting helpers.
- **cubedynamics.viz.qa_plots.plot_median_over_space** (`function`, line 9, `src/cubedynamics/viz/qa_plots.py`) — Plot the median over space of a 3D cube as a time series.

## Internal helpers

### Section 5: Full internal inventory

**cubedynamics** — cubedynamics: streaming-first climate cube math.
- **cubedynamics.plot** (`function`, line 113, `src/cubedynamics/__init__.py`) — Convenience helper for plotting a 3D cube without using the pipe.

**cubedynamics.correlation_cubes** — Correlation and trend helpers for streamed cubes.
- **cubedynamics.correlation_cubes.correlation_cube** (`function`, line 10, `src/cubedynamics/correlation_cubes.py`) — Compute correlations between a reference cube and streamed targets.

**cubedynamics.data.gridmet** — GRIDMET data access helpers.
- **cubedynamics.data.gridmet._build_coords_for_aoi** (`function`, line 339, `src/cubedynamics/data/gridmet.py`) — Create evenly spaced coordinate arrays tailored to the AOI.
- **cubedynamics.data.gridmet._coerce_legacy_gridmet_aoi** (`function`, line 251, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet._crop_to_aoi** (`function`, line 352, `src/cubedynamics/data/gridmet.py`) — Select the AOI bounds along the spatial dimensions.
- **cubedynamics.data.gridmet._load_gridmet_cube_impl** (`function`, line 148, `src/cubedynamics/data/gridmet.py`) — Internal implementation shared by legacy and modern entrypoints.
- **cubedynamics.data.gridmet._load_gridmet_cube_legacy** (`function`, line 190, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet._normalize_variables** (`function`, line 241, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet._open_gridmet_download** (`function`, line 302, `src/cubedynamics/data/gridmet.py`) — Return a small in-memory Dataset that mimics a download fallback.
- **cubedynamics.data.gridmet._open_gridmet_streaming** (`function`, line 261, `src/cubedynamics/data/gridmet.py`) — Return a dask-backed Dataset that mimics GRIDMET streaming access.
- **cubedynamics.data.gridmet._resolve_chunks** (`function`, line 362, `src/cubedynamics/data/gridmet.py`) —
- **cubedynamics.data.gridmet.load_gridmet_cube** (`function`, line 27, `src/cubedynamics/data/gridmet.py`) — Load a GRIDMET-like climate cube.

**cubedynamics.data.prism** — PRISM data access helpers with a streaming-first contract.
- **cubedynamics.data.prism._bbox_mapping_from_geojson** (`function`, line 271, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._bbox_mapping_from_point** (`function`, line 247, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._bbox_mapping_from_sequence** (`function`, line 257, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._build_coords_for_aoi** (`function`, line 414, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._coerce_aoi** (`function`, line 220, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._coerce_legacy_aoi** (`function`, line 325, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._crop_to_aoi** (`function`, line 424, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._extract_geojson_geometries** (`function`, line 290, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._flatten_geojson_coords** (`function`, line 308, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._load_prism_cube_impl** (`function`, line 124, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._load_prism_cube_legacy** (`function`, line 159, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._normalize_variables** (`function`, line 210, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._open_prism_download** (`function`, line 380, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._open_prism_streaming** (`function`, line 338, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism._resolve_chunks** (`function`, line 432, `src/cubedynamics/data/prism.py`) —
- **cubedynamics.data.prism.load_prism_cube** (`function`, line 20, `src/cubedynamics/data/prism.py`) — Load a PRISM-like cube.

**cubedynamics.data.sentinel2** — Sentinel-2 data access helpers.
- **cubedynamics.data.sentinel2._to_dataarray** (`function`, line 15, `src/cubedynamics/data/sentinel2.py`) —
- **cubedynamics.data.sentinel2.load_s2_cube** (`function`, line 25, `src/cubedynamics/data/sentinel2.py`) — Stream Sentinel-2 L2A data via cubo and return a dask-backed xarray object.
- **cubedynamics.data.sentinel2.load_s2_ndvi_cube** (`function`, line 67, `src/cubedynamics/data/sentinel2.py`) — Stream Sentinel-2 and return an NDVI cube ready for downstream ops.

**cubedynamics.demo** — Synthetic event helpers used throughout the documentation.
- **cubedynamics.demo._ellipse_polygon** (`function`, line 16, `src/cubedynamics/demo.py`) — Return a simple ellipse polygon centered at the origin.
- **cubedynamics.demo.make_demo_event** (`function`, line 23, `src/cubedynamics/demo.py`) — Create a synthetic FIRED-like GeoDataFrame for demos.

**cubedynamics.demo_vase** —
- **cubedynamics.demo_vase.DemoNamespace** (`class`, line 15, `src/cubedynamics/demo_vase.py`) — Namespace for small demo helpers, e.g.:
- **cubedynamics.demo_vase.DemoNamespace.stacked_polygon_vase** (`method`, line 22, `src/cubedynamics/demo_vase.py`) — Build a simple VaseDefinition composed of stacked polygons over time.

**cubedynamics.deprecations** — Helpers for emitting consistent deprecation warnings.
- **cubedynamics.deprecations.warn_deprecated** (`function`, line 13, `src/cubedynamics/deprecations.py`) — Issue a standardized :class:`DeprecationWarning` for a legacy symbol.

**cubedynamics.fire_time_hull** —
- **cubedynamics.fire_time_hull.ClimateCube** (`class`, line 285, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.FireEventDaily** (`class`, line 265, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.HullClimateSummary** (`class`, line 290, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.TemporalSupport** (`class`, line 31, `src/cubedynamics/fire_time_hull.py`) — Simple description of temporal coverage for a dataset.
- **cubedynamics.fire_time_hull.TemporalSupport.contains** (`method`, line 37, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.TimeHull** (`class`, line 275, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._download_and_extract_fired_to_cache** (`function`, line 54, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._download_gridmet_files_to_cache** (`function`, line 571, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._gridmet_urls_for_var_years** (`function`, line 567, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._hull_grid** (`function`, line 935, `src/cubedynamics/fire_time_hull.py`) — Recover the (M, T, 3) grid from a TimeHull, where:
- **cubedynamics.fire_time_hull._infer_cube_epsg** (`function`, line 685, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._infer_spatial_dims** (`function`, line 677, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._largest_polygon** (`function`, line 337, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._load_real_gridmet_cube** (`function`, line 584, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._load_synthetic_gridmet_cube** (`function`, line 615, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._sample_ring_equal_steps** (`function`, line 350, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull._tri_area** (`function`, line 367, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.build_fire_event** (`function`, line 397, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.build_inside_outside_climate_samples** (`function`, line 721, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.clean_event_daily_rows** (`function`, line 296, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.compute_derivative_hull** (`function`, line 961, `src/cubedynamics/fire_time_hull.py`) — Build a derivative-based hull from an existing TimeHull.
- **cubedynamics.fire_time_hull.compute_time_hull_geometry** (`function`, line 431, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.load_climate_cube_for_event** (`function`, line 657, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.load_fired_conus_ak** (`function`, line 165, `src/cubedynamics/fire_time_hull.py`) — Load FIRED CONUS+AK polygons from a local cache, with optional download.
- **cubedynamics.fire_time_hull.load_gridmet_cube** (`function`, line 638, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.pick_event_with_joint_support** (`function`, line 374, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.plot_climate_filled_hull** (`function`, line 833, `src/cubedynamics/fire_time_hull.py`) —
- **cubedynamics.fire_time_hull.plot_derivative_hull** (`function`, line 1041, `src/cubedynamics/fire_time_hull.py`) — Plot a derivative hull with color and radius encoding the same
- **cubedynamics.fire_time_hull.plot_inside_outside_hist** (`function`, line 896, `src/cubedynamics/fire_time_hull.py`) —

**cubedynamics.hulls** — Plotting helper that builds ruled surfaces from daily polygons.
- **cubedynamics.hulls._center_xy** (`function`, line 45, `src/cubedynamics/hulls.py`) —
- **cubedynamics.hulls._largest_polygon** (`function`, line 19, `src/cubedynamics/hulls.py`) —
- **cubedynamics.hulls._sample_ring_equal_steps** (`function`, line 30, `src/cubedynamics/hulls.py`) — Equal-arclength samples on the polygon exterior.
- **cubedynamics.hulls.plot_ruled_time_hull** (`function`, line 51, `src/cubedynamics/hulls.py`) — Build a 3D ruled surface describing event growth through time.

**cubedynamics.indices.vegetation** — Vegetation index helpers.
- **cubedynamics.indices.vegetation._get_band_dataarray** (`function`, line 10, `src/cubedynamics/indices/vegetation.py`) —
- **cubedynamics.indices.vegetation.compute_ndvi_from_s2** (`function`, line 20, `src/cubedynamics/indices/vegetation.py`) — Compute NDVI from a Sentinel-2 Dataset or DataArray.

**cubedynamics.ops.io** — I/O helpers for pipe chains.
- **cubedynamics.ops.io.to_netcdf** (`function`, line 8, `src/cubedynamics/ops/io.py`) — Factory for a pipeable ``.to_netcdf`` side-effect operation.
- **cubedynamics.ops.io.to_netcdf._inner** (`method`, line 11, `src/cubedynamics/ops/io.py`) —

**cubedynamics.ops.ndvi** — NDVI-related pipeable operations.
- **cubedynamics.ops.ndvi.ndvi_from_s2** (`function`, line 8, `src/cubedynamics/ops/ndvi.py`) — Factory returning a Sentinel-2 NDVI transform for pipe chains.
- **cubedynamics.ops.ndvi.ndvi_from_s2._inner** (`method`, line 11, `src/cubedynamics/ops/ndvi.py`) —

**cubedynamics.ops.stats** — Statistical pipeable operations.
- **cubedynamics.ops.stats.correlation_cube** (`function`, line 8, `src/cubedynamics/ops/stats.py`) — Factory placeholder for a future correlation cube operation.
- **cubedynamics.ops.stats.correlation_cube._inner** (`method`, line 22, `src/cubedynamics/ops/stats.py`) —

**cubedynamics.ops.transforms** — Transform-style pipeable operations.
- **cubedynamics.ops.transforms.anomaly** (`function`, line 12, `src/cubedynamics/ops/transforms.py`) — Deprecated shim forwarding to :func:`cubedynamics.verbs.stats.anomaly`.
- **cubedynamics.ops.transforms.month_filter** (`function`, line 18, `src/cubedynamics/ops/transforms.py`) — Factory for filtering calendar months from a ``time`` coordinate.
- **cubedynamics.ops.transforms.month_filter._inner** (`method`, line 30, `src/cubedynamics/ops/transforms.py`) —

**cubedynamics.ops.viz** — Visualization verbs wrapping simple interactive widgets.
- **cubedynamics.ops.viz.plot** (`function`, line 12, `src/cubedynamics/ops/viz.py`) — Legacy wrapper for the interactive plotting verb.
- **cubedynamics.ops.viz.plot._inner** (`method`, line 24, `src/cubedynamics/ops/viz.py`) —

**cubedynamics.ops_fire.climate_hull_extract** —
- **cubedynamics.ops_fire.climate_hull_extract.HullClimateSummary** (`class`, line 16, `src/cubedynamics/ops_fire/climate_hull_extract.py`) — Climate sample summary relative to a fire time-hull.
- **cubedynamics.ops_fire.climate_hull_extract._infer_cube_epsg** (`function`, line 55, `src/cubedynamics/ops_fire/climate_hull_extract.py`) — Try to infer an EPSG code for the cube from attrs/coords/rioxarray.
- **cubedynamics.ops_fire.climate_hull_extract._infer_spatial_dims** (`function`, line 35, `src/cubedynamics/ops_fire/climate_hull_extract.py`) — Infer spatial dimension names for a climate cube.
- **cubedynamics.ops_fire.climate_hull_extract.build_inside_outside_climate_samples** (`function`, line 104, `src/cubedynamics/ops_fire/climate_hull_extract.py`) — Build inside vs outside climate samples using FIRED perimeters and a climate cube.

**cubedynamics.ops_fire.fired_api** —
- **cubedynamics.ops_fire.fired_api.fired_event** (`function`, line 14, `src/cubedynamics/ops_fire/fired_api.py`) — Public entry point for loading a FIRED fire event.

**cubedynamics.ops_fire.fired_io** —
- **cubedynamics.ops_fire.fired_io.TemporalSupport** (`class`, line 20, `src/cubedynamics/ops_fire/fired_io.py`) — Simple representation of a dataset's trustworthy temporal coverage.
- **cubedynamics.ops_fire.fired_io.load_fired_conus_ak** (`function`, line 36, `src/cubedynamics/ops_fire/fired_io.py`) — Stream FIRED CONUS+AK polygons (Nov 2001–Mar 2021) from CU Scholar.
- **cubedynamics.ops_fire.fired_io.load_fired_event_by_joint_support** (`function`, line 227, `src/cubedynamics/ops_fire/fired_io.py`) — Convenience helper: load FIRED, pick an event with joint temporal support,
- **cubedynamics.ops_fire.fired_io.pick_event_with_joint_support** (`function`, line 143, `src/cubedynamics/ops_fire/fired_io.py`) — Pick a FIRED event whose buffered time window sits inside climate support.

**cubedynamics.ops_fire.time_hull** —
- **cubedynamics.ops_fire.time_hull.FireEventDaily** (`class`, line 14, `src/cubedynamics/ops_fire/time_hull.py`) — One FIRED event with daily perimeters and basic metadata.
- **cubedynamics.ops_fire.time_hull.TimeHull** (`class`, line 39, `src/cubedynamics/ops_fire/time_hull.py`) — 3D time-hull geometry for a single fire event.
- **cubedynamics.ops_fire.time_hull.Vase** (`class`, line 68, `src/cubedynamics/ops_fire/time_hull.py`) — Simple container for a vase-like surface derived from a TimeHull.
- **cubedynamics.ops_fire.time_hull._largest_polygon** (`function`, line 149, `src/cubedynamics/ops_fire/time_hull.py`) — Return the largest Polygon from a (Multi)Polygon geometry.
- **cubedynamics.ops_fire.time_hull._sample_ring_equal_steps** (`function`, line 174, `src/cubedynamics/ops_fire/time_hull.py`) — Sample `n_samples` points along the polygon's exterior at equal arc length.
- **cubedynamics.ops_fire.time_hull._tri_area** (`function`, line 211, `src/cubedynamics/ops_fire/time_hull.py`) — Area of a 3D triangle (p, q, r).
- **cubedynamics.ops_fire.time_hull.build_fire_event** (`function`, line 228, `src/cubedynamics/ops_fire/time_hull.py`) — Clean a single FIRED event and return a FireEventDaily object.
- **cubedynamics.ops_fire.time_hull.clean_event_daily_rows** (`function`, line 90, `src/cubedynamics/ops_fire/time_hull.py`) — Return a cleaned, sorted per-day GeoDataFrame for a single FIRED event.
- **cubedynamics.ops_fire.time_hull.compute_time_hull_geometry** (`function`, line 288, `src/cubedynamics/ops_fire/time_hull.py`) — Build a 3D ruled time-hull geometry from FIRED daily perimeters.
- **cubedynamics.ops_fire.time_hull.time_hull_to_vase** (`function`, line 474, `src/cubedynamics/ops_fire/time_hull.py`) — Convert a TimeHull into a vase-like representation suitable for v.vase.

**cubedynamics.ops_io.gridmet_api** —
- **cubedynamics.ops_io.gridmet_api.gridmet** (`function`, line 8, `src/cubedynamics/ops_io/gridmet_api.py`) — Load a GRIDMET variable as an xarray.DataArray suitable for CubePlot.

**cubedynamics.piping** — Pipe wrapper enabling ``|`` composition for cube operations.
- **cubedynamics.piping.Pipe** (`class`, line 41, `src/cubedynamics/piping.py`) — Wrap a value so it can flow through ``|`` pipe stages.
- **cubedynamics.piping.Pipe.__init__** (`method`, line 44, `src/cubedynamics/piping.py`) —
- **cubedynamics.piping.Pipe.__or__** (`method`, line 47, `src/cubedynamics/piping.py`) — Apply ``func`` to the wrapped value and return a new :class:`Pipe`.
- **cubedynamics.piping.Pipe.__repr__** (`method`, line 62, `src/cubedynamics/piping.py`) — Return the repr of the wrapped value for plain-text displays.
- **cubedynamics.piping.Pipe._repr_html_** (`method`, line 67, `src/cubedynamics/piping.py`) — Rich HTML representation for Jupyter notebooks.
- **cubedynamics.piping.Pipe.unwrap** (`method`, line 57, `src/cubedynamics/piping.py`) — Return the wrapped value, ending the pipe chain.
- **cubedynamics.piping.Pipe.v** (`method`, line 81, `src/cubedynamics/piping.py`) — Convenience alias for :pyattr:`value`.
- **cubedynamics.piping.Verb** (`class`, line 27, `src/cubedynamics/piping.py`) — Wrapper for callables used in pipe chains.
- **cubedynamics.piping.Verb.__call__** (`method`, line 33, `src/cubedynamics/piping.py`) —
- **cubedynamics.piping.Verb.__init__** (`method`, line 30, `src/cubedynamics/piping.py`) —
- **cubedynamics.piping._attach_viewer** (`function`, line 14, `src/cubedynamics/piping.py`) —
- **cubedynamics.piping.pipe** (`function`, line 87, `src/cubedynamics/piping.py`) — Wrap ``value`` in a :class:`Pipe`, enabling ``Pipe | op(...)`` syntax.

**cubedynamics.plotting.cube_plot** — Grammar-of-graphics + streaming core for cube plotting.
- **cubedynamics.plotting.cube_plot.CoordCube** (`class`, line 249, `src/cubedynamics/plotting/cube_plot.py`) — Camera/coordinate configuration for cube plots.
- **cubedynamics.plotting.cube_plot.CubeAes** (`class`, line 85, `src/cubedynamics/plotting/cube_plot.py`) — Aesthetic mapping for cube plots.
- **cubedynamics.plotting.cube_plot.CubeAnnotation** (`class`, line 262, `src/cubedynamics/plotting/cube_plot.py`) — Simple annotation container for planes/text anchored to cube axes.
- **cubedynamics.plotting.cube_plot.CubeFacet** (`class`, line 101, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubeLayer** (`class`, line 117, `src/cubedynamics/plotting/cube_plot.py`) — A plotting layer pairing a geom with data and stat.
- **cubedynamics.plotting.cube_plot.CubePlot** (`class`, line 428, `src/cubedynamics/plotting/cube_plot.py`) — Internal object model for cube visualizations.
- **cubedynamics.plotting.cube_plot.CubePlot.__post_init__** (`method`, line 470, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot._build_axis_meta** (`method`, line 500, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot._build_axis_meta._entry** (`method`, line 501, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot._repr_html_** (`method`, line 917, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot._resolve_dims** (`method`, line 492, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.add_layer** (`method`, line 601, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.annot_plane** (`method`, line 593, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.annot_text** (`method`, line 597, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.coord_cube** (`method`, line 575, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.facet_grid** (`method`, line 585, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.facet_wrap** (`method`, line 581, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.geom_cube** (`method`, line 605, `src/cubedynamics/plotting/cube_plot.py`) — Explicitly add a cube geometry layer.
- **cubedynamics.plotting.cube_plot.CubePlot.geom_vase_outline** (`method`, line 656, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.save** (`method`, line 893, `src/cubedynamics/plotting/cube_plot.py`) — Save the cube figure to disk.
- **cubedynamics.plotting.cube_plot.CubePlot.scale_alpha_continuous** (`method`, line 571, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.scale_fill_continuous** (`method`, line 567, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.stat_vase** (`method`, line 610, `src/cubedynamics/plotting/cube_plot.py`) — Attach a vase mask and masked cube to this plot via ``StatVase``.
- **cubedynamics.plotting.cube_plot.CubePlot.theme_cube_studio** (`method`, line 589, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.to_html** (`method`, line 662, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.to_html._annot_block** (`method`, line 674, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.to_html._apply_stat** (`method`, line 667, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.to_html._panel_label** (`method`, line 692, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.to_html._render_viewer** (`method`, line 697, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubePlot.to_html._unique_values** (`method`, line 803, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.CubeTheme** (`class`, line 48, `src/cubedynamics/plotting/cube_plot.py`) — Theme configuration for cube plots.
- **cubedynamics.plotting.cube_plot.ScaleAlphaContinuous** (`class`, line 242, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.ScaleFillContinuous** (`class`, line 149, `src/cubedynamics/plotting/cube_plot.py`) — Continuous color scale used by the cube viewer.
- **cubedynamics.plotting.cube_plot.ScaleFillContinuous._default_cmap** (`method`, line 165, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.ScaleFillContinuous.infer_breaks** (`method`, line 233, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.ScaleFillContinuous.infer_limits** (`method`, line 175, `src/cubedynamics/plotting/cube_plot.py`) — Infer limits for continuous fill scales.
- **cubedynamics.plotting.cube_plot.ScaleFillContinuous.resolved_cmap** (`method`, line 172, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._CubePlotMeta** (`class`, line 37, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._CubePlotMeta.__instancecheck__** (`method`, line 38, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._build_caption** (`function`, line 320, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._derive_legend_title** (`function`, line 309, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_lat** (`function`, line 348, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_lon** (`function`, line 357, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_numeric** (`function`, line 366, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._format_time_label** (`function`, line 340, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._infer_aes_from_data** (`function`, line 108, `src/cubedynamics/plotting/cube_plot.py`) — Infer a simple aesthetic mapping from a DataArray.
- **cubedynamics.plotting.cube_plot._looks_like_lat** (`function`, line 373, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot._looks_like_lon** (`function`, line 400, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_cube** (`function`, line 132, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_outline** (`function`, line 140, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_path3d** (`function`, line 144, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.geom_slice** (`function`, line 136, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_identity** (`function`, line 271, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_space_mean** (`function`, line 293, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_time_anomaly** (`function`, line 282, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.stat_time_mean** (`function`, line 275, `src/cubedynamics/plotting/cube_plot.py`) —
- **cubedynamics.plotting.cube_plot.theme_cube_studio** (`function`, line 78, `src/cubedynamics/plotting/cube_plot.py`) — Return the default "studio" theme.

**cubedynamics.plotting.cube_viewer** —
- **cubedynamics.plotting.cube_viewer._apply_vase_tint** (`function`, line 79, `src/cubedynamics/plotting/cube_viewer.py`) — Apply an overlay color to ``rgb_arr`` wherever ``mask_2d`` is True.
- **cubedynamics.plotting.cube_viewer._array_to_png_base64** (`function`, line 117, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._axis_range_from_ticks** (`function`, line 1198, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._build_legend_html** (`function`, line 136, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._colorbar_labels** (`function`, line 124, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._colormap_to_rgba** (`function`, line 97, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._guess_axis_name** (`function`, line 1166, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._infer_axis_ticks** (`function`, line 1175, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._interior_plane_transform** (`function`, line 158, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._reduce_to_3d_time_y_x** (`function`, line 36, `src/cubedynamics/plotting/cube_viewer.py`) — Ensure the DataArray has dims (time, y, x) for the cube viewer.
- **cubedynamics.plotting.cube_viewer._render_cube_html** (`function`, line 194, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._rgba_to_png_base64** (`function`, line 111, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._vase_panel_transform** (`function`, line 178, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer._vase_panel_transform._offset** (`method`, line 181, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer.cube_from_dataarray** (`function`, line 777, `src/cubedynamics/plotting/cube_viewer.py`) —
- **cubedynamics.plotting.cube_viewer.cube_from_dataarray._face_to_png** (`method`, line 976, `src/cubedynamics/plotting/cube_viewer.py`) —

**cubedynamics.plotting.geom** —
- **cubedynamics.plotting.geom.GeomVaseOutline** (`class`, line 5, `src/cubedynamics/plotting/geom.py`) — Grammar-of-graphics geom that indicates vase overlays should be applied

**cubedynamics.plotting.progress** — Notebook-friendly progress helpers for cube rendering.
- **cubedynamics.plotting.progress._CubeProgress** (`class`, line 8, `src/cubedynamics/plotting/progress.py`) — Simple progress helper that prints inline status updates.
- **cubedynamics.plotting.progress._CubeProgress.__init__** (`method`, line 11, `src/cubedynamics/plotting/progress.py`) —
- **cubedynamics.plotting.progress._CubeProgress._render** (`method`, line 20, `src/cubedynamics/plotting/progress.py`) —
- **cubedynamics.plotting.progress._CubeProgress.done** (`method`, line 35, `src/cubedynamics/plotting/progress.py`) —
- **cubedynamics.plotting.progress._CubeProgress.step** (`method`, line 28, `src/cubedynamics/plotting/progress.py`) —

**cubedynamics.plotting.stats** —
- **cubedynamics.plotting.stats.StatVase** (`class`, line 11, `src/cubedynamics/plotting/stats.py`) —
- **cubedynamics.plotting.stats.StatVase.compute** (`method`, line 17, `src/cubedynamics/plotting/stats.py`) — Return ``(masked_cube, mask)`` without triggering full cube load.

**cubedynamics.plotting.viewer** — Utilities for rendering the cube viewer safely inside notebooks.
- **cubedynamics.plotting.viewer._write_cube_html** (`function`, line 12, `src/cubedynamics/plotting/viewer.py`) — Write a standalone cube viewer HTML file to the working directory.
- **cubedynamics.plotting.viewer.show_cube_viewer** (`function`, line 22, `src/cubedynamics/plotting/viewer.py`) — Return an IFrame pointing at a self-contained cube viewer file.

**cubedynamics.prism_streaming** — Streaming-first helpers for PRISM datasets.
- **cubedynamics.prism_streaming.stream_prism_to_cube** (`function`, line 15, `src/cubedynamics/prism_streaming.py`) — Stream PRISM data into an xarray object.

**cubedynamics.progress** — Lightweight progress bar utilities.
- **cubedynamics.progress.progress_bar** (`function`, line 20, `src/cubedynamics/progress.py`) — Context manager that yields an ``advance(n)`` function.

**cubedynamics.sentinel** — Sentinel-2 helper utilities for CubeDynamics.
- **cubedynamics.sentinel._resolve_lat_lon_and_edge_size** (`function`, line 223, `src/cubedynamics/sentinel.py`) — Return a valid ``lat``, ``lon``, and ``edge_size`` for Sentinel-2 requests.
- **cubedynamics.sentinel.load_sentinel2_bands_cube** (`function`, line 87, `src/cubedynamics/sentinel.py`) — Stream a Sentinel-2 L2A cube for a user-selected list of bands.
- **cubedynamics.sentinel.load_sentinel2_cube** (`function`, line 18, `src/cubedynamics/sentinel.py`) — Stream a Sentinel-2 L2A cube via ``cubo``.
- **cubedynamics.sentinel.load_sentinel2_ndvi_cube** (`function`, line 126, `src/cubedynamics/sentinel.py`) — Stream Sentinel-2 L2A data and compute a raw NDVI cube.
- **cubedynamics.sentinel.load_sentinel2_ndvi_zscore_cube** (`function`, line 172, `src/cubedynamics/sentinel.py`) — Convenience wrapper that returns a z-scored Sentinel-2 NDVI cube.

**cubedynamics.stats.anomalies** — Anomaly and z-score utilities.
- **cubedynamics.stats.anomalies.rolling_mean** (`function`, line 68, `src/cubedynamics/stats/anomalies.py`) — Compute a simple rolling mean along a time-like dimension.
- **cubedynamics.stats.anomalies.temporal_anomaly** (`function`, line 33, `src/cubedynamics/stats/anomalies.py`) — Compute anomalies relative to a baseline mean over a time-like dimension.
- **cubedynamics.stats.anomalies.temporal_difference** (`function`, line 52, `src/cubedynamics/stats/anomalies.py`) — Compute lagged differences along a time-like dimension.
- **cubedynamics.stats.anomalies.zscore_over_time** (`function`, line 15, `src/cubedynamics/stats/anomalies.py`) — Deprecated helper that forwards to :func:`cubedynamics.ops.stats.zscore`.

**cubedynamics.stats.correlation** — Correlation helpers.
- **cubedynamics.stats.correlation.pearson_corr_stat** (`function`, line 12, `src/cubedynamics/stats/correlation.py`) — Compute Pearson correlation between two 1D arrays.
- **cubedynamics.stats.correlation.rolling_corr_vs_center** (`function`, line 28, `src/cubedynamics/stats/correlation.py`) — Build a rolling-window correlation cube vs the center pixel.

**cubedynamics.stats.rolling** — Rolling-window computation utilities.
- **cubedynamics.stats.rolling._empty_result** (`function`, line 13, `src/cubedynamics/stats/rolling.py`) —
- **cubedynamics.stats.rolling.rolling_pairwise_stat_cube** (`function`, line 18, `src/cubedynamics/stats/rolling.py`) — Compute a rolling-window pairwise statistic vs a reference time series.

**cubedynamics.stats.spatial** — Spatial cube math primitives.
- **cubedynamics.stats.spatial.mask_by_threshold** (`function`, line 45, `src/cubedynamics/stats/spatial.py`) — Create a boolean mask for values that satisfy a threshold condition.
- **cubedynamics.stats.spatial.spatial_coarsen_mean** (`function`, line 12, `src/cubedynamics/stats/spatial.py`) — Coarsen a DataArray by averaging blocks in the spatial dimensions.
- **cubedynamics.stats.spatial.spatial_smooth_mean** (`function`, line 28, `src/cubedynamics/stats/spatial.py`) — Apply a boxcar spatial mean filter over the y/x dimensions.

**cubedynamics.stats.tails** — Tail dependence utilities.
- **cubedynamics.stats.tails._rank_1d** (`function`, line 13, `src/cubedynamics/stats/tails.py`) — Simple 1D rank function (1..n) with ordinal tie handling.
- **cubedynamics.stats.tails.partial_tail_spearman** (`function`, line 22, `src/cubedynamics/stats/tails.py`) — Partial Spearman correlations in lower and upper tails.
- **cubedynamics.stats.tails.partial_tail_spearman._tail_corr** (`method`, line 51, `src/cubedynamics/stats/tails.py`) —
- **cubedynamics.stats.tails.rolling_tail_dep_vs_center** (`function`, line 64, `src/cubedynamics/stats/tails.py`) — Build rolling-window tail-dependence cubes vs the center pixel.

**cubedynamics.streaming.gridmet** —
- **cubedynamics.streaming.gridmet._axis_slice** (`function`, line 18, `src/cubedynamics/streaming/gridmet.py`) — Return a slice that spans ``[bound_a, bound_b]`` regardless of axis order.
- **cubedynamics.streaming.gridmet._bbox_from_geojson** (`function`, line 97, `src/cubedynamics/streaming/gridmet.py`) — Compute a simple lat/lon bounding box from a GeoJSON polygon (EPSG:4326).
- **cubedynamics.streaming.gridmet._lat_slice** (`function`, line 53, `src/cubedynamics/streaming/gridmet.py`) — Return a latitude slice that works for ascending or descending axes.
- **cubedynamics.streaming.gridmet._lon_slice** (`function`, line 59, `src/cubedynamics/streaming/gridmet.py`) — Return a longitude slice that works for ascending or descending axes.
- **cubedynamics.streaming.gridmet._open_gridmet_year** (`function`, line 114, `src/cubedynamics/streaming/gridmet.py`) — Download a single gridMET year fully in memory and open it with the best
- **cubedynamics.streaming.gridmet._prepare_stream_target** (`function`, line 77, `src/cubedynamics/streaming/gridmet.py`) — Return an object suitable for xr.open_dataset for the chosen engine.
- **cubedynamics.streaming.gridmet._select_stream_engine** (`function`, line 65, `src/cubedynamics/streaming/gridmet.py`) — Pick the best available xarray engine for streaming gridMET files.
- **cubedynamics.streaming.gridmet.stream_gridmet_to_cube** (`function`, line 168, `src/cubedynamics/streaming/gridmet.py`) — Stream a gridMET subset as an xarray.DataArray "cube" for a given AOI.

**cubedynamics.streaming.virtual** — Virtual cube streaming helpers.
- **cubedynamics.streaming.virtual.VirtualCube** (`class`, line 20, `src/cubedynamics/streaming/virtual.py`) — Representation of a lazily tiled cube.
- **cubedynamics.streaming.virtual.VirtualCube.iter_spatial_tiles** (`method`, line 55, `src/cubedynamics/streaming/virtual.py`) — Iterate over cubes tiled in space (full time range per tile).
- **cubedynamics.streaming.virtual.VirtualCube.iter_tiles** (`method`, line 62, `src/cubedynamics/streaming/virtual.py`) — Iterate over time × space tiles produced by both tilers.
- **cubedynamics.streaming.virtual.VirtualCube.iter_time_tiles** (`method`, line 48, `src/cubedynamics/streaming/virtual.py`) — Iterate over time-tiled cubes (full spatial AOI per tile).
- **cubedynamics.streaming.virtual.VirtualCube.materialize** (`method`, line 78, `src/cubedynamics/streaming/virtual.py`) — Materialize the virtual cube as a single :class:`xarray.DataArray`.
- **cubedynamics.streaming.virtual.make_spatial_tiler** (`function`, line 123, `src/cubedynamics/streaming/virtual.py`) — Create a deterministic spatial tiler for a bounding box.
- **cubedynamics.streaming.virtual.make_spatial_tiler.tiler** (`method`, line 130, `src/cubedynamics/streaming/virtual.py`) —
- **cubedynamics.streaming.virtual.make_time_tiler** (`function`, line 94, `src/cubedynamics/streaming/virtual.py`) — Create a deterministic time tiler.
- **cubedynamics.streaming.virtual.make_time_tiler.tiler** (`method`, line 102, `src/cubedynamics/streaming/virtual.py`) —

**cubedynamics.tests.test_gridmet_streaming** — Tests for the gridMET streaming helper.
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_bbox_padding** (`function`, line 103, `src/cubedynamics/tests/test_gridmet_streaming.py`) — Tiny AOI bounding boxes should still capture at least one grid cell.
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_bbox_padding._fake_year** (`method`, line 110, `src/cubedynamics/tests/test_gridmet_streaming.py`) —
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_default_source_smoke** (`function`, line 13, `src/cubedynamics/tests/test_gridmet_streaming.py`) — Calling the helper without `source` should return a time-indexed cube.
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_default_source_smoke._fake_year** (`method`, line 20, `src/cubedynamics/tests/test_gridmet_streaming.py`) —
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_descending_lat** (`function`, line 59, `src/cubedynamics/tests/test_gridmet_streaming.py`) — Descending latitude axes should still produce non-empty subsets.
- **cubedynamics.tests.test_gridmet_streaming.test_stream_gridmet_to_cube_descending_lat._fake_year** (`method`, line 66, `src/cubedynamics/tests/test_gridmet_streaming.py`) —

**cubedynamics.tests.test_import_and_pipe** — Basic import and pipe integration tests for cubedynamics.
- **cubedynamics.tests.test_import_and_pipe.test_import_cubedynamics_has_version** (`function`, line 10, `src/cubedynamics/tests/test_import_and_pipe.py`) — Ensure the package exposes a version attribute.
- **cubedynamics.tests.test_import_and_pipe.test_pipe_anomaly_variance_chain** (`function`, line 16, `src/cubedynamics/tests/test_import_and_pipe.py`) — Smoke-test chaining simple pipe verbs if available.

**cubedynamics.tests.test_imports** — Basic import smoke tests for the cubedynamics package.
- **cubedynamics.tests.test_imports.test_streaming_helpers_are_callable** (`function`, line 13, `src/cubedynamics/tests/test_imports.py`) — All public streaming helpers should be importable.
- **cubedynamics.tests.test_imports.test_streaming_stubs_raise_not_implemented** (`function`, line 24, `src/cubedynamics/tests/test_imports.py`) — Only the unimplemented helpers should raise NotImplementedError.
- **cubedynamics.tests.test_imports.test_version_exposed** (`function`, line 8, `src/cubedynamics/tests/test_imports.py`) — Ensure the package exposes a version string.

**cubedynamics.tests.test_piping_ops** — Tests for the ggplot-style pipe syntax and verbs.
- **cubedynamics.tests.test_piping_ops._make_time_series** (`function`, line 13, `src/cubedynamics/tests/test_piping_ops.py`) —
- **cubedynamics.tests.test_piping_ops.test_month_filter_reduces_time** (`function`, line 37, `src/cubedynamics/tests/test_piping_ops.py`) —
- **cubedynamics.tests.test_piping_ops.test_pipe_basic_chain** (`function`, line 23, `src/cubedynamics/tests/test_piping_ops.py`) —
- **cubedynamics.tests.test_piping_ops.test_show_cube_lexcube_returns_original_cube** (`function`, line 57, `src/cubedynamics/tests/test_piping_ops.py`) —
- **cubedynamics.tests.test_piping_ops.test_show_cube_lexcube_returns_original_cube.fake_show** (`method`, line 62, `src/cubedynamics/tests/test_piping_ops.py`) —
- **cubedynamics.tests.test_piping_ops.test_to_netcdf_roundtrip** (`function`, line 45, `src/cubedynamics/tests/test_piping_ops.py`) —

**cubedynamics.tests.test_progress** —
- **cubedynamics.tests.test_progress.test_ndvi_accepts_show_progress** (`function`, line 41, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_ndvi_accepts_show_progress._fake_loader** (`method`, line 42, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_progress_bar_updates_when_tqdm_available** (`function`, line 10, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_progress_bar_updates_when_tqdm_available.DummyTqdm** (`class`, line 11, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_progress_bar_updates_when_tqdm_available.DummyTqdm.__call__** (`method`, line 16, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_progress_bar_updates_when_tqdm_available.DummyTqdm.__enter__** (`method`, line 20, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_progress_bar_updates_when_tqdm_available.DummyTqdm.__exit__** (`method`, line 23, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_progress_bar_updates_when_tqdm_available.DummyTqdm.__init__** (`method`, line 12, `src/cubedynamics/tests/test_progress.py`) —
- **cubedynamics.tests.test_progress.test_progress_bar_updates_when_tqdm_available.DummyTqdm.update** (`method`, line 26, `src/cubedynamics/tests/test_progress.py`) —

**cubedynamics.tests.test_sentinel_bbox** —
- **cubedynamics.tests.test_sentinel_bbox.test_resolve_passthrough_when_lat_lon_provided** (`function`, line 31, `src/cubedynamics/tests/test_sentinel_bbox.py`) —
- **cubedynamics.tests.test_sentinel_bbox.test_resolve_requires_coordinates_or_bbox** (`function`, line 6, `src/cubedynamics/tests/test_sentinel_bbox.py`) —
- **cubedynamics.tests.test_sentinel_bbox.test_resolve_retains_edge_for_small_bbox** (`function`, line 21, `src/cubedynamics/tests/test_sentinel_bbox.py`) —
- **cubedynamics.tests.test_sentinel_bbox.test_resolve_uses_bbox_center_and_expands_edge** (`function`, line 11, `src/cubedynamics/tests/test_sentinel_bbox.py`) —

**cubedynamics.tests.test_streaming_contracts** — Streaming-first contract tests for cubedynamics.
- **cubedynamics.tests.test_streaming_contracts.test_streaming_functions_expose_chunks_argument** (`function`, line 19, `src/cubedynamics/tests/test_streaming_contracts.py`) — Every streaming helper must expose a ``chunks`` keyword.
- **cubedynamics.tests.test_streaming_contracts.test_streaming_stubs_raise_not_implemented** (`function`, line 30, `src/cubedynamics/tests/test_streaming_contracts.py`) — Until implemented, stub helpers should make their status clear.
- **cubedynamics.tests.test_streaming_contracts.test_stub_download_paths_are_opt_in** (`function`, line 39, `src/cubedynamics/tests/test_streaming_contracts.py`) — Stubs must still raise until real download behavior is implemented.

**cubedynamics.tubes** — Backend utilities for tube detection and analysis.
- **cubedynamics.tubes._connectivity_structure** (`function`, line 49, `src/cubedynamics/tubes.py`) —
- **cubedynamics.tubes._hull_to_polygon** (`function`, line 199, `src/cubedynamics/tubes.py`) —
- **cubedynamics.tubes.compute_suitability_from_ndvi** (`function`, line 22, `src/cubedynamics/tubes.py`) — Return a boolean mask marking suitability based on NDVI thresholds.
- **cubedynamics.tubes.compute_tube_metrics** (`function`, line 102, `src/cubedynamics/tubes.py`) — Compute per-tube metrics:
- **cubedynamics.tubes.label_tubes** (`function`, line 57, `src/cubedynamics/tubes.py`) — Label 3D connected components (tubes) in a boolean mask.
- **cubedynamics.tubes.tube_to_vase_definition** (`function`, line 216, `src/cubedynamics/tubes.py`) — Convert a single tube (tube_id) into a VaseDefinition.

**cubedynamics.utils.chunking** — Chunking and subsampling utilities.
- **cubedynamics.utils.chunking.coarsen_and_stride** (`function`, line 10, `src/cubedynamics/utils/chunking.py`) — Optionally coarsen spatially and subsample in time.

**cubedynamics.utils.cube_css** — Helpers for emitting lightweight CSS cube HTML scaffolding.
- **cubedynamics.utils.cube_css._axis_section** (`function`, line 38, `src/cubedynamics/utils/cube_css.py`) —
- **cubedynamics.utils.cube_css._colorbar_labels** (`function`, line 28, `src/cubedynamics/utils/cube_css.py`) —
- **cubedynamics.utils.cube_css._face_style** (`function`, line 19, `src/cubedynamics/utils/cube_css.py`) —
- **cubedynamics.utils.cube_css.write_css_cube_static** (`function`, line 60, `src/cubedynamics/utils/cube_css.py`) — Write a standalone HTML page with a simple CSS-based cube skeleton.

**cubedynamics.utils.dims** — Utilities for inferring canonical cube dimensions.
- **cubedynamics.utils.dims._infer_time_y_x_dims** (`function`, line 16, `src/cubedynamics/utils/dims.py`) — Infer time, y, and x dimension names from a cube-like object.

**cubedynamics.utils.drop_bad_assets** — Utilities for handling intermittent remote asset failures.
- **cubedynamics.utils.drop_bad_assets.drop_bad_assets** (`function`, line 25, `src/cubedynamics/utils/drop_bad_assets.py`) — Return a copy of ``cube`` with slices that raise errors removed.

**cubedynamics.utils.reference** — Reference pixel helpers.
- **cubedynamics.utils.reference.center_pixel_indices** (`function`, line 8, `src/cubedynamics/utils/reference.py`) — Return the (y_idx, x_idx) of the center pixel in a cube.
- **cubedynamics.utils.reference.center_pixel_series** (`function`, line 20, `src/cubedynamics/utils/reference.py`) — Extract the time series at the center pixel of a 3D cube.

**cubedynamics.variables** — Semantic variable loaders for common climate and vegetation variables.
- **cubedynamics.variables._load_temperature** (`function`, line 95, `src/cubedynamics/variables.py`) —
- **cubedynamics.variables._resolve_temp_variable** (`function`, line 84, `src/cubedynamics/variables.py`) —
- **cubedynamics.variables._year_chunks** (`function`, line 329, `src/cubedynamics/variables.py`) — Yield (start_str, end_str) for consecutive chunks of up to years_per_chunk.
- **cubedynamics.variables.estimate_cube_size** (`function`, line 43, `src/cubedynamics/variables.py`) — Return a rough scalar size estimate for a requested cube.
- **cubedynamics.variables.ndvi** (`function`, line 426, `src/cubedynamics/variables.py`) — Load a Sentinel-2 NDVI cube.
- **cubedynamics.variables.ndvi_chunked** (`function`, line 355, `src/cubedynamics/variables.py`) — Load a Sentinel-2 NDVI cube in time chunks and concatenate along 'time'.
- **cubedynamics.variables.temperature** (`function`, line 138, `src/cubedynamics/variables.py`) — Load a mean temperature cube from the chosen climate provider.
- **cubedynamics.variables.temperature.base_loader** (`method`, line 165, `src/cubedynamics/variables.py`) —
- **cubedynamics.variables.temperature_anomaly** (`function`, line 260, `src/cubedynamics/variables.py`) — Compute a temperature anomaly cube along the time dimension.
- **cubedynamics.variables.temperature_max** (`function`, line 234, `src/cubedynamics/variables.py`) — Load a maximum daily temperature cube from the selected source.
- **cubedynamics.variables.temperature_min** (`function`, line 208, `src/cubedynamics/variables.py`) — Load a minimum daily temperature cube from the selected source.

**cubedynamics.vase** — Time-varying vase polygons and masking utilities.
- **cubedynamics.vase.VaseDefinition** (`class`, line 42, `src/cubedynamics/vase.py`) — Collection of vase sections with interpolation rules.
- **cubedynamics.vase.VaseDefinition.__post_init__** (`method`, line 54, `src/cubedynamics/vase.py`) —
- **cubedynamics.vase.VaseDefinition.sorted_sections** (`method`, line 66, `src/cubedynamics/vase.py`) — Return a new VaseDefinition with sections sorted by time.
- **cubedynamics.vase.VasePanel** (`class`, line 74, `src/cubedynamics/vase.py`) — Rectangular patch approximating a vase hull segment.
- **cubedynamics.vase.VaseSection** (`class`, line 29, `src/cubedynamics/vase.py`) — Single cross-section of a vase at a given time.
- **cubedynamics.vase._normalize_value** (`function`, line 152, `src/cubedynamics/vase.py`) — Normalize ``value`` to [0, 1] between vmin and vmax, handling datetimes.
- **cubedynamics.vase._polygon_at_time** (`function`, line 88, `src/cubedynamics/vase.py`) — Return the polygon cross-section for a target time ``t``.
- **cubedynamics.vase._sample_polygon_boundary** (`function`, line 132, `src/cubedynamics/vase.py`) — Sample ``n_samples`` equally spaced points along the polygon boundary.
- **cubedynamics.vase._to_numeric_time** (`function`, line 142, `src/cubedynamics/vase.py`) — Convert datetime-like or numeric time to a float for normalization.
- **cubedynamics.vase.build_vase_mask** (`function`, line 230, `src/cubedynamics/vase.py`) — Build a boolean mask for voxels inside a time-varying vase.
- **cubedynamics.vase.build_vase_panels** (`function`, line 163, `src/cubedynamics/vase.py`) — Approximate the vase hull with rectangular panels.
- **cubedynamics.vase.extract_vase_from_attrs** (`function`, line 282, `src/cubedynamics/vase.py`) — Return the VaseDefinition attached to this DataArray, if any.

**cubedynamics.vase_viz** — Vase visualization utilities for scientific 3-D workflows.
- **cubedynamics.vase_viz._convert_time_to_numeric** (`function`, line 60, `src/cubedynamics/vase_viz.py`) —
- **cubedynamics.vase_viz._validate_dims** (`function`, line 15, `src/cubedynamics/vase_viz.py`) —
- **cubedynamics.vase_viz.extract_vase_points** (`function`, line 21, `src/cubedynamics/vase_viz.py`) — Extract coordinates and values for voxels where ``mask`` is ``True``.
- **cubedynamics.vase_viz.vase_scatter_plot** (`function`, line 66, `src/cubedynamics/vase_viz.py`) — 3-D scientific scatter plot of voxels inside the vase.
- **cubedynamics.vase_viz.vase_scatter_with_hull** (`function`, line 158, `src/cubedynamics/vase_viz.py`) — Overlay vase scatter points with a translucent hull mesh.
- **cubedynamics.vase_viz.vase_to_mesh** (`function`, line 120, `src/cubedynamics/vase_viz.py`) — Convert VaseDefinition into a 3-D mesh using a sweep (loft) of polygons.

**cubedynamics.verbs** — Namespace exposing pipe-friendly cube verbs.
- **cubedynamics.verbs._plot_time_hull_vase** (`function`, line 201, `src/cubedynamics/verbs/__init__.py`) — Render a TimeHull-derived vase using matplotlib.
- **cubedynamics.verbs._unwrap_dataarray** (`function`, line 40, `src/cubedynamics/verbs/__init__.py`) — Normalize a verb input to an (xarray.DataArray, original_obj) pair.
- **cubedynamics.verbs.climate_hist** (`function`, line 315, `src/cubedynamics/verbs/__init__.py`) — Plot histogram of climate inside vs outside fire perimeters.
- **cubedynamics.verbs.extract** (`function`, line 133, `src/cubedynamics/verbs/__init__.py`) — Verb: attach fire time-hull + climate summary (and a vase-like hull)
- **cubedynamics.verbs.extract._op** (`method`, line 171, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.fire_panel** (`function`, line 493, `src/cubedynamics/verbs/__init__.py`) — Convenience helper: fire time-hull + climate distribution "panel".
- **cubedynamics.verbs.fire_panel._inner** (`method`, line 526, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.fire_plot** (`function`, line 393, `src/cubedynamics/verbs/__init__.py`) — High-level convenience verb: fire time-hull × climate visualization.
- **cubedynamics.verbs.fire_plot._inner** (`method`, line 470, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.landsat8_mpc** (`function`, line 68, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for the Landsat MPC helper.
- **cubedynamics.verbs.landsat_ndvi_plot** (`function`, line 88, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for Landsat NDVI plotting.
- **cubedynamics.verbs.landsat_vis_ndvi** (`function`, line 80, `src/cubedynamics/verbs/__init__.py`) — Lazy import wrapper for a visualization-friendly Landsat NDVI cube.
- **cubedynamics.verbs.show_cube_lexcube** (`function`, line 96, `src/cubedynamics/verbs/__init__.py`) — Render a Lexcube widget as a side-effect and return the original cube.
- **cubedynamics.verbs.show_cube_lexcube._op** (`method`, line 104, `src/cubedynamics/verbs/__init__.py`) —
- **cubedynamics.verbs.vase** (`function`, line 274, `src/cubedynamics/verbs/__init__.py`) — High-level vase plotting verb with TimeHull support.
- **cubedynamics.verbs.vase._inner** (`method`, line 284, `src/cubedynamics/verbs/__init__.py`) —

**cubedynamics.verbs.custom** — Generic custom-function verbs.
- **cubedynamics.verbs.custom.apply** (`function`, line 10, `src/cubedynamics/verbs/custom.py`) — Return a verb that applies ``func`` to the incoming cube.
- **cubedynamics.verbs.custom.apply._op** (`method`, line 23, `src/cubedynamics/verbs/custom.py`) —

**cubedynamics.verbs.fire** —
- **cubedynamics.verbs.fire.fire_derivative** (`function`, line 167, `src/cubedynamics/verbs/fire.py`) — Fire derivative hull visualization verb.
- **cubedynamics.verbs.fire.fire_plot** (`function`, line 25, `src/cubedynamics/verbs/fire.py`) — Fire time-hull + climate visualization verb.

**cubedynamics.verbs.flatten** — Shape-changing verbs for flattening cubes.
- **cubedynamics.verbs.flatten.flatten_cube** (`function`, line 31, `src/cubedynamics/verbs/flatten.py`) — Flatten all non-time dimensions into a single ``sample`` dimension.
- **cubedynamics.verbs.flatten.flatten_cube._op** (`method`, line 40, `src/cubedynamics/verbs/flatten.py`) —
- **cubedynamics.verbs.flatten.flatten_space** (`function`, line 8, `src/cubedynamics/verbs/flatten.py`) — Flatten spatial dimensions (``y`` and ``x``) into a ``pixel`` dimension.
- **cubedynamics.verbs.flatten.flatten_space._op** (`method`, line 20, `src/cubedynamics/verbs/flatten.py`) —

**cubedynamics.verbs.landsat_mpc** — Landsat-8 streaming via Microsoft Planetary Computer (MPC).
- **cubedynamics.verbs.landsat_mpc._bounding_box_from_mask** (`function`, line 228, `src/cubedynamics/verbs/landsat_mpc.py`) — Return slices that crop to the non-NaN footprint of ``mask``.
- **cubedynamics.verbs.landsat_mpc._coarsen_if_needed** (`function`, line 248, `src/cubedynamics/verbs/landsat_mpc.py`) — Coarsen ``da`` along y/x so sizes do not exceed ``max_*``.
- **cubedynamics.verbs.landsat_mpc._compute_ndvi_from_stack** (`function`, line 204, `src/cubedynamics/verbs/landsat_mpc.py`) — Compute NDVI from a Landsat stack with a ``band`` dimension.
- **cubedynamics.verbs.landsat_mpc.landsat8_mpc** (`function`, line 155, `src/cubedynamics/verbs/landsat_mpc.py`) — Landsat 8 (MPC) streaming verb for cubedynamics.
- **cubedynamics.verbs.landsat_mpc.landsat8_mpc_stream** (`function`, line 62, `src/cubedynamics/verbs/landsat_mpc.py`) — Stream Landsat-8 Collection 2 Level-2 scenes from Microsoft Planetary Computer.
- **cubedynamics.verbs.landsat_mpc.landsat_ndvi_plot** (`function`, line 318, `src/cubedynamics/verbs/landsat_mpc.py`) — Load Landsat NDVI, downsample for visualization, and render the cube viewer.
- **cubedynamics.verbs.landsat_mpc.landsat_vis_ndvi** (`function`, line 263, `src/cubedynamics/verbs/landsat_mpc.py`) — Return a visualization-friendly Landsat NDVI cube.
- **cubedynamics.verbs.landsat_mpc.pipeable** (`function`, line 44, `src/cubedynamics/verbs/landsat_mpc.py`) — Decorator that makes a verb callable or pipe-friendly.
- **cubedynamics.verbs.landsat_mpc.pipeable._wrapper** (`method`, line 54, `src/cubedynamics/verbs/landsat_mpc.py`) —

**cubedynamics.verbs.models** — Stubs for future modeling verbs.
- **cubedynamics.verbs.models.fit_model** (`function`, line 6, `src/cubedynamics/verbs/models.py`) — Placeholder for upcoming modeling verbs.

**cubedynamics.verbs.plot** — Plotting verb for displaying cubes via :class:`CubePlot`.
- **cubedynamics.verbs.plot.PlotOptions** (`class`, line 25, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 38, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 55, `src/cubedynamics/verbs/plot.py`) —
- **cubedynamics.verbs.plot.plot** (`function`, line 70, `src/cubedynamics/verbs/plot.py`) — Plot a cube or return a plotting verb.
- **cubedynamics.verbs.plot.plot._plot** (`method`, line 103, `src/cubedynamics/verbs/plot.py`) —

**cubedynamics.verbs.plot_mean** — Verb for plotting mean and variance cubes side-by-side.
- **cubedynamics.verbs.plot_mean._materialize_if_virtual** (`function`, line 15, `src/cubedynamics/verbs/plot_mean.py`) —
- **cubedynamics.verbs.plot_mean.plot_mean** (`function`, line 21, `src/cubedynamics/verbs/plot_mean.py`) — Plot mean and variance cubes with synchronized controls.
- **cubedynamics.verbs.plot_mean.plot_mean._op** (`method`, line 34, `src/cubedynamics/verbs/plot_mean.py`) —

**cubedynamics.verbs.stats** — Statistical cube verbs with consistent cube->cube semantics.
- **cubedynamics.verbs.stats._broadcast_like** (`function`, line 43, `src/cubedynamics/verbs/stats.py`) — Broadcast ``stat`` so it can be combined elementwise with ``obj``.
- **cubedynamics.verbs.stats._ensure_dim** (`function`, line 14, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._expand_dim** (`function`, line 27, `src/cubedynamics/verbs/stats.py`) — Return ``reduced`` with ``dim`` added back as a length-1 dimension.
- **cubedynamics.verbs.stats._mean_virtual_space** (`function`, line 220, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._mean_virtual_time** (`function`, line 142, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._variance_virtual_space** (`function`, line 180, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats._variance_virtual_time** (`function`, line 98, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.anomaly** (`function`, line 247, `src/cubedynamics/verbs/stats.py`) — Return a pipe verb that subtracts the mean over ``dim``.
- **cubedynamics.verbs.stats.anomaly._op** (`method`, line 254, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.mean** (`function`, line 52, `src/cubedynamics/verbs/stats.py`) — Return a pipe-ready reducer computing the mean along ``dim``.
- **cubedynamics.verbs.stats.mean._op** (`method`, line 60, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.rolling_tail_dep_vs_center** (`function`, line 315, `src/cubedynamics/verbs/stats.py`) — Return a rolling "tail dependence vs center" contrast along ``dim``.
- **cubedynamics.verbs.stats.rolling_tail_dep_vs_center._op** (`method`, line 340, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.variance** (`function`, line 75, `src/cubedynamics/verbs/stats.py`) — Return a variance reducer along ``dim`` with optional dimension retention.
- **cubedynamics.verbs.stats.variance._op** (`method`, line 90, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.variance._variance_virtual_cube** (`method`, line 83, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.variance._variance_xarray** (`method`, line 78, `src/cubedynamics/verbs/stats.py`) —
- **cubedynamics.verbs.stats.zscore** (`function`, line 263, `src/cubedynamics/verbs/stats.py`) — Return a standardized anomaly verb (z-score) along ``dim``.
- **cubedynamics.verbs.stats.zscore._op** (`method`, line 277, `src/cubedynamics/verbs/stats.py`) —

**cubedynamics.verbs.tubes** —
- **cubedynamics.verbs.tubes.tubes** (`function`, line 11, `src/cubedynamics/verbs/tubes.py`) — High-level verb: find suitability tubes and plot one as a vase.
- **cubedynamics.verbs.tubes.tubes._inner** (`method`, line 40, `src/cubedynamics/verbs/tubes.py`) —

**cubedynamics.verbs.vase** —
- **cubedynamics.verbs.vase.vase** (`function`, line 67, `src/cubedynamics/verbs/vase.py`) — High-level vase plotting verb.
- **cubedynamics.verbs.vase.vase._inner** (`method`, line 91, `src/cubedynamics/verbs/vase.py`) —
- **cubedynamics.verbs.vase.vase_demo** (`function`, line 151, `src/cubedynamics/verbs/vase.py`) — Convenience verb: build a demo stacked-polygon vase and plot it.
- **cubedynamics.verbs.vase.vase_demo._inner** (`method`, line 190, `src/cubedynamics/verbs/vase.py`) —
- **cubedynamics.verbs.vase.vase_extract** (`function`, line 36, `src/cubedynamics/verbs/vase.py`) — Mask a cube so that values outside the vase become ``NaN``.
- **cubedynamics.verbs.vase.vase_mask** (`function`, line 12, `src/cubedynamics/verbs/vase.py`) — Compute a boolean vase mask for a time-varying polygon hull.

**cubedynamics.viewers.cube_viewer** —
- **cubedynamics.viewers.cube_viewer._extract_faces** (`function`, line 74, `src/cubedynamics/viewers/cube_viewer.py`) — Extract cube faces for top (time slice), front (x slice), and side (y slice).
- **cubedynamics.viewers.cube_viewer._face_to_base64** (`function`, line 85, `src/cubedynamics/viewers/cube_viewer.py`) — Convert a 2D array face to a base64-encoded PNG using a matplotlib colormap.
- **cubedynamics.viewers.cube_viewer._infer_dims** (`function`, line 15, `src/cubedynamics/viewers/cube_viewer.py`) — Infer time, y, x dims for a 3D DataArray.
- **cubedynamics.viewers.cube_viewer.write_cube_viewer** (`function`, line 102, `src/cubedynamics/viewers/cube_viewer.py`) — Generate a standalone HTML/JS cube viewer for a 3D DataArray.

**cubedynamics.viewers.simple_plot** —
- **cubedynamics.viewers.simple_plot._infer_dims** (`function`, line 11, `src/cubedynamics/viewers/simple_plot.py`) — Infer time, y, x dim names for a 3D cube.
- **cubedynamics.viewers.simple_plot.simple_cube_widget** (`function`, line 56, `src/cubedynamics/viewers/simple_plot.py`) — Minimal interactive viewer for a 3D cube (time, y, x).
- **cubedynamics.viewers.simple_plot.simple_cube_widget._on_slider_change** (`method`, line 149, `src/cubedynamics/viewers/simple_plot.py`) —
- **cubedynamics.viewers.simple_plot.simple_cube_widget._plot_slice** (`method`, line 127, `src/cubedynamics/viewers/simple_plot.py`) —
- **cubedynamics.viewers.simple_plot.simple_cube_widget._update_label** (`method`, line 124, `src/cubedynamics/viewers/simple_plot.py`) —

**cubedynamics.viz.lexcube_viz** — Lexcube visualization helpers.
- **cubedynamics.viz.lexcube_viz.show_cube_lexcube** (`function`, line 15, `src/cubedynamics/viz/lexcube_viz.py`) — Create a Lexcube Cube3DWidget from a 3D cube (time, y, x).

**cubedynamics.viz.qa_plots** — Quality-assurance plotting helpers.
- **cubedynamics.viz.qa_plots.plot_median_over_space** (`function`, line 9, `src/cubedynamics/viz/qa_plots.py`) — Plot the median over space of a 3D cube as a time series.

## Section 6: Notes / anomalies
- cubedynamics.tests.test_imports.test_streaming_stubs_raise_not_implemented marked as not implemented.
