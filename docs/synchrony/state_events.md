# State Cubes and Events

Synchrony starts by turning raw values into explicit states. This keeps the
rule for defining an event separate from the operator used to compare events.

## State Cube Contract

Every state constructor returns an `xarray.Dataset` with:

- `state`: boolean active/inactive condition.
- `magnitude`: distance beyond the threshold.
- `threshold`: scalar or broadcast threshold used to define the state.

```python
from cubedynamics import pipe, verbs as v

hot = (
    pipe(tmax_cube)
    | v.threshold_state(
        threshold=35.0,
        direction="above",
        name="hot_state",
    )
).unwrap()
```

Quantile states use each pixel's distribution or a rolling window:

```python
cold = (
    pipe(tmin_cube)
    | v.quantile_state(
        quantile=0.5,
        direction="below",
        rolling_window=90,
        name="cold_state",
    )
).unwrap()
```

Binary masks can be normalized with `v.binary_state()`, and biological response
states can be built with `v.change_state()`.

## Event Result Contract

Timing and duration synchrony need event identity. `v.detect_events()` turns
contiguous `True` runs into an `EventResult`:

```python
events = (
    pipe(hot)
    | v.detect_events(
        state_var="state",
        magnitude_var="magnitude",
        min_duration=2,
        max_gap=1,
    )
).unwrap()

events.dataset
events.catalog
```

The Dataset contains event variables such as `event_active`, `event_id`,
`event_age`, `event_duration`, `event_peak`, `event_mean`, `event_integral`,
`sequence_index`, and `time_since_previous_event`.

The catalog is a pandas DataFrame with one row per event. It stays outside
xarray attrs so large event tables remain visible and inspectable.

`start` and `end` are the coordinate labels of the first and last active
observations. They are not the physical start and end of those observations'
support intervals. `v.timing_synchrony(event_anchor="start")` compares event
start labels; `event_anchor="end"` compares event end labels. This event-time
question is separate from verifying that the source observations cover the
same hours. See [Temporal alignment](../concepts/temporal_alignment.md).

## Observational example

The [real PRISM states-and-events vignette](../vignettes/states_and_events.ipynb)
shows the complete value → state → persistent event → occurrence synchrony
story with a declared source, threshold, units, and plotted results. Matched
timing and duration diagnostics will be added when a vetted event catalog is
available for the publication examples.
