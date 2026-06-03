# Getting Started

This guide gets you to a first working streaming workflow as quickly as possible, while showing how the same code scales up when datasets are large.

CubeDynamics is not a storage platform or visualization package. It sits above data sources and gives you a consistent way to compute on environmental streams.

Scientists and AI agents use the same streaming interface, so the workflow you learn here is the same one that scales into notebooks, cloud jobs, and agent-orchestrated runs.

## Installation

Install from PyPI:

```bash
pip install cubedynamics
```

Or install the latest main branch:

```bash
pip install "git+https://github.com/CU-ESIIL/cubedynamics.git@main"
```

CubeDynamics runs anywhere `xarray` runs: laptops, HPC clusters, or hosted notebooks.

## Your First Stream

Most users start by loading a cube-like stream from an existing dataset. For example, this creates a precipitation cube from PRISM:

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

This example computes the mean through time for every location in the stream-backed cube and plots the result. You can swap in different verbs (e.g., `v.anomaly()`, `v.variance()`, `v.month_filter([6, 7, 8])`) without changing the pipeline structure.

The important idea is that the cube is not the product by itself. The product is the combination of:

- a streaming interface to environmental data
- a stable computation grammar built from `pipe(...)` and verbs

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
- For event windows, request daily frequency (`freq="D"`)—monthly codes like `"MS"`/`"ME"` over short ranges can return an empty time axis.
- Leave `allow_synthetic=False` unless you explicitly want demo data; provenance (`source`, `is_synthetic`, `backend_error`) on cubes will confirm what you received.
- A "streaming backend unavailable" warning means CubeDynamics fell back to a download backend. Install optional dependencies or check network access before re-running if you need streaming.

## Where to go next

- [Why CubeDynamics?](why_cubedynamics.md)
- [Streaming Environmental Data](streaming/index.md)
- [Grammar of Streaming](grammar/index.md)
- [Workflows](workflows/index.md)
- [Datasets](datasets/index.md)
- [Cube viewer (`v.plot`)](viz/cube_viewer.md)

CubeDynamics provides a unified way to compute on environmental data streams: simple enough for quick exploration, strong enough for larger scientific and agent-executed workflows.
