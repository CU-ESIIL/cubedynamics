# Climate Cube Math

![Tests](https://github.com/CU-ESIIL/climate_cube_math/actions/workflows/tests.yml/badge.svg) ![Docs](https://github.com/CU-ESIIL/climate_cube_math/actions/workflows/pages.yml/badge.svg)

**A grammar-of-graphics for spatiotemporal environmental data**

Climate Cube Math (also referred to as **CubeDynamics**) is a Python framework for analyzing environmental data as **spatiotemporal cubes**, rather than disconnected maps and time series.

It is designed for scientists and data practitioners who want to reason explicitly about **space, time, scale, and events**—and to do so reproducibly and efficiently, even for large datasets.

---

## Why this project exists

Most environmental datasets already form data cubes:
- climate grids evolving through time
- vegetation indices measured repeatedly over landscapes
- disturbance events unfolding in space and time

Yet most workflows break these dimensions apart:
- spatial analysis in GIS
- temporal analysis in tables
- statistics elsewhere
- visualization last

Climate Cube Math keeps **space and time together**, making spatiotemporal structure a first-class part of the analysis.

---

## What Climate Cube Math enables

- **Spatiotemporal cube operations** (means, variance, anomalies, synchrony)
- **Grammar-based pipelines** using `pipe | verb | verb`
- **Streaming-first analysis** via VirtualCubes for large datasets
- **Event- and hull-based workflows** (fires, droughts, phenology)
- **Integrated visualization** of space–time structure

---

## Minimal example

```python
from cubedynamics import pipe, verbs as v
import cubedynamics as cd

cube = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2022-01-01",
    end="2023-01-01",
)

pipe(cube) | v.anomaly() | v.variance() | v.plot()
```

This pipeline:
- loads a spatiotemporal cube
- computes anomalies through time
- measures variability at each spatial location
- visualizes the result

---

## Documentation

📘 Full documentation website 👉 https://cu-esiil.github.io/climate_cube_math/

Key entry points:
- Concepts – cube abstraction, pipes & verbs, streaming
- Getting Started – first success in minutes
- Capabilities & Verbs – complete textbook-style reference
- Datasets – supported data sources, fields, citations
- Recipes – end-to-end scientific workflows

---

## Installation

```bash
pip install cubedynamics
```

See the documentation for optional extras, large-data workflows, and examples.

---

## Project status & scope

- Active development
- APIs are stabilizing; deprecations follow a warn-first policy
- Focused on spatiotemporal environmental analysis
- Built on top of xarray and related ecosystem tools

See the documentation for the public API and stability guarantees.

---

## Citation

If you use Climate Cube Math in academic work, please cite:

Climate Cube Math. CU ESIIL.  
https://github.com/CU-ESIIL/climate_cube_math

(See the documentation for dataset-specific citations.)

---

## Contributing

Contributions are welcome.
- See CONTRIBUTING.md for development guidelines
- Open issues for bugs, questions, or feature discussions

---

## License

MIT License (see [LICENSE](LICENSE)).
