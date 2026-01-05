# Public API & Scope

This page describes the supported, user-facing surface of `cubedynamics` and how it is intended to evolve. Anything not listed here should be treated as internal and subject to change between releases.

## Canonical namespace

Import the library as:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
```

`cubedynamics` is the only supported top-level namespace. Symbols imported through `cd.*` follow the stability guidance below.

## Dataset loaders

These helpers create xarray-backed cubes or streaming-friendly structures. Network access may be required depending on the data source.

- `load_gridmet_cube`
- `load_prism_cube`
- `load_sentinel2_cube`
- `load_sentinel2_bands_cube`
- `load_sentinel2_ndvi_cube`
- Legacy aliases kept for compatibility (emit deprecation warnings):
  - `load_s2_cube`
  - `load_s2_ndvi_cube`
  - `load_sentinel2_ndvi_zscore_cube`

## Pipe and verbs

- `pipe` wraps any xarray `DataArray` or `Dataset` so verbs can be chained via the `|` operator.
- `verbs` is the canonical namespace for operations. Import as `from cubedynamics import verbs as v`.
- Core verbs include statistical reducers (`v.mean`, `v.variance`, `v.anomaly`, `v.zscore`), time filters (`v.month_filter`), correlation helpers (`v.correlation_cube`), NDVI utilities (`v.ndvi_from_s2`), flattening (`v.flatten_cube`, `v.flatten_space`), and visualization verbs (`v.plot`, `v.plot_mean`, `v.show_cube_lexcube`).
- Visualization verbs also cover vase-aware helpers (`v.vase`, `v.vase_extract`, `v.vase_mask`) that preserve hull metadata on cubes.

## Visualization entry points

For quick plots without a pipe chain use:

- `cubedynamics.plot(cube, time_dim="time", cmap="viridis")` – convenience wrapper around `v.plot`.
- `cubedynamics.viz` and `cubedynamics.viewers` expose lower-level components and templates for custom rendering; they are considered internal unless routed through verbs.

## What is internal?

Treat the following as implementation details that may change without notice:

- Modules under `cubedynamics.ops`, `cubedynamics.streaming`, `cubedynamics.ops_fire`, `cubedynamics.ops_io`, and `cubedynamics.viewers`.
- Demo helpers such as `demo`/`demo_vase` and example notebooks.
- Private utilities (`cubedynamics.utils`, `cubedynamics.config`, `cubedynamics.progress`, etc.).

Internal modules may be refactored or renamed as the streaming architecture stabilizes. Prefer accessing functionality through the documented loaders, `pipe`, and `verbs`.

## Stability policy

CubeDynamics follows semantic versioning for the public surface described above:

- **Patch releases (`0.x.y`)**: bug fixes only; no breaking changes to documented public symbols.
- **Minor releases (`0.y`)**: may add new verbs or loaders; existing public APIs remain compatible, but internal modules can change.
- **Major releases (`1.0` and beyond)**: may remove deprecated aliases after advance notice.

Deprecated entry points will emit `DeprecationWarning` with guidance on the replacement and a planned removal version. Legacy aliases remain available until the stated removal window.
