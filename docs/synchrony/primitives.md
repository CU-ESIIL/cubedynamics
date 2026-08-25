# Four Synchrony Primitives

The four primitive operators answer different questions about the same state or
event history.

## Occurrence Synchrony

Occurrence asks whether states happen at the same times. The default metric is
Jaccard similarity, so shared non-event days do not dominate rare-event
analyses.

```python
occurrence = (
    pipe(hot)
    | v.occurrence_synchrony(
        spatial_mode="neighbors",
        radius_km=100,
        method="jaccard",
        window=365,
        stride=30,
    )
).unwrap()
```

See the [real PRISM states-and-events vignette](../vignettes/states_and_events.ipynb)
for a complete occurrence analysis with observed values, an explicit threshold,
event-duration filtering, and a plotted reference-cell synchrony map.

## Severity Synchrony

Severity asks whether event magnitudes co-vary when both locations are active.
The default estimator is Spearman correlation on jointly active observations.

```python
severity = (
    pipe(hot)
    | v.severity_synchrony(
        spatial_mode="neighbors",
        radius_km=100,
        method="spearman",
        min_joint_events=10,
    )
).unwrap()
```

No severity figure is published until the repository carries a vetted
observational example with enough joint events for the declared estimator.

## Timing and Duration Synchrony

Timing and duration use detected events and explicit one-to-one matching.
Timing compares matched onset, peak, or end dates. Duration compares how long
matched events persist.

```python
events = pipe(hot) | v.detect_events(min_duration=2, max_gap=1)

timing = events | v.timing_synchrony(
    spatial_mode="neighbors",
    radius_km=100,
    match_tolerance="5D",
)

duration = events | v.duration_synchrony(
    spatial_mode="neighbors",
    radius_km=100,
    match_tolerance="5D",
)
```

Timing and duration examples will be published with a reviewed event catalog;
exact generated truth cases remain software tests rather than reader-facing
scientific evidence.

## Output Shapes

- Reference and neighborhood modes return map-like outputs with
  `(time_window_end, y, x)`.
- All-pairs mode returns edge tables with `(time_window_end, pair)` plus
  source, target, and distance coordinates.
- Regional mode returns time-series summaries.
- Block mode is for block-level comparisons and aligns with
  `v.block_signature`, `v.collect_blocks`, and `v.compare_blocks`.

Relational results should stay relational. Do not force all-pairs outputs into
fake maps just because a cube viewer exists.

## Diagnostics to Watch

Every primitive should be read with its diagnostics:

- `joint_event_count`
- `event_union_count`
- `valid_sample_count`
- `joint_observation_count`
- `matched_event_count`
- unmatched source and target event counts
- lag and duration-difference summaries

The section overview shows a rolling-window comparison of occurrence and
severity. Use it as a reminder that synchrony is not one number.
