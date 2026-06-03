# Streaming Environmental Data

Streaming comes before grammar in CubeDynamics.

Before you can compose operations, you need a consistent way to access environmental data without assuming one storage platform, one archive, or one deployment model.

## What Streaming Means Here

In CubeDynamics, a stream is an environmental data source that can be accessed and transformed without requiring you to materialize the entire analysis space locally first.

That includes:

- local files
- cloud-hosted raster archives
- STAC-backed assets
- synthetic or derived cubes

## Why Streaming Comes First

CubeDynamics is not built around:

- one data catalog
- one backend
- one storage engine

It is built around a stable computation interface that can sit above many sources.

That is why the docs lead with streaming before verbs.

## In This Section

- [What is streaming?](what_is_streaming.md)
- [Virtual Cubes](../concepts/virtual_cubes.md)
- [Local sources](local_sources.md)
- [Cloud sources](cloud_sources.md)
- [STAC sources](stac_sources.md)

## Shared Interface

Scientists and AI agents use the same streaming interface:

```python
cube = load_data(...)
result = pipe(cube) | some_verb()
```

The source can change. The grammar stays consistent.
