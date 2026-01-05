# Concepts Overview

CubeDynamics is organized into three conceptual layers that compose to produce
climate lexcubes:

1. **Sources** – streaming adapters for Sentinel-2, PRISM, gridMET, and other
   gridded datasets. Each returns `xarray.Dataset` objects with shared
   `(time, y, x)` axes.
2. **Cube math primitives** – functions inside `cubedynamics.stats`,
   `cubedynamics.indices`, and `cubedynamics.viz` that compute anomalies,
   correlations, and derived indicators.
3. **Pipelines & exports** – recipes that connect cubes to dashboards or models
   (NetCDF/Zarr writers, QA plots, and asynchronous workflows).

The sections below summarize how these layers interact.

## Source adapters

Every loader enforces consistent naming (time, y, x, band) and metadata (CRS,
units, history). Streaming-first behavior is preferred: data arrive chunked via
HTTP range requests, STAC assets, or cloud object storage signed URLs. Offline
fallbacks download only the required slices.

## Lexcube builders

Lexcubes are multi-dimensional cubes that store derived metrics such as
variance, synchrony, or NDVI anomalies along the same axes as the source data.
They can be nested (e.g., a `dataset` containing multiple diagnostics) and are
ready for export.

## Analysis & visualization

Downstream helpers provide rolling correlation, tail dependence, QA plots, and
hooks for interactive dashboards. See [Climate cubes](climate_cubes.md) and
[Correlation cubes](howto/correlation_cubes.md) for example notebooks and API usage.

## Verb Grammar & Docstring Conventions

CubeDynamics verbs follow a verb-first grammar so docstrings read like concise
instructions. A **verb** is any callable that consumes a cube-like object and
returns a cube so it can participate in a pipe. Verbs can be invoked directly
(`verb(cube, ...)`) or returned as pipe-ready callables (`pipe(cube) | verb(...)`).

- **Transform verbs** map one cube to another cube with the same dimensions.
- **Reducer verbs** collapse one or more dimensions (often time) while
  preserving a cube shape; they must document which dimensions survive.
- **Annotating verbs** return the incoming cube with additional attributes
  attached; the array values are unchanged.
- **Side-effect verbs** return the original cube while emitting a visualization
  or other observable output.

Dimension expectations always default to `(time, y, x)` unless documented
otherwise. If only a subset is provided, the missing axes are inferred from the
input object's metadata; verbs must state whether they require explicit dims or
can infer them. Streaming and laziness are preserved whenever inputs are Dask
arrays or `VirtualCube` instances; verbs are expected to avoid materialization
unless their semantics require it.

Minimal usage examples:

```
# Direct call
cube_out = v.mean(cube_in, dim="time")

# Pipe-ready call
cube_out = pipe(cube_in) | v.mean(dim="time") | v.zscore(dim="time")
```

Docstrings adhere to a shared template with a summary line, the grammar
contract (direct-call vs pipe-ready expectations), parameters, return value,
notes on dimension or streaming behavior, examples, and cross-references. Each
verb's docstring uses imperative, verb-first phrasing to reinforce the grammar
described above.
