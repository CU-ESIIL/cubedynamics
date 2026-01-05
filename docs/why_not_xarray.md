# Why Climate Cube Math Exists (Even If You Use xarray)

Climate Cube Math is built on top of the xarray and dask ecosystem. Many workflows can be accomplished directly with xarray alone. This project exists to provide an explicit grammar for spatiotemporal analysis, guardrails for reproducibility, and streaming-first defaults.

## When xarray is enough
- Loading small to medium-sized rasters or netCDF files
- Performing ad hoc calculations in notebooks
- Quick exploratory plots or statistics on slices

## When Climate Cube Math adds value
- Expressing a sequence of spatiotemporal operations as a single, inspectable pipeline
- Maintaining dimension semantics across complex transformations
- Streaming through continental-scale datasets without changing analysis code
- Treating events and masks as first-class volumes in space–time

## Comparison

| Goal | xarray / dask | Climate Cube Math |
| --- | --- | --- |
| Read a dataset and compute a mean | `xr.open_dataset` + `mean` | Same data access, wrapped inside a verb pipeline |
| Keep track of spatial/temporal semantics | Manual dimension handling | Explicit cube dimensions and metadata checks |
| Reproduce a multi-step workflow | Notebooks or scripts | Declarative pipes and verbs with inspectable stages |
| Stream data at scale | Requires chunking strategy per workflow | VirtualCubes stream automatically through the same verbs |
| Document intent | Comments and naming conventions | Grammar terms (verbs, pipes) map to documented concepts |

Climate Cube Math does not replace xarray. It adds an analysis grammar so that large-scale, spatiotemporal workflows stay coherent, testable, and readable.

## The cube grammar at a glance
![Cube grammar overview](assets/diagrams/grammar_overview.png)

See the [Concepts](concepts/index.md) page for the full grammar description and terminology.
