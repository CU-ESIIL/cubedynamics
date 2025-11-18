# CubeDynamics (`cubedynamics`)

CubeDynamics is a streaming-first climate cube math library with ggplot-style piping. It brings high-resolution climate archives (PRISM, gridMET, NDVI, and more) directly into your workflows so you can compose anomaly, synchrony, and correlation cubes without mirroring entire datasets.

## Features

- **Streaming PRISM/gridMET/NDVI climate data** for immediate analysis without bulk downloads.
- **Climate variance, correlation, trend, and synchrony cubes** that run on `xarray` objects and scale from laptops to clusters.
- **Pipe system** – build readable cube workflows with `pipe(cube) | anomaly() | variance()` syntax inspired by ggplot and dplyr.
- **Modular verbs under `cubedynamics.ops`** so transforms, stats, and IO live in focused modules.
- **Cloud-ready architecture** that embraces chunked processing, lazy execution, and storage backends like NetCDF or Zarr.

## Installation

### Install from GitHub (current, recommended)

Install the `cubedynamics` package directly from the `main` branch to get the latest commits:

```bash
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

### Install from PyPI (future)

Once the first release is published to PyPI, installing will be as simple as:

```bash
pip install cubedynamics
```

Until that upload happens the PyPI name is reserved but unavailable.

## Quickstart

This example runs in a fresh Jupyter notebook that only has `numpy`, `xarray`, and `cubedynamics` installed.

```python
import numpy as np
import xarray as xr
import cubedynamics as cd

# Create a tiny example climate "cube" as a 1D time series
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

print("Variance of anomalies along time:", float(result.values))
```

### Using the pipe system

- `cd.pipe(value)` wraps an `xarray` object in a `Pipe` so it can be chained.
- Each verb is a factory. Calling `cd.anomaly(dim="time")` returns a callable that will run inside the pipe.
- The `|` operator forwards the wrapped cube through each verb in sequence.
- `.unwrap()` returns the final `xarray` object so you can inspect the result or continue working outside the pipe.

## API Overview

- `pipe`
- `anomaly`
- `month_filter`
- `variance`
- `correlation_cube` (stub)
- `to_netcdf`

More verbs live under `cubedynamics.ops.transforms`, `cubedynamics.ops.stats`, and `cubedynamics.ops.io`. Each verb returns a callable object that receives the upstream cube when used inside a pipe chain.

## Philosophy

- **Streaming-first design** – CubeDynamics emphasizes adapters that yield data as soon as it is available so analyses can begin immediately.
- **Pipe chaining** – The `Pipe` helper makes cube math declarative: each verb describes *what* to do, and the pipe handles *when* to run it.
- **xarray-compatible processing** – Every verb consumes/produces `xarray.DataArray` or `xarray.Dataset` objects, making it easy to interoperate with the broader ecosystem.

Visit https://cu-esiil.github.io/climate_cube_math/ for full documentation, concepts, and the latest changelog.
