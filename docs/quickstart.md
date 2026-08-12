# Getting Started

This guide gets you to a first working grammar pipeline without a download,
credential, or optional renderer. After that, the same composition model can be
connected to streaming integrations.

CubeDynamics is not a storage platform or visualization package. It sits above data sources and gives you a consistent way to compute on environmental streams.

The stable lesson is `pipe(cube) | verb() | verb()`: the cube's source is a
separate concern.

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

## Your first cube

Start with a deterministic xarray object so the example is reproducible
everywhere:

```python
import numpy as np
import pandas as pd
import xarray as xr

cube = xr.DataArray(
    np.arange(72, dtype=float).reshape(12, 2, 3),
    dims=("time", "y", "x"),
    coords={"time": pd.date_range("2025-01-01", periods=12, freq="MS")},
    name="environmental_signal",
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

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()
```

This example computes an anomaly at every voxel and then a spatial mean for
each time step. You can swap in `v.variance`, `v.zscore`, or
`v.month_filter([6, 7, 8])` without changing the pipeline structure.

The important idea is that the cube is not the product by itself. The product is the combination of:

- a streaming interface to environmental data
- a stable computation grammar built from `pipe(...)` and verbs

## Connect a real-data integration

Once the grammar is clear, an adapter can supply the cube. This PRISM example
requires network access and is therefore not part of the offline vignette test:

```python
import cubedynamics as cd

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2020-01-01",
    end="2020-12-31",
    variable="ppt",
)

result = (pipe(cube) | v.anomaly() | v.variance()).unwrap()
```

Other maintained adapters follow the same separation: obtain a cube, then
compose verbs.

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

- [Run the publication vignettes](vignettes/index.md)
- [Understand core versus project verbs](concepts/core_and_projects.md)
- [Write a custom verb project](extending/custom_verbs.md)
- [Why CubeDynamics?](why_cubedynamics.md)
- [Streaming Environmental Data](streaming/index.md)
- [Grammar of Streaming](grammar/index.md)
- [Workflows](workflows/index.md)
- [Datasets](datasets/index.md)
- [Cube viewer (`v.plot`)](viz/cube_viewer.md)

CubeDynamics provides a unified way to compute on environmental data streams: simple enough for quick exploration, strong enough for larger scientific and agent-executed workflows.
