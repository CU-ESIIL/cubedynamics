# Why CubeDynamics exists alongside xarray

CubeDynamics is built on the xarray and Dask ecosystem. Many workflows can and
should be accomplished directly with xarray. CubeDynamics adds an inspectable
environmental grammar when a researcher wants a short analytical expression to
retain source identity, authored order, semantic state, and an ordered trace.

## When xarray is enough
- Loading small to medium-sized rasters or netCDF files
- Performing ad hoc calculations in notebooks
- Quick exploratory plots or statistics on slices

## When CubeDynamics adds value
- Expressing a sequence of spatiotemporal operations as a single, inspectable pipeline
- Recording how dimensions and semantic objects change across transformations
- Explaining meaning-changing or information-removing operation order
- Connecting source-qualified nouns to provenance and bounded QA evidence
- Reusing the same grammar with in-memory, Dask-backed, or bounded streaming objects
- Treating events and masks as first-class volumes in space–time

## Comparison

| Goal | xarray / dask | CubeDynamics |
| --- | --- | --- |
| Read a dataset and compute a mean | `xr.open_dataset` + `mean` | Same data access, wrapped inside a verb pipeline |
| Keep track of spatial/temporal semantics | Explicit code, metadata, and user discipline | Semantic state plus dimensions and metadata checks |
| Reproduce a multi-step workflow | Notebooks or scripts | Authored pipes and verbs with an ordered trace |
| Work lazily or stream | Dask and source-specific access | The same grammar can preserve supported Dask or VirtualCube behavior; transport limits remain source-specific |
| Document intent | Comments, names, and explicit xarray calls | Nouns, verbs, parameters, state, and trace map to documented contracts |

CubeDynamics does not replace or outperform xarray by definition. It adds an
analysis grammar so that a reader can recover what a concise environmental
statement asked. That grammar does not choose the right source, remove bias,
certify observations, or make a result fit for a decision.

## The cube grammar at a glance

`pipe(cube) | verb(...) | verb(...)` keeps each analytical step visible. Calling
`.unwrap()` retrieves the resulting object without forcing lazy data to compute.

See [Scientific inspectability](concepts/scientific_inspectability.md) for the
research framing and [Concepts](concepts/index.md) for broader terminology.
