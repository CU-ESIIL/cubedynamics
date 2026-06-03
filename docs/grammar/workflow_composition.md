# Workflow Composition

CubeDynamics workflows are designed to compose small transformations into scientific results.

That composition model is one of the main reasons the package works well for both humans and AI systems.

## The Pattern

```python
result = (
    pipe(cube)
    | v.anomaly()
    | v.aggregate()
    | v.detrend()
)
```

Each verb should do one interpretable thing.

## Why This Matters

Composition gives you:

- readable notebooks
- debuggable scientific pipelines
- workflows that can be scripted or orchestrated by agents

## Related Reading

- [Grammar of Streaming](index.md)
- [Verbs](../api/verbs.md)
- [Workflows](../workflows/index.md)
