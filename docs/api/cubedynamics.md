# `cubedynamics` API Reference
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

This page documents the main public modules and functions of the
`cubedynamics` package. The API is auto-generated from the docstrings
using `mkdocstrings`.

## Data loading

::: cubedynamics.data.sentinel2
::: cubedynamics.data.gridmet
::: cubedynamics.data.prism

## Pipe + verbs

- `cubedynamics.pipe`: exposes the lightweight `Pipe` helper used throughout the documentation. Import via `from cubedynamics import pipe`.
- `cubedynamics.verbs`: namespace of pipe-able callables (import with `from cubedynamics import verbs as v`). Includes transforms (`v.anomaly`), statistics (`v.mean`, `v.variance`, `v.zscore`), IO helpers, and visualization verbs such as `v.show_cube_lexcube`. New 2025 viewers include `v.plot(kind="cube")` for rotatable HTML cubes and `v.map()` for MapGL/pydeck map views. The exported `v.correlation_cube` factory is reserved for a future release and currently raises `NotImplementedError`.
- `cubedynamics.show_cube_lexcube`: functional helper that mirrors the verb and renders a Lexcube widget without entering a pipe chain.

## Vegetation indices

::: cubedynamics.indices.vegetation

## Statistics: anomalies and rolling windows

::: cubedynamics.stats.anomalies
::: cubedynamics.stats.rolling
::: cubedynamics.stats.correlation
::: cubedynamics.stats.tails
::: cubedynamics.stats.spatial

## Visualization helpers

::: cubedynamics.viz.lexcube_viz
::: cubedynamics.viz.qa_plots

## Utilities

::: cubedynamics.utils.chunking
::: cubedynamics.utils.reference
