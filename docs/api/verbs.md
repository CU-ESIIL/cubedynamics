# Verbs API
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

CubeDynamics verbs are pipe-friendly helpers that operate on cubes (xarray
DataArray, Dataset, or VirtualCube). Verbs return a callable; use
``pipe(cube) | v.<verb>(...)`` to apply.

## Reduce verbs

### ``mean(dim="time", keep_dim=True, skipna=True)``
Compute the mean along ``dim`` while keeping attributes. Supports VirtualCube
streaming for time and space aggregation.

### ``variance(dim="time", keep_dim=True, skipna=True)``
Variance reducer mirroring ``mean`` semantics, including streaming paths for
VirtualCube inputs.

### ``rolling_tail_dep_vs_center(dim="time", window=14, ...)``
Tail dependence metric against the center pixel over a rolling window. Returns a
cube with a ``tail_dep`` variable; accepts the same dimension metadata as
:mod:`cubedynamics.config`.

### ``rolling_median_split_synchrony(window_days=90, ...)``
Compute rolling Spearman synchrony below and above per-series quantiles against
the center pixel. A DataArray supplies both sets; Dataset inputs may select
different variables with ``lower_var`` and ``upper_var``. Returns
``bottom_synchrony``, ``top_synchrony``, and ``bottom_minus_top`` variables.

Use this for climate synchrony workflows where the lower half and upper half of
the climate record should be treated separately. A common temperature pattern is
to use daily minimum temperature for the below-median set and daily maximum
temperature for the above-median set:

```python
sync = pipe(prism_temperature) | v.rolling_median_split_synchrony(
    lower_var="tmin",
    upper_var="tmax",
    split_quantile=0.5,
    window_days=90,
    output_stride=30,
)
```

The verb is designed for bounded streaming batches via ``output_times`` or
``output_stride`` rather than building a single enormous global graph.

## Block comparison verbs

Blocks are named local cube footprints: AOIs, grid tiles, ecological regions,
sample neighborhoods, or any other spatial unit that should become one
comparable time signature.

### ``block_signature(block_id, variables=None, reducer="median", ...)``
Summarize a local cube into a named block time series. Spatial dimensions are
reduced with the requested reducer while the time axis is preserved. The result
has a length-one ``block`` dimension so many blocks can be concatenated safely.

```python
boulder = pipe(boulder_sync) | v.block_signature(
    block_id="boulder",
    reducer="median",
)
```

### ``collect_blocks(*others, join="inner", ...)``
Combine block signatures into one block collection. The collection keeps block
identity as a coordinate and aligns time using xarray concat semantics.

```python
block_group = pipe(boulder) | v.collect_blocks(desert, plains)
```

### ``compare_blocks(method="pearson", ...)``
Compare all unique pairs in a block collection. The result includes
``pearson_r``, ``mean_difference``, ``rmse``, and ``n`` with ``left_block`` and
``right_block`` coordinates for each pair.

```python
pairwise = pipe(block_group) | v.compare_blocks()
```

Compatibility names ``aoi_signature`` and ``compare_aoi_signature`` remain
available for older notebooks, but new spatial workflows should prefer block
language.

## Transform verbs

### ``anomaly(dim="time", keep_dim=True)``
Subtract the mean over ``dim``. Preserves attributes and supports VirtualCube
materialization paths.

### ``zscore(dim="time", keep_dim=True, skipna=True)``
Normalize by subtracting the mean and dividing by the standard deviation along
``dim``. For VirtualCube inputs the verb computes streaming means/variances and
renames outputs with a ``_zscore`` suffix when possible.

### ``month_filter(months)``
Filter calendar months out of the ``time`` dimension. Typically used as
``pipe(cube) | v.month_filter([6, 7, 8])`` to keep boreal-summer slices.

## Shape verbs

### ``flatten_space()``
Reshape a cube from ``(time, y, x)`` to ``(time, space)`` while tracking spatial
coordinates.

### ``flatten_cube()``
Flatten a cube to a long table suitable for modeling; preserves variable and
coordinate metadata.

## Event / fire / vase verbs

### ``extract(fired_event, ...)``
Attach fire time-hull geometry, climate samples, and derived vase metadata to a
cube. Returns the original type (DataArray or VirtualCube) with attrs populated.

### ``vase(fired_event, ...)`` and ``vase_extract(...)``
Wrap fire time-hull geometry into :class:`cubedynamics.vase.VaseDefinition`
objects for downstream plotting or masking. ``vase_extract`` returns the
constructed vase alongside the input cube.

### ``vase_demo(...)``
Build a synthetic vase/time-hull for demos.

### ``vase_mask(...)``
Return a boolean mask marking voxels inside the vase.

### ``tubes(...)``
Identify connected components ("tubes") in suitability masks and return per-tube
metrics.

### ``climate_hist(...)``
Plot inside/outside climate distributions for a fire event; side-effecting
viewer verb.

### ``fire_plot(...)``
High-level fire workflow that returns event/hull/summary outputs and a Plotly-based interactive hull figure (`fig_hull`).

### ``fire_panel(...)``
Compact panel combining time-hull outlines and climate histograms.

### ``fire_vase_panel(...)``
Build a multi-event Plotly panel of fire VASEs for prescribed burns. The
single-event ``fire_plot`` workflow remains unchanged; ``fire_vase_panel``
selects prescribed events from ``fired_events`` or explicit ``event_ids``, runs
the same per-event VASE workflow, and returns ``fig_panel`` plus records,
results, and failures.

Pipe-first:

```python
pipe(climate_cube) | v.fire_vase_panel(
    fired_daily=fired_daily,
    fired_events=fired_events,
    prescribed_column="fire_type",
)
```

Per-event climate loading:

```python
panel = v.fire_vase_panel(
    fired_daily=fired_daily,
    fired_events=fired_events,
    prescribed_column="fire_type",
    load_climate=True,
    climate_variable="tmmx",
)
```

## Plotting verbs

### ``plot(**kwargs)``
Render a cube in the interactive HTML viewer. Returns the incoming cube while
attaching the viewer as ``_cd_last_viewer`` so pipes can continue.

### ``plot_mean(dim="time", ...)``
Display mean and variance cubes side by side using :class:`CubePlot`. Accepts
``dim`` (default ``time``) and forwards additional keywords to the renderer.

### ``show_cube_lexcube(**kwargs)``
Render a Lexcube widget as a side effect and return the original cube. Validates
that the cube has ``(time, y, x)`` ordering.

## End-to-end example

Load NDVI via the convenience variable helper and plot with a pipe:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.variables.ndvi(lat=37.7, lon=-122.5, start="2020-06-01", end="2020-06-15")
pipe(cube) | v.anomaly(dim="time") | v.plot(title="NDVI anomaly")
```
