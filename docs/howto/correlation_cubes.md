# Correlation and synchrony

These are distinct analyses: correlation describes covariation of continuous
values; synchrony can compare occurrence, severity, timing or duration of states
and events. Choose the quantity before choosing the operation.

| Task | Implemented reference or workflow |
| --- | --- |
| Compare state occurrence, severity, timing and duration | [Four synchrony primitives](../synchrony/primitives.md) |
| Follow a complete observed state/event analysis | [States and events notebook](../vignettes/states_and_events.ipynb) |
| Compare rolling upper/lower behavior | [Median-split synchrony](../reference/verbs/rolling_median_split_synchrony.md) |
| Compare a cube with its center | [Rolling tail dependence](../reference/verbs/rolling_tail_dep_vs_center.md) |
| Compare two aligned continuous fields | [Climate and NDVI alignment requirements](../examples/climate_ndvi_correlation.md) |

`v.correlation_cube` is a [reserved, unimplemented API](../reference/verbs/correlation_cube.md).
It does not return a correlation cube. For explicit xarray calculations, align
CRS, spatial support, timestamps and missing-data semantics first. Matching
dimension names alone does not establish comparability.
