---
description: "Pre-implementation inventory of the CubeDynamics pipe, verbs, semantic contracts, provenance, and grammar gaps."
---

# Grammar Inventory

This inventory records the public grammar immediately before semantic tracing
was added. It is an implementation baseline, not a promise that every imported
project helper belongs to the minimal core grammar.

## Pipe behavior

| Concern | Existing behavior |
|---|---|
| Wrapper | `pipe(value)` returns `Pipe(value)` |
| Composition | `Pipe.__or__` calls the supplied stage exactly once, in user order |
| Result | Every stage returns a new `Pipe`; `unwrap()` returns the current value |
| Plain callables | Accepted without registration or subclassing |
| `Verb` wrapper | Forwards to its callable and supports pass-through viewer attachment |
| Laziness | Pipe itself does not compute; behavior belongs to the stage |
| Introspection | Value repr and viewer repr only; no stage history or semantic state |
| Rewriting | None |

Pass-through plotting uses `_cd_passthrough_on_call` or
`_cd_passthrough_on_pipe` and attaches `_cd_last_viewer` to the cube. Semantic
tracking must preserve this behavior.

## Public verb surface

Runtime introspection found 54 callable names imported on
`cubedynamics.verbs`; 38 are listed in `verbs.__all__`. The difference is a
legacy/de-facto-public boundary: state, event, synchrony, and biology verbs are
documented and tested even though several are absent from `__all__`.

### Common grammar

- reducers: `mean`, `variance`
- transforms: `anomaly`, `zscore`, `month_filter`, `apply`
- state/event: `threshold_state`, `quantile_state`, `binary_state`,
  `change_state`, `exceedance`, `detect_events`
- combination: `overlap`, `correlation_cube`, `sync_with`
- shape/model: `flatten_space`, `flatten_cube`, `fit_model`
- block summaries: `block_signature`, `collect_blocks`, `compare_blocks`, with
  compatibility aliases `aoi_signature` and `compare_aoi_signature`
- plotting/output: `plot`, `plot_mean`, `diagnostic_panel`,
  `show_cube_lexcube`, `to_netcdf`

### Domain/project vocabulary

- synchrony: `occurrence_synchrony`, `severity_synchrony`,
  `timing_synchrony`, `duration_synchrony`
- biology: `rasterize_observations`, `align_cube`
- remote-sensing helpers: `ndvi_from_s2`, `landsat8_mpc`,
  `landsat_vis_ndvi`, `landsat_ndvi_plot`
- Fire/VASE/tubes: `extract`, `vase`, `vase_extract`, `vase_mask`,
  `vase_demo`, `fire_plot`, `fire_derivative`, `fire_panel`,
  `fire_vase_panel`, `climate_hist`, `tubes`

Imported implementation helpers such as `compute_time_hull_geometry` and
`time_hull_to_vase` are visible on the module but are not treated as ordinary
grammar verbs.

## Existing contracts and errors

- Statistical verbs explicitly check requested dimensions and raise
  `ValueError` with the missing/current dimensions.
- State constructors require a suitable DataArray or selected Dataset variable
  and return a Dataset with `state`, `magnitude`, and `threshold`.
- `detect_events` requires a state Dataset and a time dimension, then returns an
  `EventResult` containing an event cube and catalog.
- `overlap` requires DataArray/Dataset state inputs and exact xarray coordinate
  alignment; it refuses silent resampling or reprojection and returns the
  canonical condition Dataset containing only Boolean `state`. It records the
  operand identities and alignment contract without inventing a magnitude or
  threshold for a logical intersection.
- Flattening verbs validate required spatial/time dimensions.
- Plotting accepts DataArrays, VirtualCubes, and semantic Datasets. Dataset
  selection prefers `state`, then `event_active`, then a sole variable;
  ambiguous Datasets require `variable=`.
- Errors are technical and local to each implementation. The pipe does not yet
  read them back in scientific language or suggest a preceding stage.

## Shape and information changes

| Verb family | Requires | Preserves/removes | Output |
|---|---|---|---|
| `anomaly`, `zscore` | requested dimension | preserves input dimensions | continuous field |
| `mean`, `variance` | requested dimension | removes variation over reduced dimension; may retain a length-one axis | reduced field/summary |
| state constructors | numeric/boolean field; time for quantile/change | preserves cube support | condition Dataset |
| `detect_events` | temporal condition | preserves event cube support and adds catalog | event result |
| `overlap` | exactly aligned states | preserves shared dimensions | condition Dataset |
| `flatten_space` | spatial dimensions | removes `y`, `x` as dimensions | time × pixel field |
| `flatten_cube` | time | stacks non-time dimensions | time × sample field |
| plotting | renderable semantic array/Dataset/EventResult | selected values and semantic metadata | interactive 3-D cube, static 2-D map, or static 1-D temporal line |

The key semantic gap is that a retained length-one `time` axis after
`mean(dim="time")` no longer contains time variation even though a superficial
dimension check can still find the name `time`.

## Noun and provenance conventions

Public scientific noun loaders already attach:

- `scientific_noun`, source flavor/provider/product/version and source variables;
- spatial and temporal queries, CRS, resolutions, streaming protocol;
- units, normalization/data state, retrieval time, and `is_synthetic=False`.

Provider loaders use the older standardized provenance keys `source`,
`is_synthetic`, `freq`, `requested_start`, and `requested_end`. State/event
outputs generally copy incoming attrs before adding analysis metadata.

The semantic system should reuse these attrs and add only small semantic keys;
it should not create a second provenance record.

## Keyword consistency

Most reducers use `dim=`. The desired grammatical spelling is `over=` while
retaining `dim=` for compatibility. Spatial relation verbs proposed in design
documents (`near`, `intersect`, `summarize`, `density`) are not implemented and
must not be presented as runnable APIs.

## Gaps the semantic layer must fill

- no shared verb registry or accepted/returned semantic states;
- no semantic stage history on `Pipe`;
- no deterministic explanation, suggestions, or metadata-only validation;
- no distinction between a time dimension and remaining time variation;
- no curated order-response library;
- no registry-shaped metadata for documentation or future agent tooling;
- no cross-stage scientific error that explains the missing preceding step;
- no explicit no-rewrite evidence beyond the current simple implementation.

These gaps can be addressed without changing the public sentence
`pipe(noun) | verb() | verb()` or introducing a new DSL.
