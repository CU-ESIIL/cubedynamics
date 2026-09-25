# Synchrony Grammar

Synchrony in CubeDynamics is now modeled as a small grammar rather than as one
center-pixel climate recipe.

The broader scientific and development plan is tracked in the
[Synchrony Roadmap](../project/synchrony_roadmap.md).

The state/event branch is:

```python
raw_cube -> state_cube -> event_result -> synchrony_operator -> spatial_summary
```

The current climate-tail relationship branch is:

```text
climate_cube -> local_synchrony_pairs -> local surface / fixed support /
                                           finite range / continuous decay
```

Pair construction measures `S(i,j)`. `local_synchrony_surface()` organizes the
incident relationships as `S_p(dx,dy)`. `synchrony_signature()` reduces within
declared supports. `empirical_synchrony_range()` diagnoses whether a finite
convergence distance resolves, while `empirical_synchrony_decay()` describes
continuous multiscale change without requiring a hard horizon. The branches
answer different questions and are not a mandatory sequence. See the
[local synchrony recipe](../recipes/spatial_synchrony_signature.md).

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

## Deferred design space

The roadmap also calls for bootstrap confidence intervals,
autocorrelation-preserving null models, richer threshold sensitivity, event
graphs, `followed_by`, `recurrence`, and `lagged_response`. Historically
anchored climate tails are also future work: the current tail-synchrony verbs
define tails relative to the analyzed window. Do not infer a historical-trend
analysis, climate regime, or learned convolution from the current spatial
relationship grammar.
