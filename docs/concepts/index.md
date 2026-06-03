# Concepts Overview

This section answers: **How does the CubeDynamics computation model represent space, time, and operations?** Use it to align on terminology before picking verbs, datasets, or recipes.

CubeDynamics is not another storage layer or another visualization package. It is a grammar of streaming environmental computation built to sit above many data systems.

In this section you'll find:
- How the streaming-first grammar keeps dimensions explicit across a pipeline.
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
CubeDynamics expresses analysis as a sequence of verbs connected by pipes, operating on explicit cube dimensions. This grammar keeps space, time, and scale visible throughout a workflow and ensures that intermediate steps remain inspectable.

Scientists and AI agents can both reason about the same pipeline because the abstraction is intentionally small and explicit.

![Cube grammar pipeline](../assets/diagrams/cube_grammar_pipeline.png)

## Dimensions stay explicit
At its core, CubeDynamics works with xarray-backed DataArrays but applies strong semantics:
- named spatial and temporal dimensions
- metadata about resolution, alignment, and scale
- consistency enforced across operations

The goal is to avoid hidden assumptions about where operations run. Dimensions are visible and intentional, making workflows easier to reason about, share, and orchestrate.

## Streaming via VirtualCubes
Environmental datasets are often too large to load into memory. VirtualCubes represent a cube without materializing it and stream chunks through analysis pipelines. Code stays the same whether you stream or work in memory, so scale becomes a configuration choice rather than a rewrite.

## Pipes and verbs
Instead of chaining methods, you compose verbs with `pipe(...)` to build declarative workflows:

```python
from cubedynamics import pipe, verbs as v

pipe(cube) | v.mean() | v.rolling() | v.plot()
```

Pipelines remain inspectable objects, making it straightforward to debug, document, extend analyses, or hand the same workflow to an agent.

## Read next
- [Getting Started](../quickstart.md)
- [Verbs & Examples](../capabilities/textbook_verbs.md)
- [Datasets Overview](../datasets/index.md)
- [Recipes Overview](../recipes/index.md)
- [Visualization Overview](../viz/index.md)
