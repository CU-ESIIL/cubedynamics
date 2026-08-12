# Workflow Composition

CubeDynamics workflows are designed to compose small transformations into scientific results.

That composition model is one of the main reasons the package works well for both humans and AI systems.

## The Pattern

```python
result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
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
- [Write a custom verb project](../extending/custom_verbs.md)
