# What Is Streaming?

Streaming in CubeDynamics means computation does not begin with the assumption that every dataset must be fully downloaded, indexed, and materialized locally.

Instead, workflows are designed so data can be:

- accessed lazily
- sliced narrowly
- transformed incrementally
- kept in a consistent cube interface while results are computed

## Why It Matters

Environmental data is large enough that storage-first thinking quickly becomes a bottleneck.

Streaming-first thinking lets you:

- prototype locally
- scale to cloud-hosted data
- keep the same scientific workflow while changing where the data lives

## The Cube Is Not The Product

A cube is the working interface, not the endpoint.

The value comes from what you can compute through a streaming interface:

- anomalies
- aggregation
- detrending
- event-aligned comparisons

## Read Next

- [Virtual Cubes](../concepts/virtual_cubes.md)
- [Local sources](local_sources.md)
- [Cloud sources](cloud_sources.md)
- [STAC sources](stac_sources.md)
