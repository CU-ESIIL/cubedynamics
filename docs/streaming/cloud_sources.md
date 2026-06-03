# Cloud Sources

CubeDynamics is designed to operate on cloud-hosted environmental data without turning cloud access into the central abstraction.

The goal is not to make users think in terms of provider-specific plumbing.

The goal is to make this stable:

```python
cube = load_data(...)
result = pipe(cube) | some_verb()
```

## Why Cloud Matters

Cloud-hosted archives make it possible to:

- avoid managing massive local datasets
- move from notebook experiments to larger workflows
- orchestrate the same computation in automated systems

## Role In CubeDynamics

Cloud access is part of the streaming interface, not the whole product.

CubeDynamics sits above the storage and retrieval layer and focuses on consistent environmental computation once data enters the cube interface.

## Related Reading

- [Streaming Environmental Data](index.md)
- [Datasets](../datasets/index.md)
