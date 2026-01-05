# Capabilities Overview

This section answers: **What can Climate Cube Math do once your data is in a cube?** Use it to scan the verb surface and decide which operations to combine.

In this section you'll find:
- Supported inputs for `pipe(...)` and how they map into cubes or geometries.
- Highlights of structural, statistical, event, and visualization verbs.
- Example pipelines that show how verbs compose.

Key links:
- [Verbs & Examples](textbook_verbs.md)
- [Pipe and verbs](../concepts/pipe_and_verbs.md)
- [Cube viewer (v.plot)](../viz/cube_viewer.md)
- [Event extraction and vases](../recipes/s2_tail_dep_center.md)

## Data sources you can pipe
`pipe(...)` accepts inputs ranging from xarray objects to helper loaders and VirtualCubes. Use [What is a cube?](../concepts/cubes.md) and the dataset pages to choose the right starting point.

## Core verbs at a glance
Verbs progress from inspection to aggregation, then to statistics, events, and visualization. Examples include:
- Structural helpers such as `apply`, `flatten_space`, and `to_netcdf`.
- Statistical verbs like `mean`, `variance`, `anomaly`, and `zscore`.
- Event-aware verbs including `extract`, `vase`, and fire-focused plots.
- Visualization verbs such as `plot`, `map`, and `climate_hist` that return the original object so pipelines can continue.

## Putting it together
Combine data loaders, verbs, and viewers to build readable pipelines:

```python
from cubedynamics import pipe, verbs as v

(pipe(cube)
 | v.anomaly()
 | v.variance(dim="time", keep_dim=True)
 | v.plot(title="Spatiotemporal Variance")
)
```

The same grammar works whether you stream data or work in memory.

## Read next
- [Getting Started](../quickstart.md)
- [Verbs & Examples](textbook_verbs.md)
- [Datasets Overview](../datasets/index.md)
- [Recipes Overview](../recipes/index.md)
- [Visualization Overview](../viz/index.md)
