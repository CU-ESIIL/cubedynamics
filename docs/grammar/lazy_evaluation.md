# Lazy Evaluation

Lazy evaluation in CubeDynamics means workflows should defer heavy work until results are actually needed.

This is important because CubeDynamics is built for streaming environmental computation, not eager materialization of every intermediate result.

## Why It Matters

Lazy evaluation helps:

- preserve scaling options
- keep workflows usable on large datasets
- make the same code portable between local notebooks and cloud execution

## Practical Rule

Prefer writing workflows as transformations over a cube interface:

```python
result = (
    pipe(cube)
    | v.anomaly()
    | v.aggregate()
    | v.detrend()
)
```

Let the backend decide when actual materialization is required.

## Related Reading

- [Virtual Cubes](../concepts/virtual_cubes.md)
- [Workflow composition](workflow_composition.md)
