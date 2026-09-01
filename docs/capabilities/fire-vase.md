# Fire VASE / FireHull

CubeDynamics treats FIRED fire events as spatiotemporal objects, not just a list of polygons or a one-off plot. The fire/VASE workflow turns daily perimeters into a time-stacked hull that can participate in the same cube-centered grammar used elsewhere in the library.

For the current manuscript-scale analysis, Fire VASE is also used as a
population data product: 278,569 real FIRED events are converted into
developmental profiles, placed in a shared morphospace, and attributed with
daily gridMET climate. See
[Fire VASE developmental morphology](../workflows/fire_vase_developmental_morphology.md)
for the full analysis pipeline, tables, figures, and manuscript outputs.

## Core objects

### `FireEventDaily`

`FireEventDaily` is the canonical daily fire event object.

It stores:

- `event_id`
- `gdf` with daily perimeter geometry
- `t0` / `t1`
- `centroid_lat` / `centroid_lon`

Useful entry points:

```python
from cubedynamics.fire_time_hull import FireEventDaily

event = FireEventDaily.from_fired(fired_daily, event_id=12345)
```

### `FireHull`

`FireHull` is the canonical fire-time hull / VASE object.

It stores triangulated geometry and time metadata:

- `verts_km`
- `tris`
- `t_days_vert`
- `t_norm_vert`
- `metrics`

It exposes object methods aligned with CubeDynamics design principles:

```python
hull = event.to_hull()
hull.metrics()
hull.to_mesh()
hull.to_cube(template_cube)
hull.attach_environment(cube, variables=["vpd"])
hull.plot(color="vpd")
```

`hull.plot()` without climate renders geometry colored by elapsed event day,
which is useful for inspecting the event object itself and does not fabricate
environmental measurements. Use `attach_environment(...)` followed by
`plot(color=...)` for climate-colored interpretation.

The event and climate time ranges must overlap. A mismatch is rejected with
both ranges in the error; CubeDynamics does not substitute or extrapolate
climate values. One Dataset can attach the documented climate variables
`temperature`, `precipitation`, `vpd`, `wind`, `humidity`, and `radiation`
when those named fields are present.

`TimeHull` remains available as a compatibility alias, but `FireHull` is the preferred public name going forward.

The [real FIRED event and climate recipe](../recipes/fire_event_vase_hull.md)
shows the complete data-loading and hull workflow. The publication site does
not substitute generated perimeters when FIRED or climate access fails.

## Interactive example

This embedded Plotly VASE uses a real FIRED event paired with streamed gridMET
maximum temperature. Rotate the hull to inspect how the event footprint changes
through time and how daily temperature bands are painted across the surface.

<div class="interactive-embed">
  <iframe
    src="/cubedynamics/assets/figures/fire_vase_gridmet_interactive.html"
    title="Interactive fire VASE with gridMET temperature"
    loading="lazy"
  ></iframe>
  <p class="interactive-embed__fallback">
    If the interactive VASE doesn’t load,
    <a href="/cubedynamics/assets/figures/fire_vase_gridmet_interactive.html" target="_blank" rel="noopener">open it in a new tab</a>.
  </p>
</div>

Recreate the embedded output locally:

```bash
python examples/real_fire_vase_gridmet_smoke.py \
  --output-dir artifacts/fire-vase-gridmet-real \
  --variable tmmx \
  --diagnostic-variables tmmx tmmn vpd

cp artifacts/fire-vase-gridmet-real/real_fire_vase_gridmet_interactive.html \
  docs/assets/figures/fire_vase_gridmet_interactive.html

cp artifacts/fire-vase-gridmet-real/real_fire_vase_gridmet_diagnostic.png \
  docs/assets/figures/fire_vase_gridmet_diagnostic.png
```

The first command downloads/caches FIRED event layers under the artifact
directory and streams the gridMET climate cube for the selected event window.
It also writes `real_fire_vase_gridmet_diagnostic.png`, a static panel with
VASE projections, climate traces, inside/outside samples, and hull metrics.
The second command is only needed when refreshing the website copy.

## Prescribed-burn VASE panel example

The multi-event form applies the same single-event workflow to a vetted set of
prescribed FIRED events and assembles successful results into one panel. For a
scientific run, supply the observed event tables and a loader that retrieves
the matching climate cube for each event:

