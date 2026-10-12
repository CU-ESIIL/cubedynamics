# Related work & ecosystem

CubeDynamics builds on a broad ecosystem of Earth system data cube initiatives. We focus on a grammar of analysis—`pipe(cube) | verbs`—while interoperating with storage and visualization tools.

## Earth System Data Cubes

Projects such as the Earth System Data Cube (ESDC), DeepESDL, and `xcube` popularized the idea of spatiotemporal grids stored as `xarray` datasets for analysis and AI. CubeDynamics aligns with this paradigm but keeps cubes local and analysis-ready so you can request any AOI/time range without waiting for global precomputes.

## Open Data Cube & stackstac/odc-stac/cubo

Open Data Cube and its STAC-focused companions (`stackstac`, `odc-stac`, `cubo`) provide scalable ingestion pipelines for satellite imagery. CubeDynamics happily consumes cubes produced by these systems—once the data are in `xarray`, the same `pipe(cube) | verbs` grammar applies. Use `cubo.create` or `odc-stac` notebooks to assemble Sentinel-2/landsat cubes, then bring them into CubeDynamics for anomaly detection.

## Lexcube

Lexcube offers interactive 3D visualization for `(time, y, x)` arrays. CubeDynamics exposes a `v.show_cube_lexcube` verb and helper functions so every analysis can surface an exploratory widget mid-pipeline. The docs use placeholder screenshots while the static site hosts instructions for running live notebooks.

## Ecosystem summary

> CubeDynamics builds on the Earth System Data Cube paradigm: spatiotemporal grids stored as `xarray` cubes for analysis and AI. It differs from frameworks like Open Data Cube or Earth System Data Lab by focusing on a *grammar of analysis* (pipe + verbs) rather than on data storage or infrastructure. We treat any `xarray` cube—whether it comes from PRISM, gridMET, Sentinel-2 via Cubo, or ESDC—as a first-class citizen in the same `pipe(cube) | verbs` interface.

Future updates will add explicit citations and links once the corresponding publications are finalized.

## Longer manuscript context

The [design origins and related systems companion](manuscript_context.md)
retains the manuscript's personal design history, technical precedents,
contribution pathways, and explicitly prospective synthesis and agent ideas.
