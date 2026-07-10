# Four Types of Synchrony

Start from one state cube and reuse it across synchrony operators.

```python
from cubedynamics import pipe, verbs as v

hot = (
    pipe(tmax_cube)
    | v.threshold_state(threshold=35, direction="above")
).unwrap()
```

## Occurrence

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

`occurrence_synchrony` reports the score plus `joint_event_count`,
`event_union_count`, and `valid_sample_count`.

## Severity

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

`severity_synchrony` calculates Spearman correlation on jointly active
observations and returns joint counts plus magnitude summaries.

## Timing

```python
events = (
    pipe(hot)
    | v.detect_events(state_var="state", min_duration=2, max_gap=1)
).unwrap()

timing = (
    pipe(events)
    | v.timing_synchrony(
        spatial_mode="neighbors",
        radius_km=100,
        match_tolerance="5D",
    )
).unwrap()
```

Timing synchrony uses explicit one-to-one event matching. It reports matched
event counts, unmatched event counts, mean lag, and median absolute lag.

## Duration

```python
duration = (
    pipe(events)
    | v.duration_synchrony(
        spatial_mode="neighbors",
        radius_km=100,
        match_tolerance="5D",
    )
).unwrap()
```

Duration synchrony reports a correlation-based score, direct duration
similarity, mean duration difference, and matched-event diagnostics.
