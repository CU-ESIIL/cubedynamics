# Getting Started

CubeDynamics (`cubedynamics`) runs anywhere `xarray` does—laptops, clusters, or hosted notebooks. Use this guide to install the package, spin up the first pipe chain, and know where the notebook vignette lives.

## Installation

### Install from GitHub today

Grab the latest commits straight from the main branch. Installing inside a virtual environment (via `venv` or Conda) is recommended but optional.

```bash
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

### Install from PyPI once released

As soon as the first release is uploaded to PyPI you will be able to run:

```bash
pip install cubedynamics
```

Until then, use the GitHub install above for the working package.

## First pipeline in a notebook

1. Install CubeDynamics in your notebook environment (see the command above).
2. Create a tiny in-memory cube. In CubeDynamics a “cube” is simply an `xarray.DataArray` or `xarray.Dataset` that carries time/space coordinates.
3. Chain a few verbs with the pipe syntax:

```python
import numpy as np
import xarray as xr
import cubedynamics as cd

# 1D time series cube – the same pattern works for multi-dimensional data
time = np.arange(6)
values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

cube = xr.DataArray(
    values,
    dims=["time"],
    coords={"time": time},
    name="example_variable",
)

result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.variance(dim="time")
).unwrap()

float(result.values)
```

This pipeline is dimension-agnostic—the verbs accept any axes you provide. The `.unwrap()` call returns the final `xarray` object so it behaves like any other DataArray.

## Beyond the minimal example

- Read the [Pipe Syntax & Verbs](pipe_syntax.md) page for more callables such as `month_filter`, `to_netcdf`, and how to author your own verbs.
- Explore future climate streaming examples (PRISM/gridMET/NDVI) as they land in the docs and notebooks.
- Run the full [CubeDynamics Quickstart notebook](https://github.com/CU-ESIIL/climate_cube_math/blob/main/notebooks/quickstart_cubedynamics.ipynb) for a ready-made walkthrough that matches this guide.
