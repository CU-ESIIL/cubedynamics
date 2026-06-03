# Why CubeDynamics?

CubeDynamics is often mistaken for:

- another `xarray` wrapper
- another Earth observation cube
- another Open Data Cube implementation
- another STAC interface
- another visualization package

It is none of those.

## The Strategic Role

Most systems in this ecosystem focus on one of these questions:

- How do I store data?
- How do I index data?
- How do I retrieve data?
- How do I build a cube from remote assets?

CubeDynamics focuses on a different question:

> How do I compute on a stream of environmental data?

That makes it a computation layer, not a storage layer.

## Competitive Landscape

| Project | Focus |
| --- | --- |
| `xarray` | Multidimensional arrays |
| Open Data Cube | Earth observation storage and indexing |
| `cubo` | On-demand Earth-system cubes from STAC |
| Google Earth Engine | Planetary-scale geoprocessing |
| CubeDynamics | Streaming environmental computation |

These projects are complementary. CubeDynamics benefits from them, but its purpose is different.

## Architectural Distinction

CubeDynamics is organized around this flow:

```text
Data Sources
    ↓
Streaming Interface
    ↓
Grammar of Computation
    ↓
Scientific Results
```

Not this:

```text
Data Sources
    ↓
Storage System
    ↓
Cube
```

The distinction is practical:

- you can operate on data without building a storage platform first
- you can keep workflows lightweight in notebooks
- you can move the same grammar into cloud and agent-driven execution

## Agent-Native By Design

CubeDynamics is intentionally simple enough that both humans and AI systems can reason about the same workflow.

That means:

- scientists and AI agents use the same streaming interface
- the same verbs appear in notebooks, scripts, and orchestration workflows
- the same abstractions can be debugged by a researcher or executed by an agent

## What To Read Next

- [Streaming Environmental Data](streaming/index.md)
- [Grammar of Streaming](grammar/index.md)
- [Workflows](workflows/index.md)
