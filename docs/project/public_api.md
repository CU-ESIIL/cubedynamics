# Public API & Scope

This page describes the supported, user-facing surface of `cubedynamics` and how it is intended to evolve. Anything not listed here should be treated as internal and subject to change between releases.

For the alpha release, the [explicit 0.1 support contract](api_support_0_1.md)
distinguishes stable behavior, evolving reports, projects, candidates,
compatibility and reserved names. Exported does not mean production-certified.

## Canonical namespace

Import the library as:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
```

`cubedynamics` is the only supported top-level namespace. Symbols imported through `cd.*` follow the stability guidance below.

## Core grammar

The supported center of the package is:

- `pipe(value)` and `Pipe`, which compose callables with `|` and expose
  `unwrap()` at the workflow boundary. A pipe also exposes metadata-only
  `semantic_state`, `semantic_trace`, `explain()`, `suggest()`, and
  `validate()` coaching without rewriting the workflow;
- `verbs`, conventionally imported as `v`;
- the verb-factory protocol: a configured outer function returns a callable
  that accepts the current value and returns the next one;
- common cross-project verbs: `v.apply`, `v.mean`, `v.variance`, `v.anomaly`,
  `v.zscore`, `v.month_filter`, `v.overlap`, `v.flatten_space`, and
  `v.flatten_cube`. `v.overlap` is deliberately limited to exactly aligned
  boolean/state rasters; it is not a vector intersection operation.

Plain callables are valid pipe stages. Projects do not need to register or
subclass anything to extend the grammar.

The public `cubedynamics.grammar` module contains the small semantic-state
vocabulary, verb contracts, order-rule metadata, and structured report types.
See [Semantic grammar and analysis coaching](../concepts/semantic_grammar.md).

## Maintained integrations: dataset loaders

These helpers create xarray-backed cubes or streaming-friendly structures. Network access may be required depending on the data source.

The preferred public entry point is the scientific noun namespace:

- `from cubedynamics import data`
- climate/weather nouns: `data.temperature`, `data.precipitation`, `data.vpd`,
  `data.wind`, `data.humidity`, and `data.radiation`;
- surface nouns: `data.surface_reflectance` and `data.vegetation_index`;
- discovery: `data.sources`, `data.describe`, and `data.list_sources`.
- source maintenance: `data.ServingRevision`, lifecycle/status enums,
  `data.decide_source_change`, reusable QA-profile discovery/evaluation, and
  deterministic xarray schema fingerprinting.

Noun loaders select an implemented source flavor, normalize only names and
contracts, retain original source fields in provenance, stay lazy where the
backend allows, and never permit synthetic fallback.
They add lifecycle and lineage provenance without changing the noun call
signature or the pipe grammar. Revision scientific validity and current live
endpoint health are deliberately independent.

Provider-specific loaders remain supported for deliberate low-level access:

- `load_gridmet_cube`
- `load_prism_cube`
- `load_sentinel2_cube`
- `load_sentinel2_bands_cube`
- `load_sentinel2_ndvi_cube`
- Streaming adapters exposed at the top level:
  - `stream_global_climate_cube`
  - `stream_gridmet_to_cube`
  - `stream_prism_to_cube`
- Legacy aliases kept for compatibility (emit deprecation warnings):
  - `load_s2_cube`
  - `load_s2_ndvi_cube`
  - `load_sentinel2_ndvi_zscore_cube`

## Maintained vocabulary and project extensions

### Terrain, network, and station nouns

`cubedynamics.data.usgs.streamflow`, `cubedynamics.data.three_dep.elevation`,
and `cubedynamics.data.roads.roads` are explicit **candidate** imports, not
certified catalog nouns or stable production APIs. Their bounded scope and
raw-snapshot behavior are documented in the main noun references:
[elevation](../library/nouns/elevation.md), [roads](../library/nouns/roads.md),
and [streamflow](../library/nouns/streamflow.md), each with a real-data vignette.
[Operational review](../data/source_projects/production.md) is separate from
their place in the library and does not change the existing catalog registry.
`data.validate_source_promotion` verifies evidence-bound production gates;
it does not publish or change serving history.

- Maintained adapters and vocabulary include block helpers
  (`v.block_signature`, `v.collect_blocks`, `v.compare_blocks`), correlation and
  NDVI helpers, I/O, and visualization verbs. Their external dependencies and
  side effects are documented per verb.
- Early AOI names (`v.aoi_signature`, `v.compare_aoi_signature`) remain
  available for compatibility.
- Synchrony grammar verbs include state constructors (`v.threshold_state`, `v.quantile_state`, `v.binary_state`, `v.change_state`), event detection (`v.detect_events`), primitive synchrony operators (`v.occurrence_synchrony`, `v.severity_synchrony`, `v.timing_synchrony`, `v.duration_synchrony`), biological cube helpers (`v.rasterize_observations`, `v.align_cube`), and same-pixel lagged coupling (`v.sync_with`). These are public but intentionally narrow in their first implementation: cross-location coupling, richer null diagnostics, and complex event sequence grammars are future extensions.
- Fire/VASE verbs include `v.fire_plot` for a single event, `v.fire_panel` for compact hull/histogram panels, and `v.fire_vase_panel` for multi-event prescribed-burn VASE panels. Vase-aware helpers (`v.vase`, `v.vase_extract`, `v.vase_mask`) preserve hull metadata on cubes.

Synchrony, biological coupling, tubes, and Fire VASE are domain extensions that
currently ship in the same distribution and retain their documented `0.x`
imports. Their presence does not expand the core grammar contract. Future
extraction into separately versioned projects requires normal deprecation
notice.

## Visualization entry points

For quick plots without a pipe chain use:

- `cubedynamics.plot(cube, time_dim="time", cmap="viridis")` – convenience wrapper around `v.plot`.
- `cubedynamics.viz` and `cubedynamics.viewers` expose lower-level components and templates for custom rendering; they are considered internal unless routed through verbs.

## What is internal?

Treat the following as implementation details that may change without notice:

- Modules under `cubedynamics.ops`, `cubedynamics.streaming`, `cubedynamics.ops_fire`, `cubedynamics.ops_io`, and `cubedynamics.viewers`; use the documented `cd.stream_*` helpers when you need a supported streaming entry point.
- Demo helpers such as `demo`/`demo_vase` and example notebooks.
- Exploratory notebooks under top-level `notebooks/`; supported publication
  notebooks are explicitly marked under `docs/vignettes/` or
  `docs/decision_vignettes/` and run in CI.
- Private utilities (`cubedynamics.utils`, `cubedynamics.config`, `cubedynamics.progress`, etc.).

Internal modules may be refactored or renamed as the streaming architecture stabilizes. Prefer accessing functionality through the documented loaders, `pipe`, and `verbs`.

## Stability policy

CubeDynamics follows semantic versioning for the public surface described above:

- **Patch releases (`0.x.y`)**: bug fixes only; no breaking changes to documented public symbols.
- **Minor releases (`0.y`)**: may evolve early interfaces with release notes and migration guidance; preserve the named stable subset deliberately rather than casually breaking it.
- **Major releases (`1.0` and beyond)**: may remove deprecated aliases after advance notice.

Warning-emitting deprecated entry points remain available in 0.1. Some older
shims do not yet specify a removal version; do not invent one. Compatibility
aliases without warnings are not automatically deprecated.