```python
from cubedynamics import pipe, verbs as v

panel = (
    pipe(None)
    | v.fire_vase_panel(
        fired_daily=fired_daily,
        fired_events=fired_events,
        prescribed_column="fire_type",
        prescribed_values=("prescribed", "rx", "planned"),
        climate_loader=load_observed_gridmet_for_event,
        climate_variable="tmmx",
        max_events=12,
    )
).unwrap()

panel["fig_panel"]
panel["records"]
panel["failures"]
```

This public example deliberately requires observed FIRED tables and an
observed climate loader. It does not substitute generated event geometry or
climate measurements when either source is unavailable.

## Pipe verbs

### `v.fire_plot(...)`

`fire_plot` remains the single-event fire VASE verb. It accepts either an
already-open climate cube through the pipe or a climate-loading configuration
and returns the event, hull, climate cube, summary table, and static/interactive
figures.

The preferred object route is
`FireEventDaily -> FireHull -> attach_environment -> plot`. The cube-first
`v.fire_plot(cube, fired_event=event)` spelling below is the high-level
convenience route. Older `fired_daily=`/`event_id=` inputs remain compatibility
paths, not the primary teaching API.

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(gridmet_cube)
    | v.fire_plot(
        fired_event=event,
        climate_variable="tmmx",
        prefer_streaming=True,
    )
).unwrap()
```

### `v.fire_vase_panel(...)`

`fire_vase_panel` is the multi-event verb for prescribed-burn panels. It keeps
`fire_plot` intact for one event, then runs that same VASE construction across a
set of prescribed events and assembles the results into `fig_panel`.

Prescribed events can be supplied directly with `event_ids`, selected from a
known column with `prescribed_column`/`prescribed_values`, or discovered from
text-like FIRED attributes containing prescribed-burn labels.

```python
panel = (
    pipe(gridmet_cube)
    | v.fire_vase_panel(
        fired_daily=fired_daily,
        fired_events=fired_events,
        prescribed_column="fire_type",
        prescribed_values=("prescribed", "rx", "planned"),
        max_events=12,
    )
).unwrap()

panel["fig_panel"]
panel["records"]
panel["failures"]
```

For real runs where each burn needs its own climate pull, pass a
`climate_loader(event)` callback or set `load_climate=True` with the same
climate options used by `fire_plot`.

## Metrics available now

Stable metric names currently include:

- `duration_days`
- `scale_km`
- `footprint_area_peak_km2`
- `footprint_area_final_km2`
- `hull_volume_km2_days`
- `hull_surface_km_day`

Legacy aliases retained for compatibility:

- `days`
- `volume_km2_days`
- `surface_km_day`

These metrics are geometric summaries of the hull. They are not yet a complete ecological or dynamical taxonomy.

## Environmental attribution

The scientific direction is:

```python
hull + environment -> explanatory fire manifold
```

The current first implementation is `FireHull.attach_environment(...)`, which stores per-variable `HullClimateSummary` objects keyed by variable name:

```python
hull_with_env = hull.attach_environment(cube, variables=["vpd"], method="nearest")
fig = hull_with_env.plot(color="vpd")
```

This is intentionally modest but now mesh-aware. It stores:

- the original summary-level `HullClimateSummary`
- per-layer values aligned to hull time slices
- per-vertex values aligned explicitly to the mesh

It does not yet store a fully local `(x, y, t)` field sampled independently at every hull vertex.

## Population climate tables

The manuscript pipeline separates two climate-attribution products:

- `vase_slices.parquet`: the complete-population daily centroid baseline used
  for the main manuscript figures.
- `vase_climate_exposures.parquet`: a companion table with active daily burned
  area, cumulative burned area, and exterior perimeter-extension exposure
  zones.

This separation is intentional. Centroid climate is available for the largest
population and gives a conservative baseline. Perimeter and extension
attribution are richer, but must be reported with their own coverage and sample
method metadata.

## Cube compatibility

`FireHull.to_cube(template_cube)` returns a boolean occupancy cube aligned to a supplied template grid.

Why a template is required:

- CubeDynamics prefers explicit coordinate semantics.
- The hull itself does not yet define a standalone canonical occupancy grid.
- Requiring a template keeps the conversion predictable and composable.

## Current limitations

- The fire-specific interactive hull viewer still uses Plotly.
- `FireHull.to_cube()` requires a template cube.
- `attach_environment()` currently supports `method="nearest"` only.
- Environmental attribution is summary-level, not yet full local hull-element attribution.
- FIRED ingestion, hull geometry, attribution, and rendering are clearer than before, but not fully separated into independent public submodules yet.
