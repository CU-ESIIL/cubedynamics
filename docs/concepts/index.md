# Concepts

## The Cube Abstraction
At its core, Climate Cube Math works with xarray-backed DataArrays. But it imposes strong semantics on top of them.
A cube:

- has named spatial and temporal dimensions
- carries metadata about resolution, alignment, and scale
- enforces consistency across operations

This avoids a common failure mode in spatiotemporal analysis:
> “I’m not sure what dimension this operation ran over.”

In Climate Cube Math, dimensions are explicit and intentional.

## VirtualCubes and Streaming
Environmental datasets are often too large to load into memory. VirtualCubes solve this by:

- representing a cube without materializing it
- streaming chunks through analysis pipelines
- preserving the cube abstraction throughout

From the user’s perspective:

- code stays the same
- operations stay semantic
- scale becomes a configuration choice, not a rewrite

## Pipes and Verbs: A Grammar of Analysis
Climate Cube Math uses a grammar-of-graphics–inspired design. Instead of chaining methods, you compose verbs:

```python
from cubedynamics import pipe, verbs as v

pipe(cube) | v.mean() | v.rolling() | v.plot()
```

Why this matters:

- verbs are inspectable
- pipelines are declarative
- analysis steps are explicit objects

This makes workflows easier to reason about, test, and share.

## Space, Time, and Scale
Many errors in environmental analysis come from implicit assumptions:

- mismatched resolutions
- misaligned time steps
- hidden resampling

Climate Cube Math makes these explicit:

- spatial alignment is visible
- temporal aggregation is deliberate
- scale is a first-class concern

The goal is not to hide complexity—but to make it legible.

## Where to go next
- [Getting Started / Quickstart](../quickstart.md)
- [Core Verbs](../verbs/index.md)
- [Recipes / How-tos](../howto/index.md)
