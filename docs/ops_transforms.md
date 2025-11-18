# Operations Reference – Transforms

Transform verbs reshape or filter cubes before you compute downstream statistics. All functions live under `cubedynamics.ops.transforms` but are re-exported at the package root. Examples assume `import cubedynamics as cd` and a `cube` variable that is an `xarray` object.

## `anomaly(dim)`

Computes anomalies by subtracting the mean along a dimension.

```python
result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
).unwrap()
```

- **Parameters**
  - `dim`: dimension name (e.g., `"time"`).
- **Returns**: `xarray.DataArray`/`Dataset` with mean-centered values.

## `month_filter(months)`

Filters a cube to the specified month numbers (1–12). Useful for seasonal composites before running statistics.

```python
result = (
    cd.pipe(cube)
    | cd.month_filter([6, 7, 8])
    | cd.anomaly(dim="time")
).unwrap()
```

- **Parameters**
  - `months`: iterable of integers representing desired months.
- **Behavior**: keeps the original metadata while dropping other timesteps.

Use these verbs as building blocks ahead of stats like variance or correlation.
