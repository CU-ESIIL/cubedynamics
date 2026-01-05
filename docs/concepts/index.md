# Concepts Overview

This section answers: **How does the cube grammar represent space, time, and operations?** Use it to align on terminology before picking verbs, datasets, or recipes.

In this section you'll find:
- How the cube grammar keeps dimensions explicit across a pipeline.
- The relationship between cubes, pipes, verbs, and VirtualCubes.
- Pointers to glossary terms and comparisons to other libraries.

Key links:
- [What is a cube?](cubes.md)
- [Pipe and verbs](pipe_and_verbs.md)
- [VirtualCubes](virtual_cubes.md)
- [Glossary](glossary.md)
- [Why not xarray?](../why_not_xarray.md)
- Orientation aids: [Documentation Overview](../overview.md) and [Reading Paths](../reading_paths.md)

## Cube grammar pipeline
Climate Cube Math expresses analysis as a sequence of verbs connected by pipes, operating on explicit cube dimensions. This grammar keeps space, time, and scale visible throughout a workflow and ensures that intermediate steps remain inspectable.

![Cube grammar pipeline](../assets/diagrams/cube_grammar_pipeline.png)

## Dimensions stay explicit
At its core, Climate Cube Math works with xarray-backed DataArrays but applies strong semantics:
- named spatial and temporal dimensions
- metadata about resolution, alignment, and scale
- consistency enforced across operations

The goal is to avoid hidden assumptions about where operations run. Dimensions are visible and intentional, making workflows easier to reason about and share.

## Streaming via VirtualCubes
Environmental datasets are often too large to load into memory. VirtualCubes represent a cube without materializing it and stream chunks through analysis pipelines. Code stays the same whether you stream or work in memory, so scale becomes a configuration choice.

## Pipes and verbs
Instead of chaining methods, you compose verbs with `pipe(...)` to build declarative workflows:

```python
from cubedynamics import pipe, verbs as v

pipe(cube) | v.mean() | v.rolling() | v.plot()
```

Pipelines remain inspectable objects, making it straightforward to debug, document, or extend analyses.

## Read next
- [Getting Started](../quickstart.md)
- [Verbs & Examples](../capabilities/textbook_verbs.md)
- [Datasets Overview](../datasets/index.md)
- [Recipes Overview](../recipes/index.md)
- [Visualization Overview](../viz/index.md)
