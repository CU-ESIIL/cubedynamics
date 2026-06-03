# Local Sources

CubeDynamics works with local environmental data, but it does not require local-first architecture.

Use local sources when:

- you already have files on disk
- you want deterministic demos or tests
- you are prototyping with small subsets

Local use is one deployment mode inside the broader streaming model.

## Typical Pattern

```python
cube = load_data(...)
result = pipe(cube) | some_verb()
```

The same grammar should still apply if you later move that workflow to cloud or STAC-backed sources.

## Related Reading

- [Getting Started](../quickstart.md)
- [Datasets overview](../datasets/index.md)
