---
description: "How CubeDynamics separates matching timestamp labels, physical observation windows, and scientific event timing."
---

# Temporal alignment

## What does “the same day” mean?

Two environmental products can both contain `time = 2024-07-13` without
describing the same hours of the physical world. A timestamp is a label; a
temperature maximum or precipitation total usually summarizes an interval.

```text
                         label: 2024-07-13
Source A       |========== daily observation ==========|
Source B                    |========== daily observation ==========|
               same coordinate label · different physical support
```

That distinction matters whenever a signal crosses an interval boundary. It
can change daily maxima, accumulated precipitation, threshold-crossing dates,
event starts and ends, synchrony, lagged relationships, and cross-source
correlations.

> **Alignment is part of the scientific question. Equal timestamps do not
> guarantee equal observations in time.**

For condition lag coupling, `+5D` means compare the left condition at `t` with
the right condition at `t+5D`; the right-hand condition occurs later. Negative
lags mean the right-hand condition occurs earlier. These are coordinate-label
comparisons, not observation-support shifts or event-anchor differences.

## Three separate questions

1. **Coordinate alignment:** Are the xarray time labels exactly equal?
2. **Observation-support alignment:** Do those labels represent the same
   physical instant or interval?
3. **Event-time alignment:** Which event label—start, end, or peak—is being
   compared, and within what tolerance?

CubeDynamics keeps these questions separate. None of the temporal APIs below
silently shifts, resamples, interpolates, aggregates, or truncates data.

## Inspect a source's temporal support

Source-qualified nouns carry a temporal-support rule. The rule is compact
metadata rather than a full start/end array, so it does not duplicate a large
cube. You can inspect the rule or derive one-dimensional bounds when needed:

```python
from cubedynamics import data

support = data.temporal_support(temperature)
bounds = data.observation_intervals(temperature)

support.support_type       # "interval" or "instant"
bounds.observation_start
bounds.observation_end
```

`data.observation_intervals()` reads only the time coordinate. Dask-backed
values remain lazy. If source evidence is missing, support is reported as
unknown and bounds are not invented.

## PRISM and gridMET

The PRISM Climate Group defines a PRISM day as **12:00 UTC to 12:00 UTC** and
uses a day-ending name: the interval ending at 12:00 UTC on July 13 is labeled
July 13. [PRISM dataset documentation](https://data.prism.oregonstate.edu/PRISM_datasets.pdf)
documents both the interval and label convention.

The gridMET methods page says gridMET nominally treats a day as
**midnight-to-midnight Mountain Standard Time (07:00 UTC)**. CubeDynamics pairs
that verified physical convention with the adapter's calendar-date coordinate.
[gridMET methods and data notes](https://www.climatologylab.org/gridmet.html)
document the nominal day.

Therefore equal PRISM and gridMET date labels have **different known temporal
support**. This timing distinction is not the only product difference: their
units, grids, inputs, methods, and revision histories also differ. In
particular, gridMET blends PRISM spatial information with reanalysis, so these
are not independent measurements.

```python
import cubedynamics as cd

report = cd.compare_temporal_support(prism_temperature, gridmet_temperature)
report.coordinates          # "exact", when date labels match
report.temporal_support     # "different"
```

## Make a deliberate alignment decision

`v.align_time()` is a semantic, pass-through verb. It verifies and records a
decision without changing either input:

```python
from cubedynamics import pipe, verbs as v

checked = (
    pipe(prism_temperature)
    | v.align_time(gridmet_temperature, mode="labels")
)

print(checked.explain())
print(checked.validate())
```

- `mode="labels"` explicitly pairs the unchanged labels. Different or unknown
  support remains visible as a caveat.
- `mode="require_exact_support"` requires exact labels and identical, known
  support. It rejects a known mismatch and refuses to treat unknown as exact.

Support-overlap resampling is intentionally not implemented. Defining a new
window would be a scientific transformation, not merely alignment metadata.

## Conditions and overlap

`v.overlap()` retains its exact coordinate and spatial guardrails. If two
conditions have different known temporal support, the default call fails with
guidance. A scientist can deliberately pair current labels:

```python
joint = (
    pipe(prism_condition)
    | v.overlap(gridmet_condition, temporal_alignment="labels")
)
```

The result records `coordinates=exact`, `temporal_support=different`, the two
source identities, and that no coordinates or values were modified. Using
`temporal_alignment="require_exact_support"` rejects different or unknown
support.

Unknown support is not silently called exact. For backward compatibility with
ordinary xarray conditions, overlap can proceed when support metadata is
unknown, but `validate()` emits a `CHECK` and the output records the uncertainty.

## Events and lags are another layer

`v.detect_events()` stores event `start` and `end` as labels of the first and
last active observations. They are not observation-support bounds.
`v.timing_synchrony(event_anchor="start")` compares event-start labels;
`event_anchor="end"` compares event-end labels. `v.sync_with(..., lags=("1D",))`
shifts the right condition by coordinate periods. It does not shift or
harmonize physical observation windows.

Use `data.observation_intervals()` when the physical bounds matter, and keep
that review separate from the event-matching choice.

## Real-data walkthrough

The [PRISM/gridMET temporal-alignment notebook](../examples/temporal_alignment.ipynb)
loads maximum temperature and precipitation for the same South Dakota dates,
inspects the declared intervals, and makes the label-pairing decision explicit.
It requires network access because noun loaders never substitute synthetic
observations.
