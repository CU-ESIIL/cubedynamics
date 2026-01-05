# Getting Started

This guide gets you to a first working cube and pipeline as quickly as possible, while showing how the same code scales up when datasets are large.

## Installation

Install from PyPI:

```bash
pip install cubedynamics
```

Or install the latest main branch:

```bash
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

CubeDynamics runs anywhere `xarray` runs: laptops, HPC clusters, or hosted notebooks.

## Your First Cube

Most users start by loading a cube from an existing dataset. For example, this creates a precipitation cube from PRISM:

```python
import cubedynamics as cd

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)
```

Inspect the structure to confirm dimensions and metadata:

```python
cube.dims
cube.shape
cube.attrs
```

## Your First Pipeline

Pipelines are built with the pipe (`|`) operator and a grammar of verbs:

```python
from cubedynamics import pipe, verbs as v

result = pipe(cube) | v.mean(dim="time") | v.plot()
```

This example computes the mean through time for every location in the cube and plots the result. You can swap in different verbs (e.g., `v.anomaly()`, `v.variance()`, `v.month_filter([6, 7, 8])`) without changing the pipeline structure.

## Loading Real Datasets

The same pattern works for other datasets shipped with CubeDynamics. The `load_prism_cube` call above can be expanded to longer time ranges or larger spatial domains, and other loaders follow the same conventions for inputs like latitude, longitude, date ranges, and variable names.

## Scaling Up Without Changing Code

Large requests automatically stream as **VirtualCubes**, so you do not have to rewrite your pipeline when datasets exceed memory. VirtualCubes:

- represent a cube without materializing it upfront
- stream tiles of data through the same verbs
- keep your code and semantics identical at small or large scales

## Working With Large Datasets

If you request a larger area of interest or longer date range, the loader silently returns a VirtualCube that streams tiles through the same verbs. You can inspect and control streaming when needed:

```python
ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="1970",
    end="2020",
    streaming_strategy="virtual",
    time_tile="5y",
)
print(ndvi)           # shows that it is a VirtualCube
ndvi.debug_tiles()    # prints time + space tiles
ndvi.materialize()    # forces full load; only for small areas
```

Try smaller `time_tile` values or reduced spatial bounds if you see slow progress or rate limits.

When a request is too large for a normal in-memory cube, CubeDynamics:

- splits the timeline into tiles (for example, five-year windows)
- splits the area of interest into spatial tiles when needed
- streams each tile through the verbs, tracking running statistics like variance or mean
- returns a normal-looking DataArray/Dataset at the end

## Common Pitfalls

- Make sure the requested variable name matches the dataset.
- Verify dimensions before running large analyses so operations occur over the intended axis.
- Use streaming defaults for big pulls instead of forcing full materialization.

## Where to go next

- **Concepts**
  - [What is a cube?](concepts/cubes.md)
  - [Pipe & verbs](concepts/grammar.md)
  - [VirtualCubes](concepts/virtual_cubes.md)

- **Recipes / How-tos**
  - [Minimal NDVI vignette](vignette_minimal_ndvi.md)
  - [NDVI anomalies](howto/ndvi_anomalies.md)
  - [Climate variance](howto/climate_variance.md)
  - [Correlation cubes](howto/correlation_cubes.md)

- **Visualization**
  - [Cube viewer (`v.plot`)](viz/cube_viewer.md)
  - [Map viewer (`v.map`)](viz/maps.md)

- **API Reference**
  - [API overview](api/index.md)

CubeDynamics provides a unified, cube-native way to work with spatiotemporal environmental data—simple enough for quick exploration, powerful enough for large-scale scientific analysis.
