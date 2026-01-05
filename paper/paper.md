---
title: "Climate Cube Math: streaming-first tools for spatiotemporal climate data cubes in Python"
authors:
  - name: Ty Tuff
    affiliation: 1
affiliations:
  - name: Environmental Data Science Innovation & Inclusion Lab (ESIIL), University of Colorado Boulder
    index: 1
date: 2024-08-21
bibliography: paper.bib
---

# Summary

Climate Cube Math (also referred to as **CubeDynamics**) is a Python library that treats environmental observations as spatiotemporal **data cubes**. It layers a grammar-of-graphics inspired pipeline (`pipe | verb | verb`) on top of xarray and dask so users can compose analyses that stream or compute in memory, preserve spatial and temporal structure, and remain reproducible across datasets.

# Statement of need

Environmental researchers routinely work with gridded climate archives, remotely sensed vegetation indices, and event footprints that span large spatial extents and long time series. These datasets are often too large to load eagerly, and ad hoc workflows that split space and time across tools make it hard to reproduce results or share exact transformations. Climate Cube Math addresses these pain points by providing a **streaming-first cube abstraction (VirtualCube)** and a concise grammar for chaining operations. Users can lazily compose transformations, cache intermediate cubes, and export derived products without rewriting code for each dataset. The library targets climate and Earth system scientists, ecologists, and geospatial data practitioners who need to quantify dynamics through space and time while keeping IO, computation, and provenance manageable.

# Functionality

Climate Cube Math builds on established scientific Python tools and adds a cube-oriented grammar that emphasizes readability and streaming. Key capabilities include:

- **Cube construction and streaming** through the `VirtualCube` interface for loading climate and vegetation products without eager reads.
- **Grammar-based pipelines** using `pipe` plus composable verbs for anomalies, variance, rolling statistics, and other spatiotemporal diagnostics.
- **Event- and hull-based workflows** that keep space–time structure intact for comparisons inside and outside footprints such as fires or droughts.
- **Visualization verbs** that preserve cube semantics while plotting or mapping derived results.
- **Caching and export helpers** to persist cubes or render diagnostics for downstream dashboards.

Further details and verb references are documented in the project guide.

# Example use

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2022-01-01",
    end="2023-01-01",
)

result = (
    pipe(cube)
    | v.anomaly()
    | v.variance()
    | v.plot(title="Spatiotemporal variance")
)
```

The same pipeline works for local arrays or streamed cubes, enabling reproducible analyses across datasets.

# Related work

Climate Cube Math relies on the labeled array model and chunked computation provided by xarray [@hoyer2017xarray] and dask [@dask], but introduces a cube-first grammar that centers space–time structure and streaming IO. It complements, rather than replaces, array processing frameworks by offering a domain-specific set of verbs and event-aware workflows tailored to environmental change analysis.

# Acknowledgements

Development is supported by the Environmental Data Science Innovation & Inclusion Lab (ESIIL) at the University of Colorado Boulder.
