# Operations Reference – Stats

Statistic verbs summarize cubes along dimensions or compare axes. They live in `cubedynamics.ops.stats` and are available directly via `cubedynamics`. Examples assume `import cubedynamics as cd` and a `cube` variable bound to an `xarray` object.

## `variance(dim)`

Computes the variance along a dimension.

```python
result = (
    cd.pipe(cube)
    | cd.variance(dim="time")
).unwrap()
```

- **Parameters**
  - `dim`: dimension to collapse.
- **Returns**: variance cube with the target dimension removed (or reduced) according to `xarray` semantics.

## `correlation_cube` (stub)

A forthcoming verb for building correlation matrices/surfaces between variables, time windows, or anchor pixels.

```python
result = (
    cd.pipe(cube)
    | cd.correlation_cube(target="ndvi", reference="pr")
).unwrap()
```

- **Intended behavior**: compute rolling or full-period correlations between named data variables or coordinates, returning an `xarray` cube with correlation coefficients.
- **Status**: interface stub; functionality will land alongside streaming adapters.

Combine these stats with transforms and IO verbs to produce complete analyses.
