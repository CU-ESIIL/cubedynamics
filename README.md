# CubeDynamics (`cubedynamics`)

CubeDynamics is a streaming-first climate cube math library with ggplot-style piping. It brings high-resolution climate archives (PRISM, gridMET, NDVI, and more) directly into your workflows so you can compose anomaly, synchrony, and correlation cubes without mirroring entire datasets.

## Features

- **Streaming PRISM/gridMET/NDVI climate data** for immediate analysis without bulk downloads.
- **Climate variance, correlation, trend, and synchrony cubes** that run on `xarray` objects and scale from laptops to clusters.
- **Pipe system** – build readable cube workflows with `pipe(cube) | anomaly() | variance()` syntax inspired by ggplot and dplyr.
- **Modular verbs under `cubedynamics.ops`** so transforms, stats, and IO live in focused modules.
- **Cloud-ready architecture** that embraces chunked processing, lazy execution, and storage backends like NetCDF or Zarr.

## Installation

### Install from GitHub (current)

```bash
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

### Install after PyPI release

```bash
pip install cubedynamics
```

## Quickstart (new pipe syntax)

```python
import cubedynamics as cd
import xarray as xr

# Example cube (placeholder)
cube = xr.DataArray(
    [1, 2, 3, 4, 5, 6],
    dims=["time"],
)

result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.month_filter([6])         # example of a pipeable filter
    | cd.variance(dim="time")
).unwrap()

print(result)
```

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
