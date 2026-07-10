# Synchrony Grammar

Synchrony in CubeDynamics is now modeled as a small grammar rather than as one
center-pixel climate recipe.

The broader scientific and development plan is tracked in the
[Synchrony Roadmap](../project/synchrony_roadmap.md).

The pipeline is:

```python
raw_cube -> state_cube -> event_result -> synchrony_operator -> spatial_summary
```

State cubes are ordinary `xarray.Dataset` objects with:

- `state`: boolean active/inactive condition.
- `magnitude`: distance beyond the defining threshold.
- `threshold`: scalar or broadcast threshold used to define the state.

Event results are lightweight objects with two parts: an event Dataset and a
pandas catalog. The catalog stays out of xarray attrs so large event tables are
not hidden in metadata.

## Primitive synchrony types

- `v.occurrence_synchrony`: compares whether states occur at the same times.
  The default metric is Jaccard similarity so shared non-event days do not
  dominate rare-event analyses.
- `v.severity_synchrony`: compares magnitudes when both locations are active.
  It returns joint-observation counts and magnitude summaries.
- `v.timing_synchrony`: matches detected events one-to-one and compares start,
  peak, or end timing.
- `v.duration_synchrony`: compares durations of one-to-one matched events and
  reports both correlation and direct similarity diagnostics.

## Spatial modes

The same synchrony operators can compare:

- `reference`: every pixel against a specified pixel, with `reference="center"`
  retained for backwards compatibility.
- `neighbors`: nearby pixels summarized back to a map.
- `all_pairs`: unique pairwise edges, documented as O(n^2).
- `regional`: aggregate edge summaries through time.
- `blocks`: block-level comparison hooks that align with `v.block_signature`,
  `v.collect_blocks`, and `v.compare_blocks`.

Reference and neighbor modes return map-like outputs with
`(time_window_end, y, x)`. All-pairs mode returns `(time_window_end, pair)` with
source, target, and distance coordinates. Regional mode returns time-series
summaries instead of forcing relational results into a fake cube.

## Climate-biology coupling

Biological observations can be rasterized onto a climate cube template, aligned
to another cube, converted to states, and compared with climate states using
`v.sync_with`. The first coupling implementation supports same-pixel lagged
occurrence synchrony and reports `coupling_score`, `joint_event_count`,
`valid_sample_count`, and `best_lag`.

The existing `v.rolling_median_split_synchrony` remains public. Treat it as a
convenience recipe for center-reference climate tail synchrony, not as the
general definition of synchrony.

## Deferred Design Space

The roadmap also calls for diagnostic plots, bootstrap confidence intervals,
autocorrelation-preserving null models, threshold sensitivity surfaces,
distance-decay curves, synthetic validation datasets, event graphs,
`followed_by`, `recurrence`, and `lagged_response`. These remain future phases
until their statistical contracts are explicit enough to expose as public verbs.
