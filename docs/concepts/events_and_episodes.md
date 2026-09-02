# Local events and regional episodes

## What does one event row mean?

`v.detect_events()` follows a condition through time independently at every
spatial cell. One catalog row therefore means **one contiguous local event at
one cell**. Five hundred rows mean five hundred local instances—not five
hundred independent regional heat waves.

```python
local_heat = (
    pipe(hot_state)
    | v.detect_events(min_duration=2)
).unwrap()

print(local_heat.explain())
```

`EventResult.event_scope` is `local_cell`, and its catalog records `y_index`
and `x_index` as spatial identity fields. Its bounded notebook representation
shows a scope-aware summary and five-row preview instead of dumping the entire
catalog.

## Consolidate only through declared scientific criteria

Regional episodes require a second operation:

```python
regional_heat = (
    pipe(local_heat)
    | v.consolidate_events(
        spatial_relation="neighbors",
        max_gap="2D",
        min_participating_cells=3,
    )
).unwrap()
```

The verb builds space-time connected components. Two rows can join only when
their start/end label intervals overlap or lie within `max_gap` **and** their
cells satisfy the selected relation:

- `neighbors`: cells touch by side or corner in grid-index space;
- `same_cell`: only runs at the same cell may join; or
- `radius`: geographic coordinates lie within an explicit `radius_km`.

`radius` refuses projected or out-of-range coordinates rather than guessing
their units. Matching dates alone never merge spatially unrelated events.

The result has scope `regional_episode` and exposes episode start, end,
duration in source observation coordinates, local-event count, participating
cell count, peak participation, optional peak severity, centroid, source event
IDs, and a serialized consolidation rule. Episode bounds remain coordinate
labels; the verb does not shift or resample observation support.

## Ask period questions without discarding scope

```python
annual = (
    pipe(regional_heat)
    | v.event_metrics(
        period="year",
        metrics=("event_count", "mean_duration", "max_duration"),
    )
).unwrap()
```

For local events, `event_count` counts cell instances and `event_days`
accumulates cell-days. For regional episodes, those variables count episodes
and episode-days. `date_field="start"` is the default period assignment and is
recorded in result metadata. Supported metrics are deliberately narrow:
counts, duration summaries, summed event duration, optional severity, and
regional participation summaries.

Timing and duration synchrony currently compare spatially identified
`local_cell` events. They report that scope and reject regional episodes until
an episode-level relationship contract is defined.
