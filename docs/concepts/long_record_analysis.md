# Long-record analysis

> A longer time series is not merely more observations. It creates repeated
> events, recurrence, trajectories, changing relationships, and potential
> regimes.

## One inspectable 20-year question

For daily May–September observations from 2005–2024, this grammar means:

```python
hot = (
    pipe(temperature)
    | v.month_filter([5, 6, 7, 8, 9])
    | v.quantile_state(quantile=0.90, direction="above", name="hot")
)

local_events = hot | v.detect_events(min_duration=2)

regional_events = (
    local_events
    | v.consolidate_events(
        spatial_relation="neighbors",
        max_gap="1D",
        min_participating_cells=3,
    )
)

annual = regional_events | v.event_metrics(period="year")
```

The default quantile is pooled across every selected time coordinate and
estimated independently at each remaining cell. It is not a separate annual
quantile, day-of-year climatology, monthly climatology, or detrended
percentile. `explain()` prints the reference population, including months
retained by `month_filter`.

An exact pooled quantile needs every selected time observation for each
remaining spatial chunk. With Dask inputs, `quantile_state` therefore keeps the
operation lazy but may rechunk the selected time dimension to one chunk for
compatibility across supported xarray versions. Spatial chunks are retained.
Bound the temporal domain deliberately when that exact reduction would exceed
available worker memory.

## Where computation happens

`month_filter`, threshold/quantile state creation, and `overlap` preserve Dask
laziness. `detect_events` must inspect true/false runs and therefore
materializes its condition cube to construct an in-memory catalog. Use bounded
spatial domains or tiles for very large records. Event consolidation operates
on that already-materialized catalog using a start-time sweep and compares only
temporally active candidates; it does not perform an unconditional all-pairs
date grouping.

Event contiguity respects the actual time-coordinate cadence. After seasonal
filtering, an active 30 September and active 1 May are not silently joined
because they became adjacent array positions.

## Lag direction

For `v.sync_with(right, lags=["5D"])`, `+5D` compares `left(t)` with
`right(t+5D)`: the right-hand condition occurs five days later. `-5D` means the
right-hand condition occurs five days earlier. This is a coordinate-label
comparison. It does not shift or harmonize either source's physical
observation support.

## Boundaries of the current grammar

CubeDynamics now supports observation → condition → local event → regional
episode → period metrics. Event-relative trajectories, combined period
signatures, trends, change points, and event classification remain explicit
design gaps rather than hidden pandas conventions. See the
[life-history and regime design note](../project/event_life_history_design.md).
