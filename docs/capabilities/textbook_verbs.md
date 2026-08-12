# Verb vocabulary by ownership

CubeDynamics expresses analysis as `value -> verb -> value`. This page is a
conceptual catalog of the verbs that currently ship with the distribution; the
[API reference](../api/verbs.md) is the source for exact signatures.

## Core cross-project vocabulary

These verbs demonstrate the stable composition model and are useful across
domains:

| Verb | Contract |
| --- | --- |
| `v.apply(function, **kwargs)` | Apply an ordinary function as a one-off pipe stage |
| `v.mean(dim=...)` | Reduce a dimension, optionally retaining it at length one |
| `v.variance(dim=...)` | Compute variance with the same dimension convention |
| `v.anomaly(dim="time")` | Subtract the mean while preserving cube shape |
| `v.zscore(dim="time")` | Center and scale along a dimension |
| `v.month_filter(months)` | Select calendar months |
| `v.flatten_space()` | Stack spatial dimensions for table/model workflows |
| `v.flatten_cube()` | Stack non-time dimensions |

```python
from cubedynamics import pipe, verbs as v

regional_anomaly = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()
```

## Integration verbs

Integration verbs connect the grammar to a source, file format, or renderer.
They can have optional dependencies, network behavior, or explicit side
effects:

- `v.ndvi_from_s2`, `v.landsat8_mpc`, and related remote-sensing adapters;
- `v.correlation_cube` and block-signature adapters;
- `v.to_netcdf` for explicit materialization;
- `v.plot`, `v.plot_mean`, `v.diagnostic_panel`, and
  `v.show_cube_lexcube` for rendering.

These are maintained conveniences, not requirements for creating or composing
a verb.

## Project vocabularies

The distribution currently includes specialized vocabularies developed by
projects:

- state and event construction;
- occurrence, severity, timing, duration, and lagged synchrony;
- biological observation rasterization and alignment;
- fire-event extraction, Fire VASE geometry, climate attribution, and panels;
- suitability tubes.

They remain available for `0.x` compatibility. Their domain assumptions belong
to their project documentation and should not be inferred as part of the
minimal grammar.

## Verbs that do not exist

Older design pages used prospective names such as `v.sum`, `v.min`, `v.max`,
`v.quantile`, `v.rolling`, `v.climatology`, `v.synchrony`, and `v.detrend` as if
they were implemented. They are not exported in version `0.1.0` and should not
appear in runnable examples. Use xarray through `v.apply` for a one-off, create a
project verb, or propose a focused built-in with tests and a clear cube
contract.

## Add your own vocabulary

Custom project verbs use exactly the same pipe contract. Continue with
[Write a custom verb project](../extending/custom_verbs.md) or run the
[custom-verb vignette](../vignettes/custom_verb_project.ipynb).
