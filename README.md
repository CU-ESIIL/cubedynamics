# climate_cube_math

## What is CubeDynamics?

CubeDynamics (the climate_cube_math package) is a spatiotemporal analysis system for environmental science. It treats climate, NDVI, and other geospatial datasets as data cubes—variables defined over latitude, longitude, and time:

V(lat, lon, time)

This cube representation preserves spatial and temporal coherence and supports scientific questions that require full spatiotemporal context.

## Why use a cube-based framework?

Environmental questions are rarely purely spatial or purely temporal. They depend on patterns that unfold across both:

- drought synchrony
- seasonal and interannual variability
- disturbance recovery
- climate–vegetation coupling
- propagating anomalies
- compound extreme events

CubeDynamics provides a cube-native grammar of verbs so that these analyses can be expressed directly and clearly.

## Installation

The easiest way to get started is with conda and the provided environment file:

```bash
conda env create -f envs/cube-env.yml
conda activate cube-env
pip install --no-deps "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

See [INSTALL.md](INSTALL.md) for detailed instructions, verification steps, and Docker/cloud notes.

## 10-minute Tour (Start Here)

See the full Quickstart guide:
👉 https://cu-esiil.github.io/climate_cube_math/quickstart/

Minimal example:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    lat=40.0, lon=-105.25,
    start="2020-01-01", end="2020-12-31",
)

pipe(ndvi) | v.anomaly() | v.plot()
```

## Documentation

- [Quickstart](https://cu-esiil.github.io/climate_cube_math/quickstart/)
- [Concepts](https://cu-esiil.github.io/climate_cube_math/concepts/)
- [How-to Guides](https://cu-esiil.github.io/climate_cube_math/howto/)
- [Visualization](https://cu-esiil.github.io/climate_cube_math/viz/)
- [API Reference](https://cu-esiil.github.io/climate_cube_math/api/)

Full docs: https://cu-esiil.github.io/climate_cube_math/

## Contributing

See: docs/dev/contributing.md

Developer invariants for the cube viewer and verbs: docs/dev/cube_viewer_invariants.md
